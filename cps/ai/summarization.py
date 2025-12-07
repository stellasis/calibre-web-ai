# -*- coding: utf-8 -*-

"""
AI Summarization Service
Generates book summaries using LangChain LLM integration.
"""

from datetime import datetime, timezone
from typing import Optional

from .. import config, logger, ub
from .text_extraction import extract_text
from .llm_utils import get_llm, is_langchain_available
from .db_utils import get_db_connection, ensure_table_exists

log = logger.create()

# Re-export for backward compatibility
LANGCHAIN_AVAILABLE = is_langchain_available()


def _trigger_embedding_generation(book_id: int):
    """
    Trigger embedding generation for a book after summary is created/updated.
    This runs synchronously to ensure the embedding is created with the new summary.
    Only runs if config_ai_auto_index_on_summary is enabled.
    
    Args:
        book_id: Book ID to generate embedding for
    """
    # Check if auto-indexing on summary is enabled
    if not getattr(config, 'config_ai_auto_index_on_summary', False):
        log.info("Auto-index on summary is disabled, skipping embedding generation for book %d", book_id)
        return
    
    try:
        from .embeddings import generate_embedding
        
        log.info("Triggering embedding generation for book %d after summary update", book_id)
        result = generate_embedding(book_id)
        
        if result is not None:
            log.info("Successfully generated embedding for book %d (dimension: %d)", book_id, len(result))
        else:
            log.warning("Failed to generate embedding for book %d", book_id)
            
    except Exception as e:
        # Don't fail the summary if embedding generation fails
        log.error("Error generating embedding for book %d: %s", book_id, e)


def _construct_prompt(metadata_text: str, extracted_text: str) -> str:
    """
    Construct prompt for LLM summarization.
    
    Args:
        metadata_text: Book metadata (title, author, description, tags)
        extracted_text: Extracted book content (up to token limit)
    
    Returns:
        Formatted prompt string
    """
    prompt = f"""Generate a concise summary (3-7 sentences) of the following book:

{metadata_text}

Content excerpt:
{extracted_text}

Focus on: what the book is about, who it's for, and key themes/topics. Be concise and informative."""
    
    return prompt


def generate_summary(book_id: int) -> Optional[str]:
    """
    Generate AI summary for a book.

    Args:
        book_id: Book ID from database

    Returns:
        Summary text if successful, None or error message if failed
    """
    from langchain_core.messages import HumanMessage
    from sqlalchemy import text

    if not config.config_ai_enabled:
        return "Error: AI features are disabled"

    if not LANGCHAIN_AVAILABLE:
        return "Error: LangChain not installed. Install with: pip install langchain langchain-openai langchain-anthropic langchain-community"

    max_tokens = getattr(config, 'config_ai_max_tokens_summary', 500)
    llm = get_llm(max_tokens=max_tokens)
    if not llm:
        from .llm_utils import get_api_key
        if not get_api_key():
            return "Error: API key not configured. Please set config_ai_api_key in settings."
        provider = getattr(config, 'config_ai_provider', 'openai')
        return f"Error: Failed to initialize LLM for provider '{provider}'. Check API key and model configuration."

    try:
        book_text = extract_text(book_id, max_tokens=2000)
        if not book_text:
            return f"Error: Failed to extract text for book {book_id}"

        parts = book_text.split('\n\n---\n\n')
        metadata_text = parts[0] if parts else book_text
        extracted_text = parts[1] if len(parts) > 1 else ""

        prompt = _construct_prompt(metadata_text, extracted_text)
        messages = [HumanMessage(content=prompt)]

        try:
            response = llm.invoke(messages)
            summary_text = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            log.error("LLM call failed: %s", e)
            return f"Error: LLM call failed: {str(e)}"

        if not summary_text:
            return "Error: LLM returned empty summary"

        model_name = getattr(config, 'config_ai_llm_model', 'unknown')

        try:
            with get_db_connection() as conn:
                # Ensure table exists
                ensure_table_exists(
                    conn,
                    """CREATE TABLE IF NOT EXISTS book_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        book_id INTEGER NOT NULL,
                        summary_text TEXT NOT NULL,
                        model_name VARCHAR(100) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )""",
                    "CREATE INDEX IF NOT EXISTS ix_book_summaries_book_id ON book_summaries (book_id)"
                )

                result = conn.execute(
                    text("SELECT id FROM book_summaries WHERE book_id = :book_id"),
                    {"book_id": book_id}
                ).fetchone()

                now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

                if result:
                    conn.execute(
                        text("""UPDATE book_summaries
                            SET summary_text = :summary_text, model_name = :model_name, updated_at = :updated_at
                            WHERE book_id = :book_id"""),
                        {"summary_text": summary_text, "model_name": model_name, "updated_at": now, "book_id": book_id}
                    )
                    log.info("Updated summary for book %d", book_id)
                else:
                    conn.execute(
                        text("""INSERT INTO book_summaries (book_id, summary_text, model_name, created_at, updated_at)
                            VALUES (:book_id, :summary_text, :model_name, :created_at, :updated_at)"""),
                        {"book_id": book_id, "summary_text": summary_text, "model_name": model_name, "created_at": now, "updated_at": now}
                    )
                    log.info("Inserted summary for book %d", book_id)

                conn.commit()

                # Trigger embedding generation after summary is saved
                _trigger_embedding_generation(book_id)

        except RuntimeError as e:
            log.error("Database error: %s", e)
            return f"Error: {str(e)}"
        except Exception as e:
            log.error("Failed to store summary: %s", e, exc_info=True)
            return f"Error: Failed to store summary: {str(e)}"

        return summary_text

    except Exception as e:
        log.error("Summary generation failed: %s", e)
        return f"Error: Summary generation failed: {str(e)}"

