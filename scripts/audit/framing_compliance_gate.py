"""Deterministic FOLK framing-compliance gate.

The gate enforces the FOLK framing standard's NEVER-list against teacher prose
and plan ``content_outline`` text. It deliberately strips primary-reading
quotes, Markdown blockquotes, and fenced code before scanning so quoted folk
texts cannot trip prose framing rules.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CURRICULUM = ROOT / "curriculum" / "l2-uk-en"

DEBUNKING_WINDOW_CHARS = 160

HARD_RULES: dict[str, dict[str, str]] = {
    "C1": {
        "severity": "violation",
        "title": "pagan-core-Christian-veneer structure",
        "message": "pre-Christian core token co-occurs with Christian shell token in the same section",
    },
    "C2": {
        "severity": "violation",
        "title": "producing magic applied to carols",
        "message": "продукувальна магія co-occurs with колядки/щедрівки/щедрування in the same section",
    },
}

WARN_RULES: dict[str, dict[str, str]] = {
    "W1": {
        "severity": "warning",
        "title": "applied magic framing",
        "message": "прикладна магія appears in FOLK teacher prose",
    },
    "W2": {
        "severity": "warning",
        "title": "pagan cosmogony as carol frame",
        "message": "cosmogony/creation frame is used in a section title or thesis line that names carols",
    },
    "W3": {
        "severity": "warning",
        "title": "demonology as section subject",
        "message": "demonology/unclean forces/witchcraft appears as a section title subject",
    },
}

_CORE_RE = re.compile(
    r"(?:дохристиянськ\w*\s+(?:ядро|основа|корінь|субстрат)|язичницьк\w*\s+(?:ядро|основа))",
    re.IGNORECASE,
)
_SHELL_RE = re.compile(
    r"християнськ\w*\s+(?:оболонк\w*|нашаруванн\w*|шар|вернісаж|маск\w*)",
    re.IGNORECASE,
)
_PRODUCING_MAGIC_RE = re.compile(r"продукувальн\w*\s+магі\w*", re.IGNORECASE)
_APPLIED_MAGIC_RE = re.compile(r"прикладн\w*\s+магі\w*", re.IGNORECASE)
_CAROL_RE = re.compile(r"колядк\w*|щедрівк\w*|щедрування", re.IGNORECASE)
_COSMOGONY_RE = re.compile(r"міф\s+про\s+створення\s+світу|космогон\w*", re.IGNORECASE)
_DEMONOLOGY_RE = re.compile(r"демонолог\w*|нечист\w*\s+сил\w*|відьм\w*", re.IGNORECASE)
_DEBUNKING_RE = re.compile(
    r"контест|радянськ|атеїстичн|спотворен|хибн|не\s+варто|заперечу[йj]|критик|imperial|імперськ",
    re.IGNORECASE,
)
_MYTH_DEBUNKING_RE = re.compile(
    r"міф\s+про\s+(?:магі\w*|язич\w*|дохристиян\w*|поган\w*|окульт\w*|відьм\w*|демонолог\w*)",
    re.IGNORECASE,
)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


@dataclass(frozen=True)
class ScanSection:
    source: str
    source_path: str
    heading: str
    text: str
    line_numbers: tuple[int, ...]


def _level_key(level: str | None) -> str:
    return str(level or "").strip().casefold()


def _default_module_path(level: str, slug: str, repo_root: Path) -> Path:
    return repo_root / "curriculum" / "l2-uk-en" / _level_key(level) / slug / "module.md"


def _default_plan_path(level: str, slug: str, repo_root: Path) -> Path:
    return repo_root / "curriculum" / "l2-uk-en" / "plans" / _level_key(level) / f"{slug}.yaml"


def _repo_rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _mask_line(line: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in line)


def strip_teacher_prose_exclusions(text: str) -> str:
    """Mask quoted/non-prose regions while preserving line numbers."""
    lines = text.splitlines(keepends=True)
    cleaned: list[str] = []
    in_primary_reading = False
    in_fence = False

    for line in lines:
        stripped = line.strip()
        starts_fence = bool(_FENCE_RE.match(line))

        if in_primary_reading:
            cleaned.append(_mask_line(line))
            if stripped == ":::":
                in_primary_reading = False
            continue

        if in_fence:
            cleaned.append(_mask_line(line))
            if starts_fence:
                in_fence = False
            continue

        if stripped.startswith(":::primary-reading"):
            cleaned.append(_mask_line(line))
            if stripped != ":::":
                in_primary_reading = True
            continue

        if starts_fence:
            cleaned.append(_mask_line(line))
            in_fence = True
            continue

        if line.lstrip().startswith(">"):
            cleaned.append(_mask_line(line))
            continue

        cleaned.append(line)

    return "".join(cleaned)


def _split_module_sections(module_text: str, *, source_path: str) -> list[ScanSection]:
    cleaned = strip_teacher_prose_exclusions(module_text)
    sections: list[ScanSection] = []
    current_lines: list[str] = []
    current_numbers: list[int] = []
    current_heading = "<preamble>"

    def flush() -> None:
        nonlocal current_lines, current_numbers, current_heading
        if not current_lines:
            return
        text = "\n".join(current_lines)
        if text.strip():
            sections.append(
                ScanSection(
                    source="module.md",
                    source_path=source_path,
                    heading=current_heading,
                    text=text,
                    line_numbers=tuple(current_numbers),
                )
            )
        current_lines = []
        current_numbers = []

    for line_number, line in enumerate(cleaned.splitlines(), start=1):
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush()
            current_heading = heading_match.group(2).strip()
        current_lines.append(line)
        current_numbers.append(line_number)

    flush()
    return sections


def _mapping_value(node: yaml.nodes.MappingNode, key: str) -> yaml.nodes.Node | None:
    for key_node, value_node in node.value:
        if isinstance(key_node, yaml.nodes.ScalarNode) and key_node.value == key:
            return value_node
    return None


def _scalar_node_text(node: yaml.nodes.Node | None) -> tuple[str, int] | None:
    if isinstance(node, yaml.nodes.ScalarNode) and isinstance(node.value, str):
        return node.value, node.start_mark.line + 1
    return None


def _plan_outline_sections(plan_text: str, *, source_path: str) -> list[ScanSection]:
    if not plan_text.strip():
        return []
    try:
        root = yaml.compose(plan_text)
    except yaml.YAMLError:
        return []
    if not isinstance(root, yaml.nodes.MappingNode):
        return []
    outline = _mapping_value(root, "content_outline")
    if not isinstance(outline, yaml.nodes.SequenceNode):
        return []

    sections: list[ScanSection] = []
    for index, entry in enumerate(outline.value, start=1):
        if not isinstance(entry, yaml.nodes.MappingNode):
            continue
        heading = f"content_outline[{index}]"

        section_value = _scalar_node_text(_mapping_value(entry, "section"))
        if section_value is not None:
            heading, line_number = section_value
            sections.append(
                ScanSection(
                    source="plan content_outline",
                    source_path=source_path,
                    heading=heading,
                    text=heading,
                    line_numbers=(line_number,),
                )
            )

        points = _mapping_value(entry, "points")
        if isinstance(points, yaml.nodes.SequenceNode):
            for point in points.value:
                point_value = _scalar_node_text(point)
                if point_value is None:
                    continue
                text, line_number = point_value
                sections.append(
                    ScanSection(
                        source="plan content_outline",
                        source_path=source_path,
                        heading=heading,
                        text=text,
                        line_numbers=(line_number,),
                    )
                )

    return sections


def _line_for_offset(section: ScanSection, offset: int) -> int:
    line_index = section.text[:offset].count("\n")
    if line_index >= len(section.line_numbers):
        return section.line_numbers[-1] if section.line_numbers else 1
    return section.line_numbers[line_index]


def _snippet(text: str, start: int, end: int, *, limit: int = 220) -> str:
    padded_start = max(0, start - 70)
    padded_end = min(len(text), end + 70)
    snippet = re.sub(r"\s+", " ", text[padded_start:padded_end]).strip()
    if len(snippet) <= limit:
        return snippet
    return f"{snippet[: limit - 1].rstrip()}..."


def _combined_snippet(text: str, matches: list[re.Match[str]]) -> str:
    if not matches:
        return ""
    start = min(match.start() for match in matches)
    end = max(match.end() for match in matches)
    if end - start <= 220:
        return _snippet(text, start, end)
    return " ... ".join(match.group(0) for match in matches)


def _has_debunking_context(section: ScanSection, start: int, end: int) -> bool:
    context_start = max(0, start - DEBUNKING_WINDOW_CHARS)
    context_end = min(len(section.text), end + DEBUNKING_WINDOW_CHARS)
    context = section.text[context_start:context_end]
    return bool(_DEBUNKING_RE.search(context) or _MYTH_DEBUNKING_RE.search(context))


def _item(
    *,
    rule_id: str,
    severity: str,
    section: ScanSection,
    start: int,
    end: int,
    snippet: str,
) -> dict[str, Any]:
    rule = HARD_RULES.get(rule_id) or WARN_RULES[rule_id]
    return {
        "rule_id": rule_id,
        "severity": severity,
        "source": section.source,
        "source_path": section.source_path,
        "line": _line_for_offset(section, start),
        "section": section.heading,
        "title": rule["title"],
        "message": rule["message"],
        "snippet": snippet,
    }


def _append_or_exempt(
    *,
    rule_id: str,
    severity: str,
    section: ScanSection,
    start: int,
    end: int,
    snippet: str,
    violations: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    infos: list[dict[str, Any]],
) -> None:
    if _has_debunking_context(section, start, end):
        infos.append(
            _item(
                rule_id=rule_id,
                severity="info",
                section=section,
                start=start,
                end=end,
                snippet=snippet,
            )
        )
        return
    target = violations if severity == "violation" else warnings
    target.append(
        _item(
            rule_id=rule_id,
            severity=severity,
            section=section,
            start=start,
            end=end,
            snippet=snippet,
        )
    )


def _check_section(
    section: ScanSection,
    *,
    violations: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    infos: list[dict[str, Any]],
) -> None:
    core_matches = list(_CORE_RE.finditer(section.text))
    shell_matches = list(_SHELL_RE.finditer(section.text))
    if core_matches and shell_matches:
        core = core_matches[0]
        shell = shell_matches[0]
        start = min(core.start(), shell.start())
        end = max(core.end(), shell.end())
        _append_or_exempt(
            rule_id="C1",
            severity="violation",
            section=section,
            start=start,
            end=end,
            snippet=_combined_snippet(section.text, [core, shell]),
            violations=violations,
            warnings=warnings,
            infos=infos,
        )

    producing_magic_matches = list(_PRODUCING_MAGIC_RE.finditer(section.text))
    carol_matches = list(_CAROL_RE.finditer(section.text))
    if producing_magic_matches and carol_matches:
        magic = producing_magic_matches[0]
        carol = carol_matches[0]
        _append_or_exempt(
            rule_id="C2",
            severity="violation",
            section=section,
            start=magic.start(),
            end=magic.end(),
            snippet=_combined_snippet(section.text, [magic, carol]),
            violations=violations,
            warnings=warnings,
            infos=infos,
        )

    for match in _APPLIED_MAGIC_RE.finditer(section.text):
        _append_or_exempt(
            rule_id="W1",
            severity="warning",
            section=section,
            start=match.start(),
            end=match.end(),
            snippet=_snippet(section.text, match.start(), match.end()),
            violations=violations,
            warnings=warnings,
            infos=infos,
        )

    _check_cosmogony_frame(section, violations=violations, warnings=warnings, infos=infos)
    _check_demonology_title(section, violations=violations, warnings=warnings, infos=infos)


def _check_cosmogony_frame(
    section: ScanSection,
    *,
    violations: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    infos: list[dict[str, Any]],
) -> None:
    lines = section.text.splitlines()
    for index, line in enumerate(lines):
        heading_match = _HEADING_RE.match(line)
        is_heading = bool(heading_match)
        thesis_line = len(line.strip()) <= 180 or line.strip().casefold().startswith("ключова теза")
        if not (is_heading or thesis_line):
            continue
        cosmogony = _COSMOGONY_RE.search(line)
        carol = _CAROL_RE.search(line)
        if not cosmogony or not carol:
            continue
        line_start = sum(len(previous) + 1 for previous in lines[:index])
        start = line_start + min(cosmogony.start(), carol.start())
        end = line_start + max(cosmogony.end(), carol.end())
        _append_or_exempt(
            rule_id="W2",
            severity="warning",
            section=section,
            start=start,
            end=end,
            snippet=line.strip(),
            violations=violations,
            warnings=warnings,
            infos=infos,
        )


def _check_demonology_title(
    section: ScanSection,
    *,
    violations: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    infos: list[dict[str, Any]],
) -> None:
    first_line = section.text.splitlines()[0] if section.text.splitlines() else section.heading
    title = section.heading if section.source == "plan content_outline" else first_line
    match = _DEMONOLOGY_RE.search(title)
    if not match:
        return
    start = section.text.find(title)
    if start < 0:
        start = 0
    start += match.start()
    end = start + len(match.group(0))
    _append_or_exempt(
        rule_id="W3",
        severity="warning",
        section=section,
        start=start,
        end=end,
        snippet=title.strip(),
        violations=violations,
        warnings=warnings,
        infos=infos,
    )


def check_framing_compliance(
    module_text: str,
    *,
    plan_text: str = "",
    module_source_path: str = "module.md",
    plan_source_path: str = "plan.yaml",
) -> dict[str, Any]:
    """Run deterministic FOLK framing checks on module prose plus plan outline."""
    sections = _split_module_sections(module_text, source_path=module_source_path)
    sections.extend(_plan_outline_sections(plan_text, source_path=plan_source_path))

    violations: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []

    for section in sections:
        _check_section(section, violations=violations, warnings=warnings, infos=infos)

    return {
        "passed": not violations,
        "violations": violations,
        "warnings": warnings,
        "infos": infos,
    }


def verify(
    level: str,
    slug: str,
    *,
    module_path: Path | None = None,
    plan_path: Path | None = None,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    """Verify one FOLK module's teacher-prose framing."""
    repo_root = repo_root.resolve()
    if _level_key(level) != "folk":
        return {
            "applicable": False,
            "level": level,
            "slug": slug,
            "passed": True,
            "reason": "level is not folk",
            "violations": [],
            "warnings": [],
            "infos": [],
        }

    resolved_module_path = module_path or _default_module_path(level, slug, repo_root)
    resolved_plan_path = plan_path or _default_plan_path(level, slug, repo_root)

    missing: list[str] = []
    if not resolved_module_path.exists():
        missing.append(_repo_rel(resolved_module_path, repo_root))
    if not resolved_plan_path.exists():
        missing.append(_repo_rel(resolved_plan_path, repo_root))
    if missing:
        return {
            "applicable": False,
            "level": level,
            "slug": slug,
            "passed": True,
            "reason": "missing source file(s): " + ", ".join(missing),
            "violations": [],
            "warnings": [],
            "infos": [],
        }

    module_text = resolved_module_path.read_text(encoding="utf-8")
    plan_text = resolved_plan_path.read_text(encoding="utf-8")
    report = check_framing_compliance(
        module_text,
        plan_text=plan_text,
        module_source_path=_repo_rel(resolved_module_path, repo_root),
        plan_source_path=_repo_rel(resolved_plan_path, repo_root),
    )
    return {
        "applicable": True,
        "level": level,
        "slug": slug,
        "reason": "passed" if report["passed"] else "hard framing violation(s)",
        **report,
    }


def _format_item(item: dict[str, Any]) -> str:
    label = item["severity"].upper()
    return (
        f"{label} {item['rule_id']} {item['source_path']}:{item['line']} "
        f"section={item['section']!r}: {item['title']}\n"
        f"  snippet: {item['snippet']}"
    )


def print_report(report: dict[str, Any]) -> None:
    status = "PASS" if report["passed"] else "FAIL"
    level = report.get("level", "<unknown>")
    slug = report.get("slug", "<unknown>")
    print(f"{status}: {level}/{slug} framing compliance: {report.get('reason', 'checked')}")
    print(
        "counts: "
        f"violations={len(report.get('violations', []))} "
        f"warnings={len(report.get('warnings', []))} "
        f"infos={len(report.get('infos', []))}"
    )
    for key in ("violations", "warnings", "infos"):
        for item in report.get(key, []):
            print(_format_item(item))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("level", help="Curriculum level, e.g. folk")
    parser.add_argument("slug", help="Module slug")
    parser.add_argument("--repo-root", type=Path, default=ROOT, help="Repository root")
    parser.add_argument("--module-path", type=Path, help="Override module.md path")
    parser.add_argument("--plan-path", type=Path, help="Override plan YAML path")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = verify(
        args.level,
        args.slug,
        module_path=args.module_path,
        plan_path=args.plan_path,
        repo_root=args.repo_root,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_report(report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
