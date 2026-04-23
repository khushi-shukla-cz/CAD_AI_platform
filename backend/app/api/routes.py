"""
routes.py
---------
FastAPI router for the CAD analysis API.
"""

import os
import uuid
import tempfile
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.settings import settings
from app.services.cad_parser import parse_stl
from app.services.validation_engine import validate_geometry
from app.models.schemas import AnalyzeResponse, CADResponse, ValidationResponse

logger = logging.getLogger(__name__)

router = APIRouter()
MAX_UPLOAD_BYTES = settings.max_upload_bytes
UPLOAD_CHUNK_SIZE = settings.upload_chunk_size


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze an STL file",
    description=(
        "Upload an STL file to receive geometry metadata and a list of "
        "validation issues (e.g. watertight check, complexity grading)."
    ),
    status_code=status.HTTP_200_OK,
)
async def analyze_stl(file: UploadFile = File(..., description="STL file to analyze")) -> AnalyzeResponse:
    """
    Accept an STL upload, parse geometry, run validation, and return results.

    Args:
        file: The uploaded STL file (ASCII or binary).

    Returns:
        AnalyzeResponse containing geometry metadata and validation issues.

    Raises:
        422 Unprocessable Entity: If the uploaded file is not an .stl file.
        500 Internal Server Error: If parsing or validation fails unexpectedly.
    """
    _validate_upload(file)

    tmp_path = await _save_temp_file(file)
    try:
        parsed = _run_parse(tmp_path)
        validation = _run_validation(parsed)
    finally:
        _cleanup(tmp_path)

    return AnalyzeResponse(
        geometry=CADResponse(**parsed),
        validation=ValidationResponse(**validation),
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _validate_upload(file: UploadFile) -> None:
    """Raise 422 if the uploaded file does not have an .stl extension."""
    filename = file.filename or ""
    if not filename.lower().endswith(".stl"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid file type '{filename}'. Only .stl files are accepted.",
        )


async def _save_temp_file(file: UploadFile) -> str:
    """
    Write the uploaded file to a named temp file and return its path.

    A UUID suffix is added to prevent collisions under concurrent requests.
    """
    suffix = f"_{uuid.uuid4().hex}.stl"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    total_bytes = 0
    try:
        while True:
            chunk = await file.read(UPLOAD_CHUNK_SIZE)
            if not chunk:
                break

            total_bytes += len(chunk)
            if total_bytes > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        "Uploaded file is too large. "
                        f"Maximum allowed size is {MAX_UPLOAD_BYTES} bytes."
                    ),
                )

            tmp.write(chunk)

        tmp.flush()
    finally:
        tmp.close()

    logger.debug("Uploaded file saved temporarily at: %s", tmp.name)
    return tmp.name


def _run_parse(tmp_path: str) -> dict:
    """Call parse_stl and convert ValueError / FileNotFoundError to HTTP 422."""
    try:
        return parse_stl(tmp_path)
    except (FileNotFoundError, ValueError) as exc:
        logger.warning("STL parse error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during STL parsing.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while parsing the STL file.",
        ) from exc


def _run_validation(parsed: dict) -> dict:
    """Call validate_geometry and wrap unexpected errors as HTTP 500."""
    try:
        return validate_geometry(parsed)
    except Exception as exc:
        logger.exception("Unexpected error during geometry validation.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during geometry validation.",
        ) from exc


def _cleanup(path: str) -> None:
    """Silently remove a temporary file, logging any failure."""
    try:
        os.unlink(path)
        logger.debug("Temporary file removed: %s", path)
    except OSError as exc:
        logger.warning("Could not remove temporary file '%s': %s", path, exc)