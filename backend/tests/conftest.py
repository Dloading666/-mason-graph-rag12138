"""Pytest fixtures for API testing."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.server.api.main import app  # noqa: E402


def auth_headers(username: str = "admin", password: str = "Admin@123") -> dict[str, str]:
    client = TestClient(app)
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

