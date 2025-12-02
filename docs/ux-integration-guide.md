# UX Integration Guide: AI Features for Calibre-Web

**Purpose:** Lightweight guide for integrating AI features into existing calibre-web UI  
**Target:** Developers implementing AI features  
**Date:** 2025-01-27

---

## Overview

This guide provides specific instructions for integrating three AI features into calibre-web's existing Bootstrap-based UI:

1. **AI Summary** - Button and display area on book detail page
2. **AI Semantic Search** - Toggle/tab on search page
3. **Similar Books** - Section on book detail page
4. **AI Configuration** - Admin settings section

**Design Philosophy:** Match existing calibre-web patterns exactly. New features should feel native to the application, not like add-ons.

---

## 1. AI Summary Feature

### 1.1 Placement in Template

**File:** `cps/templates/detail.html`

**Location:** After the book metadata section, before or after the comments/description section.

**Recommended placement:** After the book metadata (`<div class="col-sm-9 col-lg-9 book-meta">`) and before the comments section.

### 1.2 UI Components

**Generate Button:**
```html
{% if config.config_ai_enabled %}
  <div class="ai-summary-section" style="margin-top: 20px; margin-bottom: 20px;">
    <div class="btn-toolbar" role="toolbar">
      <div class="btn-group" role="group">
        <button id="generate-ai-summary" 
                type="button" 
                class="btn btn-primary"
                data-book-id="{{ entry.id }}">
          <span class="glyphicon glyphicon-text-width"></span> 
          {{ _('Generate AI Summary') }}
        </button>
        {% if ai_summary %}
          <button id="refresh-ai-summary" 
                  type="button" 
                  class="btn btn-default"
                  data-book-id="{{ entry.id }}">
            <span class="glyphicon glyphicon-refresh"></span> 
          </button>
        {% endif %}
      </div>
    </div>
    
    <div id="ai-summary-container" style="margin-top: 15px;">
      {% if ai_summary %}
        <div class="panel panel-default">
          <div class="panel-heading">
            <h4 class="panel-title">
              <span class="glyphicon glyphicon-info-sign"></span> 
              {{ _('AI Summary') }}
            </h4>
          </div>
          <div class="panel-body">
            <p>{{ ai_summary.summary_text }}</p>
            <small class="text-muted">
              {{ _('Generated on') }} {{ ai_summary.created_at.strftime('%Y-%m-%d %H:%M') }}
            </small>
          </div>
        </div>
      {% else %}
        <div id="ai-summary-placeholder" class="text-muted" style="display: none;">
          <p>{{ _('Click "Generate AI Summary" to create an AI-powered summary of this book.') }}</p>
        </div>
      {% endif %}
      
      <div id="ai-summary-loading" style="display: none;">
        <div class="text-center">
          <span class="glyphicon glyphicon-refresh glyphicon-spin"></span>
          <p>{{ _('Generating summary...') }}</p>
        </div>
      </div>
      
      <div id="ai-summary-error" class="alert alert-danger" style="display: none;">
        <span class="glyphicon glyphicon-exclamation-sign"></span>
        <span id="ai-summary-error-message"></span>
      </div>
    </div>
  </div>
{% endif %}
```

**Design Patterns:**
- Use `btn btn-primary` for primary action (matches existing download/read buttons)
- Use `btn btn-default` for secondary action (refresh)
- Use `panel panel-default` for summary display (matches existing info sections)
- Use `glyphicon` icons consistent with existing UI
- Use Bootstrap spacing utilities (`margin-top`, `margin-bottom`)

### 1.3 JavaScript Integration

**File:** `cps/static/js/ai/summary.js`

**Functionality:**
- Handle button click → POST to `/api/ai/summary/<book_id>`
- Show loading state (spinner)
- Display summary on success
- Show error message on failure
- Handle refresh button

**Example:**
```javascript
$(document).ready(function() {
  $('#generate-ai-summary').on('click', function() {
    var bookId = $(this).data('book-id');
    var $container = $('#ai-summary-container');
    var $loading = $('#ai-summary-loading');
    var $error = $('#ai-summary-error');
    var $placeholder = $('#ai-summary-placeholder');
    
    // Hide existing content
    $container.find('.panel').hide();
    $error.hide();
    $placeholder.hide();
    
    // Show loading
    $loading.show();
    
    $.ajax({
      url: '/api/ai/summary/' + bookId,
      method: 'POST',
      success: function(data) {
        $loading.hide();
        // Reload page or update DOM with new summary
        location.reload();
      },
      error: function(xhr) {
        $loading.hide();
        $error.show();
        $('#ai-summary-error-message').text(
          xhr.responseJSON?.error || 'Failed to generate summary'
        );
      }
    });
  });
});
```

### 1.4 User Flow

```
User views book detail page
  ↓
User clicks "Generate AI Summary" button
  ↓
Button shows loading state (spinner)
  ↓
Background task generates summary
  ↓
Page refreshes or updates with summary
  ↓
Summary displayed in panel below button
```

---

## 2. AI Semantic Search Feature

### 2.1 Placement in Template

**File:** `cps/templates/search.html`

**Location:** Near the search input, as a toggle or tab.

**Recommended placement:** Add toggle button next to existing sort buttons, or add a tab/radio button group above search results.

### 2.2 UI Components

**Option A: Toggle Button (Recommended)**
```html
{% if config.config_ai_enabled %}
  <div class="btn-toolbar" role="toolbar" style="margin-bottom: 15px;">
    <div class="btn-group" role="group" data-toggle="buttons">
      <label class="btn btn-primary{% if not ai_search %} active{% endif %}">
        <input type="radio" name="search-mode" value="standard" autocomplete="off" checked>
        <span class="glyphicon glyphicon-search"></span> {{ _('Standard Search') }}
      </label>
      <label class="btn btn-primary{% if ai_search %} active{% endif %}">
        <input type="radio" name="search-mode" value="ai" autocomplete="off">
        <span class="glyphicon glyphicon-brain"></span> {{ _('AI Search') }} <span class="badge">Beta</span>
      </label>
    </div>
  </div>
{% endif %}
```

**Option B: Tab Interface**
```html
{% if config.config_ai_enabled %}
  <ul class="nav nav-tabs" role="tablist" style="margin-bottom: 15px;">
    <li role="presentation"{% if not ai_search %} class="active"{% endif %}>
      <a href="{{ url_for('web.search', q=query) }}">
        <span class="glyphicon glyphicon-search"></span> {{ _('Standard Search') }}
      </a>
    </li>
    <li role="presentation"{% if ai_search %} class="active"{% endif %}>
      <a href="{{ url_for('web.search', q=query, ai=1) }}">
        <span class="glyphicon glyphicon-brain"></span> {{ _('AI Search') }} <span class="badge">Beta</span>
      </a>
    </li>
  </ul>
{% endif %}
```

**Design Patterns:**
- Use `btn-group` with radio buttons for toggle (matches existing sort buttons)
- Use `nav-tabs` if preferred (matches existing tab patterns)
- Add "Beta" badge to indicate experimental feature
- Use `glyphicon-brain` or `glyphicon-search` for visual distinction

### 2.3 Search Results Display

**No changes needed** - AI search results use the same display format as standard search results. The route handler determines which search method to use based on `?ai=1` parameter.

**JavaScript Enhancement:**
```javascript
// In cps/static/js/ai/search.js
$(document).ready(function() {
  $('input[name="search-mode"]').on('change', function() {
    var mode = $(this).val();
    var query = $('#query').val();
    var url = new URL(window.location);
    
    if (mode === 'ai') {
      url.searchParams.set('ai', '1');
    } else {
      url.searchParams.delete('ai');
    }
    
    if (query) {
      url.searchParams.set('q', query);
    }
    
    window.location.href = url.toString();
  });
});
```

### 2.4 User Flow

```
User navigates to search page
  ↓
User sees search input and mode toggle
  ↓
User selects "AI Search" mode
  ↓
User enters natural language query
  ↓
User submits search
  ↓
Results displayed using semantic similarity
  ↓
Results look identical to standard search (same card layout)
```

---

## 3. Similar Books Feature

### 3.1 Placement in Template

**File:** `cps/templates/detail.html`

**Location:** Near the bottom of the detail page, after all other book information sections.

**Recommended placement:** After the comments/description section, before the footer or related books section (if exists).

### 3.2 UI Components

```html
{% if config.config_ai_enabled and similar_books %}
  <div class="similar-books-section" style="margin-top: 30px;">
    <h3>
      <span class="glyphicon glyphicon-book"></span> 
      {{ _('Similar Books') }}
    </h3>
    <div class="row display-flex">
      {% for similar_book in similar_books[:8] %}
        <div class="col-sm-3 col-lg-2 col-xs-6 book">
          <div class="cover">
            <a href="{{ url_for('web.show_book', book_id=similar_book.id) }}">
              <span class="img" title="{{ similar_book.title }}">
                {{ image.book_cover(similar_book) }}
              </span>
            </a>
          </div>
          <div class="meta">
            <a href="{{ url_for('web.show_book', book_id=similar_book.id) }}">
              <p title="{{ similar_book.title }}" class="title">
                {{ similar_book.title|shortentitle }}
              </p>
            </a>
            <p class="author">
              {% for author in similar_book.authors %}
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
  </div>
{% elif config.config_ai_enabled and not similar_books and entry.id %}
  <div class="similar-books-section" style="margin-top: 30px;">
    <div class="alert alert-info">
      <span class="glyphicon glyphicon-info-sign"></span>
      {{ _('Similar books will appear here after an AI summary is generated for this book.') }}
    </div>
  </div>
{% endif %}
```

**Design Patterns:**
- Use exact same layout as search results (`row display-flex`, `col-sm-3 col-lg-2 col-xs-6 book`)
- Reuse `cover` and `meta` classes for consistency
- Use `image.book_cover()` macro for covers
- Show info message if no similar books available (when no summary exists)
- Limit to 8 books maximum (as per PRD)

### 3.3 User Flow

```
User views book detail page
  ↓
Page loads similar books section
  ↓
If embedding exists:
  - Fetch similar books via API
  - Display in grid layout (same as search results)
  ↓
If no embedding:
  - Show info message: "Similar books will appear after summary is generated"
  ↓
User clicks similar book → navigates to that book's detail page
```

---

## 4. AI Configuration (Admin)

### 4.1 Placement in Template

**File:** `cps/templates/admin.html`

**Location:** Add new section after existing configuration sections (Email, Features, etc.).

**Recommended placement:** After "Features" section, before "Advanced" or at the end of configuration sections.

### 4.2 UI Components

```html
{% if current_user.role_admin() %}
  <div class="row">
    <div class="col">
      <h2>{{ _('AI Features') }}</h2>
      
      {% if config.get_ai_enabled() %}
        <div class="col-xs-12 col-sm-12">
          <div class="row">
            <div class="col-xs-6 col-sm-3">{{ _('AI Features') }}</div>
            <div class="col-xs-6 col-sm-3">
              <span class="glyphicon glyphicon-ok text-success"></span> {{ _('Enabled') }}
            </div>
          </div>
          <div class="row">
            <div class="col-xs-6 col-sm-3">{{ _('AI Provider') }}</div>
            <div class="col-xs-6 col-sm-3">{{ config.config_ai_provider|default('Not configured') }}</div>
          </div>
          <div class="row">
            <div class="col-xs-6 col-sm-3">{{ _('LLM Model') }}</div>
            <div class="col-xs-6 col-sm-3">{{ config.config_ai_llm_model|default('Not configured') }}</div>
          </div>
          <div class="row">
            <div class="col-xs-6 col-sm-3">{{ _('Embedding Model') }}</div>
            <div class="col-xs-6 col-sm-3">{{ config.config_ai_embedding_model|default('Not configured') }}</div>
          </div>
          <div class="row">
            <div class="col-xs-6 col-sm-3">{{ _('API Key') }}</div>
            <div class="col-xs-6 col-sm-3">
              {% if config.config_ai_api_key %}
                <span class="text-muted">{{ _('Configured') }} ({{ config.config_ai_api_key[:8] }}...)</span>
              {% else %}
                <span class="text-danger">{{ _('Not configured') }}</span>
              {% endif %}
            </div>
          </div>
          <div class="row">
            <div class="col-xs-12">
              <small class="text-muted">
                {{ _('API keys are stored securely in the database. Configure via Edit AI Settings.') }}
              </small>
            </div>
          </div>
        </div>
      {% else %}
        <div class="col-xs-12 col-sm-12">
          <div class="row">
            <div class="col-xs-6 col-sm-3">{{ _('AI Features') }}</div>
            <div class="col-xs-6 col-sm-3">
              <span class="glyphicon glyphicon-remove text-danger"></span> {{ _('Disabled') }}
            </div>
          </div>
          <div class="alert alert-info">
            <span class="glyphicon glyphicon-info-sign"></span>
            {{ _('AI features are disabled. Configure AI settings to enable.') }}
          </div>
        </div>
      {% endif %}
      
      <a class="btn btn-default" id="admin_edit_ai" href="{{ url_for('admin.edit_ai_settings') }}">
        {{ _('Edit AI Settings') }}
      </a>
    </div>
  </div>
{% endif %}
```

**Edit Settings Page:**
Create `cps/templates/admin_ai_settings.html` following the pattern of `admin_edit_email.html`:

```html
{% extends "layout.html" %}
{% block body %}
<div class="container-fluid">
  <h2>{{ _('AI Features Configuration') }}</h2>
  
  <form method="POST" action="{{ url_for('admin.edit_ai_settings') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    
    <div class="form-group">
      <label for="ai_enabled">{{ _('Enable AI Features') }}</label>
      <input type="checkbox" name="ai_enabled" id="ai_enabled" 
             {% if config.config_ai_enabled %}checked{% endif %}>
    </div>
    
    <div class="form-group">
      <label for="ai_provider">{{ _('AI Provider') }}</label>
      <select name="ai_provider" id="ai_provider" class="form-control">
        <option value="openai" {% if config.config_ai_provider == 'openai' %}selected{% endif %}>OpenAI</option>
        <option value="anthropic" {% if config.config_ai_provider == 'anthropic' %}selected{% endif %}>Anthropic</option>
        <option value="ollama" {% if config.config_ai_provider == 'ollama' %}selected{% endif %}>Ollama</option>
      </select>
    </div>
    
    <div class="form-group">
      <label for="ai_api_key">{{ _('API Key') }}</label>
      <input type="password" 
             name="ai_api_key" 
             id="ai_api_key" 
             class="form-control"
             placeholder="{{ _('Enter API key') }}"
             value="{% if config.config_ai_api_key %}{{ config.config_ai_api_key }}{% endif %}">
      <small class="text-muted">
        {{ _('API key is stored securely in the database. Leave blank to keep existing key.') }}
      </small>
    </div>
    
    <!-- Additional form fields for LLM model, embedding model, etc. -->
    
    <button type="submit" class="btn btn-default">{{ _('Save') }}</button>
    <a href="{{ url_for('admin.admin') }}" class="btn btn-default">{{ _('Cancel') }}</a>
  </form>
</div>
{% endblock %}
```

**Design Patterns:**
- Use same table/row layout as existing admin sections
- Use `glyphicon-ok` / `glyphicon-remove` for status indicators
- Use `text-success` / `text-danger` for status colors
- Use `btn btn-default` for action buttons
- Follow existing form patterns for edit page

---

## 5. Design Consistency Rules

### 5.1 Bootstrap Classes

**Always use:**
- `btn btn-primary` for primary actions
- `btn btn-default` for secondary actions
- `btn-group` for button groups
- `panel panel-default` for content sections
- `alert alert-info` / `alert-danger` for messages
- `glyphicon` icons (not Font Awesome or other icon sets)
- Bootstrap grid: `col-sm-*`, `col-lg-*`, `col-xs-*`

**Never use:**
- Custom CSS classes that don't exist in calibre-web
- Inline styles except for spacing (`margin-top`, `margin-bottom`)
- Different icon libraries
- Different button styles

### 5.2 Spacing

**Consistent margins:**
- Section spacing: `margin-top: 20px` or `margin-top: 30px`
- Button groups: Use `btn-toolbar` wrapper
- Content sections: Use `panel` or existing spacing patterns

### 5.3 Colors

**Use existing color scheme:**
- Primary actions: Bootstrap default blue (`btn-primary`)
- Secondary actions: Bootstrap default gray (`btn-default`)
- Success: `text-success` (green)
- Danger: `text-danger` (red)
- Info: `alert-info` (light blue)
- Muted text: `text-muted`

### 5.4 Icons

**Available glyphicons in calibre-web:**
- `glyphicon-search` - Search
- `glyphicon-text-width` - Text/summary
- `glyphicon-refresh` - Refresh/reload
- `glyphicon-book` - Books
- `glyphicon-info-sign` - Information
- `glyphicon-ok` - Success/enabled
- `glyphicon-remove` - Error/disabled
- `glyphicon-exclamation-sign` - Warning
- `glyphicon-brain` - AI (if available, otherwise use `glyphicon-cog`)

---

## 6. Accessibility Considerations

### 6.1 ARIA Labels

**Always include:**
- `role="toolbar"` for button groups
- `role="group"` for button groups
- `aria-label` or `aria-labelledby` for groups
- `aria-expanded` for dropdowns/toggles

**Example:**
```html
<div class="btn-group" role="group" aria-label="AI Summary Actions">
  <button id="generate-ai-summary" type="button" class="btn btn-primary">
    <span class="glyphicon glyphicon-text-width"></span> 
    Generate AI Summary
  </button>
</div>
```

### 6.2 Keyboard Navigation

**Ensure:**
- All buttons are keyboard accessible (native `<button>` elements)
- Focus states are visible (Bootstrap handles this)
- Tab order is logical
- Form inputs have proper labels

### 6.3 Screen Readers

**Provide:**
- Descriptive button text (not just icons)
- Status messages for async operations
- Error messages that are announced
- Loading states that are announced

**Example:**
```html
<button id="generate-ai-summary" type="button" class="btn btn-primary">
  <span class="glyphicon glyphicon-text-width" aria-hidden="true"></span> 
  <span class="sr-only">Generate</span> AI Summary
</button>
```

### 6.4 Color Contrast

**Verify:**
- Text meets WCAG AA contrast ratios (Bootstrap defaults should be fine)
- Don't rely solely on color to convey information
- Use icons + text, not just color

---

## 7. Responsive Design

### 7.1 Breakpoints

**Follow existing patterns:**
- Mobile: `col-xs-6` (2 columns)
- Tablet: `col-sm-3` (4 columns)
- Desktop: `col-lg-2` (6 columns)

**Example (Similar Books):**
```html
<div class="col-sm-3 col-lg-2 col-xs-6 book">
  <!-- Book card -->
</div>
```

### 7.2 Mobile Considerations

**For AI Summary:**
- Button should be full-width on mobile or use `btn-block`
- Summary text should wrap properly
- Panel should stack vertically

**For AI Search:**
- Toggle buttons should stack on mobile or use `btn-group-vertical`
- Search input should remain full-width

**For Similar Books:**
- Grid automatically adapts (2 columns on mobile, 4 on tablet, 6 on desktop)
- No changes needed - existing pattern handles this

---

## 8. User Flow Diagrams

### 8.1 AI Summary Flow

```
┌─────────────────────────────────────┐
│  User views book detail page        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  User clicks "Generate AI Summary"  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Button shows loading spinner       │
│  Background task enqueued          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Summary generated (async)         │
│  Stored in database                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Page updates/refreshes             │
│  Summary displayed in panel         │
└─────────────────────────────────────┘
```

### 8.2 AI Search Flow

```
┌─────────────────────────────────────┐
│  User navigates to search page      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  User toggles to "AI Search" mode  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  User enters natural language query │
│  Example: "cozy fantasy books"      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Query converted to embedding       │
│  Vector search performed            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Results displayed (same layout)    │
│  Ranked by semantic similarity      │
└─────────────────────────────────────┘
```

### 8.3 Similar Books Flow

```
┌─────────────────────────────────────┐
│  User views book detail page        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Page checks for book embedding    │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │           │
    Has embedding  No embedding
         │           │
         ▼           ▼
┌──────────────┐  ┌──────────────────────┐
│ Fetch similar│  │ Show info message:   │
│ books via    │  │ "Similar books will  │
│ vector search│  │ appear after summary"│
└──────┬───────┘  └──────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Display 3-8 similar books         │
│  In grid layout (same as search)   │
└─────────────────────────────────────┘
```

---

## 9. Implementation Checklist

### 9.1 Template Extensions

- [ ] Add AI Summary section to `detail.html`
- [ ] Add AI Search toggle to `search.html`
- [ ] Add Similar Books section to `detail.html`
- [ ] Add AI Configuration section to `admin.html`
- [ ] Create `admin_ai_settings.html` for configuration form

### 9.2 JavaScript Files

- [ ] Create `cps/static/js/ai/summary.js` for summary generation
- [ ] Create `cps/static/js/ai/search.js` for search mode toggle
- [ ] Include scripts in templates (via `{% block header %}` or base template)

### 9.3 CSS (if needed)

- [ ] Add minimal CSS to `cps/static/css/style.css` or create `cps/static/css/ai.css`
- [ ] Only add styles that don't exist in Bootstrap
- [ ] Prefer Bootstrap utility classes over custom CSS

### 9.4 Testing

- [ ] Test on mobile devices (responsive layout)
- [ ] Test keyboard navigation
- [ ] Test with screen reader (basic)
- [ ] Test error states (API failures, timeouts)
- [ ] Test loading states
- [ ] Verify matches existing UI patterns

---

## 10. Quick Reference

### 10.1 Button Patterns

```html
<!-- Primary action -->
<button class="btn btn-primary">
  <span class="glyphicon glyphicon-icon-name"></span> Text
</button>

<!-- Secondary action -->
<button class="btn btn-default">
  <span class="glyphicon glyphicon-icon-name"></span> Text
</button>

<!-- Button group -->
<div class="btn-group" role="group">
  <button class="btn btn-primary">Action 1</button>
  <button class="btn btn-primary">Action 2</button>
</div>
```

### 10.2 Panel Pattern

```html
<div class="panel panel-default">
  <div class="panel-heading">
    <h4 class="panel-title">Title</h4>
  </div>
  <div class="panel-body">
    Content here
  </div>
</div>
```

### 10.3 Alert Pattern

```html
<div class="alert alert-info">
  <span class="glyphicon glyphicon-info-sign"></span>
  Message text
</div>
```

### 10.4 Grid Pattern

```html
<div class="row display-flex">
  <div class="col-sm-3 col-lg-2 col-xs-6 book">
    <!-- Book card -->
  </div>
</div>
```

---

## 11. Common Pitfalls to Avoid

❌ **Don't:**
- Create custom CSS that conflicts with existing styles
- Use different icon libraries (stick to Glyphicons)
- Use different button styles
- Add features that don't match existing patterns
- Skip accessibility attributes
- Hard-code text (always use `{{ _('Text') }}` for i18n)

✅ **Do:**
- Match existing Bootstrap patterns exactly
- Use existing CSS classes
- Follow existing spacing conventions
- Test responsive behavior
- Include ARIA labels
- Use translation functions for all text

---

## 12. Integration with Architecture

This guide implements the UI components specified in `docs/architecture.md`:

- **FR1 (AI Summary):** Section 1 of this guide
- **FR2 (AI Search):** Section 2 of this guide
- **FR3 (Similar Books):** Section 3 of this guide
- **FR4 (Configuration):** Section 4 of this guide

All UI components follow the architectural patterns:
- Template extensions (not new templates)
- JavaScript in `cps/static/js/ai/`
- Configuration in admin UI
- Conditional rendering based on `config.config_ai_enabled`

---

**Document Status:** Complete and ready for implementation  
**Last Updated:** 2025-01-27  
**Related Documents:** `docs/architecture.md`, `docs/prd.md`

