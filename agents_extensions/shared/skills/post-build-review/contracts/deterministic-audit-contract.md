# Deterministic audit contract

Deterministic contract version: `2.0.0`

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

Scan resolved learner surfaces with the generic patterns in track policy.
Record mechanically detected research/build workflow register as policy
findings, and inventory task lines that require audio, video, image, text, or
interactive evidence. Code records matches, paths, lines, and modalities; the
semantic reviewer decides whether the learner evidence is usable and
pedagogically appropriate.

For every module, build a hash-bound statement inventory from every
learner-visible content, activity, vocabulary, and resource-note statement.
Record immutable unit IDs, exact paths and lines, text hashes, and conservative
risk signals for universal quantifiers. For seminar modules, separately
inventory learner resources and every detected named-source attribution, and
add source-attribution signals to the corresponding statements. A
configured source alias with no matching learner resource is a material
`SOURCE_TRACEABILITY` finding. Only curated source aliases are named; an
attribution context without one uses the fail-closed `<unnamed-source>` label,
so incidental acronyms do not become spurious source identities.

Allowed deterministic skips must remain explicit in the result. Version 2.0.0
accepts the read-only omission of MDX regeneration validation, supersedes the
excluded legacy LLM-QG with the semantic stage, and records network liveness as
an external advisory. None may disappear silently.
