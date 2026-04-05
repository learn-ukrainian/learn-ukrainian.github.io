# Plan Review: genitive-dates-numbers

**Track:** a2 | **Sequence:** 5 | **Version:** 1.0
**Verdict:** NEEDS FIXES

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 2000, Config: 2000 |
| section_budgets | PASS | Sum = 2000 (500+800+700) vs target 2000 (0%) |
| required_fields | FAIL | Missing: `persona`, `grammar`, `register` |
| version_string | PASS | version: '1.0' |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Genitive with dates/months | YES | A2 cases (lines 1265-1285) | A2 | PASS |
| Numeral-noun agreement (1, 2-4, 5+) | YES | A2 numerals (lines 1235-1242) | A2 | PASS |
| Genitive of negation (direct object) | YES | A2 genitive (lines 1265-1285) | A2 | PASS |

All grammar topics are within A2 scope per the State Standard.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Dates: ordinal + month in genitive | Textbook corpus | YES | Standard pattern: перше січня, друге лютого |
| 1, 2-4, 5+ rule | Заболотний Gr6 p184, Авраменко Gr11 p34, Litvinova Gr6 p241 | PARTIALLY | **Critical error in plan** — see below |
| Genitive of negation with direct object | Авраменко Gr8 p77 | YES | Confirmed: прямий додаток in родовому відмінку при запереченні |

## Vocabulary Verification
| Word | VESUM | Issues |
|------|-------|--------|
| число (дата) | OK | |
| місяць | OK | |
| січень (січня) | OK | Both forms verified |
| лютий (лютого) | OK | |
| березень (березня) | OK | |
| квітень (квітня) | OK | |
| травень (травня) | OK | |
| червень (червня) | OK | |
| липень (липня) | OK | |
| серпень (серпня) | OK | |
| вересень (вересня) | OK | |
| жовтень (жовтня) | OK | |
| листопад (листопада) | OK | |
| грудень (грудня) | OK | |
| заперечення | OK | |
| числівник | OK | |
| додаток | OK | |
| правило | OK | |

All vocabulary verified. No ghost words.

## Issues Found

### CRITICAL (must fix before build)

1. **WRONG GRAMMAR RULE: "2, 3, 4 → Genitive Singular"**: Section 2 states: "2, 3, 4 (+22-24..): Genitive Singular (два столи, три столи, чотири столи)." This is **factually incorrect**. The examples "два столи, три столи" are Nominative PLURAL, not Genitive Singular. The textbook (Заболотний Gr6 p184) explicitly states: "Із числівниками два, три, чотири, обидва в називному відмінку іменники вживаємо **в називному відмінку множини**." The correct rule is:
   - 1: Nominative Singular (один стіл)
   - 2, 3, 4: **Nominative Plural** (два столи) — NOT Genitive Singular
   - 5+: Genitive Plural (п'ять столів)

   The plan's label is wrong even though its examples happen to be correct. This must be fixed before build or it will teach a fundamentally incorrect grammar rule.

2. **Missing required fields**: Plan lacks `persona`, `grammar`, and `register` fields.

### HIGH (should fix before build)

1. **Section 3 (Negation with direct object) is B1-level nuance**: The genitive of negation (Acc → Gen under negation) is an advanced topic. The State Standard puts basic genitive at A2, but the subtle semantic distinction between "Я не читаю книгу" vs "Я не читаю книги" (the "any book" distinction) is difficult for A2 learners. The textbooks treat this in Grade 8 (Авраменко Gr8), not Grade 5-6. Consider simplifying to "recognition only" or moving to a later module.

2. **Scope overload**: Three substantial grammar topics (dates, number agreement, genitive of negation) in 2000 words is very dense. Each of these is a lesson unto itself in Ukrainian textbooks. Consider dropping the negation section and dedicating more space to dates and number agreement with richer practice.

### MEDIUM (fix if possible)

1. **Dialogue situation is good**: Hotel booking scenario naturally motivates dates and counting. Well chosen.
2. **Month vocabulary dominates required list**: 14 of 18 required words are month names. While necessary, this leaves little room for other high-frequency genitive vocabulary. Consider moving some months to "recommended" and adding more genitive-triggering words (без, від, для, до) to "required."

### LOW (informational)

1. **"вересня" note**: Plan says "Note that 'вересня' and 'листопада' have the -а ending." This is odd as a special note — all masculine month names end in -а/-я in genitive. The note seems to highlight something that isn't actually exceptional.

## Suggested Fixes

**Fix 1 — Correct the 2-4 rule (CRITICAL):**
```yaml
# OLD (section 2, point 3)
'2, 3, 4 (+22-24..): Genitive Singular (два столи, три столи, чотири столи).'
# NEW
'2, 3, 4 (+22-24..): Nominative Plural (два столи, три столи, чотири столи).'
```

**Fix 2 — Add missing fields:**
```yaml
persona: friendly-tutor
grammar:
  - genitive_with_dates
  - numeral_noun_agreement
  - genitive_of_negation
register: informal-educational
```

**Fix 3 — Fix the misleading "вересня" note:**
```yaml
# OLD
'Examples: перше січня, друге лютого, двадцять п''яте грудня. Note that ''вересня''
  and ''листопада'' have the -а ending.'
# NEW
'Examples: перше січня, друге лютого, двадцять п''яте грудня. All month names
  are masculine and take the standard genitive endings: -я (січня, лютого, березня...)
  or -а (листопада).'
```
