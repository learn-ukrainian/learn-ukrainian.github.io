## Linguistic Scan
No Russianisms, Surzhyk, calques, paronyms, or forbidden Russian characters found.

Critical grammar-teaching errors found:
- `"Petro is a man, so his past tense verbs all end in the masculine suffix **-в** or **-вся** ... and **ліг**"` teaches a false rule. `ліг` is itself a masculine past form without `-в/-вся`.
- `"because Anna is a woman, every single past tense verb ends in **-ла**"` and `"A man must strictly use the **-в** or **-вся** forms throughout his story"` confuse narrator gender with subject agreement. In the same model text, `Учора був звичайний день` is masculine because `день` is masculine.

## Exercise Check
Found 3 markers:
- `order-daily-routine`
- `fill-in-time-markers`
- `fill-in-gender-consistency`

These correspond to the 3 `activity_hints` in the plan, and each appears after the relevant teaching section. No inline DSL exercise logic errors to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The two planned day-narration dialogues, time markers, sequencing words, model narrative, template, and summary are present, but the source-of-truth police-report dialogue situation never appears in the actual module. I searched the content for `велосипед`, `Поліцейський`, `кав'ярня`, `куртка`, and `кепка` and found 0 occurrences. |
| 2. Linguistic accuracy | 4/10 | The prose teaches false grammar rules: `"his past tense verbs all end in the masculine suffix **-в** or **-вся**"` despite the same sentence listing `**ліг**`, and later `"every single past tense verb ends in **-ла**"` / `"A man must strictly use the **-в** or **-вся** forms throughout his story"`, which misstates past-tense agreement. |
| 3. Pedagogical quality | 6/10 | The module has usable dialogues and examples, but long English framing delays the teaching: `"Chaining events together in a logical order is a vital skill..."`, `"A truly natural story is more than just a list of verbs; it is a tapestry..."`, and the summary metaphor `"building a bridge across time"` add exposition where tighter guided instruction would work better. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary appears in prose (`учора`, `зранку`, `вдень`, `ввечері`, `потім`, `прокинутися`, `поснідати`, `обідати`), and recommended items are also used naturally (`спочатку`, `нарешті`, `повернутися`, `лягти`, `звичайний`, `продукти`, `серіал`, `колега`). |
| 5. Exercise quality | 10/10 | Marker count matches the plan exactly, and each marker follows the teaching it tests. The ordering marker comes after the verb/time-marker explanation; the two fill-in markers come after the model narrative and gender discussion. |
| 6. Engagement & tone | 5/10 | The teacher voice is consistent, but the module leans on generic metaphor and filler: `"it is the key to sharing your life with others"`, `"it is a tapestry"`, `"building a bridge across time"`, `"sounds professional and natural"`. These inflate the text without adding much instructional value. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and in order, the activity markers are intact, and the pipeline word count is 1857, safely above the 1200 target. |
| 8. Cultural accuracy | 10/10 | No Russian-centric framing, no decolonial issues, and no false cultural claims. The examples stay within ordinary Ukrainian everyday contexts. |
| 9. Dialogue & conversation quality | 8/10 | The two included dialogues are clear and usable, with named speakers and full-day sequencing, but the planned police-report exchange is missing, so the dialogue set is less varied than the plan requires. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Dialogues` opening: `"Whether you are telling a friend about your weekend or reporting a missing item to the authorities..."` followed by `"Now, let us listen to a feminine perspective."` Search confirmed 0 occurrences of `велосипед`, `Поліцейський`, `кав'ярня`, `куртка`, `кепка`.  
Issue: The source-of-truth plan includes a police-report dialogue situation, but the generated module never actually models it.  
Fix: Insert a short police-report dialogue using the planned speakers and vocabulary before the Anna dialogue.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `"Petro is a man, so his past tense verbs all end in the masculine suffix **-в** or **-вся**. He says **прокинувся** ... and **ліг**"` and Summary: `"A man must strictly use the **-в** or **-вся** forms throughout his story"`  
Issue: This teaches a false rule. Masculine past forms do not all end in `-в/-вся`; `ліг` is already a counterexample in the same module.  
Fix: Rewrite the rule to say that first-person past forms must agree with the speaker, but some masculine forms are irregular, for example `ліг`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `"because Anna is a woman, every single past tense verb ends in **-ла**"` and Summary: `"while a woman must strictly use the **-ла** or **-лася** forms throughout her story"`  
Issue: This confuses narrator gender with verb agreement. Past tense agrees with its subject, not with the narrator globally; the same model story contains `Учора був звичайний день`, where `був` agrees with `день`, not Anna.  
Fix: Explain that verbs describing Anna’s own `я` actions use feminine forms, but verbs with other subjects keep the gender/number of those subjects.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `"Chaining events together in a logical order is a vital skill in any language..."`, `"A truly natural story is more than just a list of verbs; it is a tapestry..."`, and `"Narrating your day in Ukrainian is like building a bridge across time."`  
Issue: Long English metaphor/filler slows the PPP flow and dilutes the teaching focus.  
Fix: Replace these paragraphs with short, task-focused setup and summary sentences that move quickly into Ukrainian examples.

## Verdict: REVISE
REVISE. There are critical grammar-teaching errors and one source-of-truth dialogue omission. The module is salvageable with targeted edits, so this is not a full reject.

<fixes>
- find: |
    Chaining events together in a logical order is a vital skill in any language, and in Ukrainian, it is the key to sharing your life with others. Whether you are telling a friend about your weekend or reporting a missing item to the authorities, you need to know how to sequence actions. Talking about your daily routine — what you did from the moment you opened your eyes until you went to sleep — is one of the most common conversational topics. By the end of this module, you will be able to turn a simple list of actions into a coherent story that flows naturally from morning to night.
  replace: |
    To tell what happened yesterday, you need to put actions in order. In this module, you will hear short dialogues and build a simple story from morning to night using time markers and past-tense verbs.

- find: |
    This short conversation demonstrates how the "skeleton" of a day is built using four main blocks: **зранку** (in the morning), **вдень** (in the afternoon), **ввечері** (in the evening), and finally, **лягти** (to lie down/go to) спати. Petro is a man, so his past tense verbs all end in the masculine suffix **-в** or **-вся**. He says **прокинувся** (I woke up), **поснідав** (I had breakfast), **пішов** (I went), and **ліг** (I lay down). These endings are consistent throughout his entire story, reflecting his gender in every action he recounts.
  replace: |
    This short conversation demonstrates how a day can be structured with time markers such as **зранку** (in the morning), **вдень** (in the afternoon), and **ввечері** (in the evening), ending with **лягти спати** (to go to bed). Petro is a man, so when he talks about his own actions in the past, he uses masculine forms such as **прокинувся** (I woke up), **поснідав** (I had breakfast), and **пішов** (I went). Some masculine past forms are irregular, such as **ліг** (I lay down), so do not expect every masculine form to end in **-в** or **-вся**.

- find: |
    Now, let us listen to a feminine perspective. Anna is telling her friend about her Saturday. Pay attention to how the verb endings change and how she uses "then" to keep the story moving.
  replace: |
    Here is one more real-life past-tense situation from this module's theme: a police report about a stolen bicycle.

    > **Поліцейський:** Що сталося? *(What happened?)*
    > **Свідок:** Я припаркував велосипед біля магазину. Потім зайшов у кав'ярню. Коли вийшов, велосипед зник. *(I parked the bicycle near the store. Then I went into the cafe. When I came out, the bicycle was gone.)*
    > **Поліцейський:** Ви бачили когось? *(Did you see anyone?)*
    > **Свідок:** Так, бачив чоловіка в куртці та кепці. *(Yes, I saw a man in a jacket and a cap.)*

    Now, let us listen to a feminine perspective. Anna is telling her friend about her Saturday. Pay attention to how the verb endings change and how she uses "then" to keep the story moving.

- find: |
    A truly natural story is more than just a list of verbs; it is a tapestry that combines your actions with the places you visited, the food you ate, and the people you met. To make your narrative "come alive," you should integrate the vocabulary you have learned in previous modules. Instead of just saying "I ate," you can say "I ate porridge and drank coffee." This adds texture and personality to your speech.
  replace: |
    A natural story combines actions with places, food, and people. That is why the model narrative below mixes routine verbs with familiar vocabulary from earlier modules.

- find: |
    If we analyze Anna's story, we can see why it sounds so authentic. First, because Anna is a woman, every single past tense verb ends in **-ла**: **прокинулася**, **поснідала**, **пішла**, **обідала**, **ходила**, **лягла**. This consistency is the hallmark of a fluent speaker. Second, she uses her surroundings to ground the story. She doesn't just "go"; she goes to the **магазин** (store) or the **кафе**. She doesn't just "eat"; she eats **продукти** (groceries) or a **салат**.
  replace: |
    If we analyze Anna's story, we can see why it sounds so natural. When Anna talks about her own past actions with **я**, she uses feminine forms such as **прокинулася**, **поснідала**, **пішла**, **обідала**, **ходила**, and **лягла**. Notice, however, that past-tense verbs agree with their subject: in **Учора був звичайний день**, the verb **був** is masculine because **день** is masculine. She also grounds the story with concrete details such as **кафе**, **магазин**, **салат**, and **продукти**.

- find: |
    Narrating your day in Ukrainian is like building a bridge across time. You start with a solid foundation of time markers that divide your story into logical segments. By using **зранку** (in the morning), **вдень** (in the afternoon), and **ввечері** (in the evening), you provide a clear, natural flow that native speakers expect. These words act as signposts, letting your listener know exactly where they are in your timeline.

    To make that bridge smooth, you use sequencing words as the "glue" between your sentences. Without words like **спочатку** (first), **потім** (then), **після цього** (after that), and **нарешті** (finally), your speech would sound like a series of disconnected bumps. These connectors are the secret to moving beyond disjointed phrases into a fluid, connected story that sounds professional and natural.
  replace: |
    To narrate your day in Ukrainian, organize the story with time markers such as **зранку**, **вдень**, **ввечері**, and, when needed, **вночі**. Then connect the actions with sequencing words such as **спочатку**, **потім**, **після цього**, and **нарешті** so the story moves clearly from one event to the next.

- find: |
    The most important rule to remember is gender consistency. In English, "I went" is the same for everyone, but in Ukrainian, your gender is built into the verb itself. A man must strictly use the **-в** or **-вся** forms throughout his story, while a woman must strictly use the **-ла** or **-лася** forms. Switching between them mid-story is a common learner mistake that can confuse your listener.
  replace: |
    The most important rule to remember is agreement in the first person past tense. When you talk about your own actions with **я**, choose the form that matches your gender: for example, **я пішов / я пішла**, **я прокинувся / я прокинулася**. But past-tense verbs still agree with their actual subject, so **день був звичайний** stays masculine because **день** is masculine. Mixing **я пішов** and **я пішла** in the same self-narration is a common learner mistake.
</fixes>