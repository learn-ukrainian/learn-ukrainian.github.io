"""RAG pipeline configuration — model paths, collection names, trust tiers."""

import sys
from pathlib import Path

# Add scripts/ to path if not already there
_scripts_dir = str(Path(__file__).resolve().parent.parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from config import (
    PROJECT_ROOT,
    SOURCES_DB,
)
from config import (
    TEXTBOOK_IMAGES_DIR as IMAGES_DIR,
)
from config import (
    VESUM_DB as VESUM_DB_PATH,
)

# ── Paths (backward compat) ───────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
TEXTBOOKS_DIR = DATA_DIR / "textbooks"
CHUNKS_DIR = DATA_DIR / "textbook_chunks"
LITERARY_DIR = DATA_DIR / "literary_texts"
VESUM_DIR = DATA_DIR / "vesum"

SOURCES_DB_PATH = SOURCES_DB

# ── Qdrant (DEPRECATED - use SQLite FTS5) ──────────────────────────
QDRANT_HOST = "localhost"
QDRANT_REST_PORT = 6333
QDRANT_GRPC_PORT = 6334

TEXT_COLLECTION = "textbook_chunks"
IMAGE_COLLECTION = "textbook_images"
LITERARY_COLLECTION = "literary_texts"

# Dictionary / reference collections
STYLE_GUIDE_COLLECTION = "style_guide"
PULS_CEFR_COLLECTION = "puls_cefr"
SUM11_COLLECTION = "sum11"
GRINCHENKO_COLLECTION = "grinchenko_dict"
FRAZEOLOHICHNYI_COLLECTION = "frazeolohichnyi"
BALLA_COLLECTION = "balla_en_uk"
UKRAJINET_COLLECTION = "ukrajinet"
DMKLINGER_COLLECTION = "dmklinger_uk_en"
WIKTIONARY_COLLECTION = "wiktionary_uk"

# ── VESUM ────────────────────────────────────────────────────────
VESUM_URL = "https://github.com/brown-uk/dict_uk/releases/download/v6.7.5/dict_corp_vis.txt.bz2"

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
MIN_CLEAN_CHAR_RATIO = 0.80

UKRAINIAN_CHARS = set(
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯабвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "ʼ'0123456789 \n\t.,;:!?-—–()\"«»…"
)

# ── Trust tiers ────────────────────────────────────────────────────
NUS_CUTOFF_YEAR = 2022


def get_trust_tier(pdf_stem: str) -> int:
    meta = parse_pdf_metadata_from_stem(pdf_stem)
    return 1 if meta["year"] >= NUS_CUTOFF_YEAR else 2


def parse_pdf_metadata_from_stem(stem: str) -> dict:
    parts = stem.split("-")
    grade = int(parts[0]) if parts[0].isdigit() else 0
    year = 0
    for p in parts:
        if len(p) == 4 and p.isdigit():
            year = int(p)
    return {"grade": grade, "year": year}


def parse_pdf_metadata(pdf_path: Path) -> dict:
    stem = pdf_path.stem
    parts = stem.split("-")
    grade = int(parts[0]) if parts[0].isdigit() else 0
    year = 0
    for p in parts:
        if len(p) == 4 and p.isdigit():
            year = int(p)
    author = ""
    for i, p in enumerate(parts):
        if len(p) == 4 and p.isdigit() and i > 0:
            author = parts[i - 1]
            break
    part = int(parts[-1]) if parts[-1].isdigit() else 1
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
