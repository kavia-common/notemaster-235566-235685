from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session

from src.api.db import Tag, get_db
from src.api.schemas import TagCreate, TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get(
    "",
    response_model=List[TagOut],
    summary="List tags",
    description="List all tags sorted by name.",
    operation_id="list_tags",
)
def list_tags(db: Session = Depends(get_db)) -> List[Tag]:
    stmt = select(Tag).order_by(asc(func.lower(Tag.name)), asc(Tag.id))
    return list(db.execute(stmt).scalars().all())


@router.post(
    "",
    response_model=TagOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
    description="Create a tag if it does not exist. Returns existing tag if already created.",
    operation_id="create_tag",
)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)) -> Tag:
    existing = db.execute(select(Tag).where(Tag.name == payload.name)).scalar_one_or_none()
    if existing:
        return existing

    tag = Tag(name=payload.name)
    db.add(tag)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # If a race condition caused unique violation, try fetch again.
        existing = db.execute(select(Tag).where(Tag.name == payload.name)).scalar_one_or_none()
        if existing:
            return existing
        raise HTTPException(status_code=500, detail="Could not create tag.")
    db.refresh(tag)
    return tag
