## Linguistic Scan
No linguistic errors found.

## Exercise Check
Markers present: `fill-in-khotity-conjugation`, `quiz-modal-choice`, `fill-in-modal-logic`, `quiz-verb-patterns`.

The marker count matches the four `activity_hints`, and each marker appears after the relevant teaching material. No inline DSL exercise blocks are present, so there is no exercise-logic error visible at the prose layer.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned sections and plan vocabulary are present, but section pacing drifts badly from the 300-word targets: `Хоті́ти` ≈ 432 words, `Могти́ і му́сити` ≈ 463, `Підсумок` ≈ 377. The prose also never cites `Караман` or `Літвінова`, even though both references are in the plan. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or wrong case/gender forms found. Core forms like `каву`, `допомогти`, `порекомендувати`, and `треба` are valid. |
| 3. Pedagogical quality | 7/10 | The module has many examples, but A1 explanations become too abstract: `"A key morphological feature..."`, `"Compound Verbal Predicate structure"`, and `"logical linguistic foundation"` add metalanguage and English theory that are heavier than the level requires. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary appears naturally in prose, and all recommended items are used in context: `шкода`, `допомогти`, `борщ`, `порекомендувати`, `треба`. |
| 5. Exercise quality | 9/10 | All four planned activity types have matching markers, and they come after the relevant teaching sections. No prose-level exercise logic problems are visible. |
| 6. Engagement & tone | 7/10 | Parts of the summary slip into generic filler: `"You have now successfully built the grammatical foundation..."` and `"instantly multiply the variety..."` add length without adding much learner value. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and in order; the pipeline word count is 1577, above the 1200 target; inject markers are expected and not stray artifacts. |
| 8. Cultural accuracy | 9/10 | The module presents Ukrainian on its own terms, uses ordinary everyday situations, and avoids Russian-centered framing. |
| 9. Dialogue & conversation quality | 9/10 | The named-speaker weekend dialogue is natural and multi-turn; the café exchange is short but functional and supports the grammar point. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Хоті́ти (To Want)`, `## Могти́ і му́сити (Can and Must)`, `## Підсумок — Summary` — especially `"The verb **хотіти**..."`, `"The verb **могти**..."`, and the first two summary paragraphs  
Issue: Three sections overshoot the planned 300-word pacing by a wide margin, and the module does not integrate the planned textbook references `Караман` and `Літвінова`.  
Fix: Replace the most verbose theory paragraphs with shorter rule-first explanations and add one concise sentence citing the two plan references in the `Хоті́ти` section.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `"When you want to express a clear desire to perform an action, you use what is called a Compound Verbal Predicate structure."` and `"These three distinct modal verbs form the logical linguistic foundation..."`  
Issue: The module explains A1 grammar with advanced metalanguage instead of simple pattern-based teaching. This raises cognitive load without helping the learner produce better sentences.  
Fix: Rewrite these passages in plain A1 language: `хотіти + infinitive`, `могти + infinitive`, `мусити + infinitive`, with the existing examples doing the work.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `"You have now successfully built the grammatical foundation necessary..."` and `"By seamlessly combining..."`  
Issue: The summary opens with generic, congratulatory filler instead of a direct recap.  
Fix: Replace the opener with a concise practical summary of the three patterns and the two stem changes.

## Verdict: REVISE
REVISE. No Ukrainian-language error was found, but there are multiple quality findings, and dimensions 1, 3, and 6 are below 9. This needs targeted tightening, not a full rebuild.

<fixes>
- find: 'The verb **хотіти** (to want) is one of the most frequently used words in the Ukrainian language, and it operates as a true irregular verb. Despite ending in **-іти́**, which typically signals a Group II conjugation pattern, **хотіти** actually conjugates according to the specific rules of Group I. When pronouncing this word, you must ensure that you make the first vowel a clear, open Ukrainian **о**, carefully distinguishing it from the reduced sounds you might encounter in other Slavic languages.'
  replace: 'The verb **хотіти** (to want) is irregular. Although it ends in **-іти́**, it conjugates as Group I. This matches the plan references: **Караман** (Grade 10, p.179) and **Літвінова** (Grade 7, p.55) both treat **хотіти** as a Group I exception.'
- find: 'A key morphological feature of **хотіти** is the consistent consonant shift that occurs right in its root. As you conjugate it through the present tense, the letter **т** from the dictionary form (**хот-**) changes entirely to the letter **ч** (**хоч-**) across every single grammatical person. This shift is a very common and essential phonetic pattern in Ukrainian.'
  replace: 'In the present tense, the stem changes from **хот-** to **хоч-** in every form.'
- find: 'When you want to express a clear desire to perform an action, you use what is called a Compound Verbal Predicate structure. This simply means you take the conjugated modal verb (**хочу**, **хочеш**, etc.) and immediately follow it with the infinitive form of the main verb. Unlike English, which explicitly requires the particle "to" placed between the two verbs, Ukrainian simply links them directly together. To form the negative, place the particle **не** directly before the verb: **я не хочу** (I do not want), **ти не хочеш?** (do you not want?), **вона не хоче** (she does not want). While polite requests use conditional forms like **хоті́в би** or **хоті́ла би** (I would like) — which you will learn later — for now, **я хочу** is the standard, direct way to express a want.'
  replace: 'To talk about an action, use **хотіти + infinitive**: **Я хочу читати**, **Ти не хочеш гуляти?** For negation, put **не** before the verb: **Я не хочу спати**. Conditional requests like **хоті́в би / хоті́ла би** come later.'
- find: 'The verb **могти** (can, to be able) expresses personal ability or granted permission, and it is also classified as an irregular Group I verb. Much like "to want", it features a significant consonant shift within its root structure. The original letter **г** (**мог-**) transforms into **ж** (**мож-**) consistently across all present tense forms. This predictable shift is a hallmark of Ukrainian pronunciation.'
  replace: 'The verb **могти** (can, to be able) is also irregular. In the present tense, the stem changes from **мог-** to **мож-**.'
- find: 'You will use **могти** primarily to talk about your internal physical abilities, to discuss newly acquired skills, or to formally ask for permission from someone else. It functions identically to **хотіти** by forming a compound structure with a following infinitive verb to create a complete thought.'
  replace: 'Use **могти + infinitive** for ability or possibility: **Я можу говорити українською**, **Ти можеш допомогти?**, **Він не може працювати**.'
- find: 'In sharp contrast, the verb **мусити** (must, to have to) expresses a strong, unavoidable obligation. This verb operates as a regular Group II verb with only one minor, yet critical exception: the consonant **с** shifts to **ш** strictly in the first-person singular ("I" form). The rest of the conjugation paradigm follows the standard Group II pattern flawlessly. While **хотіти** focuses entirely on personal choice, **мусити** equals pure obligation. It is much stronger than **тре́ба** (need to), which functions as a simpler, impersonal alternative that you will use later.'
  replace: '**Мусити** expresses obligation. It follows Group II endings, with one key stem change in the **я** form: **я мушу**, but **ти мусиш, він/вона мусить, ми мусимо, ви мусите, вони мусять**. It is stronger and more personal than impersonal **треба**.'
- find: 'These three distinct modal verbs form the logical linguistic foundation for negotiating any daily situation. You can combine them to easily explain complex circumstances, weighing your internal desires against your actual abilities and your pressing duties. Observe how beautifully they work together in a single context: **я хочу гуляти** (I possess the internal desire to walk), **але́ не можу** (but I lack the physical possibility or ability to do so) — **я мушу працювати** (because I hold the strict necessity to work).'
  replace: 'Together, these verbs let you compare desire, ability, and obligation: **я хочу гуляти, але не можу — я мушу працювати**.'
- find: 'For a slightly softer or more impersonal way to say "it is necessary" or "I need to," Ukrainians frequently use the single word **треба** (need to). It does not conjugate at all for different grammatical persons, making it very beginner-friendly for rapidly expressing everyday needs.'
  replace: 'For a softer impersonal meaning, Ukrainian often uses **треба**. It does not change by person.'
- find: 'You have now successfully built the grammatical foundation necessary for expressing complex thoughts using the Compound Verbal Predicate structure. By seamlessly combining a conjugated modal verb with any infinitive action, you instantly multiply the variety of sentences you can independently create. Always remember the critical consonant shifts that define the two major irregular verbs: the root of **хотіти** completely trades its **т** for a **ч** across the entire paradigm, while the root of **могти** consistently shifts its **г** to a **ж** across every single present tense form (**вони можуть**). You also learned that the verb of strict obligation, **мусити**, remains entirely regular for Group II, except for the **с** shifting to **ш** exclusively in the specific **я мушу** form.'
  replace: 'Remember the three core patterns: **хочу + infinitive** for desire, **можу + infinitive** for ability, and **мушу + infinitive** for obligation. The irregular stems are **хот- → хоч-** and **мог- → мож-**. **Мусити** is regular except for **я мушу**.'
- find: 'From a strictly practical standpoint, it is incredibly important to remember the core equations of these modals: **Хочу** + infinitive expresses desire (I want to). **Можу** + infinitive expresses ability (I can). **Мушу** + infinitive expresses obligation (I must). Furthermore, **хотіти** is by far the most versatile of the three verbs discussed. It stands as the only modal verb that frequently pairs directly with a noun object to express a direct physical desire, such as **я хочу каву** (I want coffee). On the other hand, both **могти** and **мусити** almost always demand an accompanying infinitive action to make logical sense, such as **я можу працювати** (I can work). To effectively negate any of these statements, you simply place the negative particle **не** immediately before the conjugated modal verb: **я не хочу** (I do not want), **ми не можемо** (we cannot).'
  replace: '**Хотіти** can also take a noun: **Я хочу каву**. **Могти** and **мусити** usually need an infinitive: **Я можу працювати**, **Я мушу працювати**. To negate them, put **не** before the modal verb: **я не хочу**, **ми не можемо**.'
</fixes>