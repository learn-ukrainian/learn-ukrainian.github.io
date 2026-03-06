# Prompt Engineering Review: body-and-health

**Track:** a1 | **Sequence:** M48
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE; activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Dative ban directly contradicts module content | CRITICAL | LEVEL_CONSTRAINTS | M48's core structure is "У мене болить..." and "Мені погано" -- both dative constructions. The level constraints say "Dative case FORBIDDEN (no мені, тобі...)". Fix2 flagged "голові", "вам" (3x) as dative violations. The research explicitly notes dative as required for this module. This is the same conflict as M40 and M47 but more severe -- dative IS the teaching objective. |
| Subordinate clause ban vs. "бо/тому що" teaching | HIGH | LEVEL_CONSTRAINTS | The meta outline explicitly includes teaching "бо" and "тому що" in the summary section. The level constraints ban "тому що, бо, щоб" categorically. Fix2 flagged 9 subordinate clause violations. The content correctly used these per the plan. |
| Imperative constraint wrong for M48 | MEDIUM | phase-2-prompt.md | The constraint says "Imperative forms NOT taught until M47". M48 is AFTER M47, so imperatives should be allowed. Research correctly notes "Since this is post-M47, imperative forms are permitted." But the template still injects the pre-M47 constraint text unchanged. |
| Activity item counts too low | MEDIUM | phase-C-prompt.md | Fix2 flagged 6 activities with too few items (fill-in x3, true-false, unjumble, quiz all under minimum). Same pattern as M47. |
| Textbook examples partially relevant | LOW | phase-2-prompt.md | Zaharijchuk p.21 mentions "Заболить живіт" -- somewhat relevant to body/health. Better than M40/M47 but still mostly Grade 1 letter drills. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No dative exemption for "У мене болить" pattern | CRITICAL -- module literally cannot be written without dative | Level constraints MUST exempt taught grammar. If a module's plan teaches dative patterns, the dative ban must be lifted for that module. |
| Post-M47 imperative status not reflected | MEDIUM | Template should detect module number and adjust constraint: "Imperative forms ARE available (M47+ module)" |
| Metalanguage terms "однина, множина" flagged | LOW | These are basic grammar terms used in tables. Add to allowed metalanguage list for M30+ |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| 3x dative "вам" flagged | conflicting_guidance | Module teaches dative patterns but constraints ban dative | Exempt module-taught grammar from constraint bans |
| 9 subordinate clause violations | conflicting_guidance | Module teaches "бо/тому що" per plan but constraints ban them | Same as above -- plan-taught grammar exemption |
| 6 activity item count violations | template_gap | Same as M47 -- minimums not prominent enough | Inline minimums in schema examples |
| Robotic "у ме́не..." x3 | template_gap | Core teaching pattern "У мене болить X" naturally repeats. Anti-robotic detector flags pedagogical repetition. | Exempt Ukrainian example blocks from robotic detection |
| Density gate FAIL (6 < 6) | model_limitation | Borderline density, fixed by adding content | Minor -- self-corrected |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 2 | Fix1: generic audit failure (no details). Fix2: density, pedagogy (23 violations: 3 dative, 9 subordinate clause, 6 activity items, metalanguage, robotic). | YES -- plan-aware constraint relaxation would eliminate ~18 of 23 violations. |

## Suggested Template Fixes

### Fix 1: Plan-aware constraint relaxation (Priority: CRITICAL)
**Before:** Same LEVEL_CONSTRAINTS for all A1 modules, banning dative/instrumental/subordinate regardless of teaching objectives
**After:** Pipeline reads plan objectives and vocabulary_hints. If plan teaches dative patterns (e.g., "У мене болить"), automatically remove dative from banned list for that module. Same for subordinate clauses if "бо/тому що" in plan.
**Applies to:** All modules where plan contradicts level constraints

### Fix 2: Dynamic imperative constraint based on module number (Priority: HIGH)
**Before:** Static text "Imperative forms NOT taught until M47" injected for ALL modules including M48+
**After:** For M47: "This module INTRODUCES imperatives." For M48+: "Imperative forms ARE available (taught in M47)."
**Applies to:** All A1 modules M47+

### Fix 3: Exempt pedagogical repetition from robotic detection (Priority: MEDIUM)
**Before:** "У мене болить..." x3 flagged as robotic
**After:** Repetition inside clearly pedagogical blocks (vocabulary tables, grammar pattern demonstrations, drill examples) exempt from robotic structure detector
**Applies to:** All grammar-focused modules

## Summary

**Template health:** BROKEN
**Top 3 fixes by leverage:**
1. Plan-aware constraint relaxation -- the single highest-impact fix across the entire pipeline. The level constraints are designed for early A1 modules but applied uniformly, creating impossible contradictions when later modules teach the very grammar that's banned.
2. Dynamic imperative constraint text based on module number
3. Exempt pedagogical repetition patterns from robotic structure detection
