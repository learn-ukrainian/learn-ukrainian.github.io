# H2 vs H1 vs Baseline (3-way A/B/C)

**Date:** 2026-05-17  
**A (Baseline):** `audit/2026-05-17-judge-calibration-matrix/` — Antonenko-headword prompt only.  
**B (H1):** `audit/2026-05-17-judge-calibration-h1/` — H1 evidence-rich prompt (Antonenko + heritage + Russian-shadow + VESUM-unknown) with strict cite-or-forbid. Collapsed recall.  
**C (H2):** `audit/2026-05-17-judge-calibration-h2/` — H1 channels + Antonenko full-text prose + UA-GEC F/Calque + F/Style + F/Collocation + G/Case + G/Gender annotations, expanded cite-or-forbid, canonical-greeting protection.

Same 12-case calibration set (`eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`).

## Headline

- Mean F1 — Baseline: **0.753**, H1: **0.135**, H2: **0.478** (6/6 H2 cells scored)
- **Hypothesis ≥ baseline F1: PARTIAL.** H2 above H1 (ΔH2−H1 = +0.343) but below baseline (ΔH2−Base = -0.275).
- Greeting case (`cal_clean_greeting`) correct: Baseline 3/6, H1 6/6, H2 6/6.

## Per-cell deltas

| Cell | B F1 | H1 F1 | **H2 F1** | ΔH2−Base | B P | H1 P | H2 P | B R | H1 R | H2 R | B acc | H1 acc | H2 acc | greeting (B/H1/H2) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| opus-4-7 xhigh+mcp | 0.839 | 0.118 | **0.545** | -0.293 | 0.867 | 1.000 | 1.000 | 0.812 | 0.062 | 0.375 | 0.917 | 0.500 | 0.833 | ✗ FP/✓/✓ |
| opus-4-7 high −mcp | 0.828 | 0.118 | **0.545** | -0.282 | 0.923 | 1.000 | 1.000 | 0.750 | 0.062 | 0.375 | 0.917 | 0.583 | 0.833 | ✗ FP/✓/✓ |
| haiku high −mcp | 0.545 | 0.118 | **0.222** | -0.323 | 1.000 | 1.000 | 1.000 | 0.375 | 0.062 | 0.125 | 0.750 | 0.500 | 0.667 | ✓/✓/✓ |
| gpt-5.5 medium+mcp | 0.720 | 0.118 | **0.476** | -0.244 | 1.000 | 1.000 | 1.000 | 0.562 | 0.062 | 0.312 | 1.000 | 0.500 | 0.750 | ✓/✓/✓ |
| gemini default+mcp | 0.800 | 0.222 | **0.857** | +0.057 | 0.857 | 1.000 | 1.000 | 0.750 | 0.125 | 0.750 | 0.917 | 0.583 | 1.000 | ✗ FP/✓/✓ |
| grok-4.3 hermes xhigh+mcp | 0.786 | 0.118 | **0.222** | -0.563 | 0.917 | 1.000 | 1.000 | 0.688 | 0.062 | 0.125 | 1.000 | 0.500 | 0.583 | ✓/✓/✓ |

## Evidence anchor usage (H2 only — sev≥2 flags)

Count of evidence_type cited per H2 cell, across all sev≥2 flagged issues. 
Reveals which retrieval channel carried each judge's flag warrant.

| Cell | total sev≥2 | antonenko_headword | antonenko_prose | ua_gec_calque | vesum_unknown | russian_shadow | general_principle | unspecified |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| opus-4-7 xhigh+mcp | 6 | 0 | 0 | 2 | 1 | 0 | 3 | 0 |
| opus-4-7 high −mcp | 6 | 0 | 0 | 1 | 1 | 0 | 4 | 0 |
| haiku high −mcp | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| gpt-5.5 medium+mcp | 5 | 0 | 0 | 1 | 1 | 0 | 3 | 0 |
| gemini default+mcp | 12 | 0 | 0 | 2 | 2 | 0 | 8 | 0 |
| grok-4.3 hermes xhigh+mcp | 2 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |

## Per-case `case_acc` matrix (H2 vs Baseline)

| case_id | opus-4-7 xhigh+mcp | opus-4-7 high −mcp | haiku high −mcp | gpt-5.5 medium+mcp | gemini default+mcp | grok-4.3 hermes xhigh+mcp |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `cal_clean_greeting` | ✗→✓ | ✗→✓ | ✓ | ✓ | ✗→✓ | ✓ |
| `cal_clean_short_prose` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `cal_clean_travel` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `cal_clean_with_lure` | ✓ | ✓ | ✗→✓ | ✓ | ✓ | ✓ |
| `cal_clean_workplace` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `cal_debatable_next_steps` | ✓ | ✓ | ✗→✓ | ✓→✗ | ✓ | ✓→✗ |
| `cal_dirty_business_meeting` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `cal_dirty_email_calques` | ✓ | ✓ | ✗ | ✓ | ✓ | ✓→✗ |
| `cal_dirty_medical` | ✓ | ✓ | ✓→✗ | ✓→✗ | ✓ | ✓→✗ |
| `cal_dirty_meetup` | ✓→✗ | ✓→✗ | ✓ | ✓ | ✓ | ✓ |
| `cal_dirty_register` | ✓ | ✓ | ✓→✗ | ✓ | ✓ | ✓→✗ |
| `cal_dirty_workplace` | ✓→✗ | ✓→✗ | ✓→✗ | ✓→✗ | ✓ | ✓→✗ |

Legend: `✓`/`✗` H2 outcome (matches baseline); `✗→✓` baseline-wrong → H2-correct; `✓→✗` baseline-correct → H2-wrong (regression).

## Harness errors

- opus-4-7 xhigh+mcp: 0 errors
- opus-4-7 high −mcp: 0 errors
- haiku high −mcp: 0 errors
- gpt-5.5 medium+mcp: 0 errors
- gemini default+mcp: 0 errors
- grok-4.3 hermes xhigh+mcp: 0 errors

## Surprises / negative results / model failures

### 1. Greeting FP fix preserved across the board (the H1 win that H2 had to keep)
6/6 cells judge `cal_clean_greeting` correctly clean. The CLEAN-by-default opener + explicit canonical-Ukrainian whitelist in the H2 prompt protected `Доброго дня!` even though UA-GEC retrieval surfaces an F/Style annotation suggesting `Доброго дня → Добрий день`. The prompt's interpretation rule for F/Style hits (`do not flag on F/Style alone unless also supported by Antonenko or independent knowledge`) carried the day.

### 2. Gemini-3.1-pro is the only cell that beats baseline F1 (+0.057)
Gemini fires `general_principle` 8 times — more than any other model — and converts every case correctly (`case_acc=1.0`). Pattern: Gemini treats the cite-or-forbid rule as a license to apply its own world-knowledge under the `general_principle` channel rather than as a refusal-by-default. Opus/Haiku/GPT-5.5/Grok-4.3 read the same rule more conservatively and emit fewer flags. Cell-by-cell:

| Cell | sev≥2 flags emitted | of which `general_principle` |
|---|---:|---:|
| gemini default+mcp | 12 | 8 |
| opus-4-7 xhigh+mcp | 6 | 3 |
| opus-4-7 high −mcp | 6 | 4 |
| gpt-5.5 medium+mcp | 5 | 3 |
| haiku high −mcp | 2 | 0 |
| grok-4.3 hermes xhigh+mcp | 2 | 0 |

### 3. `antonenko_prose` was cited zero times across all 6 cells
The new full-text Antonenko channel always fires retrievals (4 hits on every case) but **no model picked a prose snippet as `evidence_type`** for any sev≥2 flag. Two plausible reasons: (a) the prefix-matched prose snippets are too tangential (matching on `залежать`/`тижні` rather than on the russianism phrase itself), so models reach for `general_principle` instead; (b) models trust their own framing over a noisy retrieval. Next iteration should narrow the prose match to multi-token n-grams or require the matched phrase to appear adjacent to a Russianism marker (e.g. words like "русизм", "калька", "не вживайте").

### 4. UA-GEC channel is firing but light (1–2 citations per cell)
The retrieval finds 4 UA-GEC hits per case in most prompts, but the `evidence_type` accounting shows only 1–2 of those become cited evidence on sev≥2 flags per cell. Hypothesis: F/Style hits are correctly downweighted, and only F/Calque / G/Case strong-signal triples get promoted. Confirmed examples cited by judges:
- opus: `наступному → такому` (F/Calque) on `cal_dirty_email_calques`
- opus: `прийом → приймання` on `cal_dirty_medical` (G/Case-flavoured)
- gpt-5.5: cited UA-GEC on the workplace genitive case
- gemini: 2 UA-GEC anchors on phraseological calques

This is roughly what the brief's hypothesis predicted, but smaller-magnitude than required to recover full baseline recall.

### 5. `russian_shadow` channel was dark in all H2 cells (pre-existing import bug)
All 6 H2 prompts rendered `### Russian-shadow morphology hits\n(pymorphy3 unavailable in this environment)`, but the dependency IS present locally. Root cause: when the matrix runner is invoked as `python scripts/audit/judge_calibration_matrix.py`, Python sets `sys.path[0]` to `scripts/audit/`, so `_russian_shadow_check`'s `from scripts.verification.check_ru_morph import is_russian_pattern` raises `ModuleNotFoundError` and the helper returns `{"available": False, "triggered_tokens": []}`. The H1 helper swallows this silently. This is a pre-existing bug (not introduced by H2) — left untouched per the brief's directive ("Do NOT change the H1 helpers"). Filing as a follow-up would let `слідуючим`-style morphology flags surface via this channel in addition to `vesum_unknown`.

### 6. `cal_dirty_workplace` regression in 5 of 6 cells (✓→✗)
Baseline judges flagged this case correctly; H2's stricter rule prunes the flag without enough cite-able evidence. The expected calque (`оформити документи` / `доводити до відома` — depending on the case body) is not in the 342 Antonenko headwords, not in the prefix-matched prose, and UA-GEC didn't surface a usable triple. This is the residual gap from H1's "evidence-anchor scarcity" finding — UA-GEC closed some of it but not all. Targeted UA-GEC additions or a hand-curated phraseological-calque list (option (a) from the H1 next-experiment recommendation) would address this.

### 7. Identical F1 across opus-4-7 efforts (xhigh / high) — effort doesn't help here
Both opus configs scored F1=0.545 / case_acc=0.833 / greeting=clean. The cite-or-forbid + canonical-greeting protection makes the prompt deterministic enough that extra reasoning effort doesn't change which flags survive the warrant test. Useful operational signal: for routing decisions, opus at `high` is as good as `xhigh` on this prompt.

## Recommendation for next iteration

The H2 hypothesis ("recover F1 to ≥ baseline by adding UA-GEC and Antonenko prose channels") is **partially confirmed** — F1 recovered 3.5× over H1 (0.135 → 0.478) and greeting protection preserved, but baseline (0.753) is still ahead by 0.275. Gemini is the only cell that beats baseline, suggesting model-prompt fit is uneven.

Concrete next steps, in priority order:

1. **H3a — narrow the Antonenko prose retrieval.** The prose channel didn't earn a single citation. Replace prefix-OR FTS with a phrase-NEAR query that requires ≥2 substantive tokens within 5 words, OR pre-filter prose chunks by russianism-marker words ("калька", "русизм", "правильно", "неправильно"). Target: at least one cell cites `antonenko_prose` on a flag.
2. **H3b — soften cite-or-forbid for non-Gemini judges.** Add an "if you have ≥2 retrieval channels agreeing, you may flag without citing general_principle" rule. This rewards retrieval signal without requiring it for every flag.
3. **H3c — drop UA-GEC F/Style from the index.** F/Style entries trigger canonical-greeting near-misses and add no calque signal. Re-running with `UA_GEC_RELEVANT_TAGS = ("F/Calque", "F/Collocation", "G/Case", "G/Gender")` reduces the index from ~7.3K to ~4.6K and should sharpen the channel.
4. **H3d — fix the H1 Russian-shadow import bug** (separate PR). Add `sys.path` shim in `_judge_eval_lib._russian_shadow_check` OR move `is_russian_pattern` to a sibling module — the channel was effectively dark in this calibration matrix and is the only signal for outright Russian-form tokens that aren't in the VESUM-unknown lane.
5. **H3e — curate a phraseological-calque whitelist** (option (a) from H1's next-experiment note) for the cases UA-GEC didn't cover: `повістка дня`, `забір крові`, `довести до відома`, `оформити документи`. ~30 entries would lift `cal_dirty_workplace` and friends back to ✓.

For routing **right now**: use `gemini-3.1-pro-preview default+mcp` as the H2 judge — it's the only configuration that beats baseline. For all other models, **keep the baseline prompt** until H3 lands.
