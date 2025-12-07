# AI Discovery & Insights for Calibre-Web – Week 1 MVP

## 1. Overview

Add AI-powered discovery features to `janeczku/calibre-web` to help users find and understand books more easily, without changing the core Calibre DB model.

Week-1 focus:

1. **On-demand AI summaries** for individual books (using metadata and, where possible, a small slice of the actual text).
2. **AI semantic search** over books, powered primarily by AI-generated summaries (with metadata as a fallback).
3. **“Similar books” recommendations** on the book detail page (reusing the same embeddings).

Implementation assumes a hosted LLM + embeddings API, orchestrated via **LangChain**, and a single-user or small-library deployment.

---

## 2. Goals & Non-Goals

### 2.1 Goals (for this week)

* Let users generate concise **AI summaries** of books to quickly understand what they’re about.
* Use those summaries as the **primary text source for semantic embeddings**.
* Let users perform **natural-language search** such as:

  * “cozy fantasy with found family and low stakes”
  * “intro book for machine learning with practical exercises”
* Surface a **“Similar books”** section on each book’s detail page.
* Ship something that can be enabled/disabled via configuration.

### 2.2 Non-Goals (this week)

* Full-library, production-grade retrieval-augmented Q&A over entire books.
* Complex, highly-scalable background job orchestration (simple workers and/or cron are fine).
* Multi-tenant / large-scale optimization.
* UI localization or extensive UX polish.

---

## 3. Users & Use Cases

### 3.1 Target Users

* Existing calibre-web users with mid-sized personal or team libraries.
* Power readers who search by vibe or topic, not specific titles.
* Knowledge workers using calibre-web for technical or non-fiction libraries.

### 3.2 Core Use Cases

1. **Semantic search for discovery**
   As a user, I want to type a fuzzy, natural query and get relevant books ranked by meaning, not just string matches.

2. **Similar book suggestions**
   As a user viewing a book, I want to see a short list of similar books to explore related content.

3. **Quick AI summary**
   As a user, I want a short AI-generated summary of a book so I can decide whether it’s worth reading.

4. **Summary-first indexing**
   As an admin, I want the system to use concise, human-readable summaries for search and recommendations so results feel aligned with how a reader would describe the book.

---

## 4. Product Scope (MVP)

### 4.1 AI Summary (On-Demand) — First Priority

**User experience**

* On the book detail page, add:

  * A button: **“Generate AI summary”**.
  * An area to display the summary; once generated, show:

    * A short paragraph (3–7 sentences) and/or a few bullet points.

**Behavior**

* When the button is clicked:

  1. Gather book metadata (title, author, description). Include the first 20 pages or first chapter (whichever is greater).
  2. Send a prompt (via LangChain) to the configured LLM to generate a concise summary focused on:

     * What the book is about.
     * Who it is for (audience).
     * Key themes/topics.
  3. Save the summary in the database or cache tied to the book.
  4. On subsequent visits, reuse the stored summary unless manually refreshed.

* These summaries become the **primary text used to build semantic embeddings** for discovery features (search and similar-books).

* Admins can optionally **pre-generate summaries for all books** via an admin-only bulk action (e.g., CLI command that enqueues background jobs).

---

### 4.2 AI Semantic Search (Using Summaries)

**User experience**

* Add an **“AI Search”** toggle or separate tab on the search page.
* Input: reuse the existing search text box, but clearly label the mode as something like **“AI Search (beta)”**.
* Output: list of books (cover, title, author, short snippet), similar to existing search results.

**Behavior**

* When “AI Search” is active:

  1. Take the user’s free-text query.
  2. Compute an embedding for the query via the configured embedding model (through LangChain).
  3. Compare the query embedding against precomputed **book embeddings** that are derived primarily from AI summaries.
  4. If a book doesn’t have a summary yet, fall back to an embedding built from metadata (title, author, description, tags).
  5. Return the top N results sorted by similarity score.

---

### 4.3 “Similar Books” Recommendations (Reusing Embeddings)

**User experience**

* On the book detail page, show a new section near the bottom:

  * Heading: **“Similar books”** (or **“You might also like”**).
  * Show 3–8 books with cover, title, and author.

**Behavior**

* On page load:

  1. Look up the embedding for the current book.
  2. Find the nearest neighbors in embedding space, excluding the current book itself.
  3. Display the top N results.
* If no embedding is available (e.g., no summary yet and no metadata embedding, or AI is disabled):

  * Hide the section, or
  * Show a small message like “Similar books will appear here after a summary is generated.”

---

## 5. Technical Design (High-Level)

### 5.1 Architecture

* New module (example): `cps/ai/` for:

  * `summarization.py` – AI summary generation and retrieval (via LangChain LLMs).
  * `embeddings.py` – create and retrieve vector representations for books (via LangChain embedding models).
  * `search.py` – semantic search and similarity queries.

* Data storage options (MVP):

  * Add a simple table to the calibre-web DB, e.g. `book_summaries`:

    * `book_id` (FK to book)
    * `summary_text`
    * `model_name`
    * `updated_at`
  * Add a simple table for embeddings, e.g. `book_embeddings`:

    * `book_id` (FK to book)
    * `vector` (BLOB or JSON)
    * `model_name`
    * `updated_at`

For the MVP, in-database storage is acceptable; no separate vector database is required.

### 5.2 Embedding Workflow (Summary-First)

* **Primary source for embeddings:**

  * Use the **AI-generated summary** as the main text input when building a book’s embedding.
  * If a book has no AI summary yet, fall back to concatenated metadata:

    * `title`, `author`, `description`, and `tags`.

* **Initial batch:**

  * Provide a simple admin-only CLI or management command, e.g.:

    * `python cps/ai/enqueue_embedding_backfill.py`
  * This command enqueues background jobs for each book that needs an embedding (using a simple worker system such as Celery, RQ, or a cron-driven queue processor).
  * Each worker job:

    1. Fetches the stored AI summary if available; otherwise builds a metadata string.
    2. Calls the configured embedding model (via LangChain) to generate a vector.
    3. Stores or updates the vector in the `book_embeddings` table.

* **Incremental updates:**

  * When a new summary is created or an existing one is refreshed:

    * Regenerate the book’s embedding by enqueuing a small background job after the summary is saved, **or**
    * Expose a simple admin action like “Regenerate embeddings” for that book that enqueues a job.
  * Optionally, add a bulk “Rebuild embeddings” CLI for admins when changing models (which again just queues jobs).

* **Usage:**

  * AI Search and “Similar books” both read from the same embedding store so behavior is consistent across features.

### 5.3 Integration Points

* **Search route/controller:**

  * Add conditional handling for AI search when `?ai=1` or via a separate endpoint.
  * Use the query embedding (via LangChain) to fetch results from `book_embeddings`.

* **Book detail view:**

  * Expose the “Generate AI summary” button and display area.
  * Allow admins (or background jobs) to pre-generate summaries for all books.
  * Fetch similar books using `ai.search.similar_to(book_id)` which reads from embeddings.
  * Show/hide AI sections based on configuration and data availability.

### 5.4 Configuration

Add configuration options (for example in `config.py` or the admin UI):

* `AI_ENABLED` (bool)
* `AI_PROVIDER` (string; used by LangChain; default points at a single provider/model combo but can be overridden in config).
* `AI_LANGCHAIN_LLM` (string; logical LLM name or model id used for summarization).
* `AI_LANGCHAIN_EMBEDDINGS` (string; logical embedding model name used for vectors).
* `AI_MAX_TOKENS_SUMMARY`
* Background worker config (e.g., Redis URL, queue name) if using Celery/RQ.
* API key or secret management (environment variables for the chosen provider; optionally surfaced read-only in the UI).

If `AI_ENABLED = False`, hide AI-related UI and avoid any network calls.

### 5.5 Configuration Specification

#### Configuration Options Table

| Option | Type | Default | Required | Validation Rules | Description |
|--------|------|---------|----------|------------------|-------------|
| `AI_ENABLED` | boolean | `false` | No | Must be `true` or `false` | Master toggle for all AI features. When `false`, all AI UI is hidden and no network calls are made. |
| `AI_PROVIDER` | string | `"openai"` | Yes (if `AI_ENABLED=true`) | Must be one of: `"openai"`, `"openrouter"`, `"anthropic"`, `"ollama"`, `"local"` | LangChain provider identifier. Determines which AI service to use. OpenRouter provides access to multiple models via OpenAI-compatible API. |
| `AI_LANGCHAIN_LLM` | string | `"gpt-4o-mini"` | Yes (if `AI_ENABLED=true`) | Non-empty string, valid model identifier for selected provider | LLM model name/ID for summarization. Must be a valid model for the configured provider. |
| `AI_LANGCHAIN_EMBEDDINGS` | string | `"text-embedding-3-small"` | Yes (if `AI_ENABLED=true`) | Non-empty string, valid embedding model identifier for selected provider | Embedding model name/ID for vector generation. Must be a valid embedding model for the configured provider. |
| `AI_MAX_TOKENS_SUMMARY` | integer | `500` | No | Must be between 100 and 2000 | Maximum tokens for summary generation. Lower values produce shorter summaries. |
| `AI_WORKER_QUEUE_URL` | string | `""` (empty) | Conditional | If provided, must be valid Redis URL or queue connection string | Background worker queue connection (e.g., Redis URL for Celery/RQ). Required if using background jobs. |
| `AI_WORKER_QUEUE_NAME` | string | `"calibre_ai_tasks"` | No | Non-empty string, alphanumeric and underscores only | Queue name for background tasks. Used if worker queue is configured. |
| `AI_API_KEY` | string | `""` (empty) | Yes (if `AI_ENABLED=true`) | Non-empty string when AI is enabled | API key for the configured AI provider. Stored securely in database, editable in admin UI. |
| `AI_TIMEOUT_SECONDS` | integer | `60` | No | Must be between 10 and 300 | Request timeout in seconds for AI API calls. Prevents hanging requests. |
| `AI_MAX_RETRIES` | integer | `3` | No | Must be between 0 and 10 | Maximum number of retry attempts for failed AI API calls. |

#### Configuration Storage

* **Primary Storage:** Admin UI configuration (stored in existing calibre-web config database)
  * All configuration options including API keys are stored in the database
  * API keys are stored securely in the database (encrypted/hashed if possible)
  * Configuration is editable via admin interface
* **Optional Override:** Environment variables (for non-sensitive settings only)
  * Can override database values for non-sensitive settings (e.g., `AI_ENABLED`)
  * API keys should NOT be set via environment variables (use database storage)
* **Fallback:** Default values (as specified in table above)

#### Configuration Validation Rules

1. **Dependency Validation:**
   * If `AI_ENABLED=false`, all other AI config options are ignored
   * If `AI_ENABLED=true`, `AI_PROVIDER`, `AI_LANGCHAIN_LLM`, `AI_LANGCHAIN_EMBEDDINGS`, and `AI_API_KEY` must be provided
   * If background jobs are used, `AI_WORKER_QUEUE_URL` must be provided

2. **Provider-Specific Validation:**
   * `AI_PROVIDER` must match a supported LangChain provider
   * `AI_LANGCHAIN_LLM` must be a valid model for the selected provider
   * `AI_LANGCHAIN_EMBEDDINGS` must be a valid embedding model for the selected provider
   * Validation should occur on configuration save/update

3. **Value Range Validation:**
   * Integer values must be within specified ranges
   * String values must match required patterns (e.g., queue name format)
   * Boolean values must be explicit `true`/`false` (not truthy/falsy)

4. **API Key Validation:**
   * Format validation based on provider (e.g., OpenAI keys start with `sk-`)
   * Basic format check on save (full validation requires API test call)
   * Optional: Test API key validity on configuration save (with user confirmation)

#### Configuration Change Impact

1. **Changing `AI_ENABLED`:**
   * `false` → `true`: Requires all required config to be set, triggers validation
   * `true` → `false`: Immediately hides all AI UI, stops all background jobs

2. **Changing `AI_PROVIDER` or Model Settings:**
   * Requires API key validation for new provider
   * Existing summaries and embeddings remain valid (cached)
   * New summaries/embeddings will use new model
   * **Recommendation:** Provide admin action to "Rebuild embeddings with new model" if model changes

3. **Changing `AI_LANGCHAIN_LLM` or `AI_LANGCHAIN_EMBEDDINGS`:**
   * Existing summaries remain valid (no regeneration required)
   * Existing embeddings remain valid but may not be optimal for new model
   * New summaries/embeddings use new model
   * **Recommendation:** Provide bulk "Regenerate embeddings" action when embedding model changes

4. **Changing Worker Configuration:**
   * Requires restart of background worker processes
   * In-flight jobs may be lost (graceful shutdown recommended)
   * Queue migration may be needed if queue URL changes

#### Admin UI Configuration Layout

**Location:** Admin interface → Configuration → AI Features section

**Layout:**
1. **Master Toggle:**
   * Large, prominent toggle: "Enable AI Features"
   * When disabled, all other options are grayed out/hidden

2. **Provider Settings:**
   * Dropdown: "AI Provider" (OpenAI, Anthropic, Ollama, Local)
   * Text input: "LLM Model" (with provider-specific suggestions/validation)
   * Text input: "Embedding Model" (with provider-specific suggestions/validation)
   * Password input: "API Key" (masked input, stored securely in database, with "Test Connection" button)

3. **Generation Settings:**
   * Number input: "Max Summary Tokens" (100-2000, with slider)
   * Number input: "Request Timeout (seconds)" (10-300)
   * Number input: "Max Retries" (0-10)

4. **Background Jobs (Optional):**
   * Toggle: "Use Background Jobs"
   * Text input: "Queue URL" (Redis URL format)
   * Text input: "Queue Name" (default: calibre_ai_tasks)
   * Info: "Background jobs allow non-blocking summary/embedding generation"

5. **Actions:**
   * Button: "Test Configuration" (validates all settings, tests API connection)
   * Button: "Save Configuration"
   * Button: "Rebuild Embeddings" (if model changed, with confirmation)

**Validation Feedback:**
* Real-time validation on input fields (red border + error message)
* Summary validation status at bottom of section
* "Test Configuration" button provides detailed validation results

---

## 6. Constraints & Assumptions

* Using **LangChain** as an abstraction over one configured provider/model by default; advanced setups can override models in configuration, but a full multi-provider UI is out of scope.
* Library size is moderate (for example up to a few tens of thousands of books), but the design should tolerate larger libraries by offloading work to background jobs.
* Network access is available from the server to the chosen AI provider.
* Latency of AI calls is acceptable for:

  * Summary (one-time per book; cached).
  * Search (one request per query).

---

## 7. Success Criteria (Week 1)

Qualitative prototype criteria:

1. **Summaries work end-to-end:**

   * For a sample of books, the button (or bulk admin action) generates and persists summaries.
2. **Embeddings are built from summaries:**

   * A background worker, driven by an admin command, can generate embeddings for books using summaries or metadata.
3. **Semantic search works end-to-end:**

   * AI Search returns relevant books for natural language queries using the embeddings.
4. **Similar books are rendered:**

   * At least 3–5 reasonable similar books shown for typical titles.
5. **Feature can be turned off:**

   * Toggling configuration reliably hides AI UI and avoids network calls.

---

## 8. Risks & Open Questions

### 8.1 Risks

* Cost of embedding large libraries with a hosted API.
* Latency for summary generation on slower networks.
* Schema changes may conflict with future upstream updates in calibre-web.
* Token limits if including actual book text beyond descriptions.
* Operational complexity of running background workers (queue, monitoring) for users who are not already running such infrastructure.

### 8.2 Open Questions

* How big can a typical library be before embedding generation becomes painful in practice?
  (To be validated with real libraries; background jobs help, but we may want guidance such as “if backfill takes more than N hours, consider limiting which books are embedded.”)
* What should the **default LangChain model choices** be for a typical self-hosted deployment (e.g., cost vs. quality trade-offs)?
* Do we need a lightweight UI for changing LangChain model/provider settings, or is config-file / environment-based configuration sufficient for the MVP?

---

## 9. Rough Timeline (1 Week)

**Day 1–2 – Summaries First**

* Explore the codebase to identify:

  * Book detail view/template.
  * Where to add summary UI elements and backend endpoints.
* Add database fields/tables needed to store **AI summaries** per book.
* Implement the LangChain LLM client/service and a minimal abstraction layer (e.g., `ai/summarization.py`).
* Wire up:

  * “Generate AI summary” button on the book detail page.
  * Backend endpoint that:

    * Calls the LLM via LangChain.
    * Persists the summary.
    * Returns it to the UI.
* Add basic error handling and a simple loading/error state in the UI.

**Day 3–4 – Background Jobs, Embeddings, Search, Similar Books**

* Set up a simple background worker stack (e.g., Celery/RQ + Redis or similar queue):

  * Define jobs for “generate summary” and “generate embedding for book X”.
* Add the **embeddings** table and service (e.g., `ai/embeddings.py`):

  * Fields: `book_id`, `vector`, `model_name`, `updated_at`.
* Implement the **embedding backfill** command:

  * For all books with a summary, enqueue embedding jobs.
  * For books without a summary, optionally enqueue summary jobs first and then embeddings.
* Implement the **semantic search** backend:

  * Endpoint that takes a query, gets its embedding via LangChain, and returns similar books.
* Integrate AI Search into the UI:

  * Toggle or tab on the search page to switch to AI results.
* Implement **“Similar books”**:

  * Backend function to get nearest neighbors for a book from `book_embeddings`.
  * UI block on the book detail page that renders those neighbors.

**Day 5 – Polish, Config, and Docs**

* Add configuration options and guards:

  * `AI_ENABLED`, LangChain model settings, provider API keys via environment variables.
  * Ensure AI features and UI are hidden when disabled.
* Tighten error handling:

  * Timeouts, missing API key, provider errors.
  * Graceful fallbacks (e.g., disable AI search if no embeddings available).
* Light smoke testing on a sample library:

  * Generate summaries and embeddings for a handful of books.
  * Verify AI Search and Similar Books behave sensibly.
  * Confirm that background jobs complete successfully.
* Write minimal documentation:

  * How to enable AI and configure LangChain models/provider.
  * How to run the embedding/summary backfill commands.
  * Any cost/performance caveats and recommended library sizes.
