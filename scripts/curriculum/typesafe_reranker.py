"""TypeSafe System One Semantic Re-ranker for Ukrainian Curriculum and Sources.

Adopts the Re-ranking architectural pattern from TypeSafe AI:
https://docs.typesafe.ai/cookbooks/rerank_typesafe.md

Given an educational query (lesson objective or linguistic concept) and a shortlist
of candidate chunks retrieved via fast search (SQLite FTS5 from data/sources.db),
TypeSafe System One scores each candidate on pedagogical relevance and instructional clarity.

Candidates are sorted by calibrated score, bubbling up authoritative textbook explanations
and authentic illustrative examples while pruning syllabus noise and off-topic mentions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RerankCandidate:
    """A candidate passage retrieved from fast search (e.g., FTS5)."""

    id: str
    text: str
    title: str = ""
    grade: int | None = None
    author: str = ""
    source_file: str = ""
    metadata: dict[str, Any] | None = None


@dataclass
class RerankResult:
    """A candidate evaluated and scored by the re-ranker."""

    candidate: RerankCandidate
    relevance_score: float  # P(teaches_concept) from Noul, in [0.0, 1.0]
    clarity_level: int  # 0 to 3 from Score
    composite_score: float  # Combined ranking metric in [0.0, 1.0]
    is_uncertain: bool  # True if confidence / top probability was low (< 0.60)
    original_rank: int
    reranked_rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.candidate.id,
            "title": self.candidate.title,
            "grade": self.candidate.grade,
            "relevance_score": round(self.relevance_score, 4),
            "clarity_level": self.clarity_level,
            "composite_score": round(self.composite_score, 4),
            "is_uncertain": self.is_uncertain,
            "original_rank": self.original_rank,
            "reranked_rank": self.reranked_rank,
            "snippet": self.candidate.text[:200] + ("..." if len(self.candidate.text) > 200 else ""),
        }


def _resolve_typesafe_key() -> str:
    """Resolve TypeSafe API key from environment or user home secrets."""
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key

    key_files = [
        Path.home() / ".config" / "typesafe" / "key",
        Path.home() / ".typesafe_api_key",
        Path.home() / ".gemini" / "antigravity-cli" / "typesafe_api_key",
    ]
    for p in key_files:
        if p.is_file():
            content = p.read_text(encoding="utf-8").strip()
            if content:
                return content
    return ""


class TypeSafeReranker:
    """Semantic re-ranker backed by TypeSafe System One (Jev)."""

    QUESTIONS: ClassVar[dict[str, Any]] = {
        "teaches_concept": {
            "type": "noul",
            "instructions": "Does this textbook excerpt directly explain, teach, or provide authentic instructional models for the queried language topic?",
            "criteria": {
                "true": "The passage clearly teaches the grammar rule, morphological paradigm, syntax, or provides explicit illustrative examples of the target concept.",
                "false": "The passage only mentions the keyword in passing, is administrative/curriculum syllabus metadata, table of contents, or is unrelated to teaching the concept.",
            },
        },
        "clarity_level": {
            "type": "score",
            "instructions": "Rate the pedagogical instructional utility of this passage for a learner curriculum.",
            "levels": {
                "0": "No instructional value: metadata, syllabus list, or noise.",
                "1": "Incidental or tangential mention with minimal instructional context.",
                "2": "Clear, contextual textbook sentences illustrating the concept in use.",
                "3": "Exemplary instructional explanation with explicit rules, paradigms, or canonical definitions.",
            },
        },
    }

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.typesafe.ai"):
        self.api_key = api_key or _resolve_typesafe_key()
        self.base_url = base_url.rstrip("/")

    def rerank(
        self,
        query: str,
        candidates: list[RerankCandidate],
        *,
        top_k: int | None = None,
        drop_threshold: float = 0.20,
    ) -> list[RerankResult]:
        """Re-rank candidate passages against the query.

        Args:
            query: The pedagogical objective or grammatical search target.
            candidates: List of candidate passages from fast search.
            top_k: Max number of top results to return (None for all).
            drop_threshold: Minimum composite score required to avoid being pruned.

        Returns:
            List of RerankResult sorted by composite score descending.
        """
        if not candidates:
            return []

        results = self._rerank_remote(query, candidates) if self.api_key else self._rerank_heuristic(query, candidates)

        # Sort by composite score descending, original rank as secondary tie-breaker
        results.sort(key=lambda r: (r.composite_score, -r.original_rank), reverse=True)

        # Assign reranked ranks
        for idx, res in enumerate(results, start=1):
            res.reranked_rank = idx

        # Filter dropped items if threshold specified
        if drop_threshold > 0.0:
            filtered = [r for r in results if r.composite_score >= drop_threshold]
            # If everything was below threshold, keep at least the single best result
            if not filtered and results:
                filtered = [results[0]]
            results = filtered

        if top_k is not None and top_k > 0:
            results = results[:top_k]

        return results

    def _rerank_remote(self, query: str, candidates: list[RerankCandidate]) -> list[RerankResult]:
        """Execute remote TypeSafe System One calls for each candidate."""
        results: list[RerankResult] = []
        url = f"{self.base_url}/v1/system_one"

        for idx, cand in enumerate(candidates):
            state = {
                "query": query,
                "candidate": {
                    "title": cand.title,
                    "grade": cand.grade,
                    "text": cand.text,
                },
            }

            payload = {
                "model": "jev-latest",
                "state": state,
                "questions": self.QUESTIONS,
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "learn-ukrainian-reranker/1.0",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    answers = data.get("answers", {})

                    relevance = float(answers.get("teaches_concept", {}).get("noul", 0.5))
                    clarity_raw = answers.get("clarity_level", {}).get("score", 1.0)
                    clarity = round(clarity_raw)

                    conf_rel = float(answers.get("teaches_concept", {}).get("confidence", 1.0))
                    conf_clar = float(answers.get("clarity_level", {}).get("confidence", 1.0))
                    is_uncertain = min(conf_rel, conf_clar) < 0.60

                    composite = self._calculate_composite(relevance, clarity)

                    results.append(
                        RerankResult(
                            candidate=cand,
                            relevance_score=relevance,
                            clarity_level=clarity,
                            composite_score=composite,
                            is_uncertain=is_uncertain,
                            original_rank=idx + 1,
                        )
                    )
            except Exception:
                # Fall back to heuristic for this candidate if network/API fails
                fallback_res = self._score_single_heuristic(query, cand, idx + 1)
                results.append(fallback_res)

        return results

    def _rerank_heuristic(self, query: str, candidates: list[RerankCandidate]) -> list[RerankResult]:
        """Offline deterministic heuristic for testing and fallback environments."""
        return [self._score_single_heuristic(query, cand, idx + 1) for idx, cand in enumerate(candidates)]

    def _score_single_heuristic(self, query: str, cand: RerankCandidate, rank: int) -> RerankResult:
        """Deterministic lexical/pedagogical heuristic for offline test parity."""
        q_tokens = {tok.lower() for tok in re.findall(r"[\w'’ʼ-]+", query) if len(tok) > 2}
        text_lower = cand.text.lower()
        title_lower = cand.title.lower()

        # Check for syllabus/noise markers
        noise_markers = ["зміст", "календарне планування", "програма курсу", "видавництво", "підручник для"]
        is_noise = any(m in text_lower or m in title_lower for m in noise_markers)

        # Check for instructional markers
        rule_markers = [
            "правило",
            "запам'ятайте",
            "зверніть увагу",
            "парадигма",
            "таблиця",
            "відмінювання",
            "наприклад",
            "вправа",
        ]
        instructional_hits = sum(1 for m in rule_markers if m in text_lower)

        # Token overlap ratio
        overlap = sum(1 for t in q_tokens if t in text_lower or t in title_lower)
        overlap_ratio = overlap / max(1, len(q_tokens))

        if is_noise and overlap_ratio < 0.5:
            relevance = 0.10
            clarity = 0
            is_uncertain = False
        elif instructional_hits >= 2 and overlap_ratio >= 0.5:
            relevance = min(0.95, 0.65 + 0.15 * overlap_ratio + 0.05 * instructional_hits)
            clarity = 3
            is_uncertain = False
        elif instructional_hits >= 1 and overlap_ratio >= 0.3:
            relevance = min(0.85, 0.50 + 0.20 * overlap_ratio)
            clarity = 2
            is_uncertain = False
        elif overlap_ratio > 0:
            relevance = 0.30 + 0.25 * overlap_ratio
            clarity = 1
            is_uncertain = True
        else:
            relevance = 0.05
            clarity = 0
            is_uncertain = False

        composite = self._calculate_composite(relevance, clarity)

        return RerankResult(
            candidate=cand,
            relevance_score=relevance,
            clarity_level=clarity,
            composite_score=composite,
            is_uncertain=is_uncertain,
            original_rank=rank,
        )

    @staticmethod
    def _calculate_composite(relevance: float, clarity: int) -> float:
        """Combine P(teaches) and clarity level (0-3) into a single metric in [0.0, 1.0]."""
        # Clarity level 0-3 scales from 0.25 to 1.0
        clarity_weight = (clarity + 1.0) / 4.0
        # 70% weight to direct relevance, 30% to instructional clarity
        score = (0.70 * relevance) + (0.30 * clarity_weight)
        return min(1.0, max(0.0, score))


def rerank_textbook_candidates(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    top_k: int | None = 10,
    drop_threshold: float = 0.20,
    reranker: TypeSafeReranker | None = None,
) -> list[RerankResult]:
    """Helper to re-rank candidate dicts returned from SQLite FTS5 / sources_db queries."""
    model = reranker or TypeSafeReranker()
    parsed_candidates = [
        RerankCandidate(
            id=str(c.get("chunk_id") or c.get("id") or f"c_{i}"),
            text=c.get("text", ""),
            title=c.get("title") or c.get("section_title") or "",
            grade=c.get("grade"),
            author=c.get("author") or c.get("author_uk") or "",
            source_file=c.get("source_file", ""),
            metadata=c,
        )
        for i, c in enumerate(candidates)
    ]
    return model.rerank(query, parsed_candidates, top_k=top_k, drop_threshold=drop_threshold)


def main() -> None:
    parser = argparse.ArgumentParser(description="TypeSafe System One Semantic Re-ranker for Ukrainian text")
    parser.add_argument("--query", "-q", required=True, help="Target search concept or lesson objective")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of top candidates to display")
    parser.add_argument("--drop-threshold", type=float, default=0.20, help="Drop threshold for low-relevance noise")
    args = parser.parse_args()

    reranker = TypeSafeReranker()
    print(f"TypeSafe Reranker initialized (Remote API: {'Active' if reranker.api_key else 'Heuristic offline'})")
    print(f"Query: {args.query}\n")


if __name__ == "__main__":
    main()
