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

Bindings exist only in memory and require the original loaded object and
unchanged content. Missing, copied, changed, ambiguous or mismatched records
withhold the action. Mixed-source daily previews withhold it, as required by
#10704. URLs over 2,000 bytes also withhold it. Disclosure resets when the item
or interface locale changes. Nothing submits an issue automatically.

This change does not authorize publishing a deck or deploying the site.
