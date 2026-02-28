===RESEARCH_START===

# Дослідження: Direction and Origin

## State Standard Reference
§4.2.3.2: "в, у, на (указівка на кінцевий пункт руху або переміщення): Степан заходить у кімнату. Я кладу книжку на твій стіл;"
Alignment: This module addresses the A1 requirement to use the Accusative case with prepositions в/у/на to indicate direction. 
*Note:* The Genitive case for direction and origin (до, з, від) is formally cataloged under the A2 standard (§4.2.2.2), but is essential to introduce here as a lexical chunk to complete the basic spatial paradigm (Де? Куди? Звідки?).

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| іти | Very high (Core Verb) | іти в магазин, іти на роботу |
| їхати | Very high (Core Verb) | їхати до Києва, їхати у Львів |
| до | High (Preposition) | додому, до лікаря, до друга |
| з / із / зі | High (Preposition) | з України, зі Львова, із Києва |

## Cultural Hooks
1. **"В Україну" vs "На Україну"**: Asserting sovereignty. Historically, Russian imperial and Soviet sources used "на Україну" (treating it as a territory or borderland). Modern, decolonized Ukrainian standard strictly requires "в Україну" (to Ukraine) and "з України" (from Ukraine), treating it as an independent state.
2. **"Додому"**: The cultural weight of returning home. It acts as a fixed adverbial form of direction that bypasses the need for complex case endings, making it an easy, high-frequency "quick win" for learners.

## Common Learner Errors
1. **Location vs Direction (Де? vs Куди?)**: Using the Locative instead of Accusative for movement. e.g., "Я іду в школі" (incorrect) → "Я іду в школу" (correct). — *Why it happens*: Learners translate English "to/in" directly without distinguishing static position from motion.
2. **"З" vs "Від" for Origin**: e.g., "Я йду з лікаря" (incorrect) → "Я йду від лікаря" (correct). — *Why it happens*: Applying "from" uniformly. Learners must differentiate spatial origin (з/із/зі) from human source (від).
3. **Using "на" for Countries**: e.g., "Я їду на Україну" (incorrect) → "Я їду в Україну" (correct). — *Why it happens*: Echoes of Russian colonial framing.

## Cross-References
- Builds on: a1-34 (Checkpoint Cases)
- Prepares for: a1-36 (Yesterday - Past Tense)

## Notes for Content Writing
- **Scaffolding:** This is an A1 module. English scaffolding is MANDATORY for all grammar explanations before showing Ukrainian examples.
- **Decolonized Framing:** Take a brief moment to explicitly teach *why* we say "в Україну", positioning the language as a marker of identity and independence.
- **Visual Pedagogy:** Rely heavily on comparative tables to contrast "Де?" (Locative), "Куди?" (Accusative/Genitive), and "Звідки?" (Genitive) so the paradigm is visually clear.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Куди? + Знахідний"
    words: 500
    points:
      - "Note for author: Use English scaffolding for all grammar rules and explanations (A1 requirement)."
      - "Introduce the question 'Куди?' (Where to?) and contrast it with 'Де?' (Where at?)."
      - "Explain the rule for direction: verbs of motion (іти, їхати) + в/у or на + Accusative case."
      - "Detail the Accusative forms for inanimate nouns (masculine remains same, feminine -а/-я changes to -у/-ю)."
      - "Provide clear examples: Я іду в магазин, Я їду на роботу. Include a decolonization note on using 'в Україну' instead of 'на Україну'."
  - section: "До + Родовий"
    words: 400
    points:
      - "Introduce 'до' + Genitive case for direction."
      - "Explain its specific semantic use: approaching a boundary, a city, or going to see a person (до лікаря, до Києва)."
      - "Contrast with в/у: 'в лікарню' (entering the building) vs 'до лікаря' (visiting the person)."
      - "Provide a brief Genitive ending overview for the core examples used."
  - section: "Звідки? + Родовий"
    words: 400
    points:
      - "Introduce the question 'Звідки?' (Where from?)."
      - "Explain 'з / із / зі' + Genitive for spatial origin (з України, зі Львова)."
      - "Explain 'від' + Genitive for origin/returning from a person (від мами, від лікаря)."
      - "Include phonetic/euphony rules for choosing between з, із, and зі."
  - section: "Три питання"
    words: 400
    points:
      - "Present the unified spatial paradigm: Де? (Location) → Куди? (Destination) → Звідки? (Origin)."
      - "Create a comprehensive summary table showing parallel phrases: в школі / в школу / зі школи."
      - "Demonstrate with multiple noun types (a building, an event, a person, a country)."
  - section: "Практика"
    words: 300
    points:
      - "Provide simple dialogue examples reflecting real-life travel and daily movement (Куди ти йдеш? — Я на роботу)."
      - "Include guided transformation examples: taking a location and producing its direction and origin equivalents."
      - "Final summary of the key grammatical takeaways."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Tool execution (search)
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: Error during grep search operation: Process exited with code 2: error: The argument '--threads <NUM>' requires 1 values, but 2 were provided
**Self-Correction**: Used `run_shell_command` with ripgrep (`rg`) directly to bypass the bug in the `grep_search` tool wrapper, as advised by the system guidelines.
**Proposed Tooling Fix**: The Python script or MCP server wrapping the `grep_search` tool is incorrectly injecting a redundant `--threads` flag that causes ripgrep to fail. The wrapper needs to be updated to remove the duplicate argument.
===FRICTION_END===
