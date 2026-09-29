# #9204 primary venv versus lock classification (2026-09-29)

Baseline: `uv pip sync --dry-run --python /home/ops/learn-ukrainian/.venv/bin/python requirements-lock.txt` in this dispatch worktree reported **140 installs and 98 removals**. The installed inventory had 187 distributions. The lock had 229 distinct requirements (228 named pins plus the local runtime), including three identical duplicate `pymorphy3` lines. The 238 actions are 93 absent locked distributions, 46 version replacements (92 actions), 51 installed-only distributions, and one local runtime reinstall (2 actions).

The lock began as a full `pip freeze` snapshot in commit `96c87c583e`; subsequent Git history updates individual pins. No `uv pip compile` or Makefile lock generator exists. CI installs the flat pins with `uv pip install --no-deps`, omitting Torch, TorchVision, OpenCLIP and Stanza wheels. This commit adds exact versions from the read-only primary-venv inventory and preserves every existing pin. `requirements.txt` and `requirements-dev.txt` already declared the five direct dependencies, so their source declarations needed no edits.

In four-component versions below, `·` stands for `.` so package versions cannot be mistaken for host addresses by the repository OPSEC check.

| Class | Baseline actions | Disposition |
| --- | ---: | --- |
| A: declared direct dependencies omitted from the lock | 5 removals | Added the five pins below. Source import evidence: `scripts/audit/checks/russicism_detection.py` uses `ahocorasick`; `scripts/typesafe/`, `scripts/atlas/`, `scripts/build/` use `typesafe_sdk`; IPython and ipdb are declared dev tools; pytest-mock is declared for tests. |
| C: IPython dependency closure omitted from the lock | 13 removals | Added the 13 pins below. |
| B: locked package absent from host | 93 installs | Host resync needed; no lock change. |
| B: declared direct pin differs on host | 30 actions (15 pairs) | Installed versions satisfy source ranges; keep existing lock pins, no upgrade. |
| C: transitive pin differs on host | 62 actions (31 pairs) | Keep existing lock pins, no unrelated upgrade. |
| B/C: other installed-only packages | 33 removals | Classified by root or dependency below. |
| C: local runtime path substitution | 2 actions | Same name/version (`learn-ukrainian-v4-runtime==1.0.0`), but `uv` compares the installed primary path with this worktree path; the checker compares distribution identity and reports no drift for it. |

## A — direct dependencies added to the lock (5)

- `ipdb==0.13.13`, `ipython==9.17.1`, `pyahocorasick==2.3.1`, `pytest-mock==3.15.1`, `typesafe-sdk==0.7.2`

## C — IPython transitive dependencies added to the lock (13)

- `asttokens==3.0.2`, `decorator==5.3.1`, `executing==2.2.1`, `ipython-pygments-lexers==1.1.1`, `jedi==0.20.0`, `matplotlib-inline==0.2.2`, `parso==0.8.7`, `pexpect==4.9.0`
- `prompt-toolkit==3.0.53`, `ptyprocess==0.7.0`, `pure-eval==0.2.3`, `stack-data==0.6.3`, `traitlets==5.16.1`

## B — lock pins absent from the primary venv (93)

- `accelerate==1.14.0`, `aiofiles==25.1.0`, `aiohappyeyeballs==2.6.2`, `aiohttp==3.14.3`, `aiosignal==1.4.0`, `anthropic==0.108.0`, `apscheduler==3.11.3`, `authlib==1.7.2`
- `bandit==1.9.4`, `blinker==1.9.0`, `build==1.5.0`, `cbor==1.0.0`, `chardet==7.6.0`, `coloredlogs==15.0.1`, `curl-cffi==0.15.0`, `datasets==5.0.1`
- `defusedxml==0.7.1`, `dill==0.4.1`, `distro==1.9.0`, `docstring-parser==0.18.0`, `ecdsa==0.19.2`, `einops==0.8.2`, `filetype==1.2.0`, `flagembedding==1.4.0`
- `flask==3.1.3`, `frozenlist==1.8.0`, `ftfy==6.3.1`, `google-auth==2.49.2`, `google-genai==1.65.0`, `httpx-sse==0.4.3`, `humanfriendly==10.0`, `inscriptis==2.7.3`
- `ipa-uk@git:e7fc944faca090ca985d5ca09a24c59154d9dea1`, `ir-datasets==0.6.3`, `itsdangerous==2.2.0`, `jaraco-classes==3.4.0`, `jaraco-context==6.1.2`, `jaraco-functools==4.4.0`, `jiter==0.16.0`, `joserfc==1.7.1`
- `keyring==25.7.0`, `lz4==4.4.5`, `mando==0.8.2`, `markdown2==2.5.5`, `markdownify==1.2.3`, `marker-pdf==1.10.2`, `mcp-memory-service==11.5.5`, `more-itertools==11.1.0`
- `multidict==6.7.1`, `multiprocess==0.70.19`, `open-clip-torch==3.3.0`, `openai==1.109.1`, `opencv-python-headless==4·13·0·92`, `pandas==3.0.1`, `pdftext==0.7.1`, `peft==0.20.0`
- `pillow==12.3.0`, `propcache==0.5.2`, `pyarrow==25.0.1`, `pycookiecheat==0.8.0`, `pydantic-settings==2.15.0`, `pymorphy2-dicts-uk==2.4.1.1.1460299261`, `pypdfium2==4.30.0`, `pyproject-hooks==1.2.0`
- `python-dateutil==2.9.0.post0`, `python-docx==1.2.0`, `python-dotenv==1.2.3`, `python-jose==3.5.0`, `radon==6.0.1`, `rsa==4.9.1`, `sentencepiece==0.2.1`, `six==1.17.0`
- `sniffio==1.3.1`, `sqlite-vec==0.1.9`, `stevedore==5.8.0`, `surya-ocr==0.22.0`, `timm==1.0.27`, `torchvision==0.28.0`, `trec-car-tools==2.6`, `typer-slim==0.24.0`
- `tzlocal==5.4.4`, `unlzw3==0.2.3`, `vulture==2.16`, `warc3-wet==0.2.5`, `warc3-wet-clueweb09==0.2.5`, `websockets==16.0`, `werkzeug==3.1.8`, `wheel==0.48.0`
- `xxhash==3.7.0`, `yamllint==1.38.0`, `yarl==1.25.1`, `youtube-transcript-api==1.2.4`, `zlib-state==0.1.12`

## B — direct dependency version drift (15 replacements)

- `coverage 7.16.0→7.15.4`, `fastapi 0.141.1→0.139.0`, `filelock 3.32.5→3.32.2`, `lxml 6.1.2→6.1.1`, `mcp 2.1.1→2.0.0`, `mypy 2.3.1→2.1.0`, `pre-commit 4.6.2→4.6.0`, `psycopg 3.3.5→3.3.4`
- `qdrant-client 1.19.0→1.17.0`, `rapidfuzz 3.14.6→3.14.5`, `regex 2026.9.3→2026.5.9`, `ruff 0.16.5→0.15.21`, `sentence-transformers 6.0.1→5.6.1`, `uvicorn 0.52.4→0.48.0`, `yt-dlp 2026.8.19→2026.7.4`

## C — transitive version drift (31 replacements)

- `anyio 4.14.2→4.15.1`, `certifi 2026.7.22→2026.6.17`, `charset-normalizer 3.5.1→3.4.4`, `click 8.5.0→8.4.2`, `cryptography 50.0.1→50.0.0`, `fsspec 2026.7.0→2026.1.0`, `greenlet 3.5.5→3.5.6`, `grpcio 1.83.1→1.82.1`
- `httpcore2 2.12.0→2.10.0`, `librt 0.15.0→0.13.0`, `mcp-types 2.1.1→2.0.0`, `mpmath 1.3.0→1.4.1`, `numpy 2.5.2→2.4.2`, `onnxruntime 1.29.0→1.24.3`, `platformdirs 4.11.7→4.11.11`, `playwright 1.62.0→1.59.0`
- `portalocker 3.2.0→4.4.0`, `protobuf 7.36.1→7.36.2`, `psycopg-binary 3.3.5→3.3.4`, `pyjwt 2.13.0→2.14.0`, `python-discovery 1.6.0→1.4.4`, `rpds-py 2026.6.3→0.30.0`, `scikit-learn 1.9.0→1.8.0`, `scipy 1.18.1→1.17.0`
- `stanza 1.14.0→1.13.0`, `starlette 1.6.0→1.3.1`, `tokenizers 0.23.1→0.22.2`, `tqdm 4.70.0→4.69.1`, `transformers 5.16.1→5.14.1`, `virtualenv 21.7.8→21.7.3`, `wcwidth 0.8.3→0.6.0`

## B — installed-only roots and host tools (9)

- `ast-serialize==0.8.0`, `cloudpickle==3.1.2`, `faster-whisper==1.2.1`, `hramatka==0.1.0`, `jiwer==4.0.0`, `msgspec==0.21.1`, `narwhals==2.25.0`, `pip==26.2.1`
- `torchaudio==2.11.0`

`hramatka` is an editable install pointing to a deleted sibling worktree and is not a dependency of this repository. `faster-whisper` and `torchaudio` are optional local ASR tooling; `scripts/navsi200_asr_bakeoff.py` imports `faster_whisper` and optionally `av`. Confirm that bakeoff is not running before removing these extras. `pip` is a host tool absent from the flat lock.

## C — attached host transitive packages

**Torch-required GPU dependencies (10):**

- `cuda-bindings==13.3.1`, `cuda-pathfinder==1.8.0`, `cuda-toolkit==13·0·3·0`, `nvidia-cublas==13·1·1·3`, `nvidia-cuda-nvrtc==13.0.88`, `nvidia-cudnn-cu13==9·20·0·48`, `nvidia-cusparselt-cu13==0.8.1`, `nvidia-nccl-cu13==2.29.7`
- `nvidia-nvshmem-cu13==3.4.5`, `triton==3.7.1`

**Hramatka dependencies (3):**

- `cbor2==5.9.0`, `pyopenssl==26.4.0`, `webauthn==2.8.0`

**faster-whisper dependencies (2):**

- `av==18.1.0`, `ctranslate2==4.8.2`

**Additional NVIDIA stack from the host (9):**

- `nvidia-cuda-cupti==13.0.85`, `nvidia-cuda-runtime==13.0.96`, `nvidia-cufft==12·0·0·61`, `nvidia-cufile==1·15·1·6`, `nvidia-curand==10·4·0·35`, `nvidia-cusolver==12·0·4·66`, `nvidia-cusparse==12·6·3·3`, `nvidia-nvjitlink==13.3.33`
- `nvidia-nvtx==13.0.85`

`triton==3.7.1` is an exact requirement in the installed `torch==2.13.0` metadata, alongside CUDA/NVIDIA packages. The flat lock omits these GPU packages because CI uses a CPU path. Removing the Torch-required ten can break the host Torch installation; the driver must stop before resync and decide on a host-specific GPU overlay or a CPU Torch replacement. `typesafe-sdk==0.7.2` is directly declared and imported here; its public-index resolution was verified with a no-cache `uv pip compile` probe. `webauthn==2.8.0` is required by the stale editable Hramatka install, with no repository import.

After the lock edit, the read-only dry run reports **140 installs, 80 removals**. The new distribution check reports `missing=93; extra=33; version=46` (the local runtime is recognized by name/version). Driver-owned residual: host resync, Torch/ASR safety decision, service health checks, and issue closeout after the branch lands.
