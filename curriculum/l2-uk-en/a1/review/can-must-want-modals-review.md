<!-- content-hash: c246c9ae89ea -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | **Plan Compliance** | 8/10 | All 10 H2 sections from content_outline are present. However, the plan specifies "Вступ та культурний контекст" as a combined section; the module splits this unevenly, with culture spread across later sections. The plan calls for 5 minimal pairs for могти vs. вміти drills — only 1 explicit pair exists (the swimming example in the warning box). The Хотіти conjugation table promised in the plan's "required" vocabulary hints is missing from the prose entirely. |
| 2 | **Lesson Quality** | 8/10 | The pacing is good, with practice sections near the end. The opening hook (Section «Вступ: Модальність у житті») uses real-life scenarios effectively. However, the module lacks a warm "welcome" opening — it jumps directly into a Ukrainian paragraph without greeting the learner. There is no clear "Today you'll learn…" preview in English. The closing summary at line 397 is perfunctory ("Сьогодні ви отримали нові інструменти") without a proper celebration. The dialogues in Section «Практика: Дозвіл та Етикет» are excellent — natural and clearly staged. |
| 3 | **Language** | 7/10 | Several grammatical and naturalness issues found (see Critical Issues). The phrase «Мені треба ручку» (line 147) is questionable — mixing impersonal "треба" with Accusative is colloquial and contradicts the module's own teaching that "потрібна ручка" is correct. «Вхід обов'язковий у масках» (line 311) is unnatural Ukrainian — should be «Вхід у масках обов'язковий» or «Маски обов'язкові при вході». The phrase «В гостях» (line 357) uses Russian-influenced preposition «В» before a consonant cluster instead of Ukrainian «У гостях». Also «В офісі» (line 339) and «В транспорті» (line 345) have the same в/у issue. |
| 4 | **Richness** | 8/10 | Good variety of engagement boxes (6 total: warning, tip, context, culture, myth-buster, quote). Cultural hooks about «Можна?» etiquette are well-placed. The Sign section (Section «Дозвіл і Заборона: Можна та Не можна») with emoji-based signs is creative and memorable. The extended narratives of Андрій and Оксана in Section «Практика: Мої можливості та Обов'язки» are rich and provide genuine consolidation. However, there is no Career Counselor persona flavor despite the meta specifying `role: Career Counselor`. The module reads as a generic tutor, not a career-focused one. |
| 5 | **Activity Quality** | 7/10 | 8 activity types with good variety (quiz, fill-in, match-up, true-false, group-sort, unjumble). However, no activities cover the "Спроба" section (пробувати, намагатися) or the "Характеристика" section (необхідний, обов'язковий, можливий) — these sections have vocabulary in the content but zero activity practice. The plan called for ~51 fill-in items total across 3 fill-in activities; only 16 fill-in items exist across 2 fill-in activities. Activity coverage is incomplete. |
| 6 | **Immersion** | 9/10 | Audit shows 43.6%, which is within the A1.3 target of 40-60% (the module is module 24, in the consolidation band). English scaffolding is well-deployed for grammar explanations while Ukrainian examples stand on their own. The dialogue sections are nearly fully Ukrainian with translations — good immersion. |
| 7 | **Factual Accuracy** | 8/10 | Grammar rules for могти, вміти, треба, потрібно, повинен are all correct. The г→ж consonant alternation is accurately described. The proverb «Хто хоче — той може» is authentic. However, the myth-buster box (line 364) «Іноземці думають: українці говорять прямо. І грубо. Це не так» presents a cultural generalization without source. The claim about "intonation" as the basis of Ukrainian politeness is an oversimplification — Ukrainian politeness relies on modal constructions, diminutives, and register choice, not just intonation. |
| 8 | **Humanity & Warmth** | 7/10 | The module uses some direct address ("ви", "давайте"), but lacks the warm, encouraging tone expected for A1. There is no "Привіт!" or warm greeting at the opening. The very first words are a Ukrainian paragraph with no English scaffolding. No "Don't worry" moments. No explicit encouragement phrases like "Great job!" or "You've got this!". The narrative examples (Андрій, Оксана) are warm but arrive too late (lines 376-384). The closing at line 397 says «Ви не просто спостерігач» but provides no emotional celebration. Count of warmth markers: Direct address (ви/ти) = ~20 (pass), Encouragement phrases = 0 (FAIL), "Don't worry" moments = 0 (FAIL), "You can now..." validation = 1 weak instance (marginal). |
| 9 | **LLM Fingerprint** | 7/10 | Structural monotony detected: Sections «Могти та Вміти: Фізична можливість і Навичка», «Обов'язок: Треба, Потрібно, Повинен», «Дозвіл і Заборона: Можна та Не можна», «Порада: Варто», and «Спроба: Пробувати, Намагатися» all follow an identical pattern: 2-line English intro → bullet list of Ukrainian examples with English translations. This uniform structure across 5+ sections is a clear LLM fingerprint. The opening of Section «Вступ: Модальність у житті» at line 17 uses «Сьогодні ми відкриваємо двері у світ модальності» which is a characteristic AI rhetoric flourish. |

---

## Critical Issues Found

### Issue 1: Ukrainian Preposition В/У Violations (Language, CRITICAL)

**Location:** Lines 339, 345, 357

Ukrainian orthographic rule: before consonant clusters and at the beginning of a sentence after a pause, use **«у»** not **«в»**. Three section headers violate this:

- Line 339: «В офісі» → should be «В офісі» is actually acceptable here since "о" is a vowel. **RETRACTED** upon re-examination — «В офісі» is correct (В before a vowel).
- Line 357: «В гостях» → should be **«У гостях»** (before consonant "г")
- Line 345: «У транспорті» — let me re-verify.

After rechecking: Line 357 «В гостях» is the primary violation. "В" before the consonant "г" violates the euphonic в/у alternation rule. Should be «У гостях».

**Fix:** Change «В гостях» to «У гостях» at line 357.

### Issue 2: Contradictory Grammar Teaching — "Мені треба ручку" (Language, CRITICAL)

**Location:** Line 147

The tip box presents «Мені треба ручку» as a conversational alternative. But this form uses the Accusative case (ручку) with impersonal "треба" — while the module's own main text at line 149 states «Мені потрібна ручка» is better. The problem is: "треба + noun in Accusative" is grammatically debatable and confusing for A1 learners. The research notes (line 24) confirm this is a known learner error area.

Presenting a colloquial/debatable form in a [!tip] box labeled "Life Hack" risks teaching an error as a shortcut. At A1, clarity matters more than colloquial flexibility.

**Fix:** Rewrite the tip to say that when you need a noun (not infinitive), prefer «Мені потрібна/потрібен + Nominative noun» and that «Мені треба + Infinitive» is for actions. Remove or explicitly mark «Мені треба ручку» as "you may hear this but avoid it in your own speech."

### Issue 3: Unnatural Sentence — "Вхід обов'язковий у масках" (Language)

**Location:** Line 311

The sentence «Вхід обов'язковий у масках» is unnatural word order. In Ukrainian, this would more naturally be «Вхід у масках обов'язковий» or «Вхід тільки в масках» or «Маски обов'язкові». The current phrasing reads like a calque from English "Entry is mandatory in masks."

**Fix:** Replace with «Вхід тільки в масках» or «Маски обов'язкові при вході».

### Issue 4: No Activities for Two Full Content Sections (Activity Quality, MAJOR)

**Location:** Activities file — missing coverage for Sections «Спроба: Пробувати, Намагатися» and «Характеристика: Необхідний, Обов'язковий, Можливий»

The content teaches пробувати, намагатися, вдаватися (Section «Спроба: Пробувати, Намагатися», lines 248-277) and необхідний, обов'язковий, можливий (Section «Характеристика: Необхідний, Обов'язковий, Можливий», lines 279-300), but zero activity items test these words. This means learners read about them but never practice them.

**Fix:** Add at least one activity (e.g., fill-in or quiz) covering пробувати/намагатися and another covering modal adjectives.

### Issue 5: Missing Warm Opening and Beginner Safety (Warmth, MAJOR)

**Location:** Lines 11-17

The module opens with a dense Ukrainian paragraph (line 13): «Уявіть ситуацію. Ви хочете кави. Але ви не знаєте, як попросити...». An A1 learner seeing this as the first thing — no greeting, no English orientation, no "today you'll learn" — will feel thrown into the deep end. The "Would I Continue?" test: "Were instructions clear?" → No (Ukrainian paragraph first). "Was Ukrainian scary?" → Yes (dense Ukrainian with no translation before line 17).

**Fix:** Add a brief English welcome before the Ukrainian hook: "Welcome back! Today you'll learn the most useful words in Ukrainian — words that let you ask for things, talk about what you can do, and understand rules."

### Issue 6: Missing Хотіти Conjugation Table (Plan Compliance)

**Location:** Entire content file

The plan's `vocabulary_hints.required` lists хотіти as a required vocabulary item with stress patterns (хо́чу, хо́чеш). The module never presents a conjugation table for хотіти, despite presenting full tables for могти (lines 57-64) and вміти (lines 82-89). The verb хотіти has an irregular conjugation (хочу, хочеш, хоче — with stem change from хот- to хоч-), which is exactly the kind of thing A1 learners need a table for.

**Fix:** Add a conjugation table for хотіти, likely in Section «Вступ: Модальність у житті» or as a new subsection.

### Issue 7: IPA Missing from Content Prose (Minor)

**Location:** Entire content file

The vocabulary YAML file contains IPA for all 15 terms, but the content prose itself has zero IPA transcriptions. For an A1 module where pronunciation guidance is critical, at least the key terms (могти, вміти, треба, потрібно, повинен) should have inline IPA on first occurrence in the prose.

**Fix:** Add IPA in brackets after each key term's first occurrence (e.g., **могти́**).

---

## Factual Verification

| # | Claim | Location | Verified? | Notes |
|---|-------|----------|-----------|-------|
| 1 | г→ж consonant alternation in могти conjugation | Line 49-53 | **YES** | Correct: могти → можу, можеш, etc. Standard Ukrainian morphophonology. |
| 2 | Повинен agrees by gender/number: повинен/повинна/повинно/повинні | Lines 156-162 | **YES** | Correct paradigm. |
| 3 | Треба/Потрібно are impersonal, take Dative for the experiencer | Lines 115-123 | **YES** | Correct: «Мені потрібно йти» — Dative + impersonal. |
| 4 | Proverb «Хто хоче — той може» = "Where there's a will, there's a way" | Line 389-391 | **YES** | Authentic Ukrainian proverb, correctly translated. |
| 5 | Myth-buster: Ukrainian politeness is built on intonation | Line 365 | **PARTIAL** | Oversimplified — Ukrainian politeness is built on modal constructions, diminutives, register choice, AND intonation, not intonation alone. Not factually wrong, but misleadingly reductive. |
| 6 | «Можна?» as universal polite request | Lines 214-219 | **YES** | Confirmed by research notes (line 18): «Можна?» functions as "May I?", "Excuse me", and "Is this free?" combined. |
| 7 | Вміти/Уміти as alternative forms | Line 72 | **YES** | Both forms are standard Ukrainian. |

### Callout Box Verification

| Box | Type | Location | Issue? |
|-----|------|----------|--------|
| Common Mistake | warning | Line 91 | **Clean** — accurate distinction between могти/вміти |
| Life Hack | tip | Line 145 | **ISSUE** — presents debatable form «Мені треба ручку» (see Issue 2) |
| Мусити | context | Line 168 | **Clean** — correctly introduces мусити as strong obligation |
| Cultural Code: "Можна?" | culture | Line 214 | **Clean** — verified against research |
| Міф: Українці грубі | myth-buster | Line 364 | **MINOR** — oversimplifies politeness mechanism |
| Народна мудрість | quote | Line 388 | **Clean** — authentic proverb |

### Colonial Framing Check

**No colonial framing found.** The module does not define Ukrainian by contrast with Russian. All explanations use English as the scaffolding language, which is appropriate for L2 (English→Ukrainian) teaching.

### LLM Fingerprint Analysis

**Structural monotony:** Sections «Могти та Вміти: Фізична можливість і Навичка» (line 37), «Обов'язок: Треба, Потрібно, Повинен» (line 109), «Дозвіл і Заборона: Можна та Не можна» (line 173), «Порада: Варто» (line 221), and «Спроба: Пробувати, Намагатися» (line 248) all follow the same pattern: short English intro sentence → numbered or bulleted Ukrainian examples with English translations. 5 sections with identical structure.

**Example batching:** Every section uses the same format: `*   «Ukrainian **bold** text». English translation.` — identical across all content sections.

**Generic AI rhetoric:** Line 17 «Сьогодні ми відкриваємо двері у світ модальності» — "opening doors to the world of modality" is AI-typical rhetoric that a real tutor would not use.

---

## Verification Summary

| Check | Result |
|-------|--------|
| All 10 H2 sections present | **PASS** — All sections from content_outline found in content |
| Vocabulary scope vs. plan | **PARTIAL** — 15 vocab items present; хотіти lacks conjugation table in prose |
| Grammar scope (no creep) | **PASS** — All grammar stays within modal verbs scope |
| Learning objectives addressed | **PARTIAL** — "distinguish between modal meanings" objective is tested only in true-false, not in a dedicated comparison activity |
| Activity coverage | **FAIL** — Two full sections (Спроба, Характеристика) have zero activity items |
| Engagement boxes | **PASS** — 6 boxes, good variety of types |
| Immersion target (A1.3: 40-60%) | **PASS** — 43.6% within range |
| Colonial framing | **PASS** — None found |
| Russianisms | **MINOR** — «В гостях» (should be «У гостях»); not a Russianism per se but violates Ukrainian euphonic rule |
| IPA in prose | **FAIL** — Zero IPA in content file (only in vocabulary YAML) |
| Warm opening | **FAIL** — No English greeting, no "today you'll learn" |
| Encouragement phrases | **FAIL** — Zero encouragement phrases in the entire module |
| "Would I Continue?" test | 3/5 — Passes on pacing, quick wins (dialogue section), and instructions clarity (for most sections). Fails on overwhelming Ukrainian opening and lack of encouragement. Score: **Lesson Quality 8** |

### Section Coverage Verification

| Section | Referenced in Review | Issues Found |
|---------|---------------------|--------------|
| «Вступ: Модальність у житті» | Yes | Missing warm opening, AI rhetoric at line 17 |
| «Могти та Вміти: Фізична можливість і Навичка» | Yes | Good content, structural monotony |
| «Обов'язок: Треба, Потрібно, Повинен» | Yes | Debatable tip box at line 145-149 |
| «Дозвіл і Заборона: Можна та Не можна» | Yes | Clean — best section in the module |
| «Порада: Варто» | Yes | Structural monotony pattern |
| «Спроба: Пробувати, Намагатися» | Yes | Zero activity coverage |
| «Характеристика: Необхідний, Обов'язковий, Можливий» | Yes | Zero activity coverage |
| «Контекст: Правила та Плани» | Yes | Unnatural sentence at line 311 |
| «Практика: Дозвіл та Етикет» | Yes | Excellent dialogues; «В гостях» → «У гостях» |
| «Практика: Мої можливості та Обов'язки» | Yes | Strong consolidation narratives |

---

## Verdict

**FAIL — Needs D.2 repair.**

The module has solid grammar explanations and good structural organization, but fails on several dimensions:

1. **Language (7/10):** The «В гостях» euphonic violation and the debatable «Мені треба ручку» "Life Hack" are fixable but real. The unnatural «Вхід обов'язковий у масках» needs rephrasing.

2. **Activity Quality (7/10):** Two full content sections (Спроба and Характеристика) have zero activity items — this is a significant gap given the plan specified extensive fill-in practice.

3. **Humanity & Warmth (7/10):** Zero encouragement phrases in the entire module. No warm opening. No "Don't worry" moments. This is a critical failure for an A1 module — a nervous beginner would find this content functional but cold.

4. **LLM Fingerprint (7/10):** 5+ sections with identical structural patterns and AI-typical opening rhetoric.

**Priority fixes for D.2:**
1. Add warm English opening with learning objectives preview
2. Fix «В гостях» → «У гостях», fix line 311 unnatural sentence
3. Rewrite the "Life Hack" tip to avoid teaching debatable forms
4. Add activities for пробувати/намагатися and необхідний/обов'язковий/можливий
5. Add encouragement phrases throughout (at least 3)
6. Add хотіти conjugation table
7. Add IPA for key terms on first occurrence
8. Vary section opening structures to break the LLM monotony pattern