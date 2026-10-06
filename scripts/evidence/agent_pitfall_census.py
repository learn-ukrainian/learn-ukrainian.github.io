#!/usr/bin/env python3
"""Count agent-repair signals in git history for the rearchitecture plan.

Use it to refresh the tables in docs/plans/agent-friendly-rearchitecture.md.
Do not use it as a fleet-speed benchmark or as proof that a red CI run was a
mistake: a failed gate is often the gate refusing a bad head.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Windows chosen from the measured X-Agent adoption curve in this script:
# from 2026-07 the trailer is present on the large majority of commits.
PRIMARY_SINCE = "2026-07-01"
PRIMARY_UNTIL = "2026-10-06"
SAMPLE_SINCE = "2026-09-30"
SAMPLE_UNTIL = "2026-10-06"
# Bounds are explicit UTC-midnight instants: git resolves a date-only bound with
# the current time of day in the host timezone, making earlier runs irreproducible.
WINDOW_UTC_OFFSET = "+00:00"

FIX_SCOPE = re.compile(r"^fix\(([^)]+)\)", re.I)
FIX_PREFIX = re.compile(r"^fix(\(|:)", re.I)
REVERT_PREFIX = re.compile(r"^revert(\(|:|\s)", re.I)
REVERT_WORD = re.compile(r"revert", re.I)

# Scope tokens naming an internal machine use a neutral label;
# digest keys keep the alias out of the repo.
SCOPE_LABELS = {
    "1f3114901bde88416893b1537d441fe77bcdb112fc436c9655846dfeab20a3ba": "internal-host",
}

# Subject regexes. A commit may match more than one. The match count is
# measured; calling the regex a single root cause is an inference the plan
# marks separately.
SUBJECT_CLASSES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "hook_guard",
        re.compile(r"redirect|bash-accurate|bypass|primary.checkout|quote-aware", re.I),
    ),
    (
        "removal_or_reap",
        re.compile(r"worktree remov|reap|keep_worktree|ignored output|preservation", re.I),
    ),
    (
        "routing_credit",
        re.compile(r"credit|pace deficit|near-cap|substitution|headroom", re.I),
    ),
    (
        "review_machinery",
        re.compile(r"verdict|authorship|sources tool|reviewer family|prompt", re.I),
    ),
    (
        "ci_selection",
        re.compile(r"merge queue|path filter|cheap-exit|CI Gate|shard|fastlane", re.I),
    ),
    (
        "test_isolation",
        re.compile(r"\bflake|isolate|xdist", re.I),
    ),
    (
        "opsec_path",
        re.compile(r"\bopsec\b|host path|absolute path|run-root", re.I),
    ),
    (
        "source_evidence",
        re.compile(r"VESUM|ULIF|source-bound|cited|gloss|\bstress\b", re.I),
    ),
    (
        "timeout_or_cache",
        re.compile(r"timeout|\bslow\b|\bcache\b|hydrat", re.I),
    ),
)


def _git(*args: str) -> str:
    env = os.environ.copy()
    env["TZ"] = "UTC"
    return subprocess.check_output(["git", *args], text=True, errors="replace", timeout=120, env=env)


def _window_instant(date: str) -> str:
    return f"{date}T00:00:00{WINDOW_UTC_OFFSET}"


def _commits(since: str, until: str) -> list[tuple[str, str, str, str]]:
    """Return (sha, date, subject, body) for non-merge commits in [since, until)."""
    raw = _git(
        "log",
        "--no-merges",
        f"--since={_window_instant(since)}",
        f"--until={_window_instant(until)}",
        "--format=%H%x1f%cI%x1f%s%x1f%b%x1e",
    )
    rows: list[tuple[str, str, str, str]] = []
    for chunk in raw.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        parts = chunk.split("\x1f", 3)
        if len(parts) < 4:
            continue
        rows.append((parts[0], parts[1], parts[2], parts[3]))
    return rows


def _path_buckets(since: str, until: str) -> dict[str, int]:
    raw = _git(
        "log",
        "--no-merges",
        f"--since={_window_instant(since)}",
        f"--until={_window_instant(until)}",
        "--pretty=format:%x1e%H%x1f%s",
        "--name-only",
    )
    counts: Counter[str] = Counter()

    def bucket(path: str) -> str | None:
        if path.startswith("scripts/lexicon/") or path.startswith("data/lexicon/"):
            return "lexicon"
        if path.startswith("site/") and re.search(r"atlas|word-card|wordcard", path, re.I):
            return "site_atlas"
        if path.startswith("site/") and re.search(r"practice", path, re.I):
            return "site_practice"
        if path.startswith("site/"):
            return "site_other"
        if path == ".github/workflows/ci.yml":
            return "ci_yml"
        if path.startswith(".github/workflows/"):
            return "workflows_other"
        if (
            path.startswith("scripts/delegate.py")
            or path.startswith("scripts/review/")
            or path.startswith("scripts/orchestration/")
            or path.startswith("scripts/fleet/")
            or path.startswith("scripts/agent_runtime/")
            or path.startswith("scripts/runtime/")
            or "/hooks/" in path
        ):
            return "delivery"
        if path.startswith("curriculum/"):
            return "curriculum"
        if path.startswith("tests/") or path.startswith("site/tests/"):
            return "tests"
        return None

    for chunk in raw.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        head = lines[0]
        if "\x1f" not in head:
            continue
        _sha, subject = head.split("\x1f", 1)
        if not FIX_PREFIX.match(subject):
            continue
        hit: set[str] = set()
        for line in lines[1:]:
            path = line.strip()
            if not path:
                continue
            name = bucket(path)
            if name:
                hit.add(name)
        if not hit:
            hit.add("no_listed_bucket")
        for name in hit:
            counts[name] += 1
    return dict(counts)


def _window(since: str, until: str) -> dict[str, object]:
    rows = _commits(since, until)
    scopes: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    fix_n = 0
    revert_prefix: list[dict[str, str]] = []
    revert_mention: list[dict[str, str]] = []
    missing_trailer = 0
    for sha, date, subject, body in rows:
        if "X-Agent:" not in body:
            missing_trailer += 1
        if FIX_PREFIX.match(subject):
            fix_n += 1
            match = FIX_SCOPE.match(subject)
            scope = match.group(1).lower() if match else "<no-scope>"
            scope = SCOPE_LABELS.get(hashlib.sha256(scope.encode()).hexdigest(), scope)
            scopes[scope] += 1
            for name, pattern in SUBJECT_CLASSES:
                if pattern.search(subject):
                    classes[name] += 1
        if REVERT_PREFIX.match(subject):
            revert_prefix.append({"sha": sha, "date": date[:10], "subject": subject})
        elif REVERT_WORD.search(subject):
            revert_mention.append({"sha": sha, "date": date[:10], "subject": subject})
    return {
        "since": since,
        "until_exclusive": until,
        "since_instant": _window_instant(since),
        "until_exclusive_instant": _window_instant(until),
        "non_merge_commits": len(rows),
        "fix_prefix_commits": fix_n,
        "missing_x_agent_trailer": missing_trailer,
        "fix_scopes": scopes.most_common(),
        "fix_subject_class_hits": classes.most_common(),
        "revert_prefix_commits": revert_prefix,
        "revert_mention_commits": revert_mention,
        "fix_path_buckets": _path_buckets(since, until),
    }


def _trailer_by_month() -> list[dict[str, int | str]]:
    raw = _git("log", "--no-merges", "--format=%cI%x1f%b%x1e")
    total: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    for chunk in raw.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk.strip() or "\x1f" not in chunk:
            continue
        date, body = chunk.split("\x1f", 1)
        month = date[:7]
        total[month] += 1
        if "X-Agent:" not in body:
            missing[month] += 1
    return [{"month": month, "non_merge": total[month], "missing_x_agent": missing[month]} for month in sorted(total)]


def _structure(root: Path) -> dict[str, object]:
    skip = {".venv", ".git", "node_modules", ".worktrees"}
    defs_remove: list[str] = []
    defs_raw: list[str] = []
    calls_raw_prod: list[str] = []
    calls_raw_tests: list[str] = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if any(part in skip for part in Path(rel).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        in_tests = rel.startswith("tests/") or "/tests/" in rel
        for lineno, line in enumerate(text.splitlines(), 1):
            loc = f"{rel}:{lineno}"
            stripped = line.lstrip()
            if stripped.startswith("def remove_unclaimed_worktree"):
                defs_remove.append(loc)
            if stripped.startswith("def git_worktree_remove"):
                defs_raw.append(loc)
            if "git_worktree_remove(" in line and "def git_worktree_remove" not in line:
                if in_tests:
                    calls_raw_tests.append(loc)
                else:
                    calls_raw_prod.append(loc)
    return {
        "remove_unclaimed_worktree_definitions": defs_remove,
        "git_worktree_remove_definitions": defs_raw,
        "git_worktree_remove_production_calls": calls_raw_prod,
        "git_worktree_remove_test_calls": len(calls_raw_tests),
    }


def build_report(root: Path) -> dict[str, object]:
    head = _git("rev-parse", "HEAD").strip()
    return {
        "head": head,
        "timezone": "UTC",
        "method": (
            "Non-merge git history with explicit UTC-midnight window bounds and TZ=UTC for git. "
            "Monthly trailer figures use %cI and each commit's committer offset, independent of the host clock. "
            "fix() scope counts are the subject token with neutral internal-machine labels. "
            "Subject-class hits are regex matches and are not mutually exclusive. "
            "Path buckets count fix commits that touch at least one matching path. "
            "Structure lines are a source scan of this checkout."
        ),
        "x_agent_by_month": _trailer_by_month(),
        "primary_window": _window(PRIMARY_SINCE, PRIMARY_UNTIL),
        "approved_plan_sample_window": _window(SAMPLE_SINCE, SAMPLE_UNTIL),
        "structure_on_head": _structure(root),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count fix-commit scopes, path buckets, reverts, X-Agent trailers, "
            "and worktree-removal definitions.\n"
            "Use for the agent-friendly rearchitecture plan. Do not use the "
            "counts as a delivery-speed claim or as a judgement that every "
            "failed CI run was an agent mistake."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/evidence/agent_pitfall_census.py\n"
            "  .venv/bin/python scripts/evidence/agent_pitfall_census.py --pretty\n"
            "\n"
            "Outputs: JSON on stdout. Writes nothing.\n"
            "Exit codes: 0 on success, 1 if git fails or times out.\n"
            "Related: docs/plans/agent-friendly-rearchitecture.md, "
            "docs/plans/agent-friendly-delivery.md, epic #9737.\n"
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Indent the JSON. Default is compact JSON.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to scan for removal definitions. Default: .",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = build_report(root)
    # Never emit an absolute path. Structure locations are repo-relative.
    encoded = json.dumps(report, indent=2 if args.pretty else None, sort_keys=True)
    if "/home/" in encoded or "/Users/" in encoded or "file://" in encoded:
        print("census refused: output contained a host path", file=sys.stderr)
        return 1
    print(encoded)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"git failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
