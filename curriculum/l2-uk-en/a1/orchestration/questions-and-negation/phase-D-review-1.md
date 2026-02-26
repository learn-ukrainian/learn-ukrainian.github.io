**Reviewed-By:** claude-opus-4-6

---

# Phase D.1 Review: Questions & Negation (A1-07)

**Module:** `curriculum/l2-uk-en/a1/questions-and-negation.md`
**Word count:** 2741 / 2000 (137.1%) — exceeds minimum, no penalty
**Activities:** 8 | **Vocabulary:** 24 | **Callout boxes:** 6

---

## Scores

| # | Dimension | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Lesson Quality | 8/10 | Good pacing and warm tone; structural monotony (7x identical sub-headers) weakens flow; "Investigative Journalist" persona from plan absent |
| 2 | Language Quality | 7/10 | «шо» described as "lazy pronunciation" (line 158) is linguistically inaccurate; "cheesecake" / "сирник" narrative mismatch (lines 275 vs 277); IPA inconsistencies between content and vocabulary |
| 3 | Factual Accuracy | 8/10 | "Cheesecake" ≠ "сирник" (cottage cheese pancake); "шо" is dialectal, not Surzhyk; ALF cultural hook checks out |
| 4 | Immersion | 9/10 | 21.2% falls within the 15–35% band for modules 6–10; English/Ukrainian balance is well-scaffolded |
| 5 | Richness | 7/10 | Zero markdown tables in a module teaching 9 question words — a grammar summary table is critically needed; richness at 70% vs 95% threshold |
| 6 | Activity Quality | 6/10 | Two fill-in activities (8 items each) all share the identical answer and identical options — zero differentiation; frequency adverbs taught in content but absent from activities |
| 7 | LLM Fingerprint | 7/10 | "Важливо знати:" repeated 7 times across sections; "Ввічливі запитання" activity has 8 identical explanations copy-pasted verbatim |
| 8 | Humanity & Warmth | 9/10 | Encouraging tutor voice throughout; "Would I Continue?" test: 5/5 pass; good emotional beats |

---

## Critical Issues Found

### Issue 1 (HIGH) — Activity monotony renders exercises pedagogically useless

**Location:** Activities YAML, lines 161–196 ("Скажіть «ні»") and lines 240–275 ("Ввічливі запитання")

The "Скажіть «ні»" fill-in has 8 items where EVERY answer is "не" and EVERY item offers the same 4 options: `["не", "ні", "так", "чи"]`. After the learner completes item 1, items 2–8 provide zero additional learning — they are pure repetition with no variation in context, answer, or distractor set. The same issue applies to "Ввічливі запитання" where all 8 items answer "Чи" with options `["Чи", "Не", "Ні", "Так"]`.

Additionally, the explanation text is copied verbatim 7 times: «Заперечна частка «не» ставиться перед дієсловом.» (activity lines 167, 171, 175, 179, 191, 195) and 8 times: «Ввічливе запитання часто починається з частки «Чи».» (activity lines 246, 250, 254, 258, 262, 266, 270, 274).

**Fix:** Vary the target word (not always "не" before a verb — include negating adjectives, adverbs, nouns), vary distractors, and vary explanations. For "Чи" exercises, mix in items where the answer is NOT "Чи" (e.g., a question-word question) so the learner must discriminate.

### Issue 2 (HIGH) — IPA double stress on завжди in both content and vocabulary

**Location:** Content line 170, Vocabulary line 50

Content: «**за́вжди́**» — two accent marks on one word. Ukrainian words carry a single primary stress. Standard pronunciation: завжди́ [zɑˈʋʒdɪ] (stress on final syllable).

Vocabulary: `[ˈzɑˈʋʒdɪ]` — two primary stress markers, which is phonologically impossible. Should be `[zɑˈʋʒdɪ]`.

**Fix:** Content: change `за́вжди́` to `завжди́`. Vocabulary: change `[ˈzɑˈʋʒdɪ]` to `[zɑˈʋʒdɪ]`.

### Issue 3 (MEDIUM) — "шо" mislabeled as "lazy pronunciation"

**Location:** Content line 158

Verbatim: «**Шо** = Very casual, spoken, sometimes considered "Surzhyk" (mixed language) or just lazy pronunciation.»

Calling "шо" "lazy pronunciation" is linguistically inaccurate and pedagogically harmful. "Шо" is a dialectal variant present across many authentic Ukrainian dialects (particularly southern and central). It is not a sign of laziness or language mixing. The "Surzhyk" label is also debatable — "шо" predates modern Surzhyk and exists in genuine Ukrainian dialects independently of Russian influence.

**Fix:** Replace with something like: «**Шо** = A widespread spoken variant found in many Ukrainian dialects. Standard written form is always **що**, but **шо** is extremely common in everyday conversation across Ukraine.»

### Issue 4 (MEDIUM) — "Cheesecake" / "сирник" narrative mismatch

**Location:** Content lines 275–277

Line 275: «Imagine you are at a Lviv coffee shop. You want to know if they have cheesecake.»
Line 277: «**Вибачте, чи у вас є сирник?** (Excuse me, do you have syrnyk (cottage cheese pancakes)?)»

A сирник is a cottage cheese pancake (fried in a pan), NOT a cheesecake. The English setup text says "cheesecake" but the Ukrainian word and its own parenthetical translation correctly say "cottage cheese pancakes." This will confuse learners who know what cheesecake is.

**Fix:** Change line 275 to: «You want to know if they have syrnyk (a cottage cheese pancake).»

### Issue 5 (MEDIUM) — Structural monotony: "Важливо знати:" ×7

**Location:** Content lines 75, 95, 122, 151, 164, 180, 236

The sub-header «Важливо знати:» appears 7 times across sections «Граматика: Як будувати питання» (5 times), «Вступ: Мистецтво ставити питання» (1 time), and «Практика: Інтонація та конструктор» (1 time). Real Ukrainian textbooks vary their "note" headers — e.g., "Зверніть увагу", "Порада", "Запам'ятайте", "Підказка".

**Fix:** Replace at least 4 of the 7 instances with varied alternatives: «Зверніть увагу:», «Запам'ятайте:», «Підказка:», «Порада:».

### Issue 6 (MEDIUM) — No tables in a grammar module teaching 9 question words

**Location:** Entire content file — no markdown tables found

Section «Граматика: Як будувати питання» introduces 9 question words (lines 130–138) as a numbered list. A grammar summary table would be far more effective for reference and scanning — e.g., columns for Question Word | IPA | Meaning | Example. The same section covers Чи vs Intonation questions which could benefit from a comparison table. The audit reports richness at 70% (threshold: 95%) with tables: 0/2.

**Fix:** Add at minimum:
1. A question words summary table in section «Граматика: Як будувати питання» (Word | IPA | English | Example)
2. A comparison table for Чи-questions vs Intonation-questions in section «Практика: Інтонація та конструктор»

### Issue 7 (LOW) — IPA inconsistency between content and vocabulary for звідки and скільки

**Location:** Content line 134 vs Vocabulary line 86; Content line 138 vs Vocabulary line 42

- **звідки**: Content `[ˈzʋʲidkɪ]` vs Vocabulary `[ˈzʲʋʲidkɪ]` — the з palatalization differs
- **скільки**: Content `[ˈskʲilʲkɪ]` vs Vocabulary `[ˈsʲkʲilʲkɪ]` — the с palatalization differs

Content and vocabulary should be consistent. The content versions (without regressive palatalization on the initial consonant) are more standard.

**Fix:** Align vocabulary IPA to match content: `[ˈzʋʲidkɪ]` for звідки, `[ˈskʲilʲkɪ]` for скільки.

### Issue 8 (LOW) — Frequency adverbs taught but not practiced in activities

**Location:** Content lines 167–181 (section «Граматика: Як будувати питання», sub-section «Слова частоти»)

The content teaches four frequency adverbs (завжди, часто, іноді, ніколи) with examples and the important double-negation rule for ніколи. However, NO activity in the YAML practices these. The plan explicitly calls for: "practicing 'Ні, я ніколи не...' to integrate frequency adverbs." The word "ніколи" does not appear in any activity item.

**Fix:** Add a fill-in or quiz activity targeting frequency adverbs, including items requiring double negation with ніколи.

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| Ukrainian has no auxiliary "do/does" for questions | Line 20–25 | **CORRECT** — Ukrainian forms questions without auxiliary verbs |
| «не» placed before the word it negates | Line 38 | **CORRECT** — standard negation rule |
| «Ні» vs «не» distinction | Lines 48–56 | **CORRECT** — accurately explains the functional difference |
| «Чи» as formal question marker | Lines 60–78 | **CORRECT** — «чи» marks yes/no questions, more formal register |
| Animals use «Хто» not «Що» | Lines 233, 237 | **CORRECT** — animate nouns take «Хто» |
| Double negation with «ніколи» | Line 181 | **CORRECT** — «Я ніколи не читаю» is standard |
| «Так» can mean "so" in other contexts | Line 123 | **CORRECT** — «так» also functions as an intensifier |
| ALF dubbed into Ukrainian in the 1990s | Lines 343–345 | **PLAUSIBLE** — the ALF Ukrainian dub is well-known; the cats quote circulates in Ukrainian internet culture |
| "Шо" = Surzhyk or lazy pronunciation | Line 158 | **INACCURATE** — "шо" is dialectal, not necessarily Surzhyk or lazy (see Issue 3) |
| "Сирник" = cheesecake | Lines 275–277 | **INCORRECT** — сирник is a cottage cheese pancake, not cheesecake (see Issue 4) |

---

## Plan Compliance

**Section coverage (meta content_outline → content H2):**

| Meta section | Content H2 | Present? |
|---|---|---|
| Вступ: Мистецтво ставити питання | Section «Вступ: Мистецтво ставити питання» | YES |
| Граматика: Як будувати питання | Section «Граматика: Як будувати питання» | YES |
| Практика: Інтонація та конструктор | Section «Практика: Інтонація та конструктор» | YES |
| Застосування: Розмова в реальному житті | Section «Застосування: Розмова в реальному житті» | YES |
| Культурний контекст: Ввічливість і гумор | Section «Культурний контекст: Ввічливість і гумор» | YES |

**Vocabulary coverage:** All required words from `vocabulary_hints.required` are present in the vocabulary YAML (чи, що, хто, де, коли, не, так, ні) plus all recommended words (куди, звідки, чому, як, скільки, завжди, ніколи).

**Objectives coverage:**
- Learner can ask yes/no questions using чи — COVERED (lines 60–78)
- Learner can form questions with question words — COVERED (lines 125–149)
- Learner can make negative statements with не — COVERED (lines 37–56)
- Learner understands frequency adverbs — COVERED in content (lines 167–181), NOT practiced in activities

**Missing from plan:** The plan specifies a "Roleplay: 'The Investigative Journalist'" persona activity (plan file line 51–52) which is absent from both content and activities. The content has café and social scenarios but no investigative journalist roleplay.

---

## Colonial Framing Check

No colonial framing detected. The content does not define Ukrainian by contrast with Russian. Comparisons are made with English (the learner's L1), which is appropriate. The "шо" discussion (lines 154–165) does not reference Russian.

---

## LLM Fingerprint Analysis

| Pattern | Found? | Details |
|---------|--------|---------|
| Structural monotony (3+ sections start same way) | **YES** | «Важливо знати:» appears 7 times (lines 75, 95, 122, 151, 164, 180, 236) |
| Example batching uniformity | Mild | Examples use consistent `* **Ukrainian** — English` format across sections, but mixed with dialogues and practice grids — acceptable variation |
| "це не просто" / "це не лише" ×2+ | No | Not found |
| Generic AI clichés | No | No "діамант", "двигун прогресу", etc. |
| "In this lesson, we will explore..." | Borderline | Line 18: "Today, we will learn how to transform..." — acceptable tutor voice |
| Callout monotony (3+ same title) | No | All callout titles are unique |
| Activity explanation copy-paste | **YES** | 7 identical explanations in "Скажіть «ні»", 8 identical in "Ввічливі запитання" |

---

## Russicism / Anglicism Check

| Pattern | Found? | Location |
|---------|--------|----------|
| давайте попрактикуємо / повторимо / подивимося | No | Not found anywhere in content |
| кушати, тапочки, здача, получати | No | N/A |
| надіятися, вообще | No | N/A |
| "роблять каву" | No | N/A |

No Russicisms or Anglicisms detected. Clean.

---

## Beginner Safety ("Would I Continue?" Test)

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | **PASS** | Concepts chunked well, pacing comfortable |
| Were instructions clear? | **PASS** | Always knew what to do |
| Did I get quick wins? | **PASS** | Early examples simple, practice grids accessible |
| Was Ukrainian scary? | **PASS** | Introduced with translations, gentle scaffolding |
| Would I come back tomorrow? | **PASS** | Encouraging tone, fun ALF hook at the end |

Result: 5/5 PASS

---

## Verification Summary

| Metric | Result |
|--------|--------|
| Citations verified via Grep | 12/12 |
| Fabricated citations | 0 |
| Issues with line numbers | 8 |
| Dimensions below 9 | 5 (Language 7, Richness 7, Activities 6, LLM Fingerprint 7, Lesson 8) |
| Colonial framing | None |
| Russicisms | None |
| D.0 pre-screen issues confirmed | N/A (clean) |

---

## Verdict

**NEEDS REVISION**

The content is pedagogically sound with warm tutor voice, good pacing, and accurate core grammar. However, three categories of issues require fixing before approval:

1. **Activity quality is the most serious problem.** Two of 8 activities are effectively single-item exercises stretched to 8 with copy-paste. These need genuine differentiation in answers, distractors, and explanations. Frequency adverbs need activity coverage.

2. **Richness gaps** — zero tables in a grammar module introducing 9 question words is a missed opportunity. Adding summary tables and a comparison table would close the richness gap efficiently.

3. **Content accuracy** — the "cheesecake" / "сирник" mismatch and the "lazy pronunciation" characterization of "шо" need correction. The double-stress IPA on завжди needs fixing in both content and vocabulary.

**Priority fix order:** Activities (Issue 1) → Tables (Issue 6) → IPA (Issues 2, 7) → "шо" characterization (Issue 3) → "cheesecake" (Issue 4) → structural monotony (Issue 5) → frequency adverb activities (Issue 8)