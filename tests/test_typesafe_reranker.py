"""Tests for TypeSafe System One Semantic Re-ranker."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.curriculum.typesafe_reranker import (
    RerankCandidate,
    TypeSafeReranker,
    rerank_textbook_candidates,
)


@pytest.fixture
def sample_candidates() -> list[RerankCandidate]:
    return [
        RerankCandidate(
            id="cand_toc",
            title="Календарне планування 6 клас",
            text="Зміст. Розділ 2. Дієслово. Способи дієслів. Минулий час дієслова. Стор. 45-50. Видавництво Освіта.",
            grade=6,
        ),
        RerankCandidate(
            id="cand_rule",
            title="Минулий час дієслів. Творення і відмінювання",
            text="Правило. Запам'ятайте: дієслова в минулому часі змінюються за родами (в однині) та числами. Зверніть увагу: суфікс -л- випадає у формах чоловічого роду після приголосних: ніс, біг (але несла, бігла). Таблиця відмінювання подана нижче. Наприклад: писав, писала, писали.",
            grade=6,
        ),
        RerankCandidate(
            id="cand_passing",
            title="Вправи на закріплення синтаксису",
            text="Складіть речення з поданими словами. Позначте головні члени речення. Вчора ми гуляли в парку.",
            grade=6,
        ),
        RerankCandidate(
            id="cand_irrelevant",
            title="Історія України 7 клас",
            text="Київська Русь за часів Ярослава Мудрого досягла найвищого розквіту. Було укладено збірник законів Руська Правда.",
            grade=7,
        ),
    ]


def test_reranker_heuristic_order(sample_candidates: list[RerankCandidate]) -> None:
    """Verify that pedagogical rule passage rises to Rank 1 over syllabus TOC and off-topic chunks."""
    reranker = TypeSafeReranker(api_key="")  # Force heuristic
    query = "минулий час дієслова: правила творення та закінчення"

    results = reranker.rerank(query, sample_candidates)

    assert len(results) >= 2
    # Pedagogical explanation must be Top 1
    top_hit = results[0]
    assert top_hit.candidate.id == "cand_rule"
    assert top_hit.clarity_level >= 2
    assert top_hit.relevance_score > 0.70
    assert top_hit.composite_score > 0.70
    assert top_hit.reranked_rank == 1

    # TOC and irrelevant should be ranked lower or pruned
    remaining_ids = [r.candidate.id for r in results[1:]]
    assert "cand_irrelevant" not in remaining_ids or results[-1].candidate.id == "cand_irrelevant"


def test_reranker_top_k(sample_candidates: list[RerankCandidate]) -> None:
    """Verify top_k parameter truncates output accurately."""
    reranker = TypeSafeReranker(api_key="")
    query = "дієслово"

    results = reranker.rerank(query, sample_candidates, top_k=2, drop_threshold=0.0)
    assert len(results) == 2
    assert results[0].reranked_rank == 1
    assert results[1].reranked_rank == 2


def test_reranker_drop_threshold() -> None:
    """Verify pruning of low-scoring noise candidates."""
    reranker = TypeSafeReranker(api_key="")
    candidates = [
        RerankCandidate(id="noise_1", text="Астрономія і фізика далеких галактик."),
        RerankCandidate(id="noise_2", text="Хімічні властивості металів і лугів."),
    ]
    query = "відмінювання іменників другої відміни"

    # All candidates are irrelevant, but reranker guarantees at least 1 returned item
    results = reranker.rerank(query, candidates, drop_threshold=0.50)
    assert len(results) == 1
    assert results[0].candidate.id in ("noise_1", "noise_2")


def test_reranker_to_dict(sample_candidates: list[RerankCandidate]) -> None:
    """Verify serialization structure."""
    reranker = TypeSafeReranker(api_key="")
    query = "минулий час"
    results = reranker.rerank(query, sample_candidates[:1])
    d = results[0].to_dict()

    assert "id" in d
    assert "title" in d
    assert "relevance_score" in d
    assert "clarity_level" in d
    assert "composite_score" in d
    assert "is_uncertain" in d
    assert "reranked_rank" in d
    assert "snippet" in d


def test_rerank_textbook_candidates_helper() -> None:
    """Verify integration helper accepting dict inputs."""
    raw_dicts = [
        {
            "chunk_id": "txt_101",
            "section_title": "Урок 14. Чергування звуків",
            "text": "Правило: у коренях дієслів чергуються звуки [о] - [а], наприклад: перемогти - перемагати.",
            "grade": 5,
        },
        {
            "chunk_id": "txt_102",
            "section_title": "Зміст підручника",
            "text": "Зміст. Чергування голосних. Вправи.",
            "grade": 5,
        },
    ]

    # With drop_threshold=0.0, both items are retained and ranked
    results_all = rerank_textbook_candidates(
        "чергування звуків у коренях дієслів", raw_dicts, top_k=2, drop_threshold=0.0
    )
    assert len(results_all) == 2
    assert results_all[0].candidate.id == "txt_101"
    assert results_all[0].composite_score > results_all[1].composite_score

    # With default drop_threshold=0.20, TOC noise is cleanly pruned
    results_pruned = rerank_textbook_candidates("чергування звуків у коренях дієслів", raw_dicts, top_k=2)
    assert len(results_pruned) == 1
    assert results_pruned[0].candidate.id == "txt_101"


@patch("urllib.request.urlopen")
def test_rerank_remote_mock(mock_urlopen: MagicMock) -> None:
    """Verify remote API payload handling and answer parsing."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(
        {
            "model": "jev-latest",
            "answers": {
                "teaches_concept": {"noul": 0.88, "confidence": 0.92},
                "clarity_level": {"score": 3.0, "confidence": 0.85},
            },
        }
    ).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    reranker = TypeSafeReranker(api_key="ts-test-key")
    candidate = RerankCandidate(id="test_remote", title="Дієвідміни", text="Правило відмінювання дієслів.")
    results = reranker.rerank("дієвідміни дієслів", [candidate])

    assert len(results) == 1
    assert results[0].candidate.id == "test_remote"
    assert results[0].relevance_score == 0.88
    assert results[0].clarity_level == 3
    assert not results[0].is_uncertain
    assert results[0].composite_score == pytest.approx(0.70 * 0.88 + 0.30 * 1.0, rel=1e-3)
