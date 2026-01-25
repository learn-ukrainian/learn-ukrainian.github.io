# Subsection Word Count Flexibility Guide

**For agents struggling with section-level word count violations**

## Core Principle

**Section word targets are FLEXIBLE GUIDANCE, not hard limits.**

### What MUST be met
1. ✅ **Total word count** ≥ `word_target` (e.g., 4000 for B2-HIST)
2. ✅ Each section within **±10% tolerance** of target

### What is FLEXIBLE
- ✅ You can redistribute words between sections
- ✅ One section can be 20% over if another is 10% under
- ✅ Content depth in one section is valuable

---

## Real Example: sloviany-origins (M04)

**Current state:**
```
Target: 4000 words
Actual: 3528 words ❌ (-472 short)

Sections:
✅ Вступ: 251 / 250 (+1)
❌ Читання: 489 / 650 (-161)
❌ Господарство: 382 / 600 (-218)
❌ Суспільство: 579 / 800 (-221)
✅ Духовний світ: 1237 / 600 (+637) ⭐ WAY OVER
❌ Первинні джерела: 198 / 300 (-102)
❌ Деколонізаційний: 237 / 400 (-163)
❌ Підсумок: 155 / 400 (-245)
```

**Problem diagnosis:**
- Total is 472 words SHORT ← **PRIMARY ISSUE**
- "Духовний світ" has **+637 extra words** (106% over target!)
- Multiple sections are significantly under target

---

## Fix Strategy Options

### Option A: Redistribute + Expand (RECOMMENDED)

**Step 1: Redistribute from "Духовний світ" (has 637 extra words)**

Move content to under-target sections:
- Move 200 words to "Підсумок" (most under-target: -245)
- Move 150 words to "Суспільство" (-221)
- Move 150 words to "Деколонізаційний" (-163)
- Keep ~137 words in "Духовний світ" (still slightly over, but OK)

**Step 2: Expand remaining short sections with new content**
- Expand "Читання" by ~60 words (remaining gap after redistribution)
- Expand "Господарство" by ~70 words
- Expand "Первинні джерела" by ~50 words

**Result:**
```
Total: ~4000 words ✅
All sections within ±10% ✅
```

---

### Option B: Expand All (Simple but More Work)

Just expand each under-target section:
- Expand "Читання" by 161 words
- Expand "Господарство" by 218 words
- Expand "Суспільство" by 221 words
- Expand "Первинні джерела" by 102 words
- Expand "Деколонізаційний" by 163 words
- Expand "Підсумок" by 245 words

**Total expansion needed:** ~1110 words (to hit all targets + cover deficit)

**Result:**
```
Total: ~4640 words ✅ (160% of minimum - excellent depth!)
All sections hit targets ✅
```

---

### Option C: Trim + Redistribute (Only if Total is Already Met)

**Not applicable here** because total is under 4000.

Use this when:
- Total ≥ word_target ✅
- One section massively over
- Other sections slightly under

Example (different module):
```
Total: 4100 / 4000 ✅
Section A: 1800 / 1200 (+600)
Section B: 950 / 1200 (-250)

Fix: Move 250 words from A to B
Result: A=1550, B=1200, Total=4100 ✅
```

---

## How to Redistribute Content

### Identify moveable content in over-target section

**"Духовний світ: Язичництво" (1237 words, target 600)**

Likely has:
- Main pantheon discussion (core - keep)
- Extended deity descriptions (moveable)
- Cultural context (moveable to "Суспільство")
- Modern legacy (moveable to "Підсумок")

### Example redistribution:

**From "Духовний світ":**
```markdown
### Спадщина язичництва

Навіть після хрещення Русі багато язичницьких звичаїв збереглися.
Масляниця, Купала, Коляда — це все відгомони дохристиянської епохи.
Ці традиції продовжують жити у фольклорі, піснях та обрядах.
```

**Move to "Підсумок":**
```markdown
## Підсумок

...existing content...

Навіть після хрещення Русі багато язичницьких звичаїв збереглися.
Масляниця, Купала, Коляда — це все відгомони дохристиянської епохи.
Ці традиції продовжують жити у фольклорі, піснях та обрядах,
демонструючи тяглість української культурної традиції від
найдавніших часів до сьогодення.
```

---

## Batch Fix Approach

**Apply Option A using batch-fix pattern:**

```
DIAGNOSE:
- Read all 4 files (meta, md, activities, vocab)
- Read audit report
- Identify: Total -472, "Духовний світ" +637

EXECUTE (all in one response):
1. Edit markdown:
   - Cut 500 words from "Духовний світ"
   - Paste redistributed content to under-target sections
   - Expand remaining sections by ~150 total words
2. No meta changes needed (outline is correctly budgeted at 4000)

VERIFY:
- Run audit
- Should show total ≥ 4000 ✅
- All sections within ±10% ✅
```

---

## Key Takeaways

1. **Total word count is king** - must be ≥ word_target
2. **Section targets are guidance** - ±10% tolerance
3. **Redistribution is valid** - move content between sections
4. **Over-target sections are OK** - content depth is valuable
5. **Fix in batch** - one comprehensive edit, not iterative cycles

---

## Quick Decision Tree

```
Is total ≥ word_target?
├─ NO → Expand under-target sections with new content
│        (Option B or A with expansion)
└─ YES → Are all sections within ±10%?
    ├─ YES → ✅ DONE
    └─ NO → Redistribute from over-sections to under-sections
             (Option A without expansion)
```

---

**Updated:** 2026-01-25
**See also:** NON-NEGOTIABLE-RULES.md #3, module-lesson-qa.md #3
