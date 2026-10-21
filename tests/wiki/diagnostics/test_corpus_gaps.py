"""Tests for the corpus gap audit diagnostic."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import pytest

_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, os.path.join(_project_root, "scripts"))

from wiki.diagnostics.corpus_gaps import audit


def _make_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            grade TEXT,
            author TEXT,
            author_uk TEXT DEFAULT '',
            char_count INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE external_articles (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL,
            url TEXT NOT NULL,
            url_normalized TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            domain TEXT,
            char_count INTEGER,
            channel_id TEXT,
            speaker TEXT,
            register_tag TEXT,
            decolonization_tag TEXT,
            quality_tier INTEGER,
            publish_date TEXT,
            duration_s INTEGER,
            chunk_start_ts INTEGER,
            chunk_end_ts INTEGER,
            video_id TEXT
        )
        """
    )
    return conn


def test_existence_check_against_synthetic_corpus(tmp_path):
    db_path = tmp_path / "sources.db"
    conn = _make_db(db_path)
    conn.execute(
        """
        INSERT INTO textbooks (chunk_id, title, text, source_file, grade, author, char_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "tb-1",
            "Phonetics",
            "Українська буква ї завжди позначає два звуки і допомагає чути [йі].",
            "tb.jsonl",
            "2",
            "Автор",
            90,
        ),
    )
    conn.execute(
        """
        INSERT INTO external_articles (
            chunk_id, url, url_normalized, title, text, source_file, domain, char_count,
            channel_id, speaker, register_tag, decolonization_tag, quality_tier,
            publish_date, duration_s, chunk_start_ts, chunk_end_ts, video_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ext-1",
            "https://example.com",
            "https://example.com",
            "History",
            "У правописі 1933 року літеру ґ було вилучено з абетки.",
            "ext.jsonl",
            "example.com",
            72,
            "",
            "",
            "",
            "",
            2,
            "",
            0,
            None,
            None,
            "",
        ),
    )
    conn.commit()

    present = audit.check_concept_coverage(
        conn,
        {
            "concept": "буква ї позначає два звуки",
            "variants": ["буква ї позначає два звуки", "[йі]"],
        },
    )
    missing = audit.check_concept_coverage(
        conn,
        {
            "concept": "неіснуюча прогалина",
            "variants": ["неіснуюча прогалина"],
        },
    )

    assert present["in_textbooks"] is True
    assert present["in_external"] is False
    assert present["textbooks_match_count"] == 1
    assert missing["absent_from_corpus"] is True


def test_concept_extraction_rejects_override_before_preparation(monkeypatch):
    import pytest

    def forbidden(*args, **kwargs):
        raise AssertionError("unauthorized model reached preparation")

    monkeypatch.setattr(audit.tempfile, "TemporaryDirectory", forbidden)
    monkeypatch.setattr(audit.subprocess, "run", forbidden)
    for model in ("gpt-5.5", "unknown", ""):
        with pytest.raises(ValueError, match=r"requires gpt-6\.1-sol"):
            audit.run_codex_concept_extraction("fixture", model=model)


@pytest.mark.needs_artifact("corpus_audit_snapshots", "corpus_audit/coverage_map.json")
def test_load_coverage_map_resolves_the_published_artifact() -> None:
    coverage_map = audit.load_coverage_map()
    assert coverage_map["metadata"]["article_count"] == len(coverage_map["articles"])
    assert audit.classify_gap_categories(coverage_map)


def test_load_coverage_map_fails_closed_when_the_published_map_is_absent(tmp_path: Path, monkeypatch) -> None:
    from scripts.storage import paths

    repo = tmp_path / "repo"
    (repo / "registry/artifacts").mkdir(parents=True)
    manifest = Path(__file__).resolve().parents[3] / "registry/artifacts/corpus_audit_snapshots.manifest.json"
    (repo / "registry/artifacts/corpus_audit_snapshots.manifest.json").write_bytes(manifest.read_bytes())
    monkeypatch.setattr(audit, "artifact_path", lambda group, rel: paths.artifact_path(group, rel, repo=repo))
    with pytest.raises(paths.MissingArtifactError, match="artifacts hydrate --group corpus_audit_snapshots"):
        audit.load_coverage_map()
    with pytest.raises(paths.MissingArtifactError):
        audit.load_coverage_map(Path(audit.COVERAGE_MAP_PATH.relative_to(audit.PROJECT_ROOT)).resolve())


def test_load_coverage_map_reads_the_present_published_map(tmp_path: Path, monkeypatch) -> None:
    import hashlib
    import json
    import subprocess

    from scripts.storage import paths

    repo = tmp_path / "repo"
    (repo / "registry/artifacts").mkdir(parents=True)
    (repo / "data/corpus_audit").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=30)
    payload = b'{"articles": [], "metadata": {"article_count": 0}}'
    (repo / "data/corpus_audit/coverage_map.json").write_bytes(payload)
    manifest_file = Path(__file__).resolve().parents[3] / "registry/artifacts/corpus_audit_snapshots.manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    entry = next(item for item in manifest["entries"] if item["path"] == "data/corpus_audit/coverage_map.json")
    digest = hashlib.sha256(payload).hexdigest()
    entry.update(sha256=digest, store=digest, size=len(payload))
    manifest["entries"] = [entry]
    (repo / "registry/artifacts/corpus_audit_snapshots.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setenv("LU_ARTIFACT_STORE", str(tmp_path / "store"))
    monkeypatch.setattr(audit, "artifact_path", lambda group, rel: paths.artifact_path(group, rel, repo=repo))
    assert audit.load_coverage_map() == {"articles": [], "metadata": {"article_count": 0}}


@pytest.mark.parametrize("module_name", ["classify", "report"])
def test_default_cli_writes_nothing_when_the_published_map_is_absent(tmp_path: Path, monkeypatch, module_name: str) -> None:
    import importlib

    from scripts.storage import paths

    module = importlib.import_module(f"wiki.diagnostics.corpus_gaps.{module_name}")
    output = tmp_path / "out.md"

    def missing(group: str, rel: str) -> Path:
        raise paths.MissingArtifactError(group, rel, "hydrate")

    monkeypatch.setattr(audit, "artifact_path", missing)
    argv = [module_name, "--output", str(output)]
    if module_name == "report":
        articles = tmp_path / "article_concepts.json"
        articles.write_text("{}", encoding="utf-8")
        argv += ["--article-concepts", str(articles)]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(paths.MissingArtifactError):
        module.main()
    assert not output.exists()
