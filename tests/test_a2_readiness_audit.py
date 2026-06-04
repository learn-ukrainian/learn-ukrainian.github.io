from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from validate.a2_readiness_audit import audit, main


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_minimal_a2(root: Path, *, slug: str = "sample", items: int = 8) -> None:
    _write_yaml(root / "curriculum/l2-uk-en/curriculum.yaml", {"levels": {"a2": {"modules": [slug]}}})
    _write_yaml(
        root / f"curriculum/l2-uk-en/plans/a2/{slug}.yaml",
        {
            "module": "a2-001",
            "level": "A2",
            "sequence": 1,
            "slug": slug,
            "version": "1.0.0",
            "title": "Sample",
            "objectives": ["Practice a sample A2 topic."],
            "word_target": 2000,
            "grammar": ["sample grammar"],
            "register": "neutral everyday Ukrainian",
            "persona": "careful A2 curriculum writer",
            "content_outline": [{"section": "Main", "words": 2000}],
            "activity_hints": [{"type": "quiz", "items": items}],
        },
    )
    _write_text(
        root / f"wiki/grammar/a2/{slug}.md",
        "# Sample\n\nA clean wiki page with no verification marker.\n",
    )
    _write_yaml(root / f"wiki/grammar/a2/{slug}.sources.yaml", {"sources": []})
    _write_text(
        root / f"wiki/.reviews/grammar/a2/{slug}-review-LOCKED.md",
        "\n".join(
            [
                "# Sample Review LOCKED",
                "Factual accuracy: 9/10 with concrete evidence.",
                "Ukrainian language quality: 9/10 with concrete evidence.",
                "Decolonization: 9/10 with concrete evidence.",
                "Completeness: 9/10 with concrete evidence.",
                "Actionable guidance: 9/10 with concrete evidence.",
                "LOCKED until source inputs change.",
            ]
        ),
    )


def test_clean_minimal_a2_passes(tmp_path: Path) -> None:
    _write_minimal_a2(tmp_path)

    result = audit(tmp_path)

    assert result.failed is False
    assert result.summary["manifest_modules"] == 1
    assert result.summary["activity_density_below_floor"] == 0
    assert result.summary["verify_markers"] == 0
    assert result.summary["locked_reviews"] == 1
    assert result.summary["plan_backup_files"] == 0
    assert result.summary["missing_readiness_fields"] == {
        "grammar": 0,
        "register": 0,
        "persona": 0,
    }


def test_a2_audit_reports_current_blocker_classes(tmp_path: Path) -> None:
    _write_minimal_a2(tmp_path, items=6)
    plan_path = tmp_path / "curriculum/l2-uk-en/plans/a2/sample.yaml"
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    for field in ("grammar", "register", "persona"):
        plan.pop(field)
    _write_yaml(plan_path, plan)
    _write_text(
        tmp_path / "wiki/grammar/a2/sample.md",
        "# Sample\n\nThis still needs source proof. <!-- VERIFY -->\n",
    )
    (tmp_path / "wiki/.reviews/grammar/a2/sample-review-LOCKED.md").unlink()
    _write_text(tmp_path / "curriculum/l2-uk-en/plans/a2/sample.yaml.bak", "version: 0.9.0\n")

    result = audit(tmp_path)
    checks = {finding.check for finding in result.findings}

    assert result.failed is True
    assert "activity_density" in checks
    assert "readiness_fields" in checks
    assert "wiki_verify" in checks
    assert "wiki_reviews" in checks
    assert "plan_backups" in checks
    assert result.summary["activity_density_below_floor"] == 1
    assert result.summary["verify_markers"] == 1
    assert result.summary["locked_reviews"] == 0
    assert result.summary["plan_backup_files"] == 1
    assert result.summary["missing_readiness_fields"] == {
        "grammar": 1,
        "register": 1,
        "persona": 1,
    }


def test_a2_audit_json_cli(tmp_path: Path, capsys) -> None:
    _write_minimal_a2(tmp_path)

    assert main(["--root", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["summary"]["manifest_modules"] == 1
    assert payload["summary"]["errors"] == 0
    assert payload["findings"] == []
