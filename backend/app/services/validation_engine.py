"""
validation_engine.py
--------------------
Validates parsed STL geometry data and returns a structured list of issues.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Severity constants
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"


def _check_watertight(parsed_data: dict) -> dict[str, str] | None:
    """
    Return a HIGH severity issue if the mesh is not watertight.

    Args:
        parsed_data: Output dict from parse_stl().

    Returns:
        An issue dict, or None if the mesh is watertight.
    """
    if not parsed_data.get("is_watertight", True):
        return {
            "type": "non_watertight_mesh",
            "severity": HIGH,
            "message": (
                "Mesh is not watertight. "
                "This may cause manufacturing or simulation issues."
            ),
        }
    return None


def _check_complexity(parsed_data: dict) -> dict[str, str]:
    """
    Return a severity-graded issue based on complexity_score.

    Thresholds:
        score > 5   → HIGH
        2 < score ≤ 5 → MEDIUM
        score ≤ 2   → LOW

    Args:
        parsed_data: Output dict from parse_stl().

    Returns:
        An issue dict describing the complexity level.
    """
    score: float = parsed_data.get("complexity_score", 0.0)

    if score > 5:
        severity = HIGH
        message = (
            f"Geometry complexity is very high (score: {score}). "
            "Consider decimating the mesh before manufacturing or simulation."
        )
    elif score > 2:
        severity = MEDIUM
        message = (
            f"Geometry complexity is moderate (score: {score}). "
            "Review mesh density if performance is a concern."
        )
    else:
        severity = LOW
        message = f"Geometry complexity is within acceptable range (score: {score})."

    return {
        "type": "geometry_complexity",
        "severity": severity,
        "message": message,
    }


def validate_geometry(parsed_data: dict[str, Any]) -> dict[str, Any]:
    """
    Run all geometry validations against parsed STL data.

    Validations performed
    ---------------------
    - Watertight check: flags open meshes as HIGH severity.
    - Complexity check: grades mesh density as LOW / MEDIUM / HIGH.

    Args:
        parsed_data: The dictionary returned by ``parse_stl()``.

    Returns:
        A dict with ``"issues"``, ``"summary"``, and ``"confidence_score"``.
        Each issue has the keys ``type``, ``severity``, and ``message``.

    Example::

        >>> result = validate_geometry(parsed_data)
        >>> result["issues"][0]["severity"]
        'HIGH'
    """
    issues: list[dict] = []

    watertight_issue = _check_watertight(parsed_data)
    if watertight_issue:
        issues.append(watertight_issue)

    issues.append(_check_complexity(parsed_data))

    logger.info(
        "Validation complete — %d issue(s) found (%d HIGH).",
        len(issues),
        sum(1 for i in issues if i["severity"] == HIGH),
    )

    return {
        "issues": issues,
        "summary": generate_summary(parsed_data, issues),
        "confidence_score": 0.85,
    }


def generate_summary(parsed_data, issues):
    if not parsed_data["is_watertight"]:
        return {
            "design_quality": "POOR",
            "risk_level": "HIGH",
            "recommendation": "Fix mesh before manufacturing"
        }

    if parsed_data["complexity_score"] > 5:
        return {
            "design_quality": "COMPLEX",
            "risk_level": "MEDIUM",
            "recommendation": "May increase manufacturing cost"
        }

    return {
        "design_quality": "GOOD",
        "risk_level": "LOW",
        "recommendation": "Suitable for standard use"
    }