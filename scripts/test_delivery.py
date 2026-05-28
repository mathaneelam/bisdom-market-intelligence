import asyncio
import logging
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.brief import Brief
from app.delivery.email import EmailSender
from app.delivery.telegram import TelegramSender
from app.delivery.whatsapp import WhatsAppSender

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_delivery")

def create_mock_brief() -> Brief:
    """Create a mock brief for testing delivery formatting."""
    return Brief(
        brief_date=datetime.utcnow().date(),
        pain_pulse=[
            {"summary": "IndiaMART fake leads complaint", "relevance_score": 8, "insight": "Users are frustrated by poor quality leads."}
        ],
        competitor_move=[
            {"summary": "Fiber2Fashion launched a new AI feature", "relevance_score": 9, "insight": "Competitors are moving into AI tooling."}
        ],
        opportunity=[
            {"summary": "D2C brand looking for a new garment manufacturer", "relevance_score": 7, "insight": "Direct lead generation opportunity."}
        ],
        full_html="<html><body><h1>Test Brief</h1><p>This is a test brief.</p></body></html>"
    )

async def main():
    logger.info("Starting delivery tests (Dry run, unless keys are provided in .env)...")
    
    mock_brief = create_mock_brief()
    
    email_sender = EmailSender()
    await email_sender.send_brief(mock_brief)
    
    telegram_sender = TelegramSender()
    await telegram_sender.send_brief(mock_brief)
    
    whatsapp_sender = WhatsAppSender()
    await whatsapp_sender.send_brief(mock_brief)
    
    logger.info("Delivery testing complete.")

if __name__ == "__main__":
    asyncio.run(main())
