# Plan Review: my-family

**Track:** a1 | **Sequence:** 6 | **Version:** 1.4.0 | **Lifecycle:** locked
**Verdict:** PASS (one borderline MEDIUM around `муж` framing)
**Authority:** `docs/l2-uk-en/state-standard-2024-mapping.yaml` — A1 §4.2.1.4 (pronouns, light), §4.2.3.1 (nominative); §4.2.2.2 Genitive — A2 (used here only as frozen `у мене/тебе/вас` chunks).

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 1200 = Config A1: 1200 |
| section_budgets | PASS | Sum = 400+200+250+200+150 = 1200 (exact match) |
| required_fields | PASS | All present |
| version_string | PASS | `version: '1.4.0'` (explicit string) |
| no Latin in Cyrillic | PASS | Scan clean per locked review_notes |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Possessive pronouns: мій/моя/моє/мої, твій/-я/-є | YES (§4.2.1.4) | A1 | A1 | PASS — nominative only, full paradigm deferred to A2 |
| Gender agreement (мій брат vs моя сестра) | YES (§4.2.1.2) | A1 | A1 | PASS |
| Cardinals one/two with gender (один брат, одна сестра) | YES (§4.2.1.3 — basic forms) | A1 | A1 | PASS |
| `У мене/тебе/вас є` (frozen genitive expression) | Genitive A2 nominally | A2 | A1 (frozen chunk) | MEDIUM — documented pedagogical exception |
| Negative `у мене немає` deferred to A2 | Correct scope discipline | A2 | A2 (deferred) | PASS — plan explicitly defers |
| Patronymic recognition (`-івна / -ївна`) | YES — vocative §4.2.3.4 at A1 (recognition framing) | A1 | A1 (recognition only) | PASS — properly fenced as recognition-only |

## Grammar Verification (Textbook RAG)
| Concept | Source | Correct? | Notes |
|---------|--------|----------|-------|
| Ukrainian has no single «grandparents» word — must say «бабуся і дідусь» | Standard / ULP Ep.6 | YES | Correct cultural-linguistic note |
| Two synonyms for «family»: сім'я / родина | Standard | YES | Both VESUM-confirmed; both used naturally |
| `у мене є` not `я маю X` for possession | ULP Ep.6 (cited) | YES | Correct — `мати` for possession is calque/awkward in colloquial register |
| Patronymic suffixes: -ович/-йович (m), -івна/-ївна (f) | NUS standard + wiki Крок 6 | YES | Plan correctly distinguishes Ukrainian -івна from Russian -овна — strong decolonization note |
| Gender of cardinal один: один брат vs одна сестра vs два брати vs дві сестри | Standard | YES | Correctly stated |

## Vocabulary Verification (VESUM)
| Word | VESUM | Notes |
|------|-------|-------|
| Required: сім'я, мама, тато, брат, сестра, бабуся, дідусь, мій/моя/моє/мої, твій/-я/-є, у мене є, у тебе є | All FOUND | OK |
| Recommended: батьки, дядько, тітка, дочка, син, дружина, чоловік, родичі, його, її, один/одна, два/дві, чи, тільки, ім'я, прізвище, по батькові | All FOUND (note: `по батькові` is a phrase, not a single VESUM headword — component words верифіковано) | OK |
| Russianism counter-pairs in fill-in activity: жена, муж, бабушка, родственники, ребьонок, младший, женатий | **жена / бабушка / родственники / ребьонок / младший / женатий = NOT FOUND in VESUM** | Plan correctly flags these as Surzhyk |
| `муж` | **FOUND in VESUM** (noun) | See MEDIUM below — `муж` is a legitimate Ukrainian word (archaic/elevated register meaning "man, husband"; cf. Грінченко, Біблійні переклади). It is NOT a Russianism in the strict sense — but in modern colloquial register, native speakers default to `чоловік`. |
| `папа` | **FOUND in VESUM** (noun, 2 matches) | Plan deliberately avoids flagging `папа` per the locked-review note ("VESUM lists `папа` without restrictive tags") — correctly handled |

## Issues Found

### CRITICAL (must fix before build)
None.

### HIGH (should fix before build)
None.

### MEDIUM (fix if possible)
1. **`муж/чоловік` framing in fill-in activity** (activity_hints[4].items[1]). `муж` IS in VESUM as a Ukrainian noun (archaic/elevated: «муж — чоловік, особа чоловічої статі», cf. «державні мужі»). Framing it as a Surzhyk pair against `чоловік` could be misleading — the contrast is **register**, not Russianism status. The locked-review explicitly dropped `папа/тато` from the drill for exactly this reason; the same logic should apply to `муж`. Suggested fix: either (a) remove the `муж/чоловік` pair from the activity (down to 6 items), OR (b) reframe the item explicitly as "У розмовному регістрі модерної української основна форма — `чоловік`. `Муж` — піднесений / архаїчний регістр (державні мужі)." Without this nuance, the writer may build the activity as a black-and-white "wrong/right" item, contradicting the plan's own author-discipline (cf. the careful `папа` handling).
2. **Genitive in frozen `у мене/тебе/вас є`** — same documented pedagogical compromise as in M5 (who-am-i). Plan explicitly defers full paradigm to A2 and uses only the chunk. Acceptable; cross-cutting concern, see summary.

### LOW (informational)
1. The plan's family-Surzhyk drill (7 pairs) is well-curated. The dropped `папа/тато` pair (after Codex AC-3 adversarial review) shows excellent dictionary discipline.
2. Dialogue 3 connects to A1.1 capstone (`Привіт! Мене звати... Моя мама — вчителька...`) — strong end-of-phase synthesis preview before M7 checkpoint.
3. Plan correctly avoids teaching `у нього/неї/нас/них` paradigm — these involve case forms of personal pronouns (А2). Defers via "введемо поступово через діалоги як сталі фрази".

## Suggested Fixes
```yaml
# activity_hints[4].items — adjust муж/чоловік framing or remove
# Option A (recommended): remove the муж/чоловік row, keep 6 items
items:
  - Моя {дружина|жена} — вчителька.
  - Це моя {бабуся|бабушка}. Їй сімдесят років.
  - У нас велика родина — близько десяти {родичів|родственників}.
  - Моя племінниця ще маленька {дитина|ребьонок}.
  - Мій {молодший|младший} брат навчається в школі.
  - Мій старший брат уже {одружений|женатий}. У нього двоє дітей.

# Option B: reframe with a register-note in author_note
```

## Verdict
PASS with one MEDIUM fix recommended. The plan is exemplary in scope management (defers full paradigm of `у мене`/possessive pronouns to A2, fences patronymics as recognition-only) and decolonization discipline (feminitive default, native-form vocab priority). The `муж/чоловік` adjustment is a 1-line edit. Recommend **NEEDS_FIX** for the muz reframing — or accept current state as LOCK_NOW if the team confirms the register-Surzhyk framing is intentional.
