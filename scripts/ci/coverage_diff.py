"""Compare executed coverage identities, rather than aggregate percentages (#11226)."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import quote

SOURCES = ("scripts", ".mcp", "agents_extensions", "packages")
# pytest-cov --cov-context=test records "<nodeid>|<phase>", not a bare node ID.
TEST_PHASES = {"setup", "run", "teardown"}


def test_node(context: str) -> str:
    """Reduce a pytest-cov test context to its node ID, leaving custom contexts alone."""
    node, separator, phase = context.rpartition("|")
    return node if separator and phase in TEST_PHASES else context


def test_nodes(contexts) -> list[str]:
    return sorted({test_node(context) for context in contexts if context})


def read_report(path: Path) -> dict:
    """Reject incomplete/non-branch reports instead of silently comparing empty sets."""
    manifest_path = path.with_name("manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"{manifest_path}: expected a readable manifest with complete: true") from error
    if not isinstance(manifest, dict) or manifest.get("complete") is not True:
        raise ValueError(f"{manifest_path}: expected complete: true before comparing coverage")
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("meta", {}).get("branch_coverage") is not True or not report.get("files"):
        raise ValueError(f"{path}: expected a non-empty branch coverage JSON report")
    for name, data in report["files"].items():
        parts = PurePosixPath(name).parts
        if not parts or parts[0] not in SOURCES or ".." in parts:
            raise ValueError(f"{path}: expected repository-relative production path: {name}")
        lines = data["executed_lines"]
        arcs = data.get("executed_arcs", data["executed_branches"])
        if not isinstance(lines, list) or any(type(line) is not int or line < 1 for line in lines):
            raise ValueError(f"{path}: invalid executed_lines for {name}")
        if not isinstance(arcs, list) or any(
            not isinstance(arc, list) or len(arc) != 2 or any(type(line) is not int for line in arc) for arc in arcs
        ):
            raise ValueError(f"{path}: invalid executed arcs for {name}")
    return report


def lost_coverage(baseline: dict, candidate: dict) -> list[dict]:
    """A disappeared file loses every executed line and arc; gains never offset losses."""
    losses = []
    for name, before in sorted(baseline["files"].items()):
        after = candidate["files"].get(name, {})
        arc_key = "executed_arcs" if "executed_arcs" in before else "executed_branches"
        if after and ("executed_arcs" in before) != ("executed_arcs" in after):
            raise ValueError(f"{name}: cannot compare all arcs with branch-only arcs")
        lines = sorted(set(before["executed_lines"]) - set(after.get("executed_lines", [])))
        arcs = sorted(set(map(tuple, before[arc_key])) - set(map(tuple, after.get(arc_key, []))))
        if lines or arcs:
            losses.append(
                {"file": name, "lost_lines": lines, "lost_arcs": arcs, "line_count": len(lines), "arc_count": len(arcs)}
            )
    return losses


def read_deleted_nodes(path: Path) -> list[str]:
    """Read explicit deleted test node IDs, one per line."""
    try:
        return sorted(
            {
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            }
        )
    except OSError as error:
        raise ValueError(f"{path}: cannot read deleted test node IDs: {error}") from error


def deleted_test_files(repo: Path, git_range: str, tests_dir: str = "tests") -> list[str]:
    """Files deleted or renamed away by ``git diff --name-status`` under tests_dir."""
    if ".." not in git_range:
        raise ValueError("--git-range must be BASE..HEAD")
    base, head = git_range.split("..", 1)
    if not base or not head:
        raise ValueError("--git-range must name both commits")
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo), "diff", "--name-status", base, head, "--", tests_dir],
            text=True,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as error:
        # TimeoutExpired.stderr may be bytes or None even in text mode; use its message.
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) and error.stderr else str(error)
        raise ValueError(f"{repo}: cannot diff {git_range}: {detail.strip()}") from error
    deleted = set()
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        # D = deleted, Rxxx = renamed from fields[1] to fields[2].
        if fields[0].startswith(("D", "R")):
            deleted.add(fields[1])
    return sorted(deleted)


def load_context_data(filename: Path):
    """Read a baseline combined .coverage that carries per-test contexts."""
    import coverage

    if not filename.is_file():
        raise ValueError(f"{filename}: expected a combined .coverage file")
    data = coverage.CoverageData(basename=str(filename))
    try:
        data.read()
    except coverage.CoverageException as error:
        raise ValueError(f"{filename}: cannot read coverage data: {error}") from error
    if not data.has_arcs():
        raise ValueError(f"{filename}: expected branch coverage")
    if not data.measured_contexts() - {""}:
        raise ValueError(f"{filename}: expected per-test contexts; measure the baseline with contexts=true")
    return data


def line_context_map(data, losses: list[dict]) -> dict[tuple[str, int], list[str]]:
    """Baseline tests covering each lost line, from coverage's per-line contexts."""
    result = {}
    for item in losses:
        name = item["file"]
        contexts_by_line = data.contexts_by_lineno(name)
        for line in item["lost_lines"]:
            result[(name, line)] = test_nodes(contexts_by_line.get(line, []))
    return result


def arc_context_map(filename: Path, losses: list[dict]) -> dict[tuple[str, int, int], list[str]]:
    """Baseline tests covering each lost arc, from the sqlite arc/context rows.

    CoverageData queries arcs one context at a time. That would issue hundreds of
    thousands of reads for a whole-suite baseline, so read the documented
    per-context arc table once and filter to lost identities in Python.
    """
    wanted = {item["file"]: {tuple(arc) for arc in item["lost_arcs"]} for item in losses if item["lost_arcs"]}
    if not wanted:
        return {}
    connection = None
    try:
        connection = sqlite3.connect(f"file:{quote(str(filename.resolve()))}?mode=ro", uri=True)
        rows = connection.execute(
            "SELECT file.path, context.context, arc.fromno, arc.tono "
            "FROM arc JOIN file ON file.id = arc.file_id JOIN context ON context.id = arc.context_id"
        )
        result: dict[tuple[str, int, int], set[str]] = {}
        for name, context, fromno, tono in rows:
            if context and (fromno, tono) in wanted.get(name, set()):
                result.setdefault((name, fromno, tono), set()).add(context)
        return {key: test_nodes(contexts) for key, contexts in result.items()}
    except sqlite3.Error as error:
        raise ValueError(f"{filename}: cannot read per-context arcs: {error}") from error
    finally:
        if connection is not None:
            connection.close()


def lost_identities(losses: list[dict], lines: dict, arcs: dict) -> list[dict]:
    """One record per lost line and arc with its covering baseline tests."""
    identities = []
    for item in losses:
        name = item["file"]
        for line in item["lost_lines"]:
            identities.append({"file": name, "line": line, "tests": lines[(name, line)]})
        for fromno, tono in item["lost_arcs"]:
            identities.append({"file": name, "arc": [fromno, tono], "tests": arcs.get((name, fromno, tono), [])})
    return identities


def identity_label(identity: dict) -> str:
    """Readable key for one lost identity: ``file:line`` or ``file:from->to``."""
    if "line" in identity:
        return f"{identity['file']}:{identity['line']}"
    fromno, tono = identity["arc"]
    return f"{identity['file']}:{fromno}->{tono}"


def restore_plan(identities: list[dict], deleted: set[str], candidate_root: Path) -> dict:
    """Which deleted tests to restore so lost identities in live production code return.

    ``candidate_tests`` is every deleted test covering any such identity.
    ``restore_set`` is a small covering subset chosen by the standard greedy
    set-cover heuristic: repeatedly take the test that covers the most
    still-uncovered identities, breaking ties by test ID. Greedy stays within a
    factor of ln(n) + 1 of the optimum (n = identities); it is not guaranteed
    to be the exact minimum, which is NP-hard to compute. ``restore_coverage``
    names the identities each chosen test adds when it is picked.
    ``unrestorable_identities`` are live losses no deleted test covered, so no
    restore can recover them. Files absent from the candidate checkout are dead
    and excluded throughout.
    """
    dead_files = sorted(
        {identity["file"] for identity in identities if not (candidate_root / identity["file"]).is_file()}
    )
    live = [identity for identity in identities if identity["file"] not in dead_files]
    order = {identity_label(identity): index for index, identity in enumerate(live)}
    covers: dict[str, set[str]] = {}
    unrestorable = []
    for identity in live:
        tests = [test for test in identity["tests"] if test in deleted]
        if not tests:
            unrestorable.append(identity)
        for test in tests:
            covers.setdefault(test, set()).add(identity_label(identity))
    uncovered = set().union(*covers.values())
    chosen: dict[str, list[str]] = {}
    while uncovered:
        test = min(covers, key=lambda name: (-len(covers[name] & uncovered), name))
        gained = covers[test] & uncovered
        chosen[test] = sorted(gained, key=order.__getitem__)
        uncovered -= gained
    return {
        "dead_files": dead_files,
        "candidate_tests": sorted(covers),
        "restore_set": sorted(chosen),
        "restore_coverage": chosen,
        "unrestorable_identities": unrestorable,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "List production files with lost executed lines or arcs.\n"
            "Use for paired branch coverage reports from coverage-ref.yml; "
            "do not use percentages or reports from different source layouts.\n"
            "With --baseline-data, map every lost line and arc to the baseline tests "
            "that covered it, list every deleted test covering a live loss "
            "(candidate_tests), and choose a small restore_set of them with the greedy "
            "set-cover heuristic (within ln(n) + 1 of the minimum, not exactly minimal).\n"
            "Lines executed only in subprocesses have no pytest test context; they are "
            "reported under unattributed_lost_identities."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/ci/coverage_diff.py baseline/coverage.json candidate/coverage.json\n"
            "  .venv/bin/python scripts/ci/coverage_diff.py baseline/coverage.json candidate/coverage.json \\\n"
            "    --baseline-data baseline/.coverage --git-range <base>..<head>\n"
            "Outputs: JSON to stdout with every lost identity, covering baseline tests, candidate_tests, "
            "a greedy restore_set and unrestorable_identities; "
            "no files written. The baseline .coverage must have per-test contexts.\n"
            "Exit codes: 0 = no loss; 1 = lost coverage; 2 = invalid input.\n"
            "Related: .github/workflows/coverage-ref.yml; scripts/ci/coverage_ref.py; #11226. "
            "Requires a sibling manifest.json with complete: true for both reports.\n"
            "Line/arc numbers are literal identities: source edits that move lines require review."
        ),
    )
    parser.add_argument("baseline", type=Path, help="Baseline branch JSON, e.g. main/coverage.json")
    parser.add_argument("candidate", type=Path, help="Candidate branch JSON, e.g. prune/coverage.json")
    parser.add_argument(
        "--baseline-data",
        type=Path,
        help="Baseline combined .coverage measured with per-test contexts, e.g. baseline/.coverage",
    )
    parser.add_argument(
        "--deleted-test-nodes",
        type=Path,
        help="File of deleted test node IDs, one per line (use for tests removed from a modified file)",
    )
    parser.add_argument(
        "--git-range",
        help="BASE..HEAD: derive deleted test files with git diff --name-status under --tests-dir",
    )
    parser.add_argument("--git-repo", type=Path, default=Path("."), help="Repository for --git-range (default: .)")
    parser.add_argument("--tests-dir", default="tests", help="Code path git diff should inspect (default: tests)")
    parser.add_argument(
        "--candidate-root",
        type=Path,
        default=Path("."),
        help="Candidate checkout used to exclude dead production files (default: .)",
    )
    args = parser.parse_args(argv)
    try:
        if (args.deleted_test_nodes or args.git_range) and not args.baseline_data:
            raise ValueError("--deleted-test-nodes and --git-range require --baseline-data")
        losses = lost_coverage(read_report(args.baseline), read_report(args.candidate))
        payload: dict = {"files_with_losses": losses}
        if args.baseline_data:
            data = load_context_data(args.baseline_data)
            deleted = set(read_deleted_nodes(args.deleted_test_nodes)) if args.deleted_test_nodes else set()
            if args.git_range:
                deleted_files = set(deleted_test_files(args.git_repo, args.git_range, args.tests_dir))
                contexts = {context for context in data.measured_contexts() if context}
                deleted |= {
                    test_node(context) for context in contexts if test_node(context).split("::", 1)[0] in deleted_files
                }
            lines = line_context_map(data, losses)
            arcs = arc_context_map(args.baseline_data, losses)
            identities = lost_identities(losses, lines, arcs)
            payload.update(
                {
                    "lost_identities": identities,
                    # coverage's subprocess patch does not inherit pytest-cov's
                    # test context, so subprocess-only lines stay unattributed.
                    "unattributed_lost_identities": [
                        {key: value for key, value in identity.items() if key != "tests"}
                        for identity in identities
                        if not identity["tests"]
                    ],
                    "deleted_test_nodes": sorted(deleted),
                    **restore_plan(identities, deleted, args.candidate_root),
                }
            )
    except (OSError, ValueError, KeyError, TypeError, AttributeError, sqlite3.Error) as error:
        print(f"coverage_diff: {error}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2))
    return int(bool(losses))


if __name__ == "__main__":
    raise SystemExit(main())
