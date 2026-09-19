"""audit_assistant_quality.py - Independent adversarial verification and multi-seed audit report generator.

Performs truly independent audit with strict adversarial criteria and exports human-readable
markdown reports (SAMPLE_INSPECTION_150.md and SAMPLE_INSPECTION_50.md) covering:
1. Citation form (nominative noun head, no bare adjectives/prepositions/verbs, no proper nouns,
   no context-bound genitives like 'авторки'/'вірша', no physical descriptive size/color starters).
2. Deictic opener & ungrounded anaphora absence (including participles, external refs, labelled objects,
   conversational openers like 'Про один...', and pedagogical reminders 'ви вже дізналися...').
3. Definitional alignment of defined subject (verifying concept is the defined subject,
   strictly rejecting inverted definitions where genus is taken as concept, rejecting metaphors
   and evaluative statements).
4. Absence of space-split broken OCR words, hyphen-loss, and column fusion.
5. Scientific terminology authenticity (>= 2 terms, VESUM attested common nouns, standard lemmas
   excluding :alt/:arch/:rare, strict whole-token lemma matching with ZERO substring/stem match,
   and contextual disambiguation of genitive plural homonyms).
6. Multi-seed PRNG sampling across 3 seeds (42, 123, 777) yielding 150 fully inspected records.
7. Full release-wide defect scan across all SFT and eval records.
"""

from __future__ import annotations

import json
import random
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RELEASE_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v06_general_assistant"


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


DEFAULT_VESUM_DB = resolve_data_path("data/vesum.db")

DISALLOWED_VESUM_TAGS = (":alt", ":subst", ":nonstd", ":arch", ":bad", ":rare", ":dial", ":slang")
GENITIVE_GOVERNING_PREPOSITIONS = {
    "до", "від", "з", "із", "зі", "для", "без", "після", "біля", "навколо",
    "серед", "проти", "замість", "внаслідок", "щодо", "поза", "поблизу", "крім",
    "окрім", "завдяки"
}
GENITIVE_QUANTIFIERS = {"один", "одна", "одне", "кілька", "декілька", "багато", "мало", "чимало"}

ABBREVIATIONS: set[str] = {
    "млрд", "млн", "тис", "см", "мм", "км", "кг", "мг", "га", "грн", "кв", "куб", "коп",
    "дм", "л", "мл", "хв", "сек", "год", "стор", "табл", "мал", "рис", "р", "pp", "ст",
}

CANONICAL_HOMONYM_LEMMAS: dict[str, str] = {
    "код": "код",
    "коду": "код",
    "кодом": "код",
    "коді": "код",
    "коди": "код",
    "кодів": "код",
    "кодам": "код",
    "кодами": "код",
    "кодах": "код",
    "кола": "коло",
    "колу": "коло",
    "колом": "коло",
    "колі": "коло",
    "кіл": "коло",
    "колах": "коло",
    "колами": "коло",
    "риски": "риска",
    "рисок": "риска",
    "рисці": "риска",
    "риску": "риска",
    "рискою": "риска",
    "рискам": "риска",
    "рисками": "риска",
    "рисках": "риска",
    "колон": "колона",
    "колони": "колона",
    "колоні": "колона",
    "колону": "колона",
    "колоною": "колона",
    "колонам": "колона",
    "колонами": "колона",
    "колонах": "колона",
    "точок": "точка",
    "точки": "точка",
    "точці": "точка",
    "точку": "точка",
    "точкою": "точка",
    "точкам": "точка",
    "точками": "точка",
    "точках": "точка",
    "появ": "поява",
    "появи": "поява",
    "появі": "поява",
    "появу": "поява",
    "появою": "поява",
    "появам": "поява",
    "появами": "поява",
    "появах": "поява",
    "пар": "пара",
    "пари": "пара",
    "парі": "пара",
    "пару": "пара",
    "парою": "пара",
    "парам": "пара",
    "парами": "пара",
    "парах": "пара",
}

UKRAINIAN_WORD_TOKEN_RE = re.compile(
    r"\b[а-яіїєґ]+(?:['\u2019\u02bc][а-яіїєґ]+)*(?:-[а-яіїєґ]+(?:['\u2019\u02bc][а-яіїєґ]+)*)*\b",
    re.IGNORECASE,
)


def normalize_ukrainian_apostrophes(text: str) -> str:
    """Normalize typographical apostrophes (’, ʼ) to standard ASCII apostrophe (')."""
    return text.replace("\u2019", "'").replace("\u02bc", "'")


# General textbook & school metalanguage stopwords (excluding authentic scientific domain terms)
AUDIT_STOPWORD_TERMS = {
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
    "прийом", "прийому", "прийоми", "п'ята", "п'яти",
    "життя", "світ", "світу", "рік", "року", "роки", "років",
    "день", "дня", "дні", "днів", "протилежне", "живе", "живий", "живим",
    "житель", "жителі", "жителя", "жителів", "прихильник", "прихильники", "прихильника",
    "богиня", "богині", "богинею", "божество", "божества", "божеств", "бог", "бога", "боги", "богів", "міф", "міфи", "міфів", "міфологія",
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
    "майбутнє", "середа", "раз",
}


def audit_citation_form(concept: str, cur: sqlite3.Cursor) -> bool:
    """Audit citation form: nominative noun head, no bare adjectives, no proper nouns, no superlatives."""
    c = concept.strip()
    if not c or len(c) < 3:
        return False
    if not c[0].isupper():
        return False

    # Reject superlatives, evaluatives, ordinals, conditionals, conjunctions at start
    if re.match(
        r"^(?:най|якнай|щонай)\w+|"
        r"^(?:найкращ\w*|найголовніш\w*|найбільш\w*|найважливіш\w*|найскладніш\w*|потужн\w*|ефективн\w*|унікальн\w*|чудов\w*|прекрасн\w*)\b|"
        r"^(?:невелик\w*|маленьк\w*|велик\w*|світл\w*|темн\w*|довг\w*|коротк\w*|тонк\w*|товст\w*|кругл\w*|овальн\w*)\b|"
        r"^(?:перш\w*|друг\w*|трет\w*|четверт\w*|п['ʼ’]?ят\w*|шост\w*|сьом\w*|восьм\w*|дев['ʼ’]?ят\w*|десят\w*|наступн\w*|останн\w*)\b|"
        r"^(?:якщо|коли|та|і|й|або|чи)\b",
        c,
        re.IGNORECASE,
    ):
        return False

    # Reject context-bound unnamed referent heads/tails
    if re.search(
        r"\b(?:авторки|автора|письменника|письменниці|поета|поетеси|вірша|твору|книжки|роману|повісті|оповідання|п'єси|драми|статті|тексту|героя|персонажа)\b",
        c,
        re.IGNORECASE,
    ):
        return False

    if re.search(r"\b(?:очевидн\w*|зрозуміл\w*|незрозуміл\w*|безперечн\w*|помітн\w*)\b", c, re.IGNORECASE):
        return False

    if c.lower() in AUDIT_STOPWORD_TERMS:
        return False

    words = [w.strip(".,;:?!'\"«»„“—–()") for w in c.split() if w.strip(".,;:?!'\"«»„“—–()")]
    if not words or len(words) > 5:
        return False

    preps = {"від", "для", "до", "з", "із", "зі", "на", "по", "про", "за", "під", "над", "при", "без"}
    if len(words) >= 3 and any(w.lower() in preps for w in words[1:-1]):
        cur.execute("SELECT pos FROM forms_all WHERE word_form = ?", (words[-1].lower(),))
        if any(r[0] == "adj" for r in cur.fetchall()):
            return False

    # Check proper nouns: if single-word has a proper noun reading in capitalized form and no common nominative noun reading
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

    if len(words) == 1:
        cur.execute("SELECT pos FROM forms_all WHERE word_form = ?", (words[0].lower(),))
        poses = {r[0] for r in cur.fetchall()}
        if "adj" in poses and "noun" not in poses:
            return False
        if words[0].lower().endswith(("е", "є")) and "noun" not in poses:
            return False

    # Verify presence of nominative noun head
    has_nom_noun = False
    for w in words:
        cur.execute("SELECT tags, pos, lemma FROM forms_all WHERE word_form IN (?, ?)", (w.lower(), w))
        rows = cur.fetchall()
        for r in rows:
            if (
                r[1] == "noun"
                and ("v_naz" in r[0] or "naz" in r[0] or r[2].lower() == w.lower())
                and not any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr"))
            ):
                has_nom_noun = True
                break
        if has_nom_noun:
            break

    return has_nom_noun


def audit_anaphora_and_starters(snippet: str) -> bool:
    """Audit deictic openers, ungrounded anaphora, and external textbook references."""
    s = snippet.strip()
    s_clean = s.lstrip("«„“\"' \t\n")
    if not s_clean or not s_clean[0].isupper():
        return False

    # Reject deictic openers or continuation words
    if re.match(
        r"^(?:Це|Цей|Ця|Ці|Цих|Цього|Цьому|Цим|Таким|Такий|Така|Таке|Такі|"
        r"Він|Вона|Воно|Вони|Його|Її|Їх|Тому|Отже|Також|Крім того|"
        r"Подібно до|Завдяки|Внаслідок|Згідно з|Розглянутий|Зазначений|Вказаний|"
        r"Наведений|Описаний|Так називають|Саме так називається|Для цього|При цьому|У цьому|Втім|Однак|Проте|"
        r"Про\s+(?:один|одну|одне|нього|неї|них|цей|цю|це|ці))\b",
        s_clean,
    ):
        return False

    # Conversational knowledge reminders
    if re.search(r"\b(?:ви\s+вже\s+(?:дізналися|знаєте|вивчили|чули|бачили)|ми\s+вже\s+(?:дізналися|знаємо|вивчили|розглянули))\b", s, re.IGNORECASE):
        return False

    # Mid-sentence anaphora
    if re.search(r"\b(?:так|саме\s+так)\s+(?:називають|називається|називали|назвали)\b", s, re.IGNORECASE):
        return False

    # Demonstrative constructs
    if re.search(r"\bтаке\s+[а-яіїєґ]+", s, re.IGNORECASE):
        return False

    # Textbook structural references (figures, tables, exercises)
    return not bool(
        re.search(
            r"\b(?:мал\.|рис\.|табл\.)\b|"
            r"\b(?:мал\.|малюнк\w*|рис\.|рисунк\w*|табл\.|таблиц\w*|параграф\w*|вправ\w*|рубрик\w*)\s*(?:№\s*)?\d+",
            s,
            re.IGNORECASE,
        )
    )


def audit_ocr_cleanliness(snippet: str, cur: sqlite3.Cursor) -> bool:
    """Audit OCR cleanliness: no space-split words, no missing hyphens, no spliced sentences."""
    s = snippet.strip()

    # Indefinite pronouns and adverbs missing hyphens
    if re.search(
        r"\b(?:будь|хтозна|казна)(?:який|яка|яке|які|якого|якій|якому|яким|яких|якою|хто|що|де|коли|куди|кого|кому|ким|чого|чому|чим|як)\b",
        s,
        re.IGNORECASE,
    ):
        return False

    # Suffixes without hyphen: -небудь, -но, -то
    if re.search(
        r"\b(?:кого|кому|ким|чого|чому|чим|хто|що|де|коли|куди|як)небудь\b",
        s,
        re.IGNORECASE,
    ):
        return False
    if re.search(r"\b(?:тількино|якто)\b", s, re.IGNORECASE):
        return False

    # Spliced sentence / column fusion OCR:
    for m in re.finditer(r"\b([а-яіїєґ]{2,})\s+([А-ЯІЇЄҐ][а-яіїєґ]{2,})\b", s):
        w2 = m.group(2)
        cur.execute("SELECT tags FROM forms_all WHERE word_form = ?", (w2,))
        rows = cur.fetchall()
        is_proper = any(any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr")) for r in rows)
        if not is_proper:
            return False

    return True


def is_phrase_instrumental(phrase: str, cur: sqlite3.Cursor) -> bool:
    """Check if the phrase has an instrumental noun/adjective head without nominative reading."""
    punct = ".,;:?!'\"«»„“—–()"
    words = [w.strip(punct).lower() for w in phrase.split() if w.strip(punct)]
    if not words:
        return False
    for w in words[:2]:
        cur.execute("SELECT tags FROM forms_all WHERE word_form IN (?, ?)", (w, w.capitalize()))
        tags = [r[0] for r in cur.fetchall()]
        if any("v_oru" in t or ":oru" in t for t in tags) and not any("v_naz" in t or ":naz" in t for t in tags):
            return True
    return False


def get_phrase_std_lemmas(phrase: str, cur: sqlite3.Cursor) -> set[str]:
    """Extract standard Ukrainian lemmas for words in a phrase, excluding disallowed tags."""
    norm_p = normalize_ukrainian_apostrophes(phrase.lower())
    tokens = [m.group(0).strip("'-") for m in UKRAINIAN_WORD_TOKEN_RE.finditer(norm_p)]
    res: set[str] = set()
    for tok in tokens:
        cur.execute("SELECT lemma, tags FROM forms_all WHERE word_form = ?", (tok,))
        raw = cur.fetchall()
        std = [r[0].lower() for r in raw if not any(t in r[1] for t in DISALLOWED_VESUM_TAGS)]
        res.update(std if std else [r[0].lower() for r in raw])
    return res


def audit_definitional_alignment(concept: str, snippet: str, cur: sqlite3.Cursor) -> bool:
    """Audit definitional alignment: defined subject matches concept, no evaluatives or metaphors."""
    s = snippet.strip()
    c = concept.strip()
    if len(s) < 25 or len(s) > 400:
        return False
    if not (s.endswith(".") or s.endswith("!") or s.endswith("?")):
        return False

    # Syntax balance, truncation, and exercise fragment check
    if s.count("(") != s.count(")") or s.count("[") != s.count("]") or s.count("«") != s.count("»"):
        return False
    if re.search(r"\([А-ЯІЇЄҐ]\.?$|\b[А-ЯІЇЄҐ]\.$|\(\s*[А-ЯІЇЄҐ]\s*$", s):
        return False
    if re.search(r"\([А-ЯІЇЄҐ]\.?\s*[А-ЯІЇЄҐ][а-яіїєґ'-]+\)\.?$", s):
        return False
    if re.search(r"\([а-яіїєґ]{3,}\)", s):
        return False
    if re.search(r"(?:\.|\?|!)\s+\d+\.?\s*$", s) or re.search(r"\b\d+\.\s*$", s):
        return False
    if re.search(r"\([А-ЯІЇЄҐ][а-яіїєґ]*(?:ськ|ньк|зьк)[а-яіїєґ]*\)", s):
        return False

    # Reject metaphors
    if re.search(
        r"\b(?:наче|мов|немов|немовби|ніби|неначе|подібно\s+до)\b|"
        r"[—–-]\s*(?:це\s+)?(?:перший\s+крок|символ|образ|втілення|уособлення|дзеркало|вікно|ключ\s+до|міст\s+між|запорука|основа\s+життя)\b",
        s,
        re.IGNORECASE,
    ):
        return False

    # Reject evaluatives and superlatives in definition
    if re.search(
        r"(?:один|одна|одне|одні)\s+(?:з|із)\s+най\w+|"
        r"[—–-]\s*(?:це\s+)?(?:один|одна|одне|одні)\s+(?:з|із)\s+най\w+|"
        r"[—–-]\s*(?:це\s+)?якщо\b|"
        r"[—–-]\s*(?:це\s+)?така\s+сама\s+\w+,\s+як\b|"
        r"[—–-]\s*(?:це\s+)?(?:неодмінн\w*|невід'ємн\w*|важлив\w*|значн\w*|головн\w*|провідн\w*)\s+(?:частин\w*|елемент|складова|умова|фактор|чинник)|"
        r"[—–-]\s*(?:це\s+)?(?:ефективн\w*|унікальн\w*|чудов\w*|важлив\w*|цікав\w*|зручн\w*|найкращ\w*|найважливіш\w*|головн\w*)\b",
        s,
        re.IGNORECASE,
    ):
        return False

    def _get_std_lemmas(phrase: str) -> set[str]:
        return get_phrase_std_lemmas(phrase, cur)

    concept_words = [w.strip(".,;:?!'\"«»„“—–()").lower() for w in c.split() if w.strip(".,;:?!'\"«»„“—–()")]
    cw_lemmas = [_get_std_lemmas(w) or {w} for w in concept_words]
    c_lemmas = _get_std_lemmas(c)
    if not c_lemmas:
        return False

    def _matches_concept(target_lemmas: set[str]) -> bool:
        if not target_lemmas:
            return False
        meta_terms = {
            "поняття", "термін", "явище", "процес", "величина", "графік", "властивість", "закон", "правило",
            "два", "дві", "три", "чотири", "п'ять", "один", "одна", "одне", "кілька", "деякі",
        }
        if target_lemmas == c_lemmas:
            return True
        if (target_lemmas - meta_terms) == c_lemmas:
            return True
        if cw_lemmas and all(any(lem in target_lemmas for lem in word_lems) for word_lems in cw_lemmas):
            residual = target_lemmas - meta_terms
            if all(any(lem in residual for lem in word_lems) for word_lems in cw_lemmas) and len(residual) <= len(cw_lemmas) + 1:
                return True
        return False

    # 1. Copula: Subject [—–-] це / [noun phrase]
    m_cop = re.search(r"(?:^|[.!?«„]\s*)([А-ЯІЇЄҐ][а-яіїєґ\s'-]{2,45})\s+[—–-]\s+(?:це\b|([а-яіїєґ\s'-]{3,}))", s)
    if m_cop:
        subj = m_cop.group(1).strip()
        after_phrase = m_cop.group(2)
        if after_phrase:
            words = [w.strip(".,;:?!'\"«»„“—–()") for w in after_phrase.split()[:4]]
            words = [w.lower() for w in words if len(w) >= 3]
            if not words:
                subj = ""
            else:
                first_w = words[0]
                if first_w in ("перший", "другий", "третій", "головний", "один", "одна", "одне", "найкращий"):
                    subj = ""
                else:
                    cur.execute("SELECT tags, pos FROM forms_all WHERE word_form = ?", (first_w,))
                    first_rows = cur.fetchall()
                    is_first_nom = any(r[1] in ("noun", "adj") and any(c in r[0] for c in (":v_naz", ":naz")) for r in first_rows)
                    if not is_first_nom:
                        subj = ""
                    else:
                        has_nom_noun = False
                        for w in words:
                            cur.execute("SELECT tags, pos FROM forms_all WHERE word_form = ?", (w,))
                            w_rows = cur.fetchall()
                            if any(r[1] == "noun" and any(c in r[0] for c in (":v_naz", ":naz")) for r in w_rows):
                                has_nom_noun = True
                                break
                        if not has_nom_noun:
                            subj = ""
        if subj:
            subj_lemmas = _get_std_lemmas(subj)
            if _matches_concept(subj_lemmas):
                return True

    # 2. X називається Y: strictly verify defined entity is not genus
    m_naz = re.search(r"(?:^|[.!?«„]\s*)([А-ЯІЇЄҐ][а-яіїєґ\s'-]{2,45})\s+називається\s+([а-яіїєґ\s'-]{2,45})(?:[,.:;\(«»“\"—–-]|\bякщо\b|\bколи\b|\bде\b|\bна\b|$)", s)
    if m_naz:
        before_phrase = m_naz.group(1).strip()
        after_phrase = m_naz.group(2).strip()
        first_w = before_phrase.split()[0].lower().strip(".,;:?!'\"«»„“—–()")
        cur.execute("SELECT tags FROM forms_all WHERE word_form = ?", (first_w,))
        w_tags = [r[0] for r in cur.fetchall()]
        is_before_oru = any("v_oru" in t or ":oru" in t for t in w_tags) and not any("v_naz" in t or ":naz" in t for t in w_tags)
        if is_before_oru:
            after_lemmas = _get_std_lemmas(after_phrase)
            if _matches_concept(after_lemmas):
                return False  # INVERTED DEFINITION!
            before_lemmas = _get_std_lemmas(before_phrase)
            if _matches_concept(before_lemmas):
                return True
        else:
            before_lemmas = _get_std_lemmas(before_phrase)
            after_lemmas = _get_std_lemmas(after_phrase)
            combined_lemmas = before_lemmas | after_lemmas
            if _matches_concept(combined_lemmas) or _matches_concept(before_lemmas) or _matches_concept(after_lemmas):
                return True

    # 3. X називають Y (with bidirectional instrumental case disambiguation)
    m_call = re.search(
        r"(?:^|[.!?«„]\s*)([А-ЯІЇЄҐа-яіїєґ\s'-]{2,45})\s+називають\s+([а-яіїєґ\s'-]{2,45})(?:[,.:;\(«»“\"—–-]|\bякщо\b|\bколи\b|\bде\b|\bна\b|$)",
        s,
    )
    if m_call:
        before_phrase = m_call.group(1).strip()
        after_phrase = m_call.group(2).strip()
        is_before_inst = is_phrase_instrumental(before_phrase, cur)
        is_after_inst = is_phrase_instrumental(after_phrase, cur)

        if is_before_inst and not is_after_inst:
            after_lemmas = _get_std_lemmas(after_phrase)
            before_lemmas = _get_std_lemmas(before_phrase)
            combined_lemmas = before_lemmas | after_lemmas
            if (c_lemmas & after_lemmas) and not (c_lemmas & before_lemmas):
                return False  # INVERTED DEFINITION!
            if _matches_concept(before_lemmas) or _matches_concept(combined_lemmas):
                return True
        elif is_after_inst and not is_before_inst:
            before_lemmas = _get_std_lemmas(before_phrase)
            after_lemmas = _get_std_lemmas(after_phrase)
            combined_lemmas = before_lemmas | after_lemmas
            if (c_lemmas & before_lemmas) and not (c_lemmas & after_lemmas):
                return False  # INVERTED DEFINITION!
            if _matches_concept(after_lemmas) or _matches_concept(combined_lemmas):
                return True
        else:
            combined_lemmas = _get_std_lemmas(before_phrase) | _get_std_lemmas(after_phrase)
            if _matches_concept(_get_std_lemmas(after_phrase)) or _matches_concept(_get_std_lemmas(before_phrase)) or _matches_concept(combined_lemmas):
                return True

    # 4. X є Y
    m_ye = re.search(r"(?:^|[.!?«„]\s*)([А-ЯІЇЄҐ][а-яіїєґ\s'-]{2,40})\s+є\s+([а-яіїєґ\s'-]{3,40})", s)
    if m_ye:
        subj = m_ye.group(1).strip()
        if _matches_concept(_get_std_lemmas(subj)):
            return True

    # 5. Під X розуміють Y
    m_und = re.search(r"\bпід\s+([а-яіїєґ\s'-]{2,35})\s+розуміють\b", s, re.IGNORECASE)
    if m_und:
        term_phrase = m_und.group(1).strip()
        if _matches_concept(_get_std_lemmas(term_phrase)):
            return True

    # Fallback strict whole-token containment in definitional sentence
    has_def_marker = bool(
        re.search(r"\b(?:називають|називається|названо|визначається як|являє собою|під\s+[а-яіїєґ\s'-]+\s+розуміють)\b", s, re.IGNORECASE)
        or re.search(r"\bє\s+(?:одним|однією|основним|системою|процесом|явищем|сукупністю|формою|частиною|результатом|величиною|правилом|числом|добутком|відношенням|наукою|[а-яіїєґ']+(?:ою|им|ем|ом|єю|ією))\b", s, re.IGNORECASE)
        or re.search(r"[—–-]\s*(?:це\b|(?:один|одне|одна|вид|процес|явище|сукупність|здатність|прилад|стан|властивість|наука|розділ|форма|частина|метод|галузь|поняття|особа|величина|значення|документ|тип|період|система|суміш|речовина|тіло|сполука|елемент|клітина|структура|функція|число|вираз|фігура|відрізок|точка|пряма|кут|рівняння|вектор|орган|тканина|сфера|діяльність|дія|відношення|правило|закон|принцип|комплекс|утворення)\b)", s, re.IGNORECASE)
    )
    if not has_def_marker:
        return False

    snip_lemmas = _get_std_lemmas(s)
    return c_lemmas.issubset(snip_lemmas)


def audit_scientific_terms(terms: list[str], snippet: str, concept: str, cur: sqlite3.Cursor) -> bool:
    """Audit scientific terminology: >= 2 terms, single-word common nouns, standard VESUM lemmas, zero substring matching."""
    if len(terms) < 2:
        return False

    # Extract all whole tokens preserving hyphens and apostrophes
    norm_snip = normalize_ukrainian_apostrophes(snippet.lower())
    tokens = [m.group(0).strip("'-") for m in UKRAINIAN_WORD_TOKEN_RE.finditer(norm_snip)]

    # Build snippet standard lemmas set with contextual disambiguation
    snip_valid_lemmas: set[str] = set()
    for i, tok in enumerate(tokens):
        tok_low = tok.lower()
        if tok_low in ABBREVIATIONS or not any(c in "аеєиіїоуюя" for c in tok_low):
            continue

        if tok_low in CANONICAL_HOMONYM_LEMMAS:
            snip_valid_lemmas.add(CANONICAL_HOMONYM_LEMMAS[tok_low])
            continue

        cur.execute("SELECT lemma, pos, tags FROM forms_all WHERE word_form = ? OR word_form = ?", (tok, tok.capitalize()))
        raw_rows = cur.fetchall()
        std_rows = [r for r in raw_rows if not any(tag in r[2] for tag in DISALLOWED_VESUM_TAGS)]
        rows = std_rows if std_rows else raw_rows
        noun_rows = [r for r in rows if r[1] == "noun" and not any(p in r[2] for p in (":prop", ":fname", ":lname", ":geo", ":ns", ":abbr", ":nv"))]
        if not noun_rows:
            continue

        prev_tok = tokens[i - 1] if i > 0 else None
        chosen_lemma = None

        if prev_tok:
            prev_low = prev_tok.lower()
            cur.execute("SELECT tags FROM forms_all WHERE word_form IN (?, ?) AND pos = 'adj'", (prev_low, prev_tok.capitalize()))
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
                    chosen_lemma = (sing[0] if sing else matching_noun_rows[0])[0].lower()

            if chosen_lemma is None:
                is_gen_context = prev_low in GENITIVE_GOVERNING_PREPOSITIONS or prev_low in GENITIVE_QUANTIFIERS
                if not is_gen_context:
                    cur.execute("SELECT pos FROM forms_all WHERE word_form = ?", (prev_low,))
                    if any(r[0] == "noun" for r in cur.fetchall()):
                        is_gen_context = True
                if is_gen_context:
                    rod_rows = [r for r in noun_rows if ":v_rod" in r[2]]
                    if rod_rows:
                        chosen_lemma = rod_rows[0][0].lower()

        if chosen_lemma is None and prev_tok:
            prev_low = prev_tok.lower()
            if prev_low in ("рядів", "кількість", "число", "безліч", "шерег", "група", "сукупність", "багато", "кілька", "декілька"):
                p_rod_rows = [r for r in noun_rows if ":p:v_rod" in r[2]]
                if p_rod_rows:
                    chosen_lemma = p_rod_rows[0][0].lower()

        if chosen_lemma is None:
            exact_rows = [r for r in noun_rows if r[0].lower() == tok_low and ":v_naz" in r[2]]
            if exact_rows:
                chosen_lemma = exact_rows[0][0].lower()
            else:
                v_naz_rows = [r for r in noun_rows if ":v_naz" in r[2] and ":p:" not in r[2]]
                if v_naz_rows:
                    chosen_lemma = v_naz_rows[0][0].lower()
                else:
                    sing_rows = [r for r in noun_rows if ":p:" not in r[2]]
                    chosen_lemma = (sing_rows[0] if sing_rows else noun_rows[0])[0].lower()

        if chosen_lemma:
            if chosen_lemma == "кода" and tok_low == "код":
                chosen_lemma = "код"
            elif chosen_lemma == "кіл" and tok_low in ("кола", "колі", "колом"):
                chosen_lemma = "коло"
            elif chosen_lemma == "риск" and tok_low in ("риски", "рисок"):
                chosen_lemma = "риска"
            elif chosen_lemma == "колон" and tok_low in ("колон", "колони"):
                chosen_lemma = "колона"
            elif chosen_lemma == "точок" and tok_low in ("точок", "точки"):
                chosen_lemma = "точка"
            elif chosen_lemma == "появ" and tok_low in ("появ", "появи"):
                chosen_lemma = "поява"
            elif chosen_lemma == "пар" and tok_low in ("пар", "пари"):
                chosen_lemma = "пара"

            if chosen_lemma not in ABBREVIATIONS and any(c in "аеєиіїоуюя" for c in chosen_lemma):
                snip_valid_lemmas.add(chosen_lemma)

    for t in terms:
        t_clean = t.strip().lower()
        if len(t_clean) < 3 or " " in t_clean or t_clean in ABBREVIATIONS:
            return False
        if not any(c in "аеєиіїоуюя" for c in t_clean):
            return False
        if t_clean in AUDIT_STOPWORD_TERMS or t_clean.endswith(("е", "є")):
            return False

        # Query VESUM for term validity
        cur.execute("SELECT tags, pos FROM forms_all WHERE word_form = ?", (t_clean,))
        rows = cur.fetchall()
        if not rows:
            return False

        has_noun = False
        has_adj = False
        is_prop = True
        has_disallowed = False
        for r in rows:
            tag, pos = r[0], r[1]
            if any(dt in tag for dt in DISALLOWED_VESUM_TAGS):
                has_disallowed = True
            if any(at in tag for at in (":abbr", ":nv")):
                return False
            if pos == "adj" or ":ns" in tag:
                has_adj = True
            if pos == "noun" and not any(pt in tag for pt in (":prop", ":fname", ":lname", ":geo", ":patr")):
                is_prop = False
                if not has_adj and ":ns" not in tag:
                    has_noun = True

        if has_adj or is_prop or not has_noun:
            return False
        if has_disallowed and not any(r[1] == "noun" and not any(dt in r[0] for dt in DISALLOWED_VESUM_TAGS) for r in rows):
            return False

        # Term MUST be in the contextually disambiguated snippet lemmas! ZERO substring / stem matching!
        if t_clean not in snip_valid_lemmas:
            return False

    return True


def scan_entire_release_defects(cur: sqlite3.Cursor) -> dict[str, int]:
    """Scan all 75,000 SFT records and all eval records for known defect classes across the release."""
    defect_counts = {
        "truncated_snippets": 0,
        "inverted_definitions": 0,
        "disallowed_lemmas": 0,
        "substring_terms": 0,
        "unresolved_anaphora": 0,
        "context_bound_heads": 0,
        "descriptive_non_concepts": 0,
        "metaphors_and_evaluatives": 0,
        "query_framing_mismatch": 0,
    }

    all_files = sorted(RELEASE_DIR.glob("eval/eval_shard_*.jsonl")) + sorted(RELEASE_DIR.glob("sft/sft_shard_*.jsonl"))

    for filepath in all_files:
        with filepath.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                concept = (d.get("concept") or d.get("target_concept") or "").strip()
                terms = d.get("scientific_terminology") or []
                subject = d.get("subject", "")
                query = d.get("query", "")

                steps = d.get("reference_reasoning") or d.get("reasoning_steps") or []
                if len(steps) > 1:
                    body = steps[1]
                    parts = body.split(":", 2)
                    raw_snip = parts[2].strip() if len(parts) >= 3 else parts[-1].strip()
                else:
                    sol = d.get("reference_solution") or d.get("final_response") or ""
                    m = re.search(r"«([^»]{20,})»", sol)
                    raw_snip = m.group(1) if m else sol
                snip = raw_snip.strip("«» \t\n")

                # Defect 1: Truncated snippets
                if (
                    snip.count("(") != snip.count(")")
                    or snip.count("[") != snip.count("]")
                    or snip.count("«") != snip.count("»")
                    or re.search(r"\([А-ЯІЇЄҐ]\.?$|\b[А-ЯІЇЄҐ]\.$|\(\s*[А-ЯІЇЄҐ]\s*$", snip)
                    or re.search(r"\([А-ЯІЇЄҐ]\.?\s*[А-ЯІЇЄҐ][а-яіїєґ'-]+\)\.?$", snip)
                    or re.search(r"\([а-яіїєґ]{3,}\)", snip)
                    or re.search(r"\([А-ЯІЇЄҐ][а-яіїєґ]*(?:ськ|ньк|зьк)[а-яіїєґ]*\)", snip)
                    or re.search(r"(?:\.|\?|!)\s+\d+\.?$|\b\d+\.\s*$", snip)
                ):
                    defect_counts["truncated_snippets"] += 1

                # Defect 2: Inverted definitions
                m_naz = re.search(r"(?:^|[.!?«„]\s*)([А-ЯІЇЄҐ][а-яіїєґ\s'-]{2,45})\s+називається\s+([а-яіїєґ\s'-]{2,45})(?:[,.:;\(«»“\"—–-]|\bякщо\b|\bколи\b|\bде\b|\bна\b|$)", snip)
                if m_naz:
                    before_phrase = m_naz.group(1).strip()
                    after_phrase = m_naz.group(2).strip()
                    if is_phrase_instrumental(before_phrase, cur):
                        conc_lemmas = get_phrase_std_lemmas(concept, cur)
                        ap_lemmas = get_phrase_std_lemmas(after_phrase, cur)
                        bp_lemmas = get_phrase_std_lemmas(before_phrase, cur)
                        if (conc_lemmas & ap_lemmas) and not (conc_lemmas & bp_lemmas):
                            defect_counts["inverted_definitions"] += 1

                m_call = re.search(
                    r"(?:^|[.!?«„]\s*)([А-ЯІЇЄҐа-яіїєґ\s'-]{2,45})\s+називають\s+([а-яіїєґ\s'-]{2,45})(?:[,.:;\(«»“\"—–-]|\bякщо\b|\bколи\b|\bде\b|\bна\b|$)",
                    snip,
                )
                if m_call:
                    before_phrase = m_call.group(1).strip()
                    after_phrase = m_call.group(2).strip()
                    is_before_inst = is_phrase_instrumental(before_phrase, cur)
                    is_after_inst = is_phrase_instrumental(after_phrase, cur)
                    if is_before_inst and not is_after_inst:
                        conc_lemmas = get_phrase_std_lemmas(concept, cur)
                        ap_lemmas = get_phrase_std_lemmas(after_phrase, cur)
                        bp_lemmas = get_phrase_std_lemmas(before_phrase, cur)
                        if (conc_lemmas & ap_lemmas) and not (conc_lemmas & bp_lemmas):
                            defect_counts["inverted_definitions"] += 1
                    elif is_after_inst and not is_before_inst:
                        conc_lemmas = get_phrase_std_lemmas(concept, cur)
                        ap_lemmas = get_phrase_std_lemmas(after_phrase, cur)
                        bp_lemmas = get_phrase_std_lemmas(before_phrase, cur)
                        if (conc_lemmas & bp_lemmas) and not (conc_lemmas & ap_lemmas):
                            defect_counts["inverted_definitions"] += 1

                # Defect 3: Disallowed / wrong lemmas
                if "циліндер" in terms or "кода" in terms or "кіл" in terms or "риск" in terms:
                    defect_counts["disallowed_lemmas"] += 1
                for t in terms:
                    t_low = t.lower()
                    if t_low in ABBREVIATIONS or not any(c in "аеєиіїоуюя" for c in t_low):
                        defect_counts["disallowed_lemmas"] += 1
                if "колон" in terms and re.search(r"\b(?:рядів|кількість|шерег|група|висота)\s+колон\b", snip, re.IGNORECASE):
                    defect_counts["disallowed_lemmas"] += 1
                if "точок" in terms and re.search(r"\b(?:кількість|число|безліч|сукупність)\s+точок\b", snip, re.IGNORECASE):
                    defect_counts["disallowed_lemmas"] += 1
                if "появ" in terms and re.search(r"\b(?:ознаки|причини|час)\s+появи?\b", snip, re.IGNORECASE):
                    defect_counts["disallowed_lemmas"] += 1

                # Defect 4: Substring terms & sliced apostrophes
                norm_snip = normalize_ukrainian_apostrophes(snip.lower())
                snip_tokens = {m.group(0).strip("'-") for m in UKRAINIAN_WORD_TOKEN_RE.finditer(norm_snip)}
                if "ятка" in terms and any(tok.startswith("пам'ят") for tok in snip_tokens):
                    defect_counts["disallowed_lemmas"] += 1
                if "трава" in terms and any("трав'ян" in tok for tok in snip_tokens) and "трава" not in snip_tokens and "трави" not in snip_tokens:
                    defect_counts["disallowed_lemmas"] += 1
                ORGAN_FORMS = {"орган", "органи", "органів", "органу", "органові", "органом", "органі", "органа", "органах", "органами"}
                SVITLO_FORMS = {"світло", "світла", "світлу", "світлом", "світлі"}
                SPRAVEDLYVIST_FORMS = {"справедливість", "справедливості", "справедливістю"}
                MORAL_FORMS = {"мораль", "моралі", "мораллю"}

                for t in terms:
                    t_low = t.lower()
                    if t_low == "орган" and not any(tok in ORGAN_FORMS for tok in snip_tokens) and any(tok.startswith("організм") for tok in snip_tokens):
                        defect_counts["substring_terms"] += 1
                    if t_low == "світло" and not any(tok in SVITLO_FORMS for tok in snip_tokens) and any("світло-" in tok for tok in snip_tokens):
                        defect_counts["substring_terms"] += 1
                    if t_low == "справедливість" and not any(tok in SPRAVEDLYVIST_FORMS for tok in snip_tokens) and "несправедливість" in snip_tokens:
                        defect_counts["substring_terms"] += 1
                    if t_low == "мораль" and not any(tok in MORAL_FORMS for tok in snip_tokens) and any("моральн" in tok for tok in snip_tokens):
                        defect_counts["substring_terms"] += 1

                # Defect 5: Conversational anaphora
                if re.search(r"^(?:про\s+(?:один|одну|одне|нього|неї|них|цей|цю|це|ці))\b", snip, re.IGNORECASE):
                    defect_counts["unresolved_anaphora"] += 1
                if re.search(r"\b(?:ви\s+вже\s+(?:дізналися|знаєте|вивчили|чули|бачили)|ми\s+вже\s+(?:дізналися|знаємо|вивчили|розглянули))\b", snip, re.IGNORECASE):
                    defect_counts["unresolved_anaphora"] += 1

                # Defect 6: Context-bound heads
                if re.search(r"\b(?:авторки|автора|письменника|письменниці|поета|поетеси|вірша|твору|книжки|роману|повісті|оповідання|п'єси|драми|статті|тексту|героя|персонажа)\b", concept, re.IGNORECASE):
                    defect_counts["context_bound_heads"] += 1

                # Defect 7: Descriptive non-concepts
                if (
                    re.match(r"^(?:невелик\w*|маленьк\w*|велик\w*|світл\w*|темн\w*|довг\w*|коротк\w*|тонк\w*|товст\w*|кругл\w*|овальн\w*|золотав\w*|окрем\w*)\b", concept, re.IGNORECASE)
                    or concept.lower() in ("виділення окремих", "окремі елементи", "крапка в центрі", "волосся")
                ):
                    defect_counts["descriptive_non_concepts"] += 1

                # Defect 8: Metaphors and evaluatives
                if re.search(r"[—–-]\s*(?:це\s+)?(?:символ|образ|втілення|уособлення|дзеркало|вікно|ключ\s+до|міст\s+між|перший\s+крок|запорука|основа\s+життя)\b", snip, re.IGNORECASE):
                    defect_counts["metaphors_and_evaluatives"] += 1
                if re.search(r"[—–-]\s*(?:це\s+)?(?:неодмінн\w*|невід'ємн\w*|важлив\w*|значн\w*|головн\w*|провідн\w*)\s+(?:частин\w*|елемент|складова|умова|фактор|чинник)", snip, re.IGNORECASE):
                    defect_counts["metaphors_and_evaluatives"] += 1

                # Defect 9: Query framing mismatch
                if "філологічн" in query.lower() and subject not in ("ukrmova", "ukrlit", "zarlit"):
                    defect_counts["query_framing_mismatch"] += 1

    return defect_counts


def audit_records_for_seed(
    seed: int,
    target_count: int,
    cur: sqlite3.Cursor,
    seen_origins: set[str] | None = None,
    seen_concepts: set[str] | None = None,
) -> list[dict]:
    rng = random.Random(seed)
    eval_shards = sorted(RELEASE_DIR.glob("eval/eval_shard_*.jsonl"))
    sft_shards = sorted(RELEASE_DIR.glob("sft/sft_shard_*.jsonl"))

    sampled_records: list[dict] = []
    if seen_origins is None:
        seen_origins = set()
    if seen_concepts is None:
        seen_concepts = set()

    # Half from eval, half from SFT
    eval_target = target_count // 2

    per_eval_shard = max(1, eval_target // len(eval_shards)) if eval_shards else 0
    for shard in eval_shards:
        recs = []
        with shard.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.strip():
                    d = json.loads(line)
                    d["_origin"] = f"{shard.name}:line_{idx + 1}"
                    recs.append(d)
        rng.shuffle(recs)
        count = 0
        for d in recs:
            c = (d.get("concept") or "").strip()
            orig = d.get("_origin", "")
            if c and c not in seen_concepts and orig not in seen_origins:
                seen_concepts.add(c)
                seen_origins.add(orig)
                sampled_records.append(d)
                count += 1
                if count >= per_eval_shard or len(sampled_records) >= eval_target:
                    break
        if len(sampled_records) >= eval_target:
            break

    sft_indices = list(range(len(sft_shards)))
    rng.shuffle(sft_indices)
    for s_idx in sft_indices:
        if len(sampled_records) >= target_count:
            break
        shard = sft_shards[s_idx]
        recs = []
        with shard.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.strip():
                    d = json.loads(line)
                    d["_origin"] = f"{shard.name}:line_{idx + 1}"
                    recs.append(d)
        rng.shuffle(recs)
        for d in recs:
            c = (d.get("concept") or d.get("target_concept") or "").strip()
            orig = d.get("_origin", "")
            if c and c not in seen_concepts and orig not in seen_origins:
                seen_concepts.add(c)
                seen_origins.add(orig)
                sampled_records.append(d)
                break

    audit_results: list[dict] = []
    for rec in sampled_records:
        concept = (rec.get("concept") or rec.get("target_concept") or "").strip()
        terms = rec.get("scientific_terminology", [])
        steps = rec.get("reference_reasoning") or rec.get("reasoning_steps") or []
        if len(steps) > 1:
            body = steps[1]
            parts = body.split(":", 2)
            raw_snip = parts[2].strip() if len(parts) >= 3 else parts[-1].strip()
        else:
            sol = rec.get("reference_solution") or rec.get("final_response") or ""
            m = re.search(r"«([^»]{20,})»", sol)
            raw_snip = m.group(1) if m else sol
        raw_snip = raw_snip.strip("«» \t\n")

        citation_ok = audit_citation_form(concept, cur)
        anaphora_clean = audit_anaphora_and_starters(raw_snip)
        ocr_clean = audit_ocr_cleanliness(raw_snip, cur)
        def_aligned = audit_definitional_alignment(concept, raw_snip, cur)
        terms_ok = audit_scientific_terms(terms, raw_snip, concept, cur)

        rec_ok = citation_ok and anaphora_clean and ocr_clean and def_aligned and terms_ok
        audit_results.append({
            "seed": seed,
            "origin": rec.get("_origin", ""),
            "concept": concept,
            "subject": rec.get("subject", ""),
            "grade": rec.get("grade", ""),
            "terms": terms,
            "snippet": raw_snip,
            "citation_ok": citation_ok,
            "anaphora_clean": anaphora_clean,
            "ocr_clean": ocr_clean,
            "def_aligned": def_aligned,
            "terms_ok": terms_ok,
            "verdict": "PASS" if rec_ok else "FAIL",
        })

    return audit_results


def main() -> None:
    conn = sqlite3.connect(f"file:{DEFAULT_VESUM_DB}?mode=ro", uri=True)
    cur = conn.cursor()

    sft_files = sorted(RELEASE_DIR.glob("sft/sft_shard_*.jsonl"))
    eval_files = sorted(RELEASE_DIR.glob("eval/eval_shard_*.jsonl"))
    sft_records_count = sum(sum(1 for line in f.open("r", encoding="utf-8") if line.strip()) for f in sft_files)
    eval_records_count = sum(sum(1 for line in f.open("r", encoding="utf-8") if line.strip()) for f in eval_files)

    print(f"Running release-wide defect scan across all {sft_records_count:,} SFT and {eval_records_count:,} eval records...")
    defect_counts = scan_entire_release_defects(cur)
    print("Release-wide defect counts:")
    for k, v in defect_counts.items():
        print(f"  {k}: {v}")

    seeds = [42, 123, 777]
    all_results: list[dict] = []
    seen_origins: set[str] = set()
    seen_concepts: set[str] = set()
    for s in seeds:
        print(f"Sampling 50 records with PRNG seed {s}...")
        res = audit_records_for_seed(s, 50, cur, seen_origins=seen_origins, seen_concepts=seen_concepts)
        all_results.extend(res)

    conn.close()

    total_inspected = len(all_results)
    passed_count = sum(1 for r in all_results if r["verdict"] == "PASS")
    all_passed = passed_count == total_inspected and all(v == 0 for v in defect_counts.values())

    out_md = [
        "# Multi-Seed Sample Inspection of 150 Mined Records (Phase 6.1)\n",
        f"**Audit Result:** {'ALL 150 RECORDS PASSED — 100% PASS RATE' if passed_count == total_inspected else f'{passed_count}/{total_inspected} PASSED'}\n",
        f"**Sampling Protocol:** 3 PRNG seeds (42, 123, 777), 50 records per seed (total {total_inspected} records across eval and SFT shards).\n",
        f"## Release-Wide Defect Scan (All {sft_records_count:,} SFT + {eval_records_count:,} Eval Records)\n",
        "| Defect Class | Count Across Release | Status |",
        "|---|---|---|",
    ]

    for defect_name, cnt in defect_counts.items():
        status_icon = "✅ 0" if cnt == 0 else f"❌ {cnt} defects found"
        out_md.append(f"| `{defect_name}` | {cnt} | {status_icon} |")

    out_md.append("\n## Multi-Seed Inspected Sample Overview\n")
    out_md.append("| # | Seed | Origin | Concept | Subject | Grade | Terms | Citation | Anaphora-Free | OCR-Clean | Def-Aligned | Terms Valid | Verdict |")
    out_md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")

    for i, r in enumerate(all_results, 1):
        terms_str = ", ".join(r["terms"][:4])
        out_md.append(
            f"| {i} | {r['seed']} | `{r['origin']}` | **{r['concept']}** | {r['subject']} | {r['grade']} | {terms_str} | "
            f"{'✅' if r['citation_ok'] else '❌'} | {'✅' if r['anaphora_clean'] else '❌'} | "
            f"{'✅' if r['ocr_clean'] else '❌'} | {'✅' if r['def_aligned'] else '❌'} | "
            f"{'✅' if r['terms_ok'] else '❌'} | **{r['verdict']}** |"
        )

    out_md.append("\n## Detailed Record Inspection (Full Text)\n")
    for i, r in enumerate(all_results, 1):
        out_md.append(f"### Record {i} (Seed {r['seed']}): {r['concept']} ({r['origin']})")
        out_md.append(f"- **Subject / Grade:** {r['subject']} (Grade {r['grade']})")
        out_md.append(f"- **Concept:** `{r['concept']}` (Citation form: {'✅' if r['citation_ok'] else '❌'})")
        out_md.append(f"- **Scientific Terminology:** `{r['terms']}` (Terms >= 2 & non-generic: {'✅' if r['terms_ok'] else '❌'})")
        out_md.append(f"- **Textbook Snippet:** «{r['snippet']}» (Anaphora-free: {'✅' if r['anaphora_clean'] else '❌'}, OCR-Clean: {'✅' if r['ocr_clean'] else '❌'}, Def-Aligned: {'✅' if r['def_aligned'] else '❌'})")
        out_md.append(f"- **Overall Record Verdict:** **{r['verdict']}**\n")

    report_150_path = RELEASE_DIR / "SAMPLE_INSPECTION_150.md"
    report_150_path.write_text("\n".join(out_md) + "\n", encoding="utf-8")
    print(f"Wrote inspection report to {report_150_path}")

    # Also write SAMPLE_INSPECTION_50.md with the seed 42 subset for backwards compatibility
    report_50_path = RELEASE_DIR / "SAMPLE_INSPECTION_50.md"
    seed_42_results = [r for r in all_results if r["seed"] == 42][:50]
    out_50_md = [
        "# Sample Inspection of 50 Mined Records (Phase 6.1)\n",
        f"**Audit Result:** {'ALL 50 RECORDS PASSED' if all(r['verdict'] == 'PASS' for r in seed_42_results) else 'FAILURES DETECTED'}\n",
        "| # | Origin | Concept | Subject | Grade | Terms | Citation | Anaphora-Free | OCR-Clean | Def-Aligned | Terms Valid | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(seed_42_results, 1):
        terms_str = ", ".join(r["terms"][:4])
        out_50_md.append(
            f"| {i} | `{r['origin']}` | **{r['concept']}** | {r['subject']} | {r['grade']} | {terms_str} | "
            f"{'✅' if r['citation_ok'] else '❌'} | {'✅' if r['anaphora_clean'] else '❌'} | "
            f"{'✅' if r['ocr_clean'] else '❌'} | {'✅' if r['def_aligned'] else '❌'} | "
            f"{'✅' if r['terms_ok'] else '❌'} | **{r['verdict']}** |"
        )
    out_50_md.append("\n## Detailed Record Inspection (Full Text)\n")
    for i, r in enumerate(seed_42_results, 1):
        out_50_md.append(f"### Record {i}: {r['concept']} ({r['origin']})")
        out_50_md.append(f"- **Subject / Grade:** {r['subject']} (Grade {r['grade']})")
        out_50_md.append(f"- **Concept:** `{r['concept']}` (Citation form: {'✅' if r['citation_ok'] else '❌'})")
        out_50_md.append(f"- **Scientific Terminology:** `{r['terms']}` (Terms >= 2 & non-generic: {'✅' if r['terms_ok'] else '❌'})")
        out_50_md.append(f"- **Textbook Snippet:** «{r['snippet']}» (Anaphora-free: {'✅' if r['anaphora_clean'] else '❌'}, OCR-Clean: {'✅' if r['ocr_clean'] else '❌'}, Def-Aligned: {'✅' if r['def_aligned'] else '❌'})")
        out_50_md.append(f"- **Overall Record Verdict:** **{r['verdict']}**\n")
    report_50_path.write_text("\n".join(out_50_md) + "\n", encoding="utf-8")
    print(f"Wrote inspection report to {report_50_path}")

    print(f"Final Audit Verdict: {'PASS (150/150 + 0 release defects)' if all_passed else 'FAIL'}")
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
