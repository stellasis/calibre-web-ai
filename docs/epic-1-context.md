# Epic 1: Foundation Setup - Technical Context

**Epic:** Epic 1 - Foundation Setup  
**Created:** 2025-01-27  
**Status:** Ready for Story Drafting  
**Purpose:** Detailed technical implementation context for Epic 1 stories

---

## Epic Overview

**Epic Goal:** Establish the technical infrastructure (database, configuration, text extraction, background tasks) needed for all AI features.

**User Value:** Establishes the technical infrastructure needed for all AI features, enabling users to configure and use AI capabilities.

**PRD Coverage:** FR4 (Configuration Management), FR5 (Background Job System) - foundational support for all features

**Dependencies:** None (foundation epic)

---

## Technical Architecture Context

### Database Architecture

**Schema Location:** `app_settings` database (user DB), NOT `calibre` database
- `calibre` DB is read-only and managed by Calibre desktop
- `app_settings` DB is writable and already used for user data (Shelf, ReadBook, etc.)
- Follows existing pattern: user-specific data goes in `app_settings`
- Avoids conflicts with upstream Calibre updates

**Tables Required:**
1. `book_summaries` - Stores AI-generated summaries
2. `book_embeddings` - Stores vector embeddings (BLOB format)
3. `book_embeddings_vss` - Virtual table for sqlite-vss vector search

**Model Location:** Add to `cps/ub.py` following existing patterns
- Use SQLAlchemy declarative base: `Base = declarative_base()`
- Use `__table_args__ = {'schema': 'app_settings'}`
- Follow existing relationship patterns and indexes

**Vector Storage Format:**
- Column type: `BLOB` (SQLAlchemy `LargeBinary` type)
- Store as: Binary representation of float array (4 bytes per float)
- Serialization: `np.array(embedding, dtype=np.float32).tobytes()`
- Deserialization: `np.frombuffer(blob, dtype=np.float32)`
- Dimension: Store `vector_dimension` column (e.g., 1536 for text-embedding-3-small)

**Foreign Key Pattern:**
- `book_id` references `calibre.books.id` (cross-database reference)
- No FK constraint (cross-database references don't support constraints)
- Use application-level validation

### sqlite-vss Extension

**Extension Details:**
- Extension name: `vector0` (loadable extension for SQLite)
- Virtual table module: `vss0`
- Installation: Must be available at runtime (verify during Story 1.2)
- Loading: `db.load_extension('vector0')` or equivalent on database connection

**Virtual Table Setup:**
- Table name: `book_embeddings_vss`
- Structure: Matches `book_embeddings` table for vector column
- Linked to: `book_embeddings.vector` column
- Query function: `vss_distance()` for similarity search
- Query function: `vss_search()` for efficient nearest neighbor search

**Migration Script:**
- Location: `migrations/002_create_vss_table.sql`
- Creates virtual table using `vss0` module
- Links to `book_embeddings.vector` column

### Configuration Management

**Storage Pattern:**
- Primary: Admin UI configuration (stored in existing calibre-web config database)
- Optional: Environment variables for non-sensitive settings (can override database values)
- Fallback: Default values

**Configuration Options (from PRD Section 5.5):**
- `AI_ENABLED` (Boolean, default=False) - Master toggle
- `AI_PROVIDER` (String, default="openai") - Provider identifier
- `AI_LANGCHAIN_LLM` (String, default="gpt-4o-mini") - LLM model name
- `AI_LANGCHAIN_EMBEDDINGS` (String, default="text-embedding-3-small") - Embedding model name
- `AI_API_KEY` (String, default="") - API key (stored securely in database)
- `AI_MAX_TOKENS_SUMMARY` (Integer, default=500) - Max tokens for summaries
- `AI_TIMEOUT_SECONDS` (Integer, default=60) - Request timeout
- `AI_MAX_RETRIES` (Integer, default=3) - Max retry attempts

**Implementation Location:** Extend `cps/config_sql.py` following existing configuration patterns

**Access Pattern:**
- Accessible via `config.config_ai_*` attributes
- API keys stored securely (encrypted/hashed if possible)
- Never store API keys in environment variables (use database only)

**Validation Rules:**
1. **Dependency Validation:**
   - If `AI_ENABLED=false`, all other AI config options are ignored
   - If `AI_ENABLED=true`, `AI_PROVIDER`, `AI_LANGCHAIN_LLM`, `AI_LANGCHAIN_EMBEDDINGS`, and `AI_API_KEY` must be provided

2. **Provider-Specific Validation:**
   - `AI_PROVIDER` must match a supported LangChain provider
   - `AI_LANGCHAIN_LLM` must be a valid model for the selected provider
   - `AI_LANGCHAIN_EMBEDDINGS` must be a valid embedding model for the selected provider

3. **Value Range Validation:**
   - `AI_MAX_TOKENS_SUMMARY`: Must be between 100 and 2000
   - `AI_TIMEOUT_SECONDS`: Must be between 10 and 300
   - `AI_MAX_RETRIES`: Must be between 0 and 10

4. **API Key Validation:**
   - Format validation based on provider (e.g., OpenAI keys start with `sk-`)
   - Basic format check on save (full validation requires API test call)

### Text Extraction Service

**Service Location:** Create `cps/ai/text_extraction.py`

**Format Support:**
- **EPUB:** Extract text from HTML/XHTML chapters using `zipfile` + `lxml` (extend `cps/epub.py` patterns)
- **PDF:** Use `PyPDF` to extract text from first N pages
- **TXT:** Direct file read with encoding detection
- **Other formats:** Fall back to metadata-only

**Text Limits:**
- Target: ~2000 tokens (~1500 words) for summary input
- Extract first 20 pages OR first chapter, whichever is greater
- Truncate if exceeds token limit

**Function Signature:**
```python
def extract_text(book_id: int, max_tokens: int = 2000) -> str:
    """
    Extract text from book for AI processing.
    
    Returns:
        String containing: book metadata (title, author, description, tags) + 
        extracted text (if format supported) up to token limit
    """
```

**Error Handling:**
- Graceful fallback to metadata-only if extraction fails
- Log errors for debugging
- No exceptions raised to calling code (return empty string or metadata-only)

**Dependencies:**
- Existing libraries: `lxml`, `zipfile` for EPUB
- Existing library: `PyPDF` for PDF
- Follow existing `cps/epub.py` patterns for EPUB extraction

### Background Task Infrastructure

**Task System:** Integrate with existing APScheduler + WorkerThread system
- No need for Celery/RQ/Redis (reduces complexity)
- Follows existing patterns (`TaskGenerateCoverThumbnails`, etc.)

**Task Base Class:** Extend `CalibreTask` from `cps.services.worker`

**Required Methods:**
- `run(self, worker_thread)` - Main task execution
- `name` property - Human-readable task name (translatable via `N_()`)
- `is_cancellable` property - Whether task can be cancelled

**Task Initialization Pattern:**
```python
class TaskGenerateAISummary(CalibreTask):
    def __init__(self, book_id, task_message='Generating AI summary'):
        super(TaskGenerateAISummary, self).__init__(task_message)
        self.book_id = book_id
        self.log = logger.create()
```

**Task Execution Pattern:**
- Use `app.app_context()` for database access in background tasks
- Update `self.progress` (0.0 to 1.0) during execution
- Update `self.message` for status updates
- Call `self._handleSuccess()` or `self._handleError()` on completion

**Task Scheduling:**
- Immediate: `WorkerThread.add(user, task, hidden=False)`
- Scheduled: `BackgroundScheduler.schedule_task_immediately(task, user, name)`

**Task Status:**
- Integrated with existing task status UI
- Tasks visible in task status interface

**Database Access in Tasks:**
- Use `ub.get_new_session_instance()` for database access in background context
- Always use `app.app_context()` wrapper

**Example Reference:** See `cps/tasks/thumbnail.py` for existing task patterns

---

## Story-Specific Technical Context

### Story 1.1: Database Schema and Models

**Migration Script:**
- Location: `migrations/001_add_ai_tables.sql`
- Creates `book_summaries` and `book_embeddings` tables in `app_settings` schema

**Table: `book_summaries`**
- Columns: `id`, `book_id`, `summary_text`, `model_name`, `created_at`, `updated_at`
- Index: `idx_book_summaries_book_id` on `book_id`

**Table: `book_embeddings`**
- Columns: `id`, `book_id`, `vector` (BLOB), `vector_dimension`, `model_name`, `created_at`, `updated_at`
- Index: `idx_book_embeddings_book_id` on `book_id`

**Models in `cps/ub.py`:**
- `BookSummary` class extending `Base`
- `BookEmbedding` class extending `Base`
- Use `__table_args__ = {'schema': 'app_settings'}`
- Follow existing model patterns in `cps/ub.py`

**Key Implementation Details:**
- Use SQLAlchemy `LargeBinary` type for `vector` column
- Foreign key `book_id` references `calibre.books.id` (cross-database, no FK constraint)
- Timestamps use `timezone.utc` default

### Story 1.2: sqlite-vss Extension Setup

**Extension Loading:**
- Load extension on database connection: `db.load_extension('vector0')`
- Location: Database connection setup code
- Error handling: Log warning if extension not available, but don't crash

**Virtual Table Creation:**
- Migration script: `migrations/002_create_vss_table.sql`
- Virtual table name: `book_embeddings_vss`
- Uses `vss0` module
- Links to `book_embeddings.vector` column

**Verification:**
- Test that `vss_distance()` function is available
- Test that virtual table can be queried
- Verify extension version compatibility

**Installation Notes:**
- sqlite-vss extension must be available at runtime
- Installation method to be determined during implementation (pre-built binaries vs. compilation)
- Document installation process for deployment

### Story 1.3: Configuration Management Infrastructure

**File to Extend:** `cps/config_sql.py`

**Configuration Attributes:**
- `config_ai_enabled` (Boolean)
- `config_ai_provider` (String)
- `config_ai_llm_model` (String)
- `config_ai_embedding_model` (String)
- `config_ai_api_key` (String) - stored securely
- `config_ai_max_tokens_summary` (Integer)
- `config_ai_timeout_seconds` (Integer)
- `config_ai_max_retries` (Integer)

**Storage:**
- Store in existing config database tables
- Follow existing `config_sql.py` patterns
- API keys: Encrypted/hashed if possible

**Validation Implementation:**
- Dependency validation (AI_ENABLED cascade)
- Provider-specific validation (model names)
- Value range validation (integers)
- API key format validation

**Access Pattern:**
- Primary: `config.config_ai_*` attributes
- Optional: Environment variable override for non-sensitive settings
- Fallback: Default values

### Story 1.4: Text Extraction Service

**Service File:** `cps/ai/text_extraction.py`

**Function Implementation:**
```python
def extract_text(book_id: int, max_tokens: int = 2000) -> str:
    """
    Extract text from book for AI processing.
    
    Returns string containing:
    - Book metadata (title, author, description, tags) - always included
    - Extracted text (if format supported) - up to token limit
    """
```

**Format-Specific Extraction:**
- **EPUB:** Use `zipfile` + `lxml` to extract HTML/XHTML content
  - Extract first 20 pages OR first chapter, whichever is greater
  - Follow existing `cps/epub.py` patterns
- **PDF:** Use `PyPDF` to extract text from first N pages
  - Extract first 20 pages
- **TXT:** Direct file read with encoding detection
- **Other formats:** Return metadata-only string

**Text Processing:**
- Target: ~2000 tokens (~1500 words)
- Truncate if exceeds token limit
- Always include metadata even if text extraction fails

**Error Handling:**
- Graceful fallback to metadata-only if extraction fails
- Log errors for debugging
- Return empty string or metadata-only (don't raise exceptions)

### Story 1.5: Background Task Base Infrastructure

**Task Files:** Future tasks will be in `cps/tasks/ai_summary.py`, `cps/tasks/ai_embedding.py`

**Task Base Class:** `CalibreTask` from `cps.services.worker`

**Required Implementation:**
- Extend `CalibreTask` base class
- Implement `run(self, worker_thread)` method
- Use `app.app_context()` for database access
- Update `self.progress` (0.0 to 1.0) during execution
- Update `self.message` for status updates
- Call `self._handleSuccess()` or `self._handleError()` on completion
- Implement `name` property (translatable via `N_()`)
- Implement `is_cancellable` property

**Task Scheduling:**
- Immediate: `WorkerThread.add(user, task, hidden=False)`
- Scheduled: `BackgroundScheduler.schedule_task_immediately(task, user, name)`

**Database Access:**
- Use `ub.get_new_session_instance()` for database access
- Always wrap in `app.app_context()`

**Reference Implementation:** See `cps/tasks/thumbnail.py` for existing task patterns

---

## Codebase Integration Points

### Existing Patterns to Follow

**Database Models:**
- Location: `cps/ub.py`
- Pattern: SQLAlchemy declarative base with `Base = declarative_base()`
- Schema: Use `__table_args__ = {'schema': 'app_settings'}`
- Example: See existing models in `cps/ub.py`

**Configuration:**
- Location: `cps/config_sql.py`
- Pattern: Store in existing config database tables
- Access: Via `config.config_*` attributes
- Example: See existing configuration options

**Background Tasks:**
- Location: `cps/tasks/`
- Pattern: Extend `CalibreTask` from `cps.services.worker`
- Example: `cps/tasks/thumbnail.py`

**Text Extraction:**
- EPUB patterns: `cps/epub.py`
- Use existing `lxml`, `zipfile` libraries
- Use existing `PyPDF` library

**Service Layer:**
- Location: `cps/services/` or `cps/ai/`
- Pattern: Business logic separated from routes
- Example: `cps/services/Metadata.py`

### Files to Create/Modify

**New Files:**
- `migrations/001_add_ai_tables.sql` - Database migration
- `migrations/002_create_vss_table.sql` - Virtual table migration
- `cps/ai/text_extraction.py` - Text extraction service

**Files to Extend:**
- `cps/ub.py` - Add `BookSummary` and `BookEmbedding` models
- `cps/config_sql.py` - Add AI configuration options

**Files to Reference:**
- `cps/tasks/thumbnail.py` - Background task patterns
- `cps/epub.py` - EPUB extraction patterns
- `cps/services/worker.py` - `CalibreTask` base class

---

## Dependencies and Prerequisites

### External Dependencies

**Required:**
- LangChain (for LLM/embedding orchestration) - version to be verified
- sqlite-vss extension - version and installation method to be determined
- NumPy (for vector operations) - may already be in dependencies

**Existing Dependencies (Already Available):**
- `lxml` - for EPUB text extraction
- `zipfile` - for EPUB file handling
- `PyPDF` - for PDF text extraction
- SQLAlchemy - for database models
- APScheduler - for background task scheduling
- Flask - for web framework

### Internal Dependencies

**Story Dependencies:**
- Story 1.2 depends on Story 1.1 (sqlite-vss needs database schema)
- Stories 1.3, 1.4, 1.5 are independent (can be done in parallel)
- All stories in Epic 1 are prerequisites for Epic 2

**System Dependencies:**
- Existing APScheduler + WorkerThread system must be running
- Database connection must support extension loading
- Existing config system must be functional

---

## Testing Considerations

### Database Schema Testing
- Verify tables created in `app_settings` schema
- Verify indexes created correctly
- Verify foreign key references (application-level)
- Test BLOB storage and retrieval

### sqlite-vss Testing
- Verify extension loads successfully
- Verify virtual table created correctly
- Test `vss_distance()` function
- Test `vss_search()` function
- Verify vector storage and retrieval

### Configuration Testing
- Verify all configuration options accessible
- Test validation rules
- Test API key storage security
- Test environment variable override
- Test default values

### Text Extraction Testing
- Test EPUB extraction (first 20 pages or first chapter)
- Test PDF extraction (first 20 pages)
- Test TXT extraction
- Test metadata-only fallback
- Test token limit truncation
- Test error handling

### Background Task Testing
- Verify task extends `CalibreTask` correctly
- Test task scheduling (immediate and scheduled)
- Test task status updates
- Test database access in background context
- Test error handling

---

## Implementation Notes

### Critical Implementation Details

1. **Database Schema:**
   - Must use `app_settings` schema, NOT `calibre` schema
   - BLOB format for vectors is required for sqlite-vss
   - Cross-database references don't support FK constraints

2. **sqlite-vss Extension:**
   - Extension must be available at runtime
   - Installation method needs to be determined
   - Virtual table must be created after regular table

3. **Configuration:**
   - API keys must be stored securely in database
   - Never store API keys in environment variables
   - Validation must enforce dependency rules

4. **Text Extraction:**
   - Must handle multiple formats gracefully
   - Must always include metadata even if extraction fails
   - Token limits must be enforced

5. **Background Tasks:**
   - Must use existing APScheduler + WorkerThread system
   - Must use `app.app_context()` for database access
   - Must follow existing task patterns

### Common Pitfalls to Avoid

1. **Don't modify `calibre` database** - Use `app_settings` schema only
2. **Don't use JSON for vectors** - Use BLOB format for sqlite-vss
3. **Don't add Celery/RQ** - Use existing APScheduler + WorkerThread
4. **Don't store API keys in environment** - Use database storage
5. **Don't raise exceptions in text extraction** - Return metadata-only on failure

---

## Next Steps After Epic 1

**Epic 1 Enables:**
- Epic 2: AI Summary Feature (needs database, configuration, text extraction, background tasks)
- Epic 3: AI Semantic Search (needs database, sqlite-vss, configuration)
- Epic 4: Similar Books (needs database, sqlite-vss, embeddings)
- Epic 5: Configuration UI (needs configuration infrastructure)

**Recommended Story Sequence:**
1. Story 1.1 (Database Schema) - Foundation for all features
2. Story 1.2 (sqlite-vss) - Required for search and similar books
3. Story 1.3 (Configuration) - Required for all AI features
4. Story 1.4 (Text Extraction) - Required for summary generation
5. Story 1.5 (Background Tasks) - Required for async operations

**Parallel Work:**
- Stories 1.3, 1.4, 1.5 can be done in parallel after 1.1 and 1.2

---

_This technical context document provides comprehensive implementation guidance for Epic 1. Use this document when drafting and implementing Epic 1 stories._




