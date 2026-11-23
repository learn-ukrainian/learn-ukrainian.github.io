"""Deterministic, source-grounded Ukrainian paronym extractor.

Extracts ONLY explicit paronym presentations (dictionary entries, dash/slash
pairs, explicit paronym exercises) from plain text documents (textbook chunks
and MiyKlas pages). Every output pair carries the exact source locator and
verbatim quoted excerpt; nothing is inferred from model knowledge.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from itertools import combinations

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

# Explicit non-paronym disclaimers (e.g. narrow-definition exclusions, non-existent words).
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
    meaning: str | None = None
    example: str | None = None


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
    shared_context: str | None = None
    source_url: str = ""


def normalize_token(raw: str) -> str:
    """Normalize a Ukrainian token for canonical matching (NFC, unstressed, ASCII apostrophe)."""
    text = unicodedata.normalize("NFC", raw)
    text = _PDF_PUA_STRESS_RE.sub("", text)
    text = _INLINE_DIGIT_STRESS_RE.sub("", text)
    text = text.replace("’", "'").replace("ʼ", "'").replace("`", "'")
    return " ".join(text.strip().lower().split())


def _clean_text_for_parsing(raw_text: str) -> str:
    """Clean PDF/HTML artifacts while keeping line structure for parsing."""
    text = unicodedata.normalize("NFC", raw_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = _PDF_PUA_STRESS_RE.sub("", text)
    text = _INLINE_DIGIT_STRESS_RE.sub("", text)
    # Rejoin PDF soft line-wrap hyphenations (e.g. "іммігра-\nція" -> "імміграція").
    text = _LINE_WRAP_HYPHEN_RE.sub(r"\1\2", text)
    return text


def _clean_quote(snippet: str) -> str:
    """Collapse internal newlines/extra spaces for a compact verbatim quote."""
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


def _split_meaning_and_example(definition: str) -> tuple[str | None, str | None]:
    """Split a source's short meaning from an optional trailing parenthesized or colon example."""
    body = _clean_quote(definition).strip(" .;")
    if not body:
        return None, None

    # Pattern 1: trailing parenthesized example "(авторитарний уряд)" at end of gloss.
    m_paren = re.search(r"^(.*?)\s*\(([^()]{3,160})\)\s*\.?$", body)
    if m_paren:
        gloss = m_paren.group(1).strip(" .;:")
        ex = m_paren.group(2).strip(" .;")
        if gloss and not ex.lower().startswith(("від ", "грец", "лат", "франц", "англ", "італ", "нім")):
            return gloss, ex

    # Pattern 2: meaning followed by ": example" (e.g. "сільський багатир", "серцевий м'яз").
    if ":" in body:
        left, right = body.split(":", 1)
        left = left.strip(" .;")
        right = right.strip(" .;")
        if left and right and len(left) >= 6:
            return left, right

    # Pattern 3: sentence meaning followed by example sentence(s) (e.g. Zabolotnyi dictionary).
    m_sent = re.match(rf"^([^.]{{6,200}})\.\s+([{UK_UPPER}].+)$", body)
    if m_sent:
        return m_sent.group(1).strip(), m_sent.group(2).strip()

    return body, None


def _emit_group_pairs(
    members: list[MemberNote],
    doc: SourceDocument,
    *,
    pattern: str,
    quoted_line: str,
    shared_context: str | None = None,
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
    quote = _clean_quote(quoted_line)
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
                quoted_line=quote,
                shared_context=_clean_quote(shared_context) if shared_context else None,
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


def _extract_slash_dictionary(clean_text: str, doc: SourceDocument) -> list[RawPairAttestation]:
    if not re.search(r"словнич[оа]к\s+паронімів", clean_text, re.IGNORECASE):
        return []
    lines = [ln.strip() for ln in clean_text.splitlines()]
    out: list[RawPairAttestation] = []
    i = 0
    while i < len(lines):
        m_hdr = _SLASH_DICT_HEADER_RE.match(lines[i])
        if not m_hdr:
            i += 1
            continue
        raw_headwords = [h.strip() for h in m_hdr.group(1).split("//")]
        norm_targets = {normalize_token(h): h for h in raw_headwords if _is_valid_headword(h)}
        if len(norm_targets) < 2:
            i += 1
            continue
        start_i = i
        i += 1
        entries: dict[str, str] = {}
        current_key: str | None = None
        while i < len(lines):
            ln = lines[i]
            if not ln or _SLASH_DICT_HEADER_RE.match(ln) or re.fullmatch(r"\d{1,3}", ln):
                break
            m_def = _DEF_LINE_RE.match(ln)
            if m_def and normalize_token(m_def.group(1)) in norm_targets:
                current_key = normalize_token(m_def.group(1))
                entries[current_key] = m_def.group(2).strip()
            elif current_key is not None:
                entries[current_key] = f"{entries[current_key]} {ln}".strip()
            i += 1
        block_quote = " ".join(ln for ln in lines[start_i:i] if ln)
        members: list[MemberNote] = []
        for norm_w, raw_w in norm_targets.items():
            meaning, example = _split_meaning_and_example(entries.get(norm_w, ""))
            members.append(
                MemberNote(word=norm_w, attested_form=raw_w, meaning=meaning, example=example)
            )
        out.extend(
            _emit_group_pairs(members, doc, pattern="slash_dictionary", quoted_line=block_quote)
        )
    return out


# ── Pattern 1b: Blank-line-grouped MiyKlas dictionary ("Короткий словник паронімів") ──

def _extract_miyklas_dictionary(clean_text: str, doc: SourceDocument) -> list[RawPairAttestation]:
    if not re.search(r"короткий\s+словник\s+паронімів", clean_text, re.IGNORECASE):
        return []
    out: list[RawPairAttestation] = []
    blocks = re.split(r"\n\s*\n", clean_text)
    for block in blocks:
        if re.match(r"^\s*Джерела\s*:", block, re.IGNORECASE):
            break
        raw_lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        # Also split lines where two consecutive entries share one HTML div without <br/>.
        expanded_lines: list[str] = []
        for ln in raw_lines:
            expanded_lines.extend(
                part.strip() for part in _INLINE_DICT_SPLIT_RE.split(ln) if part.strip()
            )
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
            meaning, example = _split_meaning_and_example(m.group(2))
            members.append(
                MemberNote(
                    word=normalize_token(raw_hw),
                    attested_form=raw_hw,
                    meaning=meaning,
                    example=example,
                )
            )
        if 2 <= len(members) <= 4:
            out.extend(
                _emit_group_pairs(
                    members,
                    doc,
                    pattern="dictionary_block",
                    quoted_line=" ".join(expanded_lines),
                )
            )
    return out


# ── Pattern 1c: Named inline dictionary boxes in textbooks ──

_NAMED_DEF_BOX_TRIGGERS = (
    re.compile(r"запам['’ʼ]ятайте\s+значення\s+паронімів\s*\.", re.IGNORECASE),
    re.compile(r"розрізняйте\s+пароніми\b[^\n.]*\.", re.IGNORECASE),
    re.compile(r"в\s+українській\s+мові\s+маємо\s+пароніми\b[^\n.]*\.", re.IGNORECASE),
    re.compile(
        rf"({WORD_CORE})\s+[іійта]+\s+({WORD_CORE})\s*[{DASH_CHARS}]\s*пароніми[^\n.]*\.",
        re.IGNORECASE,
    ),
    re.compile(r"має\s+словник\s+паронімів\s*:", re.IGNORECASE),
)

_BOX_STOP_RE = re.compile(
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
    clean_text: str, doc: SourceDocument
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
            flat = _clean_quote(segment_body)
            entries = list(_INLINE_HEADWORD_DEF_RE.finditer(flat))
            members: list[MemberNote] = []
            for em in entries:
                raw_hw = em.group(1).strip()
                if not _is_valid_single_word(raw_hw):
                    continue
                meaning, example = _split_meaning_and_example(em.group(2))
                members.append(
                    MemberNote(
                        word=normalize_token(raw_hw),
                        attested_form=raw_hw,
                        meaning=meaning,
                        example=example,
                    )
                )
            if 2 <= len(members) <= 4:
                span_end = tail_start + (stop_m.start() if stop_m else len(tail))
                full_quote = clean_text[m.start() : span_end]
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
        lines = [ln.strip() for ln in clean_text.splitlines()]
        for idx in range(len(lines) - 1):
            m1 = _DEF_LINE_RE.match(lines[idx])
            m2 = _DEF_LINE_RE.match(lines[idx + 1])
            if not (m1 and m2):
                continue
            w1, w2 = m1.group(1).strip(), m2.group(1).strip()
            if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
                continue
            n1, n2 = normalize_token(w1), normalize_token(w2)
            if n1 == n2 or not _is_similar_enough_for_paronym(w1, w2):
                continue
            context_above = "\n".join(lines[max(0, idx - 5) : idx])
            if not (
                re.search(rf"\b{re.escape(n1)}\b.*\b{re.escape(n2)}\b", context_above, re.IGNORECASE)
                or re.search(rf"\b{re.escape(n2)}\b.*\b{re.escape(n1)}\b", context_above, re.IGNORECASE)
                or re.search(r"паронім|відрізняються\s+слова", context_above, re.IGNORECASE)
            ):
                continue
            if _NON_PARONYM_SECTION_RE.search(context_above):
                continue
            g1, g2 = m1.group(2).strip(), m2.group(2).strip()
            if len(g1.split()) < 2 or len(g2.split()) < 2:
                continue
            raw_pair_line = f"{lines[idx]} {lines[idx + 1]}"
            if any(raw_pair_line[:25] in clean_text[s:e] for s, e in consumed):
                continue
            meaning1, ex1 = _split_meaning_and_example(g1)
            meaning2, ex2 = _split_meaning_and_example(g2)
            members = [
                MemberNote(word=n1, attested_form=w1, meaning=meaning1, example=ex1),
                MemberNote(word=n2, attested_form=w2, meaning=meaning2, example=ex2),
            ]
            out.extend(
                _emit_group_pairs(
                    members,
                    doc,
                    pattern="dictionary_block",
                    quoted_line=raw_pair_line,
                )
            )
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
_COLON_SLASH_CHAIN_RE = re.compile(
    rf"(?<![{UK_LETTER}])({WORD_CORE})\s*/\s*({WORD_CORE})\s*:\s*([^.\n]{{4,180}})"
)

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

_SEMICOLON_COMMA_ITEM_RE = re.compile(
    rf"^\s*({WORD_CORE}(?:\s*,\s*{WORD_CORE}){{1,2}})(?:\s*\(([^()]{{3,80}})\))?\s*$"
)

_CHOICE_EXERCISE_PROMPT_RE = re.compile(
    r"(?:вибираючи|добираючи|вибравши|виберіть|розкривши\s+дужки)[^.\n]{0,120}"
    r"(?:дуж|потрібне\s+слово|потрібні\s+слова|доцільне)",
    re.IGNORECASE,
)
_CHOICE_PAIR_RE = re.compile(rf"\(\s*({WORD_CORE})\s*,\s*({WORD_CORE})\s*\)")

_QUESTION_PAIR_RE = re.compile(
    rf"(?:^|\n)\s*({WORD_CORE})\?\s*\n?\s*({WORD_CORE})\?(?=\s*(?:\n|$))"
)


def _has_dedicated_paronym_heading(clean_text: str, doc: SourceDocument) -> bool:
    """True only when the document/page itself is dedicated to paronyms (not mixed homonyms/synonyms)."""
    if doc.source_type == "miyklas":
        return True
    first_lines = "\n".join(clean_text.splitlines()[:4])
    if _PASSING_MENTION_RE.search(first_lines):
        return False
    return bool(
        re.search(
            r"(?:^|\n)\s*(?:§\s*\d+\.?\s*пароніми\b|\d+\.\s*пароніми\b|пароніми\s*$|пароніми\.\s*запобігання|"
            r"3\.5\.\s*явище\s+паронімії|словничок\s+паронімів|короткий\s+словник\s+паронімів)",
            first_lines,
            re.IGNORECASE,
        )
    )


def _has_active_paronym_cue(seg: str) -> bool:
    """True when a segment explicitly introduces or asks about paronyms (not a passing book/topic list)."""
    if not _PARONYM_CUE_RE.search(seg):
        return False
    # Check if every occurrence of "паронім" in this segment is just a passing mention.
    stripped = _PASSING_MENTION_RE.sub("", seg)
    return bool(_PARONYM_CUE_RE.search(stripped))


def _split_paronym_segments(clean_text: str, doc: SourceDocument) -> list[tuple[str, bool]]:
    """Split document into segments tagged with whether they are active paronym contexts."""
    if _TOC_RE.search(clean_text):
        return []

    has_doc_paronym_heading = _has_dedicated_paronym_heading(clean_text, doc)

    boundary_re = re.compile(
        r"(?=\n(?:§\s*\d+|І{1,3}\s+[А-ЯІЇЄҐ]|Вправа\s+\d+|Зауважте!|Зверни\s+увагу!|"
        r"Культура\s+(?:слова|мовлення)|Рекомендована\s+література|Перевірте\s+себе|"
        r"Домашнє\s+завдання|Практикум\b|ПОРУШЕННЯ\s+ЛЕКСИЧНИХ|У\s+словнику\s+|"
        r"Антонімами\s+називають|Синоніми\s+|Синонімічне\s+значення|"
        r"Омоніми\s+|Омонімічне\s+значення|ФУНКЦІОНАЛЬНІ\s+АСПЕКТИ|"
        r"Пароніми\s*\(|Пароніми\s*[—–−-]|Паронімічне\s+значення|3\.5\.\s*Явище\s+паронімії|"
        r"До\s+речі…|•\s*паронімів\s*:|"
        r"З['’ʼ]ясуйте\s+за\s+словником\s+значення\s+паронімів|"
        r"Складіть\s+висловлення\s*\(усно\),\s+обігравши\s+такі\s+пари|"
        r"(?:[2-9]|[1-9]\d{1,2})\.\s+(?:Прочитайте|Перепишіть|Спишіть|Запишіть|Виберіть|"
        r"Розподіліть|Розкрийте|Утворіть|утворіть|Розгляньте|Виконайте|З['’ʼ]ясуйте|Витлумачте|"
        r"Складіть|З\s+кожним|Поєднайте|Знайдіть|Випишіть|Доберіть|Підготуйте|Поміркуйте|"
        r"Відредагуйте|Чому\s+так|Я\s*—\s*редактор|Поясніть|Дослідіть|Запам['’ʼ]ятайте)))|"
        r"(?<=\.\s)(?=(?:Антонімами\s+називають|Синонімами\s+називають|Омонімами\s+називають|"
        r"Синонімічне\s+значення|Омонімічне\s+значення|Паронімічне\s+значення|"
        r"Іншим\s+різновидом\s+парадигматичних|"
        r"8[1-9]\.\s|23[5-9]\s|29[4-9]\.\s|Чи\s+є\s+слова\b|З['’ʼ]ясуйте\s+рід\s+паронімів\b|"
        r"Складіть\s+висловлення\s*\(усно\),\s+обігравши\s+такі\s+пари))"
    )
    raw_segments = [s.strip() for s in boundary_re.split(clean_text) if s.strip()]

    tagged: list[tuple[str, bool]] = []
    in_paronym_lesson = has_doc_paronym_heading
    for idx, seg in enumerate(raw_segments):
        if _MULTIPLE_CHOICE_RE.search(seg):
            tagged.append((seg, False))
            continue
        # Reject lowercase multiple-choice options "а) ... б) ... в)" UNLESS it's a
        # categorization exercise ("Розподіліть пароніми за значенням так: а) ... б) ...").
        if re.search(r"(?:^|\n)\s*а\)\s+.+\n\s*б\)\s+", seg, re.IGNORECASE) and not re.search(
            r"розподіліть\s+пароніми", seg, re.IGNORECASE
        ):
            tagged.append((seg, False))
            continue
        if _DISCLAIMER_RE.search(seg) and not re.search(
            r"пароніми[^.]{0,120}:", seg, re.IGNORECASE
        ):
            tagged.append((seg, False))
            continue
        first_line = seg.splitlines()[0] if seg else ""
        if _NON_PARONYM_SECTION_RE.search(first_line) and not _has_active_paronym_cue(first_line):
            in_paronym_lesson = False
            tagged.append((seg, False))
            continue
        if (
            re.search(r"^(?:антонім|синонім|омонім|омограф|омофон)", first_line, re.IGNORECASE)
            and not _has_active_paronym_cue(seg)
        ):
            in_paronym_lesson = False
            tagged.append((seg, False))
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
            tagged.append((seg, False))
            continue

        has_local_cue = _has_active_paronym_cue(seg)
        if re.search(r"мають\s+різні\s+лексичні\s+значення\s*:", seg, re.IGNORECASE):
            has_local_cue = True
        # Lead-in exercise immediately before "Пароніми (від гр. ...)" (e.g. 11-klas Glazova 294).
        if (
            not has_local_cue
            and idx + 1 < len(raw_segments)
            and re.match(r"^Пароніми\s*\(", raw_segments[idx + 1], re.IGNORECASE)
            and re.search(r"словосполучення|лексичне\s+значення", seg, re.IGNORECASE)
        ):
            has_local_cue = True
        # Exercises explicitly continuing paronyms after an editing block.
        if re.match(r"^297\.\s", seg) or re.match(
            r"^Складіть\s+висловлення\s*\(усно\),\s+обігравши\s+такі\s+пари", seg, re.IGNORECASE
        ):
            has_local_cue = True
        if has_local_cue:
            in_paronym_lesson = True
        active = has_local_cue or in_paronym_lesson
        tagged.append((seg, active))
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


def _strip_subclause_disclaimers(seg: str) -> str:
    """Remove disclaimer sentences inside an otherwise valid paronym paragraph."""
    sentences = re.split(r"(?<=[.!?])\s+", seg)
    kept = [s for s in sentences if not _DISCLAIMER_RE.search(s)]
    return " ".join(kept)


def _extract_from_segment(seg: str, doc: SourceDocument) -> list[RawPairAttestation]:
    out: list[RawPairAttestation] = []
    # Never extract from multiple-choice options A/B/V/G.
    if re.search(r"(?:^|\n)\s*[Аа]\s+\S+.*\n\s*[Бб]\s+\S+.*\n\s*[Вв]\s+\S+", seg):
        return out

    # Special case: 10-klas Avramenko s0131 bullet list — keep ONLY the "• паронімів:" bullet.
    if re.search(r"•\s*паронімів\s*:", seg, re.IGNORECASE):
        m_b = re.search(r"(•\s*паронімів\s*:[^\n•]+)", seg, re.IGNORECASE)
        if m_b:
            seg = m_b.group(1)

    clean_seg = _strip_subclause_disclaimers(seg)
    if not clean_seg.strip():
        return out

    # Flat single-space view for patterns that can wrap across PDF line breaks.
    flat_seg = _clean_quote(clean_seg)

    rich_pairs: set[tuple[str, str]] = set()

    # 1. Parenthesized gloss pairs: "word1 (gloss1) — word2 (gloss2)"
    for m in _PAREN_GLOSS_PAIR_RE.finditer(flat_seg):
        w1, g1, w2, g2 = m.group(1), m.group(2), m.group(3), m.group(4)
        if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
            continue
        if not _is_similar_enough_for_paronym(w1, w2):
            continue
        m1, e1 = _split_meaning_and_example(g1)
        m2, e2 = _split_meaning_and_example(g2)
        members = [
            MemberNote(word=normalize_token(w1), attested_form=w1, meaning=m1, example=e1),
            MemberNote(word=normalize_token(w2), attested_form=w2, meaning=m2, example=e2),
        ]
        atts = _emit_group_pairs(
            members, doc, pattern="parenthesized_gloss_pair", quoted_line=m.group(0)
        )
        for att in atts:
            rich_pairs.add((att.member_a.word, att.member_b.word))
        out.extend(atts)

    # 2. Inline definition pairs: "word1 — def1 і/а word2 — def2"
    for m in _INLINE_DEF_PAIR_RE.finditer(flat_seg):
        w1, g1, w2, g2 = m.group(1), m.group(2), m.group(3), m.group(4)
        if not (_is_valid_single_word(w1) and _is_valid_single_word(w2)):
            continue
        if not _is_similar_enough_for_paronym(w1, w2):
            continue
        pair_key = tuple(sorted((normalize_token(w1), normalize_token(w2))))
        if pair_key in rich_pairs:
            continue
        m1, e1 = _split_meaning_and_example(g1)
        m2, e2 = _split_meaning_and_example(g2)
        members = [
            MemberNote(word=normalize_token(w1), attested_form=w1, meaning=m1, example=e1),
            MemberNote(word=normalize_token(w2), attested_form=w2, meaning=m2, example=e2),
        ]
        atts = _emit_group_pairs(
            members, doc, pattern="inline_definition_pair", quoted_line=m.group(0)
        )
        for att in atts:
            rich_pairs.add((att.member_a.word, att.member_b.word))
        out.extend(atts)

    # 3. Stacked gloss pairs (5-klas Zabolotnyi s0027: "1) вистава – виставка\n(спектакль) (показ...)")
    for m in re.finditer(
        rf"\d\)\s*({WORD_CORE})\s*[{DASH_CHARS}]\s*({WORD_CORE})\s*\n\s*\(([^)]+)\)\s*\(([^)]+)\)",
        clean_seg,
    ):
        w1, w2, g1, g2 = m.group(1), m.group(2), m.group(3), m.group(4)
        if _is_valid_single_word(w1) and _is_valid_single_word(w2) and _is_similar_enough_for_paronym(w1, w2):
            members = [
                MemberNote(word=normalize_token(w1), attested_form=w1, meaning=_clean_quote(g1)),
                MemberNote(word=normalize_token(w2), attested_form=w2, meaning=_clean_quote(g2)),
            ]
            atts = _emit_group_pairs(
                members, doc, pattern="parenthesized_gloss_pair", quoted_line=m.group(0)
            )
            for att in atts:
                rich_pairs.add((att.member_a.word, att.member_b.word))
            out.extend(atts)

    # 4. Dash-separated paronym chains: "word1 — word2 [— word3]"
    # Run over flat sentences (not raw lines) so PDF line-wrapped pairs like "уява —\nуявлення"
    # and "заїхати —\nвід'їхати" are preserved intact.
    for line_or_sent in re.split(r"(?<=[.!?])\s+", flat_seg):
        chunk = line_or_sent.strip()
        if not chunk or _DISCLAIMER_RE.search(chunk):
            continue
        # Skip poetry/pun quotes with attribution like "(Л. Костенко)" or "(Нар. тв.)".
        if re.search(
            r"\([А-ЯІЇЄҐ]\.\s*[А-ЯІЇЄҐ][а-яіїєґ]+|Нар\.\s*тв|Ліна\s+Костенко|Тарапуньки",
            chunk,
        ):
            continue
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
                _is_similar_enough_for_paronym(raw_tokens[k], raw_tokens[k + 1])
                for k in range(len(raw_tokens) - 1)
            ):
                continue
            after = chunk[m.end() :].lstrip()
            if after and after[0] not in ",;.)]:»\"'" and not re.match(
                r"^(?:та\s+ін|тощо|і\s+т\.)", after, re.IGNORECASE
            ):
                continue
            before = chunk[: m.start()].rstrip()
            if re.search(r"(?:від\s+гр\.|грец\.|лат\.|рос\.|нім\.)$", before, re.IGNORECASE):
                continue
            members = [MemberNote(word=normalize_token(t), attested_form=t) for t in raw_tokens]
            for att in _emit_group_pairs(
                members, doc, pattern="dash_pair_list", quoted_line=chunk
            ):
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
            _is_similar_enough_for_paronym(raw_tokens[k], raw_tokens[k + 1])
            for k in range(len(raw_tokens) - 1)
        ):
            continue
        members = [MemberNote(word=normalize_token(t), attested_form=t) for t in raw_tokens]
        for att in _emit_group_pairs(
            members, doc, pattern="slash_pair_list", quoted_line=m.group(0)
        ):
            if (att.member_a.word, att.member_b.word) not in rich_pairs:
                out.append(att)

    # 5b. Single-slash collocation headers: "Особистий / особовий: власність, господарство..."
    for m in _COLON_SLASH_CHAIN_RE.finditer(flat_seg):
        w1, w2, shared = m.group(1), m.group(2), m.group(3).strip()
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
            quoted_line=m.group(0),
            shared_context=shared,
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
                members, doc, pattern="conjunction_pair", quoted_line=m.group(0)
            ):
                if (att.member_a.word, att.member_b.word) not in rich_pairs:
                    out.append(att)

    for m in _COLON_CONJ_LIST_RE.finditer(flat_seg):
        list_body = m.group(1)
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
            for att in _emit_group_pairs(
                members, doc, pattern="conjunction_pair", quoted_line=m.group(0)
            ):
                if (att.member_a.word, att.member_b.word) not in rich_pairs:
                    out.append(att)

    # 7. Semicolon-delimited comma groups in explicit paronym exercises
    if ";" in flat_seg and re.search(
        r"(?:паронім|утворіть\s+словосполучення|складіть\s+речення|поясніть\s+різницю)",
        flat_seg,
        re.IGNORECASE,
    ):
        for sent in re.split(r"(?<=[.!?])\s+", flat_seg):
            if ";" not in sent:
                continue
            parts = [p.strip(" .") for p in sent.split(";") if p.strip(" .")]
            if len(parts) < 2:
                continue
            for part in parts:
                mi = _SEMICOLON_COMMA_ITEM_RE.match(part)
                if not mi:
                    continue
                raw_words = [w.strip() for w in mi.group(1).split(",") if w.strip()]
                if not (2 <= len(raw_words) <= 3):
                    continue
                if not all(_is_valid_single_word(w) for w in raw_words):
                    continue
                if not all(
                    _is_similar_enough_for_paronym(raw_words[k], raw_words[k + 1])
                    for k in range(len(raw_words) - 1)
                ):
                    continue
                shared = mi.group(2).strip() if mi.group(2) else None
                members = [MemberNote(word=normalize_token(w), attested_form=w) for w in raw_words]
                for att in _emit_group_pairs(
                    members,
                    doc,
                    pattern="semicolon_comma_group",
                    quoted_line=part,
                    shared_context=shared,
                ):
                    if (att.member_a.word, att.member_b.word) not in rich_pairs:
                        out.append(att)

    # 7b. Explicit "із такими трьома паронімами: водний, водяний, водянистий"
    for m in re.finditer(
        rf"паронімами\s*:\s*({WORD_CORE}(?:\s*,\s*{WORD_CORE}){{1,3}})", flat_seg, re.IGNORECASE
    ):
        raw_words = [w.strip() for w in m.group(1).split(",") if w.strip()]
        if (
            2 <= len(raw_words) <= 4
            and all(_is_valid_single_word(w) for w in raw_words)
            and all(
                _is_similar_enough_for_paronym(raw_words[k], raw_words[k + 1])
                for k in range(len(raw_words) - 1)
            )
        ):
            members = [MemberNote(word=normalize_token(w), attested_form=w) for w in raw_words]
            out.extend(
                _emit_group_pairs(
                    members, doc, pattern="semicolon_comma_group", quoted_line=m.group(0)
                )
            )

    # 8. Choice-in-parentheses exercises inside paronym lessons: "(плутає, путає)"
    if _CHOICE_EXERCISE_PROMPT_RE.search(flat_seg):
        for sent in re.split(r"(?<=[.!?])\s+", flat_seg):
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
                for att in _emit_group_pairs(
                    members, doc, pattern="exercise_choice_pair", quoted_line=sent
                ):
                    if (att.member_a.word, att.member_b.word) not in rich_pairs:
                        out.append(att)

    # 9. Question pairs in paronym intro ("Адрес? Адреса?", "Шкіряний? Шкірний?")
    for m in _QUESTION_PAIR_RE.finditer(clean_seg):
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
            members, doc, pattern="question_pair", quoted_line=m.group(0)
        ):
            if (att.member_a.word, att.member_b.word) not in rich_pairs:
                out.append(att)

    return out


def extract_from_document(doc: SourceDocument) -> list[RawPairAttestation]:
    """Deterministically extract all explicit paronym pair attestations from one SourceDocument."""
    clean_text = _clean_text_for_parsing(doc.text)
    if not clean_text.strip():
        return []

    if re.search(r"словнич[оа]к\s+паронімів", clean_text, re.IGNORECASE):
        return _extract_slash_dictionary(clean_text, doc)
    if re.search(r"короткий\s+словник\s+паронімів", clean_text, re.IGNORECASE):
        return _extract_miyklas_dictionary(clean_text, doc)

    # Summary-table lexical-group overview (7-klas Avramenko s0242/s0243): extract ONLY the
    # explicit Пароніми example row ("рятувальник — ...; рятівник — ...").
    if re.search(r"ГРУПИ\s+ЛЕКСИКИ", clean_text, re.IGNORECASE) and re.search(
        r"рятувальник\s*[—–-]", clean_text, re.IGNORECASE
    ):
        m_row = re.search(
            r"(рятувальник\s*[—–-][^;]+;\s*рятівник\s*[—–-][^\n]+)",
            clean_text,
            re.IGNORECASE | re.DOTALL,
        )
        if not m_row:
            return []
        raw_row = _clean_quote(m_row.group(1))
        members = []
        for part in raw_row.split(";"):
            md = re.match(rf"^\s*({WORD_CORE})\s*[{DASH_CHARS}]\s*(.+)$", part.strip())
            if md:
                meaning, ex = _split_meaning_and_example(md.group(2))
                members.append(
                    MemberNote(
                        word=normalize_token(md.group(1)),
                        attested_form=md.group(1),
                        meaning=meaning,
                        example=ex,
                    )
                )
        return _emit_group_pairs(
            members, doc, pattern="inline_definition_pair", quoted_line=raw_row
        )

    attestations: list[RawPairAttestation] = []
    box_atts, consumed_spans = _extract_named_definition_boxes(clean_text, doc)
    attestations.extend(box_atts)

    residual_text = clean_text
    for start, end in sorted(consumed_spans, reverse=True):
        residual_text = residual_text[:start] + "\n" + residual_text[end:]

    for seg, active in _split_paronym_segments(residual_text, doc):
        if active:
            attestations.extend(_extract_from_segment(seg, doc))

    deduped: list[RawPairAttestation] = []
    seen: set[tuple[str, str, str, str]] = set()
    for att in attestations:
        key = (att.member_a.word, att.member_b.word, att.pattern, att.quoted_line)
        if key not in seen:
            seen.add(key)
            deduped.append(att)
    return deduped
