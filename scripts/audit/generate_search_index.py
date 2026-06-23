"""Generate the compact Word Atlas client search index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.audit.generate_daily_pool import kind_for_source
from scripts.audit.lexeme_filter import is_lexeme_entry
from scripts.etymology.transliterate import transliterate

DEFAULT_MANIFEST = Path("site/src/data/lexicon-manifest.json")
DEFAULT_OUT = Path("site/src/data/lexicon-search-index.json")


def _search_row(entry: dict[str, Any]) -> dict[str, Any] | None:
    # Grammar metaterms (pos == "grammar term") are not lemmas — keep them out of search.
    # is_lexeme_entry already guarantees a non-empty lemma + url_slug.
    if not is_lexeme_entry(entry):
        return None
    lemma = entry.get("lemma")
    slug = entry.get("url_slug")
    gloss = entry.get("gloss")
    return {
        "l": lemma,
        "s": slug,
        "g": gloss if isinstance(gloss, str) else None,
        "r": transliterate(lemma),
        "k": kind_for_source(entry.get("primary_source")),
    }


def build_index(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return lemma-sorted compact search rows from manifest entries."""
    rows = [row for entry in entries if (row := _search_row(entry)) is not None]
    return sorted(rows, key=lambda row: row["l"])


def write_index(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")

    write_index(build_index(entries), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
