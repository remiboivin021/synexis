CREATE TABLE IF NOT EXISTS meta(
  schema_version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS documents(
  doc_id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  source_type TEXT NOT NULL,
  title TEXT NOT NULL,
  mtime INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  error TEXT,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks(
  chunk_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  text_hash TEXT NOT NULL,
  start_char INTEGER NOT NULL,
  end_char INTEGER NOT NULL,
  heading_path TEXT,
  FOREIGN KEY(doc_id) REFERENCES documents(doc_id),
  UNIQUE(doc_id, ordinal)
);

CREATE TABLE IF NOT EXISTS errors(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stage TEXT NOT NULL,
  path TEXT,
  doc_id TEXT,
  chunk_id TEXT,
  message TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
