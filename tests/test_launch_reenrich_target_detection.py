"""Target-detection regression test for the #6466 campaign launcher scripts.

Root cause covered: both launcher scripts used to hardcode
``--target missing-translation`` + ``--slugs-file <residual dump>``
unconditionally. A caller passing ``--target full-catalog`` (the #6466
runbook's own documented invocation) would still get the stale residual
slugs-file filter applied on top, silently narrowing a "full catalog" run
down to whatever small residual set happened to be on disk -- exit 0, looks
done, campaign result is wrong. These scripts have no existing pytest
coverage (they are VPS-side bash, not imported Python), so this drives them
via subprocess with a ``--print-target`` debug hook that exits before any
filesystem/systemd side effect.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LOCAL_LAUNCHER = ROOT / "scripts" / "lexicon" / "runner" / "launch_reenrich_class_b.sh"
REMOTE_LAUNCHER = ROOT / "scripts" / "lexicon" / "runner" / "launch_reenrich_class_b_remote.sh"


def _run_local_launcher(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": "/usr/bin:/bin",
        "ATLAS_REPO": str(tmp_path),
        "ATLAS_RUN_ROOT": str(tmp_path),
    }
    return subprocess.run(
        ["bash", str(LOCAL_LAUNCHER), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env=env,
    )


@pytest.mark.parametrize(
    "args,expected_target",
    [
        ((), "missing-translation"),
        (("--limit", "5"), "missing-translation"),
        (("--target", "full-catalog"), "full-catalog"),
        (("--target=full-catalog",), "full-catalog"),
        (("--target", "full-catalog", "--limit", "10"), "full-catalog"),
        (
            ("--target=missing-anchor", "--target", "full-catalog"),
            "full-catalog",
        ),
        (("--target", "missing-anchor"), "missing-anchor"),
    ],
)
def test_local_launcher_resolves_target(tmp_path: Path, args: tuple[str, ...], expected_target: str) -> None:
    proc = _run_local_launcher(tmp_path, *args, "--print-target")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == expected_target


def test_full_catalog_does_not_carry_slugs_file(tmp_path: Path) -> None:
    """The bug this test guards: --target full-catalog must never also
    inject --slugs-file into the driver invocation (see reenrich_thin_entries
    -- a slug_filter silently narrows an already-selected target list)."""
    proc = _run_local_launcher(tmp_path, "--target=full-catalog", "--print-target")
    assert proc.returncode == 0, proc.stderr
    # The print-target hook exits before COMMON_ARGS is built, so this test
    # also asserts the source directly reflects the guard, since the
    # constructed argv itself is not observable via --print-target alone.
    source = LOCAL_LAUNCHER.read_text(encoding="utf-8")
    guard = 'if [[ "$TARGET" == "missing-translation" ]]; then'
    slugs_line = 'COMMON_ARGS+=(--slugs-file "$SLUGS_FILE")'
    assert guard in source
    assert slugs_line in source
    # The slugs-file append must be textually inside the missing-translation
    # guard block, not unconditional at COMMON_ARGS construction time.
    guard_idx = source.index(guard)
    unconditional_common_args = 'COMMON_ARGS=(\n  --manifest "$WORK_MANIFEST"\n  --local\n  --target "$TARGET"\n  --sources-db "$SOURCES_DB"\n  --write\n)'
    assert unconditional_common_args in source
    assert source.index(slugs_line) > guard_idx


@pytest.mark.parametrize(
    "args,expected_target",
    [
        ([], "missing-translation"),
        (["--limit", "10"], "missing-translation"),
        (["--target", "full-catalog"], "full-catalog"),
        (["--target=full-catalog"], "full-catalog"),
        (["--target", "full-catalog", "--limit", "10"], "full-catalog"),
        (["--target=missing-anchor", "--target", "full-catalog"], "full-catalog"),
    ],
)
def test_remote_target_detection(args: list[str], expected_target: str) -> None:
    """The remote wrapper's own TARGET detection (used to gate the residual
    slugs-file sync/require) must resolve identically to the local
    launcher's for the same argv -- verified by sourcing just the detection
    block so this doesn't require a real SSH host."""
    source = REMOTE_LAUNCHER.read_text(encoding="utf-8")
    start = source.index('TARGET="missing-translation"')
    end = source.index("\n\n", start)
    detection_block = source[start:end]
    script = (
        'EXTRA_ARGS=("$@")\n'
        f"{detection_block}\n"
        'printf "%s\\n" "$TARGET"\n'
    )
    proc = subprocess.run(
        ["bash", "-c", script, "--", *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == expected_target


def test_remote_wrapper_skips_residual_requirement_for_full_catalog() -> None:
    source = REMOTE_LAUNCHER.read_text(encoding="utf-8")
    assert 'if [[ "$TARGET" == "missing-translation" ]]; then' in source
    # The residual-dump existence check and its scp must both be nested
    # inside that guard, not unconditional.
    guard_idx = source.index('if [[ "$TARGET" == "missing-translation" ]]; then')
    residual_check_idx = source.index("local residual dump not found")
    residual_scp_idx = source.index('scp_q "$LOCAL_RESIDUAL"')
    assert residual_check_idx > guard_idx
    assert residual_scp_idx > guard_idx
