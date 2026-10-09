"""Frontend CI hydrates and builds once and reuses only a verified build (#9718)."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.repo_invariant

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github/workflows/ci.yml"
PACKAGE = ROOT / "site/package.json"
VITEST_CONFIG = ROOT / "site/vitest.config.ts"
BUILD_RENDERS = ROOT / "site/tests/unit/build-renders.test.ts"

STEP = "Build, drift check, unit and built-output tests"
HELPER = "tests/helpers/ci-build-artifact.ts"
DRIFT = "git diff --exit-code -- src/data/lexicon-teacher-lesson-keys.json src/data/practice-zno-meta.json"
UNIT_VITEST = (
    "vitest run --exclude tests/unit/build-renders.test.ts --exclude tests/unit/etymology-handler-built-output.test.ts"
)
# A4: bounded file parallelism for the CI unit command only. Three workers leave one of
# the 4-vCPU runner's cores to the Vitest main process (Vitest's own cores-1 default).
UNIT_CI_PARALLELISM = "--fileParallelism --maxWorkers=3"

# build-renders.test.ts as of bec14d5a24 (before #9718): test names, assertions and
# error patterns that must keep running unchanged against the build they check.
ORIGINAL_TEST_NAMES = (
    "astro build succeeds with zero errors",
    "generates expected page count",
    "no pages have rendering errors in output",
    "renders Starlight tabs for lesson pages instead of raw tab markers",
    "renders /a1/weather/ as an arc module page without raw tab markers",
    "renders directive admonitions instead of raw directive markers",
)
ORIGINAL_ASSERTIONS = (
    "expect(buildExitCode).toBe(0);",
    "expect(errorLines).toEqual([]);",
    "expect(pageCount).toBeGreaterThanOrEqual(10);",
    "expect(matches, `Build output contains: ${pattern}`).toBeNull();",
    "expect(existsSync(lessonPage), `no tabbed lesson page found: ${lessonPage}`).toBe(true);",
    "expect(html).not.toContain('starlight-tab-item');",
    "expect(html).toContain('role=\"tablist\"');",
    'expect((html.match(/class="lu-tab-panel"/g) || []).length).toBeGreaterThan(0);',
    "expect(existsSync(weatherPage), `missing ${weatherPage}`).toBe(true);",
    "expect(html).toContain('data-arc-module=\"weather\"');",
    "expect(html).not.toContain('starlight-tab-item');",
    "expect(html).not.toContain('role=\"tablist\"');",
    "expect(html).not.toContain('lu-tab-panel');",
    "expect(rawMatches).toEqual([]);",
    "expect(renderedAdmonitionCount).toBeGreaterThan(0);",
)
ORIGINAL_ERROR_PATTERNS = (
    "/Caught error rendering/,",
    "/Cannot read properties of undefined/,",
    "/UnknownContentCollectionError/,",
    "/is not a function/,",
    "/Module not found/,",
)


def frontend_jobs_steps() -> list[dict]:
    return yaml.safe_load(CI.read_text(encoding="utf-8"))["jobs"]["frontend"]["steps"]


def build_step() -> dict:
    return next(step for step in frontend_jobs_steps() if step.get("name") == STEP)


def run_lines(step: dict) -> list[str]:
    joined = re.sub(r"\\\n\s*", "", step["run"])
    return [line.strip() for line in joined.splitlines() if line.strip()]


def site_scripts() -> dict[str, str]:
    return json.loads(PACKAGE.read_text(encoding="utf-8"))["scripts"]


def clean_git_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def test_ci_hydrates_and_builds_once_then_reuses_the_verified_build() -> None:
    step = build_step()
    assert step["working-directory"] == "site"
    assert step["env"]["FRONTEND_BUILD_RECORD"].startswith("${{ runner.temp }}/")
    assert run_lines(step) == [
        "set -euo pipefail",
        "npm run hydrate",
        f'node --experimental-strip-types {HELPER} record --record "$FRONTEND_BUILD_RECORD" -- npm run astro -- build',
        DRIFT,
        "npm run test:unit:ci",
        f'node --experimental-strip-types {HELPER} verify --record "$FRONTEND_BUILD_RECORD"',
        "npm run test:built-output",
    ]
    assert site_scripts()["astro"] == "astro"
    job_runs = "\n".join(step.get("run", "") for step in frontend_jobs_steps())
    assert job_runs.count("npm run hydrate") == 1
    assert "npm run build" not in job_runs
    assert re.search(r"npm run test:unit(?!:ci)", job_runs) is None


def test_default_site_commands_stay_self_contained() -> None:
    scripts = site_scripts()
    assert scripts["build"] == "npm run hydrate && astro build"
    assert scripts["test"] == "npm run test:unit && npm run test:built-output"
    assert scripts["test:unit"] == f"npm run hydrate && {UNIT_VITEST}"
    assert scripts["test:built-output"] == (
        "vitest run tests/unit/build-renders.test.ts tests/unit/etymology-handler-built-output.test.ts"
    )
    config = VITEST_CONFIG.read_text(encoding="utf-8")
    assert re.search(r"^\s*fileParallelism: false,$", config, re.M)
    # Per-file isolation stays on: several unit files set process.env.
    assert "isolate" not in config


def test_ci_unit_command_verifies_then_runs_the_same_selection_in_parallel_without_hydrate() -> None:
    scripts = site_scripts()
    verify, vitest = scripts["test:unit:ci"].split(" && ")
    assert verify == f'node --experimental-strip-types ./{HELPER} verify --record "$FRONTEND_BUILD_RECORD"'
    assert scripts["test:unit"].removeprefix("npm run hydrate && ") == UNIT_VITEST
    assert vitest == UNIT_VITEST.replace("vitest run", f"vitest run {UNIT_CI_PARALLELISM}", 1)
    assert "isolate" not in vitest


def test_build_renders_keeps_original_tests_and_assertions() -> None:
    source = BUILD_RENDERS.read_text(encoding="utf-8")
    assert tuple(re.findall(r"^  it\('([^']+)'", source, re.M)) == ORIGINAL_TEST_NAMES
    assert tuple(line.strip() for line in source.splitlines() if "expect(" in line) == ORIGINAL_ASSERTIONS
    assert tuple(line.strip() for line in source.splitlines() if re.fullmatch(r"\s*/.+/,", line)) == (
        ORIGINAL_ERROR_PATTERNS
    )


def test_build_renders_builds_itself_only_without_a_record() -> None:
    source = BUILD_RENDERS.read_text(encoding="utf-8")
    assert source.count("execSync(") == 1
    assert source.count("verifyBuildRecord(") == 1
    standalone = source.index("if (BUILD_RECORD === undefined) {")
    build = source.index("execSync('npm run build 2>&1', {")
    assert standalone < build
    assert "env: { ...process.env, ATLAS_MANIFEST_ALLOW_STALE_POINTER: '1' }," in source
    assert "timeout: 360000," in source
    reuse = source.index("if (BUILD_RECORD !== undefined) {")
    assert source.index("beforeAll(() => {", reuse) < source.index("verifyBuildRecord(BUILD_RECORD)") < standalone


def test_drift_check_fails_on_generated_teacher_key_drift(tmp_path: Path) -> None:
    site = tmp_path / "site"
    (site / "src/data").mkdir(parents=True)
    teacher_keys = site / "src/data/lexicon-teacher-lesson-keys.json"
    teacher_keys.write_text('{"keys": []}\n', encoding="utf-8")
    (site / "src/data/practice-zno-meta.json").write_text("{}\n", encoding="utf-8")
    env = clean_git_env()
    git = ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false"]
    for args in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "fixture"]):
        subprocess.run([*git, *args], cwd=tmp_path, env=env, check=True, timeout=60)
    drift = shlex.split(next(line for line in run_lines(build_step()) if line.startswith("git diff")))

    assert subprocess.run(drift, cwd=site, env=env, capture_output=True, timeout=60).returncode == 0
    teacher_keys.write_text('{"keys": ["drifted"]}\n', encoding="utf-8")
    assert subprocess.run(drift, cwd=site, env=env, capture_output=True, timeout=60).returncode == 1
