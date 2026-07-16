#!/usr/bin/env python3
"""Build the hermetic ``runtime_shards_fixture.db`` used by exporter + route parity.

Requires a full ``data/atlas.db`` locally (or ``ATLAS_SRC_DB``). The committed
fixture is small and CI-safe; regenerate when representative rows change:

  ATLAS_SRC_DB=/path/to/atlas.db \\
    .venv/bin/python tests/fixtures/atlas/build_runtime_shards_fixture.py

PR #2 extends the fixture with test-only rows so EVERY ``ATLAS_ENTRY_TYPES``
value plus ``form_route`` is present (production currently only ships lemma +
multiword_term).
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

from scripts.atlas import atlas_db
from scripts.atlas.export_runtime_shards import (
    _site_build_entry_model_gates,
    export_runtime_shards,
    load_entry_records,
    open_readonly_db,
)

SRC_CANDIDATES: list[Path] = []
if os.environ.get("ATLAS_SRC_DB"):
    SRC_CANDIDATES.append(Path(os.environ["ATLAS_SRC_DB"]))
for base in [ROOT, *ROOT.parents]:
    SRC_CANDIDATES.append(base / "data" / "atlas.db")
SRC = next((path for path in SRC_CANDIDATES if path.is_file()), None)
DST = Path(__file__).resolve().parent / "runtime_shards_fixture.db"

# Must match site/src/lib/lexicon/atlasDb.ts ATLAS_ENTRY_TYPES plus form_route.
REQUIRED_TYPE_SET = {
    "lemma",
    "expression",
    "phraseologism",
    "proverb",
    "multiword_term",
    "proper_name",
    "form_route",
}

WANTED_ARTICLES = {
    "прапор",  # rich lemma + marked morphology
    "файний",  # heritage warning_severity treasured
    "достовірний",  # russianism heritage classification
    "іван",  # form_of target
    "ілля",  # proper name surface (stored as lemma in prod)
    "ласка",  # component lemma for будь ласка
    "будь-ласка",  # multiword (partial component link)
    "доконаний",  # component lemma
    "вид",  # component lemma
    "доконаний-вид",  # multiword + resolved component links
}
WANTED_FORM_ROUTES = {"іване"}  # form_of → іван
MISSING_SENTINEL = "fixture-missing-sentinel"

# Test-only articles covering entry types absent from current production data.
SYNTHETIC_ARTICLES: list[dict[str, object]] = [
    {
        "slug": "fixture-expression",
        "entry_type": "expression",
        "lemma": "на добраніч",
        "display_head": "на добраніч",
        "gloss": "good night",
        "pos": "phrase",
    },
    {
        "slug": "fixture-phraseologism",
        "entry_type": "phraseologism",
        "lemma": "бити байдики",
        "display_head": "бити байдики",
        "gloss": "to idle",
        "pos": "phrase",
    },
    {
        "slug": "fixture-proverb",
        "entry_type": "proverb",
        "lemma": "без праці нема калача",
        "display_head": "без праці нема калача",
        "gloss": "no pain, no gain",
        "pos": "phrase",
    },
    {
        "slug": "fixture-proper-name",
        "entry_type": "proper_name",
        "lemma": "Київ",
        "display_head": "Київ",
        "gloss": "Kyiv",
        "pos": "name",
    },
]


def _copy_rows(
    src: sqlite3.Connection,
    dst: sqlite3.Connection,
    table: str,
    where: str,
    params: tuple[object, ...] = (),
) -> int:
    cols = [row[1] for row in src.execute(f"PRAGMA table_info({table})")]
    rows = src.execute(f"SELECT * FROM {table} WHERE {where}", params).fetchall()
    placeholders = ",".join("?" * len(cols))
    col_list = ",".join(cols)
    for row in rows:
        dst.execute(
            f"INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({placeholders})",
            [row[col] for col in cols],
        )
    return len(rows)


def _trim_morph(morph: object) -> tuple[object, bool]:
    if not isinstance(morph, dict):
        return morph, False
    changed = False
    out = dict(morph)
    forms = out.get("forms")
    if isinstance(forms, list) and len(forms) > 8:
        out["forms"] = forms[:8]
        out["form_count"] = len(out["forms"])
        changed = True
    marked = out.get("marked_forms")
    if isinstance(marked, list) and len(marked) > 8:
        out["marked_forms"] = marked[:8]
        out["marked_form_count"] = len(out["marked_forms"])
        changed = True
    return out, changed


def _payload_for_synthetic(article: dict[str, object]) -> str:
    payload = {
        "lemma": article["lemma"],
        "url_slug": article["slug"],
        "gloss": article["gloss"],
        "pos": article["pos"],
        "ipa": None,
        "primary_source": "fixture",
        "course_usage": [],
        "enrichment": {
            "meaning": {
                "definitions": [f"fixture {article['entry_type']} meaning"],
                "source": "fixture",
            },
            "sources": ["fixture"],
        },
        "heritage_status": None,
        "sections": None,
    }
    return json.dumps(payload, ensure_ascii=False)


def _insert_synthetic(dst: sqlite3.Connection) -> None:
    max_order = dst.execute("SELECT COALESCE(MAX(route_order), 0) FROM article_payloads").fetchone()[0]
    now = "2026-07-16T00:00:00+00:00"
    for index, article in enumerate(SYNTHETIC_ARTICLES, start=1):
        slug = str(article["slug"])
        dst.execute(
            """INSERT OR REPLACE INTO articles (
                 slug, display_head, lemma, entry_type, pos, gloss,
                 review_state, visibility, cefr, heritage_classification,
                 created_at, updated_at
               ) VALUES (?, ?, ?, ?, ?, ?, 'approved', 'public', NULL, NULL, ?, ?)""",
            (
                slug,
                article["display_head"],
                article["lemma"],
                article["entry_type"],
                article["pos"],
                article["gloss"],
                now,
                now,
            ),
        )
        dst.execute(
            """INSERT OR REPLACE INTO article_payloads (
                 slug, route_order, payload_json, is_public_route
               ) VALUES (?, ?, ?, 1)""",
            (slug, int(max_order) + index, _payload_for_synthetic(article)),
        )


def _assert_type_coverage(dst: sqlite3.Connection) -> None:
    present: set[str] = set()
    for (entry_type,) in dst.execute(
        "SELECT entry_type FROM articles WHERE review_state='approved' AND visibility='public'"
    ):
        present.add(entry_type)
    for (_slug,) in dst.execute(
        """SELECT ap.slug FROM article_payloads ap
           LEFT JOIN articles a ON a.slug = ap.slug
           WHERE ap.is_public_route = 1 AND a.slug IS NULL"""
    ):
        present.add("form_route")
        break
    missing = REQUIRED_TYPE_SET - present
    if missing:
        raise SystemExit(f"fixture type-set incomplete; missing={sorted(missing)} present={sorted(present)}")
    extra_required_ok = present >= REQUIRED_TYPE_SET
    if not extra_required_ok:
        raise SystemExit(f"fixture type-set coverage failed: {sorted(present)}")
    print(
        "fixture type-set coverage:",
        " ".join(sorted(REQUIRED_TYPE_SET)),
        f"(present={sorted(present)})",
    )
    sentinel = dst.execute(
        "SELECT 1 FROM article_payloads WHERE slug=?", (MISSING_SENTINEL,)
    ).fetchone()
    if sentinel:
        raise SystemExit(f"missing sentinel {MISSING_SENTINEL!r} must not be a public route")
    print(f"missing sentinel absent: {MISSING_SENTINEL}")


def build() -> Path:
    if SRC is None or not SRC.is_file():
        raise SystemExit(
            "missing source DB; set ATLAS_SRC_DB or place data/atlas.db under the repo root"
        )

    if DST.exists():
        DST.unlink()

    src = sqlite3.connect(f"file:{SRC}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(DST)
    dst.executescript(atlas_db.SCHEMA)

    articles = tuple(sorted(WANTED_ARTICLES))
    payloads = tuple(sorted(WANTED_ARTICLES | WANTED_FORM_ROUTES))

    print("articles", _copy_rows(src, dst, "articles", f"slug IN ({','.join('?' * len(articles))})", articles))
    print(
        "payloads",
        _copy_rows(src, dst, "article_payloads", f"slug IN ({','.join('?' * len(payloads))})", payloads),
    )
    print("aliases", _copy_rows(src, dst, "aliases", f"target_slug IN ({','.join('?' * len(articles))})", articles))
    print(
        "enrichment",
        _copy_rows(src, dst, "enrichment", f"slug IN ({','.join('?' * len(articles))})", articles),
    )
    print(
        "provenance",
        _copy_rows(src, dst, "article_provenance", f"slug IN ({','.join('?' * len(articles))})", articles),
    )
    print(
        "related",
        _copy_rows(
            src,
            dst,
            "related_entries",
            f"slug IN ({','.join('?' * len(articles))}) OR related_slug IN ({','.join('?' * len(articles))})",
            articles + articles,
        ),
    )
    print("metadata", _copy_rows(src, dst, "manifest_metadata", "1=1"))

    for slug in articles:
        row = dst.execute("SELECT payload_json FROM article_payloads WHERE slug=?", (slug,)).fetchone()
        if not row:
            continue
        payload = json.loads(row[0])
        enrichment = payload.get("enrichment")
        if isinstance(enrichment, dict) and "morphology" in enrichment:
            morph, changed = _trim_morph(enrichment.get("morphology"))
            if changed:
                enrichment["morphology"] = morph
                payload["enrichment"] = enrichment
                dst.execute(
                    "UPDATE article_payloads SET payload_json=? WHERE slug=?",
                    (json.dumps(payload, ensure_ascii=False), slug),
                )
        for erow in dst.execute(
            "SELECT rowid, payload_json FROM enrichment WHERE slug=? AND section='morphology'",
            (slug,),
        ).fetchall():
            morph, changed = _trim_morph(json.loads(erow[1]))
            if changed:
                dst.execute(
                    "UPDATE enrichment SET payload_json=? WHERE rowid=?",
                    (json.dumps(morph, ensure_ascii=False), erow[0]),
                )

    _insert_synthetic(dst)

    dst.execute("DELETE FROM articles_fts")
    for row in dst.execute("SELECT slug, display_head, lemma, gloss FROM articles"):
        alias_text = " ".join(
            alias
            for (alias,) in dst.execute(
                "SELECT alias FROM aliases WHERE target_slug=? AND visibility='public'",
                (row[0],),
            )
        )
        dst.execute(
            "INSERT INTO articles_fts(slug, display_head, lemma, gloss, aliases) VALUES (?,?,?,?,?)",
            (row[0], row[1], row[2], row[3], alias_text),
        )

    dst.commit()
    _assert_type_coverage(dst)
    dst.execute("VACUUM")
    dst.close()
    src.close()

    conn = open_readonly_db(DST)
    gates = _site_build_entry_model_gates(conn)
    records = load_entry_records(conn, practice_levels_by_slug={})
    print("gates", gates)
    for record in records:
        links = record["renderContext"]["componentLinks"]
        enrichment = record["entry"].get("enrichment")
        morph = enrichment.get("morphology") if isinstance(enrichment, dict) else None
        marked = isinstance(morph, dict) and bool(morph.get("marked_forms"))
        heritage = record["entry"].get("heritage_status")
        classification = heritage.get("classification") if isinstance(heritage, dict) else None
        print(
            f"  {record['slug']}: kind={record['kind']} "
            f"type={record['entry'].get('entry_type')} "
            f"aliases={len(record['aliases'])} links={links} "
            f"marked={marked} heritage={classification}"
        )
    conn.close()

    with tempfile.TemporaryDirectory() as tmp:
        report = export_runtime_shards(
            db_path=DST,
            out_dir=Path(tmp),
            include_decks=False,
            deck_dir=None,
            verify=True,
        )
        print("export", report["dataVersion"], report["counts"])

    print("wrote", DST, "bytes", DST.stat().st_size)
    return DST


if __name__ == "__main__":
    build()
