# 2026-05-05 — CoT scaffolding + Tier-1 verification pilot guide (#1673 + #1661)

This guide describes how to run the 3-module ablation pilot for the V7
prompt-discipline diff that combines:

- **#1673** — chain-of-thought reasoning checklist (writer + reviewer)
- **#1661** — Tier-1 verification discipline (writer) and audit (reviewer)

The diff itself is in PR (link in commit body). Until the pilot runs and
the user signs off, the PR stays **DRAFT**. Per memory rule
`PROMPT-ABLATION DISCIPLINE`, pipeline-prompt changes pilot on ≥ 3 seeded
modules before any `--range` rollout.

## What the prompts now require

**Writer (`scripts/build/phases/linear-write.md`):**

1. Reasoning checklist (CoT, 4 steps): word-budget per section, plan-vocab
   terms, register check, teaching sequence.
2. Tier-1 verification discipline (5 steps): VESUM word-verification,
   modern Ukrainian default, source-citation discipline, quote-attribution
   discipline, end-of-output gate.

**Reviewer (`scripts/build/phases/linear-review-dim.md`):**

1. Per-dim CoT (4 steps): list 3 verbatim quotes, map to rubric, aggregate
   score, verdict.
2. Tier-1 verification audit (5 items A–E): source-attribution audit,
   quote verification, sovietization flag (decolonization / naturalness),
   modern Ukrainian guard, reinforce rule #6.

## Three modules to pilot

Pick three seeded modules across levels so the pilot covers different
content types (vocabulary lesson, grammar lesson, advanced/grammar).
The `tests/test_prompt_cot_tier1_scaffolding.py` ablation already verifies
these three plans render against the new templates with no template-token
or placeholder failures, so the writer call will not crash on a malformed
prompt:

| Level | Slug | Plan | Notes |
|-------|------|------|-------|
| a1 | `my-morning` | `curriculum/l2-uk-en/plans/a1/my-morning.yaml` | A1 reflexive verbs, prior round-3.5 baseline exists |
| a2 | `a2-bridge` | `curriculum/l2-uk-en/plans/a2/a2-bridge.yaml` | A2 review/bridge module |
| b1 | `adjectives-comparative` | `curriculum/l2-uk-en/plans/b1/adjectives-comparative.yaml` | B1 grammar lesson |

Substitute different slugs if any of these have un-shippable plans by the
time the pilot runs — the only requirement is each plan passes
`linear_pipeline.plan_check` AND has a prior baseline output for diffing.

## Run the pilot

For each module above, one at a time, run the V7 build with the writer
backend you want to evaluate (default `claude-tools`):

```bash
.venv/bin/python scripts/build/v7_build.py a1 my-morning \
    --writer claude-tools \
    --out /tmp/v7-pilot/a1-my-morning
```

```bash
.venv/bin/python scripts/build/v7_build.py a2 a2-bridge \
    --writer claude-tools \
    --out /tmp/v7-pilot/a2-a2-bridge
```

```bash
.venv/bin/python scripts/build/v7_build.py b1 adjectives-comparative \
    --writer claude-tools \
    --out /tmp/v7-pilot/b1-adjectives-comparative
```

`--out` keeps the pilot artifacts out of `curriculum/` so they do not
overwrite the live tree. The writer prompt, knowledge packet, generated
artifacts, Python QG, and LLM QG report all land under that directory.

> Per memory rule **BATCH COMMANDS — NEVER RUN, ONLY SUGGEST** the user
> runs the builds — Claude does not. This guide is documentation. If
> Claude is asked to run a single-module build for verification it is
> still **one slug at a time**, never `--range`.

For the `gemini-tools` cross-family run (recommended for the cross-review
hook in the PR body):

```bash
.venv/bin/python scripts/build/v7_build.py a1 my-morning \
    --writer gemini-tools \
    --out /tmp/v7-pilot-gemini/a1-my-morning
```

## Compare and score

For each pilot module:

1. **Compare output.** If a `<slug>.bak.md` baseline exists in the live
   curriculum tree, diff `module.md` from the pilot vs. the baseline.
   The diff should show: more verified example words, fewer or no
   ungroundable source citations, no fused literary quotes, and per-section
   word counts matching the contract budgets the writer reasoned out
   in step 1 of CoT.
2. **Re-run the per-dim reviewer** on the pilot artifacts (already part of
   `v7_build.py`'s LLM QG step). Compare per-dim scores and FLAG strings
   against the pre-CoT/Tier-1 baseline. Expect (a) decolonization +
   naturalness scores to either rise OR drop with FLAG strings naming the
   specific failures, and (b) `evidence` fields to be verbatim quotes from
   the actual artifacts (not paraphrased summaries) — that's the rule #6
   reinforcement.
3. **Capture findings.** Write a short pilot report under
   `docs/reports/2026-05-05-cot-tier1-pilot-<slug>.md` with the
   before/after diff and the per-dim score deltas.

## User-facing checklist (to sign off the DRAFT PR)

- [ ] Did fabricated source citations drop or surface as
      `unverified citation` FLAG strings?
- [ ] Did fused / non-existent literary quotes drop or surface as
      `fabricated quote` FLAG strings?
- [ ] Did per-section word counts hold within the ±10% contract budget
      the CoT block forces the writer to commit to?
- [ ] Did per-dim reviews cite specific verbatim quotes rather than
      paraphrased summaries?
- [ ] Did the writer leave `<!-- VERIFY: lemma "X" not in VESUM -->`
      markers when it could not ground a candidate, instead of silently
      substituting a confabulated alternative?
- [ ] (Cross-family) Did Gemini-as-writer behave the same way the
      Claude-as-writer pilot did, on the same slug?

If all six check out across the three modules, the PR can leave DRAFT and
go to merge review. If any of the six fail on ≥ 1 module, write the
pilot report, add a follow-up issue (or amend this brief), and keep the
PR DRAFT.

## After the pilot — follow-up

EPIC #1657 Phase 2 introduces single-call MCP primitives `verify_quote`,
`verify_source_attribution`, `check_modern_form`. When that lands, the
discipline blocks in this PR collapse from multi-tool composition to
1-tool calls. That simplification PR should reference this one and remove
the now-redundant tool-name lists from both prompts. Bounded throwaway
risk on the prompt blocks: ~50 lines.

## Related

- Parent EPIC: #1657 — verification-layer architecture
- Tier ordering: `docs/session-state/2026-05-04-tools-before-a1-20.md`
- Сибір case study: search prior session handoffs for "fabricated citations"
- Decision (writer-choice still open): `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3
