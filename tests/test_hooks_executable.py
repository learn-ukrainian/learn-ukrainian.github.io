import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def test_hooks_are_executable_in_git():
    """Verify that all hooks in agents_extensions/shared/hooks/ have the 100755 executable permission in git."""
    hooks_dir = REPO_ROOT / "agents_extensions" / "shared" / "hooks"
    assert hooks_dir.is_dir(), f"Hooks directory not found at {hooks_dir}"

    # Run git ls-files -s to inspect the staging area/index file modes
    cmd = ["git", "ls-files", "-s", "agents_extensions/shared/hooks/"]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    lines = res.stdout.strip().split("\n")
    assert lines and lines[0], "No hook files tracked under agents_extensions/shared/hooks/"

    non_executable = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            mode = parts[0]
            path = parts[3]
            # Mode must be 100755 for executable files in git
            if mode != "100755":
                non_executable.append((path, mode))

    assert not non_executable, f"Found non-executable hook files in git tree (expected 100755): {non_executable}"
