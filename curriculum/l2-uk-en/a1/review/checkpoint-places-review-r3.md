## Linguistic Scan
Linguistic errors found:
- Multiple violations of euphony rules (`у/в` and `і/й` alternations) in the prose, which is critical for a module reviewing euphony (e.g., "Я іду", "Метро у Києві", "я у готелі"). 

## Exercise Check
All four `<!-- INJECT_ACTIVITY: -->` markers are present, ordered correctly, and match the `activity_hints` in the plan in terms of type, focus, and count.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The text misses the plan point requiring `Потьомкінські сходи` in the final Odesa description. |
| 2. Linguistic accuracy | 6/10 | CRITICAL euphony errors: "> **Метро у Києві ду́же зру́чне.**" (after vowel, before consonant -> should be 'в'). "> **Я іду в музе́й.**" (after vowel -> should be 'йду'). "> **Увечері я у готе́лі.**" (after vowel -> should be 'в'). |
| 3. Pedagogical quality | 8/10 | Contradicting its own taught euphony rules undermines the pedagogy. Otherwise, the PPP structure is excellent. |
| 4. Vocabulary coverage | 9/10 | Misses `сходи` (Potemkin Stairs) which was explicitly requested in the plan for the final section. |
| 5. Exercise quality | 10/10 | Activities perfectly match the plan and test what was just taught. |
| 6. Engagement & tone | 9/10 | Natural dialogue, good situational framing. The introductory paragraph is slightly meta. |
| 7. Structural integrity | 9/10 | Word count (1561) is over 30% higher than the plan target (1200), though markdown is clean and H2 headers are correct. |
| 8. Cultural accuracy | 9/10 | "> — **Оксана:** Кафе на площі Незале́жності. Це одна́ зупинка на метро." - Independence Square is not one stop from Arsenalna on the same line (requires transfer or walking from Khreshchatyk). |
| 9. Dialogue & conversation quality | 10/10 | The conversation with the local in Kyiv is realistic, natural, and integrates all cases smoothly. |

## Findings
[1. Plan adherence] [major]
Location: `Now try it yourself. Imagine you're video-calling a friend while walking through Одеса (Odesa). Describe what you see:`
Issue: The plan explicitly required `showing: ... Потьомкінські сходи (pl, Potemkin Stairs)`. This vocabulary item is missing from the bullet points.
Fix: Add `- **Бачу Потьо́мкінські схо́ди.** (I see the Potemkin Stairs.)` to the list.

[2. Linguistic accuracy] [critical]
Location: `> **Зараз я у Києві.** *(Right now I'm in Kyiv.)*` and `**«Я зараз у Києві! Хочу їхати у Львів!»**`
Issue: Euphony violation. After a vowel ("я") and before a consonant ("К"), "в" must be used instead of "у".
Fix: Change to `**Зараз я в Києві.**`

[2. Linguistic accuracy] [critical]
Location: `**Метро у Києві ду́же зру́чне.** *(The metro in Kyiv is very convenient.)*`
Issue: Euphony violation. After a vowel ("о") and before a consonant ("К"), "в" must be used.
Fix: Change to `**Метро в Києві ду́же зру́чне.**`

[2. Linguistic accuracy] [critical]
Location: `> **Я іду в музе́й.** *(I go to the museum.)*`
Issue: Euphony violation. After a vowel ("Я"), the form `йду` must be used instead of `іду`.
Fix: Change to `> **Я йду в музе́й.** *(I go to the museum.)*`

[2. Linguistic accuracy] [critical]
Location: `> **Увечері я у готе́лі.** *(In the evening I'm at the hotel.)*`
Issue: Euphony violation. After a vowel ("я") and before a consonant ("г"), "в" must be used.
Fix: Change to `> **Увечері я в готе́лі.** *(In the evening I'm at the hotel.)*`

[2. Linguistic accuracy] [critical]
Location: `- **В парку.** (In the park.)`
Issue: Euphony violation. At the start of an isolated phrase or sentence before a consonant, "У" is standard.
Fix: Change to `- **У парку.** (In the park.)`

[8. Cultural accuracy] [minor]
Location: `> — **Оксана:** Кафе на площі Незале́жності. Це одна́ зупинка на метро.`
Issue: From Arsenalna station, Maidan Nezalezhnosti is not one stop (it requires a transfer to the Blue line). Khreshchatyk is one stop away.
Fix: Change the location to `на Хреща́тику`.

## Verdict: REVISE
The module contains multiple CRITICAL euphony errors (у/в, і/й) in the prose, which is unacceptable for a lesson that explicitly teaches and tests these very rules. A minor factual error regarding the Kyiv metro system and a missing vocabulary requirement (Потьомкінські сходи) must also be fixed.

<fixes>
- find: "**Зараз я у Києві.** *(Right now I'm in Kyiv.)*"
  replace: "**Зараз я в Києві.** *(Right now I'm in Kyiv.)*"
- find: "**«Я зараз у Києві! Хочу їхати у Львів!»** *(\"I'm in Kyiv now! I want to go to Lviv!\")*"
  replace: "**«Я зараз в Києві! Хочу їхати у Львів!»** *(\"I'm in Kyiv now! I want to go to Lviv!\")*"
- find: "**Метро у Києві ду́же зру́чне.** *(The metro in Kyiv is very convenient.)*"
  replace: "**Метро в Києві ду́же зру́чне.** *(The metro in Kyiv is very convenient.)*"
- find: "> **Я іду в музе́й.** *(I go to the museum.)*"
  replace: "> **Я йду в музе́й.** *(I go to the museum.)*"
- find: "> **Увечері я у готе́лі.** *(In the evening I'm at the hotel.)*"
  replace: "> **Увечері я в готе́лі.** *(In the evening I'm at the hotel.)*"
- find: "**В парку.** (In the park.)"
  replace: "**У парку.** (In the park.)"
- find: "> — **Оксана:** Кафе на площі Незале́жності. Це одна́ зупинка на метро. *(There's a café at Independence Square. It's one metro stop.)*"
  replace: "> — **Оксана:** Кафе на Хреща́тику. Це одна́ зупинка на метро. *(There's a café on Khreshchatyk. It's one metro stop.)*"
- find: "- **Іду до по́рту.** (I'm heading to the port.)\n- **Потім хочу на пляж.** (Then I want to go to the beach.)"
  replace: "- **Іду до по́рту.** (I'm heading to the port.)\n- **Бачу Потьо́мкінські схо́ди.** (I see the Potemkin Stairs.)\n- **Потім хочу на пляж.** (Then I want to go to the beach.)"
</fixes>
