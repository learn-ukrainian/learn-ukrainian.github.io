#!/usr/bin/env python3
"""Upload a previously built external dataset package to a private Hub repository.

Require --dataset-dir, --repo-id and a token from --token or HF_TOKEN, without persistent
login. Validate source quarantine before any Hub call, authenticate, and verify
effective private visibility before uploading. Only an exact repository-not-found
error with HTTP 404 permits private repository creation, followed by a fresh
privacy check. Public or unknown privacy refuses the upload.

These transfer checks do not establish the quality, access, capacity or release
approval required by docs/projects/open-model-data/HF_DATASET_STORAGE_DESIGN.md.
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
    """Validate quarantine admission before any Hub call.

    Load the sealed inventory even for an empty package. Raise
    QuarantinedArtifactError for a missing inventory or unexpected schema, a non-directory,
    quarantined package or file paths, a manifest with invalid UTF-8, malformed JSON or a non-object value,
    or the legacy ULDR dataset name. Other inventory read or parse errors
    propagate. This does not validate release contents.
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
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as exc:
            raise QuarantinedArtifactError(f"unreadable package manifest {manifest}; refusing upload") from exc
        if name == QUARANTINED_PACKAGE_NAME:
            raise QuarantinedArtifactError(
                f"Refusing Hugging Face upload of {dataset_dir}: a ULDR package is built only from the "
                "quarantined old-plan release sets (#9607, plan PA1)."
            )


def main() -> int:
    """Parse CLI options and upload an admitted package to a verified private target.

    --dataset-dir and --repo-id are required. --private is enabled
    by default. --token takes precedence over HF_TOKEN; cached login is not used.
    Return 0 after upload, or 1 for a missing input, quarantine refusal, missing
    token or Hub client, authentication failure, target preparation or privacy
    failure, or upload failure. Hub failures use generic messages without raw
    exceptions or identity responses. Invalid CLI arguments exit via argparse.

    The caller must satisfy release prerequisites separately. A successful
    upload does not verify readback, access grants, capacity or semantic quality.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Upload a previously built dataset to a private Hugging Face repository.\n"
            "Use only after checking the external package and its intended repository; public targets are refused."
        ),
        epilog=(
            "Example: .venv/bin/python "
            "scripts/projects/open_model_data/upload_to_huggingface.py "
            "--dataset-dir '<external-package-dir>' --repo-id '<verified-project-org>/<dataset-name>' --private\n"
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
        required=True,
        help="Hugging Face repo ID in the verified project organization (required; format: organization/dataset)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Hugging Face API token (default: HF_TOKEN environment variable; never saved locally)",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        default=True,
        help="Create a private repository (default: private; existing public repositories are refused)",
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
    if not token or not token.strip():
        print("ERROR: Provide a Hugging Face token via --token or HF_TOKEN.")
        return 1

    try:
        from huggingface_hub import HfApi
        from huggingface_hub.errors import RepositoryNotFoundError
    except ImportError:
        print("ERROR: huggingface_hub is not installed. Install via: pip install huggingface_hub")
        return 1

    try:
        api = HfApi(token=token)
        api.whoami()
    except Exception:
        print("ERROR: Hugging Face authentication failed.")
        return 1

    try:
        try:
            info = api.repo_info(repo_id=args.repo_id, repo_type="dataset")
        except RepositoryNotFoundError as exc:
            # The Hub also uses this class for authentication failures and gated repos.
            if type(exc) is not RepositoryNotFoundError or getattr(exc.response, "status_code", None) != 404:
                raise
            api.create_repo(
                repo_id=args.repo_id,
                repo_type="dataset",
                private=args.private,
                exist_ok=True,
            )
            # A concurrent creator may have won with a public repo; create_repo does not change it.
            info = api.repo_info(repo_id=args.repo_id, repo_type="dataset")
        if getattr(info, "private", None) is not True:
            print("ERROR: Target repository is public or its privacy could not be verified; refusing upload.")
            return 1
    except Exception:
        print("ERROR: Could not prepare and verify a private Hugging Face dataset repository.")
        return 1

    try:
        api.upload_folder(
            folder_path=str(dataset_dir),
            repo_id=args.repo_id,
            repo_type="dataset",
            commit_message="Release Unified Ukrainian Language Decolonization & Reasoning (ULDR) Master Dataset",
        )
    except Exception:
        print("ERROR: Hugging Face dataset upload failed.")
        return 1

    print("\n" + "=" * 70)
    print("✓ SUCCESS: Dataset successfully uploaded to Hugging Face Hub!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
