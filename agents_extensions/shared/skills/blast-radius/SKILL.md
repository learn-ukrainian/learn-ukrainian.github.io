---
name: blast-radius
description: Investigate a change's consumers, downstream effects and testing perimeter without implementing fixes. Use for /blast-radius or questions about what a change could break.
---

# Blast radius

Investigate impact only. Keep repository files unchanged; return proposed fixes
to the authoring worker through the accountable driver. This skill grants no
deployment, merge, external mutation or additional delegation authority.

1. Establish the exact revision or proposed change, altered behaviour and
   acceptance criteria. State the safety assumptions whose failure would cause
   a material regression.
2. Trace direct callers and transitive consumers using symbol and import search.
   Follow effects beyond imports: serialized fields, shared schemas, database
   readers, configuration, feature flags, generated artifacts and other languages.
   Check pinned dependency behaviour and local patches where they matter.
3. Trace lifecycle and failure paths: initialization, asynchronous completion,
   retries, cache invalidation and teardown. Cite concrete code or contract
   locations for each plausible failure; label missing evidence as unknown.
4. Map the testing perimeter to affected consumers and contracts. Name focused
   regression, integration and user-visible checks, including edge cases that
   could falsify the safety assumptions. An empty search proves only that no
   match was found within the searched scope.
5. **Prove it works:** use existing tests or non-mutating reproductions, where
   the assigned seat permits execution, to observe real behaviour against the
   acceptance criteria. Record revision, inputs, commands and actual results.
   Do not edit tests or production code during investigation. If a probe needs
   writes, external effects or execution unavailable to the reviewer, give the
   owning worker the required check and mark the assumption unproven.

Return the affected paths and consumers, ranked risks with impact and
likelihood, cleared risks with evidence, and the explicit testing perimeter.
Name residual evidence gaps and their owners. Escalate material uncertainty,
ownership conflicts or wider design questions to the driver; investigation is
not the independent exact-head review or current-head CI approval required by
`agents_extensions/shared/rules/workflow.md`.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
