"""Tests for RAG ingestion tools — parsing, chunking, deduplication.

Tests pure functions only — no network calls, no Qdrant.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

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
        from scripts.rag.extract_text import split_into_sections

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
        from scripts.rag.extract_text import estimate_tokens

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
        from scripts.rag.extract_text import check_quality

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
        is_clean, _ratio = self.check_quality("This is English text only.")
        assert not is_clean


class TestTextbookExtractionReadiness:
    def test_explicit_pypdf_backend_preserves_page_order_and_source_marker(
        self, tmp_path
    ):
        from pypdf import PdfWriter

        from scripts.rag.extract_text import extract_pypdf_native_pages

        pdf_path = tmp_path / "fixture.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.add_blank_page(width=100, height=100)
        with pdf_path.open("wb") as handle:
            writer.write(handle)

        pages = extract_pypdf_native_pages(pdf_path)

        assert [page["page_number"] for page in pages] == [1, 2]
        assert all(
            page["layout"]["source_order"] == "pypdf page.extract_text"
            for page in pages
        )

    def test_pypdf_backend_accepts_blank_password_encryption(self, tmp_path):
        from pypdf import PdfWriter

        from scripts.rag.extract_text import extract_pypdf_native_pages

        pdf_path = tmp_path / "blank-password.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt(user_password="")
        with pdf_path.open("wb") as handle:
            writer.write(handle)

        pages = extract_pypdf_native_pages(pdf_path)

        assert [page["page_number"] for page in pages] == [1]
        assert pages[0]["text"] == ""

    def test_native_anomaly_detector_flags_exact_duplicate_lines_without_repair(self):
        from scripts.rag.extract_text import detect_native_text_anomalies

        repeated = "Рекомендовано Міністерством освіти і науки України"
        source = f"Звичайний рядок\n{repeated}\n{repeated}\nНаступний рядок"
        result = detect_native_text_anomalies(source)

        assert result["requires_visual_verification"] is True
        assert result["adjacent_duplicate_line_pairs"] == [
            {"lines": [2, 3], "text": repeated}
        ]
        assert source.splitlines() == [
            "Звичайний рядок",
            repeated,
            repeated,
            "Наступний рядок",
        ]

    def test_native_anomaly_detector_flags_truncated_duplicate(self):
        from scripts.rag.extract_text import detect_native_text_anomalies

        result = detect_native_text_anomalies("Числові дані\nислові дані")

        assert result["requires_visual_verification"] is True
        assert result["adjacent_first_character_truncation_pairs"] == [
            {"lines": [1, 2], "text": ["Числові дані", "ислові дані"]}
        ]

    def test_native_anomaly_detector_flags_repeated_span_inside_one_pdf_line(self):
        from scripts.rag.extract_text import detect_native_text_anomalies

        damaged = (
            "другої та на 25 см менша від третьої. Знайдіть сторо- "
            "та на 25 см менша від третьої. Знайдіть сторо- "
            "на 25 см менша від третьої. Знайдіть сторо-"
        )
        result = detect_native_text_anomalies(damaged)

        assert result["requires_visual_verification"] is True
        assert result["intraline_duplicate_token_spans"] == [
            {
                "line": 1,
                "token_spans": [[3, 8], [12, 17], [20, 25]],
                "text": "на 25 см менша від третьої.",
            }
        ]

    def test_native_anomaly_detector_does_not_flag_short_repetition_inside_one_line(self):
        from scripts.rag.extract_text import detect_native_text_anomalies

        result = detect_native_text_anomalies("так, так, так; ні, ні, ні")

        assert result["requires_visual_verification"] is False
        assert result["intraline_duplicate_token_spans"] == []

    def test_native_anomaly_detector_records_single_letter_run_without_blocking(self):
        from scripts.rag.extract_text import detect_native_text_anomalies

        result = detect_native_text_anomalies("Звичайний текст\nП б і і і І")

        assert result["requires_visual_verification"] is False
        assert result["total_findings"] == 0
        assert result["total_layout_observations"] == 1
        assert result["single_letter_token_runs"] == [
            {"line": 2, "token_span": [1, 6], "text": "П б і і і І"}
        ]

    def test_native_anomaly_detector_records_soft_hyphen_layout_marker_without_repair(self):
        from scripts.rag.extract_text import detect_native_text_anomalies

        source = "взаємопов’яза\u00ad них процесів"
        result = detect_native_text_anomalies(source)

        assert result["requires_visual_verification"] is False
        assert result["total_findings"] == 0
        assert result["total_layout_observations"] == 1
        assert result["soft_hyphen_whitespace_sequences"] == [
            {
                "start_offset": 13,
                "end_offset": 15,
                "codepoints": ["U+00AD", "U+0020"],
            }
        ]
        assert source == "взаємопов’яза\u00ad них процесів"

    def test_native_anomaly_detector_leaves_ordinary_text_unflagged(self):
        from scripts.rag.extract_text import detect_native_text_anomalies

        result = detect_native_text_anomalies(
            "Українська мова\nЦе звичайний текст підручника."
        )

        assert result["requires_visual_verification"] is False
        assert result["total_findings"] == 0

    def test_native_anomaly_detector_does_not_treat_roman_numerals_or_answer_lines_as_damage(self):
        from scripts.rag.extract_text import detect_native_text_anomalies

        result = detect_native_text_anomalies(
            "II школяр\nIII школяр\n________________________________________\n"
            "________________________________________"
        )

        assert result["requires_visual_verification"] is False
        assert result["total_findings"] == 0

    @pytest.mark.skipif(
        sys.platform != "darwin" or shutil.which("cupsfilter") is None,
        reason="Apple Vision OCR regression requires macOS and cupsfilter",
    )
    def test_apple_vision_ocr_keeps_upright_pdf_orientation(self, tmp_path):
        source = tmp_path / "upright-ukrainian.txt"
        source.write_text(
            "Українська мова. Це якісний шкільний підручник.\n" * 12,
            encoding="utf-8",
        )
        pdf = tmp_path / "upright-ukrainian.pdf"
        rendered = subprocess.run(
            ["cupsfilter", "-m", "application/pdf", str(source)],
            check=True,
            capture_output=True, timeout=30,
        )
        pdf.write_bytes(rendered.stdout)

        helper = ROOT / "scripts" / "rag" / "apple_vision_ocr.swift"
        completed = subprocess.run(
            [
                "swift",
                str(helper),
                "--pdf",
                str(pdf),
                "--pages",
                "1",
                "--mode",
                "ocr",
            ],
            check=True,
            capture_output=True,
            text=True, timeout=30,
        )
        text = json.loads(completed.stdout)["pages"][0]["text"]

        assert "Українська мова" in text
        assert "шкільний підручник" in text

    def test_mojibake_is_preserved_and_flagged_instead_of_repaired(self):
        from scripts.rag.extract_text import _native_page_record

        source = "Українська: äóøà. Îñü"
        page = _native_page_record(1, source)
        assert page["text"] == source
        assert page["layout"]["unicode_damage"]["suspicious_latin1_runs"] == 2

    def test_native_page_records_logical_text_anomalies_without_repair(self):
        from scripts.rag.extract_text import _native_page_record

        source = (
            "Рекомендовано Міністерством освіти і науки України\n"
            "Рекомендовано Міністерством освіти і науки України"
        )
        page = _native_page_record(1, source)

        assert page["text"] == source
        assert page["layout"]["native_text_anomalies"]["requires_visual_verification"] is True

    def test_native_exactness_audit_freezes_source_hash_and_exact_flagged_rows(self, tmp_path):
        from scripts.projects.open_model_data.textbook_native_exactness import audit_chunk_files

        root = tmp_path / "chunks"
        path = root / "grade-07" / "7-klas-test-author-2024.jsonl"
        path.parent.mkdir(parents=True)
        repeated = "Рекомендовано Міністерством освіти і науки України"
        rows = [
            {"chunk_id": "source_s0000", "page_start": 1, "page_end": 1, "text": "Чистий текст"},
            {
                "chunk_id": "source_s0001",
                "page_start": 2,
                "page_end": 2,
                "text": f"{repeated}\n{repeated}",
            },
        ]
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

        receipt, quarantined = audit_chunk_files(root)

        assert receipt["source_count"] == 1
        assert receipt["chunk_total"] == 2
        assert receipt["flagged_chunk_count"] == 1
        assert receipt["verified_flagged_chunk_count"] == 0
        assert receipt["unverified_flagged_chunk_count"] == 1
        assert receipt["flagged_page_count"] == 1
        assert receipt["sources"][0]["jsonl_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert quarantined == {path.stem: [rows[1]]}

    def test_visual_verification_marks_only_anomalous_chunk_without_changing_text(self, tmp_path):
        from scripts.projects.open_model_data.textbook_native_exactness import (
            apply_visual_verifications,
            audit_chunk_files,
            require_production_eligible_entry,
        )

        root = tmp_path / "chunks"
        path = root / "grade-00" / "source.jsonl"
        path.parent.mkdir(parents=True)
        repeated = "Цей довгий рядок помилково повторено у логічному шарі PDF."
        row = {
            "chunk_id": "source_s0000",
            "text": f"{repeated}\n{repeated}",
            "page_start": 2,
            "quality": {
                "visual_verification": {"status": "not_applicable", "evidence_id": None}
            },
        }
        path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

        receipt = apply_visual_verifications(
            root,
            {"source_s0000": "page-image:source-page-2;flash+grok"},
        )
        rewritten = json.loads(path.read_text(encoding="utf-8"))

        assert receipt["verified_chunk_count"] == 1
        assert rewritten["text"] == row["text"]
        assert rewritten["quality"]["visual_verification"] == {
            "status": "verified",
            "evidence_id": "page-image:source-page-2;flash+grok",
        }
        require_production_eligible_entry(rewritten, source_file=str(path))
        audit, _rows = audit_chunk_files(root)
        assert audit["flagged_chunk_count"] == 1
        assert audit["verified_flagged_chunk_count"] == 1
        assert audit["unverified_flagged_chunk_count"] == 0

    def test_visual_verification_refuses_clean_or_missing_chunk(self, tmp_path):
        from scripts.projects.open_model_data.textbook_native_exactness import (
            ExactnessAuditError,
            apply_visual_verifications,
        )

        root = tmp_path / "chunks"
        path = root / "grade-00" / "source.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps({"chunk_id": "clean", "text": "Чистий текст."}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        with pytest.raises(ExactnessAuditError, match="no current native-text anomaly"):
            apply_visual_verifications(root, {"clean": "page-image:1"})
        with pytest.raises(ExactnessAuditError, match="exist exactly once"):
            apply_visual_verifications(root, {"missing": "page-image:2"})

    def test_recorded_page_anomaly_survives_chunking_and_requires_verification(self, tmp_path):
        from scripts.projects.open_model_data.textbook_native_exactness import (
            apply_visual_verifications,
            audit_chunk_files,
        )

        root = tmp_path / "chunks"
        path = root / "grade-00" / "source.jsonl"
        path.parent.mkdir(parents=True)
        row = {
            "chunk_id": "source_s0000",
            "text": "Чистий фрагмент сторінки.",
            "page_start": 2,
            "quality": {
                "visual_verification": {"status": "required", "evidence_id": None}
            },
            "layout": {
                "native_text_anomalies": {
                    "requires_visual_verification": True,
                    "adjacent_duplicate_line_pairs": [{"text": "Повторений рядок"}],
                }
            },
        }
        path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

        audit, _rows = audit_chunk_files(root)
        assert audit["flagged_chunk_count"] == 1
        assert audit["unverified_flagged_chunk_count"] == 1
        assert audit["sources"][0]["findings"][0]["detection_scope"] == "recorded_page"

        apply_visual_verifications(root, {"source_s0000": "page-image:source-page-2"})
        verified, _rows = audit_chunk_files(root)
        assert verified["verified_flagged_chunk_count"] == 1
        assert verified["unverified_flagged_chunk_count"] == 0

    def test_legacy_single_letter_only_metadata_is_a_nonblocking_observation(self, tmp_path):
        from scripts.projects.open_model_data.textbook_native_exactness import (
            audit_chunk_files,
            require_production_eligible_entry,
        )

        root = tmp_path / "chunks"
        path = root / "grade-00" / "source.jsonl"
        path.parent.mkdir(parents=True)
        row = {
            "chunk_id": "source_s0000",
            "text": "У рівнянні позначено x y z q.",
            "layout": {
                "native_text_anomalies": {
                    "requires_visual_verification": True,
                    "single_letter_token_runs": [{"text": "x y z q"}],
                }
            },
        }
        path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

        require_production_eligible_entry(row, source_file="source")
        audit, _rows = audit_chunk_files(root)
        assert audit["flagged_chunk_count"] == 0

    def test_unverified_quarantine_packet_excludes_verified_findings(self, tmp_path):
        from scripts.projects.open_model_data.textbook_native_exactness import (
            apply_visual_verifications,
            audit_chunk_files,
            unverified_quarantine_packet,
        )

        root = tmp_path / "chunks"
        path = root / "grade-00" / "source.jsonl"
        path.parent.mkdir(parents=True)
        repeated = "Цей довгий рядок помилково повторено у логічному шарі PDF."
        rows = [
            {"chunk_id": "verified", "text": f"{repeated}\n{repeated}", "page_start": 2},
            {"chunk_id": "unverified", "text": f"{repeated}\n{repeated}", "page_start": 3},
        ]
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        apply_visual_verifications(root, {"verified": "page-image:2"})
        audit, flagged_rows = audit_chunk_files(root)

        packet, quarantine_rows = unverified_quarantine_packet(
            audit,
            flagged_rows,
            full_audit_sha256="a" * 64,
        )

        assert packet["flagged_chunk_count"] == 1
        assert packet["verified_flagged_chunk_count"] == 0
        assert packet["unverified_flagged_chunk_count"] == 1
        assert packet["derived_from_full_audit_sha256"] == "a" * 64
        assert [row["chunk_id"] for row in quarantine_rows["source"]] == ["unverified"]

    def test_quarantine_exclusion_archives_exact_damaged_row_without_repair(self, tmp_path):
        from scripts.projects.open_model_data.textbook_native_exactness import (
            apply_quarantine_exclusions,
            audit_chunk_files,
        )

        root = tmp_path / "chunks"
        quarantine = tmp_path / "quarantine"
        path = root / "grade-00" / "source.jsonl"
        path.parent.mkdir(parents=True)
        clean = {"chunk_id": "clean", "text": "Чистий текст."}
        repeated = "Цей довгий рядок помилково повторено у логічному шарі PDF."
        damaged = {
            "chunk_id": "damaged",
            "text": f"{repeated}\n{repeated}",
            "page_start": 7,
        }
        path.write_text(
            "".join(
                json.dumps(row, ensure_ascii=False) + "\n" for row in (clean, damaged)
            ),
            encoding="utf-8",
        )

        receipt = apply_quarantine_exclusions(
            root,
            {"damaged": "page-image:source-page-7;flash+grok"},
            quarantine_dir=quarantine,
        )

        assert receipt["excluded_chunk_count"] == 1
        retained = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        archived_path = quarantine / "grade-00" / "source.jsonl"
        archived = [
            json.loads(line) for line in archived_path.read_text(encoding="utf-8").splitlines()
        ]
        assert retained == [clean]
        assert archived == [damaged]
        audit, _rows = audit_chunk_files(root)
        assert audit["chunk_total"] == 1
        assert audit["flagged_chunk_count"] == 0

    def test_quarantine_exclusion_refuses_clean_or_missing_chunk(self, tmp_path):
        from scripts.projects.open_model_data.textbook_native_exactness import (
            ExactnessAuditError,
            apply_quarantine_exclusions,
        )

        root = tmp_path / "chunks"
        path = root / "grade-00" / "source.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps({"chunk_id": "clean", "text": "Чистий текст."}, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )

        with pytest.raises(ExactnessAuditError, match="no current native-text anomaly"):
            apply_quarantine_exclusions(
                root,
                {"clean": "page-image:1"},
                quarantine_dir=tmp_path / "quarantine",
            )
        with pytest.raises(ExactnessAuditError, match="exist exactly once"):
            apply_quarantine_exclusions(
                root,
                {"missing": "page-image:2"},
                quarantine_dir=tmp_path / "quarantine",
            )

    def test_ordinary_accented_text_is_not_flagged_as_encoding_damage(self):
        from scripts.rag.extract_text import _native_page_record

        source = "Українська мова — café naïve, déjà vu."
        page = _native_page_record(1, source)
        assert page["text"] == source
        assert page["layout"]["unicode_damage"]["suspicious_latin1_runs"] == 0

    def test_digital_detection_requires_sample_coverage(self, monkeypatch):
        from scripts.rag.extract_text import is_digital_pdf

        class FakeDoc:
            def __init__(self, pages):
                self.pages = pages

            def __len__(self):
                return len(self.pages)

            def __getitem__(self, index):
                return SimpleNamespace(get_text=lambda: self.pages[index])

            def close(self):
                return None

        sparse = ["front matter " * 12, "front matter " * 12] + [""] * 10
        adequate = ["content page " * 12] * 8 + [""] * 4
        monkeypatch.setitem(
            sys.modules,
            "pymupdf",
            SimpleNamespace(open=lambda _path: FakeDoc(sparse)),
        )
        assert not is_digital_pdf(Path("sparse.pdf"))
        monkeypatch.setitem(
            sys.modules,
            "pymupdf",
            SimpleNamespace(open=lambda _path: FakeDoc(adequate)),
        )
        assert is_digital_pdf(Path("adequate.pdf"))

    def test_hybrid_selection_ocr_only_targets_unusable_pages(self, monkeypatch):
        import scripts.rag.extract_text as extract

        native = [
            {
                "page_number": 1,
                "text": "Нативний текст сторінки один. " * 5,
                "extraction_mode": "native_text",
                "layout": {},
            },
            {"page_number": 2, "text": "", "extraction_mode": "native_text", "layout": {}},
            {
                "page_number": 3,
                "text": "Нативний текст сторінки три. " * 5,
                "extraction_mode": "native_text",
                "layout": {},
            },
            {"page_number": 4, "text": "коротко", "extraction_mode": "native_text", "layout": {}},
        ]
        monkeypatch.setattr(extract, "extract_native_pages", lambda _path: native)
        calls = []

        def fake_ocr(_path, pages):
            calls.append(pages)
            return [
                {
                    "page_number": page,
                    "text": f"Оцифрований текст сторінки {page}. " * 5,
                    "extraction_mode": "apple_vision_ocr",
                    "layout": {},
                    "ocr": {"observation_count": 4, "mean_confidence": 0.9},
                }
                for page in pages
            ]

        pages, receipt = extract.extract_page_records(Path("fixture.pdf"), ocr_runner=fake_ocr)
        assert calls == [[2, 4]]
        assert [page["extraction_mode"] for page in pages] == [
            "native_text",
            "apple_vision_ocr",
            "native_text",
            "apple_vision_ocr",
        ]
        assert receipt["status"] == "pass"
        assert receipt["content_page_count"] == 4

    def test_native_page_records_unicode_damage_without_guessing_replacements(self):
        from scripts.rag.extract_text import _native_page_record

        page = _native_page_record(
            7,
            "Назви\ufffd зображені тіла. Матеріали: \x90 папір \x90 ножиці.",
        )

        assert page["text"] == ("Назви\ufffd зображені тіла. Матеріали: \x90 папір \x90 ножиці.")
        assert page["layout"]["unicode_damage"] == {
            "replacement_characters": 1,
            "disallowed_controls": 2,
            "line_or_paragraph_separators": 0,
            "suspicious_latin1_runs": 0,
            "intra_cyrillic_dollar_symbols": 0,
        }

    def test_native_page_quarantines_unicode_line_separator_without_replacing_it(self):
        from scripts.rag.extract_text import _is_content_page_text, _native_page_record

        source_text = "Точний текст до роздільника.\u2028Точний текст після роздільника."
        page = _native_page_record(8, source_text)

        assert page["text"] == source_text
        assert page["layout"]["unicode_damage"]["line_or_paragraph_separators"] == 1
        assert _is_content_page_text(source_text) is False

    def test_jsonl_escapes_unicode_line_separator_without_changing_decoded_text(self, tmp_path):
        from scripts.rag.extract_text import _atomic_write_jsonl

        output = tmp_path / "chunks.jsonl"
        source_text = "Рядок один.\u2028Рядок два.\u2029Рядок три."

        _atomic_write_jsonl(output, [{"text": source_text}, {"text": "Наступний запис"}])

        physical_lines = output.read_text(encoding="utf-8").split("\n")
        assert len(physical_lines) == 3
        assert json.loads(physical_lines[0])["text"] == source_text
        assert json.loads(physical_lines[1])["text"] == "Наступний запис"

    def test_digital_book_does_not_ocr_or_chunk_damaged_native_page(self, monkeypatch):
        import scripts.rag.extract_text as extract

        native = [
            {
                "page_number": page,
                "text": (
                    "Чистий український текст сторінки. " * 5
                    if page < 5
                    else "Пошкоджений текст із символом \ufffd. " * 5
                ),
                "extraction_mode": "native_text",
                "layout": {},
            }
            for page in range(1, 6)
        ]
        monkeypatch.setattr(extract, "extract_native_pages", lambda _path: native)

        pages, receipt = extract.extract_page_records(
            Path("fixture.pdf"),
            ocr_runner=lambda _path, _pages: pytest.fail("OCR must not run"),
        )

        assert len(pages) == 5
        assert receipt["status"] == "pass"
        assert receipt["ocr_policy"] == "native_text_only_no_guess"
        assert receipt["ocr_requested_pages"] == []
        assert receipt["native_unusable_pages"] == [5]
        assert receipt["content_pages"] == [1, 2, 3, 4]

    def test_native_only_rejects_scanned_source_without_calling_ocr(self, monkeypatch):
        import scripts.rag.extract_text as extract

        native = [
            {
                "page_number": index,
                "text": "Точний нативний текст сторінки. " * 5 if index <= 2 else "",
                "extraction_mode": "native_text",
                "layout": {},
            }
            for index in range(1, 11)
        ]
        monkeypatch.setattr(extract, "extract_native_pages", lambda _path: native)

        with pytest.raises(extract.ExtractionQualityError) as caught:
            extract.extract_page_records(
                Path("fixture.pdf"),
                native_only=True,
                ocr_runner=lambda _path, _pages: pytest.fail("OCR must not run"),
            )

        assert caught.value.receipt["status"] == "fail"
        assert caught.value.receipt["ocr_policy"] == "native_only_rejected_scanned_source"
        assert caught.value.receipt["ocr_requested_pages"] == []
        assert caught.value.receipt["ocr_recovered_pages"] == []

    def test_quality_gate_fails_closed_and_leaves_only_failure_receipt(self, tmp_path, monkeypatch):
        import scripts.rag.extract_text as extract

        native = [
            {
                "page_number": index,
                "text": "Лише дві сторінки мають текст. " * 5 if index <= 2 else "",
                "extraction_mode": "native_text",
                "layout": {},
            }
            for index in range(1, 11)
        ]
        monkeypatch.setattr(extract, "extract_native_pages", lambda _path: native)
        output_dir = tmp_path / "chunks"
        with pytest.raises(extract.ExtractionQualityError) as caught:
            extract.process_pdf(
                Path("7-klas-test-author-2024-1.pdf"),
                output_dir=output_dir,
                ocr_runner=lambda _path, _pages: [],
            )
        assert caught.value.receipt["status"] == "fail"
        assert not list(output_dir.glob("*.jsonl"))
        assert list(output_dir.glob("*.receipt.json"))
        assert list(output_dir.glob(".*.tmp")) == []

    def test_quality_gate_rejects_long_low_confidence_garbled_ocr(self, monkeypatch):
        import scripts.rag.extract_text as extract

        native = [
            {"page_number": index, "text": "", "extraction_mode": "native_text", "layout": {}} for index in range(1, 11)
        ]
        monkeypatch.setattr(extract, "extract_native_pages", lambda _path: native)

        def garbled_ocr(_path, pages):
            return [
                {
                    "page_number": page,
                    "text": "N H O I S T R Latin lookalikes " * 8,
                    "extraction_mode": "apple_vision_ocr",
                    "layout": {},
                    "ocr": {"observation_count": 20, "mean_confidence": 0.4},
                }
                for page in pages
            ]

        with pytest.raises(extract.ExtractionQualityError) as caught:
            extract.extract_page_records(Path("fixture.pdf"), ocr_runner=garbled_ocr)

        assert caught.value.receipt["content_page_count"] == 0
        assert caught.value.receipt["ocr_quality_rejected_pages"] == list(range(1, 11))

    def test_rejected_ocr_page_is_audited_but_not_chunked(self, tmp_path, monkeypatch):
        import scripts.rag.extract_text as extract

        pages = [
            {
                "page_number": 1,
                "text": "N H O I S T R Latin lookalikes " * 8,
                "extraction_mode": "apple_vision_ocr",
                "layout": {},
                "ocr": {"observation_count": 20, "mean_confidence": 0.4},
            },
            *[
                {
                    "page_number": index,
                    "text": f"Чистий навчальний текст сторінки {index}. " * 8,
                    "extraction_mode": "native_text",
                    "layout": {},
                    "ocr": {},
                }
                for index in range(2, 11)
            ],
        ]
        receipt = extract._page_coverage_receipt(
            pages,
            total_pages=10,
            digital_coverage=extract.PageCoverage(
                total_pages=10,
                sampled_pages=tuple(range(1, 11)),
                readable_pages=tuple(range(2, 11)),
            ),
            ocr_requested_pages=[1],
            ocr_policy="scanned_source_candidate_requires_visual_verification",
            native_unusable_pages=[1],
            full_native_detection={"usable_page_count": 9, "coverage": 0.9},
        )
        assert receipt["status"] == "pass"
        assert receipt["ocr_quality_rejected_pages"] == [1]
        monkeypatch.setattr(
            extract,
            "extract_page_records",
            lambda _path, **_kwargs: (pages, receipt),
        )

        summary = extract.process_pdf(
            Path("9-klas-test-author-2026.pdf"),
            output_dir=tmp_path / "chunks",
        )
        rows = [json.loads(line) for line in Path(summary["output_file"]).read_text(encoding="utf-8").splitlines()]
        assert 1 not in {row["page_start"] for row in rows}
        assert summary["pages_recovered"] == 10
        assert summary["pages_chunked"] == 9

    def test_swift_subprocess_contract_orders_pages_and_preserves_metadata(self, tmp_path, monkeypatch):
        import scripts.rag.extract_text as extract

        helper = tmp_path / "apple_vision_ocr.swift"
        helper.write_text("// fixture helper", encoding="utf-8")
        payload = {
            "schema_version": "apple-vision-ocr.v1",
            "metadata": {
                "runtime": {"os_version": "fixture"},
                "recognizer": {"revision": 7},
            },
            "pages": [
                {
                    "page_number": 2,
                    "text": "Ось текст.",
                    "observation_count": 2,
                    "mean_confidence": 0.91,
                    "line_break_count": 1,
                },
                {
                    "page_number": 10,
                    "text": "Ще текст.",
                    "observation_count": 3,
                    "mean_confidence": 0.92,
                    "line_break_count": 0,
                },
            ],
        }
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(stdout=json.dumps(payload), stderr="")

        monkeypatch.setattr(extract.subprocess, "run", fake_run)
        pages = extract.run_apple_vision_ocr(Path("fixture.pdf"), [10, 2], helper_path=helper)
        assert calls[0][0][calls[0][0].index("--pages") + 1] == "2,10"
        assert calls[0][0][-2:] == ["--mode", "ocr"]
        assert calls[0][1]["capture_output"] is True
        assert [page["page_number"] for page in pages] == [2, 10]
        assert pages[0]["ocr"]["recognizer"] == {"revision": 7}

    def test_pdfkit_native_subprocess_contract_extracts_all_pages(self, tmp_path, monkeypatch):
        import scripts.rag.extract_text as extract

        helper = tmp_path / "apple_vision_ocr.swift"
        helper.write_text("// fixture helper", encoding="utf-8")
        payload = {
            "schema_version": "apple-vision-ocr.v1",
            "metadata": {"runtime": {"os_version": "fixture"}},
            "pages": [
                {"page_number": 1, "text": "Перша сторінка."},
                {"page_number": 2, "text": "Друга сторінка."},
            ],
        }
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(stdout=json.dumps(payload), stderr="")

        monkeypatch.setattr(extract.subprocess, "run", fake_run)
        pages = extract.run_apple_pdfkit_native(Path("fixture.pdf"), helper_path=helper)

        assert calls[0][0][-4:] == ["--pages", "all", "--mode", "native"]
        assert [page["page_number"] for page in pages] == [1, 2]
        assert pages[0]["layout"]["source_order"] == "PDFKit page.string"
        assert pages[0]["native_runtime"] == {"os_version": "fixture"}

    def test_pdfkit_native_spatial_requires_explicit_pages_and_keeps_candidate_unverified(
        self, tmp_path, monkeypatch
    ):
        import scripts.rag.extract_text as extract

        helper = tmp_path / "apple_vision_ocr.swift"
        helper.write_text("// fixture helper", encoding="utf-8")
        payload = {
            "schema_version": "apple-vision-ocr.v1",
            "metadata": {
                "runtime": {"os_version": "fixture"},
                "recognizer": {"request": "PDFSelection.selectionsByLine"},
            },
            "pages": [
                {
                    "page_number": 72,
                    "text": "150.° Накресліть довільний трикутник\nйого медіани.",
                }
            ],
        }
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(stdout=json.dumps(payload), stderr="")

        monkeypatch.setattr(extract.subprocess, "run", fake_run)
        pages = extract.run_apple_pdfkit_native_spatial(
            Path("fixture.pdf"), [72, 72], helper_path=helper
        )

        assert calls[0][0][-4:] == ["--pages", "72", "--mode", "native-spatial"]
        assert pages[0]["page_number"] == 72
        assert pages[0]["layout"]["source_order"] == "PDFKit selectionsByLine coordinate order"
        assert pages[0]["layout"]["native_text_anomalies"]["requires_visual_verification"] is False
        assert "quality" not in pages[0]

    def test_pdfkit_native_spatial_rejects_missing_page_scope(self, tmp_path):
        import scripts.rag.extract_text as extract

        helper = tmp_path / "apple_vision_ocr.swift"
        helper.write_text("// fixture helper", encoding="utf-8")
        with pytest.raises(extract.ExtractionError, match="positive one-based pages"):
            extract.run_apple_pdfkit_native_spatial(Path("fixture.pdf"), [], helper_path=helper)

    def test_legacy_markdown_ocr_uses_dependency_free_page_inventory(self, monkeypatch):
        import scripts.rag.extract_text as extract

        monkeypatch.setattr(
            extract,
            "extract_native_pages",
            lambda _path: [{"page_number": 1}, {"page_number": 2}],
        )
        calls = []

        def fake_ocr(_path, pages):
            calls.append(pages)
            return [{"page_number": page, "text": f"Текст {page}."} for page in pages]

        monkeypatch.setattr(extract, "run_apple_vision_ocr", fake_ocr)

        assert extract.extract_markdown_ocr(Path("fixture.pdf")) == (
            "## Сторінка 1\n\nТекст 1.\n\n## Сторінка 2\n\nТекст 2."
        )
        assert calls == [[1, 2]]

    def test_atomic_output_cleanup_on_replace_failure(self, tmp_path, monkeypatch):
        import scripts.rag.extract_text as extract

        output = tmp_path / "output.jsonl"
        monkeypatch.setattr(extract.os, "replace", lambda *_args: (_ for _ in ()).throw(OSError("boom")))
        with pytest.raises(OSError, match="boom"):
            extract._atomic_write(output, "fixture\n")
        assert not output.exists()
        assert list(tmp_path.glob(".*.tmp")) == []

    def test_process_writes_page_provenance_continuation_and_receipt(self, tmp_path, monkeypatch):
        import scripts.rag.extract_text as extract

        page_texts = [
            "Це сторінка без завершення " * 8,
            "продовжується на наступній сторінці. " * 8,
            "Завершена сторінка тексту. " * 8,
        ]
        page_records = [
            {
                "page_number": index,
                "text": text,
                "extraction_mode": "native_text" if index != 2 else "apple_vision_ocr",
                "layout": {"formula_structure": "lossy", "latex_preserved": False},
                "ocr": (
                    {"observation_count": 12, "mean_confidence": 0.88, "runtime": {"os_version": "fixture"}}
                    if index == 2
                    else {}
                ),
            }
            for index, text in enumerate(page_texts, start=1)
        ]
        receipt = {
            "schema_version": "textbook-page-coverage.v1",
            "status": "pass",
            "total_pages": 3,
            "content_page_count": 3,
            "content_page_coverage": 1.0,
            "ocr_requested_pages": [2],
        }
        monkeypatch.setattr(
            extract,
            "extract_page_records",
            lambda _path, **_kwargs: (page_records, receipt),
        )
        output_dir = tmp_path / "chunks"
        summary = extract.process_pdf(Path("3-klas-test-author-2024-1.pdf"), output_dir=output_dir)
        output_path = Path(summary["output_file"])
        rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
        assert {row["page_start"] for row in rows} == {1, 2, 3}
        assert rows[0]["continuation"] is True
        assert rows[1]["continuation_of_previous"] is True
        assert rows[1]["page_extraction_mode"] == "apple_vision_ocr"
        assert rows[1]["layout"]["latex_preserved"] is False
        assert rows[1]["ocr"]["observation_count"] == 12
        assert Path(summary["receipt_file"]).exists()
        assert list(output_dir.glob(".*.tmp")) == []

    def test_formula_layout_is_retained_and_flagged_instead_of_dropped(self, tmp_path, monkeypatch):
        import scripts.rag.extract_text as extract

        formula = "Розв’язання: 2x + 3 = 7; x = 2. " * 20
        monkeypatch.setattr(
            extract,
            "extract_page_records",
            lambda _path, **_kwargs: (
                [
                    {
                        "page_number": 27,
                        "text": formula,
                        "extraction_mode": "native_text",
                        "layout": {"formula_structure": "lossy"},
                    }
                ],
                {
                    "status": "pass",
                    "total_pages": 27,
                    "content_page_count": 27,
                    "content_page_coverage": 1.0,
                    "ocr_requested_pages": [],
                },
            ),
        )
        summary = extract.process_pdf(
            Path("7-klas-algebra-merzliak-2024-1.pdf"),
            output_dir=tmp_path / "chunks",
            symbol_noise_threshold=0.0,
        )
        row = json.loads(Path(summary["output_file"]).read_text(encoding="utf-8"))
        assert row["layout"]["formula_structure"] == "lossy"
        assert row["layout"]["formula_gate_override"] is True


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
        season, level, _focus = self.get_season_info(1)
        assert isinstance(season, int)
        assert level in ("A0", "A1", "A2", "B1", "B2")

    def test_unknown_episode(self):
        season, level, _focus = self.get_season_info(9999)
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
        episodes = [
            {"trackName": "ULP 4-55 | Рідна мова | Native language", "description": "", "releaseDate": "2023-01-01"}
        ]
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
        episodes = [
            {
                "trackName": "FMU 1-15 | Weather in Ukrainian | 5 Minute Ukrainian",
                "description": "",
                "releaseDate": "2023-01-01",
            }
        ]
        result = self.parse_fmu_itunes(episodes)
        assert len(result) == 1
        assert result[0]["episode"] == 15
        assert result[0]["series"] == "FMU"


# ── scrape_ukrlib: narod folk worklist (forgery/prose exclusion) ──


class TestNarodWorklist:
    """The /narod/ folk worklist crawls song genres wholesale but must NEVER
    surface the «Велесова книга» forgery or the prose казки misfiled under
    Народний епос (genre 11)."""

    def test_build_excludes_forgery_and_prose_includes_curated(self, monkeypatch):
        import scrape_ukrlib as su

        # Stub the live crawl so the test is network-free. Song genres only.
        fake = {
            2: [(0, "Жали женчики жали")],
            3: [(5, "Пісня про Байду")],
            5: [(2, "Як ще не було початку світа")],
            6: [(3, "Щедрик щедрик щедрівочка")],
        }
        monkeypatch.setattr(su, "_discover_narod_bookids", lambda gid: fake.get(gid, []))
        works = su._build_narod_worklist()
        pairs = {(w["genre_id"], w["bookid"]) for w in works}

        # Song genres crawled wholesale
        assert (2, 0) in pairs and (6, 3) in pairs
        # Curated genres (веснянки id=0 non-enumerable + epos думи) included
        assert (0, 0) in pairs  # Ой весна, весна (веснянка)
        assert (11, 1) in pairs  # Втеча трьох братів — authentic duma
        # Forgery + prose казки are NEVER included (not in the curated epos list)
        assert (11, 0) not in pairs  # «Велесова книга» forgery
        assert (11, 14) not in pairs  # «Летючий корабель» prose казка
        # Per-genre tags assigned
        tags = {w["genre"] for w in works}
        assert {"carol", "duma", "spring_song", "harvest_song", "historical_song"} <= tags

    def test_exclude_set_blocks_a_song_genre_listing(self, monkeypatch):
        import scrape_ukrlib as su

        # If a bad bookid ever appears in a song-genre listing, NAROD_EXCLUDE blocks it.
        monkeypatch.setattr(su, "_discover_narod_bookids", lambda gid: [(0, "good"), (99, "bad")] if gid == 2 else [])
        monkeypatch.setattr(su, "NAROD_EXCLUDE", {(2, 99)})
        pairs = {(w["genre_id"], w["bookid"]) for w in su._build_narod_worklist()}
        assert (2, 0) in pairs
        assert (2, 99) not in pairs
