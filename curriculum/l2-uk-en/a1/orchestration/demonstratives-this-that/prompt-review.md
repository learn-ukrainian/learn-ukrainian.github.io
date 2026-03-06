# Prompt Engineering Review: demonstratives-this-that

**Track:** a1 | **Sequence:** 21
**Pipeline:** v4
**Validate attempts:** 5
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| IPA ban rule catches stage directions | HIGH | phase-2-prompt.md | The IPA_BANNED check flagged "[pointing to the counter]" and "[pointing behind the vendor]" -- these are stage directions in square brackets, not IPA. The prompt's IPA ban rule uses bracket detection that is too broad. |
| Section heading mismatch (same as M20) | HIGH | phase-2-prompt.md | Word budget table uses English titles ("Цей, Ця, Це: 'This' in Ukrainian") but plan expects "Цей vs Той у контексті (This vs That in context)" and "Практика (Practice)". PLAN_SECTION_MISSING on fix1. |
| Immersion target conflicting with content type | MEDIUM | phase-2-prompt.md | Immersion target "35-55%" but module is grammar-heavy (demonstrative pronouns). Gemini produced 25.1% initially, took multiple fixes to reach 39.3%. |
| Imperative constraint still lacks alternatives (same as M20) | MEDIUM | phase-2-prompt.md | Виберіть and Зверніть imperatives persisted through fix3 and fix5. Same root cause as M20 -- no positive alternatives provided. |
| Textbook examples irrelevant | LOW | phase-2-prompt.md | Grade 1 bukvar letter exercises (Й й, В в, Б б, Е е, Т т, К к) injected for M21 demonstratives module. Zero pedagogical overlap. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Stage direction vs IPA distinction | False positive IPA violations on fix1 wasted an iteration | Audit rule should distinguish `[stage direction]` from `[phonetic transcription]` -- or prompt should say "use parentheses for stage directions, not brackets" |
| Vocab-in-content requirement | Fix2 found only 12/20 (60%) vocab words in content+activities | Content prompt should explicitly say "Every vocabulary word from the plan MUST appear at least once in your prose or examples" |
| Dative case ban specifics | Fix2 flagged "мові" (locative of "мова") as dative -- this is actually locative, which IS allowed at A1 | Audit rule may have a false positive; prompt should clarify locative vs dative better |
| Metalanguage term policy | Fix2 flagged "однина" (singular) as metalanguage not in vocabulary | Prompt should list which Ukrainian grammar terms are allowed at A1 and which must stay in English |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| PLAN_SECTION_MISSING (fix1) | template_gap | Same as M20: English-only section titles vs bilingual plan titles | Inject exact meta titles |
| IPA false positive (fix1) | schema_mismatch | Bracket detection too broad -- catches stage directions | Fix audit rule or add prompt guidance: "Use (parentheses) not [brackets] for stage directions" |
| Immersion 25.1% LOW (fix2) | conflicting_guidance | Same as M20: grammar module + immersion target conflict | Provide immersion recipes |
| Imperatives persist (fix3, fix5) | template_gap | Same as M20: no alternatives given | Add imperative alternatives table |
| Vocab not in content (fix2) | context_gap | Content writer doesn't know vocab must appear in prose | Add explicit vocab-in-content requirement |
| "мові" false positive dative (fix2) | schema_mismatch | Audit confuses locative "мові" with dative | Fix audit rule -- locative is allowed at A1 |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 5 | fix1: section mismatch + IPA false positive; fix2: immersion + dative false positive + robotic + vocab gap; fix3: imperatives; fix4: immersion 34.6% (barely under 35%); fix5: imperative "Виберіть" | YES -- 4 of 5 preventable. IPA false positive and dative false positive are audit bugs, not prompt issues. Imperatives and section mismatch are template gaps. |

**Critical finding:** Fix4 shows immersion at 34.6% against a 35% minimum -- a 0.4% gap that triggers a full fix iteration. The immersion tolerance may be too tight, or the prompt should help Gemini overshoot to 40% to provide a safety margin.

## Suggested Template Fixes

### Fix 1: Inject exact H2 titles from meta (Priority: HIGH)
Same fix as M20 -- cross-module pattern.

### Fix 2: Add imperative alternatives table (Priority: HIGH)
Same fix as M20 -- cross-module pattern.

### Fix 3: Add vocab-in-content requirement (Priority: HIGH)
**Before:** No mention that vocab words must appear in prose
**After:** Add: "Every word from vocabulary_hints MUST appear at least once in your lesson text or examples. Check your draft against the vocabulary list before submitting."

### Fix 4: Fix IPA false positive for stage directions (Priority: MEDIUM)
**Before:** Audit flags any `[text in brackets]` as IPA
**After:** Either fix audit regex to exclude multi-word stage directions, or add to prompt: "Use (parentheses) for stage directions -- square brackets are reserved and will trigger IPA violations"

### Fix 5: Add immersion overshoot guidance (Priority: MEDIUM)
**Before:** "TARGET: 35-55%"
**After:** "TARGET: 35-55% (aim for 40-45% to provide safety margin -- modules at 34% will fail)"

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Inject exact H2 titles from meta (prevents fix1 -- same pattern as M20)
2. Add imperative alternatives table (prevents fix3/fix5 -- same pattern as M20)
3. Add vocab-in-content requirement (prevents fix2 vocab gap)
