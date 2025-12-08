# AI Integration Guide

This guide explains how to enable and configure AI features in Calibre-Web. All AI features are optional and can be fully configured through the admin interface.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Basic AI Setup](#basic-ai-setup)
  - [Supported AI Providers](#supported-ai-providers)
  - [Full Book Indexing](#full-book-indexing)
  - [Book Chatbot](#book-chatbot)
- [AI Features Overview](#ai-features-overview)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Cost Considerations](#cost-considerations)

---

## Prerequisites

Before enabling AI features, ensure you have:

1. **Calibre-Web installed and running** - The base application must be working correctly
2. **Admin access** - You need administrator privileges to configure AI settings
3. **API key** (for cloud providers) - From OpenAI, Anthropic, or another supported provider
4. **Python 3.8+** - Required for LangChain dependencies

---

## Quick Start

### 1. Install AI Dependencies

```bash
# Install LangChain and provider packages
pip install langchain langchain-openai langchain-anthropic langchain-community
```

### 2. Configure in Admin Panel

1. Log in as admin
2. Navigate to **Admin → AI Settings**
3. Check **"Enable AI Features"**
4. Select your **AI Provider** (e.g., OpenAI)
5. Enter your **API Key**
6. Click **Save**

### 3. Test Configuration

Click the **"Test Configuration"** button to verify your API key and settings work correctly.

---

## Installation

### Required Python Packages

Install the LangChain framework and provider-specific packages:

```bash
# Core LangChain packages (required)
pip install langchain langchain-core

# For OpenAI (GPT-4, GPT-4o-mini, embeddings)
pip install langchain-openai

# For Anthropic (Claude models)
pip install langchain-anthropic

# For Ollama (local models) and other community integrations
pip install langchain-community
```

#### Provider-Specific Installation

| Provider | Required Package | Install Command |
|----------|------------------|-----------------|
| OpenAI | `langchain-openai` | `pip install langchain-openai` |
| Anthropic | `langchain-anthropic` | `pip install langchain-anthropic` |
| Ollama | `langchain-community` | `pip install langchain-community` |
| OpenRouter | `langchain-openai` | `pip install langchain-openai` |

#### All Packages (Recommended)

For full flexibility, install all AI packages:

```bash
pip install langchain langchain-core langchain-openai langchain-anthropic langchain-community
```

---

## Configuration

### Basic AI Setup

1. **Access AI Settings**
   - Log in as administrator
   - Go to **Admin** (top navigation)
   - Click **"AI Settings"**

2. **Enable AI Features**
   - Check the **"Enable AI Features"** checkbox
   - This is the master toggle for all AI functionality

3. **Select Provider**
   - Choose from: **OpenAI**, **Anthropic**, or **Ollama**
   - OpenAI is the default and recommended provider

4. **Configure Models**
   - **LLM Model**: For text generation (summaries, chatbot responses)
   - **Embedding Model**: For vector embeddings (search, similarity)

5. **Enter API Key**
   - Paste your provider's API key
   - Keys are stored securely (encrypted) in the database
   - Leave blank when editing to keep the existing key

6. **Save and Test**
   - Click **Save** to apply settings
   - Click **Test Configuration** to verify the connection

---

### Supported AI Providers

#### OpenAI (Recommended)

- **Best for**: Most users, reliable performance, good cost/quality balance
- **Get API Key**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

| Setting | Recommended Value |
|---------|-------------------|
| LLM Model | `gpt-4o-mini` |
| Embedding Model | `text-embedding-3-small` |

```
API Key Format: sk-xxxxxxxxxxxxxxxxxxxxxx
```

#### Anthropic

- **Best for**: Users preferring Claude models
- **Get API Key**: [console.anthropic.com](https://console.anthropic.com/)

| Setting | Recommended Value |
|---------|-------------------|
| LLM Model | `claude-3-haiku-20240307` |
| Embedding Model | (Use with OpenAI embeddings) |

> **Note**: Anthropic doesn't offer embedding models. Consider using OpenAI for embeddings with Claude for text generation.

#### Ollama (Self-Hosted)

- **Best for**: Privacy-conscious users, offline usage, no API costs
- **Setup**: Install [Ollama](https://ollama.ai/) locally

| Setting | Recommended Value |
|---------|-------------------|
| LLM Model | `llama3.2` or `mistral` |
| Embedding Model | `nomic-embed-text` |

**Environment variable** (optional):
```bash
export OLLAMA_BASE_URL=http://localhost:11434
```

#### OpenRouter

- **Best for**: Access to multiple models through one API
- **Get API Key**: [openrouter.ai](https://openrouter.ai/)

OpenRouter uses OpenAI-compatible API format. Set provider to **OpenAI** and configure:
- Base URL will be automatically set for OpenRouter models

---

### Full Book Indexing

Full book indexing enables deep search within book content by:
- Splitting books into semantic chunks (~500 tokens each)
- Generating embeddings for each chunk
- Enabling passage-level search and chatbot features

#### Enabling Full Book Indexing

1. In **AI Settings**, scroll to **"Full Book Indexing"** section
2. Check **"Enable Full Book Indexing"**
3. Configure chunk settings (defaults work well for most libraries)
4. Save settings

#### Indexing Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Chunk Size (tokens) | 500 | Target size for each text chunk |
| Chunk Overlap (tokens) | 50 | Overlap between chunks for context |
| Max Chunks per Book | 5000 | Safety limit for very large books |
| Embedding Batch Size | 25 | Chunks processed per API call |
| Auto-Index on Summary | Off | Automatically index when generating summaries |

#### Indexing a Book

1. Open a book's detail page
2. Click **"Index Book"** button
3. Wait for indexing to complete (progress shown in task queue)
4. Once indexed, deep search and chatbot features are available

#### Bulk Indexing

Administrators can index multiple books:
- **Admin → Tasks → Index All Books**: Queue all unindexed books
- Progress visible in the task queue

---

### Book Chatbot

The chatbot uses RAG (Retrieval-Augmented Generation) to answer questions about book content.

#### Requirements

- AI features must be enabled
- Full book indexing must be enabled
- The specific book must be indexed

#### Enabling the Chatbot

1. In **AI Settings**, scroll to **"Book Chatbot"** section
2. Check **"Enable Book Chatbot"**
3. Configure chatbot settings
4. Save

#### Chatbot Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Max Chatbot Tokens | 500 | Maximum response length |
| Chunks Limit | 5 | Number of relevant passages to use |
| Similarity Threshold | 0.3 | Minimum relevance score (lower = more results) |
| Chat History Limit | 5 | Previous exchanges to include for context |

#### Using the Chatbot

1. Navigate to an indexed book's detail page
2. Click the **"Ask AI"** or **"Chat"** button
3. Type your question about the book
4. View AI-generated answer with source references

---

## AI Features Overview

### Feature Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                  AI Enabled (Master Toggle)             │
├─────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐                  │
│  │ AI Summaries  │  │ AI Search     │                  │
│  │ (Standalone)  │  │ (Uses embeds) │                  │
│  └───────────────┘  └───────────────┘                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Full Book Indexing                     │   │
│  │  ┌─────────────────────────────────────────┐    │   │
│  │  │            Book Chatbot                  │    │   │
│  │  │     (Requires Full Book Indexing)        │    │   │
│  │  └─────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Feature Summary

| Feature | Requires | Description |
|---------|----------|-------------|
| **AI Summaries** | AI Enabled | Generate book summaries from metadata/content |
| **AI Search** | AI Enabled | Semantic search using embeddings |
| **Full Book Indexing** | AI Enabled | Index full book text for deep search |
| **Book Chatbot** | AI Enabled + Full Indexing | Q&A about book content |

---

## Configuration Reference

### All Configuration Options

| Setting | Type | Default | Range | Description |
|---------|------|---------|-------|-------------|
| `AI Enabled` | Boolean | `false` | - | Master toggle for all AI features |
| `AI Provider` | String | `openai` | openai, anthropic, ollama | AI service provider |
| `LLM Model` | String | `gpt-4o-mini` | - | Model for text generation |
| `Embedding Model` | String | `text-embedding-3-small` | - | Model for embeddings |
| `API Key` | String | - | - | Provider API key (encrypted) |
| `Max Summary Tokens` | Integer | `500` | 100-2000 | Summary length limit |
| `Request Timeout` | Integer | `60` | 10-300 | API timeout in seconds |
| `Max Retries` | Integer | `3` | 0-10 | Retry attempts on failure |
| `Full Index Enabled` | Boolean | `false` | - | Enable full book indexing |
| `Chunk Size` | Integer | `500` | 100-2000 | Tokens per chunk |
| `Chunk Overlap` | Integer | `50` | 0-200 | Overlap between chunks |
| `Max Chunks/Book` | Integer | `5000` | 100-50000 | Safety limit |
| `Batch Size` | Integer | `25` | 1-100 | Chunks per API call |
| `Auto-Index on Summary` | Boolean | `false` | - | Auto-index after summary |
| `Chatbot Enabled` | Boolean | `false` | - | Enable chatbot feature |
| `Chatbot Max Tokens` | Integer | `500` | 100-2000 | Chatbot response limit |
| `Chatbot Chunks Limit` | Integer | `5` | 1-20 | Context chunks |
| `Similarity Threshold` | Float | `0.3` | 0.0-1.0 | Minimum relevance |
| `Chat History Limit` | Integer | `5` | 0-20 | Previous exchanges |

---

## Troubleshooting

### Common Issues

#### "LangChain not installed"

**Solution**: Install the required packages:
```bash
pip install langchain langchain-openai langchain-anthropic langchain-community
```

#### "API key not configured or invalid"

**Causes**:
- API key not entered in settings
- API key format incorrect
- API key expired or invalid

**Solutions**:
1. Go to **Admin → AI Settings**
2. Enter a valid API key
3. Click **Test Configuration** to verify
4. For OpenAI, keys should start with `sk-`

#### "AI features disabled"

**Solution**: Enable AI in settings:
1. Go to **Admin → AI Settings**
2. Check **"Enable AI Features"**
3. Configure provider and API key
4. Save settings

#### Chatbot says "Book is not indexed"

**Solution**: Index the book first:
1. Go to the book's detail page
2. Click **"Index Book"**
3. Wait for indexing to complete
4. Try the chatbot again

#### Slow Performance / Timeouts

**Solutions**:
1. Increase **Request Timeout** in AI Settings (up to 300 seconds)
2. For Ollama, ensure the model is loaded (`ollama pull <model>`)
3. Reduce **Chunk Size** or **Batch Size** for indexing
4. Use faster models (e.g., `gpt-4o-mini` instead of `gpt-4`)

#### Empty or Poor Quality Summaries

**Solutions**:
1. Ensure the book has extractable text content (not image-only PDFs)
2. Increase **Max Summary Tokens** for longer summaries
3. Try a different LLM model

### Checking Logs

View detailed error messages in the Calibre-Web logs:
- Default location: `calibre-web.log` in the application directory
- Look for entries with `[AI]` or `LangChain` keywords

---

## Cost Considerations

### OpenAI Pricing (as of 2024)

| Model | Type | Cost |
|-------|------|------|
| `gpt-4o-mini` | LLM | ~$0.15/1M input, $0.60/1M output |
| `text-embedding-3-small` | Embedding | ~$0.02/1M tokens |

### Estimated Costs

| Operation | Approximate Cost |
|-----------|------------------|
| Generate 1 summary | $0.001 - $0.01 |
| Index 1 book (300 pages) | $0.01 - $0.05 |
| 1 chatbot question | $0.001 - $0.005 |
| Index 100 books | $1 - $5 |

### Cost Optimization Tips

1. **Use efficient models**: `gpt-4o-mini` is 10-20x cheaper than `gpt-4`
2. **Index selectively**: Only index books you'll search/chat with
3. **Disable auto-indexing**: Manual indexing gives you control
4. **Self-host with Ollama**: Zero API costs after hardware investment
5. **Cache summaries**: Summaries are stored, avoiding regeneration costs

---

## API Endpoints (For Developers)

AI features expose REST API endpoints for programmatic access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/summary/<book_id>` | POST | Generate summary |
| `/api/ai/summary/<book_id>/status` | GET | Check summary status |
| `/api/ai/index/<book_id>` | POST | Start book indexing |
| `/api/ai/index/<book_id>/status` | GET | Get indexing progress |
| `/api/ai/index/search` | POST | Search indexed content |
| `/api/ai/chatbot/<book_id>/ask` | POST | Ask chatbot question |
| `/api/ai/chatbot/<book_id>/status` | GET | Check chatbot availability |

---

## Security Notes

1. **API keys are encrypted** in the database - never stored in plain text
2. **API keys are never exposed** in the UI after saving
3. **Use environment variables** for additional security in production:
   - API keys should only be stored in the database (not environment variables)
4. **HTTPS recommended** for production deployments
5. **Admin-only access** - Only administrators can configure AI settings

---

## Support

- **Issues**: Report bugs on the project's issue tracker
- **Documentation**: See the project wiki for additional guides
- **Community**: Join the Discord server for help

---

*Last updated: December 2024*

