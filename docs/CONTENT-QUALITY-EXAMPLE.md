# Content Quality Audit - Example Output

## Example 1: High-Quality Module (Pass)

```bash
$ export GEMINI_API_KEY="your-key"
$ export AUDIT_CONTENT_QUALITY="true"
$ python3 scripts/audit_module.py curriculum/l2-uk-en/a1/06-the-living-verb-i.md
```

**Output:**
```
--- STRICT GATES (Level A1) ---
Words        ✅ 850/300
Activities   ✅ 10/8
Density      ✅ All > 12
Unique_types ✅ 6/4 types
Priority     ✅ Priority types used
Engagement   ✅ 4/3
Audio        ℹ️ No audio
Vocab        ✅ 28/20
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Immersion    🇺🇦 12.5% (target 8-18% (M06))

✅ AUDIT PASSED.
```

**LLM Evaluation:**
- Coherence: 5/5
- Relevance: 5/5
- Educational: 5/5
- Language: 5/5
- Overall: 5/5
- Recommendation: PASS

---

## Example 2: Module with Issues (Warning)

```bash
$ export GEMINI_API_KEY="your-key"
$ export AUDIT_CONTENT_QUALITY="true"
$ python3 scripts/audit_module.py curriculum/l2-uk-en/a2/12-aspect-introduction.md
```

**Output:**
```
## PEDAGOGICAL VIOLATIONS
- **[CONTENT_QUALITY]** Moderate quality score: 3/5
  - FIX: Consider improvements: Examples could be more varied, explanation of completion aspect needs more context

- **[CONTENT_QUALITY]** Low Educational score: 2/5
  - FIX: Improve educational value

--- STRICT GATES (Level A2) ---
Words        ✅ 1050/450
Activities   ✅ 12/10
Density      ✅ All > 12
Unique_types ✅ 7/5 types
Priority     ✅ Priority types used
Engagement   ✅ 5/3
Audio        ℹ️ No audio
Vocab        ✅ 32/25
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ⚠️ 2 violations (non-blocking)
Immersion    🇺🇦 42.3% (target 35-55% (M12))

## Recommendation
⚠️ MINOR FIXES (severity 25/100)

✓ AUDIT PASSED (with warnings).
```

**LLM Evaluation:**
- Coherence: 4/5
- Relevance: 4/5
- Educational: 2/5 ⚠️
- Language: 3/5
- Overall: 3/5
- Recommendation: NEEDS_IMPROVEMENT

**Issues Identified:**
1. Examples are all similar in structure (verb pairs shown but not used in context)
2. Missing explanation of when to use perfective vs imperfective
3. No clear progression from basic to complex usage

**Strengths:**
1. Clear table showing aspect pairs
2. Good verb conjugation examples
3. Well-structured introduction

---

## Example 3: Word Salad Detected (Fail)

```bash
$ export GEMINI_API_KEY="your-key"
$ export AUDIT_CONTENT_QUALITY="true"
$ python3 scripts/audit_module.py curriculum/l2-uk-en/b1/broken-module.md
```

**Output:**
```
## PEDAGOGICAL VIOLATIONS
- **[CONTENT_QUALITY]** Low quality score: 1/5
  - FIX: Issues: Repetitive sentence patterns, unclear topic progression, examples don't match explanations, missing coherent structure

- **[CONTENT_QUALITY]** Content appears to be word salad or meaningless filler
  - FIX: Rewrite with clear educational structure and meaningful examples

- **[CONTENT_QUALITY]** Low Coherence score: 1/5
  - FIX: Improve coherence

- **[CONTENT_QUALITY]** Low Relevance score: 2/5
  - FIX: Improve relevance

- **[CONTENT_QUALITY]** Low Educational score: 1/5
  - FIX: Improve educational value

- **[CONTENT_QUALITY]** Low Language score: 1/5
  - FIX: Improve language quality

- **[CONTENT_QUALITY]** LLM recommends complete rewrite
  - FIX: Major issues: No clear topic, repetitive examples, confusing explanations, appears auto-generated

--- STRICT GATES (Level B1) ---
Words        ✅ 1200/600
Activities   ✅ 14/12
Density      ✅ All > 12
Unique_types ✅ 8/6 types
Priority     ✅ Priority types used
Engagement   ✅ 6/4
Audio        ℹ️ No audio
Vocab        ✅ 40/30
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ❌ 8 violations (BLOCKING)
Immersion    🇺🇦 38.5% (target 35-55% (M20))

## Recommendation
🔄 REWRITE (severity 85/100)

❌ AUDIT FAILED.
```

**LLM Evaluation:**
- Coherence: 1/5 ❌
- Relevance: 2/5 ❌
- Educational: 1/5 ❌
- Language: 1/5 ❌
- Overall: 1/5 ❌
- Recommendation: REWRITE

**Critical Issues:**
1. Content repeats the same sentence structure 15+ times
2. Examples don't relate to the stated topic (motion verbs)
3. Explanations contradict each other
4. Appears to be auto-generated filler text
5. No pedagogical progression

---

## Example 4: API Not Configured (Default)

```bash
$ python3 scripts/audit_module.py curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md
```

**Output:**
```
--- STRICT GATES (Level A1) ---
Words        ✅ 983/300
Activities   ✅ 8/8
Density      ✅ All > 12
Unique_types ✅ 6/4 types
Priority     ✅ Priority types used
Engagement   ✅ 3/3
Audio        ℹ️ No audio
Vocab        ✅ 35/20
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Immersion    🇺🇦 9.9% (target 5-15% (M01))

✅ AUDIT PASSED.
```

**Note:** No content quality violations shown because `AUDIT_CONTENT_QUALITY` is not enabled.

---

## Interpreting Results

### Severity Levels

| Severity | Score | Impact | Action |
|----------|-------|--------|--------|
| **Pass** | 4-5/5 | No violations | Continue |
| **Warning** | 3/5 | Non-blocking | Consider improvements |
| **Error** | 1-2/5 | May block | Fix required |
| **Critical** | Word salad | Blocking | Complete rewrite |

### Common Issues

1. **Low Coherence**: Content jumps between topics without clear transitions
2. **Low Relevance**: Module teaches something different from the title
3. **Low Educational**: Missing explanations, poor examples, no progression
4. **Low Language**: Repetitive, confusing, grammatically incorrect
5. **Word Salad**: Meaningless filler, auto-generated patterns

### Fixing Issues

**For Coherence:**
- Add clear section transitions
- Organize content from simple to complex
- Use consistent terminology

**For Relevance:**
- Ensure examples match the topic
- Check that grammar explanations align with module focus
- Remove off-topic content

**For Educational Value:**
- Add clear explanations before examples
- Show progression (simple → complex)
- Include varied, meaningful examples
- Add "observe first" patterns for inductive learning

**For Language Quality:**
- Remove repetitive patterns
- Vary sentence structure
- Fix grammatical errors
- Use precise terminology

**For Word Salad:**
- Complete rewrite required
- Use curriculum plan as guide
- Follow established module templates
- Focus on one clear concept per section

---

## Integration Examples

### Check all A1 modules
```bash
export GEMINI_API_KEY="your-key"
export AUDIT_CONTENT_QUALITY="true"

for i in {1..34}; do
  echo "=== Module $i ==="
  python3 scripts/audit_module.py curriculum/l2-uk-en/a1/*-*.md 2>&1 | \
    grep "CONTENT_QUALITY" || echo "No content issues"
done
```

### Pipeline with content quality
```bash
export GEMINI_API_KEY="your-key"
export AUDIT_CONTENT_QUALITY="true"
npm run pipeline l2-uk-en a1
```

### Batch report
```bash
export GEMINI_API_KEY="your-key"
export AUDIT_CONTENT_QUALITY="true"

for f in curriculum/l2-uk-en/a2/*.md; do
  score=$(python3 scripts/audit_module.py "$f" 2>&1 | \
    grep "overall_score" | cut -d: -f2)
  echo "$(basename $f): Score $score"
done | sort -t: -k2 -n
```
