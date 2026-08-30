"""Tests for verb pedagogy enrichment (#7471): stems, government, aspect,
aspect_partner. Fixture-first -- no live sources.db or VESUM DB required in CI.

Two enrichment passes are covered:
1. ``scripts.lexicon.ohoiko_quality_enrichment``: Anna Ohoiko's 500-verbs pages
   (stems, government, and the headword-pair aspect_partner cross-link).
2. ``scripts.lexicon.verb_pedagogy_vesum_aspect``: VESUM aspect fill across
   every Atlas verb, plus the dictionary-cross-reference partner fallback.
"""

from __future__ import annotations

from typing import Any

from scripts.lexicon import enrich_manifest as enrich_manifest_module
from scripts.lexicon import verb_pedagogy_vesum_aspect as vpa
from scripts.lexicon.ohoiko_quality_enrichment import (
    _extract_500_verbs_government,
    _extract_500_verbs_stems,
    apply_ohoiko_quality_enrichment,
    enrich_entry_with_verb_pedagogy,
    parse_500_verbs_chunk,
)

# ---------------------------------------------------------------------------
# Fixtures: realistic 500-verbs page shapes (mirrors SAMPLE_500_CHUNKS in
# tests/test_anna_quality_ohoiko_examples.py; kept local so this file's
# assertions don't depend on that file's fixture data).
# ---------------------------------------------------------------------------

V0001_TEXT = (
    "аналізува́ти | проаналізува́ти                                        Present / Future Stems: аналізу- | проаналізу-\n"
    "to analyze\n"
    "ОСОБА                          НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
    "ТЕПЕРІШНІЙ ЧАС ― PRESENT TENSE\n"
    "я                   аналізу́ю\n"
    "+ accusative:\n"
    "Ми ана́лізуємо результа́ти.                                      We are analyzing the results.\n"
)

# Entry 383 shape: stems label appears BEFORE the headword pair on the line.
V0383_TEXT = (
    "Present / Future Stems: прош-/прос- | попрош-/попрос-                                         проси́ти | попроси́ти\n"
    "Conjugation: 2nd (-ять)                                                                                   to ask (for); to request\n"
    "ОСОБА                            НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
    "я                   прошу́\n"
    "+ accusative + infinitive:\n"
    "Він про́сить допомо́ги.                                          He asks for help.\n"
)

# Entry 277 shape: OCR combining-accent wrap folds the headword continuation
# and the stems label onto the same merged line (#7457 shape).
V0277_TEXT = (
    "об’єд\n"
    "to unite sth/sb [to come together, to unite]\n"
    "́ нувати [ся] | об’єдна́ти [ся]                                                Present / Future Stems: об’єдну- | об’єдна-\n"
    "ОСОБА                                    НЕДОКОНАНИЙ ВИД                                              ДОКОНАНИЙ ВИД\n"
    "я                       об’єд́ ную [ся]\n"
    "+ accusative:\n"
    "Ми об’єдна́ли зуси́лля.                                          We joined our efforts.\n"
)

# Multi-perfective headword: two perfective legs off one imperfective.
V0018_TEXT = (
    "будува́ти | збудува́ти, побудува́ти                                                  Present / Future Stems: буду- | збуду-\n"
    "to build\n"
    "ОСОБА                           НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
    "я                   буду́ю\n"
    "+ accusative:\n"
    "Робітники́ будую́ть но́вий міст.                                  Workers are building a new bridge.\n"
)

# Two-aspect verb: both legs of the headword pair are the same lemma.
V0002_TEXT = (
    "атакува́ти | атакува́ти                                                                 Present / Future Stems: атаку- | атаку-\n"
    "to attack, to assault\n"
    "ОСОБА                      НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
    "я                      атаку́ю\n"
    "+ accusative:\n"
    "Воро́г атаку́є.                                                  The enemy attacks.\n"
)

# Reflexive government (``-ся + до + genitive:``), no accusative object.
V0365_TEXT = (
    "приєд\n"
    "to add, to attach, to join sth [to join]\n"
    "́ нувати [ся] | приєдна́ти [ся]                                                Present / Future Stems: приєдну- | приєдна-\n"
    "ОСОБА                                     НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
    "я                         приєд́ ную [ся]\n"
    "-ся + до + genitive:\n"
    "Він приєдна́вся до на́шої кома́нди.                               He joined our team.\n"
)


# ---------------------------------------------------------------------------
# Unit tests: _extract_500_verbs_stems
# ---------------------------------------------------------------------------


def test_extract_stems_common_shape() -> None:
    lines = [line for line in V0001_TEXT.splitlines() if line.strip()]
    assert _extract_500_verbs_stems(lines) == ["аналізу-", "проаналізу-"]


def test_extract_stems_label_before_headword() -> None:
    lines = [line for line in V0383_TEXT.splitlines() if line.strip()]
    assert _extract_500_verbs_stems(lines) == ["прош-/прос-", "попрош-/попрос-"]


def test_extract_stems_ocr_merged_line() -> None:
    lines = [line for line in V0277_TEXT.splitlines() if line.strip()]
    assert _extract_500_verbs_stems(lines) == ["об’єдну-", "об’єдна-"]


def test_extract_stems_absent_returns_none() -> None:
    assert _extract_500_verbs_stems(["якийсь рядок без міток", "ще один"]) is None


# ---------------------------------------------------------------------------
# Unit tests: _extract_500_verbs_government
# ---------------------------------------------------------------------------


def test_extract_government_accusative() -> None:
    lines = [line for line in V0001_TEXT.splitlines() if line.strip()]
    assert _extract_500_verbs_government(lines) == ["+ accusative"]


def test_extract_government_accusative_plus_infinitive() -> None:
    lines = [line for line in V0383_TEXT.splitlines() if line.strip()]
    assert _extract_500_verbs_government(lines) == ["+ accusative + infinitive"]


def test_extract_government_reflexive_genitive() -> None:
    lines = [line for line in V0365_TEXT.splitlines() if line.strip()]
    assert _extract_500_verbs_government(lines) == ["-ся + до + genitive"]


def test_extract_government_none_when_absent() -> None:
    lines = ["ОСОБА НЕДОКОНАНИЙ ВИД", "я аналізую", "+ 5:"]
    assert _extract_500_verbs_government(lines) == []


def test_extract_government_dedupes_repeated_labels() -> None:
    lines = ["+ accusative:", "Якийсь приклад.", "+ accusative:", "Ще приклад."]
    assert _extract_500_verbs_government(lines) == ["+ accusative"]


# ---------------------------------------------------------------------------
# parse_500_verbs_chunk: stems/government land on ParsedOhoikoEntry
# ---------------------------------------------------------------------------


def test_parse_500_verbs_chunk_populates_stems_and_government() -> None:
    parsed = parse_500_verbs_chunk("anna-ohoiko-500-verbs_e0001", "аналізува́ти | проаналізува́ти", V0001_TEXT)
    assert parsed.stems == ["аналізу-", "проаналізу-"]
    assert parsed.government == ["+ accusative"]


def test_parse_500_verbs_chunk_ocr_wrapped_entry_stems() -> None:
    parsed = parse_500_verbs_chunk("anna-ohoiko-500-verbs_e0277", "об’єд", V0277_TEXT)
    assert parsed.lemmas == ["об’єднувати", "об’єднуватися", "об’єднати", "об’єднатися"]
    assert parsed.stems == ["об’єдну-", "об’єдна-"]
    assert parsed.government == ["+ accusative"]


def test_parse_500_verbs_chunk_1000_words_never_sets_pedagogy() -> None:
    from scripts.lexicon.ohoiko_quality_enrichment import parse_1000_words_chunk

    parsed = parse_1000_words_chunk(
        "anna-ohoiko-1000-words-2nd-ed_e0003",
        "авто́бус",
        "3. авто́бус  bus\nСашко́ ї́здить в шко́лу авто́бусом.               Sashko goes to school by bus.\n",
    )
    assert parsed.stems is None
    assert parsed.government is None


# ---------------------------------------------------------------------------
# enrich_entry_with_verb_pedagogy
# ---------------------------------------------------------------------------


def test_enrich_entry_with_verb_pedagogy_writes_stems_and_government() -> None:
    entry: dict[str, Any] = {"lemma": "аналізувати", "enrichment": {"sources": ["VESUM"]}}
    changed = enrich_entry_with_verb_pedagogy(
        entry,
        stems=["аналізу-", "проаналізу-"],
        government=["+ accusative"],
        locator="ohoiko-500-verbs entry 1",
    )
    assert changed is True
    vp = entry["enrichment"]["verb_pedagogy"]
    assert vp["stems"] == {
        "present_future": ["аналізу-", "проаналізу-"],
        "source": "Anna Ohoiko",
        "locator": "ohoiko-500-verbs entry 1",
    }
    assert vp["government"] == [
        {"label": "+ accusative", "source": "Anna Ohoiko", "locator": "ohoiko-500-verbs entry 1"}
    ]
    assert "Anna Ohoiko" in entry["enrichment"]["sources"]
    assert "VESUM" in entry["enrichment"]["sources"]


def test_enrich_entry_with_verb_pedagogy_never_overwrites_aspect_partner() -> None:
    entry: dict[str, Any] = {
        "lemma": "аналізувати",
        "enrichment": {"verb_pedagogy": {"aspect_partner": {"lemma": "проаналізувати", "source": "Anna Ohoiko"}}},
    }
    changed = enrich_entry_with_verb_pedagogy(
        entry, aspect_partner={"lemma": "щось інше", "source": "dictionary cross-reference"}
    )
    assert changed is False
    assert entry["enrichment"]["verb_pedagogy"]["aspect_partner"]["lemma"] == "проаналізувати"


def test_enrich_entry_with_verb_pedagogy_no_fields_is_noop() -> None:
    entry: dict[str, Any] = {"lemma": "аналізувати"}
    assert enrich_entry_with_verb_pedagogy(entry) is False
    assert entry.get("enrichment", {}).get("verb_pedagogy") == {}


# ---------------------------------------------------------------------------
# apply_ohoiko_quality_enrichment: end-to-end aspect_partner cross-linking
# ---------------------------------------------------------------------------


def _stub_manifest(lemmas: list[str]) -> dict[str, Any]:
    return {
        "entries": [
            {"lemma": lemma, "url_slug": lemma, "pos": "verb", "enrichment": None} for lemma in lemmas
        ]
    }


def test_apply_ohoiko_quality_enrichment_cross_links_aspect_pair() -> None:
    manifest = _stub_manifest(["аналізувати", "проаналізувати"])
    parsed_500 = [parse_500_verbs_chunk("anna-ohoiko-500-verbs_e0001", "x", V0001_TEXT)]
    stats = apply_ohoiko_quality_enrichment(manifest, parsed_1000=[], parsed_500=parsed_500)

    by_lemma = {e["lemma"]: e for e in manifest["entries"]}
    imperf_vp = by_lemma["аналізувати"]["enrichment"]["verb_pedagogy"]
    perf_vp = by_lemma["проаналізувати"]["enrichment"]["verb_pedagogy"]

    assert imperf_vp["aspect_partner"] == {
        "lemma": "проаналізувати",
        "source": "Anna Ohoiko",
        "url_slug": "проаналізувати",
    }
    assert perf_vp["aspect_partner"] == {
        "lemma": "аналізувати",
        "source": "Anna Ohoiko",
        "url_slug": "аналізувати",
    }
    assert imperf_vp["stems"]["present_future"] == ["аналізу-", "проаналізу-"]
    assert perf_vp["stems"]["present_future"] == ["аналізу-", "проаналізу-"]
    assert imperf_vp["government"][0]["label"] == "+ accusative"
    assert stats["500_aspect_partner_applied"] == 2
    assert stats["500_stems_applied"] == 2
    assert stats["500_government_applied"] == 2


def test_apply_ohoiko_quality_enrichment_partner_omits_url_slug_when_leg_missing() -> None:
    # Only the imperfective leg is a live Atlas entry.
    manifest = _stub_manifest(["аналізувати"])
    parsed_500 = [parse_500_verbs_chunk("anna-ohoiko-500-verbs_e0001", "x", V0001_TEXT)]
    apply_ohoiko_quality_enrichment(manifest, parsed_1000=[], parsed_500=parsed_500)

    vp = manifest["entries"][0]["enrichment"]["verb_pedagogy"]
    assert vp["aspect_partner"] == {"lemma": "проаналізувати", "source": "Anna Ohoiko"}
    assert "url_slug" not in vp["aspect_partner"]


def test_apply_ohoiko_quality_enrichment_two_aspect_verb_gets_no_partner() -> None:
    manifest = _stub_manifest(["атакувати"])
    parsed_500 = [parse_500_verbs_chunk("anna-ohoiko-500-verbs_e0002", "x", V0002_TEXT)]
    stats = apply_ohoiko_quality_enrichment(manifest, parsed_1000=[], parsed_500=parsed_500)

    vp = manifest["entries"][0]["enrichment"]["verb_pedagogy"]
    assert "aspect_partner" not in vp
    assert vp["stems"]["present_future"] == ["атаку-", "атаку-"]
    assert stats["500_aspect_partner_applied"] == 0


def test_apply_ohoiko_quality_enrichment_multi_perfective_all_point_to_imperfective() -> None:
    manifest = _stub_manifest(["будувати", "збудувати", "побудувати"])
    parsed_500 = [parse_500_verbs_chunk("anna-ohoiko-500-verbs_e0018", "x", V0018_TEXT)]
    apply_ohoiko_quality_enrichment(manifest, parsed_1000=[], parsed_500=parsed_500)

    by_lemma = {e["lemma"]: e for e in manifest["entries"]}
    # Imperfective's canonical partner is the first-listed perfective.
    assert by_lemma["будувати"]["enrichment"]["verb_pedagogy"]["aspect_partner"]["lemma"] == "збудувати"
    # Both perfectives point back to the imperfective.
    assert by_lemma["збудувати"]["enrichment"]["verb_pedagogy"]["aspect_partner"]["lemma"] == "будувати"
    assert by_lemma["побудувати"]["enrichment"]["verb_pedagogy"]["aspect_partner"]["lemma"] == "будувати"


# ---------------------------------------------------------------------------
# verb_pedagogy_vesum_aspect: VESUM aspect fill across all Atlas verbs
# ---------------------------------------------------------------------------

_FAKE_VESUM_ROWS: dict[str, list[dict[str, str]]] = {
    "заховати": [{"word_form": "заховати", "lemma": "заховати", "pos": "verb", "tags": "verb:inf:perf"}],
    "заховувати": [{"word_form": "заховувати", "lemma": "заховувати", "pos": "verb", "tags": "verb:inf:imperf"}],
    "ходити": [{"word_form": "ходити", "lemma": "ходити", "pos": "verb", "tags": "verb:inf:imperf"}],
    "піти": [{"word_form": "піти", "lemma": "піти", "pos": "verb", "tags": "verb:inf:perf"}],
    "атакувати": [
        {"word_form": "атакувати", "lemma": "атакувати", "pos": "verb", "tags": "verb:inf:imperf"},
        {"word_form": "атакувати", "lemma": "атакувати", "pos": "verb", "tags": "verb:inf:perf"},
    ],
    "святий": [{"word_form": "святий", "lemma": "святий", "pos": "adj", "tags": "adj:m:v_naz:compb"}],
}


def _patch_fake_vesum(monkeypatch) -> None:
    monkeypatch.setattr(
        enrich_manifest_module, "verify_word", lambda word: _FAKE_VESUM_ROWS.get(word, [])
    )


def test_apply_vesum_verb_aspect_sets_known_aspects(monkeypatch) -> None:
    _patch_fake_vesum(monkeypatch)
    manifest = _stub_manifest(["заховати", "заховувати"])
    stats = vpa.apply_vesum_verb_aspect(manifest)

    by_lemma = {e["lemma"]: e for e in manifest["entries"]}
    assert by_lemma["заховати"]["enrichment"]["verb_pedagogy"]["aspect"] == "perfective"
    assert by_lemma["заховувати"]["enrichment"]["verb_pedagogy"]["aspect"] == "imperfective"
    assert "VESUM" in by_lemma["заховати"]["enrichment"]["sources"]
    assert stats == {
        "verbs_total": 2,
        "verbs_aspect_known": 2,
        "aspect_applied": 2,
        "aspect_partner_from_xref": 0,
    }


def test_apply_vesum_verb_aspect_skips_ambiguous_and_non_verb(monkeypatch) -> None:
    _patch_fake_vesum(monkeypatch)
    manifest = _stub_manifest(["атакувати"])  # both imperf+perf tags -> ambiguous
    manifest["entries"].append({"lemma": "святий", "pos": "adj", "enrichment": None})
    stats = vpa.apply_vesum_verb_aspect(manifest)

    by_lemma = {e["lemma"]: e for e in manifest["entries"]}
    assert by_lemma["атакувати"]["enrichment"] is None
    assert by_lemma["святий"]["enrichment"] is None
    assert stats["verbs_total"] == 1  # only the pos=="verb" entry counts
    assert stats["verbs_aspect_known"] == 0


def test_apply_vesum_verb_aspect_fills_partner_from_dictionary_cross_reference(monkeypatch) -> None:
    _patch_fake_vesum(monkeypatch)
    manifest = _stub_manifest(["заховати"])
    manifest["entries"][0]["enrichment"] = {
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["(докон. до заховувати / див. заховувати) сховати щось."],
                "cross_reference": {"raw": "див. заховувати", "target": "заховувати"},
            }
        ]
    }
    manifest["entries"].append({"lemma": "заховувати", "url_slug": "заховувати", "pos": "verb", "enrichment": None})

    stats = vpa.apply_vesum_verb_aspect(manifest)

    vp = manifest["entries"][0]["enrichment"]["verb_pedagogy"]
    assert vp["aspect_partner"] == {"lemma": "заховувати", "source": "СУМ-20", "url_slug": "заховувати"}
    assert stats["aspect_partner_from_xref"] == 1


def test_apply_vesum_verb_aspect_ignores_cross_reference_with_same_aspect(monkeypatch) -> None:
    _patch_fake_vesum(monkeypatch)
    manifest = _stub_manifest(["заховати"])
    manifest["entries"][0]["enrichment"] = {
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["(див. заховати) те саме, що заховати."],
                # Same lemma both sides -> same aspect -> not an aspect pair.
                "cross_reference": {"raw": "див. заховати", "target": "заховати"},
            }
        ]
    }
    vpa.apply_vesum_verb_aspect(manifest)
    assert "aspect_partner" not in manifest["entries"][0]["enrichment"]["verb_pedagogy"]


def test_apply_vesum_verb_aspect_never_overwrites_anna_sourced_partner(monkeypatch) -> None:
    _patch_fake_vesum(monkeypatch)
    manifest = _stub_manifest(["заховати"])
    manifest["entries"][0]["enrichment"] = {
        "verb_pedagogy": {"aspect_partner": {"lemma": "заховувати", "source": "Anna Ohoiko"}},
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["..."],
                "cross_reference": {"raw": "див. інше", "target": "заховувати"},
            }
        ],
    }
    stats = vpa.apply_vesum_verb_aspect(manifest)
    assert manifest["entries"][0]["enrichment"]["verb_pedagogy"]["aspect_partner"]["source"] == "Anna Ohoiko"
    assert stats["aspect_partner_from_xref"] == 0
