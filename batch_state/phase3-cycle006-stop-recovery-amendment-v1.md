# Phase 3 Cycle 006 controlled-stop successor amendment v1

Issue: `#6375`
Evaluation cycle: `phase3-v2-1-evaluation-cycle-006`

## Exact outcome and denominator

The immutable Cycle006-v3 source package remains untouched. A new successor
package may adopt exactly the 41 already fully verified Gemini packet seals:
40 clean packets (2,000 rows) and residual packet 1 (50 rows), for an adopted
denominator of 2,050 rows. The builder must reverify each adopted packet using
the existing chunk and semantic validators before and after custody transfer.

Residual packet 2 is not adopted. Its two failed calls had the generic,
text-free `structured_output_envelope_drift` terminal outcome and its provider
stop is immutable in the source package.

## Custody and privacy boundary

The successor is a new, non-existing mode-0700 destination only. It exclusively
publishes fsynced mode-0600 copies of the frozen source package and only the
reverified, sealed packet artifacts; it never hardlinks source files. It omits
the source `provider-stop.json`, every packet-2 attempt marker, and every
incomplete packet-2 artifact. A mode-0600 text-free receipt
binds both source and destination custody and manifest SHA-256 values, adopted
packet and row counts, and the omission facts.

The builder may hash private files and invoke the pre-existing validators, but
must never print, retain, or create a receipt containing prompt bodies, labels,
raw provider output, logs, stderr, conversation identifiers, or account data.
It makes no provider calls and does not inspect source content beyond what the
existing validators require for seal verification.

## Stop, residual, and third-call policy

The source stop permanently forbids new calls in the source. The sole
authorization for a third call on residual packet 2 is scoped to the newly
prepared successor package after its provenance receipt verifies; it is not an
authorization to resume, alter, or delete any source attempt state. This
amendment does not authorize a changed prompt, model, taxonomy, validator,
chunk size, custody binding, packet order, label reuse beyond the 2,050 adopted
rows, adjudication, publication, or a claim that the full 10,159-row Cycle006
denominator is complete.

Any source/destination collision, symlink, permission drift, unexpected or
partial state, failed seal revalidation, mismatched adopted count, or receipt
binding drift is terminal and leaves no destination. The residual is exactly
8,109 rows: residual packet 2 onward must be completed only through the
successor's separately authorized controlled execution.

## Completion terms

This amendment is complete only when the new destination has exactly the
frozen package, the 41 reverified adopted Gemini packet seals, no copied stop
or packet-2 attempt state, and a valid 0600 text-free provenance receipt. It
is preparation evidence, not a provider execution, completion certificate, or
semantic evaluation result.
