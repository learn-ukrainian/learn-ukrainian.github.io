"""What a rendered review prompt was rendered against, and whether a review attempt still matches it (#9163).

A review seat's sources MCP server launches from the primary checkout, while its prompt may be rendered in any
checkout. The prompt tells the seat what the server prints, so the prompt's templates and the server code that
answers the seat must come from the same code. At render time ``render_record`` records, beside the prompt, the
checkout that rendered it, the templates that render actually loaded and that checkout's server-code digest. At
dispatch ``check_render_contract`` compares that record with the server code the attempt would run and with the
render checkout's templates as they are now, and refuses on any difference.

The server-code digest covers the code the server runs, not a directory listing: the server entry plus every
repository module it imports, found by a static walk of its ``import`` statements resolved the way the server's
own ``sys.path`` resolves them (``scripts/``, then the repository root, then the server's directory, then the
import path of the interpreter the server launches with). Files are read from disk whatever git thinks of them
(ignored, untracked or dirty), and a symlink contributes its target's bytes. Imports made dynamically
(``importlib``) are not seen; the server makes none.

A top-level import the walk finds in a site directory of that interpreter is an installed distribution: its
owner is found through the ``RECORD`` files of the ``*.dist-info`` directories there, and every Python source and
extension module that ``RECORD`` lists is hashed, under the distribution's name and version. An import found
nowhere refuses as ``review_server_import_unresolved``, and so does one in a site directory that no ``RECORD``
installs, unless the import is optional (inside a ``try`` catching ``ImportError``, or a branch of an ``if``):
then its absence is itself recorded, so installing it later changes the digest. Only code outside distributions
is walked; a distribution's own imports are not.

The digest is taken three times per attempt: at render, at admission (``check_render_contract``) and at launch
(``check_launch_contract``, called by ``review_mcp.prepare_review_attempt`` on the exact checkout and interpreter
it writes into the seat's MCP configuration), so an update of the primary checkout between admission and launch
refuses too.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.common.repo_root import project_interpreter

#: The sources server a review seat calls, relative to a checkout.
SERVER_ENTRY = ".mcp/servers/sources/server.py"
#: Key of the render record inside the prompt's ``<prompt>.files_read.json`` sidecar.
RENDER_RECORD_KEY = "render_contract"
RENDER_RECORD_VERSION = 2
_SERVER_DIGEST_VERSION = b"lu-review-server-code-digest-v2"
_REPOSITORY_DIGEST_VERSION = b"lu-review-server-repository-digest-v1"
_DISTRIBUTION_DIGEST_VERSION = b"lu-review-server-distribution-digest-v1"
_TEMPLATE_DIGEST_VERSION = b"lu-review-template-digest-v1"
_MISSING = "missing"
_FIX = "pull the primary checkout to origin/main, then re-render and retry"
_INTERPRETER_TIMEOUT_S = 60
#: What the server's interpreter imports from: its ``sys.path`` after the script directory, the standard library.
_INTERPRETER_QUERY = """\
import importlib.machinery, json, site, sys, sysconfig
print(json.dumps({
    "path": sys.path[1:],
    "site_dirs": site.getsitepackages() + ([site.getusersitepackages()] if site.ENABLE_USER_SITE else []),
    "stdlib": sorted(set(sys.stdlib_module_names) | set(sys.builtin_module_names)),
    "stdlib_dirs": sorted({sysconfig.get_path("stdlib"), sysconfig.get_path("platstdlib")}),
    "extension_suffixes": importlib.machinery.EXTENSION_SUFFIXES,
}))
"""
#: Exceptions whose handler makes the imports of a ``try`` optional.
_IMPORT_ERROR_CATCHERS = frozenset({"ImportError", "ModuleNotFoundError", "Exception", "BaseException"})
#: A file changed this recently is hashed again rather than cached: its stat may not yet show a later write.
_RACY_WINDOW_NS = 2_000_000_000
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

    def __init__(self, roots: Iterable[Path], extension_suffixes: Iterable[str] = ()):
        self.roots = tuple(roots)
        self.extension_suffixes = tuple(extension_suffixes)
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

    def _scan(self, directories: Iterable[Path], leaf: str) -> _Module | None:
        portions: list[Path] = []
        for directory in directories:
            package = directory / leaf
            if (package / "__init__.py").is_file():
                return _Module((package / "__init__.py",), (package,))
            for suffix in (".py", *self.extension_suffixes):
                if (directory / f"{leaf}{suffix}").is_file():
                    return _Module((directory / f"{leaf}{suffix}",), ())
            if package.is_dir():
                portions.append(package)
        return _Module((), tuple(portions)) if portions else None


def _catches_import_error(handler: ast.ExceptHandler) -> bool:
    caught = handler.type
    if caught is None:
        return True
    names = caught.elts if isinstance(caught, ast.Tuple) else [caught]
    return any(isinstance(name, ast.Name) and name.id in _IMPORT_ERROR_CATCHERS for name in names)


def _imported_names(tree: ast.AST, package: str) -> list[tuple[str, bool]]:
    """Every module name an ``import``/``from … import`` in ``tree`` may load, with its parent packages.

    Each name comes with whether it is optional: its import sits in a ``try`` that catches ``ImportError`` (an
    optional import in the body, the fallback of one in a handler) or in a branch of an ``if`` (an import made
    only under a condition, such as the script-mode fallback ``if __package__: … else: …``).
    """
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try | ast.TryStar) and any(_catches_import_error(h) for h in node.handlers):
            parts: list[ast.AST] = [*node.body, *node.handlers]
        elif isinstance(node, ast.If):
            parts = [*node.body, *node.orelse]
        else:
            continue
        for part in parts:
            guarded.update(id(inner) for inner in ast.walk(part) if isinstance(inner, ast.Import | ast.ImportFrom))
    names: list[tuple[str, bool]] = []
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
            names.extend((".".join(parts[: index + 1]), id(node) in guarded) for index in range(len(parts)))
    return names


#: Import names by (content sha256, package): content-addressed, so a changed file can never hit a stale entry.
_IMPORTS_CACHE: dict[tuple[str, str], tuple[tuple[str, bool], ...]] = {}


def _imports_of(sha256: str, package: str, data: bytes) -> tuple[tuple[str, bool], ...]:
    """``(name, optional)`` per imported name; a name imported both ways is required."""
    key = (sha256, package)
    if key not in _IMPORTS_CACHE:
        try:
            tree = ast.parse(data)
        except (SyntaxError, ValueError):
            tree = None  # still hashed; a module that does not parse imports nothing
        optional: dict[str, bool] = {}
        for name, guarded in _imported_names(tree, package) if tree else ():
            optional[name] = optional.get(name, True) and guarded
        _IMPORTS_CACHE[key] = tuple(optional.items())
    return _IMPORTS_CACHE[key]


def _logical(path: Path, checkout: Path) -> str:
    return path.relative_to(checkout).as_posix() if path.is_relative_to(checkout) else path.as_posix()


@dataclass(frozen=True)
class _Interpreter:
    """Where an interpreter imports from, as the sources server launched with it would."""

    executable: str
    path: tuple[Path, ...]  # its ``sys.path`` after the script directory
    site_dirs: tuple[Path, ...]  # where installed distributions live
    stdlib: frozenset[str]  # standard-library and built-in top-level module names
    stdlib_dirs: tuple[Path, ...]
    extension_suffixes: tuple[str, ...]


#: By interpreter path, per process: what an interpreter's import path is does not change under a running dispatch.
_INTERPRETERS: dict[str, _Interpreter] = {}


def _interpreter(executable: Path) -> _Interpreter:
    key = str(executable)
    if key not in _INTERPRETERS:
        try:
            done = subprocess.run(
                [key, "-c", _INTERPRETER_QUERY],
                capture_output=True,
                text=True,
                timeout=_INTERPRETER_TIMEOUT_S,
                check=True,
            )
            data = json.loads(done.stdout)
            _INTERPRETERS[key] = _Interpreter(
                executable=key,
                path=tuple(Path(entry) for entry in data["path"] if entry),
                site_dirs=tuple(Path(entry) for entry in data["site_dirs"]),
                stdlib=frozenset(data["stdlib"]),
                stdlib_dirs=tuple(Path(entry) for entry in data["stdlib_dirs"]),
                extension_suffixes=tuple(data["extension_suffixes"]),
            )
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
            raise ReviewContractError(
                "review attempt refused: review_server_interpreter_unreadable: cannot read the import path of "
                f"{key}, the interpreter the sources server launches with: {exc} (#9163)"
            ) from exc
    return _INTERPRETERS[key]


def _record_paths(record: str) -> Iterable[str]:
    for line in record.splitlines():
        if line.startswith('"'):
            yield from (row[0] for row in csv.reader([line]) if row)
        elif line:
            yield line.split(",", 1)[0]


def _distribution_owners(site_dir: Path) -> dict[str, list[Path]]:
    """The ``*.dist-info`` directories in ``site_dir`` whose ``RECORD`` installs each top-level module name."""
    owners: dict[str, list[Path]] = {}
    for info in sorted(site_dir.glob("*.dist-info")):
        try:
            record = (info / "RECORD").read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        tops: set[str] = set()
        for entry in _record_paths(record):
            first, slash, _rest = entry.partition("/")
            if first in {"", "..", "__pycache__"} or first.endswith((".dist-info", ".data")):
                continue
            tops.add(first if slash else first.split(".", 1)[0])
        for top in tops:
            owners.setdefault(top, []).append(info)
    return owners


#: sha256 by (path, stat), per process: a stat change (a write, a replaced inode) is a miss.
_FILE_HASHES: dict[tuple[str, int, int, int, int, int], str] = {}


def _file_sha256(path: Path) -> str:
    """sha256 of an installed file's bytes; ``missing`` when its ``RECORD`` lists a file that is gone."""
    try:
        stat = path.stat()
        key = (str(path), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        if key in _FILE_HASHES:
            return _FILE_HASHES[key]
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return _MISSING
    if time.time_ns() - max(stat.st_mtime_ns, stat.st_ctime_ns) > _RACY_WINDOW_NS:
        _FILE_HASHES[key] = sha
    return sha


@dataclass(frozen=True)
class _Distribution:
    name: str
    version: str
    files: dict[str, str]  # each Python source or extension module its RECORD lists: sha256 by RECORD path


def _distribution(info: Path, extension_suffixes: tuple[str, ...]) -> _Distribution:
    dist = importlib.metadata.Distribution.at(info)
    files: dict[str, str] = {}
    for file in dist.files or ():
        name = str(file)
        if "__pycache__" not in file.parts and name.endswith((".py", *extension_suffixes)):
            files[name] = _file_sha256(Path(dist.locate_file(file)))
    return _Distribution(dist.metadata["Name"] or info.name, dist.version or "unknown", dict(sorted(files.items())))


def _mapping_digest(version: bytes, entries: Mapping[str, str]) -> str:
    hasher = hashlib.sha256(version + b"\0")
    for name, value in entries.items():
        hasher.update(name.encode("utf-8", errors="surrogateescape") + b"\0" + value.encode("utf-8") + b"\n")
    return f"sha256:{hasher.hexdigest()}"


@dataclass(frozen=True)
class ServerCode:
    """What the sources server of a checkout executes, as launched with one interpreter."""

    files: dict[str, str]  # executed files outside any distribution: sha256 by path, relative inside the checkout
    distributions: dict[str, _Distribution]  # installed distributions it imports, by name
    absent: tuple[str, ...]  # optional top-level imports found nowhere

    def components(self) -> dict[str, str]:
        """One digest per part, so a refusal can name the part that changed: the repository, each distribution."""
        parts = {"repository": _mapping_digest(_REPOSITORY_DIGEST_VERSION, self.files)}
        for name, dist in self.distributions.items():
            parts[f"distribution {name}"] = (
                f"{dist.version} {_mapping_digest(_DISTRIBUTION_DIGEST_VERSION, dist.files)}"
            )
        parts["absent optional imports"] = ", ".join(self.absent) or "none"
        return parts

    @property
    def digest(self) -> str:
        return _mapping_digest(_SERVER_DIGEST_VERSION, self.components())


def _placement(
    top: str, finder: _ModuleFinder, python: _Interpreter, site_owners: dict[Path, dict[str, list[Path]]]
) -> tuple[str, tuple[Path, ...]]:
    """Where the top-level module ``top`` comes from: ``code`` (the repository, or a plain import-path directory
    such as a ``PYTHONPATH`` entry: walked and hashed), ``stdlib``, ``distribution`` (with its ``dist-info``
    directories), ``absent``, or ``unowned`` (in a site directory, at those paths, but installed by no RECORD)."""
    module = finder.find(top)
    if module is None:
        return "absent", ()
    repository_roots = finder.roots[: len(finder.roots) - len(python.path)]
    infos: list[Path] = []
    for location in module.files or module.search:
        # The import-path entry it was found in: a package's ``__init__.py`` sits one level deeper.
        entry = location.parent.parent if location.name == "__init__.py" else location.parent
        if entry in repository_roots:
            continue
        if entry in python.site_dirs:
            if entry not in site_owners:
                site_owners[entry] = _distribution_owners(entry)
            owned = site_owners[entry].get(top)
            if not owned:
                return "unowned", tuple(module.files or module.search)
            infos.extend(owned)
        elif any(entry.is_relative_to(stdlib) for stdlib in python.stdlib_dirs):
            return "stdlib", ()
    return ("distribution", tuple(dict.fromkeys(infos))) if infos else ("code", ())


def server_code(checkout: Path, interpreter: Path | None = None) -> ServerCode:
    """What the sources server of ``checkout`` executes when ``interpreter`` (the project interpreter) launches it.

    The entry and each repository module it imports, recursively (a symlink is followed and its target's bytes
    hashed), and each installed distribution a top-level import resolves to. The standard library is not the
    checkout's. An import found nowhere refuses unless it is optional (see ``_imported_names``).
    """
    root = Path(checkout).resolve()
    entry = root / SERVER_ENTRY
    if not entry.is_file():
        raise ReviewContractError(f"review attempt refused: no sources server at {entry} (#9163)")
    python = _interpreter(Path(interpreter) if interpreter is not None else project_interpreter())
    finder = _ModuleFinder((root / "scripts", root, entry.resolve().parent, *python.path), python.extension_suffixes)
    site_owners: dict[Path, dict[str, list[Path]]] = {}
    placements: dict[str, tuple[str, tuple[Path, ...]]] = {}
    hashes: dict[str, str] = {}
    infos: dict[Path, None] = {}
    absent: dict[str, bool] = {}  # top-level name: whether every import of it is optional
    unowned: dict[str, tuple[Path, ...]] = {}
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
        for name, optional in _imports_of(hashes[key], package, data):
            top = name.partition(".")[0]
            if top in python.stdlib:
                continue
            if top not in placements:
                placements[top] = _placement(top, finder, python, site_owners)
            where, found = placements[top]
            if where == "distribution":
                infos.update(dict.fromkeys(found))
            elif where == "absent":
                absent[top] = absent.get(top, True) and optional
            elif where == "unowned":
                unowned[top] = found
            elif where == "code":
                module = finder.find(name)
                for file in module.files if module is not None else ():
                    pending.append((file, name if file.name == "__init__.py" else name.rpartition(".")[0]))
    unresolved = [f"{top} (found nowhere)" for top, optional in sorted(absent.items()) if not optional]
    unresolved += [
        f"{top} (at {', '.join(map(str, found))}, installed by no distribution RECORD)"
        for top, found in sorted(unowned.items())
    ]
    if unresolved:
        raise ReviewContractError(
            "review attempt refused: review_server_import_unresolved: the sources server at "
            f"{entry} imports {'; '.join(unresolved)}, which resolve to neither the repository, the standard "
            f"library nor a distribution installed for {python.executable}, so its code cannot be digested (#9163)"
        )
    distributions = [_distribution(info, python.extension_suffixes) for info in infos]
    return ServerCode(
        files=dict(sorted(hashes.items())),
        distributions={dist.name: dist for dist in sorted(distributions, key=lambda dist: dist.name)},
        absent=tuple(sorted(absent)),
    )


def server_code_files(checkout: Path, interpreter: Path | None = None) -> dict[str, str]:
    """sha256 of every repository file the sources server of ``checkout`` executes, by path (see ``server_code``)."""
    return server_code(checkout, interpreter).files


def server_code_digest(checkout: Path, interpreter: Path | None = None) -> str:
    """One deterministic digest of ``server_code``: what decides the sources server's behaviour."""
    return server_code(checkout, interpreter).digest


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
    render_checkout: Path, prompts_dir: Path, loaded_templates: Mapping[str, str], prompt_sha256: str
) -> dict[str, Any]:
    """The record a render writes beside its prompt: where it rendered, what it loaded, the server it matched."""
    checkout = Path(render_checkout).resolve()
    return {
        "version": RENDER_RECORD_VERSION,
        "render_checkout": str(checkout),
        "prompts_dir": str(Path(prompts_dir).resolve()),
        "templates": dict(sorted(loaded_templates.items())),
        "template_digest": template_digest(loaded_templates),
        **_server_fields(server_code(checkout)),
        "prompt_sha256": prompt_sha256,
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


def _read_render_record(prompt_file: Path | None) -> dict[str, Any]:
    if prompt_file is None:
        raise ReviewContractError(
            "review attempt refused: review_render_record_missing: a --review-attempt prompt must come from "
            f"--prompt-file, whose render record says what it was rendered against; {_RERENDER} (#9163)"
        )
    sidecar = render_record_path(Path(prompt_file))
    try:
        record = json.loads(sidecar.read_text(encoding="utf-8")).get(RENDER_RECORD_KEY)
    except (OSError, ValueError, AttributeError) as exc:
        raise ReviewContractError(
            f"review attempt refused: review_render_record_missing: cannot read {sidecar}: {exc}; {_RERENDER} (#9163)"
        ) from exc
    fields = ("render_checkout", "prompts_dir", "template_digest", "server_digest", "prompt_sha256")
    if (
        not isinstance(record, dict)
        or record.get("version") != RENDER_RECORD_VERSION
        or not all(isinstance(record.get(field), str) for field in fields)
        or not isinstance(record.get("templates"), dict)
        or not record["templates"]
        or not isinstance(record.get("server_components"), dict)
    ):
        raise ReviewContractError(
            f"review attempt refused: review_render_record_missing: {sidecar} holds no version "
            f"{RENDER_RECORD_VERSION} {RENDER_RECORD_KEY} record; {_RERENDER} (#9163)"
        )
    return record


def check_render_contract(
    prompt_file: Path | None, prompt_text: str, server_checkout: Path, interpreter: Path | None = None
) -> dict[str, Any]:
    """Refuse a review attempt whose prompt was rendered against other code than the attempt would run (#9163).

    ``server_checkout`` is where the attempt's sources server launches, with ``interpreter`` (the project
    interpreter by default). Compares the render record's server digest with that server's code now, and its
    template digest with the render checkout's loaded templates now. Returns the record the task stores: the
    digests compared, and the server components and interpreter ``check_launch_contract`` checks again at launch.
    """
    recorded = _read_render_record(prompt_file)
    prompt_sha256 = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
    if prompt_sha256 != recorded["prompt_sha256"]:
        raise ReviewContractError(
            "review attempt refused: review_render_record_stale: the prompt file hashes to "
            f"{prompt_sha256}, its render record names {recorded['prompt_sha256']}; {_RERENDER} (#9163)"
        )
    server = Path(server_checkout).resolve()
    python = Path(interpreter) if interpreter is not None else project_interpreter()
    code = server_code(server, python)
    templates_now = current_templates(Path(recorded["prompts_dir"]), recorded["templates"])
    contract = {
        "render_checkout": recorded["render_checkout"],
        "server_checkout": str(server),
        "server_interpreter": str(python),
        "render_server_digest": recorded["server_digest"],
        **_server_fields(code),
        "render_template_digest": recorded["template_digest"],
        "template_digest": template_digest(templates_now),
        "templates": sorted(recorded["templates"]),
        "prompt_sha256": prompt_sha256,
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
    update of the primary checkout (or its installed distributions) after admission refuses here, before launch.
    """
    server = Path(server_checkout).resolve()
    code = server_code(server, interpreter)
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
