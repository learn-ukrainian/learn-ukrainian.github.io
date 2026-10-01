# Decision: Layer B entailment gate shelved — no cutover

- **ID:** dec-016
- **Date:** 2026-10-01
- **Expires:** 2026-12-30
- **Status:** active (operator decision 2026-10-01)
- **Scope:** pipeline
- **Issue:** #8305
- **Related:** #4797

## Decision

1. **No cutover.** The Layer B entailment gate is shelved. It is not armed, flipped or promoted from shadow to canonical scoring.
2. **The shadow-tier attestation expires on 2026-10-12, on purpose.** It is not renewed.
3. **No code or gate change accompanies this decision.** Existing behavior is untouched; this record only fixes the plan of record.

## Reason

The infrastructure backlog takes priority. A cutover would first need a cutover-tier qualification and an explicit operator go, and neither is scheduled.

## Preserved

- The design: [`layerb-entailment-gate-design.md`](../projects/qg-quality-gate/layerb-entailment-gate-design.md) (now bannered as shelved).
- The public 23-case adversarial gold under `tests/fixtures/curriculum_qg/layer_b_adversarial/`.

## Lapses

- The shadow-tier attestation, on 2026-10-12.

## Revisit condition

A new operator decision. A cutover-tier qualification would be required again; the lapsed shadow-tier attestation does not carry over.

## Alternatives Considered

- **Proceed to cutover now:** Rejected. It would compete with the infrastructure backlog and has no cutover-tier qualification or operator go.
- **Renew the shadow-tier attestation:** Rejected. Renewal spends effort on a gate that is not being cut over.

## Open actions

Open custody actions are tracked in section 2 of #8305.
