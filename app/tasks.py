from celery import shared_task
from django.db.models import F
from django_redis import get_redis_connection
from .models import  ClickEvent, ShortURLMeta




@shared_task
def enqueue_click(short_url_id, user_agent, device_type):
    redis_conn = get_redis_connection("default")

    redis_conn.incr(f"click_count:{short_url_id}")

    redis_conn.rpush(
        f"click_events:{short_url_id}",
        f"{user_agent}|{device_type}"
    )


def handle_click_count(redis_conn, key):
    if isinstance(key, bytes):
        key = key.decode()

    key_str = key
    short_url_id = key_str.split(":")[-1]

    count = int(redis_conn.get(key) or 0)

    if count > 0:
        ShortURLMeta.objects.filter(
            short_url_id=short_url_id
        ).update(
            click_count=F("click_count") + count
        )

    redis_conn.delete(key)



def handle_click_events(redis_conn, key):
    if isinstance(key, bytes):
        key = key.decode()
    key_str = key

    short_url_id = key_str.split(":")[-1]

    events = redis_conn.lrange(key, 0, -1)

    click_objects = []

    for event in events:
        decoded = event.decode()
        user_agent, device_type = decoded.split("|")
        click_objects.append(
            ClickEvent(
                short_url_id=short_url_id,
                user_agent=user_agent,
                device_type=device_type
            )
        )

    if click_objects:
        ClickEvent.objects.bulk_create(click_objects)

    redis_conn.delete(key)




@shared_task
def flush_analytics():
    redis_conn = get_redis_connection("default")

    lock_key = "analytics_flush_lock"

    lock_acquired = redis_conn.set(lock_key, "1", nx=True, ex=60)

    if not lock_acquired:
        print("Flush already running.")
        return

    try:
        # First handle orphan processing keys
        for key in redis_conn.scan_iter("processing:click_count:*"):
            handle_click_count(redis_conn, key)

        for key in redis_conn.scan_iter("processing:click_events:*"):
            handle_click_events(redis_conn, key)

        # Then handle fresh keys
        for key in redis_conn.scan_iter("click_count:*"):
            processing_key = f"processing:{key.decode()}"
            redis_conn.rename(key, processing_key)
            handle_click_count(redis_conn, processing_key)

        for key in redis_conn.scan_iter("click_events:*"):
            processing_key = f"processing:{key.decode()}"
            redis_conn.rename(key, processing_key)
            handle_click_events(redis_conn, processing_key)

    finally:
        redis_conn.delete(lock_key)
