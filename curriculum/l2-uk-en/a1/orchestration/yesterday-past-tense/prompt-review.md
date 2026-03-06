# Prompt Engineering Review: yesterday-past-tense

**Track:** a1 | **Sequence:** 36
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE with self-corrections, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Section heading mismatch (same cross-module pattern) | HIGH | phase-2-prompt.md | Fix1 found 4 missing plan sections -- ALL 4 section titles were mismatched. Gemini wrote different section titles than the meta content_outline expected. |
| Dative case false positive on word fragments | MEDIUM | validate-fix2-prompt.md | Fix2 flagged "Чолові" and "телеві" as dative case -- these appear to be word fragments from the audit parser misreading Ukrainian text at line boundaries, not actual dative usage. |
| Sentence length rule too strict for grammar tables | MEDIUM | phase-2-prompt.md | Fix2 flagged a 20-word "sentence" and an 11-word "sentence" -- these may be table content or headings parsed as prose sentences. The 10-word max is correct for prose but audit may miscount table rows. |
| Activity prompt length validation too narrow | LOW | validate-fix2-prompt.md | Fix2 flagged quiz Q6 and Q8 with "prompt length 2 (target: 5-10)" -- these are quiz questions with very short prompts like "Він/вона?" which are pedagogically appropriate for gender-focused questions. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Section heading format (same as M20/M21) | 4 sections missing on fix1 | Inject exact meta titles |
| Metalanguage allowlist | "множина" (plural) flagged as metalanguage not in vocabulary | Provide list of allowed grammar terms at A1 or require English equivalents |
| Content writer self-corrected euphony | Friction report shows self-correction for euphony (в вікні patterns) but no friction type reported | Good: Gemini caught this proactively. Template's euphony rules working. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| PLAN_SECTION_MISSING x4 (fix1) | template_gap | Same as M20/M21 -- section title format mismatch | Inject exact meta titles |
| Dative false positive (fix2) | schema_mismatch | Audit parser misread word fragments as dative | Fix audit tokenizer |
| Sentence length false positive (fix2) | schema_mismatch | Table content parsed as prose sentences | Audit should exclude tables from sentence length check |
| Immersion 32.5% LOW (fix2) | conflicting_guidance | Same pattern as M20/M21 but for M36 band (35-55%) | Immersion recipes |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 2 | fix1: 4 section mismatches; fix2: immersion + dative false positives + sentence length + quiz prompt length + metalanguage | PARTIALLY -- fix1 fully preventable with exact titles; fix2 partially audit bugs |

**Notable:** Only 2 validate attempts vs 5 for M20 and M21. The content writer (Gemini) did excellent self-correction work on euphony, which reduced friction. The euphony rules in the prompt are working well.

## Suggested Template Fixes

### Fix 1: Inject exact H2 titles from meta (Priority: HIGH)
Same cross-module fix. This module had ALL 4 sections mismatched.

### Fix 2: Metalanguage allowlist for A1 (Priority: MEDIUM)
**Before:** No guidance on which Ukrainian grammar terms are acceptable
**After:** Add: "At A1, use English for grammar terms. Ukrainian metalanguage terms (множина, однина, родовий, etc.) should only appear if they are in the module's vocabulary_hints."

### Fix 3: Audit parser improvements (Priority: MEDIUM)
Multiple false positives from the audit:
- Word fragment dative detection ("Чолові", "телеві")
- Table content counted as prose sentences
- Quiz prompt length too rigid for gender-identification questions

## Summary

**Template health:** NEEDS WORK (but better execution than M20/M21)
**Top 3 fixes by leverage:**
1. Inject exact H2 titles from meta (prevented ALL fix1 issues across 4 modules so far)
2. Fix audit false positives (dative fragments, sentence length in tables)
3. Add metalanguage allowlist
