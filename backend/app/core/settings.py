"""
settings.py
-----------
Environment-backed application settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)
DEFAULT_ALLOWED_METHODS = ("GET", "POST", "OPTIONS")
DEFAULT_ALLOWED_HEADERS = (
    "Accept",
    "Authorization",
    "Content-Type",
    "Origin",
    "X-Requested-With",
)


def _parse_csv_values(raw: str, setting_name: str) -> list[str]:
    values = [value.strip() for value in raw.split(",") if value.strip()]
    if not values:
        raise ValueError(f"{setting_name} must contain at least one value.")

    if any(value == "*" for value in values):
        raise ValueError(f"{setting_name} cannot contain wildcard '*' values.")

    return values


def _parse_positive_int(raw: str, setting_name: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{setting_name} must be an integer; got {raw!r}.") from exc

    if value <= 0:
        raise ValueError(f"{setting_name} must be greater than 0; got {value}.")

    return value


@dataclass(frozen=True)
class Settings:
    cors_allowed_origins: list[str]
    cors_allowed_methods: list[str]
    cors_allowed_headers: list[str]
    max_upload_bytes: int
    upload_chunk_size: int


def get_settings() -> Settings:
    try:
        max_upload_bytes = _parse_positive_int(
            os.getenv("CAD_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)),
            "CAD_MAX_UPLOAD_BYTES",
        )
        upload_chunk_size = _parse_positive_int(
            os.getenv("CAD_UPLOAD_CHUNK_SIZE", str(1024 * 1024)),
            "CAD_UPLOAD_CHUNK_SIZE",
        )
    except ValueError as exc:
        raise RuntimeError(f"Invalid application settings: {exc}") from exc

    if upload_chunk_size > max_upload_bytes:
        raise RuntimeError(
            "Invalid application settings: CAD_UPLOAD_CHUNK_SIZE must be less than or "
            "equal to CAD_MAX_UPLOAD_BYTES."
        )

    try:
        return Settings(
            cors_allowed_origins=_parse_csv_values(
                os.getenv(
                    "CAD_CORS_ALLOWED_ORIGINS",
                    ",".join(DEFAULT_ALLOWED_ORIGINS),
                ),
                "CAD_CORS_ALLOWED_ORIGINS",
            ),
            cors_allowed_methods=_parse_csv_values(
                os.getenv(
                    "CAD_CORS_ALLOWED_METHODS",
                    ",".join(DEFAULT_ALLOWED_METHODS),
                ),
                "CAD_CORS_ALLOWED_METHODS",
            ),
            cors_allowed_headers=_parse_csv_values(
                os.getenv(
                    "CAD_CORS_ALLOWED_HEADERS",
                    ",".join(DEFAULT_ALLOWED_HEADERS),
                ),
                "CAD_CORS_ALLOWED_HEADERS",
            ),
            max_upload_bytes=max_upload_bytes,
            upload_chunk_size=upload_chunk_size,
        )
    except ValueError as exc:
        raise RuntimeError(f"Invalid application settings: {exc}") from exc


settings = get_settings()
