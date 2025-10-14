from flask_mail import Message
from flask import current_app
from app import mail
from threading import Thread #  running asynchronous tasks - return immediately
    
def send_async_email(app, msg): # runs in a background thread
    with app.app_context(): # pushes a Flask application context in that thread
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    if not current_app.config.get("EMAIL_ENABLED", True) or not current_app.config.get("MAIL_SERVER"):
        current_app.logger.info("Email disabled; skipping send. subject=%r to=%r", subject, recipients)
        return
    
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_objext(), msg)).start()

