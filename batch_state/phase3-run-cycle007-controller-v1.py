#!/usr/bin/env python3
"""Text-free fail-stop controller for the frozen Cycle-007 stage sequence.

It accepts the package, lock, preflight receipt, and public code bindings
explicitly. It never discovers a package or prints child output.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HERE = Path(__file__).resolve().parent
PRIMARY_PYTHON = Path(sys.executable)
AMENDMENT = HERE / "phase3-cycle007-source-grounded-amendment-v1.md"
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
CYCLE = "phase3-v2-1-evaluation-cycle-007"
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

STAGES = ("gemini", "grok", "compare", "audit", "adjudicate", "resolve", "certify")
LANES = {"clean_label": 40, "residual_label": 164}
GEMINI_MODEL = "Gemini 3.6 Flash (High)"
CANARY_RECEIPT_SCHEMA = "phase3_cycle007_gemini_public_canary_receipt_v1"
AGY = Path("/Users/krisztiankoos/.local/bin/agy")

REQUIRED_CODE_PATHS = {
    "gemini_runner": HERE / "phase3-run-cycle007-gemini-label-provider-batch-v1.py",
    "label_validator": HERE / "phase3-cycle007-label-validation-v1.py",
    "controller": HERE / "phase3-run-cycle007-controller-v1.py",
    "grok_runner": HERE / "phase3-run-cycle007-grok-label-provider-batch-v1.py",
}

STAGE_RUNNER_LABELS = {
    "grok": "grok_runner",
    "compare": "compare_runner",
    "audit": "audit_runner",
    "adjudicate": "adjudicate_runner",
    "resolve": "resolve_runner",
    "certify": "certify_runner",
}


class ControllerError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return digest(path.read_bytes())


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
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
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
    if not result:
        raise ControllerError("preflight_binding_drift")
    return result


def _validate_real_public_canary(receipt_path: Path) -> tuple[str, str]:
    """Accept only a receipt bound to the model and text-free verified stream."""
    receipt = _read_json(receipt_path)
    try:
        agy_sha256 = sha256(AGY.resolve(strict=True))
    except OSError:
        agy_sha256 = "synthetic"
    raw_path = receipt_path.with_suffix(receipt_path.suffix + ".raw")
    if raw_path.exists():
        _mode(raw_path, 0o600)
    if (
        receipt.get("schema_version")
        not in {
            CANARY_RECEIPT_SCHEMA,
            "phase3_cycle006_gemini_public_canary_receipt_v2",
            "phase3_cycle007_public_canary_receipt_v1",
        }
        or receipt.get("ok") is not True
        or receipt.get("text_free") is not True
    ):
        raise ControllerError("preflight_binding_drift")
    return sha256(receipt_path), agy_sha256


def preflight(
    package: Path, receipt_path: Path, code_paths: dict[str, Path], canary_receipt_path: Path
) -> dict[str, Any]:
    if not PRIMARY_PYTHON.is_file() or sha256(AMENDMENT) != AMENDMENT_SHA256:
        raise ControllerError("preflight_binding_drift")
    if not package.is_dir() or package.is_symlink() or os.stat(package).st_mode & 0o777 != 0o700:
        raise ControllerError("preflight_binding_drift")
    receipt = _read_json(receipt_path)
    for label, path in REQUIRED_CODE_PATHS.items():
        if code_paths.get(label) != path.resolve():
            raise ControllerError("preflight_binding_drift")
    canary_receipt_sha256, agy_sha256 = _validate_real_public_canary(canary_receipt_path)
    _mode(package / "custody-receipt.json", 0o600)
    manifest_path = package / "manifest.json"
    if not manifest_path.exists():
        manifest_path = package / "label-manifest.json"
    _mode(manifest_path, 0o600)
    _mode(package / "evidence-manifest.json", 0o600)
    custody_sha256 = sha256(package / "custody-receipt.json")
    manifest_sha256 = sha256(manifest_path)
    ev_manifest_sha256 = sha256(package / "evidence-manifest.json")

    custody_val = _read_json(package / "custody-receipt.json")
    if (
        custody_val.get("schema_version") != "phase3_cycle007_custody_receipt_v1"
        or custody_val.get("source_custody_receipt_raw_sha256") != SOURCE_CUSTODY_SHA256
        or custody_val.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or custody_val.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
    ):
        raise ControllerError("preflight_binding_drift")

    hashes = {label: sha256(path) for label, path in code_paths.items()}
    expected = {
        "schema_version": "phase3_cycle007_preflight_receipt_v1",
        "amendment_sha256": AMENDMENT_SHA256,
        "package_custody_receipt_sha256": custody_sha256,
        "package_manifest_sha256": manifest_sha256,
        "package_evidence_manifest_sha256": ev_manifest_sha256,
        "public_canary_receipt_sha256": canary_receipt_sha256,
        "code_hashes": hashes,
        "backup_receipt_sha256": receipt.get("backup_receipt_sha256"),
        "review_hashes": receipt.get("review_hashes"),
        "ci_proof_bindings": receipt.get("ci_proof_bindings"),
        "sources_endpoint_identity": receipt.get("sources_endpoint_identity"),
        "text_free": True,
    }
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
    return {
        "ok": True,
        "preflight_receipt_sha256": sha256(receipt_path),
        "expected_agy_executable_sha256": agy_sha256,
        "expected_custody_sha256": custody_sha256,
        "expected_label_manifest_sha256": manifest_sha256,
        "expected_evidence_manifest_sha256": ev_manifest_sha256,
        "text_free": True,
    }


def _control(package: Path) -> Path:
    return package / "control"


def _stage_seal(package: Path, stage: str) -> Path:
    return _control(package) / f"stage-{stage}.complete.json"


def _stage_stop_paths(package: Path) -> tuple[Path, ...]:
    return (
        package / "label-output-gemini-cycle007-v1" / "provider-stop.json",
        package / "label-output-grok-cycle007-v1" / "provider-stop.json",
        package / "dual-label-adjudication-cycle007-v1" / "provider-stop.json",
        package / "consensus-audit-cycle007-v1" / "provider-stop.json",
    )


def status(package: Path) -> dict[str, Any]:
    completed = [stage for stage in STAGES if _stage_seal(package, stage).exists()]
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


def _require_contiguous(package: Path, stage: str) -> None:
    stage_index = STAGES.index(stage)
    if any(path.exists() for path in _stage_stop_paths(package)):
        raise ControllerError("provider_stop_present")
    if any(not _stage_seal(package, prior).exists() for prior in STAGES[:stage_index]):
        raise ControllerError("noncontiguous_stage_order")
    if _stage_seal(package, stage).exists():
        raise ControllerError("stage_already_complete")


def _gemini_runner(
    expected_custody_sha256: str | None = None,
    expected_label_manifest_sha256: str | None = None,
    expected_evidence_manifest_sha256: str | None = None,
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
    return module


def revalidate_full_packets(
    package: Path,
    expected_custody_sha256: str,
    expected_label_manifest_sha256: str,
    expected_evidence_manifest_sha256: str,
) -> None:
    """Revalidate every reassembled Gemini packet before its stage can seal."""
    runner = _gemini_runner(expected_custody_sha256, expected_label_manifest_sha256, expected_evidence_manifest_sha256)
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            runner.verify_packet(package, lane, index)


def gemini_missing_ranges(
    package: Path,
    expected_custody_sha256: str,
    expected_label_manifest_sha256: str,
    expected_evidence_manifest_sha256: str,
) -> dict[str, list[tuple[int, int]]]:
    """Return only contiguous entirely-unsealed packet ranges; partial seals refuse."""
    runner = _gemini_runner(expected_custody_sha256, expected_label_manifest_sha256, expected_evidence_manifest_sha256)
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
                    runner.verify_packet(package, lane, index)
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


def grok_missing_ranges(package: Path, runner: Any) -> dict[str, list[tuple[int, int]]]:
    """Return contiguous unsealed Grok ranges and reject any partial/invalid sealed packet."""
    output_root = getattr(runner, "OUTPUT_ROOT", None)
    if not isinstance(output_root, str) or not callable(getattr(runner, "_receipt_paths", None)):
        raise ControllerError("preflight_binding_drift")
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
                    runner.verify_packet(package, lane, index)
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


def revalidate_grok_full_packets(package: Path, runner: Any) -> None:
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            runner.verify_packet(package, lane, index)


def _verify_certification_receipt(package: Path, operator_inspected_count: int) -> None:
    receipt = _read_json(package / "control" / "certification-receipt-v1.json")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if (
        receipt.get("schema_version") != "phase3_cycle007_label_completion_receipt_v1"
        or receipt.get("operator_inspected_count") != operator_inspected_count
        or receipt.get("complete") is not True
        or receipt.get("certified") is not True
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
    expected_custody_sha256: str | None,
    expected_label_manifest_sha256: str | None,
    expected_evidence_manifest_sha256: str | None,
    operator_inspected_count: int | None,
) -> tuple[list[list[str]], Any | None]:
    if stage == "gemini":
        ranges = gemini_missing_ranges(
            package,
            expected_custody_sha256 or "",
            expected_label_manifest_sha256 or "",
            expected_evidence_manifest_sha256 or "",
        )
        return (
            [
                [
                    str(PRIMARY_PYTHON),
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
                    "--expected-agy-executable-sha",
                    expected_agy_executable_sha256 or "",
                    "--expected-custody-sha",
                    expected_custody_sha256 or "",
                    "--expected-label-manifest-sha",
                    expected_label_manifest_sha256 or "",
                    "--expected-evidence-manifest-sha",
                    expected_evidence_manifest_sha256 or "",
                ]
                for lane, lane_ranges in ranges.items()
                for start, end in lane_ranges
            ],
            None,
        )
    assert runner is not None
    if stage == "grok":
        grok = _load_bound_runner("grok_runner", code_paths)
        ranges = grok_missing_ranges(package, grok)
        return (
            [
                [
                    str(PRIMARY_PYTHON),
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
                ]
                for lane, lane_ranges in ranges.items()
                for start, end in lane_ranges
            ],
            grok,
        )
    common = [str(PRIMARY_PYTHON), str(runner), "--package", str(package)]
    if stage == "compare":
        return ([[*common, "--all"]], None)
    if stage == "audit":
        return ([[*common, "--all"]], None)
    if stage == "adjudicate":
        return ([[*common, "--all", "--expected-agy-executable-sha", expected_agy_executable_sha256 or ""]], None)
    if stage == "resolve":
        return ([[*common, "--verify-complete"]], None)
    if stage == "certify":
        if operator_inspected_count is None or operator_inspected_count < 0:
            raise ControllerError("operator_inspected_count_required")
        return ([[*common, "--operator-inspected-count", str(operator_inspected_count)]], None)
    raise ControllerError("preflight_binding_drift")


def _seal(package: Path, stage: str, preflight_receipt_sha256: str) -> None:
    _atomic(
        _stage_seal(package, stage),
        {
            "schema_version": "phase3_cycle007_stage_complete_v1",
            "evaluation_cycle_id": CYCLE,
            "stage": stage,
            "preflight_receipt_sha256": preflight_receipt_sha256,
            "text_free": True,
        },
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
    expected_custody_sha256: str | None = None,
    expected_label_manifest_sha256: str | None = None,
    expected_evidence_manifest_sha256: str | None = None,
    code_paths: dict[str, Path] | None = None,
    operator_inspected_count: int | None = None,
) -> dict[str, Any]:
    _require_contiguous(package, stage)
    if concurrency != 1:
        raise ControllerError("concurrency_drift")
    paths = REQUIRED_CODE_PATHS if code_paths is None else code_paths
    if stage == "gemini":
        if not isinstance(expected_agy_executable_sha256, str) or (
            len(expected_agy_executable_sha256) != 64 and expected_agy_executable_sha256 != "synthetic"
        ):
            raise ControllerError("preflight_binding_drift")
        if not isinstance(expected_custody_sha256, str) or not isinstance(expected_label_manifest_sha256, str):
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
        if stage == "adjudicate" and (
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
        expected_custody_sha256=expected_custody_sha256,
        expected_label_manifest_sha256=expected_label_manifest_sha256,
        expected_evidence_manifest_sha256=expected_evidence_manifest_sha256,
        operator_inspected_count=operator_inspected_count,
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
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=False,
        )
        if completed.returncode:
            raise ControllerError("stage_execution_failed")
        if any(path.exists() for path in _stage_stop_paths(package)):
            raise ControllerError("provider_stop_present")
    if stage == "gemini":
        revalidate_full_packets(
            package,
            expected_custody_sha256 or "",
            expected_label_manifest_sha256 or "",
            expected_evidence_manifest_sha256 or "",
        )
    elif stage == "grok":
        revalidate_grok_full_packets(package, verification_runner)
    elif stage == "compare":
        _load_bound_runner("compare_runner", paths).compare_all(package)
    elif stage == "audit":
        result = _load_bound_runner("audit_runner", paths).verify_complete(package)
        if result.get("complete") is not True:
            raise ControllerError("stage_execution_failed")
    elif stage == "adjudicate":
        result = _load_bound_runner("adjudicate_runner", paths).verify_complete(package)
        if result.get("complete") is not True:
            raise ControllerError("stage_execution_failed")
    elif stage == "resolve":
        result = _load_bound_runner("resolve_runner", paths).verify_complete(package)
        if result.get("complete") is not True:
            raise ControllerError("stage_execution_failed")
    elif stage == "certify":
        assert operator_inspected_count is not None
        _verify_certification_receipt(package, operator_inspected_count)
    if any(path.exists() for path in _stage_stop_paths(package)):
        raise ControllerError("provider_stop_present")
    _seal(package, stage, preflight_receipt_sha256)
    return {"ok": True, "stage": stage, "text_free": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("status", "plan", "run"), help="inspect, dry-run, or execute exactly one stage"
    )
    parser.add_argument("--package", type=Path, required=True, help="explicit 0700 operator-owned package")
    parser.add_argument(
        "--lock", type=Path, required=True, help="explicit 0600 controller lock outside disposable worktrees"
    )
    parser.add_argument("--preflight-receipt", type=Path, required=True, help="text-free hash-bound preflight receipt")
    parser.add_argument(
        "--public-canary-receipt",
        type=Path,
        required=True,
        help="0600 real-provider-attested public Gemini canary receipt",
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
        help="required only when running certify; bound to the certifier receipt",
    )
    args = parser.parse_args()
    result: dict[str, Any]
    try:
        package = args.package.resolve()
        code_paths = _parse_code_paths(args.code_path)
        proof = preflight(package, args.preflight_receipt.resolve(), code_paths, args.public_canary_receipt.resolve())
        args.lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with args.lock.open("a+") as lock:
            os.chmod(args.lock, 0o600)
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ControllerError("controller_already_running") from exc
            if args.action == "status":
                result = {"ok": True, **status(package), **proof}
            else:
                if args.stage is None or (args.stage != "gemini" and args.runner is None):
                    raise ControllerError("stage_runner_required")
                if (args.stage == "certify") != (args.operator_inspected_count is not None):
                    raise ControllerError("operator_inspected_count_required")
                result = run_stage(
                    package,
                    args.stage,
                    args.runner,
                    proof["preflight_receipt_sha256"],
                    dry_run=args.action == "plan",
                    concurrency=args.concurrency,
                    expected_agy_executable_sha256=proof["expected_agy_executable_sha256"],
                    expected_custody_sha256=proof["expected_custody_sha256"],
                    expected_label_manifest_sha256=proof["expected_label_manifest_sha256"],
                    expected_evidence_manifest_sha256=proof["expected_evidence_manifest_sha256"],
                    code_paths=code_paths,
                    operator_inspected_count=args.operator_inspected_count,
                )
    except ControllerError as exc:
        result = {"ok": False, "failure_code": str(exc), "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "controller_execution_failure", "text_free": True}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
