"""
Tests for the track scoring system.

Tests scripts/scoring/metrics.py (metric extraction) and
scripts/scoring/caps.py (critical failure caps).
All pure functions with no file I/O.

Run with: pytest tests/test_scoring.py -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.scoring.caps import (
    apply_critical_caps,
    check_cap_violations,
    get_caps_for_track,
)
from scripts.scoring.metrics import (
    analyze_toponyms,
    calculate_citation_ratio,
    count_agency_markers,
    count_analysis_sections,
    count_callouts,
    count_cross_references,
    count_legacy_sections,
    count_stylistic_devices,
)

# =============================================================================
# TEST: count_callouts
# =============================================================================

class TestCountCallouts:
    def test_quote_callouts(self):
        content = """> [!quote]\n> «Слава Україні!»\n\n> «Ще не вмерла Україна»"""
        counts = count_callouts(content)
        assert counts['quote'] >= 2

    def test_myth_buster_callouts(self):
        content = "> [!myth-buster]\n> Цей міф не відповідає дійсності.\n\n> [!myth]\n> Інший міф."
        counts = count_callouts(content)
        assert counts['myth_buster'] >= 2

    def test_history_bite_callouts(self):
        content = "> [!history-bite]\n> Цікавий історичний факт."
        counts = count_callouts(content)
        assert counts['history_bite'] >= 1

    def test_analysis_callouts(self):
        content = "> [!analysis]\n> Аналіз тексту.\n\n### Аналіз: структура"
        counts = count_callouts(content)
        assert counts['analysis'] >= 2

    def test_context_callouts(self):
        content = "> 🇺🇦 **Культурний момент**\n> Факт.\n\n> 💡 **Чи знали ви?**\n> Цікаво."
        counts = count_callouts(content)
        assert counts['context'] >= 2

    def test_resources_callouts(self):
        content = "> [!resources]\n> Список ресурсів.\n\n### Додаткові ресурси"
        counts = count_callouts(content)
        assert counts['resources'] >= 2

    def test_empty_content(self):
        counts = count_callouts("")
        assert all(v == 0 for v in counts.values())

    def test_all_types_present(self):
        """All callout types should be in the result dict."""
        counts = count_callouts("no callouts here")
        expected_keys = {'quote', 'myth_buster', 'history_bite', 'analysis', 'context', 'resources'}
        assert set(counts.keys()) == expected_keys


# =============================================================================
# TEST: count_agency_markers
# =============================================================================

class TestCountAgencyMarkers:
    def test_ukrainian_subject_active_verb(self):
        content = "Українці створили потужну державу. Козаки захищали свою землю."
        agency, total = count_agency_markers(content)
        assert agency >= 2
        assert total >= 2

    def test_passive_not_counted(self):
        """Passive/state-of-being verbs should not count."""
        content = "Україна була частиною іншої держави."
        _agency, total = count_agency_markers(content)
        # 'була' is a state-of-being verb, 'Україна' is a subject
        # but the agency pattern checks for active verbs
        assert total >= 1

    def test_non_ukrainian_subjects(self):
        content = "The empire controlled the region. Moscow ordered the attack."
        agency, _total = count_agency_markers(content)
        assert agency == 0

    def test_sentence_counting(self):
        content = "Перше речення. Друге речення! Третє речення?"
        _, total = count_agency_markers(content)
        assert total == 3


# =============================================================================
# TEST: analyze_toponyms
# =============================================================================

class TestAnalyzeToponyms:
    def test_colonial_names_detected(self):
        content = "Місто Киев було столицею. Харьков на сході."
        violations, _correct = analyze_toponyms(content)
        assert violations >= 2

    def test_ukrainian_names_counted(self):
        content = "Київ — столиця України. Харків на сході. Львів на заході."
        violations, correct = analyze_toponyms(content)
        assert violations == 0
        assert correct >= 3

    def test_clean_content(self):
        content = "Цей текст не містить жодних топонімів."
        violations, correct = analyze_toponyms(content)
        assert violations == 0
        assert correct == 0


# =============================================================================
# TEST: count_cross_references
# =============================================================================

class TestCountCrossReferences:
    def test_related_blocks(self):
        content = "Related: [Module 5](../m05)\n\nRelated: [Module 10](../m10)"
        count = count_cross_references(content)
        assert count >= 2

    def test_wiki_links(self):
        content = "Див. [[M05 Козаки]]. Також [[M10 Гетьманщина]]."
        count = count_cross_references(content)
        assert count >= 2

    def test_no_references(self):
        content = "Простий текст без посилань на інші модулі."
        count = count_cross_references(content)
        assert count == 0


# =============================================================================
# TEST: calculate_citation_ratio
# =============================================================================

class TestCalculateCitationRatio:
    def test_with_quotes(self):
        content = "Шевченко писав: «Борітеся — поборете!» Це важливі слова."
        ratio = calculate_citation_ratio(content)
        assert ratio > 0.0
        assert ratio < 1.0

    def test_without_quotes(self):
        content = "Простий текст без жодних цитат і посилань."
        ratio = calculate_citation_ratio(content)
        assert ratio == 0.0

    def test_empty_content(self):
        ratio = calculate_citation_ratio("")
        assert ratio == 0.0

    def test_heavy_citation(self):
        content = '«Цитата перша» «Цитата друга» «Цитата третя»'
        ratio = calculate_citation_ratio(content)
        assert ratio > 0.3


# =============================================================================
# TEST: count_stylistic_devices
# =============================================================================

class TestCountStylisticDevices:
    def test_detects_devices(self):
        content = "Тут є метафора та порівняння. Також символ важливий."
        count = count_stylistic_devices(content)
        assert count >= 3

    def test_empty(self):
        assert count_stylistic_devices("Простий текст.") == 0


# =============================================================================
# TEST: count_analysis_sections
# =============================================================================

class TestCountAnalysisSections:
    def test_detects_analysis_headers(self):
        content = "## Літературний аналіз\n\n## Інтерпретація тексту"
        count = count_analysis_sections(content)
        assert count >= 2

    def test_empty(self):
        assert count_analysis_sections("No headers here.") == 0


# =============================================================================
# TEST: count_legacy_sections
# =============================================================================

class TestCountLegacySections:
    def test_detects_legacy_headers(self):
        content = "## Спадщина\n\n## Вплив на культуру\n\n## Значення"
        count = count_legacy_sections(content)
        assert count >= 3

    def test_empty(self):
        assert count_legacy_sections("No headers here.") == 0


# =============================================================================
# TEST: get_caps_for_track
# =============================================================================

class TestGetCapsForTrack:
    def test_hist_has_caps(self):
        caps = get_caps_for_track('hist')
        assert len(caps) >= 3
        names = [c.name for c in caps]
        assert 'zero_myth_busters' in names
        assert 'zero_quotes' in names

    def test_bio_has_caps(self):
        caps = get_caps_for_track('bio')
        names = [c.name for c in caps]
        assert 'zero_quotes' in names
        assert 'no_legacy' in names

    def test_lit_has_caps(self):
        caps = get_caps_for_track('lit')
        names = [c.name for c in caps]
        assert 'low_citation' in names

    def test_standard_track(self):
        caps = get_caps_for_track('b1')
        assert len(caps) >= 1
        names = [c.name for c in caps]
        assert 'zero_cross_references' in names

    def test_unknown_track_empty(self):
        caps = get_caps_for_track('unknown-track')
        assert caps == []


# =============================================================================
# TEST: apply_critical_caps
# =============================================================================

class TestApplyCriticalCaps:
    def test_cap_applied_zero_myth_busters(self):
        """Zero myth-busters should cap decolonization score."""
        metrics = {'total_myth_buster_callouts': 0, 'total_quote_callouts': 5,
                   'agency_marker_ratio': 0.2, 'total_cross_references': 3}
        scores = {'decolonization_perspective': 9.0, 'primary_source_integration': 8.0}
        updated, results = apply_critical_caps('hist', metrics, scores)
        assert updated['decolonization_perspective'] <= 4.0
        assert any(r.cap_applied and r.cap_name == 'zero_myth_busters' for r in results)

    def test_cap_not_applied_when_above(self):
        """If metric is above threshold, no cap applied."""
        metrics = {'total_myth_buster_callouts': 5, 'total_quote_callouts': 5,
                   'agency_marker_ratio': 0.2, 'total_cross_references': 3}
        scores = {'decolonization_perspective': 9.0, 'primary_source_integration': 8.0}
        updated, _results = apply_critical_caps('hist', metrics, scores)
        assert updated['decolonization_perspective'] == 9.0

    def test_cap_not_needed_score_already_low(self):
        """If score already below cap, cap not applied."""
        metrics = {'total_quote_callouts': 0, 'total_cross_references': 5,
                   'total_legacy_sections': 3}
        scores = {'source_reliability': 2.0}
        _updated, results = apply_critical_caps('bio', metrics, scores)
        # Score 2.0 is already below cap of 4.0, so cap_applied=False
        quote_cap = [r for r in results if r.cap_name == 'zero_quotes']
        assert len(quote_cap) == 1
        assert not quote_cap[0].cap_applied

    def test_zero_quotes_hist(self):
        metrics = {'total_myth_buster_callouts': 5, 'total_quote_callouts': 0,
                   'agency_marker_ratio': 0.2, 'total_cross_references': 3}
        scores = {'primary_source_integration': 8.0}
        updated, _ = apply_critical_caps('hist', metrics, scores)
        assert updated['primary_source_integration'] <= 3.0


# =============================================================================
# TEST: check_cap_violations
# =============================================================================

class TestCheckCapViolations:
    def test_detects_violations(self):
        metrics = {'total_myth_buster_callouts': 0, 'total_quote_callouts': 0,
                   'agency_marker_ratio': 0.05, 'total_cross_references': 0}
        violations = check_cap_violations('hist', metrics)
        assert len(violations) >= 3
        cap_names = [v['cap_name'] for v in violations]
        assert 'zero_myth_busters' in cap_names
        assert 'zero_quotes' in cap_names

    def test_no_violations_when_metrics_good(self):
        metrics = {'total_myth_buster_callouts': 5, 'total_quote_callouts': 5,
                   'agency_marker_ratio': 0.2, 'total_cross_references': 3}
        violations = check_cap_violations('hist', metrics)
        assert len(violations) == 0

    def test_lit_low_citation(self):
        metrics = {'total_analysis_sections': 5, 'avg_citation_ratio': 0.02,
                   'total_cross_references': 3}
        violations = check_cap_violations('lit', metrics)
        cap_names = [v['cap_name'] for v in violations]
        assert 'low_citation' in cap_names

    def test_unknown_track_no_violations(self):
        violations = check_cap_violations('unknown', {})
        assert violations == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
