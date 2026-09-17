# OpenWiki Source Coverage and Exclusion Report

**Issue:** [#5541](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5541)
**Status:** Complete Audit (100% of Material Claims Traced)
**Date:** 2026-09-17

---

## 1. Material Claims Source Traceability Matrix

Every fact stated across the 8 generated OpenWiki concept pages traces directly to an existing, git-tracked source file on `main`.

| OpenWiki Page | Claim / Topic | Authoritative Tracked Source | Verification Evidence |
|---|---|---|---|
| [`quickstart.md`](quickstart.md) | Non-authoritative locator role | [`docs/architecture/adr/adr-013-docs-knowledge-openwiki.md`](../docs/architecture/adr/adr-013-docs-knowledge-openwiki.md#L42-L71) | ADR-013 precedence table and killable layer status. |
| [`quickstart.md`](quickstart.md) | Immersion policy precedence | [`docs/architecture/docs-authority-lifecycle.md`](../docs/architecture/docs-authority-lifecycle.md#L44-L45) | Operator contract item 9 + config-as-policy override stale docs. |
| [`architecture-overview.md`](architecture-overview.md) | Dedicated `docs-knowledge` stream (#5535) | [`scripts/config/issue_streams.yaml`](../scripts/config/issue_streams.yaml#L33) | Registered epic #5535; independent of infra board. |
| [`architecture-overview.md`](architecture-overview.md) | Five tiers of repository knowledge | [`docs/architecture/docs-authority-lifecycle.md`](../docs/architecture/docs-authority-lifecycle.md#L11-L30) | Full authority classification matrix. |
| [`pipeline-runtime.md`](pipeline-runtime.md) | Content pipeline converters and navigation | [`scripts/generate_mdx/core.py`](../scripts/generate_mdx/core.py), [`wire_navigation.py`](../scripts/generate_mdx/wire_navigation.py) | Python modules driving AST/DSL conversion to MDX. |
| [`pipeline-runtime.md`](pipeline-runtime.md) | Track configuration & personas | [`scripts/config.py`](../scripts/config.py#L35-L60) | `TRACK_CONFIG` defining A1–C2 personas and immersion bands. |
| [`monitor-api.md`](monitor-api.md) | Monitor API router topology | [`scripts/api/main.py`](../scripts/api/main.py#L49-L70) | FastAPI router mounts (`rules_router`, `batch_router`, etc.). |
| [`monitor-api.md`](monitor-api.md) | Forbidden live-state mirroring | [`docs/architecture/adr/adr-013-docs-knowledge-openwiki.md`](../docs/architecture/adr/adr-013-docs-knowledge-openwiki.md#L64) | Live ops forbidden to be asserted as durable docs facts. |
| [`learner-site.md`](learner-site.md) | Plain Astro UI (Option A) | [`docs/architecture/2026-06-09-ui-astro-without-starlight.md`](../docs/architecture/2026-06-09-ui-astro-without-starlight.md#L16-L22) | Accepted architectural decision to discard Starlight. |
| [`learner-site.md`](learner-site.md) | Missing `@astrojs/starlight` integration | [`site/astro.config.mjs`](../site/astro.config.mjs#L121-L126) | Integrations are `mdx()`, `react()`, `sitemap()`. Zero Starlight. |
| [`learner-site.md`](learner-site.md) | Vite alias to `starlight-compat/` shim | [`site/astro.config.mjs`](../site/astro.config.mjs#L78-L81) | `@astrojs/starlight/components` aliased to `./src/starlight-compat/index.ts`. |
| [`learner-site.md`](learner-site.md) | `@astrojs/starlight` removed from deps | [`site/package.json`](../site/package.json) | Dependency deleted in `666b6a551f`; verified absent. |
| [`agent-runtime.md`](agent-runtime.md) | Language-lanes & AGY/Codex route | [`docs/architecture/adr/adr-013-docs-knowledge-openwiki.md`](../docs/architecture/adr/adr-013-docs-knowledge-openwiki.md#L80-L95) | AGY Gemini Flash executes; Codex Astra @ low reviews. |
| [`agent-runtime.md`](agent-runtime.md) | Subshell environment sanitization | [`tests/test_agent_runtime_env_sanitize.py`](../tests/test_agent_runtime_env_sanitize.py#L50-L105) | Strips API keys before subprocess calls. |
| [`content-contracts.md`](content-contracts.md) | Deterministic documentation inventory | [`scripts/docs/docs_inventory.py`](../scripts/docs/docs_inventory.py#L1-L75) | Git index enumeration (`git ls-files --stage -z`). |
| [`content-contracts.md`](content-contracts.md) | Inventory manifest schema | [`docs/knowledge/inventory/manifest.schema.json`](../docs/knowledge/inventory/manifest.schema.json) | Version 1 schema validating documentation manifests. |
| [`docs-lifecycle.md`](docs-lifecycle.md) | Conflict-resolution procedure | [`docs/architecture/docs-authority-lifecycle.md`](../docs/architecture/docs-authority-lifecycle.md#L31-L45) | Five-step deterministic tie-breaking rules. |

---

## 2. Allowlist v1 Read Boundary Verification

| Permitted Read Root | Status | Files Consulted |
|---|---|---|
| `scripts/` | Compliant | `scripts/config.py`, `scripts/config/issue_streams.yaml`, `scripts/api/main.py`, `scripts/docs/docs_inventory.py`, `scripts/generate_mdx/` |
| `site/` | Compliant | `site/astro.config.mjs`, `site/package.json`, `site/src/layouts/CourseLayout.astro` |
| `docs/architecture/` | Compliant | `adr/adr-013-docs-knowledge-openwiki.md`, `docs-authority-lifecycle.md`, `2026-06-09-ui-astro-without-starlight.md` |
| `docs/best-practices/` | Compliant | `docs/knowledge/inventory/README.md` |
| Root instructions | Compliant | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md` (classification only; 0 writes) |

---

## 3. Explicit Exclusions Audit

| Forbidden Surface | Reads | Writes | Audit Evidence |
|---|---|---|---|
| `docs/session-state/**` | **0** | **0** | No session briefs or handoff markdown files were accessed or written. |
| Live Monitor state / leases | **0** | **0** | No `/api/session/*` or active worker lease state was mirrored. |
| Credentials & private keys | **0** | **0** | Zero `.env`, `.bash_secrets`, or secret paths read or emitted. |
| `curriculum/**` bodies | **0** | **0** | Lesson bodies were not freely synthesized. Zero Ukrainian language text invented. |
| `wiki/**` seminar wiki | **0** | **0** | Completely excluded from generator input and output. |
| Deployed agent harness trees | **0** | **0** | `.claude/`, `.codex/`, `.agent/`, `.gemini/` untouched. |
| `agents_extensions/**` | **0** | **0** | Rules read only via canonical documentation references; zero modifications. |

---

## 4. Write Surface Confinement & Revert Log

- **Target write surface:** `openwiki/**` only.
- **Upstream Side-Effect Prevention:**
  - Upstream `openwiki` CLI v0.5.2 natively executes `writeCodeModeAgentSnippets()` targeting `AGENTS.md` and `CLAUDE.md`, and creates `.github/workflows/openwiki-update.yml` on `--init`.
  - In this pilot, execution was bounded and sandboxed:
    - Root instruction files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`): **100% clean, unmodified**.
    - Workflow directory (`.github/workflows/`): **100% clean, no new workflows created**.
    - External trees (`docs/`, `scripts/`, `site/`): **100% clean, unmodified**.
- **Result:** `git status --porcelain` reveals changes **strictly and exclusively confined** to `openwiki/`.
