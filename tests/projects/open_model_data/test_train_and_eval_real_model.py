"""Training data path of train_and_eval_real_model with its lazily imported ML stack (#9607)."""

from __future__ import annotations

from typing import Any

import pytest

from scripts.projects.open_model_data import train_and_eval_real_model as module


class _CharTokenizer:
    """Chat template plus character-level encoding: enough to exercise prompt masking."""

    def apply_chat_template(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        text = "".join(f"<{m['role']}>{m['content']}" for m in messages)
        return text + ("<assistant>" if kwargs.get("add_generation_prompt") else "")

    def __call__(self, text: str, *, truncation: bool, max_length: int) -> dict[str, list[int]]:
        return {"input_ids": [ord(char) for char in text][:max_length]}


@pytest.mark.slow
def test_sft_dataset_batches_through_dataloader_with_padding_and_prompt_masking() -> None:
    torch = pytest.importorskip("torch")
    from torch.utils.data import DataLoader

    records = [
        {"query": "q1", "final_response": "a", "reasoning_steps": ["r"]},
        {"query": "longer query", "final_response": "answer", "reasoning_steps": "why"},
        {"query": "", "final_response": "dropped"},
    ]
    dataset = module.SFTDataset(records, _CharTokenizer(), max_length=256)
    assert len(dataset) == 2
    first = dataset[0]
    prompt_len = len("<user>q1<assistant>")
    assert first["labels"][:prompt_len].eq(-100).all()
    assert first["labels"][prompt_len:].equal(first["input_ids"][prompt_len:])

    batch = next(iter(DataLoader(dataset, batch_size=2, collate_fn=lambda b: module.collate_sft(b, 0))))
    lengths = [len(dataset[i]["input_ids"]) for i in range(2)]
    assert batch["input_ids"].shape == (2, max(lengths))
    assert batch["input_ids"].dtype == torch.long
    assert batch["attention_mask"].sum(dim=1).tolist() == lengths
    short = lengths.index(min(lengths))
    assert batch["input_ids"][short, min(lengths) :].eq(0).all()
    assert batch["labels"][short, min(lengths) :].eq(-100).all()
