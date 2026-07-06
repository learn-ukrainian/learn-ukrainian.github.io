# Tier-2 Disarm Procedure

This is the only documented rollback for live Tier-2 after arming.

Use it when the live reviewer lane fails canaries, the E6 circuit opens, provider
behavior drifts, or the operator stops the broad batch.

## Required Steps

1. Restore the E0 sentinel in a reviewed commit:
   - `DEFAULT_REVIEWER_MODEL_ID = "llm-reviewer-disabled-until-4370"`
   - `WorkflowOptions.enable_llm` default remains `False`
2. Freeze the spend ledger before more live calls:
   - stop the current batch;
   - copy the current ledger path and timestamp into the operator artifact;
   - do not append new live rows until the lane is re-armed by reviewed commit.
3. Invalidate current `gate_version` cache rows.
4. Leave flags/code disarmed until the canary evidence is green again and the
   user approves the next broad live batch.

## Cache Invalidation

Default command:

```bash
.venv/bin/python scripts/audit/qg_tier2_disarm.py --execute --gate-version qg_workflow.v3
```

Optional explicit DB:

```bash
.venv/bin/python scripts/audit/qg_tier2_disarm.py --execute --gate-version qg_workflow.v3 --db data/telemetry/llm_qg.db
```

Exact SQL executed by the helper:

```sql
DELETE FROM llm_qg_runs WHERE gate_version = ?;
```

The helper enables SQLite foreign keys, so matching `llm_qg_findings` rows are
cascade-deleted with their parent runs. It never changes flags or source code.

## Circuit State

The E6 circuit sidecar is local telemetry state. Inspect it at:

```bash
cat data/telemetry/llm_qg_live_circuit.json
```

After the provider lane is fixed or rerouted, clear only the circuit state:

```bash
.venv/bin/python scripts/audit/qg_workflow.py --reset-circuit
```

Use `--qg-circuit-state PATH` when operating on a non-default sidecar.
