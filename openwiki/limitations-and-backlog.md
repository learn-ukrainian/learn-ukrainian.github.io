# OpenWiki Known Limitations and Program Backlog

**Issue:** [#5541](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5541)
**Stream:** `docs-knowledge` (Epic [#5535](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5535))
**Date:** 2026-09-17

---

## 1. Upstream OpenWiki Limitations (v0.5.2)

Evaluation of upstream LangChain OpenWiki (`openwiki@0.5.2`) reveals several behavioral traits that require explicit repository containment:

1. **Root Instruction File Hijacking:**
   *Observation:* Upstream `ensureCodeModeRepoSetup` in `dist/ingestion/code-mode.js` unconditionally attempts to inject markdown snippets into root `AGENTS.md` and `CLAUDE.md`.
   *Repository Conflict:* In `learn-ukrainian`, root instruction files are deployed copies generated strictly from source rules in `agents_extensions/shared/rules/`. External generator writes to root files violate repository governance (ADR-013, FBL-003).
   *Mitigation:* Root file writes must be blocked by custom execution wrappers or reverted prior to committing.

2. **Unconditional GitHub Actions Injection:**
   *Observation:* Running `openwiki --init` automatically attempts to write `.github/workflows/openwiki-update.yml` with a default cron schedule (`0 8 * * *`).
   *Repository Conflict:* Per ADR-013 and FBL-012, recurring model calls in CI are **not authorized** due to egress and billing boundaries.
   *Mitigation:* Suppressed in pilot configuration; automated workflows remain disabled.

3. **Default Provider Assumption:**
   *Observation:* OpenWiki defaults to OpenAI (`DEFAULT_PROVIDER = "openai"`, `model = "gpt-5.6-terra"`).
   *Repository Conflict:* Ukrainian documentation is language-adjacent; LANGUAGE-LANES rules mandate AGY Gemini Flash (`gemini-3.8-flash-high`) or Codex Astra.
   *Mitigation:* Explicit provider routing pinned in `pilot-config.json` and execution environment.

4. **Flat Authority Model:**
   *Observation:* Upstream OpenWiki treats all repository text as uniform documentation fodder. It cannot natively discern that code and config-as-policy override prose, or that live operational state must not be cached.
   *Mitigation:* Strict control brief in [`openwiki/INSTRUCTIONS.md`](INSTRUCTIONS.md) establishing binding precedence and non-authoritative locator status.

---

## 2. Pilot Scope Limitations (Allowlist v1)

1. **Code-Anchored Pages Only (Budget ≤8 Pages):**
   Allowlist v1 intentionally restricts generation to core infrastructure, static site architecture, and documentation authority. Broad narrative docs and curriculum synthesis are excluded until Wave 2a (#5539/#5540 IA reorganization) completes allowlist v2.
2. **Strict Verbatim Quoting for Ukrainian Text:**
   To eliminate hallucinated pedagogy or obsolete spelling forms, OpenWiki is prohibited from generating synthetic Ukrainian text. All Ukrainian terms must be verbatim quotes from curriculum files or VESUM.
3. **No UI Visualizer Integration:**
   While OpenWiki provides a local visualizer (`openwiki visualize`), integration into the Ops API UI (`scripts/api/docs_router.py` serving `/artifacts/openwiki/`) is deferred until an explicit **adopt** verdict is rendered.

---

## 3. Backlog for Wave 3 (#5542) and Wave 4 (#5543)

### Wave 3 (#5542 — Validation and Bounded Updates)
- [ ] **Native Runner Wrapper (`scripts/docs/run_openwiki.py`):** Author a Python runner that invokes OpenWiki in a sandboxed directory, intercepts and discards root instruction writes, and synchronizes outputs to `openwiki/**`.
- [ ] **Automated Grounding & Stack Linter (`tests/test_openwiki_grounding.py`):** Add a pytest suite to verify:
  - 100% of links in `openwiki/` resolve to real tracked git files.
  - Zero mentions of Starlight or Docusaurus as current frameworks.
  - Strict absence of synthetic Ukrainian sentences.
  - Frontmatter compliance with OKF v0.2.
- [ ] **Operator-Triggered Local Update Runbook:** Define reproducible, local-only regeneration procedures for dispatch worktrees.

### Wave 4 (#5543 — Measurement, Cutover, or Kill)
- [ ] **Three-Arm Cold-Start Measurement:** Execute comparative orientation benchmarks across:
  - Arm 1: Pre-migration baseline (captured under #5536).
  - Arm 2: Post-migration curated docs (without OpenWiki).
  - Arm 3: Post-OpenWiki pilot navigation.
- [ ] **Cutover or Kill Determination:** If Arm 3 fails to achieve non-inferior correctness at lower context tokens on benchmark questions, execute ADR-013 kill clause (delete `openwiki/` and retain deterministic index).
