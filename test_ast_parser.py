#!/usr/bin/env python3
"""
Test script for the LocASTParser
"""

from loc_ast_parser import LocASTParser

def test_basic_parsing():
    """Test basic parsing functionality"""
    print("=== Testing Basic Parsing ===")
    
    test_content = '''Achievement_ImmersiveMod_name { Iron }
Plh_35 { The chains are firmly affixed }
LevelUp { You gained a level!<br>Each time you gain a level, you are fully healed and receive 4 learning points.}
Plh_100 { Hello John, how are you today? }
Plh_200 { Meet Sarah at the Black Forest tavern. }'''

    parser = LocASTParser()
    print("Original content:")
    print(test_content)

    print("\n=== Parsed entries ===")
    entries = parser.parse_file(test_content)
    for key, value in entries:
        print(f"  {key}: {value}")

    print("\n=== Analysis ===")
    analysis = parser.analyze_translation_needs(entries)
    print(f"Entries to translate: {len(analysis['to_translate'])}")
    for key, value in analysis['to_translate']:
        print(f"  - {key}: {value}")

    print(f"\nExtracted names: {analysis['names']}")

    print("\n=== Name extraction test ===")
    print("Names from 'Hello John, how are you today?':", parser.extract_names('Hello John, how are you today?'))
    print("Names from 'Meet Sarah at the Black Forest tavern.':", parser.extract_names('Meet Sarah at the Black Forest tavern.'))

def test_serialization():
    """Test serialization functionality"""
    print("\n=== Testing Serialization ===")
    
    test_entries = [
        ("Achievement_ImmersiveMod_name", "Iron"),
        ("Plh_35", "The chains are firmly affixed"),
        ("LevelUp", "You gained a level!<br>Each time you gain a level, you are fully healed and receive 4 learning points.")
    ]
    
    parser = LocASTParser()
    serialized = parser.serialize_entries(test_entries)
    print("Serialized content:")
    print(serialized)

if __name__ == "__main__":
    test_basic_parsing()
    test_serialization()
    print("\n=== All tests completed successfully! ===")