"""DB-free actual tracked-tree and combined-branch publication contracts (#10106)."""

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import publication
from tests.curriculum.evidence.test_publication import owned_entries, owned_occurrence


@pytest.fixture
def course_tree(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    entries = owned_entries()
    for path, content in {
        "docs/l2-uk-direct/textbook-selection.yaml": yaml.safe_dump({"sources": entries}),
        "site/src/data/lexicon-sentence-inventory.json": json.dumps({"rows": []}),
    }.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    return tmp_path


def track(root):
    subprocess.run(["git", "add", "."], cwd=root, check=True, timeout=30)


def add_lesson(root, module, size, unit=1):
    row = owned_occurrence(size, unit=unit)["record"]
    plan = {"lessons": [{"n": 1, "steps": [{"id": "s1", "needs": ["quote"], "ref": "T-001"}]}]}
    for path, content in {
        f"curriculum/l2-uk-en/lesson-plans/a1/{module}.yaml": plan,
        f"curriculum/l2-uk-en/evidence/a1/{module}.yaml": {"texts": [row]},
    }.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml.safe_dump(content))
    track(root)


def test_owned_excerpt_combined_tracked_tree_course_cap(course_tree):
    add_lesson(course_tree, "one", 120)
    assert publication.course_report(course_tree)["status"] == "ok"
    add_lesson(course_tree, "two", 120, unit=2)
    report = publication.course_report(course_tree)
    assert any(error.startswith("publication_course_limit:") for error in report["errors"])
    assert report["sources"]["ulp-1-00-lesson-notes"]["lesson"] == 240
    add_lesson(course_tree, "two", 80, unit=2)
    assert publication.course_report(course_tree)["status"] == "ok"


def test_owned_excerpt_combined_tracked_tree_unit_cap(course_tree):
    target = course_tree / "docs/l2-uk-direct/textbook-selection.yaml"
    target.write_text(yaml.safe_dump({"sources": owned_entries(40000)}))
    add_lesson(course_tree, "one", 120)
    add_lesson(course_tree, "two", 120)
    report = publication.course_report(course_tree)
    assert any(error.startswith("publication_unit_limit:") for error in report["errors"])
    assert not any(error.startswith("publication_course_limit:") for error in report["errors"])


def test_owned_excerpt_missing_input_legacy_page_and_proposal_fail_closed(course_tree):
    add_lesson(course_tree, "one", 120)
    pack = course_tree / "curriculum/l2-uk-en/evidence/a1/one.yaml"
    pack.rename(pack.with_suffix(".missing"))
    track(course_tree)
    assert any("demanded pack missing" in e for e in publication.course_report(course_tree)["errors"])
    page = course_tree / "site/src/content/docs/a1-v1/legacy.mdx"
    page.parent.mkdir(parents=True)
    page.write_text("Synthetic legacy page")
    track(course_tree)
    report = publication.course_report(course_tree)
    assert report["status"] == "blocked" and report["provenance_unknown"] == 1
    assert report["sources"]["ulp-1-00-lesson-notes"]["provenance_unknown"] == 1


def test_actual_tracked_tree_has_no_new_owned_excerpts_while_existing_scope_is_blocked():
    root = Path(__file__).resolve().parents[3]
    report = publication.course_report(root)
    assert len(report["sources"]) == 11
    assert report["status"] == "blocked"
    assert report["provenance_unknown"] > 0
    assert all(total["lesson"] == 0 for total in report["sources"].values()), report["errors"]
    assert {file for file, total in report["sources"].items() if total["site_data"] > total["effective_cap"]} == {
        f"ulp-{i}-00-lesson-notes" for i in range(3, 7)
    }
    assert report["sources"]["ulp-1-00-lesson-notes"]["repo_exposed"] > 0
    with pytest.raises(ValueError, match=r"publication_scope_incomplete|publication_course_limit"):
        publication.enforce_publication(
            {"steps": [{"id": "s1", "needs": ["quote"], "ref": "T-001"}]}, {"texts": [owned_occurrence(20)["record"]]}
        )
