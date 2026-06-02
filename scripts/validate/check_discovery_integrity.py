#!/usr/bin/env python3
"""Validate BIO discovery topics against their source plan subjects.

The BIO discovery files are source-first inputs for wiki compilation. A prior
corruption copied Mykola Kulish discovery topics/objectives into unrelated
figure files. This gate flags discovery topics whose likely surname does not
match the corresponding immutable plan title.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

try:
    from validate.bio_subjects import PROJECT_ROOT, load_plan_title, shares_surname
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from validate.bio_subjects import PROJECT_ROOT, load_plan_title, shares_surname


CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"


@dataclass(frozen=True)
class DiscoveryFinding:
    slug: str
    discovery_path: str
    topic: str
    plan_title: str
    reason: str


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def discovery_topic(data: dict) -> str:
    """Return the primary discovery topic string."""
    keywords = data.get("query_keywords")
    if isinstance(keywords, list):
        for item in keywords:
            if isinstance(item, str) and item.strip():
                return item.strip()
    for key in ("topic", "title"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def check_discovery_file(
    discovery_path: Path,
    *,
    plan_title: str | None = None,
) -> DiscoveryFinding | None:
    """Return a finding when a discovery topic names a different subject."""
    slug = discovery_path.stem
    data = _load_yaml(discovery_path)
    topic = discovery_topic(data)
    expected_title = plan_title if plan_title is not None else load_plan_title(slug)
    if not expected_title:
        return DiscoveryFinding(
            slug=slug,
            discovery_path=_relative(discovery_path),
            topic=topic,
            plan_title="",
            reason="missing plan title",
        )
    if not topic:
        return DiscoveryFinding(
            slug=slug,
            discovery_path=_relative(discovery_path),
            topic="",
            plan_title=expected_title,
            reason="missing discovery topic",
        )
    if shares_surname(topic, expected_title):
        return None
    return DiscoveryFinding(
        slug=slug,
        discovery_path=_relative(discovery_path),
        topic=topic,
        plan_title=expected_title,
        reason="discovery topic shares no 4+ character surname token with plan title",
    )


def iter_discovery_paths(track: str) -> list[Path]:
    discovery_dir = CURRICULUM_DIR / track / "discovery"
    return sorted(discovery_dir.glob("*.yaml"))


def check_track(track: str) -> list[DiscoveryFinding]:
    findings: list[DiscoveryFinding] = []
    for path in iter_discovery_paths(track):
        finding = check_discovery_file(path)
        if finding:
            findings.append(finding)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", default="bio", help="Track to scan (default: bio).")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = parser.parse_args(argv)

    paths = iter_discovery_paths(args.track)
    findings = check_track(args.track)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        for finding in findings:
            print(f"{finding.discovery_path}: {finding.reason}")
            print(f"  slug: {finding.slug}")
            print(f"  topic: {finding.topic}")
            print(f"  plan-title: {finding.plan_title}")
        print(f"Scanned {len(paths)} discovery file(s) · {len(findings)} mismatch(es)")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
