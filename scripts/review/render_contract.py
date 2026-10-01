"""What a rendered review prompt was rendered against, and whether a review attempt still matches it (#9163).

A review seat's sources MCP server launches from the primary checkout, while its prompt may be rendered in any
checkout. The prompt tells the seat what the server prints, so the prompt's templates and the server code that
answers the seat must come from the same code. At render time ``render_record`` records, beside the prompt, the
checkout that rendered it, the templates that render actually loaded and that checkout's server-code digest. At
dispatch ``check_render_contract`` compares that record with the server code the attempt would run and with the
render checkout's templates as they are now, and refuses on any difference. Formal manifest admission then
re-renders against server templates with ``check_prompt``; the recorded reads, hashes and logical names returned
here must match that independently observed dependency set (#9378).

The server-code digest has two components. ``repository``: the server entry plus every repository module it
imports, found by a static walk of its ``import`` statements resolved the way the server's own ``sys.path``
resolves them (``scripts/``, then the repository root, then the server's directory). Files are read from disk
whatever git thinks of them (ignored, untracked or dirty), and a symlink contributes its target's bytes. Imports
made dynamically (``importlib``) are not seen; the server makes none. An import outside the repository (standard
library or third-party) is not traced. ``requirements-lock.txt``: the sha256 of the checkout's lock file, which
pins every third-party package the project environment is built from; a checkout without it refuses.

Digests are recomputed at render, at admission (``check_render_contract`` checks both the recorded render
checkout and the actual server checkout), and at launch
(``check_launch_contract``, called by ``review_mcp.prepare_review_attempt`` on the exact checkout and interpreter
it writes into the seat's MCP configuration), so an update of the primary checkout between admission and launch
refuses too.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.common.repo_root import project_interpreter

#: The sources server a review seat calls, relative to a checkout.
SERVER_ENTRY = ".mcp/servers/sources/server.py"
#: The lock pinning every third-party package the project environment is built from, relative to a checkout.
LOCK_FILE = "requirements-lock.txt"
#: Key of the render record inside the prompt's ``<prompt>.files_read.json`` sidecar.
RENDER_RECORD_KEY = "render_contract"
RENDER_RECORD_VERSION = 4
_SERVER_DIGEST_VERSION = b"lu-review-server-code-digest-v3"
_REPOSITORY_DIGEST_VERSION = b"lu-review-server-repository-digest-v1"
_TEMPLATE_DIGEST_VERSION = b"lu-review-template-digest-v1"
_MISSING = "missing"
_FIX = "pull the primary checkout to origin/main, then re-render and retry"
_RERENDER = (
    "re-render the prompt with `python -m scripts.review.prompts.render <manifest> --output <prompt> "
    "--review-id <id> --attempt-id <id>`, then retry with --prompt-file <prompt>"
)


class ReviewContractError(ValueError):
    """A review attempt's prompt cannot be tied to the code it was rendered against, or that code differs (#9163)."""


@dataclass(frozen=True)
class _Module:
    files: tuple[Path, ...]  # the file this module executes: an ``__init__.py``, a ``.py`` module, or none
    search: tuple[Path, ...]  # its submodule search path (a package's ``__path__``); empty for a plain module


class _ModuleFinder:
    """Resolves dotted names to repository files the way a path-based import would, over fixed roots."""

    def __init__(self, roots: Iterable[Path]):
        self.roots = tuple(roots)
        self._cache: dict[str, _Module | None] = {}

    def find(self, name: str) -> _Module | None:
        if name in self._cache:
            return self._cache[name]
        parent, _, leaf = name.rpartition(".")
        found: _Module | None = None
        if parent:
            owner = self.find(parent)
            if owner is not None and owner.search:
                found = self._scan(owner.search, leaf)
        elif name not in sys.builtin_module_names:
            found = self._scan(self.roots, leaf)
        self._cache[name] = found
        return found

    @staticmethod
    def _scan(directories: Iterable[Path], leaf: str) -> _Module | None:
        portions: list[Path] = []
        for directory in directories:
            package = directory / leaf
            if (package / "__init__.py").is_file():
                return _Module((package / "__init__.py",), (package,))
            if (directory / f"{leaf}.py").is_file():
                return _Module((directory / f"{leaf}.py",), ())
            if package.is_dir():
                portions.append(package)
        return _Module((), tuple(portions)) if portions else None


def _imported_names(tree: ast.AST, package: str) -> list[str]:
    """Every module name an ``import``/``from … import`` in ``tree`` may load, with its parent packages."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                anchor = package.split(".") if package else []
                if not package or node.level - 1 >= len(anchor):
                    continue  # a relative import that could not run
                anchor = anchor[: len(anchor) - (node.level - 1)]
                base = ".".join([*anchor, *([node.module] if node.module else [])])
            if not base:
                continue
            # ``from pkg import name`` loads ``pkg.name`` when that is a submodule.
            targets = [base, *(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")]
        else:
            continue
        for target in targets:
            parts = target.split(".")
            names.extend(".".join(parts[: index + 1]) for index in range(len(parts)))
    return names


#: Import names by (content sha256, package): content-addressed, so a changed file can never hit a stale entry.
_IMPORTS_CACHE: dict[tuple[str, str], tuple[str, ...]] = {}


def _imports_of(sha256: str, package: str, data: bytes) -> tuple[str, ...]:
    key = (sha256, package)
    if key not in _IMPORTS_CACHE:
        try:
            tree = ast.parse(data)
        except (SyntaxError, ValueError):
            tree = None  # still hashed; a module that does not parse imports nothing
        _IMPORTS_CACHE[key] = tuple(dict.fromkeys(_imported_names(tree, package))) if tree else ()
    return _IMPORTS_CACHE[key]


def _logical(path: Path, checkout: Path) -> str:
    return path.relative_to(checkout).as_posix() if path.is_relative_to(checkout) else path.as_posix()


def _mapping_digest(version: bytes, entries: Mapping[str, str]) -> str:
    hasher = hashlib.sha256(version + b"\0")
    for name, value in entries.items():
        hasher.update(name.encode("utf-8", errors="surrogateescape") + b"\0" + value.encode("utf-8") + b"\n")
    return f"sha256:{hasher.hexdigest()}"


@dataclass(frozen=True)
class ServerCode:
    """What the sources server of a checkout executes: its repository files and the lock of its environment."""

    files: dict[str, str]  # sha256 by path, relative inside the checkout
    lock_sha256: str  # of ``LOCK_FILE``

    def components(self) -> dict[str, str]:
        """One digest per part, so a refusal can name the part that changed."""
        return {
            "repository": _mapping_digest(_REPOSITORY_DIGEST_VERSION, self.files),
            LOCK_FILE: f"sha256:{self.lock_sha256}",
        }

    @property
    def digest(self) -> str:
        return _mapping_digest(_SERVER_DIGEST_VERSION, self.components())


def server_code(checkout: Path) -> ServerCode:
    """What the sources server of ``checkout`` executes.

    The entry and each repository module it imports, recursively (a symlink is followed and its target's bytes
    hashed), and the checkout's ``LOCK_FILE``. Modules found outside the roots are not traced.

    Parsed import lists are cached for the process by the sha256 of the file's bytes. Package layout
    (``__init__.py``, a module file, or a namespace directory) is read on every walk, so a new ``__init__.py``
    changes the closure.
    """
    root = Path(checkout).resolve()
    entry = root / SERVER_ENTRY
    if not entry.is_file():
        raise ReviewContractError(f"review attempt refused: no sources server at {entry} (#9163)")
    lock = root / LOCK_FILE
    try:
        lock_sha256 = hashlib.sha256(lock.read_bytes()).hexdigest()
    except OSError as exc:
        raise ReviewContractError(
            f"review attempt refused: review_server_lock_missing: cannot read {lock}, which pins the third-party "
            f"packages the sources server runs with: {exc} (#9163)"
        ) from exc
    finder = _ModuleFinder((root / "scripts", root, entry.resolve().parent))
    hashes: dict[str, str] = {}
    pending: list[tuple[Path, str]] = [(entry, "")]
    while pending:
        path, package = pending.pop()
        key = _logical(path, root)
        if key in hashes:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ReviewContractError(f"review attempt refused: cannot read {path}: {exc} (#9163)") from exc
        hashes[key] = hashlib.sha256(data).hexdigest()
        for name in _imports_of(hashes[key], package, data):
            module = finder.find(name)
            for file in module.files if module is not None else ():
                pending.append((file, name if file.name == "__init__.py" else name.rpartition(".")[0]))
    return ServerCode(files=dict(sorted(hashes.items())), lock_sha256=lock_sha256)


def server_code_files(checkout: Path) -> dict[str, str]:
    """sha256 of every repository file the sources server of ``checkout`` executes, by path (see ``server_code``)."""
    return server_code(checkout).files


def server_code_digest(checkout: Path) -> str:
    """One deterministic digest of ``server_code``: what decides the sources server's behaviour."""
    return server_code(checkout).digest


def template_digest(templates: Mapping[str, str]) -> str:
    """One digest of the templates a render loaded: each name with the sha256 of its bytes (or ``missing``)."""
    hasher = hashlib.sha256(_TEMPLATE_DIGEST_VERSION + b"\0")
    for name in sorted(templates):
        hasher.update(name.encode("utf-8") + b"\0" + templates[name].encode("ascii") + b"\n")
    return f"sha256:{hasher.hexdigest()}"


def current_templates(prompts_dir: Path, names: Iterable[str]) -> dict[str, str]:
    """The sha256 of each named template in ``prompts_dir`` as it is on disk now; ``missing`` when it is gone."""
    current: dict[str, str] = {}
    for name in names:
        path = Path(prompts_dir) / name
        try:
            current[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            current[name] = _MISSING
    return current


def render_record(
    render_checkout: Path, prompts_dir: Path, loaded_templates: Mapping[str, str], prompt_sha256: str,
    *, review_id: str | None = None, attempt_id: str | None = None, input_root: Path | None = None,
) -> dict[str, Any]:
    """The record a render writes beside its prompt: where it rendered, what it loaded, the server it matched."""
    checkout = Path(render_checkout).resolve()
    return {
        "version": RENDER_RECORD_VERSION,
        "render_checkout": str(checkout),
        "input_root": str(Path(input_root or checkout).resolve()),
        "prompts_dir": str(Path(prompts_dir).resolve()),
        "templates": dict(sorted(loaded_templates.items())),
        "template_digest": template_digest(loaded_templates),
        **_server_fields(server_code(checkout)),
        "prompt_sha256": prompt_sha256,
        "review_id": review_id,
        "attempt_id": attempt_id,
    }


def _server_fields(code: ServerCode) -> dict[str, Any]:
    return {"server_digest": code.digest, "server_components": code.components()}


def _component_changes(then: Mapping[str, str], now: Mapping[str, str]) -> str:
    """The server components that differ, each with its value then and now: what a refusal names as changed."""
    changes = [
        f"{name}: {then.get(name, _MISSING)} -> {now.get(name, _MISSING)}"
        for name in sorted({*then, *now})
        if then.get(name) != now.get(name)
    ]
    return "; ".join(changes) or "none recorded"


def render_record_path(prompt_file: Path) -> Path:
    return prompt_file.with_name(f"{prompt_file.name}.files_read.json")


def _read_render_record(prompt_file: Path | None) -> tuple[dict[str, Any], dict[str, Any]]:
    if prompt_file is None:
        raise ReviewContractError(
            "review attempt refused: review_render_record_missing: a --review-attempt prompt must come from "
            f"--prompt-file, whose render record says what it was rendered against; {_RERENDER} (#9163)"
        )
    sidecar = render_record_path(Path(prompt_file))
    try:
        reads = json.loads(sidecar.read_text(encoding="utf-8"))
        record = reads.get(RENDER_RECORD_KEY)
    except (OSError, ValueError, AttributeError) as exc:
        raise ReviewContractError(
            f"review attempt refused: review_render_record_missing: cannot read {sidecar}: {exc}; {_RERENDER} (#9163)"
        ) from exc
    fields = ("render_checkout", "input_root", "prompts_dir", "template_digest", "server_digest", "prompt_sha256")
    if (
        not isinstance(record, dict)
        or record.get("version") != RENDER_RECORD_VERSION
        or not all(isinstance(record.get(field), str) for field in fields)
        or not isinstance(record.get("templates"), dict)
        or not record["templates"]
        or not isinstance(record.get("server_components"), dict)
        or any(
            not isinstance(key, str) or not isinstance(value, str)
            for field in ("templates", "server_components")
            for key, value in record[field].items()
        )
    ):
        raise ReviewContractError(
            f"review attempt refused: review_render_record_missing: {sidecar} holds no version "
            f"{RENDER_RECORD_VERSION} {RENDER_RECORD_KEY} record; {_RERENDER} (#9163)"
        )
    if any(
        Path(name).name != name or not name.endswith(".md.j2") or name in {".", ".."}
        for name in record["templates"]
    ):
        raise ReviewContractError(
            "review attempt refused: review_render_template_name_invalid: template names must be exact loader basenames"
        )
    if (
        not isinstance(reads.get("files_read", []), list)
        or any(not isinstance(path, str) for path in reads.get("files_read", []))
        or not isinstance(reads.get("template_sha256", {}), dict)
        or any(
            not isinstance(path, str) or not isinstance(sha, str)
            for path, sha in reads.get("template_sha256", {}).items()
        )
    ):
        raise ReviewContractError("review attempt refused: review_render_record_missing: malformed recorded reads")
    return record, reads


def check_render_contract(
    prompt_file: Path | None, prompt_text: str, server_checkout: Path, interpreter: Path | None = None,
    *, review_id: str | None = None, attempt_id: str | None = None,
) -> dict[str, Any]:
    """Refuse a review attempt whose prompt was rendered against other code than the attempt would run (#9163).

    ``server_checkout`` is where the attempt's sources server launches, with ``interpreter`` (the project
    interpreter by default). Compares the render record's server digest with that server's code now, and its
    template digest with the render checkout's loaded templates now. Returns the record the task stores: the
    digests compared, and the server components and interpreter ``check_launch_contract`` checks again at launch.
    """
    recorded, reads = _read_render_record(prompt_file)
    if (review_id is not None or attempt_id is not None) and (
        recorded.get("review_id"), recorded.get("attempt_id")
    ) != (review_id, attempt_id):
        raise ReviewContractError(
            f"review attempt refused: review_render_record_attempt_mismatch: render record belongs to another attempt; {_RERENDER}"
        )
    prompt_sha256 = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
    try:
        file_sha256 = hashlib.sha256(Path(prompt_file).read_bytes()).hexdigest() if prompt_file else prompt_sha256
    except OSError as exc:
        raise ReviewContractError("review attempt refused: review_render_record_stale: prompt bytes are unavailable") from exc
    if prompt_sha256 != recorded["prompt_sha256"] or file_sha256 != prompt_sha256:
        raise ReviewContractError(
            "review attempt refused: review_render_record_stale: the prompt file hashes to "
            f"{prompt_sha256}, its render record names {recorded['prompt_sha256']}; {_RERENDER} (#9163)"
        )
    server = Path(server_checkout).resolve()
    python = Path(interpreter) if interpreter is not None else project_interpreter()
    code = server_code(server)
    try:
        render_code = server_code(Path(recorded["render_checkout"]))
    except ReviewContractError as exc:
        raise ReviewContractError(
            "review attempt refused: review_render_record_digest_mismatch: recorded render checkout cannot be verified"
        ) from exc
    prompts_dir = Path(recorded["render_checkout"]) / "scripts/review/prompts"
    if Path(recorded["prompts_dir"]) != prompts_dir:
        raise ReviewContractError(
            "review attempt refused: review_render_record_prompts_dir_mismatch: recorded templates must come "
            f"from the render checkout's scripts/review/prompts directory; {_RERENDER}"
        )
    templates_now = current_templates(prompts_dir, recorded["templates"])
    inconsistent = [
        what for what, then, now in (
            ("server code", recorded["server_digest"], render_code.digest),
            ("server code", recorded["server_components"], render_code.components()),
            ("templates", recorded["template_digest"], template_digest(templates_now)),
            ("templates", recorded["templates"], templates_now),
        ) if then != now
    ]
    if _MISSING in templates_now.values():
        inconsistent.append("templates")
    if inconsistent:
        raise ReviewContractError(
            "review attempt refused: review_render_record_digest_mismatch: the prompt was rendered against different "
            f"{' and '.join(sorted(set(inconsistent)))} than this attempt would run; "
            "recorded digests do not match the render checkout; "
            f"differing server components: {_component_changes(recorded['server_components'], render_code.components())}; "
            f"{_RERENDER}"
        )
    contract = {
        "render_checkout": recorded["render_checkout"],
        "input_root": recorded["input_root"],
        "server_checkout": str(server),
        "server_interpreter": str(python),
        "render_server_digest": recorded["server_digest"],
        **_server_fields(code),
        "render_template_digest": recorded["template_digest"],
        "template_digest": template_digest(templates_now),
        "templates": sorted(recorded["templates"]),
        "prompt_sha256": prompt_sha256,
        "review_id": recorded.get("review_id"),
        "attempt_id": recorded.get("attempt_id"),
        "prompts_dir": recorded["prompts_dir"],
        "recorded_templates": recorded["templates"],
        "recorded_files_read": reads.get("files_read", []),
        "recorded_template_sha256": reads.get("template_sha256", {}),
    }
    differing = [
        what
        for what, then, now in (
            ("server code", contract["render_server_digest"], contract["server_digest"]),
            ("templates", contract["render_template_digest"], contract["template_digest"]),
        )
        if then != now
    ]
    if differing:
        raise ReviewContractError(
            "review attempt refused: review_contract_mismatch: the prompt was rendered against different "
            f"{' and '.join(differing)} than this attempt would run\n"
            f"  rendered in: {contract['render_checkout']} server digest {contract['render_server_digest']} "
            f"template digest {contract['render_template_digest']}\n"
            f"  sources server (primary checkout): {contract['server_checkout']} server digest {contract['server_digest']}\n"
            f"  differing server components: {_component_changes(recorded['server_components'], contract['server_components'])}\n"
            f"  templates now (render checkout): {recorded['prompts_dir']} template digest {contract['template_digest']}\n"
            f"  fix: {_FIX} (#9163)"
        )
    return contract


def check_launch_contract(contract: Mapping[str, Any], server_checkout: Path, interpreter: Path) -> None:
    """Refuse to launch a sources server other than the one this attempt's admission checked (#9163).

    ``contract`` is what ``check_render_contract`` returned at admission; ``server_checkout`` and ``interpreter``
    are exactly what the seat's MCP configuration launches. The server code is digested again from them now, so an
    update of the primary checkout (its code or its lock) after admission refuses here, before launch.
    """
    server = Path(server_checkout).resolve()
    code = server_code(server)
    admitted = (contract.get("server_checkout"), contract.get("server_interpreter"), contract.get("server_digest"))
    if admitted == (str(server), str(interpreter), code.digest):
        return
    raise ReviewContractError(
        "review attempt refused: review_server_changed: the sources server this attempt would launch differs from "
        "the one its admission checked\n"
        f"  admitted: {admitted[0]} with {admitted[1]} server digest {admitted[2]}\n"
        f"  launching: {server} with {interpreter} server digest {code.digest}\n"
        f"  differing server components: {_component_changes(contract.get('server_components') or {}, code.components())}\n"
        f"  fix: {_FIX} (#9163)"
    )
