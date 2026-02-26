**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Carefully omitted any decorative quotes (e.g. `«»`) within YAML values to prevent parser issues. Handled strings containing colons with single quotes to ensure schema compliance. Checked `reading` activity `id` against the required `reading-[a-z0-9-]+` pattern and confirmed exact count of 25 vocabulary items without including IPA fields. Selected only allowed activity types strictly following the `b2-hist` schema definitions.
**Proposed Tooling Fix**: N/A