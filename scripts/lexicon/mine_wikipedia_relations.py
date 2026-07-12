#!/usr/bin/env python3
"""Mine curated lexical-relation examples from Ukrainian Wikipedia.

This is a review-only miner.  It reads the four requested language articles,
keeps only explicitly formatted/listed word pairs, and requires both members
to be exact VESUM lemmas.  It never modifies the Atlas manifest.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from itertools import pairwise
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "lexicon" / "cache" / "wikipedia_relation_candidates.json"
WIKIPEDIA_API = "https://uk.wikipedia.org/w/api.php"
USER_AGENT = "learn-ukrainian-relation-miner/1.0 (https://learn-ukrainian.github.io)"
ARTICLE_TITLES = ("Пароніми", "Синоніми", "Антоніми", "Омоніми")

_WORD = r"(?<![А-Яа-яЄєІіЇїҐґ\u0300-\u036f])[А-Яа-яЄєІіЇїҐґ]+(?:['’ʼ-][А-Яа-яЄєІіЇїҐґ]+)*(?![А-Яа-яЄєІіЇїҐґ\u0300-\u036f])"
_WORD_RE = re.compile(rf"(?<![А-Яа-яЄєІіЇїҐґ])({_WORD})(?![А-Яа-яЄєІіЇїҐґ])")
_PAIR_RE = re.compile(
    rf"(?P<a>(?:'{{2,3}})?{_WORD}(?:'{{2,3}})?(?:\s*\([^()\n]{{1,220}}\))?)"
    rf"\s*[—–]\s*"
    rf"(?P<b>(?:'{{2,3}})?{_WORD}(?:'{{2,3}})?(?:\s*\([^()\n]{{1,220}}\))?)"
)
_HOMONYM_COMMA_RE = re.compile(
    rf"(?P<a>(?:'{{2,3}})?{_WORD}(?:'{{2,3}})?(?:\s*\([^()\n]{{1,220}}\))?)"
    rf"\s*,\s*"
    rf"(?P<b>(?:'{{2,3}})?{_WORD}(?:'{{2,3}})?(?:\s*\([^()\n]{{1,220}}\))?)"
)
_FORMATTED_RE = re.compile(r"'{2,3}([^'\n]+?)'{2,3}")
_HEADING_RE = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$")
_RELATION_WORDS = {
    "синонім": "synonym",
    "синоніміч": "synonym",
    "антонім": "antonym",
    "антоніміч": "antonym",
    "омонім": "homonym",
}
_NON_LEXICAL_PAIR_ENDS = {
    "але",
    "в",
    "має",
    "мають",
    "омоніми",
    "слова",
    "слово",
    "це",
}


def normalize_word(value: str) -> str:
    """Normalize a single Ukrainian lemma while retaining apostrophes."""
    value = unicodedata.normalize("NFC", html.unescape(value)).strip().lower()
    decomposed = unicodedata.normalize("NFD", value)
    return unicodedata.normalize("NFC", decomposed.replace("\u0301", "").replace("\u0300", ""))


def _clean_markup(value: str) -> str:
    value = re.sub(r"<!--.*?-->", " ", value, flags=re.DOTALL)
    value = re.sub(r"<ref[^>]*>.*?</ref>", " ", value, flags=re.DOTALL | re.IGNORECASE)
    value = re.sub(r"\{\{[^{}]*\}\}", " ", value)
    value = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", value)
    value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)
    value = re.sub(r"'{2,3}", "", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _term(raw: str) -> tuple[str | None, str | None]:
    raw = raw.strip()
    if "''" in raw:
        formatted_core = raw.split("(", 1)[0].rstrip()
        if not _FORMATTED_RE.fullmatch(formatted_core):
            return None, None
    cleaned = _clean_markup(raw)
    match = _WORD_RE.search(cleaned)
    if not match:
        return None, None
    word = normalize_word(match.group(1))
    if not _WORD_RE.fullmatch(word):
        return None, None
    tail = cleaned[match.end() :].strip()
    gloss_match = re.match(r"\(([^()]*)\)", tail)
    if tail and not gloss_match:
        # Do not turn a phrase such as ``по три — потри`` or
        # ``баранці — має форми`` into a single-word relation.
        return None, None
    gloss = _clean_markup(gloss_match.group(1)).strip(" \t,;:«»\"'") if gloss_match else None
    return word, gloss or None


def _is_curated_line(raw_line: str, section: str) -> bool:
    stripped = raw_line.strip()
    lowered = _clean_markup(raw_line).casefold()
    if stripped.startswith(("*", "#")):
        return True
    if any(cue in lowered for cue in ("наприклад", "приклад", "синонім", "антонім", "омонім")):
        return True
    if any(cue in section.casefold() for cue in ("класифіка", "приклад", "групи", "в українській")):
        return bool(re.search(r"[—–]", raw_line))
    return len(_FORMATTED_RE.findall(raw_line)) >= 2 and bool(re.search(r"[—–]", raw_line))


def _relation(default_relation: str, section: str, evidence: str) -> str:
    context = f"{section} {evidence}".casefold()
    for marker, relation in _RELATION_WORDS.items():
        if marker in context:
            return relation
    return default_relation


def parse_curated_pairs(text: str, *, default_relation: str) -> list[dict[str, str | None]]:
    """Parse explicit relation examples from article wikitext.

    The parser deliberately accepts only list/example lines and formatted
    ``word — word`` or ``word і word`` spans.  It does not infer relations
    from edit distance, definitions, or arbitrary prose.
    """
    rows: list[dict[str, str | None]] = []
    seen: set[tuple[str, str, str, str | None, str | None]] = set()
    section = "lead"
    for raw_line in text.replace("\r", "").splitlines():
        heading = _HEADING_RE.match(raw_line.strip())
        if heading:
            section = _clean_markup(heading.group(2)) or section
            continue
        if not raw_line.strip() or not _is_curated_line(raw_line, section):
            continue
        line_relation = _relation(default_relation, section, raw_line)
        # Wikimedia wikitext commonly spells spaces as ``&nbsp;`` between a
        # term and its dash.  Decode entities before applying the pair regex.
        raw_for_pairs = html.unescape(raw_line)

        matches: list[tuple[str, str, str | None, str | None]] = []
        offset = 0
        while match := _PAIR_RE.search(raw_for_pairs, offset):
            is_listed = raw_line.lstrip().startswith(("*", "#"))
            is_formatted = "''" in match.group("a") or "''" in match.group("b")
            if not is_listed and not is_formatted:
                offset = match.end("a")
                continue
            first, gloss_a = _term(match.group("a"))
            second, gloss_b = _term(match.group("b"))
            if first and second and second not in _NON_LEXICAL_PAIR_ENDS and (first != second or line_relation == "homonym"):
                matches.append((first, second, gloss_a, gloss_b))
            # Keep the left term of the match as the next search anchor so a
            # chain such as ``земний — земельний — земляний`` yields both
            # adjacent pairs without permitting matches inside a word.
            offset = match.end("a")

        formatted = list(_FORMATTED_RE.finditer(raw_for_pairs))
        for left, right in pairwise(formatted):
            separator = _clean_markup(raw_for_pairs[left.end() : right.start()])
            if not re.fullmatch(r"(?:і|й|та|[—–])", separator.strip(" \t,;:")):
                continue
            first, gloss_a = _term(left.group(0))
            second, gloss_b = _term(right.group(0))
            if first and second and second not in _NON_LEXICAL_PAIR_ENDS and (first != second or line_relation == "homonym"):
                matches.append((first, second, gloss_a, gloss_b))

        if line_relation == "homonym":
            for match in _HOMONYM_COMMA_RE.finditer(raw_for_pairs):
                first, gloss_a = _term(match.group("a"))
                second, gloss_b = _term(match.group("b"))
                if first and second and first == second:
                    matches.append((first, second, gloss_a, gloss_b))

        for first, second, gloss_a, gloss_b in matches:
            key = (first, second, line_relation, gloss_a, gloss_b)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "word_a": first,
                    "word_b": second,
                    "relation": line_relation,
                    "gloss_a": gloss_a,
                    "gloss_b": gloss_b,
                    "evidence": _clean_markup(raw_line)[:600],
                }
            )
    return rows


class VesumExactLemmaIndex:
    """Read-only exact ``lemma``/POS index backed by VESUM."""

    def __init__(self, db_path: Path):
        self.connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def exact(self, words: set[str]) -> dict[str, set[str]]:
        if not words:
            return {}
        placeholders = ",".join("?" for _ in words)
        rows = self.connection.execute(
            f"SELECT DISTINCT lemma, pos FROM forms WHERE lemma IN ({placeholders})", tuple(sorted(words))
        ).fetchall()
        result: dict[str, set[str]] = {word: set() for word in words}
        for row in rows:
            result.setdefault(normalize_word(row["lemma"]), set()).add(str(row["pos"]))
        return result


def _api_get(params: dict[str, str]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{WIKIPEDIA_API}?{query}", headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310: fixed Wikimedia URL
                payload = json.load(response)
            if "error" in payload:
                raise RuntimeError(f"Wikimedia API error: {payload['error']}")
            return payload
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 4:
                raise
            retry_after = int(error.headers.get("Retry-After", "0") or 0)
            time.sleep(min(60, max(2**attempt, retry_after)))
    raise RuntimeError("Wikimedia API retry loop exhausted")  # pragma: no cover


def fetch_article(title: str) -> tuple[str, str, str]:
    """Return requested title, canonical title, and raw wikitext."""
    payload = _api_get(
        {
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "redirects": "1",
            "format": "json",
            "formatversion": "2",
        }
    )
    parsed = payload.get("parse") or {}
    canonical = str(parsed.get("title") or title)
    return title, canonical, str(parsed.get("wikitext") or "")


def wikipedia_url(title: str) -> str:
    return f"https://uk.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'), safe="()'")}"


def mine(*, vesum_db: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch and gate the four requested articles."""
    index = VesumExactLemmaIndex(vesum_db)
    rows: list[dict[str, Any]] = []
    report: dict[str, Any] = {"articles": {}, "unreachable_articles": []}
    try:
        for requested_title in ARTICLE_TITLES:
            try:
                _requested, canonical, text = fetch_article(requested_title)
            except Exception as error:
                report["articles"][requested_title] = {"status": "unreachable", "error": f"{type(error).__name__}: {error}"}
                report["unreachable_articles"].append(requested_title)
                continue
            parsed = parse_curated_pairs(text, default_relation=_default_relation(requested_title))
            exact = index.exact({word for pair in parsed for word in (pair["word_a"], pair["word_b"]) if word})
            passed = 0
            for pair in parsed:
                first, second = str(pair["word_a"]), str(pair["word_b"])
                if not exact.get(first) or not exact.get(second):
                    continue
                passed += 1
                row = {
                    "word_a": first,
                    "word_b": second,
                    "relation": pair["relation"],
                    "source_url": wikipedia_url(canonical),
                    "article": canonical,
                    "confidence": "high",
                    "vesum_pos_a": sorted(exact[first]),
                    "vesum_pos_b": sorted(exact[second]),
                }
                if pair.get("gloss_a"):
                    row["gloss_a"] = pair["gloss_a"]
                if pair.get("gloss_b"):
                    row["gloss_b"] = pair["gloss_b"]
                rows.append(row)
            report["articles"][requested_title] = {
                "status": "ok",
                "canonical_title": canonical,
                "parsed_pairs": len(parsed),
                "vesum_passed": passed,
                "source_url": wikipedia_url(canonical),
            }
    finally:
        index.close()
    return rows, report


def _default_relation(title: str) -> str:
    lowered = title.casefold()
    if "парон" in lowered:
        return "paronym"
    if "синон" in lowered:
        return "synonym"
    if "антон" in lowered:
        return "antonym"
    return "homonym"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vesum-db", type=Path, default=ROOT / "data" / "vesum.db")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows, report = mine(vesum_db=args.vesum_db)
    payload = {"schema_version": 1, "relations": rows, "report": report}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"relation_count": len(rows), **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
