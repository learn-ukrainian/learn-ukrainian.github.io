"""Daily counts-only issue readiness report for every fleet repository (#10565)."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.ci import check_issue_task_quality as checker
from scripts.common import github_client
from scripts.common.repo_root import project_interpreter
from scripts.orchestration import fleet_repos
from scripts.orchestration import issue_stream_audit as audit
from scripts.publish.github import read

ROOT = Path(__file__).resolve().parents[2]
LIMIT = 500
COUNTERS = ("open", "missing_dor", "missing_dod", "malformed_dod", "missing_epic", "pending_native_link")
CODES = frozenset(
    {
        "forge_unavailable",
        "rate_limited",
        "listing_truncated",
        "listing_count_mismatch",
        "membership_registry_absent",
        "membership_audit_incomplete",
        "membership_audit_stale",
        "membership_audit_cache_write_failed",
        "checker_error",
    }
)


def lane(*, unavailable: bool = False) -> dict:
    return dict.fromkeys(COUNTERS, None if unavailable else 0)


def collect_repository(repo) -> tuple[list[dict] | None, int | None, dict | None, list[str]]:
    """Keep exceptions and private issue data inside this read boundary."""
    issues, count, report, codes = None, None, None, []
    try:
        issues = json.loads(
            github_client.check_output(
                [
                    "gh",
                    "issue",
                    "list",
                    "-R",
                    repo.github,
                    "--state",
                    "open",
                    "--limit",
                    str(LIMIT),
                    "--json",
                    "number,title,body,labels",
                ],
                text=True,
                timeout=60,
            )
        )
        if not isinstance(issues, list) or any(
            not isinstance(i, dict) or type(i.get("number")) is not int for i in issues
        ):
            raise ValueError
    except github_client.GitHubRateLimited:
        issues = None
        codes.append("rate_limited")
    except Exception:
        issues = None
        codes.append("forge_unavailable")
    try:
        result = read("issue-count", repo=repo.github, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise ValueError
        count = json.loads(result.stdout)["data"]["repository"]["issues"]["totalCount"]
        if type(count) is not int or count < 0:
            raise ValueError
    except github_client.GitHubRateLimited:
        count = None
        codes.append("rate_limited")
    except Exception:
        count = None
        codes.append("forge_unavailable")
    if repo.role == "public-monorepo":
        try:
            # Exactly one audit per repository, no per-issue ancestry walks.
            registry = checker.registry_for(repo.github)
            if not registry:
                raise ValueError("membership registry absent")
            # Avoid run_audit's unvalidated, checkout-local cache write.
            # Publish only after the independent census reconciles.
            report = checker.live_audit(repo.github, registry, root=ROOT)
        except github_client.GitHubRateLimited:
            codes.append("rate_limited")
        except Exception:
            codes.append("membership_audit_incomplete")
        if (
            report is not None and issues is not None and count == len(issues) and len(issues) < LIMIT
            and sorted(i["number"] for i in issues) == report.get("open_issue_numbers")
        ):
            try:
                checker.write_membership_cache(report, repo.github, registry, root=ROOT)
            except OSError:
                codes.append("membership_audit_cache_write_failed")
    return issues, count, report, codes


def summarize_repository(
    repo, issues: list[dict] | None, count: int | None, report: dict | None, codes: list[str], registry: dict
) -> dict:
    """Pure counts projection. Never copy issue fields or exception diagnostics."""
    codes = list(codes)
    public = repo.role == "public-monorepo"
    registry = registry if public else {}
    lanes = {
        key: lane(unavailable=issues is None) for key in [*registry, "unassigned", "ambiguous", "membership_unknown"]
    }
    roots = {n: key for key, ns in registry.items() for n in ns}
    membership_ok = False
    if not registry:
        codes.append("membership_registry_absent")
    elif (
        not isinstance(report, dict)
        or report.get("repository", "").casefold() != repo.github.casefold()
        or not audit.membership_report_is_complete(report)
    ):
        codes.append("membership_audit_incomplete")
    elif audit.validate_membership_report(report, checker.MAX_AGE_S) is None:
        codes.append("membership_audit_stale")
    else:
        membership_ok = True
    if issues is not None:
        if len(issues) >= LIMIT:
            codes.append("listing_truncated")
        if count is not None and (len({i["number"] for i in issues}) != count or len(issues) != count):
            codes.append("listing_count_mismatch")
        if report is not None and report.get("open_total") != len(issues):
            codes.append("membership_audit_incomplete")
            membership_ok = False
    evaluated = root_exempt = 0
    for issue in issues or []:
        number = issue["number"]
        entry = (report or {}).get("effective_membership", {}).get(str(number), {})
        if number in roots:
            key = roots[number]
            root_exempt += 1
        elif not membership_ok:
            key = "membership_unknown"
        elif entry and entry.get("unique_stream") is not True:
            key = "ambiguous"
        else:
            key = (entry.get("streams") or ["unassigned"])[0]
            if key not in lanes:
                key = "membership_unknown"
        bucket = lanes[key]
        bucket["open"] += 1
        try:
            result = checker.score_body(
                issue.get("body") or "",
                trivial=checker.issue_is_trivial(issue.get("body") or "", issue.get("labels") or []),
            )
            bucket["missing_dor"] += int(result["dor"]["status"] == "WARN")
            dod_codes = {e["code"] for e in result["dod"]["errors"]}
            bucket["missing_dod"] += int("dod_structure_absent" in dod_codes)
            bucket["malformed_dod"] += int("dod_structure_malformed" in dod_codes)
            if membership_ok:
                # Reuse canonical membership semantics over this audit snapshot.
                epic = (entry.get("epics") or [None])[0]
                parent = {"number": epic, "repository": repo.github} if entry.get("via") == "native" else None
                membership = checker.evaluate_membership(issue, repo.github, number, registry, {number: parent}, report)
                bucket["missing_epic"] += int(membership["status"] == "WARN")
                bucket["pending_native_link"] += int(membership.get("pending_native_link", False))
            evaluated += 1
        except Exception:
            codes.append("checker_error")
    if not membership_ok:
        for bucket in lanes.values():
            bucket["missing_epic"] = bucket["pending_native_link"] = None
    codes = sorted(set(codes) & CODES)
    return {
        "key": repo.key,
        "visibility": "public" if public else "private",
        "coverage": "incomplete" if codes else "complete",
        "incomplete_codes": codes,
        "open_total": count,
        "evaluated_total": evaluated,
        "root_exempt_total": root_exempt,
        "lanes": lanes,
    }


def build_report() -> dict:
    repos = fleet_repos.load_fleet_repos()
    try:
        registry = audit.load_registry(ROOT / "scripts/config/issue_streams.yaml", audit_only=True)
    except (OSError, ValueError):
        registry = {}
    source = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=10
    ).stdout.strip()
    return {
        "schema": "issue-quality-report.v1",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha": source,
        "repositories": {
            key: summarize_repository(repo, *collect_repository(repo), registry) for key, repo in repos.items()
        },
    }


def persisted_payload(day: str, *, root: Path = ROOT, build=build_report) -> bytes:
    """Publish only a completed, immutable daily payload under ignored reports."""
    directory = root / "batch_state/reports"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"issue-quality-report-{day}.json"
    if not path.exists():
        if date.fromisoformat(day) != datetime.now(UTC).date():
            raise ValueError("only today's report can be prepared; other dates require a saved payload")
        payload = (json.dumps(build(), sort_keys=True, indent=2) + "\n").encode()
        # Stage this report beside its destination, as the other atomic report
        # writers do. A managed scratch volume may be on another filesystem,
        # where the no-replace hard link below would fail.
        temporary = directory / f".issue-quality-{uuid.uuid4().hex}.json"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            with contextlib.suppress(FileExistsError):
                os.link(temporary, path)
        finally:
            temporary.unlink()
    return path.read_bytes()


def publish_payload(payload: bytes, day: str, sender: str) -> int:
    result = subprocess.run(
        [
            str(project_interpreter(ROOT)),
            "-m",
            "scripts.fleet_comms",
            "channel",
            "publish",
            "epics",
            "-",
            "--sender",
            sender,
            "--source",
            "issue-quality-report",
            "--kind",
            "report",
            "--idempotency-key",
            f"issue-quality-report:{day}",
        ],
        input=payload,
        capture_output=True,
        timeout=60,
        check=False,
        cwd=ROOT,
    )
    return int(result.returncode != 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare daily counts-only issue quality for all fleet repositories.\nUse --publish from the daily timer; default only persists and prints.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.orchestration.issue_quality_report\n  .venv/bin/python -m scripts.orchestration.issue_quality_report --publish --sender devops\nOutputs: ignored batch_state/reports/issue-quality-report-<UTC date>.json; --publish sends the same bytes on retry.\nComplete conflict-free membership audits atomically refresh shared batch_state/issue_stream_audit.json (3600s freshness).\nExit codes: 0 = persisted/published; 1 = preparation or publication failed; 2 = invalid usage.\nRelated: #10565, #10793, docs/best-practices/task-quality.md.",
    )
    parser.add_argument("--publish", action="store_true", help="Publish persisted payload to epics (default: false)")
    parser.add_argument("--sender", default="devops", help="Fleet Comms sender (default: devops)")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=datetime.now(UTC).date(),
        help="UTC day, YYYY-MM-DD; prepare today or retry a saved payload (default: today UTC)",
    )
    args = parser.parse_args(argv)
    day = args.date.isoformat()
    try:
        payload = persisted_payload(day)
        if args.publish:
            return publish_payload(payload, day, args.sender)
        print(payload.decode(), end="")
        return 0
    except Exception:
        print("issue quality report: checker_error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
