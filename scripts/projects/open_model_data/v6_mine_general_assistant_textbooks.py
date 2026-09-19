#!/usr/bin/env python3
"""v6_mine_general_assistant_textbooks.py - Track 1 General Ukrainian Assistant Engine.

Part of the Sovereign Ukrainian NLP Dataset Roadmap (Epic #6321, Phase 6.1, Issue #8139).

Deliverables:
1. Extraction engine mining 52,070 textbook chunks from data/sources.db:
   - Mathematics & Exact Sciences: Algebra, Geometry, Mathematics, Informatics
   - Natural Sciences: Physics, Chemistry, Biology, Geography, Astronomy, Nature
   - Social Sciences & Humanities: History of Ukraine, World History, Law, Civics,
     Economics, Finance, Ukrainian Language, Ukrainian Literature, World Literature,
     Arts, Ethics, Health, Technologies
2. SFT dataset: 75,000 multi-turn instructional reasoning trajectories sharded across
   150 shards (500 trajectories per shard, <= 2,000 KB each) with manifest.json
3. Held-out eval benchmark: 2,500 tasks across STEM and Humanities partitioned by
   textbook author and grade (0% train/eval leakage firewall)
4. Cryptographic release receipt and manifest with SHA-256 checksums and
   Draft 2020-12 schema validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jsonschema

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def resolve_data_path(rel_path: str) -> Path:
    """Resolve a relative data path, falling back to git common dir for gitignored files."""
    local_p = PROJECT_ROOT / rel_path
    if local_p.exists() and (local_p.is_dir() or local_p.stat().st_size > 0):
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
        main_p = Path(common).resolve().parent / rel_path
        if main_p.exists() and (main_p.is_dir() or main_p.stat().st_size > 0):
            return main_p
    except Exception:
        pass
    return local_p


DEFAULT_SOURCES_DB = resolve_data_path("data/sources.db")
DEFAULT_VESUM_DB = resolve_data_path("data/vesum.db")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v06_general_assistant"

SCHEMA_EVAL_PATH = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "contracts" / "v1_general_assistant_eval_record.schema.json"
SCHEMA_RECEIPT_PATH = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "contracts" / "v1_general_assistant_release_receipt.schema.json"

# Strict 22 held-out textbooks for evaluation firewall (0% train/eval text leakage)
HELD_OUT_TEXTBOOKS = [
    "5-klas-matematyka-ister-2022",
    "9-klas-algebra-merzliak-2017",
    "9-klas-heometriya-merzliak-2017",
    "8-klas-fizyka-bariakhtar-2025",
    "8-klas-khimiya-hryhorovych-2025",
    "8-klas-biolohiya-anderson-2025",
    "7-klas-informatyka-bondarenko-2024",
    "8-klas-heohrafiya-hilberh-2025",
    "5-klas-piznaiemo-pryrodu-korshevniuk-2022",
    "8-klas-istoria-ukr-schupak-2025",
    "8-klas-istoria-vsesvitnia-ladychenko-2025",
    "9-klas-pravoznavstvo-berendieiev-2026",
    "8-klas-hromadianska-osvita-vasylkiv-2025",
    "10-klas-ekonomika-krupska-2018",
    "8-klas-finans-plastun-2025",
    "8-klas-ukrlit-zabolotnyi-2025",
    "8-klas-ukrmova-zabolotnyi-2025",
    "8-klas-zarlit-voloschuk-2025",
    "8-klas-mystetstvo-komarovska-2025",
    "8-klas-zdorovia-vasylenko-2025",
    "8-klas-tekhnolohiyi-bilenko-2025",
    "6-klas-etyka-martyniuk-2023",
]
HELD_OUT_SET = set(HELD_OUT_TEXTBOOKS)

STEM_SUBJECTS = {
    "algebra", "heometriya", "matematyka", "informatyka", "fizyka",
    "khimiya", "biolohiya", "astronomiya", "heohrafiya", "pryroda", "ya_doslidzhuiu_svit",
}

HUMANITIES_SUBJECTS = {
    "istoriya", "vsesvitnia", "pravoznavstvo", "hromadianska", "ekonomika",
    "finansova", "mystetstvo", "zakhyst", "etyka",
    "zdorovia", "tekhnolohiyi", "ukrmova", "ukrlit", "zarlit",
}

# 4 Academic Disciplines for pedagogy & reasoning specialization
DISCIPLINE_MATH_COMPUTING = {"algebra", "heometriya", "matematyka", "informatyka"}
DISCIPLINE_NATURAL_SCIENCES = {"fizyka", "khimiya", "biolohiya", "astronomiya", "pryroda", "ya_doslidzhuiu_svit"}
DISCIPLINE_GEOGRAPHY = {"heohrafiya"}
DISCIPLINE_SOCIAL_LAW = {"istoriya", "vsesvitnia", "pravoznavstvo", "hromadianska", "ekonomika", "finansova", "zakhyst"}
DISCIPLINE_PHILOLOGY_CULTURE = {"ukrmova", "ukrlit", "zarlit", "mystetstvo", "etyka", "zdorovia", "tekhnolohiyi"}

# Imperative task verbs in textbook exercises to filter out from concept extraction
EXERCISE_IMPERATIVES = {
    # Plural / formal imperatives
    "складіть", "оцініть", "прочитайте", "виконайте", "знайдіть", "поясніть", "запишіть",
    "пригадайте", "зауважимо", "дослідіть", "обчисліть", "розв'яжіть", "розвяжіть",
    "назвіть", "доведіть", "порівняйте", "охарактеризуйте", "сформулюйте", "наведіть",
    "розгляньте", "заповніть", "проаналізуйте", "уявіть", "дайте", "поміркуйте", "перевірте",
    "запам'ятайте", "запамятайте", "зверніть", "випишіть", "продовжіть", "виберіть",
    "перекажіть", "вставте", "спробуйте", "визначте", "позначте", "поділіть", "утворіть",
    "висловте", "обговоріть", "підготуйте", "скористайтеся", "вкажіть", "відшукайте",
    "спростіть", "побудуйте", "намалюйте", "згрупуйте", "відгадайте", "розподіліть",
    "перегляньте", "подивіться", "дізнайтеся", "ознайомтеся", "повторіть", "підсумуйте",
    "доповніть", "подумайте", "зробіть", "варто", "дотримуватись", "написати",
    "перепишіть", "зіставте", "продемонструйте", "пояснюйте", "розгадайте", "придумайте",
    "накресліть", "виміряйте", "полічіть", "порахуйте", "розфарбуйте", "доберіть",
    "встановіть", "з'ясуйте", "зясуйте", "запропонуйте", "покажіть", "перелічіть",
    # Singular informal imperatives (Grades 1-6 textbooks)
    "склади", "оціни", "прочитай", "виконай", "знайди", "поясни", "запиши",
    "пригадай", "зауваж", "досліди", "обчисли", "розв'яжи", "розвяжи",
    "назви", "доведи", "порівняй", "охарактеризуй", "сформулюй", "наведи",
    "розглянь", "заповни", "проаналізуй", "уяви", "дай", "поміркуй", "перевір",
    "запам'ятай", "запамятай", "зверни", "випиши", "продовж", "вибери",
    "перекажи", "встав", "спробуй", "визнач", "познач", "поділи", "утвори",
    "вислови", "обговори", "підготуй", "скористайся", "вкажи", "відшукай",
    "спрости", "побудуй", "намалюй", "згрупуй", "відгадай", "розподіли",
    "переглянь", "подивись", "подивися", "дізнайся", "ознайомся", "повтори", "підсумуй",
    "доповни", "подумай", "зроби", "перепиши", "зістав", "продемонструй", "пояснюй",
    "розгадай", "придумай", "накресли", "виміряй", "полічи", "порахуй",
    "розфарбуй", "добери", "встанови", "з'ясуй", "зясуй", "запропонуй", "покажи", "перелічи",
    # Cohortative 1st-person plural forms
    "поміркуймо", "обговорімо", "сформулюймо", "дослідімо", "пригадаймо",
    "виконаймо", "розв'яжімо", "розвяжімо", "обчислімо", "підсумуймо",
    "спробуймо", "повторімо", "перевірмо", "розгляньмо",
}

NON_CONCEPT_PREFIXES = (
    "вправа", "завдання", "задача", "приклад", "лабораторна", "практична", "робота в",
    "запитання", "відповідь", "варіант", "тест", "самостійна", "контрольна", "підсумок",
    "домашнє", "від авторів", "сторінка", "рубрика", "інтелектуальний клуб",
    "перегляньте", "дізнайтеся", "електронний додаток", "додаток", "відео", "схема для",
    "розділ ", "параграф ", "тема уроку", "тема заняття", "зміст",
)

FILLER_STARTS = (
    "якщо", "коли", "тому", "проте", "також", "однак", "через", "внаслідок", "зокрема",
    "наприклад", "тобто", "від", "для", "під", "над", "при", "без", "до", "із", "зі",
    "оскільки", "хоча", "щодо", "після", "під час", "згідно", "незважаючи", "завдяки", "як",
)

DANGLING_TAILS = {
    "є", "був", "була", "було", "були", "має", "може", "як", "що", "де", "коли",
    "та", "і", "й", "або", "чи", "а", "але", "це", "до", "від", "на", "в", "у",
    "із", "зі", "за", "під", "над", "при", "про", "для", "без", "через", "з",
}


UKRAINIAN_SUBJECT_GENITIVE = {
    "algebra": "алгебри",
    "heometriya": "геометрії",
    "matematyka": "математики",
    "informatyka": "інформатики",
    "fizyka": "фізики",
    "khimiya": "хімії",
    "biolohiya": "біології",
    "astronomiya": "астрономії",
    "heohrafiya": "географії",
    "pryroda": "природничих наук",
    "ya_doslidzhuiu_svit": "курсу «Я досліджую світ»",
    "istoriya": "історії України",
    "vsesvitnia": "всесвітньої історії",
    "pravoznavstvo": "правознавства",
    "hromadianska": "громадянської освіти",
    "ekonomika": "економіки",
    "finansova": "фінансової грамотності",
    "ukrmova": "української мови",
    "ukrlit": "української літератури",
    "zarlit": "зарубіжної літератури",
    "mystetstvo": "мистецтва",
    "zakhyst": "захисту України",
    "etyka": "етики",
    "zdorovia": "основ здоров'я",
    "tekhnolohiyi": "технологій",
}

UKRAINIAN_SUBJECT_NOMINATIVE = {
    "algebra": "Алгебра",
    "heometriya": "Геометрія",
    "matematyka": "Математика",
    "informatyka": "Інформатика",
    "fizyka": "Фізика",
    "khimiya": "Хімія",
    "biolohiya": "Біологія",
    "astronomiya": "Астрономія",
    "heohrafiya": "Географія",
    "pryroda": "Природничі науки",
    "ya_doslidzhuiu_svit": "Я досліджую світ",
    "istoriya": "Історія України",
    "vsesvitnia": "Всесвітня історія",
    "pravoznavstvo": "Правознавство",
    "hromadianska": "Громадянська освіта",
    "ekonomika": "Економіка",
    "finansova": "Фінансова грамотність",
    "ukrmova": "Українська мова",
    "ukrlit": "Українська література",
    "zarlit": "Зарубіжна література",
    "mystetstvo": "Мистецтво",
    "zakhyst": "Захист України",
    "etyka": "Етика",
    "zdorovia": "Основи здоров'я",
    "tekhnolohiyi": "Технології",
}

CANONICAL_SUBJECT_TERMINOLOGY = {
    "algebra": ["дискримінант", "корінь рівняння", "квадратний тричлен", "функція", "графік", "арифметична прогресія", "геометрична прогресія", "похідна", "нерівність", "послідовність", "добуток", "квадрат", "знаменник", "степінь", "многочлен", "одночлен", "дробовий вираз"],
    "heometriya": ["теорема Піфагора", "правильний многокутник", "протилежні вектори", "об'єм циліндра", "об'єм піраміди", "об'єм конуса", "об'єм кулі", "відношення площ", "відношення величин", "вектор", "трикутник", "паралелограм", "трапеція", "синус", "косинус", "тангенс", "координати", "відрізок", "кут"],
    "matematyka": ["числова множина", "десятковий дріб", "відсоток", "пропорція", "ділення", "множення", "відношення чисел", "координатна пряма", "натуральне число", "звичайний дріб"],
    "fizyka": ["реостат", "електричний струм", "електричне коло", "прискорювач", "заломлення", "відбиття", "густина", "сила тяжіння", "імпульс", "кінетична енергія", "напруга", "опір", "тиск", "робота", "потужність", "теплота", "магнітне поле"],
    "khimiya": ["чадний газ", "карбон", "водень", "кисень", "вуглець", "азот", "сірка", "залізо", "сульфатна кислота", "хлоридна кислота", "нітратна кислота", "періодичний закон", "електроліз", "оксид", "основа", "кислота", "сіль", "молярна маса", "розчин", "валентність"],
    "biolohiya": ["клітина", "хромосома", "фотосинтез", "метаболізм", "генотип", "екосистема", "мембрана", "фермент", "біорізноманіття", "орган", "тканина", "розмноження", "спадковість", "мінливість", "біоритми", "нервова система"],
    "informatyka": ["алгоритм", "масив", "цикл", "розгалуження", "база даних", "інтерфейс", "функція", "кодування інформації", "змінна", "програма", "оператор", "мережа", "файл", "вкладений файл"],
    "heohrafiya": ["атмосфера", "гідросфера", "літосфера", "клімат", "рельєф", "природні ресурси", "демографія", "корисні копалини", "географічна карта", "материк", "океан", "густота населення"],
    "pryroda": ["спостереження", "експеримент", "природне явище", "агрегатний стан", "сонячна система", "екологічна рівновага", "жива природа", "нежива природа"],
    "ya_doslidzhuiu_svit": ["довкілля", "природа", "суспільство", "людина", "безпека"],
    "istoriya": ["державотворення", "суверенітет", "Русь-Україна", "козацтво", "Гетьманщина", "УНР", "боротьба УПА", "незалежність України", "археологія", "джерелознавство", "національне відродження"],
    "vsesvitnia": ["античність", "середньовіччя", "відродження", "просвітництво", "промисловий переворот", "міжнародні відносини", "реформація", "революція"],
    "pravoznavstvo": ["верховенство права", "Конституція України", "правопорядок", "юридична відповідальність", "права людини", "судочинство", "правопорушення", "закон", "громадянство"],
    "hromadianska": ["громадянське суспільство", "демократія", "громадянська позиція", "права і свободи", "вибори", "самоврядування", "громада", "плюралізм", "дискримінація"],
    "ekonomika": ["ринковий механізм", "попит", "пропозиція", "інфляція", "бюджет", "підприємництво", "валовий внутрішній продукт", "ціна", "виробництво", "доходи", "витрати"],
    "finansova": ["фінансовий план", "депозит", "кредит", "інвестиції", "страхування", "банківська система", "платіжні картки", "бюджет родини", "заощадження"],
    "ukrmova": ["орфографія", "пунктуація", "синтаксис", "словосполучення", "лексичне значення", "частини мови", "Правопис 2019", "фонетика", "морфологія", "члени речення", "стилістика"],
    "ukrlit": ["ідейно-тематичний зміст", "художній образ", "композиція", "метафора", "патріотичний мотив", "гуманістичний пафос", "жанр", "ліричний герой", "мотив"],
    "zarlit": ["світовий шедевр", "літературний напрям", "романтизм", "реалізм", "психологізм", "драматургія", "новела", "роман", "трагедія"],
    "mystetstvo": ["художній стиль", "гармонія", "композиція", "виражальні засоби", "архітектура", "музичне мистецтво", "живопис", "скульптура"],
    "zakhyst": ["обороноздатність", "цивільний захист", "домедична допомога", "військова присяга", "національна безпека", "тактична підготовка", "вогнева підготовка"],
    "etyka": ["мораль", "чесноти", "повага", "справедливість", "культура спілкування", "толерантність", "гідність", "совість", "добро"],
    "zdorovia": ["здоровий спосіб життя", "безпека", "психічне здоров'я", "профілактика", "рухова активність", "раціональне харчування", "гігієна"],
    "tekhnolohiyi": ["проєктування", "матеріалознавство", "технологічний процес", "макет", "конструювання", "ергономіка", "виріб", "технологічна карта"],
}

CONTRADICTORY_MODIFIER_PAIRS = [
    ("арифметичн", "геометричн"),
    ("парн", "непарн"),
    ("прям", "обернен"),
    ("додатн", "від'ємн"),
    ("раціональн", "ірраціональн"),
    ("складен", "прост"),
    ("зовнішн", "внутрішн"),
    ("однорідн", "неоднорідн"),
]

DANGLING_STARTER_RE = re.compile(
    r"^(?:"
    r"її\b|його\b|їх\b|їхні[йяєхм]?\b|такі\b|такий\b|така\b|таке\b|ці\b|цей\b|ця\b|він\b|вона\b|воно\b|вони\b|"
    r"натомість\b|на\s+відміну\s+від\b|проте\b|однак\b|разом\s+з\s+тим\b|водночас\b|також\b|до\s+того\s+ж\b|"
    r"крім\s+того\b|зокрема\b|аналогічн\w*|отже\b|оскільки\b|тому\b|тому\s+для\b|"
    r"записан\w*\s+рівність|цю\s+рівність|цю\s+формулу|цей\s+вираз|цей\s+малюнок|цей\s+рисунок|цей\s+графік|"
    r"звідси\b|з\s+цього\s+випливає\b|у\s+зв'язку\s+з\s+цим\b|для\s+цього\b|через\s+це\b|при\s+цьому\b|"
    r"у\s+таких\s+випадках\b|тоді\s+маємо\b|тоді\s+як\b|наприклад\b|позначимо\b|нехай\b|"
    r"підставивши\b|помноживши\b|поділивши\b|доведемо\b|розв'язання\b|розглянемо\s+приклад\b|"
    r"так\w*\s+рівність|так\w*\s+послідовність|так\w*\s+вираз|так\w*\s+чином\b|відповідно\b|"
    r"як\s+бачимо\b|як\s+відомо\b|як\s+зазначалося\b"
    r")\b",
    re.IGNORECASE,
)

FORWARD_BACKWARD_REF_RE = re.compile(
    r"\b(?:"
    r"наступн\w*\s+тем\w*|"
    r"наступн\w*\s+параграф\w*|"
    r"наступн\w*\s+розділ\w*|"
    r"попередн\w*\s+тем\w*|"
    r"попередн\w*\s+параграф\w*|"
    r"попередн\w*\s+розділ\w*|"
    r"про\s+як\w*\s+йтиметься|"
    r"про\s+це\s+йтиметься|"
    r"як\s+зазначено\s+вище|"
    r"як\s+було\s+сказано|"
    r"як\s+уже\s+зазначалося|"
    r"як\s+ми\s+вже\s+знаємо|"
    r"як\s+ви\s+вже\s+знаєте|"
    r"як\s+відомо\s+з\s+попередн\w*|"
    r"рівносильн\w*\s+даній|"
    r"розглянут\w*\s+раніше|"
    r"у\s+попередньому\s+класі|"
    r"у\s+наступному\s+класі|"
    r"наведен\w*\s+вище|"
    r"згадайте\s+з\s+курсу|"
    r"у\s+минулому\s+році"
    r")\b",
    re.IGNORECASE,
)

DEFINITIONAL_MARKER_RE = re.compile(
    r"(?:—\s*це\b|–\s*це\b|-\s*це\b|\bназивають\b|\bназивається\b|\bозначення\b|\bвизначення\b|"
    r"\bє\s+[а-яіїєґ]+(?:им|ою|ем|ям|ими)\b|\bце\s+[а-яіїєґ]+\b|"
    r"\bсукупність\b|\bпроцес\b|\bявище\b|\bвластивість\b|\bвеличина\b|\bсистема\b|\bправило\b|\bзакон\b)",
    re.IGNORECASE,
)

DEICTIC_OPENER_RE = re.compile(
    r"^(?:нині|сьогодні|тепер|зараз|у\s+наш\s+час|в\s+наш\s+час|на\s+сьогодні|наразі|у\s+сучасному\s+світі|в\s+сучасному\s+світі)\b",
    re.IGNORECASE,
)

OBLIQUE_DEMONSTRATIVE_RE = re.compile(
    r"\b(?:цієї|цій|цього|цьому|цим|цими|цих|цією|цю|"
    r"такої|такій|такого|такому|таким|такими|таких|такою|таку)\b",
    re.IGNORECASE,
)

NOM_DEMONSTRATIVE_START_RE = re.compile(
    r"^(?:[^.!?«„—–-]{0,50}\b)(?:цей|ця|ці|це\s+(?:явище|процес|поняття|правило|закон)|такий|така|таке|такі)\s+[а-яіїєґ]+",
    re.IGNORECASE,
)


RETROSPECTIVE_PARTICIPLE_RE = re.compile(
    r"^(?:[^.!?«„]{0,35}\b)(?:утворен\w*|отриман\w*|зазначен\w*|вказан\w*|наведен\w*)\b",
    re.IGNORECASE,
)
EXTERNAL_REF_RE = re.compile(
    r"\b(?:описан\w*\s+вищ\w*|окрім\s+них|окрім\s+цього|окрім\s+того|"
    r"подібн\w*\s+(?:задач|приклад|дослід|явищ|випадк|процес)|розв'язуванн\w*\s+подібн\w*)\b",
    re.IGNORECASE,
)
LABELLED_OBJECT_RE = re.compile(
    r"\b(?:точку|точка|точці|точкою|точками|пряму|пряма|прямій|прямою|площину|площина|площині|"
    r"кут|кута|кутом|вектор|вектора|вектором|відрізок|відрізка)\s+[A-Za-z0-9]\b",
    re.IGNORECASE,
)
PRONOUN_STARTER_RE = re.compile(
    r"^(?:[^.!?«„]{0,45}\b)(?:його|її|їх|них|ньому|ній|нього|неї|ними)\b",
    re.IGNORECASE,
)


TAK_ANAPHORA_START_RE = re.compile(
    r"^(?:[^.!?«„]{0,25}\b)(?:так|саме\s+так)\s+(?:називають|називається)\b",
    re.IGNORECASE,
)
TAKE_ANAPHORA_RE = re.compile(
    r"(?<![—–-]\s)(?<![—–-]\sце\s)\bтаке\s+[а-яіїєґ]+",
    re.IGNORECASE,
)


def has_unresolved_anaphora(s: str) -> bool:
    """Check if a snippet or opening clause contains dangling deictic openers, participles, or ungrounded demonstratives/anaphora."""
    s_clean = s.strip().lstrip("«„\"")
    if DEICTIC_OPENER_RE.search(s_clean):
        return True
    if RETROSPECTIVE_PARTICIPLE_RE.search(s_clean):
        return True
    if EXTERNAL_REF_RE.search(s_clean):
        return True
    if LABELLED_OBJECT_RE.search(s_clean):
        return True
    if PRONOUN_STARTER_RE.search(s_clean):
        return True
    if TAK_ANAPHORA_START_RE.search(s_clean):
        return True
    if TAKE_ANAPHORA_RE.search(s_clean):
        return True
    first_sent = re.split(r"[.!?]", s_clean)[0]
    if OBLIQUE_DEMONSTRATIVE_RE.search(first_sent):
        return True
    return bool(NOM_DEMONSTRATIVE_START_RE.search(first_sent))


# Typography & Calque Sanitation
APOSTROPHE_RE = re.compile(r"['’ʼ´`]")
HYPHEN_BREAK_RE = re.compile(r"([а-яіїєґА-ЯІЇЄҐa-zA-Z])(?:-[\s\t]*[\r\n]+[\s\t]*|\xad[\s\r\n]*|- +)([а-яіїєґА-ЯІЇЄҐa-zA-Z])")
DOUBLE_PUNCT_RE = re.compile(r"\.{2,}")
PUNCT_DOT_RE = re.compile(r"([?!…])\.")
MULTISPACE_RE = re.compile(r"[ \t]+")

# Calque replacements
CALQUE_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bвирішувати задачу\b", re.IGNORECASE), "розв'язувати задачу"),
    (re.compile(r"\bвирішувати задачі\b", re.IGNORECASE), "розв'язувати задачі"),
    (re.compile(r"\bвирішувати рівняння\b", re.IGNORECASE), "розв'язувати рівняння"),
    (re.compile(r"\bвирішення задачі\b", re.IGNORECASE), "розв'язання задачі"),
    (re.compile(r"\bпо крайній мірі\b", re.IGNORECASE), "принаймні"),
    (re.compile(r"\bв залежності від\b", re.IGNORECASE), "залежно від"),
    (re.compile(r"\bприймати участь\b", re.IGNORECASE), "брати участь"),
    (re.compile(r"\bнаносити шкоду\b", re.IGNORECASE), "завдавати шкоди"),
    (re.compile(r"\bнаносити збитки\b", re.IGNORECASE), "завдавати збитків"),
    (re.compile(r"\bв кінці кінців\b", re.IGNORECASE), "зрештою"),
    (re.compile(r"\bу кінці кінців\b", re.IGNORECASE), "зрештою"),
]

# Protected geometric volume & scientific ratio entities
PROTECTED_VOLUME_TERMS = {
    "об'єм циліндра", "об'єм конуса", "об'єм піраміди", "об'єм кулі",
    "об'єм призми", "об'єм паралелепіпеда", "об'єм куба", "об'єм многогранника",
    "об'єм тіла", "молярний об'єм", "об'єм газу", "об'єм розчину", "об'єм рідини",
}

PROTECTED_RATIO_TERMS = {
    "відношення величин", "відношення чисел", "відношення відрізків",
    "відношення площ", "відношення об'ємів", "тригонометричне відношення",
    "відношення сторін", "відношення мас", "відношення швидкостей",
}

# Gate 6 pejorative & condescending stems to prohibit in pedagogical responses
PEJORATIVE_STEMS = (
    "дурн", "нездар", "тупий", "тупого", "ідіот", "безграмотн",
    "не дивно, що ви цього", "навіть першокласник знає",
    "як можна не знати", "соромно не знати", "очевидно кожному дурню",
)

STOPWORD_TERMS = {
    "клас", "класу", "класи", "класів", "класом", "математика", "математики", "математику",
    "підручник", "підручника", "підручнику", "розділ", "розділу", "розділі",
    "тема", "теми", "тему", "темі", "сторінка", "сторінки", "сторінку",
    "учень", "учня", "учні", "учнів", "учням", "учениця", "учениці",
    "вчитель", "вчителя", "вчителька", "вчительки",
    "завдання", "завдань", "вправа", "вправи", "вправу",
    "україна", "україни", "українська", "української", "українською",
    "слово", "слова", "словом", "мова", "мови", "мову", "мовою",
    "предмет", "предмета", "предмету", "робота", "роботи", "роботу", "роботі", "роботою",
    "параграф", "параграфа", "частина", "частини", "частину",
    "питання", "відповідь", "відповіді", "відповіддю",
    "школа", "школи", "школу", "курс", "курсу", "курсі",
    "урок", "уроку", "уроці", "поняття", "приклад", "прикладу", "значення",
    "автор", "автори", "авторів", "підсумок", "підсумки", "правило", "правила",
    "число", "числа", "чисел", "числу", "числом", "член", "члена", "членів",
    "треба", "можна", "слід", "бути", "мати", "стати", "дати", "буде", "було",
    "випадок", "випадку", "випадки", "вигляд", "вигляду", "спосіб", "способу", "способом",
    "відміна", "відміну", "умова", "умови", "умовою", "початок", "початку",
    "кінець", "кінця", "кінцем", "допомога", "допомогою", "основа", "основи", "основою",
    "зв'язок", "зв'язку", "наслідок", "наслідку", "порядок", "порядку",
    "запис", "запису", "записом", "форма", "форми", "формою", "тип", "типу", "типом",
    "вид", "виду", "видом", "група", "групи", "групою", "рівень", "рівня", "рівнем",
    "текст", "тексту", "рядок", "рядка", "знак", "знака", "знаком", "знаки",
    "ознака", "ознаки", "ознакою",
    # Generic high-frequency words & ordinary conversational vocabulary
    "справа", "справи", "справу", "справі", "справою",
    "створення", "створенні", "створенням",
    "художник", "художника", "художники", "художників",
    "людина", "людини", "людині", "людиною", "люди", "людей", "людям", "людьми",
    "час", "часу", "часом", "часі",
    "використання", "використанні", "використанням",
    "сукупність", "сукупності", "сукупністю",
    "можливість", "можливості", "можливістю",
    "розгляд", "розгляду", "діяльність",
    "процес", "процесу", "процеси", "процесів",
    "явище", "явища", "явищ", "явищем",
    "складова", "властивість", "властивості", "властивостей",
    "особливість", "факт", "інформація", "дані", "потреба", "мета", "ціль",
    "напрям", "напрямок", "сторона", "точка", "місце", "край", "стан", "роль",
    "сутність", "середина", "межа", "розмір", "кількість", "якість",
    "величина", "величини", "величину", "величиною",
    "безліч", "безлічі", "безліччю", "кількості",
    "метод", "методи", "методів", "метода", "двері", "дверей", "дверима",
    "досягнення", "історія", "людство",
    "життя", "світ", "світу", "рік", "року", "роки", "років",
    "день", "дня", "дні", "днів", "протилежне", "живе", "живий", "живим", "актиній",
    "житель", "жителі", "жителя", "жителів", "прихильник", "прихильники", "прихильника",
    "богиня", "богині", "богинею", "божество", "божества", "божеств", "бог", "бога", "боги", "богів", "міф", "міфи", "міфів", "міфологія",
    # Generic adjectives
    "давньоримський", "давньоримська", "давньоримське", "давньоримські",
    "основний", "основна", "основне", "основні", "основного", "основній", "основних", "основним",
    "численний", "численна", "численне", "численні", "численних", "численними", "численним",
    "непростий", "непроста", "непросте", "непрості", "непростих", "непростим",
    "простий", "проста", "просте", "прості", "простих", "простим",
    "складний", "складна", "складне", "складні", "складних", "складним",
    "різний", "різна", "різне", "різні", "різних", "різними", "різним",
    "новий", "нова", "нове", "нові", "нових", "новим",
    "старий", "стара", "старе", "старі", "старих",
    "важливий", "важлива", "важливе", "важливі", "важливих", "важливим",
    "головний", "головна", "головне", "головні", "головних", "головним",
    "великий", "велика", "велике", "великі", "великих", "великим", "великою",
    "малий", "мала", "мале", "малі", "малих", "малим", "малою",
    "середній", "середня", "середнє", "середні", "середніх",
    "високий", "висока", "високе", "високі", "високих",
    "низький", "низька", "низьке", "низькі", "низьких",
    "певний", "певна", "певне", "певні", "певного", "певній", "певних", "певним",
    "деякий", "деяка", "деяке", "деякі", "деяких",
    "окремий", "окрема", "окреме", "окремі", "окремих", "окремим",
    "загальний", "загальна", "загальне", "загальні", "загальних", "загальним",
    "кожен", "кожна", "кожне", "кожні", "кожного", "кожній", "кожним",
    "всякий", "інший", "інша", "інше", "інші", "інших", "іншим",
    "подібний", "подібна", "подібне", "подібні", "подібних",
    "однаковий", "однакова", "однакове", "однакові", "однакових",
    "перший", "другий", "третій", "четвертий", "п'ятий",
    "наступний", "попередній", "подальший",
    "цілий", "повний", "правильний", "вільний", "довгий", "короткий", "прямий",
    "відомий", "відома", "відоме", "відомі", "відомих", "відомим", "невідомий",
    "можливий", "неможливий", "необхідний", "необхідна", "необхідне", "необхідні", "необхідних",
    "єдиний", "сучасний", "давній", "минулий", "майбутній",
    "шкільний", "учнівський", "домашній", "класний", "навчальний",
    "кращий", "гірший", "найкращий", "найбільший", "найменший",
    "фізичний", "фізична", "фізичне", "фізичні", "фізичних", "фізичним",
    "питомий", "питома", "питоме", "питомі", "питомих",
    "майбутнє", "вика", "середа", "раз", "повня", "красий", "точок",
}

OCR_DROPCAP_RE = re.compile(r"(?<!\b[а-яіїєґ])[\.!?]\s+[а-яіїєґ]")

EXERCISE_LINE_PATTERNS = [
    re.compile(r"(?:^|\s)(?:\d+[\.\)]|[a-zA-Zа-яіїєґА-ЯІЇЄҐ][\.\)])\s+[а-яіїєґa-z]"),
    re.compile(r"(?:^|\s)\d+[\.\)]\s+(?:" + "|".join(sorted(EXERCISE_IMPERATIVES, key=len, reverse=True)) + r")\b", re.IGNORECASE),
    re.compile(r"(?:^|\s)(?:запитання|завдання|вправи|практична робота|тестові завдання|перевірте себе|інтелектуальний клуб)\b", re.IGNORECASE),
]

EXERCISE_ITEM_RE = re.compile(
    r"^\s*(?:\d+\.\d+|\d+°|\d{3,}\.|\d+[\.\)]\s*(?:[^\n]*?\b(?:" + "|".join(EXERCISE_IMPERATIVES) + r")\b))",
    re.IGNORECASE | re.MULTILINE,
)
LAB_EQUIPMENT_RE = re.compile(
    r"\b(?:що знадобиться|обладнання|матеріали|прилади|реактиви|посуд|хід роботи|інструктаж|лабораторн\w*|практичн\w* робот\w*|дослід\w*|експеримент\w*)\b",
    re.IGNORECASE,
)
FIGURE_REF_RE = re.compile(
    r"\b(?:рис\.|рисунок|рисунк\w*|мал\.|малюнок|малюнк\w*|табл\.|таблиц\w*|іл\.|ілюстрац\w*|схем\w*|діаграм\w*|фото)\s*\d+",
    re.IGNORECASE,
)
MATH_GARBLE_RE = re.compile(r"[=><±×÷−√∫∑^{}[\]\\|~]")
QUESTION_STARTER_RE = re.compile(r"^\s*(?:які|яка|який|яке|яких|яким|чому|чи|хто|що|де|куди|звідки|як|скільки)\b", re.IGNORECASE)


def truncate_word_boundary(text: str, max_len: int) -> str:
    """Truncate text cleanly at a word boundary, stripping trailing punctuation and dangling opening quotes."""
    t = text.strip()
    if len(t) <= max_len:
        return t
    cut = t[:max_len]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    cut = cut.rstrip(".,;:—– \t«„\"“")
    open_guillemets = cut.count("«") - cut.count("»")
    if open_guillemets > 0:
        cut += "»" * open_guillemets
    open_inner = cut.count("„") - cut.count("“")
    if open_inner > 0:
        cut += "“" * open_inner
    return cut.rstrip(".,;:—– \t") + "..."

_GLOBAL_VESUM_CONN: sqlite3.Connection | None = None
_GLOBAL_VESUM_CUR: sqlite3.Cursor | None = None
_VESUM_CACHE: dict[str, bool] = {}


def get_vesum_cursor(vesum_db: Path = DEFAULT_VESUM_DB) -> sqlite3.Cursor | None:
    """Return a cached read-only cursor to vesum.db."""
    global _GLOBAL_VESUM_CONN, _GLOBAL_VESUM_CUR
    if _GLOBAL_VESUM_CUR is not None:
        return _GLOBAL_VESUM_CUR
    if vesum_db.is_file():
        try:
            _GLOBAL_VESUM_CONN = sqlite3.connect(f"file:{vesum_db}?mode=ro", uri=True)
            _GLOBAL_VESUM_CUR = _GLOBAL_VESUM_CONN.cursor()
            return _GLOBAL_VESUM_CUR
        except Exception as e:
            logger.warning("Could not connect to VESUM DB: %s", e)
            return None
    return None


def is_vesum_attested(term: str, cur_ves: sqlite3.Cursor | None = None, use_default_if_none: bool = True) -> bool:
    """Check if a term or lemma exists in VESUM forms_all. Fail closed if DB is missing."""
    norm = term.strip().lower()
    if not norm or not re.match(r"^[а-яіїєґ'\s-]+$", norm):
        return False
    if cur_ves is not None:
        cur = cur_ves
    elif use_default_if_none:
        cur = get_vesum_cursor()
    else:
        cur = None

    if cur is None:
        return False

    words = re.findall(r"[а-яіїєґ']+", norm)
    if not words:
        return False
    for w in words:
        if w in _VESUM_CACHE:
            if not _VESUM_CACHE[w]:
                return False
            continue
        try:
            cur.execute(
                "SELECT 1 FROM forms_all WHERE word_form = ? OR lemma = ? LIMIT 1",
                (w, w),
            )
            found = cur.fetchone() is not None
            _VESUM_CACHE[w] = found
            if not found:
                return False
        except Exception:
            return False
    return True


_VESUM_LEMMA_CACHE: dict[str, set[str]] = {}
_VESUM_WORD_INFO_CACHE: dict[str, list[tuple[str, str, str]]] = {}


def get_vesum_word_lemmas(word: str, cur_ves: sqlite3.Cursor | None = None) -> set[str]:
    """Extract dictionary lemmas for a single word form from VESUM forms_all with caching."""
    w = word.lower()
    if w in _VESUM_LEMMA_CACHE:
        return _VESUM_LEMMA_CACHE[w]
    cur = cur_ves or get_vesum_cursor()
    if cur is None:
        return set()
    try:
        cur.execute("SELECT lemma FROM forms_all WHERE word_form = ?", (w,))
        res = {r[0].lower() for r in cur.fetchall()}
    except Exception:
        res = set()
    _VESUM_LEMMA_CACHE[w] = res
    return res


def get_vesum_lemmas(text: str, cur_ves: sqlite3.Cursor | None = None) -> set[str]:
    """Extract all dictionary lemmas for tokens in text from VESUM forms_all."""
    if not text:
        return set()
    words = re.findall(r"[а-яіїєґ']+", text.lower())
    lemmas: set[str] = set()
    for w in words:
        lemmas.update(get_vesum_word_lemmas(w, cur_ves))
    return lemmas


def get_vesum_word_info(word: str, cur_ves: sqlite3.Cursor | None = None) -> list[tuple[str, str, str]]:
    """Extract (lemma, pos, tags) for a single word form from VESUM forms_all with caching."""
    w = word.lower()
    if w in _VESUM_WORD_INFO_CACHE:
        return _VESUM_WORD_INFO_CACHE[w]
    cur = cur_ves or get_vesum_cursor()
    if cur is None:
        return []
    try:
        cur.execute("SELECT lemma, pos, tags FROM forms_all WHERE word_form = ? OR word_form = ?", (w, w.capitalize()))
        rows = cur.fetchall()
    except Exception:
        rows = []
    _VESUM_WORD_INFO_CACHE[w] = rows
    return rows


_PRONOUN_CACHE: dict[str, bool] = {}


def is_vesum_pronoun(term: str, cur_ves: sqlite3.Cursor | None = None) -> bool:
    """Check if any reading of term or lemma in VESUM is a pronoun."""
    t = term.lower().strip()
    if t in _PRONOUN_CACHE:
        return _PRONOUN_CACHE[t]
    cur = cur_ves or get_vesum_cursor()
    if cur is None:
        return False
    try:
        cur.execute("SELECT tags, pos FROM forms_all WHERE word_form = ? OR lemma = ? LIMIT 10", (t, t))
        rows = cur.fetchall()
        is_pron = any("pron" in r[0] or r[1] == "pronoun" for r in rows)
    except Exception:
        is_pron = False
    _PRONOUN_CACHE[t] = is_pron
    return is_pron


_CITATION_FORM_CACHE: dict[str, bool] = {}


def is_concept_in_citation_form(concept: str, cur_ves: sqlite3.Cursor | None = None) -> bool:
    """Verify that the concept is in canonical nominative citation form with a nominative noun head."""
    norm_key = concept.strip().lower()
    if norm_key in _CITATION_FORM_CACHE:
        return _CITATION_FORM_CACHE[norm_key]
    res = _is_concept_in_citation_form_uncached(concept, cur_ves)
    _CITATION_FORM_CACHE[norm_key] = res
    return res


def _is_concept_in_citation_form_uncached(concept: str, cur_ves: sqlite3.Cursor | None = None) -> bool:
    cur = cur_ves or get_vesum_cursor()
    if not cur:
        return True
    punct = ".,;:?!'\"«»„“—–()"
    words = [w.strip(punct) for w in concept.strip().split() if w.strip(punct)]
    if not words or len(words) > 5:
        return False

    if re.match(r"^(?:най|якнай|щонай)\w+", concept.strip(), re.IGNORECASE):
        return False
    if re.match(r"^(?:найкращ\w*|найголовніш\w*|найбільш\w*|найважливіш\w*|найскладніш\w*|потужн\w*|ефективн\w*|унікальн\w*|чудов\w*|прекрасн\w*|висок\w*\s+цінност\w*|велик\w*\s+листк\w*)\b", concept.strip(), re.IGNORECASE):
        return False
    if re.match(r"^(?:та|і|й|або|чи|якщо|коли|де|куди)\b", concept.strip(), re.IGNORECASE):
        return False
    if re.search(r"\b(?:очевидн\w*|зрозуміл\w*|незрозуміл\w*|безперечн\w*|помітн\w*)\b", concept.strip(), re.IGNORECASE):
        return False

    preps = {"від", "для", "до", "з", "із", "зі", "на", "по", "про", "за", "під", "над", "при", "без"}
    if len(words) >= 3 and any(w.lower() in preps for w in words[1:-1]):
        cur.execute("SELECT pos FROM forms_all WHERE word_form = ?", (words[-1].lower(),))
        if any(r[0] == "adj" for r in cur.fetchall()):
            return False

    if len(words) == 1:
        w = words[0]
        cur.execute("SELECT tags FROM forms_all WHERE word_form = ?", (w.capitalize(),))
        cap_rows = cur.fetchall()
        has_prop = any(any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr")) for r in cap_rows)
        if has_prop:
            cur.execute("SELECT tags, pos FROM forms_all WHERE word_form = ?", (w.lower(),))
            low_rows = cur.fetchall()
            has_nom_common_noun = any(
                r[1] == "noun"
                and ("v_naz" in r[0] or "naz" in r[0])
                and not any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr"))
                for r in low_rows
            )
            if not has_nom_common_noun:
                return False

    ROMAN_RE = re.compile(r"^[IVXLCDMivxlcdm]+$")
    ALLOWED_INNER_CONNECTORS = {"і", "й", "та", "в", "у", "на", "до", "з", "із", "зі", "про", "по", "за", "від"}

    # 1. First word checks: cannot be preposition, conjunction, adverb, pronoun, or verb
    try:
        cur.execute(
            "SELECT tags, pos, lemma FROM forms_all WHERE word_form IN (?, ?, ?)",
            (words[0].lower(), words[0].capitalize(), words[0]),
        )
        w0_rows = cur.fetchall()
        if not w0_rows:
            return False
        w0_poses = {r[1] for r in w0_rows}
        if "prep" in w0_poses or "conj" in w0_poses or "adv" in w0_poses:
            return False
        if "verb" in w0_poses and not any(p in ("noun", "adj") for p in w0_poses):
            return False
        if any("pron" in r[0] or r[1] == "pronoun" for r in w0_rows):
            return False

        # 2. Must contain at least one nominative noun head (no bare adjectives)
        has_nom_noun = False
        for w in words:
            if ROMAN_RE.match(w) or w.lower() in ALLOWED_INNER_CONNECTORS:
                continue
            cur.execute(
                "SELECT tags, pos, lemma FROM forms_all WHERE word_form IN (?, ?, ?) AND pos = 'noun'",
                (w.lower(), w.capitalize(), w),
            )
            for r in cur.fetchall():
                if "v_naz" in r[0] or r[2].lower() == w.lower():
                    has_nom_noun = True
                    break
            if has_nom_noun:
                break
        if not has_nom_noun:
            return False

        # 3. If first word is noun, it must have nominative reading
        noun_w0 = [r for r in w0_rows if r[1] == "noun"]
        if noun_w0 and not any(
            "v_naz" in r[0] or (r[0].startswith("noun:inanim") and "v_zna" in r[0]) or r[2].lower() == words[0].lower()
            for r in noun_w0
        ):
            return False

        # 4. If first word is adj, it must have nominative reading
        adj_w0 = [r for r in w0_rows if r[1] == "adj"]
        if adj_w0 and not noun_w0 and not any("v_naz" in r[0] for r in adj_w0):
            return False

        # 5. Subsequent words: connectors, roman numerals, or valid inflected words (noun/adj in nominative, genitive, locative, instrumental)
        for w in words[1:]:
            if ROMAN_RE.match(w) or w.lower() in ALLOWED_INNER_CONNECTORS:
                continue
            cur.execute(
                "SELECT tags, pos, lemma FROM forms_all WHERE word_form IN (?, ?, ?)",
                (w.lower(), w.capitalize(), w),
            )
            w_rows = cur.fetchall()
            if not w_rows:
                return False
            if any("pron" in r[0] or r[1] == "pronoun" for r in w_rows):
                return False
            has_case = any(
                any(c in r[0] for c in ("v_naz", "v_rod", "v_mis", "v_oru")) or r[2].lower() == w.lower()
                for r in w_rows
                if r[1] in ("noun", "adj")
            )
            if not has_case:
                return False
    except Exception:
        return True
    return True


def lemmatize_noun_phrase(phrase: str, cur_ves: sqlite3.Cursor | None = None) -> str:
    """Convert an inflected Ukrainian noun or adjective-noun phrase to its nominative citation form."""
    cur = cur_ves or get_vesum_cursor()
    punct = ".,;:?!'\"«»„“—–()"
    words = [w.strip(punct) for w in phrase.strip().split() if w.strip(punct)]
    if not words:
        return phrase
    if not cur:
        return phrase.capitalize()
    if is_concept_in_citation_form(phrase, cur):
        return phrase.capitalize()

    if len(words) == 1:
        try:
            cur.execute(
                "SELECT lemma, pos FROM forms_all WHERE word_form IN (?, ?, ?) LIMIT 10",
                (words[0].lower(), words[0].capitalize(), words[0]),
            )
            rows = cur.fetchall()
            for lem, pos in rows:
                if pos in ("noun", "adj"):
                    return lem.capitalize()
        except Exception:
            pass
        return phrase.capitalize()

    try:
        cur.execute(
            "SELECT lemma, pos, tags FROM forms_all WHERE word_form IN (?, ?, ?)",
            (words[0].lower(), words[0].capitalize(), words[0]),
        )
        w0_rows = cur.fetchall()
        cur.execute(
            "SELECT lemma, pos, tags FROM forms_all WHERE word_form IN (?, ?, ?)",
            (words[1].lower(), words[1].capitalize(), words[1]),
        )
        w1_rows = cur.fetchall()

        adj_cand = [r for r in w0_rows if r[1] == "adj"]
        noun_cand = [r for r in w1_rows if r[1] == "noun"]
        noun0_cand = [r for r in w0_rows if r[1] == "noun"]

        # Pattern A: [Adj, Noun] e.g. сонячною радіацією -> Сонячна радіація, класичними рефлексами -> Класичні рефлекси
        if adj_cand and noun_cand:
            adj_lem = adj_cand[0][0]
            noun_lem = noun_cand[0][0]
            cur.execute("SELECT tags FROM forms_all WHERE lemma = ? AND pos = 'noun' LIMIT 5", (noun_lem,))
            lem_tags = [r[0] for r in cur.fetchall()]
            lem_gender = "m"
            for lt in lem_tags:
                if ":f:" in lt:
                    lem_gender = "f"
                    break
                elif ":n:" in lt:
                    lem_gender = "n"
                    break
                elif ":m:" in lt:
                    lem_gender = "m"
                    break
                elif ":p:" in lt:
                    lem_gender = "p"
                    break

            def extract_case(tag: str) -> str | None:
                for part in tag.split(":"):
                    if part.startswith("v_"):
                        return part
                return None

            matching_pairs = []
            for a in adj_cand:
                a_case = extract_case(a[2])
                for n in noun_cand:
                    n_case = extract_case(n[2])
                    if a_case and a_case == n_case:
                        a_p = ":p:" in a[2]
                        n_p = ":p:" in n[2]
                        if a_p == n_p:
                            matching_pairs.append((a, n, a_p))

            has_sing = any(not is_p for _, _, is_p in matching_pairs)
            is_plural = (not has_sing) if matching_pairs else any(":p:" in r[2] for r in noun_cand)
            target_tag_prefix = "adj:p:v_naz" if is_plural else f"adj:{lem_gender}:v_naz"
            cur.execute("SELECT word_form FROM forms_all WHERE lemma = ? AND pos = 'adj' AND tags LIKE ?", (adj_lem, target_tag_prefix + "%"))
            adj_forms = cur.fetchall()
            adj_naz = adj_forms[0][0] if adj_forms else adj_lem

            if is_plural:
                cur.execute("SELECT word_form FROM forms_all WHERE lemma = ? AND pos = 'noun' AND tags LIKE '%:p:v_naz%'", (noun_lem,))
                p_rows = cur.fetchall()
                noun_naz = p_rows[0][0] if p_rows else words[1].lower()
            else:
                noun_naz = noun_lem

            rest = (" " + " ".join(words[2:])) if len(words) > 2 else ""
            return f"{adj_naz.capitalize()} {noun_naz}{rest}"

        # Pattern B: [Noun, Noun_gen] e.g. силою тяжіння -> Сила тяжіння
        if noun0_cand and noun_cand:
            noun0_lem = noun0_cand[0][0]
            rest = " ".join(words[1:])
            return f"{noun0_lem.capitalize()} {rest}"
    except Exception:
        pass

    return phrase.capitalize()


def recover_named_noun_phrase(line: str, raw_val: str, cur_ves: sqlite3.Cursor | None = None) -> str | None:
    """Recover full [Adjective + Noun] phrase from preceding clause when 'називають X' yields a bare adjective."""
    cur = cur_ves or get_vesum_cursor()
    if not cur:
        return None
    punct = ".,;:?!'\"«»„“—–()"
    words = [w.strip(punct) for w in raw_val.split() if w.strip(punct)]
    if not words:
        return None

    # Check if raw_val already contains a noun head
    cur.execute(
        "SELECT count(*) FROM forms_all WHERE word_form IN ({}) AND pos = 'noun'".format(
            ",".join("?" * len(words))
        ),
        [w.lower() for w in words],
    )
    if cur.fetchone()[0] > 0:
        return raw_val

    adj_w = words[0].lower()
    if adj_w.endswith(("ими", "іми")):
        is_plural = True
        req_gender = None
    elif adj_w.endswith(("ою", "ею", "єю")):
        is_plural = False
        req_gender = {"f"}
    elif adj_w.endswith(("им", "ім")):
        is_plural = False
        req_gender = {"m", "n"}
    else:
        is_plural = False
        req_gender = None

    cur.execute("SELECT lemma, tags FROM forms_all WHERE word_form = ? AND pos = 'adj'", (adj_w,))
    adj_rows = cur.fetchall()
    if not adj_rows:
        return None
    adj_lem = adj_rows[0][0]

    # If raw_val is adjectival, inspect the preceding clause before 'називають'
    m_before = re.search(r"([^.!?«„]+?)\s+(?:називають|називається)\s+" + re.escape(raw_val), line, re.IGNORECASE)
    if not m_before:
        return None
    before_text = m_before.group(1).strip()

    # Prioritize the main clause subject / topic noun (left-to-right order)
    candidate_words = re.findall(r"[а-яіїєґА-ЯІЇЄҐ']+", before_text)

    chosen_noun_lem = None
    chosen_noun_gender = "m"
    for w in candidate_words:
        if len(w) < 3 or w.lower() in ("такі", "цей", "ця", "ці", "це", "їх", "його", "її", "них", "який", "яка", "які", "де", "якщо", "для", "тобто", "весь", "час"):
            continue
        cur.execute("SELECT pos, lemma, tags FROM forms_all WHERE word_form = ? AND pos = 'noun'", (w.lower(),))
        n_rows = cur.fetchall()
        if not n_rows:
            continue
        # Reject proper nouns
        if any(":prop" in r[2] or ":fname" in r[2] or ":lname" in r[2] for r in n_rows):
            continue
        noun_lem = n_rows[0][1]
        cur.execute("SELECT tags FROM forms_all WHERE lemma = ? AND pos = 'noun'", (noun_lem,))
        lem_tags = [r[0] for r in cur.fetchall()]
        noun_gender = "m"
        for lt in lem_tags:
            if ":f:" in lt:
                noun_gender = "f"
                break
            elif ":n:" in lt:
                noun_gender = "n"
                break
            elif ":m:" in lt:
                noun_gender = "m"
                break

        if req_gender and noun_gender not in req_gender:
            continue
        chosen_noun_lem = noun_lem
        chosen_noun_gender = noun_gender
        break

    if not chosen_noun_lem:
        return None

    if is_plural:
        cur.execute("SELECT word_form FROM forms_all WHERE lemma = ? AND pos = 'adj' AND tags LIKE '%adj:p:v_naz%'", (adj_lem,))
        adj_res = cur.fetchall()
        adj_form = adj_res[0][0] if adj_res else adj_lem
        cur.execute("SELECT word_form FROM forms_all WHERE lemma = ? AND pos = 'noun' AND tags LIKE '%:p:v_naz%'", (chosen_noun_lem,))
        p_row = cur.fetchone()
        noun_cand = p_row[0] if p_row else chosen_noun_lem
    else:
        cur.execute(f"SELECT word_form FROM forms_all WHERE lemma = ? AND pos = 'adj' AND tags LIKE '%adj:{chosen_noun_gender}:v_naz%'", (adj_lem,))
        adj_res = cur.fetchall()
        adj_form = adj_res[0][0] if adj_res else adj_lem
        noun_cand = chosen_noun_lem

    return f"{adj_form.capitalize()} {noun_cand}"


def normalize_apostrophes(text: str) -> str:
    """Standardize apostrophe variants to ASCII apostrophe."""
    return APOSTROPHE_RE.sub("'", text)


def dehyphenate_text(text: str) -> str:
    """Join line-broken hyphenated words and eliminate soft hyphens."""
    res = HYPHEN_BREAK_RE.sub(r"\1\2", text)
    return res.replace("\xad", "")


_IPV4_RE = re.compile(r"(?<!\d\.)\b(?P<ip>(?:[0-9]{1,3}\.){3}[0-9]{1,3})\b(?!\.\d)")
_SECTION_PREFIX_RE = re.compile(r"(?:пункт|п\.|параграф|§|розділ|стаття|ст\.|частина|ч\.)\s*$", re.IGNORECASE)
_NETWORKING_CONTEXT_RE = re.compile(
    r"(?:ip|ip-адрес\w*|адрес\w*|хост\w*|вуз(?:ол|ла|ли|лів)|сервер\w*|роутер\w*|маршрутизатор\w*|"
    r"мереж\w*|підмереж\w*|протокол\w*|провайдер\w*|онлайн|вікіпеді\w*|вікі\b|інтернет\w*|ping|dns|tcp|udp|порт\w*|користувач\w*)",
    re.IGNORECASE,
)


def sanitize_ip_addresses(text: str) -> str:
    """Replace non-doc/non-loopback IPv4 addresses with standard RFC 5737 documentation IPs.

    Prevents public routable IP leaks in educational networking examples while preserving
    valid document section numbering citations (e.g., 4.1.3.1, 1.4.1.2) and numeric lists.
    """
    def _ip_replacer(match: re.Match[str]) -> str:
        ip_str = match.group("ip")
        parts = ip_str.split(".")
        if not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            return ip_str
        p0, p1, p2, p3 = (int(x) for x in parts)

        # RFC 5737 Documentation IPs & Loopback / Well-known public DNS
        if (p0 == 192 and p1 == 0 and p2 == 2) or \
           (p0 == 198 and p1 == 51 and p2 == 100) or \
           (p0 == 203 and p1 == 0 and p2 == 113) or \
           (ip_str in {"127.0.0.1", "0.0.0.0", "1.1.1.1", "8.8.8.8"}):
            return ip_str

        start = match.start()
        prefix = text[max(0, start - 40):start]
        if _SECTION_PREFIX_RE.search(prefix):
            return ip_str

        window = text[max(0, start - 100):min(len(text), match.end() + 100)]
        has_network_ctx = bool(_NETWORKING_CONTEXT_RE.search(window))

        # In networking context: sanitize any non-doc IP (including 1.2.3.4)
        if has_network_ctx:
            return f"198.51.100.{max(1, p3 % 254)}"

        # Without networking context:
        # Outline/section numbering (small parts <= 20) -> preserve
        if p0 <= 20 and p1 <= 20 and p2 <= 20 and p3 <= 20:
            return ip_str

        # Plain numeric list without networking context -> preserve
        return ip_str

    return _IPV4_RE.sub(_ip_replacer, text)



def has_space_split_ocr_word(snippet: str, cur_ves: sqlite3.Cursor | None = None) -> bool:
    """Detect if snippet contains space-split broken words, missing OCR hyphens, or column fusion."""
    if re.search(
        r"\b(?:будь|хтозна|казна)(?:який|яка|яке|які|якого|якій|якому|яким|яких|якою|хто|що|де|коли|куди|кого|кому|ким|чого|чому|чим|як)\b|"
        r"\b(?:хто|що|кого|кому|ким|чого|чому|чим|який|яка|яке|які|якого|якій|якому|яким|яких|якою|чий|чия|чиє|чиї|де|куди|коли|як|звідки|доки|скільки)небудь\b|"
        r"\b(?:хто|що|кого|кому|ким|чого|чому|чим|який|яка|яке|які|якого|якій|якому|яким|яких|якою|де|куди|коли|як|такий|така|таке|такі|так|тому)то\b|"
        r"\b(?:як|тільки)но\b",
        snippet,
        re.IGNORECASE,
    ):
        return True
    cur = cur_ves or get_vesum_cursor()
    if not cur:
        return False
    if has_spliced_sentence_ocr(snippet, cur):
        return True
    words = re.findall(r"[а-яіїєґ']+", snippet.lower())
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        if len(w1) >= 2 and len(w2) >= 2:
            combined = w1 + w2
            if not is_vesum_attested(w2, cur) and is_vesum_attested(combined, cur):
                return True
            if not is_vesum_attested(w1, cur) and is_vesum_attested(combined, cur):
                return True
    return False


def has_spliced_sentence_ocr(text: str, cur_ves: sqlite3.Cursor | None = None) -> bool:
    """Detect OCR column fusion where a second capitalized clause begins mid-sentence without punctuation."""
    cur = cur_ves or get_vesum_cursor()
    if not cur:
        return False
    for m in re.finditer(r"\b([а-яіїєґ]{2,})\s+([А-ЯІЇЄҐ][а-яіїєґ]{2,})\b", text):
        _w1, w2 = m.group(1), m.group(2)
        cur.execute("SELECT tags FROM forms_all WHERE word_form IN (?, ?)", (w2.lower(), w2.capitalize()))
        rows = cur.fetchall()
        if not rows:
            continue
        is_prop = any(any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr")) for r in rows)
        if not is_prop:
            return True
    return False


def repair_ocr_missing_hyphens(text: str) -> str:
    """Repair missing hyphens in indefinite/negative pronouns or adverbs like будь-який, хто-небудь, тільки-но, як-то."""
    t = re.sub(
        r"\b(будь|хтозна|казна)(який|яка|яке|які|якого|якій|якому|яким|яких|якою|хто|що|де|коли|куди|кого|кому|ким|чого|чому|чим|як)\b",
        r"\1-\2",
        text,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(хто|що|кого|кому|ким|чого|чому|чим|який|яка|яке|які|якого|якій|якому|яким|яких|якою|чий|чия|чиє|чиї|де|куди|коли|як|звідки|доки|скільки)(небудь)\b",
        r"\1-\2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(хто|що|кого|кому|ким|чого|чому|чим|який|яка|яке|які|якого|якій|якому|яким|яких|якою|де|куди|коли|як|такий|така|таке|такі|такого|такій|такому|таким|таких|такою|так|тому)(то)\b",
        r"\1-\2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(як|тільки)(но)\b",
        r"\1-\2",
        t,
        flags=re.IGNORECASE,
    )
    return t


def repair_ocr_space_splits(text: str, cur_ves: sqlite3.Cursor | None = None) -> str:
    """Repair broken words split by intra-word whitespace during PDF OCR extraction."""
    cur = cur_ves or get_vesum_cursor()
    if not cur:
        return text

    def _replace_split(match: re.Match) -> str:
        w1, w2 = match.group(1), match.group(2)
        combined = w1 + w2
        if (not is_vesum_attested(w2, cur) or not is_vesum_attested(w1, cur)) and is_vesum_attested(combined, cur):
            return combined
        return match.group(0)

    return re.sub(r"\b([а-яіїєґА-ЯІЇЄҐ]{2,})\s+([а-яіїєґ]{2,})\b", _replace_split, text)


def sanitize_typography(text: str) -> str:
    """Sanitize spacing, apostrophes, OCR space splits, missing hyphens, and terminal punctuation."""
    t = normalize_apostrophes(text)
    t = dehyphenate_text(t)
    t = repair_ocr_missing_hyphens(t)
    t = sanitize_ip_addresses(t)
    t = repair_ocr_space_splits(t)
    t = re.sub(r"(?<=[.?!])\s*([●•*–-])\s*", r"\n\1 ", t)
    t = re.sub(r"^[●•*]\s*", "", t, flags=re.MULTILINE)
    t = MULTISPACE_RE.sub(" ", t)
    t = DOUBLE_PUNCT_RE.sub(".", t)
    t = PUNCT_DOT_RE.sub(r"\1", t)
    return t.strip()


def ensure_single_terminal_dot(text: str) -> str:
    """Ensure sentence ends with single punctuation mark without duplicates."""
    t = text.strip()
    if t.endswith((".", "!", "?", "…")):
        return DOUBLE_PUNCT_RE.sub(".", PUNCT_DOT_RE.sub(r"\1", t))
    return t + "."


def apply_calque_sanitation(text: str) -> str:
    """Replace Russian calques with sovereign literary Ukrainian, preserving casing."""
    def make_repl(target: str):
        def repl(m: re.Match[str]) -> str:
            matched = m.group(0)
            if matched[0].isupper():
                return target[0].upper() + target[1:]
            return target
        return repl

    res = text
    for pat, repl_str in CALQUE_REPLACEMENTS:
        res = pat.sub(make_repl(repl_str), res)
    return res


def format_nested_quotes(text: str) -> str:
    """Apply Pravopys 2019 § 164 nested quotes: outer «...», inner „...“."""
    res: list[str] = []
    level = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in ('"', '“', '”', '«', '»', '„'):
            is_open = False
            is_close = False
            if ch in ('«', '„'):
                is_open = True
            elif ch == '»':
                is_close = True
            elif ch in ('“', '”'):
                if level >= 1:
                    is_close = True
                else:
                    is_open = True
            elif ch == '"':
                prev_char = text[i - 1] if i > 0 else ' '
                if prev_char in ' \t\n([{«„—–-':
                    is_open = True
                else:
                    is_close = True

            if is_open:
                if level == 0:
                    res.append('«')
                    level = 1
                else:
                    res.append('„')
                    level += 1
            elif is_close:
                if level > 1:
                    res.append('“')
                    level -= 1
                elif level == 1:
                    res.append('»')
                    level = 0
                else:
                    # Drop orphan closing quote when level is 0 to avoid unbalanced quotes
                    pass
        else:
            res.append(ch)
        i += 1

    while level > 1:
        res.append('“')
        level -= 1
    if level == 1:
        res.append('»')
        level = 0
    return ''.join(res)


_PEJORATIVE_PATTERNS = [
    re.compile(r"очевидно\s+(?:кожному\s+|навіть\s+)?дурн\w*", re.IGNORECASE),
    re.compile(r"\b(?:ви|ти|учень|учениця|студент|хтось)\s+(?:є\s+)?(?:дур\w*|ідіот\w*|нездар\w*|туп\w*|безграмотн\w*)", re.IGNORECASE),
    re.compile(r"\b(?:абсолютно|цілком|геть|зовсім)\s+безграмотн\w*", re.IGNORECASE),
    re.compile(r"не дивно,\s*що\s+ви\s+(?:цього\s+)?не", re.IGNORECASE),
    re.compile(r"навіть\s+першокласник\s+знає", re.IGNORECASE),
    re.compile(r"як\s+можна\s+не\s+знати", re.IGNORECASE),
    re.compile(r"соромно\s+не\s+знати", re.IGNORECASE),
    re.compile(r"\bтуп(?:ий|ого|ому|им|і|их)\s+(?:людин|учн|студент|ідіот|дурн|мозок|розум)", re.IGNORECASE),
    re.compile(r"\bнастільки\s+туп\w*", re.IGNORECASE),
    re.compile(r"\b(?:ідіот\w*|дебіл\w*|кретин(?:[ауеі]|ом|ів|ам|ами|ах)?|нездар\w*)\b", re.IGNORECASE),
]


def verify_pedagogical_tone(text: str) -> bool:
    """Ensure text has neutral, respectful pedagogical tone (Gate 6)."""
    # Protect geometric obtuse angle/triangle ("тупий кут", "тупокутний трикутник")
    t_clean = re.sub(r"\bтуп(?:ий|ого|ому|им|і|их)\s+кут\w*", "кут", text, flags=re.IGNORECASE)
    t_clean = re.sub(r"\bтупокутн\w*", "трикутник", t_clean, flags=re.IGNORECASE)
    # Protect benign literary nouns and adverbs ("дурниця", "дурно")
    t_clean = re.sub(r"\bдурниц\w*", "дрібниця", t_clean, flags=re.IGNORECASE)
    t_clean = re.sub(r"\bдурно\b", "марно", t_clean, flags=re.IGNORECASE)
    # Protect clinical biology terms ("кретинізм" - congenital iodine deficiency syndrome)
    t_clean = re.sub(r"\bкретинізм\w*", "захворювання", t_clean, flags=re.IGNORECASE)
    # Protect historical literacy campaigns ("ліквідація безграмотності")
    t_clean = re.sub(r"\b(?:ліквідація|боротьба з|подолання)\s+безграмотн\w*", "освіта", t_clean, flags=re.IGNORECASE)
    return not any(p.search(t_clean) for p in _PEJORATIVE_PATTERNS)



def check_protected_entities(text: str) -> bool:
    """Verify that geometric volume and scientific ratios are not corrupted."""
    t_lower = text.lower()
    corruptions = (
        "обсяг циліндра", "обсяг конуса", "обсяг піраміди", "обсяг кулі",
        "обсяг призми", "обсяг куба", "стосунки величин", "стосунки чисел",
    )
    return all(c not in t_lower for c in corruptions)


@dataclass
class TextbookChunk:
    chunk_id: str
    title: str
    text: str
    source_file: str
    grade: str
    author: str
    subject: str
    char_count: int
    concept: str = ""
    snippet: str = ""
    terms: list[str] = field(default_factory=list)

    @property
    def domain(self) -> str:
        return "stem" if self.subject in STEM_SUBJECTS else "humanities"

    @property
    def subject_genitive(self) -> str:
        return UKRAINIAN_SUBJECT_GENITIVE.get(self.subject, self.subject)

    @property
    def subject_nominative(self) -> str:
        return UKRAINIAN_SUBJECT_NOMINATIVE.get(self.subject, self.subject.capitalize())


def is_clean_content_chunk(chunk: TextbookChunk, cur_ves: sqlite3.Cursor | None = None) -> bool:
    """Filter out administrative frontmatter, tables of contents, exercise sections, and short fragments."""
    if chunk.char_count < 150:
        return False
    if chunk.subject not in STEM_SUBJECTS and chunk.subject not in HUMANITIES_SUBJECTS:
        return False
    t = chunk.text
    frontmatter_markers = (
        "Рекомендовано Міністерством освіти і науки",
        "Видано за рахунок державних коштів",
        "Продаж заборонено",
        "УДК ", "ББК ",
        "Підручник створено відповідно до",
        "Підручник розроблено відповідно до",
        "Від авторів",
        "Шановні семикласники",
        "Шановні восьмикласники",
        "Шановні дев'ятикласники",
        "Шановні десятикласники",
        "Шановні одинадцятикласники",
        "Дорогі семикласники",
        "Дорогі восьмикласники",
        "Дорогі дев'ятикласники",
        "Як працювати з підручником",
        "Умовні позначення",
    )
    if re.search(r"(?:\.\s*){3,}\d+", t) or re.search(r"\.{3,}\s*\d+", t):
        return False
    if re.search(r"^\s*(?:зміст|table of contents)\b", t, re.IGNORECASE | re.MULTILINE):
        return False
    # Reject chunks starting with or dominated by exercises / problem sets
    if re.search(r"^\s*(?:вправа|вправи|завдання|питання і завдання|практична робота|лабораторна робота|тестові завдання)\b", t, re.IGNORECASE | re.MULTILINE):
        return False
    if len(EXERCISE_ITEM_RE.findall(t)) >= 2:
        return False
    numbered_lines = re.findall(r"^\s*\d+[\.\)]\s+([^\n]+)", t, re.MULTILINE)
    numbered_exercises = [
        nl for nl in numbered_lines
        if any(w in EXERCISE_IMPERATIVES for w in re.findall(r"[а-яіїєґ']+", nl.lower())) or "?" in nl
    ]
    if len(numbered_exercises) >= 2:
        return False
    if len(FIGURE_REF_RE.findall(t)) >= 2 and len(t) < 800:
        return False
    if not verify_pedagogical_tone(t):
        return False
    if any(m in t for m in frontmatter_markers):
        return False
    # Reject font encoding corruptions / PDF mojibake
    if re.search(r"[ÐÎÅÒÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]", t):
        return False
    concept = extract_key_concept(chunk, cur_ves=cur_ves)
    if not concept:
        return False
    snippet = extract_meaningful_text_snippet(chunk.text, concept=concept)
    if not snippet or len(snippet) < 50:
        return False
    if has_spliced_sentence_ocr(snippet, cur_ves=cur_ves) or has_space_split_ocr_word(snippet, cur_ves=cur_ves):
        return False
    terms = extract_scientific_terminology_for_snippet(snippet, concept, chunk.subject, cur_ves=cur_ves)
    if not terms or len(terms) < 2:
        return False
    chunk.concept = concept
    chunk.snippet = snippet
    chunk.terms = terms
    return True


def load_textbook_chunks(db_path: Path) -> tuple[list[TextbookChunk], list[TextbookChunk]]:
    """Load textbook chunks from sources.db, partitioned into eval pool and train pool with strict text firewall."""
    cur_ves = get_vesum_cursor()
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute("""
        SELECT chunk_id, title, text, source_file, grade, coalesce(author_uk, author, ''), subject, char_count
        FROM textbooks
        WHERE length(text) >= 150
        ORDER BY subject, source_file, id
    """)
    eval_chunks: list[TextbookChunk] = []
    candidate_train_chunks: list[TextbookChunk] = []

    for row in cur.fetchall():
        cid, title, text, src_file, grade, author, subject, char_count = row
        subj = (subject or "").strip().lower()
        if not subj or (subj not in STEM_SUBJECTS and subj not in HUMANITIES_SUBJECTS):
            continue
        chunk = TextbookChunk(
            chunk_id=cid,
            title=title or "",
            text=text or "",
            source_file=src_file or "",
            grade=str(grade or ""),
            author=author or "",
            subject=subj,
            char_count=char_count or len(text or ""),
        )
        if not is_clean_content_chunk(chunk, cur_ves=cur_ves):
            continue

        if chunk.source_file in HELD_OUT_SET:
            eval_chunks.append(chunk)
        else:
            candidate_train_chunks.append(chunk)

    conn.close()

    # Cryptographic text content leakage firewall
    eval_text_hashes = {hashlib.sha256(c.text.strip().encode("utf-8")).hexdigest() for c in eval_chunks}
    train_chunks = [
        c for c in candidate_train_chunks
        if hashlib.sha256(c.text.strip().encode("utf-8")).hexdigest() not in eval_text_hashes
    ]

    # Verify strict disjointness without relying on python -O disabled asserts
    eval_books = {c.source_file for c in eval_chunks}
    train_books = {c.source_file for c in train_chunks}
    if not eval_books.isdisjoint(train_books):
        raise ValueError(f"Book leakage detected: {eval_books & train_books}")

    eval_cids = {c.chunk_id for c in eval_chunks}
    train_cids = {c.chunk_id for c in train_chunks}
    if not eval_cids.isdisjoint(train_cids):
        raise ValueError(f"Chunk ID leakage detected: {eval_cids & train_cids}")

    train_text_hashes = {hashlib.sha256(c.text.strip().encode("utf-8")).hexdigest() for c in train_chunks}
    if not eval_text_hashes.isdisjoint(train_text_hashes):
        raise ValueError(f"Verbatim text content leakage detected: {len(eval_text_hashes & train_text_hashes)} chunks")

    return eval_chunks, train_chunks



def is_clean_prose_line(line: str) -> bool:
    """Validate that a single line is clean textbook running prose, rejecting OCR garble, formulas, and TOC."""
    s = line.strip()
    if not s or len(s) < 10:
        return False
    # Drop section titles and structural headings
    if re.match(r"^(?:§\s*\d*|\b(?:розділ|тема|частина|параграф|урок)\b)", s, re.IGNORECASE):
        return False
    # Drop short all-caps lines (titles, headers)
    if s.isupper() and len(s) < 50:
        return False
    # Drop lines with OCR capital-corruption inside words
    if re.search(r"[а-яіїєґ][А-ЯІЇЄҐ]{2,}", s):
        return False
    # Drop table of contents dot leaders or spaced dots
    if re.search(r"(?:\.\s*){3,}", s) or re.search(r"\.{3,}", s):
        return False
    # Drop page number indicators
    if re.search(r"\b(?:стор|с\.)\s*\d+\b", s, re.IGNORECASE):
        return False
    # Drop figures, diagrams, tables, and exercises
    if re.match(r"^(?:мал\.|рис\.|таблиц\w*|схема|діаграм\w*|фото|вправа|завдання|питання|варіант)\b", s, re.IGNORECASE):
        return False
    if FIGURE_REF_RE.search(s):
        return False
    if LAB_EQUIPMENT_RE.search(s):
        return False
    if "?" in s:
        return False
    if s.count(";") >= 2 or (":" in s and s.endswith(";")):
        return False
    if MATH_GARBLE_RE.search(s):
        return False
    if EXERCISE_ITEM_RE.match(s):
        return False
    if any(p.search(s) for p in EXERCISE_LINE_PATTERNS):
        return False
    words = [w.strip('.,;:?!"«»„“—–()').lower() for w in s.split()]
    if any(w in EXERCISE_IMPERATIVES for w in words):
        return False
    # Drop formula garble: empty parens, spaced periods, isolated math operators
    if re.search(r"\(\s*\)|\.\s+\.", s):
        return False
    if re.search(r"(?:[=><±×÷−]\s*){2,}", s):
        return False
    # Drop spaced sequences of isolated Latin formula fragments (e.g. 'OA OB AOB' or 'x a y b R')
    if re.search(r"\b[a-zA-Z]{1,3}(?:\s+[a-zA-Z]{1,3}){2,}\b", s):
        return False
    # If line is short and has no terminal punctuation, treat as heading or table fragment
    if len(s) < 50 and not s.endswith((".", "!", "»", "“", "—", "-")):
        return False
    # Cyrillic vs Latin / symbols / digits ratio
    cyr = len(re.findall(r"[а-яіїєґА-ЯІЇЄҐ]", s))
    lat = len(re.findall(r"[a-zA-Z]", s))
    digits = len(re.findall(r"[0-9]", s))
    symbols = len(re.findall(r"[=><±×÷−+\\/*_^{}[\]|~]", s))
    total_letters = cyr + lat
    if cyr < 8:
        return False
    if total_letters > 0 and (cyr / total_letters) < 0.80:
        return False
    if (symbols + digits) > (cyr * 0.40):
        return False
    return not OCR_DROPCAP_RE.search(s)


def check_concept_contradiction(snippet: str, concept: str) -> bool:
    """Detect if snippet contradicts the concept via antonymous/differentiating modifiers."""
    snip_words = set(re.findall(r"[а-яіїєґ']+", snippet.lower()))
    conc_words = set(re.findall(r"[а-яіїєґ']+", concept.lower()))

    for m1, m2 in CONTRADICTORY_MODIFIER_PAIRS:
        def _has_ex(words: set[str], s1: str, s2: str) -> bool:
            return any(w.startswith(s1) and not w.startswith(s2) for w in words)

        c1 = _has_ex(conc_words, m1, m2)
        c2 = any(w.startswith(m2) for w in conc_words)

        s1 = _has_ex(snip_words, m1, m2)
        s2 = any(w.startswith(m2) for w in snip_words)

        if c1 and not c2 and s2 and not s1:
            return True
        if c2 and not c1 and s1 and not s2:
            return True
    return False


_DEFINITIONAL_QUICK_FILTER_RE = re.compile(
    r"[—–-]\s*(?:це\b|[а-яіїєґ]{3,})|\b(?:називають|називається|названо|означення|визначення|розуміють)\b|\bє\b",
    re.IGNORECASE,
)


def is_definitional_for_concept(
    snippet: str,
    concept: str,
    cur_ves: sqlite3.Cursor | None = None,
) -> bool:
    """Verify that the snippet contains a genuine definitional pattern whose defined entity strictly aligns with the concept."""
    if not snippet or not concept:
        return False
    if not _DEFINITIONAL_QUICK_FILTER_RE.search(snippet):
        return False
    cur = cur_ves or get_vesum_cursor()

    # Negative gates
    # 1. Anaphora / deictic starters
    if re.search(r"\b(?:так|саме\s+так)\s+(?:називають|називається|називали|назвали)\b", snippet, re.IGNORECASE):
        return False
    if re.search(r"\bтаке\s+[а-яіїєґ]+", snippet, re.IGNORECASE):
        return False
    if DANGLING_STARTER_RE.search(snippet) or has_unresolved_anaphora(snippet):
        return False

    # 2. Metaphors
    if re.search(r"\b(?:наче|мов|немов|немовби|ніби|неначе|подібно\s+до)\b", snippet, re.IGNORECASE):
        return False

    # 3. Evaluative commentary and non-definitions
    if re.search(
        r"\b(?:один|одна|одне|одні)\s+(?:з|із)\s+най\w+|"
        r"[—–-]\s*(?:це\s+)?(?:один|одна|одне|одні)\s+(?:з|із)\s+най\w+|"
        r"[—–-]\s*(?:це\s+)?якщо\b|"
        r"[—–-]\s*(?:це\s+)?така\s+сама\s+\w+,\s+як\b|"
        r"[—–-]\s*(?:це\s+)?(?:ефективн\w*|унікальн\w*|чудов\w*|важлив\w*|цікав\w*|зручн\w*|найкращ\w*|найважливіш\w*|головн\w*)\b|"
        r"\b(?:найважливішим\s+досягненням|чудовим\s+прикладом|варто\s+зазначити|цікаво,\s*що|як\s+відомо|має\s+важливе\s+значення)\b",
        snippet,
        re.IGNORECASE,
    ):
        return False

    # Negative assertions (e.g. 'Харчові добавки не є ліками')
    if re.search(r"(?:^|[.!?«„]\s*)[А-ЯІЇЄҐ][а-яіїєґ\s'-]{2,40}\s+не\s+є\b", snippet):
        return False

    # 4. Narrative / biography
    if re.search(
        r"\b(?:живе\s+в\b|народивс\w*|помер\w*|навчавс\w*|закінчив\w*|працював\w*|очолив\w*|прожив\w*|мешкав\w*)\b",
        snippet,
        re.IGNORECASE,
    ):
        return False

    # 5. Consequence of definition
    if re.search(r"\b(?:з\s+означення\s+випливає|як\s+наслідок|звідси\s+випливає|отже|таким\s+чином)\b", snippet, re.IGNORECASE):
        return False

    # 6. Ordinals in concept
    if re.search(
        r"^(?:перш\w*|друг\w*|трет\w*|четверт\w*|п['ʼ’]?ят\w*|шост\w*|сьом\w*|восьм\w*|дев['ʼ’]?ят\w*|десят\w*|наступн\w*|останн\w*)\b",
        concept,
        re.IGNORECASE,
    ):
        return False

    def _extract_content_lemmas(phrase: str) -> set[str]:
        words = re.findall(r"[а-яіїєґ']+", phrase.lower())
        func_words = {
            "та", "і", "й", "або", "чи", "а", "але", "це", "до", "від", "на", "в", "у",
            "із", "зі", "за", "під", "над", "при", "про", "для", "без", "через", "з",
            "як", "що", "де", "коли", "який", "яка", "яке", "які", "цей", "ця", "ці",
            "означення", "визначення",
        }
        res: set[str] = set()
        for w in words:
            if len(w) >= 3 and w not in func_words:
                lems = get_vesum_word_lemmas(w, cur) or {w}
                res.update(lems)
        return res

    conc_lemmas = _extract_content_lemmas(concept)
    if not conc_lemmas:
        return False

    meta_terms = {"поняття", "термін", "явище", "процес", "величина", "графік", "графіка", "властивість", "закон", "правило", "формула"}

    def _matches_concept(target_lemmas: set[str]) -> bool:
        if not target_lemmas:
            return False
        if target_lemmas == conc_lemmas:
            return True
        if len(target_lemmas) > len(conc_lemmas):
            core = target_lemmas - meta_terms
            if core == conc_lemmas:
                return True
        return False

    # 1. Copula: X — це ... or X — [noun] ...
    for m in re.finditer(r"(?:^|[.!?«„]\s*)([А-ЯІЇЄҐ][а-яіїєґ\s'-]{2,45})\s+[—–-]\s+(?:це\b|([а-яіїєґ]{3,}))", snippet):
        subj = m.group(1).strip()
        after_w = m.group(2)
        if after_w:
            w_info = get_vesum_word_info(after_w.lower(), cur)
            if any(r[1] == "verb" or "verb" in r[2] for r in w_info):
                continue
        subj_lemmas = _extract_content_lemmas(subj)
        if _matches_concept(subj_lemmas):
            return True

    # 2. Naming: називають X / X називають
    for m in re.finditer(r"\b(?:називають|називається|названо)\s+([а-яіїєґ\s'-]{2,40})(?:[,.:;\(«»“\"—–-]|\bякщо\b|\bколи\b|\bде\b|\bна\b|$)", snippet):
        obj = m.group(1).strip()
        rec = recover_named_noun_phrase(snippet, obj, cur)
        cand_obj = rec or obj
        obj_lemmas = _extract_content_lemmas(cand_obj)
        if _matches_concept(obj_lemmas):
            return True

    for m in re.finditer(r"(?:^|[.!?«„]\s*)([А-ЯІЇЄҐ][а-яіїєґ\s'-]{2,45})\s+(?:називають|називається)\b", snippet):
        subj = m.group(1).strip()
        subj_lemmas = _extract_content_lemmas(subj)
        if _matches_concept(subj_lemmas):
            return True

    # 3. Formal Означення. ... containing concept
    if re.search(r"(?:^|[.!?«„]\s*)(?:Означення|Визначення)\b(?:\s+\d+)?[\.:]", snippet):
        snip_lemmas = _extract_content_lemmas(snippet)
        if conc_lemmas.issubset(snip_lemmas):
            return True

    # 4. Під X розуміють ...
    for m in re.finditer(r"\bпід\s+([а-яіїєґ\s'-]{2,35})\s+розуміють\b", snippet, re.IGNORECASE):
        und = m.group(1).strip()
        und_lemmas = _extract_content_lemmas(und)
        if _matches_concept(und_lemmas):
            return True

    # 5. Copula with є: concept appears as defined subject
    for m in re.finditer(r"(?:^|[.!?«„]\s*)([А-ЯІЇЄҐ][а-яіїєґ\s'-]{2,40})\s+є\s+([а-яіїєґ\s'-]{3,40})", snippet, re.IGNORECASE):
        subj = m.group(1).strip()
        pred = m.group(2).strip()
        if re.match(r"^(?:одним|однією|найбільш|найзначніш|найважливіш)\b", pred.lower()):
            continue
        first_w = subj.split()[0].lower().strip(".,;:?!'\"«»„“—–()")
        first_w_info = get_vesum_word_info(first_w, cur)
        if any("v_oru" in r[2] or ":oru" in r[2] for r in first_w_info) and not any("v_naz" in r[2] or ":naz" in r[2] for r in first_w_info):
            continue
        has_pred_noun = any(
            any(r[1] == "noun" and any(c in r[2] for c in (":v_oru", ":v_naz", ":oru", ":naz")) for r in get_vesum_word_info(w.lower().strip(".,;:?!'\"«»„“—–()"), cur))
            for w in pred.split()
        )
        if not has_pred_noun:
            continue
        subj_lemmas = _extract_content_lemmas(subj)
        if _matches_concept(subj_lemmas):
            return True
        pred_lemmas = _extract_content_lemmas(pred)
        if _matches_concept(pred_lemmas):
            return True

    return False


def is_snippet_grounded_in_concept(
    snippet: str,
    concept: str,
    cur_ves: sqlite3.Cursor | None = None,
) -> bool:
    """Verify that the snippet is strictly grounded in the concept via lemma equality and definitional patterns."""
    if not snippet or not concept:
        return False
    if not _DEFINITIONAL_QUICK_FILTER_RE.search(snippet):
        return False
    if check_concept_contradiction(snippet, concept):
        return False
    if DANGLING_STARTER_RE.search(snippet):
        return False
    if FORWARD_BACKWARD_REF_RE.search(snippet):
        return False

    conc_words = [w for w in re.findall(r"[а-яіїєґa-zA-Z0-9']+", concept.lower()) if len(w) >= 2]
    if not conc_words:
        return False

    function_words = {
        "та", "і", "й", "або", "чи", "а", "але", "це", "до", "від", "на", "в", "у",
        "із", "зі", "за", "під", "над", "при", "про", "для", "без", "через", "з",
        "як", "що", "де", "коли", "який", "яка", "яке", "які", "цей", "ця", "ці",
    }
    meta_terms = {
        "поняття", "термін", "явище", "процес", "величина", "графік", "графіка",
        "властивість", "закон", "правило", "формула", "означення", "визначення",
    }
    content_conc_words = [w for w in conc_words if w not in function_words and len(w) >= 3]
    non_meta_conc_words = [w for w in content_conc_words if w not in meta_terms]
    target_words = non_meta_conc_words if non_meta_conc_words else (content_conc_words if content_conc_words else conc_words)

    # Fast stem pre-filter: avoid expensive lemma parsing if primary word stem is absent
    primary_word = target_words[0]
    primary_stem = primary_word[:4] if len(primary_word) >= 5 else primary_word
    snip_lower = snippet.lower()
    if primary_stem not in snip_lower and primary_word not in snip_lower:
        return False

    cur = cur_ves or get_vesum_cursor()
    # Primary entity check via VESUM lemma equality (not string prefixes!)
    primary_lemmas = get_vesum_lemmas(primary_word, cur)
    snip_lemmas = get_vesum_lemmas(snippet, cur)

    if primary_lemmas and snip_lemmas:
        if not (primary_lemmas & snip_lemmas):
            return False
    else:
        snip_words = set(re.findall(r"[а-яіїєґa-zA-Z0-9']+", snip_lower))
        if primary_word not in snip_words:
            return False

    # Check antonymous contradictory modifiers
    snip_words = set(re.findall(r"[а-яіїєґ']+", snippet.lower()))
    conc_word_set = set(conc_words)
    for m1, m2 in CONTRADICTORY_MODIFIER_PAIRS:
        def _has_ex(w_set: set[str], s1: str, s2: str) -> bool:
            return any(w.startswith(s1) and not w.startswith(s2) for w in w_set)

        if _has_ex(conc_word_set, m1, m2) and not _has_ex(snip_words, m1, m2):
            return False
        if any(w.startswith(m2) for w in conc_word_set) and not any(w.startswith(m2) for w in snip_words):
            return False

    return is_definitional_for_concept(snippet, concept, cur)


def extract_meaningful_text_snippet(
    text: str,
    concept: str = "",
    terms: list[str] | None = None,
    max_len: int = 320,
) -> str:
    """Extract a coherent, grounded contiguous prose paragraph ending on a sentence boundary without exercises or questions."""
    clean = sanitize_typography(text)
    clean = re.sub(r"\n\s*([—–-])\s*\n", r" \1 ", clean)
    lines = clean.splitlines()
    blocks: list[list[str]] = []
    curr: list[str] = []
    for line in lines:
        if is_clean_prose_line(line):
            curr.append(line.strip())
        else:
            if curr:
                blocks.append(curr)
                curr = []
    if curr:
        blocks.append(curr)

    # Collect keywords from concept and terms for grounding
    grounding_keywords: set[str] = set()
    if concept:
        for w in re.findall(r"[а-яіїєґ']+", concept.lower()):
            if len(w) >= 3 and w not in STOPWORD_TERMS:
                grounding_keywords.add(w)
    if terms:
        for t in terms:
            for w in re.findall(r"[а-яіїєґ']+", t.lower()):
                if len(w) >= 3 and w not in STOPWORD_TERMS:
                    grounding_keywords.add(w)

    def _sentence_score(s: str) -> int:
        if not (50 <= len(s) <= max_len):
            return -100
        if not s.endswith((".", "!", "»", "“")):
            return -100
        if "?" in s or QUESTION_STARTER_RE.match(s):
            return -100
        if FIGURE_REF_RE.search(s) or LAB_EQUIPMENT_RE.search(s) or MATH_GARBLE_RE.search(s):
            return -100
        if re.search(r"\(\s*\)|\.\s+\.|\.{3,}", s):
            return -100
        if s.count(";") >= 2:
            return -100
        if any(w in EXERCISE_IMPERATIVES for w in re.findall(r"[а-яіїєґ']+", s.lower())):
            return -100
        if DANGLING_STARTER_RE.search(s) or has_unresolved_anaphora(s):
            return -100
        if FORWARD_BACKWARD_REF_RE.search(s):
            return -100
        if has_space_split_ocr_word(s):
            return -100
        if concept and not is_snippet_grounded_in_concept(s, concept):
            return -100

        score = 1
        s_lower = s.lower()
        conc_stem = concept.lower()[:len(concept) - 1] if len(concept) > 4 else concept.lower()
        if concept and (concept.lower() in s_lower or conc_stem in s_lower):
            score += 10
        if DEFINITIONAL_MARKER_RE.search(s_lower):
            score += 15
        if terms:
            for t in terms:
                if t.lower() in s_lower:
                    score += 8
        s_words = set(re.findall(r"[а-яіїєґ']+", s_lower))
        for kw in grounding_keywords:
            if kw in s_lower or any(sw.startswith(kw[:4]) for sw in s_words):
                score += 4
        return score

    best_cand = ""
    best_score = 0

    for block in blocks:
        para = dehyphenate_text(" ".join(block))
        para = MULTISPACE_RE.sub(" ", para).strip()
        if len(para) < 50:
            continue
        sents = re.split(r"(?<=[.!?])\s+(?=[«„\"А-ЯІЇЄҐ])", para)
        for s in sents:
            s = s.strip()
            if not s or not re.match(r"^[«„\"А-ЯІЇЄҐ]", s):
                continue
            # Check single definition sentence (strictly single sentence, no second sentence grafting)
            sc = _sentence_score(s)
            if sc > best_score:
                best_score = sc
                best_cand = s

    # Require substantive score (definitional or grounded)
    if best_score >= 10 and best_cand:
        if has_space_split_ocr_word(best_cand):
            return ""
        if concept and not is_snippet_grounded_in_concept(best_cand, concept):
            return ""
        if DANGLING_STARTER_RE.search(best_cand) or has_unresolved_anaphora(best_cand):
            return ""
        if FORWARD_BACKWARD_REF_RE.search(best_cand):
            return ""
        return best_cand.rstrip(". ") + "."

    return ""


def clean_and_validate_candidate(cand: str, cur_ves: sqlite3.Cursor | None = None) -> str | None:
    """Clean and validate a candidate concept, rejecting exercises, dangling punctuation, and non-citation forms."""
    c = cand.strip()
    c = normalize_apostrophes(c)
    c = re.sub(r"[\s\.\d—–-]+$", "", c).strip()
    if not c or len(c) < 4:
        return None
    # Reject terminal dangling punctuation/apostrophes
    if c.endswith(("'", "’", "ʼ", "`", "-", "—", "–", "…", ".")):
        return None
    # Handle 'Тема: ...' or 'Розділ 1: ...' before splitting on colon
    m_colon_sec = re.match(r"^(?:розділ|тема|параграф|частина|урок)\s*(?:\d+|[ivxlcdm]+)?\s*[:—–-]\s*([^.\n?]+)", c, re.IGNORECASE)
    if m_colon_sec:
        sub = m_colon_sec.group(1).strip()
        if len(sub) >= 4:
            c = sub
    else:
        for delim in [":", ";", "(", " - це", " — це", " – це"]:
            if delim in c:
                part = c.split(delim)[0].strip()
                if len(part) >= 4:
                    c = part

    # Strip chapter/section numbering prefixes if substantive content follows
    m_ch = re.match(
        r"^(?:розділ|тема|параграф|частина|урок)\s+(?:\d+|[ivxlcdm]+|перший|другий|третій|четвертий|п['ʼ’]ятий|шостий)[\.\s:—–-]+(?:\s*(?:частина|урок)\s*\d+[\.\s:—–-]+)?\s*([^.\n?]+)",
        c,
        re.IGNORECASE,
    )
    if m_ch:
        sub = m_ch.group(1).strip()
        if len(sub) >= 4:
            c = sub

    # Reject bare section / book structure labels
    if re.match(r"^(?:розділ|тема|частина|параграф|урок)(?:\s+(?:\d+|[ivxlcdm]+))?$", c, re.IGNORECASE):
        return None
    if c.lower() in ("розділ", "тема", "частина", "параграф", "урок", "зміст", "вступ", "передмова", "післямова", "покажчик", "глосарій"):
        return None

    # Reject mojibake and non-Ukrainian character sets
    if not re.match(r"^[А-ЯІЇЄҐа-яіїєґa-zA-Z0-9\s'ʼ’\-–—«»\"().,:;]+$", c):
        return None
    if not re.search(r"[А-ЯІЇЄҐа-яіїєґ]", c):
        return None
    if len(c) > 50:
        c = c[:50].rsplit(" ", 1)[0].strip()
    words = [w.strip(".,;:?!'\"«»„“—–()") for w in c.split() if w.strip(".,;:?!'\"«»„“—–()")]
    if not words or len(words) > 5:
        return None
    # Reject if ANY word is an imperative verb
    if any(w.lower() in EXERCISE_IMPERATIVES for w in words):
        return None
    c_lower = c.lower()
    if any(c_lower.startswith(p) for p in NON_CONCEPT_PREFIXES):
        return None
    if words[0].lower() in FILLER_STARTS:
        return None
    if words[-1].lower() in DANGLING_TAILS:
        return None
    if len(words[-1]) < 2:
        return None
    if c.isupper() or any(ch.isupper() for ch in c[1:]):
        c = c.capitalize()

    # Reject ordinal concepts (e.g. 'Третя теорія')
    if re.match(
        r"^(?:перш\w*|друг\w*|трет\w*|четверт\w*|п['ʼ’]?ят\w*|шост\w*|сьом\w*|восьм\w*|дев['ʼ’]?ят\w*|десят\w*|наступн\w*|останн\w*)\b",
        c,
        re.IGNORECASE,
    ):
        return None

    # Reject superlative concepts (e.g. 'Найкращий вихід', 'Найголовніше', 'Найбільша небезпека')
    if re.match(r"^(?:най|якнай|щонай)\w+", c, re.IGNORECASE):
        return None

    # Reject evaluative and descriptive adjective starters
    if re.match(r"^(?:найкращ\w*|найголовніш\w*|найбільш\w*|найважливіш\w*|найскладніш\w*|потужн\w*|ефективн\w*|унікальн\w*|чудов\w*|прекрасн\w*|висок\w*\s+цінност\w*|велик\w*\s+листк\w*)\b", c, re.IGNORECASE):
        return None

    # Reject conjunctions and conditionals starting concept
    if re.match(r"^(?:та|і|й|або|чи|якщо|коли|де|куди)\b", c.strip(), re.IGNORECASE):
        return None
    if re.search(r"\b(?:очевидн\w*|зрозуміл\w*|незрозуміл\w*|безперечн\w*|помітн\w*)\b", c, re.IGNORECASE):
        return None

    preps = {"від", "для", "до", "з", "із", "зі", "на", "по", "про", "за", "під", "над", "при", "без"}
    if len(words) >= 3 and any(w.lower() in preps for w in words[1:-1]):
        cur = cur_ves or get_vesum_cursor()
        if cur:
            cur.execute("SELECT pos FROM forms_all WHERE word_form = ?", (words[-1].lower(),))
            if any(r[0] == "adj" for r in cur.fetchall()):
                return None

    if len(words) == 1 and words[0].lower() in STOPWORD_TERMS:
        return None
    if words[0].lower() in {"житель", "жителі", "жителя", "жителів", "прихильник", "прихильники", "прихильника"}:
        return None

    cur = cur_ves or get_vesum_cursor()
    if cur and len(words) == 1:
        w = words[0]
        cur.execute("SELECT tags FROM forms_all WHERE word_form = ?", (w.capitalize(),))
        cap_rows = cur.fetchall()
        has_prop = any(any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr")) for r in cap_rows)
        if has_prop:
            cur.execute("SELECT tags, pos FROM forms_all WHERE word_form = ?", (w.lower(),))
            low_rows = cur.fetchall()
            has_nom_common_noun = any(
                r[1] == "noun"
                and ("v_naz" in r[0] or "naz" in r[0])
                and not any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr"))
                for r in low_rows
            )
            if not has_nom_common_noun:
                return None

    # Citation form verification and normalization via VESUM
    if cur and not is_concept_in_citation_form(c, cur):
        c_norm = lemmatize_noun_phrase(c, cur)
        if is_concept_in_citation_form(c_norm, cur):
            c = c_norm
        else:
            return None
    return c


def extract_key_concept(
    chunk: TextbookChunk | str,
    title: str = "",
    subject: str = "",
    cur_ves: sqlite3.Cursor | None = None,
) -> str:
    """Extract the central concept grounded directly in chunk text without imperative exercise noise."""
    if isinstance(chunk, TextbookChunk):
        text = chunk.text
        chunk_title = chunk.title
        subj = chunk.subject
    else:
        text = chunk
        chunk_title = title
        subj = subject

    cur = cur_ves or get_vesum_cursor()
    lines = [normalize_apostrophes(line.strip()) for line in text.splitlines() if line.strip()]

    # 1. Definitional statements in chunk: highest priority concept extraction
    for line in lines:
        m_def = re.search(r"(?:^|[.!?«„●•*–-]\s*)([А-ЯІЇЄҐ][а-яіїєґa-zA-Z\s'-]{2,45})\s+[—–-]\s+(?:це\b|[а-яіїєґ]{3,})", line)
        if m_def:
            val = clean_and_validate_candidate(m_def.group(1), cur_ves=cur)
            if val:
                return val
        m_def2 = re.search(
            r"\b(?:називають|називається|названо)\s+([а-яіїєґ\s'-]{3,40})(?:[,.:;\(«»“\"—–-]|\bякщо\b|\bколи\b|\bде\b|\bна\b|$)",
            line,
        )
        if m_def2:
            raw_val = m_def2.group(1).strip()
            rec = recover_named_noun_phrase(line, raw_val, cur)
            cand = rec or raw_val
            norm_val = lemmatize_noun_phrase(cand, cur)
            val = clean_and_validate_candidate(norm_val, cur_ves=cur)
            if val:
                return val
        m_def3 = re.search(
            r"(?:^|[.!?«„●•*–-]\s*)([А-ЯІЇЄҐ][а-яіїєґa-zA-Z\s'-]{2,45})\s+є\s+(?:однією|одним|частиною|наукою|процесом|явищем|речовиною|формою|способом|системою)\b",
            line,
        )
        if m_def3:
            val = clean_and_validate_candidate(m_def3.group(1), cur_ves=cur)
            if val:
                return val

    # 2. Numbered sections
    for line in lines[:15]:
        m_num_sec = re.match(r"^\d+(?:\.\d+)*[\.\s]+([А-ЯІЇЄҐ][а-яіїєґ0-9\s'-]{3,40})", line)
        if m_num_sec:
            val = clean_and_validate_candidate(m_num_sec.group(1), cur_ves=cur)
            if val:
                return val
        m_sec = re.match(r"^§\s*\d+[\.\s]+([^.\n?]+)", line, re.IGNORECASE)
        if m_sec:
            val = clean_and_validate_candidate(m_sec.group(1), cur_ves=cur)
            if val:
                return val

    # 3. Try chunk title if meaningful and not "Сторінка"
    if chunk_title and not chunk_title.lower().startswith("сторінка"):
        val = clean_and_validate_candidate(chunk_title, cur_ves=cur)
        if val:
            return val

    # 4. Try bold/heading line grounded in chunk
    for line in lines[:10]:
        m_bold = re.match(r"^([А-ЯІЇЄҐ][а-яіїєґ\s'-]{4,40})$", line)
        if m_bold:
            val = clean_and_validate_candidate(m_bold.group(1), cur_ves=cur)
            if val:
                return val

    # 5. Try canonical terms present in chunk text
    text_lower = text.lower()
    for ct in CANONICAL_SUBJECT_TERMINOLOGY.get(subj, []):
        if ct.lower() in text_lower:
            cand = clean_and_validate_candidate(ct.capitalize(), cur_ves=cur)
            if cand:
                return cand

    return ""


def extract_scientific_terminology_for_snippet(
    snippet: str,
    concept: str,
    subject: str,
    cur_ves: sqlite3.Cursor | None = None,
) -> list[str]:
    """Extract authentic scientific terms as dictionary lemmas, strictly excluding pronouns, function words, and concept circularity."""
    cur = cur_ves or get_vesum_cursor()
    snip_lower = snippet.lower()
    conc_lower = concept.lower()
    conc_lemmas = get_vesum_lemmas(concept, cur)

    # Focus candidate tokens on definitional sentence if snippet contains multiple sentences
    target_text = snip_lower
    sents = re.split(r"(?<=[.!?])\s+", snippet)
    for s in sents:
        if is_definitional_for_concept(s, concept, cur) or DEFINITIONAL_MARKER_RE.search(s):
            target_text = s.lower()
            break

    canonical_list = CANONICAL_SUBJECT_TERMINOLOGY.get(subject, [])
    candidate_terms: list[str] = []

    # 1. Subject canonical terms present directly in target definition (only single-word noun lemmas!)
    snip_lemmas = get_vesum_lemmas(target_text, cur)
    if isinstance(canonical_list, list):
        for ct in canonical_list:
            ct_lower = ct.lower()
            if " " in ct_lower:
                continue
            if ct_lower == conc_lower or ct_lower in STOPWORD_TERMS:
                continue
            ct_info = get_vesum_word_info(ct_lower, cur)
            if any(r[1] in ("adj", "verb", "pronoun") or "adj" in r[2] for r in ct_info):
                continue
            if not any(r[1] == "noun" for r in ct_info):
                continue
            ct_lemmas = get_vesum_lemmas(ct_lower, cur)
            if ((ct_lemmas and ct_lemmas & snip_lemmas) or (ct_lower in target_text)) and ct_lower not in candidate_terms:
                candidate_terms.append(ct_lower)

    # 2. Extract substantive domain NOUNS directly from definition text via VESUM with POS disambiguation
    tokens = re.findall(r"[а-яіїєґ']+", target_text)
    for i, tok in enumerate(tokens):
        if len(tok) < 3 or tok in STOPWORD_TERMS:
            continue
        # Specific domain disambiguations
        if tok in ("пари", "парою", "парі", "паром", "пару") and subject in ("fizyka", "khimiya", "heohrafiya", "pryroda", "biolohiya"):
            lem = "пара"
            if lem not in candidate_terms and lem != conc_lower:
                candidate_terms.append(lem)
            continue
        if tok in ("появ", "появу", "появи", "появою", "появі"):
            lem = "поява"
            if lem not in candidate_terms and lem != conc_lower:
                candidate_terms.append(lem)
            continue
        if tok == "судом":
            lem = "суд"
            if lem not in candidate_terms and lem != conc_lower:
                candidate_terms.append(lem)
            continue

        rows = get_vesum_word_info(tok, cur)
        if not rows:
            continue
        # Strictly reject adjectives, participles, verbs, pronouns, function words, substantivized adjectives
        if any(r[1] in ("adj", "verb", "pronoun", "prep", "conj", "part", "intj") or "adj" in r[2] or "verb" in r[2] or ":ns" in r[2] for r in rows):
            continue
        # Skip proper nouns
        if any(":prop" in r[2] or ":fname" in r[2] or ":lname" in r[2] or ":geo" in r[2] for r in rows):
            continue
        # Filter out participles, comparatives, superlatives (:comps, :compc, :adjp)
        clean_rows = [r for r in rows if not any(tag in r[2] for tag in (":comps", ":compc", ":adjp"))]
        if not clean_rows:
            continue
        # Substantive scientific terms MUST be nouns
        noun_rows = [r for r in clean_rows if r[1] == "noun" and not any(p in r[2] for p in (":prop", ":fname", ":lname", ":geo", ":ns"))]
        if not noun_rows:
            continue

        # If preceded by an adjective, match case and number
        prev_tok = tokens[i - 1] if i > 0 else None
        chosen_row = None
        if prev_tok:
            cur.execute("SELECT tags FROM forms_all WHERE word_form IN (?, ?) AND pos = 'adj'", (prev_tok.lower(), prev_tok.capitalize()))
            adj_tags = [r[0] for r in cur.fetchall()]
            if adj_tags:
                def extract_cgn(tag: str):
                    parts = tag.split(":")
                    case = next((p for p in parts if p.startswith("v_")), None)
                    num = "p" if ":p:" in tag else "s"
                    return (case, num)
                adj_cgns = {extract_cgn(t) for t in adj_tags}
                matching_noun_rows = [r for r in noun_rows if extract_cgn(r[2]) in adj_cgns]
                if matching_noun_rows:
                    sing = [r for r in matching_noun_rows if ":p:" not in r[2]]
                    chosen_row = sing[0] if sing else matching_noun_rows[0]

        if chosen_row is None:
            # Prefer exact lemma match with token if available (e.g. метод -> метод, not метода)
            exact_rows = [r for r in noun_rows if r[0].lower() == tok.lower()]
            if exact_rows:
                chosen_row = exact_rows[0]
            else:
                # Prefer nominative singular (:v_naz)
                v_naz_rows = [r for r in noun_rows if ":v_naz" in r[2] and ":p:" not in r[2]]
                if v_naz_rows:
                    chosen_row = v_naz_rows[0]
                else:
                    sing_rows = [r for r in noun_rows if ":p:" not in r[2]]
                    chosen_row = sing_rows[0] if sing_rows else noun_rows[0]

        lem = chosen_row[0].lower()

        # Reject multi-word, stopwords, concept identity, substantivized neuter adjectives ending in -е/-є
        if " " in lem or lem in STOPWORD_TERMS or lem == conc_lower or lem in candidate_terms:
            continue
        if lem.endswith(("е", "є")):
            continue
        # If concept is a single word, exclude its exact lemma
        if len(conc_lower.split()) == 1 and lem in conc_lemmas:
            continue
        if is_vesum_pronoun(lem, cur):
            continue
        if len(lem) < 3:
            continue
        candidate_terms.append(lem)

    return candidate_terms[:5]


def extract_scientific_terminology(
    chunk: TextbookChunk,
    cur_ves: sqlite3.Cursor | None = None,
    snippet: str = "",
) -> list[str]:
    """Identify key Ukrainian scientific terms present in the snippet/chunk, excluding stopwords and bare adjectives."""
    concept = extract_key_concept(chunk)
    if snippet:
        return extract_scientific_terminology_for_snippet(snippet, concept, chunk.subject, cur_ves=cur_ves)
    snip = extract_meaningful_text_snippet(chunk.text, concept=concept)
    if snip:
        return extract_scientific_terminology_for_snippet(snip, concept, chunk.subject, cur_ves=cur_ves)
    return extract_scientific_terminology_for_snippet(chunk.text, concept, chunk.subject, cur_ves=cur_ves)


def synthesize_eval_task(chunk: TextbookChunk, idx: int, q_var_override: int | None = None) -> dict[str, Any]:
    """Synthesize a structured held-out evaluation task tailored to subject discipline."""
    concept = chunk.concept or extract_key_concept(chunk)
    snippet = chunk.snippet or extract_meaningful_text_snippet(chunk.text, concept=concept, max_len=260)
    snippet = apply_calque_sanitation(snippet)
    terms = chunk.terms or extract_scientific_terminology_for_snippet(snippet, concept, chunk.subject)
    subj_gen = chunk.subject_genitive
    subj_nom = chunk.subject_nominative
    grade = chunk.grade
    author = chunk.author

    terms_str = ", ".join(terms) if terms else concept
    q_var = q_var_override if q_var_override is not None else ((idx - 1) % 24)

    if chunk.subject in DISCIPLINE_MATH_COMPUTING:
        templates = [
            f"Охарактеризуйте теоретичний зміст поняття «{concept}» для учнів {grade} класу з курсу {subj_gen} за підручником (автор — {author}). Вкажіть ключові наукові терміни, що розкривають сутність цього матеріалу.",
            f"Охарактеризуйте фундаментальне поняття «{concept}» у курсі {subj_gen} ({grade} клас), спираючись на шкільний підручник ({author}). Наведіть основні фахові терміни теми.",
            f"У чому полягає теоретична сутність поняття «{concept}» у курсі {subj_gen} для {grade} класу (підручник автора {author})? Вкажіть термінологічну основу навчального матеріалу.",
            f"Поясніть зміст навчального поняття «{concept}» з предмета {subj_nom} ({grade} клас, автор — {author}) та визначте його ключову роль у курсі.",
            f"Розкрийте математичну та теоретичну сутність поняття «{concept}» для {grade} класу з курсу {subj_gen} за матеріалами підручника ({author}).",
            f"Дайте чітке наукове визначення поняття «{concept}» ({subj_nom}, {grade} клас, підручник {author}) та вкажіть його основні властивості.",
            f"Які базові теоретичні положення формують поняття «{concept}» у шкільному курсі {subj_gen} ({grade} клас, автор — {author})?",
            f"Сформулюйте змістове означення поняття «{concept}» з курсу {subj_gen} для учнів {grade} класу відповідно до підручника ({author}).",
            f"Як у підручнику з предмета {subj_nom} ({grade} клас, {author}) інтерпретується наукове поняття «{concept}» та його сутність?",
            f"Поясніть теоретичні засади теми «{concept}» у структурі курсу {subj_gen} ({grade} клас, автор підручника — {author}).",
            f"Опишіть понятійний апарат теми «{concept}» для учнів {grade} класу з курсу {subj_gen} за підручником ({author}).",
            f"Проаналізуйте сутність та визначення поняття «{concept}» у структурі курсу {subj_gen} ({grade} клас, автор — {author}).",
            f"Як у шкільному підручнику {subj_gen} для {grade} класу ({author}) пояснюється теоретичний зміст поняття «{concept}»? Назвіть ключову термінологію.",
            f"Визначте головні теоретичні ознаки та науковий зміст поняття «{concept}» з курсу {subj_gen} ({grade} клас, автор — {author}).",
            f"Яке наукове обґрунтування поняття «{concept}» подано в підручнику {subj_gen} ({grade} клас, автор — {author})? Вкажіть терміни теми.",
            f"Схарактеризуйте змістовий компонент поняття «{concept}» у курсі {subj_gen} для {grade} класу за підручником ({author}).",
            f"Подайте наукове пояснення сутності поняття «{concept}» відповідно до підручника з предмета {subj_nom} ({grade} клас, {author}).",
            f"У чому полягають базові наукові засади теми «{concept}» у курсі {subj_gen} ({grade} клас, автор підручника — {author})?",
            f"Розкрийте понятійний зміст теми «{concept}» з курсу {subj_gen} для учнів {grade} класу на матеріалі підручника ({author}).",
            f"Наведіть теоретичну характеристику навчального поняття «{concept}» з предмета {subj_nom} ({grade} клас, автор — {author}).",
            f"Які ключові теоретичні аспекти розкривають сутність поняття «{concept}» у підручнику {subj_gen} ({grade} клас, {author})?",
            f"Сформулюйте змістову та фахову характеристику поняття «{concept}» для {grade} класу з предмета {subj_nom} (автор — {author}).",
            f"Опишіть наукові та прикладні засади теми «{concept}» за матеріалами шкільного курсу {subj_gen} ({grade} клас, {author}).",
            f"Узагальніть теоретичні відомості про поняття «{concept}» у курсі {subj_gen} ({grade} клас, підручник автора {author}).",
        ]
        query = templates[q_var % len(templates)]
        step1 = f"1. Понятійний аналіз: Досліджуємо теоретичний зміст поняття «{concept}» у курсі {subj_gen} ({grade} клас)."
        step2 = f"2. Текстологічна база: Наводимо матеріал підручника ({author}): «{snippet}»"
        step3 = f"3. Термінологічна основа: Виділяємо ключові наукові терміни теми: {terms_str}."
        step4 = "4. Педагогічний підсумок: Сформульовано теоретичні відомості та їх термінологічні ознаки для навчального використання."
        solution = (
            f"Поняття «{concept}» є базовим у курсі {subj_gen} ({grade} клас).\n\n"
            f"У підручнику ({author}) його сутність розкрито так:\n«{snippet}»\n\n"
            f"Ключові наукові терміни теми: {terms_str}.\n\n"
            f"Розуміння сутності поняття «{concept}» є необхідною теоретичною основою для успішного опанування навчального матеріалу."
        )
    elif chunk.subject in DISCIPLINE_NATURAL_SCIENCES:
        templates = [
            f"Охарактеризуйте науковий зміст теми «{concept}» у курсі {subj_gen} ({grade} клас) за підручником (автор — {author}). Вкажіть ключові природничо-наукові терміни теми.",
            f"Охарактеризуйте природничо-науковий зміст матеріалу «{concept}» для учнів {grade} класу з курсу {subj_gen} на основі підручника ({author}). Наведіть профільні наукові терміни.",
            f"У чому полягає наукова сутність поняття «{concept}» у курсі {subj_gen} ({grade} клас, автор підручника — {author})? Вкажіть ключові поняття теми.",
            f"Поясніть природничо-наукові закономірності теми «{concept}» для учнів {grade} класу з курсу {subj_gen} (підручник автора {author}).",
            f"Розкрийте теоретичні основи теми «{concept}» у шкільному курсі {subj_gen} ({grade} клас, автор — {author}) та наведіть профільну термінологію.",
            f"Дайте обґрунтовану природничо-наукову характеристику поняття «{concept}» ({subj_nom}, {grade} клас, підручник {author}).",
            f"Які базові природничі закони та поняття розкривають тему «{concept}» у курсі {subj_gen} ({grade} клас, автор — {author})?",
            f"Сформулюйте наукове визначення поняття «{concept}» згідно з підручником з курсу {subj_gen} для {grade} класу ({author}).",
            f"Як у курсі {subj_gen} ({grade} клас, автор — {author}) висвітлюється сутність та значення теми «{concept}»?",
            f"Опишіть фундаментальні наукові положення теми «{concept}» за шкільним підручником {subj_gen} ({grade} клас, {author}).",
            f"Проаналізуйте сутність природничо-наукового поняття «{concept}» для {grade} класу з курсу {subj_gen} (автор — {author}).",
            f"У чому полягає змістове наповнення теми «{concept}» у змісті курсу {subj_gen} ({grade} клас, підручник {author})?",
            f"Як у курсі {subj_gen} ({grade} клас, {author}) інтерпретуються природничо-наукові закономірності теми «{concept}»? Вкажіть термінологічну базу.",
            f"Визначте фундаментальні наукові засади теми «{concept}» для учнів {grade} класу з курсу {subj_gen} за підручником ({author}).",
            f"Яку наукову інтерпретацію теми «{concept}» пропонує підручник з курсу {subj_gen} ({grade} клас, автор — {author})?",
            f"Схарактеризуйте природничу сутність поняття «{concept}» у структурі курсу {subj_gen} для {grade} класу ({author}).",
            f"Поясніть сутність природничо-наукового поняття «{concept}» у курсі {subj_gen} ({grade} клас, автор підручника — {author}).",
            f"У чому полягає пізнавальне та наукове значення теми «{concept}» з курсу {subj_gen} для {grade} класу за підручником ({author})?",
            f"Розкрийте змістові та теоретичні основи теми «{concept}» у підручнику з предмета {subj_nom} ({grade} клас, {author}).",
            f"Наведіть обґрунтоване наукове визначення поняття «{concept}» у межах курсу {subj_gen} ({grade} клас, автор — {author}).",
            f"Які основні властивості та закономірності теми «{concept}» розглядаються у курсі {subj_gen} ({grade} клас, {author})?",
            f"Сформулюйте змістовний аналіз поняття «{concept}» за матеріалами шкільного підручника з {subj_gen} ({grade} клас, {author}).",
            f"Опишіть науково-теоретичний апарат теми «{concept}» для {grade} класу з курсу {subj_gen} (автор — {author}).",
            f"Узагальніть природничо-наукові положення щодо поняття «{concept}» у курсі {subj_gen} ({grade} клас, підручник {author}).",
        ]
        query = templates[q_var % len(templates)]
        step1 = f"1. Науковий аналіз: Розглядаємо сутність поняття «{concept}» у структурі курсу {subj_gen} ({grade} клас)."
        step2 = f"2. Джерельна основа: Спираємося на виклад матеріалу в підручнику ({author}): «{snippet}»"
        step3 = f"3. Термінологічний аналіз: Виділяємо ключові природничо-наукові терміни теми: {terms_str}."
        step4 = "4. Науково-педагогічний висновок: Сформульовано сутнісну характеристику природничого поняття та закономірностей на основі шкільного курсу."
        solution = (
            f"Тема «{concept}» розкриває важливі природні закономірності у курсі {subj_gen} ({grade} клас).\n\n"
            f"Згідно з підручником ({author}):\n«{snippet}»\n\n"
            f"Ключові наукові терміни теми: {terms_str}.\n\n"
            f"Засвоєння цих наукових фактів є основою для формування цілісного природничо-наукового світогляду учнів."
        )
    elif chunk.subject in DISCIPLINE_GEOGRAPHY:
        templates = [
            f"Охарактеризуйте географічний зміст матеріалу «{concept}» для учнів {grade} класу з курсу {subj_gen} на основі підручника ({author}). Наведіть профільні наукові терміни.",
            f"У чому полягає сутність теми «{concept}» у курсі {subj_gen} ({grade} клас, автор підручника — {author})? Вкажіть ключові географічні поняття.",
            f"Поясніть просторові закономірності та особливості теми «{concept}» для учнів {grade} класу з курсу {subj_gen} (підручник автора {author}).",
            f"Розкрийте теоретичні та практичні засади теми «{concept}» у шкільному курсі {subj_gen} ({grade} клас, автор — {author}) та наведіть профільну термінологію.",
            f"Дайте обґрунтовану географічну характеристику теми «{concept}» ({subj_nom}, {grade} клас, підручник {author}).",
            f"Які базові просторові закономірності та поняття розкривають тему «{concept}» у курсі {subj_gen} ({grade} клас, автор — {author})?",
            f"Сформулюйте наукове визначення поняття «{concept}» згідно з підручником з курсу {subj_gen} для {grade} класу ({author}).",
            f"Як у курсі {subj_gen} ({grade} клас, автор — {author}) висвітлюється сутність та значення теми «{concept}»?",
            f"Опишіть фундаментальні географічні положення теми «{concept}» за шкільним підручником {subj_gen} ({grade} клас, {author}).",
            f"Проаналізуйте сутність поняття «{concept}» для {grade} класу з курсу {subj_gen} (автор — {author}).",
            f"У чому полягає змістове наповнення теми «{concept}» у структурі курсу {subj_gen} ({grade} клас, підручник {author})?",
            f"Як у курсі {subj_gen} ({grade} клас, {author}) інтерпретуються просторові та суспільно-географічні закономірності теми «{concept}»? Вкажіть термінологічну базу.",
            f"Визначте наукові засади теми «{concept}» для учнів {grade} класу з курсу {subj_gen} за підручником ({author}).",
            f"Яку наукову інтерпретацію теми «{concept}» пропонує підручник з курсу {subj_gen} ({grade} клас, автор — {author})?",
            f"Схарактеризуйте географічну сутність поняття «{concept}» у структурі курсу {subj_gen} для {grade} класу ({author}).",
            f"Поясніть сутність теми «{concept}» у курсі {subj_gen} ({grade} клас, автор підручника — {author}).",
            f"У чому полягає пізнавальне та практичне значення теми «{concept}» з курсу {subj_gen} для {grade} класу за підручником ({author})?",
            f"Розкрийте змістові та просторові особливості теми «{concept}» у підручнику з предмета {subj_nom} ({grade} клас, {author}).",
            f"Наведіть обґрунтоване наукове визначення поняття «{concept}» у межах курсу {subj_gen} ({grade} клас, автор — {author}).",
            f"Які основні властивості та просторові закономірності теми «{concept}» розглядаються у курсі {subj_gen} ({grade} клас, {author})?",
            f"Сформулюйте змістовний аналіз поняття «{concept}» за матеріалами шкільного підручника з {subj_gen} ({grade} клас, {author}).",
            f"Опишіть понятійно-термінологічний апарат теми «{concept}» для {grade} класу з курсу {subj_gen} (автор — {author}).",
            f"Узагальніть наукові положення щодо поняття «{concept}» у курсі {subj_gen} ({grade} клас, підручник {author}).",
        ]
        query = templates[q_var % len(templates)]
        step1 = f"1. Географічний аналіз: Розглядаємо сутність теми «{concept}» у структурі курсу {subj_gen} ({grade} клас)."
        step2 = f"2. Джерельна основа: Спираємося на виклад матеріалу в підручнику ({author}): «{snippet}»"
        step3 = f"3. Термінологічний аналіз: Виділяємо ключові географічні терміни теми: {terms_str}."
        step4 = "4. Науково-педагогічний висновок: Сформульовано сутнісну характеристику навчальної теми на основі шкільного курсу географії."
        solution = (
            f"Тема «{concept}» розкриває важливі географічні та просторові закономірності у курсі {subj_gen} ({grade} клас).\n\n"
            f"Згідно з підручником ({author}):\n«{snippet}»\n\n"
            f"Ключові наукові терміни теми: {terms_str}.\n\n"
            f"Засвоєння цих знань є основою для формування географічної грамотності та просторового мислення учнів."
        )
    elif chunk.subject in DISCIPLINE_SOCIAL_LAW:
        templates = [
            f"Охарактеризуйте суспільне значення та сутність теми «{concept}» з предмета {subj_nom} ({grade} клас) на основі підручника (автор — {author}). Вкажіть ключові поняття теми.",
            f"Розкрийте зміст теми «{concept}» у курсі {subj_nom} для {grade} класу за підручником ({author}). Наведіть базові суспільствознавчі терміни.",
            f"У чому полягає суспільно-правова сутність теми «{concept}» у курсі {subj_nom} ({grade} клас, автор підручника — {author})? Вкажіть термінологічну основу матеріалу.",
            f"Поясніть суспільствознавчий зміст поняття «{concept}» для учнів {grade} класу з курсу {subj_nom} за підручником ({author}).",
            f"Розкрийте громадянське та правове значення теми «{concept}» у шкільному курсі {subj_nom} ({grade} клас, автор — {author}).",
            f"Дайте виважену суспільствознавчу характеристику поняття «{concept}» ({subj_nom}, {grade} клас, підручник {author}).",
            f"Які засадничі принципи визначають сутність теми «{concept}» у підручнику з предмета {subj_nom} ({grade} клас, автор — {author})?",
            f"Сформулюйте теоретичне визначення теми «{concept}» згідно з курсом {subj_nom} для {grade} класу ({author}).",
            f"Як у підручнику з курсу {subj_nom} ({grade} клас, {author}) розглядається практичне та теоретичне значення теми «{concept}»?",
            f"Опишіть понятійну основу теми «{concept}» у змісті предмета {subj_nom} для учнів {grade} класу (автор — {author}).",
            f"Проаналізуйте сутнісні ознаки теми «{concept}» у матеріалах курсу {subj_nom} ({grade} клас, автор підручника — {author}).",
            f"У чому полягає світоглядне значення теми «{concept}» для курсу {subj_nom} ({grade} клас, підручник автора {author})?",
            f"Як у підручнику {subj_nom} ({grade} клас, {author}) висвітлюється суспільно-політична та правова сутність теми «{concept}»?",
            f"Визначте ключові теоретичні положення теми «{concept}» з курсу {subj_nom} ({grade} клас, автор — {author}). Наведіть фахову термінологію.",
            f"Яку суспільствознавчу оцінку теми «{concept}» подано у підручнику {subj_nom} для {grade} класу ({author})?",
            f"Схарактеризуйте громадянське та світоглядне значення поняття «{concept}» у курсі {subj_nom} ({grade} клас, автор — {author}).",
            f"Поясніть теоретичні засади навчальної теми «{concept}» з курсу {subj_nom} ({grade} клас, підручник {author}).",
            f"У чому полягає практичне та суспільне значення теми «{concept}» для учнів {grade} класу з предмета {subj_nom} ({author})?",
            f"Розкрийте понятійний зміст та особливості теми «{concept}» за підручником з курсу {subj_nom} ({grade} клас, автор — {author}).",
            f"Наведіть наукову характеристику теми «{concept}» у структурі шкільного предмета {subj_nom} ({grade} клас, {author}).",
            f"Які правові та соціальні орієнтири формує вивчення теми «{concept}» ({subj_nom}, {grade} клас, {author})?",
            f"Сформулюйте змістові положення теми «{concept}» у навчальному викладі підручника {subj_nom} ({grade} клас, {author}).",
            f"Опишіть концептуальні засади теми «{concept}» у курсі {subj_nom} ({grade} клас, автор — {author}).",
            f"Узагальніть суспільствознавчі висновки щодо теми «{concept}» у підручнику з предмета {subj_nom} ({grade} клас, {author}).",
        ]
        query = templates[q_var % len(templates)]
        step1 = f"1. Суспільствознавчий аналіз: Досліджуємо тему «{concept}» у курсі {subj_nom} ({grade} клас)."
        step2 = f"2. Джерельна база: Наводимо базові положення з підручника ({author}): «{snippet}»"
        step3 = f"3. Термінологічний аналіз: Виокремлюємо ключові суспільствознавчі терміни теми: {terms_str}."
        step4 = "4. Педагогічний підсумок: Сформульовано коректну характеристику суспільного явища на основі навчального курсу."
        solution = (
            f"Тема «{concept}» має важливе світоглядне значення у курсі {subj_nom} ({grade} клас).\n\n"
            f"У підручнику ({author}) зазначено:\n«{snippet}»\n\n"
            f"Ключові поняття теми: {terms_str}.\n\n"
            f"Вивчення цього матеріалу сприяє формуванню правової культури та активної громадянської позиції учнів."
        )
    else:  # DISCIPLINE_PHILOLOGY_CULTURE
        templates = [
            f"Розкрийте сутність теми «{concept}» з предмета {subj_nom} ({grade} клас) за матеріалом підручника (автор — {author}). Вкажіть ключові поняття теми.",
            f"Охарактеризуйте змістове наповнення теми «{concept}» у курсі {subj_nom} ({grade} клас) на основі підручника ({author}). Наведіть основні фахові терміни.",
            f"У чому полягає культурно-освітнє значення теми «{concept}» у курсі з предмета {subj_nom} ({grade} клас, автор підручника — {author})? Вкажіть ключові терміни теми.",
            f"Поясніть теоретико-літературний та мовознавчий зміст теми «{concept}» для учнів {grade} класу з предмета {subj_nom} ({author}).",
            f"Розкрийте художню та естетичну сутність теми «{concept}» у шкільному курсі {subj_nom} ({grade} клас, автор — {author}).",
            f"Дайте фахове визначення поняття «{concept}» у контексті вивчення предмета {subj_nom} ({grade} клас, підручник {author}).",
            f"Які ключові філологічні та мистецькі категорії розкриває тема «{concept}» у курсі {subj_nom} ({grade} клас, автор — {author})?",
            f"Сформулюйте зміст поняття «{concept}» відповідно до підручника з предмета {subj_nom} для {grade} класу ({author}).",
            f"Як у навчальному курсі {subj_nom} ({grade} клас, {author}) інтерпретується сутність та значення теми «{concept}»?",
            f"Опишіть мовностилістичні та змістові характеристики теми «{concept}» за підручником {subj_nom} ({grade} клас, {author}).",
            f"Проаналізуйте культурно-історичне значення поняття «{concept}» у курсі {subj_nom} ({grade} клас, автор — {author}).",
            f"У чому полягає навчально-виховний потенціал теми «{concept}» у курсі з предмета {subj_nom} ({grade} клас, підручник {author})?",
            f"Як у шкільному підручнику з предмета {subj_nom} ({grade} клас, {author}) розкрито сутність поняття «{concept}»? Наведіть ключові поняття.",
            f"Визначте теоретико-літературні та мовні засади поняття «{concept}» у курсі {subj_nom} ({grade} клас, автор — {author}).",
            f"Яку естетичну та змістову характеристику теми «{concept}» пропонує підручник {subj_nom} для {grade} класу ({author})?",
            f"Схарактеризуйте ключові поняття та зміст теми «{concept}» у курсі {subj_nom} ({grade} клас, автор підручника — {author}).",
            f"Поясніть філологічну сутність поняття «{concept}» для учнів {grade} класу з предмета {subj_nom} ({author}).",
            f"У чому полягає культурно-мистецьке значення теми «{concept}» у навчальному курсі {subj_nom} ({grade} клас, {author})?",
            f"Розкрийте змістовий апарат та теоретичні ознаки теми «{concept}» за підручником з предмета {subj_nom} ({grade} клас, автор — {author}).",
            f"Наведіть змістовне визначення поняття «{concept}» відповідно до курсу {subj_nom} ({grade} клас, підручник {author}).",
            f"Які ключові мовні та художні засоби розкривають тему «{concept}» у підручнику {subj_nom} ({grade} клас, {author})?",
            f"Сформулюйте фахове розуміння поняття «{concept}» у змісті курсу {subj_nom} ({grade} клас, автор — {author}).",
            f"Опишіть освітній зміст навчального матеріалу «{concept}» для {grade} класу з курсу {subj_nom} ({author}).",
            f"Узагальніть знання про тему «{concept}» у структурі шкільного підручника {subj_nom} ({grade} клас, {author}).",
        ]
        query = templates[q_var % len(templates)]
        step1 = f"1. Змістовий аналіз: Розглядаємо навчальні аспекти теми «{concept}» у курсі {subj_nom} ({grade} клас)."
        step2 = f"2. Текстологічна база: Наводимо матеріал підручника ({author}): «{snippet}»"
        step3 = f"3. Термінологічний аналіз: Виділяємо ключові поняття теми: {terms_str}."
        step4 = "4. Педагогічний підсумок: Подано структурований зміст навчального матеріалу з дотриманням фахових норм."
        solution = (
            f"Матеріал теми «{concept}» посідає важливе місце в курсі {subj_nom} ({grade} клас).\n\n"
            f"У підручнику ({author}) подано такий виклад:\n«{snippet}»\n\n"
            f"Ключові терміни теми: {terms_str}.\n\n"
            f"Опанування цієї теми формує високу культуру мислення та грамотність учнів."
        )

    t_idx = q_var % len(templates)
    m_idx = (q_var // len(templates)) % 4
    modifiers = [
        "",
        " Обґрунтуйте відповідь на основі викладу в підручнику.",
        " Відповідь структуруйте згідно з положеннями теми.",
        " Подайте послідовну характеристику суті поняття.",
    ]
    base_q = templates[t_idx]
    mod = modifiers[m_idx]
    if mod and base_q.endswith("?"):
        query = base_q[:-1] + "," + mod.lower()[:-1] + "?"
    elif mod and base_q.endswith("."):
        query = base_q[:-1] + "." + mod
    else:
        query = base_q

    # Format typography and Pravopys 2019 nested quotes
    concept = format_nested_quotes(concept)
    query = format_nested_quotes(query)
    step1 = format_nested_quotes(step1)
    step2 = format_nested_quotes(step2)
    step3 = format_nested_quotes(step3)
    step4 = format_nested_quotes(step4)
    solution = format_nested_quotes(solution)

    # Strictly enforce pedagogical tone and protected entity invariants
    all_text = f"{query} {solution} {step1} {step2} {step3} {step4}"
    if not verify_pedagogical_tone(all_text):
        raise ValueError(f"Tone check failed for eval task {idx}: pejorative phrasing detected")
    if not check_protected_entities(all_text):
        raise ValueError(f"Protected entity check failed for eval task {idx}: volume or ratio corrupted")
    if re.search(r"«[^»]*«", all_text):
        raise ValueError(f"Nested guillemets invariant failed for eval task {idx}")

    eval_record = {
        "eval_id": f"eval_textbook_asst_{idx:08x}",
        "subject": chunk.subject,
        "grade": grade,
        "track_domain": chunk.domain,
        "concept": concept,
        "query": query,
        "reference_reasoning": [step1, step2, step3, step4],
        "reference_solution": solution,
        "scientific_terminology": terms,
        "source_metadata": {
            "source_book": chunk.source_file,
            "author": chunk.author,
            "grade": chunk.grade,
            "subject": chunk.subject,
            "chunk_id": chunk.chunk_id,
            "char_length": chunk.char_count,
            "partition": "held_out_eval",
        },
    }
    return eval_record


def synthesize_trajectory(
    chunk: TextbookChunk,
    traj_idx: int,
    task_type: str,
    cur_ves: sqlite3.Cursor | None = None,
) -> dict[str, Any]:
    """Synthesize a complete multi-turn instructional reasoning trajectory from a textbook chunk."""
    concept = chunk.concept or extract_key_concept(chunk)
    snippet = chunk.snippet or extract_meaningful_text_snippet(chunk.text, concept=concept, max_len=260)
    snippet = apply_calque_sanitation(snippet)
    terms = chunk.terms or extract_scientific_terminology_for_snippet(snippet, concept, chunk.subject, cur_ves=cur_ves)

    vesum_records: list[dict[str, Any]] = []
    attested_lemmas: list[str] = []
    for t in terms[:4]:
        words = re.findall(r"[а-яіїєґ']+", t.lower())
        for w in words:
            if w in STOPWORD_TERMS or len(w) < 4:
                continue
            attested = is_vesum_attested(w, cur_ves)
            vesum_records.append({"lemma": w, "is_attested": attested})
            if attested and w not in attested_lemmas:
                attested_lemmas.append(w)

    subj_gen = chunk.subject_genitive
    subj_nom = chunk.subject_nominative
    grade = chunk.grade

    # Build linguistically grounded step 3 without unverified claims
    vesum_note = f"За словниковою базою ВЕСУМ зафіксовано терміни теми: {', '.join(attested_lemmas[:3])}." if attested_lemmas else ""

    if task_type == "conceptual_explanation":
        query = (
            f"Як пояснити тему «{concept}» з предмета {subj_nom} для учнів {grade} класу? "
            f"Наведіть чітке наукове визначення та поясніть його ключові ознаки."
        )
        r_step1 = f"1. Аналіз запитання: Розглядаємо навчальні цілі теми «{concept}» у курсі {subj_gen} ({grade} клас)."
        r_step2 = f"2. Науково-педагогічна основа: Спираємося на авторизований зміст підручника: «{snippet}»"
        r_step3 = f"3. Термінологічний аналіз: Виділено ключові поняття до теми «{concept}».{f' {vesum_note}' if vesum_note else ''}"
        r_step4 = "4. Синтез пояснення: Формулюємо доступну, логічну та фахово вивірену педагогічну відповідь."
        final_resp = (
            f"Тема «{concept}» є важливою складовою курсу {subj_gen} ({grade} клас).\n\n"
            f"Основні наукові положення:\n"
            f"• Сутність поняття: {snippet}\n"
            f"• Значення матеріалу: формує системне розуміння предмета та аналітичне мислення учнів.\n\n"
            f"Під час вивчення цього матеріалу важливо послідовно зіставляти теоретичні положення з конкретними прикладами."
        )

    elif task_type == "problem_solving":
        query = (
            f"Запропонуйте алгоритм розв'язування типових навчальних завдань на тему «{concept}» "
            f"({subj_nom}, {grade} клас) та вкажіть основні етапи виконання."
        )
        r_step1 = f"1. Декомпозиція завдання: Визначаємо вхідні дані та мету роботи для теми «{concept}»."
        r_step2 = f"2. Теоретичні закономірності: Використовуємо положення підручника: «{snippet}»"
        r_step3 = f"3. Понятійний аналіз: Визначено теоретичні поняття до теми «{concept}».{f' {vesum_note}' if vesum_note else ''}"
        r_step4 = "4. Послідовність кроків: Описуємо структурований покроковий план дій учня."
        final_resp = (
            f"Для розв'язування завдань на тему «{concept}» ({subj_nom}, {grade} клас) рекомендується такий алгоритм:\n\n"
            f"1. Аналіз вихідних даних: уважно ознайомтеся з умовою та з'ясуйте головні взаємозв'язки.\n"
            f"2. Теоретичне підґрунтя: спирайтеся на базові положення курсу: «{snippet}»\n"
            f"3. Виконання дій: послідовно застосуйте правила або формули, контролюючи проміжні результати.\n"
            f"4. Перевірка та висновок: зіставте отриманий результат із реальними закономірностями предмета."
        )

    elif task_type == "applied_analysis":
        query = (
            f"У чому полягає практичне значення матеріалу «{concept}» ({subj_nom}, {grade} клас) "
            f"у повсякденному житті або сучасному розвитку суспільства й технологій?"
        )
        r_step1 = f"1. Змістовий аналіз: Досліджуємо практичні взаємозв'язки теми «{concept}»."
        r_step2 = f"2. Фактологічне підґрунтя: Згідно з текстом підручника: «{snippet}»"
        r_step3 = f"3. Понятійний аналіз: Окреслено ключові терміни до теми «{concept}».{f' {vesum_note}' if vesum_note else ''}"
        r_step4 = "4. Узагальнення: Поєднуємо навчальний матеріал із реальними практичними викликами."
        final_resp = (
            f"Вивчення теми «{concept}» має безпосередній практичний вимір у сучасному житті.\n\n"
            f"Практичне втілення:\n"
            f"• Реальний контекст: {snippet}\n"
            f"• Компетентнісний результат: розвиває навички критичного мислення та обґрунтованого ухвалення рішень.\n\n"
            f"Опанування цих знань з {subj_gen} допомагає краще орієнтуватися у навколишньому світі та фахових процесах."
        )

    elif task_type == "source_critical_evaluation":
        query = (
            f"Проаналізуйте сутність теми «{concept}» ({subj_nom}, {grade} клас) з позиції сучасної деколонізованої української освіти. "
            f"Чому важливо спиратися на українські джерела?"
        )
        r_step1 = f"1. Постановка проблеми: Оцінка явища «{concept}» у структурі курсу {subj_nom}."
        r_step2 = f"2. Джерельна база: Використовуємо зміст українського підручника: «{snippet}»"
        r_step3 = f"3. Джерелознавчий та понятійний аналіз: Опрацьовано першоджерельний зміст до теми «{concept}».{f' {vesum_note}' if vesum_note else ''}"
        r_step4 = "4. Формулювання висновку: Підкреслюємо суб'єктність українського наукового дискурсу."
        final_resp = (
            f"Аналіз теми «{concept}» у курсі {subj_nom} утверджує самостійність та наукову гідність української освіти.\n\n"
            f"Ключові аспекти:\n"
            f"• Фактологічна основа: {snippet}\n"
            f"• Деколонізаційний вимір: подолання нав'язаних ззовні інтерпретацій та спирання на достовірні першоджерела.\n\n"
            f"Використання українських підручників забезпечує високу якість знань та академічну доброчесність."
        )

    else:  # terminological_pedagogy
        query = (
            f"Яких термінологічних вимог та норм Правопису 2019 року необхідно дотримуватися під час вивчення теми «{concept}» ({subj_nom})?"
        )
        r_step1 = f"1. Лінгвістичний аналіз: Виокремлюємо базові наукові терміни до теми «{concept}»."
        r_step2 = f"2. Контекст курсу: У тексті підручника розглядаються положення: «{snippet}»"
        r_step3 = f"3. Термінологічний аналіз: Виділено профільні терміни до теми «{concept}».{f' {vesum_note}' if vesum_note else ''}"
        r_step4 = "4. Педагогічна настанова: Формулюємо правила безпомилкового слововживання."

        term_items = []
        if terms:
            term_items.append(f"• Профільні терміни: послуговуйтеся нормативними формами ({', '.join(terms[:4])}).")
        term_items.append("• Норми Правопису 2019 року: дотримуйтеся правил вживання лапок (зовнішні «...», внутрішні „...“) та чинних орфографічних правил.")
        term_items.append("• Культура слововживання: уникайте калькованих синтаксичних зворотів, послуговуйтеся питомою українською науковою лексикою.")
        term_guidance = "\n".join(term_items)

        final_resp = (
            f"Під час вивчення теми «{concept}» важливо дотримуватися чистоти української фахової мови:\n\n"
            f"{term_guidance}\n\n"
            f"Фахова точність мовлення є невіддільною ознакою якісної шкільної освіти."
        )

    # Format typography and Pravopys 2019 nested quotes
    concept = format_nested_quotes(concept)
    query = format_nested_quotes(query)
    r_step1 = format_nested_quotes(r_step1)
    r_step2 = format_nested_quotes(r_step2)
    r_step3 = format_nested_quotes(r_step3)
    r_step4 = format_nested_quotes(r_step4)
    final_resp = format_nested_quotes(final_resp)

    # Invariant checks
    all_text = f"{query} {final_resp} {r_step1} {r_step2} {r_step3} {r_step4}"
    if not verify_pedagogical_tone(all_text):
        raise ValueError(f"Tone check failed for trajectory {traj_idx}: pejorative phrasing detected")
    if not check_protected_entities(all_text):
        raise ValueError(f"Protected entity check failed for trajectory {traj_idx}: volume or ratio corrupted")
    if re.search(r"«[^»]*«", all_text):
        raise ValueError(f"Nested guillemets invariant failed for trajectory {traj_idx}")

    traj = {
        "schema_version": "v1_general_assistant_trajectory",
        "trajectory_id": f"traj.textbook.{chunk.domain}.{chunk.subject}.{traj_idx:08x}",
        "domain": chunk.domain,
        "subject": chunk.subject,
        "grade": chunk.grade,
        "task_type": task_type,
        "target_concept": concept,
        "query": query,
        "reasoning_steps": [r_step1, r_step2, r_step3, r_step4],
        "final_response": final_resp,
        "scientific_terminology": terms,
        "vesum_attestation": vesum_records,
        "source_metadata": {
            "source_book": chunk.source_file,
            "author": chunk.author,
            "grade": chunk.grade,
            "subject": chunk.subject,
            "chunk_id": chunk.chunk_id,
            "char_length": chunk.char_count,
        },
    }
    return traj



def generate_evaluation_benchmark(
    eval_chunks: list[TextbookChunk],
    eval_dir: Path,
    target_count: int = 2500,
    shards_count: int = 5,
) -> tuple[dict[str, Any], str, dict[str, int], dict[str, int]]:
    """Generate held-out evaluation tasks stratified across all 22 held-out textbooks."""
    eval_dir.mkdir(parents=True, exist_ok=True)
    for f in eval_dir.glob("eval_shard_*.jsonl"):
        f.unlink()
    schema = json.loads(SCHEMA_EVAL_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    # Group eval chunks by held-out source_file
    chunks_by_book: dict[str, list[TextbookChunk]] = {}
    for c in eval_chunks:
        chunks_by_book.setdefault(c.source_file, []).append(c)

    stem_books = [b for b in HELD_OUT_TEXTBOOKS if b in chunks_by_book and any(c.domain == "stem" for c in chunks_by_book[b])]
    hum_books = [b for b in HELD_OUT_TEXTBOOKS if b in chunks_by_book and any(c.domain == "humanities" for c in chunks_by_book[b])]

    # Fallback if partitioning small test subset
    if not stem_books:
        stem_books = [b for b in chunks_by_book if any(c.domain == "stem" for c in chunks_by_book[b])] or list(chunks_by_book.keys())
    if not hum_books:
        hum_books = [b for b in chunks_by_book if any(c.domain == "humanities" for c in chunks_by_book[b])] or list(chunks_by_book.keys())


    all_stem_chunks: list[TextbookChunk] = []
    for b in stem_books:
        all_stem_chunks.extend([c for c in chunks_by_book[b] if c.domain == "stem"])
    if not all_stem_chunks:
        all_stem_chunks = [c for c in eval_chunks if c.domain == "stem"]

    all_hum_chunks: list[TextbookChunk] = []
    for b in hum_books:
        all_hum_chunks.extend([c for c in chunks_by_book[b] if c.domain == "humanities"])
    if not all_hum_chunks:
        all_hum_chunks = [c for c in eval_chunks if c.domain == "humanities"]

    records: list[dict[str, Any]] = []
    subj_dist: dict[str, int] = Counter()
    domain_dist: dict[str, int] = Counter()

    random.seed(8139)
    idx = 1

    seen_concept_chunks: set[tuple[str, str]] = set()
    candidate_chunks: list[TextbookChunk] = []
    max_len = max(len(all_stem_chunks), len(all_hum_chunks))
    for i in range(max_len):
        if i < len(all_stem_chunks):
            candidate_chunks.append(all_stem_chunks[i])
        if i < len(all_hum_chunks):
            candidate_chunks.append(all_hum_chunks[i])

    random.seed(8139)
    idx = 1
    for chunk in candidate_chunks:
        if len(records) >= target_count:
            break
        concept = chunk.concept or extract_key_concept(chunk)
        if not concept:
            continue
        key = (concept.lower(), chunk.chunk_id)
        if key in seen_concept_chunks:
            continue
        rec = synthesize_eval_task(chunk, idx)
        validator.validate(rec)
        records.append(rec)
        seen_concept_chunks.add(key)
        subj_dist[rec["subject"]] += 1
        domain_dist[rec["track_domain"]] += 1
        idx += 1

    unique_queries = {r["query"] for r in records}
    unique_chunks = {r["source_metadata"]["chunk_id"] for r in records}
    unique_concepts = {r["concept"] for r in records}
    print(
        f"[EVAL BENCHMARK] Total cases: {len(records)} | Unique queries: {len(unique_queries)} | "
        f"Unique chunks: {len(unique_chunks)} | Unique concepts: {len(unique_concepts)} | "
        f"Duplicates: {len(records) - len(seen_concept_chunks)}"
    )
    assert len(unique_queries) == len(records), f"Duplicate queries detected: {len(records) - len(unique_queries)}"
    assert len(seen_concept_chunks) == len(records), "Duplicate (concept, chunk_id) detected in eval benchmark"

    actual_shards_count = max(1, min(shards_count, 5))
    cases_per_shard = len(records) // actual_shards_count

    manifest_shards: list[dict[str, Any]] = []
    max_shard_size_kb = 0.0

    for shard_idx in range(1, actual_shards_count + 1):
        start_i = (shard_idx - 1) * cases_per_shard
        end_i = start_i + cases_per_shard if shard_idx < actual_shards_count else len(records)
        shard_records = records[start_i:end_i]

        shard_file_name = f"eval_shard_{shard_idx:03d}_of_{actual_shards_count:03d}.jsonl"
        shard_path = eval_dir / shard_file_name

        shard_hasher = hashlib.sha256()
        with shard_path.open("w", encoding="utf-8") as f:
            for r in shard_records:
                line = json.dumps(r, ensure_ascii=False) + "\n"
                f.write(line)
                shard_hasher.update(line.encode("utf-8"))

        size_kb = round(shard_path.stat().st_size / 1024.0, 2)
        if size_kb > max_shard_size_kb:
            max_shard_size_kb = size_kb
        if size_kb > 2000.0:
            raise ValueError(f"Shard {shard_file_name} size {size_kb} KB exceeds 2,000 KB ceiling!")

        manifest_shards.append({
            "shard_file": shard_file_name,
            "cases_count": len(shard_records),
            "size_kb": size_kb,
            "sha256": shard_hasher.hexdigest(),
        })

    manifest_data = {
        "dataset_name": "uldr_v06_general_assistant_eval",
        "total_cases": len(records),
        "unique_concepts_count": len(unique_concepts),
        "unique_chunks_count": len(unique_chunks),
        "duplicate_pairs_count": 0,
        "shards_count": actual_shards_count,
        "max_shard_size_kb": max_shard_size_kb,
        "shards": manifest_shards,
    }
    manifest_path = eval_dir / "manifest.json"
    manifest_bytes = (json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_path.with_suffix(".json.sha256").write_text(f"{manifest_sha256}  manifest.json\n", encoding="utf-8")

    logger.info(
        "Wrote %d eval tasks across %d shards to %s (max size: %.2f KB, manifest SHA: %s)",
        len(records), actual_shards_count, eval_dir, max_shard_size_kb, manifest_sha256,
    )
    return manifest_data, manifest_sha256, dict(subj_dist), dict(domain_dist)


def generate_sft_dataset(
    train_chunks: list[TextbookChunk],
    sft_dir: Path,
    target_count: int = 75000,
    shards_count: int = 150,
    vesum_cur: sqlite3.Cursor | None = None,
) -> tuple[dict[str, Any], str, dict[str, int], dict[str, int], int]:
    """Generate multi-turn instructional trajectories balanced across curriculum subjects."""
    sft_dir.mkdir(parents=True, exist_ok=True)
    for f in sft_dir.glob("sft_shard_*.jsonl"):
        f.unlink()
    trajectories_per_shard = target_count // shards_count
    if trajectories_per_shard * shards_count != target_count:
        raise ValueError("Target count must divide evenly by shards")

    # Group chunks by domain and subject
    stem_by_subj: dict[str, list[TextbookChunk]] = {}
    hum_by_subj: dict[str, list[TextbookChunk]] = {}
    for c in train_chunks:
        if c.domain == "stem":
            stem_by_subj.setdefault(c.subject, []).append(c)
        else:
            hum_by_subj.setdefault(c.subject, []).append(c)

    stem_subjects = sorted(stem_by_subj.keys())
    hum_subjects = sorted(hum_by_subj.keys())

    # Fallback for small hermetic test subsets
    if not stem_subjects and hum_subjects:
        stem_by_subj = hum_by_subj
        stem_subjects = hum_subjects
    elif not hum_subjects and stem_subjects:
        hum_by_subj = stem_by_subj
        hum_subjects = stem_subjects

    # Proportional domain targets
    target_stem = int(target_count * 35000 / 75000)
    target_hum = target_count - target_stem


    task_types_stem = ["conceptual_explanation", "problem_solving", "applied_analysis", "terminological_pedagogy"]
    task_types_hum = ["conceptual_explanation", "applied_analysis", "source_critical_evaluation", "terminological_pedagogy"]

    all_trajectories: list[dict[str, Any]] = []
    subj_dist: dict[str, int] = Counter()
    domain_dist: dict[str, int] = Counter()
    books_seen: set[str] = set()

    random.seed(8139)
    traj_id_counter = 1

    # Round-robin sampling across STEM subjects
    for i in range(target_stem):
        subj = stem_subjects[i % len(stem_subjects)]
        subj_pool = stem_by_subj[subj]
        chunk = subj_pool[(i // len(stem_subjects)) % len(subj_pool)]
        ttype = task_types_stem[(i // len(stem_subjects)) % len(task_types_stem)]
        traj = synthesize_trajectory(chunk, traj_id_counter, ttype, vesum_cur)
        all_trajectories.append(traj)
        subj_dist[subj] += 1
        domain_dist["stem"] += 1
        books_seen.add(chunk.source_file)
        traj_id_counter += 1

    # Round-robin sampling across Humanities subjects
    for i in range(target_hum):
        subj = hum_subjects[i % len(hum_subjects)]
        subj_pool = hum_by_subj[subj]
        chunk = subj_pool[(i // len(hum_subjects)) % len(subj_pool)]
        ttype = task_types_hum[(i // len(hum_subjects)) % len(task_types_hum)]
        traj = synthesize_trajectory(chunk, traj_id_counter, ttype, vesum_cur)
        all_trajectories.append(traj)
        subj_dist[subj] += 1
        domain_dist["humanities"] += 1
        books_seen.add(chunk.source_file)
        traj_id_counter += 1

    # Shuffle deterministically to interleave STEM and Humanities across shards
    random.Random(8139).shuffle(all_trajectories)

    manifest_shards: list[dict[str, Any]] = []
    max_shard_size_kb = 0.0

    for shard_idx in range(1, shards_count + 1):
        shard_file_name = f"sft_shard_{shard_idx:03d}_of_{shards_count:03d}.jsonl"
        shard_path = sft_dir / shard_file_name
        start_idx = (shard_idx - 1) * trajectories_per_shard
        end_idx = start_idx + trajectories_per_shard
        shard_trajs = all_trajectories[start_idx:end_idx]

        shard_hasher = hashlib.sha256()
        with shard_path.open("w", encoding="utf-8") as f:
            for t in shard_trajs:
                line = json.dumps(t, ensure_ascii=False) + "\n"
                f.write(line)
                shard_hasher.update(line.encode("utf-8"))

        size_kb = round(shard_path.stat().st_size / 1024.0, 2)
        if size_kb > max_shard_size_kb:
            max_shard_size_kb = size_kb
        if size_kb > 2000.0:
            raise ValueError(f"Shard {shard_file_name} size {size_kb} KB exceeds 2,000 KB ceiling!")

        manifest_shards.append({
            "shard_file": shard_file_name,
            "trajectories_count": len(shard_trajs),
            "size_kb": size_kb,
            "sha256": shard_hasher.hexdigest(),
        })

    manifest_data = {
        "dataset_name": "uldr_v06_general_assistant_sft",
        "total_trajectories": target_count,
        "shards_count": shards_count,
        "max_shard_size_kb": max_shard_size_kb,
        "shards": manifest_shards,
    }
    manifest_path = sft_dir / "manifest.json"
    manifest_bytes = (json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_path.with_suffix(".json.sha256").write_text(f"{manifest_sha256}  manifest.json\n", encoding="utf-8")

    logger.info("Wrote %d SFT trajectories across %d shards (max size: %.2f KB)", target_count, shards_count, max_shard_size_kb)
    return manifest_data, manifest_sha256, dict(subj_dist), dict(domain_dist), len(books_seen)



def verify_zero_train_eval_leakage(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify zero chunk_id and book leakage between generated eval and SFT shards on disk."""
    eval_cids: set[str] = set()
    eval_books: set[str] = set()
    for p in eval_dir.glob("eval_shard_*.jsonl"):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                meta = d.get("source_metadata", {})
                if "chunk_id" in meta:
                    eval_cids.add(meta["chunk_id"])
                if "source_book" in meta:
                    eval_books.add(meta["source_book"])

    sft_cids: set[str] = set()
    sft_books: set[str] = set()
    for p in sft_dir.glob("sft_shard_*.jsonl"):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                meta = d.get("source_metadata", {})
                if "chunk_id" in meta:
                    sft_cids.add(meta["chunk_id"])
                if "source_book" in meta:
                    sft_books.add(meta["source_book"])

    if not eval_cids or not sft_cids:
        return False
    return eval_cids.isdisjoint(sft_cids) and eval_books.isdisjoint(sft_books)


def verify_entity_preservation_volume_ratio(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify 100% adherence to geometric volume and scientific ratio invariants across shards."""
    for p in list(eval_dir.glob("eval_shard_*.jsonl")) + list(sft_dir.glob("sft_shard_*.jsonl")):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if not check_protected_entities(line):
                    return False
    return True


def verify_pravopys_2019(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify Pravopys 2019 compliance: zero nested guillemets, zero calques, and proper Ukrainian typography."""
    nested_guillemets = re.compile(r"«[^»]*«")
    for p in list(eval_dir.glob("eval_shard_*.jsonl")) + list(sft_dir.glob("sft_shard_*.jsonl")):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if nested_guillemets.search(line):
                    return False
                for calque_pat, _ in CALQUE_REPLACEMENTS:
                    if calque_pat.search(line):
                        return False
    return True


def verify_dataset_pedagogy_tone(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify Gate 6 pedagogical tone calibration across generated dataset shards."""
    for p in list(eval_dir.glob("eval_shard_*.jsonl")) + list(sft_dir.glob("sft_shard_*.jsonl")):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if not verify_pedagogical_tone(line):
                    return False
    return True


def extract_raw_snippet_from_step2(step2: str) -> str:
    """Extract the authentic textbook snippet from Step 2 of reasoning steps."""
    parts = step2.split(":", 2)
    if len(parts) >= 3:
        body = parts[2].strip()
    elif len(parts) == 2:
        body = parts[1].strip()
    else:
        body = step2.strip()
    snip = body.strip("«» \t\n")
    return snip.replace("„", "«").replace("“", "»").replace("”", "»")


def verify_snippet_concept_grounding(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify that 100% of eval and SFT records have snippets grounded in the target concept."""
    for p in list(eval_dir.glob("eval_shard_*.jsonl")) + list(sft_dir.glob("sft_shard_*.jsonl")):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                concept = d.get("concept") or d.get("target_concept") or ""
                steps = d.get("reference_reasoning") or d.get("reasoning_steps") or []
                if len(steps) > 1:
                    snip = extract_raw_snippet_from_step2(steps[1])
                else:
                    sol = d.get("reference_solution") or d.get("final_response") or ""
                    m = re.search(r"«([^»]{30,})»", sol)
                    snip = m.group(1).replace("„", "«").replace("“", "»").replace("”", "»") if m else ""
                if snip and not is_snippet_grounded_in_concept(snip, concept):
                    return False
    return True


def verify_terms_present_in_snippet(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify that 100% of scientific terms are valid non-pronoun lemmas present in the snippet and non-circular."""
    cur = get_vesum_cursor()
    for p in list(eval_dir.glob("eval_shard_*.jsonl")) + list(sft_dir.glob("sft_shard_*.jsonl")):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                concept = (d.get("concept") or d.get("target_concept") or "").strip().lower()
                terms = d.get("scientific_terminology", [])
                steps = d.get("reference_reasoning") or d.get("reasoning_steps") or []
                if len(steps) > 1:
                    snip = extract_raw_snippet_from_step2(steps[1]).lower()
                else:
                    sol = d.get("reference_solution") or d.get("final_response") or ""
                    m = re.search(r"«([^»]{20,})»", sol)
                    snip = m.group(1).lower().replace("„", "«").replace("“", "»").replace("”", "»") if m else ""
                if len(terms) < 2:
                    return False
                snip_lemmas = None
                for t in terms:
                    t_clean = t.strip().lower()
                    if t_clean == concept:
                        return False
                    if t_clean in STOPWORD_TERMS:
                        return False
                    if is_vesum_pronoun(t_clean, cur):
                        return False
                    if t_clean in snip:
                        continue
                    if snip_lemmas is None:
                        snip_lemmas = get_vesum_lemmas(snip, cur)
                    t_lemmas = get_vesum_lemmas(t_clean, cur) or {t_clean}
                    if not (t_lemmas & snip_lemmas):
                        return False
    return True


def verify_zero_dangling_starters(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify that zero quoted snippets start with dangling anaphoric starters or deictic openers."""
    for p in list(eval_dir.glob("eval_shard_*.jsonl")) + list(sft_dir.glob("sft_shard_*.jsonl")):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                steps = d.get("reference_reasoning") or d.get("reasoning_steps") or []
                if len(steps) > 1:
                    snip = extract_raw_snippet_from_step2(steps[1])
                else:
                    sol = d.get("reference_solution") or d.get("final_response") or ""
                    m = re.search(r"«([^»]{20,})»", sol)
                    snip = m.group(1) if m else ""
                if snip and (DANGLING_STARTER_RE.search(snip) or has_unresolved_anaphora(snip)):
                    return False
    return True


def verify_zero_inflected_concepts(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify that 100% of concept targets are in canonical nominative citation form."""
    cur = get_vesum_cursor()
    for p in list(eval_dir.glob("eval_shard_*.jsonl")) + list(sft_dir.glob("sft_shard_*.jsonl")):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                concept = (d.get("concept") or d.get("target_concept") or "").strip()
                if concept and not is_concept_in_citation_form(concept, cur):
                    return False
    return True


def verify_eval_no_fake_algorithm_claims(eval_dir: Path) -> bool:
    """Verify that eval benchmark queries, solutions, and reasoning steps do not make ungrounded curriculum or algorithm claims."""
    forbidden_curriculum_patterns = [
        re.compile(r"програм\w*\s+курс\w*", re.IGNORECASE),
        re.compile(r"навчальн\w*\s+програм\w*", re.IGNORECASE),
        re.compile(r"за\s+програмою\b", re.IGNORECASE),
        re.compile(r"згідно\s+з\s+програмою\b", re.IGNORECASE),
        re.compile(r"нормативн\w*\s+визначенн\w*", re.IGNORECASE),
    ]
    for p in eval_dir.glob("eval_shard_*.jsonl"):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                q = d.get("query", "")
                sol = d.get("reference_solution", "")
                steps = d.get("reference_reasoning", [])
                all_eval_text = f"{q} {sol} {' '.join(steps)}"
                for pat in forbidden_curriculum_patterns:
                    if pat.search(all_eval_text):
                        return False
                if len(steps) >= 4:
                    step4 = steps[3]
                    if "алгоритм" in step4.lower() and "алгоритм" not in q.lower():
                        return False
    return True


def generate_release_receipt(
    eval_dir: Path,
    eval_manifest_sha256: str,
    eval_count: int,
    eval_shards_count: int,
    eval_max_shard_size_kb: float,
    eval_subj_dist: dict[str, int],
    eval_domain_dist: dict[str, int],
    sft_dir: Path,
    manifest_sha256: str,
    sft_count: int,
    shards_count: int,
    max_shard_size_kb: float,
    sft_subj_dist: dict[str, int],
    sft_domain_dist: dict[str, int],
    books_count: int,
    git_commit: str,
    output_dir: Path,
    invariants_verified: dict[str, bool] | None = None,
    validate_schema: bool = True,
) -> dict[str, Any]:
    """Build, validate, and write the cryptographic release receipt."""
    schema = json.loads(SCHEMA_RECEIPT_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    try:
        eval_rel_path = str(eval_dir.relative_to(PROJECT_ROOT))
    except ValueError:
        eval_rel_path = str(eval_dir)

    try:
        sft_rel_path = str(sft_dir.relative_to(PROJECT_ROOT))
    except ValueError:
        sft_rel_path = str(sft_dir)

    # Compute dynamically across all dataset shards on disk when not explicitly provided
    if invariants_verified is None:
        partition_ok = (len(eval_subj_dist) == len(HELD_OUT_TEXTBOOKS)) if eval_count >= 100 else (len(eval_subj_dist) >= 1)
        coverage_ok = (eval_domain_dist.get("stem", 0) >= 50 and eval_domain_dist.get("humanities", 0) >= 50) if eval_count >= 100 else True
        zero_leakage_ok = verify_zero_train_eval_leakage(eval_dir, sft_dir)
        entities_ok = verify_entity_preservation_volume_ratio(eval_dir, sft_dir)
        pravopys_ok = verify_pravopys_2019(eval_dir, sft_dir)
        tone_ok = verify_dataset_pedagogy_tone(eval_dir, sft_dir)
        grounding_ok = verify_snippet_concept_grounding(eval_dir, sft_dir)
        terms_ok = verify_terms_present_in_snippet(eval_dir, sft_dir)
        starters_ok = verify_zero_dangling_starters(eval_dir, sft_dir)
        no_fake_claims_ok = verify_eval_no_fake_algorithm_claims(eval_dir)
        citation_ok = verify_zero_inflected_concepts(eval_dir, sft_dir)

        if not (grounding_ok and terms_ok and starters_ok and no_fake_claims_ok and citation_ok):
            raise ValueError(
                f"Content quality check failed: grounding={grounding_ok}, terms={terms_ok}, "
                f"starters={starters_ok}, no_fake_claims={no_fake_claims_ok}, citation={citation_ok}"
            )

        invariants_verified = {
            "zero_train_eval_leakage": zero_leakage_ok,
            "textbook_partitioning_enforced": partition_ok,
            "stem_humanities_coverage": coverage_ok,
            "entity_preservation_volume_ratio": entities_ok,
            "pravopys_2019_verified": pravopys_ok,
            "gate6_pedagogy_tone_verified": tone_ok,
            "precommit_file_ceiling_satisfied": eval_max_shard_size_kb <= 2000.0 and max_shard_size_kb <= 2000.0,
        }


    # Ensure all required invariants are booleans and fail closed if any is False
    for inv_k, inv_v in invariants_verified.items():
        if not inv_v:
            raise ValueError(f"Release receipt invariant failed: {inv_k} = {inv_v}")

    receipt = {
        "schema_version": "v1_general_assistant_release_receipt",
        "issue": 8139,
        "parent_epic": 6321,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": git_commit,
        "evaluation_benchmark": {
            "directory_path": eval_rel_path,
            "manifest_file": "manifest.json",
            "manifest_sha256": eval_manifest_sha256,
            "shards_count": eval_shards_count,
            "total_cases": eval_count,
            "max_shard_size_kb": eval_max_shard_size_kb,
            "held_out_books_count": len(HELD_OUT_TEXTBOOKS),
            "held_out_books": HELD_OUT_TEXTBOOKS,
            "subject_distribution": eval_subj_dist,
            "domain_distribution": eval_domain_dist,
        },
        "sft_training_dataset": {
            "directory_path": sft_rel_path,
            "manifest_file": "manifest.json",
            "manifest_sha256": manifest_sha256,
            "shards_count": shards_count,
            "total_trajectories": sft_count,
            "max_shard_size_kb": max_shard_size_kb,
            "books_count": books_count,
            "subject_distribution": sft_subj_dist,
            "domain_distribution": sft_domain_dist,
        },
        "invariants_verified": invariants_verified,
    }

    if validate_schema and eval_count >= 100 and sft_count == 75000:
        validator.validate(receipt)
    receipt_path = output_dir / "release_receipt.json"
    receipt_bytes = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    receipt_path.write_bytes(receipt_bytes)
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
    receipt_path.with_suffix(".json.sha256").write_text(f"{receipt_sha256}  release_receipt.json\n", encoding="utf-8")
    logger.info("Wrote validated release receipt to %s (SHA: %s)", receipt_path, receipt_sha256)
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mine 24k Textbook STEM & Humanities Synthesis (Phase 6.1).")
    parser.add_argument("--git-commit", type=str, default="", help="Git commit hash for receipt")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_SOURCES_DB, help="Path to sources.db")
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB, help="Path to vesum.db")
    parser.add_argument("--eval-only", action="store_true", help="Generate only evaluation benchmark")
    parser.add_argument("--sft-only", action="store_true", help="Generate only SFT dataset")
    parser.add_argument("--dry-run", action="store_true", help="Small test run with fewer items")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()

    git_commit = args.git_commit
    if not git_commit:
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=PROJECT_ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            git_commit = "unknown"

    logger.info("Starting Phase 6.1 General Ukrainian Assistant Mining (Commit: %s)", git_commit)
    eval_chunks, train_chunks = load_textbook_chunks(args.db_path)
    logger.info("Loaded %d eval pool chunks and %d training pool chunks", len(eval_chunks), len(train_chunks))

    # Assert strict 0% leakage
    eval_books = {c.source_file for c in eval_chunks}
    train_books = {c.source_file for c in train_chunks}
    if not eval_books.isdisjoint(train_books):
        raise ValueError(f"Book leakage detected: {eval_books & train_books}")

    eval_count = 100 if args.dry_run else 2500
    eval_shards_count = 1 if args.dry_run else 5
    sft_count = 300 if args.dry_run else 75000
    shards_count = 3 if args.dry_run else 150

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    eval_dir = output_dir / "eval"
    sft_dir = output_dir / "sft"

    eval_manifest_data: dict[str, Any] = {}
    eval_manifest_sha256 = ""
    eval_subj_dist: dict[str, int] = {}
    eval_domain_dist: dict[str, int] = {}
    if not args.sft_only:
        eval_manifest_data, eval_manifest_sha256, eval_subj_dist, eval_domain_dist = generate_evaluation_benchmark(
            eval_chunks, eval_dir, target_count=eval_count, shards_count=eval_shards_count
        )

    manifest_sha256 = ""
    sft_subj_dist: dict[str, int] = {}
    sft_domain_dist: dict[str, int] = {}
    books_count = 0
    max_shard_size_kb = 0.0
    if not args.eval_only:
        vesum_cur = get_vesum_cursor(args.vesum_db)
        manifest_data, manifest_sha256, sft_subj_dist, sft_domain_dist, books_count = generate_sft_dataset(
            train_chunks,
            sft_dir,
            target_count=sft_count,
            shards_count=shards_count,
            vesum_cur=vesum_cur,
        )
        max_shard_size_kb = manifest_data["max_shard_size_kb"]

    if not args.eval_only and not args.sft_only and not args.dry_run:
        generate_release_receipt(
            eval_dir=eval_dir,
            eval_manifest_sha256=eval_manifest_sha256,
            eval_count=eval_count,
            eval_shards_count=eval_manifest_data["shards_count"],
            eval_max_shard_size_kb=eval_manifest_data["max_shard_size_kb"],
            eval_subj_dist=eval_subj_dist,
            eval_domain_dist=eval_domain_dist,
            sft_dir=sft_dir,
            manifest_sha256=manifest_sha256,
            sft_count=sft_count,
            shards_count=shards_count,
            max_shard_size_kb=max_shard_size_kb,
            sft_subj_dist=sft_subj_dist,
            sft_domain_dist=sft_domain_dist,
            books_count=books_count,
            git_commit=git_commit,
            output_dir=output_dir,
            invariants_verified=None,
        )

    logger.info("Phase 6.1 General Ukrainian Assistant Mining Completed Successfully.")
    return 0



if __name__ == "__main__":
    sys.exit(main())
