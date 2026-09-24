"""Tests for the seeded synthetic Atlas dataset generator (#8307)."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas.atlas_db import SCHEMA
from scripts.atlas.export_runtime_shards import export_runtime_shards
from scripts.benchmarks.generate_synthetic_atlas import build_synthetic_db, main, parse_args


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sampled_slugs(path: Path) -> list[str]:
    """Compare the chosen copy sequence, independently of seed metadata."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return [row[0] for row in conn.execute(
            "SELECT slug FROM articles WHERE slug LIKE '%--syn%' ORDER BY substr(slug, -7)"
        )]
    finally:
        conn.close()


def _make_source_db(path: Path, article_count: int = 24, *, varied_form_shapes: bool = False) -> Path:
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
        slug = "автобус" if i == article_count - 1 else f"слово-{i:03d}"
        lemma = "автобус" if i == article_count - 1 else f"слово {i}"
        cefr = "A1" if i % 2 == 0 else None
        enrichment = {"cefr": {"level": cefr}} if cefr else {}
        payload = {
            "lemma": lemma,
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
                lemma,
                lemma,
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
    # A forward relation exercises deferred FK enforcement during generation.
    cur.execute(
        "INSERT INTO related_entries(slug, related_slug, entry_type, relation, component_role, provenance)"
        " VALUES (?,?,?,?,?,?)",
        ("слово-000", "автобус", "lemma", "related", None, "verified"),
    )
    # A real Atlas form route has no articles row and links to a lemma article.
    form_payload = {
        "lemma": "автобусом",
        "url_slug": "автобусом",
        "gloss": "by bus",
        "pos": "instrument",
        "form_of": {"lemma": "автобус", "url_slug": "автобус"},
    }
    cur.execute(
        "INSERT INTO article_payloads(slug, route_order, payload_json, is_public_route) VALUES (?,?,?,?)",
        ("автобусом", 9000, json.dumps(form_payload, ensure_ascii=False), 1),
    )
    if varied_form_shapes:
        for order, (slug, form_of) in enumerate(
            (
                ("form-string", "автобус"),
                ("form-lemma", {"lemma": "автобус"}),
                ("form-unresolved", {"url_slug": "missing-target", "lemma": "автобус"}),
            ),
            start=9001,
        ):
            payload = {"lemma": slug, "url_slug": slug, "form_of": form_of}
            cur.execute(
                "INSERT INTO article_payloads(slug, route_order, payload_json, is_public_route) VALUES (?,?,?,?)",
                (slug, order, json.dumps(payload, ensure_ascii=False), 1),
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


def _assert_form_targets_resolve(db_path: Path) -> int:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        articles = {row[0] for row in conn.execute("SELECT slug FROM articles")}
        routes = conn.execute(
            """SELECT payload.slug, payload.payload_json FROM article_payloads AS payload
               LEFT JOIN articles AS article ON article.slug = payload.slug
               WHERE payload.is_public_route = 1 AND article.slug IS NULL"""
        ).fetchall()
        for slug, raw in routes:
            payload = json.loads(raw)
            assert payload["url_slug"] == slug
            assert payload["form_of"]["url_slug"] in articles
        return len(routes)
    finally:
        conn.close()


def _form_payloads(db_path: Path) -> dict[str, dict]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return {
            slug: json.loads(raw)
            for slug, raw in conn.execute(
                """SELECT payload.slug, payload.payload_json FROM article_payloads AS payload
                   LEFT JOIN articles AS article ON article.slug = payload.slug
                   WHERE article.slug IS NULL AND payload.is_public_route = 1"""
            )
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
    assert _sampled_slugs(out_a) == _sampled_slugs(out_b)


def test_different_seeds_produce_different_datasets(tmp_path: Path) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out_a = tmp_path / "seed-a.db"
    out_b = tmp_path / "seed-b.db"
    build_synthetic_db(source_db=source, out=out_a, seed=1, target_articles=500)
    build_synthetic_db(source_db=source, out=out_b, seed=2, target_articles=500)
    assert _sampled_slugs(out_a) != _sampled_slugs(out_b)


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
    assert _assert_form_targets_resolve(out) == gates["form_of"]
    conn = sqlite3.connect(out)
    try:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("SELECT COUNT(*) FROM related_entries").fetchone()[0] > 0
    finally:
        conn.close()
    report = export_runtime_shards(db_path=out, out_dir=tmp_path / "runtime", include_decks=False, verify=True)
    assert report["counts"]["articles"] == 137


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


@pytest.mark.parametrize("seed,expected_form_routes", [(1, 0), (3, 1)])
def test_downscale_target_below_source(tmp_path: Path, seed: int, expected_form_routes: int) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out = tmp_path / "small.db"
    summary = build_synthetic_db(source_db=source, out=out, seed=seed, target_articles=13)
    assert summary["articles"] == 13
    gates = _export_gate_counts(out)
    assert gates["reviewed"] == gates["public_routes"] - gates["form_of"]
    assert gates["invalid_aliases"] == 0
    assert _assert_form_targets_resolve(out) == expected_form_routes
    conn = sqlite3.connect(out)
    try:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        conn.close()
    report = export_runtime_shards(db_path=out, out_dir=tmp_path / "runtime", include_decks=False, verify=True)
    assert report["counts"]["articles"] == 13
    assert report["counts"]["formRoutes"] == expected_form_routes


def test_varied_public_form_routes_upscale_and_downscale(tmp_path: Path) -> None:
    source = _make_source_db(tmp_path / "source.db", varied_form_shapes=True)
    source_forms = _form_payloads(source)
    assert len(source_forms) == 4

    up = tmp_path / "up.db"
    up_summary = build_synthetic_db(source_db=source, out=up, seed=8307, target_articles=48)
    up_forms = _form_payloads(up)
    assert up_summary["form_routes"] == len(up_forms) == 8  # 4 originals + 4 natural-ratio copies
    assert {slug: up_forms[slug] for slug in source_forms} == source_forms
    for slug, payload in up_forms.items():
        if "--syn" in slug:
            assert payload["url_slug"] == slug
            assert payload["form_of"] == source_forms[slug.split("--syn", 1)[0]]["form_of"]
    up_report = export_runtime_shards(db_path=up, out_dir=tmp_path / "up-runtime", include_decks=False, verify=True)
    assert up_report["counts"]["formRoutes"] == 8

    down = tmp_path / "down.db"
    down_summary = build_synthetic_db(source_db=source, out=down, seed=3, target_articles=23)
    down_forms = _form_payloads(down)
    assert down_summary["downscale_form_eligible"] == 3
    assert down_summary["downscale_form_skipped_unresolved"] == 1
    assert down_summary["downscale_form_skipped_target"] == 0
    assert {slug.split("--syn", 1)[0] for slug in down_forms} == {"автобусом", "form-string", "form-lemma"}
    for slug, payload in down_forms.items():
        assert payload["url_slug"] == slug
        assert payload["form_of"] == source_forms[slug.split("--syn", 1)[0]]["form_of"]
    assert down_summary["form_routes"] == len(down_forms) == 3
    down_report = export_runtime_shards(
        db_path=down, out_dir=tmp_path / "down-runtime", include_decks=False, verify=True
    )
    assert down_report["counts"]["formRoutes"] == 3

    no_target = tmp_path / "no-target.db"
    skipped = build_synthetic_db(source_db=source, out=no_target, seed=1, target_articles=13)
    assert skipped["downscale_form_eligible"] == 0
    assert skipped["downscale_form_skipped_unresolved"] == 1
    assert skipped["downscale_form_skipped_target"] == 3
    assert skipped["form_routes"] == 0
    no_target_report = export_runtime_shards(
        db_path=no_target, out_dir=tmp_path / "no-target-runtime", include_decks=False, verify=True
    )
    assert no_target_report["counts"]["formRoutes"] == 0


@pytest.mark.parametrize("valid_sqlite", [True, False])
def test_existing_non_synthetic_output_is_preserved(tmp_path: Path, valid_sqlite: bool) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out = tmp_path / "public.db"
    if valid_sqlite:
        shutil.copyfile(source, out)
    else:
        out.write_bytes(b"public dataset")
    before = out.read_bytes()
    with pytest.raises(ValueError, match="refusing to overwrite"):
        build_synthetic_db(source_db=source, out=out, seed=1, target_articles=30)
    assert out.read_bytes() == before


@pytest.mark.parametrize("alias_kind", ["same", "normalized", "symlink", "hardlink"])
def test_source_alias_output_is_refused_and_preserved(tmp_path: Path, alias_kind: str) -> None:
    source = _make_source_db(tmp_path / "source.db")
    before = _sha256(source)
    if alias_kind == "same":
        out = source
    elif alias_kind == "normalized":
        (tmp_path / "nested").mkdir()
        out = tmp_path / "nested" / ".." / "source.db"
    else:
        out = tmp_path / f"{alias_kind}.db"
        if alias_kind == "symlink":
            out.symlink_to(source)
        else:
            out.hardlink_to(source)
    with pytest.raises(ValueError, match="output must not be the source DB"):
        build_synthetic_db(source_db=source, out=out, seed=1, target_articles=30)
    assert _sha256(source) == before
    assert _sha256(out) == before


def test_existing_synthetic_output_can_be_replaced_atomically(tmp_path: Path) -> None:
    source = _make_source_db(tmp_path / "source.db")
    out = tmp_path / "synthetic.db"
    build_synthetic_db(source_db=source, out=out, seed=1, target_articles=30)
    before = _sha256(out)
    with pytest.raises(ValueError, match="target_articles"):
        build_synthetic_db(source_db=source, out=out, seed=2, target_articles=0)
    assert _sha256(out) == before
    assert list(tmp_path.glob(".synthetic.db.*")) == []
    build_synthetic_db(source_db=source, out=out, seed=2, target_articles=30)
    assert _sha256(out) != before


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
