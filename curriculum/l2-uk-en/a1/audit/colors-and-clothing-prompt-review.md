# Prompt Engineering Review: colors-and-clothing

**Track:** a1 | **Sequence:** 12
**Pipeline:** v4
**Validate attempts:** 6 (exhausted, then escalation)
**Friction reports:** 2

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Verb conjugation constraint contradiction | HIGH | phase-2-prompt.md + placeholders.yaml | Constraints say "FORBIDDEN: verb conjugation (starts M15)" but the plan's content_outline explicitly includes "носити" conjugation (Я ношу), and the research output teaches Accusative forms with носити. The prompt embeds both the plan (which requires verb use) and the constraint (which forbids it). |
| Dative case conflict with plan phrases | HIGH | placeholders.yaml | LEVEL_CONSTRAINTS lists "Dative case FORBIDDEN" but plan content_outline includes "Мені подобається цей колір" as a required teaching point. Irreconcilable conflict. |
| Padding-driven prose quality | HIGH | phase-2-prompt.md | Friction report reveals Gemini "padded sections with highly descriptive adjectives in English" to meet word count. The EXPANSION_METHOD instruction says "Don't just write more -- write deeper" but provides no concrete technique for A1 where content scope is narrow. Result: absurdly verbose English ("beautifully and happily", "remarkably helpful phrases"). |
| Imperative ban not in writing instructions | HIGH | phase-2-prompt.md | The constraint mentions imperatives are forbidden (M47), but this is buried in PEDAGOGICAL_CONSTRAINTS. The writing instructions, immersion rule, and example sections do not repeat this. Imperatives (Почнімо, Вивчімо, Практикуймо) survived 6 fix rounds. |
| Textbook examples irrelevant | MEDIUM | phase-2-prompt.md | Grade 1 primer examples (letters М, Ш, И) are completely irrelevant for M12 (colors/clothing). Wastes ~150 tokens. |
| REQUIRED_TYPES empty | LOW | placeholders.yaml | `REQUIRED_TYPES: ''` -- no required activity types specified, yet meta.yaml requires fill-in and match-up. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No explicit guidance on how nosyty+Accusative interacts with verb ban | 6 validate fix loops: Gemini kept reintroducing conjugated forms because the plan demanded them | Add constraint-override note: "носити taught as lexical chunk; use only Я ношу as memorized phrase" |
| No word-count expansion strategy for A1 | Gemini inflated English with meaningless adverbs to hit 1200 | Add concrete A1 expansion techniques: more Ukrainian examples, comparison tables, cultural callouts |
| Irreconcilable plan-constraint conflict for dative | "Мені подобається" silently dropped | Either add dative exception for memorized chunks or revise plan |
| Fix prompts 3/5/6 identical | 3 wasted fix rounds sending identical unfixable prompts | Pipeline deduplication needed |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| Verbose English padding | template_gap | No A1-specific expansion strategy; "write deeper" too vague | Add concrete A1 expansion techniques in EXPANSION_METHOD |
| 6 validate fix loops for verbs | conflicting_guidance | Plan requires nosyty conjugation, constraints forbid ALL verbs pre-M15 | Resolve plan-vs-constraint conflict; add memorized-chunk exception list |
| Imperatives survived all rounds | context_gap | Ban buried in constraints, not in writing/immersion sections | Surface imperative ban in immersion rule |
| Russianisms (красивий/красива) | model_limitation | Despite explicit ban list, Gemini produced красивий | Strengthen pre-submission checklist |
| Duplicate fix prompts | template_gap | Pipeline sent identical fix prompts 3 times | Add deduplication: if fix prompt matches previous, escalate immediately |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 6 + escalation | Conjugated verbs, imperatives, dative phrases -- each fix removed some but introduced others or created cascading section-under-target failures | YES -- resolve plan/constraint conflicts upstream; verb-free pattern bank; imperative ban in writing instructions |

## Suggested Template Fixes

### Fix 1: Resolve Plan-Constraint Conflicts (Priority: HIGH)
Add exception mechanism for "memorized chunks" (Я ношу, Мені подобається) vs. forbidden grammar categories. Pre-validate plan vocabulary against constraints before prompt injection.

### Fix 2: A1 Expansion Strategy (Priority: HIGH)
Replace vague "write deeper" with: "(1) Add more Ukrainian example phrases with translations (2) Add comparison tables (correct vs incorrect) (3) Add callouts with common mistakes (4) Add cultural context paragraphs. Do NOT pad English prose."

### Fix 3: Imperative Ban in Writing Instructions (Priority: HIGH)
Add to immersion/writing section: "CRITICAL: Do NOT use Ukrainian imperative forms (Почнімо, Давайте, Слухайте) -- FORBIDDEN until M47. Use English instructions or noun phrases instead."

### Fix 4: Fix Prompt Deduplication (Priority: MEDIUM)
Add pipeline logic: if fix prompt content matches previous round, escalate immediately.

### Fix 5: Filter Textbook Examples by Relevance (Priority: LOW)
Skip textbook example injection when relevance score < 0.3 or module is post-alphabet (M7+).

## Summary

**Template health:** BROKEN
**Top 3 fixes by leverage:**
1. Resolve plan-constraint conflicts for verb/dative (prevents 6+ fix loops)
2. A1-specific expansion strategy (prevents verbose English padding)
3. Surface imperative ban in writing instructions (prevents recurring violations)
