"""Wave 0: Literary RAG Embedding Quality Test.

Tests whether BGE-M3 can handle texts across language periods:
1. Old East Slavic (Слово о полку Ігоревім, XII c.)
2. Middle Ukrainian (Літопис Самовидця, XVII c.)
3. PVL parallel text (original OES + modern Ukrainian translation)

For each text, runs retrieval quality tests:
- Known quote search (exact phrase)
- Semantic search in modern Ukrainian
- Cross-work concept search

Usage:
    # Full test (scrape + ingest + query)
    .venv/bin/python scripts/rag/test_wave0.py

    # Skip scraping (if data already exists)
    .venv/bin/python scripts/rag/test_wave0.py --skip-scrape

    # Only run queries (data already ingested)
    .venv/bin/python scripts/rag/test_wave0.py --queries-only
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import LITERARY_COLLECTION, LITERARY_DIR, QDRANT_HOST, QDRANT_REST_PORT
from rag.ingest import create_literary_collection, ingest_literary_chunks

# ── Wave 0 test texts ────────────────────────────────────────────
WAVE0_TEXTS = [
    {
        "slug": "slovo-o-polku",
        "url": "http://litopys.org.ua/slovo/slovo.htm",
        "work": "Слово о полку Ігоревім",
        "author": "Невідомий",
        "year": 1187,
        "genre": "poetry",
        "period": "old_east_slavic",
        "parallel": False,
        "follow_next": False,
    },
    {
        "slug": "pvl-yaremenko",
        "url": "http://litopys.org.ua/pvlyar/yar01.htm",
        "work": "Повість временних літ (переклад Яременка)",
        "author": "Нестор",
        "year": 1113,
        "genre": "chronicle",
        "period": "old_east_slavic",
        "parallel": True,
        "follow_next": True,
        "max_pages": 5,  # Just first 5 pages for testing
    },
    {
        "slug": "samovydets",
        "url": "http://litopys.org.ua/samovyd/sam01.htm",
        "work": "Літопис Самовидця",
        "author": "Невідомий",
        "year": 1702,
        "genre": "chronicle",
        "period": "middle_ukrainian",
        "parallel": False,
        "follow_next": True,
        "max_pages": 5,  # Just first 5 pages for testing
    },
]

# ── Test queries ──────────────────────────────────────────────────
TEST_QUERIES = [
    # 1. Known phrases from Slovo (should match Slovo chunks)
    {
        "query": "О Руськая земле, уже за шеломянемъ еси",
        "description": "Famous lament from Slovo (exact OES phrase)",
        "expected_work": "Слово о полку Ігоревім",
        "type": "exact_phrase",
    },
    {
        "query": "затемнення сонця знак біди",
        "description": "Solar eclipse as omen (modern Ukrainian semantic query → should match Slovo)",
        "expected_work": "Слово о полку Ігоревім",
        "type": "semantic_modern",
    },
    {
        "query": "плач Ярославни",
        "description": "Yaroslavna's lament (modern Ukrainian concept → Slovo)",
        "expected_work": "Слово о полку Ігоревім",
        "type": "semantic_modern",
    },
    # 2. PVL queries (should match PVL parallel text)
    {
        "query": "хрещення Русі Володимир",
        "description": "Baptism of Rus by Volodymyr (modern UA → PVL)",
        "expected_work": "Повість временних літ",
        "type": "semantic_modern",
    },
    {
        "query": "помста княгині Ольги",
        "description": "Olga's revenge (modern UA concept → PVL)",
        "expected_work": "Повість временних літ",
        "type": "semantic_modern",
    },
    # 3. Samovydets queries (should match Cossack chronicle)
    {
        "query": "повстання Хмельницького козаки",
        "description": "Khmelnytsky uprising Cossacks (modern UA → Samovydets)",
        "expected_work": "Літопис Самовидця",
        "type": "semantic_modern",
    },
    {
        "query": "битва козаків з поляками",
        "description": "Cossack battle with Poles (modern UA → Samovydets)",
        "expected_work": "Літопис Самовидця",
        "type": "semantic_modern",
    },
    # 4. Cross-work queries
    {
        "query": "похід князя на ворогів",
        "description": "Prince's campaign against enemies (should match multiple works)",
        "expected_work": None,  # Any match is OK
        "type": "cross_work",
    },
]


def scrape_test_texts():
    """Scrape Wave 0 test texts."""
    from rag.scrape_litopys import save_chunks, scrape_work

    LITERARY_DIR.mkdir(parents=True, exist_ok=True)

    for text in WAVE0_TEXTS:
        output_path = LITERARY_DIR / f"wave0-{text['slug']}.jsonl"
        if output_path.exists():
            print(f"  [skip] {text['work']} already scraped")
            continue

        print(f"\n[wave0] Scraping: {text['work']}")
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
        save_chunks(chunks, output_path)


def run_quality_tests(client):
    """Run retrieval quality tests against the literary collection."""
    from rag.embed import TextEncoder

    encoder = TextEncoder()

    print("\n" + "=" * 70)
    print("WAVE 0 RETRIEVAL QUALITY TEST")
    print("=" * 70)

    results = []
    total_tests = 0
    passed_tests = 0

    for test in TEST_QUERIES:
        total_tests += 1
        print(f"\n{'─' * 60}")
        print(f"Query: {test['query']}")
        print(f"Type:  {test['type']}")
        print(f"Desc:  {test['description']}")
        if test["expected_work"]:
            print(f"Expected work: {test['expected_work']}")

        # Encode query
        emb = encoder.encode([test["query"]], batch_size=1)
        dense_vec = emb["dense_vecs"][0].tolist()
        sw = emb["lexical_weights"][0]
        if isinstance(sw, dict):
            list(
                int(k) if isinstance(k, (int, float)) else hash(k) % (2**31)
                for k in sw
            )
            list(sw.values())
        else:
            _sparse_indices, _sparse_values = [], []

        # Search with RRF (dense + sparse)

        # Dense search
        dense_results = client.query_points(
            collection_name=LITERARY_COLLECTION,
            query=dense_vec,
            using="dense",
            limit=3,
            with_payload=True,
        )

        # Display results
        for rank, point in enumerate(dense_results.points, 1):
            work = point.payload.get("work", "?")
            period = point.payload.get("language_period", "?")
            text_preview = point.payload.get("text", "")[:120].replace("\n", " ")
            score = point.score

            match_marker = ""
            if test["expected_work"] and test["expected_work"] in work:
                match_marker = " ✅"
            elif test["expected_work"] is None:
                match_marker = " ✅"  # Any match OK for cross-work

            print(f"  #{rank} [{score:.3f}] {work} ({period}){match_marker}")
            print(f"       {text_preview}...")

        # Check if expected work is in top-3
        if test["expected_work"]:
            top_works = [p.payload.get("work", "") for p in dense_results.points[:3]]
            hit = any(test["expected_work"] in w for w in top_works)
        else:
            hit = len(dense_results.points) > 0

        if hit:
            passed_tests += 1
            print("  → PASS")
        else:
            print("  → FAIL (expected work not in top-3)")

        results.append({
            "query": test["query"],
            "type": test["type"],
            "expected": test["expected_work"],
            "hit": hit,
            "top_score": dense_results.points[0].score if dense_results.points else 0,
            "top_work": dense_results.points[0].payload.get("work", "") if dense_results.points else "",
        })

    # Summary
    print(f"\n{'=' * 70}")
    print(f"RESULTS: {passed_tests}/{total_tests} passed ({100 * passed_tests / total_tests:.0f}%)")
    print(f"{'=' * 70}")

    for r in results:
        status = "✅" if r["hit"] else "❌"
        print(f"  {status} [{r['type']:16s}] {r['query'][:40]:40s} → {r['top_work'][:30]} ({r['top_score']:.3f})")

    # Verdict
    print(f"\n{'─' * 70}")
    if passed_tests == total_tests:
        print("VERDICT: BGE-M3 handles all language periods well. Proceed with full ingestion.")
    elif passed_tests / total_tests >= 0.7:
        print("VERDICT: BGE-M3 handles most queries. Medieval texts may need parallel translation approach.")
    else:
        print("VERDICT: BGE-M3 struggles with medieval texts. Consider alternative model or parallel-only approach.")
    print(f"{'─' * 70}")


def main():
    parser = argparse.ArgumentParser(description="Wave 0: Literary RAG embedding quality test")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip scraping (use existing data)")
    parser.add_argument("--queries-only", action="store_true", help="Only run queries (data already ingested)")
    parser.add_argument("--recreate", action="store_true", help="Recreate collection from scratch")
    args = parser.parse_args()

    from qdrant_client import QdrantClient
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_REST_PORT, prefer_grpc=False, timeout=300)

    if not args.queries_only:
        # Step 1: Scrape
        if not args.skip_scrape:
            print("\n[wave0] Step 1: Scraping test texts...")
            scrape_test_texts()

        # Step 2: Create collection
        print("\n[wave0] Step 2: Creating literary collection...")
        create_literary_collection(client, recreate=args.recreate)

        # Step 3: Ingest
        print("\n[wave0] Step 3: Ingesting chunks...")
        total = 0
        for jsonl_file in sorted(LITERARY_DIR.glob("wave0-*.jsonl")):
            total += ingest_literary_chunks(client, jsonl_file)
        print(f"\n[wave0] Total ingested: {total} chunks")

    # Step 4: Run quality tests
    print("\n[wave0] Step 4: Running retrieval quality tests...")
    run_quality_tests(client)


if __name__ == "__main__":
    main()
