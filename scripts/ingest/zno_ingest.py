"""
Ingest ZNO booklet metadata and online tasks from zno.osvita.ua into sources.db.
"""

import argparse
import http.client
import json
import math
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

from scripts.ingest.apply_zno_annotations import apply_worksheet_annotations
from scripts.storage.paths import REGISTRY_ROOT

ROOT = Path(__file__).resolve().parents[2]
ZNO_ANNOTATIONS_WORKSHEET = REGISTRY_ROOT / "lexicon" / "paronym_worksheet_candidates.yaml"

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

# Mapping of booklet metadata to the matching interactive test on zno.osvita.ua.
#
# Up to 2021, ``ukrainian`` hosted the combined Ukrainian language and literature
# papers.  The standalone language catalogue, ``ukrmova``, is the authoritative
# online source for the NMT papers from 2022 onward.  The source is keyed by the
# complete booklet identity so that a second session cannot accidentally reuse
# an otherwise similarly named test.
ONLINE_TEST_MAPPING = {
    (2010, "sesiya-1", "mova-lit"): ("ukrainian", 15),
    (2010, "sesiya-2", "mova-lit"): ("ukrainian", 16),
    (2010, "sesiya-3", "mova-lit"): ("ukrainian", 17),
    (2011, "sesiya-1", "mova-lit"): ("ukrainian", 13),
    (2011, "sesiya-2", "mova-lit"): ("ukrainian", 14),
    (2012, "sesiya-1", "mova-lit"): ("ukrainian", 11),
    (2012, "sesiya-2", "mova-lit"): ("ukrainian", 12),
    (2013, "sesiya-1", "mova-lit"): ("ukrainian", 6),
    (2013, "sesiya-2", "mova-lit"): ("ukrainian", 10),
    (2014, "sesiya-1", "mova-lit"): ("ukrainian", 132),
    (2014, "sesiya-2", "mova-lit"): ("ukrainian", 133),
    (2014, "dodatkova", "mova-lit"): ("ukrainian", 130),
    (2015, "osnovna", "mova-lit"): ("ukrainian", 143),
    (2016, "osnovna", "mova-lit"): ("ukrainian", 189),
    (2017, "osnovna", "mova-lit"): ("ukrainian", 240),
    (2017, "dodatkova", "mova-lit"): ("ukrainian", 254),
    (2018, "osnovna", "mova-lit"): ("ukrainian", 299),
    (2018, "dodatkova", "mova-lit"): ("ukrainian", 309),
    (2019, "osnovna", "mova-lit"): ("ukrainian", 347),
    (2019, "dodatkova", "mova-lit"): ("ukrainian", 363),
    (2020, "osnovna", "mova-lit"): ("ukrainian", 401),
    (2020, "dodatkova", "mova-lit"): ("ukrainian", 429),
    (2021, "osnovna", "mova-lit"): ("ukrainian", 471),
    (2021, "dodatkova", "mova-lit"): ("ukrainian", 491),
    (2022, "osnovna", "mova"): ("ukrmova", 617),
    (2023, "sesiya-1", "mova"): ("ukrmova", 619),
    (2023, "sesiya-2", "mova"): ("ukrmova", 620),
    (2024, "sesiya-1", "mova"): ("ukrmova", 622),
    (2024, "sesiya-2", "mova"): ("ukrmova", 623),
    (2025, "sesiya-1", "mova"): ("ukrmova", 667),
    (2025, "sesiya-2", "mova"): ("ukrmova", 668),
}


# The online-test catalogue is not itself a completeness signal: it has one
# entry per booklet, while each entry expands to a full task set.  Keep this
# ledger next to the mapping so a missing or truncated HTML extraction fails
# closed.  ``expected_single_choice_with_letter_key`` is also the expected
# number of all single-choice rows: every such row must have an А–Д key.
def _expected_session(tasks: int, single_choice: int, own_statement: int) -> dict[str, int]:
    return {
        "expected_tasks": tasks,
        "expected_single_choice_with_letter_key": single_choice,
        "own_statement_count": own_statement,
    }


SESSION_COMPLETENESS = {
    (2010, "zno", "sesiya-1"): _expected_session(61, 51, 1),
    (2010, "zno", "sesiya-2"): _expected_session(61, 51, 1),
    (2010, "zno", "sesiya-3"): _expected_session(61, 51, 1),
    (2011, "zno", "sesiya-1"): _expected_session(61, 51, 1),
    (2011, "zno", "sesiya-2"): _expected_session(61, 51, 1),
    (2012, "zno", "sesiya-1"): _expected_session(61, 51, 1),
    (2012, "zno", "sesiya-2"): _expected_session(61, 51, 1),
    (2013, "zno", "sesiya-1"): _expected_session(61, 51, 1),
    (2013, "zno", "sesiya-2"): _expected_session(61, 51, 1),
    (2014, "zno", "sesiya-1"): _expected_session(61, 51, 1),
    (2014, "zno", "sesiya-2"): _expected_session(61, 51, 1),
    (2014, "zno", "dodatkova"): _expected_session(61, 51, 1),
    (2015, "zno", "osnovna"): _expected_session(58, 48, 1),
    (2016, "zno", "osnovna"): _expected_session(58, 48, 1),
    (2017, "zno", "osnovna"): _expected_session(58, 48, 1),
    (2017, "zno", "dodatkova"): _expected_session(58, 48, 1),
    (2018, "zno", "osnovna"): _expected_session(58, 48, 1),
    (2018, "zno", "dodatkova"): _expected_session(58, 48, 1),
    (2019, "zno", "osnovna"): _expected_session(58, 48, 1),
    (2019, "zno", "dodatkova"): _expected_session(58, 48, 1),
    (2020, "zno", "osnovna"): _expected_session(58, 48, 1),
    (2020, "zno", "dodatkova"): _expected_session(58, 48, 1),
    (2021, "zno", "osnovna"): _expected_session(67, 54, 4),
    (2021, "zno", "dodatkova"): _expected_session(67, 54, 4),
    (2022, "nmt", "osnovna"): _expected_session(20, 15, 0),
    (2023, "nmt", "sesiya-1"): _expected_session(30, 25, 0),
    (2023, "nmt", "sesiya-2"): _expected_session(30, 25, 0),
    (2024, "nmt", "sesiya-1"): _expected_session(30, 25, 0),
    (2024, "nmt", "sesiya-2"): _expected_session(30, 25, 0),
    (2025, "nmt", "sesiya-1"): _expected_session(30, 25, 0),
    (2025, "nmt", "sesiya-2"): _expected_session(30, 25, 0),
}
MINIMUM_COMPLETE_TASK_COUNT = 1646


def topic_norm_from_tag(topic_tag: str) -> str | None:
    """Map the source's verbatim Ukrainian topic label into our finite vocabulary.

    This deliberately uses Python ``casefold`` rather than SQLite ``lower``:
    SQLite's built-in lower() only handles ASCII and would miss Ukrainian
    uppercase labels.  ``None`` is reserved for an actually unrecognised tag
    so callers can put it on the residual list rather than silently assigning
    an empty value.
    """
    tag = " ".join(topic_tag.casefold().split())
    if not tag:
        return None
    if "фразеолог" in tag:
        return "phraseology"
    if "орфоеп" in tag or "наголос" in tag:
        return "orthoepic_norm"
    if "орфограф" in tag or "подвоєння букв" in tag:
        return "orthographic_norm"
    if "фонетик" in tag or "графік" in tag or "звуків" in tag or "звуки" in tag:
        return "phonetic"
    if "словотвір" in tag or "будова слова" in tag or "значущі частини слова" in tag:
        return "word_formation"
    if any(marker in tag for marker in ("синтаксис", "словосполуч", "реченн", "підмет", "присудок", "розділов")):
        return "syntactic_norm"
    if any(
        marker in tag
        for marker in (
            "морфолог",
            "іменник",
            "прикметник",
            "числівник",
            "займенник",
            "дієслов",
            "прислівник",
            "відмінок",
            "відмінюван",
            "кличн",
            "ступенів порівняння",
            "частини мови",
        )
    ):
        return "morphological_norm"
    if any(marker in tag for marker in ("лексик", "паронім", "синонім", "антонім", "омонім")):
        return "lexical_norm"
    if any(
        marker in tag
        for marker in ("літератур", "письменник", "творчість", "усна народна", "фольклор", "леся українка")
    ):
        return "literature"
    if any(marker in tag for marker in ("текст", "мовлення", "стилістик")):
        return "text"
    return None


def backfill_topic_norm(conn: sqlite3.Connection) -> dict[str, object]:
    """Fill only empty topic norms and report every non-empty tag not mapped.

    Reviewed worksheet values are intentionally immutable here.  The returned
    residual is JSON-serialisable so callers can expose it in the Practice
    residual report rather than hiding an unmapped source label.
    """
    rows = conn.execute(
        "SELECT id, topic_tag FROM zno_tasks WHERE trim(topic_tag) <> '' AND trim(topic_norm) = '' ORDER BY id"
    ).fetchall()
    updates: list[tuple[str, int]] = []
    residual: dict[str, int] = {}
    for task_id, topic_tag in rows:
        topic_norm = topic_norm_from_tag(str(topic_tag))
        if topic_norm is None:
            residual[str(topic_tag)] = residual.get(str(topic_tag), 0) + 1
            continue
        updates.append((topic_norm, int(task_id)))
    if updates:
        conn.executemany(
            "UPDATE zno_tasks SET topic_norm = ? WHERE id = ? AND trim(topic_norm) = ''",
            updates,
        )
    return {"updated": len(updates), "unmapped": dict(sorted(residual.items()))}


def assert_session_completeness(conn: sqlite3.Connection) -> None:
    """Fail closed unless all mapped ZNO/NMT sessions match the source ledger."""
    rows = conn.execute(
        """
        SELECT year, exam, session,
               count(*) AS tasks,
               sum(CASE WHEN task_format = 'single-choice' THEN 1 ELSE 0 END) AS single_choice,
               sum(CASE WHEN task_format = 'single-choice' AND correct_json IN ('А', 'Б', 'В', 'Г', 'Д') THEN 1 ELSE 0 END) AS letter_keyed,
               sum(CASE WHEN task_format = 'own-statement' THEN 1 ELSE 0 END) AS own_statement
        FROM zno_tasks
        GROUP BY year, exam, session
        ORDER BY year, exam, session
        """
    ).fetchall()
    actual = {
        (int(year), str(exam), str(session)): (int(tasks), int(letter_keyed), int(own_statement), int(single_choice))
        for year, exam, session, tasks, single_choice, letter_keyed, own_statement in rows
    }
    errors: list[str] = []
    if set(actual) != set(SESSION_COMPLETENESS):
        errors.append(f"session keys differ: expected={sorted(SESSION_COMPLETENESS)} actual={sorted(actual)}")
    for key, expected in SESSION_COMPLETENESS.items():
        observed = actual.get(key)
        if observed is None:
            continue
        tasks, letter_keyed, own_statement, single_choice = observed
        observed_counts = {
            "expected_tasks": tasks,
            "expected_single_choice_with_letter_key": letter_keyed,
            "own_statement_count": own_statement,
        }
        if observed_counts != expected:
            errors.append(f"{key}: expected={expected} actual={observed_counts}")
        if single_choice != letter_keyed:
            errors.append(f"{key}: {single_choice - letter_keyed} single-choice rows lack an А–Д key")
    total_tasks = sum(value[0] for value in actual.values())
    if total_tasks < MINIMUM_COMPLETE_TASK_COUNT:
        errors.append(f"task count dropped below {MINIMUM_COMPLETE_TASK_COUNT}: {total_tasks}")
    if errors:
        raise ValueError("ZNO/NMT completeness ledger failed:\n" + "\n".join(errors))


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


# Local command-line acquisition policy; intentionally no shared network layer.
USER_AGENT = (
    "LearnUkrainianBot/1.0 "
    "(+https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues)"
)
_access_stopped = False
_robots_delays: dict[str, float] = {}
_robots_states: dict[str, dict | None] = {}
_request_times: dict[str, float] = {}


class AccessStopped(RuntimeError):
    """A source denied acquisition; no later network request is allowed this run."""


def _check_access(status: int, headers: object, body: str = "") -> None:
    global _access_stopped
    fields = {str(k).lower(): str(v).lower().strip() for k, v in headers.items()}
    lowered = body[:8000].lower()
    challenged = fields.get("cf-mitigated") == "challenge" or any(
        marker in lowered for marker in (
            "checking your browser", "cf-browser-verification", "cf_chl_", "cf-chl-",
            "attention required! | cloudflare", "enable javascript and cookies to continue",
        )
    ) or bool(re.search(r"<title[^>]*>\s*just a moment", lowered))
    if _access_stopped or status in {403, 429} or challenged:
        _access_stopped = True
        raise AccessStopped("Source access denied or challenged; acquisition stopped for this run")


def _robots_stop(reason: str) -> None:
    global _access_stopped
    _access_stopped = True
    raise AccessStopped(reason)


def _robots_token(header: str) -> bytes:
    """Derive the RFC product token from the identification actually sent."""
    raw = header.encode("utf-8").lower()
    end = 0
    while end < len(raw) and (97 <= raw[end] <= 122 or raw[end] in b"_-"):
        end += 1
    if not end:
        _robots_stop("robots_configuration")
    return raw[:end]


def _robots_parse(body: bytes, header: str) -> dict:
    """Admit raw records under the adopted #8999 fail-closed contract."""
    token = _robots_token(header)
    product = header.encode("utf-8").split(b"/", 1)[0].lower()
    unresolved = len(body) > 512000 or b"\x00" in body or body.startswith(
        (b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff")
    )
    if body.startswith(b"\xef\xbb\xbf"):
        body = body[3:]
    groups = []
    agents, rules, delays = [], [], []
    orphan = []
    seen_agent = directives = False
    # Only CR/LF delimit records: bytes.splitlines would also split CTLs.
    for line in body.replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n"):
        line = line.split(b"#", 1)[0]
        key, colon, value = line.partition(b":")
        key, value = key.strip(b" \t").lower(), value.strip(b" \t")
        if not colon:
            words = key.split()
            key = words[0] if words else b""
        if key == b"user-agent":
            seen_agent = True
            if not colon:
                unresolved = True
            if directives:
                groups.append((agents, rules, delays))
                agents, rules, delays, directives = [], [], [], False
            value = value.lower()
            leading = 0
            while leading < len(value) and (97 <= value[leading] <= 122 or value[leading] in b"_-"):
                leading += 1
            if value == b"*" or value == token:
                agents.append(value)
            elif value.startswith(b"*") or value[:leading] == token or value in product:
                unresolved = True
                agents.append(value)
            else:
                agents.append(value)
        elif key in (b"allow", b"disallow", b"crawl-delay"):
            directives = bool(agents)
            if key == b"crawl-delay":
                if colon and agents:
                    try:
                        delay = float(value)
                    except ValueError:
                        continue
                    if math.isfinite(delay) and delay >= 0:
                        delays.append(delay)
                continue
            malformed = not colon
            if value:
                try:
                    value.decode("utf-8", errors="strict")
                except UnicodeDecodeError:
                    malformed = True
                malformed |= any(o <= 32 or o == 127 for o in value) or value[:1] not in (b"/", b"*")
                malformed |= any(
                    o == 37 and (i + 2 >= len(value) or any(h not in b"0123456789abcdefABCDEF" for h in value[i + 1:i + 3]))
                    for i, o in enumerate(value)
                )
                malformed |= key == b"allow" and b"$" in value[:-1]
            if key == b"allow" and (malformed or not seen_agent):
                continue
            if malformed or value:
                # None records an unresolved Disallow, selected only with its group.
                rule = (key == b"allow", None if malformed else value)
                (rules if seen_agent else orphan).append(rule)
    groups.append((agents, rules, delays))
    selected = [g for g in groups if token in g[0]] or [g for g in groups if b"*" in g[0]]
    effective = orphan + [rule for _names, values, _delays in selected for rule in values]
    unresolved |= any(value is None for _allow, value in effective)
    return {"rules": effective, "unresolved": unresolved,
            "delay": max((d for _names, _rules, values in selected for d in values), default=0.0)}


def _robots_crawl_delay(body: str) -> float:
    """The same exact group selection drives both permission and pacing."""
    return _robots_parse(body.encode("utf-8"), USER_AGENT)["delay"]


def _robots_canonical(raw: bytes, *, rule: bool, reading: int) -> tuple[str, bool, int]:
    """R1 uses atomic escape tokens; R2 uses encoded canonical characters."""
    result = []
    anchored = False
    specificity = 0
    i = 0
    unreserved = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    reserved = b":/?#[]@!&'()+,;="
    while i < len(raw):
        octet = raw[i]
        if octet == 37 and i + 2 < len(raw) and all(h in b"0123456789abcdefABCDEF" for h in raw[i + 1:i + 3]):
            octet = int(raw[i + 1:i + 3], 16)
            escaped = octet not in unreserved
            i += 3
        else:
            final = i == len(raw) - 1
            i += 1
            if rule and octet == 42:
                result.append("*")
                specificity += 1
                continue
            if rule and octet == 36 and final:
                anchored = True
                specificity += 1
                continue
            escaped = octet not in unreserved and (reading == 2 or octet not in reserved)
        if escaped:
            result.append(chr(0xE000 + octet) if reading == 1 else f"%{octet:02X}")
            specificity += 3
        else:
            result.append(chr(octet))
            specificity += 1
    return "".join(result), anchored, specificity


def _robots_match(pattern: str, anchored: bool, target: str) -> bool:
    """Leftmost segment matching, O(pattern length * target length), no backtracking."""
    segments = pattern.split("*")
    if not target.startswith(segments[0]):
        return False
    position = len(segments[0])
    if len(segments) == 1:
        return not anchored or position == len(target)
    for segment in segments[1:-1]:
        found = target.find(segment, position)
        if found < 0:
            return False
        position = found + len(segment)
    last = segments[-1]
    if anchored:
        return len(target) - len(last) >= position and target.endswith(last)
    return target.find(last, position) >= 0


def _robots_target(url: str) -> bytes:
    # Preserve params, a bare question mark, and the exact query; remove fragment.
    target = url.split("#", 1)[0]
    if "://" in target:
        target = target.split("://", 1)[1]
        cut = min((p for p in (target.find("/"), target.find("?")) if p >= 0), default=len(target))
        target = target[cut:]
    if not target.startswith("/"):
        target = "/" + target
    return target.encode("utf-8")


def _robots_check_target(url: str) -> None:
    _check_access(0, {})
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    state = _robots_states.get(origin)
    if state is None or state["unresolved"]:
        _robots_stop("robots_unresolved")
    target = _robots_target(url)
    path = target.split(b"?", 1)[0]
    if _robots_canonical(path, rule=False, reading=1)[0] == "/robots.txt":
        return
    decisions = []
    for reading in (1, 2):
        canonical = _robots_canonical(target, rule=False, reading=reading)[0]
        top = []
        best = -1
        for allow, value in state["rules"]:
            pattern, anchored, specificity = _robots_canonical(value, rule=True, reading=reading)
            if _robots_match(pattern, anchored, canonical):
                if specificity > best:
                    top, best = [], specificity
                if specificity == best:
                    top.append((allow, pattern, anchored))
        allows = {(pattern, anchored) for allow, pattern, anchored in top if allow}
        denies = {(pattern, anchored) for allow, pattern, anchored in top if not allow}
        decisions.append("allow" if not top or (allows and denies <= allows) else "disallow" if not allows else "ambiguous")
    if decisions != ["allow", "allow"]:
        _robots_stop("robots_disallowed" if decisions == ["disallow", "disallow"] else "robots_ambiguous")


def _wait_for_request(url: str, floor: float = 0.0) -> None:
    _check_access(0, {})
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    delay = max(floor, _robots_delays.get(origin, 0.0))
    previous = _request_times.get(origin)
    if previous is not None:
        remaining = delay - (time.monotonic() - previous)
        if remaining > 0:
            time.sleep(remaining)
    _request_times[origin] = time.monotonic()


FETCH_TIMEOUT_SECONDS = 30


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Inspect the redirect before issuing the next source request.
        return None


def _open(request):
    return urllib.request.build_opener(_NoRedirect()).open(request, timeout=FETCH_TIMEOUT_SECONDS)


def _fetch(url: str, rate_limit: float, *, robots: bool = True) -> str | bytes:
    _check_access(0, {})
    _robots_token(USER_AGENT)
    for _hop in range(9 if robots else 11):
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if robots and origin not in _robots_states:
            _robots_states[origin] = None
            _robots_delays[origin] = 0.0
            try:
                state = _robots_parse(_fetch(f"{origin}/robots.txt", rate_limit, robots=False), USER_AGENT)
                _robots_states[origin] = state
                _robots_delays[origin] = state["delay"]
            except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
                _robots_stop(f"robots_unreachable: {type(exc).__name__}")
        if robots:
            _robots_check_target(url)
        _wait_for_request(url, rate_limit)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            response = _open(request)
        except urllib.error.HTTPError as exc:
            # urllib represents a deliberately unfollowed redirect as HTTPError.
            response = exc
        with response:
            status = getattr(response, "status", getattr(response, "code", 200))
            headers = getattr(response, "headers", {})
            _check_access(status, headers)
            body = response.read()
            _check_access(status, headers, body[:8000].decode("utf-8", errors="replace"))
            if robots and status >= 400:
                raise urllib.error.HTTPError(url, status, "Source HTTP error", headers, None)
            location = headers.get("Location", "")
            if status in {301, 302, 303, 307, 308} and location:
                url = urljoin(url, location)
                continue
            if not robots:
                if 200 <= status < 300:
                    return body
                if 400 <= status < 500:
                    return b""
                _robots_stop("robots_unreachable")
            if not 200 <= status < 300:
                raise urllib.error.HTTPError(url, status, "Source HTTP error", headers, None)
            return body.decode("utf-8", errors="strict")
    if not robots:
        _robots_stop("robots_unreachable: redirect limit")
    raise urllib.error.URLError("Acquisition exceeded redirect limit")


def fetch_page_with_rate_limit(url: str, cache_path: Path, rate_limit: float = 2.0) -> str:
    """Fetch with per-origin observed robots floors and validated cache hits."""
    _check_access(0, {})
    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        _check_access(200, {}, html)
        return html

    html = _fetch(url, rate_limit)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html, encoding="utf-8")
    return html


def derive_task_metadata(prompt: str, options_json: str, correct_json: str, task_format: str) -> tuple[str, str]:
    """Derive only task metadata that is explicit in the source page.

    Paronym pairs require a reviewed lexical analysis and are applied separately
    with ``apply_zno_annotations.py``.  The source page itself unambiguously
    identifies synonym, antonym, and lexical-error prompts, while a
    single-choice наголос prompt identifies its target through the published
    correct answer.
    """
    prompt_normalized = prompt.casefold()
    task_subtype = ""
    if "антонім" in prompt_normalized:
        task_subtype = "antonym"
    elif "синонім" in prompt_normalized:
        task_subtype = "synonym"
    elif "лексичн" in prompt_normalized and "помилк" in prompt_normalized:
        task_subtype = "lexical_error"

    stress_word = ""
    if task_format == "single-choice" and "наголос" in prompt_normalized:
        try:
            options = json.loads(options_json)
        except json.JSONDecodeError:
            options = []
        answer_index = {"А": 0, "Б": 1, "В": 2, "Г": 3, "Д": 4}.get(correct_json)
        if isinstance(options, list) and answer_index is not None and answer_index < len(options):
            stress_word = options[answer_index]

    return task_subtype, stress_word


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
        prompt_parts = q_div.find_all("p", recursive=False) if q_div else []
        task_prompt = prompt_parts[-1].get_text(separator=" ", strip=True) if prompt_parts else stem

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

        task_subtype, stress_word = derive_task_metadata(task_prompt, options_json, correct_json, task_format)

        # Keep manually reviewed annotations on a refresh.  ``INSERT OR
        # REPLACE`` deletes the previous row before inserting a new one, which
        # silently clears topic_norm, task_subtype, paronym_pair, and
        # stress_word.  An upsert updates parsed source fields in place instead.
        conn.execute(
            """
            INSERT INTO zno_tasks(
                document_id, year, exam, session, task_no, subject, task_format,
                stem, options_json, correct_json, topic_tag, task_subtype, stress_word
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id, task_no) DO UPDATE SET
                year=excluded.year,
                exam=excluded.exam,
                session=excluded.session,
                subject=excluded.subject,
                task_format=excluded.task_format,
                stem=excluded.stem,
                options_json=excluded.options_json,
                correct_json=excluded.correct_json,
                topic_tag=excluded.topic_tag
        """,
            (
                doc_id,
                year,
                exam,
                session,
                task_no,
                subject,
                task_format,
                stem,
                options_json,
                correct_json,
                topic_tag,
                task_subtype,
                stress_word,
            ),
        )
        inserted += 1

    return inserted


def ingest_tasks(conn: sqlite3.Connection, cache_dir: Path):
    """
    Extract and ingest tasks from the matching zno.osvita.ua test pages.
    """
    # Find the document IDs that have a verified interactive source.
    cursor = conn.execute("SELECT id, year, exam, session, subject_scope FROM zno_documents")
    docs = cursor.fetchall()

    total_inserted = 0
    for doc_id, year, exam, session, subject_scope in docs:
        source = ONLINE_TEST_MAPPING.get((year, session, subject_scope))
        if not source:
            continue

        catalogue, test_id = source
        url = f"https://zno.osvita.ua/{catalogue}/{test_id}/"
        cache_path = cache_dir / f"{catalogue}_{test_id}.html"

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
        # HTML contains source text only; restore the checked-in reviewed
        # worksheet before filling any remaining empty topic classifications.
        apply_worksheet_annotations(conn, ZNO_ANNOTATIONS_WORKSHEET)
        backfill_topic_norm(conn)
        assert_session_completeness(conn)
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
