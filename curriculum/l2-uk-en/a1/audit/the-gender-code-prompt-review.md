# Prompt Engineering Review: the-gender-code

**Track:** a1 | **Sequence:** 7
**Pipeline:** v4
**Validate attempts:** 4
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity
| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Contradictory section headings | HIGH | phase-2-prompt.md vs phase-A-output.md | The phase-A research generated an alternate content_outline with different section names (The Three Pillars, The Ending is the Key, etc.) that diverged from the plan's section names (Презентація правил, Практичні вправи, etc.). Gemini initially followed the meta outline, then fix loops forced realignment to plan sections. |
| H3_WORD_RANGE misleading | MEDIUM | placeholders.yaml | H3_WORD_RANGE is set to "40-60" but each H3 subsection in the final output is 100-300 words. The instruction "Every H3 gets 40-60 words" is unrealistic for grammar modules and was effectively ignored. |
| Imperative ban not explicit enough | HIGH | phase-2-prompt.md | The GRAMMAR STATUS says "FORBIDDEN: verb conjugation, imperatives" but doesn't list concrete Ukrainian imperative forms to avoid. Gemini used Дивіться, Спробуйте, Слухайте, Зверніть -- all caught only at validate-fix3 (attempt 3 of 4). |
| Conjugated verb ban too abstract | MEDIUM | phase-2-prompt.md | "FORBIDDEN: verb conjugation" doesn't illustrate what conjugated forms look like. Gemini used "використовуємо" and "мають" -- both caught in validate-fix3 but preventable with examples. |
| Research recommends IPA | LOW | phase-A-output.md | Research notes say "Only show IPA for the first occurrence" despite IPA being banned globally. Contradicts the content prompt. |

## Context Gaps
| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No concrete imperative examples in ban | Caused 4/6 issues in validate-fix3 | Add "BANNED IMPERATIVES" box with examples: Дивіться, Слухайте, Спробуйте, Зверніть, Подивіться |
| Tier guidance file not found | TIER_GUIDANCE placeholder shows "(Tier guidance file not found: tier-1-beginner.md)" -- reviewer lacks rubric context | Fix path resolution in placeholder generation |
| Research recommends banned practice (IPA) | Could confuse Gemini if it follows research over prompt | Add IPA ban reminder to research template boundaries |

## Friction Root Causes
| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| 0 engagement boxes (fix1-2) | template_gap | Gemini's initial output had zero callout boxes despite "3+ MANDATORY" being in the prompt. Instruction was buried in the middle of the Writing Instructions section. | Move engagement gate to top-level critical instruction |
| 4 missing plan sections (fix1-2) | context_gap | Meta outline from phase-A used different section names than the plan. Gemini followed meta outline but audit checks against plan sections. | Enforce plan section name alignment in phase-A template |
| 4 imperative verbs (fix3) | template_gap | No concrete examples of banned imperatives in prompt | Add imperative ban with specific Ukrainian forms listed |
| 2 conjugated verbs (fix3) | template_gap | "verb conjugation forbidden" is too abstract for a content-writing LLM | Add "No Ukrainian verbs in present/past tense" with examples |
| Low immersion 13.9% (fix4) | template_gap | Gemini defaulted too heavily to English; no concrete guidance on how to reach 15% floor | Add minimum-immersion enforcement examples |

## Fix Loop Analysis
| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 4 | Fix1-2: engagement (0 boxes) + section name mismatch (4 sections). Fix3: imperatives (4) + conjugation (2). Fix4: immersion below floor (13.9% vs 15%). | YES -- all 4 rounds were preventable. Engagement instruction needs elevation. Section names need plan-to-meta alignment enforcement. Imperatives need concrete ban list. |

## Suggested Template Fixes

### Fix 1: Add Concrete Imperative Ban (Priority: HIGH)
**Prevents:** Imperative verb usage in early A1 modules (4 issues in this build)
**Scope:** All A1 M1-M46 modules
**Template file:** Content prompt GRAMMAR STATUS section

```diff
- FORBIDDEN: verb conjugation, imperatives, adjective agreement, plurals
+ FORBIDDEN: verb conjugation, imperatives, adjective agreement, plurals
+   BANNED IMPERATIVES (common ones Gemini uses): Дивіться, Слухайте, Спробуйте, Зверніть, Подивіться, Запам'ятайте
+   Always use English: "Look at...", "Listen!", "Try it!", "Notice!", "Remember!"
+   BANNED CONJUGATIONS: використовуємо, мають, бачимо, знаємо, вивчаємо
+   Always use English: "We use...", "They have...", "We see..."
```

### Fix 2: Elevate Engagement Requirement (Priority: HIGH)
**Prevents:** Zero-engagement first drafts requiring fix loops (2 issues in this build)
**Scope:** All beginner modules
**Template file:** Content prompt top-level instructions

```diff
+ > **CRITICAL GATE**: Content MUST contain 3+ callout boxes (> [!tip], > [!warning], > [!culture], etc.) spread across sections. Zero boxes = immediate FAIL.
```

### Fix 3: Enforce Plan Section Name Alignment (Priority: MEDIUM)
**Prevents:** Section name mismatch between plan and generated content
**Scope:** All modules
**Template file:** phase-A-prompt.md

```diff
+ **CRITICAL**: Section titles in your content_outline MUST exactly match the plan's content_outline section names. Do NOT rename sections.
```

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Add imperative/conjugation ban with concrete Ukrainian examples -- prevents 6 of 8 validate issues, applies to all A1 modules
2. Elevate engagement requirement to critical first-line instruction -- prevents 2 of 8 validate issues, applies to all beginner modules
3. Enforce plan-to-meta section name alignment -- prevents structural mismatch fix loops across all modules
