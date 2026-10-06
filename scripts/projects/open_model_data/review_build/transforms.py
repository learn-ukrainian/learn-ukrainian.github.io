"""Closed, auditable removal-only transforms. Policies belong to reviewed specs."""

import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from types import MappingProxyType
from weakref import WeakKeyDictionary

from .contract import Citation, digest
from .errors import BuildError, require


@dataclass(frozen=True)
class Result:
    text: str
    dropped_lines: tuple[tuple[int, int], ...] = ()
    joins: tuple[tuple[int, int, str], ...] = ()


_LINE_QUERIES = WeakKeyDictionary()


def queried_lines(policy: dict, reader: object) -> dict[str, set[int]]:
    """Cache reviewed row-scoped line removals in the pinned read transaction."""
    require(reader is not None and hasattr(reader, "query_values"), "transform_policy")
    query = policy["line_query"]
    key = json.dumps([query, policy["table"], policy["field"]], sort_keys=True)
    cache = _LINE_QUERIES.setdefault(reader, {})
    if key not in cache:
        rows, records = {}, []
        for raw in reader.query_values(query):
            row_key, line, field = json.loads(raw)
            require(
                isinstance(row_key, str) and type(line) is int and line > 0 and isinstance(field, str),
                "transform_policy",
            )
            field_sha256 = digest(field.encode("utf-8"))
            # Pin removed-only pages too: no response value may survive there.
            reader.field(
                Citation(
                    "line_excision",
                    query["store"],
                    policy["table"],
                    row_key,
                    policy["field"],
                    f"line {line}",
                    field_sha256,
                )
            )
            rows.setdefault(row_key, set()).add(line)
            records.append(
                {
                    "kind": "running_head_occurrence",
                    "store": query["store"],
                    "table": policy["table"],
                    "field": policy["field"],
                    "row_key": row_key,
                    "field_sha256": field_sha256,
                    "line_ranges": [[line, line]],
                }
            )
        cache[key] = (rows, records)
    return cache[key][0]


def line_excision_records(policy: dict, reader: object) -> list[dict]:
    """Original row hashes and ranges, including excisions in withheld units."""
    queried_lines(policy, reader)
    key = json.dumps([policy["line_query"], policy["table"], policy["field"]], sort_keys=True)
    return _LINE_QUERIES[reader][key][1]


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


def _lines(text: str, policy: dict, reader: object, citation=None) -> Result:
    patterns = policy.get("patterns", [])
    require(bool(patterns) and all(isinstance(p, str) for p in patterns), "transform_policy")
    selected = set()
    if "line_query" in policy:
        require(
            citation is not None
            and citation.store == policy["line_query"]["store"]
            and citation.table == policy.get("table")
            and citation.field == policy.get("field"),
            "transform_policy",
        )
        selected = queried_lines(policy, reader).get(citation.row_key, set())
    kept, dropped = [], []
    for index, line in enumerate(re.findall(r"[^\n]+\n?|\n", text), 1):
        if index in selected or any(re.fullmatch(p, line.rstrip("\r\n")) for p in patterns):
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

    result = re.sub(r"([^\W\d_]+)-\r?\n([^\W\d_]+)", join, text)
    return Result(result, joins=tuple(joins))


REGISTRY = MappingProxyType(
    {
        "verbatim": _verbatim,
        "ulif_html_text@1": _html,
        "line_excision@1": _lines,
        "dehyphenate@1": _dehyphenate,
    }
)


def transform(name: str, text: str, policy: dict | None = None, reader: object = None, citation=None) -> Result:
    if name not in REGISTRY:
        raise BuildError("unknown_transform")
    if name == "line_excision@1":
        return _lines(text, policy or {}, reader, citation)
    return REGISTRY[name](text, policy or {}, reader)
