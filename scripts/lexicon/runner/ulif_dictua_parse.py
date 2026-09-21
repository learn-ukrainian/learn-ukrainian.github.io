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

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup, Tag

from scripts.verification.stress import pedagogical_stressed_form

# Structured reduce schema (independent of fetch status stubs).
ULIF_STRUCTURED_SCHEMA_VERSION = "ulif-structured-v1"
# Keep in lockstep with scripts.rag.source_query.ULIF_PARSER_VERSION.
ULIF_PARSER_VERSION = "ulif-dictua-v2"
ULIF_FORMS_PARSER_VERSION = "ulif-forms-v1"
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

    if status == "not_found":
        sections = {}

    # A successful fetch can legitimately have no paradigm when at least one
    # relation section was parsed.  A content-empty envelope remains unusable
    # evidence and must fail closed even if its source status says ``ok``.
    if status == "ok" and not sections:
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


# ── Homonym identity + hierarchical paradigm forms (#8400) ─────────

_ACUTE = "\u0301"
_SELECT_RE = re.compile(r"Select\$(\d+)")
# Fixture paradigm cells attest only ``на/у``. Also accept the locative
# prepositions named for this parser. Longer alternatives come first so
# ``на/у`` is not consumed as ``на``.
_PREPOSITION_RE = re.compile(r"^(на/у|у/в|в/у|на|по|в|у)\s+")
_LEADING_DASH_RE = re.compile(r"^[–—-]\s*")
_NUMBER_TAGS = frozenset({"s", "p"})
_PERSON_TAGS = frozenset({"1", "2", "3"})
_INVARIABLE_PHRASE = "незмінювана словникова одиниця"
_SECTION_ROLES = frozenset({"mood", "tense", "verbform"})
_HEADER_ROLES = frozenset({"axis", "number", "gender"})
_ROW_ROLES = frozenset({"case", "person", "gender", "verbform"})


@dataclass(frozen=True, slots=True)
class LabelMapping:
    """One ULIF header or grammar line and the VESUM tag fragments it licenses.

    ``tags`` is empty only for labels that are real ULIF axes but are not
    morphological features (``відмінок``). An absent mapping is not the same
    thing: unknown labels stay raw and are flagged.
    """

    tags: tuple[str, ...]
    role: str


# Keys are casefolded ULIF labels. Values are VESUM tag fragments attested
# in ``forms_all.tags`` (``v_naz``, ``impr``, ``advp``, …). Do not add a tag
# that VESUM does not use.
ULIF_LABEL_TAGS: dict[str, LabelMapping] = {
    "називний": LabelMapping(("v_naz",), "case"),
    "родовий": LabelMapping(("v_rod",), "case"),
    "давальний": LabelMapping(("v_dav",), "case"),
    "знахідний": LabelMapping(("v_zna",), "case"),
    "орудний": LabelMapping(("v_oru",), "case"),
    "місцевий": LabelMapping(("v_mis",), "case"),
    "кличний": LabelMapping(("v_kly",), "case"),
    "однина": LabelMapping(("s",), "number"),
    "множина": LabelMapping(("p",), "number"),
    "чол. р.": LabelMapping(("m",), "gender"),
    "жін. р.": LabelMapping(("f",), "gender"),
    "сер. р.": LabelMapping(("n",), "gender"),
    "1 особа": LabelMapping(("1",), "person"),
    "2 особа": LabelMapping(("2",), "person"),
    "3 особа": LabelMapping(("3",), "person"),
    "інфінітив": LabelMapping(("inf",), "verbform"),
    "наказовий спосіб": LabelMapping(("impr",), "mood"),
    "майбутній час": LabelMapping(("futr",), "tense"),
    "теперішній час": LabelMapping(("pres",), "tense"),
    "минулий час": LabelMapping(("past",), "tense"),
    "активний дієприкметник": LabelMapping(("adjp", "actv"), "verbform"),
    "пасивний дієприкметник": LabelMapping(("adjp", "pasv"), "verbform"),
    "дієприслівник": LabelMapping(("advp",), "verbform"),
    "безособова форма": LabelMapping(("impers",), "verbform"),
    "відмінок": LabelMapping((), "axis"),
    "іменник чоловічого роду": LabelMapping(("noun", "m"), "grammar"),
    "іменник жіночого роду": LabelMapping(("noun", "f"), "grammar"),
    "іменник середнього роду": LabelMapping(("noun", "n"), "grammar"),
    "прикметник": LabelMapping(("adj",), "grammar"),
    "прислівник": LabelMapping(("adv",), "grammar"),
    "дієслово недоконаного виду": LabelMapping(("verb", "imperf"), "grammar"),
    "дієслово доконаного виду": LabelMapping(("verb", "perf"), "grammar"),
}


def normalize_ulif_label(text: str) -> str:
    """Casefold a ULIF label and collapse its whitespace."""
    return re.sub(r"\s+", " ", text).strip().casefold()


def lookup_ulif_label(text: str) -> LabelMapping | None:
    """Return the mapping for *text*, or ``None`` when ULIF's label is unknown."""
    return ULIF_LABEL_TAGS.get(normalize_ulif_label(text))


def strip_ulif_stress(text: str) -> str:
    """Drop combining acutes. Leave every other character, including case, in place."""
    return text.replace(_ACUTE, "")


def normalize_ulif_spelling(text: str) -> str:
    """Spelling key shared with ``normalize_ulif_dictua_query``: casefold, no stress."""
    return " ".join(strip_ulif_stress(text).split()).casefold()


def ulif_entry_key(normalized_spelling: str, homonym_index: int) -> str:
    """Stable key ``(normalized_spelling, homonym_index)`` rendered as text."""
    if homonym_index < 1:
        raise ValueError(f"homonym_index must be 1-based, got {homonym_index}")
    return f"{normalized_spelling}#{homonym_index}"


def _stress_record(stressed: str) -> dict[str, Any]:
    """Keep ULIF's acute exactly, and derive the unstressed form and indexes."""
    unstressed_chars: list[str] = []
    indices: list[int] = []
    for char in stressed:
        if char == _ACUTE:
            if unstressed_chars:
                indices.append(len(unstressed_chars) - 1)
            continue
        unstressed_chars.append(char)
    unstressed = "".join(unstressed_chars)
    match = {
        "stressed_form": stressed,
        "unstressed_form": unstressed,
        "vowel_indices": indices,
        "override_applied": False,
    }
    return {
        "form_unstressed": unstressed,
        "form_stressed": stressed,
        "stress_vowel_indices": indices,
        "dual_stress_flag": len(indices) > 1,
        "pedagogical_stressed_form": pedagogical_stressed_form(match),
    }


def _split_cell_surface(text: str) -> list[dict[str, Any]]:
    """Split one paradigm cell into variant rows.

    A leading ``на/у``, ``у/в``, ``в/у``, ``на``, ``в``, ``у``, or ``по``
    and a trailing ``*`` are fields, not part of the form. Commas separate
    variants.
    """
    surface = re.sub(r"\s+", " ", text).strip()
    preposition = ""
    prefix = _PREPOSITION_RE.match(surface)
    if prefix:
        preposition = prefix.group(1)
        surface = surface[prefix.end() :]
    pieces = [piece.strip() for piece in surface.split(",")]
    rows: list[dict[str, Any]] = []
    for order, piece in enumerate((piece for piece in pieces if piece), start=1):
        marked = piece.endswith("*")
        form = piece[:-1].strip() if marked else piece
        if not form:
            continue
        rows.append(
            {
                "variant_order": order,
                "preposition": preposition,
                "marked_asterisk": marked,
                **_stress_record(form),
            }
        )
    return rows


@dataclass(slots=True)
class _GridCell:
    text: str
    rowspan: int
    colspan: int
    origin_row: int
    origin_col: int


def _cell_text(cell: Tag) -> str:
    text = cell.get_text(" ", strip=True).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _expand_table(table: Tag) -> list[list[_GridCell | None]]:
    """Place each ``td``/``th`` on a grid, repeating a cell across its span."""
    occupied: dict[tuple[int, int], _GridCell] = {}
    width = 0
    raw_rows: list[list[_GridCell | None]] = []
    for row_index, tr in enumerate(table.find_all("tr", recursive=False)):
        col = 0
        for td in tr.find_all(["td", "th"], recursive=False):
            while (row_index, col) in occupied:
                col += 1
            rowspan = int(td.get("rowspan") or 1)
            colspan = int(td.get("colspan") or 1)
            cell = _GridCell(
                text=_cell_text(td),
                rowspan=rowspan,
                colspan=colspan,
                origin_row=row_index,
                origin_col=col,
            )
            for d_row in range(rowspan):
                for d_col in range(colspan):
                    occupied[(row_index + d_row, col + d_col)] = cell
            col += colspan
            width = max(width, col)
        raw_rows.append([])
    grid: list[list[_GridCell | None]] = []
    for row_index in range(len(raw_rows)):
        grid.append([occupied.get((row_index, col)) for col in range(width)])
    return grid


def _origin_cells(row: list[_GridCell | None], row_index: int) -> list[tuple[int, _GridCell]]:
    seen: set[int] = set()
    placed: list[tuple[int, _GridCell]] = []
    for col, cell in enumerate(row):
        if cell is None or cell.origin_row != row_index or id(cell) in seen:
            continue
        seen.add(id(cell))
        placed.append((col, cell))
    return placed


def _is_column_header_row(cells: list[tuple[int, _GridCell]]) -> bool:
    texts = [cell.text for _col, cell in cells if cell.text]
    if not texts:
        return False
    mappings = [lookup_ulif_label(text) for text in texts]
    if any(mapping is None or mapping.role not in _HEADER_ROLES for mapping in mappings):
        return False
    return any(mapping is not None and mapping.role in {"number", "gender", "axis"} for mapping in mappings)


def _section_label(cells: list[tuple[int, _GridCell]], width: int) -> str | None:
    texts = [cell.text for _col, cell in cells if cell.text]
    distinct = list(dict.fromkeys(texts))
    if len(distinct) != 1:
        return None
    text = distinct[0]
    if _ACUTE in text or text.endswith("*"):
        return None
    mapping = lookup_ulif_label(text)
    if mapping is not None and mapping.role in _SECTION_ROLES:
        return text
    spans_all = len(cells) == 1 and cells[0][1].colspan >= width and width > 0
    if spans_all and (mapping is None or mapping.role in _SECTION_ROLES):
        return text
    return None


def _map_label(text: str) -> tuple[list[str], list[str]]:
    mapping = lookup_ulif_label(text)
    if mapping is None:
        return [], [text]
    return list(mapping.tags), []


def canonical_grammatical_tags(tags: list[str]) -> list[str]:
    """Place number immediately before person, matching VESUM ``futr:s:1``.

    Tags that are neither number nor person stay in source order. When no
    person tag is present, number stays where the paradigm table put it
    (``past`` + gender + number is left as ``past:m:s``).
    """
    if not any(tag in _NUMBER_TAGS for tag in tags) or not any(tag in _PERSON_TAGS for tag in tags):
        return list(tags)
    ordered: list[str] = []
    placed = False
    for tag in tags:
        if tag in _NUMBER_TAGS or tag in _PERSON_TAGS:
            if not placed:
                ordered.extend(tag for tag in tags if tag in _NUMBER_TAGS)
                ordered.extend(tag for tag in tags if tag in _PERSON_TAGS)
                placed = True
            continue
        ordered.append(tag)
    return ordered


def _grammar_tags(grammatical_label: str) -> tuple[list[str], list[str]]:
    """Map a whole grammar line. Unknown lines stay raw; no tag is guessed."""
    cleaned = normalize_ulif_label(grammatical_label)
    if not cleaned:
        return [], []
    mapping = ULIF_LABEL_TAGS.get(cleaned)
    if mapping is None or mapping.role != "grammar":
        return [], [cleaned]
    return list(mapping.tags), []


def _find_paradigm_table(article: Tag) -> Tag | None:
    known = set(ULIF_LABEL_TAGS)
    for table in article.find_all("table"):
        if table.find("table") is not None:
            continue
        labels = {normalize_ulif_label(_cell_text(cell)) for cell in table.find_all(["td", "th"])}
        if labels & known:
            return table
    return None


def _direct_text(node: Tag) -> str:
    parts = [str(child) for child in node.children if isinstance(child, str)]
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def parse_register_list(html: str) -> list[dict[str, Any]]:
    """Read DictUA's register rows in list order.

    Each row's visible link text is the stressed headword. Rows are distinct by
    their ``Select$N`` postback target, not by display text: the register can
    list two senses with identical stress and capitalisation. There is no
    homonym number column on the list itself.
    """
    soup = BeautifulSoup(html, "html.parser")
    grid = soup.find(id="ContentPlaceHolder1_dgv")
    if grid is None:
        return []
    rows: list[dict[str, Any]] = []
    for link in grid.find_all("a"):
        href = str(link.get("href") or "")
        match = _SELECT_RE.search(href)
        if match is None:
            continue
        stressed = _ulif_text(link)
        row_index = int(match.group(1))
        rows.append(
            {
                "row_index": row_index,
                "select": f"Select${row_index}",
                "stressed": stressed,
                "unstressed": strip_ulif_stress(stressed),
            }
        )
    return rows


def homonym_group(rows: list[dict[str, Any]], spelling: str) -> list[dict[str, Any]]:
    """1-based homonym indexes for rows whose unstressed form equals *spelling*."""
    target = normalize_ulif_spelling(spelling)
    matched = [row for row in rows if normalize_ulif_spelling(row["unstressed"]) == target]
    group: list[dict[str, Any]] = []
    for index, row in enumerate(matched, start=1):
        group.append({**row, "homonym_index": index, "normalized_spelling": target})
    return group


_PRINTED_HOMONYM_TRAILING_RE = re.compile(r"^(.*?)\s+(\d+)\s*$")
_PRINTED_HOMONYM_LABEL_RE = re.compile(
    r"(?:омонім\w*|homonym)\s*[№#]?\s*(\d+)|№\s*(\d+)",
    re.IGNORECASE,
)


def _split_printed_homonym(headword: str) -> tuple[str, str | None]:
    """Strip a trailing printed homonym digit from a ``word_style`` headword."""
    match = _PRINTED_HOMONYM_TRAILING_RE.match(headword)
    if match is None:
        return headword, None
    return match.group(1), match.group(2)


def printed_homonym_number(html: str) -> str | None:
    """Return ULIF's own homonym number when the entry header prints one.

    DictUA often appends the digit to ``word_style`` (``Іши́м 1``). Sense glosses
    such as ``(будівля)`` are not numbers. ``None`` means the page does not
    print one.
    """
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find(id="ContentPlaceHolder1_article")
    if article is None:
        return None
    word_node = article.select_one(".word_style")
    if word_node is not None:
        _, printed = _split_printed_homonym(_direct_text(word_node))
        if printed is not None:
            return printed
    chunks: list[str] = []
    for selector in (".word_style", ".gram_style", ".comment_style"):
        for node in article.select(selector):
            chunks.append(_ulif_text(node))
    header = " ".join(chunks)
    match = _PRINTED_HOMONYM_LABEL_RE.search(header)
    if match is None:
        return None
    return next(group for group in match.groups() if group)


def _article_identity(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find(id="ContentPlaceHolder1_article")
    if article is None:
        return {
            "canonical_headword": "",
            "grammatical_label": "",
            "sense_gloss": "",
            "invariable_phrase": False,
            "paradigm_table": None,
            "content_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
            "printed_homonym_number": None,
        }
    word_node = article.select_one(".word_style")
    gram_node = article.select_one(".gram_style")
    raw_headword = _direct_text(word_node) if word_node is not None else ""
    headword, printed = _split_printed_homonym(raw_headword)
    if printed is None:
        printed = printed_homonym_number(html)
    grammar = _LEADING_DASH_RE.sub("", _ulif_text(gram_node)).strip() if gram_node is not None else ""
    notes = []
    for node in article.select(".comment_style"):
        note = _ulif_text(node)
        if note:
            notes.append(note)
    article_text = _ulif_text(article)
    return {
        "canonical_headword": headword,
        "grammatical_label": grammar,
        "sense_gloss": " ".join(notes).strip(),
        "invariable_phrase": _INVARIABLE_PHRASE in article_text,
        "paradigm_table": _find_paradigm_table(article),
        "content_sha256": hashlib.sha256(str(article).encode("utf-8")).hexdigest(),
        "printed_homonym_number": printed,
    }


def _form_row(
    *,
    entry_key: str,
    surface: dict[str, Any],
    grammatical_tags: list[str],
    unmapped_labels: list[str],
    is_lemma: bool,
    is_invariable: bool,
) -> dict[str, Any]:
    return {
        "entry_key": entry_key,
        "form_unstressed": surface["form_unstressed"],
        "form_stressed": surface["form_stressed"],
        "stress_vowel_indices": list(surface["stress_vowel_indices"]),
        "grammatical_tags": canonical_grammatical_tags(grammatical_tags),
        "unmapped_labels": list(unmapped_labels),
        "variant_order": surface["variant_order"],
        "preposition": surface["preposition"],
        "marked_asterisk": surface["marked_asterisk"],
        "is_lemma": is_lemma,
        "is_invariable": is_invariable,
        "dual_stress_flag": surface["dual_stress_flag"],
        "pedagogical_stressed_form": surface["pedagogical_stressed_form"],
    }


def _paradigm_form_rows(table: Tag, entry_key: str) -> list[dict[str, Any]]:
    grid = _expand_table(table)
    if not grid:
        return []
    width = len(grid[0])
    column_headers: dict[int, list[str]] = {}
    stacking = False
    # A tense or mood banner is the parent. A participle line under it is a
    # subsection and must not erase that parent (``гово́рячи`` stays present).
    parent_section = ""
    verbform_section = ""
    forms: list[dict[str, Any]] = []
    for row_index, row in enumerate(grid):
        origins = _origin_cells(row, row_index)
        if not origins:
            continue
        if _is_column_header_row(origins):
            if not stacking:
                column_headers = {}
                stacking = True
            for col, cell in origins:
                if not cell.text or normalize_ulif_label(cell.text) == "відмінок":
                    continue
                for offset in range(cell.colspan):
                    column_headers.setdefault(col + offset, []).append(cell.text)
            continue
        stacking = False
        section_text = _section_label(origins, width)
        if section_text is not None:
            mapping = lookup_ulif_label(section_text)
            role = mapping.role if mapping is not None else ""
            if role == "verbform":
                verbform_section = section_text
            else:
                parent_section = section_text
                verbform_section = ""
            continue
        label = ""
        form_cells = origins
        first_text = origins[0][1].text
        first_mapping = lookup_ulif_label(first_text) if first_text else None
        if (
            first_text
            and _ACUTE not in first_text
            and (
                (first_mapping is not None and first_mapping.role in _ROW_ROLES)
                or len(origins) > 1
            )
        ):
            label = first_text
            form_cells = origins[1:]
        for col, cell in form_cells:
            if not cell.text:
                continue
            header_texts = column_headers.get(col, [])
            header_tags: list[str] = []
            unmapped: list[str] = []
            for header in header_texts:
                mapping = lookup_ulif_label(header)
                if mapping is None:
                    unmapped.append(header)
                    continue
                header_tags.extend(mapping.tags)
            row_tags: list[str] = []
            if label:
                mapping = lookup_ulif_label(label)
                skip_gender = mapping is not None and mapping.role == "gender" and "p" in header_tags
                if mapping is None:
                    unmapped.append(label)
                elif not skip_gender:
                    row_tags.extend(mapping.tags)
            section_tags: list[str] = []
            for section_label in (parent_section, verbform_section):
                if not section_label:
                    continue
                mapped, raw = _map_label(section_label)
                section_tags.extend(mapped)
                unmapped.extend(raw)
            tags = [*section_tags, *row_tags, *header_tags]
            for surface in _split_cell_surface(cell.text):
                forms.append(
                    _form_row(
                        entry_key=entry_key,
                        surface=surface,
                        grammatical_tags=tags,
                        unmapped_labels=unmapped,
                        is_lemma=False,
                        is_invariable=False,
                    )
                )
    return forms


def parse_ulif_entry(
    html: str,
    *,
    homonym_index: int,
    register_position: str = "",
) -> dict[str, Any]:
    """Parse one entry page into identity plus ``ulif_forms`` rows.

    Every entry emits a base row from the headword and grammar line.
    ``is_invariable`` is set when ULIF prints no paradigm table. ``homonym_index``
    is the 1-based order of this entry inside its spelling group on the
    result list; the entry page is not asked to supply it.
    """
    identity = _article_identity(html)
    headword = str(identity["canonical_headword"])
    normalized = normalize_ulif_spelling(headword)
    key = ulif_entry_key(normalized, homonym_index)
    table = identity["paradigm_table"]
    invariable = bool(identity["invariable_phrase"] or table is None)
    grammar_tags, grammar_unmapped = _grammar_tags(str(identity["grammatical_label"]))
    base_surface = {
        "variant_order": 1,
        "preposition": "",
        "marked_asterisk": False,
        **_stress_record(headword),
    }
    forms = [
        _form_row(
            entry_key=key,
            surface=base_surface,
            grammatical_tags=grammar_tags,
            unmapped_labels=grammar_unmapped,
            is_lemma=True,
            is_invariable=invariable,
        )
    ]
    if isinstance(table, Tag):
        forms.extend(_paradigm_form_rows(table, key))
    return {
        "normalized_spelling": normalized,
        "homonym_index": homonym_index,
        "entry_key": key,
        "canonical_headword": headword,
        "grammatical_label": identity["grammatical_label"],
        "sense_gloss": identity["sense_gloss"],
        "content_sha256": identity["content_sha256"],
        "register_position": register_position,
        "printed_homonym_number": identity.get("printed_homonym_number"),
        "is_invariable": invariable,
        "parser_version": ULIF_FORMS_PARSER_VERSION,
        "forms": forms,
    }
