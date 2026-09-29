"""Launcher helpers never run from a worktree-controlled root (#9121).

``launcher_resolve_roots`` sets ``LC_DURABLE_HELPER_ROOT``, the checkout whose
``.venv/bin/python`` and helper scripts every launcher helper site executes. It
used to come from ``git rev-parse --git-common-dir``, so a rewritten ``.git``
gitfile (or its ``commondir``) or an inherited ``GIT_DIR`` picked the root.

Every test builds real temporary repositories: an honest primary with a linked
worktree, plus an attacker repository. Each ``.venv/bin/python`` is a stub that
logs ``<owner> <argv>`` and runs nothing else, so the log shows which
interpreter every site executed; ``EVIL`` or ``WORKTREE`` lines mean a planted
executable ran.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")

_COPIED = (
    "start-claude-driver.sh",
    "scripts/lib/launcher_core.sh",
    "scripts/lib/project_interpreter.sh",
    "scripts/lib/handoff_identity.sh",
    "scripts/lib/session_supervisor.sh",
    "scripts/lib/kimicc_route.sh",
    "scripts/lib/claude_route_guard.sh",
    "scripts/lib/profile_resolver.sh",
    "scripts/launchers/claude.sh",
    "scripts/launchers/kimi.sh",
    "scripts/launchers/codex.sh",
    "scripts/config/issue_streams.yaml",
    "scripts/config/launcher_stream_aliases.tsv",
)
# Helper scripts the sites name by path; the stub interpreters never run them.
_PLACEHOLDERS = (
    "scripts/orchestration/thread_handoff.py",
    "scripts/lib/kimi_coding_oauth.py",
    "scripts/lib/context_profiles.py",
    "scripts/review/model_catalog.py",
)
_SITES = (
    "import_bundle",
    "observer_heartbeat",
    "renew_heartbeat",
    "lease_close",
    "driver_agent_type",
    "slot_registry",
    "claude_profile",
    "kimi_route",
)
_EXPECTED_HONEST = {
    "import_bundle": "scripts/orchestration/thread_handoff.py",
    "observer_heartbeat": "scripts.orchestration.observer_heartbeat",
    "renew_heartbeat": "scripts.session_supervisor heartbeat",
    "lease_close": "scripts.session_supervisor close",
    "driver_agent_type": "scripts.orchestration.driver_agent_type",
    "slot_registry": "scripts.orchestration.handoff_slot_registry",
    "claude_profile": "scripts/lib/context_profiles.py",
    "kimi_route": "scripts/lib/kimi_coding_oauth.py",
}


def _clean_env(**extra: str) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("GIT_", "LC_", "LEARN_UKRAINIAN_", "KIMI", "MOONSHOT", "CLAUDE_", "SESSION_"))
    }
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env.update(extra)
    return env


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd,
        env=_clean_env(),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return result.stdout.strip()


def _stub_python(root: Path, owner: str, log: Path) -> None:
    """A ``.venv/bin/python`` that logs its argv and runs nothing else."""
    python = root / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True, exist_ok=True)
    python.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s %s\\n' {owner} \"$*\" >> {str(log)!r}\n"
        # The Kimi route asks the catalog for a route before reaching its
        # OAuth helper; answer that one call so the helper line is reached.
        'case "$1" in *model_catalog.py) printf \'k3\\tplat\\tcoding\\tkimicc_k3\\n\' ;; esac\n'
        "exit 0\n",
        encoding="utf-8",
    )
    python.chmod(0o755)


def _place_helper_scripts(root: Path) -> None:
    for relative in _PLACEHOLDERS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("raise SystemExit('stub interpreters never run this')\n", encoding="utf-8")


@dataclass
class Layout:
    tmp: Path
    primary: Path
    worktree: Path
    attacker: Path
    log: Path

    def lines(self) -> list[str]:
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def owners(self) -> set[str]:
        return {line.split(" ", 1)[0] for line in self.lines()}


@pytest.fixture()
def layout(tmp_path: Path) -> Layout:
    tmp = tmp_path.resolve()
    log = tmp / "executions.log"
    primary = tmp / "primary"
    primary.mkdir()
    for relative in _COPIED:
        destination = primary / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, destination)
    _place_helper_scripts(primary)
    (primary / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    _git(primary, "init", "-q", "-b", "main")
    _git(primary, "add", ".")
    _git(primary, "commit", "-q", "-m", "init")
    worktree = tmp / "worktree"
    _git(primary, "worktree", "add", "-q", "-b", "feature", str(worktree))
    _stub_python(primary, "HONEST", log)

    attacker = tmp / "attacker"
    attacker.mkdir()
    _place_helper_scripts(attacker)
    _git(attacker, "init", "-q", "-b", "main")
    _git(attacker, "add", ".")
    _git(attacker, "commit", "-q", "-m", "attacker")
    _stub_python(attacker, "EVIL", log)
    return Layout(tmp, primary, worktree, attacker, log)


def _hostile_env(layout: Layout) -> dict[str, str]:
    return {
        "GIT_DIR": f"{layout.attacker}/.git",
        "GIT_COMMON_DIR": f"{layout.attacker}/.git",
        "GIT_WORK_TREE": str(layout.attacker),
    }


_SITE_HARNESS = r"""
LC_ROOT="$1"
source "$LC_ROOT/scripts/lib/launcher_core.sh"
launcher_resolve_roots
printf 'resolved=%s\n' "$LC_DURABLE_HELPER_ROOT"
source "$LC_ROOT/scripts/lib/handoff_identity.sh"
site() { printf 'SITE %s\n' "$1" >> "$SITE_LOG"; }

site import_bundle
( LC_EPIC=devops; launcher_import_rollover_bundle ) >/dev/null 2>&1
site observer_heartbeat
( LC_PROVIDER=cursor LC_MODE=driver LC_DRY_RUN=0 LC_EPIC=devops; launcher_cursor_observer_presence ) >/dev/null 2>&1
site renew_heartbeat
(
  LC_MODE=driver LC_DRIVER_LEASE_CLAIMED=1 LC_DRY_RUN=0
  SESSION_STREAM_RENEW_INTERVAL_SECONDS=1 SESSION_STREAM_RENEW_JITTER_SECONDS=0
  sleep 1.6 & child=$!
  launcher_driver_renew_loop "$child"
  wait "$child"
  launcher_stop_driver_renew
) >/dev/null 2>&1
site lease_close
( LC_PROVIDER=claude LC_DRIVER_CLOSE_RETRY_SECONDS=0; launcher_close_driver_lease ) >/dev/null 2>&1
site driver_agent_type
( LC_PROVIDER=claude LC_EPIC=devops LC_DRY_RUN=0 LC_FORWARD_ARGS=(); launcher_inject_driver_agent ) >/dev/null 2>&1
site slot_registry
( launcher_require_registered_slot claude devops ) >/dev/null 2>&1
site claude_profile
( LC_MODEL=claude-opus-5-5 source "$LC_ROOT/scripts/launchers/claude.sh"; launcher_adapter_preflight ) >/dev/null 2>&1
site kimi_route
(
  LC_HARNESS=claude-code LC_ENDPOINT=coding LC_MODEL=k3 LC_ISOLATE_CONFIG=0
  source "$LC_ROOT/scripts/launchers/kimi.sh"
  launcher_adapter_preflight
) >/dev/null 2>&1
exit 0
"""


def _run_sites(layout: Layout, root: Path | None = None, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", _SITE_HARNESS, "bash", str(root or layout.worktree)],
        cwd=layout.tmp,
        env=_clean_env(HOME=str(layout.tmp / "home"), SITE_LOG=str(layout.log), **env),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def _site_executions(layout: Layout) -> dict[str, list[str]]:
    executions: dict[str, list[str]] = {}
    current = ""
    for line in layout.lines():
        if line.startswith("SITE "):
            current = line.split(" ", 1)[1]
            executions[current] = []
        else:
            executions.setdefault(current, []).append(line)
    return executions


def _assert_every_site_ran_the_primary(layout: Layout, result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr
    assert f"resolved={layout.primary}" in result.stdout
    executions = _site_executions(layout)
    assert list(executions) == list(_SITES), executions
    for name in _SITES:
        ran = executions[name]
        assert ran, f"site {name} executed no interpreter"
        assert all(line.startswith("HONEST ") for line in ran), (name, ran)
        assert any(_EXPECTED_HONEST[name] in line for line in ran), (name, ran)
    for line in layout.lines():
        assert str(layout.attacker) not in line, line
        assert str(layout.worktree / ".venv") not in line, line
    # Helper scripts named by path come from the validated primary.
    joined = "\n".join(layout.lines())
    assert f"{layout.primary}/scripts/orchestration/thread_handoff.py" in joined
    assert f"{layout.primary}/scripts/lib/kimi_coding_oauth.py" in joined


def _assert_refused_before_any_site(layout: Layout, result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 3, (result.stdout, result.stderr)
    assert "git metadata does not validate" in result.stderr
    assert "resolved=" not in result.stdout
    assert layout.lines() == [], layout.lines()


# --- baseline: an honest worktree keeps using the primary ---------------------


def test_honest_worktree_every_site_runs_the_primary_interpreter(layout: Layout) -> None:
    _assert_every_site_ran_the_primary(layout, _run_sites(layout))


def test_primary_checkout_resolves_to_itself(layout: Layout) -> None:
    _assert_every_site_ran_the_primary(layout, _run_sites(layout, root=layout.primary))


def test_worktree_reached_through_a_symlinked_path_still_resolves(layout: Layout) -> None:
    alias = layout.tmp / "alias"
    alias.symlink_to(layout.worktree)
    _assert_every_site_ran_the_primary(layout, _run_sites(layout, root=alias))


def test_relative_back_pointer_is_accepted(layout: Layout) -> None:
    """Git's ``worktree.useRelativePaths`` writes both pointers relative."""
    relative = layout.tmp / "relative"
    _git(layout.primary, "-c", "worktree.useRelativePaths=true", "worktree", "add", "-q", "-b", "rel", str(relative))
    assert (relative / ".git").read_text(encoding="utf-8").startswith("gitdir: ../")
    assert not (layout.primary / ".git" / "worktrees" / "relative" / "gitdir").read_text(
        encoding="utf-8"
    ).startswith("/")
    _assert_every_site_ran_the_primary(layout, _run_sites(layout, root=relative))


# --- environment redirection --------------------------------------------------


def test_ambient_git_dir_does_not_redirect_any_site(layout: Layout) -> None:
    _assert_every_site_ran_the_primary(layout, _run_sites(layout, **_hostile_env(layout)))


def test_worktree_local_venv_never_runs(layout: Layout) -> None:
    """The driver-agent and Kimi sites used to try the worktree's own .venv first."""
    _stub_python(layout.worktree, "WORKTREE", layout.log)
    result = _run_sites(layout, **_hostile_env(layout))
    _assert_every_site_ran_the_primary(layout, result)
    assert "WORKTREE" not in layout.owners()


def test_resolution_clears_git_local_environment(layout: Layout) -> None:
    script = (
        'LC_ROOT="$1"; source "$LC_ROOT/scripts/lib/launcher_core.sh"; launcher_resolve_roots; '
        'env | grep -E "^GIT_(DIR|COMMON_DIR|WORK_TREE|INDEX_FILE|OBJECT_DIRECTORY|CONFIG_PARAMETERS)=" || true'
    )
    result = subprocess.run(
        ["bash", "-c", script, "bash", str(layout.worktree)],
        env=_clean_env(**_hostile_env(layout), GIT_INDEX_FILE="/x", GIT_OBJECT_DIRECTORY="/x",
                       GIT_CONFIG_PARAMETERS="'core.fsmonitor=/x'"),
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


# --- hostile gitfile ----------------------------------------------------------


def test_hostile_gitfile_with_commondir_is_refused(layout: Layout) -> None:
    admin = layout.tmp / "attacker-admin"
    shutil.copytree(layout.primary / ".git" / "worktrees" / "worktree", admin)
    (admin / "commondir").write_text(f"{layout.attacker}/.git\n", encoding="utf-8")
    (layout.worktree / ".git").write_text(f"gitdir: {admin}\n", encoding="utf-8")
    # git itself follows the commondir to the attacker: the old resolver's source.
    assert _git(layout.worktree, "rev-parse", "--path-format=absolute", "--git-common-dir") == (
        f"{layout.attacker}/.git"
    )
    _assert_refused_before_any_site(layout, _run_sites(layout))


def test_gitfile_borrowing_another_repositorys_worktree_entry_is_refused(layout: Layout) -> None:
    """A well-shaped ``<attacker>/.git/worktrees/<name>`` whose back-pointer names another checkout."""
    _git(layout.attacker, "worktree", "add", "-q", "-b", "decoy", str(layout.tmp / "decoy"))
    (layout.worktree / ".git").write_text(f"gitdir: {layout.attacker}/.git/worktrees/decoy\n", encoding="utf-8")
    result = _run_sites(layout)
    _assert_refused_before_any_site(layout, result)
    assert "does not point back" in result.stderr


def test_commondir_tampered_inside_the_real_admin_dir_is_ignored(layout: Layout) -> None:
    """The resolver never reads ``commondir``, even under a validated admin dir."""
    (layout.primary / ".git" / "worktrees" / "worktree" / "commondir").write_text(
        f"{layout.attacker}/.git\n", encoding="utf-8"
    )
    _assert_every_site_ran_the_primary(layout, _run_sites(layout))


def test_codex_refuses_a_canonical_checkout_git_found_through_commondir(layout: Layout) -> None:
    (layout.primary / ".git" / "worktrees" / "worktree" / "commondir").write_text(
        f"{layout.attacker}/.git\n", encoding="utf-8"
    )
    script = r"""
LC_ROOT="$1"; source "$LC_ROOT/scripts/lib/launcher_core.sh"; launcher_resolve_roots
LC_DRY_RUN=0; source "$LC_ROOT/scripts/launchers/codex.sh"
launcher_codex_resolve_canonical_root
printf 'canonical=%s\n' "$LC_CODEX_CANONICAL_ROOT"
"""
    result = subprocess.run(
        ["bash", "-c", script, "bash", str(layout.worktree)],
        env=_clean_env(HOME=str(layout.tmp / "home")), capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert f"canonical checkout {layout.attacker} does not belong to the validated primary" in result.stderr
    assert "canonical=" not in result.stdout


def test_codex_accepts_the_validated_primary_as_canonical_checkout(layout: Layout) -> None:
    script = r"""
LC_ROOT="$1"; source "$LC_ROOT/scripts/lib/launcher_core.sh"; launcher_resolve_roots
LC_DRY_RUN=0; source "$LC_ROOT/scripts/launchers/codex.sh"
launcher_codex_resolve_canonical_root
printf 'canonical=%s\n' "$LC_CODEX_CANONICAL_ROOT"
"""
    result = subprocess.run(
        ["bash", "-c", script, "bash", str(layout.worktree)],
        env=_clean_env(HOME=str(layout.tmp / "home")), capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert f"canonical={layout.primary}" in result.stdout


# --- symlinked layouts --------------------------------------------------------


def test_symlinked_worktree_gitfile_is_refused(layout: Layout) -> None:
    real = layout.tmp / "gitfile"
    real.write_text(f"gitdir: {layout.primary}/.git/worktrees/worktree\n", encoding="utf-8")
    (layout.worktree / ".git").unlink()
    (layout.worktree / ".git").symlink_to(real)
    _assert_refused_before_any_site(layout, _run_sites(layout))


def test_gitfile_through_a_symlinked_primary_git_dir_is_refused(layout: Layout) -> None:
    fake = layout.tmp / "fake-primary"
    fake.mkdir()
    (fake / ".git").symlink_to(layout.primary / ".git")
    _stub_python(fake, "EVIL", layout.log)
    (layout.worktree / ".git").write_text(f"gitdir: {fake}/.git/worktrees/worktree\n", encoding="utf-8")
    _assert_refused_before_any_site(layout, _run_sites(layout))


def test_gitfile_through_a_symlinked_worktrees_dir_is_refused(layout: Layout) -> None:
    fake = layout.tmp / "fake-primary"
    (fake / ".git").mkdir(parents=True)
    (fake / ".git" / "worktrees").symlink_to(layout.primary / ".git" / "worktrees")
    _stub_python(fake, "EVIL", layout.log)
    (layout.worktree / ".git").write_text(f"gitdir: {fake}/.git/worktrees/worktree\n", encoding="utf-8")
    _assert_refused_before_any_site(layout, _run_sites(layout))


def test_symlinked_back_pointer_file_is_refused(layout: Layout) -> None:
    admin = layout.primary / ".git" / "worktrees" / "worktree"
    real = layout.tmp / "pointer"
    real.write_text((admin / "gitdir").read_text(encoding="utf-8"), encoding="utf-8")
    (admin / "gitdir").unlink()
    (admin / "gitdir").symlink_to(real)
    _assert_refused_before_any_site(layout, _run_sites(layout))


# --- forged fake primary ------------------------------------------------------


def test_fake_primary_without_a_back_pointer_is_refused(layout: Layout) -> None:
    fake = layout.tmp / "fake-primary"
    (fake / ".git" / "worktrees" / "worktree").mkdir(parents=True)
    _stub_python(fake, "EVIL", layout.log)
    (layout.worktree / ".git").write_text(f"gitdir: {fake}/.git/worktrees/worktree\n", encoding="utf-8")
    result = _run_sites(layout)
    _assert_refused_before_any_site(layout, result)
    assert "does not point back" in result.stderr


def test_fake_primary_pointing_back_at_another_worktree_is_refused(layout: Layout) -> None:
    fake = layout.tmp / "fake-primary"
    admin = fake / ".git" / "worktrees" / "worktree"
    admin.mkdir(parents=True)
    (admin / "gitdir").write_text(f"{layout.tmp}/elsewhere/.git\n", encoding="utf-8")
    (layout.tmp / "elsewhere").mkdir()
    _stub_python(fake, "EVIL", layout.log)
    (layout.worktree / ".git").write_text(f"gitdir: {admin}\n", encoding="utf-8")
    _assert_refused_before_any_site(layout, _run_sites(layout))


def test_residual_fully_forged_primary_is_locally_indistinguishable(layout: Layout) -> None:
    """Documented #9121 residual (see scripts/lib/project_interpreter.sh).

    Whoever can rewrite the gitfile can also forge the back-pointer, so a
    complete fake primary validates. This pins the known limit; a trust anchor
    outside the worktree would flip it.
    """
    fake = layout.tmp / "fake-primary"
    admin = fake / ".git" / "worktrees" / "worktree"
    admin.mkdir(parents=True)
    (admin / "gitdir").write_text(f"{layout.worktree}/.git\n", encoding="utf-8")
    (layout.worktree / ".git").write_text(f"gitdir: {admin}\n", encoding="utf-8")
    script = 'source "$1/scripts/lib/project_interpreter.sh"; project_primary_root_resolve "$1"'
    result = subprocess.run(
        ["bash", "-c", script, "bash", str(layout.worktree)],
        env=_clean_env(), capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(fake)


# --- real launcher entry point -------------------------------------------------


def _run_driver(layout: Layout, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(layout.worktree / "start-claude-driver.sh"), "--epic", "devops"],
        cwd=layout.worktree,
        env=_clean_env(HOME=str(layout.tmp / "home"), LAUNCHER_DRY_RUN="1", **env),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_real_driver_launcher_refuses_a_hostile_gitfile(layout: Layout) -> None:
    _git(layout.attacker, "worktree", "add", "-q", "-b", "decoy", str(layout.tmp / "decoy"))
    (layout.worktree / ".git").write_text(f"gitdir: {layout.attacker}/.git/worktrees/decoy\n", encoding="utf-8")
    result = _run_driver(layout)
    assert result.returncode == 3, (result.stdout, result.stderr)
    assert "git metadata does not validate" in result.stderr
    assert layout.lines() == []


def test_real_driver_launcher_ignores_ambient_git_dir(layout: Layout) -> None:
    _stub_python(layout.worktree, "WORKTREE", layout.log)
    result = _run_driver(layout, **_hostile_env(layout))
    # The trimmed sandbox stops the dry run later on; only who ran matters here.
    assert "git metadata does not validate" not in result.stderr
    assert layout.lines(), result.stderr
    assert layout.owners() == {"HONEST"}, layout.lines()


def test_session_supervisor_state_root_ignores_git_redirection(layout: Layout) -> None:
    script = 'source "$1/scripts/lib/session_supervisor.sh"; _canonical_state_root "$1"'
    ambient = subprocess.run(
        ["bash", "-c", script, "bash", str(layout.worktree)],
        env=_clean_env(**_hostile_env(layout)), capture_output=True, text=True, check=False, timeout=30,
    )
    assert ambient.returncode == 0, ambient.stderr
    assert ambient.stdout.strip() == str(layout.primary)

    _git(layout.attacker, "worktree", "add", "-q", "-b", "decoy", str(layout.tmp / "decoy"))
    (layout.worktree / ".git").write_text(f"gitdir: {layout.attacker}/.git/worktrees/decoy\n", encoding="utf-8")
    hostile = subprocess.run(
        ["bash", "-c", script, "bash", str(layout.worktree)],
        env=_clean_env(), capture_output=True, text=True, check=False, timeout=30,
    )
    assert hostile.returncode == 1
    assert "cannot resolve canonical state root" in hostile.stderr
    assert hostile.stdout == ""
