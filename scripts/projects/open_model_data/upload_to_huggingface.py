#!/usr/bin/env python3
"""Upload unified ULDR dataset directly to Hugging Face Hub.

Pass the external directory created by package_unified_dataset.py explicitly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.projects.open_model_data.paths import (
    QuarantinedArtifactError,
    quarantine_inventory,
    refuse_quarantined,
)

# Every package with this name was assembled from the sealed old-plan release sets (#9607).
QUARANTINED_PACKAGE_NAME = "Ukrainian Linguistic Decolonization & Reasoning (ULDR)"


def refuse_quarantined_package(dataset_dir: Path) -> None:
    """Refuse a package directory that is, holds, or was built from quarantined artifacts.

    The sealed inventory is loaded first, whatever the package holds (even nothing), so a
    missing or invalid inventory refuses every upload before any hub call.
    """
    quarantine_inventory()
    if not dataset_dir.is_dir():
        raise QuarantinedArtifactError(f"Hugging Face upload input is not a package directory: {dataset_dir}")
    refuse_quarantined(dataset_dir, "Hugging Face upload directory")
    for path in sorted(dataset_dir.rglob("*")):
        if path.is_file():
            refuse_quarantined(path, "Hugging Face upload file")
    manifest = dataset_dir / "manifest.json"
    if manifest.is_file():
        try:
            name = json.loads(manifest.read_text(encoding="utf-8")).get("dataset_name")
        except (json.JSONDecodeError, AttributeError) as exc:
            raise QuarantinedArtifactError(f"unreadable package manifest {manifest}; refusing upload") from exc
        if name == QUARANTINED_PACKAGE_NAME:
            raise QuarantinedArtifactError(
                f"Refusing Hugging Face upload of {dataset_dir}: a ULDR package is built only from the "
                "quarantined old-plan release sets (#9607, plan PA1)."
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Upload a previously built unified ULDR dataset to Hugging Face.\n"
            "Use only after checking the external package and its intended repository."
        ),
        epilog=(
            "Example: /home/ops/learn-ukrainian/.venv/bin/python "
            "scripts/projects/open_model_data/upload_to_huggingface.py "
            "--dataset-dir /tmp/uldr-v02 --repo-id owner/uldr --private\n"
            "Outputs: a dataset repository commit on Hugging Face; no local package files.\n"
            "Exit codes: 0 on upload; nonzero on invalid input, a quarantined package (#9607), authentication, "
            "or upload failure.\n"
            "Related: package_unified_dataset.py, paths.refuse_quarantined, issues #8809 and #9607."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        required=True,
        help="External package directory containing train.jsonl, dpo.jsonl, eval.jsonl, README.md",
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default="krisztiankoos/uldr",
        help="Hugging Face repo ID (default: krisztiankoos/uldr)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Hugging Face API token (defaults to HF_TOKEN env variable or ~/.cache/huggingface/token)",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Make repository private (default is public)",
    )
    args = parser.parse_args()

    dataset_dir = args.dataset_dir
    if not dataset_dir.exists():
        print(f"ERROR: Dataset directory does not exist: {dataset_dir}")
        print("Run package_unified_dataset.py first!")
        return 1
    try:
        refuse_quarantined_package(dataset_dir)
    except QuarantinedArtifactError as exc:
        print(f"ERROR: {exc}")
        return 1

    token = args.token or os.environ.get("HF_TOKEN")

    try:
        from huggingface_hub import HfApi, login
    except ImportError:
        print("ERROR: huggingface_hub is not installed. Install via: pip install huggingface_hub")
        return 1

    if token:
        login(token=token)

    api = HfApi(token=token)

    try:
        user_info = api.whoami()
        print(f"Authenticated as Hugging Face user: {user_info.get('name')} (Pro: {user_info.get('isPro', False)})")
    except Exception as e:
        print(f"Authentication error: {e}")
        print("\nPlease provide a valid Hugging Face token:")
        print("  export HF_TOKEN='hf_...'")
        print("  or pass --token 'hf_...'")
        return 1

    print(f"Ensuring Hugging Face dataset repository exists: {args.repo_id}...")
    api.create_repo(
        repo_id=args.repo_id,
        repo_type="dataset",
        private=args.private,
        exist_ok=True,
    )

    print(f"Uploading files from {dataset_dir} to {args.repo_id}...")
    api.upload_folder(
        folder_path=str(dataset_dir),
        repo_id=args.repo_id,
        repo_type="dataset",
        commit_message="Release Unified Ukrainian Language Decolonization & Reasoning (ULDR) Master Dataset",
    )

    print("\n" + "=" * 70)
    print("✓ SUCCESS: Dataset successfully uploaded to Hugging Face Hub!")
    print(f"Repository URL: https://huggingface.co/datasets/{args.repo_id}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
