"""Run the audited data-gated tests in an isolated host worktree.

Use the nightly systemd timer after installation, or run a no-report subset to
check host provisioning. This module never edits the primary checkout.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

from scripts.orchestration.dispatch_isolation import _parse_bytes, build_scope_argv

SOURCE_ROOT = Path(__file__).resolve().parents[2]
SELECTION = Path(__file__).with_name("data_tier_selection.json")
BASELINE = Path(__file__).with_name("data_tier_known_failures.json")
ISSUE_TITLE = "[infra][tests] Nightly data-tier failures"
MIN_AVAILABLE_BYTES = 6 * 1024**3
RUN_BUDGET_SECONDS = 7 * 3600
HYDRATION_BUDGET_SECONDS = 3600
ISSUE_BODY_LIMIT = 60000
HOST_DATABASES = ("sources.db", "vesum.db", "atlas.db", "ulif_dump_all.db")
ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9])/(?!/)[^\s\]\[),:;]+")
NETWORK_ADDRESS = re.compile(r"https?://[^\s\]\[),:;]+|(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")


class DataTierError(RuntimeError):
    """Nightly data-tier run cannot produce trustworthy results."""


def safe_text(value: str) -> str:
    """Keep private host paths out of persisted receipts and GitHub bodies."""
    value = value.replace(socket.gethostname(), "<host>")
    value = NETWORK_ADDRESS.sub("<network-address>", value)
    return ABSOLUTE_PATH.sub("<host-path>", value)


def command(argv: list[str], *, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise DataTierError(f"{argv[0]} failed ({result.returncode}): {safe_text(result.stderr.strip())}")
    return result


def run_process_group(
    argv: list[str],
    *,
    timeout: int,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    stdout: object | None = None,
) -> int:
    """Wait in the foreground and stop descendants if a whole-run bound expires."""
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdout=stdout,
        stderr=subprocess.STDOUT if stdout else None,
        start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout)
    except BaseException as error:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
        if isinstance(error, subprocess.TimeoutExpired):
            raise DataTierError(f"command timed out after {timeout} seconds") from error
        raise


def primary_checkout() -> Path:
    common = command(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=SOURCE_ROOT).stdout.strip()
    primary = Path(common).resolve().parent
    if not (primary / ".git").is_dir():
        raise DataTierError("Git common directory does not identify a primary checkout")
    return primary


def load_selection() -> dict:
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    ids = selection["nodeids"]
    if selection["schema"] != 1 or len(ids) != selection["class_c_merge_group"] or len(ids) != len(set(ids)):
        raise DataTierError("data-tier selection count or uniqueness differs from the audited class C")
    if not all(path.startswith("tests/") and path.endswith(".py") for path in selection["files"]):
        raise DataTierError("data-tier selection contains an invalid test file")
    return selection


def available_memory() -> int:
    for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise DataTierError("MemAvailable is unavailable")


def require_memory() -> None:
    available = available_memory()
    if available < MIN_AVAILABLE_BYTES:
        raise DataTierError(f"MemAvailable {available // 1024**2} MiB is below the 6 GiB floor")
    slice_state = command(
        ["systemctl", "--user", "show", "-p", "LoadState,ActiveState,MemoryCurrent,MemoryMax", "lu-dispatch.slice"],
        cwd=SOURCE_ROOT,
    ).stdout
    properties = dict(line.split("=", 1) for line in slice_state.splitlines() if "=" in line)
    if properties.get("LoadState") != "loaded":
        raise DataTierError("lu-dispatch.slice is unavailable")
    if properties.get("ActiveState") == "inactive":
        return
    current = _parse_bytes(properties.get("MemoryCurrent"))
    maximum = _parse_bytes(properties.get("MemoryMax"))
    if current is None or (maximum is None and properties.get("MemoryMax") != "infinity"):
        raise DataTierError("lu-dispatch.slice memory headroom is unknown")
    if maximum is not None and maximum - current < 4 * 1024**3:
        raise DataTierError("lu-dispatch.slice has less than 4 GiB headroom")


def prune_stale_worktrees(primary: Path) -> None:
    """Reap abandoned nightly checkouts only when no nightly scope is active."""
    parent = primary / ".worktrees" / "data-tier"
    if not parent.is_dir():
        return
    scopes = command(
        ["systemctl", "--user", "list-units", "--type=scope", "--state=active", "--no-legend", "lu-data-tier-*"],
        cwd=SOURCE_ROOT,
    ).stdout
    if scopes.strip():
        raise DataTierError("a previous data-tier scope is still active; cleanup withheld")
    for checkout in parent.glob("run-*"):
        if checkout.is_symlink() or not checkout.is_dir() or not re.fullmatch(r"run-[0-9a-f]{32}", checkout.name):
            continue
        # Leave a concurrent or recently interrupted runner's checkout alone.
        if time.time() - checkout.stat().st_mtime < 9 * 3600:
            continue
        remove_test_worktree(primary, checkout)


def remove_test_worktree(primary: Path, checkout: Path) -> None:
    command(
        ["git", "--git-dir", str(primary / ".git"), "worktree", "remove", "--force", str(checkout)],
        cwd=primary / ".worktrees" / "data-tier",
        timeout=600,
    )


def stop_scope(unit: str) -> None:
    result = subprocess.run(
        ["systemctl", "--user", "show", "-p", "LoadState", unit],
        cwd=SOURCE_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if "LoadState=not-found" in result.stdout:
        return
    if result.returncode:
        raise DataTierError(f"scope state unavailable: {safe_text(result.stderr)}")
    command(["systemctl", "--user", "stop", unit], cwd=SOURCE_ROOT, timeout=60)


def make_test_worktree(primary: Path) -> Path:
    # Use Git's common directory only to register a new linked checkout. All
    # code freshness operations happen from that checkout, never from primary.
    git_dir = primary / ".git"
    parent = primary / ".worktrees" / "data-tier"
    parent.mkdir(parents=True, exist_ok=True)
    path = parent / f"run-{uuid.uuid4().hex}"
    command(
        ["git", "--git-dir", str(git_dir), "worktree", "add", "--detach", str(path), "origin/main"],
        cwd=parent,
        timeout=300,
    )
    try:
        command(["git", "fetch", "--no-tags", "origin", "main"], cwd=path, timeout=300)
        command(["git", "reset", "--hard", "origin/main"], cwd=path, timeout=300)
        command(["git", "sparse-checkout", "disable"], cwd=path, timeout=300)
        if command(["git", "status", "--porcelain"], cwd=path).stdout.strip():
            raise DataTierError("new data-tier checkout is not clean")
    except BaseException:
        command(["git", "--git-dir", str(git_dir), "worktree", "remove", "--force", str(path)], cwd=parent, timeout=600)
        raise
    return path


def snapshot_databases(primary: Path, checkout: Path, *, only: str | None) -> list[str]:
    names = ("sources.db",) if only else HOST_DATABASES
    missing = []
    target_dir = checkout / "data"
    target_dir.mkdir(exist_ok=True)
    for name in names:
        source = primary / "data" / name
        if not source.is_file():
            missing.append(name)
            continue
        target = target_dir / name
        # SQLite's online backup gives a consistent snapshot even if ingestion
        # has left a WAL beside the primary database. The source is read-only.
        with (
            contextlib.closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=30)) as reader,
            contextlib.closing(sqlite3.connect(target)) as writer,
        ):
            reader.backup(writer, pages=1024, sleep=0.1)
    return missing


def provision_host_files(primary: Path, checkout: Path) -> None:
    for relative in (
        "data/ua-gec",
        "data/literary_texts",
        "data/external_articles",
        "site/public/lexicon",
    ):
        source = primary / relative
        target = checkout / relative
        if not source.is_dir():
            continue
        for file in source.rglob("*"):
            if not file.is_file() or file.is_symlink():
                continue
            destination = target / file.relative_to(source)
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, destination)


def hydrate(checkout: Path, groups: list[str], project_python: Path) -> dict[str, str]:
    failures = {}
    deadline = time.monotonic() + HYDRATION_BUDGET_SECONDS
    for group in groups:
        remaining = int(deadline - time.monotonic())
        if remaining <= 0:
            failures[group] = "hydration budget exhausted"
            continue
        try:
            result = subprocess.run(
                [str(project_python), "-m", "scripts.storage.artifacts", "hydrate", "--group", group],
                cwd=checkout,
                capture_output=True,
                text=True,
                check=False,
                timeout=min(1800, remaining),
            )
        except subprocess.TimeoutExpired:
            failures[group] = "hydration timed out"
            continue
        if result.returncode:
            detail = (result.stderr or result.stdout).strip().splitlines()
            failures[group] = safe_text(detail[-1] if detail else f"hydrate exited {result.returncode}")
    return failures


def bulk_status(checkout: Path, project_python: Path) -> tuple[str | None, str]:
    result = subprocess.run(
        [str(project_python), "-m", "scripts.storage", "status", "--json"],
        cwd=checkout,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if result.returncode:
        return None, "storage status unavailable"
    try:
        bulk = json.loads(result.stdout)["bulk_root"]
    except (ValueError, KeyError, TypeError):
        return None, "storage status invalid"
    if not bulk.get("available") or not bulk.get("path"):
        return None, str(bulk.get("reason") or "bulk root unavailable")
    return str(bulk["path"]), str(bulk.get("reason") or "available")


def _key(nodeid: str) -> str:
    return "sha256:" + hashlib.sha256(nodeid.encode()).hexdigest()


class SelectionPlugin:
    def __init__(self, selection: dict, only: str | None, bulk_reason: str | None, collected: Path) -> None:
        self.selection = selection
        self.only = only
        self.bulk_reason = bulk_reason
        self.collected = collected
        self.selected_nodeids: list[str] = []
        self.bulk_skipped: list[str] = []
        self.collection_skips: list[tuple[str, str]] = []
        self.collection_errors: list[tuple[str, str]] = []

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self.collection_errors.append((report.nodeid, safe_text(str(report.longrepr))))
        if report.skipped and report.nodeid in self.selection["nodeids"]:
            detail = report.longrepr[2] if isinstance(report.longrepr, tuple) else str(report.longrepr)
            self.collection_skips.append((report.nodeid, safe_text(str(detail))))

    def pytest_collection_modifyitems(self, items: list[pytest.Item], config: pytest.Config) -> None:
        wanted = set(self.selection["nodeids"])
        bulk = set(self.selection.get("bulk_nodeids", []))
        selected, deselected = [], []
        for item in items:
            nodeid = item.nodeid
            key = _key(nodeid)
            file = nodeid.split("::", 1)[0]
            keep = (nodeid in wanted or key in wanted or file in wanted) and (self.only is None or file == self.only)
            if any(item.get_closest_marker(marker) for marker in ("live_network", "live_github", "postgres")):
                keep = False
            if keep:
                if self.bulk_reason and (nodeid in bulk or key in bulk):
                    self.bulk_skipped.append(nodeid)
                    deselected.append(item)
                else:
                    selected.append(item)
            else:
                deselected.append(item)
        items[:] = selected
        config.hook.pytest_deselected(items=deselected)
        self.selected_nodeids = [item.nodeid for item in selected]
        self.collected.write_text(json.dumps([safe_text(item.nodeid) for item in selected]), encoding="utf-8")


def pytest_child(args: argparse.Namespace) -> int:
    selection = load_selection()
    plugin = SelectionPlugin(selection, args.only, args.bulk_reason, Path(args.collected))
    files = [args.only] if args.only else selection["files"]
    collection_status = pytest.main(
        ["--collect-only", "--continue-on-collection-errors", "-q", *files], plugins=[plugin]
    )
    if collection_status not in (0, 1, 5) or (collection_status == 1 and not plugin.collection_errors):
        return int(collection_status)
    if (
        not plugin.selected_nodeids
        and not plugin.bulk_skipped
        and not plugin.collection_skips
        and not plugin.collection_errors
    ):
        raise DataTierError("the audited selection collected no tests")
    if plugin.selected_nodeids:
        status = run_process_group(
            [
                sys.executable,
                "-m",
                "pytest",
                "-n",
                "2",
                "--timeout=180",
                "--timeout-method=thread",
                "-q",
                "-r",
                "s",
                f"--junitxml={args.junit}",
                *plugin.selected_nodeids,
            ],
            timeout=21600,
        )
    else:
        ET.ElementTree(ET.Element("testsuite")).write(args.junit, encoding="utf-8", xml_declaration=True)
        status = 0
    if plugin.bulk_skipped or plugin.collection_skips or plugin.collection_errors:
        tree = ET.parse(args.junit)
        suite = next(tree.iter("testsuite"))
        for nodeid in plugin.bulk_skipped:
            case = ET.SubElement(suite, "testcase", classname="data_tier", name=safe_text(nodeid))
            ET.SubElement(case, "skipped", message=f"bulk root unavailable: {safe_text(args.bulk_reason)}")
        for nodeid, reason in plugin.collection_skips:
            case = ET.SubElement(suite, "testcase", classname="data_tier", name=safe_text(nodeid))
            ET.SubElement(case, "skipped", message=reason)
        for nodeid, reason in plugin.collection_errors:
            case = ET.SubElement(suite, "testcase", classname="data_tier", name=safe_text(nodeid))
            ET.SubElement(case, "error", message=reason)
        skipped = len(plugin.bulk_skipped) + len(plugin.collection_skips)
        added = skipped + len(plugin.collection_errors)
        for element in {tree.getroot(), suite}:
            if element.tag in {"testsuite", "testsuites"}:
                element.set("tests", str(int(element.get("tests", "0")) + added))
                element.set("skipped", str(int(element.get("skipped", "0")) + skipped))
                element.set("errors", str(int(element.get("errors", "0")) + len(plugin.collection_errors)))
        tree.write(args.junit, encoding="utf-8", xml_declaration=True)
    return status or (1 if plugin.collection_errors else 0)


def sanitize_junit(path: Path) -> None:
    tree = ET.parse(path)
    for element in tree.iter():
        element.attrib.update({key: safe_text(value) for key, value in element.attrib.items()})
        if element.text:
            element.text = safe_text(element.text)
        if element.tail:
            element.tail = safe_text(element.tail)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def junit_summary(path: Path) -> dict:
    counts = Counter()
    reasons = Counter()
    failures = []
    for case in ET.parse(path).iter("testcase"):
        counts["ran"] += 1
        classname = case.attrib.get("classname", "")
        parts = classname.split(".")
        stem = next((index for index, part in enumerate(parts) if part.startswith("test_")), None)
        if stem is None:
            nodeid = case.attrib.get("name", "")
        else:
            file = "/".join(parts[: stem + 1]) + ".py"
            nodeid = "::".join([file, *parts[stem + 1 :], case.attrib.get("name", "")])
        if case.find("failure") is not None or case.find("error") is not None:
            counts["failed"] += 1
            failures.append(safe_text(nodeid))
        elif (skipped := case.find("skipped")) is not None:
            counts["skipped"] += 1
            reasons[safe_text(skipped.attrib.get("message", "unspecified").splitlines()[0])] += 1
        else:
            counts["passed"] += 1
    return {
        "ran": counts["ran"],
        "passed": counts["passed"],
        "failed": counts["failed"],
        "skipped": counts["skipped"],
        "skip_reasons": dict(reasons.most_common()),
        "failing_tests": sorted(set(failures)),
    }


def known_issue(nodeid: str, baseline: dict[str, int]) -> int | None:
    return baseline.get(nodeid)


def issue_body(summary: dict, baseline: dict[str, int]) -> str:
    lines = [
        "Nightly data-tier run failed.",
        "",
        f"Run: `{safe_text(summary['run_key'])}` at `{safe_text(summary['main_sha'])}`.",
        f"Ran {summary['ran']}; passed {summary['passed']}; failed {summary['failed']}; skipped {summary['skipped']}.",
    ]
    lines.extend(["", f"Runner errors ({len(summary.get('runner_errors', []))}):"])
    lines.extend(f"- {safe_text(reason)}" for reason in summary.get("runner_errors", []))
    lines.extend(["", f"Hydration errors ({len(summary.get('hydration_errors', {}))}):"])
    lines.extend(
        f"- {safe_text(group)}: {safe_text(reason)}" for group, reason in summary.get("hydration_errors", {}).items()
    )
    lines.extend(["", f"Missing databases ({len(summary.get('missing_databases', []))}):"])
    lines.extend(f"- {safe_text(name)}" for name in summary.get("missing_databases", []))
    lines.extend(["", f"Failing tests ({len(summary['failing_tests'])} total):"])
    for nodeid in summary["failing_tests"]:
        issue = known_issue(nodeid, baseline)
        lines.append(f"- `{safe_text(nodeid)}`" + (f" — known issue #{issue}" if issue else " — new"))
    lines.extend(["", "Skipped by reason:"])
    lines.extend(f"- {count}: {safe_text(reason)}" for reason, count in summary["skip_reasons"].items())
    footer = "\nFull details: local run JUnit, log and JSON summary (named by run key).\n"
    body = ""
    for index, line in enumerate(lines):
        clipped = line[:1024] + (" … [detail truncated]" if len(line) > 1024 else "")
        if len(body) + len(clipped) + len(footer) + 100 > ISSUE_BODY_LIMIT:
            body += f"\n[Truncated: {len(lines) - index} remaining report lines; see local receipts.]\n"
            break
        body += clipped + "\n"
    return body + footer


def run_failed(summary: dict) -> bool:
    return bool(
        summary["failed"]
        or summary.get("pytest_exit")
        or summary.get("runner_errors")
        or summary.get("hydration_errors")
        or summary.get("missing_databases")
    )


def _gh(args: list[str], *, input_text: str | None = None) -> str:
    result = subprocess.run(["gh", *args], input=input_text, capture_output=True, text=True, check=False, timeout=90)
    if result.returncode:
        raise DataTierError(f"gh failed ({result.returncode}): {safe_text(result.stderr.strip())}")
    return result.stdout


def report(summary: dict, baseline: dict[str, int]) -> str:
    issues = json.loads(
        _gh(
            [
                "issue",
                "list",
                "--state",
                "all",
                "--search",
                "Nightly data-tier failures in:title",
                "--limit",
                "100",
                "--json",
                "number,title,state",
            ]
        )
    )
    matching = [issue for issue in issues if issue["title"] == ISSUE_TITLE]
    if len(matching) > 1:
        raise DataTierError("multiple data-tier failure issues have the stable title")
    issue = matching[0] if matching else None
    if run_failed(summary):
        body = issue_body(summary, baseline)
        if issue:
            if issue["state"] != "OPEN":
                _gh(["issue", "reopen", str(issue["number"])])
            _gh(["issue", "edit", str(issue["number"]), "--body-file", "-"], input_text=body)
            return f"updated issue #{issue['number']}"
        created = _gh(
            ["issue", "create", "--title", ISSUE_TITLE, "--label", "infra", "--body-file", "-"], input_text=body
        )
        return f"created {created.strip()}"
    if issue and issue["state"] == "OPEN":
        comments = json.loads(_gh(["issue", "view", str(issue["number"]), "--json", "comments"]))["comments"]
        marker = f"Data-tier clean run `{summary['run_key']}`"
        if not any(marker in comment["body"] for comment in comments):
            _gh(
                [
                    "issue",
                    "comment",
                    str(issue["number"]),
                    "--body",
                    marker + f": {summary['passed']} passed, {summary['skipped']} skipped.",
                ]
            )
        _gh(["issue", "close", str(issue["number"])])
        return f"closed issue #{issue['number']} after clean run"
    return "no issue change"


def run(args: argparse.Namespace) -> int:
    started = dt.datetime.now(dt.UTC)
    run_key = started.strftime("%Y%m%dT%H%M%S") + f"-{uuid.uuid4().hex[:8]}Z"
    deadline = time.monotonic() + RUN_BUDGET_SECONDS
    summary = {
        "run_key": run_key,
        "main_sha": "unavailable",
        "ran": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "collected": 0,
        "pytest_exit": None,
        "failing_tests": [],
        "skip_reasons": {},
        "runner_errors": [],
        "hydration_errors": {},
        "missing_databases": [],
    }
    baseline = {}
    primary = checkout = output_dir = log = scope_unit = None
    try:
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))["known_failures"]
        selection = load_selection()
        if args.only and args.only not in selection["files"]:
            raise DataTierError("--only must name a file in the audited selection")
        if args.only and not args.no_report:
            raise DataTierError("a subset requires --no-report")
        primary = primary_checkout()
        output_dir = primary / "batch_state" / "data-tier"
        output_dir.mkdir(parents=True, exist_ok=True)
        junit = output_dir / f"{run_key}.junit.xml"
        collected = output_dir / f"{run_key}.collected.json"
        log = output_dir / f"{run_key}.log"
        require_memory()
        project_python = primary / ".venv" / "bin" / "python"
        if not project_python.is_file():
            raise DataTierError("shared project interpreter unavailable")
        prune_stale_worktrees(primary)
        checkout = make_test_worktree(primary)
        summary["main_sha"] = command(["git", "rev-parse", "HEAD"], cwd=checkout).stdout.strip()
        summary["missing_databases"] = snapshot_databases(primary, checkout, only=args.only)
        if not args.only:
            provision_host_files(primary, checkout)
        summary["hydration_errors"] = (
            hydrate(checkout, selection["artifact_groups"], project_python) if not args.only else {}
        )
        bulk_root, bulk_reason = bulk_status(checkout, project_python)
        summary["bulk_status"] = "available" if bulk_root else f"unavailable: {safe_text(bulk_reason)}"
        require_memory()
        child = [
            str(project_python),
            "-m",
            "scripts.ci.data_tier",
            "pytest-child",
            "--junit",
            str(junit),
            "--collected",
            str(collected),
        ]
        if args.only:
            child.extend(["--only", args.only])
        if not bulk_root:
            child.extend(["--bulk-reason", bulk_reason])
        remaining = int(deadline - time.monotonic())
        if remaining <= 0:
            raise DataTierError("whole-run budget exhausted before pytest")
        scope_unit = f"lu-data-tier-{run_key}.scope"
        scope = build_scope_argv(["nice", "-n", "10", *child], unit=scope_unit)
        environment = os.environ.copy()
        if bulk_root:
            environment["LU_BULK_ROOT"] = bulk_root
        else:
            environment.pop("LU_BULK_ROOT", None)
        with log.open("w", encoding="utf-8") as stream:
            pytest_exit = run_process_group(scope, cwd=checkout, env=environment, stdout=stream, timeout=remaining)
        summary["pytest_exit"] = pytest_exit
        if not junit.exists():
            raise DataTierError(f"pytest produced no JUnit (exit {pytest_exit}); inspect local run log")
        sanitize_junit(junit)
        summary.update(junit_summary(junit))
        summary.update(
            {
                "run_key": run_key,
                "pytest_exit": pytest_exit,
                "selection_cases": selection["class_c_merge_group"],
                "collected": len(json.loads(collected.read_text())) if collected.exists() else 0,
            }
        )
        if pytest_exit and not summary["failed"]:
            summary["runner_errors"].append(f"pytest exited {pytest_exit} without testcase failures")
    except Exception as error:
        summary["runner_errors"].append(safe_text(str(error)))
    finally:
        # The scope is outside the service cgroup: stop it before removing its
        # checkout, including when SIGTERM interrupts the waiting parent.
        scope_stopped = True
        if scope_unit:
            try:
                stop_scope(scope_unit)
            except Exception as error:
                scope_stopped = False
                summary["runner_errors"].append(f"scope cleanup failed: {safe_text(str(error))}")
        if checkout and scope_stopped:
            try:
                remove_test_worktree(primary, checkout)
            except Exception as error:
                summary["runner_errors"].append(f"checkout cleanup failed: {safe_text(str(error))}")
        if log and log.exists():
            try:
                log.write_text(safe_text(log.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
            except Exception as error:
                summary["runner_errors"].append(f"log sanitization failed: {safe_text(str(error))}")

    def persist() -> None:
        if output_dir:
            try:
                (output_dir / f"{run_key}.summary.json").write_text(
                    json.dumps(summary, indent=2, sort_keys=True) + "\n"
                )
            except Exception as error:
                summary["runner_errors"].append(f"summary write failed: {safe_text(str(error))}")

    persist()
    if not args.no_report:
        for _attempt in range(2):
            if _attempt:
                persist()
            try:
                print(report(summary, baseline))
                break
            except Exception as error:
                summary["runner_errors"].append(f"GitHub reporting failed: {safe_text(str(error))}")
        else:
            persist()
    print(json.dumps(summary, sort_keys=True))
    return 1 if run_failed(summary) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the audited class-C data-tier tests from a fresh origin/main worktree.\n"
            "Use for the nightly host run; use --only with --no-report for a bounded manual check."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  <project-python> -m scripts.ci.data_tier run\n"
            "  <project-python> -m scripts.ci.data_tier run --only tests/test_citation_resolution_invariant.py --no-report\n"
            "Outputs: JUnit, run log, collection receipt and JSON summary under batch_state/data-tier/.\n"
            "Exit codes: 0 = tests passed; 1 = tests failed or run incomplete; 2 = invalid usage.\n"
            "Related: issues #9229, #9218 and #8403."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", help="Run the audited selection and optionally report to GitHub.")
    run_parser.add_argument(
        "--only", help="Run one selected test file for a manual smoke check (default: full selection)."
    )
    run_parser.add_argument(
        "--no-report", action="store_true", help="Do not create or update a GitHub issue (default: report)."
    )
    child = sub.add_parser("pytest-child", help="Internal subprocess executed inside the dispatch slice.")
    child.add_argument("--junit", required=True, help="JUnit output file path.")
    child.add_argument("--collected", required=True, help="Selected collection receipt path.")
    child.add_argument("--only", help="Selected file path for a manual subset.")
    child.add_argument("--bulk-reason", help="Host bulk-root unavailability reason.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    def interrupted(signum: int, _frame: object) -> None:
        raise DataTierError(f"run interrupted by signal {signum}")

    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        return pytest_child(args) if args.command == "pytest-child" else run(args)
    except (DataTierError, OSError, subprocess.TimeoutExpired, sqlite3.Error) as error:
        print(f"data-tier: {safe_text(str(error))}", file=sys.stderr)
        return 1
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    raise SystemExit(main())
