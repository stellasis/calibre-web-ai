# -*- coding: utf-8 -*-

"""
AI features blueprint for calibre-web-ai.
"""

from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from .. import config, logger, calibre_db, csrf
from ..services.worker import WorkerThread
from ..tasks.ai_summary import TaskGenerateAISummary
from ..tasks.ai_full_index import TaskFullBookIndex
from ..usermanagement import login_required_if_no_ano
from ..cw_login import current_user
from ..admin import admin_required

log = logger.create()

ai = Blueprint('ai', __name__, url_prefix='')


# Exempt AI API endpoints from CSRF (they use authentication via login_required)
# This follows the same pattern as kobo.py API endpoints
def exempt_from_csrf(view_func):
    """Decorator to exempt a view from CSRF protection if csrf is enabled."""
    if csrf:
        return csrf.exempt(view_func)
    return view_func


@ai.route("/api/ai/summary/<int:book_id>/status", methods=['GET'])
@login_required_if_no_ano
@exempt_from_csrf
def get_summary_status(book_id):
    """
    Check if summary exists for a book and task status.
    
    Returns:
        JSON with summary status, text if available, and task status
    """
    log.debug("Summary status endpoint called for book %d", book_id)
    
    if not config.config_ai_enabled:
        log.warning("Summary status check attempted but AI is disabled")
        return jsonify({'error': 'AI features disabled'}), 403
    
    try:
        from .. import ub
        from ..services.worker import WorkerThread, STAT_WAITING, STAT_STARTED, STAT_FAIL, STAT_FINISH_SUCCESS
        from sqlalchemy import create_engine
        
        # Check if summary exists using SQLAlchemy Core (raw SQL)
        # This ensures we see the latest committed data from background tasks
        import os
        from sqlalchemy import text
        
        summary_data = None
        db_path = getattr(ub, 'app_DB_path', None)
        if db_path:
            # CRITICAL: Use absolute path to match what summarization uses
            db_path = os.path.abspath(db_path)
            log.debug("Checking summary status in database: %s", db_path)
            
            engine = None
            conn = None
            try:
                engine = create_engine(
                    f'sqlite:///{db_path}',
                    echo=False,
                    connect_args={'check_same_thread': False}
                )
                conn = engine.connect()
                
                result = conn.execute(
                    text("SELECT summary_text, created_at FROM book_summaries WHERE book_id = :book_id"),
                    {"book_id": book_id}
                ).fetchone()
                
                if result:
                    summary_data = {
                        'summary_text': result[0],
                        'created_at': result[1]
                    }
                    log.debug("Found summary for book %d (length: %d)", book_id, len(result[0]))
                else:
                    log.debug("No summary found for book %d in %s", book_id, db_path)
                
            except Exception as e:
                log.error("Error checking summary: %s", e, exc_info=True)
            finally:
                if conn:
                    conn.close()
                if engine:
                    engine.dispose()
        
        # Check for running/failed tasks for this book
        task_status = None
        task_error = None
        try:
            tasks = WorkerThread.get_instance().tasks
            for _, _, _, task, _ in tasks:
                # Check if this is an AI summary task for this book
                if hasattr(task, 'book_id') and task.book_id == book_id:
                    if task.stat == STAT_WAITING:
                        task_status = 'waiting'
                    elif task.stat == STAT_STARTED:
                        task_status = 'running'
                        task_error = task.message if hasattr(task, 'message') else None
                    elif task.stat == STAT_FAIL:
                        task_status = 'failed'
                        task_error = task.error if hasattr(task, 'error') and task.error else 'Unknown error'
                    elif task.stat == STAT_FINISH_SUCCESS:
                        task_status = 'completed'
                    break
        except Exception as e:
            log.debug("Error checking task status: %s", e)
        
        if summary_data:
            return jsonify({
                'status': 'exists',
                'summary': summary_data['summary_text'],
                'created_at': summary_data['created_at'],
                'task_status': task_status
            }), 200
        else:
            return jsonify({
                'status': 'not_found',
                'task_status': task_status,
                'task_error': task_error
            }), 200
    except Exception as e:
        log.error("Error checking summary status: %s", e, exc_info=True)
        return jsonify({'error': f'Error checking summary: {str(e)}'}), 500


@ai.route("/api/ai/summary/<int:book_id>", methods=['POST'])
@login_required_if_no_ano
@exempt_from_csrf
def generate_summary(book_id):
    """
    API endpoint to trigger AI summary generation.
    
    Args:
        book_id: Book ID from database
    
    Returns:
        JSON response with status
    """
    # Check if AI is enabled
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    # Validate book exists
    try:
        book = calibre_db.get_book(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404
    except Exception as e:
        log.error("Error validating book %d: %s", book_id, e, exc_info=True)
        return jsonify({'error': f'Book validation failed: {str(e)}'}), 500
    
    # Check if summary already exists (optional: return existing)
    try:
        from .. import ub
        existing_summary = ub.session.query(ub.BookSummary).filter(
            ub.BookSummary.book_id == book_id
        ).first()
        
        # Option: Return existing summary if present and not regenerating
        if existing_summary and not request.args.get('regenerate'):
            return jsonify({
                'status': 'exists',
                'book_id': book_id,
                'summary': existing_summary.summary_text,
                'message': 'Summary already exists'
            }), 200
    except Exception as e:
        log.warning("Error checking existing summary: %s", e)
        # Continue to generate new summary
    
    # Enqueue background task
    try:
        task = TaskGenerateAISummary(book_id)
        # Pass username string for consistency with other endpoints
        username = current_user.name if current_user.is_authenticated else 'System'
        WorkerThread.add(username, task, hidden=False)
        
        return jsonify({
            'status': 'queued',
            'book_id': book_id,
            'message': 'Summary generation started'
        }), 202
    except Exception as e:
        from .llm_utils import safe_str

        log.error("Error enqueueing summary task: %s", e, exc_info=True)
        error_msg = safe_str(e)
        if 'langchain' in error_msg.lower():
            error_msg = 'LangChain not installed. Install with: pip install langchain langchain-openai langchain-anthropic langchain-community'
        elif 'api' in error_msg.lower() or 'key' in error_msg.lower():
            error_msg = 'API key not configured or invalid. Check admin settings.'
        else:
            error_msg = f'Failed to start summary generation: {error_msg}'
        return jsonify({'error': error_msg}), 500


@ai.route("/api/ai/index/<int:book_id>", methods=['POST'])
@login_required_if_no_ano
@exempt_from_csrf
def start_indexing(book_id):
    """
    API endpoint to trigger full book indexing.
    
    Args:
        book_id: Book ID from database
    
    Returns:
        JSON response with status
    """
    # Check if AI is enabled
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    # Check if full indexing is enabled
    if not getattr(config, 'config_ai_full_index_enabled', False):
        return jsonify({'error': 'Full book indexing is disabled'}), 403
    
    # Validate book exists
    try:
        book = calibre_db.get_book(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404
    except Exception as e:
        log.error("Error validating book %d: %s", book_id, e, exc_info=True)
        return jsonify({'error': f'Book validation failed: {str(e)}'}), 500
    
    # Check if already indexed or in progress
    try:
        from .. import ub
        from ..ub import BookChunk, BookChunkEmbedding
        from sqlalchemy import text, create_engine
        
        status = ub.session.query(ub.BookIndexStatus).filter_by(book_id=book_id).first()
        
        if status:
            if status.status == 'completed':
                # Check if embeddings actually exist using a fresh connection to bypass ORM caching
                try:
                    db_path = ub.app_DB_path
                    engine = create_engine(f'sqlite:///{db_path}', echo=False)
                    with engine.connect() as conn:
                        chunk_count = conn.execute(
                            text("SELECT COUNT(*) FROM book_chunks WHERE book_id = :book_id"),
                            {"book_id": book_id}
                        ).scalar() or 0
                        embedding_count = conn.execute(
                            text("SELECT COUNT(*) FROM book_chunk_embeddings WHERE book_id = :book_id"),
                            {"book_id": book_id}
                        ).scalar() or 0
                    engine.dispose()
                except Exception as e:
                    log.warning("Fresh connection failed, using ORM: %s", e)
                    chunk_count = ub.session.query(BookChunk).filter_by(book_id=book_id).count()
                    embedding_count = ub.session.query(BookChunkEmbedding).filter_by(book_id=book_id).count()
                
                if chunk_count > 0 and embedding_count == chunk_count:
                    # Truly completed - embeddings exist
                    return jsonify({
                        'status': 'already_indexed',
                        'book_id': book_id,
                        'total_chunks': status.total_chunks,
                        'message': 'Book already indexed'
                    }), 200
                else:
                    # Status says completed but embeddings missing/incomplete - reset and re-index
                    log.info("Book %d status is 'completed' but has %d/%d embeddings - resetting for re-index", 
                            book_id, embedding_count, chunk_count)
                    status.status = 'pending'
                    status.processed_chunks = 0
                    status.error_message = None
                    ub.session.commit()
                    # Continue to start indexing
            elif status.status == 'processing':
                # Check if the task is stale (no update in 5 minutes)
                stale_threshold = timedelta(minutes=5)
                now = datetime.now(timezone.utc)
                
                # Handle timezone-naive updated_at from database
                updated_at = status.updated_at
                if updated_at and updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                
                if updated_at and (now - updated_at) > stale_threshold:
                    # Task is stale - likely crashed or timed out
                    log.warning("Book %d indexing task appears stale (last update: %s) - allowing re-index", 
                               book_id, updated_at)
                    status.status = 'failed'
                    status.error_message = 'Previous task timed out - resuming'
                    ub.session.commit()
                    # Continue to start indexing (will resume from where it left off)
                else:
                    return jsonify({
                        'status': 'in_progress',
                        'book_id': book_id,
                        'message': 'Indexing already in progress',
                        'last_update': updated_at.isoformat() if updated_at else None
                    }), 200
            elif status.status == 'failed':
                # Reset failed status to allow retry
                log.info("Book %d status is 'failed' - resetting for retry", book_id)
                status.status = 'pending'
                status.error_message = None
                ub.session.commit()
                # Continue to start indexing
    except Exception as e:
        log.warning("Error checking index status: %s", e)
        # Continue to start indexing
    
    # Enqueue background task
    try:
        task = TaskFullBookIndex(book_id)
        username = current_user.name if current_user.is_authenticated else 'System'
        WorkerThread.add(username, task, hidden=False)
        
        return jsonify({
            'status': 'started',
            'book_id': book_id,
            'message': 'Indexing started'
        }), 202
    except Exception as e:
        log.error("Error enqueueing indexing task: %s", e, exc_info=True)
        return jsonify({'error': f'Failed to start indexing: {str(e)}'}), 500


@ai.route("/api/ai/index/<int:book_id>/status", methods=['GET'])
@login_required_if_no_ano
@exempt_from_csrf
def get_index_status(book_id):
    """
    Get indexing status for a book.
    
    Returns:
        JSON with indexing status and progress
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    try:
        from .. import ub
        from ..ub import BookChunk, BookChunkEmbedding
        from sqlalchemy import text, create_engine
        
        status = ub.session.query(ub.BookIndexStatus).filter_by(book_id=book_id).first()
        
        if not status:
            return jsonify({
                'status': 'not_indexed',
                'book_id': book_id
            }), 200
        
        # Get actual counts using a fresh connection to bypass ORM caching entirely
        # This ensures we see data written by background tasks via raw connections
        try:
            db_path = ub.app_DB_path
            engine = create_engine(f'sqlite:///{db_path}', echo=False)
            with engine.connect() as conn:
                chunk_count = conn.execute(
                    text("SELECT COUNT(*) FROM book_chunks WHERE book_id = :book_id"),
                    {"book_id": book_id}
                ).scalar() or 0
                embedding_count = conn.execute(
                    text("SELECT COUNT(*) FROM book_chunk_embeddings WHERE book_id = :book_id"),
                    {"book_id": book_id}
                ).scalar() or 0
            engine.dispose()
        except Exception as e:
            log.warning("Fresh connection failed, falling back to ORM: %s", e)
            chunk_count = ub.session.query(BookChunk).filter_by(book_id=book_id).count()
            embedding_count = ub.session.query(BookChunkEmbedding).filter_by(book_id=book_id).count()
        
        # Calculate progress percentage
        progress = 0.0
        if status.total_chunks > 0:
            progress = (status.processed_chunks / status.total_chunks) * 100.0
        
        # Determine actual state
        actual_status = status.status
        is_stale = False
        
        # Check if processing task is stale (no update in 5 minutes)
        if status.status == 'processing':
            stale_threshold = timedelta(minutes=5)
            now = datetime.now(timezone.utc)
            updated_at = status.updated_at
            if updated_at and updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            if updated_at and (now - updated_at) > stale_threshold:
                is_stale = True
                actual_status = 'stale'
        
        # Only override status if NOT actively processing
        if status.status != 'processing':
            if chunk_count > 0 and embedding_count == 0:
                # Chunks exist but no embeddings - embedding failed
                actual_status = 'chunked_but_not_embedded'
            elif chunk_count > embedding_count:
                # Partial embedding
                actual_status = 'partially_embedded'
            elif chunk_count == embedding_count and embedding_count > 0:
                # Fully embedded
                actual_status = 'completed'
        
        return jsonify({
            'status': actual_status,
            'book_id': book_id,
            'total_chunks': status.total_chunks,
            'processed_chunks': status.processed_chunks,
            'chunk_count': chunk_count,  # Actual count from database
            'embedding_count': embedding_count,  # Actual count from database
            'progress': round(progress, 1),
            'is_stale': is_stale,
            'error_message': status.error_message,
            'started_at': status.started_at.isoformat() if status.started_at else None,
            'completed_at': status.completed_at.isoformat() if status.completed_at else None
        }), 200
    except Exception as e:
        log.error("Error getting index status: %s", e, exc_info=True)
        return jsonify({'error': f'Error getting status: {str(e)}'}), 500


@ai.route("/api/ai/index/<int:book_id>/resync", methods=['POST'])
@admin_required
@exempt_from_csrf
def resync_index(book_id):
    """
    Re-sync existing embeddings to virtual table (useful if virtual table is empty).
    
    Returns:
        JSON with status
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    if not getattr(config, 'config_ai_full_index_enabled', False):
        return jsonify({'error': 'Full book indexing is disabled'}), 403
    
    try:
        from .sync_virtual_table import resync_book_to_virtual_table
        
        success = resync_book_to_virtual_table(book_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'book_id': book_id,
                'message': 'Embeddings re-synced to virtual table'
            }), 200
        else:
            return jsonify({
                'status': 'failed',
                'book_id': book_id,
                'error': 'Failed to re-sync embeddings. Check logs for details.'
            }), 500
            
    except Exception as e:
        log.error("Error re-syncing index for book %d: %s", book_id, e, exc_info=True)
        return jsonify({'error': f'Error: {str(e)}'}), 500


@ai.route("/api/ai/index/<int:book_id>/reset", methods=['POST'])
@login_required_if_no_ano
@exempt_from_csrf
def reset_index_status(book_id):
    """
    Reset indexing status to allow re-indexing.
    
    Returns:
        JSON with status
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    if not getattr(config, 'config_ai_full_index_enabled', False):
        return jsonify({'error': 'Full book indexing is disabled'}), 403
    
    try:
        from .. import ub
        
        status = ub.session.query(ub.BookIndexStatus).filter_by(book_id=book_id).first()
        
        if status:
            status.status = 'pending'
            status.error_message = None
            status.started_at = None
            status.completed_at = None
            status.updated_at = datetime.now(timezone.utc)
            ub.session.commit()
            
            return jsonify({
                'status': 'reset',
                'book_id': book_id,
                'message': 'Status reset to pending'
            }), 200
        else:
            return jsonify({
                'status': 'not_found',
                'book_id': book_id
            }), 404
            
    except Exception as e:
        log.error("Error resetting index status for book %d: %s", book_id, e, exc_info=True)
        return jsonify({'error': f'Error: {str(e)}'}), 500


@ai.route("/api/ai/index/<int:book_id>", methods=['DELETE'])
@admin_required
@exempt_from_csrf
def delete_index(book_id):
    """
    Delete book index (remove all chunks and embeddings).
    
    Requires admin permission.
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    try:
        from .. import ub
        from ..ub import BookChunk, BookChunkEmbedding, BookIndexStatus
        
        # Delete chunks (embeddings will cascade delete)
        ub.session.query(BookChunk).filter_by(book_id=book_id).delete()
        
        # Delete embeddings directly (in case cascade didn't work)
        ub.session.query(BookChunkEmbedding).filter_by(book_id=book_id).delete()
        
        # Delete status
        ub.session.query(BookIndexStatus).filter_by(book_id=book_id).delete()
        
        ub.session.commit()
        
        # Also delete from virtual table
        try:
            import os
            from sqlalchemy import create_engine, text
            db_path = getattr(ub, 'app_DB_path', None)
            if db_path:
                db_path = os.path.abspath(db_path)
                engine = create_engine(
                    f'sqlite:///{db_path}',
                    echo=False,
                    connect_args={'check_same_thread': False}
                )
                with engine.connect() as conn:
                    # Get chunk IDs that were deleted
                    # Note: We need to delete from virtual table before deleting chunks
                    # But since we already deleted, we'll just try to clean up any orphaned entries
                    conn.execute(
                        text("DELETE FROM book_chunk_embeddings_vec WHERE chunk_id IN "
                             "(SELECT chunk_id FROM book_chunk_embeddings WHERE book_id = :book_id)"),
                        {"book_id": book_id}
                    )
                    conn.commit()
                engine.dispose()
        except Exception as e:
            log.warning("Error cleaning virtual table: %s", e)
        
        return jsonify({
            'status': 'deleted',
            'book_id': book_id,
            'message': 'Index deleted'
        }), 200
    except Exception as e:
        log.error("Error deleting index: %s", e, exc_info=True)
        return jsonify({'error': f'Error deleting index: {str(e)}'}), 500


@ai.route("/api/ai/index/search", methods=['POST'])
@login_required_if_no_ano
@exempt_from_csrf
def search_indexed_content():
    """
    Search within indexed book chunks.
    
    Request body:
        {
            "query": "search text",
            "book_id": optional book ID to filter,
            "limit": optional limit (default 20)
        }
    
    Returns:
        JSON with search results
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    if not getattr(config, 'config_ai_full_index_enabled', False):
        return jsonify({'error': 'Full book indexing is disabled'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        book_id = data.get('book_id')
        limit = data.get('limit', 20)
        
        from ..ai.chunk_search import search_chunks
        
        results = search_chunks(query, book_id=book_id, limit=limit)
        
        # Format results for JSON response
        formatted_results = []
        for result in results:
            formatted_results.append({
                'chunk_id': result['chunk_id'],
                'book_id': result['book_id'],
                'chunk_index': result['chunk_index'],
                'chunk_text': result['chunk_text'],
                'chapter_title': result['chapter_title'],
                'similarity_score': result['similarity_score'],
                'book': {
                    'id': result['book'].id if result['book'] else None,
                    'title': result['book'].title if result['book'] else None,
                    'authors': [a.name for a in result['book'].authors] if result['book'] and result['book'].authors else []
                } if result['book'] else None
            })
        
        return jsonify({
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results)
        }), 200
    except Exception as e:
        log.error("Error searching indexed content: %s", e, exc_info=True)
        return jsonify({'error': f'Search failed: {str(e)}'}), 500


@ai.route("/api/ai/index/stats", methods=['GET'])
@login_required_if_no_ano
@exempt_from_csrf
def get_index_stats():
    """
    Get indexing statistics.
    
    Returns:
        JSON with total indexed books, chunks, and storage estimate
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    if not getattr(config, 'config_ai_full_index_enabled', False):
        return jsonify({'error': 'Full book indexing is disabled'}), 403
    
    try:
        from .. import ub
        from ..ub import BookIndexStatus, BookChunk, BookChunkEmbedding
        from sqlalchemy import func
        
        # Count indexed books
        indexed_count = ub.session.query(BookIndexStatus).filter_by(status='completed').count()
        
        # Count total chunks
        total_chunks = ub.session.query(func.count(BookChunk.id)).scalar() or 0
        
        # Estimate storage (rough: ~6KB per chunk embedding)
        storage_estimate_mb = (total_chunks * 6) / 1024.0  # MB
        
        return jsonify({
            'indexed_books': indexed_count,
            'total_chunks': total_chunks,
            'storage_estimate_mb': round(storage_estimate_mb, 2)
        }), 200
    except Exception as e:
        log.error("Error getting index stats: %s", e, exc_info=True)
        return jsonify({'error': f'Error getting stats: {str(e)}'}), 500


@ai.route("/api/ai/index/bulk/all", methods=['POST'])
@admin_required
@exempt_from_csrf
def bulk_index_all():
    """
    Bulk index all books in the library.
    
    Returns:
        JSON with count of books queued for indexing
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    if not getattr(config, 'config_ai_full_index_enabled', False):
        return jsonify({'error': 'Full book indexing is disabled'}), 403
    
    try:
        from .. import ub, db
        from ..ub import BookIndexStatus
        
        # Get all books (use allow_show_archived=True for admin operations)
        all_books = calibre_db.session.query(db.Books).filter(
            calibre_db.common_filters(allow_show_archived=True)
        ).all()
        
        # Get already indexed book IDs
        indexed_book_ids = set(
            ub.session.query(BookIndexStatus.book_id)
            .filter_by(status='completed')
            .all()
        )
        indexed_book_ids = {row[0] for row in indexed_book_ids}
        
        # Get books in progress
        processing_book_ids = set(
            ub.session.query(BookIndexStatus.book_id)
            .filter_by(status='processing')
            .all()
        )
        processing_book_ids = {row[0] for row in processing_book_ids}
        
        # Queue indexing for books that aren't indexed or processing
        queued_count = 0
        username = current_user.name if current_user.is_authenticated else 'System'
        
        for book in all_books:
            if book.id not in indexed_book_ids and book.id not in processing_book_ids:
                try:
                    task = TaskFullBookIndex(book.id)
                    WorkerThread.add(username, task, hidden=False)
                    queued_count += 1
                except Exception as e:
                    log.warning("Failed to queue indexing for book %d: %s", book.id, e)
        
        return jsonify({
            'status': 'queued',
            'queued_count': queued_count,
            'total_books': len(all_books),
            'already_indexed': len(indexed_book_ids),
            'in_progress': len(processing_book_ids),
            'message': f'Queued {queued_count} books for indexing'
        }), 200
    except Exception as e:
        log.error("Error in bulk index all: %s", e, exc_info=True)
        return jsonify({'error': f'Bulk indexing failed: {str(e)}'}), 500


@ai.route("/api/ai/index/bulk/unindexed", methods=['POST'])
@admin_required
@exempt_from_csrf
def bulk_index_unindexed():
    """
    Bulk index only books that haven't been indexed yet.
    
    Returns:
        JSON with count of books queued for indexing
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    if not getattr(config, 'config_ai_full_index_enabled', False):
        return jsonify({'error': 'Full book indexing is disabled'}), 403
    
    try:
        from .. import ub, db
        from ..ub import BookIndexStatus
        
        # Get all books (use allow_show_archived=True for admin operations)
        all_books = calibre_db.session.query(db.Books).filter(
            calibre_db.common_filters(allow_show_archived=True)
        ).all()
        
        # Get indexed book IDs (completed or processing)
        indexed_book_ids = set(
            ub.session.query(BookIndexStatus.book_id)
            .filter(BookIndexStatus.status.in_(['completed', 'processing']))
            .all()
        )
        indexed_book_ids = {row[0] for row in indexed_book_ids}
        
        # Queue indexing for unindexed books
        queued_count = 0
        username = current_user.name if current_user.is_authenticated else 'System'
        
        for book in all_books:
            if book.id not in indexed_book_ids:
                try:
                    task = TaskFullBookIndex(book.id)
                    WorkerThread.add(username, task, hidden=False)
                    queued_count += 1
                except Exception as e:
                    log.warning("Failed to queue indexing for book %d: %s", book.id, e)
        
        return jsonify({
            'status': 'queued',
            'queued_count': queued_count,
            'total_books': len(all_books),
            'already_indexed': len(indexed_book_ids),
            'message': f'Queued {queued_count} unindexed books for indexing'
        }), 200
    except Exception as e:
        log.error("Error in bulk index unindexed: %s", e, exc_info=True)
        return jsonify({'error': f'Bulk indexing failed: {str(e)}'}), 500


@ai.route("/api/ai/index/queue", methods=['GET'])
@admin_required
@exempt_from_csrf
def get_indexing_queue():
    """
    Get current indexing queue status.
    
    Returns:
        JSON with list of pending/processing indexing tasks
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    if not getattr(config, 'config_ai_full_index_enabled', False):
        return jsonify({'error': 'Full book indexing is disabled'}), 403
    
    try:
        from ..services.worker import WorkerThread, STAT_WAITING, STAT_STARTED
        
        tasks = WorkerThread.get_instance().tasks
        indexing_tasks = []
        
        for _, _, _, task, _ in tasks:
            # Check if this is an indexing task
            if isinstance(task, TaskFullBookIndex):
                task_info = {
                    'book_id': task.book_id,
                    'status': 'waiting' if task.stat == STAT_WAITING else 'processing' if task.stat == STAT_STARTED else 'unknown',
                    'message': getattr(task, 'message', ''),
                    'progress': getattr(task, 'progress', 0.0)
                }
                indexing_tasks.append(task_info)
        
        return jsonify({
            'tasks': indexing_tasks,
            'count': len(indexing_tasks)
        }), 200
    except Exception as e:
        log.error("Error getting indexing queue: %s", e, exc_info=True)
        return jsonify({'error': f'Error getting queue: {str(e)}'}), 500


# ============================================================================
# Chatbot API Endpoints
# ============================================================================

@ai.route("/api/ai/chatbot/<int:book_id>/ask", methods=['POST'])
@login_required_if_no_ano
@exempt_from_csrf
def ask_book_question(book_id):
    """
    Ask a question about a book using the RAG chatbot.
    
    Request body:
        {
            'question': 'user question',
            'conversation_history': [{'question': str, 'answer': str}, ...]  # optional
        }
    
    Returns:
        JSON with answer, chunks_used, confidence, and optional error
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    if not getattr(config, 'config_ai_chatbot_enabled', False):
        return jsonify({'error': 'Chatbot feature disabled'}), 403
    
    try:
        from .chatbot import ask_question
        
        # Log request details for debugging
        log.debug("Chatbot ask request - Content-Type: %s, Method: %s, book_id: %d", 
                 request.content_type, request.method, book_id)
        
        # Validate Content-Type (be more lenient - check if JSON can be parsed)
        content_type = request.content_type or ''
        if content_type and 'application/json' not in content_type.lower():
            # Try to parse JSON anyway - some clients send wrong content-type
            try:
                data = request.get_json(force=True)
                log.warning("Content-Type was %s but JSON parsed successfully", content_type)
            except Exception:
                log.error("Invalid Content-Type: %s, and JSON parsing failed", content_type)
                return jsonify({'error': 'Content-Type must be application/json'}), 400
        else:
            # Get request data
            data = request.get_json() or {}
        
        # Log request data (sanitized)
        log.debug("Chatbot ask request data - question length: %d, has_history: %s", 
                 len(data.get('question', '')), bool(data.get('conversation_history')))
        
        question = data.get('question', '').strip()
        conversation_history = data.get('conversation_history', None)
        
        # Validate conversation_history structure
        if conversation_history is not None:
            if not isinstance(conversation_history, list):
                log.error("Invalid conversation_history type: %s (expected list)", type(conversation_history))
                return jsonify({'error': 'conversation_history must be a list'}), 400
            if len(conversation_history) > 10:
                log.warning("conversation_history too long: %d (max 10)", len(conversation_history))
                return jsonify({'error': 'conversation_history cannot exceed 10 exchanges'}), 400
            for i, exchange in enumerate(conversation_history):
                if not isinstance(exchange, dict):
                    log.error("conversation_history[%d] is not a dict: %s", i, type(exchange))
                    return jsonify({'error': 'conversation_history must contain dicts with question and answer keys'}), 400
                if 'question' not in exchange or 'answer' not in exchange:
                    log.error("conversation_history[%d] missing keys: %s", i, list(exchange.keys()))
                    return jsonify({'error': 'conversation_history must contain dicts with question and answer keys'}), 400
        
        # Validate question
        if not question:
            log.error("Empty question provided")
            return jsonify({'error': 'Question is required'}), 400
        
        # Validate book exists
        try:
            book = calibre_db.get_book(book_id)
            if not book:
                return jsonify({'error': 'Book not found'}), 404
        except Exception as e:
            log.error("Error fetching book %d: %s", book_id, e)
            return jsonify({'error': 'Book not found'}), 404
        
        # Call chatbot service
        result = ask_question(book_id, question, conversation_history)
        
        # Check for errors - use standardized response format
        if result.get('error'):
            error_msg = result['error']
            status_code = 500  # Default to 500 for LLM/unknown errors
            
            # Map specific errors to HTTP status codes (improved mapping)
            error_lower = error_msg.lower()
            if 'not indexed' in error_lower or 'index the book' in error_lower or 'not embedded' in error_lower:
                status_code = 400
            elif 'not found' in error_lower:
                status_code = 404
            elif 'disabled' in error_lower:
                status_code = 403
            elif 'timeout' in error_lower or 'timed out' in error_lower:
                status_code = 504
            elif 'api key' in error_lower or 'not configured' in error_lower:
                status_code = 503  # Service unavailable due to misconfiguration
            
            # Return standardized error response
            return jsonify({
                'error': error_msg,
                'answer': '',
                'chunks_used': [],
                'confidence': 0.0
            }), status_code
        
        # Return success response
        # Serialize chunks_used to avoid "Books is not JSON serializable" error
        chunks_used = result.get('chunks_used', [])
        serialized_chunks = []
        for chunk in chunks_used:
            serialized_chunk = {
                'chunk_id': chunk.get('chunk_id'),
                'book_id': chunk.get('book_id'),
                'chunk_index': chunk.get('chunk_index'),
                'chunk_text': chunk.get('chunk_text'),
                'chapter_title': chunk.get('chapter_title'),
                'similarity_score': chunk.get('similarity_score'),
            }
            # Serialize book object if present
            book = chunk.get('book')
            if book:
                serialized_chunk['book'] = {
                    'id': book.id if hasattr(book, 'id') else None,
                    'title': book.title if hasattr(book, 'title') else None,
                }
            serialized_chunks.append(serialized_chunk)

        return jsonify({
            'answer': result.get('answer', ''),
            'chunks_used': serialized_chunks,
            'confidence': result.get('confidence', 0.0)
        }), 200
        
    except Exception as e:
        log.error("Error in ask_book_question: %s", e, exc_info=True)
        return jsonify({'error': 'Failed to generate answer'}), 500


@ai.route("/api/ai/chatbot/<int:book_id>/status", methods=['GET'])
@login_required_if_no_ano
@exempt_from_csrf
def get_chatbot_status(book_id):
    """
    Check chatbot availability for a book.
    
    Returns:
        JSON with available, book_indexed, and optional reason
    """
    if not config.config_ai_enabled:
        return jsonify({
            'available': False,
            'book_indexed': False,
            'reason': 'AI features disabled'
        }), 200
    
    if not getattr(config, 'config_ai_chatbot_enabled', False):
        return jsonify({
            'available': False,
            'book_indexed': False,
            'reason': 'Chatbot feature disabled'
        }), 200
    
    try:
        from .chatbot import _check_book_indexed
        
        # Check if book exists
        try:
            book = calibre_db.get_book(book_id)
            if not book:
                return jsonify({
                    'available': False,
                    'book_indexed': False,
                    'reason': 'Book not found'
                }), 404
        except Exception as e:
            log.error("Error fetching book %d: %s", book_id, e)
            return jsonify({
                'available': False,
                'book_indexed': False,
                'reason': 'Book not found'
            }), 404
        
        # Check if book is indexed
        book_indexed = _check_book_indexed(book_id)
        
        return jsonify({
            'available': book_indexed,
            'book_indexed': book_indexed,
            'reason': None if book_indexed else 'Book is not indexed'
        }), 200
        
    except Exception as e:
        log.error("Error in get_chatbot_status: %s", e, exc_info=True)
        return jsonify({
            'available': False,
            'book_indexed': False,
            'reason': f'Error checking status: {str(e)}'
        }), 500


@ai.route("/api/ai/chatbot/<int:book_id>/clear", methods=['POST'])
@login_required_if_no_ano
@exempt_from_csrf
def clear_chatbot_history(book_id):
    """
    Clear conversation history for a book.
    
    Note: This endpoint is a no-op for client-side history (localStorage).
    It validates the book exists and returns success. Actual history clearing
    is handled client-side via localStorage. This endpoint exists for API
    consistency and future server-side history support (if implemented).
    
    Returns:
        JSON with status: {'status': 'cleared'}
    """
    if not config.config_ai_enabled:
        return jsonify({'error': 'AI features disabled'}), 403
    
    if not getattr(config, 'config_ai_chatbot_enabled', False):
        return jsonify({'error': 'Chatbot feature disabled'}), 403
    
    try:
        # Validate book exists
        book = calibre_db.get_book(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        
        # For now, this is a no-op (history is client-side)
        # In Story 7.4, this could clear server-side history if implemented
        return jsonify({'status': 'cleared'}), 200
        
    except Exception as e:
        log.error("Error in clear_chatbot_history: %s", e, exc_info=True)
        return jsonify({'error': f'Error clearing history: {str(e)}'}), 500
