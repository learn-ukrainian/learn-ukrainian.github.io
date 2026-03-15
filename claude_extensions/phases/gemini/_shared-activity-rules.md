## YAML Formatting Rules (HARD FAIL if violated)

**Do NOT use Ukrainian angular quotes `«»` in YAML values.** They break YAML parsing when combined with colons.

```yaml
❌ WRONG (guillemets + colon = YAML parse error):
  title: «Знайдіть пару: термін та його значення»
  explanation: Термін «доконати» означає: завершити дію.

✅ RIGHT (plain strings, quote with single quotes if value contains colon):
  title: 'Знайдіть пару: термін та його значення'
  explanation: Термін доконати означає завершити дію.
```

**Rules:**
1. **Never use `«»` in YAML** — use plain text or single/double quotes
2. **Quote any value containing `:`** with single quotes: `'text: with colon'`
3. **Double-check** every `title`, `question`, `sentence`, `explanation`, and `text` field

## Language Quality (applies to ALL Ukrainian text in activities)

- **No Russianisms**: кушати→їсти, приймати участь→брати участь, получати→отримувати, самий кращий→найкращий, відноситися→стосуватися, слідуючий→наступний
- **No Russian characters**: ы, э, ё, ъ must NEVER appear
- **No IPA**: NEVER include IPA symbols or `ipa` fields
- **No Latin transliteration**: Reference Ukrainian words in Cyrillic, not Latin (ZhYty → Жити)

## Vocabulary YAML Rules

1. **Object with `items:` wrapper** — NOT a bare list
2. **Follow plan's vocabulary_hints** — include all required items
3. **Each entry needs**: `lemma` (NOT `term`), `translation`, `pos`
4. **Optional fields**: `gender` (for nouns: m/f/n), `aspect` (for verbs), `notes`, `usage`, `example`
5. **NO `ipa` field**
6. **Count target**: {VOCAB_COUNT_TARGET} items

## Output Delimiters

> **Content outside delimiters is automatically discarded by the extraction pipeline.**

Activities block (BARE LIST — no wrapper):
```
===ACTIVITIES_START===
- type: quiz
  title: "..."
  items:
    ...
===ACTIVITIES_END===
```

Vocabulary block (OBJECT with `items:` wrapper):
```
===VOCABULARY_START===
items:
  - lemma: "слово"
    translation: "word"
    pos: "noun"
===VOCABULARY_END===
```

## Builder Notes (MANDATORY)

```
===BUILDER_NOTES_START===
phase: ACTIVITIES
status: SUCCESS | PARTIAL | BLOCKED
activity_count: {number of activities generated}
deviations:
  - "{any deviations from plan activity_hints and why}"
frictions:
  - type: SCHEMA_MISMATCH | PLAN_GAP | CONTENT_VOCABULARY_GAP
    description: "{what went wrong}"
    proposed_fix: "{how to fix}"
unverified_terms:
  - "{Ukrainian words in activities you couldn't verify}"
review_focus:
  - "{activities or items that need reviewer attention}"
===BUILDER_NOTES_END===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 3: Activities + Vocabulary
**Step**: {what you were doing when friction occurred, or "Full YAML generation"}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

## Item Counting

Use the post-generation verification block below to confirm you hit the required item counts. If any type is short, add more items before outputting.

## Activity Focus Override

If the plan's `activity_hints` includes a `focus` description, it is a HARD OVERRIDE of the default pattern for that activity type. Read the focus carefully and implement it literally.

Example: If focus says "Match Ukrainian letter to its sound (for false friends: Н≠H, С≠C)" → your match-up pairs MUST be letter→sound, NOT word→translation.

## Post-Generation Verification (MANDATORY)

After generating all activities, output this verification block:

```
===ACTIVITY_VERIFY_START===
Activity counts vs plan:
  - {type}: {actual} items (plan: {required}) ✅|❌
  - ...
Focus compliance:
  - {type}: {focus description} → implemented as: {what you actually built} ✅|❌
===ACTIVITY_VERIFY_END===
```

If any line shows ❌, output a corrected `===ACTIVITIES_START===` to `===ACTIVITIES_END===` block with the fixes applied, THEN output the friction report.

## Boundaries

- Do NOT modify lesson content — only generate activities and vocabulary
- Do NOT add fields not in the schema (check schema carefully!)
- Do NOT wrap in `activities:` or `vocabulary:` dictionary keys
- Do NOT request skills or delegate to Claude
