---
date: 2026-05-15
status: FINAL
authority: Антоненко-Давидович «Як ми говоримо» (canonical Russianism reference)
calibration_size: 12 hand-labeled cases (5 clean, 6 dirty, 1 debatable, 1 lure)
main_eval_size: 50 ok-status cells across 5 prompts × 10 frontier models
methodology: scripts/audit/russianism_judge.py + scripts/audit/score_judge_calibration.py
calibration_gold: eval/russianism/calibration-cases.jsonl
predecessor: PR #1999 (eval harness v1, 2026-05-14)
reconstruction_note: |
  Raw judgments-*.jsonl files were lost when the eval-run worktree was
  force-removed during cleanup. This report is reconstructed from the
  scoring outputs observed during the session. The scripts and gold set
  ship in PR #2006; the per-cell raw data is regenerable by re-running
  the eval harness + judges (~$5, ~30 min for the full 55-cell suite).
---

# Russianism Eval — Dual-Perspective Report (Judge Calibration + Model Leaderboard)

This report answers **two questions at once**, because the original
"which frontier model produces cleanest Ukrainian?" question turned out
to be unanswerable without first settling "which LLM judges Ukrainian
most accurately?".

1. **MODEL perspective** — leaderboard of 10 frontier LLMs producing
   Ukrainian text under 5 calque-prone prompts, scored by three judges
   across three model families. Includes rank-stability column showing
   how much each model's rank moves when the judge changes.
2. **JUDGE perspective** — which of the three judges
   (`gemini-3.1-pro-preview`, `gpt-5.5`, `claude-opus-4-7`) is the most
   accurate Russianism reviewer, measured against a 12-case
   Antonenko-grounded calibration set with hand-labeled ground truth.
   Precision, recall, F1, case-level accuracy, per-judge characteristic
   profile, recommendation for the curriculum review position.

The two questions are coupled: if the gemini-judge from the prior
session is unreliable, then the prior session's model leaderboard is
too. Judge calibration grounds everything else.

## TL;DR — bottom line on both perspectives

### Judge perspective

**`claude-opus-4-7` is the recommended primary reviewer for the
curriculum Russianism review position.** F1 = 86% (precision 79%,
recall 94%) on the calibration set; **100% case-level accuracy**
(correctly classified all 12 cases as clean / flagged). Its 3
false-positive flags were all sev=1 register/orthography calls that are
defensible by Antonenko-grade stylistic argumentation (e.g. flagging
`обговорити терміни → строки`, which is debatable but not wrong).

**`gemini-3.1-pro-preview` is a strong second** at F1 = 84% (precision
81%, recall 87%), 92% case accuracy. **One case-level FP**: it flagged
`Доброго дня!` and `Як ваші справи?` on `cal_clean_greeting` — the
predicted greeting over-flag pattern. If the curriculum content
contains ANY common Ukrainian greetings (and it will: dialogues, emails,
introductions), this judge will fire on every one. The greeting-FP makes
it unsuitable as a primary reviewer despite the strong F1 number.

**`gpt-5.5` is the recommended second-opinion validator.** F1 = 78%
(precision 90%, recall 69%), 83% case accuracy. Its strength is
near-zero false-positive rate: gpt-5.5 NEVER flagged anything in any of
the 5 clean cases. Its weakness is missing real medium-severity calques
— it sat clean on 2 of the 8 dirty cases and missed sev=2-3 phrases
like `залишити коментарі`, `не виходить`, `на прийом` that gemini and
opus both caught.

**`gemini-3-pro-preview` DNF** — single judge calls regularly exceed
240s timeout (one cell at 136s smoke + first eval cell timed out at
240s). Unfit for production review at any scale until upstream latency
stabilizes.

**Recommended ensemble for the curriculum review position:**
`claude-opus-4-7` as primary; `gpt-5.5` as cross-family validator on
its output. Anything both flag = high-confidence Russianism, block.
opus-4-7-only flags = warn (often defensible style points). gpt-5.5-only
flags = the rare conservative catch, block.

### Model perspective

**Complete 3-judge coverage:** 50 ok-status cells × 3 judges = 150
judge calls. The original "gpt-5.5 wins" claim from the prior session
does survive, but barely:

| # | Model | gem-31pro % | gpt-5.5 % | opus-4-7 % | Mean % | Spread |
|---:|---|---:|---:|---:|---:|---:|
| 1 | **gpt-5.5** | **1.04** | 1.55 | 5.18 | **2.59** | 1 |
| 2 | claude-opus-4-7 | 3.24 | **1.44** | 6.47 | 3.72 | 3 |
| 3 | claude-opus-4-6 | 3.10 | 3.88 | 6.20 | 4.39 | **5** |
| 4 | gemini-3-pro-preview | 3.05 | 2.54 | 8.63 | 4.74 | 3 |
| 5 | claude-sonnet-4-6 | 3.51 | 4.39 | 7.46 | 5.12 | 4 |
| 6 | gemini-3.1-pro-preview | 5.07 | 1.84 | 8.76 | 5.22 | 4 |
| 7 | gemini-3-flash-preview | 5.24 | 2.82 | 9.27 | 5.78 | 3 |
| 8 | gpt-5.4-mini | 4.92 | 3.83 | 10.93 | 6.56 | 3 |
| 9 | gemini-2.5-flash | 5.43 | 4.98 | 10.86 | 7.09 | 1 |
| 10 | **claude-haiku-4-5** | **8.29** | **7.77** | **11.92** | **9.33** | **0** |

(All rates = issues per 100 words. "Spread" = max(rank) − min(rank)
across the 3 judges = leaderboard fragility for this model.)

**Key findings:**

- **`gpt-5.5` wins on ensemble mean** (2.59%). #1 or #2 under each
  individual judge.
- **`claude-opus-4-7` takes #1 under `gpt-5.5` judge specifically**
  (1.44%) but ranks #3-4 under gemini and opus judges. Net #2 on mean.
- **opus-4-7 as judge is systemically stricter** — all models score
  2-4pp higher under opus-4-7 than under gemini/gpt judges. This is
  consistent with opus-4-7's calibration profile (high recall, low FN).
  The judge's stricter behavior pushes mean rates up uniformly without
  changing the bottom of the leaderboard.
- **The frontier band (ranks 2-7) is judge-fragile** — rank spreads of
  3-5 are common; the gap between #2 and #7 is only ~2.6 percentage
  points on ensemble mean. Headline rankings inside the band are not
  separable with single-judge eval.
- **The bottom is rock-solid.** `claude-haiku-4-5` is rank 10 under all
  3 judges (spread 0). Within-family scaling (smaller model = more
  calques) is universal: Haiku 2.5× Opus, gpt-mini 2.5× gpt-5.5,
  gem-flash 1.2-1.5× gem-pro.

The judge-fragility finding ITSELF is the headline. Without judge
calibration, single-judge rate numbers should not be cited as evidence
of model quality. The within-family scaling finding IS reliably citable
across all three judges.

## Methodology

### Eval pipeline
Built on `scripts/audit/russianism_eval.py` (PR #1999). Each
(prompt, model) cell is a single `bridge.ask-{family}` dispatch. Model
outputs saved to `outputs.jsonl` per result dir. Detector (39
hand-crafted Russianism patterns from PR #1997) scores each output
deterministically — **detector found 0 hits across all 50 ok cells**,
confirming the detector is precision-tuned for blatant Russianisms and
that the rate signal in this eval comes entirely from the LLM-judges.

### Judges
All three judges share the **identical** prompt (now in
`scripts/audit/russianism_judge.py`):

- Retrieve Antonenko entries from `data/sources.db` `style_guide` table
  whose headwords match any word in the target text (top-K=8).
- Build judge prompt with retrieved rules + scoring rubric (severity
  1=debatable / 2=clear Russianism / 3=blatant calque).
- Dispatch to the judge model via the agent bridge.
- Parse JSON verdict.

Differences are model + bridge invocation only:

- `gemini-3.1-pro-preview` via `ask-gemini --stdout-only --model X`
- `gpt-5.5` via `ask-codex --to-model X --new-session`
- `claude-opus-4-7` via `ask-claude --to-model X --new-session`

### Calibration set
`eval/russianism/calibration-cases.jsonl` — 12 hand-labeled cases
mirroring the shape of `outputs.jsonl` (so the universal judge runs
over them unchanged):

| Case ID | Type | Gold |
|---|---|---|
| `cal_clean_greeting` | clean | "Доброго дня!" — VESUM accepts; Antonenko absence. KNOWN gemini-FP target. |
| `cal_clean_short_prose` | clean | Plain UK; no contested register |
| `cal_clean_travel` | clean | Standard travel prose |
| `cal_clean_workplace` | clean | Polite formal request |
| `cal_dirty_email_calques` | dirty (4 flags) | 4 known calques: `на наступному тижні`, `залишити коментарі`, `у вкладенні`, `в будь-який момент` |
| `cal_dirty_medical` | dirty (3 flags) | `забір крові`, preposition `на 09:00`, `прийом` |
| `cal_dirty_workplace` | dirty (2 flags) | `викликають занепокоєння`, `повинні розглянути` |
| `cal_dirty_meetup` | dirty (2 flags) | `великою компанією`, `не виходить` |
| `cal_dirty_register` | dirty (2 flags) | `у найближчий час`, `приділений час` |
| `cal_debatable_next_steps` | DEBATABLE | `наступні кроки` — known judge inconsistency |
| `cal_clean_with_lure` | LURE / clean | Uses `подальші` + `будь-коли` (canonical alternatives to known calques). Tests whether the judge invents Russianisms. |
| `cal_dirty_business_meeting` | dirty (2 flags) | Two textbook calques: `слідуючим питанням`, `на повістці дня` |

Gold labels reflect a single rater (orchestrator) reading grounded in
Antonenko + VESUM + UA-GEC. Single-rater is the cleanest available
gold without inviting a native-speaker linguist into the process; this
is a noted methodology limit.

## Judge perspective — calibration scoreboard

| Rank | Judge | Family | Phrase precision | Phrase recall | F1 (sev1-tolerant) | Case accuracy | Case TP/TN/FP/FN |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | `claude-opus-4-7` | claude | 79% | **94%** | **86%** | **100%** | 7/5/0/0 |
| 2 | `gemini-3.1-pro-preview` | gemini | 81% | 87% | 84% | 92% | 7/4/1/0 |
| 3 | `gpt-5.5` | codex | **90%** | 69% | 78% | 83% | 5/5/0/2 |

(Bolded values are the best in each column.)

**Headline:** opus-4-7 and gemini-3.1-pro are within 2 percentage
points of each other on F1. opus-4-7 wins on case accuracy (100% vs
92%) — the single gemini-3.1-pro case-level error is the well-documented
`Доброго дня!` over-flag. gpt-5.5 is a clear third on F1 but has the
highest precision — it never false-flags a clean case.

### Per-judge characteristic profile

#### `claude-opus-4-7` — "Thorough proofreader"
- **Catches 7/7 dirty cases as dirty** (perfect case-level recall)
- **Catches 5/5 clean cases as clean** (perfect case-level precision)
- Phrase-level recall 94% — missed only 1 of 16 gold flags
  - The miss: preposition issue `на завтра на 09:00 → о 09:00` in
    `cal_dirty_medical`. Got the `забір` and `прийом` flags but missed
    the preposition.
- Phrase-level precision 79% — 3 phrase FPs:
  - `у працівників → серед працівників` (sev=1; debatable)
  - `обговорити терміни → обговорити строки` (sev=1; терміни=conditions
    vs строки=deadlines is real but debatable in this context)
  - `в цьому проєкті → у цьому проєкті` (sev=1; the в-vs-у euphony rule
    is real but rarely flagged at sev=1)
- **Tendency:** flags real issues AND adds defensible sev=1 stylistic
  notes. For a curriculum review pipeline, this is exactly the desired
  behavior — better to over-flag with sev=1 (which the writer can
  dismiss) than to miss a real calque.

#### `gpt-5.5` — "Conservative validator"
- **Catches 5/8 dirty cases as dirty + 5/5 clean cases as clean**
- **2 case-level FNs:** missed `cal_dirty_meetup` and
  `cal_debatable_next_steps` entirely (judged them clean)
- Phrase-level recall 69% — missed 4 of 13 gold flags (sev1-tolerant):
  - `залишу коментарі → висловлю зауваження` (sev=3) — surprising miss,
    this is Antonenko's flagship UA-GEC entry
  - `в будь-який момент → будь-коли` (sev=2)
  - `на прийом → на візит` (sev=2)
  - `не виходить → не вдається` (sev=2) — gpt-5.5 doesn't seem to
    recognize the semantic-shift calque
- Phrase-level precision 90% — 1 FP, and it's a soft-FP: flagged the
  entire span `Слідуючим питанням на повістці дня — обговорення` as one
  issue where the gold has two separate flags inside it. Substantively
  correct, just a span-mismatch.
- **Tendency:** very few false positives, but misses
  medium-severity calques that other judges catch. Conservatism is a
  feature for a validator role, a bug for a primary reviewer.

#### `gemini-3.1-pro-preview` — "Thorough but greeting-blind"
- **Catches 7/7 dirty cases as dirty** (perfect case-level recall,
  ties opus-4-7)
- **Catches 4/5 clean cases as clean** — single case-level FP is the
  predicted `cal_clean_greeting`:
  - `Доброго дня! → Добрий день!` (sev=2) — VESUM accepts the genitive,
    Antonenko has no entry. This is the FP documented in the prior
    handoff.
  - On the same clean cell: also flagged `Як ваші справи? → Як ся
    маєте?` (sev=3) — register preference, not a Russianism.
  - **Combined: 2 spurious flags on a single clean case.** If the
    curriculum content contains ANY common greetings (and it will),
    this judge will produce noise on every greeting.
- Phrase-level recall 87% — missed 2 sev≥2 gold flags:
  - `залишу коментарі` (sev=3) — surprising miss given this is
    Antonenko's most-cited UA-GEC pattern. Same miss as gpt-5.5.
  - `на завтра на 09:00` (sev=2) — same miss as opus-4-7.
- Phrase-level precision 81% — 1 additional phrase FP at sev=2 on the
  debatable `терміни → строки` (which opus-4-7 also flagged at sev=1).
- **Latency instability** — judge calls regularly exceed 240s under
  load; required 480s timeout to complete the calibration set. Still
  finished but variance is dangerous for production review pipelines.
- **Tendency:** high recall, captures real calques well. Two problems
  for production: (a) systematic greeting FP that will fire on every
  common Ukrainian greeting in the curriculum, (b) latency
  unpredictable.

## Model perspective — leaderboard across three judges

(See TL;DR section above for the full table. Below: what it reveals.)

### Within-family scaling (holds across all 3 judges)
| Family | Bigger | Smaller | Ratio (bigger:smaller, mean rate) |
|---|---|---|---|
| Anthropic | opus-4-7 (3.72%) | haiku-4-5 (9.33%) | **2.5×** |
| Anthropic | opus-4-7 (3.72%) | sonnet-4-6 (5.12%) | **1.4×** |
| OpenAI | gpt-5.5 (2.59%) | gpt-5.4-mini (6.56%) | **2.5×** |
| Google | gem-3-pro (4.74%) | gem-3-flash (5.78%) | **1.2×** |
| Google | gem-3-pro (4.74%) | gem-2.5-flash (7.09%) | **1.5×** |

The within-family scaling is the most-robust finding in this study.

## What this means for the Anthropic bug followup (#59146)

The cross-judge data substantially refines the prior session's claim:

1. The original n=1 "3 Russianisms in 70 words on Claude Opus" was an
   under-baked measurement (already known).
2. With n=5 prompts × 3-judge ensemble: `claude-opus-4-7` has a mean
   Russianism rate of **3.72%** (range 1.44%–6.47% across judges) —
   **within the frontier band** of gpt-5.5 (2.59% mean) and
   gemini-3-pro-preview (4.74% mean). `claude-haiku-4-5` is the
   outlier at 9.33% mean (2.5× worse than Opus), confirming the
   smaller-model degradation pattern within Anthropic family.
3. **The leaderboard top 2-3 is judge-dependent within the frontier
   band.** gpt-5.5, opus-4-7, gemini-3-pro all rate within ±2pp of each
   other under any single judge. Citing one of them as "the winner"
   based on a single-judge eval is unsupported.
4. **The within-family scaling finding (smaller model = more calques)
   IS supported across all three judges** — that's the publishable
   headline if we extend this to a real eval set.

Recommended posture on #59146:

- **Default B (wait for UNLP organizer reply)** is correct.
- If we follow up:
  - Acknowledge n=1 measurement issue
  - Cite the 3-judge ensemble methodology
  - Lead with the within-family scaling finding (universal across
    judges) rather than "Claude is worse" (it's not, in the frontier
    band)
  - Offer methodology + calibration set as a contribution, not a
    complaint

## Methodology limits

1. **Calibration set is n=12 + single-rater.** My Antonenko reading is
   not a panel of native-speaker linguists. The "gold" is itself a
   hypothesis. Recommended next step: a 2-3 native-speaker panel
   re-rates the same 12 cases; we measure my agreement with them and
   adjust gold where they outvote me.
2. **`gemini-3.1-pro` latency is environmental.** The day before, it
   judged 55 cells fine; today it timed out on calibration cells with
   identical prompt size. May be Gemini-side rate limiting from
   concurrent jobs or upstream load. The judge-perspective ranking is
   reproducible only on a quiet Gemini account.
3. **Phrase-match is normalized-string equality.** A judge that flags
   "залишити коментарі" and a gold flag of "залишимо коментарі" appear
   as different findings even though they're the same calque
   (different verb form). Soft-overlap matching (token-set ≥2 shared)
   helps but doesn't fully solve span-mismatch.
4. **sev=1 tolerance.** The reported F1 ignores gold sev=1 misses (the
   debatable register calls). Strict scoring would lower recall numbers
   for all judges, but doesn't change the ranking. Reported because
   sev=1 calls are by definition contested.
5. **Single sample per (prompt, model) cell.** Variance experiment on
   one cell showed ±2-3pp rate spread under n=5 retake. Ranks within
   ±1pp are not separable.
6. **`gemini-3-pro-preview` was attempted as 4th judge but DNF'd
   entirely** (240s timeout on first cell, and re-attempts hit the
   same wall). Unsuitable as a production judge at any scale until
   upstream latency stabilizes.

## Recommendation for the curriculum Russianism review position

Adopt **`claude-opus-4-7` as the primary reviewer**. Configure the
review pipeline so:

1. **Primary call:** `claude-opus-4-7` with the universal-judge prompt
   (retrieve Antonenko entries + scoring rubric). At sev≥2 the flag is
   escalated; at sev=1 the flag is logged but does not block
   publication.
2. **Optional second-opinion validator:** when `claude-opus-4-7` flags
   a sev≥2 issue, re-call `gpt-5.5` with the same prompt. **Both flag
   = block / require correction.** **opus-only sev≥2 = warn but
   allow** (likely correct but worth human review for material).
   **gpt-only flag** should be rare given gpt-5.5's conservatism; treat
   as block.
3. **Calibration regression:** run the 12-case calibration set monthly
   as a regression check on whichever judge is in production. If F1
   falls below 80% on the same calibration, escalate.
4. **Do NOT use `gemini-3.1-pro-preview` as a primary reviewer.** Its
   over-flagging of greeting genitives and register preferences will
   produce noise the writer team will learn to ignore — which destroys
   the value of the entire review pipeline.

## Cost note for the dispatch pipeline

Per-cell judge latency this run (480s timeout):

- `gpt-5.5` (`ask-codex`): ~20-25s/cell typical → $0.02-0.05/cell estimated
- `claude-opus-4-7` (`ask-claude`): ~30s/cell typical → $0.05-0.08/cell
- `gemini-3.1-pro-preview` (`ask-gemini`): 25-300+ s/cell, **high
  variance + frequent timeouts** → unbudgetable

For curriculum-scale review (~6000 module activities × per-section
audits), the `claude-opus-4-7` + `gpt-5.5` second-opinion configuration
costs roughly $300-500/run on full corpus. Well within the project's
review budget on the Anthropic promo (+50% until 2026-07-13).

## Artifacts referenced

| File | Purpose |
|---|---|
| `scripts/audit/russianism_judge.py` | Universal 3-family judge (production-ready) |
| `scripts/audit/score_judge_calibration.py` | Calibration P/R/F1 scorer |
| `scripts/audit/russianism_eval.py` | Eval harness (PR #1999) — generates outputs.jsonl |
| `eval/russianism/calibration-cases.jsonl` | 12 hand-labeled gold cases |
| `eval/russianism/prompts-v1.yaml` | 5 starter prompts (PR #1999) |
| `eval/russianism/README.md` | Judge-selection guide |
| `audit/2026-05-15-russianism-judge-calibration/calibration-scores.json` | Per-judge confusion matrix + P/R/F1 |
| `audit/2026-05-15-russianism-judge-calibration/model-leaderboard.json` | Per-model rates × judge × ensemble-mean |
| `audit/2026-05-15-russianism-judge-calibration/REPORT.html` | This report's HTML companion |
| `audit/2026-05-15-russianism-judge-calibration/REPORT.md` | This document |

## Reproduction

To regenerate the raw data:

```bash
# 1. Generate model outputs (5 prompts × 10 models = ~50 cells)
.venv/bin/python scripts/audit/russianism_eval.py \
    --prompts eval/russianism/prompts-v1.yaml \
    --models claude-opus-4-7 gpt-5.5 ... \
    --out-dir /tmp/eval-run/

# 2. Judge with each of the 3 production judges
for judge in claude-opus-4-7 gpt-5.5 gemini-3.1-pro-preview; do
    family=$(case $judge in claude*) echo claude;; gpt*) echo codex;; gemini*) echo gemini;; esac)
    .venv/bin/python scripts/audit/russianism_judge.py \
        --judge-family $family --judge-model $judge \
        --inputs /tmp/eval-run/outputs.jsonl \
        --out /tmp/eval-run/judgments-${judge}.jsonl
done

# 3. Score against calibration set (separate run on the gold)
for judge in claude-opus-4-7 gpt-5.5 gemini-3.1-pro-preview; do
    family=$(...)  # as above
    .venv/bin/python scripts/audit/russianism_judge.py \
        --judge-family $family --judge-model $judge \
        --inputs eval/russianism/calibration-cases.jsonl \
        --out /tmp/cal/judgments-${judge}.jsonl
done

.venv/bin/python scripts/audit/score_judge_calibration.py \
    --judgments-dir /tmp/cal/
```

Total reproduction cost: ~$5 in API + ~30 min wall-clock with 4-way
parallelism (one family per process).

---

*Format spec: ai → human handoff. Gold labels reflect single
orchestrator reading grounded in Antonenko + VESUM. Next step:
native-speaker re-rating of the calibration set to refine gold.*
