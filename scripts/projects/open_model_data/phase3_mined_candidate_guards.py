"""Guards for Phase 3.1–3.2 mined candidates (#8006 / #8015 CF F1–F5).

These predicates are the acceptance-criteria lock: inverted date-range gold,
miner-invented UA-GEC wrappers, invented ZNO ellipses, and unconstrained
manifest filenames must fail here even when a JSONL file is otherwise well-formed.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import jsonschema

from scripts.projects.open_model_data.phase3_decolonization_partition import (
    is_phase30_uagec_heldout_doc,
)

DEFAULT_CUSTODY_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "projects"
    / "open_model_data"
    / "decolonization"
    / "partitions"
    / "train_source_custody.json"
)

ALLOWED_MINED_JSONL_FILENAMES = frozenset(
    {
        "corpus_contrast_tables.jsonl",
        "zno_distractor_tasks.jsonl",
        "uagec_mined_calques.jsonl",
    }
)
MINED_FILENAME_RE = re.compile(r"^(corpus_contrast_tables|zno_distractor_tasks|uagec_mined_calques)\.jsonl$")

DO_DATE_RANGE_RE = re.compile(r"\bз\s+\d+\s+до\b", re.IGNORECASE)
PO_DATE_RANGE_RE = re.compile(r"\bз\s+\d+\s+по\b", re.IGNORECASE)
SYNTHETIC_UAGEC_WRAPPER_RE = re.compile(
    r"^У тексті вжито (?:вираз|конструкцію):\s*«.+»\s*\(виправлено на:\s*«.+»\)\.?\s*$"
)
# Ukrainian «скорочено». The previous typo ``[c?корочено]`` never matched
# ``[скорочено]`` and left miner-spliced `` ... ... `` behind.
INVENTED_ZNO_ELLIPSIS_RE = re.compile(r"\[\s*(?:c|с)?корочено\s*\]", re.IGNORECASE)
INVENTED_ZNO_CONNECTOR_RE = re.compile(
    r"\s*\.\.\.\s*\[\s*(?:c|с)?корочено\s*\]\s*\.\.\.\s*",
    re.IGNORECASE,
)
INVENTED_ZNO_SPLICE_RE = re.compile(r"\s*\.\.\.\s*\.\.\.\s*")

SCHEMA_RECORD_DEFS = {
    "corpus_contrast_tables": "contrastRecord",
    "zno_distractor_tasks": "znoRecord",
    "uagec_mined_calques": "uagecRecord",
}


def is_inverted_do_po_date_range(incorrect: str, correct: str) -> bool:
    """True when normative Ukrainian ``з N до`` is labeled wrong against calque ``з N по``."""
    return bool(DO_DATE_RANGE_RE.search(incorrect or "") and PO_DATE_RANGE_RE.search(correct or ""))


def is_synthetic_uagec_wrapper(sentence_context: str) -> bool:
    """True for miner-invented «У тексті вжито вираз/конструкцію» wrappers."""
    return bool(SYNTHETIC_UAGEC_WRAPPER_RE.match((sentence_context or "").strip()))


def contains_invented_zno_ellipsis(stem: str) -> bool:
    """True for miner-inserted ``[скорочено]`` or leftover spliced `` ... ... ``."""
    text = stem or ""
    return bool(INVENTED_ZNO_ELLIPSIS_RE.search(text) or INVENTED_ZNO_SPLICE_RE.search(text))


def is_constrained_mined_filename(filename: str) -> bool:
    """True only for the three basename-only mined JSONL artifacts."""
    if not filename or "/" in filename or "\\" in filename:
        return False
    return bool(MINED_FILENAME_RE.fullmatch(filename))


def is_grounded_uagec_sentence(sentence_context: str, error: str) -> bool:
    """Fail-closed: original sentence, not a wrapper, and it contains the error span."""
    ctx = (sentence_context or "").strip()
    err = (error or "").strip()
    if not ctx or not err:
        return False
    if is_synthetic_uagec_wrapper(ctx):
        return False
    if contains_invented_zno_ellipsis(ctx):
        return False
    return err in ctx


def g_case_ratio(g_case_admitted: int, mined_records: int) -> float:
    """Exact (unrounded) G/Case share used for the ≤ 0.25 curriculum cap."""
    if mined_records <= 0:
        return 0.0
    return g_case_admitted / mined_records


def g_case_ratio_within_cap(g_case_admitted: int, mined_records: int) -> bool:
    return g_case_ratio(g_case_admitted, mined_records) <= 0.25


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _record_schema(schema: Mapping[str, Any], def_name: str) -> dict[str, Any]:
    defs = schema.get("$defs") or {}
    if def_name not in defs:
        raise ValueError(f"schema is missing $defs.{def_name}")
    return {
        "$schema": schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "$defs": defs,
        **defs[def_name],
    }


def verify_mined_manifest(
    output_dir: Path,
    schema_path: Path,
) -> dict[str, Any]:
    """Validate manifest + JSONL bytes/hashes/record schemas. Raises ValueError on failure."""
    manifest_path = output_dir / "decolonization_mined_manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"Missing manifest: {manifest_path.name}")
    if not schema_path.is_file():
        raise ValueError(f"Missing schema: {schema_path.name}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(manifest))
    if errors:
        raise ValueError(f"Manifest schema errors: {[e.message for e in errors]}")

    files = manifest["files"]
    for key, fmeta in files.items():
        filename = fmeta["filename"]
        if not is_constrained_mined_filename(filename):
            raise ValueError(f"Unconstrained mined filename: {filename!r}")
        fpath = output_dir / filename
        if not fpath.is_file():
            raise ValueError(f"Missing artifact: {filename}")
        actual_sha = sha256_file(fpath)
        if actual_sha != fmeta["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {filename}: manifest {fmeta['sha256']} file {actual_sha}")
        records = load_jsonl(fpath)
        if len(records) != fmeta["record_count"]:
            raise ValueError(
                f"Record count mismatch for {filename}: manifest {fmeta['record_count']} file {len(records)}"
            )
        def_name = SCHEMA_RECORD_DEFS[key]
        record_schema = _record_schema(schema, def_name)
        validator = jsonschema.Draft202012Validator(record_schema)
        for index, rec in enumerate(records):
            rec_errors = list(validator.iter_errors(rec))
            if rec_errors:
                raise ValueError(f"{filename} line {index + 1}: {rec_errors[0].message}")

    uagec_path = output_dir / "uagec_mined_calques.jsonl"
    uagec_records = load_jsonl(uagec_path)
    heldout = [rec["doc_id"] for rec in uagec_records if is_phase30_uagec_heldout_doc(str(rec["doc_id"]))]
    if heldout:
        raise ValueError(f"Phase 3.0 held-out UA-GEC leak: {len(set(heldout))} docs")
    wrappers = sum(1 for rec in uagec_records if is_synthetic_uagec_wrapper(rec.get("sentence_context", "")))
    if wrappers:
        raise ValueError(f"Synthetic UA-GEC wrappers present: {wrappers}")
    ungrounded = [
        rec["record_id"]
        for rec in uagec_records
        if not is_grounded_uagec_sentence(rec.get("sentence_context", ""), rec.get("error", ""))
    ]
    if ungrounded:
        raise ValueError(f"Ungrounded UA-GEC sentence_context: {len(ungrounded)}")

    contrast_path = output_dir / "corpus_contrast_tables.jsonl"
    inverted = [
        rec.get("item_id")
        for rec in load_jsonl(contrast_path)
        if is_inverted_do_po_date_range(rec.get("incorrect", ""), rec.get("correct", ""))
    ]
    if inverted:
        raise ValueError(f"Inverted з…до / з…по gold pairs: {inverted}")

    zno_path = output_dir / "zno_distractor_tasks.jsonl"
    invented = [
        rec.get("task_id") for rec in load_jsonl(zno_path) if contains_invented_zno_ellipsis(rec.get("stem", ""))
    ]
    if invented:
        raise ValueError(f"Invented ZNO ellipsis or spliced ' ... ... ' in stems: {len(invented)}")

    summary = manifest["uagec_mining_summary"]
    admitted = int(summary["g_case_admitted"])
    mined = int(files["uagec_mined_calques"]["record_count"])
    exact = g_case_ratio(admitted, mined)
    if not g_case_ratio_within_cap(admitted, mined):
        raise ValueError(f"G/Case cap violated: {exact} > 0.25")
    reported = float(summary["g_case_admitted_ratio"])
    if abs(exact - reported) > 1e-6:
        raise ValueError(f"g_case_admitted_ratio {reported} != {admitted}/{mined} ({exact})")

    custody_path = DEFAULT_CUSTODY_FILE
    if custody_path.is_file():
        custody = json.loads(custody_path.read_text(encoding="utf-8"))
        zno_expected = custody.get("zno_tasks", {}).get("count")
        zno_actual = int(files["zno_distractor_tasks"]["record_count"])
        if zno_expected is not None and zno_actual != zno_expected:
            raise ValueError(f"ZNO count {zno_actual} != custody {zno_expected}")

    return {"ok": True, "files": {key: fmeta["sha256"] for key, fmeta in files.items()}}
