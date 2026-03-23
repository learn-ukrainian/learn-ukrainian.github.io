"""Live query tools for Ukrainian language research sources.

Provides programmatic access to external Ukrainian-language resources
for fact-checking, vocabulary verification, and research grounding.

Sources:
  - Wikipedia (uk.wikipedia.org) — encyclopedic summaries and extracts
  - GRAC (uacorpus.org) — corpus frequency, concordance, collocations
  - ULIF (lcorp.ulif.org.ua) — declension/conjugation paradigms
  - r2u (r2u.org.ua) — Russian→Ukrainian translation dictionary
  - pravopys (2019.pravopys.net) — official orthography rules (2019)
  - SUM-20 (sum20ua.com) — academic dictionary definitions (А–Р only)

Usage:
    from rag.source_query import wikipedia_summary, grac_frequency, ulif_paradigm

    # Wikipedia
    result = wikipedia_summary("Тарас Шевченко")

    # GRAC corpus frequency
    result = grac_frequency("книга")

    # ULIF paradigm
    result = ulif_paradigm("стіл")
"""

import re
from html.parser import HTMLParser
from typing import Any, ClassVar
from urllib.parse import quote

import requests

# ── Shared config ────────────────────────────────────────────────

REQUEST_TIMEOUT = 15
# Browser-like UA required by some Ukrainian sites (pravopys blocks bot UAs)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "uk,en-US;q=0.7,en;q=0.3",
})


def _get(url: str, timeout: int = REQUEST_TIMEOUT, **kwargs) -> requests.Response:
    """GET with standard timeout and error handling."""
    return _SESSION.get(url, timeout=timeout, **kwargs)


# ══════════════════════════════════════════════════════════════════
# Wikipedia (uk.wikipedia.org)
# ══════════════════════════════════════════════════════════════════

WIKI_REST = "https://uk.wikipedia.org/api/rest_v1"
WIKI_API = "https://uk.wikipedia.org/w/api.php"


def wikipedia_summary(title: str) -> dict[str, Any] | None:
    """Fetch a Wikipedia article summary via REST API.

    Returns dict with keys: title, description, extract, url
    or None if article not found.
    """
    url = f"{WIKI_REST}/page/summary/{quote(title)}"
    try:
        r = _get(url)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
        return {
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "extract": data.get("extract", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except requests.RequestException:
        return None


def wikipedia_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Search Ukrainian Wikipedia. Returns list of {title, snippet}."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
        "utf8": 1,
    }
    try:
        r = _get(WIKI_API, params=params)
        r.raise_for_status()
        results = r.json().get("query", {}).get("search", [])
        return [
            {
                "title": item["title"],
                "snippet": re.sub(r"<[^>]+>", "", item.get("snippet", "")),
            }
            for item in results
        ]
    except requests.RequestException:
        return []


def wikipedia_sections(title: str) -> list[dict[str, Any]] | None:
    """Get section structure of a Wikipedia article.

    Returns list of {toclevel, number, line, index} or None.
    """
    params = {
        "action": "parse",
        "page": title,
        "prop": "sections",
        "format": "json",
        "utf8": 1,
    }
    try:
        r = _get(WIKI_API, params=params)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            return None
        return data.get("parse", {}).get("sections", [])
    except requests.RequestException:
        return None


def wikipedia_extract(title: str, max_chars: int = 50000) -> dict[str, Any] | None:
    """Fetch full plaintext of a Wikipedia article.

    Uses the MediaWiki API with prop=extracts&explaintext=1 for clean text.
    Returns dict with keys: title, extract, url — or None if not found.
    """
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts|info",
        "explaintext": 1,
        "exlimit": 1,
        "inprop": "url",
        "redirects": 1,
        "format": "json",
        "utf8": 1,
    }
    try:
        r = _get(WIKI_API, params=params)
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        # MediaWiki returns pages keyed by page ID; -1 means not found
        for page_id, page in pages.items():
            if page_id == "-1" or "missing" in page:
                return None
            extract = page.get("extract", "")
            if max_chars and len(extract) > max_chars:
                extract = extract[:max_chars] + "\n\n[... truncated ...]"
            return {
                "title": page.get("title", title),
                "extract": extract,
                "url": page.get("fullurl", f"https://uk.wikipedia.org/wiki/{quote(title)}"),
            }
        return None
    except requests.RequestException:
        return None


def wikipedia_section_text(title: str, section_index: int) -> dict[str, Any] | None:
    """Fetch text of a specific section of a Wikipedia article.

    Uses action=parse with section parameter. Returns wikitext converted
    to plaintext (strips markup). Returns dict with keys: title, section,
    text — or None if not found.
    """
    params = {
        "action": "parse",
        "page": title,
        "section": section_index,
        "prop": "wikitext",
        "format": "json",
        "utf8": 1,
    }
    try:
        r = _get(WIKI_API, params=params)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            return None
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        # Strip common wikitext markup for readability
        text = _strip_wikitext(wikitext)
        return {
            "title": data.get("parse", {}).get("title", title),
            "section": section_index,
            "text": text,
        }
    except requests.RequestException:
        return None


def _strip_wikitext(text: str) -> str:
    """Convert wikitext to approximate plaintext."""
    # Remove references <ref>...</ref>
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*/?>", "", text)
    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Remove templates {{ ... }} (simple, non-nested)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Second pass for one level of nesting
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Convert [[link|display]] → display, [[link]] → link
    text = re.sub(r"\[\[[^]]*\|([^]]*)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^]]*)\]\]", r"\1", text)
    # Remove external links [url text] → text
    text = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\]", "", text)
    # Remove bold/italic markup
    text = re.sub(r"'{2,5}", "", text)
    # Remove section headers (== Title ==) — keep the text
    text = re.sub(r"^=+\s*(.*?)\s*=+$", r"\1", text, flags=re.MULTILINE)
    # Remove remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ══════════════════════════════════════════════════════════════════
# GRAC Corpus (uacorpus.org) — NoSketch Engine API
# ══════════════════════════════════════════════════════════════════

GRAC_BASE = "https://sketch.uacorpus.org/bonito/run.cgi"
GRAC_CORPUS = "grac19a"


def grac_frequency(word: str) -> dict[str, Any] | None:
    """Get word frequency from GRAC corpus.

    Returns dict with keys: word, freq, rel_freq (per million)
    or None on failure.
    """
    params = {
        "corpname": GRAC_CORPUS,
        "wlattr": "word",
        "wlpat": word,
        "wlminfreq": 1,
        "wlmaxitems": 10,
        "format": "json",
    }
    try:
        r = _get(f"{GRAC_BASE}/wordlist", params=params)
        r.raise_for_status()
        data = r.json()
        items = data.get("Items", [])
        if not items:
            return {"word": word, "freq": 0, "rel_freq": 0.0}
        # Find exact match or return first
        for item in items:
            if item.get("str", "") == word:
                return {
                    "word": word,
                    "freq": item.get("frq", 0),
                    "rel_freq": item.get("relfreq", 0.0),
                }
        first = items[0]
        return {
            "word": first.get("str", word),
            "freq": first.get("frq", 0),
            "rel_freq": first.get("relfreq", 0.0),
        }
    except requests.RequestException:
        return None


def grac_lemma_frequency(lemma: str) -> dict[str, Any] | None:
    """Get frequency of all forms of a lemma from GRAC.

    Returns dict with keys: lemma, total_freq, forms [{word, freq, pct}]
    or None on failure.
    """
    cql = f'[lemma="{lemma}"]'
    params = {
        "corpname": GRAC_CORPUS,
        "q": f"q{cql}",
        "fcrit": "word/e 0~0>0",
        "flimit": 1,
        "format": "json",
    }
    try:
        r = _get(f"{GRAC_BASE}/freqs", params=params)
        r.raise_for_status()
        data = r.json()
        blocks = data.get("Blocks", [])
        if not blocks or not blocks[0].get("Items"):
            return {"lemma": lemma, "total_freq": 0, "forms": []}
        items = blocks[0]["Items"]
        forms = []
        total = 0
        for item in items:
            freq = item.get("frq", 0)
            total += freq
            forms.append({
                "word": item.get("str", ""),
                "freq": freq,
                "pct": item.get("poc", 0.0),
            })
        return {"lemma": lemma, "total_freq": total, "forms": forms}
    except requests.RequestException:
        return None


def grac_concordance(query: str, limit: int = 10) -> list[dict[str, str]]:
    """Get concordance lines (KWIC) from GRAC for a simple query.

    Returns list of {left, kwic, right} dicts.
    """
    params = {
        "corpname": GRAC_CORPUS,
        "iquery": query,
        "queryselector": "iqueryrow",
        "pagesize": limit,
        "format": "json",
    }
    try:
        r = _get(f"{GRAC_BASE}/first", params=params)
        r.raise_for_status()
        data = r.json()
        lines = data.get("Lines", [])
        results = []
        for line in lines:
            left = " ".join(t.get("str", "") for t in line.get("Left", []))
            kwic = " ".join(t.get("str", "") for t in line.get("Kwic", []))
            right = " ".join(t.get("str", "") for t in line.get("Right", []))
            results.append({"left": left.strip(), "kwic": kwic.strip(), "right": right.strip()})
        return results
    except requests.RequestException:
        return []


def grac_collocations(
    lemma: str, window: int = 5, limit: int = 20, sort: str = "t"
) -> list[dict[str, Any]]:
    """Get collocations for a lemma from GRAC.

    Args:
        lemma: Ukrainian lemma to find collocates for
        window: context window size (default ±5)
        limit: max collocates to return
        sort: sort function — 't' (t-score), 'm' (MI), 'd' (logDice)

    Returns list of {word, freq, score} dicts.
    """
    cql = f'[lemma="{lemma}"]'
    params = {
        "corpname": GRAC_CORPUS,
        "q": f"q{cql}",
        "cattr": "lemma",
        "cfromw": -window,
        "ctow": window,
        "cminfreq": 3,
        "cmaxitems": limit,
        "csortfn": sort,
        "format": "json",
    }
    try:
        r = _get(f"{GRAC_BASE}/collx", params=params)
        r.raise_for_status()
        data = r.json()
        items = data.get("Items", [])
        return [
            {
                "word": item.get("str", ""),
                "freq": item.get("freq", 0),
                "score": item.get(sort, 0.0),
            }
            for item in items
        ]
    except requests.RequestException:
        return []


# ══════════════════════════════════════════════════════════════════
# ULIF — Ukrainian Lingua-Information Fund (paradigm tables)
# ══════════════════════════════════════════════════════════════════

ULIF_BASE = "https://lcorp.ulif.org.ua/dictua"


class _UlifParadigmParser(HTMLParser):
    """Extract paradigm table from ULIF HTML.

    ULIF pages have multiple tables. The paradigm table is identified
    by containing case labels (називний, родовий, etc.).
    We collect all tables, then keep only the one with case data.
    """

    CASE_LABELS: ClassVar[set[str]] = {"називний", "родовий", "давальний", "знахідний", "орудний", "місцевий", "кличний"}

    def __init__(self):
        super().__init__()
        self._in_table = False
        self._in_cell = False
        self._table_idx = 0
        self._current_row: list[str] = []
        self._all_tables: list[list[list[str]]] = []
        self._current_table: list[list[str]] = []
        self._cell_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table = True
            self._current_table = []
        elif self._in_table and tag in ("td", "th"):
            self._in_cell = True
            self._cell_text = ""

    def handle_endtag(self, tag):
        if tag == "table" and self._in_table:
            self._in_table = False
            if self._current_row:
                self._current_table.append(self._current_row)
                self._current_row = []
            self._all_tables.append(self._current_table)
            self._current_table = []
        elif self._in_table and tag in ("td", "th"):
            self._in_cell = False
            self._current_row.append(self._cell_text.strip())
        elif self._in_table and tag == "tr":
            if self._current_row:
                self._current_table.append(self._current_row)
            self._current_row = []

    def handle_data(self, data):
        if self._in_cell:
            self._cell_text += data

    def get_paradigm_rows(self) -> list[list[str]]:
        """Return rows from the table containing case labels."""
        for table in self._all_tables:
            for row in table:
                if any(cell.lower() in self.CASE_LABELS for cell in row):
                    # Filter out empty/header rows
                    return [r for r in table if any(c.strip() for c in r) and len(r) > 1]
        return []


def ulif_paradigm(word: str) -> dict[str, Any] | None:
    """Fetch declension/conjugation paradigm from ULIF.

    ULIF is an ASP.NET WebForms app — requires a two-step process:
    1. GET the page to obtain ViewState/EventValidation tokens
    2. POST with the word in the search field (image button needs .x/.y)

    Returns dict with keys: word, rows (list of lists representing
    the paradigm table — header row + case rows) or None on failure.
    """
    try:
        # Step 1: GET to obtain ASP.NET tokens
        r1 = _get(ULIF_BASE)
        r1.raise_for_status()

        vs_m = re.search(r'name="__VIEWSTATE"[^>]*value="([^"]*)"', r1.text)
        vsgen_m = re.search(r'name="__VIEWSTATEGENERATOR"[^>]*value="([^"]*)"', r1.text)
        ev_m = re.search(r'name="__EVENTVALIDATION"[^>]*value="([^"]*)"', r1.text)
        if not vs_m or not ev_m:
            return None

        # Step 2: POST with search word (image button sends .x/.y)
        data = {
            "__VIEWSTATE": vs_m.group(1),
            "__VIEWSTATEGENERATOR": vsgen_m.group(1) if vsgen_m else "",
            "__EVENTVALIDATION": ev_m.group(1),
            "ctl00$ContentPlaceHolder1$tsearch": word,
            "ctl00$ContentPlaceHolder1$search.x": "10",
            "ctl00$ContentPlaceHolder1$search.y": "10",
        }
        r2 = _SESSION.post(f"{ULIF_BASE}/", data=data, timeout=REQUEST_TIMEOUT)
        r2.raise_for_status()

        parser = _UlifParadigmParser()
        parser.feed(r2.text)
        rows = parser.get_paradigm_rows()
        if not rows:
            return None
        return {"word": word, "rows": rows}
    except requests.RequestException:
        return None


# ══════════════════════════════════════════════════════════════════
# r2u.org.ua — Russian→Ukrainian dictionary
# ══════════════════════════════════════════════════════════════════

R2U_BASE = "https://r2u.org.ua"


def _parse_dict_entries(html: str) -> list[dict[str, str]]:
    """Parse dictionary entries from r2u/e2u HTML (table-based layout).

    Both sites use <td class="result_row"> or <td class="result_row_main">
    with <b> or <span class="...Bold"> for headwords and inline translations.
    """
    import re
    entries = []
    # Find all result_row cells
    for match in re.finditer(
        r'<td[^>]*class="result_row(?:_main)?"[^>]*>(.*?)</td>',
        html, re.DOTALL,
    ):
        cell = match.group(1)
        # Extract headword (bold text)
        hw_match = re.search(r'<b>([^<]+)</b>|<span class="[^"]*Bold">([^<]+)</span>', cell)
        if not hw_match:
            continue
        headword = (hw_match.group(1) or hw_match.group(2) or "").strip()

        # Extract translation (strip all HTML tags)
        translation = re.sub(r"<[^>]+>", " ", cell)
        translation = re.sub(r"\s+", " ", translation).strip()

        if headword:
            entries.append({"headword": headword, "translation": translation})

    return entries


def r2u_translate(russian_word: str) -> list[dict[str, str]]:
    """Look up Russian→Ukrainian translation on r2u.org.ua.

    Uses the /s endpoint (?w=word). Returns list of {headword, translation} dicts.
    """
    try:
        r = _get(f"{R2U_BASE}/s", params={"w": russian_word}, timeout=20)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return _parse_dict_entries(r.text)
    except requests.RequestException:
        return []


# ══════════════════════════════════════════════════════════════════
# e2u (e2u.org.ua) — English→Ukrainian translation dictionary
# ══════════════════════════════════════════════════════════════════

E2U_BASE = "https://e2u.org.ua"


def e2u_translate(english_word: str) -> list[dict[str, str]]:
    """Look up English→Ukrainian translation on e2u.org.ua.

    Uses the /s endpoint (?w=word). 331,723 entries across general, IT,
    scientific, EU, business, and legal dictionaries.
    """
    try:
        r = _get(f"{E2U_BASE}/s", params={"w": english_word, "dicts": "all"}, timeout=20)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return _parse_dict_entries(r.text)
    except requests.RequestException:
        return []


WIKTIONARY_API = "https://en.wiktionary.org/w/api.php"


def wiktionary_translate(ukrainian_word: str) -> str:
    """Look up Ukrainian word → English translation via Wiktionary API.

    Queries en.wiktionary.org for the Ukrainian section of the word's page.
    Returns the first English definition, or empty string if not found.

    Free API, no scraping needed. Works for most common Ukrainian words.
    """
    try:
        r = _get(WIKTIONARY_API, params={
            "action": "parse", "page": ukrainian_word.lower(),
            "format": "json", "prop": "wikitext",
        }, timeout=15, headers={"User-Agent": "LearnUkrainian/1.0"})
        if r.status_code != 200:
            return ""

        data = r.json()
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        if not wikitext:
            return ""

        # Find Ukrainian section
        import re
        uk_section = re.search(r"==Ukrainian==(.*?)(?=\n==[A-Z]|\Z)", wikitext, re.DOTALL)
        if not uk_section:
            return ""

        # Extract first definition (# [[translation]])
        defs = re.findall(r"#\s*(?:\{\{[^}]+\}\}\s*)?(?:\[\[)?([a-zA-Z][a-zA-Z\s,]+?)(?:\]\])?(?:\s*$|\s*,)", uk_section.group(1), re.MULTILINE)
        if defs:
            return defs[0].strip()

        # Fallback: any [[word]] in definitions
        links = re.findall(r"\[\[([a-zA-Z][a-zA-Z\s]+?)\]\]", uk_section.group(1))
        if links:
            return links[0].strip()

        return ""
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════
# pravopys (2019.pravopys.net) — Ukrainian orthography rules
# ══════════════════════════════════════════════════════════════════

PRAVOPYS_BASE = "https://2019.pravopys.net"

# Static mapping of topics to section numbers (1-61)
# Search is client-side JS only — no server API
PRAVOPYS_SECTIONS = {
    "е-и": 1, "і-и": 2, "ї-йі": 3, "я-ю-є": 4,
    "г": 5, "ґ": 6, "апостроф": 7, "йо-ьо": 8,
    "чергування-о-і": 9, "чергування-е-і": 10, "чергування-інші": 11,
    "приголосні-перед-суфіксами": 12, "зміни-приголосних": 13,
    "спрощення": 14, "давальний": 15, "орудний": 16,
    "місцевий": 17, "кличний": 18,
    "подвоєння": 19, "уподібнення": 20,
    "зубні-перед-м-якими": 21, "африкати": 22,
    "у-в": 23, "і-й": 24, "з-із-зі": 25,
    "м-який-знак": 26, "м-який-знак-не": 27,
    "спрощення-груп": 28,
    "подовження": 29, "подвоєння-загальне": 30,
    "префікси": 31,
    "суфікси-іменників": 32, "суфікси-прикметників": 33, "суфікси-дієслів": 34,
    "разом-іменники": 35, "разом-прикметники": 36,
    "разом-числівники": 37, "разом-займенники": 38,
    "разом-прислівники": 39, "разом-прийменники": 40,
    "разом-сполучники": 41, "разом-частки": 42,
    "через-дефіс": 43, "разом-окремо": 44,
    "велика-літера-загальне": 45, "велика-літера-речення": 46,
    "велика-літера-заголовки": 47, "велика-літера-після-двокрапки": 48,
    "імена": 49, "географічні": 50, "астрономічні": 51,
    "історичні": 52, "релігійні": 53, "державні": 54,
    "документи": 55, "звання": 56, "нагороди": 57,
    "торгові-марки": 58, "породи-тварин": 59,
    "стилістичні": 60, "абревіатури": 61,
}


def _extract_pravopys_text(html: str) -> str:
    """Extract rule text from pravopys section HTML.

    The site doesn't use consistent CSS classes. We strip navigation,
    scripts, and styles, then extract the remaining body text.
    """
    # Remove non-content elements
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<nav[^>]*>.*?</nav>", "", text, flags=re.DOTALL)
    text = re.sub(r"<header[^>]*>.*?</header>", "", text, flags=re.DOTALL)
    text = re.sub(r"<footer[^>]*>.*?</footer>", "", text, flags=re.DOTALL)
    # Convert block elements to newlines
    text = re.sub(r"<(?:p|li|h[1-6]|div|br)[^>]*>", "\n", text)
    # Convert HTML entities
    text = text.replace("&nbsp;", " ").replace("&#x301;", "\u0301")
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Find where the rule content starts (§ or first Cyrillic block)
    match = re.search(r"§\s*\d|(?:Апостроф|Велика|Подвоєння|М.який|Чергування)", text)
    if match:
        text = text[max(0, match.start() - 20):]
    return text.strip()


def pravopys_section(section_num: int) -> dict[str, Any] | None:
    """Fetch an orthography rule section by number (1-61).

    Returns dict with keys: section, url, text
    or None on failure.
    """
    if not 1 <= section_num <= 61:
        return None
    url = f"{PRAVOPYS_BASE}/sections/{section_num}/"
    try:
        r = _get(url)
        if r.status_code in (403, 404):
            return None
        r.raise_for_status()
        r.encoding = "utf-8"  # Site returns ISO-8859-1 header but content is UTF-8
        text = _extract_pravopys_text(r.text)
        if not text:
            return None
        return {"section": section_num, "url": url, "text": text}
    except requests.RequestException:
        return None


def pravopys_lookup(topic: str) -> dict[str, Any] | None:
    """Look up an orthography rule by topic keyword.

    Uses the static topic→section mapping. Tries exact match first,
    then substring match. Returns the section content or None.
    """
    topic_lower = topic.lower().strip()
    # Exact match
    if topic_lower in PRAVOPYS_SECTIONS:
        return pravopys_section(PRAVOPYS_SECTIONS[topic_lower])
    # Substring match
    for key, num in PRAVOPYS_SECTIONS.items():
        if topic_lower in key or key in topic_lower:
            return pravopys_section(num)
    return None


# ══════════════════════════════════════════════════════════════════
# SUM-20 (sum20ua.com) — Academic Ukrainian dictionary
# Only covers volumes 1–16 (А–Р)
# ══════════════════════════════════════════════════════════════════

SUM_BASE = "https://sum20ua.com"


class _SumEntryParser(HTMLParser):
    """Extract dictionary entry from SUM-20 HTML."""

    def __init__(self):
        super().__init__()
        self._in_entry = False
        self._entries: list[str] = []
        self._current = ""
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if tag == "div" and ("word-entry" in cls or "entry-text" in cls):
            self._in_entry = True
            self._current = ""
            self._depth = 0
        if self._in_entry:
            self._depth += 1

    def handle_endtag(self, tag):
        if self._in_entry:
            self._depth -= 1
            if tag == "div" and self._depth <= 0:
                self._in_entry = False
                if self._current.strip():
                    self._entries.append(self._current.strip())

    def handle_data(self, data):
        if self._in_entry:
            self._current += data


def sum_definition(word: str) -> dict[str, Any] | None:
    """Look up a word in the SUM-20 dictionary.

    Only covers А–Р (volumes 1–16). Returns dict with keys:
    word, url, text (raw entry text) or None on failure.

    Warning: server is slow and intermittently unreliable.
    """
    url = f"{SUM_BASE}/Entry/search/{quote(word)}"
    try:
        r = _get(url, timeout=20)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        parser = _SumEntryParser()
        parser.feed(r.text)
        if parser._entries:
            return {"word": word, "url": url, "text": parser._entries[0]}
        # Fallback: try to extract text near the word
        # SUM doesn't have consistent CSS classes
        idx = r.text.lower().find(word.lower())
        if idx > 0:
            snippet = r.text[max(0, idx - 200):idx + 500]
            clean = re.sub(r"<[^>]+>", " ", snippet)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean:
                return {"word": word, "url": url, "text": clean}
        return None
    except requests.RequestException:
        return None


# ══════════════════════════════════════════════════════════════════
# Convenience: multi-source lookup
# ══════════════════════════════════════════════════════════════════

def verify_word_sources(word: str) -> dict[str, Any]:
    """Query multiple sources for a Ukrainian word.

    Returns a dict with results from each source that returned data.
    Useful for cross-referencing during research validation.
    """
    results: dict[str, Any] = {"word": word}

    freq = grac_frequency(word)
    if freq and freq.get("freq", 0) > 0:
        results["grac"] = freq

    paradigm = ulif_paradigm(word)
    if paradigm:
        results["ulif"] = paradigm

    wiki = wikipedia_search(word, limit=3)
    if wiki:
        results["wikipedia"] = wiki

    return results


def check_russicism(russian_form: str, ukrainian_form: str) -> dict[str, Any]:
    """Check if a suspected Russicism has a proper Ukrainian equivalent.

    Queries r2u for the Russian form and checks GRAC frequency
    for both forms to determine which is standard Ukrainian.
    """
    result: dict[str, Any] = {
        "russian": russian_form,
        "ukrainian": ukrainian_form,
    }

    # Check r2u for the Russian→Ukrainian mapping
    translations = r2u_translate(russian_form)
    if translations:
        result["r2u_translations"] = translations

    # Check GRAC frequency for both forms
    ru_freq = grac_frequency(russian_form)
    uk_freq = grac_frequency(ukrainian_form)
    if ru_freq:
        result["russian_in_grac"] = ru_freq
    if uk_freq:
        result["ukrainian_in_grac"] = uk_freq

    return result
