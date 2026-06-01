"""Tests for the seminar-quality language linter (scripts/validate/lint_seminar_quality.py).

Covers the two defect classes — Latin-in-Cyrillic and russianisms/calques — with an
emphasis on FALSE-POSITIVE guards: legitimate Latin (X-променів, STEM, IEU, Ems, Roman
numerals, URLs) and VESUM-codified words (інакомислення) must NOT be flagged, while the
proven defects (LIT-модулі, L2-студентам, hindsight-осуду, арест, постумно, prison-sense
термін) must be.
"""

import os
import sys

import pytest
import yaml

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))

from validate.lint_seminar_quality import (
    _scan_latin_in_cyrillic,
    lint_plan,
)

# ── Latin-in-Cyrillic: defects ───────────────────────────────────────────────

@pytest.mark.parametrize("token", ["LIT-модулі", "L2-студентам", "hindsight-осуду"])
def test_latin_abbreviation_glued_to_cyrillic_is_flagged(token):
    hits = _scan_latin_in_cyrillic(f"текст {token} текст")
    assert hits, f"{token} should be flagged"
    assert hits[0][1] == "high"


@pytest.mark.parametrize("token", ["Cлово", "мистецтвoм", "Оспiщев"])
def test_intra_word_homoglyph_is_flagged(token):
    # These mix Latin + Cyrillic *inside* one word (homoglyph substitution).
    hits = _scan_latin_in_cyrillic(token)
    assert hits, f"{token} homoglyph should be flagged"
    assert hits[0][1] == "high"


# ── Latin-in-Cyrillic: legitimate (must NOT flag) ────────────────────────────

@pytest.mark.parametrize("text", [
    "дослідження X-променів у фізиці",
    "осі Y та координати",
    "STEM-освіта в школах",
    "за даними IEU та ESU",
    "Ems-указ 1876 року",
    "XIX-столітні джерела",
    "у XVIII ст. та на початку XX століття",
    "посилання uk.wikipedia.org/wiki/Драй-Хмара на статтю",
    "https://esu.com.ua/article про постать",
])
def test_legitimate_latin_is_not_flagged(text):
    assert _scan_latin_in_cyrillic(text) == [], f"false positive on: {text}"


# ── End-to-end plan linting via lint_plan ────────────────────────────────────

def _lint_dict(tmp_path, plan: dict) -> list[tuple[str, str, str]]:
    path = tmp_path / "subject.yaml"
    path.write_text(yaml.dump(plan, allow_unicode=True), encoding="utf-8")
    return [(f.rule, f.text, f.severity) for f in lint_plan(path)]


def _rules(findings) -> set[str]:
    return {f[0] for f in findings}


def test_arest_russianism_flagged_high(tmp_path):
    findings = _lint_dict(tmp_path, {
        "title": "Тест",
        "content_outline": [{"section": "Біографія",
                             "points": ["Арешт стався 1948 року"]}],  # correct form
    })
    assert "арест" not in _rules(findings), "«арешт» (correct) must not be flagged"

    findings = _lint_dict(tmp_path, {
        "title": "Тест",
        "content_outline": [{"section": "Біографія",
                             "points": ["Арест 29 січня 1948 року"]}],  # russianism
    })
    assert ("арест", "Арест", "high") in findings


def test_prefixed_arest_is_flagged_but_correct_form_is_not(tmp_path):
    # Prefixed russianism «заарестовано» (not in VESUM) must be caught...
    flagged = _lint_dict(tmp_path, {
        "content_outline": [{"section": "Репресії",
                             "points": ["Його було заарестовано в 1937 році"]}],
    })
    assert "арест" in _rules(flagged)
    # ...while the correct «заарештовано» (with ш) and медичне «парестезія» are NOT.
    clean = _lint_dict(tmp_path, {
        "content_outline": [{"section": "Репресії",
                             "points": ["Його заарештовано 1937; парестезія була симптомом"]}],
    })
    assert "арест" not in _rules(clean)


def test_vlast_russian_plural_is_flagged(tmp_path):
    flagged = _lint_dict(tmp_path, {
        "content_outline": [{"section": "Війна",
                             "points": ["Депортований нацистськими властями до Берліна"]}],
    })
    assert "власті" in _rules(flagged)
    # Legitimate «властивість»/«властивий» and Ukrainian «владами» must NOT be flagged.
    clean = _lint_dict(tmp_path, {
        "content_outline": [{"section": "Стиль",
                             "points": ["Властивий йому стиль і художня властивість образів"]}],
    })
    assert "власті" not in _rules(clean)


def test_postum_russianism_flagged(tmp_path):
    findings = _lint_dict(tmp_path, {
        "content_outline": [{"section": "Спадщина",
                             "points": ["Постумно реабілітований у 1960-х"]}],
    })
    assert "постум" in _rules(findings)


def test_inakomyslennia_is_not_flagged_but_inakomysliach_is(tmp_path):
    # «інакомислення» — VESUM-codified abstract noun, must NOT be flagged.
    findings = _lint_dict(tmp_path, {
        "content_outline": [{"section": "Контекст",
                             "points": ["Релігійне інакомислення доби застою"]}],
    })
    assert "інакомисляч" not in _rules(findings)

    # «інакомисляч» — non-standard person-form calque, advisory flag.
    findings = _lint_dict(tmp_path, {
        "content_outline": [{"section": "Контекст",
                             "points": ["Він був інакомислячим митцем"]}],
    })
    assert "інакомисляч" in _rules(findings)


def test_termin_prison_sense_needs_context(tmp_path):
    # Prison collocation → flag.
    flagged = _lint_dict(tmp_path, {
        "content_outline": [{"section": "Покарання",
                             "points": ["Відбував термін у таборі суворого режиму"]}],
    })
    assert "термін_строк" in _rules(flagged)

    # «термін» as deadline / terminology → no imprisonment context → no flag.
    clean = _lint_dict(tmp_path, {
        "content_outline": [{"section": "Наука",
                             "points": ["Запровадив новий науковий термін у мовознавстві"]}],
    })
    assert "термін_строк" not in _rules(clean)


def test_identifier_and_citation_fields_are_skipped(tmp_path):
    # connects_to / slug / references must not be scanned even if they contain
    # Latin-Cyrillic mixes (slugs) or URLs with Cyrillic article titles.
    findings = _lint_dict(tmp_path, {
        "slug": "viktor-domontovych",
        "module": "bio-201",
        "connects_to": ["bio-mykola-zerov", "lit-neoclassicism"],
        "references": [{"title": "Драй-Хмара", "path": "uk.wikipedia.org/wiki/Драй-Хмара"}],
        "content_outline": [{"section": "Огляд", "points": ["Чистий український текст."]}],
    })
    assert findings == [], f"identifier/citation fields should be skipped, got {findings}"


def test_clean_plan_has_no_findings(tmp_path):
    findings = _lint_dict(tmp_path, {
        "title": "Михайло Драй-Хмара",
        "content_outline": [
            {"section": "Розминка", "points": ["Поет-неокласик та перекладач."]},
            {"section": "Репресії", "points": ["Заарештований 1935 року; помер на Колимі."]},
        ],
        "activity_hints": [{"focus": "Дискусія про неокласицизм", "type": "debate"}],
    })
    assert findings == []
