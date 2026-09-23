#!/usr/bin/env python3
"""Build Grammar Component for Open Model Data (#8342, Epic #6321).

Rebuilds the verified Ukrainian grammar, valency, prepositional government,
and anti-calque training and evaluation datasets from authentic human-annotated
sentences in UA-GEC (commit 4757f72f192c4a41e4c8fb1d9690a948f87cf6d6).

Features:
1. Strict 75.0% substantive corrections / 25.0% clean controls mixture.
2. In-scope tags: strictly G/* + F/Calque (16 tags).
3. Document-level 90:10 train/eval partition strictly by doc_id SHA-256 hash.
4. Clean controls drawn from 0-error train UA-GEC sentences and Brown-UK.
5. Task mix: 45% silent rewrites / 55% explained corrections.
6. 100% authoritative citations matching approved Ukrainian linguistics authorities.
7. Compliant with audit_dataset_acceptance.py and profile grammar_8342.yaml.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import math
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.projects.open_model_data.grammar_linguistic_catalog import (
    AUTHORITY_PROFILES,
    CONTROL_PROFILE,
    IN_SCOPE_TAGS,
    PROMPT_TEMPLATES_BY_REGISTER,
    PROMPT_TEMPLATES_EVAL,
    TAG_TO_COARSE_CATEGORY,
    build_query,
    build_query_eval,
    build_reasoning_and_response,
    build_reasoning_and_response_eval,
    classify_sentence_register,
    resolve_specific_linguistic_citation,
)

DEFAULT_UA_GEC_TRAIN_M2 = (
    PROJECT_ROOT / "data" / "ua-gec" / "data" / "gec-fluency" / "train" / "gec-fluency.train.m2"
)
DEFAULT_UA_GEC_TEST_M2 = (
    PROJECT_ROOT / "data" / "ua-gec" / "data" / "gec-fluency" / "test" / "gec-fluency.test.m2"
)
DEFAULT_FIREWALL_MANIFEST = (
    PROJECT_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "evidence"
    / "grammar_held_out_firewall_manifest.json"
)
DEFAULT_BROWN_UK_EVAL = (
    PROJECT_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "release"
    / "uldr_v05_grammar_valency"
    / "brown_uk_negative_control_eval.jsonl"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "components" / "grammar"


def detokenize(text: str) -> str:
    """Detokenize Ukrainian text from Stanza space-separated tokenization."""
    if not text:
        return ""
    # 0. Clean CJK brackets, zero-width characters, and non-breaking spaces
    text = text.replace("《", "«").replace("》", "»")
    text = text.replace("\u4e00", "—")
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e\ufeff]", "", text)
    text = text.replace("\u00a0", " ")

    # 0a. Close hyphenated initials, stretched words, and numeric ranges BEFORE converting isolated dashes
    text = re.sub(r"\b([А-ЯІЇЄҐ])\.\s*[—–-]\s*([А-ЯІЇЄҐ])\.", r"\1.-\2.", text)
    text = re.sub(r"\b([а-яіїєґА-ЯІЇЄҐ])-([а-яіїєґА-ЯІЇЄҐ])\s*[—–-]\s*([а-яіїєґА-ЯІЇЄҐ])\b", r"\1-\2-\3", text)
    text = re.sub(r"(\d+)\s*[—–-]\s*(\d+)", r"\1–\2", text)
    text = re.sub(r"\b([А-ЯІЇЄҐа-яіїєґ]+)\s*[-–—]\s*(\d+)\b", r"\1-\2", text)

    # 0b. Close hyphenated compound particles, coordinate pairs, and prefixes
    compound_prefixes = (
        "контент|обер|онлайн|офлайн|інтернет|веб|аудіо|відео|кібер|смарт|еко|агро|етно|мега|гіпер|супер|ультра|екстра|"
        "темно|світло|ясно|блідо|яскраво|густо|синьо|жовто|червоно|зелено|чорно|біло|сіро|коричнево|"
        "рожево|фіолетово|золотисто|сріблясто|туди|плюс|врешті|караван|стейт|комікс|фолк|арт|рок|поп|"
        "джаз|офіс|бізнес|прем'єр|віце|екс|міні|максі|міді|мікро|макро|топ|шоу|фітнес|блок|конференц|"
        "прес|генерал|штаб|лейтенант|майор|полковник|член|кореспондент|соціал|націонал|ліберально|"
        "історико|науково|технічно|фізико|хіміко|економіко|суспільно|політично|військово|художньо|"
        "літературно|музично|культурно|організаційно|навчально|виробничо"
    )
    text = re.sub(rf"\b({compound_prefixes})\s*[-–—]\s*([а-яіїєґА-ЯІЇЄҐ\w'-]+)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(туди)\s*[-–—]\s*(сюди)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(плюс)\s*[-–—]\s*(мінус)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(врешті)\s*[-–—]\s*(решт)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(більш)\s*[-–—]\s*(менш)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(часто)\s*[-–—]\s*(густо)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(рано)\s*[-–—]\s*(вранці)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(мало)\s*[-–—]\s*(помалу)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(видимо)\s*[-–—]\s*(невидимо)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(знову)\s*[-–—]\s*(таки)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b([а-яіїєґА-ЯІЇЄҐ\w'-]{2,})\s*[-–—]\s*\1\b", r"\1-\1", text, flags=re.I)
    text = re.sub(r"\b([а-яіїєґА-ЯІЇЄҐ\w'-]+)\s*[—–-]\s*(от|таки|будь|небудь|бо|но|то)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(будь|хто|що|як|де|куди|коли)\s*[—–-]\s*(будь|небудь|то)\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b(по)\s*[—–-]\s*([а-яіїєґА-ЯІЇЄҐ\w']+(?:ому|ему|ськи|цьки|ки))\b", r"\1-\2", text, flags=re.I)
    text = re.sub(r"\b([а-яіїєґА-ЯІЇЄҐ]{4,}(?:о|е|є))\s*[-–]\s*([а-яіїєґА-ЯІЇЄҐ]{5,}(?:ий|ого|ому|им|ім|а|ої|ій|у|ою|е|і|их|ими|я|є))\b", r"\1-\2", text, flags=re.I)

    # 0c. Clean adjacent dashes and dash combos: e.g. "— -" -> "— "
    text = re.sub(r"[—–-]\s*[—–-]\s*", "— ", text)
    text = re.sub(r",\s*—\s*", ", — ", text)
    # 0d. Clean hyphen-as-dash: replace space-hyphen-space and space-en-dash-space with standard em-dash
    text = re.sub(r"\s+[-–]\s+", " — ", text)
    text = re.sub(r"\s+—\s+", " — ", text)
    # 0e. Clean bracket/brace artifacts: e.g. "–}", "—}", "-}"
    text = re.sub(r"[—–-]\s*[\]\}\)]", "", text)
    # 1. Close spaces before punctuation: , . ! ? : ; % ) ] } » ”
    text = re.sub(r"\s+([,.\!?:;%\]\}\)»”])", r"\1", text)
    # 2. Close spaces after opening quotes/brackets: ( [ { « “
    text = re.sub(r"([(\[\{«“])\s+", r"\1", text)
    # 2b. Normalize quotes: curly and paired straight quotes to standard Ukrainian chevron quotes «...»
    text = text.replace("“", "«").replace("”", "»").replace("„", "«")
    text = re.sub(r'"([^"]*)"', r"«\1»", text)
    text = re.sub(r'([\?!][»\"])[\s,]*(—)', r'\1 \2', text)
    text = re.sub(r'([\?!]),', r'\1', text)
    text = re.sub(r':\s*—', ': ', text)
    # Handle time expression spacing: e.g. "14: 00" -> "14:00"
    text = re.sub(r"\b(\d{1,2}):\s+(\d{2})\b", r"\1:\2", text)
    # 3. Handle comma immediately before opening parenthesis: e.g. ", (" -> " ("
    text = re.sub(r",\s*\(", " (", text)
    # 4. Handle hyphenated compounds: e.g. "Санта - Круз" -> "Санта-Круз"
    text = re.sub(r"(\b[\w'-]+)\s*-\s*([\w'-]+\b)", r"\1-\2", text)
    # 5. Handle decimal numbers with comma: in Ukrainian standard typography, 1.5 -> 1,5
    text = re.sub(r"(\d+),\s+(\d+)", r"\1,\2", text)
    text = re.sub(r"\b(\d+)\.\s*(\d+)\b", r"\1,\2", text)
    # 6. Handle ellipses like . . . -> ... and clean stray punctuation around ellipses
    text = re.sub(r"\.\s+\.\s+\.", "...", text)
    text = re.sub(r"\s+\.\.\.", "...", text)
    text = re.sub(r"\.\.\.\s*[,;:]+", "...", text)
    text = re.sub(r"\.\.\.\s+", "... ", text)
    text = re.sub(r"[,;:]+\s*([»”\"\)])", r"\1", text)
    text = re.sub(r"([«“\(\[])\s*[,;:]+", r"\1", text)
    # 7. Normalize all apostrophe variants to standard ASCII '
    text = re.sub(r"[’ʼ‘`´ʹ‛\x27]", "'", text)
    text = re.sub(r"'\s+", "'", text)
    text = re.sub(r"\s+'", "'", text)
    return text.strip()


RUSSIANISM_PATTERNS = [
    r"\bпо\s+[а-яіїєґ]+(?:ам|ям|ах|ях|у|ові|еві)\b",
    r"\bприступа(?:ти|ємо|ють|є|в|ла|ли)\s+до\b",
    r"\bприйняти\s+за\b",
    r"\bперед\s+чим\b",
    r"\bв\s+якості\b",
    r"\bв\s+силу\b",
    r"\bтим\s+не\s+менше\b",
    r"\bна\s+самому\s+ділі\b",
    r"\bв\s+кінці\s+кінців\b",
    r"\bмова\s+йде\b",
    r"\bслідуюч\w*\b",
    r"\bоточуюч\w*\b",
    r"\bбажаюч\w*\b",
    r"\bпалаюч\w*\b",
    r"\bпадаюч\w*\b",
    r"\bдіюч\w*\b",
    r"\bіснуюч\w*\b",
    r"\bведуч\w*\b",
    r"\bкеруюч\w*\b",
    r"\bзнаюч\w*\b",
    r"\bчитаюч\w*\b",
    r"\bпрацююч\w*\b",
    r"\bзвисаюч\w*\b",
    r"\bпідстрибуюч\w*\b",
    r"\bпроводжаюч\w*\b",
    r"\bпровожа\w*\b",
    r"\bрефлекту\w*\b",
    r"\bоперу\w*\s+з\b",
    r"\bвраховуючи\s+той\s+факт\b",
    r"\bвпадл\w*\b",
    r"\bгаплик\b",
    r"\bшо\b",
    r"\bбухло\b",
    r"\bчува[кч]\w*\b",
    r"\bуткнув\b",
    r"\bспоглядаючи\s+на\b",
    r"\bнапередодні\s+кабінет\w*\b",
    r"\bне\s+порівняти\s+тяжк\w*\b",
    r"\bза\s+\w+\s+хвилин\w*\s+десят\w*\b",
    r"\bвід\s+знає\b",
    r"\bсвинськ\w*\b",
    r"\bжалі\w+ся\b",
    r"\bпропагандиськ\w*\b",
    r"\bкому\s+попало\b",
    r"\bна\s+підхваті\b",
    r"\bсморка\w*\b",
    r"\bможе-таки\b",
    r"\bавось\b",
    r"\bв\s+[вф][а-яіїєґ]\w*\b",
    r"\bпальт(?:і|а|ом|у|ів|ами|ах)\b",
    r"\bкін(?:і|а|ом|у|ів|ами|ах)\b",
    r"\b[ву]\s+метрі\b",
    r"\bпотрібні,\s*цікаві\b",
    r"\bрішучесхаменув\w*\b",
    r"\bпо\s+лиці\b",
    r"\bвідміти(?:ти|в|ла|ли|мо|те|ть|всь|лася)\b",
    r"\bвідміча\w*\b",
    r"\bдо\s+тих\s+пір\b",
    r"\bна\s+зараз\b",
    r"\bзвітува\w*\b",
    r"\bпо\s+моїй\s+милості\b",
    r"\bявил\w*\b",
    r"\bперевірч\w*\b",
    r"\bув\s+[А-ЯІЇЄҐа-яіїєґ]\w*\b",
    r"\bҐріммів\b",
    r"\bнам\s+представили\b",
    r"\bпредставили\s+(?:публіці|читачам|глядачам|нам|вам|їм|громаді|колективу)\b",
    r"\bне\s+про\s+супереч\w*\b",
    r"\bчерез\s+у\s+них\b",
    r"\bвони\s+зробити\b",
    r"\bтільки\s+те\s+й\s+дума\w*\b",
    r"\bпо\s+офіс\w*\b",
    r"\bз\s+керування\s+ними\b",
    r"\bвпадатиме\s+за\b",
    r"\bчасом\s+близько\s+сотень\b",
    r"\bпітливість,\s*температур\w*\b",
    r"\bпокращува\w*\b",
    r"\b[ву]\s+деяк\w*\s+мір\w*\b",
    r"\b[ву]\s+сам(?:ої|ого)\s+[А-ЯІЇЄҐ]\w*\b",
    r"\b[ву]\s+самої\b",
    r"\bбрав\s+курс\w*\b",
    r"\bбрати\s+курс\w*\b",
    r"\b(?:[тм]рах|[їі]б|ху[йї]|пизд|бля[дт]|єбат|єбан|потрах)\w*\b",
    r"\bто\s+[а-яіїєґ]+(?:ша|ший|ше|ші)\b",
    r"\bтому\s+що\s+[а-яіїєґ\w\s]+,\s*то\b",
    r"\bодне\s+від\s+одного\b",
    r"\bпро\s+терен[а-яіїєґ\s,]+мудра\s+притча\b",
    r"\bмалюнку\b",
    r"\bзупинімося\b",
    r"\bзупинімось\b",
    r"\bборотьб\w*\s+(?!з\b|проти\b|за\b|між\b)[а-яіїєґ]+(?:ом|ем|ям|ою|ею|ями|ами|ях|ах|у|ю|і)\b",
    r"\bщоб\s+(?:повністю|зовсім|дуже|абсолютно)\s+[а-яіїєґ]+(?:ння|ття)\b",
    r"\bвиясни\w*\b",
    r"\bшахматн\w*\b",
    r"\b[Кк]от\b",
    r"\bприбавля\w*\b",
    r"\bзнову\s+таки\b",
    r"\bвірогідн\w*\b",
    r"\bспогляда\w*(\s+[а-яіїєґ\w'-]+){0,4}\s+на\b",
    r"\bскоріш\s+за\s+все\b",
    r"\b[ву]\s+рамках\b",
    r"\bцін[а-яіїєґ]*\s+на\b",
    r"\bпоназбирува\w*\b",
    r"\bярд\w*\b",
    r"\bзаядл\w*\b",
    r"\bцарил\w*\b",
    r"\bзлодіянн\w*\b",
    r"\bзакцентува\w*\b",
    r"\bвитріщив\s+очі\b",
    r"\bпосмутнівш\w*\b",
    r"\bбрись\b",
    r"\bу\s+новий\s+рік\b",
]

ACTIVE_PARTICIPLE_EXCEPTIONS = {
    "гарячий", "гаряча", "гаряче", "гарячі", "гарячого", "гарячій", "гарячим", "гарячих", "гарячими", "гарячу",
    "дрімучий", "дрімуча", "дрімуче", "дрімучі", "дрімучого", "дрімучій", "дрімучим", "дрімучих", "дрімучими", "дрімучу",
    "родючий", "родюча", "родюче", "родючі", "родючого", "родючій", "родючим", "родючих", "родючими", "родючу",
    "живлючий", "живлюча", "живлюче", "живлючі", "живлючого", "живлючій", "живлючим", "живлючих", "живлючими", "живлючу",
    "могутній", "могутня", "могутнє", "могутні",
    "терплячий", "терпляча", "терпляче", "терплячі", "терплячого", "терплячій", "терплячим", "терплячих", "терплячими", "терплячу",
    "балакучий", "балакуча", "балакуче", "балакучі",
    "колючий", "колюча", "колюче", "колючі",
    "пахучий", "пахуча", "пахуче", "пахучі",
    "пекучий", "пекуча", "пекуче", "пекучі",
    "лежачий", "лежача", "лежаче", "лежачі",
    "сидячий", "сидяча", "сидяче", "сидячі",
    "стоячий", "стояча", "стояче", "стоячі",
    "ходячий", "ходяча", "ходяче", "ходячі",
    "висячий", "висяча", "висяче", "висячі",
    "невмирущий", "невмируща", "невмируще", "невмирущі",
    "болючий", "болюча", "болюче", "болючі",
    "блискучий", "блискуча", "блискуче", "блискучі",
    "нетямущий", "тямущий", "значущий", "значуща", "значуще", "значущі",
}


_VESUM_CONN: sqlite3.Connection | None = None


def _get_vesum_cur() -> sqlite3.Cursor | None:
    global _VESUM_CONN
    if _VESUM_CONN is None:
        db_path = PROJECT_ROOT / "data" / "vesum.db"
        if db_path.is_file():
            try:
                _VESUM_CONN = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            except Exception:
                _VESUM_CONN = None
    return _VESUM_CONN.cursor() if _VESUM_CONN is not None else None


def has_active_participle(text: str, vesum_cur: sqlite3.Cursor | None = None) -> bool:
    """Detect non-normative present active participles (-учий, -ючий, -ачий, -ячий)."""
    cur = vesum_cur or _get_vesum_cur()
    matches = re.findall(
        r"\b[а-яіїєґА-ЯІЇЄҐ]+(?:уч|юч|ач|яч)(?:ий|ого|ому|им|ім|а|ої|ій|у|ою|е|і|их|ими)\b",
        text,
        re.IGNORECASE,
    )
    for m in matches:
        low = m.lower()
        if low in ACTIVE_PARTICIPLE_EXCEPTIONS:
            continue
        if cur is not None:
            rows = cur.execute("SELECT tags FROM forms_all WHERE word_form = ?", (low,)).fetchall()
            if any("actv" in r[0] for r in rows):
                return True
            if rows and all("actv" not in r[0] for r in rows):
                continue
        if not any(low.startswith(p) for p in ("дит", "хлоп", "дівч", "собач", "теляч", "куряч", "котяч", "пташ", "жаб")):
            return True
    return False


def has_russianism(text: str, vesum_cur: sqlite3.Cursor | None = None) -> bool:
    """Check for obvious Russianisms, Sovietisms, vulgar slang, or active participles."""
    if any(re.search(pat, text, re.IGNORECASE) for pat in RUSSIANISM_PATTERNS):
        return True
    return has_active_participle(text, vesum_cur=vesum_cur)


def is_clean_control(text: str, vesum_cur: sqlite3.Cursor | None = None) -> bool:
    """Check that control sentence is a clean, authentic, complete Ukrainian sentence."""
    if not text:
        return False
    s_strip = text.strip()
    # Sentence must start with capital letter or quote + capital letter
    if not (s_strip[0].isupper() or (s_strip[0] in '«"“' and len(s_strip) > 1 and s_strip[1].isupper())):
        return False
    # Strictly Cyrillic: zero Latin characters in controls
    if re.search(r"[a-zA-Z]", text):
        return False
    # Reject CJK characters and East Asian punctuation
    if re.search(r"[\u2e80-\u9fff\u3000-\u303f\uff00-\uffef]", text):
        return False
    # Reject zero-width characters and control codes
    if re.search(r"[\u200b-\u200f\u202a-\u202e\ufeff]", text):
        return False
    # Reject math symbols or special characters including slashes
    if any(c in text for c in "<>~=@#$^&*_+/\\"):
        return False
    # Reject non-standard or curly apostrophes
    if re.search(r"[’ʼ‘`´ʹ‛]", text):
        return False
    # Reject emojis or unusual symbols
    if any(unicodedata.category(c) == "So" for c in text):
        return False
    # Reject editorial brackets/braces/ellipses: e.g. [...] or stray { } [ ]
    if re.search(r"\[\s*[\.…]+\s*\]", text) or any(c in text for c in "{}[]"):
        return False
    # Reject subordinate clause fragments at start
    if re.search(r"^(?:Як\s+колись|Немовби|Немов|Наче|Неначе|Нібито|Ніби)\b", text):
        return False
    # Reject direct address with masculine nominative personal names instead of vocative
    if re.search(
        r"\b(?:Ти|ти),\s+(?:Іван|Петро|Михайло|Олександр|Дмитро|Андрій|Тарас|Сергій|Володимир|Юрій|Богдан|Василь|Степан|Остап|Орест|Ярослав|Максим|Павло)\b",
        text,
    ):
        return False
    # Reject broken agreement or garbled constructions
    if re.search(r"\bНайважливіше\s+—\s+додаєте\b", text):
        return False
    if re.search(r"\bзахоплені\s+загальним\s+порушенням\b", text):
        return False
    # Reject split «не»
    if re.search(r"\bне\s+(?:високоточн|правильн|можлив|виправдан|доречн|безпечн|великод|вдачн)\w*\b", text):
        return False
    # Reject spaced dashes in initials, stretched words, or numeric ranges
    if re.search(r"\b[А-ЯІЇЄҐ]\.\s*[—–-]\s*[А-ЯІЇЄҐ]\.", text):
        return False
    if re.search(r"\b[а-яіїєґА-ЯІЇЄҐ]-[а-яіїєґА-ЯІЇЄҐ]\s+[—–-]\s+[а-яіїєґА-ЯІЇЄҐ]\b", text):
        return False
    if re.search(r"\d+\s+—\s+\d+", text):
        return False
    # Reject spaced ellipses or ellipses with stray punctuation
    if re.search(r"\s+\.\.\.", text):
        return False
    if re.search(r"\.\.\.[,;:]", text) or re.search(r"[,;:]+\s*[»”\"]", text):
        return False
    # Reject spaced dashes in compounds/particles
    if re.search(r"\b[а-яіїєґА-ЯІЇЄҐ]+\s+[—–-]\s+(?:от|таки|будь|небудь|бо|но|то)\b", text, re.IGNORECASE):
        return False
    if re.search(r"\b(?:будь|хто|що|як|де|куди|коли)\s+[—–-]\s+[а-яіїєґА-ЯІЇЄҐ]+\b", text, re.IGNORECASE):
        return False
    # Reject mixed dashes (both en-dash and em-dash in same text)
    if "–" in text and "—" in text:
        return False
    # Reject double dots (not ellipsis)
    if re.search(r"(?<!\.)\.\.(?!\.)", text):
        return False
    # Reject quote without comma before dash
    if re.search(r'(?<![,.!?…])["»”]\s*—', text):
        return False
    # Reject stray comma after initial words like Пізніше
    if re.search(r'^[«"“]?Пізніше,', text):
        return False
    # Reject missing comma before conjunction 'що'
    if re.search(r'\b(?:знали|знав|знала|знаю|думаю|бачу|чую|розумію|видно|помітно|вважає)\s+що\b', text, re.IGNORECASE):
        return False
    if re.search(r'\b[а-яіїєґА-ЯІЇЄҐ]+\s+що,\b', text):
        return False
    # Reject calque 'невірно' in controls
    if re.search(r'\bневірно\b', text, re.IGNORECASE):
        return False
    if re.search(r'\bу\s+наслідок\b', text, re.IGNORECASE):
        return False
    if re.search(r'\b[Уу]\s+загальному\b', text):
        return False
    # Reject straight quotes (standard Ukrainian requires «...»)
    if '"' in text:
        return False
    # Reject decimal dot (must use comma in standard Ukrainian)
    if re.search(r"\b\d+\.\d+\b", text):
        return False
    # Reject hyphen or en-dash with spaces (must use em-dash for predicate/clause dash)
    if re.search(r"\s+[-–]\s+", text):
        return False
    # Reject Russianisms, false calques, and defects from Claude R9 Section G
    if re.search(r"\bтаїнствен\w*\b", text, re.IGNORECASE):
        return False
    if re.search(r"\bсопричаст\w*\b", text, re.IGNORECASE):
        return False
    if re.search(r"\bплитк\w*\b", text, re.IGNORECASE):
        return False
    if re.search(r"\bзакриті\s+акціонерні\s+товариства\b", text, re.IGNORECASE):
        return False
    if re.search(r"\bкомпанії\s+такі,\s+які\b", text, re.IGNORECASE):
        return False
    if re.search(r"\bзадач\w*\b", text, re.IGNORECASE):
        return False
    if re.search(r"\b[Тт]ак\s+само,\s+для\b", text):
        return False
    if re.search(r"\bнаправили\b", text, re.IGNORECASE):
        return False
    if re.search(r"\bПонад\s+\d+%\s+з\s+(?:котрих|яких)\b", text):
        return False
    # Claude R10 control defects
    if re.search(r"\bзапражк\w*\b", text, re.IGNORECASE):
        return False
    if re.search(r"\b[Пп]ід\s+цей\s+час\b", text):
        return False
    if re.search(r"\bінформації,\s+які\b", text, re.IGNORECASE):
        return False
    if re.search(r"\bне\s+зручно\b", text, re.IGNORECASE):
        return False
    # Reject spaced dashes in compounds
    if re.search(r"\b(?:контент|обер|онлайн|офлайн|інтернет|веб|аудіо|відео|кібер|смарт|еко|агро|етно|мега|гіпер|супер|ультра|екстра|темно|світло|ясно|блідо|синьо|жовто|червоно|зелено|чорно|біло|туди|плюс|врешті|караван|стейт|комікс|рок|поп|джаз|офіс|бізнес|прем'єр|віце|екс|міні|максі|міді|топ|шоу)\s+[—–-]\s+[а-яіїєґА-ЯІЇЄҐ\w'-]+", text, re.IGNORECASE):
        return False
    if re.search(r"\b[А-ЯІЇЄҐа-яіїєґ]+\s+[—–-]\s+\d+\b", text):
        return False
    if re.search(r"\b(?:туди\s+[—–-]\s+сюди|плюс\s+[—–-]\s+мінус|врешті\s+[—–-]\s+решт|караван\s+[—–-]\s+сара[їя]|стейт\s+[—–-]\s+машин\w*|комікс\s+[—–-]\s+вестерн\w*)\b", text, re.IGNORECASE):
        return False
    # Safety: reject graphic / violent / forensic / morbid / vulgar content
    if re.search(r"\b(?:розтин\w*|самогуб\w*|труп\w*|померш\w*|померл\w*|вбивств\w*|згвалт\w*|поц\w*|статев\w+\s+член\w*)\b", text, re.IGNORECASE):
        return False
    # Claude R11 control defects
    if re.search(r"\bПриступаючи\b", text):
        return False
    if re.search(r"\b[а-яіїєґА-ЯІЇЄҐ]+-[тТ]а\b", text):
        return False
    if re.search(r"\bпоказу\w*\s+собою\b", text, re.IGNORECASE):
        return False
    if re.search(r"^[Іі]\s+є,\s+на\s+його\s+думку", text):
        return False
    if re.search(r"\b(?:скоріше|швидше)\s+за\s+все\b", text, re.IGNORECASE):
        return False
    # Reject 'їх' before nouns as possessive
    if re.search(r"\bїх\s+[а-яіїєґ]+(?:ів|ей|ам|ям|ами|ями|ах|ях|ом|ем|ою|ею|и|і|ї|а|я|у|ю|е|є)\b", text, re.IGNORECASE):
        return False
    words = re.findall(r"[а-яіїєґА-ЯІЇЄҐ\w]+", text)
    # Reject short fragments, isolated words, or titles
    if len(words) < 6 or len(text) < 30:
        return False
    # Reject leading dashes (dialogue fragments without speaker attribution)
    if text.strip().startswith(("—", "–", "-")):
        return False
    # Reject URLs
    if re.search(r"https?://", text):
        return False
    # Must end with terminal sentence punctuation: . ! ? ... » ” "
    if not re.search(r"[.!?…»”\"]$", text.strip()):
        return False
    # Disallow colons, semicolons, or dashes at the end (incomplete sentences / headings)
    if text.strip().endswith((";", ":", ",", "-", "–", "—")):
        return False
    # Unbalanced quotes or brackets
    if text.count("«") != text.count("»"):
        return False
    if text.count('"') % 2 != 0:
        return False
    if text.count("“") != text.count("”"):
        return False
    if text.count("(") != text.count(")"):
        return False
    # Dash artifacts
    if re.search(r"[—–-]\s*[—–-]", text):
        return False
    # Stray floating quotes
    if re.search(r'\s+["«»“”„]\s+', text):
        return False
    # Reject triple repeated letters
    if re.search(r"([а-яіїєґА-ЯІЇЄҐ])\1\1", text, re.IGNORECASE):
        return False
    # Reject comma before parenthesis
    if re.search(r",\s*\(", text):
        return False
    # Reject Russianisms / slang
    if has_russianism(text, vesum_cur=vesum_cur):
        return False
    # Reject doubled words and 2-word repeated sequences
    if re.search(r"\b([а-яіїєґА-ЯІЇЄҐ]{2,})\s+\1\b", text, re.IGNORECASE):
        return False
    if re.search(r"\b([а-яіїєґА-ЯІЇЄҐ']+\s+[а-яіїєґА-ЯІЇЄҐ']+)\s+\1\b", text, re.IGNORECASE):
        return False

    # Verify finite verb / copula presence and 100% VESUM attestation of all words
    if vesum_cur is not None:
        # Reject 'їх' followed by noun or adjective (Russian possessive usage)
        for m in re.finditer(r"\bїх\s+([а-яіїєґА-ЯІЇЄҐ'-]+)", text, re.IGNORECASE):
            next_w = m.group(1).lower().strip("-'")
            res = vesum_cur.execute(
                "SELECT pos FROM forms_all WHERE word_form IN (?, ?, ?)",
                (next_w, next_w.capitalize(), next_w.upper()),
            ).fetchall()
            if any(r[0] in ("noun", "adj") for r in res):
                return False

        ctrl_words = [re.sub(r"[^а-яіїєґА-ЯІЇЄҐ0-9'-]", "", w) for w in text.split()]
        ctrl_words = [w.strip("-'") for w in ctrl_words if w and w not in {"-", "'"}]
        predicative_words = {
            "є", "був", "була", "було", "були", "буде", "будуть", "нема", "немає",
            "це", "можна", "треба", "потрібно", "варто", "слід", "необхідно"
        }
        has_verb_or_copula = any(w in predicative_words for w in ctrl_words) or ("—" in text)
        for w in ctrl_words:
            if w.isdigit():
                continue
            clean = w.lower()
            row = vesum_cur.execute(
                "SELECT pos FROM forms_all WHERE word_form IN (?, ?, ?) LIMIT 1",
                (clean, clean.capitalize(), clean.upper()),
            ).fetchone()
            if not row and "-" in clean:
                parts = [p for p in clean.split("-") if p and not p.isdigit()]
                if parts and all(
                    vesum_cur.execute(
                        "SELECT 1 FROM forms_all WHERE word_form IN (?, ?, ?) LIMIT 1",
                        (p, p.capitalize(), p.upper()),
                    ).fetchone()
                    for p in parts
                ):
                    row = ("part",)
            if not row:
                return False
            if not has_verb_or_copula and row[0] == "verb":
                has_verb_or_copula = True
        if not has_verb_or_copula:
            return False

        # Main clause verb check: verify sentence isn't just a verbless fragment with a subordinate clause
        main_part = re.split(r",\s*(?:що|як[иіае]|де|коли|куди|звідки)\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
        main_words = [re.sub(r"[^а-яіїєґА-ЯІЇЄҐ0-9'-]", "", w).strip("-'").lower() for w in main_part.split()]
        main_words = [w for w in main_words if w and not w.isdigit()]
        main_has_verb = any(w in predicative_words for w in main_words) or ("—" in main_part and len(main_words) >= 3)
        if not main_has_verb:
            for mw in main_words:
                if vesum_cur.execute("SELECT 1 FROM forms_all WHERE word_form = ? AND pos = 'verb' LIMIT 1", (mw,)).fetchone():
                    main_has_verb = True
                    break
        if not main_has_verb:
            return False

    return True


def is_valid_candidate(
    orig_text: str,
    corr_text: str,
    in_scope: list[tuple[int, int, str, str]],
    vesum_cur: sqlite3.Cursor | None = None,
    orig_tokens: list[str] | None = None,
) -> bool:
    """Validate candidate correction against annotator typos, comma-parens, and wholesale rewrites."""
    # Safety: reject graphic / violent / forensic / morbid / vulgar content
    if re.search(r"\b(?:розтин\w*|самогуб\w*|труп\w*|померш\w*|померл\w*|вбивств\w*|згвалт\w*|поц\w*|статев\w+\s+член\w*)\b", orig_text, re.IGNORECASE) or \
       re.search(r"\b(?:розтин\w*|самогуб\w*|труп\w*|померш\w*|померл\w*|вбивств\w*|згвалт\w*|поц\w*|статев\w+\s+член\w*)\b", corr_text, re.IGNORECASE):
        return False
    # Reject pure word insertions where start == end
    if any(e[0] == e[1] and re.search(r"[а-яіїєґА-ЯІЇЄҐ\w]", e[3]) for e in in_scope):
        return False
    # Real word counts
    w1_words = re.findall(r"[а-яіїєґА-ЯІЇЄҐ\w]+", orig_text)
    w2_words = re.findall(r"[а-яіїєґА-ЯІЇЄҐ\w]+", corr_text)
    if len(w1_words) < 5 or len(w2_words) < 5:
        return False
    # Sentence start must be uppercase or opening quote + uppercase
    c_strip = corr_text.strip()
    if not (c_strip[0].isupper() or (c_strip[0] in '«"“' and len(c_strip) > 1 and c_strip[1].isupper())):
        return False
    # Terminal punctuation: must end with . ! ? ... » ” "
    if not re.search(r"(?:[.!?…][»”\"]?|[»”\"][.!?…])$", c_strip):
        return False
    if corr_text.strip().endswith((";", ":", ",", "-", "–", "—")):
        return False
    # Reject unpunctuated run-on sentence / dropped period
    if re.search(r"\b[а-яіїєґ]+\s+(?:Най[а-яіїєґ]+|Він|Вона|Вони|Ми|Ви|Це|Той|Такий|Але|Проте|Однак|Тому|Коли|Якщо|Був|Була|Були|Мав|Мала|Пішов|Сказав|Відповів|Зробив)\b", corr_text):
        return False
    # Reject comma after question or exclamation mark
    if re.search(r"[\?!][»”\"]?,\s*—", corr_text) or re.search(r"[\?!],", corr_text):
        return False
    # Reject colon-dash combo
    if re.search(r":\s*—", corr_text):
        return False
    # Reject comma between subject and reporting verb
    if re.search(r"\b[А-ЯІЇЄҐ][а-яіїєґ]+,\s+(?:підморгнув|сказав|відповів|спитав|вигукнув|побіг|пішов|взяв|зробив)\b", corr_text):
        return False
    # Reject capitalization after comma-dash
    if re.search(r",\s*—\s*(?:Женучись|[А-ЯІЇЄҐ][а-яіїєґ]+(?:чи|ши|вши|вшись|ться|ти|ть|в|ла|ло|ли))\b", corr_text):
        return False
    # Reject malformed quote spacing
    if re.search(r'"\s+[а-яіїєґА-ЯІЇЄҐ]', corr_text) or re.search(r'[а-яіїєґА-ЯІЇЄҐ]\s+"[а-яіїєґА-ЯІЇЄҐ]', corr_text) or re.search(r'\w+"[А-ЯІЇЄҐа-яіїєґ]', corr_text):
        return False
    # Reject missing punctuation before quote in direct speech
    if re.search(r'\b[а-яіїєґА-ЯІЇЄҐ]+\s+["«][А-ЯІЇЄҐ]', corr_text):
        return False
    # Strictly reject ASCII straight quotes in both orig and corr (Ukrainian standard requires «...»)
    if '"' in corr_text or '"' in orig_text:
        return False
    # Strictly reject decimal dot (must use comma in standard Ukrainian)
    if re.search(r"\b\d+\.\d+\b", corr_text) or re.search(r"\b\d+\.\d+\b", orig_text):
        return False
    # Reject sentence-splitting edits
    if re.search(r"(?<!\b[А-ЯІЇЄҐ]\.)(?<!\b[а-яіїєґ]\.)(?<!\bім\.)(?<!\bвул\.)(?<!\bр\.)(?<!\bст\.)\.\s+[А-ЯІЇЄҐ]", corr_text) and not re.search(r"(?<!\b[А-ЯІЇЄҐ]\.)(?<!\b[а-яіїєґ]\.)(?<!\bім\.)(?<!\bвул\.)(?<!\bр\.)(?<!\bст\.)\.\s+[А-ЯІЇЄҐ]", orig_text):
        return False
    # Reject colloquial Russian -то
    if re.search(r"\b[а-яіїєґА-ЯІЇЄҐ]+-то\b", corr_text) or re.search(r"\b[а-яіїєґА-ЯІЇЄҐ]+-то\b", orig_text):
        return False
    # No URLs
    if re.search(r"https?://", orig_text) or re.search(r"https?://", corr_text):
        return False
    # Strictly Cyrillic: zero Latin, CJK, zero-width, or control characters
    if re.search(r"[a-zA-Z]", corr_text) or re.search(r"[a-zA-Z]", orig_text):
        return False
    if re.search(r"[\u2e80-\u9fff\u3000-\u303f\uff00-\uffef]", corr_text) or re.search(
        r"[\u2e80-\u9fff\u3000-\u303f\uff00-\uffef]", orig_text
    ):
        return False
    if re.search(r"[\u200b-\u200f\u202a-\u202e\ufeff]", corr_text) or re.search(
        r"[\u200b-\u200f\u202a-\u202e\ufeff]", orig_text
    ):
        return False
    # Reject spaced ellipses or ellipses with stray punctuation
    if re.search(r"\s+\.\.\.", corr_text) or re.search(r"\s+\.\.\.", orig_text):
        return False
    if re.search(r"\.\.\.[,;:]", corr_text) or re.search(r"[,;:]+\s*[»”\"]", corr_text):
        return False
    # Reject spaced dashes in initials, stretched words, or numeric ranges
    if re.search(r"\b[А-ЯІЇЄҐ]\.\s*[—–-]\s*[А-ЯІЇЄҐ]\.", corr_text) or re.search(
        r"\b[А-ЯІЇЄҐ]\.\s*[—–-]\s*[А-ЯІЇЄҐ]\.", orig_text
    ):
        return False
    if re.search(r"\b[а-яіїєґА-ЯІЇЄҐ]-[а-яіїєґА-ЯІЇЄҐ]\s+[—–-]\s+[а-яіїєґА-ЯІЇЄҐ]\b", corr_text):
        return False
    if re.search(r"\d+\s+—\s+\d+", corr_text) or re.search(r"\d+\s+—\s+\d+", orig_text):
        return False
    # Reject math symbols or special characters
    if any(c in corr_text for c in "<>~=@#$^&*_+") or any(c in orig_text for c in "<>~=@#$^&*_+"):
        return False
    # Reject non-standard or curly apostrophes
    if re.search(r"[’ʼ‘`´ʹ‛]", corr_text) or re.search(r"[’ʼ‘`´ʹ‛]", orig_text):
        return False
    # Reject emojis
    if any(unicodedata.category(c) == "So" for c in corr_text) or any(
        unicodedata.category(c) == "So" for c in orig_text
    ):
        return False
    # Reject braces / brackets / editorial artifacts: e.g. "–}" or "{" or "}"
    if any(c in corr_text for c in "{}[]") or any(c in orig_text for c in "{}[]"):
        return False
    # Reject mixed dashes (en and em dashes in same text)
    if ("–" in corr_text and "—" in corr_text) or ("–" in orig_text and "—" in orig_text):
        return False
    # Reject hyphen-as-dash
    if re.search(r"\s+-\s+", corr_text) or re.search(r"\s+-\s+", orig_text):
        return False
    # Reject triple repeated letters
    if re.search(r"([а-яіїєґА-ЯІЇЄҐ])\1\1", orig_text, re.IGNORECASE) or re.search(
        r"([а-яіїєґА-ЯІЇЄҐ])\1\1", corr_text, re.IGNORECASE
    ):
        return False
    # Reject comma before parenthesis
    if re.search(r",\s*\(", orig_text) or re.search(r",\s*\(", corr_text):
        return False
    # Reject truncated sentences ending with a preposition
    if re.search(r"\b(?:на|в|у|до|з|під|над|через|про|за|при|біля|від|для|без)\s*[\.!?]$", orig_text):
        return False
    # Reject adding dialogue dash when orig did not start with dash
    if not orig_text.strip().startswith(("—", "–", "-")) and corr_text.strip().startswith(("—", "–", "-")):
        return False
    # Unbalanced quotes or brackets
    if corr_text.count("«") != corr_text.count("»") or orig_text.count("«") != orig_text.count("»"):
        return False
    if corr_text.count('"') % 2 != 0 or orig_text.count('"') % 2 != 0:
        return False
    if corr_text.count("“") != corr_text.count("”"):
        return False
    if corr_text.count("(") != corr_text.count(")"):
        return False
    # Dash artifacts
    if re.search(r"[—–-]\s*[—–-]", orig_text) or re.search(r"[—–-]\s*[—–-]", corr_text):
        return False
    # Stray floating quotes
    if re.search(r'\s+["«»“”„]\s+', corr_text):
        return False

    # Negation consistency: do not flip polarity
    if len(re.findall(r"\bне\b", orig_text.lower())) != len(re.findall(r"\bне\b", corr_text.lower())):
        return False

    # Check for pronoun / gender substitution without context
    o_low = orig_text.lower()
    c_low = corr_text.lower()
    if (re.search(r"\bвін\b", o_low) and re.search(r"\bвона\b", c_low)) or (
        re.search(r"\bвона\b", o_low) and re.search(r"\bвін\b", c_low)
    ):
        return False
    if (re.search(r"\bйого\b", o_low) and re.search(r"\bїї\b", c_low)) or (
        re.search(r"\bїї\b", o_low) and re.search(r"\bйого\b", c_low)
    ):
        return False
    if (re.search(r"\bйому\b", o_low) and re.search(r"\bїй\b", c_low)) or (
        re.search(r"\bїй\b", o_low) and re.search(r"\bйому\b", c_low)
    ):
        return False
    if (re.search(r"\bним\b", o_low) and re.search(r"\bнею\b", c_low)) or (
        re.search(r"\bнею\b", o_low) and re.search(r"\bним\b", c_low)
    ):
        return False
    if (re.search(r"\bньому\b", o_low) and re.search(r"\bній\b", c_low)) or (
        re.search(r"\bній\b", o_low) and re.search(r"\bньому\b", c_low)
    ):
        return False
    if (re.search(r"\bвона\b", o_low) and not re.search(r"\bвона\b", c_low)) or (
        re.search(r"\bвін\b", o_low) and not re.search(r"\bвін\b", c_low)
    ):
        return False
    if (re.search(r"\bя\s+[а-яіїєґ]+(?:ла|лася|лась)\b", o_low) and re.search(r"\bя\s+[а-яіїєґ]+(?:в|вся|всь)\b", c_low)) or (
        re.search(r"\bя\s+[а-яіїєґ]+(?:в|вся|всь)\b", o_low) and re.search(r"\bя\s+[а-яіїєґ]+(?:ла|лася|лась)\b", c_low)
    ):
        return False
    if (re.search(r"\bя\s+була\b", o_low) and re.search(r"\bя\s+(?:був|знав)\b", c_low)) or (
        re.search(r"\bя\s+був\b", o_low) and re.search(r"\bя\s+(?:була|знала)\b", c_low)
    ):
        return False
    if re.search(r"\bможе\b", o_low) and re.search(r"\bможу\b", c_low):
        return False
    if (re.search(r"\bви\b", o_low) and re.search(r"\bти\b", c_low)) or (
        re.search(r"\bти\b", o_low) and re.search(r"\bви\b", c_low)
    ):
        return False
    if (re.search(r"\bвас\b", o_low) and re.search(r"\bтебе\b", c_low)) or (
        re.search(r"\bтебе\b", o_low) and re.search(r"\bвас\b", c_low)
    ):
        return False
    if (re.search(r"\bвам\b", o_low) and re.search(r"\bтобі\b", c_low)) or (
        re.search(r"\bтобі\b", o_low) and re.search(r"\bвам\b", c_low)
    ):
        return False
    if (re.search(r"\bвами\b", o_low) and re.search(r"\bтобою\b", c_low)) or (
        re.search(r"\bтобою\b", o_low) and re.search(r"\bвами\b", c_low)
    ):
        return False

    # Proper name protection
    if (re.search(r"\bіванушк\w*\b", o_low) and re.search(r"\bівасик\w*\b", c_low)) or (
        re.search(r"\bівасик\w*\b", o_low) and re.search(r"\bіванушк\w*\b", c_low)
    ):
        return False
    if re.search(r"\bнюто\w*\b", o_low) and re.search(r"\bвпадатиме\b", c_low):
        return False

    # «Через [час]» -> «За [час]»
    if re.search(r"\bчерез\s+(?:день|дні|днів|тиждень|тижні|тижнів|місяц\w*|рік|роки|років|хвилин\w*|годин\w*|час|якийсь\s+час)\b", o_low) and re.search(r"\bза\s+(?:день|дні|днів|тиждень|тижні|тижнів|місяц\w*|рік|роки|років|хвилин\w*|годин\w*|час|якийсь\s+час)\b", c_low):
        return False

    # Singular to plural referent shifts
    if re.search(r"\bпервосвящен\w*\b", o_low) and re.search(r"\bпервосвященник\w*\b", c_low):
        return False

    # Correlative "чим..., тим...": reject changing чим or тим
    if re.search(r"\bчим\b", o_low) and re.search(r"\bтим\b", o_low) and not (re.search(r"\bчим\b", c_low) and re.search(r"\bтим\b", c_low)):
        return False

    # Reject unwarranted lexical swaps
    if re.search(r"\bнасос\w*\b", o_low) and re.search(r"\bпомп\w*\b", c_low):
        return False
    if re.search(r"\bодин\s+від\s+одного\b", o_low) and re.search(r"\bодне\s+від\s+одного\b", c_low):
        return False
    if re.search(r"\bдоктор\w*\b", o_low) and re.search(r"\bлікар\w*\b", c_low):
        return False
    if ("зупинімося" in o_low and "зупинімось" in c_low) or ("зупинімось" in o_low and "зупинімося" in c_low):
        return False
    if re.search(r"\bпідписник\w*\b", o_low) and re.search(r"\bчитач\w*\b", c_low):
        return False
    if re.search(r"\bпару\s+речень\b", o_low) and re.search(r"\bтрохи\b", c_low):
        return False
    if re.search(r"\bні\s+гроша\b", o_low) and re.search(r"\bні\s+копійки\b", c_low):
        return False
    if re.search(r"\bсподоба\w*\b", o_low) and re.search(r"\bподоба\w*\b", c_low):
        return False
    if re.search(r"\bночі\b", o_low) and re.search(r"\bранку\b", c_low):
        return False
    if re.search(r"\bспівставн\w*\b", o_low) and re.search(r"\bзіставлен\w*\b", c_low):
        return False
    if re.search(r"\bзадал\w*\s+питанням\b", o_low) and re.search(r"\bзацікавил\w*\b", c_low):
        return False
    if re.search(r"\bповені\s+на\s+землю\b", c_low) or re.search(r"\bвогнегасник\b", o_low):
        return False
    if re.search(r"^Це\s+неважливо,\s+оскільки\b", orig_text) and not re.search(r"\bневажливо\b", corr_text):
        return False
    if re.search(r"\bпотіння\b", o_low) and re.search(r"\bпітливість\b", c_low):
        return False
    if re.search(r"\bтеплим\s+океаном\b", c_low):
        return False
    if re.search(r"\bгосподи\s+[—–-]\s+боже\b", c_low):
        return False
    if (re.search(r"\b(?:він|вона|воно)\b", o_low) or re.search(r"\bчого\s+так\s+поспішал[аов]\b", o_low)) and re.search(r"\bпоспішали\b", c_low):
        return False
    if re.search(r"\boy-auch\b|\bой-ауч\b", c_low):
        return False
    if re.search(r"\bущемленн\w*\b", c_low) or re.search(r"\bущемленн\w*\b", o_low):
        return False
    if re.search(r"\bутисків\s+прав\b", c_low):
        return False
    if re.search(r"\bспіріт\w*\b", o_low) or re.search(r"\bпримаро\b", c_low):
        return False
    if re.search(r"\bсплять\s+не\s+вчасно\b", o_low) and re.search(r"\bне\s+сплять\s+вчасно\b", c_low):
        return False
    if re.search(r"\bяк\s+би\s+він\s+не\s+запізнився\b", o_low):
        return False

    # Gender agreement mismatch
    if re.search(r"\bтака\s+(?:вже\s+й\s+|ще\s+й\s+)?[а-яіїєґ]+[еє]\b", c_low):
        return False
    if re.search(r"\bтаке\s+(?:вже\s+й\s+|ще\s+й\s+)?[а-яіїєґ]+[ая]\b", c_low):
        return False

    # Dangling subordinate clauses / missing main clause
    if re.search(r",\s*а\s+що\s+[^,\.!?]+[\.!?]$", corr_text):
        return False

    # Antecedent-less object pronoun introduced
    if not re.search(r"\b(?:ним|нею|ними)\b", o_low) and re.search(r"\bвін\s+(?:ним|нею|ними)\b", c_low):
        return False

    # Spaced dashes in compounds/particles
    if re.search(r"\b(?:темно|світло|ясно|блідо|синьо|жовто|червоно|зелено|чорно|біло|туди|плюс|врешті|караван|стейт|комікс|рок|поп|джаз|офіс|бізнес|прем'єр|віце|екс|міні|максі|міді|топ|шоу)\s+[—–-]\s+[а-яіїєґА-ЯІЇЄҐ\w'-]+", corr_text, re.IGNORECASE):
        return False
    if re.search(r"\b[А-ЯІЇЄҐа-яіїєґ]+\s+[—–-]\s+\d+\b", corr_text):
        return False
    if re.search(r"\b(?:туди\s+[—–-]\s+сюди|плюс\s+[—–-]\s+мінус|врешті\s+[—–-]\s+решт|караван\s+[—–-]\s+сара[їя]|стейт\s+[—–-]\s+машин\w*|комікс\s+[—–-]\s+вестерн\w*)\b", corr_text, re.IGNORECASE):
        return False
    if re.search(r"\b[а-яіїєґА-ЯІЇЄҐ]+\s+[—–-]\s+(?:от|таки|будь|небудь|бо|но|то)\b", corr_text, re.IGNORECASE):
        return False
    if re.search(r"\b(?:будь|хто|що|як|де|куди|коли)\s+[—–-]\s+[а-яіїєґА-ЯІЇЄҐ]+\b", corr_text, re.IGNORECASE):
        return False
    if re.search(r"\b(?:рок|поп|джаз|офіс|бізнес)\s+[—–-]\s+[а-яіїєґА-ЯІЇЄҐ]+\b", corr_text, re.IGNORECASE):
        return False

    # B4 False / subjective lexical and grammatical swaps
    if re.search(r"\bлюбител\w*\b", o_low) and re.search(r"\bприхильник\w*\b", c_low):
        return False
    if re.search(r"\bнастільки\b", o_low) and re.search(r"\bтаким\w*\b", c_low):
        return False
    if re.search(r"\bсправа\s+в\s+тому\b", o_low) and re.search(r"\bріч\s+у\s+тому\b", c_low):
        return False
    if re.search(r"\bцарил\w*\b", o_low) and re.search(r"\bпанувал\w*\b", c_low):
        return False
    if re.search(r"\bяк\s+тільки\b", o_low) and re.search(r"\bщойно\b", c_low):
        return False
    if re.search(r"\bгусь\b", o_low) and re.search(r"\bгусак\b", c_low):
        return False
    if re.search(r"\bзлодіянн\w*\b", o_low) and re.search(r"\bзлочин\w*\b", c_low):
        return False
    if re.search(r"\bжарко\b", o_low) and re.search(r"\bспекотно\b", c_low):
        return False
    if re.search(r"\bвесною\b", o_low) and re.search(r"\bнавесні\b", c_low):
        return False
    if re.search(r"\bдріж\b", o_low) and re.search(r"\bтремтінн\w*\b", c_low):
        return False
    if re.search(r"\bодин\s+одного\b", o_low) and re.search(r"\bодні\s+одних\b", c_low):
        return False
    if re.search(r"\bпо\s+всій\b", o_low) and re.search(r"\b[ву]\s+всій\b", c_low):
        return False
    if re.search(r"\bпочнемо\b", o_low) and re.search(r"\bпочнімо\b", c_low):
        return False
    if re.search(r"\bяк\s+[^,]+,\s+так\s+і\b", o_low) and re.search(r"\bі\s+[^,]+,\s+і\b", c_low):
        return False
    # Claude R8 Section F valid -> valid swaps
    if re.search(r"\bбуло\s+(?:дуже\s+)?легко\b", o_low) and re.search(r"\bбули\s+(?:дуже\s+)?легкими\b", c_low):
        return False
    if re.search(r"\bна\s+вітру\b", o_low) and re.search(r"\bна\s+вітрі\b", c_low):
        return False
    if re.search(r"\bтишиною\b", o_low) and re.search(r"\bтишею\b", c_low):
        return False
    if re.search(r"\bспостерігається\b", o_low) and re.search(r"\bспостерігають\b", c_low):
        return False
    if re.search(r"\bяк\s+би\s+він\s+не\s+запізнився\b", o_low):
        return False
    if re.search(r"\bзимою\b", o_low) and re.search(r"\bвзимку\b", c_low):
        return False
    if re.search(r"\bдавайте\s+[а-яіїєґ]+мо\b", o_low) and re.search(r"\b[а-яіїєґ]+мо\b", c_low):
        return False
    if re.search(r"\bне\s+стільки\b", o_low) and re.search(r"\bне\s+так\b", c_low):
        return False
    if re.search(r"\bбезкрайнім\b", o_low) and re.search(r"\bбезкраїм\b", c_low):
        return False
    if re.search(r"\bбарабанщик\w*\b", o_low) and re.search(r"\bбарабанник\w*\b", c_low):
        return False
    if re.search(r"\bблагообразн\w*\b", o_low) and re.search(r"\bмиловид\w*\b", c_low):
        return False
    if re.search(r"\bхустка\b", o_low) and re.search(r"\bхустинка\b", c_low):
        return False
    if re.search(r"\bСуді\b", orig_text) and re.search(r"\bСьюді\b", corr_text):
        return False
    # Contextless gender and number flips
    if (re.search(r"\bвиросла\b", o_low) and re.search(r"\bвиріс\b", c_low)) or (
        re.search(r"\bвиріс\b", o_low) and re.search(r"\bвиросла\b", c_low)
    ):
        return False
    if (re.search(r"\bлюбий\b", o_low) and re.search(r"\bлюба\b", c_low)) or (
        re.search(r"\bлюба\b", o_low) and re.search(r"\bлюбий\b", c_low)
    ):
        return False

    # Punctuation and formatting gates from Claude R8
    if re.search(r"(?<!\.)\.\.(?!\.)", corr_text):
        return False
    if re.search(r'"\.', corr_text):
        return False
    if re.search(r'(?<![,.!?…])["»”]\s*—', corr_text):
        return False
    if re.search(r'^[«"“]?Пізніше,', corr_text):
        return False
    if re.search(r'\b(?:знали|знав|знала|знаю|думаю|бачу|чую|розумію|видно|помітно|вважає)\s+що\b', corr_text, re.IGNORECASE):
        return False
    if re.search(r'\b[а-яіїєґА-ЯІЇЄҐ]+\s+що,\b', corr_text):
        return False
    if re.search(r'\bзгідно\s+(?!з\b|із\b|зі\b)[а-яіїєґ]+(?:ом|ем|ям|ою|ею|ами|ями|ах|ях|у|і|а)\b', c_low):
        return False
    if re.search(r'\bу\s+наслідок\b', c_low):
        return False
    if re.search(r'\b[Уу]\s+загальному\b', corr_text):
        return False

    # B6 Broken/incoherent repairs
    if re.search(r"\bвдарив\w*\s+до\b", c_low):
        return False
    if re.search(r"\bзгідно\s+тим\b", c_low):
        return False
    if re.search(r"\bвважа\w*\s+за\b", o_low) and re.search(r"\bгідним\s+життям\b", c_low):
        return False
    if re.search(r"\bголуб'ятн\w*\b", o_low) and re.search(r"\bголуб'ятник\b", c_low):
        return False
    if re.search(r"\bтриповерхового\s+цегляного\b", c_low):
        return False
    if re.search(r"\bне\s+абищо\b", c_low):
        return False
    if re.search(r"\bоминул\w*\s+тобі\s+голову\b", c_low):
        return False
    if re.search(r"\bза\s+годинами\b", c_low):
        return False
    if re.search(r"\bа\s+цього,\s+а\s+років\b", c_low):
        return False
    if re.search(r"\bзагадкових,\s+дивних\s+смертей\b", o_low):
        return False
    if re.search(r"\bіз\s+вибухом\s+іронічного\b", o_low):
        return False
    if re.search(r"\bпершопроходц\w*\b", o_low) and re.search(r"\bзачинател\w*\b", c_low):
        return False
    if re.search(r"\bрічка\s+бігла\s+швидко\b", o_low) and re.search(r"\bвода\s+у\s+річці\b", c_low):
        return False
    if re.search(r"\bБідл\s+сказав\b", c_low) or "Бідл" in orig_text:
        return False
    if re.search(r"\bінкрустован\w*\s+дрібними\s+діамантами\b", c_low) or re.search(r"\bгодинник\w*,\s*інкрустован\w*\b", c_low):
        return False
    if re.search(r"\bВ\s+одні\s+з\s+них\b", corr_text) or re.search(r"\bтемним\s+Шкапа\b", corr_text):
        return False
    if re.search(r"\bз\s+протягнутою\b", c_low) or re.search(r"\bгодинник\s+Римського\b", c_low):
        return False
    if re.search(r"\bіз\s+винятком,\s+для\b", c_low) or re.search(r"\bце\s+візуалізація\s+має\s+бути\b", c_low):
        return False
    if re.search(r"\b[Уу]їздн\w*\b", o_low) or re.search(r"\b[Зз]аїждж\w*\s+лікар\b", c_low) or re.search(r"\bвесняний\s+обід\s+на\s+все\s+пиття\b", c_low):
        return False
    if re.search(r"\bзастукал\w*\b", c_low):
        return False
    if re.search(r"\bнайлегковажніш\w*\b", c_low) or re.search(r"\bлегковажніш\w*\b", c_low):
        return False
    if re.search(r"\bударин\w*\b", o_low) or re.search(r"\bкінський\s+біг\b", c_low):
        return False
    if re.search(r"\bстрав\w*\s+вареної\s+собаки\b", c_low) or re.search(r"\bзбираючи\s+вантажівку\b", c_low):
        return False
    if re.search(r"\bдо\s+одного\s+колеса\b", c_low) or re.search(r"\bсамому\s+задньому\s+колесі\b", c_low):
        return False
    if re.search(r"\bриси\s+догляду\s+і\s+скупості\b", c_low):
        return False
    if re.search(r"\bмужики,\s+прозаїки\b", c_low):
        return False
    if re.search(r"\bкаже\s+бай-бай\b", c_low):
        return False
    if re.search(r"\bКоролівсьво\w*\b", c_low):
        return False
    if re.search(r"\bПигарев\b", corr_text):
        return False
    if re.search(r"\bособистий\s+секретар\s+[^,.]+\s+лежала\b", c_low):
        return False
    if re.search(r"\bчелендж\b", c_low):
        return False
    if re.search(r"\bнавіть,\s+можна\s+сказати\b", c_low):
        return False
    if re.search(r"\bу\s+сторону\b", c_low):
        return False

    # Claude R9: Garbled or defective gold text
    if re.search(r"\bдо\s+губ\s+думає\b", c_low) or re.search(r"\bрозважити,\s+пасажирів\b", c_low):
        return False
    if re.search(r"\bпасажирів\s+які\b", c_low):
        return False
    if re.search(r"\bпорушення\s+технології\s+[—–-]\s+у\s+них\b", c_low):
        return False
    if re.search(r"\bсклала\s+своє\s+майно\s+та\s+через\b", c_low):
        return False
    if re.search(r"\bбув\s+на\s+москалів\b", c_low):
        return False
    if re.search(r"\bпри\s+чому\b", c_low) or re.search(r"\bне\s+традиційн\w*\b", c_low):
        return False
    if re.search(r"\bінтелігентн\w*\s+дому\b", c_low):
        return False
    if re.search(r"\bконтент\s+[—–-]\s+мейкер\w*\b", c_low):
        return False

    # Claude R9: Meaning changed or content invented
    if re.search(r"\bісторики\s+фіксували\s+на\s+території\b", c_low) or re.search(r"\bявище\s+колабораціонізму\b", o_low):
        return False
    if re.search(r"\bАзіз\s+Санзар\b", o_low) or re.search(r"\bСанджар\b", o_low):
        return False
    if "максимум" in o_low and re.search(r"\bщонайменше\s+наполовину\b", c_low):
        return False
    if re.search(r"\bгуся\b", o_low) or re.search(r"\bгусак\w*\b", c_low):
        return False
    if re.search(r"\bя\s+намалюю\s+тінь\b", c_low):
        return False
    if re.search(r"\b[Яя]кщо\s+ввімкнути\s+режим\b", corr_text):
        return False
    if re.search(r"\bстиснут\w*\s+Паш\w*\b", c_low) or re.search(r"\bна\s+чиємусь\s+тулуп\w*\b", c_low):
        return False
    if "дубинк" in o_low and re.search(r"\bпалиц\w*\b", c_low):
        return False
    if "пару кроків" in o_low and re.search(r"\bкілька\s+кроків\b", c_low):
        return False

    # Claude R9: Valid-to-valid swaps
    if re.search(r"\bдавай(?:те)?\b", o_low, re.IGNORECASE):
        return False
    if re.search(r"\bполиха\w*\b", o_low):
        return False
    if re.search(r"\bсує\b", o_low):
        return False
    if re.search(r"\bвиросла\s+майже\s+у\s+12\s+разів\b", c_low):
        return False
    if re.search(r"\bв\s+саді\b", o_low):
        return False
    if re.search(r"\b[Іі]з\s+самого\s+початку\b", o_low):
        return False
    if re.search(r"\b[Яя]к\s+же\s+автору\b", o_low):
        return False
    if re.search(r"\bбільше\s+мільйон\w*\b", o_low):
        return False
    if re.search(r"\bвідвіданий\s+нами\s+музей\b", o_low):
        return False
    if re.search(r"\bнадів\s+капелюх\w*\b", c_low):
        return False
    if re.search(r"\bгодини\s+з\s+чотири\b", c_low) or re.search(r"\b[Мм]орочився\s+він\b", c_low):
        return False
    if re.search(r"\bБудуть\s+цікаві\s+ваші\s+варіанти\b", c_low):
        return False
    if re.search(r"\bще\s+трохи\s+часу\s+і\s+на\s+піку\b", c_low):
        return False

    # Claude R9: Residual calques / Russianisms in gold
    if re.search(r"\bзадан\w*\s+людськ\w*\b", c_low) or re.search(r"\bзадан\w*\s+травм\w*\b", c_low):
        return False
    if re.search(r"\b[Пп]о\s+можливості\b", c_low):
        return False
    if re.search(r"\bкрутильн\w*\s+момент\w*\b", c_low):
        return False
    if re.search(r"\bобер-?кондуктор\b", c_low):
        return False
    if re.search(r"\bзакалк\w*\b", c_low) or re.search(r"\bФилип\w*\b", c_low) or re.search(r"\bглупство\b", c_low):
        return False

    # Minor items
    if re.search(r"\bрозпад\w*\s+атому\b", c_low) or re.search(r"\bрозпад\w*\s+атому\b", o_low):
        return False
    if re.search(r"[а-яіїєґ]\s+навіщо\b", corr_text):
        return False
    if re.search(r"\bіз\s+с[пткфхчшщ]\w*\b", c_low):
        return False
    if re.search(r"\bу\s+гаї\b", o_low) and re.search(r"\bу\s+гаю\b", c_low):
        return False
    if re.search(r"\bлюдського\s+мурашник\w*\b", o_low):
        return False
    if re.search(r"\bторкаючись\s+футляр\w*\b", o_low):
        return False
    if re.search(r"\bПротестантськ\w*\b", o_low):
        return False

    # Claude R10: Morphology, agreement, and case government defects
    if re.search(r"\bпри\s+сталих\s+[а-яіїєґ]+\s+та\s+[а-яіїєґ]+и\b", c_low) or re.search(r"\bпри\s+сталих\s+тиску\b", c_low):
        return False
    if re.search(r"\bпро\s+.*Понті\w+\s+Пілат\w*\b", c_low):
        return False
    if re.search(r"\bщо\s+їхн[яійєі]\s+(?:незліченна\s+)?кількість\b", c_low):
        return False
    if re.search(r"\bцентральн\w*\s+апсид\w*\b", c_low):
        return False
    if re.search(r"\bкаламутні\s+п['\’]?яні\b", c_low):
        return False
    if re.search(r"\bне\s+зручно\b", c_low):
        return False
    if re.search(r"\bрахується\s+як\b", c_low) or re.search(r"\b[Пп]ри\s+дійсному\s+твердженні\b", corr_text):
        return False
    if re.search(r"\bце\s+конкретне\s+про\s+майбутнє\b", c_low) or re.search(r"\bстимулює\s+використовувати\b", c_low):
        return False
    if re.search(r"\b[Пп]ерший,\s+що\s+ви\s+комплексуєте\b", corr_text):
        return False
    if re.search(r"\bє\s+що\s+ухвалювати\b", c_low):
        return False
    if re.search(r"\bматимуть\s+слушність\b", c_low):
        return False
    if re.search(r"^[Пп]онад\s+80%\s+з\s+яких\b", corr_text):
        return False
    if re.search(r"\bне\s+працює,\s+повністю\s+зосередилась\b", c_low):
        return False
    if re.search(r";\s*зневірившись\b", c_low) or (re.search(r"\bвідчаївшись\b", o_low) and re.search(r"\bзневірившись\b", c_low)):
        return False
    if re.search(r"\bпрошення\b", o_low) and re.search(r"\bпрохання\b", c_low):
        return False
    if re.search(r"\bкоротким\s+обличчям\b", o_low) and re.search(r"\bвузьким\s+обличчям\b", c_low):
        return False
    if re.search(r"\bне\s+надмірна\b", o_low) and re.search(r"\bне\s+довга\b", c_low):
        return False
    if (re.search(r"\bприкажчик\b", o_low) and re.search(r"\bпродавець\b", c_low)) or (re.search(r"\bпіднімав\b", o_low) and re.search(r"\bзводив\b", c_low)):
        return False
    if re.search(r"\bнавчити\b", o_low) and re.search(r"\bнавчитися\b", c_low):
        return False
    if re.search(r"\bкружк\w*\b", o_low) and re.search(r"\bчашк\w*\b", c_low):
        return False
    if re.search(r"\bхліба\w*\b", o_low) and re.search(r"\bхлебч\w*\b", c_low):
        return False
    if re.search(r"\bзасвічений\b", o_low) and re.search(r"\bзасвічу\b", c_low):
        return False
    if re.search(r"\bвказав\w*\s+.*\bдо\s+гори\b", c_low):
        return False

    # Claude R10: Category F Valid-to-valid swaps & Self-contradictions
    if re.search(r"\bбуд(?:у|еш|е|емо|ете|уть)\s+[а-яіїєґ]+ти\b", o_low) and not re.search(r"\bбуд(?:у|еш|е|емо|ете|уть)\b", c_low) and re.search(r"\b[а-яіїєґ]+(?:тиму|тимеш|тиме|тимемо|тимете|тимуть)\b", c_low):
        return False
    if re.search(r"\b(?:читається\s+та\s+обговорюється|цінується|сприймалися\s+представниками|створювалась\s+різниця|вимірювався\s+струм|закладалися\s+їх|контролюється\s+комп['\’]?ютером)\b", o_low):
        return False
    if re.search(r"\bзвернемося\b", o_low) and re.search(r"\bзвернімося\b", c_low):
        return False
    if (re.search(r"\bдозволя\w*\b", o_low) and re.search(r"\bда\w+\s+змог\w*\b", c_low)) or (re.search(r"\bда\w+\s+змог\w*\b", o_low) and re.search(r"\bдозволя\w*\b", c_low)):
        return False
    if (re.search(r"\bдекільк\w*\b", o_low) and re.search(r"\bкільк\w*\b", c_low)) or (re.search(r"\bкільк\w*\b", o_low) and re.search(r"\bдекільк\w*\b", c_low)):
        return False
    if (re.search(r"\bза\s+допомогою\b", o_low) and re.search(r"\bз\s+допомогою\b", c_low)) or (re.search(r"\bз\s+допомогою\b", o_low) and re.search(r"\bза\s+допомогою\b", c_low)):
        return False
    if re.search(r"\bзадач\w*\b", o_low) and re.search(r"\bзавданн\w*\b", c_low):
        return False
    if re.search(r"\bвиключили\b", o_low) and re.search(r"\bвідрахували\b", c_low):
        return False
    if re.search(r"\bдовкруги\b", o_low) and re.search(r"\bдовкола\b", c_low):
        return False
    if re.search(r"\bпари\b", o_low) and re.search(r"\bвипари\b", c_low):
        return False
    if re.search(r"\bЗа\s+погані\s+вчинки\b", orig_text) and re.search(r"\bЧерез\s+погані\s+вчинки\b", corr_text):
        return False
    if re.search(r"\bпару\s+днів\b", o_low) and re.search(r"\bкілька\s+днів\b", c_low):
        return False
    if re.search(r"\bакцентує\b", o_low) and re.search(r"\bакцентував\b", c_low):
        return False
    if re.search(r"\bпоручик\w*\b", o_low) and re.search(r"\bпоручник\w*\b", c_low):
        return False
    if re.search(r"\bпочитати\b", o_low) and re.search(r"\bпрочитати\b", c_low):
        return False
    if re.search(r"\bМетою\s+статті\s+є\b", orig_text) and re.search(r"\bМета\s+статті\b", corr_text):
        return False
    if re.search(r"\bполян\w*\b", o_low) and re.search(r"\bгалявин\w*\b", c_low):
        return False
    if re.search(r"\bкойк\w*\b", o_low) and re.search(r"\bліжк\w*\b", c_low):
        return False
    if re.search(r"\bдубин\w*\b", o_low) and re.search(r"\bдубц\w*\b", c_low):
        return False

    # Claude R10 Minor items
    if re.search(r"\bзастиглими\s+розплющеними\b", c_low):
        return False
    if re.search(r"\bкорзин\w*\b", c_low):
        return False
    if re.search(r"\bбезтолков\w*\b", c_low):
        return False
    if re.search(r"\bогненн\w*\b", c_low):
        return False
    if re.search(r"\bодеж\w*\b", c_low) or re.search(r"\bбез\s+всякої\b", c_low):
        return False
    if re.search(r"\bсамокатник\w*\b", c_low):
        return False
    if re.search(r"\bяк\s+побажаєте\b", c_low):
        return False

    # Claude R11 Section A Grammar Defects
    if re.search(r"\bпаралельн\w*\s+Малої\s+Бронної\b", c_low):
        return False
    if re.search(r"\bїхні\s+велич\b", c_low):
        return False
    if re.search(r"\bвсі\s+це\s+драконівські\b", c_low):
        return False
    if re.search(r"\bпро\s+політику\s+та\s+літератури\b", c_low):
        return False
    if re.search(r"\bЗапам[\x27\u2019\u02bc]яталалося\b", corr_text, re.IGNORECASE) or re.search(r"\bпустим\s+ротом\b", c_low):
        return False
    if re.search(r"\b(?:скоріше|швидше)\s+за\s+все\b", c_low):
        return False

    # Claude R11 Section B Invented / Meaning-changing rewrites
    if re.search(r"\bсуспільств\w*\b", o_low) and re.search(r"\bлюдств\w*\b", c_low):
        return False
    if re.search(r"\bподібн\w*\s+площ\w*\b", o_low) and re.search(r"\bтакою\s+самою\b", c_low):
        return False
    if re.search(r"\bбачити\s+цю\s+атмосферу\b", o_low) and re.search(r"\bвідчувати\b", c_low):
        return False
    if re.search(r"\bпродукту\b", c_low) and not re.search(r"\bпродукту\b", o_low):
        return False
    if re.search(r"\bздобути\s+завдяки\s+книгам\b", c_low):
        return False
    if re.search(r"\bзробити\s+сюрприз\b", c_low):
        return False
    if re.search(r"\bзаповним\b", o_low) and re.search(r"\bзаповнив\b", c_low):
        return False
    if re.search(r"\bзробленим\s+воно\s+буде\b", o_low):
        return False
    if re.search(r"\bСтарий\s+добрий\s+Боб\b", o_low) and re.search(r"\bБобе\b", c_low):
        return False
    if re.search(r"\bрозревіл\w*\b", o_low) and re.search(r"\bрозрюмсал\w*\b", c_low):
        return False
    if re.search(r"\bшибанувш\w*\b", o_low):
        return False
    if re.search(r"\bспадав\b", c_low) and not re.search(r"\bспадав\b", o_low):
        return False
    if re.search(r"\bбула\s+вже\s+ланкова\b", c_low):
        return False
    if re.search(r"\bна\s+спільну\s+користь\b", o_low) and re.search(r"\bдля\s+спільної\s+користі\b", c_low):
        return False

    # Claude R11 Section C Category F general gates
    # Future tense analytic vs synthetic
    if re.search(r"\bбуд(?:у|еш|е|емо|ете|уть)\s+[а-яіїєґА-ЯІЇЄҐ'-]+ти\b", o_low) and re.search(r"\b[а-яіїєґА-ЯІЇЄҐ'-]+тим(?:у|еш|е|емо|ете|уть)\b", c_low):
        return False
    if re.search(r"\b[а-яіїєґА-ЯІЇЄҐ'-]+тим(?:у|еш|е|емо|ете|уть)\b", o_low) and re.search(r"\bбуд(?:у|еш|е|емо|ете|уть)\s+[а-яіїєґА-ЯІЇЄҐ'-]+ти\b", c_low):
        return False
    # Particle б/би
    if re.search(r"\bб\b", o_low) and re.search(r"\bби\b", c_low) and not re.search(r"\bби\b", o_low):
        return False
    if re.search(r"\bби\b", o_low) and re.search(r"\bб\b", c_low) and not re.search(r"\bб\b", o_low):
        return False
    # Relative pronoun swap що -> який
    if orig_tokens:
        for start, end, _tag, repl in in_scope:
            if start < len(orig_tokens):
                err_w = " ".join(orig_tokens[start:end]).lower().strip()
                repl_w = repl.lower().strip()
                if err_w == "що" and re.match(r"^як(?:ий|а|е|і|ого|ій|им|их|ому|ою|у)\b", repl_w):
                    return False
    # Reflexive passive to active conversion
    if orig_tokens:
        for start, end, _tag, repl in in_scope:
            if start < len(orig_tokens):
                err_w = " ".join(orig_tokens[start:end]).lower().strip()
                repl_w = repl.lower().strip()
                if (
                    (err_w.endswith(("ся", "сь")) or any(w.endswith(("ся", "сь")) for w in err_w.split()))
                    and not repl_w.endswith(("ся", "сь"))
                    and (any(repl_w.endswith(suf) for suf in ("ють", "ять", "уть", "ать", "ли", "в", "ла", "ло", "є", "ють.", "ять.", "уть.", "ать.")) or "можна" in repl_w)
                ):
                    return False
    # Lexical Category F swaps
    if re.search(r"\bпару\b", o_low) and re.search(r"\bкільк\w*\b", c_low):
        return False
    if re.search(r"\bколи\s+б\b", o_low) and re.search(r"\bякби\b", c_low):
        return False
    if re.search(r"\bпідряд\b", o_low) and re.search(r"\bпоспіль\b", c_low):
        return False
    if re.search(r"\bбільше\s+того\b", o_low) and re.search(r"\bба\s+більше\b", c_low):
        return False
    if re.search(r"\bсправля\w*\s+враженн\w*\b", o_low) and re.search(r"\bвража\w*\b", c_low):
        return False
    if re.search(r"\bпалити\b", o_low) and re.search(r"\bкурити\b", c_low):
        return False
    if re.search(r"\bдатчан\w*\b", o_low) and re.search(r"\bданц\w*\b", c_low):
        return False
    if re.search(r"\bнарн\w*\b", o_low) and re.search(r"\bгарн\w*\b", c_low):
        return False
    if re.search(r"\bяке\s+ж\s+було\b", o_low) and re.search(r"\bяким\s+же\s+було\b", c_low):
        return False

    # Reject unpaired comma after relative pronoun
    if re.search(r"\b(?:який|яка|яке|які|якого|якій|яким|яких|яку)\s+(?:через|задля|внаслідок|попри)\s+[^,;]+,\s+[а-яіїєґА-ЯІЇЄҐ]", corr_text):
        return False

    # Reject wholesale essay rewrites where changed token share > 30%
    w1 = re.findall(r"\w+", orig_text.lower())
    w2 = re.findall(r"\w+", corr_text.lower())
    if not w1 or not w2:
        return False
    sm = difflib.SequenceMatcher(None, w1, w2)
    if sm.ratio() < 0.65:
        return False
    matched = sum(block.size for block in sm.get_matching_blocks())
    changed_words = max(len(w1), len(w2)) - matched
    if changed_words > 7:
        return False
    if len(w1) <= 8 and changed_words > 2:
        return False
    if len(w1) <= 14 and changed_words > 5:
        return False

    # Reject adjacent doubled words and 2-word repeated sequences
    if re.search(r"\b([а-яіїєґА-ЯІЇЄҐ]{2,})\s+\1\b", corr_text, re.IGNORECASE):
        return False
    if re.search(r"\b([а-яіїєґА-ЯІЇЄҐ']+\s+[а-яіїєґА-ЯІЇЄҐ']+)\s+\1\b", corr_text, re.IGNORECASE):
        return False
    # Reject repeated word separated by a single intervening word: e.g. "приносять саме приносять"
    if re.search(r"\b([а-яіїєґА-ЯІЇЄҐ']{3,})\s+\S+\s+\1\b", corr_text, re.IGNORECASE):
        return False

    # Reject repeated word (3+ chars) within 1 to 4 intervening words (e.g. "не треба молодої нареченої треба", "бухгалтер ... бухгалтера")
    # except legitimate idioms like "день у день", "раз у раз", "рік у рік", "час від часу", "сам на сам"
    words_c_3 = [w.lower() for w in re.findall(r"\b[а-яіїєґА-ЯІЇЄҐ']{3,}\b", corr_text)]
    idioms_allowed = {("день", "день"), ("раз", "раз"), ("рік", "рік"), ("сам", "сам"), ("час", "час"), ("край", "край"), ("пліч", "пліч")}
    for i in range(len(words_c_3)):
        for dist in range(1, 5):
            if i + dist + 1 < len(words_c_3):
                w_a = words_c_3[i]
                w_b = words_c_3[i + dist + 1]
                if w_a == w_b and (w_a, w_b) not in idioms_allowed:
                    return False

    # Reject adjacent stem repetition (e.g. з'явилася з'явила)
    words = re.findall(r"\b[\w'-]+\b", corr_text.lower())
    for i in range(len(words) - 1):
        a, b = words[i], words[i + 1]
        if len(a) >= 5 and len(b) >= 5 and (a.startswith(b[:4]) or b.startswith(a[:4])):
            return False

    # Reject missing sentence punctuation before capitalized pronoun/conjunction
    if re.search(
        r"[а-яіїєґ]\s+(Так|Він|Вона|Вони|Ми|Ви|Це|Але|Проте|Тоді|Якщо|Однак|Тому)\b",
        corr_text,
    ):
        return False

    # Reject Russianisms in orig_text and corr_text
    if has_russianism(corr_text, vesum_cur=vesum_cur) or has_russianism(orig_text, vesum_cur=vesum_cur):
        return False

    # Check ALL lowercase words in corr_text against VESUM and ensure finite verb / copula presence
    if vesum_cur is not None:
        cand_words = [re.sub(r"[^а-яіїєґА-ЯІЇЄҐ0-9'-]", "", w) for w in corr_text.split()]
        cand_words = [w.strip("-'").lower() for w in cand_words if w and w not in {"-", "'"}]
        predicative_words = {
            "є", "був", "була", "було", "були", "буде", "будуть", "нема", "немає",
            "це", "можна", "треба", "потрібно", "варто", "слід", "необхідно"
        }
        has_verb_or_copula = any(w in predicative_words for w in cand_words) or ("—" in corr_text and len(cand_words) >= 4)
        if not has_verb_or_copula:
            for w in cand_words:
                if w.isdigit():
                    continue
                row = vesum_cur.execute(
                    "SELECT pos, tags FROM forms_all WHERE word_form IN (?, ?, ?) LIMIT 1",
                    (w, w.capitalize(), w.upper()),
                ).fetchone()
                if row and row[0] == "verb" and "inf" not in row[1] and "adjp" not in row[1] and "advp" not in row[1]:
                    has_verb_or_copula = True
                    break
        if not has_verb_or_copula:
            return False

        words_c = re.findall(r"\b[\w'-]+\b", corr_text)
        for w in words_c:
            if "-" in w or w.isupper() or w[0].isupper() or len(w) <= 2 or any(c.isdigit() for c in w) or w.lower() in {"поцокалася", "зеєловських", "в'язей"}:
                continue
            row = vesum_cur.execute(
                "SELECT 1 FROM forms_all WHERE word_form = ? LIMIT 1",
                (w.lower(),),
            ).fetchone()
            if not row:
                return False

    return True


def load_held_out_firewall(
    manifest_path: Path = DEFAULT_FIREWALL_MANIFEST,
    test_m2_path: Path | None = None,
) -> tuple[set[str], set[str], set[str]]:
    """Load complete held-out test split firewall (doc IDs, source sentences, target sentences).

    Fails closed if the persistent committed firewall manifest is missing or empty.
    """
    if not manifest_path.is_file():
        raise RuntimeError(
            f"Held-out test firewall manifest missing at {manifest_path}. "
            "Cannot proceed without guaranteed test partition containment."
        )

    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    test_doc_ids = set(data.get("test_doc_ids", []))
    test_sources = set(data.get("test_source_sentences", []))
    test_targets = set(data.get("test_target_sentences", []))

    if not test_doc_ids or not test_sources or not test_targets:
        raise RuntimeError(
            f"Held-out test firewall manifest at {manifest_path} is empty or invalid. "
            f"Stats: docs={len(test_doc_ids)}, sources={len(test_sources)}, targets={len(test_targets)}"
        )

    return test_doc_ids, test_sources, test_targets


def build_jaccard_firewall_matcher(
    test_sentences: set[str],
    threshold: float = 0.80,
) -> Any:
    """Build an inverted index matcher to detect token Jaccard similarity >= threshold against held-out test."""
    def tokenize(text: str) -> frozenset[str]:
        return frozenset(re.findall(r"\w+", text.lower()))

    test_token_list = [tokenize(s) for s in test_sentences if s]
    test_lens = [len(t) for t in test_token_list]

    word_to_test_ids: dict[str, list[int]] = defaultdict(list)
    for idx, tset in enumerate(test_token_list):
        for w in tset:
            word_to_test_ids[w].append(idx)

    req_factor = threshold / (1.0 + threshold)

    def is_near_duplicate(cand_text: str) -> bool:
        cand_tokens = tokenize(cand_text)
        k = len(cand_tokens)
        if k == 0:
            return False
        min_len = math.ceil(k * threshold)
        max_len = int(k / threshold)

        id_counts: dict[int, int] = defaultdict(int)
        for w in cand_tokens:
            tids = word_to_test_ids.get(w)
            if not tids:
                continue
            for tid in tids:
                if min_len <= test_lens[tid] <= max_len:
                    id_counts[tid] += 1

        for tid, inter in id_counts.items():
            L = test_lens[tid]
            req_intersection = math.ceil(req_factor * (k + L))
            if inter >= req_intersection:
                union = k + L - inter
                if union > 0 and (inter / union) >= threshold:
                    return True
        return False

    return is_near_duplicate


def load_brown_uk_controls(
    brown_path: Path,
    is_near_dup_fn: Any = None,
    vesum_cur: sqlite3.Cursor | None = None,
) -> list[dict[str, Any]]:
    """Load pristine control sentences with authentic attribution from Brown-UK corpus."""
    if not brown_path.is_file():
        raise RuntimeError(f"Required Brown-UK control file missing at {brown_path}")
    controls = []
    brown_doc_counters: Counter[str] = Counter()
    with brown_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                sent = detokenize(data.get("sentence_text", "").strip())
                if not sent or not is_clean_control(sent, vesum_cur=vesum_cur) or (is_near_dup_fn and is_near_dup_fn(sent)):
                    continue
                doc_id = data.get("document_id") or "brown_uk"
                doc_name = data.get("source_metadata", {}).get("doc_name") or f"{doc_id}.txt"
                eval_id = data.get("eval_id")
                sent_idx = brown_doc_counters[doc_id]
                brown_doc_counters[doc_id] += 1
                controls.append(
                    {
                        "doc_id": doc_id,
                        "doc_name": doc_name,
                        "eval_id": eval_id,
                        "sent_idx": sent_idx,
                        "original_text": sent,
                        "source_type": "brown_uk_good",
                        "source_corpus": "brown_uk",
                        "license": "CC BY-NC-SA 4.0",
                    }
                )
    return controls


def parse_m2_sentences(m2_path: Path) -> list[dict[str, Any]]:
    """Parse M2 file into structured sentence records."""
    records = []
    doc_id = None
    cur_sent = None
    cur_edits: dict[int, list[tuple[int, int, str, str]]] = {}
    sent_idx = 0

    with m2_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                if cur_sent is not None:
                    records.append(
                        {
                            "doc_id": doc_id,
                            "sent_idx": sent_idx,
                            "sent_tokens": cur_sent.split(),
                            "edits_by_ann": cur_edits,
                        }
                    )
                    sent_idx += 1
                    cur_sent = None
                    cur_edits = {}
                continue
            m_doc = re.match(r"^S # (\d{4})$", line)
            if m_doc:
                if cur_sent is not None:
                    records.append(
                        {
                            "doc_id": doc_id,
                            "sent_idx": sent_idx,
                            "sent_tokens": cur_sent.split(),
                            "edits_by_ann": cur_edits,
                        }
                    )
                    cur_sent = None
                    cur_edits = {}
                doc_id = m_doc.group(1)
                sent_idx = 0
            elif line.startswith("S "):
                if cur_sent is not None:
                    records.append(
                        {
                            "doc_id": doc_id,
                            "sent_idx": sent_idx,
                            "sent_tokens": cur_sent.split(),
                            "edits_by_ann": cur_edits,
                        }
                    )
                    sent_idx += 1
                cur_sent = line[2:].strip()
                cur_edits = {}
            elif line.startswith("A "):
                parts = line[2:].split("|||")
                span = parts[0].split()
                start, end = int(span[0]), int(span[1])
                tag = parts[1]
                corr = parts[2]
                ann_id = int(parts[5]) if len(parts) > 5 else 0
                if ann_id not in cur_edits:
                    cur_edits[ann_id] = []
                cur_edits[ann_id].append((start, end, tag, corr))

    if cur_sent is not None:
        records.append(
            {
                "doc_id": doc_id,
                "sent_idx": sent_idx,
                "sent_tokens": cur_sent.split(),
                "edits_by_ann": cur_edits,
            }
        )
    return records


def build_grammar_dataset(
    train_m2_path: Path = DEFAULT_UA_GEC_TRAIN_M2,
    test_m2_path: Path = DEFAULT_UA_GEC_TEST_M2,
    firewall_manifest_path: Path = DEFAULT_FIREWALL_MANIFEST,
    brown_path: Path = DEFAULT_BROWN_UK_EVAL,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Execute complete dataset build pipeline."""
    print("🚀 Initializing Grammar Component Build (#8342)...")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load test firewall blacklist (Fail-closed)
    test_doc_ids, test_sources, test_targets = load_held_out_firewall(
        manifest_path=firewall_manifest_path,
        test_m2_path=test_m2_path,
    )
    all_test_sentences = test_sources | test_targets
    is_test_near_duplicate = build_jaccard_firewall_matcher(all_test_sentences, threshold=0.80)
    print(
        f"🔒 Held-out test firewall active: {len(test_doc_ids)} docs, "
        f"{len(test_sources)} source sents, {len(test_targets)} target sents, Jaccard < 0.80 enforced."
    )

    vesum_db_path = PROJECT_ROOT / "data" / "vesum.db"
    vesum_conn = sqlite3.connect(f"file:{vesum_db_path}?mode=ro", uri=True)
    vesum_cur = vesum_conn.cursor()

    # 2. Load Brown-UK pristine controls
    brown_controls = load_brown_uk_controls(
        brown_path, is_near_dup_fn=is_test_near_duplicate, vesum_cur=vesum_cur
    )
    print(f"📖 Loaded {len(brown_controls)} pristine Brown-UK control sentences.")

    # 3. Parse UA-GEC train sentences
    if not train_m2_path.is_file():
        raise RuntimeError(f"UA-GEC train M2 missing at {train_m2_path}")
    raw_sentences = parse_m2_sentences(train_m2_path)
    print(f"📄 Parsed {len(raw_sentences)} sentences from {train_m2_path.name}.")

    # 4. Partition UA-GEC documents 90:10 by doc_id SHA-256 hash (filtering test doc IDs)
    doc_splits = {}
    for item in raw_sentences:
        d = item["doc_id"]
        if d in test_doc_ids:
            continue
        if d not in doc_splits:
            h = int(hashlib.sha256(d.encode("utf-8")).hexdigest(), 16)
            doc_splits[d] = "eval" if (h % 10 == 0) else "train"

    train_doc_count = sum(1 for s in doc_splits.values() if s == "train")
    eval_doc_count = sum(1 for s in doc_splits.values() if s == "eval")
    print(
        f"🔀 UA-GEC partition: {train_doc_count} train docs ({train_doc_count/len(doc_splits):.1%}), "
        f"{eval_doc_count} eval docs ({eval_doc_count/len(doc_splits):.1%})."
    )

    # 5. Extract substantive corrections and pristine zero-error controls
    seen_corrections: set[tuple[str, str]] = set()
    seen_control_texts: set[str] = set()
    euphony_pairs = {
        ("і", "й"), ("й", "і"),
        ("у", "в"), ("в", "у"),
        ("з", "із"), ("із", "з"),
        ("з", "зі"), ("зі", "з"),
        ("із", "зі"), ("зі", "із"),
    }

    eval_items_raw = [item for item in raw_sentences if doc_splits.get(item["doc_id"]) == "eval"]
    train_items_raw = [item for item in raw_sentences if doc_splits.get(item["doc_id"]) == "train"]

    eval_corrections = []
    eval_clean_candidates = []
    parallel_target_retentions = 0

    # 5a. Process eval documents first
    for item in eval_items_raw:
        d = item["doc_id"]
        orig_tokens = item["sent_tokens"]
        orig_text = detokenize(" ".join(orig_tokens))

        if (
            not orig_text
            or orig_text in test_sources
            or orig_text in test_targets
            or is_test_near_duplicate(orig_text)
        ):
            continue

        all_edits = [e for elist in item["edits_by_ann"].values() for e in elist if e[2] != "noop"]
        if not all_edits:
            if (
                is_clean_control(orig_text, vesum_cur=vesum_cur)
                and orig_text not in seen_control_texts
                and not is_test_near_duplicate(orig_text)
            ):
                seen_control_texts.add(orig_text)
                eval_clean_candidates.append(
                    {
                        "doc_id": d,
                        "doc_name": f"{d}.txt",
                        "sent_idx": item["sent_idx"],
                        "original_text": orig_text,
                        "source_type": "ua_gec_gold_clean",
                        "source_corpus": "ua_gec_2.0",
                        "license": "CC BY 4.0",
                    }
                )
            continue

        distinct_targets_for_sentence: set[str] = set()
        for ann_id, edit_list in sorted(item["edits_by_ann"].items()):
            in_scope = [e for e in edit_list if e[2] in IN_SCOPE_TAGS]
            if not in_scope:
                continue

            all_non_noop = [e for e in edit_list if e[2] != "noop"]
            all_sorted = sorted(all_non_noop, key=lambda x: (x[0], x[1]), reverse=True)

            valid = True
            for i in range(len(all_sorted) - 1):
                if all_sorted[i][0] < all_sorted[i + 1][1]:
                    valid = False
                    break
            if not valid:
                continue

            toks = list(orig_tokens)
            for start, end, _tag, corr in all_sorted:
                repl = corr.split() if corr else []
                toks[start:end] = repl

            corr_text = detokenize(" ".join(toks))
            if not orig_text.strip().startswith(("—", "–", "-")) and corr_text.strip().startswith(("—", "–", "-")):
                corr_text = re.sub(r"^[—–-]\s*", "", corr_text.strip())
            if orig_text.strip().startswith(("—", "–", "-")) and not corr_text.strip().startswith(("—", "–", "-")):
                corr_text = "— " + corr_text.strip()
            if (
                orig_text != corr_text
                and corr_text not in test_sources
                and corr_text not in test_targets
                and not is_test_near_duplicate(corr_text)
                and is_valid_candidate(orig_text, corr_text, in_scope, vesum_cur, orig_tokens=orig_tokens)
            ):
                pair_key = (orig_text, corr_text)
                if pair_key in seen_corrections:
                    continue
                seen_corrections.add(pair_key)
                if len(distinct_targets_for_sentence) > 0:
                    parallel_target_retentions += 1
                distinct_targets_for_sentence.add(corr_text)

                sorted_in_scope = sorted(
                    in_scope,
                    key=lambda e: (
                        0 if resolve_specific_linguistic_citation(
                            e[2],
                            " ".join(orig_tokens[e[0] : e[1]]),
                            e[3],
                            orig_text,
                            corr_text,
                        ) is not None else 1,
                        e[0],
                    ),
                )
                primary_edit = sorted_in_scope[0]
                primary_tag = primary_edit[2]
                err_span = " ".join(orig_tokens[primary_edit[0] : primary_edit[1]]).strip(" ,.-–—;:?!\"'«»")
                repl_span = primary_edit[3].strip(" ,.-–—;:?!\"'«»")
                all_tags = [e[2] for e in in_scope]
                content_edits = []
                for e in all_non_noop:
                    if e[2] == "noop":
                        continue
                    if e[2] == "Punctuation":
                        if "," in " ".join(orig_tokens[e[0]:e[1]]) and "," not in e[3]:
                            content_edits.append(e)
                    elif e[2] == "Spelling":
                        orig_w = " ".join(orig_tokens[e[0]:e[1]]).lower().strip()
                        repl_w = e[3].lower().strip()
                        if (orig_w, repl_w) not in euphony_pairs:
                            content_edits.append(e)
                    else:
                        content_edits.append(e)

                eval_corrections.append(
                    {
                        "doc_id": d,
                        "doc_name": f"{d}.txt",
                        "sent_idx": item["sent_idx"],
                        "ann_id": ann_id,
                        "original_text": orig_text,
                        "corrected_text": corr_text,
                        "primary_tag": primary_tag,
                        "all_tags": all_tags,
                        "err_span": err_span,
                        "repl_span": repl_span,
                        "num_content_edits": len(content_edits),
                        "num_total_edits": len(all_non_noop),
                        "has_other_content": any(e[2] not in IN_SCOPE_TAGS for e in content_edits),
                        "source_type": "ua_gec_human_annotated",
                        "source_corpus": "ua_gec_2.0",
                        "license": "CC BY 4.0",
                    }
                )

    # Eval split sentences: strictly forbidden in train to guarantee zero leakage
    eval_forbidden_sentences = (
        {c["original_text"] for c in eval_corrections}
        | {c["corrected_text"] for c in eval_corrections}
        | {c["original_text"] for c in eval_clean_candidates}
    )

    # 5b. Process train documents
    train_corrections = []
    train_clean_candidates = []

    for item in train_items_raw:
        d = item["doc_id"]
        orig_tokens = item["sent_tokens"]
        orig_text = detokenize(" ".join(orig_tokens))

        if (
            not orig_text
            or orig_text in test_sources
            or orig_text in test_targets
            or orig_text in eval_forbidden_sentences
            or is_test_near_duplicate(orig_text)
        ):
            continue

        all_edits = [e for elist in item["edits_by_ann"].values() for e in elist if e[2] != "noop"]
        if not all_edits:
            if (
                is_clean_control(orig_text, vesum_cur=vesum_cur)
                and orig_text not in seen_control_texts
                and not is_test_near_duplicate(orig_text)
            ):
                seen_control_texts.add(orig_text)
                train_clean_candidates.append(
                    {
                        "doc_id": d,
                        "doc_name": f"{d}.txt",
                        "sent_idx": item["sent_idx"],
                        "original_text": orig_text,
                        "source_type": "ua_gec_gold_clean",
                        "source_corpus": "ua_gec_2.0",
                        "license": "CC BY 4.0",
                    }
                )
            continue

        distinct_targets_for_sentence: set[str] = set()
        for ann_id, edit_list in sorted(item["edits_by_ann"].items()):
            in_scope = [e for e in edit_list if e[2] in IN_SCOPE_TAGS]
            if not in_scope:
                continue

            all_non_noop = [e for e in edit_list if e[2] != "noop"]
            all_sorted = sorted(all_non_noop, key=lambda x: (x[0], x[1]), reverse=True)

            valid = True
            for i in range(len(all_sorted) - 1):
                if all_sorted[i][0] < all_sorted[i + 1][1]:
                    valid = False
                    break
            if not valid:
                continue

            toks = list(orig_tokens)
            for start, end, _tag, corr in all_sorted:
                repl = corr.split() if corr else []
                toks[start:end] = repl

            corr_text = detokenize(" ".join(toks))
            if not orig_text.strip().startswith(("—", "–", "-")) and corr_text.strip().startswith(("—", "–", "-")):
                corr_text = re.sub(r"^[—–-]\s*", "", corr_text.strip())
            if orig_text.strip().startswith(("—", "–", "-")) and not corr_text.strip().startswith(("—", "–", "-")):
                corr_text = "— " + corr_text.strip()
            if (
                orig_text != corr_text
                and corr_text not in test_sources
                and corr_text not in test_targets
                and corr_text not in eval_forbidden_sentences
                and not is_test_near_duplicate(corr_text)
                and is_valid_candidate(orig_text, corr_text, in_scope, vesum_cur, orig_tokens=orig_tokens)
            ):
                pair_key = (orig_text, corr_text)
                if pair_key in seen_corrections:
                    continue
                seen_corrections.add(pair_key)
                if len(distinct_targets_for_sentence) > 0:
                    parallel_target_retentions += 1
                distinct_targets_for_sentence.add(corr_text)

                sorted_in_scope = sorted(
                    in_scope,
                    key=lambda e: (
                        0 if resolve_specific_linguistic_citation(
                            e[2],
                            " ".join(orig_tokens[e[0] : e[1]]),
                            e[3],
                            orig_text,
                            corr_text,
                        ) is not None else 1,
                        e[0],
                    ),
                )
                primary_edit = sorted_in_scope[0]
                primary_tag = primary_edit[2]
                err_span = " ".join(orig_tokens[primary_edit[0] : primary_edit[1]]).strip(" ,.-–—;:?!\"'«»")
                repl_span = primary_edit[3].strip(" ,.-–—;:?!\"'«»")
                all_tags = [e[2] for e in in_scope]
                content_edits = []
                for e in all_non_noop:
                    if e[2] == "noop":
                        continue
                    if e[2] == "Punctuation":
                        if "," in " ".join(orig_tokens[e[0]:e[1]]) and "," not in e[3]:
                            content_edits.append(e)
                    elif e[2] == "Spelling":
                        orig_w = " ".join(orig_tokens[e[0]:e[1]]).lower().strip()
                        repl_w = e[3].lower().strip()
                        if (orig_w, repl_w) not in euphony_pairs:
                            content_edits.append(e)
                    else:
                        content_edits.append(e)

                train_corrections.append(
                    {
                        "doc_id": d,
                        "doc_name": f"{d}.txt",
                        "sent_idx": item["sent_idx"],
                        "ann_id": ann_id,
                        "original_text": orig_text,
                        "corrected_text": corr_text,
                        "primary_tag": primary_tag,
                        "all_tags": all_tags,
                        "err_span": err_span,
                        "repl_span": repl_span,
                        "num_content_edits": len(content_edits),
                        "num_total_edits": len(all_non_noop),
                        "has_other_content": any(e[2] not in IN_SCOPE_TAGS for e in content_edits),
                        "source_type": "ua_gec_human_annotated",
                        "source_corpus": "ua_gec_2.0",
                        "license": "CC BY 4.0",
                    }
                )

    print(
        f"📊 Extracted substantive corrections: {len(train_corrections)} train, "
        f"{len(eval_corrections)} eval. Parallel annotator target retentions: {parallel_target_retentions}."
    )
    print(f"🛡️  Extracted clean control candidates: {len(train_clean_candidates)} train, {len(eval_clean_candidates)} eval.")

    # Determine explainable candidates: strictly single edit, single category, verified token match
    def can_explain_candidate(cand_item: dict[str, Any]) -> bool:
        # Multi-edit sentences MUST fail closed to silent_rewrite per Claude R7 B5 and Claude R8 D
        if cand_item.get("num_content_edits", 1) > 1:
            return False
        tags = cand_item.get("all_tags", [])
        if len(tags) > 1 or len(set(tags)) > 1:
            return False
        cats = {TAG_TO_COARSE_CATEGORY.get(t, t) for t in tags}
        if len(cats) > 1:
            return False
        cit = resolve_specific_linguistic_citation(
            cand_item["primary_tag"],
            cand_item.get("err_span", ""),
            cand_item.get("repl_span", ""),
            cand_item["original_text"],
            cand_item["corrected_text"],
        )
        if cit is None:
            return False
        # Verify named token in citation matches changed tokens
        desc, rule = cit[1], cit[2]
        err_w = cand_item.get("err_span", "").strip()
        corr_w = cand_item.get("repl_span", "").strip()
        if err_w and f"«{err_w}»" not in desc and f"«{err_w}»" not in rule and err_w not in desc and err_w not in rule:
            return False
        return not bool(corr_w and f"«{corr_w}»" not in desc and f"«{corr_w}»" not in rule and corr_w not in desc and corr_w not in rule)

    # Overall calibration: exact 55.0% explained corrections across the full dataset
    eval_expl_count = sum(1 for c in eval_corrections if can_explain_candidate(c))
    train_explainable = [c for c in train_corrections if can_explain_candidate(c)]
    train_unexplainable = [c for c in train_corrections if not can_explain_candidate(c)]

    target_total_corrections = 1160
    total_expl_needed = round(target_total_corrections * 0.55)
    target_train_expl = min(len(train_explainable), max(0, total_expl_needed - eval_expl_count))
    target_train_total = target_total_corrections - len(eval_corrections)
    target_train_unexpl = target_train_total - target_train_expl

    orig_counts = Counter(c["original_text"] for c in train_corrections)
    base_cats = Counter(TAG_TO_COARSE_CATEGORY.get(c["primary_tag"], c["primary_tag"]) for c in eval_corrections)

    def expl_priority(item: dict[str, Any]):
        orig = item["original_text"]
        is_parallel = 0 if orig_counts[orig] > 1 else 1
        h = hashlib.sha256(f"{item['doc_id']}_{orig}_{item['corrected_text']}".encode()).hexdigest()
        return (is_parallel, h)

    sorted_expl = sorted(train_explainable, key=expl_priority)
    selected_expl = sorted_expl[:target_train_expl]

    expl_origs = {c["original_text"] for c in selected_expl}
    base_cats.update(TAG_TO_COARSE_CATEGORY.get(c["primary_tag"], c["primary_tag"]) for c in selected_expl)

    def unexpl_priority(item: dict[str, Any]):
        orig = item["original_text"]
        is_parallel = 0 if orig_counts[orig] > 1 else 1
        partner_in_expl = 0 if orig in expl_origs else 1
        cat = TAG_TO_COARSE_CATEGORY.get(item["primary_tag"], item["primary_tag"])
        deficit = max(0, 50 - base_cats.get(cat, 0))
        h = hashlib.sha256(f"{item['doc_id']}_{orig}_{item['corrected_text']}".encode()).hexdigest()
        return (is_parallel, partner_in_expl, -deficit, h)

    sorted_unexpl = sorted(train_unexplainable, key=unexpl_priority)
    selected_unexpl = sorted_unexpl[:target_train_unexpl]

    train_corrections = selected_expl + selected_unexpl
    train_corrections.sort(key=lambda x: hashlib.sha256(f"{x['doc_id']}_{x['original_text']}_{x['corrected_text']}".encode()).hexdigest())

    # 6. Formulate exact 75.0% corrections / 25.0% controls mixture
    # Partition Brown-UK controls strictly by doc_id hash (90:10)
    brown_train_available = []
    brown_eval_available = []
    seen_corr_sources = {c["original_text"] for c in train_corrections + eval_corrections}

    for b in brown_controls:
        txt = b["original_text"]
        if (
            txt in test_sources
            or txt in test_targets
            or txt in seen_control_texts
            or txt in seen_corr_sources
        ):
            continue
        h = int(hashlib.sha256(b["doc_id"].encode("utf-8")).hexdigest(), 16)
        if h % 10 == 0:
            brown_eval_available.append(b)
        else:
            brown_train_available.append(b)

    target_train_controls = 350
    target_eval_controls = 51

    print(f"🎯 Target controls for 25.0% share: {target_train_controls} train, {target_eval_controls} eval.")

    # Populate train controls: prioritize Brown-UK, then gold UA-GEC train clean
    train_controls = []
    brown_train_allocation = min(target_train_controls, len(brown_train_available))

    for b in brown_train_available[:brown_train_allocation]:
        seen_control_texts.add(b["original_text"])
        train_controls.append(b)

    for item in train_clean_candidates:
        if len(train_controls) >= target_train_controls:
            break
        train_controls.append(item)

    # Populate eval controls: prioritize Brown-UK eval partition, then gold UA-GEC eval clean
    eval_controls = []
    for b in brown_eval_available:
        if len(eval_controls) >= target_eval_controls:
            break
        if b["original_text"] not in seen_control_texts:
            seen_control_texts.add(b["original_text"])
            eval_controls.append(b)

    for item in eval_clean_candidates:
        if len(eval_controls) >= target_eval_controls:
            break
        eval_controls.append(item)

    print(
        f"✅ Formed train slice: {len(train_corrections)} corrections + {len(train_controls)} controls = "
        f"{len(train_corrections) + len(train_controls)} total (control share: {len(train_controls) / (len(train_corrections) + len(train_controls)):.2%})."
    )
    print(
        f"✅ Formed eval slice: {len(eval_corrections)} corrections + {len(eval_controls)} controls = "
        f"{len(eval_corrections) + len(eval_controls)} total (control share: {len(eval_controls) / (len(eval_corrections) + len(eval_controls)):.2%})."
    )

    # 7. Build records with diversified queries, 45/55 task mix, and authoritative citations
    def format_records(
        corrections: list[dict[str, Any]],
        controls: list[dict[str, Any]],
        split_name: str,
    ) -> list[dict[str, Any]]:
        dataset_records = []
        global_seed = 0 if split_name == "train" else 50000

        # Interleave corrections and controls
        all_raw_items = []
        for c in corrections:
            all_raw_items.append((True, c))
        for c in controls:
            all_raw_items.append((False, c))

        # Deterministic shuffle / sort by content hash
        all_raw_items.sort(
            key=lambda x: hashlib.sha256(f"{x[1]['doc_id']}_{x[1]['original_text']}".encode()).hexdigest()
        )



        eligible_err_indices = [
            i for i, (is_err, it) in enumerate(all_raw_items)
            if is_err and can_explain_candidate(it)
        ]
        explained_err_indices = set(eligible_err_indices)

        # Assign task mix: calibrated to land ~55% explained corrections post citation drop
        used_queries: set[str] = set()
        for idx, (is_err, item) in enumerate(all_raw_items):
            seed_idx = global_seed + idx
            orig_text = item["original_text"]
            reg = classify_sentence_register(orig_text)

            if split_name == "eval":
                query = ""
                for offset in range(len(PROMPT_TEMPLATES_EVAL)):
                    cand = PROMPT_TEMPLATES_EVAL[(seed_idx + offset) % len(PROMPT_TEMPLATES_EVAL)].format(sentence=orig_text)
                    if cand not in used_queries:
                        query = cand
                        used_queries.add(cand)
                        seed_idx = seed_idx + offset
                        break
                if not query:
                    query = build_query_eval(orig_text, seed_idx)
            else:
                templates = PROMPT_TEMPLATES_BY_REGISTER.get(reg) or PROMPT_TEMPLATES_BY_REGISTER["journalistic"]
                query = ""
                for offset in range(len(templates)):
                    cand = templates[(seed_idx + offset) % len(templates)].format(sentence=orig_text)
                    if cand not in used_queries:
                        query = cand
                        used_queries.add(cand)
                        seed_idx = seed_idx + offset
                        break
                if not query:
                    query = build_query(orig_text, reg, seed_idx)

            is_explained = (idx in explained_err_indices) if is_err else (idx % 100 < 55)

            if is_err:
                corr_text = item["corrected_text"]
                primary_tag = item["primary_tag"]
                coarse_category = TAG_TO_COARSE_CATEGORY.get(primary_tag, "syntax_structure")
                err_span = item["err_span"]
                repl_span = item["repl_span"]
                doc_id = item["doc_id"]
                doc_name = item.get("doc_name") or f"{doc_id}.txt"
                ann_id = item.get("ann_id", 0)
                sent_idx = item.get("sent_idx", idx)
                record_id = f"gram_{doc_id}_s{sent_idx}_a{ann_id}"
                source_corpus = item.get("source_corpus", "ua_gec_2.0")
                license_type = item.get("license", "CC BY 4.0")

                if split_name == "eval":
                    reasoning_steps, final_response, source_meta = build_reasoning_and_response_eval(
                        original_text=orig_text,
                        corrected_text=corr_text,
                        is_erroneous=True,
                        is_explained=is_explained,
                        primary_tag=primary_tag,
                        register=reg,
                        error_span=err_span,
                        replacement_span=repl_span,
                        seed_index=seed_idx,
                    )
                else:
                    reasoning_steps, final_response, source_meta = build_reasoning_and_response(
                        original_text=orig_text,
                        corrected_text=corr_text,
                        is_erroneous=True,
                        is_explained=is_explained,
                        primary_tag=primary_tag,
                        register=reg,
                        error_span=err_span,
                        replacement_span=repl_span,
                        seed_index=seed_idx,
                    )

                actual_task_type = "explained_correction" if reasoning_steps else "silent_rewrite"

                source_meta["doc_id"] = doc_id
                source_meta["doc_name"] = doc_name
                source_meta["annotator_id"] = ann_id
                source_meta["license"] = license_type
                source_meta["source_corpus"] = source_corpus
                source_meta["task_type"] = actual_task_type

                rec = {
                    "record_id": record_id,
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "split": split_name,
                    "category": coarse_category,
                    "tag": primary_tag,
                    "in_scope_tags": item["all_tags"],
                    "disposition": "correction",
                    "is_erroneous": True,
                    "task_type": actual_task_type,
                    "register": reg,
                    "query": query,
                    "original_text": orig_text,
                    "corrected_text": corr_text,
                    "final_response": final_response,
                    "reasoning_steps": reasoning_steps,
                    "chosen": corr_text,
                    "rejected": orig_text,
                    "source_corpus": source_corpus,
                    "license": license_type,
                    "source_metadata": source_meta,
                }
            else:
                doc_id = item["doc_id"]
                doc_name = item.get("doc_name") or f"{doc_id}.txt"
                sent_idx = item.get("sent_idx", idx)
                record_id = f"ctrl_{doc_id}_s{sent_idx}"
                coarse_category = "protective_authentic_control"
                source_corpus = item.get(
                    "source_corpus",
                    "brown_uk" if "brown" in item.get("source_type", "") else "ua_gec_2.0",
                )
                license_type = item.get(
                    "license",
                    "CC BY-NC-SA 4.0" if "brown" in item.get("source_type", "") else "CC BY 4.0",
                )

                if split_name == "eval":
                    reasoning_steps, final_response, source_meta = build_reasoning_and_response_eval(
                        original_text=orig_text,
                        corrected_text=orig_text,
                        is_erroneous=False,
                        is_explained=is_explained,
                        primary_tag="control_clean",
                        register=reg,
                        error_span="",
                        replacement_span="",
                        seed_index=seed_idx,
                    )
                else:
                    reasoning_steps, final_response, source_meta = build_reasoning_and_response(
                        original_text=orig_text,
                        corrected_text=orig_text,
                        is_erroneous=False,
                        is_explained=is_explained,
                        primary_tag="control_clean",
                        register=reg,
                        error_span="",
                        replacement_span="",
                        seed_index=seed_idx,
                    )

                actual_task_type = "explained_control" if reasoning_steps else "silent_control"

                source_meta["doc_id"] = doc_id
                source_meta["doc_name"] = doc_name
                if item.get("eval_id"):
                    source_meta["eval_id"] = item["eval_id"]
                source_meta["license"] = license_type
                source_meta["source_corpus"] = source_corpus
                source_meta["task_type"] = actual_task_type

                rec = {
                    "record_id": record_id,
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "split": split_name,
                    "category": coarse_category,
                    "tag": "control_clean",
                    "in_scope_tags": [],
                    "disposition": "control",
                    "is_erroneous": False,
                    "task_type": actual_task_type,
                    "register": reg,
                    "query": query,
                    "original_text": orig_text,
                    "corrected_text": orig_text,
                    "final_response": final_response,
                    "reasoning_steps": reasoning_steps,
                    "chosen": orig_text,
                    "rejected": None,
                    "source_corpus": source_corpus,
                    "license": license_type,
                    "source_metadata": source_meta,
                }

            dataset_records.append(rec)
        return dataset_records

    train_dataset_records = format_records(train_corrections, train_controls, "train")
    eval_dataset_records = format_records(eval_corrections, eval_controls, "eval")

    # 8. Write JSONL shards (< 1.8 MB each to respect repository 2,000,000 byte gate)
    for old_shard in output_dir.glob("grammar_*_shard_*.jsonl"):
        old_shard.unlink()

    num_train_shards = 8
    train_shard_size = (len(train_dataset_records) + num_train_shards - 1) // num_train_shards
    manifest_splits = {}

    for shard_idx in range(num_train_shards):
        shard_records = train_dataset_records[shard_idx * train_shard_size : (shard_idx + 1) * train_shard_size]
        fname = f"grammar_train_shard_{shard_idx + 1:02d}_of_{num_train_shards:02d}.jsonl"
        shard_path = output_dir / fname
        with shard_path.open("w", encoding="utf-8") as f:
            for r in shard_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        manifest_splits[fname] = "train"

    num_eval_shards = 2
    eval_shard_size = (len(eval_dataset_records) + num_eval_shards - 1) // num_eval_shards

    for shard_idx in range(num_eval_shards):
        shard_records = eval_dataset_records[shard_idx * eval_shard_size : (shard_idx + 1) * eval_shard_size]
        fname = f"grammar_eval_shard_{shard_idx + 1:02d}_of_{num_eval_shards:02d}.jsonl"
        shard_path = output_dir / fname
        with shard_path.open("w", encoding="utf-8") as f:
            for r in shard_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        manifest_splits[fname] = "eval"

    print(f"💾 Wrote {len(train_dataset_records)} train records across {num_train_shards} shards.")
    print(f"💾 Wrote {len(eval_dataset_records)} eval records across {num_eval_shards} shards.")

    # 9. Write cases.json catalog
    cases = []
    for tag in sorted(IN_SCOPE_TAGS):
        prof = AUTHORITY_PROFILES[tag]
        cases.append(
            {
                "case_id": f"gram_tag_{tag.replace('/', '_').lower()}",
                "tag": tag,
                "category": TAG_TO_COARSE_CATEGORY.get(tag, "syntax_structure"),
                "authority": prof["authority"],
                "description": prof["description"],
                "rule_template": prof["rule_template"],
                "status": "active_in_scope",
            }
        )
    cases.append(
        {
            "case_id": "gram_control_clean",
            "tag": "control_clean",
            "category": "protective_authentic_control",
            "authority": CONTROL_PROFILE["authority"],
            "description": CONTROL_PROFILE["description"],
            "rule_template": CONTROL_PROFILE["rule_template"],
            "status": "active_control",
        }
    )

    cases_file = output_dir / "cases.json"
    with cases_file.open("w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"💾 Wrote {len(cases)} cases to {cases_file.name}.")

    # 10. Write manifest.json
    total_records = len(train_dataset_records) + len(eval_dataset_records)
    total_corrections = len(train_corrections) + len(eval_corrections)
    total_controls = len(train_controls) + len(eval_controls)

    manifest = {
        "dataset_name": "grammar_v1",
        "version": "1.0.0",
        "task_type": "correction",
        "has_evaluation_split": True,
        "splits": manifest_splits,
        "description": "Verified Ukrainian grammar, valency, and morphosyntactic corrections rebuilt from authentic human-annotated sentences in UA-GEC (#8342).",
        "governing_issues": ["#8342", "#6321"],
        "licenses": {
            "ua_gec_2.0": {
                "license": "CC BY 4.0",
                "attribution": "UA-GEC: Corpus of Annotated Sentences for Ukrainian GEC",
            },
            "brown_uk": {
                "license": "CC BY-NC-SA 4.0",
                "attribution": "Brown-UK: Corpus of Contemporary Ukrainian (BrUK)",
            },
        },
        "statistics": {
            "total_records": total_records,
            "train_records": len(train_dataset_records),
            "eval_records": len(eval_dataset_records),
            "substantive_corrections": total_corrections,
            "clean_controls": total_controls,
            "clean_control_share": round(total_controls / total_records, 4),
            "substantive_correction_share": round(total_corrections / total_records, 4),
            "category_counts": dict(Counter(r["category"] for r in train_dataset_records + eval_dataset_records)),
            "source_corpus_counts": dict(Counter(r["source_corpus"] for r in train_dataset_records + eval_dataset_records)),
            "license_counts": dict(Counter(r["license"] for r in train_dataset_records + eval_dataset_records)),
        },
    }

    manifest_file = output_dir / "manifest.json"
    with manifest_file.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"💾 Wrote dataset manifest to {manifest_file.name}.")

    vesum_conn.close()

    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Grammar Component Dataset (#8342)")
    parser.add_argument("--train-m2", type=Path, default=DEFAULT_UA_GEC_TRAIN_M2)
    parser.add_argument("--test-m2", type=Path, default=DEFAULT_UA_GEC_TEST_M2)
    parser.add_argument("--firewall-manifest", type=Path, default=DEFAULT_FIREWALL_MANIFEST)
    parser.add_argument("--brown", type=Path, default=DEFAULT_BROWN_UK_EVAL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    build_grammar_dataset(
        train_m2_path=args.train_m2,
        test_m2_path=args.test_m2,
        firewall_manifest_path=args.firewall_manifest,
        brown_path=args.brown,
        output_dir=args.output_dir,
    )
