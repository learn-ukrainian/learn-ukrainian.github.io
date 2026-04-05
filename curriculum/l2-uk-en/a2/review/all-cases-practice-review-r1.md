Now I have all the evidence I need. Let me compile the full review.

## Linguistic Scan

**Four separate checks:**

1. **Russianisms:** 
   - **"на прийомі"** — The lemma "прийом" is **NOT IN VESUM** (verified twice: both `verify_lemma('прийом')` and `verify_words(['прийомі', 'прийому'])` return NOT FOUND). This is a Russian borrowing from "приём". Ukrainian alternatives: "на прийманні (у лікаря)" or restructure. Appears in prose: `or sit «на прийомі» *(at an appointment)*`.

2. **Surzhyk:** No surzhyk detected.

3. **Calques:**
   - **"знаходиться"** — Used in the doctor dialogue: `«Вона знаходиться прямо біля лікарні.»` Антоненко-Давидович (`ad-148`) explicitly flags "знаходитися" for indicating location as a calque of Russian "находиться". Correct Ukrainian: "є", "міститься", "перебуває", or restructure. **WORSE:** the same verb is listed in the case cheat sheet under Locative verbs — `знаходитися *(to be located)*` — meaning it is being **taught** as correct Ukrainian.

4. **Paronyms:** No paronym errors detected.

**Russian characters (ы, э, ё, ъ):** None found.
**Gender/case errors:** None detected — all case forms verified correct.
**Factual claims about grammar:** All correct (vowel alternation і→е/о in closed→open syllables, animate accusative = genitive, dual form "два ока", etc.).

## Exercise Check

Four activity markers found, matching all four plan `activity_hints`:

| # | Marker | After section | Matches plan hint? |
|---|--------|--------------|-------------------|
| 1 | `<!-- INJECT_ACTIVITY: quiz, Identify which case... -->` | Dialogue 1 | ✓ quiz, 8 items |
| 2 | `<!-- INJECT_ACTIVITY: fill-in, Complete gaps... -->` | Dialogue 2 | ✓ fill-in, 8 items |
| 3 | `<!-- INJECT_ACTIVITY: match-up, Match sentence halves... -->` | Dialogue 3 | ✓ match-up, 8 items |
| 4 | `<!-- INJECT_ACTIVITY: error-correction, Find and fix... -->` | Самоперевірка | ✓ error-correction (no item count in marker — plan says 6) |

**Placement:** Good — each marker follows the teaching section it tests.  
**Distribution:** Evenly spread across all four sections. ✓  
**Issue:** Error-correction marker doesn't specify item count; plan requires 6. Minor — the YAML generator should handle this.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | **Deduction:** Plan specifies "Extended dialogue (12-15 exchanges)" for Dialogue 1, but the actual dialogue has only **7 exchanges** (Оксана×4, Андрій×3). Dialogue 2 has ~9 exchanges (borderline). Dialogue 3 has 8 exchanges. Plan's Section 2 point says "learner rewrites selected sentences changing singular to plural" — this is covered in prose but the fill-in activity marker doesn't specifically focus on singular→plural rewriting; it covers "all 7 cases, both singular and plural." **Reward:** All 4 content_outline sections present. Cultural note on birthday traditions ✓. Geography vocabulary with multiple cases ✓. Planning expressions (Давай поїдемо, Може спочатку, А потім можна) ✓. All 10 required vocabulary items used naturally in prose. Case cheat sheet with questions, prepositions, and verb triggers ✓. |
| 2. Linguistic accuracy | 7/10 | **Deduction:** (1) "Вона **знаходиться** прямо біля лікарні" — calque of Russian "находиться", confirmed by Антоненко-Давидович (ad-148). (2) "знаходитися" taught as a standard Locative verb in the case cheat sheet — teaches a calque as correct Ukrainian. (3) "на **прийомі**" — "прийом" NOT IN VESUM; Russicism from "приём". **Reward:** All other Ukrainian is clean — no surzhyk, no Russian characters, case forms correct throughout, vowel alternation explanation accurate, dual "два ока" example correct. |
| 3. Pedagogical quality | 8/10 | **Reward:** Clear PPP flow — dialogues provide the situation, prose extracts patterns, activities practice. Multiple examples per grammar point (3+ for each case). Singular/plural contrast explained well (один рецепт → багато рецептів, одне око → два ока → п'ять очей). Transport Instrumental without preposition explained clearly. **Deduction:** Some explanatory paragraphs are long English-heavy blocks (e.g., the paragraph starting "Medical conversations naturally require specific vocabulary" runs ~100 words of English before a Ukrainian example). Could benefit from more frequent Ukrainian sentence interjections. |
| 4. Vocabulary coverage | 9/10 | **All 10 required words used naturally:** вечірка ("велику вечірку"), подарунок ("купив подарунок Олені"), лікар ("працюють лікарі"), пацієнт ("Пацієнт: Добрий день"), здоров'я ("Бажаю вам здоров'я!"), ліки ("за ліками"), подорож ("планують спільну подорож"), потяг ("Потягом чи автівкою?"), визначне місце ("багато визначних місць"), запрошувати ("запросила друзів"). **All 5 recommended words used:** рецепт ✓, температура ✓, Карпати ✓, милуватися ✓, частувати ✓. **Minor:** No explicit new-word introduction ceremony — words appear naturally in context, which is appropriate for A2.5 synthesis module. |
| 5. Exercise quality | 8/10 | **Reward:** All 4 plan activity types represented with markers. Placement is pedagogically sound — each after its teaching section. Focus descriptions in markers closely match plan hints. **Deduction:** Error-correction marker lacks item count (plan says 6). Cannot verify actual exercise content (YAML generated separately). The fill-in activity focus ("all 7 cases, both singular and plural") is broad — plan's Section 2 specifically wanted singular→plural rewriting, which is a narrower exercise. |
| 6. Engagement & tone | 8/10 | **Reward:** Dialogues feel natural — friends planning a party is relatable. Hospital visit is practical. Travel planning across real Ukrainian cities with real geography. Cultural note about birthday traditions is a genuine insight. No motivational openers, no gamified language. **Deduction:** Some mild meta-commentary: "In this dialogue, we see how the Vocative case and the Nominative plural function in a natural conversation" — this is a "Let us observe" pattern. Also: "Medical conversations naturally require specific vocabulary" — generic opening. |
| 7. Structural integrity | 9/10 | All 4 H2 sections present and correctly ordered. Word count 2388 > 2000 target ✓. Clean markdown formatting. No stray tags. No duplicate summary sections. Activity markers cleanly placed. |
| 8. Cultural accuracy | 9/10 | Birthday tradition correct — іменинник частує гостей ✓. No "like Russian but..." framing anywhere. Ukrainian geography presented on its own terms. Vocative usage in social context (пане докторе, лікарю) culturally appropriate. **Minor:** "у 2024 році" in the travel dialogue — the module is timeless content, a specific year is odd but harmless. |
| 9. Dialogue quality | 7/10 | **Reward:** Named speakers with distinct roles (Оксана/Андрій planning, Лікар/Пацієнт consulting, Тарас/Андрій dreaming). Situations are realistic and culturally grounded. Speakers have personality (Андрій is practical — "Не хвилюйся, я замовлю"; Тарас proposes the route). **Deduction:** Dialogue 1 is significantly shorter than planned (7 exchanges vs. 12-15). All three dialogues are on the short side for "extended" dialogues. Dialogue 2, while natural, is somewhat formulaic (symptom→diagnosis→prescription). |

## Findings

```
[LINGUISTIC ACCURACY] [CRITICAL]
Location: Dialogue 2 prose — "Вона знаходиться прямо біля лікарні."
Issue: "знаходитися" for indicating location is a calque of Russian "находиться". Confirmed by Антоненко-Давидович (ad-148): this verb means "to find oneself" in Ukrainian, not "to be located." For static location, use "є", "міститься", or restructure.
Fix: Replace "Вона знаходиться прямо біля лікарні" → "Вона прямо біля лікарні" or "Вона є прямо біля лікарні."
```

```
[LINGUISTIC ACCURACY] [CRITICAL]
Location: Case cheat sheet, §6 Місцевий відмінок — "знаходитися *(to be located)*"
Issue: Teaching "знаходитися" as a standard Locative verb perpetuates the calque. Learners will internalize this as correct Ukrainian. Антоненко-Давидович says to use "бути, перебувати, міститися" instead.
Fix: Replace "знаходитися *(to be located)*" → "міститися *(to be located)*" in the cheat sheet verb list.
```

```
[LINGUISTIC ACCURACY] [CRITICAL]
Location: Dialogue 2 prose — "or sit «на прийомі» *(at an appointment)*"
Issue: The lemma "прийом" is NOT IN VESUM (verified via verify_lemma and verify_words). This is a Russicism from Russian "приём". Ukrainian alternative: "на прийманні" (from "приймання", which IS in VESUM).
Fix: Replace «на прийомі» with «на прийманні» or restructure to «у лікаря».
```

```
[PLAN ADHERENCE] [MAJOR]
Location: Діалог 1: Організовуємо день народження
Issue: Plan requires "Extended dialogue (12-15 exchanges)" but the actual dialogue has only 7 exchanges. This is roughly half the planned length. The module is above word target overall (2388 vs 2000), so the short dialogue reflects an imbalance — too much English explanation, not enough Ukrainian dialogue.
Fix: Expand Dialogue 1 to at least 12 exchanges. Add exchanges covering: deciding on a time, discussing who to invite specifically, debating between two restaurants, discussing what to wear — all using different cases.
```

```
[DIALOGUE QUALITY] [MAJOR]
Location: All three dialogues
Issue: While all dialogues are natural in tone, they are all shorter than "extended" — Dialogue 1 (7 exchanges), Dialogue 2 (~9 exchanges), Dialogue 3 (8 exchanges). For a synthesis module that aims to practice all 7 cases in dialogue, more exchanges = more natural case variety.
Fix: Expand each dialogue by 3-5 exchanges to create more organic case usage opportunities. This also addresses the plan adherence gap.
```

```
[ENGAGEMENT] [MINOR]
Location: Section 1 explanation paragraph — "In this dialogue, we see how the Vocative case and the Nominative plural function in a natural conversation."
Issue: Meta-commentary ("we see how X functions") — slightly lectured rather than demonstrated. Better to lead with the example.
Fix: Rephrase to lead with the observation: "When the friends address each other, they use the Vocative case..."
```

## Verdict: REVISE

Three critical linguistic errors (two involving "знаходитися" calque, one "прийом" Russicism) and a major plan adherence gap (Dialogue 1 at 7 exchanges vs. planned 12-15). The critical errors are especially concerning because one of them (`знаходитися` in the cheat sheet) **teaches** incorrect Ukrainian — a learner will memorize this calque as a standard verb. The content is otherwise strong: vocabulary coverage is excellent, case explanations are accurate, and dialogues are natural in tone. Fixes are targeted and will not require a rewrite.

<fixes>
- find: "Вона знаходиться прямо біля лікарні."
  replace: "Вона — прямо біля лікарні."
- find: "or sit «на прийомі» *(at an appointment)*"
  replace: "or sit «у лікаря» *(at the doctor's)*"
- find: "**Дієслова:** *(Verbs:)* жити *(to live)*, знаходитися *(to be located)*, сидіти *(to sit)*."
  replace: "**Дієслова:** *(Verbs:)* жити *(to live)*, міститися *(to be located)*, сидіти *(to sit)*."
- find: "In this dialogue, we see how the Vocative case and the Nominative plural function in a natural conversation. When the friends address each other, they use the Vocative case. You can hear this in the forms"
  replace: "When the friends address each other, they use the Vocative case. You can hear this in the forms"
</fixes>

**Note to pipeline:** The dialogue length issue (7 exchanges vs. 12-15 planned) cannot be fixed with find/replace — it requires content generation. If a second review round still shows short dialogues, escalate to a targeted rewrite of Dialogue 1 only.
