"""
Pattern Matcher — clusters signals into recurring themes.

After the scorer processes a signal, the pattern matcher asks Claude:
"Does this signal match any existing pattern, or is it a new one?"

If match → link signal to pattern, increment count, update trend.
If new  → create a new pattern from the signal.
"""
import json
import logging
import asyncio
from datetime import datetime, date, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import base as models_base
from app.models.pattern import Pattern
from app.models.signal_pattern import SignalPattern
from app.models.processed_signal import ProcessedSignal
from app.processors.bedrock_processor import BedrockProcessor, MODEL_ID

logger = logging.getLogger(__name__)

MATCH_SYSTEM = """You are a pattern clustering assistant for Bisdom market intelligence.

Given a NEW signal and a list of EXISTING patterns, determine if the signal belongs to an existing pattern or is a new one.

Rules:
- Match if the signal describes the SAME core problem/opportunity, even with different wording
- "spam calls from IndiaMART" and "barrage of phone calls after posting" are the SAME pattern
- "fake leads" and "wrong quality supplier" are DIFFERENT patterns
- Be strict: only match if the core issue is truly the same

Return ONLY valid JSON:
{
  "match": true/false,
  "pattern_id": "uuid-of-matched-pattern" or null,
  "new_pattern": null or {
    "name": "Short pattern name (under 80 chars)",
    "description": "One paragraph explaining the recurring issue",
    "bisdom_action": "What Bisdom should do about this pattern"
  }
}

JSON only. No preamble. No markdown."""


class PatternMatcher:
    def __init__(self):
        self.processor = BedrockProcessor()

    async def match_signal(self, signal: ProcessedSignal, session: AsyncSession) -> str | None:
        """
        Match a single processed signal to an existing pattern, or create a new one.
        Returns the pattern_id (existing or new).
        """
        if not self.processor.client:
            return None

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

        try:
            response = self.processor.client.invoke_model(
                modelId=MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 512,
                    "system": MATCH_SYSTEM,
                    "messages": [{"role": "user", "content": prompt}],
                }),
            )

            result = json.loads(response["body"].read())
            text = result["content"][0]["text"].strip()

            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())

            today = date.today()

            if data.get("match") and data.get("pattern_id"):
                # Link to existing pattern
                pattern_id = data["pattern_id"]

                # Verify pattern exists
                pattern = await session.get(Pattern, pattern_id)
                if not pattern:
                    logger.warning("Claude returned non-existent pattern ID: %s", pattern_id)
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
                await session.flush()  # Get the ID

                link = SignalPattern(signal_id=signal.id, pattern_id=pattern.id)
                session.add(link)

                logger.info("New pattern created: %s", pattern.name)
                return str(pattern.id)

        except Exception as e:
            logger.error("Pattern matching error: %s", e)
            return None

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
                await asyncio.sleep(0.3)  # Gentle on Bedrock

            await session.commit()

        logger.info("Pattern matching complete: %d/%d signals matched.", matched, len(signals))
        return matched
