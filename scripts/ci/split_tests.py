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

``refresh`` freezes median weights from at most 20 examined successful
merge-group runs, retaining committed weights where observations
are absent or incompatible with HEAD test-file blobs. ci.yml publishes those
artifacts only after its full partition audit, and distributes one snapshot to the whole matrix. Unavailable telemetry
keeps the committed weights inside that one snapshot and exits 0. Shards do
not choose a fallback themselves: every shard reads the same refresh-job
result. Success requires the uploaded snapshot (a shard that still cannot
read it fails). Any other result uses the committed weights. Weights never
change which files run.

Stdlib only, so it runs before the project environment is installed.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
import zlib
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path
from xml.etree import ElementTree

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common import github_client

DEFAULT_DURATIONS = Path(__file__).with_name("pytest-file-durations.json")
# Repo-relative path the workflow passes to ``split``. It names DEFAULT_DURATIONS
# without putting a runner path in the job log.
COMMITTED_DURATION_PATH = Path("scripts/ci/pytest-file-durations.json")
DEFAULT_HISTORY = Path(__file__).with_name("history-tests.txt")
HISTORY_SHARD = 1  # ci.yml: the one pytest shard with a full-history checkout
TIMING_ARTIFACT = "pytest-file-durations"
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024
MAX_MEMBER_BYTES = 1024 * 1024
# needs.refresh-pytest-durations.result. Only these four exist; anything else
# is rejected so a shard cannot invent an input the others did not choose.
REFRESH_RESULTS = frozenset({"success", "failure", "cancelled", "skipped"})
SOURCE_SNAPSHOT = "snapshot"
SOURCE_COMMITTED = "committed"
MAX_LOOKUP_BYTES = 32 * 1024 * 1024
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_TREE_ENTRIES = 100_000
LOOKUP_SECONDS = 120
MAX_LOOKUP_CALLS = 60


class DurationSnapshotRequired(RuntimeError):
    """The refresh job succeeded, so this shard cannot run on other weights."""


def duration_source_decision(refresh_result: str) -> str:
    """``snapshot`` or ``committed``, from the shared refresh-job result.

    Every shard passes the same ``needs.refresh-pytest-durations.result``.
    The result does not depend on this shard's download. Only ``success``
    selects the snapshot that job uploaded. ``failure``, ``cancelled`` and
    ``skipped`` select the committed weights.
    """
    if refresh_result not in REFRESH_RESULTS:
        raise ValueError("refresh result must be success, failure, cancelled, or skipped")
    return SOURCE_SNAPSHOT if refresh_result == "success" else SOURCE_COMMITTED


def resolve_duration_path(refresh_result: str, snapshot: Path) -> Path:
    """Weights path every shard must pass to ``split``.

    When the decision is ``snapshot``, a missing or invalid file raises
    ``DurationSnapshotRequired`` instead of falling back. When it is
    ``committed``, ``snapshot`` is ignored even if it holds different weights.
    """
    if duration_source_decision(refresh_result) == SOURCE_COMMITTED:
        return COMMITTED_DURATION_PATH
    try:
        validate_durations(json.loads(snapshot.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        raise DurationSnapshotRequired(
            "refresh succeeded but the shared duration snapshot is unavailable"
        ) from None
    return snapshot


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


def github_api(endpoint: str, *, timeout: float = 30, max_bytes: int = MAX_RESPONSE_BYTES) -> bytes:
    """Use the existing scoped client, spooling bounded bodies without logging them."""
    bound = min(max_bytes, MAX_ARCHIVE_BYTES) if endpoint.endswith("/zip") else max_bytes
    with tempfile.TemporaryFile() as download:
        try:
            github_client.run(["gh", "api", endpoint], check=True, stdout=download, stderr=subprocess.PIPE,
                              timeout=timeout, max_response_bytes=bound)
        except subprocess.CalledProcessError as exc:
            observation = getattr(exc, "github_result", None)
            if observation is not None and observation.status == 413:
                raise ValueError("response exceeds size limit") from exc
            raise
        if download.tell() > bound:
            raise ValueError("response exceeds size limit")
        download.seek(0)
        return download.read(bound + 1)


class TimingLookup:
    """One aggregate deadline and conservative byte/call accounting, including failures."""

    def __init__(self) -> None:
        self.started = time.monotonic()
        self.calls = self.bytes = 0

    def read(self, endpoint: str) -> bytes:
        remaining = LOOKUP_SECONDS - (time.monotonic() - self.started)
        bound = min(MAX_RESPONSE_BYTES, MAX_LOOKUP_BYTES - self.bytes)
        if remaining <= 0 or self.calls >= MAX_LOOKUP_CALLS or bound <= 0:
            raise ValueError("lookup budget exhausted")
        if endpoint.endswith("/zip"):
            bound = min(bound, MAX_ARCHIVE_BYTES)
        self.calls += 1
        # A failed bounded response may have consumed its entire allocation.
        self.bytes += bound
        body = github_api(endpoint, timeout=min(30, remaining), max_bytes=bound)
        if len(body) > bound:
            raise ValueError("response exceeds size limit")
        self.bytes -= bound - len(body)
        return body


def sha1(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def tree_entries(value: dict, expected: str | None = None) -> dict[str, dict]:
    """Validate a complete tree response; duplicate or unsafe identities are unknown."""
    if value.get("truncated") is not False or not sha1(value.get("sha")):
        raise ValueError("unknown tree completeness")
    if expected is not None and value["sha"] != expected:
        raise ValueError("conflicting tree identity")
    rows = value["tree"]
    if not isinstance(rows, list) or len(rows) > MAX_TREE_ENTRIES:
        raise ValueError("invalid tree entries")
    entries = {}
    for row in rows:
        name = row["path"]
        if (not isinstance(name, str) or not name or any(p in ("", ".", "..") for p in name.split("/"))
                or any(ord(c) < 32 for c in name) or name in entries or not sha1(row.get("sha"))
                or (row.get("type"), row.get("mode")) not in {
                    ("blob", "100644"), ("blob", "100755"), ("blob", "120000"),
                    ("tree", "040000"), ("commit", "160000")}):
            raise ValueError("invalid tree identity")
        entries[name] = row
    return entries


def git_tree_sha(rows: list[tuple[str, dict]]) -> str:
    rows = sorted(rows, key=lambda item: (item[0] + ("/" if item[1]["type"] == "tree" else "")).encode())
    body = b"".join(r["mode"].lstrip("0").encode() + b" " + n.encode() + b"\0" + bytes.fromhex(r["sha"]) for n, r in rows)
    return hashlib.sha1(b"tree " + str(len(body)).encode() + b"\0" + body).hexdigest()


def test_blob_map(value: dict, expected: str) -> dict[str, str]:
    """Rebuild every Git tree hash to reject omitted descendants, even without truncation.

    Blob equality detects changed test files, not shared fixtures, markers,
    dependencies or application behavior. It is not workload-equivalence proof.
    """
    entries = tree_entries(value, expected)
    children: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    trees = {"": expected, **{p: r["sha"] for p, r in entries.items() if r["type"] == "tree"}}
    for path, row in entries.items():
        parent, _, name = path.rpartition("/")
        if parent not in trees:
            raise ValueError("incomplete recursive tree")
        children[parent].append((name, row))
    for parent, digest in trees.items():
        if git_tree_sha(children[parent]) != digest:
            raise ValueError("incomplete or conflicting recursive tree")
    return {"tests/" + p: r["sha"] for p, r in entries.items() if r["type"] == "blob" and r["mode"] in {"100644", "100755"}}


def checkout_test_blobs() -> dict[str, str]:
    """Read HEAD's tracked identities once; sparse checkout needs no materialization."""
    raw = subprocess.check_output(["git", "ls-tree", "-rz", "HEAD", "--", "tests"], timeout=30)
    result = {}
    for entry in raw.decode().split("\0"):
        if entry:
            metadata, path = entry.split("\t", 1)
            mode, kind, digest = metadata.split()
            if kind == "blob" and mode in {"100644", "100755"}:
                result[path] = digest
    return result


def archive_json(payload: bytes, name: str) -> object:
    """Read one bounded JSON member; never extract an archive to the checkout."""
    if len(payload) > MAX_ARCHIVE_BYTES:
        raise ValueError("timing archive exceeds size limit")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [info for info in archive.infolist() if info.filename == name]
        if len(members) != 1 or members[0].file_size > MAX_MEMBER_BYTES:
            raise ValueError("expected one bounded timing member")
        with archive.open(members[0]) as member:
            data = member.read(MAX_MEMBER_BYTES + 1)
        if len(data) > MAX_MEMBER_BYTES:
            raise ValueError("timing member exceeds size limit")
    return json.loads(data)


def archive_durations(payload: bytes) -> dict[str, float]:
    return validate_durations(archive_json(payload, "pytest-file-durations.json"))


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
    lookup = TimingLookup()
    counts: Counter = Counter()
    try:
        current = checkout_test_blobs()
        runs = json.loads(lookup.read(
            f"repos/{repo}/actions/workflows/ci.yml/runs?event=merge_group&status=success&per_page=20"
        ))["workflow_runs"]
        if not isinstance(runs, list):
            raise ValueError("invalid run listing")
        by_run: dict[int, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for name in (TIMING_ARTIFACT, "ci-tested-tree"):
            listing = json.loads(lookup.read(f"repos/{repo}/actions/artifacts?name={name}&per_page=100"))
            if not isinstance(listing["artifacts"], list) or len(listing["artifacts"]) > 100:
                raise ValueError("invalid artifact listing")
            for artifact in listing["artifacts"]:
                if artifact["name"] == name and not artifact["expired"]:
                    by_run[artifact["workflow_run"]["id"]][name].append(artifact)
    except (subprocess.SubprocessError, OSError, ValueError, KeyError, TypeError, AttributeError):
        print("duration lookup unavailable; retaining committed fallback", file=sys.stderr)
        runs = []
    for run in runs[:20]:
        counts["candidates_examined"] += 1
        phase = "identity_unknown"
        try:
            if (not isinstance(run, dict) or run.get("event") != "merge_group"
                    or run.get("status") != "completed" or run.get("conclusion") != "success"
                    or run.get("run_attempt") != 1 or run.get("path") != ".github/workflows/ci.yml"):
                counts["ineligible"] += 1
                continue
            artifacts = by_run[run["id"]]
            if any(len(artifacts[n]) != 1 for n in (TIMING_ARTIFACT, "ci-tested-tree")):
                counts["artifact_missing_or_duplicate"] += 1
                continue
            head = run["head_sha"]
            if not sha1(head) or any(artifacts[n][0]["workflow_run"]["head_sha"] != head for n in artifacts):
                raise ValueError("conflicting artifact identity")
            record = archive_json(lookup.read(
                f"repos/{repo}/actions/artifacts/{int(artifacts['ci-tested-tree'][0]['id'])}/zip"
            ), "tested-tree.json")
            if (record["sha"] != head or record["run_id"] != run["id"] or record["run_attempt"] != 1
                    or record["event"] != "merge_group" or record["tier"] != "full" or not sha1(record["tree"])):
                raise ValueError("conflicting tested identity")
            commit = json.loads(lookup.read(f"repos/{repo}/git/commits/{head}"))
            if commit["sha"] != head or commit["tree"]["sha"] != record["tree"]:
                raise ValueError("conflicting commit identity")
            root = tree_entries(json.loads(lookup.read(f"repos/{repo}/git/trees/{record['tree']}")), record["tree"])
            if any("/" in p for p in root) or git_tree_sha(list(root.items())) != record["tree"]:
                raise ValueError("incomplete root tree")
            subtree = root["tests"]
            if subtree["type"] != "tree":
                raise ValueError("missing test tree")
            identity = test_blob_map(json.loads(lookup.read(
                f"repos/{repo}/git/trees/{subtree['sha']}?recursive=1"
            )), subtree["sha"])
            counts["identities_resolved"] += 1
            phase = "artifact_invalid"
            observed = archive_durations(lookup.read(
                f"repos/{repo}/actions/artifacts/{int(artifacts[TIMING_ARTIFACT][0]['id'])}/zip"
            ))
            compatible = {}
            for name, seconds in observed.items():
                reason = "missing_identity" if name not in current or name not in identity else (
                    "admitted" if current[name] == identity[name] else "changed_blob")
                counts[reason] += 1
                if reason == "admitted":
                    compatible[name] = seconds
            if compatible:
                samples.append(compatible)
            if len(samples) == limit:
                break
        except (subprocess.SubprocessError, OSError, ValueError, KeyError, TypeError,
                zipfile.BadZipFile, RuntimeError, EOFError, zlib.error, AttributeError):
            counts[phase] += 1
            print("duration sample unavailable or invalid; skipping sample", file=sys.stderr)
    print("duration lookup: " + json.dumps({**counts, "calls": lookup.calls, "bytes": lookup.bytes,
          "elapsed": round(time.monotonic() - lookup.started, 3)}, sort_keys=True))
    # Preserve older measurements for files absent from the sampled runs.
    snapshot = {**recorded, **median_durations(samples)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"duration snapshot: {len(samples)} successful merge-group samples, {len(snapshot)} file weights")
    return len(samples)


def tracked_test_files(root: Path | None = None) -> list[str]:
    """Tracked ``tests/**/test_*.py`` paths, the same denominator ci.yml shards split.

    ``git ls-files`` is the selection. A duration snapshot never adds or drops a file.
    """
    repo = root or Path(__file__).resolve().parents[2]
    listed = subprocess.check_output(["git", "ls-files", "--", "tests"], cwd=repo, text=True, timeout=30)
    return [line for line in listed.splitlines() if re.fullmatch(r"tests/(?:[^/]+/)*test_[^/]+\.py", line)]


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
  .venv/bin/python -m scripts.ci.split_tests duration-source --refresh-result success --snapshot ci-artifacts/pytest-file-durations.json
Outputs: file paths or timing JSON on stdout; refresh writes one immutable timing snapshot.
duration-source prints the weights path every shard must use, or ``snapshot`` / ``committed`` with ``--decide``.
Exit codes: 0 = success (including refresh fallback and a committed duration source); 1 = invalid data, or the refresh job succeeded and the shared snapshot is missing or invalid; 2 = CLI usage error.
Related: .github/workflows/ci.yml; issues #9065 and #11040.
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
    source = commands.add_parser(
        "duration-source",
        help="print the weights path every shard must use for one refresh-job result",
    )
    source.add_argument(
        "--refresh-result",
        required=True,
        help="needs.refresh-pytest-durations.result: success, failure, cancelled, or skipped",
    )
    source.add_argument(
        "--snapshot",
        type=Path,
        help="downloaded snapshot path, e.g. ci-artifacts/pytest-file-durations.json",
    )
    source.add_argument(
        "--decide",
        action="store_true",
        help="print snapshot or committed from the refresh result alone; do not read --snapshot",
    )
    refresh = commands.add_parser("refresh", help="freeze median weights from recent successful merge-group artifacts")
    refresh.add_argument("--repo", required=True, help="GitHub owner/repo; uses GH_TOKEN with actions:read")
    refresh.add_argument("--output", required=True, type=Path, help="immutable snapshot JSON shared by all shards")
    refresh.add_argument(
        "--fallback", type=Path, default=DEFAULT_DURATIONS, help="offline weights (default: committed JSON)"
    )
    refresh.add_argument("--limit", type=int, default=20, help="successful timing samples from at most 20 examined runs, 1..20 (default: 20)")
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
    if args.command == "duration-source":
        try:
            if args.decide:
                if args.snapshot is not None:
                    parser.error("--decide does not read --snapshot")
                print(duration_source_decision(args.refresh_result))
                return 0
            if args.snapshot is None:
                parser.error("duration-source requires --snapshot or --decide")
            print(resolve_duration_path(args.refresh_result, args.snapshot))
        except DurationSnapshotRequired as exc:
            print(exc, file=sys.stderr)
            return 1
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
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
