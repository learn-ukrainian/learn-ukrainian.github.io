"""Hugging Face dataset synchronization tool for Word Atlas audio (#7873).

Initializes and synchronizes the public Hugging Face Datasets repository
`learn-ukrainian/word-atlas-audio` with local OGG/Opus audio assets, manifest, and dataset card.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

DEFAULT_REPO_ID = "learn-ukrainian/word-atlas-audio"
DATASET_CARD_TEMPLATE = """---
license: cc-by-nc-4.0
task_categories:
  - text-to-speech
language:
  - uk
tags:
  - ukrainian
  - audio
  - pronunciation
  - word-atlas
  - piper-tts
  - opus
size_categories:
  - 10K<n<100K
---

# Word Atlas & Practice Hub Ukrainian Audio Dataset

Pre-recorded high-fidelity Ukrainian pronunciation clips for the **Word Atlas** and **Practice Hub** at [learn-ukrainian.org](https://learn-ukrainian.org).

## Dataset Summary
- **Audio Format:** OGG / Opus
- **Bitrate:** 24 kbps mono, VBR, 24 kHz
- **Average Size:** ~1.5–3 KB per word clip
- **Voice Engine:** Piper TTS `uk_UA-ukrainian_tts-medium` (speaker `lada` / ID 0)
- **Stress Authority:** Unambiguous lexical stress from Ukrainian State Standard 2024, VESUM, and ULIF morphological dictionaries
- **Repository Layout:** Sharded 2-character prefix folders (`audio/xx/{hash}.opus`) with root `manifest.json`

## Direct On-Demand CDN Fetch
Browser clients derive the asset URL deterministically without loading large manifest payloads:
```javascript
const key = lemma.toLowerCase().replace(/[\\u0300\\u0301]/g, '').replace(/[’ʼ]/g, "'").trim();
const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(key));
const hex = Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
const url = `https://huggingface.co/datasets/learn-ukrainian/word-atlas-audio/resolve/main/audio/${hex.slice(0, 2)}/${hex}.opus`;
```

## License
- Audio dataset: Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).
- Voice model dataset: CC0 (rhasspy/piper-voices).
"""


def ensure_dataset_card(directory: Path) -> Path:
    """Create README.md dataset card if not already present."""
    readme_path = directory / "README.md"
    if not readme_path.exists():
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        readme_path.write_text(DATASET_CARD_TEMPLATE, encoding="utf-8")
    return readme_path


def scan_local_files(directory: Path) -> list[Path]:
    """List all audio files and manifests in directory."""
    files = []
    for p in directory.rglob("*"):
        if p.is_file() and (p.suffix in {".opus", ".json", ".md"}):
            files.append(p)
    return files


def sync_hf_dataset(
    local_dir: Path,
    repo_id: str = DEFAULT_REPO_ID,
    token: str | None = None,
    dry_run: bool = False,
    init_only: bool = False,
) -> dict[str, Any]:
    """Initialize repository and upload audio folder to Hugging Face Hub."""
    ensure_dataset_card(local_dir)
    files = scan_local_files(local_dir)

    total_bytes = sum(f.stat().st_size for f in files)
    opus_count = sum(1 for f in files if f.suffix == ".opus")

    result = {
        "repo_id": repo_id,
        "total_files": len(files),
        "opus_files": opus_count,
        "total_bytes": total_bytes,
        "dry_run": dry_run,
        "init_only": init_only,
    }

    if dry_run:
        return result

    from huggingface_hub import HfApi

    effective_token = token or os.environ.get("HF_TOKEN")
    if not effective_token:
        raise ValueError("HF_TOKEN environment variable or --token required for Hugging Face API operations")

    api = HfApi(token=effective_token)
    api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True, private=False)

    if init_only:
        readme_path = local_dir / "README.md"
        commit_info = api.upload_file(
            path_or_fileobj=str(readme_path),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
            commit_message="Initialize Word Atlas audio dataset card",
        )
        result["commit"] = str(commit_info)
        return result

    commit_info = api.upload_folder(
        folder_path=str(local_dir),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message=f"Sync Word Atlas audio ({opus_count} clips)",
    )
    result["commit"] = str(commit_info)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synchronize Word Atlas audio with Hugging Face Datasets repository (#7873).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--local-dir", type=Path, default=Path("batch_state/audio_opus"), help="Local audio directory")
    parser.add_argument(
        "--repo-id", default=DEFAULT_REPO_ID, help=f"Hugging Face dataset repo (default: {DEFAULT_REPO_ID})"
    )
    parser.add_argument("--token", help="Hugging Face API token (defaults to HF_TOKEN env var)")
    parser.add_argument("--init-only", action="store_true", help="Initialize repository and card without audio sync")
    parser.add_argument("--dry-run", action="store_true", help="Scan and preview upload without API calls")
    args = parser.parse_args()

    if not args.local_dir.exists():
        args.local_dir.mkdir(parents=True, exist_ok=True)

    res = sync_hf_dataset(
        args.local_dir,
        repo_id=args.repo_id,
        token=args.token,
        dry_run=args.dry_run,
        init_only=args.init_only,
    )
    print(f"Hugging Face dataset sync status: {res}")


if __name__ == "__main__":
    main()
