import requests
import logging
import os

logger = logging.getLogger(__name__)

class EmailUtils:
    RESEND_API_KEY = os.environ.get("RESEND_EMAIL_API_KEY")
    RESEND_API_URL = os.environ.get("RESEND_EMAIL_URL")

    def __init__(self, to_email, subject, message):
        self.to_email = to_email
        self.from_email = os.environ.get("RESEND_TO_MAIL")
        self.subject = subject
        self.message = message
        self.status = None
        self.response = None

    def send_email(self):
        headers = {
            "Authorization": f"Bearer {self.RESEND_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "from": self.from_email,
            "to": [self.to_email],
            "subject": self.subject,
            "text": self.message
        }

        try:
            print(f"sending email to {self.to_email} with subject {self.subject}")
            response = requests.post(self.RESEND_API_URL, json=data, headers=headers)
            response.raise_for_status()
            self.status = "Success"
            self.response = response.json()
        except requests.exceptions.RequestException as e:
            logger.exception("Failed to send email to %s: %s", self.to_email, e)
            self.reason = "Failed to send email to %s: %s", self.to_email, e
            self.status = "Error"
            self.response = str(e)
