#!/usr/bin/env python3
"""Advisory task-quality checker for GitHub issue / brief bodies (#7854).

Fail-open by default: prints PASS or WARN and exits 0. Use --strict to exit 1
on WARN. Does not invent a control plane; nests under docs/best-practices/task-quality.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common import github_client
from scripts.common.repo_root import main_checkout_root
from scripts.orchestration import fleet_repos, postmerge_criteria
from scripts.orchestration import issue_stream_audit as audit
from scripts.orchestration import task_lifecycle as lifecycle
from scripts.publish.github import read

ROOT = Path(__file__).resolve().parents[2]
MAX_AGE_S = 3600
MEMBERSHIP_CACHE_SCHEMA_VERSION = 1
# delegate.py gives --issue --strict 135 seconds: 60 for the issue, 60 for
# membership (cache validation and any live audit included), 15 for overhead.
NON_OVERRIDABLE = frozenset({"dod_structure_malformed", "membership_conflicting_ancestry"})


class _DeadlineExpired(BaseException):
    """Escape the auditor's retry handlers, then translate at the I/O boundary."""


@dataclass
class MembershipProgress:
    stage: str = "registry"


def error(section: str, field: str, code: str, message: str) -> dict:
    return {"section": section, "field": field, "code": code, "message": message}


def section(status: str, errors: list[dict] | None = None, **details) -> dict:
    return {"status": status, "errors": errors or [], **details}


def membership_error(code: str, message: str | None = None) -> dict:
    return section("WARN", [error("membership", "ancestry", code, message or code.replace("_", " "))])


@contextmanager
def time_budget(seconds: float = 60):
    """Bound issue fetching or membership observation, including audit retries."""

    def expired(_signum, _frame):
        raise _DeadlineExpired

    old_handler = signal.signal(signal.SIGALRM, expired)
    old_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    except _DeadlineExpired:
        raise TimeoutError("issue quality deadline") from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, *old_timer)
        signal.signal(signal.SIGALRM, old_handler)


def registry_for(repository: str) -> dict[str, list[int]] | None:
    """Only the public monorepo owns this registry; numbers are repository scoped."""
    for repo in fleet_repos.load_fleet_repos().values():
        if repo.github.casefold() == repository.casefold() and repo.role == "public-monorepo":
            try:
                return audit.load_registry(ROOT / "scripts/config/issue_streams.yaml", audit_only=True)
            except FileNotFoundError:
                return {}
    return None


def registry_absence(repository: str) -> dict:
    known = any(r.github.casefold() == repository.casefold() for r in fleet_repos.load_fleet_repos().values())
    if known:
        return section("membership_not_applicable")
    return membership_error("membership_registry_absent")


def live_audit(
    repository: str, registry: dict, *, root: Path = ROOT, progress: MembershipProgress | None = None
) -> dict:
    """Compose the existing live auditor in memory. Never write its shared cache."""
    progress = progress or MembershipProgress()
    progress.stage = "live_audit_repository"
    observed_repository = "/".join(audit._repo_owner_name(root))
    if observed_repository.casefold() != repository.casefold():
        raise ValueError("audit repository does not match target")
    progress.stage = "live_audit_open_issues"
    issues = audit.fetch_open_issues(root)
    warnings: list[dict] = []
    roots = {n for ns in registry.values() for n in ns}
    root_positions = {n: i for i, n in enumerate(sorted(roots), 1)}
    branch_positions = dict(root_positions)
    retry_budget = audit._RetryBudget()

    def fetch_batch(cursors):
        pages = {}
        for number, cursor in cursors.items():
            position = branch_positions[number]
            progress.stage = f"live_audit_root_{position}_of_{len(roots)}_issue_{number}"
            page = audit._fetch_subissue_batch({number: cursor}, root, roots, retry_budget)
            pages.update(page)
            node = page.get(number)
            if isinstance(node, dict):
                for child in (node.get("subIssues") or {}).get("nodes") or ():
                    if not isinstance(child, dict) or type(child.get("number")) is not int:
                        continue
                    child_repo = (child.get("repository") or {}).get("nameWithOwner")
                    if isinstance(child_repo, str) and child_repo.casefold() != repository.casefold():
                        continue
                    branch_positions.setdefault(child["number"], position)
        return pages

    # Keep the auditor's shared forest traversal and completeness semantics.
    # Split transport batches so a timeout identifies the root and exact call.
    membership = audit._tree_membership(roots, fetch_batch, warnings, repo_slug=repository)
    progress.stage = "live_audit_classification"
    report = audit.classify(issues, registry, membership, incomplete_nodes=audit._unread_warning_nodes(warnings))
    report.update(repository=observed_repository, warnings=warnings)
    if len(issues) >= 500:
        report["membership_complete"] = False
    return report


def read_parent(repository: str, number: int) -> dict | None:
    proc = read("issue-parent", repo=repository, number=number, capture_output=True, text=True, timeout=30)
    if proc.returncode:
        raise RuntimeError("parent read failed")
    doc = json.loads(proc.stdout)
    repo = (doc.get("data") or {}).get("repository")
    if (
        doc.get("errors")
        or not isinstance(repo, dict)
        or str(repo.get("nameWithOwner", "")).casefold() != repository.casefold()
    ):
        raise ValueError("parent repository unread")
    issue = repo.get("issue")
    if (
        not isinstance(issue, dict)
        or type(issue.get("number")) is not int
        or issue["number"] != number
        or "parent" not in issue
    ):
        raise ValueError("parent issue unread")
    parent = issue["parent"]
    if parent is None:
        return None
    if not isinstance(parent, dict):
        raise ValueError("parent malformed")
    slug = (parent.get("repository") or {}).get("nameWithOwner")
    if not lifecycle.repository_identity_valid(slug) or type(parent.get("number")) is not int or parent["number"] < 1:
        raise ValueError("parent identity malformed")
    return {"number": parent["number"], "repository": slug}


def _claim(issue: dict, roots: list[int], index: dict, parents: dict) -> int | None:
    """Resolve the documented title/body claim independently of the observed root."""
    candidates = re.findall(r"\[(\d+)\]", issue.get("title") or "")
    candidates += re.findall(r"(?im)^Parent:\s*#(\d+)\b", issue.get("body") or "")
    for candidate in candidates:
        number = int(candidate)
        visited = set()
        for _ in range(8):
            if number in roots:
                return number
            entry = index.get(str(number), {})
            if entry.get("unique_stream") is True and len(entry.get("epics", [])) == 1:
                return entry["epics"][0]
            if number in visited or not parents.get(number):
                break
            visited.add(number)
            parent = parents[number]
            number = parent.get("number")
    return None


def _audit_refusal(report: dict, repository: str, registry: dict) -> dict | None:
    if not audit.membership_report_is_complete(report):
        return membership_error("membership_audit_incomplete")
    if audit.validate_membership_report(report, MAX_AGE_S) is None:
        return membership_error("membership_audit_stale")
    observed_repository = report.get("repository")
    if not isinstance(observed_repository, str) or observed_repository.casefold() != repository.casefold():
        return membership_error("membership_audit_repository_mismatch")
    if report.get("streams") != {k: sorted(v) for k, v in registry.items()}:
        return membership_error("membership_audit_registry_mismatch")
    if "schema_version" in report and (
        type(report["schema_version"]) is not int or report["schema_version"] != MEMBERSHIP_CACHE_SCHEMA_VERSION
    ):
        return membership_error("membership_audit_cache_schema")
    if "schema_version" in report and (
        (results := _membership_root_results(report, registry)) is None or report.get("root_results") != results
    ):
        return membership_error("membership_audit_cache_schema")
    return None


def _membership_root_results(report: dict, registry: dict) -> dict | None:
    """Group the validated effective index by root, refusing conflicting owners."""
    roots = {n for ns in registry.values() for n in ns}
    if any(
        w["code"] == "unresolved_subissue"
        and (not audit._is_positive_int(w.get("issue")) or w["issue"] in roots)
        for w in report.get("warnings") or ()
    ):
        return None
    numbers = report.get("open_issue_numbers")
    if (
        not isinstance(numbers, list)
        or len(numbers) >= 500
        or len(set(numbers)) != len(numbers)
        or type(report.get("open_total")) is not int
        or report.get("open_total") != len(numbers)
        or report.get("multi_homed") != []
    ):
        return None
    root_results = {str(n): {"native": [], "body": []} for n in sorted(roots)}
    stream_of = {n: key for key, ns in registry.items() for n in ns}
    for number, entry in report["effective_membership"].items():
        if entry["unique_stream"] is not True or entry["epics"][0] not in roots:
            return None
        epic = entry["epics"][0]
        if entry["streams"] != [stream_of[epic]]:
            return None
        root_results[str(epic)][entry["via"]].append(int(number))
    for result in root_results.values():
        for members in result.values():
            members.sort()
    return root_results


def write_membership_cache(report: dict, repository: str, registry: dict, *, root: Path | None = None) -> bool:
    """Publish only fresh, complete, conflict-free evidence beside the shared cache.

    ``report`` is a membership audit from ``live_audit``. The Monitor serves this
    shared file as its hygiene report, so the writer appends the same closed-epic
    and milestone warnings ``run_audit`` adds; a failed lookup writes nothing.
    """
    if _audit_refusal(report, repository, registry):
        return False
    root_results = _membership_root_results(report, registry)
    if root_results is None:
        return False
    checkout = ROOT if root is None else root
    warnings = [*(report.get("warnings") or ()), *audit.hygiene_warnings(checkout, set(report["open_issue_numbers"]))]
    payload = json.dumps(
        {
            **report, "warnings": warnings,
            "schema_version": MEMBERSHIP_CACHE_SCHEMA_VERSION, "root_results": root_results,
        },
        ensure_ascii=False, sort_keys=True,
    ) + "\n"
    path = main_checkout_root(checkout) / "batch_state/issue_stream_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".issue-stream-audit-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return True


def evaluate_membership(
    issue: dict, repository: str, number: int, registry: dict, parents: dict, report: dict | None = None
) -> dict:
    """Pure evaluation of qualified observations using the canonical validator."""
    roots = [n for ns in registry.values() for n in ns]
    if number in roots:
        return section("root_exempt")
    if report is not None:
        refusal = _audit_refusal(report, repository, registry)
        if refusal:
            return refusal
    index = (report or {}).get("effective_membership", {})
    entry = index.get(str(number), {})
    if entry and entry.get("unique_stream") is not True:
        return membership_error("membership_conflicting_ancestry")
    claim = _claim(issue, roots, index, parents)
    if claim is not None and entry and entry.get("epics") != [claim]:
        return membership_error("membership_conflicting_ancestry")
    observed_root = next(
        (
            p["number"]
            for p in parents.values()
            if p and p.get("repository", "").casefold() == repository.casefold() and p.get("number") in roots
        ),
        None,
    )
    if claim is None:
        claim = observed_root or (entry.get("epics") or [None])[0]
    # A synthetic claim permits the canonical resolver to diagnose a cycle,
    # missing link or repository crossing even when no documentary claim exists.
    result = lifecycle.resolve_live_ancestry(
        repository=repository,
        issue_number=number,
        stream_epic=claim or roots[0],
        registered_epics=roots,
        read_parent=lambda _r, n: parents[n],
        membership_report=report,
    )
    if result["valid"]:
        return section("PASS", pending_native_link=result["method"] == "body")
    if (
        report is not None and parents.get(number) is None and not entry
        and number in report.get("open_issue_numbers", [])
        and not any(w["code"] == "unresolved_subissue" for w in report.get("warnings") or ())
    ):
        return membership_error(
            "membership_unregistered_parentless",
            f"Issue #{number} has no native parent and no registered stream membership. "
            f"Register #{number} as a native sub-issue of one registered stream root or its overflow container; "
            f"if the native link is at capacity, add '- [ ] #{number}' to exactly one registered root's body "
            "and refresh the membership audit.",
        )
    reason = result["reason"]
    if any(s in reason for s in ("cyclic", "crosses a repository", "different registered", "multi-homed")):
        code = "membership_conflicting_ancestry"
    elif parents.get(number) is None and not entry:
        code = "membership_missing_parent"
    else:
        code = "membership_unknown"
    return membership_error(code)


def cached_membership(issue: dict, repository: str, number: int, registry: dict, parents: dict) -> dict:
    """Read shared audit evidence, then apply the canonical validator and resolver."""
    path = main_checkout_root(ROOT) / "batch_state" / "issue_stream_audit.json"
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return membership_error("membership_audit_cache_missing")
    except (OSError, ValueError):
        return membership_error("membership_audit_cache_unreadable")
    return evaluate_membership(issue, repository, number, registry, parents, report)


def observe_membership(issue: dict, repository: str, number: int, *, audit_orphans: bool = True) -> dict:
    """Walk native ancestry; qualify cached or bounded live evidence for orphans."""
    progress = MembershipProgress()
    cache_rejection = None
    try:
        registry = registry_for(repository)
        if registry is None:
            return registry_absence(repository)
        if not registry:
            return membership_error("membership_registry_absent")
        roots = {n for ns in registry.values() for n in ns}
        if number in roots:
            return section("root_exempt")
        parents: dict = {}
        current = number
        for _ in range(8):
            progress.stage = f"parent_{current}"
            parent = read_parent(repository, current)
            parents[current] = parent
            if (
                parent is None
                or parent.get("repository", "").casefold() != repository.casefold()
                or parent.get("number") in roots
                or parent.get("number") in parents
            ):
                break
            if type(parent.get("number")) is not int:
                raise ValueError("malformed parent")
            current = parent["number"]
        report = None
        if audit_orphans and parents.get(number) is None:
            progress.stage = "cached_audit_validation"
            cached = cached_membership(issue, repository, number, registry, parents)
            if cached["status"] == "PASS" or cached["errors"][0]["code"] == "membership_unregistered_parentless":
                return cached
            cache_rejection = cached["errors"][0]["code"]
            progress.stage = "live_audit"
            report = live_audit(repository, registry, progress=progress)
        result = evaluate_membership(issue, repository, number, registry, parents, report)
        if report is not None and (
            result["status"] == "PASS" or result["errors"][0]["code"] == "membership_unregistered_parentless"
        ):
            progress.stage = "live_audit_cache_write"
            # The verdict is final. Publication, including its milestone lookups,
            # is best effort: no deadline or failure there may change the verdict.
            try:
                write_membership_cache(report, repository, registry)
            except (_DeadlineExpired, TimeoutError, subprocess.TimeoutExpired):
                result["cache_write_error"] = "membership_audit_cache_write_timeout"
            except Exception:
                result["cache_write_error"] = "membership_audit_cache_write_failed"
    except (_DeadlineExpired, TimeoutError, subprocess.TimeoutExpired):
        code = "membership_timeout" if progress.stage.startswith("parent_") else f"membership_timeout_{progress.stage}"
        result = membership_error(code)
    except github_client.GitHubRateLimited:
        result = membership_error("membership_rate_limited")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
        result = membership_error("membership_unknown")
    if cache_rejection and result["status"] != "PASS":
        result["cache_rejection"] = cache_rejection
    return result


HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
PLACEHOLDER_RE = re.compile(r"(?i)^(?:todo|tbd|n/?a|…|\.\.\.|\[.*\]|<.*>|criterion \d+|path/to/)\s*$")
EXPLICIT_NONE_RE = re.compile(r"(?i)^(?:none|n/?a|na)\s*(?:[—\-].*)?$")
TERMINAL_GOALS = ("merge", "deploy", "certify", "decision-only", "audit-only")


@dataclass(frozen=True)
class FieldCheck:
    key: str
    label: str
    heading: re.Pattern[str]


# Locate sections by heading; values must be substantive (not empty/placeholder).
FIELDS: tuple[FieldCheck, ...] = (
    FieldCheck(
        "outcome",
        "user-visible outcome / what",
        re.compile(
            r"(?im)^#{1,3}\s*(?:user[- ]visible\s+outcome|outcome|overview|problem(?:\s+statement)?)\s*$"
            r"|^\*\*what\*\*\s*:"
        ),
    ),
    FieldCheck(
        "why",
        "why / evidence",
        re.compile(r"(?im)^#{1,3}\s*(?:why(?:\s*/\s*evidence)?|evidence|repro)\s*$"),
    ),
    FieldCheck(
        "in_scope",
        "in scope / paths",
        re.compile(r"(?im)^#{1,3}\s*(?:in\s+scope|scope|affected)\s*$"),
    ),
    FieldCheck(
        "non_goals",
        "non-goals / out of scope",
        re.compile(r"(?im)^#{1,3}\s*(?:non[- ]goals?|out of scope)\s*$"),
    ),
    FieldCheck(
        "denominator",
        "denominator / scope size",
        re.compile(r"(?im)^#{1,3}\s*(?:denominator)\s*$"),
    ),
    FieldCheck(
        "verify",
        "verify commands / held-out check",
        re.compile(r"(?im)^#{1,3}\s*(?:verify|verification|test plan)\s*$"),
    ),
    FieldCheck(
        "deps",
        "dependencies (or explicit none)",
        re.compile(r"(?im)^#{1,3}\s*(?:deps|dependencies|blockers)\s*$"),
    ),
    FieldCheck(
        "dod",
        "definition of done / acceptance criteria",
        re.compile(
            r"(?im)^#{1,3}\s*(?:definition of done|acceptance criteria(?:\s*/\s*definition of done)?|done)\s*$"
            r"|^\s*-\s*\[\s*[xX ]\s*\]\s*AC-\d+"
        ),
    ),
    FieldCheck(
        "terminal_goal",
        "terminal goal (merge|deploy|certify|decision-only|audit-only)",
        re.compile(r"(?im)^#{1,3}\s*(?:terminal goal)\s*$"),
    ),
    FieldCheck(
        "accountable_driver",
        "accountable driver",
        re.compile(r"(?im)^#{1,3}\s*(?:accountable\s+driver|driver)\s*$"),
    ),
    FieldCheck(
        "stop_policy",
        "stop policy",
        re.compile(r"(?im)^#{1,3}\s*(?:stop\s+policy|stop)\s*$"),
    ),
    FieldCheck(
        "residual",
        "residual policy / leftover owner",
        re.compile(r"(?im)^#{1,3}\s*(?:residual(?:\s+policy)?|leftovers?)\s*$"),
    ),
    FieldCheck(
        "review_plan",
        "review plan (author family · outside-family reviewer · backup)",
        re.compile(r"(?im)^#{1,3}\s*(?:review\s+plan|cf\s+path|cross[- ]family\s+review)\s*$"),
    ),
)

TRIVIAL_RE = re.compile(
    r"(?im)^(?:\*\*)?(?:trivial|typo-only|single-line)(?:\*\*)?[ \t]*:[ \t]*(?:yes|true|exempt)\b"
    r"|^(?:trivial|typo-only)[ \t]+fix\b"
)
FIRST_LINE_TRIVIAL_RE = re.compile(r"(?i)trivial:[ \t]*(?:yes|true|exempt)?[ \t]*")
HEADING_LINE_RE = re.compile(r"(?m)^(#{1,6}\s+\S.*|\*\*[^*]+\*\*\s*:.*)$")


def issue_is_trivial(body: str, labels: list[dict[str, str]]) -> bool:
    first_line = (body or "").split("\n", 1)[0].strip()
    return bool(FIRST_LINE_TRIVIAL_RE.fullmatch(first_line)) or any(
        label.get("name", "").casefold() == "trivial" for label in labels
    )


def _strip_noise(text: str) -> str:
    return HTML_COMMENT_RE.sub("", text or "")


def _section_body(text: str, heading: re.Pattern[str]) -> str | None:
    match = heading.search(text)
    if not match:
        return None
    rest = text[match.end() :]
    next_heading = HEADING_LINE_RE.search(rest)
    chunk = rest if next_heading is None else rest[: next_heading.start()]
    return chunk.strip()


def _substantive(chunk: str | None, *, allow_none: bool = False) -> bool:
    if chunk is None:
        return False
    lines = []
    for raw in chunk.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if re.match(r"^(```|~~~)", stripped):
            continue
        # Markdown headings / hash comments; keep "#1234" issue refs.
        if stripped.startswith("#") and not re.match(r"^#\d", stripped) and re.match(r"^#{1,6}(?:\s|$)", stripped):
            continue
        line = stripped.lstrip("-* ").strip()
        line = re.sub(r"^\[\s*[xX ]\s*\]\s*", "", line).strip()
        if not line or line in {"```", "~~~"}:
            continue
        # Bare fence language tags are not content.
        if re.fullmatch(r"[a-zA-Z0-9_+-]+", line) and re.match(r"^(```|~~~)", raw.strip()):
            continue
        if allow_none and EXPLICIT_NONE_RE.match(line):
            lines.append(line)
            continue
        if PLACEHOLDER_RE.match(line):
            continue
        lines.append(line)
    return bool(lines)


def _terminal_goal_ok(chunk: str | None) -> bool:
    if not chunk:
        return False
    lowered = chunk.lower()
    return any(re.search(rf"(?i)\b{re.escape(goal)}\b", lowered) for goal in TERMINAL_GOALS)


def score_body(body: str, *, trivial: bool = False) -> dict[str, object]:
    text = _strip_noise(body or "")
    if trivial or issue_is_trivial(body, []) or TRIVIAL_RE.search(text):
        return complete_result(
            {
                "verdict": "PASS",
                "trivial": True,
                "missing": [],
                "present": [f.key for f in FIELDS],
                "notes": ["trivial exemption — full card not required"],
            },
            body,
        )

    missing: list[str] = []
    present: list[str] = []
    for field in FIELDS:
        chunk = _section_body(text, field.heading)
        if field.key == "terminal_goal":
            ok = _terminal_goal_ok(chunk)
        else:
            ok = _substantive(chunk, allow_none=field.key in {"deps", "residual", "non_goals"})
        if ok:
            present.append(field.key)
        else:
            missing.append(field.key)

    verdict = "PASS" if not missing else "WARN"
    return complete_result(
        {
            "verdict": verdict,
            "trivial": False,
            "missing": missing,
            "present": present,
            "notes": [],
        },
        body,
    )


def complete_result(result: dict, body: str, membership: dict | None = None) -> dict:
    """Keep the legacy keys while adding independent, field-level sections."""
    result = dict(result)
    result["missing"] = list(result["missing"])
    result["dor"] = section(
        "PASS" if not result["missing"] else "WARN",
        [error("dor", key, key, "required task card field is absent or empty") for key in result["missing"]],
    )
    dod_errors = []
    try:
        criteria = lifecycle.parse_issue_acceptance_criteria(postmerge_criteria.visible_markdown(body))
        for item in criteria:
            if postmerge_criteria.POST_MERGE_RE.search(item["text"]):
                owner, due = postmerge_criteria.item_assignment(item["text"])
                if not owner or not due:
                    dod_errors.append(error(
                        "dod", item["id"], "post_merge_unowned",
                        "post-merge evidence requires owner: <recognized lane> and due: YYYY-MM-DD "
                        "on the same item line; due is the evidence collection and review deadline",
                    ))
    except lifecycle.LifecycleError as exc:
        code = (
            "dod_structure_absent"
            if str(exc) == "issue body has no stable-ID acceptance criteria"
            else "dod_structure_malformed"
        )
        if not result["trivial"] or code == "dod_structure_malformed":
            dod_errors.append(error("dod", "acceptance_criteria", code, str(exc)))
    result["dod"] = section("WARN" if dod_errors else "exempt" if result["trivial"] else "PASS", dod_errors)
    result["membership"] = membership or section("unchecked")
    # Trivial cards retain their admission exemption, but malformed structure
    # remains visible in the DoD section, comments, reports and CLI notes.
    if result["trivial"]:
        result["notes"] = [*result["notes"], *(e["code"] for e in dod_errors)]
        result["missing"].extend(e["code"] for e in dod_errors if e["code"] == "post_merge_unowned")
    for part in ([result["membership"]] if result["trivial"] else [result["dod"], result["membership"]]):
        result["missing"].extend(e["code"] for e in part["errors"])
    result["verdict"] = "WARN" if result["missing"] else "PASS"
    return result


def evaluate_issue(issue: dict, membership: dict) -> dict:
    body = issue.get("body") or ""
    result = score_body(body, trivial=issue_is_trivial(body, issue.get("labels") or []))
    result["membership"] = membership
    result["missing"].extend(e["code"] for e in membership["errors"])
    result["verdict"] = "WARN" if result["missing"] else "PASS"
    return result


def fetch_issue(repo: str, number: int) -> dict:
    raw = github_client.check_output(
        [
            "gh",
            "issue",
            "view",
            str(number),
            "-R",
            repo,
            "--json",
            "body,title,labels",
        ],
        text=True,
        timeout=60,
    )
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("body", ""), (str, type(None))):
        raise ValueError("issue unread")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check DoR, stable-ID DoD structure and live issue membership.\n"
        "Use --issue for dispatch; body-only modes leave membership unchecked.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.ci.check_issue_task_quality --issue 10565 --strict --json\n"
        "  .venv/bin/python -m scripts.ci.check_issue_task_quality --body-file card.md\n"
        "Outputs: stdout; successful complete live membership audits atomically refresh batch_state/issue_stream_audit.json.\n"
        "Issue fetch and membership each have a 60-second budget.\n"
        "Parentless targets try a validated audit cache (maximum age 3600s) before a live audit.\n"
        "Timeout codes identify the target fetch, cache validation, or live audit root and issue.\n"
        "Exit codes: 0 = advisory or PASS; 1 = strict WARN; 2 = invalid arguments.\n"
        "Related: docs/best-practices/task-quality.md, issue #10565.",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--issue", type=int, help="GitHub issue number (uses gh)")
    src.add_argument("--body-file", type=str, help="Path to markdown body")
    src.add_argument("--body", type=str, help="Inline markdown body")
    parser.add_argument(
        "--repo",
        default="learn-ukrainian/learn-ukrainian.github.io",
        help="owner/repo for --issue (default: learn-ukrainian/learn-ukrainian.github.io); other pinned checkouts may use this CLI",
    )
    parser.add_argument(
        "--trivial",
        action="store_true",
        help="Treat as trivial exempt even without the word in the body",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN (default: always 0 — fail-open advisory)",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable result")
    args = parser.parse_args(argv)

    try:
        if args.issue is not None:
            with time_budget():
                issue = fetch_issue(args.repo, args.issue)
            if args.trivial:
                issue = {**issue, "labels": [{"name": "trivial"}]}
            try:
                with time_budget():
                    membership = observe_membership(issue, args.repo, args.issue)
            except (TimeoutError, subprocess.TimeoutExpired):
                membership = membership_error("membership_timeout")
            result = evaluate_issue(issue, membership)
        elif args.body_file:
            with open(args.body_file, encoding="utf-8") as handle:
                body = handle.read()
            issue_trivial = False
        else:
            body = args.body or ""
            issue_trivial = False
        if args.issue is None:
            result = score_body(body, trivial=args.trivial or issue_trivial)
    except (
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
        UnicodeError,
        ValueError,
        RuntimeError,
    ) as exc:
        timeout = isinstance(exc, (TimeoutError, subprocess.TimeoutExpired))
        timeout_code = "membership_timeout_target_fetch"
        result = {
            "verdict": "WARN",
            "trivial": False,
            "missing": ["input", "checker_error", *([timeout_code] if timeout else [])],
            "present": [],
            "notes": ["input_error"],
            "dor": section("unchecked"),
            "dod": section("unchecked"),
            "membership": section("unchecked", membership_error(timeout_code)["errors"] if timeout else []),
        }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"verdict={result['verdict']}")
        if result["trivial"]:
            print("trivial=true")
        if result["missing"]:
            print("missing=" + ",".join(str(x) for x in result["missing"]))
        if result["present"]:
            print("present=" + ",".join(str(x) for x in result["present"]))
        for note in result["notes"]:
            print(f"note={note}")
        print("canonical=docs/best-practices/task-quality.md")

    if args.strict and result["verdict"] == "WARN":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
