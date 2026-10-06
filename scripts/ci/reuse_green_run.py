"""Merge queue: reuse a green full run of ci.yml on the identical tree.

A merge-group commit whose tree equals the tree a pull_request run of ci.yml
already tested in full, and passed, holds the same code; running the same
jobs again cannot learn anything new. Reuse is allowed only when one
candidate run proves all of the following; anything else, including any
lookup error, is reuse=false and the queue run executes every job:

* the run: a ``pull_request`` run of ``.github/workflows/ci.yml`` for the
  queued PR's current head commit, completed with ``success`` in its first and
  only attempt (a re-run mixes jobs of different attempts);
* its ``ci-tested-tree`` record (written by ``pytest report`` only after every
  shard passed and the report proved every test file ran): ``tier: full``,
  the queued PR's number, this run's id and attempt, more than zero tests,
  and the tested commit's SHA;
* the tested commit, read from GitHub rather than taken from the record: a
  merge of the queued PR's head (the pull_request merge commit) whose tree is
  the merge-group commit's tree, and the record names that same tree;
* the run's jobs: exactly the complete ci.yml inventory (``EXPECTED_JOBS``
  plus ``pytest (N)`` for every shard in ci.yml's matrix), each exactly once,
  completed with ``success``; the only other jobs allowed are the queue-only
  jobs (``SKIPPED_ON_PULL_REQUEST``), and those must be ``skipped``. Advisory
  jobs (``REUSE_NEUTRAL_JOBS``) are ignored and never included in reused jobs.

Decision, written to ``$GITHUB_OUTPUT`` as ``reuse`` and ``run_id``; the job
summary names the reused run and the job id of every reused job.

Stdlib plus the ``gh`` CLI, so it runs before any project install.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

ARTIFACT = "ci-tested-tree"
FULL_TIER = "full"
WORKFLOW = ".github/workflows/ci.yml"
# ci.yml job names a pull_request run must have succeeded in, besides pytest (N).
EXPECTED_JOBS = (
    "Secret scan",
    "Checks",
    "Freeze pytest durations",
    "Frontend",
    "Dependency audit",
    "pytest report",
    "CI Gate",
)
# ci.yml jobs that run only in the merge queue.
SKIPPED_ON_PULL_REQUEST = ("Reuse check", "Queue commit metadata scan")
# Advisory jobs have no bearing on reuse, regardless of their result.
REUSE_NEUTRAL_JOBS = ("Component shadow",)
# refs/heads/gh-readonly-queue/<base>/pr-<number>-<parent sha>; the prefix is
# stripped by GitHub in merge_group.head_ref for some payloads, so match both.
_QUEUE_REF = re.compile(r"(?:^|/)gh-readonly-queue/.+/pr-(?P<number>[1-9][0-9]*)-[0-9a-f]{40}$")
_SHARD_MATRIX = re.compile(r"^\s+shard:\s*\[(?P<shards>[0-9,\s]+)\]\s*$", re.MULTILINE)
_SHA = re.compile(r"[0-9a-f]{40}")
_GH_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class Queued:
    """What the reused run must have tested."""

    pr: int
    pr_head: str
    tree: str  # the merge-group commit's tree
    jobs: tuple[str, ...]  # the complete expected job inventory


@dataclass(frozen=True)
class Candidate:
    run: dict  # id, event, path, status, conclusion, run_attempt, head_sha
    load_record: Callable[[], dict | None]  # the ci-tested-tree record, None when absent
    load_commit: Callable[[str], dict]  # sha -> {sha, tree, parents}
    load_jobs: Callable[[], dict]  # {total_count, jobs: [{name, status, conclusion, id, run_attempt}]}


@dataclass(frozen=True)
class Decision:
    reuse: bool
    run_id: str
    reason: str
    jobs: tuple[tuple[str, int], ...] = ()  # (job name, job id) in the reused run


def queued_pr_number(head_ref: str) -> int:
    match = _QUEUE_REF.search(head_ref)
    if match is None:
        raise ValueError(f"not a merge-queue ref: {head_ref!r}")
    return int(match.group("number"))


def pytest_shards(workflow: str) -> tuple[int, ...]:
    """The ``pytest`` matrix's shard numbers from ci.yml's text."""
    matches = _SHARD_MATRIX.findall(workflow)
    if len(matches) != 1:
        raise ValueError(f"expected one 'shard: [...]' matrix in {WORKFLOW}, found {len(matches)}")
    shards = tuple(int(value) for value in matches[0].replace(",", " ").split())
    if not shards or shards != tuple(range(1, len(shards) + 1)):
        raise ValueError(f"pytest shards are not 1..N: {shards}")
    return shards


def expected_jobs(shards: Iterable[int]) -> tuple[str, ...]:
    return (*EXPECTED_JOBS, *(f"pytest ({shard})" for shard in shards))


def run_problem(run: dict, queued: Queued) -> str | None:
    expected = {
        "event": "pull_request",
        "path": WORKFLOW,
        "status": "completed",
        "conclusion": "success",
        "run_attempt": 1,
        "head_sha": queued.pr_head,
    }
    for key, value in expected.items():
        if run.get(key) != value:
            return f"{key} is {run.get(key)!r}, not {value!r}"
    return None


def record_problem(record: dict | None, run: dict, queued: Queued) -> str | None:
    if record is None:
        return f"no {ARTIFACT} record"
    expected = {"tier": FULL_TIER, "pr": queued.pr, "run_id": run["id"], "run_attempt": 1}
    for key, value in expected.items():
        if record.get(key) != value:
            return f"record {key} is {record.get(key)!r}, not {value!r}"
    tests = record.get("tests")
    if not isinstance(tests, int) or isinstance(tests, bool) or tests <= 0:
        return f"record claims {tests!r} tests"
    if not isinstance(record.get("sha"), str) or not _SHA.fullmatch(record["sha"]):
        return f"record sha {record.get('sha')!r} is not a commit SHA"
    return None


def commit_problem(commit: dict, record: dict, queued: Queued) -> str | None:
    """``commit`` is GitHub's view of ``record['sha']``; the record's own tree is not trusted."""
    if commit.get("sha") != record["sha"]:
        return f"GitHub returned commit {commit.get('sha')!r} for {record['sha']}"
    if len(commit.get("parents", [])) != 2 or queued.pr_head not in commit["parents"]:
        return f"tested commit {record['sha']} is not a merge of PR head {queued.pr_head}"
    if commit.get("tree") != queued.tree:
        return f"tested commit {record['sha']} has tree {commit.get('tree')}, the queue commit {queued.tree}"
    if record.get("tree") != queued.tree:
        return f"record tree {record.get('tree')!r} is not the tested commit's tree"
    return None


def job_inventory(listing: dict, expected: tuple[str, ...]) -> tuple[tuple[str, int], ...] | str:
    """``(name, id)`` of every expected job, or why the run's jobs are not exactly the inventory."""
    jobs = listing.get("jobs", [])
    if listing.get("total_count") != len(jobs):
        return f"{len(jobs)} of {listing.get('total_count')} jobs listed"
    jobs = [job for job in jobs if job.get("name") not in REUSE_NEUTRAL_JOBS]
    if attempts := sorted({job.get("run_attempt") for job in jobs} - {1}):
        return f"jobs from run attempt {attempts}"
    counts = Counter(job.get("name") for job in jobs)
    for job in jobs:
        name = job.get("name")
        if name in SKIPPED_ON_PULL_REQUEST:
            if job.get("conclusion") != "skipped":
                return f"{name!r} concluded {job.get('conclusion')!r}, not 'skipped'"
        elif name not in expected:
            return f"unexpected job {name!r}"
    found = []
    for name in expected:
        if counts[name] != 1:
            return f"{counts[name]} jobs named {name!r}"
        job = next(job for job in jobs if job.get("name") == name)
        if (job.get("status"), job.get("conclusion")) != ("completed", "success"):
            return f"{name!r} is {job.get('status')!r}/{job.get('conclusion')!r}"
        found.append((name, int(job["id"])))
    return tuple(found)


def decide(queued: Queued, candidates: Iterable[Candidate]) -> Decision:
    """Pick the first candidate run that proves a full, green run of the queued tree.

    Exceptions propagate to the caller, which fails closed.
    """
    reasons = []
    for candidate in candidates:
        run_id = str(candidate.run.get("id"))
        if problem := run_problem(candidate.run, queued):
            reasons.append(f"run {run_id}: {problem}")
            continue
        record = candidate.load_record()
        if (problem := record_problem(record, candidate.run, queued)) or (
            problem := commit_problem(candidate.load_commit(record["sha"]), record, queued)
        ):
            reasons.append(f"run {run_id}: {problem}")
            continue
        jobs = job_inventory(candidate.load_jobs(), queued.jobs)
        if isinstance(jobs, str):
            reasons.append(f"run {run_id}: {jobs}")
            continue
        return Decision(
            True,
            run_id,
            f"run {run_id} tested PR #{queued.pr} at {record['sha']} (tree {queued.tree}, "
            f"{record['tests']} tests) and all {len(jobs)} jobs succeeded",
            jobs,
        )
    return Decision(False, "", "; ".join(reasons) or "no successful pull_request run of the queued head")


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True, timeout=_GH_TIMEOUT_SECONDS).stdout


def _gh_json(path: str, jq: str) -> object:
    return json.loads(_gh("api", path, "--jq", jq))


def _load_record(repo: str, run_id: str) -> dict | None:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _gh("run", "download", run_id, "--repo", repo, "--name", ARTIFACT, "--dir", tmp)
        except subprocess.CalledProcessError as error:
            if "no artifact" in (error.stderr or "").lower() or "not found" in (error.stderr or "").lower():
                return None
            raise
        return json.loads((Path(tmp) / "tested-tree.json").read_text(encoding="utf-8"))


def lookup(repo: str, head_sha: str, head_ref: str, workflow: Path = Path(WORKFLOW)) -> Decision:
    group_tree = subprocess.run(
        ["git", "rev-parse", f"{head_sha}^{{tree}}"], capture_output=True, text=True, check=True, timeout=30
    ).stdout.strip()
    number = queued_pr_number(head_ref)
    # The checkout is the merge-group commit, so this is the ci.yml the PR run used too.
    queued = Queued(
        pr=number,
        pr_head=_gh("api", f"repos/{repo}/pulls/{number}", "--jq", ".head.sha").strip(),
        tree=group_tree,
        jobs=expected_jobs(pytest_shards(workflow.read_text(encoding="utf-8"))),
    )
    runs = _gh_json(
        f"repos/{repo}/actions/workflows/ci.yml/runs?event=pull_request&status=success"
        f"&head_sha={queued.pr_head}&per_page=10",
        "[.workflow_runs[] | {id, event, path, status, conclusion, run_attempt, head_sha}]",
    )
    return decide(
        queued,
        (
            Candidate(
                run=run,
                load_record=lambda run=run: _load_record(repo, str(run["id"])),
                load_commit=lambda sha: _gh_json(
                    f"repos/{repo}/git/commits/{sha}", "{sha, tree: .tree.sha, parents: [.parents[].sha]}"
                ),
                # Attempt 1 only: run_problem already refused any re-run.
                load_jobs=lambda run=run: _gh_json(
                    f"repos/{repo}/actions/runs/{run['id']}/attempts/1/jobs?per_page=100",
                    "{total_count, jobs: [.jobs[] | {name, status, conclusion, id, run_attempt}]}",
                ),
            )
            for run in runs
        ),
    )


def main() -> int:
    try:
        decision = lookup(os.environ["REPO"], os.environ["HEAD_SHA"], os.environ["HEAD_REF"])
    except Exception as error:  # any lookup failure runs every job
        decision = Decision(False, "", f"lookup failed, running every job: {type(error).__name__}: {error}")
    line = f"reuse={'true' if decision.reuse else 'false'} run_id={decision.run_id or '-'} reason={decision.reason}"
    jobs = [f"{name}: reused from run {decision.run_id}, job {job} (success)" for name, job in decision.jobs]
    print("\n".join([line, *jobs]))
    for name in ("GITHUB_OUTPUT", "GITHUB_STEP_SUMMARY"):
        target = os.environ.get(name)
        if not target:
            continue
        with open(target, "a", encoding="utf-8") as handle:
            if name == "GITHUB_OUTPUT":
                handle.write(f"reuse={'true' if decision.reuse else 'false'}\nrun_id={decision.run_id}\n")
            else:
                handle.write("".join(f"- {text}\n" for text in [f"Merge-queue reuse check: {line}", *jobs]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
