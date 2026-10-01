"""A review attempt refuses when its prompt was rendered against other code than its seat would run (#9163)."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime.review_mcp import check_review_contract
from scripts.common.git_context import sanitized_git_env
from scripts.review import render_contract
from scripts.review.render_contract import (
    LOCK_FILE,
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
#: relative import of its own, a lazily imported module, a git-ignored module and a third-party package (as the
#: real one imports ``learn_ukrainian_v4_runtime``), which is not traced: the lock stands for it.
SERVER_SOURCE = """\
import json

import local_settings
import tools
from lu_fake_runtime.transport import handle
from scripts.verification import vesum


def handler():
    from rag.source_query import lookup

    return json.dumps(lookup())
"""
FILES = {
    ".gitignore": ".worktrees/\n__pycache__/\nscripts/local_settings.py\n",
    SERVER_FILE: SERVER_SOURCE,
    ".mcp/servers/sources/TOOL_RESULT_V1.md": "# tool result\n",
    LOCK_FILE: "anyio==4.15.1\n./packages/v4-runtime\n",
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
def checkouts(tmp_path: Path) -> tuple[Path, Path]:
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
    # Beside the repository files, one component: the lock pinning the third-party packages.
    code = server_code(primary)
    assert code.lock_sha256 == hashlib.sha256(FILES[LOCK_FILE].encode()).hexdigest()
    assert list(code.components()) == ["repository", LOCK_FILE]


def test_a_module_created_for_an_existing_import_changes_the_digest(checkouts: tuple[Path, Path]) -> None:
    """A file added where an import already looks is part of the digest, without editing that import again."""
    primary, _worktree = checkouts
    morph = primary / "scripts/verification/morph.py"
    morph.write_text(morph.read_text(encoding="utf-8") + "\nfrom . import created\n", encoding="utf-8")
    before = server_code_digest(primary)
    assert "scripts/verification/created.py" not in server_code_files(primary)

    (primary / "scripts/verification/created.py").write_text("VALUE = 1\n", encoding="utf-8")

    assert server_code_digest(primary) != before
    assert "scripts/verification/created.py" in server_code_files(primary)


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
        pytest.param(LOCK_FILE, "server code", id="lock"),
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
    with pytest.raises(ReviewContractError, match=rf"review_render_record_missing: .* holds no version {render_contract.RENDER_RECORD_VERSION}"):
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


def test_a_changed_lock_refuses_by_name(tmp_path: Path, checkouts: tuple[Path, Path]) -> None:
    """Third-party code is not traced; the lock that pins it is a named component of the digest."""
    primary, _worktree = checkouts
    prompt = _render(primary, tmp_path / "out" / "prompt.md")
    rendered_as = server_code(primary).components()[LOCK_FILE]
    _write(primary, LOCK_FILE, "anyio==4.16.0\n./packages/v4-runtime\n")

    with pytest.raises(ReviewContractError) as refused:
        check_review_contract(prompt, PROMPT_TEXT, server_checkout=primary)

    message = str(refused.value)
    print(message)
    now = server_code(primary).components()[LOCK_FILE]
    assert "review_render_record_digest_mismatch: the prompt was rendered against different server code" in message
    assert f"differing server components: {LOCK_FILE}: {rendered_as} -> {now}" in message


def test_a_checkout_without_the_lock_refuses_by_name(tmp_path: Path, checkouts: tuple[Path, Path]) -> None:
    primary, worktree = checkouts
    prompt = _render(worktree, tmp_path / "out" / "prompt.md")
    (primary / LOCK_FILE).unlink()

    with pytest.raises(ReviewContractError) as refused:
        check_review_contract(prompt, PROMPT_TEXT, server_checkout=primary)

    message = str(refused.value)
    print(message)
    assert message.startswith(f"review attempt refused: review_server_lock_missing: cannot read {primary / LOCK_FILE}")
    with pytest.raises(ReviewContractError, match="review_server_lock_missing"):
        _render(primary, tmp_path / "out" / "again.md")


def test_a_change_in_an_untraced_third_party_package_alone_does_not_refuse(
    tmp_path: Path, checkouts: tuple[Path, Path]
) -> None:
    """Documented behaviour: code outside the repository is not traced; only a lock change reaches the digest."""
    primary, _worktree = checkouts
    site = tmp_path / "site"
    _write(site, "lu_fake_runtime/__init__.py", "")
    _write(site, "lu_fake_runtime/transport.py", "def handle():\n    return 'receipt'\n")
    prompt = _render(primary, tmp_path / "out" / "prompt.md")

    _write(site, "lu_fake_runtime/transport.py", "def handle():\n    return 'another receipt'\n")

    contract = check_review_contract(prompt, PROMPT_TEXT, server_checkout=primary)
    assert contract["server_digest"] == contract["render_server_digest"]


def test_the_launch_check_refuses_a_server_changed_since_admission(
    tmp_path: Path, checkouts: tuple[Path, Path]
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
    with pytest.raises(ReviewContractError, match="review_server_changed"):
        check_launch_contract(contract, primary, tmp_path / "other" / "bin" / "python")


def _closure_by_main_rules(checkout: Path) -> dict[str, str]:
    """File hashes from origin/main's walk: ``ast.parse``, ``ast.walk``, and path-based resolution.

    Independent of the production cache. A scanner that drops a real import, or follows one that does not
    parse, disagrees with this set.
    """
    root = Path(checkout).resolve()
    entry = root / SERVER_FILE
    roots = (root / "scripts", root, entry.resolve().parent)

    def scan(directories: tuple[Path, ...], leaf: str) -> tuple[tuple[Path, ...], tuple[Path, ...]] | None:
        portions: list[Path] = []
        for directory in directories:
            package = directory / leaf
            if (package / "__init__.py").is_file():
                return ((package / "__init__.py",), (package,))
            if (directory / f"{leaf}.py").is_file():
                return ((directory / f"{leaf}.py",), ())
            if package.is_dir():
                portions.append(package)
        return ((), tuple(portions)) if portions else None

    found: dict[str, tuple[tuple[Path, ...], tuple[Path, ...]] | None] = {}

    def find(name: str) -> tuple[tuple[Path, ...], tuple[Path, ...]] | None:
        if name in found:
            return found[name]
        parent, _, leaf = name.rpartition(".")
        module: tuple[tuple[Path, ...], tuple[Path, ...]] | None = None
        if parent:
            owner = find(parent)
            if owner is not None and owner[1]:
                module = scan(owner[1], leaf)
        elif name not in sys.builtin_module_names:
            module = scan(roots, leaf)
        found[name] = module
        return module

    def imported_names(tree: ast.AST, package: str) -> list[str]:
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    anchor = package.split(".") if package else []
                    if not package or node.level - 1 >= len(anchor):
                        continue
                    anchor = anchor[: len(anchor) - (node.level - 1)]
                    base = ".".join([*anchor, *([node.module] if node.module else [])])
                if not base:
                    continue
                targets = [base, *(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")]
            else:
                continue
            for target in targets:
                parts = target.split(".")
                names.extend(".".join(parts[: index + 1]) for index in range(len(parts)))
        return names

    hashes: dict[str, str] = {}
    pending: list[tuple[Path, str]] = [(entry, "")]
    while pending:
        path, package = pending.pop()
        key = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()
        if key in hashes:
            continue
        data = path.read_bytes()
        hashes[key] = hashlib.sha256(data).hexdigest()
        try:
            tree = ast.parse(data)
        except (SyntaxError, ValueError):
            tree = None
        names = list(dict.fromkeys(imported_names(tree, package))) if tree is not None else []
        for name in names:
            module = find(name)
            if module is None:
                continue
            for file in module[0]:
                pending.append((file, name if file.name == "__init__.py" else name.rpartition(".")[0]))
    return dict(sorted(hashes.items()))


def _assert_same_closure_as_main(root: Path) -> None:
    actual = server_code(root)
    expected_files = _closure_by_main_rules(root)
    assert actual.files == expected_files
    lock_sha256 = hashlib.sha256((root / LOCK_FILE).read_bytes()).hexdigest()
    assert actual.lock_sha256 == lock_sha256
    assert actual.digest == render_contract.ServerCode(files=expected_files, lock_sha256=lock_sha256).digest


# Real imports the rejected scanner dropped, and imports that only look real inside text it mishandled.
_COUNTEREXAMPLE_SERVER = '''\
import kept_top
if flag: import kept_inline_if
def load(): import kept_inline_function

def nested():
    import kept_inside_function_body

# comment with """ triple
import kept_after_comment

label = 'see """ inside a string'
import kept_after_string

sample = "import not_from_string"
# import not_from_comment

def documented():
    """
    import not_executed
    """
    return 1

import broken_mod
'''

_KEPT_IMPORTS = (
    "kept_top",
    "kept_inline_if",
    "kept_inline_function",
    "kept_inside_function_body",
    "kept_after_comment",
    "kept_after_string",
)
_IGNORED_IMPORTS = ("sneaky_mod", "not_from_string", "not_from_comment", "not_executed")


def _counterexample_tree(root: Path) -> None:
    _write(root, SERVER_FILE, _COUNTEREXAMPLE_SERVER)
    _write(root, LOCK_FILE, "lock\n")
    _write(root, "scripts/broken_mod.py", "def f(:\nimport sneaky_mod\n")
    for name in (*_KEPT_IMPORTS, *_IGNORED_IMPORTS):
        _write(root, f"scripts/{name}.py", "VALUE = 1\n")


def test_import_closure_matches_main_on_the_reviewer_counterexamples(tmp_path: Path) -> None:
    """One-line ``if``/function imports, quotes in comments and strings, and a module that does not parse."""
    root = tmp_path / "checkout"
    _counterexample_tree(root)

    _assert_same_closure_as_main(root)
    files = server_code_files(root)
    for name in _KEPT_IMPORTS:
        assert f"scripts/{name}.py" in files
    assert "scripts/broken_mod.py" in files
    for name in _IGNORED_IMPORTS:
        assert f"scripts/{name}.py" not in files


def test_equal_size_edit_with_restored_mtime_changes_the_digest(tmp_path: Path) -> None:
    """A same-length edit whose mtime is put back still changes the closure digest."""
    root = tmp_path / "checkout"
    _write(root, SERVER_FILE, "import kept\n")
    _write(root, LOCK_FILE, "lock\n")
    target = root / "scripts" / "kept.py"
    _write(root, "scripts/kept.py", "VALUE = 1\n")
    before = server_code(root)
    _assert_same_closure_as_main(root)

    stamp = target.stat()
    original = target.read_bytes()
    rewritten = original.replace(b"VALUE = 1", b"VALUE = 2")
    assert len(rewritten) == len(original) and rewritten != original
    target.write_bytes(rewritten)
    os.utime(target, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    assert target.stat().st_size == stamp.st_size
    assert target.stat().st_mtime_ns == stamp.st_mtime_ns

    after = server_code(root)
    _assert_same_closure_as_main(root)
    assert after.digest != before.digest
    assert after.files["scripts/kept.py"] != before.files["scripts/kept.py"]


def test_new_init_py_in_an_imported_namespace_package_changes_the_closure(tmp_path: Path) -> None:
    """Adding ``__init__.py`` to a namespace package already imported is part of the next digest."""
    root = tmp_path / "checkout"
    _write(root, SERVER_FILE, "import scripts.ns.mod\n")
    _write(root, LOCK_FILE, "lock\n")
    _write(root, "scripts/__init__.py", "")
    _write(root, "scripts/ns/mod.py", "VALUE = 1\n")
    _write(root, "scripts/kept_from_init.py", "VALUE = 1\n")
    before = server_code(root)
    _assert_same_closure_as_main(root)
    assert "scripts/ns/__init__.py" not in before.files
    assert "scripts/ns/mod.py" in before.files
    assert "scripts/kept_from_init.py" not in before.files

    _write(root, "scripts/ns/__init__.py", "import kept_from_init\n")

    after = server_code(root)
    _assert_same_closure_as_main(root)
    assert "scripts/ns/__init__.py" in after.files
    assert "scripts/kept_from_init.py" in after.files
    assert after.digest != before.digest
