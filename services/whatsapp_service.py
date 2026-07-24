import os
import requests
import logging
from core.config import settings

logger = logging.getLogger("sentry.whatsapp")

class WhatsAppClient:
    """
    Production WhatsApp Integration Client supporting both:
    1. Meta WhatsApp Cloud API (Official Meta Graph API)
    2. Twilio for WhatsApp API
    """

    def __init__(self):
        self.provider = os.getenv("WHATSAPP_PROVIDER", "meta").lower()
        
        # Meta Cloud API Credentials
        self.meta_phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.meta_access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.meta_version = os.getenv("META_WA_API_VERSION", "v19.0")

        # Twilio Credentials
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from_number = os.getenv("TWILIO_WA_PHONE_NUMBER", "whatsapp:+14155238886")

    def send_text_message(self, to_phone: str, text_content: str) -> bool:
        """
        Sends outbound WhatsApp text message to user phone number.
        to_phone should be in E.164 format (e.g. "+2348123456789" or "2348123456789").
        """
        if self.provider == "meta":
            return self._send_meta_message(to_phone, text_content)
        elif self.provider == "twilio":
            return self._send_twilio_message(to_phone, text_content)
        else:
            logger.warning(f"Simulated WhatsApp send to {to_phone}: {text_content[:60]}...")
            return True

    def _send_meta_message(self, to_phone: str, text_content: str) -> bool:
        if not self.meta_phone_number_id or not self.meta_access_token:
            logger.error("Meta WhatsApp credentials missing. Set META_WA_PHONE_NUMBER_ID and META_WA_ACCESS_TOKEN.")
            return False

        clean_phone = to_phone.replace("whatsapp:", "").replace("+", "").strip()
        url = f"https://graph.facebook.com/{self.meta_version}/{self.meta_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.meta_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text_content
            }
        }

        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code in [200, 201]:
                logger.info(f"Successfully sent Meta WA message to {clean_phone}")
                return True
            else:
                logger.error(f"Meta WA API Error ({res.status_code}): {res.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to communicate with Meta WA API: {e}")
            return False

    def _send_twilio_message(self, to_phone: str, text_content: str) -> bool:
        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.error("Twilio credentials missing. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")
            return False

        formatted_to = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
        
        data = {
            "From": self.twilio_from_number,
            "To": formatted_to,
            "Body": text_content
        }

        try:
            res = requests.post(
                url,
                data=data,
                auth=(self.twilio_account_sid, self.twilio_auth_token),
                timeout=10
            )
            if res.status_code in [200, 201]:
                logger.info(f"Successfully sent Twilio WA message to {formatted_to}")
                return True
            else:
                logger.error(f"Twilio WA API Error ({res.status_code}): {res.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to communicate with Twilio WA API: {e}")
            return False

wa_client = WhatsAppClient()
