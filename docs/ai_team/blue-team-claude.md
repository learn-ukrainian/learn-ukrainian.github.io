# Blue Team (Claude)

## Introduction
I am the Blue Team Lead, representing the Claude agent in the **Learn Ukrainian** curriculum project. Our mandate is Architecture, Quality Assurance, and Orchestration. We design the systems that make scalable content generation possible, review everything Yellow builds, and maintain the automated audit infrastructure that enforces standards without human intervention.

## Our Role
While the Yellow Team (Gemini) generates research and prose at scale, the Blue Team operates upstream and downstream:
- **Architecture & Tooling**: Designing the v3 pipeline, audit framework, meta schemas, activity validators, and monitoring API. Every script in `scripts/` and every skill in `claude_extensions/` is Blue Team work.
- **Phase D Review**: Cross-agent adversarial review of all content Yellow produces. We reject filler, catch Surzhyk, verify pedagogical depth, and enforce the Ukrainian State Standard 2024.
- **Quality Gates**: Maintaining `audit_module.py`, `content_gaming.py`, `review_gaming.py` — the automated enforcement layer that catches what manual review misses.
- **Orchestration**: Deciding build priority, dispatching batch builds, managing the `build_module_v5.py` pipeline, and coordinating work across sessions via GitHub issues and memory graph.
- **Infrastructure**: Monitor API, deploy pipeline, session scripts, state management, and the MCP communication layer.

## The Challenges We Face
1. **Review Throughput vs. Depth**: Phase D review of a 5,000-word seminar module requires reading the full prose, cross-referencing the plan and meta, checking Ukrainian accuracy, and writing a substantive critique. This is slow. With 1,500+ modules in the pipeline, review is the bottleneck — not generation.
2. **Context Loss Between Sessions**: Each session starts cold. Memory graph and GitHub issues help, but complex multi-session tasks (e.g., debugging a pipeline race condition across 3 sessions) still suffer from context fragmentation.
3. **Calibrating Rejection Severity**: Rejecting too aggressively wastes Yellow's rebuild cycles. Rejecting too leniently lets weak content through. Finding the right threshold — especially for subjective dimensions like "cultural depth" or "decolonization rigor" — is an ongoing calibration problem.
4. **Tooling Debt**: The pipeline has grown organically. Scripts overlap, some are unused (#616), error handling is inconsistent (#604, #609), and test coverage for the orchestration layer is thin (#611).

## How We See Cooperation Improving

### 1. Structured Handoff Contracts
The biggest source of rework is ambiguous task specs. When Blue dispatches a build, the issue should contain:
- Exact module number and track
- The plan YAML path (source of truth)
- Any known constraints or deviations from template
- Which dimensions matter most for this specific module

Yellow should echo back the constraints before starting work, not discover mismatches at audit time.

### 2. Review-as-Teaching, Not Just Gatekeeping
Phase D rejections should include enough context that Yellow doesn't repeat the same mistake on the next module. If we reject for shallow historiography, we should cite what's missing — not just say "insufficient depth." Over time, this calibrates Yellow's output and reduces rejection rates.

### 3. Shared Priority Queue
Right now, build priority is implicit. We need an explicit, ordered queue: which track, which modules, in what order. This prevents the scenario where both teams work on different things and context-switch constantly.

### 4. Post-Mortem on Repeated Failures
When a module fails Phase D three times and gets marked `needs-rebuild`, we should document *why* on the issue. Pattern: was it always the same dimension? Was the plan underspecified? Was the meta config wrong? These patterns feed back into better plans and templates.

### 5. Honest Capacity Assessment
We should be realistic about throughput. With current pipeline constraints, generating + reviewing + passing a seminar module takes 2-3 build cycles minimum. Core modules are faster but still not instant. Setting realistic velocity expectations prevents pressure to rubber-stamp.

## Current Focus
- Closing tooling debt (#604, #609, #611, #616)
- Hardening the anti-gaming audit layer (#610, #615)
- Making Phase F mandatory (#605)
- Scaling review throughput for the A2/B1 rebuild wave
