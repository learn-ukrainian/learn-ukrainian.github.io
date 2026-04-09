## Linguistic Scan
2 linguistic errors found:
1. The rule stating `А форма знахідного відмінка для істот завжди збігається з формою родового відмінка` is factually incorrect. For feminine singular animate nouns (like "мама"), the accusative form ("маму") does NOT match the genitive form ("мами"). The rule is generally true only for masculine singular animates and plural animates.
2. The phrase `за часом` in `Дієслова змінюють свою форму за особами та за часом` uses the singular, whereas the standard Ukrainian grammatical terminology is plural: `змінюються за часами`.

## Exercise Check
- `<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-to-their-english-equivalents -->`: Present. Placed logically after parts of speech introduction. Matches plan hint.
- `<!-- INJECT_ACTIVITY: group-sort-sort-words-into-parts-of-speech-imennyk-prykmetnyk-diieslovo-etc -->`: Present. Placed at the end of the parts of speech section. Matches plan hint.
- `<!-- INJECT_ACTIVITY: fill-in-complete-case-questions-rodovyi -->`: Present. Placed after the case system and question method are explained. Matches plan hint.
- `<!-- INJECT_ACTIVITY: quiz-identify-the-part-of-speech-of-underlined-words-in-ukrainian-sentences -->`: Present. Placed after the grammar labeling and gender/number section. Matches plan hint.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Deductions for two missing or altered items: 1) The generated content used a different mnemonic (`«Нашого Ромчика Дивує Зебра — Оця Маленька Красуня»`) than the one explicitly requested in the plan (`"Не Роби Дурниць, Знай, Орудуй Місцем, Кличний!"`). 2) The plan requested `Practice: label 10 words from previous modules with their full grammatical description` in section 3, which was completely omitted (the text ends abruptly with `Це ваша головна мета на цьому етапі`). |
| 2. Linguistic accuracy | 8/10 | Deduction for a critical factual error regarding cases: `А форма знахідного відмінка для істот завжди збігається з формою родового відмінка` (this is false for feminine singular nouns). Also a minor error with grammatical terminology: `змінюють свою форму за ... часом` instead of standard `за часами`. |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical flow. Complex grammar metalanguage is broken down using the actual methods and analogies found in Ukrainian Grade 3-4 textbooks. The reading comprehension exercise analyzing a Ukrainian grammar rule without translation is exceptionally well-designed. |
| 4. Vocabulary coverage | 10/10 | All 12 required terms and all 5 recommended terms from the plan were naturally integrated with clear context and examples. |
| 5. Exercise quality | 10/10 | All 4 activity markers are present, correctly placed after the relevant instructional content, and match the specified focus of the plan. |
| 6. Engagement & tone | 10/10 | Very encouraging, structured teacher persona. The inclusion of classroom dialogues ("Марко: Наступне речення: «Я бачу кота»...") makes the metalanguage lesson feel active rather than passive. |
| 7. Structural integrity | 10/10 | Clean Markdown formatting. All sections from the plan are present with identical headers. Word count (3174 words) robustly meets the 2000-word target. |
| 8. Cultural accuracy | 10/10 | Uses authentic Ukrainian pedagogical approaches (e.g., teaching cases using the "question method" from verbs, rather than prepositions or rote ending memorization). |
| 9. Dialogue & conversation quality | 10/10 | The embedded dialogues are natural, appropriately leveled, and highly effective at modeling how students practice grammar analysis. |

## Findings

[DIMENSION] 1. Plan adherence [SEVERITY: major]
Location: `Вони вчать спеціальну фразу: «**Нашого Ромчика Дивує Зебра — Оця Маленька Красуня**» *(Our Romchik is surprised by the zebra — this little beauty)*.`
Issue: The writer used a different case mnemonic than the one explicitly requested in the plan ("Не Роби Дурниць...").
Fix: Replace the generated phrase to match the plan's mnemonic exactly.

[DIMENSION] 1. Plan adherence [SEVERITY: major]
Location: `Ви точно знаєте, чому слово має таку форму. *(You know exactly why the word has such a form.)* Це ваша головна мета на цьому етапі. *(This is your main goal at this stage.)*`
Issue: The writer completely skipped the required section 3 plan point: "Practice: label 10 words from previous modules with their full grammatical description in Ukrainian terms."
Fix: Insert the missing 10-word labeling practice directly after this paragraph.

[DIMENSION] 2. Linguistic accuracy [SEVERITY: critical]
Location: `А форма знахідного відмінка для істот завжди збігається з формою родового відмінка.`
Issue: Factual grammar error. The accusative case form coincides with the genitive ONLY for masculine singular animates (and plurals). It does NOT coincide for feminine singular animates (e.g., Н: мама, Р: мами, Зн: маму). The absolute statement "завжди" is a critical falsehood that will teach the wrong rule.
Fix: Qualify the rule by specifying "для істот чоловічого роду" (for masculine animates).

[DIMENSION] 2. Linguistic accuracy [SEVERITY: critical]
Location: `З яким відмінком збігається форма знахідного відмінка для всіх істот? *(Which case does the accusative form for all animates coincide with?)* Вона збігається з родовим відмінком.`
Issue: Propagates the factual error from the textbook excerpt into the comprehension question and its answer.
Fix: Update the question to match the corrected rule ("для істот чоловічого роду").

[DIMENSION] 2. Linguistic accuracy [SEVERITY: minor]
Location: `Дієслова змінюють свою форму за особами та за часом.`
Issue: Uses singular "за часом" when describing verb conjugation categories. The standard grammatical terminology uses the plural "за часами".
Fix: Change "за часом" to "за часами".

## Verdict: REVISE
The module is incredibly strong pedagogically but contains a critical factual error regarding the rules of the accusative case that must be corrected. It also omitted a required practice exercise from the plan. With deterministic find/replace fixes, this module will be ready to pass.

<fixes>
- find: "Дієслова змінюють свою форму за особами та за часом."
  replace: "Дієслова змінюють свою форму за особами та за часами."
- find: "Вони вчать спеціальну фразу: «**Нашого Ромчика Дивує Зебра — Оця Маленька Красуня**» *(Our Romchik is surprised by the zebra — this little beauty)*."
  replace: "Вони вчать спеціальну фразу: «**Не Роби Дурниць, Знай, Орудуй Місцем, Кличний!**» *(Don't do silly things, know, operate with place, vocative!)*."
- find: "Ви точно знаєте, чому слово має таку форму. *(You know exactly why the word has such a form.)* Це ваша головна мета на цьому етапі. *(This is your main goal at this stage.)*"
  replace: "Ви точно знаєте, чому слово має таку форму. *(You know exactly why the word has such a form.)* Це ваша головна мета на цьому етапі. *(This is your main goal at this stage.)*\n\nДавайте попрактикуємось аналізувати слова з попередніх модулів:\n1. **брат** *(brother)* — іменник, чоловічий рід, однина, називний відмінок.\n2. **(для) сестри** *(for sister)* — іменник, жіночий рід, однина, родовий відмінок.\n3. **(у) місті** *(in the city)* — іменник, середній рід, однина, місцевий відмінок.\n4. **новий** *(new)* — прикметник, чоловічий рід, однина, називний відмінок.\n5. **великі** *(big)* — прикметник, множина, називний відмінок.\n6. **студентом** *(by a student)* — іменник, чоловічий рід, однина, орудний відмінок.\n7. **(до) Києва** *(to Kyiv)* — іменник, чоловічий рід, однина, родовий відмінок.\n8. **я** *(I)* — займенник, однина, називний відмінок.\n9. **працювати** *(to work)* — дієслово, початкова форма (інфінітив).\n10. **смачну (каву)** *(tasty coffee)* — прикметник, жіночий рід, однина, знахідний відмінок."
- find: "А форма знахідного відмінка для істот завжди збігається з формою родового відмінка."
  replace: "А форма знахідного відмінка для істот чоловічого роду збігається з формою родового відмінка."
- find: "З яким відмінком збігається форма знахідного відмінка для всіх істот? *(Which case does the accusative form for all animates coincide with?)* Вона збігається з родовим відмінком."
  replace: "З яким відмінком збігається форма знахідного відмінка для істот чоловічого роду? *(Which case does the accusative form for masculine animates coincide with?)* Вона збігається з родовим відмінком."
</fixes>
