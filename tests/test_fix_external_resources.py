"""Tests for fix_external_resources.py — audit and clean external_resources.yaml."""

import sys
from pathlib import Path
from typing import ClassVar

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fix_external_resources import (
    audit,
    build_url_usage_map,
    clean,
    is_generic_homepage,
    is_youtube_channel_page,
    is_youtube_search_url,
    normalize_url,
)

# ── Detection functions ───────────────────────────────────────────────


class TestIsYoutubeSearchUrl:
    def test_search_results_page(self):
        assert is_youtube_search_url(
            "https://www.youtube.com/results?search_query=фільм+наймичка+1963"
        )

    def test_normal_video(self):
        assert not is_youtube_search_url(
            "https://www.youtube.com/watch?v=Vl5MAW3AYoU"
        )

    def test_empty(self):
        assert not is_youtube_search_url("")

    def test_other_site(self):
        assert not is_youtube_search_url("https://ukrainianlessons.com/results?search_query=x")


class TestIsGenericHomepage:
    def test_bare_youtube(self):
        assert is_generic_homepage("https://www.youtube.com/")

    def test_bare_domain_no_slash(self):
        assert is_generic_homepage("https://uacorpus.org")

    def test_domain_with_path(self):
        assert not is_generic_homepage("https://www.ukrainianlessons.com/episode1/")

    def test_unknown_domain_bare(self):
        # Not in _HOMEPAGE_DOMAINS, so not flagged
        assert not is_generic_homepage("https://example.com/")

    def test_empty(self):
        assert not is_generic_homepage("")


class TestIsYoutubeChannelPage:
    def test_at_channel(self):
        assert is_youtube_channel_page("https://www.youtube.com/@LearnUkrainian")

    def test_c_channel(self):
        assert is_youtube_channel_page("https://www.youtube.com/c/SomeChannel")

    def test_channel_id(self):
        assert is_youtube_channel_page("https://www.youtube.com/channel/UC123abc")

    def test_normal_video(self):
        assert not is_youtube_channel_page("https://www.youtube.com/watch?v=abc123")

    def test_non_youtube(self):
        assert not is_youtube_channel_page("https://example.com/@user")


class TestNormalizeUrl:
    def test_http_to_https(self):
        assert normalize_url("http://litopys.org.ua/") == "https://litopys.org.ua"

    def test_strip_trailing_slash(self):
        assert normalize_url("https://uacorpus.org/") == "https://uacorpus.org"

    def test_preserves_path(self):
        assert normalize_url("https://example.com/page") == "https://example.com/page"

    def test_strips_whitespace(self):
        assert normalize_url("  https://example.com  ") == "https://example.com"


# ── URL usage map ─────────────────────────────────────────────────────


class TestBuildUrlUsageMap:
    def test_counts_across_modules(self):
        resources = {
            "mod-a": {"articles": [{"url": "https://example.com/1", "title": "A"}]},
            "mod-b": {"articles": [{"url": "https://example.com/1", "title": "B"}]},
            "mod-c": {"youtube": [{"url": "https://example.com/2", "title": "C"}]},
        }
        usage = build_url_usage_map(resources)
        assert usage["https://example.com/1"] == 2
        assert usage["https://example.com/2"] == 1

    def test_same_url_in_multiple_categories_counted_once_per_module(self):
        resources = {
            "mod-a": {
                "articles": [{"url": "https://example.com/1", "title": "A"}],
                "websites": [{"url": "https://example.com/1", "title": "A"}],
            },
        }
        usage = build_url_usage_map(resources)
        assert usage["https://example.com/1"] == 1  # Same module = counted once

    def test_http_https_normalized(self):
        resources = {
            "mod-a": {"articles": [{"url": "http://example.com/page", "title": "A"}]},
            "mod-b": {"articles": [{"url": "https://example.com/page", "title": "B"}]},
        }
        usage = build_url_usage_map(resources)
        assert usage["https://example.com/page"] == 2


# ── Audit ─────────────────────────────────────────────────────────────


class TestAudit:
    FIXTURE: ClassVar[dict] = {
        "good-module": {
            "articles": [
                {"url": "https://www.ukrainianlessons.com/episode1/", "title": "Good"},
            ],
        },
        "bad-search": {
            "youtube": [
                {
                    "url": "https://www.youtube.com/results?search_query=test",
                    "title": "Search",
                },
            ],
        },
        "bad-homepage": {
            "websites": [{"url": "https://www.youtube.com/", "title": "YouTube"}],
        },
        "bad-channel": {
            "youtube": [
                {"url": "https://www.youtube.com/@SomeChannel", "title": "Channel"},
            ],
        },
        "bad-http": {
            "articles": [
                {"url": "http://litopys.org.ua/some/page", "title": "HTTP"},
            ],
        },
        "bad-dupe": {
            "articles": [
                {"url": "https://example.com/page", "title": "A"},
            ],
            "websites": [
                {"url": "https://example.com/page", "title": "A"},
            ],
        },
    }

    def test_detects_youtube_search(self):
        report = audit(self.FIXTURE)
        assert len(report["youtube_search"]) == 1
        assert report["youtube_search"][0][0] == "bad-search"

    def test_detects_generic_homepage(self):
        report = audit(self.FIXTURE)
        assert len(report["generic_homepage"]) == 1

    def test_detects_channel_page(self):
        report = audit(self.FIXTURE)
        assert len(report["channel_page"]) == 1

    def test_detects_http(self):
        report = audit(self.FIXTURE)
        assert len(report["http_entries"]) == 1

    def test_detects_within_module_dupes(self):
        report = audit(self.FIXTURE)
        assert len(report["within_module_dupes"]) == 1

    def test_counts_total(self):
        report = audit(self.FIXTURE)
        assert report["total_entries"] == 7
        assert report["total_modules"] == 6


# ── Clean ─────────────────────────────────────────────────────────────


class TestClean:
    def test_removes_search_urls(self):
        resources = {
            "mod": {
                "youtube": [
                    {
                        "url": "https://www.youtube.com/results?search_query=x",
                        "title": "Bad",
                    },
                    {
                        "url": "https://www.youtube.com/watch?v=abc123",
                        "title": "Good",
                    },
                ],
            },
        }
        cleaned, stats = clean(resources)
        assert stats["removed_search"] == 1
        assert len(cleaned["mod"]["youtube"]) == 1
        assert "watch" in cleaned["mod"]["youtube"][0]["url"]

    def test_removes_homepages(self):
        resources = {
            "mod": {
                "websites": [{"url": "https://www.youtube.com/", "title": "YT"}],
            },
        }
        cleaned, stats = clean(resources)
        assert stats["removed_homepage"] == 1
        assert "mod" not in cleaned  # Module removed (empty)
        assert stats["removed_empty_modules"] == 1

    def test_removes_channel_pages(self):
        resources = {
            "mod": {
                "youtube": [{"url": "https://www.youtube.com/@Channel", "title": "Ch"}],
            },
        }
        _cleaned, stats = clean(resources)
        assert stats["removed_channel"] == 1

    def test_removes_overused(self):
        # URL in 6 modules, max_uses=5
        resources = {
            f"mod-{i}": {
                "articles": [{"url": "https://overused.com/page", "title": "Same"}],
            }
            for i in range(6)
        }
        cleaned, stats = clean(resources, max_uses=5)
        assert stats["removed_overused"] == 6
        assert len(cleaned) == 0

    def test_deduplicates_within_module(self):
        resources = {
            "mod": {
                "articles": [{"url": "https://example.com/page", "title": "A"}],
                "websites": [{"url": "https://example.com/page", "title": "A"}],
            },
        }
        cleaned, stats = clean(resources)
        assert stats["removed_dupes"] == 1
        # First category (articles) keeps it
        assert "articles" in cleaned["mod"]
        assert "websites" not in cleaned["mod"]

    def test_normalizes_http(self):
        resources = {
            "mod": {
                "articles": [
                    {"url": "http://litopys.org.ua/some/page", "title": "Old"},
                ],
            },
        }
        cleaned, stats = clean(resources)
        assert stats["normalized_http"] == 1
        assert cleaned["mod"]["articles"][0]["url"].startswith("https://")

    def test_keeps_good_entries(self):
        resources = {
            "mod": {
                "articles": [
                    {"url": "https://www.ukrainianlessons.com/episode1/", "title": "Good"},
                ],
                "youtube": [
                    {"url": "https://www.youtube.com/watch?v=abc123", "title": "Video"},
                ],
            },
        }
        cleaned, stats = clean(resources)
        assert stats["total_removed"] == 0
        assert stats["total_remaining"] == 2
        assert len(cleaned["mod"]["articles"]) == 1
        assert len(cleaned["mod"]["youtube"]) == 1

    def test_empty_resources(self):
        cleaned, stats = clean({})
        assert cleaned == {}
        assert stats["total_removed"] == 0


# ── Integration ───────────────────────────────────────────────────────


class TestIntegration:
    def test_audit_on_real_file(self):
        """Smoke test: audit the actual external_resources.yaml."""
        resources_path = (
            Path(__file__).parent.parent
            / "docs"
            / "resources"
            / "external_resources.yaml"
        )
        if not resources_path.exists():
            pytest.skip("external_resources.yaml not found")

        data = yaml.safe_load(resources_path.read_text("utf-8"))
        resources = data.get("resources", {})
        report = audit(resources)

        assert report["total_entries"] > 0
        assert report["total_modules"] > 0
        # After #752 cleanup, no YouTube search URLs should remain
        assert len(report["youtube_search"]) == 0

    def test_clean_then_audit_shows_no_search_urls(self):
        """After cleaning, audit should find zero YouTube search URLs."""
        resources = {
            "mod-a": {
                "youtube": [
                    {
                        "url": "https://www.youtube.com/results?search_query=x",
                        "title": "Bad",
                    },
                    {
                        "url": "https://www.youtube.com/watch?v=good",
                        "title": "Good",
                    },
                ],
            },
            "mod-b": {
                "articles": [
                    {"url": "https://example.com/page", "title": "Nice"},
                ],
            },
        }
        cleaned, _ = clean(resources)
        report = audit(cleaned)
        assert len(report["youtube_search"]) == 0
        assert report["total_entries"] == 2
