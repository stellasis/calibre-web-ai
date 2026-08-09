# This fork (stellasis/calibre-web-ai)

Public fork of [bluesam1/calibre-web-ai](https://github.com/bluesam1/calibre-web-ai) (itself a fork of [janeczku/calibre-web](https://github.com/janeczku/calibre-web) with AI features).

```
janeczku/calibre-web
        ▲
bluesam1/calibre-web-ai     ← upstream for AI work
        ▲
stellasis/calibre-web-ai    ← this repo
```

## Remotes (recommended)

```bash
git remote add upstream https://github.com/bluesam1/calibre-web-ai.git
# origin = your fork (stellasis/calibre-web-ai)
```

## Notable changes here

- **EPUB chapter-aware chunking** (`cps/ai/chunking.py`): chunks do not cross spine/chapter boundaries; paragraph pack + overlap still apply *within* a chapter. PDF/TXT unchanged (flat split).
- **Unit tests** under `test/unit/` (no LLM / API key). EPUB fixture: Project Gutenberg #84 (*Frankenstein*, public domain) in `test/fixtures/`.
- **Agent rule** `.cursor/rules/tests-with-code.mdc`: behaviour changes should ship with tests.

```bash
pip install 'lxml>=4' 'chardet>=5'   # for EPUB extract test
PYTHONPATH=. python3 -m unittest discover -s test/unit -p 'test_*.py' -v
```

## Contributing upstream

Open PRs against **bluesam1/calibre-web-ai** for AI/indexing changes. Vanilla Calibre-Web issues/PRs belong on janeczku.

After indexing logic changes, existing full-book indexes may need a **re-index** so chunk boundaries match the new rules.
