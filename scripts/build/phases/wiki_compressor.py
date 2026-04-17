"""Targeted wiki compression for the V6 contract-first pipeline."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ'][A-Za-zА-Яа-яІіЇїЄєҐґ'’-]{1,}")
_STOPWORDS = {
    "але",
    "або",
    "для",
    "про",
    "при",
    "після",
    "перед",
    "which",
    "that",
    "with",
    "from",
    "this",
    "these",
    "those",
    "what",
    "when",
    "where",
    "into",
    "та",
    "що",
    "як",
    "вже",
    "саме",
    "тому",
    "буде",
    "also",
    "their",
    "there",
    "вона",
    "вони",
    "його",
    "your",
    "must",
    "have",
    "has",
}


def _tokenize(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    text = re.sub(r"[-_/.:]+", " ", text)
    return {
        token.lower()
        for token in _TOKEN_RE.findall(text)
        if len(token) > 2 and token.lower() not in _STOPWORDS
    }


def _clean_inline_markup(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_wiki_articles(wiki_packet: str) -> list[dict]:
    """Parse knowledge-packet wiki articles into article blocks."""
    if not wiki_packet:
        return []

    matches = list(re.finditer(r"^### Вікі:\s+(.+)$", wiki_packet, re.MULTILINE))
    articles: list[dict] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(wiki_packet)
        path = match.group(1).strip()
        body = wiki_packet[start:end].strip()
        if not body:
            continue
        articles.append({
            "path": path,
            "blocks": _split_article_blocks(path, body),
        })
    return articles


def _split_article_blocks(path: str, body: str) -> list[dict]:
    lines = body.splitlines()
    blocks: list[dict] = []
    heading = "Overview"
    chunk: list[str] = []

    def flush() -> None:
        text = "\n".join(chunk).strip()
        if not text:
            return
        blocks.append({
            "path": path,
            "heading": heading,
            "citation": f"{path} :: {heading}",
            "text": text,
            "tokens": _tokenize(f"{path}\n{heading}\n{text}"),
        })

    for line in lines:
        if re.match(r"^###+?\s+", line):
            flush()
            heading = re.sub(r"^###+\s+", "", line).strip() or "Overview"
            chunk = []
            continue
        chunk.append(line)
    flush()

    if not blocks:
        cleaned = body.strip()
        return [{
            "path": path,
            "heading": "Overview",
            "citation": f"{path} :: Overview",
            "text": cleaned,
            "tokens": _tokenize(cleaned),
        }]
    return blocks


def _score_block(block: dict, query_tokens: set[str]) -> tuple[int, list[str]]:
    overlap = sorted(query_tokens & block["tokens"])
    if not overlap:
        return 0, []
    heading_bonus = 2 if any(token in _tokenize(block["heading"]) for token in overlap) else 0
    return len(overlap) + heading_bonus, overlap[:6]


def _trim_excerpt(text: str, *, max_chars: int = 520) -> str:
    cleaned = _clean_inline_markup(text)
    if len(cleaned) <= max_chars:
        return cleaned
    trimmed = cleaned[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{trimmed}..."


def _anchor_claim(excerpt: str) -> str:
    """Return the first sentence of an excerpt for scenario anchoring.

    Uses :func:`linguistics.tokenize_uk.tokenize_sents` (#1318) so
    Ukrainian abbreviations (р., ст., тис., м., вул., …) don't create
    false sentence boundaries — the old regex ``(?<=[.!?])\\s+`` broke
    ``1953 р. почалась...`` into two anchors.
    """
    # Import lazily: this module is imported during pipeline startup
    # and we want to avoid pulling scripts/linguistics/ onto every
    # Python startup path just for one call.
    from linguistics.tokenize_uk import tokenize_sents

    parts = tokenize_sents(excerpt)
    return parts[0].strip() if parts else excerpt.strip()


def compress_wiki_packet(
    plan: dict,
    wiki_packet: str,
    *,
    items_per_section: int = 2,
) -> dict:
    """Map wiki facts to plan sections and extract prompt-sized excerpts."""
    sections = plan.get("content_outline") or []
    articles = _parse_wiki_articles(wiki_packet)
    result = {
        "section_excerpts": {},
        "anchors_by_section": defaultdict(list),
        "factual_anchors": [],
    }

    if not sections or not articles:
        return result

    all_blocks = [block for article in articles for block in article["blocks"]]
    situation_text = " ".join(
        " ".join(
            [
                str(item.get("setting", "")),
                str(item.get("motivation", "")),
                " ".join(str(s) for s in (item.get("speakers") or [])),
            ]
        )
        for item in (plan.get("dialogue_situations") or [])
    )
    dialogue_keywords = {"dialogues", "dialogue", "діалоги", "діалог", "service", "exchange"}
    for section in sections:
        name = str(section.get("section", "")).strip()
        if not name:
            continue
        query_parts = (
            [name]
            + [str(point) for point in (section.get("points") or [])[:5]]
        )
        section_tokens = _tokenize(" ".join(query_parts))
        if section_tokens & dialogue_keywords and situation_text:
            query_parts.append(situation_text)
        query = " ".join(query_parts)
        query_tokens = _tokenize(query)
        ranked: list[tuple[int, list[str], dict]] = []
        for block in all_blocks:
            score, overlap = _score_block(block, query_tokens)
            if score > 0:
                ranked.append((score, overlap, block))
        ranked.sort(key=lambda item: (-item[0], item[2]["citation"]))

        seen_citations: set[str] = set()
        section_items: list[dict] = []
        for score, overlap, block in ranked:
            citation = block["citation"]
            if citation in seen_citations:
                continue
            seen_citations.add(citation)
            excerpt = _trim_excerpt(block["text"])
            item = {
                "citation": citation,
                "source_path": block["path"],
                "source_heading": block["heading"],
                "matched_terms": overlap,
                "score": score,
                "excerpt": excerpt,
            }
            section_items.append(item)
            anchor = {
                "section": name,
                "claim": _anchor_claim(excerpt),
                "citation": citation,
                "matched_terms": overlap[:4],
            }
            result["anchors_by_section"][name].append(anchor)
            result["factual_anchors"].append(anchor)
            if len(section_items) >= items_per_section:
                break

        result["section_excerpts"][name] = section_items

    result["anchors_by_section"] = dict(result["anchors_by_section"])
    return result
