"""One pytest JUnit reader for CI failure summaries and the flake ledger."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree


@dataclass(frozen=True)
class TestResult:
    node_id: str
    outcome: str
    message: str
    reruns: int
    source: Path


def parse_junit(paths: list[Path]) -> list[TestResult]:
    """Read pytest xunit2 files; reject unrecognised/missing node identities.

    `outcome` is passed, failed, error, or skipped. The `flake.reruns`
    testcase property records a first-attempt failure followed by success.
    This API is shared with #9063's failing-test summary.
    """
    results: list[TestResult] = []
    for path in paths:
        root = ElementTree.parse(path).getroot()
        if root.tag not in ("testsuite", "testsuites"):
            raise ValueError(f"{path}: not JUnit XML")
        by_node: dict[str, TestResult] = {}
        for case in root.iter("testcase"):
            file = case.get("file")
            name = case.get("name")
            classname = case.get("classname", "")
            if not name:
                raise ValueError(f"{path}: testcase lacks pytest name")
            # pytest emits collection errors with an empty classname and a
            # dotted module path in name (the CI shard JUnit family).
            node_id = (name.replace(".", "/") + ".py" if "." in name else name) if not classname else ""
            if classname and not file:
                parts = classname.split(".")
                class_start = next((index for index, part in enumerate(parts) if part.startswith("Test")), len(parts))
                module_parts = parts[:class_start]
                if not module_parts:
                    raise ValueError(f"{path}: testcase lacks pytest module identity")
                file = "/".join(module_parts) + ".py"
            if classname and not file.endswith(".py"):
                raise ValueError(f"{path}: testcase lacks pytest file identity")
            if classname:
                module = file[:-3].replace("/", ".")
                suffix = classname.removeprefix(module).lstrip(".")
                node_id = "::".join((file, *(suffix.split(".") if suffix else ()), name))
            children = {tag: case.find(tag) for tag in ("error", "failure", "skipped")}
            raw_outcome = next((tag for tag in ("error", "failure", "skipped") if children[tag] is not None), "passed")
            outcome = "failed" if raw_outcome == "failure" else raw_outcome
            detail = children[raw_outcome] if raw_outcome != "passed" else None
            message = ((detail.get("message", "") or detail.text or "") if detail is not None else "").strip()
            properties = {prop.get("name"): prop.get("value") for prop in case.findall("./properties/property")}
            rerun_raw = properties.get("flake.reruns", "0")
            try:
                reruns = int(rerun_raw)
            except ValueError as exc:
                raise ValueError(f"{path}: invalid flake.reruns property") from exc
            if reruns < 0:
                raise ValueError(f"{path}: negative flake.reruns property")
            by_node[node_id] = TestResult(node_id, outcome, message, reruns, path)
        results.extend(by_node.values())
    return results
