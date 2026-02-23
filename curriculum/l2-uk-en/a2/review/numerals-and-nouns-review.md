<!-- content-hash: b4e3dde8fabe -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Weight | Weighted |
|---|-----------|-------|--------|----------|
| 1 | Lesson Quality | 8 | 2 | 16 |
| 2 | Language Quality | 7 | 3 | 21 |
| 3 | Immersion Balance | 9 | 1 | 9 |
| 4 | Richness | 8 | 1 | 8 |
| 5 | LLM Fingerprint | 8 | 1 | 8 |
| 6 | Activity Quality | 7 | 2 | 14 |
| 7 | Factual Accuracy | 8 | 2 | 16 |
| 8 | Vocabulary Coverage | 8 | 1 | 8 |
| 9 | Humanity / Warmth | 9 | 1 | 9 |
| 10 | Plan Compliance | 7 | 2 | 14 |
| | **Weighted Total** | | **17** | **123/170 (72.4%)** |

---

## Dimension Evidence

### 1. Lesson Quality — 8/10

**"Would I Continue?" Test: 4/5 Pass**

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | PASS | Good pacing, examples interspersed with explanations |
| Were instructions clear? | FAIL | Internal contradiction: line 138 teaches an incorrect animate Accusative form that lines 307-316 later contradict |
| Did I get quick wins? | PASS | Zone 1 examples are simple and provide immediate understanding |
| Was Ukrainian scary? | PASS | Well-scaffolded bilingual presentation |
| Would I come back tomorrow? | PASS | Market roleplay is engaging and relatable |

The lesson arc (WELCOME → PREVIEW → PRESENT → PRACTICE → CELEBRATE) is solid. The Zone mental model is pedagogically strong. The opening is warm with «Чому це важливо?» framing. The closing summary has self-check questions. However, the animacy contradiction within the module (teaching wrong form in one section, correcting it in another) would confuse an attentive learner.

### 2. Language Quality — 7/10

**Critical grammar errors found:**

**Issue 1 (Line 138):** «Я бачу **дві красиві дівчини**.» — This sentence uses «бачу» (Accusative verb) with animate noun «дівчини». Per the module's own animacy rule taught at lines 307-316, animate objects with Zone 2 numerals in Accusative require Genitive-like forms. Correct: «Я бачу двох красивих дівчат.» This is a critical error because it teaches an incorrect form in the Zone 2 gender section that the module itself contradicts later.

**Issue 2 (Line 310):** «У парку швидко бігають **троє собак**.» — This sentence appears under "2. Істоти (Animate Objects)" in the Accusative animacy section. Two problems: (a) «бігають» is intransitive — the dogs are the subject (Nominative), not an object (Accusative), so this sentence doesn't demonstrate the Accusative animacy rule at all; (b) «троє» is a collective numeral form not taught anywhere in this module — the module teaches «три» → «трьох» for animate Accusative.

**Issue 3 (Line 313):** «Вона дуже добре знає **чотирьох мовників**.» — The word «мовник» is non-standard at A2. The standard Ukrainian word for "linguist" is «мовознавець» or «лінгвіст». Using obscure vocabulary in grammar examples is pedagogically questionable for beginners.

**No Russianisms detected.** No word salad. English quality is warm and accessible.

### 3. Immersion Balance — 9/10

At 72.3% Ukrainian (target 60-75% for A2 M21-50), the immersion is well-calibrated. English is used appropriately for abstract grammar concepts (Zone explanations, the Dual Legacy, animacy rules) while all examples, dialogues, and market practice are fully Ukrainian. The transition between languages is smooth and predictable, creating safety for learners.

### 4. Richness — 8/10

Strong cultural hooks: the hryvnia history (lines 36-43), the Dual Legacy section (lines 105-114), and the market roleplay (lines 320-340). Varied visual aids: error analysis tables (lines 75-80), zone summary table (lines 265-269), inline examples with translations. Named Ukrainian references: Київська Русь, гривня, ринок, двоїна. Deduction: the missing Dative case content means one planned dimension of richness is absent.

### 5. LLM Fingerprint — 8/10

**Structural monotony test:** Section openers are varied — «Коли ви вчитеся...» (section «Вступ»), «Перша зона найпростіша...» (section «Презентація: Зони 1 та 2»), «Ласкаво просимо до Зони 3...» (section «Презентація: Зона 3 та Складні числівники»), «Найкраще місце для активної практики...» (section «Практика на ринку»), «До цього часу ми розглядали...» (section «Діалоги та одушевленість»). No monotony.

**Example batching:** Most sections use the same format (Ukrainian bold + English translation + comment), which is somewhat uniform across 5+ sections. Borderline.

**LLM cliché check:** One instance of «це не просто» at line 40 (below 2x threshold). The [!fact] box at line 113-114 is vaguely worded: «Українська мова відрізняється серед своїх сусідів цікавою рисою.» — "its neighbors" is an imprecise claim typical of LLM hedging (most Slavic languages retain dual traces to varying degrees).

**Callout monotony:** Callout types vary: [!tip], [!culture], [!warning] (×2), [!fact], [!myth-buster], [!observe]. No monotony.

### 6. Activity Quality — 7/10

**12 activities** present with good type variety (group-sort, fill-in ×2, match-up, true-false, quiz, error-correction, unjumble, mark-the-words, select, translate, cloze).

**Critical activity issue (Activity file line 49-50):** The fill-in item «Це велика ___ проблема.» with answer «одна» produces «Це велика одна проблема.» — unnatural Ukrainian word order. The numeral should precede the adjective: «Це одна велика проблема.» This item would teach wrong word order.

**Missing Dative activity:** The plan specifies `type: fill-in, focus: Dative with numerals, items: 8` — no such activity exists. This is a significant gap.

**Unjumble punctuation (Activity file line 271):** «Дайте будь ласка дві пляшки» — missing commas around «будь ласка». Minor for unjumble format.

### 7. Factual Accuracy — 8/10

**Hryvnia history (lines 36-40):** The claim that «гривня» was a unit of weight in Kyivan Rus is accurate. The etymology connecting «гривня» to «загривок» (nape/neck) is a commonly cited folk etymology — plausible but not universally accepted by linguists. The claim about «рубль» from «рубати» (to chop) is the standard etymology and is accurate.

**[!fact] box (line 114):** «Українська мова відрізняється серед своїх сусідів цікавою рисою. Вона дуже яскраво зберігає сліди двоїни у своїй сучасній граматиці.» — This is an overstatement. Slovenian retains a full dual number system. Polish, Czech, and other Slavic languages also have dual traces. Claiming Ukrainian is distinctive "among its neighbors" in this regard is misleading.

**Grammar rules verified:** Zone 1 (gender agreement with 1), Zone 2 (Nominative Plural with 2-4), Zone 3 (Genitive Plural with 5-20), 11-14 trap, Last Digit Rule — all grammatically correct. The animacy rule explanation (lines 297-318) is correct in principle but has flawed examples (see Language Quality).

**Vocabulary IPA (file lines 52-54, 56-58):** «п'ятдесят» transcribed as [pjɑddɛˈsʲɑt] — the [dd] cluster appears to be an assimilation error; standard is [td]. «Вісімдесят» transcribed as [ʋʲisʲimdɛˈsʲɑt] — stress placement on final syllable is questionable; primary stress should be [ˈʋʲisʲimdɛsʲɑt].

### 8. Vocabulary Coverage — 8/10

All required vocabulary items from the plan are present in both content and vocabulary file: один/одна/одне, два/дві, три, чотири, п'ять, десять, двадцять, гривня, долар, євро. All recommended items present: ринок, кілограм, пляшка, рік. The vocabulary file has 27 items with IPA, translations, and POS. Gender noted where relevant. Deductions for the IPA issues noted above.

### 9. Humanity / Warmth — 9/10

Abundant direct address throughout (ви/вам/ваш used extensively). Encouragement phrases: «Давайте!» (multiple), «Не бійтеся зовсім робити помилки» (line 340), «Ви будете повністю готові» (line 225), «Це стане дуже легко для вас» (line 25). Cultural warmth through market scenario and hryvnia history. The persona (Encouraging Cultural Guide / Inventory Manager) is consistently maintained. Missing only a strong "You can now..." celebration at the very end — the closing is in English summary style rather than a warm Ukrainian congratulation.

### 10. Plan Compliance — 7/10

**Sections present:** All 5 H2 sections from content_outline are present: «Вступ», «Презентація: Зони 1 та 2», «Презентація: Зона 3 та Складні числівники», «Практика на ринку», «Діалоги та одушевленість».

**Missing objective:** «Learner can use numerals in dative case» — The content uses Dative constructions implicitly in age expressions (lines 213-223: «Моєму братові двадцять один рік», «Моїй сестрі тридцять один рік», etc.) but never explicitly teaches Dative case with numerals. The word "Dative" / "давальний" appears nowhere in the content.

**Missing activity:** Plan specifies `type: fill-in, focus: Dative with numerals, items: 8` — no such activity exists in the activity file.

**Word count:** 4633/3000 (154.4%) — exceeds minimum, which is fine. Content is substantive, not padded.

---

## Critical Issues Found

### Issue 1: Animate Accusative Contradiction (CRITICAL — Grammar Error)
- **Location:** Content line 138 vs lines 307-316
- **Description:** Section «Презентація: Зони 1 та 2» at line 138 presents «Я бачу дві красиві дівчини» as a correct example of feminine Zone 2 agreement. But section «Діалоги та одушевленість» at lines 307-316 teaches that animate objects in Accusative with Zone 2 numbers must take Genitive-like forms (два→двох, три→трьох). «Дівчини» are animate, so the correct Accusative form is «Я бачу двох красивих дівчат.» The module teaches an incorrect form and then contradicts itself.
- **Fix:** Replace line 138 with an inanimate feminine example, e.g., «Я бачу дві красиві картини.» (I see two beautiful paintings.)

### Issue 2: Wrong Example Under Accusative Animacy (CRITICAL — Pedagogical Error)
- **Location:** Content line 310
- **Description:** «У парку швидко бігають троє собак» appears under the "Істоти (Animate Objects)" section about Accusative animacy. Problems: (a) «бігають» is intransitive — the dogs are the subject in Nominative, not an Accusative object; (b) «троє» is a collective numeral not taught in this module (the module teaches три→трьох for animate Accusative). This example doesn't demonstrate the claimed rule.
- **Fix:** Replace with a proper transitive+Accusative example: «Я бачу трьох собак у парку.» (I see three dogs in the park.)

### Issue 3: Unnatural Activity Item (SIGNIFICANT — Activity Error)
- **Location:** Activity file line 49-50
- **Description:** Fill-in item «Це велика ___ проблема.» with answer «одна» produces «Це велика одна проблема.» — unnatural word order. Ukrainian requires the numeral before the adjective: «Це одна велика проблема.»
- **Fix:** Change sentence to «Це ___ велика проблема.» or replace entirely with a more natural sentence: «У нас є ___ проблема.»

### Issue 4: Missing Dative Case Content and Activity (SIGNIFICANT — Plan Gap)
- **Location:** Entire content file; entire activity file
- **Description:** Plan objective «Learner can use numerals in dative case» and activity hint `type: fill-in, focus: Dative with numerals, items: 8` are both unaddressed. The content implicitly uses Dative constructions in age expressions but never names or teaches the Dative case. No activity focuses on Dative.
- **Fix:** Either (a) add a subsection to section «Діалоги та одушевленість» explicitly naming Dative constructions in age expressions and add 8 fill-in items, or (b) remove the Dative objective from the plan if it's deferred to a later module. Option (a) is preferred.

### Issue 5: Collective Numeral "троє" Not Taught (MINOR — Scope Leak)
- **Location:** Content line 310
- **Description:** The sentence uses «троє собак» which employs the collective numeral form «троє» — a concept not introduced anywhere in this module. The module teaches «три» → «трьох» for animate Accusative. Using an untaught form in examples confuses the Zone system.
- **Fix:** Covered by Issue 2 fix above.

---

## Factual Verification

| Claim | Location | Verdict | Notes |
|-------|----------|---------|-------|
| Гривня as Kyivan Rus unit of weight/currency | Line 38 | **Accurate** | Well-documented historical fact |
| «Загривок» etymology for «гривня» | Line 38 | **Plausible** | Common folk etymology, not universally accepted |
| «Рубль» from «рубати» | Line 38 | **Accurate** | Standard etymology |
| Zone 1: число 1 agrees in gender | Lines 47-67 | **Accurate** | Standard grammar rule |
| Zone 2: Nominative Plural with 2-4 | Lines 85-103 | **Accurate** | Correct Ukrainian rule |
| Ancient Dual legacy for 2-4 pattern | Lines 107-114 | **Partially accurate** | The Dual Legacy is real, but the claim that Ukrainian is distinctive "among its neighbors" is overstated (Slovenian has full dual) |
| Numbers 11-14 take Zone 3 (Genitive Plural) | Lines 166-182 | **Accurate** | Correct grammar rule |
| Last Digit Rule for compound numbers | Lines 184-204 | **Accurate** | Standard rule |
| «Євро» is indeclinable | Lines 273-286 | **Accurate** | Correct — standard indeclinable borrowing |
| Animate Accusative shift with Zone 2 | Lines 293-318 | **Rule is accurate** | But examples contain errors (see Critical Issues 1 & 2) |

---

## Verification Summary

| Check | Result |
|-------|--------|
| Russianisms found | None |
| Colonial framing found | None (line 114 "серед сусідів" is vague but doesn't name Russian as baseline) |
| Word salad found | None |
| LLM fingerprints (>2 pattern instances) | None exceeding threshold |
| Grammar scope violations | None (all grammar within numeral agreement scope) |
| Activity errors found | Yes — 1 critical (unnatural word order), 1 missing (Dative) |
| Content grammar errors found | Yes — 2 critical (animate Accusative contradiction, wrong example case) |
| Factual errors found | 1 minor (overstated Dual uniqueness claim) |
| Plan compliance gaps | Yes — missing Dative case objective coverage |
| IPA issues | Yes — 2 vocabulary entries (п'ятдесят, вісімдесят) |

---

## Verdict

**NEEDS REVISION** — The module has strong pedagogical structure and warm tone, but contains two critical grammar errors that directly mislead learners about animate Accusative forms. The internal contradiction (line 138 vs lines 307-316) is especially concerning because the module teaches an incorrect form and then teaches the correct rule that contradicts it. The missing Dative case content represents a significant plan compliance gap. These issues require targeted fixes in Phase D.2 before the module can pass.

**Priority fixes:**
1. Replace line 138 animate example with inanimate feminine noun (Critical)
2. Replace line 310 Nominative example with proper Accusative animate example (Critical)
3. Fix activity item «Це велика ___ проблема.» word order (Significant)
4. Add Dative case subsection and 8 fill-in activity items (Significant)
5. Fix IPA for п'ятдесят and вісімдесят in vocabulary file (Minor)