#!/usr/bin/env python3
"""Produce a deterministic, fail-closed audit of the frozen literary candidate.

This tool is deliberately an auditor, not an exporter: it never writes the input
JSONL or SQLite database and opens SQLite through ``mode=ro``.  Its output is a
receipt for a particular pair of input hashes, not a claim about literary quality.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET = REPO_ROOT / "data/datasets/hramatka_literary_poltava_v1/hramatka_literary_poltava_v1.jsonl"
EVIDENCE_DIR = REPO_ROOT / "data/datasets/hramatka_literary_poltava_v1/evidence"
REPORT_PATH = REPO_ROOT / "docs/research/hramatka_literary_poltava_candidate_audit.md"
REQUIRED_FIELDS = ("id", "author", "work", "year", "language_period", "dialect_standard", "text")
NEAR_THRESHOLD = 0.90
RUSSIAN_ONLY = set("ыэъё")
STALE_CLAIMS = [
    {
        "path": "scripts/dataset/export_literary_poltava_dataset.py",
        "lines": "1-5, 40, 52-82",
        "claim": "The random export is pristine, authentic Poltava-Kyiv data ready to fine-tune open models.",
        "support_status": "unsupported_and_unsafe_to_regenerate",
        "action": "Do not run against the committed candidate; replace only after a rights-cleared rebuild.",
    },
    {
        "path": "docs/architecture/ADR_013_LITERARY_POLTAVA_ALIGNMENT.md",
        "lines": "19, 23-47",
        "claim": "The corpus is pristine, decolonized, hand-verified, release-ready, and approved for fine-tuning.",
        "support_status": "contradicted_by_fail_closed_audit",
        "action": "Supersede in a separately scoped documentation correction; do not use as current authority.",
    },
    {
        "path": "docs/guides/HUGGINGFACE_GEMMA_FINETUNING_GUIDE.md",
        "lines": "3, 8-25",
        "claim": "The candidate is a clean pre-packaged dataset that can be uploaded publicly.",
        "support_status": "contradicted_by_unknown_rights_and_provenance",
        "action": "Do not upload or train; retire or gate the guide in a separate documentation change.",
    },
    {
        "path": "docs/research/DATASET_UNIQUENESS_AND_UNLP_GAP_ANALYSIS.md",
        "lines": "23-59",
        "claim": "The project is releasing a unique decolonized dataset with zero machine translation or calques.",
        "support_status": "unestablished",
        "action": "Retain only as historical research after adding a clear supersession notice.",
    },
    {
        "path": "docs/research/UNLP_DATASET_SURVEY_AND_EVALUATION.md",
        "lines": "35-71",
        "claim": "The candidate should be used for Poltava alignment and decolonized fine-tuning.",
        "support_status": "contradicted_by_rebuild_required_verdict",
        "action": "Do not use as a training recommendation; supersede separately.",
    },
    {
        "path": "docs/strategy/STRATEGY_MAKING_GOOGLE_NOTICE_OUR_BENCHMARKS.md",
        "lines": "3-8, 21-55",
        "claim": "Purity, publication readiness, and visibility probabilities support public release.",
        "support_status": "already_disclaimed_in_document_header",
        "action": "No audit-PR edit; preserve the existing historical-context warning.",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def normalized_text(text: str) -> str:
    """NFC, case-fold, whitespace/punctuation-normalized comparison form."""
    text = unicodedata.normalize("NFC", text).casefold()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def token_shingles(text: str, width: int = 3) -> set[str]:
    tokens = normalized_text(text).split()
    if not tokens:
        return set()
    if len(tokens) < width:
        return {" ".join(tokens)}
    return {" ".join(tokens[index : index + width]) for index in range(len(tokens) - width + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def connected_clusters(edges: list[tuple[int, int, float]]) -> list[dict[str, Any]]:
    parent: dict[int, int] = {}

    def find(item: int) -> int:
        parent.setdefault(item, item)
        if parent[item] != item:
            parent[item] = find(parent[item])
        return parent[item]

    def join(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for left, right, _ in edges:
        join(left, right)
    groups: dict[int, list[int]] = collections.defaultdict(list)
    for item in parent:
        groups[find(item)].append(item)
    edge_by_group: dict[int, list[tuple[int, int, float]]] = collections.defaultdict(list)
    for edge in edges:
        edge_by_group[find(edge[0])].append(edge)
    return [
        {"members": sorted(members), "edges": sorted(edge_by_group[root])}
        for root, members in sorted(groups.items(), key=lambda pair: min(pair[1]))
    ]


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} is not a JSON object")
            value["_line"] = line_number
            records.append(value)
    return records


def database_rows(path: Path, ids: list[int]) -> dict[int, dict[str, Any]]:
    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(literary_texts)")]
        required = {"id", "chunk_id", "source_file", "work_id", "genre", "source_url"}
        missing = required - set(columns)
        if missing:
            raise ValueError(f"literary_texts lacks required columns: {sorted(missing)}")
        rows: dict[int, dict[str, Any]] = {}
        for offset in range(0, len(ids), 900):
            placeholders = ",".join("?" for _ in ids[offset : offset + 900])
            query = (
                "SELECT id, chunk_id, source_file, work_id, genre, source_url, author, work, year FROM literary_texts WHERE id IN ("
                + placeholders
                + ")"
            )
            for row in connection.execute(query, ids[offset : offset + 900]):
                rows[row[0]] = dict(
                    zip(
                        ("id", "chunk_id", "source_file", "work_id", "genre", "source_url", "author", "work", "year"),
                        row,
                        strict=True,
                    )
                )
    return rows


def evaluation_texts(paths: list[Path]) -> list[str]:
    texts: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        if path.suffix == ".jsonl":
            values = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        else:
            values = [json.loads(path.read_text(encoding="utf-8"))]
        stack = list(values)
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                layouts = value.get("record_layouts")
                compact_items = value.get("items")
                if isinstance(layouts, dict) and isinstance(compact_items, list):
                    item_fields = layouts.get("item")
                    reference_fields = layouts.get("reference")
                    if not isinstance(item_fields, list) or not isinstance(reference_fields, list):
                        raise ValueError(f"compact evaluation inventory lacks record layouts: {path}")
                    for compact_item in compact_items:
                        item = dict(zip(item_fields, compact_item, strict=True))
                        source = item.get("source")
                        if isinstance(source, str):
                            texts.append(source)
                        for compact_reference in item.get("references", []):
                            reference = dict(zip(reference_fields, compact_reference, strict=True))
                            target = reference.get("target")
                            if isinstance(target, str):
                                texts.append(target)
                    continue
                for key, child in value.items():
                    if key in {"source", "target", "text", "reference"} and isinstance(child, str):
                        texts.append(child)
                    else:
                        stack.append(child)
            elif isinstance(value, list):
                stack.extend(value)
    return texts


def anomaly_flags(record: dict[str, Any], row: dict[str, Any] | None) -> list[str]:
    text = record.get("text") if isinstance(record.get("text"), str) else ""
    flags: list[str] = []
    letters = [character for character in text if character.isalpha()]
    if letters and sum("А" <= c.upper() <= "Я" or c.upper() == "І" for c in letters) / len(letters) < 0.50:
        flags.append("low_cyrillic_ratio_signal")
    if RUSSIAN_ONLY & set(text.casefold()):
        flags.append("russian_only_letter_signal")
    if "�" in text or any(unicodedata.category(character) == "Cs" for character in text):
        flags.append("encoding_damage_signal")
    if re.search(r"(?:\.{5,}|_{5,}|[.·]\s*[.·]\s*[.·])", text):
        flags.append("ocr_or_layout_noise_signal")
    words = normalized_text(text).split()
    if len(words) > 12 and max(collections.Counter(words).values(), default=0) / len(words) > 0.30:
        flags.append("repetition_signal")
    if row and record.get("year") != row.get("year"):
        flags.append("year_lineage_mismatch_signal")
    if row and record.get("author") not in {row.get("author"), None, "Unknown"}:
        flags.append("author_lineage_mismatch_signal")
    if row and record.get("work") not in {row.get("work"), None, "Unknown"}:
        flags.append("work_lineage_mismatch_signal")
    return flags


def audit(
    dataset: Path, source_db: Path, output_dir: Path, report_path: Path, evaluation_paths: list[Path]
) -> dict[str, Any]:
    input_hashes_before = {"dataset_sha256": sha256_file(dataset), "sources_db_sha256": sha256_file(source_db)}
    records = load_records(dataset)
    ids = [int(str(record.get("id", "")).removeprefix("lit-")) for record in records]
    rows = database_rows(source_db, ids)
    normalized = [normalized_text(str(record.get("text", ""))) for record in records]
    exact_groups: dict[str, list[int]] = collections.defaultdict(list)
    for index, value in enumerate(normalized):
        exact_groups[value].append(index)
    exact_edges = [(items[0], item, 1.0) for items in exact_groups.values() if len(items) > 1 for item in items[1:]]
    shingles = [token_shingles(str(record.get("text", ""))) for record in records]
    # Exhaust every pair.  The cardinality pre-filter is necessary for Jaccard
    # >= threshold and cannot discard a qualifying pair.
    near_edges = []
    for left in range(len(records)):
        for right in range(left + 1, len(records)):
            if normalized[left] == normalized[right]:
                continue
            smaller, larger = sorted((len(shingles[left]), len(shingles[right])))
            if not larger or smaller / larger < NEAR_THRESHOLD:
                continue
            score = jaccard(shingles[left], shingles[right])
            if score >= NEAR_THRESHOLD:
                near_edges.append((left, right, round(score, 6)))
    evaluation_inventories = []
    evaluation_inventory_texts: list[str] = []
    for path in evaluation_paths:
        if not path.exists():
            continue
        inventory_texts = evaluation_texts([path])
        evaluation_inventory_texts.extend(inventory_texts)
        evaluation_inventories.append(
            {
                "path": display_path(path),
                "sha256": sha256_file(path),
                "text_count": len(inventory_texts),
                "unique_normalized_text_count": len({normalized_text(text) for text in inventory_texts}),
            }
        )
    eval_normalized = {normalized_text(text) for text in evaluation_inventory_texts}
    eval_shingles = [token_shingles(text) for text in eval_normalized]
    eval_overlap: list[dict[str, Any]] = []
    for index, value in enumerate(normalized):
        if value in eval_normalized:
            eval_overlap.append({"record_index": index, "kind": "exact"})
        elif any(jaccard(shingles[index], eval_set) >= NEAR_THRESHOLD for eval_set in eval_shingles):
            eval_overlap.append({"record_index": index, "kind": "near"})
    required_missing = {field: sum(not record.get(field) for record in records) for field in REQUIRED_FIELDS}
    author_counts = collections.Counter(str(record.get("author") or "<missing>") for record in records)
    work_counts = collections.Counter(str(record.get("work") or "<missing>") for record in records)
    period_counts = collections.Counter(str(record.get("language_period") or "<missing>") for record in records)
    genre_counts = collections.Counter(
        str(rows.get(ids[index], {}).get("genre") or "<missing>") for index in range(len(records))
    )
    source_file_counts = collections.Counter(
        str(rows.get(ids[index], {}).get("source_file") or "<missing>") for index in range(len(records))
    )
    dispositions: list[dict[str, Any]] = []
    overlapping_indexes = {entry["record_index"] for entry in eval_overlap}
    for index, record in enumerate(records):
        row = rows.get(ids[index])
        missing_lineage = []
        if not row:
            missing_lineage.append("literary_texts_row")
        else:
            for field in ("chunk_id", "work_id", "source_file", "source_url"):
                if not row.get(field):
                    missing_lineage.append(field)
        # The database schema has no authoritative acquisition/rights fields.
        missing_rights = [
            "external_source_or_catalog_id",
            "acquisition_source",
            "edition_or_editor",
            "license",
            "copyright_status",
            "redistribution_permission",
            "model_training_permission",
            "translation_origin",
            "region",
            "register",
        ]
        disposition = "excluded_pending_rights_and_provenance"
        if index in overlapping_indexes:
            disposition = "excluded_evaluation_overlap"
        dispositions.append(
            {
                "id": record.get("id"),
                "line": record["_line"],
                "source_db_id": ids[index],
                "lineage": row or None,
                "missing_lineage": missing_lineage,
                "missing_rights_or_metadata": missing_rights,
                "anomaly_signals": anomaly_flags(record, row),
                "evaluation_overlap": index in overlapping_indexes,
                "disposition": disposition,
            }
        )
    clusters = {
        "normalization": "Unicode NFC, case-fold, non-word characters collapsed to spaces, whitespace collapsed",
        "near_duplicate_algorithm": "Exhaustive pairwise 3-token-shingle Jaccard >= 0.90; a necessary shingle-cardinality pre-filter is applied; clusters are connected components",
        "exact_clusters": connected_clusters(exact_edges),
        "near_clusters": connected_clusters(near_edges),
    }
    lineage_projection = [
        {"source_db_id": item_id, "lineage": rows.get(item_id)}
        for item_id in sorted(ids)
    ]
    source_db_contract = {
        "path_contract": "data/sources.db (operator-supplied, gitignored local runtime input)",
        "committed_with_repository": False,
        "acquisition_provenance": "unknown_fail_closed",
        "rerun_requirement": (
            "Supply a read-only SQLite file whose SHA-256 equals the recorded hash; "
            "the committed record dispositions are the frozen lineage snapshot."
        ),
        "sqlite_open_mode": "URI mode=ro",
        "table": "literary_texts",
        "selected_columns": [
            "id",
            "chunk_id",
            "source_file",
            "work_id",
            "genre",
            "source_url",
            "author",
            "work",
            "year",
        ],
        "selected_row_count": len(rows),
        "selected_lineage_projection_sha256": hashlib.sha256(
            canonical_json(lineage_projection).encode("utf-8")
        ).hexdigest(),
        "sources_db_sha256": input_hashes_before["sources_db_sha256"],
    }
    summary = {
        "schema_version": "literary_poltava_candidate_audit.v1",
        "input_hashes": input_hashes_before,
        "record_count": len(records),
        "unique_ids": len(set(record.get("id") for record in records)),
        "jsonl_schema": {
            "required_fields": list(REQUIRED_FIELDS),
            "observed_fields": sorted({key for record in records for key in record if key != "_line"}),
        },
        "required_field_missing": required_missing,
        "source_db_rows_joined": len(rows),
        "source_db_rows_missing": len(records) - len(rows),
        "all_records_have_unknown_rights": True,
        "collection_verdict": "rebuild_required",
        "verdict_reason": "No record has evidence for license, copyright, redistribution, or model-training permission; those unknowns fail closed.",
        "duplicate_counts": {
            "exact_clusters": len(clusters["exact_clusters"]),
            "exact_records": sum(len(c["members"]) for c in clusters["exact_clusters"]),
            "near_clusters": len(clusters["near_clusters"]),
            "near_records": sum(len(c["members"]) for c in clusters["near_clusters"]),
        },
        "evaluation_overlap_counts": dict(collections.Counter(entry["kind"] for entry in eval_overlap)),
        "evaluation_inventories": evaluation_inventories,
        "concentrations": {
            "author_top_20": author_counts.most_common(20),
            "work_top_20": work_counts.most_common(20),
            "language_period": period_counts.most_common(),
            "genre": genre_counts.most_common(),
            "acquisition_channel_proxy_source_file_top_20": source_file_counts.most_common(20),
        },
        "metadata_missing_counts": {
            "external_source_or_catalog_id": len(records),
            "acquisition_source": len(records),
            "edition_or_editor": len(records),
            "license": len(records),
            "copyright_status": len(records),
            "redistribution_permission": len(records),
            "model_training_permission": len(records),
            "translation_origin": len(records),
            "region": len(records),
            "register": len(records),
        },
        "anomaly_signal_counts": collections.Counter(
            flag for disposition in dispositions for flag in disposition["anomaly_signals"]
        ),
        "limitations": [
            "Heuristic anomaly flags are signals, not linguistic or legal adjudications.",
            "No record-level external catalog, license, publisher, estate, or government/legal citation was supplied; this audit makes no external rights assertion.",
            "The labels pure, native, decolonized, and Poltava standard are unestablished by this audit.",
        ],
        "stale_claim_inventory": STALE_CLAIMS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "audit_summary.json", summary)
    write_json(output_dir / "duplicate_clusters.json", clusters)
    write_json(
        output_dir / "evaluation_overlap.json",
        {"inventories": evaluation_inventories, "overlaps": eval_overlap},
    )
    write_json(
        output_dir / "input_contract.json",
        {
            "schema_version": "literary_poltava_candidate_inputs.v1",
            "dataset": {
                "path": display_path(dataset),
                "sha256": input_hashes_before["dataset_sha256"],
                "record_count": len(records),
            },
            "sources_db": source_db_contract,
            "evaluation_inventories": evaluation_inventories,
        },
    )
    with (output_dir / "record_dispositions.jsonl").open("w", encoding="utf-8") as handle:
        for disposition in dispositions:
            handle.write(canonical_json(disposition) + "\n")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")
    input_hashes_after = {"dataset_sha256": sha256_file(dataset), "sources_db_sha256": sha256_file(source_db)}
    if input_hashes_before != input_hashes_after:
        raise RuntimeError("an audit input changed while it was being read")
    return summary


def render_report(summary: dict[str, Any]) -> str:
    concentrations = summary["concentrations"]
    return "\n".join(
        [
            "# Literary Poltava candidate audit",
            "",
            "## Observed facts",
            "",
            f"- Frozen JSONL SHA-256: `{summary['input_hashes']['dataset_sha256']}`.",
            f"- Source database SHA-256: `{summary['input_hashes']['sources_db_sha256']}`.",
            f"- Records: {summary['record_count']}; unique IDs: {summary['unique_ids']}; joined database rows: {summary['source_db_rows_joined']}.",
            f"- Missing database rows: {summary['source_db_rows_missing']}; all records lack recorded rights evidence.",
            f"- Missing rights/provenance fields: {canonical_json(summary['metadata_missing_counts'])}.",
            f"- Anomaly signals (heuristic only): {canonical_json(summary['anomaly_signal_counts'])}.",
            f"- Exact duplicate clusters: {summary['duplicate_counts']['exact_clusters']}; near-duplicate clusters: {summary['duplicate_counts']['near_clusters']}.",
            f"- Evaluation overlaps: {canonical_json(summary['evaluation_overlap_counts'])}.",
            "",
            "## Inferences",
            "",
            f"- **Verdict: {summary['collection_verdict']}** — {summary['verdict_reason']}",
            "- The top author concentrations are recorded in the machine-readable receipt: "
            + canonical_json(concentrations["author_top_20"][:5])
            + ".",
            "",
            "## Unknowns and limits",
            "",
            *[f"- {item}" for item in summary["limitations"]],
            "",
            "## Recommendations",
            "",
            "- Rebuild from sources with per-work external catalog identifiers, acquisition receipts, edition/editor, license, copyright, redistribution, and explicit model-training permissions.",
            "- Exclude every record marked as evaluation overlap from any future training view; have Ukrainian linguistic experts review all anomaly signals and any regional/standard claim.",
            "",
            "## Stale-claim inventory",
            "",
            "| Path | Lines | Claim | Support status | Action |",
            "| --- | --- | --- | --- | --- |",
            *[
                "| {path} | {lines} | {claim} | `{support_status}` | {action} |".format(**claim)
                for claim in summary["stale_claim_inventory"]
            ],
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--sources-db", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=EVIDENCE_DIR)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument(
        "--evaluation",
        type=Path,
        action="append",
        default=[
            REPO_ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json",
            REPO_ROOT / "data/projects/ua_eval_harness/evalset_v1.jsonl",
        ],
    )
    args = parser.parse_args()
    print(canonical_json(audit(args.dataset, args.sources_db, args.output_dir, args.report, args.evaluation)))


if __name__ == "__main__":
    main()
