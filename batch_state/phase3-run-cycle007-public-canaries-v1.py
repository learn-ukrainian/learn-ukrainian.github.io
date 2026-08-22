#!/usr/bin/env python3
"""Run public Cycle-007 Gemini and Grok canaries with source-grounded evidence.

Validates model compliance against the frozen Cycle-007 amendment using
dedicated public synthetic clean-label fixtures:
- Trap: "слідуючий раз"
- Heritage control: "філіжанка"

Supports real provider liveness challenges and explicit synthetic modes.
Permits one structural retry; semantic failure is terminal.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator

HERE = Path(__file__).resolve().parent
CYCLE = "phase3-v2-1-evaluation-cycle-007"
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
DOMAIN = "phase3-cycle007-public-canary-v1"

GEMINI_MODEL = "Gemini 3.6 Flash (High)"
GEMINI_FAMILY = "google"
GEMINI_HARNESS = "agy"
AGY = Path("/Users/krisztiankoos/.local/bin/agy")
GEMINI_SCHEMA_VERSION = "phase3_cycle007_gemini_public_canary_receipt_v1"

GROK_MODEL = "grok-4.5"
GROK_FAMILY = "xai"
GROK_HARNESS = "native_grok"
GROK = Path("/Users/krisztiankoos/.local/bin/grok")
GROK_SCHEMA_VERSION = "phase3_cycle007_grok_public_canary_receipt_v1"

SOURCE_VALIDATOR = HERE / "phase3-cycle007-label-validation-v1.py"


def _load_validator() -> Any:
    source_path = SOURCE_VALIDATOR
    if not source_path.is_file() or source_path.is_symlink():
        raise RuntimeError("Cycle-007 semantic validator unavailable")
    spec = importlib.util.spec_from_file_location("cycle007_public_semantic_validator", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cycle-007 semantic validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = _load_validator()


class CanaryError(ValueError):
    """Base error for canary execution."""

    def __init__(self, code: str, *, structural: bool = False) -> None:
        self.code = code
        self.structural = structural
        super().__init__(code)


class CanaryStructuralError(CanaryError):
    """Structural error eligible for one retry."""

    def __init__(self, code: str) -> None:
        super().__init__(code, structural=True)


class CanarySemanticError(CanaryError):
    """Semantic assertion or invariant failure (terminal; no retry)."""

    def __init__(self, code: str) -> None:
        super().__init__(code, structural=False)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanaryStructuralError("duplicate_json_key")
        result[key] = value
    return result


def _mode(path: Path, expected: int) -> None:
    if not path.exists() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) != expected:
        raise CanaryError("invalid_file_mode")


def _atomic(path: Path, value: Any, *, raw: bool = False) -> str:
    data = value if raw else canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    if path.exists() or path.is_symlink():
        _mode(path, 0o600)
        if path.read_bytes() != data:
            raise CanaryError("receipt_state_drift")
        return digest(data)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return digest(data)


def fixture_rows() -> list[dict[str, Any]]:
    """Return the exact 2-row dedicated clean-label public canary fixture."""
    return [
        {
            "unit_id": f"{DOMAIN}-trap",
            "unit_sha256": digest(f"{DOMAIN}:trap:слідуючий раз".encode()),
            "source_text": "слідуючий раз",
            "family_id": DOMAIN,
        },
        {
            "unit_id": f"{DOMAIN}-control",
            "unit_sha256": digest(f"{DOMAIN}:control:філіжанка".encode()),
            "source_text": "філіжанка",
            "family_id": DOMAIN,
        },
    ]


GEMINI_CANARY_PROMPT = """# Phase 3 Cycle 007 public Gemini canary review

This is a public synthetic clean-label canary in domain `phase3-cycle007-public-canary-v1`.
Return only the schema-constrained result for the ordinal public rows appended below.
Preserve every `unit_id` and `unit_sha256` exactly.

For each row:
- `agree` requires `clean_modern_standard_prose: true`, a valid `modern_genre_id`, and sufficient cited evidence IDs.
- every reject requires `clean_modern_standard_prose: false`, `modern_genre_id: null`, and cited evidence IDs.

Ukrainian sources and the evidence sidecar are authoritative over model memory.
Cite sorted, unique `evidence_ids` from the row's compiled evidence sidecar.
"""

GROK_CANARY_PROMPT = """# Phase 3 Cycle 007 public Grok canary review

This is a public synthetic clean-label canary in domain `phase3-cycle007-public-canary-v1`.
Return only the schema-constrained JSON result with top-level key `labels` containing the 2 public rows appended below.
Preserve every `unit_id` and `unit_sha256` exactly.

For each row:
- `agree` requires `clean_modern_standard_prose: true`, a valid `modern_genre_id`, and sufficient cited evidence IDs.
- every reject requires `clean_modern_standard_prose: false`, `modern_genre_id: null`, and cited evidence IDs.

Ukrainian sources and the evidence sidecar are authoritative over model memory.
Cite sorted, unique `evidence_ids` from the row's compiled evidence sidecar.
"""


def compile_public_sidecar(
    client: compiler.LocalMcpSourcesClient | compiler.SourcesClient,
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compile and validate an immutable public evidence sidecar."""
    if rows is None:
        rows = fixture_rows()
    sidecar = compiler.compile_packet_sidecar(1, rows, client, residual_lane=False)
    identity = client.server_identity()
    expected_identity = {
        "tokenizer_id": compiler.TOKENIZER_ID,
        "tokenizer_version": compiler.TOKENIZER_VERSION,
        "code_hashes": compiler.CODE_HASHES,
        "server_code_sha256": identity["server_code_sha256"],
        "sources_db_sha256": identity["sources_db_sha256"],
        "vesum_db_sha256": identity["vesum_db_sha256"],
    }
    validator.validate_sidecar(sidecar, expected_identity=expected_identity)
    return sidecar


def gemini_schema(rows: list[dict[str, Any]], challenge: str) -> dict[str, Any]:
    """Generate Gemini JSON schema requiring liveness_challenge."""
    def label_for(row: dict[str, Any]) -> dict[str, Any]:
        identity = {"unit_id": {"enum": [row["unit_id"]]}, "unit_sha256": {"enum": [row["unit_sha256"]]}}
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "unit_id",
                "unit_sha256",
                "decision_code",
                "clean_modern_standard_prose",
                "modern_genre_id",
                "evidence_ids",
            ],
            "properties": identity
            | {
                "decision_code": {"enum": sorted(SOURCE.REJECTS)},
                "clean_modern_standard_prose": {"type": "boolean"},
                "modern_genre_id": {"anyOf": [{"enum": sorted(SOURCE.GENRES)}, {"type": "null"}]},
                "evidence_ids": {"type": "array", "items": {"type": "string"}},
            },
        }

    properties = {f"p{position:02d}": label_for(row) for position, row in enumerate(rows, 1)}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["labels_by_position", "liveness_challenge"],
        "properties": {
            "labels_by_position": {
                "type": "object",
                "additionalProperties": False,
                "required": list(properties),
                "properties": properties,
            },
            "liveness_challenge": {"enum": [challenge]},
        },
    }


def gemini_prompt(challenge: str, rows: list[dict[str, Any]], sidecar: dict[str, Any]) -> bytes:
    return (
        GEMINI_CANARY_PROMPT.strip()
        + f"\n\nEcho this exact liveness challenge in liveness_challenge: {challenge}\n"
        + "\n--- BEGIN IMMUTABLE PUBLIC PACKET JSON ---\n"
        + json.dumps({"rows": rows}, ensure_ascii=False, indent=2)
        + "\n--- END IMMUTABLE PUBLIC PACKET JSON ---\n"
        + "\n--- BEGIN IMMUTABLE EVIDENCE SIDECAR JSON ---\n"
        + json.dumps(sidecar, ensure_ascii=False, indent=2)
        + "\n--- END IMMUTABLE EVIDENCE SIDECAR JSON ---\n"
    ).encode("utf-8")


def grok_prompt(challenge: str, rows: list[dict[str, Any]], sidecar: dict[str, Any]) -> bytes:
    return (
        GROK_CANARY_PROMPT.strip()
        + f"\n\nEcho this exact liveness challenge in liveness_challenge: {challenge}\n"
        + "\n--- BEGIN IMMUTABLE PUBLIC PACKET JSON ---\n"
        + json.dumps({"rows": rows}, ensure_ascii=False, indent=2)
        + "\n--- END IMMUTABLE PUBLIC PACKET JSON ---\n"
        + "\n--- BEGIN IMMUTABLE EVIDENCE SIDECAR JSON ---\n"
        + json.dumps(sidecar, ensure_ascii=False, indent=2)
        + "\n--- END IMMUTABLE EVIDENCE SIDECAR JSON ---\n"
    ).encode("utf-8")


def _agy_stream(raw: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        events = [
            json.loads(line, object_pairs_hook=_pairs)
            for line in raw.decode("utf-8", "strict").splitlines()
            if line.strip()
        ]
    except (UnicodeDecodeError, json.JSONDecodeError, CanaryError) as exc:
        raise CanaryStructuralError("stream_json_invalid") from exc
    if not events:
        raise CanaryStructuralError("stream_json_invalid")
    init_events = [event for event in events if isinstance(event, dict) and event.get("event") == "init"]
    result_events = [event for event in events if isinstance(event, dict) and event.get("event") == "result"]
    if len(init_events) != 1 or len(result_events) != 1:
        raise CanaryStructuralError("terminal_result_count_drift")
    if events[0] is not init_events[0] or events[-1] is not result_events[0]:
        raise CanaryStructuralError("terminal_result_count_drift")
    init, result_event = init_events[0], result_events[0]
    config, result = init.get("init"), result_event.get("result")
    if not isinstance(config, dict) or config.get("model") != GEMINI_MODEL:
        raise CanaryStructuralError("structured_output_envelope_drift")
    if not isinstance(result, dict) or result.get("status") != "SUCCESS" or "structured_output" not in result:
        raise CanaryStructuralError("structured_output_envelope_drift")
    return init, result


def _extract_gemini(raw: bytes, challenge: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    init, result = _agy_stream(raw)
    output = result["structured_output"]
    if isinstance(output, str):
        try:
            output = json.loads(output, object_pairs_hook=_pairs)
        except (json.JSONDecodeError, CanaryError) as exc:
            raise CanaryStructuralError("label_json_invalid") from exc
    if not isinstance(output, dict):
        raise CanaryStructuralError("structured_output_envelope_drift")
    if set(output) != {"labels_by_position", "liveness_challenge"} or output.get("liveness_challenge") != challenge:
        raise CanaryStructuralError("structured_output_envelope_drift")
    positions = output["labels_by_position"]
    if not isinstance(positions, dict) or set(positions) != {"p01", "p02"}:
        raise CanaryStructuralError("ordinal_key_drift")
    labels = [positions["p01"], positions["p02"]]
    return init, result, {"labels": labels}


def _extract_grok(raw: bytes, challenge: str) -> dict[str, Any]:
    try:
        direct = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, CanaryError) as exc:
        raise CanaryStructuralError("stream_json_invalid") from exc
    if (
        not isinstance(direct, dict)
        or set(direct) != {"labels", "liveness_challenge"}
        or direct.get("liveness_challenge") != challenge
        or not isinstance(direct.get("labels"), list)
    ):
        raise CanaryStructuralError("structured_output_envelope_drift")
    return {"labels": direct["labels"]}


def verify_semantic_canary_assertions(
    sidecar: Mapping[str, Any],
    normalized_labels: Sequence[Mapping[str, Any]],
) -> tuple[bool, bool]:
    """Verify semantic assertions over validated labels against the sidecar.

    Assertions:
    1. Trap row:
       - rejected with cited attested Antonenko style guidance plus cited Russian-shadow suspicion.
       - suspicion alone is never sufficient.
    2. Heritage control row:
       - labeled agree with both cited sufficient heritage and VESUM evidence.
       - has no attested Antonenko warning or Russian-shadow suspicion.
    """
    if len(normalized_labels) != 2:
        raise CanarySemanticError("expected_two_labels")
    trap_label, control_label = normalized_labels[0], normalized_labels[1]
    trap_ev_row = sidecar["rows"][0]
    control_ev_row = sidecar["rows"][1]

    # 1. Trap verification
    if trap_label["decision_code"] == "agree" or trap_label["clean_modern_standard_prose"] is True:
        raise CanarySemanticError("trap_not_rejected")
    if trap_label["decision_code"] not in SOURCE.REJECTS:
        raise CanarySemanticError("invalid_trap_decision_code")

    trap_cited_ids = set(trap_label.get("evidence_ids", []))
    trap_evidence_by_id = {str(rec["evidence_id"]): rec for rec in trap_ev_row.get("evidence", [])}

    has_antonenko_style = False
    has_russian_shadow = False
    for eid in trap_cited_ids:
        rec = trap_evidence_by_id.get(eid)
        if rec is None:
            raise CanarySemanticError("foreign_evidence_id_in_trap")
        if rec.get("channel") == "antonenko_style" and rec.get("status") == "attested":
            has_antonenko_style = True
        if rec.get("channel") == "russian_shadow_suspicion" and rec.get("status") == "attested":
            has_russian_shadow = True

    if not has_antonenko_style and has_russian_shadow:
        raise CanarySemanticError("russian_shadow_suspicion_alone_insufficient")
    if not (has_antonenko_style and has_russian_shadow):
        raise CanarySemanticError("trap_missing_required_antonenko_or_shadow_evidence")

    # 2. Heritage control verification
    if control_label["decision_code"] != "agree" or control_label["clean_modern_standard_prose"] is not True:
        raise CanarySemanticError("heritage_control_not_agreed")
    if control_label.get("modern_genre_id") not in SOURCE.GENRES:
        raise CanarySemanticError("heritage_control_missing_genre")

    control_cited_ids = set(control_label.get("evidence_ids", []))
    control_evidence_by_id = {str(rec["evidence_id"]): rec for rec in control_ev_row.get("evidence", [])}

    has_sufficient_heritage = False
    has_sufficient_vesum = False
    for eid in control_cited_ids:
        rec = control_evidence_by_id.get(eid)
        if rec is None:
            raise CanarySemanticError("foreign_evidence_id_in_control")
        if rec.get("status") == "attested" and rec.get("supports") in contract.SUFFICIENT_SUPPORTS:
            if rec.get("channel") == "heritage_attestation":
                has_sufficient_heritage = True
            if rec.get("channel") == "vesum_attestation":
                has_sufficient_vesum = True

    if not (has_sufficient_heritage and has_sufficient_vesum):
        raise CanarySemanticError("heritage_control_missing_vesum_or_heritage_evidence")
    if any(
        rec.get("channel") in {"antonenko_style", "russian_shadow_suspicion"}
        and rec.get("status") == "attested"
        for rec in control_ev_row.get("evidence", [])
    ):
        raise CanarySemanticError("heritage_control_has_style_or_shadow_warning")

    return True, True


def build_receipt(
    provider_name: str,
    *,
    execution_mode: str,
    provider_calls: int,
    rows: list[dict[str, Any]],
    sidecar: dict[str, Any],
    prompt_bytes: bytes,
    exe_sha256: str,
    raw_response: bytes,
    normalized_labels: list[dict[str, Any]],
    sources_identity: Mapping[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Build exact text-free canary receipt matching per-provider schema."""
    if provider_name == "gemini":
        schema_version = GEMINI_SCHEMA_VERSION
        model = GEMINI_MODEL
        family = GEMINI_FAMILY
        harness = GEMINI_HARNESS
        response_hashes = {
            "raw_stream_sha256": digest(raw_response),
            "labels_raw_sha256": digest(canonical({"labels": normalized_labels})),
        }
    elif provider_name == "grok":
        schema_version = GROK_SCHEMA_VERSION
        model = GROK_MODEL
        family = GROK_FAMILY
        harness = GROK_HARNESS
        response_hashes = {
            "response_raw_sha256": digest(raw_response),
            "labels_raw_sha256": digest(canonical({"labels": normalized_labels})),
        }
    else:
        raise CanaryError("unknown_provider")

    value: dict[str, Any] = {
        "schema_version": schema_version,
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "ok": True,
        "execution_mode": execution_mode,
        "exact_model": model,
        "model_family": family,
        "harness": harness,
        "provider_call_count": provider_calls,
        "fixture_hashes": {
            "fixture_raw_sha256": digest(canonical(rows)),
            "row_count": len(rows),
            "identity_set_sha256": digest(canonical(sorted((r["unit_id"], r["unit_sha256"]) for r in rows))),
        },
        "sidecar_hashes": {
            "sidecar_id": sidecar["sidecar_id"],
            "sidecar_raw_sha256": digest(canonical(sidecar)),
        },
        "prompt_hashes": {
            "prompt_sha256": digest(prompt_bytes),
        },
        "code_hashes": {
            "compiler_sha256": compiler.COMPILER_MODULE_SHA256,
            "validator_sha256": contract.sha256_file(SOURCE_VALIDATOR),
            "canary_runner_sha256": contract.sha256_file(Path(__file__)),
        },
        "executable_sha256": exe_sha256,
        "response_hashes": response_hashes,
        "sources_endpoint_identity": {
            "server_code_sha256": str(sources_identity["server_code_sha256"]),
            "sources_db_sha256": str(sources_identity["sources_db_sha256"]),
            "sources_db_bytes": int(sources_identity["sources_db_bytes"]),
            "vesum_db_sha256": str(sources_identity["vesum_db_sha256"]),
            "vesum_db_bytes": int(sources_identity["vesum_db_bytes"]),
        },
        "sources_mcp_used": True,
        "valid_evidence_ids": True,
        "russian_surzhyk_trap_rejected": True,
        "heritage_control_preserved": True,
        "provenance_basis": provenance,
        "text_free": True,
    }
    value["receipt_sha256"] = digest(canonical(value))
    return value


def make_synthetic_mcp_client(tmp_path: Path) -> compiler.LocalMcpSourcesClient:
    """Create a synthetic in-memory Sources MCP double for tests."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    sources_db = tmp_path / "sources.db"
    vesum_db = tmp_path / "vesum.db"
    server_code = tmp_path / "server.py"
    sources_db.write_bytes(b"synthetic_sources_db")
    vesum_db.write_bytes(b"synthetic_vesum_db")
    server_code.write_bytes(b"synthetic_server_code")
    files = {"sources_db": sources_db, "vesum_db": vesum_db, "server_code": server_code}

    def verify_words_fn(args: Mapping[str, Any]) -> str:
        words = args.get("words", [])
        lines = [f"Batch verification: {len(words)} words", ""]
        found_count = 0
        body_lines = []
        for w in words:
            if w in ("раз", "філіжанка"):
                body_lines.append(f"- **{w}** — FOUND (1 match): {w}(noun)")
                found_count += 1
            else:
                body_lines.append(f"- **{w}** — NOT FOUND")
        lines.append(f"Found: {found_count}/{len(words)}")
        lines.extend(body_lines)
        return "\n".join(lines)

    def check_modern_form_fn(args: Mapping[str, Any]) -> str:
        w = args.get("word")
        if w in ("раз", "філіжанка"):
            return json.dumps({"is_modern_codified": True, "has_archaic_form": False, "has_only_archaic_form": False})
        return json.dumps({"is_modern_codified": False, "has_archaic_form": False, "has_only_archaic_form": False})

    def search_style_guide_fn(args: Mapping[str, Any]) -> str:
        q = str(args.get("query", ""))
        if "слідуючий" in q:
            return f'Found 1 results in **Антоненко-Давидович** for: "{q}"\n### Result 1\n- **Entry**: слідуючий'
        return f'No results in Антоненко-Давидович for: "{q}"'

    def search_text_fn(args: Mapping[str, Any]) -> str:
        q = str(args.get("query", ""))
        if "слідуючий" in q:
            return f'Found 1 results for: "{q}"\n### Result 1\n- **Text**: слідуючий раз'
        return "No results found."

    def search_heritage_fn(args: Mapping[str, Any]) -> str:
        q = str(args.get("query", ""))
        if "філіжанка" in q:
            return f'Found 1 heritage evidence row(s) for: "{q}"\n### Evidence 1\n- **Headword**: філіжанка'
        return f'No heritage evidence found for: "{q}"'

    def check_russian_shadow_fn(args: Mapping[str, Any]) -> str:
        w = args.get("word")
        if w == "слідуючий":
            return json.dumps({"matches_russian": True, "russian_lemma": "следующий", "confidence": 1.0})
        return json.dumps({"matches_russian": False, "russian_lemma": None, "confidence": 0.0})

    responses = {
        "mcp_server_identity": json.dumps(
            {
                "server_code_sha256": contract.sha256_file(server_code),
                "sources_db_sha256": contract.sha256_file(sources_db),
                "sources_db_bytes": sources_db.stat().st_size,
                "vesum_db_sha256": contract.sha256_file(vesum_db),
                "vesum_db_bytes": vesum_db.stat().st_size,
            }
        ),
        "verify_words": verify_words_fn,
        "check_modern_form": check_modern_form_fn,
        "search_style_guide": search_style_guide_fn,
        "search_text": search_text_fn,
        "search_ua_gec_errors": "No UA-GEC results found.",
        "search_heritage": search_heritage_fn,
        "check_russian_shadow": check_russian_shadow_fn,
        "query_pravopys": "No pravopys section found.",
        "query_ulif": json.dumps({"status": "not_found", "entry": None}),
        "search_slovnyk_me": "No slovnyk.me results.",
        "query_grac": json.dumps({"status": "unavailable", "entry": None}),
    }

    transport = compiler.FakeMcpToolTransport(tool_names=compiler.REQUIRED_TOOL_NAMES, responses=responses)
    return compiler.LocalMcpSourcesClient(transport=transport, **files)


def static_verify(provider_name: str) -> dict[str, Any]:
    """Validate static shapes and evidence contracts without provider invocation."""
    rows = fixture_rows()
    assert len(rows) == 2
    challenge = secrets.token_hex(32)
    if provider_name not in {"gemini", "grok"}:
        raise CanaryError("unknown_provider")

    tmp = Path(tempfile.mkdtemp(prefix=".static-canary-"))
    try:
        client = make_synthetic_mcp_client(tmp)
        sidecar = compile_public_sidecar(client, rows)
        client.close()
        if provider_name == "gemini":
            schema = gemini_schema(rows, challenge)
            assert schema["required"] == ["labels_by_position", "liveness_challenge"]
            prompt = gemini_prompt(challenge, rows, sidecar)
        else:
            prompt = grok_prompt(challenge, rows, sidecar)

        trap_ev = sidecar["rows"][0]["evidence"]
        trap_antonenko = next(e["evidence_id"] for e in trap_ev if e["channel"] == "antonenko_style" and e["status"] == "attested")
        trap_shadow = next(e["evidence_id"] for e in trap_ev if e["channel"] == "russian_shadow_suspicion" and e["status"] == "attested")

        ctrl_ev = sidecar["rows"][1]["evidence"]
        ctrl_vesum = next(e["evidence_id"] for e in ctrl_ev if e["channel"] == "vesum_attestation" and e["status"] == "attested")
        ctrl_heritage = next(e["evidence_id"] for e in ctrl_ev if e["channel"] == "heritage_attestation" and e["status"] == "attested")

        labels = [
            {
                "unit_id": rows[0]["unit_id"],
                "unit_sha256": rows[0]["unit_sha256"],
                "decision_code": "reject_insufficient_locator_evidence",
                "clean_modern_standard_prose": False,
                "modern_genre_id": None,
                "evidence_ids": sorted([trap_antonenko, trap_shadow]),
            },
            {
                "unit_id": rows[1]["unit_id"],
                "unit_sha256": rows[1]["unit_sha256"],
                "decision_code": "agree",
                "clean_modern_standard_prose": True,
                "modern_genre_id": "scientific_expository",
                "evidence_ids": sorted([ctrl_vesum, ctrl_heritage]),
            },
        ]
        SOURCE.validate("clean_label", {"rows": rows}, canonical({"labels": labels}), sidecar=sidecar)
        verify_semantic_canary_assertions(sidecar, labels)

        return {
            "ok": True,
            "provider": provider_name,
            "mode": "static",
            "prompt_sha256": digest(prompt),
            "fixture_hashes": {
                "fixture_raw_sha256": digest(canonical(rows)),
                "row_count": len(rows),
                "identity_set_sha256": digest(canonical(sorted((r["unit_id"], r["unit_sha256"]) for r in rows))),
            },
            "sidecar_id": sidecar["sidecar_id"],
            "text_free": True,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def invoke_canary(
    provider_name: str,
    provider_bin: Path,
    *,
    execution_mode: str = "real",
    receipt_path: Path | None = None,
    sources_client: compiler.LocalMcpSourcesClient | None = None,
    mcp_endpoint: str = compiler.DEFAULT_MCP_ENDPOINT,
    max_attempts: int = 2,
) -> dict[str, Any]:
    """Execute provider canary with challenge, sidecar compilation, retry and verification."""
    if execution_mode not in {"real", "synthetic"}:
        raise CanaryError("invalid_execution_mode")
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or not 1 <= max_attempts <= 2:
        raise CanaryError("invalid_attempt_limit")
    if execution_mode == "real" and sources_client is not None:
        raise CanaryError("real_mode_prohibits_injected_sources_client")

    # Verify real executable identity if real mode is requested
    if execution_mode == "real":
        try:
            resolved_exe = provider_bin.resolve(strict=True)
        except OSError as exc:
            raise CanaryError("provider_executable_unavailable") from exc
        if not resolved_exe.is_file() or resolved_exe.is_symlink():
            raise CanaryError("invalid_executable")
        expected_live_bin = AGY if provider_name == "gemini" else GROK
        try:
            resolved_live = expected_live_bin.resolve(strict=True)
        except OSError:
            resolved_live = None
        if resolved_live is None or resolved_exe != resolved_live:
            raise CanaryError("provider_executable_mismatch")
        exe_sha256 = contract.sha256_file(resolved_exe)
    else:
        try:
            resolved_exe = provider_bin.resolve(strict=True)
            exe_sha256 = contract.sha256_file(resolved_exe)
        except OSError:
            exe_sha256 = "synthetic"

    # Setup sources client
    tmp_mcp: Path | None = None
    if sources_client is None:
        if execution_mode == "synthetic":
            tmp_mcp = Path(tempfile.mkdtemp(prefix=".canary-mcp-"))
            sources_client = make_synthetic_mcp_client(tmp_mcp)
        else:
            sources_client = compiler.LocalMcpSourcesClient(endpoint_url=mcp_endpoint)

    runtime = Path(tempfile.mkdtemp(prefix=f".cycle007-canary-{provider_name}-"))
    os.chmod(runtime, 0o700)
    try:
        rows = fixture_rows()
        sidecar = compile_public_sidecar(sources_client, rows)
        sources_identity = sources_client.server_identity()

        challenge = secrets.token_hex(32)
        if provider_name == "gemini":
            prompt_bytes = gemini_prompt(challenge, rows, sidecar)
            schema_dict = gemini_schema(rows, challenge)
            schema_path = runtime / "response-schema.json"
            stdin_path = runtime / "prompt.stdin"
            log_path = runtime / "agy.log"
            _atomic(schema_path, schema_dict)
            _atomic(
                stdin_path,
                canonical({"event": "user", "message": {"content": [{"type": "text", "text": prompt_bytes.decode("utf-8")}]}}),
                raw=True,
            )
            _atomic(log_path, b"", raw=True)
            cmd = [
                str(provider_bin),
                "--model",
                GEMINI_MODEL,
                "--mode",
                "plan",
                "--sandbox",
                "--disable-slash-commands",
                "--input-format",
                "stream-json",
                "--output-format",
                "stream-json",
                "--json-schema",
                str(schema_path),
                "--print",
                "",
                "--log-file",
                str(log_path),
            ]
        else:
            prompt_bytes = grok_prompt(challenge, rows, sidecar)
            stdin_path = runtime / "prompt.stdin"
            _atomic(stdin_path, prompt_bytes, raw=True)
            cmd = [
                str(provider_bin),
                "--model",
                GROK_MODEL,
                "--reasoning-effort",
                "high",
                "--output-format",
                "plain",
                "--permission-mode",
                "plan",
                "--no-alt-screen",
                "--no-memory",
                "--no-subagents",
                "--disable-web-search",
                "--verbatim",
            ]

        attempt = 1
        provider_calls = 0
        raw_output: bytes = b""
        normalized_labels: list[dict[str, Any]] = []
        provenance: dict[str, Any] = {}

        while attempt <= max_attempts:
            provider_calls += 1
            raw_path = runtime / f"provider-{attempt}.raw"
            try:
                with stdin_path.open("rb") as stdin, raw_path.open("xb") as stdout:
                    os.chmod(raw_path, 0o600)
                    completed = subprocess.run(
                        cmd,
                        stdin=stdin,
                        stdout=stdout,
                        stderr=subprocess.DEVNULL,
                        check=False,
                        shell=False,
                    )
                if completed.returncode != 0:
                    raise CanaryStructuralError("provider_process_nonzero_exit")
                raw_output = raw_path.read_bytes()
                if not raw_output.strip():
                    raise CanaryStructuralError("provider_output_empty")

                if provider_name == "gemini":
                    init_ev, res_ev, extracted = _extract_gemini(raw_output, challenge)
                    norm = extracted["labels"]
                    provenance = {
                        "init_model": init_ev["init"]["model"],
                        "result_status": res_ev.get("status", "SUCCESS"),
                        "init_conversation_id": init_ev.get("conversation_id"),
                        "result_conversation_id": res_ev.get("conversation_id"),
                        "challenge_sha256": digest(challenge.encode("utf-8")),
                        "raw_stream_sha256": digest(raw_output),
                    }
                else:
                    extracted = _extract_grok(raw_output, challenge)
                    norm = extracted["labels"]
                    provenance = {
                        "challenge_sha256": digest(challenge.encode("utf-8")),
                        "response_raw_sha256": digest(raw_output),
                    }

                # Semantic validation through official validator
                try:
                    SOURCE.validate("clean_label", {"rows": rows}, canonical({"labels": norm}), sidecar=sidecar)
                except SOURCE.Invalid as exc:
                    raise CanarySemanticError(str(exc)) from exc

                # Dedicated semantic canary assertions
                verify_semantic_canary_assertions(sidecar, norm)
                normalized_labels = norm
                break

            except CanaryStructuralError as exc:
                if attempt < max_attempts:
                    attempt += 1
                    continue
                raise CanaryError(exc.code, structural=True) from exc
            except (CanarySemanticError, SOURCE.Invalid):
                # Semantic failure is terminal; no provider retry
                raise

        if provider_calls < 1 or not normalized_labels or not raw_output:
            raise CanaryError("provider_result_missing")
        receipt = build_receipt(
            provider_name,
            execution_mode=execution_mode,
            provider_calls=provider_calls,
            rows=rows,
            sidecar=sidecar,
            prompt_bytes=prompt_bytes,
            exe_sha256=exe_sha256,
            raw_response=raw_output,
            normalized_labels=normalized_labels,
            sources_identity=sources_identity,
            provenance=provenance,
        )

        if receipt_path is not None:
            _atomic(receipt_path, receipt)
            if execution_mode == "real":
                _atomic(receipt_path.with_suffix(receipt_path.suffix + ".raw"), raw_output, raw=True)

        return receipt

    finally:
        shutil.rmtree(runtime, ignore_errors=True)
        if tmp_mcp is not None:
            shutil.rmtree(tmp_mcp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("gemini", "grok"), required=True, help="target provider harness")
    parser.add_argument("--static", action="store_true", help="static schema/evidence proof without provider execution")
    parser.add_argument("--test-provider-bin", type=Path, help="synthetic provider executable fixture")
    parser.add_argument("--synthetic-mcp", action="store_true", help="use in-memory synthetic Sources MCP double")
    parser.add_argument("--mcp-endpoint", default=compiler.DEFAULT_MCP_ENDPOINT, help="Sources MCP endpoint URL")
    parser.add_argument("--receipt", type=Path, help="0600 output receipt path")
    args = parser.parse_args()

    try:
        if args.static:
            if args.test_provider_bin or args.synthetic_mcp:
                raise CanaryError("static_mode_prohibits_provider_args")
            result = static_verify(args.provider)
            if args.receipt:
                _atomic(args.receipt, result)
        elif args.test_provider_bin:
            result = invoke_canary(
                args.provider,
                args.test_provider_bin,
                execution_mode="synthetic",
                receipt_path=args.receipt,
                mcp_endpoint=args.mcp_endpoint,
            )
        elif args.synthetic_mcp:
            provider_bin = AGY if args.provider == "gemini" else GROK
            result = invoke_canary(
                args.provider,
                provider_bin,
                execution_mode="synthetic",
                receipt_path=args.receipt,
                mcp_endpoint=args.mcp_endpoint,
            )
        else:
            if args.receipt is None:
                raise CanaryError("receipt_path_required_for_real_mode")
            provider_bin = AGY if args.provider == "gemini" else GROK
            result = invoke_canary(
                args.provider,
                provider_bin,
                execution_mode="real",
                receipt_path=args.receipt,
                mcp_endpoint=args.mcp_endpoint,
            )

        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except CanaryError as exc:
        result = {"ok": False, "failure_code": exc.code, "text_free": True}
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 2
    except Exception:
        result = {"ok": False, "failure_code": "canary_execution_failed", "text_free": True}
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
