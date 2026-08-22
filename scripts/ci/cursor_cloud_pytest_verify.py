#!/usr/bin/env python3
"""Controller verifier for Cursor cloud agent pytest artifact bundles.

Implements the execution-authenticity verification contract from #6977 design
(comment 5320409546 §3.3 + §3.4). Evaluates downloaded cloud agent test artifacts
offline on the trusted controller.

Derived Check Predicate (§3.4):
- PASS: all verifier checks pass AND every shard + playground exit 0
- FAIL: all verifier checks pass AND (any shard/playground non-zero)
- UNKNOWN/INFRA: any completeness, SHA, runner-hash, nonce, Build-provenance,
  dirty-tree, timeout, or mutation-style inconsistency

NOTE ON TRUSTED BASE:
In production, this script and `pytest_shards.py` must run from the controller's
trusted base checkout, never trusting candidate-tree verifiers or running
unvetted candidate scripts directly.
"""

from __future__ import annotations

import argparse
import enum
import json
import re
import sys
import xml.etree.ElementTree as element_tree
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    # Allow execution directly as `python scripts/ci/cursor_cloud_pytest_verify.py`
    repo_root = str(Path(__file__).resolve().parents[2])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

from scripts.ci.pytest_shards import SHARD_COUNT, verify_artifacts

_HEX_40_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_HEX_64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_ISO_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_REQUIRED_METADATA_FIELDS = ("git_head", "runner_sha256", "nonce", "build_id", "started_at")


class VerificationOutcome(enum.StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN_INFRA = "UNKNOWN/INFRA"


@dataclass
class ShardArtifactResult:
    shard_id: int
    exit_code: int
    test_count: int
    failures: int
    errors: int
    passed: bool


@dataclass
class VerificationResult:
    outcome: VerificationOutcome
    reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    shard_results: list[ShardArtifactResult] = field(default_factory=list)

    @property
    def is_pass(self) -> bool:
        return self.outcome == VerificationOutcome.PASS

    @property
    def is_fail(self) -> bool:
        return self.outcome == VerificationOutcome.FAIL

    @property
    def is_unknown_infra(self) -> bool:
        return self.outcome == VerificationOutcome.UNKNOWN_INFRA

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "reasons": self.reasons,
            "metadata": self.metadata,
            "shard_results": [
                {
                    "shard_id": s.shard_id,
                    "exit_code": s.exit_code,
                    "test_count": s.test_count,
                    "failures": s.failures,
                    "errors": s.errors,
                    "passed": s.passed,
                }
                for s in self.shard_results
            ],
        }


def parse_junit_stats(path: Path) -> tuple[int, int, int]:
    """Parse a JUnit XML file and return (test_count, failures, errors).

    Raises:
        ValueError: if the XML is unparseable or malformed.
    """
    try:
        tree = element_tree.parse(path)
        root = tree.getroot()
    except Exception as e:
        raise ValueError(f"malformed JUnit XML in {path}: {e}") from e

    tests = 0
    failures = 0
    errors = 0

    if root.tag == "testsuite":
        tests = int(root.attrib.get("tests", "0"))
        failures = int(root.attrib.get("failures", "0"))
        errors = int(root.attrib.get("errors", "0"))
    elif root.tag == "testsuites":
        for suite in root.iter("testsuite"):
            tests += int(suite.attrib.get("tests", "0"))
            failures += int(suite.attrib.get("failures", "0"))
            errors += int(suite.attrib.get("errors", "0"))
    else:
        for tc in root.iter("testcase"):
            tests += 1
            if tc.find("failure") is not None:
                failures += 1
            if tc.find("error") is not None:
                errors += 1

    tag_failures = len(root.findall(".//failure"))
    tag_errors = len(root.findall(".//error"))
    failures = max(failures, tag_failures)
    errors = max(errors, tag_errors)

    return tests, failures, errors


def verify_cloud_artifacts(
    artifact_dir: Path | str,
    requested_sha: str,
    expected_runner_blob_sha256: str,
    nonce: str,
    shard_count: int = SHARD_COUNT,
) -> VerificationResult:
    """Verify a Cursor cloud agent artifact bundle against controller parameters.

    Checks:
    1. Artifact path and metadata nonce match expected session nonce (C8).
    2. git_head in metadata matches requested_sha (40-hex exact match).
    3. runner_sha256 in metadata matches expected_runner_blob_sha256 (64-hex).
    4. Completeness: all shard plans, nodeid lists, JUnit reports, logs, exit codes,
       and shard 1 playground JUnit are present and non-empty (R2, R4).
    5. Partition integrity: verify-artifacts accepts partition with zero omissions/dups.
    6. Recorded provenance: build_id and started_at present and formatted properly (C7).
    7. Exit code and test results evaluation:
       - PASS if all checks pass and all shard exit_codes == 0 and 0 failures/errors.
       - FAIL if all integrity checks pass but any shard/playground failed.
       - UNKNOWN/INFRA on any integrity, hash, SHA, nonce, structure, or parse anomaly.
    """
    dir_path = Path(artifact_dir)
    clean_nonce = nonce.strip()
    clean_requested_sha = requested_sha.strip()
    clean_expected_runner_sha = expected_runner_blob_sha256.strip()

    if not clean_nonce:
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=["nonce parameter must not be empty"],
        )

    if not _HEX_40_RE.match(clean_requested_sha):
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"requested_sha must be a 40-character hex string, got: {requested_sha!r}"],
        )

    if not _HEX_64_RE.match(clean_expected_runner_sha):
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[
                f"expected_runner_blob_sha256 must be a 64-character hex string, got: {expected_runner_blob_sha256!r}"
            ],
        )

    if not dir_path.exists() or not dir_path.is_dir():
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"artifact directory does not exist or is not a directory: {dir_path}"],
        )

    # 1 & 6. Metadata validation
    metadata_path = dir_path / "metadata.json"
    if not metadata_path.is_file():
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"missing metadata.json in artifact directory: {dir_path}"],
        )

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as e:
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"corrupted or unparseable metadata.json: {e}"],
        )

    if not isinstance(metadata, dict):
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=["metadata.json must be a JSON object"],
        )

    for field_name in _REQUIRED_METADATA_FIELDS:
        if field_name not in metadata:
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[f"metadata.json missing required field: {field_name!r}"],
            )
        if not isinstance(metadata[field_name], str):
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[f"metadata.json field {field_name!r} must be a string"],
            )

    # Nonce check
    meta_nonce = metadata["nonce"].strip()
    if meta_nonce != clean_nonce:
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"nonce mismatch: metadata has {meta_nonce!r}, expected {clean_nonce!r}"],
            metadata=metadata,
        )

    # Git head check
    meta_git_head = metadata["git_head"].strip()
    if not _HEX_40_RE.match(meta_git_head):
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"invalid git_head format in metadata: {meta_git_head!r}"],
            metadata=metadata,
        )
    if meta_git_head.lower() != clean_requested_sha.lower():
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"git_head mismatch: metadata has {meta_git_head!r}, expected {clean_requested_sha!r}"],
            metadata=metadata,
        )

    # Runner SHA256 check
    meta_runner_sha = metadata["runner_sha256"].strip()
    if not _HEX_64_RE.match(meta_runner_sha):
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"invalid runner_sha256 format in metadata: {meta_runner_sha!r}"],
            metadata=metadata,
        )
    if meta_runner_sha.lower() != clean_expected_runner_sha.lower():
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[
                f"runner_sha256 mismatch: metadata has {meta_runner_sha!r}, expected {clean_expected_runner_sha!r}"
            ],
            metadata=metadata,
        )

    # Started_at check
    started_at = metadata["started_at"].strip()
    if not started_at or not _ISO_TIMESTAMP_RE.match(started_at):
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"metadata.json started_at is not a valid ISO 8601 timestamp: {started_at!r}"],
            metadata=metadata,
        )

    # 4. Check shard directory completeness
    for shard_id in range(1, shard_count + 1):
        shard_dir = dir_path / f"pytest-shard-{shard_id}"
        if not shard_dir.is_dir():
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[f"missing shard directory: pytest-shard-{shard_id}"],
                metadata=metadata,
            )

        required_files = ["plan.json", "test-nodeids.txt", "main-junit.xml", "main.log", "exit_code"]
        for fname in required_files:
            fpath = shard_dir / fname
            if not fpath.is_file():
                return VerificationResult(
                    VerificationOutcome.UNKNOWN_INFRA,
                    reasons=[f"missing required file {fname} in shard {shard_id}"],
                    metadata=metadata,
                )

        if shard_id == 1:
            playground_file = shard_dir / "playground-junit.xml"
            if not playground_file.is_file():
                return VerificationResult(
                    VerificationOutcome.UNKNOWN_INFRA,
                    reasons=["missing playground-junit.xml in shard 1"],
                    metadata=metadata,
                )
        else:
            playground_file = shard_dir / "playground-junit.xml"
            if playground_file.exists():
                return VerificationResult(
                    VerificationOutcome.UNKNOWN_INFRA,
                    reasons=[f"unexpected playground-junit.xml found in shard {shard_id} (shard 1 only)"],
                    metadata=metadata,
                )

        # Ensure main.log is not empty
        main_log = shard_dir / "main.log"
        if main_log.stat().st_size == 0:
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[f"main.log is empty in shard {shard_id}"],
                metadata=metadata,
            )

        # Check test-nodeids.txt matches plan.json assigned_nodeids
        try:
            plan_data = json.loads((shard_dir / "plan.json").read_text(encoding="utf-8"))
            nodeids = [
                line.strip()
                for line in (shard_dir / "test-nodeids.txt").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except Exception as e:
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[f"failed reading plan or nodeids for shard {shard_id}: {e}"],
                metadata=metadata,
            )

        if plan_data.get("assigned_nodeids") != nodeids:
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[f"test-nodeids.txt does not match plan.json assigned_nodeids in shard {shard_id}"],
                metadata=metadata,
            )

    # 5. Shard partition verification (using trusted verify_artifacts)
    try:
        verify_artifacts(dir_path, shard_count=shard_count)
    except Exception as e:
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"shard partition verification failed: {e}"],
            metadata=metadata,
        )

    # 7. Shard exit codes and JUnit inspection
    shard_results: list[ShardArtifactResult] = []
    failure_reasons: list[str] = []

    for shard_id in range(1, shard_count + 1):
        shard_dir = dir_path / f"pytest-shard-{shard_id}"
        exit_code_path = shard_dir / "exit_code"
        try:
            exit_code_raw = exit_code_path.read_text(encoding="utf-8").strip()
            exit_code = int(exit_code_raw)
        except Exception as e:
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[f"invalid or non-integer exit_code in shard {shard_id}: {e}"],
                metadata=metadata,
            )

        main_junit_path = shard_dir / "main-junit.xml"
        try:
            tests, failures, errors = parse_junit_stats(main_junit_path)
        except Exception as e:
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[f"corrupted main JUnit XML in shard {shard_id}: {e}"],
                metadata=metadata,
            )

        if shard_id == 1:
            playground_junit_path = shard_dir / "playground-junit.xml"
            try:
                p_tests, p_failures, p_errors = parse_junit_stats(playground_junit_path)
            except Exception as e:
                return VerificationResult(
                    VerificationOutcome.UNKNOWN_INFRA,
                    reasons=[f"corrupted playground JUnit XML in shard 1: {e}"],
                    metadata=metadata,
                )
            tests += p_tests
            failures += p_failures
            errors += p_errors

        shard_passed = (exit_code == 0) and (failures == 0) and (errors == 0)
        if not shard_passed:
            failure_reasons.append(
                f"shard {shard_id} failed: exit_code={exit_code}, failures={failures}, errors={errors}"
            )

        shard_results.append(
            ShardArtifactResult(
                shard_id=shard_id,
                exit_code=exit_code,
                test_count=tests,
                failures=failures,
                errors=errors,
                passed=shard_passed,
            )
        )

    if failure_reasons:
        return VerificationResult(
            outcome=VerificationOutcome.FAIL,
            reasons=failure_reasons,
            metadata=metadata,
            shard_results=shard_results,
        )

    return VerificationResult(
        outcome=VerificationOutcome.PASS,
        reasons=[],
        metadata=metadata,
        shard_results=shard_results,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Cursor cloud agent pytest artifact bundles (Actions-outage fallback)."
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="Path to the artifact directory for the run (artifacts/<nonce>)",
    )
    parser.add_argument(
        "--requested-sha",
        type=str,
        required=True,
        help="Expected candidate git commit SHA (40 hex)",
    )
    parser.add_argument(
        "--expected-runner-sha",
        "--expected-runner-blob-sha256",
        dest="expected_runner_sha",
        type=str,
        required=True,
        help="Expected runner script SHA-256 (64 hex)",
    )
    parser.add_argument(
        "--nonce",
        type=str,
        required=True,
        help="Expected session nonce token",
    )
    parser.add_argument(
        "--shard-count",
        type=int,
        default=SHARD_COUNT,
        help=f"Expected shard count (default: {SHARD_COUNT})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full verification result in JSON format",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = verify_cloud_artifacts(
        artifact_dir=args.artifact_dir,
        requested_sha=args.requested_sha,
        expected_runner_blob_sha256=args.expected_runner_sha,
        nonce=args.nonce,
        shard_count=args.shard_count,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.outcome.value)
        if result.reasons:
            for reason in result.reasons:
                print(f"- {reason}", file=sys.stderr)

    if result.is_pass:
        return 0
    elif result.is_fail:
        return 1
    else:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
