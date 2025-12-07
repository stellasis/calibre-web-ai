# Story 3.3: Search Route Integration and UI

**Status:** ready-for-dev  
**Epic:** Epic 3 - AI Semantic Search  
**Story ID:** 3.3  
**Created:** 2025-12-04  
**Prerequisites:** Story 3.2 (Semantic Search Service)

---

## Story

As a user,  
I want to toggle between standard and AI search on the search page,  
So that I can use semantic search when needed.

---

## Acceptance Criteria

**Given** I am on the search page  
**When** `config.config_ai_enabled` is true  
**Then** I see a search mode toggle:

- **Toggle Options:**
  - "Standard Search" (default, active)
  - "AI Search" (with "Beta" badge)
  - Implemented as `btn-group` with radio buttons OR `nav-tabs`
  - Icons: `glyphicon-search` for standard, `glyphicon-brain` for AI

**And** when I select "AI Search" and submit a query:
- URL includes `?ai=1` parameter
- Route handler checks `?ai=1` parameter
- If `ai=1`: Calls `ai.search.semantic_search(query)` (from Story 3.2)
- If not: Uses existing standard search
- Results displayed in same layout as standard search

**And** route implementation:
- File: Extend `cps/search.py` (existing search route)
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

---

## Tasks / Subtasks

- [ ] Task 1: Extend search route handler (AC: route implementation)
  - [ ] Locate search route in `cps/search.py` (`simple_search()` function)
  - [ ] Add `?ai=1` parameter detection: `request.args.get('ai') == '1'`
  - [ ] If `ai=1` and `config.config_ai_enabled`:
    - [ ] Call `ai.search.semantic_search(query, limit=20)`
    - [ ] Pass results to template with `ai_search=True`
  - [ ] If not `ai=1` or AI disabled:
    - [ ] Use existing standard search
    - [ ] Pass results to template with `ai_search=False`
  - [ ] Ensure results format matches existing search result format

- [ ] Task 2: Add search mode toggle to template (AC: template integration)
  - [ ] Open `cps/templates/search.html`
  - [ ] Add toggle button group near search input (before or after sort buttons)
  - [ ] Use Bootstrap `btn-group` with radio buttons (Option A from UX guide)
  - [ ] Add conditional: `{% if config.config_ai_enabled %}`
  - [ ] Toggle options:
    - [ ] "Standard Search" with `glyphicon-search` icon (default, active)
    - [ ] "AI Search" with `glyphicon-brain` icon and "Beta" badge
  - [ ] Set active state based on `ai_search` template variable

- [ ] Task 3: Create JavaScript for mode switching (AC: JavaScript functionality)
  - [ ] Create `cps/static/js/ai/search.js` file
  - [ ] Follow pattern from `cps/static/js/ai/summary.js`
  - [ ] Handle radio button change event
  - [ ] Update URL with `?ai=1` parameter when AI mode selected
  - [ ] Remove `?ai=1` parameter when standard mode selected
  - [ ] Reload page with updated URL
  - [ ] Preserve existing query parameter (`?q=query`)

- [ ] Task 4: Include JavaScript in template (AC: JavaScript functionality)
  - [ ] Add script include in `cps/templates/search.html`
  - [ ] Use `{% block header %}` or base template pattern
  - [ ] Include: `<script src="{{ url_for('static', filename='js/ai/search.js') }}"></script>`
  - [ ] Ensure jQuery is loaded (should already be available)

- [ ] Task 5: Ensure results display compatibility (AC: results display)
  - [ ] Verify AI search results match existing search result format
  - [ ] Ensure results use same template structure (`entries` variable)
  - [ ] Test that results display correctly in existing search template
  - [ ] No special formatting needed (reuse existing search result template)

- [ ] Task 6: Testing
  - [ ] Test search route with `?ai=1` parameter
  - [ ] Test search route without `?ai=1` parameter (standard search)
  - [ ] Test template rendering with AI mode
  - [ ] Test template rendering without AI mode
  - [ ] Test JavaScript mode toggle functionality
  - [ ] Test conditional rendering (`config.config_ai_enabled`)
  - [ ] Test results display (same format as standard search)

---

## Dev Notes

### Architecture Compliance

**Route Extension:** [Source: docs/epic-3-context.md#Route-Integration, docs/epics/epic-3-search.md#Story-3.3]
- File: Extend `cps/search.py` (existing search route)
- Route: Existing search route with `?ai=1` parameter handling
- Function: Check `request.args.get('ai') == '1'` to determine search mode
- Pass `ai_search=True` to template when AI mode active

**Route Implementation Pattern:** [Source: docs/epic-3-context.md#Route-Implementation, cps/search.py]
```python
@search.route("/search", methods=["GET"])
@login_required_if_no_ano
def simple_search():
    query = request.args.get("query")
    ai_mode = request.args.get('ai') == '1'
    
    if ai_mode and config.config_ai_enabled:
        # Use AI semantic search
        results = ai.search.semantic_search(query, limit=20)
        return render_title_template('search.html',
                                   entries=results,
                                   query=query,
                                   ai_search=True,
                                   ...)
    else:
        # Use standard search (existing logic)
        ...
```

**Template Integration:** [Source: docs/epic-3-context.md#Template-Integration, docs/ux-integration-guide.md#2.1-2.3]
- File: `cps/templates/search.html`
- Placement: Near search input, as toggle button group or tabs
- Conditional: `{% if config.config_ai_enabled %}`
- JavaScript: `cps/static/js/ai/search.js` for mode switching

**UI Components:** [Source: docs/ux-integration-guide.md#2.2, docs/epic-3-context.md#UI-Integration]
- **Option A: Button Group (Recommended)**
  - Bootstrap `btn-group` with radio buttons
  - "Standard Search" (default, active)
  - "AI Search" (with "Beta" badge)
  - Icons: `glyphicon-search` for standard, `glyphicon-brain` for AI

- **Option B: Tab Interface**
  - Bootstrap `nav-tabs`
  - Same options as button group

**JavaScript Functionality:** [Source: docs/ux-integration-guide.md#2.3, docs/epic-3-context.md#JavaScript-Functionality]
- File: `cps/static/js/ai/search.js`
- Functionality:
  - Mode toggle updates URL with `?ai=1` parameter
  - Page reloads with AI search results
  - Results use same display format as standard search
- Follow pattern from `cps/static/js/ai/summary.js`

**Results Display:** [Source: docs/epic-3-context.md#Results-Display, docs/ux-integration-guide.md#2.3]
- Same layout as standard search results
- No special formatting needed (reuse existing search result template)
- Display similarity score optionally (for debugging/transparency)

### Codebase Integration Points

**Existing Search Route:** [Source: cps/search.py lines 40-51]
- Route: `@search.route("/search", methods=["GET"])`
- Function: `simple_search()`
- Decorator: `@login_required_if_no_ano`
- Current behavior: Redirects to `web.books_list` with search data
- Need to extend to handle `?ai=1` parameter before redirect

**Search Template:** [Source: cps/templates/search.html]
- Template structure: Uses `entries` variable for results
- Display format: Grid layout with book covers (`col-sm-3 col-lg-2 col-xs-6 book`)
- Sort buttons: Already present (lines 31-38)
- Placement: Add toggle near sort buttons or search input

**JavaScript Patterns:** [Source: cps/static/js/ai/summary.js]
- Follow jQuery-based pattern
- Use CSRF token handling
- Use AJAX for API calls (if needed)
- Handle loading states and errors

**Template Rendering:** [Source: cps/search.py]
- Use `render_title_template()` function
- Pass template variables: `entries`, `query`, `ai_search`, etc.
- Follow existing template variable patterns

### Project Structure Notes

**File Organization:**
- Extend existing: `cps/search.py`
- Extend existing: `cps/templates/search.html`
- New file: `cps/static/js/ai/search.js`
- Follows existing `cps/ai/` and `cps/static/js/ai/` patterns

**Naming Conventions:** [Source: docs/architecture.md#Naming-Patterns]
- Route parameter: `ai=1` (query parameter)
- Template variable: `ai_search` (boolean)
- JavaScript file: `search.js` (snake_case)
- Follows existing codebase patterns

### References

- [Source: docs/epic-3-context.md] - Epic 3 technical context
- [Source: docs/epics/epic-3-search.md#Story-3.3] - Story requirements
- [Source: docs/ux-integration-guide.md#2.1-2.3] - UX design patterns
- [Source: docs/architecture.md#3.2] - API endpoint patterns
- [Source: cps/search.py] - Existing search route
- [Source: cps/templates/search.html] - Existing search template
- [Source: cps/static/js/ai/summary.js] - JavaScript patterns
- [Source: Story 3.2] - Semantic search service

### Critical Implementation Details

1. **Route Extension:** [Source: docs/epic-3-context.md#Route-Pattern]
   - Extend existing search route, don't replace it
   - Check `?ai=1` parameter to determine search mode
   - Pass `ai_search=True` to template when AI mode active
   - Maintain backward compatibility (standard search still works)

2. **Template Integration:** [Source: docs/ux-integration-guide.md#2.1-2.2]
   - Add toggle near search input or sort buttons
   - Use Bootstrap `btn-group` with radio buttons (recommended)
   - Conditional rendering: `{% if config.config_ai_enabled %}`
   - Set active state based on `ai_search` variable

3. **JavaScript Functionality:** [Source: docs/ux-integration-guide.md#2.3]
   - Update URL with `?ai=1` parameter when AI mode selected
   - Remove `?ai=1` parameter when standard mode selected
   - Preserve existing query parameter (`?q=query`)
   - Reload page with updated URL

4. **Results Display:** [Source: docs/epic-3-context.md#Results-Display]
   - Same layout as standard search (reuse existing template)
   - No special formatting needed
   - Ensure results format matches `entries` variable structure

### Common Pitfalls to Avoid

1. **Don't break existing search** - AI search should be additive, not replacement
2. **Don't forget conditional rendering** - Only show toggle if `config.config_ai_enabled`
3. **Don't forget URL parameter handling** - Must preserve `?q=query` when toggling
4. **Don't forget results format** - Must match existing search result structure
5. **Don't forget JavaScript inclusion** - Must include script in template

---

## Dev Agent Record

### Context Reference

- Epic 3 Technical Context: `docs/epic-3-context.md`
- Epic 3 Story Details: `docs/epics/epic-3-search.md`
- Story 3.2: `docs/sprint-artifacts/3-2-semantic-search-service.md`
- UX Integration Guide: `docs/ux-integration-guide.md`

### Agent Model Used

TBD

### Debug Log References

TBD

### Completion Notes List

TBD

### File List

TBD



