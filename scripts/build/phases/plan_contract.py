"""Module contract generation for contract-first write/review flows."""

from __future__ import annotations

import re

import yaml
from build.phases.wiki_compressor import compress_wiki_packet


class ContractBuildError(ValueError):
    """Raised when a plan cannot produce a usable module contract."""


_TERM_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ'][А-Яа-яІіЇїЄєҐґ'’-]{2,}")
_TERM_STOPWORDS = {
    "або",
    "але",
    "вони",
    "вона",
    "його",
    "також",
    "which",
    "their",
    "this",
    "that",
    "from",
    "then",
    "with",
    "when",
    "where",
}


def _require_non_empty(plan: dict, key: str) -> list | dict | str:
    value = plan.get(key)
    if not value:
        raise ContractBuildError(f"Plan missing required field for contract stage: {key}")
    return value


def _extract_terms(text: str, *, limit: int = 8) -> list[str]:
    seen: list[str] = []
    for match in _TERM_RE.findall(text or ""):
        lowered = match.lower()
        if lowered in _TERM_STOPWORDS or match in seen:
            continue
        seen.append(match)
        if len(seen) >= limit:
            break
    return seen


def _word_budget_entry(words: int) -> dict[str, int]:
    lower = max(1, round(words * 0.9))
    upper = max(lower, round(words * 1.1))
    return {
        "target": words,
        "min": lower,
        "max": upper,
    }


def build_contract(
    plan: dict,
    wiki_packet: str,
    *,
    level: str,
    slug: str,
    module_num: int,
) -> tuple[dict, dict]:
    """Build `contract.yaml` plus section-mapped wiki excerpts."""
    outline = _require_non_empty(plan, "content_outline")
    dialogue_situations = _require_non_empty(plan, "dialogue_situations")
    activity_hints = _require_non_empty(plan, "activity_hints")
    word_target = plan.get("word_target")
    if isinstance(word_target, bool) or not isinstance(word_target, (int, float)) or word_target <= 0:
        raise ContractBuildError("Plan missing numeric word_target for contract stage")

    compression = compress_wiki_packet(plan, wiki_packet)
    sections: list[dict] = []
    section_word_budgets: dict[str, dict[str, int]] = {}
    for index, section in enumerate(outline, start=1):
        name = str(section.get("section", "")).strip()
        if not name:
            raise ContractBuildError("content_outline entry missing section title")
        words = int(section.get("words") or 0)
        if words <= 0:
            raise ContractBuildError(f"content_outline section '{name}' missing positive words budget")
        section_word_budgets[name] = _word_budget_entry(words)
        section_anchors = compression["anchors_by_section"].get(name, [])
        sections.append({
            "order": index,
            "name": name,
            "word_budget": section_word_budgets[name],
            "teaching_beats": [str(point) for point in (section.get("points") or [])],
            "required_terms": _extract_terms(" ".join(str(point) for point in (section.get("points") or []))),
            "factual_anchors": section_anchors,
            "activity_types_after_section": [
                hint.get("type", "")
                for hint in activity_hints
                if hint.get("type")
            ],
        })

    vocab = plan.get("vocabulary_hints") or plan.get("vocabulary") or {}
    must_introduce: list[str] = []
    if isinstance(vocab, list):
        for item in vocab:
            if isinstance(item, dict):
                word = item.get("word")
                if word:
                    must_introduce.append(str(word))
            elif item:
                must_introduce.append(str(item))
    elif isinstance(vocab, dict):
        must_introduce = [str(item) for item in (vocab.get("required") or [])]

    contract = {
        "module": {
            "slug": slug,
            "level": level,
            "module_num": module_num,
            "title": plan.get("title", slug),
            "phase": plan.get("phase", ""),
            "word_target": int(word_target),
        },
        "teaching_beats": {
            "section_order": [section["name"] for section in sections],
            "sections": sections,
        },
        "dialogue_acts": [
            {
                "setting": str(item.get("setting", "")).strip(),
                "speakers": [str(s) for s in (item.get("speakers") or [])],
                "function": str(item.get("motivation", "")).strip(),
            }
            for item in dialogue_situations
        ],
        "vocab_grammar_targets": {
            "must_introduce": must_introduce,
            "scope_lock": [str(item) for item in (plan.get("grammar") or [])],
        },
        "factual_anchors": compression["factual_anchors"],
        "banned_error_patterns": [
            "Russianisms",
            "Surzhyk",
            "Calques",
            "Invented grammar",
            "Meta-narration",
            "Formulaic section openers",
        ],
        "activity_obligations": [
            {
                "order": index,
                "id": str(hint.get("id") or ""),
                "type": str(hint.get("type") or ""),
                "focus": str(hint.get("focus") or ""),
            }
            for index, hint in enumerate(activity_hints, start=1)
        ],
        "section_word_budgets": section_word_budgets,
        "artifacts": {
            "wiki_excerpt_file": "wiki-excerpts.yaml",
        },
    }
    return contract, {
        "sections": compression["section_excerpts"],
        "factual_anchors": compression["factual_anchors"],
    }


def dump_yaml(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
