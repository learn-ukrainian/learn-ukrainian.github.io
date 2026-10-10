"""Unit and integration tests for scripts.ingest.usage_advice_ingest.

Tests:
- SQLite schemas creation and indexing for Glavcom and mova.ua
- Honest User-Agent defaults and overrides
- Stop on HTTP 403 circuit breaker (AccessDeniedError, zero retries)
- Exponential backoff and Retry-After handling on HTTP 429 and 5xx
- Incremental ingest mode (skipping existing URLs in database)
- Word-pair and usage-advice extraction across multiple categories
- JSON export helpers
- CLI argument parsing and error exits
"""

from __future__ import annotations

import email.utils
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from scripts.ingest.usage_advice_ingest import (
    DEFAULT_USER_AGENT,
    EXIT_HTTP_403_FORBIDDEN,
    MOVAUA_CREDIT,
    MOVNE_AUTHOR,
    AccessDeniedError,
    RateLimitOrServerError,
    SourceChoice,
    clean_movaua_title,
    discover_movaua_manifest,
    discover_movne_manifest,
    ensure_movaua_schema,
    ensure_movne_schema,
    export_movaua_summary_json,
    export_movne_summary_json,
    extract_movaua_usage_pairs,
    extract_movne_word_pairs,
    ingest_movaua,
    ingest_movne_pytannya,
    main,
    parse_args,
    parse_retry_after,
    polite_get,
    reextract_movaua,
    reextract_movne,
)


class TestUsageAdviceIngest(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")

    def tearDown(self) -> None:
        self.conn.close()

    def test_schema_creation(self) -> None:
        ensure_movne_schema(self.conn)
        tables = {r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        self.assertIn("movne_pytannya_issues", tables)
        self.assertIn("movne_word_pairs", tables)

        ensure_movaua_schema(self.conn)
        tables = {r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        self.assertIn("movaua_articles", tables)
        self.assertIn("movaua_usage_pairs", tables)

    def test_parse_retry_after(self) -> None:
        self.assertIsNone(parse_retry_after(None))
        self.assertIsNone(parse_retry_after(""))
        self.assertIsNone(parse_retry_after("invalid"))
        self.assertEqual(parse_retry_after("120"), 120.0)
        self.assertEqual(parse_retry_after("  45  "), 45.0)

        # HTTP Date format
        future_date = email.utils.formatdate(timeval=email.utils.time.time() + 60, usegmt=True)
        res = parse_retry_after(future_date)
        self.assertIsNotNone(res)
        self.assertGreater(res, 0.0)

    def test_polite_get_success(self) -> None:
        session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        mock_resp.text = "<html>OK</html>"
        session.get.return_value = mock_resp

        sleep_calls: list[float] = []
        resp = polite_get(
            session,
            "https://example.com/test",
            delay=1.5,
            sleep_fn=sleep_calls.append,
        )
        self.assertEqual(resp.status_code, 200)
        session.get.assert_called_once_with("https://example.com/test", timeout=20.0)
        self.assertEqual(sleep_calls, [1.5])

    def test_polite_get_circuit_breaker_403(self) -> None:
        session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 403
        session.get.return_value = mock_resp

        with self.assertRaises(AccessDeniedError):
            polite_get(session, "https://example.com/blocked", max_retries=5)

        # Must fail immediately on first attempt without retrying
        self.assertEqual(session.get.call_count, 1)

    def test_polite_get_backoff_429_and_5xx(self) -> None:
        session = MagicMock(spec=requests.Session)

        r429 = MagicMock(spec=requests.Response)
        r429.status_code = 429
        r429.headers = {"Retry-After": "5"}

        r503 = MagicMock(spec=requests.Response)
        r503.status_code = 503
        r503.headers = {}

        r200 = MagicMock(spec=requests.Response)
        r200.status_code = 200
        r200.text = "success"

        session.get.side_effect = [r429, r503, r200]
        sleep_calls: list[float] = []

        resp = polite_get(
            session,
            "https://example.com/retry",
            delay=1.0,
            retry_backoff=2.0,
            max_retries=3,
            sleep_fn=sleep_calls.append,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(session.get.call_count, 3)
        # Attempt 1: retry-after 5s; Attempt 2: delay*(2^1) = 2s; Final success: polite delay 1.0s
        self.assertEqual(sleep_calls, [5.0, 2.0, 1.0])

    def test_polite_get_exhaust_retries_raises(self) -> None:
        session = MagicMock(spec=requests.Session)
        r500 = MagicMock(spec=requests.Response)
        r500.status_code = 500
        r500.headers = {}
        session.get.return_value = r500

        with self.assertRaises(RateLimitOrServerError):
            polite_get(session, "https://example.com/500", delay=0.1, max_retries=2, sleep_fn=lambda _: None)

        self.assertEqual(session.get.call_count, 3)  # initial + 2 retries

    def test_extract_movne_word_pairs(self) -> None:
        html = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Оксана Коваленко: Як правильно казати: «на протязі року» чи «протягом року»?</p>
            <p>Правильно вживати: протягом року. Вислів «на протязі» в українській мові означає перебування на різкому струмені повітря.</p>
            <p>Отже, уникайте кальки «на протязі року».</p>

            <h2>• 2 •</h2>
            <p>Андрій: Чи можна вживати вислів «у кінці кінців»?</p>
            <p>Це суржик і калька з російського «в конце концов». Правильно казати: зрештою, врешті-решт або кінець кінцем.</p>
        </div>
        """
        pairs = extract_movne_word_pairs(1, "https://glavcom.ua/issue1.html", html)
        self.assertEqual(len(pairs), 2)

        p1 = pairs[0]
        self.assertEqual(p1["issue_number"], 1)
        self.assertEqual(p1["question_num"], 1)
        self.assertEqual(p1["reader_name"], "Оксана Коваленко")
        self.assertIn("на протязі року", p1["questioned_form"])
        self.assertEqual(p1["verdict_form"], "протягом року")
        self.assertEqual(p1["verdict_type"], "preferred")
        self.assertIn("струмені повітря", p1["reasoning"])

        p2 = pairs[1]
        self.assertEqual(p2["question_num"], 2)
        self.assertEqual(p2["reader_name"], "Андрій")
        self.assertIn("у кінці кінців", p2["questioned_form"])
        self.assertIn("зрештою", p2["verdict_form"])

    def test_extract_movaua_usage_pairs_various_categories(self) -> None:
        # 1. Anti-surzhyk
        p_surzhyk = extract_movaua_usage_pairs(
            article_id=10,
            url="https://ukr-mova.in.ua/antusurzhuk/bilshist-chleniv-chy-bilshist-chleny",
            section="antusurzhuk",
            title="Більшість членів чи більшість члени? | Мова – ДНК нації",
            image_alt="Більшість членів",
            article_text="Після слів більшість, меншість вживаємо родовий відмінок: більшість членів.",
        )
        self.assertEqual(len(p_surzhyk), 1)
        self.assertEqual(p_surzhyk[0]["pair_type"], "anti_surzhyk")
        self.assertEqual(p_surzhyk[0]["recommended_form"], "Більшість членів")

        # 2. Paronyms
        p_paronym = extract_movaua_usage_pairs(
            article_id=11,
            url="https://ukr-mova.in.ua/paronimu/adresa-i-adres",
            section="paronimu",
            title="Адреса і адрес. У чому різниця?",
            image_alt="",
            article_text="Адреса — місце проживання; адрес — письмове вітання.",
        )
        self.assertEqual(len(p_paronym), 1)
        self.assertEqual(p_paronym[0]["pair_type"], "paronym")
        self.assertEqual(p_paronym[0]["questioned_form"], "Адреса / адрес")

        # 3. Stress
        p_stress = extract_movaua_usage_pairs(
            article_id=12,
            url="https://ukr-mova.in.ua/nagolos/chornosem",
            section="nagolos",
            title="Наголос у слові «чорнозем»",
            image_alt="чорно́зем",
            article_text="Правильно наголошувати чорно́зем.",
        )
        self.assertEqual(len(p_stress), 1)
        self.assertEqual(p_stress[0]["pair_type"], "stress")
        self.assertEqual(p_stress[0]["questioned_form"], "чорнозем")
        self.assertEqual(p_stress[0]["recommended_form"], "чорно́зем")

        # 4. Idioms
        p_idiom = extract_movaua_usage_pairs(
            article_id=13,
            url="https://ukr-mova.in.ua/frazeologizmu/bitu-bayduku",
            section="frazeologizmu",
            title="Значення фразеологізму «бити байдики»",
            image_alt="Ледарювати",
            article_text="Бити байдики означає нічого не робити, марнувати час.",
        )
        self.assertEqual(len(p_idiom), 1)
        self.assertEqual(p_idiom[0]["pair_type"], "idiom")
        self.assertEqual(p_idiom[0]["recommended_form"], "бити байдики")

    def test_clean_movaua_title(self) -> None:
        self.assertEqual(
            clean_movaua_title("Пів яблука чи пів'яблука | Мова – ДНК нації"),
            "Пів яблука чи пів'яблука",
        )
        self.assertEqual(
            clean_movaua_title("Наголос у слові «жалюзі» | Мова - ДНК нації"),
            "Наголос у слові «жалюзі»",
        )

    def test_ingest_movne_incremental(self) -> None:
        manifest = [
            {"issue_number": 1, "url": "https://glavcom.ua/issue1.html", "title": "Випуск 1"},
            {"issue_number": 2, "url": "https://glavcom.ua/issue2.html", "title": "Випуск 2"},
            {"issue_number": 3, "url": "https://glavcom.ua/issue3.html", "title": "Випуск 3"},
        ]

        session = MagicMock(spec=requests.Session)
        r = MagicMock(spec=requests.Response)
        r.status_code = 200
        r.text = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Читач: Як правильно?</p>
            <p>Правильно: так.</p>
        </div>
        """
        session.get.return_value = r

        # Pass 1: limit 2 items
        stats1 = ingest_movne_pytannya(
            self.conn,
            session=session,
            manifest=manifest,
            incremental=True,
            limit=2,
            delay=0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(stats1.total_manifest, 3)
        self.assertEqual(stats1.cached_existing, 0)
        self.assertEqual(stats1.fetched_new, 2)
        self.assertEqual(session.get.call_count, 2)

        # Pass 2: incremental pass with full manifest
        session.get.reset_mock()
        stats2 = ingest_movne_pytannya(
            self.conn,
            session=session,
            manifest=manifest,
            incremental=True,
            delay=0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(stats2.total_manifest, 3)
        self.assertEqual(stats2.cached_existing, 2)
        self.assertEqual(stats2.fetched_new, 1)  # Only issue 3 fetched!
        self.assertEqual(session.get.call_count, 1)

    def test_ingest_movaua_incremental(self) -> None:
        manifest = [
            {"url": "https://ukr-mova.in.ua/item1", "section": "antusurzhuk"},
            {"url": "https://ukr-mova.in.ua/item2", "section": "paronimu"},
        ]
        session = MagicMock(spec=requests.Session)
        r = MagicMock(spec=requests.Response)
        r.status_code = 200
        r.text = "<html><title>Title | Мова – ДНК нації</title><div class='text'>Body</div></html>"
        session.get.return_value = r

        stats1 = ingest_movaua(
            self.conn,
            session=session,
            manifest=manifest,
            incremental=True,
            limit=1,
            delay=0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(stats1.fetched_new, 1)
        self.assertEqual(session.get.call_count, 1)

        # Run 2: Item 1 cached, only Item 2 fetched
        session.get.reset_mock()
        stats2 = ingest_movaua(
            self.conn,
            session=session,
            manifest=manifest,
            incremental=True,
            delay=0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(stats2.cached_existing, 1)
        self.assertEqual(stats2.fetched_new, 1)
        self.assertEqual(session.get.call_count, 1)

    def test_export_summaries_json(self, tmp_path: Path | None = None) -> None:
        ensure_movne_schema(self.conn)
        ensure_movaua_schema(self.conn)

        self.conn.execute(
            """
            INSERT INTO movne_pytannya_issues
            (id, url, issue_number, title, date, description, raw_html, article_text, content_sha256, fetched_at)
            VALUES (1, 'https://example.com/1', 1, 'Issue 1', '2026-01-01', 'Desc', '<html></html>', 'Text', 'sha1', '2026-01-01')
            """
        )
        self.conn.execute(
            """
            INSERT INTO movne_word_pairs
            (issue_id, issue_number, question_num, reader_name, question_raw, questioned_form, verdict_form, verdict_type, reasoning, url, created_at)
            VALUES (1, 1, 1, 'Олена', 'Як сказати?', 'калька', 'норма', 'preferred', 'пояснення', 'https://example.com/1', '2026-01-01')
            """
        )

        import tempfile

        with tempfile.TemporaryDirectory() as td:
            movne_out = Path(td) / "movne.json"
            data = export_movne_summary_json(self.conn, movne_out)
            self.assertEqual(data["author"], MOVNE_AUTHOR)
            self.assertEqual(data["total_issues"], 1)
            self.assertEqual(data["total_pairs"], 1)
            self.assertTrue(movne_out.exists())

            movaua_out = Path(td) / "movaua.json"
            data_m = export_movaua_summary_json(self.conn, movaua_out)
            self.assertEqual(data_m["credit"], MOVAUA_CREDIT)
            self.assertTrue(movaua_out.exists())

    def test_extract_movne_word_pairs_contrastive_nepravylno_first(self) -> None:
        html = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Олександр: Чи вживається слово «слідуючий»?</p>
            <p>Неправильно казати «слідуючий». Правильно — «наступний».</p>
        </div>
        """
        pairs = extract_movne_word_pairs(1, "https://glavcom.ua/issue_contrastive.html", html)
        self.assertEqual(len(pairs), 1)
        p = pairs[0]
        self.assertEqual(p["verdict_form"], "наступний")
        self.assertEqual(p["verdict_type"], "preferred")
        self.assertEqual(p["questioned_form"], "слідуючий")

    def test_ingest_movaua_no_incremental_does_not_double_pairs(self) -> None:
        manifest = [
            {"url": "https://ukr-mova.in.ua/item1", "section": "antusurzhuk"},
        ]
        session = MagicMock(spec=requests.Session)
        r = MagicMock(spec=requests.Response)
        r.status_code = 200
        r.text = "<html><title>Більшість членів чи більшість члени? | Мова – ДНК нації</title><div class='text'>Більшість членів</div></html>"
        session.get.return_value = r

        ingest_movaua(
            self.conn, session=session, manifest=manifest, incremental=False, delay=0, sleep_fn=lambda _: None
        )
        pairs_count_1 = self.conn.execute("SELECT COUNT(*) FROM movaua_usage_pairs").fetchone()[0]

        ingest_movaua(
            self.conn, session=session, manifest=manifest, incremental=False, delay=0, sleep_fn=lambda _: None
        )
        pairs_count_2 = self.conn.execute("SELECT COUNT(*) FROM movaua_usage_pairs").fetchone()[0]
        self.assertEqual(pairs_count_1, pairs_count_2)
        self.assertEqual(pairs_count_1, 1)

    def test_cli_parse_args(self) -> None:
        args = parse_args(["--source", "movne_pytannya", "--delay", "0.5", "--limit", "10", "--no-incremental"])
        self.assertEqual(args.source, SourceChoice.MOVNE)
        self.assertEqual(args.delay, 0.5)
        self.assertEqual(args.limit, 10)
        self.assertFalse(args.incremental)
        self.assertEqual(args.user_agent, DEFAULT_USER_AGENT)

    @patch("scripts.ingest.usage_advice_ingest.ingest_movne_pytannya")
    def test_cli_main_exit_codes(self, mock_movne: MagicMock) -> None:
        mock_movne.side_effect = AccessDeniedError("403 Forbidden")
        code = main(["--source", "movne_pytannya", "--db-movne", ":memory:"])
        self.assertEqual(code, EXIT_HTTP_403_FORBIDDEN)

    def test_user_agent_explicitly_set_on_session(self) -> None:
        session = requests.Session()
        self.assertIn("python-requests", session.headers.get("User-Agent", ""))
        ingest_movne_pytannya(
            self.conn,
            session=session,
            manifest=[],
            user_agent="CustomAgent/2.0",
        )
        self.assertEqual(session.headers.get("User-Agent"), "CustomAgent/2.0")

    def test_403_circuit_breaker_marks_error_and_skips_incremental(self) -> None:
        session = MagicMock(spec=requests.Session)
        resp403 = MagicMock(spec=requests.Response)
        resp403.status_code = 403
        session.get.return_value = resp403

        manifest = [{"issue_number": 1, "url": "https://glavcom.ua/blocked.html", "title": "Blocked"}]
        with self.assertRaises(AccessDeniedError):
            ingest_movne_pytannya(self.conn, session=session, manifest=manifest, delay=0, sleep_fn=lambda _: None)

        row = self.conn.execute(
            "SELECT url, error_status FROM movne_pytannya_issues WHERE url = ?",
            ("https://glavcom.ua/blocked.html",),
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "http_403")

        session.get.reset_mock()
        stats = ingest_movne_pytannya(
            self.conn, session=session, manifest=manifest, incremental=True, delay=0, sleep_fn=lambda _: None
        )
        self.assertEqual(stats.fetched_new, 0)
        self.assertEqual(session.get.call_count, 0)

    def test_reextract_movne_and_movaua(self) -> None:
        ensure_movne_schema(self.conn)
        ensure_movaua_schema(self.conn)

        movne_html = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Ірина: Як правильно казати: «на протязі» чи «протягом»?</p>
            <p>Правильно вживати: протягом. На протязі — це на вітрі.</p>
        </div>
        """
        self.conn.execute(
            """
            INSERT INTO movne_pytannya_issues
            (id, url, issue_number, title, date, description, raw_html, article_text, content_sha256, fetched_at)
            VALUES (1, 'https://glavcom.ua/issue1.html', 1, 'Випуск 1', '', '', ?, '', 'sha', '2026-01-01')
            """,
            (movne_html,),
        )
        movne_pairs = reextract_movne(self.conn)
        self.assertEqual(movne_pairs, 1)
        pair_row = self.conn.execute(
            "SELECT questioned_form, verdict_form FROM movne_word_pairs WHERE issue_id = 1"
        ).fetchone()
        self.assertEqual(pair_row[0], "на протязі")
        self.assertEqual(pair_row[1], "протягом")

        self.conn.execute(
            """
            INSERT INTO movaua_articles
            (id, url, section, title, date, image_url, image_alt, raw_html, article_text, content_sha256, fetched_at)
            VALUES (1, 'https://ukr-mova.in.ua/paronim/1', 'пароніми', 'Ефектний і ефективний', '', '', '', '<html></html>', 'Текст про різницю', 'sha', '2026-01-01')
            """
        )
        movaua_pairs = reextract_movaua(self.conn)
        self.assertEqual(movaua_pairs, 1)
        m_row = self.conn.execute(
            "SELECT questioned_form, recommended_form, pair_type FROM movaua_usage_pairs WHERE article_id = 1"
        ).fetchone()
        self.assertEqual(m_row[0], "Ефектний / ефективний")
        self.assertEqual(m_row[1], "Ефектний / ефективний")
        self.assertEqual(m_row[2], "paronym")

    def test_extract_movne_nested_wrapper_divs(self) -> None:
        html = """
        <div class="art_body_uniq">
            <div class="q-block">
                <h3>• 1 •</h3>
                <div class="q-inner">
                    <p>Марія: Як сказати «слідуючий»?</p>
                    <p>Правильно: наступний.</p>
                </div>
            </div>
        </div>
        """
        pairs = extract_movne_word_pairs(1, "https://glavcom.ua/nested.html", html)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["reader_name"], "Марія")
        self.assertEqual(pairs[0]["verdict_form"], "наступний")

    def test_reader_name_strips_question_prefixes(self) -> None:
        html = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Як правильно: чи можна казати «на протязі»?</p>
            <p>Правильно казати: протягом.</p>
            <h2>• 2 •</h2>
            <p>Запитує Петро: чи вживається слово «вірогідний»?</p>
            <p>Правильно казати: ймовірний.</p>
        </div>
        """
        pairs = extract_movne_word_pairs(1, "https://glavcom.ua/prefix.html", html)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0]["reader_name"], "")
        self.assertEqual(pairs[1]["reader_name"], "Петро")

    def test_full_verdict_list_and_explanation_strip(self) -> None:
        html = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Питання: як замінити «в кінці кінців»?</p>
            <p>Правильно казати: зрештою, врешті-решт або кінець кінцем, бо це калька з російської.</p>
        </div>
        """
        pairs = extract_movne_word_pairs(1, "https://glavcom.ua/list.html", html)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["verdict_form"], "зрештою, врешті-решт або кінець кінцем")

    def test_movaua_flexible_category_and_paronym_clean(self) -> None:
        p1 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/u1", "антисуржик", "Квиток чи білет?", "Квиток", "Текст")
        self.assertEqual(p1[0]["pair_type"], "anti_surzhyk")

        p2 = extract_movaua_usage_pairs(2, "https://ukr-mova.in.ua/u2", "синоніми", "Синоніми до слова «гарний»", "Вродливий", "Текст")
        self.assertEqual(p2[0]["pair_type"], "synonym")

        p3 = extract_movaua_usage_pairs(3, "https://ukr-mova.in.ua/u3", "пароніми", "Адрес і адреса", "", "Текст")
        self.assertEqual(p3[0]["pair_type"], "paronym")
        self.assertNotIn("(диференціація значень)", p3[0]["recommended_form"])
        self.assertEqual(p3[0]["recommended_form"], "Адрес / адреса")

    def test_discover_movne_host_allowlist_and_true_issue(self) -> None:
        session = MagicMock(spec=requests.Session)
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 200
        resp.text = """
        <div class="article_story_list">
            <div class="article_title"><a href="https://glavcom.ua/specprojects/movne_pytannya/45.html">«Мовне питання». Випуск № 45</a></div>
            <div class="article_description">Опис</div>
            <div class="article_date">2026-05-01</div>
        </div>
        <div class="article_story_list">
            <div class="article_title"><a href="https://external-ad.com/spam.html">Зовнішнє посилання</a></div>
        </div>
        """
        session.get.return_value = resp
        items = discover_movne_manifest(session, pages=["https://glavcom.ua/test.html"], delay=0, sleep_fn=lambda _: None)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://glavcom.ua/specprojects/movne_pytannya/45.html")
        self.assertEqual(items[0]["issue_number"], 45)

    def test_discover_movaua_nested_sitemaps(self) -> None:
        session = MagicMock(spec=requests.Session)
        r_index = MagicMock(spec=requests.Response)
        r_index.status_code = 200
        r_index.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap><loc>https://ukr-mova.in.ua/sitemap_sub.xml</loc></sitemap>
        </sitemapindex>"""

        r_sub = MagicMock(spec=requests.Response)
        r_sub.status_code = 200
        r_sub.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://ukr-mova.in.ua/antusurzhuk/item1</loc></url>
        </urlset>"""

        session.get.side_effect = [r_index, r_sub]
        items = discover_movaua_manifest(session, sitemap_url="https://ukr-mova.in.ua/sitemap.xml", delay=0, sleep_fn=lambda _: None)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://ukr-mova.in.ua/antusurzhuk/item1")
        self.assertEqual(items[0]["section"], "antusurzhuk")

    def test_movaua_date_and_image_urljoin(self) -> None:
        manifest = [{"url": "https://ukr-mova.in.ua/item_rel", "section": "antusurzhuk"}]
        session = MagicMock(spec=requests.Session)
        r = MagicMock(spec=requests.Response)
        r.status_code = 200
        r.text = """
        <html>
            <title>Тест</title>
            <time datetime="2026-03-15">15 березня 2026</time>
            <div class="illustration"><img src="/images/rule1.png" alt="Правило" /></div>
            <div class="article-content">Текст статті</div>
        </html>
        """
        session.get.return_value = r
        ingest_movaua(self.conn, session=session, manifest=manifest, delay=0, sleep_fn=lambda _: None)
        row = self.conn.execute(
            "SELECT date, image_url, image_alt FROM movaua_articles WHERE url = 'https://ukr-mova.in.ua/item_rel'"
        ).fetchone()
        self.assertEqual(row[0], "2026-03-15")
        self.assertEqual(row[1], "https://ukr-mova.in.ua/images/rule1.png")
        self.assertEqual(row[2], "Правило")

    def test_cli_re_extract_mode(self) -> None:
        args = parse_args(["--re-extract", "--source", "all"])
        self.assertTrue(args.re_extract)
        code = main(["--re-extract", "--source", "movne_pytannya", "--db-movne", "non_existent.db"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
