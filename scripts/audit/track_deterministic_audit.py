#!/usr/bin/env python3
"""Reusable deterministic track audit runner.

The runner is manifest-driven, read-only by default, and intentionally excludes
old LLM-QG persistence until issue #2156 defines the replacement path.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from audit.check_no_internal_ids import (
    INTERNAL_ID_PATTERNS,
    INTERNAL_REGISTER_PATTERNS,
    _blank_html_comments,
)
from audit.checks.yaml_schema_validation import validate_activity_yaml_file
from audit.content_surface_gates import scan_module_surface
from manifest_utils import get_modules_for_level
from wiki.domains import resolve_write_domain

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SITE_DOCS_ROOT = PROJECT_ROOT / "site" / "src" / "content" / "docs"
SITE_READINGS_ROOT = PROJECT_ROOT / "site" / "src" / "content" / "readings"
DEFAULT_CONFIG = PROJECT_ROOT / "scripts" / "audit" / "track_deterministic_audit_config.yaml"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

VALID_POS = {
    "noun",
    "verb",
    "adj",
    "adv",
    "pron",
    "prep",
    "conj",
    "part",
    "intj",
    "num",
    "phrase",
    "propn",
    "other",
    "suffix",
    "prefix",
}
VALID_GENDER = {"m", "f", "n", "pl", "-", ""}

SEVERITY_ORDER = {"blocker": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
FAIL_ON_CHOICES = ("blocker", "high", "medium", "low", "info", "never")

PROTECTED_CONFIGS = {
    ".python-version",
    ".yamllint",
    ".markdownlint.json",
    "package.json",
    "package-lock.json",
}
FORBIDDEN_DIFF_RE = re.compile(
    r"(^|/)status/.*\.json$"
    r"|(^|/)audit/.*-review\.md$"
    r"|(^|/)review/.*-review\.md$"
    r"|^docs/.*-STATUS\.md$"
    r"|^data/telemetry/"
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_LINK_RE = re.compile(r"""\b(?:href|to)=["']([^"']+)["']""")


@dataclass(frozen=True)
class Finding:
    track: str
    module_num: int | None
    slug: str | None
    category: str
    severity: str
    file: str | None
    line: int | None
    message: str
    evidence: str
    auto_fixable: bool
    recommended_remediation_batch: str
    judgement_required: bool = False

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SkippedCheck:
    category: str
    reason: str
    track: str
    module_num: int | None = None
    slug: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModulePaths:
    track: str
    module_num: int
    slug: str
    title: str
    module_dir: Path
    plan: Path
    module_md: Path
    activities: Path
    vocabulary: Path
    resources: Path
    wiki: Path
    wiki_sources: Path
    site_mdx: Path

    def file_for_key(self, key: str) -> Path:
        return getattr(self, key)

    @property
    def built(self) -> bool:
        return self.module_md.exists()


def display_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def merged_track_config(config: dict[str, Any], track: str) -> dict[str, Any]:
    defaults = config.get("defaults") if isinstance(config.get("defaults"), dict) else {}
    tracks = config.get("tracks") if isinstance(config.get("tracks"), dict) else {}
    track_config = tracks.get(track) if isinstance(tracks.get(track), dict) else {}

    merged = dict(defaults)
    for key, value in track_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def parse_range(value: str | None) -> tuple[int, int] | None:
    if value is None:
        return None
    match = re.fullmatch(r"(\d+)-(\d+)", value.strip())
    if not match:
        raise argparse.ArgumentTypeError(f"Range must be N-M, got: {value}")
    start, end = int(match.group(1)), int(match.group(2))
    if start < 1 or end < start:
        raise argparse.ArgumentTypeError(f"Invalid module range: {value}")
    return start, end


def parse_slug_filter(values: list[str] | None) -> set[str] | None:
    if not values:
        return None
    slugs: set[str] = set()
    for value in values:
        slugs.update(part.strip() for part in value.split(",") if part.strip())
    return slugs or None


def module_paths(track: str, module: Any) -> ModulePaths:
    slug = module.slug
    module_dir = CURRICULUM_ROOT / track / slug
    wiki_root = PROJECT_ROOT / "wiki" / resolve_write_domain(track, slug)
    return ModulePaths(
        track=track,
        module_num=int(module.local_num),
        slug=slug,
        title=str(getattr(module, "title", slug)),
        module_dir=module_dir,
        plan=CURRICULUM_ROOT / "plans" / track / f"{slug}.yaml",
        module_md=module_dir / "module.md",
        activities=module_dir / "activities.yaml",
        vocabulary=module_dir / "vocabulary.yaml",
        resources=module_dir / "resources.yaml",
        wiki=wiki_root / f"{slug}.md",
        wiki_sources=wiki_root / f"{slug}.sources.yaml",
        site_mdx=SITE_DOCS_ROOT / track / f"{slug}.mdx",
    )


def select_modules(track: str, range_filter: tuple[int, int] | None, slugs: set[str] | None) -> list[ModulePaths]:
    modules = [module_paths(track, module) for module in get_modules_for_level(track)]
    if range_filter is not None:
        start, end = range_filter
        modules = [module for module in modules if start <= module.module_num <= end]
    if slugs is not None:
        modules = [module for module in modules if module.slug in slugs]
    return modules


def finding(
    paths: ModulePaths | None,
    *,
    track: str,
    category: str,
    severity: str,
    file: Path | None,
    line: int | None,
    message: str,
    evidence: str,
    auto_fixable: bool,
    recommended_remediation_batch: str,
    judgement_required: bool = False,
) -> Finding:
    return Finding(
        track=paths.track if paths is not None else track,
        module_num=paths.module_num if paths is not None else None,
        slug=paths.slug if paths is not None else None,
        category=category,
        severity=severity,
        file=display_path(file),
        line=line,
        message=message,
        evidence=evidence[:500],
        auto_fixable=auto_fixable,
        recommended_remediation_batch=recommended_remediation_batch,
        judgement_required=judgement_required,
    )


def check_inventory(paths: ModulePaths, config: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    required_files = config.get("required_files") or []
    optional_files = config.get("optional_files") or []
    severity_cfg = config.get("severity") if isinstance(config.get("severity"), dict) else {}
    required_severity = severity_cfg.get("missing_required_file", "high")
    optional_severity = severity_cfg.get("optional_missing", "info")

    for key in required_files:
        path = paths.file_for_key(str(key))
        if not path.exists():
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="inventory",
                    severity=required_severity,
                    file=path,
                    line=None,
                    message=f"Required artifact is missing: {key}",
                    evidence=display_path(path) or str(path),
                    auto_fixable=False,
                    recommended_remediation_batch="inventory-and-source-presence",
                )
            )

    for key in optional_files:
        path = paths.file_for_key(str(key))
        if not path.exists():
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="inventory",
                    severity=optional_severity,
                    file=path,
                    line=None,
                    message=f"Optional artifact is absent: {key}",
                    evidence=display_path(path) or str(path),
                    auto_fixable=False,
                    recommended_remediation_batch="inventory-and-source-presence",
                )
            )
    return findings


def check_activity_yaml(paths: ModulePaths) -> list[Finding]:
    if not paths.activities.exists():
        return []
    is_valid, errors = validate_activity_yaml_file(paths.activities)
    if is_valid:
        return []
    return [
        finding(
            paths,
            track=paths.track,
            category="activity_validity",
            severity="high",
            file=paths.activities,
            line=None,
            message="Activity YAML failed deterministic validation.",
            evidence=error,
            auto_fixable=False,
            recommended_remediation_batch="activity-yaml-validation",
        )
        for error in errors
    ]


def vocabulary_items(data: Any) -> tuple[list[Any] | None, bool]:
    if isinstance(data, list):
        return data, False
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"], True
    return None, False


def check_vocabulary_yaml(paths: ModulePaths) -> list[Finding]:
    if not paths.vocabulary.exists():
        return []
    findings: list[Finding] = []
    try:
        data = yaml.safe_load(paths.vocabulary.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [
            finding(
                paths,
                track=paths.track,
                category="vocabulary_validity",
                severity="high",
                file=paths.vocabulary,
                line=None,
                message="Vocabulary YAML could not be parsed.",
                evidence=str(exc),
                auto_fixable=False,
                recommended_remediation_batch="vocabulary-yaml-validation",
            )
        ]

    items, enriched_schema = vocabulary_items(data)
    if items is None:
        return [
            finding(
                paths,
                track=paths.track,
                category="vocabulary_validity",
                severity="high",
                file=paths.vocabulary,
                line=None,
                message="Vocabulary YAML uses an unsupported schema.",
                evidence="Expected a bare list or a mapping with an items list.",
                auto_fixable=False,
                recommended_remediation_batch="vocabulary-yaml-validation",
            )
        ]

    lemmas: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="vocabulary_validity",
                    severity="high",
                    file=paths.vocabulary,
                    line=None,
                    message="Vocabulary item is not a mapping.",
                    evidence=f"item_index={index}",
                    auto_fixable=False,
                    recommended_remediation_batch="vocabulary-yaml-validation",
                )
            )
            continue

        lemma = item.get("lemma") if enriched_schema else item.get("word") or item.get("lemma")
        if not lemma:
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="vocabulary_validity",
                    severity="high",
                    file=paths.vocabulary,
                    line=None,
                    message="Vocabulary item is missing lemma or word.",
                    evidence=f"item_index={index}",
                    auto_fixable=False,
                    recommended_remediation_batch="vocabulary-yaml-validation",
                )
            )
            continue

        lemma = str(lemma)
        if lemma in lemmas:
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="vocabulary_validity",
                    severity="medium",
                    file=paths.vocabulary,
                    line=None,
                    message="Vocabulary YAML contains a duplicate lemma.",
                    evidence=lemma,
                    auto_fixable=True,
                    recommended_remediation_batch="vocabulary-yaml-validation",
                )
            )
        lemmas.add(lemma)

        if not item.get("translation"):
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="vocabulary_validity",
                    severity="high",
                    file=paths.vocabulary,
                    line=None,
                    message="Vocabulary item is missing translation.",
                    evidence=lemma,
                    auto_fixable=False,
                    recommended_remediation_batch="vocabulary-yaml-validation",
                )
            )

        if not enriched_schema:
            continue
        if not item.get("ipa"):
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="vocabulary_validity",
                    severity="medium",
                    file=paths.vocabulary,
                    line=None,
                    message="Enriched vocabulary item is missing IPA.",
                    evidence=lemma,
                    auto_fixable=False,
                    recommended_remediation_batch="vocabulary-yaml-validation",
                )
            )
        pos = item.get("pos", "other")
        if pos not in VALID_POS:
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="vocabulary_validity",
                    severity="medium",
                    file=paths.vocabulary,
                    line=None,
                    message="Vocabulary item has invalid POS.",
                    evidence=f"{lemma}: {pos}",
                    auto_fixable=False,
                    recommended_remediation_batch="vocabulary-yaml-validation",
                )
            )
        if pos == "noun":
            gender = item.get("gender", "")
            if not gender or gender not in VALID_GENDER:
                findings.append(
                    finding(
                        paths,
                        track=paths.track,
                        category="vocabulary_validity",
                        severity="medium",
                        file=paths.vocabulary,
                        line=None,
                        message="Noun vocabulary item has missing or invalid gender.",
                        evidence=f"{lemma}: {gender}",
                        auto_fixable=False,
                        recommended_remediation_batch="vocabulary-yaml-validation",
                    )
                )
    return findings


def iter_urls(value: Any, location: str = "") -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_location = f"{location}.{key}" if location else str(key)
            if key == "url" and isinstance(item, str):
                urls.append((item, next_location))
            else:
                urls.extend(iter_urls(item, next_location))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            urls.extend(iter_urls(item, f"{location}[{index}]"))
    return urls


def check_resources_yaml(paths: ModulePaths) -> list[Finding]:
    if not paths.resources.exists():
        return []
    findings: list[Finding] = []
    try:
        data = yaml.safe_load(paths.resources.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [
            finding(
                paths,
                track=paths.track,
                category="resource_presence",
                severity="high",
                file=paths.resources,
                line=None,
                message="Resources YAML could not be parsed.",
                evidence=str(exc),
                auto_fixable=False,
                recommended_remediation_batch="resource-yaml-validation",
            )
        ]

    if data is None:
        findings.append(
            finding(
                paths,
                track=paths.track,
                category="resource_presence",
                severity="medium",
                file=paths.resources,
                line=None,
                message="Resources YAML is empty.",
                evidence=display_path(paths.resources) or str(paths.resources),
                auto_fixable=False,
                recommended_remediation_batch="resource-yaml-validation",
            )
        )
        return findings

    for url, location in iter_urls(data):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="resource_presence",
                    severity="medium",
                    file=paths.resources,
                    line=None,
                    message="Resource URL is not an absolute HTTP(S) URL.",
                    evidence=f"{location}: {url}",
                    auto_fixable=False,
                    recommended_remediation_batch="resource-yaml-validation",
                )
            )
    return findings


def surface_severity(item: dict[str, Any]) -> str:
    raw = str(item.get("severity", "")).lower()
    kind = str(item.get("type", ""))
    if raw == "critical" and kind in {"ai_leakage", "path_leakage", "ukrainian_grammar_calque"}:
        return "blocker"
    if raw == "critical":
        return "high"
    if raw == "warning":
        return "medium"
    if raw == "info":
        return "info"
    return "low"


def check_surface(paths: ModulePaths) -> list[Finding]:
    if not paths.built:
        return []
    report = scan_module_surface(paths.module_dir, level=paths.track)
    findings: list[Finding] = []
    for item in report.get("findings", []):
        source = str(item.get("source") or "module.md")
        source_path = paths.module_dir / source
        kind = str(item.get("type") or "surface")
        findings.append(
            finding(
                paths,
                track=paths.track,
                category="english_internal_leakage",
                severity=surface_severity(item),
                file=source_path,
                line=item.get("line") if isinstance(item.get("line"), int) and item.get("line") > 0 else None,
                message=str(item.get("message") or kind),
                evidence=f"{kind}: {item.get('text', '')}",
                auto_fixable=False,
                recommended_remediation_batch="surface-leakage-review",
                judgement_required=kind in {"english_led_line", "english_ratio"},
            )
        )
    return findings


# `chunk_id` / `packet_chunk_id` keys in resources.yaml are internal
# corpus-provenance metadata consumed by the plan-reference gate
# (linear_pipeline._plan_reference_match_gate / _resource_chunk_id). The MDX
# renderer strips them, so a bare provenance-key line never reaches a learner
# surface and is not a leak. Prose that *mentions* the term (title/notes/lesson
# body, or the rendered .mdx) is still scanned and still flagged.
_RESOURCE_FILENAMES = {"resources.yaml", "resources.yml"}
_RESOURCE_PROVENANCE_KEY_RE = re.compile(
    r"^\s*(?:-\s*)?(?:packet_)?chunk_id\s*:", re.IGNORECASE
)


def check_internal_leakage(paths: ModulePaths) -> list[Finding]:
    candidate_files = [
        paths.module_md,
        paths.activities,
        paths.vocabulary,
        paths.resources,
        paths.site_mdx,
    ]
    patterns = (*INTERNAL_ID_PATTERNS, *INTERNAL_REGISTER_PATTERNS)
    findings: list[Finding] = []
    for path in candidate_files:
        if not path.exists():
            continue
        is_resources = path.name in _RESOURCE_FILENAMES
        # HTML comments (e.g. <!-- VERIFY: … chunk_id="…" -->) never render, so blank
        # them before scanning, consistent with check_no_internal_ids.scan_file.
        text = _blank_html_comments(path.read_text(encoding="utf-8"))
        for line_no, line in enumerate(text.splitlines(), start=1):
            if is_resources and _RESOURCE_PROVENANCE_KEY_RE.match(line):
                # Non-rendering provenance key — not a learner surface.
                continue
            for spec in patterns:
                for match in spec.pattern.finditer(line):
                    findings.append(
                        finding(
                            paths,
                            track=paths.track,
                            category="internal_leakage",
                            severity="blocker",
                            file=path,
                            line=line_no,
                            message=f"Internal {spec.kind} leaked to learner surface.",
                            evidence=match.group(0),
                            auto_fixable=False,
                            recommended_remediation_batch="surface-leakage-review",
                            judgement_required=True,
                        )
                    )
    return findings


def link_targets(text: str) -> list[tuple[str, int]]:
    targets: list[tuple[str, int]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for regex in (MARKDOWN_LINK_RE, HTML_LINK_RE):
            for match in regex.finditer(line):
                targets.append((match.group(1), line_no))
    return targets


def route_path_exists(track: str, current_mdx: Path, raw_target: str) -> bool:
    target = raw_target.split("#", 1)[0].strip()
    if not target or target.startswith(("#", "mailto:", "tel:")):
        return True
    parsed = urlparse(target)
    if parsed.scheme in {"http", "https"}:
        return True
    if target.startswith("{") or target.startswith("@"):
        return True

    if target.startswith("/"):
        parts = [part for part in target.strip("/").split("/") if part]
        if not parts:
            return True
        if parts[0] == "readings" and len(parts) >= 2:
            return (SITE_READINGS_ROOT / f"{parts[1]}.mdx").exists()
        docs_path = SITE_DOCS_ROOT.joinpath(*parts)
        return docs_path.with_suffix(".mdx").exists() or (docs_path / "index.mdx").exists()

    resolved = (current_mdx.parent / target).resolve()
    if resolved.suffix:
        return resolved.exists()
    return resolved.with_suffix(".mdx").exists() or (resolved / "index.mdx").exists()


def check_mdx_routes(paths: ModulePaths) -> list[Finding]:
    findings: list[Finding] = []
    index_path = SITE_DOCS_ROOT / paths.track / "index.mdx"
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        if f'slug: "{paths.slug}"' not in index_text and f"slug: '{paths.slug}'" not in index_text:
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="mdx_index_parity",
                    severity="high",
                    file=index_path,
                    line=None,
                    message="Track landing/index MDX does not list the module slug.",
                    evidence=paths.slug,
                    auto_fixable=True,
                    recommended_remediation_batch="mdx-route-parity",
                )
            )
    else:
        findings.append(
            finding(
                paths,
                track=paths.track,
                category="mdx_index_parity",
                severity="high",
                file=index_path,
                line=None,
                message="Track landing/index MDX is missing.",
                evidence=display_path(index_path) or str(index_path),
                auto_fixable=True,
                recommended_remediation_batch="mdx-route-parity",
            )
        )

    if not paths.site_mdx.exists():
        return findings

    text = paths.site_mdx.read_text(encoding="utf-8")
    for target, line_no in link_targets(text):
        if not route_path_exists(paths.track, paths.site_mdx, target):
            findings.append(
                finding(
                    paths,
                    track=paths.track,
                    category="link_route_health",
                    severity="high",
                    file=paths.site_mdx,
                    line=line_no,
                    message="Learner-facing MDX link target does not resolve to a local route.",
                    evidence=target,
                    auto_fixable=False,
                    recommended_remediation_batch="mdx-route-parity",
                )
            )
    return findings


def git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=PROJECT_ROOT, text=True)


def changed_files_for_diff_gate() -> list[str]:
    files: set[str] = set()
    for args in (["diff", "--name-only"], ["diff", "--cached", "--name-only"], ["ls-files", "--others", "--exclude-standard"]):
        output = git_output(args)
        files.update(line.strip() for line in output.splitlines() if line.strip())
    return sorted(files)


def protected_config_changed() -> list[str]:
    changed: list[str] = []
    for path in sorted(PROTECTED_CONFIGS):
        result = subprocess.run(
            ["git", "diff", "--quiet", "--", path],
            cwd=PROJECT_ROOT,
            check=False,
        )
        staged = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", path],
            cwd=PROJECT_ROOT,
            check=False,
        )
        if result.returncode != 0 or staged.returncode != 0:
            changed.append(path)
    return changed


def check_protected_diff(track: str) -> list[Finding]:
    findings: list[Finding] = []
    for path in changed_files_for_diff_gate():
        if FORBIDDEN_DIFF_RE.search(path):
            findings.append(
                finding(
                    None,
                    track=track,
                    category="protected_artifact_hygiene",
                    severity="blocker",
                    file=PROJECT_ROOT / path,
                    line=None,
                    message="Forbidden generated artifact or telemetry path appears in the diff.",
                    evidence=path,
                    auto_fixable=True,
                    recommended_remediation_batch="protected-artifact-cleanup",
                )
            )
    for path in protected_config_changed():
        findings.append(
            finding(
                None,
                track=track,
                category="protected_artifact_hygiene",
                severity="blocker",
                file=PROJECT_ROOT / path,
                line=None,
                message="Protected config/package file is modified.",
                evidence=path,
                auto_fixable=False,
                recommended_remediation_batch="protected-config-cleanup",
            )
        )
    return findings


def run_mdx_validate(paths: ModulePaths) -> list[Finding]:
    before = paths.site_mdx.read_bytes() if paths.site_mdx.exists() else None
    result = subprocess.run(
        [
            str(VENV_PYTHON),
            "scripts/generate_mdx.py",
            "l2-uk-en",
            paths.track,
            str(paths.module_num),
            "--validate",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    after = paths.site_mdx.read_bytes() if paths.site_mdx.exists() else None
    drifted = before != after
    if drifted and before is not None:
        paths.site_mdx.write_bytes(before)
    if result.returncode == 0 and not drifted:
        return []
    return [
        finding(
            paths,
            track=paths.track,
            category="mdx_generation_validate",
            severity="high",
            file=paths.site_mdx,
            line=None,
            message="MDX generation validation failed or produced drift.",
            evidence=f"returncode={result.returncode}; drifted={drifted}; stdout={result.stdout[-300:]} stderr={result.stderr[-300:]}",
            auto_fixable=drifted,
            recommended_remediation_batch="mdx-route-parity",
        )
    ]


def audit_track(
    *,
    track: str,
    config: dict[str, Any],
    range_filter: tuple[int, int] | None,
    slugs: set[str] | None,
    run_mdx_generation_validate: bool,
) -> dict[str, Any]:
    track_config = merged_track_config(config, track)
    checks = track_config.get("checks") if isinstance(track_config.get("checks"), dict) else {}
    modules = select_modules(track, range_filter, slugs)
    findings: list[Finding] = []
    skipped: list[SkippedCheck] = [
        SkippedCheck(
            category="llm_qg",
            reason="excluded pending issue #2156; old LLM-QG rows are not read or recreated",
            track=track,
        )
    ]

    if not modules:
        findings.append(
            finding(
                None,
                track=track,
                category="inventory",
                severity="blocker",
                file=CURRICULUM_ROOT / "curriculum.yaml",
                line=None,
                message="No modules selected for track audit.",
                evidence=f"track={track}",
                auto_fixable=False,
                recommended_remediation_batch="inventory-and-source-presence",
            )
        )

    for paths in modules:
        findings.extend(check_inventory(paths, track_config))
        if checks.get("activity_yaml", True):
            findings.extend(check_activity_yaml(paths))
        else:
            skipped.append(SkippedCheck("activity_validity", "disabled by config", track, paths.module_num, paths.slug))
        if checks.get("vocabulary_yaml", True):
            findings.extend(check_vocabulary_yaml(paths))
        else:
            skipped.append(SkippedCheck("vocabulary_validity", "disabled by config", track, paths.module_num, paths.slug))
        if checks.get("resources_yaml", True):
            findings.extend(check_resources_yaml(paths))
        else:
            skipped.append(SkippedCheck("resource_presence", "disabled by config", track, paths.module_num, paths.slug))
        if checks.get("surface_gates", True):
            findings.extend(check_surface(paths))
        else:
            skipped.append(SkippedCheck("english_internal_leakage", "disabled by config", track, paths.module_num, paths.slug))
        if checks.get("internal_leakage", True):
            findings.extend(check_internal_leakage(paths))
        else:
            skipped.append(SkippedCheck("internal_leakage", "disabled by config", track, paths.module_num, paths.slug))
        if checks.get("mdx_routes", True):
            findings.extend(check_mdx_routes(paths))
        else:
            skipped.append(SkippedCheck("link_route_health", "disabled by config", track, paths.module_num, paths.slug))

        if run_mdx_generation_validate or checks.get("mdx_generation_validate", False):
            findings.extend(run_mdx_validate(paths))
        else:
            skipped.append(
                SkippedCheck(
                    "mdx_generation_validate",
                    "skipped by default because generate_mdx.py rewrites site MDX before validating",
                    track,
                    paths.module_num,
                    paths.slug,
                )
            )

        if not checks.get("external_resource_liveness", False):
            skipped.append(
                SkippedCheck(
                    "external_resource_liveness",
                    "skipped by default because live URL checks are network-dependent",
                    track,
                    paths.module_num,
                    paths.slug,
                )
            )

    if checks.get("protected_diff", True):
        findings.extend(check_protected_diff(track))
    else:
        skipped.append(SkippedCheck("protected_artifact_hygiene", "disabled by config", track))

    return build_result(track=track, modules=modules, findings=findings, skipped=skipped)


def build_result(
    *,
    track: str,
    modules: list[ModulePaths],
    findings: list[Finding],
    skipped: list[SkippedCheck],
) -> dict[str, Any]:
    by_severity = Counter(item.severity for item in findings)
    by_category = Counter(item.category for item in findings)
    auto_fixable = sum(1 for item in findings if item.auto_fixable)
    judgement_required = sum(1 for item in findings if item.judgement_required)
    deterministic_failures = len(findings) - judgement_required
    built_count = sum(1 for item in modules if item.built)
    module_findings: dict[str, int] = defaultdict(int)
    for item in findings:
        if item.slug:
            module_findings[item.slug] += 1

    return {
        "track": track,
        "summary": {
            "modules_selected": len(modules),
            "modules_built": built_count,
            "modules_not_built": len(modules) - built_count,
            "findings_total": len(findings),
            "findings_by_severity": {key: by_severity.get(key, 0) for key in SEVERITY_ORDER},
            "findings_by_category": dict(sorted(by_category.items())),
            "modules_with_findings": len(module_findings),
            "auto_fixable_findings": auto_fixable,
            "remediation_only_findings": len(findings) - auto_fixable,
            "deterministic_failures": deterministic_failures,
            "judgement_required_content_work": judgement_required,
            "skipped_checks": len(skipped),
            "llm_qg_excluded_pending_2156": True,
        },
        "modules": [
            {
                "module_num": item.module_num,
                "slug": item.slug,
                "title": item.title,
                "built": item.built,
                "module_dir": display_path(item.module_dir),
            }
            for item in modules
        ],
        "findings": [item.to_json() for item in sorted(findings, key=finding_sort_key)],
        "skipped": [item.to_json() for item in skipped],
    }


def finding_sort_key(item: Finding) -> tuple[int, int, str, str]:
    module_num = item.module_num or 0
    return (-SEVERITY_ORDER[item.severity], module_num, item.category, item.file or "")


def result_has_failures(result: dict[str, Any], fail_on: str) -> bool:
    if fail_on == "never":
        return False
    threshold = SEVERITY_ORDER[fail_on]
    return any(SEVERITY_ORDER[item["severity"]] >= threshold for item in result["findings"])


def format_summary(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        f"Track deterministic audit: {result['track']}",
        f"Modules selected: {summary['modules_selected']} built: {summary['modules_built']} not_built: {summary['modules_not_built']}",
        f"Findings: {summary['findings_total']} "
        f"(blocker={summary['findings_by_severity']['blocker']}, "
        f"high={summary['findings_by_severity']['high']}, "
        f"medium={summary['findings_by_severity']['medium']}, "
        f"low={summary['findings_by_severity']['low']}, "
        f"info={summary['findings_by_severity']['info']})",
        f"Deterministic failures: {summary['deterministic_failures']}",
        f"Judgement-required content work: {summary['judgement_required_content_work']}",
        f"Auto-fixable findings: {summary['auto_fixable_findings']}",
        f"Remediation-only findings: {summary['remediation_only_findings']}",
        f"Skipped checks: {summary['skipped_checks']}",
        "LLM-QG: excluded pending #2156",
    ]
    if result["findings"]:
        lines.append("")
        lines.append("Top findings:")
        for item in result["findings"][:20]:
            location = item["file"] or "<repo>"
            if item["line"]:
                location = f"{location}:{item['line']}"
            module = f"M{item['module_num']:02d} {item['slug']}" if item["module_num"] else "track"
            lines.append(f"- [{item['severity']}] {module} {item['category']} {location}: {item['message']}")
        if len(result["findings"]) > 20:
            lines.append(f"- ... {len(result['findings']) - 20} more finding(s)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a reusable deterministic audit over one curriculum track.")
    parser.add_argument("--track", required=True, help="Track or level id from curriculum.yaml, e.g. b2")
    parser.add_argument("--range", dest="module_range", type=parse_range, help="Module range N-M")
    parser.add_argument("--slugs", nargs="*", help="Comma-separated or repeated slug filters")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument(
        "--run-mdx-generation-validate",
        action="store_true",
        help="Opt in to generate_mdx.py --validate. The runner restores the target MDX if drift is produced.",
    )
    parser.add_argument("--fail-on", choices=FAIL_ON_CHOICES, default="high")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = read_yaml(args.config)
    result = audit_track(
        track=args.track.lower(),
        config=config,
        range_filter=args.module_range,
        slugs=parse_slug_filter(args.slugs),
        run_mdx_generation_validate=args.run_mdx_generation_validate,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_summary(result))

    return 1 if result_has_failures(result, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
