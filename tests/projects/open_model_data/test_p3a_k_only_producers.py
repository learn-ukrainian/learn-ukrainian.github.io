"""Committed-K fixture proofs for P3a companion-only producer routes."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

import pytest

from scripts.projects.open_model_data import (
    phase3_historical_protection_channels as historical,
)
from scripts.projects.open_model_data import (
    v4_dataset_quality_evaluation as quality,
)
from scripts.projects.open_model_data import (
    v4_mine_gold_seeds as seeds,
)
from scripts.projects.open_model_data import (
    v4_reproduce_deliverables as delivery,
)
from scripts.storage import artifacts, paths

K_PATHS = (
    quality._ASSESSMENT,
    delivery._DELIVERY_RECEIPT,
    "registry/projects/open_model_data/admission/phase3_historical_protection_channels_v1.json",
    "registry/projects/open_model_data/decolonization/seeds/human_gold_seeds_150_trajectories.jsonl",
    "registry/projects/open_model_data/decolonization/seeds/human_gold_seeds_150_dpo.jsonl",
    "registry/projects/open_model_data/decolonization/seeds/human_gold_seeds_manifest.json",
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=30)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    artifact = root / "data/projects/open_model_data/a.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"A-old")
    (root / "registry/artifacts").mkdir(parents=True)
    with (root / "registry/artifacts/classification-v1.tsv").open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(("path", "mode", "blob", "size", "class", "group", "reason", "judgment"))
        writer.writerow(
            (
                "data/projects/open_model_data/a.json",
                "100644",
                "",
                5,
                "A",
                "open_model_other_indexes",
                "fixture",
                "test",
            )
        )
    for relative in K_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"old")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "committed K baseline")
    assert artifacts.manifest_build(root, "open_model_other_indexes", "HEAD") == 1
    staged_a = tmp_path / "bind-a"
    staged_a.write_bytes(b"A-bound")
    old_a = paths.hash_file(artifact)
    companions = []
    for index, relative in enumerate(K_PATHS):
        source = tmp_path / f"bind-k-{index}"
        source.write_bytes(b"old")
        companions.append(artifacts.CompanionChange(relative, source, hashlib.sha256(b"old").hexdigest()))
    artifacts.publish_set(
        root,
        "open_model_other_indexes",
        [artifacts.ArtifactChange("replace", "projects/open_model_data/a.json", staged_a, old_a)],
        "fixture",
        companions=companions,
        expected_members={"projects/open_model_data/a.json"},
    )
    return root


@pytest.mark.parametrize("route", ["quality", "delivery", "seeds", "historical"])
def test_k_only_changed_unchanged_and_refusal(repo: Path, monkeypatch: pytest.MonkeyPatch, route: str) -> None:
    monkeypatch.setattr(seeds, "REPO_ROOT", repo)
    monkeypatch.setattr(seeds, "DEFAULT_SEEDS_DIR", repo / "registry/projects/open_model_data/decolonization/seeds")
    monkeypatch.setattr(historical, "ROOT", repo)
    monkeypatch.setattr(historical, "OUTPUT", repo / K_PATHS[2])
    monkeypatch.setattr(historical, "build_contract", lambda: {"fixture": True})

    if route == "quality":
        outputs = {K_PATHS[0]: b"new"}

        def publish() -> None:
            quality._publish_assessment(repo, repo / K_PATHS[0], b"new")
    elif route == "delivery":
        outputs = {K_PATHS[1]: b"new"}

        def publish() -> None:
            delivery._publish_delivery_receipt(repo, repo / K_PATHS[1], b"new")
    elif route == "seeds":
        outputs = {relative: b"new" for relative in K_PATHS[3:]}

        def publish() -> None:
            seeds._publish_seed_files(
                repo / "registry/projects/open_model_data/decolonization/seeds",
                {Path(relative).name: b"new" for relative in K_PATHS[3:]},
            )
    else:
        outputs = {K_PATHS[2]: historical.canonical_json({"fixture": True})}

        def publish() -> None:
            historical.write_contract(repo / K_PATHS[2])

    before_a = (repo / "data/projects/open_model_data/a.json").read_bytes()
    publish()
    assert paths.artifact_set("open_model_other_indexes", repo=repo).companions.items() >= outputs.items()
    assert (repo / "data/projects/open_model_data/a.json").read_bytes() == before_a
    # Same bytes are checked under the lock and require no intervening commit.
    publish()
    assert (repo / "data/projects/open_model_data/a.json").read_bytes() == before_a
    # Changed bytes remain protected by the committed-HEAD requirement.
    if route != "historical":
        with pytest.raises(ValueError, match="dirty K companion"):
            if route == "quality":
                quality._publish_assessment(repo, repo / K_PATHS[0], b"newer")
            elif route == "delivery":
                delivery._publish_delivery_receipt(repo, repo / K_PATHS[1], b"newer")
            else:
                seeds._publish_seed_files(
                    repo / "registry/projects/open_model_data/decolonization/seeds",
                    {Path(relative).name: b"newer" for relative in K_PATHS[3:]},
                )
        for relative, content in outputs.items():
            assert (repo / relative).read_bytes() == content


@pytest.mark.parametrize("route", ["quality", "delivery", "seeds"])
def test_external_output_is_independent(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: str
) -> None:
    external = tmp_path / "external"
    external.mkdir()
    before = paths.artifact_set("open_model_other_indexes", repo=repo)
    if route == "quality":
        quality._publish_assessment(repo, external / "quality.json", b"external")
        assert (external / "quality.json").read_bytes() == b"external"
    elif route == "delivery":
        delivery._publish_delivery_receipt(repo, external / "receipt.json", b"external")
        assert (external / "receipt.json").read_bytes() == b"external"
    else:
        monkeypatch.setattr(seeds, "REPO_ROOT", repo)
        monkeypatch.setattr(seeds, "DEFAULT_SEEDS_DIR", repo / "registry/projects/open_model_data/decolonization/seeds")
        seeds._publish_seed_files(external, {"seeds.json": b"external"})
        assert (external / "seeds.json").read_bytes() == b"external"
    after = paths.artifact_set("open_model_other_indexes", repo=repo)
    assert before.manifest == after.manifest
    assert before.companions == after.companions
