import logging
import resend
from app.config import settings
from app.models.brief import Brief

logger = logging.getLogger(__name__)

class EmailSender:
    """
    Service for sending the Daily Brief via Email using Resend.
    """
    def __init__(self):
        # We configure the resend library with our API key from config
        resend.api_key = settings.RESEND_API_KEY

    async def send_brief(self, brief: Brief) -> bool:
        if not settings.RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not set. Skipping email delivery.")
            return False
            
        if not settings.TARGET_EMAILS:
            logger.warning("No TARGET_EMAILS configured. Skipping email delivery.")
            return False

        try:
            # We construct the email payload (order)
            params = {
                "from": "Bisdom Intelligence <onboarding@resend.dev>",
                "to": settings.TARGET_EMAILS,
                "subject": f"Bisdom Market Intelligence Brief - {brief.brief_date}",
                "html": brief.full_html,
            }

            # We use the SDK to send the request
            email_response = resend.Emails.send(params)
            
            logger.info(f"Email sent successfully. ID: {email_response.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
