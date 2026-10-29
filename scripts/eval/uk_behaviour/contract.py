"""Frozen terms of ``uk-behaviour/2``: families, modes, caps, seats and statuses.

Every number here is either quoted from ``docs/evaluations/uk-behaviour-freeze.md``
or a G3 seal that the protocol leaves to the evaluation maintainer (the size and
claim caps, and the answer-position rule). ``manifest_problems`` checks the
public manifest against these constants, so a drift fails before any scoring.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.eval.uk_preamble.common import Seat

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "docs" / "evaluations" / "uk-behaviour-freeze.manifest.json"

PROTOCOL = "uk-behaviour/2"
SCORER = "uk-behaviour-score/2"
MANIFEST_SCHEMA = "uk-behaviour-freeze/2"
HARNESS = "uk-behaviour-harness/1"

SPLITS = ("development", "selection", "final")
JUDGING_MODES = ("repair", "authoring")
STRATA = ("dialect", "heritage", "rare_valid")
REPEATS = 3
SOURCES_CALLS_PER_PASS = 32  # per tool-enabled candidate, judge, dispute and deterministic pass
HARD_TIMEOUT_SECONDS = 1200
OUTPUT_SHUFFLE_SEED = 10453
AUDIT_SELECTION_SEED = 10454

# Cell statuses in precedence order (protocol § Authority and verifiable receipts).
INVALID_FABRICATED_RECEIPT = "INVALID_FABRICATED_RECEIPT"
INVALID_OVERPRODUCTION = "INVALID_OVERPRODUCTION"
UNRESOLVED_EVALUATOR = "UNRESOLVED_EVALUATOR"
COMPLETE = "COMPLETE"
STATUS_PRECEDENCE = (INVALID_FABRICATED_RECEIPT, INVALID_OVERPRODUCTION, UNRESOLVED_EVALUATOR, COMPLETE)

# The claim facets of the authority table and the pedagogy and exercise dimensions.
FACETS = (
    "form",
    "stress",
    "meaning",
    "historical",
    "naturalness",
    "pedagogy",
    "spelling_style",
    "exercise",
)

EXERCISE_DEFECTS = (
    "stem_translates_answer",
    "stem_names_answer",
    "stem_describes_form",
    "giveaway_gloss",
    "distractor_agreement_leak",
    "ambiguous_key",
    "wrong_key",
    "stress",
    "form",
    "answer_position_pattern",
)
PEDAGOGY_DEFECTS = (
    "standard_coverage_or_sequencing",
    "textbook_sequencing",
    "prerequisite_or_load",
    "child_level",
    "target_mismatch",
    "incomplete_or_unsuitable_section",
    "answer_given_away",
    "missing_planned_video",
    "hidden_player_audio_only",
    "ohoiko_presentation",
)
# Exercise defects that rest on the request alone (its exact text, or the key positions derived
# from it); the others also need Sources receipts for their linguistic premise.
EXERCISE_REQUEST_DEFECTS = frozenset(
    {"stem_translates_answer", "stem_names_answer", "stem_describes_form", "giveaway_gloss", "answer_position_pattern"}
)
# The facet whose authorities a linguistic exercise defect's own receipt must satisfy.
EXERCISE_DEFECT_FACETS = {
    "distractor_agreement_leak": "form",
    "ambiguous_key": "meaning",
    "wrong_key": "meaning",
    "stress": "stress",
    "form": "form",
}
PEDAGOGY_NORMS = ("state_standard_2024", "ukrainian_school_textbooks", "ohoiko_method")
ANCHOR_KINDS = (
    "standard_lines",
    "coverage_map",
    "textbook_page",
    "ohoiko_practice",
    "ohoiko_progression",
    "learner_state",
    "adult_adaptation",
    "video_resource",
    "video_decision",
    "leak",
)
# The one permitted source of each anchor kind: a Sources receipt (``search_text``) for a
# textbook page, a JSON pointer below the named request field, or else a ``norm_evidence``
# entry of the same kind.
ANCHOR_RECEIPT_KINDS = frozenset({"textbook_page"})
ANCHOR_POINTER_ROOTS = {"learner_state": "/learner_state", "leak": "/snippet"}
# Required anchors per pedagogy defect (protocol roster, lines 206-215): each tuple is one
# required part, satisfied by an anchor of any kind it lists.
PEDAGOGY_ANCHORS: dict[str, tuple[tuple[str, ...], ...]] = {
    "standard_coverage_or_sequencing": (("standard_lines",), ("coverage_map",)),
    "textbook_sequencing": (("textbook_page",),),
    "prerequisite_or_load": (("learner_state",), ("textbook_page", "ohoiko_progression")),
    "child_level": (("textbook_page",), ("adult_adaptation",)),
    "target_mismatch": (("standard_lines", "textbook_page"),),
    "incomplete_or_unsuitable_section": (("standard_lines", "textbook_page"),),
    "answer_given_away": (("ohoiko_practice",), ("leak",)),
    "missing_planned_video": (("standard_lines",), ("ohoiko_practice",), ("video_resource",), ("video_decision",)),
    "hidden_player_audio_only": (("standard_lines",), ("ohoiko_practice",), ("video_resource",), ("video_decision",)),
    "ohoiko_presentation": (("ohoiko_practice",), ("ohoiko_progression",), ("learner_state",)),
}
CARD_FACETS = ("meaning", "stress", "form")


@dataclass(frozen=True)
class SizeCap:
    """Presealed maximum size of one candidate output (protocol lines 531-532 and 626-629).

    ``max_tokens`` counts scoring tokens (``uk_preamble.common.tokenize``), a deterministic
    measure; provider token limits are runtime settings pinned with the baseline runner.
    Claims are the assertions a judge enumerates, every repetition included. ``batched``
    bounds those whose evidence a shared batched call checks (forms through ``verify_words``,
    senses and paradigms through ``query_ulif_records``; writer families only) and
    ``max_claims`` bounds the rest, which are checked one by one. ``max_edits`` bounds
    proposed or applied edits.
    """

    max_bytes: int
    max_tokens: int
    max_claims: int
    max_edits: int
    batched: int = 0


@dataclass(frozen=True)
class FamilyContract:
    family: str
    kind: str  # the inherited dispatch kind: "writing" or "review"
    sources_tools: bool  # fresh writers do not search (writer contract)
    candidate_receipts_required: bool  # a finding earns credit only through its own cited receipt
    prompt: str  # repository path of a pinned production asset, or a private slot
    output: str  # "lesson-draft", "v7-module", "review-envelope" or "passage-envelope"
    modes: tuple[str, ...]
    cap: SizeCap


PRIVATE_PROMPT_SLOTS = {
    "card_review": "private://uk-behaviour-v2/card-review-prompt",
    "exercise_review": "private://uk-behaviour-v2/exercise-review-prompt",
    "pedagogy_review": "private://uk-behaviour-v2/pedagogy-review-prompt",
}
JUDGE_SLOT = "private://uk-behaviour-v2/semantic-scorer-and-judge-template"

# Caps are G3 seals. Writer caps exceed the largest tracked production artifact of their
# kind (A2 V7 module.md 30.6 KB plus activities 23.1 KB; A1 lessons are smaller), so a
# production-sized output never trips them. Review caps follow the request size: one card,
# one exercise block, one snippet or one passage. Every cap fits the 32-call judge budget
# under ``coverage.plan_calls``; the no-paid proof checks that at each cap.
FAMILIES: dict[str, FamilyContract] = {
    "fresh_lesson": FamilyContract(
        "fresh_lesson",
        "writing",
        False,
        False,
        "scripts/build/fresh/prompts/lesson-writer.md.j2",
        "lesson-draft",
        ("authoring",),
        SizeCap(max_bytes=65536, max_tokens=16384, max_claims=12, max_edits=0, batched=400),
    ),
    "fresh_activities": FamilyContract(
        "fresh_activities",
        "writing",
        False,
        False,
        "scripts/build/fresh/prompts/lesson-writer.md.j2",
        "lesson-draft",
        ("authoring",),
        SizeCap(max_bytes=65536, max_tokens=16384, max_claims=12, max_edits=0, batched=400),
    ),
    "v7_module": FamilyContract(
        "v7_module",
        "writing",
        True,
        False,
        "agents_extensions/shared/agents/curriculum-writer.md",
        "v7-module",
        ("authoring",),
        SizeCap(max_bytes=131072, max_tokens=40000, max_claims=10, max_edits=0, batched=400),
    ),
    "exercise_review": FamilyContract(
        "exercise_review",
        "review",
        True,
        True,
        PRIVATE_PROMPT_SLOTS["exercise_review"],
        "review-envelope",
        ("repair",),
        SizeCap(max_bytes=24576, max_tokens=6144, max_claims=12, max_edits=12),
    ),
    "card_review": FamilyContract(
        "card_review",
        "review",
        True,
        True,
        PRIVATE_PROMPT_SLOTS["card_review"],
        "review-envelope",
        ("repair",),
        SizeCap(max_bytes=16384, max_tokens=4096, max_claims=8, max_edits=8),
    ),
    "passage_review": FamilyContract(
        "passage_review",
        "review",
        True,
        True,
        "agents_extensions/shared/skills/content-review/content-review-prompt.md",
        "passage-envelope",
        ("repair", "authoring"),
        SizeCap(max_bytes=32768, max_tokens=8192, max_claims=14, max_edits=14),
    ),
    "pedagogy_review": FamilyContract(
        "pedagogy_review",
        "review",
        True,
        True,
        PRIVATE_PROMPT_SLOTS["pedagogy_review"],
        "review-envelope",
        ("repair", "authoring"),
        SizeCap(max_bytes=24576, max_tokens=6144, max_claims=10, max_edits=0),
    ),
}
FAMILY_ORDER = tuple(FAMILIES)

CANDIDATE_SEATS: dict[str, Seat] = {
    "gpt-6.1-sol": Seat("gpt-6.1-sol", "sol", "codex", "gpt-6.1-sol", "high", "openai"),
    "gpt-6.1-terra": Seat("gpt-6.1-terra", "terra", "codex", "gpt-6.1-terra", "high", "openai"),
}
PRIMARY_JUDGE = Seat("claude-opus-5-5", "opus", "claude", "claude-opus-5-5", "high", "anthropic")
AUDIT_JUDGE = Seat("gemini-3.8-flash-high", "flash", "agy", "gemini-3.8-flash-high", None, "google")


def answer_position_pattern(key_positions: list[int]) -> bool:
    """The frozen answer-position rule of the exercise-review prompt.

    It applies to an ordered block of at least six choice items. The block has the defect
    when one zero-based key position holds the key in at least 80% of the items (rounded
    up), or when every item's position equals the position 2 (or 3) items earlier, from
    the first item to the last; a final partial cycle counts.
    """
    count = len(key_positions)
    if count < 6:
        return False
    if max(key_positions.count(position) for position in set(key_positions)) >= math.ceil(0.8 * count):
        return True
    return any(all(key_positions[i] == key_positions[i % period] for i in range(count)) for period in (2, 3))


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_problems(manifest: dict[str, Any]) -> list[str]:
    """Where the public manifest departs from the constants this scorer implements."""
    problems = []
    expected = {
        "schema": MANIFEST_SCHEMA,
        "protocol": PROTOCOL,
        "scorer": SCORER,
        "repeats": REPEATS,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            problems.append(f"manifest {key} is {manifest.get(key)!r}, not {value!r}")
    budget = manifest.get("budget", {})
    if budget.get("sources_calls_per_pass") != SOURCES_CALLS_PER_PASS:
        problems.append("manifest Sources calls per pass differ from 32")
    if budget.get("hard_timeout_seconds") != HARD_TIMEOUT_SECONDS:
        problems.append("manifest hard timeout differs from 1200 seconds")
    custody = manifest.get("custody", {})
    if custody.get("output_shuffle_seed") != OUTPUT_SHUFFLE_SEED:
        problems.append("manifest output shuffle seed differs from 10453")
    if custody.get("audit_selection_seed") != AUDIT_SELECTION_SEED:
        problems.append("manifest audit selection seed differs from 10454")
    if manifest.get("scoring", {}).get("macro_family_count") != len(FAMILIES):
        problems.append("manifest macro family count differs from the seven families")
    for split in SPLITS:
        counts = manifest.get("splits", {}).get(split, {})
        modes = counts.get("modes_by_family", {})
        if set(modes) != set(FAMILIES):
            problems.append(f"{split}: mode table families differ from the seven families")
            continue
        for family, contract in FAMILIES.items():
            used = {mode for mode, number in modes[family].items() if number}
            if not used <= set(contract.modes):
                problems.append(f"{split}: {family} uses modes {sorted(used)} outside {list(contract.modes)}")
        defects = counts.get("exercise_defects_by_kind", {})
        if tuple(defects) != EXERCISE_DEFECTS:
            problems.append(f"{split}: exercise defect kinds differ from the exercise-review prompt")
        kinds = [kind for kind in counts.get("pedagogy_defects_by_kind_and_mode", {}) if kind != "clean"]
        if tuple(kinds) != PEDAGOGY_DEFECTS:
            problems.append(f"{split}: pedagogy defect kinds differ from the pedagogy-review prompt")
        if counts.get("card_facets") != list(CARD_FACETS):
            problems.append(f"{split}: card facets differ from meaning, stress and form")
    return problems
