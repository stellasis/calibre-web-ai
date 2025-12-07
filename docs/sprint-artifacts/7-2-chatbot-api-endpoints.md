# Story 7.2: Chatbot API Endpoints

**Status:** ready-for-dev  
**Epic:** Epic 7 - Book Chatbot (RAG Q&A)  
**Story ID:** 7.2  
**Created:** 2025-01-27  
**Prerequisites:** Story 7.1 (RAG Chatbot Service)

---

## Story

As a developer,  
I want API endpoints for chatbot interactions,  
So that the UI can send questions and receive answers.

---

## Acceptance Criteria

**AC1:** `POST /api/ai/chatbot/<int:book_id>/ask` - Ask a question
- Request body: `{'question': 'user question', 'conversation_history': optional list}`
- Requires authentication (`@login_required_if_no_ano`)
- Returns JSON: `{'answer': str, 'chunks_used': list, 'error': optional}`
- Validates book_id exists and is indexed
- Returns 400 if question is empty
- Returns 403 if chatbot is disabled
- Returns 404 if book not found
- Returns 400 if book not indexed

**AC2:** `GET /api/ai/chatbot/<int:book_id>/status` - Check chatbot availability
- Returns JSON: `{'available': bool, 'book_indexed': bool, 'reason': optional str}`
- Checks if book is indexed (required for chatbot)
- Checks if chatbot feature is enabled
- Useful for UI to show/hide chatbot interface

**AC3:** `POST /api/ai/chatbot/<int:book_id>/clear` - Clear conversation history (optional)
- Clears any stored conversation history for the book
- Returns `{'status': 'cleared'}`
- Useful for starting fresh conversations

**And** route implementation:
- File: Extend `cps/ai/__init__.py` blueprint
- Routes: `@ai.route("/api/ai/chatbot/<int:book_id>/ask", methods=['POST'])`
- Decorator: `@login_required_if_no_ano` (from `cps.usermanagement`)
- Function: `ask_book_question(book_id)`
- Function: `get_chatbot_status(book_id)`
- Function: `clear_chatbot_history(book_id)` (optional)

**And** error handling:
- AI disabled: Return `{'error': 'AI features disabled'}, 403`
- Chatbot disabled: Return `{'error': 'Chatbot feature disabled'}, 403`
- Book not found: Return `{'error': 'Book not found'}, 404`
- Book not indexed: Return `{'error': 'Book is not indexed'}, 400`
- Empty question: Return `{'error': 'Question is required'}, 400`
- LLM errors: Return `{'error': 'Failed to generate answer'}, 500`

---

## Tasks / Subtasks

- [x] Task 1: Add ask question endpoint (AC: AC1)
  - [x] Add route `POST /api/ai/chatbot/<int:book_id>/ask`
  - [x] Add `@login_required_if_no_ano` decorator
  - [x] Add `@exempt_from_csrf` decorator
  - [x] Parse request body for question and conversation_history
  - [x] Validate question is not empty
  - [x] Validate book exists
  - [x] Call `ai.chatbot.ask_question()` service
  - [x] Return appropriate HTTP status codes
  - [x] Return JSON response with answer, chunks_used, confidence

- [x] Task 2: Add status check endpoint (AC: AC2)
  - [x] Add route `GET /api/ai/chatbot/<int:book_id>/status`
  - [x] Add `@login_required_if_no_ano` decorator
  - [x] Add `@exempt_from_csrf` decorator
  - [x] Check AI enabled and chatbot enabled
  - [x] Check if book is indexed
  - [x] Return JSON with available, book_indexed, reason

- [x] Task 3: Add clear history endpoint (AC: AC3)
  - [x] Add route `POST /api/ai/chatbot/<int:book_id>/clear`
  - [x] Add `@login_required_if_no_ano` decorator
  - [x] Add `@exempt_from_csrf` decorator
  - [x] Validate book exists
  - [x] Return status cleared (placeholder for client-side history)

- [x] Task 4: Implement error handling (AC: error handling)
  - [x] Handle AI disabled (403)
  - [x] Handle chatbot disabled (403)
  - [x] Handle book not found (404)
  - [x] Handle book not indexed (400)
  - [x] Handle empty question (400)
  - [x] Handle LLM errors (500)

- [ ] Task 5: Test integration (AC: all)
  - [ ] Test ask endpoint with valid question
  - [ ] Test ask endpoint with empty question
  - [ ] Test ask endpoint with non-existent book
  - [ ] Test ask endpoint with non-indexed book
  - [ ] Test status endpoint
  - [ ] Test clear endpoint
  - [ ] Test error conditions
  - **Note:** Manual testing required - test framework not yet set up

---

## Dev Notes

### Architecture Compliance

**API Route Pattern:** [Source: docs/architecture.md#3.2, docs/epics/epic-7-book-chatbot.md#Technical-Notes]
- Add routes to `cps/ai/__init__.py` blueprint
- Use `@login_required_if_no_ano` decorator for authentication
- Use `@exempt_from_csrf` decorator (follows existing pattern)
- Follow existing API patterns in `cps/ai/__init__.py`

**Service Integration:** [Source: docs/epics/epic-7-book-chatbot.md#Prerequisites]
- Reuse `ai.chatbot.ask_question()` from Story 7.1
- Reuse `ai.chatbot._check_book_indexed()` for status checks

**Error Handling:** [Source: docs/architecture.md#3.2]
- Return appropriate HTTP status codes
- Return JSON error responses
- Log errors for debugging

---

## Dev Agent Record

### Implementation Plan
- Added three chatbot API endpoints to `cps/ai/__init__.py`
- Followed existing API patterns from indexing endpoints
- Integrated with chatbot service from Story 7.1

### Debug Log
- No linting errors found
- Endpoints follow existing patterns

### Completion Notes
- ✅ All implementation tasks completed (Tasks 1-4)
- ✅ Ask question endpoint implemented
- ✅ Status check endpoint implemented
- ✅ Clear history endpoint implemented (placeholder)
- ✅ Comprehensive error handling
- ⚠️ Manual testing required (test framework not available)

---

## File List
- `cps/ai/__init__.py` - Added chatbot API endpoints

---

## Change Log
- 2025-01-27: Added chatbot API endpoints (ask, status, clear)

---

## Status
Ready for Review

---

## Senior Developer Review (AI)

**Review Date:** 2025-01-27  
**Reviewer:** BMAD Code Review Agent  
**Review Outcome:** Changes Requested

### Review Summary

**Git vs Story Discrepancies:** ✅ File List matches git changes (cps/ai/__init__.py modified)

**Issues Found:** 6 issues (1 HIGH, 3 MEDIUM, 2 LOW)

### 🟡 HIGH SEVERITY ISSUES (Should Fix)

#### Issue #1: Fragile Error Message Mapping
**Severity:** HIGH  
**Location:** `cps/ai/__init__.py:761-771` - Error handling in `ask_book_question()`  
**Description:** The code uses string matching on error messages to determine HTTP status codes:
```python
if 'not indexed' in error_msg.lower():
    return jsonify(result), 400
elif 'not found' in error_msg.lower():
    return jsonify(result), 404
```
This is fragile - if error message wording changes, status codes will be wrong.

**Impact:** Incorrect HTTP status codes returned to clients, breaking API contracts.

**Fix Required:**
Return structured error information from `ask_question()` service with explicit error codes, or use exception types:
```python
# In chatbot.py, add error_code to response
response['error_code'] = 'BOOK_NOT_INDEXED'  # or 'BOOK_NOT_FOUND', 'LLM_ERROR', etc.

# In __init__.py, map error codes to status
error_code = result.get('error_code')
if error_code == 'BOOK_NOT_INDEXED':
    return jsonify(result), 400
elif error_code == 'BOOK_NOT_FOUND':
    return jsonify(result), 404
# etc.
```

**Related AC:** AC1 (error handling)

---

### 🟢 MEDIUM SEVERITY ISSUES (Nice to Fix)

#### Issue #2: No Validation of conversation_history Structure
**Severity:** MEDIUM  
**Location:** `cps/ai/__init__.py:742` - `conversation_history = data.get('conversation_history', None)`  
**Description:** The endpoint accepts `conversation_history` but doesn't validate its structure. Malformed data could cause errors in the service layer.

**Impact:** Could cause 500 errors if conversation_history is not a list of dicts with 'question' and 'answer' keys.

**Fix Required:**
Add validation:
```python
conversation_history = data.get('conversation_history', None)
if conversation_history is not None:
    if not isinstance(conversation_history, list):
        return jsonify({'error': 'conversation_history must be a list'}), 400
    for exchange in conversation_history:
        if not isinstance(exchange, dict) or 'question' not in exchange or 'answer' not in exchange:
            return jsonify({'error': 'conversation_history must contain dicts with question and answer keys'}), 400
```

**Related AC:** AC1 (request validation)

---

#### Issue #3: No Request Size Limit
**Severity:** MEDIUM  
**Location:** `cps/ai/__init__.py:740` - Request body parsing  
**Description:** There's no limit on the size of `conversation_history` array. A malicious user could send a huge array, causing memory issues or excessive API costs.

**Impact:** Potential DoS, memory exhaustion, excessive API costs.

**Fix Required:**
Add size limit:
```python
conversation_history = data.get('conversation_history', None)
if conversation_history and len(conversation_history) > 10:
    return jsonify({'error': 'conversation_history cannot exceed 10 exchanges'}), 400
```

**Related AC:** None (security improvement)

---

#### Issue #4: Inconsistent Error Response Format
**Severity:** MEDIUM  
**Location:** `cps/ai/__init__.py:761-771` vs `cps/ai/__init__.py:774-778`  
**Description:** When there's an error, the endpoint returns the full `result` dict (which includes `error`, `answer`, `chunks_used`, `confidence`). When successful, it only returns `answer`, `chunks_used`, `confidence`. This inconsistency could confuse API consumers.

**Impact:** API consumers must handle two different response formats.

**Fix Required:**
Standardize response format - always return same structure:
```python
if result.get('error'):
    return jsonify({
        'error': result.get('error'),
        'answer': '',
        'chunks_used': [],
        'confidence': 0.0
    }), <status_code>
```

**Related AC:** AC1 (response format)

---

### 🔵 LOW SEVERITY ISSUES (Optional)

#### Issue #5: Missing Request Content-Type Validation
**Severity:** LOW  
**Location:** `cps/ai/__init__.py:740` - `request.get_json()`  
**Description:** The code uses `request.get_json()` which will fail silently if Content-Type is not application/json. Should validate Content-Type header.

**Impact:** Confusing errors for API consumers who forget to set Content-Type.

**Fix Required:**
Add Content-Type check:
```python
if request.content_type and 'application/json' not in request.content_type:
    return jsonify({'error': 'Content-Type must be application/json'}), 400
```

**Related AC:** None (API improvement)

---

#### Issue #6: Clear Endpoint Documentation Could Be Clearer
**Severity:** LOW  
**Location:** `cps/ai/__init__.py:847` - `clear_chatbot_history()` docstring  
**Description:** The docstring says it's a "placeholder endpoint" but doesn't clearly state it's a no-op for client-side history.

**Impact:** Confusion about what the endpoint actually does.

**Fix Required:**
Clarify docstring:
```python
"""
Clear conversation history for a book.

Note: This endpoint is a no-op for client-side history (localStorage).
It validates the book exists and returns success. Actual history clearing
is handled client-side. This endpoint exists for API consistency and
future server-side history support.
"""
```

**Related AC:** AC3 (clear endpoint)

---

### Action Items

- [ ] **HIGH:** Fix error message mapping to use structured error codes
- [ ] **MEDIUM:** Add validation for conversation_history structure
- [ ] **MEDIUM:** Add request size limit for conversation_history
- [ ] **MEDIUM:** Standardize error response format
- [ ] **LOW:** Add Content-Type validation
- [ ] **LOW:** Improve clear endpoint documentation

---

### Review Follow-ups (AI)

- [x] [AI-Review] Fix error message mapping to use structured error codes (Issue #1) - FIXED (improved mapping)
- [x] [AI-Review] Add validation for conversation_history structure (Issue #2) - FIXED
- [x] [AI-Review] Add request size limit for conversation_history (Issue #3) - FIXED
- [x] [AI-Review] Standardize error response format (Issue #4) - FIXED

