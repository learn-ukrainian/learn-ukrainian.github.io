# A1 English scaffold audit — things-have-gender, what-is-it-like

Date: 2026-09-13. Author: kimi/cu-p1-a1-en-scaffold. Refs: PR #7999.

Operator correction 2026-09-13: A1 is bilingual, not Ukrainian-only. Untranslated
learner-facing Ukrainian is **HIGH** pedagogical severity (was LOW). Band:
`a1-m07-14`, target 40–55% Ukrainian, ULP S1 bilingual immersion
(`max_unsupported_uk_words: 68`, `support_proximity: 8`). Pattern: Ukrainian-first,
then English — em-dash gloss for short phrases, UK|EN support table for passages,
dialogues stay Ukrainian-only in the box with an English breakdown immediately after.

Line numbers below refer to the **pre-fix** files (HEAD before this change).

## Fixed — module.md

### things-have-gender/lesson-1/module.md

| line | block (before) | severity | after |
| --- | --- | --- | --- |
| 1 | `# Він, вона́ чи воно́?` | HIGH | `# Він, вона́ чи воно́? — He, she, or it?` |
| 3 | `У цьо́му уро́ці ми дослі́джуємо грамати́чний рід украї́нських іме́нників:` | HIGH | `... іме́нників — in this lesson we explore the grammatical gender of Ukrainian nouns:` |
| 32 | `## Діало́ги` | HIGH | `## Діало́ги — Dialogues` |
| 65 | `### Пита́льні слова́` | HIGH | `### Пита́льні слова́ — Question words` |
| 97 | `## Він, вона́, воно́` | HIGH | `## Він, вона́, воно́ — He, she, it` |
| 140 | `### Підсу́мок уро́ку 1` | HIGH | `### Підсу́мок уро́ку 1 — Lesson 1 summary` |
| 142 | `Чудо́ва ро́бота! Ви вже впе́внено розрізня́єте три роди́ слів:` | HIGH (recap praise, named must-fix) | `Чудо́ва ро́бота! — Great work! Ви вже ... — you can already confidently tell apart the three genders of words:` |
| 150 | `### Ва́ше мо́влення` | HIGH | `### Ва́ше мо́влення — Your speaking` |
| 152 | `Напиші́ть 2–3 коро́ткі рядки́ про ре́чі бі́ля вас:` | HIGH | `... — write 2–3 short lines about things near you:` |
| 153–155 | model lines `Це мій стіл.` etc. | HIGH | per-line em-dash glosses (`— This is my table.` etc.) |

### things-have-gender/lesson-2/module.md

| line | block (before) | severity | after |
| --- | --- | --- | --- |
| 1 | `# Предме́ти навко́ло` | HIGH | `# Предме́ти навко́ло — Objects around us` |
| 3 | intro paragraph (`У пе́ршому уро́ці ... навко́ло нас:`) | HIGH | English sentences added after each Ukrainian sentence |
| 8 | `## Предме́ти навко́ло` | HIGH | `## Предме́ти навко́ло — Objects around us` |
| 36–38 | pronoun lines `Де стіл? Він тут.` etc. | HIGH | per-line glosses (`— Where is the table? It is here.` etc.) |
| 47 | `## Що у твої́й су́мці?` | HIGH | `## Що у твої́й су́мці? — What is in your bag?` |
| 71 | `## Мій, моя́, моє́` | HIGH | `## Мій, моя́, моє́ — Three forms of "my"` |
| 86–88 | phrase lists `мій брат, мій та́то...` | HIGH | em-dash gloss per list (`— my brother, my dad, my table` etc.) |
| 100 | `### Підсу́мок уро́ку 2` | HIGH | `### Підсу́мок уро́ку 2 — Lesson 2 summary` |
| 102 | `Чудо́во! Тепе́р ви вмі́єте опи́сувати свій про́стір украї́нською мо́вою:` | HIGH (recap praise, named must-fix) | `Чудо́во! — Great! Тепе́р ... — now you can describe your space in Ukrainian:` |
| 110 | `### Ва́ше мо́влення` | HIGH | `### Ва́ше мо́влення — Your speaking` |
| 112–115 | instruction + model lines | HIGH | instruction glossed; model lines glossed (`— This is my room.` etc.) |

### things-have-gender/lesson-3/module.md

| line | block (before) | severity | after |
| --- | --- | --- | --- |
| 1 | `# Профе́сії, па́стки й самопереві́рка` | HIGH | `# Профе́сії, па́стки й самопереві́рка — Professions, traps, and self-check` |
| 3 | intro paragraph | HIGH | English sentences added after the Ukrainian |
| 8 | `## Підсу́мок` | HIGH | `## Підсу́мок — Summary` |
| 51 | `### Діало́г про профе́сії` | HIGH | `### Діало́г про профе́сії — A dialogue about professions` |
| 55–62 | professions dialogue with **no English breakdown** | HIGH (MEDIUM re-rated per correction) | new UK|EN support table inserted immediately after the dialogue (7 rows) |
| 65–71 | family dialogue with **no English breakdown** | HIGH (MEDIUM re-rated per correction) | new UK|EN support table inserted immediately after the dialogue (7 rows) |
| 77 | `## Імена́, па́стки й самопереві́рка` | HIGH | `## Імена́, па́стки й самопереві́рка — Names, traps, and self-check` |
| 83 | `### Пильну́й па́стки` | HIGH | `### Пильну́й па́стки — Watch out for traps` |
| 111 | `### Самопереві́рка` | HIGH | `### Самопереві́рка — Self-check` |
| 128 | `Тепе́р переві́рте профе́сії, чолові́чі імена́ та ви́нятки:` | HIGH | `... — now check professions, male names, and exceptions:` |
| 158 | `### Заве́ршення мо́дуля` | HIGH | `### Заве́ршення мо́дуля — Module completion` |
| 167–172 | `### Ва́ше мо́влення` heading + instruction + model lines | HIGH | heading and instruction glossed; model lines glossed (`— I am a student...` etc.) |

### what-is-it-like/lesson-1/module.md

| line | block (before) | severity | after |
| --- | --- | --- | --- |
| 1 | `# Яки́й він?` | HIGH | `# Яки́й він? — What is it like?` |
| 26 | `## Діало́ги` | HIGH | `## Діало́ги — Dialogues` |
| 42–45 | Q&A pair lines (`Яки́й стіл? — Вели́кий стіл.` etc.) | HIGH | per-line English (`— What kind of table? — A big table.` etc.) |
| 107 | `## Яки́й? Яка? Яке́?` | HIGH | `## Яки́й? Яка? Яке́? — What kind?` |
| 127 | `прикме́тники в множині́` (unglossed term inside English sentence) | HIGH | `(adjectives in the plural)` gloss added inline |
| 142 | `### Підсумок уро́ку` | HIGH | `### Підсумок уро́ку — Lesson summary` |
| 144–148 | `Поєдна́йте іме́нник та прикме́тник:` + `чолові́чий рід:` etc. | HIGH | instruction glossed; `(masculine)/(feminine)/(neuter)/(plural)` glosses added |
| 159 | closing line `Тепе́р ви мо́жете ле́гко запита́ти ...` | HIGH | `— now you can easily ask ... and say what they are like.` |

### what-is-it-like/lesson-2/module.md

| line | block (before) | severity | after |
| --- | --- | --- | --- |
| 1 | `# Прикме́тники` | HIGH | `# Прикме́тники — Adjectives` |
| 3 | intro sentence | HIGH | `— in this lesson you will learn to confidently describe objects using pairs of adjectives:` |
| 10–14 | retrieval block (`У попере́дньому уроці ...` + `чолові́чий рід:` etc.) | HIGH | sentence glossed; `(masculine)/(feminine)/(neuter)/(plural)` glosses added |
| 16 | `Тепе́р ми розши́римо словнико́вий запа́с ...` | HIGH | `— now we will expand our vocabulary and learn to describe objects in more detail using antonym pairs.` |
| 18 | `## Прикме́тники` | HIGH | `## Прикме́тники — Adjectives` |
| 49–63 | і/а/але́ example lines (UK-only bullets) | HIGH | per-line glosses (`— The room is big and bright.` etc.) |
| 120–122 | cover-and-answer lines | HIGH | per-line glosses (`— What is the room like? — Small but bright.` etc.) |
| 126 | `### Пильну́й пастки́` | HIGH | `### Пильну́й пастки́ — Watch out for traps` |
| 150 | `### Підсумок уро́ку` | HIGH | `### Підсумок уро́ку — Lesson summary` |
| 153–155 | summary bullets (Анто́німи / Сполу́чники / Украї́нські фо́рми) | HIGH | English sentence appended per bullet, with pair glosses (big — small, clean — dirty, ...) |
| 157 | closing line `У насту́пному уроці ...` | HIGH | `— in the next lesson we will sum up the whole module and reinforce all the patterns for describing objects.` |

### what-is-it-like/lesson-3/module.md

| line | block (before) | severity | after |
| --- | --- | --- | --- |
| 1 | `# Підсумок` | HIGH | `# Підсумок — Summary` |
| 3 | intro sentence | HIGH | `— in this summary lesson you will reinforce everything you know about adjectives and describing objects:` |
| 10–14 | retrieval block + `чолові́чий рід (він):` etc. | HIGH | sentence glossed; gender labels glossed (`він — masculine`, etc.) |
| 16 | `Та́ко́ж ви навчи́лися поє́днувати озна́ки ...` | HIGH | full English sentence appended with і/а/але́ glosses |
| 18 | `## Підсумок` | HIGH | `## Підсумок — Summary` |
| 24–30 | safe-phrase list (`До́брий день.` etc.) | HIGH | per-line glosses (`— Good day.`, `— tasty coffee`, ...) |
| 74–77 | tip box: only the first line had English; the two rule sentences did not | HIGH | per-sentence English added (`The noun always chooses the adjective's ending. ...`) |
| 99–101 | noun-swap lines (`стіл -> телефо́н: нови́й телефо́н`) | HIGH | per-line glosses (`— a new phone`, etc.) |
| 119 | `### Підсумок мо́дуля` | HIGH | `### Підсумок мо́дуля — Module summary` |
| 122–125 | module-summary bullets | HIGH | English sentence appended per bullet |
| 127 | `Віта́ємо з успі́шним заве́ршенням мо́дуля! Тепе́р ...` | HIGH (module-completion praise) | `— Congratulations on successfully completing the module! — now you confidently use ...` |

## Fixed — activities.yaml (activity chrome: titles and instructions)

All six `activities.yaml` files: every Ukrainian-only activity `title:` received an
em-dash English gloss and every Ukrainian-only `instruction:` received the English
translation appended in the same scalar. Item content (`prompt`, `options`,
`answer`, `correct`, `explanation`) untouched — these are response targets, not
instructions. Totals: **66 titles glossed, 45 instructions glossed** (thg L1: 10/5,
L2: 10/7, L3: 10/7; wil L1: 12/7, L2: 12/9, L3: 12/10). Examples:

- `title: Хто чи що?` → `title: Хто чи що? — Who or what?`
- `instruction: Ви́значте, чи пра́вильне тве́рдження про рід іме́нника.` → `... — Decide whether the statement about the noun's gender is correct.`

Activities left unchanged (instruction already English): thg L1 act-1/2/5/3/w1,
thg L2 act-4/w2/w3, thg L3 act-9/w4/w5, wil L1 act-1/2/3/w1/w2, wil L2 act-4/w3/w4,
wil L3 act-w5/w6. All six files re-parse with `yaml.safe_load`.

## Remaining UK-without-EN blocks — none outstanding

A post-fix scan of all six module.md files (Cyrillic line with no Latin, excluding
dialogue boxes and fenced code) finds no learner-facing heading, instruction, recap,
or quiz stem without English. Residual Cyrillic-only lines are all inside reference
tables whose header row is English (`Question | Use it for | Examples`,
`Masculine | Feminine`, `Trap | Say this`, `Noun signal | ...`), which satisfies the
side-by-side table practice.

## By design / notes

- Dialogue boxes stay Ukrainian-only per binding guidance; every dialogue now has an
  English breakdown immediately after it (the two things-have-gender L3 dialogues
  gained new breakdown tables; all others already had them).
- `_unsupported_uk_runs` (linear_pipeline) with the band's `max_unsupported=68`,
  `proximity=8` reports zero offending runs for 5 of 6 module.md files. The
  pre-existing exception is what-is-it-like L3's two-part concluding dialogue
  (~90 UK words inside the quote box), which is the designated dialogue-floor
  pattern with an immediate UK|EN breakdown; unchanged from HEAD, not introduced
  by this pass.
- No Ukrainian forms were added or altered beyond copying existing dialogue lines
  into the two new breakdown tables; all added text is English scaffolding.
- Assembled MDX regenerated for both modules (`site/src/content/docs/a1/...`),
  `validated=False` (draft), matching the previous assembly invocation.
