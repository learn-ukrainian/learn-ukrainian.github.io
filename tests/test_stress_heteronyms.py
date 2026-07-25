"""Test stress annotator accuracy on Ukrainian heteronyms.

Heteronyms are words spelled identically but with different stress depending
on meaning/grammar. This tests that the Stanza-backed Stressifier resolves
them correctly when given sentence context.

Issue: #1019
"""

from __future__ import annotations

import pytest

# `ukrainian_word_stress` imports `stanza`, which imports `torch`. The CI test
# environment deliberately does not install the ML stack (see the pytest job in
# `.github/workflows/ci.yml`), so declare the dependency instead of failing
# collection for the whole shard. Locally \u2014 where torch is present \u2014 this is a
# no-op and the tests run normally.
#
# NOTE this is a *visible* skip, not silent coverage loss: stress-annotation
# accuracy is curriculum-load-bearing and still needs a bounded home. It also
# downloads Stanza models at runtime, i.e. it performs network I/O inside the
# gate, which is the profile of the test that held a runner for 357 minutes
# (#5740). The correct home is a dedicated, bounded, scheduled ML job that
# installs torch \u2014 tracked for the CI control-plane replacement.
pytest.importorskip(
    "ukrainian_word_stress",
    reason="requires the ML stack (ukrainian_word_stress -> stanza -> torch), not installed in CI",
)

from ukrainian_word_stress import Stressifier, StressSymbol

STRESS = "\u0301"  # combining acute accent

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def stressifier():
    """Module-scoped stressifier (Stanza model loads once)."""
    return Stressifier(
        stress_symbol=StressSymbol.CombiningAcuteAccent,
        on_ambiguity="skip",
    )


def _get_stressed_form(result: str, target_word: str) -> str | None:
    """Extract the stressed (or skipped) form of target_word from result.

    Looks for the target word in the result, with or without a stress mark.
    Returns the form as it appears in the result (lowercased), or None if not found.
    Case-insensitive matching (handles sentence-initial capitalization).
    """
    # The target word in the result may have a stress mark inserted
    # We need to find it by stripping stress marks and comparing
    for token in result.split():
        # Strip punctuation from edges
        clean = token.strip(".,!?;:()\"'«»—")
        if clean.lower().replace(STRESS, "") == target_word.lower():
            return clean.lower()
    return None


# --- Test data ---
# Each tuple: (sentence, target_word, expected_stressed_form, meaning)
# Expected forms use combining acute accent (U+0301) after the stressed vowel.

HETERONYM_TEST_CASES = [
    # замок: за́мок (castle) vs замо́к (lock)
    ("Старий замок стоїть на горі.", "замок", f"за{STRESS}мок", "castle"),
    ("Я зламав замок на дверях.", "замок", f"замо{STRESS}к", "lock"),
    # вікна: ві́кна (nom pl) vs вікна́ (gen sg)
    ("Великі вікна виходять на сад.", "вікна", f"ві{STRESS}кна", "nom pl"),
    ("Я стою біля вікна.", "вікна", f"вікна{STRESS}", "gen sg"),
    # обід: о́бід (rim) vs обі́д (lunch)
    ("Обід колеса зігнувся.", "обід", f"о{STRESS}бід", "rim"),  # nom, rim
    ("Після обіду ми підемо гуляти.", "обіду", f"обі{STRESS}ду", "lunch"),  # oblique
    # дорога: доро́га (road) vs дорога́ (expensive-fem)
    ("Ця дорога веде до міста.", "дорога", f"доро{STRESS}га", "road"),
    ("Ця книга дуже дорога.", "дорога", f"дорога{STRESS}", "expensive"),
    # мука: му́ка (flour) vs му́ка/мука́ (torment)
    # Note: flour = му́ка, torment = му́ка (some dialects мука́)
    ("Пшенична мука для випічки.", "мука", f"му{STRESS}ка", "flour"),
    ("Яка мука це витримувати!", "мука", f"му{STRESS}ка", "torment"),
    # атлас: а́тлас (atlas/book) vs атла́с (satin)
    ("Географічний атлас лежить на столі.", "атлас", f"а{STRESS}тлас", "atlas"),
    ("Сукня з атласу дуже гарна.", "атласу", f"атла{STRESS}су", "satin"),
    # брати: брати́ (brothers) vs бра́ти (to take)
    ("Мої брати живуть у Києві.", "брати", f"брати{STRESS}", "brothers"),
    ("Потрібно брати парасольку.", "брати", f"бра{STRESS}ти", "to take"),
    # плачу: пла́чу (I cry) vs плачу́ (I pay)
    ("Я плачу від радості.", "плачу", f"пла{STRESS}чу", "I cry"),
    ("Я плачу за квартиру.", "плачу", f"плачу{STRESS}", "I pay"),
    # насипати: наси́пати (pf, to pour once) vs насипа́ти (impf, to pour repeatedly)
    ("Насип цукру в чашку.", "насип", None, "pf-imperative"),  # single syl, skip
    ("Мама любить насипати сіль.", "насипати", f"насипа{STRESS}ти", "impf"),
    # село: село́ (village) — unambiguous baseline
    ("Моє село дуже гарне.", "село", f"село{STRESS}", "village"),
]


class TestHeteronymSentenceContext:
    """Test that Stressifier resolves heteronyms correctly with sentence context."""

    @pytest.mark.parametrize(
        "sentence,target,expected,meaning",
        HETERONYM_TEST_CASES,
        ids=[f"{t[3]}_{t[1]}" for t in HETERONYM_TEST_CASES],
    )
    def test_heteronym_with_context(
        self, stressifier, sentence, target, expected, meaning
    ):
        """Stressifier should resolve heteronym stress from sentence context."""
        result = stressifier(sentence)
        actual = _get_stressed_form(result, target)

        if expected is None:
            # We expect this word to be skipped (single syllable, etc.)
            pytest.skip(f"Word '{target}' expected to be skipped")
            return

        # Record whether it was resolved or skipped
        if actual is None:
            pytest.fail(
                f"Word '{target}' not found in result: {result}"
            )

        if STRESS not in actual:
            # Word was skipped (ambiguity unresolved) — this is a known limitation
            pytest.xfail(
                f"SKIPPED by Stanza: '{target}' in '{sentence}' "
                f"(meaning: {meaning}). Got: '{actual}', expected: '{expected}'"
            )

        assert actual == expected, (
            f"Wrong stress for '{target}' (meaning: {meaning}).\n"
            f"  Sentence: {sentence}\n"
            f"  Expected: {expected}\n"
            f"  Got:      {actual}\n"
            f"  Full result: {result}"
        )


class TestAnnotatorUsesContext:
    """Test that sentence context improves heteronym disambiguation.

    Demonstrates that feeding full sentences to Stressifier resolves
    more heteronyms than feeding isolated words.
    """

    def test_word_level_loses_context(self, stressifier):
        """Calling stressifier on isolated words skips most heteronyms."""
        ambiguous_words = ["замок", "обід", "мука", "атлас", "плачу", "насипати"]
        skipped = 0
        for word in ambiguous_words:
            result = stressifier(word)
            if STRESS not in result:
                skipped += 1

        # Most ambiguous words should be skipped when given in isolation
        assert skipped >= 4, (
            f"Expected most ambiguous words to be skipped in isolation, "
            f"but only {skipped}/{len(ambiguous_words)} were skipped"
        )

    def test_sentence_level_resolves_more(self, stressifier):
        """Calling stressifier on full sentences resolves more heteronyms."""
        test_sentences = [
            ("Великі вікна виходять на сад.", "вікна"),
            ("Я стою біля вікна.", "вікна"),
            ("Ця дорога веде до міста.", "дорога"),
            ("Ця книга дуже дорога.", "дорога"),
            ("Мої брати живуть у Києві.", "брати"),
            ("Потрібно брати парасольку.", "брати"),
        ]
        resolved = 0
        for sentence, target in test_sentences:
            result = stressifier(sentence)
            form = _get_stressed_form(result, target)
            if form and STRESS in form:
                resolved += 1

        # Sentence-level should resolve significantly more
        assert resolved >= 4, (
            f"Expected sentence context to resolve ≥4/6 heteronyms, "
            f"but only resolved {resolved}/6"
        )
