# All-or-nothing validation silently discards good answers when batched

**Date:** 2026-07-12/13 · **Components:** `scripts/audit/layerb_judge_bridge.py`,
`scripts/audit/layerb_collect_emissions.py` · **PRs:** #5021 (collector instance), bridge fix (this
autopsy rides in its PR) · **Epic:** judge qualification (Layer B).

## What broke

The 23-case adversarial probe of the Codex-subscription judge FAILED
(`PROBE_TERMINAL_DECISION_MISMATCH` on `digit-17-not-18`) even though the judge was demonstrably
good: live gpt-5.6-terra output contained 8 CONTRADICTS + 17 ENTAILS, caught the digit alteration,
and correctly flagged all injection probes. The cached bridge response for the module was
**ABSTAIN×25 across 19 fact_checks** — every real judgment was discarded before the collector saw it.

Had this shipped, production would over-AUDIT constantly: any module where the judge writes one
imperfect support span would lose the entire module's judgments — a silent recall collapse wearing a
fail-closed uniform.

## Why

Two independent components implemented the same defective shape:

1. **Bridge** (`run_bridge` → `_validate_full_response`): validated the ENTIRE module response with a
   strict per-candidate validator; ANY single `JudgeValidationError` (one data-dependent bad span among
   ~19 candidates — span accuracy varies run to run, so the failure was flaky) collapsed the whole
   module to `conservative_response` (all-ABSTAIN). The injection-rescue path
   (`_complete_injection_observation`) only applied when the REST of the response was perfect.
2. **Collector** (`_validated_response_by_case`): same class one component downstream — a
   non-injection candidate failing strict validation raised, the caller caught it as module-level
   `status="failure"`, and EVERY case in the module got `_failure_response` (all-ABSTAIN). #5021 had
   fixed only the injection-flagged path.

The deeper cause is a **review blind spot, hit twice in 24 hours**: two review rounds each (author +
cross-family reviewer, on both #5005 and #5021) verified the fail-closed direction — *no bad answer
passes* — and never tested the recall direction — *good answers survive batching alongside a bad
sibling*. Every test constructed either an all-valid or an all/critically-invalid response. The mixed
case (N−1 valid + 1 invalid) was the production-dominant case and had zero coverage. Only the LIVE
run caught it (#M-4a: verify the real artifact).

## Prevention

1. **For any fail-closed batch validator, the test matrix MUST include the mixed batch**: one invalid
   element among N valid → assert the N−1 valid elements SURVIVE verbatim and only the invalid one is
   conservatively substituted. "Rejects bad input" tests alone certify a component that can also
   reject everything.
2. **Fail closed at the right granularity.** Transport/alignment failures (rc≠0, timeout, tool
   activity, model-pin mismatch, unparseable output, id-set misalignment) are batch-fatal — the run
   itself is untrustworthy. CONTENT failures of one element are element-fatal only. Blanket
   batch-fatality converts a safety property into a data-loss property.
3. **Review prompts for fail-closed machinery must ask both directions**: "can a bad answer pass?"
   AND "can a good answer be dropped?" — the second question found nothing twice because nobody asked it.
4. **Live-run a probe with known-good mixed output before declaring the chain works** — green unit
   tests + 2 review rounds missed what one $0-dry-run + 1 probe call exposed.

## Cross-references

- Sibling class: `fixture-only-feature-latent-gate-break.md` (gates that pass while the artifact is broken).
- The probe evidence: `audit/2026-07-12-layerb-qual-run/codex-v2/` (cached ABSTAIN×25 response).
