"""RAG pipeline configuration — model paths, collection names, trust tiers.

NOTE (Colima): If using Colima with VZ framework, port forwarding may not work
automatically. Set up an SSH tunnel before using Qdrant:

    ssh -i ~/.colima/_lima/_config/user -o StrictHostKeyChecking=no \\
        -p $(colima ssh-config 2>/dev/null | grep Port | awk '{print $2}') \\
        -N -L 6333:localhost:6333 -L 6334:localhost:6334 \\
        $(whoami)@127.0.0.1 &
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
TEXTBOOKS_DIR = DATA_DIR / "textbooks"
IMAGES_DIR = DATA_DIR / "textbook_images"
CHUNKS_DIR = DATA_DIR / "textbook_chunks"

# ── Qdrant ─────────────────────────────────────────────────────────
QDRANT_HOST = "localhost"
QDRANT_REST_PORT = 6333
QDRANT_GRPC_PORT = 6334

TEXT_COLLECTION = "textbook_chunks"
IMAGE_COLLECTION = "textbook_images"

# ── Embedding models ───────────────────────────────────────────────
BGE_M3_MODEL = "BAAI/bge-m3"
BGE_M3_DENSE_DIM = 1024

SIGLIP_MODEL = "ViT-SO400M-14-SigLIP2"
SIGLIP_PRETRAINED = "webli"
SIGLIP_DIM = 1152

# ── Chunking ───────────────────────────────────────────────────────
CHUNK_MIN_TOKENS = 128
CHUNK_MAX_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 64

# Min image dimensions (skip tiny icons/decorations)
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100

# ── Quality gate ───────────────────────────────────────────────────
# Chunks with < this ratio of Ukrainian/Latin chars are flagged as garbled
MIN_CLEAN_CHAR_RATIO = 0.80

# Ukrainian Cyrillic character ranges (А-Я, а-я, Ґ, ґ, Є, є, І, і, Ї, ї)
UKRAINIAN_CHARS = set(
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯабвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "ʼ'0123456789 \n\t.,;:!?-—–()\"«»…"
)

# ── Trust tiers ────────────────────────────────────────────────────
# Tier 1: NUS 2022+ editions (latest State Standard aligned)
# Tier 2: 2017–2021 editions (older curriculum)
NUS_CUTOFF_YEAR = 2022


def get_trust_tier(pdf_stem: str) -> int:
    """Return trust tier based on publication year.

    Tier 1: 2022+ (NUS aligned)
    Tier 2: pre-2022 (older curriculum)
    """
    meta = parse_pdf_metadata_from_stem(pdf_stem)
    return 1 if meta["year"] >= NUS_CUTOFF_YEAR else 2


def parse_pdf_metadata_from_stem(stem: str) -> dict:
    """Lightweight metadata extraction from just the stem string."""
    parts = stem.split("-")
    grade = int(parts[0]) if parts[0].isdigit() else 0
    year = 0
    for p in parts:
        if len(p) == 4 and p.isdigit():
            year = int(p)
    return {"grade": grade, "year": year}


def parse_pdf_metadata(pdf_path: Path) -> dict:
    """Extract grade, author, year from filename convention.

    Convention: {grade}-klas-{subject}-{author}-{year}-{part}.pdf
    Example:    3-klas-ukrainska-mova-vashulenko-2020-1.pdf
    """
    stem = pdf_path.stem
    parts = stem.split("-")

    grade = int(parts[0]) if parts[0].isdigit() else 0

    # Find year (4-digit number that's not grade)
    year = 0
    for p in parts:
        if len(p) == 4 and p.isdigit():
            year = int(p)

    # Author is the part before the year
    author = ""
    for i, p in enumerate(parts):
        if len(p) == 4 and p.isdigit() and i > 0:
            author = parts[i - 1]
            break

    # Part number (last element if digit)
    part = int(parts[-1]) if parts[-1].isdigit() else 1

    # Subject: everything between "klas" and author
    subject_parts = []
    in_subject = False
    for p in parts:
        if p == "klas":
            in_subject = True
            continue
        if p == author:
            break
        if in_subject:
            subject_parts.append(p)
    subject = "-".join(subject_parts) if subject_parts else "ukrainska-mova"

    return {
        "grade": grade,
        "author": author,
        "year": year,
        "part": part,
        "subject": subject,
        "trust_tier": get_trust_tier(stem),
        "pdf_stem": stem,
    }
