# Batch Operations Guide

This guide describes how to perform batch operations on curriculum modules using the automated tools.

## Overview

Batch operations allow you to process multiple modules simultaneously or sequentially. This is useful for large-scale research, fixing common issues across a level, or performing comprehensive reviews.

## Batch Manager CLI

The primary entry point for batch operations is `scripts/batch_manager.py`.

### Commands

#### 1. fix-review
Launches a batch fix and review loop for a range of modules.

```bash
.venv/bin/python scripts/batch_manager.py fix-review b1 1 20 --model gemini-1.5-pro
```
- **Action:** Runs `batch_fix_review.py`.
- **Logic:** Audits modules, fixes failures with Gemini, and re-reviews until they pass.

#### 2. research
Launches a research batch for a range of modules.

```bash
.venv/bin/python scripts/batch_manager.py research b2-hist 1 10
```
- **Action:** Runs `batch_research.py`.
- **Output:** Generates `research/{slug}-research.md` for each module.

#### 3. list
Lists all active and recent batch tasks.

```bash
.venv/bin/python scripts/batch_manager.py list
```

#### 4. show
Shows detailed status and output for a specific task.

```bash
.venv/bin/python scripts/batch_manager.py show research-b2-hist-1-10-20260214120000
```

#### 5. stop
Marks a task as stopped (note: does not kill the background process).

```bash
.venv/bin/python scripts/batch_manager.py stop <task-id>
```

---

## Task Tracking & Metadata

Every batch operation creates a task in the `tasks/` directory:

- **`.json` file:** Contains metadata (task ID, operation, track, range, status, start/stop times).
- **`.output` file:** Contains the stdout/stderr logs of the operation.

### Monitoring Progress

To monitor a running batch in real-time, tail the output file:

```bash
tail -f tasks/<task-id>.output
```

---

## Resuming and Retrying

### Resuming a Batch
If a batch operation is interrupted, you can resume it by running the same command again. Most scripts are idempotent and will skip modules that are already complete (e.g., `batch_research.py` skips existing research files).

### Retrying Failed Modules
If certain modules fail in a batch, you can run a smaller batch targeting only those modules:

```bash
.venv/bin/python scripts/batch_manager.py fix-review b1 5 5  # Single module
.venv/bin/python scripts/batch_manager.py fix-review b1 12 15 # Specific range
```

---

## Troubleshooting

### PID Management
The `batch_manager.py` does not automatically kill background processes when `stop` is called. To manually kill a background batch:

1. Find the PID: `ps aux | grep batch`
2. Kill the process: `kill <pid>`

### Log Errors
If a batch is stuck or behaving unexpectedly, check the `.output` file in the `tasks/` directory for detailed error messages.

### Resource Limits
Parallel batch operations can be resource-intensive. If you encounter rate limits or memory issues, consider:
- Reducing the batch size.
- Using a faster model (e.g., `gemini-1.5-flash`).
- Running batches sequentially instead of in parallel.
