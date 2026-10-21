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

from scripts.lexicon.calque_corrections import (
    CURATED_CALQUES,
    LEXICALISED_SAFE,
    PHRASAL_CALQUES,
    SENSE_RESTRICTED_CALQUES,
    SOURCE_CHECKED_CHUNKS,
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


def test_yavlyatysia_cites_the_chunk_that_holds_its_correction():
    """#9603: Авраменко 9 кл. s0159 holds «являтися переможцем → бути переможцем»; s0162 does not.

    Verified by the driver's source receipt (sources MCP get_chunk_context on
    both chunks); this pins the repaired locator offline.
    """
    evidence = SENSE_RESTRICTED_CALQUES["являтися"]["evidence"]
    locators = [item.partition(":")[0] for item in evidence]
    assert "9-klas-ukrajinska-mova-avramenko-2017_s0159" in locators
    assert "9-klas-ukrajinska-mova-avramenko-2017_s0162" not in locators


def test_source_checked_chunks_bind_each_cited_excerpt_to_its_correction():
    """#9603: each reviewer-checked chunk binds the verbatim excerpt its record cites.

    The excerpts were re-read with sources MCP get_chunk_context and checked as
    verbatim (``…``-joined) spans of the read-only primary sources.db chunk
    (receipt: batch_state/reports/atlas-9603-final-review-repair/source-passages.json).
    The 7-klas litvinova/zabolotnyi 2024 and 9-klas zabolotnyi 2017 books are
    absent there, so their locators must stay unchecked references.
    """
    from scripts.lexicon.heritage_classifier import _curated_calque_map, source_text_digest

    kinds = {"sense": "sense_restricted", "phrase": "phrasal"}
    for locator, (scope, rejected, endorsed, digest) in SOURCE_CHECKED_CHUNKS.items():
        row = _curated_calque_map()[rejected]
        assert row["kind"] == kinds[scope], locator
        assert {form.partition(" (")[0] for form in endorsed} <= set(row["corrections"]), locator
        excerpts = [item.partition(":")[2].strip() for item in row["evidence"] if item.partition(":")[0] == locator]
        assert [source_text_digest(item) for item in excerpts] == [digest], locator
        # A stated context is the passage's own: «чинний (закон)», «активний (вулкан)».
        for form in endorsed:
            base, _, context = form.partition(" (")
            text = excerpts[0].casefold()
            assert base in text and context.rstrip(")") in text, (locator, form)
    assert SOURCE_CHECKED_CHUNKS["7-klas-ukrmova-avramenko-2024_s0106"][2] == ("чинний (закон)", "активний (вулкан)")
    cited = {
        item.partition(":")[0]
        for bucket in (CURATED_CALQUES, PHRASAL_CALQUES, SENSE_RESTRICTED_CALQUES)
        for row in bucket.values()
        for item in row.get("evidence", [])
    }
    for absent in (
        "7-klas-ukrmova-litvinova-2024_s0186",
        "7-klas-ukrmova-zabolotnyi-2024_s0229",
        "7-klas-ukrmova-zabolotnyi-2024_s0143",
        "7-klas-ukrmova-zabolotnyi-2024_s0124",
        "9-klas-ukrmova-zabolotnyi-2017_s0291",
    ):
        assert absent in cited and absent not in SOURCE_CHECKED_CHUNKS
