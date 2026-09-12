### `BLOCKED_BUDGET_EXHAUSTED`

Do not reopen, retry, or silently replace the run. Preserve the terminal
ledger and open a later run only after a separately adjudicated source or
protocol change establishes new scope.

Report the bounded ledger's `elapsed_time_ms`, `model_call_count`,
`repair_count`, and `final_quality_disposition` with the blocker and next
action. These counts are authoritative; do not add a hidden retry, stability
check, semantic review, repair, or quality-gate call outside them.
