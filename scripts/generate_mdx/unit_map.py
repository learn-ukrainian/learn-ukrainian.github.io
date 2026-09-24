"""Unit->output mapping carried through `generate_mdx` (fresh engine E3c-1, #8397 #8430).

The Urok renderer records, for every expanded unit it emits, the byte range of the unit's
text in its markdown. `generate_mdx` then rewrites that markdown in a fixed sequence of
transforms (frontmatter parsing, section clean-up, readings insertion, YouTube embedding,
inline activity injection, callouts, dialogues, duplicate-H1 removal, heading emojis, tab
wrapping, `normalize_mdx`). After each transform the map is carried forward: a unit whose
bytes survive unchanged inside one contiguous equal region of the transform's diff keeps its
(shifted) location; a unit the transform removed or rewrote is marked lost, with the
transform's name. `verify` then re-reads every unit at its own location in the final page
text and fails closed for lost units. Nothing is ever searched for in the page.

A unit whose page location is a component prop (a dialogue line inside the DialogueBox
`exchanges` payload) is tracked as the escaped bytes inside the JSX with the codec that
decodes them back to learner text (`CODEC_JS_JSON_STRING`).
"""

from __future__ import annotations

import json
import re
from collections.abc import Hashable
from dataclasses import dataclass
from difflib import SequenceMatcher

CODEC_PLAIN = "plain"
# A JSON string body inside a single-quoted JS string literal: `JSON.parse('...')`.
CODEC_JS_JSON_STRING = "js_json_string"

LOST_REMOVED = "removed"
LOST_REWRITTEN = "rewritten"

_JS_STRING_UNESCAPE_RE = re.compile(r"\\([\\'])")


def encode_js_json_string(text: str) -> str:
    """Bytes of `text` inside `JSON.parse('...')`: a JSON string body, then JS-escaped.

    Both escapes substitute per character, so encoding fragments separately and
    concatenating them yields the encoding of the concatenation.
    """
    body = json.dumps(text, ensure_ascii=False)[1:-1]
    return body.replace("\\", "\\\\").replace("'", "\\'")


def decode_js_json_string(fragment: str) -> str:
    """Inverse of `encode_js_json_string`: what `JSON.parse` yields for the fragment."""
    return json.loads('"' + _JS_STRING_UNESCAPE_RE.sub(r"\1", fragment) + '"')


def decode(codec: str, fragment: str) -> str:
    if codec == CODEC_PLAIN:
        return fragment
    if codec == CODEC_JS_JSON_STRING:
        return decode_js_json_string(fragment)
    raise ValueError(f"unknown unit codec {codec!r}")


class UnitMapError(Exception):
    """A tracked unit is not at its location in the final page text (fail closed)."""

    def __init__(self, kind: str, key: Hashable, transform: str, text: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.key = key
        self.transform = transform
        self.text = text
        self.message = message


@dataclass
class TrackedUnit:
    key: Hashable
    text: str
    codec: str = CODEC_PLAIN
    start: int | None = None
    end: int | None = None
    lost_by: str | None = None
    lost_kind: str | None = None

    @property
    def live(self) -> bool:
        return self.lost_by is None


def _common_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def _common_suffix_len(a: str, b: str, limit: int) -> int:
    i = 0
    while i < limit and a[len(a) - 1 - i] == b[len(b) - 1 - i]:
        i += 1
    return i


def _line_offsets(lines: list[str]) -> list[int]:
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    return offsets


_LINE_KEY_RE = re.compile(r"^[\s>]+")


def _line_key(line: str) -> str:
    """Alignment key of a line: leading blockquote markers and edge whitespace ignored.

    Transforms typically strip `> ` prefixes (callouts) or pad lines; keying on the content
    keeps such lines as anchors, while blank lines (empty key) never anchor the alignment.
    """
    return _LINE_KEY_RE.sub("", line).rstrip()


def _char_regions(b_chunk: str, a_chunk: str, b_base: int, a_base: int) -> list[tuple[int, int, int]]:
    matcher = SequenceMatcher(None, b_chunk, a_chunk, autojunk=False)
    return [(b_base + blk.a, a_base + blk.b, blk.size) for blk in matcher.get_matching_blocks() if blk.size]


def equal_regions(before: str, after: str) -> list[tuple[int, int, int]]:
    """Regions `(before_start, after_start, length)` whose bytes a transform left in place.

    Regions are in document order on both sides (monotonic) and non-overlapping. The diff is
    the common prefix and suffix, then a line-level alignment of the middle keyed on line
    content (`_line_key`), refined character by character wherever paired lines are not
    byte-identical and inside replaced line groups. Adjacent regions are merged.
    """
    if before == after:
        return [(0, 0, len(before))] if before else []
    prefix = _common_prefix_len(before, after)
    suffix = _common_suffix_len(before, after, min(len(before), len(after)) - prefix)
    regions: list[tuple[int, int, int]] = []
    if prefix:
        regions.append((0, 0, prefix))
    b_mid = before[prefix : len(before) - suffix]
    a_mid = after[prefix : len(after) - suffix]
    b_lines = b_mid.splitlines(keepends=True)
    a_lines = a_mid.splitlines(keepends=True)
    b_off = _line_offsets(b_lines)
    a_off = _line_offsets(a_lines)
    b_keys = [_line_key(line) for line in b_lines]
    a_keys = [_line_key(line) for line in a_lines]
    matcher = SequenceMatcher(lambda key: key == "", b_keys, a_keys, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2), strict=True):
                if b_lines[i] == a_lines[j]:
                    regions.append((prefix + b_off[i], prefix + a_off[j], len(b_lines[i])))
                else:
                    regions.extend(_char_regions(b_lines[i], a_lines[j], prefix + b_off[i], prefix + a_off[j]))
        elif tag == "replace":
            regions.extend(
                _char_regions(
                    b_mid[b_off[i1] : b_off[i2]],
                    a_mid[a_off[j1] : a_off[j2]],
                    prefix + b_off[i1],
                    prefix + a_off[j1],
                )
            )
    if suffix:
        regions.append((len(before) - suffix, len(after) - suffix, suffix))
    merged: list[tuple[int, int, int]] = []
    for region in regions:
        if merged:
            b_start, a_start, length = merged[-1]
            if b_start + length == region[0] and a_start + length == region[1]:
                merged[-1] = (b_start, a_start, length + region[2])
                continue
        merged.append(region)
    return merged


class LessonUnitMap:
    """Tracked units and their byte ranges in `text`, carried through transforms."""

    def __init__(self, text: str = "") -> None:
        self.text = text
        self.units: dict[Hashable, TrackedUnit] = {}

    def track(self, key: Hashable, start: int, end: int, text: str, codec: str = CODEC_PLAIN) -> None:
        """Record that `text` lives at `[start, end)` of the current text (encoded per `codec`)."""
        if key in self.units:
            raise ValueError(f"unit {key!r} is already tracked")
        if not 0 <= start <= end <= len(self.text) or decode(codec, self.text[start:end]) != text:
            raise ValueError(f"unit {key!r}: bytes {self.text[start:end]!r} at [{start}, {end}) do not carry {text!r}")
        self.units[key] = TrackedUnit(key=key, text=text, codec=codec, start=start, end=end)

    def texts(self) -> dict[Hashable, str]:
        return {key: unit.text for key, unit in self.units.items()}

    def carry(self, before: str, after: str, transform: str) -> None:
        """Advance the map over one transform that turned `before` into `after`."""
        if before != self.text:
            raise ValueError(f"transform {transform!r} was not applied to the mapped text")
        if before != after:
            regions = equal_regions(before, after)
            for unit in self.units.values():
                if not unit.live:
                    continue
                assert unit.start is not None and unit.end is not None
                target = _map_range(regions, unit.start, unit.end)
                if target is None:
                    unit.lost_kind = (
                        LOST_REMOVED if not _overlaps_any(regions, unit.start, unit.end) else LOST_REWRITTEN
                    )
                    unit.lost_by = transform
                    unit.start = unit.end = None
                else:
                    unit.start, unit.end = target
        self.text = after

    def adopt(self, other: LessonUnitMap) -> None:
        """Take over the units of a map in the same coordinate space (same current text)."""
        if other.text != self.text:
            raise ValueError("cannot adopt units mapped onto a different text")
        for key, unit in other.units.items():
            if key in self.units:
                raise ValueError(f"unit {key!r} is already tracked")
            self.units[key] = unit

    def verify(self, final: str) -> dict[Hashable, str]:
        """Read every unit back at its own location in `final`; fail closed for lost units.

        Returns the decoded text found for every unit, keyed by unit key.
        """
        if final != self.text:
            raise ValueError("the final text is not the text the map was carried to")
        found: dict[Hashable, str] = {}
        for key, unit in self.units.items():
            if not unit.live:
                assert unit.lost_by is not None and unit.lost_kind is not None
                verb = "removed" if unit.lost_kind == LOST_REMOVED else "rewrote"
                raise UnitMapError(
                    unit.lost_kind,
                    key,
                    unit.lost_by,
                    unit.text,
                    f"generate_mdx transform {unit.lost_by!r} {verb} the bytes of unit {key!r} ({unit.text!r}); "
                    "the page does not carry that text at the unit's location",
                )
            assert unit.start is not None and unit.end is not None
            fragment = final[unit.start : unit.end]
            try:
                text = decode(unit.codec, fragment)
            except ValueError as exc:
                raise UnitMapError(
                    LOST_REWRITTEN,
                    key,
                    "verify",
                    unit.text,
                    f"unit {key!r}: the page bytes {fragment!r} do not decode as {unit.codec}: {exc}",
                ) from exc
            if text != unit.text:
                raise UnitMapError(
                    LOST_REWRITTEN,
                    key,
                    "verify",
                    unit.text,
                    f"unit {key!r}: the page carries {text!r} at the unit's location, not {unit.text!r}",
                )
            found[key] = text
        return found


def _map_range(regions: list[tuple[int, int, int]], start: int, end: int) -> tuple[int, int] | None:
    for b_start, a_start, length in regions:
        if b_start <= start and end <= b_start + length:
            return (a_start + start - b_start, a_start + end - b_start)
    return None


def _overlaps_any(regions: list[tuple[int, int, int]], start: int, end: int) -> bool:
    return any(b_start < end and start < b_start + length for b_start, _a_start, length in regions)
