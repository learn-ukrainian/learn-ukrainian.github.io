---
type: Reference
title: OpenWiki Quickstart and Repository Navigator
description: Non-authoritative navigation portal and entrypoint for code-anchored repository knowledge under allowlist v1.
tags: [quickstart, navigation, entrypoint, architecture, docs-knowledge]
---

# OpenWiki Quickstart and Repository Navigator

> [!IMPORTANT]
> **Non-Authoritative Locator Notice**
> This directory (`openwiki/`) is a killable, non-authoritative navigation and synthesis layer generated under [ADR-013](../docs/architecture/adr/adr-013-docs-knowledge-openwiki.md). It does not establish binding repository policy, does not override code or configuration, and never breaks ties during conflict resolution. For any load-bearing task, consult the cited git-tracked source files directly.

## Welcome to learn-ukrainian

The `learn-ukrainian` repository powers a comprehensive, open-source Ukrainian language learning platform. It encompasses static site generation, content authoring pipelines, automated linguistic verification, learner tracking, and multi-agent coordination tooling.

### Repository Knowledge Map (Allowlist v1 Core Pages)

This pilot covers the code-anchored allowlist v1 surface (≤8 pages). Explore the focused domain guides below:

1. [Architecture Overview](architecture-overview.md)
   High-level architectural structure, separation of concerns, stream governance ([`scripts/config/issue_streams.yaml`](../scripts/config/issue_streams.yaml)), and architectural decision records ([ADR-013](../docs/architecture/adr/adr-013-docs-knowledge-openwiki.md)).

2. [Learner Site & UI Architecture](learner-site.md)
   Plain Astro static builder architecture ([`site/astro.config.mjs`](../site/astro.config.mjs)), custom [`CourseLayout.astro`](../site/src/layouts/CourseLayout.astro), de-Starlight verification ([`docs/architecture/2026-06-09-ui-astro-without-starlight.md`](../docs/architecture/2026-06-09-ui-astro-without-starlight.md)), and search index routing.

3. [Pipeline & Build Runtime](pipeline-runtime.md)
   Curriculum MDX generation ([`scripts/generate_mdx/`](../scripts/generate_mdx/)), build orchestration ([`scripts/build/`](../scripts/build/)), and config-as-policy knobs ([`scripts/config.py`](../scripts/config.py)).

4. [Monitor API & Tooling Surface](monitor-api.md)
   FastAPI operational server structure ([`scripts/api/main.py`](../scripts/api/main.py)), router inventory, and static contracts. (Live leases and session streams are strictly non-authoritative here).

5. [Agent Runtime & Security Harness](agent-runtime.md)
   Agent bridging mechanisms ([`scripts/ai_agent_bridge/`](../scripts/ai_agent_bridge/)), environment sanitization ([`tests/test_agent_runtime_env_sanitize.py`](../tests/test_agent_runtime_env_sanitize.py)), and secret protection rules.

6. [Content Quality & Contracts](content-contracts.md)
   Linguistic verification gates, deterministic documentation inventory ([`scripts/docs/docs_inventory.py`](../scripts/docs/docs_inventory.py)), and quality assurance scripts ([`scripts/audit/`](../scripts/audit/)).

7. [Documentation Authority & Lifecycle](docs-lifecycle.md)
   Hierarchy of repository truth ([`docs/architecture/docs-authority-lifecycle.md`](../docs/architecture/docs-authority-lifecycle.md)), conflict resolution rules, and the worked immersion policy example.

---

## Fast Orientation for AI Agents

When answering questions or planning changes, follow this rapid sequence:

```mermaid
flowchart TD
    A["Agent Query"] --> B{"Fact Category?"}
    B -->|"Behavioral / Code"| C["Read Code & Tests in scripts/ or site/"]
    B -->|"Config / Policy"| D["Read scripts/config.py (Config-as-Policy)"]
    B -->|"UI Framework"| E["Plain Astro (site/src/layouts/CourseLayout.astro)"]
    B -->|"Live State / Leases"| F["Query Monitor API live (NEVER OpenWiki)"]
    B -->|"Docs Navigation"| G["Consult OpenWiki as Locator, then verify cited source"]
```

### Key Truth Invariants
- **Learner UI:** Plain Astro builder (`site/`). Starlight integration is deleted; `@astrojs/starlight` exists solely as a Vite alias to [`site/src/starlight-compat/index.ts`](../site/src/starlight-compat/index.ts).
- **Immersion Policy:** Config-as-policy in [`scripts/config.py`](../scripts/config.py) (`IMMERSION_POLICIES`) and operator expectations win over narrative docs.
- **Rules:** Source rules live in [`agents_extensions/shared/rules/`](../agents_extensions/shared/rules/) and serve via `/api/rules`; `.claude/`, `.codex/`, `.gemini/` are deployed mirror copies.
