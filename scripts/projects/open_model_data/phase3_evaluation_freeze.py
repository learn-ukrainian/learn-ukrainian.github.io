#!/usr/bin/env python3
"""Build the label-blind all-family Phase 3 evaluation partition.

The steward consumes the single private source-unit materialization, freezes
evaluation membership before authoring, and writes only text-free private
indices plus a text-free public receipt.  It does not label Ukrainian gold,
author rules, score a release, or copy source text into another artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import sys
import tempfile
import unicodedata
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_fixed_release as fixed_release
from scripts.projects.open_model_data import phase3_functional_roles as roles
from scripts.projects.open_model_data import phase3_near_duplicate as near
from scripts.projects.open_model_data import phase3_source_unit_materialization as materializer

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
DEFAULT_ROLE_CONTRACT = DATA / "evidence/correction_protection_functional_role_contract_v2_1.json"
DEFAULT_EVALUATION_CONTRACT = DATA / "evidence/correction_protection_evaluation_contract_v1.json"
DEFAULT_SCHEMA = DATA / "contracts/phase3_evaluation_freeze_bundle_v1.schema.json"
IMPLEMENTATION_VERSION = "phase3_evaluation_freeze_v1"
SCHEMA_VERSION = "phase3_evaluation_partition_receipt_v1"
ROLE_ID = "heldout_steward"
TASK_ID = "phase3-v2-1-heldout-stewardship"
ACTION_KIND = "freeze_label_blind_all_family_evaluation_partition"
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
PUBLIC_FILE_MODE = 0o640  # group-readable; no world bits (CodeQL #352)
PARTITION_FILENAME = "partition_manifest_v1.jsonl"
CLEARANCE_FILENAME = "author_clearance_v1.jsonl"
QUARANTINE_FILENAME = "quarantine_v1.jsonl"
SEALED_INTERFACE_FILENAME = "sealed-evaluator-interface.json"
EVALUATION_INPUT_FILENAME = "evaluation-input-manifest.json"
SEALED_INTERFACE_RECEIPT_VERSION = "phase3_sealed_evaluator_interface_receipt_v1"
SEALED_INTERFACE_ACTION_KIND = "custody_heldout_bytes_locators_fingerprints"
FAMILIES = materializer.FAMILIES
TOTALS = {
    "antonenko_style_guide": 342,
    "ua_gec": 8937,
    "school_textbooks": 54979,
    "antonenko_textbook_representation": 169,
    "calque_inventory": 58,
    "pravopys_2019_complete": 1090,
    "pravopys_2026_complete": 1466,
    "other_normative_style_inventory": 0,
}
UA_GEC = "ua_gec"
SCHOOL = "school_textbooks"
ZERO_EVALUATION_FAMILIES = frozenset(
    {"antonenko_textbook_representation", "other_normative_style_inventory"}
)
PHENOMENA = (
    "direct_address_vocative",
    "impersonal_no_to_expressed_agent",
    "prepositional_government_valency",
    "pravopys_parallel_norms",
    "participial_versus_lexicalized_chyi",
    "numeral_agreement",
    "semantic_false_friends_interlanguage_homonyms",
    "lexical_interference",
    "phrase_collocation",
    "orthography",
    "punctuation",
    "syntactic_calque",
)


class EvaluationFreezeError(ValueError):
    """The evaluation partition cannot be frozen without leakage or drift."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationFreezeError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise EvaluationFreezeError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def _regular_private(path: Path, label: str) -> None:
    try:
        result = path.lstat()
    except OSError as exc:
        raise EvaluationFreezeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not path.is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} permissions must be 0600")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationFreezeError(f"cannot read {label}: {path}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _private_source_rows(path: Path, receipt: Mapping[str, Any]) -> list[dict[str, Any]]:
    _regular_private(path, "private source materialization")
    require(receipt.get("schema_version") == "phase3_source_unit_materialization_receipt_v1", "wrong materialization receipt")
    require(receipt.get("private_record_count") == 67041, "materialization denominator drift")
    require(receipt.get("private_jsonl_sha256") == sha256_file(path), "materialization payload hash drift")
    rows: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            digest.update(raw)
            require(raw.endswith(b"\n"), f"materialization row lacks LF: {line_number}")
            try:
                row = json.loads(raw.decode("utf-8", "strict"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise EvaluationFreezeError(f"invalid materialization row: {line_number}") from exc
            require(isinstance(row, dict), f"materialization row is not an object: {line_number}")
            require(
                set(row)
                == {
                    "family_id",
                    "unit_id",
                    "unit_sha256",
                    "frozen_locator",
                    "frozen_locator_sha256",
                    "document_or_edition_identity",
                    "source_text",
                    "source_record",
                    "source_text_sha256",
                },
                f"materialization row shape drift: {line_number}",
            )
            require(
                sha256_bytes(row["source_text"].encode("utf-8")) == row["source_text_sha256"],
                f"source text hash drift: {line_number}",
            )
            rows.append(row)
    require(digest.hexdigest() == receipt["private_jsonl_sha256"], "materialization stream hash drift")
    require(len(rows) == 67041, "materialization row count drift")
    counts = {family: sum(row["family_id"] == family for row in rows) for family in FAMILIES}
    require(counts == TOTALS == receipt.get("family_counts"), "materialization family counts drift")
    require(len({row["unit_id"] for row in rows}) == len(rows), "duplicate materialized unit id")
    return rows


def _load_exposed(path: Path) -> tuple[set[tuple[str, str]], str]:
    """Load private prior-exposure commitments without accepting labels or text."""
    _regular_private(path, "prior-exposure manifest")
    exposed: set[tuple[str, str]] = set()
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            try:
                row = json.loads(raw.decode("utf-8", "strict"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise EvaluationFreezeError(f"invalid prior-exposure row: {line_number}") from exc
            require(
                isinstance(row, dict) and set(row) == {"unit_id", "unit_sha256"},
                f"prior-exposure row shape drift: {line_number}",
            )
            pair = (row["unit_id"], row["unit_sha256"])
            require(all(isinstance(item, str) and item for item in pair), "prior-exposure identity drift")
            require(pair not in exposed, "duplicate prior-exposure identity")
            exposed.add(pair)
    return exposed, sha256_file(path)


def _load_external_exclusions(path: Path) -> tuple[dict[str, Any], str]:
    """Load UA Eval/public-canary records used only by the steward firewall."""
    _regular_private(path, "external exclusion interface")
    value = _read_json(path, "external exclusion interface")
    records = value.get("records")
    if records is None:
        records = [*value.get("frozen_ua_eval_records", []), *value.get("public_canary_records", [])]
    require(isinstance(records, list) and records, "external exclusion records missing")
    policy = near.policy_for_governed_use(
        "ua_eval_exclusion", expected_fingerprint=near.PINNED_POLICY_FINGERPRINT
    )
    documents: set[str] = set()
    units: set[tuple[str, str]] = set()
    exact: set[str] = set()
    surfaces: list[str] = []
    fingerprints: list[near.TextFingerprint] = []
    token_index: dict[str, list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        require(isinstance(record, Mapping), f"external exclusion record malformed: {index}")
        require(
            set(record) == {
                "source_document_identity",
                "unit_identity",
                "span_fingerprint",
                "normalized_surface",
            },
            f"external exclusion record shape drift: {index}",
        )
        document = record["source_document_identity"]
        unit = record["unit_identity"]
        surface = record["normalized_surface"]
        require(all(isinstance(item, str) and item for item in (document, unit, surface)), "external exclusion value drift")
        fingerprint = near.fingerprint(surface)
        require(fingerprint.exact_fingerprint == record["span_fingerprint"], "external exclusion fingerprint drift")
        documents.add(document)
        units.add((document, unit))
        exact.add(fingerprint.exact_fingerprint)
        surfaces.append(surface)
        fingerprints.append(fingerprint)
        for token in set(fingerprint.tokens):
            token_index[token].append(index)
    return {
        "documents": documents,
        "units": units,
        "exact": exact,
        "surfaces": surfaces,
        "fingerprints": fingerprints,
        "token_index": token_index,
        "policy": policy,
    }, sha256_file(path)


def _external_excluded(row: Mapping[str, Any], index: Mapping[str, Any]) -> bool:
    document = row["document_or_edition_identity"]
    unit_id = row["unit_id"]
    if document in index["documents"] or (document, unit_id) in index["units"]:
        return True
    try:
        probe = near.fingerprint(row["source_text"])
    except near.NearDuplicatePolicyError:
        return True
    if probe.exact_fingerprint in index["exact"]:
        return True
    tokens = set(probe.tokens)
    if not tokens:
        candidates: Iterable[int] = range(len(index["surfaces"]))
    else:
        shared: dict[int, int] = defaultdict(int)
        for token in tokens:
            for candidate in index["token_index"].get(token, ()):
                shared[candidate] += 1
        required = max(1, math.ceil(0.9 * len(tokens)))
        candidates = (candidate for candidate, count in shared.items() if count >= required)
    return any(
        near.duplicate_or_fail_closed(
            row["source_text"], index["surfaces"][candidate], scope="span", policy=index["policy"]
        )
        for candidate in candidates
    )


def _surface_index(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Index sealed surfaces for an exhaustive 0.90-threshold candidate search."""
    fingerprints: list[near.TextFingerprint] = []
    surfaces: list[str] = []
    exact: set[str] = set()
    token_index: dict[str, list[int]] = defaultdict(list)
    token_sets: list[frozenset[str]] = []
    policy = near.policy_for_governed_use(
        "train_development_to_heldout_firewall",
        expected_fingerprint=near.PINNED_POLICY_FINGERPRINT,
    )
    for index, row in enumerate(rows):
        fingerprint = near.fingerprint(row["source_text"])
        fingerprints.append(fingerprint)
        surfaces.append(row["source_text"])
        exact.add(fingerprint.exact_fingerprint)
        tokens = frozenset(fingerprint.tokens)
        token_sets.append(tokens)
        for token in tokens:
            token_index[token].append(index)
    return {
        "fingerprints": fingerprints,
        "surfaces": surfaces,
        "exact": exact,
        "token_index": token_index,
        "token_sets": token_sets,
        "policy": policy,
    }


def _heldout_neighbour(row: Mapping[str, Any], index: Mapping[str, Any]) -> bool:
    """Detect exact/near heldout neighbours without a quadratic all-pairs scan."""
    try:
        probe = near.fingerprint(row["source_text"])
    except near.NearDuplicatePolicyError:
        return True
    if probe.exact_fingerprint in index["exact"]:
        return True
    tokens = frozenset(probe.tokens)
    if not tokens:
        candidates: set[int] = {
            candidate for candidate, item in enumerate(index["token_sets"]) if not item
        }
    else:
        required = math.ceil(0.9 * len(tokens))
        # Any set sharing at least ``required`` probe tokens must contain at
        # least one member of this smallest-posting hitting set.
        hitting_size = len(tokens) - required + 1
        hitting_tokens = sorted(
            tokens, key=lambda token: (len(index["token_index"].get(token, ())), token)
        )[:hitting_size]
        candidates = {
            candidate
            for token in hitting_tokens
            for candidate in index["token_index"].get(token, ())
        }
    for candidate in candidates:
        candidate_tokens = index["token_sets"][candidate]
        union = len(tokens | candidate_tokens)
        jaccard = 1.0 if union == 0 else len(tokens & candidate_tokens) / union
        if jaccard < 0.9:
            continue
        if near.duplicate_or_fail_closed(
            row["source_text"],
            index["surfaces"][candidate],
            scope="span",
            policy=index["policy"],
        ):
            return True
    return False


def _rank(seed: str, row: Mapping[str, Any]) -> bytes:
    return hashlib.sha256(
        seed.encode("utf-8")
        + b"\0"
        + row["unit_id"].encode("utf-8")
        + b"\0"
        + row["unit_sha256"].encode("ascii")
    ).digest()


def _document_rank(seed: str, document: str, members: Sequence[Mapping[str, Any]]) -> bytes:
    commitment = sha256_value(sorted((row["unit_id"], row["unit_sha256"]) for row in members))
    return hashlib.sha256(seed.encode("utf-8") + b"\0" + document.encode("utf-8") + b"\0" + commitment.encode("ascii")).digest()


def _structural_clean_candidate(text: str) -> bool:
    value = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    if not 160 <= len(value) <= 1600 or len(value.split()) < 20:
        return False
    nonspace = [char for char in value if not char.isspace()]
    if not nonspace or sum(char.isalpha() for char in nonspace) * 100 < len(nonspace) * 60:
        return False
    return sum(value.count(mark) for mark in (".", "!", "?", "…")) >= 2


def _school_membership(rows: Sequence[Mapping[str, Any]], cycle: str) -> set[str]:
    limit = math.floor(len(rows) * 0.20)
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["document_or_edition_identity"]].append(row)
    require(len(grouped) >= 3, "school document identity breadth missing")
    selected: set[str] = set()
    for _document, members in sorted(
        grouped.items(), key=lambda item: _document_rank(f"{cycle}:school-document-v1", item[0], item[1])
    ):
        if len(selected) + len(members) <= limit:
            selected.update(row["unit_id"] for row in members)
    require(selected and len(selected) <= limit, "school evaluation share selection failed")
    return selected


def _ua_test_membership(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    by_document: dict[str, set[str]] = defaultdict(set)
    selected: set[str] = set()
    for row in rows:
        record = row["source_record"]
        require(isinstance(record, Mapping), "UA-GEC source record missing")
        partition = record.get("partition")
        require(isinstance(partition, str) and "/" in partition, "UA-GEC partition malformed")
        split = partition.rsplit("/", 1)[1]
        require(split in {"train", "test"}, "UA-GEC split malformed")
        by_document[row["document_or_edition_identity"]].add(split)
        if split == "test":
            selected.add(row["unit_id"])
    require(all(splits != {"train", "test"} for splits in by_document.values()), "UA-GEC document spans train and test")
    require(len(selected) <= math.floor(len(rows) * 0.20), "UA-GEC sealed share exceeds 20 percent")
    return selected


def _unit_membership(rows: Sequence[Mapping[str, Any]], cycle: str, family: str) -> set[str]:
    if family in ZERO_EVALUATION_FAMILIES:
        return set()
    limit = math.floor(len(rows) * 0.20)
    ordered = sorted(rows, key=lambda row: _rank(f"{cycle}:{family}:unit-v1", row))
    return {row["unit_id"] for row in ordered[:limit]}


def partition(
    rows: Sequence[Mapping[str, Any]],
    *,
    cycle: str,
    exposed: set[tuple[str, str]],
    external_index: Mapping[str, Any],
) -> dict[str, Any]:
    by_family: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[row["family_id"]].append(row)
    raw_selected: set[str] = set()
    for family in FAMILIES:
        family_rows = by_family[family]
        if family == UA_GEC:
            raw_selected.update(_ua_test_membership(family_rows))
        elif family == SCHOOL:
            raw_selected.update(_school_membership(family_rows, cycle))
        else:
            raw_selected.update(_unit_membership(family_rows, cycle, family))

    partition_rows: list[dict[str, Any]] = []
    clearance_rows: list[dict[str, Any]] = []
    quarantine_rows: list[dict[str, Any]] = []
    selected_rows: list[Mapping[str, Any]] = []
    author_candidates: list[Mapping[str, Any]] = []
    for row in rows:
        identity = (row["unit_id"], row["unit_sha256"])
        external = _external_excluded(row, external_index)
        if identity in exposed:
            quarantine_rows.append(_text_free_row(row, reason="prior_exposure"))
        elif external:
            quarantine_rows.append(_text_free_row(row, reason="ua_eval_or_public_canary_overlap"))
        elif row["unit_id"] in raw_selected:
            selected_rows.append(row)
        else:
            author_candidates.append(row)

    heldout_index = _surface_index(selected_rows)
    for row in author_candidates:
        if _heldout_neighbour(row, heldout_index):
            quarantine_rows.append(_text_free_row(row, reason="heldout_exact_or_near_neighbour"))
        else:
            clearance_rows.append(_text_free_row(row, reason="author_cleared"))

    clean_eligible = [
        row for row in selected_rows if row["family_id"] == SCHOOL and _structural_clean_candidate(row["source_text"])
    ]
    grouped_clean: dict[str, deque[Mapping[str, Any]]] = {}
    for document in sorted({row["document_or_edition_identity"] for row in clean_eligible}):
        members = [row for row in clean_eligible if row["document_or_edition_identity"] == document]
        grouped_clean[document] = deque(sorted(members, key=lambda row: _rank(f"{cycle}:clean-unit-v1", row)))
    document_order = sorted(grouped_clean, key=lambda document: sha256_value([cycle, "clean-document-v1", document]))
    queues = deque(grouped_clean[document] for document in document_order)
    clean_ids: set[str] = set()
    while queues and len(clean_ids) < 2000:
        queue = queues.popleft()
        clean_ids.add(queue.popleft()["unit_id"])
        if queue:
            queues.append(queue)
    require(len(clean_ids) == 2000, "clean-modern candidate universe is smaller than 2,000")
    for row in selected_rows:
        partition_rows.append(
            {
                **_text_free_row(row, reason="evaluation_only"),
                "candidate_lane": "clean_modern" if row["unit_id"] in clean_ids else "phenomenon_strata",
                "source_text_sha256": row["source_text_sha256"],
                "frozen_locator_sha256": row["frozen_locator_sha256"],
            }
        )

    partition_rows.sort(key=lambda row: (row["family_id"], row["unit_id"]))
    clearance_rows.sort(key=lambda row: (row["family_id"], row["unit_id"]))
    quarantine_rows.sort(key=lambda row: (row["family_id"], row["unit_id"]))
    all_ids = {row["unit_id"] for row in partition_rows + clearance_rows + quarantine_rows}
    require(len(all_ids) == 67041, "partition accounting is not exact")
    require(len(partition_rows) + len(clearance_rows) + len(quarantine_rows) == 67041, "partition sets overlap")
    family_counts = {
        family: {
            "family_total": TOTALS[family],
            "sealed_evaluation": sum(row["family_id"] == family for row in partition_rows),
            "author_cleared": sum(row["family_id"] == family for row in clearance_rows),
            "quarantined": sum(row["family_id"] == family for row in quarantine_rows),
        }
        for family in FAMILIES
    }
    for family, counts in family_counts.items():
        require(sum(value for key, value in counts.items() if key != "family_total") == counts["family_total"], f"family accounting drift: {family}")
        require(counts["sealed_evaluation"] <= math.floor(counts["family_total"] * 0.20), f"sealed share exceeds 20 percent: {family}")
    return {
        "partition_rows": partition_rows,
        "clearance_rows": clearance_rows,
        "quarantine_rows": quarantine_rows,
        "family_counts": family_counts,
        "clean_candidate_count": len(clean_ids),
    }


def _text_free_row(row: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
    return {
        "family_id": row["family_id"],
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "reason": reason,
    }


def _jsonl(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(canonical_bytes(row) for row in rows)


def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
    """Atomically write *payload* with private-by-default permissions.

    Private evaluation artifacts must not be group/world readable. Public
    receipts use :func:`_atomic_write_public` instead so CodeQL can see the
    intentional world-read bit only on the non-secret path.
    """
    if mode & 0o077:
        raise ValueError(f"private write refuses group/other bits: {mode:04o}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _atomic_write_public(path: Path, payload: bytes) -> None:
    """Write a non-secret public receipt (world-readable by design)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), PUBLIC_FILE_MODE)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, PUBLIC_FILE_MODE)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _prepare_private_dir(path: Path) -> None:
    require(not path.is_symlink(), "private evaluation directory may not be a symlink")
    path.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    os.chmod(path, PRIVATE_DIR_MODE)
    require(stat.S_IMODE(path.stat().st_mode) == PRIVATE_DIR_MODE, "private evaluation directory must be 0700")
    allowed = {
        PARTITION_FILENAME,
        CLEARANCE_FILENAME,
        QUARANTINE_FILENAME,
        SEALED_INTERFACE_FILENAME,
        EVALUATION_INPUT_FILENAME,
    }
    for child in path.iterdir():
        require(child.name in allowed and child.is_file() and not child.is_symlink(), "unexpected private evaluation artifact")


def _role_binding(role_contract: Mapping[str, Any]) -> dict[str, str]:
    try:
        roles.verify_value(role_contract)
        binding = roles.binding_for_role(role_contract, ROLE_ID)
    except roles.FunctionalRoleError as exc:
        raise EvaluationFreezeError(str(exc)) from exc
    require(binding == {"role_id": ROLE_ID, "task_id": TASK_ID}, "heldout steward binding drift")
    return binding


def _action_receipt(
    *,
    role_contract: Mapping[str, Any],
    role_contract_path: Path,
    input_sha256: str,
    output_sha256: str,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    binding = _role_binding(role_contract)
    steward = next(item for item in role_contract["functional_roles"] if item["role_id"] == ROLE_ID)
    identity = {
        **binding,
        "input_manifest_sha256": input_sha256,
        "evaluation_cycle_id": role_contract["evaluation_cycle"]["evaluation_cycle_id"],
        "output_sha256": output_sha256,
        "status": "completed",
    }
    receipt = {
        "receipt_id": "phase3_functional_action:" + sha256_bytes(canonical_json(identity).encode("utf-8")),
        **binding,
        "action_kind": ACTION_KIND,
        "provider": "local",
        "exact_model": steward["exact_model"],
        "model_family": steward["model_family"],
        "harness": steward["harness"],
        "input_manifest_sha256": input_sha256,
        "output_sha256": output_sha256,
        "evaluation_cycle_id": role_contract["evaluation_cycle"]["evaluation_cycle_id"],
        "base_contract_sha256": roles.BASE_SHA256,
        "amendment_sha256": roles.AMENDMENT_SHA256,
        "combined_contract_sha256": roles.COMBINED_SHA256,
        "functional_role_contract_sha256": sha256_file(role_contract_path),
        "conflict_graph_sha256": roles.conflict_graph_sha256(role_contract),
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "completed",
    }
    require(set(receipt) == set(roles.ACTION_RECEIPT_FIELDS), "steward action receipt shape drift")
    return receipt


def build(
    *,
    source_jsonl: Path,
    materialization_receipt_path: Path,
    prior_exposure_manifest: Path,
    external_exclusion_interface: Path,
    private_dir: Path,
    public_receipt_path: Path,
    role_contract_path: Path,
    evaluation_contract_path: Path,
    schema_path: Path,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    materialization_receipt = _read_json(materialization_receipt_path, "materialization receipt")
    rows = _private_source_rows(source_jsonl, materialization_receipt)
    exposed, exposed_sha256 = _load_exposed(prior_exposure_manifest)
    external, external_sha256 = _load_external_exclusions(external_exclusion_interface)
    role_contract = _read_json(role_contract_path, "functional role contract")
    evaluation_contract = _read_json(evaluation_contract_path, "evaluation contract")
    binding = _role_binding(role_contract)
    cycle = role_contract["evaluation_cycle"]["evaluation_cycle_id"]
    require(
        evaluation_contract["functional_role_evaluation_cycle"]["evaluation_cycle_id"] == cycle,
        "evaluation-cycle binding drift",
    )
    result = partition(rows, cycle=cycle, exposed=exposed, external_index=external)
    partition_payload = _jsonl(result["partition_rows"])
    clearance_payload = _jsonl(result["clearance_rows"])
    quarantine_payload = _jsonl(result["quarantine_rows"])
    input_bindings = {
        "source_materialization_receipt_sha256": sha256_file(materialization_receipt_path),
        "source_materialization_jsonl_sha256": sha256_file(source_jsonl),
        "source_universe_receipt_sha256": materialization_receipt["source_universe_receipt_sha256"],
        "prior_exposure_manifest_sha256": exposed_sha256,
        "prior_exposure_count": len(exposed),
        "external_exclusion_interface_sha256": external_sha256,
        "near_duplicate_policy_fingerprint_sha256": near.PINNED_POLICY_FINGERPRINT,
        "functional_role_contract_sha256": sha256_file(role_contract_path),
        "conflict_graph_sha256": roles.conflict_graph_sha256(role_contract),
        "evaluation_contract_sha256": sha256_file(evaluation_contract_path),
        "base_contract_sha256": roles.BASE_SHA256,
        "amendment_sha256": roles.AMENDMENT_SHA256,
        "combined_contract_sha256": roles.COMBINED_SHA256,
        "evaluation_cycle_id": cycle,
    }
    output = {
        "partition_manifest_sha256": sha256_bytes(partition_payload),
        "author_clearance_sha256": sha256_bytes(clearance_payload),
        "quarantine_sha256": sha256_bytes(quarantine_payload),
        "family_counts": result["family_counts"],
        "clean_candidate_count": result["clean_candidate_count"],
    }
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "implementation_version": IMPLEMENTATION_VERSION,
        "role_binding": binding,
        "input_bindings": input_bindings,
        "artifact_hashes": {
            "partition_manifest_sha256": output["partition_manifest_sha256"],
            "author_clearance_sha256": output["author_clearance_sha256"],
            "quarantine_sha256": output["quarantine_sha256"],
        },
        "family_counts": output["family_counts"],
        "aggregates": {
            "input_total": 67041,
            "sealed_evaluation_total": len(result["partition_rows"]),
            "author_cleared_total": len(result["clearance_rows"]),
            "quarantined_total": len(result["quarantine_rows"]),
            "clean_modern_candidate_total": result["clean_candidate_count"],
        },
        "gates": {
            "all_eight_family_partitions_accounted": True,
            "sealed_share_at_most_0_20_every_family": True,
            "partition_frozen_before_author_transport": True,
            "prior_exposures_excluded": True,
            "ua_eval_and_public_canary_overlap_excluded": True,
            "source_bytes_copied_into_partition_artifacts": False,
            "labels_present": False,
            "production_transport_enabled": False,
        },
    }
    receipt["action_receipt"] = _action_receipt(
        role_contract=role_contract,
        role_contract_path=role_contract_path,
        input_sha256=sha256_value(input_bindings),
        output_sha256=sha256_value(output),
        started_at=started_at,
        completed_at=completed_at,
    )
    receipt["receipt_sha256"] = sha256_value(receipt)
    schema = _read_json(schema_path, "evaluation freeze schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    require(not errors, f"evaluation freeze schema violation: {errors[0].message if errors else ''}")
    serialized = canonical_json(receipt)
    require(
        not any(token in serialized for token in ("source_text", "source_record", "unit_id", "document_or_edition_identity", "frozen_locator")),
        "public evaluation receipt leaks source or heldout identity",
    )
    _prepare_private_dir(private_dir)
    _atomic_write(private_dir / PARTITION_FILENAME, partition_payload, PRIVATE_FILE_MODE)
    _atomic_write(private_dir / CLEARANCE_FILENAME, clearance_payload, PRIVATE_FILE_MODE)
    _atomic_write(private_dir / QUARANTINE_FILENAME, quarantine_payload, PRIVATE_FILE_MODE)
    _atomic_write_public(public_receipt_path, canonical_bytes(receipt))
    return receipt


def _read_private_json_list(path: Path, label: str) -> list[dict[str, Any]]:
    _regular_private(path, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationFreezeError(f"cannot read {label}: {path}") from exc
    require(isinstance(value, list) and all(isinstance(row, dict) for row in value), f"{label} must be a JSON list of objects")
    return value


def _private_partition_rows(path: Path, freeze_receipt: Mapping[str, Any]) -> list[dict[str, Any]]:
    _regular_private(path, "private partition manifest")
    require(
        freeze_receipt.get("artifact_hashes", {}).get("partition_manifest_sha256") == sha256_file(path),
        "private partition hash drift",
    )
    rows: list[dict[str, Any]] = []
    try:
        for number, raw in enumerate(path.read_bytes().splitlines(), start=1):
            row = json.loads(raw.decode("utf-8"))
            require(isinstance(row, dict), f"private partition row {number} must be an object")
            require(
                set(row) == {"family_id", "unit_id", "unit_sha256", "reason", "candidate_lane", "source_text_sha256", "frozen_locator_sha256"},
                "private partition row shape drift",
            )
            rows.append(row)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvaluationFreezeError(f"cannot read private partition manifest: {path}") from exc
    require(len(rows) == 9392 and len({row["unit_id"] for row in rows}) == 9392, "sealed partition denominator drift")
    return rows


def _comprehensive_label_bundle(
    path: Path,
    *,
    sealed_labels_path: Path,
    partition_path: Path,
    evaluation_freeze_receipt_path: Path,
) -> dict[str, Any]:
    """Verify the explicit 9,392-row label closure; 2,000-only labels are unsafe."""

    bundle = _read_json(path, "comprehensive sealed-label bundle")
    required = {
        "schema_version", "text_free", "evaluation_cycle_id", "evaluation_freeze_receipt_sha256",
        "partition_manifest_sha256", "sealed_labels_sha256", "row_count", "clean_modern_row_count",
        "phenomenon_strata_row_count", "phenomenon_stratum_commitments", "complete",
        "frozen_before_rule_extraction", "receipt_sha256",
    }
    require(set(bundle) == required, "comprehensive sealed-label bundle is not closed")
    require(bundle["schema_version"] == "phase3_comprehensive_sealed_label_bundle_v1" and bundle["text_free"] is True, "wrong comprehensive sealed-label bundle")
    require(bundle["evaluation_cycle_id"] == "phase3-v2-1-evaluation-cycle-001", "sealed-label cycle drift")
    require(bundle["evaluation_freeze_receipt_sha256"] == sha256_file(evaluation_freeze_receipt_path), "sealed-label freeze receipt drift")
    require(bundle["partition_manifest_sha256"] == sha256_file(partition_path), "sealed-label partition drift")
    require(bundle["sealed_labels_sha256"] == sha256_file(sealed_labels_path), "sealed-label payload drift")
    require(
        bundle["row_count"] == 9392
        and bundle["clean_modern_row_count"] == 2000
        and bundle["phenomenon_strata_row_count"] == 7392,
        "comprehensive labels must cover 2,000 clean_modern plus 7,392 phenomenon strata",
    )
    commitments = bundle["phenomenon_stratum_commitments"]
    require(isinstance(commitments, Mapping) and set(commitments) == set(PHENOMENA), "phenomenon stratum commitments are incomplete")
    require(all(isinstance(value, str) and len(value) == 64 for value in commitments.values()), "invalid phenomenon stratum commitment")
    require(bundle["complete"] is True and bundle["frozen_before_rule_extraction"] is True, "sealed labels were not closed before extraction")
    body = dict(bundle)
    claimed = body.pop("receipt_sha256")
    require(claimed == sha256_value(body), "comprehensive sealed-label receipt hash drift")
    return bundle


def _sealed_interface_rows(
    *,
    labels: Sequence[Mapping[str, Any]],
    partition_rows: Sequence[Mapping[str, Any]],
    materialized_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    partition_by_id = {row["unit_id"]: row for row in partition_rows}
    materialized_by_id = {row["unit_id"]: row for row in materialized_rows}
    require(len(materialized_by_id) == 67041, "private materialization denominator drift")
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    lane_counts = {"clean_modern": 0, "phenomenon_strata": 0}
    for label in labels:
        require(isinstance(label.get("unit_id"), str) and isinstance(label.get("unit_sha256"), str), "sealed label identity is missing")
        unit_id = label["unit_id"]
        partition = partition_by_id.get(unit_id)
        source = materialized_by_id.get(unit_id)
        require(unit_id not in seen and partition is not None and source is not None, "sealed label is not an exact partition/materialization member")
        seen.add(unit_id)
        require(label["unit_sha256"] == partition["unit_sha256"] == source["unit_sha256"], "sealed label unit hash drift")
        require(source["family_id"] == partition["family_id"] and source["source_text_sha256"] == partition["source_text_sha256"], "sealed label source binding drift")
        lane = partition["candidate_lane"]
        require(lane in lane_counts, "only frozen evaluation lanes may enter the scorer interface")
        lane_counts[lane] += 1
        label_payload = dict(label)
        label_payload.pop("unit_id")
        label_payload.pop("unit_sha256")
        require("source_text" not in label_payload and "source_record" not in label_payload, "sealed label payload duplicates source bytes")
        output.append(
            {
                "unit_id": unit_id,
                "unit_sha256": source["unit_sha256"],
                "family_id": source["family_id"],
                "document_or_edition_identity": source["document_or_edition_identity"],
                "source_text": source["source_text"],
                "source_text_sha256": source["source_text_sha256"],
                "candidate_lane": lane,
                "label": label_payload,
            }
        )
    require(seen == set(partition_by_id), "sealed labels do not exactly cover the frozen evaluation partition")
    require(lane_counts == {"clean_modern": 2000, "phenomenon_strata": 7392}, "sealed interface lane denominator drift")
    return sorted(output, key=lambda row: row["unit_id"])


def emit_sealed_interface(
    *,
    release_manifest_path: Path,
    comprehensive_sealed_label_bundle_path: Path,
    sealed_labels_path: Path,
    partition_path: Path,
    source_jsonl: Path,
    materialization_receipt_path: Path,
    evaluation_freeze_receipt_path: Path,
    private_dir: Path,
    public_receipt_path: Path,
    role_contract_path: Path = DEFAULT_ROLE_CONTRACT,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    """Open the scorer-only interface only after the release and all labels seal.

    This fails closed for the historical 2,000-row clean_modern label lane:
    scorer input requires all 9,392 frozen evaluation identities.
    """

    manifest = fixed_release.validate_manifest(release_manifest_path)
    freeze_receipt = _read_json(evaluation_freeze_receipt_path, "evaluation freeze receipt")
    require(
        manifest["input_hashes"]["evaluation_freeze_receipt_sha256"] == sha256_file(evaluation_freeze_receipt_path),
        "fixed release is not bound to this evaluation freeze",
    )
    labels_bundle = _comprehensive_label_bundle(
        comprehensive_sealed_label_bundle_path,
        sealed_labels_path=sealed_labels_path,
        partition_path=partition_path,
        evaluation_freeze_receipt_path=evaluation_freeze_receipt_path,
    )
    labels = _read_private_json_list(sealed_labels_path, "comprehensive sealed labels")
    require(len(labels) == 9392, "2,000-only sealed labels cannot open the scorer interface")
    materialization_receipt = _read_json(materialization_receipt_path, "materialization receipt")
    materialized_rows = _private_source_rows(source_jsonl, materialization_receipt)
    partition_rows = _private_partition_rows(partition_path, freeze_receipt)
    rows = _sealed_interface_rows(labels=labels, partition_rows=partition_rows, materialized_rows=materialized_rows)
    role_contract = _read_json(role_contract_path, "functional role contract")
    binding = _role_binding(role_contract)
    interface: dict[str, Any] = {
        "schema_version": "phase3_sealed_evaluator_interface_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-001",
        "release_manifest_sha256": manifest["manifest_sha256"],
        "fixed_release_sha256": manifest["artifact_hashes"]["fixed-release-rules.jsonl"],
        "heldout_evaluation_freeze_sha256": sha256_file(comprehensive_sealed_label_bundle_path),
        "denominator_contract_sha256": manifest["artifact_hashes"]["denominator-contract.json"],
        "threshold_contract_sha256": manifest["artifact_hashes"]["threshold-contract.json"],
        "row_count": 9392,
        "lane_counts": {"clean_modern": 2000, "phenomenon_strata": 7392},
        "phenomenon_stratum_commitments": dict(labels_bundle["phenomenon_stratum_commitments"]),
        "rows": rows,
    }
    interface["interface_manifest_sha256"] = sha256_value(interface)
    _prepare_private_dir(private_dir)
    interface_path = private_dir / SEALED_INTERFACE_FILENAME
    _atomic_write(interface_path, canonical_bytes(interface), PRIVATE_FILE_MODE)
    evaluation_input = {
        "schema_version": "phase3_evaluation_input_manifest_v1",
        "evaluation_cycle_id": interface["evaluation_cycle_id"],
        "fixed_release_task_id": fixed_release.TASK_ID,
        "fixed_release_sha256": interface["fixed_release_sha256"],
        "heldout_evaluation_freeze_sha256": interface["heldout_evaluation_freeze_sha256"],
        "denominator_contract_sha256": interface["denominator_contract_sha256"],
        "threshold_contract_sha256": interface["threshold_contract_sha256"],
        "published_inputs_manifest_sha256": manifest["artifact_hashes"]["published-inputs-manifest.json"],
        "sealed_evaluator_interface_sha256": sha256_file(interface_path),
        "release_instructions_sha256": manifest["artifact_hashes"]["release-instructions.json"],
        "ukrainian_recipe_sha256": manifest["artifact_hashes"]["ukrainian-recipe.json"],
        "english_recipe_sha256": manifest["artifact_hashes"]["english-recipe.json"],
        "release_mutation_allowed": False,
        "threshold_mutation_allowed": False,
        "heldout_plaintext_exposed": False,
    }
    _atomic_write(private_dir / EVALUATION_INPUT_FILENAME, canonical_bytes(evaluation_input), PRIVATE_FILE_MODE)
    output = {
        "sealed_evaluator_interface_sha256": evaluation_input["sealed_evaluator_interface_sha256"],
        "evaluation_input_manifest_sha256": sha256_value(evaluation_input),
        "row_count": 9392,
    }
    receipt = {
        "schema_version": SEALED_INTERFACE_RECEIPT_VERSION,
        "text_free": True,
        "role_binding": binding,
        "release_manifest_sha256": manifest["manifest_sha256"],
        "evaluation_freeze_receipt_sha256": sha256_file(evaluation_freeze_receipt_path),
        "comprehensive_sealed_label_bundle_sha256": sha256_file(comprehensive_sealed_label_bundle_path),
        "output": output,
        "gates": {"fixed_release_validated_first": True, "complete_partition_labels_required": True, "heldout_plaintext_exported": False, "outsider_receives_freeze_container": False},
    }
    receipt["action_receipt"] = _action_receipt(
        role_contract=role_contract,
        role_contract_path=role_contract_path,
        input_sha256=sha256_value({"release_manifest_sha256": manifest["manifest_sha256"], "labels_bundle_sha256": sha256_file(comprehensive_sealed_label_bundle_path)}),
        output_sha256=sha256_value(output),
        started_at=started_at,
        completed_at=completed_at,
    )
    receipt["action_receipt"]["action_kind"] = SEALED_INTERFACE_ACTION_KIND
    receipt["receipt_sha256"] = sha256_value(receipt)
    _atomic_write_public(public_receipt_path, canonical_bytes(receipt))
    return {"interface": interface, "evaluation_input": evaluation_input, "receipt": receipt}


def main(argv: Sequence[str] | None = None) -> int:
    cli_argv = list(sys.argv[1:] if argv is None else argv)
    if cli_argv and cli_argv[0] == "emit-sealed-interface":
        parser = argparse.ArgumentParser(description="Emit the scorer-only sealed interface after release freeze.")
        parser.add_argument("--release-manifest", type=Path, required=True)
        parser.add_argument("--comprehensive-sealed-label-bundle", type=Path, required=True)
        parser.add_argument("--sealed-labels", type=Path, required=True)
        parser.add_argument("--partition", type=Path, required=True)
        parser.add_argument("--source-jsonl", type=Path, required=True)
        parser.add_argument("--materialization-receipt", type=Path, required=True)
        parser.add_argument("--evaluation-freeze-receipt", type=Path, required=True)
        parser.add_argument("--private-dir", type=Path, required=True)
        parser.add_argument("--public-receipt", type=Path, required=True)
        parser.add_argument("--role-contract", type=Path, default=DEFAULT_ROLE_CONTRACT)
        parser.add_argument("--started-at", required=True)
        parser.add_argument("--completed-at", required=True)
        args = parser.parse_args(cli_argv[1:])
        try:
            result = emit_sealed_interface(
                release_manifest_path=args.release_manifest,
                comprehensive_sealed_label_bundle_path=args.comprehensive_sealed_label_bundle,
                sealed_labels_path=args.sealed_labels,
                partition_path=args.partition,
                source_jsonl=args.source_jsonl,
                materialization_receipt_path=args.materialization_receipt,
                evaluation_freeze_receipt_path=args.evaluation_freeze_receipt,
                private_dir=args.private_dir,
                public_receipt_path=args.public_receipt,
                role_contract_path=args.role_contract,
                started_at=args.started_at,
                completed_at=args.completed_at,
            )
        except EvaluationFreezeError as exc:
            parser.error(str(exc))
        sys.stdout.write(canonical_json({"ok": True, "receipt_sha256": result["receipt"]["receipt_sha256"]}) + "\n")
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-jsonl", type=Path, required=True)
    parser.add_argument("--materialization-receipt", type=Path, required=True)
    parser.add_argument("--prior-exposure-manifest", type=Path, required=True)
    parser.add_argument("--external-exclusion-interface", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--public-receipt", type=Path, required=True)
    parser.add_argument("--role-contract", type=Path, default=DEFAULT_ROLE_CONTRACT)
    parser.add_argument("--evaluation-contract", type=Path, default=DEFAULT_EVALUATION_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--completed-at", required=True)
    args = parser.parse_args(cli_argv)
    try:
        receipt = build(
            source_jsonl=args.source_jsonl,
            materialization_receipt_path=args.materialization_receipt,
            prior_exposure_manifest=args.prior_exposure_manifest,
            external_exclusion_interface=args.external_exclusion_interface,
            private_dir=args.private_dir,
            public_receipt_path=args.public_receipt,
            role_contract_path=args.role_contract,
            evaluation_contract_path=args.evaluation_contract,
            schema_path=args.schema,
            started_at=args.started_at,
            completed_at=args.completed_at,
        )
    except EvaluationFreezeError as exc:
        parser.error(str(exc))
    sys.stdout.write(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
