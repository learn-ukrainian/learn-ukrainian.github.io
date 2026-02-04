# Track Scoring Verification System

Automated scoring system for curriculum tracks that enables objective 10/10 scoring without manual estimation.

## Overview

This system extracts quantitative metrics from curriculum modules and calculates weighted scores for each track. All measurements are automated (no LLM calls) ensuring reproducible results.

## Quick Start

```bash
# Score a single track
npm run score:b2-hist

# Score all tracks (summary)
npm run score:all

# Extract raw metrics
npm run metrics:extract b2-hist
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: Metric Extraction (metrics.py) - Per Module            │
├─────────────────────────────────────────────────────────────────┤
│ - Callout counts: [!quote], [!myth-buster], [!history-bite]     │
│ - Agency markers (Ukrainian subjects with active verbs)         │
│ - Toponym consistency check                                     │
│ - Era vocabulary items                                          │
│ - Cross-references                                              │
│ - Stylistic device density                                      │
│ - Citation ratio                                                │
│                                                                 │
│ OUTPUT: ModuleMetrics dataclass per module                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: Track Aggregation (aggregator.py)                      │
├─────────────────────────────────────────────────────────────────┤
│ - Aggregates all module metrics for track                       │
│ - Applies track-specific weighting matrix                       │
│ - Enforces critical failure caps                                │
│ - Generates verified 10/10 score with evidence                  │
│                                                                 │
│ OUTPUT: TrackScore with criterion breakdown                     │
└─────────────────────────────────────────────────────────────────┘
```

## Module Structure

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports |
| `config.py` | Track criteria definitions and weights |
| `metrics.py` | Metric extraction functions |
| `aggregator.py` | Module → track score aggregation |
| `caps.py` | Critical failure cap logic |
| `report.py` | Output formatting |

## Supported Tracks

### Specialized Tracks

| Track ID | Description | Module Count | Key Criteria |
|----------|-------------|--------------|--------------|
| `b2-hist` | Ukrainian History (B2) | 140 | Historical accuracy, primary sources, decolonization |
| `c1-hist` | Historiography (C1) | 30 | Source criticism, methodology, thematic coherence |
| `c1-bio` | Ukrainian Biographies (C1) | 128 | Biographical accuracy, legacy analysis, context |
| `lit` | Ukrainian Literature | 30 | Literary depth, authentic texts, stylistic devices |

### Standard Tracks

| Track ID | Description | Module Count |
|----------|-------------|--------------|
| `a1` | Standard A1 | 44 |
| `a2` | Standard A2 | 70 |
| `b1` | Standard B1 | 92 |
| `b2` | Standard B2 | 94 |
| `c1` | Standard C1 | 106 |
| `c2` | Standard C2 | 100 |

## Scoring Criteria

### B2-HIST Track (Ukrainian History)

| Criterion | Weight | Measurement |
|-----------|--------|-------------|
| Audit pass rate | 15% | status_json_pass_count / total_modules |
| Primary source integration | 15% | avg_quote_callouts_per_module |
| Historical accuracy | 15% | manual_verification + naturalness_gate |
| Decolonization perspective | 10% | myth_buster_count + agency_markers + toponym_consistency |
| Era-appropriate vocabulary | 10% | vocab_files_with_items / total_modules |
| Chronological coherence | 10% | date_sequence_validation |
| Critical analysis skills | 10% | critical_analysis_activities + analysis_callouts |
| Activity coverage | 10% | activity_files_present / total_modules |
| Internal consistency | 5% | cross_reference_count + terminology_consistency |

### LIT Track (Ukrainian Literature)

| Criterion | Weight | Measurement |
|-----------|--------|-------------|
| Audit pass rate | 15% | status_json_pass_count / total_modules |
| Literary depth/analysis | 20% | stylistic_device_density + analysis_sections |
| Authentic text engagement | 15% | citation_ratio + literary_quote_count |
| Archaic/literary vocabulary | 10% | archaic_vocab_items + literary_terms |
| Intertextual links | 10% | intertextual_reference_count |
| Activity coverage | 10% | activity_files_present / total_modules |
| Vocabulary coverage | 10% | vocab_files_with_items / total_modules |
| Internal consistency | 5% | cross_reference_count |
| CEFR alignment | 5% | level_tag_verification |

## Critical Failure Caps

Certain metric thresholds cap maximum scores regardless of other criteria:

| Condition | Cap | Track | Rationale |
|-----------|-----|-------|-----------|
| 0 `[!myth-buster]` callouts | Decolonization ≤ 4/10 | HIST | Can't score high without active myth-busting |
| 0 `[!quote]` blocks | Primary sources ≤ 3/10 | HIST/BIO | No sources = no integration |
| `citation_ratio` < 5% | Authentic engagement ≤ 5/10 | LIT | Too little direct text |
| 0 cross-references | Internal consistency ≤ 5/10 | All | No module connections |
| `agency_marker_ratio` < 10% | Decolonization ≤ 6/10 | HIST | Passive/external framing |

## Metrics Reference

### Callout Extraction

| Metric | Pattern | Purpose |
|--------|---------|---------|
| `quote_callouts` | `[!quote]`, `«...»` | Primary source quotes |
| `myth_buster_callouts` | `[!myth-buster]`, `### Міф` | Myth-busting sections |
| `history_bite_callouts` | `[!history-bite]`, `🏛️` | Historical facts |
| `analysis_callouts` | `[!analysis]`, `### Аналіз` | Analysis sections |
| `context_callouts` | `🇺🇦 Культурний момент`, `💡 Чи знали ви?` | Cultural context |

### Agency Markers

Measures decolonization perspective by detecting how often Ukrainians are portrayed as active agents.

**Ukrainian subjects detected:**
- `українці`, `народ`, `козаки`, `гетьман`
- `Україна`, `УНР`, `ЗУНР`, `Січ`
- `вони` + active verb (contextual)

**Active verb patterns:**
- Past tense: `-ли`, `-ав`, `-ла`, `-ло`
- Present tense: `-ить`, `-ять`, `-уть`

**Formula:** `agency_marker_ratio = agency_markers / total_sentences`

### Toponym Analysis

Detects colonial/Russian place names vs correct Ukrainian toponyms.

**Violations (colonial forms):**
- `Киев` → should be `Київ`
- `Харьков` → should be `Харків`
- `Малороссия` → colonial term

**Correct forms counted:**
- `Київ`, `Харків`, `Львів`, `Одеса`, `Маріуполь`, etc.

### Citation Ratio (LIT Track)

```
citation_ratio = quoted_characters / total_characters
```

Where quoted characters are text within `«...»` or `"..."` marks.

Target: ≥ 10% for full score

### Cross-References

Patterns detected:
- `Related: [...]`
- `[[M01-...]]` (wiki-style links)
- `див. модуль` (Ukrainian)
- `Пов'язано:`
- `Дивіться також:`

## Output Formats

### Console (default)

```
═══════════════════════════════════════════════════════════════════
  B2-HIST Track Scoring Report
  Generated: 2026-02-02 | Modules: 140 | Coverage: 100%
═══════════════════════════════════════════════════════════════════

AUTOMATED METRICS (from extract_track_metrics.py):
┌─────────────────────────────┬─────────┬─────────────────────────────┐
│ Metric                      │ Total   │ Per Module Avg              │
├─────────────────────────────┼─────────┼─────────────────────────────┤
│ [!quote] callouts           │ 416     │ 2.97                        │
│ [!myth-buster] callouts     │ 160     │ 1.14                        │
...
```

### Markdown (`--format markdown`)

```markdown
# B2-HIST Track Scoring Report

**Generated:** 2026-02-02
**Modules:** 140/140
**Final Score:** 8.85/10

## Criteria Scores

| Criterion | Weight | Score | Weighted |
|-----------|--------|-------|----------|
| Audit Pass Rate | 15% | 10/10 | 1.50 |
...
```

## Extending the System

### Adding a New Track

1. Add track config to `config.py`:

```python
TRACK_CONFIGS['new-track'] = {
    'name': 'New Track Name',
    'level_dir': 'new-track',
    'module_count': 50,
    'criteria': {
        'criterion_name': {
            'name': 'Display Name',
            'weight': 0.15,
            'description': '...',
            'measurement': 'metric_formula',
            'auto_fail_threshold': None,
            'cap_conditions': None,
        },
        # ... more criteria
    },
}
```

2. Add scoring logic to `aggregator.py`:

```python
elif criterion_name == 'new_criterion':
    # Calculate score based on track_metrics
    return calculated_score
```

3. Add caps to `caps.py` if needed:

```python
CRITICAL_CAPS['new-track'] = [
    CapCondition(
        name='zero_something',
        criterion='criterion_name',
        max_score=5.0,
        metric_name='total_something',
        threshold=0,
        reason_template='Reason for cap',
    ),
]
```

### Adding a New Metric

1. Add extraction logic to `metrics.py`:

```python
def count_new_metric(content: str) -> int:
    """Count new metric from content."""
    pattern = r'your_regex_pattern'
    matches = re.findall(pattern, content, re.IGNORECASE)
    return len(matches)
```

2. Add to `ModuleMetrics` dataclass:

```python
@dataclass
class ModuleMetrics:
    # ... existing fields
    new_metric: int = 0
```

3. Update `extract_module_metrics()` to call new function

4. Update `TrackMetrics` in `aggregator.py` with totals/averages

## Testing

```bash
# Run a quick test
.venv/bin/python scripts/score_track.py b2-hist

# Verify metrics extraction
.venv/bin/python scripts/extract_track_metrics.py b2-hist --format json | head -50

# Compare with manual verification
npm run score:all 2>&1 | tee scoring-output.txt
```

## Troubleshooting

### "Level directory not found"

The track's `level_dir` in config doesn't match an existing directory:
```
curriculum/l2-uk-en/{level_dir}/
```

### Unexpected zero counts

Check that the module files exist and contain expected patterns:
```bash
grep -r '\[!quote\]' curriculum/l2-uk-en/b2-hist/*.md | wc -l
```

### Score doesn't match expectations

1. Run with `--format json` to see raw metrics
2. Check if critical caps are being applied
3. Verify the scoring formula in `aggregator.py`

## LLM Verification Infrastructure

### Validation Tiers

| Tier | Name | When Applied |
|------|------|--------------|
| 1 | Automated | Default - all modules start here |
| 2 | LLM Verified | Risk-based: low naturalness score or sensitive tags |
| 3 | Gold Standard | Human-verified or stratified sample (20%) |

### Status JSON Verification Block

After LLM or human verification, add a `verification` block to `status/{slug}.json`:

```json
{
  "module": "slug-name",
  "level": "b2-hist",
  "gates": { ... },
  "overall": { ... },
  "verification": {
    "tier": "llm-verified",
    "reviewer": "claude",
    "timestamp": "2026-02-02T14:30:00Z",
    "score": 9.2,
    "evidence": "Verified 3 callouts, natural Ukrainian, no colonial framing",
    "critical_review": "Full review text here..."
  }
}
```

### Setting Verification Programmatically

```python
from scripts.audit.report import set_verification

set_verification(
    status_file='curriculum/l2-uk-en/b2-hist/status/oleh-ihor.json',
    tier='llm-verified',
    reviewer='claude',
    score=9.5,
    evidence='All callouts present, agency markers strong'
)
```

### Sampling Logic

The `sampling.py` module determines which modules need verification:

```python
from scripts.scoring.sampling import (
    determine_tier,      # What tier SHOULD this module be?
    get_validation_status,  # What tier IS it currently?
    should_sample,       # Is this in the 20% stratified sample?
    get_sampling_candidates,  # Which modules need verification?
)

# Find modules needing LLM verification
candidates = get_sampling_candidates(module_data_list)
```

**Risk triggers for Tier 2 (LLM Verified):**
- Naturalness score < 8.0
- Tags include: politics, war, religion, history, ideology, gender, controversial, policy, identity

**Tier 3 (Stratified Sample):**
- 20% of remaining modules (deterministic via slug hash)

## See Also

- `docs/l2-uk-en/B2-HIST-10-10-IMPROVEMENT-PLAN.md` - Improvement plan
- `docs/STATUS-SYSTEM.md` - Status caching system
- `scripts/audit/` - Module auditing system
