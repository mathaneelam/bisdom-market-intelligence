import io
import logging
from datetime import datetime, timezone

import instaloader
from sqlalchemy import select

from app.models.base import AsyncSessionLocal
from app.models.instagram_session import InstagramSession

logger = logging.getLogger(__name__)


async def load_session_from_db(L: instaloader.Instaloader, username: str) -> bool:
    """Load a previously saved Instagram session from the database, if one exists.

    Lets the session survive redeploys/restarts on hosts with an ephemeral
    filesystem (Railway, Render), where the local instaloader session file
    written by the import scripts would otherwise be lost.
    """
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(select(InstagramSession).where(InstagramSession.username == username))
        ).scalars().first()

    if not row:
        return False

    L.context.load_session_from_file(username, io.BytesIO(row.session_data))
    return True


async def save_session_to_db(L: instaloader.Instaloader, username: str) -> None:
    """Persist the current Instagram session to the database."""
    buf = io.BytesIO()
    L.context.save_session_to_file(buf)
    data = buf.getvalue()

    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(select(InstagramSession).where(InstagramSession.username == username))
        ).scalars().first()

        if row:
            row.session_data = data
            row.updated_at = datetime.now(timezone.utc)
        else:
            db.add(InstagramSession(username=username, session_data=data))

        await db.commit()

    logger.info("Instagram session for '%s' saved to database.", username)
