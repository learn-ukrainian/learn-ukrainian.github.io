"""Unit tests for TypeSafe RAG Passage Qualification and Soviet Bias Triage Gate."""

from __future__ import annotations

from scripts.rag.typesafe_passage_gate import (
    CandidatePassage,
    PassageDisposition,
    TypeSafePassageGate,
)


def test_pedagogical_evidence_accepted():
    """Verify high-quality textbook passage is accepted as verified evidence."""
    gate = TypeSafePassageGate(mock=True)
    passage = CandidatePassage(
        id="gr7-phonetics-01",
        title="Чергування голосних о, е з і",
        text="В українській мові в закритих складах звуки [о], [е] переходять у [і]: кіт — кота, ніч — ночі.",
        source="textbooks",
    )

    result = gate.evaluate_passage("Поясніть чергування голосних звуків", passage)
    assert result.disposition == PassageDisposition.ACCEPTED
    assert result.is_relevant >= 0.50
    assert result.contains_evidence >= 0.55
    assert result.soviet_bias < 0.20
    assert result.calque_score < 0.20


def test_soviet_ideological_framing_quarantined_to_conflict():
    """Verify Sovietized framing is strictly quarantined into conflict/warning block."""
    gate = TypeSafePassageGate(mock=True)
    passage = CandidatePassage(
        id="sum11-ideology-02",
        title="Розвиток радянської мови",
        text="Завдяки невтомній турботі комуністичної партії та братньому російському народу мова розквітає.",
        source="sum11",
    )

    result = gate.evaluate_passage("Розвиток лексики в 20 столітті", passage)
    assert result.disposition == PassageDisposition.CONFLICT_QUARANTINE
    assert result.soviet_bias > 0.65
    assert "Soviet/imperial" in result.reason


def test_calque_surzhyk_excluded():
    """Verify passage carrying Russianisms or syntactic calques is excluded."""
    gate = TypeSafePassageGate(mock=True)
    passage = CandidatePassage(
        id="wiki-calque-03",
        title="Оголошення",
        text="Студенти повинні приймати участь у виборах на протязі всього дня.",
        source="wikipedia",
    )

    result = gate.evaluate_passage("Студентське самоврядування", passage)
    assert result.disposition == PassageDisposition.EXCLUDED
    assert result.calque_score > 0.70
    assert "Russianism/Surzhyk" in result.reason


def test_irrelevant_passage_excluded():
    """Verify off-topic passage falls below relevance threshold and is dropped."""
    gate = TypeSafePassageGate(mock=True)
    passage = CandidatePassage(
        id="physics-04",
        title="Закон Архімеда",
        text="На тіло, занурене в рідину або газ, діє виштовхувальна сила.",
        source="textbooks",
    )

    result = gate.evaluate_passage("Відмінювання іменників другої відміни", passage)
    assert result.disposition == PassageDisposition.EXCLUDED
    assert result.is_relevant < 0.45


def test_triage_and_evidence_block_formatting():
    """Verify batch triage cleanly separates accepted evidence from quarantined conflict text."""
    gate = TypeSafePassageGate(mock=True)
    passages = [
        CandidatePassage(
            id="p1",
            title="Граматика",
            text="Іменники чоловічого роду з основою на приголосний належать до другої відміни.",
            source="textbooks",
        ),
        CandidatePassage(
            id="p2",
            title="Радянська лексика",
            text="Спільна термінологія народів СРСР зближує культури.",
            source="sum11",
        ),
        CandidatePassage(
            id="p3",
            title="Астрономія",
            text="Земля обертається навколо Сонця за 365 днів.",
            source="textbooks",
        ),
    ]

    triage = gate.triage_passages("Правила другої відміни", passages)

    assert len(triage.accepted) == 1
    assert triage.accepted[0].id == "p1"
    assert len(triage.quarantined_conflict) == 1
    assert triage.quarantined_conflict[0].id == "p2"
    assert len(triage.excluded) == 1
    assert triage.excluded[0].id == "p3"

    acc_block, conf_block = triage.format_evidence_blocks()
    assert "[p1]" in acc_block
    assert "[p2]" in conf_block
    assert "SOVIET/IDEOLOGICAL BIAS" in conf_block


def test_live_api_failure_routes_to_curator_review(monkeypatch):
    """Live API errors must not silently fall back to the keyword mock."""
    gate = TypeSafePassageGate(api_key="test-key", mock=False)
    passage = CandidatePassage(
        id="api-fail-01",
        title="Чергування",
        text="В українській мові в закритих складах звуки [о], [е] переходять у [і].",
        source="textbooks",
    )

    def _boom(*_a, **_k):
        raise TimeoutError("simulated typesafe outage")

    monkeypatch.setattr("urllib.request.urlopen", _boom)
    result = gate.evaluate_passage("Чергування голосних", passage)
    assert result.disposition == PassageDisposition.CURATOR_REVIEW
    assert result.is_relevant == 0.0
    assert "Live TypeSafe API failure" in result.reason
