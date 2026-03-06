# Prompt Engineering Review: reflexive-verbs

**Track:** a1 | **Sequence:** 17
**Pipeline:** v4
**Validate attempts:** 1
**Friction reports:** 2 (phase-2: NONE, phase-C: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Expand prompt sent despite word count already above target | MEDIUM | phase-2-expand-2.md, phase-2-expand-3.md | Both expand prompts say "previous output was 1476 words -- below the 1200 word minimum" and then calculate "need -276 more words" (negative number). The module was ABOVE target but the expand logic fired anyway. This is a pipeline bug. |
| Expand prompt asks for full rewrite | MEDIUM | phase-2-expand-2.md | "Rewrite the ENTIRE module with expanded content" -- when only specific sections need expansion (or none, since 1476 > 1200). Full rewrites waste tokens and risk quality regression. |
| Imperative constraint not surfaced enough | LOW | phase-2-prompt.md | Constraints mention "Imperative forms NOT taught until M47" but no imperatives were found in the final output -- the constraint worked for this module. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Expand logic triggered incorrectly | 2 unnecessary full rewrites (expand-2, expand-3) wasting tokens and time | Fix expand threshold logic: only trigger if word count < target |
| VESUM false negatives on morpheme fragments | -сь, -ться, -цця flagged as unverified but are morphological suffixes being taught | Add suffix whitelist to VESUM screening for grammar-teaching modules |
| Proper nouns (Одеса, Олег) fail VESUM | False negatives on city and personal names | Add proper noun detection to VESUM screening |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| Unnecessary expand rounds | template_gap | Pipeline expand logic fired despite 1476 > 1200 target; calculated "need -276 more words" | Fix expand threshold comparison: `if word_count < target then expand` |
| Full rewrite on expand | template_gap | Expand prompt says "Rewrite the ENTIRE module" instead of expanding specific sections | Change expand prompt to: "Expand only sections under their individual word targets" |
| VESUM suffix false negatives | schema_mismatch | -ся, -ться, -сь are taught as morphological units but VESUM doesn't recognize isolated suffixes | Add suffix whitelist for grammar modules |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| content | 3 (1 original + 2 unnecessary expands) | Expand logic bug (triggered despite word count above target) | YES -- fix expand threshold |
| validate | 1 | Minor audit issue, quickly resolved | Marginal |

## Suggested Template Fixes

### Fix 1: Fix Expand Threshold Logic (Priority: HIGH)
The expand logic calculates "need -276 more words" (negative) and still triggers. Fix: only send expand prompt if `word_count < word_target`.

### Fix 2: Targeted Expansion Instead of Full Rewrite (Priority: MEDIUM)
Replace "Rewrite the ENTIRE module" in expand prompt with "Expand only sections that are under their individual word targets. Do NOT rewrite sections that are already at or above target."

### Fix 3: VESUM Suffix Whitelist (Priority: LOW)
Add whitelist of common morphological suffixes (-ся, -сь, -ться, -цця, -ий, -ій, -ю) that appear in grammar-teaching modules as isolated units.

### Fix 4: Proper Noun Detection (Priority: LOW)
Add proper noun detection to VESUM screening. Capitalized Ukrainian words matching common name/city patterns should not be flagged.

## Summary

**Template health:** GOOD
**Top 3 fixes by leverage:**
1. Fix expand threshold logic (prevents 2 unnecessary full rewrites per module)
2. Targeted expansion instead of full rewrite (reduces token waste and quality regression risk)
3. VESUM suffix whitelist (reduces false negative noise in grammar modules)
