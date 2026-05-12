"""Learner-state audit checks for V7 modules."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

try:
    from scripts.config import get_immersion_structural
    from scripts.pipeline.learner_state import build_learner_state
except ModuleNotFoundError:  # pragma: no cover - CLI path compatibility
    from config import get_immersion_structural
    from pipeline.learner_state import build_learner_state


def _vesum_helpers():
    """Lazy import of linear_pipeline VESUM helpers.

    Deferred to call time because importing scripts.build.linear_pipeline at
    module-load time pulls in scripts.build.citation_matcher and other deeply
    qualified imports that fail under bare-cwd script invocation (see
    test_vocab_progression.py::test_cli_smoke). Lazy import lets the audit
    package load cleanly in CLI contexts; the import only fires when the
    audit check actually runs (always under fully-qualified entry points).
    """
    try:
        from scripts.build.linear_pipeline import (
            _iter_vesum_word_surfaces,
            _normalize_for_vesum,
        )
    except ModuleNotFoundError:  # pragma: no cover
        from build.linear_pipeline import (
            _iter_vesum_word_surfaces,
            _normalize_for_vesum,
        )
    return _iter_vesum_word_surfaces, _normalize_for_vesum


def _strip_non_body_prose(content: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"^\|.*\|$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"https?://\S+", " ", text)
    return text


def _extract_ukrainian_surfaces(content: str) -> list[str]:
    _iter_vesum_word_surfaces, _normalize_for_vesum = _vesum_helpers()
    words = _iter_vesum_word_surfaces(_normalize_for_vesum(_strip_non_body_prose(content)))
    seen: set[str] = set()
    ordered: list[str] = []
    for word in words:
        lower = word.lower()
        if lower not in seen:
            seen.add(lower)
            ordered.append(lower)
    return ordered


def _load_declared_vocab(module_dir: str | Path | None) -> set[str]:
    if module_dir is None:
        return set()
    path = Path(module_dir) / "vocabulary.yaml"
    if not path.exists():
        return set()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return set()
    return {
        str(item["lemma"]).lower()
        for item in items
        if isinstance(item, dict) and item.get("lemma")
    }


def _unknown_vocab_severity(module_num: int) -> str:
    return "WARN" if module_num <= 3 else "HARD"


def _known_grammar_severity(level: str) -> str:
    return "WARN" if level.lower() in {"a1", "a2"} else "HARD"


def _unsupported_tolerance(level: str, module_num: int) -> int:
    structural = get_immersion_structural(level.lower(), module_num)
    return int(structural["max_unsupported_uk_words"])


def check_unknown_vocabulary(
    content: str,
    level: str,
    module_num: int,
    module_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Flag Ukrainian prose words outside learner-state and module vocabulary."""
    learner_state = build_learner_state(level.lower(), module_num)
    allowed = {
        str(lemma).lower()
        for lemma in learner_state.get("cumulative_vocabulary", [])
        if lemma
    }
    allowed.update(_load_declared_vocab(module_dir))

    unknown = [word for word in _extract_ukrainian_surfaces(content) if word not in allowed]
    tolerance = _unsupported_tolerance(level, module_num)
    if len(unknown) <= tolerance:
        return []

    severity = _unknown_vocab_severity(module_num)
    return [
        {
            "type": "unknown_vocabulary",
            "severity": severity,
            "lemma": word,
            "issue": (
                f"Ukrainian lemma '{word}' is not in cumulative learner state "
                "or this module's vocabulary.yaml."
            ),
            "fix": "Add the lemma to vocabulary.yaml or rewrite the prose with taught vocabulary.",
        }
        for word in unknown
    ]


def check_known_grammar_re_explanation(
    content: str,
    level: str,
    module_num: int,
) -> list[dict[str, Any]]:
    """Flag section headers that appear to re-explain already-taught grammar."""
    learner_state = build_learner_state(level.lower(), module_num)
    known_topics = [
        str(topic).strip().lower()
        for topic in learner_state.get("known_grammar", [])
        if str(topic).strip()
    ]
    if not known_topics:
        return []

    severity = _known_grammar_severity(level)
    violations: list[dict[str, Any]] = []
    for match in re.finditer(r"^(#{2,3})\s+(.+?)\s*$", content, re.MULTILINE):
        header = match.group(2).strip()
        header_lower = header.lower()
        for topic in known_topics:
            if topic in header_lower:
                violations.append(
                    {
                        "type": "known_grammar_re_explanation",
                        "severity": severity,
                        "topic": topic,
                        "header": header,
                        "line": content.count("\n", 0, match.start()) + 1,
                        "issue": (
                            f"Section header '{header}' appears to re-explain "
                            f"already-taught grammar topic '{topic}'."
                        ),
                        "fix": "Assume the grammar as known and use the section for new content.",
                    }
                )
                break
    return violations


def check_learner_state(
    content: str,
    level: str,
    module_num: int,
    module_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Run all learner-state checks for a module."""
    return [
        *check_unknown_vocabulary(content, level, module_num, module_dir),
        *check_known_grammar_re_explanation(content, level, module_num),
    ]
