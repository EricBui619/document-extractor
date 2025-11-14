"""
Content Structure Fixer Module
Fixes common structural issues in extracted content, particularly section-table associations
"""

from typing import Dict, List
import re


class ContentStructureFixer:
    """Fix structural issues in extracted content"""

    def __init__(self):
        """Initialize the fixer"""
        pass

    def fix_section_table_order(self, content: Dict) -> Dict:
        """
        Fix cases where tables appear before their section headings

        Common issue: A table is extracted before its section heading due to
        vertical position, but logically belongs to that section.

        Example:
            BEFORE: [table data] → "II. MINERAL OWNERSHIP:"
            AFTER:  "II. MINERAL OWNERSHIP:" → [table data]

        Args:
            content: Extracted content dictionary

        Returns:
            Fixed content dictionary with proper section-table order
        """
        if 'content_items' not in content:
            return content

        items = content['content_items']
        if len(items) < 2:
            return content

        fixed_items = []
        i = 0

        while i < len(items):
            current = items[i]

            # Check if current item is a table
            if current.get('type') == 'table':
                # Look ahead for a section heading (within next 2 items)
                section_header_idx = None
                for j in range(i + 1, min(i + 3, len(items))):
                    next_item = items[j]
                    if next_item.get('type') in ['header', 'paragraph']:
                        content_text = next_item.get('content', '')
                        # Check if it's a numbered section (I., II., III., etc.)
                        if re.match(r'^[IVX]+\.|^\d+\.', content_text.strip()):
                            section_header_idx = j
                            break

                # If we found a section header after the table, swap them
                if section_header_idx is not None:
                    print(f"  ⚙ Fixing: Moving section header before table")
                    section_header = items[section_header_idx]

                    # Add the section header first
                    fixed_items.append(section_header)

                    # Then add any items between table and header (if any)
                    for k in range(i, section_header_idx):
                        if k != i:  # Don't add the table yet
                            fixed_items.append(items[k])

                    # Finally add the table
                    fixed_items.append(current)

                    # Move index past all processed items
                    i = section_header_idx + 1
                else:
                    # No section header found, keep table as is
                    fixed_items.append(current)
                    i += 1
            else:
                # Not a table, keep as is
                fixed_items.append(current)
                i += 1

        content['content_items'] = fixed_items
        return content

    def fix_header_hierarchy(self, content: Dict) -> Dict:
        """
        Ensure headers have proper hierarchy and metadata

        Args:
            content: Extracted content dictionary

        Returns:
            Fixed content with proper header levels
        """
        if 'content_items' not in content:
            return content

        for item in content['content_items']:
            if item.get('type') == 'header':
                text = item.get('content', '')

                # Detect section numbers and assign appropriate levels
                if re.match(r'^[IVX]+\.', text.strip()):
                    # Roman numeral sections (I., II., III.) → Level 2
                    item.setdefault('metadata', {})['level'] = 2
                elif re.match(r'^\d+\.', text.strip()):
                    # Arabic numeral sections (1., 2., 3.) → Level 3
                    item.setdefault('metadata', {})['level'] = 3
                else:
                    # Default level
                    item.setdefault('metadata', {})['level'] = item.get('metadata', {}).get('level', 1)

        return content

    def merge_split_tables(self, content: Dict) -> Dict:
        """
        Merge tables that were incorrectly split across extractions

        Args:
            content: Extracted content dictionary

        Returns:
            Fixed content with merged tables
        """
        if 'content_items' not in content:
            return content

        items = content['content_items']
        fixed_items = []
        i = 0

        while i < len(items):
            current = items[i]

            # Check if current and next items are both tables
            if (current.get('type') == 'table' and
                i + 1 < len(items) and
                items[i + 1].get('type') == 'table'):

                # Check if they're close vertically (within 5% of page height)
                current_pos = current.get('position', {})
                next_pos = items[i + 1].get('position', {})

                current_y_end = current_pos.get('y_end', 0)
                next_y_start = next_pos.get('y_start', 100)

                if abs(next_y_start - current_y_end) < 5:
                    print(f"  ⚙ Merging adjacent tables")
                    # Merge the tables
                    current_html = current.get('html', '')
                    next_html = items[i + 1].get('html', '')

                    # Simple merge: combine table bodies
                    # Remove closing </table> from first, opening <table> tags from second
                    merged_html = current_html.replace('</table>', '')
                    next_html_body = re.sub(r'^.*?<tbody>', '<tbody>', next_html, flags=re.DOTALL)
                    merged_html += next_html_body

                    current['html'] = merged_html
                    current['position']['y_end'] = next_pos.get('y_end', current_y_end)

                    fixed_items.append(current)
                    i += 2  # Skip next table
                else:
                    fixed_items.append(current)
                    i += 1
            else:
                fixed_items.append(current)
                i += 1

        content['content_items'] = fixed_items
        return content

    def fix_content_structure(self, content: Dict) -> Dict:
        """
        Apply all structural fixes to content

        Args:
            content: Extracted content dictionary

        Returns:
            Fixed content dictionary
        """
        print(f"  🔧 Applying structural fixes...")

        # Apply fixes in order
        content = self.fix_section_table_order(content)
        content = self.fix_header_hierarchy(content)
        content = self.merge_split_tables(content)

        print(f"  ✓ Structural fixes applied")
        return content


def main():
    """Example usage"""
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python content_structure_fixer.py <content.json>")
        sys.exit(1)

    # Load content
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        content = json.load(f)

    # Fix structure
    fixer = ContentStructureFixer()
    fixed_content = fixer.fix_content_structure(content)

    # Save fixed content
    output_path = sys.argv[1].replace('.json', '_fixed.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fixed_content, f, indent=2, ensure_ascii=False)

    print(f"Fixed content saved to: {output_path}")


if __name__ == "__main__":
    main()
