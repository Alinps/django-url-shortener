from celery import shared_task
from django.db.models import F
from .models import  ClickEvent, ShortURLMeta


@shared_task(bind=True,autoretry_for=(Exception,),retry_kwargs={"max_retries":3, "countdown":5})
def record_click_event(self, short_url_id, user_agent, device_type):

    # Increment click count safely
    ShortURLMeta.objects.filter(short_url_id=short_url_id).update(
        click_count=F("click_count")+1
    )
    print("executed task:", short_url_id)
    # Store click event
    ClickEvent.objects.create(
        short_url_id=short_url_id,
        user_agent=user_agent,
        device_type=device_type
    )
