# Story 5.1: Admin Configuration Display

**Status:** Ready for Review  
**Epic:** Epic 5 - Configuration UI  
**Story ID:** 5.1  
**Created:** 2025-12-04

---

## Story

As an administrator,  
I want to see AI configuration status in the admin interface,  
So that I can quickly check if AI features are configured.

---

## Acceptance Criteria

**Given** I am an administrator viewing the admin page  
**When** I navigate to the admin interface  
**Then** I see an "AI Features" section:

- **Placement:** After "Configuration" section (around line 163), before "Scheduled Tasks" section
- **Layout:** Table/row layout matching existing admin sections

- **Status Display:** (if AI enabled)
  - AI Features: `glyphicon-ok text-success` "Enabled"
  - AI Provider: Provider name (e.g., "OpenAI")
  - LLM Model: Model name (e.g., "gpt-4o-mini")
  - Embedding Model: Model name (e.g., "text-embedding-3-small")
  - API Key: "Configured (sk-1234...)" or "Not configured" (masked display)

- **Status Display:** (if AI disabled)
  - AI Features: `glyphicon-remove text-danger` "Disabled"
  - Info alert: "AI features are disabled. Configure AI settings to enable."

- **Action Button:** "Edit AI Settings" (`btn btn-default`)
  - Links to `/admin/edit_ai_settings` route

**And** template integration:
- File: `cps/templates/admin.html`
- Placement: After "Configuration" section (after line 163), before "Scheduled Tasks" section
- Conditional: `{% if current_user.role_admin() %}`
- Use existing admin section patterns (table/row layout)

---

## Tasks / Subtasks

- [x] Task 1: Add AI Features section to admin.html template (AC: template integration)
  - [x] Open `cps/templates/admin.html`
  - [x] Add new section after "Configuration" section (after line 163)
  - [x] Use same structure as "Configuration" section (row/col layout)
  - [x] Add conditional rendering for admin users
  - [x] Add status display rows for AI configuration values
  - [x] Add "Edit AI Settings" button

- [x] Task 2: Update admin route to pass AI configuration (AC: status display)
  - [x] Open `cps/admin.py`
  - [x] Modify `admin()` route function (around line 205)
  - [x] Load AI configuration from `config.config_ai_*` attributes
  - [x] Pass AI configuration values to template
  - [x] Handle API key masking (show first 8 chars + "...")

- [x] Task 3: Create route for edit_ai_settings (AC: action button)
  - [x] Add route `@admi.route("/admin/edit_ai_settings")` in `cps/admin.py`
  - [x] Add `@admin_required` decorator
  - [x] Create placeholder function (will be implemented in Story 5.2)
  - [x] Return redirect to admin page for now

- [x] Task 4: Test integration (AC: all)
  - [x] Code review and syntax validation completed
  - [x] Manual testing required (no local test framework available)
  - [x] Verified template syntax and route implementation
  - [x] Verified API key masking logic
  - [x] Verified button link route exists

---

## Dev Notes

### Architecture Compliance

**Template Integration:** [Source: docs/architecture.md#4.4, docs/epics/epic-5-configuration.md#Story-5.1]
- Extend existing `admin.html` template
- Use Bootstrap classes and Glyphicons
- Follow existing admin section patterns (row/col layout)

**Route Handler:** [Source: docs/architecture.md#4.4, docs/epics/epic-5-configuration.md#Story-5.1]
- Extend existing `admin()` route in `cps/admin.py`
- Load configuration from `config.config_ai_*` attributes
- Pass configuration values to template

**Configuration Access:** [Source: docs/architecture.md#3.5, docs/sprint-artifacts/1-3-configuration-management-infrastructure.md]
- Configuration stored in database via `cps/config_sql.py`
- Access via `config.config_ai_enabled`, `config.config_ai_provider`, etc.
- API key stored encrypted in `config_ai_api_key_e` column

**UX Integration:** [Source: docs/ux-integration-guide.md#4, docs/epics/epic-5-configuration.md#UX-Integration]
- Follow UX Design section 4.1-4.2 exactly
- Use table/row layout matching existing admin sections
- Use status indicators: `glyphicon-ok` / `glyphicon-remove` with `text-success` / `text-danger`
- Mask API key display: Show first 8 characters + "..."

### Technical Implementation Details

**Template Section Pattern:**
```jinja2
{% if current_user.role_admin() %}
  <div class="row">
    <div class="col">
      <h2>{{_('AI Features')}}</h2>
      <div class="col-xs-12 col-sm-12">
        <div class="row">
          <div class="col-xs-6 col-sm-7">{{_('AI Features')}}</div>
          <div class="col-xs-6 col-sm-5">
            {% if config.config_ai_enabled %}
              <span class="glyphicon glyphicon-ok text-success"></span> {{_('Enabled')}}
            {% else %}
              <span class="glyphicon glyphicon-remove text-danger"></span> {{_('Disabled')}}
            {% endif %}
          </div>
        </div>
        <!-- More rows for provider, models, API key -->
      </div>
      <a class="btn btn-default" href="{{url_for('admin.edit_ai_settings')}}">{{_('Edit AI Settings')}}</a>
    </div>
  </div>
{% endif %}
```

**Route Handler Pattern:**
```python
@admi.route("/admin/view")
@user_login_required
@admin_required
def admin():
    # ... existing code ...
    
    # Load AI configuration
    ai_config = {
        'enabled': config.config_ai_enabled,
        'provider': config.config_ai_provider,
        'llm_model': config.config_ai_llm_model,
        'embedding_model': config.config_ai_embedding_model,
        'api_key_masked': mask_api_key(config.config_ai_api_key) if config.config_ai_api_key else None
    }
    
    return render_title_template("admin.html", ..., ai_config=ai_config, ...)
```

**API Key Masking:**
```python
def mask_api_key(api_key):
    """Mask API key for display: show first 8 chars + '...'"""
    if not api_key or len(api_key) < 8:
        return None
    return api_key[:8] + "..."
```

### Previous Story Learnings

**From Story 1.3 (Configuration Infrastructure):**
- Configuration is stored in database via `cps/config_sql.py`
- Access configuration via `config.config_ai_*` attributes
- API key is encrypted in `config_ai_api_key_e` column
- Use `config.config_ai_api_key` to get decrypted key (if available)

**From Story 2.4 (UI Integration):**
- Follow existing template patterns exactly
- Use Bootstrap classes consistently
- Use Glyphicons for status indicators
- Conditional rendering with `{% if config.config_ai_enabled %}`

---

## File List

- `cps/templates/admin.html` - Added AI Features section after Configuration section
- `cps/admin.py` - Updated admin() route to pass masked API key, added edit_ai_settings() route

---

## Dev Agent Record

### Implementation Notes

**Task 1 - Template Integration:**
- Added AI Features section to `admin.html` after Configuration section (line 163)
- Used same row/col layout pattern as existing admin sections
- Added conditional rendering with `{% if current_user.role_admin() %}`
- Implemented status display with glyphicons (ok/remove) and text-success/text-danger classes
- Added info alert when AI is disabled
- Added "Edit AI Settings" button linking to `/admin/edit_ai_settings`

**Task 2 - Route Updates:**
- Modified `admin()` route in `cps/admin.py` to mask API key
- Created helper logic to show first 8 characters + "..." for API key display
- Passed `ai_api_key_masked` variable to template

**Task 3 - Edit Route:**
- Added `edit_ai_settings()` route with `@admin_required` decorator
- Created placeholder that redirects to admin page (full implementation in Story 5.2)

### Technical Decisions

- API key masking: Show first 8 characters + "..." for security
- Template structure: Followed existing admin section patterns exactly
- Conditional rendering: Only show to admin users using `current_user.role_admin()`

---

## Change Log

- 2025-12-04: Added AI Features section to admin interface
  - Added template section displaying AI configuration status
  - Updated admin route to pass masked API key
  - Added placeholder edit_ai_settings route

