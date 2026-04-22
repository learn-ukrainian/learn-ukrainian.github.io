# Gemini brief: systemic writer-gap pattern analysis across all 20 bakeoff reviews

**Task ID:** `gemini-peak-bakeoff-patterns`
**Worktree:** `.worktrees/gemini-peak-bakeoff-patterns`
**Branch:** `gemini/peak-bakeoff-patterns`
**Mode:** `--mode workspace-write` (docs only, no code)
**Model:** `gemini-3.1-pro-preview`

## Why you're running now

14:00–20:00 CET peak window. Krisztian is AFK. Claude's main session is stopped (expensive during peak). A separate headless Claude dispatch (`claude-1370-writer-harden`) is working on hardening `scripts/build/phases/v6-write.md` against the #1 complaint surfaced by the 2026-04-22 writer bakeoff (activity_hint item counts).

**Your role:** surface the OTHER gaps we might be missing. If #1370's hardening only catches activity-count but the bakeoff reviews flag 2-3 more systemic patterns, Phase 3's 124-module build will still underperform. Your analysis becomes input for a potential #1370 follow-up PR or for a separate hardening ticket.

## Worktree setup (mandatory — `.claude/rules/delegate-must-use-worktree.md`)

```bash
git worktree add -b gemini/peak-bakeoff-patterns .worktrees/gemini-peak-bakeoff-patterns
cd .worktrees/gemini-peak-bakeoff-patterns
```

Do NOT branch in the main checkout.

## What to read

All 20 review YAMLs in:
```
experiments/writer-bakeoff-2026-04-22/reviews/
├── codex-on-gemini-flash.yaml
├── codex-on-gemini-pro.yaml
├── codex-on-opus.yaml
├── codex-on-sonnet.yaml
├── gemini-flash-on-codex.yaml
├── gemini-flash-on-gemini-pro.yaml
├── gemini-flash-on-opus.yaml
├── gemini-flash-on-sonnet.yaml
├── gemini-pro-on-codex.yaml
├── gemini-pro-on-gemini-flash.yaml
├── gemini-pro-on-opus.yaml
├── gemini-pro-on-sonnet.yaml
├── opus-on-codex.yaml
├── opus-on-gemini-flash.yaml
├── opus-on-gemini-pro.yaml
├── opus-on-sonnet.yaml
├── sonnet-on-codex.yaml
├── sonnet-on-gemini-flash.yaml
├── sonnet-on-gemini-pro.yaml
├── sonnet-on-opus.yaml
└── _aggregate.json
```

Each YAML has six-axis scoring (`linguistic_correctness`, `pedagogical_accuracy`, `decodability_a1`, `plan_adherence`, `register_naturalness`, `honesty`), with `evidence` blocks and `missing_from_plan` / `extra_not_in_plan` lists.

Also read for context:
- `docs/experiments/2026-04-22-writer-bakeoff-results.md` — user-facing writeup
- `scripts/build/phases/v6-write.md` — current writer prompt (v6)
- `experiments/writer-bakeoff-2026-04-22/reviews/_aggregate.json` — per-writer + per-reviewer statistics

## Your task

Cross-reference all 20 review YAMLs. Produce a ranked list of SYSTEMIC gaps (patterns that appear in ≥3 reviews across different writer/reviewer combinations). Exclude idiosyncratic one-off complaints.

**Known gap (do NOT re-surface as a finding — already in flight via #1370):**
- Activity-count contract: writers produce fewer `activity_hints` items than plan spec. Dominant complaint, being addressed.

**What we WANT to know:**
- What are the #2, #3, #4, #5 gaps? Rank by breadth (how many reviews mention) × severity (how badly it tanks the relevant axis).
- For each gap:
  - Name it concisely
  - Cite 3+ specific evidence quotes from different review YAMLs (file + line if helpful)
  - Which axis it primarily damages
  - Diagnose: is this a prompt gap, a plan gap, a model-pre-training contamination issue, or something else?
  - Propose a concrete prompt-hardening direction (1–2 sentences)

**The "honesty" axis is your sharpest lens.** Per `_aggregate.json`, every writer scored low on `honesty` (Opus 6.75, Sonnet 5.25, Gemini-flash 4.5). Review the honesty-axis evidence across all 20 reviews and extract the patterns. This is almost certainly one of the top gaps.

**Look for patterns by reviewer model too.** Codex-as-reviewer has mean-evidence-entries 22.5 (very detailed); Gemini-flash-as-reviewer 9.5 (thinner). Codex findings weight higher for systemic analysis.

## Acceptance criteria

Deliverable: **`docs/experiments/2026-04-22-writer-bakeoff-patterns.md`** with:

1. **Executive summary** — ranked list of top 5 systemic gaps, one line each
2. **Per-gap section** (one per top gap):
   - Name + one-line definition
   - Breadth: reviews mentioning / 20
   - Severity: avg axis-score impact
   - Evidence: 3+ quotes with provenance
   - Diagnosis: root cause category
   - Prompt-hardening direction
3. **Anti-patterns we can NOT fix via prompt hardening** — things that need plan changes or corpus work (flag clearly so #1370 doesn't over-promise)
4. **Open questions** — anything the review data doesn't resolve and needs a human call

Length target: 800–1500 words. Dense analysis, not filler. Quote evidence sparingly but exactly.

## Do NOT

- Do NOT edit `scripts/build/phases/v6-write.md` — #1370 headless Claude is doing that in a parallel worktree; conflict risk
- Do NOT re-litigate the activity-count gap (already in flight)
- Do NOT propose changes to plan YAML structure — out of scope
- Do NOT branch in the main checkout
- Do NOT fabricate evidence quotes — every quote must be literally present in a review YAML

## Adversarial review before merge

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex \
  "Adversarial review of bakeoff pattern analysis. Read the doc in this branch. Verify each cited quote exists in the referenced review YAML. Flag any fabrications or over-claims." \
  --task-id gemini-peak-patterns-review
```

Address findings. If Codex flags fabricated quotes, correct them BEFORE opening the PR.

## Deliverables

1. Single commit on branch `gemini/peak-bakeoff-patterns`:
   - `docs(experiments): writer-bakeoff systemic gaps beyond activity-count`
2. PR → main: `docs: writer-bakeoff pattern analysis — 5 systemic gaps ranked`
3. PR body: brief description + the ranked list + link to doc
4. Codex review completed, findings addressed

## Time estimate

60–90 min. Most of the time is reading and cross-referencing.

## Context for Krisztian's review (post-20:00 CET)

When Krisztian reviews, he wants to quickly:
- See the ranked list
- Spot-check 1-2 cited quotes for honesty
- Decide which gaps to fold into #1370 follow-up vs. a separate issue

Write for that reading mode.
