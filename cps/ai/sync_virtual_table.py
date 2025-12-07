# -*- coding: utf-8 -*-

"""
Utility to re-sync existing embeddings to the virtual table.
Use this if embeddings exist but virtual table is empty (e.g., after fixing sqlite-vec loading).
"""

import os
from typing import Optional
import numpy as np
from sqlalchemy import create_engine, text

from .. import config, logger, ub
from ..ub import session, BookChunkEmbedding

log = logger.create()


def resync_book_to_virtual_table(book_id: int) -> bool:
    """
    Re-sync all embeddings for a book to the virtual table.
    
    Args:
        book_id: Book ID to re-sync
    
    Returns:
        True if successful, False otherwise
    """
    db_path = getattr(ub, 'app_DB_path', None)
    if not db_path:
        log.error("Database path not configured")
        return False
    
    db_path = os.path.abspath(db_path)
    
    try:
        # Get all embeddings for this book
        embeddings = session.query(BookChunkEmbedding).filter_by(book_id=book_id).all()
        
        if not embeddings:
            log.warning("No embeddings found for book %d", book_id)
            return False
        
        log.info("Re-syncing %d embeddings for book %d to virtual table", len(embeddings), book_id)
        
        engine = create_engine(
            f'sqlite:///{db_path}',
            echo=False,
            connect_args={'check_same_thread': False}
        )
        
        with engine.connect() as conn:
            # Load sqlite-vec
            try:
                import sqlite_vec
                raw_conn = conn.connection.dbapi_connection
                raw_conn.enable_load_extension(True)
                sqlite_vec.load(raw_conn)
                raw_conn.enable_load_extension(False)
            except ImportError:
                log.error("sqlite-vec package not installed")
                return False
            except Exception as e:
                log.error("Failed to load sqlite-vec: %s", e)
                return False
            
            # Ensure virtual table exists
            from .chunk_embeddings import _ensure_chunk_virtual_table
            if not _ensure_chunk_virtual_table(conn):
                log.error("Failed to ensure virtual table exists")
                return False
            
            # Sync each embedding
            synced_count = 0
            for emb in embeddings:
                try:
                    # Get embedding bytes (already stored as BLOB)
                    embedding_bytes = emb.vector
                    
                    # Delete existing entry
                    conn.execute(
                        text("DELETE FROM book_chunk_embeddings_vec WHERE chunk_id = :chunk_id"),
                        {"chunk_id": emb.chunk_id}
                    )
                    
                    # Insert into virtual table
                    conn.execute(
                        text("INSERT INTO book_chunk_embeddings_vec (chunk_id, embedding) VALUES (:chunk_id, :embedding)"),
                        {"chunk_id": emb.chunk_id, "embedding": embedding_bytes}
                    )
                    synced_count += 1
                except Exception as e:
                    log.warning("Failed to sync chunk %d: %s", emb.chunk_id, e)
            
            conn.commit()
            log.info("Successfully synced %d/%d embeddings to virtual table for book %d", 
                    synced_count, len(embeddings), book_id)
            
            return synced_count == len(embeddings)
            
    except Exception as e:
        log.error("Failed to re-sync book %d: %s", book_id, e, exc_info=True)
        return False


def resync_all_to_virtual_table() -> dict:
    """
    Re-sync all embeddings in the database to the virtual table.
    
    Returns:
        Dict with 'total', 'synced', 'failed' counts
    """
    db_path = getattr(ub, 'app_DB_path', None)
    if not db_path:
        log.error("Database path not configured")
        return {'total': 0, 'synced': 0, 'failed': 0}
    
    db_path = os.path.abspath(db_path)
    
    try:
        # Get all unique book IDs with embeddings
        book_ids = session.query(BookChunkEmbedding.book_id).distinct().all()
        book_ids = [row[0] for row in book_ids]
        
        log.info("Re-syncing %d books to virtual table", len(book_ids))
        
        results = {'total': len(book_ids), 'synced': 0, 'failed': 0}
        
        for book_id in book_ids:
            if resync_book_to_virtual_table(book_id):
                results['synced'] += 1
            else:
                results['failed'] += 1
        
        log.info("Re-sync complete: %d synced, %d failed", results['synced'], results['failed'])
        return results
        
    except Exception as e:
        log.error("Failed to re-sync all: %s", e, exc_info=True)
        return {'total': 0, 'synced': 0, 'failed': 0}

