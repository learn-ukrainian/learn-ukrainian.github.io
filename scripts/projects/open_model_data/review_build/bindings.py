"""Declarative binding-spec.v1 interpreter, independent of candidate extraction.

Selectors: {area: slots|context|response, slot: name, citation: 0,
            field: optional DB column}; absent field selects exact value text.
Rules: equal, same_row, one_group, example_list, contiguous_pages, contrast_pair,
       form_agreement, literal, set_query_equal. Unknown rules fail closed. A component owns the
reviewed spec, not a callable validation hook.
"""

import re
import unicodedata
from itertools import pairwise

from .contract import Candidate, Value
from .errors import BuildError, require
from .snapshot import SnapshotReader
from .transforms import source_text_defects, transform, unresolved_overlaps


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
        require(type(minimum) is int and minimum >= 1, "binding_selector")
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


def _list_punctuation(text: str) -> tuple[dict[int, str], bool]:
    """Scan outer punctuation; apostrophes inside words are never quotes."""
    pairs = {"(": ")", "[": "]", "«": "»", "“": "”", "‘": "’", '"': '"', "'": "'"}
    stack = []
    balanced = True
    punctuation = {}
    for pos, char in enumerate(text):
        if char in "'’" and pos and pos + 1 < len(text) and text[pos - 1].isalpha() and text[pos + 1].isalpha():
            continue
        if stack and char == stack[-1]:
            stack.pop()
        elif char in pairs:
            stack.append(pairs[char])
        elif char in ")]»”":
            if char != ")" or not re.search(r"(?:^|[\s;])(?:\d+|[^\W\d_])$", text[:pos]):
                balanced = False
        elif not stack:
            punctuation[pos] = char
    return punctuation, balanced and not stack


def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def example_regions(text: str) -> list[tuple[int, int]]:
    """Find colon lists, stopping at sentence/rule boundaries and later colons.

    Explicit example introductions can have one item. Other introductions need
    a comma/semicolon list; ambiguous single prose clauses fail closed.
    """
    regions = []
    paragraph_outer, _ = _list_punctuation(text)
    for match in re.finditer(r":", text):
        if match.start() not in paragraph_outer:
            continue
        start = match.end()
        if re.match(r"[ \t]*\n", text[start:]):
            start += re.match(r"[ \t]*\n[ \t]*", text[start:]).end()
        end = len(text)
        outer, _ = _list_punctuation(text[start:])
        numbered = re.match(r"\s*(?:\d+[.)]|[^\W\d_]\))\s", text[start:])
        for stop in re.finditer(r":|\.(?=\s+[^\W\d_])|\n(?=[ \t]*(?:\n|\d+[.)]|§|Rule\b|Правило\b))", text[start:]):
            if stop.start() not in outer:
                continue
            pos = start + stop.start()
            if numbered and stop.group() == "\n" and re.match(r"[ \t]*\d+[.)]\s", text[pos + 1 :]):
                continue
            if stop.group() == ".":
                if numbered:
                    continue
                following = text[pos + 1 :].lstrip()
                if not re.match(r"(?:Rule|Правило)\b", following):
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


def _region_end_ambiguous(text: str, end: int) -> bool:
    """A later colon cannot prove that the preceding example ended."""
    return text[end : end + 1] == ":"


def _lexical_example(text: str) -> bool:
    """A single orthographic item, optionally with balanced printed annotations.

    Multiword unquoted phrases need an explicit item delimiter. No token count
    or guessed syntactic completeness licenses a comma boundary.
    """
    outer, balanced = _list_punctuation(text)
    if not balanced:
        return False
    if any(char in text for char in '«»“”"‘'):
        return False
    visible = "".join(char for pos, char in enumerate(text) if pos in outer)
    # A raw printed word may wrap after its hyphen; do not join its bytes.
    visible = re.sub(r"-\s*\n\s*", "-", visible).strip()
    return bool(re.fullmatch(r"[^\W_][\w\u0300-\u036f'’ʼ-]*", visible))


def _explicit_example_intro(text: str, start: int) -> bool:
    colon = text.rfind(":", 0, start)
    intro_start = max(text.rfind(":", 0, colon), text.rfind("\n", 0, colon)) + 1
    return bool(re.search(r"\b(?:examples?|e\.g|наприклад|як-от)\b", text[intro_start:colon], re.I))


def _quoted_example(text: str) -> bool:
    outer, balanced = _list_punctuation(text)
    return bool(text and balanced and not outer and text[0] in "«“\"'‘" and text[-1] in "»”\"'’")


def _annotation_role_ambiguous(text: str) -> bool:
    """Capitalized parenthetical labels may cite a larger printed example.

    Flat paragraph text does not retain the typography distinguishing an author
    label from a lexical annotation. Withhold the entire colon region: earlier
    semicolon groups can also belong to the same cited sentence.
    """
    return any(any(char.isupper() for char in match.group()) for match in re.finditer(r"\([^)]*\)", text))


def example_boundaries(text: str) -> list[tuple[tuple[int, int], str]]:
    """Enumerate safe examples and unresolved list spans without editing text.

    Semicolons delimit groups. Within a group, explicit numbered/lettered items
    own their internal commas. Otherwise comma-separated items must each be
    lexical examples. Balanced outer quotes delimit one printed example. An
    unresolved group is counted once and withheld, never emitted as fragments.
    """
    items = []
    for start, end in example_regions(text):
        outer, balanced = _list_punctuation(text[start:end])
        if not balanced or _annotation_role_ambiguous(text[start:end]):
            items.append((_trim_span(text, start, end), "example_boundary_ambiguous"))
            continue
        separators = [start - 1, *(start + p for p, c in outer.items() if c == ";"), end]
        for left, right in pairwise(separators):
            a, b = _trim_span(text, left + 1, right)
            if a == b:
                continue
            if right == end and _region_end_ambiguous(text, end):
                items.append(((a, b), "example_boundary_ambiguous"))
                continue
            part = text[a:b]
            punctuation, _ = _list_punctuation(part)
            markers = [
                m
                for m in re.finditer(r"(?m)(?:^|\n)[ \t]*(?:\d+[.)]|[^\W\d_]\))\s+", part)
                if m.start() == 0 or m.start() in punctuation
            ]
            if markers and markers[0].start() == 0:
                for index, marker in enumerate(markers):
                    limit = markers[index + 1].start() if index + 1 < len(markers) else len(part)
                    span = _trim_span(text, a + marker.end(), a + limit)
                    if span[0] < span[1]:
                        content = text[slice(*span)]
                        inner, _ = _list_punctuation(content)
                        comma_parts = content.split(",")
                        # Numbering alone also occurs in rule conditions and in
                        # groups containing multiple examples. Neither proves
                        # that a prose span is exactly one printed example.
                        atomic_list = len(comma_parts) > 1 and all(_lexical_example(p.strip()) for p in comma_parts)
                        explicit = _explicit_example_intro(text, start)
                        one = (
                            _lexical_example(content)
                            or _quoted_example(content)
                            or (explicit and not atomic_list and any(char.isalpha() for char in inner.values()))
                        )
                        items.append((span, "ok" if one else "example_boundary_ambiguous"))
                continue
            commas = [p for p, c in punctuation.items() if c == ","]
            cuts = [-1, *commas, len(part)]
            spans = [_trim_span(text, a + l + 1, a + r) for l, r in pairwise(cuts)]
            if all(l < r and _lexical_example(text[l:r]) for l, r in spans):
                items.extend((span, "ok") for span in spans)
            elif not commas and _quoted_example(part):
                items.append(((a, b), "ok"))
            else:
                items.append(((a, b), "example_boundary_ambiguous"))
    return items


def example_items(text: str) -> list[tuple[int, int]]:
    """All independently counted units, including unresolved list groups."""
    return [span for span, _ in example_boundaries(text)]


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
        # Authenticate source column and locator for every expanded witness.
        for ref in selectors:
            citation = citation_for(candidate, ref)
            if "citation_field" in rule:
                require(citation.field == rule["citation_field"], "binding_field")
            if "locator_field" in rule:
                row = reader.row(citation)
                require(
                    rule["locator_field"] in row and citation.locator == row[rule["locator_field"]],
                    "binding_locator",
                )
        if op == "equal":
            operands = [operand(candidate, s, reader) for s in selectors]
            require(len(operands) >= 2 and all(o == operands[0] for o in operands), "binding_equal")
            agreements.append(selectors)
        elif op == "literal":
            require(
                bool(selectors) and all(operand(candidate, ref, reader) == rule["expected"] for ref in selectors),
                "binding_literal",
            )
        elif op == "set_query_equal":
            require(bool(selectors) and bool(rule.get("queries")), "binding_set")
            normalizer = rule["normalizer"]
            expected = {normalize(operand(candidate, ref, reader), normalizer) for ref in selectors}
            for definition in rule["queries"]:
                query = dict(definition["query"])
                query["parameters"] = [operand(candidate, ref, reader) for ref in definition.get("parameters", [])]
                actual = {normalize(value, normalizer) for value in reader.query_values(query)}
                require(actual == expected, "binding_set")
        elif op == "same_row":
            citations = [citation_for(candidate, s) for s in selectors]
            require(len(citations) >= 2 and len({(c.store, c.table, c.row_key) for c in citations}) == 1, "binding_row")
        elif op == "one_group":
            operands = [operand(candidate, s, reader) for s in selectors]
            require(bool(operands) and all(o is not None and o == operands[0] for o in operands), "binding_group")
        elif op == "pattern_absent":
            require(
                bool(selectors) and isinstance(rule.get("pattern"), str) and bool(rule["pattern"]), "binding_pattern"
            )
            require(
                all(re.search(rule["pattern"], operand(candidate, ref, reader)) is None for ref in selectors),
                "binding_pattern",
            )
        elif op == "transform_resolved":
            require(bool(selectors) and rule.get("transform") == "dehyphenate@2", "binding_transform")
            policy = policies.get(rule["transform"])
            require(isinstance(policy, dict), "transform_policy")
            for ref in selectors:
                _, field = reader.field(citation_for(candidate, ref))
                resolved = transform(rule["transform"], field, policy, reader)
                require(not unresolved_overlaps(resolved, select(candidate, ref).span), "binding_hyphenation")
                require(
                    not source_text_defects(resolved.text, policy, reader, original=field), "binding_source_text_defect"
                )
        elif op == "whole_field":
            require(bool(selectors), "binding_whole_field")
            for ref in selectors:
                value = select(candidate, ref)
                require(ref.get("citation", 0) == 0 and "field" not in ref, "binding_whole_field")
                _, field = reader.field(value.citations[0])
                require(isinstance(field, str) and value.span is None, "binding_whole_field")
                require(
                    value.text == transform(value.transform, field, policies.get(value.transform), reader).text,
                    "binding_whole_field",
                )
        elif op == "example_list":
            require(len(selectors) == 1, "binding_example")
            value = select(candidate, selectors[0])
            citation = value.citations[0]
            _, field = reader.field(citation)
            require(isinstance(field, str) and value.span is not None, "binding_example")
            source = transform(value.transform, field, policies.get(value.transform), reader).text
            require(
                (value.span, "ok") in example_boundaries(source),
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
