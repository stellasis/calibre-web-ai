# Test fixtures

## `pg84_frankenstein.epub`

[Project Gutenberg #84](https://www.gutenberg.org/ebooks/84) — *Frankenstein* (Shelley).  
Public domain in the USA. Downloaded as **EPUB (no images)**.

Used to exercise real spine/chapter extraction + chapter-aware chunking  
(Chapter 1 vs Chapter 2 markers in `test/unit/test_ai_chunking.py`).

Re-download:

```bash
curl -fsSL -A 'calibre-web-ai-tests/1.0' \
  -o test/fixtures/pg84_frankenstein.epub \
  'https://www.gutenberg.org/ebooks/84.epub.noimages'
```
