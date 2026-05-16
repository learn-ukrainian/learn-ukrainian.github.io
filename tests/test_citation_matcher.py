"""Tests for ``scripts/build/citation_matcher.py``.

These tests pin the canonicalization that lets plan references written in
Cyrillic match textbook chunk-id-derived source records written in Latin.
Two real transliteration schemes coexist in the pipeline:

- Plan references use the BGN/PCGN-flavoured table in
  ``citation_matcher._CYRILLIC_TO_LATIN`` (х → "kh", й → "i").
- Chunk-ids and the ``source`` field synthesized from them in
  ``_parse_mcp_search_text_markdown`` use the Wikipedia-flavoured
  transliteration shipped by upstream textbook ingestion (х → "h", й → "j").

Without canonicalization, the two schemes produce different fold strings
for the same author and ``textbook_grounding`` silently rejects every
A1 module that cites a textbook with a "kh"-or-"j"-bearing author —
which is what happened on a1/m20 build 2026-05-16 23:01:56 (gate JSON:
``matched: [], missing: [Захарійчук Grade 1, p.24]``).
"""

from __future__ import annotations

from scripts.build.citation_matcher import (
    citation_keys_match,
    extract_citation_key,
    fold_citation_author,
)


class TestFoldCitationAuthor:
    """``fold_citation_author`` must collapse Cyrillic + Latin variants
    to one canonical form, *without* merging genuinely distinct authors."""

    def test_zaharijchuk_variants_canonicalize(self):
        # The a1/m20 regression: plan ref vs chunk-id-derived title.
        assert fold_citation_author("Захарійчук") == fold_citation_author(
            "Zaharijchuk"
        )

    def test_kh_and_h_collapse(self):
        # х can transliterate to either "kh" (BGN) or "h" (Wikipedia).
        assert fold_citation_author("Хитренко") == fold_citation_author("Khytrenko")
        assert fold_citation_author("Хитренко") == fold_citation_author("Hytrenko")

    def test_j_and_i_collapse(self):
        # й can transliterate to either "i" (BGN) or "j" (Wikipedia).
        # и/і can transliterate to either "y" or "i".
        assert fold_citation_author("Заболотний") == fold_citation_author("Zabolotny")
        assert fold_citation_author("Заболотний") == fold_citation_author("Zabolotnyi")

    def test_distinct_authors_stay_distinct(self):
        # The canonicalization must not be so aggressive that it merges
        # genuinely different names.
        assert fold_citation_author("Захарко") != fold_citation_author("Захарійчук")
        assert fold_citation_author("Авраменко") != fold_citation_author("Захарійчук")
        assert fold_citation_author("Вашуленко") != fold_citation_author("Авраменко")

    def test_already_latin_stays_stable(self):
        # Plain Latin input round-trips through the same pipeline.
        assert fold_citation_author("Avramenko") == fold_citation_author("Авраменко")


class TestCitationKeysMatchAcrossTransliterations:
    """End-to-end: a plan reference and a chunk-id-derived title that
    refer to the same textbook page band must match through both
    ``extract_citation_key`` and ``citation_keys_match``."""

    def test_m20_textbook_grounding_regression(self):
        # The synthesized title comes from ``_parse_mcp_search_text_markdown``
        # via ``Section: Сторінка 26`` — the gate's page_tolerance=5 covers
        # the chunk's Section-page-vs-textbook-page offset.
        plan_ref = "Захарійчук Grade 1, p.24"
        result_title = "Zaharijchuk Grade 1, p.26"

        plan_key = extract_citation_key(plan_ref)
        result_key = extract_citation_key(result_title)

        assert plan_key is not None
        assert result_key is not None
        assert citation_keys_match(result_key, plan_key)

    def test_page_outside_tolerance_does_not_match(self):
        # Page tolerance is 5 by default — a 10-page gap must not match.
        plan_key = extract_citation_key("Захарійчук Grade 1, p.24")
        far_key = extract_citation_key("Zaharijchuk Grade 1, p.40")
        assert plan_key is not None and far_key is not None
        assert not citation_keys_match(far_key, plan_key)

    def test_different_grade_does_not_match(self):
        plan_key = extract_citation_key("Захарійчук Grade 1, p.24")
        wrong_grade = extract_citation_key("Zaharijchuk Grade 2, p.24")
        assert plan_key is not None and wrong_grade is not None
        assert not citation_keys_match(wrong_grade, plan_key)
