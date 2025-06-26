"""
Sample vector embeddings and related fixtures for integration testing.
"""
import numpy as np
from typing import Dict, List, Any
import random

def generate_random_embedding(dimension: int = 1536) -> List[float]:
    """Generate a random embedding vector of specified dimension."""
    # Generate random normalized vector
    vector = np.random.normal(0, 1, dimension)
    # Normalize to unit vector
    vector = vector / np.linalg.norm(vector)
    return vector.tolist()

def generate_similar_embedding(base_embedding: List[float], similarity: float = 0.8) -> List[float]:
    """Generate an embedding similar to the base embedding."""
    base = np.array(base_embedding)
    noise = np.random.normal(0, 1, len(base))
    noise = noise / np.linalg.norm(noise)
    
    # Mix base and noise based on similarity
    similar = similarity * base + (1 - similarity) * noise
    similar = similar / np.linalg.norm(similar)
    return similar.tolist()

# Sample embeddings for different content types
SAMPLE_EMBEDDINGS = {
    "user_requests": [
        {
            "id": "emb_req_001",
            "text": "Create a REST API for managing books",
            "embedding": generate_random_embedding(),
            "metadata": {
                "type": "user_request",
                "complexity": "medium",
                "domain": "web_development"
            }
        },
        {
            "id": "emb_req_002", 
            "text": "Build a real-time chat application",
            "embedding": generate_random_embedding(),
            "metadata": {
                "type": "user_request",
                "complexity": "complex",
                "domain": "web_development"
            }
        },
        {
            "id": "emb_req_003",
            "text": "Write a function to validate email addresses",
            "embedding": generate_random_embedding(),
            "metadata": {
                "type": "user_request",
                "complexity": "simple",
                "domain": "utility"
            }
        }
    ],
    "specifications": [
        {
            "id": "emb_spec_001",
            "text": "Book Management REST API with CRUD operations",
            "embedding": generate_random_embedding(),
            "metadata": {
                "type": "specification",
                "agent": "spec_agent",
                "task_id": "spec_001"
            }
        }
    ],
    "code_snippets": [
        {
            "id": "emb_code_001",
            "text": "FastAPI endpoint for creating books",
            "embedding": generate_random_embedding(),
            "metadata": {
                "type": "code",
                "language": "python",
                "framework": "fastapi",
                "agent": "coding_agent"
            }
        }
    ]
}

def create_embedding_clusters(num_clusters: int = 3, items_per_cluster: int = 5) -> Dict[str, Any]:
    """Create clusters of similar embeddings for testing semantic search."""
    clusters = {}
    
    for cluster_id in range(num_clusters):
        # Generate a random center embedding
        center_embedding = generate_random_embedding()
        cluster_name = f"cluster_{cluster_id}"
        clusters[cluster_name] = {
            "center": center_embedding,
            "items": []
        }
        
        # Generate similar embeddings around the center
        for item_id in range(items_per_cluster):
            similar_embedding = generate_similar_embedding(center_embedding, 0.9)
            clusters[cluster_name]["items"].append({
                "id": f"{cluster_name}_item_{item_id}",
                "embedding": similar_embedding,
                "text": f"Sample text for {cluster_name} item {item_id}",
                "similarity_to_center": 0.9
            })
    
    return clusters

def generate_search_test_data() -> Dict[str, Any]:
    """Generate test data for semantic search functionality."""
    # Create base embeddings
    base_texts = [
        "Create a web application with authentication",
        "Build a REST API with database integration", 
        "Implement user registration and login",
        "Design a microservices architecture",
        "Write unit tests for API endpoints"
    ]
    
    search_data = {
        "documents": [],
        "queries": [],
        "expected_matches": {}
    }
    
    # Generate document embeddings
    for i, text in enumerate(base_texts):
        doc_embedding = generate_random_embedding()
        search_data["documents"].append({
            "id": f"doc_{i}",
            "text": text,
            "embedding": doc_embedding,
            "metadata": {"category": "development"}
        })
    
    # Generate query embeddings that should match specific documents
    search_data["queries"] = [
        {
            "id": "query_001",
            "text": "How to build a web app with user login?",
            "embedding": generate_similar_embedding(search_data["documents"][0]["embedding"], 0.85),
            "expected_matches": ["doc_0", "doc_2"]  # Should match auth-related docs
        },
        {
            "id": "query_002", 
            "text": "REST API development guide",
            "embedding": generate_similar_embedding(search_data["documents"][1]["embedding"], 0.85),
            "expected_matches": ["doc_1", "doc_4"]  # Should match API-related docs
        }
    ]
    
    return search_data

# Vector database operation fixtures
VECTOR_DB_OPERATIONS = {
    "insert": {
        "vectors": [
            {
                "id": "vec_001",
                "values": generate_random_embedding(),
                "metadata": {"type": "user_request", "timestamp": "2025-01-01T12:00:00Z"}
            },
            {
                "id": "vec_002", 
                "values": generate_random_embedding(),
                "metadata": {"type": "specification", "timestamp": "2025-01-01T12:15:00Z"}
            }
        ],
        "namespace": "test"
    },
    "query": {
        "vector": generate_random_embedding(),
        "top_k": 5,
        "namespace": "test",
        "include_metadata": True,
        "expected_results": [
            {"id": "vec_001", "score": 0.95, "metadata": {"type": "user_request"}},
            {"id": "vec_002", "score": 0.87, "metadata": {"type": "specification"}}
        ]
    },
    "delete": {
        "ids": ["vec_001", "vec_002"],
        "namespace": "test"
    }
}

def generate_comprehensive_vector_fixtures() -> Dict[str, Any]:
    """Generate comprehensive vector embedding fixtures for testing."""
    return {
        "sample_embeddings": SAMPLE_EMBEDDINGS,
        "embedding_clusters": create_embedding_clusters(),
        "search_test_data": generate_search_test_data(),
        "vector_db_operations": VECTOR_DB_OPERATIONS,
        "dimensions": {
            "openai_ada": 1536,
            "openai_small": 1536,
            "sentence_transformers": 768
        }
    }
