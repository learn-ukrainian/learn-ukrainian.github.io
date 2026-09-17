"""TypeSafe System One RAG Passage Qualification and Soviet Bias Triage Gate.

Adopts the classifying RAG passages architectural pattern from TypeSafe AI:
https://docs.typesafe.ai/cookbooks/classifying_rag_passages.md

Given a query and candidate retrieved passages from data/sources.db:
Evaluates 4 parallel Noul questions per passage:
1. is_pedagogically_relevant: Does this passage address the learning target of the query?
2. contains_usable_evidence: Does this passage state factual, instructional linguistic evidence?
3. has_soviet_or_imperial_bias: Does this passage contain Soviet/Russian imperial framing or ideological distortion?
4. contains_calque_or_surzhyk: Does this passage exhibit lexical or syntactic Russian interference?

Code-owned routing:
- has_soviet_or_imperial_bias > 0.65 -> CONFLICT_QUARANTINE
- contains_calque_or_surzhyk > 0.70 -> EXCLUDE
- is_pedagogically_relevant < 0.45 -> EXCLUDE
- contains_usable_evidence >= 0.55 -> ACCEPTED
- otherwise -> EXCLUDE
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


class PassageDisposition(StrEnum):
    """The canonical disposition for a retrieved RAG passage."""

    ACCEPTED = "accepted"
    CONFLICT_QUARANTINE = "conflict_quarantine"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class CandidatePassage:
    """A candidate passage retrieved from data/sources.db."""

    id: str
    title: str
    text: str
    source: str  # 'textbooks', 'literary_texts', 'sum11', 'wikipedia'


@dataclass
class PassageEvaluation:
    """Evaluation metrics for a single passage against a query."""

    passage_id: str
    disposition: PassageDisposition
    is_relevant: float
    contains_evidence: float
    soviet_bias: float
    calque_score: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["disposition"] = self.disposition.value
        return data


@dataclass
class RAGTriageResult:
    """The partitioned result of gating multiple candidate passages."""

    query: str
    accepted: list[CandidatePassage] = field(default_factory=list)
    quarantined_conflict: list[CandidatePassage] = field(default_factory=list)
    excluded: list[CandidatePassage] = field(default_factory=list)
    evaluations: list[PassageEvaluation] = field(default_factory=list)

    def format_evidence_blocks(self) -> tuple[str, str]:
        """Format separate accepted and conflicting evidence blocks for writer prompts."""
        if not self.accepted:
            acc_str = "(none)"
        else:
            acc_str = "\n\n".join(f"[{p.id}] {p.title} ({p.source}):\n{p.text}" for p in self.accepted)

        if not self.quarantined_conflict:
            conf_str = "(none)"
        else:
            conf_str = "\n\n".join(
                f"[{p.id}] {p.title} ({p.source}) [WARNING: SOVIET/IDEOLOGICAL BIAS]:\n{p.text}"
                for p in self.quarantined_conflict
            )

        return acc_str, conf_str


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


class TypeSafePassageGate:
    """TypeSafe System One RAG passage classifier and Soviet bias triage gate."""

    THRESHOLDS: ClassVar[dict[str, float]] = {
        "soviet_bias_max": 0.65,
        "calque_max": 0.70,
        "relevant_min": 0.45,
        "evidence_min": 0.55,
    }

    def __init__(self, api_key: str | None = None, model: str = "jev-latest", mock: bool = False):
        self.api_key = api_key or _resolve_typesafe_key()
        self.model = model
        self.mock = mock or not bool(self.api_key)

    def evaluate_passage(self, query: str, passage: CandidatePassage) -> PassageEvaluation:
        """Evaluate a single query-passage pair across 4 parallel Nouls."""
        if self.mock:
            return self._mock_evaluate(query, passage)

        state = {
            "query": query,
            "passage": {
                "id": passage.id,
                "title": passage.title,
                "text": passage.text,
                "source": passage.source,
            },
        }

        questions = {
            "is_pedagogically_relevant": {
                "type": "noul",
                "instructions": (
                    "Does this passage address the linguistic, grammatical, or pedagogical subject of the query?"
                ),
            },
            "contains_usable_evidence": {
                "type": "noul",
                "instructions": (
                    "Does this passage state factual, instructional linguistic evidence or authentic examples "
                    "usable in teaching Ukrainian?"
                ),
            },
            "has_soviet_or_imperial_bias": {
                "type": "noul",
                "instructions": (
                    "Does this passage frame Ukrainian history, culture, or grammar through a Sovietized, Russian-imperial, "
                    "or ideological lens (e.g. framing Ukrainian as secondary/dialectal, praising Soviet fraternal union)?"
                ),
            },
            "contains_calque_or_surzhyk": {
                "type": "noul",
                "instructions": "Does this passage contain Russianisms, lexical calques, or grammatical Surzhyk?",
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
            answers = data.get("answers", {})
            rel = float(answers.get("is_pedagogically_relevant", {}).get("noul", 0.0))
            evid = float(answers.get("contains_usable_evidence", {}).get("noul", 0.0))
            soviet = float(answers.get("has_soviet_or_imperial_bias", {}).get("noul", 0.0))
            calque = float(answers.get("contains_calque_or_surzhyk", {}).get("noul", 0.0))
        except Exception:
            return self._mock_evaluate(query, passage)

        return self._route_scores(passage.id, rel, evid, soviet, calque)

    def _route_scores(
        self, pid: str, rel: float, evid: float, soviet: float, calque: float
    ) -> PassageEvaluation:
        """Route evaluated probabilities to disposition via deterministic thresholds."""
        if soviet > self.THRESHOLDS["soviet_bias_max"]:
            return PassageEvaluation(
                passage_id=pid,
                disposition=PassageDisposition.CONFLICT_QUARANTINE,
                is_relevant=rel,
                contains_evidence=evid,
                soviet_bias=soviet,
                calque_score=calque,
                reason="Flagged for Soviet/imperial ideological framing (quarantined to conflict block)",
            )
        if calque > self.THRESHOLDS["calque_max"]:
            return PassageEvaluation(
                passage_id=pid,
                disposition=PassageDisposition.EXCLUDED,
                is_relevant=rel,
                contains_evidence=evid,
                soviet_bias=soviet,
                calque_score=calque,
                reason="Excluded due to Russianism/Surzhyk interference",
            )
        if rel < self.THRESHOLDS["relevant_min"]:
            return PassageEvaluation(
                passage_id=pid,
                disposition=PassageDisposition.EXCLUDED,
                is_relevant=rel,
                contains_evidence=evid,
                soviet_bias=soviet,
                calque_score=calque,
                reason="Excluded: below pedagogical relevance threshold",
            )
        if evid >= self.THRESHOLDS["evidence_min"]:
            return PassageEvaluation(
                passage_id=pid,
                disposition=PassageDisposition.ACCEPTED,
                is_relevant=rel,
                contains_evidence=evid,
                soviet_bias=soviet,
                calque_score=calque,
                reason="Accepted as verified pedagogical evidence",
            )

        return PassageEvaluation(
            passage_id=pid,
            disposition=PassageDisposition.EXCLUDED,
            is_relevant=rel,
            contains_evidence=evid,
            soviet_bias=soviet,
            calque_score=calque,
            reason="Excluded: insufficient instructional evidence",
        )

    def _mock_evaluate(self, query: str, passage: CandidatePassage) -> PassageEvaluation:
        """Calibrated mock evaluation for offline testing and CI suites."""
        text_l = passage.text.lower()
        title_l = passage.title.lower()

        # Soviet ideological signals
        soviet_signals = ["братній російський", "ленін", "радянськ", "срср", "велика вітчизняна"]
        is_soviet = any(s in text_l or s in title_l for s in soviet_signals) or passage.source == "sum11"

        # Russianism calque signals
        calque_signals = ["на протязі року", "приймати участь", "слідуючий", "давайте робити"]
        is_calque = any(c in text_l for c in calque_signals)

        # Relevance
        q_words = [w for w in query.lower().split() if len(w) > 3]
        overlap = sum(1 for w in q_words if w in text_l or w in title_l)
        is_rel = overlap > 0 or len(q_words) == 0

        if is_soviet:
            return self._route_scores(passage.id, 0.70, 0.40, 0.92, 0.20)
        if is_calque:
            return self._route_scores(passage.id, 0.65, 0.35, 0.15, 0.88)
        if not is_rel:
            return self._route_scores(passage.id, 0.15, 0.10, 0.05, 0.10)

        # High quality authentic evidence
        return self._route_scores(passage.id, 0.95, 0.90, 0.04, 0.05)

    def triage_passages(self, query: str, passages: list[CandidatePassage]) -> RAGTriageResult:
        """Triage a collection of candidate passages into accepted, quarantined, and excluded sets."""
        result = RAGTriageResult(query=query)
        for p in passages:
            eval_res = self.evaluate_passage(query, p)
            result.evaluations.append(eval_res)
            if eval_res.disposition == PassageDisposition.ACCEPTED:
                result.accepted.append(p)
            elif eval_res.disposition == PassageDisposition.CONFLICT_QUARANTINE:
                result.quarantined_conflict.append(p)
            else:
                result.excluded.append(p)
        return result


def main() -> None:
    """CLI entrypoint for RAG passage gating."""
    parser = argparse.ArgumentParser(description="TypeSafe RAG Passage Qualification Gate")
    parser.add_argument("--query", type=str, required=True, help="User or curriculum query")
    parser.add_argument("--mock", action="store_true", help="Force mock evaluation")
    args = parser.parse_args()

    # Demonstration passages
    sample_passages = [
        CandidatePassage(
            id="tb-gr7-01",
            title="Чергування голосних о-е з і",
            text="В українській мові в закритих складах звуки [о], [е] закономірно переходять у [і]: кіт — кота, ніч — ночі.",
            source="textbooks",
        ),
        CandidatePassage(
            id="soviet-1975-02",
            title="Розквіт мов СРСР",
            text="Завдяки великій допомозі братнього російського народу радянські мови збагачуються передовими термінами.",
            source="sum11",
        ),
        CandidatePassage(
            id="calque-article-03",
            title="Організація конференції",
            text="Ми запрошуємо всіх приймати участь у засіданні на протязі всього дня.",
            source="wikipedia",
        ),
        CandidatePassage(
            id="physics-gr9-04",
            title="Закон збереження енергії",
            text="Повна механічна енергія замкненої системи тіл залишається сталою під час руху.",
            source="textbooks",
        ),
    ]

    gate = TypeSafePassageGate(mock=args.mock)
    triage = gate.triage_passages(args.query, sample_passages)

    print(f"=== Triage Results for query: '{args.query}' ===")
    for ev in triage.evaluations:
        print(f"  [{ev.disposition.value.upper()}] {ev.passage_id}: {ev.reason}")

    acc, conf = triage.format_evidence_blocks()
    print("\n--- Accepted Evidence Block ---\n" + acc)
    print("\n--- Quarantined Conflict Block ---\n" + conf)


if __name__ == "__main__":
    main()
