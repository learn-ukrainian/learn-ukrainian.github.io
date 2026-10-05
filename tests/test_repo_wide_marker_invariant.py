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
   collection-only child run. The PR-tier checks collect only the test files a
   source prefilter says can carry the mark; that is an early warning, and
   ``_candidate_test_files`` names the shapes it misses. The exact check,
   ``test_registry_matches_every_collected_repo_wide_mark`` in
   ``tests/test_repo_wide_registry_exact.py``, is ``slow`` (the nightly lane):
   it collects every test file CI collects, with no prefilter, and compares the
   registry with the collected marks both ways. It lives in its own module,
   without ``repo_wide``, so a worker's ``pytest -m repo_wide`` never runs a
   whole-suite collection.
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

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_ROOT = _REPO_ROOT / "tests"

# Whole-tree scanners over tests/, scripts/, agents_extensions/ (or a stable
# subtree of them) that carry the marker at module scope.
KNOWN_REPO_WIDE_MODULES = frozenset(
    {
        "tests/ai_agent_bridge/test_module_identity.py",
        "tests/api/test_api_subprocess_timeout.py",
        "tests/api/test_import_pinning.py",
        "tests/hygiene/test_tracked_symlink_targets.py",
        "tests/orchestration/test_thread_restart_e2e.py",
        "tests/orchestration/test_worktree_removal_invariant.py",
        "tests/test_agent_fleet_tooling_guardrails.py",
        "tests/test_ask_opencode.py",
        "tests/test_curriculum_upgrade_no_host_run_root.py",
        "tests/test_cyrillic_roundtrip_invariant.py",
        "tests/test_docs_catalogue.py",
        "tests/test_docs_catalogue_coverage.py",
        "tests/test_docs_find_lookups_part1.py",
        "tests/test_docs_find_lookups_part2.py",
        "tests/test_docs_find_lookups_part3.py",
        "tests/test_docs_find_lookups_part4.py",
        "tests/test_docs_find_lookups_part5.py",
        "tests/test_docs_find_lookups_part6.py",
        "tests/test_docs_find_lookups_part7.py",
        "tests/test_docs_find_lookups_part8.py",
        "tests/test_fleet_routing_open_model_data_import_guard.py",
        "tests/test_frontend_denominator_invariant.py",
        "tests/test_hooks_executable.py",
        "tests/test_lesson_atlas_link_census.py",
        "tests/test_lint_fleet_roster.py",
        "tests/test_lint_prompts.py",
        "tests/test_lint_test_assertions.py",
        "tests/test_no_rewrite_contract.py",
        "tests/test_post_processor_mutation_invariant.py",
        "tests/test_public_tree_no_baked_host_run_root.py",
        "tests/test_pytest_plugins_not_test_modules.py",
        "tests/test_repo_wide_marker_invariant.py",
        "tests/test_session_identity_env_isolation.py",
        "tests/test_session_state_retired.py",
        "tests/test_sparse_collection_guard.py",
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
    "tests/agent_runtime/test_attempt_safe_read.py::test_scripts_only_import_does_not_load_isolation",
    "tests/agent_runtime/test_claude_no_background.py::test_claude_code_harness_denominator_is_complete",
    "tests/agent_runtime/test_claude_permissions.py::test_tracked_hooks_work_in_fresh_clone_without_deployed_claude",
    "tests/agent_runtime/test_npm_shim.py::test_shim_files_are_regular_executables",
    "tests/api/test_app_factory.py::test_db_access_patterns_have_the_step_two_allowlist",
    "tests/audit/test_post_build_review.py::test_prompt_versions_match_track_policy",
    "tests/build/test_fresh_page_safety.py::test_ci_runs_site_toolchain_tests_in_required_frontend_job",
    "tests/build/test_fresh_plan_review.py::test_every_plan_manifest_of_record_in_the_repository_still_validates",
    "tests/build/test_fresh_style_cards.py::test_the_three_bands_and_nothing_else",
    "tests/common/test_jsonl_splitlines_guard.py::test_scripts_structured_readers_do_not_use_str_splitlines",
    "tests/packaging/test_systemd_templates.py::test_data_volume_dropins_cover_all_services_and_preserve_commands",
    "tests/projects/open_model_data/test_k_path_literal_guard.py::test_k_path_literals_are_resolved_or_allowlisted",
    "tests/projects/open_model_data/test_quarantine.py::test_archive_import_guard_active_code",
    "tests/projects/open_model_data/test_quarantine.py::test_archive_lists_every_archived_python_file",
    "tests/projects/open_model_data/test_v4_per_slot_factory.py::test_no_test_in_this_suite_asserts_nonzero_completion_behind_a_stubbed_validator",
    "tests/review/test_integration_check.py::test_no_cyrillic_in_the_check_or_its_tests",
    "tests/review/test_prompts.py::test_a_re_review_template_may_name_its_previous_findings_but_a_first_review_template_may_not",
    "tests/review/test_prompts.py::test_a_template_that_includes_imports_or_extends_a_file_fails_lint_and_render",
    "tests/review/test_prompts.py::test_no_cyrillic_characters_in_templates_or_code",
    "tests/review/test_prompts.py::test_no_e3d_placeholder_markers_are_left",
    "tests/review/test_prompts.py::test_template_lint_refuses_an_unclosed_fence_and_a_template_that_does_not_parse",
    "tests/review/test_prompts.py::test_template_lint_refuses_another_modules_slug_but_not_ordinary_prose",
    "tests/review/test_prompts.py::test_template_lint_refuses_unresolved_placeholders_in_what_a_template_renders",
    "tests/review/test_prompts.py::test_template_lint_refuses_v1_writer_and_earlier_edition_wording",
    "tests/review/test_prompts.py::test_the_shipped_templates_pass_the_lint_and_are_all_linted",
    "tests/review/test_prompts.py::test_the_template_prose_exemption_is_exactly_the_real_collisions_of_the_shipped_templates",
    "tests/storage/test_no_tracked_data.py::test_tracked_data_paths_are_all_allowlisted",
    "tests/test_agent_seat_onboarding_docs.py::test_live_driver_diagnostics_never_claim_again",
    "tests/test_ci_dependency_check.py::test_ci_interpreter_pin_matches_the_warmer_and_advisory_cache",
    "tests/test_conftest_task_store_guard.py::test_task_store_consumers_use_call_time_resolver",
    "tests/test_dashboards.py::TestApiEndpoints.test_endpoints_defined_in_router",
    "tests/test_deploy_script_idempotency.py::test_claude_deploy_ships_epic_named_skills_and_keeps_epic_handoffs",
    "tests/test_deploy_script_idempotency.py::test_claude_diff_excludes_do_not_mask_shipped_source",
    "tests/test_deploy_script_idempotency.py::test_codex_skills_have_one_discovery_root_and_migrate_verified_legacy",
    "tests/test_deploy_script_idempotency.py::test_fresh_deploy_produces_synced_output",
    "tests/test_drive_epic_skill_core.py::test_every_reference_is_linked_from_the_core",
    "tests/test_drive_epic_skill_core.py::test_section_citations_used_by_scripts_still_resolve",
    "tests/test_driver_work_api_onboarding.py::test_skill_teaches_grok_bot_with_hard_exclusions",
    "tests/test_driver_work_api_onboarding.py::test_skill_teaches_the_full_health_enum",
    "tests/test_driver_work_api_onboarding.py::test_skill_teaches_work_api_projection_semantics",
    "tests/test_kimi_coding_only_admission.py::test_every_allowlisted_root_exists_in_the_repository",
    "tests/test_landings_use_levellanding.py::test_arc_landings_are_generated_pages_the_router_mounts_from_frontmatter",
    "tests/test_launcher_contract.py::test_retired_names_are_absent_from_tracked_content",
    "tests/test_live_driver_message_consumption.py::test_drive_epic_skill_keeps_all_required_live_inbox_boundaries",
    "tests/test_llm_reviewer_dispatch.py::test_no_production_entrypoint_constructs_bare_bakeoff_arm",
    "tests/test_manifest_io.py::test_lexicon_scripts_do_not_open_manifest_inplace",
    "tests/test_no_hardcoded_venv_interpreter.py::test_no_executing_hardcoded_venv_interpreter",
    "tests/test_ohoiko_source_inventory_scope.py::test_ohoiko_abetka_inventory_covers_all_committed_key_words",
    "tests/test_operator_contract_wiring.py::test_epic_driver_and_v2_template_keep_prompt_adequacy_gate",
    "tests/test_prompt_template_render.py::test_phase_template_renders_without_unknown_tokens",
    "tests/test_review_reviewer_resolver.py::test_resolve_reviewer_classifies_every_adapter_and_reviewer_hook",
    "tests/test_schema_validation.py::TestPlanYamlSchemaCheck.test_a2_plans_match_module_schema",
    "tests/test_session_streams.py::test_backslash_tracked_paths_add_no_hostname_rejections",
    "tests/test_session_streams.py::test_collision_exceptions_are_exact_tracked_repository_names",
    "tests/test_session_streams.py::test_embedded_host_filter_accepts_every_tracked_basename",
    "tests/test_session_streams.py::test_embedded_host_exemptions_are_required_by_tracked_basenames",
    "tests/test_skill_instruction_routes.py::test_split_skill_references_are_reachable_from_their_entrypoint",
    "tests/test_skill_instruction_routes.py::test_task_scope_selector_keeps_canonical_sources_and_phase_gates_reachable",
    "tests/test_storage_classification_table.py::test_frozen_rows_and_git_index_totals",
)

# Escape hatch for a scanner the best-effort heuristic flags but that is not
# actually repo-wide. Each entry needs a concrete reason; the registry is kept
# fresh by ``test_not_repo_wide_entries_are_justified``.
NOT_REPO_WIDE = {
    "tests/review/test_prompts.py::test_isolated_prompt_bytes_equal_main_before_9464": (
        "Globs only tests/review/fixtures/isolated-main-prompts/*.md.j2, not a repository "
        "tree. Fixture files are not test modules, so changes force the full tier; "
        "changes to the test module select it directly, and prompt renderer changes "
        "select it through its imports."
    ),
    "tests/test_ci_split.py::test_planned_shard_collects_build_tests_through_directory": (
        "Runs `git ls-files -- tests` to plan the CI shards and a pytest --collect-only "
        "over one shard's allowlist; it checks the split and the conftest allowlist hook, "
        "not a repository invariant."
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
    "tests/test_open_model_phase3_school_context_negative_recovery.py::test_schema_and_committed_receipt_validate": (
        "Runs `git ls-files --stage` on one registry receipt to assert mode 100644. "
        "That path is a single tracked file, not a repository tree scan."
    ),
    "tests/test_ci_pr_triggers.py::test_no_workflow_reruns_ci_on_a_label": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change already forces the full tier."
    ),
    "tests/test_ci_pr_triggers.py::test_exactly_one_ci_gate_job_across_workflows": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change already forces the full tier."
    ),
    "tests/test_dashboards.py::TestDashboardInventory.test_expected_dashboards_exist": (
        "Scans dashboards/; dashboards/ is not a test or script candidate, so any change already forces the full tier."
    ),
    "tests/test_dashboards.py::TestApiEndpoints.test_fetch_calls_in_html": (
        "Scans dashboards/; dashboards/ is not a test or script candidate, so any change already forces the full tier."
    ),
    "tests/test_layerb_candidates.py::test_ci_differential_replays_all_unit_fixtures_at_pinned_base_values": (
        "Scans tests/fixtures/qg_bakeoff; fixture files are not test modules, so any change "
        "already forces the full tier."
    ),
    "tests/test_monitor_route_contracts.py::test_every_dashboard_html_file_has_page_contract": (
        "Scans dashboards/; dashboards/ is not a test or script candidate, so any change already forces the full tier."
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
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change already forces the full tier."
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
    "tests/test_dispatch_xdist_cap.py::test_ci_workflows_do_not_set_the_dispatch_marker": (
        "Scans .github/workflows; .github/ is on the shared-root denylist, so any change already forces the full tier."
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
            "test_deploy_preflight_preserves_declared_glob_and_trailing_slash_subtrees",
            "test_codex_legacy_migration_preserves_modified_content",
            "test_agent_manifest_rejects_symlinked_intermediate_component",
            "test_gemini_shared_skill_overlay_is_checked_without_deleting_provider_skills",
            "test_agent_manifest_reaps_retired_hook_without_touching_agent_state",
            "test_agent_manifest_unlinks_symlink_leaf_without_following_target",
            "test_agent_manifest_reaps_legitimate_nested_file",
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
            "test_pyc_named_symlink_is_deployed",
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


def _function_marked(tree: ast.Module, function: str) -> bool:
    entry = _top_level_functions(tree).get(function)
    if entry is None:
        return False
    node, owner = entry
    return _marked_by_repo_wide(node.decorator_list) or (
        owner is not None and _marked_by_repo_wide(owner.decorator_list)
    )


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


@lru_cache(maxsize=128)
def _cached_scan_facts(filename: str, source: str) -> tuple[frozenset[str], frozenset[str], tuple[str, ...]]:
    """Reuse call-graph facts for identical module content without retaining ASTs."""
    tree = ast.parse(source, filename=filename)
    return (
        frozenset(_top_level_functions(tree)),
        frozenset(_implicated_test_functions(tree, source)),
        tuple(_module_level_scan_sites(tree)),
    )


def test_repo_tree_scanners_carry_the_marker() -> None:
    """A test that scans a repo tree or runs a repo lint must be ``repo_wide``.

    Per-function granularity: every implicated test is checked on its own, so a
    module with two scanners and one marker fails.
    """
    missing: list[str] = []
    for module in _test_module_paths():
        source = module.read_text(encoding="utf-8")
        # Every supported direct scanner contains one of these names or the
        # literal git argv prefix. Skip modules that cannot have a scan site;
        # the AST pass remains authoritative for every possible candidate.
        if not _could_contain_scan(source):
            continue
        relative = module.relative_to(_REPO_ROOT).as_posix()
        tree = ast.parse(source, filename=str(module))
        module_marked = _module_marked(tree)
        # The module mark applies to every function and module-level scan. No
        # scan-site analysis can add a missing marker once this is established.
        if module_marked:
            continue
        for function, sites in _implicated_test_functions(tree, source).items():
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


# The registry checks below read the marks pytest itself applies, so alias
# imports, class ``pytestmark``, conftest hooks, inherited tests and
# ``pytest.param(..., marks=...)`` count exactly as CI sees them (#9434). A
# child interpreter collects (never runs) the candidate files with the
# repository's own config; ``pytest_itemcollected`` keeps the tests that ``-m``
# later deselects, and the marks are read after every modifyitems hook ran.
# The child is ``--collect-only``, which the dispatch cap exempts from the
# full-suite lock that a worker's serial ``pytest -m repo_wide`` parent holds.
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
# Collecting the whole suite took 178s on a loaded 16-core host (2026-10-03).
# One child must collect it all: a modifyitems hook sees only its own run's items.
_EXACT_COLLECT_TIMEOUT_S = 1200
_MARK_NAME = "repo_wide"
_EXACT_CHECK_MODULE = "tests/test_repo_wide_registry_exact.py"
_EXACT_CHECK = f"{_EXACT_CHECK_MODULE}::test_registry_matches_every_collected_repo_wide_mark"


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
    {"import_module", "__import__", "spec_from_file_location", "SourceFileLoader", "run_path", "run_module"}
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


def _ci_test_files() -> list[Path]:
    """Every test file CI's shards collect between them (``git ls-files -- tests`` named ``test_*.py``, ci.yml)."""
    return sorted(
        path
        for path in _listed_files("tests")
        if path.name.startswith("test_") and path.suffix == ".py" and path.is_file()
    )


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
        result = subprocess.run(
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
            capture_output=True,
            text=True,
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
def _repository_marks() -> tuple[frozenset[str], frozenset[str]]:
    candidates = _candidate_test_files(
        _REPO_ROOT, _repository_python_sources(), _test_module_paths(), _global_plugin_names()
    )
    return _collect_repo_wide_marks(_REPO_ROOT, candidates)


def _unregistered_repo_wide_nodes(
    marked: tuple[frozenset[str], frozenset[str]],
    known_modules: Collection[str],
    known_functions: Collection[str],
) -> list[str]:
    modules, functions = marked
    return sorted((modules - set(known_modules)) | (functions - set(known_functions)))


def test_known_repo_wide_modules_carry_the_marker() -> None:
    missing = [module for module in sorted(KNOWN_REPO_WIDE_MODULES) if not (_REPO_ROOT / module).is_file()]
    assert not missing, f"known repo-wide modules no longer exist: {missing}"
    modules, _functions = _repository_marks()
    unmarked = sorted(KNOWN_REPO_WIDE_MODULES - modules)
    assert not unmarked, "known repo-wide modules lost their module-level repo_wide marker:\n" + "\n".join(unmarked)


def test_known_repo_wide_functions_carry_the_marker() -> None:
    missing = sorted(
        {
            row.partition("::")[0]
            for row in KNOWN_REPO_WIDE_FUNCTIONS
            if not (_REPO_ROOT / row.partition("::")[0]).is_file()
        }
    )
    assert not missing, f"known repo-wide modules no longer exist: {missing}"
    _modules, functions = _repository_marks()
    unmarked = [row for row in KNOWN_REPO_WIDE_FUNCTIONS if row not in functions]
    assert not unmarked, (
        "known repo-wide tests are not collected with a function- or class-level repo_wide mark "
        "(renamed, unmarked, or now covered by a module marker):\n" + "\n".join(unmarked)
    )


def test_every_marked_test_has_a_registry_row() -> None:
    """The registry is complete: a marked test without a row fails (#9434).

    The two checks above only follow registry rows to their markers, so a
    deleted row used to pass. This check walks pytest's marks back to the rows.
    It reads the prefiltered collection; the ``slow`` exact check below reads all.
    """
    unregistered = _unregistered_repo_wide_nodes(
        _repository_marks(), KNOWN_REPO_WIDE_MODULES, KNOWN_REPO_WIDE_FUNCTIONS
    )
    assert not unregistered, (
        "These tests carry the repo_wide marker but have no row in KNOWN_REPO_WIDE_MODULES "
        "(module-level marker) or KNOWN_REPO_WIDE_FUNCTIONS (function or class marker). "
        "Add the row:\n" + "\n".join(unregistered)
    )


def test_removing_any_registry_row_fails_the_completeness_check() -> None:
    """Every row is load-bearing: dropping it is reported, and only it is reported."""
    marked = _repository_marks()
    rows = sorted(KNOWN_REPO_WIDE_MODULES) + list(KNOWN_REPO_WIDE_FUNCTIONS)
    assert len(rows) == len(set(rows)), "a registry row is listed twice"
    for row in rows:
        unregistered = _unregistered_repo_wide_nodes(
            marked,
            KNOWN_REPO_WIDE_MODULES - {row},
            [function for function in KNOWN_REPO_WIDE_FUNCTIONS if function != row],
        )
        assert unregistered == [row], f"removing {row} reported {unregistered}"


def _registry_drift(
    marked: tuple[frozenset[str], frozenset[str]],
    known_modules: Collection[str],
    known_functions: Collection[str],
) -> tuple[list[str], list[str]]:
    """Marked tests without a registry row, and registry rows without a marked collected test."""
    modules, functions = marked
    stale = sorted((set(known_modules) - modules) | (set(known_functions) - functions))
    return _unregistered_repo_wide_nodes(marked, known_modules, known_functions), stale


def _drift_report(unregistered: list[str], stale: list[str]) -> str:
    sections = []
    if unregistered:
        sections.append(
            "Marked repo_wide but missing from KNOWN_REPO_WIDE_MODULES (module-level marker) or "
            "KNOWN_REPO_WIDE_FUNCTIONS (function or class marker); add the row:\n" + "\n".join(unregistered)
        )
    if stale:
        sections.append(
            "Registry rows with no collected test carrying that repo_wide mark (renamed, removed, "
            "unmarked, or now covered by a module marker); fix or remove the row:\n" + "\n".join(stale)
        )
    return "\n\n".join(sections)


def _selected_node_ids(marker: str, module: str) -> list[str]:
    """Node ids ``pytest -m <marker> <module>`` selects, from a collection-only child.

    ``--verbosity=-1`` overrides the config's ``-v``, so pytest lists one node id per line.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "--verbosity=-1",
            "-p",
            "no:cacheprovider",
            "-m",
            marker,
            module,
        ],
        cwd=_REPO_ROOT,
        env=_child_env(),
        capture_output=True,
        text=True,
        timeout=_COLLECT_TIMEOUT_S,
    )
    selected = [line for line in result.stdout.splitlines() if line.startswith(f"{module}::")]
    # Exit 5 is "no tests collected", here because ``-m`` deselected all of them.
    assert result.returncode == (0 if selected else 5), (result.stdout + result.stderr)[-4000:]
    return selected


def test_exact_check_is_outside_the_repo_wide_selection() -> None:
    """``pytest -m repo_wide`` (worker pre-push) never selects the whole-suite collection (#9434)."""
    assert _selected_node_ids(_MARK_NAME, _EXACT_CHECK_MODULE) == []
    assert _selected_node_ids("slow", _EXACT_CHECK_MODULE) == [_EXACT_CHECK]
    assert _EXACT_CHECK_MODULE not in KNOWN_REPO_WIDE_MODULES


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
        refused = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
            cwd=_REPO_ROOT,
            env=_child_env(),
            capture_output=True,
            text=True,
            timeout=_COLLECT_TIMEOUT_S,
        )
    finally:
        os.close(fd)
    assert marked == (frozenset({"tests/test_hooks_executable.py"}), frozenset())
    assert refused.returncode != 0
    assert FULL_SUITE_BUSY in refused.stdout + refused.stderr


def test_registry_drift_names_each_missing_and_stale_row() -> None:
    marked = (frozenset({"tests/test_m.py"}), frozenset({"tests/test_f.py::test_a", "tests/test_f.py::test_b"}))
    unregistered, stale = _registry_drift(
        marked,
        {"tests/test_gone.py", "tests/test_f.py"},
        ["tests/test_f.py::test_a", "tests/test_m.py::test_inside", "tests/test_f.py::test_renamed"],
    )
    assert unregistered == ["tests/test_f.py::test_b", "tests/test_m.py"]
    assert stale == [
        "tests/test_f.py",
        "tests/test_f.py::test_renamed",
        "tests/test_gone.py",
        "tests/test_m.py::test_inside",
    ]
    report = _drift_report(unregistered, stale)
    assert all(row in report for row in unregistered + stale)
    assert _registry_drift(marked, ["tests/test_m.py"], sorted(marked[1])) == ([], [])


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


# Shapes the prefilter misses (review-9434-b); the exact check must find each.
_PREFILTER_BLIND_SPOTS = {
    "conftest hook marks a test outside its directory": (
        {
            "tests/marked/conftest.py": """
                import pytest

                def pytest_collection_modifyitems(items):
                    for item in items:
                        if item.name == "test_plain":
                            item.add_marker(pytest.mark.repo_wide)
                """,
            "tests/marked/test_seed.py": "def test_seed():\n    ...\n",
            "tests/test_plain.py": "def test_plain():\n    ...\n",
        },
        (frozenset(), frozenset({"tests/test_plain.py::test_plain"})),
    ),
    "marked base class through an aliased dynamic import": (
        {
            "tests/scan_base.py": """
                import pytest

                class ScanBase:
                    @pytest.mark.repo_wide
                    def test_inherited(self):
                        ...
                """,
            "tests/test_inherit.py": """
                from importlib import import_module as load

                class TestScan(load("scan_base").ScanBase):
                    pass
                """,
        },
        (frozenset(), frozenset({"tests/test_inherit.py::TestScan.test_inherited"})),
    ),
    "marker name from a runtime expression": (
        {
            "tests/test_plain.py": """
                import pytest

                pytestmark = getattr(pytest.mark, "repo" + "_wide")

                def test_plain():
                    ...
                """,
        },
        (frozenset({"tests/test_plain.py"}), frozenset()),
    ),
}


@pytest.mark.parametrize("shape", sorted(_PREFILTER_BLIND_SPOTS))
def test_exact_collection_finds_marks_the_prefilter_misses(tmp_path: Path, shape: str) -> None:
    files, expected = _PREFILTER_BLIND_SPOTS[shape]
    (tmp_path / "pytest.ini").write_text("[pytest]\nmarkers =\n    repo_wide: test marker\n", encoding="utf-8")
    for relative, source in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source), encoding="utf-8")
    marked = _collect_repo_wide_marks(tmp_path, sorted(tmp_path.rglob("test_*.py")))
    assert marked == expected
    # An empty registry names the mark as unregistered; a registry of a removed test names it stale.
    assert _registry_drift(marked, (), ()) == (sorted(expected[0] | expected[1]), [])
    assert _registry_drift(marked, expected[0], [*expected[1], "tests/test_plain.py::test_gone"]) == (
        [],
        ["tests/test_plain.py::test_gone"],
    )


def test_prefilter_follows_imports_conftests_packages_and_global_plugins(tmp_path: Path) -> None:
    sources, test_files = _write_synthetic_tree(tmp_path)
    relative = {path.relative_to(tmp_path).as_posix() for path in _candidate_test_files(tmp_path, sources, test_files)}
    # Imported base class and conftest subtree reach files that never name the marker.
    assert {"tests/test_inherit.py", "tests/marked/test_plain.py"} <= relative
    assert "tests/test_unrelated.py" not in relative

    package = tmp_path / "tests" / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("import pytest\nMARK = pytest.mark.repo_wide\n", encoding="utf-8")
    (package / "test_inside.py").write_text("def test_z():\n    ...\n", encoding="utf-8")
    plugin = tmp_path / "plugins" / "global_marks.py"
    plugin.parent.mkdir()
    plugin.write_text("from pkg import MARK\n", encoding="utf-8")
    sources, test_files = sorted(tmp_path.rglob("*.py")), sorted(tmp_path.rglob("test_*.py"))
    relative = {path.relative_to(tmp_path).as_posix() for path in _candidate_test_files(tmp_path, sources, test_files)}
    assert "tests/pkg/test_inside.py" in relative
    assert "tests/test_unrelated.py" not in relative
    assert _candidate_test_files(tmp_path, sources, test_files, {"global_marks"}) == frozenset(test_files)


@pytest.mark.parametrize(
    "source",
    [
        "# repo_wide\nx = 1\n",
        '"""pytest.mark.repo_wide is described here."""\n',
        'BOUNDED_MARKERS = frozenset({"repo_wide"})\n',
        'def test_allowlist():\n    assert "repo_wide" in BOUNDED_MARKERS\n',
        'MARKERS = ["repo_wide", "slow"]\n',
        'SOURCE = "@pytest.mark.repo_wide\\ndef test_fixture(): pass"\n',
        "x = 1\n",
    ],
)
def test_marker_naming_ignores_inert_strings(source: str) -> None:
    assert not _names_the_marker(source)


@pytest.mark.parametrize(
    "source",
    [
        "import pytest as pt\nmark = pt.mark.repo_wide\n",
        "from pytest.mark import repo_wide\n",
        "@pytest.mark.repo_wide\ndef test_planted(): pass\n",
        "pytestmark = [pytest.mark.repo_wide]\n",
        'mark = getattr(pytest.mark, "repo_wide")\n',
        'mark = getattr(pytest.mark, "repo" "_wide")\n',
        'item.add_marker("repo_wide")\n',
        'item.add_marker(marker="repo_wide")\n',
        'mark = pytest.Mark(name="repo_wide", args=(), kwargs={})\n',
        'config.addinivalue_line("markers", "repo_wide: whole-tree scanner")\n',
        "@pytest.mark.repo_wide\ndef test_broken(\n",
    ],
)
def test_marker_naming_keeps_authoring_and_registration(source: str) -> None:
    assert _names_the_marker(source)


def test_prefilter_allowlist_plugin_does_not_hide_a_planted_marker(tmp_path: Path) -> None:
    """A global plugin's inert marker name must not widen collection to all tests."""
    sources, test_files = _write_synthetic_tree(tmp_path)
    plugin = tmp_path / "plugins" / "dispatch_cap.py"
    plugin.parent.mkdir()
    plugin.write_text('BOUNDED_MARKERS = frozenset({"repo_wide"})\n', encoding="utf-8")
    planted = tmp_path / "tests" / "test_planted.py"
    planted.write_text("import pytest\n@pytest.mark.repo_wide\ndef test_planted(): pass\n", encoding="utf-8")
    candidates = _candidate_test_files(tmp_path, [*sources, plugin, planted], [*test_files, planted], {plugin.stem})
    assert planted in candidates
    assert tmp_path / "tests" / "test_unrelated.py" not in candidates
    assert tmp_path / "tests" / "test_mention_only.py" not in candidates
    marked = _collect_repo_wide_marks(tmp_path, candidates)
    assert "tests/test_planted.py::test_planted" in marked[1]
    assert "tests/test_planted.py::test_planted" in _unregistered_repo_wide_nodes(marked, (), ())


@pytest.mark.parametrize("relative", ["scripts/ci/pytest_dispatch_cap.py", "tests/ci/test_pytest_dispatch_cap.py"])
def test_dispatch_cap_allowlist_is_not_a_marker_source(relative: str) -> None:
    source = (_REPO_ROOT / relative).read_text(encoding="utf-8")
    assert not _names_the_marker(source)


def test_not_repo_wide_entries_are_justified() -> None:
    """The escape hatch stays honest: real node, real reason, still a scanner."""
    known = set(KNOWN_REPO_WIDE_MODULES) | set(KNOWN_REPO_WIDE_FUNCTIONS)
    for node_id, reason in NOT_REPO_WIDE.items():
        assert reason.strip(), f"{node_id}: a NOT_REPO_WIDE entry needs a reason"
        assert node_id not in known, f"{node_id}: cannot be both repo-wide and NOT_REPO_WIDE"
        module_rel, _, function = node_id.partition("::")
        module = _REPO_ROOT / module_rel
        assert module.is_file(), f"{node_id}: module {module_rel} no longer exists"
        functions, implicated, module_sites = _cached_scan_facts(str(module), module.read_text(encoding="utf-8"))
        if function:
            assert function in functions, f"{node_id}: function no longer exists"
            assert function in implicated, f"{node_id}: no longer looks like a repo scanner; remove the stale entry"
        else:
            assert module_sites, f"{node_id}: no longer has a module-level repo scan; remove the stale entry"


def test_cached_scan_facts_recompute_after_source_changes() -> None:
    first = "def test_scan():\n    pass\n"
    second = "def test_changed():\n    pass\n"
    assert "test_scan" in _cached_scan_facts("changed.py", first)[0]
    assert "test_changed" in _cached_scan_facts("changed.py", second)[0]
    assert "test_scan" not in _cached_scan_facts("changed.py", second)[0]


def test_scan_renders_shared_bindings_once_without_caching_classification(monkeypatch: pytest.MonkeyPatch) -> None:
    tree = _synthetic(
        """
        later = base / "scripts"
        base = ROOT

        def test_first():
            later.rglob("*.py")

        def test_second():
            later.glob("*.py")
        """
    )
    original = ast.unparse
    rendered: list[ast.AST] = []

    def record(node: ast.AST) -> str:
        rendered.append(node)
        return original(node)

    # These module bindings are rendered once for module root discovery, then
    # once for the entire function scan, rather than once per test/iteration.
    monkeypatch.setattr(ast, "unparse", record)
    assert set(_implicated_test_functions(tree)) == {"test_first", "test_second"}
    binding = tree.body[0].value
    assert rendered.count(binding) == 3  # two root-discovery iterations, one shared render

    # Mutating the same AST and rescanning must render and classify it afresh.
    tree.body[1].value = ast.Name(id="tmp_path", ctx=ast.Load())
    assert _implicated_test_functions(tree) == {}


def test_scanner_guard_detects_marker_removal_and_restoration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    module = tests / "test_scanner.py"
    scanner = 'def test_scan():\n    (REPO / "scripts").rglob("*.py")\n'
    marked = "import pytest\npytestmark = pytest.mark.repo_wide\n" + scanner
    module.write_text(marked, encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(sys.modules[__name__], "_TESTS_ROOT", tests)
    test_repo_tree_scanners_carry_the_marker()
    module.write_text(scanner, encoding="utf-8")
    with pytest.raises(AssertionError, match=re.escape("tests/test_scanner.py::test_scan")):
        test_repo_tree_scanners_carry_the_marker()
    module.write_text(marked, encoding="utf-8")
    test_repo_tree_scanners_carry_the_marker()


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


def test_heuristic_prefilter_keeps_module_bound_git_argv() -> None:
    source = textwrap.dedent(
        """
        import subprocess

        GIT_CMD = ["git", "ls-files", "*.py"]

        def test_scan():
            subprocess.run(GIT_CMD, capture_output=True, check=True)
        """
    )
    assert _could_contain_scan(source)
    assert "test_scan" in _implicated_test_functions(ast.parse(source), source)


def test_heuristic_prefilter_keeps_split_git_argv_literal() -> None:
    source = textwrap.dedent(
        """
        import subprocess

        def test_scan():
            subprocess.run(["git", "ls-fi" "les", "*.py"], capture_output=True, check=True)
        """
    )
    assert _could_contain_scan(source)
    assert "test_scan" in _implicated_test_functions(ast.parse(source), source)


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
