# WP6: dual book-row span selection (private review only)

The CLI-independent helpers `batches`, `write_packets`, `validate_receipts`,
`attestation_for` and `write_reconciliation_packets` live in `antonenko.py`.
The driver runs the seats. Extractors never call a model or write Ukrainian text.

The frozen source census is 342 `style_guide` rows. Only rows with a positive
printed page or nonempty section enter packets; unlocated rows remain withheld
`locator_unavailable`. Packet batches contain at most 20 located rows, ordered
by row id. Each row includes its id, locator, complete verbatim text and UTF-8
text SHA-256. `batch_sha256` hashes canonical JSON excluding that member.
The output guard requires a private directory outside every Git checkout.

## Selection receipts and dispatch attestation

Each seat returns a separate JSON file named `<batch>.sol.json` or
`<batch>.opus.json` in the driver's `antonenko_receipts` directory. The receipt
contains exactly:

```json
{
  "schema": "antonenko-span-receipt.v1",
  "model": "gpt-6.1-sol",
  "task_id": "unique-driver-seat-task",
  "batch_sha256": "<batch digest>",
  "rows": [
    {
      "row_id": 1,
      "row_text_sha256": "<row digest>",
      "pairs": [
        {
          "rejected": {"start": 10, "end": 15},
          "recommended": {"start": 16, "end": 21}
        }
      ]
    }
  ]
}
```

The other seat's model is `claude-opus-5-5`. Every batch row must appear exactly
once per seat. Offsets count Unicode characters, start inclusive and end
exclusive, into that row's text. Select only a form that the row itself names
as wrong and its named replacement. Return `pairs: []` otherwise. No text,
paraphrase, verdict or extra field is accepted. Both receipts must carry distinct
nonempty task ids.

Each receipt requires `<batch>.<seat>.attestation.json`, with exactly:

```json
{
  "task_id": "unique-driver-seat-task",
  "model": "gpt-6.1-sol",
  "status": "done",
  "result_sha256": "<SHA-256 of original dispatch result bytes>",
  "finished_at": "<dispatch completion timestamp>"
}
```

The driver's extractor obtains these fields from the canonical
`batch_state/tasks/<task_id>.json` and `.result` files, using
`attestation_for(receipt, task, result)`. The digest covers the original result,
including any JSON fence or surrounding text, rather than the extracted JSON
file. Results may be a JSON document or contain multiple `json` fenced blocks.
Exactly one fenced block must match the receipt's `batch_sha256`; zero or
multiple matches refuse `adjudication_receipt`. The extracted receipt must equal
that selected block's canonical JSON, without field normalization.
The receipt store verifies the sidecar against that same dispatch record and
result: exact task/model, `done`, completion timestamp, result digest and
byte-derived JSON payload equality. It refuses missing sidecars or dispatch
files, incomplete execution and mismatches. Receipt, sidecar, dispatch-record
and result bytes are pinned and revalidated on pair reads. These are trusted
host execution records, not cryptographic proof of the provider's internal work.

## Pair admission and reconciliation

The accounting unit is a candidate pair: the union of both seats' selected
ordered `(rejected, recommended)` offsets, keyed by row id and both spans.
Order within a receipt is immaterial. Identically selected pairs are admitted
individually as `agreed`. A pair selected by only one seat remains withheld
`adjudication_disagreement`; agreed siblings in that row remain eligible.
Two empty lists produce one `no_pair_named` placeholder. No receipts produce
one `adjudication_pending` placeholder. Each unlocated row contributes one
`locator_unavailable` placeholder. A single selection seat, wrong model,
malformed JSON or offsets, duplicate rows/pairs, incomplete coverage or an
incorrect digest on a loaded receipt refuses the build. A receipt filed under
an obsolete batch name is ignored; its current rows stay pending.

`write_reconciliation_packets(rows, receipt_root, root)` writes host-only
`<batch>.json` packets for disputed pairs. Each item includes the complete
source row, locator, text hash, ordered offsets and their exact span texts.
It does not include agreed pairs or invoke either seat.

Each reconciliation seat returns `<batch>.reconcile.<seat>.json`:

```json
{
  "schema": "antonenko-reconcile-receipt.v1",
  "model": "gpt-6.1-sol",
  "task_id": "unique-reconciliation-seat-task",
  "batch_sha256": "<original selection batch digest>",
  "pairs": [
    {
      "row_id": 1,
      "rejected": {"start": 10, "end": 15},
      "recommended": {"start": 16, "end": 21},
      "decision": "accept"
    }
  ]
}
```

The other decision is `reject`. Each receipt must cover exactly the disputed
pair set, without duplicates or invented pairs, and both seats are required.
Reconciliation requires the same dispatch provenance through
`<batch>.reconcile.<seat>.attestation.json`. Only two explicit accepts admit a
pair as `reconciled_accepted`. Either rejection keeps it withheld as
`reconciled_rejected`; it is no longer an unresolved disagreement. Malformed, stale, partial or
unattested reconciliation refuses the build. Absence of reconciliation leaves
the original disagreements withheld.

## Records and accounting

C6b emits one `book_calque_replacement` record per admitted pair, with the
rejected expression in its slot and the recommended expression as response.
Its model-visible context is empty: the answer-bearing book passage remains
in citation provenance only. Both quoted spans use the same row and locator.
The binding checks the selected offsets and the accounting-unit receipt.
There is no additional inferred calque label.

Every pair or placeholder has one accounting unit and one candidate. Therefore
accepted counts equal emitted records, including a row with both an accepted
and an unattested pair. `operation_accounting.records_counted` and
`record_reasons` use the same units. This is a selected-pair denominator, not
a complete semantic census of the book. The receipt store independently
reconstructs these units; the gate checks coverage and uniqueness against it.
The generic optional `census_query` freezes the underlying row count separately
from the derived unit count. Other components retain their existing accounting.

C6b owns its reviewed compatibility and citation-role mappings in COMPONENT.
The location-only v2 request may name the private `antonenko_receipts` directory.
Russification contrast is a word-card projection (#8982/#8989), not a dataset
component; its predecessor extractor is preserved on the C7 input branch.
An all-withheld build reports `missing_coverage`; accepted records are required
for real generic mutation verification. Structural tests do not establish
semantic completeness.
