# A1 Plan Review — Summary Roll-Up (Sequences 1–7)

**Date:** 2026-05-13
**Reviewer:** claude-opus-4-7-xhigh (plan-review skill)
**Scope:** A1 sequences 1–7 (slugs: `sounds-letters-and-hello`, `reading-ukrainian`, `special-signs`, `stress-and-melody`, `who-am-i`, `my-family`, `checkpoint-first-contact`)
**Mode:** Review-only — no plan YAMLs modified.

## Authority

- **State Standard 2024 mapping**: `docs/l2-uk-en/state-standard-2024-mapping.yaml` (read once before review). Key A1 constraints applied throughout: nominative only as core; accusative `first_module: 11`; locative `first_module: 13`; dative/instrumental/genitive **NOT** at A1; imperative 2nd-person only at A1 (1pl `читаймо` and 3rd-person `хай/нехай` belong to A2).
- **Config**: `scripts/audit/config.py:LEVEL_CONFIG` — A1: 1200 words; A1-checkpoint: 1000 words.
- **RAG**: VESUM `mcp__sources__verify_words` (53-word batch verification), Антоненко-Давидович `mcp__sources__search_style_guide` (limited coverage 46%), NUS textbook citations cross-referenced inline.

## PASS / FAIL / NEEDS-FIX Table

| seq | slug | verdict | severity-summary | LOCK_NOW | NEEDS_FIX | NEEDS_REVISION |
|-----|------|---------|------------------|----------|-----------|----------------|
| 1 | sounds-letters-and-hello | NEEDS_FIX | 2 MEDIUM (1pl imperative `Прочитаймо` out-of-scope; `ирій` too rare for И) | | ✅ | |
| 2 | reading-ukrainian | PASS | 0 issues (1 LOW info) | ✅ | | |
| 3 | special-signs | PASS | 0 issues (2 LOW info — exemplary author-note) | ✅ | | |
| 4 | stress-and-melody | PASS | 1 MEDIUM (forward-looking TTS note re: `Як справи?` contour exception) | ✅ | | |
| 5 | who-am-i | NEEDS_FIX | 1 HIGH (Підсумок section `words: 0`); 3 MEDIUM (acc/gen as frozen chunks — accepted) | | ✅ | |
| 6 | my-family | PASS (borderline) | 1 MEDIUM (`муж/чоловік` Surzhyk-framing inconsistent with `папа/тато` discipline) | ✅ | (✅ if strict) | |
| 7 | checkpoint-first-contact | NEEDS_FIX | 1 HIGH (`тато/папа` pair contradicts M6's documented discipline); 1 MEDIUM (curriculum-wide checkpoint word_target inconsistency) | | ✅ | |

**Tally:** PASS = 3 (or 4 with M6 lenient); NEEDS_FIX = 3 (or 4 with M6 strict); NEEDS_REVISION = 0.

## CRITICAL Issues
**None.** All seven plans meet all CRITICAL gates (word_target, section_budgets within ±10%, required_fields complete, version-string, no-Latin-in-Cyrillic).

## HIGH Issues (Grouped by Pattern)

### H-1 — `тато/папа` Surzhyk-framing contradicts dictionary evidence (1 plan)
- **M7 (checkpoint-first-contact)** activity_hints[3].items[1]: `Мій {тато|папа} — інженер.` frames `папа` as a wrong form.
- `папа` IS in VESUM (2 matches, no restrictive tags). **M6 (my-family) v1.4.0 explicitly dropped this exact pair** after Codex AC-3 adversarial review with the reasoning: "VESUM lists `папа` without restrictive tags, so framing it as a dictionary-backed error would be overreach."
- M7 was reviewed in the same scale batch as M6 (2026-04-23) but contains a contradiction with its own batch's discipline.
- **Fix:** remove the тато/папа row from M7's drill, OR reframe as register preference (mirror M6's `тато is preferred colloquial register; папа is also Ukrainian but more child-register`).

### H-2 — Zero-budget section structurally anomalous (1 plan)
- **M5 (who-am-i)** content_outline[6] (`Підсумок`) has `words: 0` with note "Самоперевірка включена до практики діалогів". Sum = 1250 (+4.2%, within ±10% but unusual).
- **Fix options:** (a) delete the section entirely; (b) allocate 50–100 words and rebalance `Діалоги` from 350 → 300.

## MEDIUM Issues (Grouped by Pattern)

### M-1 — Frozen-chunk scope-stretching (cross-cutting, 2 plans: M5, M6)
Both `who-am-i` and `my-family` use case forms (accusative `Мене звати`, `А тебе?`; genitive `у мене є`, `з України`) before State Standard 2024 introduces them (accusative `first_module: 11`, genitive at A2). Plans explicitly fence these as frozen multi-word chunks with author-notes deferring the productive paradigms to M11/M16/M29/A2. This is a **defensible pedagogical compromise** — without these chunks, learners cannot perform basic self-introduction at A1 — but is currently undocumented as a standard-deviation. **Recommended action:** add a `pedagogical_deviations_from_standard:` block to both plans listing the frozen-chunk exceptions, so future audits don't re-litigate them. Not a build-blocker.

### M-2 — Out-of-scope 1pl imperative `Прочитаймо` (1 plan: M1)
State Standard §4.2.4.2 limits A1 imperative to 2nd-person only; 1pl `читаймо/прочитаймо` belongs to A2. M1 has `Прочитаймо «Привіт» по літерах` in content_outline[3].points[3]. Used as teacher meta-language ("let's read"), but the writer may render it in module prose. **Fix:** swap to 2sg `Прочитай`. 1-line edit.

### M-3 — Rare key-word `ирій` for И (1 plan: M1)
`ирій` is in VESUM but extremely low-frequency (poetic/mythological). Most NUS A1 bukvars pair И with `іній`, `Україна`, or `лина`. **Fix:** swap to `іній` (frost — high-frequency, concrete). 1-line edit.

### M-4 — `муж/чоловік` Surzhyk-framing oversimplified (1 plan: M6)
`муж` IS in VESUM as a Ukrainian noun (archaic/elevated: "державні мужі"). M6's family-Surzhyk drill frames `муж` as wrong vs `чоловік` — but it's a **register** distinction, not a Russianism. This contradicts M6's own documented `папа/тато` discipline. **Fix:** either drop the `муж/чоловік` row OR add a register-note explaining that `муж` is elevated register, not error. Borderline.

### M-5 — Curriculum-wide A1-checkpoint word_target inconsistency (cross-cutting, ≥3 plans)
| slug | focus | word_target | skill-prompt expectation | actual config target |
|------|-------|-------------|--------------------------|----------------------|
| checkpoint-first-contact | review | 1200 | 1000 (A1-checkpoint) | 1200 (falls back to A1 because focus=review) |
| checkpoint-actions | review | 1200 | 1000 | 1200 |
| checkpoint-communication | review | 1000 | 1000 | 1000 (under-target by current routing) |
| checkpoint-food-shopping | review | 1000 | 1000 | 1000 |
| checkpoint-my-world | review | 1200 | 1000 | 1200 |
| checkpoint-places | review | 1200 | 1000 | 1200 |
| checkpoint-time-nature | review | 1200 | 1000 | 1200 |

5 of 7 A1 checkpoints sit at 1200; 2 sit at 1000. The config branch only fires `A1-checkpoint=1000` if focus=`checkpoint`, but all use focus=`review`. **Not a per-plan defect** — a curriculum-wide policy decision. Orchestrator needs to decide: (a) standardize all A1 checkpoints to 1200 and update skill prompt + config doc; (b) standardize to 1000 and update plans; (c) introduce focus=`checkpoint` and rewrite all checkpoint plans.

## Cross-Cutting Patterns (≥3 plans)

### CC-1 — Frozen-chunk usage of out-of-scope cases (2 plans, but pattern-relevant to all A1.1)
Both M5 and M6 use accusative/genitive frozen chunks before the State Standard introduction module. Plans are disciplined about fencing these explicitly with author-notes. **Recommendation:** add a standard plan field `pedagogical_deviations_from_standard:` and propagate to all A1 plans that use this technique. Issue tracker: file as a curriculum-wide enhancement.

### CC-2 — Surzhyk-drill calibration discipline (3 plans: M5, M6, M7)
All three vocabulary plans contain a "Типові помилки L2" / Surzhyk-pair fill-in activity. Quality varies:
- M5 (who-am-i): clean — все відсутнє в VESUM (`спасібо`, `ізвиніть`, `тоже`, `жена`, `врач`), pairs valid.
- M6 (my-family): mostly clean — 6 of 7 pairs verified Russianism (NOT FOUND in VESUM); `муж/чоловік` is the one register-not-Russianism outlier.
- M7 (checkpoint): contains the `папа` pair that M6 explicitly dropped. Editorial-line inconsistency.

**Recommendation:** before any future Surzhyk-drill activity, run `mcp__sources__verify_words` on both sides of each pair. If the "wrong" word is in VESUM without restrictive tags, the framing must shift to register/style rather than dictionary-correctness — or the pair must be dropped.

### CC-3 — All 7 plans completed v1.x review-and-lock cycle (consistency confirmation)
All seven plans have `lifecycle: locked`, `reviewed_at: 2026-04-23` (or 2026-04-25 for the #1550 letter-module pass), `reviewed_by` populated, and explicit `review_notes` (sometimes long-form). Their v1.x changelogs document fixes from earlier reviews (e.g., М1's А у тебе? → А тебе? fix, М3's re-scoping, М4's intonation-contradiction fix). **This is a strong consistency signal** — the LOCKED batch has internal QA discipline. The findings here are residual edge-case items, not first-pass rework.

### CC-4 — NUS textbook citation hygiene (all 7 plans)
Every plan cites specific NUS textbook authorities by author, grade, page (Заболотний 5 кл. с.83; Захарійчук 1 кл. с.13–15; Большакова 1 кл. с.24, с.25, с.29, 2 кл. с.58–59; Авраменко 5 кл. с.19, с.75; Літвінова 5 кл. с.130; Кравцова 2 кл. с.13; Вашуленко 2 кл. с.23–27). This citation density per A1 is unusual and high-quality — the build pipeline can trust these references for review-tier evidence.

## Suggested Template Fixes Per Cluster

### Template fix #1 — Add `pedagogical_deviations_from_standard:` field

For plans that use case-form chunks before the State Standard module:

```yaml
pedagogical_deviations_from_standard:
- form: "Мене звати"
  case_involved: accusative
  standard_first_module: 11
  this_module: 5
  rationale: "Frozen self-introduction chunk; productive accusative paradigm deferred to M11."
- form: "А тебе?"
  case_involved: accusative
  standard_first_module: 11
  this_module: 5
  rationale: "Echo-reciprocal chunk for name exchange; explicitly distinguished from `А у тебе?` which would invoke genitive-with-preposition."
- form: "Я з + country.GEN"
  case_involved: genitive
  standard_first_module: A2
  this_module: 5
  rationale: "Country-name set phrase; genitive paradigm deferred to A2."
```

### Template fix #2 — VESUM-anchored Surzhyk drills

For Surzhyk fill-in activities: add a checklist comment at top of `activity_hints`:

```yaml
# Surzhyk-drill VESUM check (run before lock):
# - Each "wrong" form must be NOT FOUND in VESUM, OR
# - Must be reframed as register/style contrast, OR
# - Must be dropped from the drill.
# Last verified: YYYY-MM-DD with mcp__sources__verify_words batch.
```

### Template fix #3 — Zero-budget section policy

Plan field validator should reject `words: 0` sections OR require an explicit `omit_from_render: true` flag. Currently the writer may silently drop content. File as plan-schema enhancement.

## Per-Module LOCK Recommendation (one-line table)

| slug | status | severity-summary | LOCK_NOW | NEEDS_FIX | NEEDS_REVISION |
|------|--------|------------------|----------|-----------|----------------|
| sounds-letters-and-hello | NEEDS_FIX | 2 MEDIUM (1pl imp; rare И key-word) | | ✅ | |
| reading-ukrainian | PASS | clean | ✅ | | |
| special-signs | PASS | clean (exemplary) | ✅ | | |
| stress-and-melody | PASS | 1 MEDIUM (future TTS) | ✅ | | |
| who-am-i | NEEDS_FIX | 1 HIGH (Підсумок=0) + 3 MEDIUM (acc/gen chunks documented) | | ✅ | |
| my-family | PASS (borderline) | 1 MEDIUM (`муж` register) | ✅ (lenient) / ✅ (strict NEEDS_FIX) | (✅) | |
| checkpoint-first-contact | NEEDS_FIX | 1 HIGH (`папа` contradiction) + 1 MEDIUM (checkpoint word_target policy) | | ✅ | |

## Orchestrator Action Items (in priority order)

1. **LOCK_NOW**: M2 (reading-ukrainian), M3 (special-signs), M4 (stress-and-melody). Three clean plans ready for overnight build queue.
2. **Single-line YAML fixes** (NEEDS_FIX, dispatch as one batch):
   - M1: replace `Прочитаймо` → `Прочитай`; replace `ирій` → `іній`.
   - M5: delete `Підсумок: words: 0` section OR allocate 50 words and rebalance Діалоги 350→300.
   - M7: remove `тато/папа` Surzhyk-drill row; reframe `тато` vocab note.
3. **Borderline (M6)**: decide team policy on `муж/чоловік` — drop the row OR add register-note. Then LOCK.
4. **Cross-cutting decisions** (separate dispatch, not blocking M1–M7 build):
   - CC-1: add `pedagogical_deviations_from_standard:` field convention (template fix #1).
   - M-5 / CC-5: curriculum-wide A1-checkpoint word_target reconciliation (1000 vs 1200). 5 plans need alignment.
   - Template fix #2: VESUM-anchored Surzhyk-drill discipline as a plan-review checklist item.
   - Template fix #3: schema-validator rejection of `words: 0` sections.
5. **No NEEDS_REVISION** — all 7 plans are structurally sound with editing-grade fixes, not pedagogical rewrites.

## Notes on Method

- All 7 plans had been through the v1.x review-and-lock cycle in 2026-04-23/25. This audit is a second-pass cross-cutting consistency check, not a first review.
- Verifiable claims were tool-backed via `mcp__sources__verify_words` (53-word batch) and `mcp__sources__search_style_guide` (limited 46% coverage, no hits on queried Russianism phrases).
- Per #M-4 (deterministic-over-hallucination): no claim about word existence, level scope, or section sum was made without a tool call or yaml-arithmetic verification.
- No plan YAMLs were modified. All edits are recommendations only.
