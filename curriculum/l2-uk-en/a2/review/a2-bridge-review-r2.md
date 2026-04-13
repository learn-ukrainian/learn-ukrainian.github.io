## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym confusions, or Russian characters found.

Definite linguistic error:
- **Магія української фонології**: "У мене зараз ніколи немає вільного часу." This misuses **ніколи**. Local dictionary lookup confirms **ніколи** can be an adverb meaning "never" and a predicative word meaning "there is no time / I have no time" in patterns like **Мені ніколи**, but not in this hybrid construction.

## Exercise Check
All 4 planned activity markers are present and placed after the relevant teaching:
- `quiz-case-identification` after the cases section
- `fill-in-phonological-alternations` after the phonology section
- `match-up-euphony-choice` after the euphony section
- `error-correction-euphony` after the euphony section

The marker count matches the plan exactly. No exercise-logic defects are visible here because the actual YAML exercise content is not shown, only the injection markers.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The module covers the four A1 cases, the seven-case map, stress, affricates, and the A2 roadmap, but the plan point "first palatalization (г/ж, к/ч, х/ш) ... нога/ніжка, рука/ручка" is missing. Search confirmed 0 occurrences of `г/ж`, `к/ч`, `х/ш`, and `ніжка`. The roadmap also omits verb conjugation patterns. |
| 2. Linguistic accuracy | 7/10 | The sentence "У мене зараз ніколи немає вільного часу" is a real Ukrainian usage error in the stress section, so one of the model examples teaches a bad pattern. |
| 3. Pedagogical quality | 6/10 | Section 1 opens with a 122-word English theory paragraph before the first Ukrainian example, and the phonology section opens with a 120-word English theory paragraph before examples. That weakens the intended PPP flow. |
| 4. Vocabulary coverage | 9/10 | All required plan vocabulary appears in prose, including `відмінок`, `називний`, `знахідний`, `місцевий`, `кличний`, `чергування`, `голосний`, `приголосний`, and `наголос`. |
| 5. Exercise quality | 9/10 | All four planned activity markers are present, correctly typed, and positioned after the relevant teaching sections. No inline exercise logic errors are visible in the supplied content. |
| 6. Engagement & tone | 7/10 | The teacher voice is warm, but phrases like "Welcome to the A2 level!" and "As you continue your journey into the A2 level" add filler instead of instruction. |
| 7. Structural integrity | 10/10 | All four H2 sections from the plan are present and in order, the markdown is clean, and the pipeline word count is 2617, which is above target. |
| 8. Cultural accuracy | 10/10 | No Russocentric framing or cultural inaccuracies found; Ukrainian is presented on its own terms. |
| 9. Dialogue & conversation quality | 7/10 | The opening exchange is mostly teacher questions: "Що ви робите тут сьогодні?" and "Де ви зараз живете?" It reads more like an interview than a natural first-day school interaction. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Магія української фонології** — "Український наголос може повністю змінити значення слова. Старий замок стоїть на високій горі. Але я не можу відкрити цей замок на дверях. У мене зараз ніколи немає вільного часу. Я ніколи не пив таку смачну каву."  
Issue: "У мене зараз ніколи немає вільного часу" is not a correct way to illustrate the predicative/adverb contrast of **ніколи**. It teaches a malformed sentence.  
Fix: Replace it with **"Мені зараз ніколи."** so the contrast with **"Я ніколи не пив..."** is valid.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: **Магія української фонології** — "Equally important are the consonant alternations. In these noun forms, Ukrainian shows the alternations «г/з», «к/ц», and «х/с» before the ending «і»."  
Issue: The plan requires coverage of **first palatalization** `г/ж, к/ч, х/ш` with examples like `нога/ніжка` and `рука/ручка`. The module teaches a different alternation before `-і` and never covers the planned one.  
Fix: Add one short teaching sentence naming `г/ж, к/ч, х/ш` and giving the planned examples.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: **Що нас чекає на рівні А2?** — "You also learned the **місцевий** (locative) for locations and the **кличний** (vocative) for direct address. In A2, we will conquer the Genitive, Dative, and Instrumental cases. However, the most significant milestone is your introduction to verbal aspect." and "Також ми будемо багато говорити про дієслова руху."  
Issue: The roadmap omits the plan point about **verb conjugation patterns**.  
Fix: Add verb conjugation/дієвідмінювання to the A2 roadmap in both the English and Ukrainian roadmap paragraphs.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: **Пригадуємо відмінки** — "Welcome to the A2 level! In this first module, we are taking a step back..." and **Магія української фонології** — "As you continue your journey into the A2 level..."  
Issue: Both sections begin with long English theory blocks before the first Ukrainian example. That delays pattern recognition and weakens the PPP sequence of situation -> pattern -> practice.  
Fix: Compress the English setup and lead with short example-driven explanations.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: **Пригадуємо відмінки** — "Welcome to the A2 level!" and **Магія української фонології** — "As you continue your journey into the A2 level..."  
Issue: These openings sound generic and padded rather than like a focused teacher.  
Fix: Replace them with concise instructional framing tied directly to the examples.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: Opening dialogue — "Що ви робите тут сьогодні?" / "Де ви зараз живете?"  
Issue: The scene is mostly teacher-led questioning, so it feels stiff and transactional instead of like a natural arrival conversation at a language school.  
Fix: Rewrite 1-2 turns so the student volunteers information and the teacher responds, while still reviewing nominative, accusative, locative, and vocative.

## Verdict: REVISE
REVISE. There is one critical linguistic error that cannot ship, plus major plan-adherence, pedagogy, and dialogue issues. Several dimensions are below 9, so this does not meet the PASS gate.

<fixes>
- find: |-
    Український наголос може повністю змінити значення слова. Старий замок стоїть на високій горі. Але я не можу відкрити цей замок на дверях. У мене зараз ніколи немає вільного часу. Я ніколи не пив таку смачну каву.
  replace: |-
    Український наголос може повністю змінити значення слова. Старий замок стоїть на високій горі. Але я не можу відкрити цей замок на дверях. Мені зараз ніколи. Я ніколи не пив таку смачну каву.
- find: |-
    Welcome to the A2 level! In this first module, we are taking a step back to review the foundational grammar you learned in A1. The absolute cornerstone of Ukrainian grammar is the concept of a **відмінок** (case). Cases are simply different forms of a noun that show its exact grammatical role in a sentence. Instead of relying purely on word order like English does, the Ukrainian language uses specific word endings to distinguish between the person doing the action, the object receiving the action, or the physical location where the action happens. This constant process of changing endings to fit the context is called declension. Let us thoroughly review the four essential cases you already know before we introduce the remaining ones.
  replace: |-
    In this first A2 module, we briefly review the grammar from A1 before moving on. Ukrainian uses **відмінки** (cases) to show who does the action, what receives it, and where the action happens. Compare: «Я — студент», «Я вивчаю українську мову», «Я живу в Києві». Let us briefly refresh these familiar patterns before we add the new cases.
- find: |-
    As you continue your journey into the A2 level, you will start noticing that Ukrainian words sometimes change their internal structure when they take on new endings. These changes in word stems during declension might look like random exceptions at first glance, but they are actually predictable and deeply historical patterns. They exist to make the language flow naturally and beautifully. The primary mechanism behind this is the concept of **чергування** (alternation), where a specific **голосний** (vowel) or a **приголосний** (consonant) is swapped for another sound within the root of a word. Understanding these core rules of phonology will save you hours of memorization and give you a solid foundation for predicting how new words behave when you decline them.
  replace: |-
    In A2, you will notice that Ukrainian words sometimes change inside the stem when a new ending appears. Compare «стіл/стола», «Київ/Києва», and «рука/у руці». These are regular patterns of **чергування** (alternation), not random exceptions, and learning them early makes declension much easier to predict.
- find: |-
    Equally important are the consonant alternations. In these noun forms, Ukrainian shows the alternations «г/з», «к/ц», and «х/с» before the ending «і».
     When you use feminine nouns in the Dative or Locative cases, the final consonant of the root often changes before the ending «і». If the noun stem ends in the letters «г», «к», or «х», they soften and mutate into «з», «ц», and «с» respectively. This softening is completely mandatory for natural speech. For example, the word «нога» (leg) becomes «на нозі» (on the leg), the word «рука» (hand) changes to «у руці» (in the hand), and «муха» (fly) turns into «на мусі» (on the fly).
  replace: |-
    Equally important are two consonant-alternation patterns. In these noun forms, Ukrainian shows the alternations «г/з», «к/ц», and «х/с» before the ending «і». You will also meet the first palatalization «г/ж», «к/ч», and «х/ш» in related forms such as «нога/ніжка» and «рука/ручка».
     When you use feminine nouns in the Dative or Locative cases, the final consonant of the root often changes before the ending «і». If the noun stem ends in the letters «г», «к», or «х», they soften and mutate into «з», «ц», and «с» respectively. This softening is completely mandatory for natural speech. For example, the word «нога» (leg) becomes «на нозі» (on the leg), the word «рука» (hand) changes to «у руці» (in the hand), and «муха» (fly) turns into «на мусі» (on the fly).
- find: |-
    You also learned the **місцевий** (locative) for locations and the **кличний** (vocative) for direct address. In A2, we will conquer the Genitive, Dative, and Instrumental cases. However, the most significant milestone is your introduction to verbal aspect.
  replace: |-
    You also learned the **місцевий** (locative) for locations and the **кличний** (vocative) for direct address. In A2, we will conquer the Genitive, Dative, and Instrumental cases. However, the most significant milestones are your introduction to verbal aspect and your first systematic work with core verb conjugation patterns.
- find: |-
    Ми вивчимо нові відмінки, але найголовніше — це вид дієслова. Ти дізнаєшся, як показати процес дії або її результат. Також ми будемо багато говорити про дієслова руху.
  replace: |-
    Ми вивчимо нові відмінки, але найголовніше — це вид дієслова. Ти дізнаєшся, як показати процес дії або її результат. Також ми будемо працювати з базовими моделями дієвідмінювання і багато говорити про дієслова руху.
- find: |-
    > — **Викладач:** Добрий день! Ласкаво просимо до нашої школи. *(Good afternoon! Welcome to our school.)*
    > — **Новий студент:** Добрий день! Я — новий студент. *(Good afternoon! I am a new student.)*
    > — **Викладач:** Дуже приємно. Що ви робите тут сьогодні? *(Nice to meet you. What are you doing here today?)*
    > — **Новий студент:** Я вивчаю українську мову. *(I am studying the Ukrainian language.)*
    > — **Викладач:** Чудово. Де ви зараз живете? *(Wonderful. Where are you living now?)*
    > — **Новий студент:** Я живу в Києві, але моя сім'я живе у Львові. *(I live in Kyiv, but my family lives in Lviv.)*
    > — **Викладач:** Зрозуміло. Привіт, Оксано! Це наш новий учень. *(I see. Hi, Oksana! This is our new student.)*
    > — **Оксана:** Вітаю, друже! *(Greetings, friend!)*
  replace: |-
    > — **Викладач:** Добрий день! Ласкаво просимо до нашої школи. Ви на курс А2? *(Good afternoon! Welcome to our school. Are you here for the A2 course?)*
    > — **Новий студент:** Добрий день! Так, я новий студент. Я вже вивчаю українську мову й дуже радий бути тут. *(Good afternoon! Yes, I am a new student. I am already studying Ukrainian and I am very glad to be here.)*
    > — **Викладач:** Чудово. Багато наших студентів живуть у Києві, а їхні родини — в інших містах. А як у вас? *(Wonderful. Many of our students live in Kyiv, while their families are in other cities. What about you?)*
    > — **Новий студент:** Я живу в Києві, але моя сім'я живе у Львові. *(I live in Kyiv, but my family lives in Lviv.)*
    > — **Викладач:** Зрозуміло. Оксано, познайомся: це наш новий студент. *(I see. Oksana, meet our new student.)*
    > — **Оксана:** Вітаю, друже! Рада знайомству. *(Hi, friend! Nice to meet you.)*
</fixes>