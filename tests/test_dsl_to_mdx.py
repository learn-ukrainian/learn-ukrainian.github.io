"""Tests for the DSL→MDX exercise converter."""

from __future__ import annotations

import json

import pytest

from scripts.generate_mdx.dsl_to_mdx import convert_dsl_to_mdx


class TestV6Quiz:
    """V6 :::quiz format."""

    def test_basic_quiz(self):
        dsl = (
            ':::quiz\n'
            'title: "Test quiz"\n'
            '---\n'
            '- q: "Що це?"\n'
            '  o: ["кіт", "собака", "птах"]\n'
            '  a: 0\n'
            ':::'
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        assert '<Quiz client:only="react"' in result
        assert '"question": "Що це?"' in result
        assert '"correct": true' in result

    def test_multi_question_quiz(self):
        dsl = (
            ':::quiz\n'
            'title: "Multi"\n'
            '---\n'
            '- q: "Q1"\n'
            '  o: ["a", "b"]\n'
            '  a: 1\n'
            '- q: "Q2"\n'
            '  o: ["c", "d"]\n'
            '  a: 0\n'
            ':::'
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        # Parse the JSON to verify structure
        match = __import__("re").search(r'questions=\{(.+)\}', result)
        assert match
        data = json.loads(match.group(1))
        assert len(data) == 2
        # Q1: answer index 1
        assert data[0]["options"][1]["correct"] is True
        assert data[0]["options"][0]["correct"] is False
        # Q2: answer index 0
        assert data[1]["options"][0]["correct"] is True

    def test_stray_quotes_cleaned(self):
        dsl = (
            ":::quiz\n"
            'title: "Test"\n'
            "---\n"
            "- q: \"'Що ми чуємо?\"\n"
            "  o: [\"зву́ки'\", \"лі́тери'\"]\n"
            "  a: 0\n"
            ":::"
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        # Stray quotes around values inside JSON strings should be stripped
        assert "Що ми чуємо?" in result
        assert "зву́ки" in result


class TestV6FillIn:
    """V6 :::fill-in format."""

    def test_basic_fill_in(self):
        dsl = (
            ':::fill-in\n'
            'title: "Fill in"\n'
            '---\n'
            '- sentence: "Привіт, як ___?"\n'
            '  answer: "справи"\n'
            ':::'
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        assert '<FillIn client:only="react"' in result
        assert '"sentence": "Привіт, як ___?"' in result
        assert '"answer": "справи"' in result


class TestV6MatchUp:
    """V6 :::match-up format."""

    def test_basic_match_up(self):
        dsl = (
            ':::match-up\n'
            'title: "Match"\n'
            '---\n'
            '- left: "кіт"\n'
            '  right: "cat"\n'
            '- left: "собака"\n'
            '  right: "dog"\n'
            ':::'
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        assert '<MatchUp client:only="react"' in result
        assert '"left": "кіт"' in result

    def test_stray_quotes_in_pairs(self):
        dsl = (
            ":::match-up\n"
            'title: "Match"\n'
            "---\n"
            "- left: \"'В\"\n"
            "  right: \"sounds like v'\"\n"
            ":::"
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        # Stray quotes stripped
        assert "В" in result
        assert "sounds like v" in result


class TestV6GroupSort:
    """V6 :::group-sort format."""

    def test_basic_group_sort(self):
        dsl = (
            ':::group-sort\n'
            'title: "Sort"\n'
            '---\n'
            'groups:\n'
            '  - name: "Голосні"\n'
            '    items: ["А", "О"]\n'
            '  - name: "Приголосні"\n'
            '    items: ["М", "К"]\n'
            ':::'
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        assert '<GroupSort client:only="react"' in result
        assert '"name": "Голосні"' in result
        assert '"items": ["А", "О"]' in result


class TestV6TrueFalse:
    """V6 :::true-false format."""

    def test_basic_true_false(self):
        dsl = (
            ':::true-false\n'
            'title: "True or false"\n'
            '---\n'
            '- statement: "Київ — столиця України"\n'
            '  answer: true\n'
            '- statement: "Москва — столиця України"\n'
            '  answer: false\n'
            ':::'
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        assert '<TrueFalse client:only="react"' in result
        assert '"answer": true' in result
        assert '"answer": false' in result


class TestLegacyFormat:
    """Legacy :::exercise[type] format still works."""

    def test_legacy_multiple_choice(self):
        dsl = (
            ':::exercise[multiple-choice]\n'
            'Choose the answer\n'
            '- [x] correct\n'
            '- [ ] wrong\n'
            ':::'
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        assert '<Quiz' in result

    def test_legacy_cloze(self):
        dsl = (
            ':::exercise[cloze]\n'
            'The {cat} sat on the mat\n'
            ':::'
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        assert '<FillIn' in result

    def test_legacy_match(self):
        dsl = (
            ':::exercise[match]\n'
            '| Left | Right |\n'
            '| --- | --- |\n'
            '| кіт | cat |\n'
            ':::'
        )
        result, count = convert_dsl_to_mdx(dsl)
        assert count == 1
        assert '<MatchUp' in result


class TestYouTubeConversion:
    """YouTube URL → component conversion."""

    def test_bare_youtube_url(self):
        text = "\nhttps://www.youtube.com/watch?v=abc123\n"
        result, count = convert_dsl_to_mdx(text)
        assert count == 1
        assert '<YouTubeVideo client:only="react"' in result
        assert 'url="https://www.youtube.com/watch?v=abc123"' in result

    def test_youtu_be_short_url(self):
        text = "\nhttps://youtu.be/xyz789\n"
        result, count = convert_dsl_to_mdx(text)
        assert count == 1
        assert 'url="https://www.youtube.com/watch?v=xyz789"' in result


class TestMixedContent:
    """Multiple exercises in one document."""

    def test_multiple_exercises(self):
        text = (
            "# Title\n\nSome text.\n\n"
            ':::quiz\ntitle: "Q"\n---\n- q: "Q1"\n  o: ["a","b"]\n  a: 0\n:::\n\n'
            "More text.\n\n"
            ':::fill-in\ntitle: "F"\n---\n- sentence: "___"\n  answer: "x"\n:::\n\n'
        )
        result, count = convert_dsl_to_mdx(text)
        assert count == 2
        assert '<Quiz' in result
        assert '<FillIn' in result
        # Prose preserved
        assert '# Title' in result
        assert 'Some text.' in result

    def test_non_exercise_admonition_preserved(self):
        text = ":::note\nThis is a note.\n:::"
        result, count = convert_dsl_to_mdx(text)
        assert count == 0
        assert ":::note" in result


class TestActualM01Content:
    """Integration test with the real M01 file format."""

    def test_m01_exercise_count(self):
        """The M01 file has 5 exercises: 1 quiz, 1 group-sort, 2 match-up, 1 fill-in."""
        import pathlib
        m01 = pathlib.Path(
            "curriculum/l2-uk-en/a1/sounds-letters-and-hello.md"
        )
        if not m01.exists():
            pytest.skip("M01 file not available")
        text = m01.read_text()
        result, count = convert_dsl_to_mdx(text)
        assert count == 5
        assert '<Quiz' in result
        assert '<GroupSort' in result
        assert '<MatchUp' in result
        assert '<FillIn' in result
        # No DSL blocks should remain
        assert ':::quiz' not in result
        assert ':::group-sort' not in result
        assert ':::match-up' not in result
        assert ':::fill-in' not in result
