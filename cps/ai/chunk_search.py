# -*- coding: utf-8 -*-

"""
Chunk search service for full book indexing.
Searches within indexed book chunks using vector similarity.
"""

import os
from typing import Optional, List, Dict, Any
import numpy as np

from .. import config, logger, calibre_db
from ..ub import session, BookChunk, BookChunkEmbedding
from .llm_utils import get_embedding_model, is_embeddings_available
from .db_utils import get_db_connection, get_db_path, load_sqlite_vec

log = logger.create()

# Re-export for backward compatibility
LANGCHAIN_AVAILABLE = is_embeddings_available()


def _generate_query_embedding(query: str) -> Optional[np.ndarray]:
    """
    Generate embedding vector for a search query.

    Args:
        query: Search query text

    Returns:
        numpy array of embedding vector, or None on error
    """
    embedding_model = get_embedding_model()
    if not embedding_model:
        log.error("Failed to get embedding model for query")
        return None

    try:
        embedding_vector = embedding_model.embed_query(query)
        return np.array(embedding_vector, dtype=np.float32)
    except Exception as e:
        log.error("Failed to generate query embedding: %s", e)
        return None


def search_chunks(query: str, book_id: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search within indexed book chunks using vector similarity.
    
    Args:
        query: Search query text
        book_id: Optional book ID to filter results to a specific book
        limit: Maximum number of results (default 20)
    
    Returns:
        List of dicts with keys:
        - 'chunk_id': Chunk ID
        - 'book_id': Book ID
        - 'chunk_index': Chunk index in book
        - 'chunk_text': The passage content
        - 'chapter_title': Chapter title if available
        - 'similarity_score': Similarity score (0-1, higher is better)
        - 'book': Book object (title, author for context)
    """
    # Check if AI is enabled
    if not config.config_ai_enabled:
        log.warning("AI features are disabled")
        return []
    
    # Check if LangChain is available
    if not LANGCHAIN_AVAILABLE:
        log.error("LangChain not available for chunk search")
        return []
    
    if not query or not query.strip():
        log.warning("Empty search query")
        return []
    
    # Generate query embedding
    query_embedding = _generate_query_embedding(query)
    if query_embedding is None:
        log.error("Failed to generate query embedding")
        return []
    
    # Perform vector similarity search
    try:
        results = _vector_search_chunks(query_embedding, book_id, limit)
        return results
    except Exception as e:
        log.error("Chunk search failed: %s", e, exc_info=True)
        return []


def _vector_search_chunks(query_embedding: np.ndarray, book_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search on chunks using sqlite-vec.

    Args:
        query_embedding: Query embedding vector
        book_id: Optional book ID filter
        limit: Maximum number of results

    Returns:
        List of chunk search results
    """
    from sqlalchemy import text

    query_bytes = query_embedding.tobytes()
    results = []

    try:
        with get_db_connection() as conn:
            if not load_sqlite_vec(conn):
                return []

            # Ensure virtual table exists
            from .chunk_embeddings import _ensure_chunk_virtual_table
            if not _ensure_chunk_virtual_table(conn):
                log.error("Virtual table book_chunk_embeddings_vec not available")
                return []

            # Build query with optional book_id filter
            if book_id:
                # Search within specific book - do KNN first, then filter
                # Request more results from KNN to account for filtering
                knn_limit = limit * 10  # Get 10x results to filter down
                search_query = text("""
                    SELECT ce.chunk_id, e.book_id, ce.distance
                    FROM (
                        SELECT chunk_id, distance
                        FROM book_chunk_embeddings_vec
                        WHERE embedding MATCH :query_embedding AND k = :knn_limit
                    ) ce
                    JOIN book_chunk_embeddings e ON ce.chunk_id = e.chunk_id
                    WHERE e.book_id = :book_id
                    ORDER BY ce.distance
                    LIMIT :limit
                """)
                params = {"query_embedding": query_bytes, "book_id": book_id, "limit": limit, "knn_limit": knn_limit}
            else:
                # Global search across all books
                search_query = text("""
                    SELECT ce.chunk_id, e.book_id, ce.distance
                    FROM (
                        SELECT chunk_id, distance
                        FROM book_chunk_embeddings_vec
                        WHERE embedding MATCH :query_embedding AND k = :limit
                    ) ce
                    JOIN book_chunk_embeddings e ON ce.chunk_id = e.chunk_id
                    ORDER BY ce.distance
                    LIMIT :limit
                """)
                params = {"query_embedding": query_bytes, "limit": limit}
            
            try:
                search_results = conn.execute(search_query, params).fetchall()
                log.debug("sqlite-vec chunk search returned %d results", len(search_results))
            except Exception as vec_error:
                # CRITICAL: Log as ERROR and include full traceback - this should not fail silently
                log.error("sqlite-vec chunk search query FAILED: %s", vec_error, exc_info=True)
                # Check if it's a "no such table" or "no such function" error
                error_str = str(vec_error).lower()
                if 'no such table' in error_str or 'book_chunk_embeddings_vec' in error_str:
                    log.error("Virtual table does not exist or sqlite-vec extension not loaded properly")
                elif 'no such function' in error_str or 'match' in error_str:
                    log.error("sqlite-vec MATCH function not available - extension may not be loaded")
                # Still return empty list to avoid breaking the caller, but log it prominently
                return []
            
            # Fetch chunk and book details for results
            for row in search_results:
                chunk_id, result_book_id, distance = row
                similarity_score = max(0.0, 1.0 - (distance / 2.0))

                chunk = session.query(BookChunk).filter_by(id=chunk_id).first()
                if not chunk:
                    continue

                book = None
                try:
                    book = calibre_db.get_book(result_book_id)
                except Exception as e:
                    log.warning("Failed to fetch book %d: %s", result_book_id, e)

                results.append({
                    'chunk_id': chunk_id,
                    'book_id': result_book_id,
                    'chunk_index': chunk.chunk_index,
                    'chunk_text': chunk.chunk_text,
                    'chapter_title': chunk.chapter_title,
                    'similarity_score': similarity_score,
                    'distance': distance,
                    'book': book
                })

    except RuntimeError as e:
        log.error("Database error: %s", e)
    except Exception as e:
        log.error("Chunk vector search failed: %s", e, exc_info=True)

    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    return results


def get_chunk_count(book_id: Optional[int] = None) -> int:
    """
    Get total count of indexed chunks.
    
    Args:
        book_id: Optional book ID to count chunks for a specific book
    
    Returns:
        Number of chunks, or 0 if error
    """
    try:
        if book_id:
            count = session.query(BookChunk).filter_by(book_id=book_id).count()
        else:
            count = session.query(BookChunk).count()
        return count
    except Exception as e:
        log.error("Error getting chunk count: %s", e)
        return 0

