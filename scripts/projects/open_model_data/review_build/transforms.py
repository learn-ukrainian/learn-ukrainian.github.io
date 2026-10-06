"""Closed, auditable removal-only transforms. Policies belong to reviewed specs."""

import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from types import MappingProxyType

from .errors import BuildError, require


@dataclass(frozen=True)
class Result:
    text: str
    dropped_lines: tuple[tuple[int, int], ...] = ()
    joins: tuple[tuple[int, int, str], ...] = ()
    join_evidence: tuple[tuple[int, int, str, str], ...] = ()
    unresolved: tuple[tuple[int, int, str], ...] = ()


class _TextNodes(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.nodes: list[str] = []

    def handle_data(self, data: str) -> None:
        self.nodes.append(data)


def _verbatim(text: str, policy: dict, reader: object) -> Result:
    return Result(text)


def _html(text: str, policy: dict, reader: object) -> Result:
    parser = _TextNodes()
    parser.feed(text)
    parser.close()
    return Result(re.sub(r"\s+", " ", "".join(parser.nodes)).strip())


def _lines(text: str, policy: dict, reader: object) -> Result:
    patterns = policy.get("patterns", [])
    require(bool(patterns) and all(isinstance(p, str) for p in patterns), "transform_policy")
    kept, dropped = [], []
    for index, line in enumerate(text.splitlines(keepends=True), 1):
        if any(re.fullmatch(p, line.rstrip("\r\n")) for p in patterns):
            dropped.append((index, index))
        else:
            kept.append(line)
    return Result("".join(kept), tuple(dropped))


def _dehyphenate(text: str, policy: dict, reader: object) -> Result:
    require(reader is not None and hasattr(reader, "is_word"), "transform_policy")
    joins = []

    def join(match: re.Match) -> str:
        left, right = match.group(1), match.group(2)
        if reader.is_word(left + right, policy) and not reader.is_word(left + "-" + right, policy):
            joins.append((match.start(), match.end(), left + right))
            return left + right
        return match.group()

    # Combining marks belong to a source token; never attest only its suffix.
    token = r"[^\W\d_](?:[^\W\d_]|[\u0300-\u036f'’ʼ])*"
    edge = r"[\w\u0300-\u036f'’ʼ]"
    result = re.sub(rf"(?<!{edge})({token})-\r?\n({token})(?!{edge})", join, text)
    return Result(result, joins=tuple(joins))


# Protect complete tokens, including apostrophes, marks and compound hyphens.
TOKEN = r"[^\W\d_](?:[^\W\d_]|[\u0300-\u036f'’ʼ])*"
EDGE = r"[\w\u0300-\u036f'’ʼ-]"
PART = rf"{TOKEN}(?:-{TOKEN})*"
LINE_BREAK = re.compile(rf"(?<!{EDGE})(-?{PART})-[ \t]*\r?\n[ \t]*({PART}-?)(?!{EDGE})")
BREAK_SIGNAL = re.compile(r"[\w\u0300-\u036f’ʼ']+-[ \t]*\r?\n[ \t]*[\w\u0300-\u036f’ʼ']+")
WORDS = re.compile(rf"(?<!{EDGE}){TOKEN}(?:-{TOKEN})*(?!{EDGE})")


def fold_word(text: str) -> str:
    """The held VESUM folded index removes stress and folds apostrophes/case."""
    text = unicodedata.normalize("NFD", text).replace("\u0301", "").replace("\u0300", "")
    return unicodedata.normalize("NFC", text).replace("'", "’").replace("ʼ", "’").casefold()


def _dehyphenate_v2(text: str, policy: dict, reader: object) -> Result:
    """Decide each printed split independently; unmatched metadata fails closed."""
    require(reader is not None and hasattr(reader, "text_metadata"), "transform_policy")
    alternatives = reader.text_metadata(text, policy)
    joins, evidence, unresolved, covered = [], [], [], []

    def decide(left, right):
        joined, hyphenated = left + right, left + "-" + right
        joined_word = reader.is_word(joined, policy)
        hyphenated_word = reader.is_word(hyphenated, policy)
        if not hyphenated_word and (joined_word or reader.has_text_word(joined, policy)):
            return joined, "vesum_form" if joined_word else "held_text"
        if hyphenated_word and not joined_word:
            return hyphenated, "vesum_hyphenated_form"
        return None, None

    edits = []

    def resolve(start, end, left, right):
        near_left, near_right = left.strip("-").split("-")[-1], right.strip("-").split("-")[0]
        readings = {
            fold_word(left + right),
            fold_word(left + "-" + right),
            fold_word(near_left + near_right),
            fold_word(near_left + "-" + near_right),
        }
        for index, alt in enumerate(alternatives):
            if index not in covered and fold_word(alt) in readings:
                covered.append(index)
                break
        replacement, kind = decide(left, right)
        if replacement is None:
            unresolved.append((start, end, left + "-" + right))
            return
        if kind != "vesum_hyphenated_form":
            joins.append((start, end, replacement))
        evidence.append((start, end, replacement, kind))
        edits.append((start, end, replacement))

    # Printed splits take precedence over unrelated inline occurrences of the
    # same alternative. Consume each stored occurrence once.
    printed = list(LINE_BREAK.finditer(text))
    for match in printed:
        resolve(match.start(), match.end(), match[1], match[2])
    # Malformed token boundaries cannot evade the whole-token decision rule.
    for match in BREAK_SIGNAL.finditer(text):
        if not any(p.start() <= match.start() and p.end() >= match.end() for p in printed):
            unresolved.append((match.start(), match.end(), match[0]))
    inline = re.compile(rf"(?<!{EDGE})({TOKEN})-({TOKEN})(?!{EDGE})")
    for match in inline.finditer(text):
        if any(
            index not in covered and fold_word(alt) in {fold_word(match[1] + match[2]), fold_word(match[0])}
            for index, alt in enumerate(alternatives)
        ):
            resolve(match.start(), match.end(), match[1], match[2])
    result = text
    for start, end, replacement in sorted(edits, reverse=True):
        result = result[:start] + replacement + result[end:]
    for index, alt in enumerate(alternatives):
        if index not in covered:
            unresolved.append((-1, -1, alt))
    return Result(
        result, joins=tuple(sorted(joins)), join_evidence=tuple(sorted(evidence)), unresolved=tuple(sorted(unresolved))
    )


def source_text_defects(text: str, policy: dict, reader: object, *, original: str | None = None) -> tuple[str, ...]:
    """Withhold suspected fused words, never silently insert a guessed space.

    A whole form must be absent from VESUM and other held paragraphs. Each
    side of a possible split must be an attested form AND an unhyphenated held
    word. This is a conservative defect signal, not an editorial correction.
    """
    defects = []
    for match in WORDS.finditer(text):
        token = match[0]
        if (
            "-" in token
            or reader.is_word(token, policy)
            or reader.has_text_word(token, policy, exclude=original or text)
        ):
            continue
        for index in range(2, len(token) - 1):
            left, right = token[:index], token[index:]
            if (
                reader.has_text_word(left, policy)
                and reader.has_text_word(right, policy)
                and reader.is_word(left, policy)
                and reader.is_word(right, policy)
            ):
                defects.append(token)
                break
    return tuple(defects)


REGISTRY = MappingProxyType(
    {
        "verbatim": _verbatim,
        "ulif_html_text@1": _html,
        "line_excision@1": _lines,
        "dehyphenate@1": _dehyphenate,
        "dehyphenate@2": _dehyphenate_v2,
    }
)


def transform(name: str, text: str, policy: dict | None = None, reader: object = None) -> Result:
    if name not in REGISTRY:
        raise BuildError("unknown_transform")
    return REGISTRY[name](text, policy or {}, reader)
