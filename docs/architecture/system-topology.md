# System Topology

How the learn-ukrainian subsystems fit together. Reference diagram for new engineers and for anyone debugging cross-subsystem issues.

## High-level overview

```mermaid
graph TB
    subgraph Agents["Agent Layer"]
        Claude[Claude Code / API]
        Gemini[Gemini CLI]
        Codex[Codex CLI]
    end

    subgraph Runtime["scripts/agent_runtime/"]
        Runner[runner.invoke<br/>+ watchdog]
        Registry[adapter registry]
        Usage[usage.jsonl<br/>+ has_headroom]
    end

    subgraph Bridge["scripts/ai_agent_bridge/"]
        BridgeCLI[ask-claude<br/>ask-gemini<br/>ask-codex<br/>codex-usage]
        MsgBroker[(message_broker.db<br/>SQLite)]
    end

    subgraph Delegate["scripts/delegate.py"]
        Dispatch[dispatch fire-and-forget]
        TaskState[(batch_state/tasks/*.json)]
        TaskResults[batch_state/tasks/*.result]
    end

    subgraph Pipeline["scripts/build/ — v6 pipeline"]
        V6[v6_build.py<br/>17 phases]
        DispatchAgent[dispatch_agent]
        SessionAnalysis[session_analysis.py]
    end

    subgraph Wiki["scripts/wiki/"]
        Compile[compile.py]
        WikiSrc[sources.db<br/>SQLite FTS5<br/>660K entries]
        WikiArt[wiki/{domain}/*.md]
        WikiState[(wiki/.state/progress.db)]
    end

    subgraph Curriculum["Content"]
        Plans[plans/*.yaml]
        Activities[activities/*.yaml]
        Content[{slug}.md + vocab + review]
        Orch[orchestration/{slug}/<br/>dispatch/*.json<br/>state.json]
    end

    subgraph Monitor["scripts/api/ — Monitor API"]
        Main[main.py<br/>:8765]
        StateR[state_router]
        WikiR[wiki_router]
        RuntimeR[runtime_router]
        DelegateR[delegate_router]
        OrientR["/api/orient"]
    end

    subgraph Output["Publish"]
        Starlight[starlight/ Astro]
        MDX[*.mdx]
        JSON[vibe JSON]
    end

    subgraph RAG["MCP Sources Server"]
        RAGServer[.mcp/servers/sources/server.py<br/>:8766]
    end

    Pipeline --> DispatchAgent
    DispatchAgent --> Runner
    BridgeCLI --> Runner
    Dispatch --> Runner
    Runner --> Registry
    Registry --> Claude
    Registry --> Gemini
    Registry --> Codex
    Runner --> Usage

    BridgeCLI <--> MsgBroker
    Dispatch --> TaskState
    Dispatch --> TaskResults

    V6 --> Orch
    V6 --> SessionAnalysis
    SessionAnalysis --> Orch

    Compile --> WikiSrc
    Compile --> Runner
    Compile --> WikiArt
    Compile --> WikiState
    V6 --> WikiArt

    V6 --> Plans
    V6 --> Content
    V6 --> Activities

    Main --> StateR
    Main --> WikiR
    Main --> RuntimeR
    Main --> DelegateR
    Main --> OrientR
    StateR --> Orch
    WikiR --> WikiState
    WikiR --> WikiArt
    RuntimeR --> Usage
    DelegateR --> TaskState

    V6 --> Starlight
    Starlight --> MDX

    Gemini -.->|MCP| RAGServer
    Claude -.->|MCP| RAGServer
    RAGServer --> WikiSrc
```

## Data flows

### Building a module (v6 pipeline)

```
user → v6_build.py {level} {num}
  → loads plans/{level}/{slug}.yaml
  → loads wiki/{domain}/{slug}.md (knowledge packet)
  → dispatch_agent() per phase
    → runner.invoke() → adapter → CLI subprocess
    → watchdog drains stdout/stderr, kills on hard_timeout
    → parse_response() → ParseResult
  → writes orchestration/{slug}/dispatch/{seq}-{phase}-{ts}-meta.json
  → writes orchestration/{slug}/dispatch/{seq}-{phase}-{ts}-session-analysis.yaml (Gemini only)
  → writes content to curriculum/l2-uk-en/{level}/{slug}.md
  → writes activities/{slug}.yaml + vocabulary/{slug}.yaml + review/{slug}-review.md
  → publish step generates starlight MDX
```

### Agent orientation (one call)

```
agent → GET /api/orient
  → asyncio.gather runs in parallel:
    ├── git log + branch + ahead count
    ├── gh issue list
    ├── state_router.summary() (pipeline state)
    ├── usage.has_headroom() for each agent
    ├── list batch_state/tasks/*.json (delegations)
    ├── wiki.state.get_status_summary()
    ├── health checks (API, MCP, sources.db, broker)
    └── session-state files
  → single JSON response in <500ms
```

### Delegated task

```
claude (session) → delegate.py dispatch --agent codex --task-id issue-X
  → spawns detached worker process
  → worker writes batch_state/tasks/issue-X.json (status=spawning → running)
  → worker calls runner.invoke() → codex CLI
  → claude runs delegate.py wait in background (Bash run_in_background)
  → worker finishes, writes .result file + updates state (status=done)
  → wait process exits → claude gets <task-notification>
  → claude reads .result, verifies, commits from main session
```

### Wiki compilation

```
user → compile.py --track hist --slug kyivan-rus
  → loads sources.db chunks matching topic (SQLite FTS5)
  → builds prompt from compile_academic.md + source chunks
  → runner.invoke(gemini) → Gemini compiles article
  → writes wiki/grammar/b2/kyivan-rus.md
  → single-pass review scores the article
  → if score < 9.0: logs for --force recompile
  → updates wiki/.state/progress.db
```

## Key files

| Path | Purpose |
|------|---------|
| `scripts/build/v6_build.py` | The one pipeline entry point |
| `scripts/agent_runtime/runner.py` | The one LLM dispatch function |
| `scripts/api/main.py` | The one API server |
| `scripts/wiki/compile.py` | The one wiki compiler |
| `scripts/ai_agent_bridge/__main__.py` | The one bridge CLI |
| `scripts/delegate.py` | Fire-and-forget task runner |
| `data/sources.db` | SQLite FTS5 — 660K source chunks |
| `.mcp/servers/sources/server.py` | MCP sources tool server (port 8766) |
| `.mcp/servers/message-broker/messages.db` | Agent message broker (SQLite) |
| `batch_state/api_usage/*.jsonl` | Per-call usage records |
| `batch_state/tasks/*.json` | Delegated task state |
| `curriculum/l2-uk-en/{level}/orchestration/{slug}/` | Per-module build state |

## What's NOT in this diagram

- The Starlight frontend rendering pipeline (covered separately in `docs/architecture/ARCHITECTURE.md`)
- The playgrounds dashboard (`playgrounds/*.html`) — consumes monitor API but is frontend-only
- Historical v2-v5 pipelines — retired, see ADR-001 for why v6 replaced them
- Content generation internals (plan review, friction system, vocab enrichment) — covered in the pipeline `docs/decisions/decisions.yaml` and the best-practices guide tree

Updated: 2026-04-11
