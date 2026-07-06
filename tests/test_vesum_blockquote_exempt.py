from __future__ import annotations

from collections.abc import Callable

import pytest

from scripts.build import linear_pipeline


def _rejecting_verifier(
    missing_words: set[str],
    seen: list[list[str]],
) -> Callable[[list[str]], dict[str, list[dict[str, str]]]]:
    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        seen.append(words)
        return {
            word: ([] if word in missing_words else [{"lemma": word}])
            for word in words
        }

    return verify_words


def _disable_heritage_attestation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        linear_pipeline,
        "_resolve_folk_heritage_attested_missing",
        lambda missing_lc, unchecked_pairs: set(),
    )


def _gate(
    module_text: str,
    *,
    level: str,
    missing_words: set[str],
    monkeypatch: pytest.MonkeyPatch,
    activities: list[dict[str, object]] | None = None,
    vocabulary: list[dict[str, object]] | None = None,
    resources: list[dict[str, object]] | None = None,
) -> tuple[dict[str, object], list[list[str]]]:
    _disable_heritage_attestation(monkeypatch)
    seen: list[list[str]] = []
    gate = linear_pipeline._vesum_gate(
        module_text=module_text,
        activities=activities or [],
        vocabulary=vocabulary or [],
        resources=resources or [],
        verify_words_fn=_rejecting_verifier(missing_words, seen),
        level=level,
    )
    return gate, seen


def test_folk_attributed_blockquote_archaism_is_exempt_from_vesum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate, seen = _gate(
        """
Перед піснею.

> Ой у пір'єчку тиха вода.

*— Kupala [S1]*

Після пісні.
""",
        level="folk",
        missing_words={"пір'єчку"},
        monkeypatch=monkeypatch,
    )

    looked_up = {word for call in seen for word in call}
    assert gate["passed"] is True
    assert gate["missing"] == []
    assert "пір'єчку" not in looked_up


def test_folk_structured_primary_reading_is_exempt_from_vesum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate, seen = _gate(
        """
Перед читанням.

:::primary-reading{reading="demo"}
Параз бефель дань.

— Народна творчість, Wikisource; суспільне надбання.
:::

Після читання.
""",
        level="folk",
        missing_words={"параз", "бефель", "дань"},
        monkeypatch=monkeypatch,
    )

    looked_up = {word for call in seen for word in call}
    assert gate["passed"] is True
    assert gate["missing"] == []
    assert "параз" not in looked_up
    assert "бефель" not in looked_up
    assert "дань" not in looked_up


def test_folk_same_archaism_in_prose_still_fails_vesum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate, seen = _gate(
        "Перед піснею пір'єчку не вживаємо як навчальну прозу.",
        level="folk",
        missing_words={"пір'єчку"},
        monkeypatch=monkeypatch,
    )

    looked_up = {word for call in seen for word in call}
    assert gate["passed"] is False
    assert gate["missing"] == ["пір'єчку"]
    assert "пір'єчку" in looked_up


def test_folk_prose_russianism_still_fails_vesum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate, _seen = _gate(
        "Це протиріччя лишається прозовою помилкою.",
        level="folk",
        missing_words={"протиріччя"},
        monkeypatch=monkeypatch,
    )

    assert gate["passed"] is False
    assert gate["missing"] == ["протиріччя"]


def test_core_blockquote_non_vesum_word_still_fails_vesum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate, seen = _gate(
        """
Перед вправою.

> Тут фейкслово у цитатному рядку.

*— Захарійчук, Grade 1, p.24*
""",
        level="a1",
        missing_words={"фейкслово"},
        monkeypatch=monkeypatch,
    )

    looked_up = {word for call in seen for word in call}
    assert gate["passed"] is False
    assert gate["missing"] == ["фейкслово"]
    assert "фейкслово" in looked_up


def test_folk_uncited_blockquote_non_attested_form_still_fails_vesum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate, seen = _gate(
        """
Перед піснею.

> Тут городалька без джерела.
""",
        level="folk",
        missing_words={"городалька"},
        monkeypatch=monkeypatch,
    )

    looked_up = {word for call in seen for word in call}
    assert gate["passed"] is False
    assert gate["missing"] == ["городалька"]
    assert "городалька" in looked_up


def test_folk_attributed_fabricated_blockquote_is_rejected_by_quote_fidelity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("scripts.wiki.sources_db.search_literary", lambda keywords, limit=20: [])

    result = linear_pipeline._textbook_quote_fidelity_gate(
        """
> Тут городалька з вигаданим джерелом.

*— Kupala [S1]*
""",
        level="folk",
    )

    assert result["passed"] is False
    assert result["checked"] == 1
    assert result["violations"][0]["reason"] == "No match in literary corpus"


def test_blockquote_exemption_does_not_apply_to_activity_vocab_or_resource_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate, _seen = _gate(
        """
> Ой у пір'єчку тиха вода.

*— Kupala [S1]*
""",
        level="folk",
        missing_words={"пір'єчку"},
        monkeypatch=monkeypatch,
        activities=[{"id": "a1", "prompt": "У вправі пір'єчку лишається видимим."}],
        vocabulary=[{"lemma": "пір'єчку", "usage": "Не сховати пір'єчку у словнику."}],
        resources=[{"title": "Ресурс із пір'єчку", "notes": "notes are skipped"}],
    )

    assert gate["passed"] is False
    assert gate["missing"] == ["пір'єчку"]
