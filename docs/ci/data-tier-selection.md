# Nightly data-tier selection

The nightly selection in `scripts/ci/data_tier_selection.json` covers tests that can use existing repository files and local stores. It requests no artifact hydration. The machinery runner must read this product file and `data_tier_known_failures.json`, rather than packaged copies. See #9256.

## Selection accounting

The prior product selection contained 556 entries. This revision retains 127 exact node IDs and removes 429 entries. Entries are not historical runtime case counts: the removed citation file entry expanded into multiple parameter cases. The historical `source_run`, `source_sha`, and `real_store_audit` fields record the original audit, not current coverage.

| Removed selection group | Entries | Reason |
| --- | ---: | --- |
| No marker-valid bulk root | 4 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| Stopped open-model-data project (C-2181) | 383 | Stopped open-model-data project (C-2181); retained tests with existing local data. |
| benchmarks/v1/MANIFEST.json is absent from existing host data. | 3 | benchmarks/v1/MANIFEST.json is absent from existing host data. |
| 51 known citation-content xfails still reference closed #8403 | 1 | 51 known citation-content xfails still reference closed #8403; retained outside nightly for content repair on #9256. |
| Learner content defects recorded on #9256 | 2 | Learner content defects recorded on #9256; content edits frozen. |
| All five expected ukrlib JSONL outputs are absent | 5 | All five expected ukrlib JSONL outputs are absent; SQLite author checks remain. |
| wave12-krupnytsky-orlyk-biohrafiia.jsonl is absent from existing host data. | 1 | wave12-krupnytsky-orlyk-biohrafiia.jsonl is absent from existing host data. |
| The only configured complete track is a1, whose manifest contains no modules. | 1 | The only configured complete track is a1, whose manifest contains no modules. |
| Stale selection entry: the named test is absent from the current source tree. | 29 | Stale selection entry: the named test is absent from the current source tree. |

## Deleted tests and absent inputs

Tests requiring absent inputs are deleted rather than left as permanent skips. Other tests in the same files remain. Tests for existing data in the stopped open-model-data project remain in source but leave the nightly selection. No application code or learner content changes.

| Deleted test | Cases or definitions | Missing input |
| --- | ---: | --- |
| `tests/ingest/test_esum_ingest.py::test_esum_ingest_djvutxt_regression` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_channels_registry.py::test_registry_covers_all_external_source_files` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_layerb_shadow.py::test_stored_corpus_lineage_resolves_all_groundings_when_available` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_open_model_phase3_donnu_2023_morphemics_word_formation_intake.py::test_private_audit_against_drive_custody` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_open_model_phase3_evaluation_context_manifest.py::test_production_manifest_against_drive_custody` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_open_model_phase3_lnu_2024_phonetics_phonology_intake.py::test_optional_live_drive_audit` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_open_model_phase3_pliush_2005_canonical_grammar_intake.py::test_private_audit_against_drive_custody` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_open_model_phase3_pravopys_evaluation_context.py::test_production_replay_against_drive_custody` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_open_model_phase3_school_context_negative_recovery.py::test_production_receipt_reproducible_against_drive_custody` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_open_model_phase3_school_parent_section_context.py::test_production_verify_against_drive_custody` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_open_model_phase3_vspu_2025_morphemics_word_formation_intake.py::test_production_verify_against_drive_custody` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_open_model_phase3_zhdu_2026_lexicology_phraseology_intake.py::test_production_verify_against_drive_custody` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_wiki_channels.py::test_registry_schema_covers_all_live_source_files` | 1 | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_benchmark_freeze.py::test_public_fixture_hashes_match_frozen_manifest` | 1 | benchmarks/v1/MANIFEST.json is absent from existing host data. |
| `tests/test_benchmark_freeze.py::test_reference_scorecard_hash_matches_frozen_manifest` | 1 | benchmarks/v1/MANIFEST.json is absent from existing host data. |
| `tests/test_benchmark_freeze.py::test_frozen_diagnostic_values_match_current_code` | 1 | benchmarks/v1/MANIFEST.json is absent from existing host data. |
| `tests/test_reattribute_ukrlib.py::TestPostReattributedFilesValid::test_post_file_has_correct_author` | 5 | All five expected ukrlib JSONL outputs are absent; SQLite author checks remain. |
| `tests/test_scrape_diasporiana.py::TestDiasporianaJsonlSchema::test_chunk_schema_matches_existing_litopys_waves` | 1 | wave12-krupnytsky-orlyk-biohrafiia.jsonl is absent from existing host data. |
| `tests/test_site_links.py::TestCurriculumSync::test_manifest_modules_have_mdx` | 1 | The only configured complete track is a1, whose manifest contains no modules. |

The obsolete benchmark manifest helpers are removed with their tests. `test_heldout_hashes_include_only_non_hidden_json_files` remains. The removed site-sync test was the only test in its file. The SQLite author/work checks in `test_reattribute_ukrlib.py` remain.

## Existing data and remaining checks

| Group | Access |
| --- | --- |
| Sources and VESUM | Existing `requires_sources_db` / `requires_vesum_db` logical-store fixtures; read-only queries. The golden set, pronoun checks, and live style-guide examples use these fixtures. |
| UA-GEC | Read the existing primary corpus through `resolve_main_root`; build the real in-memory annotation index. |
| Atlas | Read the existing primary `data/atlas.db` through `resolve_main_root`; retain exact exported counts and alias checks. |
| Corpus snapshots and lexicon artifacts | Existing files only; no nightly hydration groups. |

## Accepted skips and content residuals

No skip reasons are accepted for the retained nightly selection. A skip means an unmet execution requirement, not a pass. Stale node IDs whose definitions no longer exist are removed explicitly in the appendix.

The Atlas membership and all-mode practice gates remain in source and are excluded from nightly because their current failures are learner-content defects. The content lane owns repair after authoring resumes; the exact audit findings are recorded on #9256. No dictionary rows, manifest entries, practice cards, thresholds, or assertions are changed.

The citation invariant also remains in source. Its 51 known-content xfails still name #8403 even though that issue is closed. Exclude the whole file from nightly rather than treating xfails as passing data coverage. Remove its obsolete known-failure entry. Content-lane follow-up is recorded on #9256.

The product change does not certify a post-landing nightly run until the machinery runner uses these product inputs and existing data without snapshots or copies. #9256 stays open until that end-to-end run passes.

## Removed selection entries

| Entry | Reason |
| --- | --- |
| `tests/ingest/test_esum_ingest.py::test_esum_ingest_djvutxt_regression` | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_benchmark_freeze.py::test_frozen_diagnostic_values_match_current_code` | benchmarks/v1/MANIFEST.json is absent from existing host data. |
| `tests/test_benchmark_freeze.py::test_public_fixture_hashes_match_frozen_manifest` | benchmarks/v1/MANIFEST.json is absent from existing host data. |
| `tests/test_benchmark_freeze.py::test_reference_scorecard_hash_matches_frozen_manifest` | benchmarks/v1/MANIFEST.json is absent from existing host data. |
| `tests/test_channels_registry.py::test_registry_covers_all_external_source_files` | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_citation_resolution_invariant.py` | 51 known citation-content xfails still reference closed #8403; retained outside nightly for content repair on #9256. |
| `tests/test_layerb_shadow.py::test_stored_corpus_lineage_resolves_all_groundings_when_available` | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_practice_quality_gate.py::test_production_practice_shards_all_modes_gate_passes` | Learner content defects recorded on #9256; content edits frozen. |
| `tests/test_reattribute_ukrlib.py::TestPostReattributedFilesValid::test_post_file_has_correct_author[ukrlib-kotlyarevsky.jsonl-\u041a\u043e\u0442\u043b\u044f\u0440\u0435\u0432\u0441\u044c\u043a\u0438\u0439 \u0406.]` | All five expected ukrlib JSONL outputs are absent; SQLite author checks remain. |
| `tests/test_reattribute_ukrlib.py::TestPostReattributedFilesValid::test_post_file_has_correct_author[ukrlib-kotsyubynsky.jsonl-\u041a\u043e\u0446\u044e\u0431\u0438\u043d\u0441\u044c\u043a\u0438\u0439 \u041c.]` | All five expected ukrlib JSONL outputs are absent; SQLite author checks remain. |
| `tests/test_reattribute_ukrlib.py::TestPostReattributedFilesValid::test_post_file_has_correct_author[ukrlib-myrny.jsonl-\u041c\u0438\u0440\u043d\u0438\u0439 \u041f.]` | All five expected ukrlib JSONL outputs are absent; SQLite author checks remain. |
| `tests/test_reattribute_ukrlib.py::TestPostReattributedFilesValid::test_post_file_has_correct_author[ukrlib-nechuy.jsonl-\u041d\u0435\u0447\u0443\u0439-\u041b\u0435\u0432\u0438\u0446\u044c\u043a\u0438\u0439 \u0406.]` | All five expected ukrlib JSONL outputs are absent; SQLite author checks remain. |
| `tests/test_reattribute_ukrlib.py::TestPostReattributedFilesValid::test_post_file_has_correct_author[ukrlib-tychyna.jsonl-\u0422\u0438\u0447\u0438\u043d\u0430 \u041f.]` | All five expected ukrlib JSONL outputs are absent; SQLite author checks remain. |
| `tests/test_scrape_diasporiana.py::TestDiasporianaJsonlSchema::test_chunk_schema_matches_existing_litopys_waves` | wave12-krupnytsky-orlyk-biohrafiia.jsonl is absent from existing host data. |
| `tests/test_site_links.py::TestCurriculumSync::test_manifest_modules_have_mdx[a1]` | The only configured complete track is a1, whose manifest contains no modules. |
| `tests/test_wiki_channels.py::test_registry_schema_covers_all_live_source_files` | No marker-valid bulk root; scripts.storage status reports no_marker_valid_bulk_root. |
| `tests/test_atlas_conformance.py::test_real_lexicon_manifest_membership_conforms` | Learner content defects recorded on #9256; content edits frozen. |
| `tests/audit/test_antonenko_prose_narrowing.py::test_marker_constant_excludes_overbroad_phrases` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/audit/test_antonenko_prose_narrowing.py::test_rendered_prompt_surfaces_narrowed_status` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/audit/test_judge_eval_lib_h2.py::test_build_judge_prompt_h2_renders_all_six_sections` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/audit/test_judge_eval_lib_h2.py::test_retrieve_evidence_returns_all_six_channels` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/audit/test_judge_eval_lib_h2.py::test_ua_gec_calque_search_returns_empty_on_no_cyrillic` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_check_text.py::test_bench_check_text_reduced` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_check_text.py::test_real_ua_gec_skipped_kind_tokens_dropped_and_counted` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_check_text.py::test_speed_warm_call_under_2s` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_esum_search.py::test_search_esum_bereza_returns_indo_european_cognates` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_esum_search.py::test_search_esum_voda_returns_cross_slavic_and_proto_slavic_cognates` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_export_runtime_shards.py::test_real_db_entry_shard_size_band` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_interjection_mechanics_engine.py::test_cli_verify_vesum_present` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_morphological_validator.py::TestBracketStripping::test_markdown_links_preserved` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_morphological_validator.py::TestBracketStripping::test_regular_words_still_checked` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_morphological_validator.py::TestImperativeDetection::test_imperative_in_callout_caught` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_morphological_validator.py::TestNonA1Imperatives::test_b1_imperative_ok` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_morphological_validator.py::TestPOSMismatch::test_verb_only_word_caught` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_morphological_validator.py::TestStressMarks::test_stressed_adjective_list` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_morphological_validator.py::TestVerbDetection::test_verb_in_chunk_exempt` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_navsi200_asr_bakeoff.py::TestAsrBakeoffLedgerAndPrivacy::test_calibration_benchmark_metrics_present` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_navsi200_captions.py::TestNavsi200CaptionsLedger::test_ledger_file_exists` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_navsi200_captions.py::TestNavsi200CaptionsLedger::test_priority_ordering_in_ledger` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_navsi200_captions.py::TestNavsi200CaptionsLedger::test_privacy_no_verbatim_captions_in_ledger` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_numeral_agreement_engine.py::test_zero_collision_guarantee_large_scale` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_ohoiko_paired_headword_split.py::test_clean_tokens_and_ocr_lookalike_dispositions` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_ohoiko_paired_headword_split.py::test_english_contaminated_second_leg_is_multiword` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_vocab_gen.py::TestVesumEnrichment::test_verb_gets_pos` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_esum_search.py::test_search_esum_nonexistent_word_returns_empty_list` | Stale selection entry: the named test is absent from the current source tree. |
| `tests/test_esum_search.py::test_search_esum_maty_is_outside_volume_one_scope` | Stale selection entry: the named test is absent from the current source tree. |
