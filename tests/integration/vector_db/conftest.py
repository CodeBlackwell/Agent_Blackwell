"""
Vector DB integration test fixtures and configuration.
"""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock

import numpy as np
import pytest

from tests.fixtures.vector_embeddings import (
    generate_random_embedding,
    generate_similar_embedding,
)


class MockVectorDBClient:
    """Mock vector database client for testing."""

    def __init__(self):
        """Initialize the mock vector database client."""
        self.storage = {}  # namespace -> {id: {values, metadata}}
        self.call_count = 0

    async def upsert(
        self, vectors: List[Dict], namespace: str = "default"
    ) -> Dict[str, Any]:
        """Mock upsert operation."""
        self.call_count += 1

        if namespace not in self.storage:
            self.storage[namespace] = {}

        upserted_count = 0
        for vector in vectors:
            vector_id = vector["id"]
            self.storage[namespace][vector_id] = {
                "values": vector["values"],
                "metadata": vector.get("metadata", {}),
            }
            upserted_count += 1

        return {"upserted_count": upserted_count}

    async def fetch(self, ids: List[str], namespace: str = "default") -> Dict[str, Any]:
        """Mock fetch operation."""
        self.call_count += 1

        vectors = {}
        if namespace in self.storage:
            for vector_id in ids:
                if vector_id in self.storage[namespace]:
                    vectors[vector_id] = self.storage[namespace][vector_id]

        return {"vectors": vectors}

    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        namespace: str = "default",
        include_metadata: bool = True,
        filter: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Mock query operation with similarity simulation."""
        self.call_count += 1

        matches = []
        if namespace in self.storage:
            for vector_id, stored_vector in self.storage[namespace].items():
                # Apply filters if specified
                if filter:
                    metadata = stored_vector.get("metadata", {})
                    skip_vector = False

                    for filter_key, filter_condition in filter.items():
                        if (
                            isinstance(filter_condition, dict)
                            and "$eq" in filter_condition
                        ):
                            expected_value = filter_condition["$eq"]
                            actual_value = metadata.get(filter_key)
                            if actual_value != expected_value:
                                skip_vector = True
                                break

                    if skip_vector:
                        continue

                # Calculate mock similarity score
                similarity_score = self._calculate_similarity(
                    vector, stored_vector["values"]
                )

                match = {
                    "id": vector_id,
                    "score": similarity_score,
                }

                if include_metadata:
                    match["metadata"] = stored_vector.get("metadata", {})

                matches.append(match)

        # Sort by score (highest first) and limit to top_k
        matches.sort(key=lambda x: x["score"], reverse=True)
        matches = matches[:top_k]

        return {"matches": matches}

    async def delete(
        self, ids: List[str], namespace: str = "default"
    ) -> Dict[str, Any]:
        """Mock delete operation."""
        self.call_count += 1

        deleted_count = 0
        if namespace in self.storage:
            for vector_id in ids:
                if vector_id in self.storage[namespace]:
                    del self.storage[namespace][vector_id]
                    deleted_count += 1

        return {"deleted_count": deleted_count}

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)

            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = dot_product / (norm_a * norm_b)

            # Ensure similarity is between 0 and 1 for realistic mock results
            return max(0.0, min(1.0, (similarity + 1) / 2))

        except Exception:
            # Fallback to random similarity if calculation fails
            return np.random.uniform(0.5, 0.95)

    def clear_namespace(self, namespace: str = "default"):
        """Clear all vectors in a namespace."""
        if namespace in self.storage:
            self.storage[namespace].clear()

    def clear_all(self):
        """Clear all stored vectors."""
        self.storage.clear()
        self.call_count = 0


@pytest.fixture
async def vector_db_client():
    """Provide a mock vector database client for testing."""
    client = MockVectorDBClient()
    yield client
    # Cleanup after each test
    client.clear_all()


@pytest.fixture
def sample_embeddings():
    """Provide sample embeddings for testing."""
    return {
        "base_embedding": generate_random_embedding(),
        "similar_embeddings": [
            generate_similar_embedding(generate_random_embedding(), 0.9),
            generate_similar_embedding(generate_random_embedding(), 0.8),
            generate_similar_embedding(generate_random_embedding(), 0.7),
        ],
        "random_embeddings": [generate_random_embedding() for _ in range(5)],
    }


@pytest.fixture
def sample_metadata():
    """Provide sample metadata for testing."""
    return [
        {"type": "user_request", "category": "development", "priority": "high"},
        {"type": "specification", "category": "design", "priority": "medium"},
        {"type": "code", "category": "implementation", "priority": "high"},
        {"type": "review", "category": "quality", "priority": "low"},
        {"type": "test", "category": "validation", "priority": "medium"},
    ]


@pytest.fixture
async def populated_vector_db(vector_db_client, sample_embeddings, sample_metadata):
    """Provide a vector DB client pre-populated with test data."""
    # Store base embedding
    await vector_db_client.upsert(
        vectors=[
            {
                "id": "base_001",
                "values": sample_embeddings["base_embedding"],
                "metadata": sample_metadata[0],
            }
        ],
        namespace="test",
    )

    # Store similar embeddings
    for i, embedding in enumerate(sample_embeddings["similar_embeddings"]):
        await vector_db_client.upsert(
            vectors=[
                {
                    "id": f"similar_{i+1:03d}",
                    "values": embedding,
                    "metadata": sample_metadata[i + 1]
                    if i + 1 < len(sample_metadata)
                    else sample_metadata[0],
                }
            ],
            namespace="test",
        )

    # Store random embeddings
    for i, embedding in enumerate(sample_embeddings["random_embeddings"]):
        await vector_db_client.upsert(
            vectors=[
                {
                    "id": f"random_{i+1:03d}",
                    "values": embedding,
                    "metadata": sample_metadata[i % len(sample_metadata)],
                }
            ],
            namespace="test",
        )

    return vector_db_client


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
