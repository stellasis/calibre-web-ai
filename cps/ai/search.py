# -*- coding: utf-8 -*-

"""
AI Semantic Search Service
Performs semantic search using vector similarity with sqlite-vec.
"""

import os
from typing import Optional, List, Dict, Any
import numpy as np

from .. import config, logger, ub, calibre_db

log = logger.create()

# Try to import LangChain embedding classes
try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.embeddings import OllamaEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    log.warning("LangChain embeddings not available for search")


def _get_embedding_model():
    """
    Get LangChain embedding model instance based on configuration.
    Reuses the same pattern as embeddings.py
    
    Returns:
        LangChain embeddings instance or None if not available/configured
    """
    if not LANGCHAIN_AVAILABLE:
        return None
    
    if not config.config_ai_enabled:
        return None
    
    provider = getattr(config, 'config_ai_provider', 'openai')
    model = getattr(config, 'config_ai_embedding_model', 'text-embedding-3-small')
    
    api_key = getattr(config, 'config_ai_api_key', None)
    if not api_key:
        api_key_e = getattr(config, 'config_ai_api_key_e', None)
        if api_key_e:
            api_key = api_key_e
        else:
            return None
    
    timeout = getattr(config, 'config_ai_timeout_seconds', 60)
    max_retries = getattr(config, 'config_ai_max_retries', 3)
    
    try:
        if provider == 'openai':
            return OpenAIEmbeddings(
                model=model,
                api_key=api_key,
                timeout=timeout,
                max_retries=max_retries
            )
        elif provider == 'openrouter':
            return OpenAIEmbeddings(
                model=model,
                api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                timeout=timeout,
                max_retries=max_retries
            )
        elif provider == 'ollama':
            return OllamaEmbeddings(
                model=model,
                base_url=os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            )
        else:
            log.error("Unknown AI provider for embeddings: %s", provider)
            return None
    except Exception as e:
        log.error("Failed to initialize embedding model for search: %s", e)
        return None


def _generate_query_embedding(query: str) -> Optional[np.ndarray]:
    """
    Generate embedding vector for a search query.
    
    Args:
        query: Search query text
    
    Returns:
        numpy array of embedding vector, or None on error
    """
    embedding_model = _get_embedding_model()
    if not embedding_model:
        log.error("Failed to get embedding model for query")
        return None
    
    try:
        embedding_vector = embedding_model.embed_query(query)
        return np.array(embedding_vector, dtype=np.float32)
    except Exception as e:
        log.error("Failed to generate query embedding: %s", e)
        return None


def semantic_search(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Perform semantic search using natural language query.
    
    Process:
    1. Check config.config_ai_enabled - return empty list if disabled
    2. Generate query embedding (using LangChain)
    3. Query book_embeddings_vec virtual table using MATCH operator
    4. Order by distance (ascending = most similar)
    5. Limit to limit results
    6. Return ranked results with book objects
    
    Args:
        query: Natural language search query
        limit: Maximum number of results (default 20)
    
    Returns:
        List of dicts with keys: 'book_id', 'similarity_score', 'book' (book object)
        Sorted by similarity score (highest first)
    """
    # Check if AI is enabled
    if not config.config_ai_enabled:
        log.warning("AI features are disabled")
        return []
    
    # Check if LangChain is available
    if not LANGCHAIN_AVAILABLE:
        log.error("LangChain not available for semantic search")
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
        results = _vector_search(query_embedding, limit)
        return results
    except Exception as e:
        log.error("Semantic search failed: %s", e, exc_info=True)
        return []


def _vector_search(query_embedding: np.ndarray, limit: int) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search using sqlite-vec.
    
    Args:
        query_embedding: Query embedding vector
        limit: Maximum number of results
    
    Returns:
        List of search results with book objects
    """
    from sqlalchemy import create_engine, text
    
    db_path = getattr(ub, 'app_DB_path', None)
    if not db_path:
        log.error("Database path not configured")
        return []
    
    db_path = os.path.abspath(db_path)
    
    # Convert embedding to bytes for sqlite-vec query
    query_bytes = query_embedding.tobytes()
    
    engine = None
    results = []
    
    try:
        engine = create_engine(
            f'sqlite:///{db_path}',
            echo=False,
            connect_args={'check_same_thread': False}
        )
        
        with engine.connect() as conn:
            # Check if virtual table exists
            vt_check = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='book_embeddings_vec'")
            ).fetchone()
            
            if not vt_check:
                log.warning("Virtual table book_embeddings_vec not found - falling back to cosine similarity")
                return _fallback_search(conn, query_embedding, limit)
            
            # Try sqlite-vec MATCH query
            try:
                # sqlite-vec uses MATCH operator for KNN search
                # The embedding parameter should be passed as BLOB
                search_results = conn.execute(
                    text("""
                        SELECT book_id, distance
                        FROM book_embeddings_vec
                        WHERE embedding MATCH :query_embedding
                        ORDER BY distance
                        LIMIT :limit
                    """),
                    {"query_embedding": query_bytes, "limit": limit}
                ).fetchall()
                
                log.debug("sqlite-vec search returned %d results", len(search_results))
                
            except Exception as vec_error:
                log.warning("sqlite-vec search failed, falling back: %s", vec_error)
                return _fallback_search(conn, query_embedding, limit)
            
            # Fetch book objects for results
            for row in search_results:
                book_id, distance = row
                
                # Convert distance to similarity score (1.0 - normalized_distance)
                # sqlite-vec returns L2 distance, lower is better
                # Normalize to 0-1 range where 1 is most similar
                similarity_score = max(0.0, 1.0 - (distance / 2.0))  # Normalize assuming max distance ~2
                
                # Fetch book object
                try:
                    book = calibre_db.get_book(book_id)
                    if book:
                        results.append({
                            'book_id': book_id,
                            'similarity_score': similarity_score,
                            'book': book,
                            'distance': distance
                        })
                except Exception as e:
                    log.warning("Failed to fetch book %d: %s", book_id, e)
        
        engine.dispose()
        
    except Exception as e:
        log.error("Vector search failed: %s", e, exc_info=True)
        if engine:
            engine.dispose()
    
    # Sort by similarity score (highest first)
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return results


def _fallback_search(conn, query_embedding: np.ndarray, limit: int) -> List[Dict[str, Any]]:
    """
    Fallback search using cosine similarity when sqlite-vec is not available.
    
    Args:
        conn: Database connection
        query_embedding: Query embedding vector
        limit: Maximum number of results
    
    Returns:
        List of search results
    """
    from sqlalchemy import text
    
    results = []
    
    try:
        # Fetch all embeddings from regular table
        all_embeddings = conn.execute(
            text("SELECT book_id, vector FROM book_embeddings")
        ).fetchall()
        
        if not all_embeddings:
            log.warning("No embeddings found in database")
            return []
        
        # Calculate cosine similarity for each
        similarities = []
        query_norm = np.linalg.norm(query_embedding)
        
        for book_id, vector_blob in all_embeddings:
            try:
                book_embedding = np.frombuffer(vector_blob, dtype=np.float32)
                
                # Cosine similarity
                book_norm = np.linalg.norm(book_embedding)
                if query_norm > 0 and book_norm > 0:
                    similarity = np.dot(query_embedding, book_embedding) / (query_norm * book_norm)
                    similarities.append((book_id, float(similarity)))
            except Exception as e:
                log.warning("Failed to calculate similarity for book %d: %s", book_id, e)
        
        # Sort by similarity (highest first) and limit
        similarities.sort(key=lambda x: x[1], reverse=True)
        similarities = similarities[:limit]
        
        # Fetch book objects
        for book_id, similarity_score in similarities:
            try:
                book = calibre_db.get_book(book_id)
                if book:
                    results.append({
                        'book_id': book_id,
                        'similarity_score': similarity_score,
                        'book': book
                    })
            except Exception as e:
                log.warning("Failed to fetch book %d: %s", book_id, e)
        
    except Exception as e:
        log.error("Fallback search failed: %s", e, exc_info=True)
    
    return results


def similar_books(book_id: int, limit: int = 8) -> List[Dict[str, Any]]:
    """
    Find books similar to a given book using embedding similarity.
    
    Args:
        book_id: Book ID to find similar books for
        limit: Maximum number of results (default 8)
    
    Returns:
        List of dicts with keys: 'book_id', 'similarity_score', 'book'
        Excludes the source book from results
    """
    # Check if AI is enabled
    if not config.config_ai_enabled:
        return []
    
    # Get embedding for the source book
    from .embeddings import get_embedding
    
    source_embedding = get_embedding(book_id)
    if source_embedding is None:
        log.debug("No embedding found for book %d", book_id)
        return []
    
    # Search for similar books
    results = _vector_search(source_embedding, limit + 1)  # +1 to account for self
    
    # Filter out the source book
    results = [r for r in results if r['book_id'] != book_id]
    
    # Limit results
    return results[:limit]


def get_embedding_count() -> int:
    """
    Get total count of book embeddings in database.
    
    Returns:
        Number of embeddings, or 0 if error
    """
    from sqlalchemy import create_engine, text
    
    db_path = getattr(ub, 'app_DB_path', None)
    if not db_path:
        return 0
    
    db_path = os.path.abspath(db_path)
    
    try:
        engine = create_engine(
            f'sqlite:///{db_path}',
            echo=False,
            connect_args={'check_same_thread': False}
        )
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM book_embeddings")
            ).fetchone()
            return result[0] if result else 0
        engine.dispose()
    except Exception as e:
        log.error("Error getting embedding count: %s", e)
    
    return 0

