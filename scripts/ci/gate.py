"""Require full-suite results for the checked-out candidate."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}\Z")
COMMON = frozenset({"secret-scan", "checks", "dependency-audit", "pr-affected"})
FULL = frozenset({"frontend", "refresh-pytest-durations", "pytest", "pytest-report"})


def event_tier(event: str, payload: dict, sha: str, ref: str, actual: str) -> str:
    """Parse the external event and bind its candidate to GitHub's checked-out SHA."""
    if not SHA.fullmatch(sha) or sha != actual:
        raise ValueError("checked-out candidate does not match GITHUB_SHA")
    subprocess.run(["git", "check-ref-format", ref], check=True, capture_output=True, timeout=30)
    default = payload["repository"]["default_branch"]
    if not isinstance(default, str) or not default or any(ord(c) < 32 for c in default):
        raise ValueError("default branch is missing or invalid")
    if event == "pull_request":
        pr = payload["pull_request"]
        number = pr["number"]
        if (payload["action"] not in {"opened", "synchronize", "reopened"}
                or type(number) is not int or number < 1 or ref != f"refs/pull/{number}/merge"
                or not SHA.fullmatch(pr["base"]["sha"]) or not SHA.fullmatch(pr["head"]["sha"])):
            raise ValueError("invalid pull_request identity")
        return "full"
    if event == "merge_group":
        group = payload["merge_group"]
        queue_ref = rf"refs/heads/gh-readonly-queue/{re.escape(default)}/pr-[1-9][0-9]*-[0-9a-f]{{40}}"
        if (payload["action"] != "checks_requested" or group["head_sha"] != sha
                or group["head_ref"] != ref or not re.fullmatch(queue_ref, ref)
                or group["base_ref"] != f"refs/heads/{default}"
                or not SHA.fullmatch(group["base_sha"]) or group["base_sha"] == sha):
            raise ValueError("invalid merge_group identity")
        subprocess.run(["git", "merge-base", "--is-ancestor", group["base_sha"], sha],
                       check=True, capture_output=True, timeout=30)
        return "full"
    if event == "schedule":
        if ref != f"refs/heads/{default}" or payload["schedule"] != "30 3 * * *":
            raise ValueError("invalid nightly identity")
        return "full"
    if event == "workflow_dispatch":
        if not ref.startswith(("refs/heads/", "refs/tags/")) or any(ord(c) < 32 for c in ref):
            raise ValueError("invalid manual ref")
        if payload["ref"] not in {ref, ref.removeprefix("refs/heads/").removeprefix("refs/tags/")}:
            raise ValueError("manual event ref does not match GITHUB_REF")
        inputs = payload.get("inputs")
        if inputs is None:
            inputs = {}
        if inputs.get("secret_scan_mode", "bounded") not in {"bounded", "full-history-audit"}:
            raise ValueError("invalid manual scan mode")
        return "full"
    raise ValueError("unsupported CI event")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate CI event identity and require every result in its tier.\n"
        "Use inside ci.yml with GitHub event variables; this does not run tests or authorize a merge.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.ci.gate\n"
        "  .venv/bin/python -m scripts.ci.gate --record-queue\n"
        "Inputs: EVENT_NAME, GITHUB_EVENT_PATH, GITHUB_SHA, GITHUB_REF; NEEDS_JSON for aggregation.\n"
        "Queue recording also needs QUEUE_RECORD, GITHUB_RUN_ID and GITHUB_RUN_ATTEMPT.\n"
        "Outputs: job results and GITHUB_STEP_SUMMARY, or QUEUE_RECORD JSON; no network or Git writes.\n"
        "Exit codes: 0 valid proof; 1 missing/invalid proof; 2 invalid arguments.\n"
        "Related: .github/workflows/ci.yml; docs/runbooks/ci-gate.md; OO-98.",
    )
    parser.add_argument("--record-queue", action="store_true", default=False,
                        help="Write original queue identity to QUEUE_RECORD, e.g. queue-candidate.json; default: validate job results.")
    args = parser.parse_args()
    try:
        event = os.environ["EVENT_NAME"]
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        actual = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=30
        ).stdout.strip()
        tier = event_tier(event, payload, os.environ["GITHUB_SHA"], os.environ["GITHUB_REF"], actual)
        if args.record_queue:
            if event != "merge_group":
                raise ValueError("queue record requires a merge-group event")
            record = {key: payload["merge_group"][key] for key in ("base_sha", "head_sha", "head_ref")}
            record.update(run_id=int(os.environ["GITHUB_RUN_ID"]), run_attempt=int(os.environ["GITHUB_RUN_ATTEMPT"]))
            if record["run_id"] < 1 or record["run_attempt"] < 1:
                raise ValueError("invalid queue run identity")
            Path(os.environ["QUEUE_RECORD"]).write_text(json.dumps(record) + "\n", encoding="utf-8")
            return 0
        results = json.loads(os.environ["NEEDS_JSON"])
        if set(results) != COMMON | FULL | {"queue-metadata-scan"}:
            raise ValueError("missing or unexpected CI dependencies")
        failed = False
        for name, result in sorted(results.items()):
            expected = "success" if name in COMMON or (name in FULL and tier == "full") or (
                name == "queue-metadata-scan" and event == "merge_group"
            ) else "skipped"
            value = result.get("result")
            print(f"{name}: {value}, expected {expected}")
            if value != expected:
                if value == "cancelled":
                    print(f"::error::required job was cancelled: {name}")
                failed = True
        summary = "Full supported pytest suite and partition audits are required."
        print(summary)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
                stream.write(summary + "\n")
        if not failed:
            print("CI Gate green")
        return int(failed)
    except (KeyError, TypeError, ValueError, AttributeError, OSError, subprocess.SubprocessError) as exc:
        print(f"::error::CI proof incomplete: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
