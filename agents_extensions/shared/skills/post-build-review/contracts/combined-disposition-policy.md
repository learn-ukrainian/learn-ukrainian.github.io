# Combined disposition policy

Review protocol version: `3.0.1`

Apply disposition in this order:

1. `INCOMPLETE`: deterministic/size command error; required or unclassified
   skip; source drift; missing provenance/version/hash/reviewer fields; schema
   failure; malformed, duplicated, wrapped, or contract-invalid raw reviewer
   response; unavailable required source tooling; incomplete semantic
   coverage; required learner evidence the reviewer could not inspect.
   Any incomplete required quality dimension also produces `INCOMPLETE`.
2. `BLOCK`: any blocker from deterministic, track-policy, or semantic evidence;
   any high mechanical finding; semantic `BLOCK`.
3. `REVISE`: semantic `REVISE`; semantic high/medium finding; other actionable
   non-mechanical medium finding.
4. `PASS`: deterministic stages completed, all skips were policy-classified,
   semantic coverage completed or is correctly not applicable, all five
   quality dimensions passed at `9.0` or higher with target-backed evidence,
   and only low/info improvement-backlog findings remain. A `10.0` dimension
   additionally requires exceptional positive justification and at least two
   distinct evidence anchors; absence of findings alone is not perfection.

Semantic `PASS` never overrides deterministic or track-policy findings. A
declared claim count never substitutes for its atomic ledger. Metadata never
substitutes for direct verification of perceptual audio, video, image, text, or
interactive claims. A count
above the size-policy advisory ceiling is not an automatic failure; the
semantic reviewer decides whether the excess is sourced density or padding.
The combined result is immutable evidence for the hashed inputs only.

Canonical severity is `blocker | high | medium | low | info`, matching the
deterministic audit and code-review verifier. Adapters normalize legacy
`critical → blocker`, `major → high`, `warning/minor → medium`, and `nit → low`.
