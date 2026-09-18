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
from dataclasses import dataclass
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
DISCIPLINE_NATURAL_SCIENCES = {"fizyka", "khimiya", "biolohiya", "astronomiya", "heohrafiya", "pryroda", "ya_doslidzhuiu_svit"}
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
    "встановіть", "з'ясуйте", "зясуйте",
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
    "розфарбуй", "добери", "встанови", "з'ясуй", "зясуй",
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
    "heometriya": ["теорема Піфагора", "об'єм циліндра", "об'єм піраміди", "об'єм конуса", "об'єм кулі", "відношення площ", "відношення величин", "вектор", "трикутник", "паралелограм", "трапеція", "синус", "косинус", "тангенс", "координати", "відрізок", "кут"],
    "matematyka": ["числова множина", "десятковий дріб", "відсоток", "пропорція", "ділення", "множення", "відношення чисел", "координатна пряма", "натуральне число", "звичайний дріб"],
    "fizyka": ["прискорювач", "заломлення", "відбиття", "густина", "сила тяжіння", "імпульс", "кінетична енергія", "електричний струм", "напруга", "опір", "тиск", "робота", "потужність", "теплота", "магнітне поле"],
    "khimiya": ["водень", "кисень", "вуглець", "азот", "сірка", "залізо", "сульфатна кислота", "хлоридна кислота", "нітратна кислота", "періодичний закон", "електроліз", "оксид", "основа", "кислота", "сіль", "молярна маса", "розчин", "валентність"],
    "biolohiya": ["клітина", "хромосома", "фотосинтез", "метаболізм", "генотип", "екосистема", "мембрана", "фермент", "біорізноманіття", "орган", "тканина", "розмноження", "спадковість", "мінливість"],
    "informatyka": ["алгоритм", "масив", "цикл", "розгалуження", "база даних", "інтерфейс", "функція", "кодування інформації", "змінна", "програма", "оператор", "мережа", "файл"],
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
    r"^(?:записан\w*\s+рівність|цю\s+рівність|цю\s+формулу|цей\s+вираз|цей\s+малюнок|цей\s+рисунок|цей\s+графік|"
    r"звідси\b|у\s+таких\s+випадках|аналогічн\w*|тому\s+для|тому\b|отже\b|тоді\s+маємо|тоді\s+як|оскільки\b|"
    r"наприклад\b|позначимо\b|нехай\b|підставивши\b|помноживши\b|поділивши\b|доведемо\b|розв'язання\b|розглянемо\s+приклад|"
    r"так\w*\s+рівність|так\w*\s+послідовність|так\w*\s+вираз|так\w*\s+чином\b|"
    r"крім\s+того\b|зокрема\b|відповідно\b|проте\b|однак\b|"
    r"як\s+бачимо\b|як\s+відомо\b|як\s+зазначалося\b|вони\b|він\b|вона\b|воно\b)\b",
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


# Typography & Calque Sanitation
APOSTROPHE_RE = re.compile(r"['’ʼ´`]")
HYPHEN_BREAK_RE = re.compile(r"([а-яіїєґА-ЯІЇЄҐa-zA-Z])-[\s\r\n]+([а-яіїєґА-ЯІЇЄҐa-zA-Z])")
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
    "предмет", "предмета", "предмету", "робота", "роботи", "роботу",
    "параграф", "параграфа", "частина", "частини", "частину",
    "питання", "відповідь", "відповіді", "відповіддю",
    "школа", "школи", "школу", "курс", "курсу", "курсі",
    "урок", "уроку", "уроці", "поняття", "приклад", "прикладу", "значення",
    "автор", "автори", "авторів", "підсумок", "підсумки", "правило", "правила",
    "число", "числа", "чисел", "числу", "числом", "член", "члена", "членів",
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



def normalize_apostrophes(text: str) -> str:
    """Standardize apostrophe variants to ASCII apostrophe."""
    return APOSTROPHE_RE.sub("'", text)


def dehyphenate_text(text: str) -> str:
    """Join line-broken hyphenated words."""
    return HYPHEN_BREAK_RE.sub(r"\1\2", text)


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



def sanitize_typography(text: str) -> str:
    """Sanitize spacing, apostrophes, and terminal punctuation."""
    t = normalize_apostrophes(text)
    t = dehyphenate_text(t)
    t = sanitize_ip_addresses(t)
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

    @property
    def domain(self) -> str:
        return "stem" if self.subject in STEM_SUBJECTS else "humanities"

    @property
    def subject_genitive(self) -> str:
        return UKRAINIAN_SUBJECT_GENITIVE.get(self.subject, self.subject)

    @property
    def subject_nominative(self) -> str:
        return UKRAINIAN_SUBJECT_NOMINATIVE.get(self.subject, self.subject.capitalize())


def is_clean_content_chunk(chunk: TextbookChunk) -> bool:
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
    if len(re.findall(r"^\s*\d+[\.\)]\s+", t, re.MULTILINE)) >= 3:
        return False
    if len(FIGURE_REF_RE.findall(t)) >= 2 and len(t) < 800:
        return False
    if not verify_pedagogical_tone(t):
        return False
    if any(m in t for m in frontmatter_markers):
        return False
    concept = extract_key_concept(chunk)
    if not concept:
        return False
    snippet = extract_meaningful_text_snippet(chunk.text, concept=concept)
    if not snippet or len(snippet) < 50:
        return False
    terms = extract_scientific_terminology_for_snippet(snippet, concept, chunk.subject)
    return bool(terms)


def load_textbook_chunks(db_path: Path) -> tuple[list[TextbookChunk], list[TextbookChunk]]:
    """Load textbook chunks from sources.db, partitioned into eval pool and train pool with strict text firewall."""
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
        if not is_clean_content_chunk(chunk):
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


def is_snippet_grounded_in_concept(snippet: str, concept: str) -> bool:
    """Verify that the snippet is strictly grounded in the concept, without contradiction, dangling starter, or forward/backward pointer."""
    if not snippet or not concept:
        return False
    if check_concept_contradiction(snippet, concept):
        return False
    if DANGLING_STARTER_RE.search(snippet):
        return False
    if FORWARD_BACKWARD_REF_RE.search(snippet):
        return False

    snip_lower = snippet.lower()
    conc_lower = concept.lower()
    snip_words = set(re.findall(r"[а-яіїєґ']+", snip_lower))
    conc_words = set(re.findall(r"[а-яіїєґ']+", conc_lower))

    # Significant content words with len >= 3 (e.g. сон, рух, кут, газ, іон, світ, тіло)
    words = [w for w in re.findall(r"[а-яіїєґ']+", conc_lower) if w not in STOPWORD_TERMS and len(w) >= 3]
    if not words:
        return True

    # Primary entity check: the leading non-stopword of the concept (e.g. "сон" in "Сон як прояв біоритмів організму")
    # MUST be present in the snippet
    primary_word = words[0]
    primary_stem = primary_word[:len(primary_word) - 1] if len(primary_word) > 3 else primary_word
    primary_matched = any(sw.startswith(primary_stem) for sw in snip_words) or (primary_word in snip_lower)
    if not primary_matched:
        return False

    matched = 0
    for w in words:
        stem = w[:len(w) - 1] if len(w) > 3 else w
        if stem in snip_lower or any(sw.startswith(stem) for sw in snip_words):
            matched += 1

    if len(words) == 1:
        return matched == 1

    for m1, m2 in CONTRADICTORY_MODIFIER_PAIRS:
        def _has_ex(w_set: set[str], s1: str, s2: str) -> bool:
            return any(w.startswith(s1) and not w.startswith(s2) for w in w_set)

        if _has_ex(conc_words, m1, m2) and not _has_ex(snip_words, m1, m2):
            return False
        if any(w.startswith(m2) for w in conc_words) and not any(w.startswith(m2) for w in snip_words):
            return False

    return matched >= 1


def extract_meaningful_text_snippet(
    text: str,
    concept: str = "",
    terms: list[str] | None = None,
    max_len: int = 260,
) -> str:
    """Extract a coherent, grounded contiguous prose paragraph ending on a sentence boundary without exercises or questions."""
    clean = sanitize_typography(text)
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
        if DANGLING_STARTER_RE.search(s):
            return -100
        if FORWARD_BACKWARD_REF_RE.search(s):
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
        for i, s in enumerate(sents):
            s = s.strip()
            if not s or not re.match(r"^[«„\"А-ЯІЇЄҐ]", s):
                continue
            # Check single sentence
            sc = _sentence_score(s)
            if sc > best_score:
                best_score = sc
                best_cand = s
            # Check combining two short adjacent sentences in the same block
            if len(s) < 75 and i + 1 < len(sents):
                s_next = sents[i + 1].strip()
                s_comb = (s + " " + s_next).strip()
                sc_comb = _sentence_score(s_comb)
                if sc_comb > best_score:
                    best_score = sc_comb
                    best_cand = s_comb

    # Require substantive score (definitional or grounded)
    if best_score >= 10 and best_cand:
        if concept and not is_snippet_grounded_in_concept(best_cand, concept):
            return ""
        if DANGLING_STARTER_RE.search(best_cand):
            return ""
        if FORWARD_BACKWARD_REF_RE.search(best_cand):
            return ""
        return best_cand.rstrip(". ") + "."

    return ""


def clean_and_validate_candidate(cand: str) -> str | None:
    """Clean and validate a candidate concept, rejecting exercises, dangling punctuation, and mid-word cuts."""
    c = cand.strip()
    c = normalize_apostrophes(c)
    c = re.sub(r"[\s\.\d—–-]+$", "", c).strip()
    if not c or len(c) < 4:
        return None
    # Reject terminal dangling punctuation/apostrophes
    if c.endswith(("'", "’", "ʼ", "`", "-", "—", "–", "…", ".")):
        return None
    for delim in [":", ";", "(", " - це", " — це", " – це"]:
        if delim in c:
            part = c.split(delim)[0].strip()
            if len(part) >= 4:
                c = part
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
    return c


def extract_key_concept(chunk: TextbookChunk | str, title: str = "", subject: str = "") -> str:
    """Extract the central concept grounded directly in chunk text without imperative exercise noise."""
    if isinstance(chunk, TextbookChunk):
        text = chunk.text
        chunk_title = chunk.title
        subj = chunk.subject
    else:
        text = chunk
        chunk_title = title
        subj = subject

    lines = [normalize_apostrophes(line.strip()) for line in text.splitlines() if line.strip()]
    for line in lines[:15]:
        m_num_sec = re.match(r"^\d+[\.\s]+([А-ЯІЇЄҐ][а-яіїєґ0-9\s'-]{3,40})", line)
        if m_num_sec:
            val = clean_and_validate_candidate(m_num_sec.group(1))
            if val:
                return val
        m_sec = re.match(r"^§\s*\d+[\.\s]+([^.\n?]+)", line, re.IGNORECASE)
        if m_sec:
            val = clean_and_validate_candidate(m_sec.group(1))
            if val:
                return val
        m_tema = re.match(r"^(?:тема|розділ)\s*\d*[\.\s]+([^.\n?]+)", line, re.IGNORECASE)
        if m_tema:
            val = clean_and_validate_candidate(m_tema.group(1))
            if val:
                return val
        m_def = re.match(r"^([А-ЯІЇЄҐ][а-яіїєґa-zA-Z\s'-]{2,35})\s+[—–-]\s+це\b", line)
        if m_def:
            val = clean_and_validate_candidate(m_def.group(1))
            if val:
                return val

    # Try chunk title if meaningful
    if chunk_title and not chunk_title.lower().startswith("сторінка"):
        val = clean_and_validate_candidate(chunk_title)
        if val:
            return val

    # Try bold/heading line grounded in chunk
    for line in lines[:10]:
        m_bold = re.match(r"^([А-ЯІЇЄҐ][а-яіїєґ\s'-]{4,40})$", line)
        if m_bold:
            val = clean_and_validate_candidate(m_bold.group(1))
            if val:
                return val

    # Try canonical terms present in chunk text
    text_lower = text.lower()
    for ct in CANONICAL_SUBJECT_TERMINOLOGY.get(subj, []):
        stem = ct[:len(ct) - 1] if len(ct) > 4 else ct
        if stem in text_lower:
            return ct.capitalize()

    return ""


def extract_scientific_terminology_for_snippet(
    snippet: str,
    concept: str,
    subject: str,
    cur_ves: sqlite3.Cursor | None = None,
) -> list[str]:
    """Extract terms strictly guaranteed to appear in snippet or concept."""
    cur = cur_ves or get_vesum_cursor()

    def _get_lemma(word: str) -> str:
        if cur is None:
            return word
        try:
            cur.execute("SELECT lemma FROM forms_all WHERE word_form = ? LIMIT 1", (word,))
            row = cur.fetchone()
            return row[0] if row else word
        except Exception:
            return word

    def _has_noun_reading(word: str) -> bool:
        if cur is None:
            return not word.endswith(("ий", "ій", "а", "я", "е", "є", "их", "і", "им", "ій", "ою", "ими"))
        try:
            cur.execute("SELECT tags FROM forms_all WHERE word_form = ?", (word,))
            rows = cur.fetchall()
            if not rows:
                return True
            return any(r[0].startswith("noun") for r in rows)
        except Exception:
            return True

    snip_lower = snippet.lower()
    conc_lower = concept.lower()
    candidate_terms: list[str] = []

    # 1. Subject canonical terms present directly in snippet
    canonical_list = CANONICAL_SUBJECT_TERMINOLOGY.get(subject, [])
    if isinstance(canonical_list, list):
        for ct in canonical_list:
            ct_words = ct.split()
            if len(ct_words) == 1:
                stem = ct[:len(ct) - 1] if len(ct) > 4 else ct
                for sw in re.findall(r"[а-яіїєґ']+", snip_lower):
                    if sw.startswith(stem) and sw not in STOPWORD_TERMS and len(sw) >= 4 and sw not in candidate_terms:
                        candidate_terms.append(sw)
            else:
                if ct in snip_lower and ct not in candidate_terms:
                    candidate_terms.append(ct)

    # 2. Extract substantive domain nouns directly from snippet
    for w in re.findall(r"[а-яіїєґ']+", snip_lower):
        if len(w) >= 4 and w not in STOPWORD_TERMS and w != conc_lower and _has_noun_reading(w) and w not in candidate_terms:
            candidate_terms.append(w)

    # Note: Do not append concept itself to candidate terms (eliminates circularity)

    # 3. Filter candidate terms: reject bare adjectives and stopwords
    filtered_terms: list[str] = []
    for t in candidate_terms:
        words = [w for w in re.findall(r"[а-яіїєґ']+", t.lower()) if w not in STOPWORD_TERMS and len(w) >= 4]
        if not words:
            continue
        if len(words) == 1 and not _has_noun_reading(words[0]):
            continue
        head_word = words[-1]
        if not _has_noun_reading(head_word):
            continue
        filtered_terms.append(t)

    # 4. Strict subset deduplication
    deduped_subset: list[str] = []
    for t in filtered_terms:
        t_words = set(re.findall(r"[а-яіїєґ']+", t.lower()))
        is_sub = False
        for other in filtered_terms:
            if other == t:
                continue
            other_words = set(re.findall(r"[а-яіїєґ']+", other.lower()))
            if t_words.issubset(other_words) and len(t) < len(other):
                is_sub = True
                break
            if t.lower() in other.lower() and len(t) < len(other):
                is_sub = True
                break
        if not is_sub:
            deduped_subset.append(t)

    # 5. Deduplicate by head-word lemma
    final_terms: list[str] = []
    seen_lemmas: set[str] = set()
    for t in deduped_subset:
        words = [w for w in re.findall(r"[а-яіїєґ']+", t.lower()) if w not in STOPWORD_TERMS and len(w) >= 4]
        if not words:
            continue
        head_word = words[-1]
        lemma = _get_lemma(head_word)
        if lemma in seen_lemmas:
            continue
        seen_lemmas.add(lemma)
        final_terms.append(t)

    # 6. Strict containment verification: EVERY term must be in snippet and NOT identical to concept
    verified_terms = [
        t for t in final_terms
        if t.lower() in snip_lower and t.lower().strip() != conc_lower.strip()
    ]
    return verified_terms[:4]


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


def synthesize_eval_task(chunk: TextbookChunk, idx: int) -> dict[str, Any]:
    """Synthesize a structured held-out evaluation task tailored to subject discipline."""
    concept = extract_key_concept(chunk)
    snippet = extract_meaningful_text_snippet(chunk.text, concept=concept, max_len=260)
    snippet = apply_calque_sanitation(snippet)
    terms = extract_scientific_terminology_for_snippet(snippet, concept, chunk.subject)
    subj_gen = chunk.subject_genitive
    subj_nom = chunk.subject_nominative
    grade = chunk.grade
    author = chunk.author

    terms_str = ", ".join(terms) if terms else concept
    q_var = idx % 3

    if chunk.subject in DISCIPLINE_MATH_COMPUTING:
        if q_var == 0:
            query = (
                f"Охарактеризуйте теоретичний зміст поняття «{concept}» "
                f"для учнів {grade} класу з курсу {subj_gen} за підручником (автор — {author}). "
                f"Вкажіть ключові наукові терміни, що розкривають сутність цього матеріалу."
            )
        elif q_var == 1:
            query = (
                f"Охарактеризуйте фундаментальне поняття «{concept}» у курсі {subj_gen} ({grade} клас), "
                f"спираючись на шкільний підручник ({author}). Наведіть основні фахові терміни теми."
            )
        else:
            query = (
                f"У чому полягає теоретична сутність поняття «{concept}» у курсі {subj_gen} для {grade} класу "
                f"(підручник автора {author})? Вкажіть термінологічну основу навчального матеріалу."
            )
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
        if q_var == 0:
            query = (
                f"Охарактеризуйте науковий зміст теми «{concept}» "
                f"у курсі {subj_gen} ({grade} клас) за підручником (автор — {author}). "
                f"Вкажіть ключові природничо-наукові терміни теми."
            )
        elif q_var == 1:
            query = (
                f"Охарактеризуйте природничо-науковий зміст матеріалу «{concept}» для учнів {grade} класу "
                f"з курсу {subj_gen} на основі підручника ({author}). Наведіть профільні наукові терміни."
            )
        else:
            query = (
                f"У чому полягає наукова сутність явища «{concept}» у курсі {subj_gen} "
                f"({grade} клас, автор підручника — {author})? Вкажіть ключові поняття теми."
            )
        step1 = f"1. Науковий аналіз: Розглядаємо сутність явища «{concept}» у структурі курсу {subj_gen} ({grade} клас)."
        step2 = f"2. Джерельна основа: Спираємося на виклад матеріалу в підручнику ({author}): «{snippet}»"
        step3 = f"3. Термінологічний аналіз: Виділяємо ключові природничо-наукові терміни теми: {terms_str}."
        step4 = "4. Науково-педагогічний висновок: Сформульовано сутнісну характеристику природного явища на основі шкільного курсу."
        solution = (
            f"Тема «{concept}» розкриває важливі природні закономірності у курсі {subj_gen} ({grade} клас).\n\n"
            f"Згідно з підручником ({author}):\n«{snippet}»\n\n"
            f"Ключові наукові терміни теми: {terms_str}.\n\n"
            f"Засвоєння цих наукових фактів є основою для формування цілісного природничо-наукового світогляду учнів."
        )
    elif chunk.subject in DISCIPLINE_SOCIAL_LAW:
        if q_var == 0:
            query = (
                f"Охарактеризуйте суспільне значення та сутність теми «{concept}» "
                f"з предмета {subj_nom} ({grade} клас) на основі підручника (автор — {author}). "
                f"Вкажіть ключові поняття теми."
            )
        elif q_var == 1:
            query = (
                f"Розкрийте зміст теми «{concept}» у курсі {subj_nom} для {grade} класу "
                f"за підручником ({author}). Наведіть базові суспільствознавчі терміни."
            )
        else:
            query = (
                f"У чому полягає суспільно-правова сутність теми «{concept}» у курсі {subj_nom} "
                f"({grade} клас, автор підручника — {author})? Вкажіть термінологічну основу матеріалу."
            )
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
        if q_var == 0:
            query = (
                f"Розкрийте сутність теми «{concept}» з предмета {subj_nom} ({grade} клас) "
                f"за матеріалом підручника (автор — {author}). Вкажіть ключові поняття теми."
            )
        elif q_var == 1:
            query = (
                f"Охарактеризуйте змістове наповнення теми «{concept}» у курсі {subj_nom} ({grade} клас) "
                f"на основі підручника ({author}). Наведіть основні фахові терміни."
            )
        else:
            query = (
                f"У чому полягає культурно-освітнє значення теми «{concept}» у курсі з предмета {subj_nom} "
                f"({grade} клас, автор підручника — {author})? Вкажіть ключові терміни теми."
            )
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
    concept = extract_key_concept(chunk)
    snippet = extract_meaningful_text_snippet(chunk.text, concept=concept, max_len=260)
    snippet = apply_calque_sanitation(snippet)
    terms = extract_scientific_terminology_for_snippet(snippet, concept, chunk.subject, cur_ves=cur_ves)

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


    records: list[dict[str, Any]] = []
    subj_dist: dict[str, int] = Counter()
    domain_dist: dict[str, int] = Counter()

    target_stem = target_count // 2
    target_hum = target_count - target_stem

    random.seed(8139)
    idx = 1

    # Round-robin sampling across STEM books
    for i in range(target_stem):
        book = stem_books[i % len(stem_books)]
        book_pool = chunks_by_book[book]
        chunk = book_pool[(i // len(stem_books)) % len(book_pool)]
        rec = synthesize_eval_task(chunk, idx)
        validator.validate(rec)
        records.append(rec)
        subj_dist[rec["subject"]] += 1
        domain_dist["stem"] += 1
        idx += 1

    # Round-robin sampling across Humanities books
    for i in range(target_hum):
        book = hum_books[i % len(hum_books)]
        book_pool = chunks_by_book[book]
        chunk = book_pool[(i // len(hum_books)) % len(book_pool)]
        rec = synthesize_eval_task(chunk, idx)
        validator.validate(rec)
        records.append(rec)
        subj_dist[rec["subject"]] += 1
        domain_dist["humanities"] += 1
        idx += 1

    actual_shards_count = max(1, min(shards_count, len(records) // 100 if len(records) < 500 else shards_count))
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
    return body.strip("«» \t\n")


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
                    snip = m.group(1) if m else ""
                if snip and not is_snippet_grounded_in_concept(snip, concept):
                    return False
    return True


def verify_terms_present_in_snippet(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify that 100% of scientific terms appear directly in the snippet and are non-circular."""
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
                    snip = m.group(1).lower() if m else ""
                for t in terms:
                    t_clean = t.strip().lower()
                    if t_clean == concept:
                        return False
                    if snip and t_clean not in snip:
                        return False
    return True


def verify_zero_dangling_starters(eval_dir: Path, sft_dir: Path) -> bool:
    """Verify that zero quoted snippets start with dangling anaphoric starters."""
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
                if snip and DANGLING_STARTER_RE.search(snip):
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
        partition_ok = (len(eval_subj_dist) == len(HELD_OUT_TEXTBOOKS)) if eval_count == 2500 else (len(eval_subj_dist) >= 1)
        coverage_ok = (eval_domain_dist.get("stem", 0) >= 500 and eval_domain_dist.get("humanities", 0) >= 500) if eval_count == 2500 else True
        zero_leakage_ok = verify_zero_train_eval_leakage(eval_dir, sft_dir)
        entities_ok = verify_entity_preservation_volume_ratio(eval_dir, sft_dir)
        pravopys_ok = verify_pravopys_2019(eval_dir, sft_dir)
        tone_ok = verify_dataset_pedagogy_tone(eval_dir, sft_dir)
        grounding_ok = verify_snippet_concept_grounding(eval_dir, sft_dir)
        terms_ok = verify_terms_present_in_snippet(eval_dir, sft_dir)
        starters_ok = verify_zero_dangling_starters(eval_dir, sft_dir)
        no_fake_claims_ok = verify_eval_no_fake_algorithm_claims(eval_dir)

        if not (grounding_ok and terms_ok and starters_ok and no_fake_claims_ok):
            raise ValueError(
                f"Content quality check failed: grounding={grounding_ok}, terms={terms_ok}, "
                f"starters={starters_ok}, no_fake_claims={no_fake_claims_ok}"
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

    if validate_schema and eval_count == 2500 and sft_count == 75000:
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
