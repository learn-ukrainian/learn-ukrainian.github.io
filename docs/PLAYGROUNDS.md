# Playgrounds & Interactive Tools

The Learn Ukrainian project includes several interactive "playgrounds" for exploring curriculum architecture, monitoring module status, and prototyping activities.

## Overview

Playgrounds are HTML/JavaScript-based tools located in the `playgrounds/` directory. They provide a visual interface for complex curriculum data and allow for interactive prototyping.

## Running the Playgrounds

The easiest way to view the playgrounds is to start the playground server:

```bash
# Start the server (FastAPI)
.venv/bin/python scripts/playground_server.py
```
This will serve the playgrounds at **http://localhost:8765**.

Alternatively, you can open the `index.html` file in any browser:
```bash
open playgrounds/index.html
```

---

## Available Playgrounds

### 1. Module Status Dashboard
- **File:** `playground-module-status.html`
- **Purpose:** Real-time visualization of module completion across all levels.
- **Features:**
    - Filter by level and track.
    - View passing/failing gates for each module.
    - Links directly to module source and audit logs.
- **Data Source:** Aggregated from `curriculum/l2-uk-en/*/status/*.json`.

### 2. Batch Manager Dashboard
- **File:** `playground-batch-manager.html`
- **Purpose:** UI for launching and monitoring batch operations.
- **Features:**
    - Launch research or fix-review batches.
    - View active tasks and real-time log streaming via WebSockets.
    - Pause/Resume/Stop batch operations.
- **Modes:** API mode (connects to FastAPI) vs. CLI fallback (instructions provided).

### 3. Activity Design Studio
- **File:** `playground-activity-design.html`
- **Purpose:** Prototype and preview interactive activities.
- **Features:**
    - Live preview of all 12+ activity types.
    - Export validated YAML for use in modules.
    - Copy-paste workflow for rapid activity creation.

### 4. Curriculum Architecture
- **File:** `playground-curriculum-architecture.html`
- **Purpose:** Explore the three-layer system (Plans → Build → Status).
- **Features:**
    - Diagram of the 7-phase reconstruction workflow.
    - Explanation of track structures (Core vs. Seminar).

### 5. Claude-Gemini Communication
- **File:** `playground-claude-gemini.html`
- **Purpose:** Visualize the inter-agent message broker.
- **Features:**
    - View conversation history between agents.
    - Stats on message types and task IDs.

---

## Data Synchronization

To ensure playgrounds reflect the latest state of the curriculum, run the data synchronization script:

```bash
# Update playgrounds/data/status.json from the latest audit cache
npm run playgrounds:data
```

To rebuild the embedded data in HTML files (for offline use):
```bash
npm run playgrounds:build
```

---

## Workflow Examples

### Prototyping a New Activity
1. Open the **Activity Design Studio**.
2. Select an activity type (e.g., `unjumble`).
3. Fill in the jumbled words and the answer.
4. Click **Preview** to test the activity.
5. Click **Export YAML** and copy the result into your `activities/{slug}.yaml` file.

### Monitoring a Large Batch
1. Start the **Batch Manager Dashboard**.
2. Launch a `fix-review` batch for B1.
3. Observe the progress bar as modules are processed.
4. Click on a specific module to view its live audit output in the log viewer.
