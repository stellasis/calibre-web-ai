-- Migration: 002_create_vec_table.sql
-- Description: Create virtual table for sqlite-vec vector similarity search
-- Schema: app_settings (user database, not calibre database)
-- Date: 2025-12-02
-- Prerequisites: Story 1.1 (book_embeddings table must exist)

-- Create virtual table for vector similarity search
-- Note: This requires sqlite-vec extension to be loaded
-- sqlite-vec is the successor to sqlite-vss with better performance
CREATE VIRTUAL TABLE IF NOT EXISTS app_settings.book_embeddings_vec USING vec0(
    book_id INTEGER PRIMARY KEY,
    embedding FLOAT[1536]
);

-- Note: Vector dimension 1536 matches text-embedding-3-small model
-- KNN search example:
-- SELECT book_id, distance
-- FROM book_embeddings_vec
-- WHERE embedding MATCH :query_vector
-- ORDER BY distance
-- LIMIT 10;

