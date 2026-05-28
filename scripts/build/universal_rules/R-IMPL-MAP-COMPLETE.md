---
id: R-IMPL-MAP-COMPLETE
description: Implementation map must list every obligation_id with artifact, location, treatment.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: []
---

`<implementation_map>`: list every `obligation_id` exactly once with artifact, location, treatment. Omission causes `implementation_map_missing`. If a row cannot fit current scope, emit artifact/location `<none>` and treatment `deferred — <why>`.

Emit `<implementation_map_audit>manifest_obligations=N covered_in_map=M missing=[<deferred IDs>]</implementation_map_audit>` as the first audit line.

If `M < N`, fix the map before artifacts.

Pre-resolved tuples come from the Implementation Map Contract: `(obligation_id, artifact, location_hint, treatment_template)`. Emit each row's required element at its `location_hint` using its `treatment_template`. Do NOT invent obligations beyond the manifest; do NOT skip rows. The deterministic `wiki_coverage_gate` verifies row-by-row; missing rows produce `fix_proposals` and the rebuild is wasted. Treatment templates that look thin → copy keys/values verbatim; do not pad. Gate diagnostics, not your prose, drive seeder fixes.
