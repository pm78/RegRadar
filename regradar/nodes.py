from __future__ import annotations

import hashlib
import difflib
import io
import xml.etree.ElementTree as ET
from typing import Iterable, List, Optional

import httpx
import trafilatura
from pypdf import PdfReader

from .database import (
    ChangeEvent,
    Document,
    DocumentVersion,
    HashStoreResult,
    ParsedDoc,
    RawDoc,
    SessionLocal,
    Source,
)

USER_AGENT = "RegRadarBot/0.1"
TIMEOUT = 10.0


def fetch_sources() -> List[Source]:
    """Return all sources from the database."""
    session = SessionLocal()
    try:
        return session.query(Source).all()
    finally:
        session.close()


def fetch_documents(sources: Iterable[Source]) -> List[RawDoc]:
    """Download documents for the given sources (RSS feeds)."""
    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    raw_docs: List[RawDoc] = []
    for source in sources:
        try:
            resp = client.get(source.url)
            resp.raise_for_status()
        except Exception:
            continue
        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError:
            continue
        # Find item links in RSS feed
        for item in root.findall('.//item')[:5]:
            link_el = item.find('link')
            title_el = item.find('title')
            if link_el is None:
                continue
            link = link_el.text.strip()
            title = title_el.text.strip() if title_el is not None else None
            try:
                doc_resp = client.get(link)
                doc_resp.raise_for_status()
                raw_docs.append(RawDoc(url=link, content=doc_resp.content, source_id=source.id, title=title))
            except Exception:
                continue
    client.close()
    return raw_docs


def parse_document(raw_doc: RawDoc) -> ParsedDoc:
    """Extract text and metadata from raw document."""
    if raw_doc.url.lower().endswith('.pdf'):
        reader = PdfReader(io.BytesIO(raw_doc.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        text = trafilatura.extract(raw_doc.content.decode('utf-8', errors='ignore')) or ""
    return ParsedDoc(url=raw_doc.url, text=text, source_id=raw_doc.source_id, title=raw_doc.title)


def hash_and_store(parsed_doc: ParsedDoc) -> HashStoreResult:
    session = SessionLocal()
    try:
        content_hash = hashlib.sha256(parsed_doc.text.encode('utf-8')).hexdigest()
        document = session.query(Document).filter_by(external_id=parsed_doc.url).first()
        if document is None:
            document = Document(external_id=parsed_doc.url, source_id=parsed_doc.source_id)
            session.add(document)
            session.commit()
        version = session.query(DocumentVersion).filter_by(content_hash=content_hash, document_id=document.id).first()
        is_new = False
        if version is None:
            version = DocumentVersion(document_id=document.id, content_hash=content_hash, content=parsed_doc.text)
            session.add(version)
            session.commit()
            is_new = True
        return HashStoreResult(document=document, version=version, is_new_version=is_new)
    finally:
        session.close()


def link_versions(result: HashStoreResult) -> Optional[DocumentVersion]:
    if not result.is_new_version:
        return None
    session = SessionLocal()
    try:
        previous = (
            session.query(DocumentVersion)
            .filter(
                DocumentVersion.document_id == result.document.id,
                DocumentVersion.id < result.version.id,
            )
            .order_by(DocumentVersion.id.desc())
            .first()
        )
        return previous
    finally:
        session.close()


def compute_diff(result: HashStoreResult, previous: Optional[DocumentVersion]) -> Optional[ChangeEvent]:
    if previous is None or not result.is_new_version:
        return None
    session = SessionLocal()
    try:
        diff_lines = difflib.unified_diff(
            previous.content.splitlines(),
            result.version.content.splitlines(),
            lineterm="",
        )
        diff_text = "\n".join(diff_lines)
        event = ChangeEvent(
            document_version_id=result.version.id,
            previous_version_id=previous.id,
            diff=diff_text,
        )
        session.add(event)
        session.commit()
        return event
    finally:
        session.close()
