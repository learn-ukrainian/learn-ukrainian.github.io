Now I have sufficient evidence to write a thorough review. Let me compile my findings.

## Linguistic Scan

**1. Russianisms:** None detected. Core vocabulary is correct Ukrainian.

**2. Surzhyk:** None detected.

**3. Calques / Incorrect grammar claims:**

- **CRITICAL — `чекати` listed as accusative-governing verb.** The module states: *"Дієслова **бачити** (to see), **знати** (to know), **любити** (to love), та **чекати** (to wait) вимагають знахідного відмінка."* This is factually wrong. `чекати` governs the **genitive** case (чекати **кого? чого?**), not the accusative. Антоненко-Давидович (chunk ad-184) cites: *"чекала чоловіка"* (Kotsyubynsky) — genitive. The alternative modern construction is `чекати на + accusative` (чекати **на** маму), but the verb itself does NOT directly take accusative. The Grade 11 Заболотний textbook (p. 69) lists verb governance patterns and never places чекати with accusative. Including чекати in an accusative verb list teaches a wrong rule that learners will internalize.

- **MINOR — `дзвонити в офіс`** — The module says *"я дзвоню **в офіс** (I call the office - Accusative for direction)"*. While not strictly wrong in colloquial speech, standard Ukrainian prefers `дзвонити **до** офісу` (genitive after `до`). The construction `дзвонити в + accusative` mirrors Russian `звонить в офис`. At A2, teaching the standard construction is preferable.

**4. Paronyms:** None detected.

**5. Russian characters (ы, э, ё, ъ):** None found.

**6. Other:** `подобати` is marked as archaic (`arch`) in VESUM — the module's claim that "Я подобаю цю книгу" is absurd is pedagogically useful for learners but slightly inaccurate. The form exists archaically; the real issue is that modern Ukrainian uses only `подобатися`. This is a minor precision issue.

## Exercise Check

Four `<!-- INJECT_ACTIVITY -->` markers found:
1. **fill-in** (after Section 1 — Dative verbs) ✅ Matches plan hint, placed after teaching content
2. **match-up** (after Section 2 — подобатися) ✅ Matches plan hint, correct placement
3. **true-false** (after Section 3 — Age expressions) ✅ Matches plan hint, correct placement
4. **quiz** (after Section 4 — Dative vs. Accusative) ✅ Matches plan hint, correct placement

All 4 plan `activity_hints` have corresponding markers. Markers are spread evenly across the module, each after its relevant teaching section. Marker IDs match plan types and focuses.

**Issue:** The quiz activity (Section 4) will test dative vs. accusative using verb examples. Since `чекати` is incorrectly listed as accusative, the activity's distractors may encode the same error. The content fix must happen before activity generation.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All 4 plan sections covered with correct word distribution. Content outline points largely addressed. **Deductions:** (1) Plan Section 4 specifies `розповідати КОМУ (Dat.) ПРО ЩО (Acc.)` as a dual-case verb example — module uses `казати` instead and omits `розповідати` entirely. (2) No recommended vocabulary used: `довіряти`, `вибачати`, `посміхатися`, `співчувати`, `заздрити` all absent from prose. (3) Plan says "Contrastive drills with minimal pairs" — module compares in prose but has no explicit minimal-pair drill format. |
| 2. Linguistic accuracy | 7/10 | **Critical error:** `чекати` is listed as accusative-governing but actually takes genitive — *"Дієслова бачити, знати, любити, та **чекати** вимагають знахідного відмінка"* is factually wrong. This error appears in the contrastive section where learners are explicitly told which case to use, making it high-impact. **Minor:** `дзвонити в офіс` vs. standard `до офісу`. All other Ukrainian text verified clean — VESUM confirms 473/473 real words pass, and 9 "not found" are tokenizer artifacts (proper nouns Марк/Олена/Тарас, fragments Пам/еві/ові/ятайте/ятнадцять, heading word досвідника). |
| 3. Pedagogical quality | 9/10 | Strong PPP flow throughout: situation → pattern → practice. Each grammar point has 3+ examples. Section 1 opens with conceptual framing (Dative = case of communication), then shows paradigm with contextualized examples, then provides full pronoun chart with sentence examples. Section 2 explicitly addresses the common foreigner mistake "Я подобаю" and explains why it's wrong — excellent anticipation of learner errors. Age section builds systematically: formula → number agreement → question pattern → past tense. |
| 4. Vocabulary coverage | 8/10 | All 7 required verbs (допомагати, дякувати, дзвонити, радити, заважати, подобатися, відповідати) appear naturally in contextualized examples throughout. `рік/роки/років` forms covered with number agreement rules. **Deduction:** Zero recommended vocabulary used — `довіряти`, `вибачати`, `посміхатися`, `співчувати`, `заздрити` could have naturally appeared in Section 1 as additional dative verbs. This is a missed enrichment opportunity. |
| 5. Exercise quality | 9/10 | All 4 markers match plan activity_hints exactly in type and focus. Well-distributed — one per section. Each tests what was just taught. **Minor concern:** The quiz in Section 4 will include `чекати` as an accusative example due to the content error — must be fixed before activity generation. |
| 6. Engagement & tone | 8/10 | Mostly good — no motivational openers, no "magic of" language. The volunteer dialogue is natural and engaging with named speakers. **Deductions:** (1) Some meta-commentary: *"Learners often associate the Dative case exclusively with the preposition 'to'"* — tells rather than shows. (2) *"It is critical to remember that the verb NEVER agrees with the Dative pronoun"* — slightly heavy-handed phrasing. (3) English explanation blocks occasionally run long without Ukrainian examples (Section 4, paragraph about pronouns has ~50 words of English explanation before returning to Ukrainian). |
| 7. Structural integrity | 10/10 | All 5 sections present (4 content + summary) with correct H2 headings matching plan. Word count 2984 exceeds 2000 target comfortably. Clean markdown formatting throughout. No stray tags, no duplicate summaries, no formatting artifacts. Summary section includes self-check questions — good pedagogical closure. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms. No "like Russian but..." comparisons. The подобатися section explicitly compares to English ("I like" vs "Мені подобається") — this is the correct comparison direction (Ukrainian vs. English, not Ukrainian vs. Russian). Volunteer day dialogue reflects Ukrainian community values. Age expressions taught as Ukrainian cultural pattern. |
| 9. Dialogue & conversation quality | 9/10 | Volunteer day dialogue (Section 1) is natural, multi-turn (7 exchanges), with named speakers (Волонтер, Координатор) and clear motivations. Naturally integrates 6 dative verbs across the conversation. Age mini-dialogues (Section 3: Олена/Марк exchanges) are concise and natural. **Minor:** The age dialogues are slightly transactional — just Q&A about ages. Could benefit from a more situational framing (e.g., filling out a registration form together). |

## Findings

```
[LINGUISTIC ACCURACY] [SEVERITY: critical]
Location: Section 4 "Давальний чи знахідний?", paragraph 2
Issue: "Дієслова бачити (to see), знати (to know), любити (to love), та чекати (to wait) вимагають знахідного відмінка" — чекати governs the GENITIVE case (чекати кого? чого?), not accusative. Антоненко-Давидович (ad-184) confirms genitive governance. Teaching this as accusative at A2 will cause persistent case errors.
Fix: Replace чекати with an actual accusative-governing verb, e.g., шукати (to look for). Update the English translation accordingly.
```

```
[LINGUISTIC ACCURACY] [SEVERITY: minor]
Location: Section 1, paragraph about дзвонити
Issue: "я дзвоню в офіс (I call the office - Accusative for direction)" — standard Ukrainian prefers "дзвонити до офісу" (genitive). "Дзвонити в + accusative" mirrors Russian pattern.
Fix: Change to "я дзвоню до офісу" with appropriate case label.
```

```
[PLAN ADHERENCE] [SEVERITY: major]
Location: Section 4 "Давальний чи знахідний?", paragraph 3
Issue: Plan specifies "розповідати КОМУ (Dat.) ПРО ЩО (Acc.)" as a dual-case verb example. Module uses казати and показувати but omits розповідати entirely.
Fix: Add розповідати as a dual-case example alongside давати.
```

```
[VOCABULARY COVERAGE] [SEVERITY: minor]
Location: Section 1 (Dative verbs)
Issue: Plan lists 5 recommended verbs (довіряти, вибачати, посміхатися, співчувати, заздрити) — none appear in the content. At least 2-3 could naturally extend the dative verb list.
Fix: Add 2-3 recommended verbs as additional examples in Section 1 after the core verbs are established.
```

```
[ENGAGEMENT & TONE] [SEVERITY: minor]
Location: Section 1, paragraph 1
Issue: "Learners often associate the Dative case exclusively with the preposition 'to,' such as giving a gift 'to' a friend." — meta-commentary that tells about learners instead of teaching them directly.
Fix: Rephrase to address the learner directly: "You might associate the Dative case only with the preposition 'to,' as in giving a gift 'to' a friend."
```

## Verdict: REVISE

The module has one **critical** linguistic error (чекати as accusative) that teaches an incorrect grammar rule. This alone requires REVISE. Additionally, a major plan adherence gap (missing розповідати) and several minor improvements are needed. The overall structure, pedagogy, and Ukrainian quality are strong — these are targeted fixes, not a rewrite.

<fixes>
- find: "Дієслова **бачити** *(to see)*, **знати** *(to know)*, **любити** *(to love)*, та **чекати** *(to wait)* вимагають знахідного відмінка *(The verbs to see, to know, to love, and to wait require the accusative case)*."
  replace: "Дієслова **бачити** *(to see)*, **знати** *(to know)*, **любити** *(to love)*, та **шукати** *(to look for)* вимагають знахідного відмінка *(The verbs to see, to know, to love, and to look for require the accusative case)*."
- find: "Дієслова **бачити** *(to see)*, **знати** *(to know)*, **любити** *(to love)*, та **чекати** *(to wait)* вимагають знахідного відмінка *(The verbs to see, to know, to love, and to wait require the accusative case)*. Дієслова **допомагати** *(to help)*, **радити** *(to advise)*, **дякувати** *(to thank)*, та **дзвонити** *(to call)* вимагають давального відмінка *(The verbs to help, to advise, to thank, and to call require the dative case)*."
  replace: "Дієслова **бачити** *(to see)*, **знати** *(to know)*, **любити** *(to love)*, та **шукати** *(to look for)* вимагають знахідного відмінка *(The verbs to see, to know, to love, and to look for require the accusative case)*. Дієслова **допомагати** *(to help)*, **радити** *(to advise)*, **дякувати** *(to thank)*, та **дзвонити** *(to call)* вимагають давального відмінка *(The verbs to help, to advise, to thank, and to call require the dative case)*."
- find: "Я дзвоню **другові** *(I call a friend)*, але я дзвоню **в офіс** *(I call the office - Accusative for direction)*."
  replace: "Я дзвоню **другові** *(I call a friend)*, але я дзвоню **до офісу** *(I call the office — до + genitive for a place)*."
- find: "Це дієслова **давати** *(to give)*, **казати** *(to say)*, та **показувати** *(to show)*."
  replace: "Це дієслова **давати** *(to give)*, **розповідати** *(to tell)*, та **показувати** *(to show)*."
- find: "Слово «яблуко» — це знахідний відмінок *(The word \"apple\" is the accusative case)*. Слово «братові» — це давальний відмінок *(The word \"to the brother\" is the dative case)*. Інший приклад: «Він показує книжку сестрі» *(Another example: \"He shows a book to the sister\")*."
  replace: "Слово «яблуко» — це знахідний відмінок *(The word \"apple\" is the accusative case)*. Слово «братові» — це давальний відмінок *(The word \"to the brother\" is the dative case)*. Інший приклад: «Вона розповідає другові про подорож» *(Another example: \"She tells a friend about the trip\")*. Слово «другові» — це давальний відмінок *(\"to a friend\" is dative)*. Фраза «про подорож» — це знахідний з прийменником *(\"about the trip\" is accusative with a preposition)*. Ще один приклад: «Він показує книжку сестрі» *(\"He shows a book to the sister\")*."
- find: "Learners often associate the Dative case exclusively with the preposition \"to,\" such as giving a gift \"to\" a friend. However, many common Ukrainian verbs trigger this case directly because the action itself is inherently directed at a recipient or beneficiary."
  replace: "You might associate the Dative case only with the preposition \"to,\" as in giving a gift \"to\" a friend. However, many common Ukrainian verbs require the Dative directly because the action is inherently directed at a recipient or beneficiary."
</fixes>
