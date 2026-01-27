# Background Tasks in Claude Code 2.1

## What Are Background Tasks?

Background tasks allow you to run long-running processes (dev servers, audits, etc.) without blocking your Claude Code workflow.

## Usage

### Starting a Background Task

When Claude Code runs a command that takes a long time:

```
> Start the Docusaurus dev server

[Claude runs: cd docusaurus && npm start]
[Dev server starts...]

Press Ctrl+B to background this task
```

**Press `Ctrl+B`** to send the task to background.

### While Task Runs in Background

You can continue working on other things:

```
> Generate vocabulary exercises for B2 Module 75

[Claude works on this while dev server runs in background]
```

### Checking Task Status

```
> Show running background tasks

[Claude lists all background tasks with IDs]
```

### Viewing Task Output

```
> Show output from background task [ID]

[Claude displays recent output from the task]
```

### Stopping a Background Task

```
> Stop background task [ID]

[Claude terminates the process]
```

## Common Use Cases

### 1. Dev Server

**Problem:** Docusaurus dev server blocks Claude Code while running

**Solution:**
```
> Start Docusaurus dev server
[Ctrl+B when server is ready]

> Continue working on curriculum modules
[Server stays running]

> Stop the dev server when done
```

### 2. Long-Running Audits

**Problem:** Auditing all B2 modules (145 modules) takes 10+ minutes

**Solution:**
```
> Audit all B2 modules in background
[Ctrl+B immediately]

> Work on C1 modules while B2 audit runs
[Check results when done]
```

### 3. Database Rebuilds

**Problem:** `npm run vocab:rebuild` processes 12K+ vocabulary entries

**Solution:**
```
> Rebuild vocabulary database
[Ctrl+B after it starts]

> Continue module development
[Database rebuilds in background]
```

### 4. Parallel Testing

**Problem:** Need to run tests while continuing development

**Solution:**
```
> Run full test suite in background
[Ctrl+B immediately]

> Fix bugs found in previous test run
[New tests run in parallel]
```

## Configuration

No configuration needed - background tasks work out of the box in Claude Code 2.1.

## Best Practices

1. **Always background dev servers** - They don't need interaction
2. **Background long audits** - Check results when convenient
3. **Don't background interactive prompts** - They need input
4. **Monitor background tasks periodically** - Ensure they're still running

## Limitations

- Background tasks don't survive Claude Code restart
- Interactive prompts can't be backgrounded
- Maximum ~10 concurrent background tasks (system dependent)

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Background current task | `Ctrl+B` |
| View background tasks | `/tasks` command |
| Kill background task | `/kill [task_id]` |

## Example Workflow

```bash
# Morning: Start dev server
> Start Docusaurus dev server
[Ctrl+B]

# Work on modules all day
> Create B2 Module 132
> Fix grammar issues in A2 Module 15
> Enrich C1 Module 67 vocabulary

# Preview changes in browser
[Open http://localhost:3000 - dev server still running]

# Evening: Stop dev server
> Stop the Docusaurus dev server
[Claude finds and stops background task]
```

## Troubleshooting

### "Task not responding"

- Check if process crashed: `/tasks`
- View error output: `Show output from task [ID]`
- Restart if needed: Stop task, start new one

### "Too many background tasks"

- List all tasks: `/tasks`
- Kill unused tasks: `/kill [task_id]`
- Clean up completed tasks

### "Can't background this task"

- Some tasks require interaction
- Run them in foreground
- Or use separate terminal for those tasks
