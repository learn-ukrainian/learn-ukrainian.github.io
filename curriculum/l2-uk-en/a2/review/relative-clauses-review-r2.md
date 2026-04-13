## Linguistic Scan
No linguistic errors found.

## Exercise Check
Five activity markers are present, which matches the five `activity_hints` in the plan.

Markers are placed after the relevant teaching:
- `fill-in...` after agreement/case/comma/question-vs-relative coverage
- `quiz...` after `де / куди / звідки`
- `match-up...` right after sentence-combining is introduced
- `true-false...` after common errors and comma/agreement reminders
- `unjumble...` at the end as cumulative practice

No exercise-placement issues found from the supplied marker inventory.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned sections are present and the content does cover nominative/accusative `який`, `де/куди/звідки`, common mistakes, and `котрий`. But the pipeline total is **2967** words against a **2000** target, and the section labels `(~800 words)` / `(~750 words)` already show pacing drifting above the plan’s 750/600/650 split. |
| 2. Linguistic accuracy | 10/10 | No Russian characters found; no clear Russianisms, Surzhyk, calques, or wrong Ukrainian forms surfaced. VESUM spot-checks confirmed forms such as `означальний`, `відносний`, `котрий`, `котра`, `знаходиться`, `висловлення`, and `локація`. |
| 3. Pedagogical quality | 7/10 | The module gives many usable examples (`Людина, яку я зустрів...`, `Парк, куди ми ходимо...`, `Країна, звідки вона приїхала...`). But it opens with **156 words of English theory before the first Ukrainian model sentence**: `Have you ever wanted to describe something...` through `...new places in your life.` |
| 4. Vocabulary coverage | 9/10 | Required plan vocabulary appears naturally in the prose: `який/яка/яке/які`, `де`, `куди`, `звідки`, `означальний`, `описувати`, `речення`. Recommended items also appear: `котрий`, `затишне`, `знаходиться`, `стоїть`. |
| 5. Exercise quality | 9/10 | All five planned exercise types have markers, and each marker comes after the concept it should test. No clustering-at-the-end problem. |
| 6. Engagement & tone | 7/10 | The teacher voice is mostly fine, but lines like `This single word serves as a powerful bridge` and `shows your high level of language proficiency` add filler and self-congratulatory framing instead of instruction. |
| 7. Structural integrity | 9/10 | All H2 headings from the plan are present and ordered correctly; markers are intact; the pipeline count is above target, so there is no underlength problem. |
| 8. Cultural accuracy | 10/10 | No Russia-centered framing, no cultural inaccuracies, and the examples stay within neutral Ukrainian contexts. |
| 9. Dialogue & conversation quality | 9/10 | The realtor dialogue has named speakers, a plausible situation, and multiple turns tied to the grammar focus. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: module-level / pipeline note `Word count: 2967 words`; section headings `## Який? Яка? Яке? Які? (Which? What Kind?) (~800 words)` and `## Описуємо людей, речі та місця (Describing People, Things, and Places) (~750 words)`  
Issue: The module substantially overshoots the 2000-word target and the plan’s section pacing. The extra length mostly comes from repeated English exposition rather than added A2-value examples.  
Fix: Compress the opening theory, the section-3 setup, the intonation explanation, and the closing motivation so the examples do more of the teaching.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: first section opening: `Have you ever wanted to describe something in more detail...` through `...new places in your life.`  
Issue: The learner gets 156 words of English explanation before the first Ukrainian model sentence. That slows the PPP presentation phase and delays contact with the target structure.  
Fix: Replace the long English opener with a short rule plus an immediate Ukrainian example using `який`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Another crucial aspect of mastering relative clauses is the intonation...` plus `Головне речення починається з нейтральної інтонації...`  
Issue: Intonation is a minor plan point, but it receives a long, repetitive treatment in both English and Ukrainian. This is disproportionate at A2 and contributes to the word-budget drift.  
Fix: Reduce this to one short note explaining “pause before the clause; say it like an added description.”

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `This single word serves as a powerful bridge.` and `Such a sentence sounds much more natural and shows your high level of language proficiency.`  
Issue: These lines are filler. They praise or dramatize the grammar instead of teaching it.  
Fix: Replace them with concrete functional explanations of what the structure does.

## Verdict: REVISE
REVISE. There are no clear Ukrainian-language errors, but the module falls below the pass gate on plan adherence, pedagogical efficiency, and tone: it is badly over target, too English-heavy at key entry points, and padded with filler that should be replaced by tighter instruction.

<fixes>
- find: |-
    Have you ever wanted to describe something in more detail without starting a whole new sentence? In Ukrainian, we do this using an **означальний** (attributive, defining) clause. This is a special type of dependent **речення** (sentence, clause) that acts just like a very long adjective. It helps us **описувати** (to describe) a noun that is mentioned in the main part of the phrase. 
    
    Instead of saying "I have a car. The car is fast," you can say "I have a car that is fast." In English, you might use words like "who," "which," or "that" to smoothly connect these related ideas together. In Ukrainian, the most common way to build these connections is by using the word **який** (which, that — masc.) and its corresponding forms. This single word serves as a powerful bridge. It allows you to create much richer, more detailed stories about the interesting people, everyday objects, and new places in your life.
  replace: |-
    Ukrainian uses an **означальний** clause to add information about a noun. The most common connector is **який** and its forms: **яка, яке, які**. Compare: «Це мій друг, який живе у Києві». One sentence now contains both the person and the description.

- find: |-
    When you start learning a language, you naturally speak in short, simple sentences. This is a normal stage, but it can make your speech sound a bit choppy. To sound more advanced and fluent, you need to learn how to combine these short statements into a single, cohesive thought. You can achieve this by using an attributive clause, which in Ukrainian is called an **означальний** (attributive, defining) clause. Such a **речення** (sentence, clause) acts like a long adjective, giving more information about a specific noun. We usually connect them with words like **який** (which, that — masc.).
  replace: |-
    Learners often begin with several short sentences. Relative clauses help combine them into one clearer sentence. In Ukrainian, this usually means adding **який** and its forms to describe a person, thing, or place more precisely.

- find: |-
    > *Let's look at a typical example of short sentences. This is my friend. He lives in Kyiv. He works as a programmer. These sentences are grammatically correct, but they sound too simple. We can combine them into one beautiful sentence using a relative pronoun. This is my friend, who lives in Kyiv and works as a programmer. Such a sentence sounds much more natural and shows your high level of language proficiency.*
  replace: |-
    > *We can combine two short sentences into one clearer sentence with a relative clause.*

- find: |-
    Another crucial aspect of mastering relative clauses is the intonation. Punctuation is strict in Ukrainian: you must always place a comma before the relative pronoun or adverb that introduces the clause. This comma is not just a grammatical rule; it is a direct instruction for your voice.
    
    Головне речення починається з нейтральної інтонації. Потім ви робите коротку паузу перед комою. Підрядна частина, яка починається з цих слів, вимовляється з нижчим тоном. Вона звучить як додаткове пояснення. Після цього інтонація повертається до нормального рівня. Ця пауза перед комою дає слухачеві сигнал, що зараз буде детальний опис.
    
    > *The main sentence begins with a neutral intonation. Then you make a short pause before the comma. The subordinate part, which begins with these words, is pronounced with a lower pitch. It sounds like an additional explanation. After that, the intonation returns to a normal level. This pause before the comma gives the listener a signal that a detailed description is coming.*
  replace: |-
    Intonation is simple at this level: make a short pause before the relative clause and say it like an added description.
    
    Головне речення починається нейтрально, перед комою є коротка пауза, а підрядна частина звучить як додаткове пояснення.
    
    > *In speech, make a short pause before the relative clause and pronounce it like an added description.*

- find: |-
    Now it is time to put all this theory into practice. Knowing the rules is only the first step; true fluency comes from personalizing the grammar. Think about your own life and the things that matter to you. How would you describe your favorite place using these relative clauses? How would you describe a person you admire, or an object you use every single day?
    
    Напишіть кілька речень про своє рідне місто. Використайте слова де, куди та звідки. Потім опишіть свого найкращого друга за допомогою відносних займенників. Згадайте кафе, яке ви любите відвідувати на вихідних. Регулярна практика допоможе вам використовувати ці конструкції у реальній розмові.
  replace: |-
    Now use the pattern yourself.
    
    Напишіть кілька речень про своє рідне місто, про людину, яку ви добре знаєте, і про кафе, яке ви любите. Використайте де, куди, звідки, який, яка, яке або які.
</fixes>