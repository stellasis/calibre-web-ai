# -*- coding: utf-8 -*-

"""
Text extraction service for AI summary generation.
Extracts text from books in various formats (EPUB, PDF, TXT) for AI processing.
"""

import os
import zipfile
import chardet
from lxml import etree, html

from .. import config, logger
from .. import db

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


def estimate_tokens(text):
    """
    Rough token estimation: 1 token ≈ 0.75 words or 4 characters.
    For 2000 tokens: ~1500 words or ~8000 characters.
    """
    # Simple approximation: tokens ≈ characters / 4
    return len(text) // 4


def truncate_to_tokens(text, max_tokens):
    """Truncate text to approximately max_tokens."""
    if estimate_tokens(text) <= max_tokens:
        return text
    
    # Truncate to approximately max_tokens
    max_chars = max_tokens * 4
    return text[:max_chars]


def get_book_metadata(book):
    """Extract book metadata as formatted string."""
    title = book.title if book.title else "Unknown"
    
    authors = []
    if book.authors:
        authors = [author.name.replace('|', ',') for author in book.authors]
    author_str = ', '.join(authors) if authors else "Unknown"
    
    description = ""
    if book.comments and len(book.comments) > 0:
        description = book.comments[0].text if book.comments[0].text else ""
    
    tags = []
    if book.tags:
        tags = [tag.name for tag in book.tags]
    tags_str = ', '.join(tags) if tags else ""
    
    return f"Title: {title}\nAuthor: {author_str}\nDescription: {description}\nTags: {tags_str}"


def extract_epub_text(epub_path, max_tokens=2000):
    """Extract text from EPUB file."""
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
                return ""
            
            # Get manifest items (chapters)
            opf_ns = {
                'opf': 'http://www.idpf.org/2007/opf',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            manifest_items = opf_tree.xpath('//opf:manifest/opf:item', namespaces=opf_ns)
            spine_items = opf_tree.xpath('//opf:spine/opf:itemref', namespaces=opf_ns)
            
            # Extract text from first chapter or first 20 pages worth
            extracted_text = ""
            opf_dir = os.path.dirname(opf_path) if opf_path else ""
            
            # Create mapping of idref to href
            id_to_href = {}
            for item in manifest_items:
                item_id = item.get('id')
                item_href = item.get('href')
                if item_id and item_href and item.get('media-type', '').startswith('application/xhtml'):
                    # Resolve relative path
                    if opf_dir:
                        item_href = os.path.normpath(os.path.join(opf_dir, item_href))
                    id_to_href[item_id] = item_href
            
            # Extract from first few spine items (chapters)
            max_chapters = 20
            for idx, spine_item in enumerate(spine_items[:max_chapters]):
                if estimate_tokens(extracted_text) >= max_tokens:
                    break
                
                idref = spine_item.get('idref')
                if idref and idref in id_to_href:
                    try:
                        chapter_content = epub_zip.read(id_to_href[idref])
                        # Parse HTML/XHTML
                        chapter_tree = html.fromstring(chapter_content)
                        # Extract text
                        chapter_text = chapter_tree.text_content()
                        extracted_text += chapter_text + "\n\n"
                    except Exception as e:
                        log.debug("Failed to extract chapter %s: %s", idref, e)
                        continue
            
            return truncate_to_tokens(extracted_text, max_tokens)
            
    except Exception as e:
        log.warning("EPUB extraction failed: %s", e)
        return ""


def extract_pdf_text(pdf_path, max_tokens=2000):
    """Extract text from PDF file."""
    if not use_pdf:
        log.warning("PDF extraction not available: PyPDF not installed")
        return ""
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PdfReader(f)
            extracted_text = ""
            
            # Extract from first 20 pages
            max_pages = min(20, len(pdf_reader.pages))
            for page_num in range(max_pages):
                if estimate_tokens(extracted_text) >= max_tokens:
                    break
                
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n\n"
                except Exception as e:
                    log.debug("Failed to extract PDF page %d: %s", page_num, e)
                    continue
            
            return truncate_to_tokens(extracted_text, max_tokens)
            
    except Exception as e:
        log.warning("PDF extraction failed: %s", e)
        return ""


def extract_txt_text(txt_path, max_tokens=2000):
    """Extract text from TXT file."""
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
            
            return truncate_to_tokens(text_data, max_tokens)
            
    except Exception as e:
        log.warning("TXT extraction failed: %s", e)
        return ""


def extract_text(book_id, max_tokens=2000):
    """
    Extract text from book for AI summary generation.
    
    Args:
        book_id: Book ID from database
        max_tokens: Maximum tokens to extract (default: 2000)
    
    Returns:
        String containing book metadata and extracted text (if available)
    """
    try:
        # Get book from database
        calibre_db = db.CalibreDB()
        book = calibre_db.get_book(book_id)
        if not book:
            log.warning("Book %d not found", book_id)
            return ""
        
        # Get metadata
        metadata = get_book_metadata(book)
        
        # Try to find a supported format (EPUB, PDF, TXT in priority order)
        formats_to_try = ['EPUB', 'PDF', 'TXT']
        extracted_text = ""
        
        for fmt in formats_to_try:
            book_data = calibre_db.get_book_format(book_id, fmt)
            if not book_data:
                continue
            
            # Build file path
            if config.config_use_google_drive:
                # Google Drive not supported for text extraction yet
                log.warning("Google Drive not supported for text extraction")
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
            if fmt_lower == 'epub':
                extracted_text = extract_epub_text(file_path, max_tokens)
            elif fmt_lower == 'pdf':
                extracted_text = extract_pdf_text(file_path, max_tokens)
            elif fmt_lower == 'txt':
                extracted_text = extract_txt_text(file_path, max_tokens)
            
            if extracted_text:
                break
        
        # Combine metadata and extracted text
        if extracted_text:
            return f"{metadata}\n\n---\n\nExtracted Text:\n{extracted_text}"
        else:
            # Return metadata-only if extraction failed or format not supported
            return metadata
            
    except Exception as e:
        log.error("Text extraction failed for book %d: %s", book_id, e)
        # Return metadata-only on error
        try:
            calibre_db = db.CalibreDB()
            book = calibre_db.get_book(book_id)
            if book:
                return get_book_metadata(book)
        except Exception:
            pass
        return ""

