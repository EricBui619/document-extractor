"""
OpenAI Content Extractor with Multi-Page Context
Handles content that spans multiple pages (tables, paragraphs, etc.)
"""

import os
import base64
import json
from typing import List, Dict, Optional
from pathlib import Path
from openai import OpenAI


class MultiPageContentExtractor:
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        """
        Initialize multi-page content extractor

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model
        self.previous_page_context = None

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def extract_with_context(self, image_path: str, page_num: int,
                           previous_page_summary: Optional[str] = None) -> Dict:
        """
        Extract page content with awareness of previous page context

        Args:
            image_path: Path to page PNG
            page_num: Page number
            previous_page_summary: Summary of content from previous page

        Returns:
            Dictionary with extracted content and continuation info
        """
        print(f"\nExtracting page {page_num} with context awareness...")

        base64_image = self.encode_image_to_base64(image_path)

        # Build context-aware prompt
        context_info = ""
        if previous_page_summary:
            context_info = f"""
IMPORTANT CONTEXT FROM PREVIOUS PAGE:
{previous_page_summary}

NOTE: If this page continues content from the previous page (e.g., a table, paragraph, or section),
mark it as "continuation: true" and include the continuation_of field to link it."""

        prompt = f"""Analyze this document page (Page {page_num}) and extract ALL content with FULL CONTEXT AWARENESS.

{context_info}

CRITICAL REQUIREMENTS:

1. **CONTENT CONTINUATION DETECTION**:
   - Check if this page CONTINUES content from previous page (tables, paragraphs, lists)
   - If content continues, mark with "continuation: true" and "continuation_of: ID"
   - If content will CONTINUE on next page, mark with "continues_next_page: true"
   - Extract partial content accurately but note it's incomplete

2. **READING ORDER**:
   - Extract in natural reading order (top to bottom, left to right)
   - Assign sequential order numbers (1, 2, 3...)
   - Handle multi-column correctly

3. **TABLES - SPECIAL ATTENTION**:
   - If table starts on previous page and continues here, mark as continuation
   - Extract visible rows/columns on THIS page accurately
   - Note if table continues to next page
   - Include partial table caption if visible

4. **PARAGRAPHS**:
   - If paragraph starts on previous page, mark as continuation
   - Extract text visible on this page
   - Note if paragraph continues to next page

5. **LISTS**:
   - If list continues from previous page, mark as continuation
   - Extract items visible on this page
   - Note if list continues

OUTPUT FORMAT (JSON):
{{
    "page_num": {page_num},
    "content_items": [
        {{
            "id": "unique_id_for_this_item",
            "order": 1,
            "type": "header|paragraph|table|image|list|caption",
            "content": "Content visible on this page",
            "continuation": false,
            "continuation_of": "id_from_previous_page",
            "continues_next_page": false,
            "position": {{
                "y_start": 0-100,
                "y_end": 0-100,
                "x_start": 0-100,
                "x_end": 0-100
            }},
            "formatting": {{
                "bold": true/false,
                "italic": true/false,
                "alignment": "left|center|right|justify"
            }},
            "metadata": {{
                "level": 1-6,
                "caption": "text",
                "description": "text",
                "row_count": X,
                "column_count": Y,
                "partial_content": true/false
            }}
        }}
    ],
    "layout": {{
        "columns": 1,
        "has_header": true/false,
        "has_footer": true/false
    }},
    "page_summary": "Brief summary of main content on this page (for next page context)"
}}

EXAMPLES OF CONTINUATION:

Table spanning pages:
Page 1: Table with rows 1-10, "continues_next_page: true"
Page 2: "continuation: true, continuation_of: table_id_from_page1", rows 11-20

Paragraph spanning pages:
Page 1: Paragraph ending mid-sentence, "continues_next_page: true"
Page 2: "continuation: true", paragraph continues from previous

For tables: Use HTML <table> format. Extract EXACTLY what's visible on this page.
For continuations: Link back to original using continuation_of field."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0
            )

            result = response.choices[0].message.content
            content = self._parse_json_response(result)
            content['page_num'] = page_num

            # Store summary for next page
            self.previous_page_context = content.get('page_summary', '')

            items_count = len(content.get('content_items', []))
            continuations = sum(1 for item in content.get('content_items', [])
                              if item.get('continuation', False))

            print(f"  ✓ Extracted {items_count} items ({continuations} continuations)")

            return content

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            return {
                'page_num': page_num,
                'content_items': [],
                'layout': {},
                'page_summary': '',
                'error': str(e)
            }

    def merge_continued_content(self, pages_content: List[Dict]) -> Dict:
        """
        Merge content that spans multiple pages into complete items

        Args:
            pages_content: List of extracted content from all pages

        Returns:
            Dictionary with merged content items
        """
        print("\nMerging multi-page content...")

        merged_items = []
        item_map = {}  # Track items by ID for continuation linking

        for page_content in pages_content:
            for item in page_content.get('content_items', []):
                item_id = item.get('id', f"page{page_content['page_num']}_item{item.get('order', 0)}")

                if item.get('continuation', False):
                    # This item continues from previous page
                    parent_id = item.get('continuation_of')

                    if parent_id and parent_id in item_map:
                        # Merge with parent item
                        parent_item = item_map[parent_id]

                        if item['type'] == 'table':
                            # Merge table rows
                            parent_item['content'] = self._merge_table_html(
                                parent_item['content'],
                                item['content']
                            )
                            parent_item['metadata']['row_count'] = (
                                parent_item['metadata'].get('row_count', 0) +
                                item['metadata'].get('row_count', 0)
                            )
                        elif item['type'] in ['paragraph', 'list']:
                            # Concatenate text content
                            parent_item['content'] += ' ' + item['content']

                        # Update continuation status
                        parent_item['continues_next_page'] = item.get('continues_next_page', False)
                        parent_item['pages'].append(page_content['page_num'])

                    else:
                        # Parent not found, treat as standalone
                        item['pages'] = [page_content['page_num']]
                        merged_items.append(item)
                        item_map[item_id] = item
                else:
                    # New item (not a continuation)
                    item['pages'] = [page_content['page_num']]
                    merged_items.append(item)
                    item_map[item_id] = item

        print(f"  ✓ Merged into {len(merged_items)} complete items")

        return {
            'merged_items': merged_items,
            'total_pages': len(pages_content),
            'item_map': item_map
        }

    def _merge_table_html(self, table1: str, table2: str) -> str:
        """
        Merge two partial table HTMLs into one complete table

        Args:
            table1: HTML from first page (header + partial rows)
            table2: HTML from continuation (partial rows)

        Returns:
            Combined table HTML
        """
        # Extract tbody content from second table
        import re

        # Find all <tr> tags in table2 (excluding thead if present)
        tbody_pattern = r'<tbody>(.*?)</tbody>'
        tbody_match = re.search(tbody_pattern, table2, re.DOTALL)

        if tbody_match:
            tbody_rows = tbody_match.group(1)
        else:
            # No tbody, extract all rows except thead
            rows_pattern = r'<tr>.*?</tr>'
            all_rows = re.findall(rows_pattern, table2, re.DOTALL)
            tbody_rows = '\n'.join(all_rows)

        # Insert into table1 before closing </tbody> or </table>
        if '</tbody>' in table1:
            merged = table1.replace('</tbody>', f'{tbody_rows}\n</tbody>')
        else:
            merged = table1.replace('</table>', f'{tbody_rows}\n</table>')

        return merged

    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from OpenAI response"""
        response = response.strip()

        # Remove markdown code blocks
        if response.startswith('```'):
            lines = response.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response = '\n'.join(lines)
            response = response.replace('```json', '').replace('```', '').strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"  ⚠ JSON parse error: {str(e)}")

            # Try to fix common issues
            response = response.replace("'", '"')
            response = response.strip()

            try:
                return json.loads(response)
            except json.JSONDecodeError:
                print(f"  ✗ Could not parse JSON")
                return {
                    'content_items': [],
                    'layout': {},
                    'page_summary': ''
                }

    def save_extracted_content(self, content: Dict, output_path: str) -> str:
        """Save extracted content to JSON"""
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        return str(output_path)


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract multi-page content with context')
    parser.add_argument('image_paths', nargs='+', help='Paths to PNG images (in order)')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--api-key', help='OpenAI API key')

    args = parser.parse_args()

    extractor = MultiPageContentExtractor(api_key=args.api_key)

    # Extract all pages with context
    all_pages_content = []
    previous_summary = None

    for i, image_path in enumerate(args.image_paths, 1):
        content = extractor.extract_with_context(image_path, i, previous_summary)
        all_pages_content.append(content)
        previous_summary = content.get('page_summary', '')

    # Merge continued content
    merged_content = extractor.merge_continued_content(all_pages_content)

    # Save
    if args.output:
        extractor.save_extracted_content(merged_content, args.output)
        print(f"\n✓ Saved to: {args.output}")
    else:
        print("\nMerged Content:")
        print(json.dumps(merged_content, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
