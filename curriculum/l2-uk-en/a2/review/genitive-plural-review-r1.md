## Linguistic Scan
- `п'ять раз`: While commonly used in colloquial speech, standard Ukrainian prefers `п'ять разів` when counting times after numbers 5 and above. 
- All other phonetic explanations, morphological breakdowns (e.g., fleeting vowels, consonant clusters with inserted vowels), and word forms are linguistically accurate and correctly handle zero-endings vs. standard endings. No Russianisms or Surzhyk were found.

## Exercise Check
- **Placement Issues:** The `group-sort` marker is placed right after the masculine section, but the plan requires it to test `(-ів/-їв vs. zero vs. -ей)`. Since zero and `-ей` are primarily taught in the feminine and neuter sections, this forces learners to test on untaught material. The `match-up` marker is placed after the feminine section, before neuter nouns are introduced.
- **Marker String Deviation:** The `group-sort` marker's focus string was altered by the writer to `(-ів/-їв vs. zero)` to fit the premature placement. This violates the plan's exact hint.
- **Count:** All 4 requested exercises are present. 

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Missing several specific plan requirements: the mixed group (`площа→площ`, `задача→задач`), the masculine/neuter `-ей` exceptions (`гостей`, `коней`, `очей`), `теля→телят`, `будинків`, `студентка`, and the word `декілька`. |
| 2. Linguistic accuracy | 9/10 | High overall accuracy. Correct vowel insertion rules and soft sign placements. Minor deduction for using the colloquial `п'ять раз` instead of the standard `п'ять разів`. |
| 3. Pedagogical quality | 8/10 | The PPP structure is excellent, but placing comprehensive review exercises (`group-sort` and `match-up`) in the middle of the lesson before all rules have been taught breaks the pedagogical flow. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary is present. `декілька` from the recommended/practice list was missed. |
| 5. Exercise quality | 8/10 | The exercise formats are good, but the writer altered the plan's `activity_hints` focus string for `group-sort` to mask the fact that it was placed prematurely. |
| 6. Engagement & tone | 9/10 | Engaging dialogues and strong cultural context. Minor deduction for meta-commentary: "Finally, let us review when to actually use..." and "There is no logical reason for this; it is a historical linguistic anomaly." |
| 7. Structural integrity | 10/10 | Clean markdown, appropriate H2 usage, and logical visual flow. |
| 8. Cultural accuracy | 10/10 | Real Ukrainian situations (hryvnias, Kyiv museums) and natural vocabulary. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are solid and well-contextualized for an inventory check and daily tasks, though slightly transactional in places. |

## Findings

[1. Plan adherence] [major]
Location: Section `Чоловічий рід`, `Жіночий рід`, and `Середній рід`
Issue: Several plan points and examples were omitted: the mixed group (`площа`, `задача`), the masculine/neuter `-ей` exceptions (`гостей`, `коней`, `очей`), `теля`, `будинків`, `студентка`, and the word `декілька`.
Fix: Insert these missing examples and sections into their respective categories.

[2. Linguistic accuracy] [minor]
Location: `Я читав цю книгу п'ять **раз**.`
Issue: While understood colloquially, standard Ukrainian prefers `разів` in the Genitive plural after numbers like 5.
Fix: Change `п'ять раз` to `п'ять разів`.

[3. Pedagogical quality] [major]
Location: `<!-- INJECT_ACTIVITY: group-sort... -->` and `<!-- INJECT_ACTIVITY: match-up... -->`
Issue: `group-sort` is placed after the masculine section but tests endings (-ей, zero) that haven't been fully taught yet. `match-up` tests all genders but is placed before the neuter section.
Fix: Move both markers to the end of the lesson before the summary, and restore the exact focus string from the plan for `group-sort`.

[6. Engagement & tone] [minor]
Location: "Finally, let us review when to actually use all these complex Genitive plural forms." and "There is no logical reason for this; it is a historical linguistic anomaly."
Issue: Unnecessary meta-commentary ("let us review") and "telling instead of showing" ("historical anomaly").
Fix: Rephrase to be more direct and remove the meta-commentary.

## Verdict: REVISE
The module correctly explains one of the hardest grammatical cases in Ukrainian and uses excellent examples. However, missing several key plan points (like the mixed group and neuter exceptions) and the premature placement of comprehensive exercises require a revision cycle to fix.

<fixes>
- find: "автобус *(bus)* → автобус + -ів = **автобусів** *(buses)*"
  replace: "автобус *(bus)* → автобус + -ів = **автобусів** *(buses)*\n* будинок *(building)* → будинк + -ів = **будинків** *(buildings)*"
- find: "Ми довго чекаємо біля старих **автобусів**. *(We are waiting a long time near the old buses.)*"
  replace: "Ми довго чекаємо біля старих **автобусів**. *(We are waiting a long time near the old buses.)*\nНа цій вулиці багато високих **будинків**. *(There are many tall buildings on this street.)*"
- find: "зупинка *(stop)* → зупин + о + к = **зупинок**"
  replace: "зупинка *(stop)* → зупин + о + к = **зупинок**\n* студентка *(student, f)* → студент + о + к = **студенток**"
- find: "Автобус проїхав п'ять **зупинок**. *(The bus passed five stops.)*"
  replace: "Автобус проїхав п'ять **зупинок**. *(The bus passed five stops.)*\nВ аудиторії було багато **студенток**. *(There were many female students in the classroom.)*"
- find: "Дідусь знає багато цікавих **історій**. *(Grandfather knows many interesting stories.)*"
  replace: "Дідусь знає багато цікавих **історій**. *(Grandfather knows many interesting stories.)*\n\nIf a feminine stem ends in a postalveolar consonant (**ж**, **ч**, **ш**, **щ**), the noun takes a zero ending without any vowel insertion. These are called the mixed group. Because the sounds are already quite strong, they don't need an inserted vowel to be pronounced clearly.\n\n**Паттерн: Основа на ж, ч, ш, щ → нульове закінчення** *(Pattern: Stem in ж, ч, ш, щ → zero ending)*\n* площа *(square)* → площ + ∅ = **площ**\n* задача *(math problem)* → задач + ∅ = **задач**\n\n**Читаємо українською**\nУ місті п'ять великих **площ**. *(There are five large squares in the city.)*\nСтуденти вирішили десять складних **задач**. *(The students solved ten difficult math problems.)*"
- find: "Вони вивчають історію африканських **племен**. *(They are studying the history of African tribes.)*"
  replace: "Вони вивчають історію африканських **племен**. *(They are studying the history of African tribes.)*\n\nSimilarly, neuter nouns denoting young animals take a zero ending in the Genitive plural after their plural stem.\n\n**Паттерн: Назви малят → нульове закінчення** *(Pattern: Baby animals → zero ending)*\n* теля *(calf)* → телят + ∅ = **телят**\n\n**Читаємо українською**\nНа фермі багато маленьких **телят**. *(There are many small calves on the farm.)*\n\nNote that the exceptional **-ей** ending we saw in the feminine gender also appears in a very small, closed group of masculine and neuter nouns. You must memorize these common words.\n\n**Паттерн: Винятки чоловічого та середнього роду на -ей** *(Pattern: Masculine and neuter exceptions with -ей)*\n* гість *(guest, m)* → гост + -ей = **гостей**\n* кінь *(horse, m)* → кон + -ей = **коней**\n* око *(eye, n)* → оч + -ей = **очей**\n\n**Читаємо українською**\nНа святі було багато **гостей**. *(There were many guests at the holiday.)*\nУ фермера є п'ять **коней**. *(The farmer has five horses.)*\nУ неї немає блакитних **очей**. *(She does not have blue eyes.)*"
- find: "Сьогодні у нас немає **лекцій**. *(Today we have no lectures.)*"
  replace: "Сьогодні у нас немає **лекцій**. *(Today we have no lectures.)*\nМи відвідали декілька **лекцій**. *(We attended several lectures.)*"
- find: "У нас є тільки п'ять **днів**. *(We have only five days.)*"
  replace: "У нас є тільки п'ять **днів**. *(We have only five days.)*\nМи чекали декілька **днів**. *(We waited for several days.)*"
- find: "Я читав цю книгу п'ять **раз**. *(I read this book five times.)*\n\n<!-- INJECT_ACTIVITY: group-sort, Sort Genitive plural forms by ending type (-ів/-їв vs. zero) -->"
  replace: "Я читав цю книгу п'ять **разів**. *(I read this book five times.)*"
- find: "— **Викладач:** Близько ста **сімей**. *(About a hundred families.)*\n\n<!-- INJECT_ACTIVITY: match-up, Match Nominative singular nouns to their Genitive plural forms -->"
  replace: "— **Викладач:** Близько ста **сімей**. *(About a hundred families.)*"
- find: "<!-- INJECT_ACTIVITY: fill-in, Form the Genitive plural of given nouns (all three genders) -->\n<!-- INJECT_ACTIVITY: quiz, Choose the correct Genitive plural ending (-ів, -ей, zero, or -їв) -->\n\n## Підсумок — Summary"
  replace: "<!-- INJECT_ACTIVITY: fill-in, Form the Genitive plural of given nouns (all three genders) -->\n<!-- INJECT_ACTIVITY: quiz, Choose the correct Genitive plural ending (-ів, -ей, zero, or -їв) -->\n<!-- INJECT_ACTIVITY: match-up, Match Nominative singular nouns to their Genitive plural forms -->\n<!-- INJECT_ACTIVITY: group-sort, Sort Genitive plural forms by ending type (-ів/-їв vs. zero vs. -ей) -->\n\n## Підсумок — Summary"
- find: "Finally, let us review when to actually use all these complex Genitive plural forms."
  replace: "These Genitive plural forms are essential for everyday situations, specifically when counting."
- find: "There is no logical reason for this; it is a historical linguistic anomaly. You simply need to memorize these exceptions, as they include some of the most common words used in everyday Ukrainian speech."
  replace: "These exceptions include some of the most common words used in everyday Ukrainian speech."
</fixes>
