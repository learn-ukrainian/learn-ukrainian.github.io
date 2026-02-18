**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: AMBIGUITY_IN_INSTRUCTIONS
**Raw Error**: None
**Self-Correction**: The instructions listed `group-sort` in the "Correct YAML Examples" section but excluded it from the "ALLOWED types" list. I chose to strictly follow the ALLOWED list and used `match-up` instead of `group-sort` to avoid potential audit failure. Also, the `cloze` requirement of 14 items forced a very dense summary text, which I constructed carefully to meet the count.
**Proposed Tooling Fix**: Clarify in the skill instructions whether `group-sort` is allowed for B1, and review the minimum item count for `cloze` to ensure it encourages good pedagogical flow rather than just density.
