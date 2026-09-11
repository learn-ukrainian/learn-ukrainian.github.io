### `REVIEWER_INSTABILITY`

Stop content mutation. Preserve both review results. Identical source, config,
protocol, prompt, and reviewer identity with a different material finding or
disposition fingerprint is reviewer/tooling instability. Adjudicate the route,
prompt, evidence access, or reviewer. Record either a real `audit_tooling`
change with `record-change` or a no-source-change route adjudication with
`record-instability-adjudication`. Do not commission another semantic review
in the active bounded run: preserve the instability and route it to a later
run. Never average results or rewrite content to chase the flip.
