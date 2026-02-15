**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Checked `true-false` activity type in prompt vs schema. Prompt text excluded it from "ALLOWED" list despite being in schema, so I adhered to the prompt's strict allowed list and replaced `true-false` with `quiz` or `match-up` where appropriate, or just avoided it.
**Proposed Tooling Fix**: N/A
