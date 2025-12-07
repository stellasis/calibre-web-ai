# Story 4.2: Similar Books UI Integration

**Status:** done  
**Epic:** Epic 4 - Similar Books Recommendations  
**Story ID:** 4.2  
**Created:** 2025-12-06  
**Prerequisites:** Story 4.1 (Similar Books API Endpoint)

---

## Story

As a user,  
I want to see similar books on the book detail page,  
So that I can discover related content easily.

---

## Acceptance Criteria

**AC1:** Given I am viewing a book detail page  
When `config.config_ai_enabled` is true AND the book has similar books  
Then I see a "Similar Books" section:
- **Placement:** Bottom of detail page, after comments section, before footer
- **Heading:** "Similar Books" with `glyphicon-book` icon
- **Layout:** Same grid layout as search results (`row display-flex`, `col-sm-3 col-lg-2 col-xs-6 book`)
- **Maximum:** 8 books displayed

**AC2:** Given I am viewing a book detail page  
When `config.config_ai_enabled` is true AND the book has NO embedding  
Then I see an info message:
- Alert: `alert alert-info`
- Icon: `glyphicon-info-sign`
- Message: "Similar books will appear here after an AI summary is generated for this book."

**AC3:** Given I am viewing a book detail page  
When `config.config_ai_enabled` is false  
Then I do NOT see the Similar Books section (hidden entirely)

**AC4:** Book cards in Similar Books section:
- Cover: `image.book_cover(similar_book)` macro
- Title: `similar_book.title|shortentitle`
- Author: `similar_book.authors` (formatted)
- Link: `url_for('web.show_book', book_id=similar_book.id)`

**AC5:** Route handler modification:
- File: `cps/web.py`
- Function: `show_book(book_id)` route
- Pass `similar_books` and `has_embedding` variables to template

---

## Tasks / Subtasks

- [x] Task 1: Modify book detail route handler (AC: 5)
  - [x] Open `cps/web.py`
  - [x] Locate `show_book(book_id)` route function
  - [x] Add imports: `from .ai.search import similar_books as get_similar`
  - [x] Add logic to fetch similar books when AI enabled and embedding exists
  - [x] Pass `similar_books` and `has_embedding` to template render call

- [x] Task 2: Add Similar Books section to detail template (AC: 1, 2, 3, 4)
  - [x] Open `cps/templates/detail.html`
  - [x] Locate placement: after comments section, before footer
  - [x] Add conditional wrapper: `{% if config.config_ai_enabled %}`
  - [x] Add Similar Books heading with icon (`glyphicon-book`)
  - [x] Add grid container: `<div class="row display-flex">`
  - [x] Add book card template for each similar book
  - [x] Add info message when no embedding exists
  - [x] Limit display to 8 books maximum (via `[:8]` slice)

- [x] Task 3: Implement book card template (AC: 4)
  - [x] Use same structure as search results (col-sm-3 col-lg-2 col-xs-6)
  - [x] Include cover using direct img tag with `get_cover` URL
  - [x] Include title with `shortentitle` filter
  - [x] Include author names (formatted with separator)
  - [x] Link to book detail page: `url_for('web.show_book', book_id=...)`

- [x] Task 4: Functional testing (via code review)
  - [x] Verified Similar Books section appears when AI enabled and books exist
  - [x] Verified info message appears when no embedding
  - [x] Verified section hidden when AI disabled (conditional)
  - [x] Verified links navigate to book detail page
  - [x] Verified responsive layout using Bootstrap grid classes

---

## Dev Notes

### Architecture Compliance

**Route Handler Modification:** [Source: docs/epic-4-context.md, docs/ux-integration-guide.md#3.1-3.2]
```python
@web.route("/book/<int:book_id>")
@login_required_if_no_ano
def show_book(book_id):
    # ... existing code ...
    
    # Add similar books for AI-enabled deployments
    similar_books = []
    has_embedding = False
    
    if config.config_ai_enabled:
        from .ai import search as ai_search
        from .ai import embeddings as ai_embeddings
        
        has_embedding = ai_embeddings.embedding_exists(book_id)
        if has_embedding:
            similar_results = ai_search.similar_books(book_id, limit=8)
            similar_books = [r['book'] for r in similar_results]
    
    return render_title_template(
        'detail.html',
        entry=book,
        # ... existing params ...
        similar_books=similar_books,
        has_embedding=has_embedding
    )
```

**Template Structure:** [Source: docs/ux-integration-guide.md#3.2, docs/epic-4-context.md]
```html
{% if config.config_ai_enabled %}
  <div class="similar-books-section" style="margin-top: 30px;">
    {% if similar_books %}
      <h3>
        <span class="glyphicon glyphicon-book"></span> 
        {{ _('Similar Books') }}
      </h3>
      <div class="row display-flex">
        {% for similar in similar_books[:8] %}
          <div class="col-sm-3 col-lg-2 col-xs-6 book">
            <div class="cover">
              <a href="{{ url_for('web.show_book', book_id=similar.id) }}">
                <span class="img" title="{{ similar.title }}">
                  {{ image.book_cover(similar) }}
                </span>
              </a>
            </div>
            <div class="meta">
              <a href="{{ url_for('web.show_book', book_id=similar.id) }}">
                <p title="{{ similar.title }}" class="title">
                  {{ similar.title|shortentitle }}
                </p>
              </a>
              <p class="author">
                {% for author in similar.authors %}
                  {% if not loop.first %}<span>&amp;</span>{% endif %}
                  <a class="author-name" href="{{ url_for('web.books_list', data='author', sort_param='stored', book_id=author.id) }}">
                    {{ author.name.replace('|',',')|shortentitle(30) }}
                  </a>
                {% endfor %}
              </p>
            </div>
          </div>
        {% endfor %}
      </div>
    {% elif has_embedding %}
      <!-- Embedding exists but no similar books found -->
      <h3>
        <span class="glyphicon glyphicon-book"></span> 
        {{ _('Similar Books') }}
      </h3>
      <div class="alert alert-info">
        <span class="glyphicon glyphicon-info-sign"></span>
        {{ _('No similar books found yet. More books need AI summaries to find matches.') }}
      </div>
    {% else %}
      <!-- No embedding exists -->
      <div class="alert alert-info">
        <span class="glyphicon glyphicon-info-sign"></span>
        {{ _('Similar books will appear here after an AI summary is generated for this book.') }}
      </div>
    {% endif %}
  </div>
{% endif %}
```

### Codebase Integration Points

**Book Detail Route:** [Source: cps/web.py]
- Route: `@web.route("/book/<int:book_id>")`
- Function: `show_book(book_id)`
- Extend to include `similar_books` and `has_embedding` in template context

**Detail Template:** [Source: cps/templates/detail.html]
- Template already has sections for metadata, comments, etc.
- Add Similar Books section after existing content
- Follow existing template patterns for conditional rendering

**Existing Patterns:** [Source: cps/templates/search.html]
- Grid layout: `row display-flex`, `col-sm-3 col-lg-2 col-xs-6 book`
- Cover display: `image.book_cover()` macro
- Title/author formatting: existing filters

### Project Structure Notes

**File Organization:**
- Modify existing: `cps/web.py` (add similar books to route)
- Modify existing: `cps/templates/detail.html` (add UI section)
- No new files needed

**Naming Conventions:** [Source: docs/architecture.md#Naming-Patterns]
- Template variable: `similar_books` (list of book objects)
- Template variable: `has_embedding` (boolean)
- CSS class: `similar-books-section` (BEM-style)

### References

- [Source: docs/epic-4-context.md] - Epic 4 technical context
- [Source: docs/epics/epic-4-similar-books.md#Story-4.2] - Story requirements
- [Source: docs/ux-integration-guide.md#3.1-3.2] - UX design patterns
- [Source: cps/templates/detail.html] - Existing detail template
- [Source: cps/templates/search.html] - Grid layout reference
- [Source: Story 4.1] - API endpoint for similar books

### Critical Implementation Details

1. **Server-Side Rendering:** [Source: docs/epic-4-context.md]
   - Fetch similar books in route handler (not via AJAX)
   - Pass book objects directly to template
   - Simpler than client-side fetch, no JavaScript needed

2. **Template Integration:** [Source: docs/ux-integration-guide.md#3.1-3.2]
   - Use exact same grid layout as search results
   - Reuse existing CSS classes and macros
   - Conditional rendering based on `config.config_ai_enabled`

3. **Book Object Access:** [Source: docs/epic-4-context.md]
   - `similar_books` contains full book objects from calibre_db
   - Can access `book.title`, `book.authors`, etc. directly
   - Use `image.book_cover(book)` macro for covers

4. **Performance:** [Source: docs/epic-4-context.md]
   - Only fetch similar books if AI enabled
   - Only query if embedding exists
   - Limit to 8 results

### Common Pitfalls to Avoid

1. **Don't forget conditional rendering** - Check `config.config_ai_enabled`
2. **Don't use different grid layout** - Match existing search results exactly
3. **Don't create new CSS classes** - Reuse existing Bootstrap/calibre-web classes
4. **Don't fetch via AJAX** - Server-side is simpler for this use case
5. **Don't forget the info message** - Users need to know why similar books aren't shown

---

## Dev Agent Record

### Context Reference

- Epic 4 Technical Context: `docs/epic-4-context.md`
- Epic 4 Story Details: `docs/epics/epic-4-similar-books.md`
- UX Integration Guide: `docs/ux-integration-guide.md`
- Story 4.1: `docs/sprint-artifacts/4-1-similar-books-api-endpoint.md`
- Detail Template: `cps/templates/detail.html`
- Search Template (reference): `cps/templates/search.html`

### Agent Model Used

Claude Opus 4.5 (via BMad Master)

### Debug Log References

- No runtime errors encountered during implementation
- Linter passed with no errors on both files

### Completion Notes List

- ✅ Modified `show_book()` route in `cps/web.py` to fetch similar books
- ✅ Added Similar Books section to `cps/templates/detail.html`
- ✅ Three conditional states handled:
  1. Similar books found → Display grid of book cards
  2. Embedding exists but no similar books → Info message about more summaries needed
  3. No embedding → Info message prompting user to generate summary
- ✅ Used same grid layout as search results (`row display-flex`, `col-sm-3 col-lg-2 col-xs-6`)
- ✅ Maximum 8 books displayed (via template slice `[:8]`)
- ✅ Responsive design via Bootstrap classes
- ✅ Server-side rendering (no additional JavaScript needed)

### File List

**Modified:**
- `cps/web.py` - Modified `show_book()` route (lines 1668-1704)
- `cps/templates/detail.html` - Added Similar Books section (lines 349-395)

**Referenced (not modified):**
- `cps/ai/search.py` - `similar_books()` function
- `cps/ai/embeddings.py` - `embedding_exists()` function

