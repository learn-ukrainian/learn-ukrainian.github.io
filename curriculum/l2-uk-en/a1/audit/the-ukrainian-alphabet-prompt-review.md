# Prompt & Context Engineering Review: the-ukrainian-alphabet

**Track:** a1 | **Sequence:** 1
**Pipeline:** v5
**Validate attempts:** 0 (precheck failed — `systemic-5-failures`)
**Friction reports:** 2 (content: NONE, validate-dedup: PROMPT_ENGINEERING_BUG)
**Gemini self-audit iterations:** 3
**Model:** gemini-3.1-pro-preview

---

## Context Engineering Analysis

### Instruction → Understanding → Output Gap

| Instruction (from prompt) | What Gemini produced | Gap type | Evidence |
|--------------------------|---------------------|----------|----------|
| "Each letter below MUST get its video embedded in the corresponding H3 section" + per-letter video URLs | 10 H3 sections with near-identical structure: video link → 1-sentence description | **structural_impossibility** | Sections "Літера І", "Літера Н", "Літера К", "Літера С" flagged 71-77% CONTENT_REDUNDANCY overlap — the mandated format is inherently repetitive |
| "VOCAB-IN-CONTENT RULE: All vocabulary words from vocabulary_hints MUST appear at least once" | All 23 vocab words appear in content (ма́ма line 109, дя́кую line 131, тут line 147, etc.) | **validator_bug** | screen-result reports 7 words "missing" (дя́кую, ма́ма, ма́сло, мі́сто, о́ко, та́то, тут) — all have stress marks in vocab YAML; likely a stress-mark normalization mismatch in the VOCAB_NOT_IN_CONTENT checker |
| "3+ callout boxes" | 4 callout boxes (tip, warning, did-you-know, culture) | **compliant** | Lines 29-30, 85-87, 46-47, 153-154 |
| "No dialogues (verbs are banned)" | 1 blockquote dialogue (line 136-137: "Це кіт?" / "Так, це кіт.") — verb-free, using only Це+noun | **instruction_conflict** | Prompt says "Do NOT write dialogues" but also mandates "Blockquote dialogues" in structural containment. Gemini found a middle ground (verb-free dialogue) but richness calculator docks for only 0/4 dialogues |
| "EXACT H2 titles from the outline" | All 6 H2 sections match exactly | **compliant** | ✅ |
| "1200-1800 words" | 1227 words (1419 raw before audit stripping) | **compliant** | ✅ Word target met |

### Gemini Self-Audit Findings

- **Iterations:** 3
- **Gates passed:** Persona, Words, Engagement, Audio, Structure, Lint, Pedagogy, Immersion
- **Gates failed:** none (self-reported)
- **Fixes applied:** Added missing YAML frontmatter, fixed content redundancy in Summary, added missing `## Presentation` header
- **What Gemini missed:** CONTENT_REDUNDANCY in letter H3 sections (structural, not fixable by self-audit), VOCAB_NOT_IN_CONTENT (likely validator bug, not Gemini's fault)

### Immersion Breakdown (per section)

| Section | Est. English words | Est. Ukrainian words | Ukrainian % | Containers used |
|---------|-------------------|---------------------|-------------|----------------|
| Вступ — Introduction | ~140 | ~6 | ~4% | 0 |
| Букви і звуки — Letters and Sounds | ~195 | ~10 | ~5% | 1 callout |
| Голосні та приголосні — Vowels and Consonants | ~165 | ~15 | ~8% | 1 callout, 1 list |
| Перші 10 літер — First 10 Letters | ~280 | ~50 | ~15% | 1 callout, 1 table, blending patterns |
| Перші слова — First Words in Context | ~120 | ~40 | ~25% | 1 callout, 1 dialogue, 1 list |
| Підсумок — Summary | ~60 | ~20 | ~25% | 0 |
| **TOTAL** | ~960 | ~141 | **~6.2%** | |

Immersion at 6.2% — within 5-15% target. Front sections are underweight (4-5%), final sections overweight (25%). Acceptable for an alphabet module where early sections are necessarily English-heavy.

### Root Cause Verdict

**Primary gap:** structural_impossibility + validator_bug

**Explanation:** The prompt mandates per-letter H3 sections with video embeds, creating 10 sections with inherently repetitive structure (video → 1-line description). The CONTENT_REDUNDANCY checker sees 71-77% overlap because letters **are** taught the same way. This is a **template design flaw** — the prompt creates a structure that the validator rejects. Separately, the VOCAB_NOT_IN_CONTENT failure is a **validator bug** — all 7 "missing" words actually appear in content but carry stress marks (´) that the checker doesn't normalize.

---

## Prompt Clarity

| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| Contradictory dialogue guidance | HIGH | content-prompt.md §Writing Style + §Structural Containment | "Do NOT write dialogues" (line ~ban) vs "Blockquote dialogues — mini-conversations with labeled speakers" (structural containment). Gemini found a creative middle ground but the conflict is confusing |
| Prompt length: 846 lines | MEDIUM | content-prompt.md | Full-build prompt is enormous. Gemini's 3-iteration self-audit suggests it processed it, but the length risks attention dilution. Most important instructions (grammar ban, immersion target) are buried in the middle |
| Missing instruction: letter section differentiation | HIGH | content-prompt.md §Writing Style | The prompt mandates per-letter H3 sections with mandatory videos but gives NO guidance on how to make each section unique. Should specify: "For each letter, include at least one unique comparison, mnemonic, or false-friend warning" |
| OLD template architecture | MEDIUM | content-prompt.md | Uses inline content rules instead of new `{QUALITY_DIMENSIONS}` / `{PREFLIGHT_INSTRUCTIONS}` placeholders. Self-audit is at the END of the prompt instead of a preflight gate BEFORE writing |
| Textbook excerpts too long | LOW | content-prompt.md §Textbook Source Material | ~300 tokens of raw textbook excerpts (Grade 1 pages) that are minimally useful for THIS module. The research file already distills the relevant pedagogical approach |

---

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No richness score requirements | Richness score 47/95 (engagement 2/5, cultural 0/3, examples 7/24, dialogues 0/4, tables 1/2) — Gemini had no target | Inject `{RICHNESS_TARGETS}` placeholder with per-component minimums. For alphabet modules, waive dialogue requirement |
| No per-letter differentiation examples | 4 CONTENT_REDUNDANCY violations in letter H3 sections | Add example in prompt: "Літера Н: **Н** looks like English H but sounds like N. This is the most common false friend…" vs "Літера М: **М** is identical to English M. No surprises here." |
| Validator stress-mark behavior not communicated | Gemini correctly used stress marks throughout, but validator's VOCAB_NOT_IN_CONTENT doesn't normalize them | This is a tooling fix, not a prompt fix. See Fix 4 below |

---

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| content-friction-1: NONE | N/A | Clean build, no friction during content generation | N/A |
| validate-dedup: PROMPT_ENGINEERING_BUG | **template_gap** | Validate phase deduped because fix prompt couldn't address CONTENT_REDUNDANCY — the letter H3 pattern is structural, not a prose quality issue | Restructure letter sections to avoid per-H3 repetition (see Fix 1) |
| systemic-5-failures | **structural_impossibility** | 4 CONTENT_REDUNDANCY + 1 VOCAB_NOT_IN_CONTENT + richness gap — all systemic, not fixable by Gemini rewording | Template + validator fixes needed |

---

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 0 (precheck halted) | systemic-5-failures: 4 CONTENT_REDUNDANCY from mandatory per-letter H3 format, 1 VOCAB_NOT_IN_CONTENT from stress-mark mismatch | **YES** — Fix letter section template (Fix 1) + fix validator stress normalization (Fix 4) |

---

## Suggested Template Fixes

### Fix 1: Restructure Letter Sections to Avoid Redundancy (Priority: HIGH)

**Prevents:** CONTENT_REDUNDANCY (4 violations)
**Scope:** All alphabet/phonology modules (a1 M1-M4)
**Template file:** `claude_extensions/phases/gemini/beginner-content.md` or content-prompt template

Instead of mandating individual H3 per letter, group letters by type and put the video links in a reference table:

```diff
- **Each letter below MUST get its video embedded in the corresponding H3 section:**
- - **Літера А**: [Anna Ohoiko — Ukrainian Lessons — А](...)
- - **Літера О**: [Anna Ohoiko — Ukrainian Lessons — О](...)
- [... 10 separate H3 sections]
+ **Group letters by characteristic** (false friends, familiar shapes, vowels). Embed videos
+ in a reference table, not individual H3 sections. Write 2-3 substantial paragraphs per
+ GROUP, not 1 sentence per letter:
+
+ | Letter | Video | Category |
+ |--------|-------|----------|
+ | А | [link] | Familiar vowel |
+ | О | [link] | Familiar vowel |
+ | ... | ... | ... |
+
+ Then discuss each GROUP in a paragraph:
+ - **Familiar shapes** (А, О, М, Т, К): "Five of your first 10 letters look identical..."
+ - **False friends** (Н, С): "Two letters look like English letters but sound completely..."
+ - **New shapes** (У, І, Л): "Three letters have shapes you haven't seen..."
```

### Fix 2: Resolve Dialogue Contradiction (Priority: MEDIUM)

**Prevents:** Confusion + richness score penalty
**Scope:** All alphabet/phonology modules
**Template file:** beginner-content.md §Writing Style

```diff
- **FORBIDDEN patterns (HARD FAIL):**
- - Dialogues (verbs are banned in this phase — dialogues need verbs)
+ **FORBIDDEN patterns (HARD FAIL):**
+ - Dialogues that use verbs (verbs are banned in this phase)
+
+ **ALLOWED dialogue format (verb-free):**
+ Verb-free mini-exchanges using Це + noun pattern are encouraged for practice:
+ > — Це кіт?
+ > — Так, це кіт.
```

### Fix 3: Add Richness Score Targets (Priority: MEDIUM)

**Prevents:** Low richness scores (47/95 on this build)
**Scope:** All modules
**Template file:** `_shared-quality-dimensions.md` or injected via `{RICHNESS_TARGETS}`

```diff
+ ### Richness Targets
+ Your content should include a mix of these elements:
+ - **Engagement boxes**: 3+ (callouts: tip, warning, culture, did-you-know)
+ - **Example sentences**: 15+ Ukrainian examples with English gloss
+ - **Tables**: 2+ (letter charts, vocabulary tables, etc.)
+ - **Cultural notes**: 1+ (history, traditions, or linguistic heritage)
+ For alphabet modules: dialogues are optional (verb-free only).
```

### Fix 4: Fix VOCAB_NOT_IN_CONTENT Validator (Priority: HIGH)

**Prevents:** False VOCAB_NOT_IN_CONTENT failures
**Scope:** All modules (validator tooling)
**File:** `scripts/audit/` (validator code)

The VOCAB_NOT_IN_CONTENT checker must normalize stress marks (combining acute accent U+0301) before comparing vocabulary lemmas against content text. All 7 "missing" words (дя́кую, ма́ма, ма́сло, мі́сто, о́ко, та́то, тут) actually appear in the content.

```diff
# In the vocab-in-content checker:
+ import unicodedata
+ def strip_stress(text):
+     return unicodedata.normalize('NFD', text).replace('\u0301', '')
+
- if lemma in content_text:
+ if strip_stress(lemma) in strip_stress(content_text):
```

### Fix 5: Migrate to New Template Architecture (Priority: LOW)

**Prevents:** Prompt bloat, inconsistent quality gates
**Scope:** All beginner modules
**Template file:** content-prompt.md → beginner-content.md

This module was built with the OLD inline template (846 lines). The new architecture uses `{QUALITY_DIMENSIONS}` and `{PREFLIGHT_INSTRUCTIONS}` placeholders, which are shorter and more consistent. Rebuild with the new template to verify the new architecture works for alphabet modules.

---

## AGREEMENT_ERROR (Deterministic Issue)

The screen-result flags: `Agreement mismatch: 'Приголосні́' (p) + 'го́лос' (m)` at ~line 47.

**Verdict: False positive.** Line 47 reads: "**Приголосні́** means «along with the vowels», showing that they need a vowel..." — this is an etymology explanation, not a grammatical agreement. The word **приголосні́** is derived from **го́лос** but they don't need to agree grammatically in this context. The agreement checker is pattern-matching adjacent words incorrectly.

---

## Summary

**Template health:** NEEDS WORK

**Top 3 fixes by leverage:**
1. **Fix 1: Restructure letter sections** — eliminates 4 CONTENT_REDUNDANCY violations, applicable to M1-M4 alphabet/phonology modules
2. **Fix 4: Stress-mark normalization in validator** — eliminates false VOCAB_NOT_IN_CONTENT failures across ALL modules using stress marks
3. **Fix 2: Resolve dialogue contradiction** — clarifies allowed dialogue format for verb-free modules, improves richness scores

**Overall assessment:** Gemini produced solid, pedagogically appropriate content. The 5 validation failures are all systemic (template structure + validator bugs), not content quality issues. The build itself is PASS-worthy; the validate phase blocked on issues that need tooling/template fixes rather than content rewrites.
