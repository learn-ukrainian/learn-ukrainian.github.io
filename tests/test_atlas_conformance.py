from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.audit.validate_atlas_conformance import HeritageLemmaLookup, VesumLemmaLookup, validate
from scripts.lexicon.build_kaikki_lookup import KAIKKI_SOURCE
from scripts.lexicon.manifest_io import load_manifest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
VESUM_PATH = PROJECT_ROOT / "data" / "vesum.db"
SOURCES_PATH = PROJECT_ROOT / "data" / "sources.db"
CURRICULUM_PATH = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"

FAKE_CURRICULUM = {"levels": {"a1": {"modules": ["known-module"]}}}


def _manifest(entry: dict) -> dict:
    return {"entries": [entry]}


def _entry(**overrides: object) -> dict:
    entry = {
        "lemma": "слово",
        "url_slug": "слово",
        "gloss": "word",
        "pos": "noun",
        "ipa": None,
        "primary_source": "test",
        "course_usage": [{"track": "a1", "slug": "known-module"}],
        "heritage_status": {
            "classification": "standard",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "sovietization_risk": 0,
            "calque_warning": None,
        },
    }
    entry.update(overrides)
    return entry


def _gates_for(
    entry: dict, vesum: set[str] | None = None, heritage: set[str] | None = None
) -> list[str]:
    fake_vesum = vesum if vesum is not None else {"слово"}
    violations = validate(
        _manifest(entry), vesum=fake_vesum, curriculum=FAKE_CURRICULUM, heritage=heritage
    )
    return [violation.gate for violation in violations]


def test_real_lexicon_manifest_conforms_to_atlas_gates():
    manifest = load_manifest(MANIFEST_PATH)
    curriculum = yaml.safe_load(CURRICULUM_PATH.read_text(encoding="utf-8"))
    heritage = SOURCES_PATH if SOURCES_PATH.exists() else None

    if VESUM_PATH.exists():
        # Local dev: full enforcement incl. lemma↔VESUM membership.
        with VesumLemmaLookup(VESUM_PATH) as vesum:
            violations = validate(manifest, vesum=vesum, curriculum=curriculum, heritage=heritage)
    else:
        # CI lacks the 967MB gitignored data/vesum.db → vesum=None skips ONLY the
        # lemma_in_vesum gate; every other §8 gate still enforces on the real manifest.
        violations = validate(manifest, vesum=None, curriculum=curriculum, heritage=heritage)

    assert violations == []


def test_clean_fixture_passes_all_gates():
    assert _gates_for(_entry()) == []


def test_lemma_in_vesum_flags_missing_single_word():
    assert _gates_for(_entry(), vesum=set()) == ["lemma_in_vesum"]


def test_lemma_in_vesum_exempts_genuine_multi_word_phrase():
    entry = _entry(lemma="До побачення", url_slug="до-побачення")

    assert _gates_for(entry, vesum=set()) == []


def test_lemma_in_vesum_exempts_proper_nouns():
    entry = _entry(lemma="Ілля", url_slug="ілля", pos="proper noun")

    assert _gates_for(entry, vesum=set()) == []


def test_lemma_in_vesum_resolves_capitalized_vesum_entries():
    # #3197 follow-up: VESUM stores proper nouns / abbreviations capitalized
    # (Афіни, УЗД). The old casefold-only lookup queried "афіни"/"узд" and missed
    # them; probing the case-preserved form must resolve them. pos is a common noun
    # here so the proper-noun exemption does NOT mask the lookup path under test.
    assert _gates_for(_entry(lemma="Афіни", url_slug="афіни", pos="noun"), vesum={"Афіни"}) == []
    assert _gates_for(_entry(lemma="УЗД", url_slug="узд", pos="noun:n"), vesum={"УЗД"}) == []


def test_lemma_in_vesum_exempts_proper_noun_with_morphology_suffix():
    # #3197 follow-up: real proper-noun pos tags carry a :pl/:m suffix
    # ("proper noun:pl" for Афіни/Чернівці); the exemption must match the base pos.
    entry = _entry(lemma="Чернівці", url_slug="чернівці", pos="proper noun:pl")

    assert _gates_for(entry, vesum=set()) == []


def test_lemma_in_vesum_exempts_heritage_word_absent_from_vesum():
    # #3197 follow-up: хвастливий is authentic Ukrainian (Грінченко 1907 «=
    # хвастовитий» + ЕСУМ Proto-Slavic + СУМ-20) but absent from VESUM. VESUM
    # membership is necessary-but-not-sufficient; the heritage allowlist exempts it.
    entry = _entry(lemma="хвастливий", url_slug="хвастливий", pos="adjective")

    assert _gates_for(entry, vesum=set()) == []


def test_lemma_in_vesum_heritage_fallback_exempts_attested_word():
    # #3211: a VESUM-miss is cross-checked against the heritage corpus before flagging.
    # A word absent from VESUM but attested in Грінченко/ЕСУМ (fake heritage set, NOT in
    # the manual allowlist) is exempted — the gate self-heals on ANY heritage-attested
    # VESUM gap, not only the curated ones. (кобіта = the canonical heritage-defense word.)
    entry = _entry(lemma="кобіта", url_slug="кобіта", pos="noun")

    assert _gates_for(entry, vesum=set(), heritage={"кобіта"}) == []


def test_lemma_in_vesum_exempts_modern_technical_term_in_both_modes():
    # #3270: морфонеміка / контрфактичний are standard MODERN terms absent from VESUM AND
    # from the HISTORICAL heritage corpus. The live heritage lookup cannot self-heal them,
    # so the curated modern-technical allowlist must exempt them in BOTH modes — including
    # the live-heritage mode (heritage present but NOT attesting), which was the failing case.
    for lemma, pos in (
        ("морфонеміка", "noun"),
        ("контрфактичний", "adjective"),
        ("топікалізація", "noun"),
        ("цільнозерновий", "adjective"),
    ):
        entry = _entry(lemma=lemma, url_slug=lemma, pos=pos)
        assert _gates_for(entry, vesum=set()) == []  # offline mode (no heritage source)
        assert _gates_for(entry, vesum=set(), heritage=set()) == []  # live mode, not attested


def test_lemma_in_vesum_exempts_delimited_heads_when_each_component_is_known():
    entry = _entry(lemma="не/ні", url_slug="не-ні", pos="particle pair")
    assert _gates_for(entry, vesum={"не", "ні"}, heritage=set()) == []

    entry = _entry(lemma="доти...доки", url_slug="доти-доки", pos="correlative conjunction")
    assert _gates_for(entry, vesum={"доти", "доки"}, heritage=set()) == []


def test_lemma_in_vesum_flags_delimited_heads_with_unknown_component():
    entry = _entry(lemma="не/зызыжщ", url_slug="не-зызыжщ", pos="particle pair")
    assert _gates_for(entry, vesum={"не"}, heritage=set()) == ["lemma_in_vesum"]


def test_lemma_in_vesum_flags_when_absent_from_both_vesum_and_heritage():
    # #3211: the gate still catches genuinely-unattested single words — absent from VESUM
    # AND not in the heritage corpus (heritage present but empty) → violation. The allowlist
    # is bypassed when a heritage corpus is wired.
    entry = _entry(lemma="зызыжщ", url_slug="зызыжщ", pos="noun")

    assert _gates_for(entry, vesum=set(), heritage=set()) == ["lemma_in_vesum"]


def test_lemma_in_vesum_allowlist_is_offline_fallback_when_no_heritage():
    # #3211: when the heritage corpus is unavailable (heritage=None, e.g. no sources.db),
    # the curated allowlist still exempts known VESUM-gap words.
    entry = _entry(lemma="хвастливий", url_slug="хвастливий", pos="adjective")

    assert _gates_for(entry, vesum=set(), heritage=None) == []


@pytest.mark.skipif(not SOURCES_PATH.exists(), reason="needs gitignored data/sources.db")
def test_heritage_lemma_lookup_attests_grinchenko_word_real_db():
    # #3211: real Грінченко/ЕСУМ lookup — хвастливий is attested (Грінченко headword),
    # nonsense is not. Proves the live fallback resolves the VESUM gap without an allowlist.
    with HeritageLemmaLookup(SOURCES_PATH) as heritage:
        assert heritage.has_attestation("хвастливий") is True
        assert heritage.has_attestation("зызыжщ") is False


def test_lemma_in_vesum_exempts_deliberate_warning_seed():
    entry = _entry(
        lemma="міроприємство",
        url_slug="міроприємство",
        primary_source="surzhyk_to_avoid",
        heritage_status={
            "classification": "russianism",
            "attestations": [{"source": "standard_alternative", "ref": "захід"}],
            "is_russianism": True,
            "russian_shadow": False,
            "sovietization_risk": 0,
            "calque_warning": None,
        },
    )

    assert _gates_for(entry, vesum=set()) == []


def test_provenance_per_section_flags_missing_source():
    entry = _entry(
        enrichment={
            "meaning": {
                "definitions": ["Лексичне значення для тесту."],
            }
        }
    )

    assert _gates_for(entry) == ["provenance_per_section"]


def test_section_omitted_not_empty_flags_empty_section():
    entry = _entry(
        enrichment={
            "meaning": {
                "definitions": [],
                "source": "Вікісловник",
            }
        }
    )

    assert _gates_for(entry) == ["section_omitted_not_empty"]


def test_morphology_marked_forms_only_is_renderable_content():
    """#4891 renders marked_forms in their own subsection: a marked-forms-only
    morphology (VESUM has no unmarked modern paradigm — slang/variant lemmas
    like «баг») must NOT flag section_omitted_not_empty. Detonated on the
    #4936 publish (29 lemmas, red main)."""
    entry = _entry(
        enrichment={
            "morphology": {
                "pos": "іменник",
                "form_count": 0,
                "forms": [],
                "source": "VESUM",
                "marked_forms": [
                    {
                        "form": "багові",
                        "label": "чол., давальний",
                        "marker": "slang",
                        "marker_label": "сленгова форма",
                    }
                ],
            }
        }
    )

    assert _gates_for(entry) == []


def test_morphology_all_form_containers_empty_still_flags():
    """Truly empty morphology (forms, paradigm, AND marked_forms empty) keeps
    failing the gate — the marked-forms allowance must not fail-open."""
    entry = _entry(
        enrichment={
            "morphology": {
                "pos": "іменник",
                "form_count": 0,
                "forms": [],
                "marked_forms": [],
                "source": "VESUM",
            }
        }
    )

    assert _gates_for(entry) == ["section_omitted_not_empty"]


def test_synonyms_section_requires_source_and_items():
    entry = _entry(
        sections={
            "synonyms": {
                "items": [],
                "source": "slovnyk.me: Словник синонімів",
            }
        }
    )

    assert _gates_for(entry) == ["section_omitted_not_empty"]


def test_idioms_section_requires_source_and_cards():
    entry = _entry(
        sections={
            "idioms": {
                "items": [{"phrase": "яблуко розбрату", "definition": ""}],
            }
        }
    )

    assert _gates_for(entry) == ["provenance_per_section", "section_omitted_not_empty"]


def test_heritage_evidence_required_flags_authentic_without_presoviet_attestation():
    entry = _entry(
        heritage_status={
            "classification": "dialect",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "sovietization_risk": 0,
            "calque_warning": None,
        }
    )

    assert _gates_for(entry) == ["heritage_evidence_required"]


def test_sovietization_must_be_flagged_for_unflagged_sum11_card_risk():
    entry = _entry(
        enrichment={
            "definition_cards": [
                {
                    "id": "sum11-flagged",
                    "source": "СУМ-11",
                    "definitions": ["Ідеологічно навантажене тлумачення."],
                    "sovietization_risk": 1,
                }
            ]
        }
    )

    assert _gates_for(entry) == ["sovietization_must_be_flagged"]


def test_sovietization_passes_when_sum11_card_carries_inline_caveat():
    entry = _entry(
        enrichment={
            "definition_cards": [
                {
                    "id": "sum11-flagged",
                    "source": "СУМ-11",
                    "definitions": ["Ідеологічно навантажене тлумачення."],
                    "sovietization_risk": 1,
                    "flag_note": "⚠ СУМ-11 — радянське видання; подаємо обережно.",
                }
            ]
        }
    )

    assert _gates_for(entry) == []


def test_cross_link_integrity_flags_unknown_course_slug():
    entry = _entry(course_usage=[{"track": "a1", "slug": "missing-module"}])

    assert _gates_for(entry) == ["cross_link_integrity"]


def test_wiki_summary_attributed_flags_missing_freshness_date():
    entry = _entry(
        enrichment={
            "wikipedia": {
                "summary": "Short article summary.",
                "url": "https://uk.wikipedia.org/wiki/%D0%A1%D0%BB%D0%BE%D0%B2%D0%BE",
            }
        }
    )

    assert _gates_for(entry) == ["wiki_summary_attributed"]


def test_pronunciation_ipa_must_be_well_formed_string():
    entry = _entry(pronunciation={"ipa": ["[slɔˈwɔ]"], "source": KAIKKI_SOURCE})

    assert _gates_for(entry) == ["pronunciation_ipa_well_formed"]


def test_pronunciation_requires_kaikki_source_attribution():
    entry = _entry(pronunciation={"ipa": "[slɔˈwɔ]", "source": "Wiktionary"})

    assert _gates_for(entry) == ["kaikki_attribution_required"]


def test_kaikki_pronunciation_and_etymology_pass_with_cc_by_sa_source():
    entry = _entry(
        pronunciation={"ipa": "[slɔˈwɔ]", "source": KAIKKI_SOURCE},
        enrichment={
            "etymology": {
                "text": "From Proto-Slavic *slovo.",
                "source": KAIKKI_SOURCE,
            }
        },
    )

    assert _gates_for(entry) == []


def test_kaikki_etymology_source_must_carry_cc_by_sa_attribution():
    entry = _entry(
        enrichment={
            "etymology": {
                "text": "From Proto-Slavic *slovo.",
                "source": "kaikki/Wiktionary",
            }
        }
    )

    assert _gates_for(entry) == ["kaikki_attribution_required"]


def test_kaikki_etymology_tolerates_base_form_suffix():
    # #2971 appends " (etymology of base form X)" to derived-lemma etymologies;
    # the attribution prefix is intact, so this must PASS (regression: a real
    # re-enrich produced these and turned the conformance gate RED on main).
    entry = _entry(
        enrichment={
            "etymology": {
                "text": "From Proto-Slavic *vyględati.",
                "source": f"{KAIKKI_SOURCE} (etymology of base form вигляд)",
            }
        }
    )

    assert _gates_for(entry) == []


def test_kaikki_etymology_base_form_suffix_without_attribution_still_fails():
    entry = _entry(
        enrichment={
            "etymology": {
                "text": "From Proto-Slavic *vyględati.",
                "source": "kaikki/Wiktionary (etymology of base form вигляд)",
            }
        }
    )

    assert _gates_for(entry) == ["kaikki_attribution_required"]
