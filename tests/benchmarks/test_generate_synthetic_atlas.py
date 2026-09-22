"""Tests for the seeded synthetic Atlas dataset generator (#8307)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas.atlas_db import SCHEMA
from scripts.benchmarks.generate_synthetic_atlas import build_synthetic_db, main, parse_args


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_source_db(path: Path, article_count: int = 24) -> Path:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO manifest_metadata(key, value_json) VALUES (?,?)",
        ("version", json.dumps("0.1")),
    )
    cur.execute(
        "INSERT INTO manifest_metadata(key, value_json) VALUES (?,?)",
        ("generated_at", json.dumps("2026-09-11T10:12:36+00:00")),
    )
    for i in range(article_count):
        slug = f"слово-{i:03d}"
        cefr = "A1" if i % 2 == 0 else None
        enrichment = {"cefr": {"level": cefr}} if cefr else {}
        payload = {
            "lemma": f"слово {i}",
            "url_slug": slug,
            "gloss": f"word {i}",
            "pos": "noun",
            "enrichment": enrichment,
        }
        cur.execute(
            "INSERT INTO articles(slug, display_head, lemma, entry_type, pos, gloss,"
            " review_state, visibility, cefr, heritage_classification, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                slug,
                f"слово {i}",
                f"слово {i}",
                "lemma",
                "noun",
                f"word {i}",
                "approved",
                "public",
                cefr,
                "unknown",
                "2026-01-01",
                "2026-01-01",
            ),
        )
        cur.execute(
            "INSERT INTO article_payloads(slug, route_order, payload_json, is_public_route) VALUES (?,?,?,?)",
            (slug, i, json.dumps(payload, ensure_ascii=False), 1),
        )
        cur.execute(
            "INSERT INTO aliases(alias, kind, source, target_slug, visibility) VALUES (?,?,?,?,?)",
            (f"slovo-{i:03d}", "transliteration", "test", slug, "public"),
        )
        cur.execute(
            "INSERT INTO enrichment(slug, section, payload_json, source, filled_at, phase) VALUES (?,?,?,?,?,?)",
            (slug, "meaning", json.dumps({"items": [f"def {i}"]}, ensure_ascii=False), "test", "2026-01-01", "local"),
        )
        cur.execute(
            "INSERT INTO article_provenance(slug, source_family, source_locator, extraction_mode) VALUES (?,?,?,?)",
            (slug, "test", "fixture", "test_fixture"),
        )
    # one form-of route payload: a public route with no articles row
    form_payload = {"lemma": "словеса", "url_slug": "словеса", "gloss": "words", "pos": "noun"}
    cur.execute(
        "INSERT INTO article_payloads(slug, route_order, payload_json, is_public_route) VALUES (?,?,?,?)",
        ("словеса", 9000, json.dumps(form_payload, ensure_ascii=False), 1),
    )
    cur.execute(
        """INSERT INTO articles_fts(slug, display_head, lemma, gloss, aliases)
           SELECT a.slug, a.display_head, a.lemma, COALESCE(a.gloss,''),
                  COALESCE((SELECT group_concat(al.alias, ' ') FROM aliases al WHERE al.target_slug = a.slug), '')
           FROM articles a"""
    )
    conn.commit()
    conn.close()
    return path


def _export_gate_counts(db_path: Path) -> dict[str, int]:
    """The hard gates from scripts/atlas/export_runtime_shards.py."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        reviewed = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE review_state = 'approved' AND visibility = 'public'"
        ).fetchone()[0]
        public_routes = conn.execute("SELECT COUNT(*) FROM article_payloads WHERE is_public_route = 1").fetchone()[0]
        form_of = conn.execute(
            """SELECT COUNT(*) FROM article_payloads AS payload
               LEFT JOIN articles AS article ON article.slug = payload.slug
               WHERE payload.is_public_route = 1 AND article.slug IS NULL"""
        ).fetchone()[0]
        invalid_aliases = conn.execute(
            """SELECT COUNT(*) FROM aliases AS alias
               LEFT JOIN articles AS article ON article.slug = alias.target_slug
               WHERE alias.visibility = 'public'
                 AND (article.slug IS NULL OR article.review_state != 'approved'
                      OR article.visibility != 'public')"""
        ).fetchone()[0]
        return {
            "reviewed": reviewed,
            "public_routes": public_routes,
            "form_of": form_of,
            "invalid_aliases": invalid_aliases,
        }
    finally:
        conn.close()


def test_same_seed_produces_byte_identical_dataset(tmp_path: Path) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out_a = tmp_path / "synthetic-a.db"
    out_b = tmp_path / "synthetic-b.db"
    summary_a = build_synthetic_db(source_db=source, out=out_a, seed=8307, target_articles=200)
    summary_b = build_synthetic_db(source_db=source, out=out_b, seed=8307, target_articles=200)
    assert _sha256(out_a) == _sha256(out_b)
    assert summary_a["sha256"] == summary_b["sha256"]


def test_different_seeds_produce_different_datasets(tmp_path: Path) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out_a = tmp_path / "seed-a.db"
    out_b = tmp_path / "seed-b.db"
    build_synthetic_db(source_db=source, out=out_a, seed=1, target_articles=500)
    build_synthetic_db(source_db=source, out=out_b, seed=2, target_articles=500)
    assert _sha256(out_a) != _sha256(out_b)


def test_synthetic_db_hits_target_and_satisfies_export_gates(tmp_path: Path) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out = tmp_path / "synthetic.db"
    summary = build_synthetic_db(source_db=source, out=out, seed=8307, target_articles=137)
    assert summary["articles"] == 137
    gates = _export_gate_counts(out)
    assert gates["reviewed"] == 137
    assert gates["reviewed"] == gates["public_routes"] - gates["form_of"]
    assert gates["invalid_aliases"] == 0
    assert gates["form_of"] >= 1  # natural-ratio form-of route copies preserved


def test_dataset_is_marked_synthetic(tmp_path: Path) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out = tmp_path / "synthetic.db"
    build_synthetic_db(source_db=source, out=out, seed=42, target_articles=60)
    conn = sqlite3.connect(f"file:{out}?mode=ro", uri=True)
    try:
        metadata = dict(conn.execute("SELECT key, value_json FROM manifest_metadata"))
        assert json.loads(metadata["dataset_kind"]) == "synthetic-resample"
        assert json.loads(metadata["synthetic_seed"]) == 42
        copy_count = conn.execute("SELECT COUNT(*) FROM articles WHERE slug LIKE '%--syn%'").fetchone()[0]
        assert copy_count == 60 - 24
        marked = conn.execute(
            "SELECT COUNT(*) FROM article_provenance WHERE extraction_mode = 'synthetic_resample'"
        ).fetchone()[0]
        assert marked == copy_count
        # copied payloads carry the new slug, not the source slug
        slug, payload_json = conn.execute(
            "SELECT slug, payload_json FROM article_payloads WHERE slug LIKE '%--syn%' LIMIT 1"
        ).fetchone()
        assert json.loads(payload_json)["url_slug"] == slug
    finally:
        conn.close()


def test_downscale_target_below_source(tmp_path: Path) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out = tmp_path / "small.db"
    summary = build_synthetic_db(source_db=source, out=out, seed=7, target_articles=5)
    assert summary["articles"] == 5
    gates = _export_gate_counts(out)
    assert gates["reviewed"] == gates["public_routes"] - gates["form_of"]
    assert gates["invalid_aliases"] == 0


def test_cli_help_and_parse() -> None:
    with pytest.raises(SystemExit) as excinfo:
        parse_args(["--help"])
    assert excinfo.value.code == 0
    args = parse_args(["--seed", "9", "--target", "100"])
    assert args.seed == 9
    assert args.target == 100


def test_main_runs_end_to_end(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out = tmp_path / "cli.db"
    rc = main(["--source-db", str(source), "--out", str(out), "--seed", "3", "--target", "30"])
    assert rc == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["articles"] == 30
    assert summary["sha256"] == _sha256(out)
