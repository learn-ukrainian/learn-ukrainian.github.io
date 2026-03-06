# Prompt Engineering Review: mine-and-yours

**Track:** a1 | **Sequence:** 20
**Pipeline:** v4
**Validate attempts:** 5
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Unreplaced placeholder `{H3_WORD_RANGE}` in content prompt | MEDIUM | phase-2-prompt.md | Line 6 reads "Every H3 gets {H3_WORD_RANGE} words" -- placeholder visible to Gemini rather than resolved value (60-80). Gemini must infer from placeholders.yaml. |
| Section headings mismatch between outline and plan | HIGH | phase-2-prompt.md | Word budget table uses outline titles ("Introduction: Whose is this?") but plan/meta uses different Ukrainian/English dual titles ("Вступ: Чия це річ?"). Gemini wrote English-only headings, causing PLAN_SECTION_MISSING on fix1. |
| Immersion rule unclear for M20 band | MEDIUM | phase-2-prompt.md | Immersion target "25-40%" but content prompt also says to "Write cultural notes, practical sections in Ukrainian first" -- tension between low immersion target and strong Ukrainian-first instruction. Gemini produced 8.4% initially. |
| Imperative constraint mentioned but no positive examples | MEDIUM | phase-2-prompt.md | Prompt says "Before M47, use indirect requests or English for instructions" but gives no examples of what TO write instead of imperatives. Gemini used Прочитайте, Порівняйте, Зверніть -- all imperatives caught in fix5. |
| Textbook examples irrelevant to M20 topic | LOW | phase-2-prompt.md | Grade 1 bukvar examples (letter-sound exercises) have zero relevance to possessive pronouns at M20. Wasted ~100 lines of context. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Section heading format expectation (bilingual H2) | Caused PLAN_SECTION_MISSING on fix1 -- Gemini wrote English-only headings while plan expected "Українська назва (English Name)" format | Add explicit instruction: "H2 headings MUST match meta content_outline titles exactly, including Ukrainian/English dual format" |
| No imperative alternatives list | 3 imperatives survived to fix5 (Прочитайте, Порівняйте, Зверніть) | Add table of imperative -> replacement patterns (e.g., "Порівняйте:" -> "For comparison:" or "Порівняння:") |
| Immersion calculation method | Model produced 8.4% initially, had to iterate 3 times to reach 25% | Explain how immersion % is calculated and give a concrete paragraph-level example at target % |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| PLAN_SECTION_MISSING (fix1) | template_gap | Prompt gives section titles in English but plan expects bilingual "Укр (Eng)" format | Inject exact H2 titles from meta into prompt, not a simplified English-only version |
| Immersion 8.4% LOW (fix2-4) | conflicting_guidance | Prompt says "25-40% Ukrainian" but then says "Grammar RULES stay in English" for a grammar module -- almost everything is grammar rules | Provide immersion recipes: "Ukrainian labels before tables", "Ukrainian callout text", "Ukrainian mini-dialogues" |
| Imperatives (fix5) | template_gap | Constraint mentioned abstractly but no concrete alternatives given | Add "INSTEAD OF / USE" table for common instructional imperatives |
| Section balance bloated (fix2-4) | template_gap | Section word budgets given but no instruction about balance tolerance | Already in non-negotiable rules but not echoed in prompt |
| Robotic structure (fix2-4) | model_limitation | 3 sentences starting with "if the..." | Anti-robotic section exists but may need stronger emphasis |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 5 | fix1: section heading mismatch; fix2-4: immersion too low + robotic structure + section bloat (same 3 issues repeated); fix5: imperatives | YES -- fix1 preventable by injecting exact H2 titles; fix2-4 are the SAME issues repeated 3 times (fix prompt was identical across fix2/fix3/fix4 -- pipeline sent same instructions); fix5 preventable with imperative alternatives |

**Critical finding:** validate-fix2, validate-fix3, and validate-fix4 prompts are IDENTICAL. The pipeline re-sent the exact same fix instructions 3 times without progress feedback. This is a pipeline bug -- fix prompts should include what changed since last attempt and why the previous fix was insufficient.

## Suggested Template Fixes

### Fix 1: Inject exact H2 titles from meta (Priority: HIGH)
**Before:** Section word budget table uses simplified English titles
**After:** Table uses exact meta `content_outline` titles in "Українська (English)" format, with explicit instruction "Use these EXACT headings as your H2 titles"

### Fix 2: Add imperative alternatives table (Priority: HIGH)
**Before:** "Before M47, use indirect requests or English for instructions"
**After:** Add table:
```
| Instead of (imperative) | Use (alternative) |
|------------------------|-------------------|
| Прочитайте цей діалог: | Reading practice: / Діалог: |
| Порівняйте: | Comparison: / Порівняння: |
| Зверніть увагу: | Note: / Важливо: |
| Виберіть: | Choose the correct answer: |
```

### Fix 3: Provide immersion recipe for grammar modules (Priority: HIGH)
**Before:** "TARGET: 25-40% Ukrainian"
**After:** Add concrete recipe with example showing how to reach 25-40% in a grammar module:
- Ukrainian section headers with (English) in parentheses
- Ukrainian example blocks introduced by "Наприклад:" / "Порівняння:"
- Short Ukrainian phrases with (translations) in explanatory paragraphs
- Mini-dialogues in Ukrainian with English glosses

### Fix 4: De-duplicate fix prompts (Priority: HIGH)
**Before:** Fix2/3/4 send identical instructions
**After:** Pipeline should track previous fix attempts and include delta: "Previous fix attempt changed X but immersion only reached Y%. Try Z strategy instead."

### Fix 5: Remove irrelevant textbook examples for M7+ modules (Priority: MEDIUM)
**Before:** Grade 1 bukvar letter exercises injected for M20 (possessive pronouns)
**After:** Only inject textbook examples when they match the module's pedagogical level and topic

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Inject exact H2 titles from meta to prevent section heading mismatches (prevents fix1 pattern across all modules)
2. Add imperative alternatives table (prevents fix5 pattern -- recurring across mine-and-yours AND demonstratives-this-that)
3. Provide immersion recipes with concrete paragraph-level examples (prevents fix2-4 loop pattern)
