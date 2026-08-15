"""Tests for scripts/verification/stress.py — the verify_stress oracle (#6515).

Covers the pinned design contract (issue #6515: design note + K3 review +
round-2 revision):
- любов/разом override hits (exact-lemma-only, per round-2 §4)
- a multi-stress heteronym (замок) enumerating every reading, incl. the
  true-homograph unresolvable_by_tags case (round-2 §3b)
- unknown-word not_found
- U+0301-marked input agree/disagree (input_mismatch, round-2 §3a)
- the four invalid_input error classes (round-2 §3d)
- a golden decode of the packed trie value for замок (round-2 §3c —
  guards the sanctioned private-API byte-layout parsing)
"""

from __future__ import annotations

from unittest.mock import patch

from scripts.verification.stress import (
    _load_trie,
    _parse_dictionary_value,
    _trie_value,
    verify_stress,
)

STRESS = "́"


class TestOverrides:
    def test_lyubov_override(self):
        result = verify_stress("любов")
        assert result["status"] == "ok"
        match = result["matches"][0]
        assert match["stressed_form"] == f"любо{STRESS}в"
        assert match["unstressed_form"] == "любов"
        assert match["vowel_index"] == 3
        assert match["override_applied"] is True
        assert match["required_tags"] == []

    def test_razom_override(self):
        result = verify_stress("разом")
        match = result["matches"][0]
        assert match["stressed_form"] == f"ра{STRESS}зом"
        assert match["override_applied"] is True

    def test_override_is_exact_lemma_only_not_inflected_forms(self):
        # "любові" is an inflected (dative/locative) form of "любов"; the
        # override is keyed by the bare lemma string only (round-2 §4) — an
        # inflected form must fall through to the raw dictionary answer,
        # not the override.
        result = verify_stress("любові")
        assert all(not m["override_applied"] for m in result["matches"])


class TestHeteronymEnumeration:
    def test_zamok_enumerates_every_reading(self):
        result = verify_stress("замок")
        assert result["status"] == "ambiguous"
        stressed_forms = {m["stressed_form"] for m in result["matches"]}
        assert stressed_forms == {f"за{STRESS}мок", f"замо{STRESS}к"}
        assert all(m["override_applied"] is False for m in result["matches"])
        assert all(m["required_tags"] for m in result["matches"])

    def test_zamok_true_homograph_unresolvable_by_tags(self):
        # The "castle" and "lock" nominative-noun readings carry
        # byte-identical required_tags — no tag combination the dictionary
        # offers can disambiguate them (round-2 §3b).
        result = verify_stress("замок", pos="NOUN", tags="Case=Nom,Number=Sing,Gender=Masc")
        assert result["status"] == "ambiguous"
        assert result["unresolvable_by_tags"] is True

    def test_zamok_resolves_with_full_required_tags(self):
        result = verify_stress("замок", pos="VERB", tags="Number=Sing")
        assert result["status"] == "ok"
        assert len(result["matches"]) == 1
        assert result["matches"][0]["stressed_form"] == f"замо{STRESS}к"

    def test_unresolvable_by_tags_false_for_unambiguous_word(self):
        result = verify_stress("село")
        assert result["status"] == "ok"
        assert result["unresolvable_by_tags"] is False


class TestNotFound:
    def test_unknown_word(self):
        # Valid Ukrainian-alphabet nonsense word, ≥2 vowels, not in the
        # dictionary.
        result = verify_stress("квазюрап")
        assert result["status"] == "not_found"
        assert result["matches"] == []


class TestInputMismatch:
    def test_agreeing_mark_is_false_not_omitted(self):
        result = verify_stress(f"за{STRESS}мок")
        agrees = [m for m in result["matches"] if m["vowel_index"] == 1]
        assert agrees and all(m["input_mismatch"] is False for m in agrees)

    def test_disagreeing_mark_is_true(self):
        result = verify_stress(f"за{STRESS}мок")
        disagrees = [m for m in result["matches"] if m["vowel_index"] == 3]
        assert disagrees and all(m["input_mismatch"] is True for m in disagrees)

    def test_no_mark_omits_the_key(self):
        result = verify_stress("замок")
        assert all("input_mismatch" not in m for m in result["matches"])

    def test_grave_accent_also_counts_as_a_mark(self):
        # U+0300 (combining grave) is the other mark #5375/#6832 normalizes.
        result = verify_stress("за̀мок")
        assert all("input_mismatch" in m for m in result["matches"])


class TestInvalidInput:
    def test_empty(self):
        result = verify_stress("")
        assert result["status"] == "invalid_input"
        assert "empty" in result["error"]

    def test_whitespace_only(self):
        result = verify_stress("   ")
        assert result["status"] == "invalid_input"

    def test_multi_word(self):
        result = verify_stress("добрий день")
        assert result["status"] == "invalid_input"
        assert "multi-word" in result["error"]

    def test_non_cyrillic(self):
        result = verify_stress("hello")
        assert result["status"] == "invalid_input"
        assert "Cyrillic" in result["error"]

    def test_single_syllable(self):
        result = verify_stress("я")
        assert result["status"] == "invalid_input"
        assert "single-syllable" in result["error"]

    def test_invalid_input_distinct_from_not_found(self):
        # A stray multi-word string must not be reported as "dictionary
        # doesn't know this word" (round-2 §3d) — status differs.
        assert verify_stress("добрий день")["status"] != verify_stress("квазюрап")["status"]


class TestVesumJoin:
    def test_attaches_single_unambiguous_vesum_match(self):
        mock_matches = [{"lemma": "замокти", "pos": "verb", "tags": "verb:perf:past:m"}]
        with patch("scripts.verification.vesum.verify_word", return_value=mock_matches):
            result = verify_stress("замок", pos="VERB", tags="Number=Sing")
        assert result["matches"][0]["vesum"] == mock_matches[0]

    def test_null_when_vesum_join_ambiguous(self):
        mock_matches = [
            {"lemma": "замок", "pos": "noun", "tags": "noun:inanim:m:v_naz:xp1"},
            {"lemma": "замок", "pos": "noun", "tags": "noun:inanim:m:v_naz:xp2"},
        ]
        with patch("scripts.verification.vesum.verify_word", return_value=mock_matches):
            result = verify_stress("замок", pos="NOUN", tags="Case=Nom,Number=Sing,Gender=Masc")
        assert all(m["vesum"] is None for m in result["matches"])

    def test_vesum_join_failure_does_not_crash_the_call(self):
        with patch("scripts.verification.vesum.verify_word", side_effect=FileNotFoundError("no db")):
            result = verify_stress("замок")
        assert result["status"] == "ambiguous"
        assert all(m["vesum"] is None for m in result["matches"])


class TestSourceInfo:
    def test_source_envelope_present_on_every_status(self):
        for word in ("замок", "квазюрап", "", "любов"):
            result = verify_stress(word)
            source = result["source"]
            assert source["dictionary"] == "ukrainian-word-stress (ULIF-derived)"
            assert source["trie_entries"] > 2_000_000
            assert len(source["digest"]) == 64  # sha256 hex


class TestStressGolden:
    """Golden-entry test for the sanctioned packed-value decode (round-2 §3c).

    Fails loudly if `ukrainian_word_stress` ever changes its trie packing
    format — the signal round-2 mandated as the safety net for using the
    package-private byte layout.
    """

    def test_zamok_golden_entry(self):
        trie = _load_trie()
        value = _trie_value(trie, "замок")
        assert value is not None
        readings = _parse_dictionary_value(value)
        as_sets = sorted((tuple(sorted(tags)), tuple(positions)) for tags, positions in readings)
        assert as_sets == sorted(
            [
                (tuple(sorted(["Number=Sing", "Case=Nom", "upos=NOUN", "Gender=Masc"])), (2,)),
                (tuple(sorted(["Number=Sing", "Case=Acc", "upos=NOUN", "Gender=Masc"])), (2,)),
                (tuple(sorted(["Number=Sing", "Case=Nom", "upos=NOUN", "Gender=Masc"])), (4,)),
                (tuple(sorted(["Number=Sing", "Case=Acc", "upos=NOUN", "Gender=Masc"])), (4,)),
                (tuple(sorted(["Number=Sing", "upos=VERB"])), (4,)),
            ]
        )
