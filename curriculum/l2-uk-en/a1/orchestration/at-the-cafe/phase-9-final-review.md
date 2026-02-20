Good — the vocabulary file exists but has a different format than other vocab files. Now I have everything I need for a thorough review.

---

## Phase 9 Final QA Review: at-the-cafe (a1-19)

### Issues Found

---

#### CRITICAL: IPA — Що transcribed as Russian [ʃtɔ]
**Location:** `at-the-cafe.md:72, 73`
**Text:** `[ʃtɔ bɐˈʒɑ.je.te]` and `[ʃtɔ ˈbu.de.te ...]`
**Problem:** Ukrainian Щ = [ʃt͡ʃ], not [ʃt]. The transcription [ʃtɔ] is the **Russian pronunciation of что**. Ukrainian Що = [ʃt͡ʃɔ]. This is the single most dangerous error in the module — it teaches the Russian phoneme in a Ukrainian language course.

#### CRITICAL: IPA — Missing tie bars on Ч throughout
**Location:** Lines 31, 35, 290, 296, 316, 326
**Problem:** Ч is an affricate [t͡ʃ] but is consistently written as [tʃ] (two separate sounds). This contradicts the same document's correct usage of tie bars for Ц [t͡s] (line 55: офіціант, line 230: цукром). Inconsistency teaches learners that Ч and Ц have different phonological status when they don't.

#### CRITICAL: IPA — Missing tie bar + wrong stress on ДЖ
**Location:** `at-the-cafe.md:231`  
**Text:** `[z dʒɛˈmɔm]`
**Problem:** (a) ДЖ is an affricate [d͡ʒ], not two separate sounds. (b) Stress is wrong — джем retains stress on the stem: дже́мом [ˈd͡ʒɛ.mɔm], not джемо́м.

#### CRITICAL: IPA — Wrong stress on мед- forms
**Location:** `at-the-cafe.md:232, 239`
**Text:** `[z mɛˈdɔm]`, `[bɛz mɛˈdʊ]`
**Problem:** Standard Ukrainian stress: ме́дом [ˈmɛ.dɔm], ме́ду [ˈmɛ.dʊ]. The stress is on the stem, not the ending. Green Team flagged this — confirmed.

#### MODERATE: Сирник mistranslated as "cheesecake"
**Location:** `at-the-cafe.md:342`
**Text:** `**Сирник** is a cheesecake`
**Problem:** Factual error. A сирник is a **cottage cheese pancake** (pan-fried from сир/тварог), not a Western-style cheesecake (which is чізкейк in modern Ukrainian). A learner ordering сирник expecting cheesecake will be surprised. This matters for a café module.

#### MODERATE: Kulchytsky legend presented as verified fact
**Location:** `at-the-cafe.md:392-395`
**Text:** `"Did you know that a Ukrainian taught Europe how to drink coffee?"`, `"inventing the recipe for modern coffee culture"`
**Problem:** The meta itself says "Yuriy Kulchytsky **legend**." The research file says "credited with." But the prose states it as uncontested fact. The claim that he "taught Europe to drink coffee" and "invented the recipe" is disputed by historians (Johannes Diodato, an Armenian, received Vienna's first coffee house license in 1685). For a curriculum that includes history modules, presenting contested legends as facts undermines credibility.

#### MODERATE: Missing plan objective — "ask for recommendations"
**Location:** Plan objective #2: "Learner can ask for recommendations"
**Problem:** The content teaches how to order, specify, and pay — but never teaches how to ask for a recommendation (e.g., Що порадите?). This is a plan compliance gap. No self-check question maps to this objective either.

#### MODERATE: капучіно (plan recommended vocabulary) absent from content
**Location:** Entire module
**Problem:** The plan's `vocabulary_hints.recommended` lists капучіно but it appears nowhere in the lesson — not even on the simulated café menu, where it would be the most natural item.

#### MINOR: "liquids" → "drinks"
**Location:** `at-the-cafe.md:28`
**Text:** `the "Big Three" liquids`
**Problem:** "Liquids" is clinical/robotic. "Drinks" is natural. Green Team flagged this — agreed.

#### MINOR: Vocabulary file uses `items:` wrapper inconsistent with other vocab files
**Location:** `vocabulary/at-the-cafe.yaml:1`
**Problem:** The file uses `items:` dict wrapper while other A1 vocab files (e.g., food-and-shopping.yaml) use a bare list at root. Not a content error but a schema inconsistency.

#### NOT FIXED (flagged only): LLM fingerprint phrases
**Location:** Lines 13, 19
**Text:** "golden ticket to local culture", "the soul of a Ukrainian city"
**Assessment:** Stock LLM phrases, but the warmup voice is intentionally engaging and the persona is "Chatty Barista." These are tolerable in context. Not fixing.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
- **Що бажаєте?** [ʃtɔ bɐˈʒɑ.je.te] — What do you desire/wish?
- **Що будете замовляти?** [ʃtɔ ˈbu.de.te zɐ.mou̯ˈlʲɑ.tɪ] — What will you order?
---NEW---
- **Що бажаєте?** [ʃt͡ʃɔ bɐˈʒɑ.je.te] — What do you desire/wish?
- **Що будете замовляти?** [ʃt͡ʃɔ ˈbu.de.te zɐ.mou̯ˈlʲɑ.tɪ] — What will you order?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
2. **чай** [tʃɑi̯] — tea (masculine)
---NEW---
2. **чай** [t͡ʃɑi̯] — tea (masculine)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
4. **тістечко** [ˈtʲis.te.tʃko] — pastry/cake (neuter)
---NEW---
4. **тістечко** [ˈtʲis.tet͡ʃ.ko] — pastry/cake (neuter)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
- **з джемом** [z dʒɛˈmɔm] — with jam
- **з медом** [z mɛˈdɔm] — with honey
---NEW---
- **з джемом** [z ˈd͡ʒɛ.mɔm] — with jam
- **з медом** [z ˈmɛ.dɔm] — with honey
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
- **без меду** [bɛz mɛˈdʊ] — without honey
---NEW---
- **без меду** [bɛz ˈmɛ.dʊ] — without honey
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
In English, "check" and "bill" are often interchangeable. In Ukrainian, **чек** [tʃɛk] is the *receipt*
---NEW---
In English, "check" and "bill" are often interchangeable. In Ukrainian, **чек** [t͡ʃɛk] is the *receipt*
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
- **Готівкою чи карткою?** [ɦoˈtʲiu̯.ko.jʊ tʃɪ ˈkɑrt.ko.jʊ]
---NEW---
- **Готівкою чи карткою?** [ɦoˈtʲiu̯.ko.jʊ t͡ʃɪ ˈkɑrt.ko.jʊ]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
Leaving a tip is called **чайові** [tʃɐ.joˈʋʲi] (literally: "tea money").
---NEW---
Leaving a tip is called **чайові** [t͡ʃɐ.joˈʋʲi] (literally: "tea money").
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
- **До побачення!** [dɔ poˈbɑ.tʃe.nʲːɐ] — Goodbye!
---NEW---
- **До побачення!** [dɔ poˈbɑ.t͡ʃe.nʲːɐ] — Goodbye!
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
Before we look at the menu, you need the "Big Three" liquids that keep Ukraine running.
---NEW---
Before we look at the menu, you need the "Big Three" drinks that keep Ukraine running.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
Did you know that a Ukrainian taught Europe how to drink coffee?
**Юрій Кульчицький** (Yuriy Kulchytsky) was a hero of the Battle of Vienna in 1683. As a reward for his bravery, he asked for the bags of "strange beans" the Ottoman army left behind. The Viennese thought it was camel feed. Kulchytsky knew better.

He opened one of the first coffee houses in Vienna. But the bitter black drink was too strong for the locals. So, he added honey and milk—inventing the recipe for modern coffee culture. In Lviv, there is a statue dedicated to him.
---NEW---
There is a beloved Ukrainian legend about coffee. **Юрій Кульчицький** (Yuriy Kulchytsky) was a hero of the Battle of Vienna in 1683. According to the story, as a reward for his bravery, he asked for the bags of "strange beans" the Ottoman army left behind. The Viennese thought it was camel feed. Kulchytsky knew better.

Legend has it that he opened one of the first coffee houses in Vienna. But the bitter black drink was too strong for the locals. So, he added honey and milk — and that is how Ukrainians like to explain the birth of European coffee culture. In Lviv, there is a statue dedicated to him.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
*Note: **Медівник** is a honey cake, and **Сирник** is a cheesecake.*
---NEW---
*Note: **Медівник** is a honey cake, and **Сирник** is a cottage cheese pancake.*
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
3. **Це все?**
   - **Так, дякую.** (Yes, thanks.)
   - **Ні, ще воду, будь ласка.** (No, also water, please.)

### Mini-Dialogue: The Latte Order
---NEW---
3. **Це все?**
   - **Так, дякую.** (Yes, thanks.)
   - **Ні, ще воду, будь ласка.** (No, also water, please.)

### Asking for a Recommendation
If you are unsure what to order, you can ask:
- **Що порадите?** — What do you recommend?

This is a polite way to get the waiter's suggestion. Notice it uses the **Ви** form — just like **«Що бажаєте?»**.

### Mini-Dialogue: The Latte Order
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe.md
---OLD---
| НАПОЇ (Drinks) | ДЕСЕРТИ (Desserts) |
| :--- | :--- |
| Еспресо | Шоколадне тістечко |
| Американо | Круасан з джемом |
| Кава з молоком | Медівник |
| Чай (зелений / чорний) | Сирник |
| Сік (апельсиновий / яблучний) | Морозиво (ванільне / шоколадне) |
---NEW---
| НАПОЇ (Drinks) | ДЕСЕРТИ (Desserts) |
| :--- | :--- |
| Еспресо | Шоколадне тістечко |
| Капучіно | Круасан з джемом |
| Американо | Медівник |
| Кава з молоком | Сирник |
| Чай (зелений / чорний) | Морозиво (ванільне / шоколадне) |
| Сік (апельсиновий / яблучний) | |
===FIX_END===

---

### Summary

| Category | Issues Found | Fixed | Remaining |
|----------|-------------|-------|-----------|
| IPA (Що = Russian) | 1 (2 instances) | 1 | 0 |
| IPA (Ч tie bars) | 6 instances | 6 | 0 |
| IPA (ДЖ tie bar + stress) | 1 | 1 | 0 |
| IPA (мед- stress) | 2 | 2 | 0 |
| Factual (сирник) | 1 | 1 | 0 |
| Factual (Kulchytsky) | 1 | 1 | 0 |
| Plan compliance (recommendation) | 1 | 1 | 0 |
| Plan compliance (капучіно) | 1 | 1 | 0 |
| Style ("liquids") | 1 | 1 | 0 |
| Vocab file format | 1 | 0 | 1 (flagged) |
| LLM fingerprint | 2 | 0 | 2 (tolerable) |

**Total: 18 issues found, 15 fixed, 3 remaining (1 structural flag, 2 tolerable style)**

The Що [ʃtɔ] issue was the most serious — this is literally the Russian pronunciation of что being taught in a Ukrainian course. All IPA issues are now corrected with proper tie bars and stress placement. The Kulchytsky text now properly frames the story as a legend. The сирник mistranslation is fixed. The missing "ask for recommendations" objective is now addressed.

After these fixes, the module is sound: pedagogically strong, culturally grounded, activities are clean, grammar is accurate, and all plan sections + objectives are covered.

===VERDICT===
APPROVE
===END_VERDICT===