# Lane report format (operator orders C-2783 LANE-CHECKIN-1027, C-2106, C-1399)

The one format for lane-to-CTO and CTO-to-operator status reports. Other files point here.

## Hourly lane report

At most 8 lines, in this order:

1. **SHIPPED** since the last report: issues closed, PRs merged, user-visible features.
2. **IN PROGRESS**: outcome, PR or task, ETA.
3. **BLOCKERS**: what, and who can fix it.
4. **FRICTION**: a tool or process that cost time.
5. **NEXT**.

Per deliverable, one blocker line: `state | blocker | who fixes | next | ETA`.

Any usage report lists all 10 pools: Claude a, Claude b, Codex/Sol (+ reset credits),
Grok+Cursor, Muse, AGY, OpenRouter, DeepSeek, Claude API keys (2), Codex API credits. A pool
with no reader says NOT CHECKED plus the command that would read it.

Timestamps come from `date -u` only.

## Lane driver (drive-epic)

- Answer the CTO's hourly check-in in this format within 20 minutes.
- While an operator-priority outcome is open, send it unprompted every 30 minutes.
- Send it through Fleet Comms to the CTO.

## CTO

- Ask every lane hourly for this report.
- Act on every blocker and friction in the same cycle (fix, order or escalate) and record
  the action in the tracker.
- Nudge a lane silent past 20 minutes.
- Review the outcome choice of a lane that has shipped nothing in 2 hours.
- Report to the operator in the same format; add the 10-pool usage line when asked about
  capacity.
