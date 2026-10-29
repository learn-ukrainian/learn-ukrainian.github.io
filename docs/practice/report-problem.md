# Reporting a practice item

The report action opens an editable GitHub issue prefill after an interface-locale
disclosure that reports are public and require a GitHub account. The learner submits
the issue manually. The destination is fixed in `practice-report.ts`.

The prefill contains seven fields: deck, version, digest, item, type,
interface locale and public prompt-reference ID. Values are percent-encoded within
the body. The prompt reference is a public artifact path and array position;
together with the digest it identifies the parsed record. No rendered prompt,
typed answer, imported document or saved progress is included.

CEFR and teacher records bind only when response size and SHA-256 match the
bundled release pointer. Bundled ZNO, culture and mechanics datasets use the
SHA-256 of the exact imported UTF-8 text as their consumer-derived version.
Daily previews use the exact public pool response. Matching exposes an action
for each pair; teacher grammar and cloze use the displayed drill's identifier.

Bindings exist only in memory and require unchanged attested content. Missing,
arbitrarily copied, changed, ambiguous or mismatched records withhold the action.
The single permitted projection is the built-in withdrawal in
`withoutDisabledPracticeModes`, checked by `retainWithdrawnPracticeOrigin`:

- The original must still pass its origin, snapshot and function checks. Both
  records must be plain objects without getters or symbol fields, and their
  computed item IDs must match. Only pointer-attested practice lexemes and index
  records qualify, so daily, teacher, bundled and imported records cannot gain origins.
- A lexeme copy has exactly the original's own fields plus `gloss`, `glossClean`
  and `meaningMcEligible`, with values `''`, `''` and `false`. Every other own
  field must retain its value under `Object.is`, including nested object and
  function references.
- An index copy has exactly the original's own fields. Only `modes` may differ:
  it keeps original modes in their original order, without additions or duplicates.
  Keeping every mode in a new array is accepted. All other fields use `Object.is`.
- The helper takes no caller-defined predicate or mapping and never overwrites
  an existing origin on the copy. It carries only deck, version, raw artifact
  digest, item ID and original locator from the verified origin. It recomputes
  the copy's snapshot and functions, so later mutation still withholds reporting.
  Repeated built-in withdrawal may bind again from a still-verified projection.

Any new projection requires its own designated approval. Unsupported glosses
and meaning modes remain withdrawn; source data and pointers are unchanged.
Mixed-source daily previews withhold reporting, as required by
#10704. URLs over 2,000 bytes also withhold it. Disclosure resets when the item
or interface locale changes. Nothing submits an issue automatically.

This change does not authorize publishing a deck or deploying the site.
