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
1. **Plan depth**: Does the outline specify every objective and point clearly enough to teach it with explanations, connections, and examples?
2. **Research quality**: Is there enough factual material to write about? Empty or thin research = FAIL.
3. **Vocabulary**: Are vocabulary_hints provided and sufficient for the level?
4. **Contradictions**: Do any teaching constraints conflict with the available evidence?
5. **Structural elements**: Scan content_outline points for visual keywords (chart, table, list, map, display, show). Count how many structural elements (tables, bulleted lists) you must produce — you will be checked against this count.
6. **Activity hint compliance**: Read activity_hints. Note each type's item count and focus description. These are HARD constraints — your output will be validated against them.

### If FAIL:
Output ONLY the preflight block above. Do NOT generate content. The pipeline will save your report and halt.

### If PASS:
Output the following INTENT block, then proceed to content generation. Writing these constraints yourself forces them into your working memory.

```
===INTENT_START===
structural_elements_required:
  - section: "{section name}" → must contain: {table|bulleted list|numbered list}
  - ...
vocabulary_must_appear: [{list all required vocab words}]
activity_targets: [{type}: {count} items (focus: {focus or "default"}), ...]
coverage_gaps: [{section}: {missing point or evidence}, ...]
===INTENT_END===
```

Then proceed immediately to content generation below.
