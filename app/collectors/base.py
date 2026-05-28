import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime

import redis.asyncio as aioredis

from app.config import settings
from app.models import base as models_base
from app.models.signal import Signal

logger = logging.getLogger(__name__)

DEDUP_TTL_SECONDS = 30 * 24 * 3600  # 30 days


class BaseCollector(ABC):
    """
    Abstract base class for all signal collectors.

    Every collector (Reddit, RSS, Instagram, etc.) inherits from this class
    and implements the `collect()` method. The save and deduplication logic
    is shared here so it never needs to be written twice.
    """

    stream: str = "unknown"  # overridden by each subclass, e.g. "pain_pulse"

    def __init__(self):
        self.redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis

    @abstractmethod
    async def collect(self) -> list[dict]:
        """
        Fetch raw signals from the source.
        Must return a list of dicts with at minimum:
          - source_url (str)   — unique URL for deduplication
          - raw_content (str)  — the text content
          - source (str)       — human-readable source name
          - author (str|None)  — author if available
          - language (str)     — "en", "hi", "ta", etc.
        """

    async def save(self, signals: list[dict]) -> int:
        """Deduplicates by source_url hash and saves new signals to the DB."""
        if not signals:
            logger.info("[%s] No signals to save.", self.stream)
            return 0

        redis = await self._get_redis()
        saved_count = 0

        async with models_base.AsyncSessionLocal() as session:
            for data in signals:
                source_url = data.get("source_url") or ""
                url_hash = hashlib.sha256(source_url.encode()).hexdigest()
                dedup_key = f"dedup:{url_hash}"

                if await redis.exists(dedup_key):
                    logger.debug("[%s] Duplicate skipped: %s", self.stream, source_url)
                    continue

                signal = Signal(
                    stream=data.get("stream", self.stream),
                    source=data.get("source"),
                    source_url=source_url or None,
                    raw_content=data.get("raw_content"),
                    author=data.get("author"),
                    language=data.get("language", "en"),
                    collected_at=data.get("collected_at", datetime.utcnow()),
                )
                session.add(signal)
                await redis.setex(dedup_key, DEDUP_TTL_SECONDS, "1")
                saved_count += 1

            await session.commit()

        logger.info(
            "[%s] Saved %d new signals (skipped %d duplicates).",
            self.stream,
            saved_count,
            len(signals) - saved_count,
        )
        return saved_count

    async def run(self) -> int:
        """Orchestrates a full collect-and-save cycle."""
        logger.info("[%s] Starting collection run.", self.stream)
        try:
            signals = await self.collect()
            logger.info("[%s] Collected %d raw signals.", self.stream, len(signals))
            saved = await self.save(signals)
            return saved
        except Exception as exc:
            logger.exception("[%s] Collection run failed: %s", self.stream, exc)
            return 0
        finally:
            if self.redis:
                await self.redis.aclose()
                self.redis = None
