"""Every rule the review validator enforces on a return's shape is stated in each review prompt (#9137).

A seat that is not told a rule it is then rejected for (a finding listed under two checks, a missing
``sub_dimension``) spends its attempt id and a full review; a seat told a rule stricter or looser than the
validator's wastes effort or is rejected. This ties each rejection to the sentence that states it, both ways:

* rule -> enforcement: each stated rule names the function of ``scripts/review/validate/validate.py`` that
  raises its code for that review kind, and the test reads the validator's source: the function must contain a
  ``check.add(codes.<CODE>, ...)`` call and must be reachable from ``validate_review``. Removing the call (or
  the call that reaches it) fails here even though the code stays defined in ``codes.py``;
* code -> sentence: every code the validator raises is classified below, and each code a return's own text can
  trigger has a distinctive phrase that must appear in exactly one bullet of each template that applies;
* sentence -> code: every bullet of the templates' rules section matches exactly one applicable code.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest
import yaml

from scripts.review.prompts.render import PROMPTS_DIR
from scripts.review.validate import codes, validate

REPO_ROOT = Path(__file__).resolve().parents[2]
SECTION_HEADING = "### Rules the validator enforces on the return"
PLAN, LESSON, REREVIEW = "plan-review.md.j2", "lesson-review.md.j2", "lesson-rereview.md.j2"
ALL = frozenset({PLAN, LESSON, REREVIEW})
LESSONS = frozenset({LESSON, REREVIEW})

#: validate.py function that raises a shared code for every kind, and the per-kind location checkers.
_REVIEW, _TAXONOMY, _EVIDENCE, _RESOLVE = "validate_review", "_check_taxonomy", "_check_finding_evidence", "_resolve"
_PLAN_LOCATIONS, _LESSON_LOCATIONS = "_check_plan_locations", "_check_locations"


def _everywhere(function: str) -> dict[str, str]:
    return dict.fromkeys(ALL, function)


def _per_kind(plan: str | None, lesson: str) -> dict[str, str]:
    return {**({PLAN: plan} if plan else {}), **dict.fromkeys(LESSONS, lesson)}


#: code -> (phrase every applicable template's rules section must carry in exactly one bullet,
#:          {template: function of validate.py that raises the code for that template's review kind}).
RULES: dict[str, tuple[str, dict[str, str]]] = {
    codes.REVIEW_UNREADABLE: ("The return is one YAML mapping", _everywhere(_REVIEW)),
    codes.SCHEMA_INVALID: ("no field the schema does not define", _everywhere(_REVIEW)),
    codes.MANIFEST_KIND_MISMATCH: ("the kind of the manifest this prompt was rendered from", _everywhere(_REVIEW)),
    codes.MANIFEST_HASH_MISMATCH: (
        "exactly the Manifest SHA256 printed at the top of this prompt",
        _everywhere(_REVIEW),
    ),
    codes.DUPLICATE_FINDING_ID: ("`id` is used once", _everywhere(_TAXONOMY)),
    codes.CHECK_MISSING: ("an empty list is not `clean`", _everywhere(_TAXONOMY)),
    codes.CHECK_NOT_APPLICABLE: ("No check is added beyond", _everywhere(_TAXONOMY)),
    codes.FINDING_NOT_REFERENCED: ("is listed under exactly one check", _everywhere(_TAXONOMY)),
    codes.DANGLING_CHECK_REFERENCE: ("only ids of findings that exist in `findings`", _everywhere(_TAXONOMY)),
    codes.LANGUAGE_SUB_DIMENSION_MISSING: ("carries a `sub_dimension`", _everywhere(_TAXONOMY)),
    codes.SUB_DIMENSION_INVALID: ("`sub_dimension` is one of", _everywhere(_TAXONOMY)),
    codes.EVIDENCE_BRANCH_COUNT: ("exactly one evidence branch", _everywhere(_EVIDENCE)),
    codes.UNSUPPORTED_SEVERITY_ABOVE_MINOR: ("has severity MINOR", _everywhere(_EVIDENCE)),
    codes.UNSUPPORTED_WITHOUT_SEARCHES: ("lists at least one search", _everywhere(_EVIDENCE)),
    codes.OUTCOME_NOT_IN_LEDGER: (
        "Each search `outcome` is the value printed beside its receipt",
        _everywhere(_EVIDENCE),
    ),
    codes.RECEIPT_NOT_IN_LEDGER: ("Every receipt a finding cites", _everywhere(_RESOLVE)),
    codes.EVIDENCE_RECEIPT_INVALID: (
        "has `status: ok` and comes from a tool in the review tool list",
        _everywhere(_EVIDENCE),
    ),
    codes.EXPECTED_NOT_IN_RESULT: (
        "`expected`, when present, is a substring of the stored result",
        _everywhere(_EVIDENCE),
    ),
    codes.QUOTE_EMPTY: ("`quote` has visible text", _per_kind(_PLAN_LOCATIONS, _LESSON_LOCATIONS)),
    codes.QUOTE_NOT_IN_UNIT: ("`quote` occurs inside the text of the", _per_kind(_PLAN_LOCATIONS, _LESSON_LOCATIONS)),
    codes.LOCATION_NOT_IN_PLAN: ("exist in the plan document", {PLAN: _PLAN_LOCATIONS}),
    codes.LOCATION_NOT_IN_LESSON: ("match a unit of the lesson together", _per_kind(None, _LESSON_LOCATIONS)),
    codes.LOCATION_INCOMPLETE: ("names both `activity` and `item`", _per_kind(None, _LESSON_LOCATIONS)),
    codes.SCOPE_MISSING: ("carries a `scope`", _per_kind(_PLAN_LOCATIONS, _LESSON_LOCATIONS)),
}

#: code -> why no sentence in a prompt can state it: the seat's return text cannot cause it.
NOT_STATED = {
    codes.MANIFEST_UNREADABLE: "the manifest file, not the return",
    codes.LEDGER_UNREADABLE: "the harness's ledger file, not the return",
    codes.LEDGER_HASH_STALE_LAST_LINE: "the harness's ledger sidecar, not the return",
    codes.LESSON_UNREADABLE: "the expanded lesson file, not the return",
    codes.PLAN_MANIFEST_INVALID: "the plan manifest, not the return",
    codes.PLAN_UNREADABLE: "the pinned plan document, not the return",
    codes.PLAN_BYTES_MISMATCH: "the pinned plan document, not the return",
    codes.PLAN_INPUTS_STALE: "inputs that changed after the manifest, not the return",
}


def _section(name: str) -> str:
    lines = (PROMPTS_DIR / name).read_text(encoding="utf-8").splitlines()
    start = lines.index(SECTION_HEADING)
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith(("### ", "## ", "---"))),
        len(lines),
    )
    return "\n".join(lines[start + 1 : end])


def _bullets(name: str) -> list[str]:
    return [line[2:] for line in _section(name).splitlines() if line.startswith("- ")]


def test_every_validator_code_is_classified_exactly_once() -> None:
    classified = [*RULES, *NOT_STATED]
    assert len(classified) == len(set(classified)), "a code is both stated and not stated"
    assert set(classified) == set(codes.DESCRIPTIONS), (
        "classify each new or removed validator code in RULES (a sentence in the templates) "
        f"or NOT_STATED (a reason): {sorted(set(classified) ^ set(codes.DESCRIPTIONS))}"
    )


def _validator_source() -> ast.Module:
    return ast.parse(Path(validate.__file__).read_text(encoding="utf-8"))


def _enforced_codes() -> dict[str, set[str]]:
    """Rejection code -> functions of validate.py holding a ``check.add(codes.<CODE>, ...)`` call for it."""
    found: dict[str, set[str]] = {}
    for function in (node for node in _validator_source().body if isinstance(node, ast.FunctionDef)):
        for call in (node for node in ast.walk(function) if isinstance(node, ast.Call)):
            target, args = call.func, call.args
            if not (isinstance(target, ast.Attribute) and target.attr == "add" and args):
                continue
            first = args[0]
            if isinstance(first, ast.Attribute) and isinstance(first.value, ast.Name) and first.value.id == "codes":
                found.setdefault(getattr(codes, first.attr), set()).add(function.name)
    return found


def _reachable_from_validate_review() -> set[str]:
    """Functions of validate.py that ``validate_review`` reaches through calls by name."""
    functions = {node.name: node for node in _validator_source().body if isinstance(node, ast.FunctionDef)}
    reached, pending = set(), ["validate_review"]
    while pending:
        name = pending.pop()
        if name in reached:
            continue
        reached.add(name)
        pending.extend(
            call.func.id
            for call in ast.walk(functions[name])
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id in functions
        )
    return reached


def test_every_code_in_the_registry_is_raised_by_the_validator() -> None:
    dead = sorted(set(codes.DESCRIPTIONS) - set(_enforced_codes()))
    assert not dead, f"codes.py defines codes no check.add(...) call in validate.py raises: {dead}"


@pytest.mark.parametrize("template", sorted(ALL))
def test_each_stated_rule_is_enforced_by_a_reachable_validator_call(template: str) -> None:
    enforced, reachable = _enforced_codes(), _reachable_from_validate_review()
    for code, (_, functions) in RULES.items():
        if template not in functions:
            continue
        function = functions[template]
        assert function in enforced.get(code, set()), (
            f"{template} states {code} but {function} in validate.py has no check.add(codes.*) call for it"
        )
        assert function in reachable, f"{template} states {code} but validate_review no longer reaches {function}"


@pytest.mark.parametrize("template", sorted(ALL))
def test_each_applicable_code_is_stated_in_exactly_one_bullet(template: str) -> None:
    bullets = _bullets(template)
    for code, (phrase, templates) in RULES.items():
        if template not in templates:
            continue
        found = [bullet for bullet in bullets if phrase in bullet]
        assert len(found) == 1, f"{template}: {code} ({phrase!r}) is stated in {len(found)} bullets, not 1"


@pytest.mark.parametrize("template", sorted(ALL))
def test_each_bullet_states_exactly_one_applicable_code(template: str) -> None:
    for bullet in _bullets(template):
        matched = [code for code, (phrase, templates) in RULES.items() if template in templates and phrase in bullet]
        assert len(matched) == 1, f"{template}: {bullet!r} states {matched or 'no applicable validator code'}"


@pytest.mark.parametrize("template", sorted(ALL))
def test_the_rules_are_plain_text_so_the_rendered_prompt_carries_them(template: str) -> None:
    section = _section(template)
    assert "{{" not in section and "{%" not in section and "{#" not in section
    assert len(_bullets(template)) == sum(template in templates for _, templates in RULES.values())


@pytest.mark.parametrize("template", sorted(ALL))
def test_the_enumerations_the_schema_enforces_are_listed(template: str) -> None:
    schema = json.loads((REPO_ROOT / "schemas" / "review-v1.schema.json").read_text(encoding="utf-8"))
    finding = schema["$defs"]["finding"]["properties"]
    taxonomy = yaml.safe_load((REPO_ROOT / "schemas" / "review-taxonomy-v1.yaml").read_text(encoding="utf-8"))
    section = _section(template)
    wanted = [
        *finding["dimension"]["enum"],
        *finding["sub_dimension"]["enum"],
        *finding["severity"]["enum"],
        *finding["status"]["enum"],
        *taxonomy["sub_dimensions"]["language"],
    ]
    missing = [value for value in wanted if not re.search(rf"\b{re.escape(value)}\b", section)]
    assert not missing, f"{template}: the rules section does not list {missing}"
    assert set(taxonomy["sub_dimensions"]["language"]) == set(finding["sub_dimension"]["enum"])
