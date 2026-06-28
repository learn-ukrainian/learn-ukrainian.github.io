from pathlib import Path

import pytest

from scripts.audit import check_no_internal_ids


def test_clean_fixture_has_no_findings(tmp_path: Path) -> None:
    clean = tmp_path / "clean.mdx"
    clean.write_text(
        "---\ntitle: Clean\n---\n\nA public source URL is fine: https://www.ukrlib.com.ua/demo/\n",
        encoding="utf-8",
    )

    assert check_no_internal_ids.scan_files([clean]) == []


def test_violating_fixture_reports_chunk_and_section_ids(tmp_path: Path) -> None:
    bad = tmp_path / "bad.mdx"
    bad.write_text(
        "---\ntitle: Bad\n---\n\ntruthSource={`5794da94_c0817`}\nSource section S4433 leaked.\n",
        encoding="utf-8",
    )

    findings = check_no_internal_ids.scan_files([bad])

    assert [(finding.line_no, finding.value) for finding in findings] == [
        (5, "5794da94_c0817"),
        (6, "S4433"),
    ]


@pytest.mark.parametrize(
    "term",
    [
        "source hammer",
        "source-first",
        "learner-facing",
        "chunk_id",
        "службова позначка",
    ],
)
def test_learner_page_process_register_terms_fail(term: str, tmp_path: Path) -> None:
    bad = tmp_path / "bad.mdx"
    bad.write_text(f"Visible learner text mentions {term}.\n", encoding="utf-8")

    findings = check_no_internal_ids.scan_files([bad])

    assert [(finding.kind, finding.value) for finding in findings] == [("build/process term", term)]


def test_normal_ukrainian_source_wording_passes(tmp_path: Path) -> None:
    clean = tmp_path / "clean.mdx"
    clean.write_text(
        "публічний текст\nпершоджерело\nуривок\nджерельна сторінка\n",
        encoding="utf-8",
    )

    assert check_no_internal_ids.scan_files([clean]) == []


def test_candidate_selection_scans_only_routable_learner_surfaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(check_no_internal_ids, "PROJECT_ROOT", tmp_path)

    visible_doc = tmp_path / "site/src/content/docs/folk/topic.mdx"
    visible_doc.parent.mkdir(parents=True)
    visible_doc.write_text("---\ntitle: Topic\n---\n\nsource hammer\n", encoding="utf-8")

    visible_reading = tmp_path / "site/src/content/readings/visible.mdx"
    visible_reading.parent.mkdir(parents=True)
    visible_reading.write_text(
        "---\ntitle: Visible\npublished: true\ncanonical: true\n---\n\nsource hammer\n",
        encoding="utf-8",
    )

    nested_reading = tmp_path / "site/src/content/readings/folk/nested.mdx"
    nested_reading.parent.mkdir(parents=True)
    nested_reading.write_text(
        "---\ntitle: Nested\npublished: true\ncanonical: true\n---\n\nsource hammer\n",
        encoding="utf-8",
    )

    hidden_reading = tmp_path / "site/src/content/readings/hidden.mdx"
    hidden_reading.write_text(
        "---\ntitle: Hidden\npublished: false\ncanonical: false\n---\n\nsource hammer\n",
        encoding="utf-8",
    )

    module = tmp_path / "curriculum/l2-uk-en/folk/topic/module.md"
    activities = tmp_path / "curriculum/l2-uk-en/folk/topic/activities.yaml"
    vocab = tmp_path / "curriculum/l2-uk-en/folk/topic/vocabulary.yaml"
    resources = tmp_path / "curriculum/l2-uk-en/folk/topic/resources.yaml"
    for path in [module, activities, vocab, resources]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source hammer\n", encoding="utf-8")

    plan = tmp_path / "curriculum/l2-uk-en/plans/folk/topic.yaml"
    sidecar = tmp_path / "curriculum/l2-uk-en/folk/topic/promote_quality.json"
    audit = tmp_path / "curriculum/l2-uk-en/folk/topic/audit/topic-review.md"
    pr_body = tmp_path / "docs/pr-bodies/folk-topic.md"
    for path in [plan, sidecar, audit, pr_body]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source hammer\n", encoding="utf-8")

    candidates = check_no_internal_ids.scan_candidates(
        [
            visible_doc,
            visible_reading,
            nested_reading,
            hidden_reading,
            module,
            activities,
            vocab,
            resources,
            plan,
            sidecar,
            audit,
            pr_body,
        ]
    )

    assert {path.relative_to(tmp_path).as_posix() for path in candidates} == {
        "site/src/content/docs/folk/topic.mdx",
        "site/src/content/readings/visible.mdx",
        "site/src/content/readings/folk/nested.mdx",
        "curriculum/l2-uk-en/folk/topic/module.md",
        "curriculum/l2-uk-en/folk/topic/activities.yaml",
        "curriculum/l2-uk-en/folk/topic/vocabulary.yaml",
        "curriculum/l2-uk-en/folk/topic/resources.yaml",
    }


def test_main_files_mode_prints_file_line_on_violation(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "bad.mdx"
    bad.write_text("Visible leak 40beaaff_c0000.\n", encoding="utf-8")

    exit_code = check_no_internal_ids.main(["--files", str(bad)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert f"{bad}:1:14: internal corpus chunk id leaked: 40beaaff_c0000\n" == output


def test_non_mdx_explicit_file_is_ignored(tmp_path: Path, capsys) -> None:
    note = tmp_path / "note.txt"
    note.write_text("Internal-looking text 40beaaff_c0000 outside MDX.\n", encoding="utf-8")

    exit_code = check_no_internal_ids.main(["--files", str(note)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert output == "0 findings: no learner surface files to scan.\n"
