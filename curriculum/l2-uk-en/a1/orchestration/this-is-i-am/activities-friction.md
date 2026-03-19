**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: PLAN_GAP
**Raw Error**: Plan activity_hints[2] specifies items: 4 for fill-in type, but activities-a1.schema.json requires minItems: 6
**Self-Correction**: Expanded fill-in #3 from 4 items to 6 items to meet schema minimum while maintaining the "meeting someone new" focus
**Proposed Tooling Fix**: Plan validation should warn when activity_hints item count is below schema minItems for the specified type