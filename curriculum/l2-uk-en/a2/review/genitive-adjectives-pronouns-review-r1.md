## Linguistic Scan
Errors found:
1. `телефона` — In standard Ukrainian, inanimate objects like "телефон" take the `-у` ending in the Genitive singular (`телефону`). Using `-а` is colloquial and incorrect for standard A2 pedagogy.

## Exercise Check
- `genitive-adjectives-fill` (after Adjective section): Placed correctly. Tests what was taught. Matches hint 1.
- `possessive-pronouns-quiz` (after Possessives section): Placed correctly. Matches hint 2.
- `genitive-phrases-match` (after Possessives section): Placed correctly. Matches hint 3.
- `demonstrative-adjective-noun-fill` (after Demonstratives section): Placed correctly. Matches hint 4.
- `genitive-phrases-correction` (after Demonstratives section): Placed correctly. Matches hint 5.
All 5 `<!-- INJECT_ACTIVITY: -->` markers are properly placed and logically follow the teaching content.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covers all grammar points and vocabulary perfectly. Adapts the "lost and found" dialogue from a suitcase to a phone, which is acceptable but misses the specific noun suggested. |
| 2. Linguistic accuracy | 8/10 | Incorrectly teaches that the Genitive of "телефон" is "телефона" (`**Якого** телефона?`). The standard Genitive singular form is "телефону". |
| 3. Pedagogical quality | 6/10 | Contains a critical pedagogical trap: the writer conflated the masculine animate Accusative case (which looks exactly like the Genitive) with true Genitive constructions. Teaching "Що ти знаєш про того чоловіка?" and "Він довго шукає великого чорного кота." in a Genitive lesson teaches learners that "про" or "шукати (concrete objects)" take the Genitive case, which is completely wrong (they take Accusative). |
| 4. Vocabulary coverage | 10/10 | All required and recommended words (прикметник, узгодження, вчителька, старший, дівчина) are integrated naturally into the prose and examples. |
| 5. Exercise quality | 10/10 | The 5 required exercise markers correspond directly to the plan's `activity_hints` and are distributed well. |
| 6. Engagement & tone | 9/10 | The tone is direct, encouraging, and clear. Dialogues are practical and grounded in real-world scenarios. |
| 7. Structural integrity | 10/10 | Excellent structure. No markdown artifacts. Grammar notes (`:::note`) are used perfectly to summarize endings. |
| 8. Cultural accuracy | 10/10 | Good use of culturally appropriate Ukrainian names (Богдан, Олена, Дмитро) and authentic context. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues flow well, especially the "lost and found" scenario and the casual exchanges about neighbors and gifts. |

## Findings

[2. Linguistic accuracy] [critical]
Location: `**Якого** телефона? *(Which phone? — Genitive)*`
Issue: The Genitive form of the inanimate noun "телефон" is "телефону", not "телефона". Teaching "телефона" as the standard Genitive form is factually incorrect.
Fix: Change "телефона" to "телефону".

[3. Pedagogical quality] [critical]
Location: `> — **Власник:** Добрий день! Я шукаю свого нового телефона.`
Issue: The verb "шукати" with a specific concrete inanimate object technically takes the Accusative case (свій новий телефон). Presenting this as the opening dialogue for a Genitive lesson is highly confusing.
Fix: Replace with a clear, unambiguous Genitive construction: `У вас немає мого нового телефону?`

[3. Pedagogical quality] [critical]
Location: `Він довго шукає великого чорного кота. *(He is looking for a big black cat for a long time.)*`
Issue: "Шукати" + an animate noun takes the Accusative case. Because masculine animate Accusative matches Genitive exactly, using this as an example misleads learners into thinking this is a Genitive usage.
Fix: Replace with a strict Genitive construction using negation: `Тут поблизу немає великого чорного кота.`

[3. Pedagogical quality] [critical]
Location: `> — **Олег:** Ти знаєш його нового друга? *(Do you know his new friend?)*`
Issue: The verb "знати" takes the Accusative case. Again, using an animate Accusative noun as an example in a Genitive lesson is a severe pedagogical flaw.
Fix: Replace with a true Genitive trigger: `Це подарунок для його нового друга?`

[3. Pedagogical quality] [critical]
Location: `> — **Віктор:** Що ти знаєш про того чоловіка?` and `але я знаю цього хлопця.`
Issue: The preposition "про" strictly dictates the Accusative case. Teaching "про того чоловіка" as an example of Genitive usage teaches a fundamentally wrong grammatical rule.
Fix: Replace with true Genitive constructions using "для": `Чи є лист для того чоловіка?` and `Немає листа для того чоловіка, але є для цього хлопця.`

## Verdict: REVISE
The module requires revision due to multiple critical pedagogical errors where Accusative case constructions (involving animate masculine nouns or the preposition "про") were incorrectly presented as examples of the Genitive case. The structural and linguistic fixes are provided below.

<fixes>
- find: |
    > — **Власник:** Добрий день! Я шукаю свого нового телефона. *(Good day! I am looking for my new phone.)*
    > — **Працівник:** Якого телефона? У нас сьогодні дуже багато знайдених телефонів. *(Which phone? We have a lot of found phones today.)*
    > — **Власник:** Великого чорного телефона. *(A big black phone.)*
  replace: |
    > — **Власник:** Добрий день! У вас немає мого нового телефону? *(Good day! Do you not have my new phone?)*
    > — **Працівник:** Якого телефону? У нас сьогодні дуже багато знайдених телефонів. *(Which phone? We have a lot of found phones today.)*
    > — **Власник:** Великого чорного телефону. *(A big black phone.)*
- find: |
    **Який** телефон? *(Which phone? — Nominative)*
    **Якого** телефона? *(Which phone? — Genitive)*
  replace: |
    **Який** телефон? *(Which phone? — Nominative)*
    **Якого** телефону? *(Which phone? — Genitive)*
- find: |
    Він довго шукає великого чорного кота. *(He is looking for a big black cat for a long time.)*
  replace: |
    Тут поблизу немає великого чорного кота. *(There is no big black cat nearby here.)*
- find: |
    > — **Олег:** Ти знаєш його нового друга? *(Do you know his new friend?)*
    > — **Ірина:** Ні, я ніколи не бачила його друга. *(No, I have never seen his friend.)*
  replace: |
    > — **Олег:** Це подарунок для його нового друга? *(Is this a gift for his new friend?)*
    > — **Ірина:** Ні, я не бачила його друга сьогодні. *(No, I have not seen his friend today.)*
- find: |
    > — **Віктор:** Що ти знаєш про того чоловіка? *(What do you know about that man?)*
    > — **Марія:** Я нічого не знаю про того чоловіка, але я знаю цього хлопця. *(I know nothing about that man, but I know this guy.)*
    > — **Віктор:** Ти взяла ключі від цього автомобіля? *(Did you take the keys from this car?)*
  replace: |
    > — **Віктор:** Чи є лист для того чоловіка? *(Is there a letter for that man?)*
    > — **Марія:** Немає листа для того чоловіка, але є для цього хлопця. *(There is no letter for that man, but there is for this guy.)*
    > — **Віктор:** Ти взяла ключі від цього автомобіля? *(Did you take the keys from this car?)*
</fixes>
