#!/usr/bin/env python3
"""Upload unified ULDR dataset directly to Hugging Face Hub.

Usage:
  # Using HF_TOKEN env variable:
  export HF_TOKEN="hf_..."
  python scripts/projects/open_model_data/upload_to_huggingface.py

  # Or passing token via CLI:
  python scripts/projects/open_model_data/upload_to_huggingface.py --token hf_...

  # Custom repo:
  python scripts/projects/open_model_data/upload_to_huggingface.py --repo-id krisztiankoos/uldr --private
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload unified ULDR dataset to Hugging Face.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=REPO_ROOT / "data" / "projects" / "open_model_data" / "export" / "uldr_v01",
        help="Path to directory containing train.jsonl, dpo.jsonl, eval.jsonl, README.md",
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

    dataset_dir = args.dataset_dir
    if not dataset_dir.exists():
        print(f"ERROR: Dataset directory does not exist: {dataset_dir}")
        print("Run package_unified_dataset.py first!")
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
