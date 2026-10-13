"""API preload must survive a closed PyMuPDF message stream.

Importing the deprecated ``fitz`` alias calls ``pymupdf.message_warning``,
which writes to the stream PyMuPDF captured at its own import. Pytest capture
can close that stream before a later ``api_client`` lifespan runs
``preload_all()``.
"""

from __future__ import annotations

import io
import sys

import pytest


def test_preload_all_completes_when_pymupdf_message_stream_is_closed(monkeypatch):
    pymupdf = pytest.importorskip("pymupdf")
    from scripts.api.preload import OPTIONAL_MODULES, preload_all

    closed = io.StringIO()
    closed.close()
    monkeypatch.setattr(pymupdf, "_g_out_message", closed)
    previous = sys.modules.pop("fitz", None)
    try:
        preload_all()
        assert "fitz" not in OPTIONAL_MODULES
        assert "fitz" not in sys.modules
    finally:
        if previous is not None and "fitz" not in sys.modules:
            sys.modules["fitz"] = previous
