# -*- coding: utf-8 -*-

"""
Background task for full book indexing (chunking and embedding).
"""

from .. import app, db, logger, ub
from ..services.worker import CalibreTask
from ..ai.chunking import chunk_book
from ..ai.chunk_embeddings import embed_chunks
from flask_babel import lazy_gettext as N_

log = logger.create()


class TaskFullBookIndex(CalibreTask):
    """Background task to fully index a book (chunk and embed)."""
    
    def __init__(self, book_id, task_message='Indexing book'):
        super(TaskFullBookIndex, self).__init__(task_message)
        self.book_id = book_id
        self.log = logger.create()
    
    @property
    def name(self):
        return N_("Full Book Index")
    
    def __str__(self):
        return "Full Book Index for Book {}".format(self.book_id)
    
    @property
    def is_cancellable(self):
        return True  # Can be cancelled (stops after current batch)
    
    def run(self, worker_thread):
        """Execute the full book indexing task."""
        with app.app_context():
            try:
                # Get book title for message
                calibre_db = db.CalibreDB()
                book = calibre_db.get_book(self.book_id)
                book_title = book.title if book else f"Book {self.book_id}"
                
                # Update message with book title
                self.message = f"Indexing {book_title}"
                
                # Step 1: Chunking (progress: 0.0 - 0.3)
                # Check if chunks already exist
                from ..ub import BookChunk
                existing_chunks = ub.session.query(BookChunk).filter_by(book_id=self.book_id).count()
                
                if existing_chunks > 0:
                    log.info("Book %d already has %d chunks, skipping chunking step", self.book_id, existing_chunks)
                    # Get chunk IDs for progress tracking
                    chunk_ids = [chunk.id for chunk in ub.session.query(BookChunk).filter_by(book_id=self.book_id).all()]
                else:
                    self.progress = 0.0
                    self.message = f"Chunking {book_title}..."
                    log.info("Starting chunking for book %d", self.book_id)
                    
                    chunk_ids = chunk_book(self.book_id)
                    
                    if not chunk_ids:
                        error_msg = "Chunking failed or produced no chunks"
                        self._handleError(error_msg)
                        log.error("Full book indexing failed for book %d: %s", self.book_id, error_msg)
                        return
                    
                    log.info("Chunked book %d into %d chunks", self.book_id, len(chunk_ids))
                
                # Step 2: Embedding (progress: 0.3 - 1.0)
                self.progress = 0.3
                self.message = f"Embedding {len(chunk_ids)} chunks for {book_title}..."
                log.info("Starting embedding for book %d (%d chunks)", self.book_id, len(chunk_ids))
                
                # Update status to processing
                from ..ub import BookIndexStatus
                status = ub.session.query(BookIndexStatus).filter_by(book_id=self.book_id).first()
                if status:
                    status.status = 'processing'
                    ub.session.commit()
                    log.info("Updated status to 'processing' for book %d", self.book_id)
                
                try:
                    success = embed_chunks(self.book_id)
                except Exception as embed_error:
                    log.exception("Exception in embed_chunks for book %d: %s", self.book_id, embed_error)
                    success = False
                    # Update status to failed
                    if status:
                        status.status = 'failed'
                        status.error_message = str(embed_error)[:500]
                        ub.session.commit()
                
                if success:
                    # Success
                    self.progress = 1.0
                    self.message = "Complete"
                    self._handleSuccess()
                    log.info("Full book indexing completed successfully for book %d", self.book_id)
                    # Update status to completed
                    if status:
                        status.status = 'completed'
                        from datetime import datetime, timezone
                        status.completed_at = datetime.now(timezone.utc)
                        ub.session.commit()
                else:
                    # Error from embedding service
                    error_msg = "Embedding failed - check logs for details"
                    self._handleError(error_msg)
                    log.error("Full book indexing failed for book %d: %s", self.book_id, error_msg)
                    # Update status to failed
                    if status:
                        status.status = 'failed'
                        status.error_message = error_msg
                        ub.session.commit()
                    
            except Exception as e:
                # Safely convert exception to string
                error_str = str(e) if e else "Unknown error"
                error_msg = f"Task failed: {error_str}"
                self._handleError(error_msg)
                log.exception("Exception in TaskFullBookIndex for book %d: %s", self.book_id, e)


