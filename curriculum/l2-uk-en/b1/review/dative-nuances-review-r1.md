## Linguistic Scan
Errors found:
1. **Russianism/Calque**: The construction "Давайте" + verb is used 9 times (e.g., "Давайте поговоримо", "Давайте порівняємо"). This is a direct calque from Russian ("давайте поговорим"). Ukrainian requires the synthetic imperative form (Поговорімо, Порівняймо, Зайдімо).
2. **Russianism/Calque**: The word "підтримуючим" (active present participle) is used unnaturally as an adjective: "Цей тон є дуже м'яким, підтримуючим і ненав'язливим".
3. **Non-existent word / Grammar error**: The text lists "навсупроти" as a preposition that takes the Dative case for "contrary to". "Навсупроти" does not exist in VESUM or СУМ-11. The correct preposition taking the Dative case for "contrary to" is "всупереч". 

## Exercise Check
- `<!-- INJECT_ACTIVITY: reading -->` (Matches plan: reading)
- `<!-- INJECT_ACTIVITY: fill-in -->` (Matches plan: fill-in)
- `<!-- INJECT_ACTIVITY: essay-age-practice -->` (Matches plan: essay-response)
- `<!-- INJECT_ACTIVITY: match-age-terms -->` (Matches plan: match-up)
- `<!-- INJECT_ACTIVITY: quiz-impersonal-logic -->` (Matches plan: quiz)
- `<!-- INJECT_ACTIVITY: dialogue-dative-advice -->` (Issue: The `dialogue` prefix does not match any valid type in the plan's `activity_hints`.)
- `<!-- INJECT_ACTIVITY: fill-in-dative-of-purpose-and-prepositions -->` (Matches plan: fill-in)
- `<!-- INJECT_ACTIVITY: error-case-governance -->` (Matches plan: error-correction)

*There are 8 markers total, which is good for density, but one uses an unsupported prefix.*

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Covered most points well, but missed two specific elements: 1) The reading passage ("Зранку мені було холодно...") from Section 1 was omitted. 2) The grammatical contrast between "Гімн волі" (Genitive) and "Гімн свободі" (Dative) from Section 5 was missing. |
| 2. Linguistic accuracy | 6/10 | Found multiple critical linguistic errors: 1) "Давайте" + verb used 9 times instead of proper imperatives. 2) "підтримуючим" used as a participle-adjective. 3) The non-existent word "навсупроти" used instead of "всупереч". |
| 3. Pedagogical quality | 10/10 | Outstanding flow. Grammar rules are explained clearly, not just listed. Excellent contrast with English logic ("I am thirty" vs "Мені тридцять") and good use of impersonal logic. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items from the plan are naturally embedded into the prose and dialogue. |
| 5. Exercise quality | 9/10 | Markers are placed logically after their respective sections. However, the marker `<!-- INJECT_ACTIVITY: dialogue-dative-advice -->` uses an activity type `dialogue` which is not present in the plan's `activity_hints`. |
| 6. Engagement & tone | 9/10 | The tone is appropriately supportive and engaging. Mild deduction for the repetitive use of the non-standard "Давайте" opener, but the persona is otherwise excellent. |
| 7. Structural integrity | 10/10 | Word count is 5486, well over the 4000 target. All required H2 headings are present and properly formatted. |
| 8. Cultural accuracy | 10/10 | Excellent decolonized approach. References to Khreshchatyk, Ukrainian perspectives on age, and the distinction between "дякувати" vs "благодарить" show strong cultural awareness. |
| 9. Dialogue & conversation quality | 10/10 | Conversations are natural and contextualized. The family walking on Khreshchatyk and the friends discussing stress are believable, multi-turn exchanges with named speakers. |

## Findings
[Plan adherence] [Major]
Location: Section 1 (Давальний суб'єкта стану), before the dialogue.
Issue: The plan explicitly required a reading passage ("Зранку мені було холодно. Потім стало веселіше...") for learners to identify dative constructions. This was omitted.
Fix: Insert the reading passage before the dialogue scenario.

[Plan adherence] [Major]
Location: Section 5 (Давальний мети і призначення), "напис: «Присвята моїм дорогим вчителям» *(A dedication to my dear teachers)*."
Issue: The plan required noting the difference between "Гімн волі" (Genitive) and "Гімн свободі" (Dative). This was omitted.
Fix: Insert an explanation of "гімн волі" vs "гімн свободі" right after the dedication example.

[Linguistic accuracy] [Critical]
Location: Throughout the text (9 instances, e.g., "Давайте поговоримо", "Давайте порівняємо", "Давайте зайдемо")
Issue: The construction "Давайте" + verb is a Russianism/calque when used to form the imperative. Proper Ukrainian uses synthetic imperative forms (-імо, -ймо).
Fix: Replace all instances with the correct imperative forms (Поговорімо, Порівняймо, Зайдімо, etc.).

[Linguistic accuracy] [Critical]
Location: Section 4 (Давальний адресата і зацікавленої особи), "Цей тон є дуже м'яким, підтримуючим і ненав'язливим."
Issue: "Підтримуючим" is an active present participle (-учий/-ючий) used unnaturally as an adjective, which is a calque from Russian.
Fix: Replace with "турботливим".

[Linguistic accuracy] [Critical]
Location: Section 5 (Давальний мети і призначення), "«напереріз» *(across / intercepting)*, «навсупроти» *(contrary to)*, та «на зло» *(to spite)*."
Issue: "навсупроти" does not exist in standard dictionaries (VESUM/SUM-11) and "навпроти" takes the Genitive. The correct preposition for "contrary to" with the Dative case is "всупереч".
Fix: Replace "навсупроти" with "всупереч".

[Exercise quality] [Minor]
Location: Section 4 (Давальний адресата і зацікавленої особи), "<!-- INJECT_ACTIVITY: dialogue-dative-advice -->"
Issue: The marker uses the prefix `dialogue`, which is not listed in the plan's `activity_hints`. This may cause the pipeline to fail to find a matching exercise generator template.
Fix: Change the marker to `fill-in-dative-advice`.

## Verdict: REVISE
The text is pedagogically very strong and hits the word count easily, but it contains multiple critical linguistic errors (Russianisms like "Давайте" + verb, "підтримуючим", and the non-existent word "навсупроти") and missed two specific required plan points. These must be fixed deterministically before the module can be published. 

<fixes>
- find: "Давайте поговоримо про одну з"
  replace: "Поговорімо про одну з"
- find: "Давайте порівняємо дві конструкції."
  replace: "Порівняймо дві конструкції."
- find: "Давайте подивимося, як ці конструкції працюють у реальному житті. Уявіть холодний зимовий день"
  replace: "Прочитайте короткий уривок, де герой описує свій день через стани: «Зранку мені було холодно. Потім стало веселіше. Увечері мені не спалося, і я читав книжку». Спробуйте знайти тут усі давальні конструкції. А тепер подивімося, як ці конструкції працюють у реальному житті. Уявіть холодний зимовий день"
- find: "Давайте зайдемо в кафе,"
  replace: "Зайдімо в кафе,"
- find: "Давайте детально згадаємо правила"
  replace: "Детально згадаймо правила"
- find: "Давайте детальніше проаналізуємо, чому українці"
  replace: "Детальніше проаналізуймо, чому українці"
- find: "Щоб краще відчути цю зміну тону, давайте проаналізуємо кілька пар"
  replace: "Щоб краще відчути цю зміну тону, проаналізуймо кілька пар"
- find: "Давайте уважно подивимося, як усе це працює"
  replace: "Уважно подивімося, як усе це працює"
- find: "Давайте коротко підсумуємо п'ять головних"
  replace: "Коротко підсумуймо п'ять головних"
- find: "напис: «Присвята моїм дорогим вчителям» *(A dedication to my dear teachers)*."
  replace: "напис: «Присвята моїм дорогим вчителям» *(A dedication to my dear teachers)*. Зверніть увагу на різницю між виразами «гімн волі» та «гімн свободі». У першому випадку використовується родовий відмінок, а в другому — давальний для позначення присвяти."
- find: "Цей тон є дуже м'яким, підтримуючим і ненав'язливим."
  replace: "Цей тон є дуже м'яким, турботливим і ненав'язливим."
- find: "«напереріз» *(across / intercepting)*, «навсупроти» *(contrary to)*, та «на зло»"
  replace: "«напереріз» *(across / intercepting)*, «всупереч» *(contrary to)*, та «на зло»"
- find: "<!-- INJECT_ACTIVITY: dialogue-dative-advice -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-dative-advice -->"
</fixes>
