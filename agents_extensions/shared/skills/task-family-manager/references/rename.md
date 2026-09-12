## Rename

Use a fresh UUID for each operation. The preview persists an immutable exact rename map and digest. Generated titles keep role/generation suffixes and respect the local planner's 60-character title limit.

```bash
.venv/bin/python -m scripts.orchestration.task_family preview-rename \
  --repo-root /absolute/project \
  --manifest /absolute/manifest.json \
  --operation-id 00000000-0000-4000-8000-000000000010 \
  --base-title "Lifecycle complete" \
  --select-task 00000000-0000-4000-8000-000000000001 \
  --select-task 00000000-0000-4000-8000-000000000002 \
  --confirm-pin-unknown 00000000-0000-4000-8000-000000000001 \
  --confirm-pin-unknown 00000000-0000-4000-8000-000000000002 \
  --actor codex/operator --json
```

Family rename requires every included task. Repeat both selection arguments for every included UUID. After the user has seen the preview, call `set_thread_title` once per selected task using that task's exact `new_title`. Immediately reconcile each result:

```bash
.venv/bin/python -m scripts.orchestration.task_family reconcile-title \
  --repo-root /absolute/project \
  --family-id issue-5140-family \
  --operation-id 00000000-0000-4000-8000-000000000010 \
  --plan-digest <64-lowercase-hex-digest> \
  --db auto \
  --task-id 00000000-0000-4000-8000-000000000001 \
  --cwd /absolute/project \
  --expected-title "Lifecycle complete [Lead]"
```

Proceed sequentially and stop on the first mismatch. A retry is read-back-only when that exact action already succeeded.
