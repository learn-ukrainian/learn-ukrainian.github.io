#!/usr/bin/env python3
"""Run the bounded, non-treatment Gemma 4 L40S hardware probe.

The local launcher validates an exact operator authorization before it can
create a Hugging Face Job. The remote worker uses only deterministic synthetic
token IDs, writes no Hub artifact, and produces a machine-readable receipt in
its logs. The provider-enforced timeout is the economic backstop.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import multiprocessing
import os
import platform
import re
import subprocess
import tempfile
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from queue import Empty
from typing import Any


def _resolve_root(script_path: Path) -> Path:
    """Resolve the repository root locally and a harmless base remotely."""
    resolved = script_path.resolve()
    for candidate in resolved.parents:
        if (candidate / "data/projects/open_model_data/contracts").is_dir():
            return candidate
    return resolved.parent


ROOT = _resolve_root(Path(__file__))
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
PLAN_SCHEMA = CONTRACTS / "gemma_hardware_probe_plan_v1.schema.json"
AUTH_SCHEMA = CONTRACTS / "gemma_hardware_probe_authorization_v1.schema.json"
RECEIPT_SCHEMA = CONTRACTS / "gemma_hardware_probe_receipt_v1.schema.json"
PLAN_PATH = ROOT / "data/projects/open_model_data/treatments/gemma4_it_l40s_hf_jobs_probe_plan_v1.json"
ATTEMPT_LEDGER_PATH = ROOT / "batch_state/6170/hf-probe-launch.json"
EXPECTED_PLAN_SHA256 = "c78684279f5f34ff7b2c567e88182b4f8bcf6c154f570c12a6e72c492b4eef69"
MODEL_IDENTIFIER = "google/gemma-4-31B-it"
MODEL_REVISION = "842da3794eaa0b77d5f08bae87a17459d91ff475"
PROBE_ID = "gemma4-it-l40s-hf-jobs-hardware-probe-v1"
RECEIPT_MARKER = "GEMMA_HARDWARE_PROBE_RECEIPT="
JOB_ID_PATTERN = re.compile(r"(?<![0-9a-f])[0-9a-f]{24}(?![0-9a-f])")
REQUIRED_PACKAGES = (
    "accelerate==1.14.0",
    "bitsandbytes==0.50.0",
    "huggingface_hub==1.25.1",
    "peft==0.20.0",
    "torch==2.13.0",
    "transformers==5.14.1",
)
SNAPSHOT_FILES = {
    "chat_template.jinja": (18683, "ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4"),
    "config.json": (4621, "e967dd38bc5cfd38bd09a995a7bf4a754075df2b46aba68f7fbb5a791e6d8dd1"),
    "generation_config.json": (208, "d4226bbe3117d2d253ba4609720ba82c6c4ce4627a9a6ae05387c78983ac03de"),
    "model-00001-of-00002.safetensors": (
        49784788364,
        "eeef8791537bc04f110967c513149e037d2a9ae97d49add7291ebfa62806bbfa",
    ),
    "model-00002-of-00002.safetensors": (
        12761549884,
        "018912220f559f7025d60333e0996183cd538aa77ad6f4988a89ce47be681f10",
    ),
    "model.safetensors.index.json": (
        120246,
        "d4aff3b976d69c123a29d1c085d7ba4de1ac3f4ca1726a7f81e1b11462a64ea2",
    ),
    "processor_config.json": (1689, "32bdf45d2ad4cc29a0822ddd157a182de76644f0419a6228d151495256e9813c"),
    "tokenizer.json": (32169626, "cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f"),
    "tokenizer_config.json": (3082, "9f4fec4b1dc6ecddf8f4a92e9caea5971c0e67d81309f3f9066a2bee8c362633"),
}


class HardwareProbeError(RuntimeError):
    """The bounded hardware probe cannot safely proceed."""


class ProbeExecutionError(HardwareProbeError):
    """A worker failure carrying already-persisted partial probe evidence."""

    def __init__(self, message: str, *, partial_evidence: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.partial_evidence = dict(partial_evidence)


class PhaseExecutionError(HardwareProbeError):
    """A child-phase failure carrying a durable optimizer-step marker."""

    def __init__(
        self,
        message: str,
        *,
        phase_evidence: Mapping[str, Any] | None,
        process_started: bool,
    ) -> None:
        super().__init__(message)
        self.phase_evidence = dict(phase_evidence or {})
        self.process_started = process_started


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardwareProbeError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HardwareProbeError(f"expected JSON object in {path}")
    return value


def validate_schema(value: Mapping[str, Any], schema_path: Path, *, label: str) -> None:
    from jsonschema import Draft202012Validator, FormatChecker

    schema = read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise HardwareProbeError(f"{label} schema error at {location}: {error.message}")


def write_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_atomic_bytes(path, payload)


def write_atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(raw_temp_path)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _assert_artifact(binding: Mapping[str, Any]) -> Path:
    path = ROOT / str(binding["logical_path"])
    if not path.is_file():
        raise HardwareProbeError(f"missing bound artifact: {binding['logical_path']}")
    if path.stat().st_size != int(binding["bytes"]) or sha256_file(path) != str(binding["sha256"]):
        raise HardwareProbeError(f"bound artifact drift: {binding['logical_path']}")
    return path


def validate_plan_authorization(plan_path: Path, authorization_path: Path) -> tuple[dict[str, Any], str]:
    plan = read_json(plan_path)
    validate_schema(plan, PLAN_SCHEMA, label="hardware-probe plan")
    plan_sha256 = sha256_file(plan_path)
    if plan_sha256 != EXPECTED_PLAN_SHA256:
        raise HardwareProbeError("hardware-probe plan differs from the runner-bound plan")
    _assert_artifact(plan["snapshot_manifest"])
    _assert_artifact(plan["reference_treatment"])

    authorization = read_json(authorization_path)
    validate_schema(authorization, AUTH_SCHEMA, label="hardware-probe authorization")
    if authorization["plan"]["sha256"] != plan_sha256:
        raise HardwareProbeError("authorization is not bound to the exact hardware-probe plan")
    _assert_artifact(authorization["plan"])
    _assert_artifact(authorization["runner"])
    expected = plan["provider"]
    approved = authorization["authorization"]
    comparisons = {
        "provider": expected["provider"],
        "hardware_flavor": expected["hardware_flavor"],
        "timeout_seconds": expected["timeout_seconds"],
        "maximum_provider_charge_usd": expected["maximum_provider_charge_usd"],
        "paid_attempts": expected["paid_attempts"],
    }
    for field, expected_value in comparisons.items():
        if approved[field] != expected_value:
            raise HardwareProbeError(f"authorization {field} differs from the frozen plan")
    if approved["operator_all_inclusive_ceiling_eur"] != plan["operator_ceiling"]["amount_eur"]:
        raise HardwareProbeError("authorization operator ceiling differs from the frozen plan")
    return plan, sha256_file(authorization_path)


def build_hf_job_command(
    *,
    plan_path: Path,
    authorization_path: Path,
    hf_cli: Path,
    script_path: Path | None = None,
) -> list[str]:
    plan, authorization_sha256 = validate_plan_authorization(plan_path, authorization_path)
    if not hf_cli.is_file() or not os.access(hf_cli, os.X_OK):
        raise HardwareProbeError(f"Hugging Face CLI is not executable: {hf_cli}")
    script = script_path or Path(__file__).resolve()
    if not script.is_file():
        raise HardwareProbeError(f"hardware-probe worker script is missing: {script}")
    provider = plan["provider"]
    command = [
        str(hf_cli),
        "jobs",
        "uv",
        "run",
        "--detach",
        "--timeout",
        f"{provider['timeout_seconds']}s",
        "--flavor",
        str(provider["hardware_flavor"]),
        "--secrets",
        "HF_TOKEN",
        "--name",
        "gemma4-it-l40s-probe-6170",
        "--label",
        "issue=6170",
        "--label",
        f"probe_id={PROBE_ID}",
        "--label",
        f"plan_sha256={EXPECTED_PLAN_SHA256}",
        "--label",
        f"authorization_sha256={authorization_sha256}",
        "--label",
        f"timeout_seconds={provider['timeout_seconds']}",
        "--python",
        "3.12",
    ]
    for package in REQUIRED_PACKAGES:
        command.extend(("--with", package))
    command.extend(
        (
            str(script),
            "worker",
            "--plan-sha256",
            EXPECTED_PLAN_SHA256,
            "--authorization-sha256",
            authorization_sha256,
        )
    )
    return command


def safe_job_command(
    command: Sequence[str],
    *,
    script_path: Path,
    script_placeholder: str,
) -> list[str]:
    return [
        "<HF_CLI>"
        if index == 0
        else script_placeholder if value == str(script_path) else value
        for index, value in enumerate(command)
    ]


def parse_job_id(output: str) -> str:
    matches = JOB_ID_PATTERN.findall(output.lower())
    if len(set(matches)) != 1:
        raise HardwareProbeError("Hugging Face Jobs launch did not return exactly one job ID")
    return matches[0]


def require_hf_auth(hf_cli: str) -> None:
    auth_probe = subprocess.run(
        [hf_cli, "auth", "whoami"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if auth_probe.returncode:
        raise HardwareProbeError("Hugging Face authentication is not configured")


def _parse_json_array(payload: str, *, label: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HardwareProbeError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise HardwareProbeError(f"{label} must be a JSON array of objects")
    return value


def require_no_provider_attempt(*, hf_cli: str, authorization_sha256: str) -> None:
    """Fail before launch if the provider already knows this authorization."""
    result = subprocess.run(
        [
            hf_cli,
            "jobs",
            "list",
            "--all",
            "--limit",
            "0",
            "--label",
            f"authorization_sha256={authorization_sha256}",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise HardwareProbeError("cannot establish the provider-side paid-attempt state")
    jobs = _parse_json_array(result.stdout, label="provider paid-attempt query")
    if jobs:
        raise HardwareProbeError("provider already has a job for this exact authorization")


def launch_job(command: Sequence[str]) -> str:
    require_hf_auth(command[0])
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode:
        message = result.stderr.strip() or result.stdout.strip() or "unknown launch error"
        raise HardwareProbeError(f"Hugging Face Job launch failed: {message}")
    return parse_job_id(f"{result.stdout}\n{result.stderr}")


def claim_paid_attempt(path: Path, claim: Mapping[str, Any]) -> None:
    """Claim the only authorized paid attempt before the provider call."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(claim, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise HardwareProbeError(f"paid-attempt ledger already exists: {path}") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def host_global_attempt_claim_path(authorization_sha256: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{64}", authorization_sha256):
        raise HardwareProbeError("cannot derive a host-global claim for an invalid authorization hash")
    return (
        Path(tempfile.gettempdir())
        / "learn-ukrainian-hf-probe-claims"
        / f"{authorization_sha256}.json"
    )


def create_authorized_runner_snapshot(
    *,
    authorization_path: Path,
    output_directory: Path,
) -> Path:
    """Create a private read-only copy that remains stable while HF uploads it."""
    _, authorization_sha256 = validate_plan_authorization(PLAN_PATH, authorization_path)
    authorization = read_json(authorization_path)
    binding = authorization["runner"]
    source = _assert_artifact(binding)
    payload = source.read_bytes()
    if len(payload) != binding["bytes"] or sha256_bytes(payload) != binding["sha256"]:
        raise HardwareProbeError("authorized runner changed while creating its upload snapshot")
    snapshot = output_directory / f"gemma-hardware-probe-{authorization_sha256}.authorized.py"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    except FileExistsError as exc:
        raise HardwareProbeError("authorized runner upload snapshot already exists") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        snapshot.unlink(missing_ok=True)
        raise
    if snapshot.stat().st_size != binding["bytes"] or sha256_file(snapshot) != binding["sha256"]:
        raise HardwareProbeError("authorized runner upload snapshot verification failed")
    return snapshot


def verify_authorized_runner_snapshot(*, snapshot: Path, authorization_path: Path) -> None:
    authorization = read_json(authorization_path)
    binding = authorization["runner"]
    try:
        snapshot_stat = snapshot.stat()
        snapshot_sha256 = sha256_file(snapshot)
    except OSError as exc:
        raise HardwareProbeError(f"cannot verify authorized runner upload snapshot: {exc}") from exc
    if snapshot_stat.st_size != binding["bytes"] or snapshot_sha256 != binding["sha256"]:
        raise HardwareProbeError("authorized runner upload snapshot drift")
    if snapshot_stat.st_mode & 0o222:
        raise HardwareProbeError("authorized runner upload snapshot is writable")


def reconcile_provider_receipt(
    *,
    receipt: Mapping[str, Any],
    inspection: Mapping[str, Any],
    job_id: str,
    authorization_sha256: str,
    authorization: Mapping[str, Any],
    wait_returncode: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind worker evidence to the terminal job facts returned by HF Jobs."""
    if inspection.get("id") != job_id:
        raise HardwareProbeError("provider inspection job ID drift")
    if inspection.get("flavor") != "l40sx1":
        raise HardwareProbeError("provider inspection hardware-flavor drift")
    labels = inspection.get("labels")
    if not isinstance(labels, dict):
        raise HardwareProbeError("provider inspection is missing job labels")
    required_labels = {
        "authorization_sha256": authorization_sha256,
        "issue": "6170",
        "plan_sha256": EXPECTED_PLAN_SHA256,
        "probe_id": PROBE_ID,
        "timeout_seconds": "3600",
    }
    if any(labels.get(key) != value for key, value in required_labels.items()):
        raise HardwareProbeError("provider inspection label drift")
    status = inspection.get("status")
    if not isinstance(status, dict):
        raise HardwareProbeError("provider inspection is missing job status")
    stage = status.get("stage")
    terminal_stages = {"COMPLETED", "CANCELED", "ERROR", "DELETED"}
    if stage not in terminal_stages:
        raise HardwareProbeError("provider job has not reached a terminal state")
    if (wait_returncode == 0) != (stage == "COMPLETED"):
        raise HardwareProbeError("provider wait result disagrees with terminal job status")
    if status.get("expose_urls") or status.get("ssh_url"):
        raise HardwareProbeError("provider inspection reports an exposed endpoint")
    durations = inspection.get("durations")
    if not isinstance(durations, dict):
        raise HardwareProbeError("provider inspection is missing server-side durations")
    running_seconds = durations.get("running_secs")
    if not isinstance(running_seconds, int) or isinstance(running_seconds, bool):
        raise HardwareProbeError("provider running duration is missing or invalid")
    if not 0 <= running_seconds <= 3600:
        raise HardwareProbeError("provider running duration exceeds the authorized timeout")
    provider_derived_cost_usd = round(running_seconds * 0.03 / 60, 6)
    if provider_derived_cost_usd > 1.8:
        raise HardwareProbeError("provider-derived charge exceeds the authorized maximum")
    if receipt.get("authorization_sha256") != authorization_sha256:
        raise HardwareProbeError("provider receipt authorization drift")
    environment = receipt.get("environment")
    if not isinstance(environment, dict) or environment.get("runner_sha256") != authorization["runner"]["sha256"]:
        raise HardwareProbeError("provider receipt runner drift")
    if receipt.get("status") == "completed" and stage != "COMPLETED":
        raise HardwareProbeError("completed worker receipt disagrees with provider failure status")

    reconciled = json.loads(canonical_json(receipt))
    reconciled["provider_job"].update(
        {
            "job_status": stage,
            "provider_derived_cost_usd": provider_derived_cost_usd,
            "provider_evidence_reconciled": True,
            "provider_running_seconds": running_seconds,
        }
    )
    evidence = {
        "authorization_sha256": authorization_sha256,
        "exposed_endpoints": False,
        "hardware_flavor": inspection["flavor"],
        "job_id": job_id,
        "labels": required_labels,
        "provider_derived_cost_usd": provider_derived_cost_usd,
        "provider_running_seconds": running_seconds,
        "provider_stage": stage,
        "timeout_seconds": 3600,
        "wait_returncode": wait_returncode,
    }
    return reconciled, evidence


def collect_job(
    *,
    job_id: str,
    hf_cli: Path,
    authorization_path: Path,
    output_directory: Path,
) -> dict[str, Any]:
    if not JOB_ID_PATTERN.fullmatch(job_id):
        raise HardwareProbeError("invalid Hugging Face Job ID")
    _, authorization_sha256 = validate_plan_authorization(PLAN_PATH, authorization_path)
    authorization = read_json(authorization_path)
    if not hf_cli.is_file() or not os.access(hf_cli, os.X_OK):
        raise HardwareProbeError(f"Hugging Face CLI is not executable: {hf_cli}")
    require_hf_auth(str(hf_cli))
    wait_result = subprocess.run(
        [str(hf_cli), "jobs", "wait", "--timeout", "75m", job_id],
        check=False,
        capture_output=True,
        text=True,
    )
    inspect_result = subprocess.run(
        [str(hf_cli), "jobs", "inspect", "--json", job_id],
        check=False,
        capture_output=True,
        text=True,
    )
    stats_result = subprocess.run(
        [str(hf_cli), "jobs", "stats", job_id],
        check=False,
        capture_output=True,
        text=True,
    )
    logs_result = subprocess.run(
        [str(hf_cli), "jobs", "logs", job_id],
        check=False,
        capture_output=True,
        text=True,
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    write_atomic_bytes(output_directory / "provider-wait.stdout.txt", wait_result.stdout.encode("utf-8"))
    write_atomic_bytes(output_directory / "provider-wait.stderr.txt", wait_result.stderr.encode("utf-8"))
    write_atomic_bytes(output_directory / "provider-inspect.json", inspect_result.stdout.encode("utf-8"))
    write_atomic_bytes(output_directory / "provider-stats.stdout.txt", stats_result.stdout.encode("utf-8"))
    write_atomic_bytes(output_directory / "provider-stats.stderr.txt", stats_result.stderr.encode("utf-8"))
    write_atomic_bytes(output_directory / "provider-logs.txt", logs_result.stdout.encode("utf-8"))
    if inspect_result.returncode or logs_result.returncode:
        raise HardwareProbeError("provider evidence collection failed")
    inspections = _parse_json_array(inspect_result.stdout, label="provider inspection")
    if len(inspections) != 1:
        raise HardwareProbeError("provider inspection did not return exactly one job")
    marked = [
        line.split(RECEIPT_MARKER, 1)[1].strip() for line in logs_result.stdout.splitlines() if RECEIPT_MARKER in line
    ]
    if len(marked) != 1:
        raise HardwareProbeError("provider logs do not contain exactly one hardware-probe receipt")
    try:
        receipt = json.loads(marked[0])
    except json.JSONDecodeError as exc:
        raise HardwareProbeError(f"provider receipt is invalid JSON: {exc}") from exc
    if not isinstance(receipt, dict):
        raise HardwareProbeError("provider receipt is not a JSON object")
    validate_schema(receipt, RECEIPT_SCHEMA, label="hardware-probe receipt")
    if receipt["provider_job"]["job_id"] != job_id:
        raise HardwareProbeError("provider receipt job ID drift")
    receipt, provider_evidence = reconcile_provider_receipt(
        receipt=receipt,
        inspection=inspections[0],
        job_id=job_id,
        authorization_sha256=authorization_sha256,
        authorization=authorization,
        wait_returncode=wait_result.returncode,
    )
    provider_evidence["stats_command_succeeded"] = stats_result.returncode == 0
    validate_schema(receipt, RECEIPT_SCHEMA, label="reconciled hardware-probe receipt")
    write_atomic(output_directory / "provider-evidence.json", provider_evidence)
    write_atomic(output_directory / "worker-receipt.json", receipt)
    return receipt


def _artifact(path: Path) -> dict[str, Any]:
    if path.is_file():
        return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if not path.is_dir():
        raise HardwareProbeError(f"missing checkpoint artifact: {path}")
    digest = hashlib.sha256()
    total_bytes = 0
    for child in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        relative = child.relative_to(path).as_posix().encode("utf-8")
        payload_hash = sha256_file(child).encode("ascii")
        size = child.stat().st_size
        digest.update(relative + b"\0" + str(size).encode("ascii") + b"\0" + payload_hash + b"\n")
        total_bytes += size
    if total_bytes <= 0:
        raise HardwareProbeError(f"empty checkpoint artifact: {path}")
    return {"bytes": total_bytes, "sha256": digest.hexdigest()}


def verify_snapshot(model_directory: Path) -> None:
    for relative, (expected_bytes, expected_sha256) in SNAPSHOT_FILES.items():
        path = model_directory / relative
        if not path.is_file():
            raise HardwareProbeError(f"model snapshot file missing: {relative}")
        if path.stat().st_size != expected_bytes:
            raise HardwareProbeError(f"model snapshot byte drift: {relative}")
        if sha256_file(path) != expected_sha256:
            raise HardwareProbeError(f"model snapshot hash drift: {relative}")


def download_snapshot(target: Path) -> None:
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=MODEL_IDENTIFIER,
        revision=MODEL_REVISION,
        local_dir=target,
        allow_patterns=sorted(SNAPSHOT_FILES),
    )
    verify_snapshot(target)


def _runtime_package_digest() -> str:
    versions: list[str] = []
    for requirement in REQUIRED_PACKAGES:
        name, expected = requirement.split("==", 1)
        actual = importlib.metadata.version(name)
        if actual != expected:
            raise HardwareProbeError(f"package drift: {name} is {actual}, expected {expected}")
        versions.append(requirement)
    return sha256_bytes(("\n".join(versions) + "\n").encode("utf-8"))


def _gpu_evidence() -> dict[str, Any]:
    import torch

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise HardwareProbeError("probe requires exactly one CUDA GPU")
    name = torch.cuda.get_device_name(0)
    if name != "NVIDIA L40S":
        raise HardwareProbeError(f"wrong GPU: {name}")
    total_memory = int(torch.cuda.get_device_properties(0).total_memory)
    if total_memory < 45 * 1024**3:
        raise HardwareProbeError(f"insufficient L40S memory: {total_memory} bytes")
    return {"count": 1, "name": name, "total_memory_bytes": total_memory}


def _cuda_evidence() -> tuple[str, str]:
    import torch

    runtime = str(torch.version.cuda or "unknown")
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
        check=False,
        capture_output=True,
        text=True,
    )
    driver = result.stdout.strip()
    if result.returncode or not driver:
        raise HardwareProbeError("cannot resolve the NVIDIA driver version")
    return runtime, driver


def _fixed_fixture(tokenizer: Any, *, sequence_length: int) -> dict[str, Any]:
    import torch

    sentence = "Це суто синтетичне речення для перевірки обчислювального шляху без навчальних даних. "
    encoded = tokenizer(
        sentence * (sequence_length * 2),
        add_special_tokens=True,
        max_length=sequence_length,
        padding="max_length",
        return_attention_mask=True,
        return_special_tokens_mask=True,
        return_tensors="pt",
        truncation=True,
    )
    input_ids = encoded["input_ids"]
    attention_mask = encoded["attention_mask"]
    special_tokens_mask = encoded["special_tokens_mask"]
    if tuple(input_ids.shape) != (1, sequence_length) or int(attention_mask.sum()) != sequence_length:
        raise HardwareProbeError("synthetic fixture did not produce one full-length sequence")
    labels = input_ids.clone()
    labels[(attention_mask == 0) | (special_tokens_mask != 0)] = -100
    fixture_sha256 = sha256_bytes(input_ids.numpy().tobytes())
    return {
        "attention_mask": attention_mask.to("cuda:0"),
        "fixture_sha256": fixture_sha256,
        "input_ids": input_ids.to("cuda:0"),
        "labels": labels.to("cuda:0"),
        "tokens": int(attention_mask.sum()),
        "torch": torch,
    }


def _load_probe_model(model_directory: Path, *, checkpoint_directory: Path | None) -> tuple[Any, Any]:
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForMultimodalLM, AutoProcessor, BitsAndBytesConfig

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    processor = AutoProcessor.from_pretrained(model_directory, local_files_only=True)
    model = AutoModelForMultimodalLM.from_pretrained(
        model_directory,
        device_map={"": 0},
        local_files_only=True,
        quantization_config=quantization,
        torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    if checkpoint_directory is None:
        model = get_peft_model(
            model,
            LoraConfig(
                r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            ),
        )
    else:
        model = PeftModel.from_pretrained(model, checkpoint_directory / "adapter", is_trainable=True)
    return processor, model


def _phase_child(
    result_queue: Any,
    *,
    model_directory: str,
    checkpoint_input: str | None,
    checkpoint_output: str,
    progress_marker: str,
    global_step: int,
) -> None:
    phase_evidence: dict[str, Any] | None = None
    try:
        import torch
        from bitsandbytes.optim import PagedAdamW8bit

        torch.manual_seed(6170)
        torch.cuda.manual_seed_all(6170)
        torch.cuda.reset_peak_memory_stats()
        input_checkpoint = Path(checkpoint_input) if checkpoint_input else None
        processor, model = _load_probe_model(Path(model_directory), checkpoint_directory=input_checkpoint)
        fixture = _fixed_fixture(processor.tokenizer, sequence_length=4096)
        optimizer = PagedAdamW8bit(
            (parameter for parameter in model.parameters() if parameter.requires_grad),
            lr=1e-5,
            weight_decay=0.1,
        )
        if input_checkpoint is not None:
            step = json.loads((input_checkpoint / "step.json").read_text(encoding="utf-8"))
            if int(step["global_step"]) != global_step:
                raise HardwareProbeError("checkpoint global-step drift")
            optimizer.load_state_dict(
                torch.load(input_checkpoint / "optimizer.pt", map_location="cpu", weights_only=True)
            )
            rng_state = torch.load(input_checkpoint / "rng.pt", map_location="cpu", weights_only=True)
            torch.set_rng_state(rng_state["cpu"])
            torch.cuda.set_rng_state_all(rng_state["cuda"])
        model.train()
        optimizer.zero_grad(set_to_none=True)
        started = time.monotonic()
        output = model(
            input_ids=fixture["input_ids"],
            attention_mask=fixture["attention_mask"],
            labels=fixture["labels"],
        )
        loss = output.loss
        if loss is None or not torch.isfinite(loss):
            raise HardwareProbeError("non-finite probe loss")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            (parameter for parameter in model.parameters() if parameter.requires_grad),
            max_norm=1.0,
        )
        phase_evidence = {
            "fixture_sha256": fixture["fixture_sha256"],
            "global_step": global_step + 1,
            "loss": float(loss.detach().cpu()),
            "optimizer_step_performed": False,
            "tokens": fixture["tokens"],
        }
        optimizer.step()
        phase_evidence["optimizer_step_performed"] = True
        write_atomic(Path(progress_marker), phase_evidence)
        torch.cuda.synchronize()
        elapsed = time.monotonic() - started
        target = Path(checkpoint_output)
        target.mkdir(parents=True, exist_ok=False)
        adapter_path = target / "adapter"
        model.save_pretrained(adapter_path, safe_serialization=True)
        optimizer_path = target / "optimizer.pt"
        rng_path = target / "rng.pt"
        step_path = target / "step.json"
        torch.save(optimizer.state_dict(), optimizer_path)
        torch.save(
            {"cpu": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state_all()},
            rng_path,
        )
        step_path.write_text(canonical_json({"global_step": global_step + 1}) + "\n", encoding="utf-8")
        result_queue.put(
            {
                "adapter": _artifact(adapter_path),
                "checkpoint": _artifact(target),
                "elapsed_seconds": elapsed,
                "fixture_sha256": fixture["fixture_sha256"],
                "global_step": global_step + 1,
                "loss": float(loss.detach().cpu()),
                "optimizer": _artifact(optimizer_path),
                "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
                "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
                "rng": _artifact(rng_path),
                "tokens": fixture["tokens"],
            }
        )
    except BaseException as exc:  # child must return one durable failure message
        result_queue.put(
            {
                "error": f"{type(exc).__name__}: {exc}",
                "phase_evidence": phase_evidence,
            }
        )
        raise


def run_phase_process(
    *,
    model_directory: Path,
    checkpoint_input: Path | None,
    checkpoint_output: Path,
    global_step: int,
    deadline_monotonic: float,
) -> dict[str, Any]:
    progress_marker = checkpoint_output.parent / f".{checkpoint_output.name}.optimizer-step.json"
    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue(maxsize=1)
    process = context.Process(
        target=_phase_child,
        kwargs={
            "result_queue": result_queue,
            "model_directory": str(model_directory),
            "checkpoint_input": str(checkpoint_input) if checkpoint_input else None,
            "checkpoint_output": str(checkpoint_output),
            "progress_marker": str(progress_marker),
            "global_step": global_step,
        },
    )
    try:
        process.start()
    except BaseException as exc:
        raise PhaseExecutionError(
            f"probe child could not start: {type(exc).__name__}: {exc}",
            phase_evidence=None,
            process_started=False,
        ) from exc
    remaining = max(0.0, deadline_monotonic - time.monotonic())
    process.join(timeout=remaining)
    if process.is_alive():
        process.terminate()
        process.join(timeout=10)
        if process.is_alive():
            process.kill()
            process.join(timeout=5)
        phase_evidence = read_json(progress_marker) if progress_marker.is_file() else None
        raise PhaseExecutionError(
            "probe child exceeded the internal deadline",
            phase_evidence=phase_evidence,
            process_started=True,
        )
    try:
        result = result_queue.get(timeout=2)
    except Empty as exc:
        phase_evidence = read_json(progress_marker) if progress_marker.is_file() else None
        raise PhaseExecutionError(
            f"probe child exited {process.exitcode} without evidence",
            phase_evidence=phase_evidence,
            process_started=True,
        ) from exc
    if process.exitcode != 0 or "error" in result:
        phase_evidence = (
            read_json(progress_marker)
            if progress_marker.is_file()
            else result.get("phase_evidence")
        )
        raise PhaseExecutionError(
            str(result.get("error", f"probe child exited {process.exitcode}")),
            phase_evidence=phase_evidence,
            process_started=True,
        )
    phase_evidence = read_json(progress_marker) if progress_marker.is_file() else None
    if not phase_evidence or phase_evidence.get("global_step") != global_step + 1:
        raise PhaseExecutionError(
            "probe child returned without the durable optimizer-step marker",
            phase_evidence=phase_evidence,
            process_started=True,
        )
    return result


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _completed_worker_receipt(
    *,
    authorization_sha256: str,
    job_id: str,
    started_at: str,
    started_monotonic: float,
    packages_sha256: str,
    gpu: Mapping[str, Any],
    cuda_runtime: str,
    cuda_driver: str,
    first: Mapping[str, Any],
    second: Mapping[str, Any],
) -> dict[str, Any]:
    if first["fixture_sha256"] != second["fixture_sha256"]:
        raise HardwareProbeError("synthetic fixture changed across the process boundary")
    wall_seconds = time.monotonic() - started_monotonic
    if wall_seconds > 3600:
        raise HardwareProbeError("worker exceeded the provider timeout envelope")
    total_step_seconds = float(first["elapsed_seconds"]) + float(second["elapsed_seconds"])
    tokens_processed = int(first["tokens"]) + int(second["tokens"])
    return {
        "abort_reason": None,
        "attempt": 1,
        "authorization_sha256": authorization_sha256,
        "checkpoint_resume": {
            "adapter": first["adapter"],
            "optimizer": first["optimizer"],
            "process_boundary": True,
            "reload_passed": second["global_step"] == 2,
            "rng": first["rng"],
        },
        "environment": {
            "cuda_driver": cuda_driver,
            "cuda_runtime": cuda_runtime,
            "packages_sha256": packages_sha256,
            "python": platform.python_version(),
            "runner_sha256": sha256_file(Path(__file__).resolve()),
        },
        "facts": {
            "data_upload_performed": False,
            "evaluation_data_used": False,
            "model_or_checkpoint_upload_performed": False,
            "model_quality_evaluation_performed": False,
            "private_job_script_transport_used": True,
            "publication_performed": False,
            "purpose": "hardware_validation_non_treatment",
            "synthetic_adapter_optimizer_updates_performed": True,
            "treatment_data_used": False,
            "treatment_stage_1_performed": False,
        },
        "gpu": {
            **gpu,
            "peak_allocated_bytes": max(first["peak_allocated_bytes"], second["peak_allocated_bytes"]),
            "peak_reserved_bytes": max(first["peak_reserved_bytes"], second["peak_reserved_bytes"]),
        },
        "plan": {
            "bytes": 2537,
            "logical_path": "data/projects/open_model_data/treatments/gemma4_it_l40s_hf_jobs_probe_plan_v1.json",
            "sha256": EXPECTED_PLAN_SHA256,
        },
        "probe_id": PROBE_ID,
        "provider_job": {
            "actual_invoice_cost_eur": None,
            "actual_invoice_cost_usd": None,
            "billing_usd_per_minute": 0.03,
            "exposed_ports": False,
            "hardware_flavor": "l40sx1",
            "job_id": job_id,
            "job_status": "worker_completed_pending_provider_reconciliation",
            "maximum_provider_charge_usd": 1.8,
            "provider": "Hugging Face Jobs",
            "provider_derived_cost_usd": None,
            "provider_evidence_reconciled": False,
            "provider_running_seconds": None,
            "timeout_seconds": 3600,
        },
        "runtime": {
            "ended_at": _iso_now(),
            "provider_timeout_enforced": True,
            "started_at": started_at,
            "wall_seconds": wall_seconds,
        },
        "schema_version": "gemma_hardware_probe_receipt_v1",
        "snapshot_verification": {
            "all_files_bytes_match": True,
            "all_files_sha256_match": True,
            "manifest": {
                "bytes": 1994,
                "logical_path": "data/projects/open_model_data/treatments/gemma4_it_model_snapshot_manifest_v1.json",
                "sha256": "f0552bd6ee21764a0fc8c62b76d8458775f4f5e4969d701cf4c0d35c2f86fba1",
            },
        },
        "status": "completed",
        "throughput": {
            "elapsed_seconds": total_step_seconds,
            "fixture_sha256": first["fixture_sha256"],
            "sequence_length": 4096,
            "tokens_per_second": tokens_processed / total_step_seconds,
            "tokens_processed": tokens_processed,
        },
        "training_probe": {
            "adapter": "qlora_rank16_alpha32_dropout0.05",
            "loss_after_resume": second["loss"],
            "loss_before_checkpoint": first["loss"],
            "nonfinite_detected": False,
            "optimizer_steps_after_resume": 1,
            "optimizer_steps_before_checkpoint": 1,
            "quantization": "4bit_nf4_bf16_double_quantization",
        },
    }


def run_worker(*, plan_sha256: str, authorization_sha256: str) -> dict[str, Any]:
    if plan_sha256 != EXPECTED_PLAN_SHA256:
        raise HardwareProbeError("worker plan hash differs from the frozen plan")
    if not re.fullmatch(r"[a-f0-9]{64}", authorization_sha256):
        raise HardwareProbeError("worker authorization hash is invalid")
    if os.environ.get("ACCELERATOR") != "l40sx1":
        raise HardwareProbeError("Hugging Face Jobs accelerator does not match l40sx1")
    job_id = os.environ.get("JOB_ID", "")
    if not JOB_ID_PATTERN.fullmatch(job_id):
        raise HardwareProbeError("missing or invalid Hugging Face Job ID")

    started_at = _iso_now()
    started = time.monotonic()
    deadline = started + 3300
    packages_sha256 = _runtime_package_digest()
    gpu = _gpu_evidence()
    cuda_runtime, cuda_driver = _cuda_evidence()
    work_directory = Path(tempfile.mkdtemp(prefix="gemma4-hardware-probe-"))
    model_directory = work_directory / "model"
    download_snapshot(model_directory)
    partial_evidence = {
        "cuda_driver": cuda_driver,
        "cuda_runtime": cuda_runtime,
        "gpu": gpu,
        "packages_sha256": packages_sha256,
        "python": platform.python_version(),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "snapshot_verified": True,
    }
    try:
        first = run_phase_process(
            model_directory=model_directory,
            checkpoint_input=None,
            checkpoint_output=work_directory / "checkpoint-step-1",
            global_step=0,
            deadline_monotonic=deadline,
        )
    except PhaseExecutionError as exc:
        partial_evidence["first_progress"] = exc.phase_evidence
        raise ProbeExecutionError(
            f"first phase failed: {type(exc).__name__}: {exc}",
            partial_evidence=partial_evidence,
        ) from exc
    partial_evidence["first"] = first
    try:
        write_atomic(work_directory / "partial-progress.json", partial_evidence)
        second = run_phase_process(
            model_directory=model_directory,
            checkpoint_input=work_directory / "checkpoint-step-1",
            checkpoint_output=work_directory / "checkpoint-step-2",
            global_step=1,
            deadline_monotonic=deadline,
        )
        partial_evidence["resume_process_started"] = True
        partial_evidence["second"] = second
        return _completed_worker_receipt(
            authorization_sha256=authorization_sha256,
            job_id=job_id,
            started_at=started_at,
            started_monotonic=started,
            packages_sha256=packages_sha256,
            gpu=gpu,
            cuda_runtime=cuda_runtime,
            cuda_driver=cuda_driver,
            first=first,
            second=second,
        )
    except BaseException as exc:
        if isinstance(exc, PhaseExecutionError):
            partial_evidence["resume_process_started"] = exc.process_started
            partial_evidence["second_progress"] = exc.phase_evidence
        raise ProbeExecutionError(
            f"worker failed after the first optimizer step: {type(exc).__name__}: {exc}",
            partial_evidence=partial_evidence,
        ) from exc


def aborted_worker_receipt(
    *,
    authorization_sha256: str,
    abort_reason: str,
    started_at: str,
    started_monotonic: float,
    partial_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Represent a provider-job failure without inventing unavailable evidence."""
    partial = dict(partial_evidence or {})
    first = partial.get("first") if isinstance(partial.get("first"), dict) else None
    second = partial.get("second") if isinstance(partial.get("second"), dict) else None
    first_progress = (
        partial.get("first_progress") if isinstance(partial.get("first_progress"), dict) else None
    )
    second_progress = (
        partial.get("second_progress") if isinstance(partial.get("second_progress"), dict) else None
    )
    first_step_completed = bool(first and first.get("global_step") == 1)
    second_step_completed = bool(second and second.get("global_step") == 2)
    first_step_performed = first_step_completed or bool(
        first_progress
        and first_progress.get("global_step") == 1
        and first_progress.get("optimizer_step_performed") is True
    )
    second_step_performed = second_step_completed or bool(
        second_progress
        and second_progress.get("global_step") == 2
        and second_progress.get("optimizer_step_performed") is True
    )
    first_observation = first if first_step_completed else first_progress
    second_observation = second if second_step_completed else second_progress
    gpu = partial.get("gpu") if isinstance(partial.get("gpu"), dict) else {}
    elapsed_seconds = None
    if first_step_completed and (not second_step_performed or second_step_completed):
        elapsed_seconds = float(first["elapsed_seconds"]) + (
            float(second["elapsed_seconds"]) if second_step_completed else 0.0
        )
    tokens_processed = sum(
        int(observation["tokens"])
        for observation in (first_observation, second_observation)
        if observation and observation.get("optimizer_step_performed", True) is True
    ) or None
    job_id = os.environ.get("JOB_ID", "unavailable")
    valid_authorization_sha256 = (
        authorization_sha256 if re.fullmatch(r"[a-f0-9]{64}", authorization_sha256) else "0" * 64
    )
    return {
        "abort_reason": abort_reason,
        "attempt": 1,
        "authorization_sha256": valid_authorization_sha256,
        "checkpoint_resume": {
            "adapter": first.get("adapter") if first_step_completed else None,
            "optimizer": first.get("optimizer") if first_step_completed else None,
            "process_boundary": bool(partial.get("resume_process_started")),
            "reload_passed": second_step_performed if first_step_performed else None,
            "rng": first.get("rng") if first_step_completed else None,
        },
        "environment": {
            "cuda_driver": partial.get("cuda_driver"),
            "cuda_runtime": partial.get("cuda_runtime"),
            "packages_sha256": partial.get("packages_sha256"),
            "python": partial.get("python"),
            "runner_sha256": partial.get("runner_sha256") or sha256_file(Path(__file__).resolve()),
        },
        "facts": {
            "data_upload_performed": False,
            "evaluation_data_used": False,
            "model_or_checkpoint_upload_performed": False,
            "model_quality_evaluation_performed": False,
            "private_job_script_transport_used": True,
            "publication_performed": False,
            "purpose": "hardware_validation_non_treatment",
            "synthetic_adapter_optimizer_updates_performed": first_step_performed or second_step_performed,
            "treatment_data_used": False,
            "treatment_stage_1_performed": False,
        },
        "gpu": {
            "count": int(gpu.get("count", 0)),
            "name": gpu.get("name"),
            "peak_allocated_bytes": (
                max(first["peak_allocated_bytes"], second["peak_allocated_bytes"])
                if second_step_completed
                else first.get("peak_allocated_bytes") if first_step_completed else None
            ),
            "peak_reserved_bytes": (
                max(first["peak_reserved_bytes"], second["peak_reserved_bytes"])
                if second_step_completed
                else first.get("peak_reserved_bytes") if first_step_completed else None
            ),
            "total_memory_bytes": gpu.get("total_memory_bytes"),
        },
        "plan": {
            "bytes": 2537,
            "logical_path": "data/projects/open_model_data/treatments/gemma4_it_l40s_hf_jobs_probe_plan_v1.json",
            "sha256": EXPECTED_PLAN_SHA256,
        },
        "probe_id": PROBE_ID,
        "provider_job": {
            "actual_invoice_cost_eur": None,
            "actual_invoice_cost_usd": None,
            "billing_usd_per_minute": 0.03,
            "exposed_ports": False,
            "hardware_flavor": "l40sx1",
            "job_id": job_id,
            "job_status": "worker_aborted_pending_provider_reconciliation",
            "maximum_provider_charge_usd": 1.8,
            "provider": "Hugging Face Jobs",
            "provider_derived_cost_usd": None,
            "provider_evidence_reconciled": False,
            "provider_running_seconds": None,
            "timeout_seconds": 3600,
        },
        "runtime": {
            "ended_at": _iso_now(),
            "provider_timeout_enforced": True,
            "started_at": started_at,
            "wall_seconds": max(0.0, min(3600.0, time.monotonic() - started_monotonic)),
        },
        "schema_version": "gemma_hardware_probe_receipt_v1",
        "snapshot_verification": {
            "all_files_bytes_match": True if partial.get("snapshot_verified") else None,
            "all_files_sha256_match": True if partial.get("snapshot_verified") else None,
            "manifest": {
                "bytes": 1994,
                "logical_path": "data/projects/open_model_data/treatments/gemma4_it_model_snapshot_manifest_v1.json",
                "sha256": "f0552bd6ee21764a0fc8c62b76d8458775f4f5e4969d701cf4c0d35c2f86fba1",
            },
        },
        "status": "aborted",
        "throughput": {
            "elapsed_seconds": elapsed_seconds,
            "fixture_sha256": first_observation.get("fixture_sha256") if first_observation else None,
            "sequence_length": 4096 if first_step_performed else None,
            "tokens_per_second": (
                tokens_processed / elapsed_seconds
                if elapsed_seconds is not None and elapsed_seconds > 0 and tokens_processed is not None
                else None
            ),
            "tokens_processed": tokens_processed,
        },
        "training_probe": {
            "adapter": "qlora_rank16_alpha32_dropout0.05",
            "loss_after_resume": second_observation.get("loss") if second_observation else None,
            "loss_before_checkpoint": first_observation.get("loss") if first_observation else None,
            "nonfinite_detected": False,
            "optimizer_steps_after_resume": 1 if second_step_performed else 0,
            "optimizer_steps_before_checkpoint": 1 if first_step_performed else 0,
            "quantization": "4bit_nf4_bf16_double_quantization",
        },
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--plan", type=Path, default=PLAN_PATH)
    prepare.add_argument("--authorization", type=Path, required=True)
    prepare.add_argument("--hf-cli", type=Path, default=Path(".venv/bin/hf"))
    prepare.add_argument("--output", type=Path)
    launch = subparsers.add_parser("launch")
    launch.add_argument("--plan", type=Path, default=PLAN_PATH)
    launch.add_argument("--authorization", type=Path, required=True)
    launch.add_argument("--hf-cli", type=Path, default=Path(".venv/bin/hf"))
    collect = subparsers.add_parser("collect")
    collect.add_argument("--job-id", required=True)
    collect.add_argument("--authorization", type=Path, required=True)
    collect.add_argument("--hf-cli", type=Path, default=Path(".venv/bin/hf"))
    collect.add_argument("--output-directory", type=Path, required=True)
    worker = subparsers.add_parser("worker")
    worker.add_argument("--plan-sha256", required=True)
    worker.add_argument("--authorization-sha256", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "worker":
        started_at = _iso_now()
        started_monotonic = time.monotonic()
        try:
            receipt = run_worker(
                plan_sha256=args.plan_sha256,
                authorization_sha256=args.authorization_sha256,
            )
        except BaseException as exc:
            receipt = aborted_worker_receipt(
                authorization_sha256=args.authorization_sha256,
                abort_reason=f"{type(exc).__name__}: {exc}",
                started_at=started_at,
                started_monotonic=started_monotonic,
                partial_evidence=getattr(exc, "partial_evidence", None),
            )
            print(f"{RECEIPT_MARKER}{canonical_json(receipt)}")
            return 2
        print(f"{RECEIPT_MARKER}{canonical_json(receipt)}")
        return 0
    if args.command == "collect":
        try:
            receipt = collect_job(
                job_id=args.job_id,
                hf_cli=args.hf_cli,
                authorization_path=args.authorization,
                output_directory=args.output_directory,
            )
        except HardwareProbeError as exc:
            print(f"hardware probe collection failed: {exc}")
            return 2
        print(canonical_json(receipt))
        return 0
    try:
        command = build_hf_job_command(
            plan_path=args.plan,
            authorization_path=args.authorization,
            hf_cli=args.hf_cli,
        )
        safe_command = safe_job_command(
            command,
            script_path=Path(__file__).resolve(),
            script_placeholder="<WORKTREE_RUNNER>",
        )
        prepared = {
            "authorization_sha256": sha256_file(args.authorization),
            "command": safe_command,
            "model_call_performed": False,
            "paid_job_launched": False,
            "plan_sha256": EXPECTED_PLAN_SHA256,
            "probe_id": PROBE_ID,
        }
        if args.command == "prepare":
            if args.output:
                write_atomic(args.output, prepared)
            print(canonical_json(prepared))
            return 0
        require_hf_auth(command[0])
        require_no_provider_attempt(
            hf_cli=command[0],
            authorization_sha256=prepared["authorization_sha256"],
        )
        launch_started_at = _iso_now()
        global_claim_path = host_global_attempt_claim_path(prepared["authorization_sha256"])
        claim_paid_attempt(
            global_claim_path,
            {
                **prepared,
                "claim_scope": "host_global_all_worktrees",
                "launch_started_at": launch_started_at,
                "status": "host_global_launch_claimed_before_provider_call",
            },
        )
        claim_paid_attempt(
            ATTEMPT_LEDGER_PATH,
            {
                **prepared,
                "launch_started_at": launch_started_at,
                "maximum_provider_charge_usd": 1.8,
                "paid_attempt_claimed": True,
                "provider_timeout_seconds": 3600,
                "status": "launch_claimed_before_provider_call",
            },
        )
        require_no_provider_attempt(
            hf_cli=command[0],
            authorization_sha256=prepared["authorization_sha256"],
        )
        authorized_runner_snapshot = create_authorized_runner_snapshot(
            authorization_path=args.authorization,
            output_directory=ATTEMPT_LEDGER_PATH.parent,
        )
        command = build_hf_job_command(
            plan_path=args.plan,
            authorization_path=args.authorization,
            hf_cli=args.hf_cli,
            script_path=authorized_runner_snapshot,
        )
        verify_authorized_runner_snapshot(
            snapshot=authorized_runner_snapshot,
            authorization_path=args.authorization,
        )
        prepared = {
            **prepared,
            "command": safe_job_command(
                command,
                script_path=authorized_runner_snapshot,
                script_placeholder="<AUTHORIZED_RUNNER_SNAPSHOT>",
            ),
            "command_source": "private_read_only_authorized_snapshot",
        }
        ready_claim = {
            **prepared,
            "launch_started_at": launch_started_at,
            "maximum_provider_charge_usd": 1.8,
            "paid_attempt_claimed": True,
            "provider_timeout_seconds": 3600,
            "status": "authorized_snapshot_verified_before_provider_call",
        }
        write_atomic(global_claim_path, {**ready_claim, "claim_scope": "host_global_all_worktrees"})
        write_atomic(ATTEMPT_LEDGER_PATH, ready_claim)
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode:
            failure = {
                **prepared,
                "launch_started_at": launch_started_at,
                "maximum_provider_charge_usd": 1.8,
                "paid_attempt_claimed": True,
                "provider_timeout_seconds": 3600,
                "status": "provider_launch_failed_no_retry_authorized",
            }
            write_atomic(ATTEMPT_LEDGER_PATH, failure)
            write_atomic(global_claim_path, {**failure, "claim_scope": "host_global_all_worktrees"})
            raise HardwareProbeError("Hugging Face Job launch failed after the paid attempt was claimed")
        job_id = parse_job_id(f"{result.stdout}\n{result.stderr}")
        launch_receipt = {
            **prepared,
            "job_id": job_id,
            "paid_job_launched": True,
            "provider_timeout_seconds": 3600,
            "maximum_provider_charge_usd": 1.8,
            "paid_attempt_claimed": True,
            "status": "provider_job_created",
        }
        write_atomic(ATTEMPT_LEDGER_PATH, launch_receipt)
        write_atomic(global_claim_path, {**launch_receipt, "claim_scope": "host_global_all_worktrees"})
        print(canonical_json(launch_receipt))
        return 0
    except HardwareProbeError as exc:
        print(f"hardware probe failed: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
