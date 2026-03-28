"""
cad_parser.py
-------------
Service module for parsing STL files using trimesh.
Provides structured geometric metadata extraction.
"""

import os
import logging
from typing import Any

import trimesh

logger = logging.getLogger(__name__)


def _load_mesh(file_path: str) -> trimesh.Trimesh:
    """
    Load and validate an STL file from disk.

    Args:
        file_path: Absolute or relative path to the STL file.

    Returns:
        A trimesh.Trimesh object.

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
        ValueError: If the file cannot be parsed or is not a valid mesh.
    """
    if not file_path.lower().endswith(".stl"):
        raise ValueError(
            f"Unsupported file type: '{file_path}'. Only .stl files are supported."
        )

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"STL file not found: {file_path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")

    try:
        mesh = trimesh.load(file_path, force="mesh")
    except Exception as exc:
        raise ValueError(f"Failed to parse STL file '{file_path}': {exc}") from exc

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(
            f"Loaded geometry is not a triangle mesh (got {type(mesh).__name__}). "
            "Ensure the file contains a single solid STL mesh."
        )

    if mesh.is_empty:
        raise ValueError(f"Mesh loaded from '{file_path}' is empty (no faces or vertices).")

    if mesh.faces.shape[0] == 0:
        raise ValueError(f"Mesh loaded from '{file_path}' has no faces.")

    if not mesh.is_winding_consistent:
        logger.warning(
            "Mesh winding is inconsistent in '%s'. "
            "Volume and inside/outside checks may be unreliable.",
            file_path,
        )

    return mesh


def _round_list(values: list[float], precision: int = 4) -> list[float]:
    """
    Round each float in a list to a given decimal precision.

    Args:
        values: List of raw float values.
        precision: Number of decimal places to keep (default: 4).

    Returns:
        A new list with each value rounded to *precision* decimal places.
    """
    return [round(v, precision) for v in values]


def _extract_bounding_box(mesh: trimesh.Trimesh) -> dict[str, list[float]]:
    """
    Extract the axis-aligned bounding box of the mesh.

    Args:
        mesh: A valid trimesh.Trimesh object.

    Returns:
        Dictionary with 'min' and 'max' keys, each a list of three floats
        [x, y, z] rounded to 4 decimal places.
    """
    bounds = mesh.bounds  # shape (2, 3): [[xmin, ymin, zmin], [xmax, ymax, zmax]]
    return {
        "min": _round_list(bounds[0].tolist()),
        "max": _round_list(bounds[1].tolist()),
    }


def _extract_geometry_stats(mesh: trimesh.Trimesh) -> dict[str, Any]:
    """
    Extract core geometric statistics from a mesh.

    Args:
        mesh: A valid trimesh.Trimesh object.

    Returns:
        Dictionary containing face count, vertex count, surface area, and volume.
        Volume is None when the mesh is not watertight (open surface).
    """
    is_watertight = mesh.is_watertight

    return {
        "num_faces": len(mesh.faces),
        "num_vertices": len(mesh.vertices),
        "surface_area": float(mesh.area),
        # Volume is only physically meaningful for closed (watertight) meshes.
        "volume": float(mesh.volume) if is_watertight else None,
        "is_watertight": is_watertight,
        # Rough complexity indicator: faces per 1000. Useful for downstream
        # decisions (e.g. whether to offload processing to a background task).
        "complexity_score": round(len(mesh.faces) / 1000, 4),
    }


def parse_stl(file_path: str) -> dict[str, Any]:
    """
    Parse an STL file and return a structured dictionary of geometric metadata.

    Extracted fields
    ----------------
    - num_faces      (int)   : Number of triangular faces in the mesh.
    - num_vertices   (int)   : Number of unique vertices.
    - bounding_box   (dict)  : Axis-aligned bounding box with 'min' and 'max'
                               keys, each a list of three floats [x, y, z].
    - surface_area   (float) : Total surface area in the file's native units.
    - volume         (float | None) : Enclosed volume for watertight meshes;
                               None if the mesh is an open surface.
    - is_watertight     (bool)  : Whether the mesh forms a closed solid.
    - complexity_score  (float) : Face count divided by 1000; a lightweight
                                  proxy for mesh complexity.

    .. note::
        STL files carry no unit metadata. All dimensional values (bounding box,
        surface area, volume) are expressed in whatever units the authoring tool
        used. A warning is logged as a reminder on every parse.

    .. note::
        For very large meshes ``trimesh.load`` can be slow. Consider offloading
        calls to a background task queue (e.g. Celery) when ``complexity_score``
        exceeds your latency budget.

    Args:
        file_path: Path to the STL file (ASCII or binary format).

    Returns:
        A dictionary with the keys described above plus a top-level
        ``"file_path"`` entry echoing the resolved input path.

    Raises:
        FileNotFoundError: If no file exists at *file_path*.
        ValueError: If *file_path* is not an .stl file, cannot be parsed,
                    or results in an empty / face-less mesh.

    Example::

        >>> result = parse_stl("part.stl")
        >>> result["num_faces"]
        2048
        >>> result["bounding_box"]
        {'min': [0.0, 0.0, 0.0], 'max': [10.0, 5.0, 3.0]}
        >>> result["complexity_score"]
        2.048
    """
    resolved_path = os.path.realpath(file_path)
    logger.info("Parsing STL file: %s", resolved_path)

    # Fix 4 — STL carries no unit metadata; log a reminder on every parse.
    logger.warning(
        "STL units are assumed (no unit metadata present in '%s'). "
        "Ensure the source tool's units are known before using dimensional values.",
        resolved_path,
    )

    mesh = _load_mesh(resolved_path)

    geometry_stats = _extract_geometry_stats(mesh)
    bounding_box = _extract_bounding_box(mesh)

    result: dict[str, Any] = {
        "file_path": resolved_path,
        **geometry_stats,
        "bounding_box": bounding_box,
    }

    logger.info(
        "Parsed '%s' — faces: %d, vertices: %d, watertight: %s",
        resolved_path,
        result["num_faces"],
        result["num_vertices"],
        result["is_watertight"],
    )

    return result