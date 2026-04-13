## Linguistic Scan
- Critical grammar-teaching error: `"You MUST always place a comma immediately before **що**, **де**, and **коли**..."` is false. Ukrainian places the comma between the main and subordinate clauses; when the subordinate clause comes first, the comma follows that clause. The module itself later gives `Коли я прийду, ми поговоримо.`
- Critical grammar-teaching error: `"a question word sits right at the start ... A conjunction sits in the middle"` is false. A clause-introducing `коли` can also stand at the start of the whole sentence when the subordinate clause is fronted: `Коли я прийду, ми поговоримо.`
- Critical terminology error: the module repeatedly labels `де` and `коли` as “conjunctions.” Repo textbook search distinguishes `сполучники підрядності` from `сполучні слова`; `де` and `коли` are listed under `сполучні слова` in school grammar.

## Exercise Check
All 4 planned markers are present: `fill-in-conjunctions`, `quiz-question-or-conjunction`, `fill-in-build-sentences`, `quiz-comma-placement`.

They appear after relevant teaching:
- `fill-in-conjunctions` follows the structure/comma section.
- The other 3 follow the “Two Faces” section, after the question-word vs clause-linking explanation.

Marker count matches the 4 `activity_hints`. No inline DSL exercises are present, so exercise logic beyond marker placement is not reviewable here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All planned H2 sections and all 4 activity markers are present, but section budgets are badly off plan: Dialogues `526` vs planned `300`, Complex `422`, Two Faces `403`, Summary `332`. Also, proof-of-absence check found `0` occurrences of `State Standard`, `§4.3.2`, and `Заболотний` in the module body. |
| 2. Linguistic accuracy | 4/10 | The module teaches two false grammar rules: comma placement is overstated as “always before” `що/де/коли`, and the question-word vs conjunction test fails on the module’s own `Коли я прийду, ми поговоримо.` example. It also blurs `сполучники` vs `сполучні слова`. |
| 3. Pedagogical quality | 5/10 | The PPP skeleton exists, but the opening spends well over 100 English words before the first Ukrainian example, and the core rule/diagnostic taught in the grammar sections is inaccurate. |
| 4. Vocabulary coverage | 9/10 | Required items `що, де, коли, знати, думати, казати` are covered; recommended items such as `сказати`, `бачити`, `чути`, `розуміти`, `речення`, `головне` also appear. |
| 5. Exercise quality | 8/10 | Marker count and sequencing match the plan, and each marker follows the relevant teaching. The generated YAML exercise logic is not visible here, so only placement can be assessed. |
| 6. Engagement & tone | 5/10 | Teacher warmth is present, but the module is padded with generic hype and filler: “absolute golden rule,” “essential building blocks of fluency,” “highly advanced, expressive sentences.” |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly; no stray artifacts; pipeline word count is `1810`, above the `1200` target. |
| 8. Cultural accuracy | 9/10 | No Russiacentric framing or cultural inaccuracies found. |
| 9. Dialogue & conversation quality | 7/10 | Named speakers and real situations are good, but the lesson spends too much time explaining the dialogues in English instead of letting the Ukrainian carry the teaching load. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `"You MUST always place a comma immediately before **що**, **де**, and **коли** when they act as conjunctions connecting two parts of a sentence."`  
Issue: This is factually wrong. In Ukrainian, the comma separates the clauses; if the subordinate clause comes first, the comma comes after it. The module itself later shows `Коли я прийду, ми поговоримо.`  
Fix: Replace the rule with “place a comma between the clauses,” and explicitly note what happens when the subordinate clause comes first.

- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `"a question word sits right at the start of a sentence that ends with a question mark. A conjunction sits in the middle, firmly linking two parts together"`  
Issue: This diagnostic is false. A clause-introducing `коли` can also stand at the start of the whole sentence when the subordinate clause is fronted.  
Fix: Explain that direct questions end with `?`, while clause-introducing words can appear in the middle or at the start if the subordinate clause comes first.

- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `"Job 2 is acting as Conjunctions."` and `"subordinating conjunctions you have mastered"`  
Issue: The grammar terminology is inaccurate. Repo textbook search distinguishes `сполучники підрядності` from `сполучні слова`; `де` and `коли` are taught as `сполучні слова` in school grammar.  
Fix: Relabel them as “words that introduce subordinate clauses” or explicitly distinguish `що` from `де/коли`.

- [PLAN ADHERENCE] [SEVERITY: major]  
Location: opening of `## Діалоги (Dialogues)` and the explanatory paragraphs after each dialogue  
Issue: The module overshoots the section budgets substantially, especially Dialogues (`526` vs planned `300`), because too much English commentary is doing work the examples should do.  
Fix: Compress the opening and commentary paragraphs so the Ukrainian input arrives faster and section pacing is closer to the plan.

- [PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `"When you are speaking a new language, you often start by communicating like a robot..."`  
Issue: The module opens with a long English lecture before showing Ukrainian. That delays input and violates the prompt’s pedagogy standard for example-first teaching.  
Fix: Replace the opening with a short setup that names the target forms and moves immediately into Ukrainian examples.

- [PLAN ADHERENCE] [SEVERITY: major]  
Location: `"In Ukrainian grammar, this specific structure is called a складнопідрядне речення..."`  
Issue: The plan references are not integrated. Proof-of-absence check found `0` occurrences of `State Standard`, `§4.3.2`, and `Заболотний` in the module body.  
Fix: Add one short sentence tying the lesson to `State Standard 2024 §4.3.2` and the Grade 5 `Заболотний` terminology.

## Verdict: REVISE
REVISE. The module has multiple critical grammar-teaching inaccuracies, so it cannot pass even though coverage and structure are broadly complete.

<fixes>
- find: |
    Now we must discuss the absolute golden rule of Ukrainian punctuation. This is a strict requirement that you must memorize. Unlike English, where words like "that" or "when" often do not require any punctuation before them, Ukrainian is entirely different. You MUST always place a comma immediately before **що**, **де**, and **коли** when they act as conjunctions connecting two parts of a sentence.
  replace: |
    Now we must discuss the core punctuation rule. In Ukrainian, you normally place a comma between the main clause and the subordinate clause introduced by **що**, **де**, or **коли**. If the subordinate clause comes first, the comma comes after that clause: **Коли я прийду, ми поговоримо.**

- find: |
    Job 2 is acting as Conjunctions. This is the brand-new skill we are practicing today. Here, they are used to connect clauses within a single complex sentence. How do you clearly spot the difference between the two jobs? It is quite simple: a question word sits right at the start of a sentence that ends with a question mark. A conjunction sits in the middle, firmly linking two parts together, and it is always preceded by a comma.
  replace: |
    Job 2 is acting as words that introduce a subordinate clause. This is the brand-new skill we are practicing today. Here, they connect two parts of one complex sentence. How do you spot the difference? A question word forms a direct question and the sentence ends with a question mark. A clause-introducing word links clauses, and it can stand in the middle of the sentence or at the start if the subordinate clause comes first.

- find: |
    Let's provide a comprehensive recap of the subordinating conjunctions you have mastered at the A1 level. They are the essential building blocks of fluency.

    | Conjunction | Meaning | Example |
  replace: |
    Let's provide a concise recap of the words that introduce subordinate clauses at the A1 level.

    | Word | Meaning | Example |

- find: |
    We must strongly reiterate the paramount punctuation rule: Always place a comma before the conjunction when it connects two clauses. This tiny punctuation mark is the absolute secret to perfect, natural Ukrainian writing. Do not forget it.
  replace: |
    We must reiterate the punctuation rule: place a comma between the two clauses. If the subordinate clause comes first, the comma follows it; if the main clause comes first, the comma stands before the clause-introducing word.

- find: |
    When you are speaking a new language, you often start by communicating like a robot: "I am here. The cafe is there. I will come." While this gets the point across, native speakers do not talk this way. They naturally flow their ideas together. They connect their thoughts into longer, smoother sentences. Instead of stating two separate, isolated facts, they link them into one clear and cohesive message. Today, we will learn how to build these essential bridges in your Ukrainian conversations. We will explore how to make plans, how to explain where things are located, and how to express what you know or think.
  replace: |
    At first, learners often use short separate sentences: "I am here. The cafe is there. I will come." In this module, you will learn how Ukrainian links those ideas with **що**, **де**, and **коли** so you can talk about what you know, where things are, and when something happens.

- find: |
    Notice the highly natural conversational flow in this exchange. We can clearly see how a single sentence can contain multiple clauses linked by these specific conjunctions. This grammar skill makes your spoken Ukrainian sound much more advanced, fluent, and expressive, allowing you to share complex, layered information effortlessly in everyday situations.
  replace: |
    This exchange shows how one sentence can contain more than one clause linked by **що**, **де**, and **коли**.

- find: |
    In Ukrainian grammar, this specific structure is called a складнопідрядне речення (complex sentence with a subordinate clause).
  replace: |
    In Ukrainian grammar, this specific structure is called a складнопідрядне речення (complex sentence with a subordinate clause). This is the same school term used in Grade 5 textbooks such as Заболотний, and it aligns with State Standard 2024 §4.3.2 on basic complex sentences.
</fixes>