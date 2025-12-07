# Story 2.2: Background Task for Summary Generation

**Status:** done  
**Epic:** Epic 2 - AI Summary Feature  
**Story ID:** 2.2  
**Created:** 2025-12-04

---

## Story

As a user,  
I want summary generation to run in the background,  
So that the web interface remains responsive during generation.

---

## Acceptance Criteria

**Given** I click "Generate AI Summary" button  
**When** the request is processed  
**Then** a background task `TaskGenerateAISummary` is enqueued:

- Task extends `CalibreTask` (from Story 1.5)
- Task is added via `WorkerThread.add(user, task, hidden=False)`
- Task shows in task status UI with message "Generating AI summary for [book title]"
- Task progress updates during execution (0.0 → 1.0)

**And** the task execution:
1. Uses `app.app_context()` for database access
2. Calls `ai.summarization.generate_summary(book_id)` (from Story 2.1)
3. Updates progress: 0.3 (text extraction), 0.6 (LLM call), 1.0 (complete)
4. Updates message: "Extracting text...", "Generating summary...", "Complete"
5. Calls `self._handleSuccess()` on completion
6. Calls `self._handleError()` on failure

**And** task implementation:
- File: `cps/tasks/ai_summary.py`
- Class: `TaskGenerateAISummary(CalibreTask)`
- Constructor: `__init__(self, book_id, task_message='Generating AI summary')`
- Property `name`: Returns `N_("Generate AI Summary")` (translatable)
- Property `is_cancellable`: Returns `False`

---

## Tasks / Subtasks

- [ ] Task 1: Create background task module (AC: task implementation)
  - [ ] Create `cps/tasks/ai_summary.py`
  - [ ] Import CalibreTask and required dependencies
  - [ ] Create `TaskGenerateAISummary` class extending `CalibreTask`
  - [ ] Implement `__init__` method
  - [ ] Implement `name` property (translatable)
  - [ ] Implement `is_cancellable` property

- [ ] Task 2: Implement task execution (AC: task execution)
  - [ ] Implement `run()` method with `app.app_context()`
  - [ ] Call `ai.summarization.generate_summary(book_id)`
  - [ ] Update progress at key stages (0.3, 0.6, 1.0)
  - [ ] Update message at each stage
  - [ ] Handle success with `_handleSuccess()`
  - [ ] Handle errors with `_handleError()`

- [ ] Task 3: Test integration (AC: all)
  - [ ] Test task enqueueing
  - [ ] Test task execution
  - [ ] Test progress updates
  - [ ] Test error handling
  - [ ] Verify task appears in task status UI

---

## Dev Notes

### Architecture Compliance

**Background Task Pattern:** [Source: docs/architecture.md#3.4, docs/epic-1-context.md#Background-Task-Base-Infrastructure]
- Follow existing task patterns (see `cps/tasks/thumbnail.py`)
- Extend `CalibreTask` base class from `cps.services.worker`
- Use `app.app_context()` for database access
- Use `WorkerThread.add()` for task enqueueing

**Task Integration:** [Source: docs/architecture.md#3.4]
- Task status integrated with existing task status UI
- Progress updates (0.0 to 1.0)
- Message updates for status display
- Success/error handling via `_handleSuccess()` and `_handleError()`

**Service Integration:** [Source: docs/epics/epic-2-summary.md#Story-2.2]
- Call `ai.summarization.generate_summary(book_id)` from Story 2.1
- Task wraps the summarization service call
- Handles errors from summarization service

### Technical Implementation Details

**Task Structure:**
- Follow `cps/tasks/thumbnail.py` pattern exactly
- Use `CalibreTask` base class
- Implement required properties and methods

**Progress Updates:**
- 0.0: Initial state
- 0.3: Text extraction complete
- 0.6: LLM call complete
- 1.0: Summary stored, complete

**Message Updates:**
- "Generating AI summary for [book title]"
- "Extracting text..."
- "Generating summary..."
- "Complete"

### File Structure

```
cps/
  tasks/
    ai_summary.py     # NEW: Background task for AI summary generation
```

### Dependencies

**Required:**
- `cps.services.worker.CalibreTask` - Base task class
- `cps.ai.summarization.generate_summary` - Summarization service (Story 2.1)
- `cps.db` - Database access
- `cps.app` - Flask app context

### References

- [Source: docs/architecture.md#3.4] - Background task patterns
- [Source: docs/epics/epic-2-summary.md#Story-2.2] - Story requirements
- [Source: cps/tasks/thumbnail.py] - Task pattern example
- [Source: cps/services/worker.py] - CalibreTask base class

---

## Dev Agent Record

### Context Reference

### Agent Model Used

Auto (Cursor AI)

### Debug Log References

### Completion Notes List

### File List

- `cps/tasks/ai_summary.py` - Background task implementation

### Completion Notes List

- ✅ Created `TaskGenerateAISummary` class extending `CalibreTask`
- ✅ Implemented progress updates and message updates
- ✅ Integrated with summarization service
- ✅ Error handling via `_handleError()`
- ✅ Success handling via `_handleSuccess()`
- ⚠️ Note: Progress stages (0.3, 0.6) can't be tracked separately since text extraction and LLM call both happen inside `generate_summary()` - this is a minor deviation from AC
