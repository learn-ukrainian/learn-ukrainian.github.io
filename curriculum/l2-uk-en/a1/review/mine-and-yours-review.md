<!-- content-hash: a31a2722b6a9 -->
**Reviewed-By:** claude-opus-4-6

# Phase D.1 Review: Mine and Yours (a1-14)

**Module:** `curriculum/l2-uk-en/a1/mine-and-yours.md`
**Level:** A1 | **Sequence:** 14 | **Phase:** A1.2 [Navigation]
**Word count:** 3017 / 2000 (150.8%) — exceeds minimum, appropriate
**Persona:** Patient Supportive Tutor / Kindergarten Teacher

---

## Plan Verification

### Outline Compliance

The meta `content_outline` specifies 5 sections:
1. Вступ: Бюро знахідок (250w)
2. Граматика: Мій, твій, наш (750w)
3. Граматика: Його, її, їхній (400w)
4. Практика: Чия це річ? (300w)
5. Культура: Твій чи Ваш? (300w)

The content file has all 5 plus an **additional** section «Діалоги: Це мій телефон» between Практика and Культура. This extra section is not in the meta content_outline but aligns with the plan's `activity_hints` which call for "Whose is this? conversations" and the plan's mention of "рольова гра «Чия це сумка?»". The dialogues are pedagogically valuable for A1 — this deviation is acceptable.

The content also includes a `# Підсумок` summary and `## Vocabulary` table at the end.

### Vocabulary Scope

Plan `vocabulary_hints.required` items: мій, моя, моє, його, її, наш, чий, чия — **all present** in content.
Plan `vocabulary_hints.recommended` items: ваш, їхній, свій, чиє, річ — **all present** in content.

The vocabulary YAML file contains 21 items. The in-content vocabulary table at line 425 contains only 16 items, missing: твоє, чия, чиє, чиї, свій, річ. These items are taught in the lesson body but omitted from the summary table. This is a gap.

### Activity Scope (CRITICAL GAP)

The plan specifies 7 activity types including **3 dedicated свій exercises**:
- quiz: Свій vs його/її contrastive (8 items)
- true-false: Свій key concepts (8 items)
- fill-in: Свій in context (6 items)

**None of these exist.** The activities file has zero exercises where свій is the correct answer. It appears only as a distractor in the "Його, її чи їхній?" fill-in (lines 209-237). This means the plan objective "Learner can use свій correctly to show reflexive possession" is **untested** in the activity set.

### Objectives Coverage

| Objective | Addressed |
|-----------|-----------|
| Use possessive pronouns мій/твій/його/її/наш/ваш/їхній | Yes — all sections |
| Match possessives to noun gender | Yes — Section «Граматика: Мій, твій, наш» |
| Ask and answer questions about possession | Yes — Section «Практика: Чия це річ?» + dialogues |
| Distinguish variable vs invariable possessives | Yes — Section «Граматика: Його, її, їхній» |
| Use свій for reflexive possession | Partially — prose only, **no activities** |

---

## Deep Verification

### Section «Вступ: Бюро знахідок»

**Strengths:** Warm opening at line 19: «Привіт! Ласкаво просимо!» Sets a relatable "Lost and Found" scenario. Clear preview of learning outcomes at lines 30-33. Good gender intuition refresh connecting to prior module at line 55.

The question paradigm at lines 46-49 is cleanly presented with IPA:
- «Чий це паспорт?» [t͡ʃɪj]
- «Чия це сумка?» [t͡ʃɪˈja]
- «Чиє це фото?» [t͡ʃɪˈjɛ]
- «Чиї це ключі?» [t͡ʃɪˈji]

IPA is correct. The [!context] box at line 37 effectively bridges English rigidity ("my" never changes) to Ukrainian flexibility.

**Issue:** Line 13 intro paragraph has a slightly formal register: "In this lesson, you will learn how to claim what is yours, ask about what belongs to others, and navigate the polite boundaries of ownership in Ukrainian." The phrase "navigate the polite boundaries of ownership" is overly abstract for A1. A simpler framing would be more appropriate.

### Section «Граматика: Мій, твій, наш»

**Strengths:** Clean paradigm presentation. The parallel between мій and твій is well highlighted (line 84: "It mirrors мій perfectly. You just change the first letter from M to T"). The [!tip] box at line 98 with the rhyme pattern (Чия? — Моя. / Чиє? — Моє. / Чиї? — Мої.) is an excellent mnemonic.

The наш/ваш section at line 107 correctly notes the vowel difference: «Мій/твій flow with the vowels -я, -є, -ї. Наш/ваш use the vowels -а, -е, -і» (line 123).

**No Ukrainian errors detected** in this section. All paradigms are correct.

### Section «Граматика: Його, її, їхній»

**Strengths:** The "best news" framing at line 133 is encouraging — telling learners that його/її don't change. The table at lines 139-144 is a clear visual aid. The contrast between «Андрій любить свою маму» and «Андрій любить його маму» at lines 188-189 is pedagogically effective.

The [!warning] box at line 156 about його pronunciation (г = [ɦ]) is important and well placed.

**Issue — їхній section:** At line 162, the subsection title «Займенник «Їхній»: Стандарт проти суржику» uses "суржик" but the content at line 164 says "even some native speakers influenced by Russian" — this is a legitimate decolonization context, not colonial framing. However, the word "суржик" (surzhyk) in the H3 title may confuse A1 learners who haven't encountered this term. It's introduced without definition.

**Issue — свій scope:** The subsection «Свій: Концепція «Власний»» at line 181 introduces this as an "advanced concept" but gives three full example sentences in the [!myth-buster] box (lines 199-201). For A1, this is reasonable depth. However, the total absence of свій from activities means learners have zero practice opportunity.

### Section «Практика: Чия це річ?»

**Strengths:** The algorithm at lines 230-256 gives learners a clear step-by-step decision process. Three worked examples (кава, паспорт, вікно) cover all three genders. The common error section at line 259 addresses «Мій книга» with a vivid analogy (line 263: "Saying 'мій книга' sounds to a Ukrainian ear like saying 'He is a beautiful actress' in English").

Line 268: «Це... (aha, window ends in -o)... моє вікно» — good micro-pause technique.

The "Відмінки" preview at line 279 is a smart forward reference that warns about case changes without teaching them. Line 288 says "Don't panic!" — appropriate encouragement.

### Section «Діалоги: Це мій телефон»

**Strengths:** Four realistic scenarios (café, dorm, bus, airport) at varied registers. Each dialogue has an Аналіз section explaining the grammar. The bus scenario (Сценарій 3, line 322) is particularly engaging with humor.

Verified dialogue Ukrainian at line 326: «Обережно! Це моя нога!» — natural and correct.

The [!observe] box at line 352 about possessives as standalone answers is a useful grammar insight.

**Minor:** This entire section isn't in the meta content_outline, though the plan mentions dialogues under the Practice section.

### Section «Культура: Твій чи Ваш?»

**Strengths:** Excellent social distance explanation. The "switching to ти" ritual at line 368 — «Можемо перейти на ти?» — is culturally accurate and important. The capital letter etiquette section at line 379 is a genuine useful cultural insight.

The «Мовний пуризм: Їхній проти Їх» subsection at line 391 provides good historical context about russification affecting language norms. The decolonization framing is appropriate and not colonial — it explains why "їхній" is the standard form, not defining Ukrainian by what Russian does.

The proverb in the [!culture] box at line 402 — «Своя сорочка ближче до тіла» — is a real, widely-known Ukrainian proverb. Grammatical annotation (своя agrees with сорочка) is a nice pedagogical touch.

### Section «Vocabulary»

The in-content vocabulary table (lines 427-443) has 16 entries but the vocabulary YAML has 21 items. Missing from the content table: твоє, чия, чиє, чиї, свій, річ — all of which are taught in the lesson and should be in the summary.

### IPA Verification (CRITICAL — vocabulary YAML)

Three IPA errors in the vocabulary YAML file that contradict the (correct) content:

| Word | Vocab YAML | Content Table | Correct | Issue |
|------|-----------|---------------|---------|-------|
| його | [ˈjɔɦɔ] (line 41) | [jɔˈɦɔ] (line 439) | [jɔˈɦɔ] | Wrong stress — should be on 2nd syllable |
| її | [jiji] (line 45) | [jiˈji] (line 440) | [jiˈji] | Missing stress mark |
| прикметник | [prɪˈkmɛtnɪk] (line 81) | [prɪkˈmɛtnɪk] (line 443) | [prɪkˈmɛtnɪk] | Wrong stress placement |

The content body IPA is correct throughout. The vocabulary YAML file has the errors.

### Activity-by-Activity Review

| # | Type | Title | Items | Quality |
|---|------|-------|-------|---------|
| 1 | match-up | Переклад займенників | 8 | Good — covers range of pronouns |
| 2 | group-sort | Він, Вона, Воно чи Вони? | 16 | Good — reinforces gender |
| 3 | quiz | Правильна форма для предмета | 8 | Good — tests agreement |
| 4 | fill-in | Мій, моя, моє чи мої? | 8 | Good — focused drill |
| 5 | match-up | Запитання та відповіді | 8 | Good — Чий?→answer pairing |
| 6 | unjumble | Побудуйте речення | 6 | Good — sentence building |
| 7 | fill-in | Його, її чи їхній? | 8 | Good — invariable focus |
| 8 | quiz | Соціальна дистанція | 8 | Good — cultural etiquette |
| 9 | true-false | Правда чи ні? | 8 | Good — concept checking |
| 10 | fill-in | Змішана практика | 8 | Good — integration |

**Activity gap:** No свій-focused activities. The plan requires 22 items across 3 activity types (quiz, true-false, fill-in) dedicated to свій. Zero are present.

**Activity item correctness:** All reviewed items have correct answers. Activity 7 item at line 228 correctly uses "Їхні" for plural "друзі" and at line 231 correctly uses "Їхнє" for neuter "рішення".

---

## Critical Issues Found

### Issue 1: Missing свій Activities (Plan Compliance — CRITICAL)

**Location:** Activities file — entirely absent
**Evidence:** Plan `activity_hints` specifies 3 dedicated свій activity types totaling 22 items. Activities file has zero exercises where свій is the correct answer. It appears only as a distractor option (lines 209, 213, 217, 221, 225, 237).
**Impact:** Plan objective "Learner can use свій correctly to show reflexive possession" is untested.
**Fix:** Add 3 activities: (1) quiz contrasting свій vs його/її with sentences like «Я читаю ___ книгу» vs «Він читає ___ книгу» (8 items); (2) true-false testing свій concepts (8 items); (3) fill-in with свій in context (6 items).

### Issue 2: Vocabulary YAML IPA Errors (Data Integrity — CRITICAL)

**Location:** `vocabulary/mine-and-yours.yaml` lines 41, 45, 81
**Evidence:** Three IPA transcriptions have incorrect stress placement:
- його: `[ˈjɔɦɔ]` should be `[jɔˈɦɔ]` (stress on 2nd syllable, not 1st)
- її: `[jiji]` should be `[jiˈji]` (missing stress mark entirely)
- прикметник: `[prɪˈkmɛtnɪk]` should be `[prɪkˈmɛtnɪk]` (stress misplaced)
**Impact:** Learners relying on vocabulary data would learn incorrect pronunciation.
**Fix:** Correct the three IPA entries in the vocabulary YAML to match the (correct) content body.

### Issue 3: In-Content Vocabulary Table Incomplete

**Location:** Content lines 425-443
**Evidence:** Table has 16 items but vocabulary YAML has 21. Missing from table: твоє, чия, чиє, чиї, свій, річ — all taught in the lesson body.
**Impact:** Learners lose a reference for 6 key items they encountered during the lesson.
**Fix:** Add the 6 missing items to the Vocabulary table.

### Issue 4: Pacing — Two Grammar Sections Before Practice

**Location:** Sections «Граматика: Мій, твій, наш» and «Граматика: Його, її, їхній» (lines 64-222)
**Evidence:** ~160 lines of grammar content (мій/твій/наш/ваш paradigms + його/її/їхній/свій) before the first practice opportunity in section «Практика: Чия це річ?» at line 224. For A1 learners, this exceeds the recommended 2 concepts before practice.
**Impact:** Cognitive overload risk. A nervous beginner may feel overwhelmed by the density.
**Fix:** Consider adding a brief "Try it!" micro-exercise between sections 2 and 3 (e.g., 3-4 items matching мій/твій/наш forms to nouns) so learners get a quick win before encountering його/її/їхній.

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| Possessive paradigms (мій/моя/моє/мої, etc.) | Lines 67-70, 79-88, 112-121 | **Correct** — all forms accurate per standard Ukrainian grammar |
| Його/її are invariable (Genitive forms) | Lines 133-136 | **Correct** — grammatically accurate explanation |
| Їхній changes like an adjective | Lines 166-172 | **Correct** — paradigm accurate |
| Capital Ваш in letters = respect to one person | Lines 381-389 | **Correct** — standard Ukrainian epistolary etiquette |
| "Їх" as possessive = Russian influence | Lines 164, 393-396 | **Correct** — historically accurate; russification did normalize this |
| Proverb «Своя сорочка ближче до тіла» | Line 402 | **Correct** — real, widely-known Ukrainian proverb |
| Switching to "ти" ritual | Lines 367-369 | **Correct** — culturally accurate social norm |
| God addressed as Ти in Ukrainian prayers | Line 364 | **Correct** — standard in Ukrainian Christian tradition |

**No fabricated facts detected.** All grammar rules, cultural claims, and the proverb are verified.

---

## "Would I Continue?" Test (Beginner Safety)

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | **Borderline** | Two dense grammar sections before practice is heavy |
| Were instructions clear? | **Pass** | Always knew what to do, algorithm is explicit |
| Did I get quick wins? | **Partial** | No practice until Section 4; dialogues provide modeling but not active practice |
| Was Ukrainian scary? | **Pass** | Well scaffolded with English throughout |
| Would I come back tomorrow? | **Pass** | Dialogues and culture section are engaging enough |

**Score: 3.5/5** → Lesson Quality 8/10

### Emotional Safety Mapping

- Welcome/orientation: **Present** — line 19 «Привіт! Ласкаво просимо!»
- Curiosity trigger: **Present** — Lost and Found scenario, line 21
- Quick wins: **Late** — first practice at line 224
- Encouragement: **Present but sparse** — line 35 "Calmly and confidently", line 133 "best news", line 288 "Don't panic! ... You are a learner!"
- Progress marker: **Present** — line 418-423 «Тепер ви можете сказати...» / «Це був гарний урок.»

Encouragement density is adequate but could be stronger between sections 2 and 3.

---

## LLM Fingerprint Analysis

| Test | Result |
|------|--------|
| Section opening monotony | **Pass** — all 6 H2 sections open differently |
| Example format batching | **Minor flag** — sections 2, 3, and 6 use similar bullet-list format, but interspersed with tables and dialogues. Not uniform enough to flag. |
| "це не просто" / "не лише" | **Pass** — zero instances found |
| Generic AI rhetoric | **Pass** — no "It is important to note", no "In this lesson, we will explore" |
| Stacked abstract nouns | **Pass** — not found |
| Callout monotony | **Pass** — 6 callouts using 6 different types |
| Example plausibility | **Pass** — all Ukrainian examples are natural and plausible |

**Overall:** Content reads as authentic tutor voice, not AI-generated. The "dance partners" metaphor at line 62 and the "wearing a red dress / wearing a tie" visualization at lines 266-267 are creative and non-formulaic.

---

## Colonial Framing Check

Two references to Russian found:
1. Line 164: "Many students (and even some native speakers influenced by Russian) say 'їх дім'" — **Legitimate.** Explains why a non-standard form exists, contextualizing as influence rather than baseline comparison.
2. Line 394: "In Soviet times, there was a policy called 'russification'" — **Legitimate decolonization context.** Explains historical pressure on Ukrainian, framing їхній as a "return to the language's roots."

**No colonial framing detected.** Ukrainian is presented on its own terms throughout. Russian is referenced only as historical context for language purism.

---

## Scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Language (Ukrainian) | **8** | All paradigms correct. Ukrainian sentences throughout are grammatically sound. BUT 3 IPA errors in vocabulary YAML (його stress, її stress, прикметник stress). Content body IPA is correct. |
| 2 | Language (English) | **9** | Clear, warm tutor voice. Accessible B1-level English. One minor formality issue at line 13 ("navigate the polite boundaries of ownership"). Otherwise excellent scaffolding. |
| 3 | Lesson Quality | **8** | Good structure with engaging Lost and Found framing. Four dialogues are excellent. BUT pacing issue: ~160 lines of grammar before first practice. "Would I Continue?" = 3.5/5. |
| 4 | Richness | **8** | 6 callout boxes (context, tip, warning, myth-buster, observe, culture). 4 dialogues with analysis. 1 proverb. Dance metaphor, visualization technique. No named Ukrainian references beyond the proverb. |
| 5 | Activities | **7** | 10 activities with good type variety (match-up, group-sort, quiz, fill-in, unjumble, true-false). All answers correct. BUT entirely missing 22 items of свій-focused exercises required by plan. |
| 6 | Immersion | **8** | 25.1% Ukrainian (target 25-40%). At the floor of the range but appropriate for a grammar-heavy A1.2 module that requires extensive English explanation of possessive agreement. |
| 7 | LLM Fingerprint | **8** | No structural monotony, no AI clichés, varied section openings. Some uniformity in bullet-list example format across grammar sections. Metaphors are original (dance partners, dress/tie visualization). |
| 8 | Factual Accuracy | **9** | All grammar paradigms verified correct. Proverb verified. Cultural claims (capital Ваш, ти/Ви switching) accurate. Russification context historically correct. |
| 9 | Humanity/Warmth | **8** | Warm opening and closing. "Don't panic!" encouragement. "Best news" framing for invariable forms. BUT mid-lesson encouragement is sparse — long stretches of grammar without positive reinforcement between sections 2 and 3. |

---

## Verification Summary

| Check | Status |
|-------|--------|
| Plan outline compliance | **PASS** — all 5 meta sections present; 1 extra section (Діалоги) is pedagogically beneficial |
| Vocabulary scope | **PARTIAL** — all required/recommended items in content body; 6 items missing from in-content vocab table |
| Activity scope | **FAIL** — missing all 3 sviy-focused activity types from plan (22 items) |
| Grammar accuracy | **PASS** — all paradigms, rules, and examples verified correct |
| IPA accuracy (content) | **PASS** — all IPA in lesson body is correct |
| IPA accuracy (vocab YAML) | **FAIL** — 3 errors: його, її, прикметник |
| Colonial framing | **PASS** — no colonial framing; Russian references are legitimate decolonization context |
| LLM fingerprint | **PASS** — no patterns detected |
| Factual accuracy | **PASS** — all claims verified |
| Beginner safety | **PARTIAL** — warm but pacing issue with late first practice |

---

## Verdict

**NEEDS REVISION** — The content prose is strong: warm, well-structured, and grammatically accurate with engaging dialogues and cultural depth. However, **two critical gaps** prevent passing:

1. **Missing свій activities** — The plan explicitly requires 22 items across 3 activity types focused on свій vs його/її. Zero exist. This leaves a core learning objective entirely untested.
2. **Vocabulary YAML IPA errors** — Three stress placement errors in the vocabulary data file would teach incorrect pronunciation.

**Required fixes for D.2:**
1. Add 3 свій-focused activities to the activities YAML (quiz: 8 items, true-false: 8 items, fill-in: 6 items)
2. Fix 3 IPA entries in vocabulary YAML: його → [jɔˈɦɔ], її → [jiˈji], прикметник → [prɪkˈmɛtnɪk]
3. Add 6 missing items (твоє, чия, чиє, чиї, свій, річ) to the in-content Vocabulary table

**Recommended improvements (not blocking):**
4. Add a mini-exercise (3-4 items) between sections «Граматика: Мій, твій, наш» and «Граматика: Його, її, їхній» for a quick win
5. Add 1-2 encouragement lines at the transition between grammar sections