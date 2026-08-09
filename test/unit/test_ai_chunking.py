# -*- coding: utf-8 -*-
"""
Unit tests for chapter-aware book chunking (no LLM / API key / Flask app).

Run from repo root:
  python3 -m unittest test.unit.test_ai_chunking
"""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[2]


def _load_chunking_module():
    """Load cps.ai.chunking without importing the real Flask cps package."""
    if "cps.ai.chunking" in sys.modules:
        return sys.modules["cps.ai.chunking"]

    # Third-party imports used at module import time
    for name in ("chardet", "lxml", "lxml.etree", "lxml.html"):
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)

    cps = types.ModuleType("cps")
    cps.__path__ = []
    cps.config = MagicMock()
    logger = MagicMock()
    logger.create = MagicMock(return_value=MagicMock())
    cps.logger = logger
    cps.db = MagicMock()
    sys.modules["cps"] = cps

    ub = types.ModuleType("cps.ub")
    ub.session = MagicMock()
    ub.BookChunk = type("BookChunk", (), {})
    ub.BookIndexStatus = type("BookIndexStatus", (), {})
    sys.modules["cps.ub"] = ub
    cps.ub = ub

    ai = types.ModuleType("cps.ai")
    ai.__path__ = []
    sys.modules["cps.ai"] = ai

    path = ROOT / "cps" / "ai" / "chunking.py"
    spec = importlib.util.spec_from_file_location("cps.ai.chunking", path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "cps.ai"
    sys.modules["cps.ai.chunking"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestSplitTextWithinChapters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chunking = _load_chunking_module()

    def test_no_chapters_matches_flat_split(self):
        text = "Para one.\n\nPara two.\n\nPara three.\n\n"
        flat = self.chunking.split_text_into_chunks(text, 8, 1)
        nested = self.chunking.split_text_within_chapters(text, [], 8, 1)
        self.assertEqual([c["text"] for c in flat], [c["text"] for c in nested])

    def test_chunks_do_not_cross_chapter_boundaries(self):
        ch1 = "Alpha only here.\n\nStill alpha.\n\n"
        ch2 = "Beta only here.\n\nStill beta.\n\n"
        full = ch1 + ch2
        chapters = [
            ("Chapter Alpha", 0, len(ch1)),
            ("Chapter Beta", len(ch1), len(full)),
        ]
        chunks = self.chunking.split_text_within_chapters(
            full, chapters, chunk_size_tokens=5, chunk_overlap_tokens=1
        )
        self.assertTrue(chunks)
        titles = {c["chapter_title"] for c in chunks}
        self.assertEqual(titles, {"Chapter Alpha", "Chapter Beta"})
        for c in chunks:
            text = c["text"]
            if c["chapter_title"] == "Chapter Alpha":
                self.assertNotIn("Beta", text)
            if c["chapter_title"] == "Chapter Beta":
                self.assertNotIn("Alpha", text)

    def test_long_chapter_yields_multiple_same_title_chunks(self):
        # Many short paragraphs so tiny token budget forces several chunks
        paras = "\n\n".join(f"Sentence number {i} about topic." for i in range(20))
        ch1 = paras + "\n\n"
        ch2 = "Other chapter marker word UNIQUEBETA.\n\n"
        full = ch1 + ch2
        chapters = [
            ("Long Chapter", 0, len(ch1)),
            ("Short Chapter", len(ch1), len(full)),
        ]
        chunks = self.chunking.split_text_within_chapters(
            full, chapters, chunk_size_tokens=10, chunk_overlap_tokens=2
        )
        long_chunks = [c for c in chunks if c["chapter_title"] == "Long Chapter"]
        self.assertGreaterEqual(len(long_chunks), 2)
        for c in long_chunks:
            self.assertNotIn("UNIQUEBETA", c["text"])

    def test_overlap_does_not_pull_prior_chapter_text(self):
        ch1 = "ENDMARK chapter one final words.\n\n"
        ch2 = "Start of chapter two content here.\n\nMore chapter two.\n\n"
        full = ch1 + ch2
        chapters = [
            ("One", 0, len(ch1)),
            ("Two", len(ch1), len(full)),
        ]
        chunks = self.chunking.split_text_within_chapters(
            full, chapters, chunk_size_tokens=8, chunk_overlap_tokens=20
        )
        two_chunks = [c for c in chunks if c["chapter_title"] == "Two"]
        self.assertTrue(two_chunks)
        for c in two_chunks:
            self.assertNotIn("ENDMARK", c["text"])


if __name__ == "__main__":
    unittest.main()
