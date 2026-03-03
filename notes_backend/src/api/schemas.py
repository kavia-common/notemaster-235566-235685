from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TagOut(BaseModel):
    id: int = Field(..., description="Tag ID.")
    name: str = Field(..., description="Tag name.")

    model_config = {"from_attributes": True}


class NoteOut(BaseModel):
    id: int = Field(..., description="Note ID.")
    title: str = Field(..., description="Note title.")
    content: str = Field(..., description="Note content.")
    pinned: bool = Field(..., description="Whether the note is pinned.")
    tags: List[TagOut] = Field(default_factory=list, description="Tags assigned to the note.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")

    model_config = {"from_attributes": True}


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Note title.")
    content: str = Field("", max_length=20000, description="Note content.")
    pinned: bool = Field(False, description="Whether the note is pinned.")
    tags: List[str] = Field(default_factory=list, description="Optional list of tag names to assign.")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        clean = []
        for t in v:
            t = t.strip()
            if not t:
                continue
            if len(t) > 64:
                raise ValueError("Tag names must be <= 64 characters.")
            clean.append(t)
        # De-duplicate while preserving order
        deduped = list(dict.fromkeys(clean))
        if len(deduped) > 50:
            raise ValueError("Too many tags; max 50.")
        return deduped


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated title.")
    content: Optional[str] = Field(None, max_length=20000, description="Updated content.")
    pinned: Optional[bool] = Field(None, description="Updated pinned status.")
    tags: Optional[List[str]] = Field(None, description="Replace tags with this list of tag names.")


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="New tag name.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tag name cannot be blank.")
        return v


class SearchResponse(BaseModel):
    query: str = Field(..., description="Search query used.")
    results: List[NoteOut] = Field(..., description="Matched notes.")
