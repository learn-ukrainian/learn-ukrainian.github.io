#!/usr/bin/env python3
"""Hash-first Hugging Face Jobs transport with no mounted volumes."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

JOB_ID_PATTERN = re.compile(r"[a-f0-9]{20,64}")
SHA256_PATTERN = re.compile(r"[a-f0-9]{64}")
REPO_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}")
SAFE_PATH_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.\-/]{0,255}")
TRANSPORT_RECEIPT_SCHEMA = "ua_open_weight_eval_hf_jobs_transport_receipt.v1"


class TransportError(ValueError):
    """Raised when the no-volume transport contract cannot be satisfied."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TransportError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_path(value: str, *, label: str) -> str:
    _require(SAFE_PATH_PATTERN.fullmatch(value) is not None, f"invalid {label}")
    _require(".." not in value.split("/"), f"unsafe {label}")
    return value.strip("/")


def verify_manifest(value: Mapping[str, Any], expected_bundle_sha256: str) -> list[dict[str, Any]]:
    _require(value.get("schema_version") == "ua_open_weight_eval_hf_jobs_bundle.v1", "bundle schema drift")
    _require(SHA256_PATTERN.fullmatch(expected_bundle_sha256) is not None, "invalid expected bundle SHA-256")
    unsigned = {key: item for key, item in value.items() if key != "bundle_sha256"}
    observed = sha256_bytes(canonical_json(unsigned).encode("utf-8"))
    _require(value.get("bundle_sha256") == expected_bundle_sha256 == observed, "bundle digest drift")
    records = value.get("files")
    _require(isinstance(records, list) and bool(records), "bundle file records are missing")
    paths: set[str] = set()
    verified: list[dict[str, Any]] = []
    for raw in records:
        _require(isinstance(raw, dict), "bundle file record drift")
        path = _safe_path(str(raw.get("path", "")), label="bundle file path")
        _require("/" not in path, "bundle files must be flat")
        _require(path not in paths, "duplicate bundle file path")
        size = raw.get("bytes")
        digest = raw.get("sha256")
        _require(isinstance(size, int) and not isinstance(size, bool) and size >= 0, "bundle byte record drift")
        _require(isinstance(digest, str) and SHA256_PATTERN.fullmatch(digest) is not None, "bundle hash record drift")
        paths.add(path)
        verified.append({"path": path, "bytes": size, "sha256": digest})
    required = {
        "canary_selection.json",
        "hf_jobs_transport.py",
        "hf_jobs_worker.py",
        "requests.jsonl",
        "run_config.json",
    }
    _require(required.issubset(paths), "bundle runtime files are missing")
    return verified


def download_verified_bundle(
    *, repo_id: str, revision: str, prefix: str, bundle_sha256: str, output: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    from huggingface_hub import hf_hub_download

    _require(REPO_ID_PATTERN.fullmatch(repo_id) is not None, "invalid transport repository")
    _require(re.fullmatch(r"[a-f0-9]{40}", revision) is not None, "transport revision must be an immutable commit")
    prefix = _safe_path(prefix, label="transport prefix")
    output.mkdir(parents=True, exist_ok=False)
    manifest_source = Path(
        hf_hub_download(
            repo_id=repo_id,
            repo_type="dataset",
            revision=revision,
            filename=f"{prefix}/BUNDLE_MANIFEST.json",
            token=True,
        )
    )
    manifest = json.loads(manifest_source.read_text(encoding="utf-8"))
    _require(isinstance(manifest, dict), "bundle manifest is not an object")
    records = verify_manifest(manifest, bundle_sha256)
    downloaded: list[dict[str, Any]] = []
    for record in records:
        source = Path(
            hf_hub_download(
                repo_id=repo_id,
                repo_type="dataset",
                revision=revision,
                filename=f"{prefix}/{record['path']}",
                token=True,
            )
        )
        destination = output / record["path"]
        destination.write_bytes(source.read_bytes())
        _require(destination.stat().st_size == record["bytes"], f"download byte drift: {record['path']}")
        digest = sha256_file(destination)
        _require(digest == record["sha256"], f"download hash drift: {record['path']}")
        downloaded.append({**record, "verified_sha256": digest})
    (output / "BUNDLE_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest, downloaded


def upload_json(*, repo_id: str, path_in_repo: str, value: Mapping[str, Any], commit_message: str) -> str:
    from huggingface_hub import HfApi

    payload = (json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    api = HfApi(token=os.environ["HF_TOKEN"])
    _require(bool(api.repo_info(repo_id=repo_id, repo_type="dataset").private), "artifact repository is not private")
    info = api.upload_file(
        path_or_fileobj=io.BytesIO(payload),
        path_in_repo=_safe_path(path_in_repo, label="upload path"),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message=commit_message,
    )
    oid = getattr(info, "oid", None)
    _require(isinstance(oid, str) and re.fullmatch(r"[a-f0-9]{40}", oid) is not None, "upload commit is missing")
    return oid


def run_preflight(args: argparse.Namespace, files: list[dict[str, Any]]) -> dict[str, Any]:
    job_id = os.environ.get("JOB_ID", "")
    _require(JOB_ID_PATTERN.fullmatch(job_id) is not None, "missing or invalid Hugging Face Job ID")
    _require(os.environ.get("ACCELERATOR") == "none", "CPU preflight unexpectedly has an accelerator")
    receipt = {
        "schema_version": TRANSPORT_RECEIPT_SCHEMA,
        "status": "passed",
        "mode": "preflight",
        "job_id": job_id,
        "hardware_flavor": "cpu-basic",
        "container_reached_running": True,
        "transport": {
            "repository": args.transport_repo,
            "revision": args.transport_revision,
            "prefix": args.transport_prefix,
            "bundle_sha256": args.bundle_sha256,
            "downloaded_files": files,
            "all_hashes_verified": True,
            "mounted_volumes": 0,
        },
        "facts": {
            "model_execution_started": False,
            "model_weights_downloaded": False,
            "receipt_uploaded_directly": True,
        },
    }
    path = f"{_safe_path(args.artifact_prefix, label='artifact prefix')}/{job_id}/transport_receipt.json"
    receipt["upload_commit"] = upload_json(
        repo_id=args.transport_repo,
        path_in_repo=path,
        value=receipt,
        commit_message=f"transport preflight receipt {job_id}",
    )
    receipt["artifact_path"] = path
    return receipt


def run_worker(args: argparse.Namespace, root: Path) -> int:
    config = json.loads((root / "run_config.json").read_text(encoding="utf-8"))
    plugin = config["runtime"]["vllm_gguf_plugin"]["filename"]
    install = subprocess.run(
        ["uv", "pip", "install", "--system", str(root / plugin)],
        check=False,
    )
    _require(install.returncode == 0, "verified plugin installation failed")
    output = root / "output"
    command = [
        "python",
        str(root / "hf_jobs_worker.py"),
        "--mode",
        args.mode,
        "--config",
        str(root / "run_config.json"),
        "--requests",
        str(root / "requests.jsonl"),
        "--requests-sha256",
        args.requests_sha256,
        "--output-root",
        str(output),
        "--artifact-repo",
        args.transport_repo,
        "--artifact-prefix",
        _safe_path(args.artifact_prefix, label="artifact prefix"),
    ]
    if args.mode == "canary":
        command.extend(["--selection", str(root / "canary_selection.json")])
    return subprocess.run(command, check=False).returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["preflight", "canary", "full"], required=True)
    parser.add_argument("--transport-repo", required=True)
    parser.add_argument("--transport-revision", required=True)
    parser.add_argument("--transport-prefix", required=True)
    parser.add_argument("--artifact-prefix", required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--requests-sha256")
    parser.add_argument("--work-root", type=Path, default=Path("/workspace"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _require(bool(os.environ.get("HF_TOKEN")), "HF_TOKEN is required for private direct transport")
    _require(not args.work_root.exists(), "work root already exists")
    _, files = download_verified_bundle(
        repo_id=args.transport_repo,
        revision=args.transport_revision,
        prefix=args.transport_prefix,
        bundle_sha256=args.bundle_sha256,
        output=args.work_root,
    )
    if args.mode == "preflight":
        receipt = run_preflight(args, files)
        print(canonical_json(receipt))
        return 0
    _require(isinstance(args.requests_sha256, str), "request SHA-256 is required for model execution")
    return run_worker(args, args.work_root)


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as exc:
        print(canonical_json({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}), file=sys.stderr)
        raise
    raise SystemExit(exit_code)
