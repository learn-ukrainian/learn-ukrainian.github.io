# Decolonization Contrast-Pair Rationale

**Status:** Recorded 2026-05-28 as rationale for the module-agnostic writer rule.

**Related:** `docs/decisions/pending/2026-05-28-wiki-driven-prompt-generator.md`, issue #2383, PR #2358.

## Context

The writer prompt requires A1-A2 vocabulary modules in L1-Russian-substitutable domains to include at least one explicit bad-form contrast pair with `<!-- bad -->...<!-- /bad -->` markers. The rule belongs in the universal prompt because it is a general pedagogical and review obligation. The empirical build history that motivated the rule does not belong in the prompt template because it contaminates future modules with one module's vocabulary, source shape, and review history.

## Empirical Grounding

The immediate trigger was m20 round #12 with `codex-tools` on build `a1-my-morning-20260526-204640`. The module used Ukrainian-canonical vocabulary throughout and included one decolonization stance line, but it emitted zero bad-form markers. Under the recalibrated decolonization rubric from PR #2358, the reviewer scored the module 8.7: Ukrainian-canonical vocabulary and grammar-on-Ukrainian-terms were present, but criterion (b), an explicit bad-form contrast pair, was absent. That was 0.3 below the A1 decolonization floor of 9.0.

Follow-up review identified the missing contrast-pair shape as the practical gap: for an A1 routine vocabulary domain, one concrete marked pair was enough to make the decolonization work visible without forcing extra political rhetoric into a grammar lesson.

## Decision

Keep the universal rule body in `scripts/build/phases/linear-write.md`: eligible A1-A2 vocabulary modules must include at least one topic-appropriate contrast pair using the bad-form marker syntax. The actual pair must come from the module's wiki, plan, or cited RAG content.

Keep the empirical m20/PR #2358 history here in the decision journal only. Prompt templates must not name m20, its build IDs, its textbook chunk IDs, or its morning-routine vocabulary as canonical examples.
