"""Report-only component selection and an independent full-JUnit failure oracle.

Never execute or deselect tests. Register before collecting candidate receipts;
missing evidence is unresolved, including after the day-30 stop.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.ci import components, pytest_report
from scripts.ci import dependency_change_scope as dependency
from scripts.ci.junit_results import parse_junit
from scripts.common import github_client

SCHEMA = "component-shadow.v1"
BASELINE = "2026-10-03T00:00:00Z..2026-10-06T11:14:28Z"
FLAKE_RULE = "Every full-JUnit failure counts, including flaky tests; no post-hoc reclassification."
BASE_RULE = "Exempt only the same failing ID in an artifact-complete first-attempt rerun of the event base SHA."
INJECTION_COVERAGE = set(components.NODE_IDS) | {"shared-fixture", "dynamic-load", "subprocess", "stale-artifact"}
TOOLS = ("scripts/ci/component_shadow.py", "scripts/ci/components.py", "scripts/ci/components.json",
         "scripts/ci/junit_results.py", "scripts/ci/dependency_change_scope.py",
         "scripts/ci/dependency_change_denominator.json", "scripts/ci/pytest_report.py",
         "scripts/ci/frontend_change_scope.py", "scripts/ci/frontend_change_denominator.json",
         "scripts/common/repo_root.py", "scripts/common/jsonl.py", "scripts/storage/test_baseline.py",
         "scripts/deploy/auto_deploy_eligibility.py")
REVIEW_EDGE_CENSUS = {
    "head_sha": "c3695226db3b18ec0e3ab42c9a7a3221e00df69c",
    "source": "claude-opus-5-5 review of record; measured selection, not the current census",
    "total": 14692,
    "by_kind": {"file_reads": 10379, "subprocess": 2427, "sys_path": 1641,
                "dynamic_loads": 240, "missing_imports": 5},
    "resolution_owner": "#9721 driver; separate edge-resolution follow-up",
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include UTC offset")
    return parsed


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value: dict, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def identities(root: Path, graph: dict) -> dict:
    return {"graph_hash": digest(graph), "source_hash": digest({
        path: hashlib.sha256(source).hexdigest() for path, source in components.python_sources(root).items()
    }), "tool_hashes": {name: hashlib.sha256((components.ROOT / name).read_bytes()).hexdigest() for name in TOOLS}}


def dependency_input(path: str, patterns: list[str]) -> bool:
    """Include nested dependency manifests and lockfiles, beyond audit scope."""
    name = Path(path).name.lower()
    return (dependency.path_in_denominator(path, patterns)
            or name in {"package.json", "pyproject.toml", "setup.py", "setup.cfg", "pipfile",
                        "cargo.toml", "go.mod", "go.sum", "gemfile", "pnpm-workspace.yaml"}
            or (name.startswith("requirements") and Path(path).suffix in {".txt", ".in"})
            or name.endswith((".lock", "-lock.json", "-lock.yaml", "-lock.yml"))
            or name in {"gemfile.lock", "pipfile.lock", "yarn.lock"})


def select(base: str, head: str, event: str, root: Path = components.ROOT) -> dict:
    """Use the event head and merge base; all uncertainty selects the full set."""
    # Observe historical source checkouts with the registered observer/map,
    # even when those commits predate the component tooling itself.
    manifest = components.load_manifest()
    graph = components.import_graph(manifest, root)
    all_tests = sorted(pytest_report.tracked_test_files(root))
    reason, paths = "", []
    if event != "pull_request":
        reason = "non-pr-event"
    elif not base:
        reason = "missing-base"
    else:
        try:
            diff_range = dependency.resolve_git_range(base, head, cwd=root)
            raw = subprocess.run(["git", "diff", "--name-status", "-M", "-z", diff_range],
                                 cwd=root, check=True, capture_output=True, timeout=30).stdout
            paths = dependency._parse_name_status_z(raw)
            if not paths:
                reason = "empty-diff"
        except (dependency.MergeBaseError, subprocess.SubprocessError, OSError):
            reason = "diff-unavailable"
    patterns = dependency.load_denominator(components.ROOT / dependency.DENOMINATOR_REL)["paths"]
    if any(path.startswith((".github/", "scripts/ci/")) or dependency_input(path, patterns) for path in paths):
        reason = "workflow-tool-or-dependency"
    affected = components.affected(paths, manifest, graph)
    if not reason and (affected["fallback_reasons"] or "shared-core" in affected["components"]):
        reason = ",".join(affected["fallback_reasons"]) or "shared-core"
    nodes = list(components.NODE_IDS) if reason else affected["components"]
    # Resolve importer and shared integration obligations through the map, not
    # through its static manifest test list. Full fallback is the entire census.
    selected = set(all_tests) if reason else {
        file for node in nodes for file in components.test_files(node, manifest, root)
    }
    return {"mode": "full" if reason else "selected", "reason": reason or "component-closure",
            "changed_paths": paths, "selected_nodes": sorted(nodes),
            "selected_test_files": sorted(selected), "would_skip_test_files": sorted(set(all_tests) - selected),
            "unresolved_edges": graph["unresolved_edges"], "identities": identities(root, graph)}


def read_full_results(directory: Path, root: Path, shards: int) -> dict:
    """Keep every failing ID and collection error, and audit artifact coverage."""
    reports = sorted(directory.rglob("pytest-shard-*.xml"))
    lists = sorted(directory.rglob("pytest-shard-*-files.txt"))
    expected = {f"pytest-shard-{i}" for i in range(1, shards + 1)}
    problems = []
    if {p.stem for p in reports} != expected or len(reports) != shards:
        problems.append("missing-or-duplicate-junit-shards")
    if {p.name.removesuffix("-files.txt") for p in lists} != expected or len(lists) != shards:
        problems.append("missing-or-duplicate-file-lists")
    files = {p.name.removesuffix("-files.txt"): p.read_text().splitlines() for p in lists}
    problems.extend(pytest_report.partition_problems(files, pytest_report.tracked_test_files(root)))
    results = []
    junit_hashes, seconds_by_file = {}, {}
    for path in reports:
        junit_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            parsed, cases = junit_cases(path)
            results.extend(parsed)
            if not parsed:
                problems.append("empty-junit-shard:" + path.name)
            # Independent duration estimate, never used for failure identities.
            for case, result in zip(cases, parsed, strict=True):
                file = result.node_id.split("::", 1)[0]
                seconds_by_file[file] = seconds_by_file.get(file, 0.0) + float(case.get("time", 0))
        except (ValueError, ET.ParseError, OSError):
            problems.append("unreadable-junit:" + path.name)
    collection_errors = sorted({r.node_id for r in results if r.outcome == "error" and "::" not in r.node_id})
    collected = sorted({r.node_id for r in results if "::" in r.node_id})
    marked = sorted({line.strip() for p in directory.rglob("pytest-shard-*-needs-artifact.txt")
                     for line in p.read_text().splitlines() if line.strip()})
    if not results:
        problems.append("no-junit-results")
    return {"collected_test_ids": sorted(set(collected) | set(marked)),
            "collection_basis": "full-run JUnit cases plus pre-deselection needs_artifact lists",
            "executed_test_ids": sorted({r.node_id for r in results if "::" in r.node_id and r.outcome != "skipped"}),
            "full_junit_failing_ids": sorted({r.node_id for r in results if r.outcome in {"failed", "error"}}),
            "collection_errors": collection_errors, "artifact_problems": sorted(set(problems)),
            "junit_hashes": junit_hashes, "test_seconds_by_file": seconds_by_file}


def junit_cases(path: Path) -> tuple[list, list]:
    """Keep failing duplicate IDs (including reruns), using the common ID reader."""
    tree = ET.parse(path)
    if tree.getroot().tag not in {"testsuites", "testsuite"}:
        raise ValueError("not JUnit XML")
    cases = list(tree.iter("testcase"))
    results = []
    for case in cases:
        suite = ET.Element("testsuite")
        suite.append(case)
        # The shared reader accepts ElementTree file objects as well as paths.
        results.extend(parse_junit([io.StringIO(ET.tostring(suite, encoding="unicode"))]))
    return results, cases


def oracle_failures(receipt: dict, directory: Path) -> tuple[set, set]:
    """Re-read retained JUnit independently; receipt claims are not the oracle."""
    run = str(receipt["run_id"])
    case_root = (directory / run / "junit").resolve()
    if not case_root.is_relative_to(directory.resolve()):
        raise ValueError("artifact path escapes receipt directory")
    hashes = receipt["junit_hashes"]
    paths = sorted(case_root.rglob("*.xml"))
    if not hashes or len(paths) != len(hashes) or {p.name for p in paths} != set(hashes):
        raise ValueError("missing-or-duplicate-oracle-artifacts")
    failed, collection = set(), set()
    for path in paths:
        if not path.resolve().is_relative_to(case_root) or hashlib.sha256(path.read_bytes()).hexdigest() != hashes[path.name]:
            raise ValueError("oracle-artifact-digest-mismatch")
        results, _ = junit_cases(path)
        if not results:
            raise ValueError("empty-oracle-artifact")
        failed.update(result.node_id for result in results if result.outcome in {"failed", "error"})
        collection.update(result.node_id for result in results if result.outcome == "error" and "::" not in result.node_id)
    if failed != set(receipt["full_junit_failing_ids"]) or collection != set(receipt["collection_errors"]):
        raise ValueError("receipt-oracle-disagreement")
    return failed, collection


def projected_cost(selection: dict, evidence: dict, cost: dict | None,
                   unknown_reason: str = "matched-pr-queue-cost-inputs-not-supplied") -> dict:
    """Preserve queue reuse in the PR projection; absent inputs stay unknown."""
    seconds = evidence["test_seconds_by_file"]
    total = sum(seconds.values())
    selected = sum(value for file, value in seconds.items() if file in selection["selected_test_files"])
    ratio = selected / total if total > 0 else None
    result = {"status": "unknown", "selected_test_time_fraction": ratio,
              "method": "test-time proportional PR estimate; preserve queue reuse, add all attempts and overhead",
              "elapsed_wait_minutes": None, "net_runner_minutes_saved": None}
    fields = {"full_pr_runner_minutes", "full_queue_runner_minutes", "reuse_probability",
              "reporter_runner_minutes", "rerun_runner_minutes", "ejection_runner_minutes",
              "duplicated_preparation_runner_minutes", "elapsed_wait_minutes"}
    if cost is None:
        return result | {"unknown_reason": unknown_reason}
    if not fields <= cost.keys() or ratio is None:
        return result | {"unknown_reason": "incomplete-cost-inputs-or-test-duration-evidence"}
    if any(not isinstance(cost[key], (int, float)) or cost[key] < 0 for key in fields) or cost["reuse_probability"] > 1:
        raise ValueError("invalid cost inputs")
    full = selection["mode"] == "full"
    # The advisory job is reuse-neutral: both projections retain the same
    # exact-tree queue reuse probability.
    queue = (1 - cost["reuse_probability"]) * cost["full_queue_runner_minutes"]
    overhead = sum(cost[key] for key in fields if key.endswith("runner_minutes") and not key.startswith("full_"))
    candidate = cost["full_pr_runner_minutes"] * (1 if full else ratio) + queue + overhead
    baseline = cost["full_pr_runner_minutes"] + queue
    return result | {"status": "projected", "inputs": cost, "lost_reuse_runner_minutes": 0,
                     "candidate_pr_plus_queue_runner_minutes": candidate,
                     "baseline_pr_plus_queue_runner_minutes": baseline,
                     "elapsed_wait_minutes": cost["elapsed_wait_minutes"],
                     "net_runner_minutes_saved": baseline - candidate}


def report(args) -> dict:
    receipt = {"schema": SCHEMA, "kind": args.kind, "run_id": str(args.run_id),
               "run_attempt": args.attempt, "event": args.event, "base_sha": args.base, "head_sha": args.head,
               "candidate_run_id": args.candidate_run_id, "observed_at": utc_now(),
               "review_unresolved_edge_census": REVIEW_EDGE_CENSUS}
    try:
        selection = select(args.base, args.head, args.event, args.root)
        results = read_full_results(args.results, args.root, args.shards)
        cost = json.loads(args.cost.read_text()) if args.cost else None
        receipt |= selection | results | {"projected_cost_after_lost_reuse": projected_cost(
            selection, results, cost, getattr(args, "cost_unknown_reason", "matched-pr-queue-cost-inputs-not-supplied"))}
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        receipt |= {"mode": "full", "reason": "report-unavailable", "artifact_problems": [type(exc).__name__]}
    write_json(args.output, receipt)
    return receipt


def gh_pages(endpoint: str, key: str) -> list[dict]:
    data = json.loads(github_client.run(["gh", "api", "--paginate", "--slurp", endpoint],
                                    check=True, capture_output=True, text=True, timeout=180).stdout)
    rows = [row for page in data for row in page[key]]
    if data and len(rows) != data[0]["total_count"]:
        raise ValueError("incomplete GitHub census")
    return rows


def inventory(repository: str, created: str, *, first_attempts: bool = False) -> dict:
    """Read run/job metadata only; no candidate test outcomes or artifacts."""
    runs = gh_pages(f"repos/{repository}/actions/workflows/ci.yml/runs?created={created}&per_page=100", "workflow_runs")
    rows = []
    for run in runs:
        if run["event"] not in {"pull_request", "merge_group"}:
            continue
        if first_attempts:
            run = json.loads(github_client.run(["gh", "api", f"repos/{repository}/actions/runs/{run['id']}/attempts/1"],
                                            check=True, capture_output=True, text=True, timeout=60).stdout)
            endpoint = f"repos/{repository}/actions/runs/{run['id']}/attempts/1/jobs?per_page=100"
        else:
            endpoint = f"repos/{repository}/actions/runs/{run['id']}/jobs?filter=latest&per_page=100"
        jobs = gh_pages(endpoint, "jobs")
        rows.append({"run_id": str(run["id"]), "event": run["event"], "status": run["status"],
                     "conclusion": run["conclusion"], "run_attempt": run["run_attempt"],
                     "created_at": run["created_at"], "completed_at": run["updated_at"],
                     "head_sha": run["head_sha"], "pytest_red": any(
                         job["name"].startswith("pytest (") and job["conclusion"] == "failure" for job in jobs)})
        if first_attempts and run["status"] == "completed":
            completed = [job["completed_at"] for job in jobs if job.get("completed_at")]
            if not completed:
                raise ValueError("first-attempt completion has no completed jobs")
            rows[-1]["completed_at"] = max(completed, key=instant)
    return {"schema": "shadow-census.v1", "complete": True, "first_attempts": first_attempts, "created_window": created,
            "acquired_at": utc_now(), "runs": rows}


def register(baseline: dict, root: Path, *, minimum_narrowed_cases: int = 1) -> dict:
    """Freeze the complete historical inventory and rules before any receipts."""
    if baseline.get("complete") is not True or baseline.get("created_window") != BASELINE:
        raise ValueError("registration requires a complete baseline-window census")
    if type(minimum_narrowed_cases) is not int or minimum_narrowed_cases < 1:
        raise ValueError("minimum narrowed cases must be a positive integer")
    graph = components.import_graph(components.load_manifest(), root)
    now = utc_now()
    historical = sorted({str(row["run_id"]) for row in baseline["runs"]
                         if row["event"] in {"pull_request", "merge_group"} and row["pytest_red"]})
    if not historical:
        raise ValueError("baseline contains no pytest-red run IDs")
    return {"schema": SCHEMA, "registered_at": now, "stop_at": (instant(now) + timedelta(days=30)).isoformat(),
            "identities": identities(root, graph), "baseline_hash": digest(baseline),
            "baseline_window": BASELINE, "historical_run_ids": historical,
            "minimum_narrowed_cases": minimum_narrowed_cases,
            "live_window": {"completed_first_attempt_pr_runs": 150, "minimum_pytest_red_runs": 30,
                            "ordering": "completed_at, run_id; all conclusions; completed after registration"},
            "flaky_classification_rule": FLAKE_RULE, "base_commit_rerun_rule": BASE_RULE,
            "injected_cases": [], "injections_owner": "driver", "injections_frozen": False}


def check(registration: dict, directory: Path, *, now: str | None = None) -> dict:
    """Score full failures independently of selection, refusing incomplete windows."""
    unresolved, misses, exemptions = [], [], []
    narrowed_red, narrowed_injected = 0, 0
    minimum_narrowed = registration.get("minimum_narrowed_cases")
    if type(minimum_narrowed) is not int or minimum_narrowed < 1:
        unresolved.append("minimum-narrowed-cases-not-pre-registered")
    registered = instant(registration["registered_at"])
    if (registration.get("schema") != SCHEMA or registration.get("flaky_classification_rule") != FLAKE_RULE
        or registration.get("base_commit_rerun_rule") != BASE_RULE
        or registration.get("live_window", {}).get("completed_first_attempt_pr_runs") != 150
        or registration.get("live_window", {}).get("minimum_pytest_red_runs") != 30
        or instant(registration["stop_at"]) != registered + timedelta(days=30)):
        raise ValueError("registration does not bind the required rules/denominators")
    census_path = directory / "runs.json"
    census = json.loads(census_path.read_text()) if census_path.exists() else {}
    if census.get("complete") is not True or census.get("first_attempts") is not True:
        unresolved.append("live-run-census-missing-or-incomplete")
    rows = [r for r in census.get("runs", []) if r["event"] == "pull_request"
            and r["status"] == "completed" and r["run_attempt"] == 1
            and registered < instant(r["completed_at"]) <= instant(registration["stop_at"])]
    rows.sort(key=lambda row: (instant(row["completed_at"]), int(row["run_id"])))
    rows = rows[:150]
    if len(rows) < 150:
        unresolved.append(f"live-window:{len(rows)}/150")
    red = sum(r["pytest_red"] is True for r in rows)
    if red < 30:
        unresolved.append(f"pytest-red:{red}/30")
    injections = registration.get("injected_cases", [])
    coverage = {label for case in injections for label in case.get("coverage", [])}
    if (not registration.get("injections_frozen") or len(injections) < 12
        or not coverage >= INJECTION_COVERAGE or len({case["id"] for case in injections}) != len(injections)):
        unresolved.append("driver-held-out-injections-not-frozen")
    receipts, bases = {}, {}
    for path in directory.rglob("*.json"):
        if path == census_path:
            continue
        receipt = json.loads(path.read_text())
        if receipt.get("schema") != SCHEMA:
            continue
        if receipt.get("kind") == "base":
            key = str(receipt.get("candidate_run_id"))
            if key in bases:
                unresolved.append("duplicate-base:" + key)
            bases[key] = receipt
        else:
            key = str(receipt.get("run_id"))
            if key in receipts:
                unresolved.append("duplicate-receipt:" + key)
            receipts[key] = receipt
    live = {str(row["run_id"]): row for row in rows}
    cases = [(str(run), "historical") for run in registration["historical_run_ids"]]
    cases += [(run, "live") for run in live]
    cases += [(str(case["id"]), "injected") for case in injections]
    tools = registration["identities"]["tool_hashes"]
    for run, kind in cases:
        receipt = receipts.get(run)
        if receipt is None:
            unresolved.append("missing-receipt:" + run)
            continue
        if kind == "live" and instant(receipt["observed_at"]) <= registered:
            raise ValueError("registration-after-results:" + run)
        if instant(receipt["observed_at"]) > instant(registration["stop_at"]):
            unresolved.append("receipt-after-day-30:" + run)
            continue
        if kind == "injected":
            case = next(case for case in injections if str(case["id"]) == run)
            if (not case.get("registered_at") or
                instant(receipt["observed_at"]) <= instant(case["registered_at"])):
                unresolved.append("injection-not-pre-registered:" + run)
                continue
            expected_failures = set(case.get("expected_failure_ids", []))
            actual_failures = set(receipt.get("full_junit_failing_ids", [])) | set(receipt.get("collection_errors", []))
            if not expected_failures or not expected_failures <= actual_failures:
                unresolved.append("injection-not-demonstrated:" + run)
                continue
        if (receipt.get("kind") != kind or receipt.get("artifact_problems") != []
            or not receipt.get("junit_hashes") or receipt.get("run_attempt") != 1
            or receipt.get("identities", {}).get("tool_hashes") != tools
            or receipt.get("mode") not in {"full", "selected"}
            or not isinstance(receipt.get("would_skip_test_files"), list)
            or not all(field in receipt for field in ("selected_test_files", "full_junit_failing_ids", "collection_errors"))):
            unresolved.append("invalid-or-artifactless-receipt:" + run)
            continue
        if kind == "live" and receipt.get("head_sha") != live[run]["head_sha"]:
            unresolved.append("head-mismatch:" + run)
            continue
        try:
            failures, collection_errors = oracle_failures(receipt, directory)
        except (OSError, KeyError, ValueError, ET.ParseError):
            unresolved.append("oracle-unavailable-or-mismatched:" + run)
            continue
        skipped = set(receipt["would_skip_test_files"])
        if skipped & set(receipt["selected_test_files"]) or (receipt["mode"] == "full" and skipped):
            unresolved.append("invalid-skip-set:" + run)
            continue
        if receipt["mode"] == "selected" and skipped:
            if kind == "injected":
                narrowed_injected += 1
            elif kind == "historical" or live[run]["pytest_red"] is True:
                narrowed_red += 1
        base = bases.get(run, {})
        base_ok = (base.get("artifact_problems") == [] and base.get("junit_hashes")
                   and base.get("head_sha") == receipt.get("base_sha") and bool(receipt.get("base_sha"))
                   and base.get("run_attempt") == 1 and base.get("identities", {}).get("tool_hashes") == tools
                   and instant(base["observed_at"]) >= registered)
        base_failures = set()
        if base_ok:
            try:
                base_failures, _ = oracle_failures(base, directory)
            except (OSError, KeyError, ValueError, ET.ParseError):
                unresolved.append("base-oracle-unavailable-or-mismatched:" + run)
                base_ok = False
        selected = set(receipt["selected_test_files"])
        for failure in sorted(failures | collection_errors):
            if failure.split("::", 1)[0] in selected:
                continue
            item = {"run_id": run, "test_id": failure}
            # Collection errors always count; a base-test exemption cannot hide a
            # collection failure outside the proposed suite.
            if failure not in collection_errors and base_ok and failure in base_failures:
                exemptions.append(item)
            else:
                misses.append(item)
    narrowed = narrowed_red + narrowed_injected
    if type(minimum_narrowed) is int and minimum_narrowed >= 1 and narrowed < minimum_narrowed:
        unresolved.append(f"narrowed-cases:{narrowed}/{minimum_narrowed}")
    stopped = instant(now or utc_now()) >= instant(registration["stop_at"])
    return {"status": "inconclusive" if unresolved and stopped else "unresolved" if unresolved else "fail" if misses else "pass",
            "registered_case_count": len(cases), "live_run_count": len(rows), "pytest_red_run_count": red,
            "narrowed_case_count": narrowed, "narrowed_red_case_count": narrowed_red,
            "narrowed_injected_case_count": narrowed_injected, "minimum_narrowed_cases": minimum_narrowed,
            "missed_failure_count": len(misses), "missed_failures": misses, "base_exemptions": exemptions,
            "unresolved_count": len(unresolved), "unresolved": unresolved, "day_30_stop": stopped}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute advisory selection and score full-run failures.\nUse before PR narrowing; this tool never executes tests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  $P -m scripts.ci.component_shadow select --base origin/main --head HEAD\n"
               "  $P -m scripts.ci.component_shadow register --baseline baseline.json --output registration.json\n"
               "  $P -m scripts.ci.component_shadow check --registration registration.json --receipts shadow/\n"
               "Outputs: ignored JSON registration/census/receipts; no test or Git mutations.\n"
               "Exit codes: 0 report-only or complete zero-miss check; 1 incomplete/missed; 2 invalid input.\n"
               "Related: #9721 slice 6; docs/runbooks/ci-gate.md. $P is the prescribed project interpreter.")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("select", "report", "register", "inventory", "check"):
        sub = commands.add_parser(command, help={"select": "Print would-run selection", "report": "Write an ignored receipt, always exit 0",
            "register": "Freeze denominators before candidate results", "inventory": "Acquire complete run/job metadata with gh",
            "check": "Score all registered live, historical and injected cases"}[command])
        if command in {"select", "report", "register"}:
            sub.add_argument("--root", type=Path, default=Path.cwd(), help="repository checkout (default: cwd)")
        if command in {"select", "report"}:
            sub.add_argument("--event", default="pull_request", help="event name (default: pull_request); other events select full")
            sub.add_argument("--base", default="", help="event base SHA (default: missing -> full)")
            sub.add_argument("--head", default="HEAD", help="event head SHA, never synthetic PR merge (default: HEAD)")
        if command in {"report", "register", "inventory"}:
            sub.add_argument("--output", type=Path, required=True, help="ignored JSON output path, e.g. ci-artifacts/shadow.json")
        if command == "report":
            sub.add_argument("--results", type=Path, required=True, help="downloaded full-run shard artifacts directory")
            sub.add_argument("--shards", type=int, default=16, help="full static shard count (default: 16)")
            sub.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "local"), help="run ID (default: GITHUB_RUN_ID or local)")
            sub.add_argument("--attempt", type=int, default=int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")), help="run attempt (default: GITHUB_RUN_ATTEMPT or 1)")
            sub.add_argument("--kind", choices=("live", "historical", "base", "injected"), default="live", help="case kind (default: live)")
            sub.add_argument("--candidate-run-id", default="", help="candidate ID for a pre-registered base rerun (default: none)")
            sub.add_argument("--cost", type=Path, help="matched PR+queue cost inputs JSON (default: unknown cost)")
            sub.add_argument("--cost-unknown-reason", default="matched-pr-queue-cost-inputs-not-supplied",
                             help="receipt reason when --cost is absent (default: matched-pr-queue-cost-inputs-not-supplied)")
        if command == "register":
            sub.add_argument("--baseline", type=Path, required=True, help="complete historical inventory JSON, acquired before replay")
            sub.add_argument("--minimum-narrowed-cases", type=int, default=1,
                             help="positive minimum of narrowed red/injected cases, frozen before results (default: 1)")
        if command == "inventory":
            sub.add_argument("--repository", default="learn-ukrainian/learn-ukrainian.github.io", help="GitHub owner/repo (default: project repository)")
            sub.add_argument("--created", default=BASELINE, help="inclusive API created range (default: plan baseline window)")
            sub.add_argument("--first-attempts", action="store_true", help="read attempt-1 run/jobs even after reruns (default: latest attempt; required for live census)")
        if command == "check":
            sub.add_argument("--registration", type=Path, required=True, help="pre-result registration JSON")
            sub.add_argument("--receipts", type=Path, required=True, help="receipt directory including complete live runs.json census")
    args = parser.parse_args(argv)
    try:
        if args.command == "select":
            result = select(args.base, args.head, args.event, args.root)
        elif args.command == "report":
            result = report(args)
        elif args.command == "inventory":
            result = inventory(args.repository, args.created, first_attempts=args.first_attempts)
            write_json(args.output, result)
        elif args.command == "register":
            result = register(json.loads(args.baseline.read_text()), args.root,
                              minimum_narrowed_cases=args.minimum_narrowed_cases)
            write_json(args.output, result, exclusive=True)
        else:
            result = check(json.loads(args.registration.read_text()), args.receipts)
            print(json.dumps(result, sort_keys=True))
            return int(result["unresolved_count"] > 0 or result["missed_failure_count"] > 0)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "unresolved", "error": str(exc)}))
        return 0 if args.command == "report" else 2


if __name__ == "__main__":
    raise SystemExit(main())
