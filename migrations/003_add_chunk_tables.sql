-- Migration: 003_add_chunk_tables.sql
-- Description: Create book_chunks, book_chunk_embeddings, and book_index_status tables for full book indexing
-- Schema: app_settings (user database, not calibre database)
-- Note: SQLite doesn't support schemas, so tables are created without schema prefix
-- Date: 2025-01-27
-- Prerequisites: Story 1.1 (Database Schema), Story 1.2 (sqlite-vec)

-- Create book_chunks table
CREATE TABLE IF NOT EXISTS book_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chapter_title TEXT,
    chunk_text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    start_position INTEGER NOT NULL,
    end_position INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
);

-- Create index on book_id for book_chunks
CREATE INDEX IF NOT EXISTS idx_book_chunks_book_id ON book_chunks(book_id);

-- Create composite index on (book_id, chunk_index) for efficient ordering
CREATE INDEX IF NOT EXISTS idx_book_chunks_book_chunk ON book_chunks(book_id, chunk_index);

-- Create book_chunk_embeddings table
CREATE TABLE IF NOT EXISTS book_chunk_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    vector BLOB NOT NULL,
    vector_dimension INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (chunk_id) REFERENCES book_chunks(id) ON DELETE CASCADE
);

-- Create index on chunk_id for book_chunk_embeddings
CREATE INDEX IF NOT EXISTS idx_book_chunk_embeddings_chunk_id ON book_chunk_embeddings(chunk_id);

-- Create index on book_id for book_chunk_embeddings (denormalized for fast queries)
CREATE INDEX IF NOT EXISTS idx_book_chunk_embeddings_book_id ON book_chunk_embeddings(book_id);

-- Create book_index_status table
CREATE TABLE IF NOT EXISTS book_index_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending',
    total_chunks INTEGER DEFAULT 0,
    processed_chunks INTEGER DEFAULT 0,
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
);

-- Create index on book_id for book_index_status
CREATE INDEX IF NOT EXISTS idx_book_index_status_book_id ON book_index_status(book_id);

-- Create index on status for filtering by status
CREATE INDEX IF NOT EXISTS idx_book_index_status_status ON book_index_status(status);

-- Create virtual table for chunk vector similarity search
-- Note: This requires sqlite-vec extension to be loaded
-- If this fails when running from command line, that's okay - the virtual table
-- will be created automatically when the application runs (sqlite-vec loads on startup)
-- 
-- To create it manually with sqlite3, first load the extension:
--   .load sqlite_vec
--   CREATE VIRTUAL TABLE IF NOT EXISTS book_chunk_embeddings_vec USING vec0(...);
--
-- Or run via Python which loads the extension:
--   python -c "import sqlite3, sqlite_vec; conn = sqlite3.connect('app.db'); sqlite_vec.load(conn); conn.execute('CREATE VIRTUAL TABLE IF NOT EXISTS book_chunk_embeddings_vec USING vec0(chunk_id INTEGER PRIMARY KEY, embedding FLOAT[1536])'); conn.close()"
--
-- For now, we'll create it here - if it fails, the app will create it on startup
CREATE VIRTUAL TABLE IF NOT EXISTS book_chunk_embeddings_vec USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding FLOAT[1536]
);

-- Note: Vector dimension 1536 matches text-embedding-3-small model
-- KNN search example:
-- SELECT chunk_id, distance
-- FROM book_chunk_embeddings_vec
-- WHERE embedding MATCH :query_vector
-- ORDER BY distance
-- LIMIT 20;

