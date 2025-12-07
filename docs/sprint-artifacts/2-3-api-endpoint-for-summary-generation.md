# Story 2.3: API Endpoint for Summary Generation

**Status:** done  
**Epic:** Epic 2 - AI Summary Feature  
**Story ID:** 2.3  
**Created:** 2025-12-04

---

## Story

As a user,  
I want an API endpoint to trigger summary generation,  
So that the UI can request summaries asynchronously.

---

## Acceptance Criteria

**Given** I am an authenticated user  
**When** I POST to `/api/ai/summary/<int:book_id>`  
**Then** the endpoint:

1. Checks `config.config_ai_enabled` - returns 403 if disabled
2. Validates `book_id` exists in calibre database
3. Enqueues `TaskGenerateAISummary` background task (from Story 2.2)
4. Returns JSON response: `{'status': 'queued', 'book_id': book_id, 'message': 'Summary generation started'}`

**And** route implementation:
- File: Extend `cps/web.py` or create `cps/ai.py` blueprint
- Route: `@ai.route("/api/ai/summary/<int:book_id>", methods=['POST'])`
- Decorator: `@login_required_if_no_ano` (from `cps.usermanagement`)
- Function: `generate_summary(book_id)`

**And** error handling:
- AI disabled: Return `{'error': 'AI features disabled'}, 403`
- Book not found: Return `{'error': 'Book not found'}, 404`
- Unauthorized: Return `{'error': 'Unauthorized'}, 401`
- Server error: Return `{'error': 'Summary generation failed'}, 500`

**And** if summary already exists:
- Option A: Return existing summary immediately
- Option B: Regenerate summary (based on user preference - implement refresh button in UI)

---

## Tasks / Subtasks

- [ ] Task 1: Create AI blueprint (AC: route implementation)
  - [ ] Create `cps/ai.py` blueprint file
  - [ ] Import Flask and required dependencies
  - [ ] Create blueprint: `ai = Blueprint('ai', __name__)`
  - [ ] Register blueprint in `cps/main.py`

- [ ] Task 2: Implement API endpoint (AC: endpoint behavior)
  - [ ] Create route `/api/ai/summary/<int:book_id>`
  - [ ] Add `@login_required_if_no_ano` decorator
  - [ ] Check `config.config_ai_enabled`
  - [ ] Validate book exists
  - [ ] Enqueue `TaskGenerateAISummary` task
  - [ ] Return JSON response

- [ ] Task 3: Implement error handling (AC: error handling)
  - [ ] Handle AI disabled (403)
  - [ ] Handle book not found (404)
  - [ ] Handle unauthorized (401)
  - [ ] Handle server errors (500)

- [ ] Task 4: Test integration (AC: all)
  - [ ] Test with AI enabled
  - [ ] Test with AI disabled
  - [ ] Test with invalid book_id
  - [ ] Test unauthorized access
  - [ ] Verify task is enqueued

---

## Dev Notes

### Architecture Compliance

**Blueprint Pattern:** [Source: docs/architecture.md#3.2]
- Create new `cps/ai.py` blueprint
- Register in `cps/main.py` via `app.register_blueprint(ai)`
- Follow existing blueprint patterns

**Route Implementation:** [Source: docs/architecture.md#3.2, docs/epics/epic-2-summary.md#Story-2.3]
- Use `@login_required_if_no_ano` decorator
- Return JSON responses using `jsonify()`
- Follow existing API endpoint patterns

**Task Integration:** [Source: docs/architecture.md#3.4, docs/epics/epic-2-summary.md#Story-2.3]
- Use `WorkerThread.add(user, task, hidden=False)` to enqueue task
- Task from Story 2.2: `TaskGenerateAISummary`

**Error Handling:** [Source: docs/architecture.md#5.3]
- Use `jsonify()` for API errors
- Return appropriate HTTP status codes
- Follow existing error handling patterns

### Technical Implementation Details

**Blueprint Creation:**
```python
from flask import Blueprint
ai = Blueprint('ai', __name__)
```

**Route Handler:**
```python
@ai.route("/api/ai/summary/<int:book_id>", methods=['POST'])
@login_required_if_no_ano
def generate_summary(book_id):
    # Implementation
```

**Task Enqueueing:**
```python
from cps.services.worker import WorkerThread
from cps.tasks.ai_summary import TaskGenerateAISummary
from flask_login import current_user

task = TaskGenerateAISummary(book_id)
WorkerThread.add(current_user, task, hidden=False)
```

**Response Format:**
```python
from flask import jsonify
return jsonify({'status': 'queued', 'book_id': book_id, 'message': 'Summary generation started'}), 202
```

### File Structure

```
cps/
  ai.py              # NEW: AI blueprint with routes
  main.py            # MODIFY: Register ai blueprint
```

### Dependencies

**Required:**
- `flask.Blueprint` - Blueprint creation
- `flask.jsonify` - JSON responses
- `cps.services.worker.WorkerThread` - Task enqueueing
- `cps.tasks.ai_summary.TaskGenerateAISummary` - Background task
- `cps.usermanagement.login_required_if_no_ano` - Authentication decorator

### References

- [Source: docs/architecture.md#3.2] - Route patterns
- [Source: docs/architecture.md#3.4] - Task integration
- [Source: docs/epics/epic-2-summary.md#Story-2.3] - Story requirements
- [Source: cps/web.py] - Existing route examples

---

## Dev Agent Record

### Context Reference

### Agent Model Used

Auto (Cursor AI)

### Debug Log References

### Completion Notes List

### File List

- `cps/ai.py` - AI blueprint with API endpoint
- `cps/main.py` - Blueprint registration

### Completion Notes List

- ✅ Created `cps/ai.py` blueprint
- ✅ Implemented `/api/ai/summary/<int:book_id>` endpoint
- ✅ Added authentication via `@login_required_if_no_ano`
- ✅ Implemented error handling (403, 404, 401, 500)
- ✅ Integrated with background task system
- ✅ Returns existing summary if available (optional feature)
