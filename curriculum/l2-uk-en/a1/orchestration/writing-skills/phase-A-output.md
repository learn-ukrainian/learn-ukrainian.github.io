===RESEARCH_START===

# Дослідження: Writing Skills

## State Standard Reference
§1.3 (Письмо): "написати адресу проживання, указавши країну, місто, вулицю, номер... заповнити прості формуляри та анкети... заадресувати конверт; прості, короткі привітання, зокрема на поштових листівках."
Alignment: This module directly fulfills the A1 competency requirements for written production regarding daily life forms, basic correspondence, and addressing envelopes.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| анкета | High (Forms/Bureaucracy) | заповнити анкету, електронна анкета |
| листівка | Medium (Travel/Holidays) | поштова листівка, надіслати листівку |
| прізвище | Very High (ID/Forms) | ім'я та прізвище, дівоче прізвище |
| адреса | Very High (Daily/Post) | домашня адреса, електронна адреса |
| індекс | Medium (Post) | поштовий індекс, вказати індекс |

## Cultural Hooks
1. **European Postal Standards**: Independent Ukraine successfully transitioned its postal addressing system from the Soviet "general-to-specific" format (Country → City → Street → Name) to the European "specific-to-general" standard (Name → Street → City → Postcode), reflecting its integration into global systems. 
2. **The "По батькові" (Patronymic) Reality**: While everyday communication rarely uses patronymics among younger generations, every official Ukrainian form (анкета) still rigorously requires it. Knowing how to parse "Прізвище, Ім'я, По батькові" (ПІБ) is an essential survival skill for navigating any Ukrainian institution.

## Common Learner Errors
1. **Name confusion** → Confusing "ім'я" with full name. English speakers often put their full name under "ім'я", leaving "прізвище" blank.
2. **Greeting Case** → *Привіт з Київ* (Nominative) instead of the correct *Привіт з Києва* (Genitive). Learners forget that "з" (from) demands the Genitive case.
3. **Date Format** → Writing MM.DD.YYYY. Ukraine strictly uses DD.MM.YYYY. 

## Cross-References
- Builds on: a1-58 (Phone Basics)
- Prepares for: a1-60 (At the Market)

## Notes for Content Writing
- **Decolonized Framing**: Highlight the modern Ukrainian postal system (Ukrposhta) and its European address format. Do not compare it to Russian/Soviet bureaucracy. Frame form-filling as a normal part of modern digital and physical life in Ukraine.
- **English Scaffolding**: Since this is A1, provide clear English explanations for the structure of forms and postcards before diving into Ukrainian examples.
- **Visuals**: A mock-up table of a Ukrainian form (анкета) and an envelope (конверт) will be highly effective here.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Поштова листівка"
    words: 450
    points:
      - "Provide English scaffolding: Explain the goal of writing a short postcard from a Ukrainian city."
      - "Introduce the standard postcard template using H3s: Greeting, Body (3-4 sentences), Sign-off."
      - "Grammar focus: Explain the 'Привіт з + Genitive' construction (e.g., Привіт з Києва, Привіт зі Львова)."
      - "Provide a fully translated example of a complete postcard."
  - section: "Анкета"
    words: 450
    points:
      - "Introduce the concept of 'анкета' (form) and its importance in Ukrainian daily life."
      - "Breakdown form fields: Прізвище, Ім'я, По батькові, Дата народження, Стать, Телефон, Електронна пошта."
      - "Explain cultural nuances: The use of DD.MM.YYYY for dates and the standard options for gender (чоловіча/жіноча)."
      - "Include a visual table representing a blank Ukrainian form with English translations."
  - section: "Про себе"
    words: 400
    points:
      - "Guide the learner on how to synthesize previous knowledge into a short 'About Me' paragraph (30-50 words)."
      - "Provide the template: Мене звати... Мені ... років. Я з... Я працюю/вчуся... Моє хобі..."
      - "Show 2-3 short, distinct examples of character profiles (e.g., a student, a professional) with English translations."
  - section: "Конверт та адреса"
    words: 400
    points:
      - "Explain the modern Ukrainian address format: specific to general (Name → Street → City → Postcode)."
      - "Introduce Dative (Кому) and Genitive (Від кого) briefly as formulaic phrases used on envelopes."
      - "Define essential abbreviations: вул. (вулиця), буд. (будинок), кв. (квартира)."
      - "Provide a visual layout of a correctly addressed envelope."
  - section: "Практика"
    words: 300
    points:
      - "Provide a guided writing prompt: Ask the learner to mentally fill out a provided blank form."
      - "Provide a postcard prompt: 'You are in Odesa. Write 4 sentences using the template.' Include the model answer."
      - "Encourage the learner to write their own 40-word 'Про себе' text based on the section template."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Searching the UKRAINIAN-STATE-STANDARD-2024.txt for standard references
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: Error during grep search operation: Process exited with code 2: error: The argument '--threads <NUM>' requires 1 values, but 2 were provided
**Self-Correction**: Bypassed the broken `grep_search` custom tool and successfully used `run_shell_command` with `rg` to extract the exact requirements from §1.3 (Письмо).
**Proposed Tooling Fix**: The underlying definition of the `grep_search` tool appears to be injecting a duplicate or improperly formatted `--threads` flag into the `rg` command. The tool implementation needs to be fixed.
===FRICTION_END===
