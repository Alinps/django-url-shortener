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


@shared_task
def flush_analytics():
    redis_conn = get_redis_connection("default")

    for key in redis_conn.scan_iter("click_count:*"):
        key_str = key.decode()
        short_url_id = key_str.split(":")[1]
        count = int(redis_conn.get(key))

        if count > 0:
            ShortURLMeta.objects.filter(
                short_url_id=short_url_id,
            ).update(click_count=F("click_count")+count)

        redis_conn.delete(key)

    for key in redis_conn.scan_iter("click_events:*"):
        key_str = key.decode()
        short_url_id = key_str.split(":")[1]
        events = redis_conn.lrange(key,0,-1)

        click_objects = []

        for event in events:
            decode = event.decode()
            user_agent,device_type = decode.split("|")
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