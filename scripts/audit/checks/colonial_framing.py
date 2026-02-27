"""
Colonial Framing Check

Detects passages that define Ukrainian by contrast with Russian — treating Russian
as the baseline/default and Ukrainian as the deviation. Ukrainian should be presented
on its own terms.

Severity: warning — flags for review. Some mentions of Russia/Russian are legitimate
(historical resistance, myth-busting in quotes, Kyiv spelling context).

Auto-cleared when the line contains critical context markers (myth-busting,
historical resistance, «guillemets», decolonization callouts).

Track exemptions:
  OES, RUTH, LIT, HIST, ISTORIOHRAFIIA — may contain legitimate comparative linguistics
  or historical content involving Russian colonial rule.
"""

import re
from typing import List, Dict

# Tracks where Russian references appear in historical/comparative context
EXEMPT_TRACKS = {"oes", "ruth", "lit", "hist", "istoriohrafiia", "bio"}

# Patterns that indicate colonial framing (Russian-as-baseline)
COLONIAL_PATTERNS: List[Dict] = [
    {
        "pattern": r"(?i)\bunlike\s+(?:in\s+)?russian\b",
        "label": "Unlike-Russian comparison",
        "fix": "Present the Ukrainian feature on its own terms without Russian as baseline.",
    },
    {
        "pattern": r"(?i)\bdifferent\s+from\s+(?:the\s+)?russian\b",
        "label": "Different-from-Russian framing",
        "fix": "Describe Ukrainian independently — avoid positioning Russian as the default.",
    },
    {
        "pattern": r"(?i)\brussian[,]?\s+(?:for\s+example|for\s+instance)[,]?\s+(?:does\s+not|doesn['\u2019]t|lacks)",
        "label": "Russian-as-negative-example",
        "fix": "State what Ukrainian does, not what Russian lacks.",
    },
    {
        "pattern": r"(?i)\brussian\s+(?:does\s+not|doesn['\u2019]t)\s+(?:use|have)\b",
        "label": "Russian-lacks framing",
        "fix": "Present the Ukrainian feature positively without referencing Russian.",
    },
    {
        "pattern": r"(?i)\bto\s+a\s+western\s+eye\b",
        "label": "Patronizing Western-gaze framing",
        "fix": "Describe the feature directly without invoking a 'Western' perspective.",
    },
    {
        "pattern": r"(?i)\blook\s+(?:more\s+)?like\s+russian\b",
        "label": "Ukrainian-resembling-Russian framing",
        "fix": "Present Ukrainian orthography on its own terms.",
    },
    {
        "pattern": r"(?i)\brussian\s+(?:script|alphabet|letters?)\b",
        "label": "Reference to Russian script as comparison point",
        "fix": "If contrasting letter systems, name specific letters rather than 'Russian script'.",
    },
    {
        "pattern": r"(?i)(?:harder|flatter|harsher)\s+(?:look|sound)\s+of\s+russian",
        "label": "Aesthetic comparison with Russian",
        "fix": "Describe Ukrainian aesthetics positively without disparaging comparison.",
    },
]

# Context markers that indicate legitimate usage (myth-busting, resistance history)
LEGITIMATE_MARKERS = [
    "myth", "міф", "propaganda", "пропаганд",
    "resistance", "опір", "спротив",
    "independence", "незалежн",
    "repressed", "репрес", "banned", "заборон",
    "occupation", "окупац",
    "russification", "русифікац",
    "decoloniz", "деколоніз",
    "so-called", "так зван",
    "imperial", "імпер",
    "transliteration",  # Kyiv/Kiev context
    "[!myth-buster]", "[!culture]",
]


def _detect_track(file_path: str) -> str | None:
    if not file_path:
        return None
    path = str(file_path)
    for track in ["istoriohrafiia", "bio", "hist", "b2-pro", "c1-pro",
                  "oes", "ruth", "lit", "a1", "a2", "b1", "b2", "c1", "c2"]:
        if f"/{track}/" in path:
            return track
    return None


def _is_in_research_or_review(file_path: str) -> bool:
    """Research and review files may legitimately compare languages."""
    path = str(file_path)
    return "/research/" in path or "/review/" in path or "/audit/" in path


def _has_legitimate_context(lines: list, line_idx: int) -> bool:
    """Check if the line or surrounding context has legitimate markers."""
    # Check current line and 2 lines above/below
    start = max(0, line_idx - 2)
    end = min(len(lines), line_idx + 3)
    context = " ".join(lines[start:end]).lower()
    return any(marker in context for marker in LEGITIMATE_MARKERS)


def check_colonial_framing(content: str, file_path: str = "") -> List[Dict]:
    """
    Scan content for colonial framing patterns (Russian-as-baseline).

    Returns violations in standard audit format:
        {'type', 'severity', 'issue', 'fix', 'line'}
    """
    track = _detect_track(file_path)
    if track in EXEMPT_TRACKS:
        return []

    if _is_in_research_or_review(file_path):
        return []

    violations: List[Dict] = []
    lines = content.splitlines()

    for pat_def in COLONIAL_PATTERNS:
        rx = re.compile(pat_def["pattern"])
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip HTML comments and YAML front-matter
            if stripped.startswith("<!--") or stripped.startswith("---"):
                continue
            for match in rx.finditer(line):
                if _has_legitimate_context(lines, line_num - 1):
                    continue
                violations.append({
                    "type": "COLONIAL_FRAMING",
                    "severity": "warning",
                    "issue": (
                        f'Line {line_num}: {pat_def["label"]} — '
                        f'"{match.group()}" positions Russian as baseline.'
                    ),
                    "fix": pat_def["fix"],
                    "line": line_num,
                })

    return violations
