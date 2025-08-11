-- Initial schema for RegRadar
CREATE TABLE IF NOT EXISTS source (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL,
    source_id INT REFERENCES source(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_version (
    id SERIAL PRIMARY KEY,
    document_id INT REFERENCES document(id),
    content_hash TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS change_event (
    id SERIAL PRIMARY KEY,
    document_version_id INT REFERENCES document_version(id),
    prev_version_id INT REFERENCES document_version(id),
    diff TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS impact_assessment (
    id SERIAL PRIMARY KEY,
    document_version_id INT REFERENCES document_version(id),
    summary TEXT,
    actions TEXT,
    score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
