#!/usr/bin/env python3
"""Compile the frozen Cycle-007 evidence package through a managed local MCP.

This is intentionally a receipt-only CLI.  It accepts no row content and
emits no paths, source responses, prompts, exception details, or raw logs.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / ".mcp" / "servers" / "sources" / "server.py"
MCP_START_TIMEOUT_SECONDS = 15.0
_SERVER_IDENTITY_TOOL = "mcp_server_identity"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import (
    phase3_cycle007_evidence_compile_throughput as throughput,
)
from scripts.projects.open_model_data import (
    phase3_cycle007_evidence_compiler as compiler,
)
from scripts.projects.open_model_data import (
    phase3_cycle007_evidence_contract as evidence_contract,
)
from scripts.projects.open_model_data import (
    phase3_cycle007_materializer as materializer,
)

_CONTRACT_FAILURE_CODES = {
    "source_binding_drift": "compile_source_binding_drift",
    "manifest_binding_drift": "compile_manifest_binding_drift",
    "custody_binding_drift": "compile_custody_binding_drift",
    "packet_order_failure": "compile_packet_order_failure",
    "packet_binding_drift": "compile_packet_binding_drift",
    "source_content_binding_drift": "compile_source_content_binding_drift",
    "label_leak_detected": "compile_label_leak_detected",
    "identity_uniqueness_failure": "compile_identity_uniqueness_failure",
    "ordered_identity_commitment_failure": "compile_ordered_identity_commitment_failure",
}


class RunnerError(ValueError):
    """A closed, public-safe runner failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _SilentArgumentParser(argparse.ArgumentParser):
    """Reject bad arguments without argparse writing user-controlled values."""

    def error(self, message: str) -> None:
        del message
        raise RunnerError("argument_invalid")


def _absolute_path(value: Path) -> Path:
    if not value.is_absolute():
        raise RunnerError("path_not_absolute")
    return Path(os.path.abspath(os.fspath(value)))


def _lstat_mode(path: Path) -> int:
    try:
        return stat.S_IMODE(path.lstat().st_mode)
    except OSError as exc:
        raise RunnerError("path_unavailable") from exc


def _validate_paths(package: Path, source_manifest: Path, output: Path) -> tuple[Path, Path, Path]:
    package = _absolute_path(package)
    source_manifest = _absolute_path(source_manifest)
    output = _absolute_path(output)
    if package.is_symlink() or not package.is_dir():
        raise RunnerError("package_invalid")
    if _lstat_mode(package) != 0o700:
        raise RunnerError("package_mode_invalid")
    if source_manifest == package / "manifest.json" or source_manifest.name != "label-manifest.json":
        raise RunnerError("source_manifest_path_invalid")
    source_parent = source_manifest.parent
    if source_parent.is_symlink() or not source_parent.is_dir() or _lstat_mode(source_parent) != 0o700:
        raise RunnerError("source_manifest_parent_invalid")
    if source_manifest.is_symlink() or not source_manifest.is_file():
        raise RunnerError("source_manifest_invalid")
    if _lstat_mode(source_manifest) != 0o600:
        raise RunnerError("source_manifest_mode_invalid")
    if output != package / "evidence":
        raise RunnerError("output_path_invalid")
    if output.is_symlink():
        raise RunnerError("output_symlink")
    if os.path.lexists(output) and (
        not output.is_dir()
        or _lstat_mode(output) != 0o700
        or output.lstat().st_uid != os.geteuid()
    ):
        raise RunnerError("output_exists")
    return package, source_manifest, output


def _validate_endpoint(endpoint: str) -> tuple[str, int]:
    parsed = urlparse(endpoint)
    try:
        port = parsed.port
    except ValueError as exc:
        raise RunnerError("endpoint_invalid") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or port is None
        or not 1024 <= port <= 65535
        or parsed.path != "/mcp"
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
        or endpoint != f"http://127.0.0.1:{port}/mcp"
    ):
        raise RunnerError("endpoint_invalid")
    return "127.0.0.1", port


def _endpoint_is_listening(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _runtime_python() -> Path:
    """Return the active venv entry point without resolving its symlink.

    A resolved virtualenv executable points to the base interpreter and loses
    the worktree's installed packages.  The lexical entry point is therefore
    validated but deliberately retained for the child server command.
    """
    executable = Path(os.path.abspath(sys.executable))
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise RunnerError("reviewed_python_executable_unavailable")
    return executable


def _expected_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RunnerError("reviewed_commit_unavailable") from exc
    commit = completed.stdout.strip()
    if len(commit) != 40:
        raise RunnerError("reviewed_commit_unavailable")
    return commit


def _stop_reviewed_sources_server(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _start_reviewed_sources_server(endpoint: str) -> subprocess.Popen[bytes]:
    host, port = _validate_endpoint(endpoint)
    if _endpoint_is_listening(host, port):
        raise RunnerError("endpoint_occupied")
    if SERVER_PATH.is_symlink() or not SERVER_PATH.is_file():
        raise RunnerError("reviewed_server_unavailable")
    if compiler.DEFAULT_SERVER_CODE.resolve(strict=True) != SERVER_PATH.resolve(strict=True):
        raise RunnerError("reviewed_server_path_drift")
    expected_commit = _expected_commit()
    process = subprocess.Popen(
        [
            str(_runtime_python()),
            str(SERVER_PATH),
            "--standalone",
            "--host",
            host,
            "--port",
            str(port),
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
        start_new_session=True,
    )
    health_url = endpoint.removesuffix("/mcp") + "/health"
    try:
        deadline = time.monotonic() + MCP_START_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RunnerError("server_start_failed")
            try:
                with urllib.request.urlopen(health_url, timeout=1) as response:
                    payload = json.loads(response.read())
                if payload.get("status") == "ok" and payload.get("commit_sha") == expected_commit:
                    return process
            except (OSError, urllib.error.URLError, json.JSONDecodeError):
                pass
            time.sleep(0.1)
        raise RunnerError("server_start_timeout")
    except BaseException:
        _stop_reviewed_sources_server(process)
        raise


@contextlib.contextmanager
def _admit_reviewed_resume_root(package: Path, output: Path):
    """Admit only the reviewed runtime resume root without changing compiler identity."""
    original_top_level = materializer.OUTPUT_TOP_LEVEL
    resume_root = throughput.resume_root_for(output)
    if resume_root.parent != package:
        raise RunnerError("resume_metadata_invalid")
    if not os.path.lexists(resume_root):
        yield
        return
    try:
        info = resume_root.lstat()
    except OSError as exc:
        raise RunnerError("resume_metadata_invalid") from exc
    if (
        not stat.S_ISDIR(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or stat.S_IMODE(info.st_mode) != compiler.PRIVATE_DIR_MODE
        or info.st_uid != os.geteuid()
    ):
        raise RunnerError("resume_metadata_invalid")

    # This runner is a single-compile process. Keep the process-wide admission
    # scoped to that one call and always restore it; concurrent in-process
    # compilation would require a call-scoped materializer API instead.
    materializer.OUTPUT_TOP_LEVEL = original_top_level | {resume_root.name}
    try:
        yield
    finally:
        materializer.OUTPUT_TOP_LEVEL = original_top_level


def _normalize_resume_identity_ledger(
    output: Path,
    client: compiler.LocalMcpSourcesClient,
) -> None:
    """Normalize a live receipt while holding the compiler's exclusive lock."""
    root = throughput.resume_root_for(output)
    if not os.path.lexists(root):
        return
    with throughput.exclusive_resume_lock(root):
        _normalize_resume_identity_ledger_locked(output, client)


def _normalize_resume_identity_ledger_locked(
    output: Path,
    client: compiler.LocalMcpSourcesClient,
) -> None:
    """Remove validation-only identity calls before the frozen compiler resumes.

    The compiler attests the endpoint once when each process starts and appends
    that call while restoring the prior ledger. Earlier resumptions therefore
    accumulated identical identity calls even though the final evidence
    contract requires exactly one. The outer runner owns this checkpoint-safe
    normalization because changing either hashed resume module would invalidate
    the existing durable prefix.
    """
    root = throughput.resume_root_for(output)
    progress_path = root / throughput.PROGRESS_NAME
    if not os.path.lexists(progress_path):
        return
    receipt = throughput.read_progress(progress_path)
    if set(receipt) != throughput.PROGRESS_REQUIRED_KEYS:
        raise RunnerError("resume_progress_invalid")
    unsigned_receipt = {key: value for key, value in receipt.items() if key != "progress_sha256"}
    if receipt.get("progress_sha256") != evidence_contract.sha256_value(unsigned_receipt):
        raise RunnerError("resume_progress_invalid")

    prior_attestation = receipt.get("mcp_transport_attestation")
    prior_records = receipt.get("mcp_call_records")
    current_attestation = client.transport_attestation()
    current_records = client.transport_call_records()
    if not isinstance(prior_attestation, Mapping) or not isinstance(prior_records, list):
        raise RunnerError("resume_transport_invalid")
    if len(current_records) != 1 or current_records[0].get("tool") != _SERVER_IDENTITY_TOOL:
        raise RunnerError("resume_identity_invalid")
    throughput.validate_transport_state(
        prior_attestation,
        prior_records,
        expected_transport=str(current_attestation["transport"]),
        expected_endpoint_sha256=str(current_attestation["endpoint_sha256"]),
        expected_tool_set_sha256=str(current_attestation["required_tool_set_sha256"]),
    )

    current_identity = current_records[0]
    current_fingerprint = (
        current_identity["tool"],
        current_identity["arguments_sha256"],
        current_identity["response_sha256"],
    )
    for record in prior_records:
        if record.get("tool") != _SERVER_IDENTITY_TOOL:
            continue
        if (
            record["tool"],
            record["arguments_sha256"],
            record["response_sha256"],
        ) != current_fingerprint:
            raise RunnerError("resume_identity_drift")

    normalized_records = [
        {
            "ordinal": ordinal,
            "tool": record["tool"],
            "arguments_sha256": record["arguments_sha256"],
            "response_sha256": record["response_sha256"],
        }
        for ordinal, record in enumerate(
            (record for record in prior_records if record.get("tool") != _SERVER_IDENTITY_TOOL),
            start=1,
        )
    ]
    commitment, next_ordinal = throughput.extend_serial_call_commitment(
        throughput.initial_call_commitment(),
        normalized_records,
        starting_ordinal=1,
    )
    if next_ordinal != len(normalized_records) + 1:
        raise RunnerError("resume_transport_invalid")
    counts_by_tool = Counter(str(record["tool"]) for record in normalized_records)
    normalized_attestation = dict(prior_attestation)
    normalized_attestation.update(
        {
            "tool_call_count": len(normalized_records),
            "counts_by_tool": dict(sorted(counts_by_tool.items())),
            "server_identity_call_count": 0,
            "ordered_call_commitment_sha256": commitment,
        }
    )
    throughput.validate_transport_state(
        normalized_attestation,
        normalized_records,
        expected_transport=str(current_attestation["transport"]),
        expected_endpoint_sha256=str(current_attestation["endpoint_sha256"]),
        expected_tool_set_sha256=str(current_attestation["required_tool_set_sha256"]),
    )
    normalized_receipt = dict(receipt)
    normalized_receipt["mcp_transport_attestation"] = normalized_attestation
    normalized_receipt["mcp_call_records"] = normalized_records
    normalized_receipt["progress_sha256"] = evidence_contract.sha256_value(
        {key: value for key, value in normalized_receipt.items() if key != "progress_sha256"}
    )
    throughput.write_progress(root, normalized_receipt)


def _compile(package: Path, source_manifest: Path, output: Path, endpoint: str) -> dict[str, Any]:
    process: subprocess.Popen[bytes] | None = None
    try:
        process = _start_reviewed_sources_server(endpoint)
        with (
            compiler.LocalMcpSourcesClient(endpoint_url=endpoint) as client,
            _admit_reviewed_resume_root(package, output),
        ):
            _normalize_resume_identity_ledger(output, client)
            manifest = compiler.compile_cycle007_package(
                package,
                source_manifest,
                client,
                output,
                fixture=False,
            )
    except RunnerError:
        raise
    except Exception as exc:
        raise RunnerError(_compile_failure_code(exc)) from exc
    finally:
        _stop_reviewed_sources_server(process)
    try:
        return {
            "text_free": True,
            "ok": True,
            "packet_count": manifest["packet_count"],
            "row_count": manifest["row_count"],
            "manifest_sha256": manifest["manifest_sha256"],
            "network_lookups_performed": manifest["network_lookups_performed"],
        }
    except (KeyError, TypeError) as exc:
        raise RunnerError("compile_receipt_invalid") from exc


def _compile_failure_code(exc: Exception) -> str:
    """Reduce compiler failures to a closed code without exposing exception text."""
    if isinstance(exc, compiler.McpTransportError):
        return "compile_sources_transport_failed"
    if isinstance(exc, compiler.LocalMcpSourcesClientError):
        return "compile_sources_client_failed"
    if isinstance(exc, materializer.MaterializationError):
        return "compile_materialization_failed"
    if isinstance(exc, evidence_contract.EvidenceContractError):
        return _CONTRACT_FAILURE_CODES.get(str(exc), "compile_evidence_contract_failed")
    if isinstance(exc, throughput.ThroughputResumeError):
        return "compile_resume_failed"
    return "compile_failed"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = _SilentArgumentParser(add_help=False)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mcp-endpoint", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
        package, source_manifest, output = _validate_paths(args.package, args.source_manifest, args.output)
        _validate_endpoint(args.mcp_endpoint)
        result = _compile(package, source_manifest, output, args.mcp_endpoint)
        status = 0
    except RunnerError as exc:
        result = {"text_free": True, "ok": False, "failure_code": exc.code}
        status = 1
    except Exception:
        result = {"text_free": True, "ok": False, "failure_code": "internal_failure"}
        status = 1
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
