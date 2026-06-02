#!/usr/bin/env python3
"""Validate compiled BIO figure wiki H1 subjects against file slugs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from validate.bio_subjects import PROJECT_ROOT, load_plan_title, same_person
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from validate.bio_subjects import PROJECT_ROOT, load_plan_title, same_person


WIKI_FIGURES_DIR = PROJECT_ROOT / "wiki" / "figures"
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
WIKI_META_RE = re.compile(r"<!--\s*wiki-meta\b(?P<body>.*?)-->", re.DOTALL)
YAML_FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)
SLUG_RE = re.compile(r"^\s*slug:\s*['\"]?(?P<slug>[^'\"\s]+)", re.MULTILINE)


@dataclass(frozen=True)
class WikiSubjectFinding:
    path: str
    file_slug: str
    frontmatter_slug: str
    h1: str
    plan_title: str
    reason: str


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def first_h1(text: str) -> str:
    match = H1_RE.search(text)
    return match.group(1).strip() if match else ""


def frontmatter_slug(text: str) -> str:
    for match in (YAML_FRONTMATTER_RE.search(text), WIKI_META_RE.search(text)):
        if not match:
            continue
        slug_match = SLUG_RE.search(match.group("body"))
        if slug_match:
            return slug_match.group("slug").strip()
    slug_match = SLUG_RE.search(text)
    return slug_match.group("slug").strip() if slug_match else ""


def check_wiki_file(path: Path, *, plan_title: str | None = None) -> WikiSubjectFinding | None:
    """Return a finding when the wiki H1 names a different BIO subject."""
    text = path.read_text(encoding="utf-8")
    file_slug = path.stem
    h1 = first_h1(text)
    meta_slug = frontmatter_slug(text)
    expected_title = plan_title if plan_title is not None else load_plan_title(file_slug)
    if not expected_title:
        return WikiSubjectFinding(
            path=_relative(path),
            file_slug=file_slug,
            frontmatter_slug=meta_slug,
            h1=h1,
            plan_title="",
            reason="missing plan title for file slug",
        )
    if not h1:
        return WikiSubjectFinding(
            path=_relative(path),
            file_slug=file_slug,
            frontmatter_slug=meta_slug,
            h1="",
            plan_title=expected_title,
            reason="missing H1",
        )
    if same_person(h1, expected_title):
        return None
    return WikiSubjectFinding(
        path=_relative(path),
        file_slug=file_slug,
        frontmatter_slug=meta_slug,
        h1=h1,
        plan_title=expected_title,
        reason="H1 subject does not match file slug plan title",
    )


def iter_wiki_paths(paths: list[str] | None = None) -> list[Path]:
    if not paths:
        return sorted(WIKI_FIGURES_DIR.glob("*.md"))
    resolved: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            resolved.extend(sorted(path.glob("*.md")))
        else:
            resolved.append(path)
    return resolved


def check_paths(paths: list[Path]) -> list[WikiSubjectFinding]:
    findings: list[WikiSubjectFinding] = []
    for path in paths:
        finding = check_wiki_file(path)
        if finding:
            findings.append(finding)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", nargs="*", help="Explicit wiki files/directories.")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = parser.parse_args(argv)

    paths = iter_wiki_paths(args.paths)
    findings = check_paths(paths)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        for finding in findings:
            print(f"{finding.path}: {finding.reason}")
            print(f"  file-slug: {finding.file_slug}")
            print(f"  frontmatter-slug: {finding.frontmatter_slug}")
            print(f"  h1: {finding.h1}")
            print(f"  plan-title: {finding.plan_title}")
        print(f"Scanned {len(paths)} wiki figure file(s) · {len(findings)} subject mismatch(es)")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
