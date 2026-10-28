# Git maintenance could escape its timeout and interfere with validation

Tracked in #11157. This is a source-level autopsy of the failure mechanism.
Production incident receipts are not part of this public record. Exact incident
timing, peak memory, process ancestry and throughput effects remain unverified.

## Symptom

The scheduled runner could report completion while a detached repack continued
without resource bounds or validation exclusion. Actual incident effects remain
unverified in this public record.

## Root cause

At main commit `1e9044ad54fb5df3fd52eb026403e475e1927cce`,
`scheduled_worktree_cleanup.py:924-933` invoked plain `git gc --auto` through a
120-second subprocess timeout. Neither pack-memory settings nor a validation
admission lock bounded that command. Its hourly systemd service had no memory,
CPU or task limits. The source still existed after the reaper's retirement.

[Git documents](https://git-scm.com/docs/git-gc) that automatic GC can detach by
default. A detached repack can outlive the subprocess whose completion the
runner observes and the runner's hygiene lock. Even foreground subprocess
timeouts do not bound a descendant's memory. These are verified source defects,
not evidence that a particular pack file came from this command. Automatic
fetch maintenance was already disabled at command scope by #10856.

## Prevention

Hourly hygiene no longer invokes GC. A dedicated quiet-hour service verifies
effective cgroup bounds and ordinary-command auto-maintenance suppression,
then takes the existing validation admission lock and runs foreground GC with
one pack thread and explicit pack-memory settings. A bounded process-group
shutdown handles a hung Git tree; systemd supplies aggregate resource limits.

Regression coverage uses real disposable repositories to check admission
deferral, repacking, timeout recovery and preservation of refs, reachable and
staged objects, an active worktree and an incident-pack sentinel. Unsupported
resource bounds refuse GC. A successful no-op is reported as unchanged.

Production configuration, workload-hour validation, incident-pack disposition
and the incident-specific autopsy evidence remain with the driver on #11157.
No production recovery or throughput improvement is claimed by this PR.
