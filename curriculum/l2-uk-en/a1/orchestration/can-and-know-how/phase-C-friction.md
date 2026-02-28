**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Replaced true-false activity with quiz, as true-false was not listed in the strictly allowed types in the prompt, despite being in the plan and schema. Removed all guillemets («») from YAML values to prevent parsing issues with colons.
**Proposed Tooling Fix**: Include true-false in the allowed types in the prompt if it is permitted for A1 level.