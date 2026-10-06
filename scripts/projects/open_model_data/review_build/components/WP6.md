# WP6: dual book-row span selection (private review only)

The CLI-independent helpers `batches(rows)`, `write_packets(rows, root)` and
`validate_receipts(batch, receipts)` live in `antonenko.py`. The driver runs the
seats; extractors never call a model or write Ukrainian text.

The frozen accounting census is 342 `style_guide` rows. Only the 279 with a
positive printed page or nonempty section enter packets; the other 63 remain
withheld `locator_unavailable`. Packet batches contain at most 20 located rows,
ordered by row id. Each row includes its id, locator, complete verbatim text and
UTF-8 text SHA-256. `batch_sha256` hashes canonical JSON excluding that member.
The output guard requires a private directory outside every Git checkout.

Each seat returns a separate JSON file named `<batch-sha256>.sol.json` or
`<batch-sha256>.opus.json` in the driver's `antonenko_receipts` directory. The
receipt contains exactly:

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
nonempty task ids. The driver supplies authentic routing and execution evidence;
these fields do not cryptographically attest model execution.

The pair sets must agree exactly in both directions; order is immaterial. Any
selection difference withholds the whole row as `adjudication_disagreement`.
Two empty lists withhold as `no_pair_named`. No receipts means
`adjudication_pending`; a single seat, wrong model, malformed offsets, duplicate
rows/pairs, incomplete row coverage or stale hash refuses the build.

C6b emits one `book_calque_replacement` record per agreed pair, with the rejected
expression in its slot and the recommended expression as response. Both quote
the same book row and locator. There is no additional inferred calque label.
The binding checks the exact selected offsets; the receipt store revalidates
both pinned raw receipts against the cited rows and their hashes on each read.

C7 derives records only from those pairs. The unstressed rejected expression
must match a SUM-11 headword; an absent match is `not_sum11_headword` (excluded).
The recommended expression needs checked, successful ULIF and VESUM witnesses.
SUM-11 is cited only on the rejected side as `soviet_colonization_context`, with
risk and keywords; `c7_opt_in` and the existing contrast-pair binding remain.
Missing attestation or markers withholds the pair. No headword inventory is
queried until a row has dual-selected pairs.

Accounting stays row-grained, including unresolved rows whose semantic pair
count is unknown. A row with any withheld pair is withheld; otherwise one or
more accepted pairs accept the row, and a row whose pairs are all ineligible for
C7 is excluded. `operation_accounting.records_counted` and `record_reasons`
report individual candidates separately. They include one placeholder for each
unresolved row and therefore are not a semantic rejected-form census.
The gate's opt-in `unit_multiplicity: records` supports this without duplicate
row accounting; all record identities must still be unique. Other components
retain one-record-per-unit enforcement.

Component exports, adapters and receipt store are shared as before. Complete
held bibliography remains required; placeholder forms withhold rather than
invent an edition, year or volume. Source compatibility uses the framework's
current integration contract. An all-withheld build reports `missing_coverage`;
`verify` cannot prove accepted-record mutations and returns
`mutation_unavailable`. Passing structural tests is not semantic completeness.
