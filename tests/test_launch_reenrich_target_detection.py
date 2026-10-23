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

from tests._host_path_guard import assert_no_checkout_paths, assert_no_host_facts, assert_no_host_paths

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
        (("--target", "full-catalog"), "full-catalog"),
        (("--target=full-catalog",), "full-catalog"),
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


def _primary_root_block(source: str) -> str:
    """Extract the portable PRIMARY_ROOT resolution block verbatim."""
    start = source.index('_primary_common_dir=')
    end = source.index("\n\n", start)
    return source[start:end]


def test_remote_wrapper_resolves_primary_root_portably() -> None:
    """The remote wrapper must not hardcode /Users/... primary paths (#6571).

    PRIMARY_ROOT is resolved from the shared .git common dir so the script
    works on any operator's machine. Run the resolution block against this
    worktree and confirm the result points at a real primary checkout.
    """
    source = REMOTE_LAUNCHER.read_text(encoding="utf-8")

    # Ban the hardcoded absolute path in live source.
    assert_no_checkout_paths(source)
    assert "ATLAS_PRIMARY_ROOT" in source
    assert 'git -C "$WORKTREE" rev-parse --git-common-dir' in source

    worktree = str(ROOT)
    block = _primary_root_block(source)
    proc = subprocess.run(
        ["bash", "-c", f'WORKTREE={worktree!r}\n{block}\nprintf "%s" "$PRIMARY_ROOT"'],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    resolved = Path(proc.stdout)
    # The resolved primary root owns the shared .git store (a real checkout,
    # not a worktree gitdir).
    assert resolved.is_dir()
    assert (resolved / ".git").is_dir()


def test_launchers_never_reference_teacher_product_or_home_trees() -> None:
    """Launchers must not bake teacher-product or home-directory filesystem layout."""
    for launcher in (REMOTE_LAUNCHER, LOCAL_LAUNCHER):
        text = launcher.read_text(encoding="utf-8")
        assert_no_host_facts(text, launcher.name)
        assert_no_host_paths(text)
