"""Open, update or close one owned GitHub issue per failing scheduled job or test group.

Scheduled and nightly workflows call this as their last step (shared composite action
``.github/actions/nightly-issue``). A red run opens or comments on exactly one issue per
failing workflow (or per failing test group when JUnit reports are given). A green run
closes the issues it owns. Owners come from the path-to-lane map in
``.github/nightly-owners.json``. Every issue carries the ``nightly-failure`` label and a
``lane:<name>`` label.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

LABEL = "nightly-failure"
TITLE_PREFIX = "[nightly]"
OWNERS_PATH = Path(".github/nightly-owners.json")

Runner = Callable[[Sequence[str]], str]


def gh(args: Sequence[str]) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True,
                          timeout=60).stdout


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


def failing_test_files(junit_paths: Iterable[Path]) -> set[str]:
    files: set[str] = set()
    for report in junit_paths:
        if not report.is_file():
            continue
        for case in ET.parse(report).getroot().iter("testcase"):
            if case.find("failure") is None and case.find("error") is None:
                continue
            name = case.get("file") or (case.get("classname") or "").replace(".", "/") + ".py"
            if name:
                files.add(name if name.startswith("tests/") else f"tests/{name.split('tests/')[-1]}")
    return files


def title_for(key: str, group: str | None) -> str:
    return f"{TITLE_PREFIX} {key}: {group} failing" if group else f"{TITLE_PREFIX} {key} failing"


def open_issues(run: Runner, key: str) -> dict[str, int]:
    out = run(["issue", "list", "--state", "open", "--label", LABEL, "--limit", "200",
               "--json", "number,title"])
    prefix = f"{TITLE_PREFIX} {key}"
    return {i["title"]: i["number"] for i in json.loads(out or "[]")
            if i["title"] == f"{prefix} failing" or i["title"].startswith(f"{prefix}: ")}


def report(run: Runner, *, key: str, status: str, run_url: str, owners: dict,
           junit: Sequence[Path] = (), workflow_path: str = "") -> list[str]:
    """Return a list of actions taken (for logs and tests)."""
    actions: list[str] = []
    existing = open_issues(run, key)
    wanted: dict[str, str] = {}
    if status != "success":
        groups = sorted({group_for(f) for f in failing_test_files(junit)})
        if groups:
            for group in groups:
                wanted[title_for(key, group)] = lane_for(group.rstrip("*"), owners)
        else:
            wanted[title_for(key, None)] = lane_for(workflow_path or key, owners)
    for title, lane in wanted.items():
        body = f"Scheduled run failed: {run_url}\n\nOwner: lane `{lane}`. Closes automatically when green."
        if title in existing:
            run(["issue", "comment", str(existing[title]), "--body", body])
            actions.append(f"comment #{existing[title]} {title}")
        else:
            for label in (LABEL, f"lane:{lane}"):
                run(["label", "create", label, "--force", "--description", "Nightly failure routing"])
            run(["issue", "create", "--title", title, "--label", LABEL, "--label", f"lane:{lane}",
                 "--body", body])
            actions.append(f"create {title}")
    if status == "success" or wanted:
        for title, number in existing.items():
            if title not in wanted:
                run(["issue", "close", str(number), "--comment", f"Green again: {run_url}"])
                actions.append(f"close #{number} {title}")
    return actions


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--key", required=True, help="workflow name")
    parser.add_argument("--status", required=True, help="job status: success, failure, cancelled")
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--workflow-path", default="")
    parser.add_argument("--junit", nargs="*", default=[], type=Path)
    parser.add_argument("--owners", default=OWNERS_PATH, type=Path)
    args = parser.parse_args(argv)
    if args.status == "cancelled":
        print("cancelled run: no issue change")
        return 0
    for line in report(gh, key=args.key, status=args.status, run_url=args.run_url,
                       owners=load_owners(args.owners), junit=args.junit,
                       workflow_path=args.workflow_path):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
