"""Acceptance tests for the Atlas runtime shard exporter (PR #1 contract).

Core contract tests run against a committed hermetic fixture DB so CI does not
depend on the ~149 MB ``data/atlas.db``. Real-DB count assertions remain
opt-in via ``skipif`` when the full atlas is present locally.
"""

from __future__ import annotations

import ctypes
import dataclasses
import gzip
import hashlib
import io
import json
import mmap
import os
import random
import re
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import unicodedata
import zlib
from collections import defaultdict
from pathlib import Path
from typing import ClassVar

import pytest

from scripts.atlas import export_runtime_shards as exporter
from scripts.atlas.export_runtime_shards import (
    ExportError,
    SearchFamilyIndex,
    StagedVersion,
    export_runtime_shards,
    find_component_tokens,
    gzip_bytes,
    load_component_tokenization_vectors,
    load_entry_records,
    load_practice_levels_by_slug,
    logical_tree_fingerprint,
    open_readonly_db,
    tree_fingerprint,
    verify_tree,
)
from scripts.atlas.normalization import load_normalization_vectors, normalize_atlas_text

ROOT = Path(__file__).resolve().parents[1]
REAL_DB_PATH = ROOT / "data" / "atlas.db"
COMMITTED_RUNTIME_TREE = ROOT / "tests" / "fixtures" / "atlas" / "runtime-tree"
PRACTICE_DECKS_ROOT = ROOT / "tests" / "fixtures" / "atlas" / "practice_decks"
EXPORTER_SCRIPT = ROOT / "scripts" / "atlas" / "export_runtime_shards.py"

pytest_plugins = ("tests._export_runtime_shards_fixtures",)


def _fp(root: Path) -> str:
    """Same-build raw fingerprint (determinism only — not cross-platform)."""
    return tree_fingerprint(root)


def _logical_fp(root: Path) -> str:
    """Cross-platform logical content fingerprint (freshness guard)."""
    return logical_tree_fingerprint(root)


def test_normalization_vectors_match_python_rules() -> None:
    for case in load_normalization_vectors():
        assert normalize_atlas_text(case["input"]) == case["expected"], case


def test_component_tokenization_vectors_match_python_rules() -> None:
    for case in load_component_tokenization_vectors():
        assert find_component_tokens(str(case["input"])) == case["expected"], case


def test_script_path_invocation_exits_zero() -> None:
    """F007: ``python scripts/atlas/export_runtime_shards.py`` must not ModuleNotFoundError."""
    result = subprocess.run(
        [sys.executable, str(EXPORTER_SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()


def test_practice_levels_prefer_api_lexicon_and_lemma_id_only(fixture_db: Path) -> None:
    """F002: mirror SqliteAtlasDataSource — api/lexicon first, index lemmaId only."""
    deck_dir = PRACTICE_DECKS_ROOT / "lexicon"
    levels = load_practice_levels_by_slug(deck_dir)
    # api/lexicon A1 wins over lexicon/ A1 (which only lists файний).
    assert levels["прапор"] == ["A1"]
    assert levels["доконаний-вид"] == ["A1"]
    assert "файний" not in levels
    # lexicon-only A2 still applies when api has no A2 index.
    assert levels["іван"] == ["A2"]
    # lemma text must not become an index key (would poison ласка / вид).
    assert "ласка" not in levels
    assert "вид" not in levels

    conn = open_readonly_db(fixture_db)
    try:
        records = {
            record["slug"]: record
            for record in load_entry_records(conn, practice_levels_by_slug=levels)
        }
    finally:
        conn.close()

    assert records["прапор"]["renderContext"]["practiceLevels"] == ["A1"]
    assert records["доконаний-вид"]["renderContext"]["practiceLevels"] == ["A1"]
    assert records["іван"]["renderContext"]["practiceLevels"] == ["A2"]
    assert records["ласка"]["renderContext"]["practiceLevels"] == []
    assert records["вид"]["renderContext"]["practiceLevels"] == []
    assert records["файний"]["renderContext"]["practiceLevels"] == []


def test_export_twice_is_byte_identical(fixture_db: Path, tmp_path: Path) -> None:
    """Determinism must not depend on hydrated practice decks."""
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    report_a = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out_a,
        deck_dir=None,
        include_decks=False,
        verify=True,
    )
    report_b = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out_b,
        deck_dir=None,
        include_decks=False,
        verify=True,
    )
    assert report_a["dataVersion"] == report_b["dataVersion"]
    assert report_a["dataVersion"].startswith("atlas-v1-")
    assert _fp(out_a / "atlas") == _fp(out_b / "atlas")


def test_committed_runtime_tree_matches_fresh_fixture_export(
    fixture_export: tuple[Path, dict]
) -> None:
    """Sol F006 freshness guard: committed runtime-tree must match a live export.

    Compares *logical* content (gunzipped payloads + transport-stripped JSON),
    not raw gzip bytes — zlib builds differ across platforms (PR #5323).

    If the exporter or ``runtime_shards_fixture.db`` changes without regenerating
    the tree, this fails loudly in Python CI. Regen::

        PYTHONPATH=. .venv/bin/python \\
          tests/fixtures/atlas/build_runtime_shards_fixture.py --emit-tree
    """
    current = COMMITTED_RUNTIME_TREE / "atlas" / "current.json"
    assert current.is_file(), (
        f"missing committed runtime-tree at {COMMITTED_RUNTIME_TREE}; "
        "run build_runtime_shards_fixture.py --emit-tree"
    )
    fresh, _ = fixture_export
    committed_root = COMMITTED_RUNTIME_TREE / "atlas"
    fresh_root = fresh / "atlas"
    committed_fp = _logical_fp(committed_root)
    fresh_fp = _logical_fp(fresh_root)
    assert committed_fp == fresh_fp, (
        "committed tests/fixtures/atlas/runtime-tree is stale relative to a "
        "fresh export of runtime_shards_fixture.db; regenerate with "
        "`PYTHONPATH=. .venv/bin/python "
        "tests/fixtures/atlas/build_runtime_shards_fixture.py --emit-tree`"
    )

    # Path-set equality catches empty-dir / missing-leaf surprises without
    # requiring zlib-byte identity of committed vs freshly compressed objects.
    def _paths(root: Path) -> set[str]:
        return {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        }

    assert _paths(committed_root) == _paths(fresh_root)


def test_logical_freshness_guard_fails_on_corrupt_committed_gz(
    fixture_export: tuple[Path, dict], tmp_path: Path
) -> None:
    """Corrupt-byte property: gz payload change / undecompressable → guard fails.

    Extends the fail-closed checksum surface (see ``test_trie_split_and_checksum_fail_closed``)
    to the logical freshness comparison used cross-platform.
    """
    fresh, _ = fixture_export
    fresh_fp = _logical_fp(fresh / "atlas")

    corrupt_root = tmp_path / "corrupt-committed"
    shutil.copytree(COMMITTED_RUNTIME_TREE / "atlas", corrupt_root)
    gz_path = next(corrupt_root.rglob("*.json.gz"))
    blob = bytearray(gz_path.read_bytes())
    mid = max(10, len(blob) // 2)
    blob[mid] = (blob[mid] + 1) % 256
    gz_path.write_bytes(bytes(blob))

    stale_msg = (
        "committed tests/fixtures/atlas/runtime-tree is stale relative to a "
        "fresh export of runtime_shards_fixture.db; regenerate with "
        "`PYTHONPATH=. .venv/bin/python "
        "tests/fixtures/atlas/build_runtime_shards_fixture.py --emit-tree`"
    )
    with pytest.raises((AssertionError, ExportError)) as exc_info:
        corrupt_fp = _logical_fp(corrupt_root)
        assert corrupt_fp == fresh_fp, stale_msg

    # Must be the guard assertion or a clear ExportError — not an unrelated crash.
    if isinstance(exc_info.value, AssertionError):
        assert "stale relative" in str(exc_info.value)
    else:
        assert "undecompressable" in str(exc_info.value).lower() or "logical" in str(
            exc_info.value
        ).lower()


def test_fixture_covers_representative_entry_shapes(fixture_db: Path) -> None:
    conn = open_readonly_db(fixture_db)
    try:
        records = load_entry_records(conn, practice_levels_by_slug={})
    finally:
        conn.close()

    by_slug = {record["slug"]: record for record in records}
    assert "прапор" in by_slug
    assert by_slug["прапор"]["kind"] == "article"
    morph = (by_slug["прапор"]["entry"].get("enrichment") or {}).get("morphology")
    assert isinstance(morph, dict) and morph.get("marked_forms")

    assert by_slug["іване"]["kind"] == "form_route"
    assert by_slug["іване"]["entry"]["form_of"]["url_slug"] == "іван"

    assert any(alias["alias"] == "prapor" for alias in by_slug["прапор"]["aliases"])
    assert by_slug["достовірний"]["entry"]["heritage_status"]["classification"] == "russianism"

    links = by_slug["доконаний-вид"]["renderContext"]["componentLinks"]
    assert links == [
        {"text": "доконаний", "targetSlug": "доконаний"},
        {"text": "вид", "targetSlug": "вид"},
    ]

    # Numeric multiword: letter tokens link; digit token must not become a chip.
    numeric = by_slug["мені-20-років"]["renderContext"]["componentLinks"]
    assert numeric == [
        {"text": "Мені", "targetSlug": "я"},
        {"text": "років", "targetSlug": "рік"},
    ]
    assert all(link["text"] != "20" and not any(ch.isdigit() for ch in link["text"]) for link in numeric)


def test_trie_split_and_checksum_fail_closed(fixture_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    # Force the SHA-256 prefix trie to split by lowering the entry gzip ceiling.
    report = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
        # Large enough for the biggest single fixture record (~4 KiB gzip),
        # small enough to force the SHA-256 prefix trie to split the set.
        entry_max_gzip_bytes=8_000,
    )
    assert report["counts"]["entryShards"] >= 2, report["counts"]

    current = json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "atlas" / current["manifestUrl"]).read_text(encoding="utf-8"))
    first_id = sorted(manifest["entries"]["shards"])[0]
    descriptor = manifest["entries"]["shards"][first_id]
    shard_path = (out / "atlas" / current["manifestUrl"]).parent / descriptor["url"]
    blob = bytearray(shard_path.read_bytes())
    blob[0] = (blob[0] + 1) % 256
    shard_path.write_bytes(bytes(blob))
    with pytest.raises(ExportError, match=r"sha256 mismatch|verify failed"):
        verify_tree(out, "atlas")


def test_search_families_remain_separate(fixture_export: tuple[Path, dict]) -> None:
    out, report = fixture_export
    current = json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "atlas" / current["manifestUrl"]).read_text(encoding="utf-8"))
    for desc in manifest["search"]["articles"]["shards"].values():
        assert desc["url"].startswith("search/articles/")
    for desc in manifest["search"]["aliases"]["shards"].values():
        assert desc["url"].startswith("search/aliases/")
    assert report["counts"]["searchArticles"] == report["counts"]["articles"]
    assert report["counts"]["searchAliases"] <= report["counts"]["aliases"]
    assert report["counts"]["searchAliases"] > 0


def test_exported_entry_records_match_sqlite_projection(
    fixture_db: Path, fixture_export: tuple[Path, dict]
) -> None:
    """Export records must match the Sqlite data-source projection (parity input)."""
    out, _ = fixture_export
    conn = open_readonly_db(fixture_db)
    try:
        expected = {
            record["slug"]: record
            for record in load_entry_records(conn, practice_levels_by_slug={})
        }
    finally:
        conn.close()

    current = json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))
    version_root = (out / "atlas" / current["manifestUrl"]).parent
    manifest = json.loads((version_root / "manifest.json").read_text(encoding="utf-8"))
    exported: dict[str, dict] = {}
    for descriptor in manifest["entries"]["shards"].values():
        raw = gzip.decompress((version_root / descriptor["url"]).read_bytes())
        payload = json.loads(raw.decode("utf-8"))
        for record in payload["records"]:
            exported[record["slug"]] = record

    assert set(exported) == set(expected)
    for slug, left in expected.items():
        right = exported[slug]
        assert right["kind"] == left["kind"]
        assert right["entry"] == left["entry"]
        assert right["aliases"] == left["aliases"]
        assert right["relations"] == left["relations"]
        assert right["provenance"] == left["provenance"]
        assert right["renderContext"] == left["renderContext"]


def test_data_version_assert_flag(fixture_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=False,
    )
    with pytest.raises(ExportError, match="data-version mismatch"):
        export_runtime_shards(
            db_path=fixture_db,
            out_dir=tmp_path / "out2",
            include_decks=False,
            deck_dir=None,
            expected_data_version="atlas-v1-deadbeefdeadbeef",
        )
    export_runtime_shards(
        db_path=fixture_db,
        out_dir=tmp_path / "out3",
        include_decks=False,
        deck_dir=None,
        expected_data_version=report["dataVersion"],
    )


def test_gzip_mtime_zero_and_newline_termination(fixture_export: tuple[Path, dict]) -> None:
    out, _ = fixture_export
    current = json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "atlas" / current["manifestUrl"]).read_text(encoding="utf-8"))
    version_root = (out / "atlas" / current["manifestUrl"]).parent
    for descriptor in list(manifest["entries"]["shards"].values())[:3]:
        compressed = (version_root / descriptor["url"]).read_bytes()
        assert compressed[4:8] == b"\x00\x00\x00\x00"
        raw = gzip.decompress(compressed)
        assert raw.endswith(b"\n")
        assert hashlib.sha256(compressed).hexdigest() == descriptor["sha256"]
        assert hashlib.sha256(raw).hexdigest() == descriptor["jsonSha256"]


def _require_real_atlas_db() -> Path:
    """Fail closed for release-gate runs; ordinary CI still skipif-guarded below."""
    if not REAL_DB_PATH.is_file():
        raise AssertionError(
            "atlas_release gate requires hydrated data/atlas.db "
            f"(expected at {REAL_DB_PATH}); symlink from primary checkout or "
            "run site hydrate before publish"
        )
    return REAL_DB_PATH


@pytest.mark.skipif(not REAL_DB_PATH.is_file(), reason="data/atlas.db not available")
def test_real_db_public_counts_and_alias_targets(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=REAL_DB_PATH,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    assert report["counts"]["articles"] == 8206
    assert report["counts"]["formRoutes"] == 336
    assert report["counts"]["publicRoutes"] == 8542
    assert report["counts"]["aliases"] == 9969
    assert report["counts"]["articles"] + report["counts"]["formRoutes"] == report["counts"][
        "publicRoutes"
    ]

    conn = sqlite3.connect(f"{Path(REAL_DB_PATH).resolve().as_uri()}?mode=ro", uri=True)
    try:
        invalid = conn.execute(
            """SELECT COUNT(*)
               FROM aliases AS alias
               LEFT JOIN articles AS article ON article.slug = alias.target_slug
               WHERE alias.visibility = 'public'
                 AND (
                     article.slug IS NULL
                     OR article.review_state != 'approved'
                     OR article.visibility != 'public'
                 )"""
        ).fetchone()[0]
    finally:
        conn.close()
    assert invalid == 0


@pytest.mark.skipif(not REAL_DB_PATH.is_file(), reason="data/atlas.db not available")
def test_real_db_entry_shard_size_band(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=REAL_DB_PATH,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    sizes = report["entryShardBytes"]
    assert sizes, "expected entry shards"
    assert min(sizes) >= 524_288, sizes
    assert max(sizes) <= 1_048_576, sizes


@pytest.mark.atlas_release
def test_atlas_release_gate_real_db_counts_and_export(tmp_path: Path) -> None:
    """Publish-time release gate (``pytest -m atlas_release``).

    Requires hydrated ``data/atlas.db``. Fails closed when missing — never skip.
    Companion TS full-record parity: ``npm run test:atlas-release-gate`` (site/).
    """
    db_path = _require_real_atlas_db()
    out = tmp_path / "release-export"
    report = export_runtime_shards(
        db_path=db_path,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    assert report["counts"]["articles"] == 8206, report["counts"]
    assert report["counts"]["formRoutes"] == 336, report["counts"]
    assert report["counts"]["publicRoutes"] == 8542, report["counts"]
    assert report["counts"]["aliases"] == 9969, report["counts"]
    assert (
        report["counts"]["articles"] + report["counts"]["formRoutes"]
        == report["counts"]["publicRoutes"]
    )
    sizes = report["entryShardBytes"]
    assert sizes, "expected entry shards"
    assert min(sizes) >= 524_288, sizes
    assert max(sizes) <= 1_048_576, sizes
    assert (out / "atlas" / "current.json").is_file()
    print(
        "atlas_release gate ok:",
        report["dataVersion"],
        "publicRoutes=",
        report["counts"]["publicRoutes"],
        "entryShards=",
        report["counts"]["entryShards"],
    )


# ---------------------------------------------------------------------------
# Bounded-memory exporter (#8672): differential tests against the historical
# whole-corpus implementation, kept below as an in-memory reference oracle.
# ---------------------------------------------------------------------------

_SOURCE_DDL = """
CREATE TABLE articles (
    slug TEXT PRIMARY KEY, display_head TEXT NOT NULL, lemma TEXT NOT NULL,
    entry_type TEXT NOT NULL CHECK (entry_type IN ('expression', 'lemma', 'multiword_term', 'phraseologism', 'proper_name', 'proverb')),
    pos TEXT, gloss TEXT,
    review_state TEXT NOT NULL CHECK (review_state IN ('approved', 'needs_review', 'rejected')),
    visibility TEXT NOT NULL CHECK (visibility IN ('private', 'public')),
    cefr TEXT, heritage_classification TEXT, created_at TEXT, updated_at TEXT
);
CREATE TABLE manifest_metadata (key TEXT PRIMARY KEY, value_json TEXT NOT NULL);
CREATE TABLE article_payloads (
    slug TEXT PRIMARY KEY, route_order INTEGER NOT NULL, payload_json TEXT NOT NULL,
    is_public_route INTEGER NOT NULL CHECK (is_public_route IN (0, 1))
);
CREATE TABLE article_provenance (
    slug TEXT NOT NULL, source_family TEXT, source_locator TEXT, extraction_mode TEXT,
    FOREIGN KEY (slug) REFERENCES articles(slug)
);
CREATE TABLE aliases (
    alias TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('canonical', 'component_head', 'inflected_form', 'spelling_variant', 'translation_hint', 'transliteration', 'unstressed')),
    source TEXT, target_slug TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'public' CHECK (visibility IN ('private', 'public')),
    UNIQUE (alias, kind, target_slug)
);
CREATE TABLE related_entries (
    slug TEXT NOT NULL, related_slug TEXT NOT NULL, entry_type TEXT, relation TEXT NOT NULL,
    component_role TEXT, provenance TEXT NOT NULL CHECK (provenance IN ('unverified', 'verified')),
    CHECK (slug != related_slug), UNIQUE (slug, related_slug, relation, provenance)
);
CREATE INDEX idx_aliases_target ON aliases(target_slug);
CREATE INDEX idx_prov_slug ON article_provenance(slug);
CREATE INDEX idx_related_entries_slug_relation ON related_entries(slug, relation);
CREATE INDEX idx_article_payloads_route ON article_payloads(is_public_route, route_order);
"""

# Code-point order differs from UTF-16 order for U+FB00 vs an astral emoji.
_UNICODE_STRESS_HEADS = [
    "Київ", "київ", "за́мок", "п'ять", "п’ять", "й", "й", "ﬀ", "\U0001f600",
    "Я", "я", "ї", "abc", "Abc", "123", "a", "i",
]
_GLOSS_WORDS = [
    "the", "them", "then", "there", "a", "an", "and", "i", "in", "is", "of", "off", "often",
    "flag", "house", "go", "Water", "river", "sky", "ще",
]


def _make_source_db(
    path: Path,
    *,
    records: int = 90,
    filler_chars: int = 600,
    seed: int = 8672,
    gloss_chars: int | None = None,
) -> Path:
    """Synthetic source DB covering sort/dedup/terminal/form-route/private edge cases."""
    rng = random.Random(seed)
    conn = sqlite3.connect(path)
    conn.executescript(_SOURCE_DDL)
    conn.execute(
        "INSERT INTO manifest_metadata VALUES ('generated_at', ?)", (json.dumps("2026-01-02T03:04:05+00:00"),)
    )
    heads = list(_UNICODE_STRESS_HEADS) + [f"слово{index:03d}" for index in range(records)]
    articles: list[tuple[str, str, str]] = []
    for index, head in enumerate(heads):
        slug = unicodedata.normalize("NFC", head.lower().replace("'", "-").replace("’", "-")) + f"-{index}"
        entry_type = "lemma" if index % 5 else ("phraseologism", "multiword_term", "proper_name")[index % 3]
        articles.append((slug, head, entry_type))
    lemma_heads = [head for _, head, kind in articles if kind == "lemma"]
    rows: list[tuple[str, int, str, int]] = []
    for index, (slug, head, entry_type) in enumerate(articles):
        private = index % 17 == 16
        gloss = None if index % 7 == 6 else " ".join(rng.sample(_GLOSS_WORDS, rng.randint(1, 4)))
        if gloss_chars is not None:  # long glosses over one fixed vocabulary (body size, not key count, varies)
            gloss = (" ".join(_GLOSS_WORDS) + " ") * (gloss_chars // 60 + 1)
        cefr = ("A1", "B2", None)[index % 3]
        lemma = head if entry_type == "lemma" else " ".join(rng.sample(lemma_heads, 2))
        conn.execute(
            "INSERT INTO articles VALUES (?,?,?,?,?,?,?,?,?,?,NULL,NULL)",
            (slug, head, lemma, entry_type, "noun", gloss, "approved", "private" if private else "public", cefr, None),
        )
        payload = {
            "url_slug": slug,
            "lemma": lemma,
            "notes": "".join(rng.choice("abcdef0123456789 ") for _ in range(filler_chars)),
            "enrichment": {"cefr": {"level": cefr.lower()}} if cefr else {},
        }
        rows.append((slug, index // 3, json.dumps(payload, ensure_ascii=False), 0 if private else 1))
        if private:
            continue
        for alias, kind, source in (
            (head.lower(), "canonical", "wiki"),
            (head.capitalize(), "spelling_variant", None),
            (unicodedata.normalize("NFD", head.lower()) + "́", "unstressed", "sum"),
            (f"x{index % 4}", "translation_hint", "en"),
        ):
            conn.execute(
                "INSERT OR IGNORE INTO aliases VALUES (?,?,?,?,'public')", (alias, kind, source, slug)
            )
        conn.execute("INSERT INTO aliases VALUES (?,?,?,?,'private')", (f"hidden-{index}", "canonical", None, slug))
        for other in (articles[(index + 1) % len(articles)][0], articles[(index + 3) % len(articles)][0]):
            if other != slug:
                conn.execute(
                    "INSERT OR IGNORE INTO related_entries VALUES (?,?,?,?,?,?)",
                    (slug, other, "lemma", "see_also", None, "verified"),
                )
        for family in ("sum", "wiki"):
            conn.execute(
                "INSERT INTO article_provenance VALUES (?,?,?,?)", (slug, family, f"loc-{index}", "auto")
            )
    for index in range(6):  # form routes: public payload, no article row
        slug = f"форма-{index}"
        payload = {"url_slug": slug, "lemma": "слово001", "form_of": {"url_slug": articles[-1][0]}}
        rows.append((slug, 1000 + index, json.dumps(payload, ensure_ascii=False), 1))
    conn.executemany("INSERT INTO article_payloads VALUES (?,?,?,?)", rows)
    conn.commit()
    conn.close()
    return path


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _entry_bits(slug: str) -> str:
    digest = hashlib.sha256(exporter.normalize_slug_for_hash(slug).encode("utf-8")).digest()
    return "".join(f"{byte:08b}" for byte in digest)


def _ref_load_entry_records(conn: sqlite3.Connection, practice: dict) -> list[dict]:
    """Historical whole-corpus loader (pre-#8672)."""
    def unique_targets(rows):
        targets = defaultdict(set)
        for lookup_text, target_slug in rows:
            key = normalize_atlas_text(lookup_text)
            if key:
                targets[key].add(target_slug)
        return targets

    article_rows = conn.execute(
        """SELECT display_head, slug FROM articles
           WHERE review_state = 'approved' AND visibility = 'public' AND entry_type = 'lemma'
           ORDER BY display_head COLLATE NOCASE, slug"""
    ).fetchall()
    alias_rows = conn.execute(
        """SELECT al.alias, al.target_slug FROM aliases al JOIN articles a ON a.slug = al.target_slug
           WHERE al.visibility = 'public' AND a.review_state = 'approved'
             AND a.visibility = 'public' AND a.entry_type = 'lemma'
           ORDER BY al.alias COLLATE NOCASE, al.target_slug, al.kind"""
    ).fetchall()
    article_targets = unique_targets((r[0], r[1]) for r in article_rows)
    alias_targets = unique_targets((r[0], r[1]) for r in alias_rows)
    component_targets = {k: next(iter(v)) for k, v in article_targets.items() if len(v) == 1}
    for lookup, matched in alias_targets.items():
        if lookup not in article_targets and len(matched) == 1:
            component_targets[lookup] = next(iter(matched))
    lemma_slugs = {
        r[0]
        for r in conn.execute(
            "SELECT slug FROM articles WHERE review_state = 'approved' AND visibility = 'public' AND entry_type = 'lemma'"
        )
    }
    aliases_by_slug, relations_by_slug, provenance_by_slug = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in conn.execute(
        "SELECT alias, kind, source, target_slug FROM aliases WHERE visibility = 'public' ORDER BY target_slug, kind, alias, source"
    ):
        aliases_by_slug[row["target_slug"]].append(row)
    for row in conn.execute(
        """SELECT slug, related_slug, entry_type, relation, component_role, provenance
           FROM related_entries ORDER BY slug, relation, related_slug, provenance, component_role"""
    ):
        relations_by_slug[row["slug"]].append(row)
    for row in conn.execute(
        "SELECT slug, source_family, source_locator, extraction_mode, rowid FROM article_provenance ORDER BY slug, rowid"
    ):
        provenance_by_slug[row["slug"]].append(row)
    payload_rows = conn.execute(
        """SELECT ap.slug AS slug, ap.payload_json AS payload_json, a.entry_type AS entry_type, a.cefr AS cefr
           FROM article_payloads ap LEFT JOIN articles a ON a.slug = ap.slug
           WHERE ap.is_public_route = 1 ORDER BY ap.route_order, ap.slug"""
    ).fetchall()
    records = []
    for row in payload_rows:
        entry = json.loads(row["payload_json"])
        entry["entry_type"] = row["entry_type"]
        exporter._assert_cefr_consistent(row["slug"], row["cefr"], entry)
        slug = str(row["slug"])
        records.append(
            {
                "slug": slug,
                "kind": "article" if row["entry_type"] is not None else "form_route",
                "entry": entry,
                "aliases": exporter._sorted_alias_rows(aliases_by_slug.get(slug, [])),
                "relations": exporter._sorted_relation_rows(relations_by_slug.get(slug, [])),
                "provenance": exporter._sorted_provenance_rows(provenance_by_slug.get(slug, [])),
                "renderContext": {
                    "componentLinks": exporter.component_links_for_entry(
                        entry, component_targets=component_targets, lemma_slugs=lemma_slugs
                    ),
                    "practiceLevels": list(
                        practice.get(slug) or practice.get(str(entry.get("lemma") or "")) or []
                    ),
                },
            }
        )
    return records


def _ref_load_search_rows(conn: sqlite3.Connection):
    """Historical whole-corpus search-row loader (pre-#8672)."""
    articles = []
    for slug, display_head, gloss, entry_type, cefr in conn.execute(
        """SELECT slug, display_head, gloss, entry_type, cefr FROM articles
           WHERE review_state = 'approved' AND visibility = 'public'
           ORDER BY display_head COLLATE NOCASE, slug"""
    ).fetchall():
        row = {
            "l": display_head, "s": slug, "g": exporter._clean_text(gloss),
            "r": exporter.transliterate(display_head), "t": entry_type,
        }
        level = exporter._clean_text(cefr)
        if level:
            row["c"] = level
        articles.append(row)
    articles.sort(key=lambda row: (normalize_atlas_text(row["l"]), row["s"]))
    aliases, seen = [], set()
    for alias, kind, target_slug, target_head in conn.execute(
        """SELECT alias.alias, alias.kind, alias.target_slug, article.display_head
           FROM aliases AS alias JOIN articles AS article ON article.slug = alias.target_slug
           WHERE alias.visibility = 'public' AND article.review_state = 'approved' AND article.visibility = 'public'
           ORDER BY alias.alias COLLATE NOCASE, alias.target_slug, alias.kind"""
    ).fetchall():
        key = (normalize_atlas_text(alias), target_slug)
        if not key[0] or key in seen:
            continue
        seen.add(key)
        aliases.append({"a": alias, "k": kind, "s": target_slug, "h": target_head})
    aliases.sort(key=lambda row: (normalize_atlas_text(row["a"]), row["s"], row["k"]))
    return articles, aliases


def _ref_data_version(*, generated_at, entry_records, article_rows, alias_rows, deck_index) -> str:
    identity = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "entries": [
            {
                "slug": record["slug"],
                "kind": record["kind"],
                "entrySha256": exporter.sha256_hex(exporter.canonical_json_bytes(record["entry"])),
                "aliasesSha256": exporter.sha256_hex(exporter.canonical_json_bytes(record["aliases"])),
                "relationsSha256": exporter.sha256_hex(exporter.canonical_json_bytes(record["relations"])),
                "provenanceSha256": exporter.sha256_hex(exporter.canonical_json_bytes(record["provenance"])),
                "renderContextSha256": exporter.sha256_hex(exporter.canonical_json_bytes(record["renderContext"])),
            }
            for record in entry_records
        ],
        "searchArticles": article_rows,
        "searchAliases": alias_rows,
        "decks": {
            level: info.get("deckVersion") for level, info in sorted((deck_index.get("levels") or {}).items())
        },
    }
    return f"atlas-v1-{exporter.sha256_hex(exporter.canonical_json_bytes(identity))[:16]}"


def _ref_build_entry_shards(records, *, data_version, max_gzip_bytes, compression_level):
    """Historical recursive trie: serialises and gzips whole candidate sets."""
    prepared = sorted(((_entry_bits(r["slug"]), dict(r)) for r in records), key=lambda i: (i[0], i[1]["slug"]))
    blobs: dict[str, bytes] = {}
    descriptors: dict[str, dict] = {}

    def materialize(bit_length, prefix_value, items):
        shard_id = exporter.entry_shard_id(bit_length, prefix_value)
        ordered = [item[1] for item in sorted(items, key=lambda pair: pair[1]["slug"])]
        payload = {
            "schema": exporter.ENTRY_SHARD_SCHEMA, "schemaVersion": 1,
            "dataVersion": data_version, "records": ordered,
        }
        raw = exporter.canonical_json_bytes(payload)
        compressed = gzip_bytes(raw, compression_level=compression_level)
        if len(compressed) > max_gzip_bytes:
            if len(items) <= 1:
                raise ExportError(
                    f"single entry record exceeds entry-max-gzip-bytes "
                    f"({len(compressed)} > {max_gzip_bytes}) slug={items[0][1]['slug']!r}"
                )
            zeros = [i for i in items if i[0][bit_length] == "0"]
            ones = [i for i in items if i[0][bit_length] != "0"]
            if not zeros:
                return materialize(bit_length + 1, (prefix_value << 1) | 1, ones)
            if not ones:
                return materialize(bit_length + 1, prefix_value << 1, zeros)
            materialize(bit_length + 1, prefix_value << 1, zeros)
            return materialize(bit_length + 1, (prefix_value << 1) | 1, ones)
        blobs[shard_id] = compressed
        descriptors[shard_id] = exporter.object_descriptor(
            object_id=shard_id, relative_url=f"entries/{shard_id}.json.gz",
            count=len(ordered), raw=raw, compressed=compressed,
        )
        return None

    materialize(0, 0, prepared)
    return blobs, descriptors


def _ref_build_search_shards(rows, *, family, data_version, max_gzip_bytes, compression_level, key_fn, row_id_fn, schema):
    """Historical recursive prefix trie over dict-copied rows."""
    depth1: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        for key in key_fn(row):
            depth1[key[0]][row_id_fn(row)] = dict(row)
    blobs: dict[str, bytes] = {}
    descriptors: dict[str, dict] = {}

    def write_shard(prefix, row_map, *, terminal=False):
        shard_id = exporter.search_shard_id(prefix) + (".term" if terminal else "")
        ordered = sorted(row_map.values(), key=lambda item: (row_id_fn(item), json.dumps(item, sort_keys=True)))
        if family == "articles":
            ordered.sort(key=lambda item: (normalize_atlas_text(str(item["l"])), item["s"]))
        else:
            ordered.sort(key=lambda item: (normalize_atlas_text(str(item["a"])), item["s"], item["k"]))
        raw = exporter.canonical_json_bytes(
            {"schema": schema, "schemaVersion": 1, "dataVersion": data_version,
             "prefix": prefix, "terminal": terminal, "records": ordered}
        )
        compressed = gzip_bytes(raw, compression_level=compression_level)
        blobs[shard_id] = compressed
        descriptors[shard_id] = exporter.object_descriptor(
            object_id=shard_id, relative_url=f"search/{family}/{shard_id}.json.gz",
            count=len(ordered), raw=raw, compressed=compressed,
        )
        return shard_id

    def split_or_write(prefix, row_map):
        ordered = list(row_map.values())
        probe = gzip_bytes(
            exporter.canonical_json_bytes(
                {"schema": schema, "schemaVersion": 1, "dataVersion": data_version,
                 "prefix": prefix, "terminal": False, "records": ordered}
            ),
            compression_level=compression_level,
        )
        node = {"prefix": prefix}
        if len(probe) <= max_gzip_bytes:
            node["shardId"] = write_shard(prefix, row_map)
            return node
        children, terminals = defaultdict(dict), {}
        for row in ordered:
            for key in key_fn(row):
                if not key.startswith(prefix):
                    continue
                if key == prefix:
                    terminals[row_id_fn(row)] = row
                else:
                    children[prefix + key[len(prefix)]][row_id_fn(row)] = row
        if not children:
            raise ExportError(
                f"search {family} shard for prefix={prefix!r} exceeds max "
                f"({len(probe)} > {max_gzip_bytes}) and cannot split"
            )
        if terminals:
            node["terminalShardId"] = write_shard(prefix, terminals, terminal=True)
        node["children"] = {c[len(prefix)]: split_or_write(c, children[c]) for c in sorted(children)}
        return node

    root_children = {prefix: split_or_write(prefix, depth1[prefix]) for prefix in sorted(depth1)}
    index = {
        "strategy": "unicode-prefix-trie", "family": family, "maxGzipBytes": max_gzip_bytes,
        "tree": {"prefix": "", "children": root_children},
        "shards": {key: descriptors[key] for key in sorted(descriptors)},
    }
    return index, blobs


def _reference_export(db_path: Path, *, compression_level: int, entry_max: int, search_max: int):
    """Objects + index sections the historical exporter would emit for ``db_path``."""
    conn = open_readonly_db(db_path)
    try:
        generated_at = json.loads(
            conn.execute("SELECT value_json FROM manifest_metadata WHERE key = 'generated_at'").fetchone()[0]
        )
        records = _ref_load_entry_records(conn, {})
        article_rows, alias_rows = _ref_load_search_rows(conn)
    finally:
        conn.close()
    data_version = _ref_data_version(
        generated_at=generated_at, entry_records=records,
        article_rows=article_rows, alias_rows=alias_rows, deck_index={"levels": {}},
    )
    entry_blobs, entry_descriptors = _ref_build_entry_shards(
        records, data_version=data_version, max_gzip_bytes=entry_max, compression_level=compression_level
    )
    article_index, article_blobs = _ref_build_search_shards(
        article_rows, family="articles", data_version=data_version, max_gzip_bytes=search_max,
        compression_level=compression_level, key_fn=exporter._article_index_keys,
        row_id_fn=lambda row: str(row["s"]), schema=exporter.SEARCH_ARTICLE_SCHEMA,
    )
    alias_index, alias_blobs = _ref_build_search_shards(
        alias_rows, family="aliases", data_version=data_version, max_gzip_bytes=search_max,
        compression_level=compression_level, key_fn=exporter._alias_index_keys,
        row_id_fn=lambda row: f"{row['a']}\0{row['s']}\0{row['k']}", schema=exporter.SEARCH_ALIAS_SCHEMA,
    )
    files = {f"entries/{k}.json.gz": v for k, v in entry_blobs.items()}
    files |= {f"search/articles/{k}.json.gz": v for k, v in article_blobs.items()}
    files |= {f"search/aliases/{k}.json.gz": v for k, v in alias_blobs.items()}
    return data_version, files, {
        "entries": {"shards": entry_descriptors},
        "articles": article_index,
        "aliases": alias_index,
    }


def _export(db: Path, out: Path, **kwargs):
    return export_runtime_shards(
        db_path=db, out_dir=out, include_decks=False, deck_dir=None, verify=True, **kwargs
    )


# (entry cap, search cap): default, and small caps that force deep entry/search splits.
_CAPS = [(1_048_576, 524_288), (9_000, 800), (6_000, 700)]


@pytest.mark.parametrize("level", [0, 1, 6, 9])
@pytest.mark.parametrize(("entry_max", "search_max"), _CAPS)
def test_streamed_export_is_byte_identical_to_reference(
    edge_db: Path, tmp_path: Path, level: int, entry_max: int, search_max: int
) -> None:
    forced = (entry_max, search_max) != _CAPS[0]
    if level == 0:  # stored blocks do not shrink: same split pressure needs bigger caps
        search_max *= 3
    data_version, files, indexes = _reference_export(
        edge_db, compression_level=level, entry_max=entry_max, search_max=search_max
    )
    out = tmp_path / "out"
    report = _export(
        edge_db, out, compression_level=level,
        entry_max_gzip_bytes=entry_max, search_max_gzip_bytes=search_max,
    )
    version_root = out / "atlas" / "versions" / data_version
    assert report["dataVersion"] == data_version
    tree = _snapshot(version_root)
    assert {name: blob for name, blob in tree.items() if name != "manifest.json"} == files
    manifest = json.loads(tree["manifest.json"])
    assert manifest["entries"]["shards"] == indexes["entries"]["shards"]
    assert manifest["search"]["articles"] == indexes["articles"]
    assert manifest["search"]["aliases"] == indexes["aliases"]
    if forced:
        assert manifest["counts"]["entryShards"] > 1
        assert manifest["counts"]["searchArticleShards"] > 20
        if level:  # level-0 caps are scaled up and may leave no exact-prefix bucket to split off
            assert any(name.endswith(".term.json.gz") for name in tree), "terminal shards exercised"


class _Injected(RuntimeError):
    pass


def _fail_after_writes(monkeypatch, count: int) -> None:
    """Fail the staged object write after ``count`` (``open`` backs every staged object)."""
    real_open = exporter.StagedVersion.open
    seen = {"writes": 0}

    def open_object(self, relative: str):
        seen["writes"] += 1
        if seen["writes"] > count:
            raise _Injected(f"write #{seen['writes']} {relative}")
        return real_open(self, relative)

    monkeypatch.setattr(exporter.StagedVersion, "open", open_object)


# Stages that fail before/around installing: an identical re-export reuses the installed
# tree (no rename), a changed-limits re-export must install an alternate tree.
_REEXPORT_STAGES = [
    "first-leaf", "mid-export", "manifest", "verify", "pointer",
    "swap-transport", "pointer-transport",
]


# ---------------------------------------------------------------------------
# Heap peaks of work that touches the filesystem are traced in a fresh interpreter
# (#8997). In-process, the peak also counts process-global tables that happen to
# grow inside the window: pathlib interns every path component, and once earlier
# tests (or the modules a CI shard collects) have filled CPython's interned-string
# table, the next new name resizes it. In CI shard 1 that resize added 7.7 MB to
# one ``--verify`` window: an allocation that follows test order, not the payload.
# ---------------------------------------------------------------------------

_TRACED_SCRIPT = """
import gc, json, sys, tracemalloc
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.atlas import export_runtime_shards as ex
kind, args = sys.argv[2], json.loads(sys.argv[3])
out = Path(args["out"])
if kind == "export":
    run = lambda: ex.export_runtime_shards(db_path=Path(args["db"]), out_dir=out, **args["kwargs"])
elif kind == "verify":
    run = lambda: ex.verify_tree(out, "atlas")
else:
    from tests.test_export_runtime_shards import _shared_key_alias_index
    index, _records = _shared_key_alias_index(args["rows"], terminal=args["terminal"])
    del _records
    def open_object(relative):
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open("wb")
    run = lambda: ex.build_search_family_shards(
        index, family="aliases", data_version="v-test", schema=ex.SEARCH_ALIAS_SCHEMA,
        open_object=open_object, **args["kwargs"],
    )
# One-time, corpus-independent setup is not the measured work's memory.
ex.check_stored_gzip_runtime()
ex._json_backend()
gc.collect()
tracemalloc.start()
try:
    run()
    error = None
except ex.ExportError as exc:
    error = str(exc)
print(json.dumps({"error": error, "peak": tracemalloc.get_traced_memory()[1]}))
"""


def _traced_in_fresh_interpreter(kind: str, **args) -> tuple[str | None, int]:
    """(ExportError text or None, traced heap peak) of one ``export``/``verify``/``aliases`` run."""
    result = subprocess.run(
        [sys.executable, "-c", _TRACED_SCRIPT, str(ROOT), kind, json.dumps(args, default=str)],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=120,
    )
    assert result.returncode == 0, (kind, result.returncode, result.stderr)
    measured = json.loads(result.stdout.splitlines()[-1])
    return measured["error"], measured["peak"]


# ---------------------------------------------------------------------------
# Published trees are immutable; the pointer is switched last (review of #8672).
# ---------------------------------------------------------------------------


def _pointer(out: Path) -> dict:
    return json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))


def _pointed_manifest(out: Path) -> Path:
    return out / "atlas" / _pointer(out)["manifestUrl"]


def _version_dirs(out: Path) -> list[str]:
    return sorted(p.name for p in (out / "atlas" / "versions").iterdir() if not p.name.startswith("."))


_CHANGED_LIMITS = [
    {"compression_level": 6},
    {"entry_max_gzip_bytes": 6_000},
    {"search_max_gzip_bytes": 700},
    {"entry_target_min_gzip_bytes": 1_000},
]


_KILL_SCRIPT = """
import json, os, signal, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.atlas import export_runtime_shards as ex
point, db, out, kwargs = sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]), json.loads(sys.argv[5])
real_rename, real_replace = os.rename, os.replace
def die():
    os.kill(os.getpid(), signal.SIGKILL)
def rename(src, dst, *a, **k):
    if not Path(src).name.startswith(".export-"):
        return real_rename(src, dst, *a, **k)
    if point == "before-install":
        die()
    real_rename(src, dst, *a, **k)
    if point == "after-install":
        die()
def replace(src, dst, *a, **k):
    if Path(dst).name != "current.json":
        return real_replace(src, dst, *a, **k)
    if point == "before-pointer":
        die()
    real_replace(src, dst, *a, **k)
    if point == "after-pointer":
        die()
os.rename, os.replace = rename, replace
ex.export_runtime_shards(db_path=db, out_dir=out, include_decks=False, deck_dir=None, verify=True, **kwargs)
"""

_KILL_POINTS = ["before-install", "after-install", "before-pointer", "after-pointer"]


def _run_killed(edge_db: Path, out: Path, point: str, **kwargs) -> None:
    result = subprocess.run(
        [sys.executable, "-c", _KILL_SCRIPT, str(ROOT), point, str(edge_db), str(out), json.dumps(kwargs)],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=120,
    )
    assert result.returncode == -signal.SIGKILL, (point, result.returncode, result.stderr)


def _synthetic_stage(base: Path, data_version: str, files: dict[str, bytes]) -> StagedVersion:
    stage = StagedVersion(base, data_version)
    for relative, data in files.items():
        stage.write(relative, data)
    return stage


def _publish_synthetic(base: Path, data_version: str, files: dict[str, bytes]) -> str:
    stage = _synthetic_stage(base, data_version, files)
    try:
        return stage.install()
    finally:
        stage.discard()


_TREE_A = {"manifest.json": b"{}\n", "entries/p0.json.gz": b"a" * 100}
_TREE_B = {"manifest.json": b"{}\n", "entries/p0.json.gz": b"b" * 100}


def _fsync_target(fd: int, base: Path) -> str:
    """Which publication step an ``os.fsync`` belongs to: the only file synced is the pending pointer."""
    status = os.fstat(fd)
    if not stat.S_ISDIR(status.st_mode):
        return "pointer-file"
    if os.path.samestat(status, (base / "versions").stat()):
        return "versions-dir"
    return "base-dir" if os.path.samestat(status, base.stat()) else "other"


_FSYNC_STEPS = ["versions-dir", "pointer-file", "base-dir"]  # install, pending pointer, then (after the rename) its dir


# ---------------------------------------------------------------------------
# Search rows are replayed from the read snapshot, never retained as bodies.
# ---------------------------------------------------------------------------


def _build_indexes(conn: sqlite3.Connection) -> tuple[SearchFamilyIndex, SearchFamilyIndex]:
    articles = SearchFamilyIndex.build(
        ((row["s"], row) for row in exporter._iter_article_search_rows(conn)),
        sort_key=exporter._article_sort_key,
        key_fn=exporter._article_index_keys,
        replay=lambda slug: exporter._replay_article_search_row(conn, slug),
    )
    aliases = SearchFamilyIndex.build(
        exporter._iter_located_alias_search_rows(conn),
        sort_key=exporter._alias_sort_key,
        key_fn=exporter._alias_index_keys,
        replay=lambda rowid: exporter._replay_alias_search_row(conn, rowid),
    )
    return articles, aliases


# ---------------------------------------------------------------------------
# Uncapped work streams: an oversized unsplittable bucket is only *counted* and a
# terminal shard (historically exempt from the cap) is gzip-streamed to its file;
# neither is serialized or compressed into memory (review of #8672, P1).
# ---------------------------------------------------------------------------

_SHARED_KEY_CAP = 16_384
_KEYLESS_GLOSS_CHARS = "!#$%&()*+,-./:;<=>?@[]^{|}~"  # no TOKEN_RE word chars: adds no index key


def _shared_key_alias_index(rows: int, *, terminal: bool) -> tuple[SearchFamilyIndex, list[dict]]:
    """``rows`` long alias rows all keyed ``a`` (plus one ``ab`` row when ``terminal``)."""

    def row(position: int) -> dict:
        rng = random.Random(position)
        return {
            "a": "ab" if position == rows else "a", "k": "canonical", "s": f"s{position:05d}",
            "h": "".join(rng.choice("абвгдежзийклмнопрстуфхцчшщьюя") for _ in range(2_000)),
        }

    index = SearchFamilyIndex.build(
        ((position, row(position)) for position in range(rows + terminal)),
        sort_key=exporter._alias_sort_key, key_fn=exporter._alias_index_keys, replay=row,
    )
    return index, sorted((row(position) for position in range(rows)), key=exporter._alias_sort_key)


def _search_shard_raw(schema: str, prefix: str, records: list[dict], *, terminal: bool) -> bytes:
    return exporter.canonical_json_bytes(
        {"schema": schema, "schemaVersion": 1, "dataVersion": "v-test",
         "prefix": prefix, "terminal": terminal, "records": records}
    )


def _build_aliases_traced(rows: int, out: Path, *, terminal: bool, level: int) -> tuple[str | None, int]:
    """(ExportError text or None, traced heap peak) of one search-family build into ``out``."""
    kwargs = {"max_gzip_bytes": _SHARED_KEY_CAP, "compression_level": level}
    return _traced_in_fresh_interpreter("aliases", rows=rows, terminal=terminal, out=out, kwargs=kwargs)


def _make_shared_key_db(path: Path, *, rows: int, terminal: bool, gloss_chars: int = 8_000) -> Path:
    """Reviewer shape: ``rows`` public articles headed ``a`` with long keyless glosses."""
    conn = sqlite3.connect(path)
    conn.executescript(_SOURCE_DDL)
    conn.execute(
        "INSERT INTO manifest_metadata VALUES ('generated_at', ?)", (json.dumps("2026-01-02T03:04:05+00:00"),)
    )
    for position in range(rows + terminal):
        rng = random.Random(position)
        slug, head = f"k{position:05d}", "ab" if position == rows else "a"
        gloss = "".join(rng.choice(_KEYLESS_GLOSS_CHARS) for _ in range(gloss_chars))
        conn.execute(
            "INSERT INTO articles VALUES (?,?,?,?,?,?,?,?,?,?,NULL,NULL)",
            (slug, head, head, "lemma", "noun", gloss, "approved", "public", None, None),
        )
        payload = {"url_slug": slug, "lemma": head, "gloss": gloss}
        conn.execute(
            "INSERT INTO article_payloads VALUES (?,?,?,?)",
            (slug, position, json.dumps(payload, ensure_ascii=False), 1),
        )
    conn.commit()
    conn.close()
    return path


def _export_traced(db: Path, out: Path, *, level: int) -> tuple[str | None, int]:
    """(ExportError text or None, traced heap peak) of one full export *with* ``--verify``."""
    kwargs = {"include_decks": False, "deck_dir": None, "compression_level": level,
              "entry_max_gzip_bytes": 65_536, "search_max_gzip_bytes": _SHARED_KEY_CAP, "verify": True}
    return _traced_in_fresh_interpreter("export", db=db, out=out, kwargs=kwargs)


def _verify_traced(out: Path) -> int:
    error, peak = _traced_in_fresh_interpreter("verify", out=out)
    assert error is None
    return peak


# ---------------------------------------------------------------------------
# Level 0 is framed from a length-only model of zlib's stored blocks and streamed
# (review of #8672, P1): byte parity with the one-shot gzip, nothing buffered.
# ---------------------------------------------------------------------------

_STORED_PATTERN = bytes(range(256)) * (14 * 1024 * 1024 // 256)


def _framed(data: bytes) -> bytes:
    pieces: list[bytes] = []
    exporter._frame_stored_gzip(lambda: (data,), exporter.stored_block_plan(len(data)), pieces.append)
    return b"".join(pieces)


def _stored_sweep_lengths() -> list[int]:
    lengths = set(range(0, 64)) | set(range(32_740, 32_790)) | set(range(65_500, 65_560))
    lengths |= set(range(98_280, 98_330)) | {131_072, 196_608, 262_144}
    total = 0
    for block in exporter._OUTPUT_BLOCK_SIZES[:6]:  # framed output crossing each output-buffer growth
        total += block
        lengths |= set(range(total - 80, total + 80, 7)) | set(range(total - 40_000, total, 4_999))
    rng = random.Random(8672)
    lengths |= {rng.randrange(0, 3_000_000) for _ in range(150)}
    return sorted(length for length in lengths if 0 <= length <= len(_STORED_PATTERN))


def _model_compressobj_blocks(lengths: list[int]) -> list[tuple[int, int]]:
    """Drive the model like CPython 3.12.8 ``Compress.compress`` per call, then ``flush()``."""
    blocks: list[tuple[int, int]] = []
    model = exporter.StoredDeflateModel(lambda length, last: blocks.append((length, last)))
    for flush, pieces in ((exporter._Z_NO_FLUSH, lengths), (exporter._Z_FINISH, [0])):
        for length in pieces:
            output = exporter.OutputBlocks()
            model.avail_out, model.avail_in = output.next_block(), length
            while True:
                if model.avail_out == 0:
                    model.avail_out = output.next_block()
                model.deflate(flush)
                if model.avail_out != 0:
                    break
            assert model.avail_in == 0
    return blocks


class _StoredFrameReader:
    """Stored-block framing of a level-0 gzip stream read incrementally; data bytes are skipped, not kept."""

    def __init__(self) -> None:
        self.blocks: list[tuple[int, int]] = []
        self._skip = 10  # gzip header
        self._header = b""

    def feed(self, data: memoryview) -> None:
        position = 0
        while position < len(data) and not (self.blocks and self.blocks[-1][1]):
            if self._skip:
                taken = min(self._skip, len(data) - position)
                self._skip -= taken
                position += taken
                continue
            piece = bytes(data[position : position + 5 - len(self._header)])
            self._header += piece
            position += len(piece)
            if len(self._header) == 5:
                header = self._header
                length = header[1] | header[2] << 8
                assert header[0] >> 1 == 0 and length ^ 0xFFFF == header[3] | header[4] << 8, header
                self.blocks.append((length, header[0] & 1))
                self._skip, self._header = length, b""


def _system_libz_version() -> str | None:
    try:
        libz = ctypes.CDLL("libz.so.1")
    except OSError:
        return None
    libz.zlibVersion.restype = ctypes.c_char_p
    return libz.zlibVersion().decode()


def _resident_memory_bytes() -> int:
    """Anonymous plus shmem-backed resident memory of this process (``/proc/self/status``)."""
    fields = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    return sum(int(fields[name].split()[0]) * 1024 for name in ("RssAnon", "RssShmem"))


def _live_zlib_one_shot_blocks(total: int) -> list[tuple[int, int]]:
    """Stored blocks of the C library driven exactly like CPython 3.12 ``zlib_compress_impl`` (level 0, wbits 31).

    The input is a private anonymous mapping that is only read, so every page
    stays the shared zero page and is never resident (a shared anonymous mapping,
    ``mmap``'s default, would be backed by shmem pages as zlib reads it: checked
    below). One output buffer is reused at every growth, so a >4 GiB input costs
    256 MiB.
    """
    resident_before = _resident_memory_bytes()

    class ZStream(ctypes.Structure):
        _fields_: ClassVar[list[tuple[str, type]]] = [
            ("next_in", ctypes.c_void_p), ("avail_in", ctypes.c_uint), ("total_in", ctypes.c_ulong),
            ("next_out", ctypes.c_void_p), ("avail_out", ctypes.c_uint), ("total_out", ctypes.c_ulong),
            ("msg", ctypes.c_char_p), ("state", ctypes.c_void_p), ("zalloc", ctypes.c_void_p),
            ("zfree", ctypes.c_void_p), ("opaque", ctypes.c_void_p), ("data_type", ctypes.c_int),
            ("adler", ctypes.c_ulong), ("reserved", ctypes.c_ulong),
        ]

    libz = ctypes.CDLL("libz.so.1")
    libz.zlibVersion.restype = ctypes.c_char_p
    libz.deflate.argtypes = [ctypes.POINTER(ZStream), ctypes.c_int]
    libz.deflateEnd.argtypes = [ctypes.POINTER(ZStream)]
    stream = ZStream()
    init = libz.deflateInit2_(ctypes.byref(stream), 0, 8, 31, 8, 0, libz.zlibVersion(), ctypes.sizeof(ZStream))
    assert init == exporter._Z_OK
    private = mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS
    source = mmap.mmap(-1, max(total, 1), flags=private)
    output = mmap.mmap(-1, exporter._OUTPUT_BLOCK_SIZES[-1], flags=private)
    source_start = ctypes.addressof(ctypes.c_char.from_buffer(source))
    output_start = ctypes.addressof(ctypes.c_char.from_buffer(output))
    view = memoryview(output)
    reader = _StoredFrameReader()
    schedule = exporter.OutputBlocks()
    try:
        stream.next_in = source_start
        stream.next_out, stream.avail_out = output_start, schedule.next_block()
        produced, remaining = output_start, total
        while True:
            stream.avail_in = min(remaining, exporter._UINT_MAX)
            remaining -= stream.avail_in
            flush = zlib.Z_FINISH if remaining == 0 else zlib.Z_NO_FLUSH
            while True:
                if stream.avail_out == 0:
                    stream.next_out, stream.avail_out = output_start, schedule.next_block()
                    produced = output_start
                status = libz.deflate(ctypes.byref(stream), flush)
                reader.feed(view[produced - output_start : stream.next_out - output_start])
                produced = stream.next_out
                if stream.avail_out != 0:
                    break
            assert stream.avail_in == 0
            if flush == zlib.Z_FINISH:
                break
        assert status == exporter._Z_STREAM_END
        grown = _resident_memory_bytes() - resident_before
        # Only the (written) output buffer may become resident, never the input.
        assert grown < exporter._OUTPUT_BLOCK_SIZES[-1] + (32 << 20), f"resident memory grew {grown} bytes"
    finally:
        libz.deflateEnd(ctypes.byref(stream))
        del view
        source.close()
        output.close()
    return reader.blocks


# ---------------------------------------------------------------------------
# --verify streams (review of #8672, P1): same checks and error categories as
# the historical whole-shard verify, json.loads-exact values, bounded memory.
# ---------------------------------------------------------------------------


def _ref_verify_tree(out_dir: Path, base_path: str, *, manifest_path: Path) -> dict:
    """Historical whole-shard ``verify_tree`` (pre-streaming #8672), the parity oracle."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version_root = manifest_path.parent
    errors: list[str] = []

    def check_descriptor(descriptor, *, family):
        rel = descriptor["url"]
        path = version_root / rel
        if not path.is_file():
            errors.append(f"missing {family} object {rel}")
            return
        compressed = path.read_bytes()
        if len(compressed) != descriptor["bytes"]:
            errors.append(
                f"{family} {descriptor['id']}: bytes mismatch file={len(compressed)} desc={descriptor['bytes']}"
            )
        if exporter.sha256_hex(compressed) != descriptor["sha256"]:
            errors.append(f"{family} {descriptor['id']}: sha256 mismatch")
        try:
            raw = gzip.decompress(compressed)
        except OSError as exc:
            errors.append(f"{family} {descriptor['id']}: gzip decode failed: {exc}")
            return
        if exporter.sha256_hex(raw) != descriptor["jsonSha256"]:
            errors.append(f"{family} {descriptor['id']}: jsonSha256 mismatch")
        if len(raw) != descriptor["uncompressedBytes"]:
            errors.append(f"{family} {descriptor['id']}: uncompressedBytes mismatch")
        payload = json.loads(raw.decode("utf-8"))
        if family.startswith("deck"):
            if not isinstance(payload, dict):
                errors.append(f"{family} {descriptor['id']}: deck payload must be an object")
            return
        if payload.get("schemaVersion") != exporter.SCHEMA_VERSION:
            errors.append(f"{family} {descriptor['id']}: unsupported schemaVersion")
        if payload.get("dataVersion") != manifest.get("dataVersion"):
            errors.append(f"{family} {descriptor['id']}: dataVersion mismatch vs manifest")
        records = payload.get("records")
        if isinstance(records, list) and len(records) != descriptor["count"]:
            errors.append(
                f"{family} {descriptor['id']}: count mismatch records={len(records)} desc={descriptor['count']}"
            )

    entry_shards = manifest["entries"]["shards"]
    for descriptor in entry_shards.values():
        check_descriptor(descriptor, family="entries")
        if descriptor["bytes"] > exporter.DEFAULT_ENTRY_MAX:
            errors.append(f"entries {descriptor['id']}: gzip exceeds 1 MiB")
    for family in ("articles", "aliases"):
        for descriptor in manifest["search"][family]["shards"].values():
            check_descriptor(descriptor, family=f"search.{family}")
    for level, info in (manifest.get("decks", {}).get("levels") or {}).items():
        for part, descriptor in (info.get("parts") or {}).items():
            check_descriptor(descriptor, family=f"decks.{level}.{part}")
    if errors:
        raise ExportError("verify failed:\n- " + "\n- ".join(errors))
    seen_slugs: dict[str, str] = {}
    article_count = form_count = 0
    for shard_id, descriptor in entry_shards.items():
        payload = json.loads(gzip.decompress((version_root / descriptor["url"]).read_bytes()).decode("utf-8"))
        for record in payload["records"]:
            slug = record["slug"]
            if slug in seen_slugs:
                errors.append(f"duplicate slug {slug!r} in {seen_slugs[slug]} and {shard_id}")
            seen_slugs[slug] = shard_id
            if record["kind"] == "article":
                article_count += 1
            elif record["kind"] == "form_route":
                form_count += 1
            for alias in record.get("aliases") or []:
                if alias.get("target_slug") != slug:
                    errors.append(f"alias target mismatch on {slug!r}")
    expected = manifest["counts"]
    if article_count != expected["articles"]:
        errors.append(f"article count {article_count} != {expected['articles']}")
    if form_count != expected["formRoutes"]:
        errors.append(f"form_of count {form_count} != {expected['formRoutes']}")
    if len(seen_slugs) != expected["publicRoutes"]:
        errors.append(f"route count {len(seen_slugs)} != {expected['publicRoutes']}")
    if errors:
        raise ExportError("verify failed:\n- " + "\n- ".join(errors))
    return {
        "dataVersion": manifest["dataVersion"], "articles": article_count, "formRoutes": form_count,
        "publicRoutes": len(seen_slugs), "entryShards": len(entry_shards),
    }


def _outcome(verify, out: Path, manifest_path: Path) -> tuple[str, str]:
    try:
        return "ok", json.dumps(verify(out, "atlas", manifest_path=manifest_path), sort_keys=True)
    except ExportError as exc:
        # Only the zlib/gzip library wording after this category differs between readers.
        return "ExportError", re.sub(r"gzip decode failed: [^\n]*", "gzip decode failed", str(exc))
    except Exception as exc:
        return type(exc).__name__, ""


def _descriptors(manifest: dict) -> list[dict]:
    found = list(manifest["entries"]["shards"].values())
    for family in ("articles", "aliases"):
        found += list(manifest["search"][family]["shards"].values())
    for info in (manifest.get("decks", {}).get("levels") or {}).values():
        found += list((info.get("parts") or {}).values())
    return found


def _rewrite(root: Path, manifest: dict, descriptor: dict, raw: bytes, *, consistent: bool = True) -> None:
    compressed = gzip_bytes(raw, compression_level=9)
    (root / descriptor["url"]).write_bytes(compressed)
    if consistent:
        descriptor.update(
            bytes=len(compressed), sha256=hashlib.sha256(compressed).hexdigest(),
            uncompressedBytes=len(raw), jsonSha256=hashlib.sha256(raw).hexdigest(),
        )
    (root / "manifest.json").write_bytes(exporter.canonical_json_bytes(manifest))


def _entry_shard(root: Path, manifest: dict, index: int = 0) -> tuple[dict, dict]:
    descriptor = manifest["entries"]["shards"][sorted(manifest["entries"]["shards"])[index]]
    return descriptor, json.loads(gzip.decompress((root / descriptor["url"]).read_bytes()))


def _json_text(payload: dict) -> bytes:
    return exporter.canonical_json_bytes(payload)


def _mutate(case: str, root: Path, manifest: dict) -> None:
    descriptor, payload = _entry_shard(root, manifest)
    path = root / descriptor["url"]
    blob = path.read_bytes()
    search = next(iter(manifest["search"]["articles"]["shards"].values()))
    if case == "flip-byte":
        path.write_bytes(blob[:40] + bytes([blob[40] ^ 0xFF]) + blob[41:])
    elif case == "flip-crc":
        path.write_bytes(blob[:-8] + bytes([blob[-8] ^ 1]) + blob[-7:])
    elif case == "truncate":
        path.write_bytes(blob[: len(blob) // 2])
    elif case == "trailing-zero-padding":
        path.write_bytes(blob + b"\0\0\0")
    elif case == "trailing-garbage-member":
        path.write_bytes(blob + b"garbage")
    elif case == "second-gzip-member":
        path.write_bytes(blob + gzip_bytes(b" ", compression_level=9))
    elif case == "missing-object":
        path.unlink()
    elif case == "descriptor-bytes":
        descriptor["bytes"] += 1
    elif case == "descriptor-count":
        search["count"] += 1
    elif case == "descriptor-json-sha":
        search["jsonSha256"] = "0" * 64
    elif case == "stale-raw-descriptor":
        _rewrite(root, manifest, descriptor, _json_text({**payload, "dataVersion": "other"}), consistent=False)
    elif case in ("schema-version", "schema-version-float", "schema-version-near-one", "data-version"):
        value = {"schema-version": 2, "schema-version-float": 1.0, "schema-version-near-one": 1.0000000000000000001}
        if case == "data-version":
            raw = _json_text({**payload, "dataVersion": "atlas-v1-other"})
        else:
            raw = _json_text(payload).replace(b'"schemaVersion":1', b'"schemaVersion":' + repr(value[case]).encode())
        _rewrite(root, manifest, descriptor, raw)
    elif case == "duplicate-members-last-wins":
        text = _json_text(payload).decode()
        text = text.replace('"schemaVersion":1', '"schemaVersion":2,"records":[{"slug":"ghost"}],"schemaVersion":1', 1)
        _rewrite(root, manifest, descriptor, text.encode())
    elif case == "duplicate-records-first-wins-is-wrong":
        text = _json_text(payload).decode().rstrip("\n")
        _rewrite(root, manifest, descriptor, (text[:-1] + ',"records":[]}\n').encode())
    elif case == "duplicate-slug":
        _, other = _entry_shard(root, manifest, 1)
        payload["records"].append(other["records"][0])
        _rewrite(root, manifest, descriptor, _json_text(payload))
        descriptor["count"] += 1
        (root / "manifest.json").write_bytes(exporter.canonical_json_bytes(manifest))
    elif case == "alias-target":
        record = next(r for r in payload["records"] if r["aliases"])
        record["aliases"][0]["target_slug"] = "elsewhere"
        record["aliases"].append({**record["aliases"][0]})
        _rewrite(root, manifest, descriptor, _json_text(payload))
    elif case == "kind-count":
        payload["records"][0]["kind"] = "something-else"
        _rewrite(root, manifest, descriptor, _json_text(payload))
    elif case == "record-not-object":
        payload["records"][0] = ["not", "an", "object"]
        _rewrite(root, manifest, descriptor, _json_text(payload))
    elif case == "records-missing":
        payload.pop("records")
        _rewrite(root, manifest, descriptor, _json_text(payload))
    elif case == "bigint-overflow-surrogate-in-record":
        text = _json_text(payload).decode()
        text = text.replace(
            '"kind":', '"n":123456789012345678901234567890,"big":-1e400,"u":"\\ud800","w":"\\udc00\\ud800\\u0041","kind":', 1
        )
        _rewrite(root, manifest, descriptor, text.encode())
    elif case == "extreme-numbers-in-record":
        # json.loads: 0.0, inf, 0.0, -0.0 and two exact 4300-digit integers (the default int limit).
        numbers = (
            '"u":1e-99999999999999999999,"o":1e99999999999999999999,"z":0e99999999999999999999,'
            f'"nz":-0e-99999999999999999999,"big":{"9" * 4300},"nbig":-{"9" * 4300},'
        )
        text = _json_text(payload).decode().replace('"kind":', numbers + '"kind":', 1)
        _rewrite(root, manifest, descriptor, text.encode())
    elif case == "int-past-digit-limit-in-record":
        raw = _json_text(payload).replace(b'"kind":', b'"n":' + b"9" * 4301 + b',"kind":', 1)
        _rewrite(root, manifest, descriptor, raw)
    elif case in ("extreme-exponent-duplicate-member", "extreme-exponent-last-member-wins"):
        extreme = b'"schemaVersion":1e99999999999999999999'
        if case == "extreme-exponent-duplicate-member":  # the extreme member is overridden: schemaVersion 1
            members = extreme + b',"schemaVersion":1'
        else:  # the extreme member wins: schemaVersion 0.0
            members = b'"schemaVersion":1,' + extreme.replace(b"1e", b"1e-")
        _rewrite(root, manifest, descriptor, _json_text(payload).replace(b'"schemaVersion":1', members, 1))
    elif case == "extreme-exponent-deck":
        # A correctly hashed deck the historical json.loads verify accepts (``unused`` is 0.0).
        deck = {"id": "a1/practice-index", "url": "decks/a1/practice-index.json.gz"}
        (root / "decks" / "a1").mkdir(parents=True)
        manifest["decks"] = {"levels": {"a1": {"parts": {"practice-index": deck}}}}
        _rewrite(root, manifest, deck, b'{"deckVersion":"d","unused":1e-99999999999999999999}\n')
    elif case == "nan-infinity-in-record":
        text = _json_text(payload).decode().replace('"kind":', '"f":NaN,"z":-Infinity,"kind":', 1)
        _rewrite(root, manifest, descriptor, text.encode())
    elif case == "surrogate-alias-target":
        # yajl alone decodes both unpaired escapes as "x?": only an exact decode sees the mismatch.
        record = next(r for r in payload["records"] if r["aliases"])
        record["slug"] = "@slug@"
        for alias in record["aliases"]:
            alias["target_slug"] = "@slug@"
        record["aliases"][0]["target_slug"] = "@target@"
        text = _json_text(payload).replace(b"@slug@", b"x\\ud800").replace(b"@target@", b"x\\udbff")
        _rewrite(root, manifest, descriptor, text)
    elif case == "trailing-unterminated-string":
        _rewrite(root, manifest, descriptor, _json_text(payload) + b'"x')
    elif case == "vertical-tab-whitespace":
        _rewrite(root, manifest, descriptor, _json_text(payload).replace(b'{"', b'{\x0b"', 1))
    elif case == "invalid-json-trailing":
        _rewrite(root, manifest, descriptor, _json_text(payload) + b"{}")
    elif case == "invalid-json-truncated":
        _rewrite(root, manifest, descriptor, _json_text(payload)[:-40])
    elif case == "invalid-json-trailing-comma":
        _rewrite(root, manifest, descriptor, _json_text(payload).replace(b"]}\n", b",]}\n"))
    elif case == "invalid-utf8":
        _rewrite(root, manifest, descriptor, _json_text(payload).replace(b'"slug":"', b'"slug":"\xff', 1))
    elif case == "control-char":
        _rewrite(root, manifest, descriptor, _json_text(payload).replace(b'"slug":"', b'"slug":"\x01', 1))
    elif case == "top-level-array":
        _rewrite(root, manifest, descriptor, b"[1,2]\n")
    else:
        raise AssertionError(case)
    (root / "manifest.json").write_bytes(exporter.canonical_json_bytes(manifest))


# Cases the historical verify let escape as a raw exception now fail as ExportError.
_HISTORICAL_CRASH = {
    "flip-byte": "gzip decode failed", "truncate": "gzip decode failed",
    "invalid-json-trailing": "invalid JSON", "invalid-json-truncated": "invalid JSON",
    "invalid-json-trailing-comma": "invalid JSON", "invalid-utf8": "invalid JSON",
    "control-char": "invalid JSON", "top-level-array": "payload must be an object",
    "trailing-unterminated-string": "invalid JSON", "vertical-tab-whitespace": "invalid JSON",
    "int-past-digit-limit-in-record": "invalid JSON",
}
# NaN/Infinity are json.loads extensions the runtime's JSON.parse rejects: they fail closed.
_FAIL_CLOSED = {"nan-infinity-in-record": "invalid JSON"}
_VERIFY_CASES = [
    "flip-byte", "flip-crc", "truncate", "trailing-zero-padding", "trailing-garbage-member", "second-gzip-member",
    "missing-object", "descriptor-bytes", "descriptor-count", "descriptor-json-sha", "stale-raw-descriptor",
    "schema-version", "schema-version-float", "schema-version-near-one", "data-version",
    "duplicate-members-last-wins", "duplicate-records-first-wins-is-wrong", "duplicate-slug", "alias-target",
    "kind-count", "record-not-object", "records-missing", "bigint-overflow-surrogate-in-record",
    "nan-infinity-in-record", "surrogate-alias-target", "invalid-json-trailing", "invalid-json-truncated",
    "invalid-json-trailing-comma", "invalid-utf8", "control-char", "top-level-array",
    "trailing-unterminated-string", "vertical-tab-whitespace", "extreme-numbers-in-record",
    "int-past-digit-limit-in-record", "extreme-exponent-duplicate-member", "extreme-exponent-last-member-wins",
    "extreme-exponent-deck",
]


_JSON_DOCS = [
    b'{"a":1}', b' \n{ "a" : [ 1 , 2.5 , -0.0 , 1e2 , "x" ] , "b" : {} }\t\r\n', b"{}", b"[]", b'"s"', b"-12", b'""',
    b'{"records":[{"k":1},{"k":[1,{"x":"\\u00e9\\ud83d\\ude00"}]},{}],"schemaVersion":1,"dataVersion":"v"}',
    b'{"n":123456789012345678901234567890,"big":1e400,"tiny":1e-400,"s":"\\ud800","t":"\\udc00\\ud800\\u0041",'
    b'"records":["\\ud800x","\\ud83d\\ude00","\\\\ud800",-9223372036854775809,1E+5,-0],"dataVersion":"\\udbff"}',
    '{"укр":"слово ґанок їжак","emoji":"😀","esc":"\\"\\\\\\/\\b\\f\\n\\r\\t"}'.encode(),
    b'{"a":1,"a":2,"records":[1],"records":[2,3],"schemaVersion":7,"schemaVersion":1}',
    b'{"records":[1.5,-1.25e-3,1E+5,0,true,false,null,"1.5"]}', b'{"records":{"not":"a list"}}',
    b'[{"a":1},[2,[3]],"x",4]', b'{"deep":' + b"[" * 200 + b"]" * 200 + b"}",
    # Exponents no Decimal holds, read as json.loads reads them (review of #8672).
    b'{"deckVersion":"d","unused":1e-99999999999999999999}',
    b'{"records":[1e99999999999999999999,-1e99999999999999999999,0e99999999999999999999,-0e-99999999999999999999,'
    b'1e-99999999999999999999,-0E+99999999999999999999,0.0e-99999999999999999999,1E+000000000000000000000000001,'
    b"1e999999999999999999,1e-999999999999999999,-0.0,-0]}",
    b'{"schemaVersion":1e99999999999999999999,"records":[],"schemaVersion":1,"dataVersion":-0e99999999999999999999}',
    b'{"records":[1],"schemaVersion":1,"schemaVersion":1e-99999999999999999999,"records":[2e99999999999999999999]}',
    # Integers up to the int limit stay exact; digit runs past it outside integers are fine.
    b'{"records":[' + b"9" * 4300 + b",-" + b"9" * 4300 + b"," + b"1" * 5000 + b".5," + b"2" * 5000 + b"e-400]}",
    b'[0.' + b"0" * 5000 + b"1,1e" + b"0" * 5000 + b"1,-0e" + b"9" * 5000 + b"]",
    # Digit runs and extreme exponents inside strings are only text, also where a run starts inside an escape.
    b'["\\ud9' + b"9" * 5000 + b'","\\u12' + b"3" * 5000 + b'","\\u0' + b"0" * 5000 + b'"]',
    b'{"s":"' + b"7" * 5000 + b'","records":["1e99999999999999999999","' + b"0" * 4301 + b'"],"dataVersion":"\\ud800"}',
]
_BAD_JSON_DOCS = [
    b"", b"   ", b'{"a":1} x', b'{"a":1}{}', b'{"a":1,}', b'{"a" 1}', b'{a:1}', b"[1,]", b"[1 2]", b'{"a":01}',
    b'{"a":tru}', b'{"a":"x\x01"}', b'{"a":"\xff"}', b'\xef\xbb\xbf{"a":1}', b'{"a":"unterminated}',
    b'{"records":[1,2', b'{"a":1', b'{"a":"\\x"}', b'{"a":"\\u12"}', b'{"a":1.}', b'{"a":-}', b'{"a":[1,2]]}',
    b'{"a":"\xed\xa0\x80"}', b"nul", b'{"a":1}\x00', b'{"a":+1}', b'{"a":1} 1', b'{"a":1}  "abc"', b'"" ""',
    # yajl alone accepts these: an unterminated string after the value, \v/\f as whitespace.
    b'{"a":1}"', b'{"a":1}\n"x', b'{"a":1}"}', b'[1]"', b'false "', b'\x0b{"a":1}', b'{"a":\x0c1}', b'{"a":1}\x0b',
    b'{"a":"\\ud800"}"', b'{"a":"\\ud800\\u12"}', b'{"a":"\\udc00" "b"}',
    # Numbers: past the int limit (json.loads raises ValueError), or not JSON numbers at all.
    b"[" + b"9" * 4301 + b"]", b'{"a":-' + b"9" * 4301 + b"}", b"[0" + b"0" * 5000 + b"]", b"[-0" + b"1" * 5000 + b"]",
    b'{"a":1e99999999999999999999x}', b"[1e]", b"[1e+]", b"[.5e99999999999999999999]", b"[1.e99999999999999999999]",
    b'{"a":1e99999999999999999999,}', b"[1e99999999999999999999 1]",
]
# json.loads extensions that fail closed: not JSON (the runtime's JSON.parse rejects NaN/Infinity).
_FAIL_CLOSED_JSON_DOCS = [b'{"f":NaN}', b'{"i":Infinity}', b"[-Infinity]", b'{"f":1,"records":[NaN]}']


def _scan(doc: bytes, read_bytes: int, summarize=json.dumps) -> exporter.ScannedPayload:
    """``scan_json_payload`` as ``verify_tree`` uses it: exact re-decode when the fast pass asks."""
    scanned = exporter.scan_json_payload(io.BytesIO(doc), summarize=summarize, read_bytes=read_bytes)
    if not scanned.values_exact:
        scanned = exporter.scan_json_payload(io.BytesIO(doc), summarize=summarize, read_bytes=read_bytes, exact=True)
        assert scanned.values_exact
    return scanned


def _reject_constant(name: str):
    raise ValueError(f"{name} fails closed")


def _expected_scan(doc: bytes) -> exporter.ScannedPayload:
    """``json.loads`` + ``dict.get`` view of ``doc``, minus the literals verification fails closed on."""
    value = json.loads(doc.decode("utf-8"), parse_constant=_reject_constant)
    if not isinstance(value, dict):
        return exporter.ScannedPayload(is_object=False)
    records = value.get("records")
    return exporter.ScannedPayload(
        is_object=True, schema_version=value.get("schemaVersion"), data_version=value.get("dataVersion"),
        has_records="records" in value, records_is_list=isinstance(records, list),
        record_count=len(records) if isinstance(records, list) else 0,
        rows=[json.dumps(item) for item in records] if isinstance(records, list) else None,
    )


def _scan_outcome(doc: bytes, read_bytes: int, *, exact_only: bool = False) -> tuple:
    """Everything verification reads from ``doc`` (or that it is invalid), for exact comparison.

    ``exact_only`` runs the exact decoder alone, without yajl's syntax verdict first.
    """
    try:
        if exact_only:
            scanned = exporter.scan_json_payload(
                io.BytesIO(doc), summarize=json.dumps, read_bytes=read_bytes, exact=True
            )
        else:
            scanned = _scan(doc, read_bytes)
    except ValueError:
        return ("invalid",)
    scanned.values_exact = True
    return ("ok", json.dumps(dataclasses.asdict(scanned), sort_keys=True))


def _json_loads_outcome(doc: bytes) -> tuple:
    try:
        expected = _expected_scan(doc)
    except (ValueError, ArithmeticError, RecursionError):
        return ("invalid",)
    return ("ok", json.dumps(dataclasses.asdict(expected), sort_keys=True))
