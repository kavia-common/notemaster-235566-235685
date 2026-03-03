from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from src.api.db import Note, Tag, get_db
from src.api.schemas import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search notes",
    description="Search notes by query over title/content (case-insensitive). Optional filters: pinned and tag.",
    operation_id="search_notes",
)
def search_notes(
    q: str = Query(..., min_length=1, max_length=200, description="Search query string."),
    pinned: Optional[bool] = Query(None, description="If set, filter by pinned status."),
    tag: Optional[str] = Query(None, description="If set, filter notes that contain this tag name."),
    limit: int = Query(50, ge=1, le=200, description="Max number of results to return."),
    db: Session = Depends(get_db),
) -> SearchResponse:
    query = q.strip()
    like = f"%{query}%"

    stmt = select(Note).where(or_(Note.title.ilike(like), Note.content.ilike(like)))

    if pinned is not None:
        stmt = stmt.where(Note.pinned == pinned)

    if tag:
        stmt = stmt.join(Note.tags).where(Tag.name == tag.strip())

    stmt = stmt.order_by(desc(Note.pinned), desc(Note.updated_at), desc(Note.id)).limit(limit)
    results: List[Note] = list(db.execute(stmt).scalars().all())
    return SearchResponse(query=query, results=results)
