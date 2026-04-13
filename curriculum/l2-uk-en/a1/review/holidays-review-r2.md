## Linguistic Scan
No linguistic errors found. I found no Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian characters (`ы`, `э`, `ё`, `ъ`) in the Ukrainian text.

## Exercise Check
All 4 expected markers are present, and the IDs match the plan hints: `quiz-which-holiday`, `quiz-match-date`, `group-sort-traditions`, `fill-in-greetings`.

The issue is placement. `quiz-which-holiday`, `quiz-match-date`, and `group-sort-traditions` are clustered after `## Державні свята`, so the Christmas/Easter material gets no immediate practice after it is taught. `fill-in-greetings` is placed correctly after the greetings summary.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All planned sections exist, and planned vocabulary is covered, but the section pacing is far off the 300-word plan budget: `Діалоги` 486 words, `Українські свята` 537, `Державні свята` 408, `Підсумок` 344. The Independence dialogue also changes the planned evening detail from `салют` to `концерт`. |
| 2. Linguistic accuracy | 10/10 | No Ukrainian language errors found; the module contains no Russian-only letters and the prompt’s VESUM data confirms the vocabulary used here. |
| 3. Pedagogical quality | 6/10 | Too much space is spent on English meta-explanation instead of immediate Ukrainian input, e.g. `Ukrainian holidays are a central part of family life...`, `A **свято** is a time for rest...`, `Notice the word **подарунок**...`. Practice is also delayed by the late marker clustering. |
| 4. Vocabulary coverage | 10/10 | All required plan words appear in prose (`свято`, `святкувати`, `Різдво`, `Великдень`, `Новий рік`, `вітати`), and the recommended cultural vocabulary is also used naturally. |
| 5. Exercise quality | 6/10 | The marker inventory is complete, but `quiz-which-holiday`, `quiz-match-date`, and `group-sort-traditions` are stacked together late instead of following the holiday content they test. |
| 6. Engagement & tone | 7/10 | The cultural topic is strong, but several lines are generic filler rather than concrete teaching, e.g. `It is a very important word for any celebration.` and `The rich traditions remain exactly the same.` |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly, and the deterministic pipeline count is above the 1200-word target. |
| 8. Cultural accuracy | 8/10 | The module is broadly decolonized and culturally respectful, but `There must be exactly twelve meatless dishes` overstates a living tradition as an absolute rule. |
| 9. Dialogue & conversation quality | 6/10 | The Independence dialogue is still mostly Q&A (`Що ви робите?`, `А ввечері?`) and repeats `концерт`, so it feels more like a checklist than a natural exchange. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Ukrainian holidays are a central part of family life and national identity...`; `A **свято** is a time for rest, family, and tradition...`; `Notice the word **подарунок** (gift). It is a very important word for any celebration.`  
Issue: Generic English exposition bloats all four sections far past the plan’s 300-word budgets and weakens pacing.  
Fix: Compress or remove these meta-explanations and keep the section focused on Ukrainian examples, greetings, and culture.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> **Марко:** Що ви робите?... > **Сара:** Ввечері — концерт і святковий вечір з друзями.`  
Issue: The Independence dialogue is unnatural, repetitive, and deviates from the plan by replacing the planned evening `салют` with a second `концерт`.  
Fix: Replace the block with a more natural multi-turn exchange that keeps `парад`, `концерт`, and `салют`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: quiz-which-holiday -->` / `<!-- INJECT_ACTIVITY: quiz-match-date -->` / `<!-- INJECT_ACTIVITY: group-sort-traditions -->`  
Issue: Three exercise markers are clustered late, so learners do not get practice immediately after the Christmas/Easter teaching they are supposed to reinforce.  
Fix: Move `quiz-which-holiday` and `quiz-match-date` up to the end of `## Українські свята`; keep `group-sort-traditions` after the national-holidays section.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: `There must be exactly twelve meatless dishes, representing the twelve apostles.`  
Issue: This presents a traditional custom as an absolute rule. That is too rigid for a living cultural practice.  
Fix: Rephrase it as a tradition rather than a universal obligation.

## Verdict: REVISE
REVISE. There are no Ukrainian language errors, but there are multiple major quality problems: severe section-budget overrun from filler exposition, weak/misaligned Independence dialogue, late exercise clustering, and one overly absolute cultural claim. Those findings put several dimensions below 9, so this cannot pass as-is.

<fixes>
- find: |-
    Ukrainian holidays are a central part of family life and national identity. Knowing how to talk about celebrations is a natural way to connect with people. You will often hear questions about dates and specific traditions.
  replace: |-
    In Ukraine, holidays bring together family, food, songs, and greetings.

- find: |-
    The most important winter celebration is **Різдво** (Christmas). During the festive season, families gather to share special meals and sing traditional songs. Notice how the speakers discuss the recent date change for this holiday.
  replace: |-
    Here is a short Christmas dialogue about the holiday date and traditions.

- find: |-
    Let's break down the vocabulary. **Різдво** is the noun for Christmas, and the verb **святкувати** means to celebrate. A **колядка** is a traditional carol that children and adults sing. The word **кутя** refers to a special ritual dish eaten only during the winter holidays. When saying goodbye or raising a toast, Ukrainians use the phrase **З Різдвом!** (Merry Christmas!).
  replace: |-
    Key words here are **Різдво**, **святкувати**, **колядка**, **кутя**, and the greeting **З Різдвом!**.

- find: |-
    > **Марко:** Двадцять четверте серпня — День Незалежності! *(The twenty-fourth of August is Independence Day!)*
    > **Сара:** Так, це головне державне свято України. *(Yes, this is the main state holiday of Ukraine.)*
    > **Марко:** Що ви робите? *(What do you do?)*
    > **Сара:** Ми дивимося парад і ходимо на концерт. *(We watch the parade and go to a concert.)*
    > **Марко:** А ввечері? *(And in the evening?)*
    > **Сара:** Ввечері — концерт і святковий вечір з друзями. *(In the evening — a concert and a festive evening with friends.)*
    > **Марко:** З Днем Незалежності! *(Happy Independence Day!)*
    > **Сара:** Слава Україні! *(Glory to Ukraine!)*
  replace: |-
    > **Марко:** Двадцять четверте серпня — День Незалежності! *(The twenty-fourth of August is Independence Day!)*
    > **Сара:** Так, це головне державне свято України. Ти йдеш на парад? *(Yes, it is the main state holiday of Ukraine. Are you going to the parade?)*
    > **Марко:** Так, а потім — на концерт. *(Yes, and then to a concert.)*
    > **Сара:** Я теж. А ввечері буде салют і святковий вечір з друзями. *(Me too. And in the evening there will be fireworks and a festive evening with friends.)*
    > **Марко:** З Днем Незалежності! *(Happy Independence Day!)*
    > **Сара:** Слава Україні! *(Glory to Ukraine!)*

- find: |-
    A **свято** is a time for rest, family, and tradition. When you want to **вітати** (to greet) someone for a festive occasion but you do not know the exact phrase, you can always say **Зі святом!** (Happy Holiday!). It is a universal, polite phrase that works for almost any situation.
  replace: |-
    If you do not know the exact greeting, you can say **Зі святом!** (Happy holiday!).

- find: |-
    There must be exactly twelve meatless dishes, representing the twelve apostles.
  replace: |-
    Traditionally, families prepare twelve meatless dishes, symbolically linked to the twelve apostles.

- find: |-
    Notice the word **подарунок** (gift). It is a very important word for any celebration. The standard greeting as the clock strikes midnight is **З Новим роком!**.
  replace: |-
    **Подарунок** means “gift”. At midnight, the standard greeting is **З Новим роком!**.

- find: |-
    <!-- INJECT_ACTIVITY: quiz-which-holiday -->
    <!-- INJECT_ACTIVITY: quiz-match-date -->
    <!-- INJECT_ACTIVITY: group-sort-traditions -->
  replace: |-
    <!-- INJECT_ACTIVITY: group-sort-traditions -->

- insert_after: |-
    * Це красива українська традиція. *(This is a beautiful Ukrainian tradition.)*
  content: |-
    <!-- INJECT_ACTIVITY: quiz-which-holiday -->
    <!-- INJECT_ACTIVITY: quiz-match-date -->
</fixes>