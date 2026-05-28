"""Guard writer prompts against cross-lesson literal leakage."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import seed_implementation_map
from scripts.build.phases.wiki_manifest import extract_manifest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNK_ID_RE = re.compile(r"chunk_id:\s*([A-Za-z0-9_-]+)")
CYRILLIC_WORD_RE = re.compile(r"[А-ЯІЇЄҐа-яіїєґ][А-ЯІЇЄҐа-яіїєґ'’ʼ-]{3,}")
QUOTED_TEXT_RE = re.compile(r"[«“]([^»”]+)[»”]")
BAD_MARKER_RE = re.compile(r"<!--\s*bad\s*-->(.*?)<!--\s*/bad\s*-->", re.DOTALL)
TEXTBOOK_HINT_RE = re.compile(r"\b(?:Grade|p\.|клас|стор)\b", re.IGNORECASE)
MIN_TOKEN_LENGTH = 4


@pytest.mark.parametrize(
    ("self_slug", "other_slug"),
    [
        ("sounds-letters-and-hello", "my-morning"),
    ],
)
def test_no_cross_lesson_token_leakage(self_slug: str, other_slug: str) -> None:
    self_prompt = _render_writer_prompt_for_module(level="a1", slug=self_slug)
    self_source_text = _lesson_source_text(level="a1", slug=self_slug)
    self_specific = _extract_lesson_specific_tokens(level="a1", slug=self_slug)
    other_specific = _extract_lesson_specific_tokens(level="a1", slug=other_slug)

    leaked_tokens = sorted(
        tok
        for tok in other_specific - self_specific
        if _contains_token(self_prompt, tok) and not _contains_token(self_source_text, tok)
    )

    assert not leaked_tokens, (
        f"Lesson '{other_slug}' specific tokens leaked into '{self_slug}' "
        f"rendered writer prompt: {leaked_tokens}"
    )


def _render_writer_prompt_for_module(*, level: str, slug: str) -> str:
    """Render a writer prompt without invoking a writer agent."""
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.plan_check(plan_path)
    plan_content = plan_path.read_text(encoding="utf-8")
    wiki_manifest_data = linear_pipeline.build_wiki_manifest_data(
        level=level,
        slug=slug,
        plan=plan,
    )
    implementation_map = seed_implementation_map(wiki_manifest_data, plan=plan)
    return linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_content,
        knowledge_packet="Knowledge packet stub for leakage-sentinel prompt rendering.",
        wiki_manifest=json.dumps(wiki_manifest_data, ensure_ascii=False, indent=2),
        implementation_map=implementation_map,
    )


def _extract_lesson_specific_tokens(*, level: str, slug: str) -> set[str]:
    """Return lesson-specific wiki/plan tokens that must not leak elsewhere."""
    tokens: set[str] = set()
    plan = _load_plan(level=level, slug=slug)
    wiki_path = PROJECT_ROOT / "wiki" / "pedagogy" / level / f"{slug}.md"
    wiki_manifest = extract_manifest(wiki_path)

    for item in wiki_manifest.get("wiki_vocabulary_minimum", []):
        if isinstance(item, dict):
            tokens.update(_split_vocab_lemma(str(item.get("lemma") or "")))

    for ref in _plan_references(plan):
        tokens.update(_extract_textbook_author_names(str(ref.get("title") or "")))
        tokens.update(CHUNK_ID_RE.findall(str(ref.get("notes") or "")))

    for item in wiki_manifest.get("decolonization_bans", []):
        if isinstance(item, dict):
            tokens.update(_extract_decolonization_contrast_tokens(str(item.get("rule") or "")))

    return _clean_tokens(tokens)


def _load_plan(*, level: str, slug: str) -> dict[str, Any]:
    plan_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / level / f"{slug}.yaml"
    with plan_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), f"Plan must be a mapping: {plan_path}"
    return data


def _lesson_source_text(*, level: str, slug: str) -> str:
    plan_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / level / f"{slug}.yaml"
    wiki_path = PROJECT_ROOT / "wiki" / "pedagogy" / level / f"{slug}.md"
    return "\n".join(
        [
            plan_path.read_text(encoding="utf-8"),
            wiki_path.read_text(encoding="utf-8"),
        ]
    )


def _plan_references(plan: dict[str, Any]) -> list[dict[str, Any]]:
    references = plan.get("references") or []
    return [ref for ref in references if isinstance(ref, dict)]


def _split_vocab_lemma(lemma: str) -> set[str]:
    cleaned = re.sub(r"\([^)]*\)", "", lemma)
    return {part.strip(" `*.;:") for part in re.split(r"\s*/\s*|\s*,\s*", cleaned)}


def _extract_textbook_author_names(title: str) -> set[str]:
    if not TEXTBOOK_HINT_RE.search(title):
        return set()
    return {match.group(0) for match in CYRILLIC_WORD_RE.finditer(title)}


def _extract_decolonization_contrast_tokens(rule: str) -> set[str]:
    tokens = set(BAD_MARKER_RE.findall(rule))
    contrast_pair_re = re.compile(
        r"[«“]([^»”]+)[»”]\s*\(\s*не\s+[«“]([^»”]+)[»”]\s*\)",
        re.IGNORECASE,
    )
    for good, bad in contrast_pair_re.findall(rule):
        tokens.update({good, bad})
    if "замін" in rule.casefold() or "замість" in rule.casefold():
        tokens.update(QUOTED_TEXT_RE.findall(rule))
    return tokens


def _clean_tokens(tokens: set[str]) -> set[str]:
    cleaned: set[str] = set()
    for token in tokens:
        normalized = re.sub(r"\s+", " ", token).strip(" `*.;:()[]{}")
        if len(normalized) >= MIN_TOKEN_LENGTH:
            cleaned.add(normalized)
    return cleaned


def _contains_token(text: str, token: str) -> bool:
    if re.fullmatch(r"[А-ЯІЇЄҐа-яіїєґ'’ʼ-]+", token):
        token_re = re.compile(
            rf"(?<![А-ЯІЇЄҐа-яіїєґ'’ʼ-]){re.escape(token)}(?![А-ЯІЇЄҐа-яіїєґ'’ʼ-])"
        )
        return bool(token_re.search(text))
    return token in text
