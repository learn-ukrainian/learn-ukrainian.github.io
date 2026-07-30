#!/usr/bin/env python3
"""Run a source-only UA evaluation packet through an arbitrary model command.

This module deliberately knows nothing about gold data or scoring. It validates
the public request packet, invokes a caller-supplied command from retained
directories outside the repository, and emits strictly shaped output plus
resumable provenance receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
REQUEST_SCHEMA = "ua_eval_generation_requests.v1"
STATE_SCHEMA = "ua_eval_model_batch_state.v1"
CONFIG_SCHEMA = "ua_eval_model_run_config.v1"
METADATA_SCHEMA = "ua_eval_model_run_metadata.v1"
RUNNER_VERSION = "ua_eval_provider_neutral_batch_runner.v1"
EXPECTED_REQUEST_COUNT = 677
GOLD_FIELDS = frozenset(
    {
        "answer",
        "edit",
        "edits",
        "gold",
        "reference",
        "references",
        "target",
        "targets",
    }
)
HEADER_FIELDS = frozenset(
    {
        "type",
        "schema_version",
        "manifest_id",
        "manifest_payload_sha256",
        "prompt_path",
        "prompt_sha256",
        "input_fields",
        "gold_fields_supplied",
        "request_count",
    }
)
REQUEST_FIELDS = frozenset(
    {
        "type",
        "item_id",
        "source",
        "source_sha256",
        "prompt_sha256",
        "request_sha256",
    }
)
DECODING_FIELDS = frozenset(
    {
        "temperature",
        "top_p",
        "top_k",
        "seed",
        "max_output_tokens",
        "stop",
        "safety",
    }
)
CONFIG_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "provider",
        "route",
        "model",
        "model_version",
        "alias_resolution",
        "decoding",
        "command_identity",
    }
)
ALIAS_FIELDS = frozenset({"requested", "resolved", "evidence"})
COMMAND_IDENTITY_FIELDS = frozenset({"name", "version"})
ENV_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")
THOUGHT_WRAPPER = re.compile(
    r"^\s*<(?:think|thought)>.*?</(?:think|thought)>\s*",
    re.DOTALL | re.IGNORECASE,
)
JSON_FENCE = re.compile(
    r"\A```(?:json)?[ \t]*\r?\n(?P<body>.*)\r?\n```[ \t]*\Z",
    re.DOTALL | re.IGNORECASE,
)


class RunnerError(ValueError):
    """The public input, provider output, or resumable state is invalid."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _publish_text(path: Path, text: str) -> None:
    """Create an immutable receipt, or verify an identical existing receipt."""

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RunnerError(f"cannot validate existing immutable receipt: {path}") from exc
        if existing != text:
            raise RunnerError(f"refusing to replace a different immutable receipt: {path}") from None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RunnerError(f"cannot read JSONL: {path}") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            raise RunnerError(f"blank JSONL line {number}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RunnerError(f"invalid JSONL line {number}") from exc
        if not isinstance(row, dict):
            raise RunnerError(f"JSONL line {number} is not an object")
        rows.append(row)
    if not rows:
        raise RunnerError("request packet is empty")
    return rows


def load_source_only_packet(path: Path) -> tuple[dict[str, Any], list[dict[str, str]], str]:
    """Load the exact public request packet without manifest or gold access."""

    rows = _read_jsonl(path)
    header = rows[0]
    if (
        set(header) != HEADER_FIELDS
        or header.get("type") != "request_run"
        or header.get("schema_version") != REQUEST_SCHEMA
    ):
        raise RunnerError("request header does not match the source-only schema")
    if header["gold_fields_supplied"] != [] or header["input_fields"] != [
        "item_id",
        "source",
        "source_sha256",
        "prompt_sha256",
    ]:
        raise RunnerError("request header violates the gold firewall")
    if header["request_count"] != EXPECTED_REQUEST_COUNT or len(rows) - 1 != EXPECTED_REQUEST_COUNT:
        raise RunnerError("request packet must contain exactly 677 request rows")
    for field in ("manifest_id", "prompt_path"):
        if not isinstance(header[field], str) or not header[field]:
            raise RunnerError(f"request header has empty {field}")
    if not _is_hash(header["manifest_payload_sha256"]) or not _is_hash(header["prompt_sha256"]):
        raise RunnerError("request header hash is malformed")

    requests: list[dict[str, str]] = []
    seen: set[str] = set()
    for number, row in enumerate(rows[1:], 2):
        if GOLD_FIELDS & set(row):
            raise RunnerError(f"request row {number} contains a gold-shaped field")
        if set(row) != REQUEST_FIELDS or row.get("type") != "request":
            raise RunnerError(f"request row {number} contains unknown or missing fields")
        if not all(isinstance(row[field], str) for field in REQUEST_FIELDS - {"type"}):
            raise RunnerError(f"request row {number} contains non-string values")
        item_id = row["item_id"]
        if not item_id or item_id in seen:
            raise RunnerError(f"request row {number} has missing or duplicate item_id")
        if not row["source"] or row["prompt_sha256"] != header["prompt_sha256"]:
            raise RunnerError(f"request row {number} source or prompt hash mismatch")
        payload = {field: row[field] for field in ("item_id", "source", "source_sha256", "prompt_sha256")}
        if not _is_hash(row["source_sha256"]) or not _is_hash(row["request_sha256"]):
            raise RunnerError(f"request row {number} has malformed hashes")
        if (
            _sha256_text(row["source"]) != row["source_sha256"]
            or _sha256_text(_canonical_json(payload)) != row["request_sha256"]
        ):
            raise RunnerError(f"request row {number} hash validation failed")
        seen.add(item_id)
        requests.append({"item_id": item_id, "source": row["source"]})
    packet_sha256 = _sha256_text("\n".join(_canonical_json(row) for row in rows))
    return header, requests, packet_sha256


def _nonempty_string_object(value: Any, required: frozenset[str], label: str) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != required
        or any(not isinstance(value[field], str) or not value[field] for field in required)
    ):
        raise RunnerError(f"run config {label} must declare {sorted(required)}")


def load_run_config(path: Path) -> dict[str, Any]:
    """Load exact provider, model, route, alias, decoding, and tool metadata."""

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError("cannot read required run config JSON") from exc
    if (
        not isinstance(config, dict)
        or set(config) - (CONFIG_FIELDS | {"auth_environment"})
        or not CONFIG_FIELDS.issubset(config)
        or config.get("schema_version") != CONFIG_SCHEMA
    ):
        raise RunnerError("run config has missing or unknown fields")
    for field in CONFIG_FIELDS - {
        "schema_version",
        "alias_resolution",
        "command_identity",
        "decoding",
    }:
        if not isinstance(config[field], str) or not config[field]:
            raise RunnerError(f"run config has empty {field}")
    _nonempty_string_object(config["alias_resolution"], ALIAS_FIELDS, "alias_resolution")
    _nonempty_string_object(
        config["command_identity"],
        COMMAND_IDENTITY_FIELDS,
        "command_identity",
    )
    if not isinstance(config["decoding"], dict) or set(config["decoding"]) != DECODING_FIELDS:
        raise RunnerError("run config must declare every decoding field")
    auth = config.get("auth_environment", [])
    if not isinstance(auth, list) or any(not isinstance(name, str) or not ENV_NAME.fullmatch(name) for name in auth):
        raise RunnerError("run config auth_environment must contain environment variable names")
    return config


def _child_environment(auth_names: Sequence[str]) -> dict[str, str]:
    allowed = {
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "TMPDIR",
        "XDG_CONFIG_HOME",
    }
    allowed.update(auth_names)
    return {name: value for name, value in os.environ.items() if name in allowed}


def _temporary_parent() -> Path:
    candidates = (Path(tempfile.gettempdir()), Path("/tmp"))
    root = ROOT.resolve()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if not resolved.is_relative_to(root):
            return resolved
    raise RunnerError("no scratch directory is available outside the repository")


def _batch_prompt(instruction: str, batch: Sequence[Mapping[str, str]]) -> str:
    payload = {
        "instruction": instruction,
        "records": [{"item_id": row["item_id"], "source": row["source"]} for row in batch],
    }
    return (
        "Return exactly one JSON object with exactly this shape: "
        '{"responses":[{"item_id":"...","raw_response":"..."}]}. '
        "Return one row for every supplied item_id in the same order. "
        "Do not add fields, explanations, or code fences.\n\n" + _canonical_json(payload)
    )


def _parse_exact_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        match = JSON_FENCE.fullmatch(candidate)
        if match is None:
            raise RunnerError("provider response contains a non-exact code fence")
        candidate = match.group("body").strip()
    if not candidate.startswith("{"):
        unwrapped = THOUGHT_WRAPPER.sub("", candidate, count=1)
        if unwrapped == candidate:
            raise RunnerError("provider response is not a JSON object")
        candidate = unwrapped.strip()
    try:
        decoder = json.JSONDecoder()
        value, end = decoder.raw_decode(candidate)
    except json.JSONDecodeError as exc:
        raise RunnerError("provider response contains malformed JSON") from exc
    if candidate[end:].strip() or not isinstance(value, dict):
        raise RunnerError("provider response is not one exact JSON object")
    return value


def _assistant_text_from_event(event: Any) -> str | None:
    if not isinstance(event, dict):
        return None
    if event.get("type") == "text":
        part = event.get("part")
        if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
            return part["text"]
    if event.get("role") == "assistant":
        content = event.get("text", event.get("content"))
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            fragments = [
                part.get("text") for part in content if isinstance(part, dict) and isinstance(part.get("text"), str)
            ]
            if fragments:
                return "".join(fragments)
    for value in event.values():
        if isinstance(value, dict):
            found = _assistant_text_from_event(value)
            if found is not None:
                return found
    return None


def _validate_provider_payload(
    payload: Mapping[str, Any],
    expected_ids: Sequence[str],
) -> list[dict[str, str]]:
    if set(payload) != {"responses"} or not isinstance(payload["responses"], list):
        raise RunnerError("provider response must contain exactly a responses list")
    responses = payload["responses"]
    if len(responses) != len(expected_ids):
        raise RunnerError("provider response count does not match the batch")
    normalized: list[dict[str, str]] = []
    for row, expected_id in zip(responses, expected_ids, strict=True):
        if not isinstance(row, dict) or set(row) != {"item_id", "raw_response"}:
            raise RunnerError("provider response row has unknown or missing fields")
        if not isinstance(row["item_id"], str) or not isinstance(row["raw_response"], str):
            raise RunnerError("provider response row values must be strings")
        if row["item_id"] != expected_id:
            raise RunnerError("provider response IDs must exactly match requested order")
        normalized.append({"item_id": row["item_id"], "raw_response": row["raw_response"]})
    return normalized


def parse_provider_response(
    raw_text: str,
    expected_ids: Sequence[str],
) -> list[dict[str, str]]:
    """Accept direct JSON or the final assistant text in an NDJSON event stream."""

    try:
        payload = _parse_exact_object(raw_text)
        if set(payload) == {"responses"}:
            return _validate_provider_payload(payload, expected_ids)
    except RunnerError:
        payload = None
    if payload is None or set(payload) != {"responses"}:
        assistant_text: str | None = None
        try:
            for line in raw_text.splitlines():
                if line.strip():
                    found = _assistant_text_from_event(json.loads(line))
                    if found is not None:
                        assistant_text = found
        except json.JSONDecodeError:
            raise RunnerError("provider response is not a JSON response or NDJSON event stream") from None
        if assistant_text is None:
            raise RunnerError("provider response has no assistant text event")
        payload = _parse_exact_object(assistant_text)
    return _validate_provider_payload(payload, expected_ids)


def _subprocess_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _write_process_receipts(
    invocation_cwd: Path,
    *,
    attempted_at: str,
    returncode: int | None,
    stdout: str,
    stderr: str,
) -> dict[str, Any]:
    stdout_sha256 = _sha256_text(stdout)
    stderr_sha256 = _sha256_text(stderr)
    _publish_text(invocation_cwd / "stdout.txt", stdout)
    _publish_text(invocation_cwd / "stderr.txt", stderr)
    receipt = {
        "attempted_at": attempted_at,
        "finished_at": _now(),
        "returncode": returncode,
        "stdout_sha256": stdout_sha256,
        "stderr_sha256": stderr_sha256,
    }
    _publish_text(
        invocation_cwd / "process-receipt.json",
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return receipt


def _write_acceptance_receipt(
    invocation_cwd: Path,
    *,
    accepted: bool,
    error_class: str | None = None,
    message: str | None = None,
) -> None:
    receipt = {
        "accepted": accepted,
        "error_class": error_class,
        "message": message,
        "recorded_at": _now(),
    }
    _publish_text(
        invocation_cwd / "acceptance-receipt.json",
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _state_path(state_dir: Path, batch_index: int) -> Path:
    return state_dir / f"batch-{batch_index:04d}.json"


def _load_state(
    path: Path,
    *,
    binding_sha256: str,
    batch_sha256: str,
    expected_ids: Sequence[str],
) -> dict[str, Any]:
    try:
        state_text = path.read_text(encoding="utf-8")
        state = json.loads(state_text)
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(f"cannot validate completed state {path.name}") from exc
    required = {
        "schema_version",
        "binding_sha256",
        "batch_sha256",
        "raw_provider_output",
        "raw_provider_output_sha256",
        "responses",
        "started_at",
        "completed_at",
        "attempts",
        "failed_attempts",
    }
    if not isinstance(state, dict) or set(state) != required:
        raise RunnerError(f"completed state schema mismatch: {path.name}")
    if state["schema_version"] != STATE_SCHEMA:
        raise RunnerError(f"completed state version mismatch: {path.name}")
    if state["binding_sha256"] != binding_sha256:
        raise RunnerError(f"completed state binding mismatch: {path.name}")
    if state["batch_sha256"] != batch_sha256:
        raise RunnerError(f"completed state batch mismatch: {path.name}")
    if (
        not isinstance(state["raw_provider_output"], str)
        or _sha256_text(state["raw_provider_output"]) != state["raw_provider_output_sha256"]
    ):
        raise RunnerError(f"completed state raw output mismatch: {path.name}")
    parsed = parse_provider_response(state["raw_provider_output"], expected_ids)
    if (
        state["responses"] != parsed
        or not isinstance(state["attempts"], int)
        or state["attempts"] < 1
        or not isinstance(state["failed_attempts"], list)
        or len(state["failed_attempts"]) != state["attempts"] - 1
    ):
        raise RunnerError(f"completed state response mismatch: {path.name}")
    state["state_sha256"] = _sha256_text(state_text)
    return state


def _run_one_batch(
    batch_index: int,
    batch: Sequence[Mapping[str, str]],
    *,
    instruction: str,
    executable: str,
    command_args: Sequence[str],
    prompt_mode: str,
    timeout: int,
    retries: int,
    environment: Mapping[str, str],
    state_dir: Path,
    binding_sha256: str,
) -> dict[str, Any]:
    expected_ids = [row["item_id"] for row in batch]
    batch_sha256 = _sha256_text(_canonical_json(list(batch)))
    path = _state_path(state_dir, batch_index)
    if path.exists():
        return _load_state(
            path,
            binding_sha256=binding_sha256,
            batch_sha256=batch_sha256,
            expected_ids=expected_ids,
        )

    prompt = _batch_prompt(instruction, batch)
    failures: list[dict[str, Any]] = []
    started_at = _now()
    for attempt in range(1, retries + 2):
        attempt_at = _now()
        invocation_cwd: Path | None = None
        process_receipt: dict[str, Any] | None = None
        try:
            invocation_cwd = Path(
                tempfile.mkdtemp(
                    prefix=f"ua-eval-model-{batch_index:04d}-{attempt:02d}-",
                    dir=_temporary_parent(),
                )
            )
            command = [executable, *command_args]
            command_input: str | None = None
            if prompt_mode == "argument":
                command.append(prompt)
            else:
                command_input = prompt
            result = subprocess.run(
                command,
                cwd=invocation_cwd,
                env=dict(environment),
                input=command_input,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            process_receipt = _write_process_receipts(
                invocation_cwd,
                attempted_at=attempt_at,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
            if result.returncode:
                raise RunnerError(f"provider command returned nonzero status {result.returncode}")
            raw_output = result.stdout
            responses = parse_provider_response(raw_output, expected_ids)
            _write_acceptance_receipt(invocation_cwd, accepted=True)
            state = {
                "schema_version": STATE_SCHEMA,
                "binding_sha256": binding_sha256,
                "batch_sha256": batch_sha256,
                "raw_provider_output": raw_output,
                "raw_provider_output_sha256": _sha256_text(raw_output),
                "responses": responses,
                "started_at": started_at,
                "completed_at": _now(),
                "attempts": attempt,
                "failed_attempts": failures,
            }
            state_text = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            _publish_text(path, state_text)
            return _load_state(
                path,
                binding_sha256=binding_sha256,
                batch_sha256=batch_sha256,
                expected_ids=expected_ids,
            )
        except (RunnerError, subprocess.TimeoutExpired) as exc:
            if invocation_cwd is not None and process_receipt is None:
                process_receipt = _write_process_receipts(
                    invocation_cwd,
                    attempted_at=attempt_at,
                    returncode=None,
                    stdout=_subprocess_text(getattr(exc, "stdout", None)),
                    stderr=_subprocess_text(getattr(exc, "stderr", None)),
                )
            if invocation_cwd is not None:
                _write_acceptance_receipt(
                    invocation_cwd,
                    accepted=False,
                    error_class=type(exc).__name__,
                    message=str(exc)[-240:],
                )
            evidence = process_receipt or {
                "stdout_sha256": _sha256_text(""),
                "stderr_sha256": _sha256_text(""),
            }
            failures.append(
                {
                    "batch_index": batch_index,
                    "attempt": attempt,
                    "attempted_at": attempt_at,
                    "error_class": type(exc).__name__,
                    "message_tail": str(exc)[-240:],
                    "invocation_directory_token": (invocation_cwd.name if invocation_cwd is not None else None),
                    "stdout_sha256": evidence["stdout_sha256"],
                    "stderr_sha256": evidence["stderr_sha256"],
                }
            )
    raise RunnerError(f"batch {batch_index} exhausted {retries + 1} attempts")


def run(
    *,
    requests_path: Path,
    prompt_path: Path,
    config_path: Path,
    executable: str,
    command_args: Sequence[str],
    prompt_mode: str,
    raw_output_path: Path,
    output_path: Path,
    metadata_path: Path,
    state_dir: Path,
    batch_size: int = 40,
    workers: int = 1,
    timeout: int = 1800,
    retries: int = 1,
) -> None:
    """Execute or resume a complete source-only model run."""

    if batch_size < 1 or workers < 1 or timeout < 1 or retries < 0 or prompt_mode not in {"argument", "stdin"}:
        raise RunnerError("batch, worker, timeout, retry, or prompt-mode bounds are invalid")
    header, requests, packet_sha256 = load_source_only_packet(requests_path)
    try:
        instruction = prompt_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerError("cannot read frozen instruction") from exc
    if not instruction.strip() or _sha256_text(instruction) != header["prompt_sha256"]:
        raise RunnerError("frozen instruction is empty or does not match the packet")
    config = load_run_config(config_path)
    command_hash = _sha256_text(
        _canonical_json(
            {
                "executable": executable,
                "arguments": list(command_args),
                "prompt_mode": prompt_mode,
            }
        )
    )
    config_hash = _sha256_text(_canonical_json(config))
    binding_sha256 = _sha256_text(
        _canonical_json(
            {
                "packet": packet_sha256,
                "prompt": header["prompt_sha256"],
                "run_id": config["run_id"],
                "model": config["model"],
                "command": command_hash,
                "config": config_hash,
            }
        )
    )
    batches = [
        (index, requests[offset : offset + batch_size])
        for index, offset in enumerate(range(0, len(requests), batch_size))
    ]
    state_dir.mkdir(parents=True, exist_ok=True)
    completed: dict[int, dict[str, Any]] = {}
    environment = _child_environment(config.get("auth_environment", []))
    batch_iterator = iter(batches)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures: dict[Future[dict[str, Any]], int] = {}

        def submit_next() -> bool:
            try:
                index, batch = next(batch_iterator)
            except StopIteration:
                return False
            future = executor.submit(
                _run_one_batch,
                index,
                batch,
                instruction=instruction,
                executable=executable,
                command_args=command_args,
                prompt_mode=prompt_mode,
                timeout=timeout,
                retries=retries,
                environment=environment,
                state_dir=state_dir,
                binding_sha256=binding_sha256,
            )
            futures[future] = index
            return True

        for _ in range(min(workers, len(batches))):
            submit_next()
        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                index = futures.pop(future)
                completed[index] = future.result()
                submit_next()

    raw_rows: list[dict[str, Any]] = []
    normalized: list[dict[str, str]] = []
    batch_receipts: list[dict[str, Any]] = []
    failed_attempts: list[dict[str, Any]] = []
    for index, batch in batches:
        state = completed[index]
        expected_ids = [row["item_id"] for row in batch]
        responses = parse_provider_response(
            state["raw_provider_output"],
            expected_ids,
        )
        raw_rows.append(
            {
                "batch_index": index,
                "batch_sha256": state["batch_sha256"],
                "raw_provider_output_sha256": state["raw_provider_output_sha256"],
                "raw_provider_output": state["raw_provider_output"],
            }
        )
        normalized.extend(responses)
        failed_attempts.extend(state["failed_attempts"])
        batch_receipts.append(
            {
                "batch_index": index,
                "batch_sha256": state["batch_sha256"],
                "raw_provider_output_sha256": state["raw_provider_output_sha256"],
                "state_sha256": state["state_sha256"],
                "attempts": state["attempts"],
                "started_at": state["started_at"],
                "completed_at": state["completed_at"],
            }
        )
    response_ids = [row["item_id"] for row in normalized]
    if response_ids != [row["item_id"] for row in requests] or len(set(response_ids)) != EXPECTED_REQUEST_COUNT:
        raise RunnerError("final aggregation does not exactly cover the request packet")

    raw_text = "".join(_canonical_json(row) + "\n" for row in raw_rows)
    output_text = "".join(_canonical_json(row) + "\n" for row in normalized)
    _publish_text(raw_output_path, raw_text)
    _publish_text(output_path, output_text)
    generation_metadata = {
        "route": config["route"],
        "alias_resolution": config["alias_resolution"],
        "command_identity": config["command_identity"],
        "command_sha256": command_hash,
        "config_sha256": config_hash,
        "request_packet_sha256": packet_sha256,
        "prompt_sha256": header["prompt_sha256"],
        "request_schema": REQUEST_SCHEMA,
        "response_count": len(normalized),
        "response_ids_sha256": _sha256_text(_canonical_json(response_ids)),
        "raw_output_sha256": _sha256_text(raw_text),
        "model_output_sha256": _sha256_text(output_text),
        "batch_size": batch_size,
        "workers": workers,
        "timeout_seconds": timeout,
        "prompt_mode": prompt_mode,
        "run_started_at": min(receipt["started_at"] for receipt in batch_receipts),
        "generated_at": max(receipt["completed_at"] for receipt in batch_receipts),
        "gold_fields_supplied": [],
        "batch_receipts": batch_receipts,
        "retry_counts": {str(receipt["batch_index"]): receipt["attempts"] - 1 for receipt in batch_receipts},
        "failed_attempts": failed_attempts,
        "response_normalization": [
            "extract final assistant text from a recognized NDJSON event when needed",
            "remove one exact optional JSON code fence before schema validation",
        ],
        "isolation": ("each provider invocation used a retained working directory outside the repository"),
    }
    metadata = {
        "schema_version": METADATA_SCHEMA,
        "run_id": config["run_id"],
        "provider": config["provider"],
        "model": config["model"],
        "model_version": config["model_version"],
        "decoding": config["decoding"],
        "runner_version": RUNNER_VERSION,
        "generation_metadata": generation_metadata,
    }
    _publish_text(
        metadata_path,
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--executable", required=True)
    parser.add_argument("--command-arg", action="append", default=[])
    parser.add_argument(
        "--prompt-mode",
        choices=["argument", "stdin"],
        default="argument",
    )
    parser.add_argument("--raw-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--retries", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        run(
            requests_path=args.requests,
            prompt_path=args.prompt,
            config_path=args.config,
            executable=args.executable,
            command_args=args.command_arg,
            prompt_mode=args.prompt_mode,
            raw_output_path=args.raw_output,
            output_path=args.output,
            metadata_path=args.metadata_output,
            state_dir=args.state_dir,
            batch_size=args.batch_size,
            workers=args.workers,
            timeout=args.timeout,
            retries=args.retries,
        )
    except (RunnerError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
