"""Dagger module for learn-ukrainian local CI replay.

Why this exists
---------------
GHA ``Test (pytest)`` takes ~4m17s end-to-end (cold setup-python, fresh pip
install of every requirement, full sources.db build). Local pytest in
``.venv/`` is 0.19s for discovery. The gap is the dev-loop tax we pay every
time a CI-only bug needs reproduction.

Two prior approaches tried:

- **act (nektos/act)** — works for lightweight jobs (lint at 38s with
  ``--reuse``) but slower than GHA on pytest: **7m45s first run** because
  QEMU emulates amd64 on Apple Silicon and ``actions/cache@v4`` is a no-op
  under act. Also surfaces 4 environmental failures (rsync missing in the
  ``catthehacker/ubuntu:act-latest`` runner image) and 3 perf-budget
  failures under emulation. See ``docs/best-practices/local-ci-replay.md``.

- **Dagger (this module)** — runs natively on the host (Apple Silicon
  arm64 → arm64 containers if available; otherwise amd64 native via
  Rosetta which is faster than QEMU). Explicit cache volumes for pip /
  HF / venv. We define the base image so missing-tool problems (rsync)
  go away. The pipeline is Python code so we can be surgical about what
  runs and what doesn't.

Usage
-----

    dagger call pytest --source=.

The ``source`` arg is the repo root. Dagger uploads only the files
needed (driven by Python imports + explicit mounts).

Cache hints
-----------

The pip-cache volume persists across runs. First invocation pays the
full pip-download cost; second invocation is "already satisfied" and
much faster — that's the value prop over act's no-cache pip path.

References
----------

- GH issue #1891 — local CI replay decision (Dagger over act for heavy jobs).
- Companion doc: ``docs/best-practices/local-ci-replay.md``.
- ci.yml ``test`` job (lines 276-405) — the canonical pytest invocation
  we mirror here.
"""

from __future__ import annotations

import dagger
from dagger import dag, function, object_type

# ---------------------------------------------------------------------------
# Test-selection knobs — kept in sync with .github/workflows/ci.yml::test
# ---------------------------------------------------------------------------

# Tests excluded from the required-PR-gate pytest run. These depend on
# local corpora, generated review/orchestration artifacts, or sidecar
# binaries/CLIs that are not provisioned on GHA-hosted runners — and
# therefore also not in Dagger's clean container.
_IGNORED_TESTS: tuple[str, ...] = (
    "tests/test_rag.py",
    "tests/test_a1_review_scores.py",
    "tests/test_agent_runtime.py",
    "tests/test_channels_registry.py",
    "tests/test_convergence_loop.py",
    "tests/test_morphological_validator.py",
    "tests/test_plan_hash.py",
    "tests/test_scrape_diasporiana.py",
    "tests/test_v6_plan_hash_drift.py",
    "tests/test_vocab_gen.py",
    "tests/test_wiki_channels.py",
    "tests/test_wiki_enrichment.py",
    "tests/wiki/test_grade_filter.py",
    "tests/wiki/test_mlx_fault_injection.py",
    "tests/wiki/test_t1_t2_pipeline.py",
)

# Tests that need a serial process before the main xdist suite. The
# cache invalidation tests assert module-global counts. The stress
# annotation speed test measures one function's latency and is noisy
# under full-suite worker contention in local Dagger.
_FRESH_PROCESS_TESTS: tuple[str, ...] = (
    "tests/test_api_helpers.py::TestCacheFunctions::test_cache_invalidate_by_prefix",
    "tests/test_api_helpers.py::TestCacheFunctions::test_cache_invalidate_default_clears_all",
    "tests/test_stress_annotation.py::TestPerformance::test_annotation_speed",
)

# Python version pinned to match .python-version + ci.yml. Touched only
# when the project's Python pin moves.
_PYTHON_IMAGE = "python:3.12.8-slim-bookworm"

# Torch CPU wheel — same pin as ci.yml line 311-312. Fetched from the
# PyTorch CPU index instead of PyPI because the default wheel is the
# CUDA build (~2 GB) and we don't need GPU.
_TORCH_INDEX_URL = "https://download.pytorch.org/whl/cpu"
_TORCH_PIN = "torch==2.11.0"
_TORCHVISION_PIN = "torchvision==0.26.0"


@object_type
class LearnUkrainianCi:
    """Local-CI replay functions for learn-ukrainian.

    Mirrors the canonical jobs in ``.github/workflows/ci.yml`` so a
    developer can iterate on a CI-only failure locally without push
    rounds through GHA. Each function returns a Container — call
    ``.stdout()`` to materialize the run, or chain into another
    function for composition.
    """

    @function
    async def pytest(
        self,
        source: dagger.Directory,
        keyword: str = "not slow and not website",
        coverage: bool = False,
    ) -> str:
        """Run the project pytest suite in a clean container.

        Mirrors ``ci.yml::test``'s ``Run tests`` step. Returns the
        combined stdout/stderr of the test run.

        Parameters
        ----------
        source
            The repo root. Pass ``--source=.`` from the project dir.
        keyword
            ``-k`` filter expression. Default matches ci.yml: skip
            slow + website-dependent tests.
        coverage
            If true, run with ``--cov`` and a 35% floor (matches the
            push-to-main coverage step in ci.yml). Default false to
            mirror the PR-gate path (faster).
        """
        # System deps the project's tests and pip wheel-builds need:
        #   - ``rsync`` — tests/test_deploy_script_idempotency.py
        #   - ``git``   — any test that shells out to git
        #   - ``curl``, ``ca-certificates`` — live-API + HTTPS
        #   - ``nodejs``, ``npm`` — ubuntu-latest includes npx; Claude
        #     adapter tests expect that sidecar binary to be discoverable.
        #   - ``build-essential``, ``python3-dev`` — wheel-builds for
        #     pyproject-only packages without a manylinux aarch64 wheel
        #     on PyPI (e.g. ``zlib-state``). GHA's ubuntu-latest ships
        #     gcc + headers by default; slim-bookworm does not.
        #   - ``zlib1g-dev`` — header dep for the zlib-state native ext.
        # The slim image doesn't ship these; install once into a cache
        # layer so subsequent runs hit BuildKit cache.
        base = (
            dag.container()
            .from_(_PYTHON_IMAGE)
            .with_exec(["apt-get", "update"])
            .with_exec([
                "apt-get",
                "install",
                "-y",
                "--no-install-recommends",
                "rsync",
                "git",
                "curl",
                "ca-certificates",
                "nodejs",
                "npm",
                "build-essential",
                "python3-dev",
                "zlib1g-dev",
            ])
            .with_exec(["rm", "-rf", "/var/lib/apt/lists/*"])
        )

        # Persistent pip cache. Survives across dagger calls so the
        # second run pays only the actual test cost, not re-download.
        pip_cache = dag.cache_volume("learn-ukrainian-pip")

        # Mount the repo. Dagger figures out what to upload from the
        # call site; ``source`` is whatever ``--source=.`` resolves to.
        installed = (
            base.with_mounted_cache("/root/.cache/pip", pip_cache)
            .with_mounted_directory("/work", source)
            .with_workdir("/work")
            # Create the venv, then mirror ci.yml's dependency installs.
            .with_exec([
                "python3",
                "-m",
                "venv",
                "--without-pip",
                ".venv",
            ])
            .with_exec(["test", "-x", "/work/.venv/bin/python"])
            .with_exec([
                "curl",
                "-fsSL",
                "https://bootstrap.pypa.io/get-pip.py",
                "-o",
                "/tmp/get-pip.py",
            ])
            .with_exec([".venv/bin/python", "/tmp/get-pip.py"])
            .with_exec(["ls", "/work/.venv/bin/"])
            .with_exec([
                ".venv/bin/python",
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
            ])
            .with_exec([
                ".venv/bin/python",
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--index-url",
                _TORCH_INDEX_URL,
                _TORCH_PIN,
                _TORCHVISION_PIN,
            ])
            .with_exec([
                ".venv/bin/python",
                "-m",
                "pip",
                "install",
                "--no-deps",
                "-r",
                "requirements-lock.txt",
            ])
            .with_exec([
                ".venv/bin/python",
                "-m",
                "pip",
                "install",
                "multiprocess==0.70.18",
                "huggingface-hub==0.36.0",
            ])
        )

        # Build the pytest command. We run the fresh-process tests
        # first (separate process, so module-global cache/perf state is
        # clean), then the main suite.
        common_args = [
            "tests/",
            "-n",
            "auto",
            "-v",
            "--tb=short",
            "-k",
            keyword,
            *[f"--ignore={t}" for t in _IGNORED_TESTS],
            *[f"--deselect={t}" for t in _FRESH_PROCESS_TESTS],
        ]
        if coverage:
            common_args += [
                "--cov=scripts",
                "--cov-append",
                "--cov-report=term-missing",
                "--cov-fail-under=35",
            ]

        # Run fresh-process tests separately, then the main suite.
        # Single ``with_exec`` per shell so timing is honest and
        # failures surface at the right step.
        return await (
            installed.with_exec(
                [
                    ".venv/bin/python",
                    "-m",
                    "pytest",
                    *_FRESH_PROCESS_TESTS,
                    "-v",
                    "--tb=short",
                ]
            )
            .with_exec([".venv/bin/python", "-m", "pytest", *common_args])
            .stdout()
        )

    @function
    async def lint(self, source: dagger.Directory) -> str:
        """Run ruff against the project — mirrors ``ci.yml::lint``.

        Fast smoke test for the Dagger setup. Cold-run ≈10s with the
        pip cache cold; ≈3s warm. ci.yml's lint job runs in ~25-35s
        on GHA including setup-python overhead.
        """
        pip_cache = dag.cache_volume("learn-ukrainian-pip")
        return await (
            dag.container()
            .from_(_PYTHON_IMAGE)
            .with_mounted_cache("/root/.cache/pip", pip_cache)
            .with_mounted_directory("/work", source)
            .with_workdir("/work")
            .with_exec(["pip", "install", "ruff"])
            .with_exec(["ruff", "check", "."])
            .stdout()
        )
