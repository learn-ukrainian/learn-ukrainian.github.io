#!/usr/bin/env python3
"""Fail-closed published-site size gate for static deploys (#5274).

Profiles (set via ``DEPLOY_PROFILE`` or ``--profile``):

- ``github-pages`` — hard byte cap 900_000_000; warn at 70% of 1 GiB;
  FAIL at ≥80% of 1 GiB (or the hard cap).
- ``cloudflare-free`` — file-count cap < 20_000 (Wrangler major ≥3).
- ``cloudflare-paid`` — file-count cap < 100_000 (Wrangler major ≥3).

Unknown or missing profile → exit non-zero (fail closed).

Usage::

    DEPLOY_PROFILE=github-pages .venv/bin/python scripts/deploy/check_site_size.py site/dist
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

GIB = 1024**3
GITHUB_PAGES_HARD_CAP_BYTES = 900_000_000
GITHUB_PAGES_WARN_BYTES = int(GIB * 0.70)
GITHUB_PAGES_FAIL_BYTES = int(GIB * 0.80)
LEXICON_TARGET_ENTRIES = 20_000


@dataclass(frozen=True)
class DeployProfile:
    """Threshold table for one deployment target."""

    name: str
    max_bytes: int | None = None
    warn_bytes: int | None = None
    fail_bytes: int | None = None
    max_files: int | None = None
    wrangler_major_note: str | None = None


PROFILES: dict[str, DeployProfile] = {
    "github-pages": DeployProfile(
        name="github-pages",
        max_bytes=GITHUB_PAGES_HARD_CAP_BYTES,
        warn_bytes=GITHUB_PAGES_WARN_BYTES,
        fail_bytes=GITHUB_PAGES_FAIL_BYTES,
    ),
    "cloudflare-free": DeployProfile(
        name="cloudflare-free",
        max_files=20_000,
        wrangler_major_note=(
            "cloudflare-free requires Wrangler major version ≥3 "
            "(Workers Assets / Pages upload limits)."
        ),
    ),
    "cloudflare-paid": DeployProfile(
        name="cloudflare-paid",
        max_files=100_000,
        wrangler_major_note=(
            "cloudflare-paid requires Wrangler major version ≥3 "
            "(Workers Assets / Pages upload limits)."
        ),
    ),
}


@dataclass
class RouteFamilyStats:
    name: str
    bytes: int = 0
    files: int = 0


@dataclass
class SiteSizeReport:
    total_bytes: int
    file_count: int
    largest_files: list[tuple[int, str]]
    families: dict[str, RouteFamilyStats]
    lexicon_page_count: int
    lexicon_page_bytes: int
    projected_bytes_at_target: int | None
    warnings: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


def classify_route_family(rel_posix: str) -> str:
    """Map a dist-relative path to etymology / lexicon / base."""
    if rel_posix == "etymology" or rel_posix.startswith("etymology/"):
        return "etymology"
    if rel_posix == "lexicon" or rel_posix.startswith("lexicon/"):
        return "lexicon"
    return "base"


def is_lexicon_word_page(rel_posix: str) -> bool:
    """True for per-lemma pages: ``lexicon/<slug>/index.html`` only.

    Excludes browse/search shards, API mirrors, and the lexicon index itself.
    """
    parts = rel_posix.split("/")
    return (
        len(parts) == 3
        and parts[0] == "lexicon"
        and parts[2] == "index.html"
        and parts[1] not in {"browse", "search"}
    )


def scan_dist(dist: Path, *, largest_n: int = 15) -> SiteSizeReport:
    """Walk ``dist`` and collect byte / file / route-family stats."""
    if not dist.is_dir():
        raise FileNotFoundError(f"dist directory not found: {dist}")

    families = {
        "etymology": RouteFamilyStats("etymology"),
        "lexicon": RouteFamilyStats("lexicon"),
        "base": RouteFamilyStats("base"),
    }
    sized: list[tuple[int, str]] = []
    total_bytes = 0
    file_count = 0
    lexicon_page_count = 0
    lexicon_page_bytes = 0

    for path in dist.rglob("*"):
        if not path.is_file():
            continue
        size = path.stat().st_size
        rel = path.relative_to(dist).as_posix()
        file_count += 1
        total_bytes += size
        sized.append((size, rel))
        family = families[classify_route_family(rel)]
        family.bytes += size
        family.files += 1
        if is_lexicon_word_page(rel):
            lexicon_page_count += 1
            lexicon_page_bytes += size

    sized.sort(key=lambda item: item[0], reverse=True)
    projected: int | None = None
    if lexicon_page_count > 0:
        # Fixed base (everything that is not a per-lemma lexicon page) plus
        # a per-lexicon-page slope — replaces the old all-in /entries @20k
        # linear projection that overstated headroom when etymology routes
        # dominated the tree.
        base_bytes = total_bytes - lexicon_page_bytes
        slope = lexicon_page_bytes / lexicon_page_count
        projected = int(base_bytes + LEXICON_TARGET_ENTRIES * slope)

    return SiteSizeReport(
        total_bytes=total_bytes,
        file_count=file_count,
        largest_files=sized[:largest_n],
        families=families,
        lexicon_page_count=lexicon_page_count,
        lexicon_page_bytes=lexicon_page_bytes,
        projected_bytes_at_target=projected,
    )


def apply_profile(report: SiteSizeReport, profile: DeployProfile) -> SiteSizeReport:
    """Mutate ``report`` with warn/fail reasons for ``profile``."""
    if profile.warn_bytes is not None and report.total_bytes >= profile.warn_bytes:
        pct = 100.0 * report.total_bytes / GIB
        report.warnings.append(
            f"{profile.name}: site is {pct:.1f}% of 1 GiB "
            f"({report.total_bytes:,} bytes ≥ warn {profile.warn_bytes:,})"
        )

    fail_threshold = profile.fail_bytes
    if fail_threshold is not None and report.total_bytes >= fail_threshold:
        pct = 100.0 * report.total_bytes / GIB
        report.failures.append(
            f"{profile.name}: size {report.total_bytes:,} bytes is "
            f"{pct:.1f}% of 1 GiB (≥ fail {fail_threshold:,})"
        )

    if profile.max_bytes is not None and report.total_bytes >= profile.max_bytes:
        report.failures.append(
            f"{profile.name}: size {report.total_bytes:,} bytes exceeds "
            f"hard cap {profile.max_bytes:,}"
        )

    if profile.max_files is not None and report.file_count >= profile.max_files:
        report.failures.append(
            f"{profile.name}: file count {report.file_count:,} exceeds "
            f"cap {profile.max_files:,}"
        )

    return report


def resolve_profile(name: str | None) -> DeployProfile:
    """Return a known profile or raise ``ValueError`` (fail closed)."""
    if not name or not str(name).strip():
        raise ValueError(
            "DEPLOY_PROFILE is missing or empty — fail closed. "
            f"Known profiles: {', '.join(sorted(PROFILES))}"
        )
    key = str(name).strip()
    profile = PROFILES.get(key)
    if profile is None:
        raise ValueError(
            f"Unknown DEPLOY_PROFILE {key!r} — fail closed. "
            f"Known profiles: {', '.join(sorted(PROFILES))}"
        )
    return profile


def format_bytes(n: int) -> str:
    """Human-readable byte size (MiB / GiB)."""
    if n >= GIB:
        return f"{n / GIB:.2f} GiB"
    return f"{n / (1024**2):.1f} MiB"


def format_report(report: SiteSizeReport, profile: DeployProfile) -> str:
    """Stdout / job-summary markdown for one scan."""
    lines: list[str] = [
        f"## Deploy size gate ({profile.name})",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| total bytes | **{report.total_bytes:,}** ({format_bytes(report.total_bytes)}) |",
        f"| file count | **{report.file_count:,}** |",
        f"| budget used | **{100.0 * report.total_bytes / GIB:.1f}%** of 1 GiB |",
        f"| lexicon word pages | {report.lexicon_page_count:,} "
        f"({format_bytes(report.lexicon_page_bytes)}) |",
    ]
    if report.projected_bytes_at_target is not None:
        proj = report.projected_bytes_at_target
        lines.append(
            f"| projected @ {LEXICON_TARGET_ENTRIES:,} lexicon pages "
            f"(fixed-base + slope) | ~{format_bytes(proj)} "
            f"({100.0 * proj / GIB:.1f}% of 1 GiB) |"
        )
    if profile.max_bytes is not None:
        lines.append(f"| hard cap | {profile.max_bytes:,} bytes |")
    if profile.fail_bytes is not None:
        lines.append(f"| fail ≥ | {profile.fail_bytes:,} bytes (80% of 1 GiB) |")
    if profile.warn_bytes is not None:
        lines.append(f"| warn ≥ | {profile.warn_bytes:,} bytes (70% of 1 GiB) |")
    if profile.max_files is not None:
        lines.append(f"| file-count cap | {profile.max_files:,} |")
    if profile.wrangler_major_note:
        lines.append(f"| wrangler note | {profile.wrangler_major_note} |")

    lines.extend(["", "### Route families", "", "| Family | Files | Bytes |", "| --- | ---: | ---: |"])
    for name in ("etymology", "lexicon", "base"):
        fam = report.families.get(name)
        if fam is None:
            lines.append(f"| {name} | 0 | 0 |")
            continue
        lines.append(f"| {name} | {fam.files:,} | {fam.bytes:,} ({format_bytes(fam.bytes)}) |")

    lines.extend(["", "### Largest files", ""])
    for size, rel in report.largest_files:
        lines.append(f"- `{rel}` — {size:,} ({format_bytes(size)})")

    if report.warnings:
        lines.extend(["", "### Warnings"])
        for warning in report.warnings:
            lines.append(f"- {warning}")
    if report.failures:
        lines.extend(["", "### Failures"])
        for failure in report.failures:
            lines.append(f"- {failure}")
    else:
        lines.extend(["", "**Result:** PASS"])

    return "\n".join(lines) + "\n"


def check_site_size(
    dist: Path,
    profile_name: str | None,
    *,
    largest_n: int = 15,
) -> tuple[SiteSizeReport, DeployProfile]:
    """Scan ``dist`` and apply the named profile thresholds."""
    profile = resolve_profile(profile_name)
    report = scan_dist(dist, largest_n=largest_n)
    apply_profile(report, profile)
    return report, profile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dist",
        type=Path,
        nargs="?",
        default=Path("site/dist"),
        help="Path to the built site dist directory (default: site/dist)",
    )
    parser.add_argument(
        "--profile",
        default=os.environ.get("DEPLOY_PROFILE"),
        help="Deploy profile name (default: $DEPLOY_PROFILE)",
    )
    parser.add_argument(
        "--largest",
        type=int,
        default=15,
        help="How many largest files to list (default: 15)",
    )
    args = parser.parse_args(argv)

    try:
        report, profile = check_site_size(args.dist, args.profile, largest_n=args.largest)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    text = format_report(report, profile)
    sys.stdout.write(text)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(text)

    for warning in report.warnings:
        print(f"::warning title=Pages budget::{warning}")
    for failure in report.failures:
        print(f"::error title=Pages budget::{failure}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
