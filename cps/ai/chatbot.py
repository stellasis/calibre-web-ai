# -*- coding: utf-8 -*-

"""
RAG Chatbot Service
Generates conversational answers from book chunks using RAG (Retrieval-Augmented Generation).
"""

from typing import Optional, List, Dict, Any

from .. import config, logger, calibre_db
from ..ub import session, BookChunk, BookIndexStatus, BookChunkEmbedding
from .chunk_search import search_chunks, get_chunk_count
from .llm_utils import get_llm, get_api_key, is_langchain_available

log = logger.create()

# Re-export for backward compatibility
LANGCHAIN_AVAILABLE = is_langchain_available()


def _check_book_indexed(book_id: int) -> bool:
    """
    Check if a book has been indexed (has chunks).
    
    Args:
        book_id: Book ID to check
    
    Returns:
        True if book is indexed, False otherwise
    """
    try:
        # Check if book has chunks
        chunk_count = get_chunk_count(book_id)
        if chunk_count > 0:
            return True
        
        # Also check index status
        status = session.query(BookIndexStatus).filter_by(book_id=book_id).first()
        if status and status.status == 'completed':
            return True
        
        return False
    except Exception as e:
        log.error("Error checking if book %d is indexed: %s", book_id, e)
        return False


def _construct_rag_prompt(
    book_title: str,
    book_author: str,
    chunks: List[Dict[str, Any]],
    question: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Construct RAG prompt for LLM.
    
    Args:
        book_title: Book title
        book_author: Book author
        chunks: List of relevant chunks (dicts with chunk_text, chapter_title, similarity_score)
        question: User question
        conversation_history: Optional list of previous Q&A pairs
    
    Returns:
        Formatted prompt string
    """
    # System prompt
    system_prompt = "You are a helpful assistant answering questions about a specific book. Use only the provided book excerpts to answer. If the answer is not in the excerpts, say so."
    
    # Book context
    book_context = f"Book Information:\n- Title: {book_title}\n- Author: {book_author}\n"
    
    # Relevant chunks
    chunks_text = "Relevant Book Excerpts:\n"
    for i, chunk in enumerate(chunks, 1):
        chunk_text = chunk.get('chunk_text', '')
        chapter_title = chunk.get('chapter_title')
        if chapter_title:
            chunks_text += f"\n{chunk_text}\n[Chapter: {chapter_title}]\n"
        else:
            chunks_text += f"\n{chunk_text}\n"
    
    # Conversation history
    history_text = ""
    if conversation_history:
        history_limit = getattr(config, 'config_ai_chatbot_history_limit', 5)
        recent_history = conversation_history[-history_limit:] if len(conversation_history) > history_limit else conversation_history
        
        history_text = "\nPrevious Conversation:\n"
        for i, exchange in enumerate(recent_history, 1):
            q = exchange.get('question', '')
            a = exchange.get('answer', '')
            history_text += f"Q{i}: {q}\nA{i}: {a}\n"
    
    # Construct full prompt
    prompt = f"""{system_prompt}

{book_context}

{chunks_text}

{history_text}

User Question: {question}

Instructions:
- Answer based ONLY on the provided book excerpts
- If the answer is not in the excerpts, say "I don't have enough information from the book to answer that question."
- Be conversational and helpful
- Cite chapter names when relevant"""
    
    return prompt


def ask_question(
    book_id: int,
    question: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Ask a question about a book using RAG (Retrieval-Augmented Generation).
    
    Args:
        book_id: Book ID
        question: User question
        conversation_history: Optional list of previous Q&A pairs [{'question': str, 'answer': str}]
    
    Returns:
        Dict with keys:
        - 'answer': str - The generated answer
        - 'chunks_used': List[Dict] - Chunks that informed the answer
        - 'confidence': float - Optional confidence score (0-1)
        - 'error': Optional[str] - Error message if failed
    """
    # Initialize response structure
    response = {
        'answer': '',
        'chunks_used': [],
        'confidence': 0.0,
        'error': None
    }
    
    # Validate question input
    if not question or not isinstance(question, str):
        response['error'] = 'Question is required and must be a string'
        log.warning("Invalid question input: %s", type(question))
        return response
    
    question = question.strip()
    if not question:
        response['error'] = 'Question cannot be empty'
        log.warning("Empty question provided")
        return response
    
    # Validate question length (prevent abuse)
    if len(question) > 1000:
        response['error'] = 'Question is too long (maximum 1000 characters)'
        log.warning("Question too long: %d characters", len(question))
        return response
    
    # Validate prerequisites
    if not config.config_ai_enabled:
        response['error'] = 'AI features are disabled'
        log.warning("AI features are disabled")
        return response
    
    if not getattr(config, 'config_ai_chatbot_enabled', False):
        response['error'] = 'Chatbot feature is disabled'
        log.warning("Chatbot feature is disabled")
        return response
    
    if not LANGCHAIN_AVAILABLE:
        response['error'] = 'LangChain not installed. Install with: pip install langchain langchain-openai langchain-anthropic langchain-community'
        log.error(response['error'])
        return response
    
    # Validate book exists
    try:
        book = calibre_db.get_book(book_id)
        if not book:
            response['error'] = f'Book {book_id} not found'
            log.warning("Book %d not found", book_id)
            return response
    except Exception as e:
        response['error'] = f'Error fetching book: {str(e)}'
        log.error("Error fetching book %d: %s", book_id, e)
        return response
    
    # Check if book is indexed
    if not _check_book_indexed(book_id):
        response['error'] = 'Book is not indexed. Please index the book first.'
        log.warning("Book %d is not indexed", book_id)
        return response
    
    # Retrieve relevant chunks
    try:
        chunks_limit = getattr(config, 'config_ai_chatbot_chunks_limit', 5)
        # Request more chunks than needed to account for threshold filtering
        search_limit = max(chunks_limit * 3, 20)  # Get 3x more chunks for filtering
        chunks = search_chunks(query=question, book_id=book_id, limit=search_limit)
        
        if not chunks:
            # Check if book actually has chunks
            from .chunk_search import get_chunk_count
            chunk_count = get_chunk_count(book_id)
            if chunk_count == 0:
                response['error'] = 'Book is not indexed. Please index the book first.'
                log.warning("Book %d has no chunks (not indexed)", book_id)
            else:
                # Check if there are embeddings (chunks exist but search returned nothing)
                from ..ub import BookChunkEmbedding
                embedding_count = session.query(BookChunkEmbedding).filter_by(book_id=book_id).count()
                if embedding_count == 0:
                    response['error'] = 'Book chunks are not embedded. Please re-index the book to generate embeddings.'
                    log.error("Book %d has %d chunks but 0 embeddings - re-indexing required", book_id, chunk_count)
                elif embedding_count != chunk_count:
                    response['error'] = f'Incomplete embeddings ({embedding_count}/{chunk_count} chunks embedded). Please re-index the book.'
                    log.error("Book %d has incomplete embeddings: %d/%d chunks", book_id, embedding_count, chunk_count)
                else:
                    # Chunks and embeddings exist, but search returned nothing - likely virtual table issue
                    response['error'] = 'Search failed - virtual table may not be synced. Please re-index the book to sync embeddings to the search index.'
                    log.error("Book %d has %d chunks and %d embeddings but search returned no results - virtual table may be empty or sqlite-vec not loaded", book_id, chunk_count, embedding_count)
            return response
        
        # Log similarity scores for debugging
        if chunks:
            scores = [chunk.get('similarity_score', 0.0) for chunk in chunks[:5]]
            log.debug("Top 5 similarity scores for book %d: %s", book_id, scores)
        
        # Filter chunks by similarity threshold
        similarity_threshold = getattr(config, 'config_ai_chatbot_similarity_threshold', 0.3)
        filtered_chunks = [chunk for chunk in chunks if chunk.get('similarity_score', 0.0) >= similarity_threshold]
        
        if not filtered_chunks:
            # If no chunks meet threshold, try with a lower threshold (0.3) as fallback
            fallback_threshold = 0.3
            filtered_chunks = [chunk for chunk in chunks if chunk.get('similarity_score', 0.0) >= fallback_threshold]
            
            if not filtered_chunks:
                # Still no chunks - return error with helpful message
                max_score = max([chunk.get('similarity_score', 0.0) for chunk in chunks]) if chunks else 0.0
                response['error'] = f'No relevant content found for this question. Best match similarity: {max_score:.2f} (threshold: {similarity_threshold}). Try lowering the similarity threshold in settings or rephrasing your question.'
                log.warning("No chunks meet similarity threshold %f for book %d (best score: %f)", similarity_threshold, book_id, max_score)
                return response
            else:
                # Use fallback chunks but log it
                log.info("Using fallback threshold %f for book %d (original threshold %f)", fallback_threshold, book_id, similarity_threshold)
        
        # Select top chunks (up to chunks_limit)
        top_chunks = filtered_chunks[:min(chunks_limit, len(filtered_chunks))]
        response['chunks_used'] = top_chunks
        
    except Exception as e:
        response['error'] = f'Error retrieving chunks: {str(e)}'
        log.error("Error retrieving chunks for book %d: %s", book_id, e, exc_info=True)
        return response
    
    # Get LLM instance
    max_tokens = getattr(config, 'config_ai_max_tokens_chatbot', 500)
    llm = get_llm(max_tokens=max_tokens)
    if not llm:
        if not get_api_key():
            response['error'] = 'API key not configured. Please set config_ai_api_key in settings.'
        else:
            provider = getattr(config, 'config_ai_provider', 'openai')
            response['error'] = f"Failed to initialize LLM for provider '{provider}'. Check API key and model configuration."
        log.error(response['error'])
        return response
    
    # Construct RAG prompt
    try:
        book_title = book.title if hasattr(book, 'title') else 'Unknown'
        book_author = ', '.join([a.name for a in book.authors]) if hasattr(book, 'authors') and book.authors else 'Unknown'
        
        prompt = _construct_rag_prompt(
            book_title=book_title,
            book_author=book_author,
            chunks=top_chunks,
            question=question,
            conversation_history=conversation_history
        )
    except Exception as e:
        response['error'] = f'Error constructing prompt: {str(e)}'
        log.error("Error constructing prompt: %s", e, exc_info=True)
        return response
    
    # Generate answer with LLM
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content="You are a helpful assistant answering questions about a specific book. Use only the provided book excerpts to answer. If the answer is not in the excerpts, say so."),
            HumanMessage(content=prompt)
        ]
        
        # Log prompt for debugging (truncated for privacy)
        log.debug("RAG prompt for book %d (length: %d chars): %s", 
                 book_id, len(prompt), 
                 prompt[:200] + "..." if len(prompt) > 200 else prompt)
        
        llm_response = llm.invoke(messages)
        answer = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
        
        if not answer:
            response['error'] = 'LLM returned empty answer'
            log.warning("LLM returned empty answer for book %d", book_id)
            return response
        
        response['answer'] = answer
        
        # Calculate confidence score (average similarity of chunks used)
        if top_chunks:
            avg_similarity = sum(chunk.get('similarity_score', 0.0) for chunk in top_chunks) / len(top_chunks)
            response['confidence'] = round(avg_similarity, 2)
        
    except TimeoutError as e:
        timeout = getattr(config, 'config_ai_timeout_seconds', 60)
        error_msg = f'Request timed out after {timeout} seconds'
        response['error'] = error_msg
        log.error("LLM timeout for book %d: %s", book_id, e)
        return response
    except Exception as e:
        error_msg = f'Error generating answer: {str(e)}'
        response['error'] = error_msg
        log.error("Error generating answer for book %d: %s", book_id, e, exc_info=True)
        return response
    
    return response

