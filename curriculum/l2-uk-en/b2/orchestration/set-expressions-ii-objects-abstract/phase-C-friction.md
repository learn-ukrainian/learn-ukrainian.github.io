**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Expanded most structured activities (`true-false`, `quiz`, `fill-in`, `match-up`, `unjumble`, `error-correction`, `select`, `translate`) to exactly 14 items per activity to safely exceed schema `minItems` constraints and align closely with the high activity density target requested in the prompt. Used explicit string quoting or raw strings when handling apostrophes (e.g. `п'яти`) to ensure perfect YAML parsing compliance.
**Proposed Tooling Fix**: N/A