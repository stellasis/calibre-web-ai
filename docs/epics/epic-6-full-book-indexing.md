# Epic 6: Full Book Indexing (RAG Infrastructure)

**Epic Goal:** Enable full book content indexing using a chunked embedding architecture (RAG) to support conversational Q&A about books.

**User Value Statement:** Provides the infrastructure needed for users to ask questions about book content. Books are indexed into searchable chunks that power the book chatbot (Epic 7).

**PRD Coverage:** Infrastructure epic (enables Epic 7: Book Chatbot)

**Technical Context:**
- RAG (Retrieval-Augmented Generation) infrastructure for book content indexing
- Separate from summary-based semantic search (Epic 3) and similar books (Epic 4)
- Long-running background process for full book indexing
- Chunk-based embedding storage with book/chapter references
- Chunk search service used by Epic 7 chatbot, not exposed as standalone search feature

**Dependencies:** Epic 1 (Foundation), Epic 2 (AI Summary), Epic 3 (Semantic Search)

**Related Documents:**
- [Master Epic Index](../epics.md)
- [Epic 3: AI Semantic Search](epic-3-search.md)
- [Epic 4: Similar Books](epic-4-similar-books.md)
- [Architecture Document](../architecture.md)

---

## Epic Overview

### Why Full Book Indexing?

The existing semantic search (Epic 3) uses **summary-based embeddings**:
- ✅ Fast and efficient
- ✅ Good for "find similar books" or "cozy fantasy books" queries
- ❌ Cannot find specific passages or quotes
- ❌ Cannot answer questions about book content

**Full Book Indexing provides infrastructure for:**
- 💬 Book chatbot (Epic 7) - enables Q&A about book content
- 📖 Chunk-level content retrieval for RAG responses
- 🎯 Chapter/section-level context for accurate answers

**Note:** This epic provides the indexing infrastructure. The user-facing chatbot interface is implemented in Epic 7.

### Architecture: RAG (Retrieval-Augmented Generation)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FULL BOOK INDEXING FLOW                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Book File ──► Chunking ──► Embed Chunks ──► Store in DB       │
│    (EPUB)      (500 tok)    (per chunk)      (book_chunks)     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    USAGE BY EPIC 7 CHATBOT                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Question ──► Embed Query ──► Vector Search ──► Return Chunks │
│     (Epic 7)        (Epic 6)      (book_chunks)    (with context) │
│                                                                 │
│  ──► Send to LLM ──► Generate Answer                            │
│      (with chunks)   (RAG response - Epic 7)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Comparison: Summary Search vs Full Indexing

| Feature | Summary Search (Epic 3) | Full Indexing (Epic 6) |
|---------|------------------------|------------------------|
| **Granularity** | Book-level | Chunk/passage-level |
| **Storage** | 1 embedding per book | ~100-600 embeddings per book |
| **Use Case** | Find similar books | Infrastructure for chatbot (Epic 7) |
| **User-Facing** | Yes (search feature) | No (infrastructure only) |
| **Speed** | Very fast | Fast (optimized) |
| **Cost** | Low (~$0.0001/book) | Higher (~$0.01-0.05/book) |
| **Processing** | Quick (summary only) | Long (full book scan) |

---

## Story 6.1: Chunk Database Schema and Models

As a developer,
I want database tables to store book chunks and their embeddings,
So that full-book content can be indexed and searched.

**Acceptance Criteria:**

**Given** the AI features are being extended
**When** the database is initialized
**Then** the following tables exist in `app_settings` schema:

1. **book_chunks** table:
   - `id` (Integer, primary key)
   - `book_id` (Integer, indexed, references calibre.books.id)
   - `chunk_index` (Integer) - Position in book
   - `chapter_title` (String, nullable) - Chapter/section name if available
   - `chunk_text` (Text) - The actual text content
   - `token_count` (Integer) - Estimated tokens in chunk
   - `start_position` (Integer) - Character position in source
   - `end_position` (Integer) - Character position end
   - `created_at` (DateTime)

2. **book_chunk_embeddings** table:
   - `id` (Integer, primary key)
   - `chunk_id` (Integer, foreign key to book_chunks.id)
   - `book_id` (Integer, indexed) - Denormalized for fast queries
   - `vector` (BLOB) - Embedding vector
   - `vector_dimension` (Integer)
   - `model_name` (String)
   - `created_at` (DateTime)

3. **book_index_status** table:
   - `id` (Integer, primary key)
   - `book_id` (Integer, unique, indexed)
   - `status` (String) - 'pending', 'processing', 'completed', 'failed'
   - `total_chunks` (Integer)
   - `processed_chunks` (Integer)
   - `error_message` (Text, nullable)
   - `started_at` (DateTime, nullable)
   - `completed_at` (DateTime, nullable)
   - `created_at` (DateTime)
   - `updated_at` (DateTime)

4. **book_chunk_embeddings_vec** virtual table (sqlite-vec):
   - For fast vector similarity search across chunks

**Technical Notes:**
- Follow existing model patterns in `cps/ub.py`
- Use same BLOB format as `book_embeddings` for vectors
- Index on `book_id` for efficient per-book queries
- Consider composite index on `(book_id, chunk_index)`

**Prerequisites:** Story 1.1 (Database Schema), Story 1.2 (sqlite-vec)

---

## Story 6.2: Book Chunking Service

As a developer,
I want a service that splits books into semantic chunks,
So that each chunk can be independently embedded and searched.

**Acceptance Criteria:**

**Given** a book file (EPUB, PDF, TXT)
**When** I call `chunk_book(book_id)`
**Then** the service:

1. Extracts full text from the book (not limited to first 20 pages)
2. Splits text into semantic chunks:
   - Target size: ~500 tokens per chunk
   - Overlap: ~50 tokens between chunks (for context continuity)
   - Respect paragraph/sentence boundaries when possible
   - Preserve chapter/section markers if available
3. Stores each chunk in `book_chunks` table with:
   - `chunk_index` for ordering
   - `chapter_title` if detectable
   - `start_position` and `end_position` for source reference
   - `token_count` for the chunk
4. Updates `book_index_status` with `total_chunks` count
5. Returns list of chunk IDs

**And** chunking strategies:
- **EPUB:** Use chapter structure from spine, chunk within chapters
- **PDF:** Use page boundaries as hints, chunk by paragraphs
- **TXT:** Chunk by paragraph groups

**And** error handling:
- Large books: Process in batches, update progress
- Corrupted files: Mark status as 'failed' with error message
- Memory limits: Stream processing for very large books

**Technical Notes:**
- Create `cps/ai/chunking.py`
- Use text splitter with overlap (similar to LangChain RecursiveCharacterTextSplitter)
- Estimate tokens: ~4 characters per token
- Maximum ~10,000 chunks per book (safety limit)

**Prerequisites:** Story 1.4 (Text Extraction), Story 6.1 (Schema)

---

## Story 6.3: Chunk Embedding Service

As a developer,
I want a service that generates embeddings for book chunks,
So that chunks can be searched via vector similarity.

**Acceptance Criteria:**

**Given** chunks stored in `book_chunks` table
**When** I call `embed_chunks(book_id)`
**Then** the service:

1. Fetches all unembedded chunks for the book
2. Generates embeddings in batches (to manage API rate limits):
   - Batch size: 20-50 chunks per API call
   - Uses same embedding model as Epic 3 (configurable)
3. Stores each embedding in `book_chunk_embeddings` table
4. Syncs to `book_chunk_embeddings_vec` virtual table
5. Updates `book_index_status.processed_chunks` after each batch
6. Marks `book_index_status.status` as 'completed' when done

**And** progress tracking:
- Update `processed_chunks` count after each batch
- Allow resumption if interrupted (skip already-embedded chunks)
- Calculate and log estimated time remaining

**And** error handling:
- API errors: Retry with exponential backoff
- Rate limits: Pause and resume
- Partial failure: Mark status, allow retry

**Technical Notes:**
- Extend `cps/ai/embeddings.py` or create `cps/ai/chunk_embeddings.py`
- Use batch embedding API when available (more efficient)
- Consider async processing for large books

**Prerequisites:** Story 6.1 (Schema), Story 6.2 (Chunking)

---

## Story 6.4: Full Book Indexing Background Task

As a developer,
I want a background task that orchestrates full book indexing,
So that books can be indexed without blocking the UI.

**Acceptance Criteria:**

**Given** a book_id and indexing request
**When** the background task runs
**Then** it:

1. Creates/updates `book_index_status` record with status='processing'
2. Calls chunking service (Story 6.2)
3. Calls embedding service (Story 6.3)
4. Updates status to 'completed' on success or 'failed' on error
5. Logs progress at each major step

**And** task properties:
- Extends `CalibreTask` base class
- Shows progress in task status UI
- Can be cancelled (stops after current batch)
- Supports bulk indexing (multiple books queued)

**And** configuration options:
- `config_ai_full_index_enabled` - Master toggle
- `config_ai_max_chunks_per_book` - Safety limit (default: 5000)
- `config_ai_chunk_batch_size` - Embeddings per API call (default: 25)

**Technical Notes:**
- Create `cps/tasks/ai_full_index.py`
- Follow patterns from `cps/tasks/ai_summary.py`
- Use `WorkerThread.add()` for task scheduling
- Consider priority queue (smaller books first)

**Prerequisites:** Story 6.2 (Chunking), Story 6.3 (Embeddings), Story 1.5 (Background Tasks)

---

## Story 6.5: Chunk Search Service

As a developer,
I want a service that searches within indexed book chunks,
So that Epic 7 chatbot can retrieve relevant passages for answering questions.

**Acceptance Criteria:**

**Given** a search query and optional book_id filter
**When** I call `search_chunks(query, book_id=None, limit=20)`
**Then** the service:

1. Generates embedding for query text
2. Performs vector similarity search on `book_chunk_embeddings_vec`
3. Optionally filters by `book_id` (search within one book)
4. Returns ranked results with:
   - `chunk_id`, `book_id`, `chunk_index`
   - `chunk_text` (the passage content)
   - `chapter_title` (if available)
   - `similarity_score`
   - `book` object (title, author for context)

**And** search modes:
- **Book-scoped search:** Search within single book (primary use case for Epic 7)
- **Global search:** Search all indexed books (optional, for future use)

**Note:** This service is used by Epic 7 chatbot to retrieve relevant chunks. It is not exposed as a standalone user-facing search feature.

**Technical Notes:**
- Create `cps/ai/chunk_search.py`
- Reuse query embedding logic from `cps/ai/search.py`
- Support sqlite-vec MATCH operator with book_id filter
- Service is called by Epic 7 chatbot service

**Prerequisites:** Story 6.3 (Chunk Embeddings), Story 3.2 (Semantic Search patterns)

---

## Story 6.6: Full Indexing API Endpoints

As a developer,
I want API endpoints for triggering and monitoring full book indexing,
So that the UI can manage the indexing process.

**Acceptance Criteria:**

**AC1:** `POST /api/ai/index/<int:book_id>` - Start indexing
- Requires admin or book owner permission
- Returns `{'status': 'started', 'book_id': book_id}` or error
- If already indexed: Returns `{'status': 'already_indexed', ...}`
- If already processing: Returns `{'status': 'in_progress', ...}`

**AC2:** `GET /api/ai/index/<int:book_id>/status` - Get indexing status
- Returns current status from `book_index_status` table
- Includes progress percentage if processing

**AC3:** `DELETE /api/ai/index/<int:book_id>` - Remove book index
- Deletes all chunks and embeddings for book
- Resets status to allow re-indexing

**AC4:** `POST /api/ai/index/search` - Search indexed content (used by Epic 7)
- Request body: `{'query': 'search text', 'book_id': optional, 'limit': 20}`
- Returns chunk search results
- **Note:** This endpoint is used by Epic 7 chatbot, not exposed as standalone search

**AC5:** `GET /api/ai/index/stats` - Get indexing statistics
- Total books indexed
- Total chunks stored
- Storage usage estimate

**Technical Notes:**
- Add routes to `cps/web.py` or create `cps/ai_index.py` blueprint
- Use `@admin_required` for index/delete operations
- Use `@login_required_if_no_ano` for search/status

**Prerequisites:** Story 6.4 (Background Task), Story 6.5 (Search)

---

## Story 6.7: Full Indexing UI Integration

As a user,
I want UI controls to manage full book indexing,
So that I can index books for use with the book chatbot (Epic 7).

**Acceptance Criteria:**

**AC1:** Book detail page shows indexing status:
- Not indexed: "Index for Chatbot" or "Index for Q&A" button
- Processing: Progress bar with chunk count
- Indexed: "Indexed ✓" badge with chunk count, "Re-index" option
- Failed: Error message with "Retry" button
- Note: Indexing enables the chatbot feature (Epic 7) for this book

**AC2:** Admin page shows indexing dashboard (optional):
- Total indexed books count
- Bulk index controls (index all, index unindexed) - optional
- Storage usage estimate
- Queue status for pending indexing jobs

**Technical Notes:**
- Extend `detail.html` with indexing status section
- Extend `admin.html` with indexing dashboard (optional, for admin convenience)
- JavaScript for progress polling during indexing
- **Note:** Chunk search results are not displayed directly to users - they are used by Epic 7 chatbot

**Prerequisites:** Story 6.6 (API Endpoints)

---

## Configuration Options

New configuration options for Epic 6:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `config_ai_full_index_enabled` | Boolean | False | Master toggle for full indexing feature |
| `config_ai_chunk_size_tokens` | Integer | 500 | Target tokens per chunk |
| `config_ai_chunk_overlap_tokens` | Integer | 50 | Overlap between chunks |
| `config_ai_max_chunks_per_book` | Integer | 5000 | Safety limit per book |
| `config_ai_chunk_batch_size` | Integer | 25 | Embeddings per API call |
| `config_ai_auto_index_on_summary` | Boolean | False | Auto-index when summary generated |

---

## Technical Considerations

### Storage Estimates

| Book Size | Est. Chunks | Embedding Storage | Total per Book |
|-----------|-------------|-------------------|----------------|
| 50 pages | ~50 | 300 KB | ~350 KB |
| 200 pages | ~200 | 1.2 MB | ~1.5 MB |
| 500 pages | ~500 | 3 MB | ~4 MB |
| 1000 pages | ~1000 | 6 MB | ~8 MB |

For 1000 fully indexed books (avg 300 pages): ~2-3 GB storage

### API Cost Estimates

Using OpenAI `text-embedding-3-small` ($0.00002/1K tokens):
- Average book (200 chunks × 500 tokens): ~$0.002 per book
- 1000 books: ~$2.00 total

### Performance Considerations

1. **Indexing time:** ~2-5 minutes per book (depending on size and API speed)
2. **Search latency:** <500ms (sqlite-vec is fast)
3. **Memory:** Stream processing to avoid loading full book in memory
4. **Concurrency:** Queue-based processing, one book at a time default

---

## Implementation Sequence

**Recommended Story Order:**
1. Story 6.1 (Schema) - Foundation
2. Story 6.2 (Chunking) - Core logic
3. Story 6.3 (Chunk Embeddings) - Core logic
4. Story 6.4 (Background Task) - Orchestration
5. Story 6.5 (Search Service) - Query capability
6. Story 6.6 (API Endpoints) - Integration
7. Story 6.7 (UI Integration) - User-facing

**Parallel Work:**
- Stories 6.2 and 6.3 can be developed in parallel after 6.1
- Story 6.5 depends on 6.3
- Stories 6.6 and 6.7 are sequential

---

## Success Metrics

- [ ] Books can be fully indexed via background task
- [ ] Chunk search service returns relevant chunks (used by Epic 7)
- [ ] UI shows indexing progress and status on book detail page
- [ ] Indexed books can be used by Epic 7 chatbot
- [ ] Storage usage is reasonable (<10MB per book)
- [ ] Indexing completes in <5 minutes per book
- [ ] No impact on existing semantic search (Epic 3)
- [ ] Admin dashboard shows indexing statistics (optional)

---

_Return to [Master Epic Index](../epics.md)_


