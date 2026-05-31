import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

from datetime import datetime
from sqlalchemy import select
from app.models import base as models_base
from app.models.brief import Brief
from app.delivery.telegram import TelegramSender


# ─── Collectors ───────────────────────────────────────────────────────────────

async def run_rss_collector():
    from app.collectors.rss_feeds import RSSCollector
    logger.info("Scheduler: Running RSS Collector...")
    collector = RSSCollector()
    await collector.run()

async def run_reddit_collector():
    from app.collectors.reddit import RedditCollector
    logger.info("Scheduler: Running Reddit Collector...")
    collector = RedditCollector()
    await collector.run()

async def run_playstore_collector():
    from app.collectors.play_store import PlayStoreCollector
    logger.info("Scheduler: Running Play Store Collector...")
    collector = PlayStoreCollector()
    await collector.run()

async def run_google_trends_collector():
    from app.collectors.google_trends import GoogleTrendsCollector
    logger.info("Scheduler: Running Google Trends Collector...")
    collector = GoogleTrendsCollector()
    await collector.run()

async def run_news_collector():
    from app.collectors.news import NewsCollector
    logger.info("Scheduler: Running News Collector...")
    collector = NewsCollector()
    await collector.run()

async def run_instagram_collector():
    from app.collectors.instagram import InstagramCollector
    logger.info("Scheduler: Running Instagram Collector...")
    collector = InstagramCollector()
    await collector.run()



# ─── Processors ───────────────────────────────────────────────────────────────

async def run_ai_scorer():
    from app.processors.scorer import Scorer
    logger.info("Scheduler: Running AI Scorer...")
    scorer = Scorer()
    count = await scorer.process_batch(batch_size=50)
    logger.info("Scheduler: AI Scorer processed %d signals.", count)
    return count

async def run_pattern_matcher():
    from app.processors.pattern_matcher import PatternMatcher
    logger.info("Scheduler: Running Pattern Matcher...")
    matcher = PatternMatcher()
    count = await matcher.process_unmatched(batch_size=50)
    logger.info("Scheduler: Pattern Matcher linked %d signals.", count)
    return count

async def run_brief_builder():
    from app.processors.brief_builder import BriefBuilder
    logger.info("Scheduler: Running Brief Builder...")
    builder = BriefBuilder()
    await builder.run()


# ─── Delivery ─────────────────────────────────────────────────────────────────

async def run_telegram_delivery(force: bool = False):
    """Send today's brief to Telegram. Set force=True to resend even if already delivered."""
    logger.info("Scheduler: Running Telegram Delivery...")
    today = datetime.utcnow().date()
    async with models_base.AsyncSessionLocal() as session:
        stmt = select(Brief).where(Brief.brief_date == today)
        brief = (await session.execute(stmt)).scalars().first()
        if not brief:
            logger.warning("Scheduler: No brief found for today — skipping Telegram delivery.")
            return False
        if brief.delivered_tg and not force:
            logger.info("Scheduler: Brief already delivered via Telegram today.")
            return False
        sender = TelegramSender()
        success = await sender.send_brief(brief)
        if success:
            brief.delivered_tg = True
            await session.commit()
            logger.info("Scheduler: Telegram delivery complete.")
        return success


# ─── Bin Cleanup ──────────────────────────────────────────────────────────────

def run_bin_cleanup():
    """Auto-purge expired bin files from local disk AND git (runs daily)."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from bin_manager import BinManager
    logger.info("Scheduler: Running Bin Cleanup (7-day rule)...")
    bm = BinManager()
    deleted = bm.cleanup(days=7)
    logger.info("Scheduler: Bin Cleanup complete. %d file(s) permanently removed.", deleted)


def setup_jobs():
    """Register all scheduled jobs."""

    # Every 6 hours — RSS feeds (TechCrunch, Fibre2Fashion, etc.)
    scheduler.add_job(
        run_rss_collector,
        "interval",
        hours=6,
        id="rss_collector",
        replace_existing=True,
    )

    # Every 4 hours — Reddit (pain pulse + opportunity keywords)
    scheduler.add_job(
        run_reddit_collector,
        "interval",
        hours=4,
        id="reddit_collector",
        replace_existing=True,
    )

    # Every 12 hours — Play Store reviews (competitor pain points)
    scheduler.add_job(
        run_playstore_collector,
        "interval",
        hours=12,
        id="playstore_collector",
        replace_existing=True,
    )

    # Every 12 hours — Google Trends (market sentiment & keywords)
    scheduler.add_job(
        run_google_trends_collector,
        "interval",
        hours=12,
        id="google_trends_collector",
        replace_existing=True,
    )

    # Every 8 hours — Google News (competitor moves & PR)
    scheduler.add_job(
        run_news_collector,
        "interval",
        hours=8,
        id="news_collector",
        replace_existing=True,
    )

    # Every 12 hours — Instagram (opportunity signals)
    scheduler.add_job(
        run_instagram_collector,
        "interval",
        hours=12,
        id="instagram_collector",
        replace_existing=True,
    )

    # Daily 5:00 AM IST — AI scoring of raw signals
    scheduler.add_job(
        run_ai_scorer,
        "cron",
        hour=5,
        minute=0,
        id="ai_processing",
        replace_existing=True,
    )

    # Daily 5:15 AM IST — Pattern matching (cluster signals into themes)
    scheduler.add_job(
        run_pattern_matcher,
        "cron",
        hour=5,
        minute=15,
        id="pattern_matcher",
        replace_existing=True,
    )

    # Daily 5:30 AM IST — Build intelligence brief
    scheduler.add_job(
        run_brief_builder,
        "cron",
        hour=5,
        minute=30,
        id="brief_builder",
        replace_existing=True,
    )

    # Daily 6:00 AM IST — Send brief via Telegram
    scheduler.add_job(
        run_telegram_delivery,
        "cron",
        hour=6,
        minute=0,
        id="delivery_telegram",
        replace_existing=True,
    )

    # Daily 3:00 AM IST — Auto-purge bin files older than 7 days (local + git)
    scheduler.add_job(
        run_bin_cleanup,
        "cron",
        hour=3,
        minute=0,
        id="bin_cleanup",
        replace_existing=True,
    )

    logger.info("Scheduler: %d jobs registered.", len(scheduler.get_jobs()))
