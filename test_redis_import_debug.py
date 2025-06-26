#!/usr/bin/env python3
"""
Debug script to test different Redis import approaches under pytest
"""

def test_redis_import_approaches():
    """Test different ways to import redis.asyncio"""
    
    # Approach 1: Direct import (current failing approach)
    try:
        import redis.asyncio as redis_async1
        print("✓ Approach 1 (redis.asyncio as redis_async) SUCCESS")
        print(f"  Module: {redis_async1}")
        print(f"  File: {redis_async1.__file__}")
    except ImportError as e:
        print(f"✗ Approach 1 FAILED: {e}")
    
    # Approach 2: From import
    try:
        from redis import asyncio as redis_async2  
        print("✓ Approach 2 (from redis import asyncio) SUCCESS")
        print(f"  Module: {redis_async2}")
        print(f"  File: {redis_async2.__file__}")
    except ImportError as e:
        print(f"✗ Approach 2 FAILED: {e}")
    
    # Approach 3: Import redis then access asyncio
    try:
        import redis
        redis_async3 = redis.asyncio
        print("✓ Approach 3 (redis.asyncio after import redis) SUCCESS")
        print(f"  Module: {redis_async3}")
        print(f"  File: {redis_async3.__file__}")
    except (ImportError, AttributeError) as e:
        print(f"✗ Approach 3 FAILED: {e}")
    
    # Approach 4: Dynamic import
    try:
        import importlib
        redis_async4 = importlib.import_module('redis.asyncio')
        print("✓ Approach 4 (importlib.import_module) SUCCESS")
        print(f"  Module: {redis_async4}")
        print(f"  File: {redis_async4.__file__}")
    except ImportError as e:
        print(f"✗ Approach 4 FAILED: {e}")

if __name__ == "__main__":
    test_redis_import_approaches()
