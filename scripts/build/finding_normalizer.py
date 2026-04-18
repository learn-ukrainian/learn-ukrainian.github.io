"""Deterministic normalization for structured reviewer findings."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

ERROR_CLASS_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("plan_contradiction", ("contradiction", "conflicts with the contract", "opposite in the same section")),
    ("scenario_grammar_misalignment", ("scenario", "grammar alignment", "grammar misalignment")),
    ("activity_order", ("activity order", "marker order", "activity_obligations")),
    ("pedagogical_sequence", ("order of sections", "teaching beat", "undercovered", "pedagogical sequence")),
    ("vocab_density", ("vocabulary density", "mandatory list scope", "too much vocabulary", "too dense")),
    ("dialogue_arc_fail", ("dialogue arc", "turn-taking", "named-speaker", "reciprocal", "register rule and models the opposite")),
    ("register_drift", ("register", "formal vs informal", "ви", "ти", "teacher-student exchange formal")),
    ("calque", ("calque", "russicism", "style guide", "приймати участь", "приймати рішення")),
    ("surzhyk", ("surzhyk", "russianism", "banned russian characters")),
    ("missing_vocab", ("missing vocabulary", "required vocabulary", "contract vocabulary", "must introduce")),
    ("stress_error", ("stress", "accent", "наголос")),
    ("notation_error", ("notation", "equals sign", "sound model", "[=]", "[•]", "[–]")),
    ("paronym_mismatch", ("paronym", "aspect pair", "wrong partner", "false friend")),
    ("word_budget", ("word count", "word minimum", "budget", "below the 1200-word floor")),
    ("factual_error", ("factual error", "factually wrong", "overstates the linguistics", "mislabels")),
    ("exercise_logic", ("exercise logic", "distractor", "answer logic", "answer key")),
    ("structural_gap", ("missing section", "structural integrity", "section order", "h2 heading")),
    ("cultural_register", ("cultural accuracy", "culturally appropriate", "teacherly voice")),
    ("meta_narration", ("formulaic", "meta narration", "template narration", "formulaic section openers")),
)

PLAN_LEVEL_ERROR_CLASSES = {
    "vocab_density",
    "pedagogical_sequence",
    "scenario_grammar_misalignment",
    "plan_contradiction",
}

SPEAKER_RE = re.compile(r"(?:\*\*|`)?([А-ЯІЇЄҐA-Z][\w'’-]{1,})(?::|\*\*:)")
SECTION_RE = re.compile(r"##\s+([^(/`\n]+)")
LEXEME_RE = re.compile(r"[«\"`']([^»\"`']{2,40})[»\"`']")


def _snake_case(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower())
    return text.strip("_") or "unknown_dimension"


def _detect_error_class(text: str) -> str:
    lowered = text.lower()
    for error_class, patterns in ERROR_CLASS_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            return error_class
    return "unclassified"


def _extract_section_title(location: str, issue: str) -> str | None:
    for text in (location, issue):
        match = SECTION_RE.search(text)
        if match:
            return match.group(1).strip()
    head = location.split("/", 1)[0].strip("` ")
    if head.startswith("## "):
        return head[3:].strip()
    return None


def _extract_speaker(location: str, issue: str, fix: str) -> str | None:
    for text in (location, issue, fix):
        match = SPEAKER_RE.search(text)
        if match:
            return match.group(1)
    return None


def _extract_target_lexeme(location: str, issue: str, fix: str) -> str | None:
    for text in (location, issue, fix):
        match = LEXEME_RE.search(text)
        if match:
            return match.group(1).strip()
    quoted = re.findall(r"\b[А-Яа-яІіЇїЄєҐґ][А-Яа-яІіЇїЄєҐґ'’-]{1,}\b", fix)
    return quoted[0] if quoted else None


def _normalized_id(dimension: str, error_class: str, scope: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "dimension": dimension,
            "error_class": error_class,
            "scope": scope,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "nf_" + hashlib.sha256(payload).hexdigest()[:16]


def _append_growth_log(path: Path, finding: dict[str, Any]) -> None:
    existing = []
    if path.exists():
        loaded = yaml.safe_load(path.read_text("utf-8"))
        if isinstance(loaded, list):
            existing = loaded
    existing.append(finding)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(existing, sort_keys=False, allow_unicode=True),
        "utf-8",
    )


def normalize_finding(
    finding: dict[str, Any],
    *,
    growth_log_path: Path | None = None,
) -> dict[str, Any]:
    dimension = _snake_case(finding.get("dimension"))
    location = str(finding.get("location") or "")
    issue = str(finding.get("issue") or "")
    fix = str(finding.get("fix") or "")
    severity = _snake_case(finding.get("severity") or "major")
    combined = "\n".join(part for part in (location, issue, fix) if part)
    error_class = _detect_error_class(combined)

    scope = {
        "section_title": _extract_section_title(location, issue),
        "speaker": _extract_speaker(location, issue, fix),
        "target_lexeme": _extract_target_lexeme(location, issue, fix),
    }
    normalized = {
        "dimension": dimension,
        "severity": severity,
        "error_class": error_class,
        "scope": scope,
        "location": location,
        "issue": issue,
        "fix": fix,
        "normalized_id": _normalized_id(dimension, error_class, scope),
        "plan_level": error_class in PLAN_LEVEL_ERROR_CLASSES,
    }
    if error_class == "unclassified":
        normalized["original_prose"] = {
            "location": location,
            "issue": issue,
            "fix": fix,
        }
        if growth_log_path is not None:
            _append_growth_log(
                growth_log_path,
                {
                    "dimension": dimension,
                    "location": location,
                    "issue": issue,
                    "fix": fix,
                },
            )
    return normalized


def normalize_findings(
    findings: list[dict[str, Any]],
    *,
    growth_log_path: Path | None = None,
) -> list[dict[str, Any]]:
    return [
        normalize_finding(finding, growth_log_path=growth_log_path)
        for finding in findings
    ]
