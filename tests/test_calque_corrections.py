"""Structural + precision invariants for the §6 calque-correction dataset.

These tests are deterministic (no live MCP / sources.db). They pin the
*precision* decisions made during the #3098 grok-swarm curation so a future
careless edit that re-introduces a false-positive fails CI:

  * authentic Ukrainian words that the swarm surfaced (дійсно, відносно,
    по-моєму, …) were DROPPED after live heritage/UA-GEC verification and must
    never reappear in an always-flag bucket;
  * polysemes (вірний, дійсний, …) live in SENSE_RESTRICTED_CALQUES with an
    explicit calque_sense/authentic_sense split so the renderer never
    blanket-flags the authentic sense.

Linguistic provenance is documented per entry in calque_corrections.py and was
verified live (heritage gate + UA-GEC F/Calque pairs + VESUM) at curation time;
that is intentionally NOT re-run here to keep the suite fast and offline.
"""

from __future__ import annotations

import pytest

from scripts.lexicon.calque_corrections import (
    CURATED_CALQUES,
    LEXICALISED_SAFE,
    PHRASAL_CALQUES,
    SENSE_RESTRICTED_CALQUES,
)

# Forms the swarm proposed but that live verification cleared as authentic
# Ukrainian (or as a different — surzhyk — layer). They must NOT be flagged as
# calques in any always-flag bucket. Re-adding one is the regression this guards.
DROPPED_AUTHENTIC_FORMS = frozenset({
    "дійсно",       # authentic adverb (Грінченко; Antonenko p053)
    "відносно",     # authentic ("порівняно"); UA-GEC offers it AS a correction
    "по-моєму",     # standard Ukrainian "in my opinion"
    "з приводу",    # standard Ukrainian
    "з цього приводу",
    "ніяк",         # UA-GEC context artifact, = "in no way"
    "вроде",        # raw Russian / surzhyk insertion — different layer
    "кажись",       # surzhyk — different layer
})

_WARNING_DICT_BUCKETS = {
    "CURATED_CALQUES": CURATED_CALQUES,
    "PHRASAL_CALQUES": PHRASAL_CALQUES,
    "SENSE_RESTRICTED_CALQUES": SENSE_RESTRICTED_CALQUES,
}


@pytest.mark.parametrize("name,bucket", _WARNING_DICT_BUCKETS.items())
def test_correction_buckets_well_formed(name, bucket):
    """Every warn-bucket entry needs a non-empty corrections list + provenance."""
    assert bucket, f"{name} is unexpectedly empty"
    for headword, entry in bucket.items():
        assert headword.strip() == headword and headword, f"{name}: bad key {headword!r}"
        corrections = entry.get("corrections")
        assert isinstance(corrections, list) and corrections, (
            f"{name}[{headword!r}] missing corrections list"
        )
        assert all(isinstance(c, str) and c.strip() for c in corrections), (
            f"{name}[{headword!r}] has an empty correction"
        )
        assert headword not in corrections, (
            f"{name}[{headword!r}] lists itself as its own correction"
        )
        source = entry.get("source")
        assert isinstance(source, list) and source, (
            f"{name}[{headword!r}] missing provenance source"
        )


def test_active_participle_slice_has_evidence_and_heritage_guard():
    """The #3098 first-slice entries carry direct corpus quotes + guard notes."""
    for headword, entry in CURATED_CALQUES.items():
        if not any(suffix in headword for suffix in ("учий", "ючий", "ачий", "ячий")):
            continue

        evidence = entry.get("evidence")
        assert isinstance(evidence, list) and evidence, (
            f"CURATED_CALQUES[{headword!r}] missing quoted evidence"
        )
        assert all(isinstance(item, str) and ":" in item for item in evidence), (
            f"CURATED_CALQUES[{headword!r}] evidence must cite source refs"
        )
        guard = entry.get("heritage_guard")
        assert isinstance(guard, str) and "search_heritage" in guard, (
            f"CURATED_CALQUES[{headword!r}] missing heritage guard result"
        )


def test_pryiniaty_uchast_has_corpus_evidence_and_alias():
    """The cheap collocation slice is source-backed and catches both aspects."""
    for phrase, correction in (
        ("прийняти участь", "взяти участь"),
        ("приймати участь", "брати участь"),
    ):
        entry = PHRASAL_CALQUES[phrase]
        assert correction in entry["corrections"]
        assert any("antonenko-davydovych" in item for item in entry["evidence"])
        assert "search_heritage" in entry["heritage_guard"]


def test_collocation_slice2_phrasal_entries_have_evidence():
    """New always-flag phrase entries are direct correction pairs, not guesses."""
    expected = {
        "при допомозі": "за допомогою",
        "співпадати": "збігатися",
        "в кінці кінців": "врешті-решт",
    }
    for phrase, correction in expected.items():
        entry = PHRASAL_CALQUES[phrase]
        assert correction in entry["corrections"]
        assert entry["evidence"]
        assert "search_heritage" in entry["heritage_guard"]


def test_sense_restricted_schema():
    """Polysemes carry an explicit calque_sense / authentic_sense split."""
    assert SENSE_RESTRICTED_CALQUES, "SENSE_RESTRICTED_CALQUES is empty"
    for headword, entry in SENSE_RESTRICTED_CALQUES.items():
        for field in ("calque_sense", "authentic_sense", "note"):
            value = entry.get(field)
            assert isinstance(value, str) and value.strip(), (
                f"SENSE_RESTRICTED_CALQUES[{headword!r}] missing {field}"
            )
        # The two senses must be genuinely distinct — that distinction is the
        # whole reason the word is sense-restricted rather than always-flagged.
        assert entry["calque_sense"] != entry["authentic_sense"], (
            f"SENSE_RESTRICTED_CALQUES[{headword!r}]: calque_sense == authentic_sense"
        )


def test_collocation_slice2_sense_restricted_entries_have_guarded_senses():
    """Polysemous phrase calques stay sense-scoped to avoid false positives."""
    expected = {
        "на протязі": ("протягом", "draft"),
        "являтися": ("бути", "appear"),
        "дякуючи": ("завдяки", "thanking"),
        "так як": ("оскільки", "так, як"),
        "біля": ("близько", "near"),
        "на рахунок": ("щодо", "account"),
    }
    for headword, (correction, authentic_marker) in expected.items():
        entry = SENSE_RESTRICTED_CALQUES[headword]
        assert correction in entry["corrections"]
        assert authentic_marker in entry["authentic_sense"]
        assert entry["evidence"]
        assert "search_heritage" in entry["heritage_guard"]
        assert headword not in PHRASAL_CALQUES


def test_single_word_lexical_slice3_entries_have_evidence():
    """Slice 3 keeps only source-backed single-word lexical calques."""
    expected = {
        "слідуючий": "наступний",
        "багаточисельний": "численний",
        "міроприємство": "захід",
        "учбовий": "навчальний",
    }
    for headword, correction in expected.items():
        entry = CURATED_CALQUES[headword]
        assert correction in entry["corrections"]
        assert entry["evidence"]
        assert "search_heritage" in entry["heritage_guard"]


def test_single_word_lexical_slice3_polysemes_are_sense_restricted():
    """любий and неділя are authentic words outside the calque sense."""
    expected = {
        "любий": ("будь-який", "dear"),
        "неділя": ("тиждень", "Sunday"),
    }
    for headword, (correction, authentic_marker) in expected.items():
        entry = SENSE_RESTRICTED_CALQUES[headword]
        assert correction in entry["corrections"]
        assert authentic_marker in entry["authentic_sense"]
        assert entry["evidence"]
        assert "search_heritage" in entry["heritage_guard"]
        assert headword not in CURATED_CALQUES


def test_buckets_are_disjoint():
    """A headword must not be both warn-worthy and safe, nor double-bucketed."""
    curated = set(CURATED_CALQUES)
    phrasal = set(PHRASAL_CALQUES)
    sense = set(SENSE_RESTRICTED_CALQUES)
    safe = set(LEXICALISED_SAFE)

    assert curated.isdisjoint(safe), curated & safe
    assert curated.isdisjoint(sense), curated & sense
    assert curated.isdisjoint(phrasal), curated & phrasal
    assert phrasal.isdisjoint(sense), phrasal & sense
    assert sense.isdisjoint(safe), sense & safe


def test_dropped_authentic_forms_never_flagged():
    """Regression guard: verified-authentic forms stay out of every warn bucket.

    These were proposed by the grok-swarm but cleared as authentic / out-of-scope
    by live heritage + UA-GEC + VESUM checks. Flagging them would red-flag correct
    usage — the same false-positive class as flagging ``блискучий``.
    """
    flagged = set(CURATED_CALQUES) | set(PHRASAL_CALQUES) | set(SENSE_RESTRICTED_CALQUES)
    leaked = DROPPED_AUTHENTIC_FORMS & flagged
    assert not leaked, (
        f"authentic/out-of-scope forms re-added as calques: {sorted(leaked)} — "
        "see calque_corrections.py 'Deliberately EXCLUDED' note before re-adding"
    )


def test_curated_polysemes_landed_in_sense_restricted():
    """The verified polysemes belong in the sense-restricted bucket, not curated."""
    for headword in ("вірний", "дійсний", "відношення", "рахувати", "виглядати"):
        assert headword in SENSE_RESTRICTED_CALQUES, (
            f"{headword!r} should be sense-restricted (authentic in its base sense)"
        )
        assert headword not in CURATED_CALQUES, (
            f"{headword!r} must not be an always-flag calque"
        )


def test_pracjujucyj_yields_section6_note_with_antonenko_citation():
    """#M-4 evidence: unit test proves працюючий yields §6 note → працівник with Antonenko citation.

    This exercises the _curated_calque path used by enrich_manifest.py §6 wiring.
    Source must cite davydov / antonenko-p145 (verified live via MCP query_slovnyk_me(davydov)
    + get_chunk_context p145 prose + search_heritage guard; no invention).
    """
    from scripts.lexicon.enrich_manifest import _curated_calque

    note = _curated_calque("працюючий", "працюючий")
    assert note is not None, "no §6 note for працюючий"
    assert note.get("kind") == "participle"
    corrections = note.get("corrections", [])
    assert "працівник" in corrections, f"expected працівник in {corrections}"
    assert "той, що працює" in corrections
    sources = note.get("source", [])
    assert any("davydov" in s or "antonenko" in s for s in sources), (
        f"Antonenko/davydov citation required in sources: {sources}"
    )
    assert any("Працюючий" in item for item in note.get("evidence", []))
    assert "No heritage evidence found" in note.get("heritage_guard", "")
    print("GENERATED_§6_NOTE_FOR_працюючий_FROM_UNIT_TEST:", note)


def test_requested_spot_checks_resolve_with_evidence():
    """Pin the three requested printout forms through the production lookup."""
    from scripts.lexicon.enrich_manifest import _curated_calque

    expected = {
        "працюючий": "працівник",
        "оточуючий": "навколишній",
        "прийняти участь": "взяти участь",
    }
    for form, correction in expected.items():
        note = _curated_calque(form, form)
        assert note is not None, f"no §6 note for {form}"
        assert correction in note["corrections"]
        assert note["evidence"], f"no evidence for {form}"
        assert "search_heritage" in note["heritage_guard"]
        print(f"SPOT_CHECK_{form}:", note)
