"""Sealed PR1 fixtures are rewritten only with an explicit flag (#9001)."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from scripts.lexicon.runner import generate_pr1_fixture as gen

_SEALED = {
    "baseline_enriched.json": b'{"sealed": true}\n',
    "baseline.sha256": b"abc\n",
    "GENERATION.md": b"do not touch\n",
    "slice_input.json": b'{"entries": []}\n',
    "grac_frequency_slice.json": b"{}\n",
    "kaikki_slice.json": b"{}\n",
}


def _isolate_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fixtures = tmp_path / "fixtures"
    fixture_dir = fixtures / "runner_pr1"
    fixture_dir.mkdir(parents=True)
    monkeypatch.setattr(gen, "FIXTURES_ROOT", fixtures)
    monkeypatch.setattr(gen, "FIXTURE_DIR", fixture_dir)
    return fixture_dir


def test_resolve_sources_slice_writes_only_outside_the_fixture_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture_dir = _isolate_fixture(tmp_path, monkeypatch)
    (fixture_dir / "baseline.sha256").write_text("sealed\n", encoding="utf-8")
    dest = tmp_path / "work"

    path = gen.resolve_sources_slice(dest)

    assert path == (dest / gen.SOURCES_SLICE_NAME).resolve()
    assert path.is_file()
    assert path.stat().st_size > 0
    assert sorted(item.name for item in fixture_dir.iterdir()) == ["baseline.sha256"]


def test_resolve_sources_slice_refuses_the_fixture_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_dir = _isolate_fixture(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="tests/fixtures"):
        gen.resolve_sources_slice(fixture_dir)


def test_resolve_sources_slice_reuses_an_existing_checkout_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture_dir = _isolate_fixture(tmp_path, monkeypatch)
    existing = fixture_dir / gen.SOURCES_SLICE_NAME
    existing.write_bytes(b"already-there")
    dest = tmp_path / "work"

    assert gen.resolve_sources_slice(dest) == existing
    assert existing.read_bytes() == b"already-there"
    assert not dest.exists()


def test_default_command_does_not_rewrite_sealed_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_dir = _isolate_fixture(tmp_path, monkeypatch)
    for name, body in _SEALED.items():
        (fixture_dir / name).write_bytes(body)
    monkeypatch.delenv("LEXICON_SLOVNYK_OFFLINE", raising=False)

    assert gen.main([]) == 0

    for name, body in _SEALED.items():
        assert (fixture_dir / name).read_bytes() == body
    assert (fixture_dir / gen.SOURCES_SLICE_NAME).is_file()
    assert "LEXICON_SLOVNYK_OFFLINE" not in os.environ
    conn = sqlite3.connect(fixture_dir / gen.SOURCES_SLICE_NAME)
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert "slovnyk_cache" in tables
        assert "sum11" not in tables
        # 50 reciprocal synonym pairs (100 documents) + 25 one-way antonym sources.
        assert conn.execute("SELECT COUNT(*) FROM slovnyk_cache").fetchone()[0] == 125
        document = json.loads(conn.execute("SELECT document FROM slovnyk_cache LIMIT 1").fetchone()[0])
        newsum = document["lookups"]["newsum"]
        assert newsum["word"]
        assert newsum["text"]
        assert "source_url" not in newsum
    finally:
        conn.close()


def test_write_sealed_is_explicit_and_restores_offline_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture_dir = _isolate_fixture(tmp_path, monkeypatch)
    monkeypatch.delenv("LEXICON_SLOVNYK_OFFLINE", raising=False)

    assert gen.main(["--write-sealed"]) == 0

    for name in ("baseline_enriched.json", "baseline.sha256", "GENERATION.md", "slice_input.json"):
        assert (fixture_dir / name).is_file()
    note = (fixture_dir / "GENERATION.md").read_text(encoding="utf-8")
    assert "--write-sealed" in note
    assert (fixture_dir / gen.SOURCES_SLICE_NAME).is_file()
    assert "LEXICON_SLOVNYK_OFFLINE" not in os.environ


def test_help_states_when_sealed_files_are_written(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        gen.main(["--help"])

    assert caught.value.code == 0
    help_text = capsys.readouterr().out
    assert "--write-sealed" in help_text
    assert "--sources-out" in help_text
    assert "Exit codes:" in help_text
    assert "tests must not" in help_text.lower() or "Never set this from a test" in help_text
