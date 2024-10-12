# tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_email(subject, message, email):
    send_mail(
        subject,
        f'{message}',
        'support@theworkflow.nyc',
        [email],
        fail_silently=False,
    )