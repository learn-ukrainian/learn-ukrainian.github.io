## Linguistic Scan
- **Critical terminology error:** "Маскулінітиви" and "фемінітиви" are used to refer to masculine and feminine noun grammatical genders. In Ukrainian grammar, these terms refer specifically to nouns denoting male or female persons (e.g., professions like *директор* vs. *директорка*). The correct grammatical terms for inanimate objects are "іменники чоловічого роду" and "іменники жіночого роду".
- **Critical semantic error in contrasts:** The repetitive use of "Тут є [Nominative]" to set up the left side of a contrast is highly unnatural, and in some cases, nonsensical. For example, "Тут є час" (There is time here) or "Тут є мама" (There is a mom here) are calques of English existential phrasing that break Ukrainian semantic logic. The left side of the contrast must match the contextual placement of the right side (e.g., "У мене є час. — У мене немає часу").

## Exercise Check
- The first marker `<!-- INJECT_ACTIVITY: quiz... -->` correctly includes the `8 items` parameter.
- The remaining four `<!-- INJECT_ACTIVITY... -->` markers are missing the item counts specified in the plan (8, 8, 8, and 6 respectively).
- The exercises directly test the taught grammatical concepts and logically match the `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The module fails the word target severely (3447 words vs 2000 target; >70% over budget). It also fails the explicitly stated plan requirement to "Provide clear charts" for the Genitive singular endings, providing only text explanations. |
| 2. Linguistic accuracy | 5/10 | Incorrect grammatical terminology ("Яке закінчення мають маскулінітиви..." and "Що відбувається з закінченням фемінітивів..."). Unnatural and broken semantic setups for contrasts throughout the lesson (e.g., "Тут є час", "Тут є мама", "Тут є Марія"). |
| 3. Pedagogical quality | 6/10 | The rigid "Тут є [X]" formula used to set up Genitive contrasts creates completely disconnected sentences (e.g., "Тут є новий комп'ютер. — У школі немає комп'ютера."). The premise of the contrast is pedagogically confusing because the context does not match. |
| 4. Vocabulary coverage | 8/10 | Required words are all present, but the recommended words `відсутність` and `кількість` are completely absent from the Ukrainian text. |
| 5. Exercise quality | 7/10 | Missing item counts on the injected activity markers, failing to perfectly mirror the `activity_hints` structure. |
| 6. Engagement & tone | 6/10 | Deducting for heavy meta-commentary and "telling instead of showing": "Now you can combine everything you have learned in this module to create much richer and more complex descriptions." |
| 7. Structural integrity | 6/10 | Massively over the word budget. Activity tags lack required parameters, meaning the downstream injection might fail or default incorrectly. |
| 8. Cultural accuracy | 10/10 | Good use of realistic everyday contexts (moving into a new apartment, evaluating a new office). Appropriate names. |
| 9. Dialogue & conversation quality | 8/10 | Dialogues are functional, demonstrate the grammar well, and flow reasonably, though they are slightly transactional. |

## Findings
[2. Linguistic accuracy] [Critical]
Location: "Яке закінчення мають маскулінітиви, що позначають конкретні предмети..." and "Що відбувається з закінченням фемінітивів у множині..."
Issue: "Маскулінітиви" and "фемінітиви" refer to words denoting male/female persons, not grammatical gender categories for objects.
Fix: Change to "іменники чоловічого роду" and "іменники жіночого роду".

[2. Linguistic accuracy] [Critical]
Location: 22 instances of «Тут є [X]» used as the contrast anchor (e.g., "«Тут є час. — На жаль, у мене немає часу.»" and "«Тут є мама. — Вдома немає мами.»")
Issue: Using "Тут є" for abstract personal possession ("Тут є час") or for specific persons ("Тут є мама") is unnatural and semantically broken. 
Fix: Rewrite the left side of the contrasts to align contextually with the right side (e.g., "У мене є час", "Мама вдома").

[1. Plan adherence] [Major]
Location: Section 2: "Закінчення родового відмінка однини"
Issue: The plan explicitly asks to "Provide clear charts", but no charts were included.
Fix: (No inline fix provided for this as it requires formatting markdown tables from scratch. Accepting the text-only format with a penalty).

[7. Structural integrity] [Major]
Location: Entire module
Issue: The deterministic word count is 3447, missing the 2000 word target by 72%. 
Fix: (No inline fix provided for trimming 1400+ words. Accepting with a penalty).

[5. Exercise quality] [Minor]
Location: The four `<!-- INJECT_ACTIVITY: ... -->` tags at the end of the sections.
Issue: Missing the precise item counts (8, 8, 8, 6) explicitly specified in the plan's `activity_hints`.
Fix: Append the exact item counts to the injection tags.

[6. Engagement & tone] [Minor]
Location: "Now you can combine everything you have learned in this module to create much richer and more complex descriptions. You can talk about what you possess..."
Issue: Meta-commentary that breaks immersion; telling instead of showing.
Fix: Replace with a concise, direct transition sentence.

## Verdict: REVISE
The module accurately handles the mechanics and spelling of Genitive case endings, but contains a critical terminological error ("маскулінітиви/фемінітиви" applied to objects) and a systemic semantic breakdown in its contrast examples ("Тут є час"). It also significantly overshoots the targeted word budget. Targeted replacements must be applied to correct the linguistic errors and activity markers.

<fixes>
- find: "Яке закінчення мають маскулінітиви, що позначають конкретні предмети (наприклад, «стіл»)?"
  replace: "Яке закінчення мають іменники чоловічого роду, що позначають конкретні предмети (наприклад, «стіл»)?"
- find: "Що відбувається з закінченням фемінітивів у множині після слова «багато»?"
  replace: "Що відбувається з закінченням іменників жіночого роду у множині після слова «багато»?"
- find: "«Тут є брат. — У мене немає брата.» *(There is a brother here. — I have no brother.)*"
  replace: "«У мене є брат. — У мене немає брата.» *(I have a brother. — I have no brother.)*"
- find: "«Тут є син. — У нього немає сина.» *(There is a son here. — He has no son.)*"
  replace: "«У нього є син. — У нього немає сина.» *(He has a son. — He has no son.)*"
- find: "«Тут є телефон. — У мене немає телефона.» *(There is a phone here. — I have no phone.)*"
  replace: "«У мене є телефон. — У мене немає телефона.» *(I have a phone. — I have no phone.)*"
- find: "«Тут є новий комп'ютер. — У школі немає комп'ютера.» *(There is a new computer here. — There is no computer in the school.)*"
  replace: "«У школі є новий комп'ютер. — У школі немає комп'ютера.» *(There is a new computer in the school. — There is no computer in the school.)*"
- find: "«Тут є цукор. — У чаї немає цукру.» *(There is sugar here. — There is no sugar in the tea.)*"
  replace: "«У чаї є цукор. — У чаї немає цукру.» *(There is sugar in the tea. — There is no sugar in the tea.)*"
- find: "«Тут є час. — На жаль, у мене немає часу.» *(There is time here. — Unfortunately, I don't have time.)*"
  replace: "«У мене є час. — На жаль, у мене немає часу.» *(I have time. — Unfortunately, I don't have time.)*"
- find: "«Тут є великий парк. — Біля дому немає парку.» *(There is a big park here. — There is no park near the house.)*"
  replace: "«Біля дому є великий парк. — Біля дому немає парку.» *(There is a big park near the house. — There is no park near the house.)*"
- find: "«Тут є університет. — У цьому місті немає університету.» *(There is a university here. — There is no university in this city.)*"
  replace: "«У цьому місті є університет. — У цьому місті немає університету.» *(There is a university in this city. — There is no university in this city.)*"
- find: "«Тут є теплий пісок. — На пляжі немає піску.» *(There is warm sand here. — There is no sand on the beach.)*"
  replace: "«На пляжі є теплий пісок. — На пляжі немає піску.» *(There is warm sand on the beach. — There is no sand on the beach.)*"
- find: "«Тут є смачний сік. — У склянці немає соку.» *(There is tasty juice here. — There is no juice in the glass.)*"
  replace: "«У склянці є смачний сік. — У склянці немає соку.» *(There is tasty juice in the glass. — There is no juice in the glass.)*"
- find: "«Тут є мама. — Вдома немає мами.» *(There is a mom here. — Mom is not at home.)*"
  replace: "«Мама вдома. — Вдома немає мами.» *(Mom is at home. — Mom is not at home.)*"
- find: "«Тут є школа. — У селі немає школи.» *(There is a school here. — There is no school in the village.)*"
  replace: "«У селі є школа. — У селі немає школи.» *(There is a school in the village. — There is no school in the village.)*"
- find: "«Тут є цікава книга. — У бібліотеці немає книги.» *(There is an interesting book here. — There is no book in the library.)*"
  replace: "«У бібліотеці є цікава книга. — У бібліотеці немає книги.» *(There is an interesting book in the library. — There is no book in the library.)*"
- find: "«Тут є нова плита. — На кухні ще немає плити.» *(There is a new stove here. — There is no stove in the kitchen yet.)*"
  replace: "«На кухні є нова плита. — На кухні ще немає плити.» *(There is a new stove in the kitchen. — There is no stove in the kitchen yet.)*"
- find: "«Тут є чорна земля. — Тут немає землі.» *(There is black land here. — There is no land here.)*"
  replace: "«Тут родюча земля. — Тут немає землі.» *(There is fertile land here. — There is no land here.)*"
- find: "«Тут є широка вулиця. — У місті немає вулиці.» *(There is a wide street here. — There is no street in the city.)*"
  replace: "«У місті є широка вулиця. — У місті немає вулиці.» *(There is a wide street in the city. — There is no street in the city.)*"
- find: "«Тут є Марія. — Сьогодні на уроці немає Марії.» *(Maria is here. — Maria is not at the lesson today.)*"
  replace: "«Марія сьогодні на уроці. — Сьогодні на уроці немає Марії.» *(Maria is at the lesson today. — Maria is not at the lesson today.)*"
- find: "«Тут є велике вікно. — У кімнаті немає вікна.» *(There is a big window here. — There is no window in the room.)*"
  replace: "«У кімнаті є велике вікно. — У кімнаті немає вікна.» *(There is a big window in the room. — There is no window in the room.)*"
- find: "«Тут є чисте дзеркало. — У ванній немає дзеркала.» *(There is a clean mirror here. — There is no mirror in the bathroom.)*"
  replace: "«У ванній є чисте дзеркало. — У ванній немає дзеркала.» *(There is a clean mirror in the bathroom. — There is no mirror in the bathroom.)*"
- find: "«Тут є нове слово. — У тексті немає слова.» *(There is a new word here. — There is no word in the text.)*"
  replace: "«У тексті є нове слово. — У тексті немає слова.» *(There is a new word in the text. — There is no word in the text.)*"
- find: "«Тут є тепле море. — Біля міста немає моря.» *(There is a warm sea here. — There is no sea near the city.)*"
  replace: "«Біля міста є тепле море. — Біля міста немає моря.» *(There is a warm sea near the city. — There is no sea near the city.)*"
- find: "«Тут є зелене поле. — Біля лісу немає поля.» *(There is a green field here. — There is no field near the forest.)*"
  replace: "«Біля лісу є зелене поле. — Біля лісу немає поля.» *(There is a green field near the forest. — There is no field near the forest.)*"
- find: "Now you can combine everything you have learned in this module to create much richer and more complex descriptions. You can talk about what you possess, what you lack, and the exact quantities of things around you, all using the powerful Genitive case. Notice how the sentence structure allows you to contrast having an abundance of one thing with a complete lack of another."
  replace: "Зверніть увагу, як ми протиставляємо те, що маємо, тому, чого у нас немає (Notice how we contrast what we have with what we lack)."
- find: "<!-- INJECT_ACTIVITY: fill-in, Genitive Singular Formation -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in, Genitive Singular Formation, 8 items -->"
- find: "<!-- INJECT_ACTIVITY: match-up, Genitive Plural Formation with Quantity Words -->"
  replace: "<!-- INJECT_ACTIVITY: match-up, Genitive Plural Formation with Quantity Words, 8 items -->"
- find: "<!-- INJECT_ACTIVITY: match-up, Translate sentences with 'a lot of...' / 'I don't have...' -->"
  replace: "<!-- INJECT_ACTIVITY: match-up, Translate sentences with 'a lot of...' / 'I don't have...', 8 items -->"
- find: "<!-- INJECT_ACTIVITY: unjumble, Reorder words to form correct genitive phrases with немає and quantity expressions -->"
  replace: "<!-- INJECT_ACTIVITY: unjumble, Reorder words to form correct genitive phrases with немає and quantity expressions, 6 items -->"
</fixes>
