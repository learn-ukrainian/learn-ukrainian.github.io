# Archived old-plan open-model generators (#9607)

Archived on 2026-10-03 by #9607 (plan v3.4.3, gate PA1, epic #6321). The restart plan forbids model- or
script-written text in the dataset; these generators produced it, so they are kept for the record and
removed from active code. Nothing here may be imported or run: `__init__.py` raises `ImportError`, and
`tests/projects/open_model_data/test_quarantine.py` fails if active code imports any of these modules.

| Archived file | Origin | Why |
| --- | --- | --- |
| `scripts/v6_mine_ulif_phraseology.py` | #8140, PR #9511 | ULIF idiom generator; its work (#8140) failed review on 2026-10-03. Idioms re-enter as component C4 (plan E18). |
| `scripts/v6_mine_general_assistant_textbooks.py` | #8139 | School-subject set generator that produced the sealed `uldr_v06_general_assistant`; script-synthesized explanations and reasoning. |
| `scripts/judge_eval_seat.py` | #8139 | Seat judgment of the `uldr_v06` eval records; imports the generator above and serves only that sealed set. |
| `tests/test_v6_mine_ulif_phraseology.py`, `tests/test_v6_mine_general_assistant_textbooks.py` | as above | Tests of the archived code, archived with it (AC5). |
| `issue_8341_branch.patch` | branch `gemini/8341-school-subject-data`, head `04bef298e7`, base `8bd69fd496` | The unmerged #8341 rewrite of the school-subject generator (code and test only); it failed review on 2026-10-03 and must not be merged. The branch's generated rights-record JSON/YAML files are not copied. |

The data these generators wrote is sealed, not deleted: see
`registry/projects/open_model_data/quarantine/inventory_v1.json`.

## Tests removed from active loaders (#9607)

These tests verified, tampered with or rebuilt the sealed artifacts through the loaders that now refuse them
(or exercised the packager on the sealed release-set names). Under plan PA1 and PA7 that behaviour is prohibited,
so the tests were removed rather than inverted one by one; the refusal of each loader is covered by
`tests/projects/open_model_data/test_quarantine.py` and `test_quarantined_release_inputs_refuse_before_export`.
The originals are at commit `feb0506412` (the base of this change).

- `tests/projects/open_model_data/test_package_unified_dataset_p3a.py` (5): `test_absent_required_committed_selector_fails_before_export`, `test_external_fixture_reader_still_builds`, `test_managed_reader_uses_committed_members_and_exports_external`, `test_managed_snapshot_failure_precedes_output_mutation`, `test_partial_optional_general_assistant_release_fails_when_included`
- `tests/projects/open_model_data/test_v4_open_weight_learning_study.py` (6): `test_companion_only_prepare_rejects_changed_manifest`, `test_external_paths_remain_writable`, `test_managed_cli_explicit_paths`, `test_managed_prepare_changed_repeated_and_run_verify`, `test_managed_publish_failure_preserves_prior_state`, `test_managed_unchanged_prepare_direct_run_and_stale_recipe`
- `tests/projects/open_model_data/test_v4_pilot_canary_evaluation.py` (37): `test_adversarial_adapter_seed42_random_weights_rejected`, `test_adversarial_calque_parenthesized_reversed_recommendation_rejected`, `test_adversarial_nlp_negated_options_codex_r9`, `test_adversarial_safety_triple_asterisk_commentary_rejected`, `test_compiled_schema_cache_rechecks_changed_schema_content`, `test_empty_replay_object_fails_verification`, `test_missing_detached_sha256_fails_verification`, `test_missing_receipt_provenance_fails_verification`, `test_opsec_sentinel_fails_verification`, `test_replay_conversation_deep_validation`, `test_replay_partition_firewall_rejection`, `test_stripped_eval_cases_provenance_fails_verification`, `test_stripped_nlp_baseline_provenance_fails_verification`, `test_stripped_training_log_provenance_fails_verification`, `test_tampered_adapter_mock_random_weights_fails_verification`, `test_tampered_calque_bold_replacement_fails_verification`, `test_tampered_calque_error_on_replacement_fails_verification`, `test_tampered_calque_reversed_template_fails_verification`, `test_tampered_dataset_fails_verification`, `test_tampered_detached_sha256_fails_verification`, `test_tampered_eval_case_prediction_fails_verification`, `test_tampered_eval_cases_fails_verification`, `test_tampered_loss_reduction_pct_fails_verification`, `test_tampered_nlp_all_options_fails_verification`, `test_tampered_nlp_backtick_contradiction_fails_verification`, `test_tampered_nlp_bold_contradiction_fails_verification`, `test_tampered_receipt_gates_fail_verification`, `test_tampered_record_count_fails_verification`, `test_tampered_replay_buffer_fails_verification`, `test_tampered_safety_bold_commentary_fails_verification`, `test_tampered_safety_bold_dash_commentary_fails_verification`, `test_tampered_safety_commentary_deletion_fails_verification`, `test_tampered_safety_inline_commentary_fails_verification`, `test_tampered_training_dataset_without_log_update_fails_verification`, `test_tampered_training_log_fails_verification`, `test_trajectory_schema_deep_validation`, `test_verify_only_succeeds_on_valid_artifacts`
- `tests/projects/open_model_data/test_v4_pilot_canary_evaluation.py` helpers: the autouse validator-cache fixture and `_write_receipt_with_digest`, used only by the removed tests.
