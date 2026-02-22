<!-- content-hash: 601e712f1729 -->
# Рецензія: Combined Practice

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 43
**Overall Score:** 7.0/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS (with caveats)
- Sections: 4/4 H2 sections present (Вступ, Презентація, Практика, Висновок) — PASS
- Vocabulary: 9/9 required present, 4/4 recommended present, 7 extra context words — PASS
- Grammar scope: PASS — focuses on conjunctions і/але, sequence markers, тому що/бо, якщо, також
- Objectives: PARTIAL — "handle multi-step scenarios" and "solve unexpected problems" 
  covered; "switch between different situations" weakly covered
```

Note: The plan calls for 500 words in section «Практика: Сценарії реального життя» but the actual section contains ~700+ words including a massive reading passage (lines 265-278) that does NOT demonstrate the taught structures. The plan's intent for "Bazar Hub" and "Problem-Solving with Якщо" is met, but the padding reading passage isn't aligned with plan objectives.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Warm opening, good cultural hook, but 9× "How it works:" / "Usage note:" monotony drags the experience into a formulaic grind |
| 2 | Coherence | 7/10 | <7 | Sections follow logically, but reading passage in section «Практика: Сценарії реального життя» (lines 265-278) uses zero taught conjunctions/markers — contradicts lesson goals |
| 3 | Relevance | 8/10 | <7 | Practical scenarios (café, market, daily planning) match A1 learner needs; cultural hooks (coffee ritual, bazaar) well-chosen |
| 4 | Educational | 7/10 | <7 | Grammar teaching is clear, but model text at line 288 in section «Висновок: Мій наратив» contains punctuation errors that teach wrong patterns; analysis at lines 294-298 misquotes its own model text |
| 5 | Language | 7/10 | <8 | **AUTO-FAIL**: Model text uses «Бо» and «Тому що» as sentence-initial (after periods) — contradicts lesson's own comma rules; analysis section misquotes model text 3 times |
| 6 | Pedagogy | 7/10 | <7 | PPP structure present but reading passages (~400 words in «Практика: Сценарії реального життя» and «Висновок: Мій наратив») model the exact "robotic sentences" pattern the lesson warns against |
| 7 | Immersion | 8/10 | <6 | 37.0% vs target 35-55% — within range but at the low end for module 43/44; heavily bimodal (English-only explanations + Ukrainian-only reading blocks) |
| 8 | Activities | 6/10 | <7 | **AUTO-FAIL**: 5 unjumble answers systematically missing required commas before conjunctions; quiz at line 234 marks grammatically acceptable sentence-initial "також" as wrong |
| 9 | Richness | 7/10 | <6 | Cultural hooks (coffee ritual, bazaar) and named characters (Олена, Віктор) add texture; reading passages generic/bland |
| 10 | Beginner Safety | 7/10 | <7 | Warm opening, encouragement, clear English scaffolding — but model text with grammar errors risks teaching wrong patterns to fragile beginners |
| 11 | LLM Fingerprint | 5/10 | <7 | **AUTO-FAIL**: 9× identical "How it works:" + 9× "Usage note:" structural pattern across ALL grammar subsections — extreme template monotony |
| 12 | Linguistic Accuracy | 7/10 | <9 | **AUTO-FAIL**: Model text at line 288 has «Бо» and «Тому що» starting new sentences (after periods); 5 unjumble answers missing commas; line 30 translates "складне речення" as "complex sentence" (should be "compound sentence" for coordinating conjunctions) |
| 13 | Factual Accuracy | 8/10 | <8 | Cultural claims about coffee culture and bazaar are reasonable; self-analysis at lines 294-298 inaccurately describes its own model text in 3 places |

**Weighted Overall:** (7×1.5 + 7×1.0 + 8×1.0 + 7×1.2 + 7×1.1 + 7×1.2 + 8×1.0 + 6×1.3 + 7×0.9 + 7×1.3 + 5×1.0 + 7×1.5 + 8×1.5) / 15.5 = (10.5 + 7.0 + 8.0 + 8.4 + 7.7 + 8.4 + 8.0 + 7.8 + 6.3 + 9.1 + 5.0 + 10.5 + 12.0) / 15.5 = 108.7 / 15.5 = **7.0/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN
- Colonial framing: CLEAN
- Grammar scope: CLEAN — stays within A1 conjunctions/sequence markers
- Activity errors: **FAIL** — 5 unjumble answers missing required commas; quiz marks valid також position as wrong
- Beginner safety: 4/5 (see below)
- Factual accuracy: MINOR — self-analysis misquotes own model text; cultural claims OK

## Critical Issues Found

### Issue 1: Grammar Errors in Model Text (CRITICAL — teaches wrong patterns)
- **Location**: Line 288 / Section «Висновок: Мій наратив»
- **Original**: «Ми йдемо на каву. **Бо** ранок теплий.» and «Ми готуємо вечерю разом. **Тому що** ми любимо смачну українську їжу.»
- **Problem**: «Бо» and «тому що» are subordinating conjunctions that cannot start independent sentences after a period. The lesson itself teaches (line 62): "we always place a comma (кома) before **але**" and similar rules apply to «бо»/«тому що». The model text directly contradicts its own teaching.
- **Fix**: Change to «Ми йдемо на каву, бо ранок теплий.» and «Ми готуємо вечерю разом, тому що ми любимо смачну українську їжу.»

### Issue 2: Systematic Missing Commas in Unjumble Answers (CRITICAL)
- **Location**: Activities file, lines 365, 367, 418, 420, 424
- **Original**: 
  - «Ми не гуляємо бо холодно» (line 365)
  - «Якщо хочеш ми готуємо разом» (line 367)
  - «Вона читає але він працює» (line 418)
  - «Якщо є проблема кажи мені» (line 420)
  - «Ми купуємо це тому що треба» (line 424)
- **Problem**: All 5 answers are missing mandatory commas before/after conjunctions. The lesson explicitly teaches comma placement before «але», «бо», «тому що», and after the condition clause with «якщо».
- **Fix**: «Ми не гуляємо, бо холодно», «Якщо хочеш, ми готуємо разом», «Вона читає, але він працює», «Якщо є проблема, кажи мені», «Ми купуємо це, тому що треба»

### Issue 3: Extreme Structural Monotony — LLM Fingerprint (MAJOR)
- **Location**: Lines 36, 61, 88, 105, 122, 147, 164, 191, 242 / Sections «Вступ: Культура планування» and «Презентація: Структура та Причини»
- **Original**: Every single grammar subsection follows identical pattern: **"How it works:"** → examples → **"Usage note:"** — 9 times each
- **Problem**: This is severe LLM template-generated monotony. No human educator would structure 9 consecutive grammar points with the identical subheading pattern. It makes the lesson feel robotic — ironic for a lesson about avoiding robotic sentences.
- **Fix**: Vary the subsection structure — use "Quick rule:", "Remember:", "Pro tip:", "Pattern:", etc. Merge some shorter subsections. Remove redundant structural headers.

### Issue 4: Self-Analysis Misquotes Own Model Text (MODERATE)
- **Location**: Lines 294-297 / Section «Висновок: Мій наратив»
- **Original**: 
  - Line 294: «зустрічаю друга, і ми йдемо» — but model text at line 288 says «Спочатку я зустрічаю друга. Ми йдемо на каву.» (two separate sentences, no «і»)
  - Line 297: «але сьогодні там багато людей» — but model text says «Але там дуже багато людей» (has «дуже» not «сьогодні»)
  - Line 295: claims «тому що ми дуже любимо» — but model text says «Тому що ми любимо смачну українську їжу» (no «дуже»)
- **Problem**: The analysis section fabricates quotes from a model text that's on the same page. This erodes learner trust and teaches inaccurate reading skills.
- **Fix**: Either fix the model text to match the analysis, or rewrite the analysis to accurately describe the actual model text.

### Issue 5: Reading Passages Contradict Lesson Objectives (MODERATE)
- **Location**: Lines 265-278 / Section «Практика: Сценарії реального життя», subsection «Додаткова практика читання»
- **Original**: ~400 words of simple, disconnected sentences like «Це місто Київ. Київ дуже великий. Це столиця України. Там є багато парків.»
- **Problem**: These reading passages contain virtually ZERO instances of the taught conjunctions/sequence markers (спочатку, потім, нарешті, тому що, бо, якщо). The lesson warns against the "робот" pattern of disconnected sentences, yet the reading practice models exactly that pattern. The contrast reading at line 304 demonstrates proper usage, but the bulk text at 265-278 does not.
- **Fix**: Rewrite reading passages to incorporate taught structures, or reduce their word count and add a second passage like the good one at line 304.

### Issue 6: Match-up Pair Contradicts Three-Step Teaching (MINOR)
- **Location**: Activities file, lines 347-348
- **Original**: Left: «Спочатку робота,» → Right: «і нарешті відпочинок.»
- **Problem**: The lesson teaches the three-step sequence спочатку → потім → нарешті. Pairing «спочатку» directly with «нарешті» (skipping «потім») contradicts this teaching.
- **Fix**: Change right side to «а потім відпочинок.» or add a three-part match sequence.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 288 | «Ми йдемо на каву. **Бо** ранок теплий.» | «Ми йдемо на каву, бо ранок теплий.» | Grammar — conjunction cannot start sentence |
| 288 | «Ми готуємо вечерю разом. **Тому що** ми любимо смачну українську їжу.» | «Ми готуємо вечерю разом, тому що ми любимо смачну українську їжу.» | Grammar — conjunction cannot start sentence |
| 30 | "складне речення (complex sentence)" | "складне речення (compound sentence)" | Translation — coordinating conjunctions create compound sentences, not complex sentences |
| Act:365 | «Ми не гуляємо бо холодно» | «Ми не гуляємо, бо холодно» | Punctuation — missing comma before бо |
| Act:367 | «Якщо хочеш ми готуємо разом» | «Якщо хочеш, ми готуємо разом» | Punctuation — missing comma after condition |
| Act:418 | «Вона читає але він працює» | «Вона читає, але він працює» | Punctuation — missing comma before але |
| Act:420 | «Якщо є проблема кажи мені» | «Якщо є проблема, кажи мені» | Punctuation — missing comma after condition |
| Act:424 | «Ми купуємо це тому що треба» | «Ми купуємо це, тому що треба» | Punctuation — missing comma before тому що |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is manageable, though the reading walls (265-278) are long
- Instructions clear? **Pass** — always clear what to do next
- Quick wins? **Pass** — first dialogue and examples are immediate successes
- Ukrainian scary? **Pass** — introduced gently with English translations
- Come back tomorrow? **Fail** — the 9× identical "How it works:" / "Usage note:" structure becomes tedious; the lesson would benefit from structural variety to maintain interest

## Strengths

- **Strong cultural hooks**: The coffee ritual (line 21-22) and bazaar community context (line 215-216) in section «Вступ: Культура планування» and section «Практика: Сценарії реального життя» provide authentic Ukrainian cultural framing
- **Excellent тому що vs. бо comparison**: The comparison table at lines 180-185 in section «Презентація: Структура та Причини» clearly distinguishes register, length, and context
- **Good "Потім loop" warning**: The callout at line 136-138 in section «Презентація: Структура та Причини» addresses a real learner error with a concrete fix pattern
- **Correct також placement teaching**: Lines 194-205 in section «Презентація: Структура та Причини» clearly show correct vs. incorrect placement with visual emphasis
- **Additional reading at line 304**: The narrative in section «Висновок: Мій наратив» correctly demonstrates all taught structures (спочатку, потім, якщо, але, тому що, бо, нарешті) in a cohesive mini-story

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Line 288: Change «Ми йдемо на каву. **Бо** ранок теплий.» → «Ми йдемо на каву, бо ранок теплий.» — conjunction must connect clauses, not start sentences
2. Line 288: Change «Ми готуємо вечерю разом. **Тому що** ми любимо смачну українську їжу.» → «Ми готуємо вечерю разом, тому що ми любимо смачну українську їжу.» — same rule
3. Line 30: Change "complex sentence" → "compound sentence" — correct English grammar terminology for coordinating conjunctions
4. Activities lines 365, 367, 418, 420, 424: Add commas to all 5 unjumble answers

**Expected score after fix:** 9/10

### Language: 7/10 → 9/10
**What to fix:**
1. Lines 294-297: Rewrite analysis to accurately quote the model text — remove fabricated «сьогодні», «дуже», and non-existent «і» connection
2. Fix model text punctuation (same as Linguistic Accuracy fixes above)

**Expected score after fix:** 9/10

### Activities: 6/10 → 8/10
**What to fix:**
1. Add commas to all 5 unjumble answers (lines 365, 367, 418, 420, 424)
2. Lines 347-348: Change match-up pair «Спочатку робота,» → «і нарешті відпочинок.» to «Спочатку робота,» → «а потім відпочинок.» to align with three-step teaching
3. Line 234: Consider rewording quiz question from "правильно стоїть" to "найприродніше стоїть" since sentence-initial також is grammatically acceptable

**Expected score after fix:** 8/10

### LLM Fingerprint: 5/10 → 7/10
**What to fix:**
1. Vary the 9× "How it works:" headers — use "Quick rule:", "Pattern:", "Remember:" alternations
2. Vary the 9× "Usage note:" footers — use "Pro tip:", "When to use it:", "Native speaker insight:" alternations
3. Merge the shorter subsections (спочатку + потім + нарешті could share a structure rather than repeating the full template 3 times)

**Expected score after fix:** 7/10

### Pedagogy: 7/10 → 8/10
**What to fix:**
1. Lines 265-278: Rewrite the reading passage in section «Практика: Сценарії реального життя» to incorporate taught conjunctions/sequence markers — currently models the exact "robotic" pattern the lesson warns against
2. Alternatively, reduce this passage and add a second narrative similar to the good one at line 304

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
Experience: 8 × 1.5 = 12.0
Coherence: 8 × 1.0 = 8.0
Relevance: 8 × 1.0 = 8.0
Educational: 8 × 1.2 = 9.6
Language: 9 × 1.1 = 9.9
Pedagogy: 8 × 1.2 = 9.6
Immersion: 8 × 1.0 = 8.0
Activities: 8 × 1.3 = 10.4
Richness: 7 × 0.9 = 6.3
Beginner Safety: 8 × 1.3 = 10.4
LLM Fingerprint: 7 × 1.0 = 7.0
Linguistic Accuracy: 9 × 1.5 = 13.5
Factual Accuracy: 9 × 1.5 = 13.5

Projected Total: 126.2 / 15.5 = 8.1/10
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (core A1 track, no research file exists)
- Key Facts Ledger present: NO
- Dates checked: 0 (no dates claimed)
- Named figures verified: 0 (fictional characters Олена/Віктор only)
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 0

Callout box review:
- `[!culture]` line 21 — coffee culture in western Ukraine claim: **Plausible** — Lviv is indeed known as the coffee capital of Ukraine
- `[!history-bite]` line 215 — bazaar as community center claim: **Plausible** — traditional markets remain culturally important
- `[!tip]` line 52 — і/й euphony rule: **Accurate** — correctly stated
- `[!warning]` line 136 — потім loop example: **Accurate** — realistic learner error
- `[!observe]` line 258 — якщо as "coding logic": **Acceptable** analogy for beginners

## Verification Summary

- Content lines read: 324
- Activity items checked: 84 across 10 activities
- Ukrainian sentences verified: 35+
- IPA transcriptions checked: 5 (спочатку, потім, нарешті, бо, якщо — all correct)
- Factual claims verified: 5 (callout boxes)
- Issues found: 6 (2 critical, 2 moderate, 2 minor)

## Verdict

**FAIL**

Four auto-fail thresholds breached: Language (7 < 8), Activities (6 < 7), LLM Fingerprint (5 < 7), Linguistic Accuracy (7 < 9). The most damaging issues are: (1) the model text in section «Висновок: Мій наратив» teaches incorrect punctuation by starting sentences with «Бо» and «Тому що» after periods — directly contradicting the lesson's own comma rules; (2) 5 unjumble activity answers systematically missing required commas; (3) extreme structural monotony (9× identical "How it works:" + "Usage note:" pattern). The reading passages in section «Практика: Сценарії реального життя» also undermine pedagogy by modeling the disconnected sentence pattern the lesson warns against. Fixes are well-scoped and achievable without a full rewrite.