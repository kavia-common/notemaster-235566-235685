from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.api.db import Note, Tag, get_db
from src.api.schemas import NoteCreate, NoteOut, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


def _get_or_create_tags(db: Session, names: List[str]) -> List[Tag]:
    tags: List[Tag] = []
    for name in names:
        existing = db.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()
        if existing:
            tags.append(existing)
        else:
            t = Tag(name=name)
            db.add(t)
            db.flush()  # get id
            tags.append(t)
    return tags


@router.get(
    "",
    response_model=List[NoteOut],
    summary="List notes",
    description="List notes with optional filters (pinned, tag). Sorted by pinned desc then updated_at desc.",
    operation_id="list_notes",
)
def list_notes(
    pinned: Optional[bool] = Query(None, description="If set, filter by pinned status."),
    tag: Optional[str] = Query(None, description="If set, filter notes that contain this tag name."),
    db: Session = Depends(get_db),
) -> List[Note]:
    stmt = select(Note)

    if pinned is not None:
        stmt = stmt.where(Note.pinned == pinned)

    if tag:
        stmt = stmt.join(Note.tags).where(Tag.name == tag.strip())

    stmt = stmt.order_by(desc(Note.pinned), desc(Note.updated_at), desc(Note.id))
    return list(db.execute(stmt).scalars().all())


@router.post(
    "",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Create a new note. Optionally assigns tags by name and sets pinned status.",
    operation_id="create_note",
)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> Note:
    note = Note(title=payload.title.strip(), content=payload.content, pinned=payload.pinned)
    if payload.tags:
        note.tags = _get_or_create_tags(db, payload.tags)

    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get(
    "/{note_id}",
    response_model=NoteOut,
    summary="Get note",
    description="Fetch a single note by ID.",
    operation_id="get_note",
)
def get_note(note_id: int, db: Session = Depends(get_db)) -> Note:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    return note


@router.put(
    "/{note_id}",
    response_model=NoteOut,
    summary="Update note",
    description="Update note fields. If tags is provided, it replaces the note's tags list.",
    operation_id="update_note",
)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)) -> Note:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")

    if payload.title is not None:
        note.title = payload.title.strip()
    if payload.content is not None:
        note.content = payload.content
    if payload.pinned is not None:
        note.pinned = payload.pinned

    if payload.tags is not None:
        # Normalize and validate similarly to NoteCreate
        clean = []
        for t in payload.tags:
            t = (t or "").strip()
            if not t:
                continue
            if len(t) > 64:
                raise HTTPException(status_code=422, detail="Tag names must be <= 64 characters.")
            clean.append(t)
        clean = list(dict.fromkeys(clean))
        note.tags = _get_or_create_tags(db, clean)

    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete note",
    description="Delete a note by ID.",
    operation_id="delete_note",
)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> Response:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    db.delete(note)
    db.commit()
    # Explicit empty 204 response to satisfy FastAPI's "no response body for 204" constraint.
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{note_id}/pin",
    response_model=NoteOut,
    summary="Pin a note",
    description="Set pinned=true for the note.",
    operation_id="pin_note",
)
def pin_note(note_id: int, db: Session = Depends(get_db)) -> Note:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    note.pinned = True
    db.commit()
    db.refresh(note)
    return note


@router.post(
    "/{note_id}/unpin",
    response_model=NoteOut,
    summary="Unpin a note",
    description="Set pinned=false for the note.",
    operation_id="unpin_note",
)
def unpin_note(note_id: int, db: Session = Depends(get_db)) -> Note:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    note.pinned = False
    db.commit()
    db.refresh(note)
    return note
