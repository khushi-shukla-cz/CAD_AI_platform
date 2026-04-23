"""
schemas.py
----------
Pydantic models for request/response validation across the API.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Geometry (parse_stl output)
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    min: list[float] = Field(..., description="Minimum corner [x, y, z]")
    max: list[float] = Field(..., description="Maximum corner [x, y, z]")


class CADResponse(BaseModel):
    file_path: str = Field(..., description="Resolved absolute path of the parsed file")
    num_faces: int = Field(..., ge=0, description="Number of triangular faces")
    num_vertices: int = Field(..., ge=0, description="Number of unique vertices")
    surface_area: float = Field(..., ge=0.0, description="Total surface area (native units)")
    volume: float | None = Field(None, description="Enclosed volume; None if mesh is not watertight")
    is_watertight: bool = Field(..., description="Whether the mesh forms a closed solid")
    complexity_score: float = Field(..., ge=0.0, description="Face count / 1000")
    bounding_box: BoundingBox


# ---------------------------------------------------------------------------
# Validation (validate_geometry output)
# ---------------------------------------------------------------------------

SeverityLevel = Literal["LOW", "MEDIUM", "HIGH"]


class ValidationIssue(BaseModel):
    type: str = Field(..., description="Machine-readable issue identifier")
    severity: SeverityLevel = Field(..., description="Issue severity level")
    message: str = Field(..., description="Human-readable description of the issue")


class ValidationSummary(BaseModel):
    design_quality: str = Field(..., description="Overall design quality label")
    risk_level: str = Field(..., description="Estimated risk level")
    recommendation: str = Field(..., description="Human-readable next-step recommendation")


class ValidationResponse(BaseModel):
    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="List of validation issues found in the mesh",
    )
    summary: ValidationSummary
    confidence_score: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Combined analysis response
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    geometry: CADResponse
    validation: ValidationResponse