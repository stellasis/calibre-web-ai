# -*- coding: utf-8 -*-

"""
AI Embedding Generation Service
Generates vector embeddings for books using LangChain embedding models.
"""

import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import numpy as np

from .. import config, logger, ub
from .llm_utils import get_embedding_model, is_embeddings_available
from .db_utils import get_db_connection, ensure_table_exists

log = logger.create()

# Re-export for backward compatibility
LANGCHAIN_AVAILABLE = is_embeddings_available()


def _get_book_text(book_id: int) -> Optional[str]:
    """
    Get text to embed for a book. Prioritizes AI summary, falls back to metadata.

    Args:
        book_id: Book ID from database

    Returns:
        Text string to embed, or None if no text available
    """
    from sqlalchemy import text

    # Try to get AI summary first
    summary_text = None
    try:
        with get_db_connection() as conn:
            result = conn.execute(
                text("SELECT summary_text FROM book_summaries WHERE book_id = :book_id"),
                {"book_id": book_id}
            ).fetchone()

            if result:
                summary_text = result[0]
                log.debug("Found AI summary for book %d (length: %d)", book_id, len(summary_text))
    except RuntimeError as e:
        log.error("Database error: %s", e)
        return None
    except Exception as e:
        log.warning("Error fetching summary for book %d: %s", book_id, e)

    if summary_text:
        return summary_text

    log.debug("No summary found for book %d, falling back to metadata", book_id)
    return _get_metadata_text(book_id)


def _get_metadata_text(book_id: int) -> Optional[str]:
    """
    Build metadata text string for a book (fallback when no summary exists).
    
    Args:
        book_id: Book ID from database
    
    Returns:
        Concatenated metadata string, or None if book not found
    """
    from .. import calibre_db, db
    
    try:
        book = calibre_db.get_book(book_id)
        if not book:
            log.warning("Book %d not found", book_id)
            return None
        
        parts = []
        
        # Title
        if book.title:
            parts.append(f"Title: {book.title}")
        
        # Authors
        if book.authors:
            author_names = ", ".join(author.name.replace('|', ',') for author in book.authors)
            parts.append(f"Author: {author_names}")
        
        # Description/Comments
        if book.comments and len(book.comments) > 0:
            comment_text = book.comments[0].text if hasattr(book.comments[0], 'text') else str(book.comments[0])
            # Strip HTML tags if present
            import re
            comment_text = re.sub('<[^<]+?>', '', comment_text)
            if comment_text:
                parts.append(f"Description: {comment_text}")
        
        # Tags
        if book.tags:
            tag_names = ", ".join(tag.name for tag in book.tags)
            parts.append(f"Tags: {tag_names}")
        
        # Series
        if book.series:
            series_names = ", ".join(series.name for series in book.series)
            parts.append(f"Series: {series_names}")
        
        if not parts:
            log.warning("No metadata available for book %d", book_id)
            return None
        
        return "\n".join(parts)
        
    except Exception as e:
        log.error("Error fetching metadata for book %d: %s", book_id, e)
        return None


def generate_embedding(book_id: int) -> Optional[np.ndarray]:
    """
    Generate embedding vector for a book.

    Args:
        book_id: Book ID from database

    Returns:
        numpy array of embedding vector or None on error
    """
    if not config.config_ai_enabled:
        log.warning("AI features are disabled")
        return None

    if not LANGCHAIN_AVAILABLE:
        log.error("LangChain not available")
        return None

    embedding_model = get_embedding_model()
    if not embedding_model:
        log.error("Failed to initialize embedding model")
        return None

    text_to_embed = _get_book_text(book_id)
    if not text_to_embed:
        log.error("No text available for book %d", book_id)
        return None

    try:
        log.debug("Generating embedding for book %d (text length: %d)", book_id, len(text_to_embed))
        embedding_vector = embedding_model.embed_query(text_to_embed)
        embedding_array = np.array(embedding_vector, dtype=np.float32)
        vector_dimension = len(embedding_array)

        log.info("Generated embedding for book %d (dimension: %d)", book_id, vector_dimension)
        _store_embedding(book_id, embedding_array, vector_dimension)
        return embedding_array

    except Exception as e:
        log.error("Failed to generate embedding for book %d: %s", book_id, e)
        return None


def _store_embedding(book_id: int, embedding: np.ndarray, vector_dimension: int) -> bool:
    """
    Store embedding in database and sync to virtual table.

    Args:
        book_id: Book ID
        embedding: Embedding vector as numpy array
        vector_dimension: Dimension of the vector

    Returns:
        True if successful, False otherwise
    """
    from sqlalchemy import text

    model_name = getattr(config, 'config_ai_embedding_model', 'unknown')
    vector_blob = embedding.tobytes()

    try:
        with get_db_connection() as conn:
            ensure_table_exists(
                conn,
                """CREATE TABLE IF NOT EXISTS book_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    vector BLOB NOT NULL,
                    vector_dimension INTEGER NOT NULL,
                    model_name VARCHAR(100) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )""",
                "CREATE INDEX IF NOT EXISTS ix_book_embeddings_book_id ON book_embeddings (book_id)"
            )

            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

            result = conn.execute(
                text("SELECT id FROM book_embeddings WHERE book_id = :book_id"),
                {"book_id": book_id}
            ).fetchone()

            if result:
                conn.execute(
                    text("""UPDATE book_embeddings
                        SET vector = :vector, vector_dimension = :vector_dimension,
                            model_name = :model_name, updated_at = :updated_at
                        WHERE book_id = :book_id"""),
                    {"vector": vector_blob, "vector_dimension": vector_dimension,
                     "model_name": model_name, "updated_at": now, "book_id": book_id}
                )
                log.debug("Updated embedding for book %d", book_id)
            else:
                conn.execute(
                    text("""INSERT INTO book_embeddings (book_id, vector, vector_dimension, model_name, created_at, updated_at)
                        VALUES (:book_id, :vector, :vector_dimension, :model_name, :created_at, :updated_at)"""),
                    {"book_id": book_id, "vector": vector_blob, "vector_dimension": vector_dimension,
                     "model_name": model_name, "created_at": now, "updated_at": now}
                )
                log.debug("Inserted embedding for book %d", book_id)

            conn.commit()
            _sync_to_virtual_table(conn, book_id, embedding)
            log.info("Embedding stored for book %d", book_id)
            return True

    except RuntimeError as e:
        log.error("Database error: %s", e)
        return False
    except Exception as e:
        log.error("Failed to store embedding for book %d: %s", book_id, e, exc_info=True)
        return False


def _sync_to_virtual_table(conn, book_id: int, embedding: np.ndarray) -> bool:
    """
    Sync embedding to sqlite-vec virtual table for fast similarity search.
    
    Args:
        conn: Database connection
        book_id: Book ID
        embedding: Embedding vector as numpy array
    
    Returns:
        True if successful, False otherwise
    """
    from sqlalchemy import text
    
    try:
        # Check if virtual table exists
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='book_embeddings_vec'")
        ).fetchone()
        
        if not result:
            log.warning("Virtual table book_embeddings_vec not found - sqlite-vec may not be loaded")
            return False
        
        # Convert numpy array to bytes for sqlite-vec
        # sqlite-vec expects the embedding as a BLOB of float32 values
        embedding_bytes = embedding.tobytes()
        
        # Delete existing entry if present
        conn.execute(
            text("DELETE FROM book_embeddings_vec WHERE book_id = :book_id"),
            {"book_id": book_id}
        )
        
        # Insert into virtual table
        # Note: sqlite-vec uses vec0 module which expects embedding as BLOB
        conn.execute(
            text("INSERT INTO book_embeddings_vec (book_id, embedding) VALUES (:book_id, :embedding)"),
            {"book_id": book_id, "embedding": embedding_bytes}
        )
        
        conn.commit()
        log.debug("Synced embedding to virtual table for book %d", book_id)
        return True
        
    except Exception as e:
        log.warning("Failed to sync to virtual table for book %d: %s", book_id, e)
        # Don't fail the whole operation if virtual table sync fails
        return False


def get_embedding(book_id: int) -> Optional[np.ndarray]:
    """
    Retrieve embedding vector for a book from database.

    Args:
        book_id: Book ID

    Returns:
        numpy array of embedding vector, or None if not found
    """
    from sqlalchemy import text

    try:
        with get_db_connection() as conn:
            result = conn.execute(
                text("SELECT vector, vector_dimension FROM book_embeddings WHERE book_id = :book_id"),
                {"book_id": book_id}
            ).fetchone()

            if result:
                vector_blob, _ = result
                return np.frombuffer(vector_blob, dtype=np.float32)
    except RuntimeError:
        return None
    except Exception as e:
        log.error("Error retrieving embedding for book %d: %s", book_id, e)

    return None


def embedding_exists(book_id: int) -> bool:
    """
    Check if embedding exists for a book.

    Args:
        book_id: Book ID

    Returns:
        True if embedding exists, False otherwise
    """
    from sqlalchemy import text

    try:
        with get_db_connection() as conn:
            result = conn.execute(
                text("SELECT 1 FROM book_embeddings WHERE book_id = :book_id LIMIT 1"),
                {"book_id": book_id}
            ).fetchone()
            return result is not None
    except RuntimeError:
        return False
    except Exception as e:
        log.error("Error checking embedding existence for book %d: %s", book_id, e)

    return False

