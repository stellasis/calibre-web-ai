# Epic 5: Configuration UI

**Epic Goal:** Enable administrators to configure AI features through a user-friendly interface.

**User Value Statement:** Administrators can configure AI features, set API keys, and manage provider settings through a user-friendly interface.

**PRD Coverage:** FR4 (Configuration Management - UI component)

**Technical Context:**
- Configuration storage: Database via `cps/config_sql.py` (Architecture section 3.5)
- Admin routes: Extended `cps/admin.py` (Architecture section 4.4)
- Validation: Dependency, provider-specific, value range validation (Architecture section 3.5)
- API key security: Stored securely in database (Architecture section 3.5)

**UX Integration:**
- Placement: After "Features" section in `admin.html` (UX section 4.1)
- UI components: Table/row layout matching existing admin sections (UX section 4.2)
- Edit page: `admin_ai_settings.html` following `admin_edit_email.html` pattern (UX section 4.2)
- Status indicators: `glyphicon-ok` / `glyphicon-remove` with `text-success` / `text-danger` (UX section 4.2)

**Dependencies:** Epic 1 (Foundation Setup - configuration infrastructure)

**Related Documents:**
- [Master Epic Index](../epics.md)
- [Epic 1: Foundation Setup](epic-1-foundation.md)
- [Architecture Document](../architecture.md)
- [UX Integration Guide](../ux-integration-guide.md)

---

## Story 5.1: Admin Configuration Display

As an administrator,
I want to see AI configuration status in the admin interface,
So that I can quickly check if AI features are configured.

**Acceptance Criteria:**

**Given** I am an administrator viewing the admin page
**When** I navigate to the admin interface
**Then** I see an "AI Features" section:

- **Placement:** After "Features" section, before "Advanced" or at end of configuration sections
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
- Placement: After "Features" section
- Conditional: `{% if current_user.role_admin() %}`
- Use existing admin section patterns (table/row layout)

**Technical Notes:**
- Follow UX Design section 4.1-4.2 exactly (UX Integration Guide)
- Use table/row layout matching existing admin sections (UX section 4.2)
- Use status indicators: `glyphicon-ok` / `glyphicon-remove` with `text-success` / `text-danger` (UX section 4.2)
- Mask API key display: Show first 8 characters + "..." (UX section 4.2)

**Prerequisites:** Story 1.3 (Configuration Infrastructure)

---

## Story 5.2: Admin Configuration Edit Page

As an administrator,
I want to edit AI configuration settings,
So that I can enable/disable features and configure providers.

**Acceptance Criteria:**

**Given** I am an administrator
**When** I click "Edit AI Settings" button
**Then** I see a configuration form page:

- **Page:** `cps/templates/admin_ai_settings.html`
- **Layout:** Follows `admin_edit_email.html` pattern
- **Form Fields:**
  - Enable AI Features: Checkbox (`ai_enabled`)
  - AI Provider: Dropdown (`ai_provider`) - Options: OpenAI, Anthropic, Ollama
  - LLM Model: Text input (`ai_llm_model`) - Default: "gpt-4o-mini"
  - Embedding Model: Text input (`ai_embedding_model`) - Default: "text-embedding-3-small"
  - API Key: Password input (`ai_api_key`) - Placeholder: "Enter API key" (leave blank to keep existing)
  - Max Summary Tokens: Number input (`ai_max_tokens_summary`) - Range: 100-2000, Default: 500
  - Request Timeout: Number input (`ai_timeout_seconds`) - Range: 10-300, Default: 60
  - Max Retries: Number input (`ai_max_retries`) - Range: 0-10, Default: 3

- **Form Actions:**
  - Save button: `btn btn-default` - Saves configuration to database
  - Cancel button: `btn btn-default` - Returns to admin page
  - Test Configuration button: `btn btn-default` - Validates settings and tests API connection

- **Validation:**
  - Real-time validation on input fields (red border + error message)
  - Dependency validation: If `AI_ENABLED=true`, provider, models, and API key required
  - Provider-specific validation: Model names must be valid for selected provider
  - Value range validation: Integers must be within specified ranges
  - API key format validation: Basic format check (e.g., OpenAI keys start with "sk-")

- **Success/Error Feedback:**
  - Success: Flash message "AI settings saved successfully"
  - Error: Flash message with specific validation errors
  - Test result: Display test connection result (success/failure)

**And** route implementation:
- File: Extend `cps/admin.py`
- Routes:
  - `@admin.route("/admin/edit_ai_settings")` - GET: Display form, POST: Save configuration
  - Decorator: `@admin_required`
  - Function: `edit_ai_settings()` - Handles GET (display) and POST (save)

**And** form processing:
- GET: Load current configuration from database, render form
- POST: Validate input, save to database, redirect to admin page with flash message
- API key handling: Only update if new value provided (don't overwrite with empty string)

**Technical Notes:**
- Follow UX Design section 4.2 exactly (UX Integration Guide)
- Create `admin_ai_settings.html` following `admin_edit_email.html` pattern (UX section 4.2)
- Use Bootstrap form classes: `form-group`, `form-control` (UX section 4.2)
- Use existing admin route patterns (Architecture section 4.4)
- Store configuration in database via `cps/config_sql.py` (Architecture section 3.5)
- Implement validation rules from Architecture section 3.5

**Prerequisites:** Story 5.1 (Admin Configuration Display), Story 1.3 (Configuration Infrastructure)

---

_Return to [Master Epic Index](../epics.md)_




