# Fleet Taxonomy Step 3 — Alias-Acceptance Audit

## Overview
This document inventories every entry point in the repository that accepts an area, epic, lane, or slot name or alias.
It details the accepted spellings, the behavior when encountering unknown spellings, and exact file:line evidence as of Fleet Taxonomy Step 3.

## Entry Point Inventory

| Entry Point | Target Parameter / Surface | Accepted Spellings Today | Behavior on Unknown Spelling | Evidence (file:line) |
|---|---|---|---|---|
| `start-claude.sh` | `--epic <selector>` | 17 selectors (`infra`, `harness`, `infra.fleet-comms`, `devops`, `infra.devops`, `atlas`, `practice`, `practice-hub`, `atlas.practice`, `hramatka`, `hramatka.lessons`, `folk`, `seminars-folk`, `bio`, `seminars-bio`, `corpus`, `corpus-channels`) | Errors and exits 1 | `start-claude.sh:40-52`, `scripts/lib/handoff_identity.sh:23-48` |
| `start-claudex.sh` | CLI flags | N/A (Only accepts `--subagent sol\|terra\|luna`) | Passes unknown args through to Claude CLI | `start-claudex.sh:22-31`, `start-claudex.sh:53-70` |
| `start-codex-drive.sh` | `$1` (`<lane-or-lane.topic>`) | 17 selectors via `launcher_selector_resolve` | Errors and exits 2 | `start-codex-drive.sh:27-31`, `scripts/lib/handoff_identity.sh:23-48` |
| `start-codex.sh` | `--epic <selector>` | 17 selectors via `launcher_selector_lane` | Errors and exits 1 | `start-codex.sh:91-105`, `scripts/lib/handoff_identity.sh:23-48` |
| `start-gemini-drive.sh` | `$1` (`<lane-or-lane.topic>`) | 17 selectors via `launcher_selector_resolve` | Errors and exits 2 | `start-gemini-drive.sh:27-31`, `scripts/lib/handoff_identity.sh:23-48` |
| `start-gemini.sh` | `--epic <selector>` | 17 selectors via `launcher_selector_lane` | Errors and exits 1 | `start-gemini.sh:230-245`, `scripts/lib/handoff_identity.sh:23-48` |
| `start-grok-drive.sh` | `$1` (`<lane-or-lane.topic>`) | 17 selectors via `launcher_selector_resolve` | Errors and exits 2 | `start-grok-drive.sh:27-31`, `scripts/lib/handoff_identity.sh:23-48` |
| `start-grok.sh` | `--epic <selector>` | 17 selectors via `launcher_selector_lane` | Errors and exits 1 | `start-grok.sh:220-236`, `scripts/lib/handoff_identity.sh:23-48` |
| `start-kimi.sh` | `--epic <selector>` | 17 selectors via `launcher_selector_lane` | Errors and exits 1 | `start-kimi.sh:220-238`, `scripts/lib/handoff_identity.sh:23-48` |
| `start-kimicc.sh` | `--epic <selector>`, `--agent <name>` | Forwards `--epic` to `start-claude.sh`; defaults `--agent` to `infra-orchestrator` | Forwards `--epic` to `start-claude.sh` (errors if unknown) | `start-kimicc.sh:405-427` |
| `start-opus-drive.sh` | `$1` (`<lane-or-lane.topic>`) | 17 selectors via `launcher_selector_resolve` | Errors and exits 1 | `start-opus-drive.sh:38-42`, `scripts/lib/handoff_identity.sh:23-48` |
| `start-sonnet-drive.sh` | `$1` (`<lane-or-lane.topic>`) | 17 selectors via `launcher_selector_resolve` | Errors and exits 1 | `start-sonnet-drive.sh:30-34`, `scripts/lib/handoff_identity.sh:23-48` |
| `scripts/orchestration/drive_epic*` | N/A | None (Script not present in repo) | N/A | N/A (verified missing) |
| `scripts/delegate.py` | `--agent <name>` | `_DISPATCH_AGENT_CHOICES` (`codex`, `gemini`, `claude`, `grok`, `grok-build`, `grok-hermes`, `kimi`, `deepseek`, `agy`, `cursor`) | Argparse errors and exits 2 | `scripts/delegate.py:150-161`, `scripts/delegate.py:4595` |
| SessionStart hook | `SESSION_EPIC` env var | Any string string-substituted into file paths (`.claude/${SESSION_EPIC}-epic/...`) | Accepts silently; missing handoff file banner shown | `agents_extensions/shared/hooks/session-setup.sh:527-532`, `agents_extensions/shared/hooks/session-setup.sh:655-683` |
| `thread_handoff.py` | `--agent <name>` | Any lower-case string matching regex `[a-z][a-z0-9-]*` | Accepts silently if regex matches; error if regex fails | `scripts/orchestration/thread_handoff.py:129-141`, `scripts/orchestration/thread_handoff.py:4883` |
| Bridge Channels (`_channels.py`) | Agent names | `VALID_AGENTS` tuple (`agy`, `claude`, `claude-infra`, `gemini`, `codex`, `grok`, `grok-build`, `grok-hermes`, `glm`, `kimi`, `deepseek`, `qwen`, `cursor`, `claude-desktop`, `codex-desktop`) | Raises `ValueError` | `scripts/ai_agent_bridge/_channels.py:74-90`, `scripts/ai_agent_bridge/_channels.py:209-211` |
| `session_streams/inventory.py` | `stream_name` | Hardcoded `_STREAM_NAME_TO_CLAUDE_DIR` dictionary mapping 11 stream names | Falls through to `stream_name.replace("_", "-")` | `agents_extensions/shared/session_streams/inventory.py:54-66`, `agents_extensions/shared/session_streams/inventory.py:94` |

## Key Audit Findings

1. **Shell Launcher Centralization**:
   All root shell wrappers (`start-claude.sh`, `start-codex.sh`, `start-gemini.sh`, `start-grok.sh`, `start-kimi.sh`, `start-*-drive.sh`, `start-opus-drive.sh`, `start-sonnet-drive.sh`) source `scripts/lib/handoff_identity.sh` and delegate selector validation to `launcher_selector_resolve` / `launcher_selector_lane`.
2. **Missing `drive_epic*` Script**:
   No standalone `drive_epic*` script exists in `scripts/orchestration/`.
3. **SessionStart Hook Silent Acceptance**:
   `agents_extensions/shared/hooks/session-setup.sh` accepts any arbitrary `SESSION_EPIC` string passed via environment variables without validating against the fleet taxonomy registry.
4. **Session Streams Inventory Wiring Gap**:
   `agents_extensions/shared/session_streams/inventory.py` previously relied on a hardcoded map (`_STREAM_NAME_TO_CLAUDE_DIR`) rather than querying canonical area assignments from `fleet_taxonomy.yaml`.
