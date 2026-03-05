# Prompt Engineering Review: the-cyrillic-code-iv

**Track:** a1 | **Sequence:** 4
**Pipeline:** v4
**Validate attempts:** 6 (escalation to Claude)
**Friction reports:** 2 (both NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| No issue | — | phase-2-prompt.md | Engagement callouts correctly stated as "4+ MANDATORY". Template fix from M3 review is working. |
| Word overshoot | LOW | phase-2-prompt.md | 1952 words for 1200 target (162%). Not a problem per se, but M4 covers 10 letters + digraphs + apostrophe — the plan's word budget may be too low for this scope. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| None critical | — | Placeholders well-populated, pronunciation videos injected, constraints clear |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|--------------|
| 6 validate attempts | **tooling bug** | `_CUMULATIVE_CHARSETS[4]` was missing Ц, Ь, Ґ — the exact letters M4 teaches. Our new `UNTRANSLATED_NON_DECODABLE` check flagged every use of these letters as "not yet learned", generating false positives that Gemini tried and failed to fix. | **FIXED** — M4 charset updated to full alphabet |
| Fix prompts 4-6 had 0 issues | **tooling bug** | After fix3, the deterministic issues shifted but the fix prompt builder showed "0 issues" while audit still failed. Gemini received "fix 0 issues" — impossible to act on. 3 wasted iterations. | Fix prompt builder should always explain WHY audit failed, even when no deterministic issues remain |
| Friction reports say NONE | **model limitation** | Gemini doesn't self-diagnose issues that later cause validation failures. Consistent across M2-M4. | Not actionable — friction is self-reported |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 6 | False positive UNTRANSLATED_NON_DECODABLE from wrong M4 charset + empty fix prompts 4-6 | **YES** — charset bug now fixed, would be 0-1 attempts |

**Detailed fix loop:**
1. Fix1: 4 false positive issues (Ц, Ґ, Ь non-decodable + VESUM proper nouns)
2. Fix2: Ґ still "failing" (Gemini partially fixed but charset still wrong)
3. Fix3: Ґ still "failing" (same false positive)
4. Fix4-6: "0 issues" in prompt but audit FAIL — Gemini can't fix what it can't see

**Cost:** ~30 minutes of Gemini calls + 6 audit runs. All caused by one wrong charset entry.

## Suggested Template Fixes

### Fix 1: M4 charset already fixed (Priority: CRITICAL — DONE)
**Prevents:** 6-attempt fix loops on M4 builds
**Scope:** A1 M4 only
**File:** `scripts/audit/checks/content_quality_pipeline.py`

```diff
- 4: "АаОоУу...ЩщФф",  # missing Ц, Ь, Ґ
+ 4: "АаБб...ЩщЬьЮюЯя",  # M4 completes the alphabet
```

### Fix 2: Fix prompt should never show "0 issues" while audit fails (Priority: HIGH)
**Prevents:** Empty fix prompts that waste iterations
**Scope:** All modules
**File:** `scripts/build_module.py` (fix prompt builder)

When the fix prompt has 0 deterministic issues but audit still fails, include the raw audit output so Gemini can see the actual gate failures.

### Fix 3: VESUM proper noun allowlist (Priority: LOW)
**Prevents:** False VESUM failures on common Ukrainian proper nouns
**Scope:** All modules

VESUM not found: ДЖ, ДЗ, Львів, Тарас, Шевченко, Європа — all legitimate. Digraphs and major proper nouns should be allowlisted.

## Summary

**Template health:** GOOD (template itself is fine — the problem was a tooling charset bug)
**Top 3 fixes by leverage:**
1. **M4 charset fix** (DONE) — prevents the entire 6-attempt loop
2. **Non-empty fix prompts** — when audit fails, always explain why
3. **VESUM proper noun handling** — reduce noise in verification
