# Codebase Architecture Diagram

> Visual map of the learn-ukrainian repository — curriculum platform, AI content factory, and Starlight publishing site.
>
> Created: 2026-05-23
>
> **HTML version (rendered diagrams):** [`codebase-diagram.html`](codebase-diagram.html)

---

## 1. System Overview

```mermaid
flowchart TB
    subgraph Human["Human operators"]
        Architect["Claude — architect / reviewer"]
        Builder["Gemini — content builder"]
        Reviewer["Codex — adversarial reviewer"]
    end

    subgraph Orchestration["Orchestration layer"]
        Bridge["scripts/ai_agent_bridge/"]
        Runtime["scripts/agent_runtime/"]
        Monitor["Monitor API :8765"]
        Orchestrator["curriculum-orchestrator"]
    end

    subgraph Build["Build pipeline (V7)"]
        V7["scripts/build/v7_build.py"]
        Linear["scripts/build/linear_pipeline.py"]
        Audit["scripts/audit_module.py"]
    end

    subgraph Knowledge["Knowledge & grounding"]
        Plans["plans/{track}/{slug}.yaml"]
        Wiki["wiki/ + scripts/wiki/"]
        RAG["data/sources.db"]
        VESUM["VESUM / lexicon data"]
        Textbooks["Textbook RAG corpus"]
    end

    subgraph Content["Curriculum artifacts"]
        Meta["{track}/meta/{slug}.yaml"]
        MD["{track}/{slug}.md"]
        Acts["{track}/activities/{slug}.yaml"]
        Vocab["{track}/vocabulary/{slug}.yaml"]
        Status["{track}/status/{slug}.json"]
    end

    subgraph Publish["Published site"]
        MDX["starlight/src/content/docs/"]
        Components["React activity components"]
        Site["learn-ukrainian.github.io"]
    end

    Architect --> Orchestrator
    Builder --> Orchestrator
    Reviewer --> Orchestrator
    Orchestrator --> Bridge
    Bridge --> Runtime
    Runtime --> V7
    V7 --> Linear
    Plans --> V7
    Wiki --> Linear
    RAG --> Linear
    VESUM --> Audit
    Textbooks --> Linear
    Linear --> Meta
    Linear --> MD
    Linear --> Acts
    Linear --> Vocab
    Linear --> MDX
    Audit --> Status
    MDX --> Components
    Components --> Site
    Monitor --> Orchestration
    Monitor --> Build
```

---

## 2. Repository Layout

```mermaid
graph LR
    subgraph Root["learn-ukrainian/"]
        direction TB

        subgraph Curriculum["curriculum/"]
            L2EN["l2-uk-en/ — main track A1→C2 + seminars"]
            L2Direct["l2-uk-direct/ — L1-agnostic Ukrainian"]
            L1UK["l1-uk/ — Ukrainian wiki corpus"]
            WikiCur["wiki/ — compiled knowledge"]
        end

        subgraph Scripts["scripts/ (~1000+ files)"]
            BuildS["build/ — V7 pipeline"]
            AuditS["audit/ — quality gates"]
            BridgeS["ai_agent_bridge/ — inter-agent comms"]
            AgentRT["agent_runtime/ — unified CLI adapter"]
            WikiS["wiki/ — compile + review"]
            RAGS["rag/ — ingestion + search"]
            APIS["api/ — Monitor API"]
            GenMDX["generate_mdx/ — MDX assembly"]
        end

        subgraph Frontend["starlight/"]
            MDXDir["src/content/docs/"]
            ReactC["src/components/ — Quiz, Cloze, MatchUp…"]
            Lexicon["pages/lexicon/, etymology/"]
        end

        subgraph Infra["Supporting"]
            Data["data/ — sources.db, translations"]
            Schemas["schemas/ — activity YAML schemas"]
            Tests["tests/ — pytest suite"]
            Docs["docs/ — best-practices, decisions"]
            Orch["orchestration/ — build run archives"]
            GH[".github/ — CI, deploy"]
        end
    end
```

---

## 3. V7 Module Build Pipeline

Each of the **1,778 modules** flows through this linear pipeline:

```mermaid
flowchart LR
    P0["① plan<br/>Validate plans/{track}/{slug}.yaml"]
    P1["② knowledge_packet<br/>RAG + wiki manifest"]
    P2["③ writer<br/>LLM writes lesson + activities + vocab"]
    P3["④ python_qg<br/>Deterministic quality gates"]
    P4["⑤ wiki_coverage_gate<br/>Citation/grounding check"]
    P5["⑥ wiki_coverage_review<br/>Independent LLM review"]
    P6["⑦ llm_qg<br/>Adversarial multi-dim review"]
    P7["⑧ mdx<br/>Assemble → starlight/…/slug.mdx"]

    P0 --> P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7

    P2 -.->|"claude / gemini / codex / grok…"| Writers["AI writers via agent_runtime"]
    P3 -.->|"audit_module.py checks"| Gates["Word count, Russianisms,<br/>activity pedagogy, VESUM…"]
    P7 -.->|"React components"| Live["Published lesson page"]
```

### Per-module artifact chain

Inside `curriculum/l2-uk-en/`:

```mermaid
flowchart TD
    Plan["plans/{track}/{slug}.yaml<br/>SOURCE OF TRUTH (immutable)"]
    Meta["{track}/meta/{slug}.yaml<br/>Structural blueprint"]
    Lesson["{track}/{num}-{slug}.md<br/>Lesson prose"]
    Activities["{track}/activities/{slug}.yaml<br/>Interactive exercises"]
    Vocabulary["{track}/vocabulary/{slug}.yaml<br/>Word list + morphology"]
    Review["{track}/review/{slug}-review.md<br/>Adversarial review"]
    MDXOut["starlight/src/content/docs/{track}/{slug}.mdx<br/>PUBLISHED OUTPUT"]

    Plan --> Meta --> Lesson
    Lesson --> Activities
    Lesson --> Vocabulary
    Activities --> Review
    Review --> MDXOut
```

---

## 4. Curriculum Tracks

22 tracks, 1,778 modules:

```mermaid
mindmap
  root((learn-ukrainian))
    Core CEFR
      A1 — 55 modules — PPP
      A2 — 69 modules — PPP
      B1 — 94 modules — TTT
      B2 — 93 modules — TTT
      C1 — 132 modules — CLIL
      C2 — 110 modules — CLIL
    Seminar tracks
      HIST — Ukrainian history
      BIO — Notable Ukrainians
      ISTORIO — Historiography
      LIT — Literature + 7 sub-tracks
      FOLK — Folk culture
      OES — Old East Slavic
      RUTH — Ruthenian
    Other
      l2-uk-direct — L1-agnostic B2
      l1-uk — Wiki corpus only
```

---

## 5. Multi-Agent Architecture

```mermaid
flowchart TB
    subgraph Agents["AI agents"]
        Claude["Claude Opus 4.7<br/>Architect, plan review, orchestration"]
        Gemini["Gemini 3.1 Pro<br/>Primary content writer"]
        Codex["Codex<br/>Adversarial reviewer, bug hunter"]
        Others["Grok, DeepSeek, Qwen…<br/>Bakeoff / alternate writers"]
    end

    subgraph Comms["Communication"]
        AB["ai_agent_bridge<br/>SQLite message broker"]
        Discuss["ab discuss — multi-agent deliberation"]
        Delegate["delegate.py — worktree dispatch"]
    end

    subgraph Runtime["agent_runtime/"]
        Invoke["runner.invoke()"]
        Adapters["adapters/ — claude, codex, gemini…"]
        Registry["registry.AGENTS"]
    end

    subgraph Isolation["Isolation"]
        WT[".worktrees/dispatch/{agent}/{task}/"]
        BuildWT[".worktrees/builds/{level}-{slug}/"]
    end

    Claude --> AB
    Gemini --> AB
    Codex --> AB
    AB --> Invoke
    Delegate --> Invoke
    Invoke --> Adapters
    Adapters --> Registry
    Invoke --> WT
    V7Build["v7_build.py --worktree"] --> BuildWT
```

---

## 6. Frontend (Starlight / Astro)

```mermaid
flowchart LR
    subgraph Input
        MDX["MDX lesson files"]
        YAML["Activity YAML"]
        JSON["curriculum-stats.json<br/>vesum-vocab-lemmas.json"]
    end

    subgraph Starlight["starlight/"]
        Astro["Astro pages"]
        Content["content/docs/{track}/"]
        Comp["40+ React components"]
    end

    subgraph Components["Activity types"]
        Quiz["Quiz, TrueFalse, Cloze"]
        Match["MatchUp, GroupSort, Anagram"]
        Write["FillIn, Translate, EssayResponse"]
        Read["ReadingActivity, DialogueBox"]
        Lit["SourceBox, PaleographyAnalysis"]
    end

    subgraph Pages["Special pages"]
        Home["/ — LevelLanding"]
        Lex["/lexicon — VESUM lookup"]
        Etym["/etymology — word origins"]
    end

    MDX --> Content
    YAML --> Comp
    JSON --> Lex
    Content --> Astro
    Comp --> Components
    Astro --> Home
    Astro --> Lex
    Astro --> Etym
    Astro --> Deploy["GitHub Pages deploy"]
```

---

## 7. Data & Validation Layer

```mermaid
flowchart TB
    subgraph Sources["Grounding sources"]
        SS2024["Ukrainian State Standard 2024"]
        TB["Textbook RAG — data/sources.db"]
        UW["ukrainian_wiki corpus — A1/A2"]
        LitRAG["Literary RAG"]
        VESUM2["VESUM morphological dictionary"]
    end

    subgraph Validation["Quality gates"]
        AuditMod["audit_module.py"]
        Pipeline["npm run pipeline"]
        ValidateYAML["validate_yaml / validate_plans"]
        LintMD["markdownlint + yamllint"]
        PreCommit[".pre-commit-config.yaml"]
    end

    subgraph CI["CI / monitoring"]
        Pytest["pytest — 200+ test files"]
        MonitorAPI["Monitor API — track health, build status"]
        Dashboards["dashboards/ — build analytics"]
    end

    Sources --> AuditMod
    AuditMod --> Pipeline
    Pipeline --> ValidateYAML
    ValidateYAML --> LintMD
    LintMD --> PreCommit
    PreCommit --> Pytest
    MonitorAPI --> Dashboards
```

---

## Key Takeaways

| Layer | Role |
| --- | --- |
| `curriculum/` | Authoring source — plans, lessons, activities, vocab |
| `scripts/build/` | V7 linear pipeline — plan → writer → QG → MDX |
| `scripts/audit/` | Deterministic quality gates (word counts, pedagogy, Russianisms) |
| `scripts/agent_runtime/` | Single entrypoint for all AI CLI invocations |
| `scripts/ai_agent_bridge/` | Inter-agent messaging and dispatch |
| `starlight/` | Astro site with 40+ interactive React activity components |
| `data/` | RAG corpora, translations, lexicon databases |
| `docs/` | Best practices, architectural decisions, agent protocols |

---

## Related docs

- [`system-topology.md`](system-topology.md) — agent/runtime/bridge wiring (V6-era reference)
- [`v7-pipeline.md`](v7-pipeline.md) — V7 build pipeline details
- [`track-architecture.md`](../best-practices/track-architecture.md) — track/level structure and pedagogy models
- [`agent-runtime-guide.md`](../agent-runtime-guide.md) — `runner.invoke()` mental model
