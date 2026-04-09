## Linguistic Scan

Errors found:
1. **Calque / Russianism:** "знаходитися" used in the locative sense ("ви зараз знаходитеся в дорозі"). In Ukrainian, the correct verb for physical location or state is "перебувати" (або "бути"). 
2. **Calque:** "Микола має одне дуже затишне улюблене кафе" — literal translation of English "has a favorite cafe", which in Ukrainian implies ownership of the business. Should be rephrased naturally to "у Миколи є..." or "є одне кафе, яке Микола обожнює".
3. **Phonetic Error:** "м'який шиплячий «ж»" (referring to the verb "біжу"). In Ukrainian phonetics, hushing consonants (шиплячі: ж, ч, ш, дж) are strictly **hard (тверді)**. Calling "ж" soft is factually incorrect and contradicts Grade 5 phonetics rules.

## Exercise Check

- `<!-- INJECT_ACTIVITY: match-pairs -->` — Present (Match-up: односпрямовані/різноспрямовані).
- `<!-- INJECT_ACTIVITY: group-sort-direction -->` — Present (Group-sort: motion verbs).
- `<!-- INJECT_ACTIVITY: fill-in-conjugation -->` — Present (Fill-in: present tense).
- `<!-- INJECT_ACTIVITY: error-correction-motion -->` — Present (Error correction).
- `<!-- INJECT_ACTIVITY: quiz-choice-context -->` — Present (Context quiz).
- `<!-- INJECT_ACTIVITY: free-write-daily-routine -->` — Present (Free write).

**Notes:** All 6 expected markers from the `activity_hints` are present and strategically distributed after the relevant theory sections. The lack of bracketed metadata on some markers is acceptable since the pipeline resolves them by ID.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | **DEDUCT:** The plan explicitly required a `dialogue_situations` block ("Weekend morning in Київ — a couple decides how to get around..."), which was completely omitted. Missed textbook references: Вашуленко Grade 2 (іде час, іде дощ) and Авраменко Grade 7 (дієвідміни: літаєш vs полетять). |
| 2. Linguistic accuracy | 8/10 | **DEDUCT:** "знаходитися" замість "перебувати", "Микола має... кафе" (calque), and the critical phonetic claim that "ж" is a soft consonant ("м'який шиплячий «ж»"). |
| 3. Pedagogical quality | 9/10 | **REWARD:** Excellent PPP flow. The contrast between unidirectional and multidirectional is explained very logically with clear, relatable scenarios. |
| 4. Vocabulary coverage | 10/10 | **REWARD:** All required and recommended vocabulary items (including preview words like літати/плавати) are integrated naturally into the text. |
| 5. Exercise quality | 10/10 | **REWARD:** Exercise markers perfectly match the `activity_hints` in both quantity and placement, directly testing the taught content. |
| 6. Engagement & tone | 9/10 | **REWARD:** Natural teacher voice ("Уявіть типову життєву ситуацію"). Avoids corporate gamification. **DEDUCT:** Minor filler phrasing at times. |
| 7. Structural integrity | 10/10 | **REWARD:** Word count is 4911 (exceeds 4000-word target). All H2 headings from the plan are present and ordered correctly. |
| 8. Cultural accuracy | 10/10 | **REWARD:** Explicitly flags the Russicism "відправлятися" vs "відбуває" as a decolonization point, effectively executing the Заболотний Grade 7 note. |
| 9. Dialogue & conversation quality | 5/10 | **DEDUCT:** The required dialogue between the characters (Чоловік and Дружина) was completely skipped. |

## Findings

[Plan adherence] [major]
Location: First section (missing element before the narrative text)
Issue: The plan explicitly required a `dialogue_situations` block featuring a husband and wife planning their weekend morning ("Я йду до ринку..."). This was entirely omitted.
Fix: Inject the dialogue block right before the reading passage instruction.

[Linguistic accuracy] [critical]
Location: "це означає, що ви зараз знаходитеся в дорозі,"
Issue: The verb "знаходитися" used in the sense of "to be located/situated" is a Russianism/calque. In Ukrainian, it should be "перебувати".
Fix: Replace with "перебуваєте".

[Linguistic accuracy] [minor]
Location: "У центрі Києва Микола має одне дуже затишне улюблене кафе."
Issue: Literal calque from English ("has a favorite cafe"). In Ukrainian, "мати кафе" means to own the business. 
Fix: Rephrase to "У центрі Києва є одне дуже затишне кафе, яке Микола обожнює."

[Linguistic accuracy] [critical]
Location: "По-перше, при відмінюванні слова в теперішньому часі кореневий приголосний звук «г» послідовно перетворюється на м'який шиплячий «ж»."
Issue: Factually incorrect phonetic claim. In Ukrainian, hushing consonants (шиплячі: ж, ч, ш, дж) are strictly hard (тверді), not soft. 
Fix: Remove the word "м'який". Replace with "перетворюється на шиплячий «ж»".

[Plan adherence] [major]
Location: Section "Односпрямовані дієслова: іти, їхати, бігти"
Issue: The plan required referencing Вашуленко Grade 2, p.80 regarding the polysemy of "іти" (іде катер, іде поїзд, іде зима, іде час). This was completely omitted.
Fix: Insert the explanation of polysemy at the end of the "іти" paragraph.

[Plan adherence] [major]
Location: Section "Підсумок: система дієслів руху"
Issue: The plan required referencing Авраменко Grade 7, p.74 to note the conjugation class difference between літати (I дієвідміна) vs летіти (II дієвідміна). This was completely omitted.
Fix: Insert the conjugation rule reference when previewing "летіти" and "літати" in the conclusion.

## Verdict: REVISE
The module exceeds word count and has a great narrative flow, but it contains a critical phonetic error ("м'який ж"), a common Russian calque ("знаходитися" для локації), and it completely missed three specific structural requirements from the plan (the dialogue and two textbook references). Applying deterministic fixes below.

<fixes>
- find: "це означає, що ви зараз знаходитеся в дорозі,"
  replace: "це означає, що ви зараз перебуваєте в дорозі,"
- find: "У центрі Києва Микола має одне дуже затишне улюблене кафе. Він часто ходить туди пити міцну каву"
  replace: "У центрі Києва є одне дуже затишне кафе, яке Микола обожнює. Він часто ходить туди пити міцну каву"
- find: "кореневий приголосний звук «г» послідовно перетворюється на м'який шиплячий «ж»"
  replace: "кореневий приголосний звук «г» послідовно перетворюється на шиплячий «ж»"
- find: "Зверніть особливу увагу на виділені слова та спробуйте проаналізувати контекст їхнього використання."
  replace: "Зверніть особливу увагу на виділені слова та спробуйте проаналізувати контекст їхнього використання.

**Діалог: Ранок вихідного дня**
**Чоловік:** Я **йду** *(am walking)* до ринку. А ти **їдеш** *(are riding)* на Поділ?
**Дружина:** Так. Діти вже **біжать** *(are running)* у парк. А бабуся якраз **їде** *(is riding)* трамваєм."
- find: "Використовуйте ці форми для будь-якого руху пішки, який ви робите просто зараз."
  replace: "Використовуйте ці форми для будь-якого руху пішки, який ви робите просто зараз. Крім того, українська мова використовує це дієслово в переносному значенні (як зазначає підручник Вашуленка, 2 клас, с. 80): ми кажемо «іде дощ» *(it is raining)*, «іде час» *(time is passing)* або «іде зима» *(winter is coming)*. Навіть механічні об'єкти можуть «іти»: «іде поїзд» або «іде катер»."
- find: "Дієслова для повітряних польотів та плавання у воді ми значно детальніше розглянемо у наступних модулях, але їхня внутрішня логіка є ідентичною до слова «іти»."
  replace: "Дієслова для повітряних польотів та плавання у воді ми значно детальніше розглянемо у наступних модулях, але їхня внутрішня логіка є ідентичною до слова «іти». Зверніть увагу на важливу граматичну деталь (за Авраменком, 7 клас, с. 74): різноспрямоване дієслово «літати» належить до I дієвідміни (ти літаєш), тоді як односпрямоване «летіти» — до II дієвідміни (вони летять)."
</fixes>
