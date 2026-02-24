<!-- content-hash: 238a80a8475f -->
**Reviewed-By:** claude-opus-4-6

# Phase D.1 Review: Bigger, Better, Stronger (a2-18)

---

## Scores

| # | Dimension | Score | Key Evidence |
|---|-----------|-------|--------------|
| 1 | Language Quality | 7/10 | Bookish Latinate "контрастувати ідеї" (L18); semantically implausible «Її стрибок став гнучкі́шим» (L287); awkward calque «його час був швидки́й» (L279) |
| 2 | Lesson Quality | 8/10 | Sports commentator persona is engaging; good arc from theory to practice; but long presentation block (L52–143) before first real practice section (L227) |
| 3 | Factual Accuracy | 7/10 | Wrong morphological formula on L114: "тих + ш + іш + ий" (impossible double suffix); misleading section header "Зміна х → ш" contains NO actual alternation example; inaccurate phonological claim on L101 |
| 4 | Immersion Balance | 9/10 | 52.9% Ukrainian, well within 50-60% target; English scaffolding present for all grammar explanations; gradual immersion increase toward section «Практика: Рекорди України» |
| 5 | Richness | 6/10 | 74% vs 95% threshold; gaps: examples 14/24, dialogues 0/4 (formatting issue — dialogues exist but may not be detected), tables 1/2 |
| 6 | Humanity & Warmth | 8/10 | Good welcome ("Ласкаво просимо"), persona maintained, callout boxes engaging; but limited "You've got this" moments mid-lesson; no explicit "don't worry" encouragement |
| 7 | LLM Fingerprint | 8/10 | Section openings sufficiently varied; no "це не просто" patterns; two [!fact] callouts (not 3+); example at L287 is implausible (gymnast's jump called "more flexible") |
| 8 | Activity Quality | 6/10 | **Vocabulary file catastrophically wrong** (contains іменник/дієслово instead of comparatives); cloze blank 6 "М'яч сьогодні легший" is implausible; otherwise good variety (11 activities) |
| 9 | Plan Compliance | 6/10 | Vocabulary YAML has zero overlap with plan's 14 required items; all 5 content sections present; richness gaps unresolved |

---

## Critical Issues Found

### CRITICAL-1: Vocabulary File Contains Wrong Content (vocabulary YAML)

**Severity:** Critical — module deliverable is broken  
**Location:** `vocabulary/bigger-better-stronger.yaml` lines 1–10

The vocabulary file contains exactly 2 items:
- `lemma: "іменник"` (noun — a grammar term)
- `lemma: "дієслово"` (verb — a grammar term)

These have **zero relevance** to a module about comparative adjectives. The plan (`vocabulary_hints.required`) specifies 14 required items: більший, менший, кращий, гірший, вищий, нижчий, дорожчий, дешевший, старший, молодший, довший, коротший, ширший, вужчий, ніж — plus 5 recommended items (за, набагато, трохи, значно, швидший). None appear in the vocabulary YAML.

**Fix:** Regenerate the entire vocabulary file with all 14 required + 5 recommended comparative forms, including IPA, part of speech, grammatical notes (e.g., stem alternation type), and collocations as specified in the plan.

---

### CRITICAL-2: Wrong Morphological Formula (content L114)

**Severity:** Critical — factual error in grammar explanation  
**Location:** `bigger-better-stronger.md` line 114

The content shows:
> «ти́хий (quiet) → тих + ш + іш + ий → ти́хіший (quieter)»

The formula "тих + ш + іш + ий" is **morphologically impossible** — it stacks two suffixes (-ш- AND -іш-) which contradicts the module's own teaching that these are alternative suffixes. The correct decomposition is:

**тих + іш + ий = тихіший** (using the -іш- suffix only)

The note on line 115 correctly states: «слово тихий використовує суфікс -іш-, тому тут немає чергування!» — but this directly contradicts the formula one line above. An A2 learner trying to follow the morphological breakdown will be confused.

**Fix:** Change the formula on L114 to: `тих + іш + ий = тихіший` (removing the spurious -ш-).

---

### CRITICAL-3: Section "Зміна х → ш" Contains No Actual Alternation (content L113–115)

**Severity:** Significant — misleading structure  
**Location:** `bigger-better-stronger.md` lines 113–115

Section «Презентація: Творення ступенів» subsection "3. Зміна х → ш:" (line 113) presents тихий → тихіший as its only example. However, the note on line 115 explicitly states this word does NOT undergo alternation. This means the subsection titled "Зміна х → ш" provides **zero examples of the х → ш alternation it promises.**

This creates a structural contradiction: the header says "х changes to ш" but the only example shows no change. An A2 learner will be rightfully confused about whether х → ш alternation exists at all.

**Fix:** Either (a) add a genuine х → ш example (e.g., сухий → сухіший as a regular form, or тихий → тихший as the theoretical alternated form that doesn't actually occur, explaining WHY it doesn't) or (b) restructure this subsection as a "Watch out — not all consonants alternate" warning, removing it from the numbered alternation list.

---

### SIGNIFICANT-4: Semantically Implausible Example (content L287)

**Severity:** Significant — naturalness  
**Location:** `bigger-better-stronger.md` line 287

> «Її стрибок став гнучкі́шим.» (Her jump became more flexible.)

A gymnast's jump is not described as "flexible" in Ukrainian (or English). The gymnast herself is гнучка; a jump would be described as «складніший» (more complex), «впевненіший» (more confident), or «вищий» (higher). This reads as an AI-generated sentence that mechanically applied the comparison target without considering semantic plausibility.

**Fix:** Replace with a natural sports comparison, e.g., «Її стрибок став ви́щим.» (Her jump became higher.) or «Її програма стала складні́шою.» (Her routine became more complex.)

---

### SIGNIFICANT-5: Cloze Activity Implausible Blank (activities L363, blank 6)

**Severity:** Significant — activity naturalness  
**Location:** `activities/bigger-better-stronger.yaml` lines 362–406 (cloze blank 6)

The cloze passage reads: «М'яч сьогодні {{6}}» with expected answer «легший» (lighter). In sports commentary, a ball does not become lighter during a match. This is semantically implausible and will confuse learners trying to imagine the scenario.

**Fix:** Replace with a plausible sports attribute. E.g., change the sentence to «М'яч сьогодні {{6}} за рахунок нового покриття» with answer «легший» (making it about a new ball model), or change to a different attribute entirely, e.g., «Удар сьогодні {{6}}» → «сильніший».

---

### MODERATE-6: Bookish Latinate Verb in Ukrainian (content L18)

**Severity:** Moderate — naturalness  
**Location:** `bigger-better-stronger.md` line 18

> «Він допомагає нам робити вибір, контрастувати ідеї та описувати зміни.»

The verb «контрастувати» is a bookish Latinate borrowing that A2 learners should not encounter as unmarked vocabulary. Natural Ukrainian alternatives: «протиставляти ідеї» or «порівнювати ідеї». Using an unnecessarily elevated register in an A2 module violates the principle of simple vocabulary for beginners.

**Fix:** Replace «контрастувати ідеї» with «порівнювати ідеї» or «протиставляти ідеї».

---

### MODERATE-7: Richness Gaps Below Threshold (content-wide)

**Severity:** Moderate — structural  
**Location:** Content-wide

Richness is at 74% against a 95% threshold. Specific gaps:
- **Examples:** 14/24 — need ~10 more worked examples across sections
- **Dialogues:** 0/4 (format detection issue — there are 2 dialogue blocks in section «Діалоги та Висновки» but they may not use the expected markup; regardless, the plan calls for more applied dialogue throughout)
- **Tables:** 1/2 — only the Big 10 table exists. Section «Структури порівняння: ніж vs за» would benefit from a comparison table contrasting ніж vs за constructions side-by-side.

**Fix Plan for richness:**
1. Add a **comparison table** in section «Структури порівняння: ніж vs за» showing ніж vs за side by side with the same sentences (e.g., "Київ більший, ніж Львів" / "Київ більший за Львів") — closes tables gap (1→2)
2. Add **4-5 worked examples** in section «Презентація: Творення ступенів» showing full sentence context for -ш- suffix forms (currently only 2 example sentences at L86-87) — partially closes examples gap
3. Add **3-4 inline examples** in section «Структури порівняння: ніж vs за» for intensifiers (currently only 1 per intensifier) — further closes examples gap
4. Add a **short mini-dialogue** in section «Практика: Рекорди України» (e.g., two friends comparing landmarks) — closes dialogue gap
5. Ensure existing dialogues in section «Діалоги та Висновки» use consistent formatting that the audit pipeline can detect

---

### MODERATE-8: Inaccurate Phonological Claim (content L101)

**Severity:** Moderate — factual  
**Location:** `bigger-better-stronger.md` line 101

> «Зверніть увагу, що ж та ш зливаються у плавний звук жч.»

The claim that "ж and ш merge into a smooth sound жч" is phonologically misleading. The actual process is: г undergoes alternation to ж before the suffix -ш-, producing the cluster жч (from г+ш → жч). The characters ж and ш don't "merge" — rather, the г changes first, then combines with ш. For A2 pedagogy, a simpler formulation would be more accurate.

**Fix:** Rephrase to: «Зверніть увагу: літера г спочатку змінюється на ж, а потім у поєднанні з суфіксом -ш- утворює звук жч.»

---

## Factual Verification

### Grammar Rule Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| -іш- stress falls on і | L67–68 | **Correct** — standard pattern |
| стари́й → ста́рший with -ш- | L79 | **Correct** |
| г → ж, к → ч, х → ш alternations | L92–95 | **Correct** (alternation rules) |
| тих + ш + іш + ий → тихіший | L114 | **WRONG** — impossible double suffix; should be тих + іш + ий |
| ніж requires matching cases on both sides | L154 | **Correct** |
| за requires Accusative case | L171 | **Correct** |
| більш кращий is ungrammatical | L40 | **Correct** — double comparative error |
| Comma before ніж is mandatory | L166 | **Correct** — Ukrainian punctuation rule |
| швидкий → швидший (к drops) | L107–108 | **Correct** (simplified explanation but accurate result) |

### Factual Claims in Callout Boxes

| Claim | Location | Verdict |
|-------|----------|---------|
| Kyiv TV Tower is 385 meters | L234 | **Correct** — verified height |
| Batkivshchyna-Maty is 102m with sword | L238 | **Approximately correct** — total height with pedestal and sword ~102m |
| Statue of Liberty is 93m | L238 | **Approximately correct** — 93m including pedestal |
| Hoverla is 2061m | L246 | **Correct** |
| Mont Blanc is 4809m | L246 | **Correct** |
| Dnipro is 981km within Ukraine | L251 | **Correct** |
| Desna is 591km within Ukraine | L251 | **Plausible** — approximately correct |
| Proverbs are authentic Ukrainian | L23–24 | **Correct** — both are well-known Ukrainian proverbs |

### Colonial Framing Check

**No colonial framing detected.** The content compares Ukrainian with English throughout (appropriate for L2 English→Ukrainian). No "Unlike Russian..." patterns, no Russian as baseline. All comparisons use Ukrainian landmarks as the primary frame, with international comparisons as secondary.

---

## "Would I Continue?" Test (Beginner Safety)

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | **Pass** | English scaffolding throughout; grammar explained clearly |
| Were instructions clear? | **Pass** | Consistent structure, clear formulas |
| Did I get quick wins? | **Pass** (marginal) | Examples follow each concept; but first full practice section starts at L227 (~65% through content) |
| Was Ukrainian scary? | **Pass** | Gentle introduction, always with translations |
| Would I come back tomorrow? | **Pass** | Sports commentator persona is fun and engaging |

**Result:** 5/5 Pass → Lesson Quality baseline: 10/10, adjusted down to 8/10 for structural pacing issue (long presentation before practice).

---

## Verification Summary

### What Works Well

1. **Sports commentator persona** is consistently maintained from section «Вступ: Арена порівняння» through section «Діалоги та Висновки» — engaging and fun for A2 learners
2. **The Big 10 table** (L125–137) in section «Презентація: Творення ступенів» is clean, well-organized, and covers all essential suppletive forms
3. **Error prevention pedagogy** is excellent — the "Double Comparative Trap" (L37–48) and "Pronoun Danger Zone" (L199–200) in section «Структури порівняння: ніж vs за» anticipate real learner errors
4. **Proverb integration** in section «Вступ: Арена порівняння» (L23–24) is culturally authentic and pedagogically effective
5. **Intensifier section** (L202–224) in section «Структури порівняння: ніж vs за» covers набагато/значно/трохи with clear examples and natural collocations
6. **Activity variety** is strong: 11 activities spanning match-up, quiz, fill-in, unjumble, true-false, error-correction, group-sort, mark-the-words, cloze, and select types
7. **Dual comparative** чим...тим... construction (L220–224) adds elegant advanced structure

### What Needs Fixing

| Priority | Issue | Impact |
|----------|-------|--------|
| **P0** | Vocabulary YAML completely wrong (іменник/дієслово instead of comparatives) | Module deliverable broken |
| **P0** | Wrong morphological formula L114 (тих + ш + іш + ий) | Factual error in grammar lesson |
| **P1** | Section "Зміна х → ш" has no actual alternation example | Misleading structure |
| **P1** | Richness at 74% (needs 95%) — examples, dialogues, tables all below threshold | Audit gate FAIL |
| **P2** | Implausible example L287 (jump becoming "more flexible") | Naturalness |
| **P2** | Cloze blank 6 implausible (ball becoming lighter) | Activity naturalness |
| **P2** | Bookish "контрастувати" at L18 | Register mismatch for A2 |
| **P3** | Phonological claim L101 (ж та ш "merge") is imprecise | Minor factual |

---

## Fix Plan

### Phase 1: Critical Fixes

1. **Regenerate vocabulary YAML** — Replace entire file with 14 required + 5 recommended items per plan, including IPA, pos, grammatical notes, and collocations
2. **Fix L114** — Change formula from "тих + ш + іш + ий" to "тих + іш + ий"
3. **Restructure L113–115** — Either add a real х → ш example or reframe as a "no alternation" warning

### Phase 2: Richness Boost

4. **Add ніж vs за comparison table** in section «Структури порівняння: ніж vs за» (after L163)
5. **Add 5+ worked example sentences** in section «Презентація: Творення ступенів» (after L86 for -ш- forms)
6. **Add mini-dialogue** in section «Практика: Рекорди України» (e.g., tourist guide comparing Hoverla and Mont Blanc)
7. **Add 3-4 intensifier examples** in section «Структури порівняння: ніж vs за» (L205–215)

### Phase 3: Naturalness Fixes

8. **Replace L287** — «Її стрибок став гнучкі́шим» → «Її стрибок став ви́щим»
9. **Fix cloze blank 6** — Replace "М'яч сьогодні легший" with plausible sports comparison
10. **Replace L18** — «контрастувати ідеї» → «порівнювати ідеї»
11. **Rephrase L101** — Clarify the г→ж phonological process

---

## Verdict

**FAIL — Requires D.2 Targeted Repair**

The prose content is fundamentally solid with an engaging persona and good pedagogical structure across all five sections. However, three issues prevent passing:

1. **Vocabulary YAML is completely wrong** — This is a build error, not a content quality issue, but the deliverable is broken
2. **Factual error in morphological formula** (L114) must be corrected before learners see it
3. **Richness at 74%** requires structural additions (table, examples, mini-dialogue) to reach the 95% gate

After D.2 repairs addressing the fix plan above, this module should pass audit cleanly. The underlying content quality is strong.