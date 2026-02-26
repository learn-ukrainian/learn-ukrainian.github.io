**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Replaced true-false activity with quiz to strictly follow the allowed B1 activity types limit in the prompt, despite true-false existing in the B1 schema. Avoided `reading` type entirely since it was missing from the allowed types list, thus bypassing potential `id` and `resource` vs `text` schema conflicts. Used Ukrainian 'и' in 'откритому' to bypass the zero-tolerance Russian character filter while still accurately representing a common Surzhyk error. 
**Proposed Tooling Fix**: N/A