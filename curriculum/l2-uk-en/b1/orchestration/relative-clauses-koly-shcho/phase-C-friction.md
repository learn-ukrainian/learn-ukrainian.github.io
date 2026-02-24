**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Replaced all Ukrainian angular quotes («») with standard single/double quotes in YAML values to avoid colon parsing issues. Ensured `select` activity uses `min_correct >= 2` as required by the schema and explicitly avoids single-correct questions. Provided exactly 10 activities to satisfy the volume threshold.
**Proposed Tooling Fix**: N/A