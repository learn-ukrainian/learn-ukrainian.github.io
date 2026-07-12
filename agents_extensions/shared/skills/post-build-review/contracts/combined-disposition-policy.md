# Combined disposition policy

Review protocol version: `1.0.0`

Apply disposition in this order:

1. `INCOMPLETE`: deterministic/size command error; required or unclassified
   skip; source drift; missing provenance/version/hash/reviewer fields; schema
   failure; unavailable required source tooling; incomplete semantic coverage.
2. `BLOCK`: any blocker from deterministic, track-policy, or semantic evidence;
   any high mechanical finding; semantic `BLOCK`.
3. `REVISE`: semantic `REVISE`; semantic high/medium finding; other actionable
   non-mechanical medium finding.
4. `PASS`: deterministic stages completed, all skips were policy-classified,
   semantic coverage completed or is correctly not applicable, and only
   low/info findings remain.

Semantic `PASS` never overrides deterministic or track-policy findings. A count
above the size-policy advisory ceiling is not an automatic failure; the
semantic reviewer decides whether the excess is sourced density or padding.
The combined result is immutable evidence for the hashed inputs only.

Canonical severity is `blocker | high | medium | low | info`, matching the
deterministic audit and code-review verifier. Adapters normalize legacy
`critical → blocker`, `major → high`, `warning/minor → medium`, and `nit → low`.
