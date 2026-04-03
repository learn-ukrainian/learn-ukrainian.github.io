## Linguistic Scan
No general linguistic errors found (vocabulary exists in VESUM and is used naturally), but two grammatical mislabeling errors were found in the explanations (`до центру` as accusative and `на метро` as locative).

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-directions -->` is present and logically tests direction phrases.
- `<!-- INJECT_ACTIVITY: quiz-de-kudy -->` is present and tests locative vs. accusative correctly.
- `<!-- INJECT_ACTIVITY: fill-in-transport -->` is present and tests transport means.
- `<!-- INJECT_ACTIVITY: match-navigation -->` is present and serves as an excellent wrap-up.
All placeholders match the plan's hints in type, focus, and count.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The writer followed the `content_outline` perfectly, but missed the `dialogue_situations` instruction to include Lviv landmarks (Площа Ринок, Оперний театр, Високий замок). |
| 2. Linguistic accuracy | 7/10 | The text incorrectly labeled `до центру` as an accusative case construction (it is genitive with 'до'). Also, it wrongly claimed that `на метро` is used for static location, whereas `в/у метро` is the correct Ukrainian locative form. |
| 3. Pedagogical quality | 8/10 | The explanation of motion vs. location is excellent and the PPP flow is strong, but the grammatical mislabeling of `до` as accusative creates a confusing precedent for learners. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary is used in natural contexts. One recommended word, `поруч`, was absent from the generated text. |
| 5. Exercise quality | 10/10 | The four `<!-- INJECT_ACTIVITY: ... -->` markers align perfectly with the plan's hints and are placed logically after the taught concepts. |
| 6. Engagement & tone | 10/10 | The tone is excellent. The writer uses natural openers like "Navigating a Ukrainian city means juggling two questions at once" and avoids generic enthusiasm. |
| 7. Structural integrity | 10/10 | The markdown is clean, headings match the plan exactly, and the word count is 1281 words, which is within the target range. |
| 8. Cultural accuracy | 8/10 | The text places a dialogue featuring a metro ride in Lviv ("a stranger asking for help on a Lviv street... Їдьте на метро"). This is factually wrong since Lviv does not have a metro system. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are culturally appropriate and natural, featuring sequence words like "Спочатку... потім" and realistic conversational flow. |

## Findings

[Linguistic accuracy] [critical]
Location: `The destination uses accusative: **на зупинку** (to the stop), **до центру** (to the center).`
Issue: The phrase `до центру` is incorrectly labeled as an accusative construction. The preposition `до` always takes the genitive case in Ukrainian.
Fix: Add "or genitive with до" to accurately describe the grammar.

[Linguistic accuracy] [critical]
Location: `Metro always stays with **на**: **на метро** — both for location and transport.`
Issue: The text claims `на метро` is used for location. This is a factual error. In Ukrainian, `у/в метро` is used for static location ("дав концерт у метро"), while `на метро` or `метро` (instrumental) is for transport.
Fix: Correct the rule to state that location uses в/у and transport uses на.

[Cultural accuracy] [critical]
Location: `a stranger asking for help on a Lviv street` and `**Марі́я** lives in Lviv`
Issue: The text places examples featuring a metro ride in Lviv. Lviv does not have a metro.
Fix: Change the setting of these specific metro examples to Kyiv to maintain factual accuracy while preserving the transport grammar lesson.

[Plan adherence] [major]
Location: `Three example outputs for different situations: [...] - Small town: ...`
Issue: The writer missed the `dialogue_situations` instruction to include Lviv landmarks (Площа Ринок, Оперний театр, Високий замок).
Fix: Replace the "Small town" example with a "Lviv Old Town" example that includes these landmarks.

[Vocabulary coverage] [minor]
Location: Text-wide
Issue: The recommended vocabulary word `поруч` (nearby) is missing from the module.
Fix: Incorporate `поруч` into the new Lviv Old Town example to satisfy the vocabulary requirement.

## Verdict: REVISE
The module has strong pedagogical flow and excellent tone, but contains critical linguistic mislabeling (`до` as accusative, `на метро` for location) and a cultural/factual error (a metro in Lviv). These must be corrected before publishing.

<fixes>
- find: "a stranger asking for help on a Lviv street,"
  replace: "a stranger asking for help on a Kyiv street,"
- find: "The destination uses accusative: **на зупинку** (to the stop), **до центру** (to the center)."
  replace: "The destination uses accusative (**на зупинку** — to the stop) or genitive with **до** (**до центру** — to the center)."
- find: "Metro always stays with **на**: **на метро** — both for location and transport."
  replace: "Metro uses **в/у** for location (**в метро**) and **на** for transport (**на метро**)."
- find: "**Марі́я** lives in Lviv and is heading to the theater:"
  replace: "**Марі́я** lives in Kyiv and is heading to the theater:"
- find: "**Марія живе́ у Льво́ві** (де? — locative)."
  replace: "**Марія живе́ у Киє́ві** (де? — locative)."
- find: "- Small town: **Я живу у мале́нькому мі́сті. Біля мого дому є парк. Магазин близько — три хвилини пішки. У моєму районі є бібліотека, кафе і школа.**"
  replace: "- Lviv Old Town: **Я живу у Львові. Біля мого дому Площа Ринок. Оперний театр поруч — три хвилини пішки. Високий замок далеко — треба їхати автобусом.**"
</fixes>
