## Linguistic Scan
No linguistic errors found. No Russian-only characters (`ы`, `э`, `ё`, `ъ`) found in the module text.

## Exercise Check
- `quiz-dative-recognition` appears after Part 1 recognition content and matches the plan’s `quiz` hint.
- `fill-in-dative-endings` and `match-up-dative-verbs` appear after Part 2 form/government teaching and match the plan’s `fill-in` and `match-up` hints.
- `error-correction-dative` appears after the error-review section and matches the plan’s `error-correction` hint.
- Marker count matches the plan: 4/4.
- No inline DSL exercise blocks are present here, so exercise answer logic cannot be audited from this text alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | Part 1 is far over its 400-word budget: it runs about 581 words. The planned “Summary comparison chart of Nominative, Genitive, Dative endings for nouns, adjectives, and pronouns” is only a two-column phrase chart: `мій новий дім` / `моя старша сестра`, with no pronoun column. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym misuse, or wrong case forms found. High-risk forms such as `панові`, `подрузі`, `ріці`, `мусі`, `дякувати`, and `подобатися` check out. |
| 3. Pedagogical quality | 8/10 | Example density is strong, but a checkpoint module spends too much time in English meta-explanation: `The office Secret Santa game revolves around...`, `A state happens to you...` instead of moving faster to recognition and contrast tasks. |
| 4. Vocabulary coverage | 10/10 | All required items appear naturally in prose/examples: `давальний відмінок`, `допомагати`, `дякувати`, `подобатися`, `подарувати`, `надіслати`, `потрібно`, `холодно`. Recommended `закінчення`, `чергування`, `узгодження` also appear. |
| 5. Exercise quality | 10/10 | All four planned markers are present and placed after the relevant teaching blocks: `quiz-dative-recognition`, `fill-in-dative-endings`, `match-up-dative-verbs`, `error-correction-dative`. |
| 6. Engagement & tone | 8/10 | Mostly teacherly and clear, but the close slips into generic uplift: `Recognizing these structures ensures your Ukrainian sounds natural, polite, and deeply authentic...` |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and in order; the markdown is clean; the pipeline word count is 2073, which is safely above the 1500 target. |
| 8. Cultural accuracy | 10/10 | No Russia-centered framing or cultural inaccuracies. The module stays within Ukrainian usage and references. |
| 9. Dialogue & conversation quality | 10/10 | The Secret Santa dialogue is situational, named-speaker based, and aligned with the plan’s dialogue scenario. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Частина 1: Розпізнавання` — “The office Secret Santa game revolves around matching people with gifts.” / “To accurately identify the **давальний відмінок**...” / “A state happens to you, rather than you actively doing it.”  
Issue: The recognition section is substantially over budget and too discursive for a checkpoint module. It spends too many words on English exposition instead of moving directly to recognition contrasts and dative identification.  
Fix: Compress the three explanatory paragraphs so they point directly to `кому?/чому?`, the dative-vs-locative contrast, and the dative experiencer pattern.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Огляд помилок та порівняння відмінків` — “To consolidate your knowledge, review this summary comparison chart...” and the table below it  
Issue: The plan requires a summary chart for nominative, genitive, and dative endings covering nouns, adjectives, and pronouns. The current chart only shows two noun phrases and omits pronoun forms entirely.  
Fix: Replace the chart with a version that keeps the phrase contrasts and adds a personal-pronoun column.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `Підсумок` — “Recognizing these structures ensures your Ukrainian sounds natural, polite, and deeply authentic...”  
Issue: The closing uses generic promotional language rather than concrete learning payoff.  
Fix: Replace the promotional phrasing with a brief, specific recap of what the learner can now do with the dative case.

## Verdict: REVISE
REVISE. There are no linguistic blockers, but there are clear plan/pedagogy issues: Part 1 overruns its budget by a wide margin, and the required comparison chart is incomplete.

<fixes>
- find: "The office Secret Santa game revolves around matching people with gifts. When you talk about the recipient or the addressee of an action — the person who receives the book, the chocolate, or the wine — you are using the **давальний відмінок** *(dative case)*. The name of the case comes from the verb **давати** *(to give)*, which perfectly describes its primary function in the Ukrainian language. Whether you give a present, write an email, or tell a story, the person on the receiving end always takes the **давальний відмінок** *(dative case)*."
  replace: "In the Secret Santa dialogue, the recipient of the action takes the **давальний відмінок** *(dative case)*: **Олексієві, Наталці, новому колезі, шефу**."

- find: "To accurately identify the **давальний відмінок** *(dative case)* in a sentence, you must ask the questions **кому?** *(to whom?)* or **чому?** *(to what?)*. These questions separate the recipient of an action from other grammatical roles. A common challenge for learners is confusing the **давальний відмінок** *(dative case)* with the locative case, because many feminine nouns share the exact same **закінчення** *(ending (grammar))* in both cases. You can distinguish them by the question they answer and the presence of a preposition. The locative case answers **на/у кому? на/у чому?** *(on/in whom? on/in what?)* and is always accompanied by a preposition. The dative case usually functions without a preposition."
  replace: "To identify the **давальний відмінок** *(dative case)*, ask **кому?** *(to whom?)* or **чому?** *(to what?)*. The main checkpoint contrast here is with the locative: locative forms usually appear with a preposition (**на/у кому? на/у чому?**), while dative forms usually do not."

- find: "The **давальний відмінок** *(dative case)* is also fundamental for expressing physical or emotional states in impersonal constructions. When describing how someone feels, Ukrainian often uses a dative experiencer rather than a nominative active subject. A state happens to you, rather than you actively doing it. Compare the nominative subject sentence **Я замерзла.** *(I froze. - active verb)* with the impersonal dative state **Мені холодно.** *(I am cold [cold is happening to me]. - state)*. This structure is essential for expressing needs and impressions."
  replace: "The **давальний відмінок** *(dative case)* also appears in impersonal state expressions. Compare **Я замерзла.** *(I froze.)* with **Мені холодно.** *(I am cold.)*: the person experiencing the state is in the dative case. This pattern also appears with **потрібно** and similar expressions."

- find: "To consolidate your knowledge, review this summary comparison chart formatting the nominative, genitive, and dative endings for full phrases. Notice how the modifiers and nouns shift together. This review follows the core contrasts emphasized in Заболотний Grade 10, §157; Захарійчук Grade 4, §281; and Кравцова Grade 4, §135.\n\n| Відмінок *(Case)* | Чоловічий рід *(Masculine)* | Жіночий рід *(Feminine)* |\n| :--- | :--- | :--- |\n| **Називний** *(Nom)* | мій новий дім | моя старша сестра |\n| **Родовий** *(Gen)* | мого нового дому | моєї старшої сестри |\n| **Давальний** *(Dat)* | моєму новому дому / домові | моїй старшій сестрі |"
  replace: "To consolidate your knowledge, review this summary comparison chart of nominative, genitive, and dative forms. It keeps the phrase contrasts and adds core personal-pronoun forms, reflecting the contrasts emphasized in Заболотний Grade 10, §157; Захарійчук Grade 4, §281; and Кравцова Grade 4, §135.\n\n| Відмінок *(Case)* | Чоловічий рід *(Masculine phrase)* | Жіночий рід *(Feminine phrase)* | Особові займенники *(Personal pronouns)* |\n| :--- | :--- | :--- | :--- |\n| **Називний** *(Nom)* | мій новий дім | моя старша сестра | я, ти, вона |\n| **Родовий** *(Gen)* | мого нового дому | моєї старшої сестри | мене, тебе, її |\n| **Давальний** *(Dat)* | моєму новому дому / домові | моїй старшій сестрі | мені, тобі, їй |"

- find: "You have now reviewed the essential **закінчення** *(ending (grammar))* for all genders, including the distinctly Ukrainian parallel masculine forms like **-ові** and **-еві**, and the vital consonant alternations in feminine nouns. You have practiced strict **узгодження** *(agreement (grammar))* across adjectives, possessive pronouns, and nouns. Most importantly, you understand the critical verb government for verbs like **допомагати** *(to help)*, **дякувати** *(to thank)*, and **подобатися** *(to be pleasing to, to like)*, breaking free from English syntax patterns. Recognizing these structures ensures your Ukrainian sounds natural, polite, and deeply authentic as you prepare to integrate these skills into more complex dialogues in the upcoming modules."
  replace: "You have now reviewed the essential **закінчення** *(ending (grammar))* for all genders, the main consonant alternations in feminine nouns, pronoun forms, and **узгодження** *(agreement (grammar))* across modifiers and nouns. You have also reviewed verb government for **допомагати** *(to help)*, **дякувати** *(to thank)*, and **подобатися** *(to be pleasing to, to like)*, which prepares you for more complex A2 dialogues."
</fixes>