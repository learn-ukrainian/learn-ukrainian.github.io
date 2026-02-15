# Fix: Activity Pedagogy Violations (Attempt 1)

> **You are Gemini, fixing activities that failed audit.**
> **Your ONLY task: Fix the pedagogy violations in the activities YAML.**

## Files to Read

Read the current activities file:
```
curriculum/l2-uk-en/b1/activities/03-reading-grammar-rules.yaml
```

Read the activity schema:
```
schemas/activities-b1.schema.json
```

## Audit Failures

5 pedagogy violations found:

1. **match-up** 'Інструкції до вправ' has 8 pairs (target: 12-18)
   → FIX: Add 4+ more pairs to reach 12 minimum

2. **quiz** 'Аналітична термінологія' Q1 prompt length 3 words (target: 5-20)
   → FIX: Rewrite question to be at least 5 words

3. **quiz** 'Аналітична термінологія' Q4 prompt length 4 words (target: 5-20)
   → FIX: Rewrite question to be at least 5 words

4. **quiz** 'Аналітична термінологія' Q6 prompt length 3 words (target: 5-20)
   → FIX: Rewrite question to be at least 5 words

5. **quiz** 'Аналітична термінологія' Q8 prompt length 3 words (target: 5-20)
   → FIX: Rewrite question to be at least 5 words

## Your Task

**Output the COMPLETE fixed activities YAML** — all 6 activities with these fixes applied.

### Fix Instructions

**Match-up:** Keep all existing pairs. Add 4+ new pairs using instruction verbs and grammar terms from the lesson content.

**Quiz questions:** Rewrite ALL 8 quiz questions to be at least 5 Ukrainian words long. Make them complete questions, not fragments. Examples:
- ❌ "Що таке контекст?" (3 words)
- ✅ "Що означає термін контекст у граматиці?" (6 words)

### YAML Rules (CRITICAL)

- **BARE LIST at root** — no wrapper
- **No «» guillemets in YAML** — use plain text or single quotes if value contains `:`
- **No extra fields** not in schema
- **All 6 activities must be present in output**

## Output Format

```
===ACTIVITIES_START===
{all 6 activities, complete YAML}
===ACTIVITIES_END===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 4 Fix: Activity Pedagogy
**Step**: {what you were doing}
**Friction Type**: NONE | ...
**Raw Error**: {error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT add new activity types
- Do NOT remove existing activities
- Do NOT change activity types
- ONLY fix the listed violations
