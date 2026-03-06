# Prompt Engineering Review: at-the-cafe

**Track:** a1 | **Sequence:** 41
**Pipeline:** v4
**Validate attempts:** 6 (exhausted) + 1 escalation
**Friction reports:** 2 (phase-2-friction-1, phase-C-friction)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Imperative ban still not prominent enough | HIGH | phase-2-prompt.md | Same pattern as M39: the constraint is present but Gemini still produced `Порівняйте` in content. Only caught at fix 3 (attempt 3). The ban needs explicit examples. |
| `## Summary` heading level mismatch persists across 4 fix attempts | CRITICAL | validate-fix prompts | Fix prompts 4-6 and escalation all report the same issue: `## Summary` should be `# Summary`. The model could not fix a simple heading change across 4 attempts. This strongly suggests the fix prompt format is confusing — the model does not understand where in the file to make the change, or the SECTION_FIX output format does not support heading-level changes. |
| Dative case used in vocabulary hints | MEDIUM | placeholders.yaml (VOCAB_HINTS) | Vocab hints include "Мені, будь ласка..." and "Мені каву..." which use Dative (мені). The content correctly uses these as lexical chunks, but the plan vocabulary is technically contradicting the A1 Dative ban. This creates ambiguity for the model. |
| Instrumental case in vocab hints | MEDIUM | placeholders.yaml (VOCAB_HINTS) | Vocab hints include "оплатити карткою", "платити готівкою" which are Instrumental case forms — banned at A1. Content treats them as lexical chunks, but the model could be confused about whether to explain the grammar. |
| IPA false positive in audit | LOW | validate-fix3-prompt.md | Audit flagged `[Accusative]` as "Banned IPA transcription" — this is a false positive. Square brackets around an English grammar term are not IPA. The audit regex is too aggressive. |
| Meta outline uses `title:` key | MEDIUM | phase-A-output.md | Same issue as M39 — the research output uses `title:` in content_outline but the audit expects `section:`. This module escaped the crash because the escalation for M39 happened first and fixed the meta, but the template still outputs the wrong key. |
| Plan section name mismatch | MEDIUM | validate-fix1-prompt.md | Audit reports "Missing 1 plan section(s): Продукція та Підсумок (Production and Summary)" — the content had 4 sections with different names than the plan. Fix 1 added the missing section, but the plan section naming was never aligned with the content outline in meta. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| M39 (food-vocabulary) content not injected | Gemini duplicated Accusative case teaching that was already covered in M39. Without seeing M39 content, it could not build on prior knowledge. | Inject M39 summary or at minimum its vocab list and grammar topics. |
| Heading level spec not explicit in content prompt | Content prompt says "each section maps to an H2" but Summary spec requires H1. This contradictory guidance caused the persistent `## Summary` issue. | Add explicit note: "The Summary section uses `# Підсумок` (H1), not H2." |
| Fix prompt does not include current file content for heading fixes | Fix prompts 4-6 tell the model to change `## Summary` to `# Summary` but the SECTION_FIX output format expects `## {section title}` as the delimiter. The model cannot output `# Summary` inside a `===SECTION_FIX_START===` block that expects `## {title}`. | Change fix output format to support any heading level, or have the pipeline apply heading fixes directly without model intervention. |
| Discovery returned irrelevant videos | Low | Discovery found videos about "My Family Forced Me to Marry" and "36 English Phrases" with 0.0 relevance. These waste context window. | Filter out 0.0 relevance videos before injecting into context. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| Imperative `Порівняйте` in content | template_gap | Same root cause as M39. The imperative ban lacks explicit examples of banned forms. | See M39 Fix 1 — add imperative detection examples. |
| `## Summary` heading stuck across 4 attempts | template_gap | The SECTION_FIX output format uses `## {section title}` as delimiter, making it structurally impossible for the model to output `# Summary`. The fix format itself prevents the fix. | Either: (a) have pipeline apply heading-level fixes as a regex pass, or (b) change SECTION_FIX format to allow any heading level. |
| IPA false positive `[Accusative]` | schema_mismatch | Audit IPA regex matches any `[text]` pattern, not just phonetic symbols. English grammar terms in brackets trigger false positives. | Refine IPA regex to only match actual IPA characters (ɑ, ɛ, ʃ, etc.) or known phonetic bracket patterns. |
| Immersion too low (18% at fix 2) | model_limitation | Initial content was heavily English. Gemini defaulted to English explanations despite the 35-55% Ukrainian target. Fix 2 asked for +5-8% improvement, which was insufficient. By escalation, immersion reached 38.1% — barely above minimum. | Add Ukrainian sentence templates/starters in the content prompt to scaffold immersion. |
| Plan section name drift | template_gap | Content outline in meta had section names that differed from what Gemini actually wrote. The pipeline detected "missing sections" but the names were just different, not truly missing. | Validate meta section names against plan section names during research phase. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 6 + escalation | Heading level `## Summary` (fixes 4-6, escalation), immersion too low (fix 2), IPA false positive (fix 3), imperative (fix 3), plan section missing (fix 1) | PARTIALLY — heading level fix is structurally impossible in current format; IPA false positive is an audit bug; immersion was a model limitation |

The fix loop is dominated by the `## Summary` heading issue. Fixes 4, 5, 6, and the escalation ALL report the same single violation. The model attempted the fix each time but the output format prevented success. This is a template/pipeline structural problem, not a model problem.

Fix 1 addressed a real content gap (missing plan section). Fix 2 addressed immersion (too low). Fix 3 addressed an IPA false positive and an imperative. Fixes 4-6 were pure waste — the same heading issue repeated.

## Suggested Template Fixes

### Fix 1: Auto-fix heading levels in pipeline (Priority: CRITICAL)
**Prevents:** 4 wasted fix attempts on a trivial heading change
**Scope:** All modules
**Template file:** `scripts/pipeline_v5.py` (validate phase)

Add a pre-model regex pass: if the only violation is a heading level mismatch, apply `sed` to change `## Summary` to `# Summary` (or whatever the spec requires) without invoking the model. This is a deterministic fix that should never require an LLM.

### Fix 2: Fix IPA detection regex (Priority: HIGH)
**Prevents:** False positives on `[Accusative]`, `[Grammar]` etc.
**Scope:** All modules
**Template file:** `scripts/audit/checks/` (IPA detection)

Current regex matches any `[text]` in content. Should only match patterns containing actual IPA characters or known phonetic notation patterns like `[ˈmɑmɑ]`, `[a-na-nas]`.

### Fix 3: Inject prior module context (Priority: MEDIUM)
**Prevents:** Content duplication across sequential modules (M39 food-vocabulary and M41 at-the-cafe both teach Accusative case from scratch)
**Scope:** All modules with `connects_to` / `builds_on` references
**Template file:** `claude_extensions/templates/a1-content-prompt.md`

Add: "This module builds on M39 (Food and Drink). The learner already knows: [auto-inject M39 vocab list and grammar topics]. Do NOT re-teach these concepts — reference them briefly and build on them."

### Fix 4: Add immersion scaffolding to content prompt (Priority: MEDIUM)
**Prevents:** Content that starts at 18% immersion (far below 35% target)
**Scope:** All A1 modules
**Template file:** `claude_extensions/templates/a1-content-prompt.md`

Add concrete Ukrainian sentence starters the model should use:
```
For each English explanation paragraph, FIRST write 2-3 Ukrainian sentences (max 10 words each) with the key content. THEN write the English explanation. This ensures Ukrainian immersion reaches the 35-55% target.
```

### Fix 5: Filter zero-relevance discoveries (Priority: LOW)
**Prevents:** Irrelevant videos wasting context window
**Scope:** All modules with discovery phase
**Template file:** `scripts/pipeline_v5.py` (discovery injection)

Filter out any discovery items with `relevance_score: 0.0` before injecting into placeholders.

### Fix 6: Clarify Summary heading level in content prompt (Priority: LOW)
**Prevents:** Ambiguity about whether Summary is H1 or H2
**Scope:** All modules
**Template file:** `claude_extensions/templates/a1-content-prompt.md`

The output format template already shows `# Підсумок` as H1, but the writing instructions say "each section maps to an H2." Add explicit note: "All body sections use ## (H2). The final Summary uses # Підсумок (H1)."

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. **Auto-fix heading levels in pipeline** — eliminates the dominant fix loop pattern (4 wasted attempts on a trivial regex fix)
2. **Fix IPA detection regex** — eliminates false positives that trigger unnecessary fix attempts
3. **Add imperative examples to constraint text** (cross-module with M39) — prevents imperative violations across all A1 modules
