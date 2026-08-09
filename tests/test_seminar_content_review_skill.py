"""Regression coverage for the read-only seminar review contract (#4840)."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SKILL_DIR = _REPO_ROOT / "agents_extensions" / "shared" / "skills" / "seminar-content-review"


def test_read_only_seminar_review_guidance_names_safe_commands_and_artifact_ban() -> None:
    skill = (_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    prompt = (_SKILL_DIR / "seminar-content-review-prompt.md").read_text(encoding="utf-8")

    assert "scripts.build.verify_shippable <track> <slug>" in skill
    assert "scripts/audit/module_quality_audit.py --level <track> --format json" in skill
    assert "scripts/audit_module.py" in skill
    assert "scripts.audit.audit_module" in skill
    assert "do **not** create `status/`, `audit/`, `review/`, `.cache/`, telemetry" in skill
    assert "advisory coverage evidence only" in skill
    assert "Read-only execution contract" in prompt
    assert "no `--output`" in prompt
    assert "no\n`--astro-build`" in prompt
    assert "do not invent a release blocker" in prompt
