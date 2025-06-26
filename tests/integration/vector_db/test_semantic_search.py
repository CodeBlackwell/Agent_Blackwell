"""
Phase 4: Pinecone/Vector DB Integration Tests - Semantic Search
Tests for semantic search functionality, similarity matching, and context retrieval.
"""

import asyncio
from typing import Any, Dict, List

import numpy as np
import pytest

from tests.fixtures.vector_embeddings import (
    SAMPLE_EMBEDDINGS,
    create_embedding_clusters,
    generate_random_embedding,
    generate_search_test_data,
    generate_similar_embedding,
)


class TestSemanticSearch:
    """Test semantic search and similarity matching functionality."""

    @pytest.mark.asyncio
    async def test_basic_similarity_search(self, vector_db_client):
        """Test basic similarity search with known similar vectors."""
        # Create base embedding and similar variants
        base_embedding = generate_random_embedding()

        # Store base and similar embeddings
        vectors = [
            {
                "id": "base_001",
                "values": base_embedding,
                "metadata": {"type": "base", "content": "Base document"},
            },
            {
                "id": "similar_001",
                "values": generate_similar_embedding(base_embedding, 0.9),
                "metadata": {"type": "similar", "content": "Very similar document"},
            },
            {
                "id": "similar_002",
                "values": generate_similar_embedding(base_embedding, 0.7),
                "metadata": {
                    "type": "similar",
                    "content": "Moderately similar document",
                },
            },
            {
                "id": "different_001",
                "values": generate_random_embedding(),
                "metadata": {"type": "different", "content": "Different document"},
            },
        ]

        await vector_db_client.upsert(vectors=vectors, namespace="similarity_test")

        # Search using base embedding
        results = await vector_db_client.query(
            vector=base_embedding,
            top_k=4,
            namespace="similarity_test",
            include_metadata=True,
        )

        matches = results.get("matches", [])
        assert len(matches) >= 3

        # First match should be the base itself (or very close)
        first_match = matches[0]
        assert first_match["score"] >= 0.98  # Should be nearly identical

        # Similar embeddings should have high scores
        similar_matches = [m for m in matches if m["metadata"]["type"] == "similar"]
        assert len(similar_matches) >= 2
        assert all(m["score"] >= 0.6 for m in similar_matches)

    @pytest.mark.asyncio
    async def test_top_k_filtering(self, vector_db_client):
        """Test that top_k parameter correctly limits results."""
        query_vector = generate_random_embedding()

        # Store more vectors than we'll request
        vectors = []
        for i in range(20):
            vectors.append(
                {
                    "id": f"topk_test_{i:03d}",
                    "values": generate_similar_embedding(query_vector, 0.8),
                    "metadata": {"index": i},
                }
            )

        await vector_db_client.upsert(vectors=vectors, namespace="topk_test")

        # Test different top_k values
        for k in [1, 3, 5, 10]:
            results = await vector_db_client.query(
                vector=query_vector,
                top_k=k,
                namespace="topk_test",
                include_metadata=True,
            )

            matches = results.get("matches", [])
            assert len(matches) == k

            # Results should be sorted by score (highest first)
            scores = [m["score"] for m in matches]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_metadata_filtering(self, vector_db_client):
        """Test filtering search results by metadata."""
        query_vector = generate_random_embedding()

        # Store vectors with different metadata
        vectors = []
        categories = ["category_a", "category_b", "category_c"]

        for i, category in enumerate(categories * 3):  # 9 vectors total
            vectors.append(
                {
                    "id": f"filter_test_{i:03d}",
                    "values": generate_similar_embedding(query_vector, 0.8),
                    "metadata": {
                        "category": category,
                        "priority": "high" if i % 2 == 0 else "low",
                    },
                }
            )

        await vector_db_client.upsert(vectors=vectors, namespace="filter_test")

        # Test category filtering
        results = await vector_db_client.query(
            vector=query_vector,
            top_k=10,
            namespace="filter_test",
            include_metadata=True,
            filter={"category": {"$eq": "category_a"}},
        )

        matches = results.get("matches", [])
        assert len(matches) == 3  # Should only return category_a vectors
        assert all(m["metadata"]["category"] == "category_a" for m in matches)

        # Test priority filtering
        results = await vector_db_client.query(
            vector=query_vector,
            top_k=10,
            namespace="filter_test",
            include_metadata=True,
            filter={"priority": {"$eq": "high"}},
        )

        matches = results.get("matches", [])
        assert all(m["metadata"]["priority"] == "high" for m in matches)


class TestSemanticClustering:
    """Test semantic clustering and related vector discovery."""

    @pytest.mark.asyncio
    async def test_cluster_discovery(self, vector_db_client):
        """Test discovering semantically related vectors in clusters."""
        # Create embedding clusters
        clusters = create_embedding_clusters(num_clusters=3, items_per_cluster=5)

        # Store all cluster items
        vectors = []
        for cluster_name, cluster_data in clusters.items():
            for item in cluster_data["items"]:
                vectors.append(
                    {
                        "id": item["id"],
                        "values": item["embedding"],
                        "metadata": {"cluster": cluster_name, "text": item["text"]},
                    }
                )

        await vector_db_client.upsert(vectors=vectors, namespace="cluster_test")

        # Test querying with cluster centers
        for cluster_name, cluster_data in clusters.items():
            center_vector = cluster_data["center"]

            results = await vector_db_client.query(
                vector=center_vector,
                top_k=8,  # Should get most/all items from this cluster
                namespace="cluster_test",
                include_metadata=True,
            )

            matches = results.get("matches", [])

            # Most matches should be from the same cluster
            same_cluster_matches = [
                m for m in matches if m["metadata"]["cluster"] == cluster_name
            ]

            # Should find at least 3 items from the same cluster
            assert len(same_cluster_matches) >= 3

            # Same cluster matches should have higher scores
            if len(matches) > len(same_cluster_matches):
                other_cluster_matches = [
                    m for m in matches if m["metadata"]["cluster"] != cluster_name
                ]

                avg_same_cluster_score = sum(
                    m["score"] for m in same_cluster_matches
                ) / len(same_cluster_matches)

                avg_other_cluster_score = sum(
                    m["score"] for m in other_cluster_matches
                ) / len(other_cluster_matches)

                assert avg_same_cluster_score > avg_other_cluster_score


class TestKnowledgePersistence:
    """Test knowledge persistence and context retrieval functionality."""

    @pytest.mark.asyncio
    async def test_conversation_context_storage(self, vector_db_client):
        """Test storing and retrieving conversation context."""
        # Simulate storing conversation turns
        conversation_vectors = []
        conversation_id = "conv_001"

        turns = [
            "User: How do I create a REST API?",
            "Assistant: To create a REST API, you can use frameworks like FastAPI or Flask...",
            "User: What about authentication?",
            "Assistant: For authentication, you can implement JWT tokens or OAuth...",
            "User: Show me an example with FastAPI",
            "Assistant: Here's a FastAPI example with JWT authentication...",
        ]

        for i, turn in enumerate(turns):
            conversation_vectors.append(
                {
                    "id": f"{conversation_id}_turn_{i:03d}",
                    "values": generate_random_embedding(),
                    "metadata": {
                        "conversation_id": conversation_id,
                        "turn_number": i,
                        "speaker": "user" if i % 2 == 0 else "assistant",
                        "content": turn,
                        "timestamp": f"2025-01-01T12:{i:02d}:00Z",
                    },
                }
            )

        await vector_db_client.upsert(
            vectors=conversation_vectors, namespace="conversations"
        )

        # Test retrieving conversation context
        query_vector = generate_random_embedding()

        results = await vector_db_client.query(
            vector=query_vector,
            top_k=10,
            namespace="conversations",
            include_metadata=True,
            filter={"conversation_id": {"$eq": conversation_id}},
        )

        matches = results.get("matches", [])
        assert len(matches) == len(turns)

        # Verify conversation order can be reconstructed
        sorted_matches = sorted(matches, key=lambda x: x["metadata"]["turn_number"])
        for i, match in enumerate(sorted_matches):
            assert match["metadata"]["turn_number"] == i
            assert match["metadata"]["content"] == turns[i]

    @pytest.mark.asyncio
    async def test_knowledge_base_retrieval(self, vector_db_client):
        """Test retrieving relevant knowledge from stored documents."""
        # Store knowledge base documents
        knowledge_docs = [
            {
                "id": "kb_python_basics",
                "content": "Python is a high-level programming language with dynamic typing",
                "category": "programming",
                "tags": ["python", "basics", "language"],
            },
            {
                "id": "kb_api_design",
                "content": "REST API design principles include statelessness and resource-based URLs",
                "category": "api_design",
                "tags": ["rest", "api", "design", "principles"],
            },
            {
                "id": "kb_authentication",
                "content": "JWT tokens provide stateless authentication for web applications",
                "category": "security",
                "tags": ["jwt", "auth", "security", "tokens"],
            },
        ]

        vectors = []
        for doc in knowledge_docs:
            vectors.append(
                {
                    "id": doc["id"],
                    "values": generate_random_embedding(),
                    "metadata": {
                        "content": doc["content"],
                        "category": doc["category"],
                        "tags": doc["tags"],
                    },
                }
            )

        await vector_db_client.upsert(vectors=vectors, namespace="knowledge_base")

        # Test knowledge retrieval with different query types
        query_scenarios = [
            {
                "query": "How to implement authentication in web apps?",
                "expected_categories": ["security", "api_design"],
                "expected_tags": ["jwt", "auth"],
            },
            {
                "query": "Python programming language features",
                "expected_categories": ["programming"],
                "expected_tags": ["python", "basics"],
            },
        ]

        for scenario in query_scenarios:
            query_vector = generate_random_embedding()

            results = await vector_db_client.query(
                vector=query_vector,
                top_k=5,
                namespace="knowledge_base",
                include_metadata=True,
            )

            matches = results.get("matches", [])
            assert len(matches) > 0

            # Verify we get relevant results
            found_categories = set()
            found_tags = set()

            for match in matches:
                found_categories.add(match["metadata"]["category"])
                found_tags.update(match["metadata"]["tags"])

            # Should find at least some expected categories/tags
            expected_cats = set(scenario["expected_categories"])
            expected_tags_set = set(scenario["expected_tags"])

            assert (
                len(found_categories.intersection(expected_cats)) > 0
                or len(found_tags.intersection(expected_tags_set)) > 0
            )
