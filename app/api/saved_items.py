from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.base import get_db
from app.models.saved_item import SavedItem
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/saved-items", tags=["saved-items"])

class SavedItemCreate(BaseModel):
    item_type: str = Field(..., max_length=50)
    item_id: str | None = None
    title: str | None = None
    content: dict | None = None

class SavedItemResponse(SavedItemCreate):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("", response_model=SavedItemResponse)
def save_item(item_in: SavedItemCreate, db: Session = Depends(get_db)) -> Any:
    """Save an item from the dashboard or platform."""
    # Optional: check if already saved
    if item_in.item_id:
        existing = db.execute(
            select(SavedItem).where(
                SavedItem.item_type == item_in.item_type,
                SavedItem.item_id == item_in.item_id
            )
        ).scalar_one_or_none()
        if existing:
            return existing

    item = SavedItem(
        item_type=item_in.item_type,
        item_id=item_in.item_id,
        title=item_in.title,
        content=item_in.content
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("", response_model=List[SavedItemResponse])
def get_saved_items(
    skip: int = 0, limit: int = 50, item_type: str | None = None, db: Session = Depends(get_db)
) -> Any:
    """Get all saved items, ordered by newest first."""
    stmt = select(SavedItem).order_by(desc(SavedItem.created_at)).offset(skip).limit(limit)
    if item_type:
        stmt = stmt.where(SavedItem.item_type == item_type)
    
    items = db.execute(stmt).scalars().all()
    return items

@router.delete("/{item_id}")
def delete_saved_item(item_id: UUID, db: Session = Depends(get_db)) -> Any:
    """Remove a saved item."""
    item = db.get(SavedItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Saved item not found")
    
    db.delete(item)
    db.commit()
    return {"status": "ok"}
