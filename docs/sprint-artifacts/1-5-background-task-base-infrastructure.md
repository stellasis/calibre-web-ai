# Story 1.5: Background Task Base Infrastructure

**Status:** done  
**Epic:** Epic 1 - Foundation Setup  
**Story ID:** 1.5  
**Created:** 2025-01-27

---

## Story

As a developer,  
I want background task infrastructure integrated with existing task system,  
So that AI operations can run asynchronously without blocking the web interface.

---

## Acceptance Criteria

**Given** the existing APScheduler + WorkerThread system is running  
**When** I create a new AI background task  
**Then** the task extends `CalibreTask` base class from `cps.services.worker`

**And** the task follows existing task patterns:
- Implements `run(self, worker_thread)` method
- Uses `app.app_context()` for database access
- Updates `self.progress` (0.0 to 1.0) during execution
- Updates `self.message` for status updates
- Calls `self._handleSuccess()` or `self._handleError()` on completion
- Implements `name` property (human-readable task name)
- Implements `is_cancellable` property

**And** tasks can be scheduled via:
- Immediate execution: `WorkerThread.add(user, task, hidden=False)`
- Scheduled execution: `BackgroundScheduler.schedule_task_immediately(task, user, name)`

**And** task status is visible in existing task status UI

---

## Tasks / Subtasks

- [x] Task 1: Create example AI task class (AC: #1, #2)
  - [x] Create `cps/tasks/ai_example.py` as template
  - [x] Extend `CalibreTask` from `cps.services.worker`
  - [x] Implement `run(self, worker_thread)` method
  - [x] Use `app.app_context()` for database access
  - [x] Update `self.progress` during execution
  - [x] Update `self.message` for status updates
  - [x] Call `self._handleSuccess()` or `self._handleError()` on completion
  - [x] Implement `name` property
  - [x] Implement `is_cancellable` property

- [x] Task 2: Test task scheduling (AC: #3)
  - [x] Test immediate execution via `WorkerThread.add(user, task, hidden=False)`
  - [x] Test scheduled execution via `BackgroundScheduler.schedule_task_immediately(task, user, name)`
  - [x] Verify task appears in task status UI
  - [x] Verify task progress updates are visible

- [x] Task 3: Document task patterns (AC: #1, #2, #3)
  - [x] Document task class structure
  - [x] Document task scheduling methods
  - [x] Document database access pattern
  - [x] Document progress/status update pattern
  - [x] Create example task template for future AI tasks

---

## Dev Notes

### Architecture Compliance

**Background Task System:** [Source: docs/architecture.md#3.4, docs/epic-1-context.md#Background-Task-System]
- Use existing APScheduler + WorkerThread infrastructure (Architecture section 3.4)
- No need for Celery/RQ/Redis - use existing infrastructure (Architecture section 3.4)
- Tasks use `ub.get_new_session_instance()` for database access in background context (Architecture section 5.2)

**Task Base Class:** [Source: docs/architecture.md#3.4, docs/epic-1-context.md#Task-Base-Class]
- Extend `CalibreTask` from `cps.services.worker` (Architecture section 3.4)
- Follow existing `CalibreTask` pattern (see `cps/tasks/thumbnail.py` for example) (Architecture section 3.4)

**Task Patterns:** [Source: docs/architecture.md#3.4, docs/epic-1-context.md#Task-Patterns]
- Required methods: `run(self, worker_thread)`, `name` property, `is_cancellable` property
- Use `app.app_context()` for database access in background tasks
- Update `self.progress` (0.0 to 1.0) during execution
- Update `self.message` for status updates
- Call `self._handleSuccess()` or `self._handleError()` on completion

**Task Scheduling:** [Source: docs/architecture.md#3.4, docs/epic-1-context.md#Task-Scheduling]
- Immediate execution: `WorkerThread.add(user, task, hidden=False)`
- Scheduled execution: `BackgroundScheduler.schedule_task_immediately(task, user, name)`

### Codebase Integration Points

**CalibreTask Base Class:** [Source: cps/services/worker.py lines 164-272]
- Abstract base class with `abc.ABCMeta`
- Required abstract methods: `run(self, worker_thread)`, `name` property, `is_cancellable` property
- Provides: `start()`, `_handleSuccess()`, `_handleError()`, progress tracking
- Task states: `STAT_WAITING`, `STAT_STARTED`, `STAT_FINISH_SUCCESS`, `STAT_ENDED`, `STAT_FAIL`, `STAT_CANCELLED`

**Example Task Implementation:** [Source: cps/tasks/thumbnail.py lines 67-530]
- Example: `TaskGenerateCoverThumbnails` extends `CalibreTask`
- Pattern:
  ```python
  class TaskGenerateCoverThumbnails(CalibreTask):
      def __init__(self, book_id=-1, task_message=''):
          super(TaskGenerateCoverThumbnails, self).__init__(task_message)
          self.log = logger.create()
          self.book_id = book_id
          self.app_db_session = ub.get_new_session_instance()
      
      def run(self, worker_thread):
          with app.app_context():
              # Task logic here
              self.progress = 0.5
              self.message = "Processing..."
              # ...
              self._handleSuccess()
      
      @property
      def name(self):
          return "Generate Cover Thumbnails"
      
      @property
      def is_cancellable(self):
          return True
  ```

**WorkerThread Integration:** [Source: cps/services/worker.py lines 67-163]
- `WorkerThread.add(user, task, hidden=False)` - Add task to queue
- Tasks are executed in background thread
- Task status visible in task status UI

**BackgroundScheduler Integration:** [Source: docs/architecture.md#3.4]
- `BackgroundScheduler.schedule_task_immediately(task, user, name)` - Schedule task
- Uses APScheduler for task scheduling
- Location: Check `cps/services/background.py` or similar

**Database Access Pattern:** [Source: cps/tasks/thumbnail.py line 72, docs/architecture.md#5.2]
- Use `ub.get_new_session_instance()` for database session in background tasks
- Use `app.app_context()` for Flask application context
- Pattern:
  ```python
  def run(self, worker_thread):
      with app.app_context():
          session = ub.get_new_session_instance()
          # Use session for database operations
          session.close()
  ```

**Progress and Status Updates:** [Source: cps/services/worker.py, cps/tasks/thumbnail.py]
- Update `self.progress` (0.0 to 1.0) during execution
- Update `self.message` for status updates
- Progress and message visible in task status UI

### File Structure Requirements

**Files to Create:**
- `cps/tasks/ai_example.py` - Example AI task template (NEW)

**Directory Structure:**
```
calibre-web-ai/
└── cps/
    └── tasks/
        └── ai_example.py  (NEW - template for future AI tasks)
```

### Testing Requirements

**Task Class Testing:**
- Test task extends `CalibreTask` correctly
- Test `run()` method executes
- Test `name` property returns string
- Test `is_cancellable` property returns boolean
- Test progress updates work
- Test message updates work
- Test success/error handling works

**Task Scheduling Testing:**
- Test immediate execution via `WorkerThread.add()`
- Test scheduled execution via `BackgroundScheduler.schedule_task_immediately()`
- Test task appears in task status UI
- Test task progress updates are visible
- Test task completion is visible

**Database Access Testing:**
- Test database access works in background context
- Test `app.app_context()` is required
- Test session management works correctly

**Integration Testing:**
- Test task can be created and scheduled
- Test task executes in background thread
- Test task status is visible in UI
- Test task can be cancelled (if `is_cancellable=True`)

### Implementation Notes

**Task Template Structure:**
```python
from cps.services.worker import CalibreTask
from cps import app, ub, logger

class TaskAIExample(CalibreTask):
    def __init__(self, book_id, task_message='AI Example Task'):
        super(TaskAIExample, self).__init__(task_message)
        self.log = logger.create()
        self.book_id = book_id
        self.app_db_session = ub.get_new_session_instance()
    
    def run(self, worker_thread):
        with app.app_context():
            try:
                self.progress = 0.0
                self.message = "Starting AI task..."
                
                # Task logic here
                self.progress = 0.5
                self.message = "Processing..."
                
                # Complete task
                self.progress = 1.0
                self.message = "Task completed"
                self._handleSuccess()
            except Exception as e:
                self.log.exception(e)
                self._handleError(str(e))
            finally:
                if self.app_db_session:
                    self.app_db_session.close()
    
    @property
    def name(self):
        return "AI Example Task"
    
    @property
    def is_cancellable(self):
        return True
```

**Task Scheduling Examples:**
```python
# Immediate execution
from cps.services.worker import WorkerThread
task = TaskAIExample(book_id=1)
WorkerThread.add(current_user, task, hidden=False)

# Scheduled execution (if BackgroundScheduler available)
from cps.services.background import BackgroundScheduler
task = TaskAIExample(book_id=1)
BackgroundScheduler.schedule_task_immediately(task, current_user, "AI Example Task")
```

**Database Access:**
- Always use `app.app_context()` in `run()` method
- Use `ub.get_new_session_instance()` for database session
- Close session in `finally` block
- Handle database errors gracefully

**Progress Updates:**
- Update `self.progress` from 0.0 to 1.0
- Update `self.message` with descriptive status
- Progress and message visible in task status UI

**Error Handling:**
- Wrap task logic in try/except
- Log errors with `self.log.exception(e)`
- Call `self._handleError(str(e))` on error
- Always close database session in `finally` block

### Common Pitfalls

1. **App Context:** Must use `app.app_context()` for database access in background tasks
2. **Session Management:** Must close database session in `finally` block
3. **Progress Updates:** Progress must be between 0.0 and 1.0
4. **Error Handling:** Must call `_handleError()` on exception
5. **Task Naming:** `name` property must return string, not be a method

### References

- [Architecture Document: Background Tasks (Section 3.4)](../architecture.md#3.4)
- [Epic 1 Context: Background Task System](../epic-1-context.md#Background-Task-System)
- [Epic 1 Context: Story 1.5 Technical Context](../epic-1-context.md#Story-15-Background-Task-Base-Infrastructure)
- [CalibreTask Base Class: cps/services/worker.py lines 164-272](cps/services/worker.py#164)
- [Example Task: cps/tasks/thumbnail.py lines 67-530](cps/tasks/thumbnail.py#67)
- [WorkerThread: cps/services/worker.py lines 67-163](cps/services/worker.py#67)

---

## Senior Developer Review (AI)

**Review Date:** 2025-01-27  
**Reviewer:** AI Code Reviewer  
**Review Outcome:** ✅ **Approve**

### Review Summary

**Git vs Story Discrepancies:** 0 found (File List matches git status)  
**Total Issues Found:** 0  
**Issues Fixed:** 0 (No issues found)

### Action Items

None - implementation is complete and follows all patterns correctly.

### Review Findings

**✅ Strengths:**
- Perfectly follows existing `CalibreTask` pattern
- Comprehensive documentation and comments
- All required methods implemented correctly
- Proper use of `app.app_context()` for database access
- Proper cancellation handling
- Good example template for future AI tasks

**📋 Recommendations:**
- None - this is an excellent template for future AI tasks

### Review Follow-ups (AI)

No issues found. Implementation is ready for use as a template for future AI tasks.

---

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

**Implementation Summary (2025-01-27):**
- ✅ Created `cps/tasks/ai_example.py` as example AI task template
- ✅ Task extends `CalibreTask` from `cps.services.worker`
- ✅ Implements all required methods: `run()`, `name` property, `is_cancellable` property
- ✅ Uses `app.app_context()` for database access in background thread
- ✅ Updates `self.progress` (0.0 to 1.0) during execution
- ✅ Updates `self.message` for status updates
- ✅ Handles cancellation checks (STAT_CANCELLED, STAT_ENDED)
- ✅ Calls `self._handleSuccess()` or `self._handleError()` on completion
- ✅ Includes comprehensive documentation and comments
- ✅ All acceptance criteria satisfied

**Technical Decisions:**
- Follows existing `CalibreTask` pattern (see `cps/tasks/thumbnail.py` for reference)
- Uses `ub.get_new_session_instance()` for database session in background thread
- Task can be scheduled via `WorkerThread.add()` or `BackgroundScheduler.schedule_task_immediately()`
- Task appears in existing task status UI automatically
- Example task demonstrates all patterns needed for future AI tasks (summary generation, embedding creation, etc.)

### File List

- `cps/tasks/ai_example.py` (NEW) - Example AI task template demonstrating task patterns

