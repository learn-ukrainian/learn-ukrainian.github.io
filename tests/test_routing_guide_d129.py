"""Regression check for operator decision D-129 (#10464).

No Claude model reviews through Cursor. The catalog keeps Opus on the native
Claude CLI; these guides must not offer that review on a Cursor route.

A unit is one markdown table row, or one paragraph of consecutive non-blank
lines. Table cells are instruction contexts, and the row carries review
context: a review or advisor word in any cell applies to every Cursor
invocation in that row. In prose, an instruction is one sentence. Breaks are
sentence-ending punctuation followed by whitespace, and a hard line break that
starts a new list item. A wrapped line stays in its sentence, and a break
never falls inside a backtick span.

An invocation is a backtick span, or the unspanned text between spans, that
contains ``--agent cursor`` or ``--agent=cursor``. Its pin is the ``--model``
value in that same span, in either flag order. Otherwise the pin is the
nearest backticked bare model id in the instruction. An invocation with no pin
is unpinned. A non-Claude pin clears only that invocation.

The invocation offends when its sentence or table row is review context and
its pin is a Claude model (``claude-*``, or a token containing ``opus`` or
``sonnet``). An unpinned invocation offends in that same context when the
sentence, or any cell of the table row, names Claude, Opus, or Sonnet.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Globs repository guide trees, so the module is registered in
# tests/test_repo_wide_marker_invariant.py.
pytestmark = pytest.mark.repo_wide

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "agents_extensions" / "shared" / "rules" / "fleet-driver-routing.md"

_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_LIST_MARKER = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
_CURSOR_AGENT = re.compile(r"--agent(?:=|\s+)cursor\b", re.IGNORECASE)
_MODEL_FLAG = re.compile(r"--model(?:=|\s+)(?P<model>[^\s`]+)", re.IGNORECASE)
_BARE_BACKTICK = re.compile(r"`([^`\s]+)`")
_BARE_MODEL_ID = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9.]+)+")
# Union of origin/main _REVIEW_WORDS (review, reviews, reviewer, reviewers,
# cross-family, CF) and the advisor words. One constant feeds the detector
# and the term table.
_REVIEW_CONTEXT_TERMS = (
    "review",
    "reviews",
    "reviewer",
    "reviewers",
    "cross-family",
    "CF",
    "advisor",
    "advisors",
    "advisory",
)
_REVIEW_CONTEXT_WORDS = re.compile(
    r"\b(?:" + "|".join(re.escape(term) for term in _REVIEW_CONTEXT_TERMS) + r")\b",
    re.IGNORECASE,
)
_NATIVE_CLAUDE_OR_CURSOR_SLUG = re.compile(
    r"native\s+Claude\s+or\s+verified\s+Cursor\s+slug",
    re.IGNORECASE,
)
_CURSOR_SLUG = re.compile(r"\bCursor\s+slug\b", re.IGNORECASE)
_CLAUDE_NAME = re.compile(r"\b(?:Claude|Opus|Sonnet)\b|\bclaude-[a-z0-9]", re.IGNORECASE)
_CLAUDE_POOL_ROW = re.compile(r"^\|\s*Claude (Sonnet|Opus|Fable)\b", re.IGNORECASE)
_NOT_REVIEW_ROUTE = "not a review route (D-129)"

_WRAPPED_REVIEW = "For a formal review, use\n`--agent cursor --model claude-sonnet-5-5-high`"
_EQUALS_FORM = "For a formal review, pass `--agent=cursor --model claude-opus-5-5`."
_EQUALS_NAMED_MODEL = "For a formal review, pass `--agent=cursor` with `claude-sonnet-5-5-high`."
_MIXED_COMMAND = (
    "For a formal review, use `--agent cursor --model grok-4.7-high` or `--agent=cursor` with `claude-sonnet-5-5-high`."
)
_TABLE_SLUG = (
    "| **Claude Opus 5.5** | deep code review and hard advisory judgment "
    "| Anthropic / native Claude or verified Cursor slug |"
)
_GROK_REVIEW = "For code review, use `--agent cursor --model grok-4.7-high`."
_RESOLVER_PICK = "For cross-family review of a Grok author, use the resolver non-xAI pick."
_PROHIBITION = "No Claude model reviews through Cursor (D-129, #10464)."
_GROK_BESIDE_OPUS = (
    "Review admission: `claude-fable-5-1` holds no review role. "
    "Grok 4.7 reviews through Cursor `--agent cursor --model grok-4.7-high`. "
    "Route execution-dependent reviews to Opus 5.5."
)

POSITIVE_EXAMPLES = (_WRAPPED_REVIEW, _EQUALS_FORM, _EQUALS_NAMED_MODEL, _MIXED_COMMAND, _TABLE_SLUG)
NEGATIVE_EXAMPLES = (_GROK_REVIEW, _RESOLVER_PICK, _PROHIBITION, _GROK_BESIDE_OPUS)


def split_units(text: str) -> list[tuple[int, str]]:
    """Return ``(start_line, text)`` for each table row and joined paragraph."""
    units: list[tuple[int, str]] = []
    paragraph: list[str] = []
    start: int | None = None

    def flush() -> None:
        nonlocal start
        if start is not None and paragraph:
            # Keep hard breaks so a later list item is not glued into this sentence.
            units.append((start, "\n".join(paragraph)))
        paragraph.clear()
        start = None

    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            flush()
            continue
        if _TABLE_ROW.match(line):
            flush()
            units.append((number, line.strip()))
            continue
        if start is None:
            start = number
        paragraph.append(line.strip())
    flush()
    return units


def _normalize_model(raw: str) -> str:
    return raw.strip().strip("`").rstrip(".,;:)")


def _pin_is_claude(model: str) -> bool:
    token = _normalize_model(model)
    if re.match(r"claude-", token, re.IGNORECASE):
        return True
    return re.search(r"opus|sonnet", token, re.IGNORECASE) is not None


def _is_table_row(unit: str) -> bool:
    return "\n" not in unit and _TABLE_ROW.match(unit) is not None


def _table_cells(row: str) -> list[str]:
    body = row.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    for char in body:
        if char == "`":
            in_code = not in_code
            current.append(char)
        elif char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return [cell for cell in cells if cell]


def _mask_code_spans(text: str) -> tuple[str, list[str]]:
    """Replace backtick spans so sentence breaks cannot fall inside them."""
    spans: list[str] = []
    parts: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "`":
            next_tick = text.find("`", index)
            if next_tick == -1:
                parts.append(text[index:])
                break
            parts.append(text[index:next_tick])
            index = next_tick
            continue
        end = text.find("`", index + 1)
        if end == -1:
            parts.append(text[index:])
            break
        spans.append(text[index : end + 1])
        parts.append(f"\x00{len(spans) - 1}\x00")
        index = end + 1
    return "".join(parts), spans


def _unmask(text: str, spans: list[str]) -> str:
    return re.sub(r"\x00(\d+)\x00", lambda match: spans[int(match.group(1))], text)


def _prose_instructions(unit: str) -> list[str]:
    masked, spans = _mask_code_spans(unit)
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in masked.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if current and _LIST_MARKER.match(stripped):
            blocks.append(current)
            current = [stripped]
        else:
            current.append(stripped)
    if current:
        blocks.append(current)
    instructions: list[str] = []
    for block in blocks:
        joined = " ".join(block)
        for piece in re.split(r"(?<=[.!?])\s+", joined):
            text = _unmask(piece, spans).strip()
            if text:
                instructions.append(text)
    return instructions


def _located_runs(instruction: str) -> list[tuple[int, int, str]]:
    """Backtick spans and the unspanned gaps between them, with absolute offsets."""
    runs: list[tuple[int, int, str]] = []
    index = 0
    length = len(instruction)
    while index < length:
        if instruction[index] == "`":
            end = instruction.find("`", index + 1)
            if end == -1:
                runs.append((index, length, instruction[index:]))
                break
            runs.append((index, end + 1, instruction[index : end + 1]))
            index = end + 1
            continue
        end = instruction.find("`", index)
        if end == -1:
            end = length
        if end > index:
            runs.append((index, end, instruction[index:end]))
        index = end
    return runs


def _models_in_run(text: str, agents: list[re.Match[str]]) -> dict[int, str]:
    """Pair each ``--model`` in this run with the nearest ``--agent cursor``."""
    models = list(_MODEL_FLAG.finditer(text))
    pairs: list[tuple[int, int, re.Match[str]]] = []
    for model in models:
        for agent in agents:
            pairs.append((abs(model.start() - agent.start()), agent.start(), model))
    pairs.sort(key=lambda item: (item[0], item[1], item[2].start()))
    assigned: dict[int, str] = {}
    used_models: set[int] = set()
    used_agents: set[int] = set()
    for _distance, agent_at, model in pairs:
        if agent_at in used_agents or model.start() in used_models:
            continue
        assigned[agent_at] = _normalize_model(model.group("model"))
        used_agents.add(agent_at)
        used_models.add(model.start())
    return assigned


def _bare_models(instruction: str) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    for match in _BARE_BACKTICK.finditer(instruction):
        token = match.group(1)
        if _BARE_MODEL_ID.fullmatch(token) and re.search(r"\d", token):
            found.append((match.start(), match.end(), token))
    return found


def _nearest_bare(agent_at: int, bares: list[tuple[int, int, str]]) -> str | None:
    best: tuple[int, int, str] | None = None
    for start, end, model in bares:
        if start <= agent_at < end:
            continue
        distance = abs(agent_at - start)
        if best is None or distance < best[0] or (distance == best[0] and start < best[1]):
            best = (distance, start, model)
    return None if best is None else best[2]


def _invocation_pins(instruction: str) -> list[str | None]:
    """One pin per Cursor invocation. ``None`` means the invocation is unpinned.

    A ``--model`` value inside another invocation's command span is not a bare
    model id, so it cannot become this invocation's pin.
    """
    located: list[tuple[int, str | None]] = []
    for start, _end, text in _located_runs(instruction):
        agents = list(_CURSOR_AGENT.finditer(text))
        if not agents:
            continue
        assigned = _models_in_run(text, agents)
        for agent in agents:
            located.append((start + agent.start(), assigned.get(agent.start())))
    if not located:
        return []
    bares = _bare_models(instruction)
    return [model if model is not None else _nearest_bare(agent_at, bares) for agent_at, model in located]


def _instruction_offends(instruction: str, review: bool, name_scope: str) -> bool:
    if not review:
        return False
    for pin in _invocation_pins(instruction):
        if pin is None:
            if _CLAUDE_NAME.search(name_scope):
                return True
        elif _pin_is_claude(pin):
            return True
    return False


def _command_offers_claude_review(unit: str) -> bool:
    if _is_table_row(unit):
        cells = _table_cells(unit)
        # The row, not the cell, carries review context. An unpinned invocation
        # still sees Claude/Opus/Sonnet named in another cell of that row.
        review = any(_REVIEW_CONTEXT_WORDS.search(cell) for cell in cells)
        return any(_instruction_offends(cell, review, unit) for cell in cells)
    return any(
        _instruction_offends(instruction, _REVIEW_CONTEXT_WORDS.search(instruction) is not None, instruction)
        for instruction in _prose_instructions(unit)
    )


def _slug_offers_claude_review(unit: str) -> bool:
    if _NATIVE_CLAUDE_OR_CURSOR_SLUG.search(unit):
        return True
    return bool(_CURSOR_SLUG.search(unit) and _CLAUDE_NAME.search(unit) and _REVIEW_CONTEXT_WORDS.search(unit))


def offers_claude_review_through_cursor(unit: str) -> bool:
    return _command_offers_claude_review(unit) or _slug_offers_claude_review(unit)


def _guarded_files() -> list[Path]:
    rules = sorted((ROOT / "agents_extensions" / "shared" / "rules").glob("*.md"))
    references = sorted((ROOT / "agents_extensions" / "shared" / "skills" / "drive-epic" / "references").glob("*.md"))
    return [
        *rules,
        ROOT / "docs" / "best-practices" / "fleet-role-scorecard.md",
        ROOT / "docs" / "best-practices" / "agent-activity-matrix.md",
        *references,
    ]


def _offenders(text: str) -> list[tuple[int, str]]:
    return [(number, unit) for number, unit in split_units(text) if offers_claude_review_through_cursor(unit)]


@pytest.mark.parametrize("sample", POSITIVE_EXAMPLES)
def test_positive_examples_are_flagged(sample: str) -> None:
    assert _offenders(sample), sample


def test_wrapped_command_is_caught_only_as_one_paragraph() -> None:
    lines = _WRAPPED_REVIEW.splitlines()
    assert len(lines) == 2
    assert not any(offers_claude_review_through_cursor(line) for line in lines)
    units = split_units(_WRAPPED_REVIEW)
    assert len(units) == 1
    assert offers_claude_review_through_cursor(units[0][1])


def test_table_row_stays_separate_from_neighboring_paragraphs() -> None:
    text = f"{_RESOLVER_PICK}\n{_TABLE_SLUG}\n{_PROHIBITION}\n"
    units = [unit for _, unit in split_units(text)]
    assert units == [_RESOLVER_PICK, _TABLE_SLUG, _PROHIBITION]
    assert [offers_claude_review_through_cursor(unit) for unit in units] == [False, True, False]


@pytest.mark.parametrize("sample", NEGATIVE_EXAMPLES)
def test_negative_examples_pass(sample: str) -> None:
    assert not _offenders(sample), sample


def test_guarded_set_includes_the_named_documents() -> None:
    rels = {path.relative_to(ROOT).as_posix() for path in _guarded_files()}
    assert {
        "agents_extensions/shared/rules/fleet-driver-routing.md",
        "agents_extensions/shared/rules/model-assignment.md",
        "docs/best-practices/fleet-role-scorecard.md",
        "docs/best-practices/agent-activity-matrix.md",
        "agents_extensions/shared/skills/drive-epic/references/routing-and-dispatch.md",
    } <= rels
    assert all(path.is_file() for path in _guarded_files())


def test_guarded_docs_do_not_offer_claude_review_through_cursor() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}:{number}: {unit[:240]}"
        for path in _guarded_files()
        for number, unit in _offenders(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, "D-129: no Claude model reviews through Cursor; offending units:\n" + "\n".join(offenders)


def test_grok_author_review_does_not_name_an_other_models_slug() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    assert "Other Models slug" not in text


def test_claude_rows_of_the_other_models_pool_are_marked_not_a_review_route() -> None:
    rows = [
        (number, line)
        for number, line in enumerate(GUIDE.read_text(encoding="utf-8").splitlines(), start=1)
        if _CLAUDE_POOL_ROW.match(line)
    ]
    assert rows, "expected Claude rows in the Other Models price table"
    unmarked = [f"{number}: {line.strip()}" for number, line in rows if _NOT_REVIEW_ROUTE not in line]
    assert not unmarked, f"Claude pool rows must say '{_NOT_REVIEW_ROUTE}':\n" + "\n".join(unmarked)


def test_guide_states_the_resolver_decides_review_of_a_grok_author() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    assert "D-129" in text
    assert re.search(r"reviewer resolver'?s? non-xAI pick", text)


_MERGED_REVIEW_WORDS = re.compile(
    r"\b(?:review|reviews|reviewer|reviewers|cross-family|CF)\b",
    re.IGNORECASE,
)
_MERGED_CURSOR_AGENT = re.compile(r"--agent(?:=|\s+)cursor\b", re.IGNORECASE)
_MERGED_CLAUDE_MODEL = re.compile(r"\bclaude-[a-z0-9]")

_MODEL_BEFORE_AGENT = "For formal review, use `--model claude-opus-5-5 --agent cursor`."
_TABLE_CLAUDE_CELL = "| Claude Opus 5.5 | Formal review | `--agent cursor` |"
_REVIEW_THEN_CODING = (
    "For formal review, use `--agent cursor --model grok-4.7-high`. "
    "For coding, use `--agent cursor --model claude-sonnet-5-5-high`."
)
_CODING_THEN_REVIEW = (
    "For coding, use `--agent cursor --model claude-sonnet-5-5-high`. "
    "For formal review, use `--agent cursor --model grok-4.7-high`."
)
_REVIEW_CLAUDE_THEN_CODING_GROK = (
    "For formal review, use `--agent cursor --model claude-opus-5-5`. "
    "For coding, use `--agent cursor --model grok-4.7-high`."
)
_CF_REVIEW = "For formal CF, use `--agent cursor --model claude-opus-5-5`."
_CROSS_FAMILY_REVIEW = "For cross-family, use `--agent cursor --model claude-sonnet-5-5-high`."
_LIST_ITEM_BOUNDARY = (
    "- For formal review, use `--agent cursor --model grok-4.7-high`\n"
    "- For coding, use `--agent cursor --model claude-sonnet-5-5-high`\n"
)
_WRAPPED_LIST_ITEM = "- For a formal review, use\n  `--agent cursor --model claude-sonnet-5-5-high`\n"

# Intentional narrowings versus origin/main's line detector. A Claude token and
# a review word share the line, but they are not this invocation's pin. The
# valid coding-sentence case is the stopping rule's narrowing; the other
# entries are the same rule (a neighboring sentence's Claude token, or the
# reverse order).
_INTENTIONAL_NARROWINGS: dict[str, str] = {
    _REVIEW_THEN_CODING: (
        "valid coding sentence: its Claude pin is not in the review sentence, "
        "whose Cursor invocation is pinned to grok-4.7-high"
    ),
    _CODING_THEN_REVIEW: (
        "valid coding sentence: its Claude pin precedes the review sentence, "
        "whose Cursor invocation is pinned to grok-4.7-high and does not reach backward"
    ),
    _GROK_BESIDE_OPUS: (
        "valid grok review pin: claude-fable-5-1 is a different sentence and is "
        "not the Cursor invocation's --model value"
    ),
}

_FLAG_ORDERS = ("agent-first", "model-first")
_SEPARATORS = ("space", "=")
_SPAN_KINDS = ("one-span", "separate-model")
_PIN_MODELS = ("claude-opus-5-5", "claude-sonnet-5-5-high", "grok-4.7-high")
_CASE_CONTEXTS = ("review-sentence", "coding-sentence", "review-row", "plain-row")
_SEPARATOR_IDS = {"space": "sp", "=": "eq"}


def _merged_detector(text: str) -> bool:
    """origin/main line detector, plus the ``--agent=cursor`` form.

    A line offends when it contains a Cursor agent flag, a ``claude-`` model
    token, and a merged ``_REVIEW_WORDS`` match. Advisor words are not part of
    that merged set.
    """
    for line in text.splitlines():
        if (
            _MERGED_CURSOR_AGENT.search(line)
            and _MERGED_CLAUDE_MODEL.search(line)
            and _MERGED_REVIEW_WORDS.search(line)
        ):
            return True
    return False


def _render_invocation(order: str, separator: str, span: str, model: str) -> str:
    if separator == "space":
        agent = "--agent cursor"
        model_flag = f"--model {model}"
    else:
        agent = "--agent=cursor"
        model_flag = f"--model={model}"
    if span == "one-span":
        inner = f"{agent} {model_flag}" if order == "agent-first" else f"{model_flag} {agent}"
        return f"`{inner}`"
    if order == "agent-first":
        return f"`{agent}` with `{model}`"
    return f"`{model}` with `{agent}`"


def _render_case(order: str, separator: str, span: str, model: str, context: str) -> str:
    rendered = _render_invocation(order, separator, span, model)
    if context == "review-sentence":
        return f"For formal review, use {rendered}."
    if context == "coding-sentence":
        return f"For coding, use {rendered}."
    if context == "review-row":
        return f"| task | Formal review | {rendered} |"
    return f"| task | coding work | {rendered} |"


def _expects_offender(model: str, context: str) -> bool:
    in_review = context in {"review-sentence", "review-row"}
    claude = model.startswith("claude-") or "opus" in model or "sonnet" in model
    return in_review and claude


class _Case:
    def __init__(self, case_id: str, text: str, offender: bool) -> None:
        self.case_id = case_id
        self.text = text
        self.offender = offender


_INVOCATION_CASES = [
    _Case(
        case_id=f"{order}-{_SEPARATOR_IDS[separator]}-{span}-{model}-{context}",
        text=_render_case(order, separator, span, model, context),
        offender=_expects_offender(model, context),
    )
    for order in _FLAG_ORDERS
    for separator in _SEPARATORS
    for span in _SPAN_KINDS
    for model in _PIN_MODELS
    for context in _CASE_CONTEXTS
]


def _monotonicity_corpus() -> list[str]:
    samples = [
        *POSITIVE_EXAMPLES,
        *NEGATIVE_EXAMPLES,
        _MODEL_BEFORE_AGENT,
        _TABLE_CLAUDE_CELL,
        _REVIEW_THEN_CODING,
        _CODING_THEN_REVIEW,
        _REVIEW_CLAUDE_THEN_CODING_GROK,
        _CF_REVIEW,
        _CROSS_FAMILY_REVIEW,
        _LIST_ITEM_BOUNDARY,
        _WRAPPED_LIST_ITEM,
    ]
    samples.extend(
        f"For formal {term}, use `--agent cursor --model claude-opus-5-5`." for term in _REVIEW_CONTEXT_TERMS
    )
    samples.extend(case.text for case in _INVOCATION_CASES)
    return samples


def test_model_before_agent_is_bound_to_the_invocation() -> None:
    assert offers_claude_review_through_cursor(_MODEL_BEFORE_AGENT)


def test_table_row_claude_cell_binds_an_unpinned_cursor_invocation() -> None:
    assert offers_claude_review_through_cursor(_TABLE_CLAUDE_CELL)


def test_review_sentence_does_not_paint_the_following_coding_sentence() -> None:
    assert not offers_claude_review_through_cursor(_REVIEW_THEN_CODING)
    assert not offers_claude_review_through_cursor(_CODING_THEN_REVIEW)
    assert offers_claude_review_through_cursor(_REVIEW_CLAUDE_THEN_CODING_GROK)


def test_cf_and_cross_family_are_review_context() -> None:
    assert offers_claude_review_through_cursor(_CF_REVIEW)
    assert offers_claude_review_through_cursor(_CROSS_FAMILY_REVIEW)


def test_list_item_break_does_not_carry_review_context() -> None:
    assert not _offenders(_LIST_ITEM_BOUNDARY)
    units = split_units(_WRAPPED_LIST_ITEM)
    assert len(units) == 1
    assert offers_claude_review_through_cursor(units[0][1])


@pytest.mark.parametrize("term", _REVIEW_CONTEXT_TERMS)
def test_each_review_context_term_flags_a_claude_cursor_invocation(term: str) -> None:
    sample = f"For formal {term}, use `--agent cursor --model claude-opus-5-5`."
    assert offers_claude_review_through_cursor(sample), term


@pytest.mark.parametrize("case", _INVOCATION_CASES, ids=lambda case: case.case_id)
def test_invocation_cross_product(case: _Case) -> None:
    got = offers_claude_review_through_cursor(case.text)
    assert got is case.offender, f"{case.case_id}: {case.text}"


def test_guard_is_monotonic_with_the_merged_line_detector() -> None:
    weakenings: list[str] = []
    for sample in _monotonicity_corpus():
        if sample in _INTENTIONAL_NARROWINGS:
            continue
        if _merged_detector(sample) and not offers_claude_review_through_cursor(sample):
            weakenings.append(sample)
    assert not weakenings, "new guard is weaker than origin/main on:\n" + "\n".join(weakenings)
    for sample, reason in _INTENTIONAL_NARROWINGS.items():
        assert reason
        assert _merged_detector(sample), sample
        assert not offers_claude_review_through_cursor(sample), sample
