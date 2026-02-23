<!-- content-hash: b3cdf6435373 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Plan Adherence | 9/10 | All 4 H2 sections present and aligned with meta outline. Vocabulary scope matches plan requirements. Minor: plan separates toast/etiquette into section 4 but content places it in section 1. |
| 2 | Immersion Balance | 8/10 | 35.5% Ukrainian per audit, at the floor of 35-55% target. For an A1.4 phase module, this is borderline low — more Ukrainian could be woven in, especially in section «Культурний контекст: Українська гостинність» which already demonstrates a bilingual pattern. |
| 3 | Language Quality | 7/10 | **Russianism detected**: «красиві картини» (line 337) — project standards explicitly list красивий→гарний as flagged Russianism. Line 391 «В Україні не можна бути в куртці у ресторані» is slightly unnatural (more natural: «не прийнято сидіти в куртці»). Unjumble answers systematically omit required commas with «будь ласка» (5 instances). |
| 4 | Factual Accuracy | 9/10 | Cultural facts verified: three-course structure (Перше/Друге/Третє), tipping at 10% matches research notes, «Будьмо!» toast with «Гей!» response is accurate, proverbs «Хліб — усьому голова» and «Гість у дім — Бог у дім» are genuine. Menu prices plausible for 2024-era Ukrainian restaurants. |
| 5 | Activity Quality | 7/10 | 10 activities, good type variety (match-up ×3, group-sort ×1, quiz ×2, fill-in ×2, unjumble ×2). **Critical**: unjumble answers missing commas (5 instances). **Inconsistency**: fill-in teaches «дайте воду» (Acc., line 174) but unjumble uses «дайте води» (Gen. partitive, line 455) without explanation — confusing at A1. Quiz distractors are appropriately simple. |
| 6 | Richness | 8/10 | Good cultural hooks: Будьмо toast (line 57-71), гардероб etiquette (line 389-396), bread culture (line 398-404), «Смачного!» usage (line 406-416). Two genuine proverbs. Sample menu is a nice touch. Extended reading passage «Вечеря у Львові» (line 329-362) is engaging. Deducted for formulaic Ukrainian-then-English pattern in section «Культурний контекст: Українська гостинність» (5 repetitions of same structure). |
| 7 | Lesson Quality | 8/10 | "Would I Continue?" test: 3/5 pass. PASS: instructions clear (step-by-step Крок 1-6), Ukrainian not scary (good English support), content engaging. FAIL: no warm welcome/preview ("Привіт!" absent, no "Today you'll learn..."), no quick wins (massive content dump before any practice). Pacing concern: Section «Презентація: Як зробити замовлення» introduces ~30 new terms before any active practice. |
| 8 | LLM Fingerprint | 7/10 | **Structural monotony**: 3 of 4 H2 sections open with "Let's..." pattern (lines 17, 79, 254). Section «Культурний контекст: Українська гостинність» uses formulaic "Ukrainian sentence → English expansion" ×5 (lines 379, 385, 391, 400, 408). Line 379 + 381: redundant restatement of the same idea in two languages without adding value. |
| 9 | Humanity & Warmth | 7/10 | Zero "Don't worry" moments. Zero encouragement phrases ("Great!", "Well done!"). Only one "You can now..." validation at the very end (line 430). No warm greeting. Direct address ("you") is present throughout but emotional scaffolding is absent. For A1, this is too cold — learners need more reassurance. |

---

## Critical Issues Found

### Issue 1: Russianism «красиві» (AUTO-FAIL LIST)
- **Location**: Line 337, section «Практика: Діалоги у ресторані»
- **Citation**: «На стіні висять красиві картини.»
- **Problem**: Project standards explicitly list красивий→гарний as a flagged Russianism. While "красивий" exists in SUM, the project's review protocol marks it for replacement.
- **Fix**: Replace «красиві картини» with «гарні картини» on line 337. Also update «Картини — paintings» in Словничок (line 370) — the word itself is fine, only the adjective needs correction.

### Issue 2: Unjumble Activities Missing Commas with «будь ласка»
- **Location**: Activities file, lines 231, 237, 250, 449, 474
- **Citations**: 
  - Line 231: `answer: 'Столик на двох будь ласка'` → should be `'Столик на двох, будь ласка'`
  - Line 237: `answer: 'Можна меню будь ласка'` → should be `'Можна меню, будь ласка'`
  - Line 250: `answer: 'Дайте будь ласка рахунок'` → should be `'Дайте, будь ласка, рахунок'`
  - Line 449: `answer: 'Мені будь ласка каву'` → should be `'Мені, будь ласка, каву'`
  - Line 474: `answer: 'Можна рахунок будь ласка'` → should be `'Можна рахунок, будь ласка'`
- **Problem**: «Будь ласка» is a parenthetical/inserted phrase (вставне слово) that requires comma separation in Ukrainian orthography. The content file itself uses commas correctly (e.g., line 123: «Дайте, будь ласка, меню.»), but all 5 unjumble answers omit them. This teaches incorrect punctuation.
- **Fix**: Either add comma-bearing tokens to the word arrays, or add commas to the answer strings so learners see correct punctuation in the model answer.

### Issue 3: Case Inconsistency Between Activities
- **Location**: Activities file, fill-in line 174 vs unjumble line 455
- **Citations**:
  - Fill-in (line 173-176): `sentence: 'Будь ласка, дайте {{answer}}.'` with `answer: 'воду'` (Accusative)
  - Unjumble (line 452-455): words `['Дайте', 'будь', 'ласка', 'води']` with `answer: 'Дайте будь ласка води'` (Genitive partitive)
- **Problem**: The same verb «дайте» takes Accusative «воду» in one activity and Genitive «води» in another. Both are grammatically correct (Acc = specific, Gen = partitive), but at A1, the module teaches Accusative for ordering (section «Презентація: Як зробити замовлення», line 178) — introducing Genitive without explanation in the activities contradicts the grammar presentation.
- **Fix**: Change unjumble item to use «воду» (Acc.) for consistency, or add a brief note about partitive Genitive.

### Issue 4: Missing Beginner Safety Elements
- **Location**: Global — entire module
- **Problem**: The module lacks required emotional safety markers for A1:
  - No warm welcome/greeting (zero instances of "Привіт!" or equivalent)
  - No learning preview ("Today you'll learn..." absent)
  - No "Don't worry" / reassurance moments (zero instances)
  - No mid-module encouragement (zero instances of "Great!", "Well done!", "You've got this!")
  - Only one "You can now..." validation, at line 430 (very end)
  - The opening quote block (line 11-13) jumps straight into why the topic matters without first welcoming the learner
- **Required fix**: Add a warm opening before the quote block, add 2-3 encouragement moments within section «Презентація: Як зробити замовлення» (after grammar tables and between steps), and add at least one "Don't worry" moment after the Accusative case introduction (line 178-192).

### Issue 5: Structural Monotony (LLM Fingerprint)
- **Location**: Section openings and section «Культурний контекст: Українська гостинність»
- **Problem A — Section openings**: Three of four H2 sections open with "Let's..." pattern:
  - Line 17: "Before we look at the menu, let's understand..."
  - Line 79: "Now that we are seated, let's learn..."
  - Line 254: "Let's see these phrases in action."
- **Problem B — Formulaic subsection structure** in section «Культурний контекст: Українська гостинність»: Every subsection follows the identical pattern of a bold Ukrainian sentence → English expansion:
  - Line 379: «В Україні ресторан — це більше, ніж просто їжа.» → English
  - Line 385: «Багато ресторанів мають живу музику.» → English
  - Line 391: «В Україні не можна бути в куртці у ресторані.» → English
  - Line 400: «Українці дуже люблять хліб.» → English
  - Line 408: «Це дуже важлива фраза.» → English
- **Problem C — Redundancy**: Lines 379+381 say the same thing twice — Ukrainian says "a restaurant is more than just food" and English says "Dining out is more than just eating" — without adding new information.
- **Fix**: Vary section openings (use questions, direct address, or scenario-setting). Break the Uk→En pattern in section «Культурний контекст: Українська гостинність» by using different presentation styles (dialogue snippets, "imagine you..." scenarios, tables). Remove the English redundancy on line 381.

---

## Factual Verification

| Claim | Location | Status | Notes |
|-------|----------|--------|-------|
| Three-course meal structure (Перше/Друге/Третє) | Line 19-38, section «Розминка: Структура меню та етикет» | Verified | Matches research notes line 19 |
| «Будьмо!» toast with «Гей!» response | Line 57-71, section «Розминка: Структура меню та етикет» | Verified | Matches research notes line 18 |
| Tipping at 10-15% | Line 243-244, section «Презентація: Як зробити замовлення» | Verified | Research notes say 10%; content says 10% polite / 15% generous — reasonable expansion |
| «Хліб — усьому голова» proverb | Line 403, section «Культурний контекст: Українська гостинність» | Verified | Genuine Ukrainian proverb |
| «Гість у дім — Бог у дім» proverb | Line 420, section «Культурний контекст: Українська гостинність» | Verified | Genuine Ukrainian proverb |
| Рахунок vs Чек distinction | Line 246, section «Презентація: Як зробити замовлення» | Verified | Correct: рахунок = bill before payment, чек = fiscal receipt after |
| «Без решти» = Keep the change | Line 245, section «Презентація: Як зробити замовлення» | Verified | Standard Ukrainian phrase |
| Accusative case rules for masculine/feminine/neuter | Lines 180-191, section «Презентація: Як зробити замовлення» | Verified | Correct: masc. inanimate unchanged, fem. -а→-у, neuter unchanged |
| «Счёт» flagged as Russian | Line 248-250, [!myth-buster] | Verified | Legitimate myth-buster use; «рахунок» is the correct Ukrainian term per research notes line 24 |

**Colonial framing check**: The [!myth-buster] on line 248-250 mentions Russian but is a legitimate exception — it explicitly educates learners to avoid a common Russianism, which is exactly what myth-buster blocks are for. No other colonial framing detected.

---

## Verification Summary

| Check | Result |
|-------|--------|
| Russianism scan | **FAIL** — «красиві» on line 337 (project auto-fail list: красивий→гарний) |
| Colonial framing | PASS — [!myth-buster] on line 250 is legitimate |
| Grammar scope violations | PASS — Accusative and Future Tense are the focus; Genitive with «без» is within plan scope |
| Factual accuracy | PASS — All claims verified against research notes |
| Activity errors | **FAIL** — 5 unjumble answers missing commas; case inconsistency «воду» vs «води» |
| Beginner safety | **FAIL** — Missing warm welcome, zero encouragement, zero "don't worry" moments |
| LLM fingerprint | **FAIL** — 3/4 sections open with "Let's...", formulaic Uk→En pattern ×5 in section «Культурний контекст: Українська гостинність» |
| Word count | PASS — 2865/2000 (143.2%, above minimum) |
| Callout box verification | PASS — 7 callout boxes, all factually accurate, no fabricated claims |

---

## Verdict

**REVISE** — The module has strong pedagogical content (well-structured steps, excellent sample menu, engaging dialogues, rich cultural hooks) but has 5 issues requiring repair:

1. **Russianism «красиві»** → replace with «гарні» (line 337)
2. **Unjumble comma omissions** → add commas to all 5 «будь ласка» answer strings
3. **Case inconsistency** → align «воду»/«води» usage across activities
4. **Beginner warmth deficit** → add welcome, 2-3 encouragement moments, 1+ "don't worry" moment
5. **LLM fingerprint** → vary section openings and break formulaic pattern in section «Культурний контекст: Українська гостинність»

Issues 1-3 are mechanical fixes. Issues 4-5 require moderate prose additions/edits. Overall content quality is good — the restaurant scenario is practical, the grammar teaching is clear, and the cultural content is authentic. The module needs a warmth pass to meet A1 beginner standards.