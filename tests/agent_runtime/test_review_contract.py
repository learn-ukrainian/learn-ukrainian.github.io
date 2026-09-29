"""A review attempt refuses when its prompt was rendered against other code than its seat would run (#9163)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime.review_mcp import check_review_contract
from scripts.common.git_context import sanitized_git_env
from scripts.review import render_contract
from scripts.review.render_contract import (
    RENDER_RECORD_KEY,
    ReviewContractError,
    check_launch_contract,
    render_record,
    render_record_path,
    server_code,
    server_code_digest,
    server_code_files,
)

SERVER_FILE = ".mcp/servers/sources/server.py"
PROMPTS = "scripts/review/prompts"
LOADED_TEMPLATE = "lesson-review.md.j2"
PROMPT_TEXT = "Copy the outcome printed beside each receipt.\n"

#: A server that imports the way the real one does: a module beside it (a symlink), a package module with a
#: relative import of its own, a lazily imported module, a git-ignored module, an installed distribution (as the
#: real one imports ``learn_ukrainian_v4_runtime``) and an optional import that is not installed.
SERVER_SOURCE = """\
import json

import local_settings
import tools
from lu_fake_runtime.transport import handle
from scripts.verification import vesum

try:
    import lu_optional_accelerator
except ImportError:
    lu_optional_accelerator = None


def handler():
    from rag.source_query import lookup

    return json.dumps(lookup())
"""
FILES = {
    ".gitignore": ".worktrees/\n__pycache__/\nscripts/local_settings.py\n",
    SERVER_FILE: SERVER_SOURCE,
    ".mcp/servers/sources/TOOL_RESULT_V1.md": "# tool result\n",
    "lib/tools_impl.py": "TOOLS = 1\n",
    "scripts/__init__.py": "",
    "scripts/verification/__init__.py": "",
    "scripts/verification/vesum.py": "from .morph import analyse\n",
    "scripts/verification/morph.py": "def analyse():\n    return 1\n",
    "scripts/rag/__init__.py": "",
    "scripts/rag/source_query.py": "def lookup():\n    return 'receipt'\n",
    "scripts/unused.py": "UNUSED = 1\n",
    f"{PROMPTS}/{LOADED_TEMPLATE}": "Copy the outcome printed beside each receipt.\n",
    f"{PROMPTS}/plan-review.md.j2": "Plan review.\n",
}
SYMLINK = ".mcp/servers/sources/tools.py"
IGNORED = "scripts/local_settings.py"
#: The installed distribution the server imports: its files, relative to the interpreter's site directory.
DISTRIBUTION = {
    "lu_fake_runtime/__init__.py": "",
    "lu_fake_runtime/transport.py": "def handle():\n    return 'receipt'\n",
}
DISTRIBUTION_FILE = "lu_fake_runtime/transport.py"


def _install(site: Path, name: str, version: str, files: dict[str, str]) -> None:
    """Install ``files`` into ``site`` as distribution ``name``, with the METADATA and RECORD an installer writes."""
    for path, text in files.items():
        _write(site, path, text)
    info = site / f"{name.replace('-', '_')}-{version}.dist-info"
    info.mkdir()
    (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n", encoding="utf-8")
    record = [f"{path},," for path in files] + [f"{info.name}/METADATA,,", f"{info.name}/RECORD,,"]
    (info / "RECORD").write_text("\n".join(record) + "\n", encoding="utf-8")


@pytest.fixture
def site(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway virtual environment holding the fake distribution, made the project interpreter: its site dir."""
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True, timeout=60)
    python = venv / "bin" / "python"
    site_dir = Path(
        subprocess.run(
            [str(python), "-c", "import site; print(site.getsitepackages()[0])"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout.strip()
    )
    _install(site_dir, "lu-fake-runtime", "1.0.0", DISTRIBUTION)
    monkeypatch.setattr(render_contract, "project_interpreter", lambda: python)
    return site_dir


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        env=sanitized_git_env(),
        timeout=30,
    )


def _write(checkout: Path, name: str, text: str) -> None:
    (checkout / name).parent.mkdir(parents=True, exist_ok=True)
    (checkout / name).write_text(text, encoding="utf-8")


@pytest.fixture
def checkouts(tmp_path: Path, site: Path) -> tuple[Path, Path]:
    """A temporary primary checkout and one linked worktree holding the same code: ``(primary, worktree)``."""
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    _git(primary, "config", "user.email", "test@example.com")
    _git(primary, "config", "user.name", "Test")
    for name, text in FILES.items():
        _write(primary, name, text)
    os.symlink("../../../lib/tools_impl.py", primary / SYMLINK)
    _git(primary, "add", "--", *FILES, SYMLINK)
    _git(primary, "commit", "-q", "-m", "init")
    worktree = primary / ".worktrees" / "dispatch" / "claude" / "task"
    _git(primary, "worktree", "add", "-q", "-b", "claude/task", str(worktree))
    for checkout in (primary, worktree):
        _write(checkout, IGNORED, "DEBUG = False\n")  # ignored by git, so each checkout holds its own
    return primary.resolve(), worktree.resolve()


def _render(checkout: Path, prompt_file: Path, text: str = PROMPT_TEXT) -> Path:
    """Write a prompt and its render record the way ``render_prompt`` does, as rendered in ``checkout``."""
    prompts_dir = checkout / PROMPTS
    loaded = {LOADED_TEMPLATE: hashlib.sha256((prompts_dir / LOADED_TEMPLATE).read_bytes()).hexdigest()}
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(text, encoding="utf-8")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    sidecar = {
        "files_read": [],
        "template_sha256": {},
        RENDER_RECORD_KEY: render_record(checkout, prompts_dir, loaded, sha),
    }
    render_record_path(prompt_file).write_text(json.dumps(sidecar), encoding="utf-8")
    return prompt_file


def test_server_code_is_the_entry_and_every_repository_module_it_imports(checkouts: tuple[Path, Path]) -> None:
    primary, _worktree = checkouts
    (primary / ".mcp/servers/sources/__pycache__").mkdir()
    (primary / ".mcp/servers/sources/__pycache__/server.cpython-312.pyc").write_bytes(b"\x00bytecode")

    files = server_code_files(primary)

    assert list(files) == sorted(
        [
            SERVER_FILE,
            SYMLINK,
            IGNORED,
            "scripts/__init__.py",
            "scripts/rag/__init__.py",
            "scripts/rag/source_query.py",
            "scripts/verification/__init__.py",
            "scripts/verification/morph.py",
            "scripts/verification/vesum.py",
        ]
    )
    # A symlink contributes its target's bytes, not the link text.
    assert files[SYMLINK] == hashlib.sha256(FILES["lib/tools_impl.py"].encode()).hexdigest()
    assert server_code_digest(primary) == server_code_digest(primary)
    # The installed distribution it imports, by name and version, each of its modules hashed; an optional import
    # that is not installed is recorded as absent (the standard library's ``json`` is neither).
    code = server_code(primary)
    (runtime,) = code.distributions.values()
    assert (runtime.name, runtime.version) == ("lu-fake-runtime", "1.0.0")
    assert runtime.files == {path: hashlib.sha256(text.encode()).hexdigest() for path, text in DISTRIBUTION.items()}
    assert code.absent == ("lu_optional_accelerator",)
    assert list(code.components()) == ["repository", "distribution lu-fake-runtime", "absent optional imports"]


def test_rendered_in_a_skewed_worktree_and_run_by_the_primary_server_refuses(
    tmp_path: Path, checkouts: tuple[Path, Path]
) -> None:
    """Finding 1: the render checkout's server code is what the prompt matches, not the dispatcher's."""
    primary, worktree = checkouts
    _write(worktree, "scripts/verification/morph.py", "def analyse():\n    return 2\n")
    _git(worktree, "commit", "-q", "-am", "the server prints something else")
    prompt = _render(worktree, tmp_path / "out" / "prompt.md")

    with pytest.raises(ReviewContractError) as refused:
        check_review_contract(prompt, PROMPT_TEXT, server_checkout=primary)

    message = str(refused.value)
    print(message)
    assert "review_contract_mismatch" in message
    assert "rendered against different server code than this attempt would run\n" in message
    assert "differing server components: repository: sha256:" in message
    assert f"rendered in: {worktree} server digest {server_code_digest(worktree)}" in message
    assert f"sources server (primary checkout): {primary} server digest {server_code_digest(primary)}" in message
    assert "fix: pull the primary checkout to origin/main, then re-render and retry" in message


def test_rendered_in_a_matching_worktree_proceeds_and_records_the_digests(
    tmp_path: Path, checkouts: tuple[Path, Path]
) -> None:
    primary, worktree = checkouts
    prompt = _render(worktree, tmp_path / "out" / "prompt.md")

    contract = check_review_contract(prompt, PROMPT_TEXT, server_checkout=primary)

    assert contract["render_checkout"] == str(worktree)
    assert contract["server_checkout"] == str(primary)
    assert contract["render_server_digest"] == contract["server_digest"] == server_code_digest(primary)
    assert contract["render_template_digest"] == contract["template_digest"]
    assert contract["templates"] == [LOADED_TEMPLATE]
    assert contract["prompt_sha256"] == hashlib.sha256(PROMPT_TEXT.encode()).hexdigest()


@pytest.mark.parametrize(
    ("changed", "refuses"),
    [
        pytest.param("scripts/verification/morph.py", "server code", id="module-imported-outside-server-dir"),
        pytest.param("scripts/rag/source_query.py", "server code", id="lazily-imported-module"),
        pytest.param("lib/tools_impl.py", "server code", id="symlink-target"),
        pytest.param(IGNORED, "server code", id="git-ignored-imported-module"),
        pytest.param(f"{PROMPTS}/{LOADED_TEMPLATE}", "templates", id="loaded-template"),
        pytest.param("scripts/unused.py", None, id="unimported-module"),
        pytest.param(".mcp/servers/sources/TOOL_RESULT_V1.md", None, id="document-in-server-dir"),
        pytest.param(f"{PROMPTS}/plan-review.md.j2", None, id="template-the-render-did-not-load"),
    ],
)
def test_only_code_the_attempt_runs_decides(
    tmp_path: Path, checkouts: tuple[Path, Path], changed: str, refuses: str | None
) -> None:
    """Findings 2 and 4: what the server executes and the templates the render loaded, nothing else."""
    primary, _worktree = checkouts
    prompt = _render(primary, tmp_path / "out" / "prompt.md")
    target = (primary / changed).resolve()  # a symlink's target is what changes
    target.write_text(target.read_text(encoding="utf-8") + "# changed after rendering\n", encoding="utf-8")

    if refuses is None:
        contract = check_review_contract(prompt, PROMPT_TEXT, server_checkout=primary)
        assert contract["server_digest"] == contract["render_server_digest"]
        return
    with pytest.raises(ReviewContractError, match=rf"rendered against different {refuses} than"):
        check_review_contract(prompt, PROMPT_TEXT, server_checkout=primary)


def test_a_prompt_without_its_render_record_refuses_with_its_own_code(
    tmp_path: Path, checkouts: tuple[Path, Path]
) -> None:
    primary, _worktree = checkouts
    with pytest.raises(ReviewContractError, match=r"review_render_record_missing: .*--prompt-file") as literal:
        check_review_contract(None, PROMPT_TEXT, server_checkout=primary)
    print(literal.value)

    bare = tmp_path / "bare.md"
    bare.write_text(PROMPT_TEXT, encoding="utf-8")
    with pytest.raises(ReviewContractError, match=r"review_render_record_missing: cannot read .*re-render"):
        check_review_contract(bare, PROMPT_TEXT, server_checkout=primary)

    render_record_path(bare).write_text(json.dumps({"files_read": [], "template_sha256": {}}), encoding="utf-8")
    with pytest.raises(ReviewContractError, match=r"review_render_record_missing: .* holds no version 2"):
        check_review_contract(bare, PROMPT_TEXT, server_checkout=primary)


def test_a_prompt_edited_after_rendering_refuses_as_stale(tmp_path: Path, checkouts: tuple[Path, Path]) -> None:
    primary, _worktree = checkouts
    prompt = _render(primary, tmp_path / "out" / "prompt.md")

    with pytest.raises(ReviewContractError, match=r"review_render_record_stale: the prompt file hashes to"):
        check_review_contract(prompt, PROMPT_TEXT + "edited\n", server_checkout=primary)


def test_a_checkout_without_a_sources_server_refuses_by_name(tmp_path: Path, checkouts: tuple[Path, Path]) -> None:
    primary, _worktree = checkouts
    prompt = _render(primary, tmp_path / "out" / "prompt.md")
    plain = tmp_path / "plain"
    plain.mkdir()

    with pytest.raises(ReviewContractError, match=r"no sources server at .*plain/\.mcp/servers/sources/server\.py"):
        check_review_contract(prompt, PROMPT_TEXT, server_checkout=plain)


def test_a_changed_installed_distribution_the_server_imports_refuses_by_name(
    tmp_path: Path, site: Path, checkouts: tuple[Path, Path]
) -> None:
    """Round-2 finding 1: executed code outside the repository (an installed distribution) is in the digest."""
    primary, _worktree = checkouts
    prompt = _render(primary, tmp_path / "out" / "prompt.md")
    rendered_as = server_code(primary).components()["distribution lu-fake-runtime"]
    (site / DISTRIBUTION_FILE).write_text("def handle():\n    return 'another receipt'\n", encoding="utf-8")

    with pytest.raises(ReviewContractError) as refused:
        check_review_contract(prompt, PROMPT_TEXT, server_checkout=primary)

    message = str(refused.value)
    print(message)
    now = server_code(primary).components()["distribution lu-fake-runtime"]
    assert rendered_as.startswith("1.0.0 sha256:") and now.startswith("1.0.0 sha256:") and rendered_as != now
    assert "review_contract_mismatch: the prompt was rendered against different server code" in message
    assert f"differing server components: distribution lu-fake-runtime: {rendered_as} -> {now}\n" in message


@pytest.mark.parametrize(
    ("server", "unresolved"),
    [
        pytest.param("import lu_not_installed_anywhere\n", "lu_not_installed_anywhere (found nowhere)", id="nowhere"),
        pytest.param(
            "def handler():\n    from lu_unrecorded import thing\n",
            "lu_unrecorded (at {site}/lu_unrecorded.py, installed by no distribution RECORD)",
            id="in-site-dir-without-record",
        ),
    ],
)
def test_an_import_that_resolves_nowhere_refuses_with_its_code(
    tmp_path: Path, site: Path, checkouts: tuple[Path, Path], server: str, unresolved: str
) -> None:
    primary, _worktree = checkouts
    _write(site, "lu_unrecorded.py", "thing = 1\n")  # dropped into site-packages by hand, not installed
    _write(primary, SERVER_FILE, SERVER_SOURCE + server)

    with pytest.raises(ReviewContractError) as refused:
        server_code_digest(primary)

    message = str(refused.value)
    print(message)
    assert message.startswith("review attempt refused: review_server_import_unresolved: the sources server at ")
    assert f"imports {unresolved.format(site=site)}, which resolve to neither" in message
    with pytest.raises(ReviewContractError, match="review_server_import_unresolved"):
        _render(primary, tmp_path / "out" / "prompt.md")


def test_an_absent_optional_import_installed_later_changes_the_digest(site: Path, checkouts: tuple[Path, Path]) -> None:
    primary, _worktree = checkouts
    before = server_code(primary)

    _install(site, "lu-optional-accelerator", "0.1.0", {"lu_optional_accelerator.py": "FAST = True\n"})

    after = server_code(primary)
    assert after.digest != before.digest
    assert after.absent == ()
    assert after.components()["distribution lu-optional-accelerator"].startswith("0.1.0 sha256:")


def test_the_launch_check_refuses_a_server_changed_since_admission(
    tmp_path: Path, site: Path, checkouts: tuple[Path, Path]
) -> None:
    """Round-2 finding 2: the server is digested again at launch, from exactly what the seat launches."""
    primary, worktree = checkouts
    python = render_contract.project_interpreter()
    contract = check_review_contract(_render(worktree, tmp_path / "out" / "prompt.md"), PROMPT_TEXT, primary)
    assert contract["server_interpreter"] == str(python)
    check_launch_contract(contract, primary, python)  # unchanged: launches

    _write(primary, "scripts/verification/morph.py", "def analyse():\n    return 3\n")
    with pytest.raises(ReviewContractError) as refused:
        check_launch_contract(contract, primary, python)

    message = str(refused.value)
    print(message)
    assert message.startswith(
        "review attempt refused: review_server_changed: the sources server this attempt would launch differs "
        "from the one its admission checked\n"
    )
    assert f"  admitted: {primary} with {python} server digest {contract['server_digest']}\n" in message
    assert f"  launching: {primary} with {python} server digest {server_code_digest(primary)}\n" in message
    assert "  differing server components: repository: sha256:" in message

    # Another checkout or interpreter than admission checked also refuses, even with identical code.
    _write(primary, "scripts/verification/morph.py", FILES["scripts/verification/morph.py"])
    with pytest.raises(ReviewContractError, match="review_server_changed"):
        check_launch_contract(contract, worktree, python)
    twin = tmp_path / "venv-twin"  # the same distributions under another interpreter
    shutil.copytree(python.parent.parent, twin, symlinks=True)
    assert server_code_digest(primary, twin / "bin" / "python") == contract["server_digest"]
    with pytest.raises(ReviewContractError, match="review_server_changed"):
        check_launch_contract(contract, primary, twin / "bin" / "python")
