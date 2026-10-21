# OO-50 / #11226 test prune — phase A (selection)

Status: phase A done, 2026-10-21 13:42Z. The selection marks **15,102 of 40,173 test
functions (37.6%) for deletion**, plus 72 duplicate parametrize cases inside kept
functions. Phase B (mechanical apply, manifests, PR) is a separate task. No file under
`tests/` or `scripts/ci/` was changed and no test was run in this phase.

## Files

- `rubric.md`: the rubric the swarm applied (t3code classes, CTO-narrowed K-C, one kept test
  per distinct behaviour, no keep catch-all).
- `2026-10-21-public-selection.jsonl`: the selection, one row per touched test file:
  `{"file", "delete": {test: class}, "delete_cases": {test[case]: class}, "restored": {test: class}}`.
  Test names are relative to the file (`Class::test_x` for class methods). Tests not listed stay.
- `2026-10-21-public-selection-detail.jsonl.gz`: one row per listed test with the reason,
  the three votes and how the verdict was reached. It is a separate gzip file because the
  repo refuses files over 2,000 KB (the uncompressed detail is 5.5 MB).

## Method

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

## Counts (final, after restores)

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

## CI duration (from `scripts/ci/pytest-file-durations.json`)

- All files in the snapshot: 30,250.8 s summed across shards.
- Touched files (at least one deletion): 1,893 files, 28,969.2 s summed. This is an upper bound
  on the time affected, not the saving: most touched files keep some tests.
- Emptied files (every test deleted): 218 files, 3,134.9 s. This is the clearest saving.
- 60 touched files have no entry in the duration snapshot and count as 0 s.

## Residuals and risks (owner: phase B driver)

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

## Tripwire report (pass 1)

- 2026-10-21 09:44Z: after 20 pass-1 batches (3,720 rows) the delete share was 36.0%.
  That is inside the expected 25-45%, so the run continued.

## Restores (119)

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
