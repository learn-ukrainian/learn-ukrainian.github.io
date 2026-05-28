---
id: R-NO-SCAFFOLDING-LEAKS
description: No writer-side scaffolding (panel IDs, Krok labels, obligation names) in published module body.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: []
---

**No writer-side scaffolding leaks.** Writer-side scaffolding never appears in module body. Forbidden in published markdown: panel IDs (`P1`, `P2`, ...), Krok-N labels (`Крок 5:`, `Step 5:`), obligation names from the wiki_coverage manifest (`ban-4`, `step-5`, ...), reviewer-fix anchors, phase names, gate names. The module is a finished lesson, not a writer's worksheet.

Integrate each Wiki Coverage Required item into natural lesson flow (a model sentence, usage example, conjugation row, phonetic transcription). Do NOT echo `Крок N:` labels or `[S\d+]` source markers — writer-side scaffolding.
