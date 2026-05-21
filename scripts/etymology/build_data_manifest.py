"""Emit a JSON manifest of ESUM etymology entries for Astro build consumption.

Astro's dynamic route at `starlight/src/pages/etymology/[slug].astro` reads this
manifest in its `getStaticPaths()` callback. The manifest is checked into the
build pipeline at `starlight/src/data/etymology-manifest.json` (gitignored —
regenerated from `data/sources.db` on every build).

Schema (one entry per row):

```
{
  "version": "2026-05-15-v1",
  "generated_at": "ISO-8601 timestamp",
  "stats": { ... high-level counts ... },
  "entries": [
    {
      "id": 12345,
      "lemma": "серце",
      "vol": 5,
      "page": 271,
      "slug": "sertse",                # transliterated, canonical
      "page_slug": "sertse-5-271",     # disambig form (for polysemy)
      "etymology_text": "...",
      "cognate_forms": {"р.": "сéрдце", "п.": "serce", ...},
      "proto_form": "*sьrdьce" | null,
    },
    ...
  ],
  "slug_groups": {
    "sertse": ["sertse-5-271"],
    "maty": ["maty-2-48", "maty-3-412", "maty-3-413"],   # polysemy
    ...
  }
}
```

`slug_groups` is the polysemy index: any slug with >1 entry routes to a
landing page that lists each entry's vol/page link.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

try:
    from scripts.etymology.transliterate import transliterate
except ModuleNotFoundError:  # pragma: no cover - direct-script support
    from transliterate import transliterate

DEFAULT_DB = Path("data/sources.db")
DEFAULT_OUTPUT = Path("starlight/src/data/etymology-manifest.json")
MANIFEST_VERSION = "2026-05-15-v1"


def load_manifest(db_path: Path) -> dict:
    """Load all ESUM entries from sources.db and shape into the build manifest."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cognate_columns = {row["name"] for row in conn.execute("PRAGMA table_info(esum_cognate_forms)")}
        recovered_select = (
            "COALESCE(f.cognate_forms_recovered, '{}') AS cognate_forms_recovered"
            if "cognate_forms_recovered" in cognate_columns
            else "'{}' AS cognate_forms_recovered"
        )
        rows = conn.execute(
            f"""
            SELECT
                e.id,
                e.lemma,
                e.vol,
                e.page,
                e.etymology_text,
                COALESCE(f.cognate_forms, '{{}}') AS cognate_forms,
                {recovered_select},
                f.proto_form
            FROM esum_etymology_meta e
            LEFT JOIN esum_cognate_forms f ON f.entry_id = e.id
            ORDER BY e.lemma COLLATE NOCASE, e.vol, e.page, e.id
            """
        ).fetchall()
    finally:
        conn.close()

    # First pass: compute slug counts to detect collisions for polysemy ordinal.
    slug_counts: Counter[tuple[str, int, int]] = Counter(
        (transliterate(row["lemma"]) or f"entry-{row['id']}", row["vol"], row["page"])
        for row in rows
    )

    # Second pass: assign canonical slug + page_slug per entry.
    seen: Counter[tuple[str, int, int]] = Counter()
    entries: list[dict] = []
    slug_groups: dict[str, list[str]] = defaultdict(list)

    for row in rows:
        slug = transliterate(row["lemma"]) or f"entry-{row['id']}"
        key = (slug, row["vol"], row["page"])
        seen[key] += 1

        if slug_counts[key] > 1:
            page_slug = f"{slug}-{row['vol']}-{row['page']}-{seen[key]}"
        else:
            page_slug = f"{slug}-{row['vol']}-{row['page']}"

        try:
            cognate_forms = json.loads(row["cognate_forms"])
        except (json.JSONDecodeError, TypeError):
            cognate_forms = {}
        if not isinstance(cognate_forms, dict):
            cognate_forms = {}

        try:
            cognate_forms_recovered = json.loads(row["cognate_forms_recovered"])
        except (json.JSONDecodeError, TypeError):
            cognate_forms_recovered = {}
        if not isinstance(cognate_forms_recovered, dict):
            cognate_forms_recovered = {}

        entry = {
            "id": row["id"],
            "lemma": row["lemma"],
            "vol": row["vol"],
            "page": row["page"],
            "slug": slug,
            "page_slug": page_slug,
            "etymology_text": row["etymology_text"],
            "cognate_forms": cognate_forms,
            "proto_form": row["proto_form"],
        }
        if cognate_forms_recovered:
            entry["cognate_forms_recovered"] = cognate_forms_recovered
        entries.append(entry)
        slug_groups[slug].append(page_slug)

    # Stats for the build process + landing page.
    polysemy_count = sum(1 for v in slug_groups.values() if len(v) > 1)
    with_forms = sum(1 for e in entries if e["cognate_forms"])
    with_recovered_forms = sum(1 for e in entries if e.get("cognate_forms_recovered"))

    return {
        "version": MANIFEST_VERSION,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "stats": {
            "total_entries": len(entries),
            "unique_slugs": len(slug_groups),
            "polysemy_slugs": polysemy_count,
            "entries_with_cognate_forms": with_forms,
            "entries_with_cognate_forms_recovered": with_recovered_forms,
        },
        "entries": entries,
        "slug_groups": dict(slug_groups),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    manifest = load_manifest(args.db)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=None), encoding="utf-8")

    size_mb = args.output.stat().st_size / 1024 / 1024
    print(
        json.dumps(
            {
                **manifest["stats"],
                "output_file": str(args.output),
                "output_size_mb": round(size_mb, 2),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
