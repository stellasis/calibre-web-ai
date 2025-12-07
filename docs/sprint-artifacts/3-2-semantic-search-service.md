# Story 3.2: Semantic Search Service

**Status:** ready-for-dev  
**Epic:** Epic 3 - AI Semantic Search  
**Story ID:** 3.2  
**Created:** 2025-12-04  
**Prerequisites:** Story 3.1 (Embedding Generation)

---

## Story

As a developer,  
I want a semantic search service,  
So that users can search for books using natural language queries.

---

## Acceptance Criteria

**Given** a user query string  
**When** I call `ai.search.semantic_search(query, limit=20)`  
**Then** the service:

1. Checks `config.config_ai_enabled` - returns empty list if disabled
2. Generates query embedding:
   - Calls LangChain embedding model with query text
   - Uses same configuration as Story 3.1 (provider, model, API key)
3. Performs vector similarity search:
   - Uses sqlite-vec `MATCH` operator (not `vss_distance()`)
   - Queries `book_embeddings_vec` virtual table
   - Finds nearest neighbors to query embedding
   - Excludes books without embeddings
4. Returns ranked results:
   - List of books sorted by similarity score (highest first)
   - Limit to `limit` results (default 20)
   - Each result includes: `book_id`, `similarity_score`, `book` object

**And** fallback behavior:
- If no embeddings available: Return empty list
- If sqlite-vec not available: Log warning, return empty list
- If query embedding generation fails: Return empty list

**And** error handling:
- Timeout errors: Log and return empty list
- API key errors: Log and return empty list
- Provider errors: Log and return empty list
- Database errors: Log and return empty list
- Graceful degradation: Return empty list without crashing

---

## Tasks / Subtasks

- [ ] Task 1: Create search service module (AC: #1-4)
  - [ ] Create `cps/ai/search.py` file
  - [ ] Import required dependencies (LangChain, NumPy, SQLAlchemy)
  - [ ] Set up logging
  - [ ] Create `semantic_search(query, limit=20)` function signature

- [ ] Task 2: Implement AI enabled check (AC: #1)
  - [ ] Check `config.config_ai_enabled` - return empty list if disabled
  - [ ] Log warning if AI disabled

- [ ] Task 3: Implement query embedding generation (AC: #2)
  - [ ] Reuse embedding model initialization from `cps/ai/embeddings.py`
  - [ ] Call LangChain embedding model with query text
  - [ ] Use same configuration as Story 3.1 (provider, model, API key, timeout, retries)
  - [ ] Return embedding vector as numpy array
  - [ ] Handle errors: Return None on failure

- [ ] Task 4: Implement vector similarity search (AC: #3)
  - [ ] Query `book_embeddings_vec` virtual table using sqlite-vec
  - [ ] Use `MATCH` operator with query embedding
  - [ ] Order by `distance` (ascending = most similar)
  - [ ] Limit to `limit` results (default 20)
  - [ ] Exclude books without embeddings
  - [ ] SQL query pattern:
    ```sql
    SELECT book_id, distance
    FROM app_settings.book_embeddings_vec
    WHERE embedding MATCH :query_vector
    ORDER BY distance
    LIMIT :limit;
    ```

- [ ] Task 5: Implement result processing (AC: #4)
  - [ ] Convert `distance` to `similarity_score` (1.0 - distance, or normalize)
  - [ ] Fetch full book objects from `calibre.books` table
  - [ ] Return list of dicts: `{'book_id': int, 'similarity_score': float, 'book': Book}`
  - [ ] Sort by similarity score (highest first)

- [ ] Task 6: Implement fallback behavior (AC: fallback behavior)
  - [ ] If no embeddings available: Return empty list
  - [ ] If sqlite-vec not available: Log warning, return empty list
  - [ ] If query embedding fails: Return empty list

- [ ] Task 7: Implement error handling (AC: error handling)
  - [ ] Timeout errors: Log and return empty list
  - [ ] API key errors: Log and return empty list
  - [ ] Provider errors: Log and return empty list
  - [ ] Database errors: Log and return empty list
  - [ ] Graceful degradation: Return empty list without crashing

- [ ] Task 8: Testing
  - [ ] Test query embedding generation
  - [ ] Test vector similarity search with sqlite-vec
  - [ ] Test result ranking (most similar first)
  - [ ] Test limit parameter
  - [ ] Test fallback behavior (no embeddings, extension unavailable)
  - [ ] Test error handling

---

## Dev Notes

### Architecture Compliance

**Service Location:** [Source: docs/epic-3-context.md#Semantic-Search-Service, docs/epics/epic-3-search.md#Story-3.2]
- Create `cps/ai/search.py` (Architecture section 4.2)
- Follow existing service patterns (see `cps/ai/summarization.py` for LangChain integration patterns)

**Vector Similarity Search:** [Source: docs/epic-3-context.md#Vector-Similarity-Query, migrations/002_create_vec_table.sql]
- Use sqlite-vec `MATCH` operator (not `vss_distance()` function)
- Query `book_embeddings_vec` virtual table
- Virtual table: `app_settings.book_embeddings_vec USING vec0(book_id INTEGER PRIMARY KEY, embedding FLOAT[1536])`
- **CRITICAL:** Use sqlite-vec (`vec0` module, `MATCH` operator), NOT sqlite-vss (`vss0` module, `vss_distance()`)

**Query Pattern:** [Source: docs/epic-3-context.md#Query-Pattern]
```sql
SELECT book_id, distance
FROM app_settings.book_embeddings_vec
WHERE embedding MATCH :query_vector
ORDER BY distance
LIMIT :limit;
```

**Query Embedding Generation:** [Source: docs/epic-3-context.md#Query-Embedding-Generation]
- Use same LangChain embedding model as Story 3.1
- Same configuration (provider, model, API key, timeout, retries)
- Generate embedding for query text
- Reuse embedding model initialization from `cps/ai/embeddings.py`

**Result Processing:** [Source: docs/epic-3-context.md#Result-Processing]
- Convert `distance` to `similarity_score` (1.0 - distance, or normalize)
- Fetch full book objects from `calibre.books` table
- Return list of dicts: `{'book_id': int, 'similarity_score': float, 'book': Book}`
- Similarity score: Normalize to 0.0-1.0 (1.0 = most similar)

**Result Format:** [Source: docs/epic-3-context.md#Result-Format]
- Match existing search result format for UI compatibility
- Each result should include full book object (title, author, cover, etc.)
- Similarity score should be normalized (0.0 to 1.0, where 1.0 is most similar)

**Fallback Behavior:** [Source: docs/epic-3-context.md#Fallback-Behavior, docs/epics/epic-3-search.md#Story-3.2]
- If no embeddings available: Return empty list
- If sqlite-vec not available: Log warning, return empty list
- If query embedding generation fails: Return empty list

**Error Handling:** [Source: docs/epic-3-context.md#Error-Handling, docs/epics/epic-3-search.md#Story-3.2]
- Timeout errors: Log and return empty list
- API key errors: Log and return empty list
- Provider errors: Log and return empty list
- Database errors: Log and return empty list
- Graceful degradation: Return empty list without crashing

### Codebase Integration Points

**Service Patterns:** [Source: cps/ai/summarization.py]
- Follow service structure from `cps/ai/summarization.py`
- Use logger: `log = logger.create()`
- Import from parent: `from .. import config, logger, ub`
- Handle LangChain availability: Check `LANGCHAIN_AVAILABLE` flag

**Embedding Model Reuse:** [Source: cps/ai/embeddings.py (to be created)]
- Reuse embedding model initialization from `cps/ai/embeddings.py`
- Import `_get_embedding_model()` or similar helper function
- Use same configuration as embedding generation

**Database Access:** [Source: cps/db.py, cps/ub.py]
- Use SQLAlchemy session for database operations
- Query `book_embeddings_vec` virtual table
- Fetch book objects from `calibre.books` table
- Follow existing database access patterns

**Book Object Retrieval:** [Source: cps/db.py]
- Use `calibre_db.get_book_by_id()` or similar function
- Return full book objects with all metadata (title, author, cover, etc.)
- Match format expected by search results template

### Project Structure Notes

**File Organization:**
- New file: `cps/ai/search.py`
- Follows existing `cps/ai/` module structure
- Matches pattern from `cps/ai/summarization.py` and `cps/ai/embeddings.py`

**Naming Conventions:** [Source: docs/architecture.md#Naming-Patterns]
- Function: `semantic_search` (snake_case)
- Module: `search.py` (snake_case)
- Follows existing codebase patterns

### References

- [Source: docs/epic-3-context.md] - Epic 3 technical context
- [Source: docs/epics/epic-3-search.md#Story-3.2] - Story requirements
- [Source: docs/architecture.md#3.1] - Vector search architecture
- [Source: docs/architecture.md#4.2] - Service layer patterns
- [Source: migrations/002_create_vec_table.sql] - Virtual table structure
- [Source: docs/epic-1-context.md#sqlite-vec-Extension] - Extension details
- [Source: cps/ai/embeddings.py] - Embedding generation service (Story 3.1)

### Critical Implementation Details

1. **sqlite-vec vs sqlite-vss:** [Source: docs/epic-3-context.md#Critical-Implementation-Details]
   - Codebase uses **sqlite-vec** (not sqlite-vss)
   - Use `vec0` module (not `vss0`)
   - Use `MATCH` operator (not `vss_distance()`)
   - Virtual table: `book_embeddings_vec` (not `book_embeddings_vss`)

2. **Query Embedding:** [Source: docs/epic-3-context.md#Query-Embedding-Generation]
   - Use same LangChain embedding model as Story 3.1
   - Same configuration (provider, model, API key, timeout, retries)
   - Reuse embedding model initialization from `cps/ai/embeddings.py`

3. **Vector Similarity Query:** [Source: docs/epic-3-context.md#Vector-Similarity-Query]
   - Use `MATCH` operator with query embedding
   - Order by `distance` (ascending = most similar)
   - Limit to `limit` results (default 20)

4. **Result Format:** [Source: docs/epic-3-context.md#Result-Format]
   - Match existing search result format for UI compatibility
   - Include full book objects (title, author, cover, etc.)
   - Similarity score: Normalize to 0.0-1.0 (1.0 = most similar)

### Common Pitfalls to Avoid

1. **Don't use sqlite-vss syntax** - Use sqlite-vec (`vec0`, `MATCH` operator)
2. **Don't forget to fetch book objects** - Results need full book data for UI
3. **Don't skip similarity score normalization** - Should be 0.0-1.0 range
4. **Don't forget error handling** - Graceful degradation when AI unavailable
5. **Don't break existing search** - This is additive, not replacement

---

## Dev Agent Record

### Context Reference

- Epic 3 Technical Context: `docs/epic-3-context.md`
- Epic 3 Story Details: `docs/epics/epic-3-search.md`
- Story 3.1: `docs/sprint-artifacts/3-1-embedding-generation-service.md`

### Agent Model Used

TBD

### Debug Log References

TBD

### Completion Notes List

TBD

### File List

TBD



