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


MAX_SHARD_BYTES = 1_800_000  # Hard ceiling comfortably below repository 2,000,000 byte limit


def trajectory_to_sharegpt(trajectory: dict[str, Any]) -> dict[str, Any]:
    """Convert a normative ULDR trajectory to ShareGPT & ChatML/Gemma formats with <thought> block."""
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
        # Native ChatML / Gemma 3 & 4 turn structure with system instructions prepended to user turn
        "messages": [
            {"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{query}"},
            {"role": "assistant", "content": assistant_reply},
        ],
    }


def dpo_pair_to_trl(dpo_pair: dict[str, Any]) -> dict[str, Any]:
    """Convert an ULDR DPO pair to standard Hugging Face TRL DPO format with embedded system prompt."""
    meta = dpo_pair.get("metadata", {})
    target = meta.get("target_term") or dpo_pair.get("target_term", "")
    calque_cat = meta.get("calque_category")
    if not calque_cat and target:
        calque_cat, _, _ = classify_calque_type(target)

    # TRL DPOTrainer does not tokenize a separate 'system' column during training.
    # Prepend the system prompt directly into the prompt column so it is always tokenized.
    raw_prompt = dpo_pair["prompt"]
    prompt_with_system = f"{SYSTEM_PROMPT}\n\n{raw_prompt}"

    return {
        "id": dpo_pair["pair_id"],
        "target_term": target,
        "calque_category": calque_cat or "lexical_calque",
        "system": SYSTEM_PROMPT,
        "prompt": prompt_with_system,
        "chosen": dpo_pair["chosen"],
        "rejected": dpo_pair["rejected"],
    }


def _write_sharded_records(
    records: list[dict[str, Any]],
    format_fn: Any,
    output_dir: Path,
    file_prefix: str,
    partition: str,
    format_name: str,
    max_records_per_shard: int = 400,
    max_shard_bytes: int = MAX_SHARD_BYTES,
) -> tuple[list[dict[str, Any]], int]:
    """Write records into shards respecting both record-count and byte-budget limits."""
    shards_metadata: list[dict[str, Any]] = []
    total_written = 0

    current_chunk: list[dict[str, Any]] = []
    current_bytes = 0
    shard_index = 1

    def flush_shard() -> None:
        nonlocal current_chunk, current_bytes, shard_index, total_written
        if not current_chunk:
            return
        shard_file_name = f"{file_prefix}_{partition}_part{shard_index:03d}.jsonl"
        shard_path = output_dir / shard_file_name
        with shard_path.open("w", encoding="utf-8") as fh:
            for item in current_chunk:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

        actual_size = shard_path.stat().st_size
        if actual_size > max_shard_bytes:
            raise ValueError(
                f"Generated shard {shard_file_name} size {actual_size} exceeds max allowed {max_shard_bytes} bytes."
            )

        content_bytes = shard_path.read_bytes()
        shards_metadata.append(
            {
                "format": format_name,
                "partition": partition,
                "file": shard_file_name,
                "bytes": actual_size,
                "sha256": hashlib.sha256(content_bytes).hexdigest(),
                "records_count": len(current_chunk),
            }
        )
        total_written += len(current_chunk)
        shard_index += 1
        current_chunk = []
        current_bytes = 0

    for raw_item in records:
        formatted_item = format_fn(raw_item)
        line_bytes_len = len((json.dumps(formatted_item, ensure_ascii=False) + "\n").encode("utf-8"))
        if line_bytes_len > max_shard_bytes:
            raise ValueError(
                f"Individual record {formatted_item.get('id')} ({line_bytes_len} bytes) exceeds "
                f"maximum shard size {max_shard_bytes} bytes."
            )

        if current_chunk and (
            (current_bytes + line_bytes_len > max_shard_bytes) or (len(current_chunk) >= max_records_per_shard)
        ):
            flush_shard()

        current_chunk.append(formatted_item)
        current_bytes += line_bytes_len

    if current_chunk:
        flush_shard()

    return shards_metadata, total_written


def format_consumer_datasets(
    input_dir: Path,
    output_dir: Path,
    records_per_shard: int = 400,
    max_shard_bytes: int = MAX_SHARD_BYTES,
) -> dict[str, Any]:
    """Read all generated ULDR shards, validate firewalls, and format them into consumer JSONL files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = input_dir / "decolonization_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing manifest at {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Fail closed: verify all declared input shards exist and are non-empty
    declared_shards = manifest.get("shards", [])
    if not declared_shards:
        raise ValueError(f"Manifest {manifest_path} contains 0 declared shards.")

    for shard_info in declared_shards:
        traj_p = input_dir / shard_info["trajectories_file"]
        dpo_p = input_dir / shard_info["dpo_pairs_file"]
        if not traj_p.is_file():
            raise FileNotFoundError(f"Declared trajectories shard missing: {traj_p}")
        if not dpo_p.is_file():
            raise FileNotFoundError(f"Declared DPO pairs shard missing: {dpo_p}")
        if traj_p.stat().st_size == 0:
            raise ValueError(f"Declared trajectories shard is empty: {traj_p}")
        if dpo_p.stat().st_size == 0:
            raise ValueError(f"Declared DPO pairs shard is empty: {dpo_p}")

    # Clean existing consumer jsonl files
    for old_f in output_dir.glob("*.jsonl"):
        old_f.unlink()

    # Ingest partition records
    partition_records: dict[str, dict[str, list[dict[str, Any]]]] = {
        "train": {"trajs": [], "dpos": []},
        "held_out": {"trajs": [], "dpos": []},
    }

    for shard_info in declared_shards:
        part = shard_info.get("partition")
        if part not in partition_records:
            continue

        traj_p = input_dir / shard_info["trajectories_file"]
        dpo_p = input_dir / shard_info["dpo_pairs_file"]

        with traj_p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    partition_records[part]["trajs"].append(json.loads(line))

        with dpo_p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    partition_records[part]["dpos"].append(json.loads(line))

    # Cross-partition firewall validation (Finding F5)
    train_traj_ids = {t["trajectory_id"] for t in partition_records["train"]["trajs"]}
    held_out_traj_ids = {t["trajectory_id"] for t in partition_records["held_out"]["trajs"]}
    traj_id_overlap = train_traj_ids & held_out_traj_ids
    if traj_id_overlap:
        raise ValueError(
            f"Partition firewall violation: {len(traj_id_overlap)} overlapping trajectory IDs: {traj_id_overlap}"
        )

    train_dpo_ids = {d["pair_id"] for d in partition_records["train"]["dpos"]}
    held_out_dpo_ids = {d["pair_id"] for d in partition_records["held_out"]["dpos"]}
    dpo_id_overlap = train_dpo_ids & held_out_dpo_ids
    if dpo_id_overlap:
        raise ValueError(
            f"Partition firewall violation: {len(dpo_id_overlap)} overlapping DPO pair IDs: {dpo_id_overlap}"
        )

    train_targets = {
        t["target_term"].strip().lower() for t in partition_records["train"]["trajs"] if t.get("target_term")
    }
    held_out_targets = {
        t["target_term"].strip().lower() for t in partition_records["held_out"]["trajs"] if t.get("target_term")
    }
    target_overlap = train_targets & held_out_targets
    if target_overlap:
        raise ValueError(
            f"Partition firewall violation: {len(target_overlap)} overlapping target terms between train and held-out: {target_overlap}"
        )

    stats: dict[str, Any] = {
        "sharegpt_train_count": 0,
        "sharegpt_held_out_count": 0,
        "trl_dpo_train_count": 0,
        "trl_dpo_held_out_count": 0,
        "partition_firewall": {
            "verified_disjoint_ids": True,
            "verified_disjoint_targets": True,
            "train_held_out_overlap_count": 0,
        },
        "shards": [],
    }

    # Write sharded files with byte-budget control (Finding F6)
    for part in ("train", "held_out"):
        # ShareGPT
        sg_shards, sg_count = _write_sharded_records(
            records=partition_records[part]["trajs"],
            format_fn=trajectory_to_sharegpt,
            output_dir=output_dir,
            file_prefix="uldr_sharegpt",
            partition=part,
            format_name="sharegpt",
            max_records_per_shard=records_per_shard,
            max_shard_bytes=max_shard_bytes,
        )
        stats["shards"].extend(sg_shards)
        if part == "train":
            stats["sharegpt_train_count"] = sg_count
        else:
            stats["sharegpt_held_out_count"] = sg_count

        # TRL DPO
        dpo_shards, dpo_count = _write_sharded_records(
            records=partition_records[part]["dpos"],
            format_fn=dpo_pair_to_trl,
            output_dir=output_dir,
            file_prefix="uldr_dpo",
            partition=part,
            format_name="trl_dpo",
            max_records_per_shard=records_per_shard,
            max_shard_bytes=max_shard_bytes,
        )
        stats["shards"].extend(dpo_shards)
        if part == "train":
            stats["trl_dpo_train_count"] = dpo_count
        else:
            stats["trl_dpo_held_out_count"] = dpo_count

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
