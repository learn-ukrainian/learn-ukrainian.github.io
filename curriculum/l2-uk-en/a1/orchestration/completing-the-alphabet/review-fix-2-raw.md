All inline fixes from the review are confirmed in place. Here's a summary of everything:

## Summary of All Fixes

### Already applied (by Phase D.1 inline fixes — verified present):
1. **Finding 1** ✅ — тінь moved from "Soft Т" to "Soft Н" category (line 52)
2. **Finding 2** ✅ — ДЖ, ДЗ, Apostrophe video URLs changed to overview video `ksXIXj7CXwc` with notes (lines 29-40)
3. **Finding 3** ✅ — Content framing added at line 120: "These are fixed phrases — you will learn how they work grammatically later." Дякую/Будь ласка are only in match-up (recognition), not fill-in (production)
4. **Finding 4** ✅ — `vesum_exempt: true` and `notes` added to quiz activity (lines 103-104)
5. **Finding 5** ✅ — мить added to prose (line 27) and vocabulary YAML (lines 32-36)

### Fixed now (Phase D.2 — audit-blocking schema violation):
6. **YAML_SCHEMA_VIOLATION** — Added `vesum_exempt` (boolean) and `notes` (string) as optional properties to:
   - `schemas/activities-a1.schema.json` → quiz-a1 definition
   - `schemas/activities-base.schema.json` → quiz definition

This resolves the blocking `YAML_SCHEMA_VIOLATION` audit gate that was caused by the `vesum_exempt: true` and `notes` fields not being recognized by the strict schema.

### Not fixable at content level (remaining audit warnings):
- `EXTRA_SECTION_IN_MARKDOWN` for "Підсумок — Summary" — WARNING only, non-blocking
- VESUM failures for `ДЖ`, `ДЗ`, `ець`, `иця`, `М'Я` — these are uppercase letter names and suffix fragments in prose, not real word errors. The VESUM checker flags them because they appear as standalone tokens. This would need a tooling fix to skip uppercase letter names and morphological suffix examples.

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: Full Phase D.2 — Audit YAML schema violation fix
**Friction Type**: SCHEMA_MISSING_FIELD
**Raw Error**: Schema validation error at key '0': {'text': "м'ясо", 'correct': True} is not of type 'string' — caused by `vesum_exempt` and `notes` fields not being in the quiz schema (additionalProperties: false rejects unknown fields, then oneOf tries other activity types and produces confusing error)
**Self-Correction**: Added `vesum_exempt` (boolean) and `notes` (string) as optional properties to both `activities-a1.schema.json` and `activities-base.schema.json` quiz definitions
**Proposed Tooling Fix**: (1) The VESUM activity checker should read the `vesum_exempt` flag and skip distractor validation when true. (2) The VESUM prose checker should skip uppercase letter names (ДЖ, ДЗ) and morphological suffix patterns (-ець, -иця) that appear as teaching examples, not vocabulary.
===FRICTION_END===
```