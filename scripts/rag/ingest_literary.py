"""Full literary RAG ingestion — scrape, chunk, embed, and index all waves.

Waves:
    0: Test texts (Slovo, PVL parallel, Samovydets) — DONE
    1: OES chronicles & legal texts
    2: RUTH chronicles, grammars, lexicons
    3: RUTH vernacular literature & administrative docs
    4: Scholarly reference works
    5: LIT primary sources (modern Ukrainian literature)

Usage:
    # Ingest a specific wave
    .venv/bin/python scripts/rag/ingest_literary.py --wave 1

    # Ingest waves 1-3
    .venv/bin/python scripts/rag/ingest_literary.py --wave 1 2 3

    # Skip scraping (re-embed existing JSONL)
    .venv/bin/python scripts/rag/ingest_literary.py --wave 1 --skip-scrape

    # Recreate collection from scratch
    .venv/bin/python scripts/rag/ingest_literary.py --wave 1 --recreate

    # List all texts in a wave
    .venv/bin/python scripts/rag/ingest_literary.py --wave 2 --list

    # Scrape only (no embedding/ingestion)
    .venv/bin/python scripts/rag/ingest_literary.py --wave 1 --scrape-only
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import BGE_M3_DENSE_DIM, LITERARY_COLLECTION, LITERARY_DIR, QDRANT_HOST, QDRANT_REST_PORT

# ══════════════════════════════════════════════════════════════════════
# Wave definitions — all source texts organized by ingestion wave
# ══════════════════════════════════════════════════════════════════════

WAVE_1_OES = [
    # ── Chronicles ────────────────────────────────────────────────
    {
        "slug": "pvl-ipatskyi",
        "url": "http://litopys.org.ua/ipatlet/ipat01.htm",
        "work": "Повість временних літ (Іпатський список)",
        "author": "Нестор",
        "year": 1113,
        "genre": "chronicle",
        "period": "old_east_slavic",
        "parallel": False,
        "follow_next": True,
        "max_pages": 30,
    },
    {
        "slug": "pvl-lavrentiyivskyi",
        "url": "http://litopys.org.ua/lavrlet/lavr01.htm",
        "work": "Повість временних літ (Лаврентіївський список)",
        "author": "Нестор",
        "year": 1113,
        "genre": "chronicle",
        "period": "old_east_slavic",
        "parallel": False,
        "follow_next": True,
        "max_pages": 30,
    },
    {
        "slug": "kyivskyi-litopys",
        "url": "http://litopys.org.ua/litop/lit13.htm",
        "work": "Київський літопис",
        "author": "Невідомий",
        "year": 1198,
        "genre": "chronicle",
        "period": "old_east_slavic",
        "parallel": False,
        "follow_next": True,
        "max_pages": 30,
    },
    {
        "slug": "galytsko-volynskyi",
        "url": "http://litopys.org.ua/litop/lit22.htm",
        "work": "Галицько-Волинський літопис",
        "author": "Невідомий",
        "year": 1292,
        "genre": "chronicle",
        "period": "old_east_slavic",
        "parallel": False,
        "follow_next": True,
        "max_pages": 30,
    },
    {
        "slug": "galytsko-volynskyi-makhnovets",
        "url": "http://litopys.org.ua/oldukr/galvollet01.htm",
        "work": "Галицько-Волинський літопис (переклад Махновця)",
        "author": "Невідомий",
        "year": 1292,
        "genre": "chronicle",
        "period": "old_east_slavic",
        "parallel": False,
        "follow_next": True,
        "max_pages": 30,
    },
    # ── Legal texts ──────────────────────────────────────────────
    # Руська Правда is embedded within PVL editions
    # ── Literary art ─────────────────────────────────────────────
    {
        "slug": "slovo-poetic-translations",
        "url": "http://litopys.org.ua/slovo67/sl01.htm",
        "work": "Слово о полку Ігоревім (поетичні переклади)",
        "author": "Різні",
        "year": 1187,
        "genre": "poetry",
        "period": "old_east_slavic",
        "parallel": False,
        "follow_next": True,
        "max_pages": 40,
    },
    {
        "slug": "pateryk-pechersky",
        "url": "http://litopys.org.ua/paterikon/pater01.htm",
        "work": "Патерик Києво-Печерський",
        "author": "Невідомий",
        "year": 1462,
        "genre": "religious",
        "period": "old_east_slavic",
        "parallel": False,
        "follow_next": True,
        "max_pages": 50,
    },
    # ── Scholarly on OES ─────────────────────────────────────────
    {
        "slug": "peretz-slovo",
        "url": "http://litopys.org.ua/peretz/peretz01.htm",
        "work": "Перетц — Слово о полку Ігоревім (1926)",
        "author": "Перетц В.М.",
        "year": 1926,
        "genre": "scholarly",
        "period": "modern",
        "parallel": False,
        "follow_next": True,
        "max_pages": 30,
    },
]

WAVE_2_RUTH_CHRONICLES = [
    {
        "slug": "hrabianka",
        "url": "http://litopys.org.ua/grab/hrab01.htm",
        "work": "Літопис Грабянки",
        "author": "Грабянка Г.",
        "year": 1710,
        "genre": "chronicle",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 50,
    },
    {
        "slug": "velychko",
        "url": "http://litopys.org.ua/velichko/vel01.htm",
        "work": "Літопис Величка",
        "author": "Величко С.В.",
        "year": 1720,
        "genre": "chronicle",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 80,
    },
    {
        "slug": "chernihivskyi-litopys",
        "url": "http://litopys.org.ua/chernlet/chern01.htm",
        "work": "Чернігівський літопис (1587-1750)",
        "author": "Невідомий",
        "year": 1750,
        "genre": "chronicle",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 20,
    },
    {
        "slug": "istoriya-rusiv",
        "url": "http://litopys.org.ua/istrus/istrus01.htm",
        "work": "Історія Русів",
        "author": "Невідомий",
        "year": 1829,
        "genre": "chronicle",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 50,
    },
    # ── Grammars & Lexicons ──────────────────────────────────────
    {
        "slug": "smotrytsky-gramatyka",
        "url": "http://litopys.org.ua/smotrgram/sm01.htm",
        "work": "Смотрицький — Граматіки Словенскія (1619)",
        "author": "Смотрицький М.",
        "year": 1619,
        "genre": "grammar",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 30,
    },
    {
        "slug": "zyzaniy-leksys",
        "url": "http://litopys.org.ua/zyzlex/zyz01.htm",
        "work": "Зизаній — Лексис (1596)",
        "author": "Зизаній Л.",
        "year": 1596,
        "genre": "lexicon",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 20,
    },
    {
        "slug": "berynda-leksykon",
        "url": "http://litopys.org.ua/berlex/be01.htm",
        "work": "Беринда — Лексикон словенороський (1627)",
        "author": "Беринда П.",
        "year": 1627,
        "genre": "lexicon",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 60,
    },
    {
        "slug": "uzhevych-hramatyka",
        "url": "http://litopys.org.ua/uzhgram/uz01.htm",
        "work": "Ужевич — Граматика (1640-ві)",
        "author": "Ужевич І.",
        "year": 1643,
        "genre": "grammar",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 15,
    },
    {
        "slug": "fedorovych-bukvar",
        "url": "http://litopys.org.ua/fedorovych/bf01.htm",
        "work": "Федорович — Буквар (1574)",
        "author": "Федорович І.",
        "year": 1574,
        "genre": "grammar",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 10,
    },
]

WAVE_3_RUTH_VERNACULAR = [
    # ── Vernacular literature ────────────────────────────────────
    {
        "slug": "intermedii-xvii-xviii",
        "url": "http://litopys.org.ua/ukrinter/int01.htm",
        "work": "Українські інтермедії XVII-XVIII ст.",
        "author": "Різні",
        "year": 1700,
        "genre": "interlude",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 30,
    },
    {
        "slug": "poeziya-baroko",
        "url": "http://litopys.org.ua/ukrpoetry/anto01.htm",
        "work": "Українська поезія XVI-XVII ст.",
        "author": "Різні",
        "year": 1650,
        "genre": "poetry",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 30,
    },
    {
        "slug": "bajky-xvii-xviii",
        "url": "http://litopys.org.ua/bajky/bajk01.htm",
        "work": "Байки XVII-XVIII ст.",
        "author": "Різні",
        "year": 1700,
        "genre": "fable",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 20,
    },
    # ── Administrative / practical ───────────────────────────────
    {
        "slug": "hramoty-xiv",
        "url": "http://litopys.org.ua/gramxiv/grb01.htm",
        "work": "Грамоти XIV ст.",
        "author": "Різні",
        "year": 1350,
        "genre": "legal",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 20,
    },
    {
        "slug": "pysovnyk-lystuvannia",
        "url": "http://litopys.org.ua/rizne/hrinch01.htm",
        "work": "Старовинний письмовник",
        "author": "Невідомий",
        "year": 1750,
        "genre": "letter",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 15,
    },
    {
        "slug": "likarski-poradnyky",
        "url": "http://litopys.org.ua/porad/por01.htm",
        "work": "Лікарські порадники XVIII ст.",
        "author": "Невідомий",
        "year": 1750,
        "genre": "manual",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 15,
    },
]

WAVE_4_SCHOLARLY = [
    {
        "slug": "hrushevsky-istoriia",
        "url": "http://litopys.org.ua/hrushukr/hrushe01.htm",
        "work": "Грушевський — Історія української літератури",
        "author": "Грушевський М.",
        "year": 1923,
        "genre": "scholarly",
        "period": "modern",
        "parallel": False,
        "follow_next": True,
        "max_pages": 80,
    },
    {
        "slug": "chyzhevsky-istoriia-lit",
        "url": "http://litopys.org.ua/chyzh/chy01.htm",
        "work": "Чижевський — Історія української літератури",
        "author": "Чижевський Д.",
        "year": 1956,
        "genre": "scholarly",
        "period": "modern",
        "parallel": False,
        "follow_next": True,
        "max_pages": 60,
    },
    {
        "slug": "nimchuk-movoznavstvo",
        "url": "http://litopys.org.ua/nimchuk/nim01.htm",
        "work": "Німчук — Мовознавство на Україні XIV-XVII ст.",
        "author": "Німчук В.",
        "year": 1985,
        "genre": "scholarly",
        "period": "modern",
        "parallel": False,
        "follow_next": True,
        "max_pages": 40,
    },
    {
        "slug": "voitovych-dynasty",
        "url": "http://litopys.org.ua/dynasty/dyn01.htm",
        "work": "Войтович — Князівські династії Східної Європи",
        "author": "Войтович Л.",
        "year": 2000,
        "genre": "scholarly",
        "period": "modern",
        "parallel": False,
        "follow_next": True,
        "max_pages": 80,
    },
    {
        "slug": "ohloblyn-mazepa",
        "url": "http://litopys.org.ua/coss3/ohl01.htm",
        "work": "Оглоблін — Гетьман Мазепа та його доба",
        "author": "Оглоблін О.",
        "year": 1960,
        "genre": "scholarly",
        "period": "modern",
        "parallel": False,
        "follow_next": True,
        "max_pages": 40,
    },
    {
        "slug": "ukrainska-mova-encyclopedia",
        "url": "http://litopys.org.ua/ukrmova/um01.htm",
        "work": "Українська мова — Енциклопедія",
        "author": "Русанівський В.М. та ін.",
        "year": 2004,
        "genre": "scholarly",
        "period": "modern",
        "parallel": False,
        "follow_next": True,
        "max_pages": 100,
    },
]

WAVES = {
    0: ("Foundations (Slovo, PVL, Samovydets)", []),
    1: ("OES Chronicles & Legal", WAVE_1_OES),
    2: ("RUTH Chronicles, Grammars & Lexicons", WAVE_2_RUTH_CHRONICLES),
    3: ("RUTH Vernacular Literature & Admin Docs", WAVE_3_RUTH_VERNACULAR),
    4: ("Scholarly Reference Works", WAVE_4_SCHOLARLY),
    # Waves 5-10: scraped by batch_scrape_izbornyk.py, ingestion-only here
    5: ("Old Literature & Primary Sources", []),
    6: ("Chronicles & Diaries", []),
    7: ("History & Political Thought", []),
    8: ("Literary Studies", []),
    9: ("Linguistics & Grammars", []),
    10: ("Shevchenko", []),
}


def ensure_collection(client, recreate: bool = False):
    """Ensure the literary_texts collection exists."""
    from qdrant_client.models import (
        Distance,
        PayloadSchemaType,
        SparseIndexParams,
        SparseVectorParams,
        VectorParams,
    )

    exists = client.collection_exists(LITERARY_COLLECTION)
    if exists and not recreate:
        info = client.get_collection(LITERARY_COLLECTION)
        print(f"[ingest] Collection '{LITERARY_COLLECTION}' exists with {info.points_count} points")
        return
    if exists and recreate:
        print(f"[ingest] Recreating collection '{LITERARY_COLLECTION}'...")
        client.delete_collection(LITERARY_COLLECTION)

    print(f"[ingest] Creating collection '{LITERARY_COLLECTION}'...")
    client.create_collection(
        collection_name=LITERARY_COLLECTION,
        vectors_config={
            "dense": VectorParams(size=BGE_M3_DENSE_DIM, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False)),
        },
    )
    for field, schema_type in [
        ("work", PayloadSchemaType.KEYWORD),
        ("author", PayloadSchemaType.KEYWORD),
        ("year", PayloadSchemaType.INTEGER),
        ("genre", PayloadSchemaType.KEYWORD),
        ("language_period", PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=LITERARY_COLLECTION,
            field_name=field,
            field_schema=schema_type,
        )
    print("[ingest] Collection created with indexes.")


def scrape_wave(wave_num: int, texts: list[dict]):
    """Scrape all texts in a wave, saving JSONL files."""
    from rag.scrape_litopys import save_chunks, scrape_work

    LITERARY_DIR.mkdir(parents=True, exist_ok=True)
    total_chunks = 0

    for text in texts:
        output_path = LITERARY_DIR / f"wave{wave_num}-{text['slug']}.jsonl"
        if output_path.exists():
            with open(output_path) as f:
                existing = sum(1 for _ in f)
            print(f"  [skip] {text['work']} — already scraped ({existing} chunks)")
            total_chunks += existing
            continue

        print(f"\n[wave{wave_num}] Scraping: {text['work']}")
        try:
            chunks = scrape_work(
                url=text["url"],
                work=text["work"],
                author=text["author"],
                year=text["year"],
                genre=text["genre"],
                period=text["period"],
                parallel=text.get("parallel", False),
                follow_next=text.get("follow_next", False),
                max_pages=text.get("max_pages", 100),
            )
            if chunks:
                save_chunks(chunks, output_path)
                total_chunks += len(chunks)
            else:
                print(f"  [warn] No chunks generated for {text['work']}")
        except Exception as e:
            print(f"  [ERROR] Failed to scrape {text['work']}: {e}")

    print(f"\n[wave{wave_num}] Total scraped: {total_chunks} chunks")
    return total_chunks


def ingest_wave(client, wave_num: int, batch_size: int = 32):
    """Ingest all JSONL files for a wave into Qdrant."""
    from qdrant_client.models import PointStruct, SparseVector

    from rag.embed import TextEncoder

    pattern = f"wave{wave_num}-*.jsonl"
    jsonl_files = sorted(LITERARY_DIR.glob(pattern))
    if not jsonl_files:
        print(f"[wave{wave_num}] No JSONL files found matching {pattern}")
        return 0

    encoder = TextEncoder()
    total_ingested = 0

    for jsonl_path in jsonl_files:
        print(f"\n[wave{wave_num}] Ingesting {jsonl_path.name}...")

        chunks = []
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))

        if not chunks:
            print("  No chunks found.")
            continue

        # Embed in batches
        texts = [c["text"] for c in chunks]
        embeddings = encoder.encode(texts, batch_size=batch_size)
        dense_vecs = embeddings["dense_vecs"]
        sparse_weights = embeddings["lexical_weights"]

        points = []
        for i, chunk in enumerate(chunks):
            sw = sparse_weights[i]
            if isinstance(sw, dict):
                # Deduplicate indices (hash collisions can create duplicates)
                idx_map: dict[int, float] = {}
                for k, v in sw.items():
                    idx = int(k) if isinstance(k, (int, float)) else hash(k) % (2**31)
                    idx_map[idx] = idx_map.get(idx, 0.0) + v
                indices = list(idx_map.keys())
                values = list(idx_map.values())
            else:
                indices, values = [], []

            payload = {
                "text": chunk["text"],
                "chunk_id": chunk["chunk_id"],
                "work": chunk.get("work", ""),
                "author": chunk.get("author", ""),
                "year": chunk.get("year", 0),
                "genre": chunk.get("genre", ""),
                "language_period": chunk.get("language_period", ""),
                "source_url": chunk.get("source_url", ""),
                "token_count": chunk.get("token_count", 0),
            }
            if "original_text" in chunk:
                payload["original_text"] = chunk["original_text"]

            point = PointStruct(
                id=int(hashlib.sha256(chunk["chunk_id"].encode()).hexdigest()[:15], 16),
                vector={
                    "dense": dense_vecs[i].tolist(),
                    "sparse": SparseVector(indices=indices, values=values),
                },
                payload=payload,
            )
            points.append(point)

        # Upsert in batches (with retry for stale connections after long embedding)
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            for attempt in range(3):
                try:
                    client.upsert(collection_name=LITERARY_COLLECTION, points=batch)
                    break
                except Exception as e:
                    if attempt < 2 and ("408" in str(e) or "timeout" in str(e).lower()):
                        print(f"  [retry] Upsert timeout, attempt {attempt + 2}/3...")
                        time.sleep(2)
                    else:
                        raise

        print(f"  Ingested {len(points)} chunks from {jsonl_path.name}")
        total_ingested += len(points)

    print(f"\n[wave{wave_num}] Total ingested: {total_ingested} chunks")
    return total_ingested


def list_wave(wave_num: int, texts: list[dict]):
    """List all texts in a wave."""
    print(f"\nWave {wave_num}: {len(texts)} texts")
    print(f"{'─' * 70}")
    for text in texts:
        jsonl = LITERARY_DIR / f"wave{wave_num}-{text['slug']}.jsonl"
        status = "✅ scraped" if jsonl.exists() else "⬜ pending"
        print(f"  {status}  {text['work']}")
        print(f"          {text['genre']} | {text['period']} | {text['year']}")
        print(f"          {text['url']}")


def main():
    parser = argparse.ArgumentParser(description="Literary RAG ingestion")
    parser.add_argument("--wave", type=int, nargs="+", required=True,
                       help="Wave number(s) to process (1-10)")
    parser.add_argument("--skip-scrape", action="store_true",
                       help="Skip scraping (use existing JSONL)")
    parser.add_argument("--scrape-only", action="store_true",
                       help="Only scrape, don't embed/ingest")
    parser.add_argument("--recreate", action="store_true",
                       help="Recreate Qdrant collection from scratch")
    parser.add_argument("--list", action="store_true",
                       help="List texts in wave(s) without processing")
    parser.add_argument("--batch-size", type=int, default=32,
                       help="Embedding batch size (default 32)")
    args = parser.parse_args()

    for wave_num in args.wave:
        if wave_num not in WAVES:
            print(f"[error] Unknown wave: {wave_num}. Valid: {list(WAVES.keys())}")
            sys.exit(1)

    # List mode
    if args.list:
        for wave_num in args.wave:
            name, texts = WAVES[wave_num]
            list_wave(wave_num, texts)
        return

    # Connect to Qdrant (unless scrape-only)
    client = None
    if not args.scrape_only:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_REST_PORT,
                             prefer_grpc=False, timeout=300)
        ensure_collection(client, recreate=args.recreate)

    # Process each wave
    for wave_num in args.wave:
        name, texts = WAVES[wave_num]
        print(f"\n{'=' * 70}")
        print(f"WAVE {wave_num}: {name} ({len(texts)} texts)")
        print(f"{'=' * 70}")

        # Step 1: Scrape
        if not args.skip_scrape:
            print(f"\n[wave{wave_num}] Step 1: Scraping...")
            scrape_wave(wave_num, texts)

        if args.scrape_only:
            continue

        # Step 2: Ingest
        print(f"\n[wave{wave_num}] Step 2: Embedding & ingesting...")
        ingest_wave(client, wave_num, batch_size=args.batch_size)

        # Step 3: Verify
        info = client.get_collection(LITERARY_COLLECTION)
        print(f"\n[wave{wave_num}] Collection now has {info.points_count} points total")

    # Final stats
    if client:
        info = client.get_collection(LITERARY_COLLECTION)
        print(f"\n{'=' * 70}")
        print(f"DONE. literary_texts: {info.points_count} points, status: {info.status}")
        print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
