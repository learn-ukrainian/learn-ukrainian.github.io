# Рецензія: Структура речення

**Level:** B1 | **Module:** 4
**Overall Score:** 8.2/10
**Status:** PASS
**Reviewed:** 2026-02-21

## Plan Verification

```
Plan-Content Alignment: PARTIAL PASS
- Sections: PASS — All 10 meta sections present as H2/H3 (one H1 heading error on Підсумок)
- Vocabulary: 9/9 required terms covered in prose; 5/6 recommended terms present. MISSING: «ускладнене речення», «вставні слова» (plan §4.4.2). Vocabulary YAML file NOT FOUND.
- Grammar scope: PASS — No scope creep into relative/concessive clauses
- Objectives: PASS — All 3 plan objectives addressed
- Plan gap: Plan section "Класифікація речень за Державним стандартом" requires «ускладнене речення» and «вставні слова» per State Standard §4.4.2 — neither appears in content
- Activity gap: Plan specifies fill-in focus "Label sentence components" but actual fill-in is about choosing conjunctions; quiz has 8 items vs plan's 10+
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Strong teaching arc with engaging dialogues and cultural hooks; metaphor overload slightly detracts from reading flow |
| 2 | Coherence | 8/10 | <7 | Logical progression from main→secondary parts→sentence types→punctuation→practice; H1/H2 inconsistency on Підсумок; «Коли ми використовуємо» blocks appear for Підмет/Присудок/Означення but not Додаток/Обставина |
| 3 | Relevance | 9/10 | <7 | Directly addresses all 3 plan objectives; terminology is essential for B1 course progression |
| 4 | Educational | 8/10 | <7 | Step-by-step parsing walkthrough is pedagogically excellent; TTT partially applied; missing «ускладнене речення» and «вставні слова» from plan |
| 5 | Language | 8/10 | <8 | Ukrainian grammar is correct throughout; no Russianisms or calques; some passages are overwrought with stacked metaphors (see LLM Fingerprint); dialogue 1 has a role-logic error |
| 6 | Pedagogy | 8/10 | <7 | Good examples-before-rules approach in several sections; three dialogues model real usage; missing plan-required content reduces coverage |
| 7 | Immersion | 9/10 | <6 | ~90-93% Ukrainian (two English bridging paragraphs ~135 words in intro + parenthetical terms); target 70-85% — exceeds minimum comfortably |
| 8 | Activities | 8/10 | <7 | 7 diverse activity types; error-correction activity is creative; quiz has 8/10+ items per plan; fill-in deviates from plan focus |
| 9 | Richness | 8/10 | <6 | Шкільний ритуал підкреслення [!culture] is excellent; Ukrainian names in dialogues (Олена, Андрій, Тарас, Катя); school nostalgia dialogue feels authentic |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5; well-scaffolded English bridging; dense but manageable |
| 11 | LLM Fingerprint | 7/10 | <7 | ~12 distinct non-persona metaphors including flagged clichés «двигун» and «архітектура»; subsection structure is somewhat formulaic (term→explanation→questions→underlining→examples) |
| 12 | Linguistic Accuracy | 9/10 | <9 | Grammar explanations accurate for B1; sentence analyses correctly parsed; minor simplification about підмет always being називний відмінок (genitive subjects exist but outside B1 scope) |

**Weighted Overall:** (8×1.5 + 8×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 9×1.0 + 8×1.3 + 8×0.9 + 8×1.3 + 7×1.0 + 9×1.5) / 14.0 = (12 + 8 + 9 + 9.6 + 8.8 + 9.6 + 9 + 10.4 + 7.2 + 10.4 + 7 + 13.5) / 14.0 = 114.5 / 14.0 = **8.2/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no Ukrainian-vs-Russian comparisons
- Grammar scope: [CLEAN] — no relative/concessive clause content
- Activity errors: [MINOR] — quiz item count 8 vs plan 10+; fill-in focus deviation
- Beginner safety: 4/5

## Critical Issues Found

### Issue 1: Metaphor Overload (LLM Fingerprint)
- **Location**: Throughout — Присудок section, Означення section, Обставина section, Сполучники section, and others
- **Original**: «Присудок — це двигун речення, який запускає події.» / «Означення (attribute) — це «художник» у реченні.» / «Це нагадує азбуку Морзе або координати на мапі» / «спеціальний мовний «цемент»» / «серце речення» / «король і королева на шахівниці» / «фотографія; фільм» / «чорно-білий малюнок кольоровим» / «ноти для вашого голосу» / «математичне рівняння / детективну загадку» / «однокімнатні квартири / палаци»
- **Problem**: ~12 distinct metaphors from non-persona domains (chess, anatomy, art, Morse code, photography, music, cement, detective, math). Rubric flags >4 metaphors → LLM Fingerprint ≤7. «двигун» and «архітектура» are specifically listed clichés. The module reads like it never met a metaphor it didn't adopt.
- **Fix**: Replace the most egregious instances (see Fix Plan). Full resolution would require significant structural rewrite of 6+ paragraphs.

### Issue 2: Dialogue 1 Role-Logic Error
- **Location**: Section "Діалог 1: Редактор і Письменник"
- **Original**: «Ти поставила підмет у самий кінець речення.»
- **Problem**: Андрій is labeled "(автор)" and Олена is "(редактор)". Олена opens with "подивися на це есе" — implying it's Андрій's essay she's editing. But Андрій then says "Ти поставила підмет" (YOU placed the subject) to Олена, contradicting the established roles. If it's his essay, he should say "Тут підмет стоїть у кінці" or "Я поставив підмет."
- **Fix**: Change to role-neutral phrasing: «Тут підмет стоїть у самому кінці речення.»

### Issue 3: Unexplained Conjunction Switch in Dialogue 2
- **Location**: Section "Діалог 2: Страх перед комами"
- **Original**: «Виходить: «Я хочу піти в парк, та я хочу купити морозиво».»
- **Problem**: Марк's original sentence uses conjunction «і», but Іра's "correction" silently switches it to «та». In a module about punctuation, this unexplained lexical change (which is NOT the teaching point — the comma is) could confuse learners into thinking the conjunction change is part of the fix.
- **Fix**: Keep the original conjunction: «Я хочу піти в парк, і я хочу купити морозиво».

### Issue 4: Missing Plan-Required Content
- **Location**: Plan section "Класифікація речень за Державним стандартом", points 2-3
- **Original**: N/A — content absent
- **Problem**: Plan explicitly requires coverage of «ускладнене речення» (complicated simple sentences) with homogeneous parts and «вставні слова» (parenthetical words) per State Standard §4.4.2. Neither term appears in the content. Однорідні члени get a brief mention in the simple sentence section but without the term «ускладнене речення».
- **Fix**: Cannot add new sections in Phase D fix pass. Flag for Phase F or rebuild consideration.

### Issue 5: Missing Vocabulary YAML File
- **Location**: `curriculum/l2-uk-en/b1/vocabulary/sentence-structure.yaml`
- **Original**: (file not found)
- **Problem**: Plan includes 9 required + 6 recommended vocabulary items with detailed descriptions. No vocabulary file exists. This is a build pipeline issue, not a content quality issue, but it means learners have no structured vocabulary reference.
- **Fix**: Requires Phase C rebuild to generate vocabulary file. Cannot create in Phase D.

### Issue 6: Підсумок Heading Level
- **Location**: Final section
- **Original**: «# Підсумок»
- **Problem**: Uses H1 heading while all other sections use H2. Inconsistent document structure.
- **Fix**: Change to «## Підсумок»

## Ukrainian Language Issues

| Location | Current | Corrected | Type |
|------|---------|-----------|------|
| Діалог 1 | «Ти поставила підмет у самий кінець речення.» | «Тут підмет стоїть у самому кінці речення.» | Role Logic |
| Діалог 2 | «Я хочу піти в парк, та я хочу купити морозиво» | «Я хочу піти в парк, і я хочу купити морозиво» | Unexplained Lexical Change |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — Content is dense but well-organized with clear section breaks
- Instructions clear? **Pass** — English bridging in intro effectively sets up terminology
- Quick wins? **Pass** — The match-up activity provides immediate terminology practice
- Ukrainian scary? **Pass** — Parenthetical English translations reduce anxiety
- Come back tomorrow? **Marginal** — Module is long (~4000 words); a weaker B1 learner might fatigue before the dialogues

## Strengths
- The **шкільний ритуал підкреслення** [!culture] box is genuinely excellent — it grounds abstract syntax in embodied cultural practice and creates an emotional connection
- The **step-by-step parsing algorithm** (section "Синтаксис у дії") is the module's pedagogical crown jewel — clear, methodical, and genuinely teaches the skill
- **Dialogue 3** (school nostalgia) rings authentic and demonstrates that syntactic analysis is a shared Ukrainian cultural experience, not just academic exercise
- The **[!warning] Іменник чи Підмет?** box directly addresses Plan Error Pattern 1 with a concrete example (Україну as додаток, not підмет)
- The **[!myth-buster] Паніка «Pro-Drop»** box skillfully addresses Plan Error Pattern 2 and reassures learners about impersonal sentences
- **Error-correction activity** is creative and pedagogically on-target for punctuation practice

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Replace «Присудок — це двигун речення, який запускає події.» with non-cliché phrasing
2. Replace «Означення (attribute) — це «художник» у реченні. Воно розфарбовує предмети...» with direct pedagogical language
3. Replace «Це нагадує азбуку Морзе або координати на мапі, які уточнюють деталі.» with simpler description
4. Replace «спеціальний мовний «цемент»» in Сполучники section with direct language

**Note**: Full resolution to 9/10 would require removing 8+ more metaphors (серце, король/королева, фотографія/фільм, ноти, etc.), which exceeds targeted fix scope. Recommend flagging for next build iteration.

**Expected score after fix:** 8/10 (reduced from ~12 to ~8 non-persona metaphors — still >4 per rubric)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Fix dialogue 1 role confusion — currently breaks immersion
2. Fix dialogue 2 conjunction switch — currently creates pedagogical noise
3. Address «Коли ми використовуємо» inconsistency (present for 3/5 sentence parts)

**Expected score after fix:** 8→9 contingent on dialogue fixes

### Educational: 8/10 → 8/10
**What to fix:**
1. Missing «ускладнене речення» / «вставні слова» — cannot add in Phase D (would require new content)
2. Quiz needs 2 more items to meet plan's 10+ — cannot add in Phase D

**Expected score after fix:** 8/10 (plan gaps require rebuild, not fix pass)

### Coherence: 8/10 → 9/10
**What to fix:**
1. Change «# Підсумок» → «## Підсумок»

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(8×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 9×1.0 + 8×1.3 + 8×0.9 + 8×1.3 + 8×1.0 + 9×1.5) / 14.0
= (12 + 9 + 9 + 9.6 + 8.8 + 9.6 + 9 + 10.4 + 7.2 + 10.4 + 8 + 13.5) / 14.0
= 116.5 / 14.0 = 8.3/10
```

## Verification Summary

- Content lines read: ~280 (full markdown)
- Activity items checked: 58 (12 match-up pairs + 10 mark-the-words + 8 quiz + 6 unjumble + 6 error-correction + 8 fill-in + 8 true-false)
- Ukrainian sentences verified: 47 (all examples, dialogue lines, and activity sentences)
- IPA transcriptions checked: 0 (none present in content)
- Issues found: 6 (3 critical content issues, 1 plan compliance gap, 1 missing file, 1 heading error)

## Verdict

**PASS**

The module delivers effective, engaging teaching of syntactic terminology with strong cultural grounding and a well-structured progression from main parts through sentence types to full parsing. The core pedagogical content is accurate and well-scaffolded. Two blocking fix items: (1) dialogue 1 role-logic error and dialogue 2 conjunction switch need correction to avoid learner confusion; (2) metaphor density should be reduced where possible. The missing vocabulary file and plan-required «ускладнене речення» content are pipeline/rebuild concerns, not Phase D blockers.