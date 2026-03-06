# Prompt Engineering Review: description-adverbs

**Track:** a1 | **Sequence:** M42
**Pipeline:** v4 (INCOMPLETE -- failed at activities phase)
**Validate attempts:** 0 (never reached validation)
**Friction reports:** 1 (content: NONE with self-correction on euphony)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Textbook examples completely irrelevant | MEDIUM | phase-2-prompt.md | Grade 1 table-of-contents pages and syllable drills injected for an M42 adverb module. Five textbook excerpts, several duplicates of the same page (bolshakova p.79 appears 3 times). Zero pedagogical value. |
| Research mentions IPA despite ban | LOW | phase-A-output.md | Research output says "Include 4-5 core examples with IPA on their first occurrence" but the content prompt bans IPA. The research phase template should include the IPA ban reminder. |
| `{H3_WORD_RANGE}` placeholder unfilled | LOW | phase-2-prompt.md | Same unfilled placeholder as other modules |
| Pipeline halted -- no activities or validation | HIGH | state-v4.json | State shows only research, discover, content phases completed. Activities phase never ran. No completion verdict available. The `completion.md` says FAIL with 1452 words (above target), suggesting the pipeline crashed between content and activities. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Required activity types empty in phase-C | N/A -- phase-C was generated but never executed | Populate required types field |
| No prior module content for sequencing | LOW | Adverbs build on adjectives (M11), but no cross-module content injected. Research correctly notes the dependency. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| Pipeline failure after content | model_limitation | State shows content complete but activities never started. Likely a gemini-cli error (similar to must-and-want's "Premature close" error). | Not a prompt issue -- infrastructure |
| Euphony self-correction (ура́нці/вра́нці) | model_limitation | Gemini self-corrected euphony before submission. Shows the euphony rules in the prompt are working. | None needed |
| Duplicate textbook page injections | template_gap | bolshakova p.79 injected 3 times with different truncation points | Discovery/RAG deduplication needed |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| N/A | 0 | Pipeline crashed before validation | N/A -- infrastructure issue |

## Suggested Template Fixes

### Fix 1: Deduplicate textbook RAG chunks (Priority: MEDIUM)
**Before:** Same page injected multiple times (bolshakova p.79 x3)
**After:** Deduplicate by page+author before injection
**Applies to:** All modules using textbook RAG

### Fix 2: Add IPA ban to research phase template (Priority: LOW)
**Before:** Research template has no IPA guidance
**After:** Add to phase-A boundaries: "Do NOT include IPA transcriptions in vocabulary tables or examples"
**Applies to:** All modules

## Summary

**Template health:** GOOD (content phase worked well; failure was infrastructure)
**Top 3 fixes by leverage:**
1. Fix pipeline infrastructure to prevent gemini-cli crashes (not a prompt issue)
2. Deduplicate textbook RAG chunks to save context tokens
3. Add IPA ban to research phase template
