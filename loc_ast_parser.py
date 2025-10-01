import re
import json
from typing import Dict, List, Tuple, Optional

class LocASTParser:
    """
    AST Parser for Drova localization files (.loc)
    Handles the format: key { value }
    """
    
    def __init__(self):
        # Pattern to match key { value } entries
        # Handles multi-line values and escaped characters
        self.entry_pattern = re.compile(
            r'^([^{}\s]+)\s*\{\s*((?:[^{}]|\\{|\\}|\\n|\\"|\\\\)*?)\s*\}$',
            re.MULTILINE | re.DOTALL
        )
        
        # Pattern to find potential names/places for translation
        self.name_pattern = re.compile(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'  # Capitalized words (potential names)
        )
    
    def parse_file(self, content: str) -> List[Tuple[str, str]]:
        """
        Parse a .loc file content into key-value pairs
        
        Args:
            content: Raw content of the .loc file
            
        Returns:
            List of (key, value) tuples
        """
        entries = []
        lines = content.split('\n')
        current_key = None
        current_value = []
        in_entry = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line starts a new entry
            if '{' in line and not in_entry:
                parts = line.split('{', 1)
                if len(parts) == 2:
                    current_key = parts[0].strip()
                    value_part = parts[1].rstrip('}')
                    if value_part:
                        current_value.append(value_part)
                    in_entry = True
                    # Check if entry ends on same line
                    if '}' in line:
                        entries.append((current_key, ' '.join(current_value)))
                        current_key = None
                        current_value = []
                        in_entry = False
            elif in_entry:
                if '}' in line:
                    # Entry ends on this line
                    value_part = line.rstrip('}')
                    if value_part:
                        current_value.append(value_part)
                    entries.append((current_key, ' '.join(current_value)))
                    current_key = None
                    current_value = []
                    in_entry = False
                else:
                    # Continue collecting value
                    current_value.append(line)
        
        return entries
    
    def extract_names(self, text: str) -> List[str]:
        """
        Extract potential names and places from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of potential names/places
        """
        # Simple heuristic: look for capitalized words that might be names
        matches = self.name_pattern.findall(text)
        
        # Filter out common words and game-specific terms
        common_words = {
            'the', 'and', 'but', 'or', 'for', 'nor', 'so', 'yet', 'a', 'an', 'in', 'on', 
            'at', 'to', 'from', 'by', 'with', 'about', 'against', 'between', 'into', 
            'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down', 
            'of', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 
            'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 
            'just', 'should', 'now', 'dont', 'wont', 'cant', 'couldnt', 'wouldnt', 
            'shouldnt', 'isnt', 'arent', 'wasnt', 'werent', 'hasnt', 'havent', 
            'hadnt', 'doesnt', 'dont', 'didnt', 'wont', 'wouldnt', 'shouldnt', 
            'mightnt', 'mustnt', 'neednt', 'shant', 'that', 'this', 'these', 'those', 
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 
            'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'may', 
            'might', 'must', 'can', 'could', 'its', 'hers', 'his', 'theirs', 'ours', 
            'yours', 'mine', 'myself', 'yourself', 'himself', 'herself', 'itself', 
            'ourselves', 'yourselves', 'themselves', 'what', 'which', 'who', 'whom', 
            'whose', 'whatever', 'whichever', 'whoever', 'whomever', 'when', 'where', 
            'why', 'how', 'whenever', 'wherever', 'however', 'whether', 'while', 
            'though', 'although', 'even', 'if', 'unless', 'until', 'till', 'than', 
            'rather', 'whether', 'like', 'as', 'because', 'since', 'so', 'that', 
            'such', 'than', 'too', 'very', 'just', 'still', 'already', 'yet', 
            'really', 'quite', 'almost', 'nearly', 'enough', 'too', 'so', 'such', 
            'more', 'most', 'less', 'least', 'much', 'many', 'few', 'little', 
            'some', 'any', 'no', 'all', 'both', 'each', 'every', 'either', 'neither', 
            'another', 'other', 'such', 'what', 'which', 'who', 'whom', 'whose', 
            'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 
            'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs', 'myself', 
            'yourself', 'himself', 'herself', 'itself', 'ourselves', 'yourselves', 
            'themselves'
        }
        
        # Filter out common words and short names
        filtered_names = []
        for name in matches:
            if (len(name) > 2 and 
                name.lower() not in common_words and
                not name.isupper()):  # Skip all-caps acronyms
                filtered_names.append(name)
        
        return list(set(filtered_names))  # Remove duplicates
    
    def format_entry(self, key: str, value: str) -> str:
        """
        Format a key-value pair back into .loc format
        
        Args:
            key: The key
            value: The value
            
        Returns:
            Formatted string in .loc format
        """
        # Escape special characters if needed
        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
        return f"{key} {{ {escaped_value} }}"
    
    def serialize_entries(self, entries: List[Tuple[str, str]]) -> str:
        """
        Serialize parsed entries back to .loc format
        
        Args:
            entries: List of (key, value) tuples
            
        Returns:
            String in .loc format
        """
        return '\n'.join([self.format_entry(k, v) for k, v in entries])
    
    def analyze_translation_needs(self, entries: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        """
        Analyze which entries need translation and extract names
        
        Args:
            entries: List of (key, value) tuples
            
        Returns:
            Dict with 'to_translate' and 'names' keys
        """
        to_translate = []
        all_names = []
        
        for key, value in entries:
            # Check if value contains non-ASCII characters (already translated)
            if not any(ord(c) > 127 for c in value):
                to_translate.append((key, value))
            
            # Extract names from both key and value
            names_from_key = self.extract_names(key)
            names_from_value = self.extract_names(value)
            all_names.extend(names_from_key + names_from_value)
        
        return {
            'to_translate': to_translate,
            'names': list(set(all_names))  # Remove duplicates
        }


# Utility functions for integration
def parse_loc_content(content: str) -> List[Tuple[str, str]]:
    """Parse .loc file content"""
    parser = LocASTParser()
    return parser.parse_file(content)


def extract_translation_candidates(content: str) -> Dict[str, List[str]]:
    """Extract translation candidates and names from content"""
    parser = LocASTParser()
    entries = parser.parse_file(content)
    return parser.analyze_translation_needs(entries)


def serialize_to_loc_format(entries: List[Tuple[str, str]]) -> str:
    """Serialize entries back to .loc format"""
    parser = LocASTParser()
    return parser.serialize_entries(entries)


if __name__ == "__main__":
    # Test the parser
    test_content = """
    Achievement_ImmersiveMod_name { Iron }
    Plh_35 { The chains are firmly aff" }
    LevelUp { You gained a level!<br>Each time you gain a level, you are fully healed and receive 4 learning points.<br>If you find a mentor, you can use learning points to increase your ability scores and learn new talents.<br>Some talents, even weapons, require mastery.<br>Mastery is the sum of all your attribute scores.}
    """
    
    parser = LocASTParser()
    entries = parser.parse_file(test_content)
    print("Parsed entries:")
    for key, value in entries:
        print(f"  {key}: {value}")
    
    analysis = parser.analyze_translation_needs(entries)
    print(f"\nTranslation candidates: {len(analysis['to_translate'])}")
    print(f"Extracted names: {analysis['names']}")