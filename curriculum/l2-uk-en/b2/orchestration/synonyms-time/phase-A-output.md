===RESEARCH_START===

# Дослідження: Синоніми: Час та Періоди

## State Standard Reference
§4.4.1.2: "Стилістичні засоби лексики: ... синоніми: говорити, розмовляти, спілкуватися;"
Alignment: This module directly addresses B2 lexical stylistics by systematically analyzing synonymous temporal adverbs (зараз, тепер, наразі, нині, щойно, колись) and focusing on their exact stylistic and register differentiation.

## Vocabulary Frequency
| Word | Frequency / Context | Key collocations |
|------|---------------------|------------------|
| зараз | Very high / Colloquial | зараз роблю, саме зараз |
| тепер | High / Neutral | тепер ми знаємо, відтепер |
| наразі | Med-High / Official | наразі невідомо, наразі триває |
| нині | Medium / Publicistic | нині відомо, станом на нині |
| щойно | High / Immediate past | щойно повернувся, щойно отримали |
| колись | High / Narrative past | колись давно, як колись |

## Cultural Hooks
1. Hryhorii Skovoroda's philosophical valuation of time: «З усіх утрат утрата часу найтяжча» (Of all losses, the loss of time is the heaviest).
2. The traditional Ukrainian agrarian worldview prioritizing patience and natural order: «Всякому овочу свій час» (Every vegetable has its time).

## Common Learner Errors
1. Using "зараз" for extended periods (e.g., "зараз я живу в Києві" instead of "тепер я живу в Києві") — confusing immediate action with a current epoch/state.
2. Calquing "в даний момент" from the Russian "в данный момент" — Ukrainian authentically uses "наразі" or simply "зараз" depending on the register.

## Cross-References
- Builds on: B1 temporal adverbs and verb aspect pairings.
- Prepares for: C1 advanced stylistic register and publicistic phrasing.

## Notes for Content Writing
- **Decolonized Framing**: Emphasize how "наразі" and "нині" are authentically Ukrainian, resisting the Soviet-era bureaucratic tendency to flatten synonyms to match Russian equivalents. Contrast "наразі" (natural Ukrainian) with "в даний момент" (bureaucratic Russian calque).
- **Agency Pass**: Frame all examples with Ukrainians as active subjects (e.g., "Ми щойно закінчили проєкт").
- **Persona Context**: Assume the "Professional Language Coach / Archeologist" persona to explore "deep time" versus "immediate time" in Section 4.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ: Філософія та духовна цінність часу"
    words: 600
    points:
      - "Вступне слово про час як духовну категорію через максиму Г. Сковороди: «З усіх утрат утрата часу найтяжча». Опис концепції через призму сучасного міського темпу."
      - "Уособлення та невтомність часу в українській світогляді на прикладі поезії Ліни Костенко: «Єдиний, хто не втомлюється, — час». (Використати як культурний гачок)."
      - "Обговорення фольклорного принципу природного порядку та терпіння: «Всякому овочу свій час» із прикладами з української традиційної культури."
  - section: "Мить чи епоха: Диференціація «зараз» та «тепер»"
    words: 900
    points:
      - "Аналіз лексичної точності (§4.4.1.2): «зараз» для позначення поточної миті (immediate action) vs «тепер» для тривалого періоду чи епохи (current epoch/status)."
      - "Робота над типовою помилкою: детальне пояснення, чому вираз «зараз я живу в Києві» є некоректним порівняно з «тепер я живу в Києві» (уникнення кальок)."
      - "Практичні порівняння та міні-діалоги: використання «зараз» та «тепер» у реченнях про професійну діяльність та особисті зміни (напр., перехід на дистанційну роботу)."
  - section: "Офіційний та публіцистичний регістр: «наразі» та «нині»"
    words: 900
    points:
      - "Вживання слова «наразі» в офіційно-діловому контексті як ознаки тимчасовості («наразі триває», «наразі невідомо»). Розбір його автентичної української природи."
      - "Стилістичне забарвлення прислівника «нині» в публіцистиці та його порівняння з нейтральним «сьогодні»."
      - "Боротьба з мовними кальками: заміна незграбної радянської конструкції «в даний момент» на природні українські синоніми («наразі», «нині») залежно від контексту."
  - section: "Погляд Археолога: Від «щойно» до «колись давно»"
    words: 800
    points:
      - "Дослідження «глибокого часу» через наративні маркери «колись», «давно», «у давнину» та специфіку частки «колись-то» (з акцентом на історичні оповіді)."
      - "Точність вживання слова «щойно» як маркера негайного минулого (immediate past) та його роль у новинному та розмовному стилях."
      - "Використання археологічної метафори для опису часових шарів в історії України (від давнини до сучасності), інтегруючи вивчені прислівники часу."
  - section: "Синтез: Часові вирази в історичному та діловому контекстах"
    words: 800
    points:
      - "Створення історичного огляду з використанням градації часових прислівників від давнини до сьогоднішнього дня."
      - "Трансформація тексту: переписування неформальної розповіді про історичні/культурні події в офіційний звіт зі зміною часових маркерів (використання «наразі», «відтепер», «нині»)."
      - "Підсумкова дискусія про концепцію вічності та миті в українському мовному просторі, закріплення синонімічних рядів."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Full Phase A
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: Error during grep search operation: Process exited with code 2: error: The argument '--threads <NUM>' requires 1 values, but 2 were provided
**Self-Correction**: Switched to using `run_shell_command` with ripgrep (`rg`) to safely extract and locate the necessary standard mappings and keyword mentions within the UKRAINIAN-STATE-STANDARD-2024.txt file, bypassing the broken `grep_search` tool. Also noted that `read_file` with `offset` and `limit` provides a cleaner mechanism than using `sed` within a bash command.
**Proposed Tooling Fix**: Fix the `grep_search` tool wrapper as it currently injects duplicate `--threads` arguments during its internal ripgrep invocation.
===FRICTION_END===
