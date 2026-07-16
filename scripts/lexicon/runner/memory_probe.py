"""CLI: run the hard-cap memory self-test (and optional inject-OOM probe).

```bash
.venv/bin/python -m scripts.lexicon.runner.memory_probe
.venv/bin/python -m scripts.lexicon.runner.memory_probe --inject-oom
```
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from scripts.lexicon.runner.contracts import ErrorCode
from scripts.lexicon.runner.memory import (
    require_hard_cap_protection,
    run_startup_self_test,
)
from scripts.lexicon.runner.worker import run_capped_worker


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inject-oom",
        action="store_true",
        help="Also run an injected allocation breach under the proven limit",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=None,
        help="Override self-test ceiling (default: auto above current RSS)",
    )
    args = parser.parse_args(argv)

    proof = run_startup_self_test(test_max_bytes=args.max_bytes)
    print(f"SELF_TEST kind={proof.kind} enforced={proof.enforced} detail={proof.detail!r}")
    if not proof.enforced:
        print("HARD_CAP_CLAIM=refused")
        return 2
    require_hard_cap_protection(proof)
    print("HARD_CAP_CLAIM=allowed")

    if args.inject_oom:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_capped_worker(
                {
                    "job": "inject_oom",
                    "chunk_id": "oom-probe",
                    "memory_high_bytes": args.max_bytes,
                    "memory_max_bytes": args.max_bytes,
                },
                result_path=Path(tmp) / "oom_result.json",
                timeout_s=60.0,
            )
            print(
                f"INJECT_OOM outcome={result.outcome} error_code={result.error_code} "
                f"message={result.message!r}"
            )
            if result.error_code != ErrorCode.FAILED_OOM.value:
                return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
