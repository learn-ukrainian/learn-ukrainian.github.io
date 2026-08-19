"""Drift guard + unit coverage for frontend CI cheap-exit (#6917 / #6930)."""

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


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, timeout=30).strip()


def _init_fixture_repo(root: Path) -> dict[str, str]:
    """Build a mini repo that reproduces the #6930 moved-base over-count.

    Returns SHAs: fork_point, base_tip (main after denom advance), branch_head
    (out-of-scope only), branch_head_in_scope (touches site/).
    """
    _git(root, "init")
    _git(root, "config", "user.email", "ci@example.com")
    _git(root, "config", "user.name", "ci")
    (root / "docs").mkdir()
    (root / "site").mkdir()
    (root / "docs" / "a.md").write_text("docs\n", encoding="utf-8")
    (root / "site" / "index.html").write_text("site\n", encoding="utf-8")
    denom = {
        "schema_version": "frontend_change_denominator_v1",
        "version": "1",
        "paths": ["site/", "scripts/lexicon/"],
    }
    (root / "scripts" / "ci").mkdir(parents=True)
    (root / "scripts" / "ci" / "frontend_change_denominator.json").write_text(
        json.dumps(denom),
        encoding="utf-8",
    )
    _git(root, "add", ".")
    _git(root, "commit", "-m", "root")
    fork = _git(root, "rev-parse", "HEAD")
    _git(root, "branch", "-M", "main")

    _git(root, "checkout", "-b", "feature")
    (root / "docs" / "feature.md").write_text("feature only\n", encoding="utf-8")
    _git(root, "add", "docs/feature.md")
    _git(root, "commit", "-m", "feature docs")
    branch_out = _git(root, "rev-parse", "HEAD")

    (root / "site" / "extra.html").write_text("in scope\n", encoding="utf-8")
    _git(root, "add", "site/extra.html")
    _git(root, "commit", "-m", "feature site")
    branch_in = _git(root, "rev-parse", "HEAD")

    # Reset feature tip to out-of-scope-only for the cheap_exit scenario, but
    # keep branch_in SHA reachable via the object store.
    _git(root, "reset", "--hard", branch_out)

    _git(root, "checkout", "main")
    (root / "site" / "package.json").write_text('{"name":"moved-base"}\n', encoding="utf-8")
    _git(root, "add", "site/package.json")
    _git(root, "commit", "-m", "main advances with denominator file")
    base_tip = _git(root, "rev-parse", "HEAD")

    return {
        "fork": fork,
        "base_tip": base_tip,
        "branch_out": branch_out,
        "branch_in": branch_in,
        "denominator": str(root / "scripts" / "ci" / "frontend_change_denominator.json"),
    }


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

    with (
        patch.object(scope, "resolve_git_range", return_value="abc...HEAD"),
        patch.object(scope, "changed_files", side_effect=boom),
    ):
        assert scope.main(["--base", "abc123", "--event", "pull_request"]) == 0

    text = summary.read_text(encoding="utf-8")
    assert "reason=git_diff_failed" in text
    assert "decision=run" in text


def test_range_mode_for_event() -> None:
    assert scope.range_mode_for_event("pull_request") == "merge-base"
    assert scope.range_mode_for_event("merge_group") == "merge-base"
    assert scope.range_mode_for_event("push") == "two-dot"
    assert scope.range_mode_for_event("") == "two-dot"


def test_moved_base_out_of_scope_cheap_exits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#6930: main advanced with a denominator file; branch only docs → cheap_exit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    shas = _init_fixture_repo(repo)
    monkeypatch.chdir(repo)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)

    two_dot = scope.changed_files(f"{shas['base_tip']}..{shas['branch_out']}", cwd=repo)
    mb_range = scope.resolve_git_range(
        shas["base_tip"],
        shas["branch_out"],
        mode="merge-base",
        cwd=repo,
    )
    merge_base_files = scope.changed_files(mb_range, cwd=repo)

    # Quote the over-count: two-dot includes main's site/package.json.
    assert "site/package.json" in two_dot
    assert "docs/feature.md" in two_dot
    assert "site/package.json" not in merge_base_files
    assert merge_base_files == ["docs/feature.md"]

    assert (
        scope.main(
            [
                "--base",
                shas["base_tip"],
                "--head",
                shas["branch_out"],
                "--event",
                "pull_request",
                "--denominator",
                shas["denominator"],
            ],
        )
        == 0
    )


def test_moved_base_out_of_scope_prints_cheap_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    shas = _init_fixture_repo(repo)
    monkeypatch.chdir(repo)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)

    scope.main(
        [
            "--base",
            shas["base_tip"],
            "--head",
            shas["branch_out"],
            "--event",
            "pull_request",
            "--denominator",
            shas["denominator"],
        ],
    )
    out = capsys.readouterr().out
    assert "decision=cheap_exit" in out
    assert "matched=0" in out


def test_moved_base_branch_touches_denominator_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Inverse: branch itself touches site/ after base moved → run."""
    repo = tmp_path / "repo"
    repo.mkdir()
    shas = _init_fixture_repo(repo)
    monkeypatch.chdir(repo)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)

    scope.main(
        [
            "--base",
            shas["base_tip"],
            "--head",
            shas["branch_in"],
            "--event",
            "pull_request",
            "--denominator",
            shas["denominator"],
        ],
    )
    out = capsys.readouterr().out
    assert "decision=run" in out
    assert "matched=" in out
    assert "matched=0" not in out


def test_two_dot_mutation_defeats_moved_base_cheap_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Mutation check: force two-dot on a PR-shaped event → cheap_exit guard fails."""
    repo = tmp_path / "repo"
    repo.mkdir()
    shas = _init_fixture_repo(repo)
    monkeypatch.chdir(repo)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)

    with patch.object(scope, "range_mode_for_event", return_value="two-dot"):
        scope.main(
            [
                "--base",
                shas["base_tip"],
                "--head",
                shas["branch_out"],
                "--event",
                "pull_request",
                "--denominator",
                shas["denominator"],
            ],
        )
    out = capsys.readouterr().out
    # Two-dot sees main's site/package.json → falsely decides run.
    assert "decision=run" in out
    assert "matched=0" not in out


def test_merge_base_unresolvable_fails_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)

    with patch.object(scope, "git_merge_base", side_effect=scope.MergeBaseError("shallow")):
        assert scope.main(["--base", "abc123", "--head", "def456", "--event", "pull_request"]) == 0

    text = summary.read_text(encoding="utf-8")
    assert "reason=merge_base_unresolvable" in text
    assert "decision=run" in text


def test_push_event_uses_two_dot_range(tmp_path: Path) -> None:
    assert scope.resolve_git_range("aaa", "bbb", mode="two-dot", cwd=tmp_path) == "aaa..bbb"


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
    # Two-tier cutover (#6943 stage 2): CI Gate also needs `ruff` so the
    # pull_request light tier can require lint without the four-shard suite.
    assert set(jobs["ci-gate"]["needs"]) == {
        "ruff",
        "landing-class",
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
        assert "pull_request.head.sha" in scope_step["env"]["HEAD_SHA"]
        assert "merge_group.head_sha" in scope_step["env"]["HEAD_SHA"]
        assert "github.sha" in scope_step["env"]["HEAD_SHA"]
        assert scope_step["env"]["EVENT_NAME"] == "${{ github.event_name }}"
        assert "--event" in scope_step["run"]
        assert "--head" in scope_step["run"]

        checkout = steps[0]
        assert checkout["with"]["fetch-depth"] == 0

        gated = [s for s in steps[2:] if s.get("if")]
        assert gated, f"{job_name} must gate post-scope steps"
        assert all("steps.scope.outputs.run == 'true'" in str(s["if"]) for s in gated)
