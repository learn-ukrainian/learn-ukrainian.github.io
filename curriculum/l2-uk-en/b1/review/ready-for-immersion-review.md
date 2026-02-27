<!-- content-hash: 4c899d3d3d23 -->
**Reviewed-By:** claude-opus-4-6

## Scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | **Language Quality** | 8 | Ukrainian is natural and well-written throughout. No Russianisms detected. Euphony respected. However, colonial framing exists in the embedded grammar text (lines 408-409) where Ukrainian is defined by contrast with Russian: «Пор.: рос. стол — укр. стіл, рос. печь — укр. піч». While this is inside a quoted grammar passage, no decolonization framing is provided. |
| 2 | **Teaching Quality** | 8 | Strong pedagogical arc: compelling airlock metaphor hook, cultural anchors (Ґ, Грінченко, Океан Ельзи), excellent use of TTT with comparative questioning in Section «Діагностика: Що ми пам'ятаємо?». Missing a genuine diagnostic assessment for a checkpoint module — the section explains distinctions rather than testing pre-existing knowledge. Missing the planned Правило/Право error clinic entirely. |
| 3 | **Factual Accuracy** | 9 | Грінченко dictionary dates (1907-1909) and 68,000 entries: correct. Letter Ґ removed 1933, restored 1990: correct. Ікавізм dating to XIII century: approximately correct. Grammatical analyses of «Я не здамся без бою!» and «Слава Україні!» are linguistically sound. Minor: the «складна форма» description (line 230) as «Інфінітив + суфікс -м- + закінчення (-му, -меш, -ме)» is a valid pedagogical simplification. |
| 4 | **LLM Fingerprint** | 8 | Section openings are varied — no structural monotony across H2 sections. No "це не просто" patterns found. No generic AI clichés. However, Section «Система мови: Частини мови» uses a repetitive "Це X мови" formula for 5 consecutive parts of speech: «Це фундамент мови» (іменник), «Це фарби мови» (прикметник), «Це математика мови» (числівник), «Це двигун речення» (дієслово), «Це ознака дії» (прислівник). While pedagogically motivated as a mnemonic framework, the uniformity across 5+ entries reads as template-driven. |
| 5 | **Activity Quality** | 7 | Activities are individually well-designed. The error-correction type (6 items) and mark-the-words type are pedagogically excellent additions. However, activity item counts fall significantly short of plan requirements: fill-in has 8 items (plan: 15+), quiz has 8 items (plan: 20+), match-up has 12 pairs (plan: 15+). Total unique types: 6 (match-up, group-sort, fill-in, mark-the-words, error-correction, quiz) — good variety. |
| 6 | **Plan Compliance** | 7 | All 10 H2 sections from the meta content_outline are present. Word count 4460/4000 (111.5%) exceeds target. But: (a) the Правило/Право learner error clinic explicitly required in the plan is completely absent; (b) activity item counts are 40-60% below plan requirements; (c) the diagnostic section lacks an actual diagnostic test despite being a checkpoint module. |
| 7 | **Immersion** | 9 | Audit reports 98.4% Ukrainian. Plan specifies 70-85% for B1.0 bridge. The higher immersion makes sense given this module's purpose of preparing for full immersion. English appears only in parenthetical translations for new terms and the SVO comparison (lines 367-369), which is pedagogically justified. Not flagging the overshoot as an issue. |
| 8 | **Richness** | 9 | Cultural hooks: Ґ history (line 23-25), Грінченко dictionary (line 302-304), Океан Ельзи song analysis (lines 466-474), «Слава Україні!» grammar (lines 478-485). Tables: 2 (classification table line 101, abbreviations table line 289). Dialogues: 3 (Аліас game, error correction, classroom). Callout variety: [!history-bite], [!tip]×2, [!warning], [!observe], [!cultural], [!context], [!myth-buster] — 7 types. |
| 9 | **Humanity & Warmth** | 9 | Strong teacher voice throughout. Direct address frequent: «Вітаю вас», «Ви готові?», «Давайте проведемо ревізію», «Давайте проаналізуємо». Confusion anticipated: «Ви можете відчути дискомфорт. Це нормально» (line 21). Encouragement: «я вірю у вас» (line 573). Humor: «офіціант принесе вам серветки, а не рахунок» (line 504). Common mistake warnings: multiple throughout. |

---

## Critical Issues Found

### Issue 1: Missing Правило/Право Error Clinic (Plan Violation)
**Severity:** HIGH
**Location:** Should be in Section «Синтаксис: Будова речення» or «Діагностика: Що ми пам'ятаємо?»
**Plan requirement (plans/b1/ready-for-immersion.yaml, section 5):** "Learner Error Clinic 3: 'Правило' (Rule) vs 'Право' (Law/Right). Correcting the common false friend error 'У мене є правило' when the learner means 'I have the right'."
**Research notes also list this** as a key learner error: "`Правило` (rule) vs `Право` (law/right). Learners often say 'У мене є правило' when they mean 'I have the right'."
**Status:** The vocabulary file includes a note "Do not confuse with право (right/law)" but the lesson prose never addresses this error at all. No example, no explanation, no drill.
**Fix:** Add a ~100-word subsection in «Діагностика: Що ми пам'ятаємо?» or «Практикум: Метамова в дії» covering this false friend, following the same pattern as the existing error clinics (Морфологія/Синтаксис, Відміна/Відмінок, Рід/Число, Звук/Буква). Example format:

```
### Правило чи Право?
**Правило** — це інструкція, зразок (rule). *За правилом, перед "що" ставимо кому.*
**Право** — це можливість, дозвіл (right/law). *Я маю право запитати.*
Не кажіть: *"Я маю правило запитати"* — це означає щось зовсім інше!
```

### Issue 2: Activity Item Counts Far Below Plan Requirements
**Severity:** HIGH
**Location:** `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/ready-for-immersion.yaml`
**Plan requirements (plans/b1/ready-for-immersion.yaml, activity_hints):**
- fill-in: 15+ items → actual: 8 items (53%)
- quiz: 20+ items → actual: 8 items (40%)
- match-up: 15+ items → actual: 12 pairs (80%)
**Impact:** For a checkpoint module designed to test mastery of M01-04 metalanguage, having only 8 quiz items and 8 fill-in items is insufficient for comprehensive diagnostic assessment. The learner needs more practice items to genuinely test readiness for immersion.
**Fix:** Expand fill-in to 15+ items (add 7+ items covering скорочення, словникові позначки, синтаксичні терміни). Expand quiz to 20+ items (add 12+ items on parts of speech recognition, sentence analysis, register identification). Expand match-up to 15+ pairs (add 3+ pairs covering скорочення like «пор./порівняй», «і т.д./і так далі», «заст./застаріле»).

### Issue 3: Colonial Framing in Embedded Grammar Text
**Severity:** MEDIUM
**Location:** Lines 408-409 in Section «Практика розуміння: Граматичний текст»
**Text:** «Воно допомагає відрізняти українські слова від слів інших слов'янських мов.» followed by «Пор.: рос. стол — укр. стіл, рос. печь — укр. піч.»
**Context:** This is inside a quoted grammar passage that students are learning to read. Line 420 in the analysis says: «Автор порівнює з російською мовою (рос.), щоб показати унікальність української.»
**Problem:** While the comparison is presented as an authentic grammar text, the analysis at line 420 uncritically accepts the framing of Ukrainian defined by contrast with Russian. No decolonization note explains that Ukrainian ікавізм is an independent phonological development, not a "difference from Russian."
**Fix:** Add a [!decolonization] callout after line 420 or in Section «Культурний аспект» (line 442-446):

```
> [!decolonization]
> **Ікавізм — не "відмінність від російської"**
> Чергування о/е → і — це самостійний розвиток української мови, що сформувався у XIII столітті. Старі підручники часто описують українські явища через порівняння з російською, ніби українська — "варіант" іншої мови. Це не так. Ікавізм — самобутня ознака української фонетики.
```

---

## Non-Critical Issues

### Issue 4: Діагностика Section Lacks Actual Diagnostic (TTT Deviation)
**Severity:** LOW-MEDIUM
**Location:** Section «Діагностика: Що ми пам'ятаємо?» (lines 29-78)
**Problem:** For a checkpoint module using TTT pedagogy, the diagnostic section should TEST knowledge before teaching. Instead, it explains four distinctions (Морфологія/Синтаксис, Відміна/Відмінок, Рід/Число, Звук/Буква) without first asking the learner what they already know. The plan requires "TTT Diagnostic Assessment: Comprehensive test of metalanguage from M01-04 to identify specific gaps." The self-check questions only appear at the very end (lines 586-593), not at the start.
**Recommendation:** Consider adding a brief "Перевірте себе" self-assessment at the START of the diagnostic section (before explanations), then use the explanations as the "Teach" phase.

### Issue 5: «лайл.» Abbreviation Questionable
**Severity:** LOW
**Location:** Line 313 in Section «Стилістика: Як читати правила»
**Text:** «лайл. (лайливе): Обережно! Це образа.»
**Problem:** The abbreviation «лайл.» is not widely attested in standard Ukrainian dictionaries. More common dictionary abbreviations for offensive language include «вульг.» (вульгарне), «груб.» (грубе), or «лайк.» (лайкове). The abbreviation «лайл.» appears in some sources but is non-standard enough that teaching it as a standard abbreviation could mislead students.
**Recommendation:** Replace with «вульг. (вульгарне)» or add both: «вульг. / лайл.»

---

## Factual Verification

| Claim | Location | Verdict | Notes |
|-------|----------|---------|-------|
| Ґ removed in 1933 orthography reform | Line 25 | ✅ Correct | The 1933 reform (revision of 1928 Kharkiv orthography) removed Ґ |
| Ґ restored in 1990 | Line 25 | ✅ Correct | Ukrainian orthography of 1990 restored Ґ |
| Грінченко dictionary 1907-1909, 68,000 words | Line 304 | ✅ Correct | "Словарь української мови" published 1907-1909, ~68,000 entries |
| Title "Словарь української мови" | Line 304 | ✅ Correct | Original title used "Словарь" (contemporary spelling convention) |
| Ікавізм formed in XIII century | Line 444 | ✅ Approximately correct | The o/e → і shift developed approximately 13th-14th centuries |
| «Я не здамся без бою!» by Океан Ельзи | Lines 466-467 | ✅ Correct | Song "Без бою" by Океан Ельзи, became symbol of resistance |
| «Слава Україні!» grammatical analysis | Lines 480-484 | ✅ Correct | Слава = nominative, Україні = dative. Pedagogically sound analysis. |
| Three future tense forms | Lines 222-237 | ✅ Correct | Проста (прочитаю), складна (читатиму), складена (буду читати) — standard Ukrainian grammar terminology |
| Present tense only for imperfective verbs | Lines 216-219 | ✅ Correct | Standard rule; explanation «Результат або вже є (минуле), або ще буде (майбутнє)» is pedagogically sound |
| «ПлАчу» = I cry, «ПлачУ» = I pay | Lines 501-502 | ✅ Correct | Standard minimal pair for stress-based meaning distinction |

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| All H2 sections from meta content_outline present | ✅ | All 10 sections present and correctly named |
| Word count meets target | ✅ | 4460/4000 (111.5%) |
| Vocabulary coverage | ✅ | All 19 required items from plan vocabulary_hints.required are covered in vocab file (27 items total) |
| Grammar scope | ✅ | No grammar from later modules; all topics within M01-M04 integration scope |
| Russianisms | ✅ | None detected |
| Colonial framing | ⚠️ | Lines 408-409 contain Russian comparison in embedded grammar text without decolonization framing |
| LLM clichés | ✅ | No "це не просто", no "Let's explore", no generic AI rhetoric |
| Callout variety | ✅ | 7 unique callout types across 7 boxes |
| Plan-required content items | ❌ | Missing Правило/Право error clinic; activity item counts below plan thresholds |
| Objectives coverage | ⚠️ | 5/6 objectives met; "Learner can use negation and verb form terminology" partially addressed |

**Section Coverage Verification:**
- Section «Вступ: Нові правила гри» — reviewed ✅ (airlock metaphor, Ґ history, proverb)
- Section «Діагностика: Що ми пам'ятаємо?» — reviewed ✅ (4 diagnostic pairs, missing actual test)
- Section «Система мови: Частини мови» — reviewed ✅ (Tree of Speech, 10 parts of speech classified)
- Section «Дієслово: Час і Вид» — reviewed ✅ (aspect pairs, 3 future forms, clear explanations)
- Section «Стилістика: Як читати правила» — reviewed ✅ (register distinction, abbreviations, Грінченко)
- Section «Синтаксис: Будова речення» — reviewed ✅ (5 sentence members, word order contrast, punctuation)
- Section «Практика розуміння: Граматичний текст» — reviewed ✅ (vowel alternation text, guided analysis)
- Section «Практикум: Метамова в дії» — reviewed ✅ (Alias game, song analysis, error correction, stress pairs)
- Section «Ситуації: Урок української» — reviewed ✅ (classroom phrases, etiquette, myth-buster)
- Section «Підсумок: Готовність до занурення» — reviewed ✅ (safety protocol, learner's oath, self-check questions)

---

## Verdict

**CONDITIONAL PASS** — The module is well-written with strong pedagogical structure, rich cultural anchoring, and accurate grammar. Three issues require repair before full approval:

1. **[MUST FIX]** Add Правило/Право error clinic (~100 words) as required by the plan
2. **[MUST FIX]** Expand activity items to meet plan thresholds (fill-in 15+, quiz 20+, match-up 15+)
3. **[SHOULD FIX]** Add decolonization framing to the Russian comparison in the embedded grammar text (lines 408-409)

The module's prose quality, cultural hooks, and teaching arc are strong. The fixes are additive (expand activities, add missing content) rather than structural rewrites.