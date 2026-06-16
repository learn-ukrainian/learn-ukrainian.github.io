"""Tests for the VESUM inflection→lemma alias generator (#2882)."""

import scripts.lexicon.generate_vesum_aliases as gen


def test_build_alias_map_gates(monkeypatch) -> None:
    # VESUM stub: form -> rows, keyed by the (stress-stripped) form the generator queries.
    fake = {
        "брата": [{"lemma": "брат"}],                       # single lemma -> fold
        "вареники": [{"lemma": "вареник"}],                 # single, lemma NOT taught -> fold (create-page)
        "цьому": [{"lemma": "це"}, {"lemma": "цей"}],       # UNCURATED homograph -> NEVER resolve -> skip
        "добридень": [],                                     # absent from VESUM (phrase) -> skip
        "брат": [{"lemma": "брат"}],                         # form is its own lemma -> skip
    }
    monkeypatch.setattr(gen, "verify_word", lambda w: fake.get(w, []))

    aliases = gen.build_alias_map(["брата", "вареники", "цьому", "добридень", "брат"])
    # create-cases now fold (tranche 2); uncurated homographs + phrases stay out
    assert aliases == {"брата": {"lemma": "брат"}, "вареники": {"lemma": "вареник"}}


def test_keep_standalone_forms_are_not_folded(monkeypatch) -> None:
    # може would otherwise fold (single VESUM lemma) but is kept standalone (lexicalized particle)
    monkeypatch.setattr(gen, "verify_word", lambda w: [{"lemma": "могти"}])
    aliases = gen.build_alias_map(["може", "могти"])
    assert "може" not in aliases
    assert "може" in gen._KEEP_STANDALONE_FORMS


def test_uncurated_homograph_is_never_auto_resolved(monkeypatch) -> None:
    # #2882: a true homograph with NO curated decision must NOT fold — "sole taught candidate"
    # mis-merges. `цьому` (це vs цей) was deliberately left out of _CURATED_HOMOGRAPHS
    # (genuinely ambiguous demonstrative, codex-flagged), so it must stay standalone.
    monkeypatch.setattr(gen, "verify_word", lambda w: [{"lemma": "це"}, {"lemma": "цей"}])
    aliases = gen.build_alias_map(["цьому"])
    assert "цьому" not in aliases
    assert "цьому" not in gen._CURATED_HOMOGRAPHS


def test_curated_homograph_resolves_by_gloss_decision(monkeypatch) -> None:
    # #2882 curated pass: сьома is the ORDINAL ("seventh"/"seven o'clock"), so it folds to
    # сьомий — NOT the cardinal сім. This is the exact mis-merge the auto-heuristic made.
    monkeypatch.setattr(gen, "verify_word", lambda w: [{"lemma": "сьомий"}, {"lemma": "сім"}])
    aliases = gen.build_alias_map(["сьома"])
    assert aliases["сьома"] == {"lemma": "сьомий"}


def test_curated_homograph_guard_rejects_lemma_absent_from_vesum(monkeypatch) -> None:
    # Safety net: a curated lemma must be one of VESUM's candidates for the form. If VESUM no
    # longer lists it (typo / dictionary drift), DO NOT fold — stay standalone, never mis-merge.
    monkeypatch.setattr(gen, "verify_word", lambda w: [{"lemma": "сім"}, {"lemma": "інше"}])
    aliases = gen.build_alias_map(["сьома"])  # curated→сьомий, but сьомий not in candidates
    assert "сьома" not in aliases


def test_build_alias_map_strips_stress_before_lookup(monkeypatch) -> None:
    seen: list[str] = []

    def fake_verify(word: str):
        seen.append(word)
        return [{"lemma": "брат"}]

    monkeypatch.setattr(gen, "verify_word", fake_verify)
    gen.build_alias_map(["бра́та", "брат"])
    assert "бра́та" not in seen  # stress was stripped before the VESUM query
    assert "брата" in seen
