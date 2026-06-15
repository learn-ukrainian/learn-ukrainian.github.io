# Seminar module builds must SELF-CONVERGE — design (#3079)

> **Status:** DESIGN (design-first, do-NOT-blind-dispatch) — authored by the folk/seminar track driver
> (Claude) per the Session-36 handoff RESUME-HERE #3. **Owner of implementation: the infra orchestrator**
> (this is shared pipeline infra: `scripts/build/linear_pipeline.py` + `scripts/build/v7_build.py`, blast
> radius = every track). The track driver files the need + the spec; it does NOT write the pipeline code.
> **Top priority** (user 2026-06-13): the root cause of "manually made" seminar modules.
>
> **Companion docs:** issue **#3079** (the epic); `docs/folk-epic/folk-wiki-compile-grounding-register-gap.md`
> (the sibling wiki-side diagnosis, now LANDED via #3036/#3054/#3057/#3059/#3083); the koliadky proof-rebuild
> (PR **#3250**, 6.7→9.2); `docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md` (ADR-007, the
> no-LLM-regeneration-during-review invariant this design must amend); `scripts/common/thresholds.py` (the
> LLM-QG dim taxonomy); `scripts/wiki/review.py` (the PROVEN divergence-safe loop to port).

---

## 1. The problem, root-caused

Every folk module shipped so far reached a shippable state **only by manual correction-loop driving**
(cross-model codex fixes, hand-fixed coinages/citations, manual re-gating, and — for pedagogy — a manual
structural re-write). "e2e finished seminar module" is today a *manual achievement, not a pipeline outcome*.
That blocks (a) trusting the modules as finished, and (b) scaling to the other 39 folk topics + the 6 other
seminar tracks (hist/bio/istorio/lit/oes/ruth — same pipeline, same walls).

Tracing the V7 module pipeline end-to-end (`v7_build.py::build_module`) the build is four stages:

| Stage | Code | Has a correction loop? | Divergence-safe? |
| --- | --- | --- | --- |
| 1. Writer | `_run_writer` → module.md + yaml | n/a | n/a |
| 2. **python_qg** (deterministic gates) | `linear_pipeline.run_python_qg_with_corrections` (L5274) | **Yes — single-shot PER GATE** | Partial: per-gate snapshot/rollback on regression |
| 3. wiki_coverage (LLM) | `_run_wiki_coverage_review` + batched/narrow correction loops | Yes | Yes |
| 4. **LLM QG** (the §7 dimensional review) | `v7_build._run_llm_qg` (L935) | **NO — single pass, no loop at all** | n/a |

The two stages that block seminar self-convergence are **#2 (python_qg)** and **#4 (LLM QG)**. Each fails
for a *distinct, separately-fixable* reason:

### Gap A — LLM QG has no correction loop, and `pedagogical` is advisory-only

`_run_llm_qg` runs each of the 5 dims (`pedagogical, naturalness, decolonization, engagement, tone`,
`scripts/common/thresholds.py:49`) **exactly once** and returns. There is **no round loop, no fixer, no
re-review** (contrast stage 2/3, which loop). The build then (`v7_build.py:1836-1866`) blocks **only on
terminal dims**, and per the 2026-05-23 architectural reset (`thresholds.py:58-76`) the only terminal
seminar dim is **`decolonization`**. `pedagogical / naturalness / engagement / tone` are **WARNING dims**:
a low score emits `llm_qg_warning` telemetry and **the build proceeds**.

So the pedagogical dimension — the one measured at **5.8–7.0 across ALL folk modules** (Session-32 parity
batch), the one the user's "surface folk" goal is gated on — **is never acted on by the pipeline.** It is
reviewed once, advisory, and ignored. This is *why* kalendarna shipped at 7.0 and koliadky/dumy shipped
with no `llm_qg.json` at all: nothing in the pipeline tries to raise it.

### Gap B — what raises pedagogical is STRUCTURAL, which find/replace cannot do (the ADR-007 wall)

The koliadky proof-rebuild (PR #3250) is the load-bearing evidence for the whole design:

- **#3162 alone** (embed the actual колядка the module teaches, via the `literary_texts` excerpt route)
  lifted pedagogical **6.7 → 7.4**.
- A **correction pass** (python_qg green + **pedagogical deepening** + register polish) closed **7.4 → 9.2**
  (pedagogical 9.2 · naturalness 8.6 · decolonization 9.5 · engagement 9.0 · tone 8.5 — claude reviewer).

The moves that closed 7.4→9.2 were **structural**: deepen an explanation, add a self-check, integrate an
activity inline, surface an embedded primary. **None of these is a `find`→`replace` pair.** But the V7
correction architecture is, by ADR-007 (`2026-04-23-rewrite-strategies-kill-or-revert.md`) and its
structural-invariant test `tests/test_no_rewrite_contract.py`, **reviewer-as-fixer = deterministic
find/replace only, NO LLM regeneration during review.** A naive "loop until the gate passes" built on
find/replace would therefore converge back to ~7.4 (cosmetic register/citation polish), **not** 9.2 —
because the score-moving work is exactly the work find/replace is forbidden from doing.

**This is the keystone architectural decision of #3079:** automating pedagogy requires a **scoped
pedagogical re-write pass** (a bounded writer re-invocation), which is a deliberate, guard-railed
**carve-out from the ADR-007 find/replace-only invariant** — see §3 Part B.

### Gap C — python_qg does not self-converge for seminar content (the rotating gate walls)

`run_python_qg_with_corrections` (L5274) is a `while True` loop, but it gives **one correction attempt per
distinct gate** (`if failed_gate in attempts → terminal`, L5317). For morphologically-rich, citation-dense
seminar prose it hits a *rotating wall* — fix `activity_schema`, re-gate trips `vesum_verified`, fix that,
re-gate trips `word_count`, etc. — and each manual session burned cross-model codex fixes to get through.
The documented sub-walls (issue #3079, folk Sessions 11–16):

- **#2991** — correction scope is **module.md-only** → vesum/coinage violations in `activities.yaml` /
  `vocabulary.yaml` / `resources.yaml` are *uncorrectable* by the loop (the self_check STRING-not-LIST
  defect recurs EVERY folk build for exactly this reason).
- **#2997** — `vesum_verified` false-flags authentic archaic forms inside verbatim `>` blockquotes; the
  exemption only matches the exact `не «X»` frame (`_WARNING_QUOTE_RE`), not cite-to-reject `«X»`.
- **Coinage churn** — the writer introduces ~1 VESUM-absent compound per build; find/replace can't rephrase
  → it either deletes content (word_count tanks) or substitutes a NEW coinage (divergence).
- **Citation resolution** — the writer cites a work not in the `[S#]` registry; the loop can't always fix.

The deterministic side already has *some* divergence-safety (per-gate snapshot + rollback on
`yaml_invalid` / `vesum_no_improvement` / `previously_passed_regression`, L5374-5432), but it is **per-gate
single-shot**, so the rotating wall defeats it.

---

## 2. The proven pattern to port (wiki #3054, already LANDED)

The folk **wiki** loop solved the exact same class of problem and is in production
(`scripts/wiki/review.py`). #3079 should **port these four mechanisms to the module loop**, not reinvent:

1. **Best-round selection** (`review_article`, L948-985): compute the final verdict on the round with the
   highest aggregate MIN, **not the last round** — the loop can diverge on dense seminar prose (bylyny
   measured MIN 5→6→6→5; round 4 was *worse* than round 2). A PASS always breaks immediately, so for any
   passing run best==last → this **never changes a PASS outcome or the written-back text**; it only stops a
   non-passing run from committing a degraded tail. Tie-break on the earliest round (fewest mutations).
2. **MIN-based regression guard** (`_min_score_regressed`, L1034): break only when the *aggregate MIN*
   regressed, so an already-passing dim's ±1 noise doesn't kill a still-converging run.
3. **Seminar round budget** (`max_rounds_for_domain`, L144; `SEMINAR_MAX_ROUNDS=4` vs core `MAX_ROUNDS=2`):
   dense source-grounded content needs more rounds for applied fixes to be re-reviewed.
4. **Folk-competent reviewer routing** (`seminar_reviewer_overrides`, L178): route culture dims to
   **claude**, NOT gemini — Session-20 *measured* gemini's ±5 round-to-round noise on dense Ukrainian prose
   (`register` 5-7 REJECT vs claude 9 PASS on the SAME article). gemini is fleet-barred for folk culture.

---

## 3. Design

Four parts. **A + C are the bounded-loop + divergence-safety port** (mechanical, low-risk, mirror wiki).
**B is the one genuine architectural decision** (ADR carve-out). **D is the payoff** (re-promote pedagogy
so the gate actually holds). A and C can ship independently of B; B is what gets pedagogy from ~7.4 to ≥8.

### Part A — add a bounded, divergence-safe correction loop to LLM QG

Wrap stage 4 in a loop modeled on `review_article`. New function (sketch — infra to implement in
`linear_pipeline.py`, called from `v7_build.py` where `_run_llm_qg` is invoked, L1805):

```
run_llm_qg_with_corrections(module_dir, plan, ..., writer, reviewer_override,
                            max_rounds, corrector):
    rounds = []
    for round_num in 1..max_rounds:
        report = _run_llm_qg(...)                     # existing single-pass review
        rounds.append(report)
        if all warning+terminal dims >= floor: break  # PASS → stop (best==last)
        fixes = corrector(report)                     # Part B: scoped pedagogical re-write
        if not fixes.changed: break                   # nothing applied → more rounds won't help
        if _min_score_regressed(prev, report): break  # divergence guard (port from review.py)
    best = argmax_round(aggregate_min)                # best-round selection (port)
    persist best.report as llm_qg.json; keep best module artifacts
```

- **Round budget:** seminar gets `SEMINAR_MAX_ROUNDS` (start at 3 — pedagogical re-writes are expensive;
  the koliadky lift took effectively two correction passes), core stays single-pass (no behaviour change
  for a1–c2 — keep `max_rounds=1` so this is a strict no-op there).
- **Reviewer routing:** the LLM-QG reviewer for seminar pedagogy/culture dims must be **claude/GPT, never
  gemini** (port `seminar_reviewer_overrides`; the existing `reviewer_override` plumbing already threads
  through `_run_llm_qg`). `_reviewer_for_writer` already forbids same-model self-review — preserve that
  assertion (`v7_build.py:954`).
- **Best-round + MIN-guard:** import/port from `review.py` (consider extracting the wiki helpers to a shared
  `scripts/common/review_loop.py` so module + wiki share ONE tested implementation — see §5).

### Part B — structural pedagogical correction (the ADR carve-out)

The corrector in Part A **cannot be find/replace** (Gap B). It must be a **bounded, scoped writer
re-invocation** — call it the **pedagogical re-write pass**:

- **Input:** the reviewer's pedagogical findings (already structured: `evidence` / `evidence_quotes` in
  `llm_qg.json`), the current module.md + activities.yaml, and the **corpus-embedded primaries** now
  available via #3162's `literary_texts` excerpt route.
- **Action:** re-invoke the **writer** (claude-tools) with a tightly-scoped prompt: "raise pedagogical by
  doing ONLY these structural moves the reviewer named — deepen X, add a self-check for Y, integrate
  activity Z inline, surface the embedded primary — change nothing else; do not introduce new vocabulary or
  coinages; keep every existing citation." Output is a full re-written module section set, re-gated through
  python_qg (Part C) before the next LLM-QG round.
- **The ADR decision (REQUIRED — do not ship Part B without it):** this is LLM regeneration in the review
  path, which ADR-007 forbids and `tests/test_no_rewrite_contract.py` enforces. Author **ADR-009 (or an
  ADR-007 amendment)** that carves out *exactly* this case with hard guardrails, and update the invariant
  test to permit the scoped path while still rejecting unscoped regen:
  - **Scope-bounded:** only the pedagogical dimension; only the reviewer-named locations; a diff-size cap
    (reject a re-write that rewrites >N% of the module — that's a regeneration, not a correction).
  - **Divergence-safe:** wrapped by Part A's best-round + MIN-guard → a re-write that *lowers* the aggregate
    is discarded (the prior round's artifacts are kept). This is the safety ADR-007 was protecting; we
    restore it via best-round instead of via "no regen at all."
  - **No-self-review:** writer ≠ reviewer model (existing assertion).
  - **Re-gated:** every re-write re-runs python_qg (Part C) — a pedagogical re-write that breaks vesum or
    drops word_count is rejected by the deterministic gate before it can reach the next LLM-QG round.
  - **Corpus-grounded, not invented:** the re-write may only add primaries that #3162 actually embedded
    (verify_quote-resolvable) — never invented text. Corpus-hammer (#M-11) remains a human gate before ship.

### Part C — make python_qg self-converge for seminar (close the rotating walls)

Three sub-fixes (each independently shippable; #2991 is the highest-leverage):

1. **#2991 — extend correction scope beyond module.md** to `activities.yaml` / `vocabulary.yaml` /
   `resources.yaml`. This alone kills the recurring self_check STRING-not-LIST wall and the yaml-side vesum
   walls. (Largest change; the per-gate snapshot/rollback machinery already exists — extend its file set.)
2. **#2997 — widen the verbatim-quote vesum exemption** to cite-to-reject `«X»` after explicit
   foreign/reject markers (російське/імперське/чуже «X»), not only the `не «X»` frame. Sibling to #2998.
3. **Bounded multi-gate loop + cross-model fixer route:** allow the python_qg loop a small bounded number
   of *total* rounds across rotating gates (not just one-per-gate), wrapped by a **best-round** snapshot of
   the whole artifact set (port the same mechanism), and a **cross-model fixer** for coinages/citations
   (the manual recipe used codex; wire it as the automated fixer the issue's acceptance allows). The
   existing regression rollbacks stay as the floor.

### Part D — re-promote `pedagogical` warning → terminal (the payoff)

The 2026-05-23 reset demoted the subjective dims because they were **stochastic** (0 shipped modules across
6 builds). Parts A+B+routing remove the stochasticity at its source: a **stable folk-competent reviewer**
(claude, not gemini) + **best-round** (no noisy-tail commits) + a **convergence loop**. Per the reset's own
re-promotion clause (`thresholds.py:73-75`: "~20+ shipped modules with captured human decisions"), once the
loop is producing stable pedagogical scores:

- Capture LLM-vs-human agreement on pedagogical across the next ~20 seminar ships (the corpus-hammer human
  read already happens — log the human pedagogical verdict alongside `llm_qg.json`).
- When agreement holds, **add `pedagogical` to `LLM_QG_TERMINAL_DIMS` for the seminar profile** (with the
  agreement-rate justification logged, as the reset requires). Then "≥8 pedagogical" becomes a *gate*, not
  an advisory — and "surface folk" is a deterministic predicate, not a manual judgment.

---

## 4. Phased implementation plan (owner: infra orchestrator)

| Phase | Deliverable | Depends on | Risk |
| --- | --- | --- | --- |
| **P0** | Extract wiki best-round + MIN-guard helpers to shared `scripts/common/review_loop.py` (refactor, no behaviour change; wiki tests stay green) | — | Low |
| **P1** | Part C.1 (#2991 yaml-scope) + C.2 (#2997 exemption) — deterministic, no LLM | — | Low–med |
| **P2** | Part A — LLM-QG bounded loop (best-round, MIN-guard, seminar round budget, claude routing); core stays single-pass (strict no-op) | P0 | Med |
| **P3** | Part B — ADR-009 carve-out + scoped pedagogical re-write corrector + invariant-test update | P2, ADR sign-off | **High** (architectural) |
| **P4** | Part C.3 — bounded multi-gate python_qg loop + cross-model fixer route | P0, P1 | Med |
| **P5** | Part D — re-promotion data capture → flip `pedagogical` terminal for seminar | P2–P4 + ~20 ships | Low (data-gated) |

**P3 is the one phase the user/orchestrator must explicitly sign off** (it changes a core invariant). P0–P2
and P1/P4 are mechanical ports + deterministic gate fixes and can proceed in parallel.

## 5. Acceptance criteria (deterministic — tied to #3079)

- [ ] A folk module reaches `module_done` (python_qg PASS → LLM QG PASS) with **zero manual intervention**
      on a clean run, OR via the bounded automated loop above (no human-driven fixes).
- [ ] **koliadky + dumy rebuild to produce `llm_qg.json` with pedagogical ≥8 automatically** (koliadky's
      manual 9.2 is the target the loop must reach unaided; dumy is the unproven case).
- [ ] The pattern holds for **≥1 other seminar track** (hist or lit — not folk-only).
- [ ] `tests/test_no_rewrite_contract.py` still **rejects unscoped regeneration**; the new scoped
      pedagogical path is permitted only under the ADR-009 guardrails (diff-cap, scope-bound, re-gated).
- [ ] Core a1–c2 builds are **byte-identical** (Parts A/C are seminar-gated; the LLM-QG loop is a strict
      no-op at `max_rounds=1`).

## 6. Validation plan (#M-11 — verify, do not assert)

Run the loop end-to-end on the three known cases and read the artifacts, not just the metrics:
1. **koliadky** — must reach pedagogical ≥8 *automatically* (the manual 9.2 proves it's achievable; the
   loop must reproduce it unaided). Best-round must never commit a round below the input.
2. **dumy** — the genuinely-unproven module (shipped with NO `llm_qg.json`); first automated e2e.
3. **one hist or lit module** — proves not-folk-only.
Corpus-hammer (#M-11) every embedded primary in the loop's output before any ship — the loop converges the
*gate*; the human still verifies the *artifact* (the m20 lesson: green metrics ≠ good module).

## 7. Open decisions (for the orchestrator / user)

1. **P3 sign-off** — approve the ADR-007 carve-out for a scoped pedagogical re-write? (Without it, pedagogy
   stays manual; with it, folk + all seminars scale.) **Recommendation: yes, with the §3-B guardrails** —
   best-round restores the safety ADR-007 protected, so the carve-out is bounded, not a return to free regen.
2. **Reviewer cost** — claude-routed seminar LLM-QG over N rounds is Claude-quota-heavy (same finding as the
   wiki review fleet, Session-20b). Acceptable for the bounded seminar set; revisit if it dominates quota.
3. **Shared helper extraction (P0)** — port wiki helpers into `scripts/common/review_loop.py` so module +
   wiki share one tested loop, vs. duplicate the logic in `linear_pipeline.py`. **Recommendation: extract**
   (one tested implementation; the wiki loop is the battle-tested one).
