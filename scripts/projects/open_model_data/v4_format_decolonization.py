"""Downstream consumer dataset formatter for ULDR (#7926).

Transforms normative SFT reasoning trajectories and contrastive DPO pairs
into standard open-weight training formats (ShareGPT/ChatML with <thought> reasoning tags,
and Hugging Face TRL DPO format) with multi-shard packaging under the 2,000,000 byte
repository hard gate, while strictly preserving train / held-out partition isolation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.v4_decolonization_reasoning import (
    classify_calque_type,
    scan_generated_files,
)

DEFAULT_INPUT_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "generated"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "consumer"

SYSTEM_PROMPT = (
    "Ти — мовний помічник з української культури мовлення та мовної деколонізації. "
    "Твоє завдання — пояснювати автентичні норми української літературної мови, "
    "діагностувати радянські кальки, росіянізми та штучні канцелярити, "
    "розкривати їхні етимолого-морфемні та історичні першопричини, "
    "а також надавати верифікований за словником ВЕСУМ та шкільними підручниками МОН "
    "багаторівневий спектр питомих відповідників."
)


def trajectory_to_sharegpt(trajectory: dict[str, Any]) -> dict[str, Any]:
    """Convert a normative ULDR trajectory to ShareGPT format with <thought> block."""
    traj_id = trajectory["trajectory_id"]
    query = trajectory["query"]
    thought_steps = trajectory.get("reasoning_steps", [])
    response = trajectory.get("final_response") or trajectory.get("response", "")

    thought_content = "\n".join(f"Крок {i + 1}: {step}" for i, step in enumerate(thought_steps))
    assistant_reply = f"<thought>\n{thought_content}\n</thought>\n\n{response}"

    return {
        "id": traj_id,
        "target_term": trajectory.get("target_term", ""),
        "conversations": [
            {"from": "system", "value": SYSTEM_PROMPT},
            {"from": "human", "value": query},
            {"from": "gpt", "value": assistant_reply},
        ],
    }


def dpo_pair_to_trl(dpo_pair: dict[str, Any]) -> dict[str, Any]:
    """Convert an ULDR DPO pair to standard Hugging Face TRL DPO format."""
    meta = dpo_pair.get("metadata", {})
    target = meta.get("target_term") or dpo_pair.get("target_term", "")
    calque_cat = meta.get("calque_category")
    if not calque_cat and target:
        calque_cat, _, _ = classify_calque_type(target)
    return {
        "id": dpo_pair["pair_id"],
        "target_term": target,
        "calque_category": calque_cat or "lexical_calque",
        "system": SYSTEM_PROMPT,
        "prompt": dpo_pair["prompt"],
        "chosen": dpo_pair["chosen"],
        "rejected": dpo_pair["rejected"],
    }


def format_consumer_datasets(
    input_dir: Path,
    output_dir: Path,
    records_per_shard: int = 400,
) -> dict[str, Any]:
    """Read all generated ULDR shards and format them into consumer JSONL files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = input_dir / "decolonization_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing manifest at {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Clean existing consumer jsonl files
    for old_f in output_dir.glob("*.jsonl"):
        old_f.unlink()

    stats: dict[str, Any] = {
        "sharegpt_train_count": 0,
        "sharegpt_held_out_count": 0,
        "trl_dpo_train_count": 0,
        "trl_dpo_held_out_count": 0,
        "shards": [],
    }

    partitions = ("train", "held_out")

    for part in partitions:
        part_trajs: list[dict[str, Any]] = []
        part_dpos: list[dict[str, Any]] = []

        # Find shards for this partition
        for shard_info in manifest.get("shards", []):
            if shard_info.get("partition") != part:
                continue
            traj_p = input_dir / shard_info["trajectories_file"]
            dpo_p = input_dir / shard_info["dpo_pairs_file"]

            if traj_p.is_file():
                with traj_p.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            part_trajs.append(json.loads(line))

            if dpo_p.is_file():
                with dpo_p.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            part_dpos.append(json.loads(line))

        # Write sharded ShareGPT
        for i in range(0, len(part_trajs), records_per_shard):
            chunk = part_trajs[i : i + records_per_shard]
            shard_idx = (i // records_per_shard) + 1
            shard_name = f"uldr_sharegpt_{part}_part{shard_idx:03d}.jsonl"
            out_file = output_dir / shard_name
            with out_file.open("w", encoding="utf-8") as fh:
                for item in chunk:
                    sg_item = trajectory_to_sharegpt(item)
                    fh.write(json.dumps(sg_item, ensure_ascii=False) + "\n")
                    if part == "train":
                        stats["sharegpt_train_count"] += 1
                    else:
                        stats["sharegpt_held_out_count"] += 1

            stats["shards"].append(
                {
                    "format": "sharegpt",
                    "partition": part,
                    "file": shard_name,
                    "bytes": out_file.stat().st_size,
                    "sha256": hashlib.sha256(out_file.read_bytes()).hexdigest(),
                    "records_count": len(chunk),
                }
            )

        # Write sharded TRL DPO
        for i in range(0, len(part_dpos), records_per_shard):
            chunk = part_dpos[i : i + records_per_shard]
            shard_idx = (i // records_per_shard) + 1
            shard_name = f"uldr_dpo_{part}_part{shard_idx:03d}.jsonl"
            out_file = output_dir / shard_name
            with out_file.open("w", encoding="utf-8") as fh:
                for item in chunk:
                    trl_item = dpo_pair_to_trl(item)
                    fh.write(json.dumps(trl_item, ensure_ascii=False) + "\n")
                    if part == "train":
                        stats["trl_dpo_train_count"] += 1
                    else:
                        stats["trl_dpo_held_out_count"] += 1

            stats["shards"].append(
                {
                    "format": "trl_dpo",
                    "partition": part,
                    "file": shard_name,
                    "bytes": out_file.stat().st_size,
                    "sha256": hashlib.sha256(out_file.read_bytes()).hexdigest(),
                    "records_count": len(chunk),
                }
            )

    # Active private path and restricted source scan across all generated consumer shards
    consumer_shard_paths = [output_dir / sh["file"] for sh in stats["shards"]]
    zero_paths, zero_restricted, violations = scan_generated_files(consumer_shard_paths)
    if violations:
        raise RuntimeError("Private content leak detected in consumer datasets:\n" + "\n".join(violations))

    stats["quality_metrics"] = {
        "zero_private_paths": zero_paths,
        "zero_restricted_sources": zero_restricted,
    }

    summary_path = output_dir / "consumer_formats_manifest.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Format ULDR data for downstream model training")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--records-per-shard", type=int, default=400)

    args = parser.parse_args()
    stats = format_consumer_datasets(args.input_dir, args.out_dir, records_per_shard=args.records_per_shard)
    print("Successfully formatted consumer datasets:")
    print(f"  ShareGPT Train: {stats['sharegpt_train_count']} records")
    print(f"  ShareGPT Held-Out: {stats['sharegpt_held_out_count']} records")
    print(f"  TRL DPO Train: {stats['trl_dpo_train_count']} records")
    print(f"  TRL DPO Held-Out: {stats['trl_dpo_held_out_count']} records")
    print(f"  Total consumer shards: {len(stats['shards'])}")
    print(f"Manifest written to {args.out_dir / 'consumer_formats_manifest.json'}")


if __name__ == "__main__":
    main()
