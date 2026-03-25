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
- **Gemini** builds: research, write, exercises (default writer)
- **Claude** reviews: review phase (cross-agent adversarial, max 2 fix attempts)
- **Reviewer-as-fixer**: reviewer outputs `<fixes>` find/replace pairs, pipeline applies deterministically
- **Writer-driven словнік**: writer generates vocabulary with contextual translations
- **Plans**: DRAFT → REVIEWED → LOCKED lifecycle. Review plan before content build.
- Model defaults: Gemini `gemini-3.1-pro-preview` | Review: `claude-opus-4-6`
- Build: `.venv/bin/python scripts/build/v6_build.py {level} {num} [--step {step}] [--writer {gemini|claude|gemini-tools|claude-tools}]`
- Writer modes: `gemini-tools` / `claude-tools` have MCP access (VESUM/RAG) during writing

**An LLM must NEVER review its own work.** Gemini builds → Claude reviews. Enforced by `SELF_REVIEW_DETECTED` audit gate.

</critical>
