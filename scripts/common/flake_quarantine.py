"""Validate the bounded flake quarantine and select exact pytest node IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

REGISTRY = Path(__file__).resolve().parents[2] / "tests/flake_quarantine.yaml"
REQUIRED = {
    "node_id", "fix_issue", "owner", "admitted_on", "expires_on", "observed_run_ids", "renewals",
    "equivalent_coverage", "admission_approval",
}
TIMEOUT_PATTERN = r"Timeout \(>[^)]*\) from pytest-timeout"
NODE_ID = re.compile(
    r"tests/(?:[A-Za-z0-9_]+/)*test_[A-Za-z0-9_]+\.py::"
    r"(?:[A-Za-z_]\w*::)*test_[A-Za-z0-9_]+(?:\[[^\r\n]+\])?"
)


def load_registry(path: Path = REGISTRY) -> list[dict]:
    """Reject malformed or unbounded entries before pytest can apply markers.

    This is offline lint. ``check_admissions`` verifies changed entries against
    GitHub before admission; pytest never needs network access.
    """
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _registry_entries(document)


def _registry_entries(document: object) -> list[dict]:
    if not isinstance(document, dict) or set(document) != {"entries"} or not isinstance(document["entries"], list):
        raise ValueError("quarantine registry must contain only an entries list")
    seen: set[str] = set()
    for number, entry in enumerate(document["entries"], 1):
        if not isinstance(entry, dict):
            raise ValueError(f"entry {number}: expected a mapping")
        expected = REQUIRED | ({"renewed_on"} if entry.get("renewals") == 1 else set())
        if set(entry) != expected:
            raise ValueError(f"entry {number}: required fields are {sorted(expected)}")
        node_id = entry["node_id"]
        if not isinstance(node_id, str) or not NODE_ID.fullmatch(node_id):
            raise ValueError(f"entry {number}: invalid pytest node_id")
        if node_id in seen:
            raise ValueError(f"entry {number}: duplicate node_id")
        seen.add(node_id)
        if type(entry["fix_issue"]) is not int or entry["fix_issue"] <= 0:
            raise ValueError(f"entry {number}: fix_issue must be a positive issue number")
        if not isinstance(entry["owner"], str) or not entry["owner"].strip():
            raise ValueError(f"entry {number}: owner is required")
        if type(entry["admission_approval"]) is not int or entry["admission_approval"] <= 0:
            raise ValueError(f"entry {number}: admission_approval must be an issue comment ID")
        coverage = entry["equivalent_coverage"]
        if not isinstance(coverage, dict) or not coverage or any(
            not isinstance(node, str) or not NODE_ID.fullmatch(node) or node == node_id
            or not isinstance(behavior, str) or not behavior.strip()
            for node, behavior in coverage.items()
        ):
            raise ValueError(f"entry {number}: equivalent_coverage needs other exact nodes and behavior explanations")
        runs = entry["observed_run_ids"]
        if not isinstance(runs, list) or len(runs) < 2 or any(type(run) is not int or run <= 0 for run in runs):
            raise ValueError(f"entry {number}: at least two positive observed run IDs are required")
        if len(set(runs)) != len(runs):
            raise ValueError(f"entry {number}: observed run IDs must be distinct")
        if type(entry["renewals"]) is not int or entry["renewals"] not in (0, 1):
            raise ValueError(f"entry {number}: at most one renewal is permitted")
        admitted, expiry = entry["admitted_on"], entry["expires_on"]
        if not isinstance(admitted, date) or isinstance(admitted, datetime):
            raise ValueError(f"entry {number}: admitted_on must be a date")
        if not isinstance(expiry, date) or isinstance(expiry, datetime):
            raise ValueError(f"entry {number}: expires_on must be a date")
        start = admitted
        if entry["renewals"]:
            start = entry["renewed_on"]
            if not isinstance(start, date) or isinstance(start, datetime):
                raise ValueError(f"entry {number}: renewed_on must be a date")
            if not admitted <= start <= admitted + timedelta(days=30):
                raise ValueError(f"entry {number}: renewal must occur within the first 30 days")
        if not start <= expiry <= start + timedelta(days=30):
            raise ValueError(f"entry {number}: expiry must be within 30 days")
    return document["entries"]


def admission_digest(entry: dict) -> str:
    """Bind designated approval to all admission fields except its comment ID."""
    payload = {key: value for key, value in entry.items() if key != "admission_approval"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _gh(*args: str) -> str:
    from scripts.common import github_client

    return github_client.run(
        ["gh", *args], fresh=True, capture_output=True, text=True, check=True, timeout=120,
    ).stdout


def _check_admission(entry: dict, *, repository: str, destination: Path) -> None:
    from scripts.ci.junit_results import parse_junit

    endpoint = f"repos/{repository}"
    issue = json.loads(_gh("api", f"{endpoint}/issues/{entry['fix_issue']}"))
    if issue.get("state") != "open" or "pull_request" in issue:
        raise ValueError("admission requires an open repair issue, not a PR")
    approval = json.loads(_gh("api", f"{endpoint}/issues/comments/{entry['admission_approval']}"))
    marker = f"<!-- flake-quarantine-admission:{admission_digest(entry)}:APPROVE -->"
    if (
        approval.get("issue_url") != issue.get("url")
        or approval.get("author_association") not in {"OWNER", "MEMBER", "COLLABORATOR"}
        or marker not in approval.get("body", "").splitlines()
    ):
        raise ValueError("missing designated admission approval bound to this entry on the repair issue")
    for run_id in entry["observed_run_ids"]:
        run = json.loads(_gh("api", f"{endpoint}/actions/runs/{run_id}"))
        sha = run.get("head_sha", "")
        if (
            run.get("head_branch") != "main"
            or run.get("head_repository", {}).get("full_name") != repository
            or run.get("event") not in {"push", "schedule", "workflow_dispatch"}
            or run.get("path") != ".github/workflows/ci.yml"
            or run.get("status") != "completed"
            or not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha)
        ):
            raise ValueError(f"run {run_id}: expected completed CI on unmodified main in this repository")
        comparison = json.loads(_gh("api", f"{endpoint}/compare/{sha}...main"))
        if comparison.get("merge_base_commit", {}).get("sha") != sha:
            raise ValueError(f"run {run_id}: head is not an ancestor of main")
        run_dir = destination / str(run_id)
        run_dir.mkdir()
        _gh("run", "download", str(run_id), "--repo", repository,
            "--pattern", "pytest-junit-shard-*", "--dir", str(run_dir))
        results = parse_junit(sorted(run_dir.rglob("*.xml")))
        failed = [result for result in results if result.node_id == entry["node_id"]]
        if len(failed) != 1 or not (
            failed[0].outcome in {"failed", "error"}
            or (failed[0].outcome == "passed" and failed[0].reruns > 0)
        ):
            raise ValueError(f"run {run_id}: missing exact-node baseline failure")
        for node in entry["equivalent_coverage"]:
            coverage = [result for result in results if result.node_id == node]
            if len(coverage) != 1 or coverage[0].outcome != "passed" or coverage[0].reruns:
                raise ValueError(f"run {run_id}: equivalent coverage {node} must pass without reruns")


def check_admissions(entries: list[dict], previous: list[dict], *, repository: str) -> int:
    """Verify new/changed admissions; unchanged entries outlive artifact retention.

    Trusted repository publishers record designated approval on the repair issue
    after checking the operator/advisor provenance and coverage explanation.
    Their digest-bound comment attests that judgment; a run ID alone does not.
    """
    from scripts.common.scratch import ensure_scratch_root

    old = {entry["node_id"]: entry for entry in previous}
    changed = [entry for entry in entries if old.get(entry["node_id"]) != entry]
    for entry in changed:
        TMPDIR = os.environ.get("TMPDIR") or ensure_scratch_root()
        with tempfile.TemporaryDirectory(prefix="flake-admission-", dir=TMPDIR) as directory:
            _check_admission(entry, repository=repository, destination=Path(directory))
    return len(changed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify changed flake quarantine admissions against GitHub baseline evidence.\n"
        "Use before adding or renewing an entry; pytest itself performs only offline lint.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.common.flake_quarantine --base-ref origin/main\n"
            "Outputs: admission counts on stdout; temporary JUnit downloads, no GitHub writes.\n"
            "Exit codes: 0 verified; nonzero malformed entries, missing evidence or unavailable GitHub.\n"
            "Related: tests/flake_quarantine.yaml; docs/runbooks/flake-quarantine.md; #10608."
        ),
    )
    parser.add_argument("--base-ref", required=True, help="Trusted pre-change Git ref, e.g. origin/main or the PR base SHA")
    args = parser.parse_args(argv)
    entries = load_registry()
    baseline = subprocess.run(
        ["git", "show", f"{args.base_ref}:tests/flake_quarantine.yaml"],
        capture_output=True, text=True, check=True, timeout=30,
    ).stdout
    previous = _registry_entries(yaml.safe_load(baseline))
    if all(entry in previous for entry in entries):
        print(f"Quarantine admission: {len(entries)} entries, 0 changed; offline lint passed")
        return 0
    repository = json.loads(_gh("repo", "view", "--json", "nameWithOwner"))["nameWithOwner"]
    checked = check_admissions(entries, previous, repository=repository)
    print(f"Quarantine admission: {len(entries)} entries, {checked} changed admissions verified")
    return 0


def rerun_node_ids(entries: list[dict], *, today: date, event_name: str | None) -> set[str]:
    """Schedule runs expose failures; entries lose reruns after seven grace days."""
    if event_name == "schedule":
        return set()
    return {entry["node_id"] for entry in entries if today <= entry["expires_on"] + timedelta(days=7)}


if __name__ == "__main__":
    raise SystemExit(main())
