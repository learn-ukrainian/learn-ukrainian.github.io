# Practice Hub creation review

The factory loads `data/lexicon/practice-creation-review.json` offline. It never
requests a model review. Missing/malformed ledgers and missing, failed, malformed,
or stale receipts suppress new heritage/cloze output and warn with its identity.
Other validation (provenance, morphology, levels, distractors) still applies.

The committed grandfather list is frozen at `baseline_commit`, this PR's merge
base with `origin/main`. `baseline_sources` records SHA-256 of the exact source
files, including the heritage overlay and sentence-inventory residual. Do not
refresh the baseline when adding frames. Grandfathering takes precedence over
receipts: existing identities remain exempt from this creation-only gate.

Identity is SHA-256 of UTF-8 canonical JSON `[kind,prompt,answer,contrast]`, using
`ensure_ascii=False`, `sort_keys=True`, `separators=(',', ':')`, and no trailing
newline. `kind` is `heritage` or `cloze`. Prompt/answer are the actual stripped
factory text; contrast is the heritage calque or cloze `lemmaPlain`. Cloze answers
are resolved from the paradigm before admission; stress in prompts and answers
is preserved. No deck version, frame index, or source path enters identity.

For a new frame, an operator obtains AGY/Gemini review, fixes all findings, and
records the final review in the ledger's `receipts` object, keyed by identity:

```json
{
  "agent": "agy",
  "resolved_model": "gemini-<actual-resolved-model>",
  "verdict": "pass",
  "reviewed_at": "2026-09-06T12:00:00Z",
  "frame_sha": "<SHA-256 of the reviewed frame payload>"
}
```

Record the actual model and timestamp (timezone required), never this example
as review evidence. `frame_sha` hashes canonical JSON
`{"identity":[kind,prompt,answer,contrast],"source":source}` with the same settings.
Use `frame_identity`, `frame_sha`, and `heritage_source` from
`scripts.practice.creation_review` to compute the values. Heritage source is
`{"pair": <all pair fields except frames>, "frame": <entire frame>}`. Cloze
source is the entire normalized factory candidate (the output of
`read_cloze_sources` or `read_sentence_inventory`), including provenance.
Changing that payload requires a fresh receipt. Inventory reordering can change
candidate IDs and therefore invalidate a new frame's receipt; compute it after
final source ordering. The receipt ledger is trusted reviewed repository data,
not cryptographic proof of reviewer execution. No receipt is minted by this PR.

Ledger changes participate in the deck version to avoid reusing an asset version
when admission changes. The source-only sampling fingerprint remains unchanged.
