# Prompt Engineering Review: food-vocabulary

**Track:** a1 | **Sequence:** 39
**Pipeline:** v4
**Validate attempts:** 6 (exhausted) + 1 escalation
**Friction reports:** 2 (phase-2-friction-3, phase-C-friction)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Expand prompt shows negative word delta | HIGH | phase-2-expand-2.md, phase-2-expand-3.md | "Your previous output was **3526 words** — below the **1200 word minimum**. You need to add approximately **-2326 more words**." The module already exceeded the target by 2326 words but the template computed a negative delta and still triggered an expand pass. This wasted a full model call. |
| `{H3_WORD_RANGE}` placeholder not resolved in writing tone instruction | LOW | placeholders.yaml / phase-2-prompt.md | Line 7 of phase-2-prompt says "Every H3 gets {H3_WORD_RANGE} words" — the placeholder is injected into the prompt's intro but the tone instruction field itself still contains the raw token. Gemini sees it as literal text. |
| Imperative ban not prominent enough | HIGH | phase-2-prompt.md | The imperative constraint appears in Module Constraints and Pedagogical Constraints sections, but Gemini still produced 15+ imperative forms across 6 fix attempts. The ban is buried among many other rules. Needs a dedicated callout box at the top of the writing instructions. |
| Meta outline uses `title:` but audit expects `section:` key | MEDIUM | phase-A-prompt.md (outline template) | The research/meta prompt outputs `content_outline` with `title:` key. The audit's `outline_compliance.py:298` expects `section:` key. This caused a `KeyError: 'section'` crash during validation, burning fix attempts. |
| Contradictory plan vocabulary | MEDIUM | placeholders.yaml (VOCAB_HINTS) | Plan includes "Мені подобається + Dative" in section title, but Dative is banned at A1. Research correctly flagged this, but the plan section name was never corrected, causing confusion in content generation. |
| IPA mentioned in meta outline | LOW | phase-A-output.md | Research output mentions "IPA for first occurrences" in the outline point, despite IPA being banned. This conflicting instruction propagated into the meta. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| Plan section names not injected into validate-fix prompts | Fix attempts could not match sections because the fix prompt says "Missing 5 plan section(s)" without showing what the content H2s actually are. The model could not diagnose the `title:` vs `section:` key mismatch. | Inject both plan section names AND current content H2s into fix prompts. |
| No prior module content provided | Gemini has no knowledge of what M38 (My Daily Routine) taught, so cannot avoid repetition or build on prior knowledge. | Inject a summary of M38 vocab and grammar. |
| Expand prompt does not explain WHY content needs expansion | The expand prompt only shows word counts, not what quality problems exist. Since the module was already over target (3526 > 1200), the expand was incorrect. | Add logic to skip expand when content exceeds target. |
| Audit error details not parsed into fix prompts | The escalation prompt received the raw traceback including `KeyError: 'section'`, but fix prompts 1-6 only received the generic "AUDIT FAILED" message without the actual error. | Parse and inject the specific error into fix prompts. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| Dative case conflict in plan | conflicting_guidance | Plan has "Мені подобається / Я не їм" as section title implying Dative, but A1 bans Dative. Research caught it. | Fix plan to use "Я люблю / Я не їм". Remove Dative reference. |
| IPA in meta outline | conflicting_guidance | Research output included "IPA for first occurrences" in outline point despite IPA ban in shared rules. | Add explicit "NO IPA" reminder in research prompt template. |
| Imperative forms persist across 6 fix rounds | template_gap | Each fix prompt lists the same constraint text, but the model keeps generating imperatives. The instruction is not specific enough about WHICH Ukrainian words are imperatives. | Add an explicit imperative detection list: "Forms ending in -те, -мо, -ть after stems are imperatives. Examples: Запам'ятайте, Уявіть, Подивіться, Зробіть, Знайдіть." |
| `title:` vs `section:` key mismatch | schema_mismatch | Research prompt template outputs outline with `title:` key. Audit code expects `section:` key. Neither the prompt nor the audit aligns. | Either update research prompt to output `section:` or update audit code to accept `title:`. |
| Expand triggered despite over-target word count | template_gap | Pipeline computed 3526 words but still triggered expand with negative delta (-2326). Bug in pipeline word count comparison logic. | Fix pipeline: skip expand when `actual >= target`. |
| Massive word overshoot (4538 words for 1200 target) | model_limitation | Gemini produced 3.8x the target despite clear "approximately 1200 words" instruction. Expand passes made it worse. | Add hard cap: "Do NOT exceed 1800 words (1.5x target)." |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 6 + escalation | Imperative forms (fixes 1-5) + meta `title:`/`section:` key mismatch (fix 6 + escalation) | YES - imperative ban needs examples; meta schema must match audit expectations |
| expand | 2 (expand-2, expand-3) | Pipeline incorrectly triggered expand on already-over-target content | YES - pipeline bug: negative delta should skip expand |

Fix attempts 1-3 were identical (same 4 imperative issues). The model kept producing new imperatives in the fixes because it did not understand which Ukrainian words are imperative forms. Fix 4 added more imperatives in different sections. Fix 5 caught different imperatives but introduced more. Fix 6 hit the `KeyError: 'section'` crash — a completely different issue that was impossible to fix from the content side. The escalation fixed the meta YAML key mismatch.

## Suggested Template Fixes

### Fix 1: Add explicit imperative examples to constraint text (Priority: HIGH)
**Prevents:** 6-attempt fix loops for imperative violations across ALL A1 modules
**Scope:** All A1 M1-46 modules
**Template file:** `claude_extensions/templates/a1-content-prompt.md` (PEDAGOGICAL_CONSTRAINTS placeholder)

Current:
```
KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47.
```

Proposed:
```
KEY RESTRICTION: Ukrainian imperative forms are BANNED before M47.
IMPERATIVE DETECTION: Any Ukrainian verb form ending in -те, -мо (1st person plural imperative), or -ть directed at the reader is imperative. Common violations:
- Запам'ятайте, Уявіть, Подивіться, Зробіть, Знайдіть, Порівняйте, Використовуйте, Подумайте, Зробімо, Вивчімо
REPLACEMENT: Use English ("Remember:", "Imagine:", "Compare:") or indicative ("Ми порівнюємо", "Ви бачите").
```

### Fix 2: Align meta outline key with audit expectations (Priority: HIGH)
**Prevents:** `KeyError: 'section'` crash in validation
**Scope:** All modules using v4 pipeline
**Template file:** `claude_extensions/templates/research-prompt.md` (META_OUTLINE output format)

Change outline template from `title:` to `section:` key, or update `scripts/audit/checks/outline_compliance.py:298` to accept both.

### Fix 3: Fix pipeline expand logic for negative delta (Priority: HIGH)
**Prevents:** Wasted model calls on already-over-target content
**Scope:** All modules
**Template file:** `scripts/pipeline_v5.py` (expand phase trigger logic)

Add guard: `if actual_words >= target_words: skip expand phase`.

### Fix 4: Add word count ceiling to content prompt (Priority: MEDIUM)
**Prevents:** 3.8x overshoot (4538 vs 1200 target)
**Scope:** All A1 modules
**Template file:** `claude_extensions/templates/a1-content-prompt.md`

Add: "Target: 1200 words. Hard ceiling: 1800 words. Do NOT exceed 1.5x the target."

### Fix 5: Parse audit errors into fix prompts (Priority: MEDIUM)
**Prevents:** Fix prompts showing only "AUDIT FAILED" without actionable detail
**Scope:** All modules
**Template file:** `scripts/pipeline_v5.py` (validate-fix prompt generation)

Extract specific error messages (tracebacks, gate failures, violation lists) and inject them into the fix prompt's "Other Audit Failures" section.

### Fix 6: Remove conflicting IPA reference from research output (Priority: LOW)
**Prevents:** IPA references propagating into meta outline
**Scope:** A1 modules
**Template file:** `claude_extensions/templates/research-prompt.md`

Add: "Do NOT mention IPA transcriptions in outline points. IPA is BANNED at all levels."

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. **Imperative examples in constraint text** — prevents the dominant fix loop pattern (6 attempts wasted)
2. **Meta outline `title:`/`section:` key alignment** — prevents audit crash that requires escalation
3. **Pipeline expand logic fix** — prevents wasted model calls on over-target content
