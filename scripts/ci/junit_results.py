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


SUMMARY_ROW_CAP = 50
_MESSAGE_LIMIT = 200
_TEST_ID_LIMIT = 300


def _cell(text: str) -> str:
    """Make text safe inside one GitHub-flavoured Markdown table cell."""
    for raw, safe in (("\\", "\\\\"), ("|", "\\|"), ("`", "\\`"), ("<", "&lt;"), (">", "&gt;")):
        text = text.replace(raw, safe)
    return text


def _first_line(message: str) -> str:
    line = next((line.strip() for line in message.splitlines() if line.strip()), "")
    return line if len(line) <= _MESSAGE_LIMIT else line[: _MESSAGE_LIMIT - 1] + "…"


def _test_id_cell(node_id: str) -> str:
    """One-line, length-bounded, table-safe test ID (parametrize IDs are arbitrary text)."""
    flat = " ".join(node_id.split())
    if len(flat) > _TEST_ID_LIMIT:
        flat = flat[: _TEST_ID_LIMIT - 1] + "…"
    return _cell(flat)


def render_failure_summary(paths: list[Path], *, title: str = "pytest", cap: int = SUMMARY_ROW_CAP) -> str:
    """Markdown for a job summary: failing/erroring tests, or one line when green.

    Skipped tests are ignored. Missing, empty, or unreadable JUnit files are
    reported in a single line and never raise, so the summary step cannot
    change the shard's result.
    """
    existing = [path for path in paths if path.is_file() and path.stat().st_size > 0]
    if not existing:
        return f"{title}: no JUnit results to summarise.\n"
    try:
        results = parse_junit(existing)
    except (ValueError, ElementTree.ParseError) as exc:
        return f"{title}: JUnit results unreadable ({_cell(_first_line(str(exc)))}).\n"
    bad = [result for result in results if result.outcome in ("failed", "error")]
    if not bad:
        return f"{title}: {len(results)} tests, no failures.\n"
    lines = [
        f"### {_cell(title)}: {len(bad)} failing of {len(results)} tests",
        "",
        "| Test | Outcome | Message |",
        "| --- | --- | --- |",
    ]
    lines.extend(
        f"| {_test_id_cell(result.node_id)} | {result.outcome} | {_cell(_first_line(result.message))} |"
        for result in bad[:cap]
    )
    if len(bad) > cap:
        lines.extend(["", f"and {len(bad) - cap} more"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Render failing pytest tests from JUnit XML as Markdown.")
    parser.add_argument("paths", nargs="*", type=Path, help="JUnit XML files (missing files are tolerated)")
    parser.add_argument("--title", default="pytest")
    parser.add_argument("--cap", type=int, default=SUMMARY_ROW_CAP)
    args = parser.parse_args(argv)
    print(render_failure_summary(args.paths, title=args.title, cap=args.cap), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
