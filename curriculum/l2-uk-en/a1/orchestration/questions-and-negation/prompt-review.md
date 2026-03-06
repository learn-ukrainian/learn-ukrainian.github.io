# Prompt Engineering Review: questions-and-negation

**Track:** a1 | **Sequence:** 18
**Pipeline:** v4
**Validate attempts:** 5
**Friction reports:** 2 (both NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Section title mismatch plan vs content | HIGH | validate-fix1-prompt.md | Fix1+Fix2 both report "Missing 5 plan sections" but the content has sections with different titles. Same fuzzy matching issue as M16. All 5 "missing" sections actually exist with slightly different H2 headings. |
| Imperative ban generates recurring violations | HIGH | validate-fix4/5-prompt.md | Imperatives (Порівняйте, Уявіть, Кажіть, використовуйте) survived 3 fix rounds (fix3, fix4, fix5). Each fix replaced some imperatives but the model introduced new ones in replacement text. |
| Low immersion cascade | HIGH | validate-fix3-prompt.md | Initial content had 9.2% immersion (target 25-40%). Fix3 requested +5-8% improvement but this was insufficient. The scope warning correctly noted "16% gap is too large for a fix pass" but the fix was attempted anyway. |
| Fix prompt rule contradiction | MEDIUM | validate-fix1-prompt.md | Fix rule says "Fix ONLY the issues listed -- do not rewrite working content" AND "Do NOT add or remove sections" but the issue IS missing sections, which requires adding content. Self-contradictory instructions. |
| Vocabulary disconnect | MEDIUM | validate-fix3-prompt.md | Only 7/20 vocabulary words appear in content+activities. Missing: де, звідки, знати, коли, куди, не, ні, робити, хто, чи. Many of these ARE question/negation words that should naturally appear in the content. |
| Quiz prompt length violations | LOW | validate-fix3-prompt.md | Quiz questions too long (19-20 words vs 5-10 target). Minor formatting issue. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Section title matching too strict | 2 wasted fix rounds on "missing" sections that existed with different titles | Fuzzy title matching (same fix as M16) |
| No imperative replacement patterns | Model kept introducing new imperatives when fixing old ones | Provide explicit imperative-free replacement patterns: "Порівняйте:" to "Comparison:" / "Here is a comparison:" |
| Low immersion gap too large for fix pass | Fix3 attempted 16% gap in a patch pass -- predictably insufficient | If immersion gap > 10%, restart content phase instead of patching |
| Fix rule self-contradiction for missing sections | Model confused about whether to add sections or only fix listed issues | Separate "structural fix" from "content fix" instructions |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| 5 validate rounds | conflicting_guidance + template_gap | Fix rounds 1-2: section title mismatch. Round 3: immersion + vocab + quiz length. Round 4: new imperatives introduced. Round 5: more new imperatives. | Fuzzy matching, imperative replacement patterns, immersion restart threshold |
| Section title mismatch (rounds 1-2) | schema_mismatch | Plan titles differ from content H2 headings | Normalize and fuzzy-match section titles |
| Imperatives recurring (rounds 3-5) | model_limitation + template_gap | Each fix introduces new imperatives in replacement text because model uses Ukrainian instructional phrases naturally | Provide explicit imperative-free replacement bank |
| Low immersion (round 3) | template_gap | 9.2% vs 25% minimum, too large to patch | Content restart threshold for immersion gaps > 10% |
| Vocabulary disconnect | template_gap | Question/negation words not woven into content despite being module vocabulary | Post-content vocabulary check before activities phase |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 5 | Rounds 1-2: section title fuzzy matching. Round 3: immersion gap too large for patch, vocab disconnect, quiz length. Rounds 4-5: imperative whack-a-mole (fix one, introduce another) | YES for rounds 1-2 (fuzzy matching). PARTIALLY for round 3 (immersion restart). YES for rounds 4-5 (imperative replacement bank). |

## Suggested Template Fixes

### Fix 1: Section Title Fuzzy Matching (Priority: HIGH)
Same as M16. Normalize plan section titles and content H2 headings before comparison. This alone would have saved 2 of 5 fix rounds.

### Fix 2: Imperative Replacement Bank (Priority: HIGH)
Add to fix prompts: "When replacing Ukrainian imperatives, use ONLY these English alternatives: Порівняйте -> 'Comparison:' / Уявіть -> 'Imagine this situation:' / Кажіть -> 'The correct form is:' / Використовуйте -> 'Use...' Do NOT introduce new Ukrainian imperative forms."

### Fix 3: Immersion Restart Threshold (Priority: HIGH)
If immersion gap > 10% (e.g., 9.2% vs 25% target), restart content phase instead of attempting a patch fix. Patch fixes for large immersion gaps predictably fail.

### Fix 4: Post-Content Vocabulary Weaving Check (Priority: MEDIUM)
After content phase, check that all required vocabulary items appear in the content. If missing, add them during content expansion rather than discovering the gap at validation.

### Fix 5: Fix Rule Clarity for Structural Issues (Priority: MEDIUM)
Separate structural fixes (missing sections, section reorganization) from content fixes (word changes, imperative removal). Structural fixes inherently require adding/reorganizing content, which contradicts "do not rewrite working content."

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Section title fuzzy matching (saves 2 fix rounds per module with this issue -- affects M16, M18, and likely others)
2. Imperative replacement bank (prevents whack-a-mole pattern where fixing one imperative introduces another)
3. Immersion restart threshold (prevents futile patch attempts on large immersion gaps)
