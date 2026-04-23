"""
settings.py
-----------
Environment-backed application settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _parse_allowed_origins(raw: str) -> list[str]:
    values = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return values or ["*"]


@dataclass(frozen=True)
class Settings:
    cors_allowed_origins: list[str]
    max_upload_bytes: int
    upload_chunk_size: int


def get_settings() -> Settings:
    return Settings(
        cors_allowed_origins=_parse_allowed_origins(
            os.getenv("CAD_CORS_ALLOWED_ORIGINS", "*")
        ),
        max_upload_bytes=int(os.getenv("CAD_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
        upload_chunk_size=int(os.getenv("CAD_UPLOAD_CHUNK_SIZE", str(1024 * 1024))),
    )


settings = get_settings()
