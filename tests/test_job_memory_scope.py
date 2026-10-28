"""A detached job executes only after the kernel confirms its finite pool caps."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POOL = "/user.slice/user-4242.slice/user@4242.service/lu.slice"


@pytest.fixture
def job_scope(tmp_path: Path):
    cgroups = tmp_path / "cgroups"
    relative = POOL + "/fixture.service"
    group = cgroups / relative.lstrip("/")
    group.mkdir(parents=True)
    (group / "memory.max").write_text("201326592\n")
    (group / "memory.swap.max").write_text("0\n")
    (group.parent / "memory.max").write_text("1073741824\n")
    (group.parent / "memory.swap.max").write_text("536870912\n")
    proc = tmp_path / "cgroup"
    proc.write_text("0::" + relative + "\n")
    source = (ROOT / "scripts/lib/job_memory_scope.sh").read_text()
    # Kernel boundaries only, as in the launcher scope sandbox. Production
    # cannot select a fake cgroup filesystem through arguments/environment.
    source = source.replace("/proc/self/cgroup", str(proc)).replace("/sys/fs/cgroup", str(cgroups))
    entry = tmp_path / "entry.sh"
    entry.write_text(source)
    marker = tmp_path / "started"

    def run():
        return subprocess.run(
            ["bash", str(entry), "201326592", "--", "bash", "-c",
             f"printf '%s\\n' 'a b' > {shlex.quote(str(marker))}; exit 42"],
            capture_output=True, text=True, timeout=10, check=False,
        )

    return group, proc, marker, run


def test_verified_job_keeps_arguments_and_its_own_status(job_scope):
    _, _, marker, run = job_scope
    result = run()
    assert result.returncode == 42, result.stderr
    assert marker.read_text() == "a b\n"


@pytest.mark.parametrize("failure", ["outside_pool", "unbounded_job", "wrong_max", "job_swap",
                                     "unbounded_pool", "pool_swap", "missing_limit"])
def test_unverified_job_never_executes_workload(job_scope, failure):
    group, proc, marker, run = job_scope
    if failure == "outside_pool":
        proc.write_text("0::/user.slice/user-4242.slice/user@4242.service/app.slice/fixture.service\n")
    elif failure == "unbounded_job":
        (group / "memory.max").write_text("max\n")
    elif failure == "wrong_max":
        (group / "memory.max").write_text("402653184\n")
    elif failure == "job_swap":
        (group / "memory.swap.max").write_text("max\n")
    elif failure == "unbounded_pool":
        (group.parent / "memory.max").write_text("max\n")
    elif failure == "pool_swap":
        (group.parent / "memory.swap.max").write_text("max\n")
    else:
        (group / "memory.max").unlink()
    result = run()
    assert result.returncode == 6, result.stderr
    assert "JOB_SCOPE_REFUSED" in result.stderr
    assert not marker.exists()
