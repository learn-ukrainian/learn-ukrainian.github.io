# Release notes

## 0.1.1 — corrective packaging release

Status: immutable release.

This patch preserves the `0.1.0` dataset, prompt, schema, scoring policy,
scorer behavior, and saved results. It adds a separately identified reference
run; it does not revise any historical score.

Changes:

- established six authoritative English release documents and an automated
  language and release-surface gate;
- separated unrelated development, archive, and quality-gate material from the
  researcher documentation;
- clarified which repository files are required for verification and which
  can be ignored;
- added the VESUM retrieval date and asset size to the public provenance;
- added a provider-neutral response import and execution workflow;
- added a complete 677-item Gemma 4 31B IT reference run, with raw successful
  output, normalized output, metadata, two rejected first-attempt receipts,
  saved responses, and a reproducible aggregate report stored separately;
- added a separate immutable `0.1.1` freeze that revalidates all 21 historical
  artifacts while keeping every `0.1.0` byte unchanged;
- added a credential-free smoke command that validates both freezes and
  reproduces all four saved score reports.

The published release is
[0.1.1](https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/tag/0.1.1).
The machine-readable manifest under
`data/projects/ua_eval_harness/releases/v0.1.1/` records every artifact digest.

## 0.1.0 — initial public freeze

The initial release established:

- the deterministic 677-sentence UA-GEC evaluation set;
- the minimal-edit task instruction and JSON response schema;
- exact-edit F0.5 and heritage-aware headline calque recall;
- identity, training-fixture literal-rule, and `gpt-5.6-terra` saved baselines;
- split-integrity, contamination, license, and cryptographic freeze receipts.

Release `0.1.0` is immutable. Corrective packaging work must use a new release
directory and may not alter its frozen bytes.
