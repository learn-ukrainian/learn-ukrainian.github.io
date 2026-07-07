"""
Ingest ZNO booklet metadata and online tasks from zno.osvita.ua into sources.db.
"""

import argparse
import copy
import json
import re
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

# Verified 33 booklet documents from the matrix (2010 to 2025, excluding 2009 and 3 demo sessions)
BOOKLETS = [
    {
        "id": 1,
        "year": 2025,
        "exam": "nmt",
        "session": "sesiya-1",
        "subject_scope": "mova",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/955/95541/1_Ukr_mova_1.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "scan",
        "content_assertion": "Правильні відповіді до завдань сертифікаційної роботи з української мови",
        "verified_by": "claude-live",
    },
    {
        "id": 2,
        "year": 2025,
        "exam": "nmt",
        "session": "sesiya-2",
        "subject_scope": "mova",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/955/95541/1_Ukr_mova_2.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Правильні відповіді до завдань сертифікаційної роботи",
        "verified_by": "agy-probe",
    },
    {
        "id": 3,
        "year": 2024,
        "exam": "nmt",
        "session": "sesiya-1",
        "subject_scope": "mova",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/932/93289/Ukr_mova_1.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "3.1.1.3. Психометричні характеристики завдань сертифікаційної роботи",
        "verified_by": "agy-probe",
    },
    {
        "id": 4,
        "year": 2024,
        "exam": "nmt",
        "session": "sesiya-2",
        "subject_scope": "mova",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/932/93289/Ukr_mova_2.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Завдання з української мови 2024 року (варіант 2)",
        "verified_by": "agy-probe",
    },
    {
        "id": 5,
        "year": 2023,
        "exam": "nmt",
        "session": "sesiya-1",
        "subject_scope": "mova",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/900/90040/Ukr_1_2023.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "garbled",
        "content_assertion": "Завдання з української мови 2023 року (варіант 1)",
        "verified_by": "claude-live",
    },
    {
        "id": 6,
        "year": 2023,
        "exam": "nmt",
        "session": "sesiya-2",
        "subject_scope": "mova",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/900/90040/Ukr_2_2023.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Завдання з української мови 2023 року (варіант 2)",
        "verified_by": "agy-probe",
    },
    {
        "id": 7,
        "year": 2022,
        "exam": "nmt",
        "session": "osnovna",
        "subject_scope": "mova",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/878/87872/Ukr_zoshyt-nmt-2022.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Правильні відповіді на завдання блоку «Українська мова» національного мультипредметного тесту",
        "verified_by": "agy-probe",
    },
    {
        "id": 8,
        "year": 2021,
        "exam": "zno",
        "session": "osnovna",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/826/82624/Ukr-mova_lit-ZNO_2021-osn_sesiya.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "garbled",
        "content_assertion": "Зовнішнє незалежне оцінювання 2021 року з української мови і літератури",
        "verified_by": "claude-live",
    },
    {
        "id": 9,
        "year": 2021,
        "exam": "zno",
        "session": "osnovna",
        "subject_scope": "mova",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/826/82625/Ukr-mova-ZNO_2021-osn_sesiya.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "garbled",
        "content_assertion": "Зовнішнє незалежне оцінювання 2021 року з української мови (тільки мова)",
        "verified_by": "claude-live",
    },
    {
        "id": 10,
        "year": 2021,
        "exam": "zno",
        "session": "dodatkova",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/826/82624/Ukr-mova_lit-ZNO_2021-dod_sesiya.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "garbled",
        "content_assertion": "Зовнішнє незалежне оцінювання 2021 року з української мови і літератури (додаткова сесія)",
        "verified_by": "claude-live",
    },
    {
        "id": 11,
        "year": 2021,
        "exam": "zno",
        "session": "dodatkova",
        "subject_scope": "mova",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/826/82625/1_Ukr_mova-ZNO_2021-dod_sesiya.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "garbled",
        "content_assertion": "Зовнішнє незалежне оцінювання 2021 року з української мови (тільки мова, додаткова сесія)",
        "verified_by": "claude-live",
    },
    {
        "id": 12,
        "year": 2020,
        "exam": "zno",
        "session": "osnovna",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/747/74785/Ukr-mova_lit-ZNO_2020-Zoshyt_1.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Завдання тесту ЗНО з української мови та літератури 2020 року",
        "verified_by": "agy-probe",
    },
    {
        "id": 13,
        "year": 2020,
        "exam": "zno",
        "session": "dodatkova",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/747/74785/Ukr-mova_lit-ZNO_2020-Zoshyt_1-Dod_sesiy.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Завдання тесту ЗНО з української мови та літератури 2020 року (додаткова сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 14,
        "year": 2019,
        "exam": "zno",
        "session": "osnovna",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/646/64612/Ukr-mova_lit-ZNO__2019-Zoshyt_1.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Завдання тесту ЗНО з української мови та літератури 2019 року",
        "verified_by": "agy-probe",
    },
    {
        "id": 15,
        "year": 2019,
        "exam": "zno",
        "session": "dodatkova",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/646/64612/Ukr-mova_lit-ZNO_2019-Zoshyt_1-Dod_sesiy.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Завдання тесту ЗНО з української мови та літератури 2019 року (додаткова сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 16,
        "year": 2018,
        "exam": "zno",
        "session": "osnovna",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://zno.osvita.ua/doc/files/news/608/60881/Ukr-mova_lit-Osnovne-ZNO_2018-Zoshyt_1_1.pdf",
        "mirror_host": "zno.osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "СЕРТИФІКАЦІЙНА РОБОТА З УКРАЇНСЬКОЇ МОВИ І ЛІТЕРАТУРИ",
        "verified_by": "agy-probe",
    },
    {
        "id": 17,
        "year": 2018,
        "exam": "zno",
        "session": "dodatkova",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/608/60881/Ukr-mova_lit-Dod_sesiya-ZNO_2018-Zoshyt_.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Завдання тесту ЗНО з української мови та літератури 2018 року (додаткова сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 18,
        "year": 2017,
        "exam": "zno",
        "session": "osnovna",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/557/55746/ukr_l.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": 'СЕРТИФІКАЦІЙНА РОБОТА З УКРАЇНСЬКОЇ МОВИ І ЛІТЕРАТУРИ" (2017)',
        "verified_by": "agy-probe",
    },
    {
        "id": 19,
        "year": 2017,
        "exam": "zno",
        "session": "dodatkova",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/557/55746/ukr_mov_test_dodatkov_17.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Завдання тесту ЗНО з української мови та літератури (додаткова сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 20,
        "year": 2016,
        "exam": "zno",
        "session": "osnovna",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/512/51272/scan_mov.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "scan",
        "content_assertion": "Зовнішнє незалежне оцінювання 2016 року з української мови і літератури",
        "verified_by": "agy-probe",
    },
    {
        "id": 21,
        "year": 2015,
        "exam": "zno",
        "session": "osnovna",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/468/46824/ZNO_2015_ukr_mova.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Зовнішнє незалежне оцінювання 2015 року Українська мова БАЗОВИЙ РІВЕНЬ",
        "verified_by": "agy-probe",
    },
    {
        "id": 22,
        "year": 2014,
        "exam": "zno",
        "session": "sesiya-1",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/414/41473/2014_Ukr_mova_ZNO.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на тест ЗНО з української мови та літератури 2014 року (І сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 23,
        "year": 2014,
        "exam": "zno",
        "session": "sesiya-2",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/415/41501/Zavdannya_Ukrayinska_mova_2_sesiya_2014.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на тест ЗНО з української мови та літератури 2014 року (ІІ сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 24,
        "year": 2014,
        "exam": "zno",
        "session": "dodatkova",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://lv.testportal.gov.ua/wp-content/arhiv/2014/2014_ukr_2.pdf",
        "mirror_host": "lv.testportal.gov.ua",
        "fetch_status": "dead",
        "text_layer": "clean",
        "content_assertion": "Відповіді на тест ЗНО з української мови та літератури 2014 року (додаткова сесія)",
        "verified_by": "claude-live",
    },
    {
        "id": 25,
        "year": 2013,
        "exam": "zno",
        "session": "sesiya-1",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/361/36102/ukrmova2013-1.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на тест ЗНО з української мови та літератури 2013 року (І сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 26,
        "year": 2013,
        "exam": "zno",
        "session": "sesiya-2",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/361/36121/ukrmova2013-2.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на тест ЗНО з української мови та літератури 2013 року (ІІ сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 27,
        "year": 2012,
        "exam": "zno",
        "session": "sesiya-1",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/296/29644/ukrmova2012-1.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на ЗНО з української мови та літератури 2012 року (І сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 28,
        "year": 2012,
        "exam": "zno",
        "session": "sesiya-2",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/296/29679/ukrmova2012-2.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на ЗНО з української мови та літератури 2012 року (ІІ сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 29,
        "year": 2011,
        "exam": "zno",
        "session": "sesiya-1",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/190/19043/ProgUKR1.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на ЗНО з української мови та літератури 2011 року (І сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 30,
        "year": 2011,
        "exam": "zno",
        "session": "sesiya-2",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/190/19067/ProgUKR2.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на ЗНО з української мови та літератури 2011 року (ІІ сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 31,
        "year": 2010,
        "exam": "zno",
        "session": "sesiya-1",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/77/7744/VidpProgUkr2010_I.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "wrong-content",
        "text_layer": "clean",
        "content_assertion": "Відповіді на тести ЗНО з української мови і літератури 2010 року (І сесія)",
        "verified_by": "claude-live",
    },
    {
        "id": 32,
        "year": 2010,
        "exam": "zno",
        "session": "sesiya-2",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/77/7756/VidpProgUkr2010_II.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на тести ЗНО з української мови і літератури 2010 року (ІІ сесія)",
        "verified_by": "agy-probe",
    },
    {
        "id": 33,
        "year": 2010,
        "exam": "zno",
        "session": "sesiya-3",
        "subject_scope": "mova-lit",
        "kind": "booklet",
        "url": "https://osvita.ua/doc/files/news/77/7769/VidpProgUkr2010_III.pdf",
        "mirror_host": "osvita.ua",
        "fetch_status": "ok",
        "text_layer": "clean",
        "content_assertion": "Відповіді на тести ЗНО з української мови і літератури 2010 року (ІІІ сесія)",
        "verified_by": "agy-probe",
    },
]

# Mapping of Year + Session type to test IDs on zno.osvita.ua for 2019, 2020, 2021
ONLINE_TEST_MAPPING = {
    (2019, "osnovna"): 347,
    (2019, "dodatkova"): 363,
    (2020, "osnovna"): 401,
    (2020, "dodatkova"): 429,
    (2021, "osnovna"): 471,  # maps to combined booklet mova-lit
    (2021, "dodatkova"): 491,  # maps to combined booklet mova-lit
}


def init_db(conn: sqlite3.Connection):
    """
    Initialize schema tables and indexes.
    """
    # Create tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS zno_documents (
            id INTEGER PRIMARY KEY,
            year INTEGER NOT NULL,
            exam TEXT NOT NULL,
            session TEXT NOT NULL,
            subject_scope TEXT NOT NULL,
            kind TEXT NOT NULL,
            url TEXT NOT NULL,
            mirror_host TEXT NOT NULL,
            sha256 TEXT DEFAULT NULL,
            fetch_status TEXT NOT NULL DEFAULT 'pending',
            text_layer TEXT DEFAULT '',
            extraction_method TEXT DEFAULT '',
            content_assertion TEXT DEFAULT '',
            verified_by TEXT DEFAULT '',
            license_note TEXT DEFAULT '',
            UNIQUE(url)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_zno_documents_year ON zno_documents(year, exam, session)")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS zno_tasks (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL REFERENCES zno_documents(id),
            year INTEGER NOT NULL,
            exam TEXT NOT NULL,
            session TEXT NOT NULL,
            task_no INTEGER NOT NULL,
            subject TEXT NOT NULL DEFAULT 'mova',
            task_format TEXT NOT NULL,
            stem TEXT NOT NULL,
            options_json TEXT NOT NULL DEFAULT '[]',
            correct_json TEXT NOT NULL DEFAULT '',
            topic_tag TEXT DEFAULT '',
            topic_norm TEXT DEFAULT '',
            task_subtype TEXT DEFAULT '',
            paronym_pair TEXT DEFAULT '',
            stress_word TEXT DEFAULT '',
            UNIQUE(document_id, task_no)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_zno_tasks_topic ON zno_tasks(topic_norm, year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_zno_tasks_doc ON zno_tasks(document_id)")

    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS zno_tasks_fts USING fts5(stem, options_json, topic_tag,
            content='zno_tasks', content_rowid='id', tokenize='unicode61')
    """)

    # Triggers to keep FTS in sync
    conn.execute("DROP TRIGGER IF EXISTS zno_tasks_ai")
    conn.execute("DROP TRIGGER IF EXISTS zno_tasks_ad")
    conn.execute("DROP TRIGGER IF EXISTS zno_tasks_au")

    conn.execute("""
        CREATE TRIGGER zno_tasks_ai AFTER INSERT ON zno_tasks BEGIN
            INSERT INTO zno_tasks_fts(rowid, stem, options_json, topic_tag)
            VALUES (new.id, new.stem, new.options_json, new.topic_tag);
        END
    """)
    conn.execute("""
        CREATE TRIGGER zno_tasks_ad AFTER DELETE ON zno_tasks BEGIN
            INSERT INTO zno_tasks_fts(zno_tasks_fts, rowid, stem, options_json, topic_tag)
            VALUES ('delete', old.id, old.stem, old.options_json, old.topic_tag);
        END
    """)
    conn.execute("""
        CREATE TRIGGER zno_tasks_au AFTER UPDATE ON zno_tasks BEGIN
            INSERT INTO zno_tasks_fts(zno_tasks_fts, rowid, stem, options_json, topic_tag)
            VALUES ('delete', old.id, old.stem, old.options_json, old.topic_tag);
            INSERT INTO zno_tasks_fts(rowid, stem, options_json, topic_tag)
            VALUES (new.id, new.stem, new.options_json, new.topic_tag);
        END
    """)


def ingest_documents(conn: sqlite3.Connection):
    """
    Ingest the 33 valid booklet documents idempotently.
    """
    for doc in BOOKLETS:
        conn.execute(
            """
            INSERT INTO zno_documents(
                id, year, exam, session, subject_scope, kind, url, mirror_host,
                fetch_status, text_layer, content_assertion, verified_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                year=excluded.year,
                exam=excluded.exam,
                session=excluded.session,
                subject_scope=excluded.subject_scope,
                kind=excluded.kind,
                mirror_host=excluded.mirror_host,
                fetch_status=excluded.fetch_status,
                text_layer=excluded.text_layer,
                content_assertion=excluded.content_assertion,
                verified_by=excluded.verified_by
        """,
            (
                doc["id"],
                doc["year"],
                doc["exam"],
                doc["session"],
                doc["subject_scope"],
                doc["kind"],
                doc["url"],
                doc["mirror_host"],
                doc["fetch_status"],
                doc["text_layer"],
                doc["content_assertion"],
                doc["verified_by"],
            ),
        )


# Simple global to track the time of the last HTTP request
_last_request_time = 0.0


def fetch_page_with_rate_limit(url: str, cache_path: Path, rate_limit: float = 2.0) -> str:
    """
    Fetch URL content with a rate limit, caching the results locally.
    """
    global _last_request_time
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    # Enforce rate limit
    elapsed = time.time() - _last_request_time
    if elapsed < rate_limit:
        sleep_time = rate_limit - elapsed
        time.sleep(sleep_time)

    # Fetch page
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        html = response.read().decode("utf-8")

    _last_request_time = time.time()

    # Cache locally
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html, encoding="utf-8")

    return html


def parse_and_insert_tasks(conn: sqlite3.Connection, html: str, doc_id: int, year: int, exam: str, session: str):
    """
    Parse tasks from ZNO online test page HTML and insert them into the DB.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all(class_="task-card")

    inserted = 0
    for card in cards:
        card_id = card.get("id", "")
        task_no_match = re.search(r"\d+", card_id)
        if not task_no_match:
            continue
        task_no = int(task_no_match.group(0))

        # Tip / format
        tip_input = card.find("input", attrs={"name": "q[tip]"}) or card.find("input", id=lambda x: x and "q_tip_" in x)
        tip_val = tip_input.get("value") if tip_input else "1"

        if tip_val == "1":
            task_format = "single-choice"
        elif tip_val == "4":
            task_format = "matching"
        elif tip_val == "12":
            task_format = "own-statement"
        else:
            task_format = "single-choice"

        # Stem
        q_div = card.find(class_="question")
        stem = q_div.get_text(separator="\n", strip=True) if q_div else ""

        # Topic tag verbatim
        exp = card.find(class_="explanation")
        topic_tag = ""
        if exp:
            topic_text = None
            # Scan block tags for "ТЕМА" prefix
            for tag_name in ["p", "b", "strong", "div", "span"]:
                tags = exp.find_all(tag_name)
                for t in tags:
                    t_text = t.get_text().strip()
                    if t_text.startswith("ТЕМА") or "ТЕМА:" in t_text or "ТЕМА." in t_text:
                        # Prefer parent text if it starts with ТЕМА
                        if (
                            t.parent
                            and t.parent.name in ["p", "div"]
                            and t.parent.get_text().strip().startswith("ТЕМА")
                        ):
                            topic_text = t.parent.get_text().strip()
                        else:
                            topic_text = t_text
                        break
                if topic_text:
                    break

            if topic_text:
                cleaned = re.sub(r"^ТЕМА\s*[:\.]\s*", "", topic_text, flags=re.IGNORECASE).strip()
                cleaned = " ".join(cleaned.split())
                topic_tag = f"ТЕМА: {cleaned}"

        # Classify subject (literature vs language)
        topic_lower = topic_tag.lower()
        if any(kw in topic_lower for kw in ["література", "літературн", "творчість", "письменник", "постмодернізм"]):
            subject = "lit"
        else:
            subject = "mova"

        # Parse options and correct answers
        options_json = "[]"
        correct_json = ""

        if task_format == "single-choice":
            ans_divs = card.find_all(class_="answer")
            options = []
            for ans in ans_divs:
                # Exclude span.marker from text extraction
                parts = []
                for child in ans.children:
                    if isinstance(child, str):
                        parts.append(child)
                    elif hasattr(child, "get_text") and not (
                        child.name == "span" and "marker" in child.get("class", [])
                    ):
                        parts.append(child.get_text())
                options.append("".join(parts).strip())
            options_json = json.dumps(options, ensure_ascii=False)

            # Correct answer
            result_input = card.find("input", attrs={"name": "result"})
            result_val = result_input.get("value", "").strip() if result_input else ""
            mapping = {"a": "А", "b": "Б", "c": "В", "d": "Г", "e": "Д"}
            correct_json = mapping.get(result_val.lower(), "")

        elif task_format == "matching":
            cols = card.find_all(class_=lambda x: x and "answers" in x and "col" in x)
            left_options = []
            right_options = []
            left_title = ""
            right_title = ""

            if len(cols) >= 2:
                title_div = cols[0].find(class_="quest-title")
                if title_div:
                    left_title = title_div.get_text().strip()
                for ans in cols[0].find_all(class_="answer"):
                    parts = []
                    for child in ans.children:
                        if isinstance(child, str):
                            parts.append(child)
                        elif hasattr(child, "get_text") and not (
                            child.name == "span" and "marker" in child.get("class", [])
                        ):
                            parts.append(child.get_text())
                    left_options.append("".join(parts).strip())

                title_div = cols[1].find(class_="quest-title")
                if title_div:
                    right_title = title_div.get_text().strip()
                for ans in cols[1].find_all(class_="answer"):
                    parts = []
                    for child in ans.children:
                        if isinstance(child, str):
                            parts.append(child)
                        elif hasattr(child, "get_text") and not (
                            child.name == "span" and "marker" in child.get("class", [])
                        ):
                            parts.append(child.get_text())
                    right_options.append("".join(parts).strip())

            options_dict = {"left": left_options, "right": right_options}
            if left_title:
                options_dict["left_title"] = left_title
            if right_title:
                options_dict["right_title"] = right_title
            options_json = json.dumps(options_dict, ensure_ascii=False)

            # Correct answer (e.g. "1d;2c;3e;4a")
            result_input = card.find("input", attrs={"name": "result"})
            result_val = result_input.get("value", "").strip() if result_input else ""
            correct_map = {}
            if result_val:
                mapping = {"a": "А", "b": "Б", "c": "В", "d": "Г", "e": "Д"}
                pairs = result_val.split(";")
                for p in pairs:
                    if p and len(p) >= 2:
                        left_num = p[0]
                        right_letter = p[1:]
                        correct_map[left_num] = mapping.get(right_letter.lower(), right_letter)
            correct_json = json.dumps(correct_map, ensure_ascii=False)

        elif task_format == "own-statement":
            options_json = "[]"
            correct_json = ""

        # Insert or replace task
        conn.execute(
            """
            INSERT OR REPLACE INTO zno_tasks(
                document_id, year, exam, session, task_no, subject, task_format,
                stem, options_json, correct_json, topic_tag
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (doc_id, year, exam, session, task_no, subject, task_format, stem, options_json, correct_json, topic_tag),
        )
        inserted += 1

    return inserted


def ingest_tasks(conn: sqlite3.Connection, cache_dir: Path):
    """
    Extract and ingest tasks for years 2019, 2020, 2021 from zno.osvita.ua test pages.
    """
    # Find the document IDs for the target years & sessions
    cursor = conn.execute("SELECT id, year, exam, session, subject_scope FROM zno_documents")
    docs = cursor.fetchall()

    total_inserted = 0
    for doc_id, year, exam, session, subject_scope in docs:
        if year not in [2019, 2020, 2021]:
            continue
        # We only crawl combined mova-lit sessions from the web (since there is no separate mova-only online page)
        if subject_scope != "mova-lit":
            continue

        test_id = ONLINE_TEST_MAPPING.get((year, session))
        if not test_id:
            continue

        url = f"https://zno.osvita.ua/ukrainian/{test_id}/"
        cache_path = cache_dir / f"{test_id}_main.html"

        print(f"Fetching tasks for {year} {session} (test_id: {test_id}) from {url}...")
        html = fetch_page_with_rate_limit(url, cache_path)

        inserted = parse_and_insert_tasks(conn, html, doc_id, year, exam, session)
        print(f"Ingested {inserted} tasks for document {doc_id} ({year} {session}).")
        total_inserted += inserted

    return total_inserted


def ingest(db_path: Path, cache_dir: Path) -> int:
    """
    Ingest ZNO booklet metadata and tasks.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        init_db(conn)

        # 1. Ingest metadata
        ingest_documents(conn)
        conn.commit()

        # 2. Extract and ingest online tasks
        total_tasks = ingest_tasks(conn, cache_dir)
        conn.commit()

        # Optimize FTS
        conn.execute("INSERT INTO zno_tasks_fts(zno_tasks_fts) VALUES('optimize')")
        conn.commit()

        return total_tasks
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest ZNO documents and tasks into sources.db")
    parser.add_argument("--db", type=Path, required=True, help="Path to sources.db")
    parser.add_argument(
        "--cache-dir", type=Path, default=Path("tmp/zno_cache"), help="Local cache directory for HTML pages"
    )
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Error: Database {args.db} does not exist.")
        sys.exit(1)

    print(f"Starting ZNO ingestion into {args.db}...")
    inserted_tasks = ingest(args.db, args.cache_dir)
    print(f"Successfully ingested {inserted_tasks} tasks.")
