# Release notes

## 0.1.1 — corrective packaging release

Status: release candidate.

This patch preserves the `0.1.0` dataset, prompt, schema, scoring policy,
scorer behavior, and saved results. It does not revise benchmark scores.

Changes:

- established six authoritative English release documents and an automated
  language and release-surface gate;
- separated unrelated development, archive, and quality-gate material from the
  researcher documentation;
- clarified which repository files are required for verification and which
  can be ignored;
- added the VESUM retrieval date and asset size to the public provenance;
- prepared a provider-neutral response import and execution workflow;
- reserved a separate immutable `0.1.1` freeze so that `0.1.0` bytes remain
  independently verifiable.

The final `0.1.1` entry will identify the added baseline, release-manifest
digest, and published release URL after those artifacts are frozen.

## 0.1.0 — initial public freeze

The initial release established:

- the deterministic 677-sentence UA-GEC evaluation set;
- the minimal-edit task instruction and JSON response schema;
- exact-edit F0.5 and heritage-aware headline calque recall;
- identity, training-fixture literal-rule, and `gpt-5.6-terra` saved baselines;
- split-integrity, contamination, license, and cryptographic freeze receipts.

Release `0.1.0` is immutable. Corrective packaging work must use a new release
directory and may not alter its frozen bytes.
