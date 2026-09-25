"""Inventory literal and dynamically based data-path consumers by phase.

The inventory combines literal references to each phase K/A path with an
explicit set of known path bases/helpers. Update ``KNOWN_BASES`` whenever a
reader or writer constructs an artifact path without a literal full path.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import subprocess
import sys
from pathlib import Path

CLASSIFICATION = Path("registry/artifacts/classification-v1.tsv")

# These names are intentionally listed and emitted for phase review. Generic
# checkout roots are scanned only when their joined path explicitly names
# data/ or registry/, avoiding unrelated ROOT references.
KNOWN_BASES_BY_PHASE = {
    "P1": ("DATA_DIR", "DATA_ROOT", "REGISTRY_ROOT", "artifact_path", "PRACTICE_DIR", "TRANSLATIONS_DIR"),
    "P2": ("DATA_DIR", "DATA_ROOT", "artifact_path", "LEXICON_DATA_DIR"),
    "P3": (
        "DATA_DIR",
        "DATA_ROOT",
        "artifact_path",
        "OPEN_MODEL_DATA_DIR",
        "OPEN_MODEL_DATA_ROOT",
        "CONTRACTS_DIR",
        "RELEASE_DIR",
        "DEFAULT_CONTRACTS_DIR",
        "DEFAULT_RELEASE_DIR",
    ),
    "P4": ("DATA_DIR", "DATA_ROOT", "artifact_path"),
    "P5": ("DATA_DIR", "DATA_ROOT", "REGISTRY_ROOT", "artifact_path"),
}
KNOWN_BASES = tuple(
    dict.fromkeys(
        [
            *(name for names in KNOWN_BASES_BY_PHASE.values() for name in names),
            "PROJECT_ROOT / data or registry",
            "REPO_ROOT / data or registry",
            "ROOT / data or registry",
            "Path(__file__) joined to data or registry",
        ]
    )
)


class ConsumerInventoryError(ValueError):
    """Invalid classification, phase, or repository scan."""


def _phase_excluded_prefixes(phase: str) -> tuple[str, ...]:
    phase_prefixes = {
        "P2": ("data/lexicon/",),
        "P3": ("data/projects/open_model_data/",),
        "P4": (
            "data/projects/ua_eval_harness/",
            "data/projects/ua_open_weight_eval/",
            "data/processed/",
            "data/datasets/",
        ),
    }
    if phase == "P1":
        return tuple(prefix for prefixes in phase_prefixes.values() for prefix in prefixes)
    if phase in phase_prefixes:
        return ()
    if phase == "P5":
        return ("data/",)
    raise ConsumerInventoryError(f"unknown phase {phase}; expected P1-P5")


def _artifact_paths(table: Path, phase: str) -> list[str]:
    try:
        with table.open(encoding="utf-8", newline="") as stream:
            rows = csv.DictReader(stream, delimiter="\t")
            required = {"path", "class", "group"}
            if rows.fieldnames is None or not required.issubset(rows.fieldnames):
                raise ConsumerInventoryError(f"classification table needs columns: {', '.join(sorted(required))}")
            excluded = _phase_excluded_prefixes(phase)
            if phase == "P5":
                return []
            if phase == "P1":
                return sorted(
                    row["path"] for row in rows if row["class"] in {"A", "K"} and not row["path"].startswith(excluded)
                )
            prefixes = {
                "P2": ("data/lexicon/",),
                "P3": ("data/projects/open_model_data/",),
                "P4": (
                    "data/projects/ua_eval_harness/",
                    "data/projects/ua_open_weight_eval/",
                    "data/processed/",
                    "data/datasets/",
                ),
            }[phase]
            return sorted(
                row["path"] for row in rows if row["class"] in {"A", "K"} and row["path"].startswith(prefixes)
            )
    except OSError as exc:
        raise ConsumerInventoryError(f"cannot read classification table {table}: {exc}") from exc


def _tracked_files(repo_root: Path) -> list[Path]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=repo_root, check=True, capture_output=True, timeout=30)
    return [repo_root / name.decode("utf-8") for name in result.stdout.split(b"\0") if name]


def scan_inventory(repo_root: Path, *, phase: str, table: Path | None = None) -> list[dict[str, str]]:
    """Find tracked source files mentioning phase artifact paths or known bases."""
    repo_root = repo_root.resolve()
    table_path = (table or (repo_root / CLASSIFICATION)).resolve()
    artifacts = _artifact_paths(table_path, phase)
    if not artifacts:
        return []
    base_names = KNOWN_BASES_BY_PHASE[phase]
    dynamic_pattern = re.compile(r"\b(?:" + "|".join(re.escape(name) for name in base_names) + r")\b")
    root_join_pattern = re.compile(
        r"\b(PROJECT_ROOT|REPO_ROOT|ROOT)\b\s*(?:/|\.joinpath\s*\()[^\n]{0,160}['" "](?:data|registry)(?:/|['" "])",
        re.IGNORECASE,
    )
    file_join_pattern = re.compile(r"Path\(__file__\)[^\n]{0,160}['" "](?:data|registry)(?:/|['" "])", re.IGNORECASE)
    literal_pattern = re.compile("|".join(re.escape(path) for path in sorted(artifacts, key=len, reverse=True)))
    phase_roots = {
        "P2": ("data/lexicon",),
        "P3": ("data/projects/open_model_data",),
        "P4": ("data/projects/ua_eval_harness", "data/projects/ua_open_weight_eval", "data/processed", "data/datasets"),
    }.get(phase, tuple(sorted({"/".join(path.split("/")[:3]) for path in artifacts})))
    prefix_pattern = re.compile("|".join(re.escape(root) + r"(?:/|['\"]|$)" for root in phase_roots))
    segment_join = re.compile(r"['\"]data['\"]\s*(?:(?:/|,)\s*['\"][^'\"\n]+['\"]\s*){1,5}")
    path_import = (
        re.compile(r"\b(?:from|import)\s+(?:scripts\.projects\.)?open_model_data(?:\.paths\b|\s+import\s+paths\b)")
        if phase == "P3"
        else None
    )
    rows: list[dict[str, str]] = []
    for file_path in _tracked_files(repo_root):
        if not file_path.is_file() or file_path == table_path:
            continue
        relative = file_path.relative_to(repo_root).as_posix()
        if relative.startswith(("registry/artifacts/", "data/", "curriculum/", "wiki/")) or file_path.suffix not in {
            ".py",
            ".sh",
            ".ts",
            ".tsx",
            ".js",
            ".mjs",
            ".yaml",
            ".yml",
            ".toml",
            ".md",
        }:
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found = set(literal_pattern.findall(text))
        if prefix_pattern.search(text):
            found.add("base:phase-directory-prefix")
        for match in segment_join.finditer(text):
            segments = re.findall(r"['\"]([^'\"]+)['\"]", match.group())
            if any("/".join(segments).startswith(root + "/") or "/".join(segments) == root for root in phase_roots):
                found.add("base:data-segment-join")
        if path_import and path_import.search(text):
            found.add("base:open_model_data.paths")
        found.update(f"base:{name}" for name in dynamic_pattern.findall(text))
        found.update(f"base:{name}:data-join" for name in root_join_pattern.findall(text))
        if file_join_pattern.search(text):
            found.add("base:Path(__file__):data-join")
        for label in sorted(found):
            rows.append({"artifact": label, "consumer": relative, "check": ""})
    return sorted(rows, key=lambda row: (row["artifact"], row["consumer"]))


def write_inventory(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=("artifact", "consumer", "check"),
        delimiter="\t",
        lineterminator="\n",
        quoting=csv.QUOTE_ALL,
    )
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan tracked code for literal phase paths and known dynamic path bases.\nUse before each migration phase to enumerate consumers for review and executed checks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.consumers scan --phase P1
  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.consumers scan --phase P2 --repo-root /path/to/checkout

Outputs: registry/artifacts/consumers-<phase>.tsv with artifact, consumer, and empty check columns.
Exit codes: 0 means the scan completed; 1 means Git or classification input failed.
Related: issue #8809, spec v3.3 section 8.7. Known dynamic bases by phase: """
        + "; ".join(f"{phase}={', '.join(names)}" for phase, names in KNOWN_BASES_BY_PHASE.items())
        + ". Also scans PROJECT_ROOT/REPO_ROOT/ROOT and Path(__file__) joins that explicitly contain data/ or registry/.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="write a consumer inventory for one migration phase")
    scan.add_argument("--phase", required=True, help="migration phase: P1, P2, P3, or P4")
    scan.add_argument("--repo-root", type=Path, default=Path.cwd(), help="checkout root (default: current directory)")
    scan.add_argument(
        "--table", type=Path, help="classification table (default: registry/artifacts/classification-v1.tsv)"
    )
    scan.add_argument("--output", type=Path, help="output TSV (default: registry/artifacts/consumers-<phase>.tsv)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = args.repo_root.resolve()
        rows = scan_inventory(root, phase=args.phase, table=args.table)
        output = args.output or (root / "registry" / "artifacts" / f"consumers-{args.phase}.tsv")
        if not output.is_absolute():
            output = root / output
        write_inventory(output, rows)
        print(f"wrote {len(rows)} consumer rows to {output}")
        return 0
    except (ConsumerInventoryError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
