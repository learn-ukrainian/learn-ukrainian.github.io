"""Private page-image and transcription tooling for #9604; no source text in git."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pymupdf
from jsonschema import Draft202012Validator

PDF_SHA256 = "5ea396063526800ebe095d0e8dc99477caf56964bf0ecbe13f14995c750e1555"
NOTATION_PATH = Path(__file__).with_name("pohribnyi_notation.json")
CACHE_DIR = Path(".cache/pohribnyi")
CANONICAL_MARK_ORDER = [
    "U+032D", "U+0306",  # Breve is intrinsic to the precomposed base.
    "U+A675", "U+2DF7", "U+A677", "U+2DEA", "U+1E08F",
    "U+1ABB", "U+1ABC", "U+0301", "U+0300", "U+0358", "U+0361",
]
APPROXIMATION = dict(zip("ꙵⷷꙷⷪ\U0001e08f", "иеуоі", strict=True))
DEGREE = {"\u1abb": 1, "\u1abc": 2}
STRESS = {"\u0301": "primary", "\u0300": "secondary"}
SOFTNESS = {"ʹ": "soft", "ʼ": "half_soft"}
SEPARATORS = set(" ,;‐–")
RAISED = {
    "\U0001e034": "д", "\U0001e037": "з", "\U0001e044": "ц",
    "\U0001e036": "ж", "\U0001e046": "ш", "\U0001e045": "ч", "\U0001e040": "т",
}
FROZEN_PRECOMPOSED = "ўЎйЙѐЀѝЍѓЃќЌ"
FROZEN_LETTERS = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюяыАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯЫўЎ"
WITHHELD_MARKER = "\ufffc"
WITHHELD_MARKERS = {WITHHELD_MARKER, "\ufffd"}
FROZEN_SYMBOL_POINTS = set(CANONICAL_MARK_ORDER) | {
    f"U+{ord(c):04X}" for c in set(RAISED) | SEPARATORS | set("ʹʼːўґыйѐѝ")
}


def load_notation(path: Path = NOTATION_PATH) -> dict:
    """Validate the notation-table schema before using its allowlist."""
    table = json.loads(path.read_text(encoding="utf-8"))
    validate_notation(table)
    return table


def validate_notation(table: dict) -> None:
    """Check schema, Unicode constraints and the provisional/frozen boundary."""
    schema = json.loads(NOTATION_PATH.with_suffix(".schema.json").read_text(encoding="utf-8"))
    if not Draft202012Validator(schema).is_valid(table):
        raise ValueError("Invalid notation table schema")
    if tuple(map(int, unicodedata.unidata_version.split("."))) < (15, 0, 0):
        raise ValueError("Frozen notation requires Unicode 15.0 or later")
    if (table["status"] == "provisional") != table["provisional"]:
        raise ValueError("Notation status and provisional flag disagree")
    letters = table["letters"]
    if (
        any("CYRILLIC" not in unicodedata.name(c, "") for c in letters)
        or unicodedata.normalize("NFC", letters) != letters
    ):
        raise ValueError("Notation letters must be NFC Cyrillic")
    if not table["provisional"] and (letters != FROZEN_LETTERS or table["precomposed_letters"] != FROZEN_PRECOMPOSED):
        raise ValueError("Frozen letter inventory differs from driver reconciliation")
    roles, points = set(), set()
    for symbol in table.get("symbols", []):
        role, point = symbol.get("role"), symbol.get("codepoint")
        if role in roles:
            raise ValueError("Invalid or duplicate symbol role")
        number = int(point[2:], 16)
        if number > 0x10FFFF or 0xD800 <= number <= 0xDFFF or point in points:
            raise ValueError("Invalid or duplicate codepoint")
        if "LATIN" in unicodedata.name(chr(number), ""):
            raise ValueError("Latin symbol in notation table")
        char = chr(number)
        if unicodedata.category(char) == "Cn":
            raise ValueError("Unassigned codepoint in notation table")
        if (
            symbol["glyph"] != char
            or symbol["unicode_name"] != unicodedata.name(char)
            or symbol["combining_class"] != unicodedata.combining(char)
        ):
            raise ValueError("Notation symbol Unicode metadata mismatch")
        if char in APPROXIMATION and symbol.get("letter") != APPROXIMATION[char]:
            raise ValueError("Approximation letter mapping mismatch")
        if (char in RAISED or role.startswith("raised_")) and (
            char not in RAISED or symbol.get("letter") != RAISED[char] or not role.startswith("raised_")
        ):
            raise ValueError("Raised letter mapping mismatch")
        if not table["provisional"] and symbol["provisional"]:
            raise ValueError("Frozen table contains provisional symbols")
        roles.add(role)
        points.add(point)
    if not table["provisional"] and (
        table.get("pending_classes") != [] or len(set(table.get("freeze_reviewers", []))) < 2
    ):
        raise ValueError("Frozen notation needs two reviewers and no pending classes")
    if not table["provisional"] and points != FROZEN_SYMBOL_POINTS:
        raise ValueError("Frozen symbol inventory differs from driver reconciliation")

    marks = {point for point in points if unicodedata.combining(chr(int(point[2:], 16)))}
    if set(table["combining_mark_order"]) != marks:
        raise ValueError("Combining mark order must list every combining symbol exactly once")
    if table["combining_mark_order"] != CANONICAL_MARK_ORDER:
        raise ValueError("Combining mark order differs from driver reconciliation")
    allowed = set(unicodedata.normalize("NFD", letters)) | {chr(int(point[2:], 16)) for point in points}
    for char in table["precomposed_letters"]:
        decomposed = unicodedata.normalize("NFD", char)
        if len(decomposed) < 2 or not set(decomposed) <= allowed or unicodedata.normalize("NFC", decomposed) != char:
            raise ValueError("Precomposed letters must be NFC compositions of listed letters and symbols")


def normalize_transcription(text: str, table: dict, *, printed_anomaly: bool = False) -> str:
    """Apply the notation's equal-class mark order inside brackets, then NFC.

    This is a notation convention beyond Unicode canonical equivalence (UAX #15).
    Validation never silently changes input; the diff calls this before comparing.
    """
    rank = {chr(int(point[2:], 16)): i for i, point in enumerate(table["combining_mark_order"])}
    result, end = [], 0
    for span in bracketed_spans(text, printed_anomaly=printed_anomaly):
        result.append(text[end : span["start"]])
        ordered, marks = [], []
        for char in unicodedata.normalize("NFD", span["text"]):
            if unicodedata.combining(char):
                marks.append(char)
            else:
                ordered.extend(sorted(marks, key=lambda c: (unicodedata.combining(c), rank.get(c, -1))))
                marks = []
                ordered.append(char)
        ordered.extend(sorted(marks, key=lambda c: (unicodedata.combining(c), rank.get(c, -1))))
        result.append("".join(ordered))
        end = span["end"]
    result.append(text[end:])
    return unicodedata.normalize("NFC", "".join(result))


def bracketed_spans(text: str, *, printed_anomaly: bool = False) -> list[dict]:
    """Return bracket spans; a flagged final unclosed bracket stays faithful to print."""
    spans, start = [], None
    for offset, char in enumerate(text):
        if char == "[":
            if start is not None:
                raise ValueError("Nested transcription brackets")
            start = offset
        elif char == "]":
            if start is None:
                raise ValueError("Unmatched closing bracket")
            if offset == start + 1:
                raise ValueError("Empty transcription")
            spans.append({"start": start, "end": offset + 1, "text": text[start : offset + 1]})
            start = None
    if start is not None:
        if not printed_anomaly or start + 1 == len(text):
            raise ValueError("Unclosed transcription bracket")
        spans.append({"start": start, "end": len(text), "text": text[start:], "printed_anomaly": "unclosed_bracket"})
    return spans


def _parse_transcription(text: str, table: dict) -> list[dict]:
    """Derive clusters and separators from an already allowlisted bracket span."""
    raised = {s["glyph"]: s["letter"] for s in table["symbols"] if s["role"].startswith("raised_")}
    bases = set(table["letters"] + table["precomposed_letters"])
    groups, index = [], 1
    end = len(text) - 1
    while index < end:
        char = text[index]
        if char in SEPARATORS:
            groups.append({"separator": char})
            index += 1
            continue
        if char not in bases:
            raise ValueError("Expected base letter before notation marks")
        index += 1
        # Only accented compositions need decomposing in the derived view;
        # intrinsic breve/diaeresis stays in the precomposed base (ў, й, ї).
        decomposed = unicodedata.normalize("NFD", char)
        accented = any(c in STRESS for c in decomposed[1:])
        base = unicodedata.normalize("NFC", "".join(c for c in decomposed if c not in STRESS))
        group = {
            "base": base if accented else char,
            "devoicing": False, "approximation_letter": None, "degree": 0,
            "stress": None, "slight_softening": False, "tie": False,
            "softness": None, "length": False, "raised_group": [],
        }
        marks = [c for c in decomposed[1:] if c in STRESS] if accented else []
        while index < end and unicodedata.combining(text[index]):
            marks.append(text[index])
            index += 1
        for mark in marks:
            if mark in APPROXIMATION:
                key, value = "approximation_letter", APPROXIMATION[mark]
            elif mark in DEGREE:
                key, value = "degree", DEGREE[mark]
            elif mark in STRESS:
                key, value = "stress", STRESS[mark]
            elif mark in {"\u032d", "\u0358", "\u0361"}:
                key = {"\u032d": "devoicing", "\u0358": "slight_softening", "\u0361": "tie"}[mark]
                value = True
            else:
                raise ValueError("Unexpected intrinsic mark after base letter")
            if group[key]:
                raise ValueError(f"Duplicate {key} on one base")
            group[key] = value
        if group["degree"] and not group["approximation_letter"]:
            raise ValueError("Approximation degree requires an approximation letter")
        if index < end and text[index] in SOFTNESS:
            group["softness"] = SOFTNESS[text[index]]
            index += 1
        if index < end and text[index] == "ː":
            group["length"] = True
            index += 1
        while index < end and text[index] in raised:
            item = {"letter": raised[text[index]], "tie": False, "softness": None}
            index += 1
            if index < end and text[index] == "\u0361":
                item["tie"] = True
                index += 1
            if index < end and text[index] in SOFTNESS:
                item["softness"] = SOFTNESS[text[index]]
                index += 1
            group["raised_group"].append(item)
        if group["tie"] and (index >= end or text[index] not in bases):
            raise ValueError("Affricate tie requires a following base letter")
        for pos, item in enumerate(group["raised_group"]):
            if item["tie"] and pos == len(group["raised_group"]) - 1:
                raise ValueError("Raised affricate tie requires a following raised letter")
        groups.append(group)
    return groups


def _serialize_transcription(groups: list[dict], table: dict) -> str:
    """Serialize the derived fields with canonical ordering and NFC only."""
    approximation = {v: k for k, v in APPROXIMATION.items()}
    degree = {v: k for k, v in DEGREE.items()}
    stress = {v: k for k, v in STRESS.items()}
    softness = {v: k for k, v in SOFTNESS.items()}
    raised = {s["letter"]: s["glyph"] for s in table["symbols"] if s["role"].startswith("raised_")}
    result = ["["]
    for group in groups:
        if "separator" in group:
            result.append(group["separator"])
            continue
        result.append(group["base"])
        if group["devoicing"]:
            result.append("\u032d")
        if group["approximation_letter"]:
            result.append(approximation[group["approximation_letter"]])
        if group["degree"]:
            result.append(degree[group["degree"]])
        if group["stress"]:
            result.append(stress[group["stress"]])
        if group["slight_softening"]:
            result.append("\u0358")
        if group["tie"]:
            result.append("\u0361")
        if group["softness"]:
            result.append(softness[group["softness"]])
        if group["length"]:
            result.append("ː")
        for item in group["raised_group"]:
            result.append(raised[item["letter"]])
            if item["tie"]:
                result.append("\u0361")
            if item["softness"]:
                result.append(softness[item["softness"]])
    result.append("]")
    return unicodedata.normalize("NFC", "".join(result))


def parse_transcription(text: str, table: dict) -> list[dict]:
    """Return the lossless structured view of exactly one bracketed transcription."""
    spans = validate_text(text, table)
    if len(spans) != 1 or spans[0]["text"] != text:
        raise ValueError("Expected exactly one bracketed transcription")
    return _parse_transcription(text, table)


def serialize_transcription(groups: list[dict], table: dict) -> str:
    """Recreate the authoritative string; reject inconsistent structured fields."""
    text = _serialize_transcription(groups, table)
    if parse_transcription(text, table) != groups:
        raise ValueError("Structured transcription does not round-trip")
    return text


def validate_text(text: str, table: dict, *, printed_anomaly: bool = False, allow_withheld: bool = False) -> list[dict]:
    """Validate notation, allowing only explicitly recorded print/withholding exceptions."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Paragraph text must be nonempty")
    if any(unicodedata.category(char) == "Cn" for char in text):
        raise ValueError("Unassigned codepoint in text")
    if not allow_withheld and any(c in WITHHELD_MARKERS for c in text):
        raise ValueError("Withheld marker requires a withheld entry")
    if unicodedata.normalize("NFC", text) != text:
        raise ValueError("Text is not NFC; normalization must precede offset assignment")
    allowed = set(table["letters"] + table["precomposed_letters"]) | {
        chr(int(s["codepoint"][2:], 16)) for s in table["symbols"]
    }
    if allow_withheld:
        allowed.add(WITHHELD_MARKER)
    spans = bracketed_spans(text, printed_anomaly=printed_anomaly)
    if normalize_transcription(text, table, printed_anomaly=printed_anomaly) != text:
        raise ValueError("Noncanonical combining mark order")
    for span in spans:
        interior = span["text"][1:] if span.get("printed_anomaly") else span["text"][1:-1]
        for char in interior:
            if "LATIN" in unicodedata.name(char, ""):
                raise ValueError(f"Latin codepoint U+{ord(char):04X} inside transcription")
            if char not in allowed:
                raise ValueError(f"Unknown transcription symbol U+{ord(char):04X}")
        if allow_withheld and WITHHELD_MARKER in interior:
            continue  # Missing glyphs cannot establish a complete cluster structure.
        if (
            printed_anomaly
            and interior
            and all(unicodedata.combining(c) or c in SOFTNESS or c == "ː" for c in interior)
        ):
            span["printed_anomaly"] = span.get("printed_anomaly", "mark_without_base")
            continue
        closed = span["text"] + ("]" if span.get("printed_anomaly") else "")
        if _serialize_transcription(_parse_transcription(closed, table), table) != closed:
            raise ValueError("Noncanonical transcription structure")
    return spans


def transcription_rows(data: dict | list) -> list[dict]:
    """Adapt a page packet, packet array or legacy row array without mutating input."""
    items = [data] if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise ValueError("Expected nonempty paragraph rows or page packets")
    rows = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Paragraph row or page packet must be an object")
        if "paragraphs" not in item:
            rows.append(dict(item))
            continue
        paragraphs, seat = item["paragraphs"], item.get("seat")
        if not isinstance(seat, str) or not seat.strip():
            raise ValueError("Page packet requires a nonempty seat")
        if not isinstance(paragraphs, list) or not paragraphs:
            raise ValueError("Page packet requires nonempty paragraphs")
        for paragraph in paragraphs:
            if not isinstance(paragraph, dict):
                raise ValueError("Paragraph must be an object")
            underlines = paragraph.get("underlines")
            if not isinstance(underlines, list) or any(
                not isinstance(pair, list) or len(pair) != 2 for pair in underlines
            ):
                raise ValueError("Packet underlines must be [start, end] pairs")
            rows.append(
                {
                    **paragraph,
                    "page": item.get("page"),
                    "seat": seat,
                    "paragraph": paragraph.get("n"),
                    "underlining": [{"start": pair[0], "end": pair[1]} for pair in underlines],
                }
            )
    return rows


def _ranges(value: object, text: str, name: str) -> list[dict]:
    """Check ordered, half-open ranges against the original codepoint offsets."""
    if not isinstance(value, list):
        raise ValueError(f"Explicit {name} field required (empty list if absent)")
    last_end = 0
    for interval in value:
        if not isinstance(interval, dict):
            raise ValueError(f"{name} interval must be an object")
        start, end = interval.get("start"), interval.get("end")
        if type(start) is not int or type(end) is not int or not last_end <= start < end <= len(text):
            raise ValueError(f"Invalid or overlapping {name} range")
        last_end = end
    return value


def _masked_text(row: dict) -> str:
    """Collapse withheld ranges to the canonical placeholder for validation/comparison."""
    parts, end = [], 0
    for span in row.get("withheld", []):
        parts.extend((row["text"][end : span["start"]], WITHHELD_MARKER))
        end = span["end"]
    return "".join(parts) + row["text"][end:]


def validate_rows(rows: dict | list, table: dict, *, adjudicated: bool = False, normalizing: bool = False) -> None:
    """Validate both input formats, layout and exceptions; ingest requires adjudication."""
    seen, seats = set(), {}
    for row in transcription_rows(rows):
        page, paragraph = row.get("page"), row.get("paragraph")
        if type(page) is not int or not 1 <= page <= 28 or type(paragraph) is not int or paragraph < 1:
            raise ValueError("Invalid page/paragraph locator")
        if (page, paragraph) in seen:
            raise ValueError("Duplicate page/paragraph locator")
        seen.add((page, paragraph))
        seat = row.get("seat")
        if seat is not None and (not isinstance(seat, str) or not seat.strip()):
            raise ValueError("Invalid seat")
        if page in seats and seats[page] != seat:
            raise ValueError("Mixed seats on one page")
        seats[page] = seat
        text = row.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Paragraph text must be nonempty")
        _ranges(row.get("underlining"), text, "underlining")
        withheld = _ranges(row.get("withheld", []), text, "withheld")
        for span in withheld:
            if not isinstance(span.get("reason"), str) or not span["reason"].strip():
                raise ValueError("Withheld span requires a reason")
        for offset, char in enumerate(text):
            if char in WITHHELD_MARKERS and not any(s["start"] == offset and s["end"] == offset + 1 for s in withheld):
                raise ValueError("Withheld marker must coincide with a withheld entry")
        anomaly = row.get("printed_anomaly", False)
        if type(anomaly) is not bool:
            raise ValueError("printed_anomaly must be a boolean")
        breaks = row.get("line_breaks", [])
        if not isinstance(breaks, list):
            raise ValueError("line_breaks must be a list")
        previous = -1
        for line in breaks:
            if not isinstance(line, dict):
                raise ValueError("Line break must be an object")
            offset = line.get("offset")
            if type(offset) is not int or not previous < offset <= len(text) or offset < 0:
                raise ValueError("Invalid or duplicate line break offset")
            if type(line.get("printed_hyphen")) is not bool or type(line.get("lexical", False)) is not bool:
                raise ValueError("Line break requires boolean printed_hyphen and optional lexical")
            if "‐" in text[max(0, offset - 1) : offset + 1] and not line.get("lexical", False):
                raise ValueError("Line-end U+2010 must be layout metadata unless marked lexical")
            previous = offset
        boundaries = {0, len(text)} | {
            i for i, c in enumerate(text) if not unicodedata.combining(c) or (anomaly and i > 0 and text[i - 1] == "[")
        }
        for span in row["underlining"] + withheld:
            if span["start"] not in boundaries or span["end"] not in boundaries:
                raise ValueError("Range boundary splits a combining sequence")
        if any(line["offset"] not in boundaries for line in breaks):
            raise ValueError("Line break splits a combining sequence")
        masked = _masked_text(row)
        validate_text(
            normalize_transcription(masked, table, printed_anomaly=anomaly) if normalizing else masked,
            table,
            printed_anomaly=anomaly,
            allow_withheld=bool(withheld),
        )
        if adjudicated and (
            row.get("status") != "adjudicated"
            or not isinstance(row.get("adjudicated_by"), str)
            or not row["adjudicated_by"].strip()
        ):
            raise ValueError("Adjudication status and adjudicated_by are required")


def _page_view(rows: list[dict], table: dict) -> dict:
    """Build token/prose streams with offsets into original paragraphs joined by LF."""
    view = {
        "text": "",
        "tokens": [],
        "prose": [],
        "characters": [],
        "boundaries": [],
        "paragraph_ends": [],
        "line_breaks": [],
        "withheld": [],
        "printed_anomalies": [],
    }
    for row in sorted(rows, key=lambda r: r["paragraph"]):
        if view["text"]:
            view["boundaries"].append(len(view["characters"]))
            view["paragraph_ends"].append(len(view["text"]))
            view["text"] += "\n"
            # Paragraph and prose whitespace are identical comparison units.
            _append_unit(view["prose"], " ", len(view["text"]) - 1, len(view["text"]), False)
            _append_unit(view["characters"], " ", len(view["text"]) - 1, len(view["text"]), False)
        base, text = len(view["text"]), row["text"]
        view["text"] += text
        view["withheld"].extend(
            {**span, "start": base + span["start"], "end": base + span["end"]} for span in row.get("withheld", [])
        )
        if row.get("printed_anomaly", False):
            view["printed_anomalies"].append({"start": base, "end": base + len(text)})
        spans = bracketed_spans(_masked_text(row), printed_anomaly=row.get("printed_anomaly", False))
        # Remap masked offsets to raw offsets, including multi-character withheld ranges.
        mapping, cursor = [], 0
        for withheld in row.get("withheld", []):
            mapping.extend((i, i + 1) for i in range(cursor, withheld["start"]))
            mapping.append((withheld["start"], withheld["end"]))
            cursor = withheld["end"]
        mapping.extend((i, i + 1) for i in range(cursor, len(text)))
        tokens = {}
        for span in spans:
            start, end = mapping[span["start"]][0], mapping[span["end"] - 1][1]
            raw = {"start": base + start, "end": base + end, "text": text[start:end]}
            missing = WITHHELD_MARKER in span["text"]
            key = (
                WITHHELD_MARKER
                if missing
                else normalize_transcription(span["text"], table, printed_anomaly=row.get("printed_anomaly", False))
            )
            view["tokens"].append({**raw, "key": key, "withheld": missing})
            tokens[start] = end
        withheld_at = {s["start"]: s for s in row.get("withheld", [])}
        index, token_end = 0, 0
        while index < len(text):
            if index in tokens:
                token_end = tokens[index]
            missing = index in withheld_at
            end = withheld_at[index]["end"] if missing else index + 1
            if not missing and text[index] not in "[]":
                while end < len(text) and unicodedata.combining(text[end]):
                    end += 1
            key = WITHHELD_MARKER if missing else unicodedata.normalize("NFC", text[index:end])
            if not missing and index < token_end:
                key = normalize_transcription("[" + text[index:end] + "]", table)[1:-1] if key not in "[]" else key
            underlined = any(s["start"] <= index < s["end"] for s in row["underlining"])
            _append_unit(view["characters"], key, base + index, base + end, underlined)
            if index >= token_end:
                _append_unit(view["prose"], key, base + index, base + end, underlined)
            index = end
        view["line_breaks"].extend({**line, "offset": base + line["offset"]} for line in row.get("line_breaks", []))
    while view["prose"] and view["prose"][0]["key"] == " ":
        view["prose"].pop(0)
    while view["prose"] and view["prose"][-1]["key"] == " ":
        view["prose"].pop()
    return view


def _append_unit(units: list[dict], key: str, start: int, end: int, underlined: bool) -> None:
    """Collapse layout whitespace while preserving its original offset range."""
    key = " " if key.isspace() else key
    if units and key == units[-1]["key"] == " ":
        units[-1]["end"] = end
        units[-1]["underlined"] |= underlined
    else:
        units.append({"key": key, "start": start, "end": end, "underlined": underlined})


def _reading(view: dict, units: list[dict]) -> dict | None:
    """Expose raw seat text and offsets, never comparison-only normalization."""
    if not units:
        return None
    start, end = units[0]["start"], units[-1]["end"]
    reading = {"start": start, "end": end, "text": view["text"][start:end]}
    withheld = [s for s in view["withheld"] if s["start"] < end and start < s["end"]]
    if withheld:
        reading.update(withheld=withheld, placeholder=WITHHELD_MARKER)
    return reading


def _withheld_diff(left: dict, right: dict) -> list[tuple]:
    """Align uncertainty against raw reading ranges before either reading diff.

    Full character anchors allow a placeholder to cover either prose or brackets,
    including a whole bracket span missing from one seat. The aligned gap is
    unresolved evidence; it cannot license a reading disagreement inside that gap.
    """
    a, b = left["characters"], right["characters"]
    matcher = SequenceMatcher(a=[u["key"] for u in a], b=[u["key"] for u in b], autojunk=False)
    differences, covered = [], [[], []]
    for tag, i, j, k, l in matcher.get_opcodes():
        pairs = [([x], [y]) for x, y in zip(a[i:j], b[k:l], strict=True)] if tag == "equal" else [(a[i:j], b[k:l])]
        for xs, ys in pairs:
            if not any(u["key"] == WITHHELD_MARKER for u in xs + ys):
                continue
            readings = [_reading(view, units) for view, units in ((left, xs), (right, ys))]
            differences.append(("withheld", *readings))
            for ranges, reading in zip(covered, readings, strict=True):
                if reading:
                    ranges.append((reading["start"], reading["end"]))
    for view, ranges in zip((left, right), covered, strict=True):
        for stream in ("tokens", "prose"):
            view[stream] = [
                u
                for u in view[stream]
                if not any(
                    (start <= u["start"] and u["end"] <= end)
                    if u["key"] == " "
                    else (start < u["end"] and u["start"] < end)
                    for start, end in ranges
                )
            ]
        units = []
        for unit in view["prose"]:
            _append_unit(units, unit["key"], unit["start"], unit["end"], unit["underlined"])
        while units and units[0]["key"] == " ":
            units.pop(0)
        while units and units[-1]["key"] == " ":
            units.pop()
        view["prose"] = units
    return differences


def _stream_diff(left: dict, right: dict, stream: str) -> list[tuple]:
    """Align the remaining known page tokens/prose after withholding classification."""
    a, b = left[stream], right[stream]
    matcher = SequenceMatcher(a=[u["key"] for u in a], b=[u["key"] for u in b], autojunk=False)
    differences = []
    for tag, i, j, k, l in matcher.get_opcodes():
        if tag == "equal":
            continue
        if stream == "tokens":
            pairs = [
                ([a[pos]] if pos < j else [], [b[k + pos - i]] if k + pos - i < l else [])
                for pos in range(i, i + max(j - i, l - k))
            ]
        else:
            pairs = [(a[i:j], b[k:l])]
        for xs, ys in pairs:
            kind = "bracketed_span" if stream == "tokens" else "paragraph_text"
            differences.append((kind, _reading(left, xs), _reading(right, ys)))
    return differences


def diff_transcriptions(left: dict | list, right: dict | list, table: dict) -> dict:
    """Align whole pages; paragraph splitting never drives reading disagreements."""
    left, right = transcription_rows(left), transcription_rows(right)
    validate_rows(left, table, normalizing=True)
    validate_rows(right, table, normalizing=True)
    disagreements, pages = [], []
    for page in sorted({r["page"] for r in left + right}):
        rows = [[r for r in side if r["page"] == page] for side in (left, right)]
        a, b = [_page_view(side, table) for side in rows]
        summary = {"page": page}
        for label, side, view in zip(("left", "right"), rows, (a, b), strict=True):
            summary.update(
                {
                    f"{label}_paragraphs": len(side),
                    f"{label}_bracketed_spans": len(view["tokens"]),
                    f"{label}_text": view["text"],
                    f"{label}_seat": side[0].get("seat") if side else None,
                    f"{label}_line_breaks": view["line_breaks"],
                    f"{label}_printed_anomalies": view["printed_anomalies"],
                }
            )
        pages.append(summary)
        differences = []
        if not all(rows):
            differences.append(("missing_page", _reading(a, a["characters"]), _reading(b, b["characters"])))
        differences.extend(_withheld_diff(a, b))
        differences.extend(_stream_diff(a, b, "tokens"))
        differences.extend(_stream_diff(a, b, "prose"))
        matcher = SequenceMatcher(
            a=[u["key"] for u in a["characters"]], b=[u["key"] for u in b["characters"]], autojunk=False
        )
        mapped_boundaries, underline_a, underline_b = set(), [], []
        for tag, i, j, k, l in matcher.get_opcodes():
            if tag == "equal":
                mapped_boundaries.update(k + pos - i for pos in a["boundaries"] if i <= pos <= j)
                for x, y in zip(a["characters"][i:j], b["characters"][k:l], strict=True):
                    if x["key"] != WITHHELD_MARKER and x["underlined"] != y["underlined"]:
                        underline_a.append(_reading(a, [x]))
                        underline_b.append(_reading(b, [y]))
            else:
                xs = [u for u in a["characters"][i:j] if u["underlined"] and u["key"] != WITHHELD_MARKER]
                ys = [u for u in b["characters"][k:l] if u["underlined"] and u["key"] != WITHHELD_MARKER]
                if xs or ys:
                    underline_a.append(_reading(a, xs))
                    underline_b.append(_reading(b, ys))
        if all(rows) and (len(a["boundaries"]) != len(b["boundaries"]) or mapped_boundaries != set(b["boundaries"])):
            differences.append(("paragraph_boundary", a["paragraph_ends"], b["paragraph_ends"]))
        if underline_a:
            differences.append(("underlining", underline_a, underline_b))
        for kind, lhs, rhs in differences:
            disagreements.append(
                {"page": page, "kind": kind, "left": lhs, "right": rhs, "resolution": None, "resolved_by": None}
            )
    return {
        "schema_version": 2,
        "provisional_notation": table["provisional"],
        "pages": pages,
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
    }


def render_pages(
    pdf: Path, cache: Path = CACHE_DIR, *, expected_sha256: str = PDF_SHA256, expected_pages: int = 28
) -> dict:
    """Render hash-verified PDF to a Git-ignored cache, recording page hashes and dimensions."""
    payload = pdf.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise ValueError("PDF SHA-256 does not match held artifact")
    cache = cache.resolve()
    repo = Path.cwd().resolve()
    try:
        relative = cache.relative_to(repo)
    except ValueError as exc:
        raise ValueError("Cache must be inside the worktree and Git-ignored") from exc
    targets = [relative / "manifest.json"] + [
        relative / f"page-{number:02d}.png" for number in range(1, expected_pages + 1)
    ]
    for target in targets:
        ignored = subprocess.run(["git", "check-ignore", "-q", "--", str(target)], cwd=repo, check=False, timeout=30)
        if ignored.returncode != 0:
            raise ValueError("Cache must be Git-ignored")
    with pymupdf.open(stream=payload, filetype="pdf") as document:
        if len(document) != expected_pages:
            raise ValueError("PDF page count does not match expected denominator")
        cache.mkdir(parents=True, exist_ok=True)
        pages = []
        for number, page in enumerate(document, 1):
            target = cache / f"page-{number:02d}.png"
            pixmap = page.get_pixmap(dpi=300, alpha=False)
            pixmap.save(target)
            pages.append(
                {
                    "page": number,
                    "file": target.name,
                    "width": pixmap.width,
                    "height": pixmap.height,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                }
            )
    manifest = {
        "pdf_sha256": digest,
        "dpi": 300,
        "page_count": len(pages),
        "renderer": f"PyMuPDF {pymupdf.VersionBind}",
        "pages": pages,
    }
    (cache / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_transcriptions(path: Path, *, directory: bool = False) -> list[dict]:
    """Read one JSON input or all direct *.json children in deterministic order."""
    files = sorted(path.glob("*.json")) if directory else [path]
    if not files:
        raise ValueError("Transcription directory contains no JSON files")
    rows = []
    for file in files:
        rows.extend(transcription_rows(json.loads(file.read_text(encoding="utf-8"))))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render, validate or diff private Pohribnyi transcription inputs.\n"
        "Use before adjudication; this tool does not transcribe or ingest text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.ingest.pohribnyi_tooling render --pdf held.pdf\n"
        "  .venv/bin/python -m scripts.ingest.pohribnyi_tooling validate --input .cache/rows.json\n"
        "  .venv/bin/python -m scripts.ingest.pohribnyi_tooling diff --left .cache/a.json "
        "--right .cache/b.json --output .cache/diff.json\n"
        "  Folder mode: diff --left-dir .cache/seat-a --right-dir .cache/seat-b --output .cache/diff.json\n"
        "Outputs: ignored PNGs/manifest or private JSON diff; no database writes.\n"
        "Exit codes: 0 success (diff may contain disagreements); 1 invalid data; 2 invalid CLI invocation.\n"
        "Related: #9604; pohribnyi_notation.json; docs/projects/open-model-data/PLAN.md.",
    )
    parser.add_argument(
        "--notation",
        type=Path,
        default=NOTATION_PATH,
        help="Notation JSON table (default: bundled frozen pohribnyi_notation.json).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render", help="Render the held 28-page PDF at 300 dpi.")
    render.add_argument("--pdf", type=Path, required=True, help="Held PDF path, e.g. held.pdf; SHA checked.")
    render.add_argument(
        "--cache", type=Path, default=CACHE_DIR, help="Git-ignored image directory (default: .cache/pohribnyi)."
    )
    validate = sub.add_parser("validate", help="Validate page packets or legacy paragraph rows.")
    validate.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Page-packet object/array or paragraph-array JSON, e.g. .cache/seat-a.json.",
    )
    diff = sub.add_parser("diff", help="Align whole pages and list unresolved token, prose and metadata differences.")
    left = diff.add_mutually_exclusive_group(required=True)
    left.add_argument("--left", type=Path, help="First seat JSON file, e.g. .cache/a.json; no default.")
    left.add_argument("--left-dir", type=Path, help="First seat folder of *.json page packets; no default.")
    right = diff.add_mutually_exclusive_group(required=True)
    right.add_argument("--right", type=Path, help="Second seat JSON file, e.g. .cache/b.json; no default.")
    right.add_argument("--right-dir", type=Path, help="Second seat folder of *.json page packets; no default.")
    diff.add_argument(
        "--output", type=Path, required=True, help="Private diff JSON destination, e.g. .cache/diff.json."
    )
    args = parser.parse_args(argv)
    if args.command == "diff" and bool(args.left_dir) != bool(args.right_dir):
        parser.error("Use paired --left/--right files or paired --left-dir/--right-dir folders")
    try:
        if args.command == "render":
            report = render_pages(args.pdf, args.cache)
            print(
                json.dumps(
                    {"page_count": report["page_count"], "dpi": report["dpi"], "pdf_sha256": report["pdf_sha256"]}
                )
            )
        else:
            table = load_notation(args.notation)
            if args.command == "validate":
                rows = load_transcriptions(args.input)
                validate_rows(rows, table)
                print(json.dumps({"valid_rows": len(rows), "provisional_notation": table["provisional"]}))
            else:
                report = diff_transcriptions(
                    load_transcriptions(args.left_dir or args.left, directory=bool(args.left_dir)),
                    load_transcriptions(args.right_dir or args.right, directory=bool(args.right_dir)),
                    table,
                )
                args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(json.dumps({"disagreement_count": report["disagreement_count"]}))
    except (ValueError, OSError) as exc:
        # Validation errors omit private paragraph text.
        parser.exit(1, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
