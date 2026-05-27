from pathlib import Path

from scripts.generate_mdx.utils import STARLIGHT_DOCS_DIR
from scripts.manifest_utils import get_modules_for_level


def get_prev_next_links(level: str, module_num: int) -> tuple[str | bool, str | bool]:
    """Returns (prev, next) link logic.
    Returns the slug if it exists on disk, else False.
    """
    modules = get_modules_for_level(level)
    current_idx = None
    for i, m in enumerate(modules):
        if m.local_num == module_num:
            current_idx = i
            break

    if current_idx is None:
        raise ValueError(f"Module {module_num} not found in {level}")

    prev_val = False
    if current_idx > 0:
        prev_mod = modules[current_idx - 1]
        prev_mdx = STARLIGHT_DOCS_DIR / level / f"{prev_mod.slug}.mdx"
        if prev_mdx.exists():
            prev_val = prev_mod.slug

    next_val = False
    if current_idx < len(modules) - 1:
        next_mod = modules[current_idx + 1]
        next_mdx = STARLIGHT_DOCS_DIR / level / f"{next_mod.slug}.mdx"
        if next_mdx.exists():
            next_val = next_mod.slug

    return prev_val, next_val
