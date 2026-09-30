"""Kimi: web, UI and backend coding only — the path allowlist, the one gate, and its entry points."""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import subprocess
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.agent_runtime import kimi_admission
from scripts.fleet_comms.endpoints import load_endpoint_registry
from scripts.fleet_comms.request_executor import RequestExecutor
from tests.agent_runtime.adapters.kimi_admitted import admitted_tool_config

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOKEN = "KIMI CODING-ONLY"
_BACKEND_OWNED = ("scripts/agent_runtime/runner.py", "tests/agent_runtime/test_runner.py")
_UI_OWNED = ("site/src/components/LiveStatus.tsx", "site/src/styles/match-up.css", "site/vitest.config.ts")


_REAL_RUN = subprocess.run
_REAL_POPEN = subprocess.Popen
# Read-only git plumbing the Kimi gate runs to read the tree a worker starts from.
_GATE_GIT = frozenset({"rev-parse", "ls-tree", "cat-file"})


def _fail(*_args, **_kwargs):
    raise AssertionError("a refused Kimi call reached a side effect")


def _run(cmd, **kwargs) -> subprocess.CompletedProcess:
    """``subprocess.run`` itself, even while a test has replaced ``run`` and ``Popen`` with a failure."""
    patched = subprocess.Popen
    subprocess.Popen = _REAL_POPEN
    try:
        return _REAL_RUN(cmd, **kwargs)
    finally:
        subprocess.Popen = patched


def _plumbing_only(monkeypatch) -> list[str]:
    """Let ``subprocess.run`` run only read-only git plumbing; returns the subcommands that ran."""
    ran: list[str] = []

    def run(cmd, *args, **kwargs):
        if list(cmd[:1]) != ["git"] or cmd[1] not in _GATE_GIT:
            raise AssertionError(f"a Kimi admission check ran {cmd!r}")
        ran.append(cmd[1])
        return _run(cmd, *args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", run)
    return ran


def _head(repo: Path = _REPO_ROOT) -> str:
    return _run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def _refusal(participants=("kimi",), models=(), **overrides) -> str | None:
    """The gate's refusal, with owned paths read on disk under ``repo_root`` unless ``trees`` is given."""
    kwargs = {"mode": "workspace-write", "paths": _BACKEND_OWNED, "repo": "public-monorepo", "repo_root": _REPO_ROOT}
    kwargs.update(overrides)
    if "trees" not in kwargs:
        kwargs["trees"] = (kimi_admission.DirectoryTree(kwargs["repo_root"]),) if kwargs["repo_root"] else ()
    try:
        kimi_admission.refuse_kimi_if_disallowed(participants, models, **kwargs)
    except kimi_admission.KimiAdmissionRefused as exc:
        return str(exc)
    return None


# --- the allowlist ---------------------------------------------------------------

# Admitted: Cyrillic-free UI code, the named site/src/lib helpers, site config,
# verified backend packages with their tests, CI and Dagger, and new files there.
# Paths are normalized first.
ADMITTED_PATHS = (
    "site/src/components/Card.astro",
    "site/src/components/LiveStatus.tsx",
    "site/src/components/practice/NewPanel.tsx",
    "site/src/layouts/NewLayout.astro",
    "site/src/pages/index.astro",
    "site/src/styles/match-up.css",
    "site/src/css/x.css",
    "site/src/assets/logo.svg",
    "site/src/lib/arc.ts",
    "site/src/lib/doc-nav.ts",
    "site/src/lib/readings.ts",
    "site/src/lib/a1-archive-routes.ts",
    "site/vitest.config.ts",
    "scripts/agent_runtime/runner.py",
    "scripts/api/state_router.py",
    "scripts/orchestration/dispatch_admission.py",
    "scripts/ci/pytest_shards.py",
    "scripts/fleet_comms/authority.py",
    "scripts/hygiene/branch_sweep.py",
    "scripts/storage/topology.py",
    "tests/agent_runtime/test_runner.py",
    "tests/storage/test_artifacts.py",
    ".github/workflows/ci.yml",
    ".github/actions/python-ci-env/action.yml",
    ".dagger/src/learn_ukrainian_ci/main.py",
    "./scripts/api/x.py",
    "scripts//ci/x.py",
    # Directory and glob scopes whose every file is allowlisted and Cyrillic-free.
    "scripts/storage/**",
    "scripts/hygiene/",
    "scripts/fleet_comms",
    "site/src/pages/api/**",
    "site/src/components/Live*.tsx",
)

# Refused: everything not on the allowlist (Ukrainian dataset exporters, wiki
# prompts, language tests and fixtures, site language test cases, curriculum,
# lexicon, rules, instructions, private state, non-UI site files) and the named
# exclusions inside allowlisted roots.
REFUSED_PATHS = (
    "scripts/dataset/export_ukrainian_pedagogy_dataset.py",
    "scripts/wiki/prompts/compile_pedagogy_brief.md",
    "tests/test_euphony.py",
    "tests/fixtures/messages.po",
    "site/tests/unit/adjective-mechanics.test.ts",
    "site/e2e/nav.spec.ts",
    "scripts/audit/naturalness_check.py",
    "scripts/curriculum/resolver/tokenize.py",
    "curriculum/l2-uk-en/a1/lesson.mdx",
    "wiki/topic.md",
    "data/sources.db",
    "registry/lexicon/x.yaml",
    "site/src/content/docs/a1/lesson.mdx",
    "site/src/data/words.json",
    "site/src/lexicon/entry.ts",
    "site/src/lib/i18n/chrome.ts",
    "site/src/lib/lexicon/adjective-mechanics.ts",
    "site/src/lib/new-helper.ts",
    "scripts/lexicon/x.py",
    "scripts/verification/stress.py",
    "scripts/practice/noun_mechanics_engine.py",
    "scripts/pipeline/stress_annotator.py",
    "scripts/launchd/x.plist",
    "scripts/delegate.py",
    "scripts/config/model_catalog.yaml",
    "docs/best-practices/code-quality.md",
    "agents_extensions/shared/rules/model-assignment.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/settings.json",
    ".github/CODEOWNERS",
    ".github/ISSUE_TEMPLATE/naturalness-quality.md",
    "site/package.json",
    "README.md",
    # Exclusions inside allowlisted roots.
    "scripts/agent_runtime/kimi_admission.py",
    "scripts/agent_runtime/kimi_boundary.py",
    "scripts/agent_runtime/kimi_hooks/pre-commit",
    "scripts/agent_runtime/env_sanitize.py",
    "scripts/agent_runtime/adapters/kimi.py",
    "scripts/agent_runtime/profiles/acpx-grok-sealed-review.md",
    "scripts/api/hramatka_generator.py",
    "scripts/api/sources_router.py",
    "tests/api/test_hramatka_router.py",
    "scripts/orchestration/curriculum_readiness.py",
    "scripts/orchestration/prompt_contracts.py",
    "tests/orchestration/test_curriculum_readiness.py",
    # A differently cased spelling is not the allowlisted directory.
    "Scripts/agent_runtime/runner.py",
    "site/src/Components/Card.astro",
)


@pytest.mark.parametrize("path", ADMITTED_PATHS)
def test_allowlisted_paths_are_admitted(path):
    assert kimi_admission.owned_path_reason(path) is None
    assert _refusal(paths=(path,)) is None


@pytest.mark.parametrize("path", REFUSED_PATHS)
def test_everything_off_the_allowlist_is_refused(path):
    assert kimi_admission.owned_path_reason(path)
    message = _refusal(paths=("scripts/agent_runtime/runner.py", path))
    assert message and "owned path" in message


def test_every_allowlisted_root_and_exclusion_carries_a_reason():
    for table in (kimi_admission.KIMI_OWNED_ROOTS, kimi_admission.KIMI_EXCLUDED_PATHS):
        for key, reason in table.items():
            assert reason.strip(), key


@pytest.mark.repo_wide
def test_every_allowlisted_root_exists_in_the_repository():
    tracked = subprocess.run(
        ["git", "ls-files", "site/src", "scripts", "tests", ".github", ".dagger"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.splitlines()
    for root in kimi_admission.KIMI_OWNED_ROOTS:
        if root.endswith("/"):
            assert any(path.startswith(root) for path in tracked), root
        else:
            assert root in tracked, root


def test_every_backend_package_admits_its_tests():
    for root in kimi_admission.KIMI_OWNED_ROOTS:
        if root.startswith("scripts/"):
            assert f"tests/{root.removeprefix('scripts/')}" in kimi_admission.KIMI_OWNED_ROOTS


@pytest.mark.parametrize(
    ("path", "canonical"),
    [
        ("site//src/content/docs/x.mdx", "site/src/content/docs/x.mdx"),
        ("./docs/../docs/x", "docs/x"),
        ("scripts/api/../../docs/x.md", "docs/x.md"),
        ("site/src/pages/../content/x.mdx", "site/src/content/x.mdx"),
        ("site/src/components/../../src/lib/i18n/x.ts", "site/src/lib/i18n/x.ts"),
        ("scripts\\api\\..\\..\\CLAUDE.md", "CLAUDE.md"),
    ],
)
def test_paths_are_normalized_before_the_allowlist(path, canonical):
    assert kimi_admission.normalize_owned_path(path) == canonical
    message = _refusal(paths=(path,))
    assert message and f"owned path {canonical!r}" in message


@pytest.mark.parametrize(
    "path", ["/etc/passwd", "/home/me/repo/scripts/x.py", "~/x.py", "C:/x.py", "../x.py", "scripts/../../x.py", ".", ""]
)
def test_absolute_and_escaping_paths_are_refused(path):
    assert kimi_admission.normalize_owned_path(path) is None
    message = _refusal(paths=(path,))
    assert message and "is not a repository-relative path" in message


# --- the content rule: Cyrillic text is Ukrainian content -----------------------------


@pytest.mark.parametrize(
    "path",
    [
        "site/src/components/CountSyllables.tsx",
        "site/src/components/practice/SettingsDrawer.tsx",
        "site/src/styles/course.css",
        "site/src/layouts/CourseLayout.astro",
        "site/astro.config.mjs",
    ],
)
def test_an_allowlisted_file_with_cyrillic_text_is_refused(path):
    assert kimi_admission.owned_path_reason(path) is None  # on the allowlist by path
    message = _refusal(paths=(path,))
    assert message and "Ukrainian content" in message and path in message


def test_a_cyrillic_free_component_is_admitted():
    path = "site/src/components/LiveStatus.tsx"
    assert not kimi_admission.CYRILLIC.search((_REPO_ROOT / path).read_text(encoding="utf-8"))
    assert _refusal(paths=(path,)) is None


@pytest.mark.parametrize(
    ("scope", "excluded"),
    [
        ("scripts/api/**", "scripts/api/hramatka_"),
        ("scripts/api", "scripts/api/sources_router.py"),
        ("scripts/api/", "scripts/api/hramatka_"),
        ("scripts/orchestration/**", "scripts/orchestration/curriculum_"),
        ("scripts/agent_runtime/**", "scripts/agent_runtime/kimi_admission.py"),
        ("tests/api/test_*.py", "tests/api/test_hramatka_"),
    ],
)
def test_a_broad_scope_that_contains_an_excluded_file_is_refused(scope, excluded):
    message = _refusal(paths=(scope,))
    assert message and f"owned scope {kimi_admission.normalize_owned_path(scope)!r} contains" in message
    assert excluded in message and "narrow it to specific files or clean subdirectories" in message


def test_a_glob_scope_reaching_off_allowlist_files_is_refused():
    message = _refusal(paths=("site/src/*/index.astro",))
    assert message and "owned path" in message


def _scratch_repo(tmp_path: Path) -> Path:
    components = tmp_path / "site" / "src" / "components"
    (components / "clean").mkdir(parents=True)
    (components / "clean" / "Button.tsx").write_text("export const Button = () => null;\n", encoding="utf-8")
    (components / "Lesson.tsx").write_text('export const title = "Урок";\n', encoding="utf-8")
    (components / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\xd0\x9f\xd1\x80\x00\xff")
    (components / "Wide.tsx").write_bytes("export const title = 'Урок';\n".encode("utf-16-le"))
    return tmp_path


_LESSON_CYRILLIC = "Cyrillic text in 'site/src/components/Lesson.tsx'"
_NOT_PLAIN_TEXT = "content that is not plain text"
_SCOPE_CASES = [
    ("site/src/components/**", [_LESSON_CYRILLIC, _NOT_PLAIN_TEXT, "logo.png", "Wide.tsx"]),
    ("site/src/components", [_LESSON_CYRILLIC, _NOT_PLAIN_TEXT]),
    ("site/src/components/*.tsx", [_LESSON_CYRILLIC, "'site/src/components/Wide.tsx'"]),
    ("site/src/components/clean/**", None),
    ("site/src/components/clean/Button.tsx", None),
    # A binary asset or a wide encoding is not plain text, so it cannot be checked.
    ("site/src/components/logo.png", [f"owned file holds {_NOT_PLAIN_TEXT} ('site/src/components/logo.png'"]),
    ("site/src/components/Wide.tsx", [f"owned file holds {_NOT_PLAIN_TEXT}", "UTF-16"]),
    ("site/src/components/New.tsx", None),  # a new file: the finalize check covers what it adds
]


@pytest.mark.parametrize(("scope", "expected"), _SCOPE_CASES)
def test_a_scope_holding_cyrillic_or_non_text_content_is_refused_on_disk(tmp_path, scope, expected):
    message = _refusal(paths=(scope,), repo_root=_scratch_repo(tmp_path), research_track=None)
    if expected is None:
        assert message is None
    else:
        assert message and all(fragment in message for fragment in expected), message


@pytest.mark.parametrize(("scope", "expected"), _SCOPE_CASES)
def test_a_scope_holding_cyrillic_or_non_text_content_is_refused_in_a_commit(tmp_path, monkeypatch, scope, expected):
    """The same rule read with git plumbing from a commit: its files, not a checkout of them."""
    for key in tuple(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    repo = _scratch_repo(tmp_path / "repo")
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "base")
    commit = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "rm", "-r", "-q", "--cached", "site")
    for path in (repo / "site").rglob("*"):  # the checkout no longer holds the files
        if path.is_file():
            path.unlink()
    tree = kimi_admission.CommitTree(repo, commit)
    message = _refusal(paths=(scope,), repo_root=None, trees=(tree,), research_track=None)
    if expected is None:
        assert message is None
    else:
        assert message and all(fragment in message for fragment in expected), message
        assert f"in commit {commit[:12]}" in message


def test_owned_paths_fail_closed_without_a_tree_to_read():
    message = _refusal(paths=("site/src/components/LiveStatus.tsx",), repo_root=None)
    assert message and "cannot be checked for Ukrainian content (no tree to read)" in message


def test_owned_paths_fail_closed_when_the_tree_cannot_be_resolved():
    def unresolvable():
        raise RuntimeError("no base")

    message = _refusal(paths=("site/src/components/LiveStatus.tsx",), trees=unresolvable)
    assert message and "cannot be read for Ukrainian content (no base)" in message


def test_the_tree_is_resolved_only_after_every_policy_check_admits():
    message = _refusal(paths=("site/src/components/LiveStatus.tsx",), mode="read-only", trees=_fail)
    assert message and "--mode read-only" in message


def test_an_owned_binary_asset_in_the_repository_is_refused():
    path = "site/src/assets/houston.webp"
    assert kimi_admission.owned_path_reason(path) is None  # on the allowlist by path
    message = _refusal(paths=(path,))
    assert message and _NOT_PLAIN_TEXT in message and "binary files are refused" in message


_CYRILLIC_LINE = "const label = 'Привіт';"
_UKRAINIAN = "the changed files hold Ukrainian content"
_NOT_TEXT = "the changed files hold content that is not plain text"


@pytest.mark.parametrize(
    ("after", "expected"),
    [
        (f"{_CYRILLIC_LINE}\n".encode(), _UKRAINIAN),
        ("const a = 'ԑ';\n".encode(), _UKRAINIAN),  # Cyrillic Supplement
        # A post-image is checked in full: Cyrillic text it kept from before is still refused.
        (f"x = 2\n{_CYRILLIC_LINE}\n".encode(), _UKRAINIAN),
        (b"const a = 'hello';\n", None),
        (b"a\tb\r\nc\n", None),  # tab, CR and LF are the only control characters admitted
        ("const a = 'café';\n".encode(), None),
        # A NUL byte makes git call the file binary; it is not plain text either way.
        (f"{_CYRILLIC_LINE}\0\n".encode(), _NOT_TEXT),
        (b"const a = 'hello';\0\n", _NOT_TEXT),
        (b"page\x0cbreak\n", _NOT_TEXT),
        # UTF-16 and UTF-32, with and without a byte-order mark, and single-byte encodings.
        (f"{_CYRILLIC_LINE}\n".encode("utf-16"), _NOT_TEXT),
        ("Урок".encode("utf-16-le"), _NOT_TEXT),
        ("Урок".encode("utf-16-be"), _NOT_TEXT),
        ("hello".encode("utf-16-le"), _NOT_TEXT),
        (f"{_CYRILLIC_LINE}\n".encode("utf-32-be"), _NOT_TEXT),
        (f"{_CYRILLIC_LINE}\n".encode("cp1251"), _NOT_TEXT),
        (b"\x89PNG\r\n\x1a\n\xff\xfe\xfd", _NOT_TEXT),
        (None, _NOT_TEXT),  # a post-image that could not be read
    ],
)
def test_changed_files_must_be_plain_utf8_text_without_cyrillic(after, expected):
    change = kimi_admission.FileChange("site/src/x.tsx", after)
    if expected is None:
        kimi_admission.refuse_kimi_changes("kimi", [change])
        return
    with pytest.raises(kimi_admission.KimiAdmissionRefused, match=expected) as refused:
        kimi_admission.refuse_kimi_changes("kimi", [change])
    if expected == _NOT_TEXT:
        assert kimi_admission.TEXT_RULE in str(refused.value)


def test_a_cyrillic_file_name_is_refused():
    change = kimi_admission.FileChange("site/src/Урок.tsx", b"export {};\n")
    assert kimi_admission.change_reasons([change]) == [f"{_UKRAINIAN} (Cyrillic text: site/src/Урок.tsx: (file name))"]


def test_a_deletion_adds_nothing():
    change = kimi_admission.FileChange("site/src/Урок.tsx", None, deleted=True)
    assert kimi_admission.change_reasons([change]) == []


def _git(repo: Path, *args: str) -> str:
    return _run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, timeout=30).stdout


@pytest.fixture
def kimi_worktree(tmp_path, monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    repo = tmp_path / "wt"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=kimi/task")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    (repo / "legacy.py").write_text("GREETING = 'Привіт'\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "base")
    _git(repo, "branch", "base")
    return repo


@pytest.mark.parametrize("committed", [False, True])
def test_finalize_refuses_a_kimi_diff_that_adds_cyrillic(kimi_worktree, committed):
    (kimi_worktree / "site").mkdir()
    (kimi_worktree / "site" / "Label.tsx").write_text("export const label = 'Урок';\n", encoding="utf-8")
    if committed:
        _git(kimi_worktree, "add", "-A")
        _git(kimi_worktree, "commit", "-m", "worker commit")
    message = delegate._kimi_diff_refusal(kimi_worktree, "base", "kimi")
    assert message and _TOKEN in message and "site/Label.tsx" in message


@pytest.mark.parametrize("committed", [False, True])
@pytest.mark.parametrize(
    "data",
    [
        "export const label = 'Урок';\0\n".encode(),  # git reports a binary diff
        "export const label = 'Урок';\n".encode("utf-16-le"),
        "export const label = 'Урок';\n".encode("utf-16-be"),
    ],
)
def test_finalize_refuses_content_that_is_not_plain_text(kimi_worktree, committed, data):
    label = kimi_worktree / "Label.tsx"
    label.write_bytes(data)
    _git(kimi_worktree, "add", "-A")
    if committed:
        _git(kimi_worktree, "commit", "-m", "worker commit")
    message = delegate._kimi_diff_refusal(kimi_worktree, "base", "kimi")
    assert message and _TOKEN in message and f"{_NOT_TEXT} ('Label.tsx')" in message


def test_finalize_refuses_an_undecodable_addition(kimi_worktree):
    (kimi_worktree / "blob.bin").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe\xfd")
    message = delegate._kimi_diff_refusal(kimi_worktree, "base", "kimi")
    assert message and _NOT_TEXT in message and "blob.bin" in message and "binary files are refused" in message


def test_finalize_admits_a_cyrillic_free_kimi_diff(kimi_worktree):
    (kimi_worktree / "Button.tsx").write_text("export const Button = () => null;\n", encoding="utf-8")
    (kimi_worktree / "legacy.py").write_text("GREETING = 'hello'\n", encoding="utf-8")  # a removal
    assert delegate._kimi_diff_refusal(kimi_worktree, "base", "kimi") is None
    assert _git(kimi_worktree, "status", "--porcelain").splitlines() == [" M legacy.py", "?? Button.tsx"]


def test_finalize_fails_closed_when_the_base_is_unknown(kimi_worktree):
    message = delegate._kimi_diff_refusal(kimi_worktree, "origin/missing", "kimi")
    assert message and "could not be read" in message


# --- the gate ------------------------------------------------------------------------


@pytest.mark.parametrize("participant", ["kimi", "kimicc"])
@pytest.mark.parametrize("owned", [_BACKEND_OWNED, _UI_OWNED])
def test_web_ui_and_backend_coding_is_admitted(participant, owned):
    assert _refusal(participants=(participant,), paths=owned) is None


@pytest.mark.parametrize("participant", ["kimi", "kimicc"])
def test_workspace_write_without_an_owned_path_is_refused(participant):
    message = _refusal(participants=(participant,), paths=())
    assert message and _TOKEN in message and "without an owned path" in message


@pytest.mark.parametrize("agent", ["claude", "codex", "grok", "agy", "cursor"])
def test_other_seats_are_untouched(agent):
    assert _refusal(participants=(agent,), mode="read-only", review=True, paths=("docs/x.md",)) is None
    assert _refusal(participants=(agent,), models=("gpt-6-sol",), mode=kimi_admission.ACP_MODE) is None


@pytest.mark.parametrize(
    ("agent", "model"),
    [
        ("kimi", None),
        ("kimicc", None),
        ("kimi-infra", None),
        ("acpx-kimi-shadow", None),
        ("codex", "kimi-code/k3"),
        ("x", "kimi-k3-max"),
        ("x", "k3"),
    ],
)
def test_every_kimi_seat_and_model_id_is_recognised(agent, model):
    assert kimi_admission.is_kimi_seat(agent, model=model)


def test_non_kimi_models_are_not_kimi_seats():
    assert not kimi_admission.is_kimi_seat("codex", model="gpt-6-sol")
    assert not kimi_admission.is_kimi_seat("cursor", model="composer-2.5")


def test_an_effective_kimi_model_on_any_seat_is_gated():
    message = _refusal(participants=("claude", "codex"), models=(None, "kimi-code/k3"), mode=kimi_admission.ACP_MODE)
    assert message and "ACP asks, consults, discussions, and reviews" in message


@pytest.mark.parametrize("mode", ["read-only", "danger"])
def test_non_workspace_write_modes_are_refused(mode):
    message = _refusal(mode=mode)
    assert message and f"--mode {mode}" in message


@pytest.mark.parametrize("mode", [kimi_admission.ACP_MODE, kimi_admission.REVIEW_MODE])
def test_acp_and_review_activities_are_refused(mode):
    assert _refusal(mode=mode, paths=())


@pytest.mark.parametrize("marker", ["review_verdict_required", "review_isolation", "review_id"])
def test_review_markers_are_refused(marker):
    assert "review dispatches" in _refusal(review=False, tool_config={marker: "x"})
    assert "review dispatches" in _refusal(review=True)


def test_language_lane_is_refused():
    message = _refusal(language_lane=True)
    assert message and "Ukrainian-language work" in message


@pytest.mark.parametrize("track", ["l2-uk-en", "l2-uk-direct", "core", "a1", "b2", "folk", "bio", "hramatka"])
def test_curriculum_research_tracks_are_refused(track):
    message = _refusal(research_track=track)
    assert message and "curriculum track" in message


def test_research_track_fails_closed_without_the_curriculum_manifest(tmp_path):
    message = _refusal(research_track="infra", repo_root=tmp_path)
    assert message and "cannot be proven non-curriculum" in message
    assert _refusal(research_track="infra") is None


@pytest.mark.parametrize(
    "prompt_file",
    ["/home/me/.claude/briefs/task.md", ".agent/handoff.md", "repo/.codex/prompt.md"],
)
def test_prompt_file_in_private_state_is_refused(prompt_file):
    message = _refusal(prompt_file=prompt_file)
    assert message and "agent-private state" in message


@pytest.mark.parametrize("role", ["private-infra", "private-product"])
def test_private_repositories_are_refused(role):
    message = _refusal(repo=role)
    assert message and f"--repo role {role!r} is a private repository" in message


def test_refusal_states_the_policy_and_names_the_alternative_seats():
    message = _refusal(mode="read-only", review=True, paths=("docs/x.md",))
    assert message.startswith(f"ROUTING REFUSED: {_TOKEN}")
    assert kimi_admission.POLICY_LINE in message
    # The Cursor seat's concrete xAI pin makes it a consult alternative (#9274).
    assert "consults and discussions → claude, codex, cursor, or grok" in message
    assert "--mode read-only" in message and "review dispatches" in message and "docs/x.md" in message


def test_kimi_refusal_distinguishes_reviewers_from_consult_and_discussion_seats():
    message = kimi_admission.format_refusal("kimi", ["review dispatches"])
    reviews, consultations = message.split("reviews → ", 1)[1].split("; consults and discussions → ", 1)
    assert "claude" in reviews and "codex" in reviews and "reviewer resolver" in reviews
    assert "grok" not in reviews and "kimi" not in reviews and "agy" not in reviews
    assert "grok" in consultations


def test_kimi_refusal_stays_typed_when_catalog_import_is_unavailable(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def without_catalog(name, *args, **kwargs):
        if name == "scripts.review.model_catalog":
            raise ModuleNotFoundError("catalog unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_catalog)
    with pytest.raises(kimi_admission.KimiAdmissionRefused) as refusal:
        kimi_admission.refuse_kimi_if_disallowed(("kimi",), mode="read-only", review=True)
    message = str(refusal.value)
    assert "reviews → claude, codex (per the reviewer resolver)" in message
    assert "consults and discussions → claude, codex, or grok" in message


# --- delegate dispatch admission --------------------------------------------------


def _dispatch(*extra: str) -> list[str]:
    return [
        "dispatch",
        "--agent",
        "kimi",
        "--task-id",
        "kimi-admission-fixture",
        "--prompt",
        "Implement the fix.",
        *extra,
    ]


_WRITE = ("--mode", "workspace-write", "--worktree")


@pytest.fixture
def no_spawn(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(delegate.subprocess, "Popen", _fail)
    monkeypatch.setattr(delegate.subprocess, "run", _fail)
    monkeypatch.setattr(delegate, "_run_dor_preflight", _fail)
    return tasks


_LANGUAGE_LANES_RULE = "LANGUAGE-LANES RULE"
_LANGUAGE_LANES_REASON = "--agent kimi cannot author, review, critique, settle, or judge Ukrainian language"


def _assert_refused(no_spawn, capsys, argv, reason, *, policy=_TOKEN):
    """Refused with exit 2 by exactly ``policy`` (the Kimi gate unless stated) for ``reason``, and nothing recorded."""
    rc = delegate.main(argv)
    err = capsys.readouterr().err
    assert rc == 2, err
    assert policy in err, err
    other = _LANGUAGE_LANES_RULE if policy == _TOKEN else _TOKEN
    assert other not in err, err
    assert reason in err, err
    assert not no_spawn.exists() or not any(no_spawn.iterdir())


@pytest.mark.parametrize(
    ("argv", "policy", "reason"),
    [
        (_dispatch(), _TOKEN, "--mode read-only"),
        (_dispatch("--mode", "danger", "--worktree"), _TOKEN, "--mode danger"),
        (_dispatch("--harness", "kimicc", "--require-review-verdict"), _TOKEN, "review dispatches"),
        (_dispatch(*_WRITE, "--review-profile", "code"), _TOKEN, "review dispatches"),
        # Ukrainian-language work reaches the language-lanes rule first, which refuses
        # every seat outside claude, codex and agy — Kimi included — just as early.
        (_dispatch(*_WRITE, "--language-lane"), _LANGUAGE_LANES_RULE, _LANGUAGE_LANES_REASON),
        (_dispatch(*_WRITE, "--research-track", "l2-uk-en"), _LANGUAGE_LANES_RULE, _LANGUAGE_LANES_REASON),
        (_dispatch(*_WRITE, "--research-track", "core"), _TOKEN, "--research-track 'core' is a curriculum track"),
        (_dispatch(*_WRITE, "--repo", "infra-private"), _TOKEN, "is a private repository"),
        (_dispatch(*_WRITE, "--repo", "hramatka"), _TOKEN, "is a private repository"),
        (_dispatch(*_WRITE), _TOKEN, "without an owned path"),
        # A research path classifies context; it never stands in for ownership.
        (_dispatch(*_WRITE, "--research-owned-path", "scripts/ci/x.py"), _TOKEN, "without an owned path"),
    ],
)
def test_dispatch_refuses_before_any_side_effect(no_spawn, capsys, argv, policy, reason):
    _assert_refused(no_spawn, capsys, argv, reason, policy=policy)


@pytest.mark.parametrize("repo", ["infra-private", "hramatka"])
def test_a_private_repo_refusal_does_not_depend_on_sibling_checkouts(no_spawn, capsys, monkeypatch, tmp_path, repo):
    """Without the sibling checkout, Kimi still gets the Kimi refusal; any other seat gets the checkout refusal."""
    primary = tmp_path / "learn-ukrainian.github.io"
    primary.mkdir()
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    monkeypatch.setattr(sys, "path", [*sys.path])  # dispatch prepends _REPO_ROOT entries
    _assert_refused(no_spawn, capsys, _dispatch(*_WRITE, "--repo", repo), "is a private repository")

    argv = ["dispatch", "--agent", "codex", "--task-id", "codex-sibling", "--prompt", "Fix it.", *_WRITE]
    rc = delegate.main([*argv, "--repo", repo])
    err = capsys.readouterr().err
    assert rc == 2, err
    assert f"--repo {repo} expects sibling checkout at {tmp_path}" in err and _TOKEN not in err, err
    assert not no_spawn.exists() or not any(no_spawn.iterdir())


def _isolate_host_state(monkeypatch) -> None:
    """Stub the dispatch probes that read this host (primary checkout, installs, runtime tmp, placement)."""
    from scripts.orchestration import job_host_exec

    for name in ("_resolve_dirty_primary_checkout_error", "_resolve_primary_integrity_error"):
        monkeypatch.setattr(delegate, name, lambda **_kwargs: None)
    for name in (
        "_warn_node_modules_integrity",
        "_warn_venv_integrity",
        "_warn_worktree_cleanup_integrity",
        "_warn_if_monitor_api_unreachable",
    ):
        monkeypatch.setattr(delegate, name, lambda: None)
    monkeypatch.setattr(
        delegate,
        "_sweep_runtime_tmp_orphans",
        lambda: {"leases_reaped": 0, "bytes_freed": 0, "errors": 0, "error_details": []},
    )
    monkeypatch.setattr(job_host_exec, "decide_dispatch_placement", lambda **_kwargs: ("local", "test", None))


def _is_language_lane_path(flag: str, path: str) -> bool:
    """Only a --research-owned-path under curriculum/ marks a dispatch as Ukrainian-language work."""
    return flag == "--research-owned-path" and path.startswith(("curriculum/", "scripts/curriculum/"))


@pytest.mark.parametrize("flag", ["--owned-path", "--research-owned-path"])
@pytest.mark.parametrize("path", REFUSED_PATHS)
def test_dispatch_refuses_every_off_allowlist_path_through_either_ownership_flag(no_spawn, capsys, flag, path):
    argv = _dispatch(*_WRITE, flag, "scripts/ci/x.py", flag, path)
    if _is_language_lane_path(flag, path):
        _assert_refused(no_spawn, capsys, argv, _LANGUAGE_LANES_REASON, policy=_LANGUAGE_LANES_RULE)
    else:
        expected = kimi_admission.owned_path_reason(path)
        assert expected
        _assert_refused(no_spawn, capsys, argv, expected)


@pytest.mark.parametrize(
    ("extra", "reason"),
    [
        (("--mode", "read-only"), "--mode read-only"),
        ((*_WRITE, "--owned-path", "site/src/components/CountSyllables.tsx"), "Ukrainian content"),
    ],
)
def test_a_budget_substitution_onto_kimi_is_refused_before_cleanup_and_archiving(
    no_spawn, capsys, monkeypatch, extra, reason
):
    """The gate runs on the effective route, after substitution and before any sweep or archive."""
    base = _head()
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: base)
    _plumbing_only(monkeypatch)
    monkeypatch.setenv("LU_DISPATCH_CHECK_BUDGET", "1")
    substituted: list[str] = []

    def substitute(agent, **_kwargs):
        substituted.append(agent)
        return "kimi"

    monkeypatch.setattr(delegate, "_resolve_agent_with_budget_guard", substitute)
    monkeypatch.setattr(delegate, "_resolve_substitution_model", lambda *_a: ("kimi-code/k3", "catalog-default"))
    for effect in ("_sweep_runtime_tmp_orphans", "_archive_task_artifacts", "_read_state", "_run_preflight_triage"):
        monkeypatch.setattr(delegate, effect, _fail)
    argv = ["dispatch", "--agent", "codex", "--task-id", "kimi-substitute", "--prompt", "Implement it.", *extra]
    _assert_refused(no_spawn, capsys, argv, reason)
    assert substituted == ["codex"]


@pytest.mark.parametrize(
    ("agent", "model"),
    [
        ("codex", "kimi-code/k3"),  # the reviewer's case: Codex→Cursor would replace the model with grok-4.7
        ("codex", "k3"),  # a catalog alias of the Kimi model
        ("gemini", "kimi-code/k3"),  # a retired CLI name, resolved to agy by the route
        ("glm", "kimi-code/k3"),  # a retired CLI name, resolved to cursor by the route
    ],
)
def test_an_explicit_kimi_model_is_refused_before_substitution_probes_records_or_worktrees(
    no_spawn, capsys, monkeypatch, agent, model
):
    """The original request is gated before the route resolves: no Monitor or model probe, task file or worktree."""
    monkeypatch.setenv("LU_DISPATCH_CHECK_BUDGET", "1")
    for effect in (
        "_fetch_routing_budget",  # the Monitor budget probe
        "_resolve_agent_with_budget_guard",
        "_resolve_substitution_model",
        "_adapter_model_rejection",  # the substitute adapter's model probe
        "_ensure_worktree",
        "_check_capacity_hint",
        "_sweep_runtime_tmp_orphans",
        "_archive_task_artifacts",
        "_run_preflight_triage",
    ):
        monkeypatch.setattr(delegate, effect, _fail)
    argv = ["dispatch", "--agent", agent, "--model", model, "--mode", "read-only", "--task-id", "kimi-model-sub"]
    _assert_refused(no_spawn, capsys, [*argv, "--prompt", "Look at it."], "--mode read-only")
    assert not (_REPO_ROOT / ".worktrees" / "dispatch" / "cursor" / "kimi-model-sub").exists()


def test_an_admitted_route_substitutes_after_the_original_request_is_gated(no_spawn, monkeypatch):
    """A non-Kimi request still takes its budget substitute, and the worker launches the substituted route."""
    monkeypatch.setenv("LU_DISPATCH_CHECK_BUDGET", "1")
    seen: dict[str, object] = {}

    def substitute(agent, **kwargs):
        seen.update(agent=agent, fallbacks=kwargs["fallbacks"])
        return "cursor"

    monkeypatch.setattr(delegate, "_resolve_agent_with_budget_guard", substitute)
    monkeypatch.setattr(delegate, "_resolve_substitution_model", lambda *_a: ("grok-4.7", "catalog-default"))

    class Gated(Exception):
        pass

    gate = delegate._kimi_dispatch_gate

    def stop_after_the_gate(*args, **kwargs):
        raise Gated(gate(*args, **kwargs))

    monkeypatch.setattr(delegate, "_kimi_dispatch_gate", stop_after_the_gate)
    argv = ["dispatch", "--agent", "codex", "--model", "gpt-6.1-sol", "--mode", "read-only", "--task-id", "sub"]
    with pytest.raises(Gated) as gated:
        delegate.main([*argv, "--prompt", "Look at it."])
    refusal, _start, target = gated.value.args[0]
    assert refusal is None
    assert delegate._worker_route_argv(target) == ["--agent", "cursor", "--model", "grok-4.7"]
    assert seen["agent"] == "codex" and seen["fallbacks"].get("codex") == "cursor"


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture
def clean_git_env(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)


def test_dispatch_reads_owned_paths_at_the_new_worktree_base_commit(
    no_spawn, capsys, monkeypatch, tmp_path, clean_git_env
):
    """The base commit holds Cyrillic text the dispatcher's checkout lacks: refused with no log and no worktree."""
    path = "site/src/components/LiveStatus.tsx"
    primary = tmp_path / "primary"
    (primary / path).parent.mkdir(parents=True)
    _git(primary, "init", "-q", "--initial-branch=main")
    (primary / path).write_text("export const label = 'Урок';\n", encoding="utf-8")
    base = _commit_all(primary, "base with Ukrainian content")
    _git(primary, "update-ref", "refs/remotes/origin/main", base)
    (primary / path).write_text("export const label = 'Lesson';\n", encoding="utf-8")
    _commit_all(primary, "the dispatcher checkout is clean")
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    monkeypatch.setattr(delegate, "_fetch_base", _fail)
    monkeypatch.setattr(delegate, "_fetch_existing_branch", _fail)
    ran = _plumbing_only(monkeypatch)  # any fetch or other git write raises

    reason = f"Cyrillic text in {path!r}, in commit {base[:12]}"
    _assert_refused(no_spawn, capsys, _dispatch(*_WRITE, "--owned-path", path), reason)
    assert set(ran) <= _GATE_GIT and "ls-tree" in ran
    assert not (primary / ".worktrees").exists()
    assert _git(primary, "worktree", "list").count("\n") == 1


@pytest.mark.parametrize("extra", [(), ("--branch", "kimi/task")], ids=["base", "branch"])
def test_dispatch_refuses_a_base_missing_locally_without_fetching(
    no_spawn, capsys, monkeypatch, tmp_path, clean_git_env, extra
):
    """No remote-tracking commit locally: refused with the refresh reason, never fetched."""
    path = "site/src/components/LiveStatus.tsx"
    primary = tmp_path / "primary"
    (primary / path).parent.mkdir(parents=True)
    _git(primary, "init", "-q", "--initial-branch=main")
    (primary / path).write_text("export const label = 'Lesson';\n", encoding="utf-8")
    _commit_all(primary, "no origin ref exists")
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    monkeypatch.setattr(delegate, "_fetch_base", _fail)
    monkeypatch.setattr(delegate, "_fetch_existing_branch", _fail)
    ran = _plumbing_only(monkeypatch)

    _assert_refused(no_spawn, capsys, _dispatch(*_WRITE, "--owned-path", path, *extra), "base not available locally")
    assert set(ran) <= {"rev-parse"}
    assert not (primary / ".worktrees").exists()


def test_dispatch_reads_owned_paths_in_the_reused_worktree(no_spawn, capsys, monkeypatch, tmp_path, clean_git_env):
    """A reused worktree is read on disk and at its commit, whatever the dispatcher's checkout holds."""
    path = "site/src/components/LiveStatus.tsx"
    assert not kimi_admission.CYRILLIC.search((_REPO_ROOT / path).read_text(encoding="utf-8"))
    reused = tmp_path / "reused"
    (reused / path).parent.mkdir(parents=True)
    _git(reused, "init", "-q", "--initial-branch=kimi/task")
    (reused / path).write_text("export const label = 'Урок';\n", encoding="utf-8")
    commit = _commit_all(reused, "committed Ukrainian content")
    (reused / path).write_text("export const label = 'Lesson';\n", encoding="utf-8")  # clean on disk only
    (reused / "site/src/components/Draft.tsx").write_text("export const d = 'Чернетка';\n", encoding="utf-8")
    monkeypatch.setattr(delegate, "_auto_worktree_path", lambda *_a, **_k: reused)
    _plumbing_only(monkeypatch)
    argv = _dispatch(*_WRITE, "--owned-path", "site/src/components/")
    rc = delegate.main(argv)
    err = capsys.readouterr().err
    assert rc == 2 and _TOKEN in err, err
    assert f"Cyrillic text in {path!r}, in commit {commit[:12]}" in err
    assert f"Cyrillic text in 'site/src/components/Draft.tsx', in {reused}" in err
    assert not no_spawn.exists() or not any(no_spawn.iterdir())


def test_dispatch_refuses_a_worktree_base_that_moved_after_the_gate(tmp_path, monkeypatch, capsys):
    """The base resolved under the worktree lock must be the commit the gate read."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(delegate, "_run_dor_preflight", lambda *_a, **_k: (None, None))
    monkeypatch.setattr(delegate, "_check_capacity_hint", lambda *_a, **_k: None)
    monkeypatch.setattr(delegate, "_report_dispatch_admission", lambda *_a, **_k: None)
    _isolate_host_state(monkeypatch)
    gate_base = _head()
    calls: list[bool] = []

    def resolve(**kwargs):
        calls.append(kwargs["allow_rebase"])
        return "0" * 40  # the fetch at creation moved the base

    monkeypatch.setattr(delegate, "_resolve_local_base_sha", lambda **_kwargs: gate_base)
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", resolve)
    argv = _dispatch(*_WRITE, "--dry-run", "--owned-path", "scripts/agent_runtime/runner.py")
    rc = delegate.main(argv)
    err = capsys.readouterr().err
    assert rc == 2, err
    assert _TOKEN in err and f"is not the commit {gate_base} its owned paths were read at" in err
    assert calls == [False]  # a Kimi worktree is never rebased


def test_dispatch_refuses_a_kimi_model_on_another_seat(no_spawn, capsys):
    argv = ["dispatch", "--agent", "codex", "--model", "kimi-code/k3", "--task-id", "t", "--prompt", "Review it."]
    _assert_refused(no_spawn, capsys, argv, "--mode read-only")


def test_dispatch_refuses_a_private_state_prompt_file(no_spawn, capsys, tmp_path):
    prompt = tmp_path / ".claude" / "brief.md"
    prompt.parent.mkdir()
    prompt.write_text("Implement the fix.\n", encoding="utf-8")
    argv = ["dispatch", "--agent", "kimi", "--task-id", "kimi-admission-fixture", "--prompt-file", str(prompt)]
    rc = delegate.main([*argv, *_WRITE])
    err = capsys.readouterr().err
    assert rc == 2
    assert "agent-private state" in err


class _AdmittedSentinel(Exception):
    pass


@pytest.mark.parametrize(
    "owned",
    [
        pytest.param(_BACKEND_OWNED, id="backend"),
        pytest.param(_UI_OWNED, id="ui"),
    ],
)
def test_web_ui_and_backend_dispatches_pass_admission(tmp_path, monkeypatch, owned):
    """The allowed classes clear both admission checks and reach the capacity hint."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(delegate, "_run_dor_preflight", lambda *_a, **_k: (None, None))
    _isolate_host_state(monkeypatch)
    # The gate reads the owned paths in HEAD's committed tree, the base the worktree is created from.
    base = _head()
    monkeypatch.setattr(delegate, "_resolve_local_base_sha", lambda **_kwargs: base)
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: base)
    seen: list[str] = []

    def reached(agent, **_kwargs):
        seen.append(agent)
        raise _AdmittedSentinel

    monkeypatch.setattr(delegate, "_check_capacity_hint", reached)
    ownership: list[str] = []
    for path in owned:
        ownership += ["--owned-path", path, "--research-owned-path", path]
    argv = _dispatch(*_WRITE, "--research-role", "harness", *ownership)
    with pytest.raises(_AdmittedSentinel):
        delegate.main(argv)
    assert seen == ["kimi"]


# --- delegate worker ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "review"),
    [("read-only", {"require_review_verdict": True}), ("danger", {}), ("workspace-write", {"review_id": "rev-1"})],
)
def test_worker_refuses_with_zero_side_effects(tmp_path, monkeypatch, capsys, mode, review):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    # Reading the task record is not an effect; a write is.
    monkeypatch.setattr(delegate, "_write_state_atomic", _fail)
    monkeypatch.setattr(delegate.signal, "signal", _fail)
    monkeypatch.setattr("agent_runtime.runner.invoke", _fail)

    rc = delegate._run_worker(
        task_id=f"kimi-worker-{mode}",
        agent="kimi",
        prompt="Review the diff.",
        mode=mode,
        cwd_str=str(tmp_path),
        model=None,
        hard_timeout=60,
        harness="kimicc",
        **review,
    )

    assert rc == 1
    assert _TOKEN in capsys.readouterr().err
    assert not tasks.exists()


def test_worker_reads_owned_paths_in_the_tree_it_runs_in(tmp_path, monkeypatch, capsys):
    """The worker scans its own worktree before any state write, boundary or invocation."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    for key in tuple(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    path = "site/src/components/LiveStatus.tsx"
    worktree = tmp_path / "wt"
    (worktree / path).parent.mkdir(parents=True)
    _git(worktree, "init", "-q", "--initial-branch=kimi/task")
    (worktree / path).write_text("export const label = 'Lesson';\n", encoding="utf-8")
    _commit_all(worktree, "clean base")
    (worktree / path).write_text("export const label = 'Урок';\n", encoding="utf-8")
    state_path = delegate._state_path("kimi-reused")
    delegate._write_state_atomic(
        state_path,
        {"task_id": "kimi-reused", "worktree_path": str(worktree), "worktree_base": "main", "owned_paths": [path]},
    )
    before = state_path.read_bytes()
    monkeypatch.setattr(delegate.signal, "signal", _fail)
    monkeypatch.setattr(delegate, "_write_state_atomic", _fail)
    monkeypatch.setattr("agent_runtime.runner.invoke", _fail)
    monkeypatch.setattr("scripts.agent_runtime.kimi_boundary.install", _fail)

    rc = delegate._run_worker(
        task_id="kimi-reused",
        agent="kimi",
        prompt="Implement it.",
        mode="workspace-write",
        cwd_str=str(worktree),
        model=None,
        hard_timeout=60,
    )

    assert rc == 1
    err = capsys.readouterr().err
    assert _TOKEN in err and f"Cyrillic text in {path!r}" in err
    assert state_path.read_bytes() == before


# --- runtime boundary ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "tool_config"),
    [
        ("read-only", None),
        ("danger", None),
        ("read-only", {"harness": "kimicc", "trail_isolation": True}),
        ("workspace-write", {"review_id": "rev-1"}),
    ],
)
def test_runner_invoke_refuses_before_attribution_or_trail_provisioning(tmp_path, monkeypatch, mode, tool_config):
    from scripts.agent_runtime import runner

    monkeypatch.setattr(runner, "resolve_invocation_attribution", _fail)
    monkeypatch.setattr(runner, "prepare_trail_isolation", _fail)
    monkeypatch.setattr(runner, "_invoke_impl", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        runner.invoke("kimi", "Review this.", mode=mode, cwd=tmp_path, tool_config=tool_config)


def test_inter_agent_route_refuses_a_kimi_model_override():
    from scripts.agent_runtime import runner

    for participant, model in (("kimi", None), ("kimicc", None), ("claude", "kimi-code/k3")):
        with pytest.raises(runner.InterAgentTransportError, match=_TOKEN):
            runner.resolve_inter_agent_route(participant, model=model)


def test_no_non_kimi_acp_participant_pins_a_kimi_model():
    from scripts.agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    for name, route in ACPX_SUPPORTED_PARTICIPANTS.items():
        if kimi_admission.is_kimi_model(route.get("model")):
            assert kimi_admission.is_kimi_seat(name), name


@pytest.mark.parametrize("harness", [None, "kimicc"])
@pytest.mark.parametrize("mode", ["read-only", "danger"])
def test_kimi_adapters_refuse_read_only_and_danger_before_planning(tmp_path, monkeypatch, harness, mode):
    from scripts.agent_runtime.adapters import kimi as kimi_adapter
    from scripts.agent_runtime.adapters import kimicc as kimicc_adapter

    monkeypatch.setattr(kimi_adapter, "_resolve_kimi_binary", _fail)
    monkeypatch.setattr(kimicc_adapter, "_default_claude_bin", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        kimi_adapter.KimiAdapter().build_invocation(
            prompt="p",
            mode=mode,
            cwd=tmp_path,
            model=None,
            task_id="t",
            session_id=None,
            tool_config={"harness": harness} if harness else None,
        )
    with pytest.raises(ValueError, match=_TOKEN):
        kimicc_adapter.KimiccHarness().build_invocation(
            prompt="p", mode=mode, cwd=tmp_path, model=None, task_id="t", session_id=None, tool_config=None
        )


# --- unscoped workspace-write through the runtime and the native adapters ------------

_UKRAINIAN_FEEDBACK = "Give the learners Ukrainian feedback in the syllable counter."
_UKRAINIAN_COMPONENT = "site/src/components/CountSyllables.tsx"
_ADMITTED_COMPONENT = "site/src/components/LiveStatus.tsx"


def _owned_config(*paths: str, harness: str | None = None) -> dict:
    config: dict = {kimi_admission.OWNED_PATHS_KEY: list(paths)}
    if harness:
        config["harness"] = harness
    return config


@pytest.fixture
def launch_probe(monkeypatch):
    """Record every launch plan the runtime builds; nothing is spawned."""
    from scripts.agent_runtime import runner
    from scripts.agent_runtime.adapters import kimi as kimi_adapter

    class _Reached(Exception):
        pass

    planned: list[str] = []

    def impl(agent_name, *_args, **_kwargs):
        planned.append(agent_name)
        raise _Reached

    monkeypatch.setattr(runner, "_invoke_impl", impl)
    monkeypatch.setattr(kimi_adapter, "_resolve_kimi_binary", lambda: "/bin/true")
    return planned, _Reached


@pytest.mark.parametrize("owned", [(), (_UKRAINIAN_COMPONENT,)])
def test_the_runtime_refuses_kimi_workspace_write_without_admitted_ownership(launch_probe, owned):
    from scripts.agent_runtime import runner

    planned, _ = launch_probe
    with pytest.raises(kimi_admission.KimiAdmissionRefused, match=_TOKEN) as refused:
        runner.invoke(
            "kimi", _UKRAINIAN_FEEDBACK, mode="workspace-write", cwd=_REPO_ROOT, tool_config=_owned_config(*owned)
        )
    assert ("Ukrainian content" if owned else "without an owned path") in str(refused.value)
    assert planned == []


def test_the_runtime_admits_kimi_workspace_write_that_owns_a_cyrillic_free_file(launch_probe):
    from scripts.agent_runtime import runner

    planned, reached = launch_probe
    with pytest.raises(reached):
        runner.invoke(
            "kimi",
            "Add a tooltip.",
            mode="workspace-write",
            cwd=_REPO_ROOT,
            tool_config=_owned_config(_ADMITTED_COMPONENT),
        )
    assert planned == ["kimi"]


@pytest.mark.parametrize("harness", [None, "kimicc"])
@pytest.mark.parametrize("owned", [(), (_UKRAINIAN_COMPONENT,)])
def test_the_native_adapters_refuse_unscoped_or_cyrillic_workspace_write_before_a_launch_plan(
    tmp_path, monkeypatch, harness, owned
):
    from scripts.agent_runtime.adapters import kimi as kimi_adapter
    from scripts.agent_runtime.adapters import kimicc as kimicc_adapter

    monkeypatch.setattr(kimi_adapter, "_resolve_kimi_binary", _fail)
    monkeypatch.setattr(kimicc_adapter, "_default_claude_bin", _fail)
    config = _owned_config(*owned, harness=harness)
    for adapter in (kimi_adapter.KimiAdapter(), kimicc_adapter.KimiccHarness()):
        with pytest.raises(ValueError, match=_TOKEN) as refused:
            adapter.build_invocation(
                prompt=_UKRAINIAN_FEEDBACK,
                mode="workspace-write",
                cwd=_REPO_ROOT,
                model=None,
                task_id="t",
                session_id=None,
                tool_config=config,
            )
        assert ("Ukrainian content" if owned else "without an owned path") in str(refused.value)


def test_the_native_adapter_plans_workspace_write_that_owns_a_cyrillic_free_file(monkeypatch):
    from scripts.agent_runtime.adapters import kimi as kimi_adapter

    monkeypatch.setattr(kimi_adapter, "_resolve_kimi_binary", lambda: "/bin/true")
    plan = kimi_adapter.KimiAdapter().build_invocation(
        prompt="Add a tooltip.",
        mode="workspace-write",
        cwd=_REPO_ROOT,
        model=None,
        task_id="t",
        session_id=None,
        tool_config=_owned_config(_ADMITTED_COMPONENT),
    )
    assert plan.cmd[0] == "/bin/true"


def test_a_kimi_launch_without_credential_isolation_is_refused_before_any_spawn(tmp_path, monkeypatch):
    from scripts.agent_runtime import runner
    from scripts.agent_runtime.adapters import kimi as kimi_adapter

    def no_tempdir(*_args, **_kwargs):
        raise OSError("no temporary directory")

    config = admitted_tool_config(tmp_path)
    monkeypatch.setattr(kimi_adapter, "_resolve_kimi_binary", lambda: "/bin/true")
    monkeypatch.setattr("tempfile.mkdtemp", no_tempdir)

    def git_only(cmd, *args, **kwargs):
        # The gate reads the execution tree with git plumbing; nothing else may spawn.
        if list(cmd[:1]) != ["git"]:
            _fail()
        return _REAL_POPEN(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", git_only)
    with pytest.raises(ValueError, match=_TOKEN) as refused:
        runner.invoke(
            "kimi",
            "Implement it.",
            mode="workspace-write",
            cwd=tmp_path,
            task_id="kimi-isolation",
            tool_config=config,
        )
    assert "credential isolation could not be established" in str(refused.value)


def test_trail_isolation_refuses_kimi():
    from scripts.agent_runtime.trail_isolation import TrailIsolationError, prepare_trail_isolation

    with pytest.raises(TrailIsolationError, match=_TOKEN):
        prepare_trail_isolation(
            agent_name="kimi", mode="read-only", tool_config={"trail_isolation": True, "harness": "kimicc"}
        )


# --- the worktree boundary: hooks, push block, no push credential ------------------------


def _bounded_repo(tmp_path: Path, monkeypatch, repo_hooks: dict[str, str] | None = None) -> types.SimpleNamespace:
    """A clone on a task branch with the Kimi boundary installed; ``origin`` is a bare repository.

    ``repo_hooks`` are the repository's own hooks, installed before the boundary.
    """
    from scripts.agent_runtime import kimi_boundary

    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)  # the host push guard refuses pushes to main
    origin = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    _git(tmp_path, "init", "--bare", "--initial-branch=main", str(origin))
    _git(tmp_path, "init", "--initial-branch=main", str(repo))
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "base")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "checkout", "-b", "kimi/task")
    for name, body in (repo_hooks or {}).items():
        hook = repo / ".git" / "hooks" / name
        hook.write_text(body, encoding="utf-8")
        hook.chmod(0o755)
    kimi_boundary.install(repo, agent="kimi", base_ref="origin/main", owned_paths=["site/src/components/"])
    return types.SimpleNamespace(repo=repo, origin=origin)


@pytest.fixture
def bounded_repo(tmp_path, monkeypatch):
    return _bounded_repo(tmp_path, monkeypatch)


def _git_proc(repo: Path, *args: str, env=None, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False, timeout=60, env=env, input=stdin
    )


def _write_label(repo: Path, data: bytes) -> None:
    label = repo / "site" / "src" / "components" / "Label.tsx"
    label.parent.mkdir(parents=True, exist_ok=True)
    label.write_bytes(data)


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        ("export const label = 'Урок';\n".encode(), _UKRAINIAN),
        ("export const label = 'Урок';\0\n".encode(), _NOT_TEXT),  # git calls this binary
        ("export const label = 'Урок';\n".encode("utf-16"), _NOT_TEXT),
        ("export const label = 'Урок';\n".encode("utf-16-le"), _NOT_TEXT),
    ],
)
def test_the_pre_commit_hook_refuses_a_worker_commit_that_is_not_cyrillic_free_text(bounded_repo, data, reason):
    repo = bounded_repo.repo
    head = _git(repo, "rev-parse", "HEAD")
    _write_label(repo, data)
    _git(repo, "add", "-A")
    proc = _git_proc(repo, "commit", "-m", "worker commit")
    assert proc.returncode != 0
    assert "commit refused by the Kimi worktree boundary" in proc.stderr and reason in proc.stderr
    assert _git(repo, "rev-parse", "HEAD") == head


def test_the_pre_commit_hook_refuses_a_commit_outside_the_owned_paths(bounded_repo):
    repo = bounded_repo.repo
    (repo / "README.md").write_text("changed\n", encoding="utf-8")
    proc = _git_proc(repo, "commit", "-am", "worker commit")
    assert proc.returncode != 0
    assert "changed paths outside the owned paths ('README.md')" in proc.stderr


def test_the_pre_commit_hook_admits_a_clean_owned_commit_and_keeps_the_repository_hooks(tmp_path, monkeypatch):
    """The repository's own hooks still run: its pre-commit after the Kimi check, and every other hook."""
    ran = tmp_path / "ran"
    hooks = {name: f"#!/bin/sh\necho {name} >> '{ran}'\n" for name in ("pre-commit", "commit-msg")}
    repo = _bounded_repo(tmp_path, monkeypatch, repo_hooks=hooks).repo
    _write_label(repo, b"export const label = 'Lesson';\n")
    _git(repo, "add", "-A")
    proc = _git_proc(repo, "commit", "-m", "worker commit")
    assert proc.returncode == 0, proc.stderr
    assert ran.read_text(encoding="utf-8").split() == ["pre-commit", "commit-msg"]


def test_a_worker_push_fails_and_the_pre_push_hook_refuses_cyrillic(bounded_repo):
    from scripts.agent_runtime import kimi_boundary

    repo = bounded_repo.repo
    _write_label(repo, "export const label = 'Урок';\n".encode())
    _git(repo, "add", "-A")
    _git(repo, "commit", "--no-verify", "-m", "a commit that bypassed the pre-commit hook")
    # The worktree's push URL is unusable.
    proc = _git_proc(repo, "push", "origin", "HEAD")
    assert proc.returncode != 0 and "kimi-push-disabled" in proc.stderr
    # With the push URL restored by hand, the pre-push hook still refuses the commit.
    _git(repo, "config", "--worktree", "--unset-all", "remote.origin.pushurl")
    proc = _git_proc(repo, "push", "origin", "HEAD")
    assert proc.returncode != 0 and "push refused by the Kimi worktree boundary" in proc.stderr
    assert _git(bounded_repo.origin, "branch", "--list", "kimi/task") == ""
    assert kimi_boundary.hook_reasons(repo, "pre-push", f"HEAD {_git(repo, 'rev-parse', 'HEAD').strip()} x y\n")


def test_the_kimi_worker_environment_carries_no_push_credential(bounded_repo, monkeypatch):
    from scripts.agent_runtime import kimi_boundary
    from scripts.agent_runtime.env_sanitize import build_agent_env

    for name in ("GH_TOKEN", "GITHUB_TOKEN", "LU_AGENT_GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN"):
        monkeypatch.setenv(name, "ghp_" + "x" * 36)
    monkeypatch.setenv("GIT_ASKPASS", "/usr/bin/askpass")
    env = build_agent_env(provider="kimi")
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "LU_AGENT_GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GIT_ASKPASS"):
        assert name not in env, name
    config = {env[f"GIT_CONFIG_KEY_{i}"]: env[f"GIT_CONFIG_VALUE_{i}"] for i in range(int(env["GIT_CONFIG_COUNT"]))}
    assert config["credential.helper"] == ""
    assert f"url.{kimi_boundary.PUSH_BLOCK_URL}/.pushInsteadOf" in config
    assert list(Path(env["GH_CONFIG_DIR"]).iterdir()) == []

    # Even with the worktree push block lifted, a clean push from the worker environment fails.
    repo = bounded_repo.repo
    kimi_boundary.remove(repo)
    _write_label(repo, b"export const label = 'Lesson';\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "clean worker commit")
    proc = _git_proc(repo, "push", "origin", "HEAD", env=env)
    assert proc.returncode != 0 and "kimi-push-disabled" in proc.stderr
    assert _git(bounded_repo.origin, "branch", "--list", "kimi/task") == ""


def test_remove_takes_the_boundary_down(bounded_repo):
    from scripts.agent_runtime import kimi_boundary

    repo = bounded_repo.repo
    assert kimi_boundary.is_installed(repo)
    kimi_boundary.remove(repo)
    assert not kimi_boundary.is_installed(repo)
    assert _git_proc(repo, "config", "--worktree", "--get", "core.hooksPath").returncode == 1
    assert _git_proc(repo, "config", "--get-regexp", "^kimiguard\\.").stdout == ""
    _write_label(repo, b"export const label = 'Lesson';\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "delegate commit")
    assert _git_proc(repo, "push", "origin", "HEAD").returncode == 0


# --- ACP, bridge and fleet-comms entry points ------------------------------------------


def test_compat_ask_refuses_before_telemetry(monkeypatch):
    from scripts.ai_agent_bridge import _acp_compat
    from scripts.telemetry import legacy_bridge

    monkeypatch.setattr(legacy_bridge, "start_bridge_invocation_safely", _fail)
    monkeypatch.setattr(_acp_compat, "_run_compat_ask_impl", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat.run_compat_ask("kimi", "Consult on this design.", task_id="kimi-consult")
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat.run_compat_ask("claude", "Consult.", task_id="kimi-model", model="kimi-code/k3")


def test_compat_ask_impl_refuses_before_the_job_host_forward(monkeypatch):
    from scripts.ai_agent_bridge import _acp_compat, _job_host_forward

    monkeypatch.setattr(_job_host_forward, "maybe_forward_compat_ask", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat._run_compat_ask_impl("kimi", "Consult.", task_id="kimi-forward")


def test_a_kimi_quota_substitute_is_refused_before_its_job_is_enqueued(monkeypatch, tmp_path):
    from scripts.ai_agent_bridge import _acp_compat
    from scripts.fleet_comms import authority

    config = tmp_path / "agent_fallback_substitutions.yaml"
    config.write_text("dispatch_fallbacks:\n  codex: kimi\n", encoding="utf-8")
    monkeypatch.setattr(_acp_compat, "_FALLBACK_SUBS_PATH", config)
    monkeypatch.setattr(authority, "AuthorityService", _fail)
    # The substitute is resolved and admitted in one step: a Kimi substitute never becomes a target.
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat._resolve_quota_substitution("codex", "rate_limited", already_substituted=False)
    # The job sink takes only an admitted target; a raw seat name is refused before the authority.
    with pytest.raises(TypeError, match="AdmittedTarget"):
        _acp_compat._run_single_acp_job("kimi", "Consult.", task_id="t", source=None, effort=None, review=False, hard_timeout=60)


@pytest.mark.parametrize("extra", [[], ["--pr", "9158"], ["--review"]])
def test_ask_kimi_cli_refuses_before_pr_resolution_or_dispatch(monkeypatch, extra):
    from scripts.ai_agent_bridge import _acp_compat, _cli, _dispatch_wrappers

    monkeypatch.setattr(_cli, "_resolve_same_repo_pr_head", _fail)
    monkeypatch.setattr(_acp_compat, "run_compat_ask", _fail)
    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", _fail)
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(read=_fail))
    args = _cli._build_parser().parse_args(["ask-kimi", "-", "--task-id", "kimi-cli", *extra])
    with pytest.raises(SystemExit, match=_TOKEN):
        _cli._handle_ask_kimi(args)


def test_ask_review_dispatch_refuses_before_the_temporary_prompt(monkeypatch):
    from scripts.ai_agent_bridge import _dispatch_wrappers

    monkeypatch.setattr(_dispatch_wrappers, "_prompt_directory", _fail)
    monkeypatch.setattr(_dispatch_wrappers.subprocess, "run", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _dispatch_wrappers.run_ask_review_dispatch("kimi", "Review PR #1.", task_id="kimi-review")
    with pytest.raises(ValueError, match=_TOKEN):
        _dispatch_wrappers.run_ask_review_dispatch("claude", "Review PR #1.", task_id="r", model="kimi-code/k3")


def test_ask_review_dispatch_command_never_selects_a_kimi_harness(tmp_path):
    from scripts.agent_runtime.kimi_admission import REVIEW_MODE
    from scripts.agent_runtime.target_admission import resolve_and_admit
    from scripts.ai_agent_bridge import _dispatch_wrappers

    (target,) = resolve_and_admit(("claude",), mode=REVIEW_MODE, review=True)
    cmd = _dispatch_wrappers.build_ask_review_dispatch_command(target, "t", tmp_path / "p.md", effort=None)
    assert "--harness" not in cmd


def test_authority_enqueue_request_refuses_before_any_write():
    from scripts.fleet_comms.authority import AuthorityService

    service = AuthorityService.__new__(AuthorityService)  # no connection: any write would raise AttributeError
    with pytest.raises(ValueError, match=_TOKEN):
        service.enqueue_request(recipient="kimi", body="Consult on this design.")
    with pytest.raises(ValueError, match=_TOKEN):
        service.enqueue_request(recipient="claude", body="Consult.", metadata={"requested_model": "kimi-code/k3"})


def test_authority_enqueue_discussion_refuses_before_any_write():
    from scripts.fleet_comms.authority import AuthorityService

    service = AuthorityService.__new__(AuthorityService)
    with pytest.raises(ValueError, match=_TOKEN):
        service.enqueue_discussion(
            channel="architecture",
            prompt="Compare the options.",
            participants=("claude", "kimicc"),
            rounds=1,
            task_digest="digest",
            correlation_id="corr",
            deadline_at="2026-09-30T00:00:00+00:00",
        )


def test_fleet_request_to_kimi_is_refused_before_any_insert():
    executor = RequestExecutor.__new__(RequestExecutor)
    executor.registry = load_endpoint_registry()
    with pytest.raises(ValueError, match=_TOKEN):
        executor.create_request(recipient="kimi", body="Consult on this design.")


@pytest.mark.parametrize(
    ("participants", "models"),
    [
        (("claude", "kimi"), None),
        (("claude", "codex"), {"claude": "kimi-code/k3"}),
        (("codex", "kimicc"), None),
    ],
)
def test_acp_discussion_refuses_on_effective_seats_and_models_before_the_plane(
    tmp_path, monkeypatch, participants, models
):
    from scripts.agent_runtime import acpx_discuss

    monkeypatch.setattr(acpx_discuss, "AcpxDiscussionController", _fail)
    monkeypatch.setattr(acpx_discuss, "ArtifactStore", _fail)
    monkeypatch.setattr(acpx_discuss, "default_plane_root", _fail)
    with pytest.raises(acpx_discuss.AcpxDiscussionError, match=_TOKEN):
        acpx_discuss.run_discussion(
            prompt="Compare the options.",
            cwd=tmp_path,
            task_id="t",
            correlation_id="c",
            idempotency_key="i",
            rounds=1,
            participants=participants,
            models=models,
        )


@pytest.mark.parametrize(("with_agents", "models"), [("claude,kimicc", None), ("claude,codex", "claude:kimi-code/k3")])
def test_ab_discuss_refuses_on_effective_models_before_any_channel_write(monkeypatch, capsys, with_agents, models):
    from scripts.ai_agent_bridge import _channels_cli
    from scripts.fleet_comms import authority

    monkeypatch.delenv("LU_AGENT_COMM_TRANSPORT", raising=False)
    monkeypatch.setattr(authority, "AuthorityService", _fail)
    args = types.SimpleNamespace(
        channel="architecture", body="Compare.", with_agents=with_agents, max_rounds=1, review=False, models=models
    )
    assert _channels_cli._handle_discuss(args) == 2
    assert _TOKEN in capsys.readouterr().err


def test_ab_inbox_run_for_kimi_is_refused_before_housekeeping(monkeypatch, capsys):
    from scripts.ai_agent_bridge import _channels, _channels_cli

    monkeypatch.setattr(_channels, "expire_stale_deliveries", _fail)
    args = types.SimpleNamespace(agent="kimi", once=True, until_idle=False, max_messages=None)
    assert _channels_cli._handle_inbox_run(args) == 2
    assert _TOKEN in capsys.readouterr().err


def test_inbox_worker_refuses_kimi_before_any_claim(monkeypatch):
    from scripts.ai_agent_bridge import _channels, _inbox

    monkeypatch.setattr(_inbox, "_claim_next_thread", _fail)
    monkeypatch.setattr(_channels, "expire_stale_deliveries", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _inbox.run_inbox("kimi")


# --- broker drain paths: a Kimi-addressed row is never processed ------------------------


@pytest.fixture
def broker_db(tmp_path, monkeypatch):
    """A migrated broker DB with a Kimi-addressed message (7), a Kimi-model ask (8) and an acknowledged one (9).

    Every reply, acknowledgement, failure record and ACP call raises;
    ``unchanged()`` compares the whole database with its seeded dump, and
    ``connects`` records every SQLite connection opened after seeding.
    """
    from scripts.ai_agent_bridge import _ask_lifecycle, _db, _messaging, _process

    monkeypatch.setattr(_db, "DB_PATH", tmp_path / "messages.db")
    seed = _db.get_db()
    seed.executemany(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, message_type, content, data, timestamp, acknowledged)"
        " VALUES (?, 't', 'codex', ?, 'query', 'q', ?, '2026-09-30T00:00:00+00:00', ?)",
        [(7, "kimi", None, 0), (8, "claude", json.dumps({"to_model": "kimi-code/k3"}), 0), (9, "claude", None, 1)],
    )
    seed.commit()
    before = list(seed.iterdump())
    seed.close()
    real_connect = sqlite3.connect
    connects: list[str] = []

    def connect(database, *args, **kwargs):
        connects.append(str(database))
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)
    for module, names in (
        (_process, ("send_message", "acknowledge", "record_ask_failure", "record_ask_reply", "run_compat_ask")),
        (_process, ("_notify_processing_failure", "_message_acknowledged")),
        (_ask_lifecycle, ("mark_ask_processing", "record_ask_failure", "_AskTerminalRecorder")),
        (_messaging, ("send_message", "acknowledge")),
    ):
        for name in names:
            monkeypatch.setattr(module, name, _fail)

    def unchanged() -> bool:
        check = real_connect(_db.DB_PATH)
        try:
            return list(check.iterdump()) == before
        finally:
            check.close()

    return types.SimpleNamespace(connects=connects, unchanged=unchanged)


_SKIPPED = "skipped: Kimi is not a bridge recipient"


@pytest.mark.parametrize("message_id", [7, 8])
def test_a_kimi_addressed_message_is_never_processed(broker_db, capsys, message_id):
    from scripts.ai_agent_bridge import _process

    assert _process.process_message_for_recipient(message_id) is None
    assert capsys.readouterr().out.count(_SKIPPED) == 1
    assert broker_db.unchanged()
    assert not _process.recipient_has_acp_route("kimi")


def test_process_refuses_a_kimi_model_before_the_broker_is_opened(broker_db):
    from scripts.ai_agent_bridge import _process

    with pytest.raises(ValueError, match=_TOKEN):
        _process.process_message_for_recipient(9, model="kimi-code/k3")
    assert broker_db.connects == []


@pytest.mark.parametrize("argv", [["process", "9", "--model", "kimi-code/k3"], ["process-kimi", "7"]])
def test_process_cli_refuses_a_kimi_request_unopened(broker_db, argv):
    """A Kimi seat or model named on the command line is a Kimi request: refused before the broker is opened."""
    from scripts.ai_agent_bridge import _cli

    with pytest.raises(SystemExit, match=_TOKEN):
        _cli._dispatch_command(_cli._build_parser().parse_args(argv))
    assert broker_db.connects == []
    assert broker_db.unchanged()


@pytest.mark.parametrize("argv", [["process", "7"], ["process", "8"], ["process-claude", "7"], ["process-claude", "8"]])
def test_process_cli_skips_a_stored_kimi_row_and_records_nothing(broker_db, capsys, argv):
    """A generic drain reads the broker, then skips a stored Kimi-addressed row, reporting it once."""
    from scripts.ai_agent_bridge import _cli

    _cli._dispatch_command(_cli._build_parser().parse_args(argv))
    assert capsys.readouterr().out.count(_SKIPPED) == 1
    assert broker_db.unchanged()


def test_detached_ask_worker_refuses_a_kimi_target_unopened(broker_db, monkeypatch):
    from scripts.ai_agent_bridge import _ask_lifecycle

    monkeypatch.setattr(_ask_lifecycle.atexit, "register", _fail)
    with pytest.raises(SystemExit, match=_TOKEN):
        _ask_lifecycle.process_background_ask(7, "kimi")
    assert broker_db.connects == []
    assert broker_db.unchanged()


@pytest.mark.parametrize("message_id", [7, 8])
def test_detached_ask_worker_skips_a_stored_kimi_row(broker_db, monkeypatch, capsys, message_id):
    from scripts.ai_agent_bridge import _ask_lifecycle

    monkeypatch.setattr(_ask_lifecycle.atexit, "register", _fail)
    assert _ask_lifecycle.process_background_ask(message_id, "claude") is None
    assert capsys.readouterr().out.count(_SKIPPED) == 1
    assert broker_db.unchanged()


def test_the_query_only_connection_never_creates_or_writes_the_db(broker_db, tmp_path, monkeypatch):
    from scripts.ai_agent_bridge import _db

    conn = _db.connect_readonly()
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("UPDATE messages SET acknowledged = 1")
    conn.close()
    assert broker_db.unchanged()
    monkeypatch.setattr(_db, "DB_PATH", tmp_path / "absent.db")
    assert _db.connect_readonly() is None
    assert not (tmp_path / "absent.db").exists()


# --- capacity hint -----------------------------------------------------------------


def _busy_codex(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(delegate, "_pid_alive", lambda _pid: True)
    (tasks / "busy.json").write_text(
        json.dumps({"task_id": "busy", "agent": "codex", "status": "running", "pid": 99999}), encoding="utf-8"
    )


def test_capacity_hint_never_suggests_kimi_for_non_coding_work(tmp_path, monkeypatch, capsys):
    _busy_codex(tmp_path, monkeypatch)
    review = types.SimpleNamespace(json=False, quiet=False, mode="read-only", require_review_verdict=True)
    delegate._check_capacity_hint("codex", args=review)
    err = capsys.readouterr().err
    assert "idle capacity is available in:" in err
    assert "kimi" not in err.split("available in:", 1)[1]


def test_capacity_hint_never_suggests_kimi_for_owned_content(tmp_path, monkeypatch, capsys):
    _busy_codex(tmp_path, monkeypatch)
    content = types.SimpleNamespace(
        json=False, quiet=False, mode="workspace-write", owned_path=["site/src/content/docs/x.mdx"]
    )
    delegate._check_capacity_hint("codex", args=content)
    assert "kimi" not in capsys.readouterr().err.split("available in:", 1)[1]


def test_capacity_hint_suggests_kimi_for_web_ui_and_backend_coding(tmp_path, monkeypatch, capsys):
    _busy_codex(tmp_path, monkeypatch)
    coding = types.SimpleNamespace(
        json=False,
        quiet=False,
        mode="workspace-write",
        owned_path=["site/src/components/Card.astro"],
        research_owned_path=["scripts/agent_runtime/runner.py"],
    )
    delegate._check_capacity_hint("codex", args=coding)
    assert "kimi" in capsys.readouterr().err.split("available in:", 1)[1]


# --- structural: no filesystem write before any Kimi refusal ---------------------------


class _WriteAttempt(BaseException):
    """A write before the refusal. A ``BaseException``, so no ``except Exception`` handler can swallow it."""


_WRITE_OPEN_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC


@pytest.fixture
def write_trap(tmp_path, monkeypatch):
    """Every filesystem, database and process creator raises and is recorded; reads still work.

    State roots (task records, the broker DB) live under ``tmp_path/state``, so
    a write the trap cannot see still shows up there. Tests seed state first,
    then call inside ``armed()``.
    """
    import builtins
    import io
    import shutil
    import tempfile

    state = tmp_path / "state"
    work = tmp_path / "work"
    state.mkdir()
    work.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(state / "tasks"))
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LU_AGENT_COMM_TRANSPORT", raising=False)
    from scripts.ai_agent_bridge import _db

    monkeypatch.setattr(_db, "DB_PATH", state / "broker" / "messages.db")
    attempts: list[str] = []

    def trap(name, real=None, reads=None):
        def creator(*args, **kwargs):
            if reads is not None and reads(*args, **kwargs):
                return real(*args, **kwargs)
            attempts.append(f"{name}{tuple(str(arg) for arg in args[:2])}")
            raise _WriteAttempt(f"{name} before the Kimi refusal: {args[:2]!r}")

        return creator

    def read_mode(_file, mode="r", *_args, **_kwargs):
        return not set(str(mode)) & set("wax+")

    def read_flags(_path, flags, *_args, **_kwargs):
        return not flags & _WRITE_OPEN_FLAGS

    def read_only_git(cmd, *_args, **_kwargs):
        return isinstance(cmd, (list, tuple)) and list(cmd[:1]) == ["git"] and cmd[1] in _GATE_GIT

    @contextlib.contextmanager
    def armed():
        """The trap, lifted on exit so nothing outside the call runs under it."""
        with pytest.MonkeyPatch.context() as trapped:
            _arm(trapped)
            yield attempts

    def _arm(monkeypatch) -> None:
        for owner, name in ((os, "mkdir"), (os, "makedirs"), (os, "replace"), (os, "rename"), (os, "remove")):
            monkeypatch.setattr(owner, name, trap(f"os.{name}"))
        for name in ("unlink", "rmdir", "symlink", "link", "truncate"):
            monkeypatch.setattr(os, name, trap(f"os.{name}"))
        monkeypatch.setattr(os, "open", trap("os.open", os.open, read_flags))
        monkeypatch.setattr(builtins, "open", trap("open", builtins.open, read_mode))
        monkeypatch.setattr(io, "open", trap("io.open", io.open, read_mode))
        for name in ("mkdir", "touch", "write_text", "write_bytes", "unlink", "rmdir", "rename", "replace"):
            monkeypatch.setattr(Path, name, trap(f"Path.{name}"))
        for name in ("mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile", "TemporaryDirectory"):
            monkeypatch.setattr(tempfile, name, trap(f"tempfile.{name}"))
        for name in ("copy", "copy2", "copyfile", "copytree", "move", "rmtree"):
            monkeypatch.setattr(shutil, name, trap(f"shutil.{name}"))
        # No refusal reads a database: even ``mode=ro`` creates -wal/-shm sidecars on a WAL-mode DB.
        monkeypatch.setattr(sqlite3, "connect", trap("sqlite3.connect"))
        monkeypatch.setattr(subprocess, "Popen", trap("subprocess.Popen", subprocess.Popen, read_only_git))

    return types.SimpleNamespace(state=state, work=work, armed=armed, monkeypatch=monkeypatch)


def _seed_task(state: Path, task_id: str, record: dict) -> None:
    tasks = state / "tasks"
    tasks.mkdir(exist_ok=True)
    (tasks / f"{task_id}.json").write_text(json.dumps({"task_id": task_id, **record}), encoding="utf-8")


def _tree(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() if path.is_file() else b"" for path in root.rglob("*")}


def _dispatch_main(argv):
    return lambda _trap: delegate.main(argv)


def _nested_dispatch(parent_mode: str | None):
    def call(trap):
        trap.monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "kimi-parent")
        return delegate.main(_dispatch())

    def seed(state):
        if parent_mode:
            _seed_task(state, "kimi-parent", {"mode": parent_mode, "status": "running"})

    return seed, call


def _worker(mode: str):
    def call(trap):
        return delegate._run_worker(
            task_id="kimi-worker",
            agent="kimi",
            prompt="Implement it.",
            mode=mode,
            cwd_str=str(trap.work),
            model=None,
            hard_timeout=60,
            harness="kimicc",
        )

    return call


def _runner_invoke(mode: str):
    def call(trap):
        from scripts.agent_runtime import runner

        return runner.invoke("kimi", "Implement it.", mode=mode, cwd=trap.work, tool_config=None)

    return call


def _adapter(harness: str):
    def call(trap):
        from scripts.agent_runtime.adapters import kimi as kimi_adapter
        from scripts.agent_runtime.adapters import kimicc as kimicc_adapter

        adapter = kimicc_adapter.KimiccHarness() if harness == "kimicc" else kimi_adapter.KimiAdapter()
        return adapter.build_invocation(
            prompt="p", mode="read-only", cwd=trap.work, model=None, task_id="t", session_id=None, tool_config=None
        )

    return call


def _acp_ask(trap):
    from scripts.ai_agent_bridge import _acp_compat

    return _acp_compat.run_compat_ask("kimi", "Consult on this design.", task_id="kimi-consult")


def _acp_inter_agent(trap):
    from scripts.agent_runtime import runner

    trap.monkeypatch.setenv(runner.ACPX_TRANSPORT_ENV, "active")
    return runner.invoke_inter_agent(
        "kimi", "Consult.", cwd=trap.work, task_id="t", correlation_id="c", idempotency_key="i"
    )


def _acp_discuss(trap):
    from scripts.agent_runtime import acpx_discuss

    return acpx_discuss.run_discussion(
        prompt="Compare the options.",
        cwd=trap.work,
        task_id="t",
        correlation_id="c",
        idempotency_key="i",
        rounds=1,
        participants=("claude", "kimi"),
    )


def _bridge(*argv: str, legacy_plane: bool = False):
    def call(trap):
        from scripts.ai_agent_bridge import _channels_cli, _cli

        if legacy_plane:  # authority mode retires `inbox run` before the Kimi gate
            trap.monkeypatch.setattr(_channels_cli, "_legacy_writes_retired", lambda: False)
        trap.monkeypatch.setattr(sys, "argv", ["ab", *argv])
        return _cli.main()

    return call


_PARENT_UNAVAILABLE = "read-only or unavailable parent task record"
_NESTED_WITH_PARENT = _nested_dispatch("workspace-write")
_NESTED_READ_ONLY_PARENT = _nested_dispatch("read-only")
_NESTED_WITHOUT_PARENT = _nested_dispatch(None)


@pytest.mark.parametrize(
    ("seed", "call", "refusal"),
    [
        pytest.param(None, _dispatch_main(_dispatch()), _TOKEN, id="dispatch-read-only"),
        pytest.param(None, _dispatch_main(_dispatch(*_WRITE)), _TOKEN, id="dispatch-unowned-write"),
        pytest.param(*_NESTED_WITH_PARENT, _TOKEN, id="nested-dispatch-with-parent"),
        pytest.param(*_NESTED_READ_ONLY_PARENT, _PARENT_UNAVAILABLE, id="nested-dispatch-read-only-parent"),
        pytest.param(*_NESTED_WITHOUT_PARENT, _PARENT_UNAVAILABLE, id="nested-dispatch-without-parent"),
        pytest.param(None, _worker("read-only"), _TOKEN, id="worker-read-only"),
        pytest.param(
            lambda state: _seed_task(state, "kimi-worker", {"mode": "workspace-write"}),
            _worker("workspace-write"),
            _TOKEN,
            id="worker-unowned-write",
        ),
        pytest.param(None, _runner_invoke("read-only"), _TOKEN, id="runner-invoke-read-only"),
        pytest.param(None, _runner_invoke("workspace-write"), _TOKEN, id="runner-invoke-unowned-write"),
        pytest.param(None, _adapter("kimi"), _TOKEN, id="kimi-adapter"),
        pytest.param(None, _adapter("kimicc"), _TOKEN, id="kimicc-adapter"),
        pytest.param(None, _acp_ask, _TOKEN, id="acp-ask"),
        pytest.param(None, _acp_inter_agent, _TOKEN, id="acp-inter-agent"),
        pytest.param(None, _acp_discuss, _TOKEN, id="acp-discuss"),
        pytest.param(None, _bridge("ask-kimi", "Consult.", "--task-id", "t"), _TOKEN, id="bridge-ask"),
        pytest.param(
            None,
            _bridge("ask-claude", "Consult.", "--task-id", "t", "--to-model", "kimi-code/k3"),
            _TOKEN,
            id="bridge-ask-kimi-model",
        ),
        pytest.param(None, _bridge("process-kimi", "7"), _TOKEN, id="bridge-process"),
        pytest.param(None, _bridge("inbox", "run", "kimi", "--once", legacy_plane=True), _TOKEN, id="bridge-inbox-run"),
        pytest.param(
            None, _bridge("discuss", "architecture", "Compare.", "--with", "claude,kimicc"), _TOKEN, id="bridge-discuss"
        ),
    ],
)
def test_no_entry_path_writes_before_the_kimi_refusal(write_trap, capsys, seed, call, refusal):
    """Every Kimi entry mode refuses with every creator trapped, and leaves the state roots as they were."""
    if seed:
        seed(write_trap.state)
    before = _tree(write_trap.state)

    with write_trap.armed() as attempts:
        try:
            outcome = call(write_trap)
        except _WriteAttempt as exc:
            outcome = exc
        except SystemExit as exc:
            outcome = exc.code
        except Exception as exc:  # each entry point refuses with its own error type
            outcome = exc
    captured = capsys.readouterr()

    assert attempts == []
    assert refusal in f"{outcome}\n{captured.out}\n{captured.err}"
    assert _tree(write_trap.state) == before


# --- every Kimi recipient entry against EXISTING WAL-mode broker and authority DBs ---------


def _seed_broker(live_wal: bool) -> list[sqlite3.Connection]:
    """A migrated WAL-mode broker DB and authority plane, each holding Kimi-addressed rows.

    The seeded rows are checkpointed into the main files, as SQLite leaves them
    once the last connection closes (no sidecars). With ``live_wal`` a writer
    stays open on each DB with newer, un-checkpointed inserts and routing
    updates, so ``-wal``/``-shm`` exist; the caller closes the returned writers.
    """
    from scripts.ai_agent_bridge import _db
    from scripts.fleet_comms.authority import AuthorityService

    conn = _db.get_db()
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    conn.executemany(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, message_type, content, data, timestamp)"
        " VALUES (?, 't', 'codex', ?, 'query', 'q', ?, '2026-09-30T00:00:00+00:00')",
        [(7, "kimi", None), (8, "claude", json.dumps({"to_model": "kimi-code/k3"}))],
    )
    conn.commit()
    conn.close()
    plane = _db.DB_PATH.parent.parent / "plane"
    with AuthorityService(root=plane) as service:
        service.create_channel("ops", subscribers=["claude", "kimi"])  # a legacy Kimi subscriber row
        comms = Path(service.store.db_path)
    databases = (_db.DB_PATH, comms)
    sidecars = [path.with_name(path.name + suffix) for path in databases for suffix in ("-wal", "-shm")]
    assert not any(path.exists() for path in sidecars)
    if not live_wal:
        return []
    broker = sqlite3.connect(_db.DB_PATH)
    broker.execute(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, content, timestamp)"
        " VALUES (9, 't', 'codex', 'kimi', 'q', '2026-09-30T00:00:00+00:00')"
    )
    broker.execute("UPDATE messages SET to_llm = 'kimi', data = ? WHERE id = 8", (json.dumps({"to_model": "k3"}),))
    broker.commit()
    authority = sqlite3.connect(comms)
    authority.execute(
        "INSERT INTO authority_channel_subscribers(channel_id, recipient, metadata_json, created_at)"
        " SELECT channel_id, 'kimicc', '{}', '2026-09-30T00:00:00+00:00' FROM authority_channels WHERE name = 'ops'"
    )
    authority.execute(
        "UPDATE authority_channel_subscribers SET metadata_json = '{\"lane\": 1}' WHERE recipient = 'kimi'"
    )
    authority.commit()
    assert all(path.exists() for path in sidecars)
    return [broker, authority]


def _stat_tree(root: Path) -> dict[str, tuple[int, int, bytes]]:
    """Every entry under *root* with its size, mtime and bytes: a created, touched or grown sidecar shows up."""
    return {
        str(path.relative_to(root)): (stat.st_size, stat.st_mtime_ns, path.read_bytes() if path.is_file() else b"")
        for path in sorted(root.rglob("*"))
        for stat in (path.stat(),)
    }


def _fleet(*argv: str):
    def call(trap):
        from scripts.fleet_comms import cli as fleet_cli

        return fleet_cli.main([*argv, "--root", str(trap.state / "plane")])

    return call


def _send(**kwargs):
    def call(_trap):
        from scripts.ai_agent_bridge import _messaging

        return _messaging.send_message("Consult.", **kwargs)

    return call


def _post(**kwargs):
    def call(_trap):
        from scripts.ai_agent_bridge import _channels

        return _channels.post("ops", "claude", "Consult.", **kwargs)

    return call


def _new_channel(_trap):
    from scripts.ai_agent_bridge import _channels

    return _channels.create_channel("kimi-ops", subscribers=["kimi"])


_KIMI_MODEL = ("--to-model", "kimi-code/k3")


@pytest.mark.parametrize("live_wal", [False, True], ids=["wal-checkpointed", "wal-live"])
@pytest.mark.parametrize(
    "call",
    [
        pytest.param(_bridge("ask-kimi", "Consult.", "--task-id", "t"), id="ask"),
        pytest.param(_bridge("ask-claude", "Consult.", "--task-id", "t", *_KIMI_MODEL), id="ask-kimi-model"),
        pytest.param(_bridge("send", "Consult.", "--to", "kimi"), id="send"),
        pytest.param(_bridge("send", "Consult.", "--to", "claude", *_KIMI_MODEL), id="send-kimi-model"),
        pytest.param(_bridge("post", "ops", "Consult.", "--to", "claude,kimi"), id="post"),
        pytest.param(_bridge("post", "ops", "Consult.", "--to", "claude", "--model", "k3"), id="post-kimi-model"),
        pytest.param(_bridge("p", "ops", "kimicc", "Consult."), id="p"),
        pytest.param(_bridge("channel", "new", "kimi-ops", "--agents", "kimi"), id="channel-new"),
        pytest.param(_bridge("inbox", "--for", "kimi"), id="inbox"),
        pytest.param(_bridge("inbox", "show", "kimi"), id="inbox-show"),
        pytest.param(_bridge("inbox", "run", "kimi", "--once", legacy_plane=True), id="inbox-run"),
        pytest.param(_bridge("ack-all", "kimi"), id="ack-all"),
        pytest.param(_bridge("sync", "kimi"), id="sync"),
        pytest.param(_bridge("process-kimi", "7"), id="process-kimi"),
        pytest.param(_bridge("process-ask", "7", "kimi"), id="process-ask"),
        pytest.param(_bridge("process", "8", "--model", "kimi-code/k3"), id="process-kimi-model"),
        pytest.param(_bridge("discuss", "architecture", "Compare.", "--with", "claude,kimicc"), id="discuss"),
        pytest.param(_send(to_llm="kimi"), id="send-message"),
        pytest.param(_send(to_llm="claude", to_model="kimi-code/k3"), id="send-message-kimi-model"),
        pytest.param(_post(to_agents=["kimi"]), id="channel-post"),
        pytest.param(_post(to_agents=["claude"], to_model="k3"), id="channel-post-kimi-model"),
        pytest.param(_new_channel, id="create-channel"),
        pytest.param(_acp_ask, id="acp-ask"),
        pytest.param(_acp_inter_agent, id="acp-inter-agent"),
        pytest.param(_acp_discuss, id="acp-discuss"),
        pytest.param(
            _fleet(
                "channel",
                "publish",
                "ops",
                "Consult.",
                "--sender",
                "claude",
                "--recipient",
                "kimi",
                "--idempotency-key",
                "k",
            ),
            id="fleet-publish",
        ),
        pytest.param(_fleet("channel", "subscribe", "ops", "kimicc"), id="fleet-subscribe"),
        pytest.param(_fleet("channel", "create", "kimi-ops", "--subscriber", "kimi"), id="fleet-create"),
        pytest.param(_fleet("deliveries", "claim", "--recipient", "kimi", "--worker-id", "w"), id="fleet-claim"),
    ],
)
def test_every_kimi_recipient_entry_leaves_existing_wal_databases_untouched(write_trap, capsys, call, live_wal):
    """Kimi is not a bridge recipient: each refusal opens no database, so no file or sidecar changes at all."""
    writers = _seed_broker(live_wal)
    try:
        before = _stat_tree(write_trap.state)
        with write_trap.armed() as attempts:
            try:
                outcome = call(write_trap)
            except _WriteAttempt as exc:
                outcome = exc
            except SystemExit as exc:
                outcome = exc.code
            except Exception as exc:  # each entry point refuses with its own error type
                outcome = exc
        captured = capsys.readouterr()

        assert attempts == []
        assert _TOKEN in f"{outcome}\n{captured.out}\n{captured.err}"
        assert _stat_tree(write_trap.state) == before
    finally:
        for writer in writers:
            writer.close()


# --- a Kimi model or recipient named in request data is refused like an explicit one ------------

_DATA_PAYLOADS = {
    "to-model": {"to_model": "kimi-code/k3"},
    "to-model-alias": {"to_model": "k3"},
    "model": {"model": "kimi-code/k3"},
    "target-model": {"target_model": "kimi-code/k3"},
    "requested-model": {"requested_model": "kimi-code/k3"},
    "to": {"to": "kimi"},
    "to-llm": {"to_llm": "kimicc"},
    "to-agent": {"to_agent": "kimi"},
    "to-agents": {"to_agents": ["claude", "kimi"]},
    "agent": {"agent": "acpx-kimi"},
    "target": {"target": "kimi"},
    "route": {"route": "acpx-kimi"},
    "recipients": {"recipients": ["claude", "kimicc"]},
    "participant": {"participant": "kimi"},
}


def _entry_send_message(_trap, payload, _path):
    from scripts.ai_agent_bridge import _messaging

    return _messaging.send_message("Consult.", to_llm="claude", data=json.dumps(payload))


def _entry_send_cli(trap, _payload, path):
    return _bridge("send", "Consult.", "--to", "claude", "--data", path)(trap)


def _entry_ask_cli(trap, _payload, path):
    return _bridge("ask-claude", "Consult.", "--task-id", "t", "--data", path)(trap)


def _entry_post(_trap, payload, _path):
    from scripts.ai_agent_bridge import _channels

    return _channels.post("ops", "claude", "Consult.", to_agents=["claude"], attachments=[payload])


def _entry_acp(_trap, payload, _path):
    from scripts.ai_agent_bridge import _acp_compat

    return _acp_compat.run_compat_ask("claude", "Consult.", task_id="t", data=json.dumps(payload))


_DATA_ENTRIES = {
    "send-message": _entry_send_message,
    "send-cli": _entry_send_cli,
    "ask-cli": _entry_ask_cli,
    "channel-post": _entry_post,
    "acp-ask": _entry_acp,
}


@pytest.mark.parametrize("live_wal", [False, True], ids=["wal-checkpointed", "wal-live"])
@pytest.mark.parametrize("entry", _DATA_ENTRIES)
@pytest.mark.parametrize("payload", _DATA_PAYLOADS)
def test_kimi_named_in_request_data_refuses_with_zero_effects(write_trap, capsys, payload, entry, live_wal):
    """The gate reads the merged metadata: data naming Kimi leaves every database and sidecar untouched."""
    writers = _seed_broker(live_wal)
    try:
        attachment = write_trap.work / "attachment.json"
        attachment.write_text(json.dumps(_DATA_PAYLOADS[payload]), encoding="utf-8")
        before = _stat_tree(write_trap.state)
        with write_trap.armed() as attempts:
            try:
                outcome = _DATA_ENTRIES[entry](write_trap, _DATA_PAYLOADS[payload], str(attachment))
            except _WriteAttempt as exc:
                outcome = exc
            except SystemExit as exc:
                outcome = exc.code
            except Exception as exc:  # each entry point refuses with its own error type
                outcome = exc
        captured = capsys.readouterr()

        assert attempts == []
        assert _TOKEN in f"{outcome}\n{captured.out}\n{captured.err}"
        assert _stat_tree(write_trap.state) == before
    finally:
        for writer in writers:
            writer.close()


def test_send_message_stores_no_kimi_row_for_data_supplied_model(write_trap):
    """The probe that found the gap: neutral recipient, Kimi model only in ``data``."""
    from scripts.ai_agent_bridge import _db, _messaging

    with pytest.raises(ValueError, match=_TOKEN):
        _messaging.send_message("q", to_llm="claude", data='{"to_model":"kimi-code/k3"}', quiet=True)
    assert not _db.DB_PATH.exists()


def test_explicit_model_replaces_the_data_model_as_before(write_trap, monkeypatch):
    """An explicit non-Kimi model overrides a data ``to_model``: admitted, and the explicit model is stored."""
    from scripts.ai_agent_bridge import _db, _messaging

    monkeypatch.setattr(_messaging.subprocess, "run", lambda *_a, **_k: None)
    msg_id = _messaging.send_message(
        "q", to_llm="claude", to_model="claude-opus-5-5", data='{"to_model":"kimi-code/k3"}', quiet=True
    )
    conn = _db.get_db()
    try:
        stored = json.loads(conn.execute("SELECT data FROM messages WHERE id = ?", (msg_id,)).fetchone()[0])
    finally:
        conn.close()
    assert stored["to_model"] == "claude-opus-5-5"


def test_non_json_and_neutral_data_stay_admitted():
    """Plain text, JSON arrays and neutral selector values are not refused."""
    from scripts.ai_agent_bridge import _acp_compat

    for data in (None, "plain text naming kimi in prose", "[\"kimi\"]", '{"to_model":"claude-opus-5-5","note":"kimi"}'):
        assert _acp_compat.require_compat_target("claude", data=data) == "claude"
    _acp_compat.refuse_kimi_recipients(("claude",), ("claude-opus-5-5",), attachments=({"to_model": "kimi-code/k3"},))


def test_authority_request_metadata_is_gated(tmp_path):
    """``enqueue_request`` refuses a Kimi model under any model key before writing."""
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tmp_path / "plane") as service:
        for key in kimi_admission.MODEL_SELECTOR_KEYS:
            with pytest.raises(kimi_admission.KimiAdmissionRefused):
                service.enqueue_request(recipient="claude", body="q", metadata={key: "kimi-code/k3"})
        job = service.enqueue_request(recipient="claude", body="q", metadata={"requested_model": "claude-opus-5-5"})
    assert job.job_id


class _KimiEffect(BaseException):
    """A Kimi-specific effect. A ``BaseException``, so no drain's ``except Exception`` can swallow it."""


@contextlib.contextmanager
def _kimi_effect_trap():
    """Arm, for a whole drain call, a trap on every Kimi-specific effect; generic broker reads stay allowed.

    Trapped: the ACP compat ask, the runtime runner and every legacy provider
    processor (adapter/runner invocation); process spawns and background
    relaunches; replies, acknowledgements, ask status and failure records,
    retry claims and terminal records (writes attributing processing); bridge
    usage telemetry. Every broker connection also gets an authorizer that
    records and denies any INSERT, UPDATE or DELETE on ``messages``.
    """
    from agent_runtime import runner as agent_runner
    from scripts.agent_runtime import runner as scripts_runner
    from scripts.ai_agent_bridge import (
        _acp_compat,
        _agy,
        _ask_lifecycle,
        _claude,
        _codex,
        _cursor,
        _grok_build,
        _hermes,
        _messaging,
        _opencode,
        _process,
    )
    from scripts.telemetry import legacy_bridge

    effects: list[str] = []

    def trap(name):
        def effect(*args, **_kwargs):
            effects.append(f"{name}{tuple(str(arg) for arg in args[:2])}")
            raise _KimiEffect(f"{name} on a stored Kimi row")

        return effect

    real_connect = sqlite3.connect

    def connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)

        def authorize(action, table, *_rest):
            if table == "messages" and action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE):
                effects.append(f"sqlite write {action} on messages")
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        conn.set_authorizer(authorize)
        return conn

    targets = [
        (_process, ("run_compat_ask", "send_message", "acknowledge", "record_ask_failure", "record_ask_reply")),
        (_process, ("_notify_processing_failure",)),
        (_acp_compat, ("run_compat_ask",)),
        (agent_runner, ("invoke", "invoke_inter_agent")),
        (scripts_runner, ("invoke", "invoke_inter_agent")),
        (_claude, ("process_for_claude",)),
        (_codex, ("process_for_codex",)),
        (_agy, ("process_for_agy",)),
        (_grok_build, ("process_for_grok_build",)),
        (_cursor, ("process_for_cursor",)),
        (_hermes, ("process_for_hermes",)),
        (_opencode, ("process_for_opencode",)),
        (_messaging, ("send_message", "acknowledge")),
        (_ask_lifecycle, ("mark_ask_processing", "record_ask_failure", "record_ask_reply", "_set_ask_status")),
        (_ask_lifecycle, ("claim_ask_retry", "launch_background_ask", "_AskTerminalRecorder", "_remove_pid_file")),
        (_ask_lifecycle.atexit, ("register",)),
        (subprocess, ("Popen",)),
        (os, ("fork", "posix_spawn", "posix_spawnp")),
        (legacy_bridge, ("start_bridge_invocation_safely", "finish_bridge_invocation_safely")),
        (legacy_bridge, ("record_bridge_invocation_start", "record_bridge_invocation_finish")),
    ]
    with pytest.MonkeyPatch.context() as trapped:
        for owner, names in targets:
            for name in names:
                trapped.setattr(owner, name, trap(f"{getattr(owner, '__name__', owner)}.{name}"))
        trapped.setattr(sqlite3, "connect", connect)
        yield effects


def _stored_drain_rows(writer: sqlite3.Connection) -> None:
    """Uncheckpointed Kimi-model rows addressed to the seats the batch drains select (10-12)."""
    writer.executemany(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, message_type, content, data, timestamp)"
        " VALUES (?, 't', 'agy', ?, 'query', 'q', ?, '2026-09-30T00:00:00+00:00')",
        [
            (10, "claude", json.dumps({"to_model": "kimi-code/k3"})),
            (11, "codex", json.dumps({"to_model": "k3"})),
            (12, "gemini", json.dumps({"to_model": "kimi-code/k3"})),
        ],
    )
    writer.commit()


def _direct(message_id):
    def call(_state):
        from scripts.ai_agent_bridge import _process

        return _process.process_message_for_recipient(message_id)

    return call


def _cli_argv(*argv):
    def call(_state):
        from scripts.ai_agent_bridge import _cli

        return _cli._dispatch_command(_cli._build_parser().parse_args(list(argv)))

    return call


def _interactive(message_id):
    def call(_state):
        from scripts.ai_agent_bridge import _cli

        return _cli._dispatch_interactive("process", ["process", str(message_id)])

    return call


def _target(message_id, target):
    def call(_state):
        from scripts.ai_agent_bridge import _ask_lifecycle

        return _ask_lifecycle._process_target(message_id, target, {"no_timeout": True})

    return call


def _background(message_id, target):
    def call(_state):
        from scripts.ai_agent_bridge import _ask_lifecycle

        return _ask_lifecycle.process_background_ask(message_id, target)

    return call


def _batch(seat):
    def call(_state):
        from scripts.ai_agent_bridge import _cli, _codex

        return {
            "claude": _cli.process_all_claude,
            "codex": _codex.process_all_codex,
            "gemini": _cli.process_all_gemini,
        }[seat]()

    return call


def _watchdog(agent, message_id=None):
    """The ask watchdog sweep, with a dead worker's launch record naming *agent*."""

    def call(_state):
        from scripts.ai_agent_bridge import _ask_lifecycle

        return _ask_lifecycle.run_ask_watchdog(message_id)

    call.launch_agent = agent
    return call


@pytest.mark.parametrize(
    ("call", "skips"),
    [
        pytest.param(_direct(8), 1, id="direct-routed-onto-kimi"),
        pytest.param(_direct(9), 1, id="direct-inserted-for-kimi"),
        pytest.param(_direct(10), 1, id="direct-kimi-model"),
        pytest.param(_cli_argv("process", "9"), 1, id="cli-process"),
        pytest.param(_cli_argv("process-claude", "8"), 1, id="cli-target"),
        pytest.param(_cli_argv("process-codex", "11"), 1, id="cli-target-kimi-model"),
        pytest.param(_interactive(9), 1, id="interactive-process"),
        pytest.param(_target(9, "claude"), 1, id="target-drain"),
        pytest.param(_background(9, "claude"), 1, id="background"),
        pytest.param(_background(10, "claude"), 1, id="background-kimi-model"),
        pytest.param(_batch("claude"), 1, id="process-all-claude"),
        pytest.param(_batch("codex"), 1, id="process-all-codex"),
        pytest.param(_batch("gemini"), 1, id="process-all-gemini"),
        pytest.param(_watchdog("kimi"), 3, id="ask-watchdog-kimi-launch"),
        pytest.param(_watchdog("claude", 10), 1, id="ask-watchdog-kimi-model"),
    ],
)
def test_generic_drains_skip_stored_kimi_rows_before_any_kimi_effect(tmp_path, monkeypatch, capsys, call, skips):
    """A generic drain skips a stored Kimi row before any Kimi-specific effect.

    Kimi is not a bridge recipient, and since sends refuse Kimi, a Kimi row
    can only be a legacy stored one. A generic drain (``process``,
    ``process-<seat>``, ``process-all``, a background worker, the ask
    watchdog) is not a Kimi request: reading the broker is its job, so it may
    open the WAL-mode DB and touch its ``-shm``. The binding invariant is that
    a stored Kimi-addressed row is skipped before any Kimi-specific effect —
    no adapter or runner invocation, no process, no reply row, no
    acknowledgement or status write attributing processing to Kimi, no Kimi
    telemetry — is left exactly as it was and is reported once as
    ``skipped: Kimi is not a bridge recipient``.

    The rows include uncheckpointed inserts and routing updates held in a
    live WAL (a writer stays open), and the trap is armed for the whole call.
    """
    from scripts.ai_agent_bridge import _ask_lifecycle, _db

    monkeypatch.setattr(_db, "DB_PATH", tmp_path / "state" / "broker" / "messages.db")
    broker, authority = _seed_broker(live_wal=True)
    authority.close()
    try:
        _stored_drain_rows(broker)
        launch_agent = getattr(call, "launch_agent", None)
        if launch_agent:
            monkeypatch.setattr(_ask_lifecycle, "REPO_ROOT", tmp_path)
            launch = tmp_path / "batch_state" / "asks" / "t" / "launch.json"
            launch.parent.mkdir(parents=True)
            launch.write_text(
                json.dumps({"pid": 999_999_999, "agent": launch_agent, "started_at": _ask_lifecycle._now_iso()}),
                encoding="utf-8",
            )
        before = broker.execute("SELECT * FROM messages ORDER BY id").fetchall()
        assert {row[3] for row in before if row[0] in (8, 9)} == {"kimi"}  # the WAL routing update and insert
        with _kimi_effect_trap() as effects, contextlib.suppress(_KimiEffect):
            call(None)
        out = capsys.readouterr().out

        assert effects == []
        assert out.count(_SKIPPED) == skips
        assert broker.execute("SELECT * FROM messages ORDER BY id").fetchall() == before
        assert not (tmp_path / "batch_state" / "asks" / "t" / "retry-claim").exists()
    finally:
        broker.close()


def test_a_kimi_subscriber_gets_no_delivery(tmp_path):
    """An existing Kimi subscriber row stays, but a fan-out publish never creates a delivery for it."""
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tmp_path / "plane") as service:
        service.create_channel("ops", subscribers=["claude", "kimi", "kimicc"])
        message = service.publish_message(sender="codex", body="Status.", channel="ops", idempotency_key="k")
        recipients = {
            row["recipient"]
            for row in service._conn.execute(
                "SELECT recipient FROM authority_deliveries WHERE message_id = ?", (message.message_id,)
            )
        }
        assert recipients == {"claude"}
        assert set(service.get_channel("ops").subscribers) == {"claude", "kimi", "kimicc"}


@pytest.mark.parametrize("broadcast", [False, True])
def test_channel_default_recipients_skip_kimi_seats(monkeypatch, broadcast):
    from scripts.ai_agent_bridge import _channels, _channels_cli

    channel = {"subscribers": ["claude", "kimi", "kimicc", "codex"]}
    monkeypatch.setattr(_channels, "live_agents", lambda: ["claude", "kimi", "kimicc", "codex"])
    recipients = (
        _channels_cli._broadcast_recipients(channel) if broadcast else _channels_cli._subscriber_recipients(channel)
    )
    assert recipients == ["claude", "codex"]


# --- stored Kimi deliveries: generic drains and sweeps leave them untouched ----------

_OLD = "2020-01-01T00:00:00+00:00"


@pytest.fixture
def delivery_db(tmp_path, monkeypatch):
    """A channel broker with legacy Kimi deliveries (by seat and by model) and matching non-Kimi controls.

    Kimi rows are older than their controls, so a drain that ignored the
    filter would reach them first. Returns ``rows()``, the full deliveries
    table keyed by id.
    """
    from scripts.ai_agent_bridge import _channels, _db

    db_file = tmp_path / "messages.db"
    monkeypatch.setattr("scripts.ai_agent_bridge._config.DB_PATH", db_file)
    monkeypatch.setattr(_db, "DB_PATH", db_file)
    monkeypatch.setattr(_channels, "WAKE_ROOT", tmp_path / "wake")
    _db.init_db().close()
    _channels.create_channel("topic")
    conn = _db.get_db()
    rows = [
        # id, to_agent, to_model, status, lease_until, attempt_count, retry_after, created_at
        ("kimi-model", "claude", "kimi-code/k3", "pending", None, 0, None, "2020-01-01T00:00:00+00:00"),
        ("kimi-seat", "kimi", None, "pending", None, 0, None, "2020-01-01T00:00:01+00:00"),
        ("kimi-alias-lease", "claude", "k3", "processing", _OLD, 1, None, "2020-01-01T00:00:02+00:00"),
        ("kimi-exhausted", "claude", "kimi-code/k3", "pending", None, 9, _OLD, "2020-01-01T00:00:03+00:00"),
        ("claude-pending", "claude", None, "pending", None, 0, None, "2020-01-02T00:00:00+00:00"),
        ("claude-lease", "claude", None, "processing", _OLD, 1, None, "2020-01-02T00:00:01+00:00"),
        ("claude-exhausted", "claude", None, "pending", None, 9, _OLD, "2020-01-02T00:00:02+00:00"),
    ]
    for delivery_id, to_agent, to_model, status, lease, attempts, retry_after, created_at in rows:
        conn.execute(
            "INSERT INTO channel_messages (message_id, channel, thread_id, from_agent, body, created_at)"
            " VALUES (?, 'topic', ?, 'user', 'q', ?)",
            (f"m-{delivery_id}", f"t-{delivery_id}", created_at),
        )
        conn.execute(
            "INSERT INTO deliveries (delivery_id, message_id, to_agent, to_model, status, lease_until,"
            " attempt_count, retry_after) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (delivery_id, f"m-{delivery_id}", to_agent, to_model, status, lease, attempts, retry_after),
        )
    conn.commit()
    conn.close()

    def snapshot() -> dict[str, tuple]:
        check = sqlite3.connect(db_file)
        try:
            return {row[0]: tuple(row) for row in check.execute("SELECT * FROM deliveries ORDER BY delivery_id")}
        finally:
            check.close()

    return snapshot


def _kimi_rows(snapshot: dict[str, tuple]) -> dict[str, tuple]:
    return {key: row for key, row in snapshot.items() if key.startswith("kimi-")}


def _changed(before: dict[str, tuple], after: dict[str, tuple]) -> set[str]:
    return {key for key in before if before[key] != after[key]}


def _sweep(name):
    def call():
        from scripts.ai_agent_bridge import _channels, _reconcile

        return {
            "claim": lambda: _channels.claim_next_delivery("claude"),
            "release-leases": _channels.release_expired_leases,
            "expire-stale": _channels.expire_stale_deliveries,
            "expire-dead-lanes": lambda: _channels.bulk_expire_dead_lanes(frozenset({"claude", "kimi"})),
            "reconcile": _reconcile.reconcile_deliveries,
        }[name]()

    return call


@pytest.mark.parametrize(
    ("sweep", "control"),
    [
        ("claim", {"claude-pending"}),  # the oldest eligible non-Kimi row, not the older Kimi rows
        ("release-leases", {"claude-lease"}),
        ("expire-stale", {"claude-pending", "claude-exhausted"}),
        ("expire-dead-lanes", {"claude-pending", "claude-exhausted"}),
        ("reconcile", {"claude-lease", "claude-exhausted"}),
    ],
)
def test_channel_sweeps_leave_stored_kimi_deliveries_unwritten(delivery_db, sweep, control):
    """Every generic channel drain and sweep excludes a stored Kimi delivery before it writes."""
    before = delivery_db()
    _sweep(sweep)()
    after = delivery_db()
    assert _kimi_rows(after) == _kimi_rows(before)
    assert _changed(before, after) == control


def test_the_inbox_drain_skips_a_stored_kimi_delivery_before_claim_writes_or_telemetry(delivery_db, monkeypatch):
    """The reviewer's case: a delivery to Claude pinned to a Kimi model is never claimed, failed or reported.

    The drain's own sweeps expire the old Claude rows and it delivers a fresh
    one (non-Kimi paths unchanged).
    """
    from agent_runtime.result import Result
    from scripts.ai_agent_bridge import _channels, _inbox

    telemetry: list[tuple] = []
    for name in ("emit_delivery_failed", "emit_delivery_delivered", "emit_reply_started", "emit_reply_complete"):
        monkeypatch.setattr(_inbox, name, lambda *args, _name=name, **kwargs: telemetry.append((_name, args, kwargs)))
    monkeypatch.setattr(
        "scripts.fleet_comms.bottleneck_alerts.scan_bottlenecks_at_inbox_checkpoint", lambda **_kwargs: None
    )
    invoked: list[str] = []

    def invoke(agent, prompt, **kwargs):
        invoked.append(kwargs["task_id"])
        return Result(
            ok=True,
            agent=agent,
            model=kwargs.get("model") or "claude-opus-5-5",
            mode=kwargs["mode"],
            response="reply",
            stderr_excerpt="",
            duration_s=0.0,
            session_id="s",
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        )

    monkeypatch.setattr(_inbox, "runtime_invoke", invoke)
    fresh = _channels.post("topic", "user", "q", to_agents=["claude"], auto_snapshot=False)
    before = delivery_db()

    summary = _inbox.run_inbox("claude")
    after = delivery_db()

    assert _kimi_rows(after) == _kimi_rows(before)
    kimi_threads = {f"t-{key}" for key in _kimi_rows(before)}
    assert not [event for event in telemetry if event[1] and event[1][0] in kimi_threads]
    session = _inbox._thread_session_key
    assert invoked == [session("topic", "t-claude-lease"), session("topic", str(fresh["thread_id"]))]
    delivered = {key for key, row in after.items() if row[4] == "delivered"}
    assert delivered == {"claude-lease", *(key for key in after if not key.startswith(("kimi-", "claude-")))}
    assert (summary.deliveries_claimed, summary.deliveries_failed) == (2, 0)


def test_fleet_comms_delivery_reclaim_leaves_a_stored_kimi_delivery_unwritten(tmp_path):
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tmp_path / "plane") as service:
        message = service.publish_message(sender="user", body="q", recipients=["claude"], deadline_at=_OLD)
        conn = service._conn
        conn.execute(
            "INSERT INTO authority_deliveries (delivery_id, message_id, recipient, state, deadline_at,"
            " created_at, updated_at) VALUES ('kimi-legacy', ?, 'kimi', 'queued', ?, ?, ?)",
            (message.message_id, _OLD, _OLD, _OLD),
        )
        conn.commit()
        dump = lambda: {row["delivery_id"]: tuple(row) for row in conn.execute("SELECT * FROM authority_deliveries")}  # noqa: E731
        dead_letters = lambda: conn.execute("SELECT COUNT(*) FROM authority_dead_letters").fetchone()[0]  # noqa: E731
        before, letters = dump(), dead_letters()

        assert service.reclaim_expired_deliveries() == 1
        after = dump()
        assert after["kimi-legacy"] == before["kimi-legacy"]
        assert [row[3] for key, row in after.items() if key != "kimi-legacy"] == ["expired"]
        assert dead_letters() == letters + 1


def test_the_stale_request_requeue_leaves_a_stored_kimi_request_running(tmp_path):
    """A stored request to a Kimi seat, or whose message metadata pins a Kimi model, is never requeued."""
    from scripts.fleet_comms.request_executor import RequestExecutor

    with RequestExecutor(root=tmp_path) as executor:
        kept = executor.create_request(recipient="codex", body="ping", metadata={"model": "gpt-6.1-sol"})
        legacy = executor.create_request(recipient="claude", body="ping")
        pinned = executor.create_request(recipient="claude", body="ping")
        conn = executor.store.connection
        conn.execute("UPDATE requests SET state = 'running', updated_at = '2000-01-01T00:00:00Z'")
        conn.execute("UPDATE requests SET resolved_recipient = 'kimi' WHERE request_id = ?", (legacy.request_id,))
        conn.execute(
            "UPDATE comms_messages SET metadata_json = ? WHERE message_id = ?",
            (json.dumps({"model": "kimi-code/k3"}), pinned.request_message_id),
        )
        conn.commit()

        assert executor.requeue_stale_running(stale_after_seconds=60) == [kept.request_id]
        assert executor.get_request(legacy.request_id).state == "running"
        assert executor.get_request(pinned.request_id).state == "running"


def test_create_request_refuses_a_kimi_model_in_its_metadata_before_any_insert(tmp_path):
    from scripts.agent_runtime.kimi_admission import KimiAdmissionRefused
    from scripts.fleet_comms.request_executor import RequestExecutor

    with RequestExecutor(root=tmp_path) as executor:
        conn = executor.store.connection
        with pytest.raises(KimiAdmissionRefused):
            executor.create_request(recipient="claude", body="ping", metadata={"model": "k3"})
        assert conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM comms_messages").fetchone()[0] == 0


def test_the_ancient_message_sweep_leaves_a_stored_kimi_message_unacknowledged(broker_db, capsys):
    from scripts.ai_agent_bridge import _broker, _db

    check = sqlite3.connect(_db.DB_PATH)
    check.execute("UPDATE messages SET timestamp = ?", (_OLD,))
    check.execute("UPDATE messages SET acknowledged = 0")
    check.commit()
    assert _broker._cleanup_ancient_messages("force-ack", 1, dry_run=False) == 1
    acknowledged = dict(check.execute("SELECT id, acknowledged FROM messages"))
    check.close()
    assert acknowledged == {7: 0, 8: 0, 9: 1}
    assert capsys.readouterr().out.count(_SKIPPED) == 2


# --- stored Kimi authority jobs: generic reclaim and claim paths leave them untouched ----------

_FUTURE = "2999-01-01T00:00:00Z"


def _legacy_job(service, payload, *, kind="request", deadline_at=None, lease_expires_at=None):
    """A stored job written before enqueue refused Kimi (bypasses admission, as legacy rows did)."""
    from scripts.fleet_comms.contracts import new_id

    with service._write_transaction():
        job = service._enqueue_job_tx(
            job_kind=kind,
            subject_id=new_id("legacy-subject"),
            payload=payload,
            deadline_at=deadline_at,
            idempotency_key=new_id("legacy-key"),
        )
    if lease_expires_at is not None:
        service._conn.execute(
            "UPDATE authority_jobs SET state = 'running', lease_owner = 'w', lease_expires_at = ?, fence_token = 1"
            " WHERE job_id = ?",
            (lease_expires_at, job.job_id),
        )
        service._conn.commit()
    return job.job_id


@pytest.fixture
def job_plane(tmp_path):
    """An authority plane with stored Kimi jobs (by seat, model and participant) older than non-Kimi controls.

    Every Kimi job is due for a generic write: expired deadlines, a stale
    running lease, or simply queued first. Returns ``(service, kimi_ids,
    controls, state)`` where ``state()`` snapshots the job, event and
    dead-letter rows per job.
    """
    from scripts.fleet_comms.authority import AuthorityService

    service = AuthorityService(root=tmp_path / "plane")
    kimi_ids = {
        "seat-expired": _legacy_job(service, {"recipient": "kimi", "metadata": {}}, deadline_at=_OLD),
        "model-stale-lease": _legacy_job(
            service,
            {"recipient": "claude", "metadata": {"requested_model": "kimi-code/k3"}},
            lease_expires_at=_OLD,
        ),
        "participant-expired": _legacy_job(
            service, {"participants": ["claude", "kimicc"]}, kind="discussion", deadline_at=_OLD
        ),
        "alias-queued": _legacy_job(service, {"recipient": "codex", "metadata": {"model": "k3"}}),
    }
    controls = {
        "expired": _legacy_job(service, {"recipient": "codex", "metadata": {"task_id": "e"}}, deadline_at=_OLD),
        "stale-lease": _legacy_job(service, {"recipient": "codex", "metadata": {"task_id": "s"}}, lease_expires_at=_OLD),
    }

    def state():
        conn = service._conn
        return {
            job_id: (
                tuple(conn.execute("SELECT * FROM authority_jobs WHERE job_id = ?", (job_id,)).fetchone()),
                conn.execute("SELECT COUNT(*) FROM authority_job_events WHERE job_id = ?", (job_id,)).fetchone()[0],
                conn.execute("SELECT COUNT(*) FROM authority_dead_letters WHERE job_id = ?", (job_id,)).fetchone()[0],
            )
            for job_id in (*kimi_ids.values(), *controls.values())
        }

    try:
        yield service, kimi_ids, controls, state
    finally:
        service.close()


def _job_state(service, job_id):
    return service.get_job(job_id).state


@pytest.mark.parametrize("entry", ["claim-job", "claim-next-job", "reclaim"])
def test_generic_job_reclaim_and_claims_leave_stored_kimi_jobs_unwritten(job_plane, entry):
    """The reviewer's case: claiming a non-Kimi job never expires, events or dead-letters a legacy Kimi job.

    ``claim_job`` (reached from the ACP compat ask and channel ``ask``) and
    ``claim_next_job`` both run the generic reclaim first; ``claim_next_job``
    also passes over the older queued Kimi jobs. Non-Kimi controls are
    reclaimed as before.
    """
    service, kimi_ids, controls, state = job_plane
    fresh = service.enqueue_request(recipient="claude", body="ping", deadline_at=_FUTURE)
    before = state()

    if entry == "claim-job":
        lease = service.claim_job(fresh.job_id, "worker", now="2026-09-30T00:00:00Z")
    elif entry == "claim-next-job":
        lease = service.claim_next_job("worker", now="2026-09-30T00:00:00Z")
    else:
        lease = None
        assert service.reclaim_expired_jobs(now="2026-09-30T00:00:00Z") == 2

    after = state()
    assert {job_id: after[job_id] for job_id in kimi_ids.values()} == {
        job_id: before[job_id] for job_id in kimi_ids.values()
    }
    assert _job_state(service, controls["expired"]) == "expired"
    assert after[controls["expired"]][2] == 1  # dead-lettered, as before
    if lease is not None:
        # claim_next_job takes the oldest non-Kimi queued job: the requeued control, then the fresh one.
        assert lease.job.job_id in {fresh.job_id, controls["stale-lease"]}
        assert lease.job.state == "running"
    if entry != "claim-next-job":
        assert _job_state(service, controls["stale-lease"]) == "queued"


@pytest.mark.parametrize("operation", ["claim_job", "retry_job", "redrive_job"])
def test_a_named_stored_kimi_job_is_refused_unwritten(job_plane, operation):
    """Claiming, retrying or redriving a stored Kimi job by id is refused before any write."""
    from scripts.fleet_comms.authority import AuthorityServiceError

    service, kimi_ids, _controls, state = job_plane
    job_id = kimi_ids["seat-expired"]
    service._conn.execute(
        "UPDATE authority_jobs SET state = ? WHERE job_id = ?",
        ("dead_lettered" if operation == "redrive_job" else "failed" if operation == "retry_job" else "queued", job_id),
    )
    service._conn.commit()
    before = state()
    call = getattr(service, operation)
    args = (job_id, "worker") if operation == "claim_job" else (job_id,)
    with pytest.raises(AuthorityServiceError, match=r"kimi_job_not_(claimable|retryable)"):
        call(*args, now="2026-09-30T00:00:00Z", **({} if operation == "claim_job" else {"deadline_at": _FUTURE}))
    assert state() == before


def test_an_unreadable_job_payload_is_left_unwritten(job_plane):
    """A payload that cannot be read is not provably non-Kimi, so a generic reclaim leaves the job (fail closed)."""
    service, _kimi_ids, controls, state = job_plane
    job = service.get_job(controls["expired"])
    service.store.get(job.payload_artifact_id).blob_path.write_bytes(b"tampered")
    service._kimi_payloads.clear()
    before = state()
    assert service.reclaim_expired_jobs(now="2026-09-30T00:00:00Z") == 1  # only the stale-lease control
    assert state()[controls["expired"]] == before[controls["expired"]]


def test_a_delivery_of_a_kimi_model_request_is_never_claimed_or_reclaimed(tmp_path):
    """A stored delivery to Claude of a request pinned to a Kimi model is passed over by claims and reclaims."""
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tmp_path / "plane") as service:
        legacy = service.publish_message(sender="user", body="old", recipients=["claude"], deadline_at=_FUTURE)
        stale = service.publish_message(sender="user", body="stale", recipients=["claude"], deadline_at=_OLD)
        for message in (legacy, stale):
            with service._write_transaction():
                service._enqueue_job_tx(
                    job_kind="request",
                    subject_id=message.message_id,
                    payload={"recipient": "claude", "metadata": {"requested_model": "kimi-code/k3"}},
                    deadline_at=None,
                    idempotency_key=f"legacy-{message.message_id}",
                )
        fresh = service.publish_message(sender="user", body="new", recipients=["claude"], deadline_at=_FUTURE)
        conn = service._conn
        dump = lambda: {row["delivery_id"]: tuple(row) for row in conn.execute("SELECT * FROM authority_deliveries")}  # noqa: E731
        kimi_deliveries = {*legacy.delivery_ids, *stale.delivery_ids}
        before = dump()

        lease = service.claim_next_delivery("claude", "worker", now="2026-09-30T00:00:00Z")
        assert lease is not None and lease.delivery.delivery_id == fresh.delivery_ids[0]
        after = dump()
        assert {key: after[key] for key in kimi_deliveries} == {key: before[key] for key in kimi_deliveries}
        assert not conn.execute(
            "SELECT COUNT(*) FROM authority_delivery_attempts WHERE delivery_id IN (?, ?)", tuple(kimi_deliveries)
        ).fetchone()[0]
        assert not conn.execute("SELECT COUNT(*) FROM authority_dead_letters").fetchone()[0]


# --- stored Kimi bridge messages: bulk acknowledgement, timeout notices, retention, migration ----------


@pytest.fixture
def message_db(tmp_path, monkeypatch):
    """A broker with stored Kimi messages (by seat, by ``to_model``, by another data key) and non-Kimi controls.

    Every row is old, acknowledged-or-timed-out and due for a generic write.
    Returns ``rows()``, the messages table keyed by id.
    """
    from scripts.ai_agent_bridge import _broker, _db

    db_file = tmp_path / "messages.db"
    monkeypatch.setattr(_db, "DB_PATH", db_file)
    monkeypatch.setattr(_broker, "DB_PATH", db_file)
    seed = _db.get_db()
    seed.executemany(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, message_type, content, data, timestamp, acknowledged,"
        " status) VALUES (?, 't', 'codex', ?, 'query', 'q', ?, ?, ?, ?)",
        [
            (1, "kimi", None, _OLD, 0, "timed-out:x"),
            (2, "claude", json.dumps({"to_model": "kimi-code/k3"}), _OLD, 0, "timed-out:x"),
            (3, "claude", json.dumps({"model": "k3"}), _OLD, 0, "timed-out:x"),
            (4, "claude", None, _OLD, 0, "timed-out:x"),
            (5, "claude", json.dumps({"to_model": "claude-opus-5-5"}), _OLD, 0, "timed-out:x"),
        ],
    )
    seed.commit()
    seed.close()

    def rows() -> dict[int, tuple]:
        check = sqlite3.connect(db_file)
        try:
            return {row[0]: tuple(row) for row in check.execute("SELECT * FROM messages ORDER BY id")}
        finally:
            check.close()

    return rows


_KIMI_MESSAGES = (1, 2, 3)


def test_ack_all_leaves_a_stored_kimi_model_message_unacknowledged(message_db, capsys):
    from scripts.ai_agent_bridge import _messaging

    before = message_db()
    _messaging.acknowledge_all("claude", consumed_by_live_driver=True)
    after = message_db()
    assert {key for key in before if before[key] != after[key]} == {4, 5}
    assert "4, 5" in capsys.readouterr().out


def test_timeout_notices_neither_show_nor_mark_a_stored_kimi_ask(message_db, capsys):
    from scripts.ai_agent_bridge import _ask_lifecycle

    before = message_db()
    assert _ask_lifecycle.print_timeout_notice() == [4, 5]
    _ask_lifecycle.mark_timeout_notices_shown([1, 2, 3, 4, 5])
    after = message_db()
    assert {key for key in before if before[key] != after[key]} == {4, 5}
    assert "#1 " not in capsys.readouterr().err


def test_retention_keeps_stored_kimi_messages_and_deliveries(message_db, delivery_db):
    """``ab cleanup`` retention deletes old terminal rows but keeps stored Kimi ones and their channel messages."""
    from scripts.ai_agent_bridge import _broker, _db

    conn = _db.get_db()
    conn.execute("UPDATE messages SET acknowledged = 1")
    conn.execute("UPDATE deliveries SET status = 'delivered', lease_until = NULL")
    conn.commit()
    conn.close()
    deliveries_before = delivery_db()

    assert _broker.broker_retention_cleanup("1d", dry_run=True) == 2 + 3 + 3
    assert _broker.broker_retention_cleanup("1d") == 8

    assert set(message_db()) == set(_KIMI_MESSAGES)
    assert delivery_db() == _kimi_rows(deliveries_before)
    check = sqlite3.connect(_db.DB_PATH)
    try:
        kept = {row[0] for row in check.execute("SELECT message_id FROM channel_messages")}
    finally:
        check.close()
    assert kept == {f"m-{key}" for key in _kimi_rows(deliveries_before)}


def test_the_live_consumption_backfill_leaves_a_stored_kimi_message_as_it_is(tmp_path, monkeypatch):
    """The one-time ``consumed_by_live_driver`` backfill grandfathers acknowledged rows, except stored Kimi ones."""
    from scripts.ai_agent_bridge import _db

    db_file = tmp_path / "messages.db"
    monkeypatch.setattr(_db, "DB_PATH", db_file)
    legacy = sqlite3.connect(db_file)
    legacy.execute(
        "CREATE TABLE messages (id INTEGER PRIMARY KEY, task_id TEXT, from_llm TEXT NOT NULL, to_llm TEXT NOT NULL,"
        " message_type TEXT, content TEXT NOT NULL, data TEXT, timestamp TEXT NOT NULL, acknowledged INTEGER DEFAULT 0)"
    )
    legacy.executemany(
        "INSERT INTO messages (id, from_llm, to_llm, content, data, timestamp, acknowledged)"
        " VALUES (?, 'codex', ?, 'q', ?, ?, 1)",
        [(1, "kimi", None, _OLD), (2, "claude", json.dumps({"to_model": "k3"}), _OLD), (3, "claude", None, _OLD)],
    )
    legacy.commit()
    legacy.close()

    _db.get_db().close()
    check = sqlite3.connect(db_file)
    try:
        consumed = dict(check.execute("SELECT id, consumed_by_live_driver FROM messages"))
    finally:
        check.close()
    assert consumed == {1: 0, 2: 0, 3: 1}
