import re
import logging
import asyncio
from datetime import date, timedelta

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
WEEK_HORIZON_DAYS = 7     # keep the content calendar filled this many days ahead
MAX_EVIDENCE_REVIEWS = 5  # real reviews fed to the model as receipts, per pattern
MIN_BLOG_WORDS = 600      # below this, gemma4:cloud ended its turn early — worth one retry

AUDIENCES = {
    "buyer": "BUYERS (D2C brands and corporates who source from manufacturers in India)",
    "supplier": "SUPPLIERS (garment/textile manufacturers in hubs like Tiruppur, Surat, Ludhiana, Coimbatore)",
}

# One topic/pattern per calendar day, repurposed across every platform that
# day. Rotation gives 5/7 buyer days and 2/7 supplier days (~70/30 split),
# spread evenly across the week rather than clumped — index = days from today.
AUDIENCE_ROTATION = ["buyer", "buyer", "supplier", "buyer", "buyer", "supplier", "buyer"]

PROMPT_PREAMBLE = """You are the head of content marketing for Bisdom.

ABOUT BISDOM:
Bisdom is an AI-powered B2B commerce platform for India's textile, garment and
manufacturing SME market. It connects VERIFIED buyers (D2C brands, corporates) with
VERIFIED suppliers (manufacturers). It kills three pains competitors like IndiaMART
create: (1) fake/duplicate leads, (2) expensive subscriptions with zero ROI, and
(3) "WhatsApp chaos" — deals lost across scattered chats with no order history.

Today's date is {{today}}.

YOUR TASK:
You are given a recurring PAIN PATTERN — a real, repeated complaint from the Indian
B2B market — backed by real reviews. Turn that pain into platform-native content
for Bisdom. The audience for THIS content is: {{audience}}.

Each format below has a different goal, length, and structure — they are NOT the
same post reused. Follow each one's word count and structure exactly. Write in the
audience's real voice — plain, confident, no corporate fluff, no AI-sounding filler.
Simple Hinglish phrasing is fine where it feels natural. Never invent statistics or
claims beyond what the evidence supports.

EMOJI RULE: LinkedIn, Instagram, and WhatsApp pieces may use at most 2-4 emojis
total, placed naturally (never one per line, never in Blog or Email — those stay
professional with zero emojis).

For EVERY format below, before writing its actual content, output exactly these
two labeled lines (each a single line, no line breaks inside them), then continue
directly with that format's own content:
Image: (a 1-2 sentence description of the accompanying visual/graphic for this piece)
Comment: (a short first-comment/follow-up note the author adds separately from the
main copy — a CTA, an extra stat, or hashtags kept out of the main text)

PRODUCE EXACTLY THIS {kit_label}, using these headings and nothing else:

"""

# Short-form kit: five quick, punchy pieces in one completion. These formats are
# all under ~350 words each, so one model call comfortably gives each its full
# attention without any of them getting shortchanged.
SYSTEM_PROMPT_SHORT = PROMPT_PREAMBLE.format(kit_label="KIT") + """## LinkedIn Post - Version A (Educational, do NOT name competitors)
Goal: authority. Length: 150-350 words, 12-25 short lines with white space between
ideas. Structure: Hook -> Problem -> short story or industry insight -> Lesson ->
CTA (invite comments/discussion, do not push a sale).

## LinkedIn Post - Version B (Direct contrast, you MAY name the competitor pain openly)
Same length and structure as Version A, but punchier and calls out the exact
frustration directly instead of teaching around it.

## Instagram Post (Awareness)
Caption: 80-200 words. Structure: Hook (first line stops the scroll) -> Insight ->
one line describing the visual/graphic that would accompany it -> CTA (comment,
save, or share). End with 3-5 relevant hashtags.

## Instagram Reel (Reach)
A spoken/on-screen script, 20-60 seconds total, written as four timed beats:
0-3 sec (big hook): ...
3-15 sec (the pain): ...
15-40 sec (the solution): ...
40-60 sec (CTA - follow/comment): ...
Each beat is 1-2 short punchy lines, not paragraphs.

## WhatsApp Forward (Virality)
4-12 lines maximum, each line readable without opening the message (short lines,
no paragraphs). Structure: Problem -> interesting fact -> one solution -> one CTA
-> website link.

Return ONLY the kit in clean markdown. No preamble."""

# Long-form kit: only the three pieces that need real word-count depth (Blog is
# 1200-3000 words). Kept in its own completion, away from the five short-form
# asks above, so the model spends its full output budget on getting these long
# instead of splitting attention eight ways and undershooting every long piece.
SYSTEM_PROMPT_LONG = PROMPT_PREAMBLE.format(kit_label="CONTENT") + """## LinkedIn Article (SEO + Deep Expertise)
Title: (search-friendly long-tail title)
Body: 800-2000 words. Do not stop short of 800 words. Structure: Introduction ->
why this matters -> the industry problem in depth -> Bisdom's insight/point of
view -> a concrete example or mini case study -> where this is heading ->
Conclusion with CTA (visit website / book a demo).

## Email Newsletter (Nurture Leads)
Subject: (short, curiosity or value-driven, under 60 characters)
Body: 150-500 words. Structure: Greeting -> Hook -> main value/insight -> CTA
(reply or book a demo) -> Signature.

## Blog (Organic Search - Full Draft)
Title: (search-friendly, e.g. an "IndiaMART alternative" style query)
Body: 1200-3000 words, a complete publish-ready SEO article. Do not stop short of
1200 words — this is the longest, most important piece in the kit. Structure:
Introduction -> the problem -> supporting statistics/evidence (only from what's
given) -> real examples -> Bisdom's solution -> how implementation works ->
Conclusion -> 2-3 FAQs with short answers.

Return ONLY the content in clean markdown. No preamble."""


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> reasoning blocks some models emit."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()


class ContentGenerator:
    """
    Turns high-importance pain patterns into a ready-to-review content calendar.
    One pattern -> one calendar day -> one ContentPiece row per platform format,
    written for that day's rotated audience (buyer or supplier).
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

    async def _write_kit(self, system_prompt: str, pattern: Pattern, audience_key: str, evidence: list[Signal]) -> str:
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
            max_tokens=10000,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt.format(
                        today=date.today().isoformat(),
                        audience=AUDIENCES[audience_key],
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
        )
        return strip_thinking(response.choices[0].message.content)

    async def _write_long_kit(self, pattern: Pattern, audience_key: str, evidence: list[Signal]) -> list[dict]:
        """
        Writes the long-form kit (LinkedIn Article, Email, Blog) and retries once
        if Blog comes back short — gemma4:cloud ends its turn early on the longest
        section (a clean `stop`, not a token cutoff) in roughly half of calls.
        """
        kit_markdown = await self._write_kit(SYSTEM_PROMPT_LONG, pattern, audience_key, evidence)
        pieces = self._parse_kit(kit_markdown)
        blog = next((p for p in pieces if p["format"] == "blog"), None)

        if blog and len(blog["body"].split()) < MIN_BLOG_WORDS:
            logger.info(
                "Content Generator: blog came back short (%d words) for pattern %s (%s), retrying long kit once",
                len(blog["body"].split()), pattern.id, audience_key,
            )
            kit_markdown = await self._write_kit(SYSTEM_PROMPT_LONG, pattern, audience_key, evidence)
            pieces = self._parse_kit(kit_markdown)

        return pieces

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

            title_match = re.search(r"Title:\s*(.+)", body) or re.search(r"^#\s+(.+)", body, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else None
            subject_match = re.search(r"Subject:\s*(.+)", body)
            subject = subject_match.group(1).strip() if subject_match else None
            image_match = re.search(r"Image:\s*(.+)", body)
            image_brief = image_match.group(1).strip() if image_match else None
            comment_match = re.search(r"Comment:\s*(.+)", body)
            comment_note = comment_match.group(1).strip() if comment_match else None

            # Strip the labeled meta-lines out of the rendered body/caption text
            # — they're captured into their own fields above, not shown inline.
            body = re.sub(
                r"^(Title|Subject|Image|Comment):\s*.+$\n?", "", body, flags=re.MULTILINE
            ).strip()

            meta = {"image_brief": image_brief, "comment_note": comment_note}

            # Order matters: check the more specific "LinkedIn Article" before
            # the generic "LinkedIn Post" bucket, since both contain "LinkedIn".
            if "LinkedIn Article" in header:
                pieces.append({**meta, "format": "linkedin_article", "tone": "educational", "title": title, "body": body})
            elif "LinkedIn Post" in header and "Version A" in header:
                pieces.append({**meta, "format": "linkedin", "tone": "educational", "title": None, "body": body})
            elif "LinkedIn Post" in header and "Version B" in header:
                pieces.append({**meta, "format": "linkedin", "tone": "contrast", "title": None, "body": body})
            elif "Instagram Post" in header:
                pieces.append({**meta, "format": "instagram_post", "tone": "educational", "title": None, "body": body})
            elif "Instagram Reel" in header:
                pieces.append({**meta, "format": "instagram_reel", "tone": "educational", "title": None, "body": body})
            elif "WhatsApp" in header:
                pieces.append({**meta, "format": "whatsapp", "tone": "contrast", "title": None, "body": body})
            elif "Email" in header:
                pieces.append({**meta, "format": "email", "tone": "educational", "title": subject, "body": body})
            elif "Blog" in header:
                pieces.append({**meta, "format": "blog", "tone": "educational", "title": title, "body": body})

        return pieces

    async def run(self) -> int:
        """
        Keeps the content calendar filled WEEK_HORIZON_DAYS ahead: one pattern per
        missing day, written once for that day's rotated audience (~70% buyer /
        30% supplier), repurposed across every platform format. Idempotent — if
        the calendar is already full, this is a no-op, so it's safe to run daily
        without duplicating work or requiring a strict weekly cron.
        """
        created = 0
        today = date.today()
        horizon = [today + timedelta(days=i) for i in range(WEEK_HORIZON_DAYS)]

        async with models_base.AsyncSessionLocal() as session:
            existing_dates_stmt = select(ContentPiece.scheduled_date).where(
                ContentPiece.scheduled_date.isnot(None),
                ContentPiece.scheduled_date >= today,
            ).distinct()
            existing_dates = {row[0] for row in (await session.execute(existing_dates_stmt)).all()}

            missing_days = [d for d in horizon if d not in existing_dates]

            if not missing_days:
                logger.info("Content Generator: calendar already full through %s.", horizon[-1])
                return 0

            stmt = (
                select(Pattern)
                .where(
                    Pattern.importance_score >= MIN_IMPORTANCE,
                    ~Pattern.id.in_(
                        select(ContentPiece.pattern_id).where(ContentPiece.pattern_id.isnot(None))
                    ),
                )
                .order_by(Pattern.importance_score.desc())
                .limit(len(missing_days))
            )
            patterns = (await session.execute(stmt)).scalars().all()

            if not patterns:
                logger.info(
                    "Content Generator: no new high-importance patterns to fill %d missing day(s).",
                    len(missing_days),
                )
                return 0

            logger.info(
                "Content Generator: filling %d of %d missing day(s) with new pattern(s)...",
                len(patterns), len(missing_days),
            )

            for day, pattern in zip(missing_days, patterns):
                audience_key = AUDIENCE_ROTATION[(day - today).days % len(AUDIENCE_ROTATION)]
                evidence = await self._fetch_evidence(session, pattern.id)
                evidence_ids = [sig.id for sig in evidence] or None
                batch_new = 0

                # Two separate completions: short-form pieces and long-form pieces
                # each get the model's full attention, instead of splitting one
                # call eight ways and undershooting the long-form word counts.
                for kit_name in ("short", "long"):
                    try:
                        if kit_name == "short":
                            kit_markdown = await self._write_kit(SYSTEM_PROMPT_SHORT, pattern, audience_key, evidence)
                            pieces = self._parse_kit(kit_markdown)
                        else:
                            pieces = await self._write_long_kit(pattern, audience_key, evidence)

                        if not pieces:
                            logger.warning(
                                "Content Generator: unparseable %s kit for pattern %s (%s, %s)",
                                kit_name, pattern.id, audience_key, day,
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
                                image_brief=piece.get("image_brief"),
                                comment_note=piece.get("comment_note"),
                                scheduled_date=day,
                                source_review_ids=evidence_ids,
                                model=WRITER_MODEL,
                            ))
                            batch_new += 1

                    except Exception as e:
                        logger.error(
                            "Content Generator: failed %s kit for pattern %s (%s, %s): %s",
                            kit_name, pattern.id, audience_key, day, e,
                        )

                    await asyncio.sleep(1)  # gentle on Ollama Cloud

                # Commit per day rather than once at the end. A full run can take
                # several minutes with retries, and holding one connection open
                # that long risks Neon (serverless Postgres) dropping it — which
                # previously lost an entire run's work at the final commit.
                # Short-lived transactions also mean a mid-run failure doesn't
                # roll back days that already finished.
                try:
                    await session.commit()
                    created += batch_new
                except Exception as e:
                    logger.error(
                        "Content Generator: commit failed for pattern %s (%s, %s): %s",
                        pattern.id, audience_key, day, e,
                    )
                    await session.rollback()

        logger.info("Content Generator: created %d content piece(s).", created)
        return created


async def run_content_generator():
    generator = ContentGenerator()
    await generator.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_content_generator())
