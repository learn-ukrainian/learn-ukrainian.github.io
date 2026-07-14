# Curriculum lifecycle module contract

Operate on the manifest target `{{track}}/{{slug}}` in phase `{{phase}}` from
derived state `{{module_state}}`. Treat evidence identity
`{{evidence_identity}}` as immutable input, and stop if any consumed dependency
does not match it.

Return only JSON conforming to the registered
`curriculum-lifecycle-output.v1` schema. Findings must name the owning phase;
never repair content from inside a read-only gate.
