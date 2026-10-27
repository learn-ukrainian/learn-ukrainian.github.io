"""Dispatch input, review independence and resource admission checks."""

import shutil
from pathlib import Path
from urllib.parse import unquote

import yaml

from scripts.dispatcher import git
from scripts.dispatcher.advisory import admit as check_bounded_advisory  # noqa: F401
from scripts.dispatcher.advisory import binding as advisory_binding  # noqa: F401
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


def _model_families() -> dict[str, str | None]:
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
    return families


def check_review_family(author_model: str | None, reviewer_model: str) -> None:
    if author_model is None:
        return
    families = _model_families()
    author, reviewer = families.get(author_model), families.get(reviewer_model)
    if not author or not reviewer or author == reviewer:
        raise ValueError("review independence requires two known, different model families")


def check_review_subjects(agent, model, seats, families, owned_paths, *, review=False):
    from types import SimpleNamespace

    from scripts.review.subject_seat import classify_owned_path, prepare_subject_exclusion, subject_exclusion_reason

    if review:
        for path in owned_paths:
            if classify_owned_path(path).kind == "ambiguous":
                raise ValueError(f"ambiguous review subject path: {path}")
    exclusion = prepare_subject_exclusion(subject_seats=frozenset(seats), subject_families=frozenset(families),
                                          owned_paths=tuple(owned_paths))
    if exclusion.fail_closed_reason:
        raise ValueError(exclusion.fail_closed_reason)
    if not exclusion.seats and not exclusion.families:
        return exclusion
    models = {model}
    if agent == "cursor":
        from scripts.review.model_catalog import (
            CURSOR_APPROVED_WIRE_PINS,
            cursor_pinned_models,
            substitution_default_model,
        )

        if model not in {*cursor_pinned_models(), *CURSOR_APPROVED_WIRE_PINS}:
            models.add(substitution_default_model("cursor"))
    model_families = _model_families()
    for effective_model in models:
        family = model_families.get(effective_model)
        if not family:
            raise ValueError("subject exclusion requires a known effective reviewer model family")
        candidate = SimpleNamespace(name=agent, family=family, concrete_model=effective_model,
                                    route=agent, transport=agent)
        reason = subject_exclusion_reason(candidate, seats=exclusion.seats, families=exclusion.families,
                                          evidence=exclusion.evidence)
        if reason:
            raise ValueError(reason)
    return exclusion


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
