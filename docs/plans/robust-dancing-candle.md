# Plan: Rename build_module + Discover Phase

## Context

Two changes to the v4 pipeline:

1. **Rename**: `build_module_v3.py` → `build_module.py`. The file runs v4 by default now — the v3 name is misleading.
2. **Discover phase**: Add video/blog discovery between research and content. Videos become first-class content elements planned during research, not bolted on after.

Pipeline becomes:
```
research → discover → content → activities → validate → [review] → mdx
```

GH tracking: #703 (rename), #711 (discover phase).

---

## Task 1: Rename `build_module_v3.py` → `build_module.py`

### 1.1 Git rename

```bash
git mv scripts/build_module_v3.py scripts/build_module.py
```

Update internal docstring (7 self-references in usage block).

### 1.2 Update test imports (4 files)

| File | Change |
|------|--------|
| `tests/test_build_module_v3_comprehensive.py` | `from scripts.build_module_v3 import` → `from scripts.build_module import` (~14 refs) |
| `tests/test_build_pipeline.py` | Same pattern (1 ref) |
| `tests/test_pipeline_v3.py` | Same pattern (1 ref) |
| `tests/test_v3_state.py` | Same pattern (1 ref) |

Do NOT rename test files — they describe what they test.

### 1.3 Update subprocess/path references (4 scripts)

| File | Lines | Change |
|------|-------|--------|
| `scripts/assess_research.py` | 367, 397, 510, 660 | `build_module_v3.py` → `build_module.py` |
| `scripts/preseed_runner.py` | 5, 39 | Same |
| `scripts/_archived/preseed_runner.py` | 5, 43 | Same |
| `scripts/api/comms_router.py` | 516, 525, 529 | `build_module_v3` → `build_module` (string match + regex) |

### 1.4 Update supporting files

| File | Refs |
|------|------|
| `scripts/pipeline_lib.py` | 1 (docstring) |
| `scripts/batch_gemini_config.py` | 1 (comment) |
| `claude_extensions/phases/gemini/phase-A-*.md` | 5 files (header ref) |
| `claude_extensions/hooks/check-gemini-inbox.sh` | 1 (comment) |

### 1.5 Bulk update docs (12 files)

Find-and-replace `build_module_v3` → `build_module` in:
- `docs/SCRIPTS.md` (22 refs)
- `docs/ARCHITECTURE.md` (3 refs)
- `docs/MONITOR-API.md`, `docs/ai_team/blue-team-claude.md`
- `docs/best-practices/` — 6 files (code-quality, prompt-engineering, audit-standards, context-engineering, agent-cooperation, gitflow)
- `docs/plans/robust-dancing-candle.md`
- `claude_extensions/quick-ref/monitor-api.md`

### 1.6 Update memory

Update `tasks/memory.json` entity observations (4 refs).

### 1.7 Deploy + verify

```bash
npm run claude:deploy
.venv/bin/python -m py_compile scripts/build_module.py
.venv/bin/python -m pytest tests/test_build_module_v3_comprehensive.py tests/test_build_pipeline.py tests/test_pipeline_v3.py tests/test_v3_state.py -x
```

### 1.8 What NOT to touch

- 800+ `curriculum/*/orchestration/` prompt files — historical artifacts, regenerated on next build
- Log files — historical
- `.pytest_cache/` — auto-regenerated

### 1.9 Commit

`refactor: rename build_module_v3.py to build_module.py (#703)`

---

## Task 2: Implement Discover Phase

### Architecture

Two components:
- **`scripts/video_discovery.py`** — standalone module: yt-dlp search, transcript download, Gemini scoring. Testable independently.
- **`phase_discover_v4()` in `scripts/build_module.py`** — thin wrapper calling video_discovery.py, manages state.

### 2.1 Create `scripts/video_discovery.py`

Consolidates and generalizes existing code from `auto_enrich_yt.py` and `enrich_research_yt.py`.

```python
# Key types
@dataclass
class VideoCandidate:
    url: str
    channel: str
    title: str
    transcript: str = ""
    relevance_score: float = 0.0
    relevance_note: str = ""
    transcript_excerpt: str = ""
    embed_suggestion: str = ""

@dataclass
class DiscoveryResult:
    discovered_at: str = ""
    query_keywords: list[str] = field(default_factory=list)
    videos: list[VideoCandidate] = field(default_factory=list)
    blogs: list[dict] = field(default_factory=list)  # future
    error: str | None = None
```

**Functions (all non-blocking — return empty/default on failure):**

| Function | Source | Purpose |
|----------|--------|---------|
| `clean_srt(text)` | `enrich_research_yt.py:54-77` | Strip SRT metadata, dedup lines |
| `download_transcript(url)` | `auto_enrich_yt.py` + `enrich_research_yt.py` | yt-dlp Ukrainian auto-subs → plain text |
| `filter_channels(channels, track)` | New | Filter allowlist by track relevance (`*` matches all) |
| `search_channel(keywords, channel, max_results)` | Generalized from `auto_enrich_yt.py:find_video_for_subject()` | yt-dlp search on single channel |
| `score_candidates(candidates, topic, outline, vocab, dispatch_fn)` | New | Gemini Flash relevance scoring |
| `run_discovery(topic, keywords, outline, vocab, ...)` | New | Full pipeline: search → transcript → score → rank |
| `write_discovery_yaml(result, path)` | New | Serialize to YAML |
| `read_discovery_yaml(path)` | New | Deserialize from YAML |
| `format_discovery_for_template(result)` | New | Format as markdown for `{VIDEO_DISCOVERY}` placeholder |

**Channel allowlist** (module-level constant, categorized by track relevance):

```python
DEFAULT_CHANNELS = [
    # Language learning (core A1-C2)
    {"name": "Anna Ohoiko", "handle": "@annaohoiko", "tracks": ["*"]},
    {"name": "Ukrainian with Olha", "handle": "@ukrainianwitholha", "tracks": ["*"]},
    {"name": "Let's Learn Ukrainian", "handle": "@LetsLearnUkrainian", "tracks": ["*"]},
    {"name": "Learn Ukrainian Language", "handle": "@LearnUkrainianLanguage", "tracks": ["*"]},
    {"name": "Listen & Read", "handle": "@listen-read", "tracks": ["*"]},
    {"name": "UkrainerNet", "handle": "@ukrainernet", "tracks": ["*"]},

    # History (HIST, ISTORIO, BIO)
    {"name": "Реальна Історія", "handle": "@realhistoryua", "tracks": ["hist", "istorio", "bio"]},
    {"name": "Harvard Ukrainian Research Institute", "handle": "@ukrainianresearchinstitute1041", "tracks": ["hist", "istorio", "bio", "lit"]},
    {"name": "Комік Історик", "handle": "@komikistoryk", "tracks": ["hist", "istorio", "bio"]},
    {"name": "ІМТГШ", "handle": "@imtgsh", "tracks": ["hist", "istorio"]},

    # Historical linguistics (OES, RUTH)
    {"name": "Історія Мови", "handle": "@Istoria-Movy", "tracks": ["oes", "ruth"]},

    # Culture & documentary (B2+, LIT, cultural modules)
    {"name": "Суспільне Культура", "handle": "@SuspilneKultura", "tracks": ["lit", "b2", "c1", "c2"]},
    {"name": "Суспільне Док", "handle": "@SuspilneDoc", "tracks": ["hist", "bio", "lit", "b2", "c1"]},
    {"name": "Repainted Fox", "handle": "@repaintedfox", "tracks": ["b1", "b2", "c1"]},
    {"name": "Klopotenko", "handle": "@klopotenko", "tracks": ["a2", "b1", "b2"]},
    {"name": "Radio Khartia", "handle": "@RadioKhartia", "tracks": ["lit", "c1", "c2"]},
]
```

The `tracks` field controls which channels are searched per module — a B1 grammar module won't waste time searching Реальна Історія, and an OES module will prioritize Історія Мови.

**Key design decisions:**
- `dispatch_fn` injected (not imported) — allows testing with mocks
- Flash model for scoring (cheap, this is classification not generation)
- `run_discovery()` catches all exceptions, returns `DiscoveryResult(error=...)` — non-blocking guarantee
- Transcript cap: 50,000 chars (matches existing scripts)

### 2.2 Gemini scoring prompt

**Not a template file** — assembled programmatically in `score_candidates()` (matches `_build_vocab_only_prompt()` pattern in pipeline_lib.py). Structure:

```
# Video Discovery: Relevance Scoring

## Module Context
Topic: {topic}
Sections: {outline}
Vocabulary: {vocab}

## Candidates
{for each: url, title, channel, transcript excerpt}

## Output (between delimiters)
===DISCOVERY_SCORES_START===
- video_url: "..."
  relevance_score: 0.0-1.0
  relevance_note: "..."
  embed_suggestion: "After section X — reason"
  transcript_excerpt: "..."
===DISCOVERY_SCORES_END===
```

### 2.3 Register discover phase in `scripts/build_module.py`

**Constants** (4 edits):

```python
PHASE_SEQUENCE_V4 = ["research", "discover", "content", ...]  # add "discover" at position 1

_V4_PHASE_STATE_IDS["discover"] = ["v4-discover"]
PHASE_LABELS_V4["discover"] = "Discover (video + blog search)"
PHASE_FUNCTIONS_V4["discover"] = phase_discover_v4
```

**New function `phase_discover_v4(ctx, state)`:**

- Skip if complete / `--skip-discover` / dry-run
- Extract keywords from `ctx.topic_title` + `ctx.plan["vocabulary_hints"][:5]`
- Call `run_discovery()` with `dispatch_gemini_raw` as `dispatch_fn` and `ctx.track` for channel filtering
- Write `discovery.yaml` to `ctx.orch_dir`
- Append video refs to research file
- **Always returns True** — non-blocking
- Marks phase complete even on failure (with empty discovery.yaml + error field)

**New helper `_append_discovery_to_research(ctx, result)`:**

- Appends `## Video Discovery` section to research file
- Only includes videos with `relevance_score >= 0.5`

### 2.4 Inject `{VIDEO_DISCOVERY}` into content phase

**`scripts/pipeline_lib.py` — `write_placeholders()`:**

After building placeholders dict, check `ctx.orch_dir / "discovery.yaml"`:
- If exists: `read_discovery_yaml()` → `format_discovery_for_template()` → set `VIDEO_DISCOVERY`
- If missing: `VIDEO_DISCOVERY = "(No video discoveries available)"`

**`claude_extensions/phases/gemini/phase-2-content.md`:**

Add after "Primary Source Excerpts" section:

```markdown
## Video Discoveries

{VIDEO_DISCOVERY}
```

### 2.5 CLI flag

```python
parser.add_argument("--skip-discover", action="store_true",
    help="Skip video/blog discovery phase")
```

Wire into `preflight_v4()`: `ctx.skip_discover = getattr(args, "skip_discover", False)`

Propagate in batch mode `single_args`.

### 2.6 Pipeline runner safety net

Add `"discover"` to the non-blocking phase set in `run_pipeline_v4()`:

```python
if phase_id in ("validate", "review", "discover"):
    log(f"  {phase_id}: FAIL — continuing")
    continue
```

(Safety net only — `phase_discover_v4()` already always returns True.)

### 2.7 Tests

**New file `tests/test_video_discovery.py`:**
- `test_clean_srt` — known input/output
- `test_search_channel_no_yt_dlp` — returns empty, no raise
- `test_download_transcript_failure` — returns empty, no raise
- `test_run_discovery_no_yt_dlp` — returns DiscoveryResult with error
- `test_write_read_yaml_roundtrip` — serialize/deserialize
- `test_format_empty` — fallback text
- `test_format_with_videos` — markdown output

**Add to existing test file:**
- `test_discover_in_phase_sequence` — "discover" between "research" and "content"
- `test_phase_discover_skip` — skip_discover=True → marks complete
- `test_phase_discover_dry_run` — returns True

### 2.8 Deploy + verify

```bash
npm run claude:deploy
.venv/bin/python -m py_compile scripts/build_module.py
.venv/bin/python -m py_compile scripts/video_discovery.py
.venv/bin/python scripts/build_module.py a1 1 --dry-run  # shows discover in phase list
.venv/bin/python scripts/build_module.py a1 1 --dry-run --skip-discover  # skips
```

### 2.9 Commit

`feat(pipeline): add discover phase for video/blog discovery (#711)`

---

## Execution Order

1. Steps 1.1–1.9: Rename + commit
2. Steps 2.1–2.9: Discover phase + commit

Rename first because discover adds code to the renamed file.

---

## Verification

### Rename
- [ ] `py_compile scripts/build_module.py` passes
- [ ] Tests pass: `pytest tests/test_build_module_v3_comprehensive.py tests/test_build_pipeline.py -x`
- [ ] `scripts/build_module.py a1 1 --dry-run` works
- [ ] `grep -r "build_module_v3" scripts/ tests/ docs/ claude_extensions/ --include="*.py" --include="*.sh" --include="*.md"` returns only orchestration/log files

### Discover phase
- [ ] `scripts/build_module.py a1 1 --dry-run` shows discover phase in sequence
- [ ] `--skip-discover` skips it
- [ ] `--force-phase discover` runs only discover
- [ ] `--restart-from discover` runs discover → content → ... → mdx
- [ ] `py_compile scripts/video_discovery.py` passes
- [ ] `pytest tests/test_video_discovery.py -v` passes
- [ ] Live test (with yt-dlp): `scripts/build_module.py a1 1 --force-phase discover` produces `discovery.yaml`
