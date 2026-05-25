import os
from unittest.mock import patch

import pytest

from scripts.audit.check_mdx_source_parity import MDX_DIR, SOURCE_DIR, check_parity, main


@pytest.fixture
def mock_env():
    with patch.dict(os.environ, clear=True):
        yield

@pytest.fixture
def mock_subprocess():
    with patch("scripts.audit.check_mdx_source_parity.subprocess.check_output") as m:
        yield m

@pytest.fixture
def mock_legacy_levels():
    with patch("scripts.audit.check_mdx_source_parity.get_legacy_levels", return_value={"hist", "bio", "lit"}):
        yield

def test_check_parity_mdx_only(mock_legacy_levels, mock_subprocess):
    # MDX-only diff (should fail)
    mdx_files = [MDX_DIR / "a1" / "01-hello.mdx"]
    changed_files = {MDX_DIR / "a1" / "01-hello.mdx"}
    mock_subprocess.return_value = "1 file changed\n" # Not whitespace-only

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 1
    assert "MDX file changed but no source files changed" in violations[0][1]

def test_check_parity_mdx_and_source(mock_legacy_levels, mock_subprocess):
    # MDX + source diff (pass)
    mdx_files = [MDX_DIR / "a1" / "01-hello.mdx"]
    changed_files = {
        MDX_DIR / "a1" / "01-hello.mdx",
        SOURCE_DIR / "a1" / "01-hello" / "01-hello.md"
    }
    mock_subprocess.return_value = "1 file changed\n"

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

def test_check_parity_source_only(mock_legacy_levels, mock_subprocess):
    # source-only diff (pass)
    mdx_files = []
    changed_files = {
        SOURCE_DIR / "a1" / "01-hello" / "01-hello.md"
    }

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

def test_check_parity_legacy_level(mock_legacy_levels, mock_subprocess):
    # legacy-level MDX-only (pass via allowlist)
    mdx_files = [MDX_DIR / "hist" / "01-history.mdx"]
    changed_files = {MDX_DIR / "hist" / "01-history.mdx"}
    mock_subprocess.return_value = "1 file changed\n"

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

def test_check_parity_whitespace_only(mock_legacy_levels, mock_subprocess):
    # whitespace-only MDX diff (pass per the exemption)
    mdx_files = [MDX_DIR / "a1" / "01-hello.mdx"]
    changed_files = {MDX_DIR / "a1" / "01-hello.mdx"}

    # Mock is_whitespace_only returning empty string
    mock_subprocess.return_value = ""

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

def test_main_bulk_regen_env_var(mock_env, mock_subprocess, mock_legacy_levels):
    # bulk-regen MDX-only with env var (pass)
    os.environ["MDX_PARITY_BULK_REGEN"] = "1"

    mdx_paths = [f"starlight/src/content/docs/a1/{i}.mdx" for i in range(51)]
    mock_subprocess.return_value = "\n".join(mdx_paths)

    # We pass --changed-vs-base origin/main
    exit_code = main(["--changed-vs-base", "origin/main"])
    assert exit_code == 0

def test_main_single_file_regen_env_var(mock_env, mock_subprocess, mock_legacy_levels):
    # single-file regen without env var (fail) or with env var but only 1 file (fail)
    os.environ["MDX_PARITY_BULK_REGEN"] = "1"

    mdx_paths = ["starlight/src/content/docs/a1/01-hello.mdx"]

    def side_effect(cmd, **kwargs):
        if "merge-base" in cmd:
            return "mergebase"
        elif "--shortstat" in cmd:
            return "1 file changed\n" # Not whitespace-only
        else:
            return "\n".join(mdx_paths)

    mock_subprocess.side_effect = side_effect

    exit_code = main(["--changed-vs-base", "origin/main"])
    assert exit_code == 1
