"""Merge queue: reuse a green full run of ci.yml on the identical tree.

A merge-group commit whose tree (``git rev-parse <sha>^{tree}``) equals the
tree a pull_request run of ci.yml already tested in full, and passed, holds
the same code; running the same jobs again cannot learn anything new. The
pull_request run's ``pytest report`` job records that tree in the
``ci-tested-tree`` artifact only after every shard passed and the report
proved every test file ran. The other required jobs of that run (``GATES``)
must each have one job that concluded ``success``.

Decision, written to ``$GITHUB_OUTPUT`` as ``reuse`` and ``run_id``:

* reuse=true  a successful pull_request run of the queued PR's head commit
              recorded ``tier: full`` for exactly this tree, and every gate
              in ``GATES`` succeeded in that run;
* reuse=false anything else: a different tree, no record, a record that is
              not the full tier, a gate that is missing or did not succeed,
              or any lookup error (fail closed: the queue run executes every
              job).

The job summary names the reused run and job for each gate.

Stdlib plus the ``gh`` CLI, so it runs before any project install.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

ARTIFACT = "ci-tested-tree"
FULL_TIER = "full"
# ci.yml job names whose result a reuse stands in for; pytest (N) is covered
# by the record, which pytest report writes only after every shard passed.
GATES = ("Secret scan", "Checks", "Frontend", "pytest report")
# refs/heads/gh-readonly-queue/<base>/pr-<number>-<parent sha>; the prefix is
# stripped by GitHub in merge_group.head_ref for some payloads, so match both.
_QUEUE_REF = re.compile(r"(?:^|/)gh-readonly-queue/.+/pr-(?P<number>[1-9][0-9]*)-[0-9a-f]{40}$")
_GH_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class Decision:
    reuse: bool
    run_id: str
    reason: str
    jobs: tuple[tuple[str, int], ...] = ()  # (gate, job id) in the reused run


def queued_pr_number(head_ref: str) -> int:
    match = _QUEUE_REF.search(head_ref)
    if match is None:
        raise ValueError(f"not a merge-queue ref: {head_ref!r}")
    return int(match.group("number"))


def gate_jobs(jobs: list[dict]) -> tuple[tuple[str, int], ...] | str:
    """``(gate, job id)`` for every gate in ``GATES``, or why the run does not qualify."""
    found = []
    for gate in GATES:
        matches = [job for job in jobs if job.get("name") == gate]
        if len(matches) != 1:
            return f"{len(matches)} jobs named {gate!r}"
        if matches[0].get("conclusion") != "success":
            return f"{gate!r} concluded {matches[0].get('conclusion')!r}"
        found.append((gate, int(matches[0]["id"])))
    return tuple(found)


def decide(
    group_tree: str, candidates: Iterable[tuple[str, Callable[[], dict | None], Callable[[], list[dict]]]]
) -> Decision:
    """Pick the first candidate run that proves a full, green run of ``group_tree``.

    ``candidates`` yields ``(run_id, load_record, load_jobs)`` for successful
    pull_request runs, newest first; ``load_record`` returns the parsed
    ``ci-tested-tree`` record or ``None`` when the run has none, and
    ``load_jobs`` the run's jobs (``name``, ``conclusion``, ``id``).
    Exceptions propagate to the caller, which fails closed.
    """
    reasons = []
    for run_id, load_record, load_jobs in candidates:
        record = load_record()
        if record is None:
            reasons.append(f"run {run_id}: no {ARTIFACT} record")
        elif record.get("tier") != FULL_TIER:
            reasons.append(f"run {run_id}: tier {record.get('tier')!r} is not {FULL_TIER!r}")
        elif record.get("tree") != group_tree:
            reasons.append(f"run {run_id}: tree {record.get('tree')} differs")
        elif isinstance(jobs := gate_jobs(load_jobs()), str):
            reasons.append(f"run {run_id}: {jobs}")
        else:
            return Decision(True, run_id, f"run {run_id} passed every gate on tree {group_tree}", jobs)
    return Decision(False, "", "; ".join(reasons) or "no successful pull_request run of the queued head")


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True, timeout=_GH_TIMEOUT_SECONDS).stdout


def _load_record(repo: str, run_id: str) -> dict | None:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _gh("run", "download", run_id, "--repo", repo, "--name", ARTIFACT, "--dir", tmp)
        except subprocess.CalledProcessError as error:
            if "no artifact" in (error.stderr or "").lower() or "not found" in (error.stderr or "").lower():
                return None
            raise
        return json.loads((Path(tmp) / "tested-tree.json").read_text(encoding="utf-8"))


def _load_jobs(repo: str, run_id: str) -> list[dict]:
    # ci.yml has about 22 jobs; one page of 100 holds them all.
    return json.loads(
        _gh(
            "api", f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100", "--jq", "[.jobs[] | {name, conclusion, id}]"
        )
    )


def lookup(repo: str, head_sha: str, head_ref: str) -> Decision:
    group_tree = subprocess.run(
        ["git", "rev-parse", f"{head_sha}^{{tree}}"], capture_output=True, text=True, check=True, timeout=30
    ).stdout.strip()
    number = queued_pr_number(head_ref)
    pr_head = _gh("api", f"repos/{repo}/pulls/{number}", "--jq", ".head.sha").strip()
    runs = json.loads(
        _gh(
            "api",
            f"repos/{repo}/actions/workflows/ci.yml/runs?event=pull_request&status=success&head_sha={pr_head}&per_page=10",
            "--jq",
            "[.workflow_runs[] | .id]",
        )
    )
    return decide(
        group_tree,
        (
            (str(run), lambda run=run: _load_record(repo, str(run)), lambda run=run: _load_jobs(repo, str(run)))
            for run in runs
        ),
    )


def main() -> int:
    try:
        decision = lookup(os.environ["REPO"], os.environ["HEAD_SHA"], os.environ["HEAD_REF"])
    except Exception as error:  # any lookup failure runs every job
        decision = Decision(False, "", f"lookup failed, running every job: {type(error).__name__}: {error}")
    line = f"reuse={'true' if decision.reuse else 'false'} run_id={decision.run_id or '-'} reason={decision.reason}"
    gates = [f"{gate}: reused from run {decision.run_id}, job {job} (success)" for gate, job in decision.jobs]
    print("\n".join([line, *gates]))
    for name in ("GITHUB_OUTPUT", "GITHUB_STEP_SUMMARY"):
        target = os.environ.get(name)
        if not target:
            continue
        with open(target, "a", encoding="utf-8") as handle:
            if name == "GITHUB_OUTPUT":
                handle.write(f"reuse={'true' if decision.reuse else 'false'}\nrun_id={decision.run_id}\n")
            else:
                handle.write("".join(f"- {text}\n" for text in [f"Merge-queue reuse check: {line}", *gates]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
