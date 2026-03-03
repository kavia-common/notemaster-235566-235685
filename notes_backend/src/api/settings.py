import os
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    """Strongly-typed settings loaded from environment variables."""

    # CORS
    allowed_origins: List[str]
    allowed_methods: List[str]
    allowed_headers: List[str]
    cors_max_age: int

    # Postgres
    postgres_url: Optional[str]
    postgres_user: Optional[str]
    postgres_password: Optional[str]
    postgres_db: Optional[str]
    postgres_port: Optional[str]

    @property
    def sqlalchemy_database_url(self) -> str:
        """
        Build a SQLAlchemy database URL from environment variables.

        Priority:
        1) POSTGRES_URL (if provided). Can be either:
           - "postgresql://user:pass@host:port/db"
           - "postgres://user:pass@host:port/db"
           - or host-only / host:port; then other vars are used.
        2) POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT
           with host from POSTGRES_URL (if it's host-only) or "localhost".

        Important: if POSTGRES_URL is a URI but *does not* include credentials,
        we will inject POSTGRES_USER/POSTGRES_PASSWORD to avoid psycopg2 defaulting
        to the OS user (e.g. "kavia"), which commonly fails in container setups.
        """
        raw = (self.postgres_url or "").strip()

        # If it's already a URI, normalize postgres -> postgresql for SQLAlchemy.
        if raw.startswith("postgresql://") or raw.startswith("postgres://"):
            normalized = raw
            if normalized.startswith("postgres://"):
                normalized = "postgresql://" + normalized[len("postgres://") :]

            parsed = urlparse(normalized)

            # If URI has no username, inject from env to avoid OS-user fallback.
            if not parsed.username:
                user = self.postgres_user or "postgres"
                password = self.postgres_password or ""
                # parsed.hostname can be None if the URL is malformed; fall back.
                host = parsed.hostname or "localhost"
                port = parsed.port or int(self.postgres_port or "5432")

                # Keep db name from URI if present, else take from env/default.
                db = (parsed.path or "").lstrip("/") or (self.postgres_db or "postgres")

                auth = f"{user}:{password}@" if password else f"{user}@"
                return f"postgresql://{auth}{host}:{port}/{db}"

            return normalized

        host = raw or "localhost"
        port = self.postgres_port or "5432"
        user = self.postgres_user or "postgres"
        password = self.postgres_password or ""
        db = self.postgres_db or "postgres"

        auth = f"{user}:{password}@" if password else f"{user}@"
        return f"postgresql://{auth}{host}:{port}/{db}"


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load settings from environment variables for use by the app."""
    return Settings(
        allowed_origins=_split_csv(os.getenv("ALLOWED_ORIGINS")) or ["*"],
        allowed_methods=_split_csv(os.getenv("ALLOWED_METHODS")) or ["*"],
        allowed_headers=_split_csv(os.getenv("ALLOWED_HEADERS")) or ["*"],
        cors_max_age=int(os.getenv("CORS_MAX_AGE", "600")),
        postgres_url=os.getenv("POSTGRES_URL"),
        postgres_user=os.getenv("POSTGRES_USER"),
        postgres_password=os.getenv("POSTGRES_PASSWORD"),
        postgres_db=os.getenv("POSTGRES_DB"),
        postgres_port=os.getenv("POSTGRES_PORT"),
    )
