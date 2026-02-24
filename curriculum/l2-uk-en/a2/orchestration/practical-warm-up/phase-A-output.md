===RESEARCH_START===

# Дослідження: Practical Warm-up

## State Standard Reference
§1.1.1.2: "Особа розуміє: ... окремі вислови, короткі репліки в діалозі і не дуже довгі (30 – 50 слів) монологічні висловлювання на визначену тематику... сформульовані літературною мовою."
§1.2.1.4: "Особа вміє застосовувати стратегії, які полегшують розуміння текстів, наприклад оглядове читання, пошукове читання, і пристосовувати швидкість читання до поставлених перед нею завдань."
Alignment: This module translates theoretical knowledge into applied competence by explicitly developing active reading strategies (skimming/scanning) and listening skills for A2 benchmarks.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| питання | High (academic/civic) | вирішити питання, важливе питання |
| запитання | High (interaction) | ставити запитання, відповідати на запитання |
| слухати | High (active) | слухати уважно, слухати музику |
| чути | High (passive) | чути голос, погано чути |
| головний | Very High | головна ідея, головна інформація |

## Cultural Hooks
1. **Lviv Book Forum (Львівський міжнародний BookForum)**: The premier book fair in Ukraine, serving as a hub for contemporary Ukrainian literature and cultural exchange. It highlights the modern boom in domestic publishing.
2. **Radio Dictation of National Unity (Радіодиктант національної єдності)**: Held annually since 2000 on the Day of Ukrainian Language and Writing. Millions of Ukrainians globally tune in to write the dictation together, symbolizing profound linguistic resilience and community.

## Common Learner Errors
1. **питання vs запитання**: Learners universally use "питання" for everything. Fix: "запитання" expects an answer (a specific inquiry), while "питання" is a broader topic or problem to discuss or resolve.
2. **слухати vs чути**: Learners confuse intention with physical capability. "Я слухаю, але не чую" (I am actively trying to listen, but I physically cannot hear).

## Cross-References
- Builds on: a2-57 (Practical Intro)
- Prepares for: a2-59 (Medical Care)

## Notes for Content Writing
- Immersion Level: 75-90% (Band 3). English is restricted strictly to translation columns in vocabulary and brief clarifications of abstract reading/listening strategies. Prose, instructions, and examples must be in Ukrainian.
- Persona: "Morning Show Host / Cultural Guide". Ensure the tone is practical, engaging, and highly encouraging.
- Avoid Russianisms: Do not use or reference Russian framing for comprehension (e.g., focus on authentic Ukrainian contexts like BookForum instead of generalized post-Soviet examples).
- IPA should be present only on the first occurrence of new vocabulary words.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ"
    words: 400
    points:
      - "Set the 'Morning Show Host' persona tone, enthusiastically welcoming learners to a practical, action-oriented session."
      - "Explicitly define the module's goals in Ukrainian: understanding short texts (30-50 words) and differentiating key communicative vocabulary."
      - "Establish the A2 Band 3 immersion expectations (75-90%), using minimal English only if required to set the baseline."
  - section: "Навички читання: Скарби Книжкового Форуму"
    words: 700
    points:
      - "Introduce the 'Львівський BookForum' as an engaging cultural context for reading practice."
      - "Define 'оглядове читання' (skimming) and 'пошукове читання' (scanning) using simple Ukrainian explanations and metaphors."
      - "Provide a realistic 50-word text (e.g., a book blurb or festival poster) to practice identifying the 'головна ідея'."
      - "Include a tip box instructing learners on how to isolate 'ключові слова' (keywords) without needing to understand every single word."
  - section: "Слухання та говоріння: Активне сприйняття"
    words: 800
    points:
      - "Present a morning show mini-dialogue (6-8 exchanges) that explicitly demonstrates active listening for specific facts (names, times)."
      - "Include a 'Learner Error Clinic' callout contrasting 'чути' (passive physical hearing) and 'слухати' (active intentional listening)."
      - "Provide a structured explanation with 3 distinct example sentences for both 'чути' and 'слухати'."
      - "Add a guided practice drill where learners must logically select between 'чути' and 'слухати' based on context."
  - section: "Письмо: Радіодиктант національної єдності"
    words: 700
    points:
      - "Explain the rich cultural significance and unifying power of the 'Радіодиктант національної єдності'."
      - "Include a 'Learner Error Clinic' box contrasting 'питання' (issue/topic) and 'запитання' (inquiry expecting a response)."
      - "Illustrate the distinction with clear, short sentences (e.g., 'Це важливе питання' vs 'Можна поставити запитання?')."
      - "Simulate a mini dictation-prep exercise, focusing on transferring heard facts (like dates or simple phrases) into written text."
  - section: "Інтеграція та підсумок"
    words: 400
    points:
      - "Provide a synthesis checklist of the active reading and listening strategies covered in the module."
      - "Include a brief integration task: reading a short announcement and answering specific 'запитання' about its 'головна ідея'."
      - "Transition to the upcoming high-stakes scenario (Medical Care), emphasizing how these active perception skills will be critical."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Researching State Standard
**Friction Type**: TOOL_ERROR
**Raw Error**: Process exited with code 2: error: The argument '--threads <NUM>' requires 1 values, but 2 were provided
**Self-Correction**: The `grep_search` tool failed due to a misconfigured argument in the underlying wrapper. I bypassed it by directly executing `rg` within `run_shell_command` to successfully locate and extract the required sections (§1.1.1.2 and §1.2.1.4) from the standard.
**Proposed Tooling Fix**: The `grep_search` MCP tool appears to be double-injecting the `--threads` flag into its `rg` invocation. The tool wrapper script needs to be inspected and fixed to prevent argument duplication.
===FRICTION_END===
