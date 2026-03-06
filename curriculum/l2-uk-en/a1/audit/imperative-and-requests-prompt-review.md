# Prompt Engineering Review: imperative-and-requests

**Track:** a1 | **Sequence:** M47
**Pipeline:** v4
**Validate attempts:** 3
**Friction reports:** 2 (content: NONE; activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Dative/instrumental ban contradicts imperative teaching | HIGH | phase-2-prompt.md + LEVEL_CONSTRAINTS | M47 teaches imperatives, which naturally require dative ("вам", "мові") and instrumental ("перед дієсловом", "за правилом") in explanatory text. The level constraints ban these cases categorically, but the module's pedagogical purpose requires using them in examples. Fix2 had 19 pedagogical violations including 3 dative and 3 instrumental hits. |
| Subordinate clause ban conflicts with polite requests | HIGH | LEVEL_CONSTRAINTS | M47 research outline includes "Чи не могли б ви...?" (conditional/subjunctive) and "Щоб + infinitive" patterns. The level constraints ban "якщо, тому що, бо, щоб" categorically. The content naturally used these, causing 5 subordinate clause violations in fix2. |
| Section heading mismatch (same as M44) | HIGH | phase-2-prompt.md | Fix1 and fix3 both flagged 5 missing plan sections. Gemini wrote content with different H2 titles than the plan specified. Three separate fix attempts all focused on this. |
| Russicism "давайте подивимося" | MEDIUM | validate-fix1-prompt.md | Caught a Russicism calque in fix1. The correct form is "подивімося". This specific calque isn't in the Russianisms table in the prompt. |
| Textbook examples irrelevant | LOW | phase-2-prompt.md | Grade 1 syllable drills for an M47 imperative module. Zaharijchuk p.76 shows letter "П" introduction -- zero relevance. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No exemption for grammar metalanguage cases | HIGH -- 6 false dative/instrumental positives | Add: "When explaining grammar rules IN ENGLISH, using Ukrainian case examples is permitted. The ban applies to Ukrainian prose sentences, not grammar tables." |
| No expanded Russicism list | MEDIUM | "давайте подивимося → подивімося" not in the standard Russicism table. Add common imperative-related calques. |
| Activity minimum items not prominent enough | MEDIUM -- 4 activity items-too-few violations in fix2 | Move item minimums table to top of phase-C prompt or add bold warning |
| VESUM false negatives on proper names | LOW | "Анно", "Олено", "Павло" flagged as not found -- these are vocative forms of proper names. VESUM doesn't cover vocatives of all names. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| 5 plan section headings missing (3 fix attempts) | schema_mismatch | Gemini used different H2 titles than plan. Same root cause as M44. | Pre-validate outline against plan sections |
| 19 pedagogical violations in fix2 | conflicting_guidance | Level constraints designed for M1-M30 applied uniformly to M47 which teaches advanced grammar. Dative/instrumental/subordinate bans make no sense for a module teaching imperative mood. | Create M40+ constraint variant that relaxes case and clause restrictions |
| 4 activities with too few items | template_gap | Item minimum table exists but Gemini generated 6-item activities when 8 required | Increase prominence of minimums -- add inline reminders per type |
| "дайи" in VESUM miss | model_limitation | Gemini wrote "*дайи" (the incorrect form) in an error-example context. VESUM correctly flagged it as not a word, but it was intentional as a negative example. | Add VESUM exemption for words inside error-example callouts |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 3 | Fix1: Russicism + 5 missing sections. Fix2: 19 pedagogy violations (dative/instrumental/subordinate/complexity/activity items). Fix3: 5 sections still missing. | YES -- relaxed constraints for M40+ and outline pre-validation would eliminate all 3 iterations. |

## Suggested Template Fixes

### Fix 1: Create M40+ constraint variant (Priority: HIGH)
**Before:** Same LEVEL_CONSTRAINTS for all A1 modules including dative/instrumental/subordinate bans
**After:** M40+ variant: "Dative and instrumental cases may appear in grammar explanations and example sentences. Subordinate clauses (якщо, щоб, бо) permitted in polite request patterns. Core restrictions remain: max 10 words per Ukrainian sentence, imperfective only."
**Applies to:** All A1 modules M40-M55+

### Fix 2: Add imperative-specific Russicisms (Priority: MEDIUM)
**Before:** Generic Russicism table with 10 entries
**After:** Add: "давайте подивимося → подивімося", "давайте посмотрим → подивімося" and other imperative calques
**Applies to:** M47 and any module using imperatives

### Fix 3: Inline activity item minimums (Priority: MEDIUM)
**Before:** Minimums in a table at the top of phase-C
**After:** Add inline comment to each schema example: `items: # minItems: 8 -- HARD MINIMUM`
**Applies to:** All phase-C prompts

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Create M40+ constraint variant -- eliminates ~15 of the 19 pedagogical violations
2. Pre-validate outline sections against plan -- prevents section mismatch fix loops
3. Add imperative-specific Russicisms to scan table
