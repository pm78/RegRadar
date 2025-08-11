from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# SQLite database stored in the project directory
DATABASE_URL = "sqlite:///regradar.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)

    documents = relationship("Document", back_populates="source")


class Document(Base):
    __tablename__ = "document"

    id = Column(Integer, primary_key=True)
    external_id = Column(String, nullable=False, unique=True)
    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source = relationship("Source", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document")


class DocumentVersion(Base):
    __tablename__ = "document_version"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("document.id"), nullable=False)
    content_hash = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("content_hash"),)

    document = relationship("Document", back_populates="versions")
    events = relationship("ChangeEvent", back_populates="version", foreign_keys="ChangeEvent.document_version_id")


class ChangeEvent(Base):
    __tablename__ = "change_event"

    id = Column(Integer, primary_key=True)
    document_version_id = Column(Integer, ForeignKey("document_version.id"), nullable=False)
    previous_version_id = Column(Integer, ForeignKey("document_version.id"))
    diff = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    version = relationship("DocumentVersion", foreign_keys=[document_version_id])
    previous = relationship("DocumentVersion", foreign_keys=[previous_version_id])


# Helper dataclasses used by nodes
@dataclass
class RawDoc:
    url: str
    content: bytes
    source_id: int
    title: str | None = None


@dataclass
class ParsedDoc:
    url: str
    text: str
    source_id: int
    title: str | None = None


@dataclass
class HashStoreResult:
    document: Document
    version: DocumentVersion
    is_new_version: bool


def init_db() -> None:
    """Create tables and seed the source table with a few entries."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        if session.query(Source).count() == 0:
            sources = [
                ("EUR-Lex", "https://eur-lex.europa.eu/rss/fr/daily-rss.xml"),
                ("W3C News", "https://www.w3.org/blog/news/feed/"),
                ("Hacker News", "https://news.ycombinator.com/rss"),
                ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
                ("EU Press", "https://ec.europa.eu/commission/presscorner/home/en/rss.xml"),
            ]
            for name, url in sources:
                session.add(Source(name=name, url=url))
            session.commit()
    finally:
        session.close()
