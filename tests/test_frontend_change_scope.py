"""Drift guard + unit coverage for frontend CI cheap-exit (#6917)."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from scripts.ci import frontend_change_scope as scope

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github/workflows/ci.yml"
_DENOMINATOR = _REPO_ROOT / scope.DENOMINATOR_REL


def test_denominator_is_single_source_and_loadable() -> None:
    data = scope.load_denominator(_DENOMINATOR)
    assert data["schema_version"] == "frontend_change_denominator_v1"
    assert data["version"] == "1"
    assert "site/" in data["paths"]
    assert "scripts/atlas/" in data["paths"]
    assert "scripts/lexicon/" in data["paths"]
    assert "scripts/audit/generate_search_index.py" in data["paths"]
    assert "scripts/audit/generate_daily_pool.py" in data["paths"]
    assert ".python-version" in data["paths"]
    assert ".github/workflows/ci.yml" in data["paths"]


def test_path_matching_covers_prefixes_and_exact_entries() -> None:
    patterns = scope.load_denominator()["paths"]
    assert scope.path_in_denominator("site/package.json", patterns)
    assert scope.path_in_denominator("scripts/atlas/atlas_db.py", patterns)
    assert scope.path_in_denominator("scripts/lexicon/manifest_io.py", patterns)
    assert scope.path_in_denominator("scripts/audit/generate_search_index.py", patterns)
    assert scope.path_in_denominator(".python-version", patterns)
    assert scope.path_in_denominator(".github/workflows/ci.yml", patterns)
    assert not scope.path_in_denominator("scripts/services.sh", patterns)
    assert not scope.path_in_denominator("dashboards/work.html", patterns)
    assert not scope.path_in_denominator("package.json", patterns)
    assert not scope.path_in_denominator("scripts/audit/meta_validator.py", patterns)


def test_docs_only_change_cheap_exits() -> None:
    run, line, matched = scope.decide_from_changed(
        ["docs/runbooks/ci-gate.md", "scripts/services.sh"],
    )
    assert run is False
    assert matched == []
    assert "decision=cheap_exit" in line
    assert "denominator_version=1" in line
    assert "changed_files=2" in line
    assert "matched=0" in line


def test_site_touch_runs_frontend() -> None:
    run, line, matched = scope.decide_from_changed(["site/src/pages/index.astro"])
    assert run is True
    assert matched == ["site/src/pages/index.astro"]
    assert "decision=run" in line


def test_cyrillic_site_path_runs_frontend() -> None:
    """Non-ASCII under site/ must decide run (F1: quotePath must not C-quote it away)."""
    path = "site/src/слово.ts"
    run, line, matched = scope.decide_from_changed([path])
    assert run is True
    assert matched == [path]
    assert "decision=run" in line


def test_changed_files_uses_quote_path_false_and_nul_split(tmp_path: Path) -> None:
    """NUL-split + quotePath=false keeps Cyrillic / quote / backslash names literal."""
    cyrillic = "site/src/слово.ts"
    quoted_name = 'site/src/weird"name.ts'
    backslash_name = r"site/src/weird\name.ts"
    payload = "\0".join([cyrillic, quoted_name, backslash_name, ""]).encode("utf-8")

    fake = MagicMock()
    fake.stdout = payload
    fake.returncode = 0

    with patch("subprocess.run", return_value=fake) as run_mock:
        paths = scope.changed_files("base...HEAD", cwd=tmp_path)

    assert paths == sorted([cyrillic, quoted_name, backslash_name])
    cmd = run_mock.call_args.args[0]
    assert cmd[:3] == ["git", "-c", "core.quotePath=false"]
    assert "--name-only" in cmd
    assert "-z" in cmd
    assert run_mock.call_args.kwargs.get("text") is not True


def test_changed_files_rejects_c_quoted_octal_as_site_prefix() -> None:
    """Guard: C-quoted octal (legacy quotePath=true) must NOT match site/."""
    # What default quotePath emits for site/src/слово.ts — must not cheap-exit-match.
    c_quoted = '"site/src/\\321\\201\\320\\273\\320\\276\\320\\262\\320\\276.ts"'
    assert not scope.path_in_denominator(c_quoted, ["site/"])


def test_git_diff_failed_writes_step_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)

    def boom(*_args: object, **_kwargs: object) -> None:
        raise subprocess.CalledProcessError(128, ["git", "diff"])

    with patch.object(scope, "changed_files", side_effect=boom):
        assert scope.main(["--base", "abc123"]) == 0

    text = summary.read_text(encoding="utf-8")
    assert "reason=git_diff_failed" in text
    assert "decision=run" in text


def test_resolve_hydrate_entrypoints_from_package_json() -> None:
    entrypoints = scope.resolve_hydrate_entrypoints()
    assert "site/scripts/hydrate-manifest.mjs" in entrypoints
    assert "site/scripts/hydrate-practice-deck.mjs" in entrypoints
    assert "site/scripts/hydrate-lexicon-api-shards.ts" in entrypoints
    assert "scripts/atlas/atlas_db.py" in entrypoints
    assert "scripts/audit/generate_search_index.py" in entrypoints
    assert "scripts/audit/generate_daily_pool.py" in entrypoints


def test_hydrate_entrypoints_stay_inside_denominator() -> None:
    entrypoints = scope.assert_hydrate_entrypoints_in_denominator()
    assert entrypoints  # non-empty proof the resolver engaged package.json


def test_removing_denominator_entry_fails_hydrate_guard(tmp_path: Path) -> None:
    """Mutation check: drop an outside-site hydrate path → guard must fail."""
    original = scope.load_denominator()
    mutated = copy.deepcopy(original)
    mutated["paths"] = [p for p in mutated["paths"] if p != "scripts/atlas/"]
    assert "scripts/atlas/" not in mutated["paths"]

    denom_path = tmp_path / "denominator.json"
    denom_path.write_text(json.dumps(mutated), encoding="utf-8")
    loaded = scope.load_denominator(denom_path)

    with pytest.raises(AssertionError, match=r"scripts/atlas/atlas_db\.py"):
        scope.assert_hydrate_entrypoints_in_denominator(denominator=loaded)


def test_ci_yml_uses_shared_scope_helper_without_job_level_frontend_skip() -> None:
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]

    assert "if" not in jobs["frontend"]
    assert set(jobs["ci-gate"]["needs"]) == {
        "pytest-plan",
        "pytest-fastlane",
        "python",
        "contracts",
        "frontend",
        "coverage-floor",
    }

    for job_name in ("frontend", "frontend-e2e"):
        steps = jobs[job_name]["steps"]
        scope_step = next(s for s in steps if s.get("id") == "scope")
        assert "frontend_change_scope.py" in scope_step["run"]
        assert "pull_request.base.sha" in scope_step["env"]["BASE_SHA"]
        assert "merge_group.base_sha" in scope_step["env"]["BASE_SHA"]
        assert "github.event.before" in scope_step["env"]["BASE_SHA"]

        checkout = steps[0]
        assert checkout["with"]["fetch-depth"] == 0

        gated = [s for s in steps[2:] if s.get("if")]
        assert gated, f"{job_name} must gate post-scope steps"
        assert all("steps.scope.outputs.run == 'true'" in str(s["if"]) for s in gated)
