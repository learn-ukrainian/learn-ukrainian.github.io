# Native Grok language-seat overlay (#10835)

The operator order of 2026-10-16 (CTO order cto-grok-rule) admits native Grok 4.7
to all work, including Ukrainian, under measurement with the Sources MCP; sets the
native Claude worker default to Sonnet 5.5 (Opus 5.5 only for complex or security
work); and holds Gemini 4 until the provider fixes its cost.

`routing-10835.json` records the only two captured routing fields that change,
each as an exact `before` and `after` value, and is applied after every other
overlay (`approved_grok_language_seat_baseline` in
`tests/review/test_model_catalog.py`):

- `catalog.models.grok-4.7.roles` gains `ukrainian_review`. The role is
  descriptive. No Grok review route lists the `ukrainian` profile, and the
  resolver, delegate language-lane and sense-binding family filters still refuse
  xAI until the native Grok harness wires the Sources MCP.
- `fallbacks.worker_resource_policy` states the Sonnet worker default, the
  native Grok measurement rule, the Gemini 4 hold and the Opus 5.5 / Sol 6.1
  critical and security final sign-off.

A fresh capture in both CLI configurations was compared with every approved
surface: no other surface, model or field differs. The historical baselines,
input matrices, occurrence ledger, `capture.py`, `SPEC.md` and checksum
manifests stay byte-identical. The overlay digest is pinned in the test module,
and a scope test checks that nothing else changes.
