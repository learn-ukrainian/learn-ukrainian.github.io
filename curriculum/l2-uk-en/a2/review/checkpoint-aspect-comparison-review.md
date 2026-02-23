<!-- content-hash: edcc5bbc1393 -->
**Reviewed-By:** claude-opus-4-6

# Phase D.1 Review: checkpoint-aspect-comparison (A2-M25)

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Plan Compliance | 9/10 | All 5 plan sections present as H2s. Vocabulary scope matches required/recommended lists. No grammar scope creep. Minor: content adds "Навичка N:" prefixes not in plan — acceptable enhancement. |
| 2 | Language Quality | 7/10 | Gender agreement error on line 29 (feminine noun with masculine adjective). Spelling error "Умовий" (line 265) missing "н". Both in Ukrainian pedagogical text where grammar accuracy is paramount. |
| 3 | Factual Accuracy | 8/10 | Grammar rules correctly presented. The "більш добрий" claim (line 159) is supported by research notes but pedagogically questionable. Activity explanation (activities:125) overgeneralizes "зробити вибір завжди вимагає доконаного виду" while the lesson itself uses "робити вибір" imperfectively. |
| 4 | Activity Quality | 7/10 | 12 activities with good variety. Critical: error-correction activity titled "Зіткнення числівників" (activities:270) has first 2 items testing aspect, not numeral collision. Two unjumble answers missing required commas (activities:259, 267). |
| 5 | Vocabulary Quality | 8/10 | 31 items with IPA, pos, aspect, notes. Two IPA errors: "вчасно" uses ʍ phoneme (vocab:56), "родовий" has double stress mark (vocab:140). |
| 6 | Richness | 9/10 | Hospitality cultural hook, proverb integration «Краще пізно, ніж ніколи», house-building metaphor, synthesis dialogue with 12-point analysis, event planning challenge. Named characters (Олена, Марко). Varied callout types (8 boxes, no duplicated titles). |
| 7 | Lesson Quality | 8/10 | 4/5 on "Would I Continue?" test. Warm opening «Вітаю вас на цьому важливому етапі!» and celebration ending «Ви виконали величезну роботу!». However, mid-section encouragement is sparse — Sections «Навичка 2» and «Навичка 3» lack any warmth markers between intro and callout boxes. |
| 8 | Immersion | 8/10 | 59.6% vs target 60-75%. Marginally below floor. English is appropriately used for abstract grammar theory, Ukrainian for examples/dialogues — this is the correct A2 Band 2 strategy. Needs ~10 more words converted to Ukrainian to cross threshold. |
| 9 | LLM Fingerprint | 9/10 | Section openings are varied (Ukrainian welcome, English pedagogical frame, transitional hook, structural overview, Ukrainian summary). No "це не просто" patterns. Callout variety is excellent (tip, warning, note, fact, culture). Example formats vary (bullet lists, tables, dialogues, numbered analyses). |
| 10 | Humanity & Warmth | 8/10 | Direct address "ви" used throughout. Welcome marker present. Progress celebration at end. Missing: "don't worry" moments (0 found — need ≥2), and only 1 explicit "You can now..." validation in the closing. |

## Critical Issues Found

### Issue 1: Gender Agreement Error (Content line 29)
**Severity:** Critical — grammar error in pedagogical text about grammar

In Section «Навичка 2: Ступені порівняння: Від якості до досконалості», line 29:

> «Ми зазвичай кажемо, що річ є **добрий**.»

The noun "річ" is feminine (ж. р.) in Ukrainian. The predicate adjective must agree in gender: "є **добра**", not "є **добрий**" (masculine). A gender agreement error in a grammar checkpoint module is particularly damaging to learner trust.

**Fix:** Change «що річ є **добрий**» → «що річ є **добра**» on content line 29.

### Issue 2: Spelling Error "Умовий" (Content line 265)
**Severity:** Critical — misspelled grammatical term

In Section «Навичка 3: Модальність та узгодження числівників», line 265:

> «Бачите, як елементи поєднуються? Умовий спосіб задає гіпотетичну ситуацію, числівники вимагають точних відмінків, а прикметники дозволяють зробити оцінку.»

"Умовий" is not a word. The correct term is "Умовний" (conditional). The same term is correctly spelled earlier on line 207: «**Умовний спосіб — Conditional Mood**».

**Fix:** Change «Умовий спосіб» → «Умовний спосіб» on content line 265.

### Issue 3: Mislabeled Error-Correction Activity (Activities lines 269-302)
**Severity:** Critical — pedagogically confusing

The activity titled «Виправте помилки: Зіткнення числівників» (activities:270) claims to test numeral collision errors. However, the first two items test **verbal aspect errors**, not numeral agreement:

- Item 1 (activities:273): «Я зроблю це завдання прямо зараз.» — error is perfective in present tense
- Item 2 (activities:278): «Він купить каву в цей самий момент.» — error is perfective in present tense
- Items 3-6 (activities:283-302): actual numeral agreement errors

A learner reading "Виправте помилки: Зіткнення числівників" will expect all items to be about numeral collision. Finding aspect errors first will cause confusion.

**Fix:** Either (a) rename the activity to «Виправте помилки: Вид дієслова та числівники» to reflect both topics, or (b) move items 1-2 to a separate error-correction activity for aspect.

### Issue 4: Activity Explanation Contradicts Lesson Content (Activities line 125)
**Severity:** Moderate — factually incorrect explanation

The fill-in activity (activities:122-125) asks learners to complete: «Вони довго думали, як правильно ___ вибір.» The correct answer "зробити" is fine for this sentence. However, the explanation states:

> «Сталий вираз 'зробити вибір' завжди вимагає доконаного виду.»

This directly contradicts content line 81 in Section «Навичка 1: Вид дієслова: Процес та результат»:

> «Ми довго думали, як **робити вибір** у цій складній ситуації. (We thought for a long time about how to be making a choice... — Focus on the process.)»

The lesson explicitly teaches that "робити вибір" (imperfective) is valid when focusing on the process. The activity explanation claiming it "always requires perfective" is wrong.

**Fix:** Change explanation to: «Слово 'правильно' вказує на фокус на кінцевому результаті вибору, тому тут краще доконаний вид.»

### Issue 5: Missing Commas in Unjumble Answers (Activities lines 259, 267)
**Severity:** Moderate — punctuation errors in answer keys

Two unjumble answers are missing required commas:

1. Activities line 259: «Якби ми мали час ми зробили б це.» — missing comma after «час» (subordinate clause boundary)
2. Activities line 267: «Краще пізно ніж ніколи але краще вчасно.» — missing commas before «ніж» and before «але»

Correct answers should be:
1. «Якби ми мали час, ми зробили б це.»
2. «Краще пізно, ніж ніколи, але краще вчасно.»

### Issue 6: IPA Errors in Vocabulary (Vocab lines 56, 140)
**Severity:** Moderate — incorrect phonetic transcription

1. **вчасно** (vocab:56): IPA `[ˈʍt͡ʃɑsnɔ]` — The symbol ʍ (voiceless labial-velar fricative) is not a Ukrainian phoneme. Before voiceless /t͡ʃ/, Ukrainian /ʋ/ is realized as [u̯] (non-syllabic vowel) or [f] in rapid speech. Correct: `[ˈu̯t͡ʃɑsnɔ]` or `[ˈft͡ʃɑsnɔ]`.

2. **родовий** (vocab:140): IPA `[rɔˈdɔˈʋɪj]` has two primary stress marks. Ukrainian words have only one primary stress. Correct: `[rɔdɔˈʋɪj]`.

## Factual Verification

| Claim | Location | Status | Notes |
|-------|----------|--------|-------|
| Present tense is exclusively Imperfective | Content line 56 | **Correct** | Matches State Standard §4.2.3.1 and research notes |
| Simple comparative formed with -іш-/-ійш- | Content line 134 | **Correct** | Standard formation rule |
| Compound comparative with більш/менш | Content line 141 | **Correct** | §4.3.1 confirmed |
| Double comparative is an error | Content line 156 | **Correct** | Research notes confirm |
| Irregular: добрий → кращий | Content line 171 | **Correct** | Standard suppletive form |
| Irregular: великий → більший | Content line 173 | **Correct** | Standard suppletive form |
| Conditional formed with past tense + би/б | Content line 208 | **Correct** | Standard formation rule |
| 1-2-5 Rule: 2-4 = Nominative Plural | Content line 238 | **Correct** | §4.2.1.3 confirmed |
| 1-2-5 Rule: 5+ = Genitive Plural | Content line 245 | **Correct** | §4.2.1.3 confirmed |
| «Краще пізно, ніж ніколи» is a real proverb | Content line 186 | **Correct** | Well-known Ukrainian proverb |
| Imperfective imperative for hospitality | Content lines 112-116 | **Correct** | Culturally accurate pedagogical insight |
| «більш добрий» is grammatically possible | Content line 159 | **Debatable** | Research notes list it as correct. Most grammarians prefer suppletive "кращий" exclusively. Module's caveat "(менш вживано)" is adequate. |

**Callout Box Verification:**
- [!tip] Порада для навчання (line 45): General learning advice — no factual claims. **OK**
- [!warning] Уникайте цієї помилки! (line 70): Correctly flags perfective in present tense. **OK**
- [!note] Зверніть увагу (line 91): "вчасно" as perfective marker — reasonable pedagogical claim. **OK**
- [!fact] Лінгвістичний факт (line 149): Claims Ukrainian prefers simple comparative forms — this is accurate for colloquial speech. **OK**
- [!warning] Запам'ятайте назавжди! (line 162): Double comparative prohibition — factually correct. **OK**
- [!tip] Ввічливість (line 214): Conditional for politeness — culturally accurate. **OK**
- [!warning] Уникайте зіткнення числівників! (line 251): 1-2-5 rule summary — correct. **OK**
- [!culture] Культурний контекст у діалозі (line 299): Imperfective for workplace invitations — accurate and well-attributed to Олена. **OK**

**No fabricated claims found.** All callout boxes check out.

**Colonial Framing Check:** No instances of "Unlike Russian", "Different from Russian", or Russian-baseline comparisons found. The module correctly presents Ukrainian grammar on its own terms, with English as the contrastive baseline where needed. **PASS**

## Verification Summary

| Check | Result |
|-------|--------|
| Colonial framing | **PASS** — No Russian-baseline comparisons |
| Russianisms | **PASS** — No кушати, красивий, прекрасне, etc. |
| Double comparative | **PASS** — Correctly taught as an error |
| Grammar scope creep | **PASS** — Stays within M11-M24 review scope |
| Word salad | **PASS** — Each paragraph has one clear point |
| LLM structural monotony | **PASS** — Varied section openings |
| Example batching | **PASS** — Formats vary (bullets, tables, dialogue, numbered) |
| Callout monotony | **PASS** — 8 callouts with 5 different types, no duplicated titles |
| Plan sections present | **PASS** — All 5 plan sections present as H2 |
| Activity errors | **FAIL** — Mislabeled activity, contradictory explanation, missing commas |
| IPA accuracy | **FAIL** — 2 IPA errors in vocabulary |
| Spelling/grammar | **FAIL** — "Умовий" typo, "річ є добрий" agreement error |

**Section coverage verification:**
- Section «Огляд та вступ: Карта навичок» — reviewed (opening, skill map, immersion statement)
- Section «Навичка 1: Вид дієслова: Процес та результат» — reviewed (present tense rule, aspect pairs, hospitality hook)
- Section «Навичка 2: Ступені порівняння: Від якості до досконалості» — reviewed (simple/compound forms, double comparative trap, irregular table, proverb)
- Section «Навичка 3: Модальність та узгодження числівників» — reviewed (conditional/imperative, 1-2-5 rule, synthesis)
- Section «Навичка 4: Синтез та практичне завдання» — reviewed (dialogue analysis, transformation marathon, event planning challenge)

## Fix Plan

| # | Target | File | Location | Action |
|---|--------|------|----------|--------|
| 1 | Gender agreement | content | Line 29 | Change «що річ є **добрий**» → «що річ є **добра**» |
| 2 | Spelling error | content | Line 265 | Change «Умовий спосіб» → «Умовний спосіб» |
| 3 | Activity title | activities | Line 270 | Rename to «Виправте помилки: Вид дієслова та числівники» |
| 4 | Activity explanation | activities | Line 125 | Rewrite to explain aspect choice in context, not claim "always perfective" |
| 5 | Unjumble comma | activities | Line 259 | Fix answer to «Якби ми мали час, ми зробили б це.» |
| 6 | Unjumble commas | activities | Line 267 | Fix answer to «Краще пізно, ніж ніколи, але краще вчасно.» |
| 7 | IPA вчасно | vocabulary | Line 56 | Change `[ˈʍt͡ʃɑsnɔ]` → `[ˈu̯t͡ʃɑsnɔ]` |
| 8 | IPA родовий | vocabulary | Line 140 | Change `[rɔˈdɔˈʋɪj]` → `[rɔdɔˈʋɪj]` |
| 9 | Warmth markers | content | Sections 2-3 | Add 1-2 encouraging phrases in Sections «Навичка 2» and «Навичка 3» to improve mid-lesson warmth |
| 10 | Immersion boost | content | Global | Convert ~10 words of English scaffolding to Ukrainian where possible to cross 60% threshold |

## Verdict

**FAIL — Requires D.2 repair cycle.**

The module has strong bones: solid plan compliance, excellent cultural hooks (hospitality aspect, proverb integration), a well-constructed synthesis dialogue with 12-point analysis, and no colonial framing. The grammar explanations are accurate and well-scaffolded between English theory and Ukrainian practice.

However, it fails on execution details that are unacceptable in a grammar checkpoint module:
- Two Ukrainian language errors (gender agreement, spelling) in the very text teaching grammar
- Activity quality issues (mislabeled exercise, contradictory explanation, missing punctuation in answer keys)
- Two IPA errors in the vocabulary file
- Marginally below immersion floor

All issues are targeted and fixable in a single D.2 repair pass. The content does not need structural changes or rewriting — just precision corrections.