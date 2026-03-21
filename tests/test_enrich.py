"""Tests for V6 Step 7b: ENRICH — словник, videos, resources, dialogues."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.enrich import (
    _build_resources,
    _build_slovnyk,
    _build_video_embeds,
    _format_dialogues,
    enrich,
)


class TestSlovnyk:
    def test_required_words_with_translations(self):
        plan = {
            "vocabulary_hints": {
                "required": ["мама (mother)", "тато (father)", "вода (water)"],
            }
        }
        result = _build_slovnyk(plan)
        assert "## Словник — Vocabulary" in result
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
        assert "### Required words" in result
        assert "### Recommended words" in result
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

    def test_playlist_link(self):
        plan = {
            "pronunciation_videos": {
                "playlist": "https://www.youtube.com/playlist?list=PLabc",
            }
        }
        result = _build_video_embeds(plan)
        assert "[Full playlist]" in result

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
        assert ":::dialogue" in result
        assert "— Привіт!" in result
        assert ":::" in result

    def test_single_line_not_wrapped(self):
        content = "— Привіт!\n\nSome prose."
        result = _format_dialogues(content)
        assert ":::dialogue" not in result

    def test_no_dialogue(self):
        content = "Just regular prose without any dialogue."
        result = _format_dialogues(content)
        assert result == content


class TestEnrichIntegration:
    def test_full_enrichment(self):
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
        assert "video-embeds" in actions
        assert "external-resources" in actions

        # Enrichments should appear BEFORE summary
        slovnyk_pos = result.index("Словник")
        summary_pos = result.index("Підсумок")
        assert slovnyk_pos < summary_pos

    def test_no_summary_appends_at_end(self):
        content = "## Section 1\n\nContent only."
        plan = {"vocabulary_hints": {"required": ["тест (test)"]}}

        result, actions = enrich(content, plan)
        assert "slovnyk-table" in actions
        assert result.endswith("\n")

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

        assert len(actions) >= 3
        # All 10 required words in table
        assert result.count("| **") >= 10
        # Video embed
        assert "ksXIXj7CXwc" in result
        # Playlist link
        assert "PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV" in result
        # References
        assert "ukrainianlessons.com" in result
