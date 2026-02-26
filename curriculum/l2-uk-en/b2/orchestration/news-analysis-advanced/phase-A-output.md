
⏳ Rate limited (attempt 1/5). Waiting 30s...
===RESEARCH_START===

# Дослідження: Аналіз новин: Поглиблено

## State Standard Reference
§1.1.2.2.2: "Діалоги: великі за обсягом неофіційні чи офіційні обговорення; дискусії та суперечки на відомі теми"
§3.18: "Медіа й соціальні мережі: преса; радіо; телебачення; інтернет і соціальні мережі"
Alignment: The module teaches learners to engage in in-depth official and unofficial discussions regarding media texts, specifically analyzing bias and manipulation in press and digital media.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| упередженість | High (media/political discourse) | політична упередженість, упереджене ставлення |
| маніпуляція | High (social sciences/news) | емоційна маніпуляція, піддаватися маніпуляціям |
| джинса | Medium (specific to UA journalism) | політична джинса, замовляти джинсу |
| оприлюднити | High (official reporting) | оприлюднити дані, оприлюднити результати |

## Cultural Hooks
1. Феномен «Джинса»: A uniquely Ukrainian journalistic term for hidden advertising or paid political articles disguised as news. The term allegedly originated because politicians paid for these articles with cash carried in their jeans pockets.
2. StopFake (2014): Launched by students and alumni of the Mohyla School of Journalism, this fact-checking initiative became a globally recognized pioneer in systematically debunking Russian disinformation and exposing fake news mechanics.

## Common Learner Errors
1. "Гарячі новини" → "Свіжі/останні новини" — A literal calque from English ("hot news") or Russian. Ukrainian prefers "свіжі" (fresh) or "останні" (latest).
2. "Зробити інтерв'ю" → "Взяти/дати інтерв'ю" — Incorrect verb choice due to English influence ("to do an interview").
3. "На ефірі" → "В ефірі" — Preposition mismatch. "Ефір" (air/broadcast) requires the preposition "в" (in), not "на" (on).

## Cross-References
- Builds on: M89 (Структура новин - implicit context for this advanced module)
- Prepares for: Future professional communication or C1 analytical writing.

## Notes for Content Writing
- Frame the Ukrainian media landscape positively, focusing on post-2014 achievements like the 2017 Suspilne (Public Broadcasting) reform and independent fact-checking initiatives.
- Do not use Russian media as a baseline for comparison. Explain disinformation techniques by dismantling them logically, without repeating the propaganda as facts.
- Agency Pass: Focus on active Ukrainian initiatives in combating fake news.
- Keep examples free of Russianisms (e.g., use «отримувати», not «получати»).

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Розминка та критичний вступ"
    words: 800
    points:
      - "Перехід від вивчення структури новин (М89) до глибокого деконструктивного аналізу змісту в умовах інформаційної війни"
      - "Українські медіа в глобальному контексті: Реформа Суспільного (НСТУ) 2017 року як крок до незалежної журналістики та роль наглядової ради"
      - "Обговорення новин та відгуків про них згідно зі стандартом B2 (§3.18, §1.1.2.2.2): фокус на інтенції аргументованої дискусії"
  - section: "Упередженість та редакційна політика"
    words: 900
    points:
      - "Аналіз типів упередженості: вибіркове висвітлення (selection bias), фреймінг (framing) та замовчування фактів (omission)"
      - "Український медіа-феномен «джинса»: розпізнавання прихованої реклами та політичного замовлення під виглядом новин"
      - "Порівняльний аналіз редакційної політики: як власники медіа-холдингів впливають на інтерпретацію подій"
      - "Розмежування понять «факт» та «судження» (fact vs opinion) у новинному тексті з прикладами"
  - section: "Пропаганда та емоційні маніпуляції"
    words: 900
    points:
      - "Техніки пропаганди: демонізація опонента, whataboutism як спосіб відвернення уваги та гіперболізація загроз"
      - "Емоційна лексика як маркер маніпуляції: апеляція до страху, гніву та штучного патріотизму для зниження критичного порогу"
      - "Механіка дезінформації: аналіз методів створення фейків на прикладі російської пропаганди про Україну (без ретрансляції самих фейків)"
  - section: "Верифікація та фактчекінг"
    words: 800
    points:
      - "Методологія верифікації: застосування CRAAP-тесту (Currency, Relevance, Authority, Accuracy, Purpose) для оцінки надійності медіа"
      - "Феномен StopFake (2014): історія проєкту Могилянської школи журналістики та його світове значення у боротьбі з дезінформацією"
      - "Практичні інструменти: ресурси VoxCheck, зворотний пошук зображень та правило перехресної перевірки (мінімум три незалежні джерела)"
  - section: "Мовний аналіз та типові помилки"
    words: 600
    points:
      - "Фреймінг через граматику: активний vs пасивний стан для приховування або підкреслення відповідальності суб'єкта дії"
      - "Корекція типових лексичних помилок: калькування «гарячі новини» (вживати: свіжі/останні новини) та «зробити інтерв'ю» (вживати: взяти/дати інтерв'ю)"
      - "Стилістичні нюанси: розмежування понять «опублікувати» (для преси) та «оприлюднити» (для документів/даних); різниця між «трансляцією» та «передачею»"
      - "Робота з прийменниками у медіа-контексті: правильне вживання «в ефірі» (не «на ефірі») та «дивитися по телевізору»"
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Searching State Standard mapping
**Friction Type**: TOOL_ERROR
**Raw Error**: grep_search failed with "The argument '--threads <NUM>' requires 1 values, but 2 were provided"
**Self-Correction**: Bypassed `grep_search` and executed raw `rg` command using `run_shell_command` to successfully locate the standard sections.
**Proposed Tooling Fix**: Fix the underlying script or wrapper for `grep_search` MCP to avoid duplicating or malforming the `--threads` argument.
===FRICTION_END===
