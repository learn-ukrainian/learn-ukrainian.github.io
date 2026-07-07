"""Rewrite copyrighted fixture evidence rows to pointer-only provenance.

The rights resolver intentionally fails closed for quoted text from sources
without a public-domain or compatible-CC license. This helper performs the
mechanical fixture-side conversion required by the F3 rights freeze: it keeps
the source_file/chunk_id anchor, removes verbatim guillemet-quoted source text,
and marks the evidence row as an explicit POINTER for the resolver.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from scripts.audit.resolve_fixture_rights import (
    CHUNK_ID_RE,
    DEFAULT_FIXTURE_DIR,
    DEFAULT_LICENSE_MAP,
    DEFAULT_SOURCES_DB,
    DEFAULT_VESUM_DB,
    resolve_rows,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

COPYRIGHTED_SOURCE_FILES = frozenset(
    {
        "4-klas-ukrayinska-mova-varzatska-2021-1",
        "5-klas-istoriya-schupak-2022",
        "9-klas-istorija-ukrajini-gisem-2017",
        "imtgsh",
        "istoria_movy",
        "komik_istoryk",
        "ulp_youtube",
        "wave4-chyzhevsky-istoriia-lit",
        "wave4-ukrainska-mova-encyclopedia",
        "wave7-dzyuba-pavlenko-litopys-kultury",
        "wave7-entsyklopediia-ukrainoznavstva",
        "wave7-holobutsky-zaporizhzhia",
        "wave7-istkult-t1-kyivska-rus",
        "wave7-istkult-t2-xiii-xvii",
        "wave7-krypyakevych-istkult",
        "wave7-ohiyenko-tserka",
        "wave7-popovych-narys-kultury",
        "wave7-shcherbak-kozatstvo",
        "wave8-fdm-biobibliohrafichnyi",
        "wave8-ukr-lit-entsyklopediia",
        "wave9-rusanivsky-ist-lit-movy",
    }
)

SOURCE_REF_RE = re.compile(
    r"\b(?P<source>[A-Za-z0-9][A-Za-z0-9_-]*)\s+"
    r"(?P<chunk>(?:[a-f0-9]{8}_c\d{4}|[\w-]+_s\d{4}|ext-[\w-]+-\d+))\b"
)


def remove_guillemet_spans(text: str) -> str:
    output: list[str] = []
    depth = 0
    for char in text:
        if char == "«":
            depth += 1
            continue
        if char == "»" and depth:
            depth -= 1
            continue
        if depth == 0:
            output.append(char)
    return "".join(output)


def compact_text(text: str) -> str:
    text = text.replace("«", "'").replace("»", "'")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"(:|—)\s*([.;])", r"\2", text)
    return text.strip(" ;.")


def source_ref_from_text(text: str) -> tuple[str, str] | None:
    for match in SOURCE_REF_RE.finditer(text):
        source = match.group("source")
        if source in COPYRIGHTED_SOURCE_FILES:
            return source, match.group("chunk")
    return None


def row_source_ref(row: dict[str, Any]) -> tuple[str, str] | None:
    source_file = row.get("source_file")
    chunk_id = row.get("chunk_id")
    quote_or_ref = str(row["quote_or_ref"])
    method = str(row.get("evidence", {}).get("match_method", ""))
    if (
        source_file in COPYRIGHTED_SOURCE_FILES
        and chunk_id
        and (str(chunk_id) in quote_or_ref or method.startswith(("chunk-id:", "substring-scan:")))
    ):
        return str(source_file), str(chunk_id)
    return source_ref_from_text(quote_or_ref)


def row_claim_and_field(row_claim_id: str) -> tuple[str, str] | None:
    if row_claim_id.endswith("_verified"):
        return row_claim_id.removesuffix("_verified"), "verified_by"
    if row_claim_id.endswith("_distractor"):
        return row_claim_id.removesuffix("_distractor"), "distractor_evidence"
    return None


def residual_note(original: str, source_file: str, chunk_id: str) -> str:
    note = remove_guillemet_spans(original)
    note = note.replace(source_file, "").replace(chunk_id, "")
    note = note.replace("the REAL passage", "source anchor")
    note = note.replace("quotes Густинський", "anchors the Hустинський attribution")
    note = compact_text(note)
    note = re.sub(r"^(?:—\s*)?source anchor\.?\s*", "", note)
    note = note.strip(" :;.")
    if len(note) > 420:
        note = note[:417].rstrip() + "..."
    return note


def pointer_text(original: str, claim: dict[str, Any], field: str, source_file: str, chunk_id: str) -> str:
    claim_id = str(claim["claim_id"])
    claim_text = compact_text(str(claim.get("claim", "")))
    if field == "distractor_evidence":
        relation = "anchors the refutation of"
    elif claim.get("is_true") is False:
        relation = "anchors the verification/refutation note for"
    else:
        relation = "supports"

    parts = [
        f"POINTER: {source_file} {chunk_id} {relation} claim {claim_id}: {claim_text}.",
    ]
    note = residual_note(original, source_file, chunk_id)
    if note:
        parts.append(f"Paraphrase note: {note}.")
    parts.append("No verbatim source quote redistributed.")
    return " ".join(parts)


def rewrite_fixture_file(path: Path, rewrites: dict[tuple[str, str], dict[str, Any]], check: bool) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for claim in data.get("claims", []):
        claim_id = str(claim.get("claim_id", ""))
        for field in ("verified_by", "distractor_evidence"):
            rewrite = rewrites.get((claim_id, field))
            if not rewrite:
                continue
            original = claim.get(field)
            if original != rewrite["original"]:
                raise ValueError(f"{path}:{claim_id}.{field} changed before rewrite could apply")
            claim[field] = pointer_text(original, claim, field, rewrite["source_file"], rewrite["chunk_id"])
            changed += 1
    if changed and not check:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def build_rewrites(args: argparse.Namespace) -> dict[str, dict[tuple[str, str], dict[str, Any]]]:
    rows = resolve_rows(
        args.fixtures,
        args.sources_db,
        args.vesum_db,
        args.license_map,
        replace_list=Path("__missing_fixture_rights_replace_list__.md"),
    )
    rewrites: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    for row in rows:
        if row["classification"] != "QUOTED_TEXT":
            continue
        if str(row.get("quote_or_ref", "")).lstrip().upper().startswith("POINTER:"):
            continue
        source_ref = row_source_ref(row)
        if not source_ref:
            continue
        parsed = row_claim_and_field(row["claim_id"])
        if not parsed:
            continue
        claim_id, field = parsed
        source_file, chunk_id = source_ref
        if not CHUNK_ID_RE.fullmatch(chunk_id):
            raise ValueError(f"unexpected chunk id for {row['fixture']} {row['claim_id']}: {chunk_id}")
        rewrites.setdefault(row["fixture"], {})[(claim_id, field)] = {
            "source_file": source_file,
            "chunk_id": chunk_id,
            "original": row["quote_or_ref"],
        }
    return rewrites


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--license-map", type=Path, default=DEFAULT_LICENSE_MAP)
    parser.add_argument("--check", action="store_true", help="Print planned rewrites without writing fixtures.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rewrites = build_rewrites(args)
    total = 0
    for fixture, fixture_rewrites in sorted(rewrites.items()):
        path = args.fixtures / f"{fixture}.json"
        changed = rewrite_fixture_file(path, fixture_rewrites, args.check)
        total += changed
        if changed:
            print(f"{'would rewrite' if args.check else 'rewrote'} {path}: {changed}")
    print(f"total_rewrites={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
