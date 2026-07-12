# Deterministic audit contract

Deterministic contract version: `1.0.0`

The canonical deterministic stage composes, without reimplementing:

1. `.venv/bin/python scripts/audit/track_deterministic_audit.py --track
   <track> --slugs <slug> --format json --fail-on never`
2. `.venv/bin/python scripts/audit/module_size_policy_audit.py --tracks
   <track> --slugs <slug> --built-only --format json`
3. Mechanical rules from `config/track-policy.v1.yaml`.

`--fail-on never` preserves structured output; combined disposition applies the
severity threshold. Never pass `--output` or
`--run-mdx-generation-validate`. Never substitute the legacy module audit or
shell wrapper, which write audit/status/log artifacts and may update caches.

Record canonical argv twice (`argv` and the privacy-safe `executed_argv`),
repository-relative cwd, exit code, stdout and stderr SHA-256, configuration
path, and configuration version. Never persist a machine-local interpreter
path. Hash every resolved source file. A command error, malformed JSON, unknown skip, missing
required evidence, or changed source hash fails closed as `INCOMPLETE`.

Allowed deterministic skips must remain explicit in the result. Version 1.0.0
accepts the read-only omission of MDX regeneration validation, supersedes the
excluded legacy LLM-QG with the semantic stage, and records network liveness as
an external advisory. None may disappear silently.
