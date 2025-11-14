"""
OpenAI Content Extractor Module
Uses OpenAI Vision API to extract tables and images from PNG page images
Focuses on 100% structure preservation and proper reading order
"""

import os
import base64
import json
from typing import List, Dict, Optional
from pathlib import Path
from openai import OpenAI


class OpenAIContentExtractor:
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        """
        Initialize OpenAI content extractor

        Args:
            api_key: OpenAI API key (default: reads from OPENAI_API_KEY env variable)
            model: OpenAI model to use (default: gpt-4o for vision capabilities)
        """
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 string for API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def extract_page_content(self, image_path: str, page_num: int) -> Dict:
        """
        Extract all content from a single page image with proper reading order

        Args:
            image_path: Path to the PNG image of the page
            page_num: Page number for reference

        Returns:
            Dictionary containing extracted content in reading order
        """
        print(f"\nExtracting content from page {page_num}...")

        base64_image = self.encode_image_to_base64(image_path)

        prompt = """Analyze this document page and extract ALL content in NATURAL READING ORDER (top to bottom, left to right).

CRITICAL REQUIREMENTS:

1. **READING ORDER**: Extract content in the EXACT order a human would read it
   - Start from top-left
   - Follow natural reading flow (top to bottom, left to right)
   - Handle multi-column layouts correctly (finish left column before right column)
   - Maintain logical sequence of headers, paragraphs, tables, images, captions

2. **TABLES**: Extract with 100% EXACT structure
   - Preserve all rows and columns IN ORDER
   - Maintain merged cells (rowspan/colspan)
   - Keep cell alignment and formatting
   - Output as clean HTML <table> with proper structure
   - Include table caption/title if present

3. **IMAGES/FIGURES/CHARTS/DIAGRAMS/SHAPES**:
   - Identify ALL visual elements including shapes, diagrams, and graphical content
   - **CRITICAL**: Treat ANY visual element (diagram, shape, drawing, flowchart, organizational chart, etc.) as an "image" type content block
   - **CRITICAL - Distinguish Pictures from Text Boxes**:
     * **Extract as IMAGE** if it has:
       - Colored backgrounds (not white/transparent)
       - Graphical elements (shapes, borders, icons, photos)
       - Visual design elements
       - Text overlaid on pictures/graphics
       - Example: Info box with blue background and text → IMAGE
       - Example: Photo with caption text on it → IMAGE
     * **Extract as TEXT** if it is:
       - Plain text on white/transparent background
       - Text box with no colored background
       - Simple text paragraph in a border
       - Example: Black text on white → TEXT (not image)
   - **Image Types:**
     * "chart" - Charts, graphs, plots (bar, line, pie, scatter, etc.)
     * "diagram" - Flowcharts, organizational charts, process diagrams, mind maps, technical drawings, schematics, shapes, geometric figures
     * "table_image" - Tables that are images (not extractable as HTML)
     * "photo" - Photographs, pictures, portraits
   - **BOUNDING BOX REQUIREMENTS**:
     * Provide bounding box as percentage: {x_start, y_start, x_end, y_end}
     * **FOR PICTURES WITH COLORED BACKGROUNDS**: Set bounding box to match the colored area boundary precisely
       - If picture has blue background, the bounding box should match where the blue area starts and ends
       - Do NOT expand beyond the visible colored/graphical boundary
       - Include text that is inside the colored area
     * **INCLUDE ALL RELATED TEXT**: The bounding box MUST include:
       - ALL labels within or attached to the diagram
       - ALL annotations describing parts of the diagram
       - ALL captions below or above the diagram (e.g., "Figure 1: ...", "Chart showing...")
       - ALL legends/keys that explain the diagram
       - ALL axis labels and tick labels for charts
       - ANY text that is visually part of or directly describes the diagram
       - Text overlaid on the picture/graphic itself
     * **EXCLUDE unrelated content**: Do NOT include surrounding paragraph text, other diagrams, or unrelated content
     * The bounding box should capture the COMPLETE visual element WITH all its associated text
   - Detailed description of content (what the diagram shows, what shapes represent)
   - **IMPORTANT**: ALL visual elements (charts, diagrams, shapes, photos - EVERYTHING) must be extracted and will be embedded in the output

4. **TEXT CONTENT**:
   - Extract ALL text blocks in reading order
   - Identify type: header (h1-h6), paragraph, list, caption, page_header, page_footer
   - **CRITICAL - Preserve Line Breaks**:
     * Retain ALL line breaks from the source exactly as they appear
     * Do NOT concatenate text across original newlines
     * Each line break in the PDF should be a \n character in the JSON content string
     * Multi-line paragraphs should preserve their line structure
   - Preserve formatting: bold, italic, underline
   - Note hierarchical level for headers

5. **HEADERS AND FOOTERS**:
   - **Page Header**: Content at very TOP of page (y_start < 10%) - typically page titles, document headers
   - **Page Footer**: Content at very BOTTOM of page (y_start > 90%) - typically page numbers, copyright, dates
   - Mark these with type "page_header" or "page_footer" (different from content headers)
   - Provide exact position percentages

6. **LAYOUT STRUCTURE**:
   - Number of columns
   - Margin sizes
   - Header/footer presence
   - Page orientation

OUTPUT FORMAT (JSON):
{
    "page_num": <number>,
    "content_items": [
        {
            "order": 1,
            "type": "header|paragraph|table|image|list|caption|page_header|page_footer",
            "content": "Text content with \\n for line breaks (PRESERVE all newlines from source)",
            "position": {
                "y_start": <percentage from top, 0-100>,
                "y_end": <percentage from top, 0-100>,
                "x_start": <percentage from left, 0-100>,
                "x_end": <percentage from left, 0-100>
            },
            "formatting": {
                "bold": true/false,
                "italic": true/false,
                "underline": true/false,
                "font_size": "small|normal|large|xlarge",
                "alignment": "left|center|right|justify"
            },
            "metadata": {
                "level": 1-6 (for headers),
                "caption": "caption text" (for tables/images),
                "description": "detailed description" (for images),
                "row_count": X (for tables),
                "column_count": Y (for tables),
                "image_index": X (for images - which image on the page, 1-indexed),
                "image_type": "chart|diagram|table_image|photo|logo|decoration" (for images)
            }
        }
    ],
    "layout": {
        "columns": 1 or 2,
        "has_header": true/false,
        "has_footer": true/false,
        "page_number": "X",
        "margin_top_percent": 10,
        "margin_bottom_percent": 10,
        "margin_left_percent": 8,
        "margin_right_percent": 8
    }
}

IMPORTANT NOTES:
- For tables: Use proper HTML with <table>, <thead>, <tbody>, <tr>, <th>, <td>
- Use colspan="X" and rowspan="Y" for merged cells
- Preserve exact cell content and structure
- Extract items in the ORDER they should be read (order field is critical!)
- Position values should be accurate percentages (0-100)
- Each content item must have accurate y_start and y_end for proper ordering

**CRITICAL - LINE BREAK PRESERVATION EXAMPLE**:
If the PDF shows:
  "Line 1
   Line 2
   Line 3"

Your JSON must be:
  "content": "Line 1\\nLine 2\\nLine 3"

NOT:
  "content": "Line 1 Line 2 Line 3"  ← WRONG! Do not concatenate across newlines!"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
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
                temperature=0  # Deterministic for accuracy
            )

            result = response.choices[0].message.content

            # Parse JSON response
            content = self._parse_json_response(result)
            content['page_num'] = page_num

            # Sort content items by reading order
            if 'content_items' in content:
                content['content_items'] = sorted(
                    content['content_items'],
                    key=lambda x: (x.get('order', 999), x.get('position', {}).get('y_start', 0))
                )

            # Convert to legacy format for compatibility
            legacy_content = self._convert_to_legacy_format(content)

            items_count = len(content.get('content_items', []))
            tables_count = sum(1 for item in content.get('content_items', []) if item.get('type') == 'table')
            images_count = sum(1 for item in content.get('content_items', []) if item.get('type') == 'image')

            print(f"  ✓ Extracted {items_count} content items in reading order")
            print(f"  ✓ Found {tables_count} tables, {images_count} images")

            return legacy_content

        except Exception as e:
            print(f"  ✗ Error extracting content from page {page_num}: {str(e)}")
            return {
                'page_num': page_num,
                'content_items': [],
                'tables': [],
                'images': [],
                'text_blocks': [],
                'layout': {},
                'error': str(e)
            }

    def _convert_to_legacy_format(self, content: Dict) -> Dict:
        """Convert new content format to legacy format for backward compatibility"""
        legacy = {
            'page_num': content.get('page_num', 1),
            'tables': [],
            'images': [],
            'text_blocks': [],
            'layout': content.get('layout', {}),
            'content_items': content.get('content_items', [])  # Keep new format too
        }

        # Convert content items to legacy format
        for item in content.get('content_items', []):
            item_type = item.get('type', 'paragraph')

            if item_type == 'table':
                legacy['tables'].append({
                    'html': item.get('content', ''),
                    'position': item.get('position', {}),
                    'caption': item.get('metadata', {}).get('caption', ''),
                    'row_count': item.get('metadata', {}).get('row_count', 0),
                    'column_count': item.get('metadata', {}).get('column_count', 0),
                    'order': item.get('order', 0)
                })
            elif item_type == 'image':
                legacy['images'].append({
                    'description': item.get('metadata', {}).get('description', ''),
                    'position': item.get('position', {}),
                    'caption': item.get('metadata', {}).get('caption', ''),
                    'order': item.get('order', 0),
                    'image_path': item.get('image_path', ''),  # Include image path for HTML
                    'metadata': item.get('metadata', {})  # Include full metadata
                })
            else:
                # Text blocks (header, paragraph, list, caption)
                legacy['text_blocks'].append({
                    'type': item_type,
                    'content': item.get('content', ''),
                    'position': item.get('position', {}),
                    'formatting': item.get('formatting', {}),
                    'level': item.get('metadata', {}).get('level', 1),
                    'order': item.get('order', 0)
                })

        return legacy

    def refine_table_structure(self, table_html: str, image_path: str) -> str:
        """
        Use a second pass to verify and refine table structure for 100% accuracy

        Args:
            table_html: Initial HTML table extracted
            image_path: Path to the page image for verification

        Returns:
            Refined HTML table with verified structure
        """
        print("  Refining table structure for accuracy...")

        base64_image = self.encode_image_to_base64(image_path)

        prompt = f"""I have extracted this HTML table from a document image:

{table_html}

Please verify this table structure against the actual image and provide a CORRECTED version if needed.

CRITICAL CHECKS:
1. Are all rows present?
2. Are all columns present?
3. Are merged cells correctly identified (colspan/rowspan)?
4. Is cell content accurate?
5. Are empty cells preserved?
6. Is alignment correct?

Respond with ONLY the corrected HTML table (no explanation), or the original table if it's already perfect.
The table must be complete, valid HTML with <table>, <thead>, <tbody>, <tr>, <th>, <td> tags."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
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
                max_tokens=2048,
                temperature=0
            )

            refined_html = response.choices[0].message.content.strip()

            # Extract table HTML if wrapped in markdown code blocks
            if refined_html.startswith('```'):
                lines = refined_html.split('\n')
                refined_html = '\n'.join(lines[1:-1]) if len(lines) > 2 else refined_html
                refined_html = refined_html.replace('```html', '').replace('```', '').strip()

            print("  ✓ Table structure refined")
            return refined_html

        except Exception as e:
            print(f"  ✗ Error refining table: {str(e)}")
            return table_html

    def _verify_table_structure(self, table: Dict) -> None:
        """Verify and fix common table structure issues"""
        html = table.get('html', '')

        if not html:
            return

        # Count actual rows and columns in HTML
        row_count = html.count('<tr')
        # Rough estimation of columns from first row
        first_row_match = html.split('</tr>')[0] if '</tr>' in html else html
        col_count = first_row_match.count('<td') + first_row_match.count('<th')

        # Update counts if not present
        if 'row_count' not in table or table['row_count'] == 0:
            table['row_count'] = row_count
        if 'column_count' not in table or table['column_count'] == 0:
            table['column_count'] = col_count

    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from OpenAI response, handling markdown code blocks"""
        # Remove markdown code block markers if present
        response = response.strip()
        if response.startswith('```'):
            # Remove first and last lines if they're code block markers
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
            print(f"  Attempting to fix JSON...")

            # Try to fix common JSON issues
            response = response.replace("'", '"')  # Replace single quotes
            response = response.replace('\n', ' ')  # Remove newlines
            response = response.strip()

            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Return minimal structure
                print(f"  ✗ Could not parse JSON response")
                return {
                    'content_items': [],
                    'tables': [],
                    'images': [],
                    'text_blocks': [],
                    'layout': {}
                }

    def save_extracted_content(self, content: Dict, output_path: str) -> str:
        """Save extracted content to JSON file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        print(f"  ✓ Content saved to: {output_path}")
        return str(output_path)


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract content from PDF page image using OpenAI')
    parser.add_argument('image_path', help='Path to PNG image of the page')
    parser.add_argument('--page-num', type=int, default=1, help='Page number')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env variable)')
    parser.add_argument('--model', default='gpt-4o', help='OpenAI model to use')
    parser.add_argument('--refine-tables', action='store_true', help='Use second pass to refine table extraction')

    args = parser.parse_args()

    # Create extractor
    extractor = OpenAIContentExtractor(api_key=args.api_key, model=args.model)

    # Extract content
    content = extractor.extract_page_content(args.image_path, args.page_num)

    # Optionally refine tables
    if args.refine_tables and content.get('tables'):
        print("\nRefining table structures...")
        for i, table in enumerate(content['tables']):
            if table.get('html'):
                refined_html = extractor.refine_table_structure(table['html'], args.image_path)
                content['tables'][i]['html'] = refined_html

    # Save to file
    if args.output:
        extractor.save_extracted_content(content, args.output)
    else:
        # Print to console
        print("\nExtracted Content:")
        print(json.dumps(content, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
