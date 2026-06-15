# Pipeline Replay Regression Fixtures

`tests/replay/` is for deterministic, LLM-free regressions that replay a
recorded production-shaped input through a parser, summarizer, adapter, or gate.

Add the smallest redacted fixture that reproduces the bug under
`tests/replay/fixtures/`, then assert the real deterministic component handles
that shape. Do not add network calls, LLM invocations, local databases,
`batch_state/`, or secrets. If a component normally needs a database, stub or
monkeypatch that boundary so the test remains CI-safe.

Fixture verdicts should change only when the gate or adapter behavior is
intentionally changed, and that PR should explain which replay expectation moved.
