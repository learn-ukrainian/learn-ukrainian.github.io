# Naturalness Scan Reports

This directory contains detailed naturalness analysis reports for curriculum modules across different CEFR levels.

## Purpose

These reports document the systematic scanning of curriculum modules for **naturalness** - how natural, coherent, and connected the prose activities feel to learners. The protocol used is documented in `claude_extensions/protocols/a1-naturalness-scan.md`.

## Naturalness Criteria

Each prose activity (cloze passages, unjumbles, fill-ins) is scored 1-10 based on:

1. **Subject consistency** - Are subjects maintained throughout passages?
2. **Discourse markers** - Presence of connectors (а, але, потім, тому, спочатку, нарешті, поки, коли)
3. **Topic coherence** - Do passages maintain unified topics or jump randomly?
4. **Redundancy** - Are there repetitive or disconnected sentences?

## Scoring Standards

| Module Type | Target Score | Acceptable Range |
|-------------|--------------|------------------|
| **Content modules** | 8/10 | 7-10/10 |
| **Review/Checkpoint** | 7/10 | 6-8/10 |
| **Metalanguage modules** | 7/10 | 6-8/10 |
| **Quiz-heavy modules** | N/A | No prose to score |

## Reports Index

### A2 Level (58 modules total)

| Report | Modules | Flagged | Average Score | Status |
|--------|---------|---------|---------------|--------|
| `a2-naturalness-scan-m26-m35.md` | M26-M35 (10 modules) | 3 modules | 6.9/10 → 8.0/10 (after fixes) | Fixed |
| `a2-naturalness-scan-m36-m44.md` | M36-M44 (9 modules) | 4 modules | 6.6/10 → 8.0/10 (after fixes) | Fixed |
| `a2-naturalness-scan-m57-m58.md` | M57-M58 (2 modules) | 0 modules | 7/10 (review standards) | Deferred |

**A2 Overall Results:**
- Total modules scanned: 58
- Content modules flagged and fixed: 23 modules (41%)
- Average score before fixes: 6.9/10
- Average score after fixes: 8.0/10
- Zero critical corruption errors found

### B1 Level (91 modules total)

| Report | Modules | Flagged | Average Score | Status |
|--------|---------|---------|---------------|--------|
| `b1-naturalness-scan-m01-m05.md` | M01-M05 (5 modules) | 0 modules | 7.0/10 | Improved to 8/10+ |
| `b1-naturalness-scan-m06-m15.md` | M06-M15 (10 modules) | 0 modules | 8.3/10 | Complete ✅ |

**B1 Key Findings:**

**Metalanguage Bridge (M01-M05):**
- Purpose: Teach Ukrainian grammar terminology before full immersion
- Prose density: Very low (only 3 passages across 5 modules)
- Average score: 7.0/10 → improved to 8/10+ with M03 and M04 enhancements
- Quiz-heavy structure is pedagogically appropriate

**100% Immersion Section (M06-M15):**
- Purpose: Teach aspect mastery through natural Ukrainian narratives
- Prose density: Very high (10 modules with extensive prose)
- Average score: 8.3/10 (exceeds content module target)
- Zero modules flagged for fixes
- **Conclusion: Immersion approach is highly effective** (+1.3 points vs metalanguage)

## Methodology

### 1. Scanning Protocol

For each module:
1. Read activity YAML file
2. Extract prose activities (cloze, unjumble with 5+ sentences, fill-in with multi-sentence context)
3. Analyze naturalness in Ukrainian language mode
4. Score 1-10 based on criteria above
5. Flag modules scoring < 8/10 for content, < 7/10 for review/metalanguage

### 2. Fixing Process

For flagged modules:
1. Identify specific naturalness issues
2. **Validate vocabulary constraints** - fixes can ONLY use vocabulary from M01-M{current}
3. **Maintain grammar constraints** - fixes can ONLY use grammar taught up to current module
4. Rewrite disconnected passages as coherent narratives
5. Add discourse markers for flow
6. Ensure subject consistency throughout

### 3. Vocabulary Validation

Before any fix:
```python
# Query cumulative vocabulary for level
python /tmp/query_{level}_vocab.py {module_num}

# Check if specific word is introduced
python /tmp/query_{level}_vocab.py check "слово"
```

## Comparison: A2 vs B1 Quality

| Metric | A2 (M01-M58) | B1 M06-M15 (Immersion) |
|--------|--------------|------------------------|
| **Flagged rate** | 41% | 0% |
| **Critical errors** | Multiple (gender, vocabulary) | None |
| **Average score (before fixes)** | 6.9/10 | 8.3/10 |
| **Prose quality issues** | Disconnected drills, topic jumps | Unified narratives |

**Why B1 immersion outperforms A2:**
1. **100% immersion from M06+** forces natural Ukrainian construction
2. **Metalanguage foundation (M01-M05)** gives students vocabulary to understand explanations
3. **Aspect as organizing principle** - every module centers on coherent aspect demonstrations
4. **Mature pedagogical design** - lessons learned from A1-A2 applied to B1

## Common Naturalness Issues Found

### A2 Issues (Fixed)

1. **Disconnected drills** - List of unrelated sentences for grammar practice
   - Example: "I go to park. She buys phone. We eat soup. He learns Ukrainian."
   - Fix: Create unified story connecting all sentences

2. **Topic jumping** - Passages with chaotic subject changes
   - Example: "я → вона → ми → він → це → вони" (no coherence)
   - Fix: Maintain single subject or coherent narrative arc

3. **Missing discourse markers** - No connectors between sentences
   - Example: Sentences with no але, потім, тому, спочатку, нарешті
   - Fix: Add natural temporal/logical connectors

4. **Redundancy** - Each sentence as isolated mini-story
   - Example: Multiple unrelated complete thoughts without progression
   - Fix: Create logical progression with shared context

### B1 Strengths (No fixes needed)

1. **Unified topics** - Each module tells coherent stories
2. **Natural contexts** - Grammar taught through realistic scenarios
3. **Rich discourse markers** - Complex connectors (поки, коли, нарешті, спочатку)
4. **Strong subject consistency** - Clear subjects maintained throughout
5. **Emotional arcs** - Stories with natural progression

## Next Steps

### Completed
- ✅ A2 M01-M58 full scan (all fixes applied)
- ✅ B1 M01-M05 metalanguage scan (improvements applied to M03, M04)
- ✅ B1 M06-M15 immersion scan (all modules pass)

### Pending
- B1 M16-M91 (remaining 76 modules)
- B2 M01-M145 (145 modules)
- A1 M01-M34 (34 modules - retroactive scan)
- C1 level (if needed)

## Report Format

Each report contains:
- **Executive Summary** - Total modules, flagged count, average scores
- **Scan Results by Module** - Detailed analysis with sample passages
- **Summary by Status** - Pass/Flagged/Deferred breakdown
- **Recommended Actions** - Specific fix strategies for flagged modules
- **Vocabulary & Grammar Constraints** - Allowed vocabulary/grammar for fixes
- **Comparison** - Results compared to previous batches

## Related Documentation

- Protocol: `claude_extensions/protocols/a1-naturalness-scan.md`
- Scan skill: `claude_extensions/commands/scan-naturalness.md`
- Module richness guidelines: `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- Curriculum plans: `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`

---

**Last Updated:** 2026-01-12
**Protocol Version:** a1-naturalness-scan.md
