"""
Russicism Detection

Detects common Russian calques and lexical Russicisms in Ukrainian content.
These are words/phrases that are Russian borrowings with standard Ukrainian
equivalents. The Phase B prompt lists them as "HARD FAIL" items.

Returns list[dict] with 'type', 'severity', 'issue', 'fix' keys.
No LLM calls — pure regex matching.

Issue: #596
"""

import re

from .prose_quality import _split_narrative_zones

# ---------------------------------------------------------------------------
# Russicism patterns: (regex, term, correct_form, note)
# Ordered from most to least specific to avoid shorter patterns masking longer ones.
# ---------------------------------------------------------------------------

_RUSSICISMS: list[dict] = [
    {
        "pattern": r"\bприймати\s+участь",
        "term": "приймати участь",
        "fix": "брати участь",
        "note": "Russian calque 'принимать участие'",
    },
    {
        "pattern": r"\bсамий\s+кращий",
        "term": "самий кращий",
        "fix": "найкращий",
        "note": "Russian superlative pattern 'самый лучший'",
    },
    {
        "pattern": r"\bна\s+то,?\s+що",
        "term": "на то, що",
        "fix": "на те, що",
        "note": "Russian calque 'на то, что'",
    },
    {
        "pattern": r"\bкушати\b",
        "term": "кушати",
        "fix": "їсти",
        "note": "Russian 'кушать' — not standard Ukrainian",
    },
    {
        "pattern": r"\bполучати\b",
        "term": "получати",
        "fix": "отримувати",
        "note": "Russian 'получать'",
    },
    {
        "pattern": r"\bвідноситися\b",
        "term": "відноситися",
        "fix": "стосуватися / ставитися",
        "note": "Russian 'относиться'",
    },
    {
        "pattern": r"\bслідуючий\b",
        "term": "слідуючий",
        "fix": "наступний",
        "note": "Russian 'следующий'",
    },
    # "любий" meaning "будь-який" (any) — not "любий" meaning "dear/beloved"
    # Only flag when followed by a noun that suggests "any" meaning
    {
        "pattern": r"\bлюбий\s+(?:момент|випадок|час|день|спосіб|варіант)",
        "term": "любий (= будь-який)",
        "fix": "будь-який",
        "note": "Russian 'любой' meaning 'any' — Ukrainian 'любий' means 'dear/beloved'",
    },
    # Additional common Russicisms not in the prompt table but frequently observed
    {
        "pattern": r"\bвообще\b",
        "term": "вообще",
        "fix": "взагалі",
        "note": "Direct Russian borrowing",
    },
    {
        "pattern": r"\bконєшно\b",
        "term": "конєшно",
        "fix": "звичайно / звісно",
        "note": "Russified pronunciation spelling of 'конечно'",
    },
    {
        "pattern": r"\bнравитися\b",
        "term": "нравитися",
        "fix": "подобатися",
        "note": "Russian 'нравиться'",
    },
    {
        "pattern": r"\bскучати\b",
        "term": "скучати",
        "fix": "сумувати / нудьгувати",
        "note": "Russian 'скучать'",
    },
    {
        "pattern": r"\bприкольн\w+\b",
        "term": "прикольний/прикольно",
        "fix": "кумедний / класний / файний",
        "note": "Russian slang 'прикольный'",
    },
    # Imperative calques: давайте + future perfective → Ukrainian -мо form
    {
        "pattern": r"\bдавайте\s+попрактикуємо\b",
        "term": "давайте попрактикуємо",
        "fix": "попрактикуймо",
        "note": "Russian imperative calque 'давайте попрактикуем'",
    },
    {
        "pattern": r"\bдавайте\s+повторимо\b",
        "term": "давайте повторимо",
        "fix": "повторімо",
        "note": "Russian imperative calque 'давайте повторим'",
    },
    {
        "pattern": r"\bдавайте\s+подивимося\b",
        "term": "давайте подивимося",
        "fix": "подивімося",
        "note": "Russian imperative calque 'давайте посмотрим'",
    },
    # Lexical Russicisms from A1 proofreading scan
    {
        "pattern": r"\bздач[аіу]\b",
        "term": "здача (change/money)",
        "fix": "решта",
        "note": "Russian 'сдача' — Ukrainian uses 'решта'",
    },
    {
        "pattern": r"\bтапочк[иі]\b",
        "term": "тапочки",
        "fix": "капці",
        "note": "Russian 'тапочки' — Ukrainian uses 'капці'",
    },
    {
        "pattern": r"\bнадіятися\b",
        "term": "надіятися",
        "fix": "сподіватися",
        "note": "Russian 'надеяться' — Ukrainian prefers 'сподіватися'",
    },
    {
        "pattern": r"\bдобавити\b",
        "term": "добавити",
        "fix": "додати",
        "note": "Russian 'добавить'",
    },
    {
        "pattern": r"\bхватить\b",
        "term": "хватить",
        "fix": "вистачить",
        "note": "Russian 'хватить'",
    },
    {
        "pattern": r"\bобязательно\b",
        "term": "обязательно",
        "fix": "обов'язково",
        "note": "Direct Russian borrowing",
    },
]

# Pre-compile patterns
_COMPILED_RUSSICISMS = [
    {**r, "_compiled": re.compile(r["pattern"], re.IGNORECASE)}
    for r in _RUSSICISMS
]

# Tracks where Russicisms might appear in quoted historical sources
_EXEMPT_TRACKS = {"oes", "ruth"}


def _is_in_quote_context(text: str, match_start: int) -> bool:
    """Check if a match position is inside guillemets or a blockquote."""
    # Check for guillemets «...»
    before = text[:match_start]
    open_guillemet = before.rfind('«')
    close_guillemet = before.rfind('»')
    if open_guillemet > close_guillemet:
        return True  # Inside guillemets

    # Check for blockquote line
    line_start = before.rfind('\n') + 1
    line = text[line_start:match_start].lstrip()
    return bool(line.startswith('>'))


def check_russicisms(content: str, file_path: str = '') -> list[dict]:
    """
    Detect common Russicisms in Ukrainian content.

    Checks narrative zones for known Russian calques and borrowings.
    Skips matches inside guillemets «» or blockquotes (legitimate quoting).
    Skips OES/RUTH tracks (historical texts).

    Severity: critical if 3+ found, warning if 1-2 found.
    """
    # Check track exemption
    path_lower = file_path.lower()
    for exempt in _EXEMPT_TRACKS:
        if f'/{exempt}/' in path_lower:
            return []

    # Get narrative zones only
    narrative_zones = _split_narrative_zones(content)
    narrative_text = '\n'.join(narrative_zones)

    found = []

    for russicism in _COMPILED_RUSSICISMS:
        for m in russicism["_compiled"].finditer(narrative_text):
            # Skip if in quote context
            if _is_in_quote_context(narrative_text, m.start()):
                continue
            found.append({
                "term": russicism["term"],
                "fix": russicism["fix"],
                "note": russicism["note"],
                "matched": m.group(),
            })

    if not found:
        return []

    violations = []
    # Deduplicate by term
    unique_terms = {}
    for f in found:
        if f["term"] not in unique_terms:
            unique_terms[f["term"]] = f
        else:
            unique_terms[f["term"]]["count"] = unique_terms[f["term"]].get("count", 1) + 1

    term_list = '; '.join(
        f"'{v['term']}' → {v['fix']}"
        for v in list(unique_terms.values())[:6]
    )

    count = len(found)
    severity = 'critical' if count >= 3 else 'warning'

    violations.append({
        'type': 'RUSSICISM_DETECTED',
        'severity': severity,
        'issue': f"Found {count} Russicism(s) in content: {term_list}",
        'fix': (
            "Replace Russicisms with standard Ukrainian equivalents. "
            "These are Russian calques that have standard Ukrainian forms. "
            "See Phase B prompt 'Russianisms Pre-Output Scan' table."
        ),
    })

    return violations
