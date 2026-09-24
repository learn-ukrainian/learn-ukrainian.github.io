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
``deepseek-v4-pro``, ``cursor``, ``glm``, ``kimi``, ``dependabot``} and ``task-id`` is the
dispatch task identifier or the ``inline`` literal for orchestrator commits.
``grok-build`` is a permanent alias of the native ``grok`` seat (historical
trailers must keep validating). Examples::

    X-Agent: claude-inline/orchestrator
    X-Agent: codex/1879-fix-ci-and-wikipedia
    X-Agent: claude/1657-adr-010
    X-Agent: gemini/1787-15-handoff-verifier

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

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from scripts.orchestration.task_record_store import iter_task_records, locate_task_record
except ImportError:  # pragma: no cover
    from orchestration.task_record_store import iter_task_records, locate_task_record

_TRAILER_RE = re.compile(
    r"^X-Agent:\s+(?P<agent>claude-inline|claude|codex|gemini|agy-inline|agy|grok|grok-build|grok-hermes|deepseek-v4-pro|cursor|glm|kimi|dependabot)/(?P<task>[A-Za-z0-9._-]+)\s*$",
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


def _resolve_repo_root(cwd: Path | None = None) -> Path:
    """Resolve repository primary root from git-common-dir."""
    try:
        raw = _git("rev-parse", "--git-common-dir", cwd=cwd)
        p = Path(raw)
        p = ((cwd or Path.cwd()) / p).resolve() if not p.is_absolute() else p.resolve()
        if p.name == ".git":
            return p.parent
        return p
    except Exception:
        return (cwd or Path.cwd()).resolve()


def _resolve_worktree_dir(cwd: Path | None = None) -> Path:
    """Resolve current worktree directory."""
    try:
        raw = _git("rev-parse", "--show-toplevel", cwd=cwd)
        return Path(raw).resolve()
    except Exception:
        return (cwd or Path.cwd()).resolve()


def _default_tasks_dir(repo_root: Path | None = None) -> Path:
    """Return the default tasks directory."""
    env_dir = os.environ.get("LU_TASKS_DIR") or os.environ.get("LEARN_UKRAINIAN_TASKS_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    if repo_root is None:
        repo_root = _resolve_repo_root()
    return (repo_root / "batch_state" / "tasks").resolve()


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
            return f"X-Agent: {self.expected_agent}/{self.expected_task_id}"
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

    # 2. Detect missing tasks directory or no records present
    effective_tasks_dir = (tasks_dir or _default_tasks_dir(repo_root=_resolve_repo_root(cwd))).resolve()
    if not effective_tasks_dir.is_dir():
        return ProvenanceContext(
            active=False,
            skip_reason=f"no task records directory found ({effective_tasks_dir})",
            tasks_dir=effective_tasks_dir,
        )

    has_records = any(iter_task_records(effective_tasks_dir, include_archive=True))
    if not has_records:
        return ProvenanceContext(
            active=False,
            skip_reason=f"no task records present in {effective_tasks_dir}",
            tasks_dir=effective_tasks_dir,
        )

    # 3. Detect if we are inside a dispatch worktree whose task record is known
    repo_root = _resolve_repo_root(cwd)
    worktree_dir = _resolve_worktree_dir(cwd)

    known_task_id: str | None = None
    known_agent: str | None = None

    # Check environment markers first
    env_task_id = os.environ.get("LEARN_UKRAINIAN_DISPATCH_TASK_ID")
    env_agent = os.environ.get("LEARN_UKRAINIAN_DISPATCH_AGENT")
    env_trailer = os.environ.get("LU_X_AGENT_TRAILER")
    if env_trailer:
        m = _TRAILER_RE.match(env_trailer.strip())
        if m:
            env_agent = env_agent or m.group("agent")
            env_task_id = env_task_id or m.group("task")

    if env_task_id:
        known_task_id = env_task_id
        known_agent = env_agent

    # Inspect path layout: .worktrees/dispatch/<agent>/<task>/
    if not known_task_id:
        dispatch_root = (repo_root / ".worktrees" / "dispatch").resolve()
        try:
            rel = worktree_dir.relative_to(dispatch_root)
            if len(rel.parts) >= 2:
                path_agent, path_task = rel.parts[0], rel.parts[1]
                for candidate in (path_task, f"{path_agent}-{path_task}", f"{path_agent}/{path_task}"):
                    rec_path = locate_task_record(effective_tasks_dir, candidate)
                    if rec_path is not None:
                        try:
                            data = json.loads(rec_path.read_text(encoding="utf-8"))
                            known_task_id = data.get("task_id") or candidate
                            known_agent = data.get("agent") or path_agent
                            break
                        except Exception:
                            continue
                if not known_task_id:
                    known_task_id = path_task
                    known_agent = path_agent
        except ValueError:
            pass

    # Inspect task records matching worktree_path
    if not known_task_id:
        for rec_file in iter_task_records(effective_tasks_dir, include_archive=True):
            try:
                data = json.loads(rec_file.read_text(encoding="utf-8"))
                wt = data.get("worktree_path")
                if wt and Path(wt).resolve() == worktree_dir:
                    known_task_id = data.get("task_id")
                    known_agent = data.get("agent")
                    break
            except Exception:
                continue

    if not known_task_id:
        return ProvenanceContext(
            active=False,
            skip_reason="not inside a dispatch worktree with a known task record",
            tasks_dir=effective_tasks_dir,
        )

    if not known_agent:
        rec_path = locate_task_record(effective_tasks_dir, known_task_id)
        if rec_path is not None:
            try:
                data = json.loads(rec_path.read_text(encoding="utf-8"))
                known_agent = data.get("agent")
            except Exception:
                pass

    return ProvenanceContext(
        active=True,
        expected_task_id=known_task_id,
        expected_agent=known_agent,
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

    if provenance is None:
        provenance = resolve_provenance_context(cwd=cwd)

    if not provenance.active:
        return "PASS", trailer_str

    tasks_dir = provenance.tasks_dir or _default_tasks_dir()
    expected = (
        provenance.expected_trailer
        or f"X-Agent: {provenance.expected_agent or agent}/{provenance.expected_task_id or task}"
    )

    rec_path = locate_task_record(tasks_dir, task)
    if rec_path is None:
        return (
            "FAIL",
            f"task record {task!r} not found in {tasks_dir.name} (hot or archive); expected literal trailer: {expected!r}",
        )

    if provenance.expected_task_id and task != provenance.expected_task_id:
        return (
            "FAIL",
            f"trailer {trailer_str!r} names task {task!r} but dispatch worktree task is {provenance.expected_task_id!r}; expected literal trailer: {expected!r}",
        )

    if provenance.expected_agent:
        matched_agent = (agent == provenance.expected_agent) or (
            {agent, provenance.expected_agent} <= {"grok", "grok-build"}
        )
        if not matched_agent:
            return (
                "FAIL",
                f"trailer {trailer_str!r} names agent {agent!r} but dispatch worktree agent is {provenance.expected_agent!r}; expected literal trailer: {expected!r}",
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
