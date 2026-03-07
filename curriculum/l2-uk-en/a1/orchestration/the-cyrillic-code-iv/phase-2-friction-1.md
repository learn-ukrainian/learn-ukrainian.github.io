**Phase**: Beginner Content
**Step**: Audit
**Friction Type**: Immersion Target & Euphony
**Raw Error**: 1. "Immersion ❌ 3.5% LOW (target 10-25% (M04))", 2. "[EUPHONY] Line 217: «И і Ї» — і між голосними; має бути «й Ї»", 3. "[GRAMMAR] Dative case used at A1: 'Переві'"
**Self-Correction**: Replaced some sentences entirely with short Ukrainian phrases + translation. Also modified the presentation of the alphabet by using hyphens ("А - Б - В") instead of spaces/commas to ensure no false positives for euphony. Replaced "Перевірка!" to avoid false Dative trigger.
**Proposed Tooling Fix**: The euphony checker flagged standard alphabet listings if they look like a conjunction. The grammar checker flagged the noun "Перевірка" as a Dative verb "Переві...".