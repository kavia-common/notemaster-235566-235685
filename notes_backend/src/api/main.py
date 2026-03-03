from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import init_db
from src.api.routers.notes import router as notes_router
from src.api.routers.search import router as search_router
from src.api.routers.tags import router as tags_router
from src.api.settings import get_settings

openapi_tags = [
    {"name": "health", "description": "Service health checks."},
    {"name": "notes", "description": "Create, update, delete, list, pin/unpin notes; manage tag assignment."},
    {"name": "tags", "description": "Tag operations and discovery."},
    {"name": "search", "description": "Search notes by title/content with optional filters."},
]

settings = get_settings()

app = FastAPI(
    title="Notemaster Notes API",
    description=(
        "Backend API for a notes application. Supports notes CRUD, tags, pinning, and search. "
        "Connects to Postgres using environment-based configuration."
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# CORS so the Next.js frontend can call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
    max_age=settings.cors_max_age,
)

# Ensure tables exist on startup (simple approach for this template)
init_db()

app.include_router(notes_router)
app.include_router(tags_router)
app.include_router(search_router)


@app.get(
    "/",
    tags=["health"],
    summary="Health check",
    description="Basic health check endpoint.",
    operation_id="health_check",
)
def health_check():
    """Return a simple JSON health status."""
    return {"message": "Healthy"}
