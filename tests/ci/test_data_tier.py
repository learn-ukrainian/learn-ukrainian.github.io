"""Audited nightly data-tier selection, receipt, and single-issue reporting."""

from __future__ import annotations

import gc
import hashlib
import json
import os
import sqlite3
import stat
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ci import data_tier

pytestmark = pytest.mark.reads_content


# H126 is the frozen #9981-c case inventory. G177 adds 48 collected custody
# cases (fixture closure reaches the default store factory) and three collected
# grammar-component cases. The two injected-binding contracts are synthetic;
# six local fixture overrides are accounted for separately below.
HISTORICAL_H126 = frozenset([
    "tests/agent_runtime/test_review_mcp.py::test_sources_server_stdio_integration",
    "tests/audit/test_antonenko_prose_narrowing.py::test_marker_constant_excludes_overbroad_phrases",
    "tests/audit/test_antonenko_prose_narrowing.py::test_narrowed_retrieval_fires_on_russianism_phrase",
    "tests/audit/test_antonenko_prose_narrowing.py::test_fallback_activates_when_narrowed_query_finds_nothing",
    "tests/audit/test_antonenko_prose_narrowing.py::test_rendered_prompt_surfaces_narrowed_status",
    "tests/audit/test_antonenko_prose_narrowing.py::test_hits_preserve_backward_compatible_fields",
    "tests/build/test_fresh_style_cards.py::test_card_exemplars_are_attested_in_the_corpus[a1]",
    "tests/build/test_fresh_style_cards.py::test_card_exemplars_are_attested_in_the_corpus[a2]",
    "tests/build/test_fresh_style_cards.py::test_card_exemplars_are_attested_in_the_corpus[b1plus]",
    "tests/curriculum/evidence/test_evidence_cli.py::test_cli_dry_run_committed_five_lemmas_request",
    "tests/mcp/test_ua_gec_search.py::test_search_ua_gec_errors_execution",
    "tests/mcp/test_ua_gec_search.py::test_search_ua_gec_errors_tag_filter_does_not_raise",
    "tests/test_adjective_mechanics_engine.py::test_vesum_verification",
    "tests/test_admit_fmu_boosters.py::test_fmu_booster_all_single_words_vesum_attested",
    "tests/test_adverb_mechanics_engine.py::test_vesum_verification_clean",
    "tests/test_adverb_mechanics_engine.py::test_vesum_sanitization_and_malformed_token_detection",
    "tests/test_adverb_mechanics_engine.py::test_vesum_rejects_empty_and_punctuation_answers",
    "tests/test_atlas_conformance.py::test_real_lexicon_manifest_membership_conforms",
    "tests/test_atlas_conformance.py::test_heritage_lemma_lookup_attests_grinchenko_word_real_db",
    "tests/test_check_text.py::test_mcp_call_tool_dispatch",
    "tests/test_check_text.py::test_mcp_book_calque_acceptance",
    "tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\\u0412\\u0456\\u043d \\u043f\\u0440\\u0438\\u0439\\u043d\\u044f\\u0432 \\u043f\\u0440\\u043e\\u043f\\u043e\\u0437\\u0438\\u0446\\u0456\\u044e \\u0441\\u0442\\u0430\\u0442\\u0438 \\u0434\\u0438\\u0440\\u0435\\u043a\\u0442\\u043e\\u0440\\u043e\\u043c]",
    "tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\\u041a\\u043e\\u0440\\u043e\\u043b\\u044c \\u043f\\u0440\\u0438\\u0439\\u043d\\u044f\\u0432 \\u043f\\u0440\\u043e\\u043f\\u043e\\u0437\\u0438\\u0446\\u0456\\u044e \\u0441\\u0443\\u043b\\u0442\\u0430\\u043d\\u0430]",
    "tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\\u0412\\u0456\\u043d \\u0441\\u0442\\u043e\\u044f\\u0432 \\u043d\\u0430 \\u043f\\u0440\\u043e\\u0442\\u044f\\u0437\\u0456 \\u043a\\u0456\\u043b\\u044c\\u043a\\u0430 \\u0445\\u0432\\u0438\\u043b\\u0438\\u043d]",
    "tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\\u0412\\u0456\\u043d \\u0441\\u0438\\u0434\\u0456\\u0432 \\u043d\\u0430 \\u043f\\u0440\\u043e\\u0442\\u044f\\u0437\\u0456 \\u0433\\u043e\\u0434\\u0438\\u043d\\u0438 \\u0434\\u0432\\u0456 \\u0439 \\u0437\\u0430\\u0441\\u0442\\u0443\\u0434\\u0438\\u0432\\u0441\\u044f]",
    "tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\\u0412\\u043e\\u043d\\u0438 \\u0432\\u0442\\u0440\\u0430\\u0442\\u0438\\u043b\\u0438 \\u0441\\u0432\\u0456\\u0434\\u043e\\u043c\\u0456\\u0441\\u0442\\u044c \\u0441\\u0432\\u043e\\u0454\\u0457 \\u0432\\u0456\\u0434\\u043f\\u043e\\u0432\\u0456\\u0434\\u0430\\u043b\\u044c\\u043d\\u043e\\u0441\\u0442\\u0456]",
    "tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\\u042f\\u043a \\u043d\\u0435 \\u0434\\u0438\\u0432\\u043d\\u043e, \\u0432\\u0456\\u043d \\u043f\\u0440\\u0438\\u0439\\u0448\\u043e\\u0432]",
    "tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\\u041f\\u043e \\u043c\\u043e\\u0457\\u0439 \\u0434\\u0443\\u043c\\u0446\\u0456 \\u0442\\u0430\\u043a \\u043d\\u0435 \\u043c\\u043e\\u0436\\u043d\\u0430 \\u0440\\u043e\\u0431\\u0438\\u0442\\u0438]",
    "tests/test_check_text.py::test_mcp_concluding_is_reported_once",
    "tests/test_check_text.py::test_real_ua_gec_skipped_kind_tokens_dropped_and_counted",
    "tests/test_check_text.py::test_synthetic_shadow_curated_and_suspicion_split",
    "tests/test_check_text.py::test_acceptance_textbook_fixture_correctness_and_planted",
    "tests/test_check_text.py::test_speed_warm_call_under_2s",
    "tests/test_check_text.py::test_bench_check_text_reduced",
    "tests/test_content_lexicon_reconciler.py::test_real_vesum_db_smoke_recognizes_basic_inflected_form",
    "tests/test_content_spelling_gate.py::test_real_vesum_db_recognizes_valid_form_and_flags_typo",
    "tests/test_curated_seed_to_lexical_jsonl.py::test_sample_seed_round_trips_through_projection",
    "tests/test_esum_search.py::test_search_esum_nonexistent_word_returns_empty_list",
    "tests/test_esum_search.py::test_search_esum_sibir_is_outside_volume_one_scope",
    "tests/test_esum_search.py::test_search_esum_maty_is_outside_volume_one_scope",
    "tests/test_esum_search.py::test_search_esum_berkut_returns_turkic_origin",
    "tests/test_esum_search.py::test_search_esum_bereza_returns_indo_european_cognates",
    "tests/test_esum_search.py::test_search_esum_voda_returns_cross_slavic_and_proto_slavic_cognates",
    "tests/test_generate_practice_deck.py::test_live_heritage_normative_support_is_verbatim_and_names_every_frame",
    "tests/test_generate_practice_deck.py::test_live_language_review_fixes_are_source_bound",
    "tests/test_generate_practice_deck.py::test_live_paronym_gloss_sources_are_verbatim_and_two_sided_or_withheld",
    "tests/test_interjection_mechanics_engine.py::test_vesum_verification_100_percent",
    "tests/test_interjection_mechanics_engine.py::test_is_valid_vesum_token_rejections_and_compounds",
    "tests/test_interjection_mechanics_engine.py::test_cli_verify_vesum_present",
    "tests/test_mcp_sources_identity_integration.py::test_real_transport_attests_endpoint_identity_against_local_files",
    "tests/test_mcp_sources_identity_integration.py::test_real_transport_preflight_requires_every_frozen_tool",
    "tests/test_mcp_sources_identity_integration.py::test_real_transport_verify_words_round_trip_is_harmless_and_public",
    "tests/test_mcp_sources_identity_integration.py::test_real_endpoint_logs_hash_only_never_argument_values_or_response_text",
    "tests/test_mcp_sources_identity_integration.py::test_real_transport_fails_closed_on_a_real_tool_error",
    "tests/test_mcp_sources_server.py::TestIntegrationSmoke::test_smoke_verify_word_archaic",
    "tests/test_mcp_sources_server.py::TestIntegrationSmoke::test_smoke_verify_lemma_archaic",
    "tests/test_mcp_sources_server.py::TestIntegrationSmoke::test_smoke_check_modern_form_mixed",
    "tests/test_mcp_sources_server.py::TestIntegrationSmoke::test_smoke_check_modern_form_modern_only",
    "tests/test_mcp_sources_server.py::TestIntegrationSmoke::test_smoke_check_modern_form_archaic_only",
    "tests/test_morphological_validator.py::TestVerbDetection::test_standalone_verb_caught",
    "tests/test_morphological_validator.py::TestVerbDetection::test_verb_in_chunk_exempt",
    "tests/test_morphological_validator.py::TestVerbDetection::test_verb_after_m15_ok",
    "tests/test_morphological_validator.py::TestCaseDetection::test_locative_caught",
    "tests/test_morphological_validator.py::TestCaseDetection::test_nominative_ok",
    "tests/test_morphological_validator.py::TestCaseDetection::test_adverb_not_flagged_as_case",
    "tests/test_morphological_validator.py::TestChunkExceptions::test_farewell_exempt",
    "tests/test_morphological_validator.py::TestImperativeDetection::test_imperative_caught",
    "tests/test_morphological_validator.py::TestImperativeDetection::test_imperative_in_callout_caught",
    "tests/test_morphological_validator.py::TestImperativeDetection::test_imperative_after_m47_ok",
    "tests/test_morphological_validator.py::TestPOSMismatch::test_verb_only_word_caught",
    "tests/test_morphological_validator.py::TestStressMarks::test_stressed_words_not_split",
    "tests/test_morphological_validator.py::TestStressMarks::test_stressed_adjective_list",
    "tests/test_morphological_validator.py::TestAccusativeConstraint::test_accusative_caught_nom_only",
    "tests/test_morphological_validator.py::TestPresentTenseOnly::test_past_tense_caught",
    "tests/test_morphological_validator.py::TestPresentTenseOnly::test_noun_homonym_not_flagged_as_past",
    "tests/test_morphological_validator.py::TestAccusativeHomonyms::test_verb_homonym_not_flagged_as_acc",
    "tests/test_morphological_validator.py::TestNonA1Imperatives::test_b1_imperative_ok",
    "tests/test_morphological_validator.py::TestAgreement::test_mismatch_caught",
    "tests/test_morphological_validator.py::TestAgreement::test_correct_agreement_ok",
    "tests/test_morphological_validator.py::TestAgreement::test_це_not_flagged",
    "tests/test_morphological_validator.py::TestAgreement::test_sentence_boundary_respected",
    "tests/test_morphological_validator.py::TestBracketStripping::test_phonetic_brackets_skipped",
    "tests/test_morphological_validator.py::TestBracketStripping::test_regular_words_still_checked",
    "tests/test_morphological_validator.py::TestBracketStripping::test_markdown_links_preserved",
    "tests/test_numeral_agreement_engine.py::test_zero_collision_guarantee_large_scale",
    "tests/test_numeral_mechanics_engine.py::test_vesum_verification_clean",
    "tests/test_ohoiko_paired_headword_split.py::test_english_contaminated_second_leg_is_multiword",
    "tests/test_ohoiko_paired_headword_split.py::test_resolve_leg_lemma_recovers_ocr_lookalikes",
    "tests/test_ohoiko_paired_headword_split.py::test_space_collapse_requires_collapsed_vesum_and_invalid_components",
    "tests/test_ohoiko_paired_headword_split.py::test_space_collapse_marks_multi_component_tokenization_manual",
    "tests/test_ohoiko_paired_headword_split.py::test_clean_tokens_and_ocr_lookalike_dispositions",
    "tests/test_ohoiko_paired_headword_split.py::test_ulp_taught_leftovers_heritage_holds",
    "tests/test_ohoiko_paired_headword_split.py::test_analyze_all_curated_leftovers_disposition",
    "tests/test_ohoiko_paired_headword_split.py::test_live_curated_unit_a_leftovers_census_invariants",
    "tests/test_ohoiko_paired_headword_split.py::test_classify_taught_candidate",
    "tests/test_ohoiko_paired_headword_split.py::test_live_taught_residual_census_invariants",
    "tests/test_open_model_phase3_v3a_taxonomy_denominator_compatibility.py::test_local_source_db_reproduces_content_blind_evidence_when_available",
    "tests/test_practice_quality_gate.py::test_reviewer_source_label_probe_on_committed_err_0005[True]",
    "tests/test_practice_quality_gate.py::test_reviewer_probe_on_the_committed_deck_and_real_sources_db",
    "tests/test_practice_quality_gate.py::test_production_practice_shards_all_modes_gate_passes",
    "tests/test_reattribute_ukrlib.py::TestPostSearchQuality::test_post_author_chunks_in_sources_db[\\u041a\\u043e\\u0446\\u044e\\u0431\\u0438\\u043d\\u0441\\u044c\\u043a\\u0438\\u0439 \\u041c.-Fata Morgana]",
    "tests/test_reattribute_ukrlib.py::TestPostSearchQuality::test_post_author_chunks_in_sources_db[\\u041a\\u043e\\u0442\\u043b\\u044f\\u0440\\u0435\\u0432\\u0441\\u044c\\u043a\\u0438\\u0439 \\u0406.-\\u0415\\u043d\\u0435\\u0457\\u0434\\u0430]",
    "tests/test_reattribute_ukrlib.py::TestPostSearchQuality::test_post_author_chunks_in_sources_db[\\u041c\\u0438\\u0440\\u043d\\u0438\\u0439 \\u041f.-\\u0425\\u0456\\u0431\\u0430 \\u0440\\u0435\\u0432\\u0443\\u0442\\u044c \\u0432\\u043e\\u043b\\u0438]",
    "tests/test_reattribute_ukrlib.py::TestPostSearchQuality::test_post_author_chunks_in_sources_db[\\u0422\\u0438\\u0447\\u0438\\u043d\\u0430 \\u041f.-\\u0410\\u0440\\u0444\\u0430\\u043c\\u0438, \\u0430\\u0440\\u0444\\u0430\\u043c\\u0438]",
    "tests/test_reattribute_ukrlib.py::TestPostSearchQuality::test_post_author_chunks_in_sources_db[\\u041d\\u0435\\u0447\\u0443\\u0439-\\u041b\\u0435\\u0432\\u0438\\u0446\\u044c\\u043a\\u0438\\u0439 \\u0406.-\\u041a\\u0430\\u0439\\u0434\\u0430\\u0448\\u0435\\u0432\\u0430 \\u0441\\u0456\\u043c'\\u044f]",
    "tests/test_typesafe_distractor_validator.py::test_target_missing_from_vesum_triggers_fail_broken",
    "tests/test_typesafe_distractor_validator.py::test_ground_with_sources_direct",
    "tests/test_verb_mechanics_engine.py::test_vesum_verification",
    "tests/test_vesum_heritage_attestation.py::test_folk_vesum_gate_accepts_engine_authentic_not_in_allowlist",
    "tests/test_vesum_heritage_attestation.py::test_folk_vesum_gate_still_rejects_teaching_prose_russianisms",
    "tests/test_vesum_heritage_attestation.py::test_folk_vesum_gate_accepts_oblique_inflections_of_dialect_words",
    "tests/test_vesum_heritage_attestation.py::test_folk_vesum_gate_accepts_negated_participles_of_standard_bases",
    "tests/test_vesum_heritage_attestation.py::test_folk_vesum_gate_accepts_productive_derivational_bases",
    "tests/test_vesum_heritage_attestation.py::test_folk_vesum_gate_accepts_productive_noun_diminutives",
    "tests/test_vesum_heritage_attestation.py::test_folk_vesum_gate_accepts_inflected_denominal_adjectives",
    "tests/test_vesum_heritage_attestation.py::test_morphology_fallback_does_not_leak_russianism_via_verb_root",
    "tests/test_vesum_heritage_attestation.py::test_derivational_fallback_does_not_leak_adversarial_russianisms",
    "tests/test_vesum_heritage_attestation.py::test_direct_standard_active_participle_calques_stay_existing_behavior",
    "tests/test_vocab_coverage.py::test_inflection_via_vesum_lemma",
    "tests/test_vocab_gen.py::TestVesumEnrichment::test_noun_gets_pos_and_gender",
    "tests/test_vocab_gen.py::TestVesumEnrichment::test_verb_gets_pos",
    "tests/verification/test_antonenko_patterns.py::test_live_all_checks_clean_corpus",
    "tests/verification/test_antonenko_patterns.py::test_live_recommendations_vesum",
    "tests/verification/test_antonenko_patterns.py::test_live_evidence_chunks_contain_condemned_forms",
    "tests/wiki/test_grade_filter.py::test_search_textbooks_does_not_apply_hard_grade_filter",
    "tests/wiki/test_t1_t2_pipeline.py::test_t1_t2_pipeline_surfaces_section_level_a1_evidence"
])
CURRENT_G177 = HISTORICAL_H126 | frozenset([
    "tests/projects/open_model_data/test_grammar_component_8342.py::test_acceptance_audit_gate_end_to_end",
    "tests/projects/open_model_data/test_grammar_component_8342.py::test_linguistic_catalog_vocative_and_voice_precision",
    "tests/projects/open_model_data/test_grammar_component_8342.py::test_signoff_generator_strict_criteria_and_index_validation",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_textbook_cohort_summary_missing_on_host_reflects_archive_reachability",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_allows_missing_report_valid_prose_with_reserved_words",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_chunk_file_missing_for_permitted_textbook",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_cohort_id_mismatch_in_summary",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_contradictory_eligibility_and_forged_summary",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_duplicate_missing_source_id_and_omissions",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_duplicate_source_id",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_duplicate_source_locator",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_evidence_ref_private_host_path[/home/alice/source.jsonl]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_evidence_ref_private_host_path[C:\\\\Users\\\\alice\\\\source.jsonl]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_evidence_ref_private_host_path[\\\\\\\\server\\\\share\\\\evidence.jsonl]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_forged_access_id",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_forged_receipt_id_and_verdict",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_hash_tampering",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_index_header_tampering_and_corpus_leakage",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_mismatched_custody_status_or_host_reachable",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_provenance_index",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_report_freeform_private_host_paths[field_path0-fixture-home-archive]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_report_freeform_private_host_paths[field_path1-alice at /home/alice]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_report_freeform_private_host_paths[field_path2-processing C:\\\\Users\\\\alice\\\\data]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_report_freeform_private_host_paths[field_path3-Proceed using \\\\\\\\server\\\\share\\\\data.pdf]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_report_freeform_private_host_paths[field_path4-fixture-home-mount]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_report_freeform_private_host_paths[field_path5-blocked by C:\\\\private\\\\job]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_report_freeform_private_host_paths[field_path6-/root/admin]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_report_freeform_private_host_paths[field_path7-location=/opt/private-corpus]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_missing_report_freeform_private_host_paths[field_path8-prefix:/opt/private-corpus]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_provenance_projection_mismatch",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_recomputed_safety_assertion_violations[fixture-home-book]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_recomputed_safety_assertion_violations[C:\\\\Users\\\\alice\\\\private\\\\book.pdf]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_recomputed_safety_assertion_violations[\\\\\\\\server\\\\share\\\\private\\\\book.pdf]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_recomputed_safety_assertion_violations[relative/path/appdata/secrets.txt]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_database_stream_metrics",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_missing_report_items",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_missing_report_metadata[issue-12345-Missing report issue mismatch]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_missing_report_metadata[operator_decision_date-1999-01-01-Missing report operator_decision_date mismatch]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_missing_report_metadata[owner-unauthorized-party-Missing report owner mismatch]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_missing_report_metadata[scope-all datasets globally-Missing report scope mismatch]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_missing_report_metadata[unmounted_archive_locator-s3://tampered-bucket-Missing report unmounted_archive_locator mismatch]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_primary_store_in_index",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_progression_decision[description-Tampered progression decision text without any private paths]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_progression_decision[permitted-False]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_tampered_progression_decision[permitted_cohort_ids-mutation_val1]",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_unmounted_textbook_tampered_as_accessible",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_detects_unpermitted_source_in_database",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_handles_stub_database_with_missing_tables",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_passes_on_committed_artifacts",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_rejects_contradictory_lineage_status_and_mode_combinations",
    "tests/projects/open_model_data/test_v4_source_custody_access.py::test_verify_rejects_unknown_mode_labeled_as_confirmed_native"
])
LOCAL_OVERRIDE_REAL_STORE = frozenset([
    "tests/projects/open_model_data/test_phase3_corpus_miners.py::test_independent_sources_grounding",
    "tests/projects/open_model_data/test_phase3_corpus_miners.py::test_independent_vesum_lemma_attestation",
    "tests/projects/open_model_data/test_phase3_decolonization_partition.py::test_preserve_cases_verbatim_target_and_vesum_attestation",
    "tests/projects/open_model_data/test_phase3_decolonization_partition.py::test_derivational_closure_independent_zero_leakage",
    "tests/projects/open_model_data/test_phase3_decolonization_partition.py::test_ua_gec_test_split_strict_zero_leakage",
    "tests/projects/open_model_data/test_phase3_decolonization_partition.py::test_independent_minhash_cross_split_verification"
])
NEW_STORE_SELECTIONS = frozenset([
    "tests/test_atlas_conformance.py::test_real_lexicon_manifest_membership_conforms",
    "tests/test_esum_search.py::test_search_esum_nonexistent_word_returns_empty_list",
    "tests/test_esum_search.py::test_search_esum_sibir_is_outside_volume_one_scope",
    "tests/test_esum_search.py::test_search_esum_maty_is_outside_volume_one_scope",
    "tests/verification/test_antonenko_patterns.py::test_live_all_checks_clean_corpus",
    "tests/verification/test_antonenko_patterns.py::test_live_recommendations_vesum",
    "tests/verification/test_antonenko_patterns.py::test_live_evidence_chunks_contain_condemned_forms",
    "tests/test_check_text.py::test_mcp_book_calque_acceptance",
    "tests/test_check_text.py::test_mcp_concluding_is_reported_once",
    r"tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\u0412\u0456\u043d \u043f\u0440\u0438\u0439\u043d\u044f\u0432 \u043f\u0440\u043e\u043f\u043e\u0437\u0438\u0446\u0456\u044e \u0441\u0442\u0430\u0442\u0438 \u0434\u0438\u0440\u0435\u043a\u0442\u043e\u0440\u043e\u043c]",
    r"tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\u041a\u043e\u0440\u043e\u043b\u044c \u043f\u0440\u0438\u0439\u043d\u044f\u0432 \u043f\u0440\u043e\u043f\u043e\u0437\u0438\u0446\u0456\u044e \u0441\u0443\u043b\u0442\u0430\u043d\u0430]",
    r"tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\u0412\u0456\u043d \u0441\u0442\u043e\u044f\u0432 \u043d\u0430 \u043f\u0440\u043e\u0442\u044f\u0437\u0456 \u043a\u0456\u043b\u044c\u043a\u0430 \u0445\u0432\u0438\u043b\u0438\u043d]",
    r"tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\u0412\u0456\u043d \u0441\u0438\u0434\u0456\u0432 \u043d\u0430 \u043f\u0440\u043e\u0442\u044f\u0437\u0456 \u0433\u043e\u0434\u0438\u043d\u0438 \u0434\u0432\u0456 \u0439 \u0437\u0430\u0441\u0442\u0443\u0434\u0438\u0432\u0441\u044f]",
    r"tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\u0412\u043e\u043d\u0438 \u0432\u0442\u0440\u0430\u0442\u0438\u043b\u0438 \u0441\u0432\u0456\u0434\u043e\u043c\u0456\u0441\u0442\u044c \u0441\u0432\u043e\u0454\u0457 \u0432\u0456\u0434\u043f\u043e\u0432\u0456\u0434\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u0456]",
    r"tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\u042f\u043a \u043d\u0435 \u0434\u0438\u0432\u043d\u043e, \u0432\u0456\u043d \u043f\u0440\u0438\u0439\u0448\u043e\u0432]",
    r"tests/test_check_text.py::test_mcp_round2_no_firm_book_false_positives[\u041f\u043e \u043c\u043e\u0457\u0439 \u0434\u0443\u043c\u0446\u0456 \u0442\u0430\u043a \u043d\u0435 \u043c\u043e\u0436\u043d\u0430 \u0440\u043e\u0431\u0438\u0442\u0438]"
])
PREVIOUS_SELECTION_SHA256 = "9f33687f8c73317ecd9263d819700b024f55ab327eddf990926c04e5f019349d"
PREVIOUS_SELECTION_FILES_SHA256 = "e9370daea41d82bc7278d31fc137f9461c0e0e720ecde9b219aa362d86c7034c"


def test_selection_matches_class_c_audit_and_excludes_opt_ins() -> None:
    selection = data_tier.load_selection()
    assert selection["source_run"] == 36611889906
    assert selection["source_sha"] == "410da34bb875aca2acfc960da4d8c9b87ae7867b"
    # The audited baseline is preserved; #10021 adds the 16 exact factory omissions.
    assert selection["class_c_merge_group"] == 558
    assert selection["class_c_nightly"] == 1
    assert len(selection["nodeids"]) == 558
    assert len(selection["files"]) == 103
    assert "tests/test_citation_resolution_invariant.py" in selection["nodeids"]
    assert "tests/test_site_links.py::TestCurriculumSync::test_manifest_modules_have_mdx[a1]" in selection["nodeids"]
    assert len([nodeid for nodeid in selection["nodeids"] if nodeid.startswith("sha256:")]) == 5
    assert set(selection["artifact_groups"]) == {
        "open_model_other_indexes",
        "open_model_release_payload",
        "open_model_evidence_indexes",
        "open_model_component_payload",
        "open_model_archive_payload",
        "open_model_study_outputs",
        "corpus_audit_snapshots",
        "lexicon_candidates",
        "lexicon_recovery_snapshots",
    }
    assert all(Path(path).is_file() for path in selection["files"])
    joined = "\n".join(selection["nodeids"])
    assert "/home/" not in joined
    for forbidden in ("TYPESAFE_LIVE", "RUN_BRIDGE_INBOX_INTEGRATION", "ZNO_LIVE", "sandbox-exec", "mlx_"):
        assert forbidden not in joined


def test_real_store_selection_preserves_h126_and_covers_g177_and_overrides() -> None:
    selection = data_tier.load_selection()
    assert len(HISTORICAL_H126) == 126
    assert len(CURRENT_G177) == 177
    assert HISTORICAL_H126 <= CURRENT_G177
    assert len(LOCAL_OVERRIDE_REAL_STORE) == 6
    identified = CURRENT_G177 | LOCAL_OVERRIDE_REAL_STORE
    assert len(identified) == 183

    selected = set(selection["nodeids"])
    collected_files = set(selection["files"])
    assert {nodeid.split("::", 1)[0] for nodeid in identified} <= collected_files
    assert all(
        nodeid in selected
        or data_tier._key(nodeid) in selected
        or nodeid.split("::", 1)[0] in selected
        for nodeid in identified
    )
    assert selected >= NEW_STORE_SELECTIONS
    assert selection["real_store_audit"] == {
        "issue": 10021,
        "historical_h126": 126,
        "current_factory_g177": 177,
        "identified_real_store_cases": 183,
        "new_selection_entries": 16,
        "new_collection_files": 1,
    }
    previous = selected - NEW_STORE_SELECTIONS
    assert len(previous) == 542
    assert hashlib.sha256("\n".join(sorted(previous)).encode()).hexdigest() == PREVIOUS_SELECTION_SHA256
    previous_files = collected_files - {"tests/verification/test_antonenko_patterns.py"}
    assert len(previous_files) == 102
    assert hashlib.sha256("\n".join(sorted(previous_files)).encode()).hexdigest() == PREVIOUS_SELECTION_FILES_SHA256


def test_junit_summary_and_known_citation_issue(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text(
        '<testsuite><testcase classname="tests.test_citation_resolution_invariant" '
        'name="test_published_citations_resolve_invariant[wiki/grammar/b2/academic-writing.md]"><failure message="drift"/></testcase>'
        f'<testcase classname="tests.test_vesum" name="test_db"><skipped message="missing {Path.home()}/db"/></testcase>'
        '<testcase classname="tests.test_vesum" name="test_ok"/></testsuite>',
        encoding="utf-8",
    )
    data_tier.sanitize_junit(junit)
    summary = data_tier.junit_summary(junit)
    assert (summary["ran"], summary["passed"], summary["failed"], summary["skipped"]) == (3, 1, 1, 1)
    assert summary["skip_reasons"] == {"missing <host-path>": 1}
    assert (
        data_tier.known_issue(
            summary["failing_tests"][0],
            {
                "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant[wiki/grammar/b2/academic-writing.md]": 8403,
            },
        )
        == 8403
    )


def test_known_issue_maps_whole_test_function_and_exact_ids() -> None:
    whole = "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant"
    exact = "tests/test_x.py::test_y[case-a]"
    baseline = {whole: 8403, exact: 11, "tests/test_x.py::test_y": 12}
    assert data_tier.known_issue(f"{whole}[wiki/grammar/b2/academic-writing.md]", baseline) == 8403
    assert data_tier.known_issue(f"{whole}[wiki/grammar/b1/aspect.md]", baseline) == 8403
    assert data_tier.known_issue(whole, baseline) == 8403
    assert data_tier.known_issue(exact, baseline) == 11
    assert data_tier.known_issue("tests/test_x.py::test_y[case-b]", baseline) == 12
    assert data_tier.known_issue(f"{whole}_other[wiki/a.md]", baseline) is None
    assert data_tier.known_issue("tests/test_x.py::test_z[case-a]", baseline) is None
    assert data_tier.known_issue("tests/test_citation_resolution_invariant.py::test_other", baseline) is None


def test_shipped_baseline_maps_every_citation_parametrization_to_8403() -> None:
    baseline = json.loads(data_tier.BASELINE.read_text(encoding="utf-8"))["known_failures"]
    body = data_tier.issue_body(
        {
            "run_key": "run-1",
            "main_sha": "abc",
            "ran": 2,
            "passed": 0,
            "failed": 2,
            "skipped": 0,
            "failing_tests": [
                "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant[wiki/grammar/b2/dim-zhytlo.md]",
                "tests/test_esum_search.py::test_search_esum_berkut_returns_turkic_origin",
            ],
            "skip_reasons": {},
        },
        baseline,
    )
    assert "dim-zhytlo.md]` — known issue #8403" in body
    assert "test_search_esum_berkut_returns_turkic_origin` — new" in body


@pytest.fixture(autouse=True)
def _no_live_pool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The data-tier memory checks never read this host's real lu.slice (#9975)."""
    monkeypatch.setenv("LU_SLICE_CGROUP", str(tmp_path / "absent-pool" / "lu.slice"))


def _fake_slice(directory: Path, *, current: int, file_cache: int, high: str = "max") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "memory.current").write_text(f"{current}\n", encoding="ascii")
    (directory / "memory.high").write_text(f"{high}\n", encoding="ascii")
    (directory / "memory.max").write_text("max\n", encoding="ascii")
    (directory / "memory.stat").write_text(f"active_file 0\ninactive_file {file_cache}\n", encoding="ascii")
    return directory


def _slice_show(monkeypatch: pytest.MonkeyPatch, *, current: int, maximum: int, control_group: str = "") -> None:
    monkeypatch.setattr(data_tier, "available_memory", lambda: 10 * 1024**3)
    monkeypatch.setattr(
        data_tier,
        "command",
        lambda *args, **kwargs: SimpleNamespace(
            stdout=(
                f"LoadState=loaded\nActiveState=active\nMemoryCurrent={current}\nMemoryMax={maximum}\n"
                f"ControlGroup={control_group}\n"
            )
        ),
    )


def test_dispatch_slice_headroom_excludes_file_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gib = 1024**3
    monkeypatch.setattr(data_tier.pool_headroom, "CGROUP_ROOT", tmp_path / "cgroup")
    _fake_slice(tmp_path / "cgroup" / "lu.slice" / "lu-dispatch.slice", current=14 * gib, file_cache=12 * gib)
    _slice_show(monkeypatch, current=14 * gib, maximum=17 * gib, control_group="/lu.slice/lu-dispatch.slice")

    data_tier.require_memory()


def test_dispatch_slice_without_memory_stat_uses_raw_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    gib = 1024**3
    monkeypatch.setattr(data_tier.pool_headroom, "CGROUP_ROOT", tmp_path / "cgroup")
    _slice_show(monkeypatch, current=14 * gib, maximum=17 * gib, control_group="/lu.slice/lu-dispatch.slice")

    with pytest.raises(data_tier.DataTierError, match="less than 4 GiB headroom"):
        data_tier.require_memory()
    assert "using raw MemoryCurrent" in capsys.readouterr().err


def test_full_shared_pool_is_a_stop_condition(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gib = 1024**3
    pool = _fake_slice(tmp_path / "lu.slice", current=28 * gib, file_cache=gib, high=str(28 * gib))
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    _slice_show(monkeypatch, current=gib, maximum=17 * gib)

    with pytest.raises(data_tier.DataTierError, match=r"lu\.slice non-cache use 27\.0 GiB plus a 4 GiB"):
        data_tier.require_memory()


def test_shared_pool_with_cache_only_pressure_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gib = 1024**3
    pool = _fake_slice(tmp_path / "lu.slice", current=28 * gib, file_cache=14 * gib, high=str(28 * gib))
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    _slice_show(monkeypatch, current=gib, maximum=17 * gib)

    data_tier.require_memory()


def test_missing_pool_cgroup_skips_and_logs(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _slice_show(monkeypatch, current=1024, maximum=20 * 1024**3)

    data_tier.require_memory()

    err = capsys.readouterr().err
    assert "lu.slice pool check skipped" in err
    assert "/" not in err.split("skipped", 1)[1]


def test_memory_floor_is_a_stop_condition(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data_tier, "available_memory", lambda: 6 * 1024**3 - 1)
    with pytest.raises(data_tier.DataTierError, match="below the 6 GiB floor"):
        data_tier.require_memory()


def test_selection_filters_exact_ids_before_xdist(tmp_path: Path) -> None:
    ordinary = "tests/test_sample.py::test_data"
    private = "tests/test_sample.py::test_bulk[private fixture]"
    citation = "tests/test_citation_resolution_invariant.py::test_one[wiki/a1/example.md]"
    selection = {
        "nodeids": [ordinary, data_tier._key(private), "tests/test_citation_resolution_invariant.py"],
        "bulk_nodeids": [data_tier._key(private)],
    }

    class Item:
        def __init__(self, nodeid: str, live: bool = False) -> None:
            self.nodeid = nodeid
            self.live = live

        def get_closest_marker(self, marker: str) -> object | None:
            return object() if self.live and marker == "live_network" else None

    deselected = []
    config = SimpleNamespace(hook=SimpleNamespace(pytest_deselected=lambda items: deselected.extend(items)))
    plugin = data_tier.SelectionPlugin(selection, None, "mount absent", tmp_path / "collected.json")
    items = [Item(ordinary), Item(private), Item(citation), Item("tests/test_sample.py::test_live", live=True)]
    plugin.pytest_collection_modifyitems(items, config)

    assert plugin.selected_nodeids == [ordinary, citation]
    assert plugin.bulk_skipped == [private]
    assert [item.nodeid for item in items] == [ordinary, citation]
    assert len(deselected) == 2
    assert json.loads((tmp_path / "collected.json").read_text()) == [ordinary, citation]


def test_child_passes_only_selected_ids_to_two_workers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = "tests/test_sample.py::test_data"
    ignored = "tests/test_sample.py::test_unrelated"
    monkeypatch.setattr(
        data_tier,
        "load_selection",
        lambda: {"nodeids": [selected], "files": ["tests/test_sample.py"], "bulk_nodeids": []},
    )

    class Item:
        def __init__(self, nodeid: str) -> None:
            self.nodeid = nodeid

        def get_closest_marker(self, _marker: str) -> None:
            return None

    def collect(_argv: list[str], *, plugins: list[data_tier.SelectionPlugin]) -> int:
        items = [Item(selected), Item(ignored)]
        config = SimpleNamespace(hook=SimpleNamespace(pytest_deselected=lambda items: None))
        plugins[0].pytest_collection_modifyitems(items, config)
        return 0

    calls = []

    def execute(argv: list[str], *, timeout: int) -> int:
        calls.append(argv)
        assert timeout == 21600
        junit.write_text('<testsuite><testcase classname="tests.test_sample" name="test_data"/></testsuite>')
        return 0

    monkeypatch.setattr(data_tier.pytest, "main", collect)
    monkeypatch.setattr(data_tier, "run_process_group", execute)
    junit = tmp_path / "junit.xml"
    args = SimpleNamespace(junit=str(junit), collected=str(tmp_path / "collected.json"), only=None, bulk_reason=None)
    assert data_tier.pytest_child(args) == 0
    assert len(calls) == 1
    assert calls[0][-1] == selected
    assert ignored not in calls[0]
    assert calls[0][calls[0].index("-n") + 1] == "2"
    assert "--require-data" in calls[0]


def test_collection_time_data_skip_is_in_junit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = "tests/test_citation_resolution_invariant.py"
    monkeypatch.setattr(data_tier, "load_selection", lambda: {"nodeids": [module], "files": [module]})

    def collect(_argv: list[str], *, plugins: list[data_tier.SelectionPlugin]) -> int:
        report = SimpleNamespace(failed=False, skipped=True, nodeid=module, longrepr=(module, 1, "sources.db absent"))
        plugins[0].pytest_collectreport(report)
        return 5

    monkeypatch.setattr(data_tier.pytest, "main", collect)
    junit = tmp_path / "junit.xml"
    args = SimpleNamespace(junit=str(junit), collected=str(tmp_path / "collected.json"), only=None, bulk_reason=None)
    assert data_tier.pytest_child(args) == 0
    assert data_tier.junit_summary(junit)["skip_reasons"] == {"sources.db absent": 1}


def test_failure_reporting_uses_one_fake_gh_issue_and_clean_comment_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(data_tier.github_client, "run", subprocess.run)
    executable = tmp_path / "gh"
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"issue": None, "comments": [], "calls": []}), encoding="utf-8")
    executable.write_text(
        f"#!{sys.executable}\n"
        "import json, pathlib, sys\n"
        f"path = pathlib.Path({str(state)!r})\n"
        "state = json.loads(path.read_text())\n"
        "args = sys.argv[1:]\n"
        "state['calls'].append(args[:2])\n"
        "if args[:2] == ['issue', 'list']:\n"
        "    print(json.dumps([state['issue']] if state['issue'] else []))\n"
        "elif args[:2] == ['issue', 'create']:\n"
        "    state['issue'] = {'number': 77, 'title': '[infra][tests] Nightly data-tier failures', 'state': 'OPEN'}\n"
        "    state['body'] = sys.stdin.read()\n"
        "    print('issue 77')\n"
        "elif args[:2] == ['issue', 'edit']:\n"
        "    state['body'] = sys.stdin.read()\n"
        "elif args[:2] == ['issue', 'view']:\n"
        "    print(json.dumps({'comments': [{'body': body} for body in state['comments']]}))\n"
        "elif args[:2] == ['issue', 'comment']:\n"
        "    state['comments'].append(args[-1])\n"
        "elif args[:2] == ['issue', 'close']:\n"
        "    state['issue']['state'] = 'CLOSED'\n"
        "elif args[:2] == ['issue', 'reopen']:\n"
        "    state['issue']['state'] = 'OPEN'\n"
        "else:\n"
        "    sys.exit(4)\n"
        "path.write_text(json.dumps(state))\n",
        encoding="utf-8",
    )
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    failed = {
        "run_key": "run-1",
        "main_sha": "a" * 40,
        "ran": 2,
        "passed": 1,
        "failed": 1,
        "skipped": 0,
        "failing_tests": [
            "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant[wiki/grammar/b2/academic-writing.md]"
        ],
        "skip_reasons": {},
    }
    baseline = {
        "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant[wiki/grammar/b2/academic-writing.md]": 8403
    }
    assert data_tier.report(failed, baseline).startswith("created")
    assert data_tier.report(failed, baseline) == "updated issue #77"
    clean = {**failed, "failed": 0, "passed": 2, "failing_tests": []}
    for errors in (
        {"runner_errors": ["memory guard stopped the run"]},
        {"hydration_errors": {"group": "hydrate failed"}},
        {"missing_databases": ["sources.db"]},
    ):
        assert data_tier.report({**clean, **errors}, baseline) == "updated issue #77"
        assert json.loads(state.read_text())["comments"] == []
    assert data_tier.report(failed, baseline) == "updated issue #77"
    assert data_tier.report(clean, baseline) == "closed issue #77 after clean run"
    assert data_tier.report({**clean, "run_key": "run-2"}, baseline) == "no issue change"
    result = json.loads(state.read_text(encoding="utf-8"))
    assert "known issue #8403" in result["body"]
    assert len(result["comments"]) == 1
    assert result["calls"].count(["issue", "create"]) == 1
    assert result["calls"].count(["issue", "edit"]) == 5
    assert result["issue"]["state"] == "CLOSED"
    assert result["calls"].count(["issue", "close"]) == 1
    assert data_tier.report({**failed, "run_key": "run-3"}, baseline) == "updated issue #77"
    assert data_tier.report({**clean, "run_key": "run-4"}, baseline) == "closed issue #77 after clean run"
    result = json.loads(state.read_text())
    assert len(result["comments"]) == 2
    assert result["calls"].count(["issue", "create"]) == 1


@pytest.mark.parametrize(
    ("active", "current", "maximum", "error"),
    [
        ("inactive", "[not set]", "infinity", None),
        ("active", "1024", "infinity", None),
        ("active", "1024", str(8 * 1024**3), None),
        ("active", "[not set]", "infinity", "unknown"),
        ("active", "1024", "invalid", "unknown"),
        ("active", str(8 * 1024**3), str(10 * 1024**3), "headroom"),
    ],
)
def test_slice_memory_states(
    monkeypatch: pytest.MonkeyPatch, active: str, current: str, maximum: str, error: str | None
) -> None:
    monkeypatch.setattr(data_tier, "available_memory", lambda: 10 * 1024**3)
    monkeypatch.setattr(
        data_tier,
        "command",
        lambda *args, **kwargs: SimpleNamespace(
            stdout=f"LoadState=loaded\nActiveState={active}\nMemoryCurrent={current}\nMemoryMax={maximum}\n"
        ),
    )
    if error:
        with pytest.raises(data_tier.DataTierError, match=error):
            data_tier.require_memory()
    else:
        data_tier.require_memory()


def test_collection_error_keeps_healthy_selected_test_and_junit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test_good.py").write_text("def test_ok():\n    assert True\n")
    (tmp_path / "test_bad.py").write_text("raise ImportError('broken import')\n")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setattr(
        data_tier,
        "load_selection",
        lambda: {
            "nodeids": ["test_good.py::test_ok"],
            "files": ["test_good.py", "test_bad.py"],
        },
    )
    junit = tmp_path / "junit.xml"
    calls = []

    def execute(argv: list[str], *, timeout: int) -> int:
        calls.append(argv)
        junit.write_text('<testsuite tests="1"><testcase classname="test_good" name="test_ok"/></testsuite>')
        return 0

    monkeypatch.setattr(data_tier, "run_process_group", execute)
    args = SimpleNamespace(junit=str(junit), collected=str(tmp_path / "collected.json"), only=None, bulk_reason=None)
    assert data_tier.pytest_child(args) == 1
    assert calls[0][-1] == "test_good.py::test_ok"
    summary = data_tier.junit_summary(junit)
    assert (summary["passed"], summary["failed"]) == (1, 1)
    assert "test_bad.py" in summary["failing_tests"]


@pytest.fixture
def nightly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[SimpleNamespace]:
    primary = tmp_path / "primary"
    project_python = primary / ".venv" / "bin" / "python"
    project_python.parent.mkdir(parents=True)
    project_python.touch()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    events = []
    reports = []
    snapshots = []
    make_snapshot = data_tier.tempfile.mkdtemp
    remove_snapshot = data_tier.shutil.rmtree

    def allocate_snapshot(*args, **kwargs):
        path = make_snapshot(*args, **kwargs)
        snapshots.append(Path(path))
        return path

    monkeypatch.setattr(data_tier.tempfile, "mkdtemp", allocate_snapshot)
    monkeypatch.setattr(data_tier, "primary_checkout", lambda: primary)
    monkeypatch.setattr(data_tier, "project_interpreter", lambda root: project_python if root == primary else None)
    monkeypatch.setattr(data_tier, "require_memory", lambda: None)
    monkeypatch.setattr(data_tier, "prune_stale_worktrees", lambda _primary: None)
    monkeypatch.setattr(data_tier, "make_test_worktree", lambda _primary: checkout)
    monkeypatch.setattr(data_tier, "command", lambda *args, **kwargs: SimpleNamespace(stdout="a" * 40))
    monkeypatch.setattr(data_tier, "snapshot_databases", lambda *args, **kwargs: [])
    monkeypatch.setattr(data_tier, "provision_host_files", lambda *args: None)
    monkeypatch.setattr(data_tier, "hydrate", lambda *args: {})
    monkeypatch.setattr(data_tier, "bulk_status", lambda *args: (None, "unavailable"))
    monkeypatch.setattr(data_tier, "stop_scope", lambda unit: events.append("stop"))
    monkeypatch.setattr(data_tier, "remove_test_worktree", lambda *args: events.append("remove"))

    def execute(argv: list[str], **kwargs: object) -> int:
        assert kwargs["cwd"] == checkout
        assert "scripts.ci.data_tier" in argv
        assert "-m" in argv
        assert 0 < kwargs["timeout"] <= data_tier.RUN_BUDGET_SECONDS
        Path(argv[argv.index("--junit") + 1]).write_text('<testsuite><testcase name="test_ok"/></testsuite>')
        return 0

    monkeypatch.setattr(data_tier, "run_process_group", execute)

    def report(summary: dict, baseline: dict) -> str:
        reports.append(json.loads(json.dumps(summary)))
        return "reported"

    monkeypatch.setattr(data_tier, "report", report)
    try:
        yield SimpleNamespace(primary=primary, events=events, reports=reports, execute=execute)
    finally:
        # Production may retain snapshots until stop is proven; tests own them
        # after their assertions, even when runner cleanup is monkeypatched.
        for snapshot in snapshots:
            if snapshot.exists():
                remove_snapshot(snapshot)
            assert not snapshot.exists()


@pytest.mark.parametrize("action", ["removed", "skipped", "error"])
def test_checkout_cleanup_obeys_guard_outcome(action: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checkout = tmp_path / ".worktrees" / "data-tier" / ("run-" + "a" * 32)
    calls = []

    def remove(path: Path, **kwargs: object) -> SimpleNamespace:
        calls.append((path, kwargs))
        return SimpleNamespace(
            action=action, reason="guard outcome", error="guard failure" if action == "error" else None
        )

    monkeypatch.setattr(data_tier.worktree_claims, "remove_unclaimed_worktree", remove)
    if action == "removed":
        data_tier.remove_test_worktree(tmp_path, checkout)
    else:
        with pytest.raises(data_tier.DataTierError, match=f"checkout cleanup {action}: guard outcome"):
            data_tier.remove_test_worktree(tmp_path, checkout)
    assert calls == [
        (
            checkout,
            {
                "repo_root": tmp_path,
                "reason": "data-tier checkout cleanup",
                "owner_task_id": None,
                "force": True,
            },
        )
    ]


def test_checkout_creation_failure_uses_guarded_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    created = []
    removed = []

    def command(argv: list[str], **kwargs: object) -> SimpleNamespace:
        if "add" in argv:
            created.append(Path(argv[-2]))
            return SimpleNamespace(stdout="")
        raise data_tier.DataTierError("fetch failed")

    monkeypatch.setattr(data_tier, "command", command)
    monkeypatch.setattr(
        data_tier, "remove_test_worktree", lambda primary, checkout: removed.append((primary, checkout))
    )
    with pytest.raises(data_tier.DataTierError, match="fetch failed"):
        data_tier.make_test_worktree(tmp_path)
    assert len(created) == 1
    assert removed == [(tmp_path, created[0])]


def test_interpreter_resolver_refusal_is_reported(nightly: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    def resolve(root: Path) -> Path:
        assert root == nightly.primary
        raise FileNotFoundError("unavailable")

    monkeypatch.setattr(data_tier, "project_interpreter", resolve)
    assert data_tier.run(SimpleNamespace(only=None, no_report=False)) == 1
    assert nightly.reports[0]["runner_errors"] == ["shared project interpreter unavailable"]
    assert nightly.events == []


@pytest.mark.parametrize(
    "failure",
    [
        "selection",
        "memory",
        "interpreter",
        "worktree",
        "snapshot",
        "hydration",
        "missing_database",
        "bulk",
        "second_memory",
        "collection",
        "runner_exit",
        "timeout",
        "malformed_junit",
        "cleanup",
        "scope_cleanup",
        "signal",
        "budget",
    ],
)
def test_every_runner_failure_reaches_report(
    nightly: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise data_tier.DataTierError("runner failed at /private/example.db")

    if failure in {"selection", "memory", "worktree", "snapshot", "bulk", "cleanup", "scope_cleanup"}:
        helper = {
            "selection": "load_selection",
            "memory": "require_memory",
            "worktree": "make_test_worktree",
            "snapshot": "snapshot_databases",
            "bulk": "bulk_status",
            "cleanup": "remove_test_worktree",
            "scope_cleanup": "stop_scope",
        }[failure]
        monkeypatch.setattr(data_tier, helper, fail)
    elif failure == "interpreter":
        (nightly.primary / ".venv" / "bin" / "python").unlink()
    elif failure == "hydration":
        monkeypatch.setattr(data_tier, "hydrate", lambda *args: {"group": "missing /private/artifact"})
    elif failure == "missing_database":
        monkeypatch.setattr(data_tier, "snapshot_databases", lambda *args, **kwargs: ["sources.db"])
    elif failure == "second_memory":
        memory_calls = iter([None, "fail"])

        def memory() -> None:
            if next(memory_calls):
                fail()

        monkeypatch.setattr(data_tier, "require_memory", memory)
    elif failure == "budget":
        clock = iter([0, data_tier.RUN_BUDGET_SECONDS + 1])
        monkeypatch.setattr(data_tier.time, "monotonic", lambda: next(clock))
    else:

        def execute(argv: list[str], **kwargs: object) -> int:
            if failure == "timeout":
                raise subprocess.TimeoutExpired("pytest", 1)
            if failure == "signal":
                os.kill(os.getpid(), data_tier.signal.SIGTERM)
            if failure == "collection":
                return 2
            nightly.execute(argv, **kwargs)
            if failure == "malformed_junit":
                Path(argv[argv.index("--junit") + 1]).write_text("invalid xml")
            return 3 if failure == "runner_exit" else 0

        monkeypatch.setattr(data_tier, "run_process_group", execute)
    assert data_tier.main(["run"]) == 1
    assert len(nightly.reports) == 1
    summary = nightly.reports[0]
    assert data_tier.run_failed(summary)
    body = data_tier.issue_body(summary, {})
    assert "/private/" not in body
    assert summary["run_key"] in body
    assert summary["runner_errors"] or summary["hydration_errors"] or summary["missing_databases"]
    receipts = list((nightly.primary / "batch_state" / "data-tier").glob("*.summary.json"))
    if failure != "selection":
        assert json.loads(receipts[0].read_text()) == summary
    if "stop" in nightly.events and failure != "cleanup":
        assert nightly.events == ["stop", "remove"]
    if failure == "scope_cleanup":
        assert nightly.events == []


def test_github_failure_is_single_attempt_and_persisted(
    nightly: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def report(summary: dict, baseline: dict) -> str:
        calls.append(json.loads(json.dumps(summary)))
        raise data_tier.DataTierError("gh unavailable at /private/gh")

    monkeypatch.setattr(data_tier, "report", report)
    assert data_tier.run(SimpleNamespace(only=None, no_report=False)) == 1
    assert len(calls) == 1
    summary = json.loads(next((nightly.primary / "batch_state" / "data-tier").glob("*.summary.json")).read_text())
    assert len(summary["runner_errors"]) == 1
    assert "/private/" not in json.dumps(summary)


def test_clean_run_and_no_report(nightly: SimpleNamespace) -> None:
    assert data_tier.run(SimpleNamespace(only=None, no_report=True)) == 0
    assert nightly.reports == []
    assert nightly.events == ["stop", "remove"]


def test_issue_body_is_bounded_with_total_and_runner_errors() -> None:
    summary = {
        "run_key": "run-1",
        "main_sha": "a" * 40,
        "ran": 700,
        "passed": 0,
        "failed": 700,
        "skipped": 0,
        "failing_tests": [f"test_{i}" + "x" * 1000 for i in range(700)],
        "skip_reasons": {},
        "runner_errors": ["runner failed at /private/log"],
        "hydration_errors": {"group": "hydrate failed"},
        "missing_databases": ["sources.db"],
    }
    body = data_tier.issue_body(summary, {})
    assert len(body) <= data_tier.ISSUE_BODY_LIMIT
    assert "700 total" in body
    assert "runner failed at <host-path>" in body
    assert "hydrate failed" in body and "sources.db" in body
    assert "Truncated" in body and "local run JUnit" in body


def test_hydration_has_total_budget_and_records_timeouts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = iter([0, 0, data_tier.HYDRATION_BUDGET_SECONDS - 10, data_tier.HYDRATION_BUDGET_SECONDS + 1])
    monkeypatch.setattr(data_tier.time, "monotonic", lambda: next(clock))
    calls = []

    def run(argv: list[str], **kwargs: object) -> None:
        calls.append(kwargs["timeout"])
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(data_tier.subprocess, "run", run)
    errors = data_tier.hydrate(tmp_path, ["first", "second", "third"], Path(sys.executable))
    assert calls == [1800, 10]
    assert errors == {
        "first": "hydration timed out",
        "second": "hydration timed out",
        "third": "hydration budget exhausted",
    }


def test_host_file_provisioning_copies_content_but_not_nested_repository_metadata(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    checkout = tmp_path / "checkout"
    nested = primary / "data" / "ua-gec"
    for relative, text in (
        ("data/train/doc.txt", "content\n"),
        (".git/HEAD", "ref: refs/heads/main\n"),
        (".git/refs/heads/entire/checkpoints/v1", "df01a9f6\n"),
        (".entire/settings.json", "{}\n"),
        (".entire/metadata/state.json", "{}\n"),
        ("python/pkg/.gitkeep", ""),
    ):
        path = nested / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    lexicon = primary / "site" / "public" / "lexicon" / "a.json"
    lexicon.parent.mkdir(parents=True)
    lexicon.write_text("{}\n", encoding="utf-8")

    data_tier.provision_host_files(primary, checkout)

    copy = checkout / "data" / "ua-gec"
    assert (copy / "data" / "train" / "doc.txt").read_text(encoding="utf-8") == "content\n"
    assert (copy / "python" / "pkg" / ".gitkeep").is_file()
    assert (checkout / "site" / "public" / "lexicon" / "a.json").is_file()
    assert not (copy / ".git").exists()
    assert not (copy / ".entire").exists()


def test_stale_worktrees_pruned_only_without_active_scopes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent = tmp_path / ".worktrees" / "data-tier"
    old = parent / ("run-" + "a" * 32)
    recent = parent / ("run-" + "b" * 32)
    unrelated = parent / "run-unrelated"
    for path in (old, recent, unrelated):
        path.mkdir(parents=True)
    os.utime(old, (0, 0))
    removed = []
    monkeypatch.setattr(data_tier, "remove_test_worktree", lambda primary, checkout: removed.append(checkout))
    monkeypatch.setattr(data_tier, "command", lambda *args, **kwargs: SimpleNamespace(stdout="active.scope"))
    with pytest.raises(data_tier.DataTierError, match="still active"):
        data_tier.prune_stale_worktrees(tmp_path)
    assert removed == []
    monkeypatch.setattr(data_tier, "command", lambda *args, **kwargs: SimpleNamespace(stdout=""))
    data_tier.prune_stale_worktrees(tmp_path)
    assert removed == [old]


def test_scope_stop_handles_collected_and_loaded_units(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    state = "not-found"

    def command(argv: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(argv)
        return SimpleNamespace(stdout=f"LoadState={state}\n", returncode=1 if state == "not-found" else 0, stderr="")

    monkeypatch.setattr(data_tier, "command", command)
    monkeypatch.setattr(data_tier.subprocess, "run", command)
    data_tier.stop_scope("lu-data-tier-test.scope")
    assert len(calls) == 1
    state = "loaded"
    data_tier.stop_scope("lu-data-tier-test.scope")
    assert calls[-1] == ["systemctl", "--user", "stop", "lu-data-tier-test.scope"]


@pytest.mark.parametrize("interrupted", [False, True])
def test_process_group_stops_descendants_on_timeout_or_interruption(
    monkeypatch: pytest.MonkeyPatch, interrupted: bool
) -> None:
    waits = []
    signals = []

    class Process:
        pid = 123

        def wait(self, *, timeout: int) -> int:
            waits.append(timeout)
            if len(waits) == 1 and interrupted:
                raise data_tier.DataTierError("run interrupted")
            if len(waits) < 3:
                raise subprocess.TimeoutExpired("child", timeout)
            return 0

    monkeypatch.setattr(data_tier.subprocess, "Popen", lambda *args, **kwargs: Process())
    monkeypatch.setattr(data_tier.os, "killpg", lambda pid, sig: signals.append(sig))
    with pytest.raises(data_tier.DataTierError, match="interrupted" if interrupted else "timed out"):
        data_tier.run_process_group([sys.executable, "-c", "pass"], timeout=2)
    assert signals == [data_tier.signal.SIGTERM, data_tier.signal.SIGKILL]
    assert waits == [2, 30, 10]


@pytest.mark.parametrize("only", [None, "tests/test_input.py"])
def test_snapshots_keep_logical_stores_outside_checkout(tmp_path, only):
    primary = tmp_path / "primary"
    (primary / "data").mkdir(parents=True)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    snapshots = tmp_path / "scratch"
    for name in data_tier.HOST_DATABASES:
        with sqlite3.connect(primary / "data" / name) as connection:
            connection.execute("CREATE TABLE witness (value TEXT)")
            connection.execute("INSERT INTO witness VALUES ('snapshot')")
    assert data_tier.snapshot_databases(primary, checkout, snapshots, only=only) == []
    for name in ("sources.db", "vesum.db"):
        assert not (checkout / "data" / name).exists()
        with sqlite3.connect((snapshots / name).as_uri() + "?mode=ro", uri=True) as connection:
            assert connection.execute("SELECT value FROM witness").fetchone() == ("snapshot",)
    assert (checkout / "data" / "atlas.db").exists() == (only is None)


def test_nightly_exports_snapshot_bindings_and_reaps_them(nightly, monkeypatch):
    seen = []

    def execute(argv, **kwargs):
        env = kwargs["env"]
        sources, vesum = (Path(env[key]) for key in ("LU_SOURCES_DB", "LU_VESUM_DB"))
        assert sources.parent == vesum.parent
        assert sources.parent.is_dir()
        assert not sources.is_relative_to(nightly.primary)
        assert not sources.is_relative_to(kwargs["cwd"])
        seen.append(sources.parent)
        return nightly.execute(argv, **kwargs)

    monkeypatch.setenv("LU_SOURCES_DB", "inherited-live-store")
    monkeypatch.setenv("LU_VESUM_DB", "inherited-live-store")
    monkeypatch.setattr(data_tier, "run_process_group", execute)
    assert data_tier.run(SimpleNamespace(only=None, no_report=True)) == 0
    assert len(seen) == 1
    assert not seen[0].exists()


def test_nightly_retains_readable_snapshots_when_scope_stop_fails(nightly, monkeypatch, tmp_path):
    snapshots = []
    external_sentinel = tmp_path / "outside-snapshot.txt"
    external_sentinel.write_text("keep", encoding="utf-8")

    def snapshot(primary, checkout, snapshots_dir, *, only):
        snapshots.append(snapshots_dir)
        # Generic synthetic bytes witness; real store filenames and bindings
        # are covered by test_nightly_exports_snapshot_bindings_and_reaps_them.
        path = snapshots_dir / "retention-witness.db"
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE witness (value TEXT)")
            connection.execute("INSERT INTO witness VALUES ('retained')")
        return []

    def refuse_stop(unit):
        nightly.events.append("stop")
        raise data_tier.DataTierError("scope remains active")

    monkeypatch.setattr(data_tier, "snapshot_databases", snapshot)
    monkeypatch.setattr(data_tier, "stop_scope", refuse_stop)
    assert data_tier.run(SimpleNamespace(only=None, no_report=True)) == 1
    gc.collect()

    assert len(snapshots) == 1
    assert snapshots[0].is_dir()
    witness_uri = (snapshots[0] / "retention-witness.db").as_uri() + "?mode=ro"
    with sqlite3.connect(witness_uri, uri=True) as connection:
        assert connection.execute("SELECT value FROM witness").fetchone() == ("retained",)
    assert nightly.events == ["stop"]
    assert external_sentinel.read_text(encoding="utf-8") == "keep"
    summary = json.loads(next((nightly.primary / "batch_state" / "data-tier").glob("*.summary.json")).read_text())
    assert any(error.startswith("scope cleanup failed:") for error in summary["runner_errors"])


def test_nightly_removes_snapshots_before_child_launch_failure(nightly, monkeypatch, tmp_path):
    snapshots = []
    external_sentinel = tmp_path / "outside-snapshot.txt"
    external_sentinel.write_text("keep", encoding="utf-8")

    def snapshot(primary, checkout, snapshots_dir, *, only):
        snapshots.append(snapshots_dir)
        return []

    def fail_provision(*args):
        raise data_tier.DataTierError("provision failed")

    monkeypatch.setattr(data_tier, "snapshot_databases", snapshot)
    monkeypatch.setattr(data_tier, "provision_host_files", fail_provision)
    assert data_tier.run(SimpleNamespace(only=None, no_report=True)) == 1

    assert len(snapshots) == 1
    assert not snapshots[0].exists()
    assert nightly.events == ["remove"]
    assert external_sentinel.read_text(encoding="utf-8") == "keep"


def test_nightly_reports_snapshot_cleanup_failure(nightly, monkeypatch):
    snapshots = []
    monkeypatch.setattr(data_tier, "snapshot_databases", lambda _p, _c, root, **_kw: snapshots.append(root) or [])

    def fail_cleanup(path):
        raise OSError("snapshot removal denied")

    monkeypatch.setattr(data_tier.shutil, "rmtree", fail_cleanup)
    assert data_tier.run(SimpleNamespace(only=None, no_report=True)) == 1

    assert len(snapshots) == 1 and snapshots[0].is_dir()
    summary = json.loads(next((nightly.primary / "batch_state" / "data-tier").glob("*.summary.json")).read_text())
    assert "snapshot cleanup failed: snapshot removal denied" in summary["runner_errors"]


@pytest.mark.parametrize("available", [True, False])
def test_data_tier_child_executes_in_real_linked_worktree(tmp_path, available):
    """Exercise backup -> overrides -> resolver -> required child with real Git."""
    primary = tmp_path / "primary"
    primary.mkdir()

    def git(*args):
        subprocess.run(["git", *args], cwd=primary, check=True, capture_output=True, text=True, timeout=30)

    git("init", "-q")
    (primary / "sentinel").write_text("synthetic repository\n", encoding="utf-8")
    git("add", "sentinel")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
    checkout = tmp_path / "linked"
    git("worktree", "add", "--detach", str(checkout), "HEAD")
    assert (checkout / ".git").is_file()
    (checkout / "scripts").mkdir()
    (checkout / "data").mkdir()
    (primary / "data").mkdir()
    if available:
        for name in ("sources.db", "vesum.db"):
            with sqlite3.connect(primary / "data" / name) as connection:
                connection.execute("CREATE TABLE witness (value TEXT)")
                connection.execute("INSERT INTO witness VALUES ('snapshot')")
    snapshots = tmp_path / "scratch"
    missing = data_tier.snapshot_databases(primary, checkout, snapshots, only="tests/test_input.py")
    assert missing == ([] if available else ["sources.db", "vesum.db"])
    root = Path(data_tier.__file__).resolve().parents[2]
    (checkout / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (checkout / "conftest.py").write_text(
        f"import sys\nsys.path.insert(0, {str(root)!r})\n"
        "pytest_plugins = ['tests.data_store_fixtures']\n", encoding="utf-8",
    )
    tests = checkout / "tests"
    tests.mkdir()
    (tests / "test_input.py").write_text(
        "import sqlite3\nimport pytest\nfrom pathlib import Path\n"
        "@pytest.mark.parametrize('store', ['sources', 'vesum'])\n"
        "def test_snapshot(store, data_store_factory):\n"
        "    assert Path('.git').is_file()\n"
        "    path = data_store_factory(store, required_sqlite_tables=('witness',))\n"
        "    assert not path.is_relative_to(Path.cwd())\n"
        "    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as conn:\n"
        "        assert conn.execute('SELECT value FROM witness').fetchone() == ('snapshot',)\n",
        encoding="utf-8",
    )
    junit = tmp_path / "result.xml"
    code = (
        f"import sys\nsys.path.insert(0, {str(root)!r})\n"
        "from scripts.ci import data_tier\nfrom types import SimpleNamespace\n"
        "data_tier.load_selection = lambda: {'files': ['tests/test_input.py'], "
        "'nodeids': ['tests/test_input.py'], 'bulk_nodeids': []}\n"
        f"raise SystemExit(data_tier.pytest_child(SimpleNamespace(junit={str(junit)!r}, "
        f"collected={str(tmp_path / 'collected.json')!r}, only=None, bulk_reason=None)))\n"
    )
    env = {**os.environ, "LU_SOURCES_DB": str(snapshots / "sources.db"),
           "LU_VESUM_DB": str(snapshots / "vesum.db")}
    env.pop("GITHUB_STEP_SUMMARY", None)
    result = subprocess.run([sys.executable, "-c", code], cwd=checkout, env=env,
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == (0 if available else 1), result.stdout + result.stderr
    summary = data_tier.junit_summary(junit)
    assert summary["ran"] == 2
    assert summary["skipped"] == 0
    assert summary["passed"] == (2 if available else 0)
    assert summary["failed"] == (0 if available else 2)
    if not available:
        assert "reason=store_missing" in result.stdout
        assert "worktree_local_store" not in result.stdout


def test_nightly_rejects_scratch_inside_a_checkout(nightly, monkeypatch):
    (nightly.primary / ".git").mkdir()
    scratch = nightly.primary / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(data_tier.tempfile, "gettempdir", lambda: str(scratch))
    assert data_tier.run(SimpleNamespace(only=None, no_report=False)) == 1
    assert nightly.reports[-1]["runner_errors"] == ["runner scratch root must be outside any Git checkout"]
    assert nightly.events == ["remove"]


def test_malformed_pool_memory_high_skips_with_a_stderr_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    gib = 1024**3
    pool = _fake_slice(tmp_path / "lu.slice", current=25 * gib, file_cache=0, high="28G")
    (pool / "memory.max").write_text(f"{29 * gib}\n", encoding="ascii")
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    _slice_show(monkeypatch, current=gib, maximum=17 * gib)

    data_tier.require_memory()

    err = capsys.readouterr().err
    assert "lu.slice pool check skipped (lu.slice memory.high is neither a number nor 'max')" in err


def test_uncapped_pool_is_not_silent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pool = _fake_slice(tmp_path / "lu.slice", current=30 * 1024**3, file_cache=0)
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    _slice_show(monkeypatch, current=1024**3, maximum=20 * 1024**3)

    data_tier.require_memory()

    assert "lu.slice has no memory.high or memory.max limit" in capsys.readouterr().err
