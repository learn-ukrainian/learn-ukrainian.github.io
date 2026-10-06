"""Declarative binding-spec.v1 interpreter, independent of candidate extraction.

Selectors: {area: slots|context|response, slot: name, citation: 0,
            field: optional DB column}; absent field selects exact value text.
Rules: equal, same_row, one_group, example_list, contiguous_pages, contrast_pair,
       form_agreement, literal. Unknown rules fail closed. A component owns the
reviewed spec, not a callable validation hook.
"""

import re
import unicodedata

from .contract import Candidate, Value
from .errors import BuildError, require
from .snapshot import SnapshotReader
from .transforms import transform


def select(candidate: Candidate, selector: dict) -> Value:
    require(selector.get("area") in {"slots", "context", "response"}, "binding_selector")
    matches = [v for v in getattr(candidate, selector["area"]) if v.slot == selector["slot"]]
    require(len(matches) == 1, "binding_selector")
    return matches[0]


def citation_for(candidate: Candidate, selector: dict):
    value = select(candidate, selector)
    index = selector.get("citation", 0)
    require(isinstance(index, int) and 0 <= index < len(value.citations), "binding_selector")
    return value.citations[index]


def operand(candidate: Candidate, selector: dict, reader: SnapshotReader):
    value = select(candidate, selector)
    if "field" in selector:
        row = reader.row(citation_for(candidate, selector))
        require(selector["field"] in row, "binding_field")
        return row[selector["field"]]
    if selector.get("citation", 0):
        _, field = reader.field(citation_for(candidate, selector))
        return field
    return value.text


def boundary(candidate: Candidate, definition: int | dict, reader: SnapshotReader) -> int:
    if isinstance(definition, dict) and "query" in definition:
        query = dict(definition["query"])
        query["parameters"] = [operand(candidate, ref, reader) for ref in definition.get("parameters", [])]
        result = reader.units(query)
        require(len(result) == 1, "binding_pages")
        return int(result[0])
    value = operand(candidate, definition, reader) if isinstance(definition, dict) else definition
    require(type(value) is int, "binding_pages")
    return value


def example_regions(text: str) -> list[tuple[int, int]]:
    """Colon-introduced list through its line/paragraph terminator (not next paragraph)."""
    regions = []
    for match in re.finditer(r":(?:[ \t]*\n[ \t]*)?", text):
        end = text.find("\n", match.end())
        regions.append((match.end(), len(text) if end < 0 else end))
    return regions


def _unstress(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\u0301", ""))


def check(candidate: Candidate, spec: dict, reader: SnapshotReader, policies: dict) -> set[str]:
    require(spec.get("schema") == "binding-spec.v1" and bool(spec.get("rules")), "binding_spec")
    passed = set()
    agreements: list[list[dict]] = []
    for rule in spec["rules"]:
        op = rule["op"]
        selectors = rule.get("values", [])
        if op == "equal":
            operands = [operand(candidate, s, reader) for s in selectors]
            require(len(operands) >= 2 and all(o == operands[0] for o in operands), "binding_equal")
            agreements.append(selectors)
        elif op == "literal":
            require(
                len(selectors) == 1 and operand(candidate, selectors[0], reader) == rule["expected"], "binding_literal"
            )
        elif op == "same_row":
            citations = [citation_for(candidate, s) for s in selectors]
            require(len(citations) >= 2 and len({(c.store, c.table, c.row_key) for c in citations}) == 1, "binding_row")
        elif op == "one_group":
            operands = [operand(candidate, s, reader) for s in selectors]
            require(bool(operands) and all(o is not None and o == operands[0] for o in operands), "binding_group")
        elif op == "example_list":
            value = select(candidate, selectors[0])
            citation = value.citations[0]
            _, field = reader.field(citation)
            require(isinstance(field, str) and value.span is not None, "binding_example")
            source = transform(value.transform, field, policies.get(value.transform), reader).text
            require(
                any(start <= value.span[0] < value.span[1] <= end for start, end in example_regions(source)),
                "binding_example",
            )
        elif op == "contiguous_pages":
            pages = [operand(candidate, s, reader) for s in selectors]
            require(
                bool(pages)
                and all(type(p) is int for p in pages)
                and pages
                == list(
                    range(boundary(candidate, rule["first"], reader), boundary(candidate, rule["next_heading"], reader))
                ),
                "binding_pages",
            )
            citations = [citation_for(candidate, s) for s in selectors]
            sources = [reader.row(c)[rule["source_field"]] for c in citations]
            require(len(set(sources)) == 1, "binding_pages")
        elif op == "form_agreement":
            require(len(selectors) == 2, "binding_agreement")
            require(
                citation_for(candidate, selectors[0]) == citation_for(candidate, rule["left_tags"])
                and citation_for(candidate, selectors[1]) == citation_for(candidate, rule["right_tags"]),
                "binding_agreement",
            )
            agreements.append(selectors)
            require(
                _unstress(str(operand(candidate, selectors[0], reader)))
                == _unstress(str(operand(candidate, selectors[1], reader))),
                "binding_agreement",
            )
            require(
                operand(candidate, rule["left_tags"], reader) == operand(candidate, rule["right_tags"], reader),
                "binding_agreement",
            )
        elif op == "contrast_pair":
            rejected, recommended, response = (
                select(candidate, rule[key]) for key in ("rejected", "recommended", "response")
            )
            require(
                rejected in candidate.context and recommended in candidate.context and response in candidate.response,
                "binding_contrast",
            )
            require(rejected.text != recommended.text and response.text == recommended.text, "binding_contrast")
            book_left = citation_for(candidate, rule["book_rejected"])
            book_right = citation_for(candidate, rule["book_recommended"])
            require(
                book_left.source_id == book_right.source_id
                and book_left.table == book_right.table
                and book_left.row_key == book_right.row_key
                and book_left.store == book_right.store,
                "binding_contrast",
            )
            require(book_left.source_id == rule["book_source"], "binding_contrast")
            # Both model-visible members must quote the shared book row as one of their citations.
            require(book_left in rejected.citations and book_right in recommended.citations, "binding_contrast")
            for book, member in ((book_left, rejected), (book_right, recommended)):
                _, witness = reader.field(book)
                require(isinstance(witness, str) and member.text in witness, "binding_contrast")
            for citation in recommended.citations:
                if citation.source_id in {rule["ulif_source"], rule["vesum_source"]}:
                    _, witness = reader.field(citation)
                    require(
                        isinstance(witness, str) and _unstress(witness) == _unstress(recommended.text),
                        "binding_contrast",
                    )
            for selector_name in ("rejected", "recommended"):
                ref = rule[selector_name]
                member = select(candidate, ref)
                agreements.append([{**ref, "citation": i} for i in range(len(member.citations))])
            for key, value in (("rejected_key", rejected), ("recommended_key", recommended)):
                require(operand(candidate, rule[key], reader) == _unstress(value.text), "binding_contrast")
            require(
                {rule["ulif_source"], rule["vesum_source"]} <= {c.source_id for c in recommended.citations},
                "binding_contrast",
            )
            require(rule["sum11_source"] in {c.source_id for c in rejected.citations}, "binding_contrast")
            receipt = reader.row(citation_for(candidate, rule["receipt"]))
            require(
                receipt[rule["pair_field"]] == book_left.row_key
                and receipt[rule["sol_field"]] == "APPROVE"
                and receipt[rule["opus_field"]] == "APPROVE",
                "binding_adjudication",
            )
        else:
            raise BuildError("unknown_binding")
        passed.add(op)
    # A mere mention of a supporting row is insufficient: exact-field
    # agreement must connect it to this value's primary citation (possibly
    # transitively), or the contrast rule must have authenticated its form.
    graph: dict[tuple, set] = {}
    for refs in agreements:
        nodes = []
        for ref in refs:
            citation = citation_for(candidate, ref)
            if "field" not in ref or ref["field"] == citation.field:
                nodes.append((ref["area"], ref["slot"], ref.get("citation", 0)))
        for node in nodes:
            graph.setdefault(node, set()).update(nodes)
    for area in ("slots", "context", "response"):
        for value in getattr(candidate, area):
            reached = {(area, value.slot, 0)}
            pending = list(reached)
            while pending:
                node = pending.pop()
                for neighbor in graph.get(node, set()) - reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
            for index in range(1, len(value.citations)):
                require((area, value.slot, index) in reached, "supporting_unbound")
    return passed
