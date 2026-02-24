===RESEARCH_START===

# Дослідження: Числівники: збірні та дроби

## State Standard Reference
§4.2.1.3: "Числівник: кількісні числівники один (одна, одне, одні), два (дві), три, чотири: один, одного, двох, двом, на трьох, чотирьох, чотирма"
Alignment: The State Standard broadly outlines quantitative numeral declensions for B1. This module addresses the functional necessity of collective (збірні) and fractional (дробові) numerals to achieve fluency in daily communication, specifically counting groups of people, pluralia tantum nouns, and percentages, which expand upon the basic B1 quantitative numeral requirement.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| половина | Very High | о пів на другу, половина часу, друга половина |
| двоє/троє | High | нас двоє, двоє дітей, троє дверей, троє друзів |
| півтора | High | півтора року, півтора місяця, півтора літра |
| чверть | High | чверть на третю, чверть століття |
| відсоток | Medium (Formal) | сто відсотків, п'ять відсотків |

## Cultural Hooks
1. Сакральне число три ("Бог трійцю любить"): Deeply embedded in Ukrainian folklore (three brothers, three tasks in fairy tales, three roads). It demonstrates the cultural resonance of "троє" and the adverbial form "утрьох".
2. Сакральна дюжина (12): The traditional 12 Lenten dishes (пісні страви) prepared for Christmas Eve (Святий Вечір), representing the 12 apostles and the 12 months of the year, anchoring numeral usage in an authentic Ukrainian custom.

## Common Learner Errors
1. «Два студенти» vs «нас двоє» → Correct form: "нас двоє" (for groups of people/mixed gender) — Learners incorrectly translate "two of us" directly using the cardinal numeral.
2. The Grandmother Trap → Correct form: "три бабусі" (not "троє бабусь") — Collectives cannot be used with feminine animate nouns.
3. The Phone Trap → Correct form: "два телефони" (not "двоє телефонів") — Collectives cannot be used with inanimate masculine nouns.
4. "Півтора" agreement → Correct form: "півтора року" (not "півтора років") — "Півтора" mandates the Genitive Singular, contrasting with plural requirements in some other Slavic languages.

## Cross-References
- Builds on: b1-48 (Diminutives Master Class)
- Prepares for: b1-50 (Checkpoint Participles Numerals)

## Notes for Content Writing
- 100% immersion required. Do not use English in grammatical explanations. English is strictly reserved for the «Переклад» column in the vocabulary table.
- Emphasize the distinct nature of Ukrainian collective numerals. Do not contrast with Russian; frame Ukrainian as having a rich, organic system for describing collective animacy and pluralia tantum (e.g., «двоє ножиць»).
- Ensure clear layout (tables, flowcharts) for the Genitive plural agreement after collectives and the Genitive singular after «півтора».
- Use IPA exclusively in the vocabulary YAML file, never inline in the markdown content.
- Ensure no header shares exact duplicate words if it can be avoided to pass the audit script. 

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ та діагностика"
    words: 500
    points:
      - "Diagnostic cloze task: testing the distinction between 'два' and 'двоє' in conversational contexts (e.g., 'два студенти' vs 'нас двоє')."
      - "Module objectives in Ukrainian: mastering collective and fractional numerals to achieve natural B1+ fluency in daily situations."
      - "Explicit reminder: 100% Ukrainian immersion, establishing the grammatical baseline."
  - section: "Збірні числівники та «Пастки»"
    words: 1200
    points:
      - "The 'Who counts?' logic (Flowchart/rules): identifying triggers for collectives, specifically living males (двоє хлопців), mixed groups, baby animals (четверо цуценят), and plurale tantum (троє дверей)."
      - "Rule breakdown: mandatory Genitive Plural case agreement after collective numerals (двоє студентів, четверо коней) presented in a clear paradigm table."
      - "Addressing the 'Grandmother Trap': explicit rule forbidding collectives with feminine animate nouns (must use 'три бабусі')."
      - "Addressing the 'Phone Trap': explicit rule forbidding collectives with inanimate masculine nouns (must use 'два телефони')."
  - section: "Дроби, відсотки та особливі форми"
    words: 1000
    points:
      - "Fractional numerals in daily life: половина, третина, чверть; emphasizing their integration into time-telling expressions (чверть на третю, о пів на другу)."
      - "Mastering 'півтора/півтори' (one and a half): high-frequency usage and the strict requirement for the following noun to be in Genitive Singular (півтора місяця, півтори години)."
      - "Percentages and decimals: formation rules, reading format (нуль цілих п'ять десятих), and agreement with the Genitive case (п'ять відсотків)."
  - section: "Культурний контекст: Магія чисел"
    words: 800
    points:
      - "Analysis of the magical number 3 in Ukrainian Folklore: exploring the proverb 'Бог трійцю любить' and the recurrence of 'three brothers/tasks' in traditional tales."
      - "The Holy Number 12 and the '12 Dishes': cultural anchoring of Christmas Eve (Святий Вечір) traditions, representing the apostles and the months of the year."
      - "Reading comprehension incorporating both collective numerals and cultural statistics."
  - section: "Мовленнєва практика та підсумок"
    words: 500
    points:
      - "Real-world social scenarios: mini-dialogues applying 'нас п'ятеро' at a restaurant and discussing statistics using fractions."
      - "Mathematical contexts and recipes: applying fractional numerals to measurements with a focus on conversational fluidity."
      - "Summary table consolidating rules for cardinal vs. collective triggers and 'півтора' agreement."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Full Phase A
**Friction Type**: TOOL_REDUNDANCY / STATE_STANDARD_NOT_FOUND
**Raw Error**: `grep_search` failed with `--threads` argument error; State standard mapping file maps §4.2.1.3 to "collective numerals (двоє, п'ятеро), fractions" but the exact line bounds 2085-2093 in the text refer generally to cardinal/ordinal/indefinite numerals and do not explicitly name "збірні" or "дробові", although they are subsumed under the category.
**Self-Correction**: Used `run_shell_command` with `sed` and `rg` instead. Re-evaluated the mapping to confirm that B1 numerals encompass collectives and fractions under the broad umbrella of numeral declension (§4.2.1.3).
**Proposed Tooling Fix**: Fix the `grep_search` wrapper that injects an extra `--threads` flag for `rg`. Update the State Standard Mapping comments to clarify that collective/fractional specifics are inferred from the broad "кількісні числівники" heading in B1.
===FRICTION_END===
