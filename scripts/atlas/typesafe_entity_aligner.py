"""Multi-Dictionary Entity Alignment and Decolonization Gate using TypeSafe System One.

Implements the entity alignment pattern from TypeSafe AI:
https://docs.typesafe.ai/cookbooks/entity_alignment.md

For candidate pairs of headwords across Ukrainian dictionary sources
(СУМ-20, ВТС, Грінченко 1907, ULIF, and historical СУМ-11):
1. Evaluates a single 3-level Score question:
   - Level 0: different_lexical_entity -> leave unlinked
   - Level 1: related_or_polysemous_needs_curator -> curator review
   - Level 2: same_lexical_entity -> candidate for unified Atlas entry
2. Parallel diagnostic Nouls evaluated in the same single System One request:
   - is_decolonized_preferred_variant (authentic Ukrainian vs Soviet/Russianism calque)
   - identical_pos_and_gender (morphosyntactic concord)
   - definition_semantic_match (referential equivalence)
3. Zero-threshold routing where score levels directly drive merge/curator actions.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class AlignmentAction(StrEnum):
    """The canonical disposition for a candidate dictionary entity pair."""

    UNLINKED = "unlinked"  # Different lexical entity; distinct concepts
    CURATOR_REVIEW = "curator_review"  # Related, near-synonym, or polysemous split
    MERGE = "merge"  # Exact lexical equivalent; decolonized peer


@dataclass(frozen=True)
class DictionaryEntry:
    """A headword entry from a specific Ukrainian dictionary source."""

    headword: str
    source: str  # 'СУМ-20', 'ВТС', 'Грінченко-1907', 'СУМ-11', 'ULIF'
    definition: str
    pos: str  # 'noun', 'verb', 'adj', 'adv'
    gender: str | None = None  # 'm', 'f', 'n'
    notes: str | None = None


@dataclass
class AlignmentEvaluation:
    """The structured result of evaluating two candidate dictionary entries."""

    candidate_a: str
    source_a: str
    candidate_b: str
    source_b: str
    action: AlignmentAction
    score_level: int  # 0, 1, or 2
    score_label: str
    confidence: float
    is_decolonized_preferred: bool
    identical_pos_and_gender: bool
    definition_semantic_match: bool
    probabilities: dict[str, float] = field(default_factory=dict)
    curator_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["action"] = self.action.value
        return data


def _resolve_typesafe_key() -> str:
    """Resolve TypeSafe API key from environment or user home secrets."""
    if key := os.environ.get("TYPESAFE_API_KEY", "").strip():
        return key
    for fname in ("typesafe-ai.key", "typsafe-ai.key"):
        path = Path.home() / ".secrets" / fname
        if path.is_file():
            try:
                line = path.read_text(encoding="utf-8").strip().splitlines()[0]
                if line:
                    return line
            except Exception:
                pass
    return ""


class TypeSafeEntityAligner:
    """Multi-dictionary entity aligner utilizing TypeSafe System One."""

    SCORE_LEVELS: ClassVar[dict[int, str]] = {
        0: "different_lexical_entity",
        1: "related_or_polysemous_needs_curator",
        2: "same_lexical_entity",
    }

    def __init__(self, api_key: str | None = None, model: str = "jev-latest", mock: bool = False):
        self.api_key = api_key or _resolve_typesafe_key()
        self.model = model
        self.mock = mock or not bool(self.api_key)

    def align_entries(self, entry_a: DictionaryEntry, entry_b: DictionaryEntry) -> AlignmentEvaluation:
        """Evaluate alignment between two dictionary entries using Score + Nouls."""
        if self.mock:
            return self._mock_alignment(entry_a, entry_b)

        state = {
            "entity_a": {
                "headword": entry_a.headword,
                "source": entry_a.source,
                "definition": entry_a.definition,
                "pos": entry_a.pos,
                "gender": entry_a.gender,
                "notes": entry_a.notes,
            },
            "entity_b": {
                "headword": entry_b.headword,
                "source": entry_b.source,
                "definition": entry_b.definition,
                "pos": entry_b.pos,
                "gender": entry_b.gender,
                "notes": entry_b.notes,
            },
        }

        questions = {
            "how_entities_relate": {
                "type": "score",
                "instructions": (
                    "How do `entity_a` and `entity_b` relate in the context of Ukrainian lexicography? "
                    "Level 0: different concepts or unrelated headwords. "
                    "Level 1: near-synonyms, polysemous sense splits, or stylistic variants requiring human curator inspection. "
                    "Level 2: same lexical entity or authentic decolonized synonym pairs denoting the identical referent."
                ),
                "levels": self.SCORE_LEVELS,
            },
            "is_decolonized_preferred": {
                "type": "noul",
                "instructions": (
                    "Is `entity_a` or `entity_b` an authentic/decolonized Ukrainian form (e.g. пилосмок, праска, слухавка) "
                    "contrasted with a Soviet/Russian calque (пилосос, утюг, трубка)?"
                ),
            },
            "identical_pos_and_gender": {
                "type": "noul",
                "instructions": "Do `entity_a` and `entity_b` have the exact same part of speech and grammatical gender?",
            },
            "definition_semantic_match": {
                "type": "noul",
                "instructions": "Do the definitions of `entity_a` and `entity_b` describe the exact same real-world concept or object?",
            },
        }

        body = json.dumps(
            {
                "state": state,
                "questions": questions,
                "model": self.model,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            "https://api.typesafe.ai/v1/systemone",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.load(resp)
        except Exception as e:
            # Fallback on network or API failure
            return self._mock_alignment(entry_a, entry_b, notes=f"Fallback from error: {e}")

        answers = data.get("answers", {})
        score_ans = answers.get("how_entities_relate", {})
        score_val = int(score_ans.get("score", 1))
        conf = float(score_ans.get("confidence", 0.75))
        probs = score_ans.get("probabilities", {})

        decol_noul = float(answers.get("is_decolonized_preferred", {}).get("noul", 0.0))
        pos_noul = float(answers.get("identical_pos_and_gender", {}).get("noul", 0.0))
        def_noul = float(answers.get("definition_semantic_match", {}).get("noul", 0.0))

        # Code-owned routing based on TypeSafe entity_alignment pattern
        if score_val == 2 and def_noul >= 0.70 and pos_noul >= 0.60:
            action = AlignmentAction.MERGE
        elif score_val == 0 or def_noul <= 0.20:
            action = AlignmentAction.UNLINKED
        else:
            action = AlignmentAction.CURATOR_REVIEW

        curator_notes = []
        if decol_noul >= 0.70:
            curator_notes.append("Decolonized vs Soviet/calque cluster pair detected.")
        if pos_noul < 0.50:
            curator_notes.append("Part of speech or grammatical gender discrepancy.")
        if def_noul < 0.60 and score_val >= 1:
            curator_notes.append("Partial definition divergence — check polysemy.")

        return AlignmentEvaluation(
            candidate_a=entry_a.headword,
            source_a=entry_a.source,
            candidate_b=entry_b.headword,
            source_b=entry_b.source,
            action=action,
            score_level=score_val,
            score_label=self.SCORE_LEVELS.get(score_val, "unknown"),
            confidence=conf,
            is_decolonized_preferred=(decol_noul >= 0.60),
            identical_pos_and_gender=(pos_noul >= 0.60),
            definition_semantic_match=(def_noul >= 0.60),
            probabilities=probs,
            curator_notes="; ".join(curator_notes),
        )

    def _mock_alignment(
        self, entry_a: DictionaryEntry, entry_b: DictionaryEntry, notes: str = ""
    ) -> AlignmentEvaluation:
        """High-precision simulated alignment for offline testing and CI environments."""
        hw_a = entry_a.headword.lower().strip()
        hw_b = entry_b.headword.lower().strip()

        # Known authentic decolonized synonym pairs
        decol_pairs = {
            frozenset(["пилосмок", "порохотяг"]): (2, True, True, True),
            frozenset(["пилосмок", "пилосос"]): (1, True, True, True),
            frozenset(["праска", "утюг"]): (1, True, True, True),
            frozenset(["слухавка", "трубка"]): (1, True, True, True),
            frozenset(["авто", "автомобіль"]): (2, False, True, True),
            frozenset(["летовище", "аеропорт"]): (2, True, True, True),
        }

        pair_key = frozenset([hw_a, hw_b])
        if pair_key in decol_pairs:
            score, decol, pos_match, def_match = decol_pairs[pair_key]
            action = AlignmentAction.MERGE if score == 2 else AlignmentAction.CURATOR_REVIEW
            cur_note = "Decolonized pair cluster" if decol else "Direct synonym"
            if notes:
                cur_note += f" ({notes})"
            return AlignmentEvaluation(
                candidate_a=entry_a.headword,
                source_a=entry_a.source,
                candidate_b=entry_b.headword,
                source_b=entry_b.source,
                action=action,
                score_level=score,
                score_label=self.SCORE_LEVELS[score],
                confidence=0.92,
                is_decolonized_preferred=decol,
                identical_pos_and_gender=pos_match,
                definition_semantic_match=def_match,
                probabilities={"0": 0.02, "1": 0.18, "2": 0.80} if score == 2 else {"0": 0.05, "1": 0.85, "2": 0.10},
                curator_notes=cur_note,
            )

        # Identical headwords from different dictionaries
        if hw_a == hw_b:
            pos_match = entry_a.pos == entry_b.pos
            def_match = (
                bool(entry_a.definition and entry_b.definition)
                and (entry_a.definition[:15] in entry_b.definition or entry_b.definition[:15] in entry_a.definition)
            )
            score = 2 if (pos_match and def_match) else 1
            action = AlignmentAction.MERGE if score == 2 else AlignmentAction.CURATOR_REVIEW
            return AlignmentEvaluation(
                candidate_a=entry_a.headword,
                source_a=entry_a.source,
                candidate_b=entry_b.headword,
                source_b=entry_b.source,
                action=action,
                score_level=score,
                score_label=self.SCORE_LEVELS[score],
                confidence=0.95 if score == 2 else 0.70,
                is_decolonized_preferred=False,
                identical_pos_and_gender=pos_match,
                definition_semantic_match=def_match,
                probabilities={"0": 0.01, "1": 0.09, "2": 0.90} if score == 2 else {"0": 0.10, "1": 0.75, "2": 0.15},
                curator_notes="Cross-dictionary identical headword" + (f" ({notes})" if notes else ""),
            )

        # Unrelated entities
        return AlignmentEvaluation(
            candidate_a=entry_a.headword,
            source_a=entry_a.source,
            candidate_b=entry_b.headword,
            source_b=entry_b.source,
            action=AlignmentAction.UNLINKED,
            score_level=0,
            score_label=self.SCORE_LEVELS[0],
            confidence=0.96,
            is_decolonized_preferred=False,
            identical_pos_and_gender=(entry_a.pos == entry_b.pos),
            definition_semantic_match=False,
            probabilities={"0": 0.96, "1": 0.03, "2": 0.01},
            curator_notes="Distinct lexical items" + (f" ({notes})" if notes else ""),
        )


def main() -> None:
    """CLI entrypoint for testing and evaluating dictionary alignments."""
    parser = argparse.ArgumentParser(description="Multi-Dictionary Entity Alignment Gate via TypeSafe System One")
    parser.add_argument("--hw1", type=str, default="пилосмок", help="First headword")
    parser.add_argument("--src1", type=str, default="СУМ-20", help="Source for first headword")
    parser.add_argument("--def1", type=str, default="Апарат для очищення від пилу та сміття.", help="Definition 1")
    parser.add_argument("--hw2", type=str, default="порохотяг", help="Second headword")
    parser.add_argument("--src2", type=str, default="Грінченко-1907", help="Source for second headword")
    parser.add_argument("--def2", type=str, default="Прилад, яким втягують пил.", help="Definition 2")
    parser.add_argument("--mock", action="store_true", help="Force mock System One evaluation")
    args = parser.parse_args()

    entry_a = DictionaryEntry(headword=args.hw1, source=args.src1, definition=args.def1, pos="noun", gender="m")
    entry_b = DictionaryEntry(headword=args.hw2, source=args.src2, definition=args.def2, pos="noun", gender="m")

    aligner = TypeSafeEntityAligner(mock=args.mock)
    result = aligner.align_entries(entry_a, entry_b)

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
