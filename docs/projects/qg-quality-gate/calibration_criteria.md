# Calibration Criteria & Level Profiles for LLM Quality Gate Reviewer

This document defines the calibration criteria, level profiles, false-positive/false-negative controls, and structural validation specifications implemented for the LLM reviewer layer in the Ukrainian-quality gates evaluation harness (#4309).

> [!NOTE]
> **Deterministic Layer Precedence**:
> Lexical Russianisms, orthography, and baseline grammar validation are handled FIRST by deterministic gates (#4308, #912, curriculum QG). The LLM reviewer pass acts as a supplementary gate for style, register, and stylistic calques.

---

## 1. Level Profiles & Immersion Policies

Linguistic expectations and immersion rules are strictly partitioned by target CEFR level:

### A1/A2 (Scaffolded Support)
* **Goal**: Provide beginner-appropriate bilingual grounding.
* **Scaffolding Policy**: Substantial English instruction and translation scaffolding are expected and allowed.
* **Defect Handling**: Do NOT flag English text as leakage. English is only rejected if it contains AI personae, temporary paths, or internal metadata.
* **Max-Immersion Constraint**: Never recommend increasing the English ratio or adding English translations where Ukrainian-only content exists. Respect the level's maximum immersion goal.

### B1+ (Ukrainian-led Immersion)
* **Goal**: Transition learners to full immersion.
* **Immersion Policy**: All instructional prose, grammar explanations, and metadata directions must be written in natural Ukrainian.
* **Defect Handling**: Any English-led paragraphs or English explanations are flagged as `ENGLISH_LEAKAGE` (`level_policy` dimension, `critical` severity).
* **Gloss Exemption**: Brief bilingual vocabulary glosses (e.g. `**Застосунок** - app.`) are allowed and must not be flagged.

### Seminar Register & Factual Sensitivity (bio, folk, hist, istorio, lit, oes, ruth, etc.)
* **Goal**: Achieve scholarly register, factual correctness, and historical sensitivity.
* **Pathos/Register Control**: Strictly avoid marketing language, enthusiastic hype, and patriotic slogans (e.g., "неймовірна подорож", "пориньмо у захопливий світ"). The register must remain objective and formal.
* **Vital Status Check**:Biography modules must verify whether the subject is living or deceased. For LIVING subjects, headers or prose sections implying death or legacy (e.g., "Last Years" / `Останні роки` or "Legacy" / `Спадщина`) are strictly forbidden as they mimic obituaries. Instead, use "Contemporary Stage" / `Сучасний етап` or "Influence" / `Вплив`.
* **Factual Grounding**: All historical and cultural details must be verified against primary resources (e.g., `litopys.org.ua`). The YouTube channel "REALNA ISTORIIA" (Akim Galimov) is the gold standard for historical modules. Reject low-quality propaganda channels.

---

## 2. Severity Calibration Guidelines
* **critical**: Factual errors, resource/evidence/pipeline leakages (AI personae, absolute paths), missing mandatory structural elements (such as model answers in B2+), and severe grammatical errors (such as case alignment or predicative-instrumental errors).
* **warning**: Style and register issues (unnatural/syntactic calques, unnatural metalanguage/register, minor prepositions), or pedagogical mismatches.
* **info**: Non-critical suggestions, minor stylistic alternatives, or optional improvements.

---

## 3. B1-27 Calibration Criteria (HARD Calibration)

The B1-27 *restored-bad* examples contain unidiomatic or calqued Ukrainian constructions that are not lexical Russianisms (pure Russian words) but are stylistic/syntactic defects. The reviewer must detect:

| Restored-Bad Phrase | Expected Issue ID | Dimension | Severity | Target Idiomatic Ukrainian | Rationale |
|---|---|---|---|---|---|
| `застосунок має бути відкритий` | `AWKWARD_PASSIVE_RESULT_STATE` | `ukrainian_style` | `critical` | `відкрийте застосунок` / `застосунок має бути відкритим` | Predicative-instrumental case error (nominative instead of instrumental). Do NOT flag 'має бути відкритим'. |
| `Застереження каже: будь обережний` | `UNNATURAL_ANTHROPOMORPHISM` | `ukrainian_style` | `warning` | `Зверніть увагу` / `Будьте обережні` | Abstract warnings must not speak. Scoped strictly to metalanguage; do NOT flag natural personifications like 'правило каже'. |
| `радить не робити певної поведінки` | `UKRAINIAN_GRAMMAR_CALQUE` | `ukrainian_style` | `warning` | `рекомендує уникати...` | Unnatural verbal government and nominalization calque. Downgraded to warning. |
| `дія має дати конкретний результат чи описати процес?` | `UNNATURAL_META_REGISTER` | `ukrainian_style` | `warning` | (Avoid in learner-facing text) | AI/reviewer metalanguage / dry syntactic jargon in learner-facing text. Downgraded to warning. |
| `доконаний вид дає результат із вікном` | `UKRAINIAN_GRAMMAR_CALQUE` | `ukrainian_style` | `warning` | `доконаний вид позначає результат...` | Literal calqued metaphor and unidiomatic argument structure. Downgraded to warning. |
| `У кухні` | `CALQUED_PREPOSITION` | `ukrainian_style` | `warning` | `На кухні` | Location prep calque. Downgraded to warning; do not auto-fail in informal contexts. |

---

## 3. False-Positive / False-Negative Controls

To maintain high precision, the LLM reviewer must distinguish actual defects from valid teaching contexts:

* **Contrastive Examples**: The presence of a bad form (e.g., in a "Correct vs Incorrect" table or strikethrough like `~~wrong form~~`) is a `teaching_contrast` or `quoted_bad_form` disposition and must not penalize the module.
* **Heritage/SUM Attestation**: Authentic Ukrainian archaisms, dialectal forms, and complex syntax validated by VESUM/СУМ/Grinchenko must not be flagged as calques or Russianisms.
* **Level Simplicity**: A1/A2 grammatical simplicity (e.g., SVO rigidity or explicit copula `є` in early A1) must not be flagged as unnatural.

---

## 4. Structural Model Answer Check Spec

For modules graded at level B2, C1, or C2, all productive writing tasks (specifically `type: essay-response` in `activities.yaml`) must contain a `model_answer` field, and the answer must start with the markdown callout:
```markdown
> [!model-answer]
```
If missing, it triggers a `MISSING_MODEL_ANSWER` defect:
* **Dimension**: `pedagogical`
* **Severity**: `critical`
* **Disposition**: `defect`
* **Confidence**: `deterministic`

---

## 5. Live Tier-2 Enablement — Exit Criteria (#4370 extension; fleet-reviewed 2026-07-06)

Live Tier-2 (the tooled LLM reviewer auto-invoked inside `qg_workflow` on real modules, spending real
quota) stays DISABLED until ALL criteria hold. Panel: codex + cursor + agy (bridge tasks
`review-4370-exit-criteria*`), all findings folded; deepseek separately audited the underlying
scorecard numbers. E3 is a **minimum regression canary** («better than bare + gates alive»), NOT a
quality bar — arming does not assert seminar fact-checking is defect-free (the claim↔evidence
alignment gap is un-gateable by construction).

### E0 — The explicit arm (manual, user-visible)
`WorkflowOptions.enable_llm` defaults off and `DEFAULT_REVIEWER_MODEL_ID` is the sentinel
`llm-reviewer-disabled-until-4370`. Arming = replacing the sentinel with the production pin +
enabling the flag in ONE reviewed commit that links the green E3 evidence. Scope the first arm to
the SEMINAR route only (the B1+ gemma prompt-only route has no MCP grounding and needs its own
canary before arming).

### E1 — Grounded end-to-end evidence ✅ (recorded, with named residual)
The transport→telemetry→gates→verdict chain ran live: D6 «Веснянки» (model-evidence.md §D6) and the
step-3 matrix (SCORECARD.md, committed). NAMED RESIDUAL: the vesnianky melody M-trap was CONFIRMED
on a real-but-irrelevant excerpt in both — claim↔evidence alignment is model judgment. The D6
quote-abridgment debt is CLOSED (#4416/#4429, segment-wise normalized matching, `qg_workflow.v3`).

### E2 — Bare control measured ✅ + no-bare-fallback is BINDING
Harness lift +180…+310 (§step-3): bare models CONFIRM fabrications. Consequences: (a) Tier-2 has NO
tool-less fallback — provider failure = PROVIDER_FAILURE/INCOMPLETE, never parametric judgment;
(b) build item: `assert require_mcp` on the seminar live path + a lint that no production entrypoint
constructs a bare-arm invocation (bare exists only under `QG_BAKEOFF=1`).

### E3 — Minimum regression canary ⏳ (the operational switch)
Run the 4-fixture tooled matrix on the PRODUCTION pin (`--arm tooled --force`, fresh out-dir), then
evaluate with the deterministic checker (build item: `scripts/audit/qg_tier2_canary_check.py`,
nonzero exit on fail — never human-parsed SCORECARD). The canary set is PINNED to the four
folk-domain anchors (`qg_tier2_canary_check.CANARY_FIXTURE_SLUGS`: koliadky, kupalski, vesnianky,
zhnyvarski), NOT to every fixture in `tests/fixtures/qg_bakeoff/` — that directory is also the growth
corpus for the #4312 paper (e.g. the #4539 history-domain passages), and extra passages must not move
the 7/4 denominators or the required-artifact set. Expanding the pinned set is a DELIBERATE
re-calibration (bump denominators + thresholds in one reviewed commit), never a side effect of adding
a bakeoff fixture. The checker consumes only single-run calibration directories; multi-run bakeoff
reference directories are deliberately refused and must not be used as E3 inputs. PASS requires ALL,
per the STRICT live path (bakeoff-orthogonal stripping does NOT
apply to production):
- (a) every cell: `status=ran`, `invalid_fact_checks=0`, `required_ungrounded_findings=0`,
  `findings_schema_invalid=false`, no parse/provider failure. NOTE (codex, verified): today's
  tooled cells are `ungrounded_findings` — the current pin does NOT yet pass; that is the point.
- (b) `missing_claims=0` and class-M alignment ≥ 4/7 (anti-gaming: a model must not pass by
  OMITTING hard claims);
- (c) class-U: 0 CONFIRMED (judgment column), honesty ≥ 3/4;
- (d) class-M: 0 CONFIRMED-on-fabricated EXCEPT cells named in the committed allowlist
  (`tier2_canary_allowlist.json`; today: the vesnianky melody alignment cell). A new exception
  requires a reviewed allowlist commit — never a threshold bump;
- (e) flap control: TWO consecutive green runs to arm; ANY red run after arming = auto-disarm
  (restore E0 sentinel) until re-greened;
- (f) provenance recorded per run: fixture-set hash, gate_version, prompt hash, pin, route, date;
- (g) freshness: re-run on ANY change to prompt/gates/schema/pin/route/fixtures/scorer, AND max
  age 7 days before any broad live batch;
- (h) RELATION to the existing dispatcher canary (`llm_qg_canaries` → `_exact_canary_passes`):
  DISTINCT and BOTH REQUIRED. The dispatcher canary guards per-route calque/register behavior at
  dispatch time; this regression canary guards fabrication/grounding behavior at arming time.
  Passing one never substitutes for the other.
- (i) diagnostic (non-blocking): one second-family reference cell for drift comparison — it must
  never imply fallback routing.

### E4 — Cost factors from measured data ⏳
`estimate_llm_cost` still uses placeholder rates («prompt byte estimate»). Replace with step-3
medians (tool calls/passage: gemma 4–8, ds-pro 10–17, ds-flash 15–35; wall 16–268 s; OpenRouter
gemma pin + deepseek API pricing), cite SCORECARD.md, add a soft anomaly band (~1.5× max observed
tool calls → telemetry warning, never a cell failure; the hard 40-call cap stays).

### E5 — Routing guard on the Tier-2 transport ✅
`_invoke_opencode_reviewer` asserts the guard (qwen ban + no subscription-family-over-OpenRouter);
`tests/audit/test_qg_bakeoff.py::test_reviewer_opencode_transport_is_guarded` green.

### E6 — Post-arm operations ⏳ (must exist BEFORE the first broad batch)
- Circuit breaker: >15% terminal failures over any 30 consecutive live passages → trip, alert,
  pause (no quota burn on a failing lane);
- SLO telemetry: track `inadmissible_positive_verdicts`, theatre invalidations, provider error
  rate, cost vs E4 estimate;
- Rollback: ONE documented disarm procedure (E0 sentinel restore + invalidate current
  gate_version cache rows + spend-ledger freeze);
- Quota preflight before batch compiles;
- Human spot-check of live seminar fact-check findings until the alignment gap closes;
- Ownership: the infra driver runs canaries and commits evidence; the USER approves the first
  broad live batch.
