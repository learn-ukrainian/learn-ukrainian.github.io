"""Issue-stream auditor — every open GH issue must belong to exactly one stream epic.

Registry: scripts/config/issue_streams.yaml (streams → epic issue numbers).
Membership: native GitHub sub-issue of a stream epic, OR (fallback while the
native migration is pending) a ``#N`` reference in a stream epic's body.

Usage:
  .venv/bin/python -m scripts.orchestration.issue_stream_audit           # human summary
  .venv/bin/python -m scripts.orchestration.issue_stream_audit --json    # machine output
  .venv/bin/python -m scripts.orchestration.issue_stream_audit --check   # exit 1 on orphans
  .venv/bin/python -m scripts.orchestration.issue_stream_audit --from-cache --max-age 3600
  .venv/bin/python -m scripts.orchestration.issue_stream_audit --migrate # body refs → native sub-issues

Cache: batch_state/issue_stream_audit.json (gitignored runtime state) — written on
every live run; the session-setup hook and /api/state/issues-health read it.

GH incident #4708: manual epic checklists rot (fixed-but-open issues, auto-closed
issues orphaning scope). This gate makes drift visible at every cold start.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "scripts" / "config" / "issue_streams.yaml"
CACHE_PATH = ROOT / "batch_state" / "issue_stream_audit.json"
ISSUE_REF_RE = re.compile(r"#(\d{2,6})\b")


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, list[int]]:
    """Return {stream_key: [epic_numbers]}."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    streams = doc.get("streams") or {}
    registry: dict[str, list[int]] = {}
    for key, spec in streams.items():
        epics = [int(n) for n in (spec.get("epics") or [])]
        if not epics:
            raise ValueError(f"stream {key!r} has no epics")
        registry[key] = epics
    if not registry:
        raise ValueError("issue_streams.yaml defines no streams")
    return registry


def _gh_json(args: list[str], timeout_s: float = 30.0):
    proc = subprocess.run(
        ["gh", *args], capture_output=True, text=True, timeout=timeout_s, cwd=ROOT
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])}… failed: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def fetch_open_issues() -> list[dict]:
    return _gh_json(
        ["issue", "list", "--state", "open", "--limit", "500",
         "--json", "number,title"]
    )


_REPO_CACHE: dict[str, str] = {}


def _repo_owner_name() -> tuple[str, str]:
    """Resolve the actual owner/name once — GraphQL -f fields do NOT expand
    the gh {owner}/{repo} placeholders (REST paths do). Caught by live probe."""
    if not _REPO_CACHE:
        data = _gh_json(["repo", "view", "--json", "owner,name"])
        _REPO_CACHE["owner"] = data["owner"]["login"]
        _REPO_CACHE["name"] = data["name"]
    return _REPO_CACHE["owner"], _REPO_CACHE["name"]


def fetch_epic_membership(epic: int) -> tuple[set[int], set[int]]:
    """Return (native_sub_issue_numbers, body_reference_numbers) for one epic."""
    owner, name = _repo_owner_name()
    data = _gh_json([
        "api", "graphql",
        "-F", "number=" + str(epic),
        "-f", f"owner={owner}", "-f", f"name={name}",
        "-f",
        "query=query($owner:String!,$name:String!,$number:Int!){"
        "repository(owner:$owner,name:$name){issue(number:$number){body "
        "subIssues(first:100){nodes{number}}}}}",
    ])
    issue = (data.get("data") or {}).get("repository", {}).get("issue") or {}
    native = {n["number"] for n in (issue.get("subIssues") or {}).get("nodes") or []}
    body = issue.get("body") or ""
    refs = {int(m) for m in ISSUE_REF_RE.findall(body)}
    return native, refs


def classify(
    open_issues: list[dict],
    registry: dict[str, list[int]],
    membership: dict[int, tuple[set[int], set[int]]],
) -> dict:
    """Pure classification — unit-testable without network."""
    epic_numbers = {e for epics in registry.values() for e in epics}
    stream_of_epic = {e: key for key, epics in registry.items() for e in epics}

    native_streams: dict[int, set[str]] = {}
    body_streams: dict[int, set[str]] = {}
    native_linked: set[int] = set()
    for epic, (native, refs) in membership.items():
        stream = stream_of_epic[epic]
        for n in native:
            native_streams.setdefault(n, set()).add(stream)
        for n in refs:
            body_streams.setdefault(n, set()).add(stream)
        native_linked |= native
    # Native sub-issue links are DELIBERATE membership; body refs are the
    # migration fallback. Once an issue has any native link, prose mentions in
    # other epics' bodies must not multi-home it.
    issue_streams: dict[int, set[str]] = {
        n: (native_streams.get(n) or body_streams.get(n) or set())
        for n in set(native_streams) | set(body_streams)
    }

    open_numbers = {i["number"] for i in open_issues}
    titles = {i["number"]: i["title"] for i in open_issues}

    orphans = sorted(
        n for n in open_numbers if n not in epic_numbers and not issue_streams.get(n)
    )
    multi_homed = sorted(
        n for n in open_numbers
        if n not in epic_numbers and len(issue_streams.get(n, ())) > 1
    )
    body_only = sorted(
        n for n in open_numbers
        if n not in epic_numbers and issue_streams.get(n) and n not in native_linked
    )
    missing_epics = sorted(e for e in epic_numbers if e not in open_numbers)

    return {
        "generated_at": int(time.time()),
        "open_total": len(open_numbers),
        "streams": {k: sorted(v) for k, v in registry.items()},
        "orphans": [{"number": n, "title": titles[n]} for n in orphans],
        "multi_homed": [
            {"number": n, "title": titles[n], "streams": sorted(issue_streams[n])}
            for n in multi_homed
        ],
        "pending_native_link": body_only,
        "closed_or_missing_epics": missing_epics,
        # The invariant is EXACTLY ONE stream — multi-homed violates it (codex F1).
        "ok": not orphans and not missing_epics and not multi_homed,
    }


def run_audit() -> dict:
    registry = load_registry()
    open_issues = fetch_open_issues()
    membership = {
        epic: fetch_epic_membership(epic)
        for epics in registry.values()
        for epic in epics
    }
    report = classify(open_issues, registry, membership)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


def read_cache(max_age_s: int) -> dict | None:
    try:
        report = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if time.time() - report.get("generated_at", 0) > max_age_s:
        return None
    return report


def _node_id(number: int) -> str:
    data = _gh_json([
        "api", f"repos/{{owner}}/{{repo}}/issues/{number}", "--jq", "{node_id}"
    ])
    return data["node_id"]


def migrate(report: dict) -> int:
    """Create native sub-issue links for pending body-only references.

    Ambiguous cases — body-referenced from MORE THAN ONE stream — are skipped
    (codex F2): GitHub's single-parent constraint would otherwise make the
    winner order-dependent instead of deliberate. Resolve them manually.
    """
    registry = load_registry()
    ambiguous = {m["number"] for m in report.get("multi_homed", [])}
    if ambiguous:
        print(
            "skipping ambiguous multi-homed (resolve manually): "
            + ", ".join(f"#{n}" for n in sorted(ambiguous)),
            file=sys.stderr,
        )
    created = 0
    for stream_key, epics in registry.items():
        for epic in epics:
            native, refs = fetch_epic_membership(epic)
            pending = sorted(
                refs - native - ambiguous
                - {e for es in registry.values() for e in es}
            )
            if not pending:
                continue
            epic_node = _node_id(epic)
            for n in pending:
                if n not in {x if isinstance(x, int) else x["number"]
                             for x in report.get("pending_native_link", [])}:
                    continue
                try:
                    child_node = _node_id(n)
                    _gh_json([
                        "api", "graphql",
                        "-f",
                        "query=mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,"
                        "subIssueId:$c}){issue{number}}}",
                        "-f", f"p={epic_node}", "-f", f"c={child_node}",
                    ])
                    created += 1
                    print(f"linked #{n} → epic #{epic} ({stream_key})")
                except RuntimeError as exc:
                    print(f"WARN: link #{n} → #{epic} failed: {exc}", file=sys.stderr)
    return created


def human_summary(report: dict) -> str:
    lines = [
        f"open issues: {report['open_total']} · streams: {len(report['streams'])}"
        f" · ok: {report['ok']}"
    ]
    if report["orphans"]:
        lines.append(f"ORPHANS ({len(report['orphans'])} — no stream epic):")
        lines += [f"  #{o['number']} {o['title'][:80]}" for o in report["orphans"]]
    if report["multi_homed"]:
        lines.append(f"multi-homed ({len(report['multi_homed'])}):")
        lines += [
            f"  #{m['number']} in {', '.join(m['streams'])}" for m in report["multi_homed"]
        ]
    if report["pending_native_link"]:
        lines.append(
            f"pending native sub-issue link: {len(report['pending_native_link'])}"
            " (run --migrate)"
        )
    if report["closed_or_missing_epics"]:
        lines.append(f"⚠️ stream epics not open: {report['closed_or_missing_epics']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true", help="exit 1 unless ok")
    parser.add_argument("--from-cache", action="store_true")
    parser.add_argument("--max-age", type=int, default=3600)
    parser.add_argument("--migrate", action="store_true")
    args = parser.parse_args(argv)

    report = read_cache(args.max_age) if args.from_cache else None
    if report is None:
        if args.from_cache and args.check:
            # Hook path: never block a session start on the network.
            print("issue-stream audit: no fresh cache (run the auditor to refresh)")
            return 0
        report = run_audit()

    if args.migrate:
        created = migrate(report)
        print(f"created {created} native sub-issue link(s)")
        report = run_audit()

    print(json.dumps(report, ensure_ascii=False, indent=1) if args.json
          else human_summary(report))
    return 0 if (report["ok"] or not args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
