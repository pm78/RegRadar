"""FastAPI application exposing read-only endpoints for RegRadar."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session, joinedload

from .database import (
    SessionLocal,
    ImpactAssessment,
    DocumentVersion,
    Document,
    Source,
    ChangeEvent,
)


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY = os.getenv("API_KEY")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(api_key: str = Depends(api_key_header)) -> None:
    if API_KEY and api_key == API_KEY:
        return
    raise HTTPException(status_code=401, detail="Unauthorized")


app = FastAPI(title="RegRadar API")


@app.get("/v1/changes", dependencies=[Depends(require_api_key)])
def list_changes(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source_id: Optional[int] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db),
) -> Dict[str, List[Dict[str, Any]]]:
    """Return published impact assessments with optional filters."""

    query = (
        db.query(ImpactAssessment, DocumentVersion, Document, Source, ChangeEvent)
        .join(DocumentVersion, ImpactAssessment.document_version_id == DocumentVersion.id)
        .join(Document, DocumentVersion.document_id == Document.id)
        .join(Source, Document.source_id == Source.id)
        .outerjoin(ChangeEvent, ChangeEvent.document_version_id == DocumentVersion.id)
    )

    if start_date:
        query = query.filter(ImpactAssessment.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(ImpactAssessment.created_at <= datetime.fromisoformat(end_date))
    if source_id:
        query = query.filter(Source.id == source_id)
    if min_score:
        query = query.filter(ImpactAssessment.score >= min_score)

    rows = query.order_by(ImpactAssessment.created_at.desc()).all()
    items: List[Dict[str, Any]] = []
    for assessment, version, document, source, change in rows:
        items.append(
            {
                "id": assessment.id,
                "summary": assessment.summary,
                "actions": assessment.actions,
                "score": assessment.score,
                "created_at": assessment.created_at.isoformat(),
                "document": {
                    "id": document.id,
                    "external_id": document.external_id,
                    "source": source.name,
                },
                "diff": change.diff if change else None,
            }
        )
    return {"items": items}


@app.get("/v1/documents/{doc_id}", dependencies=[Depends(require_api_key)])
def get_document(doc_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    doc = (
        db.query(Document)
        .options(joinedload(Document.versions))
        .filter(Document.id == doc_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    versions = [
        {
            "id": v.id,
            "created_at": v.created_at.isoformat(),
            "content": v.content,
        }
        for v in doc.versions
    ]
    return {
        "id": doc.id,
        "external_id": doc.external_id,
        "source_id": doc.source_id,
        "created_at": doc.created_at.isoformat() if hasattr(doc, "created_at") else None,
        "versions": versions,
    }


@app.get("/v1/impacts/{impact_id}", dependencies=[Depends(require_api_key)])
def get_impact(impact_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    row = (
        db.query(ImpactAssessment, DocumentVersion, Document, Source)
        .join(DocumentVersion, ImpactAssessment.document_version_id == DocumentVersion.id)
        .join(Document, DocumentVersion.document_id == Document.id)
        .join(Source, Document.source_id == Source.id)
        .filter(ImpactAssessment.id == impact_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Impact not found")
    assessment, version, document, source = row
    return {
        "id": assessment.id,
        "summary": assessment.summary,
        "actions": assessment.actions,
        "score": assessment.score,
        "created_at": assessment.created_at.isoformat(),
        "document": {
            "id": document.id,
            "external_id": document.external_id,
            "source": source.name,
            "version_id": version.id,
        },
    }


__all__ = ["app"]

