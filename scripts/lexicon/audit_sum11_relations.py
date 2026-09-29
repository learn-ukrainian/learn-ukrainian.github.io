#!/usr/bin/env python3
"""Reproduce the read-only #8990 stored СУМ-11 relation and source audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import subprocess
from collections import defaultdict
from pathlib import Path

from scripts.lexicon.enrich_manifest import _antonyms_ulif, _section_item_key, _synonyms_ulif
from scripts.verification import vesum

ROOT = Path(__file__).resolve().parents[2]


def primary_data_dir(repo_root: Path) -> Path:
    common_dir = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()
    return Path(common_dir).resolve().parent / "data"


PRIMARY_DATA = primary_data_dir(ROOT)
SEARCH_RUN = "ULIF DictUA exact headword relation; VESUM lemma gate"
COUNT_START = "<!-- audit-counts:start -->"
COUNT_END = "<!-- audit-counts:end -->"


def _ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only=ON")
    return conn


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _item_text(item: object) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for field in ("word", "target", "lemma", "phrase", "text", "definition"):
            if isinstance(item.get(field), str) and item[field].strip():
                return item[field]
    return json.dumps(item, ensure_ascii=False, sort_keys=True)


def _write_tsv(path: Path, rows: list[tuple[str, str, str, str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(("slug", "section", "item", "search_run", "result"))
        writer.writerows(sorted(rows))


def audit(atlas_db: Path, sources_db: Path, vesum_db: Path, out_dir: Path, audit_doc: Path) -> dict:
    # The production extractor uses the shared VESUM resolver. Check its resolved
    # database rather than silently consulting a different snapshot.
    if vesum._resolve_vesum_db_path().resolve() != vesum_db.resolve():
        raise ValueError("production VESUM resolver does not point to --vesum-db")
    with vesum.get_vesum_connection(vesum_db) as vesum_conn:
        vesum_conn.execute("PRAGMA query_only=ON")
    atlas, sources = _ro(atlas_db), _ro(sources_db)
    totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    held: list[tuple[str, str, str, str, str]] = []
    confirmed: list[tuple[str, str, str, str, str]] = []
    held_sources: list[tuple[str, str, str]] = []
    try:
        rows = atlas.execute(
            "SELECT p.slug, p.payload_json, a.pos FROM article_payloads p "
            "LEFT JOIN articles a USING(slug) "
            "ORDER BY p.slug"
        )
        for slug, raw, pos in rows:
            entry = json.loads(raw)
            sections = entry.get("sections") or {}
            for name in ("synonyms", "antonyms", "homonyms"):
                section = sections.get(name)
                if not isinstance(section, dict) or "СУМ-11" not in json.dumps(section, ensure_ascii=False):
                    continue
                totals[name]["rows"] += 1
                if name == "synonyms":
                    replacement = _synonyms_ulif(sources, entry.get("lemma") or slug)
                elif name == "antonyms":
                    replacement = _antonyms_ulif(sources, entry.get("lemma") or slug, entry_pos=pos)
                else:
                    replacement = None  # No independent homonym replacement pass in this audit.
                replacement_keys = {
                    key for item in (replacement or {}).get("items", [])
                    if (key := _section_item_key(item))
                }
                unresolved = False
                for item in section.get("items") or []:
                    key = _section_item_key(item)
                    result = "confirmed" if name != "homonyms" and key and key in replacement_keys else "unresolved"
                    search = SEARCH_RUN if name != "homonyms" else "No independent homonym replacement gate"
                    record = (slug, name, _item_text(item), search, result)
                    if result == "confirmed":
                        confirmed.append(record)
                        totals[name]["confirmed_items"] += 1
                    else:
                        held.append(record)
                        totals[name]["held_items"] += 1
                        unresolved = True
                totals[name]["held_rows" if unresolved else "fully_confirmed_rows"] += 1
            source_list = (entry.get("enrichment") or {}).get("sources") or []
            if isinstance(source_list, list):
                matches = [source for source in source_list if isinstance(source, str) and "СУМ-11" in source]
                if matches:
                    totals["top-level sources"]["rows"] += 1
                    totals["top-level sources"]["held_rows"] += 1
                    totals["top-level sources"]["held_items"] += len(matches)
                    held_sources.extend((slug, source, "unverified") for source in matches)
    finally:
        atlas.close()
        sources.close()

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_tsv(out_dir / "sum11-held-relations.tsv", held)
    _write_tsv(out_dir / "sum11-confirmed-relations.tsv", confirmed)
    with (out_dir / "sum11-held-sources.tsv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(("slug", "source", "result"))
        writer.writerows(sorted(held_sources))
    columns = ("rows", "fully_confirmed_rows", "held_rows", "confirmed_items", "held_items")
    lines = ["| Section | Cited rows | Fully confirmed rows | Held rows | Confirmed items | Held items |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name in ("synonyms", "antonyms", "homonyms"):
        numbers = [totals[name][key] for key in columns]
        lines.append(f"| {name} | " + " | ".join(f"{value:,}" for value in numbers) + " |")
    relation_totals = [sum(totals[name][key] for name in ("synonyms", "antonyms", "homonyms"))
                       for key in columns]
    lines.append("| **Relation total** | " + " | ".join(f"**{value:,}**" for value in relation_totals) + " |")
    numbers = [totals["top-level sources"][key] for key in columns]
    lines.append("| top-level sources | " + " | ".join(f"{value:,}" for value in numbers) + " |")
    fingerprints = {name: _sha256(path) for name, path in
                    (("atlas.db", atlas_db), ("sources.db", sources_db), ("vesum.db", vesum_db))}
    block = "\n".join([COUNT_START, "\n".join(lines), "", "Source SHA-256: " +
                        ", ".join(f"`{name}` `{value}`" for name, value in fingerprints.items()), COUNT_END])
    doc = audit_doc.read_text(encoding="utf-8")
    if COUNT_START not in doc or COUNT_END not in doc:
        raise ValueError("audit count markers missing")
    start = doc.index(COUNT_START)
    end = doc.index(COUNT_END) + len(COUNT_END)
    audit_doc.write_text(doc[:start] + block + doc[end:], encoding="utf-8")
    return {name: dict(totals[name]) for name in ("synonyms", "antonyms", "homonyms", "top-level sources")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas-db", type=Path, default=PRIMARY_DATA / "atlas.db")
    parser.add_argument("--sources-db", type=Path, default=PRIMARY_DATA / "sources.db")
    parser.add_argument("--vesum-db", type=Path, default=PRIMARY_DATA / "vesum.db")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "docs" / "lexicon")
    parser.add_argument("--audit-doc", type=Path, default=ROOT / "docs" / "lexicon" / "sum11-reference-audit.md")
    args = parser.parse_args()
    print(json.dumps(audit(args.atlas_db, args.sources_db, args.vesum_db, args.out_dir, args.audit_doc), sort_keys=True))


if __name__ == "__main__":
    main()
