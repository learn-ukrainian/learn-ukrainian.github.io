# Prompt Engineering Review: describing-things-adjectives (Post-Fix Rebuild)

**Track:** a1 | **Sequence:** 11
**Pipeline:** v5
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE, activities: NONE)
**Previous build:** Failed (dedup-exhausted, KeyError crash)

## Fix Effectiveness

| Fix # | Description | Effective? | Details |
|-------|-------------|------------|---------|
| 1 | Imperative ban examples in PEDAGOGICAL_CONSTRAINTS | YES | No banned imperatives in output content. Gemini respected the INSTEAD OF -> USE mapping completely. |
| 2 | Heading post-processing (H2 matching to outline) | PARTIAL | Fix 1 revealed MISSING_OUTLINE_SECTION for 2 sections -- Gemini used different H2 titles than the outline ("Презентація 2: М'яка група та Специфіка" vs "М'яка група та множина"). Post-processing could not fuzzy-match these. |
| 3 | Empty fix guard | NOT TESTED | No empty fix scenario occurred. |
| 4 | KeyError crash fix | YES | No KeyError crash. Pipeline completed all phases cleanly. |
| 5 | Section title matching improvements | PARTIAL | Gemini deviated from outline section titles in initial content (used "Презентація:" prefix and different subtitles). Validation caught this but it required a fix attempt to resolve. |

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Section title mismatch not prevented | MEDIUM | phase-2-prompt.md | The prompt says "Follow the content_outline" and "each section maps to an H2" but does not explicitly say "Use the EXACT H2 titles from the outline." Gemini used creative variations (e.g., "Презентація: Тверда група" instead of "Тверда група прикметників"; "Презентація 2: М'яка група та Специфіка" instead of "М'яка група та множина"). This caused MISSING_OUTLINE_SECTION errors requiring fix 1. |
| Immersion target contradicts verb-free constraint | LOW | placeholders.yaml | IMMERSION_RULE says "25-40% Ukrainian" but LEVEL_CONSTRAINTS ban all verbs. Gemini initially produced 13.7% Ukrainian immersion because achieving 25%+ with verb-free Ukrainian is genuinely difficult. Fix 1 had to expand Ukrainian content blocks with repetitive verb-free patterns to reach 25.1%. |
| Self-check answer format not specified | LOW | phase-2-prompt.md | The prompt did not specify that self-check answers need English translations. Validate-fix2 had to add English to 4 answer items. The template should include a note like "All Ukrainian in self-check answers must include English translations." |
| Word target overshoot massive | INFO | phase-2-prompt.md | Target 1200, output 2963 words (247% of target). The prompt says "approximately 1200 words" but Gemini wrote nearly 2.5x. Not harmful (passes audit), but indicates weak word budget enforcement. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No prior module content injected | LOW | M11 builds on M7 (Gender Code). Research references it but actual content from M7 is not provided. Gemini handled this adequately via the SEQUENCE CONSTRAINTS block. |
| No explicit heading match instruction | MEDIUM | Add to phase-2 content template: "CRITICAL: Your H2 headings MUST exactly match the `title` field from each content_outline section. Do not paraphrase, prefix, or modify section titles." |
| Self-check English requirement not in content template | LOW | Add to the Summary/Self-Check section guidance: "Every Ukrainian answer in self-check must include an English translation in parentheses." |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| MISSING_OUTLINE_SECTION (2 sections) | template_gap | Gemini used creative H2 titles ("Презентація 2: М'яка група та Специфіка") instead of outline titles ("М'яка група та множина"). The post-processing heading matcher could not fuzzy-match these. | Add explicit instruction: "Use EXACT H2 titles from content_outline. Do not add prefixes like 'Презентація:' or modify subtitle text." |
| Immersion 13.7% (target 25-40%) | conflicting_guidance | Verb-free constraint severely limits Ukrainian content volume. Gemini wrote English-heavy content because grammar explanations must be in English. Fix 1 added repetitive verb-free Ukrainian blocks to reach 25.1%. | Consider adjusting M11 immersion target to 20-35% for verb-free modules, OR provide more verb-free immersion pattern examples. |
| SELF_CHECK_NEEDS_ENGLISH (4 items) | template_gap | Self-check answer format was not specified to require English translations. | Add to self-check guidance in content template. |
| ROBOTIC_STRUCTURE (3x "what is...") | model_limitation | Gemini's default pattern for introducing concepts. Anti-robotic writing section exists but was insufficient to prevent this specific pattern. | Minor model tendency, not a template issue. Already addressed by varied sentence opener guidance. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|-----------|--------------|
| Validate | 2 | Fix 1: Missing sections (heading mismatch) + low immersion + robotic structure. Fix 2: Self-check missing English translations. | YES (heading mismatch) / PARTIALLY (immersion) / YES (self-check English) |

**Fix 1** was the heavy lift: it had to restore 2 missing sections (by matching H2 titles to outline), boost immersion from 13.7% to 25.1%, and fix robotic sentence structures. The response indicates success: "All outline sections restored, immersion target reached (25.1%), and robotic structures resolved."

**Fix 2** was lightweight: adding English translations to 4 self-check answers. Response: "SUCCESS".

Both fixes were clean -- no cascading issues or regressions. The fix loop was efficient (2 attempts, both successful).

## Suggested Template Fixes (priority ranked)

### P1: Exact heading match instruction (prevents fix loops)

**File:** Content template (phase-2-prompt or beginner content template)
**Where:** Section structure instructions

**Before:** "Follow the content_outline from {META_PATH} -- each section maps to an H2."

**After:** "Follow the content_outline from {META_PATH} -- each section maps to an H2. CRITICAL: Your H2 headings MUST use the EXACT `title` text from each content_outline section. Do not add prefixes (like 'Презентація:', 'Part 1:'), do not paraphrase, do not modify the bilingual title format. The audit matches H2 headings literally against the outline."

### P2: Self-check answer format guidance

**File:** Content template, summary section
**Add:** "Self-check answers: Every Ukrainian answer must include an English translation in parentheses, e.g., 'новий телефон (new phone)'."

### P3: Immersion target calibration for verb-free modules

**File:** `placeholders.yaml` generation logic (or `scripts/pipeline_v5.py`)
**Issue:** M1-M14 have VERB-FREE constraint which makes 25% Ukrainian immersion difficult. Consider:
- Adjusting target to 20-35% for verb-free modules, OR
- Adding more verb-free immersion examples in the pattern bank (the current bank has 9 patterns, but more variety would help), OR
- Accepting that 20-25% is the realistic floor for verb-free modules

## Comparison with Pre-Fix Build

| Dimension | Previous Build | Current Build |
|-----------|---------------|---------------|
| Pipeline completion | FAILED (dedup-exhausted) | PASSED |
| KeyError crash | YES (crashed during heading processing) | NO |
| Heading level issues | YES (caused KeyError) | NO (but heading TITLE mismatch required fix) |
| Content quality | N/A (never completed) | Good -- 2963 words, 4 callouts, 8 activities |
| Fix attempts | Exhausted all attempts | 2 of N attempts, both successful |
| Immersion | N/A | 25.1% (borderline but passing) |
| VESUM verification | N/A | 96.4% (133/138; 5 not found are fragments: "-ий", "-ій", "нов", "синий", "Хрещатик") |

## Summary

**Template health:** GOOD -- the v5 template fixes (imperative ban, KeyError crash, heading post-processing) all worked effectively. Two remaining gaps (exact heading match instruction, self-check English requirement) are minor and easily fixable.

**Comparison:** IMPROVED -- the previous build crashed and exhausted fix attempts. This build completed cleanly in 2 fix attempts with no regressions. The module passed all audit gates with strong numbers (2963/1200 words, 8 activities, 21 vocab items, 25.1% immersion).

**Remaining risk:** The immersion target of 25-40% is borderline achievable for verb-free modules. The module barely passed at 25.1% after fix 1 injected additional Ukrainian blocks. This could be a recurring issue for M1-M14 modules.
