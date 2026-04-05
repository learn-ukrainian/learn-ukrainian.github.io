Now I have all the evidence needed. Let me compile the full review.

---

## Linguistic Scan

### 1. Russianisms
No Russianisms found.

### 2. Surzhyk
No Surzhyk found.

### 3. Calques
No calques found. `займатися спортом`, `цікавитися музикою`, `пахнути квітами` — all natural Ukrainian patterns (no hits in Антоненко-Давидович style guide = no concern).

### 4. Paronyms
No paronym errors found.

### 5. Russian characters (ы, э, ё, ъ)
None found.

### 6. Factual/grammatical errors

**CRITICAL — Wrong terminology: "склад" instead of "основа"**
The module repeatedly uses "склад" (meaning "syllable" or "composition/warehouse") where the correct Ukrainian grammatical term is **"основа"** (stem). Every Grade 4 textbook in our RAG consistently uses "основа":
- Кравцова: "Іменники чоловічого роду **з основою** на твердий приголосний"
- Захарійчук: "Іменники **з основою** на твердий приголосний, крім [ж], [ч], [ш]"
- Варзацька: "Іменники жіночого роду на -а (-я) **з основою** на..."

Affected passages:
- "Більшість іменників із **твердим складом** отримують закінчення -ою" → should be "твердою основою"
- "Якщо іменник жіночого роду має **м'який склад**" → "м'яку основу"
- "Якщо слово закінчується на твердий приголосний" (masculine section) — this phrasing is acceptable but inconsistent with the feminine section's use of "склад"

**CRITICAL — Wrong terminology: "корінь" instead of "основа" in plural section**
Section 3 uses "корінь" (root) instead of "основа" (stem). Root ≠ stem in Ukrainian linguistics. "Корінь" is the morpheme without affixes; "основа" is the word minus the inflectional ending.
- "Для слів із **твердим коренем** ми використовуємо закінчення -ами" → "твердою основою"
- "Для слів із **м'яким коренем** ми додаємо закінчення -ями" → "м'якою основою"

**CRITICAL — "дверями" is NOT a valid Ukrainian form**
VESUM verification confirms: the instrumental of "двері" has only two forms: **дверима** and **дверми**. The form "дверями" is NOT in VESUM (confirmed in the ✗ list and by `verify_words`). The module states: "Слово двері може бути дверима або дверями" — this teaches a non-existent form.

**MAJOR — Hushing consonants conflated with soft consonants**
The module states: "Для іменників із м'яким складом ми додаємо закінчення -ем" and gives **ніж → ножем** as an example. But [ж] is a **hushing** consonant, NOT a soft consonant. The textbooks explicitly separate these: "з основою на **м'який приголосний та ж, ч, ш**" (Кравцова Grade 4, с. 56). By calling ніж "soft stem," the module teaches an incorrect phonological classification.

---

## Exercise Check

**Activity markers inventory:**

| # | Type | Location | Matches plan? | Placement |
|---|------|----------|---------------|-----------|
| 1 | fill-in | After Section 1 (tools) | ✅ Yes — "Put noun in Instrumental singular" | ✅ After teaching tool endings |
| 2 | match-up | After Section 2 (transport) | ✅ Yes — "Match transport nouns to Instrumental forms" | ✅ After transport vocab |
| 3 | unjumble | After Section 3 (plural) | ✅ Yes — "Reorder words for instrumental phrases" | ✅ After plural endings |
| 4 | quiz | After Section 4 (practice) | ✅ Yes — "Choose з + Instr vs bare Instr" | ✅ After contrastive drill |
| 5 | group-sort | After Section 4 (practice) | ✅ Yes — "Sort Tool/Means vs Accompaniment" | ✅ After contrastive drill |

All 5 activity markers present, matching plan's `activity_hints` in type, focus, and item count. Well-distributed across sections.

---

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | **Covered:** All 4 content_outline sections present with their key points. All required vocabulary used in context (ручка, олівець, фарба, лінійка, ніж, ложка, автобус, потяг, літак, трамвай, засіб). All recommended vocabulary present (знаряддя, транспорт, пішки, корабель). Fixed expressions (пахнути квітами, займатися спортом) covered in section 4 as planned. **Missing:** Plan's `dialogue_situations` specifies an **art class dialogue** (Вчитель мистецтва + Учні) with tools: олівцем, пензлем, ножицями. This is entirely absent — replaced by a commute dialogue. Section 4 plan calls for "Dialogue: At school — students discuss what they write with, draw with, and how they get to school" — this dialogue is also absent. Plan references (Кравцова Grade 4, Захарійчук Grade 4) are not cited or integrated despite being excellent sources for the ending rules. |
| 2. Linguistic accuracy | 5/10 | **Three critical errors:** (1) "склад" used instead of "основа" for "stem" — "Більшість іменників із твердим складом отримують закінчення -ою" — wrong term, every textbook uses "основа." (2) "дверями" presented as valid form — "Слово двері може бути дверима або дверями" — VESUM confirms only дверима/дверми exist. (3) "корінь" used instead of "основа" in section 3 — "Для слів із твердим коренем ми використовуємо закінчення -ами." **One major error:** Hushing consonants [ж, ч, ш] conflated with soft consonants — "Для іменників із м'яким складом ми додаємо закінчення -ем" applied to ніж→ножем, but ж is hushing, not soft. All verified forms (ганчіркою, олівцем, трамваєм, кораблем, etc.) are correct per VESUM. |
| 3. Pedagogical quality | 7/10 | **Strengths:** Good PPP flow — presents concept → shows examples → provides practice. Multiple examples per grammar point (6+ tool nouns, 8+ transport nouns). Contrastive section (tool vs companion) is well-structured with clear pairs. **Weaknesses:** Wrong terminology ("склад," "корінь") means learners acquire incorrect metalanguage. The masculine -ем rule doesn't distinguish soft from hushing consonants — a learner seeing the rule won't know WHY ніж gets -ем (textbooks explicitly state "м'який приголосний та ж, ч, ш"). The III declension plural section only shows hushing examples (ночами, подорожами, речами) but the plan asks for -ями examples too. |
| 4. Vocabulary coverage | 10/10 | All 11 required words used naturally in prose: ручка (sec 1), олівець (sec 1), фарба (sec 1), лінійка (sec 1), ніж (sec 1), ложка (sec 1), автобус (sec 2), потяг (sec 2), літак (sec 2), трамвай (sec 2), засіб (sec 2). All 4 recommended words present: знаряддя (section title), транспорт (sec 2), пішки (sec 2), корабель (sec 2). Vocabulary introduced contextually in sentences, not as bare lists. |
| 5. Exercise quality | 9/10 | All 5 planned activity types present (fill-in, match-up, unjumble, quiz, group-sort). Each placed after the relevant teaching content. Item counts match plan (8, 8, 6, 8, 8). Focus descriptions align with plan's activity_hints. Minor: two activities (quiz + group-sort) are back-to-back at end of section 4 — slightly clustered, but both logically belong there after the contrastive drill. |
| 6. Engagement & tone | 8/10 | **Good:** Practical examples (daily chores, commute dialogue), cultural details (маршрутка, eating with паличками in Japan vs ложками in Ukraine). The Андрій/Марія dialogue is natural and situational. **Minor deductions:** Some meta-commentary: "Let's look at how feminine nouns change" (sec 1), "Now we will learn the spelling rules" (sec 1), "Ці прості та знайомі дії чудово показують функцію цього відмінка" — telling not showing. "This bare Instrumental form is elegant and natural" — unnecessary editorial praise. |
| 7. Structural integrity | 9/10 | All 4 planned sections present as H2 headings with correct ordering. Additional Підсумок (summary) section — appropriate for A2. Clean markdown, proper blockquote formatting for dialogue. Word count 2853 — well above 2000 target. No stray tags or formatting artifacts. |
| 8. Cultural accuracy | 9/10 | Ukrainian presented on its own terms — no "like Russian" comparisons. Маршрутка and метро as culturally authentic transport. The Japanese chopsticks example adds cross-cultural interest without centering on English. Minor: no decolonization issues. |
| 9. Dialogue & conversation quality | 6/10 | **Present:** Андрій/Марія commute dialogue — multi-turn, named speakers, natural situation, culturally appropriate (colleagues at work). **Missing:** Plan's art class dialogue (Вчитель мистецтва + Учні) covering tool vocabulary (олівцем, пензлем, ножицями) — entirely absent. Section 4's planned school dialogue (students discussing tools and commute) — also absent. Only 1 dialogue in the module vs 3 expected from the plan. The Q&A in Підсумок is formulaic, not a real dialogue. |

---

## Findings

**[LINGUISTIC ACCURACY] [CRITICAL]**
Location: Section 1, paragraphs 2–3: "Більшість іменників із **твердим складом** отримують закінчення -ою" and "Якщо іменник жіночого роду має **м'який склад**, закінчення змінюється на -ею"
Issue: "Склад" means "syllable" or "composition" — the correct grammatical term for "stem" is **"основа."** Every Grade 4 textbook (Кравцова, Захарійчук, Варзацька) uses "основа." Teaching wrong terminology means learners will be confused by all other Ukrainian grammar resources.
Fix: Replace "склад" → "основа" with correct grammatical agreement throughout section 1.

**[LINGUISTIC ACCURACY] [CRITICAL]**
Location: Section 3, paragraph 1: "Для слів із **твердим коренем** ми використовуємо закінчення -ами" and "Для слів із **м'яким коренем** ми додаємо закінчення -ями"
Issue: "Корінь" (root) ≠ "основа" (stem). These are different linguistic concepts. The module uses wrong terminology inconsistently (склад in sec 1, корінь in sec 3).
Fix: Replace "коренем" → "основою" in both instances.

**[LINGUISTIC ACCURACY] [CRITICAL]**
Location: Section 3, paragraph 1: "Слово **двері** *(door)* може бути **дверима** *(with doors)* або **дверями** *(with doors)*"
Issue: VESUM confirms only two instrumental forms for "двері": **дверима** and **дверми**. "Дверями" is NOT a valid form (confirmed ✗ in VESUM verification). Teaching a non-existent form.
Fix: Replace "дверями" with "дверми" — the actual second variant in VESUM.

**[LINGUISTIC ACCURACY] [MAJOR]**
Location: Section 1, paragraph 3: "Для іменників із **м'яким складом** ми додаємо закінчення -ем. Thus, **олівець** becomes **олівцем**, and **ніж** becomes **ножем**."
Issue: The rule states -ем is for "soft stems" but ніж has a stem ending in [ж] — a **hushing** consonant, not a soft one. Textbooks explicitly separate these: "з основою на **м'який приголосний та ж, ч, ш**" (Кравцова Grade 4, с. 56). By grouping ніж under "soft," the module teaches incorrect phonological classification.
Fix: After fixing "склад"→"основа," explicitly state the rule covers soft consonants AND hushing consonants [ж, ч, ш], matching the textbook formulation.

**[PLAN ADHERENCE / DIALOGUE QUALITY] [MAJOR]**
Location: Module-wide
Issue: Plan's `dialogue_situations` specifies an **art class** dialogue (Вчитель мистецтва + Учні) with tool vocabulary: олівцем, пензлем, ножицями. This dialogue is entirely absent. Additionally, section 4's plan calls for "Dialogue: At school — students discuss what they write with, draw with, and how they get to school" — also absent. The module has only 1 dialogue (commute) instead of the 3 expected.
Fix: Cannot be addressed with find/replace — requires content addition. Flagged for writer.

**[ENGAGEMENT & TONE] [MINOR]**
Location: Section 2: "This bare Instrumental form is elegant and natural."
Issue: Editorial praise — telling the learner the form is "elegant" rather than showing it through usage. Mild "selling the content" tone.
Fix: Remove or rephrase to factual description.

---

## Verdict: REVISE

Three critical linguistic errors (wrong terminology "склад"/"корінь" instead of "основа," non-existent form "дверями") and one major error (hushing consonants misclassified as soft) prevent shipping. These are factual errors that would teach learners incorrect Ukrainian grammar terminology and non-existent word forms. The missing dialogues are a plan adherence gap but secondary to the linguistic issues.

<fixes>
- find: "Більшість іменників із твердим складом отримують закінчення **-ою**."
  replace: "Більшість іменників із твердою основою отримують закінчення **-ою**."
- find: "Якщо іменник жіночого роду має м'який склад, закінчення змінюється на **-ею**."
  replace: "Якщо іменник жіночого роду має м'яку основу, закінчення змінюється на **-ею**."
- find: "Якщо слово закінчується на **-ія**, воно отримує закінчення **-єю**."
  replace: "Якщо основа іменника закінчується на **[й]** (слова на **-ія**), закінчення буде **-єю**."
- find: "Для іменників із м'яким складом ми додаємо закінчення **-ем**."
  replace: "Для іменників із м'якою основою, а також з основою на шиплячі [ж], [ч], [ш], ми додаємо закінчення **-ем**."
- find: "Якщо слово закінчується на **-й**, ми завжди пишемо закінчення **-єм**."
  replace: "Якщо основа закінчується на **[й]**, ми завжди пишемо закінчення **-єм**."
- find: "Для слів із твердим коренем ми використовуємо закінчення **-ами** *(-amy)*."
  replace: "Для слів із твердою основою ми використовуємо закінчення **-ами** *(-amy)*."
- find: "Для слів із м'яким коренем ми додаємо закінчення **-ями** *(-yamy)*."
  replace: "Для слів із м'якою основою ми додаємо закінчення **-ями** *(-yamy)*."
- find: "Слово **двері** *(door)* може бути **дверима** *(with doors)* або **дверями** *(with doors)*."
  replace: "Слово **двері** *(door)* може бути **дверима** *(with doors)* або **дверми** *(with doors)*."
- find: "This bare Instrumental form is elegant and natural."
  replace: "This bare Instrumental form is common in everyday speech."
</fixes>
