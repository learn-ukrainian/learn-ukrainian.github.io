# Antonym and homonym residual taxonomy (#6338)

Curated antonym and homonym pairs are not coverage merely because they occur
in a YAML file. A pair is emitted only when both source legs, its authored
frame, and its resulting item satisfy the production builder. The audit below
uses that same selector and builder; it does not create lexemes, assign CEFR,
or relax a frame to improve a count.

```bash
.venv/bin/python -m scripts.audit.relation_residual_audit \
  --relation antonym --vesum-db <vesum-db> --out <antonym-residual.json>
.venv/bin/python -m scripts.audit.relation_residual_audit \
  --relation homonym --vesum-db <vesum-db> --out <homonym-residual.json>
```

The `summary` is a stable count view. The optional `--out` file is the named
per-pair ledger used to decide follow-up work; it is local evidence and must
not be committed as a generated practice artifact.

## Pair outcomes

| Outcome | Meaning | Honest next action |
| --- | --- | --- |
| `pair_invalid` | Required pair fields, citations, or frames are malformed. | Repair the curated source record with evidence. |
| `no_valid_frames` | The pair has no frame that passes the production frame validator. | Author or review a source-backed frame; do not emit a bare pair. |
| `missing_leg` | At least one leg cannot enter the selected practice pool. | Read its leg status; never invent or force-admit it. |
| `frame_answer_unresolved` | Both legs were selected, but no generated frame item survived production validation. | Correct the authored frame or its source evidence. |
| `emitted` | At least one public item passed the same builder and validators as a deck build. | Count it as actual emitted coverage. |

## Leg statuses

`missing_leg` carries `legA` and `legB`, so a follow-up can distinguish these
causes instead of treating all missing pairs as one opaque number:

| Status | Meaning | Boundary |
| --- | --- | --- |
| `missing_from_atlas` | No matching Atlas entry exists. | Atlas intake, not practice generation. |
| `not_lexeme_entry` | The matched Atlas row is not an eligible lexeme record. | Preserve the record type; do not coerce it to a lexeme. |
| `ineligible` | The entry failed an existing practice-admission gate. The report keeps its exact `reason`. | Resolve the cited gate with source evidence; do not flip admission. |
| `eligible_not_selected` | The row is eligible but absent from this selected pool. | Inspect pool configuration and priority evidence. |
| `selected` | The leg reached the pool. `cefr_status` says `anchored` or `uses_b1_fallback`. | Continue to the frame/item outcome; do not call this emitted coverage. |

`uses_b1_fallback` is a named CEFR residual. It records the existing curated
relation fallback rather than silently presenting an unanchored leg as a
curriculum placement. A missing curriculum anchor remains an `ineligible`
reason when the admission gate rejects it.

## Synonym placement residual

The synonym mode has a separate, intentional placement floor. An approved
synonym pair is not an A1 card, and it is B1+ by default even if both legs are
already present at A1 or A2. This is a delivery policy for meaning-sensitive
contrast, not a failed relation emission.

The named residual is therefore `below_b1_floor`: the pair is approved and
otherwise buildable, but is unavailable in A1/A2 because its availability is
floored at B1. It must not be counted as a missing pair or as an A1/A2
generation defect. A pair may move only to A2 when both legs are A2 and the
curated verdict has a valid `a2Exception: true` plus curator. A1 remains
outside that exception path. The nomination command reports candidates for
review without changing the deck:

```bash
.venv/bin/python -m scripts.audit.generate_practice_deck \
  --nominate-a2-synonyms --atlas-db <atlas-db> \
  --vesum-db <vesum-db> --synonym-verdicts <synonym-verdicts>
```

An invalid exception flag drops only the exception and keeps the approved pair
at the B1+ floor. That is fail-closed placement, not a reason to lower the
floor or manufacture A1/A2 cards.
