"""
Imperial Framing Terminology Check

Detects Russian/Soviet imperial terminology in curriculum content.
Flags terms that represent colonial or propagandistic narratives.

Two tiers:
  ALWAYS_BANNED  → severity: error (blocks pass) — no valid use case
  SUSPICIOUS     → severity: warning (flags for review) — might be
                   legitimate in critical/educational context;
                   auto-cleared if term is inside «guillemets» or
                   preceded by critical markers (міф, пропаганда…)

Track exemptions:
  OES, RUTH — fully exempt (teach historical Ruthenian/OES texts
               that legitimately contain archaic imperial vocabulary)
"""

import re
from typing import List, Dict

# Tracks where historical imperial terms may appear legitimately
EXEMPT_TRACKS = {"oes", "ruth"}

# ---------------------------------------------------------------------------
# Term definitions
# ---------------------------------------------------------------------------

# Always wrong — no valid educational use that requires the uncritical form
ALWAYS_BANNED: List[Dict] = [
    {
        "pattern": r"Велика\s+Вітчизняна\s+війна",
        "term": "Велика Вітчизняна війна",
        "reason": "Soviet propaganda framing of WWII",
        "fix": 'Use "Друга світова війна". '
               'The GPW framing erases Ukrainian suffering and reframes Russian aggression as defence.',
    },
    {
        "pattern": r"Kievan\s+Rus[''ʼ]?",
        "term": "Kievan Rus",
        "reason": "Russian-imperial transliteration ('Kiev' not 'Kyiv')",
        "fix": "Use \"Kyivan Rus'\" in English, \"Київська Русь\" in Ukrainian.",
    },
    {
        "pattern": r"\bKiev\b",
        "term": "Kiev",
        "reason": "Russian transliteration of Kyiv",
        "fix": 'Use "Kyiv". This applies to all English text in the module.',
    },
    {
        "pattern": r"триєдин\w*\s+(?:народ|брат\w*|слов\w*)",
        "term": "триєдиний народ/братерство",
        "reason": "Russian imperial myth of Slavic triune brotherhood",
        "fix": "Remove or reframe explicitly as a myth being debunked.",
    },
]

# Suspicious — might appear in critical/educational context;
# only flagged if NOT inside quotes or preceded by critical markers
SUSPICIOUS: List[Dict] = [
    {
        "pattern": r"возз['\u2019\u02bc]єднання",
        "term": "возз'єднання",
        "reason": 'Soviet "reunification" myth for the 1654 Pereiaslav agreement',
        "fix": 'Use "союз", "угода", "Переяславська угода". '
               "Ukraine was not 'reuniting' — it signed a military alliance.",
    },
    {
        "pattern": r"Мало\s*росі[яї]",
        "term": "Малоросія",
        "reason": "Russian colonial geographic construct",
        "fix": "Use Ukrainian regional terms (Лівобережжя, Правобережжя, Слобожанщина…)",
    },
    {
        "pattern": r"Мало\s*рос(?:ійськ)\w*",
        "term": "Малоросійський",
        "reason": "Russian colonial adjective",
        "fix": "Use specific Ukrainian regional adjectives.",
    },
    {
        "pattern": r"Ново\s*росі[яї]",
        "term": "Новоросія",
        "reason": "Russian imperial/contemporary propaganda geographic term",
        "fix": "Use 'Південь України' or specific oblast names.",
    },
]

# Markers that indicate a term is being critically discussed, not endorsed
CRITICAL_MARKERS = [
    "так звана", "так зван", "так зване", "так звані",
    "міф", "пропаганд", "фальш", "неправильн", "помилков",
    "myth", "propaganda", "so-called",
    "\u00abне ",   # «не — negation before guillemet
    " не \"",      # не " — negation before curly/straight quote
    " не \u201c",  # не " — negation before curly open quote
    "це не",       # explicitly not this thing
    "не є",        # is not
    "decoloniz",   # inside a decolonization callout
    "imperial",    # being discussed as imperial construct
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_track(file_path: str) -> str | None:
    if not file_path:
        return None
    path = str(file_path)
    for track in ["c1-hist", "c1-bio", "b2-hist", "b2-pro", "c1-pro",
                  "oes", "ruth", "lit", "a1", "a2", "b1", "b2", "c1", "c2"]:
        if f"/{track}/" in path:
            return track
    return None


def _in_quotes(line: str, pos: int) -> bool:
    """Return True if pos is inside «…», "…", "…", or "…" in line."""
    before = line[:pos]
    # Guillemets «»
    if before.count("«") > before.count("»"):
        return True
    # Curly double quotes " "
    if before.count("\u201c") > before.count("\u201d"):
        return True
    # Straight ASCII double quotes " — odd count = inside a pair
    if before.count('"') % 2 == 1:
        return True
    return False


def _has_critical_framing(line: str, pos: int) -> bool:
    """Return True if the match looks like it's being critically discussed."""
    if _in_quotes(line, pos):
        return True
    context = line[:pos].lower()
    # Also check the full line for decolonization callout markers
    line_lower = line.lower()
    return any(m in context for m in CRITICAL_MARKERS) or \
           any(m in line_lower for m in ["decoloniz", "[!decoloniz"])


# ---------------------------------------------------------------------------
# Main check
# ---------------------------------------------------------------------------

def check_imperial_terminology(content: str, file_path: str = "") -> List[Dict]:
    """
    Scan content for Russian/Soviet imperial framing terminology.

    Returns violations in standard audit format:
        {'type', 'severity', 'issue', 'fix', 'line'}
    """
    track = _detect_track(file_path)
    if track in EXEMPT_TRACKS:
        return []

    violations: List[Dict] = []
    lines = content.splitlines()

    def _scan(term_list: List[Dict], always_error: bool) -> None:
        for term_def in term_list:
            rx = re.compile(term_def["pattern"], re.IGNORECASE)
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                # Skip HTML comments and YAML front-matter
                if stripped.startswith("<!--") or stripped.startswith("---"):
                    continue
                for match in rx.finditer(line):
                    if not always_error and _has_critical_framing(line, match.start()):
                        continue  # educational critical usage — fine
                    severity = "error" if always_error else "warning"
                    qualifier = "" if always_error else (
                        " If citing/debunking, wrap in «guillemets» to suppress this warning."
                    )
                    violations.append({
                        "type": "IMPERIAL_TERMINOLOGY",
                        "severity": severity,
                        "issue": (
                            f'Line {line_num}: {"Banned" if always_error else "Suspicious"} '
                            f'imperial term "{term_def["term"]}" — {term_def["reason"]}.{qualifier}'
                        ),
                        "fix": term_def["fix"],
                        "line": line_num,
                    })

    _scan(ALWAYS_BANNED, always_error=True)
    _scan(SUSPICIOUS, always_error=False)

    return violations
