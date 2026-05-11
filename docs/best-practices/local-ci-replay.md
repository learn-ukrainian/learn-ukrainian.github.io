# Local CI Replay with Dagger

> **TL;DR.** `dagger call pytest --source=.` runs the full pytest suite in
> a native arm64 container with a persistent pip cache. First run on
> Apple Silicon: **3m15s** (vs ~4m17s on GHA, vs 7m45s with `act`).
> Tracked under [#1891][issue-1891].
>
> History: we tried `act` (nektos/act) first and shipped it under #1892 +
> #1893. Measured timings revealed act was **slower than GHA** on heavy
> jobs (7m45s vs 4m17s) due to QEMU emulating amd64 on Apple Silicon
> plus `actions/cache@v4` being a no-op. We pivoted to Dagger after the
> user confirmed it worked well in another project — native arm64 wins
> structurally. The act setup was removed in the same PR.

[issue-1891]: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1891

---

## Why Dagger over act on Apple Silicon

Three structural wins:

| Concern | act | Dagger |
|---|---|---|
| Architecture | amd64 emulated via QEMU on arm64 host (~2-3× slower for CPU-bound steps) | Native aarch64 — uses your CPU directly |
| Caching | `actions/cache@v4` is a no-op; pip wheels re-download every cold run | Explicit `cache_volume` mounts — pip cache survives cold container restarts |
| Runner image | `ghcr.io/catthehacker/ubuntu:act-latest` — missing rsync, no control over installed tools | You pin the base image and apt packages — `python:3.12.8-slim-bookworm + build-essential + python3-dev + zlib1g-dev` for us |

These translate to: act first-run pytest at **7m45s with 7 failures**
(4× rsync-missing + 3× perf budgets violated by emulation) versus
Dagger first-run pytest at **3m15s with 4 failures** (3× claude-binary
not in path, 1× borderline perf at 15.30s vs 15.0s budget).

## Setup (one-time)

```bash
brew install dagger      # macOS host (or `curl -L https://dl.dagger.io/dagger/install.sh | sh`)
```

You also need a container daemon (Docker Desktop, OrbStack, or any
BuildKit-compatible runtime). OrbStack is recommended on macOS — Dagger
auto-detects it.

Verify:

```bash
dagger version           # expect v0.20.x
dagger functions         # lists the project's pipeline functions
```

## Common commands

```bash
# Lint (smoke test for the setup) — ~34s cold, ~10s warm
dagger call lint --source=.

# Run the full pytest suite — first run ~3m15s, warm-cache runs faster
dagger call pytest --source=.

# Pass through pytest's -k filter
dagger call pytest --source=. --keyword='not slow and not website'

# Run with coverage (matches ci.yml's push-to-main coverage step)
dagger call pytest --source=. --coverage=true
```

## Measured timings

### `pytest` job

| Run | Description | Real time |
|---|---|---|
| 1 (build fail) | First attempt — wheel build error on `zlib-state` (missing gcc); proved Dagger's speed in failure mode | 1m19s to fail |
| 2 (cold) | apt cache cold, pip cache cold, full install + test suite | **3m15s** total — 1m45s in pytest proper |
| 3 (warm) | pip cache hits "already satisfied" path; apt and base image layer-cached | **2m23s** total — 2m05s in pytest proper |

The warm-cache run saves ~52s vs cold (pip install drops to near-zero
because wheels are already in the cache volume). Pytest itself is
~roughly host-load-flaky between runs (1m45s ↔ 2m05s).

For comparison: GHA pytest is ~4m17s. act pytest was **7m45s** first
run with no cache benefit on subsequent runs because act ignores
`actions/cache@v4`. Net win: **Dagger warm is ~1.8× faster than GHA cold
and ~3.2× faster than act**.

### `lint` job (smoke test)

| Run | Description | Real time |
|---|---|---|
| 1 (cold) | Pull base image + apt + install ruff + run | **34s** |

## Pipeline definition

The pipeline lives in `.dagger/src/learn_ukrainian_ci/main.py` and uses
the Dagger Python SDK. Each `@function`-decorated method becomes a
callable subcommand. Key design choices, all documented inline in the
module:

- **Base image** pinned to `python:3.12.8-slim-bookworm` — matches
  `.python-version` and `ci.yml`'s setup-python pin.
- **apt deps**: `rsync git curl ca-certificates build-essential
  python3-dev zlib1g-dev`. GHA's `ubuntu-latest` ships these by default;
  slim does not.
- **Torch CPU wheel** installed first with `--no-deps` from PyTorch's
  CPU index (`https://download.pytorch.org/whl/cpu`) — matches
  `ci.yml::test` lines 311-312.
- **Persistent pip cache** via `dag.cache_volume("learn-ukrainian-pip")`
  mounted at `/root/.cache/pip`. This survives across `dagger call`
  invocations.
- **Test selection** mirrors `ci.yml::test` exactly: same `-k` filter,
  same `--ignore=` list, same fresh-process tests run separately.

## Known failure modes under Dagger (first-run, 2026-05-12)

Three categories, three different fixes:

| Tests | Cause | Fix |
|---|---|---|
| 3× `test_agent_runtime_effort.py` | Tests instantiate `ClaudeAdapter`, which requires `npx`/`claude` binary on PATH. Slim container doesn't have Node.js. | Add `nodejs` to the apt install, OR `npm install -g @anthropic-ai/claude-code`. Tracked separately — these tests already skip cleanly on GHA via a different mechanism. |
| 1× `test_annotation_speed` | Perf budget 15.0s — on this host runs at 15.30s natively. Same test under act (QEMU emulated) runs at 27s; under GHA at ~9-12s. | Either bump the budget to 20s, or skip under `LOCAL_CI_REPLAY=1` env. Borderline; flaky depending on host load. |

## Lifting to another project

Copy `.dagger/` and `dagger.json` into the target project. Modify
`.dagger/src/<module-name>/main.py`:

1. Update `_PYTHON_IMAGE` to the target project's pin.
2. Update apt-deps list for the target's wheel-build needs (run pytest
   once and let the build errors tell you).
3. Update `_TORCH_PIN` if the project uses different torch or no torch.
4. Update `_IGNORED_TESTS` and `_FRESH_PROCESS_TESTS` to match the
   target's `ci.yml::test`.

Then `dagger develop` regenerates the SDK runtime and `dagger functions`
verifies the discovery.

The pipeline-as-code pattern is the value prop: same Dagger module runs
identically on laptop + GHA (when we eventually add a Dagger GHA action)
+ any other Dagger-compatible runtime. No fork between local and
production pipelines.
