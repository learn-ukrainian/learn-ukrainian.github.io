# Prompt Engineering Review: plurals-and-alternation

**Track:** a1 | **Sequence:** 13
**Pipeline:** v4
**Validate attempts:** 0 (pipeline FAIL -- activities phase completed but validate never ran)
**Friction reports:** 2 (both NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Verb conjugation ban vs example sentences | HIGH | phase-2-prompt.md | GRAMMAR STATUS says "FORBIDDEN: verb conjugation" but immersion rule says "Provide 3-4 Ukrainian examples per grammar point" with no guidance on verb-free patterns. Gemini used грають, сидять in example sentences. |
| Unjumble schema example missing | HIGH | phase-C-prompt.md | Schema reference shows quiz, anagram, match-up, fill-in, group-sort, true-false but NO unjumble example. Gemini used wrong schema (sentence field instead of words array). |
| Research recommends IPA despite ban | MEDIUM | phase-A-output.md | Research says "Provide IPA only for the first occurrence" but IPA is BANNED at all levels. Research template doesn't enforce the ban. |
| Textbook examples irrelevant | LOW | phase-2-prompt.md | Grade 1 examples about apostrophes, letter Ш, И have zero relevance to plural formation (M13). |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No unjumble schema example | CRITICAL: broken unjumble activity (wrong schema) | Add unjumble example with `words` array + `answer` string to phase-C |
| Plan-meta alignment gap | Consonant alternation preview (к to ц, г to з) in plan but not in meta; content missed it entirely | Pre-validate plan vs meta alignment before content phase |
| No verb-free sentence patterns | Conjugated verbs in examples despite ban | Add verb-free pattern bank for pre-M15 modules |
| No vocabulary cross-check | 4 required plan items (дитина, людина, гроші, двері) absent from vocabulary YAML | Add post-C vocabulary checklist against plan hints |
| Research recommends IPA | Could cause IPA violations | Add IPA ban to research template |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| Content used conjugated verbs | conflicting_guidance | Constraints ban verbs but plurals naturally need sentence context | Verb-free sentence patterns |
| Unjumble schema violation | schema_mismatch | No example in prompt; model guessed wrong | Add inline unjumble schema example |
| Mislabeled vowel alternation (i-to-o called i-to-e) | model_limitation | Gemini confused alternation types | Add explicit alternation examples in research or plan hints |
| Missing consonant alternation | context_gap | Plan had it, meta dropped it, content followed meta | Plan-meta alignment check |
| Pipeline stopped before validate | unknown | State shows content/activities complete but validate never ran | Pipeline execution issue |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 0 (never ran) | Pipeline execution issue | N/A -- pipeline bug |
| content-review found 2 CRITICAL + 3 HIGH | - | Would have required extensive fixes | YES: unjumble schema example prevents 1 CRITICAL; verb-free patterns prevent 1 HIGH |

## Suggested Template Fixes

### Fix 1: Add Unjumble Schema Example (Priority: HIGH)
Add to phase-C-prompt.md:
```yaml
### unjumble (sentence building)
- type: unjumble
  title: "Build the Sentence"
  items:
    - words: ["Це", "нові", "книги"]
      answer: "Це нові книги."
```
Cross-module applicability: ALL modules using unjumble.

### Fix 2: Verb-Free Sentence Patterns for Pre-M15 (Priority: HIGH)
Add to constraints: "For Ukrainian examples, use only: Це + noun, Ось + noun, Там + noun, noun + adjective patterns. Do NOT use conjugated verbs."

### Fix 3: Plan-Meta Alignment Check (Priority: MEDIUM)
Pre-content check that diffs plan content_outline against meta content_outline. Flag missing plan points before content generation starts.

### Fix 4: Post-C Vocabulary Checklist (Priority: HIGH)
After phase C, auto-check that every required vocabulary_hint appears in vocabulary YAML. Flag missing items before validation.

### Fix 5: IPA Ban in Research Template (Priority: LOW)
Add: "Do NOT recommend IPA transcriptions. The project bans IPA at ALL levels."

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Add unjumble schema example (prevents schema violations across all modules)
2. Verb-free sentence patterns for pre-M15 (prevents grammar scope violations across M1-M14)
3. Post-C vocabulary checklist (prevents missing required vocabulary items)
