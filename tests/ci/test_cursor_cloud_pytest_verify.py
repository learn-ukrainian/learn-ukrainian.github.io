"""Tests for Cursor cloud pytest verifier and runner contract (#6977).

Covers:
- Synthetic green bundle acceptance (PASS).
- Synthetic red bundle failure (FAIL).
- Shard 1 playground failure detection (FAIL).
- Four offline mutations of green bundle (all fail closed -> UNKNOWN/INFRA, never PASS):
  (a) runner hash mismatch/corruption
  (b) git_head / target SHA mismatch
  (c) exit_code file corruption/non-integer
  (d) shard artifact corruption (missing file, bad XML, count mismatch, digest tamper)
- Additional provenance, partition integrity, and edge case rejections (UNKNOWN/INFRA).
- Runner shell script contract assertions (clean-tree / argument / HEAD checks).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.ci.cursor_cloud_pytest_verify import (
    VerificationOutcome,
    verify_cloud_artifacts,
)
from scripts.ci.cursor_cloud_pytest_verify import (
    main as verifier_main,
)
from scripts.ci.pytest_shards import REQUIRED_MARKEXPR, SERIAL_TESTS

TEST_SHA = "0123456789abcdef0123456789abcdef01234567"
TEST_RUNNER_SHA = "a" * 64
TEST_NONCE = "test-session-nonce-42"
TEST_BUILD_ID = "build-pilot-001"
TEST_TIMESTAMP = "2026-08-22T15:00:00Z"


def _sha256_digest(items: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(items)).encode("utf-8")).hexdigest()


def create_synthetic_bundle(
    root: Path,
    *,
    sha: str = TEST_SHA,
    runner_sha: str = TEST_RUNNER_SHA,
    nonce: str = TEST_NONCE,
    build_id: str = TEST_BUILD_ID,
    started_at: str = TEST_TIMESTAMP,
    shard_count: int = 4,
    shard_exit_codes: dict[int, int] | None = None,
    shard_failures: dict[int, int] | None = None,
    playground_failures: int = 0,
    write_metadata: bool = True,
) -> Path:
    """Create a fully valid synthetic 4-shard test artifact bundle."""
    bundle_dir = root / nonce
    bundle_dir.mkdir(parents=True, exist_ok=True)

    if shard_exit_codes is None:
        shard_exit_codes = {i: 0 for i in range(1, shard_count + 1)}
    if shard_failures is None:
        shard_failures = {i: 0 for i in range(1, shard_count + 1)}

    # 2 tests per shard -> 8 tests total
    all_collected_nodeids: list[str] = []
    shard_nodeid_map: dict[int, list[str]] = {}
    for s in range(1, shard_count + 1):
        nodeids = [f"tests/test_module_{s}.py::test_case_a", f"tests/test_module_{s}.py::test_case_b"]
        shard_nodeid_map[s] = nodeids
        all_collected_nodeids.extend(nodeids)

    collected_digest = _sha256_digest(all_collected_nodeids)
    collected_count = len(all_collected_nodeids)

    for shard_id in range(1, shard_count + 1):
        s_dir = bundle_dir / f"pytest-shard-{shard_id}"
        s_dir.mkdir(parents=True, exist_ok=True)

        assigned = shard_nodeid_map[shard_id]
        assigned_digest = _sha256_digest(assigned)

        # 1. plan.json
        plan_data: dict[str, Any] = {
            "assigned_digest": assigned_digest,
            "assigned_nodeids": assigned,
            "collected_count": collected_count,
            "collected_digest": collected_digest,
            "estimated_seconds": 2.0,
            "grouping": "file",
            "markexpr": REQUIRED_MARKEXPR,
            "partition_mode": "lpt-durations",
            "serial_nodeids": list(SERIAL_TESTS) if shard_id == 1 else [],
            "shard_count": shard_count,
            "shard_id": shard_id,
        }
        (s_dir / "plan.json").write_text(json.dumps(plan_data, indent=2), encoding="utf-8")

        # 2. test-nodeids.txt
        (s_dir / "test-nodeids.txt").write_text("\n".join(assigned) + "\n", encoding="utf-8")

        # 3. main-junit.xml
        failures = shard_failures.get(shard_id, 0)
        failure_xml = ""
        if failures > 0:
            failure_xml = '<failure message="Assertion failed">AssertionError: expected True got False</failure>'

        junit_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="0" failures="{failures}" skipped="0" tests="{len(assigned)}" time="1.23">
  <testcase classname="tests.test_module_{shard_id}" name="test_case_a" time="0.50">{failure_xml if failures > 0 else ""}</testcase>
  <testcase classname="tests.test_module_{shard_id}" name="test_case_b" time="0.50"/>
</testsuite>
"""
        (s_dir / "main-junit.xml").write_text(junit_xml, encoding="utf-8")

        # 4. playground-junit.xml on shard 1
        if shard_id == 1:
            p_failure_xml = ""
            if playground_failures > 0:
                p_failure_xml = '<failure message="playground probe failed">Timeout</failure>'
            p_junit_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="0" failures="{playground_failures}" skipped="0" tests="1" time="0.30">
  <testcase classname="tests.test_playground_api_stability" name="test_playground_primary_endpoints_keep_health_fast" time="0.30">
    {p_failure_xml}
  </testcase>
</testsuite>
"""
            (s_dir / "playground-junit.xml").write_text(p_junit_xml, encoding="utf-8")

        # 5. main.log
        (s_dir / "main.log").write_text(
            f"Shard {shard_id} test run completed with exit code {shard_exit_codes.get(shard_id, 0)}\n",
            encoding="utf-8",
        )

        # 6. exit_code
        (s_dir / "exit_code").write_text(str(shard_exit_codes.get(shard_id, 0)) + "\n", encoding="utf-8")

    # 7. metadata.json
    if write_metadata:
        metadata_data = {
            "build_id": build_id,
            "git_head": sha,
            "nonce": nonce,
            "runner_sha256": runner_sha,
            "started_at": started_at,
        }
        (bundle_dir / "metadata.json").write_text(json.dumps(metadata_data, indent=2), encoding="utf-8")

    return bundle_dir


# =============================================================================
# 1. Happy Path: Green and Red Bundle Acceptance
# =============================================================================

def test_synthetic_green_bundle_passes(tmp_path: Path) -> None:
    """A complete and authentic green bundle returns PASS with zero failure reasons."""
    bundle = create_synthetic_bundle(tmp_path)
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )

    assert result.outcome == VerificationOutcome.PASS
    assert result.is_pass is True
    assert result.is_fail is False
    assert result.is_unknown_infra is False
    assert result.reasons == []
    assert len(result.shard_results) == 4
    assert all(sr.passed for sr in result.shard_results)
    assert result.metadata["git_head"] == TEST_SHA


def test_synthetic_green_bundle_cli_output_and_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI execution outputs PASS and exits 0 on a green bundle."""
    bundle = create_synthetic_bundle(tmp_path)

    exit_code = verifier_main([
        "--artifact-dir", str(bundle),
        "--requested-sha", TEST_SHA,
        "--expected-runner-sha", TEST_RUNNER_SHA,
        "--nonce", TEST_NONCE,
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "PASS"

    # Test --json flag
    exit_code_json = verifier_main([
        "--artifact-dir", str(bundle),
        "--requested-sha", TEST_SHA,
        "--expected-runner-sha", TEST_RUNNER_SHA,
        "--nonce", TEST_NONCE,
        "--json",
    ])
    assert exit_code_json == 0
    json_out = json.loads(capsys.readouterr().out)
    assert json_out["outcome"] == "PASS"
    assert json_out["reasons"] == []


def test_synthetic_red_bundle_shard_exit_code_fails(tmp_path: Path) -> None:
    """An authentic bundle with a non-zero shard exit code returns FAIL (red detection)."""
    bundle = create_synthetic_bundle(
        tmp_path,
        shard_exit_codes={1: 0, 2: 1, 3: 0, 4: 0},
        shard_failures={1: 0, 2: 1, 3: 0, 4: 0},
    )
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )

    assert result.outcome == VerificationOutcome.FAIL
    assert result.is_fail is True
    assert result.is_pass is False
    assert result.is_unknown_infra is False
    assert any("shard 2 failed" in reason for reason in result.reasons)


def test_synthetic_red_bundle_cli_exits_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI exits 1 on FAIL outcome."""
    bundle = create_synthetic_bundle(
        tmp_path,
        shard_exit_codes={1: 0, 2: 1, 3: 0, 4: 0},
        shard_failures={1: 0, 2: 1, 3: 0, 4: 0},
    )
    exit_code = verifier_main([
        "--artifact-dir", str(bundle),
        "--requested-sha", TEST_SHA,
        "--expected-runner-sha", TEST_RUNNER_SHA,
        "--nonce", TEST_NONCE,
    ])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out


def test_shard1_playground_probe_failure_fails(tmp_path: Path) -> None:
    """Shard 1 serial playground failure returns FAIL even if main tests had 0 failures."""
    bundle = create_synthetic_bundle(
        tmp_path,
        shard_exit_codes={1: 1, 2: 0, 3: 0, 4: 0},
        playground_failures=1,
    )
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )

    assert result.outcome == VerificationOutcome.FAIL
    assert result.is_fail is True
    assert any("shard 1 failed" in reason for reason in result.reasons)


# =============================================================================
# 2. Four Offline Mutations of a Green Bundle (Fail Closed -> UNKNOWN/INFRA)
# =============================================================================

def test_mutation_a_corrupted_runner_sha_rejected(tmp_path: Path) -> None:
    """Mutation (a): Runner blob hash corruption must be rejected as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path)

    # 1. Tamper runner_sha256 in metadata.json
    metadata_path = bundle / "metadata.json"
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    meta["runner_sha256"] = "f" * 64
    metadata_path.write_text(json.dumps(meta), encoding="utf-8")

    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert result.is_unknown_infra is True
    assert any("runner_sha256 mismatch" in r for r in result.reasons)

    # CLI exit code on UNKNOWN/INFRA is 2
    exit_code = verifier_main([
        "--artifact-dir", str(bundle),
        "--requested-sha", TEST_SHA,
        "--expected-runner-sha", TEST_RUNNER_SHA,
        "--nonce", TEST_NONCE,
    ])
    assert exit_code == 2


def test_mutation_b_target_sha_mismatch_rejected(tmp_path: Path) -> None:
    """Mutation (b): git_head / target SHA mismatch must be rejected as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path)

    # Controller requests a different SHA than recorded git_head
    different_sha = "9876543210fedcba9876543210fedcba98765432"
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=different_sha,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert result.is_unknown_infra is True
    assert any("git_head mismatch" in r for r in result.reasons)


def test_mutation_c_corrupted_exit_code_file_rejected(tmp_path: Path) -> None:
    """Mutation (c): Non-integer or corrupted exit_code file must be rejected as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path)

    # Corrupt exit_code in shard 3
    exit_code_file = bundle / "pytest-shard-3" / "exit_code"
    exit_code_file.write_text("CORRUPTED_NON_INT\n", encoding="utf-8")

    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert result.is_unknown_infra is True
    assert any("invalid or non-integer exit_code" in r for r in result.reasons)


def test_mutation_d_shard_artifact_corruptions_rejected(tmp_path: Path) -> None:
    """Mutation (d): Corruption of shard artifacts must be rejected as UNKNOWN/INFRA."""

    # Sub-case d1: Missing test-nodeids.txt
    b1 = create_synthetic_bundle(tmp_path / "d1")
    (b1 / "pytest-shard-2" / "test-nodeids.txt").unlink()
    r1 = verify_cloud_artifacts(b1, TEST_SHA, TEST_RUNNER_SHA, TEST_NONCE)
    assert r1.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("missing required file test-nodeids.txt" in r for r in r1.reasons)

    # Sub-case d2: Corrupted XML in main-junit.xml
    b2 = create_synthetic_bundle(tmp_path / "d2")
    (b2 / "pytest-shard-2" / "main-junit.xml").write_text("<invalid <xml >>>", encoding="utf-8")
    r2 = verify_cloud_artifacts(b2, TEST_SHA, TEST_RUNNER_SHA, TEST_NONCE)
    assert r2.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("shard partition verification failed" in r or "corrupted main JUnit XML" in r for r in r2.reasons)

    # Sub-case d3: JUnit count mismatch vs plan assigned_nodeids
    b3 = create_synthetic_bundle(tmp_path / "d3")
    bad_junit = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="0" failures="0" skipped="0" tests="99" time="1.0">
  <testcase classname="tests.test_module_2" name="test_case_a" time="0.50"/>
</testsuite>
"""
    (b3 / "pytest-shard-2" / "main-junit.xml").write_text(bad_junit, encoding="utf-8")
    r3 = verify_cloud_artifacts(b3, TEST_SHA, TEST_RUNNER_SHA, TEST_NONCE)
    assert r3.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("main JUnit count does not match plan" in r for r in r3.reasons)

    # Sub-case d4: Missing shard 1 playground-junit.xml
    b4 = create_synthetic_bundle(tmp_path / "d4")
    (b4 / "pytest-shard-1" / "playground-junit.xml").unlink()
    r4 = verify_cloud_artifacts(b4, TEST_SHA, TEST_RUNNER_SHA, TEST_NONCE)
    assert r4.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("missing playground-junit.xml" in r for r in r4.reasons)


# =============================================================================
# 3. Provenance and Partition Invariant Security Tests
# =============================================================================

def test_nonce_mismatch_rejected(tmp_path: Path) -> None:
    """Nonce mismatch between controller expectation and bundle metadata is rejected."""
    bundle = create_synthetic_bundle(tmp_path)
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce="different-nonce-token",
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("nonce mismatch" in r for r in result.reasons)


def test_missing_metadata_json_rejected(tmp_path: Path) -> None:
    """Missing metadata.json fails closed as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path, write_metadata=False)
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("missing metadata.json" in r for r in result.reasons)


def test_invalid_metadata_timestamp_rejected(tmp_path: Path) -> None:
    """Invalid or empty started_at timestamp in metadata fails closed."""
    bundle = create_synthetic_bundle(tmp_path, started_at="invalid-timestamp")
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("started_at is not a valid ISO 8601 timestamp" in r for r in result.reasons)


def test_missing_build_id_in_metadata_rejected(tmp_path: Path) -> None:
    """Missing build_id field in metadata fails closed."""
    bundle = create_synthetic_bundle(tmp_path)
    meta_path = bundle / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    del meta["build_id"]
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("missing required field: 'build_id'" in r for r in result.reasons)


def test_unexpected_playground_on_shard_two_rejected(tmp_path: Path) -> None:
    """Serial playground-junit.xml found on shard 2 fails closed."""
    bundle = create_synthetic_bundle(tmp_path)
    (bundle / "pytest-shard-2" / "playground-junit.xml").write_text("<testsuite tests='1'/>", encoding="utf-8")

    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("unexpected playground-junit.xml" in r for r in result.reasons)


def test_empty_main_log_rejected(tmp_path: Path) -> None:
    """Empty main.log file in a shard fails closed as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path)
    (bundle / "pytest-shard-1" / "main.log").write_text("", encoding="utf-8")

    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("main.log is empty" in r for r in result.reasons)


def test_duplicate_nodeid_between_shards_rejected(tmp_path: Path) -> None:
    """Duplicate node IDs across shards fail partition integrity."""
    bundle = create_synthetic_bundle(tmp_path)
    # Put test from shard 1 into shard 2 plan as well
    plan2_path = bundle / "pytest-shard-2" / "plan.json"
    plan2 = json.loads(plan2_path.read_text(encoding="utf-8"))
    dup_nodeid = "tests/test_module_1.py::test_case_a"
    plan2["assigned_nodeids"].append(dup_nodeid)
    plan2["assigned_digest"] = _sha256_digest(plan2["assigned_nodeids"])
    plan2_path.write_text(json.dumps(plan2), encoding="utf-8")
    (bundle / "pytest-shard-2" / "test-nodeids.txt").write_text(
        "\n".join(plan2["assigned_nodeids"]) + "\n",
        encoding="utf-8",
    )

    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("assigned to more than one shard" in r or "verification failed" in r for r in result.reasons)


# =============================================================================
# 4. Runner Shell Script Contract Tests
# =============================================================================

def test_runner_script_rejects_missing_sha() -> None:
    """Runner script exits non-zero if --sha is not provided."""
    proc = subprocess.run(
        ["bash", "scripts/ci/cursor_cloud_full_pytest.sh", "--nonce", "token123"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "--sha is required" in proc.stderr


def test_runner_script_rejects_invalid_sha() -> None:
    """Runner script exits non-zero if --sha is not 40 hex characters."""
    proc = subprocess.run(
        ["bash", "scripts/ci/cursor_cloud_full_pytest.sh", "--sha", "invalid-sha", "--nonce", "token123"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "40-character hex string" in proc.stderr


def test_runner_script_rejects_missing_nonce() -> None:
    """Runner script exits non-zero if --nonce is not provided."""
    proc = subprocess.run(
        ["bash", "scripts/ci/cursor_cloud_full_pytest.sh", "--sha", TEST_SHA],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "--nonce is required" in proc.stderr


def test_runner_script_rejects_head_sha_mismatch() -> None:
    """Runner script exits non-zero if requested --sha does not match git HEAD."""
    dummy_sha = "0000000000000000000000000000000000000000"
    proc = subprocess.run(
        ["bash", "scripts/ci/cursor_cloud_full_pytest.sh", "--sha", dummy_sha, "--nonce", "token123"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "does not match requested --sha" in proc.stderr or "dirty" in proc.stderr


def test_invalid_requested_sha_format_rejected(tmp_path: Path) -> None:
    """Non-40-hex requested_sha is rejected as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path)
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha="short-sha",
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("requested_sha must be a 40-character hex string" in r for r in result.reasons)


def test_invalid_runner_sha_format_rejected(tmp_path: Path) -> None:
    """Non-64-hex expected_runner_blob_sha256 is rejected as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path)
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256="short-hash",
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("expected_runner_blob_sha256 must be a 64-character hex string" in r for r in result.reasons)


def test_empty_nonce_rejected(tmp_path: Path) -> None:
    """Empty nonce parameter is rejected as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path)
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce="   ",
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("nonce parameter must not be empty" in r for r in result.reasons)


def test_nonexistent_artifact_directory_rejected(tmp_path: Path) -> None:
    """Nonexistent artifact directory is rejected as UNKNOWN/INFRA."""
    nonexistent = tmp_path / "nonexistent-dir"
    result = verify_cloud_artifacts(
        artifact_dir=nonexistent,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("does not exist or is not a directory" in r for r in result.reasons)


def test_missing_shard_directory_rejected(tmp_path: Path) -> None:
    """Missing a shard directory entirely fails closed as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path)
    import shutil
    shutil.rmtree(bundle / "pytest-shard-3")
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("missing shard directory: pytest-shard-3" in r for r in result.reasons)


def test_nodeids_txt_mismatch_with_plan_rejected(tmp_path: Path) -> None:
    """Discrepancy between test-nodeids.txt and plan.json assigned_nodeids is rejected."""
    bundle = create_synthetic_bundle(tmp_path)
    (bundle / "pytest-shard-2" / "test-nodeids.txt").write_text("tests/test_different.py::test_x\n", encoding="utf-8")
    result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("test-nodeids.txt does not match plan.json" in r for r in result.reasons)


def test_runner_script_help_flag() -> None:
    """Runner script with --help displays usage and exits 0."""
    proc = subprocess.run(
        ["bash", "scripts/ci/cursor_cloud_full_pytest.sh", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "Usage:" in proc.stdout


# =============================================================================
# 5. Delta Fail-Open Invariant Tests (#7113 Review Fixes)
# =============================================================================

def test_one_shard_synthetic_bundle_rejected_as_unknown_infra(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Fixed four-shard plane: 1-shard synthetic bundle fails closed as UNKNOWN/INFRA (never PASS)."""
    # Create 1-shard synthetic bundle (node count: 2)
    bundle_1shard = create_synthetic_bundle(tmp_path, shard_count=1)

    # 1. Verifying with shard_count=1 must be rejected (only 4 is allowed)
    res_1 = verify_cloud_artifacts(
        artifact_dir=bundle_1shard,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
        shard_count=1,
    )
    assert res_1.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert res_1.is_unknown_infra is True
    assert res_1.is_pass is False
    assert any("shard_count must be 4" in r for r in res_1.reasons)

    # 2. Verifying with default shard_count=4 fails due to missing shards 2-4
    res_4 = verify_cloud_artifacts(
        artifact_dir=bundle_1shard,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
        shard_count=4,
    )
    assert res_4.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert res_4.is_unknown_infra is True
    assert res_4.is_pass is False

    # 3. CLI execution with --shard-count 1 exits 2 with UNKNOWN/INFRA
    exit_code = verifier_main([
        "--artifact-dir", str(bundle_1shard),
        "--requested-sha", TEST_SHA,
        "--expected-runner-sha", TEST_RUNNER_SHA,
        "--nonce", TEST_NONCE,
        "--shard-count", "1",
    ])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "UNKNOWN/INFRA" in captured.out


def test_runner_script_rejects_shard_count_collapse() -> None:
    """Runner script refuses to execute with shard count != 4."""
    proc = subprocess.run(
        [
            "bash",
            "scripts/ci/cursor_cloud_full_pytest.sh",
            "--sha", TEST_SHA,
            "--nonce", "token123",
            "--shard-count", "1",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "--shard-count must be 4" in proc.stderr


def test_omitted_test_self_consistent_plans_rejected_by_anchoring(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Self-consistent omitted-test bundle (fail-open previously) is rejected as UNKNOWN/INFRA when anchored."""
    # Expected suite: 8 test nodes across 4 shards (2 tests per shard)
    expected_all_nodeids = [
        f"tests/test_module_{s}.py::{case}"
        for s in range(1, 5)
        for case in ("test_case_a", "test_case_b")
    ]
    assert len(expected_all_nodeids) == 8
    expected_digest_8 = _sha256_digest(expected_all_nodeids)

    # Create synthetic bundle (8 tests total)
    bundle = create_synthetic_bundle(tmp_path)

    # Verify happy path with anchored suite passes first
    green_result = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
        expected_nodeids=expected_all_nodeids,
        expected_collected_count=8,
        expected_collected_digest=expected_digest_8,
    )
    assert green_result.outcome == VerificationOutcome.PASS

    # Now mutate the bundle: omit 'tests/test_module_4.py::test_case_b' (leaving 7 tests)
    omitted_test = "tests/test_module_4.py::test_case_b"
    surviving_nodeids = [nid for nid in expected_all_nodeids if nid != omitted_test]
    assert len(surviving_nodeids) == 7
    surviving_digest_7 = _sha256_digest(surviving_nodeids)

    # 1. Update shard 4 artifacts to execute only 1 test
    shard4_assigned = ["tests/test_module_4.py::test_case_a"]
    (bundle / "pytest-shard-4" / "test-nodeids.txt").write_text("\n".join(shard4_assigned) + "\n", encoding="utf-8")
    junit4_xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="0" failures="0" skipped="0" tests="1" time="0.50">
  <testcase classname="tests.test_module_4" name="test_case_a" time="0.50"/>
</testsuite>
"""
    (bundle / "pytest-shard-4" / "main-junit.xml").write_text(junit4_xml, encoding="utf-8")

    # 2. Adjust all 4 plan.json files to self-consistently report collected_count=7 and collected_digest=digest(7)
    for s in range(1, 5):
        p_path = bundle / f"pytest-shard-{s}" / "plan.json"
        p_data = json.loads(p_path.read_text(encoding="utf-8"))
        p_data["collected_count"] = 7
        p_data["collected_digest"] = surviving_digest_7
        if s == 4:
            p_data["assigned_nodeids"] = shard4_assigned
            p_data["assigned_digest"] = _sha256_digest(shard4_assigned)
        p_path.write_text(json.dumps(p_data, indent=2), encoding="utf-8")

    # 3. Confirm that self-reported verify_artifacts() without anchor passes this self-consistent omitted test!
    from scripts.ci.pytest_shards import verify_artifacts
    verify_artifacts(bundle, 4)  # Passes because plans and JUnits are self-consistent!

    # 4. Controller anchored verification with expected_nodeids rejects with UNKNOWN/INFRA
    res_nodeids = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
        expected_nodeids=expected_all_nodeids,
    )
    assert res_nodeids.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert res_nodeids.is_unknown_infra is True
    assert any("collected_count" in r or "does not match anchored" in r or "missing=1" in r for r in res_nodeids.reasons)

    # 5. Controller anchored verification with expected_collected_count rejects with UNKNOWN/INFRA
    res_count = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
        expected_collected_count=8,
    )
    assert res_count.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("collected_count" in r and "8" in r for r in res_count.reasons)

    # 6. Controller anchored verification with expected_collected_digest rejects with UNKNOWN/INFRA
    res_digest = verify_cloud_artifacts(
        artifact_dir=bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
        expected_collected_digest=expected_digest_8,
    )
    assert res_digest.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert any("collected_digest" in r for r in res_digest.reasons)

    # 7. CLI verification with --expected-nodeids-file exits 2 with UNKNOWN/INFRA
    nodeids_file = tmp_path / "expected_nodeids.txt"
    nodeids_file.write_text("\n".join(expected_all_nodeids) + "\n", encoding="utf-8")
    exit_code = verifier_main([
        "--artifact-dir", str(bundle),
        "--requested-sha", TEST_SHA,
        "--expected-runner-sha", TEST_RUNNER_SHA,
        "--nonce", TEST_NONCE,
        "--expected-nodeids-file", str(nodeids_file),
    ])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "UNKNOWN/INFRA" in captured.out


def test_renamed_directory_mutation_rejected_as_unknown_infra(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Renaming bundle directory away from controller nonce fails closed as UNKNOWN/INFRA."""
    bundle = create_synthetic_bundle(tmp_path, nonce=TEST_NONCE)
    assert bundle.name == TEST_NONCE

    # Rename the bundle directory on disk
    renamed_bundle = tmp_path / "tampered-renamed-nonce-dir"
    bundle.rename(renamed_bundle)

    # Verifying renamed bundle against expected TEST_NONCE must fail as UNKNOWN/INFRA
    result = verify_cloud_artifacts(
        artifact_dir=renamed_bundle,
        requested_sha=TEST_SHA,
        expected_runner_blob_sha256=TEST_RUNNER_SHA,
        nonce=TEST_NONCE,
    )
    assert result.outcome == VerificationOutcome.UNKNOWN_INFRA
    assert result.is_unknown_infra is True
    assert any("artifact directory name" in r and "does not match expected nonce" in r for r in result.reasons)

    # CLI execution exits 2
    exit_code = verifier_main([
        "--artifact-dir", str(renamed_bundle),
        "--requested-sha", TEST_SHA,
        "--expected-runner-sha", TEST_RUNNER_SHA,
        "--nonce", TEST_NONCE,
    ])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "UNKNOWN/INFRA" in captured.out


def test_runner_script_contains_node22_confinement_and_dirty_tree_contracts() -> None:
    """Runner script asserts Node 22, write confinement outside repo, and final dirty-tree check."""
    script_path = Path("scripts/ci/cursor_cloud_full_pytest.sh")
    script_text = script_path.read_text(encoding="utf-8")

    # Fixed 4-shard plane
    assert "SHARD_COUNT must be 4" in script_text or "SHARD_COUNT\" -ne 4" in script_text

    # Node 22 check
    assert "NODE_VER" in script_text
    assert "v22" in script_text
    assert "Node 22" in script_text

    # Write confinement outside git worktree
    assert "cursor-cloud-ci-venv" in script_text or "TMPDIR" in script_text
    assert "never overwriting repo .venv" in script_text or "outside git worktree" in script_text

    # Final dirty-tree check
    assert "git status --porcelain --untracked-files=no" in script_text
    assert "modified tracked files after test execution" in script_text
