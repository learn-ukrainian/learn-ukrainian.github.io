## Linguistic Scan
No general linguistic errors like Surzhyk or Russianisms found. (The VESUM failures in the prompt data were caused by combining acute stress marks splitting the words, not invalid forms). However, there is a **CRITICAL** grammatical factual error where verbs are assigned to the wrong conjugation groups, which is detailed in the findings below. 

## Exercise Check
- `group-sort-verb-groups` (Hint #4): Tests verb group sorting. Miss-placed before the concept is explicitly reviewed. 
- `quiz-mixed-conjugation` (Hint #1): Tests mixed conjugation. Placed correctly after Grammar section.
- `fill-in-dialogue-completion` (Hint #2): Tests dialogue completion. Placed correctly after Dialogue.
- `fill-in-describe-your-day` (Hint #3): Tests sequence and morning routine. Placed correctly at the end.
- Overall exercise match is good, but the placement of the first marker is pedagogically flawed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The module missed points 5 and 6 (7 questions and double negation) in the "Граматика" section. The dialogue failed to use negation. The "Підсумок" section completely omitted the required "Next: A1.4 — Time and Nature" sentence. |
| 2. Linguistic accuracy | 4/10 | CRITICAL factual error: The text explicitly tells learners that `починається` is Group II (it is Group I), and `люблю` is Group I (it is Group II). Additionally, Оля (a female) uses the masculine "Я вчитель" instead of "вчителька". |
| 3. Pedagogical quality | 7/10 | The PPP structure is violated by placing the `group-sort-verb-groups` exercise immediately after the "Читання" section, meaning learners are tested on explicitly sorting verbs into conjugation groups before those rules are formally reviewed in the next "Граматика" section. |
| 4. Vocabulary coverage | 10/10 | Excellent coverage of target vocabulary from M15-M20 without introducing overwhelming new words. |
| 5. Exercise quality | 9/10 | The injected markers align perfectly with the plan's `activity_hints`. Deductions covered in Pedagogical quality for placement. |
| 6. Engagement & tone | 10/10 | Very natural, encouraging tone ("This is not a test. It is a mirror..."). Doesn't rely on cheap cheerleading. |
| 7. Structural integrity | 10/10 | Clean markdown, precise headers, and well-organized flow. |
| 8. Cultural accuracy | 9/10 | Good use of authentic names. Slight deduction for missing the feminitive for a female professional, which is a key part of decolonized Ukrainian standard. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue is a great multi-turn conversation ("Я теж хочу гуляти. Можна разом?"). Only deduction is for missing the required negation. |

## Findings

[1. Plan adherence] [major]
Location: "Граматика (Grammar Summary)" section
Issue: The section fails to list the 7 question words and double negation rules, which were explicitly required by points 5 and 6 of the plan's `content_outline`.
Fix: Add these missing rules to the end of the Grammar section.

[1. Plan adherence] [major]
Location: "Діалог (Connected Dialogue)" section
Issue: The plan explicitly required the dialogue to use "negation" (`Uses: both verb groups, modals, questions, negation.`), but there are no negative statements (`не`) used anywhere in the conversation.
Fix: Add natural negation to the final exchange between Оля and Максим (e.g., "я не хочу працювати").

[1. Plan adherence] [major]
Location: "Підсумок — Summary" section
Issue: The plan required the summary to mention the next step: "Next: A1.4 — Time and Nature (time, days, weather)". This was completely omitted.
Fix: Append the "Next Step" text to the end of the Summary.

[2. Linguistic accuracy] [critical]
Location: "Читання (Reading Practice)" and "Діалог (Connected Dialogue)" analysis paragraphs
Issue: The text incorrectly classifies `починається` as a Group II verb (it is Group I: `починають`), and incorrectly classifies `люблю` as a Group I verb (it is Group II: `люблять`). This explicitly teaches learners the wrong conjugation groups for common verbs.
Fix: Move `починається` to Group I and `люблю, дивлюся` to Group II in the "Читання" analysis. Move `люблю` to Group II in the "Діалог" analysis.

[2. Linguistic accuracy] [major]
Location: "Діалог (Connected Dialogue)" section
Issue: Оля, a female character, says "Я вчи́тель", using the masculine profession form. Modern Ukrainian standards (2019 Pravopys) strongly encourage feminitives for women's professions ("вчителька").
Fix: Change "Я вчи́тель" to "Я вчи́телька".

[3. Pedagogical quality] [major]
Location: "Читання (Reading Practice)" section
Issue: The `group-sort-verb-groups` exercise marker is placed immediately after the reading text, testing the students on explicitly sorting verbs into groups *before* those groups are formally summarized in the subsequent "Граматика" section. This violates PPP sequencing.
Fix: Move the `group-sort-verb-groups` marker to immediately after the "Граматика" section.

## Verdict: REVISE
The module has a critical grammatical factual error (teaching wrong conjugation groups), several missing plan requirements, and poor exercise sequencing. The provided fixes correct all of these issues while maintaining the module's excellent tone and natural dialogue flow.

<fixes>
- find: |
    and sequence words (**спочатку, потім, увечері**). Everything connects.
    
    <!-- INJECT_ACTIVITY: group-sort-verb-groups -->
    
    ## Грама́тика (Grammar Summary)
  replace: |
    and sequence words (**спочатку, потім, увечері**). Everything connects.
    
    ## Грама́тика (Grammar Summary)
- find: |
    Group I verbs (**читаю, слухаю**), Group II (**починається**), modals (**можу, хочу, мушу**),
  replace: |
    Group I verbs (**читаю, слухаю, починається**), Group II (**люблю, дивлюся**), modals (**можу, хочу, мушу**),
- find: |
    The pattern is always: conjugated verb + **ся** appended directly to the ending.
    
    <!-- INJECT_ACTIVITY: quiz-mixed-conjugation -->
  replace: |
    The pattern is always: conjugated verb + **ся** appended directly to the ending.
    
    **Питання та заперечення (Questions and Negation)**
    - Seven question words: **хто, що, де, куди, коли, чому, як**.
    - Negation is **не** before the verb. Ukrainian also uses double negation: **ніхто не знає** (nobody knows).
    
    <!-- INJECT_ACTIVITY: group-sort-verb-groups -->
    
    <!-- INJECT_ACTIVITY: quiz-mixed-conjugation -->
- find: |
    > — **Оля:** Я вчи́тель. Я виклада́ю матема́тику. *(I'm a teacher. I teach math.)*
  replace: |
    > — **Оля:** Я вчи́телька. Я виклада́ю матема́тику. *(I'm a teacher. I teach math.)*
- find: |
    > — **Оля:** Увечері я хочу відпочивати. Я читаю або слухаю музику. А ти? *(In the evening I want to rest. I read or listen to music. And you?)*
    > — **Максим:** Я теж люблю читати! *(I also love to read!)*
  replace: |
    > — **Оля:** Увечері я не хочу працювати. Я хочу відпочивати. Я читаю або слухаю музику. А ти? *(In the evening I don't want to work. I want to rest. I read or listen to music. And you?)*
    > — **Максим:** Я теж не люблю працювати увечері. Я люблю читати! *(I also don't like to work in the evening. I love to read!)*
- find: |
    Question words drive the conversation: **що** (what), **де** (where), **коли** (when). And reflexive verbs anchor the morning routine: **прокидаюся, вмиваюся**.
    
    <!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->
  replace: |
    Question words drive the conversation: **що** (what), **де** (where), **коли** (when). Negation is used naturally: **не хочу, не люблю**. And reflexive verbs anchor the morning routine: **прокидаюся, вмиваюся**.
    
    <!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->
- find: |
    Both verb groups appear naturally here. Group I: **гуляю, люблю, читаю, слухаю, працюю, почина́ю, викладаю**. Group II: **говорю**.
  replace: |
    Both verb groups appear naturally here. Group I: **гуляю, читаю, слухаю, працюю, почина́ю, викладаю**. Group II: **говорю, люблю**.
- find: |
    - **Зворотні дієслова** (Reflexive verbs) — **Я прокидаюся, вмиваюся, одягаюся** (I wake up, wash up, get dressed).
    
    <!-- INJECT_ACTIVITY: fill-in-describe-your-day -->
  replace: |
    - **Зворотні дієслова** (Reflexive verbs) — **Я прокидаюся, вмиваюся, одягаюся** (I wake up, wash up, get dressed).
    
    **Наступний крок (Next Step):** A1.4 — Time and Nature. You will learn to talk about time, days of the week, and the weather.
    
    <!-- INJECT_ACTIVITY: fill-in-describe-your-day -->
</fixes>
