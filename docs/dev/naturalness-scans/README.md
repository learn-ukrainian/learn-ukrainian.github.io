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

### A1 Level (34 modules total) ✅ COMPLETE

| Report | Modules | Flagged | Average Score | Status |
|--------|---------|---------|---------------|--------|
| `a1-naturalness-scan-m01-m34.md` | M01-M34 (34 modules) | 2 modules | 7.5/10 → 8.0/10+ | Fixed ✅ |

**A1 Overall Results:**
- **Total modules scanned:** 34/34 (100% complete)
- **Prose activities found:** 25 modules (M10-M34)
- **Modules flagged and fixed:** 2 modules (M21, M22) - 8%
- **Checkpoints deferred:** 3 modules (M10, M20, M34)
- **Average score before fixes:** 7.5/10
- **Average score after fixes:** 8.0/10+
- **Final status:** READY FOR PRODUCTION ✅

**A1 Key Findings:**
- M01-M09: No prose activities (pure vocabulary drills)
- M10-M34: Single-sentence drills with good naturalness
- Only 2 modules needed fixes (M21, M22) - disconnected sentences
- A1 has simpler activities, less prone to naturalness issues than A2

### A2 Level (58 modules total) ✅ COMPLETE

| Report | Modules | Flagged | Average Score | Status |
|--------|---------|---------|---------------|--------|
| `a2-naturalness-scan-m01-m11.md` | M01-M11 (11 modules) | 4 modules | 6.8/10 → 8.0/10 | Fixed ✅ |
| `a2-naturalness-scan-m12-m25.md` | M12-M25 (14 modules) | 8 modules | 6.7/10 → 8.0/10 | Fixed ✅ |
| `a2-naturalness-scan-m26-m35.md` | M26-M35 (10 modules) | 3 modules | 6.9/10 → 8.0/10 | Fixed ✅ |
| `a2-naturalness-scan-m36-m44.md` | M36-M44 (9 modules) | 4 modules | 6.6/10 → 8.0/10 | Fixed ✅ |
| `a2-naturalness-scan-m45-m56.md` | M45-M56 (12 modules) | 4 modules | 7.1/10 → 8.0/10 | Fixed ✅ |
| `a2-naturalness-scan-m57-m58.md` | M57-M58 (2 modules) | 0 modules | 7/10 (review) | Deferred |

**A2 Overall Results:**
- **Total modules scanned:** 58/58 (100% complete)
- **Content modules flagged and fixed:** 23 modules (41%)
- **Average score before fixes:** 6.9/10
- **Average score after fixes:** 8.0/10
- **Critical errors found:** Multiple (gender, vocabulary violations)
- **Final status:** READY FOR PRODUCTION ✅

### B1 Level (91 modules total) ✅ COMPLETE

| Report | Modules | Flagged | Average Score | Status |
|--------|---------|---------|---------------|--------|
| `b1-naturalness-scan-m01-m05.md` | M01-M05 (5 modules) | 40% → 0% | 7.0 → 8.0/10+ | Fixed ✅ |
| `b1-naturalness-scan-m06-m15.md` | M06-M15 (10 modules) | 0% | 8.3/10 | Pass ✅ |
| `b1-naturalness-scan-m16-m25.md` | M16-M25 (10 modules) | 0% | 8.2/10 | Pass ✅ |
| `b1-naturalness-scan-m26-m35.md` | M26-M35 (10 modules) | 0% | 8.4/10 | Pass ✅ |
| `b1-naturalness-scan-m36-m45.md` | M36-M45 (10 modules) | 0% | 8.3/10 | Pass ✅ |
| `b1-naturalness-scan-m46-m55.md` | M46-M55 (10 modules) | 0% | 8.2/10 | Pass ✅ |
| `b1-naturalness-scan-m56-m65.md` | M56-M65 (10 modules) | 0% | 8.4/10 | Pass ✅ |
| `b1-naturalness-scan-m66-m71.md` | M66-M71 (6 modules) | 0% | **8.5/10** ⭐ | Pass ✅ |
| `b1-naturalness-scan-m72-m86.md` | M72-M86 (15 modules) | 33% → 0% | 6.6 → 8.0/10+ | Fixed ✅ |
| `b1-naturalness-scan-m87-m91.md` | M87-M91 (5 modules) | 0% | **8.8/10** ⭐⭐ | Pass ✅ |

**B1 Overall Results:**
- **Total modules scanned:** 91/91 (100% complete)
- **Modules flagged and fixed:** 10 modules (11%)
- **Average score before fixes:** 7.8/10
- **Average score after fixes:** 8.2/10
- **Final status:** READY FOR PRODUCTION ✅

**Highest Quality Sections:**
1. 🥇 **M87-M91** (Final Integration): 8.8/10
2. 🥈 **M66-M71** (Professional Vocabulary): 8.5/10
3. 🥉 **M26-M35** (Complex Sentences I): 8.4/10

**B1 Key Findings:**

**Metalanguage Bridge (M01-M05):**
- Purpose: Teach Ukrainian grammar terminology before full immersion
- Prose density: Very low (only 3 passages across 5 modules)
- Average score: 7.0/10 → improved to 8/10+ with M03 and M04 enhancements
- Quiz-heavy structure is pedagogically appropriate

**100% Immersion Sections (M06-M15, M16-M91):**
- Purpose: Teach grammar through natural Ukrainian narratives
- Prose density: Very high (extensive prose activities)
- Average score: 8.3/10 (exceeds content module target)
- **Immersion approach is highly effective** (+1.3 points vs metalanguage)

**Cultural/Regional Modules (M72-M86):**
- Initial issues: Template repetition ("унікальний регіон"), excessive intensifiers
- Fixes applied: 19 changes across M72-M75, M80
- After fixes: 8.0/10+ average
- **Fix documentation:** `b1-naturalness-fixes-m72-m75.md`

**Final Integration (M87-M91):**
- Highest quality section in entire B1 curriculum (8.8/10)
- Perfect discourse markers and topic coherence
- Realistic grammar/vocabulary integration scenarios
- M91 Capstone achieves 9/10 (exceptional quality)

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

| Metric | A2 (M01-M58) | B1 (M01-M91) |
|--------|--------------|--------------|
| **Total modules** | 58 | 91 |
| **Flagged rate** | 41% | 11% |
| **Critical errors** | Multiple (gender, vocabulary) | None |
| **Average score (before fixes)** | 6.9/10 | 7.8/10 |
| **Average score (after fixes)** | 8.0/10 | 8.2/10 |
| **Prose quality issues** | Disconnected drills, topic jumps | Mostly unified narratives |
| **Common issues** | Missing discourse markers, subject chaos | Template repetition (M72-M86 only) |

**Why B1 outperforms A2:**
1. **100% immersion from M06+** forces natural Ukrainian construction
2. **Metalanguage foundation (M01-M05)** gives students vocabulary to understand explanations
3. **Aspect as organizing principle** - every module centers on coherent aspect demonstrations
4. **Mature pedagogical design** - lessons learned from A1-A2 applied to B1
5. **Fewer flagged modules** - 11% vs 41% (73% improvement in baseline quality)

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

### B1 Strengths (After fixes: 100% pass rate)

1. **Unified topics** - Each module tells coherent stories
2. **Natural contexts** - Grammar taught through realistic scenarios
3. **Rich discourse markers** - Complex connectors (поки, коли, нарешті, спочатку)
4. **Strong subject consistency** - Clear subjects maintained throughout
5. **Emotional arcs** - Stories with natural progression
6. **Cultural authenticity** - Deep Ukrainian content (village life, family traditions, contemporary culture)
7. **Contemporary relevance** - IT work, programming, travel, fitness integrated naturally

### B1 Issues Found and Fixed

**M72-M75 (Regional Modules):**
- ❌ Template repetition: "унікальний регіон" used in 3 consecutive modules
- ❌ Double superlatives: "найвидатніший та найвідоміший" (redundant)
- ❌ Excessive intensifiers: "дуже", "надзвичайно", "справжній" overused
- ✅ **Fixed:** Varied vocabulary, removed redundancy, added discourse markers

**M80 (Active Lifestyle):**
- ❌ Robotic transitions: "Повітря тут дуже свіже, і це допомагає..."
- ❌ Mechanical constructions: "в спокійному темпі, не поспішаю"
- ✅ **Fixed:** Natural flow, simplified constructions, removed excessive "дуже"

## Next Steps

### Completed ✅
- ✅ **A1 M01-M34** full scan (all fixes applied) - 8.0/10+ average
  - Only 2 modules flagged (M21, M22) - 8% flagged rate
  - Simpler activities, less prone to naturalness issues
  - **Final status:** READY FOR PRODUCTION
- ✅ **A2 M01-M58** full scan (all fixes applied) - 8.0/10 average
  - 23 modules flagged (41%) - significant quality improvement needed
  - Critical errors fixed (gender, vocabulary violations)
  - **Final status:** READY FOR PRODUCTION
- ✅ **B1 M01-M91** complete scan (all fixes applied) - 8.2/10 average
  - M01-M05: Metalanguage improvements
  - M72-M75: Regional module fixes (19 changes)
  - M80: Active lifestyle flow improvements
  - Only 11% flagged - highest baseline quality
  - **Final status:** READY FOR PRODUCTION

### In Progress 🔄
- **B2 M01-M10** initial scan complete (7.2/10 average)
  - Passive Voice section analyzed
  - **Status:** On hold pending B2 audit completion
  - **Resume when:** B2 audits finished

### Pending ⏳
- **B2 M11-M145** (135 remaining modules)
  - Priority: MEDIUM (per GitHub issue #415)
  - Start after B2 audits complete
- **C1 M01-M202** (202 modules)
  - Priority: LOW (per GitHub issue #416)
  - Start after C1 content completion

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
