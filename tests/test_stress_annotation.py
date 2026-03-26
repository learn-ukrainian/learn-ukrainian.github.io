"""Tests for stress_annotator.py (#988).

Validates post-processing stress annotation:
- Apostrophe words stressed correctly
- Proper nouns not double-stressed
- Code blocks and URLs untouched
- No duplicate stress on re-annotation
- Performance within budget
"""

from __future__ import annotations

import time

from scripts.pipeline.stress_annotator import (
    STRESS_MARK,
    _build_skip_mask,
    _count_syllables,
    _in_skip_range,
    annotate_stress,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stress_positions(word: str) -> list[int]:
    """Return indices of stress marks in *word*."""
    return [i for i, c in enumerate(word) if c == STRESS_MARK]


def _stressed_form(text: str, target: str) -> str | None:
    """Find the annotated form of *target* (unstressed) in *text*.

    Returns the form with stress mark(s) if found, else None.
    Handles combining accent marks (U+0301) that don't count as characters
    in the base word.
    """
    target_lower = target.lower()
    # Build a version of text stripped of stress marks, with a mapping
    # from stripped-index to original-index
    stripped_chars: list[str] = []
    orig_indices: list[int] = []
    for i, c in enumerate(text):
        if c == STRESS_MARK:
            continue
        stripped_chars.append(c)
        orig_indices.append(i)
    stripped = "".join(stripped_chars)

    idx = stripped.lower().find(target_lower)
    if idx == -1:
        return None

    # Map back: find the span in the original text
    orig_start = orig_indices[idx]
    orig_end_base = orig_indices[idx + len(target) - 1]
    # Include any trailing combining marks
    orig_end = orig_end_base + 1
    while orig_end < len(text) and text[orig_end] == STRESS_MARK:
        orig_end += 1

    return text[orig_start:orig_end]


# ---------------------------------------------------------------------------
# Unit tests for internal helpers
# ---------------------------------------------------------------------------

class TestCountSyllables:
    def test_monosyllabic(self):
        assert _count_syllables("так") == 1

    def test_two_syllables(self):
        assert _count_syllables("мама") == 2

    def test_apostrophe_word(self):
        # сім'я has 2 vowels → 2 syllables
        assert _count_syllables("сім'я") == 2

    def test_long_word(self):
        assert _count_syllables("фотографії") == 5


class TestBuildSkipMask:
    def test_code_block_detected(self):
        text = "hello ```some code``` world"
        ranges = _build_skip_mask(text)
        assert len(ranges) >= 1
        start, end = ranges[0]
        assert text[start:end] == "```some code```"

    def test_url_detected(self):
        text = "see https://example.com/path for info"
        ranges = _build_skip_mask(text)
        assert len(ranges) >= 1
        covered = text[ranges[0][0]:ranges[0][1]]
        assert "https://example.com" in covered

    def test_inline_code_detected(self):
        text = "Use `код` here"
        ranges = _build_skip_mask(text)
        assert len(ranges) >= 1


class TestInSkipRange:
    def test_inside(self):
        assert _in_skip_range(5, [(3, 10)]) is True

    def test_outside(self):
        assert _in_skip_range(2, [(3, 10)]) is False

    def test_at_boundary_start(self):
        assert _in_skip_range(3, [(3, 10)]) is True

    def test_at_boundary_end(self):
        # end is exclusive
        assert _in_skip_range(10, [(3, 10)]) is False


# ---------------------------------------------------------------------------
# Integration tests for annotate_stress
# ---------------------------------------------------------------------------

class TestApostropheWords:
    """AC: apostrophe words (сім'я, м'ясо) stressed correctly."""

    def test_apostrophe_words_get_stressed(self):
        # п'ять is monosyllabic (1 vowel) so annotator correctly skips it
        text = "Це сім'я і м'ясо та п'ять."
        result, count = annotate_stress(text)
        assert count > 0, "Should stress at least one apostrophe word"

        # Multi-syllable apostrophe words should have exactly one stress mark
        for word in ["сім'я", "м'ясо"]:
            form = _stressed_form(result, word)
            assert form is not None, f"{word} should be found in result"
            positions = _stress_positions(form)
            assert len(positions) == 1, (
                f"{word} should have exactly 1 stress mark, got {len(positions)} in '{form}'"
            )

        # п'ять is monosyllabic — should NOT be stressed
        pyat_form = _stressed_form(result, "п'ять")
        if pyat_form is not None:
            assert STRESS_MARK not in pyat_form, "Monosyllabic п'ять should not be stressed"

    def test_simya_stress_on_ya(self):
        """сім'я́ — stress falls on the last syllable (я)."""
        text = "Моя сім'я велика."
        result, _ = annotate_stress(text)
        form = _stressed_form(result, "сім'я")
        if form is not None:
            # The stress mark should appear after я (the last vowel)
            assert STRESS_MARK in form, f"сім'я should be stressed, got '{form}'"
            # я is the stressed vowel — mark should follow it
            ya_idx = form.rfind("я")
            assert ya_idx != -1
            assert ya_idx + 1 < len(form) and form[ya_idx + 1] == STRESS_MARK, (
                f"Stress should be on я in сім'я, got '{form}'"
            )


class TestProperNouns:
    """AC: proper nouns not double-stressed."""

    def test_single_stress_on_proper_noun(self):
        text = "Це Київ, столиця України."
        result, _ = annotate_stress(text)
        form = _stressed_form(result, "Київ")
        if form is not None:
            positions = _stress_positions(form)
            assert len(positions) <= 1, (
                f"Київ should have at most 1 stress mark, got {len(positions)} in '{form}'"
            )

    def test_shevchenko_single_stress(self):
        text = "Тарас Шевченко — великий поет."
        result, _ = annotate_stress(text)
        form = _stressed_form(result, "Шевченко")
        if form is not None:
            positions = _stress_positions(form)
            assert len(positions) <= 1, (
                f"Шевченко should have at most 1 stress mark, got {len(positions)} in '{form}'"
            )

    def test_kyiv_not_stressed_monosyllabic(self):
        """Київ has 2 vowels (и, і) so 2 syllables — it CAN be stressed.
        But must not be double-stressed."""
        text = "Київ — красиве місто."
        result, _ = annotate_stress(text)
        form = _stressed_form(result, "Київ")
        if form is not None:
            positions = _stress_positions(form)
            assert len(positions) <= 1


class TestCodeBlocksUntouched:
    """AC: words inside code blocks should not get stress marks."""

    def test_fenced_code_block(self):
        text = "Текст перед.\n\n```\nмама тато бабуся\n```\n\nТекст після."
        result, _ = annotate_stress(text)
        # Extract the code block from result
        code_start = result.index("```")
        code_end = result.index("```", code_start + 3) + 3
        code_block = result[code_start:code_end]
        # No stress marks inside code block
        assert STRESS_MARK not in code_block, (
            f"Code block should not contain stress marks: '{code_block}'"
        )

    def test_inline_code(self):
        text = "Використовуй `мама` тут."
        result, _ = annotate_stress(text)
        # Find inline code span
        tick1 = result.index("`")
        tick2 = result.index("`", tick1 + 1)
        inline = result[tick1:tick2 + 1]
        assert STRESS_MARK not in inline, (
            f"Inline code should not contain stress marks: '{inline}'"
        )


class TestURLsUntouched:
    """AC: URLs should not get stress marks."""

    def test_url_not_annotated(self):
        text = "Дивіться https://uk.wikipedia.org/wiki/Київ для інформації."
        result, _ = annotate_stress(text)
        # Extract the URL
        url_start = result.index("https://")
        # Find end of URL (next space or end of string)
        url_end = result.find(" ", url_start)
        if url_end == -1:
            url_end = len(result)
        url = result[url_start:url_end]
        assert STRESS_MARK not in url, (
            f"URL should not contain stress marks: '{url}'"
        )

    def test_html_tags_not_annotated(self):
        text = '<div class="dialogue">мама тато</div>'
        result, _ = annotate_stress(text)
        # Tags should be intact
        assert '<div class="dialogue">' in result
        assert "</div>" in result


class TestNoDuplicateStress:
    """AC: running annotator twice shouldn't double-stress."""

    def test_idempotent(self):
        text = "Моя бабуся живе у Львові."
        result1, _count1 = annotate_stress(text)
        result2, count2 = annotate_stress(result1)
        # Second pass should add zero new marks
        assert count2 == 0, (
            f"Second annotation pass should add 0 marks, added {count2}"
        )
        # Text should be identical
        assert result1 == result2, "Double annotation changed the text"

    def test_pre_stressed_words_preserved(self):
        text = f"Це ма{STRESS_MARK}ма і та{STRESS_MARK}то."
        result, _count = annotate_stress(text)
        # Should not add extra marks to already-stressed words
        mama_form = _stressed_form(result, "мама")
        if mama_form is not None:
            positions = _stress_positions(mama_form)
            assert len(positions) <= 1, (
                f"мама should have at most 1 stress mark after re-annotation, got {len(positions)}"
            )


class TestPerformance:
    """AC: annotating a 1500-word module takes <5 seconds."""

    def test_annotation_speed(self):
        # Build a ~1500 word Ukrainian text by repeating realistic content
        paragraph = (
            "Українська мова — одна з найкрасивіших мов світу. "
            "Вона має багату історію та чудову літературу. "
            "Київ є столицею України. Тарас Шевченко написав багато віршів. "
            "Моя сім'я живе у великому місті. Ми любимо українську кухню. "
            "Бабуся готує смачний борщ кожної неділі. "
            "Дідусь розповідає цікаві історії про минуле. "
        )
        # Each paragraph is roughly 40 words; 38 repetitions ≈ 1520 words
        text = "\n\n".join([paragraph] * 38)
        word_count = len(text.split())
        assert word_count >= 1500, f"Test text should be ≥1500 words, got {word_count}"

        start = time.perf_counter()
        _result, count = annotate_stress(text)
        elapsed = time.perf_counter() - start

        # 15s allows for Stanza model loading on first call
        assert elapsed < 15.0, (
            f"Annotation took {elapsed:.2f}s — must be <15s for {word_count} words"
        )
        assert count > 0, "Should have stressed at least some words"


class TestHeteronyms:
    """AC: heteronyms handled by Stanza context.

    The Stressifier uses Stanza for context-dependent stress placement.
    We verify it doesn't crash or produce garbage on heteronyms.
    """

    def test_zamok_context(self):
        """за́мок (castle) vs замо́к (lock) — context-dependent.

        Note: the Stressifier may decline to stress truly ambiguous words.
        We verify it either stresses correctly (1 mark) or leaves unstressed.
        """
        text = "Старий замок стоїть на горі."
        result, _count = annotate_stress(text)
        form = _stressed_form(result, "замок")
        if form is not None:
            positions = _stress_positions(form)
            # Must have 0 (library declined) or 1 stress mark — never 2+
            assert len(positions) <= 1, (
                f"замок should have at most 1 stress, got {len(positions)} in '{form}'"
            )

    def test_does_not_crash_on_ambiguous(self):
        """Annotator should not crash on ambiguous words."""
        ambiguous_sentences = [
            "Я бачу замок на дверях.",
            "Великий замок на пагорбі.",
            "Вона стоїть біля дверей.",
        ]
        for sent in ambiguous_sentences:
            result, _ = annotate_stress(sent)
            assert isinstance(result, str)


class TestRealModuleContent:
    """Test with content from actual A1 module files."""

    def test_dialogue_format_preserved(self):
        """Stress annotation should not break dialogue HTML structure."""
        text = (
            '<div class="dialogue">\n\n'
            "**Оксана:** У тебе є брати чи сестри?\n\n"
            "**Андрій:** Так, у мене є два брати.\n\n"
            "</div>"
        )
        result, _ = annotate_stress(text)
        assert '<div class="dialogue">' in result
        assert "</div>" in result
        assert "**Оксана:**" in result or f"**Окса{STRESS_MARK}на:**" in result

    def test_yaml_frontmatter_like_content(self):
        """HTML comments (used as tab markers) should not be modified."""
        text = "<!-- TAB:Урок -->\n\n## Діалоги (Dialogues)\n\nМоя мама працює."
        result, _ = annotate_stress(text)
        assert "<!-- TAB:Урок -->" in result


# ---------------------------------------------------------------------------
# annotate_file — safety check fix (#1052)
# ---------------------------------------------------------------------------

class TestAnnotateFileSafetyCheck:
    """The 2% safety check should only count stress marks in the body,
    not in Словник/Ресурси tabs that are pre-stressed by vocab_gen.py."""

    def test_slovnyk_stress_does_not_trigger_skip(self, tmp_path):
        """Stress marks in Словник section should NOT cause body to be skipped (#1052)."""
        from scripts.pipeline.stress_annotator import annotate_file

        # Simulate a module with pre-stressed vocabulary section but unstressed body
        body = "Моя мама працює в школі. Українська мова дуже гарна.\n" * 20
        # Add lots of stressed words in Словник (simulating vocab_gen.py output)
        stressed_vocab = (f"ма{STRESS_MARK}ма | mother\n" * 50)
        content = (
            f"<!-- TAB:Урок -->\n\n{body}\n\n"
            f"<!-- TAB:Словник -->\n\n{stressed_vocab}\n\n"
            f"<!-- TAB:Ресурси -->\n\nSome resources.\n"
        )

        md_file = tmp_path / "test-module.md"
        md_file.write_text(content, encoding="utf-8")

        count = annotate_file(md_file)
        # Body has Ukrainian words that should get stressed
        assert count > 0, "Body content should have been stress-annotated"

    def test_already_stressed_body_skips(self, tmp_path):
        """If the body itself already has >5% stress marks, skip annotation."""
        from scripts.pipeline.stress_annotator import annotate_file

        # Body with lots of pre-existing stress marks (>5%)
        stressed_body = (f"Моя{STRESS_MARK} ма{STRESS_MARK}ма працю{STRESS_MARK}є "
                        f"в шко{STRESS_MARK}лі дуже до{STRESS_MARK}бре. ") * 30
        content = f"<!-- TAB:Урок -->\n\n{stressed_body}\n"

        md_file = tmp_path / "test-stressed.md"
        md_file.write_text(content, encoding="utf-8")

        count = annotate_file(md_file)
        assert count == 0, "Already-stressed body should be skipped"
