## Restore and receipts

To restore, call `set_thread_archived` with `archived: false`, then reconcile the same selected task:

```bash
.venv/bin/python -m scripts.orchestration.task_family reconcile-restore \
  --repo-root /absolute/project \
  --family-id issue-5140-family \
  --operation-id 00000000-0000-4000-8000-000000000020 \
  --db auto \
  --task-id 00000000-0000-4000-8000-000000000001 \
  --cwd /absolute/project \
  --expected-title "Lifecycle complete [Lead]"
```

Render the durable receipt at any point:

```bash
.venv/bin/python -m scripts.orchestration.task_family receipt \
  --repo-root /absolute/project \
  --family-id issue-5140-family \
  --operation-id 00000000-0000-4000-8000-000000000020 --json
```

Report planned versus actual actions, skipped resources and reasons, failures with recovery instructions, restoration information, final retained resources, and the receipt path under `.agent/task-families/<family>/operations/<operation>/`.
