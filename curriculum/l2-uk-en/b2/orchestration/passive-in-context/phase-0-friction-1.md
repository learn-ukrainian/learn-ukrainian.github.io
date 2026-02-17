**Phase**: Phase 0: Research (Core)
**Step**: Reading State Standard
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: None. Mapping file reference for B2 passive was slightly broad (§4.1.3.1), requiring a keyword search to find the explicit syntax reference (§4.3.3.1).
**Self-Correction**: Used `grep` (via `run_shell_command`) to locate specific terms "пасив" and "безособові" to find the exact syntax section in the Standard.
**Proposed Tooling Fix**: Update `state-standard-2024-mapping.yaml` to include §4.3.3.1 explicitly under B2 Syntax -> One-member sentences.
