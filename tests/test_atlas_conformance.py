from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.audit.validate_atlas_conformance import VesumLemmaLookup, validate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "starlight" / "src" / "data" / "lexicon-manifest.json"
VESUM_PATH = PROJECT_ROOT / "data" / "vesum.db"
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


def _gates_for(entry: dict, vesum: set[str] | None = None) -> list[str]:
    fake_vesum = vesum if vesum is not None else {"слово"}
    violations = validate(_manifest(entry), vesum=fake_vesum, curriculum=FAKE_CURRICULUM)
    return [violation.gate for violation in violations]


def test_real_lexicon_manifest_conforms_to_atlas_gates():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    curriculum = yaml.safe_load(CURRICULUM_PATH.read_text(encoding="utf-8"))

    if VESUM_PATH.exists():
        # Local dev: full enforcement incl. lemma↔VESUM membership.
        with VesumLemmaLookup(VESUM_PATH) as vesum:
            violations = validate(manifest, vesum=vesum, curriculum=curriculum)
    else:
        # CI lacks the 967MB gitignored data/vesum.db → vesum=None skips ONLY the
        # lemma_in_vesum gate; every other §8 gate still enforces on the real manifest.
        violations = validate(manifest, vesum=None, curriculum=curriculum)

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


def test_sovietization_must_be_flagged_for_unmirrored_sum11_risk():
    entry = _entry(
        enrichment={
            "meaning": {
                "definitions": [{"text": "Ідеологічно навантажене тлумачення.", "sovietization_risk": 1}],
                "source": "СУМ-11",
            }
        }
    )

    assert _gates_for(entry) == ["sovietization_must_be_flagged"]


def test_sovietization_passes_when_meaning_carries_source_risk():
    entry = _entry(
        enrichment={
            "meaning": {
                "definitions": ["Ідеологічно навантажене тлумачення."],
                "source": "СУМ-11",
                "sovietization_risk": 1,
            }
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
