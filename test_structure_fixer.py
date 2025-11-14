"""
Test script for Content Structure Fixer
Validates that section-table ordering is fixed correctly
"""

import json
from content_structure_fixer import ContentStructureFixer


def test_section_table_fix():
    """Test fixing section-table ordering"""

    # Simulated extracted content with table before section heading
    test_content = {
        "page_num": 2,
        "content_items": [
            {
                "order": 1,
                "type": "header",
                "content": "Pacer Energy Marketing, LLC\nDivision Order Title Opinion\nJ. Z. #24-1 Well\nNovember 23, 2009\nPage 2",
                "position": {"y_start": 2, "y_end": 8}
            },
            {
                "order": 2,
                "type": "table",
                "content": "<table><thead><tr><th>OWNERS</th><th>NUMBER OF MINERAL ACRES</th><th>OIL & GAS LEASE</th></tr></thead><tbody><tr><td>1. Louise Ann Guthrie</td><td>13.3333</td><td>A</td></tr></tbody></table>",
                "html": "<table><thead><tr><th>OWNERS</th><th>NUMBER OF MINERAL ACRES</th><th>OIL & GAS LEASE</th></tr></thead><tbody><tr><td>1. Louise Ann Guthrie</td><td>13.3333</td><td>A</td></tr></tbody></table>",
                "position": {"y_start": 15, "y_end": 35}
            },
            {
                "order": 3,
                "type": "header",
                "content": "II. MINERAL OWNERSHIP:",
                "position": {"y_start": 40, "y_end": 45}
            },
            {
                "order": 4,
                "type": "header",
                "content": "III. BASE OIL AND GAS LEASES:",
                "position": {"y_start": 50, "y_end": 55}
            }
        ]
    }

    print("=" * 70)
    print("TEST: Section-Table Ordering Fix")
    print("=" * 70)

    print("\n📋 BEFORE Fix:")
    print("-" * 70)
    for i, item in enumerate(test_content['content_items']):
        item_type = item['type']
        content_preview = item.get('content', item.get('html', ''))[:60]
        print(f"  {i+1}. [{item_type.upper()}] {content_preview}...")

    # Apply fix
    fixer = ContentStructureFixer()
    fixed_content = fixer.fix_content_structure(test_content)

    print("\n✅ AFTER Fix:")
    print("-" * 70)
    for i, item in enumerate(fixed_content['content_items']):
        item_type = item['type']
        content_preview = item.get('content', item.get('html', ''))[:60]
        print(f"  {i+1}. [{item_type.upper()}] {content_preview}...")

    # Validate fix
    print("\n🔍 Validation:")
    print("-" * 70)

    # Check that section header now comes before table
    section_idx = None
    table_idx = None

    for i, item in enumerate(fixed_content['content_items']):
        if item.get('content') == "II. MINERAL OWNERSHIP:":
            section_idx = i
        if item.get('type') == 'table':
            table_idx = i

    if section_idx is not None and table_idx is not None:
        if section_idx < table_idx:
            print("✅ PASS: Section header now appears BEFORE table")
            print(f"   Section index: {section_idx}, Table index: {table_idx}")
        else:
            print("❌ FAIL: Section header still after table")
            print(f"   Section index: {section_idx}, Table index: {table_idx}")
    else:
        print("❌ FAIL: Could not find section or table")

    print("\n" + "=" * 70)
    return fixed_content


def test_header_hierarchy():
    """Test header hierarchy detection"""

    test_content = {
        "page_num": 1,
        "content_items": [
            {
                "type": "header",
                "content": "I. INTRODUCTION",
                "position": {"y_start": 10, "y_end": 15}
            },
            {
                "type": "header",
                "content": "II. MINERAL OWNERSHIP:",
                "position": {"y_start": 20, "y_end": 25}
            },
            {
                "type": "header",
                "content": "1. Overview",
                "position": {"y_start": 30, "y_end": 35}
            }
        ]
    }

    print("\n" + "=" * 70)
    print("TEST: Header Hierarchy")
    print("=" * 70)

    fixer = ContentStructureFixer()
    fixed_content = fixer.fix_header_hierarchy(test_content)

    print("\n✅ Headers with assigned levels:")
    print("-" * 70)
    for item in fixed_content['content_items']:
        if item['type'] == 'header':
            level = item.get('metadata', {}).get('level', 'Not set')
            content = item['content']
            print(f"  Level {level}: {content}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n🧪 Running Content Structure Fixer Tests\n")

    # Test 1: Section-Table ordering
    fixed = test_section_table_fix()

    # Test 2: Header hierarchy
    test_header_hierarchy()

    print("\n✅ All tests completed!\n")
