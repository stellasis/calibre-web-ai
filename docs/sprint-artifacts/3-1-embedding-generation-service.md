# Story 3.1: Embedding Generation Service

**Status:** ready-for-dev  
**Epic:** Epic 3 - AI Semantic Search  
**Story ID:** 3.1  
**Created:** 2025-12-04  
**Prerequisites:** Story 1.1 (Database Schema), Story 1.2 (sqlite-vec Extension), Story 1.3 (Configuration), Story 2.1 (Summarization - for summaries)

---

## Story

As a developer,  
I want an embedding generation service,  
So that books can be converted to vectors for semantic search.

---

## Acceptance Criteria

**Given** a book with summary (or metadata fallback)  
**When** I call `ai.embeddings.generate_embedding(book_id)`  
**Then** the service:

1. Checks `config.config_ai_enabled` - returns error if disabled
2. Fetches book summary from `book_summaries` table (if exists)
3. If no summary, builds metadata string:
   - Concatenates: `title`, `author`, `description`, `tags`
   - Uses this as fallback text for embedding
4. Calls LangChain embedding model:
   - Uses `config.config_ai_provider` to select provider
   - Uses `config.config_ai_embedding_model` for model selection
   - Uses `config.config_ai_api_key` for authentication
   - Uses `config.config_ai_timeout_seconds` for timeout
   - Uses `config.config_ai_max_retries` for retry logic
5. Generates embedding vector (e.g., 1536 dimensions for text-embedding-3-small)
6. Stores embedding in `book_embeddings` table:
   - `book_id` = provided book_id
   - `vector` = BLOB (binary float32 array): `np.array(embedding, dtype=np.float32).tobytes()`
   - `vector_dimension` = dimension of vector (e.g., 1536)
   - `model_name` = embedding model used
   - `created_at` / `updated_at` = current timestamp
7. Syncs to `book_embeddings_vec` virtual table (sqlite-vec)
8. Returns embedding vector

**And** error handling:
- Timeout errors: Log and return None
- API key errors: Log and return None
- Provider errors: Log and return None
- Missing book: Return None
- Graceful degradation: Return None without crashing

---

## Tasks / Subtasks

- [ ] Task 1: Create embeddings service module (AC: #1-8)
  - [ ] Create `cps/ai/embeddings.py` file
  - [ ] Import required dependencies (LangChain, NumPy, SQLAlchemy)
  - [ ] Set up logging
  - [ ] Create `generate_embedding(book_id)` function signature

- [ ] Task 2: Implement AI enabled check and book validation (AC: #1)
  - [ ] Check `config.config_ai_enabled` - return None if disabled
  - [ ] Validate book_id exists in database
  - [ ] Return None with error log if book not found

- [ ] Task 3: Implement embedding source selection (AC: #2-3)
  - [ ] Query `book_summaries` table for book summary
  - [ ] If summary exists, use summary text as embedding source
  - [ ] If no summary, build metadata string:
    - Fetch book from `calibre.books` table
    - Concatenate: `title`, `author`, `description`, `tags`
    - Use metadata string as fallback

- [ ] Task 4: Implement LangChain embedding model integration (AC: #4-5)
  - [ ] Create `_get_embedding_model()` helper function
  - [ ] Support providers: OpenAI, Anthropic, Ollama, OpenRouter
  - [ ] Use `config.config_ai_provider` for provider selection
  - [ ] Use `config.config_ai_embedding_model` for model selection
  - [ ] Use `config.config_ai_api_key` for authentication
  - [ ] Use `config.config_ai_timeout_seconds` for timeout
  - [ ] Use `config.config_ai_max_retries` for retry logic
  - [ ] Call embedding model with text (summary or metadata)
  - [ ] Return embedding vector as numpy array

- [ ] Task 5: Implement database storage (AC: #6)
  - [ ] Use `BookEmbedding` model from `cps/ub.py`
  - [ ] Serialize vector: `np.array(embedding, dtype=np.float32).tobytes()`
  - [ ] Store `vector_dimension` (e.g., 1536)
  - [ ] Store `model_name` for tracking
  - [ ] Set `created_at` / `updated_at` timestamps
  - [ ] Handle upsert (update if exists, insert if new)

- [ ] Task 6: Implement virtual table sync (AC: #7)
  - [ ] After storing in `book_embeddings`, sync to `book_embeddings_vec` virtual table
  - [ ] Use `INSERT` or `UPDATE` on virtual table
  - [ ] Virtual table structure: `book_id INTEGER PRIMARY KEY, embedding FLOAT[1536]`
  - [ ] Use sqlite-vec `vec0` module (not `vss0`)

- [ ] Task 7: Implement error handling (AC: error handling)
  - [ ] Timeout errors: Log and return None
  - [ ] API key errors: Log and return None
  - [ ] Provider errors: Log and return None
  - [ ] Missing book: Return None
  - [ ] Database errors: Log and return None
  - [ ] Graceful degradation: Return None without crashing

- [ ] Task 8: Testing
  - [ ] Test embedding generation for books with summaries
  - [ ] Test embedding generation for books without summaries (metadata fallback)
  - [ ] Test error handling (timeout, API key errors, provider errors)
  - [ ] Test vector storage and retrieval
  - [ ] Test virtual table sync

---

## Dev Notes

### Architecture Compliance

**Service Location:** [Source: docs/epic-3-context.md#Embedding-Generation-Service, docs/epics/epic-3-search.md#Story-3.1]
- Create `cps/ai/embeddings.py` (Architecture section 4.2)
- Follow existing service patterns (see `cps/ai/summarization.py` for LangChain integration patterns)

**LangChain Integration:** [Source: docs/epic-3-context.md#LangChain-Integration, cps/ai/summarization.py]
- Use LangChain's embedding model abstraction
- Provider selection via `config.config_ai_provider`
- Model selection via `config.config_ai_embedding_model`
- API key via `config.config_ai_api_key`
- Timeout and retry logic from config
- Follow pattern from `cps/ai/summarization.py` `_get_llm()` function for provider support

**Embedding Source Priority:** [Source: docs/epic-3-context.md#Embedding-Source-Priority, docs/prd.md#5.2]
1. **Primary:** AI summary from `book_summaries` table (if exists)
2. **Fallback:** Metadata string (title + author + description + tags)

**Vector Storage:** [Source: docs/epic-3-context.md#Vector-Storage, docs/architecture.md#3.1]
- **Table:** `book_embeddings` in `app_settings` schema (already exists from Epic 1)
- **Format:** BLOB (binary float32 array)
- **Serialization:** `np.array(embedding, dtype=np.float32).tobytes()`
- **Deserialization:** `np.frombuffer(blob, dtype=np.float32)`
- **Columns:** Use `BookEmbedding` model from `cps/ub.py` (lines 588-601)
  - `book_id` (Integer, indexed)
  - `vector` (BLOB, binary float32 array)
  - `vector_dimension` (Integer, e.g., 1536)
  - `model_name` (String)
  - `created_at` / `updated_at` (DateTime)

**Virtual Table Sync:** [Source: docs/epic-3-context.md#Virtual-Table-Sync, migrations/002_create_vec_table.sql]
- After storing in `book_embeddings`, sync to `book_embeddings_vec` virtual table
- Virtual table: `app_settings.book_embeddings_vec USING vec0(book_id INTEGER PRIMARY KEY, embedding FLOAT[1536])`
- Use `INSERT` or `UPDATE` on virtual table
- Virtual table automatically indexes for similarity search
- **CRITICAL:** Use sqlite-vec (`vec0` module), NOT sqlite-vss (`vss0` module)

**Error Handling:** [Source: docs/epic-3-context.md#Error-Handling, docs/epics/epic-3-search.md#Story-3.1]
- Timeout errors: Log and return None
- API key errors: Log and return None
- Provider errors: Log and return None
- Missing book: Return None
- Graceful degradation: Return None without crashing
- Follow error handling patterns from `cps/ai/summarization.py`

### Codebase Integration Points

**Database Models:** [Source: cps/ub.py lines 588-601]
- `BookEmbedding` model already exists in `cps/ub.py`
- Use SQLAlchemy session for database operations
- Follow existing model patterns

**Configuration Access:** [Source: cps/config_sql.py, docs/sprint-artifacts/1-3-configuration-management-infrastructure.md]
- Access via `config.config_ai_*` attributes
- API keys stored securely in database (automatically decrypted)
- Follow configuration access patterns from `cps/ai/summarization.py`

**LangChain Provider Support:** [Source: cps/ai/summarization.py lines 29-100]
- Support providers: OpenAI, Anthropic, Ollama, OpenRouter
- Follow `_get_llm()` pattern for embedding model initialization
- Use `langchain_openai`, `langchain_anthropic`, `langchain_community` packages
- For embeddings, use `OpenAIEmbeddings`, `AnthropicEmbeddings`, etc.

**Service Patterns:** [Source: cps/ai/summarization.py]
- Follow service structure from `cps/ai/summarization.py`
- Use logger: `log = logger.create()`
- Import from parent: `from .. import config, logger, ub`
- Handle LangChain availability: Check `LANGCHAIN_AVAILABLE` flag

### Project Structure Notes

**File Organization:**
- New file: `cps/ai/embeddings.py`
- Follows existing `cps/ai/` module structure
- Matches pattern from `cps/ai/summarization.py` and `cps/ai/text_extraction.py`

**Naming Conventions:** [Source: docs/architecture.md#Naming-Patterns]
- Function: `generate_embedding` (snake_case)
- Module: `embeddings.py` (snake_case)
- Follows existing codebase patterns

### References

- [Source: docs/epic-3-context.md] - Epic 3 technical context
- [Source: docs/epics/epic-3-search.md#Story-3.1] - Story requirements
- [Source: docs/architecture.md#3.1] - Vector storage format
- [Source: docs/architecture.md#4.2] - Service layer patterns
- [Source: cps/ai/summarization.py] - LangChain integration patterns
- [Source: cps/ub.py lines 588-601] - BookEmbedding model
- [Source: migrations/002_create_vec_table.sql] - Virtual table structure
- [Source: docs/epic-1-context.md#sqlite-vec-Extension] - Extension details

### Critical Implementation Details

1. **sqlite-vec vs sqlite-vss:** [Source: docs/epic-3-context.md#Critical-Implementation-Details]
   - Codebase uses **sqlite-vec** (not sqlite-vss)
   - Use `vec0` module (not `vss0`)
   - Virtual table: `book_embeddings_vec` (not `book_embeddings_vss`)
   - Migration already exists: `migrations/002_create_vec_table.sql`

2. **Embedding Source Priority:** [Source: docs/epic-3-context.md#Embedding-Source-Priority]
   - Primary: AI summary (if exists)
   - Fallback: Metadata string (title + author + description + tags)
   - Always include metadata even if summary exists (for better context)

3. **Vector Storage:** [Source: docs/epic-3-context.md#Vector-Storage]
   - Store as BLOB (binary float32 array)
   - Serialization: `np.array(embedding, dtype=np.float32).tobytes()`
   - Dimension: 1536 (for text-embedding-3-small)

4. **Virtual Table Sync:** [Source: docs/epic-3-context.md#Virtual-Table-Sync]
   - After storing in `book_embeddings`, sync to `book_embeddings_vec`
   - Use `INSERT` or `UPDATE` on virtual table
   - Virtual table automatically indexes for efficient similarity search

### Common Pitfalls to Avoid

1. **Don't use sqlite-vss syntax** - Use sqlite-vec (`vec0`, `MATCH` operator)
2. **Don't forget virtual table sync** - Embeddings must be synced to virtual table
3. **Don't skip metadata fallback** - Always have fallback when summary unavailable
4. **Don't forget error handling** - Graceful degradation when AI unavailable
5. **Don't use wrong vector format** - Must be BLOB (binary float32), not JSON

---

## Dev Agent Record

### Context Reference

- Epic 3 Technical Context: `docs/epic-3-context.md`
- Epic 3 Story Details: `docs/epics/epic-3-search.md`

### Agent Model Used

TBD

### Debug Log References

TBD

### Completion Notes List

TBD

### File List

TBD



