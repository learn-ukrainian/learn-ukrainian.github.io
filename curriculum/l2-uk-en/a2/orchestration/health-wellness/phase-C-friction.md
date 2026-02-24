**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Carefully verified quote rules to avoid using `«»` in YAML values, converted internal quotes to single and standard quotes. Structured all `id` uses strictly according to schema (avoiding forbidden fields like `id` on non-reading activities for core tracks). Ensure cloze has exactly 10 blanks to pass the strict `minItems: 10` requirement.
**Proposed Tooling Fix**: N/A