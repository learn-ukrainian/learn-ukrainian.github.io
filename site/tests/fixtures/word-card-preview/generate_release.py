"""Synthetic projection inputs, run only under tests' temporary certification authority.

Reproduce with tests/test_atlas_preview_release_fixture.py. It generates outside
the checkout and checks exact bytes against the approved committed fixtures.
No Ukrainian claims, real source stores, or real review evidence are used.
"""

import copy
import hashlib
import importlib.util
import sys
from pathlib import Path

PRODUCER_COMMIT = "7d4680686862d4ef2a66870a883aed6583bd64f7"
PRODUCER_SHA256 = "6fe2cbbb791acabe05c54a3e1df61d0110b73e43356ae838c3bee3526b933da5"
FROZEN_SOURCE = Path(__file__).with_name("producer_dataset_projection.py")


def load_frozen_projection():
    """Execute the byte-pinned producer copy, never today's live module."""
    if hashlib.sha256(FROZEN_SOURCE.read_bytes()).hexdigest() != PRODUCER_SHA256:
        raise ValueError("Pinned projection implementation changed")
    spec = importlib.util.spec_from_file_location("_atlas_frozen_projection", FROZEN_SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolves its defining module here
    spec.loader.exec_module(module)
    return module


projection = load_frozen_projection()


def generate(authority, output: Path, format: str):
    """Project two same-spelling identities using the existing synthetic authority."""
    certified = copy.deepcopy(authority.card)
    certified["assertions"] = certified["assertions"][:2]
    parallel = copy.deepcopy(certified["assertions"][1])
    parallel.update(assertion_id="wa_00000000000000000000000a", value="parallel-definition",
                    value_norm="parallel-definition", locator="ulif:row:parallel",
                    source_record_key="ulif:record:parallel")
    certified["assertions"].append(parallel)
    authority.approve(certified)
    candidate = copy.deepcopy(certified)
    candidate.update(card_id="wc_0123456789ac", card_version="synthetic-candidate-1",
                     known_gaps=["Independent linguistic review pending",
                                 "<script>globalThis.releaseInjected=1</script>"])
    for index, assertion in enumerate(candidate["assertions"]):
        assertion["assertion_id"] = "wa_" + f"{100 + index:024x}"
        assertion["subject"]["id"] = candidate["card_id"]
    candidate["assertions"][1]["value"] = "<img src=x onerror=globalThis.releaseInjected=1> RAW  A"
    candidate["assertions"][1]["value_norm"] = candidate["assertions"][1]["value"]
    cards = [certified, candidate]
    release = projection.create_release(
        cards, release_version="v0.1.0-synthetic" if format == "jsonl" else "v0.1.1-synthetic",
        format=format, allow_candidates=True,
    )
    release.write(output)
    return cards, release
