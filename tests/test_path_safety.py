"""Regression tests for the shared destructive-path guard."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.hygiene import lint_raw_rm_rf
from scripts.path_safety import assert_delete_target

pytestmark = pytest.mark.repo_invariant


def test_delete_guard_allows_descendants_of_standard_and_approved_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    worktree = repo_root / ".worktrees" / "dispatch" / "codex" / "task"
    batch_temp = repo_root / "batch_state" / "tmp" / "render"
    approved_temp = tmp_path / "approved-temp" / "staging"
    tmpdir = tmp_path / "process-tmp"
    monkeypatch.setenv("TMPDIR", str(tmpdir))

    assert assert_delete_target(worktree, repo_root=repo_root) == worktree.resolve()
    assert assert_delete_target(batch_temp, repo_root=repo_root) == batch_temp.resolve()
    assert assert_delete_target(tmpdir / "payload", repo_root=repo_root) == (tmpdir / "payload").resolve()
    assert (
        assert_delete_target(
            approved_temp,
            repo_root=repo_root,
            approved_temp_roots=(tmp_path / "approved-temp",),
        )
        == approved_temp.resolve()
    )


@pytest.mark.parametrize(
    ("target_factory", "message"),
    [
        (lambda repo_root: "", "empty"),
        (lambda repo_root: ".", "current directory"),
        (lambda repo_root: "$TMPDIR", "unexpanded shell variable"),
        (lambda repo_root: repo_root, "repository root"),
        (lambda repo_root: repo_root / ".worktrees", "not the root itself"),
        (lambda repo_root: Path.home(), "home directory"),
        (lambda repo_root: Path("/etc"), "outside approved"),
    ],
)
def test_delete_guard_refuses_catastrophic_or_unapproved_targets(
    tmp_path: Path,
    target_factory,
    message: str,
) -> None:
    repo_root = tmp_path / "repo"

    with pytest.raises(ValueError, match=message):
        assert_delete_target(target_factory(repo_root), repo_root=repo_root)


def test_symlink_escape_is_blocked(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    worktrees = repo_root / ".worktrees"
    worktrees.mkdir(parents=True)
    (worktrees / "escape").symlink_to(Path("/etc"), target_is_directory=True)

    with pytest.raises(ValueError, match="outside approved"):
        assert_delete_target(worktrees / "escape", repo_root=repo_root)


@pytest.mark.parametrize(
    ("tmpdir", "approved_temp_roots"),
    [
        ("/", ()),
        (None, (Path("/"),)),
    ],
)
def test_delete_guard_refuses_filesystem_root_as_a_temp_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmpdir: str | None,
    approved_temp_roots: tuple[Path, ...],
) -> None:
    """Neither $TMPDIR nor an explicit root can allow arbitrary deletion."""
    repo_root = tmp_path / "repo"
    arbitrary_target = tmp_path / "arbitrary-target"
    if tmpdir is None:
        monkeypatch.delenv("TMPDIR", raising=False)
    else:
        monkeypatch.setenv("TMPDIR", tmpdir)

    with pytest.raises(ValueError, match="filesystem root"):
        assert_delete_target(
            arbitrary_target,
            repo_root=repo_root,
            approved_temp_roots=approved_temp_roots,
        )


def test_earlier_tmpdir_cannot_mask_a_repository_root_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A permissive earlier root must not hide a repository-root approval (#9758)."""
    repo_root = tmp_path / "repo"
    permissive = tmp_path / "process-tmp"
    monkeypatch.setenv("TMPDIR", str(permissive))

    with pytest.raises(ValueError, match="repository or home directory"):
        assert_delete_target(
            permissive / "payload",
            repo_root=repo_root,
            approved_temp_roots=(repo_root,),
        )


def _deletion_layout(tmp_path: Path) -> dict[str, Path]:
    repo_root = tmp_path / "repo"
    return {
        "repository": repo_root,
        "home": Path.home().resolve(),
        "filesystem": Path("/"),
        "worktrees": repo_root / ".worktrees" / "dispatch" / "task",
        "batch": repo_root / "batch_state" / "tmp" / "render",
        "permissive": tmp_path / "process-tmp",
        "other": tmp_path / "other-tmp",
        "narrow": tmp_path / "narrow-temp",
        "narrow_a": tmp_path / "narrow-a",
        "narrow_b": tmp_path / "narrow-b",
    }


def _set_tmpdir(monkeypatch: pytest.MonkeyPatch, layout: dict[str, Path], mode: str) -> None:
    if mode == "unset":
        monkeypatch.delenv("TMPDIR", raising=False)
        return
    monkeypatch.setenv("TMPDIR", str(layout[mode]))


def _deletion_target(layout: dict[str, Path], mode: str, tmpdir_mode: str) -> Path:
    if mode == "tmpdir":
        return layout[tmpdir_mode] / "payload"
    if mode == "worktrees_root":
        return layout["repository"] / ".worktrees"
    if mode in {"narrow", "narrow_a", "narrow_b"}:
        return layout[mode] / "payload"
    return layout[mode]


def _approved_roots(layout: dict[str, Path], modes: tuple[str, ...]) -> tuple[Path, ...]:
    return tuple(layout[mode] for mode in modes)


@pytest.mark.parametrize(
    ("tmpdir_mode", "approved_modes", "target_mode"),
    [
        pytest.param("permissive", ("repository",), "tmpdir", id="tmpdir-masks-repository"),
        pytest.param("permissive", ("home",), "tmpdir", id="tmpdir-masks-home"),
        pytest.param("permissive", ("narrow", "repository"), "tmpdir", id="tmpdir-masks-repository-after-narrow"),
        pytest.param("permissive", ("repository", "narrow"), "tmpdir", id="tmpdir-masks-repository-before-narrow"),
        pytest.param("permissive", ("narrow", "home"), "tmpdir", id="tmpdir-masks-home-after-narrow"),
        pytest.param("permissive", ("home", "narrow"), "tmpdir", id="tmpdir-masks-home-before-narrow"),
        pytest.param("unset", ("repository",), "worktrees", id="unset-worktrees-mask-repository"),
        pytest.param("unset", ("home",), "worktrees", id="unset-worktrees-mask-home"),
        pytest.param("unset", ("repository",), "batch", id="unset-batch-mask-repository"),
        pytest.param("unset", ("home",), "batch", id="unset-batch-mask-home"),
        pytest.param("unset", ("narrow", "repository"), "narrow", id="unset-narrow-before-repository"),
        pytest.param("unset", ("narrow", "home"), "narrow", id="unset-narrow-before-home"),
        pytest.param("unset", ("repository", "narrow"), "narrow", id="unset-repository-before-narrow"),
        pytest.param("unset", ("home", "narrow"), "narrow", id="unset-home-before-narrow"),
        pytest.param("other", ("narrow", "repository"), "narrow", id="other-tmpdir-narrow-before-repository"),
        pytest.param("other", ("repository", "narrow"), "narrow", id="other-tmpdir-repository-before-narrow"),
        pytest.param("other", ("narrow", "home"), "narrow", id="other-tmpdir-narrow-before-home"),
        pytest.param("other", ("home", "narrow"), "narrow", id="other-tmpdir-home-before-narrow"),
        pytest.param("other", ("repository",), "worktrees", id="other-tmpdir-worktrees-mask-repository"),
        pytest.param("other", ("home",), "batch", id="other-tmpdir-batch-mask-home"),
        pytest.param("repository", (), "worktrees", id="tmpdir-is-repository-masked-by-worktrees"),
        pytest.param("repository", (), "batch", id="tmpdir-is-repository-masked-by-batch"),
        pytest.param("home", (), "worktrees", id="tmpdir-is-home-masked-by-worktrees"),
        pytest.param("home", (), "batch", id="tmpdir-is-home-masked-by-batch"),
        pytest.param("unset", ("repository", "home"), "worktrees", id="unset-repository-then-home"),
        pytest.param("unset", ("home", "repository"), "worktrees", id="unset-home-then-repository"),
        pytest.param("permissive", ("home", "repository"), "tmpdir", id="tmpdir-home-then-repository"),
        pytest.param("permissive", ("repository", "home"), "tmpdir", id="tmpdir-repository-then-home"),
        pytest.param("unset", ("repository",), "worktrees_root", id="worktrees-root-still-reports-repository"),
    ],
)
def test_repository_or_home_root_is_rejected_in_every_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmpdir_mode: str,
    approved_modes: tuple[str, ...],
    target_mode: str,
) -> None:
    """Repository and home approvals are rejected with ``$TMPDIR`` set or unset."""
    layout = _deletion_layout(tmp_path)
    _set_tmpdir(monkeypatch, layout, tmpdir_mode)

    with pytest.raises(ValueError, match="repository or home directory"):
        assert_delete_target(
            _deletion_target(layout, target_mode, tmpdir_mode),
            repo_root=layout["repository"],
            approved_temp_roots=_approved_roots(layout, approved_modes),
        )


@pytest.mark.parametrize(
    ("tmpdir_mode", "approved_modes", "target_mode"),
    [
        pytest.param("permissive", ("filesystem",), "tmpdir", id="tmpdir-masks-filesystem-root"),
        pytest.param("filesystem", (), "worktrees", id="tmpdir-is-filesystem-root-masked-by-worktrees"),
        pytest.param("unset", ("narrow", "filesystem"), "narrow", id="unset-narrow-before-filesystem-root"),
        pytest.param("unset", ("filesystem", "narrow"), "narrow", id="unset-filesystem-root-before-narrow"),
    ],
)
def test_filesystem_root_is_rejected_in_every_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmpdir_mode: str,
    approved_modes: tuple[str, ...],
    target_mode: str,
) -> None:
    """The filesystem-root rejection uses the same order-independent pass."""
    layout = _deletion_layout(tmp_path)
    _set_tmpdir(monkeypatch, layout, tmpdir_mode)

    with pytest.raises(ValueError, match="filesystem root"):
        assert_delete_target(
            _deletion_target(layout, target_mode, tmpdir_mode),
            repo_root=layout["repository"],
            approved_temp_roots=_approved_roots(layout, approved_modes),
        )


@pytest.mark.parametrize(
    ("tmpdir_mode", "approved_modes", "target_mode"),
    [
        pytest.param("unset", ("narrow",), "narrow", id="unset-narrow"),
        pytest.param("permissive", ("narrow",), "narrow", id="tmpdir-set-narrow"),
        pytest.param("permissive", (), "tmpdir", id="tmpdir-set-payload"),
        pytest.param("unset", (), "worktrees", id="unset-worktrees"),
        pytest.param("permissive", (), "worktrees", id="tmpdir-set-worktrees"),
        pytest.param("unset", (), "batch", id="unset-batch"),
        pytest.param("permissive", (), "batch", id="tmpdir-set-batch"),
        pytest.param("other", (), "worktrees", id="other-tmpdir-worktrees"),
        pytest.param("other", ("narrow",), "narrow", id="other-tmpdir-narrow"),
        pytest.param("unset", ("narrow_a", "narrow_b"), "narrow_a", id="unset-first-of-two-narrow"),
        pytest.param("unset", ("narrow_a", "narrow_b"), "narrow_b", id="unset-second-of-two-narrow"),
        pytest.param("permissive", ("narrow_b", "narrow_a"), "narrow_a", id="tmpdir-set-reversed-narrow-order"),
    ],
)
def test_narrow_roots_stay_allowed_in_every_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmpdir_mode: str,
    approved_modes: tuple[str, ...],
    target_mode: str,
) -> None:
    """Valid temporary roots keep the previous acceptance behavior."""
    layout = _deletion_layout(tmp_path)
    _set_tmpdir(monkeypatch, layout, tmpdir_mode)
    target = _deletion_target(layout, target_mode, tmpdir_mode)

    assert (
        assert_delete_target(
            target,
            repo_root=layout["repository"],
            approved_temp_roots=_approved_roots(layout, approved_modes),
        )
        == target.resolve()
    )


def test_directory_under_home_stays_approvable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A session subdirectory of home is a narrow root; home itself is not."""
    home = tmp_path / "home"
    session = home / ".codex" / "sessions"
    payload = session / "old.json"
    monkeypatch.setattr("scripts.path_safety.Path.home", lambda: home)
    repo_root = tmp_path / "repo"

    for tmpdir in (None, tmp_path / "process-tmp"):
        if tmpdir is None:
            monkeypatch.delenv("TMPDIR", raising=False)
        else:
            monkeypatch.setenv("TMPDIR", str(tmpdir))
        assert (
            assert_delete_target(
                payload,
                repo_root=repo_root,
                approved_temp_roots=(session,),
            )
            == payload.resolve()
        )

    permissive = tmp_path / "process-tmp"
    monkeypatch.setenv("TMPDIR", str(permissive))
    with pytest.raises(ValueError, match="repository or home directory"):
        assert_delete_target(
            permissive / "payload",
            repo_root=repo_root,
            approved_temp_roots=(session, home),
        )


def test_delete_guard_refuses_path_outside_allowed_delete_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Caller-owned temps must still be under an explicit approved root."""
    # Clear process TMPDIR so pytest's temp hierarchy cannot become an
    # accidental allowlist root for this refusal case.
    monkeypatch.delenv("TMPDIR", raising=False)
    repo_root = tmp_path / "repo"
    outside = tmp_path / "not-approved" / "payload"
    outside.parent.mkdir(parents=True)
    outside.write_text("x\n", encoding="utf-8")

    with pytest.raises(ValueError, match="outside approved"):
        assert_delete_target(
            outside,
            repo_root=repo_root,
            approved_temp_roots=(tmp_path / "other-root",),
        )


def test_raw_rm_rf_lint_allowlists_scoped_shell_cleanups() -> None:
    """services.sh lockdirs/caches stay allowlisted; new unscoped hits fail."""
    findings = lint_raw_rm_rf.find_raw_rm_rf()
    assert findings == [], f"unscoped raw rm -rf: {findings}"


def test_raw_rm_rf_lint_detects_unscoped_line(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "evil.sh").write_text('rm -rf "$HOME"\n', encoding="utf-8")
    (tmp_path / "services.sh").write_text("# no rm\n", encoding="utf-8")

    findings = lint_raw_rm_rf.find_raw_rm_rf(repo_root=tmp_path)
    assert findings == [("scripts/evil.sh:1", 'rm -rf "$HOME"')]


def test_raw_rm_rf_lint_allowlist_keyed_by_content_not_line(tmp_path: Path) -> None:
    """Allowlisted snippets survive line shifts; excess copies still fail."""
    lockdir_rm = 'rm -rf "$lockdir" 2>/dev/null || true'
    services = tmp_path / "services.sh"
    services.write_text(
        "\n".join(
            [
                "# preamble inserted above allowlisted cleanups",
                "# more lines to shift line numbers",
                lockdir_rm,
                lockdir_rm,
                'rm -rf "$vite_cache_dir"',
                'rm -rf "$dist_dir"',
                'rm -rf "$astro_dir"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    findings = lint_raw_rm_rf.find_raw_rm_rf(repo_root=tmp_path)
    assert findings == [], f"shifted allowlisted snippets should pass: {findings}"

    services.write_text(services.read_text(encoding="utf-8") + lockdir_rm + "\n", encoding="utf-8")
    findings = lint_raw_rm_rf.find_raw_rm_rf(repo_root=tmp_path)
    assert len(findings) == 1
    assert findings[0][1] == lockdir_rm
    assert findings[0][0].startswith("services.sh:")


def test_control_plane_sqlite_lint_allowlists_remaining_direct_opens() -> None:
    from scripts.hygiene import lint_control_plane_sqlite

    violations = lint_control_plane_sqlite.find_unallowlisted_connects()
    assert violations == [], f"unallowlisted control-plane sqlite opens: {violations}"
