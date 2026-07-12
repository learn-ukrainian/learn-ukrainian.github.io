from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.audit import module_size_policy_audit as audit
from scripts.build import linear_pipeline
from scripts.build.module_size_policy import (
    build_size_policy_for_plan,
    render_reviewer_size_policy,
    render_writer_size_policy,
    size_policy_allows_auto_expansion,
    size_policy_padding_diagnostic,
)
from scripts.build.phases.implementation_map import seed_implementation_map

PROMPT_FIXTURES: tuple[tuple[str, str], ...] = (
    ("bio", "andrii-malyshko"),
    ("folk", "kolomyiky"),
    ("c1", "abstract-writing"),
    ("c2", "academic-publishing"),
)


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


def _prompt_for(level: str, slug: str, writer: str) -> str:
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.load_plan(plan_path)
    plan.setdefault("slug", slug)
    manifest = {
        "slug": slug,
        "wiki_path": f"wiki/pedagogy/{level}/{slug}.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }
    return linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_path.read_text(encoding="utf-8"),
        knowledge_packet="Knowledge packet stub for #4801 size-policy prompt smoke.",
        plan_path=plan_path,
        wiki_manifest=manifest,
        implementation_map=seed_implementation_map(manifest, plan=plan),
        writer=writer,
    )


@pytest.mark.parametrize("writer", ("claude-tools", "codex-tools"))
@pytest.mark.parametrize(("level", "slug"), PROMPT_FIXTURES)
def test_claude_and_codex_writer_prompts_include_size_policy(
    level: str,
    slug: str,
    writer: str,
) -> None:
    prompt = _prompt_for(level, slug, writer)

    assert "## Module Size Policy — dossier/evidence-led expansion control (#4801)" in prompt
    assert "- Expansion permission:" in prompt
    assert "never invent depth to satisfy a fixed word count" in prompt
    assert "SIZE_POLICY_MISMATCH" in prompt
    assert "old 150% multiplier thinking as a target" in prompt


def test_size_policy_blocks_auto_expansion_when_plan_floor_exceeds_sparse_ceiling(
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

    assert record.status == "plan_review_needed"
    assert size_policy_allows_auto_expansion(record) is False
    block = render_writer_size_policy(record)
    assert "Expansion permission: plan_policy_review_required" in block


def test_reviewed_size_policy_override_allows_expansion_below_generic_track_floor(
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

    assert record.status == "explicit_override"
    assert record.advisory_ceiling == 4800
    assert record.metrics is not None
    assert size_policy_allows_auto_expansion(record) is True
    assert "Review basis:" in render_writer_size_policy(record)


def test_invalid_size_policy_override_blocks_writer_expansion(
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

    record = build_size_policy_for_plan(plan, actual_words=2100)

    assert record.status == "invalid_size_policy"
    assert size_policy_allows_auto_expansion(record) is False
    block = render_writer_size_policy(record)
    assert "Expansion permission: blocked_until_size_policy_is_valid" in block
    assert "must equal word_target" in block


def test_size_policy_reports_advisory_padding_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_size_policy_roots(monkeypatch, tmp_path)
    plan = {
        "level": "BIO",
        "slug": "dense-person",
        "word_target": 5000,
        "content_outline": [{"section": "Огляд", "words": 5000}],
        "references": [{"type": "dossier", "path": "docs/research/bio/dense-person.md"}],
    }
    _write_dossier(tmp_path, "bio", "dense-person", 900)

    record = build_size_policy_for_plan(plan, actual_words=5600)
    diagnostic = size_policy_padding_diagnostic(record)

    assert record.status == "over_advisory_ceiling"
    assert diagnostic["status"] == "over_advisory_ceiling"
    assert diagnostic["over_advisory_ceiling_words"] == 600
    assert "source-backed density from filler/padding" in diagnostic["review_action"]
    reviewer_block = render_reviewer_size_policy(record)
    assert "do not fail or pass a module on word count alone" in reviewer_block
    assert "source-backed density" in reviewer_block


def test_size_policy_uses_plan_path_slug_when_plan_has_no_slug(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_size_policy_roots(monkeypatch, tmp_path)
    plan_path = tmp_path / "curriculum" / "l2-uk-en" / "plans" / "bio" / "thin-person.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan = {
        "level": "BIO",
        "word_target": 6000,
        "content_outline": [{"section": "Огляд", "words": 6000}],
        "references": [{"type": "dossier", "path": "docs/research/bio/thin-person.md"}],
    }
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
    _write_dossier(tmp_path, "bio", "thin-person", 900)

    record = build_size_policy_for_plan(plan, plan_path=plan_path, actual_words=5500)

    assert record.slug == "thin-person"
    assert record.status == "plan_review_needed"
    assert record.dossier_path == "docs/research/bio/thin-person.md"


def test_size_policy_handles_missing_slug_without_plan_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_size_policy_roots(monkeypatch, tmp_path)
    plan = {
        "level": "BIO",
        "word_target": 5000,
        "content_outline": [{"section": "Огляд", "words": 5000}],
        "references": [],
    }

    record = build_size_policy_for_plan(plan, actual_words=4500)

    assert record.slug == ""
    assert record.dossier_path is None
    assert record.status == "missing_dossier"


def test_writer_length_precheck_returns_policy_mismatch_without_invoking_writer(
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
        raise AssertionError("writer should not be invoked when size policy blocks expansion")

    result = linear_pipeline.run_writer_draft_length_precheck(
        plan=plan,
        module_dir=module_dir,
        plan_path=plan_path,
        writer="claude-tools",
        invoker=fail_if_invoked,
        event_sink=lambda event, **fields: events.append({"event": event, **fields}),
    )

    assert result["applied"] is False
    assert result["patch_status"] == "policy_mismatch"
    assert result["policy_mismatch"] is True
    assert result["size_policy"]["status"] == "plan_review_needed"
    assert events == [
        {
            "event": "writer_draft_length_precheck",
            "status": "policy_mismatch",
            "count": 5501,
            "target": 6000,
            "short_section_count": 0,
            "size_policy_status": "plan_review_needed",
        }
    ]
