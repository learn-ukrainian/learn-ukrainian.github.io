"""Audit whether the recovered Ukrainian corpus can serve the Foundry goals.

The audit reads source metadata and aggregate receipts, never emits source text,
and keeps local model learning separate from raw-source redistribution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = (
    ROOT
    / "data/projects/open_model_data/contracts/corpus_training_usability_decision_v1.schema.json"
)
PROFILE_PATH = ROOT / "data/projects/open_model_data/profiles/full_corpus_profile_v1.json"
DETECTOR_PATH = ROOT / "data/projects/open_model_data/detector/language_contact_receipt_v1.json"
URL_MAP_PATH = ROOT / "data/pidruchnyk_urls.yaml"
MOJIBAKE_RE = re.compile(r"[ÂÃÐÑ]")
LITERARY_METADATA_FIELDS = ("work", "author", "year", "genre", "language_period")


class UsabilityAuditError(ValueError):
    """Raised when the audit cannot make a complete, evidence-backed decision."""


def canonical_json(value: Any) -> str:
    """Serialize a deterministic UTF-8 JSON value."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    """Hash one evidence artifact without emitting its contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsabilityAuditError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise UsabilityAuditError(f"expected JSON object: {path}")
    return value


def _jsonl_rows(path: Path) -> Iterator[dict[str, Any]]:
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        raise UsabilityAuditError(f"cannot read JSONL {path}: {exc}") from exc
    with handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise UsabilityAuditError(f"invalid JSONL at {path.name}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise UsabilityAuditError(f"expected object at {path.name}:{line_number}")
            yield row


def _literary_family(path: Path) -> str:
    if path.name.startswith("ukrlib-"):
        return "ukrlib"
    if path.name.startswith("wikisource-"):
        return "ukrainian_wikisource"
    if path.name.startswith("wave"):
        return "litopys_izbornyk"
    if path.name.startswith("грушевський-"):
        return "retained_hrushevsky_volumes"
    return "other"


def audit_literary(directory: Path) -> dict[str, Any]:
    """Count raw literary lineage fields without retaining text."""
    files = sorted(directory.glob("*.jsonl"))
    if not files:
        raise UsabilityAuditError(f"no literary JSONL files found under {directory}")
    rows = rows_with_locator = 0
    metadata = Counter({field: 0 for field in LITERARY_METADATA_FIELDS})
    families = Counter()
    for path in files:
        families[_literary_family(path)] += 1
        for row in _jsonl_rows(path):
            rows += 1
            rows_with_locator += int(bool(str(row.get("source_url") or row.get("source") or "").strip()))
            for field in LITERARY_METADATA_FIELDS:
                metadata[field] += int(row.get(field) not in (None, ""))
    return {
        "files": len(files),
        "file_families": dict(sorted(families.items())),
        "rows": rows,
        "rows_with_source_locator": rows_with_locator,
        "rows_with_metadata": dict(sorted(metadata.items())),
    }


def audit_textbooks(chunks_directory: Path, pdf_directory: Path, url_map_path: Path) -> dict[str, Any]:
    """Measure textbook lineage and extraction hazards without emitting text."""
    chunk_files = sorted(chunks_directory.rglob("*.jsonl"))
    pdf_files = sorted(pdf_directory.rglob("*.pdf"))
    if not chunk_files:
        raise UsabilityAuditError(f"no textbook chunk JSONL files found under {chunks_directory}")
    if not pdf_files:
        raise UsabilityAuditError(f"no textbook PDFs found under {pdf_directory}")
    try:
        url_map = yaml.safe_load(url_map_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise UsabilityAuditError(f"cannot read textbook URL map {url_map_path}: {exc}") from exc
    if not isinstance(url_map, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in url_map.items()
    ):
        raise UsabilityAuditError("textbook URL map must be a string-to-string mapping")

    rows = clean_rows = below_threshold_rows = mojibake_rows = 0
    clean_ratio_total = 0.0
    mojibake_files: set[str] = set()
    chunk_stems: set[str] = set()
    for path in chunk_files:
        chunk_stems.add(path.stem)
        for row in _jsonl_rows(path):
            rows += 1
            quality = row.get("quality")
            if not isinstance(quality, Mapping):
                quality = {}
            clean_rows += int(quality.get("is_clean") is True)
            ratio = quality.get("clean_ratio")
            ratio_value = float(ratio) if isinstance(ratio, (int, float)) else 0.0
            clean_ratio_total += ratio_value
            below_threshold_rows += int(ratio_value < 0.8)
            if MOJIBAKE_RE.search(str(row.get("text") or "")):
                mojibake_rows += 1
                mojibake_files.add(path.name)

    pdf_stems = {path.stem for path in pdf_files}
    url_stems = set(url_map)
    return {
        "below_0_8_clean_ratio_rows": below_threshold_rows,
        "chunk_files": len(chunk_files),
        "clean_rows": clean_rows,
        "exact_chunk_stem_pdf_matches": len(chunk_stems & pdf_stems),
        "exact_chunk_stem_url_matches": len(chunk_stems & url_stems),
        "mean_clean_ratio": round(clean_ratio_total / rows, 6),
        "mojibake_files": len(mojibake_files),
        "mojibake_rows": mojibake_rows,
        "not_clean_rows": rows - clean_rows,
        "page_url_mappings": len(url_map),
        "pdf_files": len(pdf_files),
        "raw_chunk_rows": rows,
    }


def build_decision(
    *,
    literary_dir: Path,
    textbook_chunks_dir: Path,
    textbook_pdfs_dir: Path,
    textbook_url_map: Path,
    profile_receipt: Path,
    detector_receipt: Path,
) -> dict[str, Any]:
    """Build the complete corpus-usability decision receipt."""
    profile = _read_json(profile_receipt)
    detector = _read_json(detector_receipt)
    if profile.get("schema_version") != "corpus_profile_receipt_v1":
        raise UsabilityAuditError("unexpected corpus profile schema version")
    if detector.get("schema_version") != "language_contact_receipt_v1":
        raise UsabilityAuditError("unexpected detector receipt schema version")
    coverage = profile["coverage"]
    detector_coverage = detector["coverage"]
    if coverage.get("complete") is not True or detector_coverage.get("complete") is not True:
        raise UsabilityAuditError("profile and detector coverage must both be complete")
    if (
        coverage["processed_rows"],
        coverage["processed_lexical_words"],
    ) != (
        detector_coverage["processed_rows"],
        detector_coverage["processed_lexical_words"],
    ):
        raise UsabilityAuditError("profile and detector corpus totals disagree")

    literary = audit_literary(literary_dir)
    textbooks = audit_textbooks(textbook_chunks_dir, textbook_pdfs_dir, textbook_url_map)
    source_distribution = profile["distributions"]["source_family"]
    if literary["rows"] != source_distribution["literary"]["rows"]:
        raise UsabilityAuditError("raw literary rows do not reconcile to the corpus profile")
    if textbooks["raw_chunk_rows"] > source_distribution["public_textbooks"]["rows"]:
        raise UsabilityAuditError("raw textbook chunks exceed profiled public-textbook rows")

    return {
        "schema_version": "corpus_training_usability_decision_v1",
        "decision_id": "foundry-corpus-usability-2026-08-02",
        "snapshot_date": "2026-08-02",
        "project_verdict": "continue",
        "corpus": {
            "records": coverage["processed_rows"],
            "lexical_words": coverage["processed_lexical_words"],
            "modern_lexical_words": profile["distributions"]["period"]["modern"]["lexical_words"],
            "middle_ukrainian_lexical_words": profile["distributions"]["period"]["middle_ukrainian"]["lexical_words"],
            "old_east_slavic_lexical_words": profile["distributions"]["period"]["old_east_slavic"]["lexical_words"],
            "vesum_attested_tokens": profile["vesum"]["tokens_attested"],
            "vesum_unknown_tokens": profile["vesum"]["tokens_unknown"],
            "language_contact_candidates": detector["candidate_arithmetic"]["total_candidates"],
        },
        "lineage": {
            "literary": literary,
            "textbooks": textbooks,
            "external_articles": {
                "records": source_distribution["external_articles"]["rows"],
                "lexical_words": source_distribution["external_articles"]["lexical_words"],
                "status": "source_urls_retained_in_database",
            },
            "wikipedia": {
                "records": source_distribution["wikipedia"]["rows"],
                "lexical_words": source_distribution["wikipedia"]["lexical_words"],
                "status": "article_urls_and_capture_timestamps_retained",
            },
        },
        "operator_attestations": {
            "literary_sources": "acquired from identified Ukrainian source families including UKRLIB, Litopys/Izbornyk, and Ukrainian Wikisource",
            "textbooks": "downloaded from a public textbook-download site intended for learners; retained selection and URL maps identify editions",
        },
        "target_use_decisions": {
            "clean_ukrainian_tool": "usable_now",
            "continued_training_of_existing_open_model": "usable_after_required_preprocessing",
            "foundation_model_training_from_scratch": "insufficient_scale",
            "automatic_correction_or_preference_gold": "insufficient_without_evidence_validation",
            "heldout_evaluation": "usable_with_evaluation_firewall",
        },
        "required_preprocessing": [
            "preserve source, work, edition, period, genre, register, and derivation lineage",
            "deduplicate before measuring the exact tokenizer and training mixture",
            "filter or mask OCR and encoding damage from modern-Ukrainian loss",
            "separate modern, historical, heritage, dialectal, quoted-Russian, other-language, and unresolved spans",
            "keep synthetic and translated project content outside the human-authored source view",
            "keep every evaluation item and derivative outside all training views",
        ],
        "capability_decisions": {
            "local_research_and_model_training": "operator_approved_for_project_goal",
            "raw_source_redistribution": "separate_decision_required",
            "public_dataset_release": "separate_decision_required",
            "public_model_or_adapter_release": "separate_decision_required",
        },
        "input_artifacts": {
            "corpus_profile_receipt_sha256": sha256_file(profile_receipt),
            "language_contact_receipt_sha256": sha256_file(detector_receipt),
            "textbook_url_map_sha256": sha256_file(textbook_url_map),
        },
        "claims": {
            "base_model_training_performed": False,
            "dataset_published": False,
            "raw_sources_redistribution_authorized": False,
            "perfect_ukrainian_guaranteed": False,
        },
    }


def write_validated(path: Path, value: Mapping[str, Any]) -> None:
    """Validate and atomically write a receipt."""
    schema = _read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise UsabilityAuditError(f"decision receipt is invalid at {location}: {errors[0].message}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write((canonical_json(value) + "\n").encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit whether the recovered corpus can serve Foundry training goals")
    parser.add_argument("--gdrive-root", type=Path, required=True)
    parser.add_argument("--profile-receipt", type=Path, default=PROFILE_PATH)
    parser.add_argument("--detector-receipt", type=Path, default=DETECTOR_PATH)
    parser.add_argument("--textbook-url-map", type=Path, default=URL_MAP_PATH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    decision = build_decision(
        literary_dir=args.gdrive_root / "literary_texts",
        textbook_chunks_dir=args.gdrive_root / "textbook_chunks",
        textbook_pdfs_dir=args.gdrive_root / "textbooks",
        textbook_url_map=args.textbook_url_map,
        profile_receipt=args.profile_receipt,
        detector_receipt=args.detector_receipt,
    )
    write_validated(args.output, decision)
    print(canonical_json(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
