===RESEARCH_START===

# Дослідження: Giving Directions

## State Standard Reference
§3.5. Середовище перебування (місто чи село): "громадський транспорт; туристичні принади (цікаві місця й культурні пам’ятки); напрямок руху (прямо, ліворуч, праворуч)."
§4.4.1.3. Спонукальне речення: "вираження розпорядження, прохання, поради, пропозиції (Дайте, будь ласка...)"
Alignment: This module directly fulfills the A2 thematic requirement for navigating urban environments and direction of movement (§3.5), while introducing imperative structures for giving instructions (§4.4.1.3) and motion/location case government.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| іти / їхати | Core A2 verbs | іти пішки, їхати на метро |
| прямо | High | йдіть прямо |
| ліворуч / наліво | High | поверніть ліворуч |
| праворуч / направо | High | поверніть праворуч |
| перехрестя | Medium | на перехресті, до перехрестя |
| пройти | High (navigation) | як пройти до...? |

## Cultural Hooks
1. **Метро «Арсенальна» (Kyiv)**: The deepest metro station in the world (105.5 meters). The escalator ride takes about 5 minutes, making it a common landmark and meeting point («зустрінемось на Арсенальній»).
2. **Площа Ринок (Lviv)**: Navigation via the four mythological fountains (Neptune, Diana, Amphitrite, Adonis) located at the corners of the square, commonly used by locals for orientation («біля Нептуна», «біля Діани»).

## Common Learner Errors
1. **Adjective vs. Adverb** → *Ідіть ліворуч*, not *Ідіть лівий*. English uses "left/right" as both adjectives and adverbs. Ukrainian strictly separates them; directions require the adverbs (ліворуч/наліво).
2. **Motion Verb Conflation** → *Я їду на метро*, not *Я йду на метро*. English "to go" covers both. Ukrainian strictly requires `їхати` for vehicular transport and `іти` for foot travel.
3. **Preposition Government** → *До парку*, not *До парк*. Forgetting that the preposition «до» demands the Genitive case.

## Cross-References
- Builds on: a2-64 (Scheduling Interviews)
- Prepares for: a2-66 (Asking for Directions)

## Notes for Content Writing
- **Decolonized Framing**: Explain the `іти/їхати` distinction as a precise Ukrainian feature that describes physical reality, rather than comparing it to the Russian system. Emphasize the semantic logic of Ukrainian.
- **Immersion Band 3**: English should be restricted primarily to the vocabulary translation columns. Explanations and prose must be near-full Ukrainian. Use clear, simple Ukrainian sentences for grammar rules.
- **Vowels**: Ensure IPA markings use [ɔ] for 'о', [ɛ] for 'е'.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ"
    words: 500
    points:
      - "Introduce the topic in Ukrainian, setting the scene of navigating a bustling Ukrainian city."
      - "Present standard urban vocabulary (вулиця, площа, перехрестя) with short definitions in Ukrainian."
      - "Integrate the cultural hook of Kyiv's 'Arsenalna' metro station as a unique navigation milestone."
      - "Integrate the cultural hook of Lviv's Rynok Square and its four mythological fountains used for orientation."
  - section: "Презентація"
    words: 800
    points:
      - "Teach the standard phrase «Вибачте, як пройти до...?» focusing on the verb «пройти»."
      - "Present directional adverbs (прямо, ліворуч/наліво, праворуч/направо) using simple Ukrainian explanations and visual text cues."
      - "Address the common error of using adjectives (лівий/правий) instead of adverbs for movement direction."
      - "Introduce the strict semantic distinction between «іти» (on foot) and «їхати» (by vehicle)."
      - "Explain the formation of basic imperative verbs for instructions (ідіть, поверніть, пройдіть)."
  - section: "Практика"
    words: 700
    points:
      - "Provide a structured exercise focusing on choosing the correct directional adverb over the adjective form."
      - "Include a drill contrasting the use of «іти» vs. «їхати» based on different modes of transport (пішки, на метро, на автобусі)."
      - "Present step-by-step navigation sequences (e.g., «пройдіть два квартали, потім поверніть...») to consolidate the imperative forms."
  - section: "Діалоги"
    words: 600
    points:
      - "Provide a dialogue modeling movement prepositions («в/на» + Accusative) versus static location («біля/навпроти» + Genitive)."
      - "Specifically demonstrate and reinforce the use of the Genitive case after the preposition «до»."
      - "Include iconic route dialogues featuring real landmarks (e.g., from a metro station to a museum) using sequencing markers (спочатку, потім)."
  - section: "Розповідь"
    words: 400
    points:
      - "Write a short narrative story about a character navigating from a train station to a destination in Lviv or Kyiv."
      - "Integrate environmental vocabulary naturally (через міст, на світлофорі, наступна зупинка)."
      - "Conclude with a summary contrasting the questions «куди?» (motion) and «де?» (static location)."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Searching State Standard mapping
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: grep_search failed with "error: The argument '--threads <NUM>' requires 1 values, but 2 were provided"
**Self-Correction**: Switched from the broken grep_search MCP tool to using run_shell_command with standard text manipulation utilities (sed) to read the exact lines of the State Standard file referenced by the mapping file.
**Proposed Tooling Fix**: The underlying ripgrep wrapper for `grep_search` appears to inject an extra or malformed `--threads` argument on macOS/darwin. Avoid `grep_search` entirely and use native `rg` via shell commands.
===FRICTION_END===
