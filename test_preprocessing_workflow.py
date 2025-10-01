#!/usr/bin/env python3
"""
测试预处理和后处理工作流程
Test script for preprocessing and post-processing workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from translate_loc import extract_pure_game_text, reassemble_translated_content

def test_complete_workflow():
    """测试完整的预处理和后处理工作流程"""
    print("=== Testing Complete Preprocessing and Post-processing Workflow ===\n")
    
    # Test content with multiple entries
    test_content = '''Achievement_ImmersiveMod_name { Iron }
Plh_35 { The chains are firmly aff\" }
LevelUp { You gained a level!<br>Each time you gain a level, you are fully healed and receive 4 learning points.}'''

    print("1. Original content:")
    print(test_content)
    print(f"   Length: {len(test_content)} characters\n")

    # Preprocessing: Extract pure game text
    print("2. Preprocessing: Extracting pure game text...")
    pure_text, original_entries = extract_pure_game_text(test_content)
    print(f"   Extracted pure game text:")
    print(f"   {pure_text}")
    print(f"   Length: {len(pure_text)} characters")
    print(f"   Original entries count: {len(original_entries)}")
    
    # Show original entries structure
    print(f"   Original entries structure:")
    for i, (key, value) in enumerate(original_entries):
        print(f"     {i+1}. {key}: {repr(value)}")
    print()

    # Simulate LLM translation (mock translated text)
    print("3. Simulating LLM translation...")
    mock_translated = '''铁
链条被牢固地固定
你升级了！<br>每次升级时，你会完全恢复并获得4个学习点数。'''
    print(f"   Mock translated text:")
    print(f"   {mock_translated}")
    print(f"   Length: {len(mock_translated)} characters\n")

    # Post-processing: Reassemble translated content
    print("4. Post-processing: Reassembling translated content...")
    reassembled = reassemble_translated_content(mock_translated, original_entries)
    print(f"   Reassembled content:")
    print(f"   {reassembled}")
    print(f"   Length: {len(reassembled)} characters\n")

    # Verification
    print("5. Verification:")
    print(f"   - Original line count: {len(test_content.split(chr(10)))}")
    print(f"   - Reassembled line count: {len(reassembled.split(chr(10)))}")
    print(f"   - Structure preserved: {len(reassembled.split(chr(10))) == len(test_content.split(chr(10)))}")
    print(f"   - Character reduction in preprocessing: {len(test_content) - len(pure_text)} chars")
    print(f"   - Final output maintains original format: {'{' in reassembled and '}' in reassembled}")
    
    # Show the reassembled entries
    from loc_ast_parser import LocASTParser
    parser = LocASTParser()
    reassembled_entries = parser.parse_file(reassembled)
    print(f"   Reassembled entries:")
    for i, (key, value) in enumerate(reassembled_entries):
        print(f"     {i+1}. {key}: {repr(value)}")

def test_edge_cases():
    """测试边界情况"""
    print("\n\n=== Testing Edge Cases ===\n")
    
    # Test with already translated content (non-ASCII characters)
    print("1. Testing with already translated content:")
    translated_content = '''Achievement_ImmersiveMod_name { 铁 }
Plh_35 { 链条被牢固地固定 }'''
    pure_text, entries = extract_pure_game_text(translated_content)
    print(f"   Original: {translated_content}")
    print(f"   Pure text extracted: {repr(pure_text)}")
    print(f"   Should be empty: {len(pure_text) == 0}")
    
    # Test with mixed content
    print("\n2. Testing with mixed content (some translated, some not):")
    mixed_content = '''Achievement_ImmersiveMod_name { Iron }
Plh_35 { 链条被牢固地固定 }
LevelUp { You gained a level! }'''
    pure_text, entries = extract_pure_game_text(mixed_content)
    print(f"   Original: {mixed_content}")
    print(f"   Pure text extracted: {repr(pure_text)}")
    print(f"   Should contain only untranslated parts: {pure_text == 'Iron\\nYou gained a level!'}")

if __name__ == "__main__":
    test_complete_workflow()
    test_edge_cases()
    print("\n=== Test Completed ===")