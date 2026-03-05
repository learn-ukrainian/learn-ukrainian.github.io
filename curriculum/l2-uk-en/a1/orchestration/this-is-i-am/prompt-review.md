# Prompt Engineering Review: this-is-i-am

**Track:** a1 | **Sequence:** 9
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| IPA ban regex too aggressive | HIGH | validate-fix1-prompt.md | The validator flagged `[Ø]` as IPA_BANNED. The symbol Ø was used pedagogically to represent the zero copula gap (e.g., "Я [Ø] студент"), not as IPA. The regex `\[...\]` catches all bracketed text. Also caught `[am]` and `[Invisible Verb]` from table headers. |
| Meta outline recommends IPA | LOW | phase-A-output.md | Research output says "Provide English translations and IPA pronunciation for 'хто' and 'що' on their first occurrence" and "Introduce IPA only on the first occurrence" — contradicting the BANNED_IPA rule in the content prompt. |
| Section title mismatch between plan and meta | MEDIUM | phase-A-output.md | Plan says "Робота над помилками та практика" and "Продакшн: Хто я і Хто ви?" but meta outline uses "Робота над помилками: Пастка «Воно»" and "Підсумок та самоперевірка". Content follows meta, which is correct, but this means the plan's last two sections were restructured silently. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No predecessor module content | LOW | M9 builds on M7 (gender) and M8 (greetings); no predecessor content injected, but this had minimal impact since the prompt constraints cover grammar status adequately. |
| TIER_GUIDANCE placeholder says "file not found" | MEDIUM | Placeholder `TIER_GUIDANCE` reads "(Tier guidance file not found: tier-1-beginner.md)". The tier rubric was not injected into the prompt, meaning Gemini had no visibility into emotional safety mapping or beginner warmth requirements. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| Content friction: NONE reported | N/A | Gemini reported no friction during content generation. Self-corrected quote formatting. | N/A |
| Activities friction: NONE reported | N/A | Gemini reported no friction during activity generation. Self-corrected unjumble removal. | N/A |
| Validate fix 1: 5 IPA_BANNED issues | schema_mismatch | The IPA ban regex `\[...\]` flagged pedagogical bracket usage in the zero copula table headers. The content prompt itself instructs using "Ø" symbol to represent the gap, but the validator bans all brackets. | Fix validator regex to whitelist `[Ø]` or change the content prompt to use a non-bracket notation (e.g., em-dash or bold Ø without brackets). |
| Validate fix 2: 0 issues listed but still FAILED | template_gap | The fix prompt says "Fix 0 issue(s)" but still shows AUDIT FAILED. This is confusing — likely the first fix resolved all IPA issues but the second validation pass failed on a different gate not listed in the fix prompt. | Improve fix prompt to always list the specific failing gate, even when 0 deterministic issues remain. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 2 | IPA_BANNED regex false positive on [Ø] in zero copula table | YES — whitelist [Ø] in the IPA scanner, or instruct Gemini to use "Ø" without brackets in the content prompt |

## Placeholder Coverage

All referenced placeholders were filled. Key observations:
- `TIER_GUIDANCE` was populated with an error message ("file not found") rather than actual tier guidance. This is a deployment issue — the tier file exists at `.claude/skills/plan-review/review-tiers/tier-1-beginner.md` but the placeholder resolver could not find it.
- `DECODABLE_VOCABULARY` is empty (correct for M9 — full alphabet known)
- `VIDEO_DISCOVERY` is empty (no videos found)
- `REQUIRED_TYPES` is empty (no required activity types specified, though the plan hints strongly at fill-in)

## Suggested Template Fixes

### Fix 1: Whitelist [Ø] in IPA Scanner (Priority: HIGH)
**Prevents:** False positive IPA_BANNED on zero copula notation
**Scope:** All A1 modules that teach zero copula (M9, M11)
**Template file:** Validation script (IPA scanner regex)

```diff
- Pattern: \[.+?\]  (catches all bracketed text)
+ Pattern: \[.+?\]  EXCEPT \[Ø\] (whitelist pedagogical symbols)
```

### Fix 2: Fix TIER_GUIDANCE Placeholder Resolution (Priority: MEDIUM)
**Prevents:** Missing emotional safety mapping guidance for Gemini
**Scope:** All A1/A2 modules
**Template file:** Placeholder resolver / `batch_gemini_config.py`

The tier file path resolution fails. Ensure the resolver looks in `.claude/skills/plan-review/review-tiers/` or inject the file content directly.

### Fix 3: Improve Fix Prompt When 0 Issues Listed (Priority: MEDIUM)
**Prevents:** Confusing "Fix 0 issues" with AUDIT FAILED
**Scope:** All modules
**Template file:** validate-fix template

```diff
- # Fix 0 issue(s) in `{slug}`
+ # Re-validation for `{slug}` — previous fix resolved deterministic issues; check remaining audit gates.
```

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Whitelist `[Ø]` in IPA scanner — prevents false positive fix loops in zero copula modules
2. Fix TIER_GUIDANCE placeholder resolution — affects all beginner modules
3. Align research phase output with content prompt rules (IPA ban should be reinforced in research prompt)
