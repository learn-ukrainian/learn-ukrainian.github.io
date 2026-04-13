## Linguistic Scan
Found 3 issues requiring fixes:
- "кар'єрного росту" (calque/Russianism; correct form: "кар'єрного зростання")
- "подати на підвищення" (literal calque of English "apply for a promotion")
- "-чиня" (factually incorrect morphological claim about the suffix for "продавчиня", which is "-ин(я)" with consonant alternation according to Правопис 2019 § 32.4)

## Exercise Check
All 6 exercise markers are present and correctly placed after their respective instructional sections.
- `match-up-work-terms` and `group-sort-categories` are placed perfectly after Section 1 (vocabulary).
- `fill-in-aspect-work` and `quiz-aspect-logic` are placed after Section 2 (aspect logic).
- `role-play-interview` and `open-writing-bio` are placed after Section 3 (situational phrasing).
The logic and placement perfectly match the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All objectives and sections covered. Word count (5958) exceeds the 4000-word target. Required vocabulary is seamlessly integrated. Dialogues match the plan's motivational structure. |
| 2. Linguistic accuracy | 8/10 | DEDUCT for two calques: "кар'єрного росту" (should be "кар'єрного зростання") and "подати на підвищення" (calque of "apply for a promotion", should be "попросити про підвищення" або "подати заяву"). Otherwise, excellent grammatical accuracy. |
| 3. Pedagogical quality | 9/10 | DEDUCT for the morphological misclassification of "-чиня". REWARD for exceptional explanations of aspect usage ("тло проти події") and precise breakdowns of Instrumental vs. Accusative case usage for duties (`відповідати за` vs `керувати`). |
| 4. Vocabulary coverage | 10/10 | All required and recommended words (професія, посада, обов'язок, стажування, etc.) are present and contextualized naturally without bare lists. |
| 5. Exercise quality | 10/10 | Markers perfectly align with the `activity_hints` in type and focus, placed precisely after the concepts are taught. |
| 6. Engagement & tone | 10/10 | Teacher persona is encouraging and professional. Great use of metaphors ("Imagine that your resume is a movie") and clear tips. |
| 7. Structural integrity | 10/10 | Clean markdown, excellent organization, and the word count significantly exceeds the target, providing rich depth. |
| 8. Cultural accuracy | 10/10 | Strong emphasis on modern Ukrainian business norms, discarding Soviet-era "робітник" in favor of "працівник", and a solid section on the importance of "фемінітиви" codified in Pravopys 2019. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are natural and effectively model the transition from informal to formal registers, though one line contained the aforementioned calque "подати на підвищення". |

## Findings

[DIMENSION] 2. Linguistic accuracy [SEVERITY: critical]
Location: `Я завжди пояснюю друзям, що мій фах дає дуже багато можливостей для кар'єрного росту.`
Issue: "кар'єрного росту" is a calque/Russianism; the natural Ukrainian phrasing is "кар'єрного зростання" (which the writer correctly uses later in the text).
Fix: Replace with "кар'єрного зростання".

[DIMENSION] 2. Linguistic accuracy [SEVERITY: critical]
Location: `Спочатку я хочу подати на підвищення. Я вже розмовляла з керівником про це. *(Not yet. First I want to apply for a promotion.`
Issue: "подати на підвищення" is an unnatural calque of the English phrase "apply for a promotion". Natural phrasing between colleagues would be "попросити про підвищення" (to ask for a promotion).
Fix: Replace with "попросити про підвищення" (and adjust the English translation to "ask for a promotion").

[DIMENSION] 3. Pedagogical quality [SEVERITY: critical]
Location: `If the masculine form ends in «-ець», the feminine form typically uses the suffix **-чиня**, transforming «продавець»`
Issue: Factually incorrect claim about Ukrainian morphology. According to Pravopys 2019 § 32.4, the suffix used to form words like "продавчиня" or "кравчиня" from stems ending in "-ець" is "-ин(я)", which attaches to the stem with a consonant alternation (ц -> ч). There is no "-чиня" suffix.
Fix: Update to correctly identify the suffix as "-ин(я)" with a consonant change.

## Verdict: REVISE
The module is exceptionally well-written, deep, and pedagogically sound, but it contains a critical morphological misclassification regarding the "-ин(я)" suffix and two calques that need to be resolved before publishing.

<fixes>
- find: "Я завжди пояснюю друзям, що мій фах дає дуже багато можливостей для кар'єрного росту."
  replace: "Я завжди пояснюю друзям, що мій фах дає дуже багато можливостей для кар'єрного зростання."
- find: "Спочатку я хочу подати на підвищення. Я вже розмовляла з керівником про це. *(Not yet. First I want to apply for a promotion."
  replace: "Спочатку я хочу попросити про підвищення. Я вже розмовляла з керівником про це. *(Not yet. First I want to ask for a promotion."
- find: "If the masculine form ends in «-ець», the feminine form typically uses the suffix **-чиня**, transforming «продавець»"
  replace: "If the masculine form ends in «-ець», the feminine form typically uses the suffix **-ин(я)** with a consonant change, transforming «продавець»"
</fixes>