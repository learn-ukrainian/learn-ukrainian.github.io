#!/usr/bin/env python3
"""Text-free fail-stop controller for the frozen Cycle-007 stage sequence.

It accepts the package, lock, preflight receipt, and public code bindings
explicitly. It never discovers a package or prints child output.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import os
import selectors
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HERE = Path(__file__).resolve().parent
# Keep the launcher path exactly as supplied by the active interpreter.  A
# venv launcher is commonly a symlink whose path is significant to Python's
# environment discovery, so resolving it here would silently leave the venv.
PRIMARY_PYTHON = Path(sys.executable)
AMENDMENT = HERE / "phase3-cycle007-source-grounded-amendment-v1.md"
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
CYCLE = "phase3-v2-1-evaluation-cycle-007"
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

STAGES = ("gemini", "grok", "compare", "audit", "adjudicate", "resolve", "certify")
LANES = {"clean_label": 40, "residual_label": 164}
LABEL_PROMPT_PATHS = {
    "gemini": {
        "clean_label": Path("prompts/gemini-clean-label.md"),
        "residual_label": Path("prompts/gemini-residual-label.md"),
    },
    "grok": {
        "clean_label": Path("prompts/grok-clean-label.md"),
        "residual_label": Path("prompts/grok-residual-label.md"),
    },
}
GEMINI_MODEL = "Gemini 3.6 Flash (High)"
GEMINI_REQUEST_BYTE_BUDGET = 1024 * 1024
GROK_MODEL = "grok-4.5"
REQUIRED_CODE_PATHS = {
    "gemini_runner": HERE / "phase3-run-cycle007-gemini-label-provider-batch-v1.py",
    "label_validator": HERE / "phase3-cycle007-label-validation-v1.py",
    "controller": HERE / "phase3-run-cycle007-controller-v1.py",
    "grok_runner": HERE / "phase3-run-cycle007-grok-label-provider-batch-v1.py",
    "compare_runner": HERE / "phase3-compare-cycle007-dual-labels-v1.py",
    "audit_runner": HERE / "phase3-audit-cycle007-consensus-v1.py",
    "adjudicate_runner": HERE / "phase3-run-cycle007-dual-label-adjudication-v1.py",
    "resolve_runner": HERE / "phase3-apply-cycle007-operator-resolutions-v1.py",
    "certify_runner": HERE / "phase3-verify-cycle007-label-completion-v1.py",
    "evidence_validator": ROOT / "scripts/projects/open_model_data/phase3_cycle007_evidence_validator.py",
    "evidence_contract": ROOT / "scripts/projects/open_model_data/phase3_cycle007_evidence_contract.py",
}
CANARY_RUNNER = HERE / "phase3-run-cycle007-public-canaries-v1.py"
EVIDENCE_COMPILER = ROOT / "scripts/projects/open_model_data/phase3_cycle007_evidence_compiler.py"
EVIDENCE_VALIDATOR = ROOT / "scripts/projects/open_model_data/phase3_cycle007_evidence_validator.py"
EVIDENCE_CONTRACT = ROOT / "scripts/projects/open_model_data/phase3_cycle007_evidence_contract.py"
PUBLIC_CANARY_DOMAIN = "phase3-cycle007-public-canary-v1"
MCP_ENDPOINT = "http://127.0.0.1:8766/mcp"
MCP_REQUIRED_TOOL_NAMES = (
    "check_modern_form",
    "check_russian_shadow",
    "mcp_server_identity",
    "query_grac",
    "query_pravopys",
    "query_ulif",
    "search_heritage",
    "search_slovnyk_me",
    "search_style_guide",
    "search_text",
    "search_ua_gec_errors",
    "verify_words",
)
AGY: Path | None = None
GROK: Path | None = None

STAGE_SEAL_SCHEMA = "phase3_cycle007_stage_complete_v2"
STAGE_SEAL_FIELDS = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "stage",
        "preflight_receipt_sha256",
        "python_executable_sha256",
        "preceding_stage_seal_sha256",
        "text_free",
        "seal_sha256",
    }
)

STAGE_RUNNER_LABELS = {
    "grok": "grok_runner",
    "compare": "compare_runner",
    "audit": "audit_runner",
    "adjudicate": "adjudicate_runner",
    "resolve": "resolve_runner",
    "certify": "certify_runner",
}
EXECUTION_LOCK_FD_ENV = "PHASE3_CYCLE007_EXECUTION_LOCK_FD"
MAX_RUNNER_STATUS_BYTES = 4096


class ControllerError(ValueError):
    pass


def _runner_failure_code(stdout: bytes) -> str:
    """Return only a bounded text-free child failure code."""
    if len(stdout) > MAX_RUNNER_STATUS_BYTES:
        return "stage_execution_failed"
    try:
        value = json.loads(stdout.decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ControllerError):
        return "stage_execution_failed"
    if not isinstance(value, dict) or set(value) != {"failure_code", "ok", "text_free"}:
        return "stage_execution_failed"
    code = value.get("failure_code")
    if (
        value.get("ok") is not False
        or value.get("text_free") is not True
        or not isinstance(code, str)
        or not 1 <= len(code) <= 64
        or not code.isascii()
        or any(not (character.islower() or character.isdigit() or character == "_") for character in code)
    ):
        return "stage_execution_failed"
    return code


def _run_stage_subprocess(
    command: list[str], *, executable: Path, pass_fds: tuple[int, ...]
) -> tuple[int, bytes]:
    """Drain child stdout while retaining only one bounded failure status."""
    with subprocess.Popen(
        command,
        executable=str(executable),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        shell=False,
        pass_fds=pass_fds,
    ) as process:
        assert process.stdout is not None
        descriptor = process.stdout.fileno()
        os.set_blocking(descriptor, False)
        status = bytearray()
        selector = selectors.DefaultSelector()
        selector.register(descriptor, selectors.EVENT_READ)

        def drain(*, single_read: bool = False) -> bool:
            while True:
                try:
                    chunk = os.read(descriptor, 64 * 1024)
                except BlockingIOError:
                    return True
                if not chunk:
                    return False
                remaining = MAX_RUNNER_STATUS_BYTES + 1 - len(status)
                if remaining > 0:
                    status.extend(chunk[:remaining])
                if single_read:
                    return True

        try:
            pipe_open = True
            while process.poll() is None:
                if pipe_open and selector.select(timeout=0.1):
                    pipe_open = drain()
                    if not pipe_open:
                        selector.unregister(descriptor)
                elif not pipe_open:
                    with contextlib.suppress(subprocess.TimeoutExpired):
                        process.wait(timeout=0.1)
            if pipe_open:
                drain(single_read=True)
        finally:
            selector.close()
        return_code = process.wait()
    return return_code, b"" if return_code == 0 else bytes(status)


def _inherited_execution_lock_fd() -> int | None:
    raw = os.environ.get(EXECUTION_LOCK_FD_ENV)
    if raw is None:
        return None
    try:
        descriptor = int(raw)
        if descriptor < 0:
            raise ValueError
        os.fstat(descriptor)
    except (ValueError, OSError) as exc:
        raise ControllerError("execution_lock_binding_drift") from exc
    return descriptor


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return digest(path.read_bytes())


def _contract_digest(value: Any) -> str:
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _expected_mcp_tool_set_sha256() -> str:
    return _contract_digest(list(MCP_REQUIRED_TOOL_NAMES))


def _hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


SOURCE_IDENTITY_HASH_KEYS = (
    "server_code_sha256",
    "sources_db_sha256",
    "vesum_db_sha256",
)


def _source_identity_hashes(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or any(not _hex64(value.get(key)) for key in SOURCE_IDENTITY_HASH_KEYS):
        raise ControllerError("preflight_binding_drift")
    return {key: value[key] for key in SOURCE_IDENTITY_HASH_KEYS}


def _public_fixture_hashes() -> dict[str, Any]:
    rows = [
        {
            "unit_id": f"{PUBLIC_CANARY_DOMAIN}-trap",
            "unit_sha256": digest(f"{PUBLIC_CANARY_DOMAIN}:trap:слідуючий раз".encode()),
            "source_text": "слідуючий раз",
            "family_id": PUBLIC_CANARY_DOMAIN,
        },
        {
            "unit_id": f"{PUBLIC_CANARY_DOMAIN}-control",
            "unit_sha256": digest(f"{PUBLIC_CANARY_DOMAIN}:control:філіжанка".encode()),
            "source_text": "філіжанка",
            "family_id": PUBLIC_CANARY_DOMAIN,
        },
    ]
    return {
        "fixture_raw_sha256": digest(canonical(rows)),
        "row_count": 2,
        "identity_set_sha256": digest(canonical(sorted((row["unit_id"], row["unit_sha256"]) for row in rows))),
    }


def _exact_hash_map(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys and all(_hex64(value[key]) for key in keys)


def _source_endpoint_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "server_code_sha256",
        "sources_db_sha256",
        "sources_db_bytes",
        "vesum_db_sha256",
        "vesum_db_bytes",
    }:
        raise ControllerError("preflight_binding_drift")
    for key in ("server_code_sha256", "sources_db_sha256", "vesum_db_sha256"):
        if not _hex64(value.get(key)):
            raise ControllerError("preflight_binding_drift")
    for key in ("sources_db_bytes", "vesum_db_bytes"):
        if not isinstance(value.get(key), int) or isinstance(value.get(key), bool) or value[key] <= 0:
            raise ControllerError("preflight_binding_drift")
    return value


def _canary_raw_artifact(receipt_path: Path, expected_provider: str, response_hashes: dict[str, Any]) -> None:
    """Bind the receipt's provider-response hash to the persisted raw artifact."""
    raw_path = Path(f"{receipt_path}.raw")
    _mode(raw_path, 0o600)
    raw_key = "raw_stream_sha256" if expected_provider == "gemini" else "response_raw_sha256"
    if response_hashes.get(raw_key) != sha256(raw_path):
        raise ControllerError("preflight_binding_drift")


def _validate_mcp_transport_attestation(manifest: dict[str, Any]) -> dict[str, Any]:
    value = manifest.get("mcp_transport_attestation")
    fields = {
        "schema_version",
        "transport",
        "endpoint_sha256",
        "required_tool_set_sha256",
        "tool_call_count",
        "counts_by_tool",
        "server_identity_call_count",
        "ordered_call_commitment_sha256",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ControllerError("preflight_binding_drift")
    if value.get("schema_version") != "phase3_cycle007_mcp_transport_attestation_v1":
        raise ControllerError("preflight_binding_drift")
    if value.get("transport") not in {"streamable_http", "synthetic"}:
        raise ControllerError("preflight_binding_drift")
    if (
        not _hex64(value.get("endpoint_sha256"))
        or value.get("endpoint_sha256") != digest(MCP_ENDPOINT.encode("utf-8"))
        or value.get("required_tool_set_sha256") != _expected_mcp_tool_set_sha256()
        or not _hex64(value.get("ordered_call_commitment_sha256"))
    ):
        raise ControllerError("preflight_binding_drift")
    counts = value.get("counts_by_tool")
    if (
        not isinstance(counts, dict)
        or any(
            not isinstance(tool, str) or not tool or not isinstance(count, int) or isinstance(count, bool) or count < 0
            for tool, count in counts.items()
        )
        or not isinstance(value.get("tool_call_count"), int)
        or isinstance(value.get("tool_call_count"), bool)
        or value["tool_call_count"] < 0
        or sum(counts.values()) != value["tool_call_count"]
        or not isinstance(value.get("server_identity_call_count"), int)
        or isinstance(value.get("server_identity_call_count"), bool)
        or value["server_identity_call_count"] < 0
        or counts.get("mcp_server_identity", 0) != value["server_identity_call_count"]
    ):
        raise ControllerError("preflight_binding_drift")
    real_denominator = (
        manifest.get("packet_count") == 204
        and manifest.get("row_count") == 10159
        and manifest.get("source_package_binding") is not None
    )
    if real_denominator and (
        value.get("transport") != "streamable_http"
        or value.get("endpoint_sha256") != digest(MCP_ENDPOINT.encode("utf-8"))
        or value.get("server_identity_call_count") != 1
        or value.get("tool_call_count", 0) <= manifest["row_count"]
    ):
        raise ControllerError("preflight_binding_drift")
    return value


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ControllerError("preflight_binding_drift")
        value[key] = item
    return value


def _mode(path: Path, expected: int) -> None:
    if not path.exists() or path.is_symlink() or os.stat(path).st_mode & 0o777 != expected:
        raise ControllerError("preflight_binding_drift")


def _read_json(path: Path) -> dict[str, Any]:
    _mode(path, 0o600)
    try:
        value = json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ControllerError) as exc:
        raise ControllerError("preflight_binding_drift") from exc
    if not isinstance(value, dict):
        raise ControllerError("preflight_binding_drift")
    return value


def _atomic(path: Path, value: dict[str, Any]) -> None:
    data = canonical(value)
    parent = path.parent
    with contextlib.suppress(FileExistsError):
        parent.mkdir(mode=0o700)
    if parent.is_symlink() or not parent.is_dir() or os.stat(parent).st_mode & 0o777 != 0o700:
        raise ControllerError("preflight_binding_drift")
    if path.exists():
        _mode(path, 0o600)
        if path.read_bytes() != data:
            raise ControllerError("controller_state_drift")
        return
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
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


def _replace_atomic(path: Path, value: dict[str, Any]) -> None:
    """Replace one validated control receipt without exposing a partial file."""
    data = canonical(value)
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir() or os.stat(parent).st_mode & 0o777 != 0o700:
        raise ControllerError("preflight_rotation_state_drift")
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
    temporary = Path(name)
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


def _canonical_embedded_receipt(path: Path) -> tuple[bytes, dict[str, Any]]:
    value = _read_json(path)
    raw = path.read_bytes()
    unsigned = {key: item for key, item in value.items() if key != "receipt_sha256"}
    if raw != canonical(value) or value.get("receipt_sha256") != digest(canonical(unsigned)):
        raise ControllerError("preflight_rotation_state_drift")
    return raw, value


def _archive_superseded_receipt(control: Path, label: str, raw: bytes, value: dict[str, Any]) -> None:
    archive = control / "superseded-receipts"
    archive.mkdir(mode=0o700, exist_ok=True)
    if archive.is_symlink() or not archive.is_dir() or os.stat(archive).st_mode & 0o777 != 0o700:
        raise ControllerError("preflight_rotation_state_drift")
    _atomic(archive / f"{label}-{digest(raw)}.json", value)


def _install_preflight_receipts(
    package: Path,
    receipt: dict[str, Any],
    gemini_receipt: dict[str, Any],
    grok_receipt: dict[str, Any],
) -> None:
    """Install or rotate an exact preflight identity before any stage is sealed.

    Rotation is explicit in the successor receipt, preserves every superseded
    receipt, writes the authoritative preflight receipt last, and is idempotent
    after interruption.
    """
    control = _control(package)
    if control.is_symlink():
        raise ControllerError("preflight_rotation_state_drift")
    with contextlib.suppress(FileExistsError):
        control.mkdir(mode=0o700)
    if control.is_symlink() or not control.is_dir() or os.stat(control).st_mode & 0o777 != 0o700:
        raise ControllerError("preflight_rotation_state_drift")
    destinations = {
        "gemini-canary": (control / "gemini-canary-receipt.json", gemini_receipt),
        "grok-canary": (control / "grok-canary-receipt.json", grok_receipt),
        "preflight": (control / "preflight-receipt.json", receipt),
    }
    preflight_path, _ = destinations["preflight"]
    if not preflight_path.exists() and not preflight_path.is_symlink():
        for _label, (path, value) in destinations.items():
            _atomic(path, value)
        return

    current_raw, current = _canonical_embedded_receipt(preflight_path)
    desired_raw = canonical(receipt)
    if current_raw == desired_raw:
        for _label, (path, value) in destinations.items():
            _atomic(path, value)
        return
    if any(_stage_seal(package, stage).exists() or _stage_seal(package, stage).is_symlink() for stage in STAGES):
        raise ControllerError("preflight_rotation_blocked")
    reviews = receipt.get("review_hashes")
    if (
        current.get("schema_version") != "phase3_cycle007_preflight_receipt_v1"
        or not isinstance(reviews, dict)
        or reviews.get("superseded_preflight_receipt_sha256") != digest(current_raw)
    ):
        raise ControllerError("preflight_rotation_not_authorized")

    # Canary copies may already be current after an interrupted rotation.  The
    # preflight copy remains authoritative and is always replaced last.
    for label in ("gemini-canary", "grok-canary"):
        path, value = destinations[label]
        if path.exists() or path.is_symlink():
            installed_raw, installed = _canonical_embedded_receipt(path)
            if installed_raw == canonical(value):
                continue
            _archive_superseded_receipt(control, label, installed_raw, installed)
            _replace_atomic(path, value)
        else:
            _atomic(path, value)
    _archive_superseded_receipt(control, "preflight", current_raw, current)
    _replace_atomic(preflight_path, receipt)


def _parse_code_paths(items: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for item in items:
        label, separator, value = item.partition("=")
        if not separator or not label or not value or label in result:
            raise ControllerError("preflight_binding_drift")
        path = Path(value).resolve()
        if not path.is_file() or path.is_symlink():
            raise ControllerError("preflight_binding_drift")
        result[label] = path
    if set(result) != set(REQUIRED_CODE_PATHS):
        raise ControllerError("preflight_binding_drift")
    return result


def _label_prompt_sha256s(package: Path) -> dict[str, dict[str, str]]:
    """Hash all four private label prompts without reading their text into receipts."""
    result: dict[str, dict[str, str]] = {}
    for provider, lanes in LABEL_PROMPT_PATHS.items():
        result[provider] = {}
        for lane, relative in lanes.items():
            path = package / relative
            _mode(path, 0o600)
            result[provider][lane] = sha256(path)
    return result


def _exact_label_prompt_sha256s(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == set(LABEL_PROMPT_PATHS)
        and all(
            isinstance(value.get(provider), dict)
            and set(value[provider]) == set(LABEL_PROMPT_PATHS[provider])
            and all(_hex64(value[provider].get(lane)) for lane in LABEL_PROMPT_PATHS[provider])
            for provider in LABEL_PROMPT_PATHS
        )
    )


EXACT_GEMINI_CANARY_KEYS = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "ok",
        "execution_mode",
        "exact_model",
        "model_family",
        "harness",
        "provider_call_count",
        "fixture_hashes",
        "sidecar_hashes",
        "prompt_hashes",
        "code_hashes",
        "executable_sha256",
        "response_hashes",
        "sources_endpoint_identity",
        "sources_mcp_used",
        "valid_evidence_ids",
        "russian_surzhyk_trap_rejected",
        "heritage_control_preserved",
        "provenance_basis",
        "text_free",
        "receipt_sha256",
    }
)

EXACT_GROK_CANARY_KEYS = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "ok",
        "execution_mode",
        "exact_model",
        "model_family",
        "harness",
        "provider_call_count",
        "fixture_hashes",
        "sidecar_hashes",
        "prompt_hashes",
        "code_hashes",
        "executable_sha256",
        "response_hashes",
        "sources_endpoint_identity",
        "sources_mcp_used",
        "valid_evidence_ids",
        "russian_surzhyk_trap_rejected",
        "heritage_control_preserved",
        "provenance_basis",
        "text_free",
        "receipt_sha256",
    }
)


def _validate_canary_receipt(
    receipt_path: Path, expected_provider: str, provider_executable: Path
) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    """Accept only a valid public canary receipt matching exact model/family/harness and bound criteria."""
    _mode(receipt_path, 0o600)
    receipt = _read_json(receipt_path)
    if receipt_path.read_bytes() != canonical(receipt):
        raise ControllerError("preflight_binding_drift")

    if expected_provider == "gemini":
        if set(receipt) != EXACT_GEMINI_CANARY_KEYS:
            raise ControllerError("preflight_binding_drift")
        if receipt.get("schema_version") != "phase3_cycle007_gemini_public_canary_receipt_v1":
            raise ControllerError("preflight_binding_drift")
        if (
            receipt.get("exact_model") != GEMINI_MODEL
            or receipt.get("model_family") != "google"
            or receipt.get("harness") != "agy"
        ):
            raise ControllerError("preflight_binding_drift")
        try:
            if provider_executable.is_symlink():
                raise ControllerError("preflight_binding_drift")
            resolved_exe = provider_executable.resolve(strict=True)
            if not resolved_exe.is_file():
                raise ControllerError("preflight_binding_drift")
            exe_sha256 = sha256(resolved_exe)
        except OSError as exc:
            raise ControllerError("preflight_binding_drift") from exc
        if receipt.get("executable_sha256") != exe_sha256:
            raise ControllerError("preflight_binding_drift")

    elif expected_provider == "grok":
        if set(receipt) != EXACT_GROK_CANARY_KEYS:
            raise ControllerError("preflight_binding_drift")
        if receipt.get("schema_version") != "phase3_cycle007_grok_public_canary_receipt_v1":
            raise ControllerError("preflight_binding_drift")
        if (
            receipt.get("exact_model") != GROK_MODEL
            or receipt.get("model_family") != "xai"
            or receipt.get("harness") != "native_grok"
        ):
            raise ControllerError("preflight_binding_drift")
        try:
            if provider_executable.is_symlink():
                raise ControllerError("preflight_binding_drift")
            resolved_exe = provider_executable.resolve(strict=True)
            if not resolved_exe.is_file():
                raise ControllerError("preflight_binding_drift")
            exe_sha256 = sha256(resolved_exe)
        except OSError as exc:
            raise ControllerError("preflight_binding_drift") from exc
        if receipt.get("executable_sha256") != exe_sha256:
            raise ControllerError("preflight_binding_drift")
    else:
        raise ControllerError("preflight_binding_drift")

    if receipt.get("execution_mode") != "real":
        raise ControllerError("preflight_binding_drift")
    if receipt.get("evaluation_cycle_id") != CYCLE:
        raise ControllerError("preflight_binding_drift")
    if receipt.get("amendment_sha256") != AMENDMENT_SHA256:
        raise ControllerError("preflight_binding_drift")
    if receipt.get("ok") is not True or receipt.get("text_free") is not True:
        raise ControllerError("preflight_binding_drift")
    if receipt.get("sources_mcp_used") is not True:
        raise ControllerError("preflight_binding_drift")
    if receipt.get("valid_evidence_ids") is not True:
        raise ControllerError("preflight_binding_drift")
    if receipt.get("russian_surzhyk_trap_rejected") is not True:
        raise ControllerError("preflight_binding_drift")
    if receipt.get("heritage_control_preserved") is not True:
        raise ControllerError("preflight_binding_drift")

    sources_id = _source_endpoint_identity(receipt.get("sources_endpoint_identity"))

    if receipt.get("fixture_hashes") != _public_fixture_hashes():
        raise ControllerError("preflight_binding_drift")
    sidecar_hashes = receipt.get("sidecar_hashes")
    if (
        not isinstance(sidecar_hashes, dict)
        or set(sidecar_hashes) != {"sidecar_id", "sidecar_raw_sha256"}
        or not isinstance(sidecar_hashes.get("sidecar_id"), str)
        or not sidecar_hashes["sidecar_id"].startswith("cycle007_sidecar:")
        or not _hex64(sidecar_hashes.get("sidecar_raw_sha256"))
    ):
        raise ControllerError("preflight_binding_drift")
    if not _exact_hash_map(receipt.get("prompt_hashes"), {"prompt_sha256"}):
        raise ControllerError("preflight_binding_drift")
    expected_canary_code_hashes = {
        "compiler_sha256": sha256(EVIDENCE_COMPILER),
        "validator_sha256": sha256(REQUIRED_CODE_PATHS["label_validator"]),
        "evidence_validator_sha256": sha256(EVIDENCE_VALIDATOR),
        "evidence_contract_sha256": sha256(EVIDENCE_CONTRACT),
        "canary_runner_sha256": sha256(CANARY_RUNNER),
    }
    if receipt.get("code_hashes") != expected_canary_code_hashes:
        raise ControllerError("preflight_binding_drift")
    response_keys = (
        {"raw_stream_sha256", "labels_raw_sha256"}
        if expected_provider == "gemini"
        else {"response_raw_sha256", "labels_raw_sha256"}
    )
    if not _exact_hash_map(receipt.get("response_hashes"), response_keys):
        raise ControllerError("preflight_binding_drift")
    _canary_raw_artifact(receipt_path, expected_provider, receipt["response_hashes"])
    if not isinstance(receipt.get("provenance_basis"), dict) or not receipt["provenance_basis"]:
        raise ControllerError("preflight_binding_drift")
    if (
        not isinstance(receipt.get("provider_call_count"), int)
        or isinstance(receipt.get("provider_call_count"), bool)
        or receipt["provider_call_count"] < 1
    ):
        raise ControllerError("preflight_binding_drift")

    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    if receipt.get("receipt_sha256") != digest(canonical(unsigned)):
        raise ControllerError("preflight_binding_drift")

    return sha256(receipt_path), exe_sha256, sources_id, receipt


def _python_executable_target() -> Path:
    """Return the launcher target after strict absolute/regular-file checks."""
    if not PRIMARY_PYTHON.is_absolute():
        raise ControllerError("preflight_binding_drift")
    try:
        target = PRIMARY_PYTHON.resolve(strict=True)
        target_stat = target.stat()
    except (OSError, RuntimeError) as exc:
        raise ControllerError("preflight_binding_drift") from exc
    if not stat.S_ISREG(target_stat.st_mode):
        raise ControllerError("preflight_binding_drift")
    return target


def _python_launcher() -> Path:
    """Return the absolute venv launcher used as the child argv[0]."""
    if not PRIMARY_PYTHON.is_absolute():
        raise ControllerError("preflight_binding_drift")
    return PRIMARY_PYTHON


def _python_executable_sha256() -> str:
    return sha256(_python_executable_target())


def _require_python_binding(expected_sha256: str) -> Path:
    target = _python_executable_target()
    actual_sha256 = sha256(target)
    if not _hex64(expected_sha256) or actual_sha256 != expected_sha256:
        raise ControllerError("preflight_binding_drift")
    return target


def preflight(
    package: Path,
    receipt_path: Path,
    code_paths: dict[str, Path],
    gemini_canary_receipt_path: Path,
    grok_canary_receipt_path: Path | None = None,
    agy_executable: Path | None = None,
    grok_executable: Path | None = None,
) -> dict[str, Any]:
    python_executable_sha256 = _python_executable_sha256()
    if sha256(AMENDMENT) != AMENDMENT_SHA256:
        raise ControllerError("preflight_binding_drift")
    if not package.is_dir() or package.is_symlink() or os.stat(package).st_mode & 0o777 != 0o700:
        raise ControllerError("preflight_binding_drift")
    receipt = _read_json(receipt_path)
    if receipt_path.read_bytes() != canonical(receipt) or set(code_paths) != set(REQUIRED_CODE_PATHS):
        raise ControllerError("preflight_binding_drift")
    for label, path in REQUIRED_CODE_PATHS.items():
        if code_paths.get(label) != path.resolve():
            raise ControllerError("preflight_binding_drift")

    agy_executable = agy_executable or AGY
    grok_executable = grok_executable or GROK
    if (
        grok_canary_receipt_path is None
        or agy_executable is None
        or grok_executable is None
        or not agy_executable.is_absolute()
        or not grok_executable.is_absolute()
    ):
        raise ControllerError("preflight_binding_drift")

    gemini_canary_sha256, agy_sha256, gemini_sources_id, gemini_receipt = _validate_canary_receipt(
        gemini_canary_receipt_path, "gemini", agy_executable
    )
    grok_canary_sha256, grok_sha256, grok_sources_id, grok_receipt = _validate_canary_receipt(
        grok_canary_receipt_path, "grok", grok_executable
    )

    if gemini_sources_id != grok_sources_id:
        raise ControllerError("preflight_binding_drift")
    if receipt.get("sources_endpoint_identity") != gemini_sources_id:
        raise ControllerError("preflight_binding_drift")

    _mode(package / "custody-receipt.json", 0o600)
    manifest_path = package / "manifest.json"
    if not manifest_path.exists():
        manifest_path = package / "label-manifest.json"
    _mode(manifest_path, 0o600)

    evidence_manifest_path = package / "evidence" / "manifest.json"
    _mode(evidence_manifest_path, 0o600)
    evidence_manifest = _read_json(evidence_manifest_path)
    _validate_mcp_transport_attestation(evidence_manifest)
    if evidence_manifest.get("manifest_sha256") != _contract_digest(
        {key: value for key, value in evidence_manifest.items() if key != "manifest_sha256"}
    ):
        raise ControllerError("preflight_binding_drift")
    if any(
        evidence_manifest.get(key) != gemini_sources_id[key]
        for key in ("server_code_sha256", "sources_db_sha256", "vesum_db_sha256")
    ):
        raise ControllerError("preflight_binding_drift")
    manifest_identity_keys = {"sources_db_bytes", "vesum_db_bytes"}
    present_manifest_identity_keys = manifest_identity_keys & set(evidence_manifest)
    if present_manifest_identity_keys and present_manifest_identity_keys != manifest_identity_keys:
        raise ControllerError("preflight_binding_drift")
    if present_manifest_identity_keys and any(
        evidence_manifest.get(key) != gemini_sources_id[key] for key in manifest_identity_keys
    ):
        raise ControllerError("preflight_binding_drift")

    custody_sha256 = sha256(package / "custody-receipt.json")
    manifest_sha256 = sha256(manifest_path)
    ev_manifest_sha256 = sha256(evidence_manifest_path)
    label_prompt_sha256s = receipt.get("label_prompt_sha256s")
    if not _exact_label_prompt_sha256s(label_prompt_sha256s) or label_prompt_sha256s != _label_prompt_sha256s(package):
        raise ControllerError("preflight_binding_drift")

    custody_val = _read_json(package / "custody-receipt.json")
    if (
        custody_val.get("schema_version") != "phase3_cycle007_custody_receipt_v1"
        or custody_val.get("source_custody_receipt_raw_sha256") != SOURCE_CUSTODY_SHA256
        or custody_val.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or custody_val.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
    ):
        raise ControllerError("preflight_binding_drift")

    hashes = {label: sha256(path) for label, path in code_paths.items()}
    expected: dict[str, Any] = {
        "schema_version": "phase3_cycle007_preflight_receipt_v1",
        "amendment_sha256": AMENDMENT_SHA256,
        "package_custody_receipt_sha256": custody_sha256,
        "package_manifest_sha256": manifest_sha256,
        "package_evidence_manifest_sha256": ev_manifest_sha256,
        "gemini_canary_receipt_sha256": gemini_canary_sha256,
        "grok_canary_receipt_sha256": grok_canary_sha256,
        "code_hashes": hashes,
        "label_prompt_sha256s": label_prompt_sha256s,
        "backup_receipt_sha256": receipt.get("backup_receipt_sha256"),
        "review_hashes": receipt.get("review_hashes"),
        "ci_proof_bindings": receipt.get("ci_proof_bindings"),
        "sources_endpoint_identity": receipt.get("sources_endpoint_identity"),
        "text_free": True,
    }
    if "public_canary_receipt_sha256" in receipt:
        expected["public_canary_receipt_sha256"] = receipt["public_canary_receipt_sha256"]

    backup = expected["backup_receipt_sha256"]
    reviews = expected["review_hashes"]
    ci_proofs = expected["ci_proof_bindings"]
    sources_id = expected["sources_endpoint_identity"]
    if (
        not isinstance(backup, str)
        or len(backup) != 64
        or not isinstance(reviews, dict)
        or not reviews
        or not isinstance(ci_proofs, dict)
        or not isinstance(sources_id, dict)
        or set(receipt) != set(expected) | {"receipt_sha256"}
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(canonical(expected))
    ):
        raise ControllerError("preflight_binding_drift")

    _install_preflight_receipts(package, receipt, gemini_receipt, grok_receipt)

    return {
        "ok": True,
        "preflight_receipt_sha256": sha256(receipt_path),
        "expected_agy_executable_sha256": agy_sha256,
        "expected_grok_executable_sha256": grok_sha256,
        "expected_custody_sha256": custody_sha256,
        "expected_label_manifest_sha256": manifest_sha256,
        "expected_evidence_manifest_sha256": ev_manifest_sha256,
        "expected_python_executable_sha256": python_executable_sha256,
        "expected_label_prompt_sha256s": label_prompt_sha256s,
        "sources_endpoint_identity": gemini_sources_id,
        "text_free": True,
    }


def _control(package: Path) -> Path:
    return package / "control"


def _stage_seal(package: Path, stage: str) -> Path:
    return _control(package) / f"stage-{stage}.complete.json"


def _stage_seal_unsigned(
    stage: str,
    preflight_receipt_sha256: str,
    python_executable_sha256: str,
    preceding_stage_seal_sha256: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": STAGE_SEAL_SCHEMA,
        "evaluation_cycle_id": CYCLE,
        "stage": stage,
        "preflight_receipt_sha256": preflight_receipt_sha256,
        "python_executable_sha256": python_executable_sha256,
        "preceding_stage_seal_sha256": preceding_stage_seal_sha256,
        "text_free": True,
    }


def _validate_stage_seal(
    package: Path,
    stage: str,
    *,
    expected_preflight_receipt_sha256: str | None = None,
    expected_python_executable_sha256: str | None = None,
) -> tuple[str, dict[str, Any]]:
    if stage not in STAGES:
        raise ControllerError("invalid_stage_seal")
    path = _stage_seal(package, stage)
    try:
        _mode(path, 0o600)
        value = _read_json(path)
        if path.read_bytes() != canonical(value):
            raise ControllerError("invalid_stage_seal")
    except ControllerError as exc:
        raise ControllerError("invalid_stage_seal") from exc

    stage_index = STAGES.index(stage)
    preceding = value.get("preceding_stage_seal_sha256")
    if (
        set(value) != STAGE_SEAL_FIELDS
        or value.get("schema_version") != STAGE_SEAL_SCHEMA
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("stage") != stage
        or value.get("text_free") is not True
        or not _hex64(value.get("preflight_receipt_sha256"))
        or not _hex64(value.get("python_executable_sha256"))
        or not isinstance(preceding, dict)
        or set(preceding) != set(STAGES[:stage_index])
        or not all(_hex64(item) for item in preceding.values())
    ):
        raise ControllerError("invalid_stage_seal")
    if (
        expected_preflight_receipt_sha256 is not None
        and value["preflight_receipt_sha256"] != expected_preflight_receipt_sha256
    ):
        raise ControllerError("invalid_stage_seal")
    if (
        expected_python_executable_sha256 is not None
        and value["python_executable_sha256"] != expected_python_executable_sha256
    ):
        raise ControllerError("invalid_stage_seal")

    unsigned = {key: item for key, item in value.items() if key != "seal_sha256"}
    if value.get("seal_sha256") != digest(canonical(unsigned)):
        raise ControllerError("invalid_stage_seal")
    for prior in STAGES[:stage_index]:
        prior_path = _stage_seal(package, prior)
        if not prior_path.is_file() or prior_path.is_symlink() or preceding[prior] != sha256(prior_path):
            raise ControllerError("invalid_stage_seal")
    return sha256(path), value


def _validate_stage_chain(
    package: Path,
    *,
    expected_preflight_receipt_sha256: str | None = None,
    expected_python_executable_sha256: str | None = None,
) -> list[str]:
    completed: list[str] = []
    seal_hashes: dict[str, str] = {}
    chain_preflight_receipt_sha256 = expected_preflight_receipt_sha256
    for index, stage in enumerate(STAGES):
        path = _stage_seal(package, stage)
        if not path.exists():
            if path.is_symlink() or any(
                _stage_seal(package, later).exists() or _stage_seal(package, later).is_symlink()
                for later in STAGES[index + 1 :]
            ):
                raise ControllerError("invalid_stage_seal")
            break
        seal_hash, value = _validate_stage_seal(
            package,
            stage,
            expected_preflight_receipt_sha256=expected_preflight_receipt_sha256,
            expected_python_executable_sha256=expected_python_executable_sha256,
        )
        preceding = value["preceding_stage_seal_sha256"]
        if any(preceding[prior] != seal_hashes[prior] for prior in STAGES[:index]):
            raise ControllerError("invalid_stage_seal")
        if chain_preflight_receipt_sha256 is None:
            chain_preflight_receipt_sha256 = value["preflight_receipt_sha256"]
        elif value["preflight_receipt_sha256"] != chain_preflight_receipt_sha256:
            raise ControllerError("invalid_stage_seal")
        if index == 0:
            preflight_path = _control(package) / "preflight-receipt.json"
            try:
                _mode(preflight_path, 0o600)
            except ControllerError as exc:
                raise ControllerError("invalid_stage_seal") from exc
            if sha256(preflight_path) != value["preflight_receipt_sha256"]:
                raise ControllerError("invalid_stage_seal")
        completed.append(stage)
        seal_hashes[stage] = seal_hash
    return completed


def _stage_stop_paths(package: Path) -> tuple[Path, ...]:
    return (
        package / "label-output-gemini-cycle007-v1" / "provider-stop.json",
        package / "label-output-grok-cycle007-v1" / "provider-stop.json",
        package / "dual-label-adjudication-cycle007-v1" / "provider-stop.json",
        package / "consensus-audit-cycle007-v1" / "provider-stop.json",
    )


def status(package: Path) -> dict[str, Any]:
    completed = _validate_stage_chain(package, expected_python_executable_sha256=_python_executable_sha256())
    stopped = any(path.exists() for path in _stage_stop_paths(package))
    runtime_directories = [
        path.name for path in package.iterdir() if path.is_dir() and path.name.startswith(".cycle007-")
    ]
    return {
        "schema_version": "phase3_cycle007_controller_status_v1",
        "evaluation_cycle_id": CYCLE,
        "completed_stages": completed,
        "stopped": stopped,
        "runtime_directory_count": len(runtime_directories),
        "ready": not stopped and not runtime_directories and completed == list(STAGES),
        "text_free": True,
    }


def _require_contiguous(
    package: Path,
    stage: str,
    preflight_receipt_sha256: str,
    python_executable_sha256: str,
) -> None:
    stage_index = STAGES.index(stage)
    if any(path.exists() for path in _stage_stop_paths(package)):
        raise ControllerError("provider_stop_present")
    _require_python_binding(python_executable_sha256)
    preflight_path = _control(package) / "preflight-receipt.json"
    try:
        _mode(preflight_path, 0o600)
    except ControllerError as exc:
        raise ControllerError("preflight_binding_drift") from exc
    if sha256(preflight_path) != preflight_receipt_sha256:
        raise ControllerError("preflight_binding_drift")
    for prior in STAGES[:stage_index]:
        prior_path = _stage_seal(package, prior)
        if prior_path.is_symlink():
            raise ControllerError("invalid_stage_seal")
        if not prior_path.exists():
            raise ControllerError("noncontiguous_stage_order")
        _validate_stage_seal(
            package,
            prior,
            expected_preflight_receipt_sha256=preflight_receipt_sha256,
            expected_python_executable_sha256=python_executable_sha256,
        )
    if any(
        _stage_seal(package, later).exists() or _stage_seal(package, later).is_symlink()
        for later in STAGES[stage_index + 1 :]
    ):
        raise ControllerError("invalid_stage_seal")
    if _stage_seal(package, stage).exists() or _stage_seal(package, stage).is_symlink():
        _validate_stage_seal(
            package,
            stage,
            expected_preflight_receipt_sha256=preflight_receipt_sha256,
            expected_python_executable_sha256=python_executable_sha256,
        )
        raise ControllerError("stage_already_complete")


def _gemini_runner(
    expected_custody_sha256: str | None = None,
    expected_label_manifest_sha256: str | None = None,
    expected_evidence_manifest_sha256: str | None = None,
    expected_sources_endpoint_identity: dict[str, Any] | None = None,
) -> Any:
    path = HERE / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_controller_gemini", path)
    if spec is None or spec.loader is None:
        raise ControllerError("preflight_binding_drift")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not isinstance(expected_custody_sha256, str) or not isinstance(expected_label_manifest_sha256, str):
        raise ControllerError("preflight_binding_drift")
    module.EXPECTED_CUSTODY_SHA256 = expected_custody_sha256
    module.EXPECTED_LABEL_MANIFEST_SHA256 = expected_label_manifest_sha256
    module.EXPECTED_EVIDENCE_MANIFEST_SHA256 = expected_evidence_manifest_sha256 or ""
    module.EXPECTED_SOURCES_ENDPOINT_IDENTITY = _source_identity_hashes(expected_sources_endpoint_identity)
    return module


def revalidate_full_packets(
    package: Path,
    expected_custody_sha256: str,
    expected_label_manifest_sha256: str,
    expected_evidence_manifest_sha256: str,
    expected_label_prompt_sha256s: dict[str, dict[str, str]],
    expected_sources_endpoint_identity: dict[str, Any],
) -> None:
    """Revalidate every reassembled Gemini packet before its stage can seal."""
    runner = _gemini_runner(
        expected_custody_sha256,
        expected_label_manifest_sha256,
        expected_evidence_manifest_sha256,
        expected_sources_endpoint_identity,
    )
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            runner.verify_packet(
                package,
                lane,
                index,
                expected_label_prompt_sha=expected_label_prompt_sha256s["gemini"][lane],
            )


def gemini_missing_ranges(
    package: Path,
    expected_custody_sha256: str,
    expected_label_manifest_sha256: str,
    expected_evidence_manifest_sha256: str,
    expected_label_prompt_sha256s: dict[str, dict[str, str]],
    expected_sources_endpoint_identity: dict[str, Any],
) -> dict[str, list[tuple[int, int]]]:
    """Return only contiguous entirely-unsealed packet ranges; partial seals refuse."""
    runner = _gemini_runner(
        expected_custody_sha256,
        expected_label_manifest_sha256,
        expected_evidence_manifest_sha256,
        expected_sources_endpoint_identity,
    )
    result: dict[str, list[tuple[int, int]]] = {}
    for lane, count in LANES.items():
        missing: list[int] = []
        output = package / runner.OUTPUT / lane
        for index in range(1, count + 1):
            required = [
                output / f"labels-{index:04d}.json",
                output / f"receipt-{index:04d}.json",
                output / f"raw-manifest-{index:04d}.json",
            ]
            present = [path.exists() for path in required]
            if any(present) and not all(present):
                raise ControllerError("partial_or_invalid_seal")
            if all(present):
                try:
                    runner.verify_packet(
                        package,
                        lane,
                        index,
                        expected_label_prompt_sha=expected_label_prompt_sha256s["gemini"][lane],
                    )
                except Exception as exc:
                    raise ControllerError("partial_or_invalid_seal") from exc
            else:
                missing.append(index)
        ranges: list[tuple[int, int]] = []
        for index in missing:
            if not ranges or index != ranges[-1][1] + 1:
                ranges.append((index, index))
            else:
                ranges[-1] = (ranges[-1][0], index)
        result[lane] = ranges
    return result


def _load_bound_runner(label: str, code_paths: dict[str, Path]) -> Any:
    path = code_paths.get(label)
    if path is None or path.is_symlink() or not path.is_file():
        raise ControllerError("preflight_binding_drift")
    spec = importlib.util.spec_from_file_location(f"cycle007_controller_{label}", path)
    if spec is None or spec.loader is None:
        raise ControllerError("preflight_binding_drift")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grok_missing_ranges(
    package: Path,
    runner: Any,
    expected_custody_sha256: str = "",
    expected_label_manifest_sha256: str = "",
    expected_evidence_manifest_sha256: str = "",
    expected_label_prompt_sha256s: dict[str, dict[str, str]] | None = None,
    expected_sources_endpoint_identity: dict[str, Any] | None = None,
) -> dict[str, list[tuple[int, int]]]:
    """Return contiguous unsealed Grok ranges and reject any partial/invalid sealed packet."""
    output_root = getattr(runner, "OUTPUT_ROOT", None)
    if not isinstance(output_root, str) or not callable(getattr(runner, "_receipt_paths", None)):
        raise ControllerError("preflight_binding_drift")
    if expected_custody_sha256:
        runner.EXPECTED_CUSTODY_SHA256 = expected_custody_sha256
    if expected_label_manifest_sha256:
        runner.EXPECTED_LABEL_MANIFEST_SHA256 = expected_label_manifest_sha256
    if expected_evidence_manifest_sha256:
        runner.EXPECTED_EVIDENCE_MANIFEST_SHA256 = expected_evidence_manifest_sha256
    runner.EXPECTED_SOURCES_ENDPOINT_IDENTITY = _source_identity_hashes(expected_sources_endpoint_identity)
    if not _exact_label_prompt_sha256s(expected_label_prompt_sha256s):
        raise ControllerError("preflight_binding_drift")
    assert expected_label_prompt_sha256s is not None
    result: dict[str, list[tuple[int, int]]] = {}
    for lane, count in LANES.items():
        missing: list[int] = []
        for index in range(1, count + 1):
            paths = runner._receipt_paths(package, lane, index)
            if not isinstance(paths, tuple) or len(paths) != 4:
                raise ControllerError("preflight_binding_drift")
            present = [path.exists() for path in paths]
            if any(present) and not all(present):
                raise ControllerError("partial_or_invalid_seal")
            if all(present):
                try:
                    runner.verify_packet(
                        package,
                        lane,
                        index,
                        expected_label_prompt_sha=expected_label_prompt_sha256s["grok"][lane],
                    )
                except Exception as exc:
                    raise ControllerError("partial_or_invalid_seal") from exc
            else:
                missing.append(index)
        ranges: list[tuple[int, int]] = []
        for index in missing:
            if not ranges or index != ranges[-1][1] + 1:
                ranges.append((index, index))
            else:
                ranges[-1] = (ranges[-1][0], index)
        result[lane] = ranges
    return result


def revalidate_grok_full_packets(
    package: Path,
    runner: Any,
    expected_custody_sha256: str = "",
    expected_label_manifest_sha256: str = "",
    expected_evidence_manifest_sha256: str = "",
    expected_grok_executable_sha256: str | None = None,
    expected_label_prompt_sha256s: dict[str, dict[str, str]] | None = None,
    expected_sources_endpoint_identity: dict[str, Any] | None = None,
) -> None:
    if expected_custody_sha256:
        runner.EXPECTED_CUSTODY_SHA256 = expected_custody_sha256
    if expected_label_manifest_sha256:
        runner.EXPECTED_LABEL_MANIFEST_SHA256 = expected_label_manifest_sha256
    if expected_evidence_manifest_sha256:
        runner.EXPECTED_EVIDENCE_MANIFEST_SHA256 = expected_evidence_manifest_sha256
    runner.EXPECTED_SOURCES_ENDPOINT_IDENTITY = _source_identity_hashes(expected_sources_endpoint_identity)
    if expected_grok_executable_sha256 and expected_grok_executable_sha256 != "synthetic":
        runner.EXPECTED_GROK_EXECUTABLE_SHA256 = expected_grok_executable_sha256
    if not _exact_label_prompt_sha256s(expected_label_prompt_sha256s):
        raise ControllerError("preflight_binding_drift")
    assert expected_label_prompt_sha256s is not None
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            runner.verify_packet(
                package,
                lane,
                index,
                expected_label_prompt_sha=expected_label_prompt_sha256s["grok"][lane],
            )


def _revalidate_compare_receipts(
    package: Path, expected_custody_sha256: str, expected_label_manifest_sha256: str
) -> None:
    receipt_file = package / "dual-label-output-cycle007-v1" / "batch-receipt.json"
    receipt = _read_json(receipt_file)
    if (
        receipt.get("schema_version") != "phase3_cycle007_dual_label_batch_receipt_v1"
        or receipt.get("evaluation_cycle_id") != CYCLE
        or receipt.get("custody_receipt_raw_sha256") != expected_custody_sha256
        or receipt.get("manifest_raw_sha256") != expected_label_manifest_sha256
        or receipt.get("text_free") is not True
    ):
        raise ControllerError("stage_execution_failed")
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            pkt_receipt = _read_json(package / "dual-label-output-cycle007-v1" / lane / f"receipt-{index:04d}.json")
            if pkt_receipt.get("schema_version") != "phase3_cycle007_dual_label_packet_receipt_v1":
                raise ControllerError("stage_execution_failed")
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    if receipt.get("receipt_sha256") != digest(canonical(unsigned)):
        raise ControllerError("stage_execution_failed")


def _revalidate_audit_receipts(
    package: Path, expected_custody_sha256: str, expected_label_manifest_sha256: str
) -> None:
    receipt_file = package / "consensus-audit-cycle007-v1" / "batch-receipt.json"
    receipt = _read_json(receipt_file)
    if (
        receipt.get("schema_version") != "phase3_cycle007_consensus_audit_batch_receipt_v1"
        or receipt.get("evaluation_cycle_id") != CYCLE
        or receipt.get("passed") is not True
        or receipt.get("terminal_findings_count") != 0
        or receipt.get("custody_receipt_raw_sha256") != expected_custody_sha256
        or receipt.get("manifest_raw_sha256") != expected_label_manifest_sha256
        or receipt.get("text_free") is not True
    ):
        raise ControllerError("stage_execution_failed")
    clean_audit = _read_json(package / "consensus-audit-cycle007-v1" / "clean-audit-receipt.json")
    risk_review = _read_json(package / "consensus-audit-cycle007-v1" / "risk-review-receipt.json")
    if clean_audit.get("terminal_findings_count") != 0 or risk_review.get("terminal_findings_count") != 0:
        raise ControllerError("stage_execution_failed")
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    if receipt.get("receipt_sha256") != digest(canonical(unsigned)):
        raise ControllerError("stage_execution_failed")


def _revalidate_adjudicate_receipts(
    package: Path, expected_custody_sha256: str, expected_label_manifest_sha256: str
) -> None:
    receipt_file = package / "dual-label-adjudication-cycle007-v1" / "batch-receipt.json"
    receipt = _read_json(receipt_file)
    if (
        receipt.get("schema_version") != "phase3_cycle007_dual_label_adjudication_batch_receipt_v1"
        or receipt.get("evaluation_cycle_id") != CYCLE
        or receipt.get("custody_receipt_raw_sha256") != expected_custody_sha256
        or receipt.get("manifest_raw_sha256") != expected_label_manifest_sha256
        or receipt.get("text_free") is not True
    ):
        raise ControllerError("stage_execution_failed")
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            pkt_receipt = _read_json(
                package / "dual-label-adjudication-cycle007-v1" / "final" / lane / f"receipt-{index:04d}.json"
            )
            if pkt_receipt.get("schema_version") != "phase3_cycle007_dual_label_adjudication_packet_receipt_v1":
                raise ControllerError("stage_execution_failed")
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    if receipt.get("receipt_sha256") != digest(canonical(unsigned)):
        raise ControllerError("stage_execution_failed")


def _revalidate_resolve_receipts(
    package: Path, expected_custody_sha256: str, expected_label_manifest_sha256: str
) -> None:
    receipt_file = package / "dual-label-final-cycle007-v1" / "batch-receipt.json"
    receipt = _read_json(receipt_file)
    if (
        receipt.get("schema_version") != "phase3_cycle007_operator_resolution_batch_receipt_v1"
        or receipt.get("evaluation_cycle_id") != CYCLE
        or receipt.get("unresolved_remaining_count") != 0
        or receipt.get("custody_receipt_raw_sha256") != expected_custody_sha256
        or receipt.get("manifest_raw_sha256") != expected_label_manifest_sha256
        or receipt.get("text_free") is not True
    ):
        raise ControllerError("stage_execution_failed")
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            pkt_receipt = _read_json(
                package / "dual-label-final-cycle007-v1" / "final" / lane / f"receipt-{index:04d}.json"
            )
            if (
                pkt_receipt.get("schema_version") != "phase3_cycle007_operator_resolution_packet_receipt_v1"
                or pkt_receipt.get("unresolved_remaining_count") != 0
            ):
                raise ControllerError("stage_execution_failed")
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    if receipt.get("receipt_sha256") != digest(canonical(unsigned)):
        raise ControllerError("stage_execution_failed")


def _verify_certification_receipt(
    package: Path,
    expected_custody_sha256: str,
    expected_label_manifest_sha256: str,
    expected_evidence_manifest_sha256: str,
) -> None:
    receipt = _read_json(package / "dual-label-final-cycle007-v1" / "certification-receipt.json")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if (
        receipt.get("schema_version") != "phase3_cycle007_label_completion_receipt_v1"
        or receipt.get("evaluation_cycle_id") != CYCLE
        or receipt.get("amendment_sha256") != AMENDMENT_SHA256
        or receipt.get("custody_receipt_raw_sha256") != expected_custody_sha256
        or receipt.get("manifest_raw_sha256") != expected_label_manifest_sha256
        or receipt.get("evidence_manifest_raw_sha256") != expected_evidence_manifest_sha256
        or receipt.get("source_custody_receipt_raw_sha256") != SOURCE_CUSTODY_SHA256
        or receipt.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or receipt.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or receipt.get("unresolved_remaining_count") != 0
        or receipt.get("terminal_findings_count") != 0
        or receipt.get("text_free") is not True
        or receipt.get("receipt_sha256") != digest(canonical(unsigned))
    ):
        raise ControllerError("stage_execution_failed")


def _commands_for_stage(
    package: Path,
    stage: str,
    runner: Path | None,
    *,
    code_paths: dict[str, Path],
    expected_agy_executable_sha256: str | None,
    expected_grok_executable_sha256: str | None = None,
    agy_executable: Path | None = None,
    grok_executable: Path | None = None,
    expected_label_prompt_sha256s: dict[str, dict[str, str]] | None = None,
    expected_custody_sha256: str | None,
    expected_label_manifest_sha256: str | None,
    expected_evidence_manifest_sha256: str | None,
    expected_sources_endpoint_identity: dict[str, Any] | None = None,
    resolution_authorization: Path | None = None,
    resolution_authority_attestation: Path | None = None,
    resolution_authority_root: Path | None = None,
    resolution_nonce_ledger: Path | None = None,
    resolution_advisor_response: Path | None = None,
) -> tuple[list[list[str]], Any | None]:
    agy_executable = agy_executable or AGY
    grok_executable = grok_executable or GROK
    if not _exact_label_prompt_sha256s(expected_label_prompt_sha256s):
        raise ControllerError("preflight_binding_drift")
    assert expected_label_prompt_sha256s is not None
    if stage == "gemini":
        if agy_executable is None:
            raise ControllerError("preflight_binding_drift")
        source_identity_hashes = _source_identity_hashes(expected_sources_endpoint_identity)
        ranges = gemini_missing_ranges(
            package,
            expected_custody_sha256 or "",
            expected_label_manifest_sha256 or "",
            expected_evidence_manifest_sha256 or "",
            expected_label_prompt_sha256s,
            source_identity_hashes,
        )
        return (
            [
                [
                    str(_python_launcher()),
                    str(code_paths["gemini_runner"]),
                    "--package",
                    str(package),
                    "--lane",
                    lane,
                    "--start",
                    str(start),
                    "--end",
                    str(end),
                    "--concurrency",
                    "1",
                    "--request-byte-budget",
                    str(GEMINI_REQUEST_BYTE_BUDGET),
                    "--provider-bin",
                    str(agy_executable),
                    "--expected-agy-executable-sha",
                    expected_agy_executable_sha256 or "",
                    "--expected-custody-sha",
                    expected_custody_sha256 or "",
                    "--expected-label-manifest-sha",
                    expected_label_manifest_sha256 or "",
                    "--expected-evidence-manifest-sha",
                    expected_evidence_manifest_sha256 or "",
                    "--expected-server-code-sha",
                    source_identity_hashes["server_code_sha256"],
                    "--expected-sources-db-sha",
                    source_identity_hashes["sources_db_sha256"],
                    "--expected-vesum-db-sha",
                    source_identity_hashes["vesum_db_sha256"],
                    "--expected-label-prompt-sha",
                    expected_label_prompt_sha256s["gemini"][lane],
                ]
                for lane, lane_ranges in ranges.items()
                for start, end in lane_ranges
            ],
            None,
        )
    assert runner is not None
    if stage == "grok":
        if grok_executable is None:
            raise ControllerError("preflight_binding_drift")
        source_identity_hashes = _source_identity_hashes(expected_sources_endpoint_identity)
        grok = _load_bound_runner("grok_runner", code_paths)
        ranges = grok_missing_ranges(
            package,
            grok,
            expected_custody_sha256 or "",
            expected_label_manifest_sha256 or "",
            expected_evidence_manifest_sha256 or "",
            expected_label_prompt_sha256s,
            source_identity_hashes,
        )
        commands: list[list[str]] = []
        for lane, lane_ranges in ranges.items():
            for start, end in lane_ranges:
                cmd = [
                    str(_python_launcher()),
                    str(runner),
                    "--package",
                    str(package),
                    "--lane",
                    lane,
                    "--start",
                    str(start),
                    "--end",
                    str(end),
                    "--concurrency",
                    "1",
                    "--provider-bin",
                    str(grok_executable),
                    "--expected-custody-sha",
                    expected_custody_sha256 or "",
                    "--expected-label-manifest-sha",
                    expected_label_manifest_sha256 or "",
                    "--expected-evidence-manifest-sha",
                    expected_evidence_manifest_sha256 or "",
                    "--expected-server-code-sha",
                    source_identity_hashes["server_code_sha256"],
                    "--expected-sources-db-sha",
                    source_identity_hashes["sources_db_sha256"],
                    "--expected-vesum-db-sha",
                    source_identity_hashes["vesum_db_sha256"],
                    "--expected-label-prompt-sha",
                    expected_label_prompt_sha256s["grok"][lane],
                ]
                if expected_grok_executable_sha256 and expected_grok_executable_sha256 != "synthetic":
                    cmd.extend(["--expected-grok-executable-sha", expected_grok_executable_sha256])
                commands.append(cmd)
        return (commands, grok)
    common = [str(_python_launcher()), str(runner), "--package", str(package)]
    if stage == "compare":
        return ([[*common, "--all"]], None)
    if stage == "audit":
        if agy_executable is None:
            raise ControllerError("preflight_binding_drift")
        cmd = list(common)
        cmd.extend(["--provider-bin", str(agy_executable)])
        if expected_agy_executable_sha256 and expected_agy_executable_sha256 != "synthetic":
            cmd.extend(["--expected-agy-executable-sha", expected_agy_executable_sha256])
        return ([cmd], None)
    if stage == "adjudicate":
        if agy_executable is None:
            raise ControllerError("preflight_binding_drift")
        cmd = [*common, "--all"]
        cmd.extend(["--provider-bin", str(agy_executable)])
        if expected_agy_executable_sha256 and expected_agy_executable_sha256 != "synthetic":
            cmd.extend(["--expected-agy-executable-sha", expected_agy_executable_sha256])
        return ([cmd], None)
    if stage == "resolve":
        command = [*common, "--all"]
        authority_paths = (
            resolution_authorization,
            resolution_authority_attestation,
            resolution_authority_root,
            resolution_nonce_ledger,
        )
        if any(path is not None for path in authority_paths):
            if any(path is None for path in authority_paths):
                raise ControllerError("preflight_binding_drift")
            command.extend(
                [
                    "--authorization",
                    str(resolution_authorization),
                    "--authority-attestation",
                    str(resolution_authority_attestation),
                    "--authority-root",
                    str(resolution_authority_root),
                    "--nonce-ledger",
                    str(resolution_nonce_ledger),
                ]
            )
            if resolution_advisor_response is not None:
                command.extend(["--advisor-response", str(resolution_advisor_response)])
        elif resolution_advisor_response is not None:
            raise ControllerError("preflight_binding_drift")
        return ([command], None)
    if stage == "certify":
        command = list(common)
        authority_paths = (
            resolution_authorization,
            resolution_authority_attestation,
            resolution_authority_root,
            resolution_nonce_ledger,
        )
        if any(path is not None for path in authority_paths):
            if any(path is None for path in authority_paths):
                raise ControllerError("preflight_binding_drift")
            command.extend(
                [
                    "--resolution-authorization",
                    str(resolution_authorization),
                    "--resolution-authority-attestation",
                    str(resolution_authority_attestation),
                    "--resolution-authority-root",
                    str(resolution_authority_root),
                    "--resolution-nonce-ledger",
                    str(resolution_nonce_ledger),
                ]
            )
        return ([command], None)
    raise ControllerError("preflight_binding_drift")


def _seal(
    package: Path,
    stage: str,
    preflight_receipt_sha256: str,
    python_executable_sha256: str,
) -> None:
    if stage not in STAGES or not _hex64(preflight_receipt_sha256) or not _hex64(python_executable_sha256):
        raise ControllerError("invalid_stage_seal")
    try:
        preflight_path = _control(package) / "preflight-receipt.json"
        _mode(preflight_path, 0o600)
        if sha256(preflight_path) != preflight_receipt_sha256:
            raise ControllerError("invalid_stage_seal")
        _require_python_binding(python_executable_sha256)
    except ControllerError as exc:
        raise ControllerError("invalid_stage_seal") from exc
    preceding: dict[str, str] = {}
    for prior in STAGES[: STAGES.index(stage)]:
        prior_hash, _prior_value = _validate_stage_seal(
            package,
            prior,
            expected_preflight_receipt_sha256=preflight_receipt_sha256,
            expected_python_executable_sha256=python_executable_sha256,
        )
        preceding[prior] = prior_hash
    unsigned = _stage_seal_unsigned(stage, preflight_receipt_sha256, python_executable_sha256, preceding)
    _atomic(
        _stage_seal(package, stage),
        {**unsigned, "seal_sha256": digest(canonical(unsigned))},
    )


def run_stage(
    package: Path,
    stage: str,
    runner: Path | None,
    preflight_receipt_sha256: str,
    *,
    dry_run: bool,
    concurrency: int = 1,
    expected_agy_executable_sha256: str | None = None,
    expected_grok_executable_sha256: str | None = None,
    agy_executable: Path | None = None,
    grok_executable: Path | None = None,
    expected_python_executable_sha256: str | None = None,
    expected_label_prompt_sha256s: dict[str, dict[str, str]] | None = None,
    expected_custody_sha256: str | None = None,
    expected_label_manifest_sha256: str | None = None,
    expected_evidence_manifest_sha256: str | None = None,
    expected_sources_endpoint_identity: dict[str, Any] | None = None,
    code_paths: dict[str, Path] | None = None,
    operator_inspected_count: int | None = None,
    resolution_authorization: Path | None = None,
    resolution_authority_attestation: Path | None = None,
    resolution_authority_root: Path | None = None,
    resolution_nonce_ledger: Path | None = None,
    resolution_advisor_response: Path | None = None,
    execution_lock_fd: int | None = None,
) -> dict[str, Any]:
    _require_contiguous(
        package,
        stage,
        preflight_receipt_sha256,
        expected_python_executable_sha256 or "",
    )
    if concurrency != 1:
        raise ControllerError("concurrency_drift")
    if not _exact_label_prompt_sha256s(expected_label_prompt_sha256s):
        raise ControllerError("preflight_binding_drift")
    assert expected_label_prompt_sha256s is not None
    paths = REQUIRED_CODE_PATHS if code_paths is None else code_paths
    if stage == "gemini":
        if not isinstance(expected_agy_executable_sha256, str) or (
            len(expected_agy_executable_sha256) != 64 and expected_agy_executable_sha256 != "synthetic"
        ):
            raise ControllerError("preflight_binding_drift")
        if (
            not isinstance(expected_custody_sha256, str)
            or not isinstance(expected_label_manifest_sha256, str)
            or not isinstance(expected_evidence_manifest_sha256, str)
        ):
            raise ControllerError("preflight_binding_drift")
    else:
        expected_paths = paths
        label = STAGE_RUNNER_LABELS[stage]
        if (
            runner is None
            or not runner.is_file()
            or runner.is_symlink()
            or expected_paths.get(label) != runner.resolve()
        ):
            raise ControllerError("preflight_binding_drift")
        if stage in ("adjudicate", "audit") and (
            not isinstance(expected_agy_executable_sha256, str)
            or (len(expected_agy_executable_sha256) != 64 and expected_agy_executable_sha256 != "synthetic")
        ):
            raise ControllerError("preflight_binding_drift")
    commands, verification_runner = _commands_for_stage(
        package,
        stage,
        runner.resolve() if runner is not None else None,
        code_paths=paths,
        expected_agy_executable_sha256=expected_agy_executable_sha256,
        expected_grok_executable_sha256=expected_grok_executable_sha256,
        agy_executable=agy_executable,
        grok_executable=grok_executable,
        expected_label_prompt_sha256s=expected_label_prompt_sha256s,
        expected_custody_sha256=expected_custody_sha256,
        expected_label_manifest_sha256=expected_label_manifest_sha256,
        expected_evidence_manifest_sha256=expected_evidence_manifest_sha256,
        expected_sources_endpoint_identity=expected_sources_endpoint_identity,
        resolution_authorization=resolution_authorization,
        resolution_authority_attestation=resolution_authority_attestation,
        resolution_authority_root=resolution_authority_root,
        resolution_nonce_ledger=resolution_nonce_ledger,
        resolution_advisor_response=resolution_advisor_response,
    )
    if dry_run:
        return {
            "ok": True,
            "stage": stage,
            "command_count": len(commands),
            "concurrency": 1,
            "text_free": True,
        }
    for command in commands:
        python_target = _require_python_binding(expected_python_executable_sha256 or "")
        # Bind exec to the verified target while argv[0] retains the venv launcher
        # that CPython uses to locate pyvenv.cfg and its installed dependencies.
        return_code, failure_status = _run_stage_subprocess(
            command,
            executable=python_target,
            pass_fds=() if execution_lock_fd is None else (execution_lock_fd,),
        )
        if return_code != 0:
            raise ControllerError(_runner_failure_code(failure_status))
        _require_python_binding(expected_python_executable_sha256 or "")
        if any(path.exists() for path in _stage_stop_paths(package)):
            raise ControllerError("provider_stop_present")

    if stage == "gemini":
        revalidate_full_packets(
            package,
            expected_custody_sha256 or "",
            expected_label_manifest_sha256 or "",
            expected_evidence_manifest_sha256 or "",
            expected_label_prompt_sha256s,
            _source_identity_hashes(expected_sources_endpoint_identity),
        )
    elif stage == "grok":
        revalidate_grok_full_packets(
            package,
            verification_runner,
            expected_custody_sha256 or "",
            expected_label_manifest_sha256 or "",
            expected_evidence_manifest_sha256 or "",
            expected_grok_executable_sha256,
            expected_label_prompt_sha256s,
            _source_identity_hashes(expected_sources_endpoint_identity),
        )
    elif stage == "compare":
        _revalidate_compare_receipts(package, expected_custody_sha256 or "", expected_label_manifest_sha256 or "")
    elif stage == "audit":
        _revalidate_audit_receipts(package, expected_custody_sha256 or "", expected_label_manifest_sha256 or "")
    elif stage == "adjudicate":
        _revalidate_adjudicate_receipts(package, expected_custody_sha256 or "", expected_label_manifest_sha256 or "")
    elif stage == "resolve":
        _revalidate_resolve_receipts(package, expected_custody_sha256 or "", expected_label_manifest_sha256 or "")
    elif stage == "certify":
        _verify_certification_receipt(
            package,
            expected_custody_sha256 or "",
            expected_label_manifest_sha256 or "",
            expected_evidence_manifest_sha256 or "",
        )
    if any(path.exists() for path in _stage_stop_paths(package)):
        raise ControllerError("provider_stop_present")
    _require_python_binding(expected_python_executable_sha256 or "")
    _seal(package, stage, preflight_receipt_sha256, expected_python_executable_sha256 or "")
    return {"ok": True, "stage": stage, "text_free": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("preflight", "status", "plan", "run"),
        help="install identity, inspect, dry-run, or execute exactly one stage",
    )
    parser.add_argument("--package", type=Path, required=True, help="explicit 0700 operator-owned package")
    parser.add_argument(
        "--lock", type=Path, required=True, help="explicit 0600 controller lock outside disposable worktrees"
    )
    parser.add_argument("--preflight-receipt", type=Path, required=True, help="text-free hash-bound preflight receipt")
    parser.add_argument(
        "--gemini-canary-receipt",
        "--public-canary-gemini",
        type=Path,
        help="0600 real-provider-attested public Gemini canary receipt",
    )
    parser.add_argument(
        "--grok-canary-receipt",
        "--public-canary-grok",
        type=Path,
        help="0600 real-provider-attested public Grok canary receipt",
    )
    parser.add_argument("--agy-executable", type=Path, required=True, help="explicit reviewed AGY executable")
    parser.add_argument("--grok-executable", type=Path, required=True, help="explicit reviewed Grok executable")
    parser.add_argument(
        "--public-canary-receipt",
        type=Path,
        help="public canary receipt alias",
    )
    parser.add_argument(
        "--code-path", action="append", default=[], help="required LABEL=/absolute/public/code/path binding; repeat"
    )
    parser.add_argument("--stage", choices=STAGES, help="stage for plan/run")
    parser.add_argument(
        "--runner", type=Path, help="non-Gemini stage runner; Gemini uses its reviewed packet-batch CLI"
    )
    parser.add_argument("--concurrency", type=int, default=1, help="must remain one for fail-stop packet execution")
    parser.add_argument(
        "--operator-inspected-count",
        type=int,
        help="optional operator inspected count parameter",
    )
    parser.add_argument("--resolution-authorization", type=Path, help="external 0600 authorization receipt")
    parser.add_argument(
        "--resolution-authority-attestation",
        type=Path,
        help="external 0600 authority attestation bound to the authorization",
    )
    parser.add_argument("--resolution-authority-root", type=Path, help="external operator-owned 0700 authority root")
    parser.add_argument(
        "--resolution-nonce-ledger", type=Path, help="separate external operator-owned 0700 nonce ledger"
    )
    parser.add_argument("--resolution-advisor-response", type=Path, help="external advisor response, when applicable")
    args = parser.parse_args()
    result: dict[str, Any]
    try:
        package = args.package.resolve()
        code_paths = _parse_code_paths(args.code_path)
        gemini_canary = args.gemini_canary_receipt or args.public_canary_receipt
        grok_canary = args.grok_canary_receipt
        if gemini_canary is None or grok_canary is None:
            raise ControllerError("preflight_binding_drift")
        args.lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with args.lock.open("a+") as lock:
            os.chmod(args.lock, 0o600)
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ControllerError("controller_already_running") from exc
            proof = preflight(
                package,
                args.preflight_receipt.resolve(),
                code_paths,
                gemini_canary.resolve(),
                grok_canary.resolve(),
                args.agy_executable,
                args.grok_executable,
            )
            execution_lock_fd = _inherited_execution_lock_fd()
            if args.action == "preflight":
                result = proof
            elif args.action == "status":
                result = {"ok": True, **status(package), **proof}
            else:
                if args.stage is None or (args.stage != "gemini" and args.runner is None):
                    raise ControllerError("stage_runner_required")
                result = run_stage(
                    package,
                    args.stage,
                    args.runner,
                    proof["preflight_receipt_sha256"],
                    dry_run=args.action == "plan",
                    concurrency=args.concurrency,
                    expected_agy_executable_sha256=proof["expected_agy_executable_sha256"],
                    expected_grok_executable_sha256=proof.get("expected_grok_executable_sha256"),
                    agy_executable=args.agy_executable,
                    grok_executable=args.grok_executable,
                    expected_python_executable_sha256=proof["expected_python_executable_sha256"],
                    expected_label_prompt_sha256s=proof["expected_label_prompt_sha256s"],
                    expected_custody_sha256=proof["expected_custody_sha256"],
                    expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
                    expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
                    expected_sources_endpoint_identity=proof["sources_endpoint_identity"],
                    code_paths=code_paths,
                    operator_inspected_count=args.operator_inspected_count,
                    resolution_authorization=args.resolution_authorization,
                    resolution_authority_attestation=args.resolution_authority_attestation,
                    resolution_authority_root=args.resolution_authority_root,
                    resolution_nonce_ledger=args.resolution_nonce_ledger,
                    resolution_advisor_response=args.resolution_advisor_response,
                    execution_lock_fd=execution_lock_fd,
                )
    except ControllerError as exc:
        result = {"ok": False, "failure_code": str(exc), "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "controller_execution_failure", "text_free": True}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
