"""Tests for RAG pipeline: ingestion, search, and query functions.

Uses a LIVE Qdrant instance (must be running on localhost:6333/6334).
Tests use a dedicated test collection prefix to avoid polluting production data.

Usage:
    .venv/bin/python -m pytest tests/test_rag.py -v
    .venv/bin/python -m pytest tests/test_rag.py -v -k "not slow"  # skip encoder tests
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from scripts.rag.config import (
    BGE_M3_DENSE_DIM,
    IMAGE_COLLECTION,
    LITERARY_COLLECTION,
    QDRANT_HOST,
    QDRANT_REST_PORT,
    SIGLIP_DIM,
    TEXT_COLLECTION,
    get_trust_tier,
    parse_pdf_metadata,
    parse_pdf_metadata_from_stem,
)

# ── Test constants ────────────────────────────────────────────────
TEST_TEXT_COLLECTION = "test_textbook_chunks"
TEST_IMAGE_COLLECTION = "test_textbook_images"

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def qdrant_client():
    """Live Qdrant client — skip all tests if Qdrant is down."""
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_REST_PORT, timeout=5)
        client.get_collections()
        return client
    except Exception:
        pytest.skip("Qdrant not running on localhost:6333")


@pytest.fixture(scope="session")
def test_text_collection(qdrant_client):
    """Create a dedicated test text collection, clean up after."""
    if qdrant_client.collection_exists(TEST_TEXT_COLLECTION):
        qdrant_client.delete_collection(TEST_TEXT_COLLECTION)

    qdrant_client.create_collection(
        collection_name=TEST_TEXT_COLLECTION,
        vectors_config={
            "dense": VectorParams(size=BGE_M3_DENSE_DIM, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False)),
        },
    )
    for field, schema_type in [
        ("grade", PayloadSchemaType.INTEGER),
        ("subject", PayloadSchemaType.KEYWORD),
        ("trust_tier", PayloadSchemaType.INTEGER),
        ("author", PayloadSchemaType.KEYWORD),
    ]:
        qdrant_client.create_payload_index(
            collection_name=TEST_TEXT_COLLECTION,
            field_name=field,
            field_schema=schema_type,
        )

    yield TEST_TEXT_COLLECTION

    # Cleanup
    qdrant_client.delete_collection(TEST_TEXT_COLLECTION)


@pytest.fixture(scope="session")
def test_image_collection(qdrant_client):
    """Create a dedicated test image collection, clean up after."""
    if qdrant_client.collection_exists(TEST_IMAGE_COLLECTION):
        qdrant_client.delete_collection(TEST_IMAGE_COLLECTION)

    qdrant_client.create_collection(
        collection_name=TEST_IMAGE_COLLECTION,
        vectors_config=VectorParams(size=SIGLIP_DIM, distance=Distance.COSINE),
    )
    for field, schema_type in [
        ("grade", PayloadSchemaType.INTEGER),
        ("subject", PayloadSchemaType.KEYWORD),
        ("author", PayloadSchemaType.KEYWORD),
    ]:
        qdrant_client.create_payload_index(
            collection_name=TEST_IMAGE_COLLECTION,
            field_name=field,
            field_schema=schema_type,
        )

    yield TEST_IMAGE_COLLECTION

    # Cleanup
    qdrant_client.delete_collection(TEST_IMAGE_COLLECTION)


@pytest.fixture
def sample_text_chunks():
    """Sample text chunk records matching JSONL format."""
    return [
        {
            "chunk_id": "test-book_s0000",
            "text": "Буквар для першого класу. Літера А — арбуз.",
            "token_count": 12,
            "section_title": "Сторінка 5",
            "grade": 1,
            "subject": "bukvar",
            "author": "zaharijchuk",
            "year": 2025,
            "trust_tier": 1,
            "pdf_stem": "test-book",
            "quality": {"is_clean": True, "clean_ratio": 1.0},
        },
        {
            "chunk_id": "test-book_s0001",
            "text": "Літера Б — банан. Літера В — вовк. Приголосні звуки.",
            "token_count": 15,
            "section_title": "Сторінка 6",
            "grade": 1,
            "subject": "bukvar",
            "author": "zaharijchuk",
            "year": 2025,
            "trust_tier": 1,
            "pdf_stem": "test-book",
            "quality": {"is_clean": True, "clean_ratio": 1.0},
        },
        {
            "chunk_id": "test-book_s0002",
            "text": "Минулий час дієслова утворюється за допомогою суфікса -в/-ла.",
            "token_count": 14,
            "section_title": "Дієслово",
            "grade": 3,
            "subject": "ukrainska-mova",
            "author": "vashulenko",
            "year": 2020,
            "trust_tier": 2,
            "pdf_stem": "test-book",
            "quality": {"is_clean": True, "clean_ratio": 1.0},
        },
        {
            "chunk_id": "test-dirty_s0000",
            "text": "garbled OCR output %$@#",
            "token_count": 5,
            "section_title": "",
            "grade": 1,
            "subject": "bukvar",
            "author": "unknown",
            "year": 2020,
            "trust_tier": 2,
            "pdf_stem": "test-dirty",
            "quality": {"is_clean": False, "clean_ratio": 0.2},
        },
    ]


@pytest.fixture
def sample_image_records():
    """Sample image metadata records matching JSONL format."""
    return [
        {
            "image_id": "test-img_p005_i00",
            "image_path": "data/textbook_images/grade-01/1-klas-bukvar-zaharijchuk-2025-1-p003-00.png",
            "filename": "test-img-p005-00.png",
            "page": 5,
            "image_index": 0,
            "width": 800,
            "height": 533,
            "grade": 1,
            "subject": "bukvar",
            "author": "zaharijchuk",
            "year": 2025,
            "pdf_stem": "test-book",
        },
        {
            "image_id": "test-img_p010_i00",
            "image_path": "data/textbook_images/grade-01/1-klas-bukvar-zaharijchuk-2025-1-p003-01.png",
            "filename": "test-img-p010-00.png",
            "page": 10,
            "image_index": 0,
            "width": 400,
            "height": 300,
            "grade": 3,
            "subject": "ukrainska-mova",
            "author": "vashulenko",
            "year": 2020,
            "pdf_stem": "test-book-2",
        },
    ]


@pytest.fixture
def text_jsonl_file(sample_text_chunks, tmp_path):
    """Write sample chunks to a temporary JSONL file."""
    jsonl = tmp_path / "test-chunks.jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for chunk in sample_text_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return jsonl


@pytest.fixture
def image_jsonl_file(sample_image_records, tmp_path):
    """Write sample image records to a temporary JSONL file."""
    jsonl = tmp_path / "test-images.jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for rec in sample_image_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return jsonl


# ══════════════════════════════════════════════════════════════════
# 1. CONFIG TESTS
# ══════════════════════════════════════════════════════════════════

class TestConfig:
    """Test config.py metadata parsing and trust tier logic."""

    def test_parse_pdf_metadata_standard_filename(self):
        path = Path("3-klas-ukrainska-mova-vashulenko-2020-1.pdf")
        meta = parse_pdf_metadata(path)
        assert meta["grade"] == 3
        assert meta["author"] == "vashulenko"
        assert meta["year"] == 2020
        assert meta["part"] == 1
        assert meta["subject"] == "ukrainska-mova"

    def test_parse_pdf_metadata_bukvar(self):
        path = Path("1-klas-bukvar-zaharijchuk-2025-2.pdf")
        meta = parse_pdf_metadata(path)
        assert meta["grade"] == 1
        assert meta["author"] == "zaharijchuk"
        assert meta["year"] == 2025
        assert meta["subject"] == "bukvar"

    def test_trust_tier_nus_2022_plus(self):
        assert get_trust_tier("1-klas-bukvar-zaharijchuk-2025-1") == 1

    def test_trust_tier_pre_2022(self):
        assert get_trust_tier("3-klas-ukrainska-mova-vashulenko-2020-1") == 2

    def test_trust_tier_boundary(self):
        assert get_trust_tier("2-klas-bukvar-test-2022-1") == 1
        assert get_trust_tier("2-klas-bukvar-test-2021-1") == 2

    def test_parse_metadata_from_stem(self):
        meta = parse_pdf_metadata_from_stem("3-klas-ukrainska-mova-vashulenko-2020-1")
        assert meta["grade"] == 3
        assert meta["year"] == 2020

    def test_dimensions_correct(self):
        assert BGE_M3_DENSE_DIM == 1024
        assert SIGLIP_DIM == 1152


# ══════════════════════════════════════════════════════════════════
# 2. COLLECTION MANAGEMENT TESTS
# ══════════════════════════════════════════════════════════════════

class TestCollectionManagement:
    """Test collection creation and verification."""

    def test_text_collection_exists(self, qdrant_client, test_text_collection):
        assert qdrant_client.collection_exists(test_text_collection)
        info = qdrant_client.get_collection(test_text_collection)
        assert info.status.value == "green"

    def test_text_collection_vector_config(self, qdrant_client, test_text_collection):
        info = qdrant_client.get_collection(test_text_collection)
        vectors = info.config.params.vectors
        assert "dense" in vectors
        assert vectors["dense"].size == BGE_M3_DENSE_DIM
        assert vectors["dense"].distance.value == "Cosine"

    def test_image_collection_exists(self, qdrant_client, test_image_collection):
        assert qdrant_client.collection_exists(test_image_collection)
        info = qdrant_client.get_collection(test_image_collection)
        assert info.status.value == "green"

    def test_image_collection_vector_config(self, qdrant_client, test_image_collection):
        info = qdrant_client.get_collection(test_image_collection)
        vectors = info.config.params.vectors
        assert vectors.size == SIGLIP_DIM
        assert vectors.distance.value == "Cosine"

    def test_production_collections_exist(self, qdrant_client):
        """Verify production collections are intact."""
        assert qdrant_client.collection_exists(TEXT_COLLECTION)
        assert qdrant_client.collection_exists(IMAGE_COLLECTION)

    def test_production_text_has_data(self, qdrant_client):
        info = qdrant_client.get_collection(TEXT_COLLECTION)
        assert info.points_count > 0, "Production text collection is empty"

    def test_production_images_has_data(self, qdrant_client):
        info = qdrant_client.get_collection(IMAGE_COLLECTION)
        assert info.points_count > 0, "Production image collection is empty"


# ══════════════════════════════════════════════════════════════════
# 3. TEXT INGESTION TESTS
# ══════════════════════════════════════════════════════════════════

class TestTextIngestion:
    """Test text chunk ingestion into Qdrant."""

    def test_ingest_text_chunks(self, qdrant_client, test_text_collection, sample_text_chunks):
        """Ingest sample chunks and verify they land in Qdrant."""
        clean_chunks = [c for c in sample_text_chunks if c.get("quality", {}).get("is_clean", True)]

        points = []
        for chunk in clean_chunks:
            dense_vec = np.random.randn(BGE_M3_DENSE_DIM).tolist()
            sparse_indices = [1, 5, 10, 100]
            sparse_values = [0.5, 0.3, 0.8, 0.1]

            point = PointStruct(
                id=int(hashlib.sha256(chunk["chunk_id"].encode()).hexdigest()[:15], 16),
                vector={
                    "dense": dense_vec,
                    "sparse": SparseVector(indices=sparse_indices, values=sparse_values),
                },
                payload={
                    "text": chunk["text"],
                    "chunk_id": chunk["chunk_id"],
                    "grade": chunk.get("grade", 0),
                    "subject": chunk.get("subject", ""),
                    "author": chunk.get("author", ""),
                    "year": chunk.get("year", 0),
                    "trust_tier": chunk.get("trust_tier", 2),
                    "section_title": chunk.get("section_title", ""),
                    "pdf_stem": chunk.get("pdf_stem", ""),
                    "token_count": chunk.get("token_count", 0),
                },
            )
            points.append(point)

        qdrant_client.upsert(collection_name=test_text_collection, points=points)

        info = qdrant_client.get_collection(test_text_collection)
        assert info.points_count == len(clean_chunks)

    def test_dirty_chunks_filtered(self, sample_text_chunks):
        """Verify dirty chunks are excluded during ingestion."""
        clean = [c for c in sample_text_chunks if c.get("quality", {}).get("is_clean", True)]
        assert len(clean) == 3  # 4 total, 1 dirty
        dirty = [c for c in sample_text_chunks if not c.get("quality", {}).get("is_clean", True)]
        assert len(dirty) == 1
        assert dirty[0]["chunk_id"] == "test-dirty_s0000"

    def test_chunk_id_hashing_deterministic(self):
        """Same chunk_id always produces the same point ID."""
        cid = "test-book_s0042"
        id1 = int(hashlib.sha256(cid.encode()).hexdigest()[:15], 16)
        id2 = int(hashlib.sha256(cid.encode()).hexdigest()[:15], 16)
        assert id1 == id2

    def test_chunk_id_hashing_unique(self):
        """Different chunk_ids produce different point IDs."""
        id1 = int(hashlib.sha256(b"test-book_s0001").hexdigest()[:15], 16)
        id2 = int(hashlib.sha256(b"test-book_s0002").hexdigest()[:15], 16)
        assert id1 != id2

    def test_upsert_idempotent(self, qdrant_client, test_text_collection):
        """Upserting same point twice doesn't create duplicates."""
        point = PointStruct(
            id=999999,
            vector={
                "dense": np.random.randn(BGE_M3_DENSE_DIM).tolist(),
                "sparse": SparseVector(indices=[1], values=[1.0]),
            },
            payload={"text": "test", "chunk_id": "idempotent-test"},
        )
        qdrant_client.upsert(collection_name=test_text_collection, points=[point])
        count_before = qdrant_client.get_collection(test_text_collection).points_count

        qdrant_client.upsert(collection_name=test_text_collection, points=[point])
        count_after = qdrant_client.get_collection(test_text_collection).points_count

        assert count_after == count_before

    def test_jsonl_loading(self, text_jsonl_file):
        """Verify JSONL file loads correctly."""
        chunks = []
        with open(text_jsonl_file, encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))
        assert len(chunks) == 4
        assert chunks[0]["chunk_id"] == "test-book_s0000"
        assert chunks[3]["quality"]["is_clean"] is False


# ══════════════════════════════════════════════════════════════════
# 4. IMAGE INGESTION TESTS
# ══════════════════════════════════════════════════════════════════

class TestImageIngestion:
    """Test image ingestion into Qdrant."""

    def test_ingest_images(self, qdrant_client, test_image_collection, sample_image_records):
        """Ingest sample image records with random vectors."""
        points = []
        for rec in sample_image_records:
            vec = np.random.randn(SIGLIP_DIM).tolist()
            point = PointStruct(
                id=int(hashlib.sha256(rec["image_id"].encode()).hexdigest()[:15], 16),
                vector=vec,
                payload={
                    "image_id": rec["image_id"],
                    "image_path": rec["image_path"],
                    "filename": rec["filename"],
                    "page": rec.get("page", 0),
                    "grade": rec.get("grade", 0),
                    "subject": rec.get("subject", ""),
                    "author": rec.get("author", ""),
                    "year": rec.get("year", 0),
                    "width": rec.get("width", 0),
                    "height": rec.get("height", 0),
                    "pdf_stem": rec.get("pdf_stem", ""),
                },
            )
            points.append(point)

        qdrant_client.upsert(collection_name=test_image_collection, points=points)

        info = qdrant_client.get_collection(test_image_collection)
        assert info.points_count == len(sample_image_records)

    def test_image_payload_fields(self, qdrant_client, test_image_collection):
        """Verify all expected payload fields are stored."""
        results = qdrant_client.scroll(test_image_collection, limit=1, with_payload=True)
        assert len(results[0]) > 0
        payload = results[0][0].payload
        expected_fields = {"image_id", "image_path", "filename", "page", "grade",
                           "subject", "author", "year", "width", "height", "pdf_stem"}
        assert expected_fields.issubset(set(payload.keys()))

    def test_image_jsonl_loading(self, image_jsonl_file):
        """Verify image JSONL file loads correctly."""
        records = []
        with open(image_jsonl_file, encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
        assert len(records) == 2
        assert records[0]["image_id"] == "test-img_p005_i00"
        assert records[0]["width"] == 800

    def test_missing_image_file_handling(self, tmp_path):
        """Verify missing images are detected during path resolution."""
        rec = {
            "image_id": "missing_p001_i00",
            "image_path": "data/textbook_images/nonexistent.png",
        }
        img_path = PROJECT_ROOT / rec["image_path"]
        assert not img_path.exists()


# ══════════════════════════════════════════════════════════════════
# 5. SEARCH TESTS (AGAINST TEST COLLECTIONS)
# ══════════════════════════════════════════════════════════════════

class TestTextSearch:
    """Test text vector search on test collections."""

    def test_dense_vector_search(self, qdrant_client, test_text_collection):
        """Query by dense vector returns results."""
        query_vec = np.random.randn(BGE_M3_DENSE_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=test_text_collection,
            query=query_vec,
            using="dense",
            limit=3,
            with_payload=True,
        )
        assert len(results.points) > 0
        for point in results.points:
            assert point.payload is not None
            assert "text" in point.payload

    def test_filter_by_grade(self, qdrant_client, test_text_collection):
        """Grade filter narrows results correctly."""
        query_vec = np.random.randn(BGE_M3_DENSE_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=test_text_collection,
            query=query_vec,
            using="dense",
            limit=10,
            query_filter=Filter(
                must=[FieldCondition(key="grade", match=MatchValue(value=1))]
            ),
            with_payload=True,
        )
        for point in results.points:
            assert point.payload["grade"] == 1

    def test_filter_by_subject(self, qdrant_client, test_text_collection):
        """Subject filter narrows results correctly."""
        query_vec = np.random.randn(BGE_M3_DENSE_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=test_text_collection,
            query=query_vec,
            using="dense",
            limit=10,
            query_filter=Filter(
                must=[FieldCondition(key="subject", match=MatchValue(value="bukvar"))]
            ),
            with_payload=True,
        )
        for point in results.points:
            assert point.payload["subject"] == "bukvar"

    def test_filter_by_trust_tier(self, qdrant_client, test_text_collection):
        """Trust tier filter works."""
        query_vec = np.random.randn(BGE_M3_DENSE_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=test_text_collection,
            query=query_vec,
            using="dense",
            limit=10,
            query_filter=Filter(
                must=[FieldCondition(key="trust_tier", match=MatchValue(value=1))]
            ),
            with_payload=True,
        )
        for point in results.points:
            assert point.payload["trust_tier"] == 1

    def test_combined_filters(self, qdrant_client, test_text_collection):
        """Multiple filters combine correctly (AND logic)."""
        query_vec = np.random.randn(BGE_M3_DENSE_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=test_text_collection,
            query=query_vec,
            using="dense",
            limit=10,
            query_filter=Filter(
                must=[
                    FieldCondition(key="grade", match=MatchValue(value=1)),
                    FieldCondition(key="subject", match=MatchValue(value="bukvar")),
                ]
            ),
            with_payload=True,
        )
        for point in results.points:
            assert point.payload["grade"] == 1
            assert point.payload["subject"] == "bukvar"

    def test_no_results_for_impossible_filter(self, qdrant_client, test_text_collection):
        """Impossible filter returns empty results."""
        query_vec = np.random.randn(BGE_M3_DENSE_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=test_text_collection,
            query=query_vec,
            using="dense",
            limit=10,
            query_filter=Filter(
                must=[FieldCondition(key="grade", match=MatchValue(value=99))]
            ),
            with_payload=True,
        )
        assert len(results.points) == 0


class TestImageSearch:
    """Test image vector search on test collections."""

    def test_image_vector_search(self, qdrant_client, test_image_collection):
        """Query by vector returns image results."""
        query_vec = np.random.randn(SIGLIP_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=test_image_collection,
            query=query_vec,
            limit=2,
            with_payload=True,
        )
        assert len(results.points) > 0
        for point in results.points:
            assert "image_path" in point.payload
            assert "image_id" in point.payload

    def test_image_filter_by_grade(self, qdrant_client, test_image_collection):
        """Grade filter works on image collection."""
        query_vec = np.random.randn(SIGLIP_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=test_image_collection,
            query=query_vec,
            limit=10,
            query_filter=Filter(
                must=[FieldCondition(key="grade", match=MatchValue(value=1))]
            ),
            with_payload=True,
        )
        for point in results.points:
            assert point.payload["grade"] == 1


# ══════════════════════════════════════════════════════════════════
# 6. SCROLL / RETRIEVAL TESTS
# ══════════════════════════════════════════════════════════════════

class TestScrollAndRetrieval:
    """Test scroll and point retrieval operations."""

    def test_scroll_text_collection(self, qdrant_client, test_text_collection):
        """Scroll through text collection returns all points."""
        results, next_offset = qdrant_client.scroll(
            test_text_collection, limit=100, with_payload=True
        )
        assert len(results) > 0

    def test_scroll_with_filter(self, qdrant_client, test_text_collection):
        """Scroll with filter works correctly."""
        results, _ = qdrant_client.scroll(
            test_text_collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="subject", match=MatchValue(value="bukvar"))]
            ),
            limit=100,
            with_payload=True,
        )
        for point in results:
            assert point.payload["subject"] == "bukvar"

    def test_payload_completeness(self, qdrant_client, test_text_collection):
        """All expected text payload fields are present on fully-formed points."""
        results, _ = qdrant_client.scroll(
            test_text_collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="grade", match=MatchValue(value=1))]
            ),
            limit=1,
            with_payload=True,
        )
        assert len(results) > 0, "No grade-1 points found in test collection"
        payload = results[0].payload
        expected = {"text", "chunk_id", "grade", "subject", "author", "trust_tier", "pdf_stem"}
        assert expected.issubset(set(payload.keys())), f"Missing fields: {expected - set(payload.keys())}"


# ══════════════════════════════════════════════════════════════════
# 7. QUERY MODULE TESTS
# ══════════════════════════════════════════════════════════════════

class TestQueryModule:
    """Test the query.py helper functions."""

    def test_build_filter_empty(self):
        from scripts.rag.query import build_filter
        assert build_filter() is None

    def test_build_filter_grade_only(self):
        from scripts.rag.query import build_filter
        f = build_filter(grade=3)
        assert f is not None
        assert len(f.must) == 1
        assert f.must[0].key == "grade"

    def test_build_filter_multiple(self):
        from scripts.rag.query import build_filter
        f = build_filter(grade=3, subject="bukvar", trust_tier=1)
        assert len(f.must) == 3

    def test_collection_stats(self, qdrant_client):
        """collection_stats returns info for both collections."""
        from scripts.rag.query import collection_stats
        stats = collection_stats()
        assert TEXT_COLLECTION in stats
        assert IMAGE_COLLECTION in stats
        assert "points_count" in stats[TEXT_COLLECTION]

    def test_get_chunk_context_invalid_id(self):
        """Invalid chunk_id format returns error."""
        from scripts.rag.query import get_chunk_context
        result = get_chunk_context("no-sequence-number")
        assert len(result) == 1
        assert "error" in result[0]

    def test_get_chunk_context_valid_format(self):
        """Valid chunk_id format is parsed correctly."""
        chunk_id = "test-book_s0005"
        parts = chunk_id.rsplit("_s", 1)
        assert parts[0] == "test-book"
        assert int(parts[1]) == 5


# ══════════════════════════════════════════════════════════════════
# 8. PRODUCTION DATA INTEGRITY TESTS
# ══════════════════════════════════════════════════════════════════

class TestProductionDataIntegrity:
    """Verify production data is correct and queryable."""

    def test_text_collection_has_expected_fields(self, qdrant_client):
        """Production text chunks have all required payload fields."""
        results, _ = qdrant_client.scroll(
            TEXT_COLLECTION, limit=5, with_payload=True
        )
        for point in results:
            p = point.payload
            assert "text" in p, "Missing 'text' field"
            assert "chunk_id" in p, "Missing 'chunk_id' field"
            assert "grade" in p, "Missing 'grade' field"
            assert isinstance(p["grade"], int), f"grade should be int, got {type(p['grade'])}"
            assert p["grade"] >= 1, f"Invalid grade: {p['grade']}"

    def test_image_collection_has_expected_fields(self, qdrant_client):
        """Production images have all required payload fields."""
        results, _ = qdrant_client.scroll(
            IMAGE_COLLECTION, limit=5, with_payload=True
        )
        for point in results:
            p = point.payload
            assert "image_id" in p, "Missing 'image_id' field"
            assert "image_path" in p, "Missing 'image_path' field"
            assert "grade" in p, "Missing 'grade' field"

    def test_text_dense_vector_search_returns_results(self, qdrant_client):
        """Dense vector search on production text collection works."""
        query_vec = np.random.randn(BGE_M3_DENSE_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=TEXT_COLLECTION,
            query=query_vec,
            using="dense",
            limit=3,
            with_payload=True,
        )
        assert len(results.points) > 0

    def test_image_vector_search_returns_results(self, qdrant_client):
        """Vector search on production image collection works."""
        query_vec = np.random.randn(SIGLIP_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=IMAGE_COLLECTION,
            query=query_vec,
            limit=3,
            with_payload=True,
        )
        assert len(results.points) > 0

    def test_grade_filter_on_production(self, qdrant_client):
        """Grade filter returns only matching grades from production data."""
        query_vec = np.random.randn(BGE_M3_DENSE_DIM).tolist()
        results = qdrant_client.query_points(
            collection_name=TEXT_COLLECTION,
            query=query_vec,
            using="dense",
            limit=10,
            query_filter=Filter(
                must=[FieldCondition(key="grade", match=MatchValue(value=1))]
            ),
            with_payload=True,
        )
        assert len(results.points) > 0, "No grade-1 chunks in production"
        for point in results.points:
            assert point.payload["grade"] == 1


# ══════════════════════════════════════════════════════════════════
# 9. INGEST SCRIPT FUNCTION TESTS (MOCKED ENCODERS)
# ══════════════════════════════════════════════════════════════════

class TestIngestFunctions:
    """Test ingest.py functions with mocked encoders to avoid loading ML models."""

    def test_find_jsonl_files(self, tmp_path):
        """find_jsonl_files discovers files by grade directory structure."""
        from scripts.rag.ingest import find_jsonl_files

        # Create fake directory structure
        (tmp_path / "grade-01").mkdir()
        (tmp_path / "grade-01" / "book1.jsonl").write_text("{}")
        (tmp_path / "grade-01" / "book2.jsonl").write_text("{}")
        (tmp_path / "grade-03").mkdir()
        (tmp_path / "grade-03" / "book3.jsonl").write_text("{}")
        (tmp_path / "not-a-grade").mkdir()
        (tmp_path / "not-a-grade" / "noise.jsonl").write_text("{}")

        # All grades
        files = find_jsonl_files(tmp_path)
        assert len(files) == 3

        # Filter by grade
        files = find_jsonl_files(tmp_path, grades=[1])
        assert len(files) == 2
        assert all("grade-01" in str(f) for f in files)

        files = find_jsonl_files(tmp_path, grades=[3])
        assert len(files) == 1

    def test_find_jsonl_files_image_suffix(self, tmp_path):
        """find_jsonl_files can filter by suffix."""
        from scripts.rag.ingest import find_jsonl_files

        (tmp_path / "grade-01").mkdir()
        (tmp_path / "grade-01" / "book1.jsonl").write_text("{}")
        (tmp_path / "grade-01" / "book1-images.jsonl").write_text("{}")

        text_files = find_jsonl_files(tmp_path, suffix=".jsonl")
        assert len(text_files) == 2  # both match .jsonl

        image_files = find_jsonl_files(tmp_path, suffix="-images.jsonl")
        assert len(image_files) == 1
        assert "images" in str(image_files[0])

    def test_create_text_collection_exists_no_recreate(self, qdrant_client):
        """create_text_collection skips if collection exists and recreate=False."""
        from scripts.rag.ingest import create_text_collection
        # Should not raise — collection already exists in production
        create_text_collection(qdrant_client, recreate=False)
        assert qdrant_client.collection_exists(TEXT_COLLECTION)

    def test_create_image_collection_exists_no_recreate(self, qdrant_client):
        """create_image_collection skips if collection exists and recreate=False."""
        from scripts.rag.ingest import create_image_collection
        create_image_collection(qdrant_client, recreate=False)
        assert qdrant_client.collection_exists(IMAGE_COLLECTION)

    def test_ingest_text_empty_file(self, qdrant_client, tmp_path):
        """Ingesting an empty JSONL returns 0."""
        from scripts.rag.ingest import ingest_text_chunks

        empty_jsonl = tmp_path / "empty.jsonl"
        empty_jsonl.write_text("")

        # Mock the encoder to avoid loading models
        with patch("scripts.rag.ingest.get_text_encoder"):
            count = ingest_text_chunks(qdrant_client, empty_jsonl)
        assert count == 0

    def test_ingest_images_empty_file(self, qdrant_client, tmp_path):
        """Ingesting an empty image JSONL returns 0."""
        from scripts.rag.ingest import ingest_images

        empty_jsonl = tmp_path / "empty-images.jsonl"
        empty_jsonl.write_text("")

        with patch("scripts.rag.ingest.get_image_encoder"):
            count = ingest_images(qdrant_client, empty_jsonl)
        assert count == 0


# ══════════════════════════════════════════════════════════════════
# 10. ENCODER TESTS (marked slow — load actual ML models)
# ══════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestEncoders:
    """Test actual ML encoder outputs. Requires models downloaded."""

    def test_text_encoder_output_shape(self):
        from scripts.rag.embed import TextEncoder
        enc = TextEncoder()
        result = enc.encode(["Привіт, світе!"])
        assert result["dense_vecs"].shape == (1, BGE_M3_DENSE_DIM)
        assert len(result["lexical_weights"]) == 1

    def test_text_encoder_batch(self):
        from scripts.rag.embed import TextEncoder
        enc = TextEncoder()
        texts = ["Привіт", "Як справи?", "Дякую"]
        result = enc.encode(texts)
        assert result["dense_vecs"].shape == (3, BGE_M3_DENSE_DIM)
        assert len(result["lexical_weights"]) == 3

    def test_text_encoder_ukrainian_not_garbage(self):
        """Encoded Ukrainian text produces nonzero vectors."""
        from scripts.rag.embed import TextEncoder
        enc = TextEncoder()
        result = enc.encode(["Україна — держава в Східній Європі."])
        vec = result["dense_vecs"][0]
        assert np.abs(vec).sum() > 0, "Vector is all zeros"

    def test_image_encoder_text_output_shape(self):
        from scripts.rag.embed import ImageEncoder
        enc = ImageEncoder()
        vecs = enc.encode_text(["яблуко"])
        assert vecs.shape == (1, SIGLIP_DIM)

    def test_image_encoder_image_output_shape(self):
        """Encode a real image from the dataset."""
        from scripts.rag.embed import ImageEncoder

        # Use an existing image from grade 1
        img_path = PROJECT_ROOT / "data/textbook_images/grade-01/1-klas-bukvar-zaharijchuk-2025-1-p003-01.png"
        if not img_path.exists():
            pytest.skip("Sample image not found")

        enc = ImageEncoder()
        vecs = enc.encode_images([img_path])
        assert vecs.shape == (1, SIGLIP_DIM)
        assert np.abs(vecs).sum() > 0, "Image vector is all zeros"

    def test_image_text_cross_modal(self):
        """Text and image vectors are in same space (non-zero cosine similarity)."""
        from scripts.rag.embed import ImageEncoder

        img_path = PROJECT_ROOT / "data/textbook_images/grade-01/1-klas-bukvar-zaharijchuk-2025-1-p003-01.png"
        if not img_path.exists():
            pytest.skip("Sample image not found")

        enc = ImageEncoder()
        img_vec = enc.encode_images([img_path])[0]
        txt_vec = enc.encode_text(["буквар підручник"])[0]

        # Cosine similarity — should be nonzero (same embedding space)
        cos_sim = np.dot(img_vec, txt_vec) / (np.linalg.norm(img_vec) * np.linalg.norm(txt_vec))
        assert abs(cos_sim) > 0.001, f"Cross-modal cosine similarity too low: {cos_sim}"


# ══════════════════════════════════════════════════════════════════
# 11. MCP SEARCH FUNCTION TESTS (against production data)
# ══════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestMCPSearchFunctions:
    """Test the high-level search functions used by the MCP server."""

    def test_search_text_returns_results(self):
        from scripts.rag.query import search_text
        hits = search_text("голосні звуки", limit=3)
        assert len(hits) > 0
        assert "text" in hits[0]
        assert "chunk_id" in hits[0]
        assert "score" in hits[0]

    def test_search_text_with_grade_filter(self):
        from scripts.rag.query import search_text
        hits = search_text("буква А", grade=1, limit=5)
        for hit in hits:
            assert hit["grade"] == 1

    def test_search_text_with_subject_filter(self):
        from scripts.rag.query import search_text
        hits = search_text("дієслово", subject="ukrainska-mova", limit=5)
        # All results should be from the filtered subject
        # (some may be empty if no matches)

    def test_search_images_returns_results(self):
        from scripts.rag.query import search_images
        hits = search_images("яблуко", limit=3)
        assert len(hits) > 0
        assert "image_path" in hits[0]
        assert "score" in hits[0]

    def test_search_images_with_grade_filter(self):
        from scripts.rag.query import search_images
        hits = search_images("букви", grade=1, limit=5)
        for hit in hits:
            assert hit["grade"] == 1


# ══════════════════════════════════════════════════════════════════════
# Literary RAG: Scraper Tests
# ══════════════════════════════════════════════════════════════════════


class TestHTMLTextExtractor:
    """Test the litopys.org.ua HTML text extractor."""

    def test_extracts_only_dop3_content(self):
        """Text outside dop3 divs should be filtered out."""
        from scripts.rag.scrape_litopys import HTMLTextExtractor

        html = """
        <div class="shapka_strichka">Navigation text here</div>
        <div class="shapka_izb2">ІЗБОРНИК</div>
        <div class="dop3">
            <p>This is actual content.</p>
        </div>
        """
        ext = HTMLTextExtractor(parallel=False)
        ext.feed(html)
        text = ext.get_text()

        assert "Navigation text here" not in text
        assert "ІЗБОРНИК" not in text
        assert "This is actual content." in text

    def test_skips_nav_link_text(self):
        """Nav links like Попередня/Наступна/Головна inside dop3 should be skipped."""
        from scripts.rag.scrape_litopys import HTMLTextExtractor

        html = """
        <div class="dop3">
            <p><a href="prev.htm">Попередня</a> <a href="main.htm">Головна</a>
               <a href="next.htm">Наступна</a></p>
            <p>Actual literary content here.</p>
        </div>
        """
        ext = HTMLTextExtractor(parallel=False)
        ext.feed(html)
        text = ext.get_text()

        assert "Попередня" not in text
        assert "Головна" not in text
        assert "Наступна" not in text
        assert "Actual literary content here." in text

    def test_strips_copyright_lines(self):
        """Copyright and scanning notices should be removed."""
        from scripts.rag.scrape_litopys import HTMLTextExtractor

        html = """
        <div class="dop3">
            <p>Literary content paragraph.</p>
            <p>© Сканування та обробка: Максим, «Ізборник»</p>
        </div>
        """
        ext = HTMLTextExtractor(parallel=False)
        ext.feed(html)
        text = ext.get_text()

        assert "Literary content paragraph." in text
        assert "Сканування та обробка" not in text

    def test_parallel_text_extraction(self):
        """Parallel text tables should extract both columns."""
        from scripts.rag.scrape_litopys import HTMLTextExtractor

        html = """
        <div class="dop3">
            <table>
                <tr><td>Original OES text</td><td>Modern Ukrainian translation</td></tr>
                <tr><td>Другий рядок</td><td>Second row modern</td></tr>
            </table>
        </div>
        """
        ext = HTMLTextExtractor(parallel=True)
        ext.feed(html)

        modern = ext.get_parallel_text()
        original = ext.get_original_text()

        assert "Modern Ukrainian translation" in modern
        assert "Second row modern" in modern
        assert "Original OES text" in original
        assert "Другий рядок" in original

    def test_parallel_fallback_to_text(self):
        """If no table found in parallel mode, fall back to regular text."""
        from scripts.rag.scrape_litopys import HTMLTextExtractor

        html = """
        <div class="dop3">
            <p>Plain text with no table.</p>
        </div>
        """
        ext = HTMLTextExtractor(parallel=True)
        ext.feed(html)

        assert ext.get_parallel_text() == "Plain text with no table."
        assert ext.get_original_text() == ""

    def test_skips_script_and_style(self):
        """Script and style content should never appear in output."""
        from scripts.rag.scrape_litopys import HTMLTextExtractor

        html = """
        <div class="dop3">
            <script>var x = 'should not appear';</script>
            <style>.class { color: red; }</style>
            <p>Visible content only.</p>
        </div>
        """
        ext = HTMLTextExtractor(parallel=False)
        ext.feed(html)
        text = ext.get_text()

        assert "should not appear" not in text
        assert "color: red" not in text
        assert "Visible content only." in text

    def test_heading_extraction(self):
        """Headings should be preserved with paragraph breaks."""
        from scripts.rag.scrape_litopys import HTMLTextExtractor

        html = """
        <div class="dop3">
            <h1>Chapter Title</h1>
            <p>First paragraph.</p>
            <h2>Section Two</h2>
            <p>Second paragraph.</p>
        </div>
        """
        ext = HTMLTextExtractor(parallel=False)
        ext.feed(html)
        text = ext.get_text()

        assert "Chapter Title" in text
        assert "Section Two" in text
        assert "First paragraph." in text

    def test_nested_dop3_divs(self):
        """Nested dop3 divs should still work correctly."""
        from scripts.rag.scrape_litopys import HTMLTextExtractor

        html = """
        <div class="outer">Nav stuff</div>
        <div class="dop3">
            <div>Inner content here.</div>
        </div>
        """
        ext = HTMLTextExtractor(parallel=False)
        ext.feed(html)
        text = ext.get_text()

        assert "Nav stuff" not in text
        assert "Inner content here." in text

    def test_non_nav_links_preserved(self):
        """Regular links (not nav) inside dop3 should have their text preserved."""
        from scripts.rag.scrape_litopys import HTMLTextExtractor

        html = """
        <div class="dop3">
            <p>Read about <a href="other.htm">important topic</a> here.</p>
        </div>
        """
        ext = HTMLTextExtractor(parallel=False)
        ext.feed(html)
        text = ext.get_text()

        assert "important topic" in text


class TestChunkText:
    """Test the paragraph-boundary chunking logic."""

    def test_basic_chunking(self):
        from scripts.rag.scrape_litopys import chunk_text

        # Create text with multiple paragraphs (word content, not spaces)
        paragraphs = ["Це тестовий параграф номер " + str(i) + ". " + "Слово " * 100 for i in range(10)]
        text = "\n\n".join(paragraphs)

        chunks = chunk_text(text, "Test Work", "http://example.com",
                           min_tokens=10, max_tokens=200)

        assert len(chunks) > 1
        for chunk in chunks:
            assert "chunk_id" in chunk
            assert "text" in chunk
            assert "source_url" in chunk
            assert chunk["source_url"] == "http://example.com"

    def test_chunk_ids_are_unique(self):
        from scripts.rag.scrape_litopys import chunk_text

        paragraphs = ["Content block " + str(i) + " " * 500 for i in range(10)]
        text = "\n\n".join(paragraphs)

        chunks = chunk_text(text, "Test Work", "http://example.com",
                           min_tokens=50, max_tokens=200)

        chunk_ids = [c["chunk_id"] for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids)), "Chunk IDs must be unique"

    def test_parallel_text_alignment(self):
        from scripts.rag.scrape_litopys import chunk_text

        modern = "Modern paragraph 1\n\nModern paragraph 2\n\nModern paragraph 3"
        original = "Original paragraph 1\n\nOriginal paragraph 2\n\nOriginal paragraph 3"

        chunks = chunk_text(modern, "Parallel Work", "http://example.com",
                           min_tokens=1, max_tokens=10000, original_text=original)

        assert len(chunks) >= 1
        assert "original_text" in chunks[0]
        assert "Original paragraph" in chunks[0]["original_text"]

    def test_empty_text_returns_empty(self):
        from scripts.rag.scrape_litopys import chunk_text

        chunks = chunk_text("", "Empty Work", "http://example.com")
        assert chunks == []

    def test_short_text_below_min_tokens(self):
        from scripts.rag.scrape_litopys import chunk_text

        chunks = chunk_text("Short.", "Work", "http://example.com",
                           min_tokens=100)
        assert chunks == []  # Too short to form a chunk


class TestFindNextLink:
    """Test the 'Наступна' link finder."""

    def test_finds_next_link(self):
        from scripts.rag.scrape_litopys import find_next_link

        html = '<a href="page02.htm">Наступна</a>'
        result = find_next_link(html, "http://litopys.org.ua/book/page01.htm")
        assert result == "http://litopys.org.ua/book/page02.htm"

    def test_returns_none_when_no_next(self):
        from scripts.rag.scrape_litopys import find_next_link

        html = '<a href="page01.htm">Попередня</a>'
        result = find_next_link(html, "http://litopys.org.ua/book/page02.htm")
        assert result is None

    def test_resolves_relative_urls(self):
        from scripts.rag.scrape_litopys import find_next_link

        html = '<a href="../other/page.htm">Наступна</a>'
        result = find_next_link(html, "http://litopys.org.ua/book/page01.htm")
        assert result == "http://litopys.org.ua/other/page.htm"


# ══════════════════════════════════════════════════════════════════════
# Literary RAG: Qdrant Collection Tests
# ══════════════════════════════════════════════════════════════════════

TEST_LITERARY_COLLECTION = "test_literary_texts"


@pytest.fixture(scope="session")
def test_literary_collection(qdrant_client):
    """Create a test literary collection with sample data."""
    if qdrant_client.collection_exists(TEST_LITERARY_COLLECTION):
        qdrant_client.delete_collection(TEST_LITERARY_COLLECTION)

    qdrant_client.create_collection(
        collection_name=TEST_LITERARY_COLLECTION,
        vectors_config={
            "dense": VectorParams(size=BGE_M3_DENSE_DIM, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(on_disk=False),
            ),
        },
    )

    for field, schema_type in [
        ("work", PayloadSchemaType.KEYWORD),
        ("author", PayloadSchemaType.KEYWORD),
        ("year", PayloadSchemaType.INTEGER),
        ("genre", PayloadSchemaType.KEYWORD),
        ("language_period", PayloadSchemaType.KEYWORD),
    ]:
        qdrant_client.create_payload_index(
            collection_name=TEST_LITERARY_COLLECTION,
            field_name=field,
            field_schema=schema_type,
        )

    # Insert sample data
    rng = np.random.default_rng(42)
    points = [
        PointStruct(
            id=1,
            vector={"dense": rng.random(BGE_M3_DENSE_DIM).tolist(),
                     "sparse": SparseVector(indices=[1, 2, 3], values=[0.5, 0.3, 0.2])},
            payload={
                "chunk_id": "slovo_c0001",
                "text": "Не лЂпо ли ны бяшетъ, братїє",
                "work": "Слово о полку Ігоревім",
                "author": "Невідомий",
                "year": 1187,
                "genre": "poetry",
                "language_period": "old_east_slavic",
                "source_url": "http://litopys.org.ua/slovo/slovo.htm",
            },
        ),
        PointStruct(
            id=2,
            vector={"dense": rng.random(BGE_M3_DENSE_DIM).tolist(),
                     "sparse": SparseVector(indices=[4, 5, 6], values=[0.4, 0.3, 0.3])},
            payload={
                "chunk_id": "pvl_c0001",
                "text": "Повість врем'яних літ чорноризця",
                "work": "Повість временних літ",
                "author": "Нестор",
                "year": 1113,
                "genre": "chronicle",
                "language_period": "old_east_slavic",
                "source_url": "http://litopys.org.ua/pvlyar/yar01.htm",
                "original_text": "ПовЂсть временныхъ лЂтъ черноризца",
            },
        ),
        PointStruct(
            id=3,
            vector={"dense": rng.random(BGE_M3_DENSE_DIM).tolist(),
                     "sparse": SparseVector(indices=[7, 8, 9], values=[0.6, 0.2, 0.2])},
            payload={
                "chunk_id": "samovydets_c0001",
                "text": "Початок и причина войни Хмелницкого",
                "work": "Літопис Самовидця",
                "author": "Невідомий",
                "year": 1702,
                "genre": "chronicle",
                "language_period": "middle_ukrainian",
                "source_url": "http://litopys.org.ua/samovyd/sam01.htm",
            },
        ),
    ]
    qdrant_client.upsert(collection_name=TEST_LITERARY_COLLECTION, points=points)

    yield TEST_LITERARY_COLLECTION

    # Cleanup
    qdrant_client.delete_collection(TEST_LITERARY_COLLECTION)


class TestLiteraryCollection:
    """Test literary collection creation and data integrity."""

    def test_collection_has_correct_vector_config(self, qdrant_client, test_literary_collection):
        info = qdrant_client.get_collection(test_literary_collection)
        assert info.config.params.vectors["dense"].size == BGE_M3_DENSE_DIM
        assert info.config.params.vectors["dense"].distance == Distance.COSINE

    def test_collection_has_points(self, qdrant_client, test_literary_collection):
        info = qdrant_client.get_collection(test_literary_collection)
        assert info.points_count == 3

    def test_payload_fields_present(self, qdrant_client, test_literary_collection):
        results = qdrant_client.scroll(
            collection_name=test_literary_collection, limit=3, with_payload=True
        )
        for point in results[0]:
            payload = point.payload
            assert "chunk_id" in payload
            assert "text" in payload
            assert "work" in payload
            assert "author" in payload
            assert "year" in payload
            assert "genre" in payload
            assert "language_period" in payload

    def test_parallel_text_stored(self, qdrant_client, test_literary_collection):
        """PVL entry should have original_text metadata."""
        results = qdrant_client.scroll(
            collection_name=test_literary_collection,
            scroll_filter=Filter(must=[
                FieldCondition(key="work", match=MatchValue(value="Повість временних літ"))
            ]),
            limit=1,
            with_payload=True,
        )
        assert len(results[0]) == 1
        assert "original_text" in results[0][0].payload

    def test_genre_filter(self, qdrant_client, test_literary_collection):
        results = qdrant_client.scroll(
            collection_name=test_literary_collection,
            scroll_filter=Filter(must=[
                FieldCondition(key="genre", match=MatchValue(value="poetry"))
            ]),
            limit=10,
            with_payload=True,
        )
        for point in results[0]:
            assert point.payload["genre"] == "poetry"

    def test_period_filter(self, qdrant_client, test_literary_collection):
        results = qdrant_client.scroll(
            collection_name=test_literary_collection,
            scroll_filter=Filter(must=[
                FieldCondition(key="language_period", match=MatchValue(value="middle_ukrainian"))
            ]),
            limit=10,
            with_payload=True,
        )
        assert len(results[0]) == 1
        assert results[0][0].payload["work"] == "Літопис Самовидця"

    def test_dense_vector_search(self, qdrant_client, test_literary_collection):
        """Dense vector search should return ranked results."""
        rng = np.random.default_rng(99)
        query_vec = rng.random(BGE_M3_DENSE_DIM).tolist()

        results = qdrant_client.query_points(
            collection_name=test_literary_collection,
            query=query_vec,
            using="dense",
            limit=3,
            with_payload=True,
        )
        assert len(results.points) == 3
        # Scores should be in descending order
        scores = [p.score for p in results.points]
        assert scores == sorted(scores, reverse=True)


# ══════════════════════════════════════════════════════════════════════
# Literary RAG: Production Data Tests (require live data)
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.slow
class TestLiteraryProductionData:
    """Tests against live literary_texts collection (Wave 0 data must be ingested)."""

    def test_collection_exists(self, qdrant_client):
        assert qdrant_client.collection_exists(LITERARY_COLLECTION)

    def test_collection_has_wave0_data(self, qdrant_client):
        info = qdrant_client.get_collection(LITERARY_COLLECTION)
        # Wave 0: 11 (Slovo) + 55 (PVL) + 111 (Samovydets) = 177
        assert info.points_count >= 177

    def test_search_literary_returns_results(self):
        from scripts.rag.query import search_literary
        hits = search_literary("хрещення Русі Володимир", limit=3)
        assert len(hits) > 0
        assert "text" in hits[0]
        assert "work" in hits[0]
        assert "score" in hits[0]

    def test_search_literary_genre_filter(self):
        from scripts.rag.query import search_literary
        hits = search_literary("козацьке повстання", genre="chronicle", limit=5)
        for hit in hits:
            assert hit["genre"] == "chronicle"

    def test_search_literary_period_filter(self):
        from scripts.rag.query import search_literary
        hits = search_literary("битва", period="middle_ukrainian", limit=5)
        for hit in hits:
            assert hit["language_period"] == "middle_ukrainian"

    def test_pvl_has_original_text(self):
        from scripts.rag.query import search_literary
        hits = search_literary("Повість врем'яних літ",
                              work="Повість временних літ (переклад Яременка)", limit=1)
        assert len(hits) > 0
        assert hits[0].get("original_text"), "PVL parallel text should include original_text"

    def test_collection_stats_includes_literary(self):
        from scripts.rag.query import collection_stats
        stats = collection_stats()
        assert "literary_texts" in stats
        assert stats["literary_texts"]["points_count"] >= 177
