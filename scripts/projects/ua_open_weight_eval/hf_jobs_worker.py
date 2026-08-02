#!/usr/bin/env python3
"""Run the frozen UA Open-Weight Eval packet on one Hugging Face GPU Job.

The worker is deliberately self-contained so the exact reviewed file can be
downloaded into a Job and hash-verified before execution. It downloads one
pinned public GGUF artifact, verifies its bytes before loading it, uploads
resumable private checkpoint state directly to a private Hub dataset, and emits
complete parsed responses without an LLM judge.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
import shutil
import statistics
import sys
import tempfile
import time
import traceback
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

REQUEST_SCHEMA = "ua_open_weight_eval_requests.v1"
RESPONSE_SCHEMA = "ua_open_weight_eval_responses.v1"
CHECKPOINT_SCHEMA = "ua_open_weight_eval_hf_jobs_checkpoint.v1"
WORKER_RECEIPT_SCHEMA = "ua_open_weight_eval_hf_jobs_worker_receipt.v1"
ALLOWED_ACTIONS = frozenset({"correct", "preserve", "abstain"})
JOB_ID_PATTERN = re.compile(r"[a-f0-9]{20,64}")
OFFLINE_GENERATION_ENVIRONMENT = {
    "HF_DATASETS_OFFLINE": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "VLLM_BATCH_INVARIANT": "1",
    "VLLM_ENABLE_V1_MULTIPROCESSING": "0",
}


class WorkerError(ValueError):
    """Raised when the frozen worker contract cannot be satisfied."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise WorkerError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob_id(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()


def write_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    temporary.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    temporary.replace(path)


def append_durable(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(dict(value)) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


class HubArtifactStore:
    """Direct authenticated persistence for private checkpoints and receipts."""

    def __init__(self, repo_id: str, prefix: str) -> None:
        from huggingface_hub import HfApi

        _require(
            re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}",
                repo_id,
            )
            is not None,
            "invalid artifact repository",
        )
        _require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.\-/]{0,255}", prefix) is not None, "invalid artifact prefix")
        _require(".." not in prefix.split("/"), "unsafe artifact prefix")
        _require(bool(os.environ.get("HF_TOKEN")), "HF_TOKEN is required for direct checkpoint upload")
        self.repo_id = repo_id
        self.prefix = prefix.strip("/")
        self.api = HfApi(token=os.environ["HF_TOKEN"])
        _require(
            bool(self.api.repo_info(repo_id=repo_id, repo_type="dataset").private),
            "artifact repository is not private",
        )

    def remote_path(self, name: str) -> str:
        _require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", name) is not None, "invalid artifact name")
        return f"{self.prefix}/{name}"

    def download_optional(self, name: str, destination: Path) -> bool:
        from huggingface_hub import hf_hub_download
        from huggingface_hub.errors import EntryNotFoundError

        try:
            source = Path(
                hf_hub_download(
                    repo_id=self.repo_id,
                    repo_type="dataset",
                    filename=self.remote_path(name),
                    token=True,
                )
            )
        except EntryNotFoundError:
            return False
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        return True

    def upload(self, path: Path, name: str) -> str:
        _require(path.is_file(), f"artifact is missing: {name}")
        info = self.api.upload_file(
            path_or_fileobj=path,
            path_in_repo=self.remote_path(name),
            repo_id=self.repo_id,
            repo_type="dataset",
            commit_message=f"persist {name} for {os.environ.get('JOB_ID', 'unknown-job')}",
        )
        oid = getattr(info, "oid", None)
        _require(isinstance(oid, str) and re.fullmatch(r"[a-f0-9]{40}", oid) is not None, "artifact upload commit drift")
        return oid


def generation_totals(records: Sequence[Mapping[str, Any]], resumed_count: int) -> dict[str, float | int]:
    _require(0 <= resumed_count <= len(records), "invalid resumed record count")
    try:
        seconds = [float(record["generation_seconds"]) for record in records]
        tokens = [int(record["generated_tokens"]) for record in records]
    except (KeyError, TypeError, ValueError) as exc:
        raise WorkerError("checkpoint generation metrics are invalid") from exc
    _require(all(value >= 0 for value in seconds), "checkpoint generation seconds must be non-negative")
    _require(all(value >= 0 for value in tokens), "checkpoint generated tokens must be non-negative")
    return {
        "generated_tokens": sum(tokens),
        "generation_seconds": sum(seconds),
        "current_generation_seconds": sum(seconds[resumed_count:]),
        "resumed_case_count": resumed_count,
    }


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkerError(f"cannot read JSON {path.name}: {exc}") from exc
    _require(isinstance(value, dict), f"expected object in {path.name}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise WorkerError(f"cannot read JSONL {path.name}: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WorkerError(f"invalid JSONL {path.name}:{number}: {exc}") from exc
        _require(isinstance(value, dict), f"expected object in {path.name}:{number}")
        rows.append(value)
    _require(bool(rows), f"empty JSONL: {path.name}")
    return rows


def load_requests(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = read_jsonl(path)
    header, requests = rows[0], rows[1:]
    _require(header.get("type") == "request_run", "request header is missing")
    _require(header.get("schema_version") == REQUEST_SCHEMA, "request schema drift")
    _require(header.get("gold_fields_supplied") == [], "request packet exposes gold fields")
    _require(header.get("case_count") == 4000 == len(requests), "request count drift")
    _require(
        header.get("input_fields") == ["item_id", "source", "source_sha256", "instruction_sha256"],
        "request input field drift",
    )
    instruction = header.get("instruction")
    instruction_sha256 = header.get("instruction_sha256")
    _require(isinstance(instruction, str), "request instruction is missing")
    _require(instruction_sha256 == sha256_text(instruction), "instruction hash drift")
    seen: set[str] = set()
    for row in requests:
        item_id = row.get("item_id")
        source = row.get("source")
        _require(row.get("type") == "request", "non-request row in packet")
        _require(isinstance(item_id, str) and item_id and item_id not in seen, "invalid request ID")
        _require(isinstance(source, str) and source, f"missing source for {item_id}")
        _require(row.get("source_sha256") == sha256_text(source), f"source hash drift for {item_id}")
        _require(row.get("instruction_sha256") == instruction_sha256, f"instruction drift for {item_id}")
        payload = {
            "item_id": item_id,
            "source": source,
            "source_sha256": row["source_sha256"],
            "instruction_sha256": instruction_sha256,
        }
        _require(row.get("request_sha256") == sha256_text(canonical_json(payload)), f"request hash drift for {item_id}")
        _require(
            not {"expected", "target", "targets", "reference", "references", "edit", "edits"}.intersection(row),
            f"gold field in {item_id}",
        )
        seen.add(item_id)
    return header, requests


def select_requests(
    requests: Sequence[dict[str, Any]], selection_path: Path | None
) -> tuple[list[dict[str, Any]], str]:
    if selection_path is None:
        item_ids = [str(row["item_id"]) for row in requests]
        selection = {"mode": "full", "item_ids": item_ids}
    else:
        selection = read_json(selection_path)
        _require(selection.get("schema_version") == "ua_open_weight_eval_canary_selection.v1", "selection schema drift")
        item_ids = selection.get("item_ids")
        _require(isinstance(item_ids, list) and len(item_ids) == 100, "canary requires exactly 100 IDs")
        _require(len(set(item_ids)) == 100 and all(isinstance(item, str) for item in item_ids), "invalid canary IDs")
        claimed_selection_sha256 = selection.get("selection_sha256")
        unsigned_selection = {key: value for key, value in selection.items() if key != "selection_sha256"}
        _require(
            claimed_selection_sha256 == sha256_text(canonical_json(unsigned_selection)),
            "canary selection hash drift",
        )
    by_id = {str(row["item_id"]): row for row in requests}
    _require(all(item in by_id for item in item_ids), "selection contains an unknown request")
    selected = [by_id[item] for item in item_ids]
    selection_sha256 = (
        str(selection["selection_sha256"])
        if selection_path is not None
        else sha256_text(canonical_json(selection))
    )
    return selected, selection_sha256


def format_prompt(source: str) -> str:
    source_json = json.dumps(source, ensure_ascii=False)
    return (
        "You are evaluating Ukrainian correction versus faithful preservation. "
        "Return exactly one JSON object and no markdown or explanation. "
        'The object must have the keys "action" and "output_text". '
        '"action" must be "correct", "preserve", or "abstain". '
        "Correct only a clearly warranted Ukrainian error. Preserve quotations, proper names, "
        "historical or regional language, deliberate register, and genuinely acceptable text. "
        "Use abstain when the evidence is insufficient. For preserve or abstain, copy the source "
        f"exactly as output_text. Source JSON string: {source_json}"
    )


def parse_model_reply(reply: str) -> dict[str, str]:
    decoder = json.JSONDecoder()
    candidates: list[Mapping[str, Any]] = []
    for index, character in enumerate(reply):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(reply[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            candidates.append(value)
    _require(len(candidates) == 1, "model reply must contain exactly one JSON object")
    value = candidates[0]
    _require(set(value) == {"action", "output_text"}, "model reply field set drift")
    action = value.get("action")
    output_text = value.get("output_text")
    _require(action in ALLOWED_ACTIONS, "model reply has an invalid action")
    _require(isinstance(output_text, str) and output_text, "model reply has no output_text")
    return {"action": str(action), "output_text": output_text}


def verify_config(config: Mapping[str, Any]) -> None:
    _require(config.get("schema_version") == "ua_open_weight_eval_hf_jobs_config.v1", "config schema drift")
    _require(config.get("suite", {}).get("case_count") == 4000, "suite count drift")
    _require(config.get("hardware", {}).get("flavor") == "l40sx1", "hardware flavor drift")
    _require(config.get("hardware", {}).get("ports_exposed") is False, "ports must remain disabled")
    _require(config.get("hardware", {}).get("ssh_enabled") is False, "SSH must remain disabled")
    _require(config.get("model", {}).get("multimodal_projector_used") is False, "projector must remain excluded")
    _require(config.get("runner", {}).get("temperature") == 0.0, "temperature drift")
    _require(config.get("runner", {}).get("seed") == 0, "seed drift")
    _require(config.get("runner", {}).get("checkpoint_upload_every_cases") == 25, "checkpoint cadence drift")
    _require(config.get("transport", {}).get("mounted_volumes") == 0, "mounted volumes are prohibited")


def verify_tokenizer_files(root: Path, tokenizer_config: Mapping[str, Any]) -> dict[str, Any]:
    allowed = tokenizer_config.get("allowed_files")
    _require(isinstance(allowed, dict) and allowed, "tokenizer allowlist is missing")
    files = sorted(item for item in root.rglob("*") if item.is_file() and ".cache" not in item.parts)
    observed_names = {item.relative_to(root).as_posix() for item in files}
    _require(observed_names == set(allowed), "tokenizer allowlist drift")
    records = []
    for path in files:
        name = path.relative_to(root).as_posix()
        expected = allowed[name]
        size = path.stat().st_size
        _require(size == expected.get("bytes"), f"tokenizer byte drift for {name}")
        digest = sha256_file(path)
        if expected.get("sha256") is not None:
            _require(digest == expected["sha256"], f"tokenizer SHA-256 drift for {name}")
        else:
            _require(git_blob_id(path) == expected.get("blob_id"), f"tokenizer blob drift for {name}")
        records.append({"path": name, "bytes": size, "sha256": digest})
    tree_sha256 = sha256_text(canonical_json(records))
    return {"files": records, "tree_sha256": tree_sha256}


def download_and_verify_model(config: Mapping[str, Any], root: Path) -> tuple[Path, dict[str, Any], float]:
    from huggingface_hub import hf_hub_download, snapshot_download

    model_config = config["model"]
    tokenizer_config = config["tokenizer"]
    started = time.monotonic()
    model_path = Path(
        hf_hub_download(
            repo_id=model_config["repository"],
            filename=model_config["artifact_filename"],
            revision=model_config["revision"],
            local_dir=root / "model",
            token=False,
        )
    )
    _require(model_path.stat().st_size == model_config["artifact_bytes"], "model artifact byte drift")
    _require(sha256_file(model_path) == model_config["artifact_sha256"], "model artifact SHA-256 drift")
    tokenizer_root = Path(
        snapshot_download(
            repo_id=tokenizer_config["repository"],
            revision=tokenizer_config["revision"],
            allow_patterns=sorted(tokenizer_config["allowed_files"]),
            local_dir=root / "tokenizer",
            token=False,
        )
    )
    tokenizer_manifest = verify_tokenizer_files(tokenizer_root, tokenizer_config)
    elapsed = time.monotonic() - started
    return model_path, {"root": tokenizer_root, **tokenizer_manifest}, elapsed


def gpu_evidence() -> dict[str, Any]:
    import torch

    _require(torch.cuda.is_available(), "CUDA is unavailable")
    _require(torch.cuda.device_count() == 1, "worker requires exactly one GPU")
    properties = torch.cuda.get_device_properties(0)
    _require("L40S" in properties.name, f"unexpected GPU: {properties.name}")
    return {
        "count": 1,
        "name": properties.name,
        "total_memory_bytes": int(properties.total_memory),
        "torch_cuda": str(torch.version.cuda),
    }


def prepare_text_runtime_tokenizer(tokenizer_root: Path) -> tuple[Path, str]:
    """Derive a text-only runtime config after the official files verify."""
    source_config = read_json(tokenizer_root / "config.json")
    _require(source_config.get("model_type") == "gemma4", "official Gemma 4 config drift")
    _require(
        source_config.get("architectures") == ["Gemma4ForConditionalGeneration"],
        "official Gemma 4 architecture drift",
    )
    text_config = source_config.get("text_config")
    _require(isinstance(text_config, dict), "official Gemma 4 text config is missing")
    runtime_config = {**text_config, "architectures": ["Gemma4ForCausalLM"]}
    _require(runtime_config.get("model_type") == "gemma4_text", "Gemma 4 text model type drift")
    runtime_root = tokenizer_root.parent / "tokenizer-text-runtime"
    shutil.copytree(tokenizer_root, runtime_root)
    write_atomic(runtime_root / "config.json", runtime_config)
    return runtime_root, sha256_file(runtime_root / "config.json")


def load_generator(
    *, config: Mapping[str, Any], model_path: Path, tokenizer_root: Path
) -> tuple[Callable[[Sequence[str]], list[tuple[str, int]]], dict[str, str], Callable[[str], str]]:
    os.environ.update(OFFLINE_GENERATION_ENVIRONMENT)
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    runtime = config["runtime"]
    runner = config["runner"]
    versions = {
        "transformers": importlib.metadata.version("transformers"),
        "vllm": importlib.metadata.version("vllm"),
        "vllm_gguf_plugin": importlib.metadata.version("vllm-gguf-plugin"),
    }
    _require(versions["vllm"] == runtime["vllm_version"], "vLLM version drift")
    _require(
        versions["vllm_gguf_plugin"] == runtime["vllm_gguf_plugin"]["version"],
        "vLLM GGUF plugin version drift",
    )
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_root, local_files_only=True, trust_remote_code=False)

    def render(prompt: str) -> str:
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
            tokenize=False,
        )
        _require(isinstance(rendered, str) and rendered, "tokenizer did not render a prompt")
        return rendered

    model = LLM(
        model=str(model_path),
        tokenizer=str(tokenizer_root),
        quantization="gguf",
        seed=int(runner["seed"]),
        max_model_len=int(runner["max_model_len"]),
        gpu_memory_utilization=float(runner["gpu_memory_utilization"]),
        trust_remote_code=False,
        enforce_eager=True,
    )
    sampling = SamplingParams(
        temperature=float(runner["temperature"]),
        seed=int(runner["seed"]),
        max_tokens=int(runner["max_tokens"]),
    )

    def generate(prompts: Sequence[str]) -> list[tuple[str, int]]:
        outputs = model.generate(list(prompts), sampling, use_tqdm=False)
        _require(len(outputs) == len(prompts), "vLLM output count drift")
        generated: list[tuple[str, int]] = []
        for output in outputs:
            _require(len(output.outputs) == 1, "vLLM produced multiple candidates")
            candidate = output.outputs[0]
            generated.append((candidate.text, len(candidate.token_ids)))
        return generated

    return generate, versions, render


def load_checkpoint(path: Path, header: Mapping[str, Any], selected: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not path.exists():
        append_durable(path, header)
        return []
    rows = read_jsonl(path)
    _require(rows[0] == header, "checkpoint header drift")
    records = rows[1:]
    _require(len(records) <= len(selected), "checkpoint has too many rows")
    expected_ids = [str(row["item_id"]) for row in selected[: len(records)]]
    _require([record.get("item_id") for record in records] == expected_ids, "checkpoint is not an exact prefix")
    for request, record in zip(selected[: len(records)], records, strict=True):
        _require(record.get("request_sha256") == request["request_sha256"], "checkpoint request hash drift")
        response = record.get("response")
        _require(isinstance(response, dict), "checkpoint response is missing")
        _require(parse_model_reply(canonical_json(response)) == response, "checkpoint response drift")
        _require(isinstance(record.get("raw_generation"), str), "checkpoint raw generation is missing")
    return records


def _quantile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return float(ordered[index])


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.time()
    started_monotonic = time.monotonic()
    config = read_json(args.config)
    verify_config(config)
    _require(args.mode in {"canary", "full"}, "unsupported run mode")
    _require((args.selection is not None) == (args.mode == "canary"), "selection/mode mismatch")
    _require(
        os.environ.get("UA_EVAL_HARDWARE_FLAVOR") == "l40sx1",
        "UA_EVAL_HARDWARE_FLAVOR must be l40sx1",
    )
    job_id = os.environ.get("JOB_ID", "")
    _require(JOB_ID_PATTERN.fullmatch(job_id) is not None, "missing or invalid Hugging Face Job ID")
    artifact_store = HubArtifactStore(args.artifact_repo, args.artifact_prefix)

    request_header, requests = load_requests(args.requests)
    _require(sha256_file(args.requests) == args.requests_sha256, "request packet SHA-256 drift")
    selected, selection_sha256 = select_requests(requests, args.selection)
    expected_count = config["canary"]["case_count"] if args.mode == "canary" else config["suite"]["case_count"]
    _require(len(selected) == expected_count, "selected case count drift")

    work_root = Path(tempfile.mkdtemp(prefix="ua-open-weight-eval-hf-job-"))
    model_path, tokenizer_manifest, download_seconds = download_and_verify_model(config, work_root)
    tokenizer_root = Path(tokenizer_manifest.pop("root"))
    runtime_tokenizer_root, runtime_config_sha256 = prepare_text_runtime_tokenizer(tokenizer_root)
    tokenizer_manifest["text_runtime_config_sha256"] = runtime_config_sha256
    gpu = gpu_evidence()
    generator, versions, render = load_generator(
        config=config,
        model_path=model_path,
        tokenizer_root=runtime_tokenizer_root,
    )
    runner_sha256 = sha256_file(Path(__file__).resolve())
    checkpoint_header = {
        "type": "checkpoint_run",
        "schema_version": CHECKPOINT_SCHEMA,
        "mode": args.mode,
        "release_id": request_header["release_id"],
        "requests_sha256": args.requests_sha256,
        "selection_sha256": selection_sha256,
        "model": config["model"],
        "tokenizer": {
            "repository": config["tokenizer"]["repository"],
            "revision": config["tokenizer"]["revision"],
            "tree_sha256": tokenizer_manifest["tree_sha256"],
            "text_runtime_config_sha256": tokenizer_manifest["text_runtime_config_sha256"],
        },
        "backend": "vllm",
        "versions": versions,
        "runner_sha256": runner_sha256,
        "decoding": {
            "temperature": config["runner"]["temperature"],
            "seed": config["runner"]["seed"],
            "max_tokens": config["runner"]["max_tokens"],
            "parse_retries": config["runner"]["parse_retries"],
        },
        "network_during_generation": "private_checkpoint_upload_only",
    }
    checkpoint_path = args.output_root / "checkpoint.jsonl"
    artifact_store.download_optional("checkpoint.jsonl", checkpoint_path)
    records = load_checkpoint(checkpoint_path, checkpoint_header, selected)
    checkpoint_commit = artifact_store.upload(checkpoint_path, "checkpoint.jsonl")
    resumed_count = len(records)
    batch_seconds: list[float] = []
    retry_seconds: list[float] = []
    batch_size = int(config["runner"]["batch_size"])
    _require(
        batch_size == int(config["runner"]["checkpoint_upload_every_cases"]),
        "checkpoint upload cadence must equal the batch size",
    )
    retries = int(config["runner"]["parse_retries"])
    position = len(records)
    while position < len(selected):
        batch = selected[position : position + batch_size]
        rendered = [render(format_prompt(str(request["source"]))) for request in batch]
        batch_started = time.monotonic()
        generations = generator(rendered)
        elapsed = time.monotonic() - batch_started
        batch_seconds.append(elapsed)
        per_request_batch_seconds = elapsed / len(batch)
        for request, (raw_generation, token_count), base_prompt in zip(batch, generations, rendered, strict=True):
            last_error = ""
            parsed: dict[str, str] | None = None
            retry_count = 0
            request_retry_seconds = 0.0
            current_generation = raw_generation
            current_tokens = token_count
            for attempt in range(retries + 1):
                try:
                    parsed = parse_model_reply(current_generation)
                    retry_count = attempt
                    break
                except WorkerError as exc:
                    last_error = str(exc)
                    if attempt == retries:
                        break
                    retry_prompt = (
                        base_prompt
                        + f" Previous reply was invalid ({last_error}); return only the required JSON object."
                    )
                    retry_started = time.monotonic()
                    [(current_generation, retry_tokens)] = generator([retry_prompt])
                    retry_elapsed = time.monotonic() - retry_started
                    retry_seconds.append(retry_elapsed)
                    request_retry_seconds += retry_elapsed
                    current_tokens += retry_tokens
            _require(parsed is not None, f"cannot parse model reply for {request['item_id']}: {last_error}")
            record = {
                "item_id": request["item_id"],
                "request_sha256": request["request_sha256"],
                "raw_generation": current_generation,
                "response": parsed,
                "generated_tokens": current_tokens,
                "generation_seconds": per_request_batch_seconds + request_retry_seconds,
                "parse_retries_used": retry_count,
            }
            append_durable(checkpoint_path, record)
            records.append(record)
        position += len(batch)
        checkpoint_commit = artifact_store.upload(checkpoint_path, "checkpoint.jsonl")
        print(f"hf-jobs-worker: completed {position}/{len(selected)}", file=sys.stderr, flush=True)
    generation = generation_totals(records, resumed_count)
    generation_seconds = float(generation["generation_seconds"])
    generated_tokens = int(generation["generated_tokens"])

    response_header = {
        "type": "run",
        "schema_version": RESPONSE_SCHEMA,
        "release_id": request_header["release_id"],
        "model": config["model"]["repository"],
        "model_revision": config["model"]["revision"],
        "model_artifact": config["model"]["artifact_filename"],
        "model_sha256": config["model"]["artifact_sha256"],
        "tokenizer": config["tokenizer"]["repository"],
        "tokenizer_revision": config["tokenizer"]["revision"],
        "tokenizer_tree_sha256": tokenizer_manifest["tree_sha256"],
        "backend": "vllm",
        "backend_version": versions["vllm"],
        "decoding": checkpoint_header["decoding"],
        "network_allowed_during_generation": True,
        "network_use": "private_checkpoint_upload_only",
        "closed_api_used": False,
        "job_id": job_id,
        "hardware_flavor": "l40sx1",
    }
    response_rows = [response_header]
    response_rows.extend({"item_id": record["item_id"], **record["response"]} for record in records)
    responses_text = "".join(canonical_json(row) + "\n" for row in response_rows)
    responses_path = args.output_root / "responses.jsonl"
    write_atomic(responses_path, responses_text)
    responses_commit = artifact_store.upload(responses_path, "responses.jsonl")
    ended_at = time.time()
    total_seconds = time.monotonic() - started_monotonic
    receipt = {
        "schema_version": WORKER_RECEIPT_SCHEMA,
        "status": "completed",
        "mode": args.mode,
        "job": {
            "id": job_id,
            "provider": "Hugging Face Jobs",
            "hardware_flavor": "l40sx1",
            "ports_exposed": False,
            "ssh_enabled": False,
        },
        "suite": {
            "release_id": request_header["release_id"],
            "case_count": len(selected),
            "requests_sha256": args.requests_sha256,
            "selection_sha256": selection_sha256,
        },
        "model": config["model"],
        "tokenizer": {
            "repository": config["tokenizer"]["repository"],
            "revision": config["tokenizer"]["revision"],
            **tokenizer_manifest,
        },
        "environment": {
            "container_amd64_digest": config["runtime"]["container_amd64_digest"],
            "platform": platform.platform(),
            "python": platform.python_version(),
            "runner_sha256": runner_sha256,
            "versions": versions,
            "gpu": gpu,
        },
        "decoding": checkpoint_header["decoding"],
        "timing": {
            "started_at_unix": started_at,
            "ended_at_unix": ended_at,
            "download_seconds": download_seconds,
            "generation_seconds": generation_seconds,
            "current_generation_seconds": generation["current_generation_seconds"],
            "resumed_case_count": generation["resumed_case_count"],
            "wall_seconds": total_seconds,
            "mean_seconds_per_case": generation_seconds / len(selected),
            "batch_seconds_p50": statistics.median(batch_seconds) if batch_seconds else None,
            "batch_seconds_p95": _quantile(batch_seconds, 0.95),
            "retry_seconds_total": sum(retry_seconds),
        },
        "throughput": {
            "generated_tokens": generated_tokens,
            "generated_tokens_per_second": generated_tokens / generation_seconds if generation_seconds else None,
            "mean_generated_tokens_per_case": generated_tokens / len(selected),
        },
        "outputs": {
            "checkpoint_sha256": sha256_file(checkpoint_path),
            "responses_sha256": sha256_file(responses_path),
            "response_count": len(records),
            "private_artifact_repository": artifact_store.repo_id,
            "private_artifact_prefix": artifact_store.prefix,
            "checkpoint_upload_commit": checkpoint_commit,
            "responses_upload_commit": responses_commit,
        },
        "facts": {
            "closed_model_judge_used": False,
            "complete": len(records) == len(selected),
            "foundry_learning_eligible": False,
            "global_quality_score_produced": False,
            "model_weights_uploaded": False,
            "training_performed": False,
        },
    }
    receipt_path = args.output_root / "worker_receipt.json"
    write_atomic(receipt_path, receipt)
    artifact_store.upload(receipt_path, "worker_receipt.json")
    return receipt


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["canary", "full"], required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--requests-sha256", required=True)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--artifact-repo", required=True)
    parser.add_argument("--artifact-prefix", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run(args)
    except BaseException as exc:
        failure = {
            "schema_version": "ua_open_weight_eval_hf_jobs_failure.v1",
            "status": "failed",
            "mode": args.mode,
            "job_id": os.environ.get("JOB_ID"),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        failure_path = args.output_root / "failure.private.json"
        with contextlib.suppress(OSError):
            write_atomic(failure_path, failure)
        with contextlib.suppress(BaseException):
            HubArtifactStore(args.artifact_repo, args.artifact_prefix).upload(failure_path, "failure.private.json")
        print(canonical_json({key: value for key, value in failure.items() if key != "traceback"}), file=sys.stderr)
        return 2
    print(canonical_json({"status": result["status"], "mode": result["mode"], "job_id": result["job"]["id"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
