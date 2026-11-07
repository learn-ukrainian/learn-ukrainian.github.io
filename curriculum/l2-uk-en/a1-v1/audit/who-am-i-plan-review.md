# Plan Review: who-am-i

**Track:** a1 | **Sequence:** 5 | **Version:** 1.2.0 | **Lifecycle:** locked
**Verdict:** NEEDS FIXES (one HIGH; multiple MEDIUM accepted as documented set-phrase exceptions)
**Authority:** `docs/l2-uk-en/state-standard-2024-mapping.yaml` — A1 §4.2.1.4 (pronouns), §4.2.3.1 (nominative), §4.2.3.2 (accusative — `first_module: 11`), §4.3.1 (simple sentences).

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 1200 = Config A1: 1200 |
| section_budgets | **HIGH** | Sum = 350+250+200+100+150+200+0 = **1250** (+4.2%, within ±10% but one section has 0 words) — see Issues |
| required_fields | PASS | All present |
| version_string | PASS | `version: '1.2.0'` (explicit string) |
| no Latin in Cyrillic | PASS | Scan clean |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Personal pronouns (nominative): я, ти, він, вона, ми, ви, вони | YES (§4.2.1.4) | A1 | A1 | PASS |
| Nominative case (Я — студент) | YES (§4.2.3.1) | A1 | A1 | PASS |
| Demonstrative «це» + noun (Це Київ) | YES (simple sentences §4.3.1) | A1 | A1 | PASS |
| `Мене звати` (acc-style frozen phrase) | Accusative §4.2.3.2 first_module=11 | A1 nominally | A1 (frozen chunk before M11) | MEDIUM — documented exception |
| `А тебе?` (acc 2sg pronoun) | Accusative §4.2.3.2 first_module=11 | A1 nominally | A1 (frozen chunk before M11) | MEDIUM — documented exception |
| `Я з України` (gen of country) | Genitive = A2 (§4.2.2.2) | A2 | A1 (frozen chunk) | MEDIUM — documented exception; plan explicitly says "завчені фрази" |
| Feminitives (лікарка, інженерка) | NOT in §4.2 but supported by VESUM | implicit | A1 | PASS — strong decolonization choice |

## Grammar Verification (Textbook RAG)
| Concept | Source | Correct? | Notes |
|---------|--------|----------|-------|
| Nullsubject-copula sentence (Я — студент) | ULP Ep.3 + standard | YES | Correctly explained — no «бути» in present tense |
| `Як тебе/вас звати?` (informal/formal pairing) | ULP Ep.3 (cited) | YES | Canonical introduction pattern |
| Echo pattern `А тебе? / А вас?` | Wiki Крок 1 (cited) | YES | Plan explicitly forbids `А у тебе?` (which would tie to A2 genitive-with-preposition) — excellent scope discipline |
| Feminitives as primary form for women | Wiki Крок 6 + Декол. #5 | YES | Decolonization principle — лікарка, вчителька, інженерка all VESUM-confirmed |
| `Звідки?` + country as set phrase | Plan defers genitive to M16/M29 explicitly | YES | Correct scope management |

## Vocabulary Verification (VESUM)
| Word | VESUM | Notes |
|------|-------|-------|
| All required: я, ти, він, вона, ви, це, студент(ка), вчитель(ка), лікар(ка), українець, українка, Україна | All FOUND | OK |
| Feminitives recommended: програмістка, інженерка, авторка | All FOUND | OK |
| Native-form recommendations: тато, дружина, дякую, спасибі, вибачте, пробачте, теж, також | All FOUND | OK |
| Russianism counter-pairs (correctly identified as NOT Ukrainian): спасібо, ізвиніть, тоже, жена, врач | **All NOT FOUND in VESUM** | Plan correctly flags these as Russianisms |

**Borderline**: `канадка` (canadian woman) — FOUND in VESUM. The alternate `канадійка` ALSO found. Both are valid; modern form is `канадка` (preferred per current VESUM frequency); `канадійка` is more colloquial. Plan uses `канадка` — fine.

## Issues Found

### CRITICAL (must fix before build)
None.

### HIGH (should fix before build)
1. **Section "Підсумок" has `words: 0`** (content_outline[6]). A section with zero word budget is anomalous — the writer may either (a) skip the section entirely, leaving no closing/self-check beat, or (b) overshoot, breaking the total budget. The plan's note says "Самоперевірка включена до практики діалогів, наведеної вище" — this is a structural intent, but a zero-budget section is a code smell. Suggested fix: either remove the section entirely (better — clean structure) OR allocate 50–100 words of explicit recap content and re-balance one of the larger sections (e.g., reduce "Діалоги" from 350 to 300). Current sum 1250 > 1200 nominal but within ±10%, so this is HIGH-priority structural cleanliness rather than a hard violation.

### MEDIUM (fix if possible)
1. **Accusative `Мене звати` + `А тебе?` at sequence 5** (State Standard puts accusative first_module=11). Plan explicitly documents these as frozen chunks, which is a defensible pedagogical compromise — without this set-phrase introduction the A1 learner has no way to say their name at all. The wiki Крок 1 and the explicit `#1392 Defect 2` avoidance both show this was carefully reasoned. Recommend: keep as is, but document the standard-deviation in the plan's review_notes (`pedagogical_deviations_from_standard:` block) so future audits don't re-litigate.
2. **Genitive `Я з України / Канади / Німеччини` at sequence 5** (Standard puts genitive at A2). Same frozen-phrase justification applies. Same recommendation.
3. **Module sequence vs phase plan**: Plan teaches nationality forms (українець/українка/канадець/канадка) but the `канадець` (m) is absent from required/recommended vocab while `канадка` (f) is implicitly used in dialogue 1 (`Я з Канади`). The dialogue uses country names not nationality, so this is fine — flag is informational only.

### LOW (informational)
1. The fill-in Surzhyk drill (activity_hints[4]) is excellent adversarial-learning coverage — 7 pairs hit the most common L2 errors. Items[6] `Це мій {врач|лікар}` is a clean Russianism counter (врач not in VESUM).
2. Dialogue 3 (Представлення когось іншого) explicitly mandates 2 speakers and a feminitive (`лікарка`, not лікар) — strong gendered-language modeling.

## Suggested Fixes

```yaml
# OPTION A — remove the zero-budget section:
# delete content_outline[6] entirely

# OPTION B — allocate real content and re-balance:
# content_outline[0] (Діалоги): words: 350 → 300
# content_outline[6] (Підсумок): words: 0 → 50
#   points:
#   - 'Самоперевірка: Привітайся з новою людиною. Назви своє ім'я, національність, професію. Запитай у відповідь.'
```

## Verdict
NEEDS_FIX (HIGH issue: zero-budget Підсумок section). The MEDIUM scope-stretching items (acc/gen as frozen chunks) are accepted pedagogical compromises but should be recorded as documented deviations. Recommend **NEEDS_FIX** before next build cycle. Once Підсумок is fixed (1-line YAML edit either way), the plan is build-ready.
