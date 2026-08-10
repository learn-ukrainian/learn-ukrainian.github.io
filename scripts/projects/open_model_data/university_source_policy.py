"""Fail-closed audience, content-disposition, and lane policy for university sources."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[3]
DEFAULT_POLICY_PATH = (
    PROJECT_ROOT
    / "data/projects/open_model_data/evidence/phase3_university_source_policy_v1.json"
)

SCHEMA_VERSION = "phase3_university_source_policy_v1"
V3_SCHEMA_VERSION = "phase3_university_source_policy_v3"
STATUS = "ACTIVE_DEFAULT_DENY"
DEFAULT_DISPOSITION = "QUARANTINE_UNTIL_AUDIENCE_PROVEN"
V3_DEFAULT_DISPOSITION = "QUARANTINE_UNTIL_AUDIENCE_AND_CONTENT_CLASSIFIED"
AUDIENCE_CLASSES = frozenset(
    {
        "A_ukrainian_university_audience",
        "B_foreign_or_second_language",
        "C_unproven",
    }
)
SUBJECT_ROLES = frozenset(
    {
        "ukrainian_linguistics",
        "ukrainian_L2_pedagogy",
        "ukrainian_literature",
        "history",
        "arts_and_culture",
    }
)
ALLOWED_LANES = frozenset(
    {
        "corpus_ingest",
        "contextual_retrieval",
        "linguistic_rule_evidence",
    }
)
CONTENT_DISPOSITIONS = frozenset(
    {
        "admit_candidate",
        "admitted",
        "contextual_only",
        "quarantine",
    }
)
TOP_LEVEL_KEYS = frozenset(
    {"schema_version", "status", "default_disposition", "source_count", "sources"}
)
SOURCE_KEYS = frozenset(
    {"source_file", "audience_class", "subject_role", "allowed_lanes", "evidence"}
)
V3_SOURCE_KEYS = SOURCE_KEYS | {"content_disposition"}
EVIDENCE_KEYS = frozenset(
    {"kind", "jsonl_sha256", "page_start", "page_end", "rows_sha256", "summary"}
)


class UniversitySourcePolicyError(RuntimeError):
    """Raised when university material lacks verified lane admission."""


def sha256_file(path: Path) -> str:
    """Return the SHA-256 of exact file bytes."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_value(value: Any) -> str:
    """Hash one JSON value using the repository's canonical JSON shape."""
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    """Load closed JSON-object rows without normalizing source text."""
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise UniversitySourcePolicyError(
                    f"university JSONL line {line_number} is not an object"
                )
            rows.append(value)
    if not rows:
        raise UniversitySourcePolicyError("university JSONL is empty")
    return rows


def evidence_rows_sha256(
    rows: list[dict[str, Any]],
    *,
    page_start: int,
    page_end: int,
) -> str:
    """Hash exact front-matter rows used to prove a source's audience."""
    selected: list[dict[str, Any]] = []
    for row in rows:
        row_start = row.get("page_start")
        row_end = row.get("page_end")
        if not isinstance(row_start, int) or not isinstance(row_end, int):
            continue
        if row_end < page_start or row_start > page_end:
            continue
        selected.append(
            {
                "chunk_id": row.get("chunk_id"),
                "page_start": row_start,
                "page_end": row_end,
                "text": row.get("text"),
            }
        )
    if not selected:
        raise UniversitySourcePolicyError(
            f"audience evidence pages {page_start}-{page_end} contain no JSONL rows"
        )
    return sha256_value(selected)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UniversitySourcePolicyError(message)


def load_policy(path: Path = DEFAULT_POLICY_PATH) -> tuple[dict[str, Any], str]:
    """Load and validate the closed, default-deny university policy."""
    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UniversitySourcePolicyError(f"cannot load university source policy: {path}") from exc
    _require(isinstance(document, dict), "university source policy must be an object")
    _require(set(document) == TOP_LEVEL_KEYS, "university source policy has an open or incomplete shape")
    schema_version = document["schema_version"]
    _require(
        schema_version in {SCHEMA_VERSION, V3_SCHEMA_VERSION},
        "unsupported university source policy schema",
    )
    _require(document["status"] == STATUS, "university source policy is not active")
    expected_default_disposition = (
        V3_DEFAULT_DISPOSITION
        if schema_version == V3_SCHEMA_VERSION
        else DEFAULT_DISPOSITION
    )
    _require(
        document["default_disposition"] == expected_default_disposition,
        "university source policy must use its schema's default quarantine disposition",
    )
    sources = document["sources"]
    _require(isinstance(sources, list), "university source policy sources must be a list")
    _require(document["source_count"] == len(sources), "university source policy count mismatch")
    source_files: list[str] = []
    for entry in sources:
        _require(isinstance(entry, dict), "university source policy entry must be an object")
        expected_source_keys = V3_SOURCE_KEYS if schema_version == V3_SCHEMA_VERSION else SOURCE_KEYS
        _require(
            set(entry) == expected_source_keys,
            "university source policy entry has an open shape",
        )
        source_file = entry["source_file"]
        audience = entry["audience_class"]
        subject_role = entry["subject_role"]
        lanes = entry["allowed_lanes"]
        evidence = entry["evidence"]
        _require(isinstance(source_file, str) and source_file.startswith("uni-"), "invalid university source_file")
        _require(audience in AUDIENCE_CLASSES, f"{source_file}: invalid audience class")
        _require(subject_role in SUBJECT_ROLES, f"{source_file}: invalid subject role")
        _require(
            isinstance(lanes, list)
            and lanes == sorted(set(lanes))
            and set(lanes) <= ALLOWED_LANES,
            f"{source_file}: invalid or non-canonical allowed lanes",
        )
        _require(isinstance(evidence, dict) and set(evidence) == EVIDENCE_KEYS, f"{source_file}: invalid evidence shape")
        _require(
            evidence["kind"]
            in {"jsonl_front_matter", "jsonl_front_matter_and_official_course"},
            f"{source_file}: unsupported evidence kind",
        )
        _require(
            isinstance(evidence["page_start"], int)
            and isinstance(evidence["page_end"], int)
            and 1 <= evidence["page_start"] <= evidence["page_end"],
            f"{source_file}: invalid evidence page range",
        )
        for key in ("jsonl_sha256", "rows_sha256"):
            _require(
                isinstance(evidence[key], str)
                and len(evidence[key]) == 64
                and all(character in "0123456789abcdef" for character in evidence[key]),
                f"{source_file}: invalid {key}",
            )
        _require(isinstance(evidence["summary"], str) and evidence["summary"].strip(), f"{source_file}: missing evidence summary")
        if schema_version == SCHEMA_VERSION:
            if audience == "A_ukrainian_university_audience":
                _require(
                    "corpus_ingest" in lanes,
                    f"{source_file}: admitted A source must permit corpus ingest",
                )
            else:
                _require(not lanes, f"{source_file}: B/C source cannot permit any production lane")
        else:
            content_disposition = entry["content_disposition"]
            _require(
                content_disposition in CONTENT_DISPOSITIONS,
                f"{source_file}: invalid content disposition",
            )
            if audience != "A_ukrainian_university_audience":
                _require(
                    content_disposition == "quarantine" and not lanes,
                    f"{source_file}: B/C source must remain quarantined with no production lane",
                )
            elif content_disposition == "quarantine":
                _require(
                    not lanes,
                    f"{source_file}: content-quarantined source cannot permit any production lane",
                )
            elif content_disposition == "contextual_only":
                _require(
                    lanes == ["contextual_retrieval", "corpus_ingest"],
                    f"{source_file}: contextual-only source must permit only contextual retrieval and corpus ingest",
                )
            elif content_disposition == "admit_candidate":
                _require(
                    lanes == ["contextual_retrieval"],
                    f"{source_file}: admit candidate cannot enter corpus or rule-authority lanes before admission",
                )
            else:
                _require(
                    "corpus_ingest" in lanes,
                    f"{source_file}: admitted source must permit corpus ingest",
                )
        if "linguistic_rule_evidence" in lanes:
            _require(
                audience == "A_ukrainian_university_audience"
                and subject_role == "ukrainian_linguistics",
                f"{source_file}: only proven Ukrainian linguistics sources may support rule evidence",
            )
            if schema_version == V3_SCHEMA_VERSION:
                _require(
                    entry["content_disposition"] == "admitted",
                    f"{source_file}: only content-admitted sources may support rule evidence",
                )
        source_files.append(source_file)
    _require(source_files == sorted(set(source_files)), "university policy source list must be unique and sorted")
    return document, sha256_file(path)


def require_source_admission(
    *,
    source_file: str,
    jsonl_path: Path,
    policy_path: Path = DEFAULT_POLICY_PATH,
    lane: str = "corpus_ingest",
) -> dict[str, Any]:
    """Return hash-bound admission metadata or fail before DB mutation."""
    _require(lane in ALLOWED_LANES, f"unsupported university source lane: {lane}")
    document, policy_sha256 = load_policy(policy_path)
    entry = next(
        (item for item in document["sources"] if item["source_file"] == source_file),
        None,
    )
    _require(
        entry is not None,
        f"{source_file}: no verified university source policy entry; default quarantine applies",
    )
    _require(
        lane in entry["allowed_lanes"],
        f"{source_file}: university source policy denies lane {lane}",
    )
    evidence = entry["evidence"]
    actual_jsonl_sha256 = sha256_file(jsonl_path)
    _require(
        actual_jsonl_sha256 == evidence["jsonl_sha256"],
        f"{source_file}: JSONL changed since audience evidence was reviewed",
    )
    rows = load_jsonl_rows(jsonl_path)
    actual_rows_sha256 = evidence_rows_sha256(
        rows,
        page_start=evidence["page_start"],
        page_end=evidence["page_end"],
    )
    _require(
        actual_rows_sha256 == evidence["rows_sha256"],
        f"{source_file}: front-matter audience evidence changed",
    )
    return {
        "audience_class": entry["audience_class"],
        "subject_role": entry["subject_role"],
        "content_disposition": entry.get("content_disposition", "legacy_audience_only"),
        "allowed_lanes": entry["allowed_lanes"],
        "policy_sha256": policy_sha256,
        "policy_entry_sha256": sha256_value(entry),
        "evidence_rows_sha256": actual_rows_sha256,
    }
