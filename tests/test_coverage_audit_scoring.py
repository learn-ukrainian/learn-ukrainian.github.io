"""Tests targeting uncovered lines in audit, scoring, and pipeline modules.

Covers:
1. scripts/audit/report.py — report generation, terminal/markdown formatting
2. scripts/scoring/aggregator.py — criterion scorer functions + dispatch table
3. scripts/audit/checks/activity_validation.py — activity type validation
4. scripts/audit/checks/vocabulary.py — vocab gate checks
5. scripts/pipeline/screen.py — content screening (deterministic)
6. scripts/audit/phases_gates.py — gate evaluation phase (selected helpers)
7. scripts/audit/checks/content_quality.py — content quality scoring
8. scripts/manifest_utils.py — curriculum manifest utilities
9. scripts/assess_research_helpers.py — research assessment rendering
10. scripts/lexical_sandbox.py — VESUM word bank
"""

import sys
from pathlib import Path

# Add scripts/ to path
SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


# ============================================================================
# 1. audit/report.py
# ============================================================================

class TestReportHeader:
    def test_header_without_module_num(self):
        from audit.report import _report_header
        lines = _report_header("/path/test.md", "A1", None, "draft", "communicative", 1200, False, None)
        assert any("Audit Report: test.md" in l for l in lines)
        assert any("PASS" in l for l in lines)

    def test_header_with_module_num(self):
        from audit.report import _report_header
        lines = _report_header("/path/test.md", "B1", 5, "draft", "communicative", 4000, True, None)
        assert any("M05" in l for l in lines)
        assert any("FAIL" in l for l in lines)

    def test_header_with_naturalness_dict(self):
        from audit.report import _report_header
        nat = {"score": 8, "status": "PASS"}
        lines = _report_header("/x.md", "A1", None, "d", "c", 1200, False, nat)
        assert any("8/10" in l for l in lines)

    def test_header_with_naturalness_int(self):
        from audit.report import _report_header
        lines = _report_header("/x.md", "A1", None, "d", "c", 1200, False, 9)
        assert any("9/10" in l for l in lines)

    def test_header_with_naturalness_low_int(self):
        from audit.report import _report_header
        lines = _report_header("/x.md", "A1", None, "d", "c", 1200, False, 5)
        assert any("FAIL" in l for l in lines)

    def test_header_with_naturalness_unknown_type(self):
        from audit.report import _report_header
        lines = _report_header("/x.md", "A1", None, "d", "c", 1200, False, "unknown")
        assert any("PENDING" in l for l in lines)


class TestReportConfigSection:
    def test_basic_config(self):
        from audit.report import _report_config_section
        config = {
            "min_activities": 3,
            "max_activities": 8,
            "min_items_per_activity": 4,
            "min_types_unique": 2,
            "priority_types": {"quiz", "fill-in"},
            "required_types": {"quiz"},
            "min_engagement": 3,
            "min_immersion": 10,
            "max_immersion": 40,
            "min_vocab": 25,
            "transliteration_allowed": False,
        }
        lines = _report_config_section(config, "A1", 1200, "grammar")
        text = "\n".join(lines)
        assert "A1-grammar" in text
        assert "Not allowed" in text
        assert "25" in text

    def test_config_no_focus(self):
        from audit.report import _report_config_section
        config = {"min_activities": 3, "min_engagement": 3, "min_immersion": 0, "max_immersion": 100, "min_vocab": 25}
        lines = _report_config_section(config, "B1", 4000, None)
        text = "\n".join(lines)
        assert "B1" in text
        assert "Allowed" in text  # default transliteration_allowed=True


class TestReportActivityBreakdown:
    def test_basic_breakdown(self):
        from audit.report import _report_activity_breakdown
        activities = [
            {"type": "quiz", "title": "Test Quiz", "items": 5, "target": 4, "status": "OK"},
            {"type": "fill-in", "title": "Test Fill", "items": 2, "target": 4, "status": "FAIL"},
        ]
        config = {"min_activities": 2, "max_activities": 6, "min_types_unique": 2, "priority_types": {"quiz"}, "required_types": {"quiz"}}
        unique_types = {"quiz", "fill-in"}
        lines = _report_activity_breakdown(activities, config, unique_types)
        text = "\n".join(lines)
        assert "Test Quiz" in text
        assert "quiz" in text.lower()
        assert "Priority" in text or "priority" in text.lower()

    def test_breakdown_no_config(self):
        from audit.report import _report_activity_breakdown
        activities = [{"type": "quiz", "title": "Q", "items": 3, "target": 3, "status": "OK"}]
        lines = _report_activity_breakdown(activities, None, None)
        assert any("Total activities" in l for l in lines)


class TestReportRichnessSection:
    def test_richness_with_data(self):
        from audit.report import _report_richness_section
        data = {
            "score": 85,
            "threshold": 95,
            "module_type": "grammar",
            "raw": {"engagement": 5, "dialogue": 3.5},
            "normalized": {"engagement": 0.8, "dialogue": 0.7},
            "targets": {"engagement": 6, "dialogue": 5},
            "weights": {"engagement": 0.3, "dialogue": 0.2},
        }
        lines = _report_richness_section(data, ["NO_ENGAGEMENT"])
        text = "\n".join(lines)
        assert "85%" in text
        assert "NO_ENGAGEMENT" in text
        assert "Dryness Flags" in text

    def test_richness_no_flags(self):
        from audit.report import _report_richness_section
        data = {"score": 100, "threshold": 95, "module_type": "vocab"}
        lines = _report_richness_section(data, None)
        text = "\n".join(lines)
        assert "100%" in text
        assert "Dryness" not in text


class TestGenerateReport:
    def test_full_report(self):
        from audit.gates import GateResult
        from audit.report import generate_report

        results = {
            "words": GateResult("PASS", "OK", "1200/1200"),
            "activities": GateResult("PASS", "OK", "5/3"),
        }
        report = generate_report(
            file_path="/path/test.md",
            phase="draft",
            level_code="A1",
            pedagogy="communicative",
            target=1200,
            has_critical_failure=False,
            results=results,
            table_rows=["| Section 1 | OK | 500 | - |"],
            lint_errors=["Error 1"],
            pedagogical_violations=[{"type": "PED", "issue": "Issue 1", "fix": "Fix 1"}],
            recommendation="UPDATE",
            reasons=["Word count low"],
            severity=40,
            template_violations=[{"type": "TMPL", "severity": "CRITICAL", "issue": "Missing section", "fix": "Add it"}],
            low_density_activities=[{"title": "Act1", "type": "quiz", "items": 2, "target": 4}],
        )
        assert "LINT ERRORS" in report
        assert "PEDAGOGICAL VIOLATIONS" in report
        assert "TEMPLATE COMPLIANCE" in report
        assert "UPDATE" in report
        assert "Low Density" in report

    def test_report_pass_no_extras(self):
        from audit.report import generate_report
        results = {"words": {"icon": "OK", "msg": "1200/1200"}}
        report = generate_report(
            file_path="/path/test.md", phase="draft", level_code="A1",
            pedagogy="c", target=1200, has_critical_failure=False,
            results=results, table_rows=[], lint_errors=[], pedagogical_violations=[],
            recommendation="PASS", reasons=[], severity=0,
        )
        assert "Section Audit" in report
        assert "LINT" not in report


class TestFormatMdxSection:
    def test_errors_and_warnings(self):
        from audit.report import _format_mdx_section
        result = _format_mdx_section(["err1"], ["warn1"])
        assert "err1" in result
        assert "warn1" in result

    def test_no_issues(self):
        from audit.report import _format_mdx_section
        result = _format_mdx_section([], [])
        assert "No issues found" in result


class TestFormatHtmlSection:
    def test_with_errors(self):
        from audit.report import _format_html_section
        result = _format_html_section(["err1"], [], 3)
        assert "err1" in result

    def test_clean(self):
        from audit.report import _format_html_section
        result = _format_html_section([], [], 5)
        assert "5 interactive elements" in result


class TestPrintFunctions:
    def test_print_gates(self, capsys):
        from audit.gates import GateResult
        from audit.report import print_gates
        results = {
            "words": GateResult("PASS", "OK", "1200/1200"),
            "immersion": GateResult("PASS", "OK", "30%"),
            "richness": {"icon": "OK", "msg": "95%"},
        }
        print_gates(results, "A1")
        captured = capsys.readouterr()
        assert "STRICT GATES" in captured.out
        assert "Immersion" in captured.out
        assert "Richness" in captured.out

    def test_print_lint_errors(self, capsys):
        from audit.report import print_lint_errors
        print_lint_errors(["err1", "err2"])
        captured = capsys.readouterr()
        assert "err1" in captured.out

    def test_print_lint_errors_empty(self, capsys):
        from audit.report import print_lint_errors
        print_lint_errors([])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_pedagogical_violations(self, capsys):
        from audit.report import print_pedagogical_violations
        violations = [{"type": "SCOPE", "issue": "Out of scope", "fix": "Remove it"}]
        print_pedagogical_violations(violations)
        captured = capsys.readouterr()
        assert "SCOPE" in captured.out

    def test_print_template_violations(self, capsys):
        from audit.report import print_template_violations
        violations = [{"severity": "CRITICAL", "type": "MISS", "issue": "Missing", "fix": "Add"}]
        print_template_violations(violations)
        captured = capsys.readouterr()
        assert "MISS" in captured.out

    def test_print_template_violations_warning(self, capsys):
        from audit.report import print_template_violations
        violations = [{"severity": "WARNING", "type": "W", "issue": "Warn", "fix": "Fix"}]
        print_template_violations(violations)
        captured = capsys.readouterr()
        assert "W" in captured.out

    def test_print_recommendation_rewrite(self, capsys):
        from audit.report import print_recommendation
        print_recommendation("REWRITE", ["Bad content"], 85)
        captured = capsys.readouterr()
        assert "REWRITE FROM SCRATCH" in captured.out

    def test_print_recommendation_update(self, capsys):
        from audit.report import print_recommendation
        print_recommendation("UPDATE", ["Minor issues"], 30)
        captured = capsys.readouterr()
        assert "UPDATE" in captured.out

    def test_print_recommendation_pass(self, capsys):
        from audit.report import print_recommendation
        print_recommendation("PASS", [], 0)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_immersion_fix_hints_low(self, capsys):
        from audit.report import print_immersion_fix_hints
        print_immersion_fix_hints(5.0, 15, 40, "B1")
        captured = capsys.readouterr()
        assert "TOO LOW" in captured.out
        assert "grammar rules in Ukrainian" in captured.out

    def test_print_immersion_fix_hints_high_a1(self, capsys):
        from audit.report import print_immersion_fix_hints
        print_immersion_fix_hints(50.0, 5, 25, "A1")
        captured = capsys.readouterr()
        assert "TOO HIGH" in captured.out
        assert "Cyrillic" in captured.out

    def test_print_immersion_fix_hints_high_a2(self, capsys):
        from audit.report import print_immersion_fix_hints
        print_immersion_fix_hints(50.0, 10, 35, "A2")
        captured = capsys.readouterr()
        assert "TOO HIGH" in captured.out

    def test_print_immersion_fix_hints_high_grammar(self, capsys):
        from audit.report import print_immersion_fix_hints
        print_immersion_fix_hints(80.0, 30, 60, "B2", "grammar")
        captured = capsys.readouterr()
        assert "grammar" in captured.out.lower()

    def test_print_immersion_fix_hints_high_other(self, capsys):
        from audit.report import print_immersion_fix_hints
        print_immersion_fix_hints(80.0, 30, 60, "B2", "vocab")
        captured = capsys.readouterr()
        assert "TOO HIGH" in captured.out

    def test_print_low_density_activities(self, capsys):
        from audit.report import print_low_density_activities
        acts = [{"title": "Quiz 1", "type": "quiz", "items": 2, "target": 5}]
        print_low_density_activities(acts)
        captured = capsys.readouterr()
        assert "Quiz 1" in captured.out
        assert "3 more" in captured.out

    def test_print_low_density_activities_empty(self, capsys):
        from audit.report import print_low_density_activities
        print_low_density_activities([])
        captured = capsys.readouterr()
        assert captured.out == ""


# ============================================================================
# 2. scoring/aggregator.py
# ============================================================================

class TestScoringAggregator:
    def _make_tm(self, **kwargs):
        from scoring.aggregator import TrackMetrics
        defaults = dict(track_id="hist", total_modules=10, modules_found=5)
        defaults.update(kwargs)
        return TrackMetrics(**defaults)

    def test_score_audit_pass_rate(self):
        from scoring.aggregator import _score_audit_pass_rate
        tm = self._make_tm(passing_modules=5)
        assert _score_audit_pass_rate(tm, 10) == 5.0
        assert _score_audit_pass_rate(tm, 0) == 0.0

    def test_score_activity_coverage(self):
        from scoring.aggregator import _score_activity_coverage
        tm = self._make_tm(modules_with_activities=10)
        assert _score_activity_coverage(tm, 10) == 10.0
        assert _score_activity_coverage(tm, 0) == 0.0

    def test_score_vocabulary_coverage(self):
        from scoring.aggregator import _score_vocabulary_coverage
        tm = self._make_tm(modules_with_vocabulary=5)
        assert _score_vocabulary_coverage(tm, 10) == 5.0

    def test_score_internal_consistency(self):
        from scoring.aggregator import _score_internal_consistency
        assert _score_internal_consistency(self._make_tm(avg_cross_references=1.5)) == 10.0
        assert _score_internal_consistency(self._make_tm(avg_cross_references=0.6)) == 7.0
        assert _score_internal_consistency(self._make_tm(avg_cross_references=0.3)) == 5.0
        assert _score_internal_consistency(self._make_tm(avg_cross_references=0.1)) == 3.0
        assert _score_internal_consistency(self._make_tm(avg_cross_references=0.0)) == 0.0

    def test_score_primary_source_integration(self):
        from scoring.aggregator import _score_primary_source_integration
        assert _score_primary_source_integration(self._make_tm(avg_quote_callouts=3.0)) == 10.0
        assert _score_primary_source_integration(self._make_tm(avg_quote_callouts=2.0)) == 8.0
        assert _score_primary_source_integration(self._make_tm(avg_quote_callouts=1.0)) == 6.0
        assert _score_primary_source_integration(self._make_tm(avg_quote_callouts=0.5)) == 4.0
        assert _score_primary_source_integration(self._make_tm(avg_quote_callouts=0.1)) == 2.0
        assert _score_primary_source_integration(self._make_tm(avg_quote_callouts=0.0)) == 0.0

    def test_score_historical_accuracy(self):
        from scoring.aggregator import _score_historical_accuracy
        assert _score_historical_accuracy(self._make_tm(avg_naturalness_score=9.5)) == 10.0
        assert _score_historical_accuracy(self._make_tm(avg_naturalness_score=8.0)) == 9.0
        assert _score_historical_accuracy(self._make_tm(avg_naturalness_score=7.0)) == 8.0
        assert _score_historical_accuracy(self._make_tm(avg_naturalness_score=6.0)) == 7.0
        assert _score_historical_accuracy(self._make_tm(avg_naturalness_score=5.0)) == 6.0
        assert _score_historical_accuracy(self._make_tm(avg_naturalness_score=3.0)) == 5.0

    def test_score_decolonization_perspective(self):
        from scoring.aggregator import _score_decolonization_perspective
        # Full score
        tm = self._make_tm(avg_myth_buster_callouts=2.0, agency_marker_ratio=0.20, total_toponym_violations=0)
        assert _score_decolonization_perspective(tm) == 10.0
        # Low myth
        tm = self._make_tm(avg_myth_buster_callouts=1.0, agency_marker_ratio=0.15, total_toponym_violations=3)
        score = _score_decolonization_perspective(tm)
        assert 5.0 <= score <= 8.0
        # Zero everything
        tm = self._make_tm(avg_myth_buster_callouts=0, agency_marker_ratio=0, total_toponym_violations=10)
        assert _score_decolonization_perspective(tm) == 0.0
        # Partial values
        tm = self._make_tm(avg_myth_buster_callouts=0.5, agency_marker_ratio=0.10, total_toponym_violations=5)
        score = _score_decolonization_perspective(tm)
        assert score > 0
        # Nonzero small myth, small agency
        tm = self._make_tm(avg_myth_buster_callouts=0.1, agency_marker_ratio=0.01, total_toponym_violations=0)
        score = _score_decolonization_perspective(tm)
        assert score >= 2.0  # 1 myth + 1 agency + 2 toponyms

    def test_score_era_vocabulary(self):
        from scoring.aggregator import _score_era_vocabulary
        assert _score_era_vocabulary(self._make_tm(modules_with_vocabulary=0), 10) == 0.0
        assert _score_era_vocabulary(self._make_tm(modules_with_vocabulary=10), 10) == 10.0

    def test_score_critical_analysis_skills(self):
        from scoring.aggregator import _score_critical_analysis_skills
        assert _score_critical_analysis_skills(self._make_tm(total_critical_analysis_activities=0), 10) == 5.0
        assert _score_critical_analysis_skills(self._make_tm(total_critical_analysis_activities=5), 10) > 5.0

    def test_score_source_reliability(self):
        from scoring.aggregator import _score_source_reliability
        assert _score_source_reliability(self._make_tm(avg_quote_callouts=2.0)) == 10.0
        assert _score_source_reliability(self._make_tm(avg_quote_callouts=1.0)) == 7.0
        assert _score_source_reliability(self._make_tm(avg_quote_callouts=0.5)) == 4.0
        assert _score_source_reliability(self._make_tm(avg_quote_callouts=0.0)) == 0.0

    def test_score_cultural_historical_context(self):
        from scoring.aggregator import _score_cultural_historical_context
        assert _score_cultural_historical_context(self._make_tm(total_context_callouts=20), 10) == 10.0
        assert _score_cultural_historical_context(self._make_tm(total_context_callouts=10), 10) == 8.0
        assert _score_cultural_historical_context(self._make_tm(total_context_callouts=5), 10) == 6.0
        assert _score_cultural_historical_context(self._make_tm(total_context_callouts=1), 10) == 4.0
        assert _score_cultural_historical_context(self._make_tm(total_context_callouts=0), 10) == 3.0

    def test_score_significance_assessment(self):
        from scoring.aggregator import _score_significance_assessment
        assert _score_significance_assessment(self._make_tm(total_legacy_sections=8), 10) == 10.0
        assert _score_significance_assessment(self._make_tm(total_legacy_sections=5), 10) == 8.0
        assert _score_significance_assessment(self._make_tm(total_legacy_sections=3), 10) == 6.0
        assert _score_significance_assessment(self._make_tm(total_legacy_sections=1), 10) == 4.0
        assert _score_significance_assessment(self._make_tm(total_legacy_sections=0), 10) == 0.0

    def test_score_literary_depth(self):
        from scoring.aggregator import _score_literary_depth
        tm = self._make_tm(total_stylistic_devices=50, total_analysis_sections=30)
        assert _score_literary_depth(tm, 10) == 10.0
        tm = self._make_tm(total_stylistic_devices=30, total_analysis_sections=20)
        assert _score_literary_depth(tm, 10) >= 8.0
        tm = self._make_tm(total_stylistic_devices=10, total_analysis_sections=10)
        assert _score_literary_depth(tm, 10) >= 4.0
        tm = self._make_tm(total_stylistic_devices=5, total_analysis_sections=5)
        assert _score_literary_depth(tm, 10) > 0
        tm = self._make_tm(total_stylistic_devices=0, total_analysis_sections=0)
        assert _score_literary_depth(tm, 10) == 0.0

    def test_score_authentic_text_engagement(self):
        from scoring.aggregator import _score_authentic_text_engagement
        assert _score_authentic_text_engagement(self._make_tm(avg_citation_ratio=0.20)) == 10.0
        assert _score_authentic_text_engagement(self._make_tm(avg_citation_ratio=0.15)) == 9.0
        assert _score_authentic_text_engagement(self._make_tm(avg_citation_ratio=0.10)) == 7.0
        assert _score_authentic_text_engagement(self._make_tm(avg_citation_ratio=0.05)) == 5.0
        assert _score_authentic_text_engagement(self._make_tm(avg_citation_ratio=0.01)) == 3.0
        assert _score_authentic_text_engagement(self._make_tm(avg_citation_ratio=0.0)) == 0.0

    def test_score_archaic_literary_vocab(self):
        from scoring.aggregator import _score_archaic_literary_vocab
        assert _score_archaic_literary_vocab(self._make_tm(modules_with_vocabulary=0)) == 5.0
        tm = self._make_tm(modules_with_vocabulary=5, total_archaic_vocab_items=10, total_vocab_items=100)
        assert _score_archaic_literary_vocab(tm) == 10.0

    def test_score_intertextual_links(self):
        from scoring.aggregator import _score_intertextual_links
        assert _score_intertextual_links(self._make_tm(avg_cross_references=1.0)) == 10.0
        assert _score_intertextual_links(self._make_tm(avg_cross_references=0.5)) == 7.0
        assert _score_intertextual_links(self._make_tm(avg_cross_references=0.1)) == 4.0
        assert _score_intertextual_links(self._make_tm(avg_cross_references=0.0)) == 0.0

    def test_score_skills_balance(self):
        from scoring.aggregator import _score_skills_balance
        tm = self._make_tm(total_activities=10, total_reading_activities=3, total_essay_activities=3, total_critical_analysis_activities=3)
        assert _score_skills_balance(tm) == 10.0
        tm = self._make_tm(total_activities=0)
        assert _score_skills_balance(tm) == 5.0
        # Only reading
        tm = self._make_tm(total_activities=5, total_reading_activities=5, total_essay_activities=0, total_critical_analysis_activities=0)
        assert _score_skills_balance(tm) == 6.5

    def test_score_cefr_alignment(self):
        from scoring.aggregator import _score_cefr_alignment
        assert _score_cefr_alignment(self._make_tm(avg_naturalness_score=9.0)) == 10.0
        assert _score_cefr_alignment(self._make_tm(avg_naturalness_score=7.0)) == 8.0
        assert _score_cefr_alignment(self._make_tm(avg_naturalness_score=4.0)) == 6.0

    def test_score_historiographical_methodology(self):
        from scoring.aggregator import _score_historiographical_methodology
        assert _score_historiographical_methodology(self._make_tm(total_analysis_sections=20), 10) == 10.0
        assert _score_historiographical_methodology(self._make_tm(total_analysis_sections=10), 10) == 7.0
        assert _score_historiographical_methodology(self._make_tm(total_analysis_sections=5), 10) == 4.0
        assert _score_historiographical_methodology(self._make_tm(total_analysis_sections=0), 10) == 2.0

    def test_score_source_criticism_skills(self):
        from scoring.aggregator import _score_source_criticism_skills
        assert _score_source_criticism_skills(self._make_tm(total_critical_analysis_activities=0), 10) == 4.0
        assert _score_source_criticism_skills(self._make_tm(total_critical_analysis_activities=5), 10) > 4.0

    def test_score_thematic_coherence(self):
        from scoring.aggregator import _score_thematic_coherence
        assert _score_thematic_coherence(self._make_tm(avg_cross_references=1.5)) == 10.0
        assert _score_thematic_coherence(self._make_tm(avg_cross_references=1.0)) == 8.0
        assert _score_thematic_coherence(self._make_tm(avg_cross_references=0.5)) == 6.0
        assert _score_thematic_coherence(self._make_tm(avg_cross_references=0.1)) == 4.0
        assert _score_thematic_coherence(self._make_tm(avg_cross_references=0.0)) == 2.0

    def test_calculate_criterion_score_static_defaults(self):
        from scoring.aggregator import calculate_criterion_score
        from scoring.config import get_track_config
        tm = self._make_tm()
        config = get_track_config("hist")
        assert calculate_criterion_score("checkpoint_structure", tm, config) == 8.0
        assert calculate_criterion_score("state_standard_compliance", tm, config) == 8.0
        assert calculate_criterion_score("chronological_coherence", tm, config) == 9.0

    def test_calculate_criterion_score_unknown(self):
        from scoring.aggregator import calculate_criterion_score
        from scoring.config import get_track_config
        tm = self._make_tm()
        config = get_track_config("hist")
        assert calculate_criterion_score("nonexistent_criterion", tm, config) == 5.0

    def test_calculate_criterion_score_zero_modules(self):
        from scoring.aggregator import calculate_criterion_score
        from scoring.config import get_track_config
        tm = self._make_tm(modules_found=0)
        config = get_track_config("hist")
        assert calculate_criterion_score("audit_pass_rate", tm, config) == 0.0


class TestAggregateTrackMetrics:
    def test_empty_metrics(self):
        from scoring.aggregator import aggregate_track_metrics
        tm = aggregate_track_metrics([], "hist")
        assert tm.modules_found == 0
        assert tm.total_word_count == 0

    def test_with_modules(self):
        from scoring.aggregator import aggregate_track_metrics
        from scoring.metrics import ModuleMetrics
        m1 = ModuleMetrics(module_slug="s1", level="hist", audit_status="pass",
                           md_exists=True, meta_exists=True, activities_exists=True,
                           vocabulary_exists=True, status_exists=True,
                           word_count=5000, quote_callouts=2, myth_buster_callouts=1,
                           history_bite_callouts=1, analysis_callouts=1, context_callouts=1,
                           resources_callouts=1, agency_markers=10, total_sentences=50,
                           cross_references=2, citation_ratio=0.15, stylistic_devices=3,
                           analysis_sections=2, legacy_sections=1, vocab_items=30,
                           era_vocab_items=5, archaic_vocab_items=3, activity_count=5,
                           activity_items=25, critical_analysis_activities=1,
                           reading_activities=2, essay_activities=1,
                           naturalness_score=8.5, validation_tier="llm-verified")
        m2 = ModuleMetrics(module_slug="s2", level="hist", audit_status="fail",
                           word_count=4000, naturalness_score=None,
                           validation_tier="gold-standard")
        m3 = ModuleMetrics(module_slug="s3", level="hist", audit_status="unknown",
                           validation_tier="automated")

        tm = aggregate_track_metrics([m1, m2, m3], "hist")
        assert tm.passing_modules == 1
        assert tm.failing_modules == 1
        assert tm.unknown_modules == 1
        assert tm.total_gold_standard == 1
        assert tm.total_llm_verified == 1
        assert tm.total_automated == 1
        assert tm.modules_with_md == 1
        assert tm.total_word_count == 9000
        assert tm.avg_word_count > 0
        assert len(tm.naturalness_scores) == 1
        assert tm.avg_naturalness_score == 8.5


# ============================================================================
# 3. audit/checks/activity_validation.py
# ============================================================================

class TestUnjumbleChecks:
    def test_check_unjumble_empty_jumbled(self):
        from audit.checks.activity_validation import check_unjumble_empty_jumbled
        activities = [
            {"type": "unjumble", "title": "Test", "items": [{"words": ["a", "b"]}, {}]},
        ]
        violations = check_unjumble_empty_jumbled(activities)
        assert len(violations) == 1
        assert violations[0]["type"] == "EMPTY_UNJUMBLE_CONTENT"

    def test_check_unjumble_with_scrambled(self):
        from audit.checks.activity_validation import check_unjumble_empty_jumbled
        activities = [{"type": "anagram", "title": "T", "items": [{"scrambled": "test"}]}]
        violations = check_unjumble_empty_jumbled(activities)
        assert len(violations) == 0

    def test_check_unjumble_runon_answer(self):
        from audit.checks.activity_validation import check_unjumble_runon_answer
        activities = [
            {"type": "unjumble", "title": "T", "items": [
                {"answer": "Привіт друже Це маленький подарунок"}
            ]},
        ]
        violations = check_unjumble_runon_answer(activities)
        assert len(violations) == 1
        assert violations[0]["type"] == "UNJUMBLE_RUNON_SENTENCE"

    def test_check_unjumble_runon_capital_after_period(self):
        from audit.checks.activity_validation import check_unjumble_runon_answer
        activities = [
            {"type": "unjumble", "title": "T", "items": [
                {"answer": "Привіт. Це подарунок"}
            ]},
        ]
        violations = check_unjumble_runon_answer(activities)
        assert len(violations) == 0

    def test_check_unjumble_runon_always_capital(self):
        from audit.checks.activity_validation import check_unjumble_runon_answer
        activities = [
            {"type": "unjumble", "title": "T", "items": [
                {"answer": "Це слово Я написав"}
            ]},
        ]
        violations = check_unjumble_runon_answer(activities)
        assert len(violations) == 0

    def test_check_unjumble_out_of_scope_dative(self):
        from audit.checks.activity_validation import check_unjumble_out_of_scope_dative
        activities = [
            {"type": "unjumble", "title": "T", "items": [
                {"words": ["моїй", "сестрі", "подобається"]}
            ]},
        ]
        violations = check_unjumble_out_of_scope_dative(activities)
        assert len(violations) == 1

    def test_check_unjumble_out_of_scope_dative_obj_attr(self):
        from audit.checks.activity_validation import check_unjumble_out_of_scope_dative
        # Test with object having .words attribute
        class Item:
            def __init__(self):
                self.words = ["твоєму", "другу"]
        activities = [{"type": "unjumble", "title": "T", "items": [Item()]}]
        violations = check_unjumble_out_of_scope_dative(activities)
        assert len(violations) == 1


class TestMdxUnjumbleRendering:
    def test_check_mdx_unjumble_rendering(self):
        from audit.checks.activity_validation import check_mdx_unjumble_rendering
        mdx = '<Unjumble key="1" title="Test" items={JSON.parse(`[{"jumbled":""}]`)}'
        violations = check_mdx_unjumble_rendering(mdx)
        assert len(violations) == 1

    def test_check_mdx_unjumble_no_issue(self):
        from audit.checks.activity_validation import check_mdx_unjumble_rendering
        mdx = '<Unjumble key="1" title="Test" items={JSON.parse(`[{"jumbled":"test words"}]`)}'
        violations = check_mdx_unjumble_rendering(mdx)
        assert len(violations) == 0


class TestMarkTheWords:
    def test_check_morpheme_patterns(self):
        from audit.checks.activity_validation import check_morpheme_patterns
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "Слово *при*йшов у текст", "answers": None},
        ]
        violations = check_morpheme_patterns(activities)
        assert len(violations) == 0

    def test_check_mark_the_words_format_mixed(self):
        from audit.checks.activity_validation import check_mark_the_words_format
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "[слово](noun) and *при*йшов together"},
        ]
        violations = check_mark_the_words_format(activities)
        assert len(violations) == 1
        assert violations[0]["type"] == "MIXED_MARK_FORMAT"

    def test_check_mark_the_words_answers_in_text(self):
        from audit.checks.activity_validation import check_mark_the_words_answers_in_text
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "This is a test sentence", "answers": ["missing_word"]},
        ]
        violations = check_mark_the_words_answers_in_text(activities)
        assert len(violations) == 1

    def test_check_mark_the_words_answers_found(self):
        from audit.checks.activity_validation import check_mark_the_words_answers_in_text
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "This is a test sentence", "answers": ["test"]},
        ]
        violations = check_mark_the_words_answers_in_text(activities)
        assert len(violations) == 0


class TestMorphemePedagogy:
    def test_vague_instruction(self):
        from audit.checks.activity_validation import check_morpheme_pedagogy
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "Click on any morphemes in the text\n\n*при*йшов"},
        ]
        violations = check_morpheme_pedagogy(activities)
        assert any(v["type"] == "VAGUE_MORPHEME_INSTRUCTION" for v in violations)

    def test_too_many_morphemes(self):
        from audit.checks.activity_validation import check_morpheme_pedagogy
        # Generate 12 distinct Ukrainian morpheme markers
        words = ["при", "від", "пере", "над", "під", "роз", "без", "ви", "за", "до", "по", "об"]
        morphemes = " ".join(f"*{w}*йшов" for w in words)
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": f"Знайдіть префікси\n\n{morphemes}"},
        ]
        violations = check_morpheme_pedagogy(activities)
        assert any(v["type"] == "TOO_MANY_MORPHEMES" for v in violations)


class TestQuizValidation:
    def test_quiz_single_correct(self):
        from audit.checks.activity_validation import check_quiz_single_correct
        activities = [
            {"type": "quiz", "title": "Q", "items": [
                {"options": [{"correct": True}, {"correct": True}, {"correct": False}]}
            ]}
        ]
        violations = check_quiz_single_correct(activities)
        assert len(violations) == 1

    def test_quiz_single_correct_ok(self):
        from audit.checks.activity_validation import check_quiz_single_correct
        activities = [
            {"type": "quiz", "title": "Q", "items": [
                {"options": [{"correct": True}, {"correct": False}]}
            ]}
        ]
        violations = check_quiz_single_correct(activities)
        assert len(violations) == 0


class TestSelectMinCorrect:
    def test_mismatch(self):
        from audit.checks.activity_validation import check_select_min_correct
        activities = [
            {"type": "select", "title": "S", "items": [
                {"min_correct": 2, "options": [{"correct": True}, {"correct": True}, {"correct": True}]}
            ]}
        ]
        violations = check_select_min_correct(activities)
        assert len(violations) == 1

    def test_match(self):
        from audit.checks.activity_validation import check_select_min_correct
        activities = [
            {"type": "select", "title": "S", "items": [
                {"min_correct": 2, "options": [{"correct": True}, {"correct": True}, {"correct": False}]}
            ]}
        ]
        violations = check_select_min_correct(activities)
        assert len(violations) == 0


class TestFillInAnswerInOptions:
    def test_answer_missing(self):
        from audit.checks.activity_validation import check_fill_in_answer_in_options
        activities = [
            {"type": "fill-in", "title": "F", "items": [
                {"answer": "correct", "options": ["wrong1", "wrong2"]}
            ]}
        ]
        violations = check_fill_in_answer_in_options(activities)
        assert len(violations) == 1

    def test_answer_present(self):
        from audit.checks.activity_validation import check_fill_in_answer_in_options
        activities = [
            {"type": "fill-in", "title": "F", "items": [
                {"answer": "correct", "options": ["correct", "wrong"]}
            ]}
        ]
        violations = check_fill_in_answer_in_options(activities)
        assert len(violations) == 0


class TestTranslateSingleCorrect:
    def test_multiple_correct(self):
        from audit.checks.activity_validation import check_translate_single_correct
        activities = [
            {"type": "translate", "title": "T", "items": [
                {"options": [{"correct": True}, {"correct": True}]}
            ]}
        ]
        violations = check_translate_single_correct(activities)
        assert len(violations) == 1


class TestSeminarReadingPairing:
    def test_not_seminar_track(self):
        from audit.checks.activity_validation import check_seminar_reading_pairing
        violations = check_seminar_reading_pairing([], "A1")
        assert len(violations) == 0

    def test_missing_reading_id(self):
        from audit.checks.activity_validation import check_seminar_reading_pairing
        activities = [
            {"type": "reading", "title": "Read 1"},
            {"type": "essay-response", "title": "Essay", "source_reading": "reading-01"},
        ]
        violations = check_seminar_reading_pairing(activities, "lit")
        assert any(v["type"] == "READING_MISSING_ID" for v in violations)

    def test_invalid_source_reading(self):
        from audit.checks.activity_validation import check_seminar_reading_pairing
        activities = [
            {"type": "reading", "title": "Read 1", "id": "reading-01"},
            {"type": "critical-analysis", "title": "Analysis", "source_reading": "reading-99"},
        ]
        violations = check_seminar_reading_pairing(activities, "hist")
        assert any(v["type"] == "INVALID_SOURCE_READING" for v in violations)

    def test_orphan_reading(self):
        from audit.checks.activity_validation import check_seminar_reading_pairing
        activities = [
            {"type": "reading", "title": "Orphan", "id": "reading-02"},
        ]
        violations = check_seminar_reading_pairing(activities, "bio")
        assert any(v["type"] == "ORPHAN_READING" for v in violations)

    def test_missing_source_reading(self):
        from audit.checks.activity_validation import check_seminar_reading_pairing
        activities = [
            {"type": "essay-response", "title": "Essay"},
        ]
        violations = check_seminar_reading_pairing(activities, "lit")
        assert any(v["type"] == "MISSING_SOURCE_READING" for v in violations)


class TestEnglishHintsInActivities:
    def test_english_hints_detected(self):
        from audit.checks.activity_validation import check_english_hints_in_activities
        activities = [
            {"type": "cloze", "title": "C", "passage": "Він (big) будинок (small) кімната (old)"}
        ]
        violations = check_english_hints_in_activities(activities, "B1", 5)
        assert len(violations) == 1

    def test_english_hints_a1_lenient(self):
        from audit.checks.activity_validation import check_english_hints_in_activities
        activities = [
            {"type": "fill-in", "title": "F", "items": [
                {"sentence": "Це (example) слово (hint) тут"}
            ]}
        ]
        violations = check_english_hints_in_activities(activities, "A1", 1)
        assert len(violations) == 0  # scaffolding hints allowed at A1

    def test_english_hints_fill_in(self):
        from audit.checks.activity_validation import check_english_hints_in_activities
        activities = [
            {"type": "fill-in", "title": "F", "items": [
                {"sentence": "Він (quickly) біжить (slowly) ходить"}
            ]}
        ]
        violations = check_english_hints_in_activities(activities, "B2", 10)
        assert len(violations) == 1


class TestGetActivityAttr:
    def test_dict(self):
        from audit.checks.activity_validation import _get_activity_attr
        assert _get_activity_attr({"type": "quiz"}, "type") == "quiz"
        assert _get_activity_attr({"type": "quiz"}, "missing", "default") == "default"

    def test_object(self):
        from audit.checks.activity_validation import _get_activity_attr
        class Obj:
            type = "quiz"
        assert _get_activity_attr(Obj(), "type") == "quiz"
        assert _get_activity_attr(Obj(), "missing", "d") == "d"


# ============================================================================
# 4. audit/checks/vocabulary.py
# ============================================================================

class TestGenerateInflections:
    def test_a_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("книга")
        assert "книги" in forms
        assert "книгу" in forms
        assert "книга" in forms

    def test_ya_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("земля")
        assert "землі" in forms
        assert "землю" in forms

    def test_o_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("вікно")
        assert "вікна" in forms
        assert "вікном" in forms

    def test_e_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("море")
        assert "моря" in forms
        assert "морем" in forms

    def test_consonant_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("стіл")
        assert "стола" in forms  # i->o alternation
        assert "столи" in forms

    def test_adjective(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("новий")
        assert "нова" in forms
        assert "нове" in forms
        assert "нові" in forms

    def test_soft_sign_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("день")
        assert "день" in forms
        # soft-sign ending should not add consonant endings
        assert "деня" not in forms


class TestExtractVocabItems:
    def test_basic_table(self):
        from audit.checks.vocabulary import extract_vocab_items
        content = """## Vocabulary
| Слово | Переклад | Примітка |
|---|---|---|
| книга | book | basic |
| стіл | table | furniture |
"""
        items = extract_vocab_items(content)
        assert len(items) == 2
        assert items[0]["uk"] == "книга"

    def test_a1_format(self):
        from audit.checks.vocabulary import extract_vocab_items
        content = """## Vocabulary
| Word | English | POS | Gender | Note |
|---|---|---|---|---|
| книга | book | noun | f | basic |
"""
        items = extract_vocab_items(content)
        assert len(items) == 1


class TestCountVocabRows:
    def test_h2_section(self):
        from audit.checks.vocabulary import count_vocab_rows
        content = """## Vocabulary
| Слово | Переклад | Примітка |
|---|---|---|
| книга | book | basic |
| стіл | table | furniture |

## Next Section
"""
        assert count_vocab_rows(content) == 2

    def test_h1_section(self):
        from audit.checks.vocabulary import count_vocab_rows
        content = """# Словник

### Group A
| Слово | Переклад | Примітка |
|---|---|---|
| книга | book | basic |

### Group B
| Слово | Переклад | Примітка |
|---|---|---|
| стіл | table | furniture |
"""
        assert count_vocab_rows(content) == 2  # Minus 2 header rows


class TestCheckVocabViolations:
    def test_missing_vocab(self):
        from audit.checks.vocabulary import check_vocab_violations
        content = "Full content with книга and стіл"
        core_content = "книга книга стіл стіл новий новий"
        vocab_words = {"книга"}
        violations = check_vocab_violations(content, core_content, vocab_words)
        # "стіл" and "новий" used 2+ times but not in vocab
        assert len(violations) >= 1

    def test_no_violations(self):
        from audit.checks.vocabulary import check_vocab_violations
        violations = check_vocab_violations("", "", set())
        assert len(violations) == 0


class TestCheckMetalanguageScaffolding:
    def test_a1_metalanguage(self):
        from audit.checks.vocabulary import check_metalanguage_scaffolding
        content = "У цьому уроці іменник дуже важливий"
        vocab = set()
        violations = check_metalanguage_scaffolding(content, vocab, "A1", 1)
        assert len(violations) >= 1

    def test_b1_exempt(self):
        from audit.checks.vocabulary import check_metalanguage_scaffolding
        content = "У цьому уроці іменник дуже важливий"
        violations = check_metalanguage_scaffolding(content, set(), "B1", 1)
        assert len(violations) == 0

    def test_a1_with_vocab(self):
        from audit.checks.vocabulary import check_metalanguage_scaffolding
        content = "У цьому уроці іменник дуже важливий"
        vocab = {"іменник"}
        violations = check_metalanguage_scaffolding(content, vocab, "A1", 1)
        assert len(violations) == 0


class TestCheckVocabTableFormat:
    def test_a1_wrong_header(self):
        from audit.checks.vocabulary import check_vocab_table_format
        content = """## Словник
| Слово | Переклад | Примітка |
|---|---|---|
| книга | book | - |
"""
        violations = check_vocab_table_format(content, "A1")
        assert any(v["type"] == "VOCAB_HEADER" for v in violations)

    def test_b1_wrong_header(self):
        from audit.checks.vocabulary import check_vocab_table_format
        content = """## Vocabulary
| Word | English | POS | Gender | Note |
|---|---|---|---|---|
| книга | book | noun | f | - |
"""
        violations = check_vocab_table_format(content, "B1")
        assert any(v["type"] == "VOCAB_HEADER" for v in violations)

    def test_a1_wrong_columns(self):
        from audit.checks.vocabulary import check_vocab_table_format
        content = """## Vocabulary
| Word | English | Note |
|---|---|---|
| книга | book | - |
"""
        violations = check_vocab_table_format(content, "A1")
        assert any(v["type"] == "VOCAB_FORMAT" for v in violations)


# ============================================================================
# 5. pipeline/screen.py
# ============================================================================

class TestScreenFixExtraH1:
    def test_demote_extra_h1(self):
        from pipeline.screen import _fix_extra_h1
        text = "# Title\n\n# Extra Heading\n\nSome text\n\n# Summary"
        result, count = _fix_extra_h1(text)
        assert count == 1
        assert "## Extra Heading" in result
        assert "# Summary" in result  # Summary stays H1

    def test_no_extra_h1(self):
        from pipeline.screen import _fix_extra_h1
        text = "# Only Title\n\nSome text"
        _result, count = _fix_extra_h1(text)
        assert count == 0

    def test_h1_in_code_block(self):
        from pipeline.screen import _fix_extra_h1
        text = "# Title\n\n```\n# Code heading\n```\n\n# Another"
        result, count = _fix_extra_h1(text)
        assert count == 1
        assert "# Code heading" in result  # Not modified inside code block


class TestScreenFixIpaBrackets:
    def test_strip_ipa(self):
        from pipeline.screen import _fix_ipa_brackets
        text = "слово [slo-vo] (word)"
        result, count = _fix_ipa_brackets(text)
        assert count >= 1
        assert "[slo-vo]" not in result

    def test_no_ipa(self):
        from pipeline.screen import _fix_ipa_brackets
        text = "Just normal text"
        _result, count = _fix_ipa_brackets(text)
        assert count == 0


class TestScreenIpaScan:
    def test_ipa_detection(self):
        from pipeline.screen import _run_ipa_scan
        text = "Some text with [ɑɛɪɔʊ] transcription"
        issues = _run_ipa_scan(text)
        assert len(issues) >= 1
        assert issues[0]["type"] == "IPA_BANNED"

    def test_syllable_breakdown(self):
        from pipeline.screen import _run_ipa_scan
        text = "Word [syl-la-ble] analysis"
        issues = _run_ipa_scan(text)
        assert len(issues) >= 1

    def test_whitelist(self):
        from pipeline.screen import _run_ipa_scan
        text = "Zero form: [Ø]"
        issues = _run_ipa_scan(text)
        assert len(issues) == 0

    def test_no_ipa(self):
        from pipeline.screen import _run_ipa_scan
        text = "Normal text without phonetics"
        issues = _run_ipa_scan(text)
        assert len(issues) == 0


# ============================================================================
# 7. audit/checks/content_quality.py
# ============================================================================

class TestIsInsideQuotedString:
    def test_inside_double_quotes(self):
        from audit.checks.content_quality import is_inside_quoted_string
        assert is_inside_quoted_string('He said "hello world" today', 14)

    def test_outside_double_quotes(self):
        from audit.checks.content_quality import is_inside_quoted_string
        assert not is_inside_quoted_string('He said "hello" today', 20)

    def test_inside_guillemets(self):
        from audit.checks.content_quality import is_inside_quoted_string
        assert is_inside_quoted_string('Він каже «привіт» тут', 12)

    def test_outside_guillemets(self):
        from audit.checks.content_quality import is_inside_quoted_string
        assert not is_inside_quoted_string('Він каже «привіт» тут', 20)


class TestIsHistoricalQuoteLine:
    def test_blockquote(self):
        from audit.checks.content_quality import is_historical_quote_line
        assert is_historical_quote_line("> Some historical text")

    def test_not_blockquote(self):
        from audit.checks.content_quality import is_historical_quote_line
        assert not is_historical_quote_line("Normal text")


class TestIsHistoricalContextBlock:
    def test_explicit_marker(self):
        from audit.checks.content_quality import is_historical_context_block
        lines = ["> **Оригінал:** Text here", "> Continuation"]
        assert is_historical_context_block(lines, 0)
        assert is_historical_context_block(lines, 1)

    def test_quote_callout(self):
        from audit.checks.content_quality import is_historical_context_block
        lines = ["> [!quote] Historical", "> More text"]
        assert is_historical_context_block(lines, 0)

    def test_not_blockquote(self):
        from audit.checks.content_quality import is_historical_context_block
        lines = ["Normal text"]
        assert not is_historical_context_block(lines, 0)

    def test_blockquote_without_marker(self):
        from audit.checks.content_quality import is_historical_context_block
        lines = ["> Just a regular blockquote"]
        assert not is_historical_context_block(lines, 0)


class TestDetectTrackFromPath:
    def test_hist_track(self):
        from audit.checks.content_quality import detect_track_from_path
        assert detect_track_from_path("/curriculum/l2-uk-en/hist/module.md") == "hist"

    def test_lit_track(self):
        from audit.checks.content_quality import detect_track_from_path
        assert detect_track_from_path("/curriculum/l2-uk-en/lit/something.md") == "lit"

    def test_no_track(self):
        from audit.checks.content_quality import detect_track_from_path
        assert detect_track_from_path("/curriculum/l2-uk-en/a1/module.md") is None

    def test_empty(self):
        from audit.checks.content_quality import detect_track_from_path
        assert detect_track_from_path("") is None


class TestBibliographySection:
    def test_inside_bibliography(self):
        from audit.checks.content_quality import is_in_bibliography_section
        lines = ["## Джерела", "Some reference"]
        assert is_in_bibliography_section(lines, 1)

    def test_outside_bibliography(self):
        from audit.checks.content_quality import is_in_bibliography_section
        lines = ["## Main content", "Some text"]
        assert not is_in_bibliography_section(lines, 1)


class TestAcademicCalloutBlock:
    def test_inside_callout(self):
        from audit.checks.content_quality import is_in_academic_callout_block
        lines = ["> [!bibliography]", "> Some reference"]
        assert is_in_academic_callout_block(lines, 1)

    def test_outside_callout(self):
        from audit.checks.content_quality import is_in_academic_callout_block
        lines = ["Normal text"]
        assert not is_in_academic_callout_block(lines, 0)


class TestContainsOnlyAllowlistedLatin:
    def test_allowlisted(self):
        from audit.checks.content_quality import contains_only_allowlisted_latin
        assert contains_only_allowlisted_latin("UNESCO NATO")

    def test_not_allowlisted(self):
        from audit.checks.content_quality import contains_only_allowlisted_latin
        assert not contains_only_allowlisted_latin("Random latin word")


class TestIsAcademicLatinContext:
    def test_bibliography(self):
        from audit.checks.content_quality import is_academic_latin_context
        lines = ["## Джерела", "Snyder (2010)"]
        assert is_academic_latin_context("Snyder (2010)", lines, 1, "hist")

    def test_not_historical_track(self):
        from audit.checks.content_quality import is_academic_latin_context
        lines = ["## Content", "Some latin"]
        assert not is_academic_latin_context("Some latin", lines, 1, None)

    def test_blockquote(self):
        from audit.checks.content_quality import is_academic_latin_context
        lines = ["> Latin reference"]
        assert is_academic_latin_context("> Latin reference", lines, 0, "hist")

    def test_paren_proper_nouns(self):
        from audit.checks.content_quality import is_academic_latin_context
        lines = ["Тімоті Снайдер (Timothy Snyder)"]
        assert is_academic_latin_context(lines[0], lines, 0, "hist")


class TestValidateCharactersInContent:
    def test_russian_chars(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = "Це тест с ы"
        violations = validate_characters_in_content(content, "A1")
        assert any(v["type"] == "RUSSIAN_CHARACTERS" for v in violations)

    def test_clean_content(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = "Це чистий український текст"
        violations = validate_characters_in_content(content, "A1")
        assert len(violations) == 0

    def test_oes_exempt(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = "ъ ѣ old text"
        violations = validate_characters_in_content(content, "oes", "/path/oes/module.md")
        assert len(violations) == 0

    def test_historical_chars_in_modern(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = "This ъ should not be here"
        violations = validate_characters_in_content(content, "A1")
        assert any(v["type"] == "HISTORICAL_CHARS_IN_MODERN" for v in violations)

    def test_historical_chars_in_blockquote(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = "> Historical text with ъ"
        violations = validate_characters_in_content(content, "hist", "/path/hist/module.md")
        assert len(violations) == 0

    def test_russian_in_quotes_allowed(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = 'Він каже "ы э" тут'
        violations = validate_characters_in_content(content, "A1")
        assert len(violations) == 0  # inside quotes


class TestValidateYamlVocabulary:
    def test_russian_chars(self):
        from audit.checks.content_quality import validate_yaml_vocabulary
        yaml_content = "uk: тест с ы"
        violations = validate_yaml_vocabulary(yaml_content)
        assert any(v["type"] == "RUSSIAN_CHARACTERS_YAML" for v in violations)

    def test_clean_yaml(self):
        from audit.checks.content_quality import validate_yaml_vocabulary
        yaml_content = "uk: тест\nen: test"
        violations = validate_yaml_vocabulary(yaml_content)
        assert len(violations) == 0

    def test_historical_in_modern_field(self):
        from audit.checks.content_quality import validate_yaml_vocabulary
        yaml_content = "uk: тест ъ\nen: test"
        violations = validate_yaml_vocabulary(yaml_content)
        assert any(v["type"] == "HISTORICAL_CHARS_IN_MODERN_YAML" for v in violations)

    def test_historical_in_allowed_field(self):
        from audit.checks.content_quality import validate_yaml_vocabulary
        yaml_content = "oes: тест ъ ѣ"
        violations = validate_yaml_vocabulary(yaml_content)
        assert not any(v["type"] == "HISTORICAL_CHARS_IN_MODERN_YAML" for v in violations)


class TestExtractLessonContent:
    def test_with_activities(self):
        from audit.checks.content_quality import extract_lesson_content
        content = "---\ntitle: Test\n---\n\n# Title\n\nContent here\n\n## Activities\n\nActivity stuff"
        result = extract_lesson_content(content)
        assert "Content here" in result
        assert "Activity stuff" not in result

    def test_with_vocabulary(self):
        from audit.checks.content_quality import extract_lesson_content
        content = "---\ntitle: Test\n---\n\n# Title\n\nContent here\n\n## Vocabulary\n\nVocab stuff"
        result = extract_lesson_content(content)
        assert "Content here" in result

    def test_no_sections(self):
        from audit.checks.content_quality import extract_lesson_content
        content = "Just plain content"
        result = extract_lesson_content(content)
        assert "plain content" in result


class TestExtractModuleMetadata:
    def test_full_metadata(self):
        from audit.checks.content_quality import extract_module_metadata
        content = 'title: Test Module\nphase: A1\nmodule: 5\npedagogy: "communicative"\n\n# My Topic'
        metadata = extract_module_metadata(content)
        assert metadata["title"] == "Test Module"
        assert metadata["phase"] == "A1"
        assert metadata["module"] == 5
        assert metadata["topic"] == "My Topic"


class TestCheckContentQuality:
    def test_with_russian_chars(self):
        from audit.checks.content_quality import check_content_quality
        content = "---\ntitle: Test\n---\n\n# Test\n\nТекст з ы"
        violations = check_content_quality(content, "A1", 1)
        assert any(v["type"] == "RUSSIAN_CHARACTERS" for v in violations)

    def test_surzhyk_module_exempt(self):
        from audit.checks.content_quality import check_content_quality
        content = "---\ntitle: Surzhyk Module\n---\n\n# Surzhyk\n\nText with ы"
        violations = check_content_quality(content, "B1", 1)
        # Surzhyk modules should not flag Russian chars
        assert not any(v["type"] == "RUSSIAN_CHARACTERS" for v in violations)


# ============================================================================
# 8. manifest_utils.py
# ============================================================================

class TestParseNumberedSlug:
    def test_numbered(self):
        from manifest_utils import parse_numbered_slug
        num, base = parse_numbered_slug("01-the-cyrillic-code-i")
        assert num == 1
        assert base == "the-cyrillic-code-i"

    def test_unnumbered(self):
        from manifest_utils import parse_numbered_slug
        num, base = parse_numbered_slug("trypillian-civilization")
        assert num is None
        assert base == "trypillian-civilization"

    def test_year_prefixed(self):
        from manifest_utils import parse_numbered_slug
        num, base = parse_numbered_slug("1991-referendum")
        assert num is None
        assert base == "1991-referendum"

    def test_two_digit(self):
        from manifest_utils import parse_numbered_slug
        num, base = parse_numbered_slug("25-travel-and-transport")
        assert num == 25
        assert base == "travel-and-transport"


class TestModuleDataclass:
    def test_path(self):
        from manifest_utils import Module
        m = Module(slug="test", title="Test", level="a1", track="core", local_num=1, global_num=1)
        assert m.path == "/a1/test"
        assert m.numbered_slug == "01-test"


# ============================================================================
# 9. assess_research_helpers.py
# ============================================================================

class TestColored:
    def test_known_quality(self):
        from research.assess_research_helpers import _colored
        result = _colored("text", "exemplary")
        assert "text" in result
        assert "\033[32m" in result

    def test_unknown_quality(self):
        from research.assess_research_helpers import _colored
        result = _colored("text", "unknown_qual")
        assert result == "text"

    def test_none_quality(self):
        from assess_research_helpers import _colored
        result = _colored("text", None)
        assert result == "text"


class TestFormatQualityRow:
    def test_missing_info_no_gaps(self):
        from assess_research_helpers import _format_quality_row
        r = {"num": 1, "slug": "test-module", "info": None}
        result = _format_quality_row(r, ["depth", "breadth"], False)
        assert "missing" in result

    def test_missing_info_show_gaps(self):
        from assess_research_helpers import _format_quality_row
        r = {"num": 1, "slug": "test-module", "info": None}
        result = _format_quality_row(r, ["depth"], True)
        assert result is None

    def test_with_info(self):
        from assess_research_helpers import _format_quality_row
        r = {"num": 1, "slug": "test-module", "info": {
            "score": 8, "quality": "solid",
            "dimensions": {"depth": {"score": 3, "max": 3}},
            "gaps": ["gap1:detail", "gap2:detail", "gap3:detail", "gap4:detail"],
            "content_alignment": {"refresh_recommended": False},
        }}
        result = _format_quality_row(r, ["depth"], False)
        assert "test-module" in result
        assert "+1" in result  # 4 gaps, show 3 + "+1"

    def test_with_refresh(self):
        from assess_research_helpers import _format_quality_row
        r = {"num": 1, "slug": "test", "info": {
            "score": 7, "quality": "adequate",
            "dimensions": {}, "gaps": [],
            "content_alignment": {"refresh_recommended": True, "reasons": ["outdated"]},
        }}
        result = _format_quality_row(r, [], True)
        assert "outdated" in result


class TestBuildRefreshQueue:
    def test_empty(self):
        from assess_research_helpers import _build_refresh_queue
        assert _build_refresh_queue([]) == []

    def test_filters_and_sorts(self):
        from assess_research_helpers import _build_refresh_queue
        results = [
            {"num": 1, "slug": "a", "info": {"score": 5, "content_alignment": {"refresh_recommended": True}}},
            {"num": 2, "slug": "b", "info": {"score": 8, "content_alignment": {"refresh_recommended": True}}},
            {"num": 3, "slug": "c", "info": {"score": 9, "content_alignment": {"refresh_recommended": False}}},
            {"num": 4, "slug": "d", "info": None},
        ]
        queue = _build_refresh_queue(results)
        assert len(queue) == 2
        assert queue[0]["slug"] == "b"  # Sorted by score desc


class TestBuildUpgradeQueue:
    def test_filters(self):
        from assess_research_helpers import _build_upgrade_queue
        results = [
            {"num": 1, "slug": "a", "info": {"score": 5}},
            {"num": 2, "slug": "b", "info": {"score": 9}},
            {"num": 3, "slug": "c", "info": None},
        ]
        queue = _build_upgrade_queue(results, min_score=9)
        assert len(queue) == 2  # score<9 and None


class TestParseSlugEntry:
    def test_string(self):
        from assess_research_helpers import _parse_slug_entry
        assert _parse_slug_entry("module-name # comment") == "module-name"

    def test_non_string(self):
        from assess_research_helpers import _parse_slug_entry
        assert _parse_slug_entry(42) == "42"


# ============================================================================
# 10. lexical_sandbox.py
# ============================================================================

class TestExtractUkrWord:
    def test_simple(self):
        from lexical_sandbox import _extract_ukr_word
        assert _extract_ukr_word("собака") == "собака"

    def test_with_translation(self):
        from lexical_sandbox import _extract_ukr_word
        assert _extract_ukr_word("новий (new) — Collocations") == "новий"

    def test_with_dash(self):
        from lexical_sandbox import _extract_ukr_word
        assert _extract_ukr_word("великий — great") == "великий"


class TestExtractGender:
    def test_masculine(self):
        from lexical_sandbox import _extract_gender
        assert _extract_gender("noun:m:v_naz") == "m"

    def test_feminine(self):
        from lexical_sandbox import _extract_gender
        assert _extract_gender("noun:f:v_naz") == "f"

    def test_neuter(self):
        from lexical_sandbox import _extract_gender
        assert _extract_gender("noun:n:v_naz") == "n"

    def test_plural(self):
        from lexical_sandbox import _extract_gender
        assert _extract_gender("noun:p:v_naz") == "p"

    def test_none(self):
        from lexical_sandbox import _extract_gender
        assert _extract_gender("verb:imperf:pres") is None


class TestExtractCase:
    def test_nominative(self):
        from lexical_sandbox import _extract_case
        assert _extract_case("noun:m:v_naz") == "v_naz"

    def test_accusative(self):
        from lexical_sandbox import _extract_case
        assert _extract_case("noun:f:v_zna") == "v_zna"

    def test_none(self):
        from lexical_sandbox import _extract_case
        assert _extract_case("verb:imperf:inf") is None


class TestFormAllowed:
    def test_no_verbs(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(no_verbs=True)
        assert not _form_allowed("verb:imperf:pres:s1", c)

    def test_no_imperatives(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(no_imperatives=True)
        assert not _form_allowed("verb:imperf:impr:s2", c)
        assert _form_allowed("verb:imperf:pres:s1", c)

    def test_present_only(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(present_only=True)
        assert not _form_allowed("verb:imperf:past:m", c)
        assert not _form_allowed("verb:perf:futr:s1", c)
        assert _form_allowed("verb:imperf:pres:s1", c)

    def test_nominative_only(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(nominative_only=True)
        assert _form_allowed("noun:m:v_naz", c)
        assert _form_allowed("noun:m:v_kly", c)
        assert not _form_allowed("noun:m:v_rod", c)

    def test_no_accusative(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(no_accusative=True)
        assert not _form_allowed("noun:f:v_zna", c)
        assert _form_allowed("noun:f:v_naz", c)

    def test_unconstrained(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint()
        assert _form_allowed("noun:m:v_rod", c)
        assert _form_allowed("verb:imperf:past:m", c)


class TestCollectCandidates:
    def test_from_dict_hints(self):
        from lexical_sandbox import _collect_candidates
        plan = {"vocabulary_hints": {"nouns": ["собака (dog)", "кіт"], "verbs": ["бігти"]}}
        candidates = _collect_candidates(plan)
        assert "собака" in candidates
        assert "кіт" in candidates
        assert "бігти" in candidates

    def test_from_list_hints(self):
        from lexical_sandbox import _collect_candidates
        plan = {"vocabulary_hints": ["собака", {"word": "кіт"}]}
        candidates = _collect_candidates(plan)
        assert "собака" in candidates
        assert "кіт" in candidates

    def test_extra_words(self):
        from lexical_sandbox import _collect_candidates
        plan = {"vocabulary_hints": {}}
        candidates = _collect_candidates(plan, extra_words=["додатковий"])
        assert "додатковий" in candidates

    def test_string_value_in_dict(self):
        from lexical_sandbox import _collect_candidates
        plan = {"vocabulary_hints": {"single": "слово"}}
        candidates = _collect_candidates(plan)
        assert "слово" in candidates


class TestSelectPrimaryMatch:
    def test_common_word_non_noun(self):
        from lexical_sandbox import _select_primary_match
        matches = [
            {"lemma": "що", "pos": "noun", "tags": "noun:n:v_naz"},
            {"lemma": "що", "pos": "conj", "tags": "conj"},
        ]
        result = _select_primary_match("що", matches, True)
        assert result["pos"] == "conj"

    def test_verb_ending(self):
        from lexical_sandbox import _select_primary_match
        matches = [
            {"lemma": "дати", "pos": "noun", "tags": "noun:f:v_naz"},
            {"lemma": "дати", "pos": "verb", "tags": "verb:perf:inf"},
        ]
        result = _select_primary_match("дати", matches, False)
        assert result["pos"] == "verb"

    def test_default(self):
        from lexical_sandbox import _select_primary_match
        matches = [{"lemma": "книга", "pos": "noun", "tags": "noun:f:v_naz"}]
        result = _select_primary_match("книга", matches, False)
        assert result["pos"] == "noun"


class TestDescribeConstraints:
    def test_all_constraints(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _describe_constraints
        c = GrammarConstraint(no_verbs=True, no_imperatives=True, nominative_only=True,
                              no_accusative=True, present_only=True)
        desc = _describe_constraints(c)
        assert len(desc) == 5
        assert "ALL verbs" in desc

    def test_no_constraints(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _describe_constraints
        c = GrammarConstraint()
        assert len(_describe_constraints(c)) == 0


class TestPrioritizeVerbForms:
    def test_ordering(self):
        from lexical_sandbox import _prioritize_verb_forms
        forms = [
            {"word_form": "пишу", "tags": "verb:imperf:pres:s1"},
            {"word_form": "пиши", "tags": "verb:imperf:impr:s2"},
            {"word_form": "писати", "tags": "verb:imperf:inf"},
            {"word_form": "писав", "tags": "verb:imperf:past:m"},
        ]
        ordered = _prioritize_verb_forms(forms, max_forms=10)
        assert ordered[0] == "пиши"  # imperative first
        assert "писати" in ordered

    def test_max_limit(self):
        from lexical_sandbox import _prioritize_verb_forms
        forms = [{"word_form": f"form{i}", "tags": "verb:imperf:pres:s1"} for i in range(20)]
        ordered = _prioritize_verb_forms(forms, max_forms=5)
        assert len(ordered) == 5


class TestParseResourceRequest:
    def test_delimited(self):
        from lexical_sandbox import parse_resource_request
        raw = '===RESOURCE_REQUEST_START===\n{"requested_vocabulary": {"nouns": ["кіт"]}}\n===RESOURCE_REQUEST_END==='
        result = parse_resource_request(raw)
        assert result is not None
        assert "nouns" in result["requested_vocabulary"]

    def test_json_block(self):
        from lexical_sandbox import parse_resource_request
        raw = 'Some text\n```json\n{"key": "value"}\n```\nMore text'
        result = parse_resource_request(raw)
        assert result == {"key": "value"}

    def test_invalid_json(self):
        from lexical_sandbox import parse_resource_request
        result = parse_resource_request("not valid json at all")
        assert result is None


class TestExtractWordsFromRequest:
    def test_dict_vocab(self):
        from lexical_sandbox import extract_words_from_request
        req = {"requested_vocabulary": {"nouns": ["кіт", "собака"]},
               "requested_phrases": ["на добраніч"]}
        words = extract_words_from_request(req)
        assert "кіт" in words
        assert "собака" in words
        # phrases should extract Ukrainian words
        assert any("добраніч" in w for w in words)

    def test_list_vocab(self):
        from lexical_sandbox import extract_words_from_request
        req = {"requested_vocabulary": ["кіт", "собака"], "requested_phrases": []}
        words = extract_words_from_request(req)
        assert "кіт" in words
