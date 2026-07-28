#!/usr/bin/env python3
"""Run source-only UA evaluation requests through an isolated Codex CLI.

This is a generation adapter, not a scorer. It receives the gold-free request
packet produced by ``evaluate_model.py prepare`` and writes importable model
output plus a provenance metadata receipt. The child Codex process runs in an
empty temporary directory with repository rules and user configuration ignored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REQUESTS = ROOT / "data/projects/ua_eval_harness/baselines/v1/generation_requests.jsonl"
DEFAULT_PROMPT = ROOT / "data/projects/ua_eval_harness/minimal_edit_prompt_v1.txt"
DEFAULT_SCHEMA = ROOT / "data/projects/ua_eval_harness/model_output_schema_v1.json"
RUNNER_VERSION = "ua_eval_codex_cli_batch_runner.v1"


class RunnerError(ValueError):
    """The source-only request or model response violated the runner contract."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RunnerError(f"cannot read requests {path}: {exc}") from exc
    for number, line in enumerate(lines, 1):
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RunnerError(f"invalid request JSONL at line {number}: {exc}") from exc
        if not isinstance(row, dict):
            raise RunnerError(f"request line {number} is not an object")
        rows.append(row)
    return rows


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(_canonical_json(dict(row)) + "\n" for row in rows), encoding="utf-8")


def _load_source_only_requests(path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    rows = _read_jsonl(path)
    if not rows or rows[0].get("schema_version") != "ua_eval_generation_requests.v1":
        raise RunnerError("request packet schema mismatch")
    header = rows[0]
    if header.get("gold_fields_supplied") != []:
        raise RunnerError("request packet reports gold fields")
    expected_fields = {
        "type",
        "item_id",
        "source",
        "source_sha256",
        "prompt_sha256",
        "request_sha256",
    }
    requests: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows[1:]:
        if set(row) != expected_fields or row.get("type") != "request":
            raise RunnerError("request row contains non-contract fields")
        item_id = str(row["item_id"])
        if not item_id or item_id in seen:
            raise RunnerError(f"missing or duplicate request id: {item_id!r}")
        seen.add(item_id)
        requests.append({"item_id": item_id, "source": str(row["source"])})
    if len(requests) != header.get("request_count"):
        raise RunnerError("request count mismatch")
    return header, requests


def _cli_version(codex_bin: str) -> str:
    result = subprocess.run(
        [codex_bin, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RunnerError(f"cannot resolve Codex CLI version: {result.stderr.strip()}")
    return result.stdout.strip()


def _child_environment() -> dict[str, str]:
    """Pass only the environment needed for CLI discovery, auth, and TLS."""
    allowed = {
        "PATH",
        "HOME",
        "CODEX_HOME",
        "TMPDIR",
        "SHELL",
        "TERM",
        "LANG",
        "LC_ALL",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
    }
    return {key: value for key, value in os.environ.items() if key in allowed}


def _run_batch(
    batch: Sequence[Mapping[str, str]],
    *,
    prompt_text: str,
    model: str,
    codex_bin: str,
    schema_path: Path,
    timeout: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    model_input = {
        "instruction": prompt_text,
        "records": [{"item_id": row["item_id"], "source": row["source"]} for row in batch],
    }
    user_prompt = (
        "Execute the Ukrainian correction task in the JSON value below. "
        "Return one response for every item_id, in the same order. "
        "Do not explain or add fields.\n\n" + _canonical_json(model_input)
    )
    with tempfile.TemporaryDirectory(prefix="ua-eval-codex-") as temp:
        temp_root = Path(temp)
        output_path = temp_root / "last-message.json"
        command = [
            codex_bin,
            "exec",
            "--model",
            model,
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--cd",
            str(temp_root),
            "--output-schema",
            str(schema_path.resolve()),
            "--output-last-message",
            str(output_path),
            "--color",
            "never",
            "-",
        ]
        result = subprocess.run(
            command,
            input=user_prompt,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            env=_child_environment(),
        )
        if result.returncode:
            raise RunnerError(f"Codex batch failed ({result.returncode}): {result.stderr[-1000:]}")
        try:
            raw_bytes = output_path.read_bytes()
            payload = json.loads(raw_bytes)
        except (OSError, json.JSONDecodeError) as exc:
            raise RunnerError(f"Codex batch returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("responses"), list):
        raise RunnerError("Codex batch response schema mismatch")
    responses = payload["responses"]
    expected_ids = [row["item_id"] for row in batch]
    returned_ids = [str(row.get("item_id", "")) for row in responses if isinstance(row, dict)]
    if returned_ids != expected_ids:
        raise RunnerError("Codex batch response IDs/order do not match requests")
    normalized = [{"item_id": str(row["item_id"]), "raw_response": str(row["raw_response"])} for row in responses]
    receipt = {
        "request_sha256": _sha256_bytes(user_prompt.encode("utf-8")),
        "raw_response_sha256": _sha256_bytes(raw_bytes),
        "items": len(batch),
    }
    return normalized, receipt


def run(
    *,
    requests_path: Path,
    prompt_path: Path,
    schema_path: Path,
    output_path: Path,
    metadata_path: Path,
    model: str,
    codex_bin: str,
    batch_size: int,
    workers: int,
    timeout: int,
) -> None:
    if batch_size < 1:
        raise RunnerError("batch size must be positive")
    if workers < 1:
        raise RunnerError("worker count must be positive")
    header, requests = _load_source_only_requests(requests_path)
    try:
        prompt_text = prompt_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerError(f"cannot read prompt {prompt_path}: {exc}") from exc
    prompt_sha256 = _sha256_bytes(prompt_text.encode("utf-8"))
    if prompt_sha256 != header.get("prompt_sha256"):
        raise RunnerError("request packet prompt hash mismatch")

    batches = [
        (offset // batch_size, requests[offset : offset + batch_size]) for offset in range(0, len(requests), batch_size)
    ]
    completed: dict[int, tuple[list[dict[str, str]], dict[str, Any]]] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _run_batch,
                batch,
                prompt_text=prompt_text,
                model=model,
                codex_bin=codex_bin,
                schema_path=schema_path,
                timeout=timeout,
            ): (batch_index, len(batch))
            for batch_index, batch in batches
        }
        for future in as_completed(futures):
            batch_index, item_count = futures[future]
            batch_output, receipt = future.result()
            receipt["batch_index"] = batch_index
            completed[batch_index] = (batch_output, receipt)
            print(f"completed batch {batch_index + 1}: {item_count} items", flush=True)
    outputs: list[dict[str, str]] = []
    receipts: list[dict[str, Any]] = []
    for batch_index, _ in batches:
        batch_output, receipt = completed[batch_index]
        outputs.extend(batch_output)
        receipts.append(receipt)
    _write_jsonl(output_path, outputs)
    cli_version = _cli_version(codex_bin)
    metadata = {
        "run_id": f"{header['manifest_id']}--{model}--codex-cli",
        "provider": "openai-subscription-via-codex-cli",
        "model": model,
        "model_version": model,
        "decoding": {
            "temperature": "provider_default_not_exposed",
            "top_p": "provider_default_not_exposed",
            "seed": "not_exposed",
            "structured_output_schema_sha256": _sha256_bytes(schema_path.read_bytes()),
        },
        "runner_version": (
            f"{RUNNER_VERSION};source_sha256={_sha256_bytes(Path(__file__).read_bytes())};{cli_version}"
        ),
        "generation_metadata": {
            "isolation": "empty temporary directory; read-only sandbox; rules and user config ignored",
            "batch_size": batch_size,
            "parallel_workers": workers,
            "batch_receipts": receipts,
            "gold_fields_supplied": [],
        },
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(outputs)} model responses to {output_path}")
    print(f"wrote provenance metadata to {metadata_path}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=Path, default=DEFAULT_REQUESTS)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args(argv)
    try:
        run(
            requests_path=args.requests,
            prompt_path=args.prompt,
            schema_path=args.schema,
            output_path=args.output,
            metadata_path=args.metadata_output,
            model=args.model,
            codex_bin=args.codex_bin,
            batch_size=args.batch_size,
            workers=args.workers,
            timeout=args.timeout,
        )
        return 0
    except (RunnerError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
