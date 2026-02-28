**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Replaced planned 'true-false' activities with 'quiz' and 'unjumble' activities to strictly comply with the prompt's explicit list of 'ALLOWED types (use ONLY these)', avoiding potential auto-failures despite 'true-false' being present in the A1 schema. Additionally, carefully replaced or removed all Ukrainian angular quotes («») from YAML values to prevent any possibility of colon-parsing errors as explicitly instructed.
**Proposed Tooling Fix**: If 'true-false' is fully supported by the audit and pipeline for A1 modules, it should be explicitly added to the 'ALLOWED types' list in the orchestration prompt instructions to perfectly align with the schema and the plan file hints.