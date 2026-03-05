# Prompt Engineering Review: greetings-and-politeness

**Track:** a1 | **Sequence:** 8
**Pipeline:** v4
**Validate attempts:** 3
**Friction reports:** 2 (content: DOC_CONFLICT, activities: NONE)

## Prompt Clarity
| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Latin transliteration conflict | MEDIUM | phase-2-prompt.md vs quick-ref/A1.md | Gemini's friction report flagged that A1.md required Latin transliteration for M01-M10, but the content prompt bans it globally. Gemini correctly followed the prompt, but the conflicting guidance creates cognitive load. |
| Imperative ban not explicit | HIGH | phase-2-prompt.md | Same issue as M7: GRAMMAR STATUS says "FORBIDDEN: imperatives" without listing concrete examples. Gemini used "Скажіть" in a dialogue (line 132), caught at validate-fix2. |
| Greetings module constraint mismatch | LOW | phase-2-prompt.md | The M7 exception about adjective agreement examples is included in M8's constraints, but M8 doesn't need it. Minor noise. |
| Plan has "Діалоги" section not in meta | MEDIUM | phase-A-output.md | Plan has 5 sections (including "Діалоги"), but meta outline only has 5 sections with Introductions absorbing dialogues. Content followed meta, not plan -- but audit matched on content sections. |

## Context Gaps
| Missing Context | Impact | Fix |
|----------------|--------|-----|
| Tier guidance file not found | Same as M7: "(Tier guidance file not found: tier-1-beginner.md)" | Fix path resolution |
| No video discoveries | Acceptable for this topic -- greetings modules don't benefit much from video | None needed |
| Quick-ref A1.md outdated transliteration rule | Creates friction/confusion for Gemini | Update A1.md to remove M01-M10 transliteration requirement |

## Friction Root Causes
| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| Latin transliteration conflict (content friction) | conflicting_guidance | A1.md says transliterate, prompt says don't. Gemini correctly prioritized prompt but had to self-correct. | Update A1.md to remove outdated rule |
| Audit failure with 0 issues (fix1) | context_gap | validate-fix1 showed "Fix 0 issue(s)" but audit still failed -- likely a transient audit error or section mismatch | Investigate audit false-fail scenario |
| Imperative "Скажіть" in dialogue (fix2) | template_gap | Same root cause as M7 -- no concrete imperative examples in ban | Add imperative ban list (same fix as M7) |
| Immersion at 15.0% floor (fix3) | template_gap | 15.0% barely missed the floor, needed padding to reach 15%+ | Add immersion floor enforcement with concrete guidance |

## Fix Loop Analysis
| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 3 | Fix1: unclear audit failure (0 identified issues). Fix2: imperative "Скажіть" in dialogue. Fix3: immersion 15.0% at floor boundary. | PARTIALLY -- Fix2 preventable with imperative ban examples. Fix3 preventable with immersion floor guidance. Fix1 may be an audit transient. |

## Suggested Template Fixes

### Fix 1: Update A1.md Quick-Ref (Priority: MEDIUM)
**Prevents:** DOC_CONFLICT friction for all beginner modules
**Scope:** All A1 M1-M10 modules
**Template file:** claude_extensions/quick-ref/A1.md

```diff
- M01-M10: Require full Latin transliteration (e.g., слово (slovo))
+ M01-M10: Latin transliteration BANNED (aligned with global ban)
```

### Fix 2: Concrete Imperative Ban (Priority: HIGH)
**Prevents:** Imperative usage in dialogues and instructions
**Scope:** All A1 M1-M46 modules
**Template file:** Content prompt GRAMMAR STATUS section
(Same fix as M7 Fix 1 -- identical template change)

### Fix 3: Immersion Floor Concrete Guidance (Priority: MEDIUM)
**Prevents:** Borderline immersion failures requiring extra fix rounds
**Scope:** All beginner modules
**Template file:** Content prompt Immersion section

```diff
- TARGET: 15-35% Ukrainian, 65-85% English.
+ TARGET: 15-35% Ukrainian, 65-85% English. MINIMUM FLOOR: 15%. To reach the floor: include Ukrainian section headings, vocabulary tables with Ukrainian entries, and inline Ukrainian phrases with English translations.
```

## Summary

**Template health:** NEEDS WORK (but slightly better than M7 -- fewer fix loops)
**Top 3 fixes by leverage:**
1. Concrete imperative ban list -- same fix as M7, prevents dialogue-embedded imperatives
2. Update A1.md to remove outdated transliteration rule -- eliminates DOC_CONFLICT friction
3. Add immersion floor enforcement guidance -- prevents borderline immersion failures
