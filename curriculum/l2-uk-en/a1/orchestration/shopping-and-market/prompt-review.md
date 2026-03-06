# Prompt Engineering Review: shopping-and-market

**Track:** a1 | **Sequence:** M40
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE with self-correction; activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Dative ban vs "Мені потрібна" in plan | HIGH | phase-2-prompt.md | Level constraints ban dative ("no мені, тобі"), but the plan/research suggest phrases like "Мені потрібна пачка цукру". Gemini produced "Мені потрібне мило" which was flagged in validate-fix2. The prompt says "no dative" but the research output (phase-A) already uses "Дайте" as a chunk. The contradiction between "fixed phrase chunks" and "grammar ban" needs explicit resolution. |
| Imperative ban vs "Дайте" usage | MEDIUM | phase-2-prompt.md | The module correctly treats "Дайте, будь ласка" as a lexical chunk (pre-M47), but the constraint section says "Imperative forms NOT taught until M47." This created confusion during validation where "Мені" was flagged but "Дайте" was not. Template should clarify: "Дайте is a permitted fixed chunk; dative pronouns are still banned." |
| Textbook examples irrelevant to M40 | LOW | phase-2-prompt.md | Textbook excerpts (Grade 1 буквар pages) show letter drills and syllable work -- completely irrelevant to a Module 40 shopping lesson. These consume ~800 tokens of context for zero benefit at this module level. |
| `{H3_WORD_RANGE}` placeholder unfilled | LOW | phase-2-prompt.md | Line 6: "Every H3 gets {H3_WORD_RANGE} words" -- placeholder not resolved. Gemini likely ignored it since section budgets are given separately. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No explicit "allowed dative chunks" list | HIGH -- caused 3 dative violations in fix2 | Add "PERMITTED DATIVE CHUNKS: Мені потрібно/потрібна (formulaic)" to sequence constraints |
| Required activity types field empty | LOW -- Gemini picked good types anyway | Populate `Required types` in phase-C-prompt targets table |
| Discovery found no videos | LOW | No action needed -- discovery is non-blocking |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| 3x "Скільки коштує..." robotic structure | template_gap | Anti-robotic rule says "no 3+ sentences starting same phrase" but doesn't distinguish Ukrainian immersion blocks (where repetition is pedagogical) from prose | Add exception: "Repetition within Ukrainian example blocks (vocabulary drills, pattern practice) is allowed" |
| Dative "Мені" flagged 3 times | conflicting_guidance | Level constraints ban dative categorically; research suggests "Мені потрібна" as essential shopping phrase | Define explicit "allowed formulaic dative" list in constraints |
| LOW_ENGAGEMENT (0 boxes in fix1) | model_limitation | Gemini initially produced 0 callout boxes despite "3+ MANDATORY" in bold | Already fixed by validation loop |
| Immersion too low (24.4%) in fix2 | template_gap | Immersion target "35-55%" stated but no concrete guidance on how to raise it during fixes | Add to fix prompt: "To raise immersion: convert English explanation sentences to Ukrainian+translation pairs" |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 2 | Fix1: engagement boxes missing. Fix2: dative "Мені" (3x), robotic structure, sentence too long, immersion low | Partially -- engagement should have been caught in initial generation. Dative issue is a template contradiction. |

## Suggested Template Fixes

### Fix 1: Resolve dative chunk contradiction (Priority: HIGH)
**Before:** "Dative case FORBIDDEN (no мені, тобі, йому...)"
**After:** "Dative case FORBIDDEN (no мені, тобі, йому...) EXCEPTION: Fixed formulaic chunks taught as vocabulary (e.g., 'Мені потрібно' in shopping modules) are permitted when explicitly listed in plan vocabulary_hints."
**Applies to:** All M30+ modules that use dative-containing fixed phrases

### Fix 2: Remove irrelevant textbook examples for M15+ (Priority: MEDIUM)
**Before:** Grade 1 буквар pages injected for all modules
**After:** Only inject textbook examples for M1-M14 (Cyrillic primer range). For M15+, inject examples from Grade 2-4 textbooks matching the module topic, or omit entirely.
**Applies to:** All A1 modules M15+

### Fix 3: Fill {H3_WORD_RANGE} placeholder (Priority: LOW)
**Before:** "Every H3 gets {H3_WORD_RANGE} words"
**After:** Calculate and inject actual range from content_outline (e.g., "Every H3 gets 50-100 words")
**Applies to:** All modules using phase-2 template

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Resolve dative ban vs. formulaic dative chunks -- prevents fix loops across all shopping/service modules
2. Remove irrelevant textbook examples for M15+ -- saves ~800 tokens, reduces confusion
3. Add immersion-raising guidance to fix prompts -- prevents multi-attempt immersion fixes
