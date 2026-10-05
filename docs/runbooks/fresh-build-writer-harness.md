# Fresh-build writer harness

**Writer harness recovery (#9525).** `writer_harness_exhausted` stops a lesson after three
dispatch/execution/harvesting defects following an attempted writer dispatch, across input changes.
Content validation and caller errors before dispatch spend no harness budget; typed `rate_limited`
and `timeout` outcomes (including subprocess timeouts) also spend none, because capacity trouble
must not become a permanent lesson stop. They still fail the current build; retry explicitly after
capacity recovers. To reset the cap, first stop all builds and writer tasks for that lesson, preserve
its task records and sidecar as local diagnostic evidence, and fix the underlying defect. Then remove
only `lesson-N.writer-harness.yaml` and its `.lock` digest from that lesson's evidence state directory
and retry once. Keep the regeneration ledger and `.mutex` files; removing a mutex can defeat locking.

## Source quote admission (#8425)

The existing `kind: quote` block and `ref` identify a displayed source span.
The engine admits otherwise out-of-state words only at an occurrence whose
reference appears in that plan step's `evidence` and whose complete expanded
unit and quote provenance match the pack text after assembly normalization.
Unlisted, partial or rewritten quotes receive no allowance. Prose, inline
quoted terms, examples and scored fields keep the ordinary inventory checks.

Display-only tokens have `skipped:source_quote` receipts with no vocabulary
candidates or selection. They do not add allowed vocabulary, satisfy core or
recycled requirements, or supply scored forms. Already-allowed words retain
normal resolution. An out-of-state word in writer prose is a writer-layer
failure. Use the reported next gate failure to continue draft repair; admitting
a source quote does not certify the whole lesson.
