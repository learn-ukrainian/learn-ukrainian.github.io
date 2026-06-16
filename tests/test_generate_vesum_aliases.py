"""Tests for the VESUM inflection→lemma alias generator (#2882)."""

import scripts.lexicon.generate_vesum_aliases as gen


def test_build_alias_map_gates(monkeypatch) -> None:
    # VESUM stub: form -> rows, keyed by the (stress-stripped) form the generator queries.
    fake = {
        "брата": [{"lemma": "брат"}],                       # single lemma -> fold
        "вареники": [{"lemma": "вареник"}],                 # single, lemma NOT taught -> fold (create-page)
        "біле": [{"lemma": "білий"}, {"lemma": "біль"}],    # homograph -> NEVER auto-resolve -> skip
        "добридень": [],                                     # absent from VESUM (phrase) -> skip
        "брат": [{"lemma": "брат"}],                         # form is its own lemma -> skip
    }
    monkeypatch.setattr(gen, "verify_word", lambda w: fake.get(w, []))

    aliases = gen.build_alias_map(["брата", "вареники", "біле", "добридень", "брат"])
    # create-cases now fold (tranche 2); homographs + phrases stay out
    assert aliases == {"брата": {"lemma": "брат"}, "вареники": {"lemma": "вареник"}}


def test_keep_standalone_forms_are_not_folded(monkeypatch) -> None:
    # може would otherwise fold (single VESUM lemma) but is kept standalone (lexicalized particle)
    monkeypatch.setattr(gen, "verify_word", lambda w: [{"lemma": "могти"}])
    aliases = gen.build_alias_map(["може", "могти"])
    assert "може" not in aliases
    assert "може" in gen._KEEP_STANDALONE_FORMS


def test_homograph_is_never_auto_resolved(monkeypatch) -> None:
    # #2882: even when only ONE candidate lemma is taught, a true homograph must NOT fold —
    # "sole taught candidate" mis-merges (сьома→сім not сьомий). Stay standalone.
    monkeypatch.setattr(gen, "verify_word", lambda w: [{"lemma": "сьомий"}, {"lemma": "сім"}])
    aliases = gen.build_alias_map(["сьома", "сім"])  # сім taught, сьомий not
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
