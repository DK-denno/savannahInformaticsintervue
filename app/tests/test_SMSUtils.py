from django.test import TestCase
from unittest.mock import patch, Mock
from app.SMSUtils import SMSUtils
import os


class SMSUtilsTests(TestCase):

    def setUp(self):
        self.phone_number = "254725328016"
        self.message = "Test message"
        self.api_key = os.environ.get("AT_API_KEY")
        self.username = os.environ.get("AT_USERNAME")
        self.sms = SMSUtils(self.phone_number, self.message)

    @patch("app.SMSUtils.requests.post")
    def test_send_via_africastalking_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "SMSMessageData": {
                "Recipients": [
                    {"status": "Success", "number": self.phone_number}
                ]
            }
        }
        mock_post.return_value = mock_response

        result = self.sms.send_via_africastalking(self.api_key, self.username)

        self.assertEqual(self.sms.status, "Success")
        self.assertIn("SMSMessageData", result)

    @patch("app.SMSUtils.requests.post")
    def test_send_via_africastalking_no_recipients(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "SMSMessageData": {
                "Recipients": []
            }
        }
        mock_post.return_value = mock_response

        result = self.sms.send_via_africastalking(self.api_key, self.username)

        self.assertEqual(self.sms.status, "failed")
        self.assertIn("No recipients returned", self.sms.reason)
        self.assertIn("SMSMessageData", result)

    @patch("app.SMSUtils.requests.post")
    def test_send_via_africastalking_exception(self, mock_post):
        mock_post.side_effect = Exception("Timeout error")

        result = self.sms.send_via_africastalking(self.api_key, self.username)

        self.assertEqual(self.sms.status, "failed")
        self.assertIn("Timeout error", result["error"])
