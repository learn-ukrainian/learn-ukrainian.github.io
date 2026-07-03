"""Level-aware deterministic surface checks for learner-facing module text.

This module catches cheap, high-precision failures before an LLM reviewer is
asked to make judgment calls. It deliberately does not try to prove native
Ukrainian style; collocation, idiom, register, and grammar-naturalness remain
LLM/native-review dimensions.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SEMINAR_LEVELS = {
    "bio",
    "folk",
    "hist",
    "istorio",
    "lit",
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


@dataclass(frozen=True, slots=True)
class SurfacePolicy:
    """Deterministic surface policy for one level family."""

    family: str
    english_policy: str
    english_led_severity: str
    english_led_min_latin_words: int
    english_ratio_warn: float | None
    english_ratio_fail: float | None
    ai_leak_severity: str = "critical"
    path_leak_severity: str = "critical"
    pathos_severity: str = "warning"


_A1_POLICY = SurfacePolicy(
    family="a1",
    english_policy="English scaffolding is expected; only internal/AI/path leaks are blocking.",
    english_led_severity="info",
    english_led_min_latin_words=9999,
    english_ratio_warn=None,
    english_ratio_fail=None,
)
_A2_POLICY = SurfacePolicy(
    family="a2",
    english_policy="English support is receding; English-led prose is a warning, not an automatic failure.",
    english_led_severity="warning",
    english_led_min_latin_words=12,
    english_ratio_warn=0.45,
    english_ratio_fail=None,
)
_B1_PLUS_POLICY = SurfacePolicy(
    family="b1_plus",
    english_policy="B1+ learner-facing lesson prose should be Ukrainian-led.",
    english_led_severity="critical",
    english_led_min_latin_words=8,
    english_ratio_warn=0.08,
    english_ratio_fail=0.18,
)
_SEMINAR_POLICY = SurfacePolicy(
    family="seminar",
    english_policy="Seminar learner-facing prose should be Ukrainian-led; English is only incidental metadata.",
    english_led_severity="critical",
    english_led_min_latin_words=8,
    english_ratio_warn=0.05,
    english_ratio_fail=0.12,
)

_LATIN_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z'-]*\b")
_CYRILLIC_WORD_RE = re.compile(r"[\u0400-\u04ff][\u0400-\u04ff'ʼ-]*")
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_TAG_RE = re.compile(r"<[^>\n]{2,160}>")
_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_YAML_KEY_RE = re.compile(r"(?m)^(\s*(?:-\s*)?)[A-Za-z_][A-Za-z0-9_-]*:(?=\s|$)")

AI_LEAK_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern, re.IGNORECASE), label)
    for pattern, label in (
        (r"\bAs an AI\b", "AI persona disclaimer"),
        (r"\bI (?:cannot|can't) (?:assist|help|comply)\b", "AI refusal text"),
        (r"\b(?:apologies|sorry),?\s+(?:but\s+)?I\b", "AI apology text"),
        (r"\bNote to self\b", "model scratchpad text"),
        (r"\bWait,\s+(?:actually|no)\b", "model self-correction text"),
        (r"\bCorrection:\s+", "model correction label"),
        (r"\bDraft:\s+", "model draft label"),
        (r"\bRewrite this\b", "model editing instruction"),
        (r"<(?:implementation_map|activity_split|plan_reasoning)_audit\b", "writer audit line"),
        (r"\b(?:Generated Content|artifact fence|reviewer-fix anchor)\b", "build/reviewer scaffolding"),
    )
)

PATH_LEAK_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern), label)
    for pattern, label in (
        (r"/Users/[^\s)]+", "local user path"),
        (r"/tmp/[^\s)]+", "temporary filesystem path"),
        (r"\bcurriculum/l2-uk-en/[^\s)]+", "curriculum source path"),
        (r"\bscripts/(?:build|audit|api|sync)/[^\s)]+", "internal script path"),
        (r"\bstarlight/src/[^\s)]+", "site source path"),
        (r"\b(?:llm_qg|python_qg|wiki_coverage_gate)\.json\b", "internal QG artifact"),
    )
)

PATHOS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern, re.IGNORECASE), label)
    for pattern, label in (
        (r"\bGreat job!\b", "generic praise"),
        (r"\bYou have unlocked\b", "gamified progress language"),
        (r"\bLet's dive in\b", "LLM-style opener"),
        (r"\bWelcome to (?:A1|A2|B1|B2|C1|C2)\b", "course-level marketing opener"),
        (r"пориньмо\s+у\s+захоплив", "inflated journey metaphor"),
        (r"неймовірн[а-яіїєґ]*\s+подорож", "inflated journey metaphor"),
        (r"ти\s+справжн[ійяє]\s+геро", "overheated learner praise"),
    )
)


def policy_for_level(level: str | None) -> SurfacePolicy:
    """Return deterministic surface policy for a level/track code."""
    clean = str(level or "").strip().lower()
    if clean in SEMINAR_LEVELS:
        return _SEMINAR_POLICY
    if clean.startswith("a1"):
        return _A1_POLICY
    if clean.startswith("a2"):
        return _A2_POLICY
    return _B1_PLUS_POLICY


def _line_no(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _mask_match(match: re.Match[str]) -> str:
    return "".join("\n" if ch == "\n" else " " for ch in match.group(0))


def _mask_ignored_regions(text: str) -> str:
    """Mask comments/code/frontmatter while preserving line numbers."""
    masked = _FRONTMATTER_RE.sub(_mask_match, text)
    masked = _FENCE_RE.sub(_mask_match, masked)
    return _HTML_COMMENT_RE.sub(_mask_match, masked)


def _mask_tags(text: str) -> str:
    return _TAG_RE.sub(_mask_match, text)


def _mask_yaml_keys(text: str) -> str:
    """Mask YAML mapping keys while preserving line numbers and scalar values."""
    return _YAML_KEY_RE.sub(
        lambda match: match.group(1) + " " * (len(match.group(0)) - len(match.group(1))),
        text,
    )


def _is_yaml_source(source: str) -> bool:
    return source.endswith((".yaml", ".yml"))


def _is_ignored_line(line: str) -> bool:
    stripped = line.strip()
    return (
        not stripped
        or stripped.startswith("|")
        or stripped.startswith("#")
        or stripped.startswith(">")
        or stripped.startswith("---")
    )


def _finding(
    *,
    kind: str,
    severity: str,
    line: int,
    text: str,
    message: str,
    source: str,
) -> dict[str, Any]:
    return {
        "type": kind,
        "severity": severity,
        "line": line,
        "text": text[:160],
        "message": message,
        "source": source,
    }


def _english_led_findings(masked: str, *, policy: SurfacePolicy, source: str) -> list[dict[str, Any]]:
    if policy.english_led_severity == "info":
        return []
    findings: list[dict[str, Any]] = []
    for line_no, line in enumerate(masked.splitlines(), 1):
        if _is_ignored_line(line):
            continue
        latin_words = _LATIN_WORD_RE.findall(line)
        if len(latin_words) < policy.english_led_min_latin_words:
            continue
        if _CYRILLIC_WORD_RE.search(line):
            continue
        findings.append(
            _finding(
                kind="english_led_line",
                severity=policy.english_led_severity,
                line=line_no,
                text=line.strip(),
                message=policy.english_policy,
                source=source,
            )
        )
    return findings


def _english_ratio_finding(masked: str, *, policy: SurfacePolicy, source: str) -> dict[str, Any] | None:
    latin_count = 0
    cyrillic_count = 0
    for line in masked.splitlines():
        if _is_ignored_line(line):
            continue
        latin_count += len(_LATIN_WORD_RE.findall(line))
        cyrillic_count += len(_CYRILLIC_WORD_RE.findall(line))
    total = latin_count + cyrillic_count
    if total == 0:
        return None
    ratio = latin_count / total
    severity: str | None = None
    if policy.english_ratio_fail is not None and ratio > policy.english_ratio_fail:
        severity = "critical"
    elif policy.english_ratio_warn is not None and ratio > policy.english_ratio_warn:
        severity = "warning"
    if severity is None:
        return None
    return _finding(
        kind="english_ratio",
        severity=severity,
        line=0,
        text=f"latin_words={latin_count} cyrillic_words={cyrillic_count} ratio={ratio:.2f}",
        message=policy.english_policy,
        source=source,
    )


def _pattern_findings(
    text: str,
    *,
    patterns: tuple[tuple[re.Pattern[str], str], ...],
    kind: str,
    severity: str,
    source: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for pattern, label in patterns:
        for match in pattern.finditer(text):
            findings.append(
                _finding(
                    kind=kind,
                    severity=severity,
                    line=_line_no(text, match.start()),
                    text=match.group(0),
                    message=label,
                    source=source,
                )
            )
    return findings


def scan_surface_text(
    text: str,
    *,
    level: str | None,
    source: str = "module.md",
    include_language_policy: bool = True,
) -> dict[str, Any]:
    """Run level-aware deterministic checks over one learner-facing text blob."""
    policy = policy_for_level(level)
    masked = _mask_ignored_regions(text)
    prose_masked = _mask_yaml_keys(masked) if _is_yaml_source(source) else masked
    language_masked = _mask_tags(prose_masked)
    findings: list[dict[str, Any]] = []
    findings.extend(
        _pattern_findings(
            prose_masked,
            patterns=AI_LEAK_PATTERNS,
            kind="ai_leakage",
            severity=policy.ai_leak_severity,
            source=source,
        )
    )
    findings.extend(
        _pattern_findings(
            prose_masked,
            patterns=PATH_LEAK_PATTERNS,
            kind="path_leakage",
            severity=policy.path_leak_severity,
            source=source,
        )
    )
    if include_language_policy:
        findings.extend(_english_led_findings(language_masked, policy=policy, source=source))
        ratio_finding = _english_ratio_finding(language_masked, policy=policy, source=source)
        if ratio_finding is not None:
            findings.append(ratio_finding)
    findings.extend(
        _pattern_findings(
            prose_masked,
            patterns=PATHOS_PATTERNS,
            kind="pathos_or_register",
            severity=policy.pathos_severity,
            source=source,
        )
    )

    critical = [item for item in findings if item.get("severity") == "critical"]
    warnings = [item for item in findings if item.get("severity") == "warning"]
    verdict = "FAIL" if critical else "WARN" if warnings else "PASS"
    return {
        "passed": not critical,
        "verdict": verdict,
        "level_policy": asdict(policy),
        "findings": findings,
        "counts": {
            "critical": len(critical),
            "warning": len(warnings),
            "total": len(findings),
        },
    }


def scan_module_surface(module_dir: Path, *, level: str | None = None) -> dict[str, Any]:
    """Run deterministic surface checks for the learner-facing files in a module."""
    sources = [
        ("module.md", module_dir / "module.md"),
        ("activities.yaml", module_dir / "activities.yaml"),
        ("vocabulary.yaml", module_dir / "vocabulary.yaml"),
        ("resources.yaml", module_dir / "resources.yaml"),
    ]
    reports: dict[str, Any] = {}
    findings: list[dict[str, Any]] = []
    for source, path in sources:
        if not path.exists():
            continue
        report = scan_surface_text(
            path.read_text(encoding="utf-8"),
            level=level,
            source=source,
            include_language_policy=source == "module.md",
        )
        reports[source] = report
        findings.extend(report["findings"])
    critical = [item for item in findings if item.get("severity") == "critical"]
    warnings = [item for item in findings if item.get("severity") == "warning"]
    return {
        "passed": not critical,
        "verdict": "FAIL" if critical else "WARN" if warnings else "PASS",
        "level": level,
        "files": reports,
        "findings": findings,
        "counts": {
            "critical": len(critical),
            "warning": len(warnings),
            "total": len(findings),
        },
    }
