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
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as element_tree
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    # Allow execution directly as `python scripts/ci/cursor_cloud_pytest_verify.py`
    repo_root = str(Path(__file__).resolve().parents[2])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

from scripts.ci.pytest_shards import SHARD_COUNT, verify_artifacts

REQUIRED_SHARD_COUNT = 4
_HEX_40_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_HEX_64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_ISO_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_REQUIRED_METADATA_FIELDS = ("git_head", "runner_sha256", "nonce", "build_id", "started_at")


def _nodeids_digest(nodeids: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sorted(nodeids)).encode("utf-8")).hexdigest()


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
    *,
    expected_nodeids: Sequence[str] | None = None,
    expected_collected_count: int | None = None,
    expected_collected_digest: str | None = None,
) -> VerificationResult:
    """Verify a Cursor cloud agent artifact bundle against controller parameters.

    Checks:
    1. Fixed 4-shard plane: shard_count must equal 4 (rejects collapse).
    2. Nonce path and metadata: bundle directory name and metadata nonce must match
       expected session nonce (C8).
    3. git_head in metadata matches requested_sha (40-hex exact match).
    4. runner_sha256 in metadata matches expected_runner_blob_sha256 (64-hex).
    5. Completeness: all shard plans, nodeid lists, JUnit reports, logs, exit codes,
       and shard 1 playground JUnit are present and non-empty (R2, R4).
    6. Anchored completeness: if expected_nodeids, expected_collected_count, or
       expected_collected_digest are provided, plans and assigned nodeids must match
       the anchored expectation (preventing self-reported omission attacks).
    7. Partition integrity: verify_artifacts accepts partition with zero omissions/dups.
    8. Recorded provenance: build_id and started_at present and formatted properly (C7).
    9. Exit code and test results evaluation:
       - PASS if all checks pass and all shard exit_codes == 0 and 0 failures/errors.
       - FAIL if all integrity checks pass but any shard/playground failed.
       - UNKNOWN/INFRA on any integrity, hash, SHA, nonce, structure, or parse anomaly.
    """
    dir_path = Path(artifact_dir)
    clean_nonce = nonce.strip()
    clean_requested_sha = requested_sha.strip()
    clean_expected_runner_sha = expected_runner_blob_sha256.strip()

    if shard_count != REQUIRED_SHARD_COUNT:
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"shard_count must be {REQUIRED_SHARD_COUNT} (fixed four-shard plane), got: {shard_count}"],
        )

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

    # Nonce check on bundle directory path (renamed-dir mutation fails UNKNOWN/INFRA)
    if dir_path.name != clean_nonce:
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[
                f"nonce mismatch: artifact directory name {dir_path.name!r} does not match expected nonce {clean_nonce!r}"
            ],
        )

    # Mandatory completeness anchoring check (exact-head anchor must be present)
    clean_expected_digest = expected_collected_digest.strip() if expected_collected_digest else None
    if (
        expected_nodeids is None
        and expected_collected_count is None
        and not clean_expected_digest
    ):
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[
                "completeness anchor is mandatory: at least one of expected_nodeids, "
                "expected_collected_count, or expected_collected_digest must be supplied "
                "(trusted exact-head node-id digest/file is absent)"
            ],
        )

    # Anchoring setup
    target_count: int | None = None
    target_digest: str | None = None
    target_nodeids_set: set[str] | None = None

    if expected_nodeids is not None:
        clean_expected_nodeids = sorted({n.strip() for n in expected_nodeids if n.strip()})
        if not clean_expected_nodeids:
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=["expected_nodeids must contain at least one non-empty test node ID"],
            )
        target_count = len(clean_expected_nodeids)
        target_digest = _nodeids_digest(clean_expected_nodeids)
        target_nodeids_set = set(clean_expected_nodeids)

        if expected_collected_count is not None and expected_collected_count != target_count:
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[
                    f"expected_collected_count ({expected_collected_count}) does not match len(expected_nodeids) ({target_count})"
                ],
            )
        if (
            clean_expected_digest is not None
            and clean_expected_digest.lower() != target_digest.lower()
        ):
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[
                    f"expected_collected_digest ({clean_expected_digest}) does not match digest of expected_nodeids ({target_digest})"
                ],
            )
    else:
        target_count = expected_collected_count
        target_digest = clean_expected_digest

    # Metadata validation
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

    # Build ID check (§3.3: missing Build provenance is never PASS)
    meta_build_id = metadata["build_id"].strip()
    if not meta_build_id:
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=["metadata.json build_id must not be empty (missing Build provenance is never PASS)"],
            metadata=metadata,
        )

    # Nonce check in metadata
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

    # 4. Check shard directory completeness and plan invariants
    all_assigned_nodeids: list[str] = []
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

        # Check plan vs anchored completeness
        plan_collected_count = plan_data.get("collected_count")
        plan_collected_digest = plan_data.get("collected_digest")

        if target_count is not None and plan_collected_count != target_count:
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[
                    f"shard {shard_id} plan collected_count ({plan_collected_count}) does not match anchored count ({target_count})"
                ],
                metadata=metadata,
            )

        if target_digest is not None and (
            not isinstance(plan_collected_digest, str)
            or plan_collected_digest.lower() != target_digest.lower()
        ):
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[
                    f"shard {shard_id} plan collected_digest ({plan_collected_digest!r}) does not match anchored digest ({target_digest!r})"
                ],
                metadata=metadata,
            )

        all_assigned_nodeids.extend(nodeids)

    # 5. Shard partition verification (using trusted verify_artifacts)
    try:
        verify_artifacts(dir_path, shard_count=shard_count)
    except Exception as e:
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[f"shard partition verification failed: {e}"],
            metadata=metadata,
        )

    # 6. Check overall assigned node IDs vs anchored suite
    if target_nodeids_set is not None:
        assigned_set = set(all_assigned_nodeids)
        if assigned_set != target_nodeids_set:
            missing = sorted(target_nodeids_set - assigned_set)
            extra = sorted(assigned_set - target_nodeids_set)
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[
                    f"shard test assignment does not match anchored suite (missing={len(missing)}, extra={len(extra)})"
                ],
                metadata=metadata,
            )

    if target_count is not None and len(all_assigned_nodeids) != target_count:
        return VerificationResult(
            VerificationOutcome.UNKNOWN_INFRA,
            reasons=[
                f"total assigned test count across shards ({len(all_assigned_nodeids)}) does not match anchored count ({target_count})"
            ],
            metadata=metadata,
        )

    if target_digest is not None:
        actual_assigned_digest = _nodeids_digest(all_assigned_nodeids)
        if actual_assigned_digest.lower() != target_digest.lower():
            return VerificationResult(
                VerificationOutcome.UNKNOWN_INFRA,
                reasons=[
                    f"digest of all assigned shard test node IDs ({actual_assigned_digest}) does not match anchored digest ({target_digest})"
                ],
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
        help=f"Expected shard count (fixed: must be {REQUIRED_SHARD_COUNT}, default: {SHARD_COUNT})",
    )
    parser.add_argument(
        "--expected-nodeids-file",
        type=Path,
        default=None,
        help="Optional path to file with expected test node IDs (one per line) to anchor completeness",
    )
    parser.add_argument(
        "--expected-collected-count",
        type=int,
        default=None,
        help="Optional expected total collected test count to anchor completeness",
    )
    parser.add_argument(
        "--expected-collected-digest",
        type=str,
        default=None,
        help="Optional expected SHA-256 digest of sorted collected test node IDs to anchor completeness",
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

    expected_nodeids: list[str] | None = None
    if args.expected_nodeids_file is not None:
        if not args.expected_nodeids_file.is_file():
            print("UNKNOWN/INFRA")
            print(f"- expected-nodeids-file not found: {args.expected_nodeids_file}", file=sys.stderr)
            return 2
        expected_nodeids = [
            line.strip()
            for line in args.expected_nodeids_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    result = verify_cloud_artifacts(
        artifact_dir=args.artifact_dir,
        requested_sha=args.requested_sha,
        expected_runner_blob_sha256=args.expected_runner_sha,
        nonce=args.nonce,
        shard_count=args.shard_count,
        expected_nodeids=expected_nodeids,
        expected_collected_count=args.expected_collected_count,
        expected_collected_digest=args.expected_collected_digest,
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
