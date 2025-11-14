"""
HTML Page Generator Module V2
Generates readable HTML pages from extracted content with proper reading flow
"""

import os
from pathlib import Path
from typing import List, Dict
import base64


class HTMLPageGenerator:
    def __init__(self, page_width: float = 612, page_height: float = 792):
        """
        Initialize HTML page generator

        Args:
            page_width: Page width in points (default: 612 = 8.5 inches)
            page_height: Page height in points (default: 792 = 11 inches)
        """
        self.page_width = page_width
        self.page_height = page_height

    def generate_page_html(self, content: Dict, page_info: Dict, output_path: str = None) -> str:
        """
        Generate HTML for a single page with proper reading order

        Args:
            content: Extracted content from OpenAI
            page_info: Page information from PDF converter
            output_path: Path to save HTML file

        Returns:
            Path to the generated HTML file
        """
        page_num = content.get('page_num', 1)
        print(f"\nGenerating readable HTML for page {page_num}...")

        # Update page dimensions
        if page_info:
            self.page_width = page_info.get('original_width', self.page_width)
            self.page_height = page_info.get('original_height', self.page_height)

        # Generate HTML content
        html_content = self._build_html(content, page_info)

        # Determine output path
        if output_path is None:
            output_dir = Path("output/html_pages")
            output_dir.mkdir(exist_ok=True, parents=True)
            output_path = output_dir / f"page_{page_num}.html"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(exist_ok=True, parents=True)

        # Write HTML to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"  ✓ Readable HTML saved to: {output_path}")
        return str(output_path)

    def _build_html(self, content: Dict, page_info: Dict) -> str:
        """Build complete HTML document with proper reading flow"""
        page_num = content.get('page_num', 1)
        layout = content.get('layout', {})

        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>Page {page_num}</title>',
            self._generate_css(layout),
            '</head>',
            '<body>',
            f'    <div class="page">',
        ]

        # Check if we have new format with content_items
        if 'content_items' in content and content['content_items']:
            # New format: render in reading order
            html_parts.append(self._render_content_items_flow(content['content_items'], page_info))
        else:
            # Legacy format: try to extract reading order
            html_parts.append(self._render_legacy_improved(content, page_info))

        # Close HTML
        html_parts.extend([
            '    </div>',
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)

    def _render_content_items_flow(self, content_items: List[Dict], page_info: Dict) -> str:
        """Render content items in natural reading flow"""
        html_parts = []

        # Sort by order and position
        sorted_items = sorted(
            content_items,
            key=lambda x: (x.get('order', 999), x.get('position', {}).get('y_start', 0))
        )

        for item in sorted_items:
            item_type = item.get('type', 'paragraph')

            if item_type == 'header':
                html_parts.append(self._render_header(item))
            elif item_type == 'paragraph':
                html_parts.append(self._render_paragraph(item))
            elif item_type == 'table':
                html_parts.append(self._render_table(item))
            elif item_type == 'image':
                html_parts.append(self._render_image(item))
            elif item_type == 'list':
                html_parts.append(self._render_list(item))
            elif item_type == 'caption':
                html_parts.append(self._render_caption(item))
            else:
                # Unknown type, treat as paragraph
                html_parts.append(self._render_paragraph(item))

        return '\n'.join(html_parts)

    def _render_header(self, item: Dict) -> str:
        """Render header element"""
        content = item.get('content', '')
        metadata = item.get('metadata', {})
        formatting = item.get('formatting', {})

        level = metadata.get('level', 1)
        level = max(1, min(6, level))  # Clamp to 1-6

        formatted_content = self._apply_formatting(content, formatting)
        alignment = formatting.get('alignment', 'left')

        return f'        <h{level} style="text-align: {alignment};">{formatted_content}</h{level}>'

    def _render_paragraph(self, item: Dict) -> str:
        """Render paragraph element"""
        content = item.get('content', '')
        formatting = item.get('formatting', {})

        formatted_content = self._apply_formatting(content, formatting)
        alignment = formatting.get('alignment', 'justify')

        return f'        <p style="text-align: {alignment};">{formatted_content}</p>'

    def _render_table(self, item: Dict) -> str:
        """Render table element"""
        table_html = item.get('content', '')
        metadata = item.get('metadata', {})
        caption = metadata.get('caption', '')

        parts = ['        <div class="table-container">']

        if caption:
            parts.append(f'            <div class="table-caption">{caption}</div>')

        parts.append(f'            {table_html}')
        parts.append('        </div>')

        return '\n'.join(parts)

    def _render_image(self, item: Dict) -> str:
        """Render image placeholder"""
        metadata = item.get('metadata', {})
        description = metadata.get('description', 'Image')
        caption = metadata.get('caption', '')

        parts = [
            '        <div class="image-container">',
            '            <div class="image-placeholder">',
            f'                <p class="image-description">{description}</p>',
            '            </div>'
        ]

        if caption:
            parts.append(f'            <p class="image-caption">{caption}</p>')

        parts.append('        </div>')

        return '\n'.join(parts)

    def _render_list(self, item: Dict) -> str:
        """Render list element"""
        content = item.get('content', '')
        formatting = item.get('formatting', {})
        metadata = item.get('metadata', {})

        # Split into items if content contains newlines
        items = [line.strip() for line in content.split('\n') if line.strip()]

        list_type = metadata.get('list_type', 'unordered')
        tag = 'ul' if list_type == 'unordered' else 'ol'

        parts = [f'        <{tag}>']
        for list_item in items:
            formatted = self._apply_formatting(list_item, formatting)
            parts.append(f'            <li>{formatted}</li>')
        parts.append(f'        </{tag}>')

        return '\n'.join(parts)

    def _render_caption(self, item: Dict) -> str:
        """Render caption element"""
        content = item.get('content', '')
        formatting = item.get('formatting', {})

        formatted_content = self._apply_formatting(content, formatting)
        return f'        <p class="caption">{formatted_content}</p>'

    def _apply_formatting(self, content: str, formatting: Dict) -> str:
        """Apply text formatting"""
        if not formatting:
            return content

        if formatting.get('bold'):
            content = f'<strong>{content}</strong>'
        if formatting.get('italic'):
            content = f'<em>{content}</em>'
        if formatting.get('underline'):
            content = f'<u>{content}</u>'

        return content

    def _render_legacy_improved(self, content: Dict, page_info: Dict) -> str:
        """Render legacy format with improved ordering"""
        all_items = []

        # Collect all elements with order/position
        for text_block in content.get('text_blocks', []):
            order = text_block.get('order', 999)
            pos = text_block.get('position', {})
            y_pos = pos.get('y_start', pos.get('top_percent', 0))
            all_items.append(('text', text_block, order, y_pos))

        for table in content.get('tables', []):
            order = table.get('order', 999)
            pos = table.get('position', {})
            y_pos = pos.get('y_start', pos.get('top_percent', 0))
            all_items.append(('table', table, order, y_pos))

        for image in content.get('images', []):
            order = image.get('order', 999)
            pos = image.get('position', {})
            y_pos = pos.get('y_start', pos.get('top_percent', 0))
            all_items.append(('image', image, order, y_pos))

        # Sort by order, then position
        all_items.sort(key=lambda x: (x[2], x[3]))

        # Render in order
        parts = []
        for elem_type, elem, _, _ in all_items:
            if elem_type == 'text':
                parts.append(self._render_text_block(elem))
            elif elem_type == 'table':
                parts.append(self._render_table_legacy(elem))
            elif elem_type == 'image':
                parts.append(self._render_image_legacy(elem))

        return '\n'.join(parts)

    def _render_text_block(self, text_block: Dict) -> str:
        """Render text block (legacy)"""
        block_type = text_block.get('type', 'paragraph')
        content = text_block.get('content', '')
        formatting = text_block.get('formatting', {})

        # Convert list format if needed
        if isinstance(formatting, list):
            formatting = {
                'bold': 'bold' in formatting,
                'italic': 'italic' in formatting,
                'underline': 'underline' in formatting
            }

        formatted = self._apply_formatting(content, formatting)

        if block_type == 'header':
            level = text_block.get('level', 1)
            return f'        <h{level}>{formatted}</h{level}>'
        elif block_type == 'list':
            items = [line.strip() for line in content.split('\n') if line.strip()]
            html = '        <ul>'
            for item in items:
                html += f'\n            <li>{self._apply_formatting(item, formatting)}</li>'
            html += '\n        </ul>'
            return html
        else:
            return f'        <p>{formatted}</p>'

    def _render_table_legacy(self, table: Dict) -> str:
        """Render table (legacy)"""
        table_html = table.get('html', '')
        caption = table.get('caption', '')

        parts = ['        <div class="table-container">']
        if caption:
            parts.append(f'            <div class="table-caption">{caption}</div>')
        parts.append(f'            {table_html}')
        parts.append('        </div>')

        return '\n'.join(parts)

    def _render_image_legacy(self, image: Dict) -> str:
        """Render image (legacy)"""
        description = image.get('description', 'Image')
        caption = image.get('caption', '')

        parts = [
            '        <div class="image-container">',
            '            <div class="image-placeholder">',
            f'                <p class="image-description">{description}</p>',
            '            </div>'
        ]

        if caption:
            parts.append(f'            <p class="image-caption">{caption}</p>')

        parts.append('        </div>')

        return '\n'.join(parts)

    def _generate_css(self, layout: Dict) -> str:
        """Generate modern, readable CSS"""
        columns = layout.get('columns', 1)

        return f'''    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Georgia', 'Times New Roman', Times, serif;
            background-color: #f5f5f5;
            padding: 20px;
            line-height: 1.8;
            color: #333;
        }}

        .page {{
            background-color: white;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 1in;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            {f'column-count: {columns};' if columns > 1 else ''}
            {f'column-gap: 0.5in;' if columns > 1 else ''}
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.75em;
            color: #000;
            line-height: 1.3;
        }}

        h1 {{ font-size: 2.2em; }}
        h2 {{ font-size: 1.8em; }}
        h3 {{ font-size: 1.5em; }}
        h4 {{ font-size: 1.3em; }}
        h5 {{ font-size: 1.1em; }}
        h6 {{ font-size: 1em; }}

        p {{
            margin-bottom: 1.2em;
        }}

        ul, ol {{
            margin-left: 2.5em;
            margin-bottom: 1.2em;
        }}

        li {{
            margin-bottom: 0.5em;
        }}

        .table-container {{
            margin: 2em 0;
            overflow-x: auto;
            break-inside: avoid;
        }}

        .table-caption {{
            font-weight: 600;
            text-align: center;
            margin-bottom: 0.75em;
            font-size: 0.95em;
            color: #444;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 0 auto;
            font-size: 0.9em;
            background-color: white;
        }}

        th, td {{
            border: 1px solid #333;
            padding: 10px 14px;
            text-align: left;
            vertical-align: top;
        }}

        th {{
            background-color: #f8f8f8;
            font-weight: bold;
            color: #000;
        }}

        td:empty::after {{
            content: "\\00a0";
        }}

        .image-container {{
            margin: 2em 0;
            text-align: center;
            break-inside: avoid;
        }}

        .image-placeholder {{
            background: linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%);
            border: 2px dashed #999;
            min-height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.75em;
            border-radius: 4px;
        }}

        .image-description {{
            color: #666;
            font-style: italic;
            padding: 30px;
            font-size: 0.95em;
        }}

        .image-caption {{
            font-style: italic;
            font-size: 0.9em;
            color: #444;
            margin-top: 0.5em;
        }}

        .caption {{
            font-style: italic;
            font-size: 0.9em;
            color: #666;
            text-align: center;
            margin: 1em 0;
        }}

        strong {{
            font-weight: 700;
        }}

        em {{
            font-style: italic;
        }}

        u {{
            text-decoration: underline;
        }}

        @media print {{
            body {{
                background-color: white;
                padding: 0;
            }}

            .page {{
                box-shadow: none;
                padding: 0.5in;
                max-width: none;
            }}

            .image-placeholder {{
                border: 1px solid #ccc;
                background: #f5f5f5;
            }}
        }}

        @media screen and (max-width: 768px) {{
            .page {{
                padding: 0.5in;
                column-count: 1 !important;
            }}
        }}
    </style>'''

    def generate_multi_page_html(self, pages_content: List[Dict], pages_info: List[Dict],
                                 output_path: str = None) -> str:
        """Generate single HTML file with all pages"""
        print(f"\nGenerating multi-page HTML document...")

        if output_path is None:
            output_path = Path("output/reconstructed_document.html")
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(exist_ok=True, parents=True)

        # Generate pages
        pages_html = []
        for content, info in zip(pages_content, pages_info):
            if info:
                self.page_width = info.get('original_width', self.page_width)
                self.page_height = info.get('original_height', self.page_height)

            if 'content_items' in content and content['content_items']:
                page_body = self._render_content_items_flow(content['content_items'], info)
            else:
                page_body = self._render_legacy_improved(content, info)

            pages_html.append(page_body)

        # Build complete HTML
        layout = pages_content[0].get('layout', {}) if pages_content else {}
        html_content = self._build_multi_page_html(pages_html, layout)

        # Save
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"  ✓ Multi-page HTML saved to: {output_path}")
        return str(output_path)

    def _build_multi_page_html(self, pages_html: List[str], layout: Dict) -> str:
        """Build complete multi-page document"""
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <title>Document</title>',
            self._generate_css(layout),
            '    <style>',
            '        .page { margin-bottom: 3em; page-break-after: always; }',
            '        .page:last-child { margin-bottom: 0; }',
            '        .page-number { text-align: center; font-size: 0.85em; color: #999; margin-top: 1.5em; padding-top: 1em; border-top: 1px solid #e0e0e0; }',
            '        @media print { .page { margin: 0; box-shadow: none; page-break-after: always; } }',
            '    </style>',
            '</head>',
            '<body>',
        ]

        for i, page_html in enumerate(pages_html, 1):
            html_parts.append('    <div class="page">')
            html_parts.append(page_html)
            html_parts.append(f'        <div class="page-number">— {i} —</div>')
            html_parts.append('    </div>')

        html_parts.extend(['</body>', '</html>'])

        return '\n'.join(html_parts)


def main():
    """Example usage"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Generate readable HTML from extracted content')
    parser.add_argument('content_json', help='Path to extracted content JSON file')
    parser.add_argument('--output', help='Output HTML file path')

    args = parser.parse_args()

    # Load content
    with open(args.content_json, 'r', encoding='utf-8') as f:
        content = json.load(f)

    # Generate HTML
    generator = HTMLPageGenerator()
    page_info = {}
    html_path = generator.generate_page_html(content, page_info, args.output)

    print(f"\n✓ Readable HTML generated: {html_path}")


if __name__ == "__main__":
    main()
