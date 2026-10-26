"""The dispatcher's three input, independence and resource checks."""

import shutil
from pathlib import Path
from urllib.parse import unquote

import yaml

from scripts.dispatcher import git
from scripts.dispatcher.types import TaskSpec

CATALOG = Path(__file__).resolve().parents[1] / "config" / "model_catalog.yaml"


def _handle_private_input(spec: TaskSpec, message: str) -> None:
    if spec.agent == "muse":
        spec.options["contributor_mode"] = "off"
    else:
        raise ValueError(message)


def check_private_input(spec: TaskSpec, repo_key: str) -> None:
    if spec.agent not in {"muse", "opencode", "hermes"}:
        return
    repos = yaml.safe_load(git.CONFIG.read_text())["repos"]
    private = {
        key: item for key, item in repos.items() if item.get("private", False) or "private" in item.get("role", "")
    }
    roots = [git.resolve_repo(key)[0] for key in private]
    if git.resolve_repo(repo_key)[0] in roots:
        return _handle_private_input(spec, "private input is not permitted for this agent")
    origin = spec.options.get("prompt_file")
    if origin and origin != "-" and any(Path(origin).resolve().is_relative_to(root) for root in roots):
        return _handle_private_input(spec, "private prompt file is not permitted for this agent")
    # The content contract is lexical: decode once, then compare without changing provider input.
    text = unquote(spec.prompt_file.read_text()).casefold()
    identifiers = [str(root) for root in roots]
    identifiers.extend(item.get(field, "") for item in private.values() for field in ("local_name", "github"))
    if any(identifier.casefold() in text for identifier in identifiers if identifier):
        _handle_private_input(spec, "private path input is not permitted for this agent")


def check_review_family(author_model: str | None, reviewer_model: str) -> None:
    if author_model is None:
        return
    models = yaml.safe_load(CATALOG.read_text())["models"]
    families = {}
    for name, item in models.items():
        for identifier in [
            name,
            *item.get("aliases", []),
            *item.get("routing_wire_ids", {}).values(),
            *item.get("runtime_model_ids", []),
        ]:
            families[identifier] = item.get("family")
    author, reviewer = families.get(author_model), families.get(reviewer_model)
    if not author or not reviewer or author == reviewer:
        raise ValueError("review independence requires two known, different model families")


def check_resources(paths) -> None:
    available = next(
        int(line.split()[1]) * 1024
        for line in Path("/proc/meminfo").read_text().splitlines()
        if line.startswith("MemAvailable:")
    )
    if available < 8.5 * 1024**3:
        raise ValueError("insufficient memory: MemAvailable must be at least 8.5 GiB")
    for path in paths:
        path = Path(path)
        while not path.exists():
            path = path.parent
        usage = shutil.disk_usage(path)
        if usage.used / usage.total >= 0.9:
            raise ValueError("insufficient disk: usage must be below 90%")
