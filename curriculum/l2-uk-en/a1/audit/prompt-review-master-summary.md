# Prompt Engineering Master Summary: A1 (27 modules)

**Date:** 2026-03-06
**Ref:** #731
**Modules reviewed:** M11-22, M36-42, M44, M46-55

## Module Results

| # | Slug | Health | Val Attempts | Friction | Top Fix |
|---|------|--------|-------------|----------|---------|
| 11 | describing-things-adjectives | NEEDS_WORK | — | — | (reviewed in M11-14 batch) |
| 12 | colors-and-clothing | **BROKEN** | 6 | 2 | Plan-constraint conflict (verbs/dative) |
| 13 | plurals-and-alternation | NEEDS_WORK | 0 | 2 | Missing unjumble schema example |
| 14 | checkpoint-first-contact | GOOD | 1 | 2 | Pre-validate plan vs constraints |
| 15 | the-living-verb-i | NEEDS_WORK | 6 | 2 | H1 heading rule |
| 16 | the-living-verb-ii | GOOD | 2 | 2 | Section title fuzzy matching |
| 17 | reflexive-verbs | GOOD | 1 | 2 | Fix expand threshold logic |
| 18 | questions-and-negation | NEEDS_WORK | 5 | 2 | Section title fuzzy matching |
| 19 | likes-and-preferences | NEEDS_WORK | 6 | 2 | H1 heading rule |
| 20 | mine-and-yours | NEEDS_WORK | 5 | 2 | Inject exact H2 titles from meta |
| 21 | demonstratives-this-that | NEEDS_WORK | 5 | 2 | Inject H2 titles + imperative alternatives |
| 22 | numbers-and-money | NEEDS_WORK | 0 | 1 | Complete pipeline run (halted) |
| 36 | yesterday-past-tense | NEEDS_WORK | 2 | 2 | Inject exact H2 titles from meta |
| 37 | tomorrow-future-tense | NEEDS_WORK | 3 | 2 | English calque warnings |
| 38 | my-daily-routine | **BROKEN** | 0 | 1 | Pipeline failure in activities phase |
| 39 | food-vocabulary | NEEDS_WORK | 7 | 2 | Imperative examples in constraint |
| 40 | shopping-and-market | NEEDS_WORK | 2 | 2 | Dative ban vs formulaic chunks |
| 41 | at-the-cafe | NEEDS_WORK | 7 | 2 | Auto-fix heading levels |
| 42 | description-adverbs | GOOD | 0 | 1 | Infrastructure (gemini-cli crash) |
| 44 | checkpoint-daily-life | NEEDS_WORK | 3 | 2 | Checkpoint-specific template |
| 46 | must-and-want | GOOD | 0 | 0 | Infrastructure (gemini-cli crash) |
| 47 | imperative-and-requests | NEEDS_WORK | 3 | 2 | M40+ constraint variant |
| 48 | body-and-health | **BROKEN** | 2 | 2 | Plan-aware constraint relaxation |
| 49 | my-family | GOOD | 1 | 2 | Level-appropriate examples |
| 50 | holidays-and-traditions | NEEDS_WORK | 1 | 2 | Instrumental exception for greetings |
| 51 | leisure-and-hobbies | NEEDS_WORK | 2 | 2 | Dative ban with alternatives |
| 52 | travel-and-transport | NEEDS_WORK | 2 | 2 | Activity item minimums |
| 53 | at-the-restaurant | NEEDS_WORK | 2 | 2 | Restructure LEVEL_CONSTRAINTS |
| 54 | checkpoint-communication | NEEDS_WORK | 4 | 2 | Russianisms checklist (давайте+pf) |
| 55 | prohibitions-and-signs | **BROKEN** | 3 | 2 | Surface research errors to content prompt |

## Health Summary

| Health | Count | Modules |
|--------|-------|---------|
| GOOD | 6 | M14, M16, M17, M42, M46, M49 |
| NEEDS_WORK | 20 | M11, M13, M15, M18-22, M36-37, M39-41, M44, M47, M50-54 |
| BROKEN | 4 | M12, M38, M48, M55 |

**Total validate attempts:** ~79 across 27 modules (avg 2.9/module)

---

## Cross-Module Pattern Analysis

### CRITICAL Patterns (affect 10+ modules)

#### 1. LEVEL_CONSTRAINTS contradict teaching objectives (14+ modules)
**Modules:** M12, M19, M20, M21, M40, M47, M48, M50, M51, M52, M53, M54, M55 + others
**Problem:** LEVEL_CONSTRAINTS uniformly ban dative, instrumental, and subordinate clauses across ALL A1 modules. But M19+ modules explicitly teach these constructs. The constraint is a dense wall of text that Gemini systematically ignores or can't comply with because the plan demands the banned grammar.
**Root cause:** Static constraint text doesn't adapt to what each module teaches.
**Fix:** **Plan-aware constraint relaxation** — if the plan's grammar list includes a construct, automatically exempt it from the ban for that module. Restructure constraints as numbered rules with worked examples.
**Impact:** Would eliminate ~40+ fix attempts across the track.

#### 2. Section heading mismatch (12+ modules)
**Modules:** M15, M18, M19, M20, M21, M36, M37, M39, M41 + others
**Problem:** Gemini outputs H2 titles that don't exactly match what the plan/meta expects. The audit tool's heading matcher is too strict on Unicode, whitespace, bilingual format. Fix loops waste 1-2 attempts each time on a matching problem, not a content problem.
**Fix:** (a) Inject exact H2 titles from meta into content prompt; (b) fuzzy match in outline_compliance.py; (c) deterministic heading normalization post-processing.
**Impact:** Would save ~24 fix attempts.

#### 3. Imperative ban lacks positive examples (10+ modules)
**Modules:** M12, M15, M18, M20, M21, M39, M41 + others
**Problem:** Constraint says "no imperatives before M47" but never lists which Ukrainian words are imperatives or what to use instead. Gemini repeatedly generates Запам'ятайте, Порівняйте, Уявіть, Зверніть увагу.
**Fix:** Add explicit banned forms list AND "INSTEAD OF X / USE Y" replacement table.
**Impact:** Would prevent 3-pass fix loops in pre-M47 modules.

### HIGH Patterns (affect 5-10 modules)

#### 4. Heading level `## Summary` vs `# Summary` (6+ modules)
**Modules:** M15, M19, M39, M41 + others
**Problem:** Content prompt output format uses `##` for section headers, making Gemini output `## Підсумок` instead of `# Підсумок`. SECTION_FIX format structurally prevents fixing it.
**Fix:** Deterministic regex post-processing: `re.sub(r'^##\s+(Підсумок|Summary)', r'# \1', content, flags=re.MULTILINE)`
**Impact:** Would save ~12 fix attempts.

#### 5. Empty/duplicate fix prompts (5+ modules)
**Modules:** M19, M20, M37 + others
**Problem:** Fix prompts sometimes contain no specific issues ("AUDIT FAILED" only), or are identical to previous attempts. Pipeline doesn't track which violations were already fixed.
**Fix:** (a) Skip fix attempt when no violations extracted; (b) SHA-256 deduplication (partially implemented); (c) track fixed violations between iterations.
**Impact:** Would save ~10 wasted API calls.

#### 6. Grade 1 bukvar examples injected into M15+ modules (all M15+ modules)
**Modules:** All modules M15-M55
**Problem:** Content prompts include 150+ lines of syllable/letter exercises from 1st-grade primers as "inspiration" for modules teaching verbs, tenses, shopping, etc. Wastes ~800 tokens per module for zero pedagogical benefit.
**Fix:** Only inject textbook examples for M1-M14 (script modules). Use level-appropriate examples for M15+.
**Impact:** Saves tokens, reduces confusion.

#### 7. No English calque checklist (all modules)
**Modules:** All Gemini-built modules
**Problem:** The Russianisms table only covers Russian→Ukrainian calques. Gemini, as an English-dominant model, systematically produces English→Ukrainian calques ("буду мати" for "will have", "робити роботу" for "do work", "зберегти гроші" for "save money").
**Fix:** Add English calque warning table to content prompt template.
**Impact:** Prevents a whole class of undetected errors.

### MEDIUM Patterns (affect 2-4 modules)

#### 8. Meta outline `title:` vs `section:` key mismatch (2+ modules)
**Modules:** M39, M41
**Problem:** Research template outputs `title:` key but `outline_compliance.py` expects `section:`. Caused KeyError crash.
**Fix:** Accept both keys in compliance checker.

#### 9. No word count upper bound (2+ modules)
**Modules:** M55 (4039w/1200 target), M17 (expand triggered above target)
**Problem:** No ceiling on word count. Over-production increases error surface and review cost. Expand phase triggered with negative delta.
**Fix:** Add explicit range (e.g., 1200-1800 for A1). Guard expand: skip if word_count >= target.

#### 10. Immersion crashes during fix loops (2+ modules)
**Modules:** M52 + others
**Problem:** Fix prompts say "do not rewrite working content" but when headings must change, model rewrites content in English, crashing immersion.
**Fix:** Add explicit immersion preservation rule to fix prompt template.

#### 11. Checkpoint modules lack specific template (2 modules)
**Modules:** M14, M44
**Problem:** Checkpoint modules (review/consolidation) use the same content template as teaching modules. They need a different structure.
**Fix:** Create checkpoint-specific content template.

#### 12. Research errors not surfaced to content prompt (1-2 modules)
**Modules:** M55
**Problem:** Research phase found error pairs but they weren't injected into content prompt constraints. Led to hallucinated forms in content.
**Fix:** Auto-surface research-identified error patterns as content constraints.

#### 13. Vocab-in-content requirement missing (2 modules)
**Modules:** M21, M37
**Problem:** Content prompt never says vocabulary words must appear in the prose. 60% coverage in M21.
**Fix:** Add "All vocabulary_hints words must appear in the content at least once" rule.

#### 14. Activity item minimums not enforced (2 modules)
**Modules:** M52 (7/9 below minimum)
**Problem:** Minimums table exists but isn't prominent enough.
**Fix:** Move to CRITICAL box with "HARD FAIL" language.

---

## Top 7 Fixes by Leverage (sorted by estimated fix attempts saved)

| # | Fix | Est. Attempts Saved | Scope | Target File |
|---|-----|-------------------|-------|-------------|
| 1 | **Plan-aware constraint relaxation** | ~40 | All A1 M19+ | `scripts/pipeline_lib.py` |
| 2 | **Section heading fuzzy match + injection** | ~24 | All modules | `scripts/audit/outline_compliance.py` + prompt templates |
| 3 | **Imperative ban with examples + alternatives** | ~15 | All A1 pre-M47 | `scripts/pipeline_lib.py` (PEDAGOGICAL_CONSTRAINTS) |
| 4 | **Deterministic heading level post-processing** | ~12 | All modules | `scripts/pipeline_v5.py` (post-processing) |
| 5 | **Empty/duplicate fix prompt prevention** | ~10 | All modules | `scripts/pipeline_v5.py` (validate loop) |
| 6 | **English calque checklist** | ~5+ | All modules | `claude_extensions/phases/gemini/beginner-content.md` |
| 7 | **Level-appropriate textbook examples** | ~3+ | All M15+ | Prompt template injection logic |

## Modules Needing Rebuild After Fixes

| Priority | Modules | Reason |
|----------|---------|--------|
| **BROKEN — rebuild first** | M12, M38, M48, M55 | Exhausted fix budget / pipeline crash / hallucinations |
| **High fix count** | M15, M18, M19, M20, M21, M39, M41, M54 | 5-7 validate attempts, likely degraded content |
| **Moderate** | M13, M36, M37, M40, M44, M47, M50, M51, M52, M53 | 1-3 attempts, may be salvageable with targeted fixes |
| **OK — skip rebuild** | M14, M16, M17, M42, M46, M49 | GOOD health, 0-2 attempts, minor issues |
| **Incomplete — needs full build** | M22, M38, M46 | Pipeline halted mid-build |

---

## Infrastructure Bugs (not prompt issues)

| Bug | Modules | Fix |
|-----|---------|-----|
| gemini-cli "Premature close" crashes | M42, M46 | Add retry logic for transient API errors |
| Pipeline halts silently after content phase | M22, M38 | Add error logging / phase transition validation |
| Expand triggered above word target | M17, M39 | Guard: `if word_count >= target: skip expand` |
| `title:` vs `section:` KeyError in outline_compliance | M39, M41 | Accept both keys |
| PLAN_SECTION_MISSING false positives (Unicode/whitespace) | M49, M50, M51 | Fuzzy heading match |
