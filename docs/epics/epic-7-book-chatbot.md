# Epic 7: Book Chatbot (RAG Q&A)

**Epic Goal:** Enable users to have conversational Q&A about book content using a chatbot interface powered by RAG (Retrieval-Augmented Generation).

**User Value Statement:** Users can ask natural language questions about a book and receive conversational answers based on the book's actual content, creating an interactive reading companion experience.

**PRD Coverage:** New feature (extension of AI capabilities)

**Technical Context:**
- RAG (Retrieval-Augmented Generation) architecture for conversational Q&A
- Builds on Epic 6 (Full Book Indexing) chunk search infrastructure
- Real-time chat interface on book detail page
- LLM-powered answer generation from retrieved book chunks
- Book-scoped conversations (chatbot only answers about the current book)

**Dependencies:** Epic 1 (Foundation), Epic 2 (AI Summary), Epic 6 (Full Book Indexing)

**Related Documents:**
- [Master Epic Index](../epics.md)
- [Epic 6: Full Book Indexing](epic-6-full-book-indexing.md)
- [Architecture Document](../architecture.md)

---

## Epic Overview

### Why a Book Chatbot?

Epic 6 enables **search** within book content, but users still need to:
- ❌ Manually review search results to find answers
- ❌ Piece together information from multiple chunks
- ❌ Interpret technical passages themselves

**Book Chatbot enables:**
- 💬 "What is the main character's motivation?"
- 💬 "Explain the time travel mechanics in this book"
- 💬 "What happens in chapter 5?"
- 💬 "Who is the antagonist and what do they want?"
- 💬 Natural conversation flow with context awareness

### Architecture: RAG Chatbot Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    BOOK CHATBOT FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Question ──► Retrieve Relevant Chunks ──► Build Context │
│     "Who is X?"      (vector search)              (top 3-5)     │
│                                                                 │
│  ──► Generate Answer with LLM ──► Return Response               │
│      (chunks + question)         (conversational)               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    CHAT INTERFACE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────┐               │
│  │ Chat History (scrollable)                    │               │
│  │ ┌─────────────────────────────────────────┐ │               │
│  │ │ User: What is the main theme?           │ │               │
│  │ │ Bot: Based on the book content...        │ │               │
│  │ └─────────────────────────────────────────┘ │               │
│  │ ┌─────────────────────────────────────────┐ │               │
│  │ │ User: Can you explain chapter 3?         │ │               │
│  │ │ Bot: Chapter 3 focuses on...             │ │               │
│  │ └─────────────────────────────────────────┘ │               │
│  └─────────────────────────────────────────────┘               │
│  ┌─────────────────────────────────────────────┐               │
│  │ [Type your question...]        [Send]        │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Comparison: Search vs Chatbot

| Feature | Chunk Search (Epic 6) | Book Chatbot (Epic 7) |
|---------|----------------------|----------------------|
| **Interaction** | Search → Results list | Question → Answer |
| **Output** | Relevant passages | Conversational response |
| **Context** | User interprets results | LLM synthesizes answer |
| **Use Case** | Find specific passages | Understand concepts |
| **UI** | Search results page | Chat interface |
| **Dependencies** | Epic 6 chunks | Epic 6 chunks + LLM |

---

## Story 7.1: RAG Chatbot Service

As a developer,
I want a RAG chatbot service that generates conversational answers from book chunks,
So that users can ask questions and get natural language responses.

**Acceptance Criteria:**

**Given** a user question and a book_id
**When** I call `ai.chatbot.ask_question(book_id, question, conversation_history=None)`
**Then** the service:

1. Validates prerequisites:
   - Checks `config.config_ai_enabled` - returns error if disabled
   - Checks `config.config_ai_chatbot_enabled` - returns error if disabled
   - Validates book_id exists and has indexed chunks
   - Returns error if book is not indexed

2. Retrieves relevant chunks:
   - Calls `ai.chunk_search.search_chunks(query=question, book_id=book_id, limit=5)`
   - Filters chunks by similarity threshold (default: 0.5)
   - Selects top 3-5 most relevant chunks for context

3. Constructs RAG prompt:
   - System prompt: "You are a helpful assistant answering questions about a specific book. Use only the provided book excerpts to answer. If the answer is not in the excerpts, say so."
   - Book context: Includes book title, author, and metadata
   - Relevant chunks: Includes top chunks with chapter titles (if available)
   - User question: The actual question
   - Optional conversation history: Previous Q&A pairs for context

4. Generates answer with LLM:
   - Uses `config.config_ai_provider` and `config.config_ai_llm_model`
   - Uses `config.config_ai_api_key` for authentication
   - Sets `config.config_ai_max_tokens_chatbot` for response limit (default: 500)
   - Uses `config.config_ai_timeout_seconds` for timeout
   - Uses `config.config_ai_max_retries` for retry logic

5. Returns structured response:
   ```python
   {
       'answer': str,  # The generated answer
       'chunks_used': List[Dict],  # Chunks that informed the answer
       'confidence': float,  # Optional: confidence score (0-1)
       'error': Optional[str]  # Error message if failed
   }
   ```

**And** error handling:
- Book not indexed: Returns `{'error': 'Book is not indexed. Please index the book first.'}`
- No relevant chunks found: Returns `{'error': 'No relevant content found for this question.'}`
- LLM timeout: Logs and returns error message
- API errors: Logs and returns error message
- Graceful degradation: Returns error without crashing

**And** conversation context:
- Optional `conversation_history` parameter: List of previous `{'question': str, 'answer': str}` pairs
- Includes last 3-5 exchanges in prompt for context awareness
- Helps with follow-up questions and references

**Technical Notes:**
- Create `cps/ai/chatbot.py` (Architecture section 4.1)
- Reuse `ai.chunk_search.search_chunks()` from Epic 6
- Use LangChain for LLM orchestration (Architecture section 4.1)
- Follow existing service patterns (see `cps/ai/summarization.py`)
- Check `AI_ENABLED` and `AI_CHATBOT_ENABLED` before operations

**Prerequisites:** Story 6.5 (Chunk Search Service), Story 2.1 (LLM Integration patterns)

---

## Story 7.2: Chatbot API Endpoints

As a developer,
I want API endpoints for chatbot interactions,
So that the UI can send questions and receive answers.

**Acceptance Criteria:**

**AC1:** `POST /api/ai/chatbot/<int:book_id>/ask` - Ask a question
- Request body: `{'question': 'user question', 'conversation_history': optional list}`
- Requires authentication (`@login_required_if_no_ano`)
- Returns JSON: `{'answer': str, 'chunks_used': list, 'error': optional}`
- Validates book_id exists and is indexed
- Returns 400 if question is empty
- Returns 403 if chatbot is disabled
- Returns 404 if book not found
- Returns 400 if book not indexed

**AC2:** `GET /api/ai/chatbot/<int:book_id>/status` - Check chatbot availability
- Returns JSON: `{'available': bool, 'book_indexed': bool, 'reason': optional str}`
- Checks if book is indexed (required for chatbot)
- Checks if chatbot feature is enabled
- Useful for UI to show/hide chatbot interface

**AC3:** `POST /api/ai/chatbot/<int:book_id>/clear` - Clear conversation history (optional)
- Clears any stored conversation history for the book
- Returns `{'status': 'cleared'}`
- Useful for starting fresh conversations

**And** route implementation:
- File: Extend `cps/ai/__init__.py` blueprint
- Routes: `@ai.route("/api/ai/chatbot/<int:book_id>/ask", methods=['POST'])`
- Decorator: `@login_required_if_no_ano` (from `cps.usermanagement`)
- Function: `ask_book_question(book_id)`
- Function: `get_chatbot_status(book_id)`
- Function: `clear_chatbot_history(book_id)` (optional)

**And** error handling:
- AI disabled: Return `{'error': 'AI features disabled'}, 403`
- Chatbot disabled: Return `{'error': 'Chatbot feature disabled'}, 403`
- Book not found: Return `{'error': 'Book not found'}, 404`
- Book not indexed: Return `{'error': 'Book is not indexed'}, 400`
- Empty question: Return `{'error': 'Question is required'}, 400`
- LLM errors: Return `{'error': 'Failed to generate answer'}, 500`

**Technical Notes:**
- Add routes to `cps/ai/__init__.py` blueprint
- Use `@exempt_from_csrf` decorator (follows existing pattern)
- Reuse `ai.chatbot.ask_question()` from Story 7.1
- Follow existing API patterns (see `cps/ai/__init__.py`)

**Prerequisites:** Story 7.1 (RAG Chatbot Service)

---

## Story 7.3: Chatbot UI Integration

As a user,
I want a chatbot interface on the book detail page,
So that I can ask questions about the book and see answers in a conversational format.

**Acceptance Criteria:**

**AC1:** Book detail page shows chatbot interface:
- **Location:** New section after "Deep Search Indexing" section (or after AI Summary if indexing not available)
- **Visibility:** Only shown when:
  - `config.config_ai_enabled` is True
  - `config.config_ai_chatbot_enabled` is True
  - Book is indexed (has chunks in `book_chunks` table)
- **Layout:** Collapsible panel with Bootstrap `panel panel-default`
- **Title:** "Ask Questions About This Book" or "Book Chatbot"

**AC2:** Chatbot interface components:
- **Chat history area:**
  - Scrollable container (max-height: 400px)
  - Shows message bubbles (user questions on right, bot answers on left)
  - Bootstrap styling: `list-group` for messages
  - User messages: `list-group-item list-group-item-info` (blue)
  - Bot messages: `list-group-item` (white/gray)
  - Timestamps (optional, small text)
  - Auto-scrolls to bottom on new messages

- **Input area:**
  - Text input field: `form-control` with placeholder "Ask a question about this book..."
  - Send button: `btn btn-primary` with glyphicon `glyphicon-send`
  - Disabled state when processing or book not indexed
  - Enter key submits question

- **Loading state:**
  - Shows spinner (`glyphicon-refresh glyphicon-spin`) while processing
  - Disables input and send button during processing
  - Shows "Thinking..." message in chat history

- **Error state:**
  - Shows error message in chat history (red styling)
  - Allows retry
  - Shows helpful messages (e.g., "Book not indexed. Please index first.")

**AC3:** JavaScript functionality:
- **File:** `cps/static/js/ai/chatbot.js`
- **Functions:**
  - `sendQuestion(bookId, question)` - Sends question to API, displays answer
  - `displayMessage(role, text, timestamp)` - Adds message to chat history
  - `clearChat()` - Clears chat history (optional)
  - `checkChatbotAvailability(bookId)` - Checks if chatbot is available
  - `handleEnterKey(event)` - Submits on Enter key
- **API calls:**
  - `POST /api/ai/chatbot/<book_id>/ask` for questions
  - `GET /api/ai/chatbot/<book_id>/status` for availability check
- **Error handling:**
  - Network errors: Show user-friendly message
  - API errors: Display error from response
  - Timeout: Show timeout message with retry option

**AC4:** Initial state and empty state:
- **When book not indexed:** Shows message: "This book is not indexed. Please index it first to use the chatbot." with link to indexing section
- **When chatbot disabled:** Section is hidden (not rendered)
- **When first opened:** Shows welcome message: "Ask me anything about this book! I can answer questions about characters, plot, themes, and more."

**AC5:** Responsive design:
- Chat interface adapts to mobile screens
- Input area stacks vertically on small screens
- Chat history scrolls properly on all screen sizes

**Technical Notes:**
- Extend `cps/templates/detail.html` with chatbot section
- Include `chatbot.js` when AI features and chatbot are enabled
- Use Bootstrap components for styling (follows UX patterns)
- Follow existing JavaScript patterns (see `cps/static/js/ai/summary.js`)
- Pass `book_id` and `chatbot_available` to template from `cps/web.py`

**Prerequisites:** Story 7.2 (Chatbot API Endpoints)

---

## Story 7.4: Chat History Persistence (Optional)

As a user,
I want my chat history to persist across page reloads,
So that I can continue conversations and reference previous answers.

**Acceptance Criteria:**

**Given** I have asked questions in the chatbot
**When** I reload the book detail page
**Then** my previous conversation is restored:
- Chat history is loaded from storage
- Messages appear in chronological order
- Conversation context is maintained for follow-up questions

**And** storage options:
- **Option 1:** Browser localStorage (client-side, per-book)
  - Key: `chatbot_history_<book_id>`
  - Stores: JSON array of `{'question': str, 'answer': str, 'timestamp': str}`
  - Cleared when user clicks "Clear Chat" or manually
- **Option 2:** Server-side storage (database)
  - New table: `book_chat_history` (optional)
  - Columns: `id`, `book_id`, `user_id`, `question`, `answer`, `created_at`
  - Per-user, per-book conversation history
  - Admin can configure retention period

**And** implementation:
- JavaScript: Load from localStorage on page load
- JavaScript: Save to localStorage after each exchange
- Optional: API endpoint to fetch/save history from server
- Optional: Database migration for `book_chat_history` table

**Technical Notes:**
- This story is **optional** - MVP can work without persistence
- If implemented, prefer localStorage for simplicity (no database changes)
- Server-side storage requires new table and API endpoints
- Consider privacy: chat history may contain sensitive questions

**Prerequisites:** Story 7.3 (Chatbot UI Integration)

---

## Configuration Options

New configuration options for Epic 7:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `config_ai_chatbot_enabled` | Boolean | False | Master toggle for chatbot feature |
| `config_ai_max_tokens_chatbot` | Integer | 500 | Maximum tokens in chatbot response |
| `config_ai_chatbot_chunks_limit` | Integer | 5 | Number of chunks to retrieve for context |
| `config_ai_chatbot_similarity_threshold` | Float | 0.5 | Minimum similarity score for chunks (0-1) |
| `config_ai_chatbot_history_limit` | Integer | 5 | Number of previous exchanges to include in context |

---

## Technical Considerations

### RAG Prompt Structure

Example prompt template:
```
You are a helpful assistant answering questions about a specific book.

Book Information:
- Title: {book_title}
- Author: {book_author}

Relevant Book Excerpts:
{chunk_1_text}
[Chapter: {chunk_1_chapter}]

{chunk_2_text}
[Chapter: {chunk_2_chapter}]

...

Previous Conversation:
{conversation_history}

User Question: {question}

Instructions:
- Answer based ONLY on the provided book excerpts
- If the answer is not in the excerpts, say "I don't have enough information from the book to answer that question."
- Be conversational and helpful
- Cite chapter names when relevant
```

### Performance Considerations

1. **Response time:** Target <5 seconds for answer generation
   - Chunk retrieval: <500ms (vector search)
   - LLM call: 2-4 seconds (depends on provider)
   - Total: ~3-5 seconds

2. **Token usage:**
   - Input: ~1000-2000 tokens (chunks + prompt + history)
   - Output: ~100-500 tokens (answer)
   - Cost: ~$0.001-0.005 per question (OpenAI GPT-4)

3. **Caching:** (Optional future enhancement)
   - Cache common questions/answers
   - Reduce API calls for repeated questions

4. **Rate limiting:** (Optional)
   - Limit questions per user per book per hour
   - Prevent abuse of LLM API

### Error Handling

- **Book not indexed:** Clear error message with link to index
- **No relevant chunks:** "I couldn't find relevant information in the book for that question."
- **LLM timeout:** "The answer is taking too long. Please try again or rephrase your question."
- **API errors:** "I'm having trouble generating an answer. Please try again later."

---

## Implementation Sequence

**Recommended Story Order:**
1. Story 7.1 (RAG Chatbot Service) - Core logic
2. Story 7.2 (Chatbot API Endpoints) - Integration layer
3. Story 7.3 (Chatbot UI Integration) - User-facing
4. Story 7.4 (Chat History Persistence) - Optional enhancement

**Dependencies:**
- Epic 6 must be completed (chunk search infrastructure)
- Book must be indexed before chatbot can work
- LLM provider must be configured (Epic 1)

**Parallel Work:**
- Story 7.1 can be developed independently
- Stories 7.2 and 7.3 are sequential
- Story 7.4 can be added later as enhancement

---

## Success Metrics

- [ ] Users can ask questions about indexed books
- [ ] Chatbot returns relevant, accurate answers
- [ ] Response time is <5 seconds
- [ ] UI is intuitive and responsive
- [ ] Error handling is clear and helpful
- [ ] Chatbot only answers about the current book
- [ ] Conversation context works for follow-up questions
- [ ] No impact on existing features (Epic 6 search, etc.)

---

## User Experience Flow

1. **User opens book detail page**
   - Sees chatbot section (if book is indexed and chatbot enabled)
   - Sees welcome message or previous chat history

2. **User asks a question**
   - Types question in input field
   - Clicks "Send" or presses Enter
   - Sees "Thinking..." message

3. **System processes question**
   - Retrieves relevant chunks (vector search)
   - Generates answer with LLM (RAG)
   - Returns answer to UI

4. **User sees answer**
   - Answer appears in chat history
   - Can ask follow-up questions
   - Can clear chat to start fresh

5. **Error scenarios**
   - Book not indexed: Clear message with link to index
   - No relevant content: Helpful message
   - API error: Error message with retry option

---

_Return to [Master Epic Index](../epics.md)_

