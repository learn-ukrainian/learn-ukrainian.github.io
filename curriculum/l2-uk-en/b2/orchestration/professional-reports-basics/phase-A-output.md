
⏳ Rate limited (attempt 1/5). Waiting 30s...

⏳ Rate limited (attempt 2/5). Waiting 60s...

⏳ Rate limited (attempt 3/5). Waiting 120s...
===RESEARCH_START===

# Дослідження: Професійні звіти: Основи

## State Standard Reference
§4.2.6: "Утворення іменників – назв діяльності (суфікси -нн-, -енн-, -інн-): читати – читання... навантажувати – навантаження..."
§4.3.3.1: "Односкладні речення з головним членом – дієсловом... безособові речення: Було приємно дивитися на веселих дітей. Там усе правильно записано."
*Примітка: §3.11 у Стандарті стосується тематики (напр., Робота, Послуги), а не стилістики.*
Alignment: Цей модуль безпосередньо реалізує вимоги B2 щодо використання віддієслівних іменників (§4.2.6) та безособових конструкцій (§4.3.3.1) у професійному мовленні.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| звіт | High (Professional) | складати звіт (не "робити звіт"), фінансовий звіт |
| аналіз | High (Academic/Pro) | проводити аналіз, на основі аналізу |
| підсумок | High (Professional) | підбивати підсумки, у підсумку |
| згідно з | High (Formal Register)| згідно з інструкцією, згідно з даними |

## Cultural Hooks
1. **Історичне коріння**: Український діловий стиль має глибокі традиції, які сягають часів Генеральної військової канцелярії Гетьманщини (17-18 ст.). Це спростовує міф про те, що ділова українська є лише "перекладом з російської".
2. **Дерадянізація мови**: Сучасний український корпоративний сектор активно відмовляється від радянського "канцеляризму" (штучної ускладненості), переходячи до лаконічних глобальних стандартів із збереженням природної української граматики.

## Common Learner Errors
1. *приймати участь* замість *брати участь* — Калька з російської мови.
2. *підводити підсумки* замість *підбивати підсумки* — Поширена калька у діловому мовленні.
3. *згідно інструкції* замість *згідно з інструкцією* — Пропуск прийменника "з" та помилка у відмінку (потрібен орудний).
4. Зловживання активним станом ("Ми виявили") там, де офіційний стиль вимагає безособовості ("Було виявлено").

## Cross-References
- Builds on: M85-86 (Professional Emails)
- Prepares for: M88 (Advanced Reports), M94 (Final Exam)

## Notes for Content Writing
- Уникайте російських порівнянь; акцентуйте на тому, що безособовість та віддієслівні іменники є природною ознакою високого стилю української мови.
- Забезпечте 100% українськомовне занурення; жодних англійських пояснень у тексті.
- Використовуйте модульні дієслова (можливо, варто зазначити) для згладжування категоричності у рекомендаціях звіту.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ"
    words: 600
    points:
      - "Introduce the Ukrainian official-business style (офіційно-діловий стиль), highlighting its deep historical roots in the Cossack Hetmanate's General Military Chancellery."
      - "Frame the transition from short-form emails (M85-86) to structured reports, emphasizing the modern shift toward concise, global standards and away from wordy Soviet 'kantseliaryzm'."
      - "Establish the expectation of 100% Ukrainian immersion for professional communication at the B2 level."
  - section: "Імерсивна розповідь: Структура та компоненти"
    words: 1000
    points:
      - "Narrative arc: Follow a junior analyst (молодший аналітик) preparing their first major project progress report, balancing technical results with practical recommendations."
      - "Break down the structural components within the story: from the Title Page (Титульна сторінка) and Methodology (Методологія), to the Appendices (Додатки)."
      - "Explain the 'Executive Summary' (Резюме) strategy: why it must be written last but placed first to provide immediate clarity for decision-makers."
  - section: "Аналіз та візуалізація даних"
    words: 1000
    points:
      - "Detail the logical organization of a report: flowing from general findings to specific conclusions with clear header hierarchy and one thought per paragraph."
      - "Provide specific vocabulary for describing data trends (зростання, зниження, стабілізація) neutrally, strictly avoiding emotional or subjective evaluations."
      - "Demonstrate how to linguistically integrate visualizations using standard formulaic expressions (e.g., 'Як показано на графіку...', 'Згідно з даними в таблиці...')."
  - section: "Граматика: Безособовість та стиль"
    words: 800
    points:
      - "State Standard §4.2.6: Teach the formation and use of deverbal nouns with suffixes -ння and -ення (виконання, забезпечення) to formalize actions."
      - "State Standard §4.3.3.1: Master impersonal constructions and the 'було' + past participle structure (було виявлено, встановлено) to emphasize results over actors."
      - "Provide comparison tables illustrating how to convert conversational active voice ('Ми проаналізували') into professional passive voice ('Було проаналізовано')."
  - section: "Підсумок та усунення помилок"
    words: 600
    points:
      - "Drill essential prepositional mastery: explicitly correct the misuse of 'згідно' and enforce 'згідно з' + Instrumental case."
      - "Correct major corporate calques: contrast the incorrect 'приймати участь' / 'підводити підсумки' with the correct 'брати участь' / 'підбивати підсумки'."
      - "Identify and eliminate common pleonasms ('вільна вакансія', 'своя автобіографія') to meet B2 conciseness standards."
      - "Synthesize the module's skills to prepare the learner for M88 (Advanced Reports) and the B2 Final Exam."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Researching State Standard
**Friction Type**: TOOL_BUG
**Raw Error**: grep_search tool failed with `error: The argument '--threads <NUM>' requires 1 values, but 2 were provided`
**Self-Correction**: Used `run_shell_command` with `rg` as a fallback, as explicitly allowed and recommended in the system prompt instructions for when the custom search tool fails. Read the file contents using `read_file` with precise offsets to extract the exact State Standard citations.
**Proposed Tooling Fix**: Fix the argument parsing for the `--threads` flag in the `grep_search` API tool definition or implementation.
===FRICTION_END===
