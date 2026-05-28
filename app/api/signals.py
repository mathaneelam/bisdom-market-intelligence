from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.signal import Signal

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/stats")
async def signal_stats(db: AsyncSession = Depends(get_db)):
    """Counts by stream — used by the Dashboard summary cards."""
    result = await db.execute(
        select(Signal.stream, func.count(Signal.id)).group_by(Signal.stream)
    )
    by_stream = {row[0] or "unknown": row[1] for row in result}
    return {
        "total": sum(by_stream.values()),
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
