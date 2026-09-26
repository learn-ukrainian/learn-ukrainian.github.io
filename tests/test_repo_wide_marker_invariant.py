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
runs the marker (``ci.yml`` adds a ``-m repo_wide`` invocation). The docs lane
runs it too, because several repo-wide tests read ``docs/``. This module is
itself ``repo_wide``.

Two checks keep the marker honest:

1. **The registry is the guarantee.** ``KNOWN_REPO_WIDE_MODULES`` and
   ``KNOWN_REPO_WIDE_FUNCTIONS`` are the authoritative list of whole-tree
   scanners. New scanners must be added there and marked; the registry checks
   fail if an entry disappears or loses its marker.
2. **The heuristic is a best-effort net.** It parses each test module's AST and
   flags test functions that walk a repository source tree (a repo-root path
   expression joined to ``.rglob()``/``.glob()``, ``os.walk``/``os.scandir``,
   ``git ls-files``/``ls-tree`` through ``subprocess``, or a known whole-tree
   linter) and then propagates to callers of a scanning helper. It only finds
   what it was taught to look for; the registry, not the heuristic, is the
   correctness anchor. A genuinely repository-rooted scanner that is *not*
   repo-wide (a content reader, a top-level launcher glob whose only possible
   changes already force the full tier, and so on) is listed in
   ``NOT_REPO_WIDE`` with a reason.

Marker detection is syntactic and per-function: a test counts as marked only
when its own ``@pytest.mark.repo_wide`` decorator, its class decorator, or a
module-level ``pytestmark`` containing ``pytest.mark.repo_wide`` applies to it.
A comment or docstring mentioning the word does not count, and decorator order
is irrelevant.
"""

from __future__ import annotations

import ast
import re
import textwrap
from collections.abc import Iterator
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
    "tests/test_hooks_executable.py",
    "tests/test_lint_fleet_roster.py",
    "tests/test_lint_prompts.py",
    "tests/test_lint_test_assertions.py",
    "tests/test_no_rewrite_contract.py",
    "tests/test_post_processor_mutation_invariant.py",
    "tests/test_public_tree_no_baked_host_run_root.py",
    "tests/test_pytest_plugins_not_test_modules.py",
    "tests/test_reads_content_marker_invariant.py",
    "tests/test_session_identity_env_isolation.py",
    "tests/test_session_state_retired.py",
    "tests/test_sparse_collection_guard.py",
    "tests/test_subprocess_timeout_guard.py",
    "tests/test_threshold_source_of_truth.py",
    "tests/test_work_privacy.py",
})

# Repo-wide tests that live in an otherwise generic module, so the marker is on
# the function (or its class) only.
KNOWN_REPO_WIDE_FUNCTIONS = (
    "tests/api/test_app_factory.py::test_db_access_patterns_have_the_step_two_allowlist",
    "tests/audit/test_post_build_review.py::test_prompt_versions_match_track_policy",
    "tests/build/test_fresh_style_cards.py::test_the_three_bands_and_nothing_else",
    "tests/projects/open_model_data/test_v4_per_slot_factory.py::test_no_test_in_this_suite_asserts_nonzero_completion_behind_a_stubbed_validator",
    "tests/test_a1_review_scores.py::TestA1ReviewScores.test_all_modules_have_review_files",
    "tests/test_a1_review_scores.py::TestA1ReviewScores.test_latest_scores_at_least_8",
    "tests/test_a1_review_scores.py::TestA1ReviewScores.test_review_files_contain_score_pattern",
    "tests/test_aggregate_findings.py::TestCollectFindings.test_with_real_a1_data",
    "tests/test_dashboards.py::TestApiEndpoints.test_endpoints_defined_in_router",
    "tests/test_landings_use_levellanding.py::test_arc_landings_are_generated_pages_the_router_mounts_from_frontmatter",
    "tests/test_launcher_contract.py::test_retired_names_are_absent_from_tracked_content",
    "tests/test_llm_reviewer_dispatch.py::test_no_production_entrypoint_constructs_bare_bakeoff_arm",
    "tests/test_manifest_io.py::test_lexicon_scripts_do_not_open_manifest_inplace",
    "tests/test_ohoiko_source_inventory_scope.py::test_ohoiko_abetka_inventory_covers_all_committed_key_words",
    "tests/test_prompt_template_render.py::test_phase_template_renders_without_unknown_tokens",
    "tests/test_schema_validation.py::TestPlanYamlSchemaCheck.test_a2_plans_match_module_schema",
    "tests/test_skill_instruction_routes.py::test_split_skill_references_are_reachable_from_their_entrypoint",
    "tests/test_skill_instruction_routes.py::test_task_scope_selector_keeps_canonical_sources_and_phase_gates_reachable",
)

# Escape hatch for a scanner the best-effort heuristic flags but that is not
# actually repo-wide. Each entry needs a concrete reason; the registry is kept
# fresh by ``test_not_repo_wide_entries_are_justified``.
NOT_REPO_WIDE = {
    "tests/test_ci_shard_partition.py::test_planned_shard_collects_build_tests_through_directory": (
        "Runs `git ls-files -- tests` and a pytest --collect-only over the planned "
        "allowlist, but every file it depends on (tests/conftest.py, scripts/ci/*, the "
        "duration snapshot) is on the shared-root denylist, so any change that could "
        "affect it already forces the full tier."
    ),
    "tests/test_fleet_comms_launcher_awareness.py::test_no_launcher_starts_an_acp_process_at_cold_start": (
        "Reads only scripts/lib/launcher_core.sh plus the repository root's start-*.sh. "
        "A root-level addition is never a test/script candidate, and scripts/lib changes "
        "have no stem-mapped test, so both force the full tier."
    ),
    "tests/test_launcher_contract.py::test_root_launcher_allowlist_is_exact": (
        "Globs only the repository root's start-*.sh; a root-level file change is not a "
        "test/script candidate and forces the full tier."
    ),
    "tests/test_start_cursor_launcher.py::test_cursor_seat_enumerated_in_launcher_core_and_public_estate": (
        "Globs only the repository root's start-*-driver.sh; a root-level file change is "
        "not a test/script candidate and forces the full tier."
    ),
    "tests/test_landings_use_levellanding.py::test_content_collection_loads_track_index_mdx_files": (
        "Reads the site/src/content/docs content tree (DOCS_ROOT) as a content reader, "
        "covered by the reads_content marker and the content lane, not a repo code-tree scan."
    ),
    "tests/test_landings_use_levellanding.py::test_track_landing_uses_levellanding_contract": (
        "Reads the site/src/content/docs content tree (DOCS_ROOT) as a content reader, "
        "covered by the reads_content marker and the content lane, not a repo code-tree scan."
    ),
    "tests/packaging/test_systemd_templates.py::test_systemd_templates_have_no_host_facts": (
        "Reads packaging/systemd; packaging/ is not a test or script candidate, so any "
        "change to a systemd template already forces the full tier."
    ),
    "tests/projects/open_model_data/test_audit_dataset_acceptance.py::test_reproduces_v05_grammar_valency_findings": (
        "Scans data/projects/open_model_data; data/ is not a test or script candidate, so "
        "any change already forces the full tier."
    ),
    "tests/projects/open_model_data/test_audit_dataset_acceptance.py::test_reproduces_v04b_middle_ukrainian_findings": (
        "Scans data/projects/open_model_data; data/ is not a test or script candidate, so "
        "any change already forces the full tier."
    ),
    "tests/projects/open_model_data/test_audit_dataset_acceptance.py::test_reproduces_v04a_kyivan_rus_findings": (
        "Scans data/projects/open_model_data; data/ is not a test or script candidate, so "
        "any change already forces the full tier."
    ),
    "tests/projects/open_model_data/test_v6_mine_grammar_valency.py::test_ua_gec_sanitized_error_spans_in_query": (
        "Scans data/projects/open_model_data; data/ is not a test or script candidate, so "
        "any change already forces the full tier."
    ),
    "tests/projects/open_model_data/test_v6_mine_grammar_valency.py::test_shards_zero_double_terminal_punctuation": (
        "Scans data/projects/open_model_data; data/ is not a test or script candidate, so "
        "any change already forces the full tier."
    ),
    "tests/projects/open_model_data/test_v6_mine_grammar_valency.py::test_control_records_verbatim_fidelity": (
        "Scans data/projects/open_model_data; data/ is not a test or script candidate, so "
        "any change already forces the full tier."
    ),
    "tests/test_ci_pr_triggers.py::test_no_workflow_reruns_ci_on_a_label": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change "
        "already forces the full tier."
    ),
    "tests/test_ci_pr_triggers.py::test_exactly_one_ci_gate_job_across_workflows": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change "
        "already forces the full tier."
    ),
    "tests/test_dashboards.py::TestDashboardInventory.test_expected_dashboards_exist": (
        "Scans dashboards/; dashboards/ is not a test or script candidate, so any change "
        "already forces the full tier."
    ),
    "tests/test_dashboards.py::TestApiEndpoints.test_fetch_calls_in_html": (
        "Scans dashboards/; dashboards/ is not a test or script candidate, so any change "
        "already forces the full tier."
    ),
    "tests/test_layerb_candidates.py::test_ci_differential_replays_all_unit_fixtures_at_pinned_base_values": (
        "Scans tests/fixtures/qg_bakeoff; fixture files are not test modules, so any change "
        "already forces the full tier."
    ),
    "tests/test_monitor_route_contracts.py::test_every_dashboard_html_file_has_page_contract": (
        "Scans dashboards/; dashboards/ is not a test or script candidate, so any change "
        "already forces the full tier."
    ),
    "tests/test_monitor_ui_contracts.py::test_all_playground_pages_use_single_monitor_shell": (
        "Scans dashboards/*.html; dashboards/ changes already force the full tier, and the "
        "module also carries reads_content."
    ),
    "tests/test_ohoiko_source_inventory_scope.py::test_ohoiko_abetka_inventory_has_review_decisions_for_all_rows": (
        "Scans data/lexicon/source-inventory-review-decisions; data/ changes already force "
        "the full tier, and the module also carries reads_content."
    ),
    "tests/test_open_model_phase3_historical_protection_channels.py::test_absent_oes_and_church_slavonic_artifacts_remain_blocked": (
        "Scans data/projects/open_model_data for named artifacts (metadata-only existence "
        "check, not a content read); data/ is not a test or script candidate, so any change "
        "already forces the full tier."
    ),
    "tests/test_paths_filter_fail_open.py::test_workflows_only_consume_valid_action_outputs": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change "
        "already forces the full tier."
    ),
    "tests/test_site_links.py::TestMdxFiles.test_no_old_module_nn_files": (
        "Reads the site/src/content/docs content tree as a content reader; the module "
        "carries reads_content and the content lane runs it."
    ),
    "tests/test_ulif_dictua.py::test_fixture_cells_keep_each_attested_preposition_out_of_the_form": (
        "Scans tests/fixtures/ulif_dictua; fixture files are not test modules, so any change "
        "already forces the full tier."
    ),
    "tests/build/test_fresh_writer.py::test_nothing_typed_no_cyrillic_in_engine_code": (
        "Scans the writer engine under scripts/build/fresh; scripts/build/ is on the "
        "shared-root denylist, so any change already forces the full tier."
    ),
    "tests/build/test_fresh_writer.py::test_r11_forbidden_paths_grep": (
        "Scans the writer engine under scripts/build/fresh; scripts/build/ is on the "
        "shared-root denylist, so any change already forces the full tier."
    ),
    "tests/test_ci_attribution.py::test_run_nodeids_kills_a_wedged_test_and_names_it_on_stderr": (
        "Uses a repository-rooted scratch path only to create and then delete a "
        "self-created temp dir (the `rglob` is cleanup); it scans no repository "
        "invariant tree, so no marker is needed."
    ),
    "tests/test_dispatch_xdist_cap.py::test_ci_workflows_do_not_set_the_dispatch_marker": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change "
        "already forces the full tier."
    ),
    "tests/test_site_links.py::TestInternalLinks.test_no_broken_cross_references": (
        "Reads the site/src/content/docs content tree through a per-track variable; that "
        "tree is content-class, so the content lane runs the module via reads_content."
    ),
    "tests/test_site_links.py::TestMdxFiles.test_all_mdx_have_frontmatter": (
        "Reads the site/src/content/docs content tree through a per-track variable; that "
        "tree is content-class, so the content lane runs the module via reads_content."
    ),
    "tests/test_site_links.py::TestMdxFiles.test_all_mdx_have_title": (
        "Reads the site/src/content/docs content tree through a per-track variable; that "
        "tree is content-class, so the content lane runs the module via reads_content."
    ),
    "tests/test_site_links.py::TestModuleCounts.test_minimum_module_count": (
        "Reads the site/src/content/docs content tree through a per-track variable; that "
        "tree is content-class, so the content lane runs the module via reads_content."
    ),
    "tests/test_source_inventory_intake.py::test_committed_source_inventory_files_are_valid": (
        "Scans data/lexicon/source-inventory; data/ is not a test or script candidate, so "
        "any change already forces the full tier."
    ),
    "tests/test_workflow_head_concurrency.py::test_merge_group_workflows_do_not_unconditionally_cancel": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change "
        "already forces the full tier."
    ),
}

# Repository-root path constants. A walk rooted at one of these (or a join into
# tests/scripts/agents_extensions) is repo-wide, not a temp fixture. The
# ``*_ROOT`` suffix and ``Path(__file__).parents[n]`` cover the inline forms.
_REPO_ROOT_CONSTANTS = frozenset({
    "REPO",
    "ROOT",
    "PROJECT_ROOT",
    "PROJECT_DIR",
    "REPO_ROOT",
    "_REPO_ROOT",
    "TESTS_ROOT",
    "_TESTS_ROOT",
    "SCRIPTS_ROOT",
    "_SCRIPTS_ROOT",
    "SCRIPTS_DIR",
    "_API_ROOT",
    "DOCS_ROOT",
    "_DOCS_ROOT",
    "SRC_ROOT",
    "SOURCE_ROOT",
    "CURRICULUM_ROOT",
    "CURRICULUM_DIR",
})

# Whole-tree linter helpers: calling one is a repo scan even without a glob.
_KNOWN_SCANNER_CALLS = frozenset({
    "find_stale_pinned_assertions",
    "scan_scripts",
    "timeout_less_calls",
    "timeout_less_calls_from_source",
    "_inplace_manifest_writers",
    "production_sites",
    "_iter_surface_python_files",
    "lint_fleet_roster",
    "lint_agent_skills",
    "lint_model_catalog",
})

_SUBPROCESS_CALLS = frozenset({
    "subprocess.run",
    "subprocess.check_output",
    "subprocess.check_call",
    "subprocess.call",
    "subprocess.Popen",
})

_GIT_TREE_TOKENS = frozenset({"ls-files", "ls-tree"})

_TMP_RECEIVER_TOKENS = ("tmp_path", "tmpdir")

_WALK_ATTRS = frozenset({"glob", "rglob", "iterdir"})


def _test_module_paths() -> list[Path]:
    return sorted(_TESTS_ROOT.rglob("test_*.py"))


def _parse(module: Path) -> ast.Module:
    return ast.parse(module.read_text(encoding="utf-8"), filename=str(module))


def _call_name(call: ast.Call) -> str:
    func = call.func
    parts: list[str] = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    return ".".join(reversed(parts))


def _is_repo_root_expr(source: str, repo_root_names: frozenset[str] = frozenset()) -> bool:
    """True when a path expression is rooted at the repository, not a temp dir.

    ``repo_root_names`` carries module-level names that were assigned a
    repository-rooted expression (transitively), e.g. ``SESSION = ROOT / "docs"``.
    """
    if any(token in source for token in _TMP_RECEIVER_TOKENS):
        return False
    if "__file__" in source and ("parents" in source or re.search(r"\.parent\b", source)):
        return True
    return any(
        token in _REPO_ROOT_CONSTANTS or token.endswith("_ROOT") or token in repo_root_names
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", source)
    )


def _module_repo_root_names(tree: ast.Module) -> frozenset[str]:
    """Module-level names assigned a repository-rooted expression, transitively."""
    assignments = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    ]
    names: set[str] = set()
    changed = True
    while changed:
        changed = False
        for statement in assignments:
            target = statement.targets[0].id
            if target in names:
                continue
            if _is_repo_root_expr(ast.unparse(statement.value), frozenset(names)):
                names.add(target)
                changed = True
    return frozenset(names)


def _iter_scope_statements(statements: list[ast.stmt]) -> Iterator[ast.stmt]:
    """Statements of a scope, descending into ``if``/``with``/``for``/``try`` blocks.

    Nested function/class definitions open a new scope, so their bodies are not
    part of the enclosing one and are not walked.
    """
    for statement in statements:
        yield statement
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for field in ("body", "orelse", "finalbody"):
            nested = getattr(statement, field, None)
            if nested:
                yield from _iter_scope_statements(nested)
        for handler in getattr(statement, "handlers", []):
            yield from _iter_scope_statements(handler.body)


def _scope_bindings(statements: list[ast.stmt]) -> dict[str, ast.expr]:
    """One-level ``name = value`` bindings in a scope body.

    Nested ``if``/``with``/``for``/``try`` blocks count: a ``cmd = [...]``
    guarded by a condition is still a binding for detection purposes.
    """
    bindings: dict[str, ast.expr] = {}
    for statement in _iter_scope_statements(statements):
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            bindings.setdefault(statement.targets[0].id, statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
        ):
            bindings.setdefault(statement.target.id, statement.value)
    return bindings


def _bindings_repo_root_names(
    bindings: dict[str, ast.expr],
    repo_root_names: frozenset[str] = frozenset(),
) -> frozenset[str]:
    """Bound names whose value is a repository-rooted expression, transitively.

    A function-local ``api_dir = ROOT / "scripts" / "api"`` roots any walk off
    ``api_dir`` just as a module-level constant would.
    """
    names: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, value in bindings.items():
            if name in names:
                continue
            if _is_repo_root_expr(ast.unparse(value), frozenset(repo_root_names | names)):
                names.add(name)
                changed = True
    return frozenset(names)


def _has_git_tree_token(sequence: ast.List | ast.Tuple) -> bool:
    values = {
        element.value
        for element in sequence.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    }
    return bool(values & _GIT_TREE_TOKENS)


def _subprocess_git_tree_scan(call: ast.Call, bindings: dict[str, ast.expr]) -> bool:
    if _call_name(call) not in _SUBPROCESS_CALLS:
        return False
    for node in ast.walk(call):
        if isinstance(node, (ast.List, ast.Tuple)):
            if _has_git_tree_token(node):
                return True
        elif isinstance(node, ast.Name):
            value = bindings.get(node.id)
            if isinstance(value, (ast.List, ast.Tuple)) and _has_git_tree_token(value):
                return True
    return False


def _direct_scan_sites(
    node: ast.AST,
    repo_root_names: frozenset[str] = frozenset(),
    bindings: dict[str, ast.expr] | None = None,
) -> list[str]:
    """Repository-tree scans performed anywhere inside ``node``."""
    bindings = bindings or {}
    sites: list[str] = []
    for call in (child for child in ast.walk(node) if isinstance(child, ast.Call)):
        name = _call_name(call)
        if isinstance(call.func, ast.Attribute) and call.func.attr in _WALK_ATTRS:
            receiver = ast.unparse(call.func.value)
            if _is_repo_root_expr(receiver, repo_root_names):
                sites.append(f"{receiver}.{call.func.attr}")
        elif name in {"os.walk", "os.scandir"} and call.args:
            argument = ast.unparse(call.args[0])
            if _is_repo_root_expr(argument, repo_root_names):
                sites.append(f"{name}({argument})")
        elif name.rsplit(".", 1)[-1] in _KNOWN_SCANNER_CALLS:
            sites.append(f"scanner:{name}")
        elif _subprocess_git_tree_scan(call, bindings):
            sites.append("subprocess git tree scan")
    return sorted(set(sites))


def _is_repo_wide_marker(node: ast.AST) -> bool:
    """True for a real ``pytest.mark.repo_wide`` attribute chain."""
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "repo_wide"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "pytest"
    )


def _marked_by_repo_wide(decorators: list[ast.expr]) -> bool:
    return any(any(_is_repo_wide_marker(node) for node in ast.walk(decorator)) for decorator in decorators)


def _module_marked(tree: ast.Module) -> bool:
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in statement.targets):
            continue
        if _marked_by_repo_wide([statement.value]):
            return True
    return False


def _top_level_functions(tree: ast.Module) -> dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.ClassDef | None]]:
    found: dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.ClassDef | None]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[f"{node.name}.{item.name}"] = (item, node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[node.name] = (node, None)
    return found


def _function_marked(tree: ast.Module, function: str) -> bool:
    entry = _top_level_functions(tree).get(function)
    if entry is None:
        return False
    node, owner = entry
    return _marked_by_repo_wide(node.decorator_list) or (
        owner is not None and _marked_by_repo_wide(owner.decorator_list)
    )


def _implicated_test_functions(tree: ast.Module) -> dict[str, list[str]]:
    """Test functions that scan a repo tree directly or via a scanning helper."""
    functions = _top_level_functions(tree)
    repo_root_names = _module_repo_root_names(tree)
    module_bindings = _scope_bindings(tree.body)
    direct: dict[str, list[str]] = {}
    for name, (node, _owner) in functions.items():
        bindings = {**module_bindings, **_scope_bindings(node.body)}
        root_names = repo_root_names | _bindings_repo_root_names(bindings, repo_root_names)
        if sites := _direct_scan_sites(node, root_names, bindings):
            direct[name] = sites

    def calls(node: ast.AST) -> set[str]:
        return {_call_name(call).rsplit(".", 1)[-1] for call in ast.walk(node) if isinstance(call, ast.Call)}

    # Propagate through every function: a test that (transitively) calls a
    # scanning helper is itself a scanner, even when the chain passes through
    # helpers that do not scan on their own. Method keys are ``Class.method``, so
    # compare on the bare callable name.
    implicated_all = set(direct)
    changed = True
    while changed:
        changed = False
        bare = {name.rsplit(".", 1)[-1] for name in implicated_all}
        for name, (node, _owner) in functions.items():
            if name not in implicated_all and calls(node) & bare:
                implicated_all.add(name)
                changed = True

    return {
        name: direct.get(name, ["via scanning helper"])
        for name in implicated_all
        if name.rsplit(".", 1)[-1].startswith("test_")
    }


def _module_level_scan_sites(tree: ast.Module) -> list[str]:
    statements = [
        statement
        for statement in tree.body
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    bindings = _scope_bindings(statements)
    module_roots = _module_repo_root_names(tree)
    root_names = module_roots | _bindings_repo_root_names(bindings, module_roots)
    return _direct_scan_sites(
        ast.Module(body=statements, type_ignores=[]),
        root_names,
        bindings,
    )


def test_repo_tree_scanners_carry_the_marker() -> None:
    """A test that scans a repo tree or runs a repo lint must be ``repo_wide``.

    Per-function granularity: every implicated test is checked on its own, so a
    module with two scanners and one marker fails.
    """
    missing: list[str] = []
    for module in _test_module_paths():
        relative = module.relative_to(_REPO_ROOT).as_posix()
        tree = _parse(module)
        module_marked = _module_marked(tree)
        for function, sites in _implicated_test_functions(tree).items():
            node_id = f"{relative}::{function}"
            if node_id in NOT_REPO_WIDE:
                continue
            if module_marked or _function_marked(tree, function):
                continue
            missing.append(f"{node_id}  ({', '.join(sites)})")
        if not module_marked and relative not in NOT_REPO_WIDE and _module_level_scan_sites(tree):
            missing.append(f"{relative}  (module-level repo tree scan)")
    assert not missing, (
        "These test functions scan repository trees or run a repo-wide linter but "
        "do not carry the repo_wide marker, so an import-selected CI tier can "
        "never run them (#8707). Add `@pytest.mark.repo_wide` (or a module "
        "`pytestmark`), or add a reasoned NOT_REPO_WIDE entry:\n" + "\n".join(missing)
    )


def test_known_repo_wide_modules_carry_the_marker() -> None:
    missing = [module for module in sorted(KNOWN_REPO_WIDE_MODULES) if not (_REPO_ROOT / module).is_file()]
    assert not missing, f"known repo-wide modules no longer exist: {missing}"
    unmarked = [
        module
        for module in sorted(KNOWN_REPO_WIDE_MODULES)
        if not _module_marked(_parse(_REPO_ROOT / module))
    ]
    assert not unmarked, (
        "known repo-wide modules lost their module-level repo_wide marker:\n" + "\n".join(unmarked)
    )


def test_known_repo_wide_functions_carry_the_marker() -> None:
    missing: list[str] = []
    unmarked: list[str] = []
    for node in KNOWN_REPO_WIDE_FUNCTIONS:
        module_rel, _, function = node.partition("::")
        module = _REPO_ROOT / module_rel
        if not module.is_file():
            missing.append(module_rel)
            continue
        if not _function_marked(_parse(module), function):
            unmarked.append(node)
    assert not missing, f"known repo-wide modules no longer exist: {missing}"
    assert not unmarked, (
        "known repo-wide tests lost their per-function repo_wide decorator "
        "(decorator order and comments must not matter):\n" + "\n".join(unmarked)
    )


def test_not_repo_wide_entries_are_justified() -> None:
    """The escape hatch stays honest: real node, real reason, still a scanner."""
    known = set(KNOWN_REPO_WIDE_MODULES) | set(KNOWN_REPO_WIDE_FUNCTIONS)
    for node_id, reason in NOT_REPO_WIDE.items():
        assert reason.strip(), f"{node_id}: a NOT_REPO_WIDE entry needs a reason"
        assert node_id not in known, f"{node_id}: cannot be both repo-wide and NOT_REPO_WIDE"
        module_rel, _, function = node_id.partition("::")
        module = _REPO_ROOT / module_rel
        assert module.is_file(), f"{node_id}: module {module_rel} no longer exists"
        tree = _parse(module)
        if function:
            assert function in _top_level_functions(tree), f"{node_id}: function no longer exists"
            assert function in _implicated_test_functions(tree), (
                f"{node_id}: no longer looks like a repo scanner; remove the stale entry"
            )
        else:
            assert _module_level_scan_sites(tree), (
                f"{node_id}: no longer has a module-level repo scan; remove the stale entry"
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


def test_docs_lane_also_runs_repo_wide() -> None:
    """Docs-only PRs only get the docs lane, and repo-wide scanners read docs/."""
    ci_text = _CI.read_text(encoding="utf-8")
    docs_blocks = re.findall(
        r'if \[ "\$DOCS_ONLY" = "true" \]; then\n(.*?)\n\s*exit 0',
        ci_text,
        re.DOTALL,
    )
    assert docs_blocks, "ci.yml has no docs-only pytest block"
    assert any(re.search(r"-m [^\n]*repo_wide", block) for block in docs_blocks), (
        "the docs lane must also run `-m repo_wide`: repo-wide tests read docs/ (#8707)"
    )


def _synthetic(source: str) -> ast.Module:
    return ast.parse(textwrap.dedent(source))


def test_marker_detection_requires_the_real_decorator() -> None:
    """A bare ``repo_wide`` mention in a comment or docstring is not a marker."""
    tree = _synthetic(
        '''
        import pytest

        # repo_wide
        """repo_wide is a marker."""

        def test_mention_only():
            assert "repo_wide" == "repo_wide"
        '''
    )
    assert not _module_marked(tree)
    assert not _function_marked(tree, "test_mention_only")


def test_marker_detection_accepts_module_function_and_class_forms() -> None:
    module_form = _synthetic(
        """
        import pytest

        pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

        def test_x():
            ...
        """
    )
    assert _module_marked(module_form)

    # Decorator order must not matter (the marker is not first).
    function_form = _synthetic(
        """
        import pytest

        @pytest.mark.other
        @pytest.mark.repo_wide
        def test_x():
            ...
        """
    )
    assert _function_marked(function_form, "test_x")

    class_form = _synthetic(
        """
        import pytest

        @pytest.mark.repo_wide
        class TestSuite:
            def test_x(self):
                ...
        """
    )
    assert _function_marked(class_form, "TestSuite.test_x")

    unrelated = _synthetic(
        """
        import pytest

        @some_other.repo_wide
        def test_x():
            ...
        """
    )
    assert not _function_marked(unrelated, "test_x")


def test_marker_detection_is_per_function() -> None:
    """Two scanners in one module, one marker: the unmarked one must stand out."""
    tree = _synthetic(
        """
        import pytest

        @pytest.mark.repo_wide
        def test_marked():
            (REPO / "tests").rglob("*.py")

        def test_unmarked():
            (REPO / "scripts").rglob("*.py")
        """
    )
    assert set(_implicated_test_functions(tree)) == {"test_marked", "test_unmarked"}
    assert not _module_marked(tree)
    assert _function_marked(tree, "test_marked")
    assert not _function_marked(tree, "test_unmarked")


def test_heuristic_roots_tmp_paths_and_git_tree_scans() -> None:
    """Temp-path receivers are skipped; repo-root and git-tree scans are flagged."""
    tmp_receiver = _synthetic(
        """
        def test_tmp(tmp_path):
            (tmp_path / "x").rglob("*.py")
        """
    )
    assert _implicated_test_functions(tmp_receiver) == {}

    file_relative = _synthetic(
        """
        from pathlib import Path

        def test_scan():
            Path(__file__).resolve().parents[1].rglob("*.py")
        """
    )
    assert "test_scan" in _implicated_test_functions(file_relative)

    git_tree_scan = _synthetic(
        """
        import subprocess

        def test_scan():
            subprocess.run(["git", "ls-files"], capture_output=True, check=True)
        """
    )
    assert "test_scan" in _implicated_test_functions(git_tree_scan)


def test_heuristic_follows_named_argv_and_derived_repo_root_constants() -> None:
    """`subprocess.run(cmd)` and `SESSION = ROOT / ...` are scanners too (#8707 review)."""
    named_argv = _synthetic(
        """
        import subprocess
        from pathlib import Path

        REPO_ROOT = Path(__file__).resolve().parents[1]

        def test_scan():
            cmd = ["git", "ls-files", "-s", "agents_extensions/shared/hooks/"]
            subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, check=True)
        """
    )
    assert "test_scan" in _implicated_test_functions(named_argv)

    derived_root = _synthetic(
        """
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[1]
        SESSION = ROOT / "docs" / "session-state"

        def test_scan():
            SESSION.iterdir()
        """
    )
    assert "test_scan" in _implicated_test_functions(derived_root)


def test_heuristic_roots_function_local_and_nested_bindings() -> None:
    """A function-local repo-root binding and an `if`-guarded argv are scanners (#8707 review)."""
    local_root = _synthetic(
        """
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[1]

        def test_scan():
            api_dir = ROOT / "scripts" / "api"
            for path in api_dir.glob("*.py"):
                path.read_text()
        """
    )
    assert "test_scan" in _implicated_test_functions(local_root)

    guarded_argv = _synthetic(
        """
        import subprocess

        def test_scan(flag):
            if flag:
                cmd = ["git", "ls-files"]
            with open("/dev/null") as _handle:
                other = ["git", "ls-tree", "-r", "HEAD"]
            subprocess.run(cmd, capture_output=True, check=True)
            subprocess.run(other, capture_output=True, check=True)
        """
    )
    assert "test_scan" in _implicated_test_functions(guarded_argv)


def test_method_keys_do_not_mask_same_named_methods() -> None:
    """Two classes with the same method name stay distinct (``Class.method`` keys)."""
    tree = _synthetic(
        """
        import pytest

        class TestOne:
            @pytest.mark.repo_wide
            def test_scan(self):
                (REPO / "tests").rglob("*.py")

        class TestTwo:
            def test_scan(self):
                (REPO / "scripts").rglob("*.py")
        """
    )
    assert set(_implicated_test_functions(tree)) == {"TestOne.test_scan", "TestTwo.test_scan"}
    assert _function_marked(tree, "TestOne.test_scan")
    assert not _function_marked(tree, "TestTwo.test_scan")
