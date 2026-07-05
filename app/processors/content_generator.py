import re
import logging
import asyncio
from datetime import date

from sqlalchemy import select
from openai import AsyncOpenAI

from app.config import settings
from app.models import base as models_base
from app.models.pattern import Pattern
from app.models.signal_pattern import SignalPattern
from app.models.processed_signal import ProcessedSignal
from app.models.signal import Signal
from app.models.content_piece import ContentPiece

logger = logging.getLogger(__name__)

WRITER_MODEL = "gemma4:cloud"
MIN_IMPORTANCE = 60      # only write about patterns that matter — skip one-off noise
MAX_PATTERNS_PER_RUN = 3  # keep daily draft volume reviewable, not a firehose
MAX_EVIDENCE_REVIEWS = 5  # real reviews fed to the model as receipts, per pattern

AUDIENCES = {
    "buyer": "BUYERS (D2C brands and corporates who source from manufacturers in India)",
    "supplier": "SUPPLIERS (garment/textile manufacturers in hubs like Tiruppur, Surat, Ludhiana, Coimbatore)",
}

SYSTEM_PROMPT = """You are the head of content marketing for Bisdom.

ABOUT BISDOM:
Bisdom is an AI-powered B2B commerce platform for India's textile, garment and
manufacturing SME market. It connects VERIFIED buyers (D2C brands, corporates) with
VERIFIED suppliers (manufacturers). It kills three pains competitors like IndiaMART
create: (1) fake/duplicate leads, (2) expensive subscriptions with zero ROI, and
(3) "WhatsApp chaos" — deals lost across scattered chats with no order history.

Today's date is {today}.

YOUR TASK:
You are given a recurring PAIN PATTERN — a real, repeated complaint from the Indian
B2B market — backed by real reviews. Turn that pain into a marketing content kit for
Bisdom. The audience for THIS kit is: {audience}.

Write in the audience's real voice — plain, confident, no corporate fluff, no emoji
overload, no AI-sounding filler. Simple Hinglish phrasing is fine where it feels
natural. Never invent statistics or claims beyond what the evidence supports.

PRODUCE EXACTLY THIS KIT, using these headings and nothing else:

## LinkedIn — Version A (Educational, do NOT name competitors)
(a short post that teaches the pain + how a platform like Bisdom solves it)

## LinkedIn — Version B (Direct contrast, you MAY name the competitor pain openly)
(a punchier post that calls out the exact frustration)

## Instagram — Caption + Reel Hook
Caption: (short, scroll-stopping, a few relevant hashtags)
Reel Hook: (the first spoken line / on-screen text, under 12 words)

## Blog — SEO Title + Outline (Educational)
Title: (search-friendly, e.g. an "IndiaMART alternative" style query)
Outline: (5-6 H2 bullet points)

## Ad Hook (Direct contrast)
(one or two lines, ad-ready)

## Email / WhatsApp Broadcast Line (Direct contrast)
(one short line for outreach)

Return ONLY the kit in clean markdown. No preamble."""


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> reasoning blocks some models emit."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()


class ContentGenerator:
    """
    Turns high-importance pain patterns into ready-to-review marketing content.
    One pattern -> one kit per audience -> one ContentPiece row per format in the kit.
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OLLAMA_API_KEY or "ollama",
            base_url=settings.OLLAMA_BASE_URL or "http://localhost:11434/v1",
        )

    async def _fetch_evidence(self, session, pattern_id) -> list[Signal]:
        """The real, dated reviews behind a pattern — used both as model input and as receipts."""
        stmt = (
            select(Signal)
            .join(ProcessedSignal, ProcessedSignal.signal_id == Signal.id)
            .join(SignalPattern, SignalPattern.signal_id == ProcessedSignal.id)
            .where(SignalPattern.pattern_id == pattern_id)
            .order_by(Signal.collected_at.desc())
            .limit(MAX_EVIDENCE_REVIEWS)
        )
        return (await session.execute(stmt)).scalars().all()

    async def _write_kit(self, pattern: Pattern, audience_key: str, evidence: list[Signal]) -> str:
        evidence_block = "\n".join(
            f"- [{sig.collected_at.date() if sig.collected_at else 'undated'}] "
            f"{sig.source}: \"{(sig.raw_content or '').strip()}\""
            for sig in evidence
        ) or "(no individual reviews on file — rely on the pattern description)"

        user_prompt = (
            f"PAIN PATTERN: {pattern.name}\n"
            f"Description: {pattern.description}\n"
            f"Suggested Bisdom action: {pattern.bisdom_action}\n"
            f"Seen in {pattern.signal_count} signals, trend: {pattern.trend}\n\n"
            f"REAL EVIDENCE (use these, don't invent new ones):\n{evidence_block}\n"
        )

        response = await self.client.chat.completions.create(
            model=WRITER_MODEL,
            max_tokens=3000,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT.format(
                        today=date.today().isoformat(),
                        audience=AUDIENCES[audience_key],
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
        )
        return strip_thinking(response.choices[0].message.content)

    def _parse_kit(self, markdown: str) -> list[dict]:
        """Split the model's one markdown kit into individual (format, tone, title, body) pieces."""
        sections = re.split(r"\n(?=##\s)", markdown.strip())
        pieces = []

        for section in sections:
            match = re.match(r"##\s*(.+)", section)
            if not match:
                continue
            header = match.group(1).strip()
            body = section[match.end():].strip()
            if not body:
                continue

            if "LinkedIn" in header and "Version A" in header:
                pieces.append({"format": "linkedin", "tone": "educational", "title": None, "body": body})
            elif "LinkedIn" in header and "Version B" in header:
                pieces.append({"format": "linkedin", "tone": "contrast", "title": None, "body": body})
            elif "Instagram" in header:
                pieces.append({"format": "instagram", "tone": "educational", "title": None, "body": body})
            elif "Blog" in header:
                title_match = re.search(r"Title:\s*(.+)", body)
                title = title_match.group(1).strip() if title_match else None
                pieces.append({"format": "blog", "tone": "educational", "title": title, "body": body})
            elif "Ad Hook" in header:
                pieces.append({"format": "ad", "tone": "contrast", "title": None, "body": body})
            elif "Email" in header or "WhatsApp" in header:
                pieces.append({"format": "email", "tone": "contrast", "title": None, "body": body})

        return pieces

    async def run(self) -> int:
        """
        Finds high-importance patterns with no content yet, writes a kit per audience,
        and saves every piece as a draft ContentPiece. Returns rows created.
        """
        created = 0

        async with models_base.AsyncSessionLocal() as session:
            stmt = (
                select(Pattern)
                .where(
                    Pattern.importance_score >= MIN_IMPORTANCE,
                    ~Pattern.id.in_(
                        select(ContentPiece.pattern_id).where(ContentPiece.pattern_id.isnot(None))
                    ),
                )
                .order_by(Pattern.importance_score.desc())
                .limit(MAX_PATTERNS_PER_RUN)
            )
            patterns = (await session.execute(stmt)).scalars().all()

            if not patterns:
                logger.info("Content Generator: no new high-importance patterns to write about.")
                return 0

            logger.info("Content Generator: writing content for %d pattern(s)...", len(patterns))

            for pattern in patterns:
                evidence = await self._fetch_evidence(session, pattern.id)
                evidence_ids = [sig.id for sig in evidence] or None

                for audience_key in AUDIENCES:
                    try:
                        kit_markdown = await self._write_kit(pattern, audience_key, evidence)
                        pieces = self._parse_kit(kit_markdown)

                        if not pieces:
                            logger.warning(
                                "Content Generator: unparseable kit for pattern %s (%s)",
                                pattern.id, audience_key,
                            )
                            continue

                        for piece in pieces:
                            session.add(ContentPiece(
                                pattern_id=pattern.id,
                                audience=audience_key,
                                format=piece["format"],
                                tone=piece["tone"],
                                title=piece["title"],
                                body=piece["body"],
                                source_review_ids=evidence_ids,
                                model=WRITER_MODEL,
                            ))
                            created += 1

                    except Exception as e:
                        logger.error(
                            "Content Generator: failed for pattern %s (%s): %s",
                            pattern.id, audience_key, e,
                        )

                    await asyncio.sleep(1)  # gentle on Ollama Cloud

            await session.commit()

        logger.info("Content Generator: created %d content piece(s).", created)
        return created


async def run_content_generator():
    generator = ContentGenerator()
    await generator.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_content_generator())
