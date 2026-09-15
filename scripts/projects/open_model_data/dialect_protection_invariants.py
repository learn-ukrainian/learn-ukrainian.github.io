"""Content predicates for Phase 5.2 dialect/historical protection (#8051 / #8086).

These allowlists and bans are imported by the suite builder and by tests so
counts/SHA cannot drift away from the authenticity contracts.
"""

from __future__ import annotations

import re
import unicodedata
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
    }
)

OES_BANNED_WORK_NEEDLES: frozenset[str] = frozenset(
    {
        "яременк",
        "переклад яременка",
        "життя та творчість",
        "збірка давніх текстів",
    }
)

OES_GRAPH_RE: re.Pattern[str] = re.compile(r"[ѣѢЂђъЪѧѩѫѭѥѡ]")

OES_MAX_YEAR = 1300

# Modern-UA / later-Slavic framing that wiki «Мовні зразки» mix into OES pages.
OES_COMMENTARY_RE: re.Pattern[str] = re.compile(
    r"означає\b|привертає увагу|дієслова|вживаються|м'?якість|"
    r"дієвідмін|теперішнього часу|дійсного способу|виступають у формах|"
    r"синтаксичн|ораторськ|смотрицьк|ужевич|знам[εе]нован|"
    r"спр[аaA]ж[εе]н|вм[Ђѣ]сто|кончащ|начертател|существител|"
    r"раствор|преходящ|прешедш|напр\.?:|граматик[аииу]|"
    r"атематичн|сигматичн|парадигм|"
    r"челъ\s*/|/\s*(?:чла|чло|чли|ла\b|ло\b|бысте|бяху|быша)|"
    r"быхъ\s+челъ|быхомъ\s+чли|бяше\s+[—–-]|"
    r"сътворихомъ|проявленье\s+крещенье|реконструкц",
    re.IGNORECASE,
)

OES_PARADIGM_SLASH_RE: re.Pattern[str] = re.compile(r"/[^/\n]{0,12}/")

OES_GARBLED_RE: re.Pattern[str] = re.compile(r"стазби|въстазби", re.IGNORECASE)

OES_MEDICAL_RE: re.Pattern[str] = re.compile(
    r"хорій|л[Ђѣεе]кар|возми\s+кор|чемериц|порохъ\s+ут|"
    r"пи[εе]тъ\s+щод|за\s+пиво|трімай\s+во\s+уста|лЂскового|"
    r"тяжарных|причиновъ\s+ко\s+см",
    re.IGNORECASE,
)

OES_WIKI_WRAPPER_RE: re.Pattern[str] = re.compile(
    r"chunk_id|\*\*«|^\*\*|\[\s*S\d+\s*\]|`[0-9a-f]{8}_c\d+|"
    r"початок розповіді|вступний заголовок|лаврент|"
    r"фрагмент\s+договору|договору\s+907|договору\s+911|"
    r"<!--|--&gt;|&lt;!--|VERIFY:|Canonical form",
    re.IGNORECASE | re.MULTILINE,
)

OES_LATER_SLAVIC_RE: re.Pattern[str] = re.compile(
    r"н[еεе]хай|рицерского|шляхецкого|статут|вольност|синопсис|"
    r"фрымарчи|позволилъ\s+мεшкан|кроиника|софонович|стародавн|"
    r"—\s+(ми|ви|він)\s+|або\s+\w+\s+бул|ґды\s+бы|кгды\s+бы|"
    r"бодай\s+бы|обыкнов|пановалъ",
    re.IGNORECASE,
)

# Text labeled as a named monument must actually be that monument.
OES_PVL_TEXT_RE: re.Pattern[str] = re.compile(
    r"повѣсти\s+врем|потоп[Ђѣ]|ноеви|симови|хамови|афетъ|"
    r"руска[ӕѧя]\s+зем|кнѧжит|нарек\s+ю|явЂ\s+будеть|"
    r"дъщерию|словеньк|живущем\s+крьщен|киликию|еюпетъ|индикия|"
    r"нирокурия|оудолжишася|свьщания|памъфилию|ефивопья|"
    r"неятью|съгрЂшениє|клЂн|столпа|столпъ|раздЂленьи\s+языкъ|"
    r"видЂти\s+градъ",
    re.IGNORECASE,
)

OES_SLOVO_TEXT_RE: re.Pattern[str] = re.compile(
    r"пълку\s+игор|полку\s+игор|боян|комони|каял|ярославн|"
    r"половец|шелом|игорь\s+възр|луце\s+жъ|не\s+лЂпо\s+ли|"
    r"русици|буи\s+тур|пирог|лебедЂ|дону\s+велик|харалу[жз]|"
    r"святъслав|побарая|боричев|трубами\s+повити|хула\s+на\s+хвалу|"
    r"сула\s+не\s+течет|жемчюжн|ожерел|плъкы|бръзыя|"
    r"чрън|посЂяна|польяна|кая\s+раны|небесЂ|дЂвици|свЂтит|"
    r"жалощам|преклонил|звЂринъ|стязи|вережени|"
    r"дивъ|ветрило|хинов|чръны|веслы|выльяти|роскропити|"
    r"ратаев|врани\s+граяхут",
    re.IGNORECASE,
)

# Legal-register Правда. Bare аще/аже/оже is not enough (paradigms, Slovo, homilies).
OES_PRAVDA_TEXT_RE: re.Pattern[str] = re.compile(
    r"закуп|холоп|гривн|гривен|продаж|вир[ъы]|послух|смерд|челядин|"
    r"урокъ|търгу|видок|батог|борть|посадник|"
    r"обель|обил|тать|кун[ъыа]|задниц|переореть|хлЂва|отариц|"
    r"наимит|остатъкъ|платити\s+за\s+нь|вирник|поконъ|огнищан|"
    r"рядовиц|головнич|розграб|потокъ|тиун|боярьск",
    re.IGNORECASE,
)

# Church ustav / homily / later editorial currency — not Russkaya Pravda.
OES_PRAVDA_ALIEN_RE: re.Pattern[str] = re.compile(
    r"диакон|дияк|диак\b|попам|попомъ|попамъ|владыц|оброкъ|"
    r"рубль|грЂхъ|немощн|тЂли\b|евангел|апостол|църк|церкв",
    re.IGNORECASE,
)

OES_PATERIK_TEXT_RE: re.Pattern[str] = re.compile(
    r"иєрємия|феодос(?:ий|ій|ия)|печерском\s+святом\s+монастыр|"
    r"антон(?:ий|ій)\s+печер",
    re.IGNORECASE,
)

OES_KYIV_CHRONICLE_TEXT_RE: re.Pattern[str] = re.compile(
    r"києвьскым|батыєва|заборолом|полЂзоша|цЂлЂ\s+быша|"
    r"наутрЂя|тынцю|гробницю|мьстиславу|мъстиславь|всеволож",
    re.IGNORECASE,
)

OES_KYRYLO_TEXT_RE: re.Pattern[str] = re.compile(
    r"кирила\s+мниха|сънятии\s+тЂла|человЂчьстЂи\s+души",
    re.IGNORECASE,
)

# --- Anti-Surzhyk (curated colonial calques only) ---

SURZHYK_TARGET_ALLOWLIST: frozenset[str] = frozenset(
    {
        "по крайній мірі",
        "по поводу",
        "приймати участь",
        "приймає участь",
        "приймають участь",
        "приймав участь",
        "приймала участь",
        "приймали участь",
        "прийняти участь",
        "приймати міри",
        "прийняти міри",
        "в кінці кінців",
        "співпадає",
        "співпадають",
        "співпадали",
        "співпадати",
        "співпадіння",
        "попасти впросак",
        "влучити впросак",
        "заключатися в",
        "заключається в",
        "нанести збитки",
        "міроприємство",
        "міроприємства",
        "міроприємств",
        "вздихнув",
        "вздихнула",
        "вскрикнув",
        "вскрикнула",
        "пробормотав",
        "бормотав",
        "запрокинув",
        "запрокинула",
        "позорний",
        "позорна",
        "позорну",
        "позорної",
        "в любий час",
        "в любий момент",
    }
)

SURZHYK_BANNED_TARGETS: frozenset[str] = frozenset(
    {
        "самий",
        "самого",
        "самому",
        "самим",
        "самих",
        "саму",
        "сама",
        "саме",
        "самі",
        "самий кращий",
        "самий важливий",
        "самий більший",
        "самий менший",
        "по вихідних",
        "по вівторках",
        "по середах",
        "по четвергах",
        "по п'ятницях",
        "по понеділках",
        "по суботах",
        "по неділях",
        "по неділям",
        "в цілому",
        "з точки зору",
        "точку зору",
        "точка зору",
        "в першу чергу",
        "у першу чергу",
        "так як",
        "в тому числі",
        "в сторону",
        "свою сторону",
        "в свою сторону",
        "з іншої сторони",
        "іншої сторони",
        "з однієї сторони",
        "однієї сторони",
        "сторона",
        "сторони",
        "сторону",
        "стороні",
        "стороною",
        "роблячи вигляд",
        "робити вигляд",
        "зробити вигляд",
        "терпіти поразку",
        "терпить поразку",
        "у більшості випадків",
        "більшості випадків",
        "свого роду",
        "вести себе",
        "підводити підсумки",
        "впадати у відчай",
        "впав у відчай",
        "дати знати",
        "з тих пір",
        "не дивлячись",
        "не дивлячись на",
        "у якості",
        "знаходиться",
        "знаходяться",
        "знаходився",
        "знаходилася",
        "знаходились",
        "являється",
        "являються",
        "являюсь",
        "відноситися",
        "відноситься",
        "відносились",
        "відносилися",
        "рішився",
        "рішилася",
        "рішились",
        "почув себе",
        "прийшлось",
        "прийшлося",
        "брюки",
        "брюках",
        "брюк",
        "стул",
        "стулі",
        "стула",
        "стулом",
        "вибачаюсь",
        "вибачаюся",
        "на відкритому повітрі",
        "на протязі",
        "слідуючи",
        "слідуючий",
        "слідуюча",
        "слідуюче",
        "слідуючі",
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
        "відмітити",
        "відмітив",
        "відмічати",
        "відмічає",
        "відмічають",
        "відправився",
        "відправились",
        "відправилася",
        "відправилися",
        "відправитися",
        "відправлятися",
        "палатка",
        "палатки",
        "палатці",
        "палатках",
        "палаткою",
        "шляпа",
        "шляпу",
        "шляпі",
        "шляпці",
        "гусь",
        "гуся",
        "любий",
        "любого",
        "любому",
        "вилка",
        "вилкою",
        "вилки",
        "вилці",
        "вилках",
        "приговор",
        "приговорити",
        "приговорений",
        "приговорені",
        "учбовий",
        "учбова",
        "учбове",
        "учбові",
        "вспівати",
        "вспіває",
        "вспіваєш",
        "табак",
        "табаку",
        "табака",
        "уверх",
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


_HOMOGLYPH_TO_CYRILLIC = str.maketrans(
    {
        "a": "а",
        "c": "с",
        "e": "е",
        "i": "і",
        "j": "ј",
        "o": "о",
        "p": "р",
        "s": "ѕ",
        "u": "у",
        "x": "х",
        "y": "у",
        "A": "А",
        "B": "В",
        "C": "С",
        "E": "Е",
        "H": "Н",
        "I": "І",
        "J": "Ј",
        "K": "К",
        "M": "М",
        "O": "О",
        "P": "Р",
        "S": "Ѕ",
        "T": "Т",
        "U": "У",
        "X": "Х",
        "Y": "У",
    }
)
_LATIN_VOWEL_TO_CYRILLIC = _HOMOGLYPH_TO_CYRILLIC


def oes_strip_combining(text: str) -> str:
    """Drop printed stresses so Половéцкомъ still matches половец and fold homoglyphs."""
    s = unicodedata.normalize("NFKC", text or "")
    s = "".join(ch for ch in unicodedata.normalize("NFKD", s) if unicodedata.category(ch) != "Mn")
    return s.translate(_HOMOGLYPH_TO_CYRILLIC)


def oes_fold_graph_variants(text: str) -> str:
    """Collapse ѡ/о, ѧ/я, ѣ/е and kin so second-graph reprints match."""
    s = oes_strip_combining(text).casefold()
    for src, dst in (
        ("ѿ", "от"),
        ("ѡ", "о"),
        ("ѧ", "я"),
        ("ѩ", "я"),
        ("ѫ", "у"),
        ("ѭ", "ю"),
        ("ѥ", "е"),
        ("ѣ", "е"),
        ("ђ", "е"),
        ("ӕ", "я"),
        ("ꙗ", "я"),
        ("ꙑ", "ы"),
    ):
        s = s.replace(src, dst)
    return s


def oes_match_blob(text: str) -> str:
    """Accent-stripped text for monument regexes (historical letters kept)."""
    return oes_strip_combining(text)


def oes_passage_fingerprint(text: str) -> str:
    """Normalize a passage so wrappers, accents, and graph variants collapse."""
    s = oes_fold_graph_variants(text)
    # [\s\S] so HTML comments that span lines are stripped (CodeQL py/bad-tag-filter).
    s = re.sub(r"<!--[\s\S]*?-->", " ", s)
    s = OES_WIKI_WRAPPER_RE.sub(" ", s)
    s = re.sub(r"\[\s*s\d+\s*\]", " ", s)
    s = re.sub(r"[*_`«»\"'“”„…·•—–~❙/\\|<>=]+", " ", s)
    s = re.sub(r"[.,;:!?()\[\]<>]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _longest_common_token_run(left: str, right: str) -> int:
    ta = left.split()
    tb = right.split()
    if not ta or not tb:
        return 0
    best = 0
    index_b = {tok: [] for tok in set(tb)}
    for j, tok in enumerate(tb):
        index_b[tok].append(j)
    for i, tok in enumerate(ta):
        for j in index_b.get(tok, ()):
            k = 0
            while i + k < len(ta) and j + k < len(tb) and ta[i + k] == tb[j + k]:
                k += 1
            if k > best:
                best = k
            if best >= 8:
                return best
    return best


def oes_passages_are_near_duplicates(left: str, right: str) -> bool:
    a = oes_passage_fingerprint(left)
    b = oes_passage_fingerprint(right)
    if not a or not b:
        return False
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if shorter in longer:
        return True
    if longer.startswith(shorter):
        return True
    return _longest_common_token_run(a, b) >= 8


def oes_text_is_diplomatic_excerpt(text: str) -> bool:
    """Reject grammar commentary, later recipes, wiki wrappers, later Slavic."""
    raw = text or ""
    if len(raw) < 25 or len(raw.split()) < 4:
        return False
    if not oes_has_diplomatic_graph(raw):
        return False
    if OES_COMMENTARY_RE.search(raw):
        return False
    if OES_PARADIGM_SLASH_RE.search(raw):
        return False
    if OES_MEDICAL_RE.search(raw):
        return False
    if OES_WIKI_WRAPPER_RE.search(raw):
        return False
    if OES_LATER_SLAVIC_RE.search(raw):
        return False
    if OES_GARBLED_RE.search(raw):
        return False
    return not ('"' in raw or "..." in raw)


def oes_work_bucket(work: str) -> str:
    blob = _norm(work)
    if "слово о полку" in blob or "слово о плъку" in blob:
        return "slovo"
    if "руська правда" in blob or "правда руска" in blob:
        return "pravda"
    if "повість временних" in blob or "повѣсть" in blob or "повість минулих" in blob:
        return "pvl"
    if "патерик" in blob:
        return "pateryk"
    return "other"


def _oes_search(pattern: re.Pattern[str], text: str) -> bool:
    blob = oes_match_blob(text)
    return bool(pattern.search(text) or pattern.search(blob))


def oes_text_is_pravda_legal(text: str) -> bool:
    if _oes_search(OES_PRAVDA_ALIEN_RE, text):
        return False
    if _oes_search(OES_SLOVO_TEXT_RE, text):
        return False
    return _oes_search(OES_PRAVDA_TEXT_RE, text)


def oes_text_matches_named_monument(text: str, work: str) -> bool:
    """The row's work label must be the monument the excerpt actually is."""
    bucket = oes_work_bucket(work)
    if bucket == "pvl":
        if _oes_search(OES_PATERIK_TEXT_RE, text) and not _oes_search(OES_PVL_TEXT_RE, text):
            return False
        if _oes_search(OES_SLOVO_TEXT_RE, text) and not _oes_search(OES_PVL_TEXT_RE, text):
            return False
        return _oes_search(OES_PVL_TEXT_RE, text)
    if bucket == "slovo":
        if OES_COMMENTARY_RE.search(text) or OES_PARADIGM_SLASH_RE.search(text):
            return False
        return _oes_search(OES_SLOVO_TEXT_RE, text)
    if bucket == "pravda":
        return oes_text_is_pravda_legal(text)
    if bucket == "pateryk":
        return _oes_search(OES_PATERIK_TEXT_RE, text)
    if "київський літопис" in _norm(work):
        return _oes_search(OES_KYIV_CHRONICLE_TEXT_RE, text)
    if "кирило турівськ" in _norm(work):
        return _oes_search(OES_KYRYLO_TEXT_RE, text)
    return False


def infer_oes_work_from_text(text: str) -> tuple[str, int] | None:
    """Assign a monument from the excerpt itself, not from a wiki filename."""
    if _oes_search(OES_PATERIK_TEXT_RE, text) and not _oes_search(OES_PVL_TEXT_RE, text):
        return "Патерик Києво-Печерський", 1220
    if _oes_search(OES_SLOVO_TEXT_RE, text):
        return "Слово о полку Ігоревім", 1187
    if oes_text_is_pravda_legal(text):
        return "Руська Правда", 1072
    if _oes_search(OES_PVL_TEXT_RE, text):
        return "Повість временних літ", 1113
    if _oes_search(OES_KYIV_CHRONICLE_TEXT_RE, text):
        return "Київський літопис", 1203
    if _oes_search(OES_KYRYLO_TEXT_RE, text):
        return "Кирило Турівський", 1180
    return None


def oes_pick_target_term(text: str) -> str:
    stripped = oes_strip_combining(text)
    for word in re.findall(r"[А-Яа-яІіЇїЄєҐґѣѢЂђъЪьѧѩѫѭѥѡ]{2,}", stripped):
        if OES_GRAPH_RE.search(word) and len(word) >= 2:
            return word
    return ""


def oes_target_occurs_in_text(target: str, text: str) -> bool:
    t = oes_strip_combining(target).casefold()
    s = oes_strip_combining(text).casefold()
    return len(t) >= 2 and t in s


def oes_record_is_authentic(case: dict[str, Any]) -> bool:
    meta = case.get("source_metadata") or {}
    work = str(meta.get("work") or "")
    author = str(meta.get("author") or "")
    period = str(meta.get("language_period") or "")
    year = meta.get("year")
    text = str(case.get("input_text") or "")
    target = str(case.get("target_term") or "")
    if has_any_needle(_blob(work, author, text), OES_BANNED_WORK_NEEDLES):
        return False
    if period != "old_east_slavic":
        return False
    if isinstance(year, int) and year > OES_MAX_YEAR:
        return False
    if not has_any_needle(work, OES_WORK_NEEDLES):
        return False
    if not oes_text_is_diplomatic_excerpt(text):
        return False
    if not oes_text_matches_named_monument(text, work):
        return False
    if len(target) < 2 or not OES_GRAPH_RE.search(target):
        return False
    return oes_target_occurs_in_text(target, text)


def oes_honest_unique_passages(texts: list[str]) -> list[str]:
    """Keep first of each near-duplicate cluster after graph/accent fold."""
    kept: list[str] = []
    for text in texts:
        if any(oes_passages_are_near_duplicates(text, prev) for prev in kept):
            continue
        kept.append(text)
    return kept


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
