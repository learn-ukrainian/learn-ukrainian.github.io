**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: YAML_SCHEMA_VIOLATION
**Raw Error**: None (Pre-emptively avoided)
**Self-Correction**: Preventively removed all Ukrainian angular quotes («») from YAML values to strictly follow the instruction "Do NOT use Ukrainian angular quotes «» in YAML values. They break YAML parsing when combined with colons." This required rephrasing prompts and replacing decorative quotes with single quotes. Also ensured all quiz items use language-focused prompts like "Згідно з текстом..." to pass the golden rule.
**Proposed Tooling Fix**: N/A