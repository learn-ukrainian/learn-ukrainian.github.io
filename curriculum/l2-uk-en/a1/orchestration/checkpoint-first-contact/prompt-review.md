# Prompt Engineering Review: checkpoint-first-contact

**Track:** a1 | **Sequence:** 14
**Pipeline:** v4
**Validate attempts:** 1
**Friction reports:** 2 (phase-2: CONTRADICTION IN INSTRUCTIONS, phase-C: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Plan objective contradicts sequence constraints | CRITICAL | phase-2-prompt.md | Plan objective #3: "Conjugate First Conjugation verbs correctly" directly contradicts "FORBIDDEN: verb conjugation (starts M15)." Gemini identified this in friction report and correctly prioritized constraints. |
| Vocabulary hints include forbidden verbs | HIGH | placeholders.yaml | Required vocabulary includes 8+ verbs (читати, писати, говорити, знати, розуміти, питати, відповідати, перевіряти) that cannot appear in content per constraints. Caused 50% vocab-not-in-content audit warning. |
| Plan section titles vs meta section titles | MEDIUM | phase-2-prompt.md | Plan: "Навичка 2: Дієслова та Питання" (Verbs & Questions). Meta: "Прикметники, Множина та Питання" (Adjectives, Plurals & Questions). Content writer had to reconcile two conflicting section definitions. |
| Word target ambiguity | LOW | placeholders.yaml | WORD_TARGET: 1200 but config.py A1-checkpoint = 1000. Plan overrides config, but creates confusion. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No explicit flag that plan is stale/contradictory | Gemini must self-diagnose at generation time, wasting tokens | Pipeline should pre-validate plan objectives against constraints and inject warnings |
| No checkpoint-specific template guidance | Uses generic beginner template; no TTT (Test-Teach-Test) guidance from the plan | Add checkpoint template variant with review/assessment focus |
| Vocabulary not filtered for constraint compatibility | 50% vocab disconnect (verbs in vocab YAML but unused in content) | Filter vocabulary hints against constraints before injection |
| Validate fix prompt lacks specifics | Fix prompt says "AUDIT FAILED" with no details about what failed | Include specific gate failures in fix prompts |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| Plan-constraint contradiction (verbs) | conflicting_guidance | Plan written before constraints finalized; never updated | Pre-validate plan against constraints |
| Vocabulary disconnect (50%) | conflicting_guidance | Required vocab includes 8 forbidden verbs | Filter vocab hints against constraints |
| Low immersion (14.8% vs 25-40%) | template_gap | Checkpoint reviews prior material; 25-40% unrealistic | Add checkpoint immersion exception |
| True-false activity error (И/Н confusion) | model_limitation | Item confuses which letter looks like H | Not easily preventable via template |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 1 | Generic audit failure, quickly resolved | Partially -- better initial prompt would produce passing first draft |

## Suggested Template Fixes

### Fix 1: Pre-Validate Plan Objectives Against Constraints (Priority: HIGH)
Before prompt injection, check each plan objective against sequence constraints. If objective references forbidden grammar, inject explicit warning and skip instruction.

### Fix 2: Filter Vocabulary Hints Against Constraints (Priority: HIGH)
Automatically flag/filter vocabulary items requiring forbidden grammar (e.g., verbs before M15) before injection into phase-C prompt.

### Fix 3: Checkpoint Template Variant (Priority: MEDIUM)
Add checkpoint-specific guidance: "Checkpoint modules review and assess prior material. Immersion target: 10-25%. Focus: self-assessment, not new teaching."

### Fix 4: Include Specific Audit Failures in Fix Prompts (Priority: MEDIUM)
Replace generic "AUDIT FAILED" with specific gate details and log excerpts.

## Summary

**Template health:** GOOD (issues are upstream plan defects, not template problems)
**Top 3 fixes by leverage:**
1. Pre-validate plan objectives against sequence constraints (eliminates root cause)
2. Filter vocabulary hints against constraints (prevents vocab disconnect)
3. Add checkpoint-specific template guidance (prevents immersion false alarms)
