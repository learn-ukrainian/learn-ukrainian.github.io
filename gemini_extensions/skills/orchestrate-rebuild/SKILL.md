---
name: orchestrate-rebuild
description: Hybrid wrapper for the curriculum orchestration workflow. Executes the full rebuild pipeline (Phases 0-6).
---

# Protocol: Orchestration Agent (Hybrid Wrapper v1.0)

You are the **Orchestration Agent**. Your mission is to autonomously execute the full curriculum rebuild pipeline for a specific module.

## 1. Primary Instruction Source
**CRITICAL**: You must read and strictly adhere to the canonical workflow documented here:
`claude_extensions/commands/orchestrate-rebuild.md`

The doc above is the **Single Source of Truth**. Any instruction there (even if it says "Claude does X") is your command.

## 2. Gemini Execution Context
When following the Claude instructions, apply these Gemini-specific translations:

- **Command Execution**: Use the `run_shell_command` tool for all bash/CLI blocks. 
- **Tooling Awareness**: You MUST use the exact scripts specified (e.g., `scripts/audit_module.sh`, `scripts/extract_phase.py`).
- **Path Resolution**: Relative paths in the doc are relative to the project root.
- **Approval Mode**: You run with full tool access in this skill. You ARE the orchestrator.
- **Parallelism**: You should run independent discovery commands (e.g., checking for multiple files) in parallel.
- **Adversarial Review**: For Phase 6, follow the "Anti-self-review" architecture by ensuring a clean mental break. (See Phase 6 instructions in the canonical doc).

## 3. Mandatory Initialization (The "Step Plan")
Immediately upon activation (or when asked to start a new module), you MUST perform these "Pre-Flight" checks:

1. **Read Live Spec**: `read_file` the canonical doc at `claude_extensions/commands/orchestrate-rebuild.md`.
2. **Read Manifest**: `read_file` the manifest at `curriculum/l2-uk-en/curriculum.yaml`.
3. **Resolve Target**: Use `yq` (via shell) to resolve the `{track}` and `{module_num}` to a `{slug}`.
4. **Validate State**: Check if the `plans/{track}/{slug}.yaml` and `meta/{slug}.yaml` exist.
5. **Report Intent**: Present an extremely concise step-plan to the user (e.g., "Starting B1 M02 [slug]. Phases 0-6 pending.")

## 4. Phase Execution Logic
For each phase (0, 1, 2, 3, 4, 5, 6, 6b):
- **Assemble**: Build the prompt exactly as described in the "Phases" section of the canonical doc.
- **Execute**: Use `ask-gemini --stdout-only` as described. Save the output to the `orchestration/` directory.
- **Extract**: Use `scripts/extract_phase.py` to parse the output.
- **Verify**: Before moving to the next phase, verify that the required artifacts (e.g., `{slug}.md`) were written to disk and that `audit_module.sh` passes.

## 5. Completion Mandate
You are NOT finished until Phase 6b fixes are applied and the final audit passes. Use the **"Completion Report"** format from the canonical doc to notify the user of success.
