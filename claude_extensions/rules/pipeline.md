---
paths:
  - "scripts/build/**"
  - "scripts/pipeline/**"
  - "scripts/audit/**"
  - "scripts/validate/**"
  - "curriculum/**/orchestration/**"
---

# Pipeline Architecture

<critical>

**Pipeline V6** (`scripts/build/v6_build.py`) — the ONLY pipeline:
- check → research → skeleton → write → exercises → annotate → enrich → verify → review → publish
- **v5, v4, and v3 are RETIRED.** Do not use `build_module_v5.py` or `build_module.py`.
- **Writer default (on `main` since 5e2afbd092, 2026-04-23):** `claude-tools` (Opus). Gemini remains available via `--writer gemini-tools` for research + exercises. Post-#1431 v2: `claude-tools` chosen for module writing while residual writer-quality gaps on colors are being closed (#1449 → EPIC #1451).
- **Codex** is the primary pipeline reviewer (cross-agent, max 2 fix attempts). Claude reserved for dimensions requiring cultural/creative nuance.
- **Reviewer-as-fixer**: reviewer outputs `<fixes>` find/replace pairs, pipeline applies deterministically.
  > ⚠️ **Live contradiction (tracked as #1456):** `scripts/build/convergence_loop.py:595-607` still has `section_rewrite` / `full_rewrite` / `writer_swap` strategies despite the no-rewrite decision. Kill-or-revert pending — do not add new rewrite strategies until Phase 2-C of EPIC #1451 resolves.
- **Writer-driven словнік**: writer generates vocabulary with contextual translations
- **Plans**: DRAFT → REVIEWED → LOCKED lifecycle. Review plan before content build.
- Model defaults: Claude writer `claude-opus-4-7` @ xhigh | Gemini `gemini-3.1-pro-preview` | Codex reviewer via `codex-tools`
- Build: `.venv/bin/python scripts/build/v6_build.py {level} {num} [--step {step}] [--writer {gemini|claude|gemini-tools|claude-tools}]`
- Writer modes: `gemini-tools` / `claude-tools` have MCP access (VESUM/RAG) during writing

**An LLM must NEVER review its own work.** Gemini builds → Claude reviews. Enforced by `SELF_REVIEW_DETECTED` audit gate.

</critical>
