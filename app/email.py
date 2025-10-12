from flask_mail import Message
from flask import current_app
from app import mail
from threading import Thread #  running asynchronous tasks - return immediately
    
def send_async_email(app, msg): # runs in a background thread
    with app.app_context(): # pushes a Flask application context in that thread
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_objext(), msg)).start()

