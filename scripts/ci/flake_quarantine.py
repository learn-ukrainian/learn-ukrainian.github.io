"""Validate the bounded flake quarantine and select exact pytest node IDs."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

REGISTRY = Path(__file__).resolve().parents[2] / "tests/flake_quarantine.yaml"
REQUIRED = {"node_id", "fix_issue", "owner", "admitted_on", "expires_on", "observed_run_ids", "renewals"}
TIMEOUT_PATTERN = r"Timeout \(>[^)]*\) from pytest-timeout"


def load_registry(path: Path = REGISTRY) -> list[dict]:
    """Reject malformed or unbounded entries before pytest can apply markers.

    The offline check validates issue syntax and evidence shape. GitHub issue
    openness is an admission-time online check, outside this offline lint.
    """
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
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
        if not isinstance(node_id, str) or not node_id.startswith("tests/") or "::test_" not in node_id:
            raise ValueError(f"entry {number}: invalid pytest node_id")
        if node_id in seen:
            raise ValueError(f"entry {number}: duplicate node_id")
        seen.add(node_id)
        if type(entry["fix_issue"]) is not int or entry["fix_issue"] <= 0:
            raise ValueError(f"entry {number}: fix_issue must be a positive issue number")
        if not isinstance(entry["owner"], str) or not entry["owner"].strip():
            raise ValueError(f"entry {number}: owner is required")
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


def rerun_node_ids(entries: list[dict], *, today: date, event_name: str | None) -> set[str]:
    """Schedule runs expose failures; entries lose reruns after seven grace days."""
    if event_name == "schedule":
        return set()
    return {entry["node_id"] for entry in entries if today <= entry["expires_on"] + timedelta(days=7)}
