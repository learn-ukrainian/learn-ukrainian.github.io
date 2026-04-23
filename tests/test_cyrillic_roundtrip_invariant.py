"""Golden-corpus invariant for Cyrillic text handling in ``scripts/``.

Covers EPIC #1451 Phase 4-B and extends the #1448 Unicode-regression work.
Every path listed in ``INVENTORY`` must be either:

- covered by ``ROUND_TRIPPERS`` in this file, or
- explicitly exempted with a note explaining why exact byte-preserving
  round-trip is not the right assertion for that code path.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analytics.vocab_progression import normalize_surface
from audit.checks.euphony import auto_fix_euphony
from audit.checks.grammar import _strip_stress as grammar_strip_stress
from audit.checks.plan_adherence import _strip_stress as plan_adherence_strip_stress
from audit.checks.stress_verification import _extract_stressed_words
from audit.cleaners import split_sentences
from linguistics.tokenize_uk import tokenize_sents, tokenize_text, tokenize_words
from rag.rag_batch_verify import strip_stress as rag_strip_stress
from rag.rag_batch_verify import tokenize_all_ukrainian
from wiki.context import _normalize_text as wiki_context_normalize_text
from wiki.diagnostics.retrieval_playback import normalize_text as retrieval_normalize_text

CORPUS = yaml.safe_load(
    (REPO_ROOT / "tests" / "fixtures" / "cyrillic_roundtrip_corpus.yaml").read_text(encoding="utf-8")
)
CASES = CORPUS["cases"]
CASES_BY_ID = {case["id"]: case for case in CASES}

FOLLOWUP_ISSUE = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1487"


@dataclass(frozen=True)
class RoundTripper:
    name: str
    fn: Callable[[str], str]
    case_ids: frozenset[str]


INVENTORY = {
    "linguistics.tokenize_words": {
        "coverage": "roundtrip",
        "path": "scripts/linguistics/tokenize_uk.py",
        "needle": "def tokenize_words(",
        "notes": "Ordered tokenizer; reconstructed from token sequence.",
    },
    "linguistics.tokenize_sents": {
        "coverage": "roundtrip",
        "path": "scripts/linguistics/tokenize_uk.py",
        "needle": "def tokenize_sents(",
        "notes": "Sentence tokenizer; reconstructed from sentence sequence.",
    },
    "linguistics.tokenize_text": {
        "coverage": "roundtrip",
        "path": "scripts/linguistics/tokenize_uk.py",
        "needle": "def tokenize_text(",
        "notes": "Nested tokenizer; flattened and reconstructed in order.",
    },
    "audit.cleaners.split_sentences": {
        "coverage": "roundtrip",
        "path": "scripts/audit/cleaners.py",
        "needle": "def split_sentences(",
        "notes": "Shared audit sentence splitter wrapping tokenize_uk.",
    },
    "audit.checks.stress_verification._extract_stressed_words": {
        "coverage": "roundtrip",
        "path": "scripts/audit/checks/stress_verification.py",
        "needle": "def _extract_stressed_words(",
        "notes": "Ordered extractor; only applicable to stress-marked corpus rows.",
    },
    "audit.checks.euphony.auto_fix_euphony": {
        "coverage": "roundtrip",
        "path": "scripts/audit/checks/euphony.py",
        "needle": "def auto_fix_euphony(",
        "notes": "Only identity-safe corpus rows are routed here.",
    },
    "rag.rag_batch_verify.tokenize_all_ukrainian": {
        "coverage": "roundtrip",
        "path": "scripts/rag/rag_batch_verify.py",
        "needle": "def tokenize_all_ukrainian(",
        "notes": "Reconstructed from the reported original tokens.",
    },
    "rag.rag_batch_verify.strip_stress": {
        "coverage": "roundtrip",
        "path": "scripts/rag/rag_batch_verify.py",
        "needle": "def strip_stress(",
        "notes": "Identity-safe on corpus rows without stress marks.",
    },
    "analytics.vocab_progression.normalize_surface": {
        "coverage": "roundtrip",
        "path": "scripts/analytics/vocab_progression.py",
        "needle": "def normalize_surface(",
        "notes": "Identity-safe only for already-normalized lowercase rows.",
    },
    "wiki.diagnostics.retrieval_playback.normalize_text": {
        "coverage": "roundtrip",
        "path": "scripts/wiki/diagnostics/retrieval_playback.py",
        "needle": "def normalize_text(",
        "notes": "Identity-safe only for lowercase rows that do not rely on apostrophe folding or NBSP collapse.",
    },
    "wiki.context._normalize_text": {
        "coverage": "roundtrip",
        "path": "scripts/wiki/context.py",
        "needle": "def _normalize_text(",
        "notes": "Identity-safe on clean lowercase words after the #1487 NFC recompose fix.",
    },
    "audit.checks.plan_adherence._strip_stress": {
        "coverage": "roundtrip",
        "path": "scripts/audit/checks/plan_adherence.py",
        "needle": "def _strip_stress(",
        "notes": "Identity-safe on non-stressed text after the #1487 NFC recompose fix.",
    },
    "audit.checks.grammar._strip_stress": {
        "coverage": "roundtrip",
        "path": "scripts/audit/checks/grammar.py",
        "needle": "def _strip_stress(",
        "notes": "Identity-safe on non-stressed text after the #1487 NFC recompose fix.",
    },
    "audit.check_plan._dialogue_tokens": {
        "coverage": "exempt",
        "path": "scripts/audit/check_plan.py",
        "needle": "def _dialogue_tokens(",
        "notes": "Unordered lowercase token set used for scene matching; exact byte round-trip is not the contract.",
    },
    "audit.checks.cross_file_integrity.extract_ukrainian_stem": {
        "coverage": "exempt",
        "path": "scripts/audit/checks/cross_file_integrity.py",
        "needle": "def extract_ukrainian_stem(",
        "notes": "Intentional heuristic stemmer; destructive by design.",
    },
    "audit.checks.content_gaming._tokenize_ukrainian": {
        "coverage": "exempt",
        "path": "scripts/audit/checks/content_gaming.py",
        "needle": "def _tokenize_ukrainian(",
        "notes": "Unordered lowercase token set for similarity scoring.",
    },
    "build.exercise_verify.extract_prose_words": {
        "coverage": "exempt",
        "path": "scripts/build/exercise_verify.py",
        "needle": "def extract_prose_words(",
        "notes": "Lowercasing extractor with stress-folding side channel; use existing exercise-verifier tests instead.",
    },
    "build.exercise_verify.extract_plan_vocab": {
        "coverage": "exempt",
        "path": "scripts/build/exercise_verify.py",
        "needle": "def extract_plan_vocab(",
        "notes": "Lowercasing vocabulary extractor, not a reversible text pipeline.",
    },
    "build.phases.wiki_compressor._tokenize": {
        "coverage": "exempt",
        "path": "scripts/build/phases/wiki_compressor.py",
        "needle": "def _tokenize(",
        "notes": "Unordered token set already covered by tests/test_wiki_compressor_tokenize.py.",
    },
    "wiki.query_builder.build_query_buckets": {
        "coverage": "exempt",
        "path": "scripts/wiki/query_builder.py",
        "needle": "def build_query_buckets(",
        "notes": "Bucket builder depends on normalize_text and emits quoted phrases/token sets, not a byte-preserving round-trip string.",
    },
    "wiki.sources_db._tokenize_normalized_text": {
        "coverage": "exempt",
        "path": "scripts/wiki/sources_db.py",
        "needle": "def _tokenize_normalized_text(",
        "notes": "Unordered token set after retrieval normalization.",
    },
}

ROUND_TRIPPERS = [
    RoundTripper(
        name="linguistics.tokenize_words",
        fn=lambda text: _reconstruct_from_chunks(text, tokenize_words(text)),
        case_ids=frozenset(CASES_BY_ID),
    ),
    RoundTripper(
        name="linguistics.tokenize_sents",
        fn=lambda text: _reconstruct_from_chunks(text, tokenize_sents(text)),
        case_ids=frozenset(CASES_BY_ID),
    ),
    RoundTripper(
        name="linguistics.tokenize_text",
        fn=lambda text: _reconstruct_from_chunks(
            text,
            [token for paragraph in tokenize_text(text) for sentence in paragraph for token in sentence],
        ),
        case_ids=frozenset(CASES_BY_ID),
    ),
    RoundTripper(
        name="audit.cleaners.split_sentences",
        fn=lambda text: _reconstruct_from_chunks(text, split_sentences(text)),
        case_ids=frozenset(CASES_BY_ID),
    ),
    RoundTripper(
        name="audit.checks.stress_verification._extract_stressed_words",
        fn=lambda text: _reconstruct_from_chunks(text, [word for word, _ in _extract_stressed_words(text)]),
        case_ids=frozenset({"stress_acute"}),
    ),
    RoundTripper(
        name="audit.checks.euphony.auto_fix_euphony",
        fn=lambda text: auto_fix_euphony(text)[0],
        case_ids=frozenset(CASES_BY_ID),
    ),
    RoundTripper(
        name="rag.rag_batch_verify.tokenize_all_ukrainian",
        fn=lambda text: _reconstruct_from_chunks(text, [original for original, _ in tokenize_all_ukrainian(text)]),
        case_ids=frozenset(CASES_BY_ID),
    ),
    RoundTripper(
        name="rag.rag_batch_verify.strip_stress",
        fn=rag_strip_stress,
        case_ids=frozenset(
            {
                "iotation_y_short_word",
                "iotation_yi_words",
                "iotation_phrase_ascii",
                "apostrophe_ascii",
                "apostrophe_modifier_letter",
                "apostrophe_right_single_quote",
                "soft_sign",
                "mixed_scripts",
                "compound_hyphenated",
                "numbers_with_ukrainian",
                "emoji_passthrough",
                "em_dash_nbsp",
            }
        ),
    ),
    RoundTripper(
        name="analytics.vocab_progression.normalize_surface",
        fn=normalize_surface,
        case_ids=frozenset(
            {
                "iotation_y_short_word",
                "iotation_yi_words",
                "iotation_phrase_ascii",
                "apostrophe_ascii",
                "soft_sign",
                "mixed_scripts",
                "compound_hyphenated",
            }
        ),
    ),
    RoundTripper(
        name="wiki.diagnostics.retrieval_playback.normalize_text",
        fn=retrieval_normalize_text,
        case_ids=frozenset(
            {
                "iotation_y_short_word",
                "iotation_yi_words",
                "iotation_phrase_ascii",
                "apostrophe_ascii",
                "soft_sign",
                "mixed_scripts",
                "stress_acute",
                "compound_hyphenated",
                "numbers_with_ukrainian",
                "emoji_passthrough",
            }
        ),
    ),
    RoundTripper(
        name="wiki.context._normalize_text",
        fn=wiki_context_normalize_text,
        case_ids=frozenset({"iotation_y_short_word", "iotation_yi_words"}),
    ),
    RoundTripper(
        name="audit.checks.plan_adherence._strip_stress",
        fn=plan_adherence_strip_stress,
        case_ids=frozenset({"iotation_y_short_word", "iotation_yi_words", "iotation_phrase_ascii"}),
    ),
    RoundTripper(
        name="audit.checks.grammar._strip_stress",
        fn=grammar_strip_stress,
        case_ids=frozenset({"iotation_y_short_word", "iotation_yi_words", "iotation_phrase_ascii"}),
    ),
]

KNOWN_XFAILS = {
}


def _reconstruct_from_chunks(text: str, chunks: list[str]) -> str:
    if not chunks:
        raise AssertionError("Round-trip helper received no chunks to reconstruct.")

    position = 0
    rebuilt: list[str] = []
    for chunk in chunks:
        index = text.find(chunk, position)
        if index < 0:
            raise AssertionError(f"Chunk {chunk!r} was not found after position {position} in {text!r}")
        rebuilt.append(text[position:index])
        rebuilt.append(chunk)
        position = index + len(chunk)
    rebuilt.append(text[position:])
    return "".join(rebuilt)


def _roundtrip_params() -> list[object]:
    params = []
    for path in ROUND_TRIPPERS:
        # Sort frozenset iteration to keep test collection deterministic
        # across pytest-xdist workers. Without this, gw0 and gw1 see
        # different test IDs and xdist refuses to run. Frozensets hash
        # differently per Python invocation (PYTHONHASHSEED), so iteration
        # order is not stable across the subprocesses xdist spawns.
        for case_id in sorted(path.case_ids):
            case = CASES_BY_ID[case_id]
            params.append(pytest.param(path, case, id=f"{path.name}[{case_id}]"))
    return params


@pytest.mark.parametrize(("path", "case"), _roundtrip_params())
def test_cyrillic_text_paths_preserve_bytes(path: RoundTripper, case: dict[str, str]) -> None:
    xfail_issue = KNOWN_XFAILS.get((path.name, case["id"]))
    if xfail_issue is not None:
        pytest.xfail(f"Pre-existing Unicode drift tracked in {xfail_issue}")

    got = path.fn(case["text"])
    assert got == case["text"], (
        f"Round-trip mutated Cyrillic: case={case['id']} path={path.name}\n"
        f"  input : {case['text']!r}\n"
        f"  output: {got!r}\n"
        f"  notes : {case.get('notes', '')}"
    )


def test_inventory_entries_still_point_at_real_code_paths() -> None:
    for path_name, meta in INVENTORY.items():
        text = (REPO_ROOT / meta["path"]).read_text(encoding="utf-8")
        assert meta["needle"] in text, f"Inventory entry {path_name} no longer matches {meta['path']}"


def test_inventory_roundtrip_registry_is_complete() -> None:
    inventory_roundtrips = {name for name, meta in INVENTORY.items() if meta["coverage"] == "roundtrip"}
    registry_names = {entry.name for entry in ROUND_TRIPPERS}
    assert registry_names == inventory_roundtrips


def test_inventory_exemptions_are_documented() -> None:
    undocumented = [
        name
        for name, meta in INVENTORY.items()
        if meta["coverage"] == "exempt" and not meta.get("notes", "").strip()
    ]
    assert undocumented == []


def test_new_unicode_handler_names_require_inventory_updates() -> None:
    candidate_names = {
        "tokenize_words",
        "tokenize_sents",
        "tokenize_text",
        "split_sentences",
        "_strip_stress",
        "_extract_stressed_words",
        "auto_fix_euphony",
        "tokenize_all_ukrainian",
        "strip_stress",
        "normalize_surface",
        "normalize_text",
        "_normalize_text",
        "_dialogue_tokens",
        "extract_ukrainian_stem",
        "_tokenize_ukrainian",
        "extract_prose_words",
        "extract_plan_vocab",
        "_tokenize",
        "build_query_buckets",
        "_tokenize_normalized_text",
    }
    expected = {meta["needle"][4:-1] for meta in INVENTORY.values()}
    found: set[str] = set()
    for path in (REPO_ROOT / "scripts").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\(", text, re.MULTILINE):
            if match.group(1) in candidate_names:
                found.add(match.group(1))

    unexpected = sorted(found - expected)
    assert unexpected == [], (
        "New Unicode/text-handling helpers were found without an inventory entry: "
        + ", ".join(unexpected)
    )
