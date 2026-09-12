"""Automated evaluation harness for Ukrainian Linguistic Decolonization & Reasoning (#7926).

Benchmarks candidate model outputs against the held-out evaluation firewall partition
(`decolonization_trajectories_held_out_part001.jsonl`), measuring:
1. Calque elimination rate (rejection of Soviet calques and Russianisms)
2. Authentic Ukrainian suggestion rate (presence of verified living standard / classical terms)
3. Morphemic and historical grounding score (presence of structural linguistic reasoning)
4. Overall State Standard 2024 compliance index
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HELD_OUT_FILE = (
    REPO_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "decolonization"
    / "generated"
    / "decolonization_trajectories_held_out_part001.jsonl"
)

REASONING_MARKERS = [
    re.compile(r"кальк", re.IGNORECASE),
    re.compile(r"росіян", re.IGNORECASE),
    re.compile(r"радянськ", re.IGNORECASE),
    re.compile(r"префікс", re.IGNORECASE),
    re.compile(r"дієприкметник", re.IGNORECASE),
    re.compile(r"суфікс", re.IGNORECASE),
    re.compile(r"питом", re.IGNORECASE),
    re.compile(r"етимолог", re.IGNORECASE),
    re.compile(r"словник", re.IGNORECASE),
    re.compile(r"весум", re.IGNORECASE),
    re.compile(r"підручник", re.IGNORECASE),
    re.compile(r"норм", re.IGNORECASE),
]

AFFIRMATION_PATTERNS = [
    r"правильно\s+(?:вживати|казати|говорити|писати)?\s*[«\"]?{term}[»\"]?",
    r"слово\s+[«\"]?{term}[»\"]?\s+є\s+(?:цілком\s+)?нормативним",
    r"вживайте\s+[«\"]?{term}[»\"]?",
    r"можна\s+(?:цілком\s+)?(?:вільно\s+)?вживати\s+[«\"]?{term}[»\"]?",
    r"{term}\s*(?:—|-|–|є|це)?\s*(?:це\s+)?(?:правильн|нормативн|прийнятн|допустим|літературн|влучн|вдало|вірн|кращ|кращий|вибір)",
    r"(?:у\s+вживанні|щодо)\s+[«\"]?{term}[»\"]?\s+немає\s+(?:жодної\s+)?помилк",
    r"[«\"]?{term}[»\"]?\s+не\s+(?:є\s+)?(?:помилк|кальк|русизм|вад)",
    r"[«\"]?{term}[»\"]?\s+не\s+вважа(?:ється|ти)\s+помилк",
]

REFUSAL_PATTERNS = [
    re.compile(r"відмов(?:ляюся|ляємося|лятися|лятимемося)", re.IGNORECASE),
    re.compile(r"не\s+(?:можу|можемо|маю\s+змоги)\s+(?:оцін|надати|відповід|визнач)", re.IGNORECASE),
    re.compile(r"як\s+(?:мовна\s+модель|штучний\s+інтелект|асистент)", re.IGNORECASE),
    re.compile(r"не\s+(?:маю|надаю)\s+(?:можливості|відповід)", re.IGNORECASE),
    re.compile(r"(?:наведено|вжито|використано)\s+лише\s+для\s+прикладу", re.IGNORECASE),
    re.compile(r"(?:оцінки|відповіді|аналізу)\s+не\s+буде", re.IGNORECASE),
    re.compile(r"не\s+буде\s+(?:оцінки|відповіді|аналізу)", re.IGNORECASE),
    re.compile(r"не\s+(?:буду|будемо)\s+(?:оцінювати|відповідати|коментувати|аналізувати)", re.IGNORECASE),
    re.compile(r"я\s+не\s+даю\s+(?:оцінок|відповідей)", re.IGNORECASE),
    re.compile(r"(?:без\s+коментарів|без\s+оцінки|без\s+відповіді)", re.IGNORECASE),
    re.compile(r"не\s+можу\s+(?:оцінити|відповісти|надати\s+оцінку)", re.IGNORECASE),
    re.compile(r"(?:це\s+)?(?:лише|тільки)\s+(?:цитата|приклад|вправа|уривок)", re.IGNORECASE),
    re.compile(r"цитата\s+з\s+(?:вправи|тексту|підручника|книги|дошки)", re.IGNORECASE),
    re.compile(r"(?:на\s+дошці|у\s+зошиті)\s+(?:написано|записано)", re.IGNORECASE),
]

EXPLANATION_CONNECTIVES = [
    re.compile(r"(?:тому\s+що|оскільки|бо\s+|через\s+те\s+що|адже)", re.IGNORECASE),
    re.compile(r"(?:замість|на\s+відміну\s+від|натомість|а\s+не)", re.IGNORECASE),
    re.compile(
        r"(?:походить\s+від|утворено|відповідає|виражає|(?:є|це|—|-|–)\s+(?:\w+\s+)?(?:кальк\w*|росіянізм\w*|помилк\w*|суржик\w*))",
        re.IGNORECASE,
    ),
    re.compile(r"(?:питомий|питоме|питомим|автентичн|власне\s+українськ)", re.IGNORECASE),
    re.compile(
        r"(?:за\s+(?:словником|підручником|правописом|весум)|у\s+(?:словнику|підручнику|правописі|весумі))",
        re.IGNORECASE,
    ),
]

SUGGESTION_PATTERNS = [
    r"(?:правильно|краще|варто|слід|рекомендуємо|рекомендовано|радимо|доцільно|доречно|потрібно|необхідно|нормативно)\s+(?:вживати|казати|говорити|писати|використовувати|брати|обирати)?\s*[:—–-]?\s*[«\"]?{alt}[»\"]?",
    r"(?:вживайте|кажіть|говоріть|пишіть|використовуйте|беріть|замініть|обирайте|надавайте\s+перевагу)\s*[:—–-]?\s*[«\"]?{alt}[»\"]?",
    r"(?:замість\s+.*?|натомість|як\s+відповідник\w*|питом\w*\s+відповідник\w*|нормативн\w*\s+відповідник\w*|правильн\w*\s+варіант\w*|питом\w*\s+слов\w*)\s+(?:є|виступає|слугує)?\s*[:—–-]?\s*[«\"]?{alt}[»\"]?",
    r"[«\"]?{alt}[»\"]?\s*(?:—|-|–|є|це)\s*(?:це\s+)?(?:питом\w*|автентичн\w*|нормативн\w*|правильн\w*|чинн\w*|літературн\w*)\s+(?:відповідник\w*|стандарт\w*|варіант\w*|слово\w*|форма\w*|норм\w*)",
    r"[«\"]?{alt}[»\"]?\s*(?:відповідає\s+(?:мовній\s+)?нормі|має\s+(?:повну\s+)?парадигму|зафіксован\w*\s+у\s+словник|є\s+літературн\w*\s+норм\w*|вважається\s+норм\w*|рекомендується|радять)",
]

ALTERNATIVE_NEGATION_PATTERNS = [
    r"не\s+(?:варто\s+|слід\s+|можна\s+|треба\s+)?(?:вживати|вживайте|використовувати|використовуйте|казати|кажіть|говорити|говоріть|писати|пишіть|радимо|рекомендуємо|брати|беріть)\s+[«\"]?{alt}[»\"]?",
    r"не\s+[«\"]?{alt}[»\"]?",
    r"(?:уникати|уникайте|відмовтеся\s+від|відмовитися\s+від)\s+[«\"]?{alt}[»\"]?",
    r"замість\s+[«\"]?{alt}[»\"]?\s+(?:вживайте|краще|правильно)\s+[«\"]?{term}[»\"]?",
]

LINGUISTIC_RELATION_PATTERNS = [
    # Relation 1: Authority Attestation Binding
    re.compile(
        r"(?:за|згідно\s+з|відповідно\s+до|підтверджен\w*)\s+(?:словником|підручником|правописом|весум|чинним\s+правописом|нормами)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:у|в)\s+(?:словнику|підручнику|правописі|весумі)\s+(?:подано|зафіксовано|наведено|зазначено|міститься|є)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:словник|підручник|правопис|весум)\s+(?:подає|фіксує|наводить|зазначає|містить|рекомендує|вказує)",
        re.IGNORECASE,
    ),
    re.compile(r"зафіксован\w*\s+(?:у|в)\s+(?:словнику|весум|підручнику|джерелах)", re.IGNORECASE),
    # Relation 2: Morphological & Word-Formation Binding
    re.compile(r"(?:утворено|походить)\s+(?:від|за\s+допомогою|через|шляхом|відповідно\s+до)", re.IGNORECASE),
    re.compile(r"(?:містить|має)\s+(?:питомий\s+)?(?:суфікс|префікс|корінь|закінчення)", re.IGNORECASE),
    re.compile(
        r"(?:суфікс\w*|префікс\w*|дієприкметник\w*|закінчення)\s+[^;.!?\n]*(?:є\s+)?(?:властив\w*|невластив\w*|питом\w*|характерн\w*|ненормативн\w*|чужорідн\w*|твори\w*|відповіда\w*)",
        re.IGNORECASE,
    ),
    re.compile(r"активн\w*\s+дієприкметник\w*", re.IGNORECASE),
    re.compile(r"словотвірн\w*\s+модел\w*", re.IGNORECASE),
    re.compile(r"наголос\s+(?:падає|на|у)", re.IGNORECASE),
    # Relation 3: Linguistic Status & Decolonization Classification
    re.compile(
        r"(?:є|це|—|-|–)\s*(?:це\s+)?(?:\w+\s+)?(?:кальк\w*|росіянізм\w*|русизм\w*|суржик\w*|запозичен\w*)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:(?:є|це|—|-|–)\s*(?:це\s+)?(?:\w+\s+)?(?:питом\w*|автентичн\w*|нормативн\w*|літературн\w*|чинн\w*)\s+(?:відповідник\w*|варіант\w*|форма\w*|слово\w*|стандарт\w*|норма\b)|(?:питом\w*|автентичн\w*|нормативн\w*|літературн\w*|чинн\w*)\s+(?:відповідник\w*|варіант\w*|форма\w*|слово\w*|стандарт\w*|норма\b)\s+(?:є|виступає|це))",
        re.IGNORECASE,
    ),
    re.compile(
        r"замість\s+(?:російськ\w*|радянськ\w*|скалькован\w*|кальк\w*|росіянізм\w*|помилк\w*)",
        re.IGNORECASE,
    ),
    re.compile(r"походить\s+від\s+рос", re.IGNORECASE),
]

NARRATIVE_AGENT_PATTERNS = [
    re.compile(
        r"\b(?:я|ми|учень|учениця|студент|студентка|автор|хтось)\s+(?:прочитав\w*|вивчив\w*|переписав\w*|знайшов\w*|побачив\w*|подивився|подивилася|дізнався|дізналася|чув\w*|думаю|вважаю|хочу|цікавить\w*)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:бо|тому\s+що|оскільки)\s+(?:я|ми|учень|студент)\b", re.IGNORECASE),
]

OTHER_ENTITY_PATTERNS = [
    re.compile(
        r"\b(?:інш\w*|сторонн\w*|чуж\w*)\s+(?:слов\w*|форм\w*|лексем\w*|термін\w*|значенн\w*|понять\w*|одиниц\w*)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:another|other)\s+(?:word|term|form|lexeme|meaning|unit)",
        re.IGNORECASE,
    ),
]

EXEMPT_LINGUISTIC_ENTITIES = {
    # Authorities & dictionaries
    "весум",
    "сум-11",
    "сум",
    "грінченко",
    "грінченка",
    "правопис",
    "правопис 2019",
    # Specific multi-word textbook & course titles
    "українська мова",
    "українська література",
    "історія україни",
    "всесвітня історія",
    "я досліджую світ",
    "зарубіжна література",
    "основи здоров'я",
    "громадянська освіта",
}

EXEMPT_AFFIXES = {
    "-чий",
    "обез-",
    "со-",
    "зне-",
    "зня-",
    "без-",
    "спів-",
    "не-",
    "на-",
    "по-",
    "за-",
    "під-",
    "від-",
    "пере-",
    "до-",
    "ви-",
    "роз-",
    "пре-",
    "при-",
    "-тель",
    "-ник",
    "-н-",
    "-ен-",
    "-ськ-",
    "-ов-",
    "-ів-",
    "-ин-",
}

GRAMMATICAL_STOPWORDS = {
    "за",
    "у",
    "в",
    "на",
    "до",
    "з",
    "із",
    "як",
    "що",
    "щоб",
    "яке",
    "який",
    "яка",
    "які",
    "яких",
    "якому",
    "яким",
    "та",
    "і",
    "й",
    "не",
    "чи",
    "або",
    "є",
    "це",
    "має",
    "мають",
    "було",
    "був",
    "була",
    "буде",
    "будуть",
    "через",
    "при",
    "під",
    "від",
    "для",
    "про",
    "по",
    "без",
    "над",
    "між",
    "серед",
    "після",
    "перед",
    "краще",
    "варто",
    "слід",
    "питоме",
    "нормативне",
    "правильне",
    "автентичне",
    "літературне",
    "чинне",
    "типове",
    "таке",
    "така",
    "такий",
    "цей",
    "ця",
    "ці",
    "бо",
    "тому",
    "оскільки",
    "виступає",
    "вважається",
}

STOPWORD_PATTERN = r"(?:" + "|".join(re.escape(w) for w in sorted(GRAMMATICAL_STOPWORDS, key=len, reverse=True)) + r")"

PART_OF_SPEECH_WORDS = (
    r"(?:у\s+)?(?:слов[аоеіу]|словом|слові|слів|"
    r"лексем[аиіуе]|лексемою|лексемі|"
    r"термін[аіу]|терміном|терміні|"
    r"понятт\w*|"
    r"іменник\w*|"
    r"прикметник\w*|"
    r"дієслов\w*|"
    r"дієприкметник\w*|"
    r"дієприслівник\w*|"
    r"прислівник\w*|"
    r"займенник\w*|"
    r"числівник\w*|"
    r"сполучник\w*|"
    r"прийменник\w*|"
    r"частк\w*|"
    r"вигук\w*)"
)

DESCRIPTOR_WORDS = (
    r"(?:суфікс\w*|префікс\w*|корен\w*|основ\w*|закінченн\w*|"
    r"значенн\w*|поясненн\w*|тлумаченн\w*|етимологі\w*|походженн\w*|"
    r"варіант\w*|форм\w*)"
)

RELATION_CHAIN = rf"(?:{DESCRIPTOR_WORDS}\s+)*"

RELATION_CHAIN_NO_FORM = (
    r"(?:(?:суфікс\w*|префікс\w*|корен\w*|основ\w*|закінченн\w*|"
    r"значенн\w*|поясненн\w*|тлумаченн\w*|етимологі\w*|походженн\w*|"
    r"варіант\w*)\s+)*"
)

NAMED_ENTITY_PATTERNS = [
    re.compile(
        rf"\b{RELATION_CHAIN}{PART_OF_SPEECH_WORDS}\s+(?!{STOPWORD_PATTERN}\b)[«\"“']?([а-яіїєґa-z0-9'’ʼ\-]+)[»\"”']?",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{RELATION_CHAIN}[«\"“']([а-яіїєґa-z0-9'’ʼ\-]+)[»\"”']",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{RELATION_CHAIN_NO_FORM}(?:форм[аиіуе]|формою|формі)\s+(?!{PART_OF_SPEECH_WORDS}\b)(?!{STOPWORD_PATTERN}\b)([а-яіїєґa-z0-9'’ʼ\-]+)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:{DESCRIPTOR_WORDS}\s+)+({PART_OF_SPEECH_WORDS})(?:\s*(?=[.,;:!?…—\-)\]»\"”']|$|\n)|\s+(?={STOPWORD_PATTERN}\b))",
        re.IGNORECASE,
    ),
]

PROTECTED_SPAN_PATTERN = re.compile(
    r"("
    r"[«\"“„][^»\"”\n]+[»\"””]"
    r"|(?<!\w)['‘][^'’\n]+['’](?!\w)"
    r"|(?<=\bслов[аоі]\s)[а-яіїєґa-z0-9'’ʼ\-]+"
    r"|(?<=\bтермін\s)[а-яіїєґa-z0-9'’ʼ\-]+"
    r"|(?<=\bтерміна\s)[а-яіїєґa-z0-9'’ʼ\-]+"
    r"|(?<=\bлексеми\s)[а-яіїєґa-z0-9'’ʼ\-]+"
    r"|(?<=\bпоняття\s)[а-яіїєґa-z0-9'’ʼ\-]+"
    r")",
    re.IGNORECASE,
)

GRAMMATICAL_MODIFIER_RULES = [
    # Gender modifying POS or form
    (
        re.compile(
            r"\b(іменник\w*|прикметник\w*|займенник\w*|числівник\w*|дієприкметник\w*|форм\w*)\s+(?:чоловічого|жіночого|середнього|спільного)\s+роду\b",
            re.IGNORECASE,
        ),
        r"\1 ",
    ),
    # Aspect modifying verb, participle, or form
    (
        re.compile(
            r"\b(дієслов\w*|дієприкметник\w*|дієприслівник\w*|форм\w*)\s+(?:доконаного|недоконаного)\s+виду\b",
            re.IGNORECASE,
        ),
        r"\1 ",
    ),
    # Tense modifying verb, participle, or form
    (
        re.compile(
            r"\b(дієслов\w*|дієприкметник\w*|форм\w*)\s+(?:теперішнього|минулого|майбутнього)\s+часу\b",
            re.IGNORECASE,
        ),
        r"\1 ",
    ),
    # Declension modifying noun, adjective, or form
    (
        re.compile(
            r"\b(іменник\w*|прикметник\w*|форм\w*)\s+(?:першої|другої|третьої|четвертої)\s+відміни\b",
            re.IGNORECASE,
        ),
        r"\1 ",
    ),
    # Group modifying noun, adjective, or form
    (
        re.compile(
            r"\b(іменник\w*|прикметник\w*|форм\w*)\s+(?:твердої|м['’ʼ]?якої|мішаної)\s+групи\b",
            re.IGNORECASE,
        ),
        r"\1 ",
    ),
    # Number modifying grammatical category words
    (
        re.compile(
            r"\b(?:(?:у\s+|в\s+)(?:формі|формах|відмінку|відмінках)|(?:числа|числі|відмінка|відмінків|особі|особах))\s+(?:однини|множини)\b",
            re.IGNORECASE,
        ),
        " ",
    ),
    # Prepositional adverbial number constructions
    (
        re.compile(r"\b(?:лише\s+|тільки\s+)?(?:в|у)\s+(?:однині|множині)\b", re.IGNORECASE),
        " ",
    ),
]


def normalize_token(s: str) -> str:
    """Strip accents and non-alphanumeric punctuation."""
    s = re.sub(r"[\u0300\u0301]", "", s)
    return s.strip().strip("«»\"'.,;:!?()[]{}").lower()


def evaluate_single_response(
    target_term: str,
    valid_alternatives: list[str],
    response_text: str,
) -> dict[str, Any]:
    """Evaluate one model output against gold decolonization targets."""
    resp_norm = response_text.lower().strip()
    term_norm = normalize_token(target_term)

    tokens = [t for t in re.split(r"\W+", resp_norm) if t]

    # Empty, whitespace-only, punctuation-only (tokenless), or vacuous responses fail immediately
    if not resp_norm or not tokens:
        return {
            "target_term": target_term,
            "calque_eliminated": False,
            "authentic_suggested": False,
            "matched_alternatives": [],
            "reasoning_grounded": False,
            "reasoning_hits": 0,
            "composite_score": 0.0,
            "is_pass": False,
        }

    # Refusal / evasion check: explicit refusal fails immediately
    for r_pat in REFUSAL_PATTERNS:
        if r_pat.search(resp_norm):
            return {
                "target_term": target_term,
                "calque_eliminated": False,
                "authentic_suggested": False,
                "matched_alternatives": [],
                "reasoning_grounded": False,
                "reasoning_hits": 0,
                "composite_score": 0.0,
                "is_pass": False,
            }

    # 1. Calque elimination check:
    # If the model explicitly affirms, defends, or recommends the calque, it fails elimination.
    calque_affirmed = False
    for pat in AFFIRMATION_PATTERNS:
        regex = re.compile(pat.format(term=re.escape(term_norm)), re.IGNORECASE)
        if regex.search(resp_norm):
            calque_affirmed = True
            break

    # If the calque is mentioned, check if it is explicitly framed as an error / calque / incorrect
    calque_present = term_norm in resp_norm
    critique_markers = (
        "кальк",
        "помилк",
        "росіян",
        "не рекоменд",
        "не варто",
        "штучн",
        "замін",
        "замість",
        "уникати",
        "суржик",
        "неправильн",
        "радянськ",
    )
    has_critique = any(m in resp_norm for m in critique_markers)

    if calque_affirmed:
        calque_eliminated = False
    elif calque_present:
        calque_eliminated = has_critique
    else:
        # Calque not mentioned; require active linguistic recommendation context
        calque_eliminated = any(
            m in resp_norm
            for m in ("правильн", "норм", "вжива", "рекоменд", "краще", "варто", "слід", "слово", "відповідник", "мовн")
        )

    # 2. Authentic suggestion check:
    # Does the response recommend at least one verified Ukrainian equivalent without negating it?
    matched_alts = []
    for alt in valid_alternatives:
        alt_norm = normalize_token(alt)
        if not alt_norm or alt_norm not in resp_norm:
            continue

        # Check if this alternative is negated or discouraged
        is_negated = False
        for n_pat in ALTERNATIVE_NEGATION_PATTERNS:
            n_regex = re.compile(n_pat.format(alt=re.escape(alt_norm), term=re.escape(term_norm)), re.IGNORECASE)
            if n_regex.search(resp_norm):
                is_negated = True
                break

        if is_negated:
            continue

        # Ignore suggestions that are merely inside attributed quotations (e.g. написано «alt»)
        quoted_in_attribution = re.search(
            rf"(?:написано|записано|сказано|процитовано|йдеться\s+про)\s*[«\"'\(][^»\"'\)]*{re.escape(alt_norm)}",
            resp_norm,
        )
        if quoted_in_attribution:
            continue

        # Check for prescriptive/normative suggestion context
        is_suggested = False
        for s_pat in SUGGESTION_PATTERNS:
            s_regex = re.compile(s_pat.format(alt=re.escape(alt_norm)), re.IGNORECASE)
            if s_regex.search(resp_norm):
                is_suggested = True
                break

        if is_suggested:
            matched_alts.append(alt)

    authentic_suggested = len(matched_alts) > 0
    if not calque_present and not authentic_suggested:
        calque_eliminated = False

    # 3. Morphemic and historical reasoning grounding check:
    tokens = [t for t in re.split(r"\W+", resp_norm) if t]
    content_tokens = [t for t in tokens if len(t) > 2]
    max_content_freq_ratio = max(Counter(content_tokens).values()) / len(content_tokens) if content_tokens else 0.0
    is_repetitive = (len(tokens) < 20 and (len(set(tokens)) / len(tokens)) < 0.65) or (
        len(tokens) >= 5 and max_content_freq_ratio > 0.20
    )

    # Verify reasoning actually references the linguistic subject (target term or alternative)
    target_tokens = {term_norm} | {normalize_token(a) for a in valid_alternatives if normalize_token(a)}
    all_target_tokens = target_tokens | {w for t in target_tokens for w in t.split()}
    sentences = [s.strip() for s in re.split(r"[.!?\n]+", resp_norm) if s.strip()]
    subject_sentences = [s for s in sentences if any(tt in s for tt in target_tokens)]
    subject_text = " ".join(subject_sentences)

    has_explanation_syntax = any(p.search(subject_text) for p in EXPLANATION_CONNECTIVES)
    has_linguistic_relation = any(p.search(subject_text) for p in LINGUISTIC_RELATION_PATTERNS)
    has_narrative_agent = any(p.search(resp_norm) for p in NARRATIVE_AGENT_PATTERNS)
    has_other_entity = any(p.search(resp_norm) for p in OTHER_ENTITY_PATTERNS)
    if not has_other_entity:
        analysis_text = re.sub(r"цитата:\s*[«\"“][^»\"”]+[»\"”]", "", resp_norm, flags=re.IGNORECASE)
        # Only strip grammatical modifier phrases in genuine modifier context outside protected spans
        parts = PROTECTED_SPAN_PATTERN.split(analysis_text)
        for i in range(0, len(parts), 2):
            while True:
                prev = parts[i]
                for pat, repl in GRAMMATICAL_MODIFIER_RULES:
                    parts[i] = pat.sub(repl, parts[i])
                if parts[i] == prev:
                    break
        analysis_text = "".join(parts)
        for pat in NAMED_ENTITY_PATTERNS:
            for m in pat.finditer(analysis_text):
                tok = normalize_token(m.group(1))
                if not tok or len(tok) <= 1:
                    continue
                if (
                    tok.startswith("-")
                    or tok.endswith("-")
                    or tok.startswith("–")
                    or tok.endswith("–")
                    or tok in EXEMPT_AFFIXES
                ):
                    continue
                words = tok.split()
                if tok in all_target_tokens or tok in GRAMMATICAL_STOPWORDS:
                    continue
                if any(w in all_target_tokens or w in GRAMMATICAL_STOPWORDS for w in words):
                    continue
                has_other_entity = True
                break
            if has_other_entity:
                break

    distinct_reasoning_markers = sum(1 for p in REASONING_MARKERS if p.search(subject_text))

    reasoning_grounded = (
        (distinct_reasoning_markers >= 2)
        and (not calque_affirmed)
        and (len(resp_norm) >= 35)
        and calque_eliminated
        and authentic_suggested
        and (not is_repetitive)
        and has_explanation_syntax
        and has_linguistic_relation
        and (not has_narrative_agent)
        and (not has_other_entity)
    )

    # 4. Composite score:
    # 0.40 calque_eliminated + 0.40 authentic_suggested + 0.20 reasoning_grounded
    composite_score = 0.0
    if calque_eliminated:
        composite_score += 0.40
    if authentic_suggested:
        composite_score += 0.40
    if reasoning_grounded:
        composite_score += 0.20

    # If the calque is affirmed or not eliminated, score is capped at 0.0
    if calque_affirmed or not calque_eliminated:
        composite_score = 0.0

    # If the response is repetitive keyword salad, lacks explanation syntax, or concerns another entity, cap score severely
    if is_repetitive or not has_explanation_syntax or has_other_entity:
        composite_score = min(composite_score, 0.40)

    # If reasoning is not grounded in the linguistic subject, cap score severely
    if not reasoning_grounded:
        composite_score = min(composite_score, 0.40)

    # If the response is an unsubstantiated fragment (< 35 characters), cap score
    if len(resp_norm) < 35:
        composite_score = min(composite_score, 0.40)

    # To achieve PASS, response must meet score threshold AND have verified reasoning grounding
    is_pass = (composite_score >= 0.80) and reasoning_grounded

    return {
        "target_term": target_term,
        "calque_eliminated": calque_eliminated,
        "authentic_suggested": authentic_suggested,
        "matched_alternatives": matched_alts,
        "reasoning_grounded": reasoning_grounded,
        "reasoning_hits": distinct_reasoning_markers,
        "composite_score": round(composite_score, 2),
        "is_pass": is_pass,
    }


def evaluate_predictions(
    held_out_path: Path,
    predictions_path: Path,
    out_report_path: Path | None = None,
) -> dict[str, Any]:
    """Evaluate predictions against the held-out partition with strict denominator reconciliation."""
    if not held_out_path.is_file():
        raise FileNotFoundError(f"Missing held-out benchmark file at {held_out_path}")
    if not predictions_path.is_file():
        raise FileNotFoundError(f"Missing predictions file at {predictions_path}")

    # Load gold items
    gold_items: dict[str, dict[str, Any]] = {}
    gold_by_id: dict[str, str] = {}
    with held_out_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            target = item.get("target_term") or normalize_token(item.get("query", ""))
            alts = [a["lemma"] for a in item.get("register_spectrum", {}).get("alternatives", [])]
            norm_key = normalize_token(target)
            gold_items[norm_key] = {
                "trajectory_id": item.get("trajectory_id"),
                "target_term": target,
                "alternatives": alts,
                "gold_response": item.get("final_response") or item.get("response"),
            }
            if item.get("trajectory_id"):
                gold_by_id[item["trajectory_id"]] = norm_key

    expected_denominator = len(gold_items)
    if expected_denominator == 0:
        raise ValueError(f"Held-out benchmark file {held_out_path} contains 0 valid gold records.")

    # Load predictions and map to gold items
    matched_predictions: dict[str, dict[str, Any]] = {}
    seen_prediction_ids: set[str] = set()
    duplicate_predictions: list[str] = []
    unknown_predictions: list[dict[str, Any]] = []

    with predictions_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pred = json.loads(line)
            pred_id = pred.get("id") or pred.get("trajectory_id", "")
            if pred_id and pred_id in seen_prediction_ids:
                duplicate_predictions.append(pred_id)
                continue
            if pred_id:
                seen_prediction_ids.add(pred_id)

            target = pred.get("target_term", "")
            norm_target = normalize_token(target)
            matched_gold_key: str | None = None

            # Priority 1: Exact trajectory ID match
            if pred_id and pred_id in gold_by_id:
                matched_gold_key = gold_by_id[pred_id]
            # Priority 2: Explicit target term match
            elif norm_target and norm_target in gold_items:
                matched_gold_key = norm_target
            # Priority 3: Fallback only if prompt unambiguously mentions EXACTLY ONE gold item
            elif pred.get("prompt"):
                prompt_lower = pred.get("prompt", "").lower()
                matching_keys = [k for k in gold_items if k and k in prompt_lower]
                if len(matching_keys) == 1:
                    matched_gold_key = matching_keys[0]

            if matched_gold_key:
                if matched_gold_key in matched_predictions:
                    duplicate_predictions.append(matched_gold_key)
                else:
                    matched_predictions[matched_gold_key] = pred
            else:
                unknown_predictions.append(pred)

    # Reconcile evaluations across the exact gold denominator
    results: list[dict[str, Any]] = []
    missing_count = 0

    for norm_key, gold in gold_items.items():
        if norm_key in matched_predictions:
            pred = matched_predictions[norm_key]
            resp_text = (
                pred.get("final_response") or pred.get("response") or pred.get("generated_text") or pred.get("text", "")
            )
            if not resp_text and "conversations" in pred and isinstance(pred["conversations"], list):
                resp_text = next(
                    (c.get("value", "") for c in pred["conversations"] if c.get("from") in ("gpt", "assistant")),
                    "",
                )
            if not resp_text and "messages" in pred and isinstance(pred["messages"], list):
                resp_text = next(
                    (m.get("content", "") for m in pred["messages"] if m.get("role") in ("assistant", "model")),
                    "",
                )
            eval_res = evaluate_single_response(gold["target_term"], gold["alternatives"], resp_text)
            eval_res["id"] = pred.get("id", gold["trajectory_id"])
            eval_res["status"] = "evaluated"
            results.append(eval_res)
        else:
            missing_count += 1
            results.append(
                {
                    "id": gold["trajectory_id"],
                    "target_term": gold["target_term"],
                    "calque_eliminated": False,
                    "authentic_suggested": False,
                    "matched_alternatives": [],
                    "reasoning_grounded": False,
                    "reasoning_hits": 0,
                    "composite_score": 0.0,
                    "is_pass": False,
                    "status": "missing_prediction",
                }
            )

    elim_count = sum(1 for r in results if r["calque_eliminated"])
    auth_count = sum(1 for r in results if r["authentic_suggested"])
    reas_count = sum(1 for r in results if r["reasoning_grounded"])
    pass_count = sum(1 for r in results if r["is_pass"])
    mean_score = sum(r["composite_score"] for r in results) / expected_denominator

    summary = {
        "expected_gold_records": expected_denominator,
        "total_evaluated": len(matched_predictions),
        "missing_records_count": missing_count,
        "duplicate_predictions_count": len(duplicate_predictions),
        "unknown_predictions_count": len(unknown_predictions),
        "calque_elimination_rate": round(elim_count / expected_denominator, 4),
        "authentic_suggestion_rate": round(auth_count / expected_denominator, 4),
        "reasoning_grounding_rate": round(reas_count / expected_denominator, 4),
        "mean_composite_score": round(mean_score, 4),
        "pass_rate": round(pass_count / expected_denominator, 4),
        "evaluations": results,
    }

    if out_report_path:
        out_report_path.parent.mkdir(parents=True, exist_ok=True)
        with out_report_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate model outputs against ULDR held-out benchmark")
    parser.add_argument("--held-out", type=Path, default=DEFAULT_HELD_OUT_FILE)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out-report", type=Path, default=None)

    args = parser.parse_args()
    summary = evaluate_predictions(args.held_out, args.predictions, args.out_report)
    print("=== ULDR Evaluation Benchmark Results ===")
    print(f"Total Evaluated:             {summary['total_evaluated']}")
    print(f"Calque Elimination Rate:     {summary['calque_elimination_rate']:.2%}")
    print(f"Authentic Suggestion Rate:   {summary['authentic_suggestion_rate']:.2%}")
    print(f"Reasoning Grounding Rate:    {summary['reasoning_grounding_rate']:.2%}")
    print(f"Mean Composite Score:        {summary['mean_composite_score']:.4f}")
    print(f"Pass Rate (Score >= 0.80):   {summary['pass_rate']:.2%}")
    if args.out_report:
        print(f"Full report saved to {args.out_report}")


if __name__ == "__main__":
    main()
