### `POST_BUILD_REVIEW_REQUIRED`

Read and follow `$post-build-review` completely for the same target. Before
any semantic/provider call, freeze and authorize its exact protocol identity:

```bash
.venv/bin/python agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
  prepare-semantic-review <track/slug> --run-id <id> \
  --protocol-version <X.Y.Z> --prompt-sha256 <sha256> --schema-sha256 <sha256> \
  --reviewer-family <family> --reviewer-model <model>
```

This command returns the only allowed phase and remaining budget. Do not make a
semantic call if it rejects. `record-review` accepts only a result bound to that
pre-existing frozen identity; protocol/tool/source drift is rejected without
consuming budget. A queued audit-tooling drift blocks every further active-run
semantic prepare or record because no packet provenance proves the result used
the frozen tooling. Use `restart-bounded-completion` for the later run. Allocate a
new invocation directory every time. Do not repair, normalize, or retry inside
that invocation. Use its emitted semantic schema when the provider supports
structured output; prompt-only JSON compliance is not a reliable automation
boundary. For Codex dispatches, emit the schema with `semantic-schema
--provider codex`; then `--output-schema <semantic_schema_path>` is mandatory.
An absent or provider-incompatible schema is `audit_tooling`, not a reason to
retry the model.
Record its exact result:

```bash
.venv/bin/python \
  agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
  record-review <track/slug> --run-id <id> --result <result_path>
```

The helper rejects target/source drift and validates the canonical result.
Never substitute `llm_qg.json`, SQLite, a score, or a generated audit report.
