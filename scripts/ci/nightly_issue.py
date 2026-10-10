"""Open, update or close one owned GitHub issue per failing scheduled job or test group.

Scheduled and nightly workflows call this as their last step (shared composite action
``.github/actions/nightly-issue``). A red run opens or comments on exactly one issue per
failing workflow (or per failing test group when JUnit reports are given). A green run
closes the issues it owns. Owners come from the path-to-lane map in
``.github/nightly-owners.json``. Every issue carries the ``nightly-failure`` label and a
``lane:<name>`` label (GitHub creates a missing label on issue creation).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common import github_client

LABEL = "nightly-failure"
TITLE_PREFIX = "[nightly]"
OWNERS_PATH = Path(".github/nightly-owners.json")

Runner = Callable[[Sequence[str]], str]


def gh(args: Sequence[str]) -> str:
    return github_client.run(["gh", *args], fresh=True, check=True, capture_output=True,
                             text=True, timeout=60).stdout


def load_owners(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("default"), str) or not isinstance(data.get("paths"), dict):
        raise ValueError(f"{path}: needs a 'default' lane and a 'paths' map")
    return data


def lane_for(path: str, owners: dict) -> str:
    """Longest matching path prefix wins; otherwise the default lane."""
    best = ""
    lane = owners["default"]
    for prefix, owner in owners["paths"].items():
        if path.startswith(prefix) and len(prefix) > len(best):
            best, lane = prefix, owner
    return lane


def group_for(test_path: str) -> str:
    """tests/<dir>/... -> tests/<dir>/ ; tests/test_<word>_x.py -> tests/test_<word>*."""
    parts = test_path.split("/")
    if len(parts) > 2 and parts[0] == "tests":
        return f"tests/{parts[1]}/"
    match = re.match(r"test_([a-z0-9]+)", parts[-1])
    return f"tests/test_{match.group(1)}*" if match else test_path


def _case_file(case: ET.Element) -> str | None:
    """Repository-relative test file of a testcase; absolute or odd paths give None."""
    name = case.get("file")
    if not name:
        parts = (case.get("classname") or "").split(".")
        for index, part in enumerate(parts):
            if part.startswith("test_"):
                name = "/".join(parts[: index + 1]) + ".py"
                break
    if not name or not name.startswith("tests/") or ".." in name.split("/"):
        return None
    return name


def failing_test_files(junit_paths: Iterable[Path]) -> set[str] | None:
    """Failing repository test files; None when a report is unreadable or a path is odd."""
    files: set[str] = set()
    for report in junit_paths:
        if not report.is_file():
            continue
        try:
            root = ET.parse(report).getroot()
        except ET.ParseError:
            return None
        for case in root.iter("testcase"):
            if case.find("failure") is None and case.find("error") is None:
                continue
            name = _case_file(case)
            if name is None:
                return None
            files.add(name)
    return files


_GROUP = re.compile(r"^tests/(?:[a-z0-9_]+/|test_[a-z0-9]+\*)$")
_RUN_URL = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[0-9]+$")
_KEY = re.compile(r"^[a-z0-9_-]{1,60}\.ya?ml$")
_LANE = re.compile(r"^[a-z0-9-]{1,40}$")


def approved_groups(root: Path) -> set[str]:
    """The approved vocabulary: groups of test files tracked in this public checkout."""
    tests = root / "tests"
    if not tests.is_dir():
        return set()
    groups = {group_for(path.relative_to(root).as_posix()) for path in tests.rglob("test_*.py")}
    return {group for group in groups if _GROUP.match(group)}


def safe_groups(files: Iterable[str] | None, approved: set[str]) -> set[str] | None:
    """Groups only from the approved vocabulary; None means report at workflow level.

    Public issue text is built only from the workflow file name, approved groups (names
    already public in this repository's tree), the owner-map lane and a validated run
    URL. The shared publisher needs the private OPSEC matcher, which Actions runners do
    not have, so free text never reaches a public title or body instead.
    """
    if files is None:
        return None
    groups = {group_for(f) for f in files}
    return groups if groups and groups <= approved else None


def title_for(key: str, group: str | None) -> str:
    return f"{TITLE_PREFIX} {key}: {group} failing" if group else f"{TITLE_PREFIX} {key} failing"


def open_issues(run: Runner, key: str) -> dict[str, int]:
    out = run(["issue", "list", "--state", "open", "--label", LABEL, "--limit", "1000",
               "--search", f'in:title "{TITLE_PREFIX} {key}"', "--json", "number,title"])
    prefix = f"{TITLE_PREFIX} {key}"
    return {i["title"]: i["number"] for i in json.loads(out or "[]")
            if i["title"] == f"{prefix} failing" or i["title"].startswith(f"{prefix}: ")}


def report(run: Runner, *, key: str, status: str, run_url: str, owners: dict,
           junit: Sequence[Path] = (), workflow_path: str = "",
           root: Path = Path(".")) -> list[str]:
    """Return a list of actions taken (for logs and tests).

    A failed run opens or comments; it never closes anything. Only a successful run
    (positive recovery evidence) closes this workflow's issues.
    """
    for value, pattern in ((key, _KEY), (run_url, _RUN_URL)):
        if not pattern.match(value):
            raise ValueError("refusing unexpected key or run URL")
    actions: list[str] = []
    existing = open_issues(run, key)
    if status == "success":
        for title, number in existing.items():
            run(["issue", "close", str(number), "--comment", f"Green again: {run_url}"])
            actions.append(f"close #{number} {title}")
        return actions
    wanted: dict[str, str] = {}
    groups = safe_groups(failing_test_files(junit), approved_groups(root))
    if groups:
        for group in sorted(groups):
            wanted[title_for(key, group)] = lane_for(group.rstrip("*"), owners)
    else:
        wanted[title_for(key, None)] = lane_for(workflow_path or key, owners)
    for title, lane in wanted.items():
        if not _LANE.match(lane):
            raise ValueError("refusing unexpected lane")
        body = f"Scheduled run failed: {run_url}\n\nOwner: lane `{lane}`. Closes automatically when green."
        if title in existing:
            run(["issue", "comment", str(existing[title]), "--body", body])
            actions.append(f"comment #{existing[title]} {title}")
        else:
            run(["issue", "create", "--title", title, "--label", LABEL, "--label", f"lane:{lane}",
                 "--body", body])
            actions.append(f"create {title}")
    return actions


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--key", required=True, help="workflow file name, e.g. zizmor.yml")
    parser.add_argument("--status", required=True, help="job status: success, failure, cancelled")
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--workflow-path", default="")
    parser.add_argument("--junit", nargs="*", default=[], type=Path)
    parser.add_argument("--owners", default=OWNERS_PATH, type=Path)
    args = parser.parse_args(argv)
    if args.status not in {"success", "failure"}:
        print(f"{args.status} run: no issue change")
        return 0
    for line in report(gh, key=args.key, status=args.status, run_url=args.run_url,
                       owners=load_owners(args.owners), junit=args.junit,
                       workflow_path=args.workflow_path):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
