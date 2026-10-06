"""Declarative binding-spec.v1 interpreter, independent of candidate extraction.

Selectors: {area: slots|context|response, slot: name, citation: 0,
            field: optional DB column}; absent field selects exact value text.
Rules: equal, same_row, one_group, example_list, contiguous_pages, contrast_pair,
       form_agreement, literal, set_query_equal, sequence_query_equal. Unknown rules fail closed. A component owns the
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
    if "index" in selector:
        index = selector["index"]
        require(type(index) is int and 0 <= index < len(matches), "binding_selector")
        return matches[index]
    require(len(matches) == 1, "binding_selector")
    return matches[0]


def expand(candidate: Candidate, selector: dict) -> list[dict]:
    """Expand declared multi-values/citations to concrete, identity-bearing refs."""
    require(selector.get("area") in {"slots", "context", "response"}, "binding_selector")
    require(selector.get("match", "one") in {"one", "all"}, "binding_selector")
    if selector.get("match") == "all":
        require("index" not in selector, "binding_selector")
        minimum = selector.get("min", 1)
        require(type(minimum) is int and minimum >= 0, "binding_selector")
        matches = [v for v in getattr(candidate, selector["area"]) if v.slot == selector["slot"]]
        require(len(matches) >= minimum, "binding_selector")
        refs = [{**selector, "index": i} for i in range(len(matches))]
    else:
        select(candidate, selector)
        refs = [dict(selector)]
    result = []
    for ref in refs:
        ref.pop("match", None)
        ref.pop("min", None)
        if ref.get("citation") == "all":
            minimum = ref.pop("citation_min", 1)
            citations = select(candidate, ref).citations
            require(type(minimum) is int and minimum >= 1 and len(citations) >= minimum, "binding_selector")
            result.extend({**ref, "citation": i} for i in range(len(citations)))
        else:
            result.append(ref)
    return result


def citation_for(candidate: Candidate, selector: dict):
    value = select(candidate, selector)
    index = selector.get("citation", 0)
    require(type(index) is int and 0 <= index < len(value.citations), "binding_selector")
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
    """Find colon lists, stopping at sentence/rule boundaries and later colons.

    Explicit example introductions can have one item. Other introductions need
    a comma/semicolon list; ambiguous single prose clauses fail closed.
    """
    regions = []
    for match in re.finditer(r":", text):
        start = match.end()
        if re.match(r"[ \t]*\n", text[start:]):
            start += re.match(r"[ \t]*\n[ \t]*", text[start:]).end()
        end = len(text)
        for stop in re.finditer(r":|\.(?=\s+[^\W\d_])|\n(?=[ \t]*(?:\n|\d+[.)]|§|Rule\b|Правило\b))", text[start:]):
            pos = start + stop.start()
            if stop.group() == ".":
                following = text[pos + 1 :].lstrip()
                if not following or not following[0].isupper():
                    continue
            end = pos
            break
        intro_start = max(text.rfind(":", 0, match.start()), text.rfind("\n", 0, match.start())) + 1
        intro = text[intro_start : match.start()]
        body = text[start:end].rstrip().rstrip(".")
        explicit = re.search(r"\b(?:examples?|e\.g|наприклад|як-от)\b", intro, re.I)
        if explicit or re.search(r"[,;]", body):
            regions.append((start, start + len(body)))
    return regions


def example_items(text: str) -> list[tuple[int, int]]:
    items = []
    for start, end in example_regions(text):
        for match in re.finditer(r"[^,;]+", text[start:end]):
            raw = match.group()
            left = start + match.start() + len(raw) - len(raw.lstrip())
            right = start + match.end() - len(raw) + len(raw.rstrip())
            if left < right:
                items.append((left, right))
    return items


def whole_token(form: str, witness: str) -> bool:
    # Apostrophes and combining marks belong to the token, even where Python's
    # Unicode \w alone would split them. No stored/source bytes are changed.
    for match in re.finditer(re.escape(form), witness):
        neighbors = witness[max(0, match.start() - 1) : match.start()] + witness[match.end() : match.end() + 1]
        if not any(c.isalnum() or c == "_" or c in "'’ʼ" or unicodedata.category(c).startswith("M") for c in neighbors):
            return True
    return False


def _unstress(text: str) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", text).replace("\u0301", ""))


def normalize(text: str, name: str) -> str:
    require(name in {"identity", "unstress_nfc"}, "binding_normalizer")
    require(isinstance(text, str), "binding_set")
    return _unstress(text) if name == "unstress_nfc" else text


def node_for(candidate: Candidate, ref: dict) -> tuple:
    # Repeated slots must not alias each other's supporting-citation evidence.
    matches = [v for v in getattr(candidate, ref["area"]) if v.slot == ref["slot"]]
    index = ref.get("index", 0)
    require(index < len(matches), "binding_selector")
    return ref["area"], ref["slot"], index, ref.get("citation", 0)


def check(candidate: Candidate, spec: dict, reader: SnapshotReader, policies: dict) -> set[str]:
    require(spec.get("schema") == "binding-spec.v1" and bool(spec.get("rules")), "binding_spec")
    passed = set()
    agreements: list[list[dict]] = []
    for rule in spec["rules"]:
        op = rule["op"]
        selectors = [ref for s in rule.get("values", []) for ref in expand(candidate, s)]
        if op == "equal":
            operands = [operand(candidate, s, reader) for s in selectors]
            require(len(operands) >= 2 and all(o == operands[0] for o in operands), "binding_equal")
            agreements.append(selectors)
        elif op == "literal":
            require(
                bool(selectors) and all(operand(candidate, ref, reader) == rule["expected"] for ref in selectors),
                "binding_literal",
            )
        elif op in {"set_query_equal", "sequence_query_equal"}:
            # An explicitly optional repeated slot may represent the empty set.
            # Every independent query must then also be empty; omission cannot
            # hide held source values. Scalar selectors remain mandatory.
            optional = any(s.get("match") == "all" and s.get("min") == 0 for s in rule.get("values", []))
            require((bool(selectors) or optional) and bool(rule.get("queries")), "binding_set")
            normalizer = rule["normalizer"]
            expected = [normalize(operand(candidate, ref, reader), normalizer) for ref in selectors]
            for definition in rule["queries"]:
                query = dict(definition["query"])
                query["parameters"] = [operand(candidate, ref, reader) for ref in definition.get("parameters", [])]
                actual = [normalize(value, normalizer) for value in reader.query_values(query)]
                if op == "set_query_equal":
                    require(set(actual) == set(expected), "binding_set")
                else:
                    require(actual == expected, "binding_sequence")
        elif op == "same_row":
            citations = [citation_for(candidate, s) for s in selectors]
            require(len(citations) >= 2 and len({(c.store, c.table, c.row_key) for c in citations}) == 1, "binding_row")
        elif op == "one_group":
            operands = [operand(candidate, s, reader) for s in selectors]
            require(bool(operands) and all(o is not None and o == operands[0] for o in operands), "binding_group")
        elif op == "example_list":
            require(len(selectors) == 1, "binding_example")
            value = select(candidate, selectors[0])
            citation = value.citations[0]
            _, field = reader.field(citation)
            require(isinstance(field, str) and value.span is not None, "binding_example")
            source = transform(value.transform, field, policies.get(value.transform), reader).text
            require(
                value.span in example_items(source),
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
            for selector_name, book in (("rejected", book_left), ("recommended", book_right)):
                ref = rule[selector_name]
                member = select(candidate, ref)
                confirmed = []
                for index, citation in enumerate(member.citations):
                    _, witness = reader.field(citation)
                    if citation == book:
                        require(isinstance(witness, str) and whole_token(member.text, witness), "binding_contrast")
                    elif (selector_name == "rejected" and citation.source_id == rule["sum11_source"]) or (
                        selector_name == "recommended"
                        and citation.source_id in {rule["ulif_source"], rule["vesum_source"]}
                    ):
                        require(
                            isinstance(witness, str) and _unstress(witness) == _unstress(member.text),
                            "binding_contrast",
                        )
                    else:
                        continue
                    confirmed.append({**ref, "citation": index})
                agreements.append(confirmed)
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
                nodes.append(node_for(candidate, ref))
        for node in nodes:
            graph.setdefault(node, set()).update(nodes)
    for area in ("slots", "context", "response"):
        occurrences = {}
        for value in getattr(candidate, area):
            index = occurrences.get(value.slot, 0)
            occurrences[value.slot] = index + 1
            reached = {(area, value.slot, index, 0)}
            pending = list(reached)
            while pending:
                node = pending.pop()
                for neighbor in graph.get(node, set()) - reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
            for citation_index in range(1, len(value.citations)):
                require((area, value.slot, index, citation_index) in reached, "supporting_unbound")
    return passed
