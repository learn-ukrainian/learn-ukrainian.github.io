# OO-50 / #11226 test prune

Status: PR #11329 coverage restore round, 2026-10-21. The final selection removes
**9,466 test functions and 49 parametrize cases**.
This round restores **5,444 functions** present in the earlier deletion set.
The final `tests/` collection contains **92,567 items**. The phase A and original
phase B reports below are historical counts, not the current selection.

## Restore round for PR #11329

Ties go to keep. The critical review found that the deleted
`tests/publish/test_merge_guard.py::test_empty_json_check_list_with_exit_code_1_is_refused`
was the sole test of refusal when `gh` exits 1 with an empty checks list. The earlier
recheck also found sole branch coverage among both tie-break and unanimous deletions.
This round applies the prescribed R1-R3 keep rules without new model votes.

- [Final selection](2026-10-21-public-selection-final.jsonl): the remaining deletions.
- [Restore manifest](2026-10-21-restore-r2.jsonl): one node id and rule per row.
  A node matching several rules has several rows. Earlier phase B keeps remain kept.

| Keep rule | Matching rows | Newly restored functions, including overlaps | Newly restored functions, R1 then R2 then R3 |
| --- | ---: | ---: | ---: |
| R1: every tie-break deletion | 3,670 | 3,609 | 3,609 |
| R2: security- or Ukrainian-named file | 2,627 | 2,552 | 1,823 |
| R3: blocker and the named branch coverage | 33 | 30 | 12 |

The manifest covers 5,562 unique rows. Some were already kept or no
longer exist on current main. R2 uses the prescribed fallback regex, case-insensitive
against the entire file path:

```text
secur|secret|opsec|guard|admission|ownership|sandbox|hook|credential|auth|publish|merge|gate|refus|ukrain|vesum|stress|sources|linguist|lexic|pravopys
```

The report's original executable filename definition was not found in the available
phase A/B scripts or documentation. This fallback matches 1,880 unanimous
rows and 747 tie-break rows. It does not reproduce the earlier report's 1,247-row pool.

| Function deletion reconciliation | Count |
| --- | ---: |
| Actually absent at the original PR head `de5b87090c7` | 14,911 |
| Old selected function already removed upstream | 1 |
| Newly restored by R1-R3 | 5,444 |
| Remaining in the final selection | 9,466 |

The upstream removal is
`tests/test_ruff_ci_scope.py::test_pre_commit_cheap_guards_configuration`.
All 72 original case selections were checked against the restored functions.
The 49 previously applied case deletions remain applicable; the 23 previously skipped
shared or generated cases stay kept.

Each of the 1,310 files containing a matched restore starts from
`origin/main`. The existing apply script reapplies only the final selection to those
files. Files without a restore keep their existing contents. Repeating reconstruction
from the same main bytes produces identical outputs. Build tests have a separate
collection because pytest skips `tests/build/` while recursing through `tests/`.

Registry rows and path lists follow surviving tests. The duration inventory drops
only files deleted by this selection. The store-access baseline, its counts and
file-count metadata are unchanged from `origin/main`. All 24 `V011_ARTIFACTS` are
byte-identical to `origin/main`; the frozen test files remain whole.

Verification: final `pytest --collect-only -q tests/`, separate build collection,
exact node-id and parameter-value comparison, the requested five test modules plus
the named R3 behavior tests, and Ruff on all changed Python files. The full suite
runs in PR CI and the merge queue. For the collection comparison, materializing
`data/projects` replaces one explicit absent-tree skip with 15 real case-state
mutation parameters. The test and its parameter helpers have identical ASTs to
`origin/main`; the comparison uses matching materialized inputs for that group.

## Phase B: original application, before this restore round

### Files

- `apply_selection.py`: the apply script, kept as a record of this one-off run. It is not
  part of the toolchain. `collect` writes node ids and parameter values, `check-covered`
  verifies the D-COVERED claims, `apply` edits `tests/`, and `verify` diffs the before and
  after collections.
- `2026-10-21-phase-b-restores.jsonl`: the 118 selected entries phase B keeps (107 tests and
  11 whole files), one row each with its source and reason.
- `2026-10-21-phase-b-recheck-sample.jsonl`: the 65 recheck-sample decisions.

### Method

1. Collect `tests/` and `tests/build` on the base. `tests/build` needs its own pass because
   pytest's default `norecursedirs` skips any directory named `build`.
2. Check the D-COVERED claims (the phase A residual). Each sibling a reason names was
   resolved on the current tree: exact name first, then a unique fuzzy match in the same
   file, then the same name anywhere. A deletion stands if a named sibling is kept, or if it
   reaches a kept test or a deletion of another class through other D-COVERED deletions.
   - Rows whose named sibling exists nowhere: 81. Of these, 65 had no independent delete
     vote of another class and were restored.
   - Deletions that only cover each other: 65, in 28 chains. One member per chain was
     restored (15). In the other 13 chains every member had an independent delete vote.
3. Recheck sample (below): 14 restores.
4. `apply` works on the AST with exact line spans:
   - It removes each selected function with its decorators and the comment lines directly
     above it.
   - It removes a selected parametrize case only when the case is a literal entry, matched
     by value against the collected parameters, and every collected case sharing that entry
     is selected.
   - It removes test classes left with no tests, and deletes a file whose every collected
     test is selected unless a surviving file imports it.
   - It removes helpers, fixtures and constants that were referenced before the apply
     (in the file, or by another test file naming the module) and are referenced nowhere
     afterwards: 773 definitions and 553 emptied classes. Then
     `ruff check --fix --select F401,F811,F841` and `--select I` run on the touched files.
   - It skips a selected test that kept code still calls or imports, a test that no longer
     exists, an inherited test, and any removal that would also remove an unselected test.
5. Keep what something outside the selection depends on. The original application edited nothing outside
   `tests/` and `docs/test-prune/`, and the first CI run showed each of these breaking:
   - Six files are kept whole because tooling pins or runs them by path:
     - `scripts/ci/linux_fs_parity.sh` runs `test_hooks_executable.py`;
     - `scripts/ci/components.json` runs `test_makefile_practice_admit.py`;
     - the npm script `test:pedagogy` runs `test_pedagogy.py`;
     - the ua_eval v0.1.1 release freeze pins the sha256 of `test_ua_eval_model_runner.py`
       and `test_ua_eval_public_v011.py`;
     - kept `test_dispatch_checkout_size.py` infers the sparse trees of
       `test_landings_use_levellanding.py` from its text.
   - Five files are kept whole because a rule, contract or schema names them as its
     enforcing test: `test_no_rewrite_contract.py`, `test_rules_core_structural_coverage.py`,
     `test_source_clis_entrypoint.py`, `test_grammar_lexical_schemas.py` and
     `test_contract_reference_sync.py`.
   - Thirteen single tests are kept:
     - two that are run by node id, by a kept test and by the required Checks job
       in `.github/workflows/ci.yml`;
     - one named as resume evidence in the curriculum-lifecycle pilot matrix;
     - one holding a sqlite reference that `scripts/hygiene/sqlite_reference_allowlist.json`
       counts;
     - seven whose store access `scripts/hygiene/store_access_baseline.json` records (the
       source-db lint fails on a baseline row whose test is gone);
     - one whose text a kept checkout-size test anchors on;
     - one restored by cross-family review finding R1.
6. Separate commit: drop the `repo_wide` registry rows (`KNOWN_REPO_WIDE_MODULES`,
   `KNOWN_REPO_WIDE_FUNCTIONS`, `NOT_REPO_WIDE`) and the path-list entries that name deleted
   tests.
7. Verify: `pytest --collect-only` over `tests/` and over `tests/build` both pass with 0
   errors. `apply_selection.py verify` reports 0 problems: every deleted function is gone,
   no unselected node id changed, and each case-pruned function lost exactly its selected
   cases, compared by the multiset of collected parameter values (review finding R2). The
   source-db lint (`lint_source_db_writable_connects.find_violations`) reports 0 violations, and
   every count pinned in `scripts/hygiene/sqlite_reference_allowlist.json` matches. `ruff check scripts/ tests/ agents_extensions/ dashboards/ docs/test-prune/` is
   clean. No test was run locally (OO-55); CI runs the full suite.

`scripts/ci/pytest-file-durations.json` was unchanged in the original application. No check requires it to match the tree:
`tests/test_ci_split.py` states that stale entries only cost shard balance. The deleted files
account for 3,093.3 s of the 30,250.8 s snapshot.

### Counts

| | Functions | Cases |
| --- | ---: | ---: |
| Selected in phase A | 15,102 | 72 |
| Restored: D-COVERED claim names no existing sibling | 65 | |
| Restored: D-COVERED chain covering no kept test | 15 | |
| Restored: recheck sample | 14 | |
| Restored: a kept test, hook or pinned config depends on it | 12 | |
| Restored: cross-family review finding | 1 | |
| Kept: whole file pinned by tooling or kept tests (6 files) | 11 | |
| Kept: whole file a rule, contract or schema cites (5 files) | 36 | |
| Skipped: no longer on main (moved or removed since phase A) | 29 | |
| Skipped: kept code still calls it | 6 | |
| Skipped: generated, not defined at its path | 1 | |
| Skipped: case is not a removable literal entry | | 23 |
| **Deleted** | **14,912** | **49** |

Of the 40,428 test functions on the base, 25,516 remain. 1,863 files were edited and 191
were deleted. One file, `tests/common/test_test_thread_caps.py`, has no tests left but is
kept because two other test files import its `EXPECTED` table.

### Delete share by directory (functions on the base)

| Directory | Before | Deleted | Share |
| --- | ---: | ---: | ---: |
| `tests/` (root files) | 25,777 | 10,258 | 39.8% |
| `projects/` | 2,302 | 624 | 27.1% |
| `orchestration/` | 2,277 | 520 | 22.8% |
| `agent_runtime/` | 1,665 | 499 | 30.0% |
| `build/` | 1,382 | 599 | 43.3% |
| `api/` | 1,041 | 431 | 41.4% |
| `review/` | 952 | 295 | 31.0% |
| `audit/` | 878 | 375 | 42.7% |
| `curriculum/` | 853 | 288 | 33.8% |
| `ai_agent_bridge/` | 498 | 152 | 30.5% |
| `ci/` | 447 | 173 | 38.7% |
| `hygiene/` | 282 | 68 | 24.1% |
| `wiki/` | 237 | 126 | 53.2% |
| `eval/` | 194 | 66 | 34.0% |
| `opsec/` | 157 | 44 | 28.0% |
| 27 smaller directories | 1,486 | 394 | 26.5% |

### Recheck sample (phase A residual)

The sample was drawn with seed 11226 and checked by three independent Claude Opus 5.5 reviewers
(22, 22 and 21 tests). It has two parts:
- 40 tie-break deletions where a vote was K-A, K-B, K-D or K-F (from 2,906 such rows);
- 25 unanimous deletions in files whose name is security- or Ukrainian-language-related
  (from 1,247 such rows).

A test was restored only if, after the prune, it would be the sole test of a reachable,
non-trivial branch and it asserts that branch's outcome.

Result: **14 of 65 restored**. That is 10 of 40 tie-breaks (25%) and 4 of 25 unanimous
deletions (16%).

| Sample | Test | Decision | Reason |
| --- | --- | --- | --- |
| tie-break | `test_generate_practice_deck.py::test_imperative_fixture_integration_includes_index_and_counts` | restore | only test that build_practice_shards emits imperative cards; the named sibling's fixture VESUM has no imperative forms |
| tie-break | `test_delegate_deleted_base.py::test_exempt_change_check_resolves_when_base_present_or_fallback_available` | delete | base states covered by kept test_resolve_merge_base_four_states; exempt-check outcome by kept test_squash_merge_overcount_recorded_commit_vs_default_fallback |
| tie-break | `ci/test_check_agent_attribution.py::test_attribution_never_needs_to_be_the_last_paragraph` | delete | same shape and pass outcome as kept test_commit_messages_shape_passes_for_a_chain |
| tie-break | `control_plane/test_component_interlock.py::test_request_executor_pg_unreachable_fails_closed` | delete | allow branch covered by kept test_plane_status_reports_real_pg_failure_not_component_refusal; typed connect failure by kept test_storage.py::test_pg_unreachable_dsn_fails_closed_quickly_no_sqlite |
| tie-break | `test_bakeoff_run.py::test_bakeoff_run_preflight_accepts_fixture_plan` | delete | _preflight happy path runs inside kept test_bakeoff_run_invokes_write_and_review_steps_in_order |
| tie-break | `projects/open_model_data/test_quarantine.py::test_archive_import_guard_active_code` | delete | repo AST scan of tracked files; reaches no production branch |
| tie-break | `test_audit_helpers.py::TestFixErrorCorrectionItems::test_rename_text_to_sentence` | restore | its sibling is deleted too, leaving fix_error_correction_items (reachable from fix_activity_violations) with no test |
| tie-break | `test_model_catalog.py::test_retired_astra_holds_no_activity_role` | delete | retired refusal covered by kept test_retired_model_refusal_names_id_and_replacement; only the wording differs |
| tie-break | `test_fleet_comms_message_plane.py::test_gemini_opens_as_agy_on_plane` | delete | pass-through to create_request; gemini-to-agy resolution kept in test_fleet_comms_wave1.py::test_request_executor_gemini_retires_to_agy_and_completes |
| tie-break | `api/test_occupancy_local.py::test_linux_empty_map_attaches_session_stream_drivers_to_host_teacher` | restore | only test of the Linux empty-map fallback in driver_seat_host_id; the named sibling uses a non-empty map |
| tie-break | `orchestration/test_install_archived_thread_cleanup_launchd.py::test_status_rejects_loaded_plist_that_does_not_run_cleanup_code` | delete | same arguments[0] check and rc 1 outcome as kept test_status_rejects_venv_python_as_program |
| tie-break | `test_plan_validation.py::TestValidatePlan::test_missing_outline` | delete | an empty outline is still refused without this branch; only the message differs; kept test_outline_sum_mismatch covers the refusal |
| tie-break | `test_ci_cache_hygiene.py::test_uv_entries_on_other_refs_are_left_alone` | restore | only test of the main-ref guard on setup-uv cache entries; without it PR-ref caches would be deleted |
| tie-break | `eval/test_zno_nmt_core.py::test_missing_invalid_and_failed_trials_are_explicit` | restore | all score_run tests are deleted; only test of the failed-run branch (scores None, not 0) and missing vs invalid counts |
| tie-break | `test_slug_utils.py::TestToBareSlag::test_three_digit_prefix` | delete | regex quantifier constant, no code branch (note: to_bare_slug keeps no direct test) |
| tie-break | `audit/test_wiki_coverage_gate_fix_proposals.py::test_unresolved_location_surfaces_substance_failure_with_proposal` | delete | same whole-text path as location 'whole file'; substance FAIL kept in test_wiki_coverage_integration_m20_scenario |
| tie-break | `test_session_identity_env_isolation.py::test_identity_variable_is_absent_inside_tests` | delete | test-harness check; the strip mechanism is kept in test_isolation_runs_before_every_fixture_and_restores_after |
| tie-break | `test_mcp_sources_server.py::TestWikipediaExtractPaging::test_pages_concatenate_and_do_not_split_the_cyrillic_word` | restore | only remaining test of the paragraph/sentence cut branch and lossless page concatenation |
| tie-break | `test_wiki_enrichment.py::TestSourceBudgeting::test_limits_background_sources_before_primary` | restore | only test of the background-source caps in _cap_source_chunks |
| tie-break | `test_atlas_preview_release_fixture.py::test_frozen_producer_is_independent_of_the_live_producer` | delete | checks fixture tooling, not production; byte contract kept in test_producer_generated_release |
| tie-break | `projects/open_model_data/test_a10_pilot_review_gate.py::test_a10_receipt_never_claims_a_review_was_executed_or_a_self_review_occurred` | delete | receipt flags asserted by kept test_a10_receipt_eligibility_all_false_and_zero_rows_emitted |
| tie-break | `curriculum/validate/test_placement_table.py::test_schema_activity_types_rejects_missing_file` | delete | generation fails either way, only the exception type differs; fail-closed parsing kept in test_load_placement_table_rejects_malformed_file |
| tie-break | `test_sum20_lookup.py::test_reader_import_does_not_load_a_network_client` | delete | static import check; runtime no-network behaviour kept in test_unknown_lemma_is_a_local_miss |
| tie-break | `test_audit_helpers.py::TestComputeOverallStatus::test_all_pass` | restore | every compute_overall_status test is deleted; only test of the pass branch and pass_count written to status JSON |
| tie-break | `test_open_model_phase3_school_parent_section_context.py::test_verify_existing_rejects_schema_binding_mutation` | delete | same mutate-rehash-refuse path as kept test_verify_existing_rejects_implementation_binding_mutation |
| tie-break | `test_mcp_sources_load.py::test_timed_out_calls_keep_counting_against_the_bound` | delete | wall-clock load test; slot retention kept timer-free in tests/rag/test_call_governor.py |
| tie-break | `api/test_routing_budget.py::test_authenticated_cursor_with_fleet_burn_and_empty_codexbar` | delete | authenticated cursor branch kept in test_code_worker_recommendation.py::test_producer_passes_observed_load_to_shared_order |
| tie-break | `projects/open_model_data/test_v4_validation_session_contract.py::test_every_decorated_packaged_validator_is_annotated_none` | delete | source-scan twin; refusal kept in test_validation_session_refuses_a_value_returning_validator |
| tie-break | `curriculum/evidence/test_reference_sense.py::test_atom_provenance_rederived_and_missing_index_refused` | delete | missing atom_index takes the tampered-binding path kept in test_public_binding_mutations_withhold[atom_index] |
| tie-break | `audit/test_module_quality_audit.py::test_planned_modules_use_manifest_order_and_profiles` | delete | order and counts kept in test_audit_modules_reports_surface_and_llm_qg_coverage; the rest is a label mapping |
| tie-break | `test_coverage_api_routers.py::TestCommsConversationDetail::test_conversation_detail` | delete | SQL filter on a deprecated legacy route still reached by kept tests/test_legacy_comms_telemetry.py |
| tie-break | `common/test_jsonl_readers_open_model_data.py::test_reader_preserves_unicode_separators` | delete | second test of #9556; kept test_jsonl_splitlines_guard.py and test_jsonl_readers_ai_agent_bridge.py cover it |
| tie-break | `trails/test_rb2_rb5_v11.py::test_migrated_trails_validate_v11` | delete | kept test_validate_trailspec.py::test_every_shipped_trail_validates validates rb2 and rb5 |
| tie-break | `projects/open_model_data/test_v4_build_assets.py::test_head_and_ancestor_commit_overrides_are_accepted` | delete | accept path runs in the built_wheel fixture of kept tests (note: its refusal branches lose all coverage) |
| tie-break | `test_fetch_ulif_homonyms.py::test_install_sigterm_handler_reports_c_previous_handler_as_installed` | delete | covered end to end by kept test_main_unblocks_sigterm_when_previous_handler_is_none (#10393) |
| tie-break | `test_wiki_coverage_gate.py::test_parse_implementation_map_inline_field_order_independence` | delete | same regex line path as kept test_parse_implementation_map_collects_all_blocks_and_inline_format |
| tie-break | `test_issue_stream_audit.py::test_read_membership_index_rejects_malformed_open_numbers` | restore | only test of the separate open-issue-numbers refusal in read_membership_index |
| tie-break | `test_agent_runtime_effort.py::test_run_worker_forwards_effort_to_runtime_invoke` | delete | mock-call mirror; per-adapter effort rendering kept in test_claude_adapter_emits_effort_when_supported |
| tie-break | `test_monitor_client_sdk.py::test_sdk_bootstrap_returns_both_components` | delete | bootstrap shape kept in test_research_registry_p3.py::test_bootstrap_role_only_routes_to_cold_start_never_and_manifest |
| tie-break | `test_check_node_modules_integrity.py::test_alert_event_names_running_dispatches` | restore | all three twins of the running-dispatch lookup (status plus live-pid filter) are deleted; one kept |
| unanimous | `test_secret_redaction.py::test_conftest_redacts_warning_source_line` | restore | only test of secret redaction on a warning's source line; the kept test has the secret only in the message |
| unanimous | `test_coverage_lexical_sandbox.py::TestExtractCase::test_accusative` | delete | one loop path; kept TestExtractCase::test_nominative and test_no_case cover found and not-found |
| unanimous | `test_sum11_source_guard.py::test_approved_contrast_only_line_is_exempt` | delete | exact-line exemption kept in test_preview_exclusion_only_exempts_the_exact_line |
| unanimous | `test_lexical_sandbox.py::TestPrioritizeVerbForms::test_deduplicates` | delete | set() de-duplication, no branch (note: _prioritize_verb_forms keeps no direct test) |
| unanimous | `test_gemini_adapter_auth.py::TestCooldownPrimitives::test_inactive_by_default` | delete | missing-state-file branch covered by kept TestCooldownPrimitives::test_clear |
| unanimous | `test_mcp_sources_server.py::TestHealthEndpoint::test_git_commit_failure_is_unknown` | delete | diagnostic fallback string; /health contract kept in test_handle_health_response |
| unanimous | `orchestration/test_tmp_leak_sweep.py::test_name_patterns_match_known_leaks` | restore | only test that unrelated old self-owned /tmp names are not sweep candidates; both covering siblings are deleted too |
| unanimous | `test_mcp_sources_load.py::test_health_stays_under_one_second_while_saturated` | delete | wall-clock latency bound; concurrency cap kept in tests/rag/test_call_governor.py |
| unanimous | `test_pg_skip_guard.py::test_postgres_files_are_found_in_the_repo` | restore | the whole file is deleted, leaving the CI postgres skip guard's file discovery with no test |
| unanimous | `test_guard_branch_switch_in_main.py::test_issue_9479_r7_missing_terminator_fails_closed` | delete | same unterminated-heredoc fail-closed path as kept test_issue_9479_r6_unknown_repository_branch_variants |
| unanimous | `test_lexicon_enrich_manifest.py::test_homonym_fixture_samples_expand_from_zero` | delete | same loop and VESUM gate as kept test_homonym_relations_require_numbering_and_an_exact_vesum_lemma |
| unanimous | `test_mcp_sources_server.py::TestSearchSourcesHandler::test_defaults_track_to_empty_string` | delete | mock-call mirror of default arguments; forwarding kept in test_returns_summary_and_structured_hits |
| unanimous | `test_redacted_environ.py::test_plain_mapping_repr_contains_the_value` | delete | asserts stdlib dict repr; redaction kept in test_environ_formatting_omits_values_and_lookups_keep_them |
| unanimous | `test_guard_pr_merge.py::test_unwrapped_mention_is_not_a_merge` | delete | allow side covered by kept test_xargs_operands_are_not_a_merge |
| unanimous | `test_mcp_sources_server.py::TestVerifyWordHandler::test_passes_pos_filter` | delete | mock-call mirror; not_found outcome kept in TestVerifyWordHandler::test_not_found |
| unanimous | `test_mcp_sources_server.py::TestCheckModernFormHandler::test_invalid_input_shape` | restore | only test of check_modern_form's invalid-input branch (empty/whitespace word refused before VESUM) |
| unanimous | `test_sources_db.py::TestSourcesDb::test_search_style_guide` | delete | basic headword hit covered by kept test_search_style_guide_lowercase_phrase_matches_capitalized_headword |
| unanimous | `test_sum20_lookup.py::test_reader_source_has_no_live_client` | delete | source grep; no-network behaviour kept in test_unknown_lemma_is_a_local_miss |
| unanimous | `test_guard_secret_print.py::test_override_on_heredoc_owner` | delete | early-return override covered by kept test_safe_commands_allowed; refuse direction kept in test_dump_boundaries_across_shell_scopes |
| unanimous | `test_guard_secret_print.py::test_round_six_false_positive_neighbors_allowed` | delete | allow-side neighbours covered by kept test_round_seven_neighbors_allowed and test_safe_commands_allowed |
| unanimous | `test_lexical_sandbox.py::TestPrioritizeVerbForms::test_present_before_infinitive` | delete | orders a prompt table column; formatting, not a VESUM verification branch |
| unanimous | `test_coverage_lexical_sandbox.py::TestDescribeConstraints::test_all_constraints` | delete | counts human-readable prompt strings; wording |
| unanimous | `test_wiki_sources.py::TestSlugToTopic::test_uses_discovery_keywords` | delete | builds a topic label string; no K behaviour |

### Restores and whole-file keeps other than the D-COVERED check

| Source | Test or file | Reason |
| --- | --- | --- |
| tooling-reference | `api/opsec_sweep/test_opsec_route_sweep.py::test_isolated_fixture_denies_real_database_access` | scripts/hygiene/store_access_baseline.json records this test's store access; the source-db lint fails on a baseline row whose test is gone |
| recheck-sample | `api/test_occupancy_local.py::test_linux_empty_map_attaches_session_stream_drivers_to_host_teacher` | only test of the Linux empty-map fallback in driver_seat_host_id; the named sibling uses a non-empty map |
| kept-test-reads-it | `audit/test_track_deterministic_audit.py::test_config_consumer_file_launches_without_pythonpath` | kept tests/test_dispatch_checkout_size.py anchors the a1 plan read on this test's '"plans" / "a1"' text |
| recheck-sample | `eval/test_zno_nmt_core.py::test_missing_invalid_and_failed_trials_are_explicit` | all score_run tests are deleted; only test of the failed-run branch (scores None, not 0) and missing vs invalid counts |
| recheck-sample | `orchestration/test_tmp_leak_sweep.py::test_name_patterns_match_known_leaks` | only test that unrelated old self-owned /tmp names are not sweep candidates; both covering siblings are deleted too |
| tooling-reference | `projects/open_model_data/test_v4_source_custody_access.py::test_validate_and_resolve_paths_protects_config_and_schemas_from_aliases` | scripts/hygiene/store_access_baseline.json records this test's store access; the source-db lint fails on a baseline row whose test is gone |
| tooling-reference | `test_activate_vesum_backup_ignored.py::test_backup_name_is_timestamped_beside_target` | scripts/hygiene/store_access_baseline.json records this test's store access; the source-db lint fails on a baseline row whose test is gone |
| recheck-sample | `test_audit_helpers.py::TestComputeOverallStatus::test_all_pass` | every compute_overall_status test is deleted; only test of the pass branch and pass_count written to status JSON |
| recheck-sample | `test_audit_helpers.py::TestFixErrorCorrectionItems::test_rename_text_to_sentence` | its sibling is deleted too, leaving fix_error_correction_items (reachable from fix_activity_violations) with no test |
| tooling-reference | `test_certification_evidence.py::test_certification_profile_selection_is_level_sensitive_and_unarmed` | agents_extensions/shared/curriculum-lifecycle/config/pilot-matrix.v1.yaml names it as resume evidence, which the kept pilot matrix test requires to exist |
| recheck-sample | `test_check_node_modules_integrity.py::test_alert_event_names_running_dispatches` | all three twins of the running-dispatch lookup (status plus live-pid filter) are deleted; one kept |
| recheck-sample | `test_ci_cache_hygiene.py::test_uv_entries_on_other_refs_are_left_alone` | only test of the main-ref guard on setup-uv cache entries; without it PR-ref caches would be deleted |
| kept-test-runs-it | `test_conftest_worktree_guard.py::test_real_checkout_acp_execution_does_not_mkdir_dispatch` | a kept test in the same file runs this test by node id in a child pytest |
| doc-cited-enforcement | `test_contract_reference_sync.py` | scripts/build/contracts/module-contract.md names this file as the test that enforces it; deleting it would leave that claim false, and this PR edits no rules or contracts |
| tooling-reference | `test_delegate_read_only_db_lookups.py::test_augment_prompt_with_worktree_teaches_primary_database_access` | scripts/hygiene/store_access_baseline.json records this test's store access; the source-db lint fails on a baseline row whose test is gone |
| tooling-reference | `test_deploy_pages_workflow.py::test_auto_deploy_dispositions_activity_kit_and_data_paths` | scripts/hygiene/store_access_baseline.json records this test's store access; the source-db lint fails on a baseline row whose test is gone |
| tooling-reference | `test_docs_catalogue_coverage.py::test_a_store_asked_by_its_name_and_format_ranks_its_own_record` | scripts/hygiene/store_access_baseline.json records this test's store access; the source-db lint fails on a baseline row whose test is gone |
| recheck-sample | `test_generate_practice_deck.py::test_imperative_fixture_integration_includes_index_and_counts` | only test that build_practice_shards emits imperative cards; the named sibling's fixture VESUM has no imperative forms |
| doc-cited-enforcement | `test_grammar_lexical_schemas.py` | the $comment of schemas/ua-grammar-lexical-evidence.v2.schema.json and ua-grammar-lexical-score.v2.schema.json names this file as the test that enforces it; deleting it would leave that claim false, and this PR edits no rules or contracts |
| tooling-reference | `test_hooks_executable.py` | scripts/ci/linux_fs_parity.sh (make target) runs this file by path; deleting it breaks that target and this PR edits nothing under scripts/ |
| recheck-sample | `test_issue_stream_audit.py::test_read_membership_index_rejects_malformed_open_numbers` | only test of the separate open-issue-numbers refusal in read_membership_index |
| kept-test-reads-it | `test_landings_use_levellanding.py` | kept tests/test_dispatch_checkout_size.py infers this file's sparse trees (curriculum, site/src/content, site/src/data) from its text |
| tooling-reference | `test_makefile_practice_admit.py` | scripts/ci/components.json lists it as a practice-frontend test file and verify argv; deleting it breaks component verify and this PR edits nothing under scripts/ |
| recheck-sample | `test_mcp_sources_server.py::TestCheckModernFormHandler::test_invalid_input_shape` | only test of check_modern_form's invalid-input branch (empty/whitespace word refused before VESUM) |
| recheck-sample | `test_mcp_sources_server.py::TestWikipediaExtractPaging::test_pages_concatenate_and_do_not_split_the_cyrillic_word` | only remaining test of the paragraph/sentence cut branch and lossless page concatenation; the kept test covers only the word-boundary cut |
| doc-cited-enforcement | `test_no_rewrite_contract.py` | agents_extensions/shared/rules/pipeline.md (ADR-007 no-regeneration rule) names this file as the test that enforces it; deleting it would leave that claim false, and this PR edits no rules or contracts |
| tooling-reference | `test_pedagogy.py` | package.json script test:pedagogy runs this file by path |
| recheck-sample | `test_pg_skip_guard.py::test_postgres_files_are_found_in_the_repo` | the whole file is deleted, leaving the CI postgres skip guard's file discovery with no test |
| tooling-reference | `test_readonly_harness_readers.py::test_dashboard_broker_routes_through_monitor_context` | scripts/hygiene/sqlite_reference_allowlist.json pins 4 sqlite references in this file and this test holds one |
| doc-cited-enforcement | `test_rules_core_structural_coverage.py` | agents_extensions/shared/rules/core-manifest.yaml names this file as the test that enforces it; deleting it would leave that claim false, and this PR edits no rules or contracts |
| review-finding | `test_secret_print_hook.py::test_unexpected_adapter_failure_denies` | cross-family review R1: only test of the adapter's outer exception boundary (an unexpected dependency failure must give a sanitized native denial); the named sibling only covers failures inside run_guard |
| recheck-sample | `test_secret_redaction.py::test_conftest_redacts_warning_source_line` | only test of secret redaction on a warning's source line; the kept test has the secret only in the message |
| doc-cited-enforcement | `test_source_clis_entrypoint.py` | agents_extensions/shared/rules/workflow.md names this file as the test that enforces it; deleting it would leave that claim false, and this PR edits no rules or contracts |
| tooling-reference | `test_source_db_write_guard.py::test_unrelated_audit_events_pass` | scripts/hygiene/store_access_baseline.json records this test's store access; the source-db lint fails on a baseline row whose test is gone |
| tooling-reference | `test_ua_eval_model_runner.py` | the ua_eval v0.1.1 release freeze (scripts/projects/ua_eval_harness/verify_release_freeze_v011.py) pins this file's sha256 |
| tooling-reference | `test_ua_eval_public_v011.py` | the ua_eval v0.1.1 release freeze (scripts/projects/ua_eval_harness/verify_release_freeze_v011.py) pins this file's sha256 |
| recheck-sample | `test_wiki_enrichment.py::TestSourceBudgeting::test_limits_background_sources_before_primary` | only test of the background-source caps in _cap_source_chunks |

The 80 D-COVERED-check restores are listed in `2026-10-21-phase-b-restores.jsonl`.

### Skipped selections (59)

| Test | Reason |
| --- | --- |
| `common/test_test_slots.py::test_a_pool_path_another_user_could_redirect_is_refused_before_anything_is_created[other-writable-ancestor]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/arc/test_arc_levels.py::test_every_position_has_band_key_with_full_coverage[b1]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/arc/test_arc_levels.py::test_every_position_has_band_key_with_full_coverage[b2]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/arc/test_arc_levels.py::test_position_count_and_first_last_slug[b1]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/arc/test_arc_levels.py::test_position_count_and_first_last_slug[b2]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/arc/test_arc_levels.py::test_standard_line_refs_have_no_duplicate_pairs[a2]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/arc/test_arc_levels.py::test_standard_line_refs_have_no_duplicate_pairs[b1]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/arc/test_arc_levels.py::test_standard_line_refs_have_no_duplicate_pairs[b2]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/evidence/test_words.py::test_excluding_markers_flag_learner_false[arch]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/evidence/test_words.py::test_excluding_markers_flag_learner_false[bad]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/evidence/test_words.py::test_excluding_markers_flag_learner_false[dialect]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/evidence/test_words.py::test_excluding_markers_flag_learner_false[obsc]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/evidence/test_words.py::test_excluding_markers_flag_learner_false[slang]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/evidence/test_words.py::test_excluding_markers_flag_learner_false[subst]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/evidence/test_words.py::test_excluding_markers_flag_learner_false[vulg]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `curriculum/test_plan_validate.py::test_code_registry_matches_produced_codes` | kept code still references it (helper call or import); not removed |
| `curriculum/test_plan_validate_mechanical.py::test_outcomes_name_lesson_and_step` | kept code still references it (helper call or import); not removed |
| `test_check_text.py::test_synthetic_ua_gec_one_word_whole_span` | not defined at that path (inherited or generated); not removed |
| `test_frontend_denominator_invariant.py::test_site_external_reads_are_in_frontend_denominator` | kept code still references it (helper call or import); not removed |
| `test_idle_settle.py::test_six_disposition_codes_accepted[ci_capacity]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `test_idle_settle.py::test_six_disposition_codes_accepted[dependency_blocked]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `test_idle_settle.py::test_six_disposition_codes_accepted[disk_capacity]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `test_idle_settle.py::test_six_disposition_codes_accepted[human_decision]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `test_idle_settle.py::test_six_disposition_codes_accepted[integration_wip_cap]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `test_idle_settle.py::test_six_disposition_codes_accepted[no_ready_work]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `test_idle_settle.py::test_six_disposition_codes_accepted[review_wip_cap]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `test_idle_settle.py::test_six_disposition_codes_accepted[worktree_wip_cap]` | case is not a removable literal parametrize entry (shared or generated); not removed |
| `test_kimi_coding_only_admission.py::test_a_commit_sha_holding_the_link_local_letters_is_no_host_detail` | kept code still references it (helper call or import); not removed |
| `test_playground_api_stability.py::test_playground_primary_endpoints_keep_health_fast` | kept code still references it (helper call or import); not removed |
| `test_pre_push_gate.py::test_a_detached_shadow_descendant_does_not_outlive_the_shadow` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_a_disabled_pool_changes_nothing` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_a_missing_governor_refuses_validation` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_actual_stages_each_get_their_own_allowance` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_admission_allowance_covers_a_predecessors_slot_wait` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_admission_wait_covers_one_full_gate_run` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_cost_deferral_only_touches_whole_modules_and_tolerates_missing_data` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_dedupe_node_ids_keeps_the_broader_selection_and_sorts` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_deferral_changes_the_receipt_key` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_empty_registry_literals_load_as_an_empty_registry` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_every_real_registry_node_id_is_collectable` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_explicit_ci_deferrals_name_registered_modules_without_timings` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_gate_pytest_child_thread_caps_match_helper` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_gate_thread_policy_parity` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_invariant_timing_sums_only_invocations_that_ran_the_subset` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_moving_the_base_temp_keeps_admission_budget_and_process_caps` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_pytest_defaults_to_bounded_parallelism_kept_by_file` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_pytest_preserves_dispatch_process_clamp` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_pytest_temp_parent_follows_the_fleet_scratch_convention` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_registry_class_methods_become_pytest_node_ids` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_registry_is_deduplicated_and_versioned` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_same_head_production_registry_or_selection_difference_cannot_coalesce` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_shadow_selector_unions_the_tests_of_every_affected_component` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_sparse_deferrals_name_real_registry_entries` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_the_gate_slot_wait_is_bounded_by_its_own_ceiling` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_the_real_registry_fits_the_run_budget_once_heavy_modules_are_deferred` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_the_real_registry_loads_by_ast_and_matches_the_module` | not collected on current main (moved, renamed or removed since phase A) |
| `test_pre_push_gate.py::test_the_run_budget_is_the_sum_of_the_two_stage_allowances` | not collected on current main (moved, renamed or removed since phase A) |
| `test_ruff_ci_scope.py::test_pre_commit_cheap_guards_configuration` | not collected on current main (moved, renamed or removed since phase A) |
| `test_writer_plan_projection.py::test_every_plan_projection_is_exact_raw_block_subtraction` | kept code still references it (helper call or import); not removed |

### Residuals and risks after the restore round

R1-R3 restore the tie-break deletions, every deletion matching the R2 filename rule,
and all named sole-coverage branches, including the merge-guard fail-closed blocker.
The old sample miss rates describe the superseded selection. They are not estimates
for the remaining final selection.

The remaining deletions have unanimous votes and fall outside the R2 filename rule.
This round performs no new model voting or independent whole-selection coverage
assessment. Earlier skipped cases and whole-file keeps remain kept. Historical
briefs and autopsies remain records of the earlier selection.

The #11226 driver owns exact-head independent review and same-head full CI before
landing. Local targeted checks and collection do not replace those gates.

## Phase A: selection (2026-10-21)

Status: phase A done, 2026-10-21 13:42Z. The selection marks **15,102 of 40,173 test
functions (37.6%) for deletion**, plus 72 duplicate parametrize cases inside kept
functions. Phase B (above) applied it. No file under
`tests/` or `scripts/ci/` was changed and no test was run in this phase.

### Files

- `rubric.md`: the rubric the swarm applied (t3code classes, CTO-narrowed K-C, one kept test
  per distinct behaviour, no keep catch-all).
- `2026-10-21-public-selection.jsonl`: the selection, one row per touched test file:
  `{"file", "delete": {test: class}, "delete_cases": {test[case]: class}, "restored": {test: class}}`.
  Test names are relative to the file (`Class::test_x` for class methods). Tests not listed stay.
- `2026-10-21-public-selection-detail.jsonl.gz`: one row per listed test with the reason,
  the three votes and how the verdict was reached. It is a separate gzip file because the
  repo refuses files over 2,000 KB (the uncompressed detail is 5.5 MB).

### Method

- Pass 1 and pass 2: two independent Claude Haiku 5.5 swarms. Each pass covered every collected
  test function under `tests/` (including `tests/build`, collected separately) and saw the
  whole file in context. The two passes grouped files into batches differently: pass 1 in
  path order, pass 2 shuffled. Pass 1: 185 + 7 + 1 batches; pass 2: 189 + 8 batches.
- Agreement decided 33,850 functions (22,418 keep, 11,432 delete). The other 6,323 (15.7%)
  went to a third independent Haiku vote (167 batches), which decided 3,789 delete and 2,534 keep.
- Restore pass (Claude Opus 5.5, 22 batches) over 908 deletes: every deleted test that at least one
  vote had classed K-C or K-E, plus all tests of the 8 security- or Ukrainian-named files
  the swarm had emptied. A test was restored only if it guards a real security boundary
  or Ukrainian-language rule and no kept test in its file covers the same path and
  outcome. 119 restored (55 K-C, 64 K-E), listed below.
- Parametrize cases: a single case is deleted only when both passes deleted that exact
  case id inside a kept function (72). 1,162 case deletes proposed by only one pass were
  not applied.

### Counts (final, after restores)

| Verdict | Functions | Share |
| --- | ---: | ---: |
| keep | 25,071 | 62.4% |
| delete | 15,102 | 37.6% |

| Keep class | Functions | Delete class | Functions |
| --- | ---: | --- | ---: |
| K-A orchestration / lifecycle | 7,326 | D-COVERED | 5,971 |
| K-D persistence / stores | 5,311 | D-TRIVIAL | 5,694 |
| K-C security boundary | 4,129 | D-WORDING | 1,445 |
| K-B protocol / format | 3,963 | D-TYPE | 630 |
| K-E Ukrainian-language | 2,836 | D-TIMER | 434 |
| K-F real-bug regression | 1,506 | D-MOCK | 409 |
| | | D-SMOKE | 295 |
| | | D-RETIRED | 207 |
| | | D-DUPCASE (whole function) | 17 |

Pass-level delete shares: pass 1 35.6% and pass 2 37.1% (40,173 rows each), tie-break
59.9% of the disputed rows.

### CI duration (from `scripts/ci/pytest-file-durations.json`)

- All files in the snapshot: 30,250.8 s summed across shards.
- Touched files (at least one deletion): 1,893 files, 28,969.2 s summed. This is an upper bound
  on the time affected, not the saving: most touched files keep some tests.
- Emptied files (every test deleted): 218 files, 3,134.9 s. This is the clearest saving.
- 60 touched files have no entry in the duration snapshot and count as 0 s.

### Residuals and risks (owner: phase B driver)

- The tie-break pass leaned toward deletion (59.9%). The restore pass reviewed only K-C and
  K-E. Disputed K-A, K-B, K-D and K-F tests that the tie-break deleted were not re-reviewed,
  so phase B's recheck should sample them.
- Deletes that all voters agreed on were not restore-reviewed, even in security or
  Ukrainian files, apart from the 8 emptied files.
- D-COVERED rows name a kept sibling in their reason, but nothing checked that the sibling
  really is kept. Phase B should verify each name against the selection before deleting.
- 1,162 single-pass parametrize-case deletes were not applied.
- Fleet Comms has no `claude-cto` recipient, so the tripwire and this final report are
  delivered in this file, as the brief allows.

### Tripwire report (pass 1)

- 2026-10-21 09:44Z: after 20 pass-1 batches (3,720 rows) the delete share was 36.0%.
  That is inside the expected 25-45%, so the run continued.

### Restores (119)

| Class | Test | Why restored |
| --- | --- | --- |
| K-C | `agent_runtime/test_acpx_claude_host_executable.py::test_paths_are_redacted_before_the_excerpt_is_bounded` | only test that private host paths in raw provider stderr are redacted, including the redact-before-truncate edge that would leak a path p... |
| K-C | `agent_runtime/test_grok_reviewer_tools.py::test_grok_bridge_refuses_other_invocations` | only test refusing a foreign interpreter or a look-alike guard script outside the hooks dir under the pinned interpreter, which would rep... |
| K-C | `agent_runtime/test_npm_shim.py::test_equivalent_tree_writers_through_symlink_are_refused` | only end-to-end refusal of aliases, abbreviations, rebuild/link/audit fix and option-value-prefixed tree writers that would empty the pri... |
| K-C | `api/test_claude_account_usage.py::test_probe_passes_only_the_sanitized_environment` | only end-to-end proof that refresh never passes ambient ANTHROPIC_API_KEY/OAuth tokens to the probe child; kept test only unit-tests chil... |
| K-C | `backup_data_script/test_completion_faults.py::test_remote_validation_names_variable_not_the_remote_name` | only test that the repository/remote validation branch never echoes the private rclone remote name; kept password-file test covers a diff... |
| K-C | `build/test_fresh_path_guard.py::test_write_manifest_error_sanitizes_reason_at_persistence_boundary` | only test that manifest.write_manifest_error redacts absolute/external host paths before persisting; kept test covers regeneration.record... |
| K-E | `build/test_register_consistency_gate.py::test_register_consistency_mixed` | only test of the blockquote exemption in colloquial 'шо' detection, and of counting several out-of-context hits with correct lines |
| K-C | `ci/test_stack_currency_report.py::test_render_withholds_unsafe_publication_shapes` | redaction vectors absent from kept canaries: private filesystem paths, IPv6, key=value tokens, markdown-link and table-pipe injection in... |
| K-C | `ci/test_stack_currency_report.py::test_version_prefix_with_extra_text_is_withheld` | distinct bypass vector: canary smuggled after a valid version prefix (unanchored allowlist) must be withheld from published report |
| K-E | `curriculum/evidence/test_sources.py::test_pronoun_tags_reach_conditioned_stress_oracle` | unique VESUM pronominal tag mapping (pron:dem -> upos=PRON, Dat vs Loc) for stress lookup; kept test covers only noun tags |
| K-E | `curriculum/resolver/test_requirement_evidence_ids.py::test_nearby_range_wrong_dictionary_and_wrong_key_do_not_resolve` | off-by-one VESUM range locators and cross-dictionary keys must not resolve; kept tests only cover nonexistent ids and valid ranges |
| K-E | `curriculum/resolver/test_requirement_evidence_ids.py::test_unrecognized_dictionary_fields_cannot_bind` | per-dictionary binding field allowlist (wrong headword/lemma field cannot support a form); test_dictionary_definition_cannot_bind_another... |
| K-E | `curriculum/resolver/test_resolver_synthetic.py::test_latin_digits_and_mixed_scripts` | only test that a Latin/Cyrillic mixed-script token fails as UNCLASSIFIABLE instead of being skipped as Latin |
| K-C | `hygiene/test_tmp_sweep_scratch.py::test_excluded_names_preserved` | only guard that the sweeper never deletes host-critical /tmp entries (ssh-*, .X11-unix, systemd-private, tmux, harness runtime) |
| K-E | `mcp/test_word_card_tool.py::test_tombstoned_evidence_cites_no_source` | suppressed (takedown) assertion must withhold the stress value; kept test_dangling_field_evidence_is_a_gap_never_a_value only covers miss... |
| K-C | `opsec/test_git_push_scan.py::test_history_the_destination_already_has_is_still_scanned` | scan bypass vector: destination-advertised history must not exclude commits (distinct from forged local tracking refs) |
| K-C | `opsec/test_git_push_scan.py::test_objects_are_read_by_the_supplied_id_not_the_local_ref` | scan bypass vector: scanner must scan the object id Git sends, not re-resolve the (now clean) local ref |
| K-C | `opsec/test_git_push_scan.py::test_scanner_error_sends_nothing` | scanner module crashing inside the running hook must fail closed; kept tests cover only a missing matcher or a shim pre-check |
| K-C | `opsec/test_override_command_scope.py::test_override_set_after_import_then_a_comment_and_a_push` | single-use secret-scan override when set in-process after publisher import (review-9681 F1 path); kept tests set it via env before start |
| K-C | `orchestration/test_run_scheduled_backup.py::test_retention_mode_redacts_output_and_preserves_failure_status` | retention mode has its own pipeline (run_redacted_retention); only test that it redacts repository and password path |
| K-C | `orchestration/test_worktree_artifacts.py::test_ignored_artifact_nested_repo_unregistered_gitlink_filter_rejected_without_execution` | no code execution via an unregistered-gitlink child's clean filter; the gitlink check must precede git status (no-child-gitdir and regist... |
| K-C | `projects/open_model_data/test_a3_heldout_source_family_seal.py::test_a3_heldout_seal_schema_forbids_sensitive_unknown_fields_on_bindings` | only test that the runtime-validated public seal schema refuses the private salt_hex / membership locator smuggled into bindings (secret... |
| K-C | `projects/open_model_data/test_v4_canonical_authority_mechanism.py::test_a3_sign_reference_check_receipt_refuses_without_a_provisioned_production_key` | only test that the A3 reference-check signing entrypoint refuses to sign without a custody-provisioned production key (no fixture-key fal... |
| K-C | `projects/open_model_data/test_v4_real_slot_mechanism.py::test_build_authorship_receipt_refuses_an_unknown_signer_key` | authentication: refuses a receipt signed by a key not registered in the trust keyring (attacker's own key); no kept test covers the unreg... |
| K-E | `projects/open_model_data/test_v4_verify_trajectory_claims.py::test_r2u_polarity_in_historical_suppression_note_expanded_negation` | only test of the historical_suppression_note R2U 1920s-dictionary claim extraction branch (kept polarity tests only cover reasoning_steps... |
| K-E | `review/test_invalid_input_receipts.py::test_real_stress_oracle_rejection_summary_is_not_evidence` | only test of the verify_stress '<word> — invalid_input:' summary branch (multi-word/non-Cyrillic) classified as no-hit, so stress-oracle... |
| K-C | `storage/test_publish_set.py::test_symlinked_store_refuses_before_lock_creation` | only test where data/ is real but data/.artifact-store is a symlink out of the repo; guards store/lock writes escaping via the store path... |
| K-C | `test_agent_runtime_log_redaction_adapters.py::test_grok_build_invocation_debug_is_constant` | only guard that the grok_build invocation debug log stays constant and never logs argv/task values; kept sibling test covers deepseek/glm... |
| K-C | `test_ask_hermes.py::test_cursor_hook_refused_by_the_guard_never_calls_entire` | only test that the cursor native hook shim honours the capture guard refusal (checkpoint route not private) and never egresses the transc... |
| K-E | `test_audit_helpers.py::TestValidateTone::test_kiev_usage` | only test that the live audit validate_tone flags the Russian-derived toponym Kiev (Kyiv rule); no kept test exercises validate_tone |
| K-E | `test_calque_corrections.py::test_pryiniaty_uchast_has_corpus_evidence_and_alias` | only test pinning an always-flag PHRASAL_CALQUES pair (прийняти/приймати участь -> взяти/брати участь, both aspects); kept tests cover cu... |
| K-C | `test_check_node_modules_integrity.py::test_site_node_modules_is_checked_independently` | only test that symlink-escape detection scans the second root site/node_modules; kept escape tests cover root node_modules only |
| K-E | `test_coverage_lexical_sandbox.py::TestFormAllowed::test_present_only_allows_present` | only test that a VESUM verb form is ALLOWED under a tense constraint (present-only must keep :pres forms); kept tests cover only the refu... |
| K-C | `test_delegate.py::test_run_worker_agy_review_link_retargeted_after_run_is_named_error` | credential OAuth token symlink retargeted to another file (points-elsewhere vector) is detected and not copied back; kept sibling only co... |
| K-C | `test_delegate_public_causes.py::test_the_advisory_committed_diff_error_names_the_exception_class_only` | distinct redaction path: _advisory_worker_diff error with a credential-bearing exception message publishes only the class; no kept test c... |
| K-C | `test_delegate_readonly_guard.py::test_read_only_agy_cwd_pin_fails_when_child_anchors_outside` | only test of the sandbox cwd-pin refusal (child outside pinned tree -> cwd_unpinned); kept siblings cover scoping and the allow path only |
| K-C | `test_delegate_rescue_kimi.py::test_a_url_rewrite_cannot_fake_the_remote_verification` | push-redirect via shared url.insteadOf rewrite is a distinct attack vector from the pushurl case in kept test_rescue_ignores_a_shared_pus... |
| K-E | `test_derived_en_fallback.py::test_pronoun_pos_is_not_treated_as_noun` | POS gate edge: 'pronoun' containing 'noun' must not derive diminutive/augmentative glosses; kept tests use adjective and permissive noun... |
| K-C | `test_driver_state.py::test_whoami_redacts_state_path` | only test that whoami replaces the private state path with '(configured)' in output, present and missing cases |
| K-E | `test_enrich_heteronyms.py::test_build_heteronyms_for_lemma_preserves_all_homonyms_when_stresses_differ` | mixed-stress partition: same-stress homonyms are all kept when one article's stress differs; kept #8039 test covers only all-same and all... |
| K-C | `test_epic_selector.py::test_leaf_file_import_and_validation_without_repository_on_sys_path` | only test in file of epic selector rejecting traversal/absolute selectors ('../x', '/absolute') used in state paths |
| K-E | `test_export_open_dataset_integrity.py::test_card_manifest_cannot_carry_extra_assertions` | word-card certification: manifest-level uncertified extra assertions refused by export_dataset and gzip_manifest with no writes; kept tes... |
| K-C | `test_github_client.py::test_host_boundary_refuses_foreign_endpoints` | credential host boundary: distinct attack vectors (uppercase/http/ftp schemes, backslash-userinfo parser differential) on request and nat... |
| K-C | `test_guard_admin_merge.py::test_issue_9479_r2_redirect_bash_argv` | admin-merge guard bypass vectors '&&>file' glued operator and '{fd}>file' prefix redirect, not covered by kept redirect/glued-operator tests |
| K-C | `test_guard_pr_merge.py::test_issue_9461_merge_text_redirects_stay_unreadable` | process substitution / here-string $(..) as merge selector or arg must refuse before any PR lookup; no kept test covers the <(..) vector |
| K-C | `test_guard_primary_checkout_write.py::test_bash_home_clobbered_or_deferred_is_unknown` | eval/prefix-scoped/function-deferred HOME clobber must make ~ unresolved, not inherited; distinct bypass vectors uncovered by kept tests |
| K-C | `test_guard_primary_checkout_write.py::test_bash_read_home_shadows_inherited_home` | read HOME rebinding must not fall back to inherited $HOME and let a primary write through; no kept test covers HOME rebinding |
| K-C | `test_guard_primary_checkout_write.py::test_issue_9088_exotic_body_cannot_skip_later_safe_opener` | safe heredoc opener inside an exotic heredoc body must not hide a primary write; not covered by the kept exotic-opener matrix |
| K-C | `test_guard_primary_checkout_write.py::test_issue_9115_escaped_nested_backtick_write_is_visible` | escaped nested backtick (\`..\`) write must stay visible; kept tests cover only unescaped nesting or depth-limit fail-closed |
| K-C | `test_guard_secret_print.py::test_dump_boundary_siblings` | bare export/declare/typeset dumps and env > /dev/stderr//dev/fd/2 leak paths; test_audit_shapes covers only -p forms and /dev/stdout |
| K-C | `test_guard_secret_print.py::test_issue_8896_nested_shell_quote_concatenation_blocks` | multi-level bash -c with shlex quote concatenation must still expose cat .env; kept tests cover only single-level -c |
| K-C | `test_guard_secret_print.py::test_nested_input_owner_boundaries_denied` | sanitizing >(wc -c) followed by a file redirect must not launder an env dump later read back; no kept test covers redirect override |
| K-C | `test_guard_secret_print.py::test_round_six_shell_fragment_boundaries` | shell quote concatenation ('os.en''viron') inside interpreter programs must not hide an environ dump; only other test with this vector is... |
| K-E | `test_heritage_classifier.py::test_scope_helpers` | only test of is_normative_locator textbook partition (non-language subject, non-approved author, bare author citation) deciding which sou... |
| K-C | `test_kimi_oauth_tty_guard.py::test_env_override_allow_tty_is_ignored_and_still_refuses` | distinct bypass vector: KIMI_OAUTH_ALLOW_TTY opt-in must not let a live token print to a terminal (P1-a regression) |
| K-C | `test_launcher_helper_root.py::test_gitfile_through_a_symlinked_worktrees_dir_is_refused` | unique guard clause (-L worktrees_dir): symlinked .git/worktrees would otherwise pass the back-pointer check and run a fake primary inter... |
| K-C | `test_launcher_helper_root.py::test_resolution_clears_git_local_environment` | only test that GIT_CONFIG_PARAMETERS (core.fsmonitor exec) / GIT_INDEX_FILE / GIT_OBJECT_DIRECTORY are scrubbed from the launcher environ... |
| K-E | `test_lexical_sandbox.py::TestFormAllowed::test_nom_only_allows_nominative` | only allow-side test of the VESUM case filter (v_naz passes nominative_only); kept tests check only blocking |
| K-E | `test_lexical_sandbox.py::TestFormAllowed::test_present_only_allows_present` | only allow-side test of the VESUM tense filter (pres passes present_only); kept tests check only blocking |
| K-C | `test_mcp_sources_privacy_logging.py::test_privacy_mode_logs_no_response_text` | privacy-mode redaction of tool response text from request log; kept tests cover only args and error leaks |
| K-E | `test_mcp_sources_server.py::TestCheckModernFormHandler::test_not_found_word_shape` | VESUM miss must yield is_modern_codified=false / not_found; distinct rejection outcome from kept found and archaic-only tests |
| K-E | `test_mcp_sources_server.py::TestDictSearchQuoteBalance::test_handle_dict_search_clips_long_definitions` | search_definitions SUM-11 hits carry verification_authority=false in envelope; kept sum11 test covers only verify_source_attribution path |
| K-E | `test_mcp_sources_server.py::TestIntegrationSmoke::test_smoke_verify_lemma_archaic` | only test of verify_lemma handler: real-VESUM archaic-form flagging for a lemma |
| K-E | `test_mcp_sources_server.py::TestQueryUlifRecordsHandler::test_live_sum11_entry_is_labelled_contrast_only` | live slovnyk.me SUM-11 hit flagged verification_authority false (Soviet dictionary never authority); no kept test on this handler path |
| K-C | `test_mdx_render_gate.py::test_sentinel_catches_template_interpolation` | unescaped ${...} code-execution injection must fail the render gate; distinct attack vector from kept under-escaped-quote SyntaxError test |
| K-C | `test_monitor_ui_contracts.py::test_delegate_detail_pane_projects_observer_safe_task_json` | delegate detail pane must not expose raw paths/stderr_excerpt (private data redaction); no kept coverage |
| K-C | `test_opsec_linter.py::test_linter_scans_itself_without_blanket_exemption` | only test of the is_linter_itself branch: leak scanner must still flag secrets/IPs in its own file (line-scoped, not blanket exemption) |
| K-E | `test_paradigm_stress.py::test_same_spelling_aspect_pair_withholds_every_shared_form` | unique aspect-homograph stress rule: perf/imperf tags bind different accents and hidden perfective readings still veto the shared display... |
| K-E | `test_practice_quality_gate.py::test_audit_teacher_cloze_detects_intentional_error_leak` | only kept-side test that surzhyk/error-exercise sentences (INTENTIONAL_ERROR_LEAK) are blocked from learner cloze decks |
| K-E | `test_reconcile_calque_clusters.py::test_candidate_ranking_key` | only test of calque-replacement preference order (textbook > heritage > VESUM) that picks the alternative learners see |
| K-C | `test_recovery_runbook_guards.py::test_newline_in_the_install_ancestor_does_not_remove_an_outside_empty_directory` | path confinement: newline stripped from the install-dir ancestor must not make an outside directory look inside the cache; kept test cove... |
| K-C | `test_review_isolation.py::test_claude_bare_alone_does_not_attest_skill_suppression` | reviewer sandbox proof: --bare without --safe-mode must not attest hook/skill/plugin suppression; no kept test exercises this capability... |
| K-C | `test_review_isolation.py::test_codex_capabilities_do_not_treat_unrelated_s_substrings_as_sandbox_proof` | reviewer sandbox proof: look-alike help flags (--strict-output, --sandboxed) must not count as sandbox/read-only evidence; kept tests cov... |
| K-E | `test_russicism_detection.py::TestBasicDetection::test_detects_відноситися` | only test of the відноситися -> стосуватися Russianism rule (own regex entry) |
| K-E | `test_russicism_detection.py::TestBasicDetection::test_detects_нравитися` | only test of the нравитися -> подобатися Russianism rule (own regex entry) |
| K-E | `test_russicism_detection.py::TestBasicDetection::test_detects_самий_кращий` | only test of the multi-word superlative calque самий кращий -> найкращий |
| K-E | `test_russicism_detection.py::TestBasicDetection::test_detects_скучати` | only test of the скучати -> сумувати Russianism rule (own regex entry) |
| K-E | `test_russicism_detection.py::TestUaGecBulkLookup::test_quotes_and_blockquotes_skipped` | only test that check_ua_gec_calques skips quoted/blockquoted text; kept quote tests cover check_russicisms only |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_бормотати_caught` | only test of lexical Russianism бормотати -> бурмотіти |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_буфетчик_caught` | only test of -чик suffix Russianism буфетчик -> буфетник |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_в_першу_чергу_caught` | only test of calque в першу чергу -> передусім |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_в_цілому_caught` | only test of calque в цілому -> загалом |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_відношення_caught` | only test of calque відношення -> стосунок/ставлення |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_відправився_reflexive_caught` | only test of reflexive calque відправився -> вирушив |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_відправляється_transitive_clean` | only false-positive guard for the відправ* rule: correct відправляється must not flag |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_з_іншої_сторони_caught` | only test of calque з іншої/однієї сторони -> з іншого боку (no kept sibling) |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_на_фоні_caught` | only test of calque на фоні -> на тлі |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_повезе_caught` | only test of calque повезе -> пощастить |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_прийшлось_caught` | only test of impersonal calque прийшлось -> довелося |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_робив_вигляд_caught` | only test of fixed-expression calque робив вигляд -> вдавав |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_справа_other_sense_clean` | only false-positive guard for справа rule: noun справа (matter) must not flag |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_справа_в_тому_caught` | only kept-candidate test of fixed-expression calque справа в тому -> річ у тому |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_співпадають_caught` | only test of lexical Russianism співпадати -> збігатися (inflection alternation regex) |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_так_як_caught` | only test of conjunction calque так як -> оскільки |
| K-E | `test_russicism_detection.py::TestUaGecCalquePatterns::test_таким_чином_caught` | only test of discourse calque таким чином -> отже |
| K-E | `test_scoring.py::TestAnalyzeToponyms::test_ukrainian_names_counted` | only test that Ukrainian toponym forms (Київ/Харків/Львів) are recognised and not flagged as Russified forms |
| K-C | `test_secret_print_hook.py::test_agy_invalid_stdin_subprocess` | only test of agy oversized-stdin (>MAX_STDIN_BYTES) fail-closed deny; malformed cases otherwise covered by test_native_cli_decisions |
| K-C | `test_secret_redaction.py::test_round5_assertion_suffix_fragments` | unique leak vector: pytest assertion diff explanation with common prefix exposes secret suffix fragments; no kept test drives value+a ==... |
| K-E | `test_semantic_false_friends.py::TestSemanticFalseFriends::test_case_insensitive` | only test that capitalized false friends (Лук (Onion)) are detected; kept tests use lowercase only |
| K-E | `test_semantic_false_friends.py::TestSemanticFalseFriends::test_colon_separator` | only test of the 'word: meaning' colon translation pattern for false-friend detection |
| K-E | `test_semantic_false_friends.py::TestSemanticFalseFriends::test_detects_лук_as_onion_dash` | only test of the 'word — meaning' dash translation pattern for semantic false-friend (Russianism) detection |
| K-E | `test_semantic_false_friends.py::TestSemanticFalseFriends::test_reversed_table` | only test of the reversed '/ meaning / word /' table pattern for false-friend detection |
| K-C | `test_session_router_path_safety.py::test_read_session_file_rejects_escape` | only test that the actual file-read sink _read_session_file applies path containment (400, never read); kept tests cover only _safe_proje... |
| K-C | `test_shared_hooks_deploy_depth.py::test_guard_without_sibling_helper_fails_closed` | only test that guard-secret-print fails closed when its helper is missing; kept fail-closed test covers merge/branch guards only |
| K-C | `test_source_inventory_review_candidates.py::test_publish_review_queue_report_rejects_traversal_into_repository` | distinct attack vector: '..' traversal back into the repo must still be refused for report writes; kept test uses a direct repo path |
| K-E | `test_sources_db.py::TestHeadwordFirstRanking::test_search_heritage_knyha_ranks_above_psaltyr` | only in-file test of search_heritage merged Grinchenko+ESUM headword-first ranking used for heritage verification; kept tests cover searc... |
| K-E | `test_stress_oracle.py::TestHeteronymEnumeration::test_unresolvable_by_tags_false_for_unambiguous_word` | only test of unresolvable_by_tags=False for an unambiguous word; kept tests only assert the True/ambiguous outcome |
| K-E | `test_stress_oracle.py::TestInvalidInput::test_single_syllable` | oracle refuses to stress monosyllabic words (Ukrainian monosyllables carry no stress mark); no kept test covers it |
| K-C | `test_typed_github_publisher.py::test_pr_creation_cannot_publish_implicit_branch_names` | public-publish gate refuses pr-create without explicit base/head so gh cannot publish an unscanned implicit branch name; distinct leak ve... |
| K-E | `test_typesafe_cyrillic_gate.py::test_evaluate_standard_with_high_shadow_override_mock` | only test of the shadow-probability-only surzhyk branch (variety=standard_modern); kept surzhyk test takes the variety=colonial_surzhyk b... |
| K-E | `test_ulif_ingest_headwords.py::test_existing_entry_identity_is_preserved_when_tab_differs` | only test that an entry's own stressed headword is not overwritten by a foreign paradigm tab (no_paradigm test passes {} tabs) |
| K-E | `test_vesum_heritage_attestation.py::test_derivational_fallback_does_not_accept_coinages` | only test that derivational fallback refuses non-Russianism coinages (двохоровий, обрядознавчий); kept refusal tests cover Russianisms only |
| K-E | `test_vesum_heritage_attestation.py::test_folk_vesum_gate_accepts_productive_noun_diminutives` | only acceptance test for the diminutive derivational rule (гаївочка, книжечка); kept tests cover adjective/verb bases and diminutive Russ... |
| K-E | `test_vesum_plan_exemptions.py::test_quoted_critical_terms_backtick_context_is_not_enough` | distinct bypass vector: backtick context must not exempt a quoted Russianism (corpus quotes accept backticks); kept test checks only unqu... |
| K-E | `test_wiki_compressor_tokenize.py::TestTokenizePreservesCyrillicLetters::test_preserves_ї` | ї uses the diaeresis combiner U+0308, distinct from й's breve U+0306 in the kept test; guards країна->краина corruption |
| K-E | `test_wiki_discipline.py::TestValidateCanonicalAnchors::test_case_insensitive` | only test that forbidden calque/Soviet-framing anchors match capitalised Cyrillic (sentence-initial forms would otherwise slip) |
| K-E | `test_word_card_assembly.py::test_r3_output_rejects_common_noun_vesum_entry_on_proper_name` | verifier-side proper-name vs common-noun VESUM binding (case-distinct homograph); kept test_r3_output_rejects_foreign_vesum_homograph cov... |
| K-E | `verification/test_antonenko_patterns.py::test_adjectives_auxiliaries_and_duration` | only positive test of the adjective-transparent gap (приймати активну участь) and auxiliary/newline-spanning calque matches; kept positiv... |
| K-E | `verification/test_antonenko_round3.py::test_missing_morphology_does_not_manufacture_duration` | only fail-closed test of the temporal-protiah duration-case check when VESUM readings are missing; no kept test in the file covers empty... |


### Phase B conflict refresh for PR #11329

Merged main `465b2bcf702508d8ec260233bb395df02c967117` into the phase B branch. Functions changed on main are kept verbatim; unchanged function deletions remain selected. Frozen hashes and ratchet baselines are unchanged.

| File | Function | Decision | Reason |
| --- | --- | --- | --- |
| `tests/test_deploy_pages_workflow.py` | `test_pages_build_installs_atlas_python_dependencies` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_deploy_pages_workflow.py` | `test_pages_deploy_uses_normal_build_and_fail_closed_size_gate` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_deploy_pages_workflow.py` | `test_pages_deploy_vendors_atlas_tree_after_build_before_size_gate` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_deploy_pages_workflow.py` | `test_pages_build_publishes_the_pinned_word_card_preview` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_deploy_pages_workflow.py` | `test_preview_pin_changes_keep_manual_deployment_semantics` | kept | Main PR #11271 added the sparse-tree declaration; preserve its reviewed version. |
| `tests/test_deploy_pages_workflow.py` | `test_pages_workflow_uses_fail_closed_auto_deploy_preflight` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_guard_list_matches_the_wired_guards` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_refusing_guard_timeouts_cover_loaded_latency` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_non_refusing_hooks_stay_fail_open` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_heal_core_bare_is_fail_open_and_bounded` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_claude_worker_settings_inherit_the_failure_policy` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_reviewer_publish_guard_blocks_on_failure` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_live_claude_runs_the_tool_call_when_a_fail_open_guard_times_out` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_branch_guard_spawns_no_git_for_commands_it_cannot_refuse` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_guard_keeps_the_shim_when_no_other_git_exists` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `_heal_fixture` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_heal_core_bare_spawns_the_checker_only_on_possible_drift` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_codex_outer_timeout_exceeds_the_inner_deadline_chain` | kept | Main PR #11323 added the dirt-audit snapshot timeout budget; preserve its reviewed version. |
| `tests/test_hook_failure_policy.py` | `test_agy_outer_timeout_exceeds_the_secret_guard_deadline` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_grok_outer_timeout_exceeds_the_bridge_deadline` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_grok_interactive_seats_run_guards_through_a_deadline_to_deny_runner` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
| `tests/test_hook_failure_policy.py` | `test_cursor_fail_open_detector_flags_a_guard_without_fail_closed` | deleted | Main did not change this function since the merge base; preserve the phase B prune. |
