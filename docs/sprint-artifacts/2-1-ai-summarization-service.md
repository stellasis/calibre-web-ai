# Story 2.1: AI Summarization Service

**Status:** done  
**Epic:** Epic 2 - AI Summary Feature  
**Story ID:** 2.1  
**Created:** 2025-12-04

---

## Story

As a developer,  
I want an AI summarization service that generates book summaries,  
So that summaries can be created and stored for books.

---

## Acceptance Criteria

**Given** a book with extracted text (from Story 1.4)  
**When** I call `ai.summarization.generate_summary(book_id)`  
**Then** the service:

1. Checks `config.config_ai_enabled` - returns error if disabled
2. Fetches book metadata and extracted text (via `ai.text_extraction.extract_text()`)
3. Constructs prompt for LLM:
   - Includes book metadata (title, author, description)
   - Includes extracted text (up to token limit)
   - Prompt focuses on: what the book is about, who it's for, key themes/topics
4. Calls LangChain LLM with configured provider/model:
   - Uses `config.config_ai_provider` to select provider
   - Uses `config.config_ai_llm_model` for model selection
   - Uses `config.config_ai_api_key` for authentication
   - Uses `config.config_ai_max_tokens_summary` for output limit
   - Uses `config.config_ai_timeout_seconds` for timeout
   - Uses `config.config_ai_max_retries` for retry logic
5. Generates concise summary (3-7 sentences or bullet points)
6. Stores summary in `book_summaries` table:
   - `book_id` = provided book_id
   - `summary_text` = generated summary
   - `model_name` = LLM model used
   - `created_at` / `updated_at` = current timestamp
7. Returns summary text

**And** error handling:
- Timeout errors: Log and return error message
- API key errors: Log and return error message
- Provider errors: Log and return error message
- Missing book: Return error message
- Graceful degradation: Return error without crashing

---

## Tasks / Subtasks

- [ ] Task 1: Create summarization service module (AC: #1-7)
  - [ ] Create `cps/ai/__init__.py` if it doesn't exist
  - [ ] Create `cps/ai/summarization.py` module
  - [ ] Import LangChain dependencies
  - [ ] Implement `generate_summary(book_id)` function
  - [ ] Add configuration check (`config.config_ai_enabled`)
  - [ ] Integrate with `ai.text_extraction.extract_text()`
  - [ ] Construct LLM prompt with metadata and extracted text
  - [ ] Implement LangChain LLM call with provider/model selection
  - [ ] Add timeout and retry logic
  - [ ] Store summary in `book_summaries` table
  - [ ] Return summary text

- [ ] Task 2: Implement error handling (AC: error handling)
  - [ ] Handle timeout errors with logging
  - [ ] Handle API key errors with logging
  - [ ] Handle provider errors with logging
  - [ ] Handle missing book errors
  - [ ] Ensure graceful degradation (no crashes)

- [ ] Task 3: Test integration (AC: all)
  - [ ] Test with AI enabled
  - [ ] Test with AI disabled
  - [ ] Test with missing book
  - [ ] Test with various error conditions
  - [ ] Verify summary stored in database

---

## Dev Notes

### Architecture Compliance

**Service Layer Pattern:** [Source: docs/architecture.md#4.1, docs/epics/epic-2-summary.md#Technical-Context]
- Create `cps/ai/summarization.py` following existing service patterns
- Follow existing service patterns (see `cps/services/Metadata.py`)
- Separate business logic from routes

**Database Integration:** [Source: docs/architecture.md#3.1, docs/epic-1-context.md#Database-Architecture]
- Store summaries in `app_settings.book_summaries` table
- Use `BookSummary` model from `cps/ub.py` (created in Story 1.1)
- Use `ub.session` for database access (app_settings schema)

**Configuration Access:** [Source: docs/architecture.md#3.5, docs/epic-1-context.md#Configuration-Management]
- Check `config.config_ai_enabled` before any AI operations
- Access configuration via `cps.config_sql.py` patterns
- Use `config.config_ai_provider`, `config.config_ai_llm_model`, etc.

**LangChain Integration:** [Source: docs/architecture.md#4.1, docs/prd.md#3]
- Use LangChain for LLM orchestration
- Support multiple providers (OpenAI, OpenRouter, Anthropic, Ollama)
- Provider selection via `config.config_ai_provider`
- Model selection via `config.config_ai_llm_model`
- OpenRouter: Uses OpenAI-compatible API, supports models from multiple providers (format: "openai/gpt-4o", "anthropic/claude-3-sonnet", etc.)

**Text Extraction Integration:** [Source: docs/epics/epic-2-summary.md#Prerequisites]
- Use `ai.text_extraction.extract_text(book_id)` from Story 1.4
- Function already implemented in `cps/ai/text_extraction.py`
- Returns metadata + extracted text (up to token limit)

### Technical Implementation Details

**LangChain Setup:**
- Install LangChain: `pip install langchain langchain-openai langchain-anthropic langchain-community`
- For OpenAI: Use `ChatOpenAI` from `langchain_openai`
- For OpenRouter: Use `ChatOpenAI` from `langchain_openai` with `base_url="https://openrouter.ai/api/v1"` (OpenAI-compatible API)
- For Anthropic: Use `ChatAnthropic` from `langchain_anthropic`
- For Ollama: Use `ChatOllama` from `langchain_community`
- Provider selection: Use factory pattern based on `config.config_ai_provider`

**Prompt Construction:**
- Include book metadata (title, author, description, tags)
- Include extracted text (already truncated to token limit by text extraction)
- Focus prompt on: what the book is about, who it's for, key themes/topics
- Example prompt structure:
  ```
  Generate a concise summary (3-7 sentences) of the following book:
  
  Title: {title}
  Author: {author}
  Description: {description}
  Tags: {tags}
  
  Content excerpt:
  {extracted_text}
  
  Focus on: what the book is about, who it's for, and key themes/topics.
  ```

**Database Storage:**
- Use `BookSummary` model from `cps/ub.py`
- Create new record or update existing (if regenerating)
- Set `book_id`, `summary_text`, `model_name`
- Timestamps handled automatically by model

**Error Handling Pattern:**
- Return error messages (strings) instead of raising exceptions
- Log errors using `logger.create()` pattern
- Graceful degradation: return empty string or error message, don't crash

### File Structure

```
cps/
  ai/
    __init__.py          # Package init (create if needed)
    summarization.py     # NEW: Summarization service
    text_extraction.py   # EXISTS: Text extraction (Story 1.4)
```

### Dependencies

**Required Packages:**
- `langchain` - Core LangChain library
- `langchain-openai` - OpenAI integration
- `langchain-anthropic` - Anthropic integration (optional)
- `langchain-community` - Community integrations (Ollama, etc.)

**Existing Dependencies (already in project):**
- `cps.ub` - Database models (BookSummary)
- `cps.config` - Configuration access
- `cps.db` - Database access
- `cps.logger` - Logging
- `cps.ai.text_extraction` - Text extraction service

### Testing Considerations

- Test with AI enabled/disabled
- Test with various providers (OpenAI, Anthropic, Ollama)
- Test with missing/invalid API keys
- Test with timeout scenarios
- Test with missing books
- Verify summary quality and format
- Verify database storage

### References

- [Source: docs/architecture.md#4.1] - Service layer patterns
- [Source: docs/architecture.md#3.1] - Database schema
- [Source: docs/architecture.md#3.5] - Configuration management
- [Source: docs/epics/epic-2-summary.md#Story-2.1] - Story requirements
- [Source: docs/epic-1-context.md] - Technical context
- [Source: cps/services/Metadata.py] - Service pattern example
- [Source: cps/ai/text_extraction.py] - Text extraction integration

---

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Auto (Cursor AI)

### Debug Log References

### Completion Notes List

### File List

- `cps/ai/summarization.py` - Summarization service implementation
- `cps/config_sql.py` - AI configuration added (if missing from Story 1.3)
- `cps/ub.py` - BookSummary and BookEmbedding models added (if missing from Story 1.1)

### Completion Notes List

- ✅ Created `cps/ai/summarization.py` with full LangChain integration
- ✅ Implemented provider selection (OpenAI, OpenRouter, Anthropic, Ollama)
- ✅ Added OpenRouter support (uses OpenAI-compatible API with base_url)
- ✅ Added error handling for all error types
- ✅ Integrated with text extraction service
- ✅ Database storage with BookSummary model
- ✅ Fixed: max_tokens parameter now properly applied to LLM calls
- ✅ Fixed: Config decryption logic improved to support both _e and non-_e fields
