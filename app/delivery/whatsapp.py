import logging
import httpx

from app.config import settings
from app.models.brief import Brief

logger = logging.getLogger(__name__)

class WhatsAppSender:
    """
    Service for sending the Daily Brief via WhatsApp Business Cloud API.
    Uses raw HTTP requests via httpx.
    """
    def __init__(self):
        self.token = settings.WHATSAPP_TOKEN
        self.phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_url = f"https://graph.facebook.com/v17.0/{self.phone_id}/messages"

    def _format_brief_for_whatsapp(self, brief: Brief) -> str:
        """
        Formats the brief into simple text since WhatsApp doesn't support HTML.
        We use bolding (*) which WhatsApp natively supports.
        """
        text = f"🚨 *Bisdom Intelligence Brief - {brief.brief_date}* 🚨\n\n"
        
        sections = [
            ("🔴 *Pain Pulse*", brief.pain_pulse),
            ("🔵 *Competitor Moves*", brief.competitor_move),
            ("🟢 *Opportunity Signals*", brief.opportunity)
        ]
        
        for title, signals in sections:
            if signals:
                text += f"{title}\n"
                for s in signals:
                    text += f"• {s.get('summary')} (Score: {s.get('relevance_score')})\n"
                text += "\n"
                
        return text

    async def send_brief(self, brief: Brief) -> bool:
        if not self.token or not self.phone_id or not settings.TARGET_PHONES:
            logger.warning("WhatsApp configuration missing. Skipping WhatsApp delivery.")
            return False

        message_text = self._format_brief_for_whatsapp(brief)
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        success = True
        
        async with httpx.AsyncClient() as client:
            for phone_number in settings.TARGET_PHONES:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": phone_number,
                    "type": "text",
                    "text": {
                        "body": message_text
                    }
                }
                
                try:
                    # Here we make the raw HTTP POST request to the API
                    response = await client.post(self.api_url, headers=headers, json=payload)
                    response.raise_for_status()
                    logger.info(f"WhatsApp message sent to {phone_number}.")
                except httpx.HTTPStatusError as e:
                    logger.error(f"WhatsApp HTTP error for {phone_number}: {e.response.text}")
                    success = False
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp to {phone_number}: {e}")
                    success = False
                    
        return success
