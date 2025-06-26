"""
Phase 4: Pinecone/Vector DB Integration Tests - Embedding Operations
Tests for embedding storage, retrieval, and basic CRUD operations.
"""

import asyncio
from typing import Any, Dict, List

import numpy as np
import pytest

from tests.fixtures.vector_embeddings import (
    SAMPLE_EMBEDDINGS,
    VECTOR_DB_OPERATIONS,
    generate_random_embedding,
    generate_similar_embedding,
)


class TestEmbeddingStorage:
    """Test embedding storage and retrieval operations."""

    @pytest.mark.asyncio
    async def test_store_single_embedding(self, vector_db_client):
        """Test storing a single embedding."""
        # Generate test embedding
        test_embedding = generate_random_embedding()
        embedding_id = "test_embedding_001"
        metadata = {
            "type": "test",
            "content": "Test embedding for storage",
            "timestamp": "2025-01-01T12:00:00Z",
        }

        # Store embedding
        result = await vector_db_client.upsert(
            vectors=[
                {"id": embedding_id, "values": test_embedding, "metadata": metadata}
            ],
            namespace="test",
        )

        assert result is not None
        assert result.get("upserted_count", 0) >= 1

    @pytest.mark.asyncio
    async def test_store_batch_embeddings(self, vector_db_client):
        """Test storing multiple embeddings in batch."""
        batch_size = 10
        vectors = []

        for i in range(batch_size):
            vectors.append(
                {
                    "id": f"batch_embedding_{i:03d}",
                    "values": generate_random_embedding(),
                    "metadata": {
                        "type": "batch_test",
                        "batch_id": "batch_001",
                        "index": i,
                    },
                }
            )

        # Store batch
        result = await vector_db_client.upsert(vectors=vectors, namespace="test")

        assert result is not None
        assert result.get("upserted_count", 0) == batch_size

    @pytest.mark.asyncio
    async def test_retrieve_embedding_by_id(self, vector_db_client):
        """Test retrieving specific embeddings by ID."""
        # First store an embedding
        test_id = "retrieve_test_001"
        test_embedding = generate_random_embedding()
        test_metadata = {"type": "retrieve_test", "content": "Test retrieval"}

        await vector_db_client.upsert(
            vectors=[
                {"id": test_id, "values": test_embedding, "metadata": test_metadata}
            ],
            namespace="test",
        )

        # Retrieve by ID
        result = await vector_db_client.fetch(ids=[test_id], namespace="test")

        assert result is not None
        assert test_id in result.get("vectors", {})
        retrieved_vector = result["vectors"][test_id]
        assert retrieved_vector["metadata"]["type"] == "retrieve_test"

    @pytest.mark.asyncio
    async def test_update_embedding_metadata(self, vector_db_client):
        """Test updating embedding metadata."""
        test_id = "update_test_001"
        original_metadata = {"type": "original", "version": 1}
        updated_metadata = {"type": "updated", "version": 2}

        # Store original
        await vector_db_client.upsert(
            vectors=[
                {
                    "id": test_id,
                    "values": generate_random_embedding(),
                    "metadata": original_metadata,
                }
            ],
            namespace="test",
        )

        # Update metadata
        await vector_db_client.upsert(
            vectors=[
                {
                    "id": test_id,
                    "values": generate_random_embedding(),
                    "metadata": updated_metadata,
                }
            ],
            namespace="test",
        )

        # Verify update
        result = await vector_db_client.fetch(ids=[test_id], namespace="test")

        retrieved_metadata = result["vectors"][test_id]["metadata"]
        assert retrieved_metadata["type"] == "updated"
        assert retrieved_metadata["version"] == 2

    @pytest.mark.asyncio
    async def test_delete_embeddings(self, vector_db_client):
        """Test deleting embeddings."""
        # Store test embeddings
        test_ids = ["delete_test_001", "delete_test_002"]
        vectors = []

        for test_id in test_ids:
            vectors.append(
                {
                    "id": test_id,
                    "values": generate_random_embedding(),
                    "metadata": {"type": "delete_test"},
                }
            )

        await vector_db_client.upsert(vectors=vectors, namespace="test")

        # Delete embeddings
        delete_result = await vector_db_client.delete(ids=test_ids, namespace="test")

        assert delete_result is not None

        # Verify deletion
        fetch_result = await vector_db_client.fetch(ids=test_ids, namespace="test")

        # Should return empty or not found
        assert len(fetch_result.get("vectors", {})) == 0


class TestEmbeddingNamespaces:
    """Test namespace isolation and management."""

    @pytest.mark.asyncio
    async def test_namespace_isolation(self, vector_db_client):
        """Test that embeddings in different namespaces are isolated."""
        test_id = "namespace_test_001"
        namespace_a = "test_namespace_a"
        namespace_b = "test_namespace_b"

        # Store same ID in different namespaces
        await vector_db_client.upsert(
            vectors=[
                {
                    "id": test_id,
                    "values": generate_random_embedding(),
                    "metadata": {"namespace": "a"},
                }
            ],
            namespace=namespace_a,
        )

        await vector_db_client.upsert(
            vectors=[
                {
                    "id": test_id,
                    "values": generate_random_embedding(),
                    "metadata": {"namespace": "b"},
                }
            ],
            namespace=namespace_b,
        )

        # Retrieve from each namespace
        result_a = await vector_db_client.fetch(ids=[test_id], namespace=namespace_a)

        result_b = await vector_db_client.fetch(ids=[test_id], namespace=namespace_b)

        # Both should exist but with different metadata
        assert result_a["vectors"][test_id]["metadata"]["namespace"] == "a"
        assert result_b["vectors"][test_id]["metadata"]["namespace"] == "b"

    @pytest.mark.asyncio
    async def test_cross_namespace_query_isolation(self, vector_db_client):
        """Test that queries don't cross namespace boundaries."""
        query_vector = generate_random_embedding()
        namespace_a = "query_test_a"
        namespace_b = "query_test_b"

        # Store vectors in different namespaces
        await vector_db_client.upsert(
            vectors=[
                {
                    "id": "query_test_a_001",
                    "values": generate_similar_embedding(query_vector, 0.9),
                    "metadata": {"namespace": "a"},
                }
            ],
            namespace=namespace_a,
        )

        await vector_db_client.upsert(
            vectors=[
                {
                    "id": "query_test_b_001",
                    "values": generate_similar_embedding(query_vector, 0.9),
                    "metadata": {"namespace": "b"},
                }
            ],
            namespace=namespace_b,
        )

        # Query each namespace
        result_a = await vector_db_client.query(
            vector=query_vector, top_k=10, namespace=namespace_a, include_metadata=True
        )

        result_b = await vector_db_client.query(
            vector=query_vector, top_k=10, namespace=namespace_b, include_metadata=True
        )

        # Each should only return results from its own namespace
        for match in result_a.get("matches", []):
            assert match["metadata"]["namespace"] == "a"

        for match in result_b.get("matches", []):
            assert match["metadata"]["namespace"] == "b"
