import asyncio
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings
from app.models.base import init_db
from app.models import base as models_base
from app.models.brief import Brief
from app.delivery.telegram import TelegramSender
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_telegram")

async def main():
    logger.info("Initializing Database Connection...")
    init_db(settings.DATABASE_URL)
    
    async with models_base.AsyncSessionLocal() as session:
        # Get the latest brief
        result = await session.execute(select(Brief).order_by(Brief.brief_date.desc()).limit(1))
        brief = result.scalars().first()
        
        if not brief:
            logger.error("No brief found in the database to send!")
            return
            
        logger.info(f"Found Brief for date: {brief.brief_date}. Sending via Telegram...")
        
        telegram_sender = TelegramSender()
        success = await telegram_sender.send_brief(brief)
        
        if success:
            logger.info("SUCCESS: The brief was successfully delivered to your Telegram app!")
            # Mark as delivered
            brief.delivered_tg = True
            await session.commit()
        else:
            logger.error("FAILED: Could not send the brief. Check your Bot Token and Chat ID in .env")

if __name__ == "__main__":
    asyncio.run(main())
