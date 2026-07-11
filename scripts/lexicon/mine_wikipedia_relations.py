#!/usr/bin/env python3
"""Mine curated Ukrainian Wikipedia/Wiktionary relation examples.

Only exact VESUM lemmas with a shared POS survive.  The output is a review
artifact; it is never wired into manifest enrichment by this script.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.relation_candidate_common import (
    DEFAULT_ARTIFACT,
    DEFAULT_VESUM_DB,
    VesumIndex,
    is_single_word,
    load_artifact,
    merge_rows,
    normalize_word,
    summarize_rows,
    write_artifact,
)

WIKIPEDIA_API = "https://uk.wikipedia.org/w/api.php"
WIKTIONARY_API = "https://uk.wiktionary.org/w/api.php"
USER_AGENT = "learn-ukrainian-relation-miner/1.0 (offline candidate extraction; contact repo maintainers)"
ARTICLE_RELATIONS = {
    "Пароніми": "paronym",
    "Синоніми": "synonym",
    "Антоніми": "antonym",
    "Омоніми": "homonym",
}
CATEGORIES = {
    "paronym": "Категорія:Пароніми",
    "homonym": "Категорія:Омоніми",
    "antonym": "Категорія:Антоніми",
    "synonym": "Категорія:Синоніми",
}
WORD_RE = re.compile(r"[А-Яа-яЄєІіЇїҐґ]+(?:['’ʼ-][А-Яа-яЄєІіЇїҐґ]+)*")
WORD_CHAR_CLASS = "A-Za-zА-Яа-яЄєІіЇїҐґ'’ʼ-"
PAIR_RE = re.compile(
    rf"(?<![{WORD_CHAR_CLASS}])(?P<first>{WORD_RE.pattern})(?![{WORD_CHAR_CLASS}])"
    rf"\s*(?:\([^)]*\)|«[^»]*»|\"[^\"]*\")?\s*[—–]\s*"
    rf"(?<![{WORD_CHAR_CLASS}])(?P<second>{WORD_RE.pattern})(?![{WORD_CHAR_CLASS}])"
)
HEADING_RE = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$")
RELATION_HEADING_RE = re.compile(r"(паронім|синонім|антонім|омонім)", re.IGNORECASE)
WIKILINK_RE = re.compile(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]")


def _api_get(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params, doseq=True)
    request = urllib.request.Request(f"{endpoint}?{query}", headers={"User-Agent": USER_AGENT})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310 — fixed Wikimedia endpoints
                payload = json.load(response)
            break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 5:
                raise
            retry_after = int(error.headers.get("Retry-After", "0") or 0)
            time.sleep(min(60, max(retry_after, 2**attempt)))
    else:  # pragma: no cover - loop either breaks or raises
        raise RuntimeError("Wikimedia API retry loop exhausted")
    if "error" in payload:
        raise RuntimeError(f"Wikimedia API error: {payload['error']}")
    return payload


def _clean_wikitext(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*>.*?</ref>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    for _ in range(4):
        new_text = re.sub(r"\{\{[^{}]*\}\}", " ", text)
        if new_text == text:
            break
        text = new_text
    text = re.sub(r"\[\[([^]|]+)\|([^]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^]]+)\]\]", r"\1", text)
    text = re.sub(r"\[https?://[^ ]+\s+([^]]+)\]", r"\1", text)
    text = re.sub(r"'''?([^']+)'''?", r"\1", text)
    cleaned = html.unescape(text).replace("&nbsp;", " ").replace("\u0301", "").replace("\u0300", "")
    return re.sub(r"\s+", " ", cleaned).strip()


def _inside_parentheses(line: str, index: int) -> bool:
    """Treat a leading list label such as ``б)`` as non-structural."""
    if ":" in line:
        context_start = line.index(":") + 1
        prefix = line[context_start:index]
    else:
        prefix = line[:index]
    return prefix.count("(") > prefix.count(")")


def _headword_pairs(text: str) -> list[tuple[str, str, str, str]]:
    """Extract raw adjacent ``word — word`` spans from relation examples."""
    pairs: list[tuple[str, str, str, str]] = []
    lines = text.replace("\r", "").splitlines()
    section = "lead"
    for raw_line in lines:
        heading = HEADING_RE.match(raw_line.strip())
        if heading:
            section = _clean_wikitext(heading.group(2)) or section
            continue
        line = _clean_wikitext(raw_line)
        if not line or line.startswith(("[[Категорія:", "{{")):
            continue
        for match in PAIR_RE.finditer(line):
            if _inside_parentheses(line, match.start()):
                continue
            if re.search(r"не\s+(?:мають|можна\s+вважати|є)\s+антонім", line.casefold()):
                continue
            first, second = normalize_word(match.group("first")), normalize_word(match.group("second"))
            if first != second and second not in {"омографія", "омонімія", "паронімія", "синонімія", "антонімія"}:
                pairs.append((first, second, section, line[:600]))
    return pairs


def _relations_for_pair(default_relation: str, section: str, evidence: str) -> set[str]:
    if section in {"paronym", "synonym", "antonym", "homonym"}:
        return {section}
    relations = {default_relation}
    if default_relation == "paronym":
        lowered = f"{section} {evidence}".casefold()
        if "синонім" in lowered:
            relations.add("synonym")
        if "антонім" in lowered:
            relations.add("antonym")
    return relations


def _source_url(title: str, *, wiki: str = "wikipedia") -> str:
    host = "uk.wiktionary.org" if wiki == "wiktionary" else "uk.wikipedia.org"
    return f"https://{host}/wiki/{urllib.parse.quote(title.replace(' ', '_'), safe="()'" )}"


def _gated_rows(
    raw_pairs: list[tuple[str, str, str, str]],
    *,
    default_relation: str,
    source: str,
    source_url: str,
    article: str,
    vesum: VesumIndex,
    confidence: str,
    category: str | None = None,
) -> tuple[list[dict[str, Any]], set[str]]:
    words = {word for first, second, _section, _evidence in raw_pairs for word in (first, second)}
    exact = vesum.exact_members(words)
    rows: list[dict[str, Any]] = []
    for first, second, section, evidence in raw_pairs:
        if source == "uk.wikipedia" and "російськ" in section.casefold():
            continue
        positions = sorted(exact.get(first, set()) & exact.get(second, set()))
        if not positions:
            continue
        for pos in positions:
            for relation in sorted(_relations_for_pair(default_relation, section, evidence)):
                row: dict[str, Any] = {
                    "relation": relation,
                    "word_a": first,
                    "word_b": second,
                    "pos": pos,
                    "confidence": confidence,
                    "source": source,
                    "source_url": source_url,
                    "article": article,
                    "section": section,
                    "evidence_text": evidence,
                    "gate": {
                        "vesum_exact_lemma": first in exact and second in exact,
                        "same_pos": True,
                    },
                    "license": "CC BY-SA 4.0" if source == "uk.wikipedia" else "CC BY-SA 4.0 / Wiktionary",
                    "attribution": "Українська Вікіпедія" if source == "uk.wikipedia" else "Український Вікісловник",
                }
                if category:
                    row["category"] = category
                gloss = _extract_gloss(first, second, evidence)
                if gloss:
                    row["distinction"] = gloss
                rows.append(row)
    return rows, words


def _extract_gloss(first: str, second: str, evidence: str) -> str | None:
    text = evidence
    first_match = re.search(re.escape(first), text, re.IGNORECASE)
    second_match = re.search(re.escape(second), text, re.IGNORECASE)
    if not first_match or not second_match:
        return None
    remainder = text[first_match.end() : second_match.start()]
    if not remainder.strip(" \t,;:()[]«»\"'—–-"):
        return None
    cleaned = re.sub(r"\s+", " ", remainder).strip(" \t,;:()[]«»\"'—–-")
    return cleaned[:500] if cleaned else None


def fetch_article(title: str) -> str:
    payload = _api_get(
        WIKIPEDIA_API,
        {"action": "parse", "page": title, "prop": "wikitext", "format": "json", "formatversion": "2", "redirects": "1"},
    )
    return str(payload.get("parse", {}).get("wikitext", ""))


def fetch_category_members(category: str) -> list[str]:
    payload = _api_get(
        WIKIPEDIA_API,
        {"action": "query", "list": "categorymembers", "cmtitle": category, "cmlimit": "500", "cmtype": "page|subcat", "format": "json", "formatversion": "2"},
    )
    return [str(item["title"]) for item in payload.get("query", {}).get("categorymembers", []) if item.get("title")]


def fetch_wiktionary_pages(titles: list[str]) -> dict[str, str]:
    pages: dict[str, str] = {}
    for start in range(0, len(titles), 50):
        batch = titles[start : start + 50]
        payload = _api_get(
            WIKTIONARY_API,
            {"action": "query", "prop": "revisions", "titles": "|".join(batch), "rvprop": "content", "rvslots": "main", "format": "json", "formatversion": "2"},
        )
        for page in payload.get("query", {}).get("pages", []):
            revisions = page.get("revisions") or []
            if revisions:
                content = revisions[0].get("slots", {}).get("main", {}).get("content", "")
                pages[str(page.get("title", ""))] = str(content)
    return pages


def _wiktionary_pairs(title: str, text: str) -> list[tuple[str, str, str, str]]:
    pairs: list[tuple[str, str, str, str]] = []
    current: str | None = None
    for raw_line in text.replace("\r", "").splitlines():
        heading = HEADING_RE.match(raw_line.strip())
        if heading:
            found = RELATION_HEADING_RE.search(_clean_wikitext(heading.group(2)))
            relation_by_stem = {
                "паронім": "paronym",
                "синонім": "synonym",
                "антонім": "antonym",
                "омонім": "homonym",
            }
            current = relation_by_stem.get(found.group(1).casefold()) if found else None
            continue
        if not current or not raw_line.lstrip().startswith(("*", "#")):
            continue
        linked = [normalize_word(_clean_wikitext(match.group(1))) for match in WIKILINK_RE.finditer(raw_line)]
        linked = [word for word in linked if is_single_word(word) and word != normalize_word(title)]
        cleaned = _clean_wikitext(raw_line).lstrip("*# ").strip()
        for target in dict.fromkeys(linked):
            pairs.append((normalize_word(title), target, current, cleaned[:600]))
    return pairs


def mine(
    *,
    vesum_db: Path = DEFAULT_VESUM_DB,
    sample_seed: int = 4975,
    wiktionary_limit: int = 100,
    sleep_seconds: float = 1.0,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    vesum = VesumIndex(vesum_db)
    try:
        rows_by_relation: dict[str, list[dict[str, Any]]] = {relation: [] for relation in ("paronyms", "synonyms", "antonyms", "homonyms")}
        category_report: dict[str, list[str]] = {}
        seed_words: set[str] = set()
        for article, default_relation in ARTICLE_RELATIONS.items():
            text = fetch_article(article)
            rows, words = _gated_rows(
                _headword_pairs(text),
                default_relation=default_relation,
                source="uk.wikipedia",
                source_url=_source_url(article),
                article=article,
                vesum=vesum,
                confidence="high",
            )
            seed_words.update(words)
            for row in rows:
                rows_by_relation[row["relation"] + "s"].append(row)
            time.sleep(sleep_seconds)

        category_pages: list[tuple[str, str]] = []
        for default_relation, category in CATEGORIES.items():
            members = fetch_category_members(category)
            category_report[category] = members
            category_pages.extend((default_relation, title) for title in members if not title.startswith("Категорія:"))
            time.sleep(sleep_seconds)
        for default_relation, title in sorted(set(category_pages)):
            text = fetch_article(title)
            rows, _words = _gated_rows(
                _headword_pairs(text),
                default_relation=default_relation,
                source="uk.wikipedia",
                source_url=_source_url(title),
                article=title,
                vesum=vesum,
                confidence="high",
                category=CATEGORIES[default_relation],
            )
            for row in rows:
                rows_by_relation[row["relation"] + "s"].append(row)
            time.sleep(sleep_seconds)

        wiktionary_titles = sorted(seed_words)[:wiktionary_limit]
        wiktionary_rows = 0
        if wiktionary_titles:
            pages = fetch_wiktionary_pages(wiktionary_titles)
            for title, text in sorted(pages.items()):
                rows, _words = _gated_rows(
                    _wiktionary_pairs(title, text),
                    default_relation="paronym",
                    source="uk.wiktionary",
                    source_url=_source_url(title, wiki="wiktionary"),
                    article=title,
                    vesum=vesum,
                    confidence="medium",
                )
                for row in rows:
                    rows_by_relation[row["relation"] + "s"].append(row)
                    wiktionary_rows += 1

        flat = [row for rows in rows_by_relation.values() for row in rows]
        summary: dict[str, Any] = {
            "article_rows": sum(len(rows) for rows in rows_by_relation.values()),
            "wiktionary_rows": wiktionary_rows,
            "category_pages": sum(len(values) for values in category_report.values()),
            "category_report": category_report,
            "wiktionary_pages_checked": len(wiktionary_titles),
            "relation_counts": {relation: len(rows_by_relation[relation]) for relation in rows_by_relation},
            "confidence_distribution": {level: sum(row["confidence"] == level for row in flat) for level in ("high", "medium")},
            **summarize_rows(flat, sample_seed=sample_seed),
        }
        return rows_by_relation, summary
    finally:
        vesum.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--sample-seed", type=int, default=4975)
    parser.add_argument("--wiktionary-limit", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--out", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args()
    rows_by_relation, summary = mine(
        vesum_db=args.vesum_db,
        sample_seed=args.sample_seed,
        wiktionary_limit=args.wiktionary_limit,
        sleep_seconds=args.sleep_seconds,
    )
    payload = load_artifact(args.out)
    added = 0
    for relation, rows in rows_by_relation.items():
        payload["relations"][relation] = [
            row for row in payload["relations"][relation] if row.get("source") not in {"uk.wikipedia", "uk.wiktionary"}
        ]
        added += merge_rows(payload, relation, rows)
    payload.setdefault("metadata", {})["wikipedia_miner"] = {
        "license": "CC BY-SA 4.0",
        "attribution": "Українська Вікіпедія; Український Вікісловник",
        "article_urls": [_source_url(title) for title in ARTICLE_RELATIONS],
        "category_urls": [_source_url(category) for category in CATEGORIES.values()],
        "summary": {key: value for key, value in summary.items() if key != "samples"},
    }
    write_artifact(payload, args.out)
    print(json.dumps({"added": added, **summary}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
