#!/usr/bin/env python3
"""Lint PR commits for the required ``X-Agent`` trailer.

Every commit on a non-main feature branch (i.e. a branch destined for a PR)
must declare which agent authored it via an ``X-Agent: <agent>/<task-id>``
trailer. Without this we cannot distinguish Codex / Gemini / Claude-headless
/ orchestrator-inline commits — the ``git committer`` field is always the
user's local config and is identical across agents.

Use when
========
- CI pre-merge gate on PRs.
- Pre-push hook on dispatch worktrees.

Do NOT use to retroactively rewrite history of already-merged commits — the
trailer is for forward-only enforcement.

Examples
========

    # Check every commit since branching from main
    .venv/bin/python scripts/audit/lint_agent_trailer.py

    # Check a specific range
    .venv/bin/python scripts/audit/lint_agent_trailer.py origin/main..HEAD

    # Check a single commit
    .venv/bin/python scripts/audit/lint_agent_trailer.py HEAD~1..HEAD

Outputs
=======
- stdout: per-commit verdict (PASS / FAIL with reason) and a final tally.
- exit 0 if every non-skipped commit has a valid ``X-Agent`` trailer.
- exit 1 if any commit is missing the trailer.

Skipped (exit 0 regardless)
===========================
- merge commits (``git log --no-merges`` is applied)
- dependabot branches (committer email ends with ``@dependabot``)
- the initial commit on main (no prior trailer expected)

Trailer format
==============
``X-Agent: <agent>/<task-id>``

Where ``agent`` ∈ {``claude-inline``, ``claude``, ``codex``, ``gemini``,
``agy-inline``, ``agy``, ``grok``, ``grok-build``, ``grok-hermes``,
``deepseek``, ``deepseek-v4-pro``, ``cursor``, ``glm``, ``kimi``, ``dependabot``} and ``task-id`` is the
dispatch task identifier or the ``inline`` literal for orchestrator commits.
``grok-build`` is a permanent alias of the native ``grok`` seat (historical
trailers must keep validating). ``gemini`` is an alias of ``agy``. Examples::

    X-Agent: claude-inline/orchestrator
    X-Agent: codex/1879-fix-ci-and-wikipedia
    X-Agent: claude/1657-adr-010
    X-Agent: gemini/1787-15-handoff-verifier
    X-Agent: deepseek/8642-some-task

Related
=======
- EPIC: parent of this lint (TBD — orchestrator-visibility follow-up)
- Sibling guardrails: scripts/audit/lint_dispatch_brief.py (#1788),
  scripts/audit/lint_anti_menu.py (#1789), scripts/audit/lint_session_state.py (#1792)
- Original ask: 2026-05-11 session — "can we make sure we know which agent is committing?"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.common.repo_root import resolve_repo_root
from scripts.orchestration.task_record_store import locate_task_record

_TRAILER_RE = re.compile(
    r"^X-Agent:\s+(?P<agent>claude-inline|claude|codex|gemini|agy-inline|agy|grok|grok-build|grok-hermes|deepseek|deepseek-v4-pro|cursor|glm|kimi|dependabot)/(?P<task>[A-Za-z0-9._-]+)\s*$",
    re.MULTILINE,
)

_CI_ENV_VARS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL")

DEFAULT_GIT_TIMEOUT_SECONDS: float = 30.0


def _detect_ci() -> str | None:
    """Return name of CI environment variable if running in CI, else None."""
    for var in _CI_ENV_VARS:
        if os.environ.get(var):
            return var
    return None


def _git(*args: str, cwd: Path | None = None) -> str:
    """Run a git command and return stdout, raising on non-zero exit."""
    return subprocess.check_output(
        ["git", *args], text=True, stderr=subprocess.PIPE, timeout=DEFAULT_GIT_TIMEOUT_SECONDS, cwd=cwd
    ).strip()


def _default_tasks_dir(repo_root: Path | None = None) -> Path:
    """Return the default tasks directory under batch_state/tasks."""
    root = repo_root or resolve_repo_root(Path(__file__), 2)
    return (root / "batch_state" / "tasks").resolve()


def _agents_match(a: str, b: str) -> bool:
    """Return True if two agent names match directly or via known aliases."""
    if a == b:
        return True
    pair = {a, b}
    return pair <= {"grok", "grok-build"} or pair <= {"gemini", "agy"} or pair <= {"deepseek", "deepseek-v4-pro"}


def locate_record_for_trailer(tasks_dir: Path, agent: str, task: str) -> tuple[Path | None, str | None]:
    """Locate task record for a trailer agent/task, normalization-aware.

    For trailer ``agent/task``, accepts a record named ``task`` or ``{agent}-task``
    (the inverse of ``_x_agent_task_id`` in delegate.py).
    """
    candidates = [task, f"{agent}-{task}"]
    if agent in ("gemini", "agy"):
        other = "agy" if agent == "gemini" else "gemini"
        candidates.append(f"{other}-{task}")
    elif agent in ("grok", "grok-build"):
        other = "grok-build" if agent == "grok" else "grok"
        candidates.append(f"{other}-{task}")
    elif agent in ("deepseek", "deepseek-v4-pro"):
        other = "deepseek" if agent == "deepseek-v4-pro" else "deepseek-v4-pro"
        candidates.append(f"{other}-{task}")

    for candidate in candidates:
        rec_path = locate_task_record(tasks_dir, candidate)
        if rec_path is not None:
            return rec_path, candidate
    return None, None


def _is_exempt_trailer(agent: str, task: str) -> bool:
    """Return True if the trailer represents a non-dispatched inline or bot commit.

    These trailers are shape-checked only:
    - *-inline/* (e.g. claude-inline/orchestrator, agy-inline/fix)
    - */inline (e.g. codex/inline, agy/inline)
    - dependabot/*
    """
    if agent.endswith("-inline") or agent == "dependabot":
        return True
    return task == "inline"


@dataclass(frozen=True)
class ProvenanceContext:
    active: bool
    skip_reason: str | None = None
    expected_task_id: str | None = None
    expected_agent: str | None = None
    tasks_dir: Path | None = None

    @property
    def expected_trailer(self) -> str | None:
        if self.expected_agent and self.expected_task_id:
            task = self.expected_task_id
            for prefix in (f"{self.expected_agent}-", f"{self.expected_agent}/"):
                if task.startswith(prefix):
                    task = task[len(prefix) :]
                    break
            return f"X-Agent: {self.expected_agent}/{task}"
        return None


def resolve_provenance_context(
    tasks_dir: Path | None = None,
    cwd: Path | None = None,
) -> ProvenanceContext:
    """Determine whether task provenance verification should run and resolve expected metadata."""
    # 1. Detect CI explicitly
    ci_var = _detect_ci()
    if ci_var:
        return ProvenanceContext(
            active=False,
            skip_reason=f"CI environment detected ({ci_var})",
            tasks_dir=tasks_dir,
        )

    # 2. Check dispatch env marker
    env_task_id = os.environ.get("LEARN_UKRAINIAN_DISPATCH_TASK_ID")
    if not env_task_id:
        return ProvenanceContext(
            active=False,
            skip_reason="dispatch task environment marker not set (LEARN_UKRAINIAN_DISPATCH_TASK_ID)",
            tasks_dir=tasks_dir,
        )

    # 3. Check tasks directory
    effective_tasks_dir = (tasks_dir or _default_tasks_dir()).resolve()
    if not effective_tasks_dir.is_dir():
        return ProvenanceContext(
            active=False,
            skip_reason=f"no task records directory found ({effective_tasks_dir})",
            tasks_dir=effective_tasks_dir,
        )

    # 4. Check if that task's record is found
    env_agent = os.environ.get("LEARN_UKRAINIAN_DISPATCH_AGENT")
    if not env_agent and (env_trailer := os.environ.get("LU_X_AGENT_TRAILER")):
        m = _TRAILER_RE.match(env_trailer.strip())
        if m:
            env_agent = m.group("agent")

    rec_path, _ = locate_record_for_trailer(effective_tasks_dir, env_agent or "", env_task_id)
    if rec_path is None:
        return ProvenanceContext(
            active=False,
            skip_reason=f"task record {env_task_id!r} not found in {effective_tasks_dir.name}",
            tasks_dir=effective_tasks_dir,
        )

    expected_agent = env_agent
    expected_task_id = env_task_id
    try:
        data = json.loads(rec_path.read_text(encoding="utf-8"))
        expected_agent = data.get("agent") or expected_agent
        expected_task_id = data.get("task_id") or expected_task_id
    except (OSError, json.JSONDecodeError):
        pass

    return ProvenanceContext(
        active=True,
        expected_task_id=expected_task_id,
        expected_agent=expected_agent,
        tasks_dir=effective_tasks_dir,
    )


def _commits_in_range(rev_range: str, cwd: Path | None = None) -> list[str]:
    """Return commit SHAs (newest first) in the range, excluding merges."""
    raw = _git("log", "--no-merges", "--format=%H", rev_range, cwd=cwd)
    return raw.splitlines() if raw else []


def _commit_meta(sha: str, cwd: Path | None = None) -> tuple[str, str, str, str]:
    """Return (committer_email, author_email, author_name, subject)."""
    raw = _git("log", "-1", "--format=%ce%n%ae%n%an%n%s", sha, cwd=cwd)
    parts = raw.splitlines()
    while len(parts) < 4:
        parts.append("")
    return parts[0], parts[1], parts[2], parts[3]


def _commit_body(sha: str, cwd: Path | None = None) -> str:
    return _git("log", "-1", "--format=%B", sha, cwd=cwd)


def _looks_like_dependabot(committer_email: str, author_email: str, author_name: str, subject: str) -> bool:
    """Recognize dependabot commits even after squash-merge rebases them through the user."""
    if "dependabot" in (committer_email + author_email + author_name).lower():
        return True
    if committer_email.endswith("@noreply.github.com"):
        return True
    # Squash-merged dependabot commit conventions
    return subject.startswith(("deps:", "Bump ", "build(deps"))


def _check_commit(
    sha: str,
    *,
    provenance: ProvenanceContext | None = None,
    cwd: Path | None = None,
) -> tuple[str, str]:
    """Return (verdict, reason). verdict ∈ {'PASS', 'SKIP', 'FAIL'}."""
    committer_email, author_email, author_name, subject = _commit_meta(sha, cwd=cwd)

    if _looks_like_dependabot(committer_email, author_email, author_name, subject):
        return "SKIP", f'dependabot/bot ("{subject[:50]}")'

    body = _commit_body(sha, cwd=cwd)
    match = _TRAILER_RE.search(body)
    if match is None:
        return "FAIL", f'missing X-Agent trailer in commit "{subject[:60]}"'

    agent = match.group("agent")
    task = match.group("task")
    trailer_str = f"X-Agent: {agent}/{task}"

    if _is_exempt_trailer(agent, task):
        return "PASS", trailer_str

    if provenance is None:
        provenance = resolve_provenance_context(cwd=cwd)

    if not provenance.active:
        return "PASS", trailer_str

    tasks_dir = provenance.tasks_dir or _default_tasks_dir()
    expected = (
        provenance.expected_trailer
        or f"X-Agent: {provenance.expected_agent or agent}/{provenance.expected_task_id or task}"
    )

    rec_path, _ = locate_record_for_trailer(tasks_dir, agent, task)
    if rec_path is None:
        return (
            "FAIL",
            f"task record {task!r} not found in {tasks_dir.name} (hot or archive); expected literal trailer: {expected!r}",
        )

    rec_agent: str | None = None
    try:
        rec_data = json.loads(rec_path.read_text(encoding="utf-8"))
        rec_agent = rec_data.get("agent")
    except (OSError, json.JSONDecodeError):
        pass

    target_agent = rec_agent or provenance.expected_agent
    if target_agent and not _agents_match(agent, target_agent):
        return (
            "FAIL",
            f"trailer {trailer_str!r} names agent {agent!r} but dispatch worktree agent is {target_agent!r}; expected literal trailer: {expected!r}",
        )

    return "PASS", trailer_str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint PR commits for required X-Agent trailer.\n"
        "Catches commits where the authoring agent isn't recorded — needed because\n"
        "git committer field is identical across all locally-dispatched agents.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "rev_range",
        nargs="?",
        default="origin/main..HEAD",
        help='Git rev range to check (default: "origin/main..HEAD"). '
        'Examples: "origin/main..HEAD", "HEAD~3..HEAD", "abc123..def456".',
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=None,
        help="Path to tasks directory (default: batch_state/tasks under repository root).",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=None,
        help="Working directory for git operations (default: current directory).",
    )
    args = parser.parse_args(argv)

    try:
        shas = _commits_in_range(args.rev_range, cwd=args.cwd)
    except subprocess.CalledProcessError as exc:
        print(f"git log failed: {exc.stderr or exc}", file=sys.stderr)
        return 2

    if not shas:
        print(f"No commits in range {args.rev_range!r} (nothing to check).")
        return 0

    provenance = resolve_provenance_context(tasks_dir=args.tasks_dir, cwd=args.cwd)
    if not provenance.active:
        print(f"ℹ️  Task provenance check skipped: {provenance.skip_reason}\n")
    else:
        print(f"🌲 Validating X-Agent task provenance (expected: {provenance.expected_trailer})\n")

    fails = 0
    print(f"Checking {len(shas)} commit(s) in {args.rev_range}:\n")
    for sha in shas:
        short = sha[:10]
        verdict, reason = _check_commit(sha, provenance=provenance, cwd=args.cwd)
        if verdict == "FAIL":
            fails += 1
            print(f"  {short}  FAIL  {reason}")
        else:
            print(f"  {short}  {verdict}  {reason}")

    print()
    if fails:
        print(
            f"❌ {fails}/{len(shas)} commit(s) failed X-Agent trailer check.\n"
            "   Add a trailer to each failing commit. Example for an orchestrator inline commit:\n"
            "       git commit --amend --trailer 'X-Agent: claude-inline/orchestrator'\n"
            "   For dispatched-agent commits, use the expected literal trailer:\n"
            f"       git commit --amend --trailer '{provenance.expected_trailer or 'X-Agent: <agent>/<task-id>'}'\n"
            "   See AGENTS.md rule #11 / GEMINI.md / agents_extensions/shared/rules/delegate-must-use-worktree.md."
        )
        return 1

    print(f"✅ All {len(shas)} non-skipped commit(s) carry an X-Agent trailer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
