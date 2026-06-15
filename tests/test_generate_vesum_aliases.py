"""Tests for the VESUM inflection→lemma alias generator (#2882)."""

import json
from pathlib import Path

import scripts.lexicon.generate_vesum_aliases as gen


def test_build_alias_map_applies_all_safety_gates(monkeypatch, tmp_path: Path) -> None:
    # VESUM stub: form -> rows. Keyed by the (stress-stripped) form the generator queries.
    fake = {
        "брата": [{"lemma": "брат"}],                       # single lemma, брат taught -> alias
        "біле": [{"lemma": "білий"}, {"lemma": "біль"}],    # ambiguous homograph -> skip
        "добридень": [],                                     # absent from VESUM (phrase) -> skip
        "вареники": [{"lemma": "вареник"}],                 # single, but вареник NOT taught -> skip
        "брат": [{"lemma": "брат"}],                         # form is its own lemma -> skip
    }
    monkeypatch.setattr(gen, "verify_word", lambda w: fake.get(w, []))

    manifest = tmp_path / "m.json"
    manifest.write_text(
        json.dumps(
            {"entries": [{"lemma": x} for x in ["брата", "біле", "добридень", "вареники", "брат"]]}
        ),
        encoding="utf-8",
    )

    aliases = gen.build_alias_map(manifest)
    assert aliases == {"брата": {"lemma": "брат"}}


def test_keep_standalone_forms_are_not_folded(monkeypatch, tmp_path: Path) -> None:
    # може would otherwise fold (single VESUM lemma могти, могти taught) but is kept standalone
    monkeypatch.setattr(gen, "verify_word", lambda w: [{"lemma": "могти"}])
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"entries": [{"lemma": "може"}, {"lemma": "могти"}]}), encoding="utf-8")

    aliases = gen.build_alias_map(manifest)
    assert "може" not in aliases
    assert "може" in gen._KEEP_STANDALONE_FORMS


def test_build_alias_map_strips_stress_before_lookup(monkeypatch, tmp_path: Path) -> None:
    seen: list[str] = []

    def fake_verify(word: str):
        seen.append(word)
        return [{"lemma": "брат"}]

    monkeypatch.setattr(gen, "verify_word", fake_verify)
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"entries": [{"lemma": "бра́та"}, {"lemma": "брат"}]}), encoding="utf-8")

    gen.build_alias_map(manifest)
    assert "бра́та" not in seen  # stress was stripped before the VESUM query
    assert "брата" in seen
