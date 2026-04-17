"""Tests for tokenize_uk-based sentence splitting (#1318).

Verifies that the shared ``split_sentences`` utility in ``cleaners.py``
correctly handles Ukrainian abbreviations, guillemets, ellipsis, and
other edge cases that the previous naive regex splitters got wrong.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from audit.cleaners import split_sentences


class TestSplitSentences:
    """Core sentence splitting tests."""

    def test_simple_sentences(self):
        result = split_sentences("Це перше речення. А це друге. І третє!")
        assert len(result) == 3

    def test_empty_input(self):
        assert split_sentences("") == []
        assert split_sentences("   ") == []

    # -- Ukrainian abbreviation handling --

    def test_abbreviation_m_city(self):
        """м. (місто) before uppercase should NOT split the sentence."""
        result = split_sentences(
            "Хрещатик — центр м. Києва. Тут багато магазинів."
        )
        # "центр м. Києва." should be ONE sentence (not split at м.)
        assert any("м. Києва" in s for s in result), (
            f"м. Києва should stay in one sentence, got: {result}"
        )

    def test_abbreviation_r_year(self):
        """р. (рік) before lowercase should NOT split."""
        result = split_sentences(
            "У 2024 р. відбулися зміни. Це вплинуло на все."
        )
        assert len(result) == 2
        assert "2024 р. відбулися" in result[0]

    def test_abbreviation_s_selo(self):
        """с. (село) should not falsely split."""
        result = split_sentences("Він поїхав у с. Вишневе. Там гарно.")
        assert any("с. Вишневе" in s for s in result)

    # -- Guillemets and dialogue --

    def test_guillemet_sentence_boundary(self):
        """» at end of quoted title is a sentence boundary."""
        result = split_sentences(
            'Він читав «Тигролови». Це цікава книга.'
        )
        assert len(result) == 2

    def test_guillemet_mid_sentence(self):
        """» with em-dash continuation is NOT a boundary."""
        result = split_sentences(
            '«Це наша земля!» — сказав він. Потім пішов.'
        )
        # The first part with dialogue + attribution is one sentence
        assert len(result) == 2

    # -- Ellipsis --

    def test_ellipsis_as_boundary(self):
        result = split_sentences("Він думав... Потім вирішив діяти.")
        assert len(result) == 2

    # -- Multi-paragraph input --

    def test_paragraph_separation(self):
        """Blank lines between paragraphs are respected."""
        text = "Перше речення.\n\nДруге речення. Третє речення."
        result = split_sentences(text)
        assert len(result) == 3

    # -- Regression: old re.split(r'[.!?—:]') was WAY too aggressive --

    def test_colon_does_not_split(self):
        """Colons should NOT create sentence boundaries."""
        result = split_sentences("Ось приклад: це важливо. Далі буде.")
        assert len(result) == 2
        assert "Ось приклад: це важливо." in result[0]

    def test_em_dash_does_not_split(self):
        """Em dashes should NOT create sentence boundaries."""
        result = split_sentences(
            "Він — інженер. Вона — вчителька."
        )
        assert len(result) == 2
        assert "—" in result[0]

    # -- Edge cases surfaced by Codex review of #1318 --

    def test_title_case_abbreviation(self):
        """Sentence-initial 'Проф.' should match lowercase 'проф.' in ABBRS.

        Codex flagged this as a corpus pattern at b1/.../text-compression
        skeleton line 118. The case-insensitive ABBRS check keeps 'Проф.'
        attached to the following surname.
        """
        result = split_sentences(
            "Напр. у 2020 році сталось важливе. Проф. Іванов писав про це."
        )
        assert len(result) == 2
        assert "Проф. Іванов" in result[1]

    def test_address_abbreviations_chain(self):
        """B1 skeleton pattern: 'м. вул. Б. ст. м.' chain stays one sentence."""
        result = split_sentences(
            "Музей розміщено в м. Києві на вул. Б. Хмельницького, 11 "
            "(ст. м. «Театральна»)."
        )
        # Whole address must be one sentence; no fragment-per-abbreviation.
        assert len(result) == 1
        assert "вул. Б. Хмельницького" in result[0]
        assert "ст. м." in result[0]

    def test_bibliography_initials(self):
        """Surname + single-letter initial (Іванюк С.) must not split.

        The upstream ``not tok1.isupper()`` guard protects single-letter
        uppercase initials like 'С.' from firing a sentence break.
        """
        result = split_sentences(
            "Іванюк С. написав працю. Далі ця праця вплинула на інших."
        )
        # 'Іванюк С. написав працю.' should stay as a single sentence.
        assert any(s.startswith("Іванюк С.") and "написав" in s for s in result), (
            f"Initial 'С.' must stay attached, got: {result}"
        )

    def test_thousand_abbreviation(self):
        """'тис.' is in the local ABBRS extension and must not split."""
        result = split_sentences(
            "Це склало 500 тис. гривень. Уряд відзвітував."
        )
        assert len(result) == 2
        assert "500 тис. гривень" in result[0]

    def test_century_abbreviation(self):
        """'ст.' (століття) is in ABBRS — used in seminar/folk corpora."""
        result = split_sentences(
            "У XVI–XVIII ст. козацтво зміцніло. Далі настала інша доба."
        )
        assert len(result) == 2
        assert "XVI–XVIII ст." in result[0]

    def test_oblast_abbreviation(self):
        """'обл.' appears in B1 address corpora."""
        result = split_sentences(
            "Село у Київській обл. Тут живе багато людей."
        )
        # Must not split at 'обл.'
        assert any("Київській обл." in s for s in result), (
            f"'обл.' must stay attached, got: {result}"
        )
