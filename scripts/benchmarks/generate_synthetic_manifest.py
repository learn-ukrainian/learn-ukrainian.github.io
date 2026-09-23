"""Deterministic seeded synthetic Atlas manifest fixture generator (#8307).

Resamples real current Atlas manifest entries into a clearly synthetic, deterministic
manifest at target row scale (default 410,000 entries) for reproducible export and build
benchmarks (#8307, #8332, #8310). Output is strictly synthetic and must never be published.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_OUT = Path("/tmp/synthetic-lexicon-manifest.json")
DEFAULT_COUNT = 410_000
DEFAULT_SEED = 42
DEFAULT_MIN_DISK_GB = 25.0
MIN_CLI_DISK_GB = 25.0
SYNTHETIC_SLUG_SUFFIX = "--syn{index:07d}"
SYNTHETIC_TIMESTAMP = "2026-09-23T00:00:00+00:00"


def resolve_manifest_path(path: Path) -> Path:
    """Resolve a manifest path against ROOT if relative and existing under ROOT."""
    resolved = path if path.is_absolute() else (ROOT / path)
    return resolved.resolve() if resolved.exists() else (Path.cwd() / path).resolve()


def assert_different_paths(source_path: Path, output_path: Path) -> None:
    """Refuse generation when output resolves to the same file as source manifest."""
    source_resolved = resolve_manifest_path(source_path)
    output_resolved = resolve_manifest_path(output_path)

    is_same = source_resolved == output_resolved
    if not is_same and source_resolved.exists() and output_resolved.exists():
        with suppress(OSError):
            is_same = source_resolved.samefile(output_resolved)

    if is_same:
        raise ValueError(
            f"Refusing to overwrite source manifest: output path '{output_path}' resolves to the same file as source path '{source_path}' ({source_resolved})"
        )


def check_free_disk_space(target_path: Path, min_gb: float = DEFAULT_MIN_DISK_GB) -> float:
    """Ensure sufficient free disk space exists before heavy fixture generation."""
    dest_dir = target_path.parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    stat = os.statvfs(dest_dir)
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    if free_gb < min_gb:
        raise RuntimeError(
            f"Insufficient free disk space: {free_gb:.2f} GB available on {dest_dir}, "
            f"minimum required is {min_gb:.2f} GB. Stopping generation to prevent exhaustion."
        )
    return free_gb


def load_source_entries(source_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load source manifest entries deterministically."""
    resolved_path = source_path if source_path.is_absolute() else (ROOT / source_path)
    if not resolved_path.exists() and resolved_path.resolve() == DEFAULT_SOURCE.resolve():
        from scripts.lexicon.manifest_io import load_manifest

        data = load_manifest(resolved_path)
    else:
        if not resolved_path.exists():
            raise FileNotFoundError(f"Source manifest not found: {resolved_path}")
        data = json.loads(resolved_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict) or "entries" not in data:
        raise ValueError(f"Invalid manifest structure in {resolved_path}: missing 'entries'")

    raw_entries = data.get("entries", [])
    if not isinstance(raw_entries, list) or len(raw_entries) == 0:
        raise ValueError(f"Source manifest {resolved_path} has no entries")

    # Sort entries by canonical url_slug / lemma to guarantee deterministic base order
    # regardless of formatting or insertion quirks in the input JSON file.
    sorted_entries = sorted(
        raw_entries,
        key=lambda e: str(e.get("url_slug") or e.get("lemma") or ""),
    )
    return sorted_entries, data


def mark_base_synthetic(source_entry: dict[str, Any]) -> dict[str, Any]:
    """Flag a base manifest entry as part of the synthetic fixture."""
    entry = dict(source_entry)
    entry["synthetic"] = True
    return entry


def make_synthetic_copy(
    source_entry: dict[str, Any],
    copy_index: int,
) -> dict[str, Any]:
    """Create a synthetic resampled copy with a unique slug and synthetic provenance."""
    entry = dict(source_entry)
    orig_slug = str(source_entry.get("url_slug") or source_entry.get("lemma") or "entry")
    entry["url_slug"] = f"{orig_slug}{SYNTHETIC_SLUG_SUFFIX.format(index=copy_index)}"
    entry["synthetic"] = True

    # Preserve and extend provenance without mutating source
    prov = list(source_entry.get("source_provenance") or [])
    prov.append(
        {
            "source_family": "synthetic_resample",
            "extraction_mode": "synthetic_resample",
            "source_locator": f"resample:{orig_slug}",
        }
    )
    entry["source_provenance"] = prov
    return entry


def generate_entry_stream(
    source_entries: list[dict[str, Any]],
    count: int,
    seed: int,
) -> Iterator[dict[str, Any]]:
    """Yield exactly `count` synthetic entries in deterministic order."""
    source_count = len(source_entries)
    rng = random.Random(seed)

    if count <= source_count:
        # Sample without replacement; different seeds choose different subsets
        selected_indices = sorted(rng.sample(range(source_count), count))
        for idx in selected_indices:
            yield mark_base_synthetic(source_entries[idx])
    else:
        # 1. Yield all base entries in deterministic sorted order
        for entry in source_entries:
            yield mark_base_synthetic(entry)

        # 2. Resample remaining entries with replacement using the seeded RNG
        num_copies = count - source_count
        copy_indices = rng.choices(range(source_count), k=num_copies)
        for copy_idx, src_idx in enumerate(copy_indices, start=1):
            yield make_synthetic_copy(source_entries[src_idx], copy_idx)


def generate_synthetic_manifest(
    source_path: Path,
    output_path: Path,
    count: int = DEFAULT_COUNT,
    seed: int = DEFAULT_SEED,
    min_disk_gb: float = DEFAULT_MIN_DISK_GB,
    generated_at: str = SYNTHETIC_TIMESTAMP,
    quiet: bool = False,
) -> dict[str, Any]:
    """Deterministically stream a synthetic manifest with exact count entries.

    Streams output directly to a sibling temporary file and atomically replaces
    only after a complete write, preventing partial files and preserving existing destinations.
    """
    if count < 1:
        raise ValueError(f"count must be at least 1, got {count}")

    assert_different_paths(source_path, output_path)
    free_gb = check_free_disk_space(output_path, min_gb=min_disk_gb)
    t0 = time.monotonic()

    if not quiet:
        print(f"Loading source manifest from {source_path}...", file=sys.stderr)
    source_entries, _ = load_source_entries(source_path)
    source_count = len(source_entries)

    output_resolved = resolve_manifest_path(output_path)
    output_resolved.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    bytes_written = 0

    version = f"0.1-synthetic-{count}"
    header = (
        "{\n"
        f'  "version": {json.dumps(version, ensure_ascii=False)},\n'
        '  "dataset_kind": "synthetic-resample",\n'
        '  "synthetic": true,\n'
        f'  "synthetic_seed": {seed},\n'
        f'  "synthetic_count": {count},\n'
        f'  "source_entries_count": {source_count},\n'
        f'  "generated_at": {json.dumps(generated_at, ensure_ascii=False)},\n'
        f'  "entries_count": {count},\n'
        '  "entries": [\n'
    )

    if not quiet:
        print(
            f"Streaming {count:,} synthetic entries (seed={seed}, source_entries={source_count:,}) to {output_path}...",
            file=sys.stderr,
        )

    temp_path = output_resolved.with_name(f".{output_resolved.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with open(temp_path, "w", encoding="utf-8", buffering=1024 * 1024) as f:
            f.write(header)
            header_bytes = header.encode("utf-8")
            hasher.update(header_bytes)
            bytes_written += len(header_bytes)

            first = True
            report_step = 50_000

            for entries_written, entry in enumerate(generate_entry_stream(source_entries, count, seed), start=1):
                line = ("    " if first else ",\n    ") + json.dumps(entry, ensure_ascii=False)
                first = False
                f.write(line)
                line_bytes = line.encode("utf-8")
                hasher.update(line_bytes)
                bytes_written += len(line_bytes)

                if not quiet and entries_written % report_step == 0:
                    print(f"  ... {entries_written:,} / {count:,} entries written", file=sys.stderr)

            footer = "\n  ]\n}\n"
            f.write(footer)
            footer_bytes = footer.encode("utf-8")
            hasher.update(footer_bytes)
            bytes_written += len(footer_bytes)

        temp_path.replace(output_resolved)
    except BaseException:
        if temp_path.exists():
            with suppress(OSError):
                temp_path.unlink()
        raise

    duration = time.monotonic() - t0
    digest = hasher.hexdigest()

    base_count = min(count, source_count)
    copies_count = max(0, count - source_count)

    summary = {
        "outcome": "success",
        "dataset_kind": "synthetic-resample",
        "synthetic": True,
        "seed": seed,
        "count": count,
        "source_path": str(source_path),
        "source_entries": source_count,
        "output_path": str(output_path),
        "base_entries": base_count,
        "resampled_copies": copies_count,
        "bytes_written": bytes_written,
        "sha256": digest,
        "duration_seconds": round(duration, 3),
        "free_disk_gb_initial": round(free_gb, 2),
    }

    if not quiet:
        print(
            f"Finished generating {count:,} entries in {duration:.2f}s "
            f"({bytes_written / (1024 * 1024):.1f} MB, sha256: {digest[:16]}...).",
            file=sys.stderr,
        )

    return summary


def _parse_min_disk_gb(val: str) -> float:
    try:
        gb = float(val)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid float value: {val!r}") from None
    if gb < MIN_CLI_DISK_GB:
        raise argparse.ArgumentTypeError(
            f"--min-disk-gb cannot be set below {MIN_CLI_DISK_GB:.1f} GB floor (got {gb})"
        )
    return gb


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a deterministic, synthetic 410,000-scale Atlas manifest fixture by resampling real entries (#8307).\n"
            "Use for reproducible benchmark and scale measurements; do NOT publish or use as production data."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/benchmarks/generate_synthetic_manifest.py --output /tmp/synthetic-manifest.json\n"
            "  .venv/bin/python scripts/benchmarks/generate_synthetic_manifest.py --count 100 --seed 42 --output /tmp/test-manifest.json\n"
            "  .venv/bin/python -m scripts.atlas.atlas_db --manifest /tmp/test-manifest.json --db /tmp/test-atlas.db\n\n"
            "Outputs:\n"
            "  Streams the synthetic manifest JSON to the requested output path and prints a JSON summary to stdout.\n\n"
            "Exit codes:\n"
            "  0 on successful generation and verification.\n"
            "  1 on manifest parsing, formatting, or filesystem error.\n"
            "  2 on CLI argument syntax errors.\n"
            "  3 when free disk space is below the required safety threshold.\n\n"
            "Related:\n"
            "  Atlas entry-model store: scripts/atlas/atlas_db.py\n"
            "  Runtime shards exporter: scripts/atlas/export_runtime_shards.py\n"
            "  DB benchmark harness: site/scripts/benchmark-atlas-db.mjs\n"
            "  Issues: #8307, #8332, #8310"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source",
        "--source-manifest",
        dest="source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Path to current public Atlas manifest to resample from (default: site/src/data/lexicon-manifest.json).",
    )
    parser.add_argument(
        "--output",
        "--out",
        dest="output",
        type=Path,
        default=DEFAULT_OUT,
        help="Output file path for the generated synthetic manifest JSON (default: /tmp/synthetic-lexicon-manifest.json).",
    )
    parser.add_argument(
        "--count",
        "--rows",
        "--target",
        dest="count",
        type=int,
        default=DEFAULT_COUNT,
        help="Total entry count to generate (default: 410000; e.g. 50 for quick testing).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="RNG seed for deterministic resampling (default: 42; same seed produces byte-identical output).",
    )
    parser.add_argument(
        "--min-disk-gb",
        type=_parse_min_disk_gb,
        default=DEFAULT_MIN_DISK_GB,
        help="Minimum required free disk space in GB before generation proceeds; mandatory floor is 25.0 GB (default: 25.0).",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress messages; emit only JSON summary to stdout (default: false).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.min_disk_gb < MIN_CLI_DISK_GB:
        print(
            f"generate_synthetic_manifest error: --min-disk-gb cannot be set below {MIN_CLI_DISK_GB:.1f} GB floor (got {args.min_disk_gb})",
            file=sys.stderr,
        )
        return 2
    try:
        summary = generate_synthetic_manifest(
            source_path=args.source,
            output_path=args.output,
            count=args.count,
            seed=args.seed,
            min_disk_gb=args.min_disk_gb,
            quiet=args.quiet,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except RuntimeError as exc:
        print(f"generate_synthetic_manifest disk/resource error: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"generate_synthetic_manifest failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
