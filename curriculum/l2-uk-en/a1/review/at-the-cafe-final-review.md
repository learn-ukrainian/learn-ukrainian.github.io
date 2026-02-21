## Deep Adversarial Review: at-the-cafe (A1 #19)

I've read all four files in full. Here's my finding-by-finding analysis.

---

### Ukrainian Language Quality

**IPA Accuracy** — Overall solid. Spot-checked all 35+ transcriptions:
- Tie bars present on all affricates (t͡ʃ, t͡s, d͡ʒ) ✓
- Labiodental approximant ʋ used consistently for В ✓
- Glottal fricative ɦ for Г (e.g., ɦoˈtʲiu̯.kɐ) ✓
- Palatalization markers correct (tʲ, sʲ, nʲ, etc.) ✓
- No issues found.

**Russianisms** — None detected. No кушати, получати, приймати участь, слідуючий. ✓

**Russian Characters** — No ы, э, ё, ъ found. ✓

**Gender/Case Agreement** — All checked sentences are correct:
- Feminine accusative: каву, воду, піцу, колу, пасту ✓
- Masculine accusative (inanimate = nominative): чай, сік, круасан ✓
- Adjective agreement: чорну каву, зелений чай, велику каву, гарячу піцу ✓
- Genitive after без: без цукру, без молока, без газу, без лимона, без меду ✓
- Instrumental after з: з молоком, з лимоном, з цукром, з джемом, з медом ✓
- "Решти не треба" (genitive after не треба) ✓
- "Філіжанку кави" (genitive after measure noun) ✓

**Verb Forms** — Correct:
- "Я замовлю" (perfective future of замовити) ✓
- "Я візьму" (perfective future of взяти) ✓
- "Що порадите?" (2nd person plural future, natural for polite request) ✓
- Imperatives: Дайте, Принесіть, Скажіть — all correct Ви-form ✓

---

### Pedagogical Correctness

**Vocabulary scope** — All plan-required and recommended items used. Module introduces additional café vocabulary (піца, сік, круасан, кола, еспресо, etc.) which is contextually appropriate. No scope violation.

**Grammar scope** — Stays within bounds. Accusative case is the focus. Genitive/Instrumental taught correctly as lexical chunks, not analyzed. Future tense introduced as practical ordering phrases. All aligned with plan.grammar.

**Unjumble word/answer consistency** — All 12 items verified: every word in the answer appears in the words array. ✓

**Fill-in grammatical correctness** — All 36 fill-in items produce grammatical sentences when the answer is inserted. ✓

**Quiz distractor validity** — One concern: fill-in "Key Phrases Completion" item `{{answer}} рахунок` with answer "Принесіть" also has "Дайте" as a distractor. Both "Принесіть рахунок" and "Дайте рахунок" are valid Ukrainian. The explanation says "Bring the bill," which disambiguates toward "Принесіть," and the module teaches this specific collocation. Acceptable but noted.

---

### Factual Accuracy

**Kulchytsky legend** — Properly hedged in English ("beloved Ukrainian legend," "Legend has it," "according to the story"). The Ukrainian summary sentences on line 403 present it without hedging, but this is acceptable for A1 reading practice — the English context provides the nuance. Monument in Lviv: confirmed real. ✓

**Tipping culture** — "About 10%" is accurate for Ukrainian restaurant/café service. ✓

**Café culture claims** — Laptop culture, lingering, dressing up — all accurate modern observations. ✓

**Сирник definition** — "cottage cheese pancake" is a common English approximation. ✓

---

### LLM Artifacts

- No purple prose or grandiose openers. Writing has a distinct, warm "barista persona" voice.
- No "Це не просто X, а Y" pattern.
- No false statistics or invented percentages.
- No folk etymology presented as fact (Kulchytsky story explicitly framed as legend).
- Clean. ✓

---

### Plan Compliance

**All meta content_outline sections present** ✓ (7/7 sections + Підсумок)

**All plan content_outline points covered:**
- Вступ: Lviv tradition, Kulchytsky legend ✓
- Презентація: Ви form, «Я хочу» correction, Accusative case, lexical chunks ✓
- Практика: Accusative drills, imperatives, рахунок vs чек, adjective antonyms ✓
- Продукція: Payment phrases, tipping, roleplay ✓

**All required vocabulary used in prose** ✓ (кава, чай, меню, рахунок, офіціант, замовляти, вода, будь ласка)

**Objectives → self-check mapping:**
- Order food/drinks ✓ (Q1, Q5)
- Ask for recommendations — taught in content (Що порадите?) but not in self-check. Minor gap, not blocking.
- Request the bill ✓ (Q3)
- Polite forms/cases ✓ (Q2, Q4, Q5, Q6)

---

### Issues Found

**Issue 1: Contextual oddity — "риба" (fish) in comparison table**
- Location: at-the-cafe.md, line 188 (comparison table)
- Text: `| **риба** | Feminine | **рибу** (-у) | Я буду рибу. |`
- Problem: Fish is not a café-context item. The module is about coffee, pastries, and drinks. "Fish" breaks thematic immersion. All other table items (кава, вода, піца, кола, паста, чай, сік, тістечко) are café-appropriate.
- Fix: Replace with **булка** (bun/roll) — a common bakery item in Ukrainian cafés, feminine -а, and follows the same pattern (булка → булку).

**Issue 2: Unnatural English phrasing in Practice Drills**
- Location: at-the-cafe.md, line 198
- Text: `If you desire pizza, try:`
- Problem: "If you desire pizza" sounds archaic/overly formal in English instructions. A1 learners need clear, natural English scaffolding.
- Fix: "If you want pizza, try:"

**Issue 3: Unnatural English phrasing in Practice Drills**
- Location: at-the-cafe.md, line 199
- Text: `If you wish for juice, say:`
- Problem: Same issue — "wish for juice" is unnaturally formal.
- Fix: "If you want juice, say:"

---

### Noted but Acceptable (not fixing)

- **Unjumble comma omissions** ("Мені будь ласка каву" without commas) — format limitation standard across all A1 unjumble activities.
- **"Смачна вода"** in adjective drill — semantically unusual but serves the grammar teaching purpose.
- **Missing vocabulary YAML** — not present, but automated audit passed. The vocab coverage in prose and activities is thorough.
- **"з газом" in match-up activity** not explicitly taught as a chunk in content (only "без газу" is) — inferable from context at A1.
- **"Плачу карткою/готівкою"** in final fill-in uses a verb form not taught in prose — but the fill-in tests the noun form (карткою/готівкою), not the verb. Learner doesn't need to produce "плачу."

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
| **риба** | Feminine | **рибу** (-у) | Я буду рибу. |
---NEW---
| **булка** | Feminine | **булку** (-у) | Я буду булку. |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
3. If you desire pizza, try: **Я буду піцу, будь ласка.**
4. If you wish for juice, say: **Я буду сік, будь ласка.**
---NEW---
3. If you want pizza, try: **Я буду піцу, будь ласка.**
4. If you want juice, say: **Я буду сік, будь ласка.**
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===