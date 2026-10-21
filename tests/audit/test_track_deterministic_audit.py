from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.audit import track_deterministic_audit as audit

pytestmark = pytest.mark.reads_content


@dataclass
class DummyModule:
    slug: str
    title: str
    level: str
    local_num: int


def write_minimal_module(root: Path, slug: str, num: int, *, english_leak: bool = False) -> None:
    curriculum = root / "curriculum" / "l2-uk-en"
    module_dir = curriculum / "b2" / slug
    module_dir.mkdir(parents=True)
    (curriculum / "plans" / "b2").mkdir(parents=True, exist_ok=True)
    (root / "wiki" / "grammar" / "b2").mkdir(parents=True, exist_ok=True)
    (root / "site" / "src" / "content" / "docs" / "b2").mkdir(parents=True, exist_ok=True)
    (root / "site" / "src" / "content" / "readings").mkdir(parents=True, exist_ok=True)

    body = (
        "This paragraph explains the entire grammar point in English before Ukrainian appears.\n"
        if english_leak
        else ""
    )
    (module_dir / "module.md").write_text(f"# Модуль {num}\n\n{body}**Я чекаю на автобус.**\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text(
        "- type: quiz\n"
        "  title: Перевірка\n"
        "  items:\n"
        "    - question: Що правильно?\n"
        "      options:\n"
        "        - text: Так\n"
        "          correct: true\n"
        "        - text: Ні\n"
        "          correct: false\n",
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text(
        "- word: слово\n  translation: word\n",
        encoding="utf-8",
    )
    (curriculum / "plans" / "b2" / f"{slug}.yaml").write_text("title: Test\n", encoding="utf-8")
    (root / "wiki" / "grammar" / "b2" / f"{slug}.md").write_text("# Вікі\n", encoding="utf-8")
    (root / "wiki" / "grammar" / "b2" / f"{slug}.sources.yaml").write_text("sources: []\n", encoding="utf-8")
    (root / "site" / "src" / "content" / "docs" / "b2" / f"{slug}.mdx").write_text(
        "---\ntitle: Test\n---\n\n[Self](/b2/test-one)\n",
        encoding="utf-8",
    )


def patch_roots(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(audit, "PROJECT_ROOT", root)
    monkeypatch.setattr(audit, "CURRICULUM_ROOT", root / "curriculum" / "l2-uk-en")
    monkeypatch.setattr(audit, "SITE_DOCS_ROOT", root / "site" / "src" / "content" / "docs")
    monkeypatch.setattr(audit, "SITE_READINGS_ROOT", root / "site" / "src" / "content" / "readings")
    monkeypatch.setattr(
        audit,
        "get_modules_for_level",
        lambda track: [
            DummyModule("test-one", "Test One", track, 1),
            DummyModule("test-two", "Test Two", track, 2),
        ],
    )
    monkeypatch.setattr(audit, "check_protected_diff", lambda track: [])


def base_config() -> dict:
    return {
        "defaults": {
            "required_files": ["plan", "module_md", "activities", "vocabulary", "site_mdx", "wiki", "wiki_sources"],
            "optional_files": ["resources"],
            "checks": {
                "activity_yaml": False,
                "vocabulary_yaml": True,
                "resources_yaml": True,
                "surface_gates": True,
                "internal_leakage": True,
                "mdx_routes": True,
                "protected_diff": True,
            },
            "severity": {
                "missing_required_file": "high",
                "optional_missing": "info",
            },
        },
        "tracks": {},
    }


@pytest.mark.parametrize(
    ("entrypoint", "arguments", "exit_code", "expected_output"),
    [
        (
            "scripts/tools/check_gate.py",
            ["--help"],
            1,
            "Stages: skeleton, content, activities",
        ),
        (
            "scripts/audit/review_plan.py",
            None,
            0,
            "DRY RUN:",
        ),
        ("scripts/audit_module.py", ["--help"], 0, "usage: audit_module.py"),
        ("scripts/analytics/vocab_progression.py", ["--help"], 0, "usage: vocab_progression.py"),
        ("scripts/generators/generate_a2_plans.py", ["--help"], 0, "usage: generate_a2_plans.py"),
        ("scripts/rag_batch_verify.py", ["--help"], 0, "usage: rag_batch_verify.py"),
        ("scripts/validate_plan_config.py", ["--help"], 0, "usage: validate_plan_config.py"),
    ],
)
@pytest.mark.repo_wide
def test_config_consumer_file_launches_without_pythonpath(
    tmp_path: Path, entrypoint: str, arguments: list[str], exit_code: int, expected_output: str
) -> None:
    """Real file launches must work even outside the repository cwd."""
    root = Path(__file__).resolve().parents[2]
    if entrypoint == "scripts/audit/review_plan.py":
        plan_path = next(
            plan_path
            for plan_path in sorted((root / "curriculum" / "l2-uk-en" / "plans" / "a1").glob("*.yaml"))
            if audit.read_yaml(plan_path)
        )
        arguments = ["a1", plan_path.stem, "--dry-run"]
        expected_output = f"DRY RUN: {plan_path.stem}"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(root / entrypoint), *arguments],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == exit_code, result.stdout + result.stderr
    assert expected_output in result.stdout
    assert result.stderr == ""


def test_track_audit_json_contract_and_llm_qg_exclusion(tmp_path, monkeypatch) -> None:
    patch_roots(monkeypatch, tmp_path)
    write_minimal_module(tmp_path, "test-one", 1)
    write_minimal_module(tmp_path, "test-two", 2)
    index = tmp_path / "site" / "src" / "content" / "docs" / "b2" / "index.mdx"
    index.write_text('slug: "test-one"\nslug: "test-two"\n', encoding="utf-8")

    result = audit.audit_track(
        track="b2",
        config=base_config(),
        range_filter=(1, 1),
        slugs=None,
        run_mdx_generation_validate=False,
    )

    assert result["track"] == "b2"
    assert result["summary"]["modules_selected"] == 1
    assert result["summary"]["llm_qg_excluded_pending_2156"] is True
    assert any(item["category"] == "llm_qg" for item in result["skipped"])
    assert all("llm_qg_status" not in item for item in result["findings"])
    assert not (tmp_path / "curriculum" / "l2-uk-en" / "b2" / "test-one" / "status").exists()
    assert not (tmp_path / "curriculum" / "l2-uk-en" / "b2" / "test-one" / "audit").exists()
