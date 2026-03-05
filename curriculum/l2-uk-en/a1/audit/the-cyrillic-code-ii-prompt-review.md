# Prompt Engineering Review: the-cyrillic-code-ii

**Track:** a1 | **Sequence:** 2
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 1 (content phase only; activities friction not captured)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| H3_WORD_RANGE placeholder in writing tone instruction | MEDIUM | placeholders.yaml | `WRITING_TONE_INSTRUCTION` references `{H3_WORD_RANGE}` but this is a nested placeholder -- Gemini sees the literal `{H3_WORD_RANGE}` string. Actual value (30-50) IS defined in placeholders.yaml separately, so it depends on whether the template engine resolves nested references. |
| Conflicting word range guidance | MEDIUM | phase-2-prompt.md | The writing tone says "Every H3 gets 30-50 words" but the section word budgets say 350 words for a section with 3-4 H3 blocks, implying ~87-117 words per H3. These are contradictory. |
| Decodable vocabulary listed twice | LOW | phase-2-prompt.md | The decodable vocabulary constraint block appears twice in the prompt (lines 42-64 in the rendered prompt): once under "Module Constraints" and once under "DECODABLE VOCABULARY". Redundancy wastes context window but does not cause errors. |
| Tier guidance missing | MEDIUM | placeholders.yaml | `TIER_GUIDANCE` is set to `'(Tier guidance file not found: tier-1-beginner.md)'`. The review prompt (D1_OUTPUT_FORMAT) was injected but the tier file was not resolved. This affects the review phase, not the content build. |
| Textbook examples are off-topic | LOW | phase-2-prompt.md | Injected textbook examples (zaharijchuk p.96, p.113, bolshakova p.24, p.79) cover letters Д, Г, Ґ, and general vowel/consonant theory -- none are relevant to M2's specific letters (К, И, І, Р, В, Т, Е). Better textbook selection would help Gemini match real primer style. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No predecessor content injected | LOW for M2 (only builds on M1 letters) | For M3+, inject the vocabulary table from the preceding module so Gemini can reference what the learner already knows |
| Discovery found no videos | LOW | Discovery phase returned `warning: No videos found across channels` but the plan already provides per-letter video URLs, which were correctly injected via PRONUNCIATION_VIDEOS. The discovery phase added no value here. |
| No previous module's engagement patterns | LOW | Gemini had no reference for what callout types M1 used. Minor issue -- the prompt specifies callout types generically. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| Content friction: NONE reported | N/A | Gemini reported no friction for content writing. Self-correction only involved typography (straight quotes to angular quotes) and word count padding. | N/A |
| Validate fix 1: LOW_ENGAGEMENT (0 engagement boxes) | **template_gap** | Gemini wrote content with 0 callout boxes despite the prompt saying "4+ across sections, at least 3 different types". The instruction exists but is buried at line 207 in the prompt, well below the decodable vocabulary constraints which occupy Gemini's attention. After fix, the module ended with 4 engagement boxes. | Move engagement box requirement HIGHER in the prompt, ideally into the section word budgets table or as a hard constraint alongside word count. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 2 | LOW_ENGAGEMENT -- 0 callout boxes in initial build | YES -- the engagement requirement is present but buried. Moving it to the "Audit Gates" section (line 277) would help, or adding a per-section callout requirement to the section word budgets table. |

## Suggested Template Fixes

### Fix 1: Elevate engagement callout requirement (Priority: HIGH)
**Prevents:** LOW_ENGAGEMENT validation failures across all beginner modules
**Scope:** All a1 modules (M1-M31)
**Template file:** beginner content template (phase-2-prompt generator)

```diff
 ### Section Word Budgets

 | Section | Target |
 |---------|--------|
-| Вступ — Introduction | 150 |
+| Вступ — Introduction | 150 | 1 callout |
-| Голосні — The Vowels И, І, Е | 350 |
+| Голосні — The Vowels И, І, Е | 350 | 1-2 callouts |
-| Приголосні — The Consonants К, Р, В, Т | 350 |
+| Приголосні — The Consonants К, Р, В, Т | 350 | 1-2 callouts |
-| Перші слова — First Real Words | 250 |
+| Перші слова — First Real Words | 250 | 1 callout |
-| Підсумок — Summary | 100 |
+| Підсумок — Summary | 100 | 0 |
```

### Fix 2: Resolve H3 word range contradiction (Priority: MEDIUM)
**Prevents:** Confusion about section depth -- Gemini may write too-thin H3 blocks
**Scope:** All beginner letter modules (M1-M4)
**Template file:** placeholders.yaml / WRITING_TONE_INSTRUCTION

```diff
-Be concise — students know nothing yet. Short, clear explanations.
-Every H3 gets {H3_WORD_RANGE} words. The activities do the teaching, not the prose.
+Be concise — students know nothing yet. Short, clear explanations.
+Each H3 subsection within a section gets 30-80 words depending on content density.
+The activities do the teaching, not the prose.
```

### Fix 3: Deduplicate decodable vocabulary block (Priority: LOW)
**Prevents:** Wasted context window tokens
**Scope:** All Cyrillic modules (M1-M4)
**Template file:** phase-2-prompt template

The "Module Constraints" block and the "DECODABLE VOCABULARY" block both contain the same letter set and available words list. Merge them into a single block.

### Fix 4: Select relevant textbook examples (Priority: LOW)
**Prevents:** Off-topic examples that don't help Gemini calibrate difficulty
**Scope:** All beginner modules
**Template file:** textbook example selector in build pipeline

Currently textbook examples are injected without filtering for the specific letters being taught. The examples for M2 should show primer pages introducing К, И, І, Р, В, Т, or Е -- not Д or general phonics theory.

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. **Elevate engagement callout requirement into section budgets** -- caused the only validation fix loop; affects all beginner modules
2. **Resolve H3 word range vs section budget contradiction** -- could cause under-depth H3 blocks in future builds
3. **Deduplicate decodable vocabulary constraints** -- saves ~200 tokens of context per build, reduces cognitive load on Gemini
