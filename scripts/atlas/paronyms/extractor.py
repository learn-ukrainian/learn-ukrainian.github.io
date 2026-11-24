"""Deterministic, source-grounded Ukrainian paronym extractor.

Extracts ONLY explicit paronym presentations (dictionary entries, dash/slash
pairs, explicit paronym exercises) from plain text documents (textbook chunks
and MiyKlas pages). Every output pair carries the exact source locator and
verbatim quoted excerpt sliced directly from the raw source text; nothing is
inferred from model knowledge.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from itertools import combinations, pairwise

# Ukrainian alphabet characters (no Russian-only letters ы/э/ё/ъ).
UK_LOWER = "а-щьюяєіїґ"
UK_UPPER = "А-ЩЬЮЯЄІЇҐ"
UK_LETTER = f"{UK_UPPER}{UK_LOWER}"
APOS = "'’ʼ"

# Single Ukrainian word (optionally with apostrophe or internal hyphen).
WORD_CORE = rf"[{UK_LETTER}]+(?:[{APOS}][{UK_LETTER}]+)*(?:-[{UK_LETTER}]+)?"
# Dictionary headword may occasionally be a 2-word expression (e.g. "На протязі"),
# which VESUM verification routes to the unverified list with an explicit reason.
HEADWORD_EXPR = rf"[{UK_UPPER}][{UK_LOWER}{APOS}]+(?:\s+[{UK_LOWER}{APOS}]+)?"

DASH_CHARS = "—–−"
DASH_SEP = rf"\s*[{DASH_CHARS}]\s*"

# Structural labels, conjunctions, prepositions, or metalanguage — never a bare paronym member.
_STOPWORDS = frozenset(
    {
        "а",
        "або",
        "адже",
        "але",
        "антоніми",
        "б",
        "без",
        "близькі",
        "бо",
        "в",
        "від",
        "він",
        "вона",
        "вони",
        "воно",
        "все",
        "всі",
        "г",
        "гр",
        "грец",
        "д",
        "де",
        "джерела",
        "дієслова",
        "для",
        "до",
        "дуже",
        "е",
        "є",
        "ж",
        "же",
        "з",
        "за",
        "зауважте",
        "зразок",
        "і",
        "із",
        "іменники",
        "ін",
        "й",
        "к",
        "коли",
        "лат",
        "лексичні",
        "лише",
        "м",
        "ми",
        "між",
        "на",
        "над",
        "наприклад",
        "не",
        "неправильно",
        "ні",
        "омоніми",
        "отже",
        "паронім",
        "пароніми",
        "паронімія",
        "під",
        "по",
        "правильно",
        "при",
        "приклад",
        "приклади",
        "прикметники",
        "прислівники",
        "про",
        "різні",
        "розм",
        "рос",
        "с",
        "синоніми",
        "слід",
        "слів",
        "слова",
        "словник",
        "слово",
        "та",
        "так",
        "такі",
        "там",
        "те",
        "теорія",
        "ти",
        "то",
        "тобто",
        "тому",
        "тощо",
        "тут",
        "у",
        "усі",
        "це",
        "цих",
        "ці",
        "через",
        "чи",
        "що",
        "щоб",
        "я",
        "як",
        "яка",
        "яке",
        "який",
        "які",
        "якщо",
    }
)

_PARONYM_CUE_RE = re.compile(r"пар[оî]\s*нім", re.IGNORECASE)

# Mentions of paronyms in passing (overview lists or book-title lists) that do NOT
# themselves start a paronym presentation section.
_PASSING_MENTION_RE = re.compile(
    r"(?:синонім\w*[,\s]+(?:омонім\w*[,\s]+|антонім\w*[,\s]+)+[ійта\s]*паронім|"
    r"омонім\w*[,\s]+(?:синонім\w*[,\s]+|антонім\w*[,\s]+)+[ійта\s]*паронім|"
    r"антонім\w*[,\s]+(?:синонім\w*[,\s]+|омонім\w*[,\s]+)+[ійта\s]*паронім|"
    r"«словник\s+паронімів»|словники\s+синонімів|"
    # A prose reference to a paronym dictionary ("У додатку є Словничок паронімів") points
    # elsewhere; only a standalone heading line opens a dictionary.
    r"(?:словнич(?:ок|ка|ку|ком)|словник(?:а|у|ом)?)\s+паронімів|"
    r"стилістичне\s+використання\s+(?:омонімів|синонімів)[^\n]{0,40}паронімів|"
    r"багатозначні\s+й\s+однозначні[^\n]{0,80}омоніми\.\s*пароніми)",
    re.IGNORECASE,
)

# Section switches away from paronyms.
_NON_PARONYM_SECTION_RE = re.compile(
    r"(?:^|\n|\.\s+)(?:"
    r"антонім(?:и|ами|ічн)|"
    r"синонім(?:и|ами|ічн)|"
    r"омонім(?:и|ами|ічн)|"
    r"омограф|омофон|омоформ|"
    r"у\s+словнику\s+(?:антонімів|синонімів|омонімів)|"
    r"енантіосемі|"
    r"рекомендована\s+література|"
    r"культура\s+(?:слова|мовлення)|"
    r"перевірте\s+себе|"
    r"питання\s+для\s+самоконтролю|"
    r"§\s*\d+\s+(?:найпоширеніші|стилістичне\s+використання\s+синонімів|групи\s+слів|словники\s+як)|"
    r"до\s+лексичних\s+помилок\s+належать|"
    r"порушення\s+лексичних\s+норм|"
    r"правильно\s+неправильно|неправильно\s+правильно|"
    r"активна\s+лексика|пасивна\s+лексика|терміни\s*\(|професіоналізми\s*[—–-]|"
    r"ііі\.\s+за\s+епідигматичним|"
    r"іншим\s+різновидом\s+парадигматичних\s+відношень\s+між\s+словами\s+є\s+антонімічні|"
    r"додаток\s+1\b|"
    r"орфографічна\s+норма|приголосні\s+основи\s+\[|"
    r"фонетика\.\s+графіка|"
    r"модуль\s+\d+|дидактична\s+мета|"
    r"векторні\s+антоніми|евфемізм\s*[—–−-]"
    r")",
    re.IGNORECASE,
)

# Non-paronym lexical topics anywhere in a segment lacking an active paronym cue.
_OTHER_LEXICAL_TOPIC_RE = re.compile(
    r"(?<![а-яіїєґ'])"
    r"(?:антонім\w*|синонім\w*|омонім\w*|омограф\w*|омофон\w*|омоформ\w*|фразеологізм\w*)",
    re.IGNORECASE,
)

# Explicit non-paronym disclaimers (e.g. narrow-definition exclusions, non-existent words).
_PARONYM_DICTIONARY_REFERENCE_RE = re.compile(
    r"(?:скористайтеся|скористайтесь|зверніться\s+до|користуйтеся|перевірте\s+за)\s+"
    r"(?:словнич(?:ок|ка|ку|ком)|словник(?:а|у|ом)?)\s+паронімів",
    re.IGNORECASE,
)

_DISCLAIMER_RE = re.compile(
    r"(?:не\s+є\s+паронім|від\s+паронімів\s+(?:слід|необхідно|а\s+відповідно)|"
    r"таких\s+слів\s*,\s*як\b|в\s+українських\s+словниках\s+немає|"
    r"заміна\s+слова\s+паронімом|"
    r"згідно\s+з\s+вузьким\s+розумінням\s+паронімії\s+не\s+всі)",
    re.IGNORECASE,
)

# Multiple-choice tests and mixed sorting/filtering quizzes containing distractors.
_MULTIPLE_CHOICE_RE = re.compile(
    r"(?:пароніми\s+(?:записано|вжито)|немає\s+паронімів|паронімом\s+до\s+слова|"
    r"(?:антоніми|синоніми|омоніми)\s+(?:записано|вжито)|"
    r"знайдіть\s+рядок\s*,\s*у\s+якому|виберіть\s+рядок\s*,\s*у\s+якому|"
    r"випишіть\s+лише\s+ті\s+пари|"
    r"виконайте\s+(?:тестові\s+)?завдання\s+в\s+тестовій|установіть\s+відповідність|"
    r"помилку\s+у\s+творенні|орфографічну\s+помилку)",
    re.IGNORECASE,
)

_PDF_PUA_STRESS_RE = re.compile(r"[\u0301\u0300\u02c8\u00ad\u200b\ufeff\ue000-\ue0ff]")
_INLINE_DIGIT_STRESS_RE = re.compile(rf"(?<=[{UK_LETTER}])5(?=[{UK_LOWER}])")
_LINE_WRAP_HYPHEN_RE = re.compile(rf"([{UK_LOWER}{APOS}])-\s*\n\s*([{UK_LOWER}])")
_TOC_RE = re.compile(r"(?:\.{5,}|(?:\.\s){5,})")


@dataclass(frozen=True)
class SourceDocument:
    """One textbook chunk or MiyKlas page fed to the paronym extractor."""

    source_type: str  # "textbook" | "miyklas"
    source_file: str
    chunk_id: str
    locator: str
    title: str
    text: str
    grade: str = ""
    author: str = ""
    source_url: str = ""
    fetch_date_utc: str = ""
    raw_html_sha256: str = ""
    text_sha256: str = ""


@dataclass(frozen=True)
class MemberNote:
    """One member of a paronym pair as presented by a source."""

    word: str
    attested_form: str


@dataclass(frozen=True)
class RawPairAttestation:
    """One source-attested paronym pair extracted verbatim from a SourceDocument."""

    member_a: MemberNote
    member_b: MemberNote
    source_type: str
    source_file: str
    chunk_id: str
    locator: str
    pattern: str
    quoted_line: str
    source_url: str = ""


def normalize_token(raw: str) -> str:
    """Normalize a Ukrainian token for canonical matching (NFC, unstressed, ASCII apostrophe)."""
    text = unicodedata.normalize("NFC", raw)
    text = _PDF_PUA_STRESS_RE.sub("", text)
    text = _INLINE_DIGIT_STRESS_RE.sub("", text)
    text = text.replace("’", "'").replace("ʼ", "'").replace("`", "'")
    return " ".join(text.strip().lower().split())


def _clean_text_with_map(raw_text: str) -> tuple[str, list[int]]:
    """Clean PDF/HTML artifacts for parsing while mapping every char back to ``raw_text``.

    Returns ``(clean_text, clean_to_raw)`` where ``len(clean_to_raw) == len(clean_text) + 1``
    so any slice ``clean_text[s:e]`` corresponds to the exact verbatim span
    ``raw_text[clean_to_raw[s]:clean_to_raw[e]]``.
    """
    n = len(raw_text)
    out_chars: list[str] = []
    out_map: list[int] = []
    i = 0
    while i < n:
        ch = raw_text[i]
        if ch == "\r":
            out_chars.append("\n")
            out_map.append(i)
            i += 2 if (i + 1 < n and raw_text[i + 1] == "\n") else 1
            continue
        if ch == "\u00a0":
            out_chars.append(" ")
            out_map.append(i)
            i += 1
            continue
        if _PDF_PUA_STRESS_RE.fullmatch(ch):
            i += 1
            continue
        if (
            ch == "5"
            and out_chars
            and re.fullmatch(rf"[{UK_LETTER}]", out_chars[-1])
            and i + 1 < n
            and re.fullmatch(rf"[{UK_LOWER}]", raw_text[i + 1])
        ):
            i += 1
            continue
        if ch == "-" and out_chars and re.fullmatch(rf"[{UK_LOWER}{APOS}]", out_chars[-1]):
            j = i + 1
            saw_nl = False
            while j < n and raw_text[j] in " \t\r\n\u00a0":
                if raw_text[j] in "\r\n":
                    saw_nl = True
                j += 1
            if saw_nl and j < n and re.fullmatch(rf"[{UK_LOWER}]", raw_text[j]):
                # Skip the soft line-wrap hyphen and intervening whitespace/newline.
                i = j
                continue
        out_chars.append(ch)
        out_map.append(i)
        i += 1
    out_map.append(n)
    return "".join(out_chars), out_map


def _clean_text_for_parsing(raw_text: str) -> str:
    """Clean PDF/HTML artifacts while keeping line structure for parsing."""
    clean_text, _ = _clean_text_with_map(raw_text)
    return clean_text


def _raw_quote(raw_text: str, clean_to_raw: list[int], clean_start: int, clean_end: int) -> str:
    """The verbatim ``raw_text`` span behind ``clean_text[clean_start:clean_end]``."""
    limit = len(clean_to_raw) - 1
    s = max(0, min(clean_start, limit))
    e = max(s, min(clean_end, limit))
    raw_start = clean_to_raw[s]
    raw_end = clean_to_raw[e]
    return raw_text[raw_start:raw_end]


def _flatten_with_map(text: str, base_offset: int) -> tuple[str, list[int]]:
    """Collapse internal whitespace runs to single spaces with an offset map into ``clean_text``."""
    out_chars: list[str] = []
    out_map: list[int] = []
    i = 0
    n = len(text)
    # Trim leading whitespace
    while i < n and text[i].isspace():
        i += 1
    end_trim = n
    while end_trim > i and text[end_trim - 1].isspace():
        end_trim -= 1
    while i < end_trim:
        if text[i].isspace():
            out_chars.append(" ")
            out_map.append(base_offset + i)
            while i < end_trim and text[i].isspace():
                i += 1
        else:
            out_chars.append(text[i])
            out_map.append(base_offset + i)
            i += 1
    out_map.append(base_offset + end_trim)
    return "".join(out_chars), out_map


def _clean_note_text(snippet: str) -> str:
    """Normalise source text for parsing (NFC, collapsed whitespace)."""
    return " ".join(unicodedata.normalize("NFC", snippet).replace("\u00a0", " ").split())


def _is_valid_single_word(token: str) -> bool:
    norm = normalize_token(token)
    if not norm or " " in norm or len(norm) < 2:
        return False
    if norm in _STOPWORDS:
        return False
    return bool(re.fullmatch(rf"[{UK_LOWER}]+(?:'[{UK_LOWER}]+)*(?:-[{UK_LOWER}]+)?", norm))


def _is_valid_headword(token: str) -> bool:
    """Allow single words or short 2-word dictionary headwords (e.g. 'На протязі')."""
    norm = normalize_token(token)
    if not norm or len(norm) < 2:
        return False
    parts = norm.split()
    if len(parts) == 1:
        return _is_valid_single_word(norm)
    if len(parts) == 2:
        return all(bool(re.fullmatch(rf"[{UK_LOWER}']+", p)) for p in parts)
    return False


def _emit_group_pairs(
    members: list[MemberNote],
    doc: SourceDocument,
    *,
    pattern: str,
    quoted_line: str,
) -> list[RawPairAttestation]:
    """Expand a 2..4-member paronym group into canonical unordered pairs."""
    out: list[RawPairAttestation] = []
    deduped: list[MemberNote] = []
    seen_words: set[str] = set()
    for m in members:
        if m.word and m.word not in seen_words:
            seen_words.add(m.word)
            deduped.append(m)
    if len(deduped) < 2 or len(deduped) > 4:
        return out
    for left, right in combinations(deduped, 2):
        a, b = (left, right) if left.word <= right.word else (right, left)
        out.append(
            RawPairAttestation(
                member_a=a,
                member_b=b,
                source_type=doc.source_type,
                source_file=doc.source_file,
                chunk_id=doc.chunk_id,
                locator=doc.locator,
                pattern=pattern,
                quoted_line=quoted_line,
                source_url=doc.source_url,
            )
        )
    return out


# ── Pattern 1a: Slash-headed dictionary entries (e.g. Zabolotnyi Додаток 2) ──

_SLASH_DICT_HEADER_RE = re.compile(rf"^({WORD_CORE}(?:\s*//\s*{WORD_CORE}){{1,3}})\s*$")
_DEF_LINE_RE = re.compile(rf"^({HEADWORD_EXPR})\s*[{DASH_CHARS}]\s+(.+)$")
_INLINE_DICT_SPLIT_RE = re.compile(
    rf"(?<=[.)])\s+(?=[{UK_UPPER}][{UK_LOWER}{APOS}]+(?:\s+[{UK_LOWER}{APOS}]+)?\s*[{DASH_CHARS}]\s+)"
)


def _line_spans(text: str) -> list[tuple[int, int, str]]:
    """Return ``(start, end, stripped_text)`` for each line in ``text``."""
    spans: list[tuple[int, int, str]] = []
    pos = 0
    for raw_line in text.splitlines(keepends=True):
        body = raw_line.rstrip("\r\n")
        lpad = len(body) - len(body.lstrip())
        stripped = body.strip()
        spans.append((pos + lpad, pos + lpad + len(stripped), stripped))
        pos += len(raw_line)
    return spans


# Dictionary headings must stand on their own line; a prose mention such as
# "У додатку є Словничок паронімів" does not open a dictionary.
_SLASH_DICT_HEADING_RE = re.compile(r"^[ \t]*словнич[оа]к\s+паронімів\.?[ \t]*$", re.IGNORECASE | re.MULTILINE)
_MIYKLAS_DICT_HEADING_RE = re.compile(r"^[ \t]*короткий\s+словник\s+паронімів\.?[ \t]*$", re.IGNORECASE | re.MULTILINE)


def _extract_slash_dictionary(
    clean_text: str, clean_to_raw: list[int], doc: SourceDocument
) -> list[RawPairAttestation]:
    m_heading = _SLASH_DICT_HEADING_RE.search(clean_text)
    if not m_heading:
        return []
    line_spans = _line_spans(clean_text)
    out: list[RawPairAttestation] = []
    # The dictionary starts at its heading; text above it in the same chunk is not part of it.
    i = next((n for n, (_, end, _) in enumerate(line_spans) if end > m_heading.start()), len(line_spans))
    while i < len(line_spans):
        l_start, _, ln_text = line_spans[i]
        m_hdr = _SLASH_DICT_HEADER_RE.match(ln_text)
        if not m_hdr:
            i += 1
            continue
        raw_headwords = [h.strip() for h in m_hdr.group(1).split("//")]
        norm_targets = {normalize_token(h): h for h in raw_headwords if _is_valid_headword(h)}
        if len(norm_targets) < 2:
            i += 1
            continue
        block_start = l_start
        block_end = line_spans[i][1]
        i += 1
        entries: dict[str, str] = {}
        current_key: str | None = None
        while i < len(line_spans):
            _, cur_end, ln = line_spans[i]
            if not ln or _SLASH_DICT_HEADER_RE.match(ln) or re.fullmatch(r"\d{1,3}", ln):
                break
            m_def = _DEF_LINE_RE.match(ln)
            if m_def and normalize_token(m_def.group(1)) in norm_targets:
                current_key = normalize_token(m_def.group(1))
                entries[current_key] = m_def.group(2).strip()
            elif current_key is not None:
                entries[current_key] = f"{entries[current_key]} {ln}".strip()
            block_end = cur_end
            i += 1
        block_quote = _raw_quote(doc.text, clean_to_raw, block_start, block_end)
        members: list[MemberNote] = []
        for norm_w, raw_w in norm_targets.items():
            members.append(MemberNote(word=norm_w, attested_form=raw_w))
        out.extend(_emit_group_pairs(members, doc, pattern="slash_dictionary", quoted_line=block_quote))
    return out


# ── Pattern 1b: Blank-line-grouped MiyKlas dictionary ("Короткий словник паронімів") ──


def _extract_miyklas_dictionary(
    clean_text: str, clean_to_raw: list[int], doc: SourceDocument
) -> list[RawPairAttestation]:
    m_heading = _MIYKLAS_DICT_HEADING_RE.search(clean_text)
    if not m_heading:
        return []
    out: list[RawPairAttestation] = []
    # The dictionary starts at its heading; blocks above it in the same page are not part of it.
    pos = m_heading.start()
    for sep_m in [*re.compile(r"\n\s*\n").finditer(clean_text, pos), None]:
        block_end = sep_m.start() if sep_m is not None else len(clean_text)
        block_start = pos
        block = clean_text[block_start:block_end]
        pos = sep_m.end() if sep_m is not None else len(clean_text)
        if re.match(r"^\s*Джерела\s*:", block, re.IGNORECASE):
            break
        raw_lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        # Also split lines where two consecutive entries share one HTML div without <br/>.
        expanded_lines: list[str] = []
        for ln in raw_lines:
            expanded_lines.extend(part.strip() for part in _INLINE_DICT_SPLIT_RE.split(ln) if part.strip())
        if len(expanded_lines) < 2:
            continue
        members: list[MemberNote] = []
        for ln in expanded_lines:
            m = _DEF_LINE_RE.match(ln)
            if not m:
                continue
            raw_hw = m.group(1).strip()
            if not _is_valid_headword(raw_hw):
                continue
            members.append(MemberNote(word=normalize_token(raw_hw), attested_form=raw_hw))
        if 2 <= len(members) <= 4:
            quote = _raw_quote(doc.text, clean_to_raw, block_start, block_end)
            out.extend(
                _emit_group_pairs(
                    members,
                    doc,
                    pattern="dictionary_block",
                    quoted_line=quote,
                )
            )
    return out


# ── Pattern 1c: Named inline dictionary boxes in textbooks ──

_NAMED_DEF_BOX_TRIGGERS = (
    re.compile(
        r"запам['’ʼ]ятайте\s+значення\s+паронім(?:ів|ічних\s+[а-яіїєґ']+)?\s*[.:]",
        re.IGNORECASE,
    ),
    re.compile(r"розрізняйте\s+пароніми\b[^\n.]*\.", re.IGNORECASE),
    re.compile(r"в\s+українській\s+мові\s+маємо\s+пароніми\b[^\n.]*\.", re.IGNORECASE),
    re.compile(
        rf"({WORD_CORE})\s+[іійта]+\s+({WORD_CORE})\s*[{DASH_CHARS}]\s*пароніми[^\n.]*\.",
        re.IGNORECASE,
    ),
    re.compile(r"має\s+словник\s+паронімів\s*:", re.IGNORECASE),
)

_BOX_STOP_RE = re.compile(
    r"(?:^|\n)\s*\d{1,3}(?:\s+\d{1,3})?\s*(?=\n|$)|"
    r"(?:^|\n|\s)(?:"
    r"\d{1,3}\.\s+[А-ЯІЇЄҐ]|"
    r"у\s+словнику\s+(?:омонімів|антонімів|синонімів)|"
    r"зверніть\s+увагу!|"
    r"зверни\s+увагу!|"
    r"цікаво,\s+що|"
    r"зауважте!|"
    r"вправа\s+\d+|"
    r"розділ\s+\d+"
    r")",
    re.IGNORECASE,
)

_INLINE_HEADWORD_DEF_RE = re.compile(
    rf"(?:^|(?<=\.\s)|(?<=\n))([{UK_UPPER}][{UK_LOWER}{APOS}]+)\s*[{DASH_CHARS}]\s+(.+?)"
    rf"(?=(?:\.\s+[{UK_UPPER}][{UK_LOWER}{APOS}]+\s*[{DASH_CHARS}]\s+)|\Z)",
    re.DOTALL,
)


def _extract_named_definition_boxes(
    clean_text: str, clean_to_raw: list[int], doc: SourceDocument
) -> tuple[list[RawPairAttestation], list[tuple[int, int]]]:
    """Extract textbook definition boxes and return (attestations, consumed_char_spans)."""
    out: list[RawPairAttestation] = []
    consumed: list[tuple[int, int]] = []
    for trig in _NAMED_DEF_BOX_TRIGGERS:
        for m in trig.finditer(clean_text):
            tail_start = m.end()
            tail = clean_text[tail_start : tail_start + 1200]
            stop_m = _BOX_STOP_RE.search(tail)
            segment = tail[: stop_m.start()] if stop_m else tail
            segment_body = re.sub(
                rf"^\s*[{UK_UPPER}{APOS}]+\s*[{DASH_CHARS}]\s*[{UK_UPPER}{APOS}]+\s*\n",
                "",
                segment,
            )
            flat = _clean_note_text(segment_body)
            entries = list(_INLINE_HEADWORD_DEF_RE.finditer(flat))
            members: list[MemberNote] = []
            for em in entries:
                raw_hw = em.group(1).strip()
                if not _is_valid_single_word(raw_hw):
                    continue
                members.append(MemberNote(word=normalize_token(raw_hw), attested_form=raw_hw))
            if 2 <= len(members) <= 4:
                span_end = tail_start + (stop_m.start() if stop_m else len(tail))
                # Trim trailing whitespace from span_end for clean raw slice.
                while span_end > m.start() and clean_text[span_end - 1].isspace():
                    span_end -= 1
                full_quote = _raw_quote(doc.text, clean_to_raw, m.start(), span_end)
                out.extend(
                    _emit_group_pairs(
                        members,
                        doc,
                        pattern="dictionary_block",
                        quoted_line=full_quote,
                    )
                )
                consumed.append((m.start(), span_end))

    # Structured 2-line definition pairs right after a paronym cue (e.g. 6-klas Avramenko
    # "Замерзнути — ... / Змерзнути — ...", MiyKlas 5-klas "Виборний — ... / Виборчий — ...").
    if _PARONYM_CUE_RE.search(clean_text):
        line_spans = _line_spans(clean_text)
        lines = [ln for _, _, ln in line_spans]
        for idx in range(len(line_spans) - 1):
            s1, _, l1 = line_spans[idx]
            _, e2, l2 = line_spans[idx + 1]
            if any(not (e2 <= cs or s1 >= ce) for cs, ce in consumed):
                continue
            m1 = _DEF_LINE_RE.match(l1)
            m2 = _DEF_LINE_RE.match(l2)
            if not (m1 and m2):
                continue
            w1, w2 = m1.group(1).strip(), m2.group(1).strip()
            if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
                continue
            n1, n2 = normalize_token(w1), normalize_token(w2)
            if n1 == n2 or not _is_similar_enough_for_paronym(w1, w2):
                continue
            context_above = "\n".join(lines[max(0, idx - 5) : idx])
            # The pair needs a local paronym cue just above it; the two words merely being
            # mentioned there is not evidence that the text is about paronyms.
            if _DISCLAIMER_RE.search(context_above) or not (
                _has_active_paronym_cue(context_above)
                or re.search(r"відрізняються\s+слова", context_above, re.IGNORECASE)
            ):
                continue
            if _NON_PARONYM_SECTION_RE.search(context_above):
                continue
            g1, g2 = m1.group(2).strip(), m2.group(2).strip()
            if len(g1.split()) < 2 or len(g2.split()) < 2:
                continue
            raw_pair_quote = _raw_quote(doc.text, clean_to_raw, s1, e2)
            members = [MemberNote(word=n1, attested_form=w1), MemberNote(word=n2, attested_form=w2)]
            out.extend(
                _emit_group_pairs(
                    members,
                    doc,
                    pattern="dictionary_block",
                    quoted_line=raw_pair_quote,
                )
            )
            consumed.append((s1, e2))
    return out, consumed


# ── Pattern 2..9 regexes ──

_INLINE_DEF_PAIR_RE = re.compile(
    rf"(?<![{UK_LETTER}])({WORD_CORE})\s*[{DASH_CHARS}]\s*([^;.!?]{{6,140}}?)"
    rf"\s+(?:і|й|а|та)\s+({WORD_CORE})\s*[{DASH_CHARS}]\s*([^;.!?]{{6,140}})",
    re.IGNORECASE,
)

_PAREN_GLOSS_PAIR_RE = re.compile(
    rf"(?<![{UK_LETTER}])({WORD_CORE})\s*\(([^()\n]{{3,100}})\)\s*"
    rf"(?:[{DASH_CHARS}]|\bі\b|\bта\b)\s*({WORD_CORE})\s*\(([^()\n]{{3,100}})\)",
    re.IGNORECASE,
)

# Double-slash ("Людяний // людний") or single-slash with collocation colon ("Особистий / особовий: ...")
_DOUBLE_SLASH_CHAIN_RE = re.compile(
    rf"(?<![{UK_LETTER}])({WORD_CORE})(?:\s*//\s*({WORD_CORE})){{1,2}}(?![{UK_LETTER}])"
)
_COLON_SLASH_CHAIN_RE = re.compile(rf"(?<![{UK_LETTER}])({WORD_CORE})\s*/\s*({WORD_CORE})\s*:\s*([^.\n]{{4,180}})")

_CONJ_PAIR_RE = re.compile(
    rf"(?:пароніми|паронімів)\s+({WORD_CORE})\s+(?:та|і|й|або)\s+({WORD_CORE})\b|"
    rf"слова\s+({WORD_CORE})\s+(?:та|і|й)\s+({WORD_CORE})\s+паронімами\b",
    re.IGNORECASE,
)
_WHEN_USE_PAIR_RE = re.compile(
    rf"вживаємо\s+слово\s+({WORD_CORE})\s*,\s*а\s+коли\s*[{DASH_CHARS}]\s*({WORD_CORE})\b",
    re.IGNORECASE,
)
_COLON_CONJ_LIST_RE = re.compile(
    rf"пароніми[^:\n]{{0,120}}:\s*({WORD_CORE}\s+(?:і|та|й)\s+{WORD_CORE}"
    rf"(?:\s*[,;]\s*{WORD_CORE}\s+(?:і|та|й)\s+{WORD_CORE})*)",
    re.IGNORECASE,
)

_SEMICOLON_COMMA_ITEM_RE = re.compile(rf"^\s*({WORD_CORE}(?:\s*,\s*{WORD_CORE}){{1,2}})(?:\s*\(([^()]{{3,80}})\))?\s*$")

_CHOICE_EXERCISE_PROMPT_RE = re.compile(
    r"(?:вибираючи|добираючи|вибравши|виберіть|розкривши\s+дужки)[^.\n]{0,120}"
    r"(?:дуж|потрібне\s+слово|потрібні\s+слова|доцільне)",
    re.IGNORECASE,
)
_CHOICE_PAIR_RE = re.compile(rf"\(\s*({WORD_CORE})\s*,\s*({WORD_CORE})\s*\)")

_QUESTION_PAIR_RE = re.compile(rf"(?:^|\n)\s*({WORD_CORE})\?\s*\n?\s*({WORD_CORE})\?(?=\s*(?:\n|$))")

_EXPLICIT_PARONYM_SECTION_HEADER_RE = re.compile(
    r"^\s*(?:"
    r"§\s*\d+\.?\s*пароніми(?:\.\s*запобігання(?:\s+помилкам(?:\s+у\s+вживанні\s+паронімів)?)?)?\.?|"
    r"пароніми\.\s*запобігання(?:\s+помилкам(?:\s+у\s+вживанні\s+паронімів)?)?(?:\s*§\s*\d+\.?)?\.?|"
    r"\d+(?:\.\d+)+\.?\s*явище\s+паронімії(?:\s+в\s+українській\s+мові)?\.?|"
    r"(?:словнич[оа]к|короткий\s+словник)\s+паронімів\.?"
    r")\s*$",
    re.IGNORECASE,
)

_BARE_OR_NUMBERED_PARONYM_HEADER_RE = re.compile(
    r"^\s*(?:\d+\.\s*)?пароніми\.?\s*$",
    re.IGNORECASE,
)

# A line starting with a dash, opening parenthesis, colon/comma/semicolon, or lowercase
# Ukrainian word continues a prose/definition sentence rather than following a bare heading.
_DEFINITION_CONTINUATION_RE = re.compile(rf"^\s*(?:[{DASH_CHARS}\-:(,;]|[{UK_LOWER}])")


def _is_dedicated_paronym_heading(seg: str, next_seg: str = "") -> bool:
    """True only when ``seg`` starts with a standalone dedicated heading (not a wrapped definition)."""
    lines = [ln.strip() for ln in seg.splitlines() if ln.strip()]
    if not lines:
        return False
    if _EXPLICIT_PARONYM_SECTION_HEADER_RE.match(lines[0]):
        return True
    if not _BARE_OR_NUMBERED_PARONYM_HEADER_RE.match(lines[0]):
        return False
    next_line = ""
    if len(lines) > 1:
        next_line = lines[1]
    elif next_seg:
        next_lines = [ln.strip() for ln in next_seg.splitlines() if ln.strip()]
        if next_lines:
            next_line = next_lines[0]
    return not (next_line and _DEFINITION_CONTINUATION_RE.match(next_line))


def _has_active_paronym_cue(seg: str) -> bool:
    """True when a segment explicitly introduces or asks about paronyms (not a passing book/topic list)."""
    if not _PARONYM_CUE_RE.search(seg):
        return False
    stripped = _PASSING_MENTION_RE.sub("", seg)
    return bool(_PARONYM_CUE_RE.search(stripped))


def _split_paronym_segments(clean_text: str, doc: SourceDocument) -> list[tuple[int, int, str, bool]]:
    """Split document into offset-preserving segments tagged with active paronym context."""
    if _TOC_RE.search(clean_text):
        return []

    boundary_re = re.compile(
        r"(?=\n[ \t]*(?:§\s*\d+|(?-i:І{1,3}\s+[А-ЯІЇЄҐ])|Вправа\s+\d+|Зауважте!|Зверни\s+увагу!|"
        r"Культура\s+(?:слова|мовлення)|Рекомендована\s+література|Перевірте\s+себе|"
        r"Домашнє\s+завдання|Практикум\b|ПОРУШЕННЯ\s+ЛЕКСИЧНИХ|У\s+словнику\s+|"
        r"Антонімами\s+називають|Антоніми\s+|Синоніми\s+|Синонімічне\s+значення|"
        r"Омоніми\s+|Омонімічне\s+значення|ФУНКЦІОНАЛЬНІ\s+АСПЕКТИ|"
        r"Пароніми\.?\s*(?=\n|$)|Пароніми\.\s*Запобігання|(?:Словнич[оа]к|Короткий\s+словник)\s+паронімів\b|"
        r"Пароніми\s*\(|Пароніми\s*[—–−-]|Паронімічне\s+значення|\d+(?:\.\d+)+\.?\s*Явище\s+паронімії|"
        r"До\s+речі…|•\s*паронімів\s*:|"
        r"З['’ʼ]ясуйте\s+за\s+словником\s+значення\s+паронімів|"
        r"Складіть\s+висловлення\s*\(усно\),\s+обігравши\s+такі\s+пари|"
        r"(?-i:(?:Вправа|Завдання)\b|"
        r"(?:Перепишіть|Спишіть|Запишіть|Виберіть|Розкрийте|Вибираючи|Добираючи|Вибравши|Розкривши|"
        r"Прочитайте|Доберіть|Підберіть|Розподіліть|Утворіть|Випишіть|Знайдіть|Виконайте|"
        r"Відредагуйте|Замініть|Виправте)\b"
        r"[^\n]{0,120}(?:дуж|потрібне\s+слово|потрібні\s+слова|доцільне|антонім|синонім|омонім))|"
        r"[1-9]\d{0,2}\.\s+(?:Антонім|Синонім|Омонім|Паронім|"
        r"[А-ЯІЇЄҐ][а-яіїєґ']+(?:\s+[а-яіїєґ']+){0,3}\s+(?:антонім|синонім|омонім|паронім)|"
        r"Прочитайте|Перепишіть|Спишіть|Запишіть|Виберіть|"
        r"Розподіліть|Розкрийте|Утворіть|утворіть|Розгляньте|Виконайте|З['’ʼ]ясуйте|Витлумачте|"
        r"Складіть|З\s+кожним|Поєднайте|Знайдіть|Випишіть|Доберіть|Підберіть|Наведіть|Подайте|"
        r"Підготуйте|Поміркуйте|Відредагуйте|Чому\s+так|Я\s*—\s*редактор|Поясніть|Дослідіть|"
        r"Запам['’ʼ]ятайте|Провідміняйте|Розгадайте|Назвіть|Укажіть|Замініть|Виправте|"
        r"Поставте|Порівняйте|Визначте|Уведіть|Поділіть|Згрупуйте|Зіставте)))|"
        r"(?<=\.\s)(?=(?:Антонімами\s+називають|Синонімами\s+називають|Омонімами\s+називають|"
        r"Синонімічне\s+значення|Омонімічне\s+значення|Паронімічне\s+значення|"
        r"Іншим\s+різновидом\s+парадигматичних|"
        r"8[1-9]\.\s|23[5-9]\s|29[4-9]\.\s|Чи\s+є\s+слова\b|З['’ʼ]ясуйте\s+рід\s+паронімів\b|"
        r"Складіть\s+висловлення\s*\(усно\),\s+обігравши\s+такі\s+пари))|"
        rf"(?<=(?-i:[{UK_LOWER})»\"'’ʼ\]\.])[.!?]\s)(?=[ \t]*(?-i:(?:Перепишіть|Спишіть|Запишіть|Виберіть|Розкрийте|"
        r"Вибираючи|Добираючи|Вибравши|Розкривши)\b"
        r"[^\n.]{0,120}(?:дуж|потрібне\s+слово|потрібні\s+слова|доцільне)))|"
        r"(?<=[.!?][»\"'’ʼ)]\s)(?=[ \t]*(?-i:(?:Перепишіть|Спишіть|Запишіть|Виберіть|Розкрийте|"
        r"Вибираючи|Добираючи|Вибравши|Розкривши)\b"
        r"[^\n.]{0,120}(?:дуж|потрібне\s+слово|потрібні\s+слова|доцільне)))",
        re.IGNORECASE,
    )

    cut_points = [0, *(m.start() for m in boundary_re.finditer(clean_text)), len(clean_text)]
    raw_segments: list[tuple[int, int, str]] = []
    for a, b in pairwise(cut_points):
        chunk = clean_text[a:b]
        if not chunk.strip():
            continue
        ltrim = len(chunk) - len(chunk.lstrip())
        rtrim = len(chunk) - len(chunk.rstrip())
        s = a + ltrim
        e = b - rtrim
        raw_segments.append((s, e, clean_text[s:e]))

    tagged: list[tuple[int, int, str, bool]] = []
    # A MiyKlas page is dedicated to paronyms as a whole. A textbook chunk enters lesson mode
    # only at the segment that itself opens with a dedicated paronym heading (boundary_re
    # starts a segment at every such heading), never for text above that heading.
    in_paronym_lesson = doc.source_type == "miyklas"
    for idx, (seg_start, seg_end, seg) in enumerate(raw_segments):
        next_seg = raw_segments[idx + 1][2] if idx + 1 < len(raw_segments) else ""
        if _is_dedicated_paronym_heading(seg, next_seg) and _has_active_paronym_cue(seg):
            in_paronym_lesson = True
        if _MULTIPLE_CHOICE_RE.search(seg):
            tagged.append((seg_start, seg_end, seg, False))
            continue
        # Reject lowercase multiple-choice options "а) ... б) ... в)" UNLESS it's a
        # categorization exercise ("Розподіліть пароніми за значенням так: а) ... б) ...").
        if re.search(r"(?:^|\n)\s*а\)\s+.+\n\s*б\)\s+", seg, re.IGNORECASE) and not re.search(
            r"розподіліть\s+пароніми", seg, re.IGNORECASE
        ):
            tagged.append((seg_start, seg_end, seg, False))
            continue
        if _DISCLAIMER_RE.search(seg) and not re.search(r"пароніми[^.]{0,120}:", seg, re.IGNORECASE):
            tagged.append((seg_start, seg_end, seg, False))
            continue
        first_line = seg.splitlines()[0] if seg else ""
        # Check topic switches on the segment's header/instruction (not inside example sentences).
        prompt_head = re.split(r"\n(?=[1-9]\.\s)", seg, maxsplit=1)[0].strip()
        prompt_body = re.sub(r"^\d{1,3}\.\s+", "", prompt_head)
        prompt_first_sent = re.split(r"(?<=[.!?])\s+", prompt_body, maxsplit=1)[0]
        if _NON_PARONYM_SECTION_RE.search(first_line) and not _has_active_paronym_cue(first_line):
            in_paronym_lesson = False
            tagged.append((seg_start, seg_end, seg, False))
            continue
        if re.search(
            r"^(?:антонім|синонім|омонім|омограф|омофон)", first_line, re.IGNORECASE
        ) and not _has_active_paronym_cue(seg):
            in_paronym_lesson = False
            tagged.append((seg_start, seg_end, seg, False))
            continue
        if _OTHER_LEXICAL_TOPIC_RE.search(prompt_first_sent) and not _has_active_paronym_cue(seg):
            in_paronym_lesson = False
            tagged.append((seg_start, seg_end, seg, False))
            continue
        if re.search(
            r"(?:словником\s+синонімів|вжиті\s+в\s+реченнях\s+синоніми|доберіть\s+до\s+слів.*синоніми|"
            r"проілюструвавши\s+омонімію|випишіть\s+пари\s+спільнокореневих|"
            r"визначте\s+лексичне\s+значення\s+виділених|у\s+яких\s+є\s+антоніми|"
            r"знайдіть\s+у\s+тексті\s+синоніми|знайдіть\s+синоніми|випишіть\s+фразеологізми|"
            r"випишіть\s+усі\s+омоніми|проілюструйте\s+омонімію|"
            r"у\s+тексті\s+слова,\s+ужиті\s+в\s+переносному|"
            r"виберіть\s+із\s+дужок\s+потрібну\s+літеру|запишіть\s+сполуки\s+слів\s+у\s+дві\s+колонки|"
            r"приголосні\s+основи\s+\[)",
            seg,
            re.IGNORECASE,
        ):
            tagged.append((seg_start, seg_end, seg, False))
            continue

        has_local_cue = _has_active_paronym_cue(seg)
        # A prompt that also asks about another lexical relation ("Які слова є синонімами, а які
        # паронімами?") is a mixed classification exercise, not a paronym presentation.
        if has_local_cue and _OTHER_LEXICAL_TOPIC_RE.search(prompt_first_sent):
            has_local_cue = False
        # A choice exercise whose own prompt sends the learner to a paronym dictionary
        # ("Спишіть, добираючи з дужок потрібне слово. Скористайтеся словничком паронімів")
        # asks about paronyms; a bare prose mention of that dictionary does not.
        if (
            not has_local_cue
            and _CHOICE_EXERCISE_PROMPT_RE.search(prompt_head)
            and _PARONYM_DICTIONARY_REFERENCE_RE.search(prompt_head)
        ):
            has_local_cue = True
        # Activate ONE immediate choice exercise ONLY when the adjacent segment provides
        # explicit paronym-lesson evidence (never chaining from one generic choice exercise
        # to the next).
        active = has_local_cue or in_paronym_lesson
        if (
            not active
            and _CHOICE_EXERCISE_PROMPT_RE.search(prompt_first_sent)
            and not _OTHER_LEXICAL_TOPIC_RE.search(prompt_first_sent)
        ):
            prev_seg = raw_segments[idx - 1][2] if idx > 0 else ""
            prev_explicit_paronym_leadin = bool(
                idx > 0
                and tagged[-1][3]
                and re.search(
                    r"(?:сплутування\s+паронімів|"
                    r"(?:визначте|знайдіть|поясніть|розрізняйте|витлумачте)\s+[^\n.]{0,40}паронім)",
                    prev_seg,
                    re.IGNORECASE,
                )
            )
            if prev_explicit_paronym_leadin:
                active = True
        tagged.append((seg_start, seg_end, seg, active))
    return tagged


def _is_similar_enough_for_paronym(w1: str, w2: str) -> bool:
    """Guard against grammatical subject-predicate dashes inside prose explanations.

    Never invents pairs; rejects unrelated prose words across a dash.
    """
    a, b = normalize_token(w1), normalize_token(w2)
    if a == b:
        return False
    if len(a) < 3 or len(b) < 3:
        return False
    if max(len(a), len(b)) - min(len(a), len(b)) > 6:
        return False
    common_prefix = 0
    for ca, cb in zip(a, b, strict=False):
        if ca == cb:
            common_prefix += 1
        else:
            break
    common_suffix = 0
    for ca, cb in zip(reversed(a), reversed(b), strict=False):
        if ca == cb:
            common_suffix += 1
        else:
            break
    if common_prefix >= 2 or common_suffix >= 3:
        return True
    bigrams_a = {a[i : i + 2] for i in range(len(a) - 1)}
    bigrams_b = {b[i : i + 2] for i in range(len(b) - 1)}
    if bigrams_a and bigrams_b:
        overlap = len(bigrams_a & bigrams_b)
        if overlap / min(len(bigrams_a), len(bigrams_b)) >= 0.45:
            return True
    return False


def _mask_subclause_disclaimers(seg: str) -> str:
    """Mask disclaimer sentences with equal-length spaces so character offsets stay exact."""
    chars = list(seg)
    pos = 0
    for m in [*list(re.finditer(r"(?<=[.!?])\s+", seg)), None]:
        end = m.start() if m is not None else len(seg)
        sent = seg[pos:end]
        if _DISCLAIMER_RE.search(sent):
            for idx in range(pos, end):
                if chars[idx] != "\n":
                    chars[idx] = " "
        pos = m.end() if m is not None else len(seg)
    return "".join(chars)


def _sentence_spans(flat_text: str) -> list[tuple[int, int, str]]:
    """Split ``flat_text`` into sentences with exact ``(start, end, trimmed_text)`` spans."""
    spans: list[tuple[int, int, str]] = []
    pos = 0
    for m in [*list(re.finditer(r"(?<=[.!?])\s+", flat_text)), None]:
        end = m.start() if m is not None else len(flat_text)
        raw = flat_text[pos:end]
        if raw.strip():
            lpad = len(raw) - len(raw.lstrip())
            rpad = len(raw) - len(raw.rstrip())
            s = pos + lpad
            e = end - rpad
            spans.append((s, e, flat_text[s:e]))
        pos = m.end() if m is not None else len(flat_text)
    return spans


def _extract_from_segment(
    seg: str, seg_start: int, clean_to_raw: list[int], doc: SourceDocument
) -> list[RawPairAttestation]:
    out: list[RawPairAttestation] = []
    # Never extract from multiple-choice options A/B/V/G.
    if re.search(r"(?:^|\n)\s*[Аа]\s+\S+.*\n\s*[Бб]\s+\S+.*\n\s*[Вв]\s+\S+", seg):
        return out

    # Special case: 10-klas Avramenko s0131 bullet list — keep ONLY the "• паронімів:" bullet.
    base_offset = seg_start
    if re.search(r"•\s*паронімів\s*:", seg, re.IGNORECASE):
        m_b = re.search(r"(•\s*паронімів\s*:[^\n•]+)", seg, re.IGNORECASE)
        if m_b:
            base_offset = seg_start + m_b.start(1)
            seg = m_b.group(1)

    masked_seg = _mask_subclause_disclaimers(seg)
    if not masked_seg.strip():
        return out

    # Flat single-space view with exact offset map back into clean_text (and thus doc.text).
    flat_seg, flat_to_clean = _flatten_with_map(masked_seg, base_offset)

    def _quote_flat(f_start: int, f_end: int) -> str:
        return _raw_quote(doc.text, clean_to_raw, flat_to_clean[f_start], flat_to_clean[f_end])

    def _quote_seg(s_start: int, s_end: int) -> str:
        return _raw_quote(doc.text, clean_to_raw, base_offset + s_start, base_offset + s_end)

    rich_pairs: set[tuple[str, str]] = set()

    # 1. Parenthesized gloss pairs: "word1 (gloss1) — word2 (gloss2)"
    for m in _PAREN_GLOSS_PAIR_RE.finditer(flat_seg):
        w1, w2 = m.group(1), m.group(3)
        if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
            continue
        if not _is_similar_enough_for_paronym(w1, w2):
            continue
        members = [
            MemberNote(word=normalize_token(w1), attested_form=w1),
            MemberNote(word=normalize_token(w2), attested_form=w2),
        ]
        atts = _emit_group_pairs(
            members, doc, pattern="parenthesized_gloss_pair", quoted_line=_quote_flat(m.start(), m.end())
        )
        for att in atts:
            rich_pairs.add((att.member_a.word, att.member_b.word))
        out.extend(atts)

    # 2. Inline definition pairs: "word1 — def1 і/а word2 — def2"
    for m in _INLINE_DEF_PAIR_RE.finditer(flat_seg):
        w1, w2 = m.group(1), m.group(3)
        if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
            continue
        if not _is_similar_enough_for_paronym(w1, w2):
            continue
        pair_key = tuple(sorted((normalize_token(w1), normalize_token(w2))))
        if pair_key in rich_pairs:
            continue
        members = [
            MemberNote(word=normalize_token(w1), attested_form=w1),
            MemberNote(word=normalize_token(w2), attested_form=w2),
        ]
        atts = _emit_group_pairs(
            members, doc, pattern="inline_definition_pair", quoted_line=_quote_flat(m.start(), m.end())
        )
        for att in atts:
            rich_pairs.add((att.member_a.word, att.member_b.word))
        out.extend(atts)

    # 3. Stacked gloss pairs (5-klas Zabolotnyi s0027: "1) вистава – виставка\n(спектакль) (показ...)")
    for m in re.finditer(
        rf"\d\)\s*({WORD_CORE})\s*[{DASH_CHARS}]\s*({WORD_CORE})\s*\n\s*\(([^)]+)\)\s*\(([^)]+)\)",
        masked_seg,
    ):
        w1, w2 = m.group(1), m.group(2)
        if _is_valid_single_word(w1) and _is_valid_single_word(w2) and _is_similar_enough_for_paronym(w1, w2):
            members = [
                MemberNote(word=normalize_token(w1), attested_form=w1),
                MemberNote(word=normalize_token(w2), attested_form=w2),
            ]
            atts = _emit_group_pairs(
                members, doc, pattern="parenthesized_gloss_pair", quoted_line=_quote_seg(m.start(), m.end())
            )
            for att in atts:
                rich_pairs.add((att.member_a.word, att.member_b.word))
            out.extend(atts)

    # 4. Dash-separated paronym chains: "word1 — word2 [— word3]"
    # Run over flat sentences with offset map so PDF line-wrapped pairs like "уява —\nуявлення"
    # and "заїхати —\nвід'їхати" are parsed intact while quoted_line stays verbatim from doc.text.
    sent_spans = _sentence_spans(flat_seg)
    for s_start, s_end, chunk in sent_spans:
        if not chunk or _DISCLAIMER_RE.search(chunk):
            continue
        # Skip poetry/pun quotes with attribution like "(Л. Костенко)" or "(Нар. тв.)".
        if re.search(
            r"\([А-ЯІЇЄҐ]\.\s*[А-ЯІЇЄҐ][а-яіїєґ]+|Нар\.\s*тв|Ліна\s+Костенко|Тарапуньки",
            chunk,
        ):
            continue
        sent_quote = _quote_flat(s_start, s_end)
        for m in re.finditer(
            rf"(?<![{UK_LETTER}])({WORD_CORE}(?:{DASH_SEP}{WORD_CORE}){{1,2}})(?![{UK_LETTER}])",
            chunk,
        ):
            chain_text = m.group(1)
            raw_tokens = [t.strip() for t in re.split(rf"[{DASH_CHARS}]", chain_text) if t.strip()]
            if not (2 <= len(raw_tokens) <= 3):
                continue
            if not all(_is_valid_single_word(t) for t in raw_tokens):
                continue
            # Never match lowercase word followed by Capitalized word (prose proper noun, e.g.
            # "картин — Катериною").
            if raw_tokens[0][0].islower() and any(t[0].isupper() for t in raw_tokens[1:]):
                continue
            if not all(
                _is_similar_enough_for_paronym(raw_tokens[k], raw_tokens[k + 1]) for k in range(len(raw_tokens) - 1)
            ):
                continue
            after = chunk[m.end() :].lstrip()
            if (
                after
                and after[0] not in ",;.)]:»\"'"
                and not re.match(r"^(?:та\s+ін|тощо|і\s+т\.)", after, re.IGNORECASE)
            ):
                continue
            before = chunk[: m.start()].rstrip()
            if re.search(r"(?:від\s+гр\.|грец\.|лат\.|рос\.|нім\.)$", before, re.IGNORECASE):
                continue
            members = [MemberNote(word=normalize_token(t), attested_form=t) for t in raw_tokens]
            for att in _emit_group_pairs(members, doc, pattern="dash_pair_list", quoted_line=sent_quote):
                if (att.member_a.word, att.member_b.word) not in rich_pairs:
                    out.append(att)

    # 5a. Double-slash pair lists: "Людяний // людний"
    for m in _DOUBLE_SLASH_CHAIN_RE.finditer(flat_seg):
        raw_tokens = [t.strip() for t in m.group(0).split("//") if t.strip()]
        if not (2 <= len(raw_tokens) <= 3):
            continue
        if not all(_is_valid_single_word(t) for t in raw_tokens):
            continue
        if not all(
            _is_similar_enough_for_paronym(raw_tokens[k], raw_tokens[k + 1]) for k in range(len(raw_tokens) - 1)
        ):
            continue
        members = [MemberNote(word=normalize_token(t), attested_form=t) for t in raw_tokens]
        for att in _emit_group_pairs(
            members, doc, pattern="slash_pair_list", quoted_line=_quote_flat(m.start(), m.end())
        ):
            if (att.member_a.word, att.member_b.word) not in rich_pairs:
                out.append(att)

    # 5b. Single-slash collocation headers: "Особистий / особовий: власність, господарство..."
    for m in _COLON_SLASH_CHAIN_RE.finditer(flat_seg):
        w1, w2 = m.group(1), m.group(2)
        if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
            continue
        if not _is_similar_enough_for_paronym(w1, w2):
            continue
        members = [
            MemberNote(word=normalize_token(w1), attested_form=w1),
            MemberNote(word=normalize_token(w2), attested_form=w2),
        ]
        for att in _emit_group_pairs(
            members,
            doc,
            pattern="slash_pair_list",
            quoted_line=_quote_flat(m.start(), m.end()),
        ):
            if (att.member_a.word, att.member_b.word) not in rich_pairs:
                out.append(att)

    # 6. Explicit conjunction pairs ("пароніми X та Y", "вживаємо слово X, а коли — Y")
    for regex in (_CONJ_PAIR_RE, _WHEN_USE_PAIR_RE):
        for m in regex.finditer(flat_seg):
            groups = [g for g in m.groups() if g is not None]
            if len(groups) != 2:
                continue
            w1, w2 = groups
            if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
                continue
            if not _is_similar_enough_for_paronym(w1, w2):
                continue
            members = [
                MemberNote(word=normalize_token(w1), attested_form=w1),
                MemberNote(word=normalize_token(w2), attested_form=w2),
            ]
            for att in _emit_group_pairs(
                members, doc, pattern="conjunction_pair", quoted_line=_quote_flat(m.start(), m.end())
            ):
                if (att.member_a.word, att.member_b.word) not in rich_pairs:
                    out.append(att)

    for m in _COLON_CONJ_LIST_RE.finditer(flat_seg):
        list_body = m.group(1)
        list_quote = _quote_flat(m.start(), m.end())
        for item in re.split(r"\s*[,;]\s*", list_body):
            mc = re.fullmatch(rf"({WORD_CORE})\s+(?:і|та|й)\s+({WORD_CORE})", item.strip())
            if not mc:
                continue
            w1, w2 = mc.group(1), mc.group(2)
            if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
                continue
            if not _is_similar_enough_for_paronym(w1, w2):
                continue
            members = [
                MemberNote(word=normalize_token(w1), attested_form=w1),
                MemberNote(word=normalize_token(w2), attested_form=w2),
            ]
            for att in _emit_group_pairs(members, doc, pattern="conjunction_pair", quoted_line=list_quote):
                if (att.member_a.word, att.member_b.word) not in rich_pairs:
                    out.append(att)

    # 7. Semicolon-delimited comma groups in explicit paronym exercises
    if ";" in flat_seg and re.search(
        r"(?:паронім|утворіть\s+словосполучення|складіть\s+речення|поясніть\s+різницю)",
        flat_seg,
        re.IGNORECASE,
    ):
        for s_start, _, sent in sent_spans:
            if ";" not in sent:
                continue
            part_spans: list[tuple[int, int, str]] = []
            p_pos = 0
            for pm in [*list(re.finditer(r";", sent)), None]:
                p_end = pm.start() if pm is not None else len(sent)
                raw_part = sent[p_pos:p_end]
                stripped = raw_part.strip(" .")
                if stripped:
                    lpad = raw_part.find(stripped)
                    ps = s_start + p_pos + lpad
                    pe = ps + len(stripped)
                    part_spans.append((ps, pe, stripped))
                p_pos = pm.end() if pm is not None else len(sent)
            if len(part_spans) < 2:
                continue
            for ps, pe, part in part_spans:
                mi = _SEMICOLON_COMMA_ITEM_RE.match(part)
                if not mi:
                    continue
                raw_words = [w.strip() for w in mi.group(1).split(",") if w.strip()]
                if not (2 <= len(raw_words) <= 3):
                    continue
                if not all(_is_valid_single_word(w) for w in raw_words):
                    continue
                if not all(
                    _is_similar_enough_for_paronym(raw_words[k], raw_words[k + 1]) for k in range(len(raw_words) - 1)
                ):
                    continue
                members = [MemberNote(word=normalize_token(w), attested_form=w) for w in raw_words]
                for att in _emit_group_pairs(
                    members,
                    doc,
                    pattern="semicolon_comma_group",
                    quoted_line=_quote_flat(ps, pe),
                ):
                    if (att.member_a.word, att.member_b.word) not in rich_pairs:
                        out.append(att)

    # 7b. Explicit "із такими трьома паронімами: водний, водяний, водянистий"
    for m in re.finditer(rf"паронімами\s*:\s*({WORD_CORE}(?:\s*,\s*{WORD_CORE}){{1,3}})", flat_seg, re.IGNORECASE):
        raw_words = [w.strip() for w in m.group(1).split(",") if w.strip()]
        if (
            2 <= len(raw_words) <= 4
            and all(_is_valid_single_word(w) for w in raw_words)
            and all(_is_similar_enough_for_paronym(raw_words[k], raw_words[k + 1]) for k in range(len(raw_words) - 1))
        ):
            members = [MemberNote(word=normalize_token(w), attested_form=w) for w in raw_words]
            out.extend(
                _emit_group_pairs(
                    members,
                    doc,
                    pattern="semicolon_comma_group",
                    quoted_line=_quote_flat(m.start(), m.end()),
                )
            )

    # 8. Choice-in-parentheses exercises inside paronym lessons: "(плутає, путає)"
    if _CHOICE_EXERCISE_PROMPT_RE.search(flat_seg):
        for s_start, s_end, sent in sent_spans:
            sent_quote = _quote_flat(s_start, s_end)
            for m in _CHOICE_PAIR_RE.finditer(sent):
                w1, w2 = m.group(1), m.group(2)
                if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
                    continue
                if not _is_similar_enough_for_paronym(w1, w2):
                    continue
                members = [
                    MemberNote(word=normalize_token(w1), attested_form=w1),
                    MemberNote(word=normalize_token(w2), attested_form=w2),
                ]
                for att in _emit_group_pairs(members, doc, pattern="exercise_choice_pair", quoted_line=sent_quote):
                    if (att.member_a.word, att.member_b.word) not in rich_pairs:
                        out.append(att)

    # 9. Question pairs in paronym intro ("Адрес? Адреса?", "Шкіряний? Шкірний?")
    for m in _QUESTION_PAIR_RE.finditer(masked_seg):
        w1, w2 = m.group(1), m.group(2)
        if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
            continue
        if not _is_similar_enough_for_paronym(w1, w2):
            continue
        members = [
            MemberNote(word=normalize_token(w1), attested_form=w1),
            MemberNote(word=normalize_token(w2), attested_form=w2),
        ]
        for att in _emit_group_pairs(members, doc, pattern="question_pair", quoted_line=_quote_seg(m.start(), m.end())):
            if (att.member_a.word, att.member_b.word) not in rich_pairs:
                out.append(att)

    return out


def _mask_spans(text: str, spans: list[tuple[int, int]]) -> str:
    """Blank ``spans`` of ``text`` with spaces, keeping newlines, so offsets stay 1-to-1."""
    chars = list(text)
    for start, end in spans:
        for idx in range(start, end):
            if chars[idx] != "\n":
                chars[idx] = " "
    return "".join(chars)


def extract_from_document(doc: SourceDocument) -> list[RawPairAttestation]:
    """Deterministically extract all explicit paronym pair attestations from one SourceDocument."""
    clean_text, clean_to_raw = _clean_text_with_map(doc.text)
    if not clean_text.strip():
        return []

    if _SLASH_DICT_HEADING_RE.search(clean_text):
        return _extract_slash_dictionary(clean_text, clean_to_raw, doc)
    if _MIYKLAS_DICT_HEADING_RE.search(clean_text):
        return _extract_miyklas_dictionary(clean_text, clean_to_raw, doc)

    # Summary-table lexical-group overview (7-klas Avramenko s0242/s0243): the table is not a
    # paronym lesson, so take ONLY its explicit Пароніми example row ("рятувальник — ...;
    # рятівник — ..."). Text after the table is read only from a dedicated paronym heading on.
    attestations: list[RawPairAttestation] = []
    lesson_start = 0
    if re.search(r"ГРУПИ\s+ЛЕКСИКИ", clean_text, re.IGNORECASE) and re.search(
        r"рятувальник\s*[—–-]", clean_text, re.IGNORECASE
    ):
        m_row = re.search(
            r"(рятувальник\s*[—–-][^;]+;\s*рятівник\s*[—–-][^\n]+)",
            clean_text,
            re.IGNORECASE | re.DOTALL,
        )
        table_end = 0
        if m_row:
            table_end = m_row.end(1)
            clean_row = _clean_note_text(m_row.group(1))
            raw_row = _raw_quote(doc.text, clean_to_raw, m_row.start(1), m_row.end(1))
            members = []
            for part in clean_row.split(";"):
                md = re.match(rf"^\s*({WORD_CORE})\s*[{DASH_CHARS}]\s*(.+)$", part.strip())
                if md:
                    members.append(MemberNote(word=normalize_token(md.group(1)), attested_form=md.group(1)))
            attestations.extend(_emit_group_pairs(members, doc, pattern="inline_definition_pair", quoted_line=raw_row))
        heading_start = next(
            (
                ls
                for ls, _, ln in _line_spans(clean_text)
                # The table's own bare "Пароніми" label is not a lesson heading, so only an
                # explicit section heading (e.g. "§ 9. Пароніми") counts, even when the row
                # did not parse and table_end is unknown.
                if ls >= table_end and _EXPLICIT_PARONYM_SECTION_HEADER_RE.match(ln)
            ),
            None,
        )
        if heading_start is None:
            return attestations
        lesson_start = heading_start

    box_atts, consumed_spans = _extract_named_definition_boxes(
        _mask_spans(clean_text, [(0, lesson_start)]), clean_to_raw, doc
    )
    attestations.extend(box_atts)

    # Mask consumed spans with spaces (preserving newlines) so character offsets stay 1-to-1.
    residual_text = _mask_spans(clean_text, [(0, lesson_start), *consumed_spans])

    for seg_start, _, seg, active in _split_paronym_segments(residual_text, doc):
        if active:
            attestations.extend(_extract_from_segment(seg, seg_start, clean_to_raw, doc))

    deduped: list[RawPairAttestation] = []
    seen: set[tuple[str, str, str, str]] = set()
    for att in attestations:
        key = (att.member_a.word, att.member_b.word, att.pattern, att.quoted_line)
        if key not in seen:
            seen.add(key)
            deduped.append(att)
    return deduped
