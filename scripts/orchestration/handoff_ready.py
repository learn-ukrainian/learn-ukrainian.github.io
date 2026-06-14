"""handoff_ready — machine-checked handoff-readiness predicate (#3138).

The 2026-06-14 failure mode: a driver *asserted* "ready for handoff" while CI was
red and a PR was unmerged. "Ready" was narrative, not verified. This script makes
readiness a deterministic predicate a driver runs (never asserts):

  1. tree clean        — the repo working tree has no uncommitted changes
  2. no in-flight       — /api/delegate/active reports 0 running dispatches
  3. branch pushed      — local branch tip == origin branch tip (nothing unpushed)
  4. pr checks green    — every BLOCKING status check on the PR is green
  5. handoff bundled    — the driver handoff is part of the PR diff (state reaches
                          main via review, not a stale origin/main RESUME-HERE)

Any check that is RED *or* UNKNOWN ⇒ NOT READY. Unknown counts as not-ready on
purpose: you cannot assert readiness on a check you could not run (anti-fabrication,
mirrors MEMORY.md #M-4). Exit 0 iff READY.

Usage:
    python -m scripts.orchestration.handoff_ready --pr 3140
    python -m scripts.orchestration.handoff_ready --branch claude/folk-x --handoff docs/folk-epic/CLAUDE-DRIVER-HANDOFF.md
"""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HANDOFF = "docs/folk-epic/CLAUDE-DRIVER-HANDOFF.md"
DELEGATE_ACTIVE_URL = "http://127.0.0.1:8765/api/delegate/active"

OK, RED, UNKNOWN = "ok", "red", "unknown"


def _git(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _gh_json(*args: str) -> tuple[int, object]:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, cwd=PROJECT_ROOT)
    if proc.returncode != 0:
        return proc.returncode, proc.stderr.strip()
    try:
        return 0, json.loads(proc.stdout or "null")
    except json.JSONDecodeError:
        return 1, proc.stdout.strip()


def check_tree_clean() -> tuple[str, str]:
    rc, out = _git("status", "--porcelain")
    if rc != 0:
        return UNKNOWN, f"git status failed: {out[:120]}"
    if out:
        n = len(out.splitlines())
        return RED, f"{n} uncommitted change(s) in the working tree"
    return OK, "working tree clean"


def check_no_inflight() -> tuple[str, str]:
    try:
        with urllib.request.urlopen(DELEGATE_ACTIVE_URL, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return UNKNOWN, f"delegate API unreachable: {exc!r}"
    total = int(data.get("total", 0))
    if total:
        ids = ", ".join(t.get("task_id", "?") for t in data.get("tasks", [])[:5])
        return RED, f"{total} dispatch(es) in flight: {ids}"
    return OK, "0 dispatches in flight"


def check_branch_pushed(branch: str) -> tuple[str, str]:
    rc_local, local = _git("rev-parse", branch)
    if rc_local != 0:
        return UNKNOWN, f"no local branch {branch}"
    rc_remote, remote = _git("ls-remote", "origin", branch)
    if rc_remote != 0:
        return UNKNOWN, f"git ls-remote failed: {remote[:120]}"
    if not remote:
        return RED, f"{branch} not pushed to origin"
    remote_sha = remote.split()[0]
    if remote_sha != local:
        return RED, f"local {local[:9]} != origin {remote_sha[:9]} (unpushed commits)"
    return OK, f"{branch} pushed (local==origin @ {local[:9]})"


def _blocking_state(pr: int) -> tuple[str, str]:
    rc, data = _gh_json(
        "pr", "view", str(pr), "--json", "statusCheckRollup,mergeStateStatus,state"
    )
    if rc != 0 or not isinstance(data, dict):
        return UNKNOWN, f"gh pr view failed: {str(data)[:120]}"
    if data.get("state") == "MERGED":
        return OK, "PR already merged"
    rollup = data.get("statusCheckRollup") or []
    if not rollup:
        # No checks at all ⇒ cannot confirm green. UNKNOWN ⇒ not ready (never
        # report "all 0 checks green" as READY — anti-fabrication, #M-4).
        return UNKNOWN, "no status checks found on the PR"
    failing = []
    pending = []
    for c in rollup:
        # Check-run vs status-context have different shapes; normalize.
        concl = (c.get("conclusion") or c.get("state") or "").upper()
        name = c.get("name") or c.get("context") or "check"
        if concl in ("SUCCESS", "NEUTRAL", "SKIPPED"):
            continue
        if concl in ("", "PENDING", "IN_PROGRESS", "QUEUED", "EXPECTED"):
            pending.append(name)
        else:
            failing.append(f"{name}={concl}")
    if failing:
        return RED, f"failing checks: {', '.join(failing[:6])}"
    if pending:
        return RED, f"checks still pending: {', '.join(pending[:6])}"
    # Checks green is necessary but not sufficient — enforce the merge state too:
    # a PR can be all-green yet BLOCKED (required review), DIRTY (conflict), or
    # BEHIND (needs update from base) and is NOT ready to hand off.
    merge_state = (data.get("mergeStateStatus") or "").upper()
    if merge_state in ("BLOCKED", "DIRTY", "BEHIND"):
        return RED, f"checks green but mergeStateStatus={merge_state} (not mergeable)"
    return OK, f"all {len(rollup)} checks green ({merge_state or '?'})"


def check_pr_checks(pr: int | None) -> tuple[str, str]:
    if pr is None:
        return UNKNOWN, "no PR number provided/discovered"
    return _blocking_state(pr)


def check_handoff_bundled(branch: str, handoff: str) -> tuple[str, str]:
    rc, out = _git("diff", "--name-only", f"origin/main...{branch}")
    if rc != 0:
        return UNKNOWN, f"git diff failed: {out[:120]}"
    files = set(out.splitlines())
    if handoff in files:
        return OK, f"{handoff} is in the PR diff"
    return RED, f"{handoff} NOT in the PR diff — refreshed state won't reach main"


def _discover_pr(branch: str) -> int | None:
    rc, data = _gh_json("pr", "list", "--head", branch, "--state", "open", "--json", "number")
    if rc == 0 and isinstance(data, list) and data:
        return int(data[0]["number"])
    return None


def evaluate(branch: str, pr: int | None, handoff: str) -> dict:
    if pr is None:
        pr = _discover_pr(branch)
    checks = {
        "tree_clean": check_tree_clean(),
        "no_inflight": check_no_inflight(),
        "branch_pushed": check_branch_pushed(branch),
        "pr_checks_green": check_pr_checks(pr),
        "handoff_bundled": check_handoff_bundled(branch, handoff),
    }
    ready = all(status == OK for status, _ in checks.values())
    return {"branch": branch, "pr": pr, "ready": ready, "checks": checks}


def _print_human(report: dict) -> None:
    icon = {OK: "✅", RED: "❌", UNKNOWN: "❔"}
    print(f"\n  handoff_ready: branch={report['branch']} pr={report['pr']}\n")
    for name, (status, detail) in report["checks"].items():
        print(f"   {icon[status]} {name:<18} {detail}")
    print()
    if report["ready"]:
        print("  ✅ READY for handoff (all predicates green).")
    else:
        print("  ❌ NOT READY — resolve the ❌/❔ checks. Do NOT declare ready.")
    print()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Machine-checked handoff-readiness predicate (#3138)")
    ap.add_argument("--branch", default=None, help="branch to check (default: current HEAD)")
    ap.add_argument("--pr", type=int, default=None, help="PR number (default: discover via gh)")
    ap.add_argument("--handoff", default=DEFAULT_HANDOFF, help="driver handoff path that must be bundled")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    branch = args.branch
    if branch is None:
        rc, out = _git("rev-parse", "--abbrev-ref", "HEAD")
        branch = out if rc == 0 else "HEAD"

    report = evaluate(branch, args.pr, args.handoff)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_human(report)
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
