---
name: build-monitoring
description: How to monitor V7 curriculum builds — the Monitor tool command template, mandatory --worktree isolation, the JSONL event fields v7_build.py/linear_pipeline.py emit, and the Monitor API for state queries without running a build. Use whenever launching or watching a `scripts/build/v7_build.py` run.
---

# Build Monitoring (MANDATORY)

**NEVER poll builds with `ScheduleWakeup` or manual loops.** Use the `Monitor` tool:

Agents may run V7 builds during autonomous orchestration — always pass `--worktree` (PR #1952) so the build runs in `.worktrees/builds/{level}-{slug}-{stamp}/` and main stays clean.

```
Monitor(
    command=".venv/bin/python -u scripts/build/v7_build.py {level} {slug} 2>&1 | grep --line-buffered '^{\"event\"'",
    description="V7 build events for {level}/{slug}",
    persistent=True,
    timeout_ms=3600000
)
```

`v7_build.py` emits JSONL events from the wrapper and `linear_pipeline.py`: single-module lifecycle notifications such as `phase_done`, `review_score`, and `module_done`; writer/reviewer telemetry such as `writer_cot_emit`, `writer_tool_call`, `writer_end_gate`, `writer_tool_theatre`, `phase_writer_summary`, `mcp_config_resolved`, `reviewer_dim_evidence`, `reviewer_audit_call`, and `phase_review_summary`; and correction diagnostics `writer_correction_unparseable`, `reviewer_fixes_unparseable`, `reviewer_fixes_anchor_unmatched`. Each line becomes a notification — zero polling overhead.

For state queries without running builds, use the Monitor API (`docs/MONITOR-API.md`):
- Track health: `/api/state/track-health/a1`
- Failing modules: `/api/state/failing?track=a2`
- Build status: `/api/state/build-status/a1`
