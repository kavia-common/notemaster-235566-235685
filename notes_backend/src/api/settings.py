import os
from dataclasses import dataclass
from typing import List, Optional


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
        """
        raw = (self.postgres_url or "").strip()

        # If it's already a full URI, normalize postgres -> postgresql for SQLAlchemy.
        if raw.startswith("postgresql://") or raw.startswith("postgres://"):
            if raw.startswith("postgres://"):
                return "postgresql://" + raw[len("postgres://") :]
            return raw

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
