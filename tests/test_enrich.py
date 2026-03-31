"""Tests for V6 Step 7b: ENRICH — tabs, словник, videos, resources, dialogues."""

import sys
import typing
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.enrich import (
    _build_resources,
    _build_slovnyk,
    _build_video_embeds,
    _format_dialogues,
    enrich,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"


class TestSlovnyk:
    def test_required_words_with_translations(self):
        plan = {
            "vocabulary_hints": {
                "required": ["мама (mother)", "тато (father)", "вода (water)"],
            }
        }
        result = _build_slovnyk(plan)
        assert "Обов'язкові слова" in result
        assert "| **мама** | mother |" in result
        assert "| **тато** | father |" in result
        assert "| **вода** | water |" in result

    def test_recommended_words(self):
        plan = {
            "vocabulary_hints": {
                "required": ["мама (mother)"],
                "recommended": ["банк (bank)", "метро (metro)"],
            }
        }
        result = _build_slovnyk(plan)
        assert "Обов'язкові" in result
        assert "Рекомендовані" in result
        assert "| **банк** | bank |" in result

    def test_words_without_translation(self):
        plan = {"vocabulary_hints": {"required": ["привіт"]}}
        result = _build_slovnyk(plan)
        assert "| **привіт** |  |" in result

    def test_empty_vocab(self):
        plan = {"vocabulary_hints": {}}
        assert _build_slovnyk(plan) == ""

    def test_no_vocab_key(self):
        plan = {}
        assert _build_slovnyk(plan) == ""


    def test_build_slovnyk_markdown_formatting(self):
        """Test that build_slovnyk_markdown produces correct table output.

        Words with 2+ syllables get stress marks (e.g. літера -> лі́тера).
        Single-syllable words (звук) stay unchanged.
        """
        from build.vocab_gen import build_slovnyk_markdown

        entries = [
            {"word": "звук", "translation": "sound", "expression": False, "pos": "ім.", "gender": "ч."},
            {"word": "літера", "translation": "letter", "expression": False, "pos": "ім.", "gender": "ж."},
        ]
        expressions = [
            {"word": "Як справи?", "translation": "How are you?", "expression": True},
        ]
        result = build_slovnyk_markdown(entries, [], expressions)

        # Single-syllable word stays unchanged
        assert "| **звук** | sound | ім. | ч. |" in result
        # Multi-syllable word gets stress mark (лі́тера) — strip combining accent for comparison
        result_stripped = result.replace("\u0301", "")
        assert "| **літера** | letter | ім. | ж. |" in result_stripped
        assert "| **Як справи?** | How are you? |" in result
        assert "Вирази" in result


class TestM01ProseOnly:
    """Integration test: M01 .md file contains only prose (no TAB markers).

    #1124 moved enrichment to publish step. The .md now contains only the Урок prose.
    Словник, Зошит, Ресурси tabs are assembled at publish time from sources.
    """

    def _load_m01(self):
        content_path = CURRICULUM_ROOT / "a1" / "sounds-letters-and-hello.md"
        plan_path = CURRICULUM_ROOT / "plans" / "a1" / "sounds-letters-and-hello.yaml"
        if not content_path.exists() or not plan_path.exists():
            return None, None
        content = content_path.read_text("utf-8")
        plan = yaml.safe_load(plan_path.read_text("utf-8"))
        return content, plan

    def test_no_tab_markers_in_md(self):
        content, _plan = self._load_m01()
        if content is None:
            import pytest
            pytest.skip("M01 content/plan not available")

        assert "<!-- TAB:" not in content, (
            "M01 .md should not have TAB markers (enrichment moved to publish)"
        )

    def test_prose_has_content(self):
        content, _plan = self._load_m01()
        if content is None:
            import pytest
            pytest.skip("M01 content/plan not available")

        word_count = len(content.split())
        assert word_count >= 500, (
            f"M01 prose should have substantial content, found {word_count} words"
        )

    def test_no_videos_in_prose(self):
        content, _plan = self._load_m01()
        if content is None:
            import pytest
            pytest.skip("M01 content/plan not available")

        assert "YouTubeVideo" not in content, (
            "Videos should not be in .md prose — they belong in workbook activities at publish"
        )

    def test_vocabulary_yaml_exists(self):
        """Словник is built from vocabulary YAML at publish time."""
        vocab_path = CURRICULUM_ROOT / "a1" / "vocabulary" / "sounds-letters-and-hello.yaml"
        if not vocab_path.exists():
            import pytest
            pytest.skip("M01 vocabulary YAML not available")

        vocab_data = yaml.safe_load(vocab_path.read_text("utf-8"))
        assert isinstance(vocab_data, dict)
        entries = vocab_data.get("vocabulary", [])
        assert len(entries) >= 10, (
            f"M01 vocabulary YAML must have at least 10 entries, found {len(entries)}"
        )


class TestVideoEmbeds:
    def test_overview_video(self):
        plan = {
            "pronunciation_videos": {
                "overview": "https://www.youtube.com/watch?v=abc123",
                "credit": "Anna Ohoiko",
            }
        }
        result = _build_video_embeds(plan)
        assert '<YouTubeVideo client:only="react" url="https://www.youtube.com/watch?v=abc123"' in result
        assert "Anna Ohoiko" in result

    def test_bare_playlist_skipped(self):
        """A bare playlist with no overview or letter videos produces nothing."""
        plan = {
            "pronunciation_videos": {
                "playlist": "https://www.youtube.com/playlist?list=PLabc",
            }
        }
        result = _build_video_embeds(plan)
        assert result == ""

    def test_playlist_with_overview(self):
        """Playlist link IS included when there's also an overview video."""
        plan = {
            "pronunciation_videos": {
                "overview": "https://www.youtube.com/watch?v=abc",
                "playlist": "https://www.youtube.com/playlist?list=PLabc",
            }
        }
        result = _build_video_embeds(plan)
        assert "Full playlist" in result

    def test_per_letter_videos(self):
        plan = {
            "pronunciation_videos": {
                "vowels": {"А": "https://youtube.com/watch?v=a1"},
                "credit": "Ukrainian Lessons",
            }
        }
        result = _build_video_embeds(plan)
        assert 'label="Літера А — Ukrainian Lessons"' in result

    def test_no_videos(self):
        plan = {}
        assert _build_video_embeds(plan) == ""


class TestResources:
    def test_with_url(self):
        plan = {
            "references": [
                {"title": "ULP Episode 1", "url": "https://ukrainianlessons.com/episode1/", "notes": "Greetings"},
            ]
        }
        result = _build_resources(plan)
        assert "[ULP Episode 1](https://ukrainianlessons.com/episode1/)" in result
        assert "_Greetings_" in result

    def test_without_url(self):
        plan = {
            "references": [
                {"title": "Большакова Grade 1, p.24"},
            ]
        }
        result = _build_resources(plan)
        assert "- Большакова Grade 1, p.24" in result

    def test_no_references(self):
        plan = {}
        assert _build_resources(plan) == ""


class TestDialogueFormatting:
    def test_wraps_dialogue_block(self):
        content = "Some prose.\n\n— Привіт!\n— Як справи?\n— Добре!\n\nMore prose."
        result = _format_dialogues(content)
        assert '<div class="dialogue">' in result
        assert "— Привіт!" in result
        assert "</div>" in result

    def test_single_line_not_wrapped(self):
        content = "— Привіт!\n\nSome prose."
        result = _format_dialogues(content)
        assert ":::dialogue" not in result

    def test_no_dialogue(self):
        content = "Just regular prose without any dialogue."
        result = _format_dialogues(content)
        assert result == content


class TestEnrichIntegration:
    def test_full_enrichment_has_tabs(self):
        content = "## Section 1\n\nSome content.\n\n## Підсумок — Summary\n\nSummary here."
        plan = {
            "vocabulary_hints": {
                "required": ["мама (mother)", "тато (father)"],
            },
            "pronunciation_videos": {
                "overview": "https://www.youtube.com/watch?v=abc",
            },
            "references": [
                {"title": "Test ref", "url": "https://example.com"},
            ],
        }

        result, actions = enrich(content, plan)

        assert "slovnyk-table" in actions
        # video-embeds no longer in enrich — handled by watch-and-repeat activities
        assert "external-resources" in actions
        assert "tab-structure" in actions

        # Tab markers present
        assert "<!-- TAB:Урок -->" in result
        assert "<!-- TAB:Словник -->" in result
        assert "<!-- TAB:Зошит -->" in result
        assert "<!-- TAB:Ресурси -->" in result

    def test_workbook_placeholder(self):
        content = "## Section 1\n\nContent."
        plan = {"vocabulary_hints": {"required": ["тест (test)"]}}

        result, actions = enrich(content, plan)
        assert "workbook-placeholder" in actions
        assert "Розширені вправи" in result  # Ukrainian "Advanced exercises"

    def test_slovnyk_in_separate_tab(self):
        content = "## Section 1\n\nContent."
        plan = {"vocabulary_hints": {"required": ["мама (mother)"]}}

        result, _actions = enrich(content, plan)
        # Словник content appears AFTER the Словник tab marker
        slovnyk_tab = result.index("<!-- TAB:Словник -->")
        slovnyk_content = result.index("Обов'язкові слова")
        assert slovnyk_content > slovnyk_tab

    def test_videos_inline_in_urok_tab(self):
        content = "## Section 1\n\nContent.\n\n## Підсумок — Summary\n\nDone."
        plan = {
            "pronunciation_videos": {
                "overview": "https://www.youtube.com/watch?v=abc",
            },
        }

        result, _actions = enrich(content, plan)
        # Videos are NOT in the Урок tab — they're handled by workbook activities
        urok_content = result.split("<!-- TAB:Словник -->")[0] if "<!-- TAB:Словник -->" in result else result.split("<!-- TAB:Зошит -->")[0]
        assert "YouTubeVideo" not in urok_content, "Videos should not be in lesson tab"

    def test_m01_plan_enrichment(self):
        """Test with actual M01 plan data."""
        plan = {
            "vocabulary_hints": {
                "required": [
                    "мама (mother)", "тато (father)", "вода (water)",
                    "рука (hand)", "книга (book)", "школа (school)",
                    "привіт (hi, informal)", "як справи (how are you)",
                    "добре (fine, good)", "чудово (great, wonderful)",
                ],
                "recommended": [
                    "банк (bank)", "аптека (pharmacy)", "метро (metro)",
                    "пошта (post office)", "зупинка (bus stop)", "нормально (okay)",
                ],
            },
            "pronunciation_videos": {
                "overview": "https://www.youtube.com/watch?v=ksXIXj7CXwc",
                "playlist": "https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV",
            },
            "references": [
                {"title": "Большакова Grade 1 буквар, p.24",
                 "notes": "Голосні/приголосні taught through poems."},
                {"title": "ULP Season 1, Episode 1",
                 "url": "https://www.ukrainianlessons.com/episode1/",
                 "notes": "Привіт, Як справи?, response patterns."},
            ],
        }

        content = "## Звуки і літери\n\nContent.\n\n## Підсумок — Summary\n\nDone."
        result, actions = enrich(content, plan)

        assert len(actions) >= 3  # slovnyk, resources, tabs, workbook
        # All 10 required words in table
        assert result.count("| **") >= 10
        # Videos NOT in enrich output — handled by workbook activities
        urok_tab = result.split("<!-- TAB:Словник -->")[0]
        assert "YouTubeVideo" not in urok_tab
        # References
        assert "ukrainianlessons.com" in result
        # All 4 tabs
        assert "<!-- TAB:Урок -->" in result
        assert "<!-- TAB:Словник -->" in result
        assert "<!-- TAB:Зошит -->" in result
        assert "<!-- TAB:Ресурси -->" in result


# ---------------------------------------------------------------------------
# МійКлас integration in _build_resources (#1040)
# ---------------------------------------------------------------------------


class TestMiyklasResourceIntegration:
    """Tests for МійКлас grammar entries injected into _build_resources()."""

    _FAKE_INDEX: typing.ClassVar = [
        {
            "title": "Голосні й приголосні звуки",
            "tags": ["звуки", "голосні", "приголосні", "фонетика"],
            "url": "/p/ukrainska-mova/5-klas/fonetika/golosni",
            "grade": 5,
            "category": "phonetics",
        },
    ]

    def _patch_index(self):
        from unittest.mock import patch
        return patch(
            "build.miyklas._load_index",
            return_value=list(self._FAKE_INDEX),
        )

    def test_miyklas_section_appears_in_resources(self):
        """When plan grammar matches, МійКлас section appears in output."""
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        with self._patch_index():
            result = _build_resources(plan)
        assert "Граматика — Grammar (МійКлас)" in result
        assert "miyklas.com.ua" in result

    def test_miyklas_links_have_correct_format(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        with self._patch_index():
            result = _build_resources(plan)
        # Format: - [title](url) (source)
        assert "[МійКлас: Голосні й приголосні звуки](" in result
        assert "(miyklas.com.ua)" in result

    def test_miyklas_alone_produces_output(self):
        """Even with no refs/ext_resources, miyklas entries alone produce output."""
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
            # No "references" key — only miyklas matches
        }
        with self._patch_index():
            result = _build_resources(plan)
        assert result != ""
        assert "МійКлас" in result

    def test_miyklas_combined_with_refs(self):
        """МійКлас entries appear alongside regular references."""
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
            "references": [
                {"title": "Test Reference", "url": "https://example.com"},
            ],
        }
        with self._patch_index():
            result = _build_resources(plan)
        assert "Джерела — References" in result
        assert "Граматика — Grammar (МійКлас)" in result

    def test_miyklas_failure_does_not_break_resources(self):
        """If miyklas raises, _build_resources still works (try/except guards it)."""
        from unittest.mock import patch
        plan = {
            "references": [
                {"title": "Fallback ref", "url": "https://example.com"},
            ],
        }
        with patch(
            "build.miyklas.build_miyklas_resource_entries",
            side_effect=RuntimeError("index unavailable"),
        ):
            result = _build_resources(plan)
        # Regular refs still present
        assert "Fallback ref" in result

    def test_no_grammar_no_miyklas_section(self):
        """Plan without grammar field produces no МійКлас section."""
        plan = {
            "references": [
                {"title": "Only ref", "url": "https://example.com"},
            ],
        }
        with self._patch_index():
            result = _build_resources(plan)
        assert "МійКлас" not in result
