from fastapi.testclient import TestClient

from app.api import routes
from main import app


client = TestClient(app)


def test_analyze_stl_success(monkeypatch):
    parsed = {
        "file_path": "C:/tmp/part.stl",
        "num_faces": 10,
        "num_vertices": 12,
        "surface_area": 24.5,
        "volume": 10.0,
        "is_watertight": True,
        "complexity_score": 0.01,
        "bounding_box": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 1.0]},
    }
    validation = {
        "issues": [],
        "summary": {
            "design_quality": "GOOD",
            "risk_level": "LOW",
            "recommendation": "Suitable for standard use",
        },
        "confidence_score": 0.85,
    }

    monkeypatch.setattr(routes, "parse_stl", lambda _path: parsed)
    monkeypatch.setattr(routes, "validate_geometry", lambda _data: validation)

    response = client.post(
        "/api/v1/analyze",
        files={"file": ("part.stl", b"solid part", "model/stl")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["geometry"]["num_faces"] == 10
    assert payload["validation"]["confidence_score"] == 0.85
    assert payload["validation"]["summary"]["risk_level"] == "LOW"


def test_analyze_rejects_non_stl():
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("part.txt", b"not-an-stl", "text/plain")},
    )

    assert response.status_code == 422
    assert "Only .stl files are accepted" in response.json()["detail"]


def test_analyze_rejects_large_file(monkeypatch):
    monkeypatch.setattr(routes, "MAX_UPLOAD_BYTES", 4)

    response = client.post(
        "/api/v1/analyze",
        files={"file": ("part.stl", b"12345", "model/stl")},
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()
