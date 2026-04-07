# -----------------------------------------------------------------------------
# EMAIL UTILS
# -----------------------------------------------------------------------------
'''
Utility functions for sending budget alert email reminders.
'''
from __future__ import annotations
import smtplib
from email.message import EmailMessage

# -----------------------------------------------------------------------------
# EMAIL CONFIGURATION
# -----------------------------------------------------------------------------
EMAIL_USER = 'hkhraibah@gmail.com'
EMAIL_PASSWORD = 'byxk viud kqlv yhon'
EMAIL_RECIPIENTS = ['khra0005@algonquinlive.com']

# -----------------------------------------------------------------------------
# EMAIL SENDING
# -----------------------------------------------------------------------------
def send_email(subject: str, body: str) -> bool:
    '''Send an email to all configured recipients.'''
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD or not EMAIL_RECIPIENTS:
            return False

        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = EMAIL_USER
        message['To'] = ', '.join(EMAIL_RECIPIENTS)
        message.set_content(body)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(message)

        return True

    except Exception:
        return False