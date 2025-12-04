# Epic 1: Foundation Setup

**Epic Goal:** Establish the technical infrastructure (database, configuration, text extraction, background tasks) needed for all AI features.

**User Value Statement:** Establishes the technical infrastructure needed for all AI features, enabling users to configure and use AI capabilities.

**PRD Coverage:** FR4 (Configuration Management), FR5 (Background Job System) - foundational support for all features

**Technical Context:**
- Database schema: `book_summaries` and `book_embeddings` tables in `app_settings` schema (Architecture section 3.1)
- sqlite-vss extension: Virtual table for vector search (Architecture section 3.1)
- Configuration: Environment variables + SQL config pattern (Architecture section 3.5)
- Background tasks: APScheduler + WorkerThread integration (Architecture section 3.4)
- Text extraction: Format-specific extractors (Architecture section 3.3)

**UX Integration:** Configuration UI foundation (UX section 4)

**Dependencies:** None (foundation epic)

**Related Documents:**
- [Master Epic Index](../epics.md)
- [Architecture Document](../architecture.md)
- [UX Integration Guide](../ux-integration-guide.md)

---

## Story 1.1: Database Schema and Models

As a developer,
I want database tables and models for AI features,
So that summaries and embeddings can be stored and retrieved.

**Acceptance Criteria:**

**Given** the application is running
**When** I execute the database migration script `migrations/001_add_ai_tables.sql`
**Then** the following tables are created in the `app_settings` schema:

- `book_summaries` table with columns:
  - `id` (Integer, primary key)
  - `book_id` (Integer, nullable=False, indexed)
  - `summary_text` (String, nullable=False)
  - `model_name` (String, nullable=False)
  - `created_at` (DateTime, default=utcnow)
  - `updated_at` (DateTime, default=utcnow, onupdate=utcnow)
  - Index on `book_id` named `idx_book_summaries_book_id`

- `book_embeddings` table with columns:
  - `id` (Integer, primary key)
  - `book_id` (Integer, nullable=False, indexed)
  - `vector` (LargeBinary/BLOB, nullable=False) - stores binary float32 array
  - `vector_dimension` (Integer, nullable=False) - e.g., 1536 for text-embedding-3-small
  - `model_name` (String, nullable=False)
  - `created_at` (DateTime, default=utcnow)
  - `updated_at` (DateTime, default=utcnow, onupdate=utcnow)
  - Index on `book_id` named `idx_book_embeddings_book_id`

**And** SQLAlchemy models are added to `cps/ub.py`:
- `BookSummary` class extending `Base` (from `cps/ub.py`)
- `BookEmbedding` class extending `Base` (from `cps/ub.py`)
- Models follow existing patterns in `cps/ub.py` (see Architecture section 3.1)
- Models use `__table_args__ = {'schema': 'app_settings'}`

**And** the migration script is located at `migrations/001_add_ai_tables.sql`

**Technical Notes:**
- Use SQLAlchemy `LargeBinary` type for `vector` column (Architecture section 3.1)
- Store vectors as BLOB format: `np.array(embedding, dtype=np.float32).tobytes()` (Architecture section 3.1)
- Foreign key `book_id` references `calibre.books.id` (cross-database reference, no FK constraint) (Architecture section 3.1)
- Follow existing `ub.py` model patterns (Architecture section 4.1)

**Prerequisites:** None

---

## Story 1.2: sqlite-vss Extension Setup

As a developer,
I want sqlite-vss extension loaded and virtual table created,
So that vector similarity search can be performed efficiently.

**Acceptance Criteria:**

**Given** sqlite-vss extension is installed
**When** the application connects to the database
**Then** the sqlite-vss extension is loaded via `db.load_extension('vector0')` or equivalent

**And** a virtual table `book_embeddings_vss` is created via migration script `migrations/002_create_vss_table.sql`:
- Virtual table uses `vss0` module
- Table structure matches `book_embeddings` table for vector column
- Virtual table is linked to `book_embeddings.vector` column

**And** the virtual table can be queried using `vss_distance()` function for similarity search

**Technical Notes:**
- sqlite-vss extension must be available at runtime (Architecture section 3.1)
- Virtual table creation follows sqlite-vss documentation (Architecture section 3.1)
- Extension loading happens in database connection setup (Architecture section 3.1)
- Migration script located at `migrations/002_create_vss_table.sql` (Architecture section 7.1)

**Prerequisites:** Story 1.1 (Database Schema)

---

## Story 1.3: Configuration Management Infrastructure

As an administrator,
I want AI configuration options stored in the database,
So that AI features can be enabled/disabled and configured without code changes.

**Acceptance Criteria:**

**Given** I am an administrator
**When** I access the configuration system
**Then** the following configuration options are available in `cps/config_sql.py`:

- `config_ai_enabled` (Boolean, default=False) - Master toggle
- `config_ai_provider` (String, default="openai") - Provider identifier
- `config_ai_llm_model` (String, default="gpt-4o-mini") - LLM model name
- `config_ai_embedding_model` (String, default="text-embedding-3-small") - Embedding model name
- `config_ai_api_key` (String, default="") - API key (stored securely)
- `config_ai_max_tokens_summary` (Integer, default=500) - Max tokens for summaries
- `config_ai_timeout_seconds` (Integer, default=60) - Request timeout
- `config_ai_max_retries` (Integer, default=3) - Max retry attempts

**And** configuration follows existing `config_sql.py` patterns:
- Options stored in existing config database tables
- Accessible via `config.config_ai_*` attributes
- API keys stored securely (encrypted/hashed if possible) (Architecture section 3.5)

**And** validation rules are implemented:
- If `AI_ENABLED=false`, all other AI config options are ignored
- If `AI_ENABLED=true`, `AI_PROVIDER`, `AI_LANGCHAIN_LLM`, `AI_LANGCHAIN_EMBEDDINGS`, and `AI_API_KEY` must be provided
- Provider-specific validation for model names
- Value range validation for integers (Architecture section 3.5)

**Technical Notes:**
- Extend `cps/config_sql.py` following existing configuration patterns (Architecture section 3.5)
- Configuration stored in database (primary), environment variables (optional override for non-sensitive), defaults (fallback) (Architecture section 3.5)
- API keys stored securely in database, never in environment variables (Architecture section 3.5)

**Prerequisites:** None

---

## Story 1.4: Text Extraction Service

As a developer,
I want a text extraction service for books,
So that book content can be extracted for AI summary generation.

**Acceptance Criteria:**

**Given** a book with format EPUB, PDF, or TXT
**When** I call `ai.text_extraction.extract_text(book_id, max_tokens=2000)`
**Then** text is extracted according to format:

- **EPUB:** Extract text from HTML/XHTML chapters using `zipfile` + `lxml` (extend `cps/epub.py` patterns)
  - Extract first 20 pages OR first chapter, whichever is greater
  - Target ~2000 tokens (~1500 words) for summary input
  - Truncate if exceeds token limit

- **PDF:** Use `PyPDF` to extract text from first N pages
  - Extract first 20 pages
  - Target ~2000 tokens
  - Truncate if exceeds token limit

- **TXT:** Direct file read with encoding detection
  - Read first ~2000 tokens
  - Truncate if exceeds token limit

- **Other formats:** Return metadata-only string (title, author, description, tags)

**And** the function returns a string containing:
- Book metadata (title, author, description, tags) - always included
- Extracted text (if format supported) - up to token limit
- Empty string if extraction fails (with fallback to metadata-only)

**And** error handling:
- Graceful fallback to metadata-only if extraction fails
- Log errors for debugging
- No exceptions raised to calling code

**Technical Notes:**
- Create `cps/ai/text_extraction.py` (Architecture section 3.3)
- Use existing libraries: `lxml`, `zipfile` for EPUB; `PyPDF` for PDF (Architecture section 3.3)
- Follow existing `cps/epub.py` patterns for EPUB extraction (Architecture section 3.3)
- Text limits: ~2000 tokens (~1500 words) for summary input (Architecture section 3.3)

**Prerequisites:** None

---

## Story 1.5: Background Task Base Infrastructure

As a developer,
I want background task infrastructure integrated with existing task system,
So that AI operations can run asynchronously without blocking the web interface.

**Acceptance Criteria:**

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

**Technical Notes:**
- Follow existing `CalibreTask` pattern (see `cps/tasks/thumbnail.py` for example) (Architecture section 3.4)
- Use existing `BackgroundScheduler` (APScheduler) and `WorkerThread` (Architecture section 3.4)
- No need for Celery/RQ/Redis - use existing infrastructure (Architecture section 3.4)
- Tasks use `ub.get_new_session_instance()` for database access in background context (Architecture section 5.2)

**Prerequisites:** None

---

_Return to [Master Epic Index](../epics.md)_




