# Data card: Ukrainian Open-Weight Evaluation 0.1.0

## Intended use

Use this release to compare local open-weight systems that correct or preserve
Ukrainian text. It supports deterministic saved-output evaluation and analysis
by track and category. It is not training data, a fluency benchmark, or a
single measure of Ukrainian quality.

## Provenance and grades

The immutable UA Eval 0.1.1 held-out manifest is the human-gold anchor. Its
error sources and accepted corrections yield 1,000 error cases and 1,000
correct controls through deterministic, hash-recorded context wrapping. This
means the suite contains 1,000 independent human-gold anchor judgments, not
4,000 independent human judgments.

The protected and unresolved halves derive from project regression evidence
and project-authored controlled seeds. Each row says `source_backed_silver`,
`controlled_silver`, or `unresolved`; none claims new human gold. Repeated
context wrappers provide controlled stress testing but do not constitute
independent linguistic examples.

The parked v0.2 review packet remains frozen evidence only. Its cases are not
silently promoted to gold.

## Licensing and attribution

Rows whose identifiers start with `uaw-011-` are UA-GEC derivatives under CC
BY 4.0. Rows whose identifiers start with `uaw-silver-` are project-authored
under MIT. The exact transformations, citation, pinned revisions, exclusions,
and file-level dispositions are recorded in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and in the generated
`PUBLICATION_MANIFEST.json`.

No VESUM dictionary byte or derived evidence artifact, private corpus byte,
provider raw output, model weight, or pending v0.2 review item is included in
the publication package.

## Risks and limitations

- UA Eval's source distribution and annotation choices still shape the gold
  half of the suite.
- Controlled silver can encode author assumptions and has limited lexical
  diversity.
- Exact-match scoring misses semantically valid alternatives outside the
  accepted set.
- Correct abstention protects ambiguity but does not resolve it.
- A model may have encountered public benchmark text during pretraining.
- The source-backed and controlled silver cases are evidence-graded stress
  tests, not qualified-human acceptance or a replacement for new human gold.

Publish the full per-track report, release hash, model and tokenizer revision,
decoding settings, and local-run receipt. Do not report a derived global score.

## Contamination policy

Every case has `foundry_learning_eligible: false`. The Foundry exclusion
registry loads the complete case file by default and applies exact and
near-duplicate filtering before emitting learning views. Evaluation requests
contain sources only; gold fields are joined only by the deterministic scorer
after model output has been saved.

The full mechanical boundary and run-disclosure requirements are in
[CONTAMINATION_POLICY.md](CONTAMINATION_POLICY.md).
