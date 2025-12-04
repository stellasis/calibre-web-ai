# Epic 4: Similar Books Recommendations

**Epic Goal:** Enable users to discover similar books on the book detail page.

**User Value Statement:** Users can discover similar books on the detail page, helping them find related content to explore.

**PRD Coverage:** FR3 (Similar Books Recommendations)

**Technical Context:**
- Service layer: Reuses `cps/ai/search.py` with `similar_to()` method (Architecture section 4.3)
- Vector search: sqlite-vss nearest neighbors query (Architecture section 3.1)
- API endpoint: `/api/ai/similar/<int:book_id>` (Architecture section 3.2)
- Conditional display: Hide when no embeddings available (Architecture section 4.3)

**UX Integration:**
- Placement: Bottom of detail page after comments section (UX section 3.1)
- UI components: Same grid layout as search results (`row display-flex`, `col-sm-3 col-lg-2 col-xs-6`) (UX section 3.2)
- Info message: Show when no embeddings available (UX section 3.2)
- Limit: Maximum 8 books (PRD section 4.3)

**Dependencies:** Epic 1 (Foundation Setup), Epic 2 (AI Summary Feature - for embeddings), Epic 3 (AI Semantic Search - reuses search infrastructure)

**Related Documents:**
- [Master Epic Index](../epics.md)
- [Epic 1: Foundation Setup](epic-1-foundation.md)
- [Epic 2: AI Summary Feature](epic-2-summary.md)
- [Epic 3: AI Semantic Search](epic-3-search.md)
- [Architecture Document](../architecture.md)
- [UX Integration Guide](../ux-integration-guide.md)

---

## Story 4.1: Similar Books API Endpoint

As a developer,
I want an API endpoint to fetch similar books,
So that the UI can display similar books on the detail page.

**Acceptance Criteria:**

**Given** a book with embedding
**When** I call GET `/api/ai/similar/<int:book_id>`
**Then** the endpoint:

1. Checks `config.config_ai_enabled` - returns 403 if disabled
2. Validates `book_id` exists in calibre database
3. Fetches book embedding from `book_embeddings` table
4. If no embedding: Returns `{'similar_books': [], 'message': 'No embedding available. Generate a summary first.'}`
5. If embedding exists: Calls `ai.search.similar_to(book_id, limit=8)`:
   - Uses sqlite-vss nearest neighbors query
   - Excludes current book from results
   - Returns top 8 most similar books
6. Returns JSON response:
   ```json
   {
     "similar_books": [
       {
         "book_id": 123,
         "similarity_score": 0.95,
         "book": { /* book object with title, author, cover, etc. */ }
       },
       ...
     ]
   }
   ```

**And** route implementation:
- File: Extend `cps/web.py` or `cps/ai.py` blueprint
- Route: `@ai.route("/api/ai/similar/<int:book_id>", methods=['GET'])`
- Decorator: `@login_required_if_no_ano`
- Function: `get_similar_books(book_id)`

**And** error handling:
- AI disabled: Return `{'error': 'AI features disabled'}, 403`
- Book not found: Return `{'error': 'Book not found'}, 404`
- Unauthorized: Return `{'error': 'Unauthorized'}, 401`
- Server error: Return `{'error': 'Failed to fetch similar books'}, 500`

**Technical Notes:**
- Extend existing blueprint or use `cps/ai.py` blueprint (Architecture section 3.2)
- Reuse `ai.search.similar_to()` method (Architecture section 4.3)
- Use sqlite-vss nearest neighbors query (Architecture section 3.1)
- Limit to 8 books maximum (PRD section 4.3)

**Prerequisites:** Story 3.1 (Embedding Generation), Story 3.2 (Semantic Search)

---

## Story 4.2: Similar Books UI Integration

As a user,
I want to see similar books on the book detail page,
So that I can discover related content easily.

**Acceptance Criteria:**

**Given** I am viewing a book detail page
**When** `config.config_ai_enabled` is true
**Then** I see a "Similar Books" section:

- **Placement:** Bottom of detail page, after comments section, before footer
- **Heading:** "Similar Books" with `glyphicon-book` icon
- **Layout:** Same grid layout as search results:
  - Container: `row display-flex`
  - Items: `col-sm-3 col-lg-2 col-xs-6 book`
  - Maximum 8 books displayed

- **Book Cards:** (if similar books available)
  - Cover: `image.book_cover(similar_book)` macro
  - Title: `similar_book.title|shortentitle`
  - Author: `similar_book.authors` (formatted)
  - Link: `url_for('web.show_book', book_id=similar_book.id)`

- **Info Message:** (if no similar books available)
  - Alert: `alert alert-info`
  - Icon: `glyphicon-info-sign`
  - Message: "Similar books will appear here after an AI summary is generated for this book."

**And** template integration:
- File: `cps/templates/detail.html`
- Placement: After comments section, before footer
- Conditional: `{% if config.config_ai_enabled %}`
- Pass `similar_books` variable from route handler:
  - Query `/api/ai/similar/<book_id>` or call `ai.search.similar_to()` directly
  - Pass empty list if no embedding available

**And** conditional display:
- If `similar_books` is empty and no embedding: Show info message
- If `similar_books` is empty but embedding exists: Show empty state (no message)
- If `similar_books` has items: Show grid of books

**Technical Notes:**
- Follow UX Design section 3.1-3.2 exactly (UX Integration Guide)
- Use same grid layout as search results (UX section 3.2)
- Use Bootstrap classes: `row display-flex`, `col-sm-3 col-lg-2 col-xs-6 book` (UX section 3.2)
- Use `image.book_cover()` macro for covers (UX section 3.2)
- Limit to 8 books maximum (PRD section 4.3)

**Prerequisites:** Story 4.1 (Similar Books API)

---

_Return to [Master Epic Index](../epics.md)_




