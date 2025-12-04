# Epic 2: AI Summary Feature

**Epic Goal:** Enable users to generate and view AI-powered summaries of books.

**User Value Statement:** Users can generate and view AI-powered summaries of books to quickly understand what they're about.

**PRD Coverage:** FR1 (AI Summary Generation)

**Technical Context:**
- Service layer: `cps/ai/summarization.py` and `cps/ai/text_extraction.py` (Architecture section 4.1)
- Database: `book_summaries` table (Architecture section 3.1)
- Background tasks: `TaskGenerateAISummary` (Architecture section 3.4)
- API endpoint: `/api/ai/summary/<int:book_id>` (Architecture section 3.2)
- LangChain integration: LLM calls for summarization (Architecture section 4.1)

**UX Integration:**
- Button placement: After book metadata section in `detail.html` (UX section 1.1)
- UI components: Bootstrap `btn btn-primary`, `panel panel-default` (UX section 1.2)
- JavaScript: `cps/static/js/ai/summary.js` for async generation (UX section 1.3)
- Loading states: Spinner with `glyphicon-refresh glyphicon-spin` (UX section 1.2)

**Dependencies:** Epic 1 (Foundation Setup)

**Related Documents:**
- [Master Epic Index](../epics.md)
- [Epic 1: Foundation Setup](epic-1-foundation.md)
- [Architecture Document](../architecture.md)
- [UX Integration Guide](../ux-integration-guide.md)

---

## Story 2.1: AI Summarization Service

As a developer,
I want an AI summarization service that generates book summaries,
So that summaries can be created and stored for books.

**Acceptance Criteria:**

**Given** a book with extracted text (from Story 1.4)
**When** I call `ai.summarization.generate_summary(book_id)`
**Then** the service:

1. Checks `config.config_ai_enabled` - returns error if disabled
2. Fetches book metadata and extracted text (via `ai.text_extraction.extract_text()`)
3. Constructs prompt for LLM:
   - Includes book metadata (title, author, description)
   - Includes extracted text (up to token limit)
   - Prompt focuses on: what the book is about, who it's for, key themes/topics
4. Calls LangChain LLM with configured provider/model:
   - Uses `config.config_ai_provider` to select provider
   - Uses `config.config_ai_llm_model` for model selection
   - Uses `config.config_ai_api_key` for authentication
   - Uses `config.config_ai_max_tokens_summary` for output limit
   - Uses `config.config_ai_timeout_seconds` for timeout
   - Uses `config.config_ai_max_retries` for retry logic
5. Generates concise summary (3-7 sentences or bullet points)
6. Stores summary in `book_summaries` table:
   - `book_id` = provided book_id
   - `summary_text` = generated summary
   - `model_name` = LLM model used
   - `created_at` / `updated_at` = current timestamp
7. Returns summary text

**And** error handling:
- Timeout errors: Log and return error message
- API key errors: Log and return error message
- Provider errors: Log and return error message
- Missing book: Return error message
- Graceful degradation: Return error without crashing

**Technical Notes:**
- Create `cps/ai/summarization.py` (Architecture section 4.1)
- Use LangChain for LLM orchestration (Architecture section 4.1)
- Follow existing service patterns (see `cps/services/Metadata.py`) (Architecture section 4.1)
- Store summaries in `app_settings.book_summaries` table (Architecture section 3.1)
- Check `AI_ENABLED` before any AI operations (Architecture section 5.1)

**Prerequisites:** Story 1.3 (Configuration), Story 1.4 (Text Extraction), Story 1.1 (Database Schema)

---

## Story 2.2: Background Task for Summary Generation

As a user,
I want summary generation to run in the background,
So that the web interface remains responsive during generation.

**Acceptance Criteria:**

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

**Technical Notes:**
- Follow existing task patterns (see `cps/tasks/thumbnail.py`) (Architecture section 3.4)
- Use `app.app_context()` in `run()` method (Architecture section 5.2)
- Task status integrated with existing task status UI (Architecture section 3.4)

**Prerequisites:** Story 1.5 (Background Tasks), Story 2.1 (Summarization Service)

---

## Story 2.3: API Endpoint for Summary Generation

As a user,
I want an API endpoint to trigger summary generation,
So that the UI can request summaries asynchronously.

**Acceptance Criteria:**

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

**Technical Notes:**
- Extend existing blueprint or create new `cps/ai.py` blueprint (Architecture section 3.2)
- Register blueprint in `cps/main.py` via `app.register_blueprint(ai)` (Architecture section 3.2)
- Use existing error handling patterns: `jsonify()` for API errors (Architecture section 5.3)
- Check `AI_ENABLED` before any AI operations (Architecture section 5.1)

**Prerequisites:** Story 2.2 (Background Task)

---

## Story 2.4: UI Integration for Summary Generation

As a user,
I want a button and display area for AI summaries on the book detail page,
So that I can generate and view summaries easily.

**Acceptance Criteria:**

**Given** I am viewing a book detail page
**When** `config.config_ai_enabled` is true
**Then** I see an AI Summary section:

- **Button:** "Generate AI Summary" with `glyphicon-text-width` icon
  - Class: `btn btn-primary`
  - Placement: After book metadata section, before comments section
  - Data attribute: `data-book-id="{{ entry.id }}"`
  - ID: `generate-ai-summary`

- **Refresh Button:** (if summary exists) with `glyphicon-refresh` icon
  - Class: `btn btn-default`
  - ID: `refresh-ai-summary`

- **Summary Display:** (if summary exists)
  - Panel: `panel panel-default`
  - Heading: "AI Summary" with `glyphicon-info-sign` icon
  - Body: Summary text from `ai_summary.summary_text`
  - Footer: "Generated on [date]" from `ai_summary.created_at`

- **Loading State:** (during generation)
  - Spinner: `glyphicon-refresh glyphicon-spin`
  - Message: "Generating summary..."

- **Error State:** (on failure)
  - Alert: `alert alert-danger`
  - Icon: `glyphicon-exclamation-sign`
  - Message: Error message from API

**And** JavaScript functionality (`cps/static/js/ai/summary.js`):
- Button click → POST to `/api/ai/summary/<book_id>`
- Show loading state (hide existing content, show spinner)
- On success: Reload page or update DOM with new summary
- On error: Show error message
- Refresh button: Same as generate (triggers regeneration)

**And** template integration:
- File: `cps/templates/detail.html`
- Placement: After `<div class="col-sm-9 col-lg-9 book-meta">`, before comments section
- Conditional: `{% if config.config_ai_enabled %}`
- Pass `ai_summary` variable from route handler (query `book_summaries` table)

**Technical Notes:**
- Follow UX Design section 1.1-1.3 exactly (UX Integration Guide)
- Use Bootstrap classes: `btn btn-primary`, `panel panel-default` (UX section 1.2)
- Use Glyphicons: `glyphicon-text-width`, `glyphicon-refresh`, `glyphicon-info-sign` (UX section 1.2)
- JavaScript in `cps/static/js/ai/summary.js` (UX section 1.3)
- Include script in template via `{% block header %}` or base template (UX section 9.2)

**Prerequisites:** Story 2.3 (API Endpoint)

---

_Return to [Master Epic Index](../epics.md)_




