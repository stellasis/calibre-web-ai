# Epic 3: AI Semantic Search

**Epic Goal:** Enable users to search for books using natural language queries with semantic similarity.

**User Value Statement:** Users can search for books using natural language queries and get results ranked by semantic similarity.

**PRD Coverage:** FR2 (AI Semantic Search)

**Technical Context:**
- Service layer: `cps/ai/search.py` and `cps/ai/embeddings.py` (Architecture section 4.2)
- Vector search: sqlite-vss virtual table with `vss_distance()` (Architecture section 3.1)
- Route integration: Extended search route with `?ai=1` parameter (Architecture section 3.2)
- Embedding generation: Uses summaries as primary source, metadata as fallback (Architecture section 4.2)
- LangChain integration: Embedding model calls (Architecture section 4.2)

**UX Integration:**
- Toggle placement: Near search input in `search.html` (UX section 2.1)
- UI components: `btn-group` with radio buttons or `nav-tabs` (UX section 2.2)
- JavaScript: `cps/static/js/ai/search.js` for mode switching (UX section 2.3)
- Results display: Same layout as standard search (UX section 2.3)

**Dependencies:** Epic 1 (Foundation Setup), Epic 2 (AI Summary Feature - for embeddings)

**Related Documents:**
- [Master Epic Index](../epics.md)
- [Epic 1: Foundation Setup](epic-1-foundation.md)
- [Epic 2: AI Summary Feature](epic-2-summary.md)
- [Architecture Document](../architecture.md)
- [UX Integration Guide](../ux-integration-guide.md)

---

## Story 3.1: Embedding Generation Service

As a developer,
I want an embedding generation service,
So that books can be converted to vectors for semantic search.

**Acceptance Criteria:**

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
7. Syncs to `book_embeddings_vss` virtual table (if sqlite-vss is configured)
8. Returns embedding vector

**And** error handling:
- Timeout errors: Log and return error message
- API key errors: Log and return error message
- Provider errors: Log and return error message
- Missing book: Return error message
- Graceful degradation: Return error without crashing

**Technical Notes:**
- Create `cps/ai/embeddings.py` (Architecture section 4.2)
- Use LangChain for embedding orchestration (Architecture section 4.2)
- Store vectors as BLOB format (Architecture section 3.1)
- Primary source: AI summary; Fallback: metadata string (Architecture section 4.2)
- Sync to sqlite-vss virtual table after storage (Architecture section 3.1)

**Prerequisites:** Story 1.1 (Database Schema), Story 1.2 (sqlite-vss), Story 1.3 (Configuration), Story 2.1 (Summarization - for summaries)

---

## Story 3.2: Semantic Search Service

As a developer,
I want a semantic search service,
So that users can search for books using natural language queries.

**Acceptance Criteria:**

**Given** a user query string
**When** I call `ai.search.semantic_search(query, limit=20)`
**Then** the service:

1. Checks `config.config_ai_enabled` - returns error if disabled
2. Generates query embedding:
   - Calls LangChain embedding model with query text
   - Uses same configuration as Story 3.1 (provider, model, API key)
3. Performs vector similarity search:
   - Uses sqlite-vss `vss_distance()` function
   - Queries `book_embeddings_vss` virtual table
   - Finds nearest neighbors to query embedding
   - Excludes books without embeddings
4. Returns ranked results:
   - List of books sorted by similarity score (highest first)
   - Limit to `limit` results (default 20)
   - Each result includes: `book_id`, `similarity_score`, `book` object

**And** fallback behavior:
- If no embeddings available: Return empty list or suggest generating summaries first
- If sqlite-vss not available: Log warning, return empty list

**And** error handling:
- Timeout errors: Log and return empty list
- API key errors: Log and return empty list
- Provider errors: Log and return empty list
- Database errors: Log and return empty list
- Graceful degradation: Return empty list without crashing

**Technical Notes:**
- Create `cps/ai/search.py` (Architecture section 4.2)
- Use sqlite-vss `vss_distance()` for similarity search (Architecture section 3.1)
- Query `book_embeddings_vss` virtual table (Architecture section 3.1)
- Use LangChain for query embedding generation (Architecture section 4.2)
- Return results in same format as standard search for UI compatibility (Architecture section 4.2)

**Prerequisites:** Story 3.1 (Embedding Generation)

---

## Story 3.3: Search Route Integration and UI

As a user,
I want to toggle between standard and AI search on the search page,
So that I can use semantic search when needed.

**Acceptance Criteria:**

**Given** I am on the search page
**When** `config.config_ai_enabled` is true
**Then** I see a search mode toggle:

- **Toggle Options:**
  - "Standard Search" (default, active)
  - "AI Search" (with "Beta" badge)
  - Implemented as `btn-group` with radio buttons OR `nav-tabs`
  - Icons: `glyphicon-search` for standard, `glyphicon-brain` (or `glyphicon-cog`) for AI

**And** when I select "AI Search" and submit a query:
- URL includes `?ai=1` parameter
- Route handler checks `?ai=1` parameter
- If `ai=1`: Calls `ai.search.semantic_search(query)` (from Story 3.2)
- If not: Uses existing standard search
- Results displayed in same layout as standard search

**And** route implementation:
- File: Extend `cps/web.py` or `cps/search.py`
- Route: Existing search route with `?ai=1` parameter handling
- Function: Check `request.args.get('ai') == '1'` to determine search mode
- Pass `ai_search=True` to template when AI mode active

**And** template integration:
- File: `cps/templates/search.html`
- Placement: Near search input, as toggle button group or tabs
- Conditional: `{% if config.config_ai_enabled %}`
- JavaScript: `cps/static/js/ai/search.js` for mode switching (updates URL with `?ai=1`)

**And** JavaScript functionality:
- Mode toggle updates URL with `?ai=1` parameter
- Page reloads with AI search results
- Results use same display format as standard search

**Technical Notes:**
- Follow UX Design section 2.1-2.3 exactly (UX Integration Guide)
- Use Bootstrap `btn-group` with radio buttons OR `nav-tabs` (UX section 2.2)
- Use Glyphicons: `glyphicon-search`, `glyphicon-brain` (UX section 2.2)
- JavaScript in `cps/static/js/ai/search.js` (UX section 2.3)
- Results display: Same layout as standard search (UX section 2.3)

**Prerequisites:** Story 3.2 (Semantic Search Service)

---

_Return to [Master Epic Index](../epics.md)_




