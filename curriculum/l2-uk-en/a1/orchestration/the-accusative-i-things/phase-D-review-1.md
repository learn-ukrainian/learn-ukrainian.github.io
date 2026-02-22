**Reviewed-By:** claude-opus-4-6

## Scores

| # | Dimension | Score |
|---|-----------|-------|
| 1 | Lesson Quality | 8 / 10 |
| 2 | Language Quality | 7 / 10 |
| 3 | Activity Quality | 8 / 10 |
| 4 | Richness | 8 / 10 |
| 5 | Humanity & Warmth | 8 / 10 |
| 6 | LLM Fingerprint | 8 / 10 |
| 7 | Factual Accuracy | 8 / 10 |
| 8 | Plan Compliance | 8 / 10 |
| 9 | Immersion Balance | 7 / 10 |
| 10 | Pacing & Cognitive Load | 7 / 10 |

**Weighted Average: 7.7 / 10**

---

## Critical Issues Found

### Issue 1 (CRITICAL): Grammar Scope Creep — Adjective Accusative in Shop Dialogue

**Location:** Section «Ситуація: У магазині та вдома», lines 329–332

The shop dialogue introduces accusative adjective agreement without any prior explanation:

- Line 329: «Газовану **воду**?» — accusative feminine adjective "газовану"
- Line 330: «Ні, звичайну **воду**.» — accusative feminine adjective "звичайну"
- Line 331: «Яку **шоколадку**? Чорну чи молочну?» — accusative interrogative pronoun "яку" plus accusative adjectives "чорну", "молочну"
- Line 332: «Чорну **шоколадку**.» — accusative feminine adjective again

This lesson explicitly teaches only **noun** endings in the accusative case. Adjective declension in the accusative is an entirely different grammar topic. An A1 learner who has just grasped that "книга → книгу" will now see "газована → газовану" and "яка → яку" with zero explanation, likely causing confusion or the false impression that they missed something.

**Fix:** Replace the dialogue with one using only bare nouns (no adjectives modifying accusative objects), or simplify so the adjectives are in nominative position. Example: the cashier could ask «Воду? Яку?» and the client could respond «Так, воду. І шоколадку.»

### Issue 2 (CRITICAL): Bazaar Phrases Use Untaught Grammar (Imperatives, Demonstratives)

**Location:** Section «Культурний погляд: Базар чи супермаркет?», lines 374–377

- Line 374: «Покажіть, будь ласка, цю диню» — imperative "Покажіть" + demonstrative pronoun accusative "цю"
- Line 375: «Дайте, будь ласка, грушу» — imperative "Дайте"
- Line 376: «Зважте, будь ласка, капусту» — imperative "Зважте"
- Line 377: «Я хо́чу спро́бувати смета́ну» — perfective infinitive "спробувати"

Imperative mood is not covered until later modules. The demonstrative pronoun "цю" (accusative of "ця") has not been taught. At A1, exposing learners to imperative constructions and demonstrative pronoun declension in a section labeled "cultural insight" creates cognitive overload. 

**Fix:** Either label these phrases explicitly as "phrases to recognize, not produce" with a note that imperatives will be taught later, or simplify to first-person constructions using taught grammar: «Я хочу диню», «Я хочу грушу», «Я хочу капусту».

### Issue 3 (MAJOR): Double Stress Marks on Two Words

**Location:** Section «Ситуація: У магазині та вдома» and «Культурний погляд: Базар чи супермаркет?»

Ukrainian words have exactly one stressed syllable. Two words have double stress marks:

- Line 343: «Я бачу **че́ргу́**.» — has stress on both "е" and "у". Correct: чергу́ (stress on final syllable only).
- Line 396: «Я купую **виши́ва́нку**.» — has stress on both "и" and "а". Correct: вишива́нку (stress on third syllable only).

**Fix:** Remove the spurious stress marks: «чергу́» and «вишива́нку».

### Issue 4 (MAJOR): Premature Exception — Feminine Consonant-Ending Nouns

**Location:** Section «Практика: Вчимося змінювати закінчення», line 245

«Я маю можли́вість» with the note: *(Feminine, but ends in a consonant, not -а/-я — no change!)*

The lesson explicitly teaches the rule: "Feminine -а → -у, -я → -ю." Immediately after presenting this clean rule, it introduces an exception (feminine nouns ending in a consonant that don't change in accusative) without flagging it as a special case for later study. A beginner will either:
- Become confused about when feminine nouns change
- Start second-guessing the rule they just learned

**Fix:** Either remove this example entirely, or explicitly mark it as a preview: "You'll learn more about this type of feminine noun later. For now, focus on -а/-я endings."

### Issue 5 (MINOR): Incorrect IPA Transcription

**Location:** Section «Теорія: Знахідний відмінок для неістот», line 211

«Я чую **звук** [zvuk].» — The transcription [zvuk] uses [v] for Ukrainian "в", which is incorrect. Ukrainian "в" is a labiodental approximant [ʋ]. The correct IPA is [zʋuk].

**Fix:** Change [zvuk] to [zʋuk].

### Issue 6 (MINOR): Dialogue Title Mismatch

**Location:** Section «Практика: Вчимося змінювати закінчення», line 271

The heading reads «Діалог: Що ти маєш? (Dialogue: What do you have?)» but the dialogue opens with «Що ти робиш?» (What are you doing?). The verb "мати" appears later ("я маю ідею") but the dialogue is not primarily about "what do you have." This title mismatch will confuse learners looking for the pattern announced in the heading.

**Fix:** Change the title to «Діалог: Що ти робиш? (Dialogue: What are you doing?)» or restructure the dialogue to open with "Що ти маєш?"

### Issue 7 (MINOR): Missing Planned Vocabulary Item "олія"

**Location:** Section «Ситуація: У магазині та вдома»

The meta plan explicitly lists «олія» (oil) as a cultural staple to include in the shopping list scenario. The word does not appear anywhere in the content. This is a plan compliance gap.

**Fix:** Add «олію» (accusative of олія) to the shopping list on lines 316–320, e.g., «Я купую олію.» (I am buying oil.)

---

## Factual Verification

### Grammar Rules

| Claim | Verdict |
|-------|---------|
| Feminine -а → -у in accusative | **Correct** (Standard §4.2.3.2.1) |
| Feminine -я → -ю in accusative | **Correct** |
| Masculine inanimate = no change in accusative | **Correct** |
| Neuter = no change in accusative | **Correct** |
| можливість doesn't change (feminine consonant ending) | **Correct** but premature for A1 |

### Cultural Claims

| Claim | Verdict |
|-------|---------|
| «Пакет потрібен?» is ubiquitous at checkouts | **Correct** — standard cashier phrase |
| Гречка as "strategic reserve" during economic worry | **Correct** — well-known Ukrainian cultural phenomenon |
| Базар vs supermarket distinction | **Correct** — markets remain vital for fresh produce |

### IPA in Vocabulary File

All 20 IPA transcriptions in the vocabulary YAML are correct. The only IPA error is in the content file itself: [zvuk] on line 211.

### Callout Box Verification

- Line 362–366: `[!culture]` "Гречка — The Strategic Reserve" — Factually accurate. Buckwheat panic-buying is a real and widely documented phenomenon in Ukraine.
- No superlative claims, no fabricated attributions, no dubious statistics found.

---

## Dimension Evidence

### 1. Lesson Quality (8/10)

**"Would I Continue?" test:** 4/5 PASS

| Question | Result | Evidence |
|----------|--------|----------|
| Did I feel overwhelmed? | PASS | Pacing is comfortable; rules introduced one gender at a time |
| Were instructions clear? | PASS | Clear English scaffolding throughout |
| Did I get quick wins? | PASS | First examples in section «Вступ: Предмети навколо нас» are immediately understandable |
| Was Ukrainian scary? | FAIL | Shop dialogue (lines 329–332) and bazaar phrases (374–377) introduce untaught grammar without warning |
| Would I come back tomorrow? | PASS | Encouraging closing with «Це чудовий результат!» |

The lesson arc is strong: warm welcome → preview ("This is the key that unlocks...") → present → practice → celebrate. Section «Практика: Вчимося змінювати закінчення» provides good step-by-step transformation drills. The "Wizard" metaphor (lines 258–265) is creative and memorable. However, the untaught grammar in two sections undermines the safety that beginners need.

### 2. Language Quality (7/10)

**Ukrainian grammar:** Mostly correct. All accusative transformations are accurate. No Russianisms detected. No colonial framing found.

**Problems:**
- Double stress marks on «че́ргу́» (line 343) and «виши́ва́нку» (line 396) are orthographic errors
- [zvuk] (line 211) is incorrect IPA for Ukrainian
- Untaught accusative adjective forms appear without glossing in the shop dialogue
- Line 136: «Я люблю цей відмінок.» — Having the tutor say "I love this case" is mildly artificial, though not technically an error

**English quality:** Clear, accessible, appropriate B1 readability. Contractions used naturally ("Don't overthink it!", "you'll learn"). No issues.

### 3. Activity Quality (8/10)

10 activities with good variety: group-sort, match-up, quiz, fill-in, unjumble. This exceeds the plan's 3-type specification and is pedagogically stronger.

**Strengths:**
- Distractors are well-chosen (nominative, genitive, locative forms as wrong answers)
- Progressive difficulty within each activity type
- All grammar in activities is correct

**Weaknesses:**
- Fill-in total is 24 items vs plan's 45 — significant shortfall
- Unjumble items are too easy (all 3-word SVO sentences: «Я бачу стіл», «Я читаю книгу»). No learner will struggle with word order in a 3-word sentence where the verb is obviously in the middle
- Activity quiz item (line 90): «У моїй кімнаті я бачу ____________ (window).» uses locative "моїй кімнаті" — grammatically correct but introduces an untaught case form in the question stem

### 4. Richness (8/10)

Section «Культурний погляд: Базар чи супермаркет?» provides genuine cultural depth: bazaar culture, the «Пакет потрібен?» meme, souvenir shopping. The «Гречка — The Strategic Reserve» callout (line 362) is a strong cultural hook. The suitcase-packing scene (lines 352–360) is creative and relatable. Multiple named Ukrainian references (Оксана, Андрій in the dialogue).

**Weakness:** The souvenir list includes «Я купую булаву́» (line 398) — buying a mace is not a typical tourist purchase and feels contrived. «Вишива́нку», «магні́т», and «тарі́лку» are authentic; the булава is not.

### 5. Humanity & Warmth (8/10)

| Marker | Count | Evidence |
|--------|-------|---------|
| Direct address (you, ви) | ~20+ | Frequent throughout |
| Encouragement phrases | 3 | "Don't overthink it!" (167), "Can you feel the pattern?" (268), "Це чудовий результат!" (417) |
| "Don't worry" moments | 2 | Warning box line 167–169, Tip box line 254–256 |
| "You can now..." validation | 2 | Lines 414, 433 |

The closing section is genuinely warm: «Ми вивчили знахідний відмінок. Ми знаємо нові слова. Ми вміємо купувати речі. Це чудовий результат!» (line 417). The "Wizard" metaphor adds personality. However, the opening block (lines 94–96) is slightly formal ("This is the key that unlocks your ability to talk about interacting with the world around you") — could be warmer.

### 6. LLM Fingerprint (8/10)

**Structural monotony test:** Section openings are varied:
- «Вступ»: "Look around your room." (informal, direct)
- «Теорія»: «Знахідний відмінок — це дуже важливий відмінок.» (Ukrainian first)
- «Практика»: "Let's practice the logic." (collaborative)
- «Ситуація»: "Language lives in context." (slightly generic)
- «Культурний погляд»: "In Ukraine, the база́р (market) is a vital institution." (concrete)

No 3+ sections start the same way. ✓

**Example batching:** Most sections use the same «**Bold Ukrainian.** (English.)» bullet format. Sections «Вступ», «Теорія», «Ситуація», and «Культурний погляд» all use this pattern. This is mildly monotonous but functional for A1 pedagogy where consistency aids learning.

**Generic AI clichés:** "Language lives in context" (line 311) is slightly generic. "This is the key that unlocks your ability" (line 96) is also borderline. No "це не просто" or "діамант" patterns found.

### 7. Factual Accuracy (8/10)

All grammar rules are correct. Cultural claims verified (see Factual Verification above). Score reduced from 9 due to:
- IPA error [zvuk] instead of [zʋuk]
- Double stress marks (orthographic inaccuracy)

### 8. Plan Compliance (8/10)

**Section coverage:** All 5 planned sections present as H2 headers. ✓
**Vocabulary:** All 11 required vocabulary items present in content. ✓ However, "олія" (planned cultural staple) is missing.
**Grammar scope:** Correctly limited to inanimate accusative, BUT the shop dialogue and bazaar phrases introduce adjective agreement and imperatives beyond scope.
**Objectives:** All 4 learning objectives addressed.
**Activity types:** Plan specifies fill-in (45 items) + quiz (15 items). Actual has 5 types with better variety but fewer fill-in items (24 vs 45).

### 9. Immersion Balance (7/10)

Audit reports 27.5% Ukrainian immersion. The module is phase A1.2, which targets 40–60% per tier guidance. At 27.5%, the Ukrainian content is below the lower bound of the A1.2 target range. The content relies heavily on English scaffolding even in sections where more Ukrainian could be used — for example, section «Ситуація: У магазині та вдома» has mostly English framing text around the Ukrainian examples.

However, the audit's own target range says 25–40%, which would make 27.5% compliant. This discrepancy between audit target and tier guidance should be resolved.

### 10. Pacing & Cognitive Load (7/10)

The lesson mostly maintains good pacing: new concepts are introduced one gender at a time, with practice before moving on. The "Step-by-Step Transformation" in section «Практика: Вчимося змінювати закінчення» (lines 219–238) is excellent — clear decision tree for each noun.

**Problems:**
- Section «Ситуація: У магазині та вдома» introduces too much vocabulary at once: картопля, морква, цибуля, ціна, знижка, товар, каса, черга, парасоля, куртка, ключ, паспорт, квиток, карта, щітка, фотоапарат — that's 16 new nouns in one section
- The shop dialogue (lines 327–334) introduces 5 untaught adjective forms alongside the practiced noun forms, spiking cognitive load
- The bazaar phrases add 4 more new nouns (диня, груша, капуста, сметана) plus imperatives

---

## Verification Summary

| Check | Result |
|-------|--------|
| Colonial framing | ✅ None found |
| Russianisms | ✅ None found |
| Grammar accuracy | ⚠️ Rules correct, but scope creep (adjective agreement, imperatives) |
| IPA accuracy | ⚠️ 1 error: [zvuk] → [zʋuk] |
| Stress marks | ❌ 2 double-stress errors: «че́ргу́», «виши́ва́нку» |
| Plan vocabulary | ⚠️ "олія" missing |
| Callout boxes | ✅ Factually accurate |
| Activity correctness | ✅ All answers verified correct |
| LLM fingerprint | ✅ No significant patterns |

---

## Verdict

**NEEDS REVISION**

The module has a strong pedagogical foundation — clear rule presentation, creative practice techniques (the Wizard metaphor), authentic cultural content, and a warm tutor voice. The core grammar is taught correctly and the activity variety exceeds the plan.

However, two critical issues prevent approval:

1. **Grammar scope creep** in the shop dialogue and bazaar section — these introduce accusative adjective agreement, imperative mood, and demonstrative pronoun declension without explanation, all of which violate A1 beginner safety principles.
2. **Orthographic errors** — double stress marks on two words need correction.

**Required fixes before passing:**
- Remove or simplify accusative adjectives in the shop dialogue (lines 329–332)
- Either simplify bazaar phrases to use taught grammar or explicitly frame them as "listen-only" phrases (lines 374–377)
- Fix double stress marks: «че́ргу́» → «чергу́», «виши́ва́нку» → «вишива́нку»
- Fix IPA: [zvuk] → [zʋuk]
- Either remove the «можливість» example or add an explicit "we'll cover this later" note
- Fix dialogue title mismatch (line 271)
- Add «олію» to the shopping list per plan