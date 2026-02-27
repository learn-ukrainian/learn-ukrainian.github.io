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
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

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
        with open(text_jsonl_file, "r", encoding="utf-8") as f:
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
        with open(image_jsonl_file, "r", encoding="utf-8") as f:
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
