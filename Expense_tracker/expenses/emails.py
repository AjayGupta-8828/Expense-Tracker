from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_welcome_email(user_email, user_name):
    subject = "Welcome to Expense Tracker"
    text_content = f"Welcome, {user_name}! Thanks for signing up."
    html_content = render_to_string('emails/welcome.html', {
        'user_name': user_name,
        'site_url': 'http://127.0.0.1:8000/',
    })

    msg = EmailMultiAlternatives(subject, text_content, 'ajaylegend506@gmail.com', [user_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()