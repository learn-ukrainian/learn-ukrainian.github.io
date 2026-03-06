# Prompt Engineering Review: the-living-verb-i

**Track:** a1 | **Sequence:** 15
**Pipeline:** v4
**Validate attempts:** 6 (exhausted)
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Summary heading level contradiction | HIGH | phase-2-prompt.md | Output format template shows `# Підсумок` (H1), but the content_outline lists "Підсумок" as a regular section. The example output format uses `# {Title}` for the module title and `# Підсумок` for summary, but the writing instructions say "each section maps to an H2." Gemini defaulted to H2, which the audit rejected. This single issue persisted across ALL 6 fix attempts. |
| Imperative constraint stated but not enforced in examples | HIGH | phase-2-prompt.md | The constraint says "Imperative forms NOT taught until M47" and "use indirect requests or English for instructions." But the `IMMERSION_RULE` says "Write cultural notes, practical sections, observations, and drill instructions in Ukrainian first" -- which naturally leads to Ukrainian imperatives. No examples of *compliant* instruction phrasing are given. |
| Textbook examples irrelevant to module topic | LOW | placeholders.yaml / phase-2-prompt.md | TEXTBOOK_EXAMPLES contains Grade 1 bukvar letter-introduction exercises (syllable drills for D, M, V). These are entirely irrelevant for M15 which teaches verb conjugation. The template injects the same examples regardless of module topic. |
| Contradictory heading instructions | HIGH | phase-2-prompt.md | The output format says `# Підсумок` (H1) for summary. But the instruction "each section maps to an H2" implies `## Підсумок`. The audit gate requires H1 for "Summary" sections. Gemini consistently chose H2 and could not resolve the ambiguity across 6 attempts. |
| `{H3_WORD_RANGE}` unreplaced in prose | LOW | phase-2-prompt.md line 6 | The persona reminder says "Every H3 gets {H3_WORD_RANGE} words" -- the literal placeholder text `{H3_WORD_RANGE}` appears in the prompt. While `H3_WORD_RANGE: 60-80` is defined in placeholders.yaml, it appears the template did not substitute inside the blockquote. |
| Conflicting immersion target vs initial output | MEDIUM | phase-2-prompt.md | Immersion target is 25-40%. Fix2 reported actual immersion at 8.0% -- a massive 17% gap. The content prompt provides the immersion rule but gives no concrete technique for achieving it in a grammar-focused module (verb conjugation tables are inherently Ukrainian-heavy or English-heavy). |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No explicit H1 vs H2 heading rule for summary sections | Critical -- caused 6 fix loops for a trivial formatting issue | Add explicit rule: "Summary/Підсумок sections use H1 (#), not H2 (##)" to content prompt output format |
| No examples of imperative-free Ukrainian instruction phrasing | High -- Gemini kept generating imperatives across fix passes 3-5 | Add a table of banned vs. allowed patterns |
| Textbook examples not filtered by module topic | Low -- wasted prompt tokens (~2000 chars) on irrelevant syllable drills | Filter TEXTBOOK_EXAMPLES by module type (letter-intro vs grammar vs vocabulary) |
| PERSONA_ROLE ("Sports Commentator") not explained | Low -- unclear how this maps to content voice for verb conjugation | Either remove or provide a sentence explaining the persona role |
| Decodable vocabulary empty but still referenced | Low -- instruction says "from the decodable vocabulary only" but DECODABLE_VOCABULARY is empty | Conditionally omit decodable vocabulary references when the field is empty |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| Summary heading level (## vs #) -- persisted all 6 fix attempts | template_gap | Output format shows `# Підсумок` but "each section maps to an H2" contradicts it. Fix prompts repeated the same instruction without resolving the ambiguity. | Add explicit heading level rule in content prompt: "Summary = H1" |
| Imperative verbs introduced repeatedly (fixes 3, 4, 5) | conflicting_guidance | IMMERSION_RULE says "write drill instructions in Ukrainian first" which naturally produces imperatives. The separate PEDAGOGICAL_CONSTRAINTS bans imperatives. Gemini resolved one imperative per fix pass but introduced new ones. | Add imperative-free examples to the immersion rule section. Add a post-generation self-check. |
| Immersion too low (8% at fix2) | context_gap | Content prompt gives the percentage target but no technique for achieving it in a grammar module. | Add concrete technique for grammar modules. |
| Missing plan sections (fix1, fix3) -- section names didn't match | schema_mismatch | Outline has "Культурний аспект та підсумок" but the audit expected sections matching this exact bilingual format. Gemini wrote different heading text. | Inject exact expected heading text from content_outline into the output format skeleton. |
| Dative case violation -- "мові" (fix2) | model_limitation | Gemini used "мові" naturally despite the dative ban. | Add "мові" to an explicit banned-word list for A1 modules. |
| Robotic structure -- 3x "we are..." (fix2) | model_limitation | LLM default repetition pattern. | Add to self-check: "Count sentence-initial phrases. Flag 3+ identical openers." |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 6 (exhausted) | Summary heading level (## vs #) persisted through ALL 6 attempts. Fix prompts 3-6 all listed it explicitly but Gemini could not apply it. Escalation also failed. | YES -- content prompt should generate `# Підсумок` from the start. |
| validate (secondary) | 3 of 6 | Imperative verbs -- each fix removed one but introduced another. Whack-a-mole pattern. | YES -- add a self-check scan step for imperatives. |
| validate (secondary) | 1 of 6 | Immersion gap (8% -> target 25%). | PARTIALLY -- better original prompt guidance needed. |

## Suggested Template Fixes

### Fix 1: Explicit Summary Heading Level in Output Format (Priority: HIGH)
**Prevents:** The exact issue that consumed all 6 fix attempts on this module.
**Scope:** Content prompt template, affects all A1 modules.
**Template file:** Content prompt output format section.

### Fix 2: Imperative-Free Instruction Examples (Priority: HIGH)
**Prevents:** 3 of 6 fix passes being consumed by imperative violations.
**Scope:** Content prompt template for M1-M46 modules.
**Template file:** PEDAGOGICAL_CONSTRAINTS placeholder / phase-2-prompt.md.

### Fix 3: Topic-Filtered Textbook Examples (Priority: MEDIUM)
**Prevents:** ~2000 tokens of irrelevant syllable drills in grammar module prompts.
**Scope:** Pipeline placeholder injection logic.

### Fix 4: Fix Prompt Should Include Full Audit Output (Priority: MEDIUM)
**Prevents:** Fix prompts with incomplete diagnostic info leading to wasted attempts.
**Scope:** Validate-fix prompt template.

### Fix 5: Immersion Achievement Techniques for Grammar Modules (Priority: LOW)
**Prevents:** Low immersion on first pass requiring fix-loop corrections.
**Scope:** Content prompt for grammar-focused modules.

## Summary

**Template health:** NEEDS WORK

**Top 3 fixes by leverage:**
1. **Explicit Summary H1 heading rule** -- would have saved all 6 fix attempts on this module (and the identical issue on likes-and-preferences). Cross-module systemic issue.
2. **Imperative-free instruction examples** -- would have prevented 3 of 6 fix attempts. The current constraint tells Gemini what NOT to do but gives no examples of what TO do instead.
3. **Full audit output in fix prompts** -- fix1 and fix2 had minimal diagnostic information, leading to blind fix attempts.
