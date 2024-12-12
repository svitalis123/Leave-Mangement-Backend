# app/utils/email.py
from flask_mail import Message
from app import mail
from flask import current_app

def send_email(to, subject, body):
    try:
        msg = Message(
            subject,
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[to]
        )
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False