**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: YAML_SCHEMA_VIOLATION
**Raw Error**: Contradiction between prompt and schema regarding `reading` activity. Prompt says `tasks` is required, but schema `reading-c1-hist` sets `additionalProperties: false` and does not define `tasks`.
**Self-Correction**: I strictly followed the JSON schema to avoid validation failure and omitted `tasks` from the `reading` activity.
**Proposed Tooling Fix**: Update the `reading-c1-hist` JSON schema to include the `tasks` property if it is truly required, or update the prompt to remove the requirement.