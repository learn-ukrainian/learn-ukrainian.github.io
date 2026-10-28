"""Deterministic provider executable copied into disposable dispatcher repositories."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def build(spec, env):
    from scripts.dispatcher.types import Invocation

    return Invocation(
        [sys.executable, str(Path(__file__)), spec.model, str(spec.prompt_file), str(spec.final_file)],
        spec.prompt_file.read_bytes(),
        env,
        spec.final_file if spec.model == "file" else None,
    )


def parse(stdout, stderr, returncode, final_text):
    from scripts.dispatcher.types import ParsedResult

    return ParsedResult(
        final_text if final_text is not None else stdout.strip(),
        {"tokens": 7},
        "terminal error" if "PARSE_ERROR" in stdout else None,
        rate_limited="CAPACITY" in stdout,
    )


# The provider environment carries no pool override, so the run selects the pool its marker names.
GOVERNED_RUN = """import os, sys, time
from pathlib import Path
from scripts.common import test_slots
pool = Path(os.environ[test_slots.HOLDER_ENV].split(":", 2)[2]).parent.parent
hold = test_slots.join_inherited({**os.environ, test_slots.DIR_ENV: str(pool)}, wait_s=5)
Path(sys.argv[1]).write_text("joined" if hold is not None else "refused")
while not Path(sys.argv[2]).exists():
    time.sleep(0.02)
"""


def main():
    model, prompt, final = sys.argv[1:]
    prompt = Path(prompt)
    prompt.with_suffix(".started.tmp").write_text(str(os.getpid()))
    prompt.with_suffix(".started.tmp").replace(prompt.with_suffix(".started"))
    if model == "cancel":
        os.kill(os.getppid(), signal.SIGTERM)
        time.sleep(120)
    if model in {"blocked", "tree", "governed"}:
        if model == "tree":
            process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
            prompt.with_suffix(".grandchild.tmp").write_text(str(process.pid))
            prompt.with_suffix(".grandchild.tmp").replace(prompt.with_suffix(".grandchild"))
        if model == "governed":  # a governed test run of this turn, holding its slots until released
            signals = (str(prompt.with_suffix(suffix)) for suffix in (".joined", ".child-release"))
            process = subprocess.Popen([sys.executable, "-c", GOVERNED_RUN, *signals])
            prompt.with_suffix(".grandchild.tmp").write_text(str(process.pid))
            prompt.with_suffix(".grandchild.tmp").replace(prompt.with_suffix(".grandchild"))
        while not prompt.with_suffix(".release").exists():
            time.sleep(0.02)
    if model in {"pushed", "unpushed", "dirty", "pushed-dirty", "pushed-nested", "capacity-dirty"}:
        delivered = Path("src/delivered.txt" if model == "pushed-nested" else "delivered.txt")
        delivered.parent.mkdir(exist_ok=True)
        delivered.write_text("literal delivered value\n")
        if model not in {"dirty", "capacity-dirty"}:
            subprocess.run(["git", "add", str(delivered)], check=True, stdout=subprocess.DEVNULL, timeout=30)
            subprocess.run(["git", "commit", "-m", "stub delivery"], check=True, stdout=subprocess.DEVNULL, timeout=30)
        if model.startswith("pushed"):
            subprocess.run(["git", "push", "origin", "HEAD"], check=True, stdout=subprocess.DEVNULL, timeout=30)
        if model == "pushed-dirty":
            delivered.write_text("uncommitted delivery\n")
    if model == "crash":
        os.kill(os.getpid(), signal.SIGKILL)
    text = sys.stdin.buffer.read().decode()
    # Echo the user's request, after the dispatcher resource catalog a real model would consume.
    if text.startswith("Dispatcher-provided shared skills"):
        text = text.split("\n</dispatch-context>\n\n", 1)[1]
    if model in {"capacity", "capacity-dirty"}:
        print("CAPACITY")
        return 1
    if model == "file":
        Path(final).write_text(text)
    else:
        print("PARSE_ERROR" if model == "error" else ("" if model == "empty" else text))
    print("stub stderr", file=sys.stderr)
    return 17 if model == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
