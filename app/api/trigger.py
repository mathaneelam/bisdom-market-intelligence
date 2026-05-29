"""
Manual trigger endpoints.
Call these from the terminal (or a future Dashboard button) to run any part of
the pipeline right now without waiting for the scheduler.

  POST /trigger/collect          — run all collectors
  POST /trigger/process          — run AI scorer on unprocessed signals
  POST /trigger/brief            — rebuild today's intelligence brief
  POST /trigger/deliver/telegram — push today's brief to Telegram
  POST /trigger/all              — full pipeline end-to-end
"""
import logging
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import select

from app.models import base as models_base
from app.models.brief import Brief

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trigger", tags=["trigger"])


# ─── Collect ──────────────────────────────────────────────────────────────────

@router.post("/collect")
async def trigger_collect():
    """Run RSS + Reddit + Play Store collectors now and save new signals to the database."""
    from app.scheduler import run_rss_collector, run_reddit_collector, run_playstore_collector
    logger.info("Manual trigger: collect")
    await run_rss_collector()
    await run_reddit_collector()
    await run_playstore_collector()
    return {"status": "ok", "message": "Collectors finished. Check /signals for new data."}


# ─── Process ──────────────────────────────────────────────────────────────────

@router.post("/process")
async def trigger_process():
    """Run the Gemini AI scorer on any unprocessed signals."""
    from app.scheduler import run_ai_scorer
    logger.info("Manual trigger: process")
    count = await run_ai_scorer()
    return {"status": "ok", "processed": count,
            "message": f"AI scorer ran. {count} signals processed."}


# ─── Brief ────────────────────────────────────────────────────────────────────

@router.post("/brief")
async def trigger_brief():
    """Rebuild today's intelligence brief from processed signals."""
    from app.scheduler import run_brief_builder
    logger.info("Manual trigger: brief")
    await run_brief_builder()
    return {"status": "ok", "message": "Brief rebuilt. Refresh the Dashboard."}


# ─── Deliver: Telegram ────────────────────────────────────────────────────────

@router.post("/deliver/telegram")
async def trigger_telegram(force: bool = False):
    """
    Push today's brief to Telegram.

    By default this respects the 'already delivered' flag — call with
    ?force=true to resend even if it was sent earlier today.
    """
    from app.delivery.telegram import TelegramSender

    logger.info("Manual trigger: telegram (force=%s)", force)
    today = datetime.utcnow().date()

    async with models_base.AsyncSessionLocal() as session:
        stmt = select(Brief).where(Brief.brief_date == today)
        brief = (await session.execute(stmt)).scalars().first()

        if not brief:
            return {
                "status": "error",
                "message": "No brief exists for today yet. Run POST /trigger/brief first.",
            }

        if brief.delivered_tg and not force:
            return {
                "status": "skipped",
                "message": "Brief already sent to Telegram today. Use ?force=true to resend.",
            }

        sender = TelegramSender()
        success = await sender.send_brief(brief)

        if success:
            brief.delivered_tg = True
            await session.commit()
            return {"status": "ok", "message": "Telegram message delivered successfully!"}

        return {
            "status": "error",
            "message": "Telegram send failed. Check server logs for details.",
        }


# ─── Full pipeline ────────────────────────────────────────────────────────────

@router.post("/all")
async def trigger_all():
    """
    Run the complete pipeline end-to-end:
    collect → AI process → build brief → deliver to Telegram.

    Use this for a manual daily run or first-time testing.
    Note: this can take 1-2 minutes because of API calls.
    """
    from app.scheduler import (
        run_rss_collector, run_reddit_collector, run_playstore_collector,
        run_ai_scorer, run_brief_builder, run_telegram_delivery,
    )
    logger.info("Manual trigger: full pipeline")

    await run_rss_collector()
    await run_reddit_collector()
    await run_playstore_collector()
    await run_ai_scorer()
    await run_brief_builder()
    await run_telegram_delivery(force=True)

    return {
        "status": "ok",
        "message": "Full pipeline complete. Check the Dashboard and your Telegram.",
    }
