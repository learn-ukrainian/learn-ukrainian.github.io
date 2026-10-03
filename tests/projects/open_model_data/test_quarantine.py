"""Quarantine of old-plan trainable artifacts: inventory, loader refusal, notebooks, archive (#9607)."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

import scripts.projects.open_model_data.paths as paths_mod
from scripts.projects.open_model_data import quarantine
from scripts.projects.open_model_data.paths import (
    LOGICAL_OPEN_MODEL_PREFIX,
    QUARANTINE_INVENTORY_PATH,
    REGISTRY_OPEN_MODEL_DATA_DIR,
    QuarantinedArtifactError,
    is_archived_or_quarantined_path,
    quarantine_reason,
    refuse_quarantined,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
OPEN_MODEL_SCRIPTS = REPO_ROOT / "scripts/projects/open_model_data"
GOLD_SEEDS = REGISTRY_OPEN_MODEL_DATA_DIR / "decolonization/seeds/human_gold_seeds_150_dpo.jsonl"
SEALED_CANARY = f"{LOGICAL_OPEN_MODEL_PREFIX}/canary/pilot_canary_train_200.jsonl"
# A path that is not an inventoried file, under a release set sealed only by its TOMBSTONE.md.
RELEASE_TOMBSTONE_PATH = f"{LOGICAL_OPEN_MODEL_PREFIX}/release/uldr_v05_grammar_valency/sft/unlisted_shard.jsonl"
NOTEBOOKS = (
    OPEN_MODEL_SCRIPTS / "pilot_canary_gemma3_4b_colab.ipynb",
    OPEN_MODEL_SCRIPTS / "production_train_gemma3_4b_colab.ipynb",
)
HUB_WRITE_CALLS = frozenset(
    {
        "create_branch",
        "create_commit",
        "create_repo",
        "push_to_hub",
        "upload_file",
        "upload_folder",
        "upload_large_folder",
    }
)
ARCHIVE_DIR = REPO_ROOT / "archive/code/open_model_data"
ARCHIVED_MODULES = ("v6_mine_ulif_phraseology", "v6_mine_general_assistant_textbooks", "judge_eval_seat")


@pytest.fixture
def inventory() -> dict[str, Any]:
    return json.loads(QUARANTINE_INVENTORY_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def sealed_copy(tmp_path: Path) -> Path:
    """A byte copy of a sealed artifact outside the open-model tree."""
    copy = tmp_path / "elsewhere" / "seeds.jsonl"
    copy.parent.mkdir()
    shutil.copyfile(GOLD_SEEDS, copy)
    return copy


@pytest.fixture
def fresh_guard_caches() -> Iterator[None]:
    for cached in (paths_mod.quarantine_inventory, paths_mod._quarantined_tails, paths_mod._quarantined_hashes):
        cached.cache_clear()
    yield
    for cached in (paths_mod.quarantine_inventory, paths_mod._quarantined_tails, paths_mod._quarantined_hashes):
        cached.cache_clear()


# AC1 — inventory lists every quarantined artifact with its hash and reason.


def test_inventory_quarantine_covers_denominator(inventory: dict[str, Any]) -> None:
    assert inventory["schema"] == "open_model_quarantine_inventory_v1"
    assert inventory["totals"]["ignored_files"] == 412
    assert inventory["totals"]["ignored_bytes"] == 637_987_720
    artifacts = inventory["artifacts"]
    assert len({item["path"] for item in artifacts}) == len(artifacts)
    reasons = {item["id"]: item["reason"] for item in inventory["sets"]}
    for item in artifacts:
        assert len(item["sha256"]) == 64 and int(item["sha256"], 16) >= 0, item["path"]
        assert item["reason"] and item["reason"] == reasons[item["set"]], item["path"]
    tracked = {item["path"] for item in artifacts if item["storage"] == "tracked"}
    registry = "registry/projects/open_model_data"
    for required in (
        f"{registry}/decolonization/seeds/human_gold_seeds_150_dpo.jsonl",
        f"{registry}/decolonization/seeds/human_gold_seeds_150_trajectories.jsonl",
        f"{registry}/components/decolonization/cases.json",
        f"{registry}/components/grammar/cases.json",
        f"{registry}/components/decolonization/acceptance_review_sample.signoff.json",
        f"{registry}/components/grammar/acceptance_review_sample.signoff.json",
        f"{registry}/release/uldr_v06_general_assistant/SAMPLE_INSPECTION_150.md",
        f"{registry}/study/uldr_v1_acceptance_sample.signoff_template.json",
    ):
        assert required in tracked, required
    assert len(json.loads((REPO_ROOT / registry / "components/decolonization/cases.json").read_text())) == 250
    assert len(json.loads((REPO_ROOT / registry / "components/grammar/cases.json").read_text())) == 17


def test_inventory_quarantine_hashes_match_tracked_files_and_manifests(inventory: dict[str, Any]) -> None:
    checked = quarantine.verify_inventory(inventory)
    assert checked["tracked"] == inventory["totals"]["tracked_files"]
    manifest = {entry["path"]: entry for entry in quarantine.ignored_manifest_entries()}
    for item in inventory["artifacts"]:
        if item["storage"] == "ignored":
            assert manifest[item["path"]]["sha256"] == item["sha256"]
            assert manifest[item["path"]]["size"] == item["bytes"]


def test_inventory_quarantine_verify_detects_drift(inventory: dict[str, Any]) -> None:
    drifted = json.loads(json.dumps(inventory))
    first_tracked = next(item for item in drifted["artifacts"] if item["storage"] == "tracked")
    first_tracked["sha256"] = "0" * 64
    with pytest.raises(quarantine.InventoryError, match="hash drift"):
        quarantine.verify_inventory(drifted)


def test_inventory_quarantine_cli_verify_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(OPEN_MODEL_SCRIPTS / "quarantine.py"), "verify"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["totals"]["ignored_files"] == 412


def test_every_tombstoned_set_has_a_seal() -> None:
    for directory in quarantine.TOMBSTONED_DIRECTORIES:
        assert (REGISTRY_OPEN_MODEL_DATA_DIR / directory / "TOMBSTONE.md").is_file(), directory


# Guard rules (paths.py).


def test_quarantine_guard_rules() -> None:
    assert quarantine_reason(SEALED_CANARY) is not None
    assert quarantine_reason(RELEASE_TOMBSTONE_PATH).startswith("sealed by")
    assert quarantine_reason(f"/elsewhere/checkout/{SEALED_CANARY}") is not None
    assert quarantine_reason(f"{LOGICAL_OPEN_MODEL_PREFIX}/release") is not None
    assert quarantine_reason(f"{LOGICAL_OPEN_MODEL_PREFIX}/archive/uldr_v1_production/sft") is not None
    assert quarantine_reason(REGISTRY_OPEN_MODEL_DATA_DIR / "contracts") is None
    assert quarantine_reason(f"{LOGICAL_OPEN_MODEL_PREFIX}/components/c1_new/train.jsonl") is None
    assert quarantine_reason(None) is None
    assert is_archived_or_quarantined_path(RELEASE_TOMBSTONE_PATH) is True
    assert is_archived_or_quarantined_path(REGISTRY_OPEN_MODEL_DATA_DIR / "treatments") is False


def test_quarantine_guard_refuses_byte_copy_but_not_new_or_empty_files(sealed_copy: Path, tmp_path: Path) -> None:
    assert quarantine_reason(sealed_copy).startswith("bytes match quarantined")
    assert is_archived_or_quarantined_path(sealed_copy) is False  # path rules alone do not hash
    fresh = tmp_path / "fresh.jsonl"
    fresh.write_text('{"text": "new"}\n', encoding="utf-8")
    empty = tmp_path / "empty.jsonl"
    empty.touch()
    assert quarantine_reason(fresh) is None
    assert quarantine_reason(empty) is None


def test_quarantine_guard_honours_new_release_tombstone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fresh_guard_caches: None
) -> None:
    registry = tmp_path / "registry/projects/open_model_data"
    artifacts = tmp_path / "data/projects/open_model_data"
    (registry / "release/new_set").mkdir(parents=True)
    monkeypatch.setattr(paths_mod, "REGISTRY_OPEN_MODEL_DATA_DIR", registry)
    monkeypatch.setattr(paths_mod, "ARTIFACT_OPEN_MODEL_DATA_DIR", artifacts)
    target = artifacts / "release/new_set/sft/shard.jsonl"
    assert quarantine_reason(target) is None
    (registry / "release/new_set/TOMBSTONE.md").write_text("sealed\n", encoding="utf-8")
    with pytest.raises(QuarantinedArtifactError, match=r"release/new_set/TOMBSTONE\.md"):
        refuse_quarantined(target, "test loader")


def test_quarantine_guard_fails_closed_without_inventory(
    sealed_copy: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fresh_guard_caches: None
) -> None:
    monkeypatch.setattr(paths_mod, "QUARANTINE_INVENTORY_PATH", tmp_path / "missing.json")
    with pytest.raises(QuarantinedArtifactError, match="inventory missing"):
        refuse_quarantined(sealed_copy, "test loader")
    with pytest.raises(QuarantinedArtifactError, match="inventory missing"):
        refuse_quarantined(f"{LOGICAL_OPEN_MODEL_PREFIX}/components/c1_new/train.jsonl", "test loader")


# AC2 — every loader refuses quarantined paths, release/ tombstones included.


def _load_script(name: str, relative: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_loader_train_and_eval_real_model_refuses(
    tmp_path: Path, sealed_copy: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module("scripts.projects.open_model_data.train_and_eval_real_model")
    fresh = tmp_path / "fresh.jsonl"
    fresh.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out"
    for train, heldout in ((sealed_copy, fresh), (fresh, RELEASE_TOMBSTONE_PATH)):
        argv = ["x", "--train-file", str(train), "--heldout-file", str(heldout), "--protection-file", str(fresh)]
        monkeypatch.setattr(sys, "argv", [*argv, "--output-dir", str(output), "--device", "cpu"])
        with pytest.raises(QuarantinedArtifactError):
            module.main()
    assert not output.exists()


def test_loader_gemma_hardware_probe_refuses() -> None:
    module = importlib.import_module("scripts.projects.open_model_data.gemma_hardware_probe")
    # The probe resolves bindings through the classification table, so use classified paths.
    release = f"{LOGICAL_OPEN_MODEL_PREFIX}/release/uldr_v05_grammar_valency/brown_uk_negative_control_eval.jsonl"
    for logical in (SEALED_CANARY, release):
        with pytest.raises(QuarantinedArtifactError):
            module._assert_artifact({"logical_path": logical, "bytes": 1, "sha256": "0" * 64})


def test_loader_package_unified_dataset_refuses(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.projects.open_model_data.package_unified_dataset")
    release = tmp_path / "release"
    (release / "uldr_v03_dialect").mkdir(parents=True)
    (release / "uldr_v03_dialect/sft_dialect_protection_500.jsonl").write_text("{}\n", encoding="utf-8")
    output = tmp_path / "package"
    for release_dir in (module.MANAGED_RELEASE_DIR, release):
        with pytest.raises(QuarantinedArtifactError):
            module.build_unified_dataset(release_dir, output)
    assert not output.exists()


def test_loader_upload_to_huggingface_refuses_before_any_hub_call(
    tmp_path: Path, sealed_copy: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module("scripts.projects.open_model_data.upload_to_huggingface")
    hub = types.ModuleType("huggingface_hub")
    hub.HfApi = lambda **_: pytest.fail("HfApi constructed for a quarantined package")  # type: ignore[attr-defined]
    hub.login = lambda **_: pytest.fail("login attempted for a quarantined package")  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "huggingface_hub", hub)
    uldr = tmp_path / "uldr"
    uldr.mkdir()
    (uldr / "manifest.json").write_text(json.dumps({"dataset_name": module.QUARANTINED_PACKAGE_NAME}), "utf-8")
    tombstoned = tmp_path / RELEASE_TOMBSTONE_PATH
    tombstoned.mkdir(parents=True)
    for dataset_dir in (sealed_copy.parent, uldr, tombstoned):
        monkeypatch.setattr(sys, "argv", ["x", "--dataset-dir", str(dataset_dir), "--token", "unused"])
        assert module.main() == 1
    with pytest.raises(QuarantinedArtifactError):
        module.refuse_quarantined_package(sealed_copy.parent)


def test_loader_v4_format_decolonization_refuses(tmp_path: Path, sealed_copy: Path) -> None:
    module = importlib.import_module("scripts.projects.open_model_data.v4_format_decolonization")
    output = tmp_path / "consumer"
    with pytest.raises(QuarantinedArtifactError):
        module.format_consumer_datasets(module.DEFAULT_INPUT_DIR, output)
    staged = tmp_path / "generated"
    staged.mkdir()
    shutil.copyfile(sealed_copy, staged / "train_trajectories.jsonl")
    (staged / "train_dpo.jsonl").write_text("{}\n", encoding="utf-8")
    manifest = {
        "shards": [
            {"partition": "train", "trajectories_file": "train_trajectories.jsonl", "dpo_pairs_file": "train_dpo.jsonl"}
        ]
    }
    (staged / "decolonization_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(QuarantinedArtifactError, match="trajectories shard"):
        module.format_consumer_datasets(staged, output)


def test_loader_v4_open_weight_learning_study_refuses(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.projects.open_model_data.v4_open_weight_learning_study")
    with pytest.raises(QuarantinedArtifactError):
        module._build_recipe_into(REPO_ROOT, tmp_path / "recipe.json")
    recipe = tmp_path / "staged_recipe.json"
    records = f"{LOGICAL_OPEN_MODEL_PREFIX}/dataset/v4_human_source_dataset_records_v1.jsonl"
    recipe.write_text(json.dumps({"dataset_target": {"records_path": records}}), encoding="utf-8")
    with pytest.raises(QuarantinedArtifactError):
        module._run_study_into(REPO_ROOT, recipe, tmp_path / "runs.jsonl", tmp_path / "receipt.json")
    assert not (tmp_path / "runs.jsonl").exists()


def test_loader_v4_pilot_canary_evaluation_refuses(tmp_path: Path, sealed_copy: Path) -> None:
    module = importlib.import_module("scripts.projects.open_model_data.v4_pilot_canary_evaluation")
    fresh = tmp_path / "fresh.jsonl"
    fresh.write_text("{}\n", encoding="utf-8")
    with pytest.raises(QuarantinedArtifactError):
        module.select_pilot_canary_dataset(sealed_copy, fresh, fresh, tmp_path / "out.jsonl")
    with pytest.raises(QuarantinedArtifactError):
        module.select_pilot_canary_dataset(
            module.DEFAULT_GOLD_SEEDS, module.DEFAULT_STEM_CONTROLS, module.DEFAULT_HELDOUT_SUITE, tmp_path / "o"
        )
    with pytest.raises(QuarantinedArtifactError):
        module.generate_or_load_adapter(tmp_path / "adapter.safetensors", sealed_copy, fresh)
    with pytest.raises(QuarantinedArtifactError):
        module.load_and_evaluate_cases(REPO_ROOT / RELEASE_TOMBSTONE_PATH)
    with pytest.raises(QuarantinedArtifactError):
        module.verify_pilot_canary()
    assert not (tmp_path / "out.jsonl").exists()


def test_loader_train_gemma_huggingface_refuses(sealed_copy: Path) -> None:
    module = _load_script("quarantine_train_gemma", "scripts/dataset/train_gemma_huggingface.py")
    for dataset in (str(sealed_copy), str(REPO_ROOT / SEALED_CANARY), str(REPO_ROOT / RELEASE_TOMBSTONE_PATH)):
        with pytest.raises(QuarantinedArtifactError):
            module.refuse_rebuild_required_candidate(dataset)


@pytest.mark.parametrize(
    "relative",
    [
        "scripts/projects/open_model_data/train_and_eval_real_model.py",
        "scripts/projects/open_model_data/gemma_hardware_probe.py",
        "scripts/projects/open_model_data/package_unified_dataset.py",
        "scripts/projects/open_model_data/upload_to_huggingface.py",
        "scripts/projects/open_model_data/v4_format_decolonization.py",
        "scripts/projects/open_model_data/v4_open_weight_learning_study.py",
        "scripts/projects/open_model_data/v4_pilot_canary_evaluation.py",
        "scripts/dataset/train_gemma_huggingface.py",
    ],
)
def test_loader_calls_the_quarantine_guard(relative: str) -> None:
    tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
    calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    assert "refuse_quarantined" in calls or "refuse_quarantined_package" in calls, relative


# AC3 — neither notebook can push to a hub.


def _code_cells(notebook: Path) -> list[str]:
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    return ["".join(cell["source"]) for cell in cells if cell["cell_type"] == "code"]


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda path: path.stem)
def test_notebook_has_no_hub_write(notebook: Path) -> None:
    for source in _code_cells(notebook):
        python = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith(("!", "%")))
        called = set()
        for node in ast.walk(ast.parse(python)):
            if isinstance(node, ast.Call):
                func = node.func
                called.add(func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", ""))
        assert not called & HUB_WRITE_CALLS, (notebook.name, called & HUB_WRITE_CALLS)
        for name in HUB_WRITE_CALLS:
            assert name not in source, (notebook.name, name)


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda path: path.stem)
def test_notebook_first_code_cell_refuses_to_run(notebook: Path) -> None:
    first = _code_cells(notebook)[0]
    with pytest.raises(RuntimeError, match=r"Quarantined \(#9607"):
        exec(compile(first, notebook.name, "exec"), {})  # the guard cell has no side effects


# AC4 / AC5 — archived generators and their tests cannot be imported by active code.


def test_archive_holds_generators_and_their_tests() -> None:
    for module in ARCHIVED_MODULES:
        assert (ARCHIVE_DIR / "scripts" / f"{module}.py").is_file()
        assert not (OPEN_MODEL_SCRIPTS / f"{module}.py").exists()
    for test in ("test_v6_mine_ulif_phraseology.py", "test_v6_mine_general_assistant_textbooks.py"):
        assert (ARCHIVE_DIR / "tests" / test).is_file()
        assert not (REPO_ROOT / "tests/projects/open_model_data" / test).exists()
    assert (ARCHIVE_DIR / "issue_8341_branch.patch").is_file()


def test_archive_package_refuses_import(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(REPO_ROOT))
    for module in ARCHIVED_MODULES:
        with pytest.raises(ImportError, match="#9607"):
            importlib.import_module(f"archive.code.open_model_data.scripts.{module}")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(f"scripts.projects.open_model_data.{module}")


def _imported_names(tree: ast.AST) -> Iterator[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            yield base
            yield from (f"{base}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", "")) in {
            "import_module",
            "__import__",
        }:
            yield from (arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str))


@pytest.mark.repo_invariant
@pytest.mark.repo_wide
def test_archive_import_guard_active_code() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "scripts", "tests"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout.split("\0")
    this_file = Path(__file__).resolve()
    offenders = []
    for relative in tracked:
        path = REPO_ROOT / relative
        if not relative.endswith(".py") or not path.is_file() or path.resolve() == this_file:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for name in _imported_names(tree):
            parts = name.split(".")
            if parts[:2] == ["archive", "code"] or any(module in parts for module in ARCHIVED_MODULES):
                offenders.append(f"{relative}: {name}")
    assert offenders == []
