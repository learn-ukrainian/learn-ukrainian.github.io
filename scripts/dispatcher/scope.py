"""The files a dispatch owns because a commit gate regenerates them from what it owns (#12169).

A gate that rewrites a generated file whenever its input changes blocks a worker that owns the
input but not the file. The dispatcher adds the file to the owned paths once, before anything reads
them, and the task record carries the result, so hooks and settlement need no rule of their own.
"""

from pathlib import PurePosixPath

# One entry per gate, matching its hook in .pre-commit-config.yaml: the input tree it watches and the
# file it regenerates. Add an entry only once that producer, input and output are established.
GENERATED_OUTPUTS = {
    "scripts/lexicon": "site/src/data/lexicon-manifest.fingerprint.json",  # atlas-lexicon-fingerprint-drift
}


def _literal_root(raw: str) -> str | None:
    """The owned path's literal part before any glob, or None when it has none."""
    path = PurePosixPath(raw.strip().replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        return None
    literal = []
    for part in path.parts:
        if any(char in part for char in "*?["):
            break
        literal.append(part)
    return "/".join(literal) or None


def with_generated_outputs(owned_paths) -> tuple[list[str], list[str]]:
    """The owned paths with every generated file a gate needs from them, and the files added.

    An owned path needs a file when its literal part is the gate's input tree, inside it or above it.
    A file the owned paths already cover is not added again.
    """
    from scripts.guardrails.delegate_ownership import path_is_owned

    owned = list(owned_paths)
    roots = [root for root in map(_literal_root, owned) if root]
    added = [output for prefix, output in GENERATED_OUTPUTS.items()
             if not path_is_owned(output, owned)
             and any(root == prefix or root.startswith(prefix + "/") or prefix.startswith(root + "/") for root in roots)]
    return owned + added, added
