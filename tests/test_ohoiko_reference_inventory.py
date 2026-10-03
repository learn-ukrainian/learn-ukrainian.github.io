"""The committed lexical inventory cannot contain workbook prose or glosses."""

import hashlib
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pytest
import yaml

from scripts.audit.source_inventory_intake import SourceInventoryError, read_source_inventory

pytestmark = pytest.mark.reads_content

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml"
LEXICAL = re.compile(r"[А-Яа-яІіЇїЄєҐґ’\- \u0301!?,.]+")


def test_committed_inventory_ip_fields_and_counts():
    payload = yaml.safe_load(INVENTORY.read_text())
    assert set(payload) == {"kind", "version", "sources"}
    source, = payload["sources"]
    assert set(source) == {"id", "source_family", "extraction_mode", "title", "path", "notes", "headwords"}
    rows = source["headwords"]
    assert len(rows) == 2043
    assert len({r["lemma"] for r in rows}) == 1897
    assert Counter(r["kind"] for r in rows) == {"word": 1652, "phrase": 92, "verb_pair_member": 299}
    assert_ip_fields(payload)
    assert len({r["pair"] for r in rows if "pair" in r}) == 147
    assert len(read_source_inventory(INVENTORY)) == len(rows)


def assert_ip_fields(payload):
    source, = payload["sources"]
    rows = source["headwords"]
    assert source["title"] == "A1 reference workbook lexical inventory"
    assert source["notes"] == 'Words-only extraction per the 2026-07-10 IP boundary (issues #4851/#4223). Only glossary headwords and appendix infinitives are retained; no English, explanations, unit sentences or conjugation columns. Printed pages 200–216 contain the glossary; 217–223 contain the verb table; 224–229 contain back matter. Apostrophes use U+2019. PDF Latin lookalikes are transcribed as the printed Cyrillic glyphs; acute vowels preserve their printed stress. Parenthetical pronoun subjects are omitted from conjugation variants. Book-labelled POS is preserved; entries without a printed abbreviation use unlabelled. Single-word vesum_pos lists every sorted unique POS of lemma-bound analyses, not inflections of other lemmas. Phrases retain per-token verification without vesum_pos. Proper-name vesum_tags retain only lemma-bound analyses with the prop marker. Appendix POS is verb. Verification states attest forms; an inflected form can be found with an empty lemma-bound vesum_pos. Missing means no VESUM form analysis, never a lookup failure.'
    assert hashlib.sha256("\n".join(sorted(r["lemma"] for r in rows if r["kind"] == "phrase")).encode()).hexdigest() == "4af46cb21aa3c8f4024bcea1a26e71f71025c46361cb111377b3244a5f35b239"
    for row in rows:
        assert set(row) <= {"lemma", "stressed", "pos", "kind", "locator", "variants", "pair", "vesum", "tokens", "vesum_pos", "vesum_tags"}
        assert {"lemma", "stressed", "pos", "kind", "locator"} <= set(row)
        for text in [row["lemma"], row["stressed"], *row.get("variants", [])]:
            assert LEXICAL.fullmatch(text), text
        assert row["lemma"] == unicodedata.normalize("NFC", row["lemma"]) and "\u0301" not in row["lemma"]
        assert re.fullmatch(r"p(?:20[0-9]|21[0-6]) Словничок|p(?:21[7-9]|22[0-3]) Додаток", row["locator"])
        assert row["pos"] in {"noun", "adj", "verb", "adv", "numr", "prep", "conj", "part", "intj", "noninfl", "unlabelled"}
        assert row["kind"] in {"word", "phrase", "verb_pair_member"}
        if row["kind"] == "phrase":
            assert "vesum" not in row and "vesum_pos" not in row and "vesum_tags" not in row and row["tokens"]
            for token in row["tokens"]:
                assert set(token) == {"form", "vesum"}
                assert LEXICAL.fullmatch(token["form"])
                assert token["vesum"] in {"found", "missing", "lookup_error"}
        else:
            assert " " not in row["lemma"]
            assert "tokens" not in row
            assert row["vesum"] in {"found", "missing", "lookup_error"}
            if row["pos"] == "unlabelled":
                assert row["vesum_pos"] == sorted(set(row["vesum_pos"]))
                if row["vesum"] != "found":
                    assert row["vesum_pos"] == []
                assert set(row["vesum_pos"]) <= {"noun", "adj", "verb", "adv", "numr", "prep", "conj", "part", "intj", "noninfl"}
        for tags in row.get("vesum_tags", []):
            assert re.fullmatch(r"[a-z0-9_]+(?::[a-z0-9_]+)*", tags) and "prop" in tags.split(":")
        if row["kind"] == "verb_pair_member":
            assert re.fullmatch(r"vp-\d{3,4}", row["pair"])
        else:
            assert "pair" not in row


def test_stressed_phrase_variants_and_two_perfectives_roundtrip():
    records = read_source_inventory(INVENTORY)
    phrase = next(r for r in records if r.lemma == "Добрий день!")
    assert phrase.stressed == "До́брий день!"
    assert [t["form"] for t in phrase.tokens] == ["Добрий", "день"]
    assert phrase.provenance_payload()["tokens"] == list(phrase.tokens)
    assert next(r for r in records if r.lemma == "мій").variants == ("моя", "моє", "мої")
    pair = next(r.pair for r in records if r.lemma == "вдягнути" and r.pair)
    assert {r.lemma for r in records if r.pair == pair} == {"вдягати", "вдягнути", "вдягти"}


@pytest.mark.parametrize("field,value", [
    ("stressed", "English"), ("kind", "sentence"), ("variants", "моя"),
    ("variants", ["a gloss"]), ("pair", "vp-x"), ("vesum", "failed"),
    ("tokens", []), ("tokens", "слово"), ("tokens", [{"form": "слово", "vesum": "found", "gloss": "word"}]),
    ("tokens", [{"form": "word", "vesum": "found"}]),
    ("tokens", [{"form": "слово", "vesum": "failed"}]),
    ("tokens", [{"form": "слово"}]),
    ("vesum_pos", "noun"), ("vesum_pos", ["gloss"]), ("vesum_pos", ["noun", "conj"]),
    ("vesum_pos", ["noun", "noun"]), ("vesum_pos", [{"pos": "noun"}]),
    ("vesum_tags", ["proper name"]), ("vesum_tags", ["noun:prop", "noun:prop"]),
    ("class", "intj"), ("class", []), ("source", "unattested"), ("page", 47),
])
def test_reader_rejects_invalid_metadata(tmp_path, field, value):
    source = {"id": "test", "source_family": "ohoiko", "extraction_mode": "curated_key_word",
              "headwords": [{"lemma": "слово", field: value}]}
    path = tmp_path / "inventory.yaml"
    path.write_text(yaml.safe_dump({"version": 1, "kind": "atlas_source_inventory", "sources": [source]}))
    with pytest.raises(SourceInventoryError):
        read_source_inventory(path)


@pytest.mark.parametrize("state", ["found", "missing", "lookup_error"])
def test_nested_verification_states_roundtrip(tmp_path, state):
    row = {"lemma": "Добрий день!", "kind": "phrase", "tokens": [{"form": "день", "vesum": state}]}
    path = tmp_path / "inventory.yaml"
    path.write_text(yaml.safe_dump({"version": 1, "kind": "atlas_source_inventory", "sources": [
        {"id": "test", "source_family": "ohoiko", "extraction_mode": "curated_key_word", "headwords": [row]}
    ]}, allow_unicode=True))
    record, = read_source_inventory(path)
    assert record.provenance_payload()["tokens"] == row["tokens"]


def test_reference_candidates_preserve_homonyms_and_legacy_pos():
    from dataclasses import replace

    from scripts.audit.source_inventory_intake import SourceInventoryRecord, source_inventory_candidates

    legacy = SourceInventoryRecord("мати", "test", "curated_key_word", "legacy.yaml", "row1", pos="verb")
    reference = replace(legacy, inventory_path="reference.yaml", kind="word", vesum="found")
    rows = [legacy, reference, replace(reference, pos="noun")]
    candidates = source_inventory_candidates(rows)
    assert len(candidates) == 2
    verb = next(c for c in candidates if c.pos == "verb")
    assert (verb.source_count, verb.frequency) == (2, 2)
    assert verb.source_provenance[-1]["kind"] == "word"
    adjective = replace(legacy, lemma="цікавий", pos="adjective")
    candidates = source_inventory_candidates([adjective, replace(reference, lemma="цікавий", pos="adj")])
    assert len(candidates) == 1 and candidates[0].pos == "adjective"
    assert candidates[0].source_count == 2
    with pytest.raises(SourceInventoryError, match="conflicting pos"):
        source_inventory_candidates([legacy, replace(legacy, pos="noun")])
    with pytest.raises(SourceInventoryError, match="conflicting gloss"):
        source_inventory_candidates([replace(legacy, gloss="one"), replace(reference, gloss="two")])


def test_phrase_conjugation_variant_keeps_its_object_and_verifies_optional_tokens():
    records = read_source_inventory(INVENTORY)
    phrase = next(r for r in records if r.lemma == "провести час")
    assert phrase.variants == ("провели час",)
    assert {"form": "провели", "vesum": "found"} in phrase.tokens
    optional = next(r for r in records if r.lemma.startswith("Що "))
    assert {"form": "в", "vesum": "found"} in optional.tokens
    assert {"form": "тебе", "vesum": "found"} in optional.tokens


@pytest.mark.parametrize("lemma,positions", [
    ("ми", ("noun",)), ("що", ("conj", "noun")), ("хто", ("noun",)), ("це", ("noun", "part")),
])
def test_committed_unlabelled_lemma_bound_pos(lemma, positions):
    record = next(r for r in read_source_inventory(INVENTORY) if r.lemma == lemma)
    assert record.pos == "unlabelled" and record.vesum_pos == positions
    assert record.provenance_payload()["vesum_pos"] == list(positions)


@pytest.mark.parametrize("lemma,positions", [
    ("ми", ("noun",)), ("що", ("conj", "noun")), ("хто", ("noun",)),
    ("це", ("noun", "part")), ("та", ("conj", "part")),
])
def test_unlabelled_candidates_augment_each_compatible_pos(lemma, positions):
    from dataclasses import replace

    from scripts.audit.source_inventory_intake import SourceInventoryRecord, source_inventory_candidates

    legacy = [SourceInventoryRecord(lemma, "fixture", "headword", "fixture", "row", pos=p, kind="word") for p in positions]
    unrelated = replace(legacy[0], pos="verb")
    reference = replace(legacy[0], kind="word", pos="unlabelled", vesum_pos=positions)
    candidates = source_inventory_candidates([*legacy, unrelated, reference])
    assert {c.pos: c.source_count for c in candidates} == {**{p: 2 for p in positions}, "verb": 1}
    for original in legacy:
        merged, = source_inventory_candidates([replace(original, kind=None), reference])
        assert merged.pos == original.pos and merged.source_count == 2
    standalone, = source_inventory_candidates([reference, reference])
    assert standalone.pos == "unlabelled" and standalone.source_count == 2


@pytest.mark.parametrize("state", ["found", "missing", "lookup_error"])
def test_unlabelled_pos_nested_roundtrip(tmp_path, state):
    positions = ["conj", "part"] if state == "found" else []
    row = {"lemma": "та", "kind": "word", "pos": "unlabelled", "vesum": state, "vesum_pos": positions}
    path = tmp_path / "inventory.yaml"
    path.write_text(yaml.safe_dump({"version": 1, "kind": "atlas_source_inventory", "sources": [
        {"id": "test", "source_family": "ohoiko", "extraction_mode": "curated_key_word", "headwords": [row]}
    ]}, allow_unicode=True))
    record, = read_source_inventory(path)
    assert record.vesum_pos == tuple(positions)
    assert record.provenance_payload()["vesum_pos"] == positions
    row.update(kind="phrase", tokens=[{"form": "та", "vesum": state}])
    path.write_text(yaml.safe_dump({"version": 1, "kind": "atlas_source_inventory", "sources": [
        {"id": "test", "source_family": "ohoiko", "extraction_mode": "curated_key_word", "headwords": [row]}
    ]}))
    with pytest.raises(SourceInventoryError, match="vesum_pos"):
        read_source_inventory(path)


def test_attested_inflection_does_not_borrow_its_lemma_pos():
    record = next(r for r in read_source_inventory(INVENTORY) if r.lemma == "був")
    assert record.pos == "unlabelled" and record.vesum == "found" and record.vesum_pos == ()


@pytest.mark.parametrize("mutation", ["phrase_sentence", "word_space", "title", "notes"])
def test_ip_scan_rejects_prose_and_metadata_drift(mutation):
    payload = yaml.safe_load(INVENTORY.read_text())
    source = payload["sources"][0]
    if mutation == "phrase_sentence":
        source["headwords"].append({"lemma": "Це коротке речення.", "kind": "phrase"})
    elif mutation == "word_space":
        next(r for r in source["headwords"] if r["kind"] == "word")["lemma"] = "два слова"
    else:
        source[mutation] += " copied prose"
    with pytest.raises(AssertionError):
        assert_ip_fields(payload)


def test_committed_phrase_segmentation_and_spelling_variants():
    from scripts.curriculum.validate.a1_reference import reference_spellings

    members, _ = reference_spellings()
    assert {"швидка допомога", "цього разу", "вчора", "учора", "бувай", "бувайте"} <= members
    assert not {"разу", "готівку", "речі", "вибачення", "цього"} & members
    rows = read_source_inventory(INVENTORY)
    assert next(r for r in rows if r.lemma == "швидка допомога").kind == "phrase"
    assert next(r for r in rows if r.lemma == "цього разу").kind == "phrase"
    farewell = next(r for r in rows if r.lemma == "бувай")
    assert (farewell.kind, farewell.pos, farewell.stressed, farewell.variants) == ("word", "intj", "Бува́й!", ("бувайте",))
    assert next(r for r in rows if r.lemma == "Що нового?").stressed == "Що ново́го?"
