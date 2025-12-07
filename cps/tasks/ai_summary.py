# -*- coding: utf-8 -*-

"""
Background task for AI summary generation.
"""

from .. import app, db, logger
from ..services.worker import CalibreTask
from ..ai.summarization import generate_summary
from flask_babel import lazy_gettext as N_

log = logger.create()


class TaskGenerateAISummary(CalibreTask):
    """Background task to generate AI summary for a book."""
    
    def __init__(self, book_id, task_message='Generating AI summary'):
        super(TaskGenerateAISummary, self).__init__(task_message)
        self.book_id = book_id
        self.log = logger.create()
    
    @property
    def name(self):
        return N_("Generate AI Summary")
    
    def __str__(self):
        # Override __str__ to return a plain string, avoiding LazyString issues
        # This matches the pattern used by other tasks like TaskConvert
        return "Generate AI Summary for Book {}".format(self.book_id)
    
    @property
    def is_cancellable(self):
        return False
    
    def run(self, worker_thread):
        """Execute the summary generation task."""
        with app.app_context():
            try:
                # Get book title for message
                calibre_db = db.CalibreDB()
                book = calibre_db.get_book(self.book_id)
                book_title = book.title if book else f"Book {self.book_id}"
                
                # Update message with book title
                self.message = f"Generating AI summary for {book_title}"
                
                # Step 1: Text extraction (progress: 0.3)
                self.progress = 0.0
                self.message = "Extracting text..."
                
                # Step 2: Generate summary (progress: 0.6)
                self.progress = 0.3
                self.message = "Generating summary..."
                
                # Call summarization service
                log.info("Starting summary generation for book %d", self.book_id)
                result = generate_summary(self.book_id)
                
                # Log the result for debugging
                if result:
                    log.debug("Summary generation returned result (length: %d, starts with: %s)", 
                             len(result), result[:50] if len(result) > 50 else result)
                else:
                    log.warning("Summary generation returned None or empty result")
                
                # Verify summary was saved to database
                try:
                    from .. import ub
                    saved_summary = ub.session.query(ub.BookSummary).filter(
                        ub.BookSummary.book_id == self.book_id
                    ).first()
                    if saved_summary:
                        log.debug("Verified summary exists in database after generation (id: %d)", saved_summary.id)
                    else:
                        log.warning("Summary generation completed but summary not found in database for book %d", self.book_id)
                except Exception as e:
                    log.warning("Error verifying summary in database: %s", e)
                
                # Check if generation was successful
                # Success if result is a non-empty string that doesn't start with error indicators
                if result and isinstance(result, str) and len(result) > 0:
                    # All error messages from generate_summary() start with "Error:" or "Failed:"
                    result_lower = result.lower()
                    is_error = result_lower.startswith("error:") or result_lower.startswith("failed:")
                    
                    if not is_error:
                        # Success - result is the summary text
                        # The summarization service has already verified the save using direct sqlite3
                        self.progress = 1.0
                        self.message = "Complete"
                        self._handleSuccess()
                        log.info("AI summary generated successfully for book %d (length: %d chars)", 
                                self.book_id, len(result))
                    else:
                        # Error from summarization service
                        error_msg = result if result else "Unknown error during summary generation"
                        # Ensure error_msg is a string (not LazyString)
                        error_msg = str(error_msg)
                        # Force LazyString to string if needed
                        if hasattr(error_msg, '_value'):
                            error_msg = str(error_msg._value) if error_msg._value else error_msg
                        self._handleError(error_msg)
                        log.error("AI summary generation failed for book %d: %s", self.book_id, error_msg)
                else:
                    # Empty or None result
                    error_msg = "Summary generation returned no result"
                    self._handleError(error_msg)
                    log.error("AI summary generation failed for book %d: %s", self.book_id, error_msg)
                    
            except Exception as e:
                from ..ai.llm_utils import safe_str
                error_msg = f"Task failed: {safe_str(e)}"
                self._handleError(error_msg)
                log.exception("Exception in TaskGenerateAISummary for book %d: %s", self.book_id, e)

