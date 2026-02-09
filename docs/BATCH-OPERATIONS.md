# Batch Operations Guide

This guide covers how to perform large-scale curriculum operations using the batch management tools.

---

## 1. Batch Manager CLI

The `scripts/batch_manager.py` script provides a unified interface for launching and monitoring batch tasks.

### Core Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `fix-review` | Audit and review a range of modules | `.venv/bin/python scripts/batch_manager.py fix-review b1 1 20` |
| `research` | Generate research for a range | `.venv/bin/python scripts/batch_manager.py research b2-hist 1 140` |
| `orchestrate` | Sequentially rebuild modules | `.venv/bin/python scripts/batch_manager.py orchestrate a1 1 10` |
| `list` | Show active/recent tasks | `.venv/bin/python scripts/batch_manager.py list` |
| `show` | View details of a specific task | `.venv/bin/python scripts/batch_manager.py show <task-id>` |
| `stop` | Mark a task as stopped | `.venv/bin/python scripts/batch_manager.py stop <task-id>` |

### Background Execution
Use the `-b` or `--background` flag to run batches in the background:
```bash
.venv/bin/python scripts/batch_manager.py fix-review b1 1 92 -b
```
This will redirect output to a `.output` file in the `tasks/` directory.

---

## 2. Task Tracking

All batch operations are tracked in the `tasks/` directory using JSON metadata files and output logs.

- **Metadata**: `tasks/{task-id}.json` (status, track, range, timestamps)
- **Output**: `tasks/{task-id}.output` (stdout/stderr of the batch process)

---

## 3. Resume & Retry Logic

Batch scripts (`batch_fix_review.py`, `batch_research.py`) support automatic resumption using a checkpoint system.

### Checkpoints
Progress is stored in `.checkpoints/{operation}-{track}.json`.
- When you restart a batch with the same track and range, it will automatically resume from the last uncompleted module.
- To force a restart from the beginning, delete the corresponding file in `.checkpoints/`.

### Retry Strategy
If a module fails (e.g., due to a temporary API error), the orchestrator will:
1. Log the failure.
2. Attempt a retry (if configured).
3. If it still fails, skip the module and move to the next.
4. Flag the module in the final report for manual attention.

---

## 4. Monitoring Tips

### Real-time Progress
If running in the background, you can monitor progress using `tail`:
```bash
tail -f tasks/fix-review-b1-1-92-20260201120000.output
```

### Message Viewer
For a visual overview of inter-agent communication during batches:
1. Start the viewer: `.venv/bin/python scripts/message_viewer.py`
2. Open `http://localhost:5055` in your browser.

### Batch Dashboard
The Batch Manager playground provides a UI to monitor and launch tasks:
1. Start the server: `.venv/bin/python scripts/playground_server.py`
2. Open `http://localhost:8765/playgrounds/playground-batch-manager.html`.

---

## 5. Troubleshooting Batches

### Stale Background Processes
If you stop a task via `batch_manager.py stop`, the background process may still be running. To kill it:
```bash
ps aux | grep batch_manager
# find the PID and then:
kill <pid>
```

### Stuck Messages
If the message broker seems stuck, check the watcher logs:
```bash
tail -f .mcp/servers/message-broker/watcher.log
```
Restart the watcher if necessary:
```bash
.venv/bin/python scripts/agent_watcher.py --stop
.venv/bin/python scripts/agent_watcher.py --daemon
```
