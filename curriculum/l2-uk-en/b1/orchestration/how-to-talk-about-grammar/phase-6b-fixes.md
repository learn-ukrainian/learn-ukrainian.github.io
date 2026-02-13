# Phase 6b: Review Fix Report

**Module:** B1 M01 — Як говорити про граматику
**Review Score:** 9.2/10
**Issues Found:** 5
**Issues Fixed:** 3
**Issues Skipped:** 2

## Fixes Applied

### Fix 1: Flawed analogy (відмінок vs відміна)
- **Classification:** Quick fix (Claude)
- **Location:** Line 51 in content
- **Before:** «модель машини» та «станцію технічного обслувування»
- **After:** «тип двигуна» та «маршрут подорожі» — clearer analogy: відміна = internal word structure, відмінок = role in sentence
- **Impact:** Pedagogical accuracy improved

### Fix 2: Equal case coverage (Називний, Місцевий)
- **Classification:** Quick fix (Claude)
- **Location:** Називний відмінок (after examples), Місцевий відмінок (after examples)
- **Action:** Added _Додаткова інформація:_ blocks for both cases to match the pattern used by Родовий, Знахідний, and Орудний
- **Impact:** All 7 cases now have consistent depth (+2 supplementary blocks)

### Fix 3: Quiz activity item count (8 → 10)
- **Classification:** Quick fix (Claude)
- **Location:** Activity 1 in activities YAML
- **Action:** Added 2 new quiz items covering Частка and Вигук (the two POS not covered by original 8 items)
- **Impact:** All 10 POS now have a quiz question; meets plan's 10+ hint
- **Side fix:** Changed single quotes to double quotes on line 92 (`зв'язок` apostrophe broke YAML parsing)

## Skipped Issues

### Skip 1: Missing IPA for aspect terms
- **Reason:** Недоконаний вид / Доконаний вид are M02 scope — briefly mentioned here for preview but not a primary teaching target of this module

### Skip 2: Typography (straight quotes at line 118)
- **Reason:** Cannot reproduce — proper Ukrainian «» guillemets found at the referenced location. Reviewer may have referenced incorrect line numbers.

## Final Audit
- Words: 4917/4000 (raw: 5179)
- Activities: 14/12 (10 quiz items now)
- All gates: PASS
