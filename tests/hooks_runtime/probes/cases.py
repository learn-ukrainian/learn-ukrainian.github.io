"""Runtime probes. The case name is HOOK_RUNTIME_CASE. Nothing runs at import."""

from __future__ import annotations

import asyncio
import os
import subprocess
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
    "asyncio_exec": asyncio_exec,
    "bytes_argv": bytes_argv,
    "command_env": command_env,
    "concurrent_starts": concurrent_starts,
    "config_shapes": config_shapes,
    "crash": crash,
    "descendant": descendant,
    "explicit_pager": explicit_pager,
    "fork_child": fork_child,
    "inherited_pager": inherited_pager,
    "launch_keyword": launch_keyword,
    "launch_positional": launch_positional,
    "noop": noop,
    "os_exec": os_exec,
    "os_system": os_system,
    "posix_spawn": posix_spawn,
    "second_level": second_level,
    "sleeper": sleeper,
    "swallow": swallow,
    "value_runner": value_runner,
}


def main() -> None:
    case = os.environ["HOOK_RUNTIME_CASE"]
    _CASES[case]()


if __name__ == "__main__":
    main()
