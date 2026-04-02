"""Tests for RAG ingestion tools — parsing, chunking, deduplication.

Tests pure functions only — no network calls, no Qdrant.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "rag"))
sys.path.insert(0, str(ROOT / "scripts" / "crawl"))


# ── scrape_ukrlib: guess_genre, chunk_text ──────────────────────

class TestUkrlibGuessGenre:
    def setup_method(self):
        from scrape_ukrlib import guess_genre
        self.guess_genre = guess_genre

    def test_poem_detected(self):
        assert self.guess_genre("Вірші про весну", "prose") == "poetry"

    def test_novel_detected(self):
        # "роман" maps to "prose" (not separate "novel" genre)
        assert self.guess_genre("Тигролови (роман)", "poetry") == "prose"

    def test_drama_detected(self):
        assert self.guess_genre("Назар Стодоля (п'єса)", "prose") == "drama"

    def test_biography_detected(self):
        assert self.guess_genre("Біографія Шевченка", "prose") == "biography"

    def test_default_returned(self):
        assert self.guess_genre("Якийсь текст", "prose") == "prose"


class TestUkrlibChunkText:
    def setup_method(self):
        from scrape_ukrlib import chunk_text
        self.chunk_text = chunk_text

    def test_empty_text(self):
        assert self.chunk_text("", "work", "http://example.com") == []

    def test_single_paragraph_below_min(self):
        # Short text below min_tokens (128) gets dropped
        text = "Це один абзац тексту."
        chunks = self.chunk_text(text, "test", "http://example.com")
        assert len(chunks) == 0

    def test_single_paragraph_above_min(self):
        text = "Український текст. " * 40  # ~760 chars > 128*4
        chunks = self.chunk_text(text, "test", "http://example.com")
        assert len(chunks) == 1

    def test_chunks_have_required_fields(self):
        text = "Перший абзац.\n\nДругий абзац."
        chunks = self.chunk_text(text, "work", "http://example.com")
        for chunk in chunks:
            assert "chunk_id" in chunk
            assert "text" in chunk
            assert "source_url" in chunk
            assert "token_count" in chunk

    def test_large_text_splits(self):
        # Create text larger than max_tokens
        paras = [f"Абзац номер {i}. " * 50 for i in range(20)]
        text = "\n\n".join(paras)
        chunks = self.chunk_text(text, "big", "http://example.com", max_tokens=200)
        assert len(chunks) > 1

    def test_chunk_ids_unique(self):
        paras = [f"Абзац {i}. " * 30 for i in range(10)]
        text = "\n\n".join(paras)
        chunks = self.chunk_text(text, "work", "http://example.com", max_tokens=100)
        ids = [c["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids))


# ── scrape_ukrlib: UkrlibTextExtractor ──────────────────────

class TestUkrlibTextExtractor:
    def setup_method(self):
        from scrape_ukrlib import UkrlibTextExtractor
        self.Extractor = UkrlibTextExtractor

    def test_basic_html(self):
        html = '<article class="prose"><p>Привіт світе!</p></article>'
        ext = self.Extractor()
        ext.feed(html)
        assert "Привіт світе!" in ext.get_text()

    def test_strips_noise_classes(self):
        html = '<article class="prose"><p>Зміст</p><div class="readalser">Реклама</div></article>'
        ext = self.Extractor()
        ext.feed(html)
        text = ext.get_text()
        assert "Зміст" in text
        assert "Реклама" not in text

    def test_ignores_content_outside_article(self):
        html = '<div><p>Навігація</p></div><article class="prose"><p>Контент</p></article>'
        ext = self.Extractor()
        ext.feed(html)
        text = ext.get_text()
        assert "Контент" in text
        assert "Навігація" not in text


# ── scrape_litopys: HTMLTextExtractor, find_next_link, chunk_text ──

class TestLitopysTextExtractor:
    def setup_method(self):
        from scrape_litopys import HTMLTextExtractor
        self.Extractor = HTMLTextExtractor

    def test_get_text_cleans_nav(self):
        ext = self.Extractor()
        ext.text_parts = ["Текст хроніки.\n‹\n›\n© 2001"]
        text = ext.get_text()
        assert "Текст хроніки." in text
        assert "‹" not in text
        assert "©" not in text

    def test_get_text_strips_dates(self):
        ext = self.Extractor()
        ext.text_parts = ["Важливий текст\n19.IX.2001 якесь"]
        text = ext.get_text()
        assert "Важливий текст" in text
        assert "19.IX.2001" not in text

    def test_get_parallel_text(self):
        ext = self.Extractor()
        ext.parallel_pairs = [
            ("Старий текст", "Сучасний переклад"),
            ("Інший оригінал", "Інший переклад"),
        ]
        text = ext.get_parallel_text()
        assert "Сучасний переклад" in text
        assert "Інший переклад" in text
        assert "Старий текст" not in text

    def test_get_original_text(self):
        ext = self.Extractor()
        ext.parallel_pairs = [("Оригінал", "Переклад")]
        text = ext.get_original_text()
        assert "Оригінал" in text
        assert "Переклад" not in text


class TestLitopysFindNextLink:
    def setup_method(self):
        from scrape_litopys import find_next_link
        self.find_next_link = find_next_link

    def test_finds_next_link(self):
        html = '<a href="page2.htm">Наступна</a>'
        result = self.find_next_link(html, "http://litopys.org.ua/page1.htm")
        assert result == "http://litopys.org.ua/page2.htm"

    def test_returns_none_when_missing(self):
        html = '<a href="page2.htm">Попередня</a>'
        result = self.find_next_link(html, "http://litopys.org.ua/page1.htm")
        assert result is None


class TestLitopysChunkText:
    def setup_method(self):
        from scrape_litopys import chunk_text
        self.chunk_text = chunk_text

    def test_empty_text(self):
        assert self.chunk_text("", "work", "http://example.com") == []

    def test_single_chunk_above_min(self):
        text = "Літописний текст про козаків. " * 30  # >128*4 chars
        chunks = self.chunk_text(text, "work", "http://example.com")
        assert len(chunks) == 1

    def test_single_chunk_below_min(self):
        chunks = self.chunk_text("Один абзац.", "work", "http://example.com")
        assert len(chunks) == 0  # Below min_tokens


# ── scrape_wikisource: is_skip_page, chunk_text ──────────────

class TestWikisourceIsSkipPage:
    def setup_method(self):
        from scrape_wikisource import is_skip_page
        self.is_skip_page = is_skip_page

    def test_category_skipped(self):
        assert self.is_skip_page("Категорія:Поезія")

    def test_author_skipped(self):
        assert self.is_skip_page("Автор:Іван Франко")

    def test_content_page_not_skipped(self):
        assert not self.is_skip_page("Кобзар/Заповіт")

    def test_dictionary_skipped(self):
        assert self.is_skip_page("Словарь української мови Б. Грінченка")


class TestWikisourceChunkText:
    def setup_method(self):
        from scrape_wikisource import chunk_text
        self.chunk_text = chunk_text

    def test_empty_text(self):
        assert self.chunk_text("", "Title", {}) == []

    def test_chunk_metadata(self):
        chunks = self.chunk_text("Текст вірша.", "Заповіт", {"author": "Шевченко"})
        assert len(chunks) == 1
        assert chunks[0]["author"] == "Шевченко"
        assert "ws_" in chunks[0]["chunk_id"]


# ── extract_text: split_into_sections, estimate_tokens, check_quality ──

class TestSplitIntoSections:
    def setup_method(self):
        from extract_text import split_into_sections
        self.split_into_sections = split_into_sections

    def test_no_headings(self):
        sections = self.split_into_sections("Just plain text.")
        assert len(sections) == 1
        assert sections[0]["title"] == "Вступ"
        assert sections[0]["level"] == 0

    def test_h1_sections(self):
        md = "# Розділ 1\n\nТекст першого розділу.\n\n# Розділ 2\n\nТекст другого."
        sections = self.split_into_sections(md)
        assert len(sections) == 2
        assert sections[0]["title"] == "Розділ 1"
        assert sections[0]["level"] == 1
        assert sections[1]["title"] == "Розділ 2"

    def test_h2_sections(self):
        md = "## Підрозділ\n\nДеталі тут."
        sections = self.split_into_sections(md)
        assert len(sections) == 1
        assert sections[0]["level"] == 2

    def test_intro_before_heading(self):
        md = "Вступний текст.\n\n# Перший\n\nЗміст."
        sections = self.split_into_sections(md)
        assert len(sections) == 2
        assert sections[0]["title"] == "Вступ"


class TestEstimateTokens:
    def setup_method(self):
        from extract_text import estimate_tokens
        self.estimate_tokens = estimate_tokens

    def test_empty(self):
        assert self.estimate_tokens("") == 1  # max(1, 0)

    def test_short_text(self):
        # 20 chars / 4 = 5 tokens
        assert self.estimate_tokens("а" * 20) == 5

    def test_returns_at_least_one(self):
        assert self.estimate_tokens("х") >= 1


class TestCheckQuality:
    def setup_method(self):
        from extract_text import check_quality
        self.check_quality = check_quality

    def test_empty_text(self):
        is_clean, ratio = self.check_quality("")
        assert not is_clean
        assert ratio == 0.0

    def test_ukrainian_text(self):
        is_clean, ratio = self.check_quality("Українська мова — гарна мова!")
        assert is_clean
        assert ratio > 0.5

    def test_ascii_only(self):
        is_clean, ratio = self.check_quality("This is English text only.")
        assert not is_clean


# ── crawl_ulp: extract_topics, get_season_info, get_fmu_level, parse_ulp_itunes ──

class TestExtractTopics:
    def setup_method(self):
        from crawl_ulp import extract_topics
        self.extract_topics = extract_topics

    def test_verb_topic(self):
        topics = self.extract_topics("Ukrainian Verbs: Conjugation")
        assert "grammar" in topics
        assert "verbs" in topics

    def test_no_match_returns_general(self):
        topics = self.extract_topics("Random episode title")
        assert topics == ["general"]

    def test_deduplication(self):
        # "verbs" and "conjugation" both add "grammar" — should appear only once
        topics = self.extract_topics("Verbs and conjugation")
        assert topics.count("grammar") == 1


class TestGetSeasonInfo:
    def setup_method(self):
        from crawl_ulp import get_season_info
        self.get_season_info = get_season_info

    def test_early_episode(self):
        season, level, focus = self.get_season_info(1)
        assert isinstance(season, int)
        assert level in ("A0", "A1", "A2", "B1", "B2")

    def test_unknown_episode(self):
        season, level, focus = self.get_season_info(9999)
        assert season == 6
        assert level == "B2"


class TestGetFmuLevel:
    def setup_method(self):
        from crawl_ulp import get_fmu_level
        self.get_fmu_level = get_fmu_level

    def test_a1(self):
        assert self.get_fmu_level(10) == "A1"

    def test_a2(self):
        assert self.get_fmu_level(30) == "A2"

    def test_b1(self):
        assert self.get_fmu_level(50) == "B1"


class TestParseUlpItunes:
    def setup_method(self):
        from crawl_ulp import parse_ulp_itunes
        self.parse_ulp_itunes = parse_ulp_itunes

    def test_pipe_format(self):
        episodes = [{"trackName": "ULP 4-55 | Рідна мова | Native language", "description": "", "releaseDate": "2023-01-01"}]
        result = self.parse_ulp_itunes(episodes)
        assert len(result) == 1
        assert result[0]["episode"] == 55
        assert result[0]["series"] == "ULP"

    def test_season3_format(self):
        episodes = [{"trackName": "ULP 3-30 Числа – Numbers", "description": "", "releaseDate": "2022-01-01"}]
        result = self.parse_ulp_itunes(episodes)
        assert len(result) == 1
        assert result[0]["episode"] == 30

    def test_skip_unparseable(self):
        episodes = [{"trackName": "Welcome to our podcast!", "description": "", "releaseDate": "2020-01-01"}]
        result = self.parse_ulp_itunes(episodes)
        assert len(result) == 0


class TestParseFmuItunes:
    def setup_method(self):
        from crawl_ulp import parse_fmu_itunes
        self.parse_fmu_itunes = parse_fmu_itunes

    def test_standard_format(self):
        episodes = [{"trackName": "FMU 1-15 | Weather in Ukrainian | 5 Minute Ukrainian", "description": "", "releaseDate": "2023-01-01"}]
        result = self.parse_fmu_itunes(episodes)
        assert len(result) == 1
        assert result[0]["episode"] == 15
        assert result[0]["series"] == "FMU"
