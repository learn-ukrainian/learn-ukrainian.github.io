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

# Split article bodies on any level-2-or-deeper markdown heading.
# Pedagogy wiki articles under `wiki/pedagogy/**` use `## Section` as their
# primary structure (Методичний підхід, Послідовність введення, Приклади з
# підручників, …). The previous `###+` pattern missed these H2s and collapsed
# each article into one ~13KB "Overview" block — the trim-to-520-chars step
# then only surfaced the generic pedagogical intro, never the concrete
# dialogue/example sections a writer actually needs (see #1282).
_HEADING_RE = re.compile(r"^##+\s+")

# Section-name cues that indicate dialogue/role-play content. Used to append
# the full scenario situation text to a dialogue section's ranking query
# (stronger signal than the general scenario-token bonus).
_DIALOGUE_SECTION_KEYWORDS = {
    "dialogues",
    "dialogue",
    "діалоги",
    "діалог",
    "service",
    "exchange",
    "розмова",
    "розмови",
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
        if _HEADING_RE.match(line):
            flush()
            heading = re.sub(r"^##+\s+", "", line).strip() or "Overview"
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


def _build_scenario_tokens(plan: dict) -> set[str]:
    """Return the set of scenario-context tokens derived from the plan.

    Combines plan-level identity fields (``title``, ``subtitle``,
    ``objectives``) with the full dialogue-situation context. The result is
    used as a module-wide "what is this module actually about" signal so
    ranking can promote blocks that describe the real scenario — not just
    the per-section query tokens (#1282).
    """
    parts: list[str] = [
        str(plan.get("title") or ""),
        str(plan.get("subtitle") or ""),
    ]
    parts.extend(str(item) for item in (plan.get("objectives") or []))
    for situation in (plan.get("dialogue_situations") or []):
        parts.append(str(situation.get("setting", "")))
        parts.append(str(situation.get("motivation", "")))
        parts.extend(str(s) for s in (situation.get("speakers") or []))
    return _tokenize(" ".join(parts))


def _scenario_article_bonus(block_path: str, plan: dict) -> int:
    """Return a bonus for blocks whose article path matches the plan slug.

    Plans like ``at-the-cafe`` typically ship alongside a wiki article at
    ``wiki/pedagogy/a1/at-the-cafe.md``. When that article is present in the
    knowledge packet, its path contains the slug verbatim and we promote its
    blocks so scenario-specific material outranks token-dense generic
    articles (e.g. ``i-eat-i-drink.md`` matching cafe dialogues on shared
    vocabulary like "їсти" / "пити") — the core #1282 problem.

    Deliberately conservative: only a slug-substring match fires. We do not
    score path-token overlap against arbitrary plan text, because that would
    re-introduce the generic-wins-on-coincidence failure mode.
    """
    slug = str(plan.get("slug") or "").strip().lower()
    if not slug or len(slug) < 3:
        return 0
    return 3 if slug in block_path.lower() else 0


def compress_wiki_packet(
    plan: dict,
    wiki_packet: str,
    *,
    items_per_section: int = 2,
    trace_size: int = 5,
) -> dict:
    """Map wiki facts to plan sections and extract prompt-sized excerpts.

    Returns a dict with:
      - ``section_excerpts``: picked top-``items_per_section`` excerpts per
        section (fed into writer prompts).
      - ``anchors_by_section`` / ``factual_anchors``: first-sentence anchors
        used by the contract.
      - ``selection_trace``: deterministic top-``trace_size`` candidate list
        per section with full score breakdowns (query / scenario / article
        bonuses and matched terms). Saved in ``wiki-excerpts.yaml`` for
        inspectability (#1282 AC-3) without entering the writer prompt.
    """
    sections = plan.get("content_outline") or []
    articles = _parse_wiki_articles(wiki_packet)
    result = {
        "section_excerpts": {},
        "anchors_by_section": defaultdict(list),
        "factual_anchors": [],
        "selection_trace": {},
    }

    if not sections or not articles:
        return result

    all_blocks = [block for article in articles for block in article["blocks"]]
    scenario_tokens = _build_scenario_tokens(plan)
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

    for section in sections:
        name = str(section.get("section", "")).strip()
        if not name:
            continue
        query_parts = (
            [name]
            + [str(point) for point in (section.get("points") or [])[:5]]
        )
        section_tokens = _tokenize(" ".join(query_parts))
        if section_tokens & _DIALOGUE_SECTION_KEYWORDS and situation_text:
            query_parts.append(situation_text)
        query_tokens = _tokenize(" ".join(query_parts))

        ranked: list[dict] = []
        for block in all_blocks:
            query_score, overlap = _score_block(block, query_tokens)
            # Require at least one per-section query-token overlap before
            # the scenario/article bonuses apply. Without this floor, a
            # scenario-article block with zero section-relevance would beat
            # a moderately-relevant generic block in a multi-section module
            # (e.g. a grammar section inside a scenario module), starving
            # the writer of actually-relevant generic context.
            if query_score == 0:
                continue
            scenario_overlap = sorted(scenario_tokens & block["tokens"])
            # Cap the scenario bonus so it enriches without dominating
            # a well-matched per-section query on short sections.
            scenario_score = min(len(scenario_overlap), 4)
            article_score = _scenario_article_bonus(block["path"], plan)
            total = query_score + scenario_score + article_score
            ranked.append({
                "block": block,
                "total": total,
                "query_score": query_score,
                "scenario_score": scenario_score,
                "article_score": article_score,
                "matched_terms": overlap,
                "scenario_terms": scenario_overlap[:6],
            })
        ranked.sort(key=lambda entry: (-entry["total"], entry["block"]["citation"]))

        seen_citations: set[str] = set()
        section_items: list[dict] = []
        trace_entries: list[dict] = []
        for entry in ranked:
            block = entry["block"]
            citation = block["citation"]
            if citation in seen_citations:
                continue
            seen_citations.add(citation)
            breakdown = {
                "query": entry["query_score"],
                "scenario": entry["scenario_score"],
                "article": entry["article_score"],
            }
            trace_entry = {
                "citation": citation,
                "source_path": block["path"],
                "source_heading": block["heading"],
                "score": entry["total"],
                "score_breakdown": breakdown,
                "matched_terms": entry["matched_terms"],
                "scenario_terms": entry["scenario_terms"],
            }
            trace_entries.append(trace_entry)
            if len(section_items) < items_per_section:
                excerpt = _trim_excerpt(block["text"])
                item = dict(trace_entry, excerpt=excerpt)
                section_items.append(item)
                anchor = {
                    "section": name,
                    "claim": _anchor_claim(excerpt),
                    "citation": citation,
                    "matched_terms": entry["matched_terms"][:4],
                }
                result["anchors_by_section"][name].append(anchor)
                result["factual_anchors"].append(anchor)
            if len(trace_entries) >= trace_size and len(section_items) >= items_per_section:
                break

        result["section_excerpts"][name] = section_items
        result["selection_trace"][name] = trace_entries

    result["anchors_by_section"] = dict(result["anchors_by_section"])
    return result
