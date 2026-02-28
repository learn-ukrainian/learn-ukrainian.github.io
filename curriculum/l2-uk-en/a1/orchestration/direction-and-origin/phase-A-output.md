===RESEARCH_START===
# Дослідження: Direction and Origin

## State Standard Reference
§4.2.3.2: "Знахідний відмінок... Із прийменниками: в, у, на (указівка на кінцевий пункт руху або переміщення): Степан заходить у кімнату."
Alignment: This module directly addresses the A1 requirement for expressing direction (Куди?) using the Accusative case.
Note: The State Standard officially maps the Genitive case (до, з/від) to A2 (§4.2.2.2). However, teaching "Звідки?" (Where from?) and basic origin phrases is pedagogically necessary at A1 as formulaic chunks, introducing the concept before formal A2 mastery.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| іти | Very High | іти в магазин, іти на роботу |
| їхати | Very High | їхати до Києва, їхати у Львів |
| до | High (Prep) | додому, до лікаря, до друга |
| з/із | High (Prep) | з України, з дому, зі школи |

## Cultural Hooks
1. "Звідки ви?" (Where are you from?) is one of the most common icebreaker questions in Ukrainian society and fundamental for building initial rapport.
2. The Ukrainian railway network (Укрзалізниця) is deeply ingrained in daily life. Discussing motion often involves travel by train (`їхати на вокзал` / `до Києва`).

## Common Learner Errors
1. "Де" vs "Куди" confusion → `Я іду в школі` (Incorrect Locative) instead of `Я іду в школу` (Correct Accusative). English uses "in" for both, causing heavy interference.
2. Overusing `до` for all "to" directions → `Я іду до школу` instead of `Я іду в школу`. Learners directly translate the English "to" as `до`.
3. Imperial framing → using the colonial `на Україну` instead of the correct, sovereign `в Україну` / `з України`.

## Cross-References
- Builds on: a1-34 (Checkpoint Cases)
- Prepares for: a1-36 (Yesterday - Past Tense)

## Notes for Content Writing
- A1 Level requires heavy English scaffolding (10-50% immersion). Introduce all grammar concepts in English before providing Ukrainian examples.
- Emphasize decolonized language: explicitly teach `в Україну` (into the state) and `з України` (from the state).
- Keep sentences short (max 8-10 words). Use IPA only for the first occurrence of new words.
===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Куди? + Знахідний"
    words: 500
    points:
      - "Note for author: Use English scaffolding for all grammar rules and explanations (A1 requirement: 10-50% immersion)."
      - "Introduce the concept of direction vs. location: contrast the question 'Куди?' (Where to?) with 'Де?' (Where at?)."
      - "Provide the primary rule for direction: Verbs of motion (іти, їхати) + prepositions 'в/у' or 'на' + Accusative case."
      - "Explain Accusative case changes for inanimate nouns: masculine remains the same as dictionary form, feminine '-а/-я' changes to '-у/-ю'. Each rule gets a clear H3 subsection."
      - "Provide contrasting examples to prevent common errors (e.g., 'в магазині' vs 'в магазин')."
      - "Include a strict decolonization note in English: always use 'в Україну' (into the sovereign state), never the imperial 'на Україну'."
  - section: "До + Родовий"
    words: 400
    points:
      - "Introduce the preposition 'до' (to/towards) and explicitly state it requires the Genitive case, using English explanations."
      - "Explain the semantic usage of 'до': going to see a person (до лікаря, до друга) or approaching a boundary/city (до Києва)."
      - "Create a distinct H3 to contrast 'в/у' (entering inside a building, like 'в лікарню') vs 'до' (going to a person, like 'до лікаря')."
      - "Provide a brief, simplified overview of Genitive endings for the core examples used here (masculine '-а/-я', feminine '-и/-і') so learners can recognize the pattern."
  - section: "Звідки? + Родовий"
    words: 400
    points:
      - "Introduce the question 'Звідки?' (Where from?) using English scaffolding."
      - "Explain the prepositions 'з / із / зі' + Genitive case for spatial origin (e.g., 'з України', 'зі Львова'). Reiterate the decolonized 'з України'."
      - "Explain the preposition 'від' + Genitive for origin related to a person (e.g., returning 'від лікаря', a gift 'від мами')."
      - "Dedicate a subsection to the basic phonetic/euphony rules for choosing between 'з', 'із', and 'зі' to sound natural."
  - section: "Три питання"
    words: 400
    points:
      - "Present the unified spatial paradigm connecting what they've learned: Де? (Location) → Куди? (Destination) → Звідки? (Origin)."
      - "Include a comprehensive summary table showing parallel phrases for the same root concept (e.g., в школі / в школу / зі школи)."
      - "Demonstrate the paradigm with multiple noun types: a building (школа), an event (робота), a person (лікар), and a country (Україна)."
  - section: "Практика"
    words: 300
    points:
      - "Provide 2-3 short, realistic mini-dialogues reflecting daily movement and travel (e.g., meeting at the train station, asking where someone is from)."
      - "Include guided transformation examples: show a location sentence and walk the learner through producing its direction and origin equivalents."
      - "Ensure all examples and dialogues have side-by-side English translations to maintain the A1 safe-harbor approach."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Full Phase A
**Friction Type**: STATE_STANDARD_NOT_FOUND
**Raw Error**: None
**Self-Correction**: The Genitive case for direction and origin (Звідки?, до, з/від) is formally introduced in the A2 State Standard mapping, not A1. I noted this pedagogical discrepancy honestly in the research block while aligning the Accusative "Куди?" with the exact A1 §4.2.3.2 reference. I bypassed using grep_search due to the known `--threads` flag issue and utilized `run_shell_command` with `rg` to confirm.
**Proposed Tooling Fix**: Fix the `grep_search` tool configuration to not pass conflicting `--threads` arguments.
===FRICTION_END===
