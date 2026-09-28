"""Every rule the review validator enforces on a return's shape is stated in each review prompt (#9137).

A seat that is not told a rule it is then rejected for (a finding listed under two checks, a missing
``sub_dimension``) spends its attempt id and a full review. This ties each rejection code of
``scripts/review/validate/codes.py`` to the sentence that states it, both ways:

* code -> sentence: every code is classified below, and each code that a return's own text can trigger has
  a distinctive phrase that must appear in exactly one bullet of each template that applies;
* sentence -> code: every bullet of the templates' rules section matches exactly one applicable code, so a
  rule stated without a code (or a code added to the validator without a sentence) fails here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from scripts.review.prompts.render import PROMPTS_DIR
from scripts.review.validate import codes

REPO_ROOT = Path(__file__).resolve().parents[2]
SECTION_HEADING = "### Rules the validator enforces on the return"
PLAN, LESSON, REREVIEW = "plan-review.md.j2", "lesson-review.md.j2", "lesson-rereview.md.j2"
ALL = frozenset({PLAN, LESSON, REREVIEW})
LESSONS = frozenset({LESSON, REREVIEW})

#: code -> (phrase every applicable template's rules section must carry in exactly one bullet, templates).
RULES: dict[str, tuple[str, frozenset[str]]] = {
    codes.REVIEW_UNREADABLE: ("The return is one YAML mapping", ALL),
    codes.SCHEMA_INVALID: ("no field the schema does not define", ALL),
    codes.MANIFEST_KIND_MISMATCH: ("the kind of the manifest this prompt was rendered from", ALL),
    codes.MANIFEST_HASH_MISMATCH: ("exactly the Manifest SHA256 printed at the top of this prompt", ALL),
    codes.DUPLICATE_FINDING_ID: ("`id` is used once", ALL),
    codes.CHECK_MISSING: ("an empty list is not `clean`", ALL),
    codes.CHECK_NOT_APPLICABLE: ("No check is added beyond", ALL),
    codes.FINDING_NOT_REFERENCED: ("is listed under exactly one check", ALL),
    codes.DANGLING_CHECK_REFERENCE: ("only ids of findings that exist in `findings`", ALL),
    codes.LANGUAGE_SUB_DIMENSION_MISSING: ("carries a `sub_dimension`", ALL),
    codes.SUB_DIMENSION_INVALID: ("`sub_dimension` is one of", ALL),
    codes.EVIDENCE_BRANCH_COUNT: ("exactly one evidence branch", ALL),
    codes.UNSUPPORTED_SEVERITY_ABOVE_MINOR: ("has severity MINOR", ALL),
    codes.UNSUPPORTED_WITHOUT_SEARCHES: ("lists at least one search", ALL),
    codes.OUTCOME_NOT_IN_LEDGER: ("what the stored result of its receipt shows", ALL),
    codes.RECEIPT_NOT_IN_LEDGER: ("cited receipt is in this attempt's ledger", ALL),
    codes.EVIDENCE_RECEIPT_INVALID: ("has `status: ok` and comes from a tool in the review tool list", ALL),
    codes.EXPECTED_NOT_IN_RESULT: ("`expected`, when present, is a substring of the stored result", ALL),
    codes.QUOTE_EMPTY: ("`quote` is non-empty text", ALL),
    codes.QUOTE_NOT_IN_UNIT: ("`quote` occurs verbatim inside the named unit", ALL),
    codes.LOCATION_NOT_IN_PLAN: ("exists in the plan document", frozenset({PLAN})),
    codes.LOCATION_NOT_IN_LESSON: ("exists in the lesson", LESSONS),
    codes.LOCATION_INCOMPLETE: ("names both `activity` and `item`", LESSONS),
    codes.SCOPE_MISSING: ("carries a `scope`", ALL),
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
