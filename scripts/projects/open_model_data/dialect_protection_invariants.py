"""Content predicates for Phase 5.2 dialect/historical protection (#8051 / #8086).

These allowlists and bans are imported by the suite builder and by tests so
counts/SHA cannot drift away from the authenticity contracts.
"""

from __future__ import annotations

import re
from typing import Any

# --- Lemko ---

LEMKO_AUTHOR_NEEDLES: frozenset[str] = frozenset(
    {
        "колесса",
        "гижа",
        "гайворонськ",
        "народна пісня",
        "фольклор",
        "байко",
        "антологія лемківськ",
    }
)

LEMKO_WORK_NEEDLES: frozenset[str] = frozenset(
    {
        "лемківщин",
        "галицької лемківщини",
        "антологія лемківської",
        "ой верше",
        "ой, верше",
        "а боже мій",
        "мої мамця",
        "ой учка",
        "ой учка, учка",
        "гаєм зелененьким",
        "а хто хоче війну",
        "народні пісні з лемківщини",
        "народні пісні лемківщини",
    }
)

LEMKO_BANNED_AUTHOR_NEEDLES: frozenset[str] = frozenset(
    {
        "гончар",
        "куліш",
        "багряний",
        "довженко",
        "франко",
        "українка",
        "кобилянськ",
        "лепкий",
        "хвильов",
        "стефаник",
        "нечуй",
        "котляревськ",
    }
)

# True Lemko / SW-Carpathian dialect markers. хижий/хижак are standard UA, not хижа.
LEMKO_MARKER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bлем\b", re.IGNORECASE),
    re.compile(r"\bкед[ь]?\b", re.IGNORECASE),
    re.compile(r"\bєднак\b", re.IGNORECASE),
    re.compile(r"\bюж\b", re.IGNORECASE),
    re.compile(r"\bци\b", re.IGNORECASE),
    re.compile(r"\bвшитко\b", re.IGNORECASE),
    re.compile(r"\bбарз\b", re.IGNORECASE),
    re.compile(r"\bвлони\b", re.IGNORECASE),
    re.compile(r"\bмамц[яюі]\b", re.IGNORECASE),
    re.compile(r"\bжегна\w*", re.IGNORECASE),
    re.compile(r"\bгвидите\b", re.IGNORECASE),
    re.compile(r"\bпозерат\b", re.IGNORECASE),
    re.compile(r"\bнех\b", re.IGNORECASE),
    re.compile(r"\bшто\b", re.IGNORECASE),
    re.compile(r"\bкадиль?\b", re.IGNORECASE),
    re.compile(r"\bсвойой\b", re.IGNORECASE),
    re.compile(r"\bтоти\b", re.IGNORECASE),
    re.compile(r"\bцерковц[юяі]\b", re.IGNORECASE),
    re.compile(r"\bлеса\b", re.IGNORECASE),
    re.compile(r"\bцижм[иы]\b", re.IGNORECASE),
    re.compile(r"\bфабриц[іи]\b", re.IGNORECASE),
    re.compile(r"\bгамери[кц]\w*", re.IGNORECASE),
    re.compile(r"\bзохабим\b", re.IGNORECASE),
    re.compile(r"\bмладий\b", re.IGNORECASE),
    re.compile(r"\bєще\b", re.IGNORECASE),
    re.compile(r"\bбило\b", re.IGNORECASE),
)

LEMKO_BANNED_TARGET_RE: re.Pattern[str] = re.compile(
    r"хиж(?:ий|ая|е|і|их|им|ими|ому|ою|о|ак\w*|у\b)",
    re.IGNORECASE,
)

# --- Old East Slavic ---

OES_WORK_NEEDLES: frozenset[str] = frozenset(
    {
        "слово о полку",
        "слово о плъку",
        "плъку игорев",
        "повість временних літ",
        "повѣсть времяньныхъ",
        "повѣсть времянныхъ",
        "повість минулих літ",
        "руська правда",
        "правда руска",
        "галицько-волинськ",
        "київський літопис",
        "патерик",
        "ізборник",
        "повчання володимира мономаха",
        "слово про закон і благодать",
        "кирило турівськ",
        "моління данила",
        "збірка давніх текстів",
    }
)

OES_BANNED_WORK_NEEDLES: frozenset[str] = frozenset(
    {
        "яременк",
        "переклад яременка",
        "життя та творчість",
    }
)

OES_GRAPH_RE: re.Pattern[str] = re.compile(r"[ѣѢЂђъЪѧѩѫѭѥѡ]")

OES_MAX_YEAR = 1300

# --- Anti-Surzhyk (curated colonial calques only) ---

SURZHYK_TARGET_ALLOWLIST: frozenset[str] = frozenset(
    {
        "вибачаюсь",
        "вибачаюся",
        "уверх",
        "запрокинув",
        "запрокинула",
        "приговорені",
        "приговорений",
        "приговор",
        "позорної",
        "позорний",
        "позорна",
        "позорну",
        "стулі",
        "стула",
        "стулом",
        "брюки",
        "брюках",
        "брюк",
        "шляпу",
        "шляпі",
        "шляпа",
        "шляпці",
        "табак",
        "табаку",
        "гусь",
        "гуся",
        "вести себе",
        "знаходиться",
        "знаходяться",
        "знаходилася",
        "знаходився",
        "знаходились",
        "прийшлось",
        "прийшлося",
        "відправився",
        "відправились",
        "відправилася",
        "відправилися",
        "бормотав",
        "пробормотав",
        "вздихнув",
        "вздихнула",
        "вспіваєш",
        "вспіває",
        "вскрикнув",
        "вскрикнула",
        "палатці",
        "палатки",
        "палатках",
        "палаткою",
        "палатка",
        "відмітити",
        "відмітив",
        "почув себе",
        "на відкритому повітрі",
        "в сторону",
        "вилкою",
        "рішились",
        "рішився",
        "рішилася",
        "заключається",
        "заключатися",
        "співпадає",
        "співпадають",
        "співпадали",
        "співпадати",
        "відноситься",
        "відносилися",
        "відноситись",
        "відносились",
        "являється",
        "являються",
        "на протязі",
        "на протязі дня",
        "на протязі року",
        "по крайній мірі",
        "з тих пір",
        "не дивлячись",
        "не дивлячись на",
        "в кінці кінців",
        "у якості",
        "слідуючий",
        "слідуюча",
        "слідуюче",
        "слідуючи",
        "слідуючі",
        "приймати участь",
        "прийняти участь",
        "кидається в очі",
        "кидаються в очі",
        "рахую, що",
        "рахувати, що",
        "підводити підсумки",
        "терпіти поразку",
        "включає в себе",
        "учбовий",
        "учбова",
        "учбове",
        "учбові",
        "міроприємство",
        "міроприємства",
        "любий",
        "любого",
        "любому",
        "по поводу",
        "дати знати",
        "впадати у відчай",
        "впав у відчай",
        "по вихідних",
        "по вівторках",
        "самий кращий",
        "самий важливий",
        "приймати міри",
        "в першу чергу",
        "роблячи вигляд",
        "свого роду",
        "в тому числі",
        "в цілому",
    }
)

SURZHYK_BANNED_TARGETS: frozenset[str] = frozenset(
    {
        "рідше",
        "дозволяє",
        "дозволяють",
        "таким чином",
        "таким чином,",
        "наступні",
        "наступне",
        "наступним чином",
        "виглядав",
        "настільки",
        "образ",
        "коментарій",
        "коментар",
    }
)

METALINGUISTIC_RE: re.Pattern[str] = re.compile(
    r"правильно сказати|правильно не\b|замість якого треба|замість того щоб|"
    r"треба казати|слід додержувати|хибний вислів|калька з російськ|"
    r"а не\s*[\"«]",
    re.IGNORECASE,
)

# Gate floors advertised as 98% empirical + 98% one-sided CP lower bound.
DIALECT_CP_FLOOR = 0.980
HISTORICAL_CP_FLOOR = 0.980
COMBINED_CP_FLOOR = 0.980
MAX_TOLERATED_DIALECT_CORRUPTION = 1
MAX_TOLERATED_HISTORICAL_CORRUPTION = 0


def _norm(value: str) -> str:
    return (value or "").casefold().strip()


def _blob(*parts: str) -> str:
    return " ".join(_norm(p) for p in parts if p)


def has_any_needle(text: str, needles: frozenset[str]) -> bool:
    blob = _norm(text)
    return any(n in blob for n in needles)


def first_lemko_marker(text: str) -> str | None:
    for pat in LEMKO_MARKER_PATTERNS:
        m = pat.search(text)
        if m:
            token = m.group(0)
            if LEMKO_BANNED_TARGET_RE.fullmatch(token):
                continue
            return token
    return None


def is_banned_lemko_target(target: str) -> bool:
    return bool(LEMKO_BANNED_TARGET_RE.search(target or ""))


def lemko_record_is_authentic(case: dict[str, Any]) -> bool:
    meta = case.get("source_metadata") or {}
    author = str(meta.get("author") or "")
    work = str(meta.get("work") or "")
    target = str(case.get("target_term") or "")
    text = str(case.get("input_text") or "")
    if has_any_needle(author, LEMKO_BANNED_AUTHOR_NEEDLES):
        return False
    if is_banned_lemko_target(target):
        return False
    if not has_any_needle(_blob(author, work), LEMKO_AUTHOR_NEEDLES | LEMKO_WORK_NEEDLES):
        return False
    marker = first_lemko_marker(text)
    if marker is None:
        return False
    return _norm(marker[:3]) in _norm(target) or _norm(target) in _norm(text)


def oes_has_diplomatic_graph(text: str) -> bool:
    return bool(OES_GRAPH_RE.search(text or ""))


def oes_record_is_authentic(case: dict[str, Any]) -> bool:
    meta = case.get("source_metadata") or {}
    work = str(meta.get("work") or "")
    author = str(meta.get("author") or "")
    period = str(meta.get("language_period") or "")
    year = meta.get("year")
    text = str(case.get("input_text") or "")
    if has_any_needle(_blob(work, author, text), OES_BANNED_WORK_NEEDLES):
        return False
    if period != "old_east_slavic":
        return False
    if isinstance(year, int) and year > OES_MAX_YEAR:
        return False
    if not has_any_needle(work, OES_WORK_NEEDLES):
        return False
    return oes_has_diplomatic_graph(text)


def normalize_surzhyk_target(target: str) -> str:
    return _norm(target).rstrip(".,;:")


def surzhyk_target_allowed(target: str) -> bool:
    norm = normalize_surzhyk_target(target)
    if norm in SURZHYK_BANNED_TARGETS:
        return False
    return norm in SURZHYK_TARGET_ALLOWLIST


def is_metalinguistic_control(text: str) -> bool:
    return bool(METALINGUISTIC_RE.search(text or ""))


def surzhyk_record_is_authentic(case: dict[str, Any]) -> bool:
    target = str(case.get("target_term") or "")
    text = str(case.get("input_text") or "")
    if is_metalinguistic_control(text):
        return False
    if not surzhyk_target_allowed(target):
        return False
    return normalize_surzhyk_target(target) in _norm(text)
