## Linguistic Scan
No linguistic errors found (Russianisms, Surzhyk, Calques). However, the writer manually inserted acute accents (stress marks) on most Ukrainian words throughout the text (e.g., `Скі́льки`, `су́мка`, `ко́шту́є`, `Іри́на`). A double stress mark on `ко́шту́є` resulted in a typo. Stress annotation is strictly handled by the pipeline after the review phase, so these manual marks must be removed.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-demonstratives-this -->` (Matches plan hint 1)
- `<!-- INJECT_ACTIVITY: fill-in-demonstratives-this -->` (Unplanned extra activity)
- `<!-- INJECT_ACTIVITY: quiz-demonstratives-that -->` (Matches plan hint 4)
- `<!-- INJECT_ACTIVITY: match-up-gender-paradigm -->` (Matches plan hint 3)
- `<!-- INJECT_ACTIVITY: fill-in-demonstratives-contrast -->` (Matches plan hint 2)

**Issue**: The plan specifies exactly 4 `activity_hints`. The text contains 5 marker injections. The extra `fill-in-demonstratives-this` marker breaks the planned structure and must be removed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Missed the word count target (1366 words is 13.8% over the 1200 target, max allowed is 1320). Added an extra activity marker that was not in the plan. Covered all outline points well. |
| 2. Linguistic accuracy | 9/10 | Ukrainian sentences are perfectly natural and grammatically correct. Deducted 1 point for the typo created by a double manual stress mark in `ко́шту́є`. |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow. Clear contrast between "this" and "that", properly integrated Заболотний textbook reference, and highly effective explanations linking new demonstratives to previously learned gender patterns. |
| 4. Vocabulary coverage | 8/10 | Covered required vocabulary well, but missed two recommended plan items: `тут` and `він, вона, воно`. |
| 5. Exercise quality | 8/10 | Injected a 5th activity marker (`fill-in-demonstratives-this`) that does not exist in the plan's 4 `activity_hints`. |
| 6. Engagement & tone | 10/10 | Great teacher tone, highly specific situational context, no generic fluff. The showroom and store scenarios work perfectly. |
| 7. Structural integrity | 7/10 | The text is littered with manual acute accents (stress marks) despite the prompt rule that "their absence is correct" as stress is handled downstream. Also exceeds the strict +10% word count ceiling. |
| 8. Cultural accuracy | 10/10 | Natural interactions, culturally appropriate use of the Hryvnia, and solid equative sentence patterns. |
| 9. Dialogue & conversation quality | 10/10 | Conversations between Iryna and the shop assistant are natural, utilizing the target grammar effectively and efficiently. |

## Findings

[Structural integrity] [Minor]
Location: Throughout the text (e.g., `Скі́льки ко́шту́є ця су́мка?`, `Іри́на walks into`)
Issue: The writer manually inserted acute accents (stress marks) on most Ukrainian words. This led to a double-stress typo on `ко́шту́є` and violates the rule that stress annotation is handled deterministically by a downstream tool. 
Fix: Strip all manual acute accents from the Ukrainian words.

[Structural integrity] [Minor]
Location: Document length (1366 words)
Issue: The module exceeds the 1200-word target by 13.8%, which is outside the strict 10% upper limit (1320 max).
Fix: Trim redundant filler about English word order and the congratulatory paragraph at the end to bring the word count into compliance.

[Exercise quality] [Major]
Location: `<!-- INJECT_ACTIVITY: fill-in-demonstratives-this -->`
Issue: An extra activity marker was injected that does not correspond to the 4 activities specified in the plan's `activity_hints`.
Fix: Remove the extra marker.

[Vocabulary coverage] [Major]
Location: `Той, та, те (That)` section
Issue: The recommended vocabulary words `тут` and `він, вона, воно` are missing from the text, despite being requested in the plan.
Fix: Integrate these words into the explanation of pointing words (`ось` and `там`).

## Verdict: REVISE
The module content is fundamentally excellent, with natural dialogues and strong pedagogy. However, it exceeds the strict word count limit, includes an unplanned extra activity marker, misses two recommended vocabulary items, and contains formatting artifacts (manual stress marks leading to a typo). The deterministic fixes below resolve these issues.

<fixes>
- find: "## Діало́ги (Dialogues)"
  replace: "## Діалоги (Dialogues)"
- find: "Іри́на walks into"
  replace: "Ірина walks into"
- find: "Скі́льки ко́шту́є ця су́мка?"
  replace: "Скільки коштує ця сумка?"
- find: "Яка? Ця черво́на?"
  replace: "Яка? Ця червона?"
- find: "Ні, та си́ня."
  replace: "Ні, та синя."
- find: "Та коштує дві́сті гри́вень."
  replace: "Та коштує двісті гривень."
- find: "А цей рюкза́к?"
  replace: "А цей рюкзак?"
- find: "Цей — сто п'ятдеся́т."
  replace: "Цей — сто п'ятдесят."
- find: "До́бре, беру́ цей рюкзак."
  replace: "Добре, беру цей рюкзак."
- find: "Те — крі́сло."
  replace: "Те — крісло."
- find: "Цей стіле́ць нови́й, а той — стари́й."
  replace: "Цей стілець новий, а той — старий."
- find: "Так, цей зру́чний, а той — ні."
  replace: "Так, цей зручний, а той — ні."
- find: "мій/моя́/моє́"
  replace: "мій/моя/моє"
- find: "яки́й/яка/яке́"
  replace: "який/яка/яке"
- find: "Ця кни́га (f)"
  replace: "Ця книга (f)"
- find: "Це вікно́ (n)"
  replace: "Це вікно (n)"
- find: "вказівні́ займе́нники цей, той змі́нюються"
  replace: "вказівні займенники цей, той змінюються"
- find: "Заболо́тний (Grade 6, p. 210)"
  replace: "Заболотний (Grade 6, p. 210)"
- find: "Цей телефо́н (m)"
  replace: "Цей телефон (m)"
- find: "Цей оліве́ць (m)"
  replace: "Цей олівець (m)"
- find: "Ця ка́мера (f)"
  replace: "Ця камера (f)"
- find: "Ця ру́чка (f)"
  replace: "Ця ручка (f)"
- find: "Це ра́діо (n)"
  replace: "Це радіо (n)"
- find: "Це мі́сто (n)"
  replace: "Це місто (n)"
- find: "Цей вели́кий черво́ний стіл."
  replace: "Цей великий червоний стіл."
- find: "Ця нова́ синя сумка."
  replace: "Ця нова синя сумка."
- find: "Це мале́ньке бі́ле вікно."
  replace: "Це маленьке біле вікно."
- find: "Цей рюкзак си́ній, а той — чо́рний."
  replace: "Цей рюкзак синій, а той — чорний."
- find: "Це крісло зру́чне, а те — ні."
  replace: "Це крісло зручне, а те — ні."
- find: "ма́ма та та́то"
  replace: "мама та тато"
- find: "Та книга ціка́ва."
  replace: "Та книга цікава."
- find: "Ірина та Макси́м"
  replace: "Ірина та Максим"
- find: "Це вели́ке чи те маленьке?"
  replace: "Це велике чи те маленьке?"
- find: "чи ___ ноутбу́к (on that shelf)?"
  replace: "чи ___ ноутбук (on that shelf)?"
- find: "The pointing word **ось** (here is / look) and the adverb **там** (there) pair naturally with demonstratives: **Ось цей телефон — дороги́й.** (Here, this phone — expensive.) **А той, там, — ні.** (And that one, over there — no.)"
  replace: "The pointing words **ось** (look) and **тут** (here), along with **там** (there), pair naturally with demonstratives: **Ось цей телефон тут — дорогий.** (Look, this phone here — expensive.) **А той, там, — ні.** (And that one, over there — no.) You can also use **він, вона, воно** to refer back to them."
- find: "<!-- INJECT_ACTIVITY: fill-in-demonstratives-this -->\n\n"
  replace: ""
- find: "Ukrainian word order is more flexible than English in general, but demonstrative + adjective + noun is the most natural, unmarked order. At A1, stick with this pattern and it will always sound right.\n\n"
  replace: ""
- find: "If you can point at objects around you and name them with the right demonstrative and gender — congratulations, you are thinking in Ukrainian. The gender system that seemed like three separate sets of words in Modules 6, 9, and now 12 is really one pattern repeated. Every new word you learn simply plugs into this system."
  replace: "The gender system that seemed like three separate sets of words in Modules 6, 9, and now 12 is really one consistent pattern repeated."
</fixes>
