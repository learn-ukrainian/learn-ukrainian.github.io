"""Runtime probes. The case name is HOOK_RUNTIME_CASE. Nothing runs at import."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import threading
import time


def second_level() -> None:
    def run_command(argv: list[str]) -> None:
        subprocess.run(argv, check=False, timeout=30)

    def git_output(*args: str) -> None:
        run_command(["git", *args])

    git_output("-c", "alias.x=!bash -n bad.sh", "x")


def value_runner() -> None:
    def run_command(argv: list[str]) -> None:
        subprocess.run(argv, check=False, timeout=30)

    def call(fn) -> None:
        fn(["bash", "-n", "x"])

    call(run_command)


def explicit_pager() -> None:
    subprocess.run(["gh", "api", "user"], env={"GH_PAGER": "cat"}, check=False, timeout=30)


def inherited_pager() -> None:
    subprocess.run(["gh", "api", "user"], check=False, timeout=30)


def launch_keyword() -> None:
    subprocess.run(["git", "rev-parse", "--git-dir"], executable="bash", check=False, timeout=30)


def launch_positional() -> None:
    proc = subprocess.Popen(["git", "status"], -1, "bash")
    proc.wait(timeout=30)


def asyncio_exec() -> None:
    async def main() -> None:
        await asyncio.create_subprocess_exec("bash", "-n", "x")

    asyncio.run(main())


def bytes_argv() -> None:
    subprocess.run([b"bash", b"-xn", b"x"], check=False, timeout=30)


def os_system() -> None:
    os.system("bash -n x")


def posix_spawn() -> None:
    os.posix_spawn("/bin/bash", ["/bin/bash", "-n", "x"], os.environ)


def os_exec() -> None:
    os.execv("/bin/bash", ["/bin/bash", "--noexec", "x"])


def fork_child() -> None:
    os.spawnv(os.P_WAIT, "/bin/echo", ["/bin/echo", "collected"])


DESCENDANT_ARGV = ("/bin/sh", "-c", "/bin/echo UNOBSERVED_CHILD > descendant-marker")


def descendant() -> None:
    subprocess.run(list(DESCENDANT_ARGV), check=False, timeout=30)


def concurrent_starts() -> None:
    """Overlap two starts so a process-global re-entrancy flag would drop one."""
    barrier = threading.Barrier(2)

    def launch(argv: list[str]) -> None:
        barrier.wait(timeout=5)
        try:
            subprocess.run(argv, check=False, timeout=30)
        except FileNotFoundError:
            return

    threads = [
        threading.Thread(target=launch, args=(["__concurrent_a__", "intercept"],)),
        threading.Thread(target=launch, args=(["__concurrent_b__", "intercept"],)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    if any(thread.is_alive() for thread in threads):
        raise RuntimeError("concurrent probe timed out")


def swallow() -> None:
    try:
        subprocess.run(["bash", "-n", "x"], check=False, timeout=30)
    except Exception:
        return


def crash() -> None:
    raise RuntimeError("probe-crash")


def sleeper() -> None:
    time.sleep(30)


def noop() -> None:
    return


def fstring_shell() -> None:
    script = "x.sh"
    subprocess.run(f"bash -n {script}", shell=True, check=False, timeout=30)


def asyncio_shell() -> None:
    async def main() -> None:
        await asyncio.create_subprocess_shell("bash -n x.sh")

    asyncio.run(main())


def bash_c() -> None:
    subprocess.run(["bash", "-c", "bash -n x.sh"], check=False, timeout=30)


def shell_git_alias() -> None:
    subprocess.run(["bash", "-c", "git -c alias.x=!bash -n bad.sh x"], check=False, timeout=30)


def timeout_wrap() -> None:
    subprocess.run(["timeout", "5", "bash", "-n", "x.sh"], check=False, timeout=30)


def env_wrap() -> None:
    subprocess.run(["env", "git", "rev-parse", "--git-dir"], check=False, timeout=30)


def nice_wrap() -> None:
    subprocess.run(["nice", "git", "status"], check=False, timeout=30)


def os_system_git() -> None:
    os.system("git rev-parse --git-dir")


def argv0_override() -> None:
    subprocess.run(["/tmp/evil/git", "rev-parse", "--git-dir"], check=False, timeout=30)


def executable_override() -> None:
    subprocess.run(["git", "rev-parse", "--git-dir"], executable="/tmp/evil/git", check=False, timeout=30)


def putenv_pager() -> None:
    os.putenv("GH_PAGER", "sentinel-value")
    try:
        subprocess.run(["git", "rev-parse", "--git-dir"], check=False, timeout=30)
    except FileNotFoundError:
        return


def redirect_mutation() -> None:
    """Change harness-controlled keys after the baseline snapshot, then launch git."""
    from pathlib import Path

    root = Path("redirect-bin")
    root.mkdir()
    git = root / "git"
    git.write_text("#!/bin/sh\ntouch real-git-executed\n", encoding="utf-8")
    git.chmod(0o755)
    for key in os.environ.get("HOOK_RUNTIME_REDIRECT_KEYS", "").split(","):
        if key:
            os.environ[key] = "redirected"
    os.environ["PATH"] = str(root.resolve())
    try:
        subprocess.run(["git", "rev-parse", "--git-dir"], check=False, timeout=30)
    except FileNotFoundError:
        return


def path_tripwire() -> None:
    """Baseline PATH names only a fake git. An allowed template must not exec it."""
    from pathlib import Path

    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    Path("shim-result").write_text(f"canned\n{result.returncode}\n{result.stdout}", encoding="utf-8")


def shim_then_forbidden() -> None:
    """A canned success must not authorize a later shell syntax check."""
    from pathlib import Path

    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    Path("shim-result").write_text(f"canned\n{result.returncode}\n{result.stdout}", encoding="utf-8")
    try:
        subprocess.run(["bash", "-n", "x.sh"], check=False, timeout=30)
    except FileNotFoundError:
        return


def python_c() -> None:
    subprocess.run([sys.executable, "-c", "print(1)"], check=False, timeout=30)


def python_loader_redirect() -> None:
    """A healer-shaped argv with PYTHONPATH changed is not the reviewed launch."""
    from pathlib import Path

    from scripts.common.repo_root import project_interpreter

    root = Path(__file__).resolve().parents[3]
    os.environ["PYTHONPATH"] = "redirected"
    try:
        subprocess.run(
            [
                str(project_interpreter(root)),
                str(root / "scripts" / "audit" / "check_core_bare.py"),
                "--repo",
                str(root),
                "--fix",
                "-q",
            ],
            check=False,
            timeout=30,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return


def command_env() -> None:
    env = {
        "BROWSER": "echo",
        "CLICOLOR": "0",
        "EDITOR": "ed",
        "GH_BROWSER": "echo",
        "GH_EDITOR": "ed",
        "GH_PAGER": "cat",
        "GIT_ASKPASS": "ask",
        "GIT_CONFIG_COUNT": "1",
        "GIT_EDITOR": "ed",
        "GIT_EXTERNAL_DIFF": "echo",
        "GIT_PAGER": "cat",
        "GIT_SEQUENCE_EDITOR": "ed",
        "GIT_SSH": "ssh",
        "GIT_SSH_COMMAND": "ssh",
        "NO_COLOR": "1",
        "PAGER": "cat",
        "SSH_ASKPASS": "ask",
        "SSH_ASKPASS_REQUIRE": "force",
        "VISUAL": "ed",
    }
    subprocess.run(["git", "rev-parse", "--git-dir"], env=env, check=False, timeout=30)


def _blocked(fn) -> None:
    try:
        fn()
    except FileNotFoundError:
        return


def config_shapes() -> None:
    _blocked(
        lambda: subprocess.run(
            ["git", "-c", "core.pager=less", "rev-parse", "--git-dir"],
            check=False,
            timeout=30,
        )
    )
    _blocked(lambda: subprocess.run(["git", "-cname=value", "status"], check=False, timeout=30))
    _blocked(lambda: subprocess.run(["git", "--config-env", "foo=BAR", "status"], check=False, timeout=30))
    _blocked(lambda: subprocess.run(["gh", "api", "--paginate"], check=False, timeout=30))


_CASES = {
    "argv0_override": argv0_override,
    "asyncio_exec": asyncio_exec,
    "asyncio_shell": asyncio_shell,
    "bash_c": bash_c,
    "bytes_argv": bytes_argv,
    "command_env": command_env,
    "concurrent_starts": concurrent_starts,
    "config_shapes": config_shapes,
    "crash": crash,
    "descendant": descendant,
    "env_wrap": env_wrap,
    "executable_override": executable_override,
    "explicit_pager": explicit_pager,
    "fork_child": fork_child,
    "fstring_shell": fstring_shell,
    "inherited_pager": inherited_pager,
    "launch_keyword": launch_keyword,
    "launch_positional": launch_positional,
    "nice_wrap": nice_wrap,
    "noop": noop,
    "os_exec": os_exec,
    "os_system": os_system,
    "os_system_git": os_system_git,
    "path_tripwire": path_tripwire,
    "posix_spawn": posix_spawn,
    "putenv_pager": putenv_pager,
    "python_c": python_c,
    "python_loader_redirect": python_loader_redirect,
    "redirect_mutation": redirect_mutation,
    "second_level": second_level,
    "shell_git_alias": shell_git_alias,
    "shim_then_forbidden": shim_then_forbidden,
    "sleeper": sleeper,
    "swallow": swallow,
    "timeout_wrap": timeout_wrap,
    "value_runner": value_runner,
}


def main() -> None:
    case = os.environ["HOOK_RUNTIME_CASE"]
    _CASES[case]()


if __name__ == "__main__":
    main()
