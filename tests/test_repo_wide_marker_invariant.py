"""``repo_wide`` marker invariant (#8707).

A test that scans the repository's own trees (rather than importing the code
it checks) must carry ``repo_wide``. The marker names the repository
invariants so a worker can run them alone before pushing
(``pytest -m repo_wide``; the dispatch sparse checkout keeps that command
working, see ``scripts/delegate.py``). CI runs every test, marked or not.
PR #8692 is why it exists: ``tests/test_lint_test_assertions.py`` scans all of
``tests/`` for hard-coded epic assertions and had no import link to the change
that broke it. This module is itself ``repo_wide``.

Two checks keep the marker honest:

1. **The registry is the guarantee.** ``KNOWN_REPO_WIDE_MODULES`` and
   ``KNOWN_REPO_WIDE_FUNCTIONS`` are the authoritative list of whole-tree
   scanners. New scanners must be added there and marked; the registry checks
   fail if an entry disappears or loses its marker, and the completeness check
   fails if a marked test has no registry row (#9434), so deleting a row cannot
   pass silently. These checks read the marks pytest applies, from a
   collection-only child run. They collect only the test files a source
   prefilter says can carry the mark; that is an early warning, and
   ``_candidate_test_files`` names the shapes it misses.
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

The heuristic's marker detection is syntactic and per-function: a scanner
counts as marked only when its own ``@pytest.mark.repo_wide`` decorator, its
class decorator, or a module-level ``pytestmark`` containing
``pytest.mark.repo_wide`` applies to it. A comment or docstring mentioning the
word does not count, and decorator order is irrelevant.
"""

from __future__ import annotations

import ast
import fcntl
import itertools
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import textwrap
import tomllib
from collections.abc import Collection, Iterator
from functools import lru_cache
from pathlib import Path

import pytest

from scripts.ci.pytest_dispatch_cap import DISPATCH_TASK_ENV, FULL_SUITE_BUSY, LOCK_ENV
from tests.process_group_child import run_in_process_group

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_ROOT = _REPO_ROOT / "tests"

# Whole-tree scanners over tests/, scripts/, agents_extensions/ (or a stable
# subtree of them) that carry the marker at module scope.
KNOWN_REPO_WIDE_MODULES = frozenset(
    {
        "tests/ai_agent_bridge/test_module_identity.py",
        "tests/hygiene/test_tracked_symlink_targets.py",
        "tests/orchestration/test_thread_restart_e2e.py",
        "tests/orchestration/test_worktree_removal_invariant.py",
        "tests/test_agent_fleet_tooling_guardrails.py",
        "tests/test_ask_opencode.py",
        "tests/test_curriculum_upgrade_no_host_run_root.py",
        "tests/test_cyrillic_roundtrip_invariant.py",
        "tests/test_dispatch_checkout_size.py",
        "tests/test_docs_catalogue.py",
        "tests/test_docs_catalogue_coverage.py",
        "tests/test_fleet_routing_open_model_data_import_guard.py",
        "tests/test_frontend_denominator_invariant.py",
        "tests/test_hooks_executable.py",
        "tests/test_issue_template_acceptance_criteria.py",
        "tests/test_lesson_atlas_link_census.py",
        "tests/test_lint_fleet_roster.py",
        "tests/test_lint_prompts.py",
        "tests/test_no_rewrite_contract.py",
        "tests/test_post_processor_mutation_invariant.py",
        "tests/test_public_tree_no_baked_host_run_root.py",
        "tests/test_repo_wide_marker_invariant.py",
        "tests/test_session_identity_env_isolation.py",
        "tests/test_source_ingest_entrypoints.py",
        "tests/test_subprocess_timeout_guard.py",
        "tests/test_sum11_source_guard.py",
        "tests/test_threshold_source_of_truth.py",
        "tests/test_work_privacy.py",
        "tests/validate/test_word_card_examples.py",
    }
)

# Repo-wide tests that live in an otherwise generic module, so the marker is on
# the function (or its class) only.
KNOWN_REPO_WIDE_FUNCTIONS = (
    "tests/test_github_client_lint.py::test_scripts_have_one_github_client",
    "tests/agent_runtime/test_claude_permissions.py::test_tracked_hooks_work_in_fresh_clone_without_deployed_claude",
    "tests/audit/test_track_deterministic_audit.py::test_config_consumer_file_launches_without_pythonpath",
    "tests/build/test_fresh_plan_review.py::test_every_plan_manifest_of_record_in_the_repository_still_validates",
    "tests/common/test_jsonl_splitlines_guard.py::test_scripts_structured_readers_do_not_use_str_splitlines",
    "tests/curriculum/evidence/test_lessons_lock.py::test_committed_lesson_lock_is_fresh",
    "tests/packaging/test_systemd_templates.py::test_data_volume_dropins_cover_all_services_and_preserve_commands",
    "tests/projects/open_model_data/test_k_path_literal_guard.py::test_k_path_literals_are_resolved_or_allowlisted",
    "tests/projects/open_model_data/test_quarantine.py::test_archive_import_guard_active_code",
    "tests/review/test_prompts.py::test_a_template_that_includes_imports_or_extends_a_file_fails_lint_and_render",
    "tests/review/test_prompts.py::test_template_lint_refuses_an_unclosed_fence_and_a_template_that_does_not_parse",
    "tests/review/test_prompts.py::test_template_lint_refuses_unresolved_placeholders_in_what_a_template_renders",
    "tests/review/test_prompts.py::test_the_shipped_templates_pass_the_lint_and_are_all_linted",
    "tests/storage/test_no_tracked_data.py::test_tracked_data_paths_are_all_allowlisted",
    "tests/test_conftest_task_store_guard.py::test_task_store_consumers_use_call_time_resolver",
    "tests/test_dashboards.py::TestApiEndpoints.test_endpoints_defined_in_router",
    "tests/test_deploy_script_idempotency.py::test_claude_deploy_ships_epic_named_skills_and_keeps_epic_handoffs",
    "tests/test_deploy_script_idempotency.py::test_claude_diff_excludes_do_not_mask_shipped_source",
    "tests/test_deploy_script_idempotency.py::test_codex_skills_have_one_discovery_root_and_migrate_verified_legacy",
    "tests/test_deploy_script_idempotency.py::test_fresh_deploy_produces_synced_output",
    "tests/test_entire_capture_guard.py::test_canary_evidence_bundle_carries_no_local_absolute_paths",
    "tests/test_kimi_coding_only_admission.py::test_every_allowlisted_root_exists_in_the_repository",
    "tests/test_landings_use_levellanding.py::test_arc_landings_are_generated_pages_the_router_mounts_from_frontmatter",
    "tests/test_llm_reviewer_dispatch.py::test_no_production_entrypoint_constructs_bare_bakeoff_arm",
    "tests/test_manifest_io.py::test_lexicon_scripts_do_not_open_manifest_inplace",
    "tests/test_no_hardcoded_venv_interpreter.py::test_no_executing_hardcoded_venv_interpreter",
    "tests/test_ohoiko_source_inventory_scope.py::test_ohoiko_abetka_inventory_covers_all_committed_key_words",
    "tests/test_review_reviewer_resolver.py::test_resolve_reviewer_classifies_every_adapter_and_reviewer_hook",
    "tests/test_readonly_source_db_connects.py::test_repo_has_no_unallowlisted_writable_source_db_connect",
    "tests/test_schema_validation.py::TestPlanYamlSchemaCheck.test_a2_plans_match_module_schema",
    "tests/test_secret_redactor_urls.py::test_ordinary_repository_corpus_is_unchanged_by_url_pass",
    "tests/test_sources_db_hardening.py::test_shared_sqlite_connections_route_through_open_readonly",
    "tests/test_storage_classification_table.py::test_frozen_rows_and_git_index_totals",
    "tests/test_red_team_consumer_trace.py::test_every_marker_or_status_consumer_has_a_fixed_handling_row",
)

# Escape hatch for a scanner the best-effort heuristic flags but that is not
# actually repo-wide. Each entry needs a concrete reason; the registry is kept
# fresh by ``test_not_repo_wide_entries_are_justified``.
NOT_REPO_WIDE = {
    "tests/test_ci_split.py::test_planned_shard_collects_build_tests_through_directory": (
        "Runs `git ls-files -- tests` to plan the CI shards and a pytest --collect-only "
        "over one shard's allowlist; it checks the split and the conftest allowlist hook, "
        "not a repository invariant."
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
    "tests/projects/open_model_data/test_atlas_pairing.py::test_pairing_does_not_modify_sources_db": (
        "Lists data/ only to stat sources.db without joining that filename onto a checkout "
        "path. data/ is not a test or script candidate, so a data change already forces the "
        "full tier. Generator changes select this test through its import."
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
    "tests/test_open_model_phase3_school_context_negative_recovery.py::test_schema_and_committed_receipt_validate": (
        "Runs `git ls-files --stage` on one registry receipt to assert mode 100644. "
        "That path is a single tracked file, not a repository tree scan."
    ),
    "tests/test_ci_pr_triggers.py::test_exactly_one_ci_gate_job_across_workflows": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change already forces the full tier."
    ),
    "tests/test_dashboards.py::TestApiEndpoints.test_fetch_calls_in_html": (
        "Scans dashboards/; dashboards/ is not a test or script candidate, so any change already forces the full tier."
    ),
    "tests/test_layerb_candidates.py::test_ci_differential_replays_all_unit_fixtures_at_pinned_base_values": (
        "Scans tests/fixtures/qg_bakeoff; fixture files are not test modules, so any change "
        "already forces the full tier."
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
    "tests/test_source_inventory_intake.py::test_committed_source_inventory_files_are_valid": (
        "Scans data/lexicon/source-inventory; data/ is not a test or script candidate, so "
        "any change already forces the full tier."
    ),
    "tests/test_workflow_head_concurrency.py::test_merge_group_workflows_do_not_unconditionally_cancel": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change already forces the full tier."
    ),
    "tests/test_shared_hooks_deploy_depth.py::test_shell_shlex_importers_do_not_write_bytecode": (
        "Globs only agents_extensions/shared/hooks/*.py to check that shell_shlex "
        "is imported after dont_write_bytecode. It does not scan the repository tree."
    ),
    "tests/audit/test_secret_scan_local.py::test_tracked_file_beneath_a_symlinked_parent_is_not_scanned": (
        "Runs `git ls-files` with cwd set to the tmp_path `repo` fixture to confirm a "
        "staged path exists there; it never lists or reads the live repository tree."
    ),
}

# These deploy tests copy only named source paths into isolated temporary
# checkouts. The heuristic follows _init_checkout into its conditional
# whole-tree and skill-discovery branches, but these callers take neither.
# They assert deployment behavior in the temporary tree, not an invariant
# across the live repository. Keep each name explicit so the registry's
# stale-entry check catches a renamed or removed test.
NOT_REPO_WIDE.update(
    {
        f"tests/test_deploy_script_idempotency.py::{name}": (
            "Copies declared source paths into a temporary checkout; the scanning "
            "helper's whole-tree branch is not taken by this test."
        )
        for name in (
            "test_codex_legacy_migration_preserves_modified_content",
            "test_agent_manifest_rejects_symlinked_intermediate_component",
            "test_gemini_shared_skill_overlay_is_checked_without_deleting_provider_skills",
            "test_agent_manifest_reaps_retired_hook_without_touching_agent_state",
            "test_agent_manifest_unlinks_symlink_leaf_without_following_target",
            "test_codex_legacy_migration_recognizes_committed_source_before_edits",
            "test_codex_legacy_python_cache_does_not_block_driver_deployment",
            "test_agent_transient_briefs_are_preserved",
            "test_gemini_shared_skill_name_collision_fails_closed",
            "test_agent_source_managed_subtrees_propagate_deletions_without_wiping_runtime",
            "test_tracked_mirror_drift_is_detected_before_deploy",
            "test_second_deploy_is_noop_for_codex_target",
            "test_gemini_shared_skill_exclusion_does_not_mask_root_drift",
            "test_tracked_mirror_resolves_each_deploy_source",
            "test_claude_epic_dirs_are_preserved",
            "test_driver_runtime_state_is_preserved",
            "test_tracked_agents_skill_declared_orphan_is_skipped",
            "test_tracked_claude_glob_orphan_is_skipped",
            "test_codex_orphan_prefix_siblings_abort_deploy_and_preserve_user_content",
            "test_drift_is_caught",
            "test_agent_manifest_keeps_lexically_unsafe_entries_rejected",
            "test_agent_manifest_migration_defers_reaping_verified_legacy_artifact",
            "test_codex_orphan_is_caught",
            "test_codex_legacy_migration_works_after_updated_sources_are_committed",
            "test_missing_codex_hooks_json_is_drift",
            "test_agent_overlay_write_stays_in_held_directory_after_root_swap",
            "test_codex_legacy_migration_requires_provenance_and_preserves_unsafe_content",
            "test_codex_retained_capture_survives_full_redeploy_with_late_writes",
            "test_bytecode_cache_is_not_an_orphan_and_is_not_declared",
        )
    }
)

# Repository-root path constants. A walk rooted at one of these (or a join into
# tests/scripts/agents_extensions) is repo-wide, not a temp fixture. The
# ``*_ROOT`` suffix and ``Path(__file__).parents[n]`` cover the inline forms.
_REPO_ROOT_CONSTANTS = frozenset(
    {
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
    }
)

# Whole-tree linter helpers: calling one is a repo scan even without a glob.
_KNOWN_SCANNER_CALLS = frozenset(
    {
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
    }
)

_SUBPROCESS_CALLS = frozenset(
    {
        "subprocess.run",
        "subprocess.check_output",
        "subprocess.check_call",
        "subprocess.call",
        "subprocess.Popen",
    }
)

_GIT_TREE_TOKENS = frozenset({"ls-files", "ls-tree"})

_TMP_RECEIVER_TOKENS = ("tmp_path", "tmpdir")

_WALK_ATTRS = frozenset({"glob", "rglob", "iterdir"})
_SCAN_SOURCE_TOKENS = _WALK_ATTRS | {"walk", "scandir"} | _KNOWN_SCANNER_CALLS


def _could_contain_scan(source: str) -> bool:
    # A subprocess argv may be module-bound or split across string tokens.
    return (
        any(token in source for token in _SCAN_SOURCE_TOKENS)
        or ("ls" in source and ("files" in source or "tree" in source))
        or "subprocess" in source
    )


def _test_module_paths() -> list[Path]:
    return sorted(_TESTS_ROOT.rglob("test_*.py"))


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
    *,
    expressions: dict[ast.expr, str] | None = None,
) -> frozenset[str]:
    """Bound names whose value is a repository-rooted expression, transitively.

    A function-local ``api_dir = ROOT / "scripts" / "api"`` roots any walk off
    ``api_dir`` just as a module-level constant would.
    ``expressions`` belongs to this scan's AST, never to a file or test session.
    Reused module bindings need rendering once, even across functions and
    fixed-point iterations; root classification still runs with current names.
    """
    expressions = {} if expressions is None else expressions
    names: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, value in bindings.items():
            if name in names:
                continue
            if value not in expressions:
                expressions[value] = ast.unparse(value)
            if _is_repo_root_expr(expressions[value], frozenset(repo_root_names | names)):
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


def _top_level_functions(
    tree: ast.Module,
) -> dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.ClassDef | None]]:
    found: dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.ClassDef | None]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[f"{node.name}.{item.name}"] = (item, node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[node.name] = (node, None)
    return found


def _implicated_test_functions(tree: ast.Module, source: str | None = None) -> dict[str, list[str]]:
    """Test functions that scan a repo tree directly or via a scanning helper."""
    functions = _top_level_functions(tree)
    repo_root_names = _module_repo_root_names(tree)
    module_bindings = _scope_bindings(tree.body)
    lines = source.splitlines(keepends=True) if source is not None else None
    function_source = (
        {
            name: "".join(
                lines[min((d.lineno for d in node.decorator_list), default=node.lineno) - 1 : node.end_lineno]
            )
            for name, (node, _owner) in functions.items()
        }
        if lines is not None
        else {}
    )
    direct: dict[str, list[str]] = {}
    expressions: dict[ast.expr, str] = {}
    for name, (node, _owner) in functions.items():
        if lines is not None and not _could_contain_scan(function_source[name]):
            continue
        bindings = {**module_bindings, **_scope_bindings(node.body)}
        root_names = repo_root_names | _bindings_repo_root_names(bindings, repo_root_names, expressions=expressions)
        if sites := _direct_scan_sites(node, root_names, bindings):
            direct[name] = sites

    def calls(node: ast.AST) -> set[str]:
        return {_call_name(call).rsplit(".", 1)[-1] for call in ast.walk(node) if isinstance(call, ast.Call)}

    # Propagate through every function: a test that (transitively) calls a
    # scanning helper is itself a scanner, even when the chain passes through
    # helpers that do not scan on their own. Method keys are ``Class.method``, so
    # compare on the bare callable name.
    function_calls: dict[str, set[str]] = {}
    implicated_all = set(direct)
    changed = True
    while changed:
        changed = False
        bare = {name.rsplit(".", 1)[-1] for name in implicated_all}
        for name, (node, _owner) in functions.items():
            if name in implicated_all:
                continue
            if lines is not None and not any(called in function_source[name] for called in bare):
                continue
            if name not in function_calls:
                function_calls[name] = calls(node)
            called = function_calls[name]
            if called & bare:
                implicated_all.add(name)
                changed = True

    return {
        name: direct.get(name, ["via scanning helper"])
        for name in implicated_all
        if name.rsplit(".", 1)[-1].startswith("test_")
    }


# The registry checks below read the marks pytest itself applies, so alias
# imports, class ``pytestmark``, conftest hooks, inherited tests and
# ``pytest.param(..., marks=...)`` count exactly as CI sees them (#9434). A
# child interpreter collects (never runs) the candidate files with the
# repository's own config; ``pytest_itemcollected`` keeps the tests that ``-m``
# later deselects, and the marks are read after every modifyitems hook ran.
# The child is ``--collect-only``, which the dispatch cap exempts from the
# full-suite lock that a worker's serial ``pytest -m repo_wide`` parent holds.
# It runs in its own process group (tests/process_group_child.py), so a test
# timeout that ends the xdist worker ends the child too (#10777).
_COLLECT_SCRIPT = textwrap.dedent(
    """
    import json
    import sys
    from pathlib import Path

    import pytest


    class RepoWideMarks:
        def __init__(self, allowed):
            self.allowed = {Path(path) for path in allowed}
            self.directories = {parent for path in self.allowed for parent in path.parents}
            self.items = {}

        def pytest_ignore_collect(self, collection_path):
            # Per-file arguments make pytest rebuild every sibling module once per
            # argument, so collect the directories and admit only the candidates.
            # An admitted directory overrides norecursedirs (``build``), as the
            # CI shard allowlist does.
            path = collection_path.resolve()
            return path not in (self.directories if path.is_dir() else self.allowed)

        def pytest_itemcollected(self, item):
            self.items[item.nodeid] = item

        def pytest_collection_finish(self, session):
            for item in session.items:
                self.items.setdefault(item.nodeid, item)


    output, allowed, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    with open(allowed, encoding="utf-8") as handle:
        collector = RepoWideMarks(frozenset(json.load(handle)))
    status = int(pytest.main(args, plugins=[collector]))
    rows = []
    for item in collector.items.values():
        carriers = [node for node, _mark in item.iter_markers_with_node("repo_wide")]
        if not carriers:
            continue
        module = item.getparent(pytest.Module)
        module_scope = module.listchain()
        names = [node.name for node in item.listchain() if isinstance(node, pytest.Class)]
        names.append(getattr(item, "originalname", item.name))
        rows.append(
            [module.nodeid, ".".join(names), any(c is n for c in carriers for n in module_scope)]
        )
    with open(output, "w", encoding="utf-8") as handle:
        json.dump({"status": status, "rows": rows}, handle)
    """
)

# The child must see every test file and the plain repository config, as CI
# does: a shard allowlist would hide files, and a parent's addopts, plugin list
# (a dispatch worker sets one) or artifact list would leak into it. It is its
# own session, not an xdist worker of the parent, so xdist's worker variables
# go too (the dispatch cap reads them to skip the full-suite lock).
_CHILD_ENV_DROP = frozenset(
    {
        "LU_PYTEST_SHARD_FILES",
        "LU_PYTEST_NEEDS_ARTIFACT_COLLECTED",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTEST_XDIST_TESTRUNUID",
        "PYTEST_XDIST_WORKER",
        "PYTEST_XDIST_WORKER_COUNT",
    }
)
_COLLECT_TIMEOUT_S = 90
_MARK_NAME = "repo_wide"


def _child_env() -> dict[str, str]:
    return {name: value for name, value in os.environ.items() if name not in _CHILD_ENV_DROP}


def _names_the_marker(source: str) -> bool:
    """True when code can author or register the marker, rather than just name it.

    Identifiers cover decorators, pytestmark, aliases and re-exports. String
    arguments count only in marker lookup, application, construction or
    registration calls; allowlists, docstrings and embedded fixture code do
    not apply marks. Indirect or computed marker names remain outside this
    approximation; the exact nightly collection is the correctness anchor.
    """
    if _MARK_NAME not in source and not ("repo" in source and "_wide" in source):
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Unknown syntax must not silently exclude a potential mark source.
        return True
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == _MARK_NAME:
            return True
        if isinstance(node, ast.Attribute) and node.attr == _MARK_NAME:
            return True
        if isinstance(node, ast.alias) and node.name == _MARK_NAME:
            return True
        if not isinstance(node, ast.Call):
            continue
        call = _call_name(node).rsplit(".", 1)[-1]
        if call not in {"getattr", "add_marker", "Mark", "addinivalue_line"}:
            continue
        values = [*node.args, *(keyword.value for keyword in node.keywords)]
        for value in values:
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            name = value.value.partition(":")[0].strip() if call == "addinivalue_line" else value.value
            if name == _MARK_NAME:
                return True
    return False


# Calls that load a module named by a string or a file path at run time.
_DYNAMIC_LOADERS = frozenset(
    {
        "import_module",
        "import_named_module",
        "__import__",
        "spec_from_file_location",
        "SourceFileLoader",
        "run_path",
        "run_module",
    }
)


def _dotted_name(path: Path, root: Path) -> str:
    """``path`` as a dotted module name from ``root``; a package is its ``__init__``."""
    parts = path.relative_to(root).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _module_loads(path: Path, root: Path, source: str) -> tuple[frozenset[str], frozenset[str]]:
    """Dotted names ``path`` imports (with their parent packages), and its run-time load strings.

    Relative imports resolve to names from ``root``. The second set holds the
    module's string constants when it calls a dynamic loader, else it is empty.
    A module Python cannot parse cannot be imported, so it loads nothing.
    """
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return frozenset(), frozenset()
    own = _dotted_name(path, root).split(".")
    package = own if path.name == "__init__.py" else own[:-1]
    names: set[str] = set()
    strings: set[str] = set()
    dynamic = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = package[: len(package) - node.level + 1] if node.level else []
            prefix = ".".join([*base, *([node.module] if node.module else [])])
            names.add(prefix)
            names.update(f"{prefix}.{alias.name}" if prefix else alias.name for alias in node.names)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytest_plugins" for target in node.targets
        ):
            names.update(
                name.strip()
                for constant in ast.walk(node.value)
                if isinstance(constant, ast.Constant) and isinstance(constant.value, str)
                for name in constant.value.split(",")
            )
        elif isinstance(node, ast.Call) and _call_name(node).rsplit(".", 1)[-1] in _DYNAMIC_LOADERS:
            dynamic = True
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    with_parents = {".".join(name.split(".")[:end]) for name in names if name for end in range(1, name.count(".") + 2)}
    return frozenset(with_parents), frozenset(strings) if dynamic else frozenset()


def _loads_any(loads: tuple[frozenset[str], frozenset[str]], targets: dict[str, Path]) -> bool:
    """True when the imports or run-time load strings reach one of ``targets`` (dotted name -> path).

    An import name matches a target whose dotted name from the repository root
    ends with it, whichever ``sys.path`` entry it is relative to. A load string
    matches by file name or by a dotted suffix ending in the module's name.
    """
    names, strings = loads
    for dotted, path in targets.items():
        if any(dotted == name or dotted.endswith("." + name) for name in names):
            return True
        stem = dotted.rsplit(".", 1)[-1]
        if any(
            text.replace("\\", "/").rsplit("/", 1)[-1] == path.name or text == stem or text.endswith("." + stem)
            for text in strings
        ):
            return True
    return False


def _candidate_test_files(
    root: Path, sources: Collection[Path], test_files: Collection[Path], global_plugins: Collection[str] = ()
) -> frozenset[Path]:
    """Test files whose collection can run code that applies a ``repo_wide`` mark.

    A mark source can author or register the marker, or import or dynamically
    load a mark source (a re-exported mark, a marked base class).
    A test file's collection runs the mark sources it is, a ``conftest.py`` or
    package ``__init__.py`` above it that is one, and every global plugin.
    Conftest hooks act by location, not import, so a directory never joins the
    import closure. Over-inclusion only costs collection time.

    This is a fast approximation, not a proof (#9434 review). It misses a
    conftest hook that marks tests outside its own directory, a mark source
    loaded through an aliased loader (``import_module as load``), and a marker
    name passed indirectly or built at run time (``"repo" + "_wide"``).
    The ``slow`` exact check collects without this filter and catches them.
    """
    texts = {path: path.read_text(encoding="utf-8", errors="replace") for path in sources}
    loads: dict[Path, tuple[frozenset[str], frozenset[str]]] = {}
    marking = {path for path, text in texts.items() if _names_the_marker(text)}
    frontier = set(marking)
    while frontier:
        targets = {_dotted_name(path, root): path for path in frontier}
        # Importing or loading a module spells its last name, so skip any file without one.
        mentions = re.compile("|".join(sorted({re.escape(dotted.rsplit(".", 1)[-1]) for dotted in targets})))
        joined: set[Path] = set()
        for path, text in texts.items():
            if path in marking or not mentions.search(text):
                continue
            if path not in loads:
                loads[path] = _module_loads(path, root, text)
            if _loads_any(loads[path], targets):
                joined.add(path)
        marking |= joined
        frontier = joined
    if any(path.stem in global_plugins for path in marking):
        return frozenset(test_files)
    marking_dirs = {path.parent for path in marking if path.name in {"conftest.py", "__init__.py"}}
    return frozenset(
        path
        for path in test_files
        if path in marking or any(path.is_relative_to(directory) for directory in marking_dirs)
    )


def _global_plugin_names() -> frozenset[str]:
    """Module stems of the plugins the repository config loads for every collection (``-p`` addopts)."""
    config = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    argv = shlex.split(config["tool"]["pytest"]["ini_options"].get("addopts", ""))
    names = [value for flag, value in itertools.pairwise(argv) if flag == "-p"]
    names += [arg[2:] for arg in argv if arg.startswith("-p") and len(arg) > 2]
    return frozenset(name.strip().rsplit(".", 1)[-1] for name in names if name.strip() and ":" not in name)


def _listed_files(pathspec: str) -> set[Path]:
    """Tracked and untracked, not ignored, files matching ``pathspec`` (tracked as in CI, untracked as soon as committed)."""
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", pathspec],
        cwd=_REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
        timeout=30,
    ).stdout
    return {_REPO_ROOT / name for name in listed.split("\0") if name}


def _repository_python_sources() -> list[Path]:
    paths = _listed_files("*.py")
    # pytest collects ignored files too, so add every conftest and test module on disk.
    paths |= set(_TESTS_ROOT.rglob("conftest.py")) | set(_test_module_paths())
    return sorted(path for path in paths if path.is_file())


def _collect_repo_wide_marks(
    root: Path, test_files: Collection[Path], timeout: float = _COLLECT_TIMEOUT_S
) -> tuple[frozenset[str], frozenset[str]]:
    """Modules marked at module (or a higher) scope, and tests marked below it.

    Function identities are ``path::Class.test`` without parameter ids, the
    collected class and not the class that defines an inherited test. A test in
    a module-marked module is covered by the module row, so it is not listed.
    Only ``test_files`` are collected, each directory admitted past
    ``norecursedirs`` as CI's shard allowlist admits it.
    """
    if not test_files:
        return frozenset(), frozenset()
    with tempfile.TemporaryDirectory() as scratch:
        output = Path(scratch) / "marks.json"
        allowed = Path(scratch) / "allowed.json"
        allowed.write_text(json.dumps(sorted(str(path.resolve()) for path in test_files)), encoding="utf-8")
        result = run_in_process_group(
            [
                sys.executable,
                "-c",
                _COLLECT_SCRIPT,
                str(output),
                str(allowed),
                "--collect-only",
                "-q",
                "-p",
                "no:cacheprovider",
                *sorted({path.relative_to(root).parts[0] for path in test_files}),
            ],
            cwd=root,
            env=_child_env(),
            timeout=timeout,
        )
        report = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else None
    assert report is not None and report["status"] in {0, 5}, (
        "collecting the repo_wide candidates failed, so the marked set is unknown:\n"
        + (result.stdout + result.stderr)[-4000:]
    )
    modules = frozenset(module for module, _name, module_scope in report["rows"] if module_scope)
    functions = frozenset(f"{module}::{name}" for module, name, module_scope in report["rows"] if module not in modules)
    return modules, functions


@lru_cache(maxsize=1)
def _repository_candidates() -> frozenset[Path]:
    return _candidate_test_files(_REPO_ROOT, _repository_python_sources(), _test_module_paths(), _global_plugin_names())


@lru_cache(maxsize=1)
def _repository_marks() -> tuple[frozenset[str], frozenset[str]]:
    return _collect_repo_wide_marks(_REPO_ROOT, _repository_candidates())


def test_the_prefilter_leaves_most_test_modules_out() -> None:
    """A mark source that tests/conftest.py or a global plugin loads makes every test a candidate (#10777).

    Collecting them all outlasts the 120 s test timeout on a loaded host, and
    the registry checks below then time out instead of checking anything. A
    test file name in a module that loads modules dynamically reads as a load
    of that test, as one in scripts/delegate.py did.
    """
    candidates, test_modules = _repository_candidates(), frozenset(_test_module_paths())

    assert len(candidates) * 2 < len(test_modules), (
        f"{len(candidates)} of {len(test_modules)} test modules are repo_wide candidates; find the "
        "mark source that tests/conftest.py or the -p plugins import and break that chain"
    )


def _unregistered_repo_wide_nodes(
    marked: tuple[frozenset[str], frozenset[str]],
    known_modules: Collection[str],
    known_functions: Collection[str],
) -> list[str]:
    modules, functions = marked
    return sorted((modules - set(known_modules)) | (functions - set(known_functions)))


def test_every_marked_test_has_a_registry_row() -> None:
    """The registry is complete: a marked test without a row fails (#9434).

    The two checks above only follow registry rows to their markers, so a
    deleted row used to pass. This check walks pytest's marks back to the rows.
    It reads the prefiltered collection; the named shapes it misses are
    documented on ``_candidate_test_files``.
    """
    unregistered = _unregistered_repo_wide_nodes(
        _repository_marks(), KNOWN_REPO_WIDE_MODULES, KNOWN_REPO_WIDE_FUNCTIONS
    )
    assert not unregistered, (
        "These tests carry the repo_wide marker but have no row in KNOWN_REPO_WIDE_MODULES "
        "(module-level marker) or KNOWN_REPO_WIDE_FUNCTIONS (function or class marker). "
        "Add the row:\n" + "\n".join(unregistered)
    )


def test_collection_child_runs_while_the_parent_holds_the_full_suite_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A dispatch worker's serial ``pytest -m repo_wide`` holds the full-suite lock (#9434).

    The child collects the ``tests`` directory, which the cap counts as the full
    suite, so it must not need the lock its parent holds. The control run shows
    the lock is held and the cap is armed in the child: a run that is not
    collection-only is still refused.
    """
    lock = tmp_path / "pytest-full-suite.lock"
    monkeypatch.setenv(DISPATCH_TASK_ENV, "repo-wide-lock-regression")
    monkeypatch.setenv(LOCK_ENV, str(lock))
    fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        marked = _collect_repo_wide_marks(_REPO_ROOT, [_REPO_ROOT / "tests/test_hooks_executable.py"])
        refused = run_in_process_group(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
            cwd=_REPO_ROOT,
            env=_child_env(),
            timeout=_COLLECT_TIMEOUT_S,
        )
    finally:
        os.close(fd)
    assert marked == (frozenset({"tests/test_hooks_executable.py"}), frozenset())
    assert refused.returncode != 0
    assert FULL_SUITE_BUSY in refused.stdout + refused.stderr


_SYNTHETIC_TREE = {
    "pytest.ini": "[pytest]\nmarkers =\n    repo_wide: test marker\n",
    "tests/test_alias.py": """
        import pytest as pt

        @pt.mark.repo_wide
        def test_alias():
            ...
        """,
    "tests/test_class_pytestmark.py": """
        import pytest

        class TestScan:
            pytestmark = [pytest.mark.slow, pytest.mark.repo_wide]

            def test_x(self):
                ...

        def test_outside():
            ...
        """,
    "tests/test_class_decorated.py": """
        import pytest

        @pytest.mark.repo_wide
        class TestDecorated:
            def test_x(self):
                ...

        def test_unmarked():
            ...
        """,
    "tests/test_module_marked.py": """
        import pytest

        pytestmark = pytest.mark.repo_wide

        @pytest.mark.repo_wide
        def test_also_decorated():
            ...
        """,
    "tests/marked/conftest.py": """
        import pytest

        def pytest_collection_modifyitems(items):
            for item in items:
                if item.name == "test_hook_marked":
                    item.add_marker(pytest.mark.repo_wide)
        """,
    "tests/marked/test_plain.py": """
        def test_hook_marked():
            ...

        def test_untouched():
            ...
        """,
    "tests/scan_base.py": """
        import pytest

        class ScanBase:
            @pytest.mark.repo_wide
            def test_inherited(self):
                ...
        """,
    "tests/test_inherit.py": """
        from scan_base import ScanBase

        class TestScan(ScanBase):
            pass
        """,
    "tests/test_params.py": """
        import pytest

        @pytest.mark.parametrize("x", [pytest.param(1, marks=pytest.mark.repo_wide), 2])
        def test_marked_param(x):
            ...

        @pytest.mark.parametrize("x", [pytest.mark.repo_wide])
        def test_mark_as_data(x):
            ...
        """,
    "tests/test_mention_only.py": '''
        """repo_wide is only mentioned here."""
        import pytest

        # repo_wide
        @pytest.mark.slow
        def test_x():
            ...
        ''',
    "tests/test_unrelated.py": """
        def test_y():
            ...
        """,
}


def _write_synthetic_tree(root: Path) -> tuple[list[Path], list[Path]]:
    for relative, source in _SYNTHETIC_TREE.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source), encoding="utf-8")
    sources = sorted(root.rglob("*.py"))
    return sources, [path for path in sources if path.name.startswith("test_")]


def test_completeness_follows_pytest_effective_marks(tmp_path: Path) -> None:
    """Each mark the AST scan missed (#9434 review) is collected under its collected identity."""
    sources, test_files = _write_synthetic_tree(tmp_path)
    candidates = _candidate_test_files(tmp_path, sources, test_files)
    marked = _collect_repo_wide_marks(tmp_path, candidates)
    assert marked == (
        frozenset({"tests/test_module_marked.py"}),
        frozenset(
            {
                "tests/test_alias.py::test_alias",
                "tests/test_class_decorated.py::TestDecorated.test_x",
                "tests/test_class_pytestmark.py::TestScan.test_x",
                "tests/marked/test_plain.py::test_hook_marked",
                "tests/test_inherit.py::TestScan.test_inherited",
                "tests/test_params.py::test_marked_param",
            }
        ),
    )
    # The prefilter loses nothing: collecting every file finds the same marks.
    assert _collect_repo_wide_marks(tmp_path, test_files) == marked
    relative = {path.relative_to(tmp_path).as_posix() for path in candidates}
    assert "tests/test_unrelated.py" not in relative
    assert "tests/test_mention_only.py" not in relative  # its docstring cannot apply a marker
    # A module row does not stand in for a function row, or the reverse.
    assert _unregistered_repo_wide_nodes(
        marked, ["tests/test_alias.py"], ["tests/test_module_marked.py::test_also_decorated"]
    ) == sorted(marked[0] | marked[1])


def _synthetic(source: str) -> ast.Module:
    return ast.parse(textwrap.dedent(source))


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
