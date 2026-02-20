All fixes are applied and verified. Here is the complete summary:

---

## Issues Found and Fixed

### Critical — Activities

**Issue 1 — Untaught word `тарілка/супу` in match-up activity**
`activities/food-and-shopping.yaml` — "тарілка" (plate) and "супу" never appear in the lesson content. Replaced with a taught combination, then simplified to remove the problematic pair entirely (9 pairs remain, all taught vocabulary).

**Issue 2 — Untaught word `олія` in Genitive fill-in activity**
`activities/food-and-shopping.yaml` — "олії" / "олія" never taught. Replaced with the Genitive fill-in item removed (11 items remain, all taught).

**Issue 3 — Untaught words `лимонад` / `какао` in group-sort**
`activities/food-and-shopping.yaml` — Neither appears in lesson prose. Removed both items from the Напої group.

### IPA Errors — Vocabulary file

**Issue 4 — `[wɔˈdɑ]` → `[ʋɔˈdɑ]`**
Ukrainian В is always [ʋ] (labiodental), not [w] (bilabial). The prose file correctly used [ʋɔˈdɑ]. Fixed.

**Issue 5 — `[tʃɑj]` → `[t͡ʃɑj]`**
Ч is an affricate requiring a tie bar. Fixed.

**Issue 6 — `[ˈjɑblʊkɔ]` → `[ˈjɑblukɔ]`**
Ukrainian У does not reduce to [ʊ] (a Russian-style reduction). Fixed to match prose.

**Issue 7 — `[kʊpʊˈʋɑtɪ]` → `[kupuˈʋɑtɪ]`**
Same [ʊ] reduction error. Fixed to match prose.

### Vocabulary file — Completeness
**Issue 8 — Missing ~15 taught words**
Added: цибуля, морква, свинина, йогурт, булка, батон, пакет, склянка, чашка, пачка, літр, банан, лимон, помідор. Vocabulary file grew from 20 to 35 entries.

### Content Prose

**Issue 9 — Duplicated Ukrainian sentence (LLM draft artifact)**
Two back-to-back near-identical sentences at the top of "Овочі та Фрукти." Removed the weaker duplicate.

**Issue 10 — Wrong Ukrainian teaser in Напої section**
"Поговоримо про види хліба" (let's talk about bread types) in the drinks section. Fixed to "Поговоримо про напої."

**Issue 11 — Сало incorrectly called `м'ясо`**
Factually imprecise and self-contradictory. Fixed to "pork-derived product" with appropriate clarification.

===VERDICT===
APPROVE
===END_VERDICT===