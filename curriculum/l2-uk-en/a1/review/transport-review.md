## Linguistic Scan
No linguistic errors found regarding Russianisms, Surzhyk, or Calques in the generated Ukrainian text itself. However, there is a **CRITICAL factual linguistic error** in the English pedagogical explanation: the text falsely claims that the Ukrainian word «відправлятися» is a "direct phonetic calque from Russian." This is completely false. The word is standard, attested in СУМ-11, and widely used in official contexts (e.g., час відправлення).

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-ticket-buying -->` (Under Діалоги) - Matches "Buy a ticket" fill-in from plan.
- `<!-- INJECT_ACTIVITY: quiz-transport-patterns -->` (Under Транспорт) - Matches "Автобусом or на метро" quiz from plan.
- `<!-- INJECT_ACTIVITY: quiz-match-situation -->` (Under Транспорт) - Matches "Which transport" quiz from plan.
- `<!-- INJECT_ACTIVITY: fill-in-directions -->` (Under Корисні фрази) - Matches "Ask for directions" fill-in from plan.
*All markers are present, correctly ordered, placed immediately after the relevant instruction, and perfectly match the plan's `activity_hints`.*

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The writer deliberately avoided the target phrase from the plan's Dialogue 2 ("О котрій відправлення?") because of a hallucinated linguistic rule. All other points were hit perfectly. |
| 2. Linguistic accuracy | 7/10 | The text contains a critical hallucination, falsely claiming that "відправлятися" is a "direct phonetic calque from Russian" when it is actually a standard Ukrainian word. The rest of the Ukrainian text is grammatically accurate. |
| 3. Pedagogical quality | 9/10 | Excellent explanation of instrumental vs prepositional transport patterns, including a great caution box. Minor deduction for literal English translations in the dialogue ("how to get to the train station?", "Take a bus or by metro"). |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary included naturally. |
| 5. Exercise quality | 10/10 | The markers match the plan's required activities perfectly and are placed effectively. |
| 6. Engagement & tone | 10/10 | Natural, encouraging, and culturally embedded. |
| 7. Structural integrity | 10/10 | All sections present, word count (1690) comfortably exceeds the target (1200). |
| 8. Cultural accuracy | 10/10 | References to Boryspil, Kyiv Metro, marshrutkas, and crowded transport etiquette are spot on. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are natural, though Dialogue 2 had a redundant turn inserted by the writer ("Є потяг о дев'ятій ранку" followed by "О котрій годині він рушає?") to avoid using the word "відправлення". |

## Findings
[2. Linguistic accuracy] [CRITICAL]
Location: Корисні фрази (Useful Phrases) section — "Many learners mistakenly use the word «відправлятися» (to depart), but this is a direct phonetic calque from Russian and sounds unnatural in standard conversational Ukrainian."
Issue: The writer hallucinated a hyper-correction. "Відправлятися" is not a phonetic calque from Russian; it is a standard Ukrainian word widely used in official contexts (e.g., час відправлення on tickets). Teaching learners that it is a calque is factually false.
Fix: Rewrite the sentence to explain that while "відправлятися" is used on printed schedules, conversational Ukrainian prefers specific motion verbs.

[1. Plan adherence] [MAJOR]
Location: Діалоги (Dialogues) section — "> **Пасажир:** Дякую. О котрій годині він рушає?"
Issue: The plan explicitly asked to teach "О котрій відправлення?". The writer avoided it because of the hallucinated linguistic rule, making the dialogue slightly redundant.
Fix: Restore the plan's exact dialogue turns. Also update the Summary paragraph to match this restoration.

[3. Pedagogical quality] [MINOR]
Location: Діалоги (Dialogues) section
Issue: The English translations are literal and clunky (e.g., "how to get to the train station?", "Take a bus or by metro").
Fix: Smooth out the English translations to sound natural ("how do I get to the train station?", "Go by bus or by metro").

[3. Pedagogical quality] [MINOR]
Location: Підсумок — Summary
Issue: The self-check translation introduces "залізничний вокзал" which wasn't taught in the text (the text just used "вокзал").
Fix: Change it to "Де вокзал?".

## Verdict: REVISE
The module is overall excellent, with strong pedagogy and deep cultural context. However, it contains a critical hallucination where it falsely teaches learners that the standard Ukrainian word "відправлятися" is a Russian calque. This linguistic falsehood must be corrected, and the intended dialogue from the plan must be restored.

<fixes>
- find: "Вибачте, як дістатися до вокзалу? *(Excuse me, how to get to the train station?)*"
  replace: "Вибачте, як дістатися до вокзалу? *(Excuse me, how do I get to the train station?)*"
- find: "Їдьте автобусом або на метро. *(Take a bus or by metro.)*"
  replace: "Їдьте автобусом або на метро. *(Go by bus or by metro.)*"
- find: "Який автобус? А можна на метро? *(Which bus? And is it possible by metro?)*"
  replace: "Який автобус? А можна на метро? *(Which bus? Can I take the metro?)*"
- find: "> **Касир:** П'ятсот гривень. Є потяг о дев'ятій ранку. *(Five hundred hryvnias. There is a train at nine in the morning.)*\n> **Пасажир:** Дякую. О котрій годині він рушає? *(Thank you. At what time does it depart?)*\n> **Касир:** О дев'ятій рівно. *(At nine exactly.)*"
  replace: "> **Касир:** П'ятсот гривень. *(Five hundred hryvnias.)*\n> **Пасажир:** Дякую. О котрій відправлення? *(Thank you. At what time is the departure?)*\n> **Касир:** О дев'ятій ранку. *(At nine in the morning.)*"
- find: "Many learners mistakenly use the word «відправлятися» (to depart), but this is a direct phonetic calque from Russian and sounds unnatural in standard conversational Ukrainian. Instead, you must use native verbs that describe motion accurately based on the type of vehicle."
  replace: "While you will frequently see the formal noun **відправлення** (departure) or the verb **відправлятися** (to depart) on printed tickets and official schedules, conversational Ukrainian often prefers native verbs that describe motion accurately based on the type of vehicle."
- find: "inquiring about transit schedules using precise phrases like **о котрій годині** (at what time) and the authentic Ukrainian motion verb **рушати** (to depart)."
  replace: "inquiring about transit schedules using precise phrases like **о котрій відправлення** (at what time is the departure) and authentic Ukrainian motion verbs like **рушати** (to depart)."
- find: "«Де залізничний вокзал?»"
  replace: "«Де вокзал?»"
</fixes>
