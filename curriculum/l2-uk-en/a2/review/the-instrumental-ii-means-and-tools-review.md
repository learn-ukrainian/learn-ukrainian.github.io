<!-- content-hash: c028eab6ad6b -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Plan Compliance | 8/10 | All 5 plan sections present as H2 headers. All required vocabulary covered. However, the meta-specified persona "Hutsul Craftsman" is completely absent — zero trace in the prose. |
| 2 | Language Quality | 7/10 | Ukrainian is mostly correct but «працювати комп'ютером» (lines 114, 120, 234) is an unnatural collocation — standard Ukrainian uses "працювати на/за комп'ютером." «креслити кольоровим олівцем» (line 137) misuses "креслити" (technical drafting) for children's drawing. English is over-academic for A2 learners with excessive intensifiers. |
| 3 | Factual Accuracy | 7/10 | Activities mark "на метро" and "на таксі" as incorrect options (activity lines 24, 45, 606), but both are standard, widely-used Ukrainian. This is a factual overclaim that will confuse learners who hear "на метро" from every native speaker. |
| 4 | Lesson Quality | 7/10 | No warm greeting or "today you'll learn" preview for the learner. Minimal encouragement throughout. English explanatory prose is dense and verbose — not the patient, simple B1-readability tutor tone required for A2. 2/5 on "Would I Continue?" test (no quick wins early, overwhelming instructions). |
| 5 | Immersion | 9/10 | 50.6% measured — within the 50-60% Band 1 target for A2. Good balance of English theory and Ukrainian examples. |
| 6 | Richness | 8/10 | Night train cultural context is authentic and well-integrated. 7 varied callout boxes. Good vocabulary breadth. Missing: the Hutsul Craftsman persona that would have given the module a unique voice. |
| 7 | Activity Quality | 7/10 | 12 activities with good type variety (fill-in, match-up, quiz, true-false, unjumble, error-correction, group-sort, mark-the-words, cloze, select). But "на метро" / "на таксі" treated as wrong in 3+ items. |
| 8 | LLM Fingerprint | 7/10 | «це не просто рух» cliché at line 68. Heavily padded English prose with stacked intensifiers ("absolutely crucial", "strictly and uncompromisingly demand", "structurally fascinating"). Implausible example sentences at lines 206, 217. |
| 9 | Humanity & Warmth | 6/10 | No opening greeting. Zero "don't worry" moments. Zero "you've got this" encouragements. The only progress marker is in the final paragraph (line 246). Module reads like a dense academic textbook, not an encouraging tutor. <3 markers → COLD_PEDAGOGY threshold hit. |

---

## Critical Issues Found

### Issue 1: FACTUAL — "на метро" / "на таксі" incorrectly marked as errors (CRITICAL)

**Location:** Activities file lines 24, 45, 334, 355, 606; Content file line 88

**Evidence:** In the fill-in activity (line 23-25):
```yaml
- sentence: "Він швидко дістався на вокзал _____."
  answer: "метро"
  options:
    - "метро"
    - "метром"
    - "на метро"    ← marked wrong
```

In the final quiz (line 601-607):
```yaml
- text: "Ми подорожуємо на метро."
  correct: false    ← marked wrong
```

**Problem:** "їхати на метро" and "їхати на таксі" are standard, everyday Ukrainian constructions used by the vast majority of native speakers. Presenting them as errors is factually incorrect and will actively confuse learners who encounter "на метро" in every real-world context. The module should teach both the bare form and the "на + noun" construction as acceptable, while emphasizing that the word form doesn't change.

**Fix:** Accept "на метро" and "на таксі" as valid alternatives across all affected activity items. Adjust content file table (line 88) to note both forms.

---

### Issue 2: NATURALNESS — «працювати комп'ютером» is not standard Ukrainian (CRITICAL)

**Location:** Content file lines 114, 120, 234; Vocabulary file line 89

**Evidence (line 120):** «Мій старший брат цілий день ефективно працює новим комп'ютером.»

**Evidence (line 234):** «Потім я довго працюю **комп'ютером** і роблю нові документи.»

**Problem:** Native Ukrainian speakers say "працювати **на** комп'ютері" (locative) or "працювати **за** комп'ютером" (instrumental with preposition). The bare instrumental "працювати комп'ютером" treats the computer as a hand tool like a hammer or pen — which is semantically wrong. A computer is a workstation you sit AT, not an instrument you wield. This collocation appears 3 times and is taught as standard, which will lead learners to produce unnatural sentences.

**Fix:** Replace "працювати комп'ютером" with "користуватися комп'ютером" (which IS natural bare instrumental), or use "працювати за комп'ютером" and note the preposition.

---

### Issue 3: WARMTH — No warm opening, minimal encouragement (MAJOR)

**Location:** Content file lines 1-12

**Evidence (line 10-12):**
```
> **Чому це важливо?**
> In Ukrainian, grammar is incredibly efficient...
```

**Problem:** The module opens with a dense English paragraph about grammar efficiency — no greeting, no "Привіт!", no learning objectives preview. There are zero "don't worry" or "you can do this!" encouragement beats throughout the module body. The only warmth appears in the final paragraph «Ви вже успішно опанували» (line 246). For an A2 module where learners are still building confidence, this COLD_PEDAGOGY pattern is a significant issue.

**Fix:** Add a warm greeting and learning preview at the top. Insert ≥3 encouragement phrases throughout (after each major section's practice, before difficult concepts).

---

### Issue 4: LANGUAGE — «креслити кольоровим олівцем» misuses "креслити" (MAJOR)

**Location:** Content file line 137

**Evidence:** «Маленькі діти дуже люблять креслити кольоровим олівцем на білому папері.»

**Problem:** "Креслити" means "to draft" (technical drawing, blueprints). Children don't "draft" — they "малюють" (draw). This is a vocabulary misuse. The English translation "to draft with a colored pencil" even highlights the awkwardness.

**Fix:** Replace "креслити" with "малювати" — «Маленькі діти дуже люблять малювати кольоровим олівцем на білому папері.»

---

### Issue 5: LLM FINGERPRINT — Implausible overloaded example sentences (MAJOR)

**Location:** Content file lines 206, 217

**Evidence (line 217):** «Я абсолютно щодня активно користуюся **робочим комп'ютером**.»

No native speaker stacks "абсолютно щодня активно" — three adverbs qualifying a single verb. This is LLM padding.

**Evidence (line 206):** «Справжній музикант глибоко слухає складну мелодію своїми вухами, а не серцем.»

This is semantically bizarre — the sentence argues a real musician listens with ears, not heart, which contradicts the universal musical cliché "listen with your heart." As a grammar example it's forced and confusing.

**Fix:** Simplify line 217 to "Я щодня користуюся робочим комп'ютером." Replace line 206 with a natural body-as-instrument example like "Музикант уважно слухає мелодію вухами."

---

### Issue 6: PERSONA — Hutsul Craftsman persona completely absent (MINOR)

**Location:** Entire content file

**Evidence:** Meta file specifies `persona: voice: Encouraging Cultural Guide, role: Hutsul Craftsman`. Grep for "Hutsul", "гуцул", "craftsman", "майстер" in the content file returns zero matches. The module reads as a generic grammar textbook with no character voice.

**Fix:** Weave in the craftsman persona through framing — e.g., tools section could reference Hutsul woodcarving traditions, the cultural context could include Carpathian craft tools.

---

### Issue 7: ENGLISH VERBOSITY — Prose is too academic for A2 learners (MINOR)

**Location:** Content file lines 126, 174, 193, 212

**Evidence (line 174):** "As you naturally progress to building significantly more complex sentences in Ukrainian, it becomes absolutely crucial to clearly understand which specific questions trigger which underlying grammatical structures."

**Evidence (line 212):** "certain highly frequent, core vocabulary verbs strictly and uncompromisingly *demand* the Instrumental case to complete their basic semantic meaning"

**Problem:** This English prose is C1-level academic writing, not the B1-readability required for A2 learners. Stacked intensifiers ("absolutely crucial", "strictly and uncompromisingly") add cognitive load without teaching value.

**Fix:** Simplify to direct, short English sentences. "It's important to understand which question to use" instead of the 40-word construction at line 174.

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| Instrumental case without preposition for means/tools (§4.2.2.5.1) | Line 19, research line 4 | CORRECT — matches State Standard |
| "метро" and "таксі" are indeclinable | Lines 80-82 | CORRECT — these words don't take endings |
| "Я їду метро" is the ONLY correct form (implies "на метро" is wrong) | Line 88, activities | OVERCLAIM — both forms are standard |
| "-ець" nouns take "-ем" ending (олівцем) | Lines 126-133 | CORRECT |
| "ж" triggers "-ем" ending (ножем) | Line 145 | CORRECT |
| "користуватися" requires instrumental | Lines 216-217 | CORRECT |
| "працювати комп'ютером" as standard | Lines 114, 120, 234 | QUESTIONABLE — "на/за комп'ютером" is standard |
| "очима" as instrumental plural of "око" | Line 198 | CORRECT |
| Night train cultural tradition (Укрзалізниця) | Lines 66-75 | CORRECT — well-documented cultural practice |
| «Я йду з ручкою» means walking alongside a pen "holding its hand" | Line 31 | OVERCLAIM — "з ручкою" simply means "carrying a pen", not anthropomorphic companionship |

---

## Verification Summary

**Sections verified:** All 5 H2 sections read in full:
- Section «Вступ: Без прийменника «з»» — Lines 14-44. Good core concept presentation but overwrought absurd-image explanation at line 31.
- Section «Транспорт і рух» — Lines 46-104. Good cultural hook with night train. Factual overclaim on "на метро" being wrong. Dialogue is natural and well-constructed.
- Section «Інструменти та знаряддя» — Lines 105-170. Solid tool vocabulary. "працювати комп'ютером" naturalness issue. "креслити" misuse at line 137. Good soft-stem drill.
- Section «Питання та відповіді» — Lines 171-226. Useful Як/Чим distinction. Body parts section is good concept but has implausible example at line 206. Verb collocation section is sound except "працювати" issue.
- Section «Практика та підсумок» — Lines 227-269. Production text at line 233-234 is effective but repeats "працювати комп'ютером" problem. Summary is adequate but lacks warmth/celebration tone.

**Activities verified:** All 12 activities examined item by item. Core pedagogical flow is sound. Type variety is excellent. 3 activity items contain "на метро"/"на таксі" wrongly marked as incorrect. Activity title «У моїй майстерні» (line 63) is grammatically correct.

**Vocabulary verified:** All 25 items present with IPA, translations, examples. Two IPA issues: "користуватися" has double stress mark [kɔˈrɪstuˈʋɑtɪsʲɑ] (line 147 in vocab file — should have single stress on "ва"); "комп'ютер" missing palatalization [kɔmˈpjutɛr] (line 85 — should be [kɔmˈpʲjutɛr]).

**Citation verification:** All «»-quoted Ukrainian text in this review was copy-pasted from Read output and verified via Grep.

---

## Verdict

**FAIL — Requires D.2 targeted repair.**

The module has a solid structural foundation — all plan sections are present, vocabulary coverage is complete, activity variety is excellent, and the immersion ratio is on target. The night train cultural hook and the soft-stem "олівцем" drill are genuine pedagogical strengths.

However, three issues require repair before passing:

1. **Factual accuracy:** "на метро" / "на таксі" must not be marked as incorrect in activities — this is a factual error that will confuse every learner who interacts with native speakers.
2. **Naturalness:** "працювати комп'ютером" must be replaced with natural collocations ("користуватися комп'ютером" or "працювати за/на комп'ютером").
3. **Warmth:** The module needs a warm greeting, learning preview, and ≥3 encouragement beats to meet A2 emotional safety requirements. Current state hits COLD_PEDAGOGY threshold.

Secondary repairs: fix "креслити" → "малювати" for children (line 137), simplify overloaded example sentences (lines 206, 217), fix двоє IPA stress errors in vocabulary, and reduce English prose verbosity throughout.