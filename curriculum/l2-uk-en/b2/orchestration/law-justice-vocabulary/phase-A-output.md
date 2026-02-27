===RESEARCH_START===

# Дослідження: Право та юстиція

## State Standard Reference
§3.7: "Суспільні відносини: права й обов’язки; правоохоронні органи; рівність і справедливість; злочинність"
Alignment: This module directly addresses the B2 requirement to navigate societal relations regarding rights, duties, and law enforcement, utilizing the requisite official register and passive grammatical structures.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| суддя | High (news/legal) | слідчий суддя, голова суду, звертання «Ваша честь» |
| адвокат | High | надати правову допомогу, адвокатський запит, свідок захисту |
| прокурор | High | державний обвинувач, санкція прокурора |
| вирок | Medium-High | винести вирок, оскаржити вирок, виправдувальний вирок |
| позов | Medium | подати позов, цивільний позов, задовольнити/відхилити позов |
| свідок | High | давати свідчення, викликати свідка |

## Cultural Hooks
1. **«Руська Правда» (Rus' Justice):** The 11th-century legal code compiled by Yaroslav the Wise. It is crucial for understanding the humanization of law in Kyivan Rus', transitioning from the practice of blood feuds to a system of monetary compensation called «віра» (vira).
2. **Магдебурзьке право (Magdeburg Law):** Adopted in Kyiv between 1494 and 1499, this system of municipal self-government firmly embedded Ukrainian cities within the European legal and administrative tradition, granting them independent courts and breaking away from absolute feudal control.

## Common Learner Errors
1. **«Юрист» vs «Адвокат»:** Learners often use «юрист» for anyone in court. «Юрист» is a general term (lawyer/legal professional), while «адвокат» specifically denotes a defense attorney admitted to the bar who represents clients in trials.
2. **«По закону» (Calque):** Using the colloquial or Russian-influenced «по закону» instead of the correct official Ukrainian forms «згідно із законом», «відповідно до закону», or «за законом».
3. **«Давати покази» (Calque):** Directly translating "to give evidence/shows" leading to the incorrect «давати покази». The correct normative phrase is «давати свідчення».

## Cross-References
- Builds on: Abstract noun formation and introductory passive constructions from B1.
- Prepares for: C1 legal/academic discourse, professional business communication (B2-PRO), and understanding historical legal documents in HIST.

## Notes for Content Writing
- **Decolonized Framing:** Frame Ukraine's legal history (Rus' Pravda, Magdeburg Law) as a continuous integration with European legal norms of self-governance and codified justice, directly challenging the imperial narrative of an inherently autocratic past.
- **Active Agency:** Use constructions that show Ukrainians actively adopting and enforcing laws (e.g., «Містяни отримали право...», «Суди захищають...»).
- **Grammar Integration:** Weave passive voice (e.g., «позов задоволено», «вирок винесено») naturally into the explanation of the litigation process to demonstrate the objective tone of the official register.
- **Visual Aid:** Include a Mermaid flowchart in the final section to visually map the stages of litigation.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ: Історія права та Державні стандарти"
    words: 700
    points:
      - "Введення лексики теми згідно з §3.7 Держстандарту: обговорення прав, обов'язків та концепції рівності."
      - "Історичний аналіз «Руської Правди» Ярослава Мудрого: пояснення переходу від кровної помсти до системи штрафів («віра»)."
      - "Етимологічний розбір слова «Правда» як найвищої форми закону та моральної справедливості."
  - section: "Судова система та європейська традиція"
    words: 800
    points:
      - "Опис ієрархії судів України: розмежування функцій місцевих, апеляційних судів та Верховного Суду."
      - "Пояснення виняткової ролі Конституційного Суду України в захисті Основного Закону."
      - "Інтеграція культурного гачка: детальний розгляд Магдебурзького права (1494 р.) як свідчення європейського шляху міського самоврядування."
  - section: "Учасники процесу та мовленнєва культура"
    words: 800
    points:
      - "Деталізація ролей у залі суду: суддя (Ваша честь), прокурор (державний обвинувач) та адвокат (захисник)."
      - "Лексична диференціація: детальне пояснення різниці між загальним терміном «юрист» та спеціалізованим «адвокат»."
      - "Корекція типових помилок: відпрацювання нормативної конструкції «давати свідчення» замість кальки «давати покази»."
      - "Граматика прийменників: заміна розмовного «по закону» на офіційно-ділове «згідно із законом»."
  - section: "Класифікація справ та офіційний регістр"
    words: 800
    points:
      - "Юридичне розмежування: різниця між кримінальним злочином та адміністративним правопорушенням."
      - "Огляд спеціалізації судочинства: цивільні спори, кримінальні та господарські справи."
      - "Інтеграція граматики: демонстрація офіційного регістру через пасивні конструкції («санкцію погоджено», «рішення ухвалено»)."
  - section: "Судочинство: від позову до вироку"
    words: 900
    points:
      - "Покроковий опис судового процесу: від подання позову до збору доказів і винесення вироку."
      - "Пояснення механізму апеляції та процедури оскарження судових рішень."
      - "Практичний мовний аналіз: розбір фрагмента адаптованого судового рішення із застосуванням сталих колокацій («задовольнити позов», «відхилити скаргу»)."
      - "Розробка блок-схеми (Mermaid) етапів судового процесу для візуалізації лексики."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Full Phase A
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: grep_search failed with "The argument '--threads <NUM>' requires 1 values, but 2 were provided"
**Self-Correction**: Replaced the `grep_search` call with a manual `run_shell_command` using `sed` and `rg` to extract and search the relevant block from the State Standard document.
**Proposed Tooling Fix**: Fix the argument parsing bug in the `grep_search` tool to prevent duplicate `--threads` flags, as noted in the GEMINI.md project context.
===FRICTION_END===
