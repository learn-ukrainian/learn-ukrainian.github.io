"""Tests for the ``--allow-verify-markers`` advisory downgrade of the wiki
compile VERIFY-marker write-block.

Default behaviour: a writer-inserted ``<!-- VERIFY -->`` marker is a hard
write-block — the article is NOT written (so a wrong-subject wiki that the
recompile was meant to replace is preserved). The opt-in advisory mode writes
the corrected article and logs the surviving markers as review TODOs.

Hermetic: ``_write_article_bundle_atomic`` with ``sources=[]`` builds a ``None``
registry, so no sources DB is touched.
"""

import os
import sys
from pathlib import Path

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))

MARKED = "# Заголовок\n\nКлавдія Латишева <!-- VERIFY: дата народження -->\n"
CLEAN = "# Заголовок\n\nЧистий текст без жодних маркерів.\n"


def test_default_gate_blocks_verify_marker(tmp_path: Path) -> None:
    """Without the flag, a surviving VERIFY marker raises and nothing is written."""
    from wiki.compiler import _write_article_bundle_atomic

    article_path = tmp_path / "figure.md"
    with pytest.raises(ValueError, match="VERIFY marker survivor"):
        _write_article_bundle_atomic(article_path, article_text=MARKED, sources=[])
    assert not article_path.exists()


def test_advisory_writes_despite_verify_marker(tmp_path: Path, capsys) -> None:
    """With allow_verify_markers, the article IS written and the marker logged."""
    from wiki.compiler import _write_article_bundle_atomic

    article_path = tmp_path / "figure.md"
    _write_article_bundle_atomic(
        article_path, article_text=MARKED, sources=[], allow_verify_markers=True
    )
    assert article_path.exists()
    assert "<!-- VERIFY:" in article_path.read_text("utf-8")
    out = capsys.readouterr().out
    assert "ADVISORY" in out


def test_clean_text_writes_in_both_modes(tmp_path: Path) -> None:
    """Marker-free text is written regardless of the flag (no false blocking)."""
    from wiki.compiler import _write_article_bundle_atomic

    strict = tmp_path / "strict.md"
    _write_article_bundle_atomic(strict, article_text=CLEAN, sources=[])
    assert strict.exists()

    advisory = tmp_path / "advisory.md"
    _write_article_bundle_atomic(
        advisory, article_text=CLEAN, sources=[], allow_verify_markers=True
    )
    assert advisory.exists()
