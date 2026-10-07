from __future__ import annotations

import json
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


def test_parse_range() -> None:
    assert audit.parse_range("1-3") == (1, 3)


def test_file_entrypoint_audits_real_module(tmp_path: Path) -> None:
    """The post-build-review file entrypoint must import the shared config."""
    root = Path(__file__).resolve().parents[2]
    output = tmp_path / "audit.json"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit/track_deterministic_audit.py",
            "--track",
            "bio",
            "--slugs",
            "oleksandr-bilash",
            "--format",
            "json",
            "--fail-on",
            "never",
            "--output",
            str(output),
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert report["track"] == "bio"
    assert report["summary"]["modules_selected"] == 1
    assert report["summary"]["modules_built"] == 1


def test_file_entrypoint_rejects_invalid_range(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    output = tmp_path / "invalid-audit.json"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit/track_deterministic_audit.py",
            "--track",
            "bio",
            "--range",
            "not-a-range",
            "--output",
            str(output),
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 2, result.stdout + result.stderr
    assert "Range must be N-M, got: not-a-range" in result.stderr
    assert "ImportError" not in result.stderr
    assert result.stdout == ""
    assert not output.exists()


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
            ["a1", "sounds-letters-and-hello", "--dry-run"],
            0,
            "DRY RUN: sounds-letters-and-hello",
        ),
        ("scripts/audit_module.py", ["--help"], 0, "usage: audit_module.py"),
        ("scripts/analytics/vocab_progression.py", ["--help"], 0, "usage: vocab_progression.py"),
        ("scripts/generators/generate_a2_plans.py", ["--help"], 0, "usage: generate_a2_plans.py"),
        ("scripts/rag_batch_verify.py", ["--help"], 0, "usage: rag_batch_verify.py"),
        ("scripts/validate_plan_config.py", ["--help"], 0, "usage: validate_plan_config.py"),
    ],
)
def test_config_consumer_file_launches_without_pythonpath(
    tmp_path: Path, entrypoint: str, arguments: list[str], exit_code: int, expected_output: str
) -> None:
    """Real file launches must work even outside the repository cwd."""
    root = Path(__file__).resolve().parents[2]
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


@pytest.mark.parametrize(
    ("path_order", "module_name"),
    [
        (["."], "scripts.audit.config"),
        (["scripts"], "audit.config"),
        (["scripts/audit", "scripts"], "audit.config"),
        (["scripts/audit", "scripts"], "config"),
    ],
)
def test_shared_config_resolves_real_policy_for_import_orders(
    tmp_path: Path, path_order: list[str], module_name: str
) -> None:
    """Resolve the real policy for package, scripts-only and audit-first loads."""
    root = Path(__file__).resolve().parents[2]
    paths = [str(root / entry) for entry in path_order]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    code = f"""
import importlib
import json
import sys
from pathlib import Path

root = Path({str(root)!r})
sys.path = {paths!r} + [
    entry for entry in sys.path
    if entry and Path(entry).resolve() not in (root, root / 'scripts', root / 'scripts/audit')
]
config = importlib.import_module({module_name!r})
shared = config.shared_get_immersion_range
assert Path(shared.__code__.co_filename).resolve() == root / 'scripts/config.py'
assert config.get_a1_immersion_range(1) == shared('a1', 1)
assert config.get_a2_immersion_range(4) == shared('a2', 4)
assert config.get_b1_immersion_range(3) == shared('b1', 3)
print(json.dumps([shared('a1', 1), shared('a2', 4), shared('b1', 3)]))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == [[40, 55], [85, 100], [100, 100]]
    assert result.stderr == ""


@pytest.mark.parametrize("include_root", [False, True])
def test_audit_first_initialization_uses_canonical_shared_policy(tmp_path: Path, include_root: bool) -> None:
    """Audit-first initialization must resolve qualified policy and public exports."""
    root = Path(__file__).resolve().parents[2]
    paths = ([str(root)] if include_root else []) + [str(root / "scripts/audit"), str(root / "scripts")]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    code = f"""
import importlib
import sys
from pathlib import Path

root = Path({str(root)!r})
sys.path = {paths!r} + [
    entry for entry in sys.path
    if entry and Path(entry).resolve() not in (root, root / 'scripts', root / 'scripts/audit')
]
package = importlib.import_module('audit')
checks = importlib.import_module('audit.checks.learner_state')
canonical = importlib.import_module('scripts.config')
assert Path(canonical.__file__).resolve() == root / 'scripts/config.py'
assert checks.get_immersion_structural is canonical.get_immersion_structural
assert canonical.get_immersion_range('a1', 1) == (40, 55)
assert package.__all__ == ['audit_module', 'check_learner_state']
assert package.check_learner_state is checks.check_learner_state
assert package.audit_module is importlib.import_module('audit.core').audit_module
assert sys.path.count(str(root)) == 1
assert 'config' not in sys.modules
print('canonical policy and audit exports resolved')
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "canonical policy and audit exports resolved\n"
    assert result.stderr == ""


def test_audit_initialization_restores_import_paths_once(monkeypatch) -> None:
    """Bootstrap missing paths without duplicating them on repeat initialization."""
    import importlib

    import scripts.audit as package

    root = Path(__file__).resolve().parents[2]
    scripts = root / "scripts"
    exports = (package.audit_module, package.check_learner_state)
    monkeypatch.setattr(sys, "path", [entry for entry in sys.path if entry not in (str(root), str(scripts))])

    importlib.reload(package)

    assert sys.path[0] == str(root)
    assert sys.path.count(str(root)) == 1
    assert sys.path.count(str(scripts)) == 1
    assert (package.audit_module, package.check_learner_state) == exports

    importlib.reload(package)

    assert sys.path.count(str(root)) == 1
    assert sys.path.count(str(scripts)) == 1
    assert (package.audit_module, package.check_learner_state) == exports


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


def test_vocabulary_validation_reports_missing_translation(tmp_path, monkeypatch) -> None:
    patch_roots(monkeypatch, tmp_path)
    write_minimal_module(tmp_path, "test-one", 1)
    vocab = tmp_path / "curriculum" / "l2-uk-en" / "b2" / "test-one" / "vocabulary.yaml"
    vocab.write_text("- word: слово\n", encoding="utf-8")

    paths = audit.select_modules("b2", (1, 1), None)[0]
    findings = audit.check_vocabulary_yaml(paths)

    assert any(item.category == "vocabulary_validity" and item.severity == "high" for item in findings)


def test_surface_gate_reports_b2_english_leak(tmp_path, monkeypatch) -> None:
    patch_roots(monkeypatch, tmp_path)
    write_minimal_module(tmp_path, "test-one", 1, english_leak=True)

    paths = audit.select_modules("b2", (1, 1), None)[0]
    findings = audit.check_surface(paths)

    assert any(item.category == "english_internal_leakage" and item.severity == "high" for item in findings)


def test_internal_leakage_skips_resource_provenance_key(tmp_path, monkeypatch) -> None:
    """`chunk_id:` / `packet_chunk_id:` keys in resources.yaml are non-rendering
    corpus-provenance metadata (consumed by the plan-reference gate), so a bare
    provenance-key line must NOT be flagged — but prose mentioning the term still is."""
    patch_roots(monkeypatch, tmp_path)
    write_minimal_module(tmp_path, "test-one", 1)
    resources = tmp_path / "curriculum" / "l2-uk-en" / "b2" / "test-one" / "resources.yaml"
    resources.write_text(
        "- title: Буквар 1 клас, с. 24\n"
        "  role: textbook\n"
        "  chunk_id: 1-klas-bukvar-2018_s0023\n"
        "  packet_chunk_id: 1-klas-bukvar-2018_s0024\n"
        "  notes: retrieved via search_text; no literal chunk_id in plan\n",
        encoding="utf-8",
    )

    paths = audit.select_modules("b2", (1, 1), None)[0]
    findings = audit.check_internal_leakage(paths)
    leaks = [f for f in findings if f.file and f.file.endswith("resources.yaml")]

    # The bare provenance-key lines are skipped...
    assert not any(f.line == 3 for f in leaks), "chunk_id: key line should not be flagged"
    assert not any(f.line == 4 for f in leaks), "packet_chunk_id: key line should not be flagged"
    # ...but the notes prose that MENTIONS chunk_id still leaks (renders in Resources tab).
    assert any(f.line == 5 for f in leaks), "notes prose mentioning chunk_id must still be flagged"


def test_module_paths_wiki_resolution() -> None:
    # 1. A1 should point under pedagogy/a1
    a1_module = DummyModule("greeting", "Greeting", "a1", 1)
    a1_paths = audit.module_paths("a1", a1_module)
    assert "wiki/pedagogy/a1/greeting.md" in a1_paths.wiki.as_posix()
    assert "wiki/pedagogy/a1/greeting.sources.yaml" in a1_paths.wiki_sources.as_posix()

    # 2. B1 should point under grammar/b1
    b1_module = DummyModule("aspect", "Aspect", "b1", 1)
    b1_paths = audit.module_paths("b1", b1_module)
    assert "wiki/grammar/b1/aspect.md" in b1_paths.wiki.as_posix()
    assert "wiki/grammar/b1/aspect.sources.yaml" in b1_paths.wiki_sources.as_posix()

    # 3. Seminar tracks should use the compiler's track-aware write domains
    bio_module = DummyModule("oleksandr-bilash", "Oleksandr Bilash", "bio", 1)
    bio_paths = audit.module_paths("bio", bio_module)
    assert "wiki/figures/oleksandr-bilash.md" in bio_paths.wiki.as_posix()
    assert "wiki/figures/oleksandr-bilash.sources.yaml" in bio_paths.wiki_sources.as_posix()
    assert "wiki/grammar/bio" not in bio_paths.wiki.as_posix()
    assert "wiki/grammar/bio" not in bio_paths.wiki_sources.as_posix()

    hist_module = DummyModule("kyivan-rus", "Kyivan Rus", "hist", 1)
    hist_paths = audit.module_paths("hist", hist_module)
    assert "wiki/periods/kyivan-rus.md" in hist_paths.wiki.as_posix()
    assert "wiki/periods/kyivan-rus.sources.yaml" in hist_paths.wiki_sources.as_posix()

    folk_module = DummyModule("koliadky-shchedrivky", "Koliadky", "folk", 1)
    folk_paths = audit.module_paths("folk", folk_module)
    assert "wiki/folk/ritual/koliadky-shchedrivky.md" in folk_paths.wiki.as_posix()
    assert "wiki/folk/ritual/koliadky-shchedrivky.sources.yaml" in folk_paths.wiki_sources.as_posix()

    # 4. Unknown tracks preserve the compiler fallback domain.
    unmapped_module = DummyModule("topic", "Topic", "unknown-track", 1)
    unmapped_paths = audit.module_paths("unknown-track", unmapped_module)
    assert "wiki/unknown-track/topic.md" in unmapped_paths.wiki.as_posix()
    assert "wiki/unknown-track/topic.sources.yaml" in unmapped_paths.wiki_sources.as_posix()


def test_a1_config_requires_wiki_like_b2() -> None:
    """#4305 user decision 2026-07-06: A1 (published entry-point track)
    promotes wiki + wiki_sources to required, mirroring B2; resources stays
    optional and optional_missing stays info-level."""
    import yaml

    from audit.track_deterministic_audit import DEFAULT_CONFIG, merged_track_config

    config = yaml.safe_load(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    for track in ("a1", "b2"):
        merged = merged_track_config(config, track)
        assert "wiki" in merged["required_files"], track
        assert "wiki_sources" in merged["required_files"], track
        assert "resources" in merged["optional_files"], track
        assert merged["severity"]["optional_missing"] == "info", track
