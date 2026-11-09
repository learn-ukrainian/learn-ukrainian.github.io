"""Keep issue-template examples out of acceptance criteria (#11213)."""

from pathlib import Path

import pytest

from scripts.ci.check_issue_task_quality import score_body
from scripts.orchestration.postmerge_criteria import visible_markdown
from scripts.orchestration.task_lifecycle import LifecycleError, parse_issue_acceptance_criteria

pytestmark = pytest.mark.repo_wide

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / ".github" / "ISSUE_TEMPLATE"
TEMPLATES = sorted(path for path in TEMPLATE_DIR.rglob("*") if path.is_file())


def criterion_ids(body: str) -> list[str]:
    try:
        return [item["id"] for item in parse_issue_acceptance_criteria(body)]
    except LifecycleError as exc:
        if str(exc) != "issue body has no stable-ID acceptance criteria":
            raise
        return []


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda path: path.name)
def test_template_criteria_match_visible_criteria(template: Path) -> None:
    body = template.read_text(encoding="utf-8")
    visible_ids = criterion_ids(visible_markdown(body))

    assert criterion_ids(body) == visible_ids
    dod = score_body(body)["dod"]
    if visible_ids:
        assert dod == {"status": "PASS", "errors": []}
    else:
        assert [error["code"] for error in dod["errors"]] == ["dod_structure_absent"]


def test_complex_template_allows_real_ac_03() -> None:
    body = (TEMPLATE_DIR / "complex-task.md").read_text(encoding="utf-8")
    body += "\n- [ ] AC-03: The requested change passes its acceptance checks.\n"

    assert criterion_ids(body) == ["AC-01", "AC-02", "AC-03"]
    assert criterion_ids(visible_markdown(body)) == ["AC-01", "AC-02", "AC-03"]
    assert score_body(body)["dod"] == {"status": "PASS", "errors": []}


def test_commented_duplicate_requires_visible_markdown() -> None:
    body = """<!--
- [ ] AC-03: Hidden example.
-->
- [ ] AC-03: The real criterion.
"""

    # Raw-parser comment handling remains follow-up #11234.
    with pytest.raises(LifecycleError, match="duplicate acceptance criterion ID in issue body: AC-03"):
        parse_issue_acceptance_criteria(body)
    assert parse_issue_acceptance_criteria(visible_markdown(body)) == [
        {"id": "AC-03", "text": "The real criterion.", "checked": False},
    ]
    assert score_body(body)["dod"] == {"status": "PASS", "errors": []}
