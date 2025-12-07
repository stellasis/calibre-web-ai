# -*- coding: utf-8 -*-

"""
Shared LLM utilities for AI modules.
Provides centralized LLM and embedding model initialization to eliminate code duplication.
"""

import os
from typing import Optional, Any

from .. import config, logger

log = logger.create()

# Track LangChain availability
LANGCHAIN_AVAILABLE = False
LANGCHAIN_EMBEDDINGS_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_community.chat_models import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    log.warning("LangChain LLM not available. Install with: pip install langchain langchain-openai langchain-anthropic langchain-community")

try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.embeddings import OllamaEmbeddings
    LANGCHAIN_EMBEDDINGS_AVAILABLE = True
except ImportError:
    log.warning("LangChain embeddings not available. Install with: pip install langchain langchain-openai langchain-community")


def get_api_key() -> Optional[str]:
    """
    Get the AI API key from configuration.
    Single source of truth for API key retrieval.

    Returns:
        API key string or None if not configured
    """
    api_key = getattr(config, 'config_ai_api_key', None)
    if not api_key:
        api_key = getattr(config, 'config_ai_api_key_e', None)
    return api_key if api_key else None


def get_llm(max_tokens: Optional[int] = None):
    """
    Get LangChain LLM instance based on configuration.

    Args:
        max_tokens: Maximum tokens for response. If None, uses config value.

    Returns:
        LangChain LLM instance or None if not available/configured
    """
    if not LANGCHAIN_AVAILABLE:
        log.error("LangChain not available")
        return None

    if not config.config_ai_enabled:
        log.warning("AI features are disabled")
        return None

    api_key = get_api_key()
    if not api_key:
        log.warning("AI API key not configured")
        return None

    provider = getattr(config, 'config_ai_provider', 'openai')
    model = getattr(config, 'config_ai_llm_model', 'gpt-4o-mini')
    timeout = getattr(config, 'config_ai_timeout_seconds', 60)
    max_retries = getattr(config, 'config_ai_max_retries', 3)

    if max_tokens is None:
        max_tokens = getattr(config, 'config_ai_max_tokens_summary', 500)

    try:
        if provider == 'openai':
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                timeout=timeout,
                max_retries=max_retries,
                max_tokens=max_tokens,
                temperature=0.7
            )
        elif provider == 'openrouter':
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=timeout,
                max_retries=max_retries,
                max_tokens=max_tokens,
                temperature=0.7
            )
        elif provider == 'anthropic':
            return ChatAnthropic(
                model=model,
                api_key=api_key,
                timeout=timeout,
                max_retries=max_retries,
                max_tokens=max_tokens,
                temperature=0.7
            )
        elif provider == 'ollama':
            return ChatOllama(
                model=model,
                base_url=os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434'),
                timeout=timeout,
                num_predict=max_tokens,
                temperature=0.7
            )
        else:
            log.error("Unknown AI provider: %s", provider)
            return None
    except Exception as e:
        log.error("Failed to initialize LLM: %s", e)
        return None


def get_embedding_model():
    """
    Get LangChain embedding model instance based on configuration.

    Returns:
        LangChain embeddings instance or None if not available/configured
    """
    if not LANGCHAIN_EMBEDDINGS_AVAILABLE:
        log.error("LangChain embeddings not available")
        return None

    if not config.config_ai_enabled:
        log.warning("AI features are disabled")
        return None

    api_key = get_api_key()
    if not api_key:
        log.warning("AI API key not configured")
        return None

    provider = getattr(config, 'config_ai_provider', 'openai')
    model = getattr(config, 'config_ai_embedding_model', 'text-embedding-3-small')
    timeout = getattr(config, 'config_ai_timeout_seconds', 60)
    max_retries = getattr(config, 'config_ai_max_retries', 3)

    try:
        if provider == 'openai':
            return OpenAIEmbeddings(
                model=model,
                api_key=api_key,
                timeout=timeout,
                max_retries=max_retries
            )
        elif provider == 'openrouter':
            return OpenAIEmbeddings(
                model=model,
                api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                timeout=timeout,
                max_retries=max_retries
            )
        elif provider == 'ollama':
            return OllamaEmbeddings(
                model=model,
                base_url=os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            )
        else:
            log.error("Unknown AI provider for embeddings: %s", provider)
            return None
    except Exception as e:
        log.error("Failed to initialize embedding model: %s", e)
        return None


def safe_str(value: Any) -> str:
    """
    Safely convert a value to string, handling Flask-Babel LazyString.

    Args:
        value: Any value to convert

    Returns:
        String representation of value
    """
    if hasattr(value, '_message'):
        msg = value._message
        return str(msg[0]) if isinstance(msg, tuple) else str(msg)
    try:
        return str(value)
    except TypeError:
        return type(value).__name__


def is_langchain_available() -> bool:
    """Check if LangChain LLM is available."""
    return LANGCHAIN_AVAILABLE


def is_embeddings_available() -> bool:
    """Check if LangChain embeddings are available."""
    return LANGCHAIN_EMBEDDINGS_AVAILABLE
