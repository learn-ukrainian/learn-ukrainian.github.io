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
import math
import re
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "scripts" / "config" / "issue_streams.yaml"
CACHE_PATH = ROOT / "batch_state" / "issue_stream_audit.json"
ISSUE_REF_RE = re.compile(r"#(\d{2,6})\b")

# ADR-011 P4 — private keys added to the cache report for the strict adoption
# gate/observability. They carry an exact effective issue→epic membership index
# and the bounded open-issue set; both are stripped from the public
# ``/api/issues/streams`` response (see ``issues_router.strip_private_index``).
PRIVATE_CACHE_KEYS = ("effective_membership", "open_issue_numbers")

# A resolver proving issue N is a live child of stream epic E, offline, from a
# fresh cache. Signature mirrors P1's ``check_research_registry.MembershipResolver``.
MembershipResolver = Callable[[int, int], bool]


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

    native_epics: dict[int, set[int]] = {}
    body_epics: dict[int, set[int]] = {}
    for epic, (native, refs) in membership.items():
        for n in native:
            native_epics.setdefault(n, set()).add(epic)
        for n in refs:
            body_epics.setdefault(n, set()).add(epic)
    native_linked = set(native_epics)
    # Native sub-issue links are DELIBERATE membership; body refs are the
    # migration fallback. Once an issue has any native link, prose mentions in
    # other epics' bodies must not multi-home it. Ambiguity is judged on the
    # EFFECTIVE EPIC set, not the distinct stream names it maps to — two native
    # epics in the SAME stream are still two owners and must be ambiguous, not
    # silently collapsed to "one stream, therefore fine" (codex/gemini review).
    owning_epics: dict[int, set[int]] = {
        n: (native_epics.get(n) or body_epics.get(n) or set())
        for n in set(native_epics) | set(body_epics)
    }

    open_numbers = {i["number"] for i in open_issues}
    titles = {i["number"]: i["title"] for i in open_issues}

    orphans = sorted(
        n for n in open_numbers if n not in epic_numbers and not owning_epics.get(n)
    )
    multi_homed = sorted(
        n for n in open_numbers
        if n not in epic_numbers and len(owning_epics.get(n, ())) > 1
    )
    body_only = sorted(
        n for n in open_numbers
        if n not in epic_numbers and owning_epics.get(n) and n not in native_linked
    )
    missing_epics = sorted(e for e in epic_numbers if e not in open_numbers)

    return {
        "generated_at": int(time.time()),
        "open_total": len(open_numbers),
        "streams": {k: sorted(v) for k, v in registry.items()},
        "orphans": [{"number": n, "title": titles[n]} for n in orphans],
        "multi_homed": [
            {
                "number": n,
                "title": titles[n],
                "streams": sorted({stream_of_epic[e] for e in owning_epics[n]}),
            }
            for n in multi_homed
        ],
        "pending_native_link": body_only,
        "closed_or_missing_epics": missing_epics,
        # The invariant is EXACTLY ONE EFFECTIVE EPIC — multi-homed violates it
        # (codex F1), including two epics that happen to share one stream.
        "ok": not orphans and not missing_epics and not multi_homed,
        # ADR-011 P4 private index (stripped from the public API): the exact
        # effective issue→epic membership, native winning over body refs, plus the
        # bounded open-issue set. Carries enough state to reject closed (absent
        # key), wrong (epic not in ``epics``), and ambiguous (``unique_stream``
        # false — more than one effective epic, even within one stream) ownership
        # without any live network call.
        "effective_membership": _effective_membership(
            open_numbers, epic_numbers, stream_of_epic, membership
        ),
        "open_issue_numbers": sorted(open_numbers),
    }


def _effective_membership(
    open_numbers: set[int],
    epic_numbers: set[int],
    stream_of_epic: dict[int, str],
    membership: dict[int, tuple[set[int], set[int]]],
) -> dict[str, dict]:
    """Exact effective issue→epic index. Native links win over body refs; epics
    and non-open issues are excluded. One entry per owned open issue.

    ``unique_stream`` means EXACT membership: exactly one effective epic — not
    merely one distinct stream *name*. Two epics that happen to live in the same
    stream are still two owners and must NOT resolve as unique (codex/gemini
    review on PR #4998): a resolver built from this index must fail closed for
    that case exactly as it does for a genuine cross-stream multi-home.
    """
    native_epics: dict[int, set[int]] = {}
    body_epics: dict[int, set[int]] = {}
    for epic, (native, refs) in membership.items():
        for n in native:
            native_epics.setdefault(n, set()).add(epic)
        for n in refs:
            body_epics.setdefault(n, set()).add(epic)
    index: dict[str, dict] = {}
    for n in sorted(set(native_epics) | set(body_epics)):
        if n in epic_numbers or n not in open_numbers:
            continue
        via = "native" if native_epics.get(n) else "body"
        epics = sorted(native_epics.get(n) or body_epics.get(n))
        streams = sorted({stream_of_epic[e] for e in epics})
        index[str(n)] = {
            "epics": epics,
            "streams": streams,
            "via": via,
            "unique_stream": len(epics) == 1,
        }
    return index


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


# --------------------------------------------------------------------------- #
# ADR-011 P4 — strict adoption gate inputs (fresh cache only; never network)
# --------------------------------------------------------------------------- #
# Cache authority window: a membership cache is trusted for at most
# ``max_age_s`` (default 3600s, matching the auditor's own session-setup
# refresh cadence) AFTER ``generated_at``, and rejected outright if
# ``generated_at`` is more than ``CACHE_FUTURE_SKEW_S`` ahead of wall-clock —
# clock skew or a corrupted/hand-edited timestamp must not be read as "still
# fresh forever" just because the age computes negative.
CACHE_FUTURE_SKEW_S = 300

_VALID_VIA = frozenset({"native", "body"})


def _is_positive_int(value: object) -> bool:
    """True for a JSON int that is a real positive integer — excludes bool
    (``isinstance(True, int)`` is True in Python) and any non-int type."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _valid_membership_entry(entry: object) -> bool:
    """Structurally + semantically validate one ``effective_membership`` entry.

    Every field is checked against the exact shape ``_effective_membership``
    produces: a non-empty list of positive-int epics, a list of non-empty
    stream-name strings, a known ``via``, and a ``unique_stream`` bool that is
    internally consistent with the epic count (exactly one effective epic —
    codex/gemini review). A cache that claims ``unique_stream: true`` for two
    epics (or vice versa) is corrupted/adversarial and must fail closed.
    """
    if not isinstance(entry, dict):
        return False
    epics = entry.get("epics")
    streams = entry.get("streams")
    via = entry.get("via")
    unique = entry.get("unique_stream")
    if not isinstance(epics, list) or not epics or not all(_is_positive_int(e) for e in epics):
        return False
    if not isinstance(streams, list) or not streams or not all(
        isinstance(s, str) and s for s in streams
    ):
        return False
    if via not in _VALID_VIA:
        return False
    if not isinstance(unique, bool):
        return False
    return unique == (len(epics) == 1)


def _valid_membership_index(index: object) -> bool:
    if not isinstance(index, dict):
        return False
    for key, entry in index.items():
        if not (isinstance(key, str) and key.isdigit() and int(key) > 0):
            return False
        if not _valid_membership_entry(entry):
            return False
    return True


def _valid_open_numbers(value: object) -> bool:
    return isinstance(value, list) and all(_is_positive_int(n) for n in value)


def read_membership_index(max_age_s: int, *, cache_path: Path | None = None) -> dict | None:
    """Return the effective issue→epic membership index from a FRESH cache.

    Fails **closed** to ``None`` — never raises, never returns a truthy-but-bogus
    value — when the cache is missing, unreadable, not a mapping, stale (older
    than ``max_age_s``), materially future-skewed (``generated_at`` more than
    ``CACHE_FUTURE_SKEW_S`` ahead of wall-clock, or non-finite/non-numeric/bool),
    was written by a pre-P4 auditor that lacks the index, or carries a
    structurally/semantically malformed ``effective_membership`` or
    ``open_issue_numbers`` (non-positive-int keys/values, unknown ``via``, a
    ``unique_stream`` bool inconsistent with its epic count, etc.). This never
    reaches GitHub: the strict adoption gate consumes a cache produced by a
    separate live auditor run, so discovery/gate paths stay offline and
    non-mutating.
    """
    path = cache_path if cache_path is not None else CACHE_PATH
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(report, dict):
        return None

    generated_at = report.get("generated_at")
    if isinstance(generated_at, bool) or not isinstance(generated_at, (int, float)):
        return None
    if not math.isfinite(generated_at):
        return None
    age = time.time() - generated_at
    if age > max_age_s or age < -CACHE_FUTURE_SKEW_S:
        return None

    index = report.get("effective_membership")
    if not _valid_membership_index(index):
        return None
    open_numbers = report.get("open_issue_numbers")
    if open_numbers is not None and not _valid_open_numbers(open_numbers):
        return None
    return report


def make_membership_resolver(report: dict) -> MembershipResolver:
    """Build a ``(issue, epic) → bool`` resolver over a fresh cache report.

    Returns ``True`` only when the issue is a live owned member (present in the
    index), belongs to exactly one EFFECTIVE EPIC (``unique_stream`` — exact
    membership, not merely one stream name), and the requested ``epic`` is one of
    its effective epics. Rejects closed/orphan (absent), wrong-epic, and
    ambiguous (more than one effective epic, even within a single stream)
    ownership — every failure mode fails closed.
    """
    index = report.get("effective_membership") or {}

    def _resolve(issue: int, epic: int) -> bool:
        entry = index.get(str(issue))
        if not isinstance(entry, dict) or not entry.get("unique_stream"):
            return False
        return int(epic) in (entry.get("epics") or [])

    return _resolve


def make_issue_resolver(report: dict) -> Callable[[str], bool]:
    """Build a consumer ``issue`` resolver.

    ``True`` only when the ref names an OPEN issue that is ALSO uniquely owned
    by exactly one effective epic/stream in the fresh membership index. Being in
    the bounded open-issue set alone is not enough — an unowned (orphaned) or
    ambiguously multi-homed open issue is not trustworthy "adopted" evidence
    (codex/gemini review on PR #4998: adopted issue consumers must be open *and*
    uniquely owned, the same proof the ownership gate itself uses). Non-digit
    refs fail closed.
    """
    open_set = {int(n) for n in (report.get("open_issue_numbers") or [])}
    index = report.get("effective_membership") or {}

    def _resolve(ref: str) -> bool:
        if not (ref.isdigit() and int(ref) in open_set):
            return False
        entry = index.get(ref)
        return isinstance(entry, dict) and bool(entry.get("unique_stream"))

    return _resolve


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
