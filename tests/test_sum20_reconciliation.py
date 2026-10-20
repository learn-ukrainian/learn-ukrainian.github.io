"""Read-only reconciliation of synthetic article inventories (#10655)."""

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.lexicon import reconcile_sum20 as report


def _stores(tmp_path: Path) -> tuple[Path, Path]:
    staging = tmp_path / "staging.db"
    official = tmp_path / "official.db"
    with sqlite3.connect(staging) as conn:
        conn.execute("CREATE TABLE sum20_slovnyk_articles (lemma, headword, text)")
        conn.executemany("INSERT INTO sum20_slovnyk_articles VALUES (?, ?, ?)", [
            ("MATCH", "MATCH", "identical"),
            ("changed", "CHANGED", "staging text"),
            ("extra", "EXTRA", "extra text"),
            ("duplicate", "DUPLICATE", "first"),
            ("duplicate", "DUPLICATE", "second"),
        ])
    with sqlite3.connect(official) as conn:
        conn.execute("CREATE TABLE sum20_articles (normalized_lookup_key, headword, article_text)")
        conn.executemany("INSERT INTO sum20_articles VALUES (?, ?, ?)", [
            ("match", "MATCH", "identical"),
            ("changed", "CHANGED", "official text"),
            ("missing", "MISSING", "missing text"),
            ("duplicate", "DUPLICATE", "first"),
        ])
    return staging, official


def test_report_compares_identity_and_full_payloads_without_writes(tmp_path, monkeypatch):
    staging, official = _stores(tmp_path)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    def forbidden(*args, **kwargs):
        raise AssertionError("reconciliation attempted network access")

    monkeypatch.setattr("socket.socket", forbidden)
    result = report.reconcile_sum20(staging, official, repository_root=tmp_path)
    assert result == {
        "identity": "normalized_article_key",
        "comparison_fields": ["headword", "article_text"],
        "counts": {
            "staging_records": 5, "official_records": 4,
            "staging_identities": 4, "official_identities": 4,
            "shared": 3, "matching": 1, "missing": 1, "extra": 1, "differing": 2,
            "staging_duplicate_identities": 1, "official_duplicate_identities": 0,
        },
        "missing": ["missing"], "extra": ["extra"], "differing": ["changed", "duplicate"],
    }
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_cli_emits_only_counts_unless_details_requested(tmp_path, capsys):
    staging, official = _stores(tmp_path)
    args = ["--repository-root", str(tmp_path), "--staging", str(staging), "--official", str(official)]
    assert report.main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["counts"]["differing"] == 2
    assert set(result) == {"identity", "comparison_fields", "counts"}
    assert report.main([*args, "--details"]) == 0
    assert json.loads(capsys.readouterr().out)["missing"] == ["missing"]


def test_cli_refuses_invalid_store_without_leaking_paths(tmp_path, capsys):
    assert report.main(["--repository-root", str(tmp_path), "--staging", str(tmp_path / "missing.db")]) == 2
    assert json.loads(capsys.readouterr().out) == {"status": "refused", "reason": "store_missing"}
    assert list(tmp_path.iterdir()) == []


def test_cli_refuses_wrong_schema(tmp_path, capsys):
    staging, official = _stores(tmp_path)
    assert report.main([
        "--repository-root", str(tmp_path), "--staging", str(official), "--official", str(staging)
    ]) == 2
    assert json.loads(capsys.readouterr().out) == {"status": "refused", "reason": "invalid_article_schema"}


def test_cli_help_explains_report_only_contract(capsys):
    with pytest.raises(SystemExit) as exc:
        report.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for text in ("Outputs:", "Exit codes:", "Related:", "--details", "never applies changes"):
        assert text in help_text


def test_inventory_refuses_missing_article_identity(tmp_path):
    staging, official = _stores(tmp_path)
    with sqlite3.connect(staging) as conn:
        conn.execute("INSERT INTO sum20_slovnyk_articles VALUES ('', 'HEAD', 'text')")
    with pytest.raises(report.Sum20StoreError, match="article_identity_missing"):
        report.reconcile_sum20(staging, official, repository_root=tmp_path)
