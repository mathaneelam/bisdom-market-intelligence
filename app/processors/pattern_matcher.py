"""
Pattern Matcher — clusters signals into recurring themes.

After the scorer processes a signal, the pattern matcher asks the LLM:
"Does this signal match any existing pattern, or is it a new one?"

If match → link signal to pattern, increment count, update trend.
If new  → create a new pattern from the signal.
"""
import logging
import asyncio
from datetime import datetime, date, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import base as models_base
from app.models.pattern import Pattern
from app.models.signal_pattern import SignalPattern
from app.models.processed_signal import ProcessedSignal
from app.processors.ollama_processor import OllamaProcessor

logger = logging.getLogger(__name__)


class PatternMatcher:
    def __init__(self):
        self.processor = OllamaProcessor()

    async def match_signal(self, signal: ProcessedSignal, session: AsyncSession) -> str | None:
        """
        Match a single processed signal to an existing pattern, or create a new one.
        Returns the pattern_id (existing or new).
        """
        # Check if already linked
        existing_link = await session.execute(
            select(SignalPattern).where(SignalPattern.signal_id == signal.id)
        )
        if existing_link.scalars().first():
            return None  # Already matched

        # Get existing patterns for this category
        stmt = select(Pattern).where(Pattern.category == signal.stream)
        patterns = (await session.execute(stmt)).scalars().all()

        # Build prompt
        if patterns:
            pattern_list = "\n".join(
                f"- ID: {p.id} | Name: {p.name} | Count: {p.signal_count}"
                for p in patterns
            )
            prompt = f"""EXISTING PATTERNS:
{pattern_list}

NEW SIGNAL:
Stream: {signal.stream}
Summary: {signal.summary}
Insight: {signal.insight}
Score: {signal.relevance_score}

Does this signal match an existing pattern, or is it new?"""
        else:
            # No patterns yet — force new pattern creation
            prompt = f"""EXISTING PATTERNS:
(none — this is the first signal in this category)

NEW SIGNAL:
Stream: {signal.stream}
Summary: {signal.summary}
Insight: {signal.insight}
Score: {signal.relevance_score}

This is the first signal. Create a new pattern for it."""

        data = await self.processor.match_pattern(prompt)
        if data is None:
            return None

        today = date.today()

        if data.get("match") and data.get("pattern_id"):
            # Link to existing pattern
            pattern_id = data["pattern_id"]

            # Verify pattern exists
            pattern = await session.get(Pattern, pattern_id)
            if not pattern:
                    logger.warning("LLM returned non-existent pattern ID: %s", pattern_id)
                return None

            # Update pattern stats
            pattern.signal_count += 1
            pattern.last_seen = today
            pattern.trend = self._calc_trend(pattern)
            pattern.importance_score = self._calc_importance(pattern)

            # Create link
            link = SignalPattern(signal_id=signal.id, pattern_id=pattern.id)
            session.add(link)

            logger.info("Signal matched pattern: %s (count=%d)", pattern.name, pattern.signal_count)
            return str(pattern.id)

        elif data.get("new_pattern"):
            np = data["new_pattern"]
            pattern = Pattern(
                name=np.get("name", signal.summary[:80]),
                description=np.get("description", signal.insight),
                category=signal.stream,
                bisdom_action=np.get("bisdom_action", ""),
                signal_count=1,
                trend="new",
                importance_score=signal.relevance_score * 10 if signal.relevance_score else 50,
                first_seen=today,
                last_seen=today,
            )
            session.add(pattern)
            await session.flush()

            link = SignalPattern(signal_id=signal.id, pattern_id=pattern.id)
            session.add(link)

            logger.info("New pattern created: %s", pattern.name)
            return str(pattern.id)

    def _calc_trend(self, pattern: Pattern) -> str:
        """Calculate trend based on recency and growth."""
        days_active = (date.today() - pattern.first_seen).days or 1
        if days_active <= 3:
            return "new"
        rate = pattern.signal_count / days_active
        if rate >= 0.5:  # More than 1 signal every 2 days
            return "growing"
        elif rate >= 0.15:
            return "stable"
        else:
            return "declining"

    def _calc_importance(self, pattern: Pattern) -> int:
        """
        Importance = frequency weight + recency weight.
        Range: 0–100.
        """
        # Frequency: more signals = more important (log scale, cap at 50)
        import math
        freq_score = min(50, int(math.log2(pattern.signal_count + 1) * 15))

        # Recency: how recently was the last signal?
        days_since = (date.today() - pattern.last_seen).days
        if days_since == 0:
            recency_score = 50
        elif days_since <= 3:
            recency_score = 40
        elif days_since <= 7:
            recency_score = 30
        elif days_since <= 14:
            recency_score = 20
        else:
            recency_score = 10

        return freq_score + recency_score

    async def process_unmatched(self, batch_size: int = 50) -> int:
        """Match all unmatched processed signals to patterns."""
        matched = 0

        async with models_base.AsyncSessionLocal() as session:
            # Find processed signals not yet linked to a pattern
            stmt = select(ProcessedSignal).where(
                ~ProcessedSignal.id.in_(
                    select(SignalPattern.signal_id)
                )
            ).limit(batch_size)

            signals = (await session.execute(stmt)).scalars().all()

            if not signals:
                logger.info("No unmatched signals to process.")
                return 0

            logger.info("Matching %d signals to patterns...", len(signals))

            for signal in signals:
                result = await self.match_signal(signal, session)
                if result:
                    matched += 1
                await asyncio.sleep(0.3)  # Gentle on Ollama

            await session.commit()

        logger.info("Pattern matching complete: %d/%d signals matched.", matched, len(signals))
        return matched
