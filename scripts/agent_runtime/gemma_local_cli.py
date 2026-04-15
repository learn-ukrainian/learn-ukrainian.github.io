"""Tiny MLX-backed Gemma 4 stdin→stdout CLI for local smoke runs.

This is intentionally a non-production helper. It exists so pipeline/prompt
iterations can hit a cheap local model before burning Gemini quota.

Issue: #1284
"""
from __future__ import annotations

import argparse
import os
import sys


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local Gemma 4 chat completion from stdin.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get(
            "GEMMA_LOCAL_MODEL",
            "mlx-community/gemma-4-e4b-it-4bit",
        ),
        help="MLX model id to load",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.environ.get("GEMMA_LOCAL_MAX_TOKENS", "4096")),
        help="Maximum new tokens to generate",
    )
    parser.add_argument(
        "--temp",
        type=float,
        default=float(os.environ.get("GEMMA_LOCAL_TEMP", "1.0")),
        help="Sampling temperature",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=float(os.environ.get("GEMMA_LOCAL_TOP_P", "0.95")),
        help="Nucleus sampling cutoff",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=int(os.environ.get("GEMMA_LOCAL_TOP_K", "64")),
        help="Top-k sampling cutoff",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    prompt = sys.stdin.read()
    if not prompt.strip():
        print("gemma-local-cli: stdin prompt was empty", file=sys.stderr)
        return 2

    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load(args.model)
    messages = [
        {
            "role": "system",
            "content": (
                "Follow the user's instructions exactly. "
                "Return only the requested output text."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    chat_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    sampler = make_sampler(
        temp=args.temp,
        top_p=args.top_p,
        top_k=args.top_k,
    )
    output = generate(
        model,
        tokenizer,
        prompt=chat_prompt,
        max_tokens=args.max_tokens,
        sampler=sampler,
        verbose=False,
    )
    sys.stdout.write(output)
    if output and not output.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
