# Рецензія: Структура речення

**Level:** B1 | **Module:** 4
**Overall Score:** 8.2/10
**Status:** PASS
**Reviewed:** 2026-02-21

## Plan Verification

```
Plan-Content Alignment: PARTIAL PASS
- Sections: PASS — All 5 plan sections covered (split across 10 meta sections). Content follows
  the meta's more granular structure, which is acceptable.
- Vocabulary: 9/9 required covered in prose; 4/6 recommended covered. MISSING: «ускладнене речення»
  and «вставні слова» (§4.4.2 items). Vocabulary YAML file not found (infrastructure gap).
- Grammar scope: CLEAN — no scope creep into B1.2+ material. Complex sentence subtypes correctly
  deferred to b1-26, b1-35 per SCOPE comment.
- Objectives: PASS — all 3 objectives addressed (identify parts, distinguish clauses, name types).
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Strong opening hook with «Чому це важливо?» and consistent construction metaphor aligned with persona. Dialogues bring theory to life. Heavy metaphor density slightly undermines naturalness. |
| 2 | Coherence | 9/10 | <7 | Logical progression: intro → main parts → secondary parts → sentence types → clause hierarchy → conjunctions → punctuation → full analysis → dialogues → summary. Each section builds on the previous. |
| 3 | Relevance | 9/10 | <7 | Directly addresses B1 metalinguistic needs. Cultural hook (school underlining ritual) contextualizes the content. Practical application shown in parsing exercises and dialogues. |
| 4 | Educational | 8/10 | <7 | Core sentence analysis concepts well explained with worked examples. Gap: plan-required «ускладнене речення» (complicated simple sentences with homogeneous parts, §4.4.2) and «вставні слова» (parenthetical words) not covered. |
| 5 | Language | 8/10 | <8 | Ukrainian prose is natural and well-written. No Russianisms detected. One pedagogical inconsistency in Dialogue 2 where «і» is switched to «та» without justification. Minor euphony question with «В українській мові» at section start (prefer «У»). |
| 6 | Pedagogy | 8/10 | <7 | Good TTT elements — warning/tip boxes anticipate confusion before rules. Error patterns (іменник vs підмет, pro-drop, додаток vs обставина) integrated organically. Practice is concentrated at end (activities file) rather than integrated throughout prose. |
| 7 | Immersion | 8/10 | <6 | ~72% Ukrainian, within 70-85% target for B1.0 Bridge. English paragraphs in intro serve as deliberate metalanguage bridge. English terms in parentheses throughout are appropriate scaffolding. |
| 8 | Activities | 7/10 | <7 | 7 activity types with ~56 items — good variety. Quiz has only 8 items vs plan-required 10+. Extra types (unjumble, error-correction) add value. All answer keys verified correct. |
| 9 | Richness | 8/10 | <6 | 8 engagement boxes (culture, warning, observe, myth-buster, 3× tip, context). School underlining ritual is a strong cultural hook. Dialogues feel authentic. Missing vocabulary YAML reduces overall richness score. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Clear explanations, warm teacher voice, progressive complexity. Warning boxes preempt confusion. Self-check questions at end provide closure. |
| 11 | LLM Fingerprint | 7/10 | <7 | >4 distinct metaphor families (architecture, anatomy, royalty, art, film, engine). «двигун» is explicitly flagged cliché. Structural monotony test: PASS (varied section openings). No "це не просто" patterns. |
| 12 | Linguistic Accuracy | 9/10 | <9 | All grammar rules accurate. Subject/predicate analysis correct. Case question assignments correct. Nominal predicate explanation (copula omission) correct. Infinitive-as-attribute analysis in «Бажання вчитися» is standard school grammar. |

**Weighted Overall:** (8×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 8×1.0 + 7×1.3 + 8×0.9 + 9×1.3 + 7×1.0 + 9×1.5) / 14.0 = (12 + 9 + 9 + 9.6 + 8.8 + 9.6 + 8 + 9.1 + 7.2 + 11.7 + 7 + 13.5) / 14.0 = 114.5 / 14.0 = **8.2/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no Russian comparisons
- Grammar scope: [CLEAN] — complex sentence subtypes correctly deferred
- Activity errors: [MINOR] — quiz count shortfall (8/10+)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Pedagogical Inconsistency in Dialogue 2 (Conjunction Switch)
- **Location**: Section "Діалог 2: Страх перед комами"
- **Original**: «Точно! Перед «і» треба ставити кому, бо це дві різні думки, дві різні «квартири». Виходить: «Я хочу піти в парк, та я хочу купити морозиво».»
- **Problem**: Іра explains the comma rule for the conjunction «і», then silently switches to «та» in the corrected sentence. The learner expects to see «і» with a comma (the point of the exercise), but gets an unexplained conjunction change. This undercuts the pedagogical clarity of the comma rule demonstration.
- **Fix**: Keep «і» in the corrected sentence: «Я хочу піти в парк, і я хочу купити морозиво».

### Issue 2: Plan Content Gap — Missing §4.4.2 Material
- **Location**: Entire module (absence)
- **Problem**: The plan explicitly requires coverage of «ускладнене речення» (complicated simple sentences) and «вставні слова» (parenthetical words) under State Standard §4.4.2. The content mentions «однорідні члени» in passing within the simple sentence section but never introduces the formal concept of «ускладнене речення» as a category between simple and complex. «Вставні слова» are entirely absent.
- **Fix**: Cannot add new sections per fix rules. Flag for Phase F or next rebuild cycle.

### Issue 3: Quiz Activity Count Shortfall
- **Location**: Activities YAML, quiz type
- **Problem**: Plan requires 10+ quiz items; only 8 provided. Missing items should cover sentence type identification edge cases (e.g., long simple sentences that look complex, sentences with homogeneous predicates).
- **Fix**: Cannot add items per fix rules. Flag for Phase F.

### Issue 4: Flagged LLM Cliché Metaphor
- **Location**: Section "Присудок"
- **Original**: «Присудок — це двигун речення, який запускає події.»
- **Problem**: «двигун» is explicitly listed as a flagged cliché metaphor in the review rubric. Combined with >4 distinct metaphor families throughout the module, this contributes to the LLM Fingerprint score of 7.
- **Fix**: Replace with a less clichéd formulation that maintains the teaching point.

### Issue 5: Missing Vocabulary YAML File
- **Location**: `curriculum/l2-uk-en/b1/vocabulary/sentence-structure.yaml`
- **Problem**: File reported as "not found". The plan specifies 9 required and 6 recommended vocabulary items. Without the vocabulary file, the module is incomplete for the build pipeline.
- **Fix**: Infrastructure issue — requires file creation in a separate phase.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Dialogue 2 | «Виходить: «Я хочу піти в парк, **та** я хочу купити морозиво»» | «Виходить: «Я хочу піти в парк, **і** я хочу купити морозиво»» | Pedagogical inconsistency |
| Пунктуація section | «**В** українській мові пунктуація» | «**У** українській мові пунктуація» | Euphony (minor — «у» preferred before vowel at sentence start) |
| Присудок section | «Присудок — це **двигун** речення» | «Присудок надає руху реченню» | LLM cliché |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — Progressive build-up, clear headings, visual system introduced step by step
- Instructions clear? **Pass** — Each concept has definition, question test, and examples
- Quick wins? **Pass** — The "граматична основа" stripping exercise gives immediate satisfaction
- Ukrainian scary? **Pass** — English bridge paragraphs ease the transition; parenthetical translations throughout
- Come back tomorrow? **Pass** — Dialogues at the end feel real and motivating; self-check questions provide closure

## Strengths

- **Cultural embedding**: The «Шкільний ритуал підкреслення» box is a standout — it connects abstract grammar to a physical, memorable school ritual that every Ukrainian knows. This is the kind of cultural insight that textbooks rarely provide.
- **Error anticipation**: The [!warning] box distinguishing «іменник» (part of speech) from «підмет» (sentence part) addresses the #1 confusion for grammar learners at this level. Well-placed and well-explained.
- **Граматична основа stripping exercise**: The "ruthless editor" metaphor for extracting «Дівчина співала» from a long sentence is pedagogically excellent — it gives learners a concrete, repeatable technique.
- **Dialogue authenticity**: Dialogue 1 (Editor and Writer) and Dialogue 3 (School nostalgia) feel natural. The characters have distinct voices and the grammar discussion emerges organically.
- **The [!context] box on «А» vs «Але»**: This is a perennial confusion for learners and the explanation is clear, concise, and correctly nuanced.

## Fix Plan to Reach 9.0/10

### Activities: 7/10 → 8/10
**What to fix:**
1. Add 2+ quiz items to meet the 10+ minimum (cannot be done in Phase D fixes — flag for Phase F)

**Expected score after fix:** 8/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Replace «двигун речення» with a less clichéd formulation
2. Consider pruning 1-2 of the weaker metaphors (e.g., «цемент» in the conjunctions section could simply be «засіб зв'язку»)

**Expected score after fix:** 8/10

### Educational: 8/10 → 9/10
**What to fix:**
1. Add brief mention of «ускладнене речення» concept in the "Типи речень" section (cannot be done in Phase D — flag for Phase F)
2. Add brief mention of «вставні слова» (parenthetical words) with 1-2 examples

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Fix the «та» → «і» inconsistency in Dialogue 2
2. Fix euphony: «В українській» → «У українській» at section start

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(8×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 8×1.2 + 8×1.0 + 8×1.3 + 8×0.9 + 9×1.3 + 8×1.0 + 9×1.5) / 14.0
= (12 + 9 + 9 + 10.8 + 9.9 + 9.6 + 8 + 10.4 + 7.2 + 11.7 + 8 + 13.5) / 14.0
= 119.1 / 14.0
= 8.5/10
```

Note: Full 9.0 requires Phase F fixes (quiz items, ускладнене речення content, vocabulary YAML creation) that cannot be addressed via inline FIND/REPLACE.

## Verification Summary

- Content lines read: ~430 (full module prose)
- Activity items checked: 56 (12 match-up pairs + 10 mark-the-words answers + 8 quiz items + 6 unjumble items + 6 error-correction items + 8 fill-in items + 8 true-false items)
- Ukrainian sentences verified: ~55 (all examples, dialogue lines, activity sentences)
- IPA transcriptions checked: 0 (not applicable — metalinguistic module)
- Issues found: 5

## Verdict

**PASS**

The module delivers solid B1 metalinguistic teaching with strong cultural embedding, clear explanations, and authentic dialogues. The persona-aligned construction metaphor works well pedagogically despite high density. Three gaps prevent a higher score: (1) missing «ускладнене речення» / «вставні слова» plan content, (2) quiz shortfall at 8/10+ items, (3) missing vocabulary YAML file. The Dialogue 2 conjunction switch is the only inline-fixable error. Remaining gaps require Phase F attention.