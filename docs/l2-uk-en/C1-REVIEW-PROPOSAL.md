# C1 Curriculum Review Proposal

**Status:** PROPOSAL - For Gemini Review
**Date:** 2025-12-29
**Reviewer:** Claude Opus 4.5

---

## Summary

This document outlines issues found during the C1 curriculum review. **NO EDITS have been made** - this is a proposal for review by Gemini before implementation.

---

## C1 Structure Overview (Current)

| Phase | Modules | Count | Content |
|-------|---------|-------|---------|
| C1.1 | M01-20 | 20 | Academic Foundation |
| C1.2 | M21-35 | 15 | Professional & Social |
| C1.3 | M36-100 | 65 | **Biographies** (historical figures, ordered by birth year) |
| C1.4 | M101-120 | 20 | Advanced Stylistics & Rhetoric |
| C1.5 | M121-145 | 25 | Folk Culture & Arts |
| C1.6 | M146-160 | 15 | Literature (Ukrainian Literary Canon) |
| **Total** | | **160** | |

**Note:** C1.3 Biographies (65 modules) was moved from B2 during the 2025 restructure for better pedagogical fit.

---

## Issues Found

### Issue 1: Line 1619 - Wrong Phase Label

**Location:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md`, Line 1619

**Current:**
```markdown
#### Module 119: C1.3 Review
```

**Should Be:**
```markdown
#### Module 119: C1.4 Review
```

**Reason:** M119 is in the C1.4 Advanced Stylistics phase (M101-120), not C1.3 Biographies (M36-100). The content on line 1620-1635 confirms this - it reviews "stylistics and rhetoric" topics.

---

### Issue 2: Mermaid Diagram Completely Outdated

**Location:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md`, Lines 2589-2660

**Problem:** The mermaid diagram was created before the 2025 restructure and has completely wrong phase labels and module assignments:

| Subgraph Label | Content Shown | Actual Phase Per Plan |
|----------------|---------------|----------------------|
| `C1_3 [Phase C1.3: Stylistics]` | M36-M53 (metaphor, irony, humor) | C1.3 = **Biographies** (M36-100) |
| `C1_4 [Phase C1.4: Folk Culture]` | M56-M72 (music, crafts, beliefs) | C1.4 = **Stylistics** (M101-120) |
| `C1_Lit [Phase C1.5-6: Literature]` | M81-M100 (Kotlyarevsky, Shevchenko) | These are **Biographies** not literature |

**Required Fix:** Rebuild the entire mermaid diagram to reflect actual C1 structure:
- C1.1: M01-20 (Academic)
- C1.2: M21-35 (Professional)
- C1.3: M36-100 (Biographies - ordered by birth year: Ольга → Залужний)
- C1.4: M101-120 (Stylistics)
- C1.5: M121-145 (Folk Culture)
- C1.6: M146-160 (Literature)

---

### Issue 3: Potential Missing Review/Checkpoint for C1.3 Biographies

**Observation:** C1.3 has 65 modules (M36-100) but no explicit review or checkpoint within the phase.

**Question for Gemini:** Should C1.3 Biographies have:
1. Era-based synthesis modules (like B2.3 History)?
2. A single checkpoint at M100?
3. Nothing (CBI pedagogy doesn't require checkpoints)?

**Current plan shows:**
- M100 is final biography (Залужний)
- No M100.5 "C1.3 Review" exists
- C1.4 starts at M101

---

## Templates Status

All C1 templates are **correctly aligned** with the curriculum plan:

| Template | Modules | Status |
|----------|---------|--------|
| `c1-biography-module-template.md` | M36-100 | ✅ Aligned |
| `c1-folk-culture-module-template.md` | M121-145 | ✅ Aligned |
| `c1-literature-module-template.md` | M146-160 | ✅ Aligned |

**Activity pedagogy principle** (test LANGUAGE, not content recall) has been added to all templates.

---

## What's Good

1. **Phase structure is sound** - 160 modules, logical progression
2. **Biography ordering is excellent** - Chronological by birth year (Ольга ~890 → Залужний 1973)
3. **Templates match plan** - All module ranges correct
4. **Activity pedagogy** - All templates updated with "test language, not recall" principle
5. **No content gaps** - All phases have complete module specifications

---

## Recommended Actions

### Must Fix
1. [ ] Line 1619: Change "C1.3 Review" → "C1.4 Review"
2. [ ] Rebuild mermaid diagram with correct phase structure

### For Discussion
3. [ ] Consider adding C1.3 synthesis/checkpoint structure for 65 biographies

---

### Issue 4: Inadequate High Culture Coverage

**Problem:** C1 has insufficient coverage of Ukrainian high culture:
- **Classical Music:** Only 1 module (M141) for 250+ years of history
- **Visual Arts:** No dedicated module (only folk crafts in M131-140)
- **Ballet:** Not covered at all
- **Theater:** Only mentioned in biographies, no dedicated module
- **Architecture:** Not covered

This is inadequate for C1 cultural fluency. A learner completing C1 should be able to discuss Ukrainian contributions to world culture with sophistication.

---

## Part A: Missing Figures in C1.3 Biographies

### Current Arts/Music Coverage in Biographies

| Module | Figure | Domain | Status |
|--------|--------|--------|--------|
| M57 | Марія Заньковецька | Theater | ✓ |
| M72 | Соломія Крушельницька | Opera (performer) | ✓ |
| M85 | Віра Холодна | Cinema | ✓ |
| M88 | Катерина Білокур | Folk Art | ✓ |
| M90 | Марія Примаченко | Folk Art | ✓ |
| M93 | Алла Горська | Dissident Art | ✓ |

### Critical Missing Figures (Must Add)

**Classical Music — The curriculum has NO major composers in biographies!**

| Figure | Dates | Why Essential | Insert Position |
|--------|-------|---------------|-----------------|
| **Дмитро Бортнянський** | 1751-1825 | Baroque choral master, court composer, influenced all European sacred music | After Skovoroda (1722) |
| **Максим Березовський** | 1745-1777 | First Ukrainian to compose opera (before Гулак-Артемовський!), tragic genius | After Skovoroda |
| **Семен Гулак-Артемовський** | 1813-1873 | **"Запорожець за Дунаєм"** — first NATIONAL Ukrainian opera (1863) | After Shevchenko (1814) |
| **Микола Лисенко** | 1842-1912 | **"Father of Ukrainian classical music"** — "Тарас Бульба", "Наталка Полтавка", founded national school | After Драгоманов (1841) |
| **Микола Леонтович** | 1877-1921 | **"Щедрик"** = "Carol of the Bells" — most famous Ukrainian music worldwide, assassinated by Cheka | After Крушельницька (1872) |
| **Борис Лятошинський** | 1895-1968 | Greatest Ukrainian symphonist, "Золотий обруч", teacher of Скорик | After Хвильовий (1893) |

**Visual Arts — World-class Ukrainian artists missing:**

| Figure | Dates | Why Essential | Insert Position |
|--------|-------|---------------|-----------------|
| **Олександр Архипенко** | 1887-1964 | World-famous sculptor, cubism pioneer, MoMA collections | Revolutionary era |
| **Олександр Богомазов** | 1880-1930 | Ukrainian avant-garde master, "Ukrainian Cézanne" | Revolutionary era |
| **Казимир Малевич** | 1879-1935 | Born Kyiv, "Black Square", suprematism founder — controversial but can't ignore | Near Богомазов |

**Ballet — Ukraine's contribution to world ballet:**

| Figure | Dates | Why Essential | Insert Position |
|--------|-------|---------------|-----------------|
| **Серж Лифар** | 1904-1986 | Legendary dancer/choreographer, Paris Opera director 30 years, transformed 20th century ballet | Soviet era |

**Theater — Revolutionary figure missing:**

| Figure | Dates | Why Essential | Insert Position |
|--------|-------|---------------|-----------------|
| **Лесь Курбас** | 1887-1937 | Theater revolutionary, Березіль theater, Executed Renaissance martyr — already mentioned in B2 history, deserves biography | Revolutionary era |

---

### Proposed New Biographies (+11 modules)

Ordered by birth year, inserting into existing sequence:

| New # | Figure | Dates | Domain |
|-------|--------|-------|--------|
| +1 | Максим Березовський | 1745-1777 | Composer (Baroque opera) |
| +2 | Дмитро Бортнянський | 1751-1825 | Composer (Choral) |
| +3 | Семен Гулак-Артемовський | 1813-1873 | Composer (First national opera) |
| +4 | Микола Лисенко | 1842-1912 | Composer (National school founder) |
| +5 | Микола Леонтович | 1877-1921 | Composer ("Щедрик") |
| +6 | Казимир Малевич | 1879-1935 | Visual Arts (Avant-garde) |
| +7 | Олександр Богомазов | 1880-1930 | Visual Arts (Avant-garde) |
| +8 | Олександр Архипенко | 1887-1964 | Sculpture (Cubism) |
| +9 | Лесь Курбас | 1887-1937 | Theater (Revolutionary) |
| +10 | Борис Лятошинський | 1895-1968 | Composer (Symphonist) |
| +11 | Серж Лифар | 1904-1986 | Ballet (World legend) |

**Result:** C1.3 Biographies grows from 65 → 76 modules (M36-111)

---

## Part B: Restructure C1.5 Folk Culture & Arts

### Current Structure (Inadequate)

| Modules | Content | Problem |
|---------|---------|---------|
| M121-130 | Folk Music | ✓ Good coverage |
| M131-140 | Folk Crafts | ✓ Good coverage |
| M141 | ALL Classical Music | ❌ ONE module for 250 years! |
| M142 | Contemporary Music | ✓ OK |
| M143 | Cinema | ✓ OK |
| M144-145 | Practice + Checkpoint | ✓ OK |

### Proposed Structure (Rich & Satisfying)

**Rename phase:** C1.5 Folk Culture & Fine Arts

| Modules | Content | Details |
|---------|---------|---------|
| M121-130 | **Folk Music & Song** (10) | колискові, веснянки, думи, кобзарство — KEEP |
| M131-140 | **Folk Arts & Crafts** (10) | вишивка, писанка, кераміка — KEEP |
| M141-143 | **Classical Music** (3) | NEW: Split into eras |
| M144-145 | **Opera & Vocal Arts** (2) | NEW: Opera tradition, great singers |
| M146-147 | **Visual Arts** (2) | NEW: Icons → Avant-garde → Contemporary |
| M148 | **Ballet & Dance** (1) | NEW: Лифар, сучасний балет |
| M149-150 | **Theater** (2) | NEW: Курбас, сучасний театр |
| M151 | **Architecture** (1) | NEW: Ukrainian Baroque, wooden churches (UNESCO) |
| M152 | **Contemporary Music** (1) | Rock, pop, Eurovision — WAS M142 |
| M153 | **Ukrainian Cinema** (1) | Довженко → сьогодення — WAS M143 |
| M154-155 | **C1.5 Practice I & II** (2) | Integration |
| M156 | **C1.5 Checkpoint** (1) | Assessment |

**Total C1.5:** 36 modules (was 25) → +11 modules

---

### Detailed Module Specifications for New Content

#### M141: Класична музика I — Витоки (1745-1863)

**Focus:** Baroque and early Romantic — before national awakening

| Composer | Works | Significance |
|----------|-------|--------------|
| Максим Березовський | "Демофонт" (1773) | First Ukrainian opera composer |
| Дмитро Бортнянський | Sacred choral works | Imperial court composer, European influence |
| Семен Гулак-Артемовський | **"Запорожець за Дунаєм"** (1863) | First NATIONAL Ukrainian opera |

**Vocabulary:** бароко, класицизм, романтизм, хорова музика, опера, арія, увертюра, лібрето, прем'єра

---

#### M142: Класична музика II — Національна школа (1863-1921)

**Focus:** Лисенко and the national awakening in music

| Composer | Works | Significance |
|----------|-------|--------------|
| **Микола Лисенко** | "Тарас Бульба", "Наталка Полтавка", "Різдвяна ніч" | Founded Ukrainian national school |
| **Микола Леонтович** | **"Щедрик"** (1916) | World's most famous Ukrainian music |
| Кирило Стеценко | "Іфігенія в Тавриді", choral works | Choral tradition master |
| Яків Степовий | Романси | Ukrainian art song |

**Vocabulary:** національна школа, хоровий концерт, романс, обробка, фольклор, етнографія, збірник

---

#### M143: Класична музика III — Модернізм і сучасність (1920-present)

**Focus:** Soviet era, repression, and contemporary renaissance

| Composer | Works | Significance |
|----------|-------|--------------|
| **Борис Лятошинський** | Симфонії, "Золотий обруч" | Greatest Ukrainian symphonist |
| Левко Ревуцький | Симфонії, концерти | Major Soviet-era voice |
| **Мирослав Скорик** | **"Мелодія"**, film scores | Iconic contemporary |
| Валентин Сильвестров | "Тихі пісні" | Avant-garde master |
| Євген Станкович | Симфонії, балети | Living legend |

**Vocabulary:** симфонія, концерт, модернізм, авангард, соцреалізм, репресії, відродження, мінімалізм

---

#### M144: Оперне мистецтво

**Focus:** Ukrainian opera tradition and great singers

| Topic | Content |
|-------|---------|
| Opera houses | Львівська опера, Київська опера — history and significance |
| Repertoire | Ukrainian operas still performed today |
| Great singers | Крушельницька, Борис Гмиря, Анатолій Солов'яненко, Анатолій Кочерга |
| Contemporary | Оксана Линів (conductor), сучасні постановки |

**Vocabulary:** оперний театр, прима, тенор, бас, баритон, сопрано, диригент, постановка, лібрето

---

#### M145: Вокальне мистецтво

**Focus:** Beyond opera — choral tradition, art song, contemporary vocal

| Topic | Content |
|-------|---------|
| Choral tradition | Church choirs, Капела Думка, Капела Ревуцького |
| Art song (романс) | Лисенко, Степовий, contemporary |
| Folk crossover | ДахаБраха, ONUKA — art music meets folk |

**Vocabulary:** хор, капела, романс, вокаліст, a cappella, обробка, аранжування

---

#### M146: Образотворче мистецтво I — Від ікони до авангарду

**Focus:** Ukrainian visual arts history

| Era | Artists | Significance |
|-----|---------|--------------|
| Icons | Київська школа, Боровиковський | Sacred art tradition |
| 19th century | Шевченко (as artist!), Реалісти | National awakening |
| Avant-garde | **Богомазов**, **Архипенко**, Екстер, **Малевич** | World-class innovators |

**Vocabulary:** ікона, іконопис, портрет, пейзаж, авангард, кубізм, супрематизм, скульптура

---

#### M147: Образотворче мистецтво II — Від соцреалізму до сьогодення

**Focus:** 20th century to contemporary

| Era | Artists | Significance |
|-----|---------|--------------|
| Soviet repression | Бойчук (murdered), Соцреалізм | Art under tyranny |
| Dissidents | **Алла Горська**, Стус (visual works) | Art as resistance |
| Folk masters | **Примаченко**, **Білокур** | Naive art tradition |
| Contemporary | Пінзель revival, сучасне мистецтво | Today's scene |

**Vocabulary:** соцреалізм, андеграунд, дисидент, наївний, народний, сучасний, інсталяція, перформанс

---

#### M148: Балет і танець

**Focus:** Ukrainian contribution to world ballet

| Topic | Content |
|-------|---------|
| **Серж Лифар** | Kyiv-born, Paris Opera director (1929-1958), transformed 20th century ballet |
| Classical ballet | Київський балет, Львівська балетна школа |
| Folk dance | Гопак, Аркан, ансамблі |
| Contemporary | Kyiv Modern Ballet, сучасний танець |

**Vocabulary:** балет, балерина, хореограф, танцівник, па-де-де, пуанти, кордебалет, народний танець

---

#### M149: Театральне мистецтво I — Від витоків до Курбаса

**Focus:** Ukrainian theater history

| Era | Figures | Significance |
|-----|---------|--------------|
| Origins | Вертеп, шкільна драма | Folk and religious roots |
| 19th century | Котляревський, Кропивницький, **Заньковецька** | National theater birth |
| Revolutionary | **Лесь Курбас**, Театр "Березіль" | World-class experimental theater |

**Vocabulary:** театр, вистава, режисер, актор, актриса, драматург, п'єса, сцена, прем'єра

---

#### M150: Театральне мистецтво II — Сучасний театр

**Focus:** Contemporary Ukrainian theater scene

| Topic | Content |
|-------|---------|
| Major theaters | Франка, Молодий театр, Театр на Лівому березі |
| Contemporary directors | Сучасна режисура |
| Experimental | Dakh Daughters, театр-перформанс |
| War and theater | Театр під час війни |

**Vocabulary:** антреприза, незалежний театр, експериментальний, постдраматичний, перформанс

---

#### M151: Українська архітектура

**Focus:** Ukrainian architectural heritage

| Era | Examples | Significance |
|-----|----------|--------------|
| Kyivan Rus' | Софія Київська, Печерська лавра | Byzantine heritage |
| Ukrainian Baroque | Козацьке бароко, Мазепинський стиль | Unique national style |
| Wooden churches | Карпатські церкви (UNESCO) | World heritage |
| Modernism | Конструктивізм Харкова, Держпром | Soviet avant-garde |
| Contemporary | Сучасна архітектура, відбудова | Post-war rebuilding |

**Vocabulary:** собор, церква, лавра, бароко, дзвіниця, іконостас, фасад, купол, пам'ятка

---

## Summary: Total Impact

### Module Count Changes

| Phase | Current | Proposed | Change |
|-------|---------|----------|--------|
| C1.3 Biographies | 65 (M36-100) | 76 (M36-111) | +11 |
| C1.4 Stylistics | 20 (M101-120) | 20 (M112-131) | Renumber |
| C1.5 Culture & Arts | 25 (M121-145) | 36 (M132-167) | +11 |
| C1.6 Literature | 15 (M146-160) | 15 (M168-182) | Renumber |
| **Total C1** | **160** | **182** | **+22** |

### What Learners Gain

After completing the expanded C1, learners can:

1. **Discuss Ukrainian classical music** from Бортнянський (1751) to Сильвестров (present)
2. **Recognize landmark works** — "Запорожець за Дунаєм", "Щедрик", "Тарас Бульба", "Мелодія"
3. **Appreciate Ukrainian visual arts** — from icons through avant-garde to contemporary
4. **Understand ballet heritage** — Лифар's world impact
5. **Analyze theater tradition** — Курбас's revolutionary approach
6. **Recognize architectural styles** — Ukrainian Baroque, wooden churches
7. **Connect arts to history** — how culture survived repression and flourishes today

---

## For Gemini Review

Please verify:
1. Are the 11 proposed new biographies the right choices? Any to add/remove?
2. Is the C1.5 restructure logical and comprehensive?
3. Should Малевич be included (controversial — born Kyiv but claimed by Russia/Poland)?
4. Are there any other major cultural figures missing?
5. Is +22 modules acceptable, or should we trim?
6. Any overlap concerns with B2 history content (Курбас mentioned there)?

After Gemini approval, Claude will implement:
1. Update C1-CURRICULUM-PLAN.md with new structure
2. Renumber all affected modules
3. Write module specifications for new content
4. Update mermaid diagram
5. Fix the typo issues (Issues 1-3)

This proposal transforms C1 from "adequate" to "world-class cultural education."

---

**Last Updated:** 2025-12-29
