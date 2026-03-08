"""Pipeline package — decomposed from pipeline_v5.py."""

from pipeline.state import (
    _state_file,
    load_state,
    save_state,
    is_complete,
    mark_complete,
    mark_failed,
    _fresh_state,
    _migrate_v4_to_v5,
)
from pipeline.parsing import (
    _extract_delimiter,
    _extract_delimiter_tolerant,
    _extract_audit_failures,
    _extract_gate_blockers,
    _extract_vesum_failures,
    _extract_h2_sections,
    _extract_fix_plan,
    _format_deterministic_issues,
    _format_filler_phrases,
    _format_vesum_verification,
    _inject_metrics_into_prompt,
    _inject_file_contents,
    _compute_metrics_direct,
    _scan_llm_filler,
    _parse_d1_review,
    _parse_factual_review,
    _build_d3_context,
    _quick_review_quality_gate,
    _get_track_calibration,
    _get_russicism_table,
)
from pipeline.fixes import (
    _module_file_paths,
    _snapshot_module_files,
    _count_diff_lines,
    _log_d1_edits,
    _apply_module_fixes,
    _apply_fixes_with_rollback,
    _clean_fix_text,
    _apply_find_replace_fixes,
)

__all__ = [
    # state
    "_state_file", "load_state", "save_state", "is_complete",
    "mark_complete", "mark_failed", "_fresh_state", "_migrate_v4_to_v5",
    # parsing
    "_extract_delimiter", "_extract_delimiter_tolerant",
    "_extract_audit_failures", "_extract_gate_blockers",
    "_extract_vesum_failures", "_extract_h2_sections", "_extract_fix_plan",
    "_format_deterministic_issues", "_format_filler_phrases",
    "_format_vesum_verification", "_inject_metrics_into_prompt",
    "_inject_file_contents", "_compute_metrics_direct", "_scan_llm_filler",
    "_parse_d1_review", "_parse_factual_review", "_build_d3_context",
    "_quick_review_quality_gate", "_get_track_calibration", "_get_russicism_table",
    # fixes
    "_module_file_paths", "_snapshot_module_files", "_count_diff_lines",
    "_log_d1_edits", "_apply_module_fixes", "_apply_fixes_with_rollback",
    "_clean_fix_text", "_apply_find_replace_fixes",
]
