## Linguistic Scan
Linguistic errors found:
- Factual Error: "Серпень" incorrectly listed as taking the "-а" ending (it takes "-я": "серпня").
- Minor calque: "Ми маємо один великий парк" is grammatically acceptable but less natural than "У нас є...".
- Phonetic/euphony: "В нашому місті" would be better as "У нашому місті".

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz, What's the Date? (Drill) -->` matches plan and tests previous section.
- `<!-- INJECT_ACTIVITY: fill-in, Counting Objects (1, 2-4, 5+ Rule) -->` matches plan and tests previous section.
- `<!-- INJECT_ACTIVITY: match-up, Accusative to Genitive Negation -->` matches plan and tests previous section.
- `<!-- INJECT_ACTIVITY: match-up, Q&A about quantities and dates -->` matches plan and provides concluding test.
All markers are present, ordered correctly, and match the `activity_hints`. No issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Text missed the specific instruction to point out where Nom. Pl. and Gen. Sg. look similar for feminine nouns (e.g., 'сестри'). Also contradicted the plan regarding the genitive ending of 'серпень'. |
| 2. Linguistic accuracy | 7/10 | Text incorrectly claims the month 'серпень' takes the ending '-а' in the Genitive ("дванадцяте серпня"). 'Серпень' takes the standard '-я' ending (серпня). "Ми маємо" is slightly calqued; "У нас є" is more natural. |
| 3. Pedagogical quality | 8/10 | The grouping of 'чоловік' (a regular hard stem taking '-ів') under the heading "Some very common masculine words take the ending -ей or change slightly" is pedagogically confusing and incorrect. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary words (число, місяць, січень-грудень, заперечення) are naturally integrated into the text and examples. |
| 5. Exercise quality | 10/10 | All 4 required exercise markers are correctly placed, match the required types/focuses from the plan, and logically follow the taught material. |
| 6. Engagement & tone | 8/10 | Contains some unnecessary flowery meta-commentary ("special, elegant grammatical tradition", "profound expression of deep negation") instead of demonstrating the rule directly. |
| 7. Structural integrity | 8/10 | Clean markdown and all sections present. Deducting because the deterministic word count (3320 words) is massively outside the 2000 target range. |
| 8. Cultural accuracy | 10/10 | Culturally relevant dates (День Незалежності - 24 серпня) and natural situations (booking a hotel) are used appropriately. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are multi-turn, natural, and use appropriate grammatical features like the Vocative case ("Олександре"). |

## Findings

[Plan adherence] [major]
Location: "This can sometimes make them look exactly like the masculine singular!\n\n* **Одна сестра** *(One sister)* -> **Дві сестри** *(Two sisters)* -> **П'ять сестер**"
Issue: The plan explicitly required pointing out where Nominative Plural and Genitive Singular can look similar (e.g., 'сестри'). The text mentions 'сестри' but does not explicitly highlight this similarity.
Fix: Add a sentence explicitly noting that Nominative Plural and Genitive Singular often look identical for feminine nouns.

[Linguistic accuracy] [critical]
Location: "Only two months take the ending **-а**.\n\n* Листопад — **одинадцяте листопада** *(the eleventh of November)*\n* Серпень — **дванадцяте серпня** *(the twelfth of August)*"
Issue: Factual error about Ukrainian grammar. "Серпень" takes the standard "-я" ending (серпня), not "-а". The example itself ("серпня") correctly ends in "я".
Fix: Replace the text to correctly state that only "листопад" takes "-а", and note that "серпень" takes the standard "-я".

[Linguistic accuracy] [minor]
Location: "В нашому місті є багато парків. *(In our city there are many parks.)* Ми маємо один великий парк у центрі."
Issue: "Ми маємо" is grammatically correct but feels calqued from English "We have". "У нас є" is more natural. Also "В нашому" should be "У нашому" for euphony at the start of a sentence.
Fix: Change to "У нашому місті є багато парків. *(In our city there are many parks.)* У нас є один великий парк у центрі."

[Pedagogical quality] [major]
Location: "Some very common masculine words take the ending **-ей** or change slightly.\n\n* **Один день** *(One day)* -> **Два дні** *(Two days)* -> **П'ять днів** *(Five days)*\n* **Один гість** *(One guest)* -> **Три гості** *(Three guests)* -> **Десять гостей** *(Ten guests)*\n* **Один чоловік** *(One man)* -> **Два чоловіки** *(Two men)* -> **П'ять чоловіків** *(Five men)*"
Issue: "чоловік" is a regular hard-stem noun taking the standard "-ів" ending (чоловіків). Grouping it under "take the ending -ей or change slightly" is confusing and factually wrong.
Fix: Reword the introductory sentence so it accurately describes the words in the list.

[Engagement & tone] [minor]
Location: "However, Ukrainian has a special, elegant grammatical tradition for negation. When you negate a verb using the particle **не** *(not)*,"
Issue: Unnecessary flowery meta-commentary ("special, elegant grammatical tradition") that tells instead of shows.
Fix: Remove the flowery opening clause.

[Engagement & tone] [minor]
Location: "The word **немає** is itself a profound expression of deep negation, and it *always* strictly requires"
Issue: Overly dramatic corporate/marketing tone ("profound expression of deep negation").
Fix: Simplify to just state the grammatical requirement directly.

[Structural integrity] [major]
Location: "**Deterministic word count: 3320 words**"
Issue: Word count is 3320, significantly exceeding the 2000 target.
Fix: No inline fix provided; requires structural pipeline adjustment or manual reduction.

## Verdict: REVISE
The module contains a critical linguistic/factual error regarding the genitive ending of the month "серпень" (claims it takes -a, when it takes -я), which contradicts the provided examples and standard Ukrainian. There are also major pedagogical and plan adherence omissions. Revisions are required to correct these issues before publication.

<fixes>
- find: "This can sometimes make them look exactly like the masculine singular!\n\n* **Одна сестра** *(One sister)* -> **Дві сестри** *(Two sisters)* -> **П'ять сестер**"
  replace: "This can sometimes make them look exactly like the masculine singular! Note that for feminine nouns, the Nominative Plural (used with 2-4) often looks identical to the Genitive Singular (e.g., **сестри**).\n\n* **Одна сестра** *(One sister)* -> **Дві сестри** *(Two sisters)* -> **П'ять сестер**"
- find: "Only two months take the ending **-а**.\n\n* Листопад — **одинадцяте листопада** *(the eleventh of November)*\n* Серпень — **дванадцяте серпня** *(the twelfth of August)*"
  replace: "Only one month takes the ending **-а**.\n\n* Листопад — **одинадцяте листопада** *(the eleventh of November)*\n\nThe month **Серпень** *(August)* takes the standard **-я**:\n* Серпень — **дванадцяте серпня** *(the twelfth of August)*"
- find: "В нашому місті є багато парків. *(In our city there are many parks.)* Ми маємо один великий парк у центрі."
  replace: "У нашому місті є багато парків. *(In our city there are many parks.)* У нас є один великий парк у центрі."
- find: "Some very common masculine words take the ending **-ей** or change slightly.\n\n* **Один день**"
  replace: "Some very common masculine words take the ending **-ей** or have vowel changes in their root. Others are completely regular but important to memorize.\n\n* **Один день**"
- find: "However, Ukrainian has a special, elegant grammatical tradition for negation. When you negate a verb using the particle **не** *(not)*,"
  replace: "When you negate a verb using the particle **не** *(not)*,"
- find: "The word **немає** is itself a profound expression of deep negation, and it *always* strictly requires"
  replace: "The word **немає** *always* strictly requires"
</fixes>
