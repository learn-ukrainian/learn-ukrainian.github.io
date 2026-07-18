"""Offline ULIF DictUA envelope → structured lemma artifact (#5230 reduce).

Consumes the durable network-cache raw body shape written by the fetch-only
phase (``fetch_ulif_20k.py`` / ``scripts.lexicon.runner.fetch_ulif_20k``):

```json
{
  "lemma": "<query>",
  "status": "ok" | "not_found" | "parse_error",
  "responses": [
    {"stage": "initial"|"paradigm"|"synonyms"|"antonyms"|"phraseology",
     "status_code": 200, "headers": {...}, "html": "..."}
  ]
}
```

HTML helpers mirror ``scripts.rag.source_query`` DictUA parsers so the reduce
path stays free of the live-query / sources.db import graph (network + offline
workers must not open sources.db).
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

# Structured reduce schema (independent of fetch status stubs).
ULIF_STRUCTURED_SCHEMA_VERSION = "ulif-structured-v1"
# Keep in lockstep with scripts.rag.source_query.ULIF_PARSER_VERSION.
ULIF_PARSER_VERSION = "ulif-dictua-v1"
ULIF_NORMALIZER_VERSION = "ulif-strip-raw-html-v1"
ULIF_SOURCE_ID = "ulif_dictua"
ULIF_OFFICIAL_URL = "https://lcorp.ulif.org.ua/dictua/"

_ULIF_REGISTER_RE = re.compile(
    r"\b(розм\.?|зах\.?|фам\.?|рідше|діал\.?|книжн\.?|заст\.?|жарт\.?|перев\.?)\b",
    re.IGNORECASE,
)
_ULIF_CASE_LABELS = {
    "називний",
    "родовий",
    "давальний",
    "знахідний",
    "орудний",
    "місцевий",
    "кличний",
}
_STAGE_SECTION = {
    "paradigm": "paradigm",
    "synonyms": "synonyms",
    "antonyms": "antonyms",
    "phraseology": "phraseology",
}


def strip_raw_html(obj: Any) -> Any:
    """Drop ``raw_html`` leaves so 20k artifacts stay memory-friendly."""
    if isinstance(obj, dict):
        return {key: strip_raw_html(value) for key, value in obj.items() if key != "raw_html"}
    if isinstance(obj, list):
        return [strip_raw_html(item) for item in obj]
    return obj


def _ulif_text(node: Tag) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def _ulif_register_labels(node: Tag) -> list[str]:
    labels: list[str] = []
    for italic in node.find_all("i"):
        for match in _ULIF_REGISTER_RE.finditer(_ulif_text(italic)):
            label = match.group(1)
            base_label = label.rstrip(".")
            if base_label.casefold() in {
                "розм",
                "зах",
                "фам",
                "діал",
                "книжн",
                "заст",
                "жарт",
                "перев",
            }:
                label = f"{base_label}."
            if label not in labels:
                labels.append(label)
    return labels


def _ulif_parentheticals(node: Tag) -> list[str]:
    return [
        re.sub(r"\s+", " ", value).strip() for value in re.findall(r"\(([^()]*)\)", _ulif_text(node)) if value.strip()
    ]


def _ulif_terms(node: Tag) -> list[dict[str, str]]:
    terms: list[dict[str, str]] = []
    for bold in node.find_all("b"):
        text = _ulif_text(bold)
        if text and any(char.isalpha() for char in text):
            terms.append({"text": text, "raw_html": str(bold)})
    return terms


def parse_ulif_paradigm(html: str) -> dict[str, object] | None:
    """Parse a noun/adjective or verb paradigm table from a DictUA response."""
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        rows: list[list[str]] = []
        for tr in table.find_all("tr", recursive=False):
            cells = tr.find_all(["td", "th"], recursive=False)
            row = [_ulif_text(cell) for cell in cells]
            if row and any(row):
                rows.append(row)
        labels = {cell.casefold() for row in rows for cell in row}
        if labels & _ULIF_CASE_LABELS or "інфінітив" in labels:
            return {"rows": rows, "raw_html": str(table)}
    return None


def parse_ulif_relation_groups(html: str, kind: str) -> list[dict]:
    """Parse ordered DictUA relation groups while retaining their source HTML."""
    soup = BeautifulSoup(html, "html.parser")
    panel = soup.select_one("div.p_cl")
    if panel is None:
        return []

    if kind == "antonyms":
        groups: list[dict] = []
        for table_index, table in enumerate(panel.select("table.tab_ant"), start=1):
            rows: list[dict] = []
            for source_order, tr in enumerate(table.find_all("tr", recursive=False)):
                cells = tr.find_all("td", recursive=False)
                if len(cells) == 2:
                    rows.append(
                        {
                            "source_order": source_order,
                            "kind": "paired_sense",
                            "left": {
                                "text": _ulif_text(cells[0]),
                                "terms": _ulif_terms(cells[0]),
                                "register_labels": _ulif_register_labels(cells[0]),
                                "citations": _ulif_parentheticals(cells[0]),
                                "raw_html": str(cells[0]),
                            },
                            "right": {
                                "text": _ulif_text(cells[1]),
                                "terms": _ulif_terms(cells[1]),
                                "register_labels": _ulif_register_labels(cells[1]),
                                "citations": _ulif_parentheticals(cells[1]),
                                "raw_html": str(cells[1]),
                            },
                        }
                    )
                elif len(cells) == 1:
                    rows.append(
                        {
                            "source_order": source_order,
                            "kind": "relation_note",
                            "text": _ulif_text(cells[0]),
                            "terms": _ulif_terms(cells[0]),
                            "register_labels": _ulif_register_labels(cells[0]),
                            "citations": _ulif_parentheticals(cells[0]),
                            "raw_html": str(cells[0]),
                        }
                    )
            if rows:
                groups.append(
                    {
                        "sense_or_group_id": f"antonyms:{table_index}",
                        "source_order": table_index - 1,
                        "rows": rows,
                        "raw_html": str(table),
                    }
                )
        return groups

    groups = []
    for source_order, paragraph in enumerate(panel.find_all("p", recursive=False)):
        text = _ulif_text(paragraph)
        if not text:
            continue
        groups.append(
            {
                "sense_or_group_id": f"{kind}:{source_order + 1}",
                "source_order": source_order,
                "terms": _ulif_terms(paragraph),
                "register_labels": _ulif_register_labels(paragraph),
                "citations": _ulif_parentheticals(paragraph),
                "text": text,
                "raw_html": str(paragraph),
            }
        )
    return groups


def ulif_headword(html: str, requested_word: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find(id="ContentPlaceHolder1_article")
    if article is not None:
        article_text = _ulif_text(article)
        match = re.match(r"^(.+?)\s+[–—-]\s+", article_text)
        if match:
            return match.group(1).strip()
    input_control = soup.find("input", attrs={"name": "ctl00$ContentPlaceHolder1$tsearch"})
    return str(input_control.get("value", requested_word)).strip() if input_control else requested_word


def ulif_search_result_matches(html: str, requested_word: str) -> bool | None:
    """Return whether DictUA's result list actually contains *requested_word*."""
    soup = BeautifulSoup(html, "html.parser")
    result_list = soup.find(id="ContentPlaceHolder1_dgv")
    if result_list is None:
        return None
    normalized_query = requested_word.replace("\u0301", "").casefold()
    candidates = {_ulif_text(link).replace("\u0301", "").casefold() for link in result_list.find_all("a")}
    return normalized_query in candidates


def _stage_html(responses: list[dict[str, Any]]) -> dict[str, str]:
    by_stage: dict[str, str] = {}
    for item in responses:
        if not isinstance(item, dict):
            continue
        stage = str(item.get("stage") or "").strip()
        html = item.get("html")
        if stage and isinstance(html, str):
            by_stage[stage] = html
    return by_stage


def _safe_status(value: Any) -> str:
    text = str(value or "").strip().casefold()
    if text in {"ok", "not_found", "parse_error"}:
        return text
    return "parse_error"


def parse_dictua_envelope(
    envelope: dict[str, Any],
    *,
    request_key: str | None = None,
    body_sha256: str | None = None,
    include_raw_html: bool = False,
) -> dict[str, Any]:
    """Parse one raw-cache envelope into a structured ULIF lemma artifact."""
    lemma = str(envelope.get("lemma") or "").strip()
    source_status = _safe_status(envelope.get("status"))
    responses = envelope.get("responses") if isinstance(envelope.get("responses"), list) else []
    by_stage = _stage_html([r for r in responses if isinstance(r, dict)])
    stages = [str(r.get("stage") or "") for r in responses if isinstance(r, dict)]

    sections: dict[str, Any] = {}
    canonical_headword = lemma
    status = source_status

    paradigm_html = by_stage.get("paradigm") or by_stage.get("search")
    if paradigm_html:
        match = ulif_search_result_matches(paradigm_html, lemma) if lemma else None
        if match is False:
            status = "not_found"
        elif match is None and source_status == "parse_error":
            status = "parse_error"
        elif match is True or source_status == "ok":
            canonical_headword = ulif_headword(paradigm_html, lemma or "")
            paradigm = parse_ulif_paradigm(paradigm_html)
            if paradigm is not None:
                sections["paradigm"] = paradigm if include_raw_html else strip_raw_html(paradigm)

    for stage, section_name in _STAGE_SECTION.items():
        if section_name == "paradigm":
            continue
        html = by_stage.get(stage)
        if not html:
            continue
        groups = parse_ulif_relation_groups(html, section_name)
        if groups:
            sections[section_name] = groups if include_raw_html else strip_raw_html(groups)

    if status == "ok":
        if "paradigm" not in sections and source_status == "ok" and paradigm_html:
            status = "parse_error"
    elif status == "not_found":
        sections = {}

    # Antonyms-only / partial envelopes with source ok and no paradigm stage keep sections.
    if status == "ok" and not paradigm_html and not sections:
        status = "parse_error"

    return {
        "body_sha256": body_sha256 or "",
        "canonical_headword": canonical_headword,
        "lemma": lemma,
        "lemma_id": lemma,
        "official_url": ULIF_OFFICIAL_URL,
        "parser_version": ULIF_PARSER_VERSION,
        "normalizer_version": ULIF_NORMALIZER_VERSION,
        "request_key": request_key or "",
        "response_count": len(responses),
        "schema_version": ULIF_STRUCTURED_SCHEMA_VERSION,
        "sections": sections,
        "source_id": ULIF_SOURCE_ID,
        "source_status": source_status,
        "stages": stages,
        "status": status,
    }


def candidate_entry_from_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    """Slim Atlas-oriented entry carrying the structured ULIF block only."""
    lemma = str(artifact.get("lemma") or artifact.get("lemma_id") or "")
    return {
        "lemma": lemma,
        "url_slug": lemma,
        "ulif_dictua": {
            "canonical_headword": artifact.get("canonical_headword") or lemma,
            "official_url": artifact.get("official_url") or ULIF_OFFICIAL_URL,
            "parser_version": artifact.get("parser_version") or ULIF_PARSER_VERSION,
            "schema_version": artifact.get("schema_version") or ULIF_STRUCTURED_SCHEMA_VERSION,
            "sections": artifact.get("sections") or {},
            "source_id": artifact.get("source_id") or ULIF_SOURCE_ID,
            "source_status": artifact.get("source_status"),
            "stages": list(artifact.get("stages") or []),
            "status": artifact.get("status") or "parse_error",
        },
    }


def artifact_filename(lemma_id: str) -> str:
    """Filesystem-safe artifact name (keeps Unicode; flattens path separators)."""
    cleaned = re.sub(r"[/\\\\]+", "_", lemma_id.strip())
    return f"{cleaned or 'empty'}.json"


def summarize_artifacts(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate ULIF field coverage for divergence-style reports (no row dumps)."""
    status_counts: dict[str, int] = {}
    section_counts = {
        "paradigm": 0,
        "synonyms": 0,
        "antonyms": 0,
        "phraseology": 0,
    }
    synonym_groups = 0
    antonym_groups = 0
    phraseology_groups = 0
    for art in artifacts:
        status = str(art.get("status") or "parse_error")
        status_counts[status] = status_counts.get(status, 0) + 1
        sections = art.get("sections") if isinstance(art.get("sections"), dict) else {}
        for name in section_counts:
            if name in sections:
                section_counts[name] += 1
        syn = sections.get("synonyms")
        if isinstance(syn, list):
            synonym_groups += len(syn)
        ant = sections.get("antonyms")
        if isinstance(ant, list):
            antonym_groups += len(ant)
        phr = sections.get("phraseology")
        if isinstance(phr, list):
            phraseology_groups += len(phr)
    return {
        "artifact_count": len(artifacts),
        "status_counts": status_counts,
        "section_presence": section_counts,
        "relation_group_totals": {
            "synonyms": synonym_groups,
            "antonyms": antonym_groups,
            "phraseology": phraseology_groups,
        },
    }
