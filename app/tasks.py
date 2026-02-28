import uuid

from celery import shared_task
from django.db.models import F
from django_redis import get_redis_connection
from .models import  ClickEvent, ShortURLMeta
from .metrics import (flush_duration_seconds,
                      flush_lock_failed_total,
                      flush_click_count_total,
                      flush_event_count_total,
                      redis_click_count_backlog,
                      redis_click_event_backlog)
import logging
logger = logging.getLogger(__name__)
from opentelemetry import trace
tracer = trace.get_tracer(__name__)




@shared_task
def enqueue_click(short_url_id, user_agent, device_type):
    with tracer.start_as_current_span("enqueue_click"):
        redis_conn = get_redis_connection("default")

        redis_conn.incr(f"click_count:{short_url_id}")

        redis_conn.rpush(
            f"click_events:{short_url_id}",
            f"{user_agent}|{device_type}"
        )
        print("enqueued click")


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
        flush_click_count_total.inc(count)

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
        flush_event_count_total.inc(len(click_objects))

    redis_conn.delete(key)




@shared_task
def flush_analytics():
    with tracer.start_as_current_span("flush_analytics"):

        redis_conn = get_redis_connection("default")

        lock_key = "analytics_flush_lock"

        lock_value = str(uuid.uuid4())

        lock_acquired = redis_conn.set(lock_key, lock_value, nx=True, ex=60)



        if not lock_acquired:
            flush_lock_failed_total.inc()
            logger.warning("Tried to flush analytics lock")
            print("Flush already running.")
            return
        with flush_duration_seconds.time():
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
                print("flush worked")
                logger.info("flush analytics flushed successfully")
            finally:
                if redis_conn.get(lock_key) == lock_value.encode():
                    redis_conn.delete(lock_key)




@shared_task
def measure_backlog():
    with tracer.start_as_current_span("measure_backlog"):
        redis_conn = get_redis_connection("default")

        click_count_keys = list(redis_conn.scan_iter("click_count:*"))
        total_events = 0
        for key in redis_conn.scan_iter("click_events:*"):
            total_events += redis_conn.llen(key)

        redis_click_count_backlog.set(len(click_count_keys))
        redis_click_event_backlog.set(total_events)
        print("metrics measured backlog")