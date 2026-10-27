"""Drift guard + unit coverage for frontend CI cheap-exit (#6917 / #6930)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from scripts.ci import frontend_change_scope as scope

pytestmark = pytest.mark.repo_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github/workflows/ci.yml"
_ACTION = _REPO_ROOT / ".github/actions/python-ci-env/action.yml"
_LOCK = _REPO_ROOT / "requirements-lock.txt"
_DENOMINATOR = _REPO_ROOT / scope.DENOMINATOR_REL


def _git(cwd: Path, *args: str) -> str:
    env = os.environ | {"AGENT_NO_MERGE": "0"}
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, timeout=30, env=env).strip()


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
    assert "reason=git_diff_failed exit=128" in text
    assert "decision=run" in text


def test_git_merge_base_timeout_raises_merge_base_error() -> None:
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "merge-base"], 30)):
        with pytest.raises(scope.MergeBaseError, match=r"timed out after 30s"):
            scope.git_merge_base("base_sha", "head_sha")


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


def test_ci_yml_frontend_job_runs_only_through_the_scope_step() -> None:
    """Every frontend step after the scope decision is gated on its `run` output."""
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    assert "frontend-e2e" not in jobs
    frontend = jobs["frontend"]
    # Full-tier events run frontend; PR admission leaves it to the merge candidate.
    assert frontend["if"] == (
        "${{ !cancelled() && (github.event_name == 'merge_group' || "
        "github.event_name == 'schedule' || github.event_name == 'workflow_dispatch') }}"
    )
    assert "reuse" not in frontend.get("needs", [])
    assert "frontend" in jobs["ci-gate"]["needs"]
    steps = frontend["steps"]
    scope_index = next(index for index, step in enumerate(steps) if step.get("id") == "scope")
    assert "scripts/ci/frontend_change_scope.py" in steps[scope_index]["run"]
    assert "github.event.merge_group.base_sha" in steps[scope_index]["env"]["BASE_SHA"]
    for step in steps[scope_index + 1 :]:
        assert step.get("if") == "steps.scope.outputs.run == 'true'", step


def _declared_selector_graph(manifest: dict) -> dict:
    """Project declared manifest edges into the graph shape ``affected`` reads.

    ``affected`` adds every declared pair unless the repository import scan
    reports an unresolved edge, which selects all nodes. The declared closure
    is therefore the guaranteed floor of the real selection, and it decides
    rule mutations without the full repository scan (#11411).
    """
    return {
        "file_edges": [],
        "unresolved_edges": [],
        "missing_mandatory_edges": [],
        "node_edges": sorted({(edge["producer"], edge["consumer"]) for edge in manifest["edges"]}),
    }


def test_component_ownership_does_not_expand_frontend_cheap_exit() -> None:
    """Shared/all-node obligations must not replace today's cheap-exit policy."""
    from scripts.ci import components

    manifest = components.load_manifest()
    owned = components.affected(["scripts/config.py"], manifest, _declared_selector_graph(manifest))
    assert set(owned["components"]) == set(components.NODE_IDS)
    run, _, matched = scope.decide_from_changed(["scripts/config.py", "docs/a.md"])
    assert run is False and matched == []
