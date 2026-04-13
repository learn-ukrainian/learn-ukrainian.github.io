## Linguistic Scan
- Factually overbroad grammar claim in **Транспорт (Transport Types)**: `"This prepositional pattern is strictly used for indeclinable nouns and for the word for car."` That is too absolute. The repo’s own grammar guidance contrasts standard neutral `автобусом` with colloquial `на автобусі`, so `strictly` teaches the rule too rigidly.

## Exercise Check
- Found 4 markers total, matching the 4 `activity_hints` in the plan.
- `quiz-which-transport` appears after the transport-vocabulary section.
- `quiz-instrumental-or-locative` appears after the transport-pattern explanation.
- `fill-in-buy-ticket` appears after the ticket-buying language.
- `fill-in-ask-directions` appears after the directions phrases.
- Marker spread is good and not clustered at the end.
- No exercise-logic errors are visible from the prose alone; the actual YAML items are not shown here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned H2 sections are present, but the source-of-truth dialogue situation “from Kyiv airport (Бориспіль) to the hotel” is only teased in English: “arrived at the Boryspil airport… hotel,” then the actual dialogue switches to `Як дістатися до вокзалу?`. |
| 2. Linguistic accuracy | 7/10 | Core Ukrainian forms are valid, but the rule “This prepositional pattern is strictly used for indeclinable nouns and for the word for car” is too absolute for actual usage. |
| 3. Pedagogical quality | 5/10 | The module spends too much time in English meta-explanation: “In the Ukrainian language, verbs of motion are highly specific and descriptive…” before returning to simple chunks. It also uses `О котрій відправлення?`, where `відправлення` is B1-level vocabulary in a core A1 ticket dialogue. |
| 4. Vocabulary coverage | 8/10 | Required plan vocabulary is present: `автобус`, `метро`, `таксі`, `потяг`, `квиток`, `зупинка`. Recommended items also appear (`трамвай`, `маршрутка`, `літак`, `прямо`, `направо`, `наліво`), though some are introduced as lists rather than lived situations. |
| 5. Exercise quality | 9/10 | All 4 planned marker types are present, correctly ordered after teaching, and evenly distributed. |
| 6. Engagement & tone | 5/10 | Too much generic filler: “This short exchange introduces several vital pieces of information” and “Practice saying them aloud multiple times until they feel completely natural to you.” The tone is teacherly, but padded. |
| 7. Structural integrity | 10/10 | Clean markdown, all planned H2 headings present, markers intact, and pipeline word count is 1270, which is above the 1200 target. |
| 8. Cultural accuracy | 6/10 | `На здоров'я!` is a poor etiquette model in a directions dialogue after `Дякую!`; project pedagogy guidance for A1 politeness models `Будь ласка` / `Про́шу` instead. |
| 9. Dialogue & conversation quality | 6/10 | The dialogues are functional but thin. They are mostly transactional and do not develop the planned airport-to-hotel scenario or distinct speaker voices. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Imagine you have just arrived at the Boryspil airport outside of Kyiv, and you need to navigate to your hotel in the city center.`  
Issue: The plan’s airport-to-hotel scenario is only mentioned in English and never turned into actual Ukrainian teaching material; the first real dialogue instead goes to `вокзал`.  
Fix: Rewrite the opening so it explicitly teaches the airport/hotel scenario with Ukrainian chunks such as `як дістатися до готелю?` and transport options.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `This prepositional pattern is strictly used for indeclinable nouns and for the word for car.`  
Issue: This states a pedagogical shortcut as a categorical grammar fact. Standard neutral Ukrainian prefers `автобусом`, but `strictly` is too absolute.  
Fix: Soften the rule: present `на метро / на таксі / на машині` as the chunks for this module, not as an exceptionless rule of the language.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `> **Приїжджий:** О котрій відправлення? *(At what time is the departure?)*`  
Issue: `відправлення` is too advanced for a core A1 transactional line; it raises lexical difficulty where the module should stay chunk-based and communicative.  
Fix: Replace it with a simpler A1 question such as `Коли потяг до Львова?`

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `In the Ukrainian language, verbs of motion are highly specific and descriptive... which simply changes the ending of the noun to mean "by means of."`  
Issue: This is a long English theory block for A1. The module should teach chunks first, not lecture about the system.  
Fix: Replace the paragraph with a short chunk-first explanation: `іти` on foot, `їхати` by transport, then examples.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: `> **Друг:** На здоров'я! *(You are welcome!)*`  
Issue: This is the wrong etiquette model for a basic directions exchange after `Дякую!` in this curriculum.  
Fix: Replace it with `Будь ласка!` or `Прошу!`

## Verdict: REVISE
The module has multiple fixable issues, including one critical language-teaching issue (`strictly used`) and several major pedagogy/cultural problems. It is not a full rewrite, but it should not pass as-is.

<fixes>
- find: "Imagine you have just arrived at the Boryspil airport outside of Kyiv, and you need to navigate to your hotel in the city center. Or perhaps you want to visit a friend across town. To use transport in Ukrainian, you need a few core skills: ask for directions, find the stop, and buy a ticket."
  replace: "Imagine you have just arrived at Boryspil airport outside Kyiv and need to get to your hotel in the city center. In Ukrainian, you need a few core skills: ask **як дістатися до готелю?** (how to get to the hotel), find the stop, and choose transport such as **автобусом**, **на метро**, or **на таксі**."
- find: "> **Друг:** На здоров'я! *(You are welcome!)*"
  replace: "> **Друг:** Будь ласка! *(You are welcome!)*"
- find: "In the Ukrainian language, verbs of motion are highly specific and descriptive. While English uses the general verb \"to go\" for almost everything, Ukrainian strictly separates walking from riding. You must use the verb **іти** (to go on foot) when walking, but you must use the verb **їхати** (to go by vehicle) whenever you use any form of transport. When stating the exact method of transport, Ukrainian uses two distinct patterns. The first pattern uses the instrumental case chunk, which simply changes the ending of the noun to mean \"by means of.\""
  replace: "Ukrainian distinguishes walking from transport. Use **іти** (to go on foot) when you walk, and use **їхати** (to go by vehicle) when you travel by transport. Then learn the transport phrase as a chunk. The first common pattern uses the instrumental case:"
- find: "The second pattern uses the preposition **на** (on / at) followed by the locative case chunk. This prepositional pattern is strictly used for indeclinable nouns and for the word for car. Because indeclinable nouns cannot change their endings, they simply follow the preposition without any modification."
  replace: "The second common pattern uses the preposition **на** followed by the locative chunk. In this module, learn it with indeclinable nouns such as **метро** and **таксі**, and with **машина**. For standard neutral Ukrainian, transport as a means is often expressed with the instrumental, so treat these combinations as fixed chunks."
- find: "> **Приїжджий:** О котрій відправлення? *(At what time is the departure?)*"
  replace: "> **Приїжджий:** Коли потяг до Львова? *(When is the train to Lviv?)*"
- find: "The second pattern requires the preposition **на** for indeclinable nouns and cars, resulting in phrases like **на метро** (by metro) or **на машині** (by car)."
  replace: "The second pattern in this module uses **на** with fixed chunks such as **на метро** (by metro), **на таксі** (by taxi), or **на машині** (by car)."
</fixes>