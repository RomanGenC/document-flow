import os

from celery import shared_task
from django.core.mail import send_mail
from django.utils.html import strip_tags

from utils.pdf.generate_pdf import convert_html_to_pdf


@shared_task(acks_late=True, bind=True)
def task_generate_pdf_from_html(self, **kwargs):
    """Таск для запуска convert_html_to_pdf"""
    try:
        convert_html_to_pdf(**kwargs)
    except Exception as error:
        raise self.retry(
            max_retries=5,
            countdown=5*60,
        )


@shared_task(acks_late=True, bind=True)
def task_send_email(self, subject, html_message, to):
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, os.getenv('EMAIL_HOST_USER'), to, html_message=html_message)
