## Linguistic Scan
- Factual grammar error in Part 1: "`Remember the core logic: concrete, countable objects and people take **-а/-я** ... while abstract concepts, materials, and institutions take **-у/-ю**`" is too absolute. VESUM confirms parallel genitive singular forms such as `стола/столу` and `магазина/магазину`, so this is not a clean semantic split learners can rely on.
- Factual grammar error in Part 2: "`For feminine words, the ending is **-ої** (or **-еї** for soft sounds)`" is wrong as stated. VESUM confirms forms like `синьої`, `моєї`, `цієї`; the contrast here is not a simple "soft sounds = -еї" rule.
- Factual grammar error in Part 2: "`For plural words of all genders, the adjective and pronoun ending is uniformly **-их**`" is wrong. VESUM confirms genitive plural forms such as `нових`, `синіх`, `моїх`, `цих`.
- Factual grammar error in Part 2: "`negation always demands the genitive`" overstates the rule and teaches bad grammar generalization. The example with `немає` is correct, but the universal claim is not.

## Exercise Check
Markers found: `quiz-preposition-identification`, `fill-in-genitive-agreement`, `error-correction-genitive`, `match-up-situations`.

Placement is correct:
- `quiz-preposition-identification` appears after the Part 1 preposition/triggers explanation.
- `fill-in-genitive-agreement` and `error-correction-genitive` appear after the Part 2 agreement/plural/error section.
- `match-up-situations` appears after the Part 3 real-life usage section.

Plan alignment is good:
- Marker types match the plan’s `activity_hints`.
- Markers are distributed across the module rather than dumped at the end.
- No inline DSL exercise blocks were present to audit for answer logic.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The module follows the planned three-part structure and uses the planned situations almost verbatim: "`біля Софійського собору` ... `без квитка` ... `для групи з десяти людей` ... `до Хрещатика`," plus market, pharmacy, and directions contexts. |
| 2. Linguistic accuracy | 5/10 | Part 2 contains several wrong rules: "`For feminine words, the ending is **-ої** (or **-еї** for soft sounds)`," "`uniformly **-их**`," and "`negation always demands the genitive`." |
| 3. Pedagogical quality | 6/10 | Several explanations are taught as absolutes when they are not: "`concrete, countable objects and people take **-а/-я**`," "`uniformly **-их**`," "`negation always demands the genitive`." Learners could memorize false rules. |
| 4. Vocabulary coverage | 10/10 | All required and recommended plan vocabulary appears in prose: "`родовий відмінок`, `прийменник`, `узгодження`, `множина`, `однина`, `закінчення`, `перевірка`, `помилка`, `виправити`, `впізнати`, `вибрати`." |
| 5. Exercise quality | 9/10 | All four planned activity types have corresponding markers placed after the relevant teaching blocks: `quiz-preposition-identification`, `fill-in-genitive-agreement`, `error-correction-genitive`, `match-up-situations`. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and concrete, with usable prompts and scenarios such as "`Звідки ви?` / `Я з України.`" and the Kyiv tour dialogue. |
| 7. Structural integrity | 9/10 | All planned sections are present and ordered correctly, and the pipeline word count is 1630; there is one visible formatting artifact in the first dialogue: "`**Гід** (Guide)**:**`." |
| 8. Cultural accuracy | 10/10 | The module uses Ukrainian settings and examples on their own terms: "`Софійського собору`," "`Хрещатика`," market/pharmacy/city-navigation contexts, with no Russia-centric framing. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues are multi-turn and situational rather than robotic one-liners: tour guide, market, pharmacy, and question-answer pairs like "`Для кого цей новий телефон?` / `Це подарунок для мого молодшого брата.`" |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Part 1 — "`Remember the core logic: concrete, countable objects and people take **-а/-я** (`біля стола`, `без брата`), while abstract concepts, materials, and institutions take **-у/-ю** (`без цукру`, `до університету`).`"  
Issue: This teaches a false deterministic rule for masculine genitive singular. VESUM confirms parallel forms like `стола/столу` and `магазина/магазину`, so the explanation must be presented as a tendency, not a hard rule.  
Fix: Rewrite this sentence to say it is a broad tendency and note that some masculine nouns allow more than one genitive form.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Part 2 — "`For feminine words, the ending is **-ої** (or **-еї** for soft sounds).`"  
Issue: This is factually wrong as a rule for adjectives and pronouns. Verified feminine genitive forms include `синьої`, `моєї`, `цієї`; "`soft sounds = -еї`" is not an accurate rule.  
Fix: Replace with wording that distinguishes adjective and pronoun patterns, e.g. adjectives often `-ої`, pronouns `-ої / -єї` depending on the word.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Part 2 — "`For plural words of all genders, the adjective and pronoun ending is uniformly **-их**.`"  
Issue: This is false. Verified genitive plural forms include both `нових` and `синіх`, as well as pronouns `моїх`, `цих`.  
Fix: Change the rule to `-их / -іх, depending on the word`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Part 2 — "`Second, never forget that negation always demands the genitive: \"I don't have a sister\" is `У мене немає сестри`, never `У мене немає сестра`.`"  
Issue: The example with `немає` is correct, but the universal claim "`always demands the genitive`" is grammatically false and overteaches the rule.  
Fix: Limit the claim to negative constructions like `немає` instead of presenting it as an absolute rule for all negation.

[STRUCTURAL INTEGRITY] [SEVERITY: minor]  
Location: Part 1 opening dialogue — "`**Гід** (Guide)**:**`"  
Issue: Markdown formatting artifact.  
Fix: Change it to "`**Гід** (Guide):`".

## Verdict: REVISE
REVISE because the module has multiple critical factual grammar errors in the teaching text. PASS is blocked both by the severity gate and by dimensions below 9, even though the structure, vocabulary coverage, and exercise-marker placement are strong.

<fixes>
- find: "Remember the core logic: concrete, countable objects and people take **-а/-я** (`біля стола`, `без брата`), while abstract concepts, materials, and institutions take **-у/-ю** (`без цукру`, `до університету`)."
  replace: "Remember a broad tendency, not an absolute rule: many names of people and many concrete objects use **-а/-я** (`без брата`), while many abstract nouns, materials, and institutions use **-у/-ю** (`без цукру`, `до університету`). Some masculine nouns allow more than one genitive form, so it is best to learn common phrases individually."
- find: "For feminine words, the ending is **-ої** (or **-еї** for soft sounds)."
  replace: "For feminine words, genitive forms commonly include **-ої** in adjectives and **-ої / -єї** in pronouns, depending on the word."
- find: "For plural words of all genders, the adjective and pronoun ending is uniformly **-их**."
  replace: "For plural words of all genders, adjective and pronoun forms commonly end in **-их / -іх**, depending on the word."
- find: "Second, never forget that negation always demands the genitive: \"I don't have a sister\" is `У мене немає сестри`, never `У мене немає сестра`."
  replace: "Second, remember that the genitive is very common in negative constructions with words like `немає`: \"I don't have a sister\" is `У мене немає сестри`, never `У мене немає сестра`."
- find: "> **Гід** (Guide)**:** Добрий день! Сьогодні ми гуляємо центром Києва. Зараз ми стоїмо **біля Софійського собору** (near Saint Sophia Cathedral)."
  replace: "> **Гід** (Guide): Добрий день! Сьогодні ми гуляємо центром Києва. Зараз ми стоїмо **біля Софійського собору** (near Saint Sophia Cathedral)."
</fixes>