# Seminar module builds must SELF-CONVERGE — design (#3079)

> **Status:** DESIGN (design-first, do-NOT-blind-dispatch) — authored by the folk/seminar track driver
> (Claude) per the Session-36 handoff RESUME-HERE #3. **Owner of implementation: the infra orchestrator**
> (this is shared pipeline infra: `scripts/build/linear_pipeline.py` + `scripts/build/v7_build.py`, blast
> radius = every track). The track driver files the need + the spec; it does NOT write the pipeline code.
> **Top priority** (user 2026-06-13): the root cause of "manually made" seminar modules.
>
> **Companion docs:** issue **#3079** (the epic); `docs/folk-epic/folk-wiki-compile-grounding-register-gap.md`
> (the sibling wiki-side diagnosis, now LANDED via #3036/#3054/#3057/#3059/#3083); the koliadky proof-rebuild
> (PR **#3250**, 6.7→9.2); `docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md` (ADR-007 — bans
> LLM *regeneration*, but explicitly **sanctions `<fixes>` `insert_after:`**, the mechanism this design
> reuses; an amendment is needed only for the conditional B2 deepen path); `scripts/common/thresholds.py`
> (the LLM-QG dim taxonomy); `scripts/wiki/review.py` (the PROVEN divergence-safe loop to port).

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

The moves that closed 7.4→9.2 split into TWO classes, and ADR-007
(`2026-04-23-rewrite-strategies-kill-or-revert.md`) draws the line **between** them — not, as an earlier
draft of this doc claimed, around "anything that isn't find/replace":

- **ADDITIVE moves** — surface an embedded primary, add a self-check, add a worked example / activity
  scaffold, add a clarifying note. These are **inserts at an anchor**, and the V7 pipeline **already supports
  them**: `<fix><insert_after>ANCHOR</insert_after><text>…</text></fix>` is a first-class fix type with a full
  applier (`linear_pipeline.py:6048–6980`), used in production today by the wiki_coverage correction loop
  (`scripts/build/phases/linear-correction-wiki-coverage.md`). ADR-007 **explicitly sanctions** it —
  `<fixes>` `insert_after:` is the *named* repair for word-budget shortfalls (ADR-007 lines 35/82/102), and
  the invariant test `tests/test_no_rewrite_contract.py` bans only the **regeneration** symbols
  (`section_rewrite`/`full_rewrite`/`writer_swap`/`<rewrite-block>`), never insertion.
- **DEEPEN-EXISTING-PROSE moves** — rewrite a shallow paragraph into a rich one. This IS what ADR-007 KILLs
  (the `full_rewrite`/`<rewrite-block>` class), and it has hard empirical evidence behind the ban: FROM-
  SCRATCH rewrites degraded content 9.6→9.2→8.4, re-validated on a1/colors (ADR-007 §Context).

**So the keystone is NOT "we must amend ADR-007."** The keystone is **Gap A**: there is no LLM-QG correction
loop to invoke the *already-compliant* `insert_after` fixer on pedagogical findings (the per-dim reviewer
`linear-review-dim.md` emits only `{score, evidence, verdict}` today — a pure scorer, no `<fixes>`). Build
that loop (§3 Part B1) and the **additive** half of the koliadky lift is automated with **no ADR change, no
test change, no new risk class**. The ADR-007 carve-out (§3 Part B2) is needed ONLY for the deepen subset,
and ONLY if validation shows insert-only can't clear ≥8 — do not reopen a twice-validated failure mode for a
win we may not need.

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
**B1 is the quick win** (insert-only corrector reusing the ADR-007-clean `insert_after` — no ADR change);
**B2 is a conditional architectural decision** (the deepen carve-out, only if B1 can't reach ≥8). **D is the
payoff** (re-promote pedagogy so the gate holds). A+C+B1 is the shippable quick win; B2 is contingent.

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
        fixes = corrector(report)                     # Part B1 insert_after fixes (B2 deepen if needed)
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

### Part B — the pedagogical corrector (B1 insert-only = quick win; B2 deepen = conditional carve-out)

Part A's loop needs a corrector. Split it in two by ADR-007's actual line (Gap B):

#### B1 — insert-only pedagogical corrector (NO ADR change — the quick win)

A new corrector prompt `linear-correction-pedagogical.md` that, given the reviewer's pedagogical findings
(already structured: `evidence` / `evidence_quotes` in `llm_qg.json`) + the **corpus-embedded primaries**
now available via #3162's `literary_texts` excerpt route, emits **`<fix><insert_after>…</insert_after>
<text>…</text></fix>`** entries that ADD the missing pedagogy at an anchor:

- surface the embedded primary the module teaches (the literal "external text"),
- insert a self-check / reflection block,
- insert a worked example or an activity scaffold,
- insert a clarifying "why this matters" note.

This **reuses already-built, already-ADR-007-compliant machinery**: the `insert_after` applier
(`linear_pipeline.py:6048–6980`) and the corrector-prompt pattern (mirror `linear-correction-wiki-coverage
-narrow.md`). **No `tests/test_no_rewrite_contract.py` change, no ADR change** — `insert_after` is the
sanctioned repair, not a forbidden one. Guardrails (all already available): re-gate every insert through
python_qg (Part C) so an insert that breaks vesum/word_count is rejected; wrap in Part A's best-round so an
insert that lowers the aggregate is discarded; **corpus-grounded only** — embedded primaries must be
`verify_quote`-resolvable, never invented; no new vocabulary/coinages (python_qg vesum catches them).

**Validate B1 first (on koliadky/dumy).** Much of koliadky's 7.4→9.2 lift was additive (embed the колядка,
self-checks, activity integration) — B1 alone may reach ≥8. If it does, B2 is **not needed**.

#### B2 — deepen-existing-prose corrector (CONDITIONAL — needs the ADR-007 carve-out)

Only if B1 validation shows insert-only cannot clear ≥8 (because the gap is *shallow existing prose*, not
*missing pedagogy*) do we need to modify existing paragraphs — which IS the `full_rewrite` class ADR-007
KILLs on hard evidence. Then, and only then, author **ADR-009 (supersede-in-part ADR-007)** for a
**bounded, scoped** pedagogical re-write with guardrails that restore the safety ADR-007 protected:

- **Scope-bounded:** pedagogical dim only; only the reviewer-named locations; a **diff-size cap** (reject a
  re-write touching >N% of the module — that's regeneration, not correction). Update the invariant test to
  permit the scoped path by its new symbol while still banning the KILLed `full_rewrite`/`<rewrite-block>`.
- **Divergence-safe:** Part A best-round + MIN-guard discards any re-write that lowers the aggregate — this
  is exactly the safety the 9.6→8.4 evidence demanded, restored mechanically instead of by a blanket ban.
- **No-self-review** (writer ≠ reviewer model, existing assertion); **re-gated** through python_qg every
  round; **corpus-grounded, not invented**. Corpus-hammer (#M-11) remains the human gate before ship.

**Recommendation: build B1, validate, and only open B2 if the data demands it** — root-cause fix first, do
not reopen a twice-validated failure mode pre-emptively.

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
| **P3** | **Part B1 — insert-only pedagogical corrector** (`linear-correction-pedagogical.md` emitting `insert_after`; reuses the existing applier). **NO ADR change, NO test change** — the quick win | P2 | **Low–med** |
| **P3-validate** | Run B1 e2e on koliadky/dumy. **If pedagogical ≥8 → STOP (B2 not needed).** Else scope B2 | P3 | — |
| **P4** | Part C.3 — bounded multi-gate python_qg loop + cross-model fixer route | P0, P1 | Med |
| **P5** | **Part B2 — deepen-prose carve-out** (ADR-009 + scoped re-write + invariant-test update) — **CONDITIONAL** on P3-validate failing | P3-validate, ADR sign-off | **High** (architectural) |
| **P6** | Part D — re-promotion data capture → flip `pedagogical` terminal for seminar | P2–P4 + ~20 ships | Low (data-gated) |

**The quick win is P0→P2→P3 (the insert-only loop) — no ADR change, reuses built machinery.** Only **P5
(B2)** needs explicit user/orch sign-off, and only if P3-validate shows insert-only can't clear ≥8. P0–P2 +
P1/P4 are mechanical ports + deterministic gate fixes and can proceed in parallel.

## 5. Acceptance criteria (deterministic — tied to #3079)

- [ ] A folk module reaches `module_done` (python_qg PASS → LLM QG PASS) with **zero manual intervention**
      on a clean run, OR via the bounded automated loop above (no human-driven fixes).
- [ ] **koliadky + dumy rebuild to produce `llm_qg.json` with pedagogical ≥8 automatically** (koliadky's
      manual 9.2 is the target the loop must reach unaided; dumy is the unproven case).
- [ ] The pattern holds for **≥1 other seminar track** (hist or lit — not folk-only).
- [ ] B1 (insert-only) ships with `tests/test_no_rewrite_contract.py` **unchanged** (insert_after is already
      compliant). If B2 is opened, the test still **rejects unscoped regeneration** and permits the scoped
      deepen path only under the ADR-009 guardrails (diff-cap, scope-bound, re-gated).
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

1. **B2 sign-off — DEFERRED, conditional.** The ADR-007 carve-out (deepen-existing-prose) is needed ONLY if
   P3-validate shows the insert-only loop (B1) can't reach ≥8. **No decision needed now** — build B1 first
   (no ADR change). If B2 becomes necessary, the recommendation is yes with the §3-B2 guardrails (best-round
   restores the safety ADR-007 protected). The earlier "P3 needs sign-off" framing was based on the wrong
   premise that all pedagogical correction needs regen; insert_after handles the additive majority.
2. **Reviewer cost** — claude-routed seminar LLM-QG over N rounds is Claude-quota-heavy (same finding as the
   wiki review fleet, Session-20b). Acceptable for the bounded seminar set; revisit if it dominates quota.
3. **Shared helper extraction (P0)** — port wiki helpers into `scripts/common/review_loop.py` so module +
   wiki share one tested loop, vs. duplicate the logic in `linear_pipeline.py`. **Recommendation: extract**
   (one tested implementation; the wiki loop is the battle-tested one).

---

## 8. P3-VALIDATE FINDINGS (Session 39, 2026-06-16) — the rotating wall is mostly GATE FALSE-POSITIVES, not coinages

**P3-validate ran for real this session** (`v7_build.py folk koliadky-shchedrivky --no-resume --worktree`, build
`folk-koliadky-shchedrivky-20260616-002047`). **Root-cause note on the prior "validation":** the Session-38
in-flight build silently NO-OP'd — `v7_build.py` **resumes by default** (`v7_build.py:1289` "skip a phase iff its
on-disk artifact exists AND reports success"), the worktree was cut from `origin/main` where koliadky already
exists at 9.2, so the writer/gates were skipped and `module.md`/`llm_qg.json` came back **byte-identical to main**.
The 9.2 was stale. **Any "does a fresh build self-converge" validation MUST pass `--no-resume`.**

### Outcome (c): the build never reached the B1 LLM-QG loop — `python_qg` terminated first
`module_failed phase=python_qg, reason="Python QG failed after ADR-008 correction paths"` (492s, after 2 correction
passes on the SAME failing words → per-gate single-shot `attempts` wall at `linear_pipeline.py:5662`). The 3 failing
gates: `word_count` (4026/4600), `vesum_verified` (7 missing), `citations_resolve` (5 unknown). So **B1 is necessary
but unreachable on a fresh build until Gap C is closed** — exactly as §1 Gap C predicted, now with the precise
taxonomy below.

### The 7 `vesum_verified` "missing" words split into 4 classes — 3 are FALSE POSITIVES no corrector can fix
Verified deterministically (ran `_extract_blockquote_records` + `verify_words` + `search_heritage` on the real build
artifacts):

| Class | Words (this build) | Where | Why flagged | Proper fix |
|---|---|---|---|---|
| **A. Verbatim folk primary embedded in `activities.yaml`** | `нащада`, `било`, `сонінько` | `activities.yaml:91` (col quoted in a compare activity), `:72` (a щедрівка `passage:`) | The module.md blockquote exemption (`_strip_quote_fidelity_verified_blockquotes`, L10188) **works** — it correctly strips these from `module.md` scope — but it does NOT reach yaml `passage`/list fields. `сонінько` is NOT in VESUM and has **no** heritage evidence → it can ONLY be handled by primary-exemption, not per-word attestation. | **Extend the verbatim-primary exemption to embedded primaries in `activities.yaml`/`vocabulary.yaml` quote fields** (#2991 yaml-scope × #3162 primary-embedding). |
| **B. Meta-linguistic citation of dialectal forms** | `нащада`, `било`, `лем` (again) | `activities.yaml:97,102` — analysis text citing «било», «з нащада», «лем» as objects of discussion | A MENTION, not a use. The existing citation arm of `_WARNING_QUOTE_RE` (L763) exempts only `як/such as «X»`; bare «X» citation of a dialectal form in analysis is not exempted (the restriction to `як «X»` was deliberate — do NOT widen to all bare «X»). | Add a **guarded** dialectal-citation exemption: bare «X» exempt only when X also appears in a verified primary of the same module, or after an explicit `діалектн…`/`запис`/foreign-reject marker. |
| **C. Foreign comparative proper nouns** | `Йоль`, `Ялда`, `Ялду` | module prose L32 + `activities.yaml:155` (comparing Yule/Yalda/Saturnalia) | Transliterated foreign festival names, declined into UK cases. Not Ukrainian lemmas. **Inconsistency proof:** `Сатурналії` is ALSO absent from VESUM yet was NOT flagged → the proper-noun handling is ad hoc. | Foreign-proper-noun handling — an allowlist of attested foreign cultural terms OR a writer foreign-term marker the gate honours. |
| **D. Genuine coinage** | `дерево-явір`, `першопочаток` | `activities.yaml:170` ("світове дерево-явір"), module prose | Real descriptive compounds, not in VESUM, no quick heritage. `явір` IS in VESUM; the hyphenated compound is the writer's. These are the ONLY genuinely-fixable items — rephrase (`світове дерево — явір`) or deeper heritage-attest. | The **cross-model fixer** (Part C.3) rephrases; OR writer-correction. |

`citations_resolve`: the 5 "unknown" are **canonical** Ukrainian scholarship (Костомаров «Слов'янська міфологія»,
Чубинський, Чижевський, Попович) + the народна-творчість primary — cited by the writer but absent from the plan's
`[S#]` registry. **Fix:** promote these canonical sources into the plan reference registry (plan-side) and/or a
canonical-source resolver in `citations_resolve`. `word_count` 4026/4600 is a real under-write the LLM-QG/writer
correction must close by ADDING prose — downstream of unblocking python_qg.

### Structural conclusion (refines §1 Gap C and the §4 plan order)
**Gate-correctness is logically PRIOR to the C.3 multi-gate loop.** A loop cannot "correct" a verbatim primary, a
glossed foreign comparison, or a cited dialectal form — deleting them is wrong. So even a perfect multi-gate loop
churns/diverges on classes A/B/C. The corrected sequencing:

1. **C.2a (Class A) — extend verbatim-primary VESUM exemption to embedded primaries in `activities.yaml`/`vocabulary.yaml`.**
   HIGHEST leverage (every folk module embeds cols/щедрівки/думи as activity passages), unambiguously correct,
   reuses the existing `_extract_blockquote_records`/attribution machinery. **Signal design (pick the robust one):**
   (i) cross-reference — an activity passage that reproduces a verified `module.md` primary inherits its exemption
   (safe, but misses passages unique to activities, e.g. the `сонінько` щедрівка); (ii) **verify_quote / literary-corpus
   resolution** — a passage that resolves to a folk/literary corpus primary is exempt (robust, can't be gamed; the
   `_textbook_grounding_gate` already does corpus matching for textbooks, so extending to the literary/folk corpus is
   architecturally consistent = #3162's "literary-corpus routing"); (iii) structural primary-source marker the writer
   emits. **Recommendation: (ii) corpus-resolution, with (i) as a corroborating fast-path.**
2. **C.2b (Class B) — guarded dialectal-citation exemption** (do not over-widen bare «X»).
3. **C.2c (Class C) — foreign-proper-noun handling** (allowlist or marker; fix the Сатурналії-vs-Йоль inconsistency).
4. **C.3 (Class D + word_count + the loop) — bounded multi-gate python_qg loop + cross-model fixer** for the genuine
   residual coinages and to iterate across gates.
5. **citations_resolve — plan-registry promotion of canonical sources** (+ optional canonical resolver).

**Status this session:** C.2a dispatched for implementation (the first, highest-leverage, clearly-correct unit);
B/C/D + citations + the loop sequenced for follow-on driving. This taxonomy supersedes §1's pre-build guess that
Gap C was dominated by coinage churn — empirically it is dominated by **verbatim-primary + foreign-proper-noun +
dialectal-citation false positives**, which are deterministic gate-correctness fixes, not LLM-fixer work.
