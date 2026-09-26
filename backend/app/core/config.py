"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv


# backend/app/core/config.py
# parents[3] resolves to the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Application settings loaded from environment variables."""

    PROJECT_NAME: str = "Digitomics Workflow Builder"
    API_V1_PREFIX: str = "/api"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://workflow:workflow@localhost:5432/workflow_builder",
    )

    LLM_PROVIDER: str = os.getenv(
        "LLM_PROVIDER",
        "rule_based",
    )

    OPENAI_API_KEY: str = os.getenv(
        "OPENAI_API_KEY",
        "",
    )

    OPENAI_MODEL: str = os.getenv(
        "OPENAI_MODEL",
        "gpt-4o-mini",
    )

    LLM_TIMEOUT_SECONDS: int = int(
        os.getenv("LLM_TIMEOUT_SECONDS", "30")
    )

    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")

    @property
    def async_database_url(self) -> str:
        """Async SQLAlchemy database URL."""

        return self.DATABASE_URL.replace(
            "postgresql+psycopg://",
            "postgresql+asyncpg://",
        )


settings = Settings()