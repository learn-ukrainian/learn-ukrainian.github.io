"""Unit->output mapping carried through `generate_mdx` (fresh engine E3c-1, #8397 #8430).

The Urok renderer records, for every expanded unit it emits, the byte range of the unit's
text in its markdown. `generate_mdx` then rewrites that markdown in a fixed sequence of
transforms (frontmatter parsing, section clean-up, readings insertion, YouTube embedding,
inline activity injection, callouts, dialogues, duplicate-H1 removal, heading emojis, tab
wrapping, `normalize_mdx`). Every transform reports its edits explicitly: the character
ranges of its input it removed or replaced, and the text it put there (`Edit`). A transform
runs its string operations through an `EditLog`, which records the edits of every regex
substitution, range replacement, insertion or strip it performs and composes them into one
edit record per transform; line-based transforms report which input line (or slice of it)
each output line came from (`LineEdits`). The map then moves every unit by those records
alone: a unit no edit touches keeps its (shifted) location; a unit an edit overlaps is
marked lost with the transform's name. Identity is by position, never by content: nothing
is diffed, matched or searched for, so a removed unit is never re-attached to identical
text elsewhere. `verify` re-reads every unit at its own location in the final page text and
fails closed for lost units.

A unit whose page location is a component prop (a dialogue line inside the DialogueBox
`exchanges` payload) is tracked as the escaped bytes inside the JSX with the codec that
decodes them back to learner text (`CODEC_JS_JSON_STRING`).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Hashable, Iterable, Sequence
from dataclasses import dataclass

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


# =============================================================================
# Edit records
# =============================================================================


@dataclass(frozen=True)
class Edit:
    """One edit of a transform: its input's `[start, end)` became `replacement`.

    `start == end` is a pure insertion at `start`; an empty `replacement` is a removal.
    """

    start: int
    end: int
    replacement: str

    def __post_init__(self) -> None:
        if not 0 <= self.start <= self.end:
            raise ValueError(f"invalid edit range [{self.start}, {self.end})")


Region = tuple[int, int, int]
"""`(before_start, after_start, length)`: bytes an edit record left in place."""


def _check_edits(edits: Sequence[Edit], length: int) -> None:
    previous_end = 0
    for edit in edits:
        if edit.start < previous_end or edit.end > length:
            raise ValueError(f"edits are not sorted and non-overlapping within [0, {length}): {edit}")
        previous_end = edit.end


def narrow_edit(text: str, edit: Edit) -> Edit | None:
    """`edit` cut down to the bytes that actually change; None if it changes nothing.

    The common prefix and common suffix of the replaced bytes and their replacement are
    left out. This is positional: bytes are kept where they stand, never matched up by content
    elsewhere, so a replacement that gives back the text it replaced is not an edit at all.
    """
    old = text[edit.start : edit.end]
    new = edit.replacement
    limit = min(len(old), len(new))
    prefix = 0
    while prefix < limit and old[prefix] == new[prefix]:
        prefix += 1
    suffix = 0
    while suffix < limit - prefix and old[len(old) - 1 - suffix] == new[len(new) - 1 - suffix]:
        suffix += 1
    if prefix == len(old) == len(new):
        return None
    return Edit(edit.start + prefix, edit.end - suffix, new[prefix : len(new) - suffix])


def narrow_edits(text: str, edits: Sequence[Edit]) -> list[Edit]:
    """`narrow_edit` over sorted edits of `text`, dropping those that change nothing."""
    _check_edits(edits, len(text))
    narrowed = (narrow_edit(text, edit) for edit in edits)
    return [edit for edit in narrowed if edit is not None]


def apply_edits(text: str, edits: Sequence[Edit]) -> str:
    """Splice sorted, non-overlapping `edits` into `text`."""
    _check_edits(edits, len(text))
    parts: list[str] = []
    cursor = 0
    for edit in edits:
        parts.append(text[cursor : edit.start])
        parts.append(edit.replacement)
        cursor = edit.end
    parts.append(text[cursor:])
    return "".join(parts)


def regions_from_edits(edits: Sequence[Edit], length: int) -> list[Region]:
    """The bytes of a text of `length` that `edits` leave in place, with their new positions."""
    _check_edits(edits, length)
    regions: list[Region] = []
    b_cursor = a_cursor = 0
    for edit in edits:
        if edit.start > b_cursor:
            regions.append((b_cursor, a_cursor, edit.start - b_cursor))
            a_cursor += edit.start - b_cursor
        a_cursor += len(edit.replacement)
        b_cursor = edit.end
    if length > b_cursor:
        regions.append((b_cursor, a_cursor, length - b_cursor))
    return regions


def edits_from_regions(before: str, after: str, regions: Iterable[Region]) -> list[Edit]:
    """The edits turning `before` into `after` given the bytes that stayed (`regions`).

    Regions must be in document order on both sides; every gap between them is one edit,
    narrowed to the bytes that differ (a gap whose two sides are equal is no edit).
    A region whose bytes differ between the two texts is a reporting bug and raises.
    """
    edits: list[Edit] = []
    b_cursor = a_cursor = 0
    for b_start, a_start, length in regions:
        if length <= 0:
            continue
        if b_start < b_cursor or a_start < a_cursor:
            raise ValueError(f"kept regions are not in document order at ({b_start}, {a_start}, {length})")
        if before[b_start : b_start + length] != after[a_start : a_start + length]:
            raise ValueError(f"kept region ({b_start}, {a_start}, {length}) is not the same bytes on both sides")
        if b_start > b_cursor or a_start > a_cursor:
            edits.append(Edit(b_cursor, b_start, after[a_cursor:a_start]))
        b_cursor = b_start + length
        a_cursor = a_start + length
    if b_cursor < len(before) or a_cursor < len(after):
        edits.append(Edit(b_cursor, len(before), after[a_cursor:]))
    return narrow_edits(before, edits)


def compose_regions(first: Sequence[Region], second: Sequence[Region]) -> list[Region]:
    """Kept regions of two consecutive steps composed: a byte stays iff both steps kept it."""
    composed: list[Region] = []
    j = 0
    for b_start, m_start, length in first:
        m_end = m_start + length
        while j < len(second) and second[j][0] + second[j][2] <= m_start:
            j += 1
        k = j
        while k < len(second) and second[k][0] < m_end:
            m2_start, a_start, length2 = second[k]
            low = max(m_start, m2_start)
            high = min(m_end, m2_start + length2)
            if high > low:
                composed.append((b_start + low - m_start, a_start + low - m2_start, high - low))
            k += 1
    return composed


_TEMPLATE_ESCAPES = {"a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\"}


def _parse_template(template: str, pattern: re.Pattern[str]) -> list[str | int] | None:
    """A `re.sub` template as literal pieces and group numbers; None if it is not that simple."""
    pieces: list[str | int] = []
    literal: list[str] = []
    i = 0
    while i < len(template):
        char = template[i]
        if char != "\\":
            literal.append(char)
            i += 1
            continue
        i += 1
        if i >= len(template):
            return None
        char = template[i]
        group: int | None = None
        if char == "g":
            close = template.find(">", i)
            if i + 1 >= len(template) or template[i + 1] != "<" or close < 0:
                return None
            name = template[i + 2 : close]
            group = int(name) if name.isdigit() else pattern.groupindex.get(name)
            if group is None:
                return None
            i = close + 1
        elif char.isdigit():
            digits = char
            if i + 1 < len(template) and template[i + 1].isdigit():
                digits += template[i + 1]
            group = int(digits)
            i += len(digits)
        elif char in _TEMPLATE_ESCAPES:
            literal.append(_TEMPLATE_ESCAPES[char])
            i += 1
            continue
        else:
            return None
        if literal:
            pieces.append("".join(literal))
            literal = []
        pieces.append(group)
    if literal:
        pieces.append("".join(literal))
    return pieces


def _match_edits(match: re.Match[str], replacement: str, template: list[str | int] | None) -> list[Edit]:
    """The edits of one substitution: group references in the template are bytes kept in place.

    A template whose group references are not in match order (or repeat a group) is reported
    as a whole-match replacement.
    """
    if template is None:
        return [Edit(match.start(), match.end(), replacement)]
    edits: list[Edit] = []
    cursor = match.start()
    literal = ""
    rebuilt: list[str] = []
    for piece in template:
        if isinstance(piece, str):
            literal += piece
            rebuilt.append(piece)
            continue
        g_start, g_end = match.span(piece)
        if g_start < 0:
            continue  # an unmatched group expands to nothing
        if g_start < cursor:
            return [Edit(match.start(), match.end(), replacement)]
        rebuilt.append(match.string[g_start:g_end])
        if g_start > cursor or literal:
            edits.append(Edit(cursor, g_start, literal))
        literal = ""
        cursor = g_end
    if "".join(rebuilt) != replacement:
        return [Edit(match.start(), match.end(), replacement)]
    if match.end() > cursor or literal:
        edits.append(Edit(cursor, match.end(), literal))
    return edits


class EditLog:
    """A text under transformation, recording every edit against the text it started from.

    With `record=False` the log only performs the string operations (the legacy path; the
    library calls are the same as before the log existed, so output is byte-identical). With
    `record=True` it also keeps the regions of `before` that are still in place, composed
    over every operation, from which `edits()` reports the transform's edit record.
    """

    def __init__(self, text: str, record: bool = True) -> None:
        self.before = text
        self.text = text
        self.record = record
        self.regions: list[Region] = [(0, 0, len(text))] if text else []

    def apply(self, edits: Sequence[Edit], result: str | None = None) -> None:
        """Advance by explicit `edits` of the current text; `result`, if given, must be what they produce."""
        if self.record:
            spliced = apply_edits(self.text, edits)
            if result is not None and spliced != result:
                raise ValueError("the reported edits do not produce the transform's output")
            narrowed = narrow_edits(self.text, edits)
            self.regions = compose_regions(self.regions, regions_from_edits(narrowed, len(self.text)))
            self.text = spliced
        else:
            self.text = result if result is not None else apply_edits(self.text, edits)

    def replace(self, start: int, end: int, replacement: str) -> None:
        """Replace `[start, end)` of the current text (an insertion when `start == end`)."""
        if self.text[start:end] == replacement:
            return
        self.apply([Edit(start, end, replacement)], self.text[:start] + replacement + self.text[end:])

    def insert(self, position: int, text: str) -> None:
        self.replace(position, position, text)

    def strip(self) -> None:
        """`str.strip()`: leading and trailing whitespace removed from the ends."""
        stripped = self.text.strip()
        if not stripped:
            self.replace(0, len(self.text), "")
            return
        lead = len(self.text) - len(self.text.lstrip())
        trail = len(self.text) - len(self.text.rstrip())
        edits = [Edit(0, lead, "")] if lead else []
        if trail:
            edits.append(Edit(len(self.text) - trail, len(self.text), ""))
        if edits:
            self.apply(edits, stripped)

    def sub(
        self,
        pattern: str | re.Pattern[str],
        repl: str | Callable[[re.Match[str]], str],
        count: int = 0,
        flags: int = 0,
    ) -> list[tuple[int, int]]:
        """`re.sub` on the current text, reporting each substitution as edits.

        A string template reports the bytes of its group references as kept in place (so a
        `\\1`-style template around a unit leaves the unit located); a callable replacement
        is reported as one whole-match replacement. Every edit is then narrowed to the bytes
        that change, so a replacement equal to its match is no edit. Returns the `[start, end)` range of every
        replacement in the new text, in order.
        """
        compiled = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        if not self.record:
            self.text = compiled.sub(repl, self.text, count)
            return []
        template = _parse_template(repl, compiled) if isinstance(repl, str) else None
        recorded: list[tuple[re.Match[str], str]] = []

        def replace(match: re.Match[str]) -> str:
            replacement = repl(match) if callable(repl) else match.expand(repl)
            recorded.append((match, replacement))
            return replacement

        result = compiled.sub(replace, self.text, count)
        edits: list[Edit] = []
        ranges: list[tuple[int, int]] = []
        delta = 0
        for match, replacement in recorded:
            edits.extend(_match_edits(match, replacement, template))
            ranges.append((match.start() + delta, match.start() + delta + len(replacement)))
            delta += len(replacement) - (match.end() - match.start())
        self.apply(edits, result)
        return ranges

    def edits(self) -> list[Edit]:
        """The transform's edit record: how `before` became the current text."""
        if not self.record:
            raise ValueError("this log did not record edits")
        return edits_from_regions(self.before, self.text, self.regions)


LineSource = tuple[int, Sequence[Region]] | None
"""Where an output line came from: `(input line, kept regions within it)`, or None for new text."""


class LineEdits:
    """Output of a line-based transform with, per output line, the input line it came from.

    The transform splits its input on newlines and appends output lines; here it says for
    each one whether it is input line `i` verbatim (`keep`), a slice of it (`slice`), input
    line `i` after its own recorded edits (`edited`) or new text (`new`). The newline between
    two output lines that come from consecutive input lines is the input's own separator;
    every other newline, and every input line never referenced, is an edit.
    """

    def __init__(self, text: str, record: bool = True) -> None:
        self.before = text
        self.lines = text.split("\n")
        self.record = record
        self.out: list[str] = []
        self.src: list[LineSource] = []

    def _append(self, text: str, source: LineSource) -> None:
        self.out.append(text)
        if self.record:
            self.src.append(source)

    def keep(self, index: int) -> None:
        line = self.lines[index]
        self._append(line, (index, [(0, 0, len(line))]))

    def slice(self, index: int, start: int, end: int) -> None:
        self._append(self.lines[index][start:end], (index, [(start, 0, end - start)]))

    def edited(self, index: int, log: EditLog) -> None:
        """Input line `index` transformed through its own `EditLog` (started from that line)."""
        if log.before != self.lines[index]:
            raise ValueError(f"the log was not started from input line {index}")
        self._append(log.text, (index, log.regions))

    def new(self, text: str) -> None:
        self._append(text, None)

    def delete(self, position: int) -> None:
        """Drop output line `position` again (a transform retracting an emitted line)."""
        del self.out[position]
        if self.record:
            del self.src[position]

    def text(self) -> str:
        return "\n".join(self.out)

    def edits(self) -> list[Edit]:
        if not self.record:
            raise ValueError("this log did not record edits")
        offsets = [0]
        for line in self.lines:
            offsets.append(offsets[-1] + len(line) + 1)
        regions: list[Region] = []
        a_cursor = 0
        previous: LineSource = None
        for position, (line, source) in enumerate(zip(self.out, self.src, strict=True)):
            if position:
                if source is not None and previous is not None and source[0] == previous[0] + 1:
                    regions.append((offsets[source[0]] - 1, a_cursor, 1))
                a_cursor += 1
            if source is not None:
                index, local = source
                regions.extend((offsets[index] + b, a_cursor + a, n) for b, a, n in local)
            a_cursor += len(line)
            previous = source
        return edits_from_regions(self.before, self.text(), regions)


# =============================================================================
# The map
# =============================================================================


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


def _carry_unit(start: int, end: int, edits: Sequence[Edit]) -> tuple[int, int] | str:
    """The unit's range after `edits`, or the kind of loss if an edit touched it."""
    shift = 0
    covered = 0
    touched = False
    for edit in edits:
        if edit.start == edit.end:
            if edit.start <= start:
                shift += len(edit.replacement)
            elif edit.start < end:
                touched = True  # an insertion inside the unit splits it
            continue
        if edit.end <= start:
            shift += len(edit.replacement) - (edit.end - edit.start)
        elif edit.start < end:
            touched = True
            covered += min(end, edit.end) - max(start, edit.start)
    if touched:
        return LOST_REMOVED if covered >= end - start else LOST_REWRITTEN
    return (start + shift, end + shift)


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

    def carry(self, before: str, after: str, transform: str, edits: Sequence[Edit]) -> None:
        """Advance the map over one transform that turned `before` into `after` by `edits`.

        The edits are the transform's own report of what it removed, replaced or inserted;
        they must reproduce `after` from `before`. Units are moved by position only.
        """
        if before != self.text:
            raise ValueError(f"transform {transform!r} was not applied to the mapped text")
        if apply_edits(before, edits) != after:
            raise ValueError(f"transform {transform!r} reported edits that do not produce its output")
        edits = narrow_edits(before, edits)
        for unit in self.units.values():
            if not unit.live:
                continue
            assert unit.start is not None and unit.end is not None
            target = _carry_unit(unit.start, unit.end, edits)
            if isinstance(target, str):
                unit.lost_kind = target
                unit.lost_by = transform
                unit.start = unit.end = None
            else:
                unit.start, unit.end = target
        self.text = after

    def carry_log(self, log: EditLog, transform: str) -> str:
        """`carry` over a recorded `EditLog`; returns the transformed text."""
        self.carry(log.before, log.text, transform, log.edits())
        return log.text

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
