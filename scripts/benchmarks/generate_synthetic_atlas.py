#!/usr/bin/env python3
"""Seeded synthetic Atlas dataset generator (#8307).

Resamples real entries from ``data/atlas.db`` into a synthetic SQLite DB of a
target article count (default: the current VESUM lemma count, ~410k scale).
The output is byte-identical for a given (source DB, seed, target) triple, so
#8332 and #8310 can regenerate the exact same dataset after any worktree is
gone.

The dataset is SYNTHETIC and must never be published:

- every resampled article gets slug suffix ``--synNNNNNNN``;
- ``article_provenance.extraction_mode`` is ``synthetic_resample`` for copies;
- ``manifest_metadata`` gains ``dataset_kind = "synthetic-resample"`` and a
  ``synthetic_seed`` row.

Resampling copies whole coherent units (article + payload + aliases +
enrichment + provenance + related entries), so the export hard gates in
``scripts/atlas/export_runtime_shards.py`` keep holding: approved+public
articles equal public routes minus form-of routes, all public aliases resolve,
and per-entry CEFR agreement is preserved verbatim. Form-of route payloads
(payload rows without an ``articles`` row) are resampled as their own units at
their natural ratio.

Usage:

    .venv/bin/python -m scripts.benchmarks.generate_synthetic_atlas \
        --source-db data/atlas.db --out data/atlas-synthetic.db --seed 8307

    # target defaults to the VESUM distinct-lemma count:
    .venv/bin/python -m scripts.benchmarks.generate_synthetic_atlas --help
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sqlite3
import tempfile
import time
from pathlib import Path

from scripts.atlas.atlas_db import SCHEMA

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_SOURCE_DB = ROOT / "data" / "atlas.db"
DEFAULT_OUT = ROOT / "data" / "atlas-synthetic.db"
DEFAULT_VESUM_DB = ROOT / "data" / "vesum.db"
DEFAULT_SEED = 8307

SLUG_SUFFIX_TEMPLATE = "--syn{index:07d}"


def _open_readonly(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only = ON")
    return conn


def count_vesum_lemmas(vesum_db: Path) -> int:
    conn = _open_readonly(vesum_db)
    try:
        return int(conn.execute("SELECT COUNT(DISTINCT lemma) FROM forms_all").fetchone()[0])
    finally:
        conn.close()


class SourceSnapshot:
    """In-memory snapshot of the real Atlas units, indexed by slug."""

    def __init__(self, source_db: Path) -> None:
        conn = _open_readonly(source_db)
        try:
            self.articles: dict[str, tuple] = {}
            for row in conn.execute(
                "SELECT slug, display_head, lemma, entry_type, pos, gloss,"
                " review_state, visibility, cefr, heritage_classification,"
                " created_at, updated_at FROM articles ORDER BY slug"
            ):
                self.articles[row[0]] = row
            self.payloads: dict[str, tuple] = {}
            for row in conn.execute(
                "SELECT slug, route_order, payload_json, is_public_route FROM article_payloads ORDER BY slug"
            ):
                self.payloads[row[0]] = row
            self.form_route_slugs = sorted(s for s in self.payloads if s not in self.articles)
            self.aliases: dict[str, list[tuple]] = {}
            for row in conn.execute(
                "SELECT alias, kind, source, target_slug, visibility FROM aliases ORDER BY target_slug, alias"
            ):
                self.aliases.setdefault(row[3], []).append((*row[:3], row[4]))
            self.enrichment: dict[str, list[tuple]] = {}
            for row in conn.execute(
                "SELECT slug, section, payload_json, source, filled_at, phase FROM enrichment ORDER BY slug, section"
            ):
                self.enrichment.setdefault(row[0], []).append(row[1:])
            self.provenance: dict[str, list[tuple]] = {}
            for row in conn.execute(
                "SELECT slug, source_family, source_locator, extraction_mode FROM article_provenance ORDER BY slug"
            ):
                self.provenance.setdefault(row[0], []).append(row[1:])
            self.related: dict[str, list[tuple]] = {}
            for row in conn.execute(
                "SELECT slug, related_slug, entry_type, relation, component_role, provenance"
                " FROM related_entries ORDER BY slug"
            ):
                self.related.setdefault(row[0], []).append(row[1:])
            self.manifest_metadata = dict(conn.execute("SELECT key, value_json FROM manifest_metadata ORDER BY key"))
        finally:
            conn.close()


def _rewrite_payload_slug(payload_json: str, old_slug: str, new_slug: str) -> str:
    payload = json.loads(payload_json)
    if payload.get("url_slug") == old_slug:
        payload["url_slug"] = new_slug
    return json.dumps(payload, ensure_ascii=False)


def _validate_output_path(source_db: Path, out: Path) -> None:
    """Refuse aliases of the source and any existing non-synthetic output."""
    if out.resolve() == source_db.resolve() or (out.exists() and source_db.exists() and out.samefile(source_db)):
        raise ValueError("output must not be the source DB")
    if out.is_symlink():
        raise ValueError("output must not be a symlink")
    if not out.exists():
        return
    if not out.is_file():
        raise ValueError("output must be a regular file")
    try:
        conn = _open_readonly(out)
        try:
            row = conn.execute("SELECT value_json FROM manifest_metadata WHERE key = 'dataset_kind'").fetchone()
            if row is None or json.loads(row[0]) != "synthetic-resample":
                raise ValueError("refusing to overwrite a non-synthetic output")
        finally:
            conn.close()
    except (sqlite3.DatabaseError, json.JSONDecodeError) as exc:
        raise ValueError("refusing to overwrite an unrecognized output") from exc


def build_synthetic_db(
    *,
    source_db: Path,
    out: Path,
    seed: int,
    target_articles: int,
) -> dict[str, object]:
    _validate_output_path(source_db, out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".tmp", dir=out.parent)
    os.close(fd)
    temp_out = Path(temp_name)
    try:
        summary = _build_synthetic_db_unchecked(
            source_db=source_db, out=temp_out, seed=seed, target_articles=target_articles
        )
        _validate_output_path(source_db, out)
        os.replace(temp_out, out)
        summary["out"] = str(out)
        return summary
    finally:
        for path in (temp_out, Path(f"{temp_out}-wal"), Path(f"{temp_out}-shm")):
            path.unlink(missing_ok=True)


def _build_synthetic_db_unchecked(
    *, source_db: Path, out: Path, seed: int, target_articles: int
) -> dict[str, object]:
    started = time.monotonic()
    snapshot = SourceSnapshot(source_db)
    article_slugs = sorted(snapshot.articles)
    source_article_count = len(article_slugs)
    if target_articles < 1:
        raise ValueError(f"target_articles must be >= 1, got {target_articles}")
    if source_article_count == 0:
        raise ValueError("source DB has no articles")

    rng = random.Random(seed)
    if target_articles >= source_article_count:
        base_slugs = article_slugs
        copy_sources = [rng.choice(article_slugs) for _ in range(target_articles - source_article_count)]
    else:
        base_slugs = sorted(rng.sample(article_slugs, target_articles))
        copy_sources = []
    base_slug_set = set(base_slugs)

    # Form-of route payloads (no articles row) scale at their natural ratio.
    form_slugs = snapshot.form_route_slugs
    if target_articles >= source_article_count:
        form_copies = round(len(form_slugs) * (target_articles - source_article_count) / source_article_count)
        form_copy_sources = [rng.choice(form_slugs) for _ in range(form_copies)] if form_slugs else []
        form_base = form_slugs
    else:
        form_base = []
        form_copy_sources = (
            sorted(rng.sample(form_slugs, round(len(form_slugs) * target_articles / source_article_count)))
            if form_slugs
            else []
        )

    out.unlink()
    conn = sqlite3.connect(out)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    # related_entries rows can reference articles inserted later in the load;
    # defer FK enforcement to COMMIT (the whole dataset is present by then).
    conn.isolation_level = None
    conn.execute("BEGIN")
    conn.execute("PRAGMA defer_foreign_keys = ON")
    cur = conn.cursor()

    stats: dict[str, int] = {
        "articles": 0,
        "payloads": 0,
        "form_routes": 0,
        "aliases": 0,
        "enrichment": 0,
        "provenance": 0,
        "related": 0,
        "copies": 0,
    }

    def insert_article_unit(slug: str, row: tuple, *, synthetic_copy: bool) -> None:
        cur.execute(
            "INSERT INTO articles(slug, display_head, lemma, entry_type, pos, gloss,"
            " review_state, visibility, cefr, heritage_classification, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (slug, *row[1:]),
        )
        stats["articles"] += 1
        src_slug = row[0]
        payload = snapshot.payloads.get(src_slug)
        if payload is not None:
            payload_json = payload[2]
            if synthetic_copy:
                payload_json = _rewrite_payload_slug(payload_json, src_slug, slug)
            cur.execute(
                "INSERT INTO article_payloads(slug, route_order, payload_json, is_public_route) VALUES (?,?,?,?)",
                (slug, payload[1], payload_json, payload[3]),
            )
            stats["payloads"] += 1
        for alias, kind, source, visibility in snapshot.aliases.get(src_slug, []):
            cur.execute(
                "INSERT OR IGNORE INTO aliases(alias, kind, source, target_slug, visibility) VALUES (?,?,?,?,?)",
                (alias, kind, source, slug, visibility),
            )
            stats["aliases"] += 1
        for section, payload_json, source, filled_at, phase in snapshot.enrichment.get(src_slug, []):
            cur.execute(
                "INSERT INTO enrichment(slug, section, payload_json, source, filled_at, phase) VALUES (?,?,?,?,?,?)",
                (slug, section, payload_json, source, filled_at, phase),
            )
            stats["enrichment"] += 1
        for source_family, source_locator, extraction_mode in snapshot.provenance.get(src_slug, []):
            if synthetic_copy:
                extraction_mode = "synthetic_resample"
            cur.execute(
                "INSERT INTO article_provenance(slug, source_family, source_locator, extraction_mode) VALUES (?,?,?,?)",
                (slug, source_family, source_locator, extraction_mode),
            )
            stats["provenance"] += 1
        for rel in snapshot.related.get(src_slug, []):
            if rel[0] not in base_slug_set:
                continue
            cur.execute(
                "INSERT INTO related_entries(slug, related_slug, entry_type, relation, component_role, provenance)"
                " VALUES (?,?,?,?,?,?)",
                (slug, *rel),
            )
            stats["related"] += 1

    def insert_form_route_unit(slug: str, payload: tuple) -> None:
        payload_json = _rewrite_payload_slug(payload[2], payload[0], slug) if slug != payload[0] else payload[2]
        cur.execute(
            "INSERT INTO article_payloads(slug, route_order, payload_json, is_public_route) VALUES (?,?,?,?)",
            (slug, payload[1], payload_json, payload[3]),
        )
        stats["payloads"] += 1
        stats["form_routes"] += 1

    for slug in base_slugs:
        insert_article_unit(slug, snapshot.articles[slug], synthetic_copy=False)
    for slug in form_base:
        insert_form_route_unit(slug, snapshot.payloads[slug])
    for index, src_slug in enumerate(copy_sources):
        new_slug = f"{src_slug}{SLUG_SUFFIX_TEMPLATE.format(index=index)}"
        insert_article_unit(new_slug, snapshot.articles[src_slug], synthetic_copy=True)
        stats["copies"] += 1
    for index, src_slug in enumerate(form_copy_sources):
        new_slug = f"{src_slug}{SLUG_SUFFIX_TEMPLATE.format(index=index)}"
        insert_form_route_unit(new_slug, snapshot.payloads[src_slug])

    metadata = dict(snapshot.manifest_metadata)
    metadata["dataset_kind"] = json.dumps("synthetic-resample")
    metadata["synthetic_seed"] = json.dumps(seed)
    metadata["synthetic_source_articles"] = json.dumps(source_article_count)
    for key, value_json in sorted(metadata.items()):
        cur.execute(
            "INSERT INTO manifest_metadata(key, value_json) VALUES (?,?)",
            (key, value_json),
        )

    cur.execute(
        """INSERT INTO articles_fts(slug, display_head, lemma, gloss, aliases)
           SELECT a.slug, a.display_head, a.lemma, COALESCE(a.gloss,''),
                  COALESCE((SELECT group_concat(al.alias, ' ') FROM aliases al WHERE al.target_slug = a.slug), '')
           FROM articles a"""
    )
    conn.execute("COMMIT")
    conn.close()

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    return {
        "seed": seed,
        "target_articles": target_articles,
        "source_db": str(source_db),
        "out": str(out),
        "out_bytes": out.stat().st_size,
        "sha256": digest,
        "duration_seconds": round(time.monotonic() - started, 3),
        **stats,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Seeded synthetic Atlas dataset generator (#8307): resamples real "
            "data/atlas.db entries up to a target article count (default: the "
            "current VESUM distinct-lemma count). Same seed + same source DB "
            "produces a byte-identical output. The dataset is synthetic and "
            "must never be published. Use only for local scale tests."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples (from a checkout with its project interpreter):\n"
            "  .venv/bin/python -m scripts.benchmarks.generate_synthetic_atlas --help\n"
            "  .venv/bin/python -m scripts.benchmarks.generate_synthetic_atlas "
            "--source-db data/atlas.db --out /tmp/atlas-synthetic.db --seed 8307 --target 1000\n"
            "Outputs: a locally marked synthetic SQLite DB and a JSON summary; "
            "never uploads data.\n"
            "Exit codes: 0 on success; nonzero on invalid input or DB failure.\n"
            "Related: GitHub issue #8307 and scripts/atlas/export_runtime_shards.py."
        ),
    )
    parser.add_argument(
        "--source-db", type=Path, default=DEFAULT_SOURCE_DB,
        help="real Atlas SQLite DB to resample from, read-only (default: data/atlas.db)",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help="local synthetic DB path; only an existing synthetic DB may be replaced (default: data/atlas-synthetic.db)",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="integer RNG seed (default: 8307)")
    parser.add_argument(
        "--target",
        type=int,
        default=None,
        help="positive target article count (default: DISTINCT lemma count in --vesum-db)",
    )
    parser.add_argument(
        "--vesum-db", type=Path, default=DEFAULT_VESUM_DB,
        help="VESUM SQLite DB used for the default target (default: data/vesum.db)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = args.target if args.target is not None else count_vesum_lemmas(args.vesum_db)
    summary = build_synthetic_db(
        source_db=args.source_db,
        out=args.out,
        seed=args.seed,
        target_articles=target,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
