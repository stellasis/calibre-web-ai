-- Migration: 001_add_ai_tables.sql
-- Description: Create book_summaries and book_embeddings tables for AI features
-- Schema: app_settings (user database, not calibre database)
-- Date: 2025-01-27

-- Create book_summaries table
CREATE TABLE IF NOT EXISTS app_settings.book_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    summary_text TEXT NOT NULL,
    model_name TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
);

-- Create index on book_id for book_summaries
CREATE INDEX IF NOT EXISTS idx_book_summaries_book_id ON app_settings.book_summaries(book_id);

-- Create book_embeddings table
CREATE TABLE IF NOT EXISTS app_settings.book_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    vector BLOB NOT NULL,
    vector_dimension INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
);

-- Create index on book_id for book_embeddings
CREATE INDEX IF NOT EXISTS idx_book_embeddings_book_id ON app_settings.book_embeddings(book_id);

