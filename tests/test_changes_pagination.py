"""Tests for pagination and sorting on the /v1/changes endpoint."""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta
from typing import Iterable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import regradar.database as db


def _seed_changes(session: db.SessionLocal, count: int = 3) -> None:
    """Populate the database with a predictable set of changes."""

    source = db.Source(name="Test Source", url="https://example.com")
    session.add(source)
    session.flush()

    base_time = datetime(2024, 1, 1, 12, 0, 0)
    for idx in range(count):
        created_at = base_time + timedelta(hours=idx)
        document = db.Document(
            external_id=f"doc-{idx}",
            source_id=source.id,
            created_at=created_at,
        )
        session.add(document)
        session.flush()

        version = db.DocumentVersion(
            document_id=document.id,
            content_hash=f"hash-{idx}",
            content=f"content {idx}",
            created_at=created_at,
        )
        session.add(version)
        session.flush()

        change = db.ChangeEvent(
            document_version_id=version.id,
            diff=f"diff {idx}",
            created_at=created_at,
        )
        session.add(change)

        session.add(
            db.ImpactAssessment(
                document_version_id=version.id,
                summary=f"Summary {idx}",
                actions=f"Actions {idx}",
                score=float(idx),
                created_at=created_at,
            )
        )

    session.commit()


@pytest.fixture
def api_context(tmp_path, monkeypatch):
    """Provide a FastAPI test client backed by an isolated database."""

    engine = create_engine(f"sqlite:///{tmp_path/'test.db'}", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db.Base.metadata.create_all(engine)

    monkeypatch.setattr(db, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.delenv("API_KEY", raising=False)

    api_module = importlib.reload(importlib.import_module("regradar.api"))

    yield {
        "client": TestClient(api_module.app),
        "SessionLocal": TestingSessionLocal,
    }

    importlib.reload(importlib.import_module("regradar.api"))


def _collect_scores(items: Iterable[dict]) -> list[float]:
    return [item["score"] for item in items]


def test_changes_endpoint_supports_pagination(api_context):
    session = api_context["SessionLocal"]()
    try:
        _seed_changes(session, count=3)
    finally:
        session.close()

    client = api_context["client"]

    response = client.get("/v1/changes", params={"limit": 2, "offset": 0})
    assert response.status_code == 200
    payload = response.json()

    assert len(payload["items"]) == 2
    assert payload["pagination"] == {
        "total": 3,
        "limit": 2,
        "offset": 0,
        "next_offset": 2,
        "prev_offset": None,
    }

    # Fetch the next page and ensure we receive the remaining item.
    response = client.get("/v1/changes", params={"limit": 2, "offset": 2})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["pagination"]["next_offset"] is None
    assert payload["pagination"]["prev_offset"] == 0


def test_changes_endpoint_supports_sorting(api_context):
    session = api_context["SessionLocal"]()
    try:
        _seed_changes(session, count=4)
    finally:
        session.close()

    client = api_context["client"]

    # Ascending sort by score should produce a monotonically increasing sequence.
    response = client.get("/v1/changes", params={"sort": "score"})
    assert response.status_code == 200
    payload = response.json()
    scores = _collect_scores(payload["items"])
    assert scores == sorted(scores)

    # Descending sort by score should invert the order.
    response = client.get("/v1/changes", params={"sort": "-score"})
    assert response.status_code == 200
    payload = response.json()
    scores = _collect_scores(payload["items"])
    assert scores == sorted(scores, reverse=True)


def test_changes_endpoint_rejects_invalid_sort(api_context):
    session = api_context["SessionLocal"]()
    session.close()

    client = api_context["client"]

    response = client.get("/v1/changes", params={"sort": "title"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid sort parameter"
