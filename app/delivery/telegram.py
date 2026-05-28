import logging
from telegram import Bot
from telegram.constants import ParseMode

from app.config import settings
from app.models.brief import Brief

logger = logging.getLogger(__name__)

class TelegramSender:
    """
    Service for sending the Daily Brief to a Telegram group.
    """
    def __init__(self):
        if settings.TELEGRAM_BOT_TOKEN:
            self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        else:
            self.bot = None

    def _format_brief_for_telegram(self, brief: Brief) -> str:
        """
        Telegram has message limits and requires specific markdown.
        We summarize the brief here instead of sending full HTML.
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
                    # Escape special characters for MarkdownV2 if needed, 
                    # but simple Markdown is easier with ParseMode.MARKDOWN
                    text += f"• {s.get('summary')} (Score: {s.get('relevance_score')})\n"
                text += "\n"
                
        return text

    async def send_brief(self, brief: Brief) -> bool:
        if not self.bot or not settings.TELEGRAM_CHAT_ID:
            logger.warning("Telegram configuration missing. Skipping Telegram delivery.")
            return False

        message = self._format_brief_for_telegram(brief)
        
        try:
            # We send the message using the Bot instance
            await self.bot.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Telegram message sent successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
