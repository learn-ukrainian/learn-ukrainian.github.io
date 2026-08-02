#!/usr/bin/env python3
"""Prepare, launch, reconcile, and publish the Issue #6273 HF Jobs baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import urllib.request
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.ua_open_weight_eval import hf_jobs_worker, suite_cli

CONFIG_PATH = ROOT / "data/projects/ua_open_weight_eval/runs/gemma4_qat_q4_0_hf_jobs_v1.json"
WORKER_PATH = ROOT / "scripts/projects/ua_open_weight_eval/hf_jobs_worker.py"
TRANSPORT_PATH = ROOT / "scripts/projects/ua_open_weight_eval/hf_jobs_transport.py"
LICENSE_PATH = ROOT / "LICENSE"
THIRD_PARTY_PATH = ROOT / "docs/projects/ua-open-weight-eval/THIRD_PARTY_NOTICES.md"
PUBLIC_FILES = frozenset(
    {
        "LICENSE-MIT.txt",
        "README.md",
        "RESULTS_MANIFEST.json",
        "SHA256SUMS",
        "THIRD_PARTY_NOTICES.md",
        "metrics.jsonl",
        "report.json",
        "responses.jsonl",
        "run_receipt.public.json",
    }
)
CATEGORIES = ("error", "correct_control", "protected", "unresolved")
RUN_MODES = frozenset({"canary", "full"})
LAUNCH_MODES = frozenset({"preflight", *RUN_MODES})
JOB_ID_PATTERN = re.compile(r"[a-f0-9]{20,64}")


class BaselineError(ValueError):
    """Raised when a baseline authorization or evidence contract fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BaselineError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    commit = completed.stdout.strip()
    _require(completed.returncode == 0 and re.fullmatch(r"[a-f0-9]{40}", commit) is not None, "source commit drift")
    return commit


def write_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    temporary.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"cannot read JSON {path}: {exc}") from exc
    _require(isinstance(value, dict), f"expected object in {path}")
    return value


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = read_json(path)
    hf_jobs_worker.verify_config(config)
    _require(config["authorization"]["issue"] == 6273, "authorization issue drift")
    _require(config["authorization"]["maximum_provider_cost_usd"] == 6.0, "cost ceiling drift")
    authorization = config["authorization"]
    _require(authorization["no_automatic_paid_retry"] is False, "retry policy drift")
    _require(authorization["recoverable_execution_retries_authorized"] is True, "retry authorization drift")
    prior_cost = float(authorization["prior_provider_cost_usd"])
    _require(0 <= prior_cost < authorization["maximum_provider_cost_usd"], "prior provider cost drift")
    incurred_costs = authorization["incurred_provider_costs"]
    _require(isinstance(incurred_costs, list) and incurred_costs, "incurred provider cost ledger drift")
    _require(
        len({entry.get("job_id") for entry in incurred_costs}) == len(incurred_costs)
        and all(
            isinstance(entry, dict)
            and JOB_ID_PATTERN.fullmatch(str(entry.get("job_id", ""))) is not None
            and entry.get("stage") in {"COMPLETED", "ERROR", "CANCELED"}
            and float(entry.get("provider_derived_cost_usd", -1)) >= 0
            for entry in incurred_costs
        ),
        "incurred provider cost ledger entry drift",
    )
    _require(
        round(sum(float(entry["provider_derived_cost_usd"]) for entry in incurred_costs), 6)
        == round(prior_cost, 6),
        "incurred provider costs do not match prior provider cost",
    )
    cpu_validation = authorization["validated_cpu_transport"]
    _require(cpu_validation["accepted_by_operator"] is True, "CPU transport acceptance drift")
    _require(JOB_ID_PATTERN.fullmatch(cpu_validation["job_id"]) is not None, "CPU transport job ID drift")
    _require(
        cpu_validation["container_reached_running"] is True
        and cpu_validation["complete_pinned_bundle_downloaded"] is True
        and cpu_validation["all_bundle_hashes_verified"] is True,
        "CPU transport evidence drift",
    )
    cpu_cost_entries = [entry for entry in incurred_costs if entry["job_id"] == cpu_validation["job_id"]]
    _require(len(cpu_cost_entries) == 1, "CPU transport cost is missing from incurred provider cost ledger")
    _require(
        float(cpu_validation["provider_derived_cost_usd"])
        == float(cpu_cost_entries[0]["provider_derived_cost_usd"]),
        "CPU transport cost does not match incurred provider cost ledger",
    )
    _require(
        re.fullmatch(r"[a-f0-9]{64}", cpu_validation["validated_bundle_sha256"]) is not None,
        "validated CPU bundle digest drift",
    )
    _require(
        re.fullmatch(r"[a-f0-9]{40}", cpu_validation["fixed_by_merge_commit"]) is not None,
        "CPU transport fix commit drift",
    )
    preflight = config["transport"]["cpu_preflight"]
    _require(config["transport"]["mounted_volumes"] == 0, "volume transport is prohibited")
    _require(
        config["canary"]["timeout_seconds"] / 60 * config["pricing"]["usd_per_minute"]
        <= config["canary"]["maximum_cost_usd"] == 0.6,
        "canary timeout exceeds its cost ceiling",
    )
    _require(preflight["flavor"] == "cpu-basic" and preflight["timeout_seconds"] == 300, "CPU preflight drift")
    _require(preflight["maximum_cost_usd"] == 0.001, "CPU preflight cost ceiling drift")
    _require(
        preflight["timeout_seconds"] / 3600 * preflight["usd_per_hour"] <= preflight["maximum_cost_usd"],
        "CPU preflight timeout exceeds its cost ceiling",
    )
    _require(config["suite"]["cases_sha256"] == sha256_file(suite_cli.CASES_PATH), "frozen cases drift")
    _require(config["suite"]["tracks"] == suite_cli.read_json(suite_cli.CONFIG_PATH)["tracks"], "track drift")
    return config


def balanced_canary(cases: Sequence[dict[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]:
    _require(len(cases) == 4000, "frozen suite must contain 4,000 cases")
    indexed = [
        {
            "position": position,
            "item_id": suite_cli.request_item_id(position),
            "case_id": case["case_id"],
            "category": case["category"],
            "tracks": list(case["tracks"]),
        }
        for position, case in enumerate(cases, 1)
    ]
    selected: list[dict[str, Any]] = []
    track_counts: Counter[str] = Counter()
    seed = f"issue-6273:{config['suite']['cases_sha256']}:canary-v1"
    per_category = int(config["canary"]["case_count"]) // len(CATEGORIES)
    _require(per_category * len(CATEGORIES) == config["canary"]["case_count"], "canary count is not category-balanced")
    for category in CATEGORIES:
        candidates = [row for row in indexed if row["category"] == category]
        for _ in range(per_category):
            choice = min(
                candidates,
                key=lambda row: (
                    sum(track_counts[track] for track in row["tracks"]),
                    max((track_counts[track] for track in row["tracks"]), default=0),
                    sha256_text(f"{seed}:{row['case_id']}"),
                ),
            )
            selected.append(choice)
            candidates.remove(choice)
            track_counts.update(choice["tracks"])
    selected.sort(key=lambda row: row["position"])
    category_counts = Counter(row["category"] for row in selected)
    _require(category_counts == Counter({category: per_category for category in CATEGORIES}), "canary balance drift")
    _require(set(track_counts) == set(config["suite"]["tracks"]), "canary does not cover all tracks")
    payload = {
        "schema_version": "ua_open_weight_eval_canary_selection.v1",
        "algorithm": config["canary"]["selection_algorithm"],
        "cases_sha256": config["suite"]["cases_sha256"],
        "case_count": len(selected),
        "item_ids": [row["item_id"] for row in selected],
        "source_case_ids": [row["case_id"] for row in selected],
        "category_counts": dict(sorted(category_counts.items())),
        "track_membership_counts": dict(sorted(track_counts.items())),
    }
    payload["selection_sha256"] = sha256_text(canonical_json(payload))
    return payload


def _download_file(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.download")
    try:
        with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def prepare_bundle(output_dir: Path, *, plugin_wheel: Path | None = None) -> dict[str, Any]:
    config = load_config()
    suite_cli.verify_release()
    _require(not output_dir.exists() or not any(output_dir.iterdir()), "bundle output directory is not empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    requests = output_dir / "requests.jsonl"
    suite_cli.prepare_requests(requests)
    selection = balanced_canary(suite_cli.read_jsonl(suite_cli.CASES_PATH), config)
    write_atomic(output_dir / "canary_selection.json", selection)
    shutil.copyfile(CONFIG_PATH, output_dir / "run_config.json")
    shutil.copyfile(WORKER_PATH, output_dir / "hf_jobs_worker.py")
    shutil.copyfile(TRANSPORT_PATH, output_dir / "hf_jobs_transport.py")
    plugin = config["runtime"]["vllm_gguf_plugin"]
    plugin_output = output_dir / plugin["filename"]
    if plugin_wheel is None:
        _download_file(plugin["url"], plugin_output)
    else:
        _require(plugin_wheel.is_file(), "plugin wheel does not exist")
        shutil.copyfile(plugin_wheel, plugin_output)
    _require(sha256_file(plugin_output) == plugin["sha256"], "GGUF plugin wheel SHA-256 drift")
    files = []
    for path in sorted(item for item in output_dir.iterdir() if item.is_file()):
        files.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "schema_version": "ua_open_weight_eval_hf_jobs_bundle.v1",
        "issue": 6273,
        "files": files,
        "requests_sha256": sha256_file(requests),
        "selection_sha256": selection["selection_sha256"],
        "source_commit": source_commit(),
        "config_sha256": sha256_file(output_dir / "run_config.json"),
        "transport_sha256": sha256_file(output_dir / "hf_jobs_transport.py"),
        "worker_sha256": sha256_file(output_dir / "hf_jobs_worker.py"),
    }
    manifest["bundle_sha256"] = sha256_text(canonical_json(manifest))
    write_atomic(output_dir / "BUNDLE_MANIFEST.json", manifest)
    verify_bundle(output_dir)
    return manifest


def verify_bundle(bundle: Path) -> dict[str, Any]:
    config = load_config(bundle / "run_config.json")
    manifest = read_json(bundle / "BUNDLE_MANIFEST.json")
    _require(manifest.get("schema_version") == "ua_open_weight_eval_hf_jobs_bundle.v1", "bundle schema drift")
    _require(re.fullmatch(r"[a-f0-9]{40}", str(manifest.get("source_commit", ""))) is not None, "bundle source commit drift")
    expected = {
        "BUNDLE_MANIFEST.json",
        "canary_selection.json",
        "hf_jobs_transport.py",
        "hf_jobs_worker.py",
        "requests.jsonl",
        "run_config.json",
        config["runtime"]["vllm_gguf_plugin"]["filename"],
    }
    observed = {item.name for item in bundle.iterdir() if item.is_file()}
    _require(observed == expected, "bundle contains missing or extra files")
    records = manifest.get("files")
    _require(isinstance(records, list), "bundle manifest files are missing")
    for record in records:
        path = bundle / record["path"]
        _require(path.is_file(), f"bundle file is missing: {record['path']}")
        _require(path.stat().st_size == record["bytes"], f"bundle byte drift: {record['path']}")
        _require(sha256_file(path) == record["sha256"], f"bundle hash drift: {record['path']}")
    unsigned = {key: value for key, value in manifest.items() if key != "bundle_sha256"}
    _require(manifest.get("bundle_sha256") == sha256_text(canonical_json(unsigned)), "bundle digest drift")
    request_header, requests = hf_jobs_worker.load_requests(bundle / "requests.jsonl")
    _require(len(requests) == 4000 and request_header["gold_fields_supplied"] == [], "request packet drift")
    selection = read_json(bundle / "canary_selection.json")
    _require(selection.get("case_count") == 100 and len(selection.get("item_ids", [])) == 100, "selection drift")
    return manifest


def verify_staged_transport(*, bundle: Path, repo_id: str, revision: str) -> dict[str, Any]:
    from huggingface_hub import HfApi, hf_hub_download

    manifest = verify_bundle(bundle)
    _require(re.fullmatch(r"[a-f0-9]{40}", revision) is not None, "transport revision must be immutable")
    prefix = f"bundles/{manifest['bundle_sha256']}"
    api = HfApi(token=os.environ.get("HF_TOKEN"))
    info = api.repo_info(repo_id=repo_id, repo_type="dataset", revision=revision)
    _require(bool(getattr(info, "private", False)), "transport dataset must remain private")
    expected = {path.name for path in bundle.iterdir() if path.is_file()}
    observed = {
        item.path.removeprefix(f"{prefix}/")
        for item in api.list_repo_tree(repo_id=repo_id, repo_type="dataset", path_in_repo=prefix, revision=revision)
        if getattr(item, "path", "").startswith(f"{prefix}/")
    }
    _require(observed == expected, "staged transport contains missing or extra files")
    verified: list[dict[str, Any]] = []
    for name in sorted(expected):
        remote = Path(
            hf_hub_download(
                repo_id=repo_id,
                repo_type="dataset",
                revision=revision,
                filename=f"{prefix}/{name}",
                token=True,
            )
        )
        local = bundle / name
        _require(remote.stat().st_size == local.stat().st_size, f"staged byte drift: {name}")
        digest = sha256_file(remote)
        _require(digest == sha256_file(local), f"staged hash drift: {name}")
        verified.append({"path": name, "bytes": remote.stat().st_size, "sha256": digest})
    return {
        "schema_version": "ua_open_weight_eval_hf_jobs_transport_stage.v1",
        "status": "verified",
        "repository": repo_id,
        "revision": revision,
        "prefix": prefix,
        "bundle_sha256": manifest["bundle_sha256"],
        "files": verified,
        "private": True,
    }


def stage_transport_bundle(*, bundle: Path, repo_id: str) -> dict[str, Any]:
    from huggingface_hub import CommitOperationAdd, HfApi

    manifest = verify_bundle(bundle)
    _require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/ua-open-weight-eval-staging-6273", repo_id) is not None, "invalid staging repository")
    token = os.environ.get("HF_TOKEN")
    _require(bool(token), "HF_TOKEN is required to stage the private transport")
    api = HfApi(token=token)
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True)
    _require(bool(api.repo_info(repo_id=repo_id, repo_type="dataset").private), "staging repository is not private")
    prefix = f"bundles/{manifest['bundle_sha256']}"
    operations = [
        CommitOperationAdd(path_in_repo=f"{prefix}/{path.name}", path_or_fileobj=path)
        for path in sorted(bundle.iterdir())
        if path.is_file()
    ]
    commit = api.create_commit(
        repo_id=repo_id,
        repo_type="dataset",
        operations=operations,
        commit_message=f"stage reviewed no-volume bundle {manifest['bundle_sha256'][:12]}",
    )
    revision = getattr(commit, "oid", None)
    _require(isinstance(revision, str), "staging commit is missing")
    return verify_staged_transport(bundle=bundle, repo_id=repo_id, revision=revision)


def verify_preflight_receipt(
    *, bundle: Path, repo_id: str, revision: str, path_in_repo: str, job_id: str
) -> dict[str, Any]:
    from huggingface_hub import hf_hub_download

    manifest = verify_bundle(bundle)
    _require(JOB_ID_PATTERN.fullmatch(job_id) is not None, "invalid preflight job ID")
    _require(re.fullmatch(r"[a-f0-9]{40}", revision) is not None, "preflight receipt revision must be immutable")
    expected_path = f"artifacts/{manifest['bundle_sha256']}/preflight/{job_id}/transport_receipt.json"
    _require(path_in_repo == expected_path, "preflight receipt path drift")
    source = Path(
        hf_hub_download(
            repo_id=repo_id,
            repo_type="dataset",
            revision=revision,
            filename=path_in_repo,
            token=True,
        )
    )
    receipt = read_json(source)
    _require(
        receipt.get("schema_version") == "ua_open_weight_eval_hf_jobs_transport_receipt.v1"
        and receipt.get("status") == "passed"
        and receipt.get("mode") == "preflight",
        "preflight receipt status drift",
    )
    _require(receipt.get("job_id") == job_id and receipt.get("hardware_flavor") == "cpu-basic", "preflight identity drift")
    transport = receipt.get("transport")
    _require(isinstance(transport, Mapping), "preflight transport evidence is missing")
    _require(transport.get("repository") == repo_id, "preflight repository drift")
    _require(transport.get("bundle_sha256") == manifest["bundle_sha256"], "preflight bundle drift")
    transport_revision = transport.get("revision")
    _require(
        isinstance(transport_revision, str) and re.fullmatch(r"[a-f0-9]{40}", transport_revision) is not None,
        "preflight transport revision drift",
    )
    _require(transport.get("all_hashes_verified") is True, "preflight hash verification failed")
    _require(transport.get("mounted_volumes") == 0, "preflight used a prohibited volume")
    facts = receipt.get("facts")
    _require(isinstance(facts, Mapping), "preflight facts are missing")
    _require(facts.get("receipt_uploaded_directly") is True, "preflight direct upload was not proven")
    _require(facts.get("model_execution_started") is False, "preflight unexpectedly started model execution")
    return {
        "schema_version": "ua_open_weight_eval_hf_jobs_preflight_verification.v1",
        "status": "passed",
        "job_id": job_id,
        "repository": repo_id,
        "revision": revision,
        "path": path_in_repo,
        "receipt_sha256": sha256_file(source),
        "bundle_sha256": manifest["bundle_sha256"],
        "transport_revision": transport_revision,
    }


def gate_gpu_canary(
    *,
    verification: Mapping[str, Any],
    provider_receipt: Mapping[str, Any],
    bundle_manifest: Mapping[str, Any],
    repo_id: str,
) -> dict[str, Any]:
    _require(
        verification.get("schema_version") == "ua_open_weight_eval_hf_jobs_preflight_verification.v1"
        and verification.get("status") == "passed",
        "CPU preflight verification did not pass",
    )
    _require(verification.get("bundle_sha256") == bundle_manifest["bundle_sha256"], "CPU preflight bundle drift")
    _require(verification.get("repository") == repo_id, "CPU preflight repository drift")
    _require(
        provider_receipt.get("schema_version") == "ua_open_weight_eval_hf_jobs_provider_receipt.v1"
        and provider_receipt.get("mode") == "preflight"
        and provider_receipt.get("stage") == "COMPLETED",
        "CPU preflight provider receipt did not complete",
    )
    _require(provider_receipt.get("job_id") == verification.get("job_id"), "CPU preflight job ID drift")
    _require(provider_receipt.get("hardware_flavor") == "cpu-basic", "CPU preflight hardware drift")
    _require(float(provider_receipt.get("provider_derived_cost_usd", math.inf)) <= 0.001, "CPU preflight cost exceeded")
    labels = provider_receipt.get("labels")
    _require(isinstance(labels, Mapping), "CPU preflight provider labels are missing")
    transport_revision = verification.get("transport_revision")
    _require(
        isinstance(transport_revision, str) and re.fullmatch(r"[a-f0-9]{40}", transport_revision) is not None,
        "CPU preflight transport revision drift",
    )
    _require(labels.get("transport") == transport_revision[:16], "CPU preflight transport label drift")
    payload = {
        "schema_version": "ua_open_weight_eval_hf_jobs_canary_gate.v1",
        "status": "passed",
        "preflight_job_id": verification["job_id"],
        "bundle_sha256": bundle_manifest["bundle_sha256"],
        "transport_repository": repo_id,
        "transport_revision": transport_revision,
        "preflight_cost_usd": provider_receipt["provider_derived_cost_usd"],
    }
    payload["gate_sha256"] = sha256_text(canonical_json(payload))
    return payload


def operator_gate_gpu_canary(
    *, bundle_manifest: Mapping[str, Any], repo_id: str, transport_revision: str, config: Mapping[str, Any]
) -> dict[str, Any]:
    """Bind the operator's superseding CPU-transport acceptance to an exact GPU bundle."""
    _require(re.fullmatch(r"[a-f0-9]{40}", transport_revision) is not None, "transport revision must be immutable")
    _require(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/ua-open-weight-eval-staging-6273", repo_id) is not None,
        "invalid staging repository",
    )
    authorization = config["authorization"]
    validation = authorization["validated_cpu_transport"]
    _require(validation["accepted_by_operator"] is True, "operator did not accept CPU transport validation")
    _require(
        validation["container_reached_running"] is True
        and validation["complete_pinned_bundle_downloaded"] is True
        and validation["all_bundle_hashes_verified"] is True,
        "accepted CPU transport evidence is incomplete",
    )
    _require(
        re.fullmatch(r"[a-f0-9]{40}", validation["fixed_by_merge_commit"]) is not None,
        "accepted CPU transport fix commit drift",
    )
    _require(
        re.fullmatch(r"[a-f0-9]{40}", str(bundle_manifest.get("source_commit", ""))) is not None,
        "GPU bundle source commit drift",
    )
    payload = {
        "schema_version": "ua_open_weight_eval_hf_jobs_operator_canary_gate.v1",
        "status": "passed",
        "authorization_source": f"operator_supersession_{authorization['superseding_authorization_at']}",
        "accepted_preflight_job_id": validation["job_id"],
        "accepted_preflight_cost_usd": validation["provider_derived_cost_usd"],
        "prior_provider_cost_usd": authorization["prior_provider_cost_usd"],
        "incurred_provider_job_ids": [entry["job_id"] for entry in authorization["incurred_provider_costs"]],
        "validated_cpu_bundle_sha256": validation["validated_bundle_sha256"],
        "accepted_cpu_fix_merge_commit": validation["fixed_by_merge_commit"],
        "bundle_sha256": bundle_manifest["bundle_sha256"],
        "bundle_source_commit": bundle_manifest["source_commit"],
        "transport_repository": repo_id,
        "transport_revision": transport_revision,
        "bindings": {
            "cases_sha256": config["suite"]["cases_sha256"],
            "model_revision": config["model"]["revision"],
            "model_sha256": config["model"]["artifact_sha256"],
            "hardware_flavor": config["hardware"]["flavor"],
            "mounted_volumes": config["transport"]["mounted_volumes"],
        },
    }
    payload["gate_sha256"] = sha256_text(canonical_json(payload))
    return payload


def _bootstrap_source() -> str:
    return """import argparse,hashlib,json,os,sys
from pathlib import Path
from huggingface_hub import hf_hub_download
p=argparse.ArgumentParser()
p.add_argument('--mode',required=True)
p.add_argument('--transport-repo',required=True)
p.add_argument('--transport-revision',required=True)
p.add_argument('--transport-prefix',required=True)
p.add_argument('--artifact-prefix',required=True)
p.add_argument('--bundle-sha256',required=True)
p.add_argument('--requests-sha256')
p.add_argument('--work-root',required=True)
a,_=p.parse_known_args()
mp=Path(hf_hub_download(repo_id=a.transport_repo,repo_type='dataset',revision=a.transport_revision,filename=f'{a.transport_prefix}/BUNDLE_MANIFEST.json',token=True))
m=json.loads(mp.read_text(encoding='utf-8'))
u={k:v for k,v in m.items() if k!='bundle_sha256'}
assert m.get('schema_version')=='ua_open_weight_eval_hf_jobs_bundle.v1'
assert m.get('bundle_sha256')==a.bundle_sha256==hashlib.sha256(json.dumps(u,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
r=next(x for x in m['files'] if x['path']=='hf_jobs_transport.py')
tp=Path(hf_hub_download(repo_id=a.transport_repo,repo_type='dataset',revision=a.transport_revision,filename=f'{a.transport_prefix}/hf_jobs_transport.py',token=True))
assert tp.stat().st_size==r['bytes'] and hashlib.sha256(tp.read_bytes()).hexdigest()==r['sha256']
os.execvp('python3',['python3',str(tp),*sys.argv[1:]])
"""


def _verify_launch_inputs(
    *, namespace: str, transport_repo: str, transport_revision: str, transport_prefix: str, manifest: Mapping[str, Any]
) -> None:
    _require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", namespace) is not None, "invalid namespace")
    _require(transport_repo == f"{namespace}/ua-open-weight-eval-staging-6273", "unexpected staging dataset repository")
    _require(re.fullmatch(r"[a-f0-9]{40}", transport_revision) is not None, "transport revision must be immutable")
    _require(
        transport_prefix == f"bundles/{manifest['bundle_sha256']}",
        "transport prefix is not bound to the bundle digest",
    )


def job_command(
    *,
    mode: str,
    namespace: str,
    bundle: Path,
    transport_repo: str,
    transport_revision: str,
    transport_prefix: str,
    hf_cli: Path,
    timeout_seconds: int,
    projection: Mapping[str, Any] | None = None,
    preflight_gate: Mapping[str, Any] | None = None,
) -> list[str]:
    _require(mode in LAUNCH_MODES, "invalid launch mode")
    _require(hf_cli.is_absolute() and hf_cli.is_file() and os.access(hf_cli, os.X_OK), "HF CLI must be executable")
    manifest = verify_bundle(bundle)
    config = load_config(bundle / "run_config.json")
    _verify_launch_inputs(
        namespace=namespace,
        transport_repo=transport_repo,
        transport_revision=transport_revision,
        transport_prefix=transport_prefix,
        manifest=manifest,
    )
    observed_cli = subprocess.run([str(hf_cli), "--version"], check=False, capture_output=True, text=True)
    _require(observed_cli.returncode == 0, "HF CLI version probe failed")
    _require(
        observed_cli.stdout.strip() == config["runtime"]["huggingface_hub_cli_version"],
        "HF CLI version drift",
    )
    if mode == "preflight":
        preflight = config["transport"]["cpu_preflight"]
        _require(projection is None, "preflight must not accept a projection")
        _require(preflight_gate is None, "preflight must not accept a canary gate")
        _require(timeout_seconds == preflight["timeout_seconds"] == 300, "preflight timeout drift")
        flavor = "cpu-basic"
        image = f"{preflight['container_image']}@{preflight['container_amd64_digest']}"
        installer = "python -m pip install --disable-pip-version-check --no-cache-dir"
        artifact_prefix = f"artifacts/{manifest['bundle_sha256']}/preflight"
    else:
        flavor = "l40sx1"
        image = f"{config['runtime']['container_image']}@{config['runtime']['container_amd64_digest']}"
        installer = "uv pip install --system"
        artifact_prefix = f"artifacts/{manifest['bundle_sha256']}/{mode}"
        if mode == "canary":
            _require(projection is None, "canary launch must not accept a full-run projection")
            _require(timeout_seconds == config["canary"]["timeout_seconds"], "canary timeout drift")
            _require(isinstance(preflight_gate, Mapping), "canary launch requires a passed CPU preflight gate")
            gate_schema = preflight_gate.get("schema_version")
            _require(
                gate_schema
                in {
                    "ua_open_weight_eval_hf_jobs_canary_gate.v1",
                    "ua_open_weight_eval_hf_jobs_operator_canary_gate.v1",
                }
                and preflight_gate.get("status") == "passed",
                "canary launch requires a passed CPU transport gate",
            )
            _require(preflight_gate.get("bundle_sha256") == manifest["bundle_sha256"], "canary gate bundle drift")
            _require(preflight_gate.get("transport_repository") == transport_repo, "canary gate repository drift")
            _require(preflight_gate.get("transport_revision") == transport_revision, "canary gate revision drift")
            if gate_schema == "ua_open_weight_eval_hf_jobs_operator_canary_gate.v1":
                expected_bindings = {
                    "cases_sha256": config["suite"]["cases_sha256"],
                    "model_revision": config["model"]["revision"],
                    "model_sha256": config["model"]["artifact_sha256"],
                    "hardware_flavor": config["hardware"]["flavor"],
                    "mounted_volumes": config["transport"]["mounted_volumes"],
                }
                _require(preflight_gate.get("bindings") == expected_bindings, "operator canary gate binding drift")
                validation = config["authorization"]["validated_cpu_transport"]
                _require(
                    preflight_gate.get("accepted_preflight_job_id") == validation["job_id"]
                    and float(preflight_gate.get("accepted_preflight_cost_usd", math.inf))
                    == float(validation["provider_derived_cost_usd"])
                    and preflight_gate.get("validated_cpu_bundle_sha256") == validation["validated_bundle_sha256"],
                    "operator canary gate CPU evidence drift",
                )
                _require(
                    float(preflight_gate.get("prior_provider_cost_usd", math.inf))
                    == float(config["authorization"]["prior_provider_cost_usd"])
                    and preflight_gate.get("incurred_provider_job_ids")
                    == [entry["job_id"] for entry in config["authorization"]["incurred_provider_costs"]],
                    "operator canary gate cumulative cost evidence drift",
                )
                _require(
                    preflight_gate.get("accepted_cpu_fix_merge_commit") == validation["fixed_by_merge_commit"]
                    and preflight_gate.get("bundle_source_commit") == manifest["source_commit"],
                    "operator canary gate source provenance drift",
                )
            gate_sha256 = preflight_gate.get("gate_sha256")
            unsigned_gate = {key: value for key, value in preflight_gate.items() if key != "gate_sha256"}
            _require(
                isinstance(gate_sha256, str)
                and re.fullmatch(r"[a-f0-9]{64}", gate_sha256) is not None
                and gate_sha256 == sha256_text(canonical_json(unsigned_gate)),
                "canary gate SHA-256 drift",
            )
        else:
            _require(preflight_gate is None, "full launch does not accept a CPU preflight gate")
            _require(isinstance(projection, Mapping), "full launch requires the passed canary projection")
            _require(
                projection.get("schema_version") == "ua_open_weight_eval_hf_jobs_projection.v1"
                and projection.get("status") == "passed",
                "full launch requires a passed projection",
            )
            expected_bindings = {
                "cases_sha256": config["suite"]["cases_sha256"],
                "model_revision": config["model"]["revision"],
                "model_sha256": config["model"]["artifact_sha256"],
            }
            _require(projection.get("bindings") == expected_bindings, "full projection binding drift")
            authorization = projection.get("authorization")
            _require(isinstance(authorization, Mapping), "full projection authorization is missing")
            _require(
                float(authorization.get("maximum_total_cost_usd", -1))
                == config["authorization"]["maximum_provider_cost_usd"],
                "full projection cost ceiling drift",
            )
            _require(
                float(authorization.get("combined_projected_cost_usd", math.inf))
                <= config["authorization"]["maximum_provider_cost_usd"],
                "full projection exceeds the total cost ceiling",
            )
            maximum_timeout = int(authorization.get("maximum_full_timeout_seconds", 0))
            _require(0 < timeout_seconds <= maximum_timeout, "full timeout exceeds the remaining-budget projection")
    _require(timeout_seconds > 0 and timeout_seconds % 60 == 0, "timeout must be positive whole minutes")
    transport_args = [
        "--mode", mode,
        "--transport-repo", transport_repo,
        "--transport-revision", transport_revision,
        "--transport-prefix", transport_prefix,
        "--artifact-prefix", artifact_prefix,
        "--bundle-sha256", manifest["bundle_sha256"],
        "--work-root", "/tmp/ua-open-weight-eval",
    ]
    if mode in RUN_MODES:
        transport_args.extend(["--requests-sha256", manifest["requests_sha256"]])
    bootstrap = shlex.join(["python3", "-c", _bootstrap_source(), *transport_args])
    shell_command = f"{installer} huggingface_hub=={config['runtime']['huggingface_hub_cli_version']} && {bootstrap}"
    labels = {
        "bundle_sha256": manifest["bundle_sha256"],
        "issue": "6273",
        "mode": mode,
        "suite": config["suite"]["cases_sha256"][:16],
        "timeout_seconds": str(timeout_seconds),
        "transport": transport_revision[:16],
    }
    if projection is not None:
        labels["projection"] = sha256_text(canonical_json(projection))[:16]
    command = [
        str(hf_cli), "jobs", "run", "--detach",
        "--flavor", flavor,
        "--timeout", f"{timeout_seconds // 60}m",
        "--namespace", namespace,
        "--name", f"ua-open-weight-eval-gemma4-{mode}",
    ]
    for key, value in sorted(labels.items()):
        command.extend(["--label", f"{key}={value}"])
    command.extend(["--secrets", "HF_TOKEN", "--env", "HF_HUB_DISABLE_TELEMETRY=1"])
    if mode in RUN_MODES:
        command.extend(
            [
                "--env", "UA_EVAL_HARDWARE_FLAVOR=l40sx1",
                "--env", "VLLM_BATCH_INVARIANT=1",
                "--env", "VLLM_ENABLE_V1_MULTIPROCESSING=0",
            ]
        )
    command.extend(["--", image, "sh", "-lc", shell_command])
    _require("--volume" not in command and "-v" not in command, "volume transport is prohibited")
    _require("--expose" not in command and "--ssh" not in command, "endpoint exposure drift")
    _require(command.count("--secrets") == 1 and "HF_TOKEN=" not in " ".join(command), "secret transport drift")
    return command


def launch_once(
    *, command: Sequence[str], mode: str, state_path: Path, execute: bool
) -> dict[str, Any]:
    _require(mode in LAUNCH_MODES, "invalid launch mode")
    if state_path.exists():
        state = read_json(state_path)
    else:
        state = {"schema_version": "ua_open_weight_eval_hf_jobs_launch_state.v1", "runs": {}}
    runs = state.get("runs")
    _require(isinstance(runs, dict), "launch state drift")
    _require(mode not in runs, f"{mode} already has a launch attempt in this state; reconcile before retry")
    intent = {
        "status": "prepared",
        "command_sha256": sha256_text(canonical_json(list(command))),
        "prepared_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    if not execute:
        return {"status": "prepared", "mode": mode, "command": list(command), **intent}
    runs[mode] = intent
    write_atomic(state_path, state)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    intent["launch_returncode"] = completed.returncode
    if completed.returncode != 0:
        intent["status"] = "launch_response_failed_reconcile_required"
        write_atomic(state_path, state)
        raise BaselineError("HF Jobs launch returned an error; reconcile provider state before retry")
    output = completed.stdout.strip()
    direct_match = JOB_ID_PATTERN.fullmatch(output)
    labelled_match = re.search(r"(?:^|\s)id[=:]\s*([a-f0-9]{20,64})(?:\s|$)", output)
    job_id = direct_match.group(0) if direct_match is not None else None
    if job_id is None and labelled_match is not None:
        job_id = labelled_match.group(1)
    if job_id is None:
        intent["status"] = "launch_response_unparseable_reconcile_required"
        write_atomic(state_path, state)
        raise BaselineError("HF Jobs launch response has no parseable job ID; reconcile by labels before any retry")
    _require(isinstance(job_id, str) and JOB_ID_PATTERN.fullmatch(job_id) is not None, "launch response has no job ID")
    intent.update({"status": "launched", "job_id": job_id})
    write_atomic(state_path, state)
    return {"status": "launched", "mode": mode, "job_id": job_id, "command_sha256": intent["command_sha256"]}


def reconcile_provider_inspection(
    *,
    inspection: Mapping[str, Any],
    mode: str,
    config: Mapping[str, Any],
    bundle_manifest: Mapping[str, Any],
    transport_revision: str,
) -> dict[str, Any]:
    _require(mode in LAUNCH_MODES, "invalid reconciliation mode")
    _require(re.fullmatch(r"[a-f0-9]{40}", transport_revision) is not None, "invalid transport revision")
    job_id = inspection.get("id")
    _require(isinstance(job_id, str) and JOB_ID_PATTERN.fullmatch(job_id) is not None, "provider job ID drift")
    expected_flavor = "cpu-basic" if mode == "preflight" else "l40sx1"
    _require(inspection.get("flavor") == expected_flavor, "provider hardware drift")
    _require(inspection.get("volumes", []) == [], "provider attached a prohibited volume")
    _require(inspection.get("secrets") == ["HF_TOKEN"], "provider secret contract drift")
    labels = inspection.get("labels")
    _require(isinstance(labels, dict), "provider labels are missing")
    expected_labels = {
        "bundle_sha256": bundle_manifest["bundle_sha256"],
        "issue": "6273",
        "mode": mode,
        "suite": config["suite"]["cases_sha256"][:16],
        "transport": transport_revision[:16],
    }
    _require(all(labels.get(key) == value for key, value in expected_labels.items()), "provider labels drift")
    allowed_labels = set(expected_labels) | {"name", "timeout_seconds"}
    if mode == "full":
        allowed_labels.add("projection")
    _require(set(labels) == allowed_labels, "provider has unexpected labels")
    status = inspection.get("status")
    _require(isinstance(status, dict), "provider status is missing")
    stage = status.get("stage")
    _require(stage in {"COMPLETED", "CANCELED", "ERROR", "DELETED"}, "provider job is not terminal")
    _require(not status.get("expose_urls") and not status.get("ssh_url"), "provider exposed an endpoint")
    durations = inspection.get("durations")
    _require(isinstance(durations, dict), "provider durations are missing")
    running_seconds = durations.get("running_secs")
    _require(isinstance(running_seconds, int) and not isinstance(running_seconds, bool), "provider duration drift")
    timeout_seconds = int(labels.get("timeout_seconds", 0))
    _require(0 <= running_seconds <= timeout_seconds, "provider duration exceeds authorization")
    billed_minutes = math.ceil(running_seconds / 60) if running_seconds else 0
    if mode == "preflight":
        hourly_price = float(config["transport"]["cpu_preflight"]["usd_per_hour"])
        maximum_cost = float(config["transport"]["cpu_preflight"]["maximum_cost_usd"])
    elif mode == "canary":
        hourly_price = float(config["pricing"]["usd_per_hour"])
        maximum_cost = float(config["canary"]["maximum_cost_usd"])
    else:
        hourly_price = float(config["pricing"]["usd_per_hour"])
        maximum_cost = float(config["authorization"]["maximum_provider_cost_usd"])
    price_per_minute = hourly_price / 60
    cost = round(billed_minutes * price_per_minute, 6)
    _require(cost <= maximum_cost, "provider cost exceeds authorization")
    return {
        "schema_version": "ua_open_weight_eval_hf_jobs_provider_receipt.v1",
        "job_id": job_id,
        "mode": mode,
        "stage": stage,
        "hardware_flavor": expected_flavor,
        "ports_exposed": False,
        "ssh_enabled": False,
        "provider_running_seconds": running_seconds,
        "provider_billed_minutes": billed_minutes,
        "provider_derived_cost_usd": cost,
        "pricing_usd_per_minute": price_per_minute,
        "timeout_seconds": timeout_seconds,
        "labels": expected_labels | {"timeout_seconds": str(timeout_seconds)},
    }


def project_full_run(
    *, worker_receipt: Mapping[str, Any], provider_receipt: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    _require(worker_receipt.get("status") == "completed" and worker_receipt.get("mode") == "canary", "canary worker receipt drift")
    _require(provider_receipt.get("stage") == "COMPLETED" and provider_receipt.get("mode") == "canary", "canary provider receipt drift")
    cases = worker_receipt["suite"]["case_count"]
    _require(cases == config["canary"]["case_count"] == 100, "canary case count drift")
    timing = worker_receipt["timing"]
    throughput = worker_receipt["throughput"]
    generation_seconds = float(timing["generation_seconds"])
    tokens_per_second = float(throughput["generated_tokens_per_second"])
    mean_tokens = float(throughput["mean_generated_tokens_per_case"])
    mean_case_seconds = float(timing["mean_seconds_per_case"])
    _require(generation_seconds > 0 and tokens_per_second > 0 and mean_case_seconds > 0, "canary throughput drift")
    full_cases = int(config["suite"]["case_count"])
    token_projection = full_cases * mean_tokens / tokens_per_second
    case_projection = full_cases * mean_case_seconds
    generation_projection = max(token_projection, case_projection)
    provider_seconds = int(provider_receipt["provider_running_seconds"])
    worker_wall = float(timing["wall_seconds"])
    current_generation_seconds = float(timing.get("current_generation_seconds", generation_seconds))
    worker_non_generation = max(
        0.0,
        worker_wall - current_generation_seconds - float(timing["download_seconds"]),
    )
    provider_outside_worker = max(0.0, provider_seconds - worker_wall)
    fixed_seconds = float(timing["download_seconds"]) + worker_non_generation + provider_outside_worker
    safety_margin = 0.25
    buffered_full_seconds = math.ceil(fixed_seconds + generation_projection * (1 + safety_margin))
    price_per_minute = float(config["pricing"]["usd_per_minute"])
    projected_full_cost = math.ceil(buffered_full_seconds / 60) * price_per_minute
    canary_cost = float(provider_receipt["provider_derived_cost_usd"])
    maximum = float(config["authorization"]["maximum_provider_cost_usd"])
    prior_cost = float(config["authorization"]["prior_provider_cost_usd"])
    remaining = round(maximum - prior_cost - canary_cost, 6)
    maximum_full_minutes = math.floor(remaining / price_per_minute)
    maximum_full_timeout_seconds = maximum_full_minutes * 60
    passed = projected_full_cost <= remaining and buffered_full_seconds <= maximum_full_timeout_seconds
    return {
        "schema_version": "ua_open_weight_eval_hf_jobs_projection.v1",
        "status": "passed" if passed else "blocked",
        "bindings": {
            "cases_sha256": config["suite"]["cases_sha256"],
            "model_revision": config["model"]["revision"],
            "model_sha256": config["model"]["artifact_sha256"],
        },
        "canary": {
            "cases": cases,
            "provider_running_seconds": provider_seconds,
            "provider_derived_cost_usd": canary_cost,
            "download_seconds": timing["download_seconds"],
            "generation_seconds": generation_seconds,
            "generated_tokens": throughput["generated_tokens"],
            "generated_tokens_per_second": tokens_per_second,
            "mean_case_seconds": mean_case_seconds,
        },
        "projection": {
            "case_latency_seconds": case_projection,
            "token_throughput_seconds": token_projection,
            "fixed_seconds": fixed_seconds,
            "safety_margin_fraction": safety_margin,
            "buffered_full_seconds": buffered_full_seconds,
            "projected_full_cost_usd": round(projected_full_cost, 6),
        },
        "authorization": {
            "maximum_total_cost_usd": maximum,
            "prior_provider_cost_usd": prior_cost,
            "remaining_after_canary_usd": remaining,
            "maximum_full_timeout_seconds": maximum_full_timeout_seconds,
            "combined_projected_cost_usd": round(prior_cost + canary_cost + projected_full_cost, 6),
        },
    }


def _metrics_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for track, track_value in report["tracks"].items():
        for category, metrics in track_value["categories"].items():
            rows.append({"track": track, "category": category, **metrics})
    _require(len(rows) == 56, "metrics flattening must produce 56 rows")
    return rows


def _results_card(config: Mapping[str, Any], public_receipt: Mapping[str, Any]) -> str:
    metadata = {
        "language": ["uk"],
        "license": ["cc-by-4.0", "mit"],
        "pretty_name": "UA Open-Weight Eval — Gemma 4 QAT Q4_0 baseline results",
        "size_categories": ["n<10K"],
        "task_categories": ["text-generation"],
        "tags": ["evaluation", "benchmark-results", "ukrainian", "gemma-4", "qat-q4_0"],
        "configs": [
            {"config_name": "metrics", "default": True, "data_files": [{"split": "test", "path": "metrics.jsonl"}]},
            {"config_name": "responses", "data_files": [{"split": "test", "path": "responses.jsonl"}]},
        ],
    }
    header = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip()
    model = config["model"]
    cost = public_receipt["provider_job"]["provider_derived_cost_usd"]
    return f"""---
{header}
---

# UA Open-Weight Eval: Gemma 4 QAT Q4_0 baseline

This dataset contains the complete parsed responses and fourteen separate track
reports from one deterministic evaluation of `{model['repository']}` at immutable
revision `{model['revision']}`. The evaluated text artifact is
`{model['artifact_filename']}` (SHA-256 `{model['artifact_sha256']}`). No model
weights or adapters are included.

The result measures this exact official QAT Q4_0 artifact. It does not represent
every Gemma 4 format, quantization, deployment, or Ukrainian capability. The
4,000 wrapped cases are not 4,000 independent human linguistic judgments. No
single “Ukrainian quality” score is produced.

Provider-derived execution cost: USD {cost:.6f}. See
`run_receipt.public.json` for the immutable model, tokenizer, runner, hardware,
decoding, timing, throughput, and cost bindings.

## Reproduction (English)

1. Download the source suite from GitHub release `ua-open-weight-eval-v0.1.0`.
2. Verify `cases.jsonl` has SHA-256 `{config['suite']['cases_sha256']}`.
3. Run the reviewed HF Jobs worker with the model/runtime revisions in the public receipt.
4. Score `responses.jsonl` with `suite_cli.py score`; compare the resulting `report.json`.
5. Verify every file against `SHA256SUMS` and `RESULTS_MANIFEST.json`.

## Відтворення (українською)

1. Завантажте вихідний набір із GitHub-релізу `ua-open-weight-eval-v0.1.0`.
2. Перевірте SHA-256 файла `cases.jsonl`: `{config['suite']['cases_sha256']}`.
3. Запустіть перевірений HF Jobs runner із точними ревізіями моделі та середовища з квитанції.
4. Оцініть `responses.jsonl` командою `suite_cli.py score` і порівняйте `report.json`.
5. Перевірте всі файли за `SHA256SUMS` і `RESULTS_MANIFEST.json`.

## Rights and evidence boundary

The response and aggregate metadata are released under the applicable MIT and
CC BY 4.0 terms described in `THIRD_PARTY_NOTICES.md`. This results repository
does not relicense the frozen source suite. Evaluation cases and outputs are
evaluation-only and are not eligible for Foundry learning views.
"""


def package_results(
    *,
    responses: Path,
    worker_receipt_path: Path,
    provider_receipt_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    config = load_config()
    worker_receipt = read_json(worker_receipt_path)
    provider_receipt = read_json(provider_receipt_path)
    _require(worker_receipt.get("status") == "completed" and worker_receipt.get("mode") == "full", "full worker receipt drift")
    _require(provider_receipt.get("stage") == "COMPLETED" and provider_receipt.get("mode") == "full", "full provider receipt drift")
    _require(worker_receipt["job"]["id"] == provider_receipt["job_id"], "job receipt ID drift")
    _require(worker_receipt["outputs"]["responses_sha256"] == sha256_file(responses), "response hash drift")
    rows = suite_cli.read_jsonl(responses)
    _require(len(rows) == 4001, "public responses require one header and 4,000 rows")
    _require(rows[0].get("model_revision") == config["model"]["revision"], "response model revision drift")
    _require(rows[0].get("model_sha256") == config["model"]["artifact_sha256"], "response model hash drift")
    _require(all(set(row) == {"item_id", "action", "output_text"} for row in rows[1:]), "response row field drift")
    _require(not output_dir.exists() or not any(output_dir.iterdir()), "results output directory is not empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(responses, output_dir / "responses.jsonl")
    report_path = output_dir / "report.json"
    report = suite_cli.score_saved(output_dir / "responses.jsonl", report_path)
    metrics_rows = _metrics_rows(report)
    write_atomic(output_dir / "metrics.jsonl", "".join(canonical_json(row) + "\n" for row in metrics_rows))
    public_receipt = {
        "schema_version": "ua_open_weight_eval_public_run_receipt.v1",
        "release": {
            "id": config["suite"]["release_id"],
            "tag": config["suite"]["release_tag"],
            "github_release_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/tag/ua-open-weight-eval-v0.1.0",
            "cases_sha256": config["suite"]["cases_sha256"],
            "requests_sha256": worker_receipt["suite"]["requests_sha256"],
        },
        "model": worker_receipt["model"],
        "tokenizer": worker_receipt["tokenizer"],
        "environment": worker_receipt["environment"]
        | {
            "launch_client": {
                "name": "huggingface_hub",
                "version": config["runtime"]["huggingface_hub_cli_version"],
            }
        },
        "decoding": worker_receipt["decoding"],
        "timing": worker_receipt["timing"],
        "throughput": worker_receipt["throughput"],
        "provider_job": provider_receipt,
        "outputs": {
            "response_count": 4000,
            "responses_sha256": sha256_file(output_dir / "responses.jsonl"),
            "report_sha256": sha256_file(report_path),
        },
        "scoring": report["scoring"],
        "tracks": list(report["tracks"]),
        "facts": worker_receipt["facts"] | {"complete_responses_published": True},
    }
    write_atomic(output_dir / "run_receipt.public.json", public_receipt)
    shutil.copyfile(LICENSE_PATH, output_dir / "LICENSE-MIT.txt")
    shutil.copyfile(THIRD_PARTY_PATH, output_dir / "THIRD_PARTY_NOTICES.md")
    write_atomic(output_dir / "README.md", _results_card(config, public_receipt))
    roles = {
        "LICENSE-MIT.txt": "project license",
        "README.md": "dataset card and bilingual reproduction guide",
        "THIRD_PARTY_NOTICES.md": "source-suite attribution and rights boundary",
        "metrics.jsonl": "fourteen-track by-category aggregate metrics",
        "report.json": "deterministic scorer report",
        "responses.jsonl": "complete parsed model responses",
        "run_receipt.public.json": "sanitized deterministic run and provider receipt",
    }
    files = []
    for name, role in sorted(roles.items()):
        path = output_dir / name
        files.append({"path": name, "role": role, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "schema_version": "ua_open_weight_eval_results_manifest.v1",
        "files": files,
        "source_suite": {
            "release_id": config["suite"]["release_id"],
            "cases_sha256": config["suite"]["cases_sha256"],
            "included": False,
        },
        "case_rights": [
            {"case_prefix": "uaw-011-", "cases": 2000, "license": "CC-BY-4.0"},
            {"case_prefix": "uaw-silver-", "cases": 2000, "license": "MIT"},
        ],
        "exclusions": [
            "model weights and derivatives",
            "source cases and request packets",
            "raw generations and private checkpoints",
            "provider command logs and failed-attempt traces",
            "private corpus or VESUM bytes",
            "global Ukrainian-quality score",
        ],
    }
    write_atomic(output_dir / "RESULTS_MANIFEST.json", manifest)
    checksum_names = sorted(PUBLIC_FILES - {"SHA256SUMS"})
    checksum_text = "".join(f"{sha256_file(output_dir / name)}  {name}\n" for name in checksum_names)
    write_atomic(output_dir / "SHA256SUMS", checksum_text)
    return verify_results_package(output_dir)


def verify_results_package(root: Path) -> dict[str, Any]:
    observed = {item.name for item in root.iterdir() if item.is_file()}
    _require(observed == PUBLIC_FILES, "results package has missing or extra files")
    manifest = read_json(root / "RESULTS_MANIFEST.json")
    _require(manifest.get("schema_version") == "ua_open_weight_eval_results_manifest.v1", "results manifest drift")
    for record in manifest.get("files", []):
        path = root / record["path"]
        _require(path.is_file(), f"manifest file missing: {record['path']}")
        _require(path.stat().st_size == record["bytes"], f"manifest byte drift: {record['path']}")
        _require(sha256_file(path) == record["sha256"], f"manifest hash drift: {record['path']}")
    checksums = {}
    for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        checksums[name] = digest
    _require(set(checksums) == PUBLIC_FILES - {"SHA256SUMS"}, "checksum file list drift")
    _require(all(sha256_file(root / name) == digest for name, digest in checksums.items()), "checksum drift")
    report = read_json(root / "report.json")
    _require(report["cases_sha256"] == load_config()["suite"]["cases_sha256"], "report cases drift")
    _require(report["scoring"]["global_quality_score"] is None, "global score must remain null")
    _require(report["scoring"]["global_score_prohibited"] is True, "global score policy drift")
    _require(len(report["tracks"]) == 14, "track count drift")
    responses = suite_cli.read_jsonl(root / "responses.jsonl")
    _require(len(responses) == 4001, "response completeness drift")
    _require(all("raw_generation" not in row for row in responses), "raw generation leaked")
    card_text = (root / "README.md").read_text(encoding="utf-8")
    _, metadata_text, _ = card_text.split("---", 2)
    metadata = yaml.safe_load(metadata_text)
    _require(metadata["language"] == ["uk"], "dataset language metadata drift")
    _require({item["config_name"] for item in metadata["configs"]} == {"metrics", "responses"}, "dataset config drift")
    for path in root.iterdir():
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        _require("/Users/" not in text and "HF_TOKEN=" not in text, f"private path or token leaked in {path.name}")
    return {
        "schema_version": "ua_open_weight_eval_results_verification.v1",
        "status": "passed",
        "files": len(PUBLIC_FILES),
        "responses": 4000,
        "tracks": 14,
        "package_sha256": sha256_text(canonical_json(checksums)),
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare-bundle")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--plugin-wheel", type=Path)
    verify = commands.add_parser("verify-bundle")
    verify.add_argument("--bundle", type=Path, required=True)
    stage = commands.add_parser("stage-transport")
    stage.add_argument("--bundle", type=Path, required=True)
    stage.add_argument("--repo", required=True)
    verify_transport = commands.add_parser("verify-transport")
    verify_transport.add_argument("--bundle", type=Path, required=True)
    verify_transport.add_argument("--repo", required=True)
    verify_transport.add_argument("--revision", required=True)
    verify_preflight = commands.add_parser("verify-preflight")
    verify_preflight.add_argument("--bundle", type=Path, required=True)
    verify_preflight.add_argument("--repo", required=True)
    verify_preflight.add_argument("--revision", required=True)
    verify_preflight.add_argument("--path", required=True)
    verify_preflight.add_argument("--job-id", required=True)
    gate_canary = commands.add_parser("gate-canary")
    gate_canary.add_argument("--verification", type=Path, required=True)
    gate_canary.add_argument("--provider-receipt", type=Path, required=True)
    gate_canary.add_argument("--bundle", type=Path, required=True)
    gate_canary.add_argument("--repo", required=True)
    gate_canary.add_argument("--output", type=Path, required=True)
    operator_gate = commands.add_parser("operator-gate-canary")
    operator_gate.add_argument("--bundle", type=Path, required=True)
    operator_gate.add_argument("--repo", required=True)
    operator_gate.add_argument("--transport-revision", required=True)
    operator_gate.add_argument("--output", type=Path, required=True)
    launch = commands.add_parser("launch")
    launch.add_argument("--mode", choices=sorted(LAUNCH_MODES), required=True)
    launch.add_argument("--namespace", required=True)
    launch.add_argument("--bundle", type=Path, required=True)
    launch.add_argument("--transport-repo", required=True)
    launch.add_argument("--transport-revision", required=True)
    launch.add_argument("--transport-prefix", required=True)
    launch.add_argument("--hf-cli", type=Path, required=True)
    launch.add_argument("--timeout-seconds", type=int, required=True)
    launch.add_argument("--projection", type=Path)
    launch.add_argument("--preflight-gate", type=Path)
    launch.add_argument("--state", type=Path, required=True)
    launch.add_argument("--execute", action="store_true")
    reconcile = commands.add_parser("reconcile-provider")
    reconcile.add_argument("--inspection", type=Path, required=True)
    reconcile.add_argument("--mode", choices=sorted(LAUNCH_MODES), required=True)
    reconcile.add_argument("--bundle", type=Path, required=True)
    reconcile.add_argument("--transport-revision", required=True)
    reconcile.add_argument("--output", type=Path, required=True)
    project = commands.add_parser("project-full")
    project.add_argument("--worker-receipt", type=Path, required=True)
    project.add_argument("--provider-receipt", type=Path, required=True)
    project.add_argument("--output", type=Path, required=True)
    package = commands.add_parser("package-results")
    package.add_argument("--responses", type=Path, required=True)
    package.add_argument("--worker-receipt", type=Path, required=True)
    package.add_argument("--provider-receipt", type=Path, required=True)
    package.add_argument("--output", type=Path, required=True)
    verify_results = commands.add_parser("verify-results")
    verify_results.add_argument("--root", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "prepare-bundle":
            result = prepare_bundle(args.output, plugin_wheel=args.plugin_wheel)
        elif args.command == "verify-bundle":
            result = verify_bundle(args.bundle)
        elif args.command == "stage-transport":
            result = stage_transport_bundle(bundle=args.bundle, repo_id=args.repo)
        elif args.command == "verify-transport":
            result = verify_staged_transport(bundle=args.bundle, repo_id=args.repo, revision=args.revision)
        elif args.command == "verify-preflight":
            result = verify_preflight_receipt(
                bundle=args.bundle,
                repo_id=args.repo,
                revision=args.revision,
                path_in_repo=args.path,
                job_id=args.job_id,
            )
        elif args.command == "gate-canary":
            result = gate_gpu_canary(
                verification=read_json(args.verification),
                provider_receipt=read_json(args.provider_receipt),
                bundle_manifest=verify_bundle(args.bundle),
                repo_id=args.repo,
            )
            write_atomic(args.output, result)
        elif args.command == "operator-gate-canary":
            result = operator_gate_gpu_canary(
                bundle_manifest=verify_bundle(args.bundle),
                repo_id=args.repo,
                transport_revision=args.transport_revision,
                config=load_config(),
            )
            write_atomic(args.output, result)
        elif args.command == "launch":
            command = job_command(
                mode=args.mode,
                namespace=args.namespace,
                bundle=args.bundle,
                transport_repo=args.transport_repo,
                transport_revision=args.transport_revision,
                transport_prefix=args.transport_prefix,
                hf_cli=args.hf_cli.resolve(),
                timeout_seconds=args.timeout_seconds,
                projection=read_json(args.projection) if args.projection is not None else None,
                preflight_gate=read_json(args.preflight_gate) if args.preflight_gate is not None else None,
            )
            result = launch_once(command=command, mode=args.mode, state_path=args.state, execute=args.execute)
        elif args.command == "reconcile-provider":
            result = reconcile_provider_inspection(
                inspection=read_json(args.inspection),
                mode=args.mode,
                config=load_config(),
                bundle_manifest=verify_bundle(args.bundle),
                transport_revision=args.transport_revision,
            )
            write_atomic(args.output, result)
        elif args.command == "project-full":
            result = project_full_run(
                worker_receipt=read_json(args.worker_receipt),
                provider_receipt=read_json(args.provider_receipt),
                config=load_config(),
            )
            write_atomic(args.output, result)
        elif args.command == "package-results":
            result = package_results(
                responses=args.responses,
                worker_receipt_path=args.worker_receipt,
                provider_receipt_path=args.provider_receipt,
                output_dir=args.output,
            )
        elif args.command == "verify-results":
            result = verify_results_package(args.root)
        else:
            raise BaselineError(f"unknown command: {args.command}")
    except (BaselineError, OSError, suite_cli.SuiteError, hf_jobs_worker.WorkerError) as exc:
        print(f"hf-jobs-baseline: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
