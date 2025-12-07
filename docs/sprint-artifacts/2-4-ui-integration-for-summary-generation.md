# Story 2.4: UI Integration for Summary Generation

**Status:** done  
**Epic:** Epic 2 - AI Summary Feature  
**Story ID:** 2.4  
**Created:** 2025-12-04

---

## Story

As a user,  
I want a button and display area for AI summaries on the book detail page,  
So that I can generate and view summaries easily.

---

## Acceptance Criteria

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

---

## Tasks / Subtasks

- [ ] Task 1: Update route handler (AC: template integration)
  - [ ] Modify book detail route in `cps/web.py`
  - [ ] Query `book_summaries` table for existing summary
  - [ ] Pass `ai_summary` variable to template

- [ ] Task 2: Update template (AC: UI components)
  - [ ] Add AI Summary section to `cps/templates/detail.html`
  - [ ] Add conditional rendering for `config.config_ai_enabled`
  - [ ] Add Generate/Refresh buttons
  - [ ] Add summary display panel
  - [ ] Add loading and error states

- [ ] Task 3: Create JavaScript (AC: JavaScript functionality)
  - [ ] Create `cps/static/js/ai/summary.js`
  - [ ] Implement button click handlers
  - [ ] Implement API call to `/api/ai/summary/<book_id>`
  - [ ] Implement loading state display
  - [ ] Implement success/error handling
  - [ ] Implement page reload or DOM update

- [ ] Task 4: Include JavaScript in template (AC: JavaScript functionality)
  - [ ] Add script tag to include `summary.js`
  - [ ] Ensure script loads after page content

- [ ] Task 5: Test integration (AC: all)
  - [ ] Test with AI enabled
  - [ ] Test with AI disabled
  - [ ] Test button click and API call
  - [ ] Test loading state
  - [ ] Test success/error handling
  - [ ] Test summary display

---

## Dev Notes

### Architecture Compliance

**Template Integration:** [Source: docs/architecture.md#4, docs/epics/epic-2-summary.md#Story-2.4]
- Extend existing `detail.html` template
- Use Bootstrap classes and Glyphicons
- Follow existing template patterns

**Route Handler:** [Source: docs/architecture.md#3.2, docs/epics/epic-2-summary.md#Story-2.4]
- Query `book_summaries` table for existing summary
- Pass `ai_summary` variable to template
- Follow existing route handler patterns

**JavaScript:** [Source: docs/architecture.md#4, docs/epics/epic-2-summary.md#Story-2.4]
- Create `cps/static/js/ai/summary.js`
- Use jQuery or vanilla JavaScript (match existing patterns)
- Follow existing JavaScript patterns

**UX Integration:** [Source: docs/epics/epic-2-summary.md#UX-Integration]
- Follow UX Design section 1.1-1.3 exactly
- Use Bootstrap classes: `btn btn-primary`, `panel panel-default`
- Use Glyphicons: `glyphicon-text-width`, `glyphicon-refresh`, `glyphicon-info-sign`

### Technical Implementation Details

**Template Section:**
```jinja2
{% if config.config_ai_enabled %}
<div class="ai-summary-section">
  <!-- Generate button -->
  <!-- Summary display -->
  <!-- Loading/error states -->
</div>
{% endif %}
```

**JavaScript Pattern:**
```javascript
$(document).ready(function() {
  $('#generate-ai-summary').click(function() {
    var bookId = $(this).data('book-id');
    // API call and state management
  });
});
```

**Route Handler:**
```python
from .. import ub
ai_summary = ub.session.query(ub.BookSummary).filter(
    ub.BookSummary.book_id == book_id
).first()
```

### File Structure

```
cps/
  templates/
    detail.html        # MODIFY: Add AI summary section
  static/
    js/
      ai/
        summary.js    # NEW: JavaScript for summary generation
```

### Dependencies

**Required:**
- `cps.templates.detail.html` - Book detail template
- `cps.static.js` - JavaScript directory
- jQuery (if used in existing templates)

### References

- [Source: docs/architecture.md#4] - Template and JavaScript patterns
- [Source: docs/epics/epic-2-summary.md#Story-2.4] - Story requirements
- [Source: cps/templates/detail.html] - Existing template
- [Source: cps/static/js/] - Existing JavaScript patterns

---

## Dev Agent Record

### Context Reference

### Agent Model Used

Auto (Cursor AI)

### Debug Log References

### Completion Notes List

### File List

- `cps/web.py` - Route handler updated to pass `ai_summary` to template
- `cps/templates/detail.html` - AI Summary section added
- `cps/static/js/ai/summary.js` - JavaScript for summary generation UI

### Completion Notes List

- ✅ Updated `show_book()` route to query and pass `ai_summary`
- ✅ Added AI Summary section to `detail.html` template
- ✅ Implemented Generate/Refresh buttons with Bootstrap styling
- ✅ Added loading and error states
- ✅ Created JavaScript for API interaction
- ✅ Integrated with existing template structure
