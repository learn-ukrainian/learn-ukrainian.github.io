# Playground User Guide

The Ukrainian Curriculum project includes several interactive HTML playgrounds to help explore, prototype, and monitor the curriculum architecture.

---

## 1. Available Playgrounds

| Playground | Purpose | Key Features |
|------------|---------|--------------|
| **Architecture** | Explore system structure | 3-layer diagram, 4-stage workflow visualization, file explorer. |
| **Status Dashboard** | Real-time completion tracking | Visual grid of all 692 modules, audit gate status, word counts. |
| **Activity Studio** | Prototype and test activities | Live preview of 6+ activity types, YAML export, schema validation. |
| **Communication** | Visualize agent interaction | Message broker flow, task threads, MCP tool snippets. |
| **Batch Manager** | Monitor large-scale operations | Task status, real-time logs, CLI command generator. |

---

## 2. Getting Started

### Starting the Server
The playgrounds are served via a FastAPI server:
```bash
.venv/bin/python scripts/playground_server.py
```
By default, the server runs on `http://localhost:8765`.

### Accessing Playgrounds
Open `http://localhost:8765/playgrounds/index.html` to see the landing page with links to all available tools.

---

## 3. Refreshing Data

The Status Dashboard and Architecture playgrounds rely on aggregated data from the audit cache. To refresh this data:

1. Run audits on modules (updates `status/*.json`).
2. Run the data aggregator:
   ```bash
   .venv/bin/python scripts/generate_playground_data.py
   ```
   This updates `playgrounds/data/status.json`.

---

## 4. Workflows

### Prototyping Activities
1. Open the **Activity Design Studio**.
2. Select an activity type (e.g., `quiz`).
3. Edit the fields in the UI.
4. Preview the rendering in real-time.
5. Click **Export YAML** to get the code for your `activities/{slug}.yaml` file.

### Monitoring a Batch
1. Launch a batch via `batch_manager.py` (CLI).
2. Open the **Batch Manager** playground.
3. Your task should appear in the active tasks list.
4. Click on the task to see real-time log output and completion percentage.

### Visualizing Agent Conversations
1. Open the **Claude-Gemini Communication** playground.
2. Select a `task_id` from the dropdown.
3. View the message thread between Claude and Gemini.
4. Use the "MCP Tool" tab to copy/paste code for interacting with the message broker.

---

## 5. API Mode vs. CLI Fallback

The Batch Manager playground can operate in two modes:

- **API Mode**: When the playground server is running with write access, you can launch tasks directly from the UI.
- **CLI Fallback**: When API access is restricted, the UI generates the exact CLI command for you to copy-paste into your terminal.

---

## 6. Screenshots & Visual Aids

*Refer to the following images for UI guidance:*

- **Status Dashboard**: `assets/docs/playground-status.png`
- **Activity Studio**: `assets/docs/playground-activity.png`
- **Workflow Diagram**: `assets/docs/workflow-diagram.png`
