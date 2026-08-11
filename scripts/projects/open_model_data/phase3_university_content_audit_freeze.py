#!/usr/bin/env python3
"""Build and validate the post-live Phase 3 university content-audit freeze.

The freeze closes the reviewed university candidate matrix and reconciles its
corpus-ingest subset with the live database.  It deliberately does not claim
SOURCE_COVERAGE_READY: the reviewed matrix still records bounded partial topic
coverage and the historical source freeze has an unresolved primary-source gap.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_VERSION = "phase3_university_content_audit_freeze_v1"
STATUS = "UNIVERSITY_CONTENT_AUDIT_FROZEN_PARTIAL_COVERAGE"
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_university_content_audit_freeze_v1.schema.json"
DEFAULT_OUTPUT_PATH = ROOT / "data/projects/open_model_data/admission/phase3_university_content_audit_freeze_v1.json"
DEFAULT_POLICY_PATH = ROOT / "data/projects/open_model_data/admission/phase3_complete_source_policy_v4.json"
DEFAULT_LIVE_GATE_PATH = ROOT / "data/projects/open_model_data/admission/phase3_live_ingest_gate_v1.json"
DEFAULT_HISTORICAL_PATH = ROOT / "data/projects/open_model_data/admission/phase3_historical_periodization_freeze_v1.json"
EXPECTED_OUTPUT_SHA256 = "d48db94a4576ffa13285d7678a774247ef6db484f85f866aa4a02f6fb33f5c0b"

EXPECTED_BINDINGS = {
    "phase3_reboot_prompt_v3_sha256": "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d",
    "phase3_recovery_prompt_v2_sha256": "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b",
    "complete_source_policy_v4_sha256": "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559",
    "university_source_matrix_v3_sha256": "e2e82934ec26b7d98002cdf87f5326b84fb2d3d7900fe675920ba99e84d190de",
    "university_source_matrix_canonical_payload_sha256": "935970fc72beb40c6e52b295dcad7ff756d9a6b8491b3eed11a56eadb3ce6c12",
    "final_source_admission_review_sha256": "8267f65aefdd8d14d24f1255c7bda4b7b92bc06f62f4c6e234696f39bd9ad22a",
    "live_ingest_gate_v1_sha256": "594b2de8ae357b4c33594a8d933d683284f4824c0c833624b20dffe75c6f6a63",
    "live_ingest_receipt_sha256": "899ecc0fe9a4aa86f7c6d169da914f4620922f0b8d6dfef4d820de7e826bc872",
    "post_live_backup_receipt_sha256": "6e2ce685a52f061b0dc8590159f9d25130ae9e08127c24e87c1725f4670dfa68",
    "pr6633_drive_backup_receipt_sha256": "13e6be4a518a1ad8654d732278650ccbd79de845b77b401661b8226f7d80aec2",
    "historical_periodization_freeze_v1_sha256": "94d07a2e4e2fe453334a494007bc823cf4be7ce07f0a21779c73163ac821a198",
}

EXPECTED_DATABASE = {
    "sha256": "de9a46838be3a4a6a2eb979ebdaf64b4d3d9984134b0074281d01b9cfd384876",
    "textbook_rows": 50153,
    "fts_rows": 50153,
    "section_rows": 36322,
    "total_sources": 187,
    "university_rows": 4078,
    "university_sources": 20,
    "integrity_check": "ok",
    "foreign_key_failure_count": 134836,
    "foreign_key_failure_sha256": "9938f7cbab6cca94bfd0a360eec114fdef404a357e02b24161da0f7cf5c6d9bb",
}

EXPECTED_TOPIC_AREAS = frozenset(
    {
        "phonetics",
        "phonology",
        "orthoepy",
        "accentology",
        "graphics",
        "orthography",
        "morphemics",
        "word formation",
        "lexicology",
        "semantics",
        "phraseology",
        "morphology",
        "syntax",
        "punctuation",
        "government/valency",
        "text linguistics",
        "discourse/pragmatics",
        "stylistics",
        "culture of language",
        "dialectology",
        "sociolinguistics",
        "language contact",
        "historical grammar",
        "history of the literary language",
        "corpus linguistics",
        "Ukrainian-specific computational linguistics/tokenization",
    }
)

LIVE_INGESTED_SOURCE_IDS = frozenset(
    {
        "uni-ukrmova-corpus-linguistics-khpi-2021-part-1",
        "uni-ukrmova-corpus-linguistics-khpi-2021-part-2",
        "uni-ukrmova-morphology-volkova-maslo-2012",
        "uni-ukrmova-text-linguistics-shevel-bilyk-2024",
    }
)


class UniversityContentAuditFreezeError(ValueError):
    """The post-live university freeze is incomplete, stale, or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UniversityContentAuditFreezeError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UniversityContentAuditFreezeError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def receipt_sha256(document: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in document.items() if key != "receipt_sha256"}
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


def _policy_sets(policy: Mapping[str, Any]) -> dict[str, set[str]]:
    sources = policy.get("sources")
    require(isinstance(sources, list), "complete source policy sources must be an array")
    by_id: dict[str, Mapping[str, Any]] = {}
    for source in sources:
        require(isinstance(source, Mapping), "complete source policy entry must be an object")
        source_id = source.get("source_id")
        require(isinstance(source_id, str) and source_id not in by_id, "invalid or duplicate policy source_id")
        by_id[source_id] = source
    candidate = set(by_id)
    corpus = {source_id for source_id, source in by_id.items() if "corpus_ingest" in source.get("allowed_lanes", [])}
    mandatory = {source_id for source_id, source in by_id.items() if source.get("final_disposition") == "admit_scoped"}
    quarantine = {source_id for source_id, source in by_id.items() if source.get("final_disposition") == "quarantine"}
    reference = candidate - corpus - quarantine
    return {
        "candidate": candidate,
        "corpus": corpus,
        "mandatory": mandatory,
        "quarantine": quarantine,
        "reference": reference,
    }


def _validate_topics(
    topics: Any,
    candidate_ids: set[str],
    quarantine_ids: set[str],
    *,
    expected_statuses: Counter[str],
) -> None:
    require(isinstance(topics, list) and len(topics) == 26, "topic denominator must contain exactly 26 areas")
    areas: list[str] = []
    statuses: Counter[str] = Counter()
    for topic in topics:
        require(isinstance(topic, Mapping), "topic row must be an object")
        area = topic.get("area")
        status = topic.get("status")
        supporting = topic.get("supporting_source_ids")
        depth = topic.get("supported_depth")
        needed = topic.get("qualified_source_needed")
        require(isinstance(area, str) and area not in areas, "invalid or duplicate topic area")
        require(status in {"missing", "partial", "sufficient"}, f"{area}: invalid topic status")
        require(
            isinstance(supporting, list)
            and len(supporting) == len(set(supporting))
            and set(supporting) <= candidate_ids
            and not (set(supporting) & quarantine_ids),
            f"{area}: invalid supporting source set",
        )
        require(isinstance(depth, str) and depth.strip(), f"{area}: missing supported depth")
        require(isinstance(needed, str) and needed.strip(), f"{area}: missing qualified-source gap")
        if status == "sufficient":
            require(needed.startswith("None;"), f"{area}: sufficient row must state that no source is needed")
        else:
            require(not needed.startswith("None;"), f"{area}: incomplete row cannot suppress its source need")
        areas.append(area)
        statuses[str(status)] += 1
    require(set(areas) == EXPECTED_TOPIC_AREAS, "topic area denominator drift")
    require(statuses == expected_statuses, "topic coverage counts drift")


def validate_document(
    document: Mapping[str, Any],
    *,
    policy_path: Path = DEFAULT_POLICY_PATH,
    schema_path: Path = SCHEMA_PATH,
) -> dict[str, Any]:
    schema = read_json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path))
    require(not errors, "; ".join(error.message for error in errors))
    require(document.get("receipt_sha256") == receipt_sha256(document), "freeze receipt hash drift")
    require(document.get("bindings") == EXPECTED_BINDINGS, "freeze bindings drift")

    policy = read_json(policy_path)
    require(sha256_file(policy_path) == EXPECTED_BINDINGS["complete_source_policy_v4_sha256"], "complete source policy byte drift")
    policy_sets = _policy_sets(policy)
    source_universe = document["source_universe"]
    expected_lists = {
        "candidate_source_ids": policy_sets["candidate"],
        "database_resident_source_ids": policy_sets["corpus"],
        "reference_only_source_ids": policy_sets["reference"],
        "quarantine_source_ids": policy_sets["quarantine"],
        "mandatory_conversion_source_ids": policy_sets["mandatory"],
    }
    for key, expected in expected_lists.items():
        require(source_universe[key] == sorted(expected), f"{key} does not match the complete source policy")
    require(source_universe["candidate_source_count"] == 30, "candidate source denominator drift")
    require(source_universe["database_resident_source_count"] == 20, "database-resident source count drift")
    require(source_universe["reference_only_source_count"] == 6, "reference-only source count drift")
    require(source_universe["quarantine_source_count"] == 4, "quarantine source count drift")
    require(source_universe["mandatory_conversion_source_count"] == 11, "mandatory conversion source count drift")
    require(source_universe["disposition_counts"] == policy.get("disposition_counts"), "source disposition counts drift")

    database = document["database"]
    require(database == EXPECTED_DATABASE, "frozen database facts drift")
    topic_coverage = document["topic_coverage"]
    require(
        topic_coverage["counts"]
        == {"areas_required": 26, "missing": 0, "partial": 21, "sufficient": 5},
        "topic coverage summary drift",
    )
    _validate_topics(
        topic_coverage["topics"],
        policy_sets["candidate"],
        policy_sets["quarantine"],
        expected_statuses=Counter({"partial": 21, "sufficient": 5}),
    )
    reconciliations = topic_coverage["post_review_reconciliations"]
    require(
        reconciliations
        == [
            {
                "area": "text linguistics",
                "prior_status": "partial",
                "final_status": "sufficient",
                "reason": (
                    "The final Ukrainian source review admitted Shevel and Bilyk (2024) with no missing evidence, "
                    "and the exact 282-row source is now live database-resident and Drive-backed."
                ),
            }
        ],
        "post-review topic reconciliation drift",
    )

    controls = document["authority_controls"]
    require(controls["database_set_equals_policy_corpus_ingest_set"] is True, "database/policy set equality not frozen")
    require(controls["l2_sources_excluded_from_native_normative_target"] is True, "L2 exclusion drift")
    require(controls["contextual_sources_cannot_authorize_rules"] is True, "contextual authority drift")
    require(controls["quarantined_sources_have_no_lanes"] is True, "quarantine lane drift")
    require(controls["source_text_committed"] is False, "source text must remain private")

    gates = document["gates"]
    require(gates["university_content_audit_complete"] is True, "university content audit is not closed")
    require(gates["university_database_reconciled"] is True, "university database is not reconciled")
    require(gates["university_source_freeze_ready"] is True, "university source freeze is not ready")
    require(gates["source_coverage_ready"] is False, "partial topic coverage cannot claim SOURCE_COVERAGE_READY")
    require(gates["overall_phase3_source_freeze_ready"] is False, "historical residual cannot close the overall source freeze")
    require(gates["phase3_complete"] is False and gates["phase4_blocked"] is True, "phase boundary drift")
    return dict(document)


def _database_evidence(path: Path) -> tuple[dict[str, Any], list[str]]:
    require(path.is_file(), f"database is missing: {path}")
    require(sha256_file(path) == EXPECTED_DATABASE["sha256"], "live database SHA-256 drift")
    uri = f"file:{path.resolve()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        counts = {
            "textbook_rows": connection.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0],
            "fts_rows": connection.execute("SELECT COUNT(*) FROM textbooks_fts").fetchone()[0],
            "section_rows": connection.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0],
            "total_sources": connection.execute("SELECT COUNT(DISTINCT source_file) FROM textbooks").fetchone()[0],
            "university_rows": connection.execute("SELECT COUNT(*) FROM textbooks WHERE grade='university'").fetchone()[0],
            "university_sources": connection.execute(
                "SELECT COUNT(DISTINCT source_file) FROM textbooks WHERE grade='university'"
            ).fetchone()[0],
        }
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        failures = sorted(tuple(row) for row in connection.execute("PRAGMA foreign_key_check").fetchall())
        university_ids = [
            str(row[0])
            for row in connection.execute(
                "SELECT DISTINCT source_file FROM textbooks WHERE grade='university' ORDER BY source_file"
            ).fetchall()
        ]
    failure_hash = sha256_bytes(json.dumps(failures, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    evidence = {
        "sha256": sha256_file(path),
        **counts,
        "integrity_check": integrity,
        "foreign_key_failure_count": len(failures),
        "foreign_key_failure_sha256": failure_hash,
    }
    return evidence, university_ids


def _validate_drive_backup(post_backup: Mapping[str, Any]) -> None:
    backup = post_backup.get("backup")
    require(isinstance(backup, Mapping), "post-live backup receipt has no backup object")
    require(backup.get("google_drive_upload_verified") is True, "post-live database backup is not provider-verified")
    require(backup.get("google_drive_uploading") is False, "post-live database backup is still uploading")
    require(isinstance(backup.get("google_drive_item_id"), str) and backup["google_drive_item_id"], "Drive item id is absent")
    backup_path = Path(str(backup.get("path", "")))
    require(backup_path.is_file(), "post-live compressed database backup is absent")
    require(sha256_file(backup_path) == backup.get("compressed_sha256"), "post-live compressed database backup hash drift")
    try:
        provider_probe = subprocess.run(
            ["xattr", "-p", "com.google.drivefs.item-id#S", str(backup_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise UniversityContentAuditFreezeError("post-live database backup lacks Drive provider metadata") from exc
    item_id = provider_probe.stdout.strip()
    require(item_id == backup.get("google_drive_item_id"), "post-live database backup Drive identity drift")
    with gzip.open(backup_path, "rb") as stream:
        restored_hash = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            restored_hash.update(chunk)
    require(restored_hash.hexdigest() == backup.get("decompressed_sha256"), "post-live backup does not restore exact database bytes")


def build_document(
    *,
    matrix_path: Path,
    final_review_path: Path,
    database_path: Path,
    post_backup_path: Path,
    live_ingest_receipt_path: Path,
    pr6633_drive_receipt_path: Path,
    policy_path: Path = DEFAULT_POLICY_PATH,
    live_gate_path: Path = DEFAULT_LIVE_GATE_PATH,
    historical_path: Path = DEFAULT_HISTORICAL_PATH,
) -> dict[str, Any]:
    for label, path, expected in (
        ("matrix", matrix_path, EXPECTED_BINDINGS["university_source_matrix_v3_sha256"]),
        ("final review", final_review_path, EXPECTED_BINDINGS["final_source_admission_review_sha256"]),
        ("post-live backup", post_backup_path, EXPECTED_BINDINGS["post_live_backup_receipt_sha256"]),
        ("live ingest", live_ingest_receipt_path, EXPECTED_BINDINGS["live_ingest_receipt_sha256"]),
        ("PR 6633 Drive", pr6633_drive_receipt_path, EXPECTED_BINDINGS["pr6633_drive_backup_receipt_sha256"]),
        ("policy", policy_path, EXPECTED_BINDINGS["complete_source_policy_v4_sha256"]),
        ("live gate", live_gate_path, EXPECTED_BINDINGS["live_ingest_gate_v1_sha256"]),
        ("historical periodization", historical_path, EXPECTED_BINDINGS["historical_periodization_freeze_v1_sha256"]),
    ):
        require(sha256_file(path) == expected, f"{label} input byte drift")

    matrix = read_json(matrix_path)
    require(
        matrix.get("canonical_payload_sha256")
        == EXPECTED_BINDINGS["university_source_matrix_canonical_payload_sha256"],
        "matrix canonical payload hash drift",
    )
    policy = read_json(policy_path)
    policy_sets = _policy_sets(policy)
    database, university_ids = _database_evidence(database_path)
    require(database == EXPECTED_DATABASE, "live database facts do not match the frozen post-ingest state")
    require(university_ids == sorted(policy_sets["corpus"]), "live university source set does not equal policy corpus-ingest set")

    post_backup = read_json(post_backup_path)
    _validate_drive_backup(post_backup)
    require(post_backup.get("database") == {key: EXPECTED_DATABASE[key] for key in ("fts_rows", "integrity_check", "section_rows", "sha256", "textbook_rows", "total_sources", "university_rows", "university_sources")}, "post-live backup database facts drift")
    live_receipt = read_json(live_ingest_receipt_path)
    require(live_receipt.get("status") == "committed", "live ingest did not commit")
    require(
        sum(int(row.get("inserted_rows", -1)) for row in live_receipt.get("per_source", [])) == 585,
        "live ingest row denominator drift",
    )
    require(
        set(live_receipt.get("requested_replace_sources", [])) == LIVE_INGESTED_SOURCE_IDS,
        "live ingest source set drift",
    )
    require(live_receipt.get("requested_quarantine_sources") == [], "live ingest unexpectedly quarantined sources")
    historical = read_json(historical_path)
    require(historical.get("periodization_layer_ready") is True, "historical periodization layer is not ready")
    require(historical.get("overall_phase3_source_freeze_ready") is False, "historical artifact unexpectedly closes overall source freeze")

    matrix_topics = matrix.get("topic_gap_matrix")
    _validate_topics(
        matrix_topics,
        policy_sets["candidate"],
        policy_sets["quarantine"],
        expected_statuses=Counter({"partial": 22, "sufficient": 4}),
    )
    topics = [
        {
            "area": topic["area"],
            "status": topic["status"],
            "supported_depth": topic["supported_depth"],
            "supporting_source_ids": topic["supporting_source_ids"],
            "qualified_source_needed": topic["qualified_source_needed"],
        }
        for topic in matrix_topics
    ]
    text_linguistics = next(topic for topic in topics if topic["area"] == "text linguistics")
    text_linguistics["status"] = "sufficient"
    text_linguistics["supported_depth"] = (
        "complete qualified 2024 textbook with definitions, theory, examples, and exercises"
    )
    text_linguistics["qualified_source_needed"] = (
        "None; the Shevel and Bilyk (2024) source passed final Ukrainian source review, is live database-resident, "
        "and supplies the complete qualified textbook identified by the matrix."
    )
    document: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "status": STATUS,
        "bindings": dict(EXPECTED_BINDINGS),
        "database": dict(EXPECTED_DATABASE),
        "source_universe": {
            "candidate_source_count": 30,
            "candidate_source_ids": sorted(policy_sets["candidate"]),
            "database_resident_source_count": 20,
            "database_resident_source_ids": sorted(policy_sets["corpus"]),
            "reference_only_source_count": 6,
            "reference_only_source_ids": sorted(policy_sets["reference"]),
            "quarantine_source_count": 4,
            "quarantine_source_ids": sorted(policy_sets["quarantine"]),
            "mandatory_conversion_source_count": 11,
            "mandatory_conversion_source_ids": sorted(policy_sets["mandatory"]),
            "disposition_counts": policy["disposition_counts"],
            "live_ingested_source_ids": sorted(LIVE_INGESTED_SOURCE_IDS),
            "live_ingested_rows": 585,
        },
        "topic_coverage": {
            "counts": {"areas_required": 26, "missing": 0, "partial": 21, "sufficient": 5},
            "topics": topics,
            "post_review_reconciliations": [
                {
                    "area": "text linguistics",
                    "prior_status": "partial",
                    "final_status": "sufficient",
                    "reason": (
                        "The final Ukrainian source review admitted Shevel and Bilyk (2024) with no missing "
                        "evidence, and the exact 282-row source is now live database-resident and Drive-backed."
                    ),
                }
            ],
        },
        "authority_controls": {
            "database_set_equals_policy_corpus_ingest_set": True,
            "l2_sources_excluded_from_native_normative_target": True,
            "contextual_sources_cannot_authorize_rules": True,
            "quarantined_sources_have_no_lanes": True,
            "source_text_committed": False,
            "superseded_denominator_path": "data/university_corpus_denominator.yaml",
            "superseded_denominator_sha256": "c677220bea2ba5b3449f528b53a93cf2e55f4b8f5b654d6af3c55910c6fd299f",
            "supersession_reason": "The legacy 12-source denominator mixes L2, stale custody, and pre-reconciliation database identities; the reviewed 30-source policy and exact 20-source corpus subset now govern Phase 3.",
        },
        "gates": {
            "university_content_audit_complete": True,
            "university_database_reconciled": True,
            "university_source_freeze_ready": True,
            "source_coverage_ready": False,
            "overall_phase3_source_freeze_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
        "remaining_residuals": [
            "Twenty-one of twenty-six required university topic areas remain partial; each exact qualified-source need is frozen in topic_coverage.topics.",
            "The original two-part 1997/1998 Nimchuk periodization article remains bibliographically located but not locally acquired and byte-hashed.",
            "Historical document-level language variety, rights, attribution, and mandatory conversion-family freezes remain incomplete.",
            "The unchanged foreign-key failure baseline is preserved as known technical debt and was not introduced by the university ingest.",
        ],
    }
    document["receipt_sha256"] = receipt_sha256(document)
    return validate_document(document, policy_path=policy_path)


def write_json_atomic(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.is_symlink(), f"refusing symlink output: {path}")
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--write", type=Path)
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--final-review", type=Path)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--post-backup", type=Path)
    parser.add_argument("--live-ingest-receipt", type=Path)
    parser.add_argument("--pr6633-drive-receipt", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument("--live-gate", type=Path, default=DEFAULT_LIVE_GATE_PATH)
    parser.add_argument("--historical", type=Path, default=DEFAULT_HISTORICAL_PATH)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.write is not None:
        required = {
            "--matrix": args.matrix,
            "--final-review": args.final_review,
            "--database": args.database,
            "--post-backup": args.post_backup,
            "--live-ingest-receipt": args.live_ingest_receipt,
            "--pr6633-drive-receipt": args.pr6633_drive_receipt,
        }
        missing = [name for name, value in required.items() if value is None]
        require(not missing, f"write mode requires: {', '.join(missing)}")
        document = build_document(
            matrix_path=args.matrix,
            final_review_path=args.final_review,
            database_path=args.database,
            post_backup_path=args.post_backup,
            live_ingest_receipt_path=args.live_ingest_receipt,
            pr6633_drive_receipt_path=args.pr6633_drive_receipt,
            policy_path=args.policy,
            live_gate_path=args.live_gate,
            historical_path=args.historical,
        )
        write_json_atomic(args.write, document)
    else:
        if args.check.resolve() == DEFAULT_OUTPUT_PATH.resolve():
            require(sha256_file(args.check) == EXPECTED_OUTPUT_SHA256, "tracked university content-audit freeze byte drift")
        validate_document(read_json(args.check), policy_path=args.policy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
