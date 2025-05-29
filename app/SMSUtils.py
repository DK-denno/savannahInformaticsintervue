import requests
import logging

logger = logging.getLogger(__name__)

class SMSUtils:
    def __init__(self, phone_number, message):
        """
        Initialize with the recipient's phone number and the message.
        """
        self.phone_number = phone_number
        self.message = message
        self.status = "pending"  # pending, sent, failed
        self.reason = ""

    def send_via_africastalking(self, api_key, username):
        """
        Send an SMS using the Africa's Talking HTTP API.
        :param api_key: Africa's Talking API key
        :param sender_id: Sender ID approved by Africa's Talking
        :param username: Africa's Talking account username
        :return: API response or error
        """
        url = "https://api.africastalking.com/version1/messaging"

        headers = {
            "apiKey": api_key,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        payload = {
            "username": username,
            "to": self.phone_number,
            "message": self.message
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            response_data = response.json()

            recipients = response_data.get("SMSMessageData", {}).get("Recipients", [])

            if recipients:
                self.status = "sent"
                logger.info(f"SMS successfully sent to {self.phone_number}")
                for recipient in recipients:
                    self.status = recipient.get("status", "")
            else:
                self.status = "failed"
                self.reason = f"SMS sending failed: No recipients returned for {self.phone_number}"
                logger.warning(f"SMS sending failed: No recipients returned for {self.phone_number}")

            return response_data

        except Exception as e:
            self.status = "failed"
            logger.exception(f"Error sending SMS to {self.phone_number}: {e}")
            return {"success": False, "error": str(e)}