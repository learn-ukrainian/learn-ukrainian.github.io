**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Removed `id` field from analytical activities per hard prompt rule, despite the schema technically allowing it. Ensured all quotes in YAML are straight, not angular, to prevent parsing errors. Wrote quiz questions to rely strictly on textual analysis rather than general knowledge recall.
**Proposed Tooling Fix**: N/A