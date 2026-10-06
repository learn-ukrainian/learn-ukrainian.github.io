"""Closed, auditable removal-only transforms. Policies belong to reviewed specs."""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from html.parser import HTMLParser
from types import MappingProxyType

from scripts.rag.word_identity import normalize_evidence_form

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
    """Use the canonical case/stress/apostrophe identity of the VESUM index."""
    return normalize_evidence_form(text)


def _dehyphenate_v2(text: str, policy: dict, reader: object) -> Result:
    """Decide each printed split independently; unmatched metadata fails closed."""
    require(reader is not None and hasattr(reader, "text_metadata"), "transform_policy")
    alternatives = reader.text_metadata(text, policy)
    joins, evidence, unresolved, covered = [], [], [], []

    def decide(left, right, alternative_covered):
        joined, hyphenated = left + right, left + "-" + right
        joined_word = reader.is_word(joined, policy)
        hyphenated_word = reader.is_word(hyphenated, policy)
        if joined_word and not hyphenated_word:
            return joined, "vesum_form"
        if alternative_covered and hyphenated_word and not joined_word:
            return hyphenated, "hyphen_alternative"
        return None, None

    edits = []

    def readings(left, right):
        near_left, near_right = left.strip("-").split("-")[-1], right.strip("-").split("-")[0]
        return {
            fold_word(left + right),
            fold_word(left + "-" + right),
            fold_word(near_left + near_right),
            fold_word(near_left + "-" + near_right),
        }

    def resolve(start, end, left, right, positions):
        matching = [index for index, alt in enumerate(alternatives) if fold_word(alt) in readings(left, right)]
        # Metadata has no offsets. A reading covers this position only when it
        # maps to exactly one split, with no competing/duplicate alternatives.
        unique = (
            len(matching) == 1
            and sum(fold_word(alternatives[matching[0]]) in readings(m[1], m[2]) for m in positions) == 1
        )
        alternative_covered = unique and matching[0] not in covered
        if alternative_covered:
            covered.append(matching[0])
        replacement, kind = decide(left, right, alternative_covered)
        if replacement is None:
            unresolved.append((start, end, left + "-" + right))
            return
        if kind == "vesum_form":
            joins.append((start, end, replacement))
        evidence.append((start, end, replacement, kind))
        edits.append((start, end, replacement))

    # Alternatives describe printed line-break splits only. Inline hyphens
    # cannot consume them; unused stored occurrences remain unresolved.
    printed = list(LINE_BREAK.finditer(text))
    for match in printed:
        resolve(match.start(), match.end(), match[1], match[2], printed)
    # Malformed token boundaries cannot evade the whole-token decision rule.
    for match in BREAK_SIGNAL.finditer(text):
        if not any(p.start() <= match.start() and p.end() >= match.end() for p in printed):
            unresolved.append((match.start(), match.end(), match[0]))
    result = text
    for start, end, replacement in sorted(edits, reverse=True):
        result = result[:start] + replacement + result[end:]
    for index, alt in enumerate(alternatives):
        if index not in covered:
            unresolved.append((-1, -1, alt))
    return Result(
        result, joins=tuple(sorted(joins)), join_evidence=tuple(sorted(evidence)), unresolved=tuple(sorted(unresolved))
    )


def unresolved_overlaps(result: Result, span: tuple[int, int] | None) -> bool:
    """Check only unresolved positions carried by a transformed value.

    Decision offsets refer to the original field. Project them through earlier
    resolved edits before comparing with model-visible spans. Unlocated metadata
    cannot prove absence and fails closed. A whole-field value carries every
    position; an empty unresolved set never withholds anything.
    """
    for start, end, _ in result.unresolved:
        if start < 0 or span is None:
            return True
        shift = sum(len(text) - (b - a) for a, b, text, _ in result.join_evidence if b <= start)
        if start + shift < span[1] and end + shift > span[0]:
            return True
    return False


@lru_cache(maxsize=256)
def _boundary_defects(original: str, text: str) -> tuple[str, ...]:
    """Locate actual whitespace deletion, rather than unrelated split witnesses."""
    defects = []
    for tag, start, end, visible, _ in SequenceMatcher(None, original, text, autojunk=False).get_opcodes():
        if tag != "delete" or not original[start:end].isspace():
            continue
        # Only a deletion strictly inside the resulting whole token loses a
        # word boundary. A retained hyphen still separates printed components.
        for match in WORDS.finditer(text):
            if match.start() < visible < match.end() and "-" not in match[0]:
                defects.append(match[0])
                break
    return tuple(defects)


def source_text_defects(text: str, policy: dict, reader: object, *, original: str | None = None) -> tuple[str, ...]:
    """Detect lost source word boundaries, never infer errors from rare words.

    Dictionary absence and separately attested pieces cannot establish a defect
    in a token printed by the source. Require positive boundary evidence in the
    cited original: two consecutive whitespace-separated words fused in output.
    No original means no evidence, rather than an invented negative attestation.
    """
    if original is None or text == original:
        return ()
    return _boundary_defects(original, text)


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
