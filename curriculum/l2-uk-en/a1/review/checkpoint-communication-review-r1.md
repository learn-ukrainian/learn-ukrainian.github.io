## Linguistic Scan
No linguistic errors found.

## Exercise Check
4/4 activity markers are present: `fill-in-vocative-imperative`, `quiz-conjunctions`, `fill-in-complex-sentences`, `quiz-holiday-match`.

Each marker appears after the relevant teaching block, and the IDs match the plan’s `activity_hints`. No inline DSL exercise blocks are present, so there is no exercise-logic audit beyond marker placement.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | The reading gives `Тарасе, привіт! ... Принеси, будь ласка, кутю...`, but it never reaches the plan’s `колядки`; literal search on the full module found 0 instances of `ярмарок`, `плакати`, `квитки`, `напої`, `стільці` from `dialogue_situations`. |
| 2. Linguistic accuracy | 9/10 | No Russianisms, Surzhyk, calques, paronym errors, or wrong case forms were found in the Ukrainian text reviewed here. Spot-checks confirmed forms such as `прийди`, `ходімо`, `кутя`, `Тарасе`, `Андрію`, `Олено`. |
| 3. Pedagogical quality | 7/10 | The module gives clear examples, but both major practice texts stay in nearly the same setup: `She is organizing a gathering for the upcoming winter holidays` and `Olena and Taras are planning a holiday gathering with friends.` A checkpoint should widen practice, not mostly restate the same scene twice. |
| 4. Vocabulary coverage | 5/10 | Holiday vocabulary is present (`Різдво`, `кутя`), but the plan’s event/delegation lexicon is missing: `ярмарок`, `плакати`, `квитки`, `напої`, `стільці`; `колядки` is also absent despite being named in the reading brief. |
| 5. Exercise quality | 9/10 | The four marker IDs match the four planned activity types and are placed after the relevant explanation blocks. No visible logic errors can be assessed yet because the actual YAML-generated items are not shown here. |
| 6. Engagement & tone | 5/10 | The summary uses generic courseware filler: `You have reached a significant milestone in your Ukrainian learning journey.` That adds sentiment, not instruction. |
| 7. Structural integrity | 7/10 | All planned H2 sections are present and the total word count is above target, but the opening section ends with a dangling fragment: `If you understand these concepts,` |
| 8. Cultural accuracy | 9/10 | The kutia note is accurate and Ukrainian-centered: `**Кутя** ... is a traditional sweet grain pudding served on Christmas Eve in Ukraine.` No Russian-centric framing appears. |
| 9. Dialogue & conversation quality | 6/10 | The dialogue is named-speaker dialogue, but it largely repeats the reading’s holiday-gathering premise instead of delivering the plan’s delegation scene with task vocabulary. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `> **Тарасе, привіт! ... Принеси, будь ласка, кутю, бо я не маю часу готувати. Скажи, коли ти будеш.**`  
Issue: The reading brief says this text should integrate all A1.7 communication tools and specifically mentions `колядки`; the current passage does not include `але`, `де`, or `колядки`, and the closing `Скажи, коли ти будеш.` is weaker than the planned `коли`-based target.  
Fix: Replace the reading message with one that explicitly includes `але`, `де`, `коли`, and `колядки`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: whole module; literal search found 0 occurrences of `ярмарок`, `плакати`, `квитки`, `напої`, `стільці`  
Issue: The plan’s delegation/event vocabulary never appears in prose, and the dialogue repeats the same holiday-gathering setup as the reading instead of delivering the planned organization scene.  
Fix: Replace the dialogue section with a school-fair organization exchange that naturally uses `ярмарок`, `плакати`, `квитки`, `напої`, and `стільці`.

[STRUCTURAL INTEGRITY] [SEVERITY: minor]  
Location: `If you understand these concepts,`  
Issue: Dangling incomplete sentence.  
Fix: Complete the sentence or remove it.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `You have reached a significant milestone in your Ukrainian learning journey.`  
Issue: Generic motivational filler weakens the teacher voice and adds no language value.  
Fix: Replace it with a concrete sentence about what this checkpoint reviews.

## Verdict: REVISE
REVISE. There are no confirmed Ukrainian-language errors, but there are major plan-adherence and vocabulary-recycling problems, plus a structural fragment and generic filler. Several dimensions are below 9, so this cannot pass as written.

<fixes>
- find: |-
    - Can you name Ukrainian holidays and greet people appropriately (**З Різдвом!**)?

    If you understand these concepts, 

    ## Читання (Reading Practice)
  replace: |-
    - Can you name Ukrainian holidays and greet people appropriately (**З Різдвом!**)?

    If you understand these concepts, you are ready for the checkpoint text and dialogue below.

    ## Читання (Reading Practice)

- find: |-
    > **Тарасе, привіт! Ти пам'ятаєш, що скоро Різдво? Я думаю, що ми маємо святкувати разом. Прийди до мене в суботу! Принеси, будь ласка, кутю, бо я не маю часу готувати. Скажи, коли ти будеш.**
    > *Taras, hi! Do you remember that Christmas is soon? I think that we must celebrate together. Come to me on Saturday! Bring kutia, please, because I do not have time to cook. Tell me when you will be here.*

    This short text naturally chains together several important communication tools. It begins with direct address using the vocative case (**Тарасе**). It connects thoughts using a subordinate clause (**що скоро Різдво**). It includes polite commands using the imperative mood (**Прийди**, **Принеси**). Finally, it provides a logical reason using a conjunction (**бо я не маю часу**). This creates a complete, natural communicative loop.
  replace: |-
    > **Тарасе, привіт! Ти пам'ятаєш, що скоро Різдво? Я думаю, що ми маємо святкувати разом, але я ще не знаю, де ми будемо. Прийди до мене в суботу! Принеси, будь ласка, кутю, бо я не маю часу готувати. Скажи, коли ти прийдеш, і ми разом заспіваємо колядки.**
    > *Taras, hi! Do you remember that Christmas is soon? I think that we should celebrate together, but I do not yet know where we will be. Come to my place on Saturday! Bring kutia, please, because I do not have time to cook. Tell me when you will come, and we will sing carols together.*

    This short text naturally chains together several important communication tools. It begins with direct address using the vocative case (**Тарасе**). It combines contrast and reason (**але**, **бо**), uses subordinate clauses (**що скоро Різдво**, **де ми будемо**, **коли ти прийдеш**), and ends with holiday vocabulary in context (**кутя**, **колядки**). This creates a complete, natural communicative loop.

- find: |-
    Read the following conversation. Olena and Taras are planning a holiday gathering with friends. They must coordinate their schedules, delegate tasks, and express traditional holiday wishes.

    > **Тарас:** Олено, привіт! Ти знаєш, що скоро Різдво? *(Olena, hi! Do you know that Christmas is soon?)*
    > **Олена:** Так, Тарасе! Я думаю, що ми можемо святкувати разом. *(Yes, Taras! I think that we can celebrate together.)*
    > **Тарас:** Добре! Скажи, коли ти вільна, бо я хочу запросити друзів. *(Good! Tell me when you are free, because I want to invite friends.)*
    > **Олена:** Я вільна двадцять четвертого. Але я не знаю, де ми будемо. *(I am free on the twenty-fourth. But I do not know where we will be.)*
    > **Тарас:** Ходімо до мене! Принеси кутю, будь ласка. *(Let's go to my place! Bring kutia, please.)*
    > **Олена:** Добре, принесу! І я знаю, де купити гарні свічки. З Різдвом! *(Good, I will bring it! And I know where to buy beautiful candles. Merry Christmas!)*

    Notice how the speakers negotiate their plans using complex sentences (**Скажи, коли ти вільна**). They handle contrast and uncertainty naturally (**Але я не знаю...**). When they assign responsibilities, they use polite requests (**Принеси кутю, будь ласка**). The vocabulary is practical and goal-oriented.

    :::caution
    **Polite Commands**
    The imperative mood is used to give commands, but in Ukrainian culture, direct commands among friends are not considered rude if spoken with a warm tone. However, always remember to add **будь ласка** (please) when asking someone to bring something or perform a specific task, as Taras does when asking for the **кутя**.
    :::
  replace: |-
    Read the following conversation. Olena and Taras are organizing a school holiday fair. They coordinate tasks, use direct address, and explain what they need with conjunctions and subordinate clauses.

    > **Організатор:** Олено, привіт! Тарасе, слухай: ми знаємо, що скоро ярмарок. *(Organizer: Olena, hi! Taras, listen: we know that the fair is soon.)*
    > **Олена:** Так! Я можу принести плакати. *(Yes! I can bring the posters.)*
    > **Організатор:** Добре! Тарасе, постав стільці, будь ласка, а потім принеси квитки. *(Good! Taras, set up the chairs, please, and then bring the tickets.)*
    > **Тарас:** Добре! Скажи, де напої, бо люди скоро прийдуть. *(Good! Tell me where the drinks are, because people will come soon.)*
    > **Олена:** Напої тут, а столи там. Я знаю, де все поставити. *(The drinks are here, and the tables are there. I know where to put everything.)*
    > **Організатор:** Чудово! Працюймо разом і зі святом! *(Excellent! Let us work together, and happy holiday!)*

    Notice how the speakers delegate tasks with the imperative (**постав**, **принеси**), explain reasons with **бо**, and ask about location with **де**. The dialogue also reuses the planned event vocabulary naturally: **ярмарок**, **плакати**, **квитки**, **напої**, **стільці**.

    :::caution
    **Polite Commands**
    The imperative mood is used to give commands, but polite wording still matters. Add **будь ласка** when asking someone to do a task, as the organizer does in **Тарасе, постав стільці, будь ласка**.
    :::

- find: |-
    You have reached a significant milestone in your Ukrainian learning journey. By completing this checkpoint, you have demonstrated that:
  replace: |-
    This checkpoint brings the A1.7 communication tools together in one place. By completing it, you have demonstrated that:
</fixes>