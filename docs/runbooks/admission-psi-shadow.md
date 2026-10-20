# Admission PSI shadow observations

Issue #10802 S2 adds local calibration observations to `dispatch_admission`.
The memory, load, worker-cap, pool, test-slot, and disk decisions remain authoritative.
The observer never authorizes workers, calls a provider, starts a service, or terminates processes.

## Candidate signal

The CPU `some` candidate refuses above 40% `avg10` or above 30% `avg60`.
Recovery requires both values below 25% and 20%, respectively, for 60 seconds of observations.
Equality remains in the hysteresis band. The previous decision persists within that band.
The first decision is unknown unless a stop threshold is exceeded or recovery is observed.
Missing or malformed CPU PSI resets the candidate to unknown.
A sample gap above 60 seconds or a backward clock resets continuity to unknown.
These values are calibration candidates, not enforcement thresholds.

Memory and I/O `some` and `full` are diagnostic measurements.
System CPU `full` is excluded because the [kernel PSI interface](https://docs.kernel.org/accounting/psi.html) leaves it undefined.

## Journal and attribution

The default journal is `batch_state/admission-shadow/` in the shared checkout.
`DISPATCH_PSI_SHADOW_DIR` overrides that directory, including for isolated tests.
Each UTC day has a JSONL file capped at 16 MiB. Each row is capped at 8 KiB.
The observer reads at most the final row of today's and yesterday's files for hysteresis state.
A non-waiting lock serializes observations across dispatch processes.
Contention, write failures, and limits produce explicit unknown persistence diagnostics.
The observer does not prune journals or start a background sampler.

Each write-capable `precheck` and `evaluate` samples the current load decision,
candidate PSI decision, PSI windows, phase, and current admission-check decision.
An early pass has no admission decision, because the remaining protections have not run.
Force overrides occur later and their outcome is explicitly unknown to this observer.
Read-only dispatches remain exempt.

Full evaluations reuse their existing live task IDs, pool counters, and test-slot snapshots.
Task, holder, and waiter lists each contain at most ten entries.
The cheap path performs no additional attribution scan and marks unavailable attribution unknown.
Task identifiers are bounded and exclude paths and free text.
These snapshots identify participants, not CPU ownership.
Unattributed load remains explicitly unknown rather than being assigned to a lane.
Admission summaries and task records include the shadow diagnostic.

## Compare a calendar day

After collecting a UTC calendar day, run the comparison from the project environment:

```bash
.venv/bin/python -m scripts.orchestration.admission_shadow \
  --directory batch_state/admission-shadow --day YYYY-MM-DD
```

The JSON report counts load-versus-PSI decisions, unknown signals, phases,
current admission-check decisions, peak `avg60` pressure, and invalid rows.
Its denominator is sampled evaluations, not unique dispatch attempts or admitted workers.
A dispatch can produce an early sample, a full evaluation, and a locked recheck.
The observed span and unknown counts expose incomplete measurements.
Unobserved intervals cannot establish continuous host health.

The Infra driver owns the live one-day comparison and subsequent calibration judgment.
Injected calendar-day tests verify the reporter but do not replace that measured trace.
An enforcement change requires a separate approved delivery.
