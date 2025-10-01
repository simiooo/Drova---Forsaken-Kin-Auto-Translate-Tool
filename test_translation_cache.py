#!/usr/bin/env python3
"""
Test script for TranslationCache functionality
"""

import asyncio
import json
import os
import tempfile
import logging
from translate_loc import TranslationCache

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

async def test_translation_cache():
    """Test the TranslationCache class functionality"""
    
    # Create a temporary cache file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_cache_data = {
            "Nemeton": "内梅顿",
            "Knawd Moor": "克诺德沼泽", 
            "Cengiz": "成吉兹",
            "Georgefarm": "乔治农场"
        }
        json.dump(test_cache_data, f, ensure_ascii=False)
        temp_cache_file = f.name
    
    try:
        print("=== Testing TranslationCache ===")
        
        # Test 1: Load existing cache
        print("\n1. Testing cache loading...")
        cache = TranslationCache(temp_cache_file)
        print(f"   Loaded {len(cache.cache)} entries from cache")
        print(f"   Cache content: {cache.cache}")
        
        # Test 2: get_name_map with existing keys
        print("\n2. Testing get_name_map with existing keys...")
        existing_keys = ["Nemeton", "Cengiz"]
        name_map = cache.get_name_map(existing_keys)
        print(f"   Requested keys: {existing_keys}")
        print(f"   Retrieved map: {name_map}")
        
        # Test 3: get_name_map with mixed keys (some existing, some missing)
        print("\n3. Testing get_name_map with mixed keys...")
        mixed_keys = ["Nemeton", "NonExistentKey", "Cengiz"]
        name_map = cache.get_name_map(mixed_keys)
        print(f"   Requested keys: {mixed_keys}")
        print(f"   Retrieved map: {name_map}")
        
        # Test 4: get_name_map with empty keys
        print("\n4. Testing get_name_map with empty keys...")
        empty_map = cache.get_name_map([])
        print(f"   Empty keys result: {empty_map}")
        
        # Test 5: Update cache with new translations
        print("\n5. Testing cache update...")
        new_translations = {
            "NewPlace": "新地点",
            "AnotherName": "另一个名字"
        }
        await cache.update(new_translations)
        print(f"   Updated cache size: {len(cache.cache)}")
        print(f"   New entries should be in cache: {new_translations}")
        
        # Test 6: Save cache and verify file content
        print("\n6. Testing cache save...")
        await cache.save()
        
        # Read the saved file to verify
        with open(temp_cache_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        print(f"   Saved cache size: {len(saved_data)}")
        print(f"   All new entries present: {all(k in saved_data for k in new_translations)}")
        
        # Test 7: Test concurrent updates (simulated)
        print("\n7. Testing concurrent operations...")
        async def concurrent_update(key, value):
            await cache.update({key: value})
            return f"Updated {key}"
        
        # Run multiple updates concurrently
        tasks = [
            concurrent_update("Concurrent1", "并发1"),
            concurrent_update("Concurrent2", "并发2"),
            concurrent_update("Concurrent3", "并发3")
        ]
        results = await asyncio.gather(*tasks)
        print(f"   Concurrent update results: {results}")
        print(f"   Final cache size: {len(cache.cache)}")
        
        # Test 8: Test with None and empty values
        print("\n8. Testing update with None and empty values...")
        await cache.update({
            "ValidKey": "有效值",
            "NoneKey": None,
            "EmptyKey": "",
            "SpaceKey": "   "
        })
        print(f"   Cache size after filtering invalid values: {len(cache.cache)}")
        print(f"   NoneKey in cache: {'NoneKey' in cache.cache}")
        print(f"   EmptyKey in cache: {'EmptyKey' in cache.cache}")
        
        print("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        raise
    finally:
        # Clean up temporary file
        if os.path.exists(temp_cache_file):
            os.unlink(temp_cache_file)
            print(f"\nCleaned up temporary file: {temp_cache_file}")

async def test_cache_file_operations():
    """Test cache file operations with edge cases"""
    print("\n=== Testing Cache File Operations ===")
    
    # Test 1: Non-existent cache file
    print("\n1. Testing with non-existent cache file...")
    cache = TranslationCache("non_existent_cache.json")
    print(f"   Cache initialized with {len(cache.cache)} entries")
    
    # Test 2: Invalid JSON file
    print("\n2. Testing with invalid JSON file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content")
        invalid_json_file = f.name
    
    try:
        cache = TranslationCache(invalid_json_file)
        print(f"   Cache initialized with {len(cache.cache)} entries (should be 0)")
    finally:
        if os.path.exists(invalid_json_file):
            os.unlink(invalid_json_file)
    
    # Test 3: Directory creation for cache file
    print("\n3. Testing directory creation...")
    nested_cache_file = "test_cache/nested/cache.json"
    cache = TranslationCache(nested_cache_file)
    await cache.update({"TestKey": "测试值"})
    await cache.save()
    
    if os.path.exists(nested_cache_file):
        print(f"   Directory created successfully")
        # Clean up
        import shutil
        shutil.rmtree("test_cache")
    else:
        print(f"   Directory creation failed")

if __name__ == "__main__":
    asyncio.run(test_translation_cache())
    asyncio.run(test_cache_file_operations())