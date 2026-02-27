**Phase**: Phase 2: Content
**Step**: Plan parsing vs Research reconciliation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: The plan's `vocabulary_hints` assumed a medical biography ("лікарка", "гінекологія", etc.), while the research correctly identified the subject as a sea captain. I resolved this by weaving the medical vocabulary into the historical context of the first section to contrast traditional female roles (doctors/activists) with Berta's unprecedented path as a captain.
**Proposed Tooling Fix**: Fix the underlying plan generator to ensure `vocabulary_hints` align with the actual historical figure when regenerating C1-BIO module plans.