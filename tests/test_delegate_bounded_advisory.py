"""#9275 envelope integrity and #10919 driver-brief admission and replay.

Outside #10919 recon/classification and bounded implementation, every ``gpt-6-luna`` dispatch and every Gemini
Flash dispatch without an explicit Ukrainian authoring/review classification,
needs an envelope issued by a finished ``gpt-6.1-sol`` advisory task and bound
to this dispatch's arguments. Test names carry the frozen acceptance-matrix row
(M1–M18) they prove.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.agent_runtime import bounded_advisory

# Delivery is proven against the driver-bound destination, never the worker's
# tracking refs (#10931); workers built by _bounded_worktree push to its origin.git.

# Lease directory names are the task ids. One module-wide id shares a lease
# across xdist workers (#9927). Each case gets its own worker id and advisor id.


# --- M1 -------------------------------------------------------------------


# --- M2 -------------------------------------------------------------------


# --- M3 -------------------------------------------------------------------


# --- M4 -------------------------------------------------------------------


# --- M5 -------------------------------------------------------------------


# --- M6 -------------------------------------------------------------------


# --- M7 -------------------------------------------------------------------


# --- M8 -------------------------------------------------------------------


# --- M9 -------------------------------------------------------------------


# --- M10 / M15 / M16 / M17: the Gemini Flash bounded fallback ---------------


# --- M11 / M18: admitted Gemini Flash dispatches ---------------------------


# --- M13 / M14 --------------------------------------------------------------


# --- The advisor side --------------------------------------------------------


# --- M12 / M13 at finalize: the envelope ceilings ------------------------------


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, timeout=30)


# The launch a worker admitted by ``_admitted_worker`` runs: what ``_start_worker`` passes.
_BOUND_LAUNCH_ARGS = (
    "effort", "hard_timeout", "silence_timeout", "initial_response_timeout", "max_budget_usd", "provider",
    "finalize_open_pr",
)  # fmt: skip


# --- Pure helpers --------------------------------------------------------------


def test_numstat_parser_and_test_path_classifier():
    entries = bounded_advisory.parse_numstat_z("3\t1\tsrc/a.py\x00-\t-\timg.png\x0010\t0\ttests/test_a.py\x00")
    assert entries == [(3, 1, "src/a.py"), (None, None, "img.png"), (10, 0, "tests/test_a.py")]
    verdict = bounded_advisory.ceiling_verdict(entries, max_changed_files=3, max_non_test_loc=4)
    assert (verdict["changed_files"], verdict["non_test_loc"], verdict["exceeded"]) == (3, 4, [])
    assert bounded_advisory.is_test_path("scripts/x/test_y.py")
    assert bounded_advisory.is_test_path("pkg/conftest.py")
    assert bounded_advisory.is_test_path("site/foo_test.ts")
    assert not bounded_advisory.is_test_path("scripts/testing_helpers.py")
    with pytest.raises(ValueError):
        bounded_advisory.parse_numstat_z("garbage\x00")


# --- M6: the binding covers the prompt text, not only the prompt path -------------


# --- Round 2 (review of record): B1 the worker backstop -------------------------


# --- Round 2: B2 classification of normalized owned paths ------------------------


@pytest.fixture
def content_repo(tmp_path, monkeypatch):
    """A git repository with Ukrainian content, code, and symlinks and attributes that cross between them."""
    for key in tuple(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts" / "gate.py").write_text("ALLOW = False\n")
    (repo / "docs" / "lessons").mkdir(parents=True)
    (repo / "docs" / "lessons" / "one.md").write_text("# Урок\n")
    (repo / "docs" / "linked-code").symlink_to("../scripts", target_is_directory=True)
    (repo / "docs" / "lessons" / "notes.md").symlink_to("../../scripts/gate.py")
    (repo / "docs" / "empty-link").symlink_to("../scripts/none", target_is_directory=True)
    (repo / "docs" / "attributed").mkdir()
    (repo / "docs" / "attributed" / "runner.txt").write_text("print('x')\n")
    (repo / "docs" / "attributed" / "readme.txt").write_text("text\n")
    (repo / "docs" / "aliased").mkdir()
    (repo / "docs" / "aliased" / "lesson.md").symlink_to("../attributed/runner.txt")
    (repo / ".gitattributes").write_text("docs/attributed/runner.txt diff=python\n")
    _git("init", "--initial-branch=main", str(repo), cwd=tmp_path)
    _git("add", "-A", cwd=repo)
    _git("-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "base", cwd=repo)
    return repo


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("docs/linked-code/", "outside the Ukrainian content roots"),
        ("docs/linked-code/gate.py", "names a code file"),
        ("docs/lessons/", "covers 'docs/lessons/notes.md', which is a code file"),
        ("docs/lessons/notes.md", "outside the Ukrainian content roots"),
        ("docs/**/*.md", "reaches directory 'docs/linked-code'"),
        ("docs/empty-link", "outside the Ukrainian content roots"),
        ("docs/attributed/", "git attributes mark as code"),
        ("docs/attributed/runner.txt", "git attributes mark as code"),
        ("docs/aliased/lesson.md", "git attributes mark as code (its target 'docs/attributed/runner.txt')"),
        ("docs/aliased/", "git attributes mark as code (its target 'docs/attributed/runner.txt')"),
        ("docs/aliased/*.md", "git attributes mark as code (its target 'docs/attributed/runner.txt')"),
    ],
)
def test_b2_symlinks_into_code_and_code_attributes_are_not_content(content_repo, path, reason):
    """Acceptance 5: ownership is judged by resolved files, symlinks followed, and by git attributes."""
    problem = bounded_advisory.content_path_problem(path, content_repo)
    assert problem is not None and reason in problem, problem


@pytest.mark.parametrize("path", ["docs/lessons/one.md", "docs/attributed/readme.txt", "docs/new-lessons/"])
def test_b2_content_only_files_beside_the_probes_stay_eligible(content_repo, path):
    assert bounded_advisory.content_path_problem(path, content_repo) is None


@pytest.mark.parametrize("inside_git_dir", [False, True], ids=["plain", "git-dir"])
def test_b2_an_unreadable_tree_fails_closed(tmp_path, monkeypatch, inside_git_dir):
    for key in tuple(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    root = tmp_path
    if inside_git_dir:
        enclosing = tmp_path / "enclosing"
        _git("init", "--initial-branch=main", str(enclosing), cwd=tmp_path)
        root = enclosing / ".git" / "unreadable"
    (root / "docs").mkdir(parents=True)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(root.parent))
    problem = bounded_advisory.content_path_problem("docs/", root)
    assert problem is not None and "cannot be resolved" in problem
    assert "not a git repository" in problem


# --- Round 2: B3 the finish-time seal --------------------------------------------


# --- Round 3: B3 the content-exemption completion gate ---------------------------


# --- Round 5: success only after every completion gate has durably passed ----------
#
# Fault injection for both gates, each with a passing, a failing and an
# unmeasurable tree. An interrupt (the worker's SIGTERM handler raises
# KeyboardInterrupt) lands during the measurement, between the measurement and
# its recording, or at the terminal write; the persisted record is what counts.

# An earlier run's passing measurement: it must never stand as this run's evidence.


# #9275 r7: one definition of the completion gates a record calls for, shared by
# the worker's terminal settle and the ask-* review wrapper.


# #10919: the driver brief is a second admission source, with the same replay boundary.
