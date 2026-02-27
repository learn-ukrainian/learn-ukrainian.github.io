Confirmed: Latin 'o' (U+006F) in "хтoнічний" instead of Cyrillic 'о' (U+043E). Now I have everything for the full review.

---

## Deep Adversarial Review: knyahynia-olha (c1-bio #1)

### Word Count
5461 words vs 5000 target. **PASS** (exceeds minimum by 9%).

### Russian Characters Check
No ы, э, ё, ъ found. **CLEAN**.

### No Russianisms detected. **CLEAN**.

---

### Issues Found

**ISSUE 1 — GRAMMAR: Broken sentence structure (content, line 24)**
> "Її сприймали як самостійну фігуру, рівну чоловікам, а повноправним політичним гравцем."

The "а повноправним політичним гравцем" is grammatically broken. After "сприймали як" (accusative), the second element with "а" needs parallel case (accusative "гравця", not instrumental "гравцем") and the construction needs "не просто...а як" to work.

**ISSUE 2 — GRAMMAR: Wrong case after "від" (content, line 56)**
> "створити безперервну династичну лінію від Рюрику"

"Від" requires genitive. "Рюрику" is dative/locative. Correct: "від Рюрика".

**ISSUE 3 — GRAMMAR: Wrong locative form of patronymic (content, line 22)**
> "при малолітньому сині Святославі Ігоровичі"

Locative singular of "Ігорович" is "Ігоровичу" (or "Ігоровичеві"), not "Ігоровичі" (which would be nominative plural).

**ISSUE 4 — TYPO: Non-word "можутьністю" (content, line 150)**
> "Такий масштаб мав вразити греків багатством і можутьністю"

"Можутьністю" is not a Ukrainian word. Correct: "могутністю" (instrumental of "могутність").

**ISSUE 5 — TYPO: "цервою" in activities YAML (line 81)**
> "Ольгу було канонізовано цервою як рівноапостольну святу."

"Цервою" → "церквою". Also flagged by Green Team.

**ISSUE 6 — FORMATTING: Missing space after period (content, line 209)**
> "Європу.Її спроби налагодити"

Missing space between sentences.

**ISSUE 7 — MIXED SCRIPT: Latin 'o' in Cyrillic word (content, line 66)**
> "в хт**o**нічний, підземний світ"

Confirmed Latin U+006F instead of Cyrillic U+043E. Invisible to readers but breaks text search and automated tooling.

**ISSUE 8 — PUNCTUATION: Missing comma before дієприслівниковий зворот (content, line 90)**
> "Ользі довелося боротися з цим відцентровим рухом поєднуючи військову силу"

Per Ukrainian punctuation rules, comma required before "поєднуючи" (adverbial participle clause).

**ISSUE 9 — VOCABULARY IPA: автократор uses /u̯/ not /ʋ/ for В (vocab, line 9)**
> ipa:

The file uses /ʋ/ for В consistently elsewhere (e.g., "ловища"). This entry should use for consistency. The QA spec explicitly requires "ʋ not w for В".

**ISSUE 10 — VOCABULARY: "ловища" lemma should be singular (vocab, line 31)**
Lemma is "ловища" (plural) but gender says "n" (neuter singular). Lemma should be "ловище". IPA stress is also wrong: (first syllable) should be (second syllable, with /ɛ/ for neuter singular ending).

**ISSUE 11 — VOCABULARY IPA: "знамення" stress on wrong syllable (vocab, line 39)**
> ipa:

Stress should be on the second syllable: (знамéння).

**ISSUE 12 — STYLISTIC: "детектив" cliché (content, lines 32, 40)**
> "Робота історика тут нагадує роботу детектива"
> "### Проблема походження: детективне розслідування"

LLM-typical metaphor, also flagged by Green Team.

**ISSUE 13 — ODD WORD CHOICE: "біологи" in self-check question (content, line 217)**
> "Чому сучасні історики та біологи сумніваються"

"Біологи" (biologists) is an odd companion to "historians" in a history self-check. The argument is demographic, not biological. "Демографи" fits better.

**ISSUE 14 — QUOTATION MARKS: Straight quotes in mixed text (content, line 182)**
> «христианської "партії" при дворі»

The rest of the module uses «лапки» consistently. This one instance uses straight double quotes.

**ISSUE 15 — FACTUAL PRECISION: "Гарольда Суворого" (content, line 78)**
> "зокрема про Гарольда Суворого, який воював на Сицилії"

The Ukrainian historiographic form of Harald Hardrada is "Гаральд Суворий" (from Norse Haraldr), not the anglicized "Гарольд". For a C1 Ukrainian history text, use the standard Ukrainian form.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
Її сприймали як самостійну фігуру, рівну чоловікам, а повноправним політичним гравцем.
---NEW---
Її сприймали не просто як самостійну фігуру, рівну чоловікам, а як повноправного політичного гравця.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
при малолітньому сині Святославі Ігоровичі після
---NEW---
при малолітньому сині Святославі Ігоровичу після
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
створити безперервну династичну лінію від Рюрику.
---NEW---
створити безперервну династичну лінію від Рюрика.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
вразити греків багатством і можутьністю «північних варварів».
---NEW---
вразити греків багатством і могутністю «північних варварів».
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
в хтoнічний, підземний світ
---NEW---
в хтонічний, підземний світ
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
інтеграції в християнську Європу.Її спроби
---NEW---
інтеграції в християнську Європу. Її спроби
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
Ользі довелося боротися з цим відцентровим рухом поєднуючи військову силу
---NEW---
Ользі довелося боротися з цим відцентровим рухом, поєднуючи військову силу
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
Робота історика тут нагадує роботу детектива, який мусить відділити правду від пізніших нашарувань.
---NEW---
Завдання дослідника — відділити документально підтверджені факти від пізніших нашарувань та ідеологічних інтерпретацій.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
### Проблема походження: детективне розслідування
---NEW---
### Проблема походження: суперечливі версії
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
4. Чому сучасні історики та біологи сумніваються у літописній даті шлюбу
---NEW---
4. Чому сучасні історики та демографи сумніваються у літописній даті шлюбу
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
без створення християнської "партії" при дворі
---NEW---
без створення християнської «партії» при дворі
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
---OLD---
зокрема про Гарольда Суворого, який воював на Сицилії
---NEW---
зокрема про Гаральда Суворого, який воював на Сицилії
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/activities/knyahynia-olha.yaml
---OLD---
    - statement: "Ольгу було канонізовано цервою як рівноапостольну святу."
---NEW---
    - statement: "Ольгу було канонізовано церквою як рівноапостольну святу."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/vocabulary/knyahynia-olha.yaml
---OLD---
    ipa:
---NEW---
    ipa:
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/vocabulary/knyahynia-olha.yaml
---OLD---
  - lemma: ловища
    translation: hunting grounds
    pos: noun
    gender: n
    ipa:
---NEW---
  - lemma: ловище
    translation: hunting ground
    pos: noun
    gender: n
    ipa:
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/vocabulary/knyahynia-olha.yaml
---OLD---
    ipa:
---NEW---
    ipa:
===FIX_END===

---

### Strengths (not rubber-stamping — these are genuine)
- Deep, analytically rich content well beyond surface-level biography
- Strong decolonization framing with concrete evidence (Moscow founded 1147, Pliska hypothesis)
- All plan hooks present: [!myth-buster], [!culture], [!context], [!history-bite], [!decolonization], [!quote]
- Factual dates, names, and source attributions are accurate (De Ceremoniis, Continuatio Reginonis, Adalbert/Libuziy sequence)
- Activities are well-designed: reading+critical-analysis chain, comparative study, essay prompt, 12-item true-false
- 100% Ukrainian immersion, no English leakage in prose
- All three plan objectives map clearly to self-check questions

### Remaining Notes (not fixing, just documenting)
- Plan vocabulary_hints lists "становище" as recommended — word absent from prose (concept covered via "знамення" and "ловища")
- SCOPE line 5 says "Related: c1-bio-01 (Олег)" while plan says "prerequisites: c1-bio-01 (Олег Віщий)" — contradicts sequence: 1 assignment. Metadata inconsistency in plan, not content.

===VERDICT===
APPROVE
===END_VERDICT===