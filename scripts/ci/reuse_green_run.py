"""Merge queue: reuse a green full pytest run of the identical tree.

A merge-group commit whose tree (``git rev-parse <sha>^{tree}``) equals the
tree a pull_request run of ci.yml already tested in full, and passed, holds
the same code; running the suite again cannot learn anything new. The
pull_request run's ``pytest report`` job records that tree in the
``ci-tested-tree`` artifact only after every shard passed and the report
proved every test file ran.

Decision, written to ``$GITHUB_OUTPUT`` as ``reuse`` and ``run_id``:

* reuse=true  a successful pull_request run of the queued PR's head commit
              recorded ``tier: full`` for exactly this tree;
* reuse=false anything else: a different tree, no record, a record that is
              not the full tier, or any lookup error (fail closed: the queue
              run executes the full suite).

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
# refs/heads/gh-readonly-queue/<base>/pr-<number>-<parent sha>; the prefix is
# stripped by GitHub in merge_group.head_ref for some payloads, so match both.
_QUEUE_REF = re.compile(r"(?:^|/)gh-readonly-queue/.+/pr-(?P<number>[1-9][0-9]*)-[0-9a-f]{40}$")
_GH_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class Decision:
    reuse: bool
    run_id: str
    reason: str


def queued_pr_number(head_ref: str) -> int:
    match = _QUEUE_REF.search(head_ref)
    if match is None:
        raise ValueError(f"not a merge-queue ref: {head_ref!r}")
    return int(match.group("number"))


def decide(group_tree: str, candidates: Iterable[tuple[str, Callable[[], dict | None]]]) -> Decision:
    """Pick the first candidate run whose record proves a full run of ``group_tree``.

    ``candidates`` yields ``(run_id, load_record)`` for successful
    pull_request runs, newest first; ``load_record`` returns the parsed
    ``ci-tested-tree`` record or ``None`` when the run has none. Exceptions
    propagate to the caller, which fails closed.
    """
    reasons = []
    for run_id, load_record in candidates:
        record = load_record()
        if record is None:
            reasons.append(f"run {run_id}: no {ARTIFACT} record")
        elif record.get("tier") != FULL_TIER:
            reasons.append(f"run {run_id}: tier {record.get('tier')!r} is not {FULL_TIER!r}")
        elif record.get("tree") != group_tree:
            reasons.append(f"run {run_id}: tree {record.get('tree')} differs")
        else:
            return Decision(True, run_id, f"run {run_id} passed the full tier on tree {group_tree}")
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
    return decide(group_tree, ((str(run), lambda run=run: _load_record(repo, str(run))) for run in runs))


def main() -> int:
    try:
        decision = lookup(os.environ["REPO"], os.environ["HEAD_SHA"], os.environ["HEAD_REF"])
    except Exception as error:  # any lookup failure runs the full suite
        decision = Decision(False, "", f"lookup failed, running the full suite: {type(error).__name__}: {error}")
    line = f"reuse={'true' if decision.reuse else 'false'} run_id={decision.run_id or '-'} reason={decision.reason}"
    print(line)
    for name in ("GITHUB_OUTPUT", "GITHUB_STEP_SUMMARY"):
        target = os.environ.get(name)
        if not target:
            continue
        with open(target, "a", encoding="utf-8") as handle:
            if name == "GITHUB_OUTPUT":
                handle.write(f"reuse={'true' if decision.reuse else 'false'}\nrun_id={decision.run_id}\n")
            else:
                handle.write(f"Merge-queue reuse check: {line}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
