"""Build a content-blind inventory of existing Ukrainian corpus assets.

The live collector reads SQLite with ``mode=ro``, inventories only filesystem
metadata outside Git, and emits no corpus or lesson bodies.  A fixture mode
validates and summarizes prebuilt metadata records without requiring Google
Drive, KubeDojo, or the live databases in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
from collections import Counter
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA = (
    ROOT
    / "data/projects/open_model_data/inventory/existing_asset_inventory_v1.schema.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "data/projects/open_model_data/inventory"
LEDGER_NAME = "recovery_ledger_v1.jsonl"
SUMMARY_NAME = "aggregate_summary_v1.json"
SCHEMA_VERSION = "existing_asset_inventory_v1"
SUMMARY_SCHEMA_VERSION = "existing_asset_inventory_summary_v1"

ORIGIN_CLASSES = (
    "human_authored_source",
    "machine_generated_ukrainian",
    "machine_translated_ukrainian",
    "human_revised_synthetic",
    "unknown_origin",
)
DATA_BOUNDARIES = (
    "public_or_external_source",
    "private_reference",
    "evaluation_only",
    "project_internal",
    "mixed",
    "unknown",
)

WORD_PATTERN = r"[^\W\d_]+(?:[’'][^\W\d_]+)*"
WORD_RE = re.compile(WORD_PATTERN, re.UNICODE)

PRIVATE_TEXTBOOK_SOURCES = (
    "anna-ohoiko-1000-words-2nd-ed",
    "anna-ohoiko-500-verbs",
    "ulp-1-00-lesson-notes",
    "ulp-2-00-lesson-notes",
    "ulp-3-00-lesson-notes",
    "ulp-4-00-lesson-notes",
    "ulp-5-00-lesson-notes",
    "ulp-6-00-lesson-notes",
)

PRIVATE_RAW_PATHS = {
    "anna-ohoiko-1000-words-2nd-ed": "private_curriculum/ohoiko/1000-words-2nd-ed.jsonl",
    "anna-ohoiko-500-verbs": "private_curriculum/ohoiko/500-verbs.jsonl",
    "ulp-1-00-lesson-notes": "private_curriculum/ulp/season-01/ulp-1-00-lesson-notes.jsonl",
    "ulp-2-00-lesson-notes": "private_curriculum/ulp/season-02/ulp-2-00-lesson-notes.jsonl",
    "ulp-3-00-lesson-notes": "private_curriculum/ulp/season-03/ulp-3-00-lesson-notes.jsonl",
    "ulp-4-00-lesson-notes": "private_curriculum/ulp/season-04/ulp-4-00-lesson-notes.jsonl",
    "ulp-5-00-lesson-notes": "private_curriculum/ulp/season-05/ulp-5-00-lesson-notes.jsonl",
    "ulp-6-00-lesson-notes": "private_curriculum/ulp/season-06/ulp-6-00-lesson-notes.jsonl",
}

DICTIONARY_COLLECTIONS = (
    ("sum11", "СУМ-11", "human_authored_source", "sum11/chunks.jsonl"),
    ("esum_cognate_forms", "ЕСУМ cognate forms", "human_authored_source", None),
    ("esum_etymology", "ЕСУМ etymology", "human_authored_source", None),
    ("grinchenko", "Грінченко 1907", "human_authored_source", "grinchenko/chunks.jsonl"),
    ("balla_en_uk", "Балла EN→UK", "human_authored_source", "balla-en-uk/chunks.jsonl"),
    ("dmklinger_uk_en", "dmklinger UK→EN", "unknown_origin", "dmklinger-uk-en/chunks.jsonl"),
    ("ukrajinet", "Ukrajinet WordNet", "machine_translated_ukrainian", "ukrajinet/chunks.jsonl"),
    ("wiktionary", "Ukrainian Wiktionary", "human_authored_source", "wiktionary/chunks.jsonl"),
    (
        "frazeolohichnyi",
        "Фразеологічний словник",
        "human_authored_source",
        "frazeolohichnyi/chunks.jsonl",
    ),
    (
        "style_guide",
        "Антоненко-Давидович style guide",
        "human_authored_source",
        "antonenko-davydovych/chunks.jsonl",
    ),
    ("puls_cefr", "PULS CEFR vocabulary", "human_authored_source", None),
)

CORE_TRACKS = ("a1", "a2", "b1", "b2")
FOLK_RECOVERY_COMMITS = {
    "dumy-nevilnytski-lytsarski": "cd46eb9e829ba5e3f40723c62db85fa4b6546e5f",
    "kalendarna-obriadovist-zvychai": "cd46eb9e829ba5e3f40723c62db85fa4b6546e5f",
    "koliadky-shchedrivky": "cd46eb9e829ba5e3f40723c62db85fa4b6546e5f",
    "narodna-kultura-yak-systema": "cd46eb9e829ba5e3f40723c62db85fa4b6546e5f",
    "narodni-viruvannia-mifolohiia-demonolohiia": (
        "5f9d1697b83e234466f8c61a5ac014d5c6cc4c1e"
    ),
    "zamovliannia-zaklynannia-prymovky": "5f9d1697b83e234466f8c61a5ac014d5c6cc4c1e",
}
ARCHIVED_PLANS_WITHOUT_MODULE_EVIDENCE = (
    "bohatyri-illiya-dobrynia",
    "bylyny-sotsialni",
    "dumy-lytsarski",
    "pokhodzhennia-dum",
    "rusalni-pisni",
    "zastavy-bohatyrski",
)
WEIGHT_SUFFIXES = (
    ".adapter",
    ".bin",
    ".ckpt",
    ".gguf",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
)

ELIGIBILITY_KEYS = (
    "internal_rag_reference",
    "provenance_investigation",
    "potential_training_admission",
    "redistribution_investigation",
    "evaluation_only",
    "synthetic_research_only",
    "excluded_pending_review",
)


def canonical_json(value: Any) -> str:
    """Return stable compact JSON without ASCII-escaping Ukrainian text."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def empty_coverage() -> dict[str, dict[str, int]]:
    return {
        "genres": {},
        "grades": {},
        "periods": {},
        "regions": {},
        "registers": {},
        "subjects": {},
    }


def eligibility(**enabled: bool) -> dict[str, bool]:
    unknown = set(enabled) - set(ELIGIBILITY_KEYS)
    if unknown:
        raise ValueError(f"unknown eligibility keys: {sorted(unknown)}")
    return {key: bool(enabled.get(key, False)) for key in ELIGIBILITY_KEYS}


def make_record(
    *,
    asset_id: str,
    label: str,
    asset_kind: str,
    origin_class: str,
    data_boundary: str,
    lifecycle_states: Iterable[str],
    measurement_scope: str,
    metrics: dict[str, Any],
    coverage: dict[str, dict[str, int]] | None,
    raw_artifact_presence: str,
    ingestion_status: str,
    content_hash_status: str,
    provenance_status: str,
    rights_status: str,
    eligibility_flags: dict[str, bool],
    evidence_refs: Iterable[str],
    limitations: Iterable[str] = (),
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one normalized metadata-only ledger record."""
    return {
        "asset_id": asset_id,
        "asset_kind": asset_kind,
        "coverage": coverage or empty_coverage(),
        "data_boundary": data_boundary,
        "details": details or {},
        "eligibility": eligibility_flags,
        "evidence_refs": sorted(set(evidence_refs)),
        "label": label,
        "lifecycle_states": sorted(set(lifecycle_states)),
        "limitations": sorted(set(limitations)),
        "lineage": {
            "content_hash_status": content_hash_status,
            "ingestion_status": ingestion_status,
            "provenance_status": provenance_status,
            "raw_artifact_presence": raw_artifact_presence,
        },
        "measurement_scope": measurement_scope,
        "metrics": dict(sorted(metrics.items())),
        "origin_class": origin_class,
        "rights_status": rights_status,
        "schema_version": SCHEMA_VERSION,
    }


def load_schema(path: Path) -> tuple[dict[str, Any], str]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema, sha256_file(path)


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_strings(child)


def assert_portable_metadata(records: Sequence[dict[str, Any]]) -> None:
    """Reject personal absolute paths, emails, and accidentally emitted bodies."""
    for record in records:
        for value in _iter_strings(record):
            if value.startswith(("/Users/", "/home/", "file://")):
                raise ValueError(f"absolute path leaked in {record.get('asset_id')}")
            if "@" in value and "github://" not in value:
                raise ValueError(f"email-like metadata leaked in {record.get('asset_id')}")
        forbidden_keys = {"content", "lesson", "prompt", "raw_response", "text"}
        if forbidden_keys.intersection(record.get("details", {})):
            raise ValueError(f"content-bearing detail key in {record.get('asset_id')}")


def validate_records(records: Sequence[dict[str, Any]], schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    ids: set[str] = set()
    errors: list[str] = []
    for record in records:
        asset_id = str(record.get("asset_id", "<missing>"))
        if asset_id in ids:
            errors.append(f"duplicate asset_id: {asset_id}")
        ids.add(asset_id)
        for error in validator.iter_errors(record):
            path = ".".join(str(part) for part in error.absolute_path)
            errors.append(f"{asset_id}:{path}:{error.message}")
        if record.get("eligibility", {}).get("potential_training_admission"):
            errors.append(f"{asset_id}: no source-record-v1 admission evidence permits training")
    assert_portable_metadata(records)
    if errors:
        raise ValueError("inventory validation failed:\n" + "\n".join(sorted(errors)))


def connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def count_map(
    connection: sqlite3.Connection,
    sql: str,
    parameters: Sequence[Any] = (),
) -> dict[str, int]:
    return {
        str(key if key not in (None, "") else "unknown"): int(count)
        for key, count in connection.execute(sql, parameters)
    }


def text_metrics(
    connection: sqlite3.Connection,
    sql: str,
    parameters: Sequence[Any] = (),
) -> dict[str, int | str]:
    rows = characters = lexical_words = whitespace_tokens = 0
    for (raw_text,) in connection.execute(sql, parameters):
        value = str(raw_text or "")
        rows += 1
        characters += len(value)
        lexical_words += len(WORD_RE.findall(value))
        whitespace_tokens += len(value.split())
    return {
        "characters": characters,
        "content_units": rows,
        "lexical_words": lexical_words,
        "rows": rows,
        "unit_label": "database_rows",
        "whitespace_tokens": whitespace_tokens,
    }


def _placeholders(count: int) -> str:
    return ",".join("?" for _ in range(count))


def _logical_files(root: Path, pattern: str) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.glob(pattern) if path.is_file())


def _source_stems(root: Path, pattern: str) -> set[str]:
    return {path.stem for path in root.glob(pattern) if path.is_file()}


def files_text_metrics(paths: Iterable[Path], unit_label: str) -> dict[str, int | str]:
    files = characters = lexical_words = whitespace_tokens = 0
    for path in sorted(paths):
        value = path.read_text(encoding="utf-8")
        files += 1
        characters += len(value)
        lexical_words += len(WORD_RE.findall(value))
        whitespace_tokens += len(value.split())
    return {
        "characters": characters,
        "content_units": files,
        "files": files,
        "lexical_words": lexical_words,
        "unit_label": unit_label,
        "whitespace_tokens": whitespace_tokens,
    }


def row_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def _db_record(
    *,
    connection: sqlite3.Connection,
    asset_id: str,
    label: str,
    table: str,
    text_column: str,
    origin_class: str,
    data_boundary: str,
    where: str = "",
    parameters: Sequence[Any] = (),
    coverage: dict[str, dict[str, int]] | None = None,
    details: dict[str, Any] | None = None,
    rights_status: str = "not_reconstructed",
    evaluation_only: bool = False,
) -> dict[str, Any]:
    clause = f" WHERE {where}" if where else ""
    metrics = text_metrics(
        connection,
        f'SELECT "{text_column}" FROM "{table}"{clause}',
        parameters,
    )
    return make_record(
        asset_id=asset_id,
        label=label,
        asset_kind="evaluation_collection" if evaluation_only else "source_collection",
        origin_class=origin_class,
        data_boundary=data_boundary,
        lifecycle_states=("current", "ingested"),
        measurement_scope="distinct_content",
        metrics=metrics,
        coverage=coverage,
        raw_artifact_presence="unknown",
        ingestion_status="ingested",
        content_hash_status="not_measured",
        provenance_status="partial",
        rights_status=rights_status,
        eligibility_flags=eligibility(
            evaluation_only=evaluation_only,
            excluded_pending_review=True,
            internal_rag_reference=not evaluation_only,
            provenance_investigation=True,
            redistribution_investigation=(
                not evaluation_only
                and data_boundary == "public_or_external_source"
            ),
        ),
        evidence_refs=(f"sqlite:sources.db#{table}",),
        limitations=(
            "Rights and per-source provenance are not normalized to source-record-v1.",
        ),
        details=details,
    )


def collect_database_records(
    database: Path,
    vesum_database: Path,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with connect_read_only(database) as connection:
        literary_coverage = empty_coverage()
        literary_coverage["genres"] = count_map(
            connection,
            "SELECT genre, COUNT(*) FROM literary_texts GROUP BY genre",
        )
        literary_coverage["periods"] = count_map(
            connection,
            "SELECT language_period, COUNT(*) FROM literary_texts "
            "GROUP BY language_period",
        )
        literary_details = {
            "distinct_works": int(
                connection.execute(
                    "SELECT COUNT(DISTINCT work_id) FROM literary_texts"
                ).fetchone()[0]
            ),
            "rows_with_source_url": int(
                connection.execute(
                    "SELECT COUNT(*) FROM literary_texts "
                    "WHERE COALESCE(source_url, '') <> ''"
                ).fetchone()[0]
            ),
            "source_groups": int(
                connection.execute(
                    "SELECT COUNT(DISTINCT source_file) FROM literary_texts"
                ).fetchone()[0]
            ),
        }
        records.append(
            _db_record(
                connection=connection,
                asset_id="db.literary_texts",
                label="Ingested literary corpus",
                table="literary_texts",
                text_column="text",
                origin_class="human_authored_source",
                data_boundary="public_or_external_source",
                coverage=literary_coverage,
                details=literary_details,
            )
        )
        for period, count in literary_coverage["periods"].items():
            metrics = text_metrics(
                connection,
                "SELECT text FROM literary_texts WHERE language_period = ?",
                (period,),
            )
            metrics["content_units"] = count
            records.append(
                make_record(
                    asset_id=f"view.literary_period.{period}",
                    label=f"Literary period overlap view: {period}",
                    asset_kind="source_collection",
                    origin_class="human_authored_source",
                    data_boundary="public_or_external_source",
                    lifecycle_states=("current", "ingested"),
                    measurement_scope="overlap_view",
                    metrics=metrics,
                    coverage={
                        **empty_coverage(),
                        "periods": {period: count},
                    },
                    raw_artifact_presence="unknown",
                    ingestion_status="ingested",
                    content_hash_status="not_measured",
                    provenance_status="partial",
                    rights_status="not_reconstructed",
                    eligibility_flags=eligibility(
                        excluded_pending_review=True,
                        provenance_investigation=True,
                    ),
                    evidence_refs=("sqlite:sources.db#literary_texts",),
                    limitations=("Overlap view; excluded from distinct totals.",),
                )
            )

        private_placeholders = _placeholders(len(PRIVATE_TEXTBOOK_SOURCES))
        public_where = f"source_file NOT IN ({private_placeholders})"
        private_where = f"source_file IN ({private_placeholders})"
        for asset_id, label, where, boundary, rights, private in (
            (
                "db.textbooks.public",
                "Ingested public/external textbook chunks",
                public_where,
                "public_or_external_source",
                "not_reconstructed",
                False,
            ),
            (
                "db.textbooks.private",
                "Ingested private curriculum reference chunks",
                private_where,
                "private_reference",
                "known_restrictions",
                True,
            ),
        ):
            coverage = empty_coverage()
            coverage["grades"] = count_map(
                connection,
                f"SELECT grade, COUNT(*) FROM textbooks WHERE {where} GROUP BY grade",
                PRIVATE_TEXTBOOK_SOURCES,
            )
            coverage["subjects"] = count_map(
                connection,
                f"SELECT subject, COUNT(*) FROM textbooks WHERE {where} GROUP BY subject",
                PRIVATE_TEXTBOOK_SOURCES,
            )
            record = _db_record(
                connection=connection,
                asset_id=asset_id,
                label=label,
                table="textbooks",
                text_column="text",
                origin_class="human_authored_source",
                data_boundary=boundary,
                where=where,
                parameters=PRIVATE_TEXTBOOK_SOURCES,
                coverage=coverage,
                rights_status=rights,
                details={"private_reference": private},
            )
            if private:
                record["eligibility"] = eligibility(
                    excluded_pending_review=True,
                    provenance_investigation=True,
                )
            records.append(record)

        external_coverage = empty_coverage()
        external_coverage["registers"] = count_map(
            connection,
            "SELECT register_tag, COUNT(*) FROM external_articles "
            "GROUP BY register_tag",
        )
        records.append(
            _db_record(
                connection=connection,
                asset_id="db.external_articles",
                label="External article and media transcripts",
                table="external_articles",
                text_column="text",
                origin_class="human_authored_source",
                data_boundary="public_or_external_source",
                coverage=external_coverage,
            )
        )
        records.append(
            _db_record(
                connection=connection,
                asset_id="db.wikipedia",
                label="Ukrainian Wikipedia snapshot chunks",
                table="wikipedia",
                text_column="text",
                origin_class="human_authored_source",
                data_boundary="public_or_external_source",
            )
        )
        wiki_coverage = empty_coverage()
        wiki_coverage["subjects"] = count_map(
            connection,
            "SELECT track, COUNT(*) FROM ukrainian_wiki GROUP BY track",
        )
        records.append(
            _db_record(
                connection=connection,
                asset_id="db.project_wiki",
                label="Project-generated Ukrainian wiki chunks",
                table="ukrainian_wiki",
                text_column="text",
                origin_class="unknown_origin",
                data_boundary="project_internal",
                coverage=wiki_coverage,
                details={
                    "reason_for_unknown_origin": (
                        "Per-article author/model lineage was not reconstructed."
                    )
                },
            )
        )

        for table, label, origin, raw_ref in DICTIONARY_COLLECTIONS:
            count = row_count(connection, table)
            records.append(
                make_record(
                    asset_id=f"lexicon.{table}",
                    label=label,
                    asset_kind="lexical_resource",
                    origin_class=origin,
                    data_boundary="public_or_external_source",
                    lifecycle_states=("current", "ingested"),
                    measurement_scope="distinct_content",
                    metrics={
                        "content_units": count,
                        "rows": count,
                        "unit_label": "lexical_rows",
                    },
                    coverage=empty_coverage(),
                    raw_artifact_presence="complete" if raw_ref else "unknown",
                    ingestion_status="ingested",
                    content_hash_status="not_measured",
                    provenance_status="partial",
                    rights_status="not_reconstructed",
                    eligibility_flags=eligibility(
                        excluded_pending_review=True,
                        internal_rag_reference=True,
                        provenance_investigation=True,
                        redistribution_investigation=True,
                    ),
                    evidence_refs=(f"sqlite:sources.db#{table}",),
                    limitations=(
                        "Counts are rows, not deduplicated lexemes or training tokens.",
                    ),
                    details={"raw_locator_present": bool(raw_ref)},
                )
            )

        ua_gec_count = row_count(connection, "ua_gec_errors")
        records.append(
            make_record(
                asset_id="eval.ua_gec_errors",
                label="UA-GEC error pairs",
                asset_kind="evaluation_collection",
                origin_class="human_authored_source",
                data_boundary="evaluation_only",
                lifecycle_states=("current", "ingested"),
                measurement_scope="distinct_content",
                metrics={
                    "content_units": ua_gec_count,
                    "rows": ua_gec_count,
                    "unit_label": "annotated_error_pairs",
                },
                coverage=empty_coverage(),
                raw_artifact_presence="complete",
                ingestion_status="ingested",
                content_hash_status="not_measured",
                provenance_status="partial",
                rights_status="evaluation_only",
                eligibility_flags=eligibility(
                    evaluation_only=True,
                    excluded_pending_review=True,
                ),
                evidence_refs=(
                    "sqlite:sources.db#ua_gec_errors",
                    "data/projects/ua_eval_harness/heldout_manifest_v1.json",
                ),
                limitations=("Evaluation boundary; not a training-admission record.",),
            )
        )
        zno_documents = row_count(connection, "zno_documents")
        zno_tasks = row_count(connection, "zno_tasks")
        records.append(
            make_record(
                asset_id="eval.zno_tasks",
                label="ZNO document and task bank",
                asset_kind="evaluation_collection",
                origin_class="human_authored_source",
                data_boundary="evaluation_only",
                lifecycle_states=("current", "ingested"),
                measurement_scope="distinct_content",
                metrics={
                    "content_units": zno_tasks,
                    "rows": zno_tasks,
                    "source_groups": zno_documents,
                    "unit_label": "exam_tasks",
                },
                coverage=empty_coverage(),
                raw_artifact_presence="partial",
                ingestion_status="ingested",
                content_hash_status="partial",
                provenance_status="partial",
                rights_status="evaluation_only",
                eligibility_flags=eligibility(
                    evaluation_only=True,
                    excluded_pending_review=True,
                ),
                evidence_refs=("sqlite:sources.db#zno_tasks",),
                limitations=("Evaluation boundary; not a training-admission record.",),
            )
        )

    with connect_read_only(vesum_database) as connection:
        forms = row_count(connection, "forms")
        lemmas = int(
            connection.execute("SELECT COUNT(DISTINCT lemma) FROM forms").fetchone()[0]
        )
        word_forms = int(
            connection.execute(
                "SELECT COUNT(DISTINCT word_form) FROM forms"
            ).fetchone()[0]
        )
    records.append(
        make_record(
            asset_id="lexicon.vesum",
            label="VESUM morphology database",
            asset_kind="lexical_resource",
            origin_class="human_authored_source",
            data_boundary="public_or_external_source",
            lifecycle_states=("current", "ingested"),
            measurement_scope="distinct_content",
            metrics={
                "content_units": forms,
                "rows": forms,
                "unit_label": "morphological_forms",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="unknown",
            ingestion_status="ingested",
            content_hash_status="not_measured",
            provenance_status="partial",
            rights_status="not_reconstructed",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                internal_rag_reference=True,
                provenance_investigation=True,
                redistribution_investigation=True,
            ),
            evidence_refs=("sqlite:vesum.db#forms",),
            limitations=("Form rows overlap by lemma and surface form.",),
            details={"distinct_lemmas": lemmas, "distinct_word_forms": word_forms},
        )
    )
    return records


def collect_repo_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    curriculum = repo_root / "curriculum/l2-uk-en"
    for track in CORE_TRACKS:
        modules = list((curriculum / track).glob("*/module.md"))
        records.append(
            make_record(
                asset_id=f"curriculum.core.{track}",
                label=f"Current {track.upper()} curriculum modules",
                asset_kind="curriculum_collection",
                origin_class="machine_generated_ukrainian",
                data_boundary="project_internal",
                lifecycle_states=("current",),
                measurement_scope="distinct_content",
                metrics=files_text_metrics(modules, "module_files"),
                coverage={**empty_coverage(), "grades": {track.upper(): len(modules)}},
                raw_artifact_presence="complete",
                ingestion_status="not_applicable",
                content_hash_status="not_measured",
                provenance_status="partial",
                rights_status="unknown",
                eligibility_flags=eligibility(
                    excluded_pending_review=True,
                    synthetic_research_only=True,
                ),
                evidence_refs=(f"curriculum/l2-uk-en/{track}/",),
                limitations=(
                    "Operator-classified AI-generated direct Ukrainian; per-module "
                    "generation lineage is incomplete.",
                ),
            )
        )

    folk_modules = list((curriculum / "folk").glob("*/module.md"))
    writer_models: Counter[str] = Counter()
    reviewer_families: Counter[str] = Counter()
    verdicts: Counter[str] = Counter()
    for sidecar in sorted((curriculum / "folk").glob("*/promote_quality.json")):
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        writer_models[str(payload.get("writer", {}).get("model", "unknown"))] += 1
        reviewer_families[str(payload.get("reviewer", {}).get("family", "unknown"))] += 1
        verdicts[str(payload.get("verdict", "unknown"))] += 1
    records.append(
        make_record(
            asset_id="curriculum.folk.current",
            label="Current FOLK curriculum modules",
            asset_kind="curriculum_collection",
            origin_class="machine_generated_ukrainian",
            data_boundary="project_internal",
            lifecycle_states=("current",),
            measurement_scope="distinct_content",
            metrics=files_text_metrics(folk_modules, "module_files"),
            coverage={**empty_coverage(), "genres": {"folk_curriculum": len(folk_modules)}},
            raw_artifact_presence="complete",
            ingestion_status="not_applicable",
            content_hash_status="recorded",
            provenance_status="partial",
            rights_status="unknown",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                synthetic_research_only=True,
            ),
            evidence_refs=("curriculum/l2-uk-en/folk/",),
            limitations=(
                "Automated promotion PASS conflicts with operator-reported unwanted "
                "AI bloat; treat as error/preference-analysis candidates only after "
                "human annotation.",
            ),
            details={
                "promotion_verdicts": dict(sorted(verdicts.items())),
                "reviewer_families": dict(sorted(reviewer_families.items())),
                "writer_models": dict(sorted(writer_models.items())),
            },
        )
    )

    bio_modules = list((curriculum / "bio").glob("*/module.md"))
    records.append(
        make_record(
            asset_id="curriculum.bio.current",
            label="Current experimental BIO curriculum modules",
            asset_kind="curriculum_collection",
            origin_class="unknown_origin",
            data_boundary="project_internal",
            lifecycle_states=("current",),
            measurement_scope="distinct_content",
            metrics=files_text_metrics(bio_modules, "module_files"),
            coverage=empty_coverage(),
            raw_artifact_presence="complete",
            ingestion_status="not_applicable",
            content_hash_status="not_measured",
            provenance_status="unresolved",
            rights_status="unknown",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                provenance_investigation=True,
            ),
            evidence_refs=("curriculum/l2-uk-en/bio/",),
            limitations=(
                "Writer/model lineage and the operator-reported unsatisfactory subset "
                "are unresolved.",
            ),
        )
    )

    pedagogy_path = (
        repo_root
        / "data/datasets/hramatka_uk_pedagogy_v1/hramatka_uk_pedagogy_v1.jsonl"
    )
    pedagogy_rows = [
        json.loads(line)
        for line in pedagogy_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records.append(
        make_record(
            asset_id="synthetic.hramatka_uk_pedagogy_v1",
            label="Hramatka Ukrainian pedagogy research rows",
            asset_kind="curriculum_collection",
            origin_class="machine_generated_ukrainian",
            data_boundary="private_reference",
            lifecycle_states=("current",),
            measurement_scope="metadata_only",
            metrics={
                "content_units": len(pedagogy_rows),
                "rows": len(pedagogy_rows),
                "unit_label": "research_rows",
            },
            coverage={**empty_coverage(), "grades": {"B1": len(pedagogy_rows)}},
            raw_artifact_presence="complete",
            ingestion_status="not_applicable",
            content_hash_status="not_measured",
            provenance_status="partial",
            rights_status="known_restrictions",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                synthetic_research_only=True,
            ),
            evidence_refs=(
                "data/datasets/hramatka_uk_pedagogy_v1/README.md",
                "docs/research/hramatka_literary_poltava_candidate_audit.md",
            ),
            limitations=(
                "Source rights, human revision, and reusable provenance are absent; "
                "README fine-tuning language is not an admission decision.",
            ),
            details={
                "model_seats": sorted({str(row.get("model_seat")) for row in pedagogy_rows}),
                "quality_tiers": sorted(
                    {str(row.get("quality_tier")) for row in pedagogy_rows}
                ),
            },
        )
    )

    heldout = json.loads(
        (repo_root / "data/projects/ua_eval_harness/heldout_manifest_v1.json").read_text(
            encoding="utf-8"
        )
    )
    eval_rows = sum(
        1
        for line in (
            repo_root / "data/projects/ua_eval_harness/evalset_v1.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    records.append(
        make_record(
            asset_id="eval.ua_gec_heldout_v1",
            label="UA-GEC held-out evaluation manifest",
            asset_kind="evaluation_collection",
            origin_class="human_authored_source",
            data_boundary="evaluation_only",
            lifecycle_states=("current",),
            measurement_scope="metadata_only",
            metrics={
                "content_units": int(heldout["counts"]["included_sentences"]),
                "rows": int(heldout["counts"]["included_sentences"]),
                "unit_label": "heldout_sentences",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="complete",
            ingestion_status="not_applicable",
            content_hash_status="recorded",
            provenance_status="complete",
            rights_status="evaluation_only",
            eligibility_flags=eligibility(
                evaluation_only=True,
                excluded_pending_review=True,
            ),
            evidence_refs=(
                "data/projects/ua_eval_harness/heldout_manifest_v1.json",
                "data/projects/ua_eval_harness/evalset_v1.jsonl",
            ),
            limitations=("Evaluation-only boundary; do not conflate manifest and evalset rows.",),
            details={"evalset_jsonl_rows": eval_rows},
        )
    )
    return records


def _run_git(repo_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def collect_git_records(repo_root: Path) -> list[dict[str, Any]]:
    tracked = _run_git(repo_root, "ls-files").splitlines()
    archive_counts = {
        "archive": sum(path.startswith("archive/") for path in tracked),
        "curriculum_archive": sum(
            path.startswith("curriculum/l2-uk-en/_archive/") for path in tracked
        ),
        "folk_archived_plans": sum(
            path.startswith("curriculum/l2-uk-en/plans/folk/_archive/")
            for path in tracked
        ),
    }
    weight_candidates = [
        path for path in tracked if path.lower().endswith(WEIGHT_SUFFIXES)
    ]
    records = [
        make_record(
            asset_id="git.tracked_archives",
            label="Tracked repository archive trees",
            asset_kind="archive_collection",
            origin_class="unknown_origin",
            data_boundary="project_internal",
            lifecycle_states=("archived_in_current_git",),
            measurement_scope="metadata_only",
            metrics={
                "files": sum(archive_counts.values()),
                "unit_label": "tracked_files",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="complete",
            ingestion_status="not_applicable",
            content_hash_status="recorded",
            provenance_status="partial",
            rights_status="unknown",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                provenance_investigation=True,
            ),
            evidence_refs=("git:HEAD#tracked-archive-paths",),
            limitations=("File inventory only; archive bodies are not emitted.",),
            details={
                "counts_by_tree": archive_counts,
                "model_weight_filename_candidates": len(weight_candidates),
            },
        )
    ]
    records.append(
        make_record(
            asset_id="git.folk_historical_modules",
            label="Deleted FOLK packages recoverable from Git history",
            asset_kind="recovery_candidate",
            origin_class="machine_generated_ukrainian",
            data_boundary="project_internal",
            lifecycle_states=("recoverable_from_git_history",),
            measurement_scope="metadata_only",
            metrics={
                "content_units": len(FOLK_RECOVERY_COMMITS),
                "unit_label": "module_versions",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="complete",
            ingestion_status="not_applicable",
            content_hash_status="recorded",
            provenance_status="partial",
            rights_status="unknown",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                provenance_investigation=True,
                synthetic_research_only=True,
            ),
            evidence_refs=tuple(f"git:{commit}" for commit in set(FOLK_RECOVERY_COMMITS.values())),
            limitations=("Recovery locator only; no historical files were restored.",),
            details={"module_commits": FOLK_RECOVERY_COMMITS},
        )
    )
    records.append(
        make_record(
            asset_id="git.folk_archived_plans_without_module_evidence",
            label="Archived FOLK plans without Git module evidence",
            asset_kind="recovery_candidate",
            origin_class="unknown_origin",
            data_boundary="project_internal",
            lifecycle_states=("planned_but_not_evidenced_as_built",),
            measurement_scope="metadata_only",
            metrics={
                "content_units": len(ARCHIVED_PLANS_WITHOUT_MODULE_EVIDENCE),
                "unit_label": "archived_plans",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="partial",
            ingestion_status="not_applicable",
            content_hash_status="recorded",
            provenance_status="unresolved",
            rights_status="unknown",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                provenance_investigation=True,
            ),
            evidence_refs=("curriculum/l2-uk-en/plans/folk/_archive/",),
            limitations=(
                "No module.md evidence was found in Git; this does not prove the "
                "modules never existed outside Git.",
            ),
            details={"plan_slugs": list(ARCHIVED_PLANS_WITHOUT_MODULE_EVIDENCE)},
        )
    )
    fsck = _run_git(repo_root, "fsck", "--full", "--no-reflogs", "--unreachable")
    unreachable = Counter()
    for line in fsck.splitlines():
        match = re.match(r"unreachable (blob|commit|tree) ", line)
        if match:
            unreachable[match.group(1)] += 1
    records.append(
        make_record(
            asset_id="git.unreachable_object_pool",
            label="Unreachable Git object pool",
            asset_kind="git_object_pool",
            origin_class="unknown_origin",
            data_boundary="unknown",
            lifecycle_states=("unknown_or_potentially_lost",),
            measurement_scope="metadata_only",
            metrics={
                "content_units": sum(unreachable.values()),
                "unit_label": "git_objects",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="complete",
            ingestion_status="not_applicable",
            content_hash_status="recorded",
            provenance_status="unresolved",
            rights_status="unknown",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                provenance_investigation=True,
            ),
            evidence_refs=("git:fsck--full--no-reflogs--unreachable",),
            limitations=(
                "All unreachable commits were path-screened separately; none contained "
                "scoped archive or curriculum paths. Do not garbage-collect repo-wide "
                "based on this inventory.",
            ),
            details={"counts_by_object_type": dict(sorted(unreachable.items()))},
        )
    )
    return records


def collect_drive_records(
    drive_root: Path,
    connection: sqlite3.Connection,
) -> list[dict[str, Any]]:
    literary_raw = _source_stems(drive_root / "literary_texts", "*.jsonl")
    literary_db = {
        Path(str(row[0])).stem
        for row in connection.execute("SELECT DISTINCT source_file FROM literary_texts")
    }
    textbook_raw = _source_stems(drive_root / "textbook_chunks", "**/*.jsonl")
    textbook_db = {
        Path(str(row[0])).stem
        for row in connection.execute("SELECT DISTINCT source_file FROM textbooks")
    }
    private_present = {
        source_id
        for source_id, relative in PRIVATE_RAW_PATHS.items()
        if (drive_root / relative).is_file()
    }
    public_chunk_db = textbook_db - set(PRIVATE_TEXTBOOK_SOURCES)
    db_only_public = sorted(public_chunk_db - textbook_raw)
    deferred = sorted(
        path.name
        for path in (drive_root / "textbooks/_deferred_scans").glob("*.pdf")
        if path.is_file()
    )
    topology = {
        name: sum(1 for path in (drive_root / name).rglob("*") if path.is_file())
        for name in (
            "alona-lessons",
            "corpus_audit",
            "datasets",
            "external_articles",
            "literary_texts",
            "native-reviewer-lessons",
            "private_curriculum",
            "processed",
            "projects",
            "raw",
            "references",
            "textbook_chunks",
            "textbook_images",
            "textbooks",
            "translations",
        )
        if (drive_root / name).exists()
    }
    return [
        make_record(
            asset_id="drive.raw_source_topology",
            label="Google Drive retained raw/source topology",
            asset_kind="raw_asset_collection",
            origin_class="unknown_origin",
            data_boundary="mixed",
            lifecycle_states=("raw_on_google_drive",),
            measurement_scope="metadata_only",
            metrics={
                "files": sum(topology.values()),
                "unit_label": "filesystem_entries",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="complete",
            ingestion_status="partially_ingested",
            content_hash_status="not_measured",
            provenance_status="unresolved",
            rights_status="unknown",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                provenance_investigation=True,
            ),
            evidence_refs=("gdrive:learn-ukrainian-data#top-level-file-census",),
            limitations=("Metadata census only; no Drive file bodies are emitted.",),
            details={"files_by_top_level_tree": topology},
        ),
        make_record(
            asset_id="drive.literary_raw_reconciliation",
            label="Literary JSONL to database reconciliation",
            asset_kind="raw_asset_collection",
            origin_class="human_authored_source",
            data_boundary="public_or_external_source",
            lifecycle_states=("raw_on_google_drive", "ingested"),
            measurement_scope="metadata_only",
            metrics={
                "content_units": len(literary_raw),
                "source_groups": len(literary_raw),
                "unit_label": "source_files",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="complete",
            ingestion_status="ingested",
            content_hash_status="not_measured",
            provenance_status="partial",
            rights_status="not_reconstructed",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                provenance_investigation=True,
                redistribution_investigation=True,
            ),
            evidence_refs=(
                "gdrive:learn-ukrainian-data/literary_texts",
                "sqlite:sources.db#literary_texts",
            ),
            limitations=(
                "Filename-stem reconciliation only; per-file JSONL line equality and "
                "content hashes were not measured.",
            ),
            details={
                "database_source_groups": len(literary_db),
                "database_only": sorted(literary_db - literary_raw),
                "raw_only": sorted(literary_raw - literary_db),
            },
        ),
        make_record(
            asset_id="drive.textbook_raw_reconciliation",
            label="Textbook PDFs/chunks to database reconciliation",
            asset_kind="raw_asset_collection",
            origin_class="human_authored_source",
            data_boundary="mixed",
            lifecycle_states=(
                "raw_on_google_drive",
                "ingested",
                "database_only_or_raw_source_unresolved",
            ),
            measurement_scope="metadata_only",
            metrics={
                "content_units": len(textbook_raw),
                "source_groups": len(textbook_raw),
                "unit_label": "chunk_source_files",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="partial",
            ingestion_status="partially_ingested",
            content_hash_status="not_measured",
            provenance_status="partial",
            rights_status="known_restrictions",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                provenance_investigation=True,
            ),
            evidence_refs=(
                "gdrive:learn-ukrainian-data/textbook_chunks",
                "gdrive:learn-ukrainian-data/private_curriculum",
                "sqlite:sources.db#textbooks",
            ),
            limitations=(
                "Per-file JSONL line equality and content hashes were not measured."
            ),
            details={
                "database_only_or_raw_chunk_unresolved": db_only_public,
                "database_source_groups": len(textbook_db),
                "private_raw_present": sorted(private_present),
                "raw_only": sorted(textbook_raw - public_chunk_db),
            },
        ),
        make_record(
            asset_id="drive.deferred_textbook_scans",
            label="Deferred textbook OCR scans",
            asset_kind="recovery_candidate",
            origin_class="human_authored_source",
            data_boundary="private_reference",
            lifecycle_states=("raw_but_uningested",),
            measurement_scope="metadata_only",
            metrics={
                "content_units": len(deferred),
                "files": len(deferred),
                "unit_label": "pdf_scans",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="complete",
            ingestion_status="not_ingested",
            content_hash_status="not_measured",
            provenance_status="partial",
            rights_status="known_restrictions",
            eligibility_flags=eligibility(excluded_pending_review=True),
            evidence_refs=("gdrive:learn-ukrainian-data/textbooks/_deferred_scans",),
            limitations=(
                "Zero scans meet the current OCR prerequisite; same-grade/subject "
                "alternatives are already ingested, so no OCR action is recommended."
            ),
            details={"files": deferred, "qualifying_for_ocr_now": 0},
        ),
        make_record(
            asset_id="drive.orphan_ocr",
            label="Orphan OCR text artifacts",
            asset_kind="recovery_candidate",
            origin_class="unknown_origin",
            data_boundary="unknown",
            lifecycle_states=("raw_but_uningested", "unknown_or_potentially_lost"),
            measurement_scope="metadata_only",
            metrics={
                "files": sum(
                    1
                    for path in (drive_root / "raw/orphan-ocr").glob("*")
                    if path.is_file()
                ),
                "unit_label": "orphan_text_files",
            },
            coverage=empty_coverage(),
            raw_artifact_presence="complete",
            ingestion_status="not_ingested",
            content_hash_status="not_measured",
            provenance_status="unresolved",
            rights_status="unknown",
            eligibility_flags=eligibility(
                excluded_pending_review=True,
                provenance_investigation=True,
            ),
            evidence_refs=("gdrive:learn-ukrainian-data/raw/orphan-ocr",),
            limitations=("Generic filenames do not establish source provenance.",),
        ),
    ]


def collect_kubedojo_record(kubedojo_root: Path) -> dict[str, Any]:
    modules = list((kubedojo_root / "src/content/docs/uk").rglob("*.md"))
    return make_record(
        asset_id="translation.kubedojo_uk",
        label="KubeDojo Ukrainian machine translations",
        asset_kind="translated_collection",
        origin_class="machine_translated_ukrainian",
        data_boundary="project_internal",
        lifecycle_states=("current",),
        measurement_scope="distinct_content",
        metrics=files_text_metrics(modules, "translated_markdown_files"),
        coverage=empty_coverage(),
        raw_artifact_presence="complete",
        ingestion_status="not_applicable",
        content_hash_status="partial",
        provenance_status="partial",
        rights_status="unknown",
        eligibility_flags=eligibility(
            excluded_pending_review=True,
            synthetic_research_only=True,
        ),
        evidence_refs=("external-repo:kubedojo/src/content/docs/uk",),
        limitations=(
            "Operator-classified machine translations; use for translationese/error "
            "analysis only. Divergence and review metadata are incomplete."
        ),
        details={
            "divergence_snapshot": {
                "covered_files": 514,
                "missing_en_commit": 0,
                "stale_files": 171,
            },
            "frontmatter_en_commit": 534,
            "frontmatter_en_file": 330,
            "files_without_en_commit": 20,
        },
    )


def aggregate_summary(
    records: Sequence[dict[str, Any]],
    *,
    schema_sha256: str,
    ledger_sha256: str,
    snapshot_date: str,
    repo_head: str,
) -> dict[str, Any]:
    by_origin = Counter(record["origin_class"] for record in records)
    by_boundary = Counter(record["data_boundary"] for record in records)
    for origin in ORIGIN_CLASSES:
        by_origin[origin] += 0
    for boundary in DATA_BOUNDARIES:
        by_boundary[boundary] += 0
    by_lifecycle = Counter(
        state for record in records for state in record["lifecycle_states"]
    )
    distinct = [record for record in records if record["measurement_scope"] == "distinct_content"]

    def metric_totals(group: Sequence[dict[str, Any]]) -> dict[str, Any]:
        numeric = ("characters", "lexical_words", "whitespace_tokens")
        totals: dict[str, Any] = {
            key: sum(int(record["metrics"].get(key, 0)) for record in group)
            for key in numeric
        }
        units: Counter[str] = Counter()
        for record in group:
            units[record["metrics"]["unit_label"]] += int(
                record["metrics"].get("content_units", 0)
            )
        totals["content_units_by_unit_label"] = dict(sorted(units.items()))
        return totals

    eligibility_views = {
        key: sorted(
            record["asset_id"]
            for record in records
            if record["eligibility"].get(key, False)
        )
        for key in ELIGIBILITY_KEYS
    }
    return {
        "counts": {
            "by_data_boundary": dict(sorted(by_boundary.items())),
            "by_lifecycle_state": dict(sorted(by_lifecycle.items())),
            "by_origin_class": dict(sorted(by_origin.items())),
            "ledger_records": len(records),
        },
        "distinct_content_totals": {
            "by_data_boundary": {
                boundary: metric_totals(
                    [record for record in distinct if record["data_boundary"] == boundary]
                )
                for boundary in sorted({record["data_boundary"] for record in distinct})
            },
            "by_origin_class": {
                origin: metric_totals(
                    [record for record in distinct if record["origin_class"] == origin]
                )
                for origin in sorted({record["origin_class"] for record in distinct})
            },
        },
        "eligibility_views": eligibility_views,
        "ledger_sha256": ledger_sha256,
        "measurement_contract": {
            "characters": "Python len() of stored Unicode strings.",
            "lexical_words": WORD_PATTERN,
            "model_token_counts": "not_run; tokenizer-specific measurement remains pending",
            "whitespace_tokens": "Python str.split(); proxy only, not model tokens.",
        },
        "repo_head": repo_head,
        "safety_assertions": {
            "potential_training_admission_assets": len(
                eligibility_views["potential_training_admission"]
            ),
            "redistribution_cleared_assets": 0,
            "source_record_v1_admissions": 0,
        },
        "schema_sha256": schema_sha256,
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "snapshot_date": snapshot_date,
    }


def load_fixture_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("fixture JSON must contain a list of ledger records")
    return payload


def write_inventory(
    records: Sequence[dict[str, Any]],
    output_dir: Path,
    schema: dict[str, Any],
    schema_sha256: str,
    snapshot_date: str,
    repo_head: str,
) -> tuple[Path, Path]:
    ordered = sorted(records, key=lambda record: record["asset_id"])
    validate_records(ordered, schema)
    ledger_bytes = ("\n".join(canonical_json(record) for record in ordered) + "\n").encode()
    ledger_sha256 = sha256_bytes(ledger_bytes)
    summary = aggregate_summary(
        ordered,
        schema_sha256=schema_sha256,
        ledger_sha256=ledger_sha256,
        snapshot_date=snapshot_date,
        repo_head=repo_head,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / LEDGER_NAME
    summary_path = output_dir / SUMMARY_NAME
    ledger_path.write_bytes(ledger_bytes)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ledger_path, summary_path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or fixture-check the existing Ukrainian asset inventory."
    )
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--snapshot-date", required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--vesum-database", type=Path)
    parser.add_argument("--drive-root", type=Path)
    parser.add_argument("--kubedojo-root", type=Path)
    parser.add_argument("--fixture-records", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    schema, schema_sha256 = load_schema(args.schema)
    repo_head = _run_git(args.repo_root, "rev-parse", "HEAD").strip()
    if args.fixture_records:
        records = load_fixture_records(args.fixture_records)
    else:
        required = {
            "--database": args.database,
            "--drive-root": args.drive_root,
            "--kubedojo-root": args.kubedojo_root,
            "--vesum-database": args.vesum_database,
        }
        missing = sorted(flag for flag, value in required.items() if value is None)
        if missing:
            raise ValueError("live mode requires " + ", ".join(missing))
        records = collect_database_records(args.database, args.vesum_database)
        records.extend(collect_repo_records(args.repo_root))
        records.extend(collect_git_records(args.repo_root))
        with connect_read_only(args.database) as connection:
            records.extend(collect_drive_records(args.drive_root, connection))
        records.append(collect_kubedojo_record(args.kubedojo_root))
    ledger_path, summary_path = write_inventory(
        records,
        args.output_dir,
        schema,
        schema_sha256,
        args.snapshot_date,
        repo_head,
    )
    print(f"wrote {len(records)} records to {ledger_path}")
    print(f"wrote summary to {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
