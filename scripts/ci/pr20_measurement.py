"""Replay the frozen last50 and predeclared next50 PR measurement, offline.

Raw GitHub snapshots are evidence, not instructions. This command never calls
GitHub, changes CI, enqueues work, or performs a rollback. See the protocol in
docs/best-practices/pr20-measurement.md for input and attribution contracts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SIZE = 50
BASELINE_MEMBERSHIP_SHA256 = "83b9115d8f86a96991ef0329d4f68bec2877fb2773b5765b4412e985b42e3272"
PROTOCOL = Path(__file__).resolve().parents[2] / "docs/best-practices/pr20-measurement.md"
SHA = re.compile(r"[0-9a-f]{40}")
QUEUE_PR = re.compile(r"gh-readonly-queue/[^/]+/pr-(\d+)-")


class InputError(ValueError):
    """A privacy-safe diagnostic with no raw input body."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def stamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InputError("timestamp must be an ISO 8601 string or null")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise InputError("timestamp requires a timezone")
    return parsed.astimezone(UTC)


def utc(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def minutes(start: Any, end: Any) -> float | None:
    a, b = stamp(start), stamp(end)
    return (b - a).total_seconds() / 60 if a is not None and b is not None else None


def stats(values: list[float | None], denominator: int | None = None) -> dict:
    """Adapt the original analyze.py ordinary median and nearest-rank p90."""
    known = sorted(x for x in values if x is not None)
    denominator = len(values) if denominator is None else denominator
    unknown = denominator - len(known)
    observed = {
        "median": round(statistics.median(known), 2) if known else None,
        "p90": round(known[math.ceil(0.9 * len(known)) - 1], 2) if known else None,
        "mean": round(statistics.mean(known), 2) if known else None,
    }
    return {
        "n": len(known), "denominator": denominator, "unknown": unknown,
        **{k: v if unknown == 0 else None for k, v in observed.items()},
        "observed": observed, "unrounded": {
            "median": statistics.median(known) if known and unknown == 0 else None,
            "p90": known[math.ceil(0.9 * len(known)) - 1] if known and unknown == 0 else None,
            "mean": statistics.mean(known) if known and unknown == 0 else None,
        },
    }


class Inputs:
    """Hash every consumed file, including explicitly absent optional telemetry."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.manifest: dict[str, str | None] = {}

    def path(self, name: str) -> Path:
        path = (self.root / name).resolve()
        if not path.is_relative_to(self.root) or Path(name).is_absolute():
            raise InputError("evidence file must stay within the input directory")
        return path

    def raw(self, name: str, *, required: bool = False) -> bytes | None:
        path = self.path(name)
        if not path.is_file():
            self.manifest[name] = None
            if required:
                raise InputError("required input missing")
            return None
        raw = path.read_bytes()
        fingerprint = digest(raw)
        if name in self.manifest and self.manifest[name] != fingerprint:
            raise InputError("input changed during replay")
        self.manifest[name] = fingerprint
        return raw

    def read(self, name: str, *, required: bool = False) -> Any:
        raw = self.raw(name, required=required)
        return json.loads(raw) if raw is not None else None

    def reference(self, refs: Any) -> bool:
        if not isinstance(refs, list) or not refs:
            return False
        return all(
            isinstance(ref, dict) and bool(ref.get("locator"))
            and isinstance(ref.get("file"), str)
            and self.read(ref["file"]) is not None
            for ref in refs
        )

    def receipt(self) -> dict:
        return {"files": dict(sorted(self.manifest.items())), "sha256": digest(encoded(self.manifest))}


def events(value: Any) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise InputError("timeline must be an array or a slurped array of pages")
    return [item for page in value for item in (page if isinstance(page, list) else [page])]


def published_reviews(detail: dict, cutoff: str) -> list[dict]:
    markers = []
    for comment in detail.get("comments", []):
        for raw in re.findall(r"<!-- cf-verdict v1 (.*?) -->", comment.get("body", "")):
            fields = dict(re.findall(r"(\w+)=([^\s]+)", raw))
            if all(fields.get(k) for k in ("task", "sha", "verdict")):
                markers.append({**fields, "posted": comment["createdAt"],
                                "edited": comment.get("includesCreatedEdit"), "url": comment.get("url")})
    for review in detail.get("reviews", []):
        if review["state"] in ("APPROVED", "CHANGES_REQUESTED"):
            markers.append({"verdict": review["state"], "sha": review["commit"]["oid"],
                            "task": review["id"], "posted": review["submittedAt"]})
    # Keep the original task/head/verdict counting convention and last duplicate.
    distinct = {(m["task"], m["sha"], m["verdict"]): m for m in markers}
    return sorted((m for m in distinct.values() if stamp(m["posted"]) <= stamp(cutoff)),
                  key=lambda m: stamp(m["posted"]))


def run_id(check: dict) -> int | None:
    match = re.search(r"/runs/(\d+)", check.get("detailsUrl", ""))
    return int(match[1]) if match else None


def qualify(pr: dict, timeline: list[dict], complete: bool) -> tuple[str | None, str | None]:
    """First non-draft instant, including PRs later converted back to draft."""
    if not complete or not isinstance(pr.get("isDraft"), bool):
        return None, "draft_history_unknown"
    transitions = sorted((e for e in timeline if e.get("event") in ("ready_for_review", "convert_to_draft")),
                         key=lambda e: stamp(e["created_at"]))
    if transitions:
        # A first ready event implies creation as draft; conversion implies non-draft.
        if transitions[0]["event"] == "ready_for_review":
            return transitions[0]["created_at"], None
        return pr["createdAt"], None
    return (None, "never_non_draft") if pr["isDraft"] else (pr["createdAt"], None)


def queue_runs(inputs: Inputs, runs: list[dict], number: int, cutoff: str, snapshot: dict) -> list[dict]:
    out = []
    for run in runs:
        if run.get("event") != "merge_group" or stamp(run["createdAt"]) > stamp(cutoff):
            continue
        match = QUEUE_PR.search(run.get("headBranch", ""))
        memberships = [m for m in snapshot.get("groups", []) if m["run_id"] == run["databaseId"]]
        membership = memberships[0] if len(memberships) == 1 else None
        full_membership = bool(membership and inputs.reference(membership.get("evidence")))
        named = int(match[1]) if match else None
        if number != named and not (full_membership and number in membership["prs"]):
            continue
        raw = inputs.read(f'queue-run-{run["databaseId"]}.json')
        if raw and (raw["databaseId"] != run["databaseId"] or raw["headSha"] != run["headSha"]
                    or raw["event"] != "merge_group" or raw["createdAt"] != run["createdAt"]):
            raise InputError("queue run identity mismatch")
        jobs = raw.get("jobs", []) if raw else []
        gates = [j for j in jobs if j["name"] == "CI Gate" and j["conclusion"] == "success"
                 and j.get("completedAt") and stamp(j["completedAt"]) <= stamp(cutoff)]
        gate = max((j["completedAt"] for j in gates), key=stamp, default=None)
        shards = [j for j in jobs if j["name"].startswith("pytest (")]
        reused = all(j["conclusion"] == "skipped" for j in shards) if shards else None
        full = bool(shards) and all(j["conclusion"] == "success" for j in shards)
        out.append({
            "id": run["databaseId"], "candidate_sha": run["headSha"], "ref": run.get("headBranch"),
            "created": run["createdAt"], "conclusion": run.get("conclusion"), "gate_completed": gate,
            "full_green": gate if full else None, "reused": reused,
            "membership": membership["prs"] if full_membership else ([named] if named else []),
            "membership_complete": full_membership,
            "workflow_to_gate": minutes(run["createdAt"], gate),
            "jobs": [{k: j.get(k) for k in ("databaseId", "run_id", "run_attempt", "head_sha", "name", "conclusion", "startedAt", "completedAt")}
                     for j in jobs],
        })
    return sorted(out, key=lambda r: (stamp(r["created"]), r["id"]))


def ledger_row(inputs: Inputs, pr: dict, runs: list[dict], snapshot: dict, baseline: bool) -> dict:
    number = pr["number"]
    detail = inputs.read(f"pr-{number}.json")
    timeline_raw = inputs.read(f"timeline-{number}.json")
    timeline = events(timeline_raw)
    if detail and detail.get("number") != number:
        raise InputError("PR detail identity mismatch")
    merged = pr.get("mergedAt")
    if merged and stamp(merged) < stamp(pr["createdAt"]):
        raise InputError("merge precedes creation")
    observed = snapshot.get("observed_at")
    cutoff = merged or observed
    if cutoff is None:
        raise InputError("unmerged rows require snapshot observed_at")
    if merged and observed and stamp(merged) > stamp(observed):
        raise InputError("merge timestamp is after snapshot observed_at")
    complete = timeline_raw is not None and (baseline or number in snapshot.get("timelines_complete", []))
    reviews_complete = detail is not None and (baseline or number in snapshot.get("reviews_complete", []))
    markers = published_reviews(detail or {}, cutoff)
    enqueues = [e for e in timeline if e.get("event") == "added_to_merge_queue"
                and stamp(e["created_at"]) <= stamp(cutoff)]
    enqueues.sort(key=lambda e: stamp(e["created_at"]))
    enqueue = enqueues[-1]["created_at"] if enqueues else None
    approvals = [m for m in markers if m["sha"] == pr["headRefOid"] and m["verdict"] in ("APPROVE", "APPROVED")]
    admission_approval = max((m["posted"] for m in approvals if enqueue and stamp(m["posted"]) <= stamp(enqueue)),
                             key=stamp, default=None)
    checks = (detail or {}).get("statusCheckRollup") or []
    runmap = {r["databaseId"]: r for r in runs}
    if len(runmap) != len(runs):
        raise InputError("duplicate run identity")
    gates = [c for c in checks if c.get("name") == "CI Gate" and c.get("conclusion") == "SUCCESS"
             and c.get("completedAt") and stamp(c["completedAt"]) <= stamp(cutoff)
             and runmap.get(run_id(c), {}).get("event") == "pull_request"
             and runmap[run_id(c)]["headSha"] == pr["headRefOid"]]
    green_check = min(gates, key=lambda c: stamp(c["completedAt"]), default=None)
    green = green_check["completedAt"] if green_check else None
    codeql = [c["completedAt"] for c in checks if c.get("name", "").startswith("Analyze (")
              and c.get("conclusion") == "SUCCESS" and c.get("completedAt")
              and stamp(c["completedAt"]) <= stamp(cutoff)]
    ready = max([admission_approval, green, *codeql], key=stamp) if admission_approval and green else None
    queues = queue_runs(inputs, runs, number, cutoff, snapshot)
    successful = [r for r in queues if r["conclusion"] == "success"]
    final_queue = successful[-1] if successful else None
    removals = []
    for e in timeline:
        if e.get("event") != "removed_from_merge_queue" or stamp(e["created_at"]) > stamp(cutoff):
            continue
        matches = [a for a in snapshot.get("removals", []) if a["event_id"] == e["id"] and a["pr"] == number]
        attribution = matches[0] if len(matches) == 1 else None
        cause = attribution.get("cause") if attribution and inputs.reference(attribution.get("evidence")) else "unknown"
        if cause not in ("merged", "pr_own_defect", "other", "unknown"):
            raise InputError("unsupported removal cause")
        removals.append({"id": e["id"], "at": e["created_at"], "cause": cause, "attribution": attribution})
    head_events = [h for h in snapshot.get("heads", []) if h["pr"] == number and h["sha"] == pr["headRefOid"]
                   and inputs.reference(h.get("evidence"))]
    head_at = head_events[0]["at"] if len(head_events) == 1 else None
    if head_at and (stamp(head_at) < stamp(pr["createdAt"]) or stamp(head_at) > stamp(cutoff)):
        raise InputError("head timestamp outside PR observation interval")
    return {
        "pr": number, "head": pr["headRefOid"], "opened": pr["createdAt"], "head_at": head_at,
        "head_observed_at": observed, "state": pr.get("state", "MERGED" if merged else "UNKNOWN"),
        "merged": merged, "merge_commit": pr.get("mergeCommit"),
        "commits": [{k: c.get(k) for k in ("oid", "committedDate")} for c in (detail or {}).get("commits", [])],
        "pr_admission_green": green, "pr_run": run_id(green_check) if green_check else None,
        "first_verdict": markers[0]["posted"] if markers else None,
        "final_approve": approvals[-1]["posted"] if approvals else None, "admission_approve": admission_approval,
        "admission_ready_proxy": ready, "reviews": markers,
        "review_rounds_published": len(markers) if reviews_complete else None,
        "reviewed_heads": len({m["sha"] for m in markers}) if reviews_complete else None,
        "last_enqueue": enqueue, "enqueues": [{"id": e["id"], "at": e["created_at"]} for e in enqueues],
        "enqueue_count": len(enqueues) if complete else None,
        "removals": removals, "timeline_complete": complete,
        "queue_runs": queues, "queue_run": final_queue["id"] if final_queue else None,
        "queue_created": final_queue["created"] if final_queue else None,
        "queue_gate_completed": final_queue["gate_completed"] if final_queue else None,
        "full_green": final_queue["full_green"] if final_queue else None,
        "open_to_merged": minutes(pr["createdAt"], merged),
        "open_to_admission": minutes(pr["createdAt"], green),
        "ready_to_enqueue": minutes(ready, enqueue),
        "queue_ci": final_queue["workflow_to_gate"] if final_queue else None,
        "enqueue_to_merged": minutes(enqueue, merged),
        "right_censored_minutes": minutes(pr["createdAt"], observed) if not merged else None,
        "unknown_reasons": [reason for reason, condition in (
            ("detail_missing", detail is None), ("timeline_incomplete", not complete),
            ("review_history_incomplete", not reviews_complete), ("head_event_unavailable", head_at is None),
            ("admission_unavailable", green is None), ("not_yet_merged", not merged),
            ("successful_queue_gate_unavailable", not final_queue or not final_queue["gate_completed"]),
            ("full_execution_unproven", not final_queue or not final_queue["full_green"]),
            ("complete_queue_membership_unavailable", any(not r["membership_complete"] for r in queues)),
        ) if condition],
    }


def guardrails(inputs: Inputs, rows: list[dict], snapshot: dict, start: str, end: str, *, census_complete: bool = True) -> dict:
    enqueues = sum(r["enqueue_count"] or 0 for r in rows)
    denominator_known = census_complete and all(r["enqueue_count"] is not None for r in rows)
    removals = [a for r in rows for a in r["removals"]]
    defects = sum(a["cause"] == "pr_own_defect" for a in removals)
    unknown = sum(a["cause"] == "unknown" for a in removals)
    rate_known = denominator_known and unknown == 0 and enqueues > 0
    incidents = []
    incident_ids = [i["id"] for i in snapshot.get("main_incidents", [])]
    if len(set(incident_ids)) != len(incident_ids):
        raise InputError("duplicate main incident identity")
    for incident in snapshot.get("main_incidents", []):
        if stamp(start) <= stamp(incident["at"]) <= stamp(end):
            item = dict(incident)
            if not inputs.reference(item.get("evidence")):
                item["cause"] = "unknown"
            if item.get("cause") not in ("change", "other", "unknown"):
                raise InputError("unsupported main incident cause")
            incidents.append(item)
    coverage = snapshot.get("main_coverage", {})
    main_complete = (coverage.get("complete") is True and inputs.reference(coverage.get("evidence"))
                     and stamp(coverage.get("start")) is not None and stamp(coverage.get("end")) is not None
                     and stamp(coverage["start"]) <= stamp(start) and stamp(coverage["end"]) >= stamp(end))
    changed_main = sum(i["cause"] == "change" for i in incidents)
    stop_ejections = denominator_known and enqueues > 0 and defects * 10 > enqueues
    stop_main = changed_main > 0
    return {
        "enqueues": enqueues if denominator_known else None, "observed_enqueues": enqueues,
        "pr_own_defect_ejections": defects, "unknown_removal_attribution": unknown,
        "ejection_rate": defects / enqueues if rate_known else None,
        "ejection_rate_lower_bound": defects / enqueues if denominator_known and enqueues else None,
        "main_incidents": incidents, "main_coverage_complete": bool(main_complete),
        "red_main_count": len(incidents) if main_complete else None,
        "change_attributed_main_breaks": changed_main,
        "stop": stop_ejections or stop_main,
        "stop_reasons": [s for s, active in (("pr_own_defect_ejections_exceed_10_percent", stop_ejections),
                                             ("main_break_attributed_to_change", stop_main)) if active],
        "stop_status": "STOP" if stop_ejections or stop_main else (
            "no_observed_trigger" if rate_known and main_complete and all(i["cause"] != "unknown" for i in incidents)
            else "UNKNOWN"),
        "action_owner": "accountable driver", "action": "one clean revert PR through normal gates" if stop_ejections or stop_main else None,
    }


def analyze(root: Path, *, baseline: bool, switch: str | None = None) -> dict:
    inputs = Inputs(root)
    prs = inputs.read("pr-list.json", required=True)
    if len({p["number"] for p in prs}) != len(prs):
        raise InputError("duplicate PR number in census")
    if baseline and (len(prs) != SIZE or inputs.manifest["pr-list.json"] != BASELINE_MEMBERSHIP_SHA256):
        raise InputError("baseline must retain the original frozen last50 pr-list.json bytes")
    runs = inputs.read("ci-runs.json") or []
    snapshot = inputs.read("snapshot.json") or {}
    if not baseline and (snapshot.get("schema") != "pr20-snapshot.v1" or not stamp(snapshot.get("observed_at"))):
        raise InputError("next50 requires a pr20-snapshot.v1 with observed_at")
    excluded, eligible, unresolved = [], [], []
    if baseline:
        # Preserve the original selection and its raw reconstruction sources.
        inputs.read("pr-candidates.json")
        for name in ("methodology.md", "analyze.py", "queue_analysis.py"):
            inputs.raw(name)
        eligible = [(p["createdAt"], p) for p in prs]
    else:
        for pr in prs:
            opened = stamp(pr["createdAt"])
            if opened > stamp(snapshot["observed_at"]):
                raise InputError("PR creation is after snapshot observed_at")
            if opened < stamp(switch):
                excluded.append({"pr": pr["number"], "reason": "opened_before_switch"})
                continue
            timeline = inputs.read(f'timeline-{pr["number"]}.json')
            at, reason = qualify(pr, events(timeline), timeline is not None and pr["number"] in snapshot.get("timelines_complete", []))
            if reason == "draft_history_unknown":
                unresolved.append(pr["number"])
            elif reason:
                excluded.append({"pr": pr["number"], "reason": reason})
            elif stamp(at) <= stamp(snapshot["observed_at"]):
                eligible.append((at, pr))
            else:
                excluded.append({"pr": pr["number"], "reason": "never_non_draft"})
        eligible.sort(key=lambda item: (stamp(item[0]), item[1]["number"]))
    rows = [dict(ledger_row(inputs, p, runs, snapshot, baseline), eligible_at=at) for at, p in eligible[:SIZE]]
    start = min((r["opened"] for r in rows), key=stamp) if baseline else switch
    end = max((r["merged"] for r in rows), key=stamp) if baseline else snapshot["observed_at"]
    selection_complete = baseline or (snapshot.get("selection_complete") is True and inputs.reference(snapshot.get("selection_evidence")) and not unresolved)
    runs_complete = baseline or (snapshot.get("runs_complete") is True and inputs.reference(snapshot.get("runs_evidence")))
    if not runs_complete:
        for row in rows:
            row["queue_ci_observed"] = row["queue_ci"]
            row["queue_ci"] = None
            row["unknown_reasons"].append("run_census_incomplete")
    guard = guardrails(inputs, rows, snapshot, start, end, census_complete=bool(selection_complete))
    metrics = {name: stats([r[name] for r in rows], SIZE) for name in
               ("open_to_merged", "open_to_admission", "ready_to_enqueue", "enqueue_to_merged", "review_rounds_published", "queue_ci")}
    complete = bool(selection_complete and len(rows) == SIZE and all(r["merged"] for r in rows))
    target = metrics["open_to_merged"]["unrounded"]["median"]
    return {
        "schema": "pr20-report.v1", "arm": "last50" if baseline else "next50", "expected_denominator": SIZE,
        "time_window": {"start": start, "end": end}, "observed_at": snapshot.get("observed_at"),
        "selection_complete": bool(selection_complete), "runs_complete": bool(runs_complete), "cohort_complete": complete,
        "merge_window": {"start": min((r["merged"] for r in rows if r["merged"]), key=stamp, default=None),
                         "end": max((r["merged"] for r in rows if r["merged"]), key=stamp, default=None)},
        "selected": len(rows), "not_yet_selected": SIZE - len(rows),
        "merged": sum(bool(r["merged"]) for r in rows), "unmerged": sum(not r["merged"] for r in rows),
        "unresolved_selection": unresolved, "excluded": excluded,
        "beyond_first50": [p["number"] for _, p in eligible[SIZE:]],
        "metrics": metrics, "median_20min": ("PASS" if target <= 20 else "FAIL") if complete and target is not None else "UNKNOWN",
        "guardrails": guard, "ledger": rows, "inputs": inputs.receipt(),
        "unknown_counts": {field: sum(r[field] is None for r in rows) for field in
                           ("head_at", "pr_admission_green", "admission_approve", "last_enqueue", "queue_created", "full_green", "merged")},
        "evidence_role": "observational reconstruction; no review qualification, test coverage or causal attribution inferred",
    }


def implementation() -> dict:
    return {"script_sha256": digest(Path(__file__).read_bytes()), "protocol_sha256": digest(PROTOCOL.read_bytes())}


def write_new(path: Path, value: dict) -> None:
    # Exclusive creation prevents accidental replacement; the digest must also
    # be deposited in the driver's durable receipt store before the switch.
    raw = encoded(value)
    with path.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"output": path.name, "sha256": digest(raw)}, sort_keys=True))


def compare(before: dict, after: dict) -> dict:
    out = {}
    for name, a, b in (
        ("review_rounds_per_pr", before["metrics"]["review_rounds_published"]["unrounded"]["mean"], after["metrics"]["review_rounds_published"]["unrounded"]["mean"]),
        ("queue_ci_p90", before["metrics"]["queue_ci"]["unrounded"]["p90"], after["metrics"]["queue_ci"]["unrounded"]["p90"]),
        ("pr_own_defect_ejection_rate", before["guardrails"]["ejection_rate"], after["guardrails"]["ejection_rate"]),
        ("red_main_incidents", before["guardrails"]["red_main_count"], after["guardrails"]["red_main_count"]),
    ):
        out[name] = {"baseline": a, "next50": b,
                     "status": ("not_worse" if b <= a else "regression")
                     if after["cohort_complete"] and a is not None and b is not None else "UNKNOWN"}
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay PR latency and safety measurements from saved raw evidence.\n"
                    "Use before and after the declared CI switch; never use this tool to change CI or certify missing data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.ci.pr20_measurement baseline --inputs saved-last50 --output last50.json
  .venv/bin/python -m scripts.ci.pr20_measurement anchor --inputs saved-last50 --switch-pr switch-pr.json --observed-at 2026-10-23T20:00:00Z --output declaration.json
  .venv/bin/python -m scripts.ci.pr20_measurement measure --inputs saved-next50 --baseline saved-last50 --anchor declaration.json --switch-receipt switch-merged.json --output next50.json
Outputs: one new JSON report/ledger or immutable premerge declaration; no network or GitHub writes.
Exit codes: 0 = artifact written, including UNKNOWN or STOP results; 2 = invalid input or existing output.
Related: docs/best-practices/pr20-measurement.md. Read the result fields before making a decision.
""",
    )
    sub = parser.add_subparsers(dest="command", required=True, help="Offline operation; see each command's --help.")
    for command in ("baseline", "anchor", "measure"):
        child = sub.add_parser(command, help={"baseline": "Replay the original frozen last50.",
                                             "anchor": "Freeze the declaration before the CI PR merges.",
                                             "measure": "Report the prospective next50, retaining incomplete rows."}[command])
        child.add_argument("--inputs", type=Path, required=True, help="Saved raw input directory, e.g. saved-last50; required.")
        child.add_argument("--output", type=Path, required=True, help="New JSON file, e.g. report.json; refuses overwrite.")
        if command == "anchor":
            child.add_argument("--switch-pr", type=Path, required=True, help="Saved gh pr view JSON for the unmerged CI PR; required.")
            child.add_argument("--observed-at", required=True, help="UTC time from date -u, e.g. 2026-10-23T20:00:00Z; required.")
        if command == "measure":
            child.add_argument("--baseline", type=Path, required=True, help="Original saved-last50 directory, unchanged since declaration; required.")
            child.add_argument("--anchor", type=Path, required=True, help="Immutable premerge declaration JSON; required.")
            child.add_argument("--switch-receipt", type=Path, required=True, help="Saved gh pr view JSON proving CI PR merge with unchanged head; required.")
    args = parser.parse_args(argv)
    try:
        if args.command == "baseline":
            result = analyze(args.inputs, baseline=True)
            result["implementation"] = implementation()
        elif args.command == "anchor":
            before = analyze(args.inputs, baseline=True)
            raw = args.switch_pr.read_bytes()
            pr = json.loads(raw)
            if pr.get("mergedAt") or pr.get("state") != "OPEN" or pr.get("isDraft") is not False:
                raise InputError("switch PR must be open, non-draft and unmerged")
            if not SHA.fullmatch(pr.get("headRefOid", "")) or pr.get("baseRefName") != "main":
                raise InputError("switch PR requires exact head SHA and main base")
            at = stamp(args.observed_at)
            if at is None or at < stamp(pr["createdAt"]):
                raise InputError("invalid premerge observation timestamp")
            source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, timeout=30).strip()
            for relative, path in (("scripts/ci/pr20_measurement.py", Path(__file__)),
                                   ("docs/best-practices/pr20-measurement.md", PROTOCOL)):
                committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], stderr=subprocess.DEVNULL, timeout=30)
                if committed != path.read_bytes():
                    raise InputError("anchor requires the committed script and protocol")
            result = {"schema": "pr20-declaration.v1", "captured_at": utc(at), "source_sha": source,
                      "switch_pr": pr["number"], "switch_head": pr["headRefOid"], "switch_pr_sha256": digest(raw),
                      "effective_switch": "actual mergedAt of this exact CI PR/head; not captured_at",
                      "baseline_inputs": before["inputs"], "implementation": implementation(),
                      "denominator": SIZE, "cohort_rule": "first non-draft eligibility then PR number; opened at/after CI merge",
                      "target": "median open-to-merged <=20 minutes; nearest-rank p90 reported",
                      "stop": "PR-own-defect removals >10% of enqueues or any change-attributed main break",
                      "owner": "accountable driver; one revert PR under normal gates if STOP"}
        else:
            raw_anchor, raw_switch = args.anchor.read_bytes(), args.switch_receipt.read_bytes()
            anchor, switched = json.loads(raw_anchor), json.loads(raw_switch)
            if anchor.get("schema") != "pr20-declaration.v1" or anchor["implementation"] != implementation():
                raise InputError("declaration schema or implementation digest mismatch")
            if (switched["number"] != anchor["switch_pr"] or switched["headRefOid"] != anchor["switch_head"]
                    or switched.get("state") != "MERGED" or switched.get("baseRefName") != "main"
                    or not SHA.fullmatch((switched.get("mergeCommit") or {}).get("oid", ""))
                    or not switched.get("mergedAt") or stamp(switched["mergedAt"]) <= stamp(anchor["captured_at"])):
                raise InputError("switch merge must follow declaration and match the frozen PR/head")
            before = analyze(args.baseline, baseline=True)
            if before["inputs"] != anchor["baseline_inputs"]:
                raise InputError("baseline inputs changed after declaration")
            result = analyze(args.inputs, baseline=False, switch=switched["mergedAt"])
            if stamp(result["observed_at"]) < stamp(switched["mergedAt"]):
                raise InputError("next50 observation precedes switch")
            result.update({"implementation": implementation(), "declaration_sha256": digest(raw_anchor),
                           "switch_receipt_sha256": digest(raw_switch), "switch": switched,
                           "baseline": before, "comparison": compare(before, result)})
        write_new(args.output, result)
    except InputError as exc:
        print(f"pr20 measurement: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError, subprocess.SubprocessError) as exc:
        # Do not echo raw inputs or exception bodies, which may contain private data.
        print(f"pr20 measurement: invalid/unavailable input or output ({type(exc).__name__}); see protocol", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
