**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | **Plan Compliance** | 5/10 | Vocabulary sidecar contains 0/8 required verbs from plan; TTT pedagogy not implemented (no diagnostic test); модальне дієслово "могти" entirely absent from prose; euphonic rules (у/в, і/й) promised in plan but never taught |
| 2 | **Immersion Balance** | 3/10 | Pre-computed 14.7% against 35-55% target. A1.3 Consolidation phase should scaffold toward Ukrainian dominance. Module is overwhelmingly English with Ukrainian confined to isolated example lines |
| 3 | **Language Quality** | 7/10 | Ukrainian examples are grammatically correct; English is clear and accessible. Minor naturalness issue: «Він роб__ смачну каву» (line 59 activities) — "робити каву" is a calque; natural Ukrainian is "варити каву". No Russianisms found. No word salad |
| 4 | **Lesson Quality** | 6/10 | "Would I Continue?" test: 3/5 Pass. Pacing is comfortable (Pass), instructions are clear (Pass), quick wins present via self-checks (Pass). But Ukrainian is NOT introduced gently — it barely appears at all (Fail). Middle sections feel like a textbook, not a tutor (Fail) |
| 5 | **Activity Quality** | 5/10 | «Числа від 1 до 8» match-up (lines 1-20 activities) is entirely off-topic — numbers are nowhere in the plan, objectives, or content. 7/8 remaining activities are solid. Activity-content mirroring is weak: unjumble sentence «Де твоя нова машина?» doesn't appear in the content |
| 6 | **Factual Accuracy** | 8/10 | The 1934 Paris linguistic contest claim (line 43) is correctly hedged as "a legend" and "historians argue about the accuracy." Grammar rules are accurate. One minor issue: line 48 says Ї is "always two sounds [ji]" but describes it as sounding like "ye" in "yeast" — [ji] ≠ [je], this is a misleading phonetic analogy |
| 7 | **Richness & Engagement** | 7/10 | 5 engagement boxes ([!note], [!culture], [!warning], [!tip], [!myth-buster]) — adequate variety. Cultural hooks present (Paris contest, Ви respect). But engagement is front-loaded: sections «Навичка 3: Система дієслів» and «Навичка 4: Система відмінків» have zero callout boxes between them |
| 8 | **LLM Fingerprint** | 7/10 | Structural monotony: 4/5 "Навичка" sections follow identical Model → Practice → Self-Check with the same sub-heading format. Example batching: all 5 skill sections present Ukrainian examples in identical bold+italic bullet format. Section openings use a metaphor-then-explanation pattern uniformly. Not egregious but clearly template-generated |
| 9 | **Humanity & Warmth** | 6/10 | Encouragement concentrated at bookends (lines 13, 291, 299-301). Middle sections «Навичка 2: Рід та узгодження» through «Навичка 4: Система відмінків» read as clinical textbook instruction with no "Great!", "Don't worry", or "You've got this!" moments. Direct address ("you") is present but warmth markers are sparse: ~2 encouragement phrases total in the body |

**Weighted Average: ~6.0/10**

---

## Critical Issues Found

### Issue 1: CRITICAL — Vocabulary Sidecar Contains Zero Required Verbs
**Location:** `vocabulary/checkpoint-core-grammar.yaml` (all 8 items)
**Evidence:** The plan (`plans/a1/checkpoint-core-grammar.yaml`, lines 53-69) requires these verbs as `vocabulary_hints.required`: бути, мати, хотіти, могти, йти, знати, робити, говорити. The vocabulary sidecar instead contains meta-linguistic terms: іменник, дієслово, прикметник, множина, однина, відмінок, рід, час. None of the 8 required verbs appear. Grep for `могти|хотіти` against the vocab file returns zero matches.
**Impact:** Complete plan vocabulary violation. Learners get grammatical terminology they won't actively use instead of the high-frequency verbs central to A1 competency.
**Fix:** Replace all 8 vocabulary entries with the plan-required verbs (бути, мати, хотіти, могти, йти, знати, робити, говорити) with proper IPA, collocations from the plan's vocabulary_hints, and usage notes.

### Issue 2: CRITICAL — Immersion at 14.7% (Target: 35-55%)
**Location:** Entire content file — all H2 sections
**Evidence:** Pre-computed audit shows 14.7% Ukrainian immersion. Even allowing for a checkpoint module where grammar theory is in English, the Ukrainian text is confined to isolated bolded example phrases. Entire paragraphs in sections «Огляд: Граматичний чекпоінт», «Навичка 1: Читання та вимова», «Навичка 2: Рід та узгодження», «Навичка 3: Система дієслів», «Навичка 4: Система відмінків» are pure English prose.
**Impact:** A1.3 phase (Consolidation) should be scaffolding toward Ukrainian dominance. At 14.7%, the learner gets almost no Ukrainian reading practice in a module about reading fluency.
**Fix:** Add Ukrainian mini-dialogues, Ukrainian instructions for practice sections, Ukrainian section summaries, and Ukrainian self-check prompts. Transform "Read this text aloud" sections into extended Ukrainian passages. Target 40-45% immersion minimum for a grammar checkpoint.

### Issue 3: CRITICAL — Off-Topic Activity "Числа від 1 до 8"
**Location:** `activities/checkpoint-core-grammar.yaml`, lines 1-20
**Evidence:** Activity title «Числа від 1 до 8» with instruction «З'єднайте число з його назвою» tests number-word matching (один, два, три...). Grep for `числ|один|два|три|чотири` against the content file returns zero matches. Numbers are not in the plan objectives, content_outline, or vocabulary_hints. The plan focus is "checkpoint" covering reading, gender, verbs, and cases.
**Impact:** 1 of 8 activities (12.5%) tests knowledge completely outside module scope. Wastes learner time and breaks diagnostic validity.
**Fix:** Replace with a grammar-relevant activity — e.g., a match-up for gender identification (noun → masculine/feminine/neuter) or verb infinitive → conjugation group matching.

### Issue 4: SERIOUS — TTT Pedagogy Not Implemented
**Location:** Section «Огляд: Граматичний чекпоінт» (line 23) and all skill sections
**Evidence:** The plan specifies `pedagogy: TTT` and explicitly states: "Structure: Diagnostic Task (Test) -> Remediation (Teach) -> Final Challenge (Test)." The content at line 23 describes itself as: "first recall the rule (Teach), look at typical mistakes, and then check if you understand them (Test)." This is Teach-Test. No diagnostic test precedes the teaching in any skill section. Each section goes straight to "Model" (teaching) → "Practice" → "Self-Check."
**Impact:** The TTT diagnostic approach would identify learner weaknesses before teaching, enabling targeted remediation. Without the initial diagnostic test, the checkpoint loses its diagnostic function.
**Fix:** Add a brief diagnostic prompt at the start of each skill section (e.g., "Before we review, try this: [Ukrainian exercise]") that tests the learner BEFORE the teaching begins. This fulfills the first "T" of TTT.

### Issue 5: SERIOUS — Modal Verb "могти" Absent from Content
**Location:** Entire content file
**Evidence:** Plan requires (line 40): "Практика вживання високочастотних модальних дієслів (могти, хотіти)". Grep for `могти|можу|можеш|можемо|можете|можуть` against the content file returns zero matches. The verb "хотіти" appears in section «Навичка 5: Практичні ситуації» (lines 231, 234-235), but "могти" is completely absent.
**Impact:** One of two explicitly required modal verbs has no coverage at all, despite being essential for A1 requests and politeness.
**Fix:** Add "могти" conjugation practice alongside "хотіти" in section «Навичка 3: Система дієслів» or «Навичка 5: Практичні ситуації», with examples like «Я можу допомогти», «Ви можете сказати?»

### Issue 6: SERIOUS — Euphonic Rules (у/в, і/й) Not Taught
**Location:** Section «Навичка 1: Читання та вимова»
**Evidence:** The plan's content_outline (lines 18-20) explicitly requires: "практичне значення евфонії та правил чергування у/в та і/й для мелодійності мовлення." Grep for `чергування|у/в|і/й` against the content file returns zero matches. The [!culture] box at line 42-43 mentions "melodic" language but never explains the actual euphonic alternation rules.
**Impact:** The euphonic rules (у/в, і/й alternation) are a distinctive feature of Ukrainian and a core reading/pronunciation skill. Missing them in a consolidation checkpoint creates a gap.
**Fix:** Add a subsection in «Навичка 1: Читання та вимова» teaching the у/в and і/й alternation rules with examples.

### Issue 7: MINOR — Misleading Phonetic Analogy for Ї
**Location:** Section «Навичка 1: Читання та вимова», line 48
**Evidence:** Content states: «Ї (Yi) — is always two sounds [ji]. It sounds like "ye" in the word "yeast".» The IPA transcription [ji] is correct, but the English analogy "ye" in "yeast" represents with a front vowel [i], whereas Ї represents [ji] where the second element is Ukrainian [i] (similar to English "ee" in "feet"). The "yeast" analogy works for the initial [j] but could mislead on the vowel quality.
**Impact:** Minor — learners might slightly mispronounce the vowel, though the IPA notation compensates.
**Fix:** Change analogy to: "It sounds like the 'yi' in 'yield'" or simply "like 'y' + 'ee'."

### Issue 8: MINOR — Activity Naturalness: "робити каву"
**Location:** `activities/checkpoint-core-grammar.yaml`, line 59
**Evidence:** Activity sentence «Він роб__ смачну каву» uses "робити каву" (to make coffee). Standard Ukrainian prefers "варити каву" (to brew coffee). "Робити каву" is a colloquial calque from English "make coffee."
**Impact:** Minor — the grammatical point (conjugation) is valid, but the collocation teaches an unnatural phrase.
**Fix:** Change to «Він вар__ смачну каву» (answer: ить, verb: варити, Group II) or use a different object: «Він роб__ домашнє завдання».

---

## Factual Verification

### Callout Box Verification

| Box | Location | Claim | Verdict |
|-----|----------|-------|---------|
| [!culture] "Music of the Language" | Line 42-43 | «in 1934 at a linguistic contest in Paris, the Ukrainian language was recognized as one of the most melodious in the world (after Italian)» | **HEDGED CORRECTLY** — text says "There is a legend" and "historians argue about the accuracy." Research notes confirm this is "widely cited" and "historically debated." No factual error. |
| [!warning] "Caution: Soft Sign" | Line 84-86 | Words ending in -ь can be masculine or feminine; examples: день, кінь (M), ніч, сіль (F) | **CORRECT** — all gender assignments verified. |
| [!tip] "Life Hack for Accusative" | Line 187-191 | Masculine inanimate nouns don't change in Accusative; feminine -а → -у, -я → -ю | **CORRECT** — standard A1 grammar rule, accurately stated. |
| [!myth-buster] "I will understand everything from context" | Line 258-260 | «"Мама любить доньку" and "Маму любить донька" are two completely different sentences» | **CORRECT** — demonstrates Nominative vs. Accusative distinction through word endings determining subject/object roles. |
| [!note] "Important Note" | Line 25-27 | English for grammar explanation, Ukrainian for examples | **ACCURATE** meta-description, though the module over-delivers on English and under-delivers on Ukrainian (see Immersion issue). |

### Grammar Rule Verification

| Rule | Location | Verdict |
|------|----------|---------|
| Gender endings: consonant (M), -а/-я (F), -о/-е (N) | Lines 80-82 | **CORRECT** |
| Adjective agreement: -ий (M), -а (F), -е (N), -і (Pl) | Lines 92-95 | **CORRECT** |
| Group I (-ати) conjugation: -ю, -єш, -є, -ємо, -єте, -ють | Lines 124-126 | **CORRECT** |
| Group II (-ити) conjugation: -лю, -иш, -ить, -имо, -ите, -лять | Lines 127-129 | **CORRECT** for "робити" specifically (роблю, робиш...). Note: the endings shown (-лю, -лять) reflect consonant mutation specific to "робити", not universal Group II endings. This could mislead for verbs like "вчити" (вчу, вчиш). |
| Past tense: -в (M), -ла (F), -ло (N), -ли (Pl) | Lines 135-138 | **CORRECT** |
| Future imperfective: буду + infinitive | Lines 142-146 | **CORRECT** |
| Accusative direction: feminine -а → -у | Lines 184-191 | **CORRECT** |
| Locative: банк → банку, школа → школі | Lines 197-198 | **CORRECT** |
| Genitive negation: час → часу, машина → машини | Lines 204-206 | **CORRECT** |

### Research Cross-Reference

The research notes confirm:
- The "Melodious Language" cultural hook (section 1 — used correctly with hedging)
- The Ви/ти politeness aspect (section 2 — present but insufficiently developed in content)
- All three common learner errors (section 3 — "To Be" trap, gender mismatch, direction vs. location — all present in content)

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Plan section coverage | **PARTIAL FAIL** | Plan sections covered thematically but meta-linguistic terms replace required vocabulary; "могти" verb entirely absent; euphonic rules (у/в, і/й) not taught |
| Vocabulary scope | **FAIL** | 0/8 required verbs in sidecar; 0/4 recommended verbs present |
| Grammar scope creep | **YES** | «Числа від 1 до 8» activity introduces content outside module scope |
| Objectives coverage | **PARTIAL** | 3/4 objectives addressed (reading fluency, gender agreement, verb conjugation, case application); case application is solid but verb section misses "могти" |
| TTT pedagogy | **NOT IMPLEMENTED** | Content uses Teach-Test, not Test-Teach-Test as specified |
| Immersion | **HARD FAIL** | 14.7% vs 35-55% target |
| Colonial framing | **CLEAN** | No Ukrainian-Russian comparisons found |
| Russianisms | **CLEAN** | No Russian ghost words detected |
| LLM fingerprint | **MODERATE** | Structural monotony in section format; uniform example presentation |
| Warmth | **WEAK** | Encouragement sparse in middle sections; functional but cold |
| Factual accuracy | **PASS** | All claims hedged or accurate; grammar rules correct |

### "Would I Continue?" Test (Beginner Safety)

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | **PASS** | Pacing is comfortable, digestible chunks |
| Were instructions clear? | **PASS** | Always knew what to do |
| Did I get quick wins? | **PASS** | Self-check sections provide validation |
| Was Ukrainian scary? | **FAIL** | Not scary because there's almost none. 14.7% immersion means the learner barely encounters Ukrainian. This is the opposite problem — too little exposure. |
| Would I come back tomorrow? | **BORDERLINE** | Middle sections feel like reading a textbook, not being tutored. Section «Навичка 5: Практичні ситуації» finally comes alive with dialogues, but learners may disengage before reaching it. |

**Result: 3/5 Pass → Lesson Quality 8/10 on the rubric, adjusted to 6/10 due to immersion failure making the "lesson" barely a Ukrainian lesson.**

---

## Section-by-Section Coverage

### Section «Огляд: Граматичний чекпоінт»
Warm opening that acknowledges the learner's journey (line 17). States the goal clearly. However, it describes TTT as "Teach then Test" (line 23), missing the diagnostic first Test. The [!note] box (line 25-27) correctly sets the English/Ukrainian expectation but the module doesn't deliver enough Ukrainian to match.

### Section «Навичка 1: Читання та вимова»
Covers tricky letters Ї, Щ, Ь well (lines 48-50). The reading passage (line 64) «Привіт! Мене звати Андрій. Я живу в Києві. Київ — це дуже гарне місто. Я люблю українську мову і хочу говорити вільно. Сьогодні гарний день!» is good practice. Missing: euphonic rules (у/в, і/й alternation) per plan requirement. The stress example «плачу́» vs «пла́чу» (line 61) is excellent.

### Section «Навичка 2: Рід та узгодження»
Gender rules clearly presented (lines 80-82). Agreement table (lines 92-95) is clean. The "Common Mistake" table (lines 102-106) with «Гарний книга» → «Гарна книга» is exactly what the plan requires. The hands-on exercise "Look around and name three objects" (line 109) is a strong pedagogical moment.

### Section «Навичка 3: Система дієслів»
Conjugation tables are clear (lines 124-129). The "To Be" trap (lines 150-156) — «Я є студент» → «Я студент» — is well executed and matches the plan's learner error focus. Missing: "могти" modal verb; Ви/ти social aspect gets only one sentence (line 131).

### Section «Навичка 4: Система відмінків»
Four cases well organized with clear questions (Хто? Що? / Куди? / Де? / Кого? Чого?). The direction vs. location contrast (lines 214-216) with «Я йду в парку» (wrong) vs «Я йду в парк» (correct) is effective. The Genitive negation examples (lines 204-206) are solid.

### Section «Навичка 5: Практичні ситуації»
Best section in the module. Three real-world scenarios with grammatical analysis inline. The café dialogue (lines 232-236) and navigation scene (lines 240-245) bring grammar to life. The myth-buster box (lines 258-260) with «Мама любить доньку» / «Маму любить донька» is excellent.

### Section «Інтеграційне завдання»
The integration dialogue (lines 278-282) is well-constructed, combining past tense (була), Locative (в магазині), Accusative (в театр), agreement (нову сукню), and Genitive (часу) in a natural conversation. This is the strongest pedagogical element.

### Section «Підсумок»
Provides closure and encouragement (lines 297-301). "You are ready to move on! Next stop — the coffee shop." is a good forward hook. "Do not be afraid to repeat" (line 299) is encouraging. Could be warmer in the middle of the journey.

### Section «Vocabulary»
Minimal — just a pointer to the sidecar (line 305-306). The sidecar itself is the wrong vocabulary set entirely (see Critical Issue 1).

---

## Verdict

**FAIL — Module requires significant revision before passing Phase D.**

### Blocking Issues (Must Fix)

1. **Replace entire vocabulary sidecar** — swap meta-linguistic terms for the 8 required verbs (бути, мати, хотіти, могти, йти, знати, робити, говорити) with proper IPA and collocations
2. **Raise immersion from 14.7% to ≥35%** — add Ukrainian dialogues, mini-exercises in Ukrainian, Ukrainian section summaries, and extended reading passages in each skill section
3. **Remove off-topic activity** «Числа від 1 до 8» — replace with grammar-relevant match-up (e.g., gender identification or case-question matching)
4. **Add "могти" to content** — include conjugation examples and practical usage in section «Навичка 3: Система дієслів» or «Навичка 5: Практичні ситуації»
5. **Add euphonic rules (у/в, і/й)** to section «Навичка 1: Читання та вимова» per plan requirement
6. **Implement TTT diagnostic test** — add a brief diagnostic exercise at the start of each skill section before teaching

### Non-Blocking Recommendations

- Add 2-3 warmth/encouragement markers to middle sections (e.g., between «Навичка 2» and «Навичка 4»)
- Fix "Ї sounds like 'ye' in 'yeast'" analogy (line 48) — "yield" is a better match for [ji]
- Fix «Він роб__ смачну каву» → «Він вар__ смачну каву» or use different object (activities line 59)
- Expand Ви/ти social grammar aspect beyond single-sentence mention (line 131)
- Vary section sub-heading structure to reduce template monotony