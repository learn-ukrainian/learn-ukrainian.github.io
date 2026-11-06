"""Read checked ULIF entry *and section* evidence for #9151 reconciliation.

The entry header is sometimes blank even when a checked homonym has a full
paradigm and synonym article. A blank header alone is not an empty payload.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.readonly_sqlite import SQLiteConnection
from scripts.lib.readonly_sqlite import open_readonly as _open_readonly


def _key(value: str) -> str:
    value = value.replace("ʼ", "'").replace("’", "'").replace("`", "'")
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in decomposed if ch != "\u0301").casefold().strip()


def _paradigm_headword(payload: dict[str, Any], lemma: str) -> str:
    for row in payload.get("rows", []):
        if not isinstance(row, list) or len(row) < 2:
            continue
        if _key(str(row[0])) not in {_key("називний"), _key("інфінітив")}:
            continue
        for form in str(row[1]).split(","):
            candidate = form.strip()
            if _key(candidate) == _key(lemma):
                return candidate
    return ""


def read_checked_ulif(conn: SQLiteConnection, lemma: str) -> list[dict[str, Any]]:
    """Return only checked homonyms, with matching lexical evidence per section."""
    rows = conn.execute(
        """SELECT id, homonym_index, canonical_headword, grammatical_label, status
           FROM ulif_dictua_entries
           WHERE normalized_query=? AND homonym_checked=1
           ORDER BY homonym_index,id""",
        (lemma.casefold(),),
    ).fetchall()
    result = []
    for entry_id, homonym, header, grammar, status in rows:
        kinds: list[str] = []
        paradigm_headword = ""
        synonym_terms: list[str] = []
        for kind, raw in conn.execute(
            """SELECT kind,payload_json FROM ulif_dictua_sections
               WHERE entry_id=? ORDER BY source_order,id""",
            (entry_id,),
        ):
            payload = json.loads(raw)
            kinds.append(kind)
            if kind == "paradigm" and not paradigm_headword:
                paradigm_headword = _paradigm_headword(payload, lemma)
            elif kind == "synonyms":
                synonym_terms.extend(
                    str(term["text"])
                    for term in payload.get("terms", [])
                    if isinstance(term, dict) and _key(str(term.get("text", ""))) == _key(lemma)
                )
        result.append(
            {
                "id": entry_id,
                "homonym_index": homonym,
                "headword": header or paradigm_headword,
                "grammatical_label": grammar,
                "status": status,
                "entry_headword": header,
                "paradigm_headword": paradigm_headword,
                "section_kinds": kinds,
                "matching_synonym_terms": sorted(set(synonym_terms)),
                "lexical_attestation": status == "ok"
                and bool(_key(header) == _key(lemma) or paradigm_headword or synonym_terms),
            }
        )
    return result


def refresh_registry(registry: Path, sources_db: Path) -> tuple[dict[str, Any], list[str]]:
    payload = json.loads(registry.read_text(encoding="utf-8"))
    changed = []
    with _open_readonly(sources_db) as conn:
        for row in payload["rows"]:
            before = (
                row.get("ulif_checked"),
                row.get("ulif_lexical_attestation"),
                row.get("ulif_unattested_checked_ids", row.get("ulif_empty_checked_ids")),
            )
            checked = read_checked_ulif(conn, row["lemma"])
            row["ulif_checked"] = checked
            row["ulif_lexical_attestation"] = any(item["lexical_attestation"] for item in checked)
            row.pop("ulif_empty_checked_ids", None)
            row["ulif_unattested_checked_ids"] = [item["id"] for item in checked if not item["lexical_attestation"]]
            after = (row["ulif_checked"], row["ulif_lexical_attestation"], row["ulif_unattested_checked_ids"])
            if before != after:
                changed.append(row["lemma"])
    payload["evidence_methods"]["ulif"] = (
        "data/sources.db mode=ro; checked ulif_dictua_entries joined by id to "
        "ulif_dictua_sections; paradigm rows and matching synonym terms resolve blank entry headers"
    )
    return payload, changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check ULIF evidence for the #9151 reconciliation registry. "
            "Use for evidence refresh, not membership admission."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example: .venv/bin/python "
            "scripts/lexicon/curated_membership_evidence.py "
            "--registry registry/lexicon/curated-membership-reconciliation-9151.json "
            "--sources-db data/sources.db\n"
            "Outputs: JSON summary on stdout; --write updates only the registry.\n"
            "Exit codes: 0 on success; nonzero on invalid inputs or read errors.\n"
            "Related: #9151 reviewed reconciliation."
        ),
    )
    parser.add_argument("--registry", type=Path, required=True, help="Reviewed reconciliation JSON path")
    parser.add_argument("--sources-db", type=Path, required=True, help="Read-only ULIF sources.db path")
    parser.add_argument(
        "--write", action="store_true", help="Write refreshed evidence to --registry (default: report only)"
    )
    args = parser.parse_args()
    payload, changed = refresh_registry(args.registry, args.sources_db)
    if args.write:
        args.registry.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(payload["rows"]), "changed": changed}, ensure_ascii=False))


if __name__ == "__main__":
    main()
