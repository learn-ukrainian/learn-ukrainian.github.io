## Linguistic Scan
- Grammar terminology error: the module explicitly says `**що** and **де** as conjunctions` and later `new subordinating conjunctions`, but in examples like `Я знаю, де він живе` school grammar treats `де` here as a `сполучне слово`, not a subordinating conjunction.
- Unnatural directions example: `Де побачиш парк, зупинись.` is weak standard-A1 input; `Там, де побачиш парк, зупинись.` is the idiomatic pattern.

## Exercise Check
Found 4 markers: `fill-in-conjunctions`, `quiz-question-or-conjunction`, `fill-in-build-sentences`, `quiz-comma-placement`.

The count matches the 4 `activity_hints`, and each marker appears after the relevant teaching point. No inline DSL exercise blocks are present here, so answer logic/distractor quality cannot be audited at item level from this content alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All outline points are covered, and `State Standard 2024 §4.3.2` plus the Grade 5 textbook are cited in `Складне речення`, but the planned 300-word sections run to 437, 433, 400, and 323 words. |
| 2. Linguistic accuracy | 7/10 | The module says `**що** and **де** as conjunctions` and later `new subordinating conjunctions`; in examples like `Я знаю, де...`, `де` is being used as a `сполучне слово`. `Де побачиш парк, зупинись.` is also unnatural. |
| 3. Pedagogical quality | 6/10 | PPP is visible, but large English meta-explanation blocks dilute the teaching, e.g. `Without these connecting words, the conversation would feel completely disconnected and choppy` and `The grammatical formula is incredibly logical and consistent`. |
| 4. Vocabulary coverage | 9/10 | All required words appear naturally (`що`, `де`, `коли`, `знати`, `думати`, `казати`), and recommended items like `сказати`, `бачити`, `чути`, `розуміти`, `речення`, `головне` also appear. |
| 5. Exercise quality | 9/10 | All four planned activity types have corresponding markers, and each marker comes after the relevant teaching section; only marker logic is visible here, not generated item content. |
| 6. Engagement & tone | 7/10 | The teacher voice is calm, but filler like `crucial links`, `completely disconnected and choppy`, `incredibly logical and consistent`, and `excellent examples` pads the module without adding much instruction. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and in order, markers are clean, and the pipeline word count is 1718, which is above target. |
| 8. Cultural accuracy | 10/10 | No Russia-centered framing or cultural misstatements appear; the module stays in everyday Ukrainian contexts. |
| 9. Dialogue & conversation quality | 7/10 | The first dialogue is functional, but the directions example `Де побачиш парк, зупинись.` is stiff, and several lead-ins narrate the dialogue instead of letting the dialogue do the teaching. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Let's detail some of the most common and useful sentence patterns using **що** and **де** as conjunctions.` / `You can now combine these new subordinating conjunctions`  
Issue: The grammar label is inaccurate. In this module’s own examples, `де` is functioning as a `сполучне слово`, not a subordinating conjunction.  
Fix: Rephrase these lines to say `що` is a conjunction here, while `де` functions as a linking word in subordinate clauses; avoid calling all three items “new subordinating conjunctions”.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> **Господар:** Де побачиш парк, зупинись. Будинок, що стоїть біля дерева, мій.`  
Issue: This is an unnatural directions sentence for A1 input. The idiomatic pattern needs a correlative anchor: `Там, де...`  
Fix: Change it to `Там, де побачиш парк, зупинись. Будинок, що стоїть біля дерева, мій.`

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Діалоги`, `Складне речення`, `Що, де, коли — двоє облич`; e.g. `At first, learners often use short separate sentences...`, `Notice exactly how the speakers connect their ideas together...`, `The grammatical formula is incredibly logical and consistent...`  
Issue: The first three sections exceed the plan’s 300-word budget by more than 10%, largely because of English-only meta-commentary that repeats obvious points instead of teaching new material.  
Fix: Compress the English framing paragraphs and keep the examples, rule statements, and contrasts.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Without these connecting words, the conversation would feel completely disconnected and choppy.` / `The grammatical formula is incredibly logical and consistent` / `These three extremely useful words have two distinct jobs`  
Issue: The module spends too much space on generic explanation and praise language instead of concise rule-plus-example instruction.  
Fix: Replace these paragraphs with short teaching-focused transitions that point directly to the pattern and examples.

## Verdict: REVISE
REVISE because there is a critical grammar-labeling error and multiple major quality issues in pacing and pedagogy. The module covers the plan well and the exercise scaffolding is in place, but it should not ship until the terminology and overlong prose are corrected.

<fixes>
- find: |
    At first, learners often use short separate sentences: "I am here. The cafe is there. I will come." In this module, you will learn how Ukrainian links those ideas with **що**, **де**, and **коли** so you can talk about what you know, where things are, and when something happens.

    Let's look at our first conversation. Two friends are planning to meet and deciding on a location and time. Notice how they link their sentences.
  replace: |
    In this module, **що**, **де**, and **коли** help you link ideas about facts, places, and time.

    Let's look at a conversation where two friends plan when and where to meet.
- find: |
    Notice exactly how the speakers connect their ideas together. The small words **де** (where), **коли** (when), and **що** (that) act as crucial links between a main thought and a dependent thought. Without these connecting words, the conversation would feel completely disconnected and choppy. They act as bridges, turning simple, brief statements into a naturally flowing dialogue.
  replace: |
    Notice how **де**, **коли**, and **що** link a main clause with a dependent clause and make the dialogue sound more natural.
- find: |
    Now, let's look at a second conversation. Here, someone is asking for directions or updates about a friend. Pay attention to how the information is layered.
  replace: |
    Now let's look at a second conversation about a friend in Kyiv.
- find: |
    This exchange shows how one sentence can contain more than one clause linked by **що**, **де**, and **коли**.
  replace: |
    This exchange combines several linked clauses.
- find: |
    Here is a short example of explaining to a lost friend how to find your apartment, using these exact connections:
  replace: |
    Here is a short directions example:
- find: |
    > **Господар:** Де побачиш парк, зупинись. Будинок, що стоїть біля дерева, мій.
  replace: |
    > **Господар:** Там, де побачиш парк, зупинись. Будинок, що стоїть біля дерева, мій.
- find: |
    Let's explain the concept of the complex **речення** (sentence). In Module 44, you successfully learned how to connect EQUAL ideas using coordinating words. You built balanced sentences like "Я читаю, і він пише" (I read, and he writes). Now, we are stepping up to a completely new level: connecting a MAIN idea with a DEPENDENT idea. In Ukrainian grammar, this specific structure is called a складнопідрядне речення (complex sentence with a subordinate clause). This is the same school term used in Grade 5 textbooks such as Заболотний, and it aligns with State Standard 2024 §4.3.2 on basic complex sentences.
     You have a **головне** (main) clause that can stand totally alone, and a dependent part that relies heavily on the main one to make full sense.
  replace: |
    In Module 44, you learned to connect equal ideas: "Я читаю, і він пише." Now we connect a main clause with a dependent clause. In Ukrainian school grammar, this is a **складнопідрядне речення**. The first part is the **головне** clause, and the second depends on it.
- find: |
    Let's break down the structure. The grammatical formula is incredibly logical and consistent: Main clause + comma + **що** / **де** / **коли** + subordinate clause. The first part of the sentence sets up the action or the central thought, and the second part delivers the specific, supporting details. Look at these concrete, clear examples to see the pattern in action:
  replace: |
    Structure: main clause + comma + clause-linking word + subordinate clause. Look at these examples:
- find: |
    Now we must discuss the core punctuation rule. In Ukrainian, you normally place a comma between the main clause and the subordinate clause introduced by **що**, **де**, or **коли**. If the subordinate clause comes first, the comma comes after that clause: **Коли я прийду, ми поговоримо.**

    Let's reinforce this essential comma rule with more examples. Read these sentences carefully and pay close attention to the punctuation marks separating the clauses:
  replace: |
    Put a comma between the clauses. If the subordinate clause comes first, put the comma after it: **Коли я прийду, ми поговоримо.**

    Read these examples:
- find: |
    See how the commas smoothly structure this paragraph about a park:
  replace: |
    Read this short paragraph:
- find: |
    These three extremely useful words have two distinct jobs, or "Two Faces" (двоє облич), in the Ukrainian language. Job 1 is acting as simple Question words. You already learned this specific function back in Module 20. We use them right at the beginning of a sentence to ask for specific information.
  replace: |
    These three words have two jobs in Ukrainian. First, they can act as question words at the start of a sentence.
- find: |
    Job 2 is acting as words that introduce a subordinate clause. This is the brand-new skill we are practicing today. Here, they connect two parts of one complex sentence. How do you spot the difference? A question word forms a direct question and the sentence ends with a question mark. A clause-introducing word links clauses, and it can stand in the middle of the sentence or at the start if the subordinate clause comes first.
  replace: |
    Second, they can introduce a subordinate clause. A question word forms a direct question with a question mark. A clause-linking word connects two parts of one sentence.
- find: |
    Let's detail some of the most common and useful sentence patterns using **що** and **де** as conjunctions. They are very frequently paired with verbs of knowing, thinking, and saying, such as **знати** (to know), **думати** (to think), and **казати** (to say).
  replace: |
    Let's look at common patterns with **що** as a conjunction and **де** as a linking word in subordinate clauses. They often appear with verbs like **знати** (to know), **думати** (to think), and **казати** (to say).
- find: |
    Now let's detail the important patterns using **коли**. This specific word connects actions in time.
  replace: |
    Here are common patterns with **коли**:
- find: |
    Notice that the comma still separates the two clauses, ensuring the sentence remains perfectly clear.

    Here is a short classroom situation using these specific words:
  replace: |
    The comma still separates the two clauses.

    Here is a short classroom situation:
- find: |
    As you progress, your sentences will become much richer. You can now combine these new subordinating conjunctions with the coordinating conjunctions you learned in Module 44 (**і**, **а**, **але**, **бо**). This allows you to build highly advanced, expressive sentences. Look at these excellent examples of double-conjunction sentences:
  replace: |
    As you progress, your sentences will become much richer. You can now combine these clause-linking words and conjunctions with the coordinating conjunctions you learned in Module 44 (**і**, **а**, **але**, **бо**). Look at these examples:
</fixes>