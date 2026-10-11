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
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from scripts.common.scratch import ensure_scratch_root
from scripts.ingest.usage_advice_ingest import (
    DEFAULT_USER_AGENT,
    EXIT_HTTP_403_FORBIDDEN,
    EXIT_HTTP_SERVER_ERROR,
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

        with tempfile.TemporaryDirectory(dir=ensure_scratch_root()) as td:
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
            <h2>• 3 •</h2>
            <p>Питання від Олени: як сказати «виключення»?</p>
            <p>Правильно казати: виняток.</p>
            <h2>• 4 •</h2>
            <p>Запитання від Сергія: як перекласти «в основному»?</p>
            <p>Правильно казати: переважно.</p>
        </div>
        """
        pairs = extract_movne_word_pairs(1, "https://glavcom.ua/prefix.html", html)
        self.assertEqual(len(pairs), 4)
        self.assertEqual(pairs[0]["reader_name"], "")
        self.assertEqual(pairs[1]["reader_name"], "Петро")
        self.assertEqual(pairs[2]["reader_name"], "Олени")
        self.assertEqual(pairs[3]["reader_name"], "Сергія")

    def test_full_verdict_list_and_explanation_strip(self) -> None:
        html = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Питання: як замінити «в кінці кінців»?</p>
            <p>Правильно казати: зрештою, а також врешті-решт або кінець кінцем, а не в кінці кінців, бо це калька з російської.</p>
        </div>
        """
        pairs = extract_movne_word_pairs(1, "https://glavcom.ua/list.html", html)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["verdict_form"], "зрештою, а також врешті-решт або кінець кінцем")

    def test_movaua_flexible_category_and_paronym_clean(self) -> None:
        p1 = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/u1", "антисуржик", "Квиток чи білет?", "Квиток", "Текст"
        )
        self.assertEqual(p1[0]["pair_type"], "anti_surzhyk")

        p2 = extract_movaua_usage_pairs(
            2, "https://ukr-mova.in.ua/u2", "синоніми", "Синоніми до слова «гарний»", "Вродливий", "Текст"
        )
        self.assertEqual(p2[0]["pair_type"], "synonym")

        p3 = extract_movaua_usage_pairs(
            3, "https://ukr-mova.in.ua/u3", "пароніми", "Адрес і адреса (диференціація значень)", "", "Текст"
        )
        self.assertEqual(p3[0]["pair_type"], "paronym")
        self.assertNotIn("(диференціація значень)", p3[0]["recommended_form"])
        self.assertEqual(p3[0]["recommended_form"], "Адрес / адреса")

        p4 = extract_movaua_usage_pairs(
            4, "https://ukr-mova.in.ua/sinonimy/u4", "sinonim", "Слова-синоніми", "Гарний", "Текст"
        )
        self.assertEqual(p4[0]["pair_type"], "synonym")

    def test_movaua_empty_recommended_form_when_direction_unknown(self) -> None:
        # Without caption and without recommendation phrases in body, don't invent direction
        pairs = extract_movaua_usage_pairs(
            1,
            "https://ukr-mova.in.ua/antusurzhuk/ambiguous",
            "антисуржик",
            "Квиток чи білет?",
            "",
            "У цьому матеріалі розглядаються особливості вживання слів у різних стилях мовлення.",
        )
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["recommended_form"], "")
        self.assertEqual(pairs[0]["questioned_form"], "Квиток / білет")

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
        items = discover_movne_manifest(
            session, pages=["https://glavcom.ua/test.html"], delay=0, sleep_fn=lambda _: None
        )
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
            <sitemap><loc>https://malicious.com/offhost_sitemap.xml</loc></sitemap>
            <sitemap><loc>http://ukr-mova.in.ua/insecure_sitemap.xml</loc></sitemap>
        </sitemapindex>"""

        r_sub = MagicMock(spec=requests.Response)
        r_sub.status_code = 200
        r_sub.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://ukr-mova.in.ua/antusurzhuk/item1</loc></url>
        </urlset>"""

        session.get.side_effect = [r_index, r_sub]
        items = discover_movaua_manifest(
            session, sitemap_url="https://ukr-mova.in.ua/sitemap.xml", delay=0, sleep_fn=lambda _: None
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://ukr-mova.in.ua/antusurzhuk/item1")
        self.assertEqual(items[0]["section"], "antusurzhuk")
        # Ensure off-host and insecure sitemaps were not fetched
        self.assertEqual(session.get.call_count, 2)

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

    def test_reextract_movaua_updates_article_metadata(self) -> None:
        ensure_movaua_schema(self.conn)
        raw_html = """
        <html>
            <title>Оновлений заголовок - Мова - ДНК нації</title>
            <time datetime="2026-04-10">10 квітня 2026</time>
            <div class="illustration"><img src="/img/new.png" alt="Нова ілюстрація" /></div>
            <div class="article-content">Оновлений текст статті.</div>
        </html>
        """
        self.conn.execute(
            """
            INSERT INTO movaua_articles (url, section, title, raw_html, article_text, content_sha256, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "https://ukr-mova.in.ua/update_test",
                "antusurzhuk",
                "Старий заголовок",
                raw_html,
                "Старий текст",
                "dummy_sha",
                "2026-04-10T12:00:00Z",
            ),
        )
        self.conn.commit()

        reextract_movaua(self.conn)
        row = self.conn.execute(
            "SELECT title, date, image_url, image_alt, article_text FROM movaua_articles WHERE url = 'https://ukr-mova.in.ua/update_test'"
        ).fetchone()
        self.assertEqual(row[0], "Оновлений заголовок - Мова - ДНК нації")
        self.assertEqual(row[1], "2026-04-10")
        self.assertEqual(row[2], "https://ukr-mova.in.ua/img/new.png")
        self.assertEqual(row[3], "Нова ілюстрація")
        self.assertIn("Оновлений текст статті.", row[4])

    def test_retry_errors_mode(self) -> None:
        ensure_movne_schema(self.conn)
        self.conn.execute(
            """
            INSERT INTO movne_pytannya_issues (url, issue_number, title, date, description, raw_html, article_text, content_sha256, fetched_at, error_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "https://glavcom.ua/err.html",
                99,
                "Error Issue",
                "2026-01-01",
                "Опис",
                "",
                "",
                "",
                "2026-01-01",
                "500 Internal Server Error",
            ),
        )
        self.conn.commit()

        # In incremental mode without retry_errors, existing error row is skipped
        manifest = [{"url": "https://glavcom.ua/err.html", "issue_number": 99, "title": "Error Issue"}]
        session = MagicMock(spec=requests.Session)
        stats = ingest_movne_pytannya(
            self.conn,
            session=session,
            manifest=manifest,
            incremental=True,
            retry_errors=False,
            delay=0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(stats.cached_existing, 1)
        self.assertEqual(session.get.call_count, 0)

        # With retry_errors=True, error row is retried
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 200
        resp.text = "<html><div class='art_body_uniq'>Вміст випуску</div></html>"
        session.get.return_value = resp

        stats2 = ingest_movne_pytannya(
            self.conn,
            session=session,
            manifest=manifest,
            incremental=True,
            retry_errors=True,
            delay=0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(stats2.cached_existing, 0)
        self.assertEqual(stats2.fetched_new, 1)
        self.assertEqual(session.get.call_count, 1)

    def test_find_body_recommendation_contrastive_negation(self) -> None:
        # Contrastive negation ("не X, а Y", "Y, а не X", "не «X», а «Y»", "«Y», а не «X»")
        t1 = "Правильно: не квиток, а білет."
        pairs1 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t1", "antusurzhuk", "квиток чи білет", "", t1)
        self.assertEqual(len(pairs1), 1)
        self.assertEqual(pairs1[0]["questioned_form"], "квиток")
        self.assertEqual(pairs1[0]["recommended_form"], "білет")

        t2 = "Треба казати: білет, а не квиток."
        pairs2 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t2", "antusurzhuk", "квиток чи білет", "", t2)
        self.assertEqual(len(pairs2), 1)
        self.assertEqual(pairs2[0]["questioned_form"], "квиток")
        self.assertEqual(pairs2[0]["recommended_form"], "білет")

        t3 = "Правильно: «не квиток, а білет»."
        pairs3 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t3", "antusurzhuk", "квиток чи білет", "", t3)
        self.assertEqual(len(pairs3), 1)
        self.assertEqual(pairs3[0]["questioned_form"], "квиток")
        self.assertEqual(pairs3[0]["recommended_form"], "білет")

        # Per-word quotes: не «X», а «Y» and «Y», а не «X»
        t4 = "Правильно: не «квиток», а «білет»."
        pairs4 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t4", "antusurzhuk", "квиток чи білет", "", t4)
        self.assertEqual(len(pairs4), 1)
        self.assertEqual(pairs4[0]["questioned_form"], "квиток")
        self.assertEqual(pairs4[0]["recommended_form"], "білет")

        t5 = "Правильно: «білет», а не «квиток»."
        pairs5 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t5", "antusurzhuk", "квиток чи білет", "", t5)
        self.assertEqual(len(pairs5), 1)
        self.assertEqual(pairs5[0]["questioned_form"], "квиток")
        self.assertEqual(pairs5[0]["recommended_form"], "білет")

        # Unstated sibling: не «квиток», а «талон» (талон is recommended, not білет)
        t6 = "Правильно: не «квиток», а «талон»."
        pairs6 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t6", "antusurzhuk", "квиток чи білет", "", t6)
        self.assertEqual(len(pairs6), 1)
        self.assertEqual(pairs6[0]["questioned_form"], "квиток")
        self.assertEqual(pairs6[0]["recommended_form"], "талон")

        # Both negated: не квиток і не білет, а талон
        t7 = "Правильно: не квиток і не білет, а талон."
        pairs7 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t7", "antusurzhuk", "квиток чи білет", "", t7)
        self.assertEqual(len(pairs7), 1)
        self.assertEqual(pairs7[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs7[0]["recommended_form"], "талон")

        # Both negated without alternative: ані квиток, ані білет
        t8 = "Для цього випадку: ані квиток, ані білет не підходять."
        pairs8 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t8", "antusurzhuk", "квиток чи білет", "", t8)
        self.assertEqual(len(pairs8), 1)
        self.assertEqual(pairs8[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs8[0]["recommended_form"], "")

        # Real lead-in with paired ані without alternative:
        t_ani_no_alt = "Правильно: ані квиток, ані білет не підходять."
        pairs_ani_no = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/t_ani1", "antusurzhuk", "квиток чи білет", "", t_ani_no_alt
        )
        self.assertEqual(len(pairs_ani_no), 1)
        self.assertEqual(pairs_ani_no[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_ani_no[0]["recommended_form"], "")

        # Real lead-in with paired ані with alternative:
        t_ani_alt = "Правильно: ані квиток, ані білет, а талон."
        pairs_ani_alt = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/t_ani2", "antusurzhuk", "квиток чи білет", "", t_ani_alt
        )
        self.assertEqual(len(pairs_ani_alt), 1)
        self.assertEqual(pairs_ani_alt[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_ani_alt[0]["recommended_form"], "талон")

        # Real lead-in with paired не ... а не ... with alternative:
        t_ne_alt = "Правильно: не квиток, а не білет, а талон."
        pairs_ne_alt = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/t_ne1", "antusurzhuk", "квиток чи білет", "", t_ne_alt
        )
        self.assertEqual(len(pairs_ne_alt), 1)
        self.assertEqual(pairs_ne_alt[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_ne_alt[0]["recommended_form"], "талон")

        # Earlier recommendation preserved over later multi-negation:
        t_b1 = "Правильно: білет, а не квиток і не талон."
        pairs_b1 = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/t_b1", "antusurzhuk", "квиток чи білет", "", t_b1
        )
        self.assertEqual(len(pairs_b1), 1)
        self.assertEqual(pairs_b1[0]["questioned_form"], "квиток")
        self.assertEqual(pairs_b1[0]["recommended_form"], "білет")

        t_b2 = "Правильно: не квиток, а білет, бо ані талон, ані чек не підходять."
        pairs_b2 = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/t_b2", "antusurzhuk", "квиток чи білет", "", t_b2
        )
        self.assertEqual(len(pairs_b2), 1)
        self.assertEqual(pairs_b2[0]["questioned_form"], "квиток")
        self.assertEqual(pairs_b2[0]["recommended_form"], "білет")

        # Negative predicate with following alternative:
        t_b3 = "Правильно: ані квиток, ані білет не підходять, а талон."
        pairs_b3 = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/t_b3", "antusurzhuk", "квиток чи білет", "", t_b3
        )
        self.assertEqual(len(pairs_b3), 1)
        self.assertEqual(pairs_b3[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_b3[0]["recommended_form"], "талон")

        t_b4 = "Правильно: ані квиток, ані білет — не нормативні, а талон."
        pairs_b4 = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/t_b4", "antusurzhuk", "квиток чи білет", "", t_b4
        )
        self.assertEqual(len(pairs_b4), 1)
        self.assertEqual(pairs_b4[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_b4[0]["recommended_form"], "талон")

        # Paired negation without alternative:
        t_b5 = "Правильно: не квиток, а не білет."
        pairs_b5 = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/t_b5", "antusurzhuk", "квиток чи білет", "", t_b5
        )
        self.assertEqual(len(pairs_b5), 1)
        self.assertEqual(pairs_b5[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_b5[0]["recommended_form"], "")

        t_b6 = "Правильно: не квиток і не білет."
        pairs_b6 = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/t_b6", "antusurzhuk", "квиток чи білет", "", t_b6
        )
        self.assertEqual(len(pairs_b6), 1)
        self.assertEqual(pairs_b6[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_b6[0]["recommended_form"], "")

        # Lead-in words ending in 'не': Для мене правильно, Головне правильно
        t9 = "Для мене правильно: білет, а не квиток."
        pairs9 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t9", "antusurzhuk", "квиток чи білет", "", t9)
        self.assertEqual(len(pairs9), 1)
        self.assertEqual(pairs9[0]["questioned_form"], "квиток")
        self.assertEqual(pairs9[0]["recommended_form"], "білет")

        t10 = "Головне правильно: білет."
        pairs10 = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/t10", "antusurzhuk", "квиток чи білет", "", t10)
        self.assertEqual(len(pairs10), 1)
        self.assertEqual(pairs10[0]["questioned_form"], "квиток")
        self.assertEqual(pairs10[0]["recommended_form"], "білет")

    def test_find_body_recommendation_negation_rejection(self) -> None:
        # Negation ("неправильно", "не варто", "не треба", "не слід") must not match as a recommendation
        text_neg = "Неправильно: квиток. Треба казати: білет на потяг."
        pairs = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/test-neg", "antusurzhuk", "квиток чи білет", "", text_neg
        )
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["questioned_form"], "квиток")
        self.assertEqual(pairs[0]["recommended_form"], "білет")

        # When body only contains negation, it should not pick questioned form as recommended
        text_only_neg = "Неправильно: квиток. Не варто так писати в офіційних документах."
        pairs_fallback = extract_movaua_usage_pairs(
            1, "https://ukr-mova.in.ua/test-neg2", "antusurzhuk", "квиток чи білет", "", text_only_neg
        )
        self.assertEqual(len(pairs_fallback), 1)
        self.assertEqual(pairs_fallback[0]["recommended_form"], "")
        self.assertIn("квиток / білет", pairs_fallback[0]["questioned_form"])

    def test_token_isolation_short_words(self) -> None:
        # Single-letter token "в" must not match inside "вашому"
        text = "Правильно: у вашому тексті писати так."
        pairs = extract_movaua_usage_pairs(1, "https://ukr-mova.in.ua/v-chy-u", "antusurzhuk", "в чи у", "", text)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["questioned_form"], "в")
        self.assertEqual(pairs[0]["recommended_form"], "у")

    def test_contains_token_apostrophes_and_hyphens(self) -> None:
        from scripts.ingest.usage_advice_ingest import _contains_token

        # Letters before/after apostrophe must not match as isolated tokens
        self.assertFalse(_contains_token("в'їзд заборонено", "в"))
        self.assertFalse(_contains_token("в’їзд заборонено", "в"))
        self.assertFalse(_contains_token("з'явитися зненацька", "з"))
        self.assertFalse(_contains_token("пів'яблука", "яблука"))
        self.assertFalse(_contains_token("пів’яблука", "яблука"))

        # Exact compound words and words with apostrophes match
        self.assertTrue(_contains_token("в'їзд заборонено", "в'їзд"))
        self.assertTrue(_contains_token("в’їзд заборонено", "в'їзд"))
        self.assertTrue(_contains_token("пів'яблука чи груша", "пів'яблука"))
        self.assertTrue(_contains_token("пів’яблука чи груша", "пів'яблука"))

        # Hyphenated words
        self.assertFalse(_contains_token("будь-який день", "будь"))
        self.assertTrue(_contains_token("будь-який день", "будь-який"))

    def test_glavcom_short_words_token_isolation(self) -> None:
        # Quoted «в» чи «у» with verdict 'у вашому тексті' must not match 'в' inside 'вашому'
        html_quoted = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Олег: Як правильно писати: «в» чи «у»?</p>
            <p>Правильно: у вашому тексті.</p>
        </div>
        """
        pairs_q = extract_movne_word_pairs(1, 1, html_quoted)
        self.assertEqual(len(pairs_q), 1)
        self.assertEqual(pairs_q[0]["questioned_form"], "в")
        self.assertEqual(pairs_q[0]["verdict_form"], "у вашому тексті")

        # Unquoted в чи у with verdict 'у вашому тексті'
        html_unquoted = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Олег: Як правильно писати в чи у?</p>
            <p>Правильно: у вашому тексті.</p>
        </div>
        """
        pairs_u = extract_movne_word_pairs(1, 1, html_unquoted)
        self.assertEqual(len(pairs_u), 1)
        self.assertEqual(pairs_u[0]["questioned_form"], "в")
        self.assertEqual(pairs_u[0]["verdict_form"], "у вашому тексті")

        # Quoted «в» чи «у» with no word 'правильно' but verdict using 'у' as a token
        html_no_prav = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Олег: Як правильно писати: «в» чи «у»?</p>
            <p>У вашому тексті вживайте прийменник у.</p>
        </div>
        """
        pairs_np = extract_movne_word_pairs(1, 1, html_no_prav)
        self.assertEqual(len(pairs_np), 1)
        self.assertEqual(pairs_np[0]["questioned_form"], "в")
        self.assertEqual(pairs_np[0]["verdict_form"], "у")

    def test_glavcom_verdict_word_boundary(self) -> None:
        # Glavcom word boundary prevents capturing trailing letters like 'ю' from 'правильною'
        html_wrong = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: Як сказати: протягом чи на протязі?</p>
            <p>Ця форма є правильною.</p>
        </div>
        """
        pairs = extract_movne_word_pairs(1, 1, html_wrong)
        self.assertEqual(len(pairs), 1)
        self.assertNotEqual(pairs[0]["verdict_form"], "ю")
        self.assertFalse(pairs[0]["verdict_form"].startswith("ю"))

        # Spaced negation "не правильно: X. Треба казати: Y." must store Y as verdict
        html_spaced_neg = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: Чи правильно так писати?</p>
            <p>Це не правильно: на протязі. Треба казати: протягом.</p>
        </div>
        """
        pairs_spaced = extract_movne_word_pairs(1, 1, html_spaced_neg)
        self.assertEqual(len(pairs_spaced), 1)
        self.assertEqual(pairs_spaced[0]["questioned_form"], "на протязі")
        self.assertEqual(pairs_spaced[0]["verdict_form"], "протягом")
        self.assertEqual(pairs_spaced[0]["verdict_type"], "preferred")

        # Contrastive in Glavcom: Правильно: не «на протязі», а «протягом».
        html_contrast = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: Як казати?</p>
            <p>Правильно: не «на протязі», а «протягом».</p>
        </div>
        """
        pairs_contrast = extract_movne_word_pairs(1, 1, html_contrast)
        self.assertEqual(len(pairs_contrast), 1)
        self.assertEqual(pairs_contrast[0]["questioned_form"], "на протязі")
        self.assertEqual(pairs_contrast[0]["verdict_form"], "протягом")
        self.assertEqual(pairs_contrast[0]["verdict_type"], "preferred")

        # Lead-in ending with 'не': Для мене правильно: білет, а не квиток.
        html_mene = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: «квиток» чи «білет»?</p>
            <p>Для мене правильно: білет, а не квиток.</p>
        </div>
        """
        pairs_mene = extract_movne_word_pairs(1, 1, html_mene)
        self.assertEqual(len(pairs_mene), 1)
        self.assertEqual(pairs_mene[0]["questioned_form"], "квиток")
        self.assertEqual(pairs_mene[0]["verdict_form"], "білет")
        self.assertEqual(pairs_mene[0]["verdict_type"], "preferred")

        # Real lead-in with paired ані with alternative in Glavcom:
        html_ani_alt = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: «квиток» чи «білет»?</p>
            <p>Правильно: ані квиток, ані білет, а талон.</p>
        </div>
        """
        pairs_ani_g = extract_movne_word_pairs(1, 1, html_ani_alt)
        self.assertEqual(len(pairs_ani_g), 1)
        self.assertEqual(pairs_ani_g[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_ani_g[0]["verdict_form"], "талон")
        self.assertEqual(pairs_ani_g[0]["verdict_type"], "preferred")

        # Real lead-in with paired ані without alternative in Glavcom:
        html_ani_none = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: «квиток» чи «білет»?</p>
            <p>Правильно: ані квиток, ані білет не підходять.</p>
        </div>
        """
        pairs_ani_gn = extract_movne_word_pairs(1, 1, html_ani_none)
        self.assertEqual(len(pairs_ani_gn), 1)
        self.assertEqual(pairs_ani_gn[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_ani_gn[0]["verdict_form"], "")
        self.assertEqual(pairs_ani_gn[0]["verdict_type"], "incorrect")

        # Glavcom blocker 1: Earlier recommendation preserved over later multi-negation:
        html_b1 = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: Як казати?</p>
            <p>Правильно: білет, а не квиток і не талон.</p>
        </div>
        """
        pairs_gb1 = extract_movne_word_pairs(1, 1, html_b1)
        self.assertEqual(len(pairs_gb1), 1)
        self.assertEqual(pairs_gb1[0]["verdict_form"], "білет")
        self.assertEqual(pairs_gb1[0]["questioned_form"], "квиток / талон")
        self.assertEqual(pairs_gb1[0]["verdict_type"], "preferred")

        # Glavcom blocker 1: Recommendation in main clause over multi-negation in бо clause:
        html_b2 = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: Як казати?</p>
            <p>Правильно: не квиток, а білет, бо ані талон, ані чек не підходять.</p>
        </div>
        """
        pairs_gb2 = extract_movne_word_pairs(1, 1, html_b2)
        self.assertEqual(len(pairs_gb2), 1)
        self.assertEqual(pairs_gb2[0]["verdict_form"], "білет")
        self.assertEqual(pairs_gb2[0]["questioned_form"], "квиток")
        self.assertEqual(pairs_gb2[0]["verdict_type"], "preferred")

        # Glavcom blocker 2: Negative predicate with following alternative:
        html_b3 = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: Як казати?</p>
            <p>Правильно: ані квиток, ані білет не підходять, а талон.</p>
        </div>
        """
        pairs_gb3 = extract_movne_word_pairs(1, 1, html_b3)
        self.assertEqual(len(pairs_gb3), 1)
        self.assertEqual(pairs_gb3[0]["verdict_form"], "талон")
        self.assertEqual(pairs_gb3[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_gb3[0]["verdict_type"], "preferred")

        html_b4 = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: Як казати?</p>
            <p>Правильно: ані квиток, ані білет — не нормативні, а талон.</p>
        </div>
        """
        pairs_gb4 = extract_movne_word_pairs(1, 1, html_b4)
        self.assertEqual(len(pairs_gb4), 1)
        self.assertEqual(pairs_gb4[0]["verdict_form"], "талон")
        self.assertEqual(pairs_gb4[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_gb4[0]["verdict_type"], "preferred")

        # Glavcom paired negation without alternative:
        html_b5 = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: «квиток» чи «білет»?</p>
            <p>Правильно: не квиток, а не білет.</p>
        </div>
        """
        pairs_gb5 = extract_movne_word_pairs(1, 1, html_b5)
        self.assertEqual(len(pairs_gb5), 1)
        self.assertEqual(pairs_gb5[0]["verdict_form"], "")
        self.assertEqual(pairs_gb5[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_gb5[0]["verdict_type"], "incorrect")

        html_b6 = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: «квиток» чи «білет»?</p>
            <p>Правильно: не квиток і не білет.</p>
        </div>
        """
        pairs_gb6 = extract_movne_word_pairs(1, 1, html_b6)
        self.assertEqual(len(pairs_gb6), 1)
        self.assertEqual(pairs_gb6[0]["verdict_form"], "")
        self.assertEqual(pairs_gb6[0]["questioned_form"], "квиток / білет")
        self.assertEqual(pairs_gb6[0]["verdict_type"], "incorrect")

        html_correct = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Андрій: Як сказати: протягом чи на протязі?</p>
            <p>Правильно казати: протягом. Форма «на протязі» — калька.</p>
        </div>
        """
        pairs_ok = extract_movne_word_pairs(1, 1, html_correct)
        self.assertEqual(len(pairs_ok), 1)
        self.assertEqual(pairs_ok[0]["verdict_form"], "протягом")

    def test_clean_verdict_balanced_parentheses(self) -> None:
        # Balanced parentheses inside alternatives must be preserved, while unclosed trailing ones are stripped
        html = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Ірина: Як правильно писати?</p>
            <p>Правильно: зрештою (іноді), а також врешті-решт (залежно від контексту).</p>
        </div>
        """
        pairs = extract_movne_word_pairs(1, 1, html)
        self.assertEqual(len(pairs), 1)
        self.assertIn("зрештою (іноді)", pairs[0]["verdict_form"])
        self.assertIn("врешті-решт (залежно від контексту)", pairs[0]["verdict_form"])

    def test_header_digit_not_question_boundary(self) -> None:
        # Headers with words and digits (e.g. "Правило 2 для дат") must not split into new questions
        html = """
        <div class="post_text">
            <h2>• 1 •</h2>
            <p>Сергій: Як правильно вживати слово?</p>
            <p>Правильно: приклад.</p>
            <h3>Правило 2 для дат</h3>
            <p>Додаткове пояснення для правила.</p>
        </div>
        """
        pairs = extract_movne_word_pairs(1, 1, html)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["question_num"], 1)

    def test_polite_get_mock_non_string_url_fallback(self) -> None:
        # Mock Response without string url should not fail urlsplit and should use request url
        session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        # When spec=requests.Response, mock_resp.url is a MagicMock, not a str
        session.get.return_value = mock_resp

        resp = polite_get(session, "https://example.com/test-mock", delay=0)
        self.assertEqual(resp.status_code, 200)

    def test_movaua_non_200_error_status_recording(self) -> None:
        ensure_movaua_schema(self.conn)
        session = MagicMock(spec=requests.Session)
        r404 = MagicMock(spec=requests.Response)
        r404.status_code = 404
        session.get.return_value = r404

        manifest = [{"url": "https://ukr-mova.in.ua/not-found", "section": "antusurzhuk", "title": "Missing"}]
        stats = ingest_movaua(
            self.conn,
            session=session,
            manifest=manifest,
            incremental=True,
            retry_errors=False,
            delay=0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(stats.errors, 1)
        self.assertEqual(stats.fetched_new, 0)

        row = self.conn.execute(
            "SELECT url, error_status FROM movaua_articles WHERE url = ?",
            ("https://ukr-mova.in.ua/not-found",),
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "http_404")

        # In incremental mode without retry_errors, it is skipped
        session.get.reset_mock()
        stats_inc = ingest_movaua(
            self.conn,
            session=session,
            manifest=manifest,
            incremental=True,
            retry_errors=False,
            delay=0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(stats_inc.cached_existing, 1)
        self.assertEqual(session.get.call_count, 0)

        # With retry_errors=True, it is retried
        r200 = MagicMock(spec=requests.Response)
        r200.status_code = 200
        r200.text = "<html><div class='field-item even'>Текст статті</div></html>"
        session.get.return_value = r200

        stats_retry = ingest_movaua(
            self.conn,
            session=session,
            manifest=manifest,
            incremental=True,
            retry_errors=True,
            delay=0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(stats_retry.fetched_new, 1)
        self.assertEqual(session.get.call_count, 1)

    def test_cli_exit_on_errors(self) -> None:
        with tempfile.TemporaryDirectory(dir=ensure_scratch_root()) as tmpdir:
            test_db = str(Path(tmpdir) / "test.db")
            session_patch = MagicMock(spec=requests.Session)
            r = MagicMock(spec=requests.Response)
            r.status_code = 500
            session_patch.get.return_value = r

            manifest = [{"url": "https://ukr-mova.in.ua/failing", "section": "antusurzhuk"}]
            with (
                patch("scripts.ingest.usage_advice_ingest.discover_movaua_manifest", return_value=manifest),
                patch("requests.Session", return_value=session_patch),
            ):
                code = main(
                    [
                        "--source",
                        "movaua",
                        "--db-movaua",
                        test_db,
                        "--limit",
                        "1",
                        "--delay",
                        "0",
                        "--max-retries",
                        "1",
                    ]
                )
                self.assertEqual(code, EXIT_HTTP_SERVER_ERROR)

    def test_cli_re_extract_mode(self) -> None:
        args = parse_args(["--re-extract", "--source", "all"])
        self.assertTrue(args.re_extract)
        with tempfile.TemporaryDirectory(dir=ensure_scratch_root()) as tmpdir:
            test_db = str(Path(tmpdir) / "test.db")
            code = main(["--re-extract", "--source", "movne_pytannya", "--db-movne", test_db])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
