# -*- coding: utf-8 -*-

"""
Book chunking service for full book indexing.
Splits books into semantic chunks for embedding and search.
"""

import os
import zipfile
import re
import chardet
from lxml import etree, html
from typing import List, Dict, Tuple, Optional

from .. import config, logger
from .. import db
from ..ub import session, BookChunk, BookIndexStatus

log = logger.create()

# Try to import PDF reader
try:
    from pypdf import PdfReader
    use_pdf = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
        use_pdf = True
    except ImportError:
        try:
            from PyPDF3 import PdfFileReader as PdfReader
            use_pdf = True
        except ImportError:
            use_pdf = False
            log.warning("PDF extraction not available: PyPDF not installed")


# Configuration defaults
DEFAULT_CHUNK_SIZE_TOKENS = 500
DEFAULT_CHUNK_OVERLAP_TOKENS = 50
MAX_CHUNKS_PER_BOOK = 10000


def estimate_tokens(text: str) -> int:
    """
    Rough token estimation: 1 token ≈ 4 characters.
    """
    return len(text) // 4


def split_text_into_chunks(
    text: str,
    chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
    chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS
) -> List[Dict[str, any]]:
    """
    Split text into chunks with overlap, respecting paragraph boundaries.
    
    Args:
        text: Text to chunk
        chunk_size_tokens: Target tokens per chunk
        chunk_overlap_tokens: Overlap tokens between chunks
    
    Returns:
        List of chunk dictionaries with 'text', 'start_pos', 'end_pos', 'token_count'
    """
    if not text:
        return []
    
    chunks = []
    chunk_size_chars = chunk_size_tokens * 4
    overlap_chars = chunk_overlap_tokens * 4
    
    # Split by paragraphs first (double newlines)
    paragraphs = re.split(r'\n\s*\n+', text)
    
    current_chunk = ""
    current_start = 0
    chunk_index = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If adding this paragraph would exceed chunk size, finalize current chunk
        if current_chunk and estimate_tokens(current_chunk + "\n\n" + para) > chunk_size_tokens:
            # Finalize current chunk
            chunk_end = len(current_chunk)
            chunks.append({
                'text': current_chunk,
                'start_pos': current_start,
                'end_pos': current_start + chunk_end,
                'token_count': estimate_tokens(current_chunk),
                'chunk_index': chunk_index
            })
            chunk_index += 1
            
            # Start new chunk with overlap
            if overlap_chars > 0 and len(current_chunk) > overlap_chars:
                # Take last overlap_chars from previous chunk
                overlap_text = current_chunk[-overlap_chars:]
                # Try to start at a sentence boundary
                sentence_end = max(
                    overlap_text.rfind('.'),
                    overlap_text.rfind('!'),
                    overlap_text.rfind('?')
                )
                if sentence_end > overlap_chars // 2:
                    overlap_text = overlap_text[sentence_end + 1:].strip()
                current_chunk = overlap_text + "\n\n" + para
                current_start = current_start + chunk_end - len(overlap_text)
            else:
                current_chunk = para
                current_start = current_start + chunk_end
        
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
                # Track start position (approximate)
                if chunks:
                    last_chunk = chunks[-1]
                    current_start = last_chunk['end_pos']
                else:
                    current_start = 0
        
        # Safety limit
        if chunk_index >= MAX_CHUNKS_PER_BOOK:
            log.warning("Reached maximum chunks limit (%d) for book", MAX_CHUNKS_PER_BOOK)
            break
    
    # Add final chunk
    if current_chunk:
        chunks.append({
            'text': current_chunk,
            'start_pos': current_start,
            'end_pos': current_start + len(current_chunk),
            'token_count': estimate_tokens(current_chunk),
            'chunk_index': chunk_index
        })
    
    return chunks


def extract_full_epub_text(epub_path: str) -> Tuple[str, List[Tuple[str, int, int]]]:
    """
    Extract full text from EPUB file with chapter information.
    
    Returns:
        Tuple of (full_text, [(chapter_title, start_pos, end_pos), ...])
    """
    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            # Get content.opf to find chapters
            try:
                container_xml = epub_zip.read('META-INF/container.xml')
                container_tree = etree.fromstring(container_xml)
                ns = {'n': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                opf_path = container_tree.xpath('n:rootfiles/n:rootfile/@full-path', namespaces=ns)[0]
                opf_content = epub_zip.read(opf_path)
                opf_tree = etree.fromstring(opf_content)
            except Exception as e:
                log.warning("Failed to read EPUB structure: %s", e)
                return "", []
            
            # Get manifest items (chapters)
            opf_ns = {
                'opf': 'http://www.idpf.org/2007/opf',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            manifest_items = opf_tree.xpath('//opf:manifest/opf:item', namespaces=opf_ns)
            spine_items = opf_tree.xpath('//opf:spine/opf:itemref', namespaces=opf_ns)
            
            log.debug("EPUB: Found %d manifest items, %d spine items", len(manifest_items), len(spine_items))
            
            # Extract full text from all chapters
            full_text = ""
            chapters = []  # List of (title, start_pos, end_pos)
            opf_dir = os.path.dirname(opf_path) if opf_path else ""
            
            # Create mapping of idref to href
            # Use the same simple approach as text_extraction.py which works
            id_to_href = {}
            for item in manifest_items:
                item_id = item.get('id')
                item_href = item.get('href')
                # Match the working summary extraction: only check for application/xhtml
                if item_id and item_href and item.get('media-type', '').startswith('application/xhtml'):
                    # Resolve relative path - ZIP files use forward slashes, not os.path.join
                    if opf_dir:
                        # Use forward slashes for ZIP file paths (works on all platforms)
                        item_href = '/'.join([opf_dir, item_href]).replace('\\', '/')
                    else:
                        # Ensure forward slashes for ZIP paths
                        item_href = item_href.replace('\\', '/')
                    id_to_href[item_id] = item_href
                    log.debug("EPUB: Mapped id '%s' to href '%s'", item_id, item_href)
            
            log.debug("EPUB: Created %d id-to-href mappings", len(id_to_href))
            
            # Extract from all spine items (chapters)
            extracted_chapters = 0
            for spine_item in spine_items:
                idref = spine_item.get('idref')
                if not idref:
                    log.debug("EPUB: Spine item missing idref")
                    continue
                if idref not in id_to_href:
                    log.warning("EPUB: Spine idref '%s' not found in manifest items", idref)
                    continue
                
                try:
                    chapter_path = id_to_href[idref]
                    log.debug("EPUB: Extracting chapter '%s' from path '%s'", idref, chapter_path)
                    chapter_content = epub_zip.read(chapter_path)
                    
                    # Parse HTML/XHTML directly (html.fromstring handles encoding automatically)
                    # This matches the working approach in text_extraction.py
                    chapter_tree = html.fromstring(chapter_content)
                    
                    # Try to get chapter title from h1/h2 or first heading
                    chapter_title = None
                    headings = chapter_tree.xpath('//h1 | //h2 | //h3')
                    if headings:
                        chapter_title = headings[0].text_content().strip()
                    
                    # Extract text (same simple approach as summary extraction)
                    chapter_text = chapter_tree.text_content()
                    
                    if chapter_text:
                        chapter_start = len(full_text)
                        full_text += chapter_text + "\n\n"
                        chapter_end = len(full_text)
                        extracted_chapters += 1
                        
                        if chapter_title:
                            chapters.append((chapter_title, chapter_start, chapter_end))
                        log.debug("EPUB: Extracted chapter '%s' (%d chars)", idref, len(chapter_text))
                    else:
                        log.warning("EPUB: Chapter '%s' extracted but text is empty", idref)
                except Exception as e:
                    log.warning("Failed to extract chapter %s (%s): %s", idref, id_to_href.get(idref, 'unknown'), e, exc_info=True)
                    continue
            
            log.info("EPUB: Extracted %d chapters, total text length: %d", extracted_chapters, len(full_text))
            
            if not full_text and extracted_chapters == 0:
                log.error("EPUB: No chapters were extracted. Spine items: %d, Mapped items: %d", len(spine_items), len(id_to_href))
                # Log spine item idrefs
                spine_idrefs = [s.get('idref') for s in spine_items if s.get('idref')]
                log.error("EPUB: Spine idrefs: %s", spine_idrefs[:10])  # First 10
                log.error("EPUB: Mapped ids: %s", list(id_to_href.keys())[:10])  # First 10
                # Try to list what's in the manifest
                for item in manifest_items[:10]:  # Log first 10 items
                    log.error("EPUB manifest item: id=%s, href=%s, media-type=%s", 
                             item.get('id'), item.get('href'), item.get('media-type'))
            
            return full_text, chapters
            
    except zipfile.BadZipFile:
        log.error("EPUB file is not a valid ZIP archive: %s", epub_path)
        return "", []
    except Exception as e:
        log.error("EPUB extraction failed for %s: %s", epub_path, e, exc_info=True)
        return "", []


def extract_full_pdf_text(pdf_path: str) -> str:
    """Extract full text from PDF file."""
    if not use_pdf:
        log.warning("PDF extraction not available: PyPDF not installed")
        return ""
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PdfReader(f)
            full_text = ""
            
            # Extract from all pages
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n\n"
                except Exception as e:
                    log.debug("Failed to extract PDF page %d: %s", page_num, e)
                    continue
            
            return full_text
            
    except Exception as e:
        log.warning("PDF extraction failed: %s", e)
        return ""


def extract_full_txt_text(txt_path: str) -> str:
    """Extract full text from TXT file."""
    try:
        with open(txt_path, 'rb') as f:
            rawdata = f.read()
            result = chardet.detect(rawdata)
            
            try:
                text_data = rawdata.decode(result['encoding'])
            except UnicodeDecodeError as e:
                log.warning("Encoding error in text file: %s", e)
                if "surrogate" in str(e):
                    text_data = rawdata.decode(result['encoding'], 'surrogatepass')
                else:
                    text_data = rawdata.decode(result['encoding'], 'ignore')
            
            return text_data
            
    except Exception as e:
        log.warning("TXT extraction failed: %s", e)
        return ""


def get_chapter_title_for_position(position: int, chapters: List[Tuple[str, int, int]]) -> Optional[str]:
    """Get chapter title for a given text position."""
    for title, start, end in chapters:
        if start <= position < end:
            return title
    return None


def chunk_book(book_id: int) -> List[int]:
    """
    Chunk a book into semantic chunks and store in database.
    
    Args:
        book_id: Book ID from database
    
    Returns:
        List of chunk IDs created
    
    Raises:
        ValueError: If book not found or format not supported
        Exception: On processing errors
    """
    try:
        # Get configuration
        chunk_size = getattr(config, 'config_ai_chunk_size_tokens', DEFAULT_CHUNK_SIZE_TOKENS)
        chunk_overlap = getattr(config, 'config_ai_chunk_overlap_tokens', DEFAULT_CHUNK_OVERLAP_TOKENS)
        max_chunks = getattr(config, 'config_ai_max_chunks_per_book', MAX_CHUNKS_PER_BOOK)
        
        # Get book from database
        calibre_db = db.CalibreDB()
        book = calibre_db.get_book(book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")
        
        # Update status to processing
        status = session.query(BookIndexStatus).filter_by(book_id=book_id).first()
        if not status:
            status = BookIndexStatus(
                book_id=book_id,
                status='processing',
                total_chunks=0,
                processed_chunks=0
            )
            session.add(status)
        else:
            status.status = 'processing'
            status.total_chunks = 0
            status.processed_chunks = 0
            status.error_message = None
        session.commit()
        
        # Try to find a supported format (EPUB, PDF, TXT in priority order)
        formats_to_try = ['EPUB', 'PDF', 'TXT']
        full_text = ""
        chapters = []
        
        for fmt in formats_to_try:
            book_data = calibre_db.get_book_format(book_id, fmt)
            if not book_data:
                continue
            
            # Build file path
            if config.config_use_google_drive:
                log.warning("Google Drive not supported for full text extraction")
                break
            
            file_path = os.path.join(
                config.get_book_path(),
                book.path,
                f"{book_data.name}.{book_data.format.lower()}"
            )
            
            if not os.path.exists(file_path):
                log.warning("Book file not found: %s", file_path)
                continue
            
            # Extract based on format
            fmt_lower = fmt.lower()
            log.info("Attempting to extract text from %s format, file: %s", fmt, file_path)
            
            if fmt_lower == 'epub':
                full_text, chapters = extract_full_epub_text(file_path)
                if not full_text:
                    log.warning("EPUB extraction returned empty text for file: %s", file_path)
            elif fmt_lower == 'pdf':
                full_text = extract_full_pdf_text(file_path)
                if not full_text:
                    log.warning("PDF extraction returned empty text for file: %s", file_path)
            elif fmt_lower == 'txt':
                full_text = extract_full_txt_text(file_path)
                if not full_text:
                    log.warning("TXT extraction returned empty text for file: %s", file_path)
            
            if full_text:
                log.info("Successfully extracted %d characters from %s format", len(full_text), fmt)
                break
            else:
                log.warning("Extraction failed or returned empty text for %s format", fmt)
        
        if not full_text:
            # Get available formats for better error message
            available_formats = []
            for fmt in ['EPUB', 'PDF', 'TXT', 'MOBI', 'AZW3', 'FB2']:
                book_data = calibre_db.get_book_format(book_id, fmt)
                if book_data:
                    available_formats.append(fmt)
            
            if available_formats:
                raise ValueError(f"No supported format found for book {book_id}. Available formats: {', '.join(available_formats)}. Supported formats: EPUB, PDF, TXT")
            else:
                raise ValueError(f"No supported format found for book {book_id}. Book has no available formats.")
        
        # Split into chunks
        chunk_data = split_text_into_chunks(full_text, chunk_size, chunk_overlap)
        
        if len(chunk_data) > max_chunks:
            log.warning("Book %d has %d chunks, limiting to %d", book_id, len(chunk_data), max_chunks)
            chunk_data = chunk_data[:max_chunks]
        
        # Delete existing chunks for this book
        session.query(BookChunk).filter_by(book_id=book_id).delete()
        
        # Store chunks in database
        for chunk_info in chunk_data:
            # Get chapter title if available
            chapter_title = None
            if chapters:
                chapter_title = get_chapter_title_for_position(
                    chunk_info['start_pos'],
                    chapters
                )
            
            chunk = BookChunk(
                book_id=book_id,
                chunk_index=chunk_info['chunk_index'],
                chapter_title=chapter_title,
                chunk_text=chunk_info['text'],
                token_count=chunk_info['token_count'],
                start_position=chunk_info['start_pos'],
                end_position=chunk_info['end_pos']
            )
            session.add(chunk)
        
        # Update status
        status.total_chunks = len(chunk_data)
        status.processed_chunks = 0  # Will be updated by embedding service
        session.commit()
        
        # Get chunk IDs after commit
        chunks = session.query(BookChunk).filter_by(book_id=book_id).order_by(BookChunk.chunk_index).all()
        chunk_ids = [chunk.id for chunk in chunks]
        
        log.info("Chunked book %d into %d chunks", book_id, len(chunk_data))
        return chunk_ids
        
    except Exception as e:
        log.error("Chunking failed for book %d: %s", book_id, e, exc_info=True)
        # Update status to failed
        try:
            status = session.query(BookIndexStatus).filter_by(book_id=book_id).first()
            if status:
                status.status = 'failed'
                status.error_message = str(e)
                session.commit()
        except Exception:
            pass
        raise

