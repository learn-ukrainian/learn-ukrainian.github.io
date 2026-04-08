## Linguistic Scan
Errors found:
1. "коньми" instead of "кіньми" (morphological error).
2. "відкриває двері" instead of "відчиняє двері" (lexical calque).
3. "ми маємо" as a calque for "there are/we have" in a grammatical explanation context.

## Exercise Check
All 5 `<!-- INJECT_ACTIVITY: ... -->` markers match the plan's `activity_hints` exactly. They are placed logically after the corresponding teaching sections. The exercises effectively test the presented grammar rules rather than pure content recall. 

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The writer missed the explicit requirement to include housework tools ("мити водою, витирати ганчіркою, чистити щіткою, підмітати віником"). The plan point "пливти кораблем" was also missing from the transport examples. |
| 2. Linguistic accuracy | 8/10 | Found one morphological error: the instrumental plural of "кінь" is given as "коньми" instead of "кіньми" (VESUM confirmed). Also found one lexical calque: "відкриває двері" instead of "відчиняє двері". |
| 3. Pedagogical quality | 9/10 | The module follows PPP and explains the concepts clearly with 2-3 examples per point. Deducted 1 point because it used a calqued phrasing "Для іменників чоловічого роду ми маємо..." instead of a natural Ukrainian impersonal construction. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is well integrated. "Корабель" (recommended) was missing. |
| 5. Exercise quality | 10/10 | All 5 requested exercise markers are correctly injected after their respective sections. |
| 6. Engagement & tone | 10/10 | Teacher persona is encouraging and provides culturally and practically relevant examples (like the difference between "with a pen" as a tool vs. companion). |
| 7. Structural integrity | 10/10 | Clean markdown, word count exceeds 2000 (2947 words), H2 headers match plan exactly. |
| 8. Cultural accuracy | 10/10 | Correctly notes that Russianisms like "відправлятися" are common errors and provides authentic Ukrainian equivalents for departure ("відбуває", "рушає", "вирушає"). |
| 9. Dialogue & conversation quality | 9/10 | The dialogues are natural and effectively contrast grammatical concepts. |

## Findings

[2. Linguistic accuracy] [Critical]
Location: Section "Орудний відмінок множини" — `Ви можете зустріти «конями» *(with horses)* або «коньми».`
Issue: Incorrect morphological form. The instrumental plural of "кінь" is "кіньми", not "коньми" (verified via VESUM).
Fix: Replace `«коньми»` with `«кіньми»`.

[2. Linguistic accuracy] [Major]
Location: Section "Чим? Знаряддя дії" — `Він відкриває старі двері ключем *(He opens the old door with a key)*.`
Issue: Lexical calque/stylistic error. In Ukrainian, doors are "відчиняються", not "відкриваються".
Fix: Replace `відкриває` with `відчиняє`.

[3. Pedagogical quality] [Minor]
Location: Section "Чим? Знаряддя дії" — `Для іменників чоловічого роду ми маємо три основні закінчення. *(For masculine nouns, we have three main endings.)*`
Issue: Stylistic calque. "Ми маємо" (we have) is often calqued from English/Russian in grammar explanations. A natural Ukrainian phrasing is "є" or "існують".
Fix: Replace with `Для іменників чоловічого роду є три основні закінчення. *(For masculine nouns, there are three main endings.)*`

[1. Plan adherence] [Major]
Location: Section "Чим? Знаряддя дії" — paragraph after `Це велика ложка...`
Issue: The plan explicitly required teaching household chores with instrumental: "Housework and daily tools: мити водою, витирати ганчіркою, чистити щіткою, підмітати віником." These were entirely omitted.
Fix: Inject the missing examples at the end of the feminine nouns paragraph.

[1. Plan adherence] [Minor]
Location: Section "Їхати автобусом: Засіб пересування" — `Моя сестра летить літаком *(by airplane)*. Мої батьки люблять подорожувати машиною *(by car)*.`
Issue: The plan explicitly listed "пливти кораблем" as a target transport collocation, but it was skipped.
Fix: Add `Мій дідусь любить пливти кораблем *(to sail by ship)*.` to the transport list.

## Verdict: REVISE
The module requires revision due to a critical morphological error ("коньми" instead of "кіньми") and the omission of specific pedagogical examples mandated by the plan. 

<fixes>
- find: "Ви можете зустріти «конями» *(with horses)* або «коньми»."
  replace: "Ви можете зустріти «конями» *(with horses)* або «кіньми»."
- find: "Він відкриває старі двері ключем *(He opens the old door with a key)*."
  replace: "Він відчиняє старі двері ключем *(He opens the old door with a key)*."
- find: "Для іменників чоловічого роду ми маємо три основні закінчення. *(For masculine nouns, we have three main endings.)*"
  replace: "Для іменників чоловічого роду є три основні закінчення. *(For masculine nouns, there are three main endings.)*"
- find: "Це велика ложка *(This is a large spoon)*. Я їм смачний суп великою ложкою *(I eat delicious soup with a large spoon)*."
  replace: "Це велика ложка *(This is a large spoon)*. Я їм смачний суп великою ложкою *(I eat delicious soup with a large spoon)*.\n\nТакож ми використовуємо орудний відмінок для домашньої роботи: мити водою *(to wash with water)*, витирати ганчіркою *(to wipe with a rag)*, чистити щіткою *(to clean with a brush)*, підмітати віником *(to sweep with a broom)*."
- find: "Моя сестра летить літаком *(by airplane)*. Мої батьки люблять подорожувати машиною *(by car)*."
  replace: "Моя сестра летить літаком *(by airplane)*. Мій дідусь любить пливти кораблем *(to sail by ship)*. Мої батьки люблять подорожувати машиною *(by car)*."
</fixes>
