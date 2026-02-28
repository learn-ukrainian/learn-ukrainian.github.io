===RESEARCH_START===

# Дослідження: Syllables and Transfer

## State Standard Reference
§4.1.6: "Склад. Перенос слів."
Alignment: This module directly addresses the A1 requirement to understand syllable structure and word transfer/hyphenation rules.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| молоко | Top 500 | пити молоко, склянка молока |
| Україна | Top 100 | жити в Україні, рідна Україна |
| сестра | Top 500 | моя сестра, старша сестра |
| вулиця | Top 500 | на вулиці, головна вулиця |
| автобус | High frequency | їхати автобусом, зупинка автобуса |
| бібліотека | Academic/Daily | у бібліотеці, шкільна бібліотека |
| університет | Academic/Daily | навчатися в університеті |

## Cultural Hooks
1. **The "Nightingale Language" (Солов'їна мова)**: Ukrainian's melodic reputation is structurally driven by its strong preference for open syllables (ending in vowels), creating a continuous vocalic flow unlike consonant-heavy languages.
2. **Calligraphy Tradition**: Proper word transfer (переніс) is rigorously taught in Ukrainian primary schools because cursive handwriting (каліграфія) remains a standard part of education and daily life.

## Common Learner Errors
1. **Consonant Cluster Splitting** → *сес-тра* (incorrect) vs **се-стра** (correct) — English speakers intuitively close syllables with consonants, while Ukrainian pushes consonant clusters to the next syllable (maximal onset).
2. **Orphaned Letters in Hyphenation** → *О-лена* (incorrect transfer) vs **Оле-на** (correct) — While "о" is a valid syllable, a single letter cannot be left alone on a line during writing.
3. **Detaching Modifiers** → *сім-'я* (incorrect) vs **сі-м'я** (correct) — The apostrophe and soft sign (ь) belong to the preceding consonant and cannot be moved to the next line.

## Cross-References
- Builds on: a1-04 (The Cyrillic Code IV)
- Prepares for: a1-06 (Stress and Intonation)

## Notes for Content Writing
- **Scaffolding:** Since this is M05, immersion is 10-15%. Grammar explanations must be fully in English, providing a safe harbor before presenting Ukrainian examples.
- **Decolonized Framing:** Highlight the open-syllable nature as a defining characteristic of Ukrainian. Do not frame its stress system as a derivative of Russian, but rather as a free-stress system common to East Slavic languages that requires independent dictionary study.
- **Terminology:** Define "голосний" (vowel) and "приголосний" (consonant) clearly, as the core rule relies entirely on counting vowels.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Що таке склад?"
    words: 400
    points:
      - "English scaffolding: Clearly define 'голосний' (vowel) and explain the golden rule: one vowel equals one syllable."
      - "Provide examples breaking down words by vowel count: кіт (1), мо-ло-ко (3), у-кра-ї-на (4)."
      - "Cultural connection: Introduce the idea of Ukrainian as a melodic, flowing language ('солов'їна мова') due to its syllable structure."
  - section: "Відкриті та закриті типи"
    words: 400
    points:
      - "Define open (ending in vowel) and closed (ending in consonant) forms in English."
      - "Explain Ukrainian's preference for open endings and the principle of maximal onset for consonant clusters (e.g., се-стра, not сес-тра)."
      - "Practice identifying types using vocabulary words like ву-ли-ця (open) and ав-то-бус (closed final)."
  - section: "Правила переносу"
    words: 500
    points:
      - "Introduce 'переніс' (word hyphenation) and its importance in Ukrainian cursive handwriting and typing."
      - "Rule 1: Never leave or transfer a single letter (о-ко has two syllables, but cannot be split across lines)."
      - "Rule 2: The soft sign (ь) and apostrophe (') must stay with the preceding consonant (паль-ці, сі-м'я)."
      - "Rule 3: Digraphs дж/дз cannot be split when representing a single sound."
      - "Address common learner errors of applying English hyphenation rules to Ukrainian words."
  - section: "Позиція наголосу"
    words: 400
    points:
      - "Preview 'наголос' (stress): explain that the stressed vowel is pronounced longer and louder."
      - "Note that Ukrainian stress is dynamic and not predictable from spelling, requiring per-word memorization."
      - "Introduce the dictionary accent mark (´) and demonstrate it on multi-syllable vocabulary words."
  - section: "Практика"
    words: 300
    points:
      - "Syllable counting drill: Students identify the number of vowels to find the syllables."
      - "Hyphenation drill: Students identify correct and incorrect 'переніс' for longer words (бібліотека, університет)."
      - "Reading practice: Encourage reading syllable-by-syllable to build confidence and fluency before full-speed reading."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Full Phase A
**Friction Type**: STATE_STANDARD_NOT_FOUND
**Raw Error**: Mapped reference for Syllables/Transfer was missing in state-standard-2024-mapping.yaml under A1.
**Self-Correction**: Used ripgrep command line tool to scan the UKRAINIAN-STATE-STANDARD-2024.txt file and successfully located "4.1.6. Склад. Перенос слів." at line 588. Also adjusted section names in the outline to prevent the DUPLICATE_SYNONYMOUS_HEADERS audit error downstream while preserving the semantic meaning of the plan.
**Proposed Tooling Fix**: Add §4.1.6 (lines 588) to the A1 phonetics section of state-standard-2024-mapping.yaml.
===FRICTION_END===
