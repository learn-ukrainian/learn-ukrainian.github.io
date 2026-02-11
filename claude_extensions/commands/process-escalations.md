# /process-escalations - Handle Gemini's Stuck Modules

<skill>
name: process-escalations
description: List and fix modules that Gemini escalated to Claude after exhausting fix iterations.
arguments: [track] (optional - filter to one track)
</skill>

## Purpose

When the batch runner (Gemini) can't fix a module after 5 iterations, it escalates to Claude via the message broker. This command reads the escalation queue and fixes modules one by one.

## Workflow

### Step 1: Scan Escalation Queue

Read all failure files with `escalated: true`:

```bash
.venv/bin/python -c "
import json, glob
for f in sorted(glob.glob('batch_state/failures/**/*.json', recursive=True)):
    data = json.loads(open(f).read())
    if data.get('escalated'):
        gates = ', '.join(data.get('failed_gates', {}).keys()) or 'content gates'
        blocking = ', '.join(data.get('blocking_issues', [])) or '-'
        wc = data.get('word_count', {})
        wc_str = f\"{wc['actual']}/{wc['target']}\" if wc.get('actual') else '-'
        print(f\"{data['track']:12} {data['slug']:40} gates={gates:20} blocking={blocking:40} wc={wc_str} iters={data['iterations_used']}\")
"
```

### Step 2: Present Summary to User

Show a table:

| # | Track | Module | Failed Gates | Blocking Issues | WC | Iters |
|---|-------|--------|--------------|-----------------|----|-------|

Ask: "Which modules should I fix? (all / specific numbers / skip)"

### Step 3: Fix Each Module

For each selected module:

1. **Look up the module number** from the track config
2. **Run `/module-fix {track} {num}`** — this audits, diagnoses, and fixes in a loop
3. **If fix succeeds** (all gates pass):
   - Delete the failure file: `rm batch_state/failures/{track}/{slug}.json`
   - Acknowledge the broker message
   - Send response to Gemini: "Fixed {track}/{slug} — all gates pass"
4. **If fix fails after Claude's attempts**:
   - Update the failure file with Claude's diagnosis
   - Ask user for guidance

### Step 4: Report

After processing all modules, show:
- How many fixed
- How many still stuck
- What gates remain failing

## After Fixing

Once the failure file is deleted, Gemini's runner will see the module as no longer escalated and can process it normally again on the next batch run. The dispatcher's `Esc` column count will decrease.

## Integration

This command should be suggested when `/check-gemini` finds escalation handoffs (task_id starts with `escalate-`).
