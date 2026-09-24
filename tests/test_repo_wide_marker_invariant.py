"""``repo_wide`` marker invariant (#8707).

The selected CI tier picks test files by import-graph candidates: the Changes
job maps a changed ``scripts/foo.py`` to ``tests/**/test_foo*.py`` and a changed
``tests/test_x.py`` to itself. A test that scans the repository's own trees has
no such import link, so selection can never pick it. That is how PR #8692
merged green on the selected tier and then turned ``main`` red:
``tests/test_lint_test_assertions.py::test_repo_test_suite_is_clean`` scans all
of ``tests/`` for hard-coded epic assertions and was never selected for a
``tests/orchestration/test_thread_handoff.py`` change.

Every test that enforces a repository-wide invariant by scanning files it does
not import must therefore carry ``repo_wide``, and the selected tier always
runs the marker (`ci.yml` adds a ``-m repo_wide`` invocation). This module is
itself ``repo_wide``.

Two checks keep the marker honest:

1. An explicit registry of the known repo-wide modules/functions. New
   whole-tree scanners must be added here (and marked).
2. A documented heuristic over each test module's source: a module that walks
   a repository source tree (a repo-root constant receiver joined to
   ``.rglob()``/``.glob()``) or calls a known whole-tree linter must carry the
   marker. The heuristic is deliberately conservative — it targets scanners
   rooted at the repository (``_REPO_ROOT``, ``REPO_ROOT``, ``PROJECT_ROOT``,
   ``_TESTS_ROOT``, ``_SCRIPTS_ROOT``, ``_API_ROOT``, ``SCRIPTS_DIR``, ...),
   not temp-path fixtures.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_ROOT = _REPO_ROOT / "tests"
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Whole-tree scanners over tests/, scripts/, agents_extensions/ (or a stable
# subtree of them) that carry the marker at module scope.
KNOWN_REPO_WIDE_MODULES = frozenset({
    "tests/ai_agent_bridge/test_module_identity.py",
    "tests/api/test_api_subprocess_timeout.py",
    "tests/api/test_import_pinning.py",
    "tests/orchestration/test_thread_restart_e2e.py",
    "tests/orchestration/test_worktree_removal_invariant.py",
    "tests/test_agent_fleet_tooling_guardrails.py",
    "tests/test_ask_opencode.py",
    "tests/test_curriculum_upgrade_no_host_run_root.py",
    "tests/test_cyrillic_roundtrip_invariant.py",
    "tests/test_fleet_routing_open_model_data_import_guard.py",
    "tests/test_lint_fleet_roster.py",
    "tests/test_lint_prompts.py",
    "tests/test_lint_test_assertions.py",
    "tests/test_no_rewrite_contract.py",
    "tests/test_post_processor_mutation_invariant.py",
    "tests/test_public_tree_no_baked_host_run_root.py",
    "tests/test_reads_content_marker_invariant.py",
    "tests/test_sparse_collection_guard.py",
    "tests/test_subprocess_timeout_guard.py",
    "tests/test_threshold_source_of_truth.py",
    "tests/test_work_privacy.py",
})

# Repo-wide tests that live in an otherwise generic module, so the marker is on
# the function only.
KNOWN_REPO_WIDE_FUNCTIONS = (
    "tests/api/test_app_factory.py::test_db_access_patterns_have_the_step_two_allowlist",
    "tests/test_llm_reviewer_dispatch.py::test_no_production_entrypoint_constructs_bare_bakeoff_arm",
    "tests/test_manifest_io.py::test_lexicon_scripts_do_not_open_manifest_inplace",
)

# Repository-root path constants. A walk rooted at one of these (or a join
# into tests/scripts/agents_extensions) is repo-wide, not a temp fixture.
_REPO_ROOT_CONSTANTS = (
    "_REPO_ROOT",
    "REPO_ROOT",
    "PROJECT_ROOT",
    "_TESTS_ROOT",
    "TESTS_ROOT",
    "_SCRIPTS_ROOT",
    "SCRIPTS_ROOT",
    "SCRIPTS_DIR",
    "_API_ROOT",
)

_WALK_RE = re.compile(r"\.(?:rglob|glob)\(|os\.walk\(|iglob\(")
_RECEIVER_RE = re.compile(r"([\w\.\[\]\"' /\(\)\-]{1,80})\.(?:rglob|glob)\(")
_SCANNER_RE = re.compile(
    r"\b(?:find_stale_pinned_assertions|scan_scripts|timeout_less_calls|"
    r"timeout_less_calls_from_source|_inplace_manifest_writers|production_sites|"
    r"_iter_surface_python_files|lint_fleet_roster|lint_agent_skills|"
    r"lint_model_catalog)\s*\("
)
_TMP_RE = re.compile(r"tmp_path|tmpdir")
_MARKER_RE = re.compile(r"repo_wide")


def _test_module_paths() -> list[Path]:
    return sorted(_TESTS_ROOT.rglob("test_*.py"))


def _repo_wide_scanner_modules() -> list[str]:
    """Documented heuristic: modules scanning a repository source tree."""
    flagged: list[str] = []
    for module in _test_module_paths():
        text = module.read_text(encoding="utf-8")
        for line in text.splitlines():
            if _TMP_RE.search(line):
                continue
            if _SCANNER_RE.search(line):
                flagged.append(module.relative_to(_REPO_ROOT).as_posix())
                break
            if _WALK_RE.search(line):
                match = _RECEIVER_RE.search(line)
                receiver = match.group(1) if match else ""
                if any(constant in receiver for constant in _REPO_ROOT_CONSTANTS):
                    flagged.append(module.relative_to(_REPO_ROOT).as_posix())
                    break
    return sorted(set(flagged))


def test_repo_tree_scanners_carry_the_marker() -> None:
    """A module that scans a repo tree or runs a repo lint must be ``repo_wide``."""
    missing = [
        module
        for module in _repo_wide_scanner_modules()
        if not _MARKER_RE.search((_REPO_ROOT / module).read_text(encoding="utf-8"))
    ]
    assert not missing, (
        "These test modules scan repository trees or run a repo-wide linter but "
        "do not carry the repo_wide marker, so an import-selected CI tier can "
        "never run them (#8707). Add `pytestmark = pytest.mark.repo_wide` "
        "(or a per-test `@pytest.mark.repo_wide`):\n" + "\n".join(missing)
    )


def test_known_repo_wide_modules_carry_the_marker() -> None:
    missing = [module for module in sorted(KNOWN_REPO_WIDE_MODULES) if not (_REPO_ROOT / module).is_file()]
    assert not missing, f"known repo-wide modules no longer exist: {missing}"
    unmarked = [
        module
        for module in sorted(KNOWN_REPO_WIDE_MODULES)
        if not _MARKER_RE.search((_REPO_ROOT / module).read_text(encoding="utf-8"))
    ]
    assert not unmarked, "known repo-wide modules lost their repo_wide marker:\n" + "\n".join(unmarked)


def test_known_repo_wide_functions_carry_the_marker() -> None:
    unmarked: list[str] = []
    for node in KNOWN_REPO_WIDE_FUNCTIONS:
        module_rel, _, function = node.partition("::")
        module = _REPO_ROOT / module_rel
        assert module.is_file(), f"known repo-wide module no longer exists: {module_rel}"
        text = module.read_text(encoding="utf-8")
        match = re.search(
            rf"(?ms)^@[^\n]*repo_wide[^\n]*\n(?:@[^\n]*\n)*def {re.escape(function)}\b",
            text,
        )
        if match is None:
            unmarked.append(node)
    assert not unmarked, (
        "known repo-wide tests lost their per-function repo_wide decorator:\n" + "\n".join(unmarked)
    )


def test_selected_tier_command_always_runs_repo_wide() -> None:
    """The selected tier must include a ``-m repo_wide`` pytest invocation."""
    ci_text = _CI.read_text(encoding="utf-8")
    selected_blocks = re.findall(
        r'if \[ "\$PYTEST_MODE" = "selected" \]; then\n(.*?)\n\s*fi',
        ci_text,
        re.DOTALL,
    )
    assert selected_blocks, "ci.yml has no selected-mode pytest block"
    assert any(re.search(r"-m [^\n]*repo_wide", block) for block in selected_blocks), (
        "the selected tier must run `-m repo_wide` so repo-wide tests always run (#8707)"
    )
