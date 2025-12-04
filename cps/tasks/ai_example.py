# -*- coding: utf-8 -*-

"""
Example AI task class demonstrating the pattern for AI background tasks.
This serves as a template for future AI tasks (e.g., TaskGenerateAISummary).
"""

from .. import app, config, logger, ub
from ..services.worker import CalibreTask, STAT_CANCELLED, STAT_ENDED
from flask_babel import lazy_gettext as N_

log = logger.create()


class TaskAIExample(CalibreTask):
    """
    Example AI task demonstrating the pattern for AI background operations.
    
    This task shows how to:
    - Extend CalibreTask base class
    - Use app.app_context() for database access
    - Update progress and message during execution
    - Handle cancellation and errors
    """
    
    def __init__(self, task_message='AI Example Task'):
        super(TaskAIExample, self).__init__(task_message)
        self.log = logger.create()
        # Get database session for background thread
        self.app_db_session = ub.get_new_session_instance()
    
    @property
    def name(self):
        """Human-readable task name."""
        return N_('AI Example Task')
    
    @property
    def is_cancellable(self):
        """This task can be cancelled."""
        return True
    
    def run(self, worker_thread):
        """
        Main task execution method.
        
        This method runs in a background thread and must:
        - Use app.app_context() for database access
        - Update self.progress (0.0 to 1.0) during execution
        - Update self.message for status updates
        - Check for cancellation (STAT_CANCELLED, STAT_ENDED)
        - Call self._handleSuccess() or self._handleError() on completion
        """
        # Check if task was cancelled before starting
        if self.stat == STAT_CANCELLED or self.stat == STAT_ENDED:
            return
        
        # Use app context for database access in background thread
        with app.app_context():
            try:
                # Example: Check AI configuration
                if not config.config_ai_enabled:
                    self._handleError("AI features are disabled")
                    return
                
                self.message = N_('Starting AI example task...')
                self.progress = 0.1
                
                # Check for cancellation
                if self.stat == STAT_CANCELLED or self.stat == STAT_ENDED:
                    return
                
                # Example: Do some work
                self.message = N_('Processing...')
                self.progress = 0.5
                
                # Simulate work (replace with actual AI operation)
                # Example: Generate summary, create embedding, etc.
                
                # Check for cancellation during work
                if self.stat == STAT_CANCELLED or self.stat == STAT_ENDED:
                    return
                
                # Example: Complete work
                self.message = N_('Finalizing...')
                self.progress = 0.9
                
                # Check for cancellation before completion
                if self.stat == STAT_CANCELLED or self.stat == STAT_ENDED:
                    return
                
                # Success!
                self.message = N_('AI example task completed successfully')
                self.progress = 1.0
                self._handleSuccess()
                
            except Exception as e:
                self.log.error("AI example task failed: %s", e)
                self._handleError(str(e))
            finally:
                # Clean up database session
                if self.app_db_session:
                    self.app_db_session.close()




