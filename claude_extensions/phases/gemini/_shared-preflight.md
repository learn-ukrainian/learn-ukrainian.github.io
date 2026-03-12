## Pre-Flight Check (MANDATORY — Do This BEFORE Writing Content)

Before generating any content, evaluate whether you have sufficient information to write a quality module. Output your assessment in this format:

```
===PREFLIGHT_START===
plan_depth: SUFFICIENT | INSUFFICIENT — {reason}
research_quality: SUFFICIENT | INSUFFICIENT — {reason}
vocabulary_coverage: SUFFICIENT | INSUFFICIENT — {reason}
contradictions: NONE | {list contradictions found}
status: PASS | FAIL
notes: {any concerns, even if passing}
===PREFLIGHT_END===
```

### What to check:
1. **Plan depth**: Does the content_outline have enough detail for {WORD_TARGET} words? Vague 3-bullet outlines for 4000+ word modules = FAIL.
2. **Research quality**: Is there enough factual material to write about? Empty or thin research = FAIL.
3. **Vocabulary**: Are vocabulary_hints provided and sufficient for the level?
4. **Contradictions**: Do any constraints conflict with each other? (e.g., word target vs available material)

### If FAIL:
Output ONLY the preflight block above. Do NOT generate content. The pipeline will save your report and halt.

### If PASS:
Proceed immediately to content generation below.
