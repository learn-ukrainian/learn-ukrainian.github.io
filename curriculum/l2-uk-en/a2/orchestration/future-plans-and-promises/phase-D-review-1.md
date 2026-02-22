**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Plan Alignment | 9/10 | All 5 planned sections present as H2. All required vocabulary items covered. All 4 learning objectives addressed. Minor gap: «приїду» from required vocab not explicitly taught in 1st person (only 3rd person «приїдуть» in dialogue). |
| 2 | Language Quality | 7/10 | Critical terminological error: «складний час» (complex/difficult time) used instead of «складений час» (compound time) on lines 33, 116, 136, 148 — while the heading on line 114 correctly uses «складеного часу». The State Standard (§4.2.3.1) uses «складена форма». This inconsistency will confuse learners. Otherwise, Ukrainian prose is grammatically sound and English is clear. |
| 3 | Activity Quality | 7/10 | Match-up activity pairs «Я буду дивитися» with «Я побачу» — these are NOT aspect pairs (дивитися→подивитися, бачити→побачити). The correct form «подивлюся» already appears as a distractor in the first fill-in activity (line 31), proving the builder knew the correct form. Additionally, unjumble answer on line 665 missing mandatory comma: «Я обіцяю що знайду» should be «Я обіцяю, що знайду». Otherwise excellent: 12 activities, 10 distinct types, ~100 total items, well-crafted distractors. |
| 4 | Lesson Quality | 8/10 | Strong opening with «Віта́ю!» and cultural hook. Clear preview of learning goals. Good practice dialogues with named characters. Production task at the end. However, several dense Ukrainian-only paragraphs (lines 39, 110, 157-160, 240) run 80-150 words without visual breaks, which could overwhelm A2 learners. Persona specified as "Ambitious Startup Founder" in meta but not reflected in content voice — reads as standard grammar tutor. |
| 5 | Richness | 8/10 | Two authentic proverbs: «Обіцянка — цяцянка, а дурневі — радість» and «Обіцяного три роки ждуть». Named characters (Олена, Антон, Максим, Анна) in dialogues. Professional context (workplace promises). Cultural frame of «тримати слово». Solid but standard — no unexpected or surprising cultural connections. |
| 6 | Immersion Balance | 9/10 | Pre-computed 51.1%, within the 50-60% Band 1 target. English used appropriately for abstract grammatical explanations. Ukrainian used for examples, dialogues, and contextual prose. Well-calibrated transitions between languages. |
| 7 | Factual Accuracy | 7/10 | Two factual errors: (1) «складний» ≠ «складений» — using the wrong Ukrainian linguistic term for compound tense, contradicting the State Standard; (2) match-up activity treats дивитися/побачити as an aspect pair, which is factually wrong. Grammar rules for aspect in future tense are otherwise accurately explained. The «буду + perfective» prohibition is correctly taught and well-illustrated. |
| 8 | LLM Fingerprint | 8/10 | Section openings are varied (no 3+ identical starts). Example formats vary across sections (bullet lists, dialogues, contrast pairs, tables). One instance of «не просто X, а Y» rhetorical pattern on line 229: «ви не просто пасивний спостерігач майбутніх подій, а людина, яка діє і приносить результати». Dense Ukrainian closing blocks in sections «Вступ», «Презентація: Доконаний вид», «Презентація: Недоконаний вид», and «Висновок та застосування» follow a repetitive formula (restate concept → everyday example → encouragement), but this is not extreme. |
| 9 | Humanity & Warmth | 8/10 | Good warmth markers: «Вітаю!» opening, frequent «ви» direct address, «Бажаю успіхів у навчанні та комунікації!» closing. Encouragement in dialogues («Чудово!»). Cultural framing makes grammar feel meaningful. Could benefit from 1-2 more explicit "don't worry" moments — the aspect mismatch warning (line 96) is stern without reassurance. |

---

## Critical Issues Found

### Issue 1: WRONG ASPECT PAIR in Match-Up Activity (CRITICAL — Activity Error)

**Location:** Activities file, lines 371-372

**Evidence:** The match-up activity pairs:
```
left: Я буду дивитися
right: Я побачу
```

**Problem:** «дивитися» (to watch/look) and «побачити» (to see) are **different verbs**, not an aspect pair. The correct morphological pairs are:
- дивитися (imperf.) → **подивитися** (perf.) — to watch/look at
- бачити (imperf.) → побачити (perf.) — to see

The builder demonstrably knew the correct form — «подивлюся» appears as a distractor option in the very first fill-in item (line 31). This error teaches learners an incorrect aspect pair relationship.

**Fix:** Change the pair to either:
- `left: Я буду дивитися` / `right: Я подивлюся` (correct morphological pair), OR
- `left: Я буду бачити` / `right: Я побачу` (correct morphological pair, though «буду бачити» is rare)

The first option is strongly preferred.

---

### Issue 2: TERMINOLOGICAL ERROR — «складний» vs «складений» (CRITICAL — Language/Factual)

**Location:** Content file, lines 33, 116, 136, 148

**Evidence (line 33):** «The Compound Future (Складний час)»
**Evidence (line 116):** «Тоді ви повинні використовувати складний майбутній час.»
**Evidence (line 136):** «Складний майбутній час фокусується на тривалості.»
**Evidence (line 148):** «Складний майбутній час структурно імітує англійське "will + дієслово".»

**Contradiction:** The heading on line 114 correctly uses «Форма складеного часу» (genitive of «складений»). The State Standard (per research file line 4) uses «складена форма майбутнього часу».

**Problem:** «складний» means "complex, difficult" — «складений» means "compound, composed." These are different Ukrainian words. Using «складний» to mean "compound" is a lexical error that contradicts the State Standard and will confuse learners who later encounter the correct term in other resources.

**Fix:** Replace all instances of «складний час/складний майбутній час» with «складений час/складений майбутній час» to match the heading on line 114 and the State Standard.

---

### Issue 3: MISSING COMMA in Unjumble Activity (MINOR — Punctuation Error)

**Location:** Activities file, line 665

**Evidence:** `answer: Я обіцяю що знайду правильне рішення`

**Problem:** Ukrainian punctuation requires a comma before the conjunction «що» introducing a subordinate clause. The correct answer should be «Я обіцяю, що знайду правильне рішення». Teaching an answer without the mandatory comma reinforces incorrect punctuation habits.

**Fix:** Change answer to `Я обіцяю, що знайду правильне рішення`.

---

### Issue 4: QUESTIONABLE PEDAGOGICAL PAIR in Section «Практика та діалоги» (MINOR)

**Location:** Content file, lines 208-209

**Evidence (line 208):** «*Намір:* Ми бу́демо виходити на вулицю. (We will be going out to the street.)»
**Evidence (line 209):** «*Результат:* Я ви́йду на п'ять хвилин. (I will step out for five minutes.)»

**Problem:** This pair shifts both pronoun (Ми→Я) and semantic context (habitual going out → single brief exit), making it a poor pedagogical illustration of the process→result transformation. The other pairs in this section maintain the same subject and clearly transform intent into result.

**Fix:** Normalize the pair: «*Намір:* Я бу́ду виходити на вулицю.» → «*Результат:* Я ви́йду на вулицю на п'ять хвилин.» (same subject, clearer transformation).

---

### Issue 5: DENSE UKRAINIAN BLOCKS at A2 Level (MODERATE — Pacing)

**Location:** Content file, lines 39, 110, 157-160, 240

**Evidence (line 39):** A single unbroken Ukrainian paragraph of ~130 words beginning with «Коли ми говоримо про майбутнє, ми завжди думаємо про наші дії.»

**Evidence (line 160):** A single Ukrainian paragraph of ~180 words beginning with «Давайте розглянемо ще кілька цікавих ситуацій для недоконаного виду.»

**Problem:** At A2 level, Ukrainian-only paragraphs exceeding ~80 words without visual breaks (subheadings, bullet points, bold key terms) risk overwhelming learners. These blocks restate concepts already explained in the bilingual sections above them, adding volume but limited new pedagogical value. Section «Презентація: Недоконаний вид» is the worst offender with two consecutive dense blocks (lines 157 and 160) totaling ~300 words of unbroken Ukrainian.

**Fix:** Break long Ukrainian paragraphs into shorter chunks (40-60 words max). Add bold key terms or inline formatting. Consider converting the vacation-planning example (line 160) into a second dialogue rather than prose narrative.

---

## Factual Verification

### Grammar Rules — VERIFIED with exceptions

| Rule | Verdict | Notes |
|------|---------|-------|
| Perfective verbs form simple future via present-tense conjugation | CORRECT | Accurately explained on lines 45-49 |
| «буду» + perfective infinitive is always wrong | CORRECT | Well-taught on lines 94-108 with clear error table |
| Compound future = «буду» + imperfective infinitive | CORRECT | Accurately explained on lines 118-127 |
| «складний час» = compound future tense | **INCORRECT** | Should be «складений час» per State Standard §4.2.3.1 |

### Cultural Claims — VERIFIED

| Claim | Verdict | Notes |
|-------|---------|-------|
| «Обіцянка — цяцянка, а дурневі — радість» proverb and meaning | CORRECT | Standard Ukrainian proverb, correctly glossed |
| «Обіцяного три роки ждуть» proverb | CORRECT | Standard proverb, usage context accurate |
| «тримати слово» as cultural value | CORRECT | Well-established cultural concept |
| «цяцянка» = small children's toy | CORRECT | Accurate etymology from «цяця» |

### Activity Factual Accuracy

| Item | Verdict | Notes |
|------|---------|-------|
| Match-up: дивитися → побачу | **INCORRECT** | Not an aspect pair. дивитися → подивитися |
| Match-up: йти → піду | BORDERLINE | Technically valid (йти → піти) but «буду йти» is uncommon in natural speech |
| Match-up: шукати → знайду | ACCEPTABLE | Not morphological pair but intentional semantic process→result pair, consistent with content line 205-206 |
| Unjumble: «Я обіцяю що...» | **PUNCTUATION ERROR** | Missing comma before «що» |

---

## Verification Summary

| Check | Result |
|-------|--------|
| All H2 sections from plan present | PASS — All 5: «Вступ», «Презентація: Доконаний вид», «Презентація: Недоконаний вид», «Практика та діалоги», «Висновок та застосування» |
| Required vocabulary items present | PASS — 14/15 required items explicitly used. «приїду» appears only as 3rd person «приїдуть» (line 173), not explicitly in 1st person paradigm |
| Learning objectives addressed | PASS — All 4 objectives covered (compound future formation, simple future formation, process/result distinction, promises vs plans) |
| Colonial framing check | PASS — No Russian comparisons found. Content frames Ukrainian aspect system on its own terms |
| Russianisms check | PASS — No Russianisms detected |
| Word count | PASS — 3058/3000 (101.9%) |
| Activity count | PASS — 12 activities |
| Engagement boxes | PASS — 4 boxes ([!note], [!warning], [!tip], [!culture]) |
| Immersion | PASS — 51.1% within 50-60% target |
| Section references in review | PASS — All 5 H2 sections referenced by Ukrainian name |

---

## Verdict

**NEEDS REPAIR** — 2 critical issues, 3 moderate/minor issues.

The module has strong pedagogical foundations: excellent activity variety (10 distinct types, ~100 items), authentic cultural hooks, and accurate core grammar teaching. The aspect mismatch prohibition is particularly well-taught with clear examples and an error table. However, two issues require mandatory fixes before approval:

1. **Match-up aspect pair error** (дивитися/побачити) — teaches incorrect linguistic knowledge
2. **Terminological error** (складний/складений) — contradicts State Standard, appears 4 times

Additionally recommended: fix the unjumble punctuation, normalize the pronoun-shifting process→result pair in section «Практика та діалоги», and break up dense Ukrainian paragraphs in sections «Вступ», «Презентація: Недоконаний вид», and «Висновок та застосування» for A2-appropriate pacing.