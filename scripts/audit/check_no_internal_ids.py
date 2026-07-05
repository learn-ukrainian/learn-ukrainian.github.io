#!/usr/bin/env python3
"""Block internal source IDs and build-process register from learner surfaces."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "site" / "src" / "content" / "docs"
READINGS_DIR = PROJECT_ROOT / "site" / "src" / "content" / "readings"

SEMINAR_DOC_TRACKS = {
    "bio",
    "folk",
    "hist",
    "istorio",
    "lit",
    "lit-crimea",
    "lit-doc",
    "lit-drama",
    "lit-essay",
    "lit-fantastika",
    "lit-hist-fic",
    "lit-humor",
    "lit-war",
    "lit-youth",
    "oes",
    "ruth",
}

# Core l2-uk-en levels whose learner surfaces are guarded by this gate. Historically
# only folk + seminar tracks were scanned, which let internal-register jargon (chunk,
# "Wiki: pedagogy/…") accumulate in core content unchecked. Add a level here ONLY once
# it is clean, or the gate will block unrelated commits touching that level.
GUARDED_CORE_LEVELS = {"a1", "a2", "b1"}

FOLK_LEARNER_SOURCE_FILES = {
    "module.md",
    "activities.yaml",
    "activities.yml",
    "vocabulary.yaml",
    "vocabulary.yml",
    "resources.yaml",
    "resources.yml",
}


@dataclass(frozen=True)
class PatternSpec:
    kind: str
    pattern: re.Pattern[str]


INTERNAL_ID_PATTERNS = (
    PatternSpec("corpus chunk id", re.compile(r"\b[0-9a-f]{8}_c[0-9]{4}\b")),
    PatternSpec("source section id", re.compile(r"\bS[0-9]{3,4}\b")),
)

INTERNAL_REGISTER_PATTERNS = (
    PatternSpec("build/process term", re.compile(r"\bsource[ -]hammer\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bsource[ -]first\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bpublic[ -]readings?\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bhosted[ -]readings?\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\blearner[ -]facing\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bC1\+\s+learner\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\blesson[ -]body\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bUkrlib[ -]URL\b", re.IGNORECASE)),
    PatternSpec("English UI label", re.compile(r"\bTexts you'll read\b", re.IGNORECASE)),
    PatternSpec(
        "build/process term",
        re.compile(r"\b(?:chunk(?:_ids?)?s?|source_chunk(?:_ids?)?)\b", re.IGNORECASE),
    ),
    # Internal authoring cross-references dumped into resources.yaml that render
    # as bogus learner resources ("Wiki: pedagogy/…", "Synthesis of M42-M46 content",
    # "Internal module M43"). See scripts/audit/strip_internal_resource_entries.py.
    PatternSpec("internal resource ref", re.compile(r"Wiki:\s*pedagogy", re.IGNORECASE)),
    PatternSpec("internal resource ref", re.compile(r"\bSynthesis of M\d", re.IGNORECASE)),
    PatternSpec("internal resource ref", re.compile(r"\bInternal module M\d", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bcorpus[ -]ids?\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\binternal[ -]corpus\b", re.IGNORECASE)),
    # Resource-selection meta-commentary the writer narrated into `notes` fields,
    # e.g. "...alternations without exposing internal course notes." The keyword
    # allowlist deliberately has no bare `\binternal\b` (too many legitimate
    # learner uses), so this specific build-register phrase is anchored explicitly.
    PatternSpec("build/process term", re.compile(r"\binternal\s+course\s+notes\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bservice[ -]ids?\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bverify_quote\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bsource[ -]verification\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bvalidation[ -]workflow\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"службов\w*\s+позначк\w*", re.IGNORECASE)),
    PatternSpec(
        "build/process term",
        re.compile(r"(?:внутрішн\w*\s+)?корпусн\w*\s+ідентифікатор\w*", re.IGNORECASE),
    ),
    PatternSpec(
        "build/process term",
        re.compile(r"технічн\w*\s+інфраструктур\w*\s+джерел\w*", re.IGNORECASE),
    ),
)

FOLK_INTERNAL_REGISTER_PATTERNS = (
    PatternSpec("build/process term", re.compile(r"\bdossiers?\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bдосьє\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\blocked[ -]plan\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\blocked[ -]reading[ -]layer\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bdo[ -]not[ -]quote\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bgate[ -]safe\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"(?<!:)\bprimary[ -]reading\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bprovenance\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bsource[ -]disagreement\b", re.IGNORECASE)),
    PatternSpec("build/process term", re.compile(r"\bquote[ -]gated\b", re.IGNORECASE)),
    PatternSpec(
        "bare reading slug in prompt",
        re.compile(r"prompt=\{[^}]*\b[a-z][a-z0-9]+(?:-[a-z0-9]+){2,}\b[^}]*\}", re.IGNORECASE),
    ),
)

LEARNER_SURFACE_PATTERNS = (*INTERNAL_ID_PATTERNS, *INTERNAL_REGISTER_PATTERNS)

# `chunk_id:` / `packet_chunk_id:` keys in resources.yaml are load-bearing corpus
# provenance (consumed by linear_pipeline._plan_reference_match_gate) that the MDX
# renderer strips — they never reach a learner surface, so a bare provenance-key
# line is not a leak. Prose that mentions the term is still scanned.
_RESOURCE_PROVENANCE_KEY_RE = re.compile(r"^\s*(?:-\s*)?(?:packet_)?chunk_id\s*:", re.IGNORECASE)
_RESOURCE_FILENAMES = {"resources.yaml", "resources.yml"}

# HTML comments never reach a learner surface (the MDX/Markdown renderer strips them),
# so build-provenance inside an authoring marker like
# ``<!-- VERIFY: … chunk_id="7-klas-…_s0078" -->`` is not a leak. Blank the comment
# spans (keeping newlines + offsets so finding line/column stay accurate) before scanning.
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _blank_html_comments(text: str) -> str:
    return _HTML_COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


@dataclass(frozen=True, order=True)
class Finding:
    path: Path
    line_no: int
    column_no: int
    kind: str
    value: str

    def format(self) -> str:
        return f"{display_path(self.path)}:{self.line_no}:{self.column_no}: internal {self.kind} leaked: {self.value}"


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _as_absolute_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _repo_relative(path: Path) -> Path | None:
    try:
        return _as_absolute_path(path).resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None


def _dedupe(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique_paths: list[Path] = []
    for path in paths:
        normalized = path.resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_paths.append(path)
    return unique_paths


def _frontmatter(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index])
    return ""


def _frontmatter_bool_false(frontmatter: str, key: str) -> bool:
    return (
        re.search(
            rf"^\s*{re.escape(key)}\s*:\s*false\s*(?:#.*)?$",
            frontmatter,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        is not None
    )


def _is_routable_reading(path: Path) -> bool:
    frontmatter = _frontmatter(path)
    return not (_frontmatter_bool_false(frontmatter, "published") or _frontmatter_bool_false(frontmatter, "canonical"))


def _frontmatter_tracks_folk(frontmatter: str) -> bool:
    return bool(
        re.search(r"^\s*tracks\s*:\s*folk\s*$", frontmatter, flags=re.IGNORECASE | re.MULTILINE)
        or re.search(r"^\s*tracks\s*:\s*\[[^\]]*\bfolk\b[^\]]*\]\s*$", frontmatter, flags=re.IGNORECASE | re.MULTILINE)
        or re.search(r"^\s*-\s*folk\s*$", frontmatter, flags=re.IGNORECASE | re.MULTILINE)
    )


def _is_folk_learner_surface(path: Path) -> bool:
    rel_path = _repo_relative(path)
    if rel_path is None:
        return False

    parts = rel_path.parts
    if len(parts) >= 5 and parts[:4] == ("site", "src", "content", "docs") and parts[4] == "folk":
        return True
    if len(parts) >= 4 and parts[:4] == ("site", "src", "content", "readings"):
        return _frontmatter_tracks_folk(_frontmatter(path))
    return len(parts) == 5 and parts[:3] == ("curriculum", "l2-uk-en", "folk") and parts[4] in FOLK_LEARNER_SOURCE_FILES


def _learner_surface_patterns(path: Path) -> tuple[PatternSpec, ...]:
    if _is_folk_learner_surface(path):
        return (*LEARNER_SURFACE_PATTERNS, *FOLK_INTERNAL_REGISTER_PATTERNS)
    return LEARNER_SURFACE_PATTERNS


def is_published_seminar_mdx(path: Path, *, allow_external: bool = False) -> bool:
    suffix = path.suffix.lower()
    if suffix not in {".md", ".mdx", ".yaml", ".yml"}:
        return False

    rel_path = _repo_relative(path)
    if rel_path is None:
        return allow_external and suffix == ".mdx"

    parts = rel_path.parts
    if len(parts) >= 5 and parts[:4] == ("site", "src", "content", "readings"):
        return suffix == ".mdx" and _is_routable_reading(path)

    if len(parts) >= 6 and parts[:4] == ("site", "src", "content", "docs"):
        return suffix == ".mdx" and parts[4] in (SEMINAR_DOC_TRACKS | GUARDED_CORE_LEVELS)

    return (
        len(parts) == 5
        and parts[:2] == ("curriculum", "l2-uk-en")
        and parts[2] in (GUARDED_CORE_LEVELS | {"folk"})
        and parts[4] in FOLK_LEARNER_SOURCE_FILES
    )


def scan_candidates(paths: list[Path], *, allow_external: bool = False) -> list[Path]:
    candidates: list[Path] = []
    for raw_path in paths:
        path = _as_absolute_path(raw_path)
        if not path.is_file():
            continue
        if is_published_seminar_mdx(path, allow_external=allow_external):
            candidates.append(path)
    return _dedupe(candidates)


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    is_resources = path.name in _RESOURCE_FILENAMES
    text = _blank_html_comments(path.read_text(encoding="utf-8"))
    for line_no, line in enumerate(text.splitlines(), start=1):
        if is_resources and _RESOURCE_PROVENANCE_KEY_RE.match(line):
            continue
        for spec in _learner_surface_patterns(path):
            for match in spec.pattern.finditer(line):
                findings.append(
                    Finding(
                        path=path,
                        line_no=line_no,
                        column_no=match.start() + 1,
                        kind=spec.kind,
                        value=match.group(0),
                    )
                )
    return findings


def scan_files(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_file(path))
    return sorted(findings)


def _git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=PROJECT_ROOT, text=True)


def get_changed_files(base: str) -> list[Path]:
    merge_base = _git_output(["merge-base", base, "HEAD"]).strip()
    output = _git_output(["diff", "--name-only", f"{merge_base}...HEAD"])
    return [PROJECT_ROOT / line for line in output.splitlines() if line]


def get_local_changed_files(*, cached: bool = False) -> list[Path]:
    cmd = ["diff", "--name-only"]
    if cached:
        cmd.append("--cached")
    output = _git_output(cmd)
    return [PROJECT_ROOT / line for line in output.splitlines() if line]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check learner surfaces for internal source IDs and build-process register."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--changed-vs-base", metavar="BASE", help="Compare base branch, e.g. origin/main")
    group.add_argument("--files", nargs="+", type=Path, help="Scan explicit files, e.g. from pre-commit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.changed_vs_base:
        raw_paths = [
            *get_changed_files(args.changed_vs_base),
            *get_local_changed_files(),
            *get_local_changed_files(cached=True),
        ]
        candidates = scan_candidates(raw_paths)
    else:
        candidates = scan_candidates(args.files, allow_external=True)

    if not candidates:
        print("0 findings: no learner surface files to scan.")
        return 0

    findings = scan_files(candidates)
    if not findings:
        print(
            f"0 findings: no internal source IDs or build-process register in "
            f"{len(candidates)} learner surface file(s)."
        )
        return 0

    for finding in findings:
        print(finding.format())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
