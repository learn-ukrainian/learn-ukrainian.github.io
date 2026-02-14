# Phase 6b Fixes: language-about-verbs (B1 M02)

## Review Score: 6.9/10 (FAIL)

## Issues from Green Team Review

### Fixed (6/7)

| # | Category | Location | Action | Status |
|---|----------|----------|--------|--------|
| 1 | Hybrid language | Line 36 | "we переходимо" → "ми переходимо" | Fixed (Claude) |
| 2 | Hybrid language | Line 64 | "we analyze" → "ми аналізуємо" | Fixed (Claude) |
| 3 | Hybrid language | Line 150 | "we talk" → "ми говоримо" | Fixed (Claude) |
| 4 | Terminology | vocabulary.yaml | `складна форма` → `складена форма` + IPA update | Fixed (Claude) |
| 5 | LLM Fingerprint | Line 23 | Rewrote "не просто X, а Y" pattern | Fixed (Claude) |
| 6 | LLM Fingerprint | Line 134 | Rewrote "Ми не просто кажемо" pattern | Fixed (Claude) |
| 7 | LLM Fingerprint | Line 147 | Rewrote "це не просто додавання" pattern | Fixed (Claude) |

### Skipped (0)

None — all actionable issues were addressed.

## Post-Fix Audit

- Words: 4015/4000 (raw: 4691)
- All strict gates: PASS
- Immersion: 94.2%
- Review validation: 1 warning (expected — fixed citations no longer match old review quotes)

## Pipeline Friction Noted

**New friction type: Hybrid language leakage.** Gemini's `gemini-3-flash-preview` occasionally inserts English words ("we", "analyze", "talk") into Ukrainian sentences. This was NOT seen in B1 M01. Recommend adding explicit instruction to Phase 2 template: "ABSOLUTELY NO English words inside Ukrainian sentences. English may ONLY appear in parenthetical equivalents (like this) after Ukrainian terms."
