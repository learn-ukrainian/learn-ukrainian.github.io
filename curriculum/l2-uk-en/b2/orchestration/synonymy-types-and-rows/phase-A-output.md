===RESEARCH_START===

# Дослідження: Синонімія: типи та синонімічні ряди

## State Standard Reference
§4.4.1.2: "Стилістичні засоби лексики: ... синоніми: говорити, розмовляти, спілкуватися;"
Alignment: This module fulfills the B2 linguistic competence requirement to understand and deploy stylistic lexical devices, specifically mastering synonymy to vary expression and match appropriate registers.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| синонім | High / Academic | абсолютний синонім, контекстуальний синонім |
| синонімічний ряд | Medium / Lexicology | побудувати синонімічний ряд, члени ряду |
| домінанта | Medium / Specialized | домінанта ряду, визначити домінанту |
| відтінок значення | High / General | тонкі відтінки, семантичний відтінок |

## Cultural Hooks
1. **Record-breaking Rows**: The Ukrainian verb "бити" (to beat) holds the record for the most synonyms, with 45 distinct words (e.g., лупцювати, товкти, дубасити, гамселити) listed in the Short Dictionary of Synonyms, showcasing the language's immense expressive capacity and nuance.
2. **Lexical Richness**: The comprehensive "Словник синонімів української мови" contains over 17,000 synonymic rows. This is a point of national pride that highlights the emotional and melodic depth (милозвучність) of Ukrainian independently of any imperial narratives.

## Common Learner Errors
1. **Paronym Confusion** → Mixing up synonyms with paronyms (words that sound similar but mean different things, e.g., адрес [greeting] vs. адреса [location]; військовий [person/military] vs. воєнний [related to war]).
2. **Register Mismatch** → Treating all synonyms in a row as perfectly interchangeable without recognizing their stylistic or emotional coloration (e.g., using a colloquial word like "пика" instead of the neutral "обличчя" in a formal context).

## Cross-References
- Builds on: b2-53 (Checkpoint Morphology)
- Prepares for: b2-55 (Synonymy in Registers)

## Notes for Content Writing
- **Decolonization**: Frame the Ukrainian lexical system as an independent, rich entity. Do not benchmark against Russian. If comparing syntax or semantic shifts, use other European languages or rely purely on internal Ukrainian logic.
- **Immersion**: B2 requires 100% Ukrainian immersion. All examples, grammatical explanations, and cultural hooks must be purely in Ukrainian. English is restricted strictly to the vocabulary YAML translation column.
- **Agency**: Use active voice ("Ми використовуємо", "Українці кажуть") instead of passive constructs ("Використовується").

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ — що таке синонімія? (Introduction — What Is Synonymy?)"
    words: 600
    points:
      - "Provide a clear H3 definition of synonymy as a core lexical phenomenon that enriches speech, referencing State Standard §4.4.1.2."
      - "Create distinct H3s to contrast synonyms against paronyms and antonyms, explicitly highlighting the common learner error of confusing them (e.g., 'адрес' vs 'адреса')."
      - "Establish the B2 motivation: precise synonym selection is the foundation for mastering functional styles, elevating both oral fluency and academic writing."
  - section: "Абсолютні та семантичні синоніми (Absolute and Semantic Synonyms)"
    words: 800
    points:
      - "Dedicate an H3 to absolute synonyms (мовознавство — лінгвістика), explaining their rarity and origin (often native terms paired with borrowed equivalents)."
      - "Dedicate an H3 to semantic (ideographic) synonyms, illustrating how they grade intensity and meaning (e.g., сміливий — відважний — безстрашний)."
      - "Walk through a practical 'semantic component analysis' to help learners identify the core meaning and differing nuances between closely related verbs (іти — крокувати — мчати)."
      - "Include a warning block against using absolute synonyms interchangeably without checking the stylistic context of the sentence."
  - section: "Контекстуальні синоніми (Contextual Synonyms)"
    words: 800
    points:
      - "Define contextual synonyms in an H3: words that only become synonymous within a specific phrase (e.g., 'золотий' acting as 'чудовий' in 'золотий характер')."
      - "Explain the mechanisms of metaphorization and semantic shift that create these synonyms, providing authentic literary examples."
      - "Showcase authorial synonyms using excerpts from classic Ukrainian writers (like Kotsiubynsky or Stefanyk) to illustrate the creative, independent power of the language."
      - "Provide an analytical breakdown of why standard dictionaries cannot list all contextual synonyms, requiring active learner reading skills and contextual deduction."
  - section: "Стилістичні синоніми та регістр (Stylistic Synonyms and Register)"
    words: 800
    points:
      - "Break down stylistic synonyms in an H3, demonstrating how the core meaning stays the same while the register changes (обличчя — лице — пика)."
      - "Analyze the difference between neutral and marked synonyms (bookish, conversational, official), and teach how to read dictionary register tags."
      - "Discuss emotionally evaluative synonyms (positive vs. negative connotation, e.g., економний vs. скупий) and their psychological impact on text perception."
      - "Explicitly bridge this knowledge to functional styles, preparing the learner for the upcoming B2-55 module on registers."
  - section: "Синонімічні ряди та домінанта (Synonymic Rows and Dominant Word)"
    words: 1000
    points:
      - "Define the 'synonymic row' structure in an H3, explaining the spectrum from the core to the periphery."
      - "Dedicate an H3 to the 'dominant word' (домінанта) — the stylistically neutral anchor of the row (e.g., 'говорити')."
      - "Include a cultural hook H3 about the richness of Ukrainian rows, mentioning the record 45 synonyms for 'бити' and the 17,000+ rows in the national dictionary."
      - "Provide a step-by-step guide on how to systematically build and rank synonymic rows by intensity and style, encouraging active dictionary usage."
      - "Conclude with an actionable synthesis task: how learners can audit their own writing to eliminate repetitive words and elevate stylistic variety."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Full Phase A
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: grep_search failed with "The argument '--threads <NUM>' requires 1 values, but 2 were provided"
**Self-Correction**: I immediately switched to using `run_shell_command` with `rg` as directly advised by the project guidelines to bypass the `grep_search` tool bug.
**Proposed Tooling Fix**: Fix the `grep_search` system tool or its alias to properly handle the `--threads` argument so it doesn't duplicate the flag.
===FRICTION_END===
