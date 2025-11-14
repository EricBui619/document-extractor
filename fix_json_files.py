"""
Fix JSON files that have parsing errors
Recovers data from raw_response field
"""

import json
import re
from pathlib import Path
import sys

def fix_json_file(file_path):
    """Fix a single JSON file"""
    print(f"Processing: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check if it has raw_response (indicating a parsing error)
    if 'raw_response' in data and data['raw_response']:
        print(f"  Found raw_response, attempting to parse...")

        raw_text = data['raw_response']

        try:
            # Fix escape sequences
            # Remove backslashes that aren't part of valid escape sequences
            fixed_text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw_text)

            # Remove control characters
            fixed_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', fixed_text)

            # Try to parse
            parsed_data = json.loads(fixed_text)

            # Update the file with parsed data
            parsed_data['page_num'] = data['page_num']

            # Save back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)

            print(f"  ✓ Fixed! Extracted {len(parsed_data.get('tables', []))} tables, "
                  f"{len(parsed_data.get('images', []))} images, "
                  f"{len(parsed_data.get('text_blocks', []))} text blocks")
            return True

        except Exception as e:
            print(f"  ✗ Could not fix: {e}")
            return False
    else:
        print(f"  ℹ  File is OK (no raw_response field)")
        return True

def fix_directory(directory):
    """Fix all JSON files in a directory"""
    directory = Path(directory)
    json_files = list(directory.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {directory}")
        return

    print(f"\nFound {len(json_files)} JSON files\n")

    fixed = 0
    errors = 0

    for json_file in json_files:
        if fix_json_file(json_file):
            fixed += 1
        else:
            errors += 1
        print()

    print(f"\nSummary: {fixed} fixed, {errors} errors")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_json_files.py <directory>")
        print("Example: python fix_json_files.py output/20251113_004401/extracted_content/")
        sys.exit(1)

    directory = sys.argv[1]
    fix_directory(directory)
