"""Learner-state audit checks for V7 modules."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import yaml

try:
    from scripts.config import get_immersion_structural
    from scripts.pipeline.learner_state import build_learner_state
except ModuleNotFoundError:  # pragma: no cover - CLI path compatibility
    from config import get_immersion_structural
    from pipeline.learner_state import build_learner_state

VerifyWordsFn = Callable[[list[str]], dict[str, list[dict[str, Any]]]]

# Closed-class words are grammatical glue: learners need them to parse A1 prose,
# but they should not be treated like newly introduced content vocabulary.
CLOSED_CLASS_FUNCTION_WORDS = frozenset(
    {
        # Personal and demonstrative pronouns: high-frequency reference words.
        "я",
        "ти",
        "він",
        "вона",
        "воно",
        "ми",
        "ви",
        "вони",
        "мене",
        "тебе",
        "його",
        "її",
        "нас",
        "вас",
        "їх",
        "мені",
        "тобі",
        "собі",
        "мій",
        "твій",
        "свій",
        "цей",
        "ця",
        "це",
        "ці",
        "той",
        "та",
        "те",
        "ті",
        # Prepositions: small relational words, not topical content lemmas.
        "у",
        "в",
        "на",
        "з",
        "із",
        "зі",
        "до",
        "від",
        "для",
        "без",
        "за",
        "під",
        "над",
        "перед",
        "після",
        "між",
        "біля",
        "через",
        "про",
        "при",
        # Conjunctions and discourse connectors needed for basic clauses.
        "і",
        "й",
        "але",
        "що",
        "як",
        "тому",
        "бо",
        "або",
        "чи",
        "якщо",
        "коли",
        "поки",
        "щоб",
        # Particles and deictics: frequent scaffolding tokens.
        "не",
        "ні",
        "же",
        "ж",
        "ось",
        "тут",
        "там",
        "ще",
        "вже",
        "лише",
        "тільки",
        "саме",
        # Interrogatives support A1 question formation and comprehension.
        "де",
        "куди",
        "звідки",
        "чому",
        "чого",
        "хто",
        "який",
        "яка",
        "яке",
        "які",
        "скільки",
        # Closed small numerals are common in schedules, ages, and exercise items.
        "один",
        "одна",
        "одне",
        "два",
        "дві",
        "три",
        "чотири",
        "п'ять",
        "шість",
        "сім",
        "вісім",
        "дев'ять",
        "десять",
        # Modal predicates are classroom-workhorse words across A1/A2 tasks.
        "можна",
        "треба",
        "потрібно",
    }
)

CONTENT_POS_PREFIXES = ("noun", "verb", "adj")
NON_CONTENT_POS_PREFIXES = ("prep", "conj", "part", "pron", "num", "advp", "intj")


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


def _load_json_or_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        if path.suffix == ".json":
            import json

            return json.loads(path.read_text(encoding="utf-8"))
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_plan_for_module(module_dir: str | Path | None, level: str) -> Mapping[str, Any] | None:
    if module_dir is None:
        return None
    path = Path(module_dir)
    slug = path.name
    plan_path = path.parents[1] / "plans" / level.lower() / f"{slug}.yaml" if len(path.parents) > 1 else None
    if plan_path is None or not plan_path.exists():
        plan_path = Path(__file__).resolve().parents[3] / "curriculum" / "l2-uk-en" / "plans" / level.lower() / f"{slug}.yaml"
    data = _load_json_or_yaml(plan_path)
    return data if isinstance(data, Mapping) else None


def _load_wiki_manifest_for_module(module_dir: str | Path | None) -> Mapping[str, Any] | None:
    if module_dir is None:
        return None
    data = _load_json_or_yaml(Path(module_dir) / "wiki_manifest.json")
    return data if isinstance(data, Mapping) else None


def _load_wiki_text_from_manifest(wiki_manifest: Mapping[str, Any] | None) -> str:
    if not wiki_manifest:
        return ""
    raw_path = str(wiki_manifest.get("wiki_path") or "").split(";", 1)[0].strip()
    if not raw_path:
        return ""
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[3] / path
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _plan_vocab_entries(plan: Mapping[str, Any] | None, source: str) -> set[str]:
    if not isinstance(plan, Mapping):
        return set()
    entries: set[str] = set()

    def add_entry(entry: Any) -> None:
        raw: str | None = None
        if isinstance(entry, str):
            raw = entry
        elif isinstance(entry, Mapping):
            for key in ("lemma", "word", "term", "text", "value"):
                value = entry.get(key)
                if isinstance(value, str):
                    raw = value
                    break
        if raw:
            lemma = re.split(r"\s+\(|\s+[—–-]\s+", raw, maxsplit=1)[0].strip()
            if lemma:
                entries.add(lemma)

    if source == "new_vocabulary":
        targets = plan.get("targets")
        if isinstance(targets, Mapping):
            for entry in targets.get("new_vocabulary", []) or []:
                add_entry(entry)
        return entries

    hints = plan.get("vocabulary_hints")
    if isinstance(hints, Mapping):
        for key in ("required", "recommended"):
            for entry in hints.get(key, []) or []:
                add_entry(entry)
    elif isinstance(hints, list):
        for entry in hints:
            add_entry(entry)
    return entries


def _wiki_vocabulary_entries(wiki_manifest: Mapping[str, Any] | None) -> set[str]:
    if not isinstance(wiki_manifest, Mapping):
        return set()
    return {
        str(item.get("lemma") or "").strip()
        for item in wiki_manifest.get("wiki_vocabulary_minimum", []) or []
        if isinstance(item, Mapping) and str(item.get("lemma") or "").strip()
    }


def _extract_bad_form_surfaces(*texts: str) -> set[str]:
    surfaces: set[str] = set()
    for text in texts:
        for match in re.finditer(r"<!--\s*bad\s*-->(.*?)<!--\s*/bad\s*-->", text, flags=re.IGNORECASE | re.DOTALL):
            surfaces.update(_extract_ukrainian_surfaces(match.group(1)))
    return surfaces


def _extract_quoted_evidence_surfaces(content: str) -> set[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in content.splitlines():
        if line.lstrip().startswith(">"):
            current.append(re.sub(r"^\s*>\s?", "", line))
            continue
        if current:
            blocks.append("\n".join(current))
            current = []
    if current:
        blocks.append("\n".join(current))
    surfaces: set[str] = set()
    for block in blocks:
        if re.search(r"\[S\d+\]", block):
            surfaces.update(_extract_ukrainian_surfaces(block))
    return surfaces


def _extract_proper_noun_surfaces(wiki_text: str) -> set[str]:
    surfaces: set[str] = set()
    for match in re.finditer(r"\b[А-ЯІЇЄҐ][а-яіїєґ]+(?:[-'’ʼ][А-ЯІЇЄҐа-яіїєґ]+)?\b", wiki_text):
        token = match.group(0)
        line_start = wiki_text.rfind("\n", 0, match.start()) + 1
        prefix = wiki_text[line_start:match.start()].strip()
        if not prefix or prefix.startswith("#"):
            continue
        surfaces.add(token.lower())
    return surfaces


def _verify_words(words: list[str], verify_words_fn: VerifyWordsFn | None) -> dict[str, list[dict[str, Any]]]:
    if not words:
        return {}
    if verify_words_fn is None:
        try:
            from scripts.verification.vesum import verify_words as verify_words_fn
        except Exception:
            return {word: [] for word in words}
    try:
        return verify_words_fn(words)
    except Exception:
        return {word: [] for word in words}


def _normalize_key(value: str) -> str:
    _, _normalize_for_vesum = _vesum_helpers()
    return _normalize_for_vesum(value).lower()


def _choose_vesum_match(matches: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not matches:
        return None
    for prefix in CONTENT_POS_PREFIXES:
        for match in matches:
            if str(match.get("pos") or "").lower().startswith(prefix):
                return match
    return matches[0]


def _surface_records(
    surfaces: list[str] | set[str],
    verify_words_fn: VerifyWordsFn | None,
) -> list[dict[str, str | None]]:
    ordered = sorted({_normalize_key(surface) for surface in surfaces if str(surface).strip()})
    matches_by_word = _verify_words(ordered, verify_words_fn)
    records: list[dict[str, str | None]] = []
    for surface in ordered:
        match = _choose_vesum_match(matches_by_word.get(surface, []))
        lemma = _normalize_key(str(match.get("lemma"))) if match and match.get("lemma") else surface
        pos = str(match.get("pos")) if match and match.get("pos") else None
        records.append({"surface": surface, "lemma": lemma, "pos": pos})
    return records


def _normalize_entry_set(
    entries: set[str],
    verify_words_fn: VerifyWordsFn | None,
) -> set[str]:
    surfaces: set[str] = set()
    for entry in entries:
        surfaces.update(_extract_ukrainian_surfaces(entry))
    return {str(record["lemma"]) for record in _surface_records(surfaces, verify_words_fn)}


def build_layered_allowlist(
    *,
    level: str,
    module_num: int,
    module_dir: str | Path | None = None,
    wiki_manifest: Mapping[str, Any] | None = None,
    plan: Mapping[str, Any] | None = None,
    wiki_text: str = "",
    content: str = "",
    verify_words_fn: VerifyWordsFn | None = None,
) -> dict[str, set[str]]:
    """Build the V7.1 layered vocabulary allowlist by source."""
    level_key = level.lower()
    manifest = wiki_manifest or _load_wiki_manifest_for_module(module_dir)
    plan_data = plan or _load_plan_for_module(module_dir, level_key)
    wiki_source_text = wiki_text or _load_wiki_text_from_manifest(manifest)
    learner_state = build_learner_state(level_key, module_num)

    sources = {
        "wiki_vocabulary_minimum": _normalize_entry_set(_wiki_vocabulary_entries(manifest), verify_words_fn),
        "plan_new_vocabulary": _normalize_entry_set(_plan_vocab_entries(plan_data, "new_vocabulary"), verify_words_fn),
        "plan_vocabulary_hints": _normalize_entry_set(_plan_vocab_entries(plan_data, "vocabulary_hints"), verify_words_fn),
        "cumulative_learner_state": _normalize_entry_set(
            {str(lemma) for lemma in learner_state.get("cumulative_vocabulary", []) if lemma},
            verify_words_fn,
        ),
        "closed_class_function_words": _normalize_entry_set(set(CLOSED_CLASS_FUNCTION_WORDS), verify_words_fn),
        "proper_nouns_in_wiki_examples": _extract_proper_noun_surfaces(wiki_source_text),
        "bad_form_markers": _normalize_entry_set(
            _extract_bad_form_surfaces(wiki_source_text, content),
            verify_words_fn,
        ),
        "quoted_evidence_from_cited_rag_chunks": _normalize_entry_set(
            _extract_quoted_evidence_surfaces(content),
            verify_words_fn,
        ),
    }
    legacy_vocab = _load_declared_vocab(module_dir)
    if legacy_vocab:
        sources["legacy_module_vocabulary"] = _normalize_entry_set(legacy_vocab, verify_words_fn)
    sources["_allowed_lemmas"] = set().union(
        *(
            value
            for key, value in sources.items()
            if key not in {"proper_nouns_in_wiki_examples"}
        )
    )
    sources["_allowed_surfaces"] = set(sources["proper_nouns_in_wiki_examples"])
    return sources


def _is_content_pos(pos: str | None) -> bool:
    if pos is None:
        return True
    pos_key = pos.lower()
    if pos_key.startswith(CONTENT_POS_PREFIXES):
        return True
    return not pos_key.startswith(NON_CONTENT_POS_PREFIXES)


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
    *,
    wiki_manifest: Mapping[str, Any] | None = None,
    plan: Mapping[str, Any] | None = None,
    wiki_text: str = "",
    max_unsupported: int | None = None,
    verify_words_fn: VerifyWordsFn | None = None,
) -> list[dict[str, Any]]:
    """Flag Ukrainian prose lemmas outside the V7.1 layered allowlist."""
    allowlist = build_layered_allowlist(
        level=level,
        module_num=module_num,
        module_dir=module_dir,
        wiki_manifest=wiki_manifest,
        plan=plan,
        wiki_text=wiki_text,
        content=content,
        verify_words_fn=verify_words_fn,
    )
    allowed_lemmas = allowlist["_allowed_lemmas"]
    allowed_surfaces = allowlist["_allowed_surfaces"]
    records = _surface_records(_extract_ukrainian_surfaces(content), verify_words_fn)
    unsupported = [
        record
        for record in records
        if str(record["lemma"]) not in allowed_lemmas
        and str(record["surface"]) not in allowed_surfaces
    ]
    tolerance = _unsupported_tolerance(level, module_num) if max_unsupported is None else max_unsupported
    if len(unsupported) <= tolerance:
        return []

    severity = _unknown_vocab_severity(module_num)
    content_unsupported = [
        record
        for record in unsupported
        if _is_content_pos(record.get("pos"))
    ]
    if not content_unsupported:
        return [
            {
                "type": "unknown_vocabulary_band",
                "severity": severity,
                "lemma": None,
                "unsupported_count": len(unsupported),
                "tolerance": tolerance,
                "issue": (
                    f"Unsupported Ukrainian function/edge tokens exceed the band "
                    f"({len(unsupported)} > {tolerance})."
                ),
                "fix": "Expand the closed-class allowlist or rewrite the prose with taught vocabulary.",
            }
        ]
    return [
        {
            "type": "unknown_vocabulary",
            "severity": severity,
            "lemma": str(record["lemma"]),
            "surface": str(record["surface"]),
            "pos": record.get("pos"),
            "issue": (
                f"Ukrainian lemma '{record['lemma']}' is not in the V7.1 "
                "wiki/plan/cumulative/closed-class layered allowlist."
            ),
            "fix": "Add the lemma to the wiki vocabulary minimum or plan vocabulary, or rewrite the prose.",
        }
        for record in content_unsupported
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
    *,
    wiki_manifest: Mapping[str, Any] | None = None,
    plan: Mapping[str, Any] | None = None,
    wiki_text: str = "",
    verify_words_fn: VerifyWordsFn | None = None,
) -> list[dict[str, Any]]:
    """Run all learner-state checks for a module."""
    return [
        *check_unknown_vocabulary(
            content,
            level,
            module_num,
            module_dir,
            wiki_manifest=wiki_manifest,
            plan=plan,
            wiki_text=wiki_text,
            verify_words_fn=verify_words_fn,
        ),
        *check_known_grammar_re_explanation(content, level, module_num),
    ]
