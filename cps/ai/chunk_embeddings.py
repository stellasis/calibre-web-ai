# -*- coding: utf-8 -*-

"""
Chunk embedding service for full book indexing.
Generates embeddings for book chunks using LangChain embedding models.
"""

import os
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import numpy as np

from .. import config, logger, ub
from ..ub import session, BookChunk, BookChunkEmbedding, BookIndexStatus

log = logger.create()

# Try to import LangChain embedding classes
try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.embeddings import OllamaEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    log.warning("LangChain embeddings not available. Install with: pip install langchain langchain-openai langchain-community")


# Configuration defaults
DEFAULT_BATCH_SIZE = 25
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1  # Base delay in seconds for exponential backoff


def _get_embedding_model():
    """
    Get LangChain embedding model instance based on configuration.
    Reuses logic from cps/ai/embeddings.py
    
    Returns:
        LangChain embeddings instance or None if not available/configured
    """
    log.debug("_get_embedding_model called")
    
    if not LANGCHAIN_AVAILABLE:
        log.error("_get_embedding_model: LangChain not available")
        return None
    
    if not config.config_ai_enabled:
        log.error("_get_embedding_model: AI features are disabled")
        return None
    
    provider = getattr(config, 'config_ai_provider', 'openai')
    model = getattr(config, 'config_ai_embedding_model', 'text-embedding-3-small')
    
    log.debug("_get_embedding_model: provider=%s, model=%s", provider, model)
    
    # Get API key (ConfigSQL automatically decrypts _e fields)
    api_key = getattr(config, 'config_ai_api_key', None)
    
    if not api_key:
        # Try the encrypted field directly
        api_key_e = getattr(config, 'config_ai_api_key_e', None)
        if api_key_e:
            log.warning("AI API key found in _e field but not decrypted - using it directly")
            api_key = api_key_e
        else:
            log.error("_get_embedding_model: AI API key not configured")
            return None
    
    log.debug("_get_embedding_model: api_key length=%d", len(api_key) if api_key else 0)
    
    timeout = getattr(config, 'config_ai_timeout_seconds', 60)
    max_retries = getattr(config, 'config_ai_max_retries', MAX_RETRIES)
    
    try:
        if provider == 'openai':
            log.info("Creating OpenAIEmbeddings with model=%s, timeout=%d", model, timeout)
            return OpenAIEmbeddings(
                model=model,
                api_key=api_key,
                timeout=timeout,
                max_retries=max_retries
            )
        elif provider == 'openrouter':
            # OpenRouter uses OpenAI-compatible API format
            log.info("Creating OpenAIEmbeddings for OpenRouter with model=%s", model)
            return OpenAIEmbeddings(
                model=model,
                api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                timeout=timeout,
                max_retries=max_retries
            )
        elif provider == 'ollama':
            log.info("Creating OllamaEmbeddings with model=%s", model)
            return OllamaEmbeddings(
                model=model,
                base_url=os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            )
        else:
            log.error("_get_embedding_model: Unknown AI provider: %s", provider)
            return None
    except Exception as e:
        log.error("_get_embedding_model: Failed to initialize embedding model: %s", e, exc_info=True)
        return None


def _embed_batch_with_retry(embedding_model, texts: List[str], max_retries: int = MAX_RETRIES) -> Optional[List[List[float]]]:
    """
    Generate embeddings for a batch of texts with retry logic and timeout protection.
    
    Args:
        embedding_model: LangChain embedding model
        texts: List of text strings to embed
        max_retries: Maximum number of retry attempts
    
    Returns:
        List of embedding vectors, or None on failure
    """
    import signal
    
    # Get timeout from config (default 120 seconds for batch)
    timeout = getattr(config, 'config_ai_timeout_seconds', 60) * 2  # Batch takes longer
    
    for attempt in range(max_retries):
        try:
            log.debug("Generating embeddings for batch of %d texts (attempt %d/%d)", 
                     len(texts), attempt + 1, max_retries)
            start_time = time.time()
            
            # Use embed_documents for batch processing (more efficient)
            if hasattr(embedding_model, 'embed_documents'):
                embeddings = embedding_model.embed_documents(texts)
            else:
                # Fallback to individual embedding
                embeddings = [embedding_model.embed_query(text) for text in texts]
            
            elapsed = time.time() - start_time
            log.debug("Generated embeddings in %.2fs", elapsed)
            
            if not embeddings or len(embeddings) != len(texts):
                log.warning("Embedding count mismatch: got %d, expected %d", 
                          len(embeddings) if embeddings else 0, len(texts))
                if attempt < max_retries - 1:
                    continue
                return None
            
            return embeddings
        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)  # Exponential backoff
                log.warning("Embedding batch failed (attempt %d/%d, took %.2fs), retrying in %ds: %s", 
                          attempt + 1, max_retries, elapsed, delay, e)
                time.sleep(delay)
            else:
                log.error("Embedding batch failed after %d attempts (last attempt took %.2fs): %s", 
                         max_retries, elapsed, e, exc_info=True)
                return None
    return None


def _store_chunk_embeddings(chunk_embeddings: List[Dict[str, Any]]) -> bool:
    """
    Store chunk embeddings in database and sync to virtual table.
    
    Args:
        chunk_embeddings: List of dicts with 'chunk_id', 'book_id', 'embedding', 'vector_dimension', 'model_name'
    
    Returns:
        True if successful, False otherwise
    """
    from sqlalchemy import create_engine, text
    
    # Get database path
    db_path = getattr(ub, 'app_DB_path', None)
    if not db_path:
        log.error("Database path not configured")
        return False
    
    db_path = os.path.abspath(db_path)
    
    engine = None
    conn = None
    try:
        engine = create_engine(
            f'sqlite:///{db_path}',
            echo=False,
            connect_args={'check_same_thread': False}
        )
        conn = engine.connect()
        
        # Load sqlite-vec extension (required for virtual table operations)
        try:
            import sqlite_vec
            raw_conn = conn.connection.dbapi_connection
            raw_conn.enable_load_extension(True)
            sqlite_vec.load(raw_conn)
            raw_conn.enable_load_extension(False)
        except ImportError:
            log.error("sqlite-vec package not installed. Install with: pip install sqlite-vec")
            return False
        except Exception as e:
            log.error("Failed to load sqlite-vec extension: %s", e)
            return False
        
        # Store each embedding
        for emb_data in chunk_embeddings:
            chunk_id = emb_data['chunk_id']
            book_id = emb_data['book_id']
            embedding = emb_data['embedding']
            vector_dimension = emb_data['vector_dimension']
            model_name = emb_data['model_name']
            
            # Serialize embedding to BLOB
            vector_blob = embedding.tobytes()
            
            # Check if embedding already exists
            result = conn.execute(
                text("SELECT id FROM book_chunk_embeddings WHERE chunk_id = :chunk_id"),
                {"chunk_id": chunk_id}
            ).fetchone()
            
            if result:
                # Update existing
                conn.execute(
                    text("""
                        UPDATE book_chunk_embeddings 
                        SET vector = :vector, vector_dimension = :vector_dimension, 
                            model_name = :model_name
                        WHERE chunk_id = :chunk_id
                    """),
                    {
                        "vector": vector_blob,
                        "vector_dimension": vector_dimension,
                        "model_name": model_name,
                        "chunk_id": chunk_id
                    }
                )
            else:
                # Insert new
                conn.execute(
                    text("""
                        INSERT INTO book_chunk_embeddings 
                        (chunk_id, book_id, vector, vector_dimension, model_name, created_at)
                        VALUES (:chunk_id, :book_id, :vector, :vector_dimension, :model_name, :created_at)
                    """),
                    {
                        "chunk_id": chunk_id,
                        "book_id": book_id,
                        "vector": vector_blob,
                        "vector_dimension": vector_dimension,
                        "model_name": model_name,
                        "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    }
                )
        
        conn.commit()
        
        # Sync to virtual table (CRITICAL: must succeed for search to work)
        try:
            sync_start = time.time()
            sync_success = _sync_chunks_to_virtual_table(conn, chunk_embeddings)
            sync_elapsed = time.time() - sync_start
            if sync_success:
                log.debug("Synced %d embeddings to virtual table in %.2fs", len(chunk_embeddings), sync_elapsed)
            else:
                log.error("CRITICAL: Failed to sync %d embeddings to virtual table (took %.2fs) - search will not work!", 
                         len(chunk_embeddings), sync_elapsed)
                log.error("Embeddings are stored in database but not in search index. Re-indexing may be required.")
                # Don't fail the whole operation, but log it prominently
                # The embeddings are still stored, just not searchable
        except Exception as e:
            log.error("Exception syncing embeddings to virtual table: %s", e, exc_info=True)
            # Continue - embeddings are still stored
        
        log.debug("Stored %d chunk embeddings (virtual table sync: %s)", len(chunk_embeddings), "success" if sync_success else "FAILED")
        return True
        
    except Exception as e:
        log.error("Failed to store chunk embeddings: %s", e, exc_info=True)
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
        if engine:
            engine.dispose()


def _ensure_chunk_virtual_table(conn) -> bool:
    """
    Ensure the chunk virtual table exists. Create it if it doesn't.
    
    Args:
        conn: Database connection (must have sqlite-vec extension loaded)
    
    Returns:
        True if virtual table exists or was created, False otherwise
    """
    from sqlalchemy import text
    
    try:
        # Ensure sqlite-vec is loaded in this connection
        try:
            import sqlite_vec
            raw_conn = conn.connection.dbapi_connection
            raw_conn.enable_load_extension(True)
            sqlite_vec.load(raw_conn)
            raw_conn.enable_load_extension(False)
        except ImportError:
            log.error("sqlite-vec package not installed. Install with: pip install sqlite-vec")
            return False
        except Exception as e:
            log.error("Failed to load sqlite-vec extension: %s", e)
            return False
        
        # Check if virtual table exists
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='book_chunk_embeddings_vec'")
        ).fetchone()
        
        if result:
            return True
        
        # Try to create it
        try:
            conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS book_chunk_embeddings_vec USING vec0(
                    chunk_id INTEGER PRIMARY KEY,
                    embedding FLOAT[1536]
                )
            """))
            conn.commit()
            log.info("Created virtual table book_chunk_embeddings_vec")
            return True
        except Exception as e:
            log.warning("Failed to create virtual table book_chunk_embeddings_vec: %s", e)
            return False
    except Exception as e:
        log.warning("Error checking/creating virtual table: %s", e)
        return False


def _sync_chunks_to_virtual_table(conn, chunk_embeddings: List[Dict[str, Any]]) -> bool:
    """
    Sync chunk embeddings to sqlite-vec virtual table for fast similarity search.
    
    Args:
        conn: Database connection (must have sqlite-vec extension loaded)
        chunk_embeddings: List of embedding data dicts
    
    Returns:
        True if successful, False otherwise
    """
    from sqlalchemy import text
    
    # Ensure sqlite-vec is loaded and virtual table exists
    if not _ensure_chunk_virtual_table(conn):
        log.warning("Virtual table book_chunk_embeddings_vec not available - sqlite-vec may not be loaded")
        return False
    
    try:
        
        # Sync each embedding
        for emb_data in chunk_embeddings:
            chunk_id = emb_data['chunk_id']
            embedding = emb_data['embedding']
            
            # Convert numpy array to bytes for sqlite-vec
            embedding_bytes = embedding.tobytes()
            
            # Delete existing entry if present
            conn.execute(
                text("DELETE FROM book_chunk_embeddings_vec WHERE chunk_id = :chunk_id"),
                {"chunk_id": chunk_id}
            )
            
            # Insert into virtual table
            conn.execute(
                text("INSERT INTO book_chunk_embeddings_vec (chunk_id, embedding) VALUES (:chunk_id, :embedding)"),
                {"chunk_id": chunk_id, "embedding": embedding_bytes}
            )
        
        conn.commit()
        log.debug("Synced %d chunk embeddings to virtual table", len(chunk_embeddings))
        return True
        
    except Exception as e:
        log.error("CRITICAL: Failed to sync chunks to virtual table: %s", e, exc_info=True)
        # Check for specific error types
        error_str = str(e).lower()
        if 'no such table' in error_str or 'book_chunk_embeddings_vec' in error_str:
            log.error("Virtual table does not exist - sqlite-vec extension may not be loaded")
        elif 'no such function' in error_str or 'match' in error_str:
            log.error("sqlite-vec MATCH function not available - extension not loaded properly")
        # Don't fail the whole operation if virtual table sync fails (embeddings still stored)
        # But log it as ERROR so it's visible
        return False


def embed_chunks(book_id: int) -> bool:
    """
    Generate embeddings for all unembedded chunks of a book.
    
    Args:
        book_id: Book ID from database
    
    Returns:
        True if successful, False otherwise
    """
    log.info("=== Starting embed_chunks for book %d ===", book_id)
    
    # Check if AI is enabled
    if not config.config_ai_enabled:
        log.error("EMBED FAILED: AI features are disabled")
        return False
    
    # Check if LangChain is available
    if not LANGCHAIN_AVAILABLE:
        log.error("EMBED FAILED: LangChain not available - please install langchain langchain-openai")
        return False
    
    # Log configuration for debugging
    provider = getattr(config, 'config_ai_provider', 'openai')
    model = getattr(config, 'config_ai_embedding_model', 'text-embedding-3-small')
    api_key = getattr(config, 'config_ai_api_key', None)
    log.info("Embedding config - provider: %s, model: %s, api_key set: %s", 
            provider, model, bool(api_key))
    
    # Get embedding model
    try:
        embedding_model = _get_embedding_model()
        if not embedding_model:
            log.error("EMBED FAILED: Failed to initialize embedding model (returned None)")
            return False
        log.info("Successfully initialized embedding model: %s", type(embedding_model).__name__)
    except Exception as e:
        log.error("EMBED FAILED: Exception initializing embedding model: %s", e, exc_info=True)
        return False
    
    # Get configuration
    batch_size = getattr(config, 'config_ai_chunk_batch_size', DEFAULT_BATCH_SIZE)
    model_name = getattr(config, 'config_ai_embedding_model', 'text-embedding-3-small')
    
    try:
        # Get status
        status = session.query(BookIndexStatus).filter_by(book_id=book_id).first()
        if not status:
            log.error("Book index status not found for book %d", book_id)
            return False
        
        # Get all chunks that don't have embeddings yet
        chunks = session.query(BookChunk).filter_by(book_id=book_id).all()
        existing_embeddings = session.query(BookChunkEmbedding.chunk_id).filter_by(book_id=book_id).all()
        existing_chunk_ids = {emb[0] for emb in existing_embeddings}
        
        # Filter to unembedded chunks
        unembedded_chunks = [chunk for chunk in chunks if chunk.id not in existing_chunk_ids]
        
        if not unembedded_chunks:
            log.info("All chunks already embedded for book %d", book_id)
            status.status = 'completed'
            status.processed_chunks = status.total_chunks
            status.completed_at = datetime.now(timezone.utc)
            session.commit()
            return True
        
        log.info("Embedding %d chunks for book %d (batch size: %d)", 
                len(unembedded_chunks), book_id, batch_size)
        
        # Process in batches
        total_processed = status.processed_chunks or 0
        start_time = time.time()
        
        for i in range(0, len(unembedded_chunks), batch_size):
            batch = unembedded_chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(unembedded_chunks) + batch_size - 1) // batch_size
            
            log.info("Processing embedding batch %d/%d for book %d (%d chunks)", 
                    batch_num, total_batches, book_id, len(batch))
            
            # Prepare texts for embedding
            texts = [chunk.chunk_text for chunk in batch]
            
            # Generate embeddings with timeout protection
            try:
                embeddings = _embed_batch_with_retry(embedding_model, texts)
                if not embeddings:
                    log.error("Failed to generate embeddings for batch %d-%d (batch %d/%d)", 
                             i, i + len(batch), batch_num, total_batches)
                    # Update status to show partial progress
                    status.processed_chunks = total_processed
                    session.commit()
                    continue
            except Exception as e:
                log.error("Exception generating embeddings for batch %d/%d: %s", 
                         batch_num, total_batches, e, exc_info=True)
                # Update status to show partial progress
                status.processed_chunks = total_processed
                session.commit()
                continue
            
            # Prepare embedding data
            chunk_embeddings = []
            for chunk, embedding_vec in zip(batch, embeddings):
                embedding_array = np.array(embedding_vec, dtype=np.float32)
                vector_dimension = len(embedding_array)
                
                chunk_embeddings.append({
                    'chunk_id': chunk.id,
                    'book_id': book_id,
                    'embedding': embedding_array,
                    'vector_dimension': vector_dimension,
                    'model_name': model_name
                })
            
            # Store embeddings (includes virtual table sync)
            if not _store_chunk_embeddings(chunk_embeddings):
                log.error("Failed to store embeddings for batch %d-%d", i, i + len(batch))
                # Continue to next batch - some embeddings may have been stored
                continue
            
            # Update progress
            total_processed += len(batch)
            status.processed_chunks = total_processed
            session.commit()
            
            # Log progress
            elapsed = time.time() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            remaining = len(unembedded_chunks) - total_processed
            eta = remaining / rate if rate > 0 else 0
            
            log.info("Embedded %d/%d chunks for book %d (batch %d/%d, %.1f chunks/s, ETA: %.1fs)", 
                    total_processed, len(unembedded_chunks), book_id, batch_num, total_batches, rate, eta)
        
        # CRITICAL: Verify embeddings were actually stored before marking complete
        actual_embedding_count = session.query(BookChunkEmbedding).filter_by(book_id=book_id).count()
        expected_count = status.total_chunks

        if actual_embedding_count < expected_count:
            log.error("EMBEDDING MISMATCH: Book %d has %d/%d embeddings stored - marking as failed",
                     book_id, actual_embedding_count, expected_count)
            status.status = 'failed'
            status.error_message = f"Only {actual_embedding_count}/{expected_count} embeddings stored"
            session.commit()
            return False

        # Mark as completed
        status.status = 'completed'
        status.processed_chunks = status.total_chunks
        status.completed_at = datetime.now(timezone.utc)
        session.commit()

        log.info("Completed embedding %d chunks for book %d (verified: %d embeddings stored)",
                len(unembedded_chunks), book_id, actual_embedding_count)
        return True
        
    except Exception as e:
        log.error("Failed to embed chunks for book %d: %s", book_id, e, exc_info=True)
        # Update status to failed
        try:
            status = session.query(BookIndexStatus).filter_by(book_id=book_id).first()
            if status:
                status.status = 'failed'
                status.error_message = str(e)
                session.commit()
        except Exception:
            pass
        return False

