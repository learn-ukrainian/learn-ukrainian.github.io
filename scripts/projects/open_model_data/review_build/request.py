"""Location-only host requests; admission policy belongs to component code."""

import json
import os
import stat
from pathlib import Path

from .contract import canonical
from .errors import BuildError, require
from .output import private_umask

KEYS = frozenset({"schema", "databases", "ua_gec", "catalog", "register", "synthetic_sources", "antonenko_receipts"})


def read_request(path: Path) -> tuple[bytes, dict]:
    try:
        content = path.read_bytes()
    except FileNotFoundError:
        raise BuildError("request_missing") from None
    request = json.loads(content)
    require(isinstance(request, dict), "request_schema")
    require(request.get("schema") == "omd-review-request.v2", "request_schema")
    require(request.keys() <= KEYS, "request_policy_key")
    require({"databases", "ua_gec", "catalog", "register"} <= request.keys(), "request_locations")
    require(isinstance(request["databases"], dict), "request_locations")
    require(
        all(
            isinstance(store, str) and store and isinstance(path, str) and path
            for store, path in request["databases"].items()
        )
        and all(isinstance(request[key], str) and request[key] for key in ("catalog", "register")),
        "request_locations",
    )
    require(isinstance(request["ua_gec"], dict), "request_locations")
    require(request["ua_gec"].keys() <= {"root"}, "request_policy_key")
    require(
        "antonenko_receipts" not in request
        or (isinstance(request["antonenko_receipts"], str) and bool(request["antonenko_receipts"].strip())),
        "request_locations",
    )
    require(isinstance(request["ua_gec"].get("root"), str) and bool(request["ua_gec"]["root"]), "request_locations")
    require(
        isinstance(request.get("synthetic_sources", []), list)
        and all(
            isinstance(source, str) and source.startswith("synthetic")
            for source in request.get("synthetic_sources", [])
        ),
        "synthetic_adapter_source",
    )
    return content, request


def repository_root() -> Path:
    """Resolve the shared repository through linked-worktree Git metadata."""
    root = Path(__file__).resolve().parents[4]
    git = root / ".git"
    if git.is_file():
        text = git.read_text().strip()
        require(text.startswith("gitdir: "), "code_identity")
        git = (root / text[8:]).resolve()
        common = git / "commondir"
        if common.exists():
            git = (git / common.read_text().strip()).resolve()
        root = git.parent
    return root


def init_request(path: Path) -> None:
    """Create a private descriptor without replacing an existing request or following links."""
    root = repository_root()
    request = {
        "schema": "omd-review-request.v2",
        "databases": {store: str(root / "data" / store) for store in ("sources.db", "vesum.db")},
        "ua_gec": {"root": str(root / "data/ua-gec")},
        "catalog": str(root / "registry/projects/open_model_data/instruction_catalog.yaml"),
        "register": str(root / "docs/sources/permissions-register.yaml"),
    }
    supplied = path.absolute()
    require(".." not in supplied.parts, "request_path")
    directory = os.open(supplied.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in supplied.parts[1:-1]:
            try:
                with private_umask():
                    os.mkdir(part, 0o700, dir_fd=directory)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        info = os.fstat(directory)
        require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700, "request_parent_mode")
        try:
            with private_umask():
                fd = os.open(
                    supplied.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory
                )
        except FileExistsError:
            raise BuildError("request_exists") from None
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(request) + b"\n")
    finally:
        os.close(directory)
