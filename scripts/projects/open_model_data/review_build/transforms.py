"""Closed, auditable removal-only transforms. Policies belong to reviewed specs."""

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from types import MappingProxyType

from .errors import BuildError, require


@dataclass(frozen=True)
class Result:
    text: str
    dropped_lines: tuple[tuple[int, int], ...] = ()
    joins: tuple[tuple[int, int, str], ...] = ()


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


REGISTRY = MappingProxyType(
    {
        "verbatim": _verbatim,
        "ulif_html_text@1": _html,
        "line_excision@1": _lines,
        "dehyphenate@1": _dehyphenate,
    }
)


def transform(name: str, text: str, policy: dict | None = None, reader: object = None) -> Result:
    if name not in REGISTRY:
        raise BuildError("unknown_transform")
    return REGISTRY[name](text, policy or {}, reader)
