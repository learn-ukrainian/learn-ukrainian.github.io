"""Shared Markdown analysis utilities for research quality scoring.

Used by research_quality.py and enrich_research_gaps.py.
"""

from __future__ import annotations

import re


def extract_section(text: str, header_patterns: list[str]) -> str | None:
    """Extract text under a section header until the next ## header or EOF."""
    for pattern in header_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = match.end()
            next_header = re.search(r"\n##\s", text[start:])
            end = start + next_header.start() if next_header else len(text)
            section = text[start:end].strip()
            return section if section else None
    return None


def count_urls(text: str) -> int:
    """Count unique URLs in text."""
    return len(set(re.findall(r"https?://[^\s\)>]+", text)))


def count_numbered_items(text: str) -> int:
    """Count numbered list items (1. 2. 3. etc.)."""
    return len(re.findall(r"^\s*\d+\.\s+", text, re.MULTILINE))


def count_blockquotes(text: str) -> int:
    """Count blockquote lines (lines starting with >)."""
    return sum(1 for line in text.splitlines() if line.strip().startswith(">"))


def count_guillemet_quotes(text: str) -> int:
    """Count guillemet-style quotes."""
    return len(re.findall(r"«[^»]+»", text))


def count_dated_entries(text: str) -> int:
    """Count list entries with year or century references.

    Matches bullet-point lines containing either:
    - A 3-4 digit year (e.g., 1654, 882)
    - A Roman or Arabic century reference with 'ст.' (e.g., IX ст., 12 ст.)
    """
    year_entries = set(re.findall(
        r"^[\s]*[-*]\s+.*\b\d{3,4}\b.*$",
        text, re.MULTILINE,
    ))
    century_entries = set(re.findall(
        r"^[\s]*[-*]\s+.*(?:[IVXLC]+|[0-9]{1,2})\s*ст\..*$",
        text, re.MULTILINE,
    ))
    return len(year_entries | century_entries)


def count_h3_subsections(text: str) -> int:
    """Count ### sub-headers."""
    return len(re.findall(r"^###\s", text, re.MULTILINE))
