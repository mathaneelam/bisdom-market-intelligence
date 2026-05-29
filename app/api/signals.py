from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.signal import Signal
from app.models.processed_signal import ProcessedSignal

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/stats")
async def signal_stats(db: AsyncSession = Depends(get_db)):
    """Counts by stream — uses AI-classified streams from processed_signals for accuracy."""
    # Raw signal count
    raw = await db.execute(select(func.count(Signal.id)))
    total = raw.scalar() or 0

    # AI-classified stream counts (from processed_signals — these reflect what Claude actually classified)
    result = await db.execute(
        select(ProcessedSignal.stream, func.count(ProcessedSignal.id)).group_by(ProcessedSignal.stream)
    )
    by_stream = {row[0] or "unknown": row[1] for row in result}

    return {
        "total": total,
        "pain_pulse": by_stream.get("pain_pulse", 0),
        "competitor_move": by_stream.get("competitor_move", 0),
        "opportunity_signal": by_stream.get("opportunity_signal", 0),
        "by_stream": by_stream,
    }


@router.get("")
async def list_signals(
    stream: str | None = Query(None, description="Filter by stream name"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of signals, newest first."""
    stmt = select(Signal).order_by(Signal.collected_at.desc()).limit(limit).offset(offset)
    count_stmt = select(func.count(Signal.id))

    if stream:
        stmt = stmt.where(Signal.stream == stream)
        count_stmt = count_stmt.where(Signal.stream == stream)

    signals = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(s.id),
                "stream": s.stream,
                "source": s.source,
                "source_url": s.source_url,
                "snippet": (s.raw_content or "")[:200],
                "author": s.author,
                "language": s.language,
                "collected_at": s.collected_at,
                "is_processed": s.is_processed,
                "is_duplicate": s.is_duplicate,
                "created_at": s.created_at,
            }
            for s in signals
        ],
    }
