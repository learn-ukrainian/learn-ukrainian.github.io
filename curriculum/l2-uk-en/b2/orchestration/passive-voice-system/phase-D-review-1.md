**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Justification |
|---|-----------|-------|---------------|
| 1 | **Teaching Quality** | 7/10 | Effective hook with вертеп metaphor, good TTT elements (examples before rules), solid progression. But the "Laboratory Scientist (Лаборант)" persona from meta is entirely absent — replaced with ethnographic storyteller. Multiple plan-required teaching points missing (see below). The "Did I Learn?" test: yes for forms 1-4 individually, but the critical cross-form comparisons (when agent is prohibited in -но/-то vs -ся) are undertaught. |
| 2 | **Linguistic Accuracy** | 6/10 | **Grammar error in a grammar module.** Line 406: «Помилок припущено» uses genitive plural ("помилок") where accusative ("помилки") is required — contradicting the module's own rule at line 183 that -но/-то requires знахідний відмінок. Also, the -но/-то form "припущено" derives from "припустити," but the intended meaning ("committing errors") uses reflexive "припуститися помилок" which cannot form -но/-то. The plan's "critical prohibition" of instrumental agents with -но/-то is not taught. |
| 3 | **Language Quality** | 8/10 | Mostly natural, fluent Ukrainian at appropriate register for B2 teaching. Good balance of formal and conversational tone. However: colonial framing at line 130 (see Critical Issues). Some passages are overly flowery for a grammar module (e.g., the extended tattoo metaphor at line 65). |
| 4 | **Plan Compliance** | 5/10 | **Major gaps.** (1) Plan section 2 requires "Аналіз державних документів: використання форм на -но/-то в Конституції України та Акті проголошення незалежності" — completely absent. (2) Plan section 2 requires "Критична заборона: неможливість вживання агента... в орудному відмінку з формами на -но/-то" — taught only for -ся, NOT for -но/-то. (3) Plan section 3 requires "Ризик двозначності: 'дитина миється' (сама) vs 'посуд миється' (кимсь)" — absent. (4) Plan section 1 requires "вважається, досліджено, встановлено" — absent. (5) Plan section 7 requires "Фінальний чекліст" and "Місток до наступної теми" in summary — absent from that section. |
| 5 | **Activity Quality** | 7/10 | Excellent variety (11 types). Good progressive difficulty. BUT: unjumble activity line 254 has «Рішення про ремонт ухвалено міською радою» as correct answer — this is an instrumental agent with -но/-то, directly contradicting the research notes and plan. The select activity (lines 486-495) tests -но/-то agent restriction that was never explicitly taught in the lesson body. |
| 6 | **LLM Fingerprint** | 7/10 | «набагато більше, ніж» pattern appears twice (lines 12, 389). Every H2 section opens with an elaborate, poetic subtitle pattern (metaphor + cultural allusion): "Метафора прожектора," "Магія -НО/-ТО: Голос Історії та Долі," "Само-дія: Механізм природи," "Голос Громади." This structural monotony (all 4 form sections: evocative title → philosophical musing → examples → error warning) is a fingerprint. The prose is substantive but the framing is formulaic. |
| 7 | **Richness** | 8/10 | Strong cultural embedding: proverbs (line 95: «За одного битого двох небитих дають»), folk songs (line 311), вертеп metaphor, ethnographic scenarios (побілка хати). Good table (lines 342-347). Missing the planned Constitution/Independence Act cultural hook — this would have been the richest, most impactful cultural reference in the module. |
| 8 | **Factual Accuracy** | 7/10 | Grammar error at line 406 (see Linguistic Accuracy). The claim at line 148 that -но/-то forms are «унікальна риса української мови, якої немає в більшості інших слов'янських мов» is an overstatement — analogous forms exist in Polish, Czech, and other Slavic languages, though Ukrainian's -но/-то is indeed particularly productive. No fabricated claims in callout boxes. |
| 9 | **Engagement** | 8/10 | 8 engagement boxes (3× `[!culture]`, 1× `[!myth-buster]`, 1× `[!tip]`, 1× `[!warning]`, 1× `[!observe]`, 1× `[!context]`). Good variety. Direct address (ви, давайте) throughout. Confusion anticipation present (common errors sections). The summary's "Перевірте себе" section (lines 449-468) is an excellent self-check. |
| 10 | **Vocabulary Sidecar** | 2/10 | The vocabulary YAML file has invalid format — entries lack `-` list prefix. Each entry starts with bare `  lemma:` instead of `- lemma:`. YAML parsers will interpret repeated keys in a mapping, discarding all but the last entry. This is why the audit reports 0 vocabulary items. The content itself (30 terms) is appropriate, but the file is unparseable as a list. |

---

## Critical Issues Found

### Issue 1: ACTIVITY_GRAMMAR_CONTRADICTION — Unjumble presents incorrect grammar as correct answer
- **Location:** Activities file, line 254 (unjumble activity, item 4)
- **Evidence:** The answer «Рішення про ремонт ухвалено міською радою» contains an instrumental agent ("міською радою") with a -но/-то form ("ухвалено"). The research notes explicitly state: *"У формах на -но/-то агент неможливий"* (research line 28). The plan requires teaching this as a "Критична заборона" (plan line 38-40). This answer should be either: (a) «Рішення про ремонт ухвалено» (agent removed), or (b) «Міська рада ухвалила рішення про ремонт» (active voice).
- **Severity:** Critical — teaches incorrect grammar in a grammar module.

### Issue 2: GRAMMAR_ERROR_IN_LESSON — Incorrect case in example sentence
- **Location:** Content file, line 406
- **Evidence:** «Помилок припущено» uses genitive plural "помилок." The module's own rule at line 183 states: «Форма на **-но/-то** вимагає прямого додатка в Знахідному відмінку.» The accusative plural of "помилка" is "помилки," not "помилок" (genitive). Correct form: «Помилки припущено» or better «Помилок припустилися» (reflexive verb + genitive, active voice).
- **Severity:** Critical — a grammar error in a grammar lesson undermines pedagogical authority.

### Issue 3: COLONIAL_FRAMING — Ukrainian defined by contrast with Russian
- **Location:** Content file, line 130
- **Evidence:** «Українська мова, на відміну від російської, дуже неохоче утворює *активні* дієприкметники теперішнього часу» — This defines Ukrainian grammar by what Russian does, making Russian the baseline. Fix: present Ukrainian's preference independently, e.g., "Українська мова дуже неохоче утворює активні дієприкметники теперішнього часу (слова на -учий/-ючий). Це чужорідний елемент для літературної норми."
- **Severity:** Critical — per review protocol, colonial framing = Language Quality ≤ 7.

### Issue 4: PLAN_VIOLATION — Missing critical -но/-то agent prohibition
- **Location:** Section «Форма 2 — Безособові конструкції на -но/-то» (lines 145-222)
- **Evidence:** The plan (line 38-40) explicitly requires: "Критична заборона: неможливість вживання агента (виконавця) в орудному відмінку з формами на -но/-то (Learner error: виправлення конструкцій на кшталт «Закон прийнято депутатами»)." The content teaches the agent prohibition ONLY for -ся forms (section «Форма 3», lines 264-288) and NEVER mentions it for -но/-то. This is the single most important learner error for this form and it's omitted.
- **Severity:** Critical — plan-required content is missing from the most important section.

### Issue 5: PLAN_VIOLATION — Missing Конституція/Акт проголошення examples
- **Location:** Section «Форма 2 — Безособові конструкції на -но/-то»
- **Evidence:** The plan (line 35-37) requires: "Аналіз державних документів: використання форм на -но/-то в Конституції України та Акті проголошення незалежності («Закон прийнято», «Державу проголошено»)." Research notes (line 18) also flag this as cultural hook #1. The content uses generic examples (храм, закон, рух транспорту) instead. This is the strongest possible cultural anchor for -но/-то forms and it's completely absent.
- **Severity:** Major — misses a key cultural hook and plan requirement.

### Issue 6: PLAN_VIOLATION — Missing -ся ambiguity discussion
- **Location:** Section «Форма 3 — Зворотний пасив із -ся» (lines 225-289)
- **Evidence:** The plan (meta line 31) requires: "Ризик двозначності: 'дитина миється' (сама) vs 'посуд миється' (кимсь)." This key concept — that -ся can mean both reflexive ("washes itself") and passive ("is being washed") — is entirely absent. The content covers the agent restriction but not the ambiguity.
- **Severity:** Major — missing plan-required content.

### Issue 7: VOCAB_YAML_FORMAT — Vocabulary file unparseable
- **Location:** Vocabulary file (all 30 entries)
- **Evidence:** Every entry starts with `  lemma:` (indented, no dash) instead of `- lemma:`. This makes the file a single YAML mapping with repeated keys rather than a list. YAML spec: repeated keys → only last survives. Audit correctly reports 0 vocabulary items.
- **Severity:** Major — vocabulary sidecar is non-functional.

### Issue 8: PERSONA_MISMATCH — Specified persona completely absent
- **Location:** Entire content file
- **Evidence:** Meta specifies `role: Laboratory Scientist (Лаборант)` but the content uses an ethnographic storyteller voice (вертеп theatre, pottery, вишиванка, косa). Not a single laboratory or scientific experiment metaphor appears. The plan specifies this persona for a reason — a grammar module benefits from systematic, analytical framing.
- **Severity:** Minor-to-Major — doesn't affect grammar accuracy but violates build config.

### Issue 9: FACTUAL_OVERSTATEMENT — Uniqueness claim for -но/-то
- **Location:** Content file, line 148
- **Evidence:** «Це унікальна риса української мови, якої немає в більшості інших слов'янських мов у такому вигляді» — Polish has analogous constructions (e.g., "Zrobiono"), Czech has similar impersonal passives. The qualifier "у такому вигляді" provides some hedge, but "немає в більшості інших слов'янських мов" is still an overstatement. Should be more nuanced: "Ця форма особливо продуктивна в українській мові."
- **Severity:** Minor — the hedge softens it, but a superlative claim in a `[!culture]`-adjacent context should be precise.

### Issue 10: ACTIVITY_TESTS_UNTAUGHT_MATERIAL — Select items test undiscussed rule
- **Location:** Activities file, lines 486-495 (select activity, item 4)
- **Evidence:** The activity asks to identify correct -но/-то usage and marks «Збори оголошено директором» and «Вікно розбито хуліганом» as incorrect (instrumental agents). But the lesson body NEVER teaches that -но/-то cannot have instrumental agents (Issue 4). Learners would have no basis to answer correctly. This must be taught before being tested.
- **Severity:** Major — violates TTT pedagogy (test content that was taught).

---

## Factual Verification

| Claim | Source Check | Verdict |
|-------|------------|---------|
| «За одного битого двох небитих дають» (line 95) | Real Ukrainian proverb | ✅ Verified |
| «-ся» historically from «себе» (line 233) | Standard etymology, confirmed | ✅ Verified |
| «-но/-то» forms require accusative object (line 172-183) | Standard grammar, Пономарів | ✅ Verified |
| «-ся» cannot take animate agent in instrumental (lines 264-284) | Standard grammar rule | ✅ Verified |
| «Помилок припущено» (line 406) | Genitive case, should be accusative | ❌ Grammar error |
| Uniqueness of -но/-то in Slavic languages (line 148) | Polish "zrobiono" is analogous | ⚠️ Overstatement |
| «Наступаючий рік» as калька (line 132) | Confirmed: standard prescriptive advice | ✅ Verified |
| «Віруючі люди» as калька (line 135) | Confirmed: prescriptive norm recommends «віряни» | ✅ Verified |
| Soviet bureaucratic language abused passive (lines 30, 392) | Historical fact, well-documented | ✅ Verified |

---

## Verification Summary

| Check | Result | Notes |
|-------|--------|-------|
| All H2 sections from plan present? | ⚠️ PARTIAL | H2 headers match meta, but multiple plan *points* within sections are missing |
| Vocabulary hints covered? | ⚠️ PARTIAL | Required terms used in content but vocab YAML file is unparseable |
| Grammar scope respected? | ✅ PASS | No scope creep into later modules |
| Objectives addressed? | ⚠️ PARTIAL | Objectives are generic ("Identify and correctly use...") — met superficially |
| Colonial framing? | ❌ FOUND | Line 130: "на відміну від російської" |
| Russianisms? | ✅ CLEAN | No Russian calques or ghost words detected |
| LLM clichés (3+)? | ⚠️ BORDERLINE | "набагато більше, ніж" ×2; structural monotony in section openings |
| Callout variety? | ✅ PASS | 7 different types, no repeated titles |
| Factual errors? | ❌ FOUND | Grammar error at line 406; overstatement at line 148 |
| Activity errors? | ❌ FOUND | Unjumble contradicts grammar; select tests untaught material |

---

## Fix Plan

### Priority 1 (Critical — must fix before pass)

1. **Section «Форма 2 — Безособові конструкції на -но/-то»**: Add a subsection (after line 193 or replacing "Уникнення канцеляриту") explicitly teaching the -но/-то agent prohibition. Include: (a) the rule that instrumental agents are impossible with -но/-то; (b) the specific error example «Закон прийнято депутатами» → «Депутати прийняли закон»; (c) a `[!warning]` box parallel to the existing one for -ся. This is a plan requirement.

2. **Section «Форма 2 — Безособові конструкції на -но/-то»**: Add Конституція України and Акт проголошення незалежності examples. Suggested placement: within "Сфера вживання" subsection (after line 191), e.g.: «В Акті проголошення незалежності: "Проголошено незалежність України"», «У Конституції: "Права і свободи людини і громадянина гарантовано Конституцією"».

3. **Line 406**: Fix «Помилок припущено» → «Помилки допущено» (accusative, standard construction) or «Ми припустилися помилок» (active voice, as already shown on line 407).

4. **Line 130**: Remove colonial framing. Replace «Українська мова, на відміну від російської, дуже неохоче утворює *активні* дієприкметники теперішнього часу» with «Українська літературна мова дуже неохоче утворює активні дієприкметники теперішнього часу (слова на -учий/-ючий). Це чужорідний елемент для норми.»

5. **Activities — unjumble item 4** (line 254): Change «Рішення про ремонт ухвалено міською радою» to either «Міська рада ухвалила рішення про ремонт» (active) or remove "міською радою" from the word bank entirely and use a different sentence.

### Priority 2 (Major — fix for quality)

6. **Section «Форма 3 — Зворотний пасив із -ся»**: Add the planned ambiguity discussion. After line 233, add examples: «Дитина миється» (reflexive: washes herself) vs «Посуд миється» (passive: is being washed [by someone]). This explains why context matters for -ся interpretation.

7. **Vocabulary YAML**: Add `-` prefix to every entry to make it a valid YAML list: `- lemma: пасивний стан` instead of `  lemma: пасивний стан`.

8. **Content — scientific register examples**: Add "вважається, досліджено, встановлено" either in section «Вступ» (as the plan intended) or in section «Форма 3» where scientific style is discussed (lines 365-371). These are core passive examples for academic Ukrainian.

### Priority 3 (Minor polish)

9. **Line 148**: Soften «немає в більшості інших слов'янських мов» to «є особливо продуктивною в українській мові порівняно з іншими слов'янськими мовами».

10. **Persona alignment**: While a full persona rewrite is not needed, consider adding 1-2 "laboratory experiment" framings (e.g., "Проведемо лінгвістичний дослід..." or "Подивимося на цю конструкцію під мікроскопом...") to partially align with the Лаборант persona.

---

## Verdict

**FAIL — Fix Required (D.2 Repair)**

The module has a strong pedagogical foundation — the four-form structure is well-conceived, examples are culturally rich, and the engagement journey works. However, it has critical issues that prevent passing:

1. A **grammar error** in a grammar lesson (line 406)
2. **Colonial framing** (line 130)
3. A **critical plan requirement** (instrumental agent prohibition with -но/-то) is completely missing — and an activity contradicts the very rule that should have been taught
4. Key **cultural anchors** (Constitution, Independence Act) required by both plan and research are absent
5. **Vocabulary YAML** is unparseable

The content needs targeted D.2 repair focused on (a) adding the -но/-то agent prohibition, (b) fixing the grammar error and colonial framing, (c) fixing the unjumble activity, and (d) fixing the vocabulary YAML format. The core content quality is solid and does not need wholesale rewriting.