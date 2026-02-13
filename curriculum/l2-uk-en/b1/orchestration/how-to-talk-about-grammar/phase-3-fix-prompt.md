# Phase 3 Fix: Activities Schema + Count

> **You are Gemini, fixing Phase 3 activities that failed audit.**

## Current Activities (READ FROM DISK)

```
curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml
```

**Activity reference guide** (CRITICAL — read the schema!):
```
docs/ACTIVITY-YAML-REFERENCE.md
```

## Audit Failures

### 1. Unjumble Schema Violation (CRITICAL)

Your unjumble activity uses the WRONG format. The JSON schema requires:

**CORRECT format** (what the schema expects):
```yaml
- type: unjumble
  title: "..."
  items:
    - words:
        - "Іменник"
        - "—"
        - "це"
        - "самостійна"
        - "частина"
        - "мови"
      answer: "Іменник — це самостійна частина мови"
```

**WRONG format** (what you produced):
```yaml
- type: unjumble
  title: "..."
  instruction: "..."  # ← NOT ALLOWED (additionalProperties: false)
  items:
    - jumbled: "Іменник / — / це / ..."  # ← WRONG: must be `words` array, not `jumbled` string
      answer: "..."
```

Two errors:
1. Field name: `jumbled` → must be `words`
2. Field type: string → must be array of strings
3. `instruction` field: NOT allowed in unjumble (additionalProperties: false in schema)

### 2. Activity Count (need 12, have 8)

B1 requires 12 activities minimum. Add 4 more activities of varied types.

**Suggested additions:**
- **translate**: 6+ items — translate grammar terms between Ukrainian and English
- **cloze**: 5+ sentences — fill in grammar terms from dropdown options (format: `{correct|wrong1|wrong2|wrong3}`)
- **select**: 6+ items — select all correct answers from options
- **error-correction**: Already have one; add a second focusing on case terminology

## Fix Instructions

1. Read the current activities YAML
2. Fix the unjumble activity (change `jumbled` → `words` array, remove `instruction` field)
3. Add 4 new activities to reach 12 total
4. Keep all existing correct activities unchanged

## Output Format

Return the COMPLETE fixed activities YAML:

```
===ACTIVITIES_START===
{all 12 activities, including fixed unjumble and 4 new ones}
===ACTIVITIES_END===
```

```
===FRICTION_START===
**Phase**: Phase 3: Activities Fix
**Step**: {what}
**Friction Type**: NONE | ...
**Raw Error**: {or "None"}
**Self-Correction**: {or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT change activities that already pass (match-up, quiz, fill-in, group-sort, true-false, mark-the-words, error-correction)
- Do NOT use forbidden types (essay-response, critical-analysis, comparative-study, authorial-intent, anagram)
- Do NOT add `instruction` field to unjumble
- BARE LIST at root — no wrapper
