## Linguistic Scan

**Four separate checks:**

1. **Russianisms** — No Russian ghost words detected. All vocabulary is natural Ukrainian.
2. **Surzhyk** — None detected.
3. **Calques** — None detected. "Замовити торт" verified as correct Ukrainian (per Антоненко-Давидович). "Виписати рецепт" is natural Ukrainian. "Ставити діагноз" — standard.
4. **Paronyms** — None detected.

**Russian characters (ы, э, ё, ъ):** None found.

**Factually wrong grammar claim — CRITICAL:**

The module states: *"The Locative case describes the setting where the action or conversation takes place. You wait «у лікарні» (in the hospital), buy pills «в аптеці» (in the pharmacy), or sit «у лікаря» (at the doctor's)."*

VESUM confirms that «лікаря» is the **Genitive** form (`v_rod`), NOT Locative. The Locative forms of «лікар» are: лікареві, лікарі, лікарю (`v_mis`). The construction «у лікаря» = "at the doctor's [office]" uses **Genitive** to express "at someone's place" — a well-known Ukrainian Genitive pattern (cf. «у бабусі» = at grandma's, also Genitive). Grouping it with Locative examples teaches the wrong case and will confuse learners.

No other linguistic errors found. All 406 common words verified by VESUM. The 18 "not found" entries are proper nouns (Андрій, Київ, Львів, Одеса, Карпати, etc.) — expected.

## Exercise Check

**Activity markers found:**
1. `<!-- INJECT_ACTIVITY: quiz, Identify which case a highlighted noun is in and explain why -->` — After Dialogue 1. Matches plan `activity_hints[1]`. Correct placement after case-rich dialogue. ✓
2. `<!-- INJECT_ACTIVITY: fill-in, Complete gaps in a dialogue with the correct case form — all 7 cases represented, both singular and plural, 8 items -->` — After Dialogue 2. Matches plan `activity_hints[0]`. Correct placement. ✓
3. `<!-- INJECT_ACTIVITY: match-up, Match sentence halves so that the case form in the first half agrees with the preposition/verb in the second half -->` — After Dialogue 3. Matches plan `activity_hints[2]`. Correct placement. ✓
4. `<!-- INJECT_ACTIVITY: error-correction, Find and fix wrong case endings across all 7 cases -->` — In Самоперевірка section. Matches plan `activity_hints[3]`. Correct placement. ✓

All 4 activity types from plan are present with markers in the right positions. Item counts specified. Markers are spread across sections, not clustered.

**Plan point gap:** Plan section 2 specifies *"After dialogue: learner rewrites selected sentences changing singular to plural (один пацієнт → багато пацієнтів)."* The prose discusses this concept but there is no dedicated exercise marker for singular→plural rewriting. The fill-in marker covers "both singular and plural" generally but doesn't specifically implement the rewriting exercise format described in the plan.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | **Deductions:** (a) Plan specifies Dialogue 1 should have "12-15 exchanges" — actual dialogue has only ~7 exchanges (Оксана: 4 turns, Андрій: 3 turns). (b) Required vocabulary «визначне місце» (landmark, sight) from `vocabulary_hints.required` is absent from the content — not found in any dialogue or explanation. (c) Plan section 2 specifies a singular→plural rewriting exercise; this is discussed in prose but not implemented as a distinct exercise. **Credits:** All 4 sections present and correctly ordered. Cultural note on birthday traditions included per plan ("не гості дарують вечірку, а іменинник частує"). All 4 activity types from `activity_hints` have markers. Case cheat sheet present per plan. All 3 dialogue settings match plan (birthday party, hospital, travel). |
| 2. Linguistic accuracy | 7/10 | **Critical error:** «у лікаря» presented as Locative case alongside «у лікарні» and «в аптеці». VESUM confirms «лікаря» is Genitive (`v_rod`), not Locative. The Locative forms are лікареві/лікарі/лікарю (`v_mis`). This teaches the wrong case. **Credits:** All other case forms verified correct — vocatives (Оксано, Андрію, Друже, Тарасе, Лікарю), genitives (торта, гостей, температури), datives (Олені, друзям, пацієнтові), instrumentals (з друзями, кулями, потягом, Карпатами). No Russianisms, surzhyk, or calques. Vowel alternation і→о explanation (Львів→Львова) is correct. |
| 3. Pedagogical quality | 8/10 | **Credits:** Clear PPP flow — dialogues present cases in context, explanations extract patterns, exercises practice. Multiple examples per grammar point (e.g., Instrumental: «з друзями», «кулями», «потягом», «автівкою», «Карпатами» — 5 examples). Grammar explanations are contextualized, not bare lists. Trigger-based teaching (verb/preposition → case) is consistent. **Minor deduction:** The «у лікаря» error undermines the Locative teaching. Some explanations are English-heavy without immediate Ukrainian follow-up (e.g., the paragraph "Medical conversations naturally require..." runs ~40 words of English before the first Ukrainian example). |
| 4. Vocabulary coverage | 8/10 | **Required vocab present (9/10):** вечірка ✓ (Dialogue 1 intro), подарунок ✓ (Dialogue 1), лікар ✓ (Dialogue 2), пацієнт ✓ (Dialogue 2), здоров'я ✓ ("Бажаю вам здоров'я!"), ліки ✓ (Dialogue 2), подорож ✓ (Dialogue 3 title+intro), потяг ✓ (Dialogue 3), запрошувати ✓ (cultural note "іменинник запрошує гостей"). **Missing:** визначне місце ✗ — not used anywhere despite being required. **Recommended vocab (5/5):** рецепт ✓, температура ✓, Карпати ✓, милуватися ✓, частувати ✓. All introduced naturally in context. |
| 5. Exercise quality | 9/10 | All 4 markers correctly placed after relevant teaching sections. Types and focus descriptions match plan exactly. Item counts specified (8, 8, 8, 6 — matches plan). Exercises test language skills (case identification, form completion, matching, error correction) not content recall. Slight concern that the fill-in marker should more explicitly address the singular→plural rewriting from plan section 2. |
| 6. Engagement & tone | 8/10 | **Credits:** Dialogues feel natural — friends planning a party, a realistic doctor visit, friends dreaming about a road trip. Cultural details are specific (birthday person treats guests, Ukrainian city names, Khreshchatyk). No motivational openers or gamified language. **Minor deduction:** "The Instrumental case is your best friend when talking about modes of transportation" — cliché phrasing. One instance of slight lecture-mode: "Understanding the Genitive plural is crucial because..." |
| 7. Structural integrity | 9/10 | All 4 H2 sections present and ordered per plan. Clean markdown. No stray tags or formatting artifacts. Word count 2370/2000 = 118.5% — above target. Activity markers cleanly formatted. |
| 8. Cultural accuracy | 10/10 | Birthday tradition correctly explained ("не гості дарують вечірку, а іменинник частує"). Decolonized — Ukrainian presented on its own terms, no Russian comparisons. Real Ukrainian geography (Київ, Львів, Одеса, Карпати, Умань, Хрещатик). Medical etiquette (пане докторе) culturally appropriate. |
| 9. Dialogue quality | 8/10 | **Credits:** Named speakers throughout (Оксана, Андрій, Лікар, Пацієнт, Тарас). Natural scenarios — surprise party planning, describing symptoms, dreaming about a road trip. Culturally appropriate responses ("Одужуйте швидше!", "Бажаю вам здоров'я!"). Distinct voices — Оксана is the organizer, Андрій handles the cake; the patient is nervous, the doctor is calm and professional. **Deduction:** Dialogue 1 has only ~7 exchanges vs plan's 12-15. All three dialogues could benefit from 2-3 more turns to feel more "extended." |

## Findings

**[LINGUISTIC ACCURACY] [CRITICAL]**
Location: Dialogue 2 explanatory prose, paragraph starting "The Instrumental case is very common..."
Issue: «у лікаря» is presented as a Locative case example: *"You wait «у лікарні» (in the hospital), buy pills «в аптеці» (in the pharmacy), or sit «у лікаря» (at the doctor's)."* VESUM confirms «лікаря» is Genitive (`v_rod`). The Locative forms of «лікар» are лікареві/лікарі/лікарю. The pattern «у + Genitive» = "at someone's place" is a Genitive construction, not Locative. This teaches the wrong case.
Fix: Remove «у лікаря» from the Locative examples and replace with a true Locative example, adding a note about the Genitive pattern.

**[PLAN ADHERENCE] [MAJOR]**
Location: Діалог 1: Організовуємо день народження
Issue: Plan specifies "Extended dialogue (12-15 exchanges)" but the actual dialogue has only ~7 exchanges. This is roughly half the planned length.
Fix: Expand Dialogue 1 with 5-6 additional exchanges that naturally incorporate more case examples (e.g., discussing what to write on the card [Dat], where to park [Loc], who hasn't confirmed yet [Gen]).

**[VOCABULARY COVERAGE] [MAJOR]**
Location: Entire module
Issue: Required vocabulary item «визначне місце» (landmark, sight) from `vocabulary_hints.required` is absent. The plan's Dialogue 3 section explicitly mentions "багато визначних місць" as a planned phrase. Searched all sections — not found.
Fix: Insert «визначне місце» naturally into Dialogue 3, e.g., in the travel discussion about what to see.

**[ENGAGEMENT & TONE] [MINOR]**
Location: Dialogue 3 explanatory prose, paragraph about transportation
Issue: "The Instrumental case is your best friend when talking about modes of transportation" — cliché phrasing ("your best friend").
Fix: Replace with direct teaching statement.

## Verdict: REVISE

The module has one critical linguistic error (teaching «у лікаря» as Locative when VESUM confirms it's Genitive), one major plan adherence gap (Dialogue 1 at ~7 exchanges vs planned 12-15), and a missing required vocabulary item (визначне місце). The critical error alone requires REVISE — it would teach learners the wrong case.

<fixes>
- find: "You wait «у лікарні» *(in the hospital)*, buy pills «в аптеці» *(in the pharmacy)*, or sit «у лікаря» *(at the doctor's)*. Remember that the Locative case always requires a preposition to indicate a place."
  replace: "You wait «у лікарні» *(in the hospital)*, buy pills «в аптеці» *(in the pharmacy)*, or are examined «на прийомі» *(at the appointment)*. Remember that the Locative case always requires a preposition to indicate a place. Be careful with «у лікаря» *(at the doctor's)* — this looks similar, but «лікаря» is actually **Genitive**, not Locative. The pattern «у + Genitive» means \"at someone's place\" (cf. «у бабусі» = at grandma's)."
- find: "The Instrumental case is your best friend when talking about modes of transportation."
  replace: "The Instrumental case is essential for expressing modes of transportation."
- find: "Хлопці хочуть відвідати багато різних міст, побачити тепле Чорне море і високі Карпати."
  replace: "Хлопці хочуть відвідати багато різних міст, побачити кожне визначне місце, тепле Чорне море і високі Карпати."
- find: "Згоден. З Києва ми можемо поїхати **до Львова** *(to Lviv)*. У Львові живе моя сестра. Ми можемо купити подарунки **друзям у Львові** *(to friends in Lviv)*."
  replace: "Згоден. З Києва ми можемо поїхати **до Львова** *(to Lviv)*. У Львові є багато **визначних місць** *(landmarks)*. Там живе моя сестра. Ми можемо купити подарунки **друзям у Львові** *(to friends in Lviv)*."
- find: "— **Андрій:** Чудова ідея! Ми відсвяткуємо день народження з друзями дуже весело. *(Great idea! We will celebrate the birthday with friends very cheerfully.)*\n> — **Оксана:** Так! Я зараз напишу друзям точну адресу кафе. *(Yes! I will write the exact address of the cafe to the friends right now.)*"
  replace: "— **Андрій:** Чудова ідея! Ми відсвяткуємо день народження з друзями дуже весело. *(Great idea! We will celebrate the birthday with friends very cheerfully.)*\n> — **Оксана:** Я бачила в Олени гарну сукню. Може, купимо щось до неї? *(I saw Olena has a nice dress. Maybe we should buy something to go with it?)*\n> — **Андрій:** Так, можемо купити їй шарф. А хто напише привітання на листівці? *(Yes, we could buy her a scarf. And who will write the greeting on the card?)*\n> — **Оксана:** Я напишу! Я маю гарний почерк. А ти подумай про музику на вечірку. *(I will write it! I have nice handwriting. And you think about the music for the party.)*\n> — **Андрій:** Добре. Я попрошу Сергія принести колонку. Він завжди має гарну музику. *(Good. I will ask Serhiy to bring a speaker. He always has good music.)*\n> — **Оксана:** Чудово! А де ми поставимо подарунки? На столі чи на полиці? *(Wonderful! And where will we put the gifts? On the table or on the shelf?)*\n> — **Андрій:** Краще на столі біля входу. Олена побачить їх одразу! *(Better on the table near the entrance. Olena will see them right away!)*\n> — **Оксана:** Ідеально! Я зараз напишу друзям точну адресу кафе. *(Perfect! I will write the exact address of the cafe to the friends right now.)*"
</fixes>
