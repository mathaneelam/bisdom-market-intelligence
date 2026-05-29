from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.pattern import Pattern
from app.models.signal_pattern import SignalPattern
from app.models.processed_signal import ProcessedSignal
from app.models.signal import Signal

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.get("")
async def list_patterns(db: AsyncSession = Depends(get_db)):
    """All patterns, ordered by importance (highest first)."""
    stmt = select(Pattern).order_by(Pattern.importance_score.desc())
    patterns = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "bisdom_action": p.bisdom_action,
            "signal_count": p.signal_count,
            "trend": p.trend,
            "importance_score": p.importance_score,
            "first_seen": p.first_seen,
            "last_seen": p.last_seen,
        }
        for p in patterns
    ]


@router.get("/top")
async def top_patterns(limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Top N patterns by importance — used by the Dashboard."""
    stmt = select(Pattern).order_by(Pattern.importance_score.desc()).limit(limit)
    patterns = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "category": p.category,
            "signal_count": p.signal_count,
            "trend": p.trend,
            "importance_score": p.importance_score,
            "bisdom_action": p.bisdom_action,
            "first_seen": p.first_seen,
            "last_seen": p.last_seen,
        }
        for p in patterns
    ]


@router.get("/{pattern_id}/signals")
async def pattern_signals(pattern_id: str, db: AsyncSession = Depends(get_db)):
    """Get all signals linked to a pattern — with source, author, date, and link."""
    stmt = (
        select(ProcessedSignal, Signal)
        .join(SignalPattern, SignalPattern.signal_id == ProcessedSignal.id)
        .join(Signal, Signal.id == ProcessedSignal.signal_id)
        .where(SignalPattern.pattern_id == pattern_id)
        .order_by(Signal.collected_at.desc())
    )
    rows = (await db.execute(stmt)).all()

    return [
        {
            "id": str(ps.id),
            "summary": ps.summary,
            "relevance_score": ps.relevance_score,
            "insight": ps.insight,
            "stream": ps.stream,
            "source": sig.source,
            "source_url": sig.source_url,
            "author": sig.author,
            "collected_at": sig.collected_at,
            "snippet": (sig.raw_content or "")[:300],
        }
        for ps, sig in rows
    ]
