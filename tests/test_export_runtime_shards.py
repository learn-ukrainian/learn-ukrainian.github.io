"""Acceptance tests for the Atlas runtime shard exporter (PR #1 contract).

Core contract tests run against a committed hermetic fixture DB so CI does not
depend on the ~149 MB ``data/atlas.db``. Real-DB count assertions remain
opt-in via ``skipif`` when the full atlas is present locally.
"""

from __future__ import annotations

import gc
import gzip
import hashlib
import json
import os
import random
import shutil
import signal
import sqlite3
import subprocess
import sys
import threading
import tracemalloc
import unicodedata
from collections import defaultdict
from pathlib import Path

import pytest

from scripts.atlas import export_runtime_shards as exporter
from scripts.atlas.export_runtime_shards import (
    EntryReplay,
    ExportError,
    SearchFamilyIndex,
    StagedVersion,
    compress_stream_bounded,
    compute_data_version,
    export_runtime_shards,
    find_component_tokens,
    gzip_bytes,
    load_component_tokenization_vectors,
    load_entry_records,
    load_practice_levels_by_slug,
    load_search_rows,
    logical_tree_fingerprint,
    open_readonly_db,
    tree_fingerprint,
    verify_tree,
)
from scripts.atlas.normalization import load_normalization_vectors, normalize_atlas_text

ROOT = Path(__file__).resolve().parents[1]
REAL_DB_PATH = ROOT / "data" / "atlas.db"
FIXTURE_DB_PATH = ROOT / "tests" / "fixtures" / "atlas" / "runtime_shards_fixture.db"
COMMITTED_RUNTIME_TREE = ROOT / "tests" / "fixtures" / "atlas" / "runtime-tree"
PRACTICE_DECKS_ROOT = ROOT / "tests" / "fixtures" / "atlas" / "practice_decks"
EXPORTER_SCRIPT = ROOT / "scripts" / "atlas" / "export_runtime_shards.py"


@pytest.fixture(scope="module")
def fixture_db() -> Path:
    assert FIXTURE_DB_PATH.is_file(), f"missing fixture DB: {FIXTURE_DB_PATH}"
    return FIXTURE_DB_PATH


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
    fixture_db: Path, tmp_path: Path
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
    fresh = tmp_path / "fresh-export"
    export_runtime_shards(
        db_path=fixture_db,
        out_dir=fresh,
        deck_dir=None,
        include_decks=False,
        verify=True,
    )
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
    fixture_db: Path, tmp_path: Path
) -> None:
    """Corrupt-byte property: gz payload change / undecompressable → guard fails.

    Extends the fail-closed checksum surface (see ``test_trie_split_and_checksum_fail_closed``)
    to the logical freshness comparison used cross-platform.
    """
    fresh = tmp_path / "fresh-export"
    export_runtime_shards(
        db_path=fixture_db,
        out_dir=fresh,
        deck_dir=None,
        include_decks=False,
        verify=True,
    )
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


def test_search_families_remain_separate(fixture_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    current = json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "atlas" / current["manifestUrl"]).read_text(encoding="utf-8"))
    for desc in manifest["search"]["articles"]["shards"].values():
        assert desc["url"].startswith("search/articles/")
    for desc in manifest["search"]["aliases"]["shards"].values():
        assert desc["url"].startswith("search/aliases/")
    assert report["counts"]["searchArticles"] == report["counts"]["articles"]
    assert report["counts"]["searchAliases"] <= report["counts"]["aliases"]
    assert report["counts"]["searchAliases"] > 0


def test_exported_entry_records_match_sqlite_projection(fixture_db: Path, tmp_path: Path) -> None:
    """Export records must match the Sqlite data-source projection (parity input)."""
    out = tmp_path / "out"
    export_runtime_shards(
        db_path=fixture_db,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
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


def test_gzip_mtime_zero_and_newline_termination(fixture_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    export_runtime_shards(
        db_path=fixture_db,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
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

    conn = sqlite3.connect(f"file:{REAL_DB_PATH}?mode=ro", uri=True)
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


@pytest.fixture(scope="module")
def edge_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _make_source_db(tmp_path_factory.mktemp("edge") / "edge.db")


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


def test_fixture_export_is_byte_identical_to_reference(fixture_db: Path, tmp_path: Path) -> None:
    data_version, files, _ = _reference_export(
        fixture_db, compression_level=9, entry_max=8_000, search_max=1_000
    )
    out = tmp_path / "out"
    _export(fixture_db, out, entry_max_gzip_bytes=8_000, search_max_gzip_bytes=1_000)
    tree = _snapshot(out / "atlas" / "versions" / data_version)
    assert {name: blob for name, blob in tree.items() if name != "manifest.json"} == files


def test_replay_records_and_search_rows_match_reference_loaders(edge_db: Path, fixture_db: Path) -> None:
    for db in (edge_db, fixture_db):
        conn = open_readonly_db(db)
        try:
            expected = _ref_load_entry_records(conn, {"слово001": ["A1", "B1"]})
            replay = EntryReplay(conn, practice_levels_by_slug={"слово001": ["A1", "B1"]})
            assert list(replay.iter_records()) == expected
            assert [replay.record_for_slug(r["slug"]) for r in expected] == expected
            assert load_entry_records(conn, practice_levels_by_slug={"слово001": ["A1", "B1"]}) == expected
            assert load_search_rows(conn) == _ref_load_search_rows(conn)
        finally:
            conn.close()


def test_search_alias_dedup_keeps_reference_survivors(edge_db: Path) -> None:
    conn = open_readonly_db(edge_db)
    try:
        _, aliases = load_search_rows(conn)
        raw = conn.execute("SELECT COUNT(*) FROM aliases WHERE visibility = 'public'").fetchone()[0]
        assert len(aliases) < raw, "fixture must actually contain normalization duplicates"
        assert aliases == _ref_load_search_rows(conn)[1]
        assert len({(normalize_atlas_text(a["a"]), a["s"]) for a in aliases}) == len(aliases)
    finally:
        conn.close()


def test_unicode_search_order_follows_code_points(edge_db: Path) -> None:
    conn = open_readonly_db(edge_db)
    try:
        articles, _ = load_search_rows(conn)
    finally:
        conn.close()
    heads = [normalize_atlas_text(row["l"]) for row in articles]
    assert heads == sorted(heads)
    assert heads.index("ﬀ") < heads.index("\U0001f600"), "UTF-16 order would invert these"


def test_data_version_hasher_matches_reference_identity(edge_db: Path) -> None:
    conn = open_readonly_db(edge_db)
    try:
        records = _ref_load_entry_records(conn, {})
        articles, aliases = _ref_load_search_rows(conn)
    finally:
        conn.close()
    deck_index = {"levels": {"B1": {"deckVersion": "d2"}, "A1": {"deckVersion": "d1"}}}
    kwargs = {
        "generated_at": "2026-01-02T03:04:05+00:00", "article_rows": articles,
        "alias_rows": aliases, "deck_index": deck_index,
    }
    assert compute_data_version(entry_records=records, **kwargs) == _ref_data_version(
        entry_records=records, **kwargs
    )
    empty = {"generated_at": "g", "article_rows": [], "alias_rows": [], "deck_index": {"levels": {}}}
    assert compute_data_version(entry_records=[], **empty) == _ref_data_version(entry_records=[], **empty)


@pytest.mark.parametrize("level", [0, 1, 2, 5, 6, 9])
def test_stream_compression_matches_one_shot_gzip(level: int) -> None:
    rng = random.Random(level)
    text = "".join(rng.choice("абвгдеж abc012,.\n") for _ in range(400_000)).encode("utf-8")
    for size in (0, 1, 300, 70_000, len(text)):
        raw = text[:size]
        expected = gzip_bytes(raw, compression_level=level)
        for chunk in (1, 7, 4_096, 65_536 + 3):
            chunks = [raw[i : i + chunk] for i in range(0, len(raw), chunk)]
            result = compress_stream_bounded(chunks, compression_level=level, max_bytes=None)
            assert result is not None
            assert result.compressed == expected
            assert result.uncompressed_bytes == len(raw)
            assert result.json_sha256 == hashlib.sha256(raw).hexdigest()
            assert gzip.decompress(result.compressed) == raw
        # Exact cap boundary: fits at len, aborts at len - 1.
        chunks = [raw[i : i + 999] for i in range(0, len(raw), 999)]
        assert compress_stream_bounded(chunks, compression_level=level, max_bytes=len(expected)) is not None
        assert compress_stream_bounded(chunks, compression_level=level, max_bytes=len(expected) - 1) is None


def test_stream_compression_aborts_before_consuming_source() -> None:
    pulled = 0

    def source():
        nonlocal pulled
        rng = random.Random(1)
        while True:
            pulled += 1
            yield bytes(rng.getrandbits(8) for _ in range(4_096))

    for level in (0, 1, 9):
        pulled = 0
        assert compress_stream_bounded(source(), compression_level=level, max_bytes=20_000) is None
        assert pulled < 20, "an oversized candidate must stop the replay early"


def test_oversized_entry_leaf_matches_reference_error(edge_db: Path, tmp_path: Path) -> None:
    with pytest.raises(ExportError) as expected:
        _reference_export(edge_db, compression_level=9, entry_max=300, search_max=524_288)
    with pytest.raises(ExportError) as actual:
        _export(edge_db, tmp_path / "out", entry_max_gzip_bytes=300)
    assert str(actual.value) == str(expected.value)
    assert "single entry record exceeds" in str(actual.value)
    assert not (tmp_path / "out" / "atlas" / "current.json").exists()


def test_unsplittable_search_shard_matches_reference_error(edge_db: Path, tmp_path: Path) -> None:
    with pytest.raises(ExportError) as expected:
        _reference_export(edge_db, compression_level=9, entry_max=1_048_576, search_max=150)
    with pytest.raises(ExportError) as actual:
        _export(edge_db, tmp_path / "out", search_max_gzip_bytes=150)
    assert str(actual.value) == str(expected.value)
    assert "cannot split" in str(actual.value)


def test_failed_first_export_publishes_nothing(edge_db: Path, tmp_path: Path, monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise RuntimeError("injected")

    monkeypatch.setattr(exporter, "verify_tree", boom)
    out = tmp_path / "out"
    with pytest.raises(RuntimeError, match="injected"):
        _export(edge_db, out)
    assert not (out / "atlas" / "current.json").exists()
    assert _snapshot(out) == {}, "no staged objects may remain"


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


@pytest.mark.parametrize("stage", _REEXPORT_STAGES)
def test_failed_reexport_keeps_current_pointer_and_referenced_tree_byte_identical(
    edge_db: Path, tmp_path: Path, monkeypatch, stage: str
) -> None:
    out = tmp_path / "out"
    kwargs = {"entry_max_gzip_bytes": 9_000, "search_max_gzip_bytes": 1_200}
    report = _export(edge_db, out, **kwargs)
    before = _snapshot(out)
    current = json.loads(before["atlas/current.json"])
    assert current["dataVersion"] == report["dataVersion"]  # re-export targets the referenced version
    total_objects = sum(1 for name in before if name.startswith(f"atlas/versions/{report['dataVersion']}/"))
    transport = stage.endswith("-transport")
    reexport = {**kwargs, "compression_level": 6} if transport else kwargs

    real_rename, real_replace = os.rename, os.replace
    if stage == "first-leaf":
        _fail_after_writes(monkeypatch, 0)
    elif stage == "mid-export":
        _fail_after_writes(monkeypatch, total_objects // 2)
    elif stage == "manifest":
        _fail_after_writes(monkeypatch, total_objects - 1)
    elif stage == "verify":
        monkeypatch.setattr(exporter, "verify_tree", lambda *a, **k: (_ for _ in ()).throw(_Injected("verify")))
    elif stage == "swap-transport":
        def rename(src, dst, *a, **k):
            if Path(src).name.startswith(".export-"):
                raise _Injected("swap")
            return real_rename(src, dst, *a, **k)

        monkeypatch.setattr(exporter.os, "rename", rename)
    else:
        def replace(src, dst, *a, **k):
            if Path(dst).name == "current.json":
                raise _Injected("pointer")
            return real_replace(src, dst, *a, **k)

        monkeypatch.setattr(exporter.os, "replace", replace)

    with pytest.raises(_Injected):
        _export(edge_db, out, **reexport)
    monkeypatch.undo()
    after = _snapshot(out)
    # The pointer and every previously installed object are byte-identical; the only
    # thing a failure may leave is a complete, unreferenced alternate tree.
    assert {name: blob for name, blob in after.items() if name in before} == before
    assert all(
        name.startswith(f"atlas/versions/{report['dataVersion']}-transport-") for name in after.keys() - before.keys()
    )
    if stage != "pointer-transport":
        assert after.keys() == before.keys()
    assert verify_tree(out, "atlas")["dataVersion"] == report["dataVersion"]
    assert _snapshot(out) == after

    # And a subsequent healthy re-export still succeeds and the referenced tree is intact.
    _export(edge_db, out, **reexport)
    healed = _snapshot(out)
    assert {name: blob for name, blob in healed.items() if name in before and name != "atlas/current.json"} == {
        name: blob for name, blob in before.items() if name != "atlas/current.json"
    }
    assert verify_tree(out, "atlas")["dataVersion"] == report["dataVersion"]
    if not transport:
        assert healed == before


def test_stale_staging_from_killed_export_is_reclaimed(edge_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    versions = out / "atlas" / "versions"
    dead = versions / ".export-999999999-deadbeef"
    dead.mkdir(parents=True)
    (dead / "orphan.bin").write_bytes(b"x")
    alive = versions / f".export-{os.getpid()}-cafebabe"
    alive.mkdir()
    _export(edge_db, out)
    assert not dead.exists()
    assert alive.exists(), "another live exporter's staging tree must not be touched"


def test_export_memory_is_bounded_by_leaf_not_corpus(tmp_path: Path) -> None:
    """Peak Python heap stays a small fraction of the payload volume being exported."""
    db = _make_source_db(tmp_path / "big.db", records=240, filler_chars=60_000, seed=5)
    payload_bytes = sum(
        len(row[0]) for row in sqlite3.connect(db).execute("SELECT payload_json FROM article_payloads")
    )
    assert payload_bytes > 14_000_000
    tracemalloc.start()
    try:
        _export(db, tmp_path / "out", compression_level=1, entry_max_gzip_bytes=150_000)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < payload_bytes * 0.25, f"peak {peak} vs payload {payload_bytes}"


# ---------------------------------------------------------------------------
# Published trees are immutable; the pointer is switched last (review of #8672).
# ---------------------------------------------------------------------------


def _pointer(out: Path) -> dict:
    return json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))


def _pointed_manifest(out: Path) -> Path:
    return out / "atlas" / _pointer(out)["manifestUrl"]


def _version_dirs(out: Path) -> list[str]:
    return sorted(p.name for p in (out / "atlas" / "versions").iterdir() if not p.name.startswith("."))


def test_identical_reexport_reuses_installed_tree_untouched(edge_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = _export(edge_db, out)
    tree = out / "atlas" / "versions" / report["dataVersion"]
    before, stat = _snapshot(out), tree.stat()
    again = _export(edge_db, out)
    assert _snapshot(out) == before
    assert tree.stat().st_ino == stat.st_ino and tree.stat().st_mtime_ns == stat.st_mtime_ns
    assert _version_dirs(out) == [report["dataVersion"]]
    assert report["manifestUrl"] == again["manifestUrl"] == f"versions/{report['dataVersion']}/manifest.json"


_CHANGED_LIMITS = [
    {"compression_level": 6},
    {"entry_max_gzip_bytes": 6_000},
    {"search_max_gzip_bytes": 700},
    {"entry_target_min_gzip_bytes": 1_000},
]


@pytest.mark.parametrize("changed", _CHANGED_LIMITS, ids=lambda item: next(iter(item)))
def test_changed_limits_keep_every_old_url_and_publish_alternate_tree(
    edge_db: Path, tmp_path: Path, changed: dict
) -> None:
    out = tmp_path / "out"
    base = {"entry_max_gzip_bytes": 9_000, "search_max_gzip_bytes": 1_200}
    first = _export(edge_db, out, **base)
    old_manifest = _pointed_manifest(out)
    before = _snapshot(out)

    second = _export(edge_db, out, **{**base, **changed})

    assert second["dataVersion"] == first["dataVersion"]  # same data, different transport bytes
    after = _snapshot(out)
    assert {name: blob for name, blob in after.items() if name in before and name != "atlas/current.json"} == {
        name: blob for name, blob in before.items() if name != "atlas/current.json"
    }, "no previously published URL may change or disappear"
    new_root = _pointed_manifest(out).parent
    assert new_root.name == f"{first['dataVersion']}-transport-{exporter._tree_digest(new_root)}"
    assert second["manifestUrl"] == _pointer(out)["manifestUrl"] == f"versions/{new_root.name}/manifest.json"
    assert verify_tree(out, "atlas")["dataVersion"] == first["dataVersion"]
    # An old-manifest reader stays valid after the pointer switched.
    assert old_manifest.is_file()
    assert verify_tree(out, "atlas", manifest_path=old_manifest)["dataVersion"] == first["dataVersion"]

    # Repeating the changed export reuses the alternate tree; the original limits point back home.
    settled = _snapshot(out)
    _export(edge_db, out, **{**base, **changed})
    assert _snapshot(out) == settled
    _export(edge_db, out, **base)
    assert _pointer(out)["manifestUrl"] == first["manifestUrl"]
    assert len(_version_dirs(out)) == 2


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


@pytest.mark.parametrize(
    ("point", "changed"),
    # An identical re-export installs nothing (it reuses the tree), so only its pointer switch can be killed.
    [(point, True) for point in _KILL_POINTS] + [("before-pointer", False), ("after-pointer", False)],
)
def test_sigkill_during_publication_always_leaves_pointer_to_complete_tree(
    edge_db: Path, tmp_path: Path, point: str, changed: bool
) -> None:
    out = tmp_path / "out"
    base = {"entry_max_gzip_bytes": 9_000, "search_max_gzip_bytes": 1_200}
    first = _export(edge_db, out, **base)
    old_pointer = (out / "atlas" / "current.json").read_bytes()
    old_manifest = _pointed_manifest(out)
    old_tree = _snapshot(old_manifest.parent)

    _run_killed(edge_db, out, point, **({**base, "compression_level": 6} if changed else base))

    assert _snapshot(old_manifest.parent) == old_tree, "the published tree is never touched"
    result = verify_tree(out, "atlas")  # pointer resolves to a complete, verifying tree
    assert result["dataVersion"] == first["dataVersion"]
    if point != "after-pointer" or not changed:
        assert (out / "atlas" / "current.json").read_bytes() == old_pointer
    else:
        assert _pointed_manifest(out).parent.name.startswith(f"{first['dataVersion']}-transport-")
    assert verify_tree(out, "atlas", manifest_path=old_manifest)["dataVersion"] == first["dataVersion"]

    # The next healthy run cleans the dead staging tree and converges.
    _export(edge_db, out, **({**base, "compression_level": 6} if changed else base))
    assert not [name for name in os.listdir(out / "atlas" / "versions") if name.startswith(".export-")]
    assert not list((out / "atlas").glob(".current-*"))
    assert verify_tree(out, "atlas")["dataVersion"] == first["dataVersion"]


@pytest.mark.parametrize("point", _KILL_POINTS)
def test_sigkill_during_first_export_never_publishes_a_dangling_pointer(
    edge_db: Path, tmp_path: Path, point: str
) -> None:
    out = tmp_path / "out"
    _run_killed(edge_db, out, point)
    pointer = out / "atlas" / "current.json"
    if point == "after-pointer":
        assert verify_tree(out, "atlas")["publicRoutes"] > 0
    else:
        assert not pointer.exists()
    report = _export(edge_db, out)
    assert verify_tree(out, "atlas")["dataVersion"] == report["dataVersion"]


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


def test_install_reuses_identical_and_never_overwrites_different(tmp_path: Path) -> None:
    base = tmp_path / "atlas"
    assert _publish_synthetic(base, "atlas-v1-x", _TREE_A) == "atlas-v1-x"
    canonical = base / "versions" / "atlas-v1-x"
    inode = canonical.stat().st_ino
    assert _publish_synthetic(base, "atlas-v1-x", _TREE_A) == "atlas-v1-x"
    assert canonical.stat().st_ino == inode

    digest = exporter._tree_digest(_synthetic_stage(base, "atlas-v1-x", _TREE_B).root)
    name = _publish_synthetic(base, "atlas-v1-x", _TREE_B)
    assert name == f"atlas-v1-x-transport-{digest}"
    assert _snapshot(canonical) == _TREE_A
    assert _publish_synthetic(base, "atlas-v1-x", _TREE_B) == name  # identical suffix is reused
    assert _version_dirs(tmp_path) == sorted(["atlas-v1-x", name])


def test_transport_collision_with_different_bytes_fails_closed(tmp_path: Path) -> None:
    base = tmp_path / "atlas"
    _publish_synthetic(base, "atlas-v1-x", _TREE_A)
    probe = _synthetic_stage(base, "atlas-v1-x", _TREE_B)
    squatter = base / "versions" / f"atlas-v1-x-transport-{exporter._tree_digest(probe.root)}"
    probe.discard()
    squatter.mkdir()
    (squatter / "manifest.json").write_bytes(b"squatter")
    with pytest.raises(ExportError, match="refusing to overwrite"):
        _publish_synthetic(base, "atlas-v1-x", _TREE_B)
    assert _snapshot(squatter) == {"manifest.json": b"squatter"}
    assert _snapshot(base / "versions" / "atlas-v1-x") == _TREE_A


@pytest.mark.parametrize("winner", ["identical", "different"])
def test_concurrent_destination_creation_never_overwrites_the_winner(
    tmp_path: Path, monkeypatch, winner: str
) -> None:
    base = tmp_path / "atlas"
    loser = _synthetic_stage(base, "atlas-v1-x", _TREE_A)
    rival = _synthetic_stage(base, "atlas-v1-x", _TREE_A if winner == "identical" else _TREE_B)
    real_rename = os.rename
    state = {"raced": False}

    def rename(src, dst, *a, **k):
        if Path(src) == loser.root and not state["raced"]:
            state["raced"] = True  # the rival lands on the canonical destination first
            real_rename(rival.root, Path(dst))
        return real_rename(src, dst, *a, **k)

    monkeypatch.setattr(exporter.os, "rename", rename)
    name = loser.install()
    loser.discard()
    monkeypatch.undo()
    canonical = base / "versions" / "atlas-v1-x"
    assert _snapshot(canonical) == (_TREE_A if winner == "identical" else _TREE_B)
    if winner == "identical":
        assert name == "atlas-v1-x"
        assert _version_dirs(tmp_path) == ["atlas-v1-x"]
    else:
        assert name.startswith("atlas-v1-x-transport-")
        assert _snapshot(base / "versions" / name) == _TREE_A


def test_concurrent_publishers_do_not_overwrite_each_other(tmp_path: Path) -> None:
    base = tmp_path / "atlas"
    trees = [_TREE_A, _TREE_B] * 3
    barrier = threading.Barrier(len(trees))
    outcomes: list[tuple[dict[str, bytes], str]] = []
    errors: list[BaseException] = []

    def worker(files: dict[str, bytes]) -> None:
        try:
            stage = _synthetic_stage(base, "atlas-v1-x", files)
            barrier.wait(timeout=30)
            try:
                outcomes.append((files, stage.publish(lambda url: json.dumps({"manifestUrl": url}).encode())))
            finally:
                stage.discard()
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(files,)) for files in trees]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert not errors, errors
    assert len(outcomes) == len(trees)
    for files, manifest_url in outcomes:
        assert _snapshot((base / manifest_url).parent) == files
    installed = _version_dirs(tmp_path)
    assert len(installed) == 2 and "atlas-v1-x" in installed
    assert (base / json.loads((base / "current.json").read_text())["manifestUrl"]).is_file()


def test_concurrent_full_exports_with_different_limits_all_stay_valid(edge_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    variants = [{"compression_level": 9}, {"compression_level": 6}] * 2
    errors: list[BaseException] = []

    def worker(kwargs: dict) -> None:
        try:
            _export(edge_db, out, **kwargs)
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(kwargs,)) for kwargs in variants]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=110)
    assert not errors, errors
    dirs = _version_dirs(out)
    assert len(dirs) == 2
    for name in dirs:
        assert verify_tree(out, "atlas", manifest_path=out / "atlas" / "versions" / name / "manifest.json")
    assert verify_tree(out, "atlas")["dataVersion"]


def test_stale_pending_pointer_from_killed_export_is_reclaimed(edge_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    base = out / "atlas"
    base.mkdir(parents=True)
    dead = base / ".current-999999999-deadbeef.json"
    dead.write_bytes(b"{}")
    alive = base / f".current-{os.getpid()}-cafebabe.json"
    alive.write_bytes(b"{}")
    _export(edge_db, out)
    assert not dead.exists()
    assert alive.exists()


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


def test_replayed_search_fragments_match_reference_rows_and_order(edge_db: Path, fixture_db: Path) -> None:
    for db in (edge_db, fixture_db):
        conn = open_readonly_db(db)
        try:
            conn.execute("BEGIN")
            articles, aliases = _build_indexes(conn)
            ref_articles, ref_aliases = _ref_load_search_rows(conn)
            assert list(articles.iter_fragments()) == [exporter._fragment_bytes(row) for row in ref_articles]
            assert list(aliases.iter_fragments()) == [exporter._fragment_bytes(row) for row in ref_aliases]
            assert not hasattr(articles, "fragments") and not hasattr(aliases, "fragments")
        finally:
            conn.close()


def test_search_index_memory_follows_key_metadata_not_gloss_bodies(tmp_path: Path) -> None:
    retained: dict[int, int] = {}
    bodies: dict[int, int] = {}
    for gloss_chars in (60, 20_000):
        db = _make_source_db(tmp_path / f"g{gloss_chars}.db", records=700, filler_chars=1, gloss_chars=gloss_chars)
        conn = open_readonly_db(db)
        try:
            conn.execute("BEGIN")
            bodies[gloss_chars] = sum(len(r[0] or "") for r in conn.execute("SELECT gloss FROM articles"))
            gc.collect()
            tracemalloc.start()
            try:
                before = tracemalloc.get_traced_memory()[0]
                articles, aliases = _build_indexes(conn)
                gc.collect()
                retained[gloss_chars] = tracemalloc.get_traced_memory()[0] - before
                assert len(articles) > 600 and len(aliases) > 600
            finally:
                tracemalloc.stop()
            del articles, aliases
        finally:
            conn.close()
    assert bodies[20_000] > 10_000_000
    assert retained[20_000] < retained[60] * 1.25, retained
    assert retained[20_000] < bodies[20_000] * 0.25, (retained, bodies)


def test_export_memory_does_not_grow_with_gloss_bodies(tmp_path: Path) -> None:
    db = _make_source_db(tmp_path / "gloss.db", records=700, filler_chars=1, gloss_chars=20_000)
    glosses = sum(len(r[0] or "") for r in sqlite3.connect(db).execute("SELECT gloss FROM articles"))
    assert glosses > 10_000_000
    tracemalloc.start()
    try:
        # No --verify: verify_tree inflates whole shards by design and is not the exporter's memory.
        export_runtime_shards(
            db_path=db, out_dir=tmp_path / "out", include_decks=False, deck_dir=None, compression_level=1
        )
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < glosses * 0.25, f"peak {peak} vs gloss bodies {glosses}"


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


def _build_aliases_traced(index: SearchFamilyIndex, out: Path, *, level: int) -> tuple[str | None, int]:
    """(ExportError text or None, traced heap peak) of one search-family build into ``out``."""

    def open_object(relative: str):
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open("wb")

    gc.collect()
    tracemalloc.start()
    try:
        try:
            exporter.build_search_family_shards(
                index, family="aliases", data_version="v-test", max_gzip_bytes=_SHARED_KEY_CAP,
                compression_level=level, schema=exporter.SEARCH_ALIAS_SCHEMA, open_object=open_object,
            )
            error = None
        except ExportError as exc:
            error = str(exc)
        return error, tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


@pytest.mark.parametrize("terminal", [False, True], ids=["unsplittable", "terminal"])
@pytest.mark.parametrize("level", [0, 1, 6, 9])
def test_uncapped_search_bucket_is_exact_and_heap_does_not_grow_with_it(
    tmp_path: Path, level: int, terminal: bool
) -> None:
    peaks: dict[int, int] = {}
    bodies: dict[int, int] = {}
    for rows in (250, 1_000):
        index, records = _shared_key_alias_index(rows, terminal=terminal)
        raw = _search_shard_raw(exporter.SEARCH_ALIAS_SCHEMA, "a", records, terminal=terminal)
        expected = gzip_bytes(raw, compression_level=level)
        assert len(expected) > 20 * _SHARED_KEY_CAP
        out = tmp_path / f"rows{rows}"
        error, peaks[rows] = _build_aliases_traced(index, out, level=level)
        bodies[rows] = len(raw)
        if terminal:
            assert error is None
            shard = f"search/aliases/{exporter.search_shard_id('a')}.term.json.gz"
            assert (out / shard).read_bytes() == expected
        else:
            assert error == (
                f"search aliases shard for prefix='a' exceeds max "
                f"({len(expected)} > {_SHARED_KEY_CAP}) and cannot split"
            )
            assert not out.exists(), "a failing bucket writes nothing"
    if level == 0:
        # Residual: stored-block framing of the one-shot gzip follows the whole input,
        # so level 0 keeps exact bytes by buffering the uncapped object (capped
        # probes still abort once raw bytes pass the cap).
        return
    assert bodies[1_000] > 4 * bodies[250] * 0.95
    assert peaks[1_000] < peaks[250] * 1.25, peaks
    assert peaks[1_000] < bodies[1_000] * 0.2, (peaks, bodies)


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
    gc.collect()
    tracemalloc.start()
    try:
        try:
            # No --verify: verify_tree inflates whole shards by design and is not the exporter's memory.
            export_runtime_shards(
                db_path=db, out_dir=out, include_decks=False, deck_dir=None, compression_level=level,
                entry_max_gzip_bytes=65_536, search_max_gzip_bytes=_SHARED_KEY_CAP,
            )
            error = None
        except ExportError as exc:
            error = str(exc)
        return error, tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


@pytest.mark.parametrize("terminal", [False, True], ids=["unsplittable", "terminal"])
def test_reviewer_long_article_rows_export_matches_reference_in_bounded_heap(
    tmp_path: Path, terminal: bool
) -> None:
    peaks: dict[int, int] = {}
    glosses: dict[int, int] = {}
    for rows in (250, 1_000):
        db = _make_shared_key_db(tmp_path / f"shared{rows}.db", rows=rows, terminal=terminal)
        glosses[rows] = sum(len(r[0]) for r in sqlite3.connect(db).execute("SELECT gloss FROM articles"))
        out = tmp_path / f"out{rows}"
        error, peaks[rows] = _export_traced(db, out, level=9)
        if terminal:
            assert error is None
            data_version, files, indexes = _reference_export(
                db, compression_level=9, entry_max=65_536, search_max=_SHARED_KEY_CAP
            )
            tree = _snapshot(out / "atlas" / "versions" / data_version)
            assert {name: blob for name, blob in tree.items() if name != "manifest.json"} == files
            manifest = json.loads(tree["manifest.json"])
            assert manifest["search"]["articles"] == indexes["articles"]
            term = indexes["articles"]["shards"][f"{exporter.search_shard_id('a')}.term"]
            assert term["count"] == rows and term["bytes"] > 20 * _SHARED_KEY_CAP
        else:
            with pytest.raises(ExportError) as expected:
                _reference_export(db, compression_level=9, entry_max=65_536, search_max=_SHARED_KEY_CAP)
            assert error == str(expected.value)
            assert "prefix='a'" in error and "cannot split" in error
            assert not (out / "atlas" / "current.json").exists()
    assert glosses[1_000] > 7_900_000
    # Per-row index metadata (locators, sort keys, route digests) may grow; shard
    # bodies may not: the old exporter's heap grew by the whole compressed bucket.
    assert peaks[1_000] - peaks[250] < (glosses[1_000] - glosses[250]) * 0.25, (peaks, glosses)
    assert peaks[1_000] < glosses[1_000] * 0.25, (peaks, glosses)


@pytest.mark.parametrize("terminal", [False, True], ids=["unsplittable", "terminal"])
def test_reviewer_long_article_rows_level0_bytes_and_error_match_reference(
    tmp_path: Path, terminal: bool
) -> None:
    db = _make_shared_key_db(tmp_path / "shared.db", rows=120, terminal=terminal, gloss_chars=600)
    out = tmp_path / "out"
    error, _ = _export_traced(db, out, level=0)
    if terminal:
        assert error is None
        data_version, files, _ = _reference_export(
            db, compression_level=0, entry_max=65_536, search_max=_SHARED_KEY_CAP
        )
        tree = _snapshot(out / "atlas" / "versions" / data_version)
        assert {name: blob for name, blob in tree.items() if name != "manifest.json"} == files
        assert any(name.endswith(".term.json.gz") for name in files)
    else:
        with pytest.raises(ExportError) as expected:
            _reference_export(db, compression_level=0, entry_max=65_536, search_max=_SHARED_KEY_CAP)
        assert error == str(expected.value)


@pytest.mark.parametrize("level", [0, 1, 6, 9])
def test_gzip_size_and_streamed_sink_match_one_shot_without_retention(level: int) -> None:
    rng = random.Random(level + 100)
    raw = "".join(rng.choice("абвгдеж abc012,.\n") for _ in range(300_000)).encode("utf-8")
    chunks = [raw[i : i + 5_000] for i in range(0, len(raw), 5_000)]
    expected = gzip_bytes(raw, compression_level=level)
    assert exporter.gzip_size(iter(chunks), compression_level=level) == len(expected)
    pieces: list[bytes] = []
    result = exporter.stream_gzip(iter(chunks), compression_level=level, sink=pieces.append)
    assert b"".join(pieces) == expected
    assert result == exporter.GzipResult(
        len(expected), hashlib.sha256(expected).hexdigest(), len(raw), hashlib.sha256(raw).hexdigest()
    )
    if level:
        assert len(pieces) > 2, "levels 1-9 hand compressed pieces over as they are produced"
