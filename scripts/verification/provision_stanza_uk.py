"""The sole installer for the pinned temporal-protiah model inventory."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from scripts.verification.stanza_models import manifest, model_root, resources_bytes, valid_file


def provision(*, verify_only: bool = False) -> dict:
    """Stage all verified downloads before publishing the immutable inventory."""
    inventory = manifest()
    root = model_root()
    if verify_only:
        if not all(valid_file(root / f["install_path"], f) for f in inventory["files"]):
            raise ValueError("missing_or_hash_mismatched_model")
        if (root / "resources.json").read_bytes() != resources_bytes():
            raise ValueError("missing_or_hash_mismatched_resources")
    else:
        from huggingface_hub import hf_hub_download

        root.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="stanza-verified-", dir=root.parent) as staging:
            staged = Path(staging)
            for entry in inventory["files"]:
                existing = root / entry["install_path"]
                source = (
                    existing
                    if valid_file(existing, entry)
                    else Path(
                        hf_hub_download(
                            repo_id=inventory["repository"],
                            filename=entry["path"],
                            revision=inventory["revision"],
                        )
                    )
                )
                if not valid_file(source, entry):
                    raise ValueError("download_hash_mismatch")
                target = staged / entry["install_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                if not valid_file(target, entry):
                    raise ValueError("staging_hash_mismatch")
            (staged / "resources.json").write_bytes(resources_bytes())
            root.mkdir(parents=True, exist_ok=True)
            for source in staged.rglob("*"):
                if source.is_file():
                    target = root / source.relative_to(staged)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(source, target)
    return {"revision": inventory["revision"], "files": len(inventory["files"]), "verified": True}


def main() -> int:
    """Provision or verify from the fixed manifest; diagnostics omit local paths."""
    parser = argparse.ArgumentParser(
        description="Install SHA-256 verified Ukrainian Stanza weights at the pinned revision.\n"
        "Use before offline temporal-protiah inference; never use runtime downloads.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.verification.provision_stanza_uk\n"
        "  .venv/bin/python -m scripts.verification.provision_stanza_uk --verify-only\n"
        "Outputs: verified weights under STANZA_RESOURCES_DIR (default ~/stanza_resources/protiah/<revision>); JSON receipt.\n"
        "Exit codes: 0 verified; 1 provisioning or integrity failure.\n"
        "Related: stanza_uk_manifest.json; docs/runbooks/temporal-protiah.md; #9661.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Check installed sizes and hashes without downloading (default: false).",
    )
    args = parser.parse_args()
    try:
        print(json.dumps(provision(verify_only=args.verify_only)))
    except Exception as error:
        print(json.dumps({"verified": False, "error": type(error).__name__}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
