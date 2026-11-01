from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.audit import module_size_policy_audit as audit
from scripts.build import linear_pipeline
from scripts.build.module_size_policy import (
    build_size_policy_for_plan,
    render_writer_size_policy,
    size_policy_allows_auto_expansion,
)

pytestmark = pytest.mark.reads_content


def _patch_size_policy_roots(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(audit, "PROJECT_ROOT", root)
    monkeypatch.setattr(audit, "CURRICULUM_ROOT", root / "curriculum" / "l2-uk-en")
    monkeypatch.setattr(audit, "RESEARCH_ROOT", root / "docs" / "research")


def _write_dossier(root: Path, track: str, slug: str, words: int) -> None:
    path = root / "docs" / "research" / track / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Досьє",
                "",
                "https://example.org/source-a",
                "https://example.org/source-b",
                " ".join(["слово"] * words),
            ]
        ),
        encoding="utf-8",
    )


def test_size_policy_never_authorizes_expansion_from_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_size_policy_roots(monkeypatch, tmp_path)
    plan = {
        "level": "BIO",
        "slug": "thin-person",
        "word_target": 6000,
        "content_outline": [{"section": "Огляд", "words": 6000}],
        "references": [{"type": "dossier", "path": "docs/research/bio/thin-person.md"}],
    }
    _write_dossier(tmp_path, "bio", "thin-person", 900)

    record = build_size_policy_for_plan(plan, actual_words=5500)

    assert record.status == "advisory_ok"
    assert size_policy_allows_auto_expansion(record) is False
    block = render_writer_size_policy(record)
    assert "neither reward nor penalize word counts" in block
    assert record.decision_signals == ()


def test_reviewed_size_policy_override_is_descriptive_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_size_policy_roots(monkeypatch, tmp_path)
    plan = {
        "level": "BIO",
        "slug": "reviewed-person",
        "word_target": 4200,
        "content_outline": [{"section": "Огляд", "words": 4200}],
        "references": [{"type": "dossier", "path": "docs/research/bio/reviewed-person.md"}],
        "size_policy": {
            "floor_words": 4200,
            "recommended_range": [4200, 4600],
            "ceiling_words": 4800,
            "basis": "Bounded chronology with verified primary-source coverage.",
            "saturation_evidence": "The dossier exhausts the available dated sources.",
            "exceptional_justification": "required_above_ceiling",
        },
    }
    _write_dossier(tmp_path, "bio", "reviewed-person", 900)

    record = build_size_policy_for_plan(plan, actual_words=4300)

    assert record.status == "advisory_ok"
    assert record.advisory_ceiling == 4800
    assert record.metrics is not None
    assert size_policy_allows_auto_expansion(record) is False
    assert "Plan floor words:" not in render_writer_size_policy(record)


def test_invalid_size_policy_metadata_does_not_become_a_finding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_size_policy_roots(monkeypatch, tmp_path)
    plan = {
        "level": "BIO",
        "slug": "unreviewed-person",
        "word_target": 2200,
        "content_outline": [{"section": "Огляд", "words": 2200}],
        "size_policy": {
            "floor_words": 2100,
            "recommended_range": [2200, 2800],
            "ceiling_words": 4000,
            "basis": "",
            "saturation_evidence": "",
            "exceptional_justification": "optional",
        },
    }

    _write_dossier(tmp_path, "bio", "unreviewed-person", 900)
    record = build_size_policy_for_plan(plan, actual_words=2100)

    assert record.status == "advisory_ok"
    assert record.decision_signals == ()
    assert size_policy_allows_auto_expansion(record) is False
    block = render_writer_size_policy(record)
    assert "neither reward nor penalize word counts" in block
    assert "must equal word_target" not in block


def test_legacy_writer_precheck_cannot_get_expansion_permission_from_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_size_policy_roots(monkeypatch, tmp_path)
    plan = {
        "level": "BIO",
        "sequence": 1,
        "slug": "thin-person",
        "word_target": 6000,
        "content_outline": [{"section": "Огляд", "words": 6000}],
        "references": [{"type": "dossier", "path": "docs/research/bio/thin-person.md"}],
    }
    _write_dossier(tmp_path, "bio", "thin-person", 900)
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(
        "## Огляд\n\n" + " ".join(["слово"] * 5500),
        encoding="utf-8",
    )
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
    events: list[dict] = []

    def fail_if_invoked(*_args, **_kwargs):
        raise AssertionError("writer must not auto-expand from word counts")

    result = linear_pipeline.run_writer_draft_length_precheck(
        plan=plan,
        module_dir=module_dir,
        plan_path=plan_path,
        writer="claude-tools",
        invoker=fail_if_invoked,
        event_sink=lambda event, **fields: events.append({"event": event, **fields}),
    )

    assert result["applied"] is False
    assert result["patch_status"] == "informational"
    assert result["outcomes"] == []
    assert result["before"]["passed"] is True
    assert result["size_policy"]["status"] == "advisory_ok"
    assert events == [
        {
            "event": "writer_draft_length_precheck",
            "status": "informational",
            "count": 5501,
        }
    ]


def test_writer_precheck_honors_explicit_evidence_gap_without_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_size_policy_roots(monkeypatch, tmp_path)
    plan = {
        "level": "A1",
        "sequence": 1,
        "slug": "exhausted-core",
        "word_target": 100,
        "content_outline": [{"section": "Огляд", "words": 100}],
    }
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(
        "<!-- EVIDENCE_GAP: objective=explain the concept; missing evidence=source support -->\n"
        "# Огляд\n\n"
        + " ".join(["слово"] * 50),
        encoding="utf-8",
    )
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")

    def fail_if_invoked(*_args, **_kwargs):
        raise AssertionError("writer must not auto-expand a draft with an evidence gap")

    result = linear_pipeline.run_writer_draft_length_precheck(
        plan=plan,
        module_dir=module_dir,
        plan_path=plan_path,
        writer="claude-tools",
        invoker=fail_if_invoked,
    )

    assert result["applied"] is False
    assert result["patch_status"] == "informational"
    assert result["before"]["passed"] is False
    assert {
        "outcome": "EVIDENCE_GAP",
        "detail": "objective=explain the concept; missing evidence=source support",
        "route": "source_research_or_versioned_plan_review",
    } in result["outcomes"]
    assert result["size_policy"]["evidence_gap"] is True
    assert result["size_policy"]["status"] == "evidence_gap"
    assert result["size_policy"]["decision_signals"] == ("evidence_gap",)
