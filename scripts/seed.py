"""
Seed script — run once after migrations to pre-fill reference data.
Usage: python -m scripts.seed
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows requires SelectorEventLoop for asyncpg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select
from app.config import settings
import app.models.base as db_base
from app.models.competitor import Competitor
from app.models.keyword import Keyword
from app.models.trade_show import TradeShow

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Competitors ────────────────────────────────────────────────────────────────
COMPETITORS = [
    {"name": "IndiaMART", "website": "https://www.indiamart.com"},
    {"name": "TradeIndia", "website": "https://www.tradeindia.com"},
    {"name": "Alibaba", "website": "https://www.alibaba.com"},
    {"name": "Fiber2Fashion", "website": "https://www.fiber2fashion.com"},
    {"name": "Textilegalaxy", "website": "https://www.textilegalaxy.com"},
    {"name": "Locofast", "website": "https://www.locofast.com"},
    {"name": "Fashinza", "website": "https://www.fashinza.com"},
    {"name": "Zilingo", "website": "https://www.zilingo.com"},
    {"name": "Textrade", "website": "https://www.textrade.com"},
    {"name": "Baazaar.com", "website": "https://www.baazaar.com"},
    {"name": "Global Textile Hub", "website": "https://www.globaltextilehub.com"},
    {"name": "Apparelsearch", "website": "https://www.apparelsearch.com"},
]

# ── Keywords ───────────────────────────────────────────────────────────────────
KEYWORDS = [
    # Pain Pulse
    {"keyword": "IndiaMART fake leads", "stream": "pain_pulse", "language": "en"},
    {"keyword": "B2B platform complaint India", "stream": "pain_pulse", "language": "en"},
    {"keyword": "garment sourcing problem India", "stream": "pain_pulse", "language": "en"},
    {"keyword": "manufacturer WhatsApp chaos", "stream": "pain_pulse", "language": "en"},
    {"keyword": "textile supplier fraud India", "stream": "pain_pulse", "language": "en"},
    {"keyword": "IndiaMART renewal not worth it", "stream": "pain_pulse", "language": "en"},
    {"keyword": "sourcing vendor problem", "stream": "pain_pulse", "language": "en"},
    # Competitor Move
    {"keyword": "IndiaMART new feature", "stream": "competitor_move", "language": "en"},
    {"keyword": "Fiber2Fashion launch", "stream": "competitor_move", "language": "en"},
    {"keyword": "Locofast update", "stream": "competitor_move", "language": "en"},
    {"keyword": "Fashinza funding", "stream": "competitor_move", "language": "en"},
    {"keyword": "B2B textile platform India launch", "stream": "competitor_move", "language": "en"},
    # Opportunity Signal
    {"keyword": "looking for garment manufacturer India", "stream": "opportunity_signal", "language": "en"},
    {"keyword": "fabric supplier India MOQ", "stream": "opportunity_signal", "language": "en"},
    {"keyword": "clothing brand manufacturer", "stream": "opportunity_signal", "language": "en"},
    {"keyword": "D2C brand sourcing India", "stream": "opportunity_signal", "language": "en"},
    {"keyword": "knitwear manufacturer India", "stream": "opportunity_signal", "language": "en"},
    {"keyword": "need textile supplier", "stream": "opportunity_signal", "language": "en"},
    {"keyword": "recommend fabric manufacturer", "stream": "opportunity_signal", "language": "en"},
    # Vernacular
    {"keyword": "IndiaMART worth it", "stream": "pain_pulse", "language": "hi"},
    {"keyword": "manufacturer dhundhna", "stream": "opportunity_signal", "language": "hi"},
    {"keyword": "textile supplier problem", "stream": "pain_pulse", "language": "ta"},
]

# ── Trade Shows ────────────────────────────────────────────────────────────────
TRADE_SHOWS = [
    {
        "name": "Bharat Tex",
        "category": "textile",
        "city": "New Delhi",
        "relevance_note": "India's largest textile trade show — key for Bisdom brand presence and lead sourcing",
    },
    {
        "name": "Knit Show Tiruppur",
        "category": "garment",
        "city": "Tiruppur",
        "relevance_note": "Core Bisdom supplier geography — knitwear manufacturers in Tiruppur",
    },
    {
        "name": "IIGF Delhi",
        "category": "garment",
        "city": "New Delhi",
        "relevance_note": "India International Garment Fair — direct access to buyers and exporters",
    },
    {
        "name": "Gartex Texprocess",
        "category": "textile",
        "city": "New Delhi",
        "relevance_note": "Textile machinery and garment technology — useful for supplier tracking",
    },
    {
        "name": "DenimsandJeans India",
        "category": "garment",
        "city": "Mumbai",
        "relevance_note": "Denim segment focus — D2C brands and denim manufacturers attend",
    },
    {
        "name": "Yarnex",
        "category": "textile",
        "city": "Tiruppur",
        "relevance_note": "Yarn trade show — raw material supplier intelligence",
    },
    {
        "name": "F&A Show",
        "category": "garment",
        "city": "Mumbai",
        "relevance_note": "Fashion and Apparel Show — D2C and retail buyer attendance",
    },
    {
        "name": "ASF",
        "category": "textile",
        "city": "Ahmedabad",
        "relevance_note": "Ahmedabad — key Bisdom supplier city for cotton and synthetic textiles",
    },
    {
        "name": "TFI",
        "category": "textile",
        "city": "Mumbai",
        "relevance_note": "Texfusion India — design and fabric innovation show",
    },
    {
        "name": "East India Garments Fair",
        "category": "garment",
        "city": "Kolkata",
        "relevance_note": "East India garment ecosystem — expansion opportunity for Bisdom",
    },
    {
        "name": "India D2C Summit",
        "category": "ecommerce",
        "city": "Bengaluru",
        "relevance_note": "Top D2C brands attend — high-value buyer leads for Bisdom",
    },
    {
        "name": "India Fashion Forum",
        "category": "fashion",
        "city": "Mumbai",
        "relevance_note": "Fashion retail industry — brand owners who need Bisdom sourcing",
    },
    {
        "name": "Fashion India Forum",
        "category": "fashion",
        "city": "New Delhi",
        "relevance_note": "Policy, retail, and brand event — broader market intelligence",
    },
]


async def seed_competitors(session) -> int:
    existing = (await session.execute(select(Competitor))).scalars().all()
    existing_names = {c.name for c in existing}
    new_rows = [
        Competitor(**c) for c in COMPETITORS if c["name"] not in existing_names
    ]
    session.add_all(new_rows)
    return len(new_rows)


async def seed_keywords(session) -> int:
    existing = (await session.execute(select(Keyword))).scalars().all()
    existing_kws = {k.keyword for k in existing}
    new_rows = [
        Keyword(**k) for k in KEYWORDS if k["keyword"] not in existing_kws
    ]
    session.add_all(new_rows)
    return len(new_rows)


async def seed_trade_shows(session) -> int:
    existing = (await session.execute(select(TradeShow))).scalars().all()
    existing_names = {t.name for t in existing}
    new_rows = [
        TradeShow(**t) for t in TRADE_SHOWS if t["name"] not in existing_names
    ]
    session.add_all(new_rows)
    return len(new_rows)


async def main():
    db_base.init_db(settings.DATABASE_URL)
    async with db_base.AsyncSessionLocal() as session:
        c = await seed_competitors(session)
        k = await seed_keywords(session)
        t = await seed_trade_shows(session)
        await session.commit()

    logger.info("Seeded: %d competitors, %d keywords, %d trade shows", c, k, t)


if __name__ == "__main__":
    asyncio.run(main())
