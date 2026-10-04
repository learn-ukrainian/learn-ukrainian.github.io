"""Static, duration-balanced split of pytest files across CI shards.

``split`` reads test file paths on stdin and prints the files for one shard.
Every shard computes the same assignment: files are placed longest first on
the least-loaded shard (LPT), using the recorded per-file seconds in
``scripts/ci/pytest-file-durations.json``. A file with no recorded time gets
the median, so a new or renamed file is still run, only balanced less well.
The shards are a partition of the input: every file lands on exactly one.

The files listed in ``scripts/ci/history-tests.txt`` need git history (or
fetch from GitHub) and always go to shard 1 (``HISTORY_SHARD``), the only
shard ci.yml checks out with full history; every other shard is a shallow
checkout. The rest of the files are balanced around them. A listed file missing from the input fails
the split, so the list cannot go stale silently.

``durations`` rebuilds that JSON from the JUnit files of a full run:

    python -m scripts.ci.split_tests durations junit/*.xml > scripts/ci/pytest-file-durations.json

``refresh`` freezes median weights from the last 20 available successful
merge-group timing artifacts, retaining committed weights where observations
are absent. ci.yml publishes those artifacts only after its full partition
audit, and distributes one snapshot to the whole matrix. Unavailable telemetry
falls back to committed weights with a diagnostic; it never changes selection.

Stdlib only, so it runs before the project environment is installed.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import statistics
import subprocess
import sys
import tempfile
import zipfile
import zlib
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from xml.etree import ElementTree

DEFAULT_DURATIONS = Path(__file__).with_name("pytest-file-durations.json")
DEFAULT_HISTORY = Path(__file__).with_name("history-tests.txt")
HISTORY_SHARD = 1  # ci.yml: the one pytest shard with a full-history checkout
TIMING_ARTIFACT = "pytest-file-durations"
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024
MAX_MEMBER_BYTES = 1024 * 1024


def validate_durations(value: object) -> dict[str, float]:
    """Reject malformed timing data; weights must never affect test selection."""
    if not isinstance(value, dict) or not value:
        raise ValueError("duration data must be a nonempty object")
    for name, seconds in value.items():
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"tests/(?:[^/]+/)*test_[^/]+\.py", name)
            or not isinstance(seconds, (int, float))
            or isinstance(seconds, bool)
            or not math.isfinite(seconds)
            or seconds < 0
        ):
            raise ValueError("invalid test file duration")
    return value


def median_durations(samples: Sequence[dict[str, float]]) -> dict[str, float]:
    """Median per file across observed runs; an absent file is not a zero."""
    observations: dict[str, list[float]] = defaultdict(list)
    for sample in samples:
        for name, seconds in validate_durations(sample).items():
            observations[name].append(seconds)
    return {name: round(statistics.median(values), 3) for name, values in sorted(observations.items())}


def github_api(endpoint: str) -> bytes:
    """Read GitHub with the runner's scoped token; never emit token or response bodies."""
    if endpoint.endswith("/zip"):
        # Spool stdout instead of buffering an untrusted download in memory.
        with tempfile.TemporaryFile() as download:
            subprocess.run(["gh", "api", endpoint], check=True, stdout=download, stderr=subprocess.PIPE, timeout=30)
            if download.tell() > MAX_ARCHIVE_BYTES:
                raise ValueError("timing archive exceeds size limit")
            download.seek(0)
            return download.read(MAX_ARCHIVE_BYTES + 1)
    return subprocess.run(["gh", "api", endpoint], check=True, capture_output=True, timeout=30).stdout


def archive_durations(payload: bytes) -> dict[str, float]:
    """Read one bounded JSON member; never extract an archive to the checkout."""
    if len(payload) > MAX_ARCHIVE_BYTES:
        raise ValueError("timing archive exceeds size limit")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [info for info in archive.infolist() if info.filename == "pytest-file-durations.json"]
        if len(members) != 1 or members[0].file_size > MAX_MEMBER_BYTES:
            raise ValueError("expected one bounded timing member")
        with archive.open(members[0]) as member:
            data = member.read(MAX_MEMBER_BYTES + 1)
        if len(data) > MAX_MEMBER_BYTES:
            raise ValueError("timing member exceeds size limit")
    return validate_durations(json.loads(data))


def refresh_durations(repo: str, fallback: Path, output: Path, limit: int = 20) -> int:
    """Freeze recent successful merge-group timings once, with an offline fallback.

    Only timing artifacts published after the full partition report passes are
    consumed. A lookup failure costs balance, never coverage. All matrix jobs
    download this single immutable snapshot instead of querying independently.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repo) or not 1 <= limit <= 20:
        raise ValueError("expected owner/repo and a sample limit in 1..20")
    recorded = validate_durations(json.loads(fallback.read_text(encoding="utf-8")))
    samples = []
    try:
        runs = json.loads(
            github_api(f"repos/{repo}/actions/workflows/ci.yml/runs?event=merge_group&status=success&per_page=100")
        )["workflow_runs"]
        listing = json.loads(github_api(f"repos/{repo}/actions/artifacts?name={TIMING_ARTIFACT}&per_page=100"))
        by_run: dict[int, list[dict]] = defaultdict(list)
        for artifact in listing["artifacts"]:
            if artifact["name"] == TIMING_ARTIFACT and not artifact["expired"]:
                by_run[artifact["workflow_run"]["id"]].append(artifact)
    except (subprocess.SubprocessError, OSError, ValueError, KeyError, TypeError):
        print("duration lookup unavailable; retaining committed fallback", file=sys.stderr)
        runs = []
        by_run = defaultdict(list)
    for run in runs:
        try:
            if not isinstance(run, dict):
                continue
            if (
                run.get("event") != "merge_group"
                or run.get("status") != "completed"
                or run.get("conclusion") != "success"
                or run.get("run_attempt") != 1
                or run.get("path") != ".github/workflows/ci.yml"
            ):
                continue
            artifacts = by_run[run["id"]]
            if len(artifacts) != 1:
                continue
            payload = github_api(f"repos/{repo}/actions/artifacts/{int(artifacts[0]['id'])}/zip")
            samples.append(archive_durations(payload))
            if len(samples) == limit:
                break
        except (
            subprocess.SubprocessError,
            OSError,
            ValueError,
            KeyError,
            TypeError,
            zipfile.BadZipFile,
            RuntimeError,
            EOFError,
            zlib.error,
        ):
            print("duration sample unavailable or invalid; skipping sample", file=sys.stderr)
    # Preserve older measurements for files absent from the sampled runs.
    snapshot = {**recorded, **median_durations(samples)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"duration snapshot: {len(samples)} successful merge-group samples, {len(snapshot)} file weights")
    return len(samples)


def read_list(path: Path) -> list[str]:
    """Paths in a list file, one per line; ``#`` starts a comment."""
    lines = (line.split("#", 1)[0].strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line]


def assign(
    files: list[str], durations: dict[str, float], shard_count: int, pinned: Sequence[str] = ()
) -> list[list[str]]:
    """Longest-processing-time-first assignment of ``files`` to ``shard_count`` shards.

    ``pinned`` files go to shard ``HISTORY_SHARD`` first; the rest are balanced around them.
    """
    if shard_count < 1:
        raise ValueError("shard_count must be at least 1")
    if len(set(files)) != len(files):
        raise ValueError("duplicate test file in the input")
    missing = sorted(set(pinned) - set(files))
    if missing:
        raise ValueError(f"pinned files are not in the input: {', '.join(missing)}")
    known = [durations[name] for name in files if name in durations]
    default = statistics.median(known) if known else 1.0
    loads = [0.0] * shard_count
    shards: list[list[str]] = [[] for _ in range(shard_count)]
    for name in pinned:
        shards[HISTORY_SHARD - 1].append(name)
        loads[HISTORY_SHARD - 1] += durations.get(name, default)
    rest = set(files) - set(pinned)
    # Name breaks ties so the order never depends on the input order.
    for name in sorted(rest, key=lambda item: (-durations.get(item, default), item)):
        target = min(range(shard_count), key=lambda index: (loads[index], index))
        shards[target].append(name)
        loads[target] += durations.get(name, default)
    return [sorted(shard) for shard in shards]


def junit_file_seconds(paths: list[Path]) -> dict[str, float]:
    """Sum testcase time per test file (``tests/.../test_x.py``) over JUnit files."""
    totals: dict[str, float] = defaultdict(float)
    for path in paths:
        for case in ElementTree.parse(path).getroot().iter("testcase"):
            parts = case.get("classname", "").split(".")
            # The module is the last dotted part named like a test file; test
            # classes are ``Test*`` and never match ``test_``.
            modules = [index for index, part in enumerate(parts) if part.startswith("test_")]
            if not modules:
                continue
            totals["/".join(parts[: modules[-1] + 1]) + ".py"] += float(case.get("time") or 0)
    return {name: round(seconds, 3) for name, seconds in sorted(totals.items())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.ci.split_tests split --shard 1 --of 16 < files.txt
  .venv/bin/python -m scripts.ci.split_tests durations junit/*.xml > durations.json
  .venv/bin/python -m scripts.ci.split_tests refresh --repo owner/repo --output snapshot.json
  .venv/bin/python -m scripts.ci.split_tests validate snapshot.json
Outputs: file paths or timing JSON on stdout; refresh writes one immutable timing snapshot.
Exit codes: 0 = success (including refresh fallback); 1 = invalid data; 2 = CLI usage error.
Related: .github/workflows/ci.yml; issue #9065.
""",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    split = commands.add_parser("split", help="print one shard's files (input: file paths on stdin)")
    split.add_argument("--shard", type=int, required=True, help="1-based shard number")
    split.add_argument("--of", type=int, required=True, dest="shard_count", help="total shards, e.g. 16")
    split.add_argument(
        "--durations", type=Path, default=DEFAULT_DURATIONS, help="file weights (default: committed JSON)"
    )
    split.add_argument("--history", type=Path, default=DEFAULT_HISTORY, help="files pinned to the history shard")
    durations = commands.add_parser("durations", help="print per-file seconds from JUnit XML")
    durations.add_argument("junit", nargs="+", type=Path, help="all shard JUnit XML files from one full run")
    validate = commands.add_parser("validate", help="check a snapshot against the shared timing schema")
    validate.add_argument("snapshot", type=Path, help="timing JSON to validate, e.g. snapshot.json")
    refresh = commands.add_parser("refresh", help="freeze median weights from recent successful merge-group artifacts")
    refresh.add_argument("--repo", required=True, help="GitHub owner/repo; uses GH_TOKEN with actions:read")
    refresh.add_argument("--output", required=True, type=Path, help="immutable snapshot JSON shared by all shards")
    refresh.add_argument(
        "--fallback", type=Path, default=DEFAULT_DURATIONS, help="offline weights (default: committed JSON)"
    )
    refresh.add_argument("--limit", type=int, default=20, help="successful timing samples, 1..20 (default: 20)")
    args = parser.parse_args(argv)

    if args.command == "durations":
        json.dump(validate_durations(junit_file_seconds(args.junit)), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.command == "validate":
        try:
            validate_durations(json.loads(args.snapshot.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            print("duration snapshot unavailable or invalid", file=sys.stderr)
            return 1
        return 0
    if args.command == "refresh":
        refresh_durations(args.repo, args.fallback, args.output, args.limit)
        return 0
    if not 1 <= args.shard <= args.shard_count:
        parser.error(f"--shard {args.shard} is outside 1..{args.shard_count}")
    files = [line.strip() for line in sys.stdin if line.strip()]
    if not files:
        parser.error("no test files on stdin")
    recorded = validate_durations(json.loads(args.durations.read_text(encoding="utf-8")))
    shard = assign(files, recorded, args.shard_count, read_list(args.history))[args.shard - 1]
    sys.stdout.write("".join(f"{name}\n" for name in shard))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
