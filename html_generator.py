"""
HTML Page Generator Module
Generates HTML pages from extracted content preserving natural reading order
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
        Generate HTML for a single page with extracted content

        Args:
            content: Extracted content from OpenAI (tables, images, text_blocks)
            page_info: Page information from PDF converter (dimensions, etc.)
            output_path: Path to save HTML file

        Returns:
            Path to the generated HTML file
        """
        page_num = content.get('page_num', 1)
        print(f"\nGenerating HTML for page {page_num}...")

        # Update page dimensions from page_info if available
        if page_info:
            self.page_width = page_info.get('original_width', self.page_width)
            self.page_height = page_info.get('original_height', self.page_height)

        # Determine output path first (needed for relative image paths)
        if output_path is None:
            output_dir = Path("output/html_pages")
            output_dir.mkdir(exist_ok=True, parents=True)
            output_path = output_dir / f"page_{page_num}.html"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(exist_ok=True, parents=True)

        # Generate HTML content (pass output_path for relative image paths)
        html_content = self._build_html(content, page_info, str(output_path))

        # Write HTML to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"  ✓ HTML saved to: {output_path}")
        return str(output_path)

    def _build_html(self, content: Dict, page_info: Dict, html_output_path: str = None) -> str:
        """Build complete HTML document with absolute positioning from extracted content"""
        page_num = content.get('page_num', 1)

        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>Page {page_num}</title>',
            self._generate_css(),
            '</head>',
            '<body>',
            '    <div class="page">',
        ]

        # Use absolute positioning from extracted content
        # All elements conform to positional definitions from extraction

        # Render text blocks with absolute positioning
        for text_block in content.get('text_blocks', []):
            html_parts.append(self._render_text_block(text_block))

        # Render tables with absolute positioning
        for table in content.get('tables', []):
            html_parts.append(self._render_table(table))

        # Render images with absolute positioning
        for image in content.get('images', []):
            html_parts.append(self._render_image(image, page_info))

        # Close HTML
        html_parts.extend([
            '    </div>',
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)

    def _generate_flow_css(self) -> str:
        """Generate CSS for flow layout (prevents overlapping)"""
        return '''    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        @page {
            size: A4;
            margin: 1in;
        }

        body {
            font-family: 'Times New Roman', Times, serif;
            background-color: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }

        .page {
            background-color: white;
            max-width: 8.27in;  /* A4 width */
            margin: 0 auto;
            padding: 1in;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            min-height: 11.69in;  /* A4 height */
        }

        h1, h2, h3, h4, h5, h6 {
            font-weight: bold;
            margin-top: 1.2em;
            margin-bottom: 0.6em;
            color: #000;
        }

        h1 { font-size: 2em; }
        h2 { font-size: 1.5em; }
        h3 { font-size: 1.3em; }
        h4 { font-size: 1.1em; }
        h5 { font-size: 1em; }
        h6 { font-size: 0.9em; }

        p {
            margin-bottom: 1em;
            text-align: justify;
        }

        ul, ol {
            margin-left: 2em;
            margin-bottom: 1em;
        }

        li {
            margin-bottom: 0.5em;
        }

        .table-container {
            margin: 1.5em 0;
            overflow-x: auto;
            page-break-inside: avoid;
        }

        .table-caption {
            font-weight: bold;
            text-align: center;
            margin-bottom: 0.5em;
            font-size: 0.95em;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 0 auto;
            font-size: 0.9em;
            background-color: white;
        }

        th, td {
            border: 1px solid #000;
            padding: 8px 12px;
            text-align: left;
            vertical-align: top;
        }

        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }

        td:empty::after {
            content: "\\00a0";
        }

        .image-container {
            margin: 1.5em 0;
            text-align: center;
            page-break-inside: avoid;
        }

        .embedded-image {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
            border: 1px solid #ddd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .image-placeholder {
            background-color: #e8e8e8;
            border: 2px dashed #999;
            min-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5em;
        }

        .image-description {
            color: #666;
            font-style: italic;
            padding: 20px;
        }

        .image-caption {
            font-style: italic;
            font-size: 0.9em;
            color: #333;
            margin-top: 0.5em;
            text-align: center;
        }

        .image-note {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            padding: 1em;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }

        .image-note-text {
            font-style: italic;
        }

        .page-header, .page-footer {
            font-size: 0.9em;
            color: #666;
            text-align: center;
            padding: 0.5em 0;
        }

        .page-header {
            border-bottom: 1px solid #ddd;
            margin-bottom: 1em;
        }

        .page-footer {
            border-top: 1px solid #ddd;
            margin-top: 1em;
        }

        @media print {
            body {
                background-color: white;
                padding: 0;
            }

            .page {
                box-shadow: none;
                padding: 0.5in;
                max-width: none;
                margin: 0;
            }
        }
    </style>'''

    def _preserve_newlines(self, text: str) -> str:
        """
        Preserve newlines by converting them to <br/> tags
        NEVER collapse or trim newline characters
        """
        if not text:
            return text
        # Convert all newlines to <br/> tags to preserve them in HTML
        return text.replace('\n', '<br/>\n')

    def _add_line_breaks(self, text: str) -> str:
        """
        Preserve newlines from JSON content - NEVER modify the content
        Keep exact same content as extracted in JSON file
        """
        if not text:
            return text

        # Only preserve existing newlines by converting to <br/> tags
        # NEVER add new line breaks that weren't in the original content
        return text.replace('\n', '<br/>\n')

    def _render_text_block_flow(self, text_block: Dict) -> str:
        """Render text block in flow layout (no absolute positioning)"""
        block_type = text_block.get('type', 'paragraph')
        content = text_block.get('content', '')
        formatting = text_block.get('formatting', [])

        # Apply formatting
        formatted_content = content
        if isinstance(formatting, dict):
            if formatting.get('bold', False):
                formatted_content = f'<strong>{formatted_content}</strong>'
            if formatting.get('italic', False):
                formatted_content = f'<em>{formatted_content}</em>'
            if formatting.get('underline', False):
                formatted_content = f'<u>{formatted_content}</u>'
        elif isinstance(formatting, list):
            if 'bold' in formatting:
                formatted_content = f'<strong>{formatted_content}</strong>'
            if 'italic' in formatting:
                formatted_content = f'<em>{formatted_content}</em>'
            if 'underline' in formatting:
                formatted_content = f'<u>{formatted_content}</u>'

        # Render based on type
        if block_type == 'header':
            level = text_block.get('level', 1)
            level = max(1, min(6, level))
            # Preserve newlines in headers
            formatted_content = self._preserve_newlines(formatted_content)
            return f'        <h{level}>{formatted_content}</h{level}>'
        elif block_type == 'page_header':
            # Preserve newlines in page headers
            formatted_content = self._preserve_newlines(formatted_content)
            return f'        <div class="page-header">{formatted_content}</div>'
        elif block_type == 'page_footer':
            # Preserve newlines in page footers
            formatted_content = self._preserve_newlines(formatted_content)
            return f'        <div class="page-footer">{formatted_content}</div>'
        elif block_type == 'list':
            items = text_block.get('items', [content])
            list_html = '        <ul>\n'
            for item in items:
                # Preserve newlines in list items
                item = self._preserve_newlines(item)
                list_html += f'            <li>{item}</li>\n'
            list_html += '        </ul>'
            return list_html
        else:
            # Preserve newlines - keep exact same content as in JSON
            formatted_content = self._preserve_newlines(formatted_content)
            return f'        <p>{formatted_content}</p>'

    def _render_table_flow(self, table: Dict) -> str:
        """Render table in flow layout"""
        table_html = table.get('html', '')
        caption = table.get('caption', '')

        parts = ['        <div class="table-container">']
        if caption:
            # Preserve newlines in caption
            caption = self._preserve_newlines(caption)
            parts.append(f'            <div class="table-caption">{caption}</div>')
        parts.append(f'            {table_html}')
        parts.append('        </div>')

        return '\n'.join(parts)

    def _get_relative_image_path(self, image_path: str, html_path: str) -> str:
        """
        Calculate relative path from HTML file to image file
        This allows images to be referenced without base64 encoding
        """
        if not image_path or not html_path:
            return image_path

        try:
            from pathlib import Path
            img_path = Path(image_path).resolve()
            html_dir = Path(html_path).parent.resolve()

            # Calculate relative path
            rel_path = os.path.relpath(img_path, html_dir)

            # Convert backslashes to forward slashes for HTML
            rel_path = rel_path.replace('\\', '/')

            return rel_path
        except:
            # Fallback to absolute path if relative calculation fails
            return image_path

    def _render_image_flow(self, image: Dict, page_info: Dict, html_output_path: str = None) -> str:
        """
        Render image in flow layout - EMBEDS ALL IMAGES
        Extracts and embeds all visual content (charts, diagrams, shapes, photos, logos, everything)
        Uses file references instead of base64 for better performance
        """
        description = image.get('description', 'Image')
        caption = image.get('caption', '')
        image_path = image.get('image_path', '')  # Path to extracted image
        image_data = image.get('image_data', '')  # Base64 encoded image (legacy)

        # Get image type from metadata
        metadata = image.get('metadata', {})
        image_type = metadata.get('image_type', 'unknown').lower()

        parts = ['        <div class="image-container">']

        # EMBED ALL IMAGES - no filtering, extract everything
        if image_data:
            # Legacy: Base64 embedded image (not recommended, large file size)
            parts.append(f'            <img src="{image_data}" alt="{description}" class="embedded-image" />')
        elif image_path and os.path.exists(image_path):
            # NEW: Use file reference instead of base64 (smaller HTML, faster loading)
            if html_output_path:
                # Calculate relative path for portability
                rel_path = self._get_relative_image_path(image_path, html_output_path)
            else:
                # Use absolute path as fallback
                rel_path = image_path.replace('\\', '/')

            parts.append(f'            <img src="{rel_path}" alt="{description}" class="embedded-image" />')
            print(f"      ✓ Added image to HTML: {Path(image_path).name}")
        else:
            # Fallback to placeholder with description if no image file available
            # DEBUG: Show why image wasn't embedded
            if not image_path:
                print(f"      ⚠ No image_path for: {description}")
            elif not os.path.exists(image_path):
                print(f"      ⚠ Image file not found: {image_path}")

            # Preserve newlines in description
            description = self._preserve_newlines(description)
            parts.extend([
                '            <div class="image-placeholder">',
                f'                <div class="image-description">{description}</div>',
                f'                <div class="image-type-label">[{image_type.upper()}]</div>',
                '            </div>'
            ])

        if caption:
            # Preserve newlines in caption
            caption = self._preserve_newlines(caption)
            parts.append(f'            <div class="image-caption">{caption}</div>')

        parts.append('        </div>')

        return '\n'.join(parts)

    def _generate_css(self) -> str:
        """Generate CSS styles for the page with absolute positioning"""
        return f'''    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Times New Roman', Times, serif;
            background-color: #f0f0f0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }}

        .page {{
            background-color: white;
            position: relative;
            width: {self.page_width}pt;
            height: {self.page_height}pt;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 0 auto;
        }}

        .text-block {{
            position: absolute;
            padding: 5px;
        }}

        .text-block.header {{
            font-weight: bold;
            font-size: 1.2em;
        }}

        .text-block.paragraph {{
            line-height: 1.6;
            text-align: justify;
        }}

        .text-block.caption {{
            font-style: italic;
            color: #666;
            font-size: 0.9em;
        }}

        .table-container {{
            position: absolute;
            padding: 10px;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 10pt;
            background-color: white;
        }}

        th, td {{
            border: 1px solid #000;
            padding: 6px 8px;
            text-align: left;
            vertical-align: top;
        }}

        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}

        td {{
            background-color: white;
        }}

        /* Preserve empty cells */
        td:empty::after {{
            content: "\\00a0";
        }}

        .image-container {{
            position: absolute;
            overflow: hidden;
        }}

        .image-container img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}

        .image-caption {{
            position: absolute;
            font-style: italic;
            font-size: 0.9em;
            color: #666;
            text-align: center;
        }}

        /* Text formatting */
        .bold {{
            font-weight: bold;
        }}

        .italic {{
            font-style: italic;
        }}

        .underline {{
            text-decoration: underline;
        }}
    </style>'''

    def _render_text_block(self, text_block: Dict) -> str:
        """Render a text block with positioning"""
        block_type = text_block.get('type', 'paragraph')
        content = text_block.get('content', '')
        position = text_block.get('position', 'top-left')
        formatting = text_block.get('formatting', [])

        # Handle both string positions (old format) and dict positions (new format)
        if isinstance(position, dict):
            # New format with percentages
            left = (position.get('x_start', 5) / 100) * self.page_width
            top = (position.get('y_start', 5) / 100) * self.page_height
            coords = {'left': left, 'top': top}
        else:
            # Old format with string like 'top-left'
            coords = self._position_to_coordinates(position, 'text')

        # Apply formatting - handle both list and dict formats
        formatted_content = content
        if isinstance(formatting, dict):
            # New format: dict with boolean flags
            if formatting.get('bold', False):
                formatted_content = f'<strong>{formatted_content}</strong>'
            if formatting.get('italic', False):
                formatted_content = f'<em>{formatted_content}</em>'
            if formatting.get('underline', False):
                formatted_content = f'<u>{formatted_content}</u>'
        elif isinstance(formatting, list):
            # Old format: list of strings
            if 'bold' in formatting:
                formatted_content = f'<strong>{formatted_content}</strong>'
            if 'italic' in formatting:
                formatted_content = f'<em>{formatted_content}</em>'
            if 'underline' in formatting:
                formatted_content = f'<u>{formatted_content}</u>'

        # Render based on type
        if block_type == 'header':
            level = text_block.get('level', 1)
            # Preserve newlines in headers
            formatted_content = self._preserve_newlines(formatted_content)
            return f'        <div class="text-block header" style="left: {coords["left"]}pt; top: {coords["top"]}pt;"><h{level}>{formatted_content}</h{level}></div>'
        elif block_type == 'list':
            items = text_block.get('items', [content])
            # Preserve newlines in list items
            list_html = '<ul>' + ''.join([f'<li>{self._preserve_newlines(item)}</li>' for item in items]) + '</ul>'
            return f'        <div class="text-block" style="left: {coords["left"]}pt; top: {coords["top"]}pt;">{list_html}</div>'
        else:
            # Preserve newlines in paragraphs
            formatted_content = self._preserve_newlines(formatted_content)
            return f'        <div class="text-block {block_type}" style="left: {coords["left"]}pt; top: {coords["top"]}pt;"><p>{formatted_content}</p></div>'

    def _render_table(self, table: Dict) -> str:
        """Render a table with positioning"""
        table_html = table.get('html', '')
        position = table.get('position', {})
        caption = table.get('caption', '')

        # Calculate position in points
        left = (position.get('left_percent', 5) / 100) * self.page_width
        top = (position.get('top_percent', 5) / 100) * self.page_height
        width = (position.get('width_percent', 90) / 100) * self.page_width

        # Build table container
        html_parts = [
            f'        <div class="table-container" style="left: {left}pt; top: {top}pt; width: {width}pt;">'
        ]

        if caption:
            # Preserve newlines in caption
            caption = self._preserve_newlines(caption)
            html_parts.append(f'            <div class="image-caption" style="margin-bottom: 5px;">{caption}</div>')

        html_parts.append(f'            {table_html}')
        html_parts.append('        </div>')

        return '\n'.join(html_parts)

    def _render_image(self, image: Dict, page_info: Dict) -> str:
        """Render an image with positioning"""
        position = image.get('position', {})
        caption = image.get('caption', '')
        description = image.get('description', '')

        # Calculate position in points
        left = (position.get('left_percent', 5) / 100) * self.page_width
        top = (position.get('top_percent', 5) / 100) * self.page_height
        width = (position.get('width_percent', 40) / 100) * self.page_width
        height = (position.get('height_percent', 30) / 100) * self.page_height

        # Create placeholder for image
        # In actual implementation, this would reference extracted image files
        placeholder_style = f"background-color: #e0e0e0; border: 1px dashed #999;"

        html_parts = [
            f'        <div class="image-container" style="left: {left}pt; top: {top}pt; width: {width}pt; height: {height}pt; {placeholder_style}">',
            f'            <div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 0.8em; color: #666; padding: 10px; text-align: center;">',
            f'                Image: {description}',
            '            </div>',
            '        </div>'
        ]

        if caption:
            # Preserve newlines in caption
            caption = self._preserve_newlines(caption)
            caption_top = top + height + 5
            html_parts.append(f'        <div class="image-caption" style="left: {left}pt; top: {caption_top}pt; width: {width}pt;">{caption}</div>')

        return '\n'.join(html_parts)

    def _position_to_coordinates(self, position_str: str, element_type: str) -> Dict[str, float]:
        """Convert position string (e.g., 'top-left') to approximate coordinates"""
        # Parse position string
        parts = position_str.lower().split('-')
        v_pos = parts[0] if len(parts) > 0 else 'top'
        h_pos = parts[1] if len(parts) > 1 else 'left'

        # Vertical positioning
        if v_pos == 'top':
            top = self.page_height * 0.1
        elif v_pos == 'middle':
            top = self.page_height * 0.45
        elif v_pos == 'bottom':
            top = self.page_height * 0.75
        else:
            top = self.page_height * 0.1

        # Horizontal positioning
        if h_pos == 'left':
            left = self.page_width * 0.1
        elif h_pos == 'center':
            left = self.page_width * 0.25
        elif h_pos == 'right':
            left = self.page_width * 0.6
        else:
            left = self.page_width * 0.1

        return {'left': left, 'top': top}

    def embed_image_as_base64(self, image_path: str) -> str:
        """Embed image as base64 data URL"""
        try:
            with open(image_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')

            # Determine image format
            ext = Path(image_path).suffix.lower()
            mime_type = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml'
            }.get(ext, 'image/png')

            return f"data:{mime_type};base64,{img_data}"
        except Exception as e:
            print(f"  ✗ Error embedding image: {str(e)}")
            return ""

    def generate_multi_page_html(self, pages_content: List[Dict], pages_info: List[Dict],
                                 output_path: str = None) -> str:
        """
        Generate a single HTML file with all pages

        Args:
            pages_content: List of extracted content for each page
            pages_info: List of page information
            output_path: Path to save the combined HTML

        Returns:
            Path to the generated HTML file
        """
        print(f"\nGenerating multi-page HTML document...")

        if output_path is None:
            output_path = Path("output/reconstructed_document.html")
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(exist_ok=True, parents=True)

        # Generate individual page HTML strings
        pages_html = []
        for content, info in zip(pages_content, pages_info):
            if info:
                self.page_width = info.get('original_width', self.page_width)
                self.page_height = info.get('original_height', self.page_height)

            page_body = self._build_page_body(content, info, str(output_path))
            pages_html.append(page_body)

        # Combine into single document
        html_content = self._build_multi_page_html(pages_html)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"  ✓ Multi-page HTML saved to: {output_path}")
        return str(output_path)

    def _build_page_body(self, content: Dict, page_info: Dict, html_output_path: str = None) -> str:
        """Build HTML body content for a single page with flow layout"""
        # Collect all content items with their positions for sorting
        all_items = []

        for text_block in content.get('text_blocks', []):
            pos = text_block.get('position', {})
            y_pos = pos.get('y_start', 0) if isinstance(pos, dict) else 0
            all_items.append(('text', text_block, y_pos))

        for table in content.get('tables', []):
            pos = table.get('position', {})
            y_pos = pos.get('top_percent', 0) if isinstance(pos, dict) else 0
            all_items.append(('table', table, y_pos))

        for image in content.get('images', []):
            pos = image.get('position', {})
            y_pos = pos.get('top_percent', 0) if isinstance(pos, dict) else 0
            all_items.append(('image', image, y_pos))

        # Sort by vertical position to maintain reading order
        all_items.sort(key=lambda x: x[2])

        # Render in order using FLOW methods (prevents overlapping)
        parts = []
        for item_type, item, _ in all_items:
            if item_type == 'text':
                parts.append(self._render_text_block_flow(item))
            elif item_type == 'table':
                parts.append(self._render_table_flow(item))
            elif item_type == 'image':
                parts.append(self._render_image_flow(item, page_info, html_output_path))

        return '\n'.join(parts)

    def _build_multi_page_html(self, pages_html: List[str]) -> str:
        """Build complete multi-page HTML document with flow layout"""
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <title>Reconstructed Document</title>',
            self._generate_flow_css(),  # Use flow CSS instead of absolute positioning CSS
            '    <style>',
            '        .page {',
            '            margin-bottom: 40px;',
            '            page-break-after: always;',
            '        }',
            '        @media print {',
            '            body { background-color: white; padding: 0; }',
            '            .page { margin: 0; box-shadow: none; page-break-after: always; }',
            '        }',
            '    </style>',
            '</head>',
            '<body>',
        ]

        # Add each page with flow layout (NO fixed width/height to prevent overflow)
        for i, page_html in enumerate(pages_html, 1):
            html_parts.append('    <div class="page">')
            html_parts.append(page_html)
            html_parts.append('    </div>')

        html_parts.extend([
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)


def main():
    """Example usage"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Generate HTML from extracted content')
    parser.add_argument('content_json', help='Path to extracted content JSON file')
    parser.add_argument('--output', help='Output HTML file path')
    parser.add_argument('--page-width', type=float, default=612, help='Page width in points')
    parser.add_argument('--page-height', type=float, default=792, help='Page height in points')

    args = parser.parse_args()

    # Load content
    with open(args.content_json, 'r', encoding='utf-8') as f:
        content = json.load(f)

    # Create generator
    generator = HTMLPageGenerator(page_width=args.page_width, page_height=args.page_height)

    # Generate HTML
    page_info = {'original_width': args.page_width, 'original_height': args.page_height}
    html_path = generator.generate_page_html(content, page_info, args.output)

    print(f"\nHTML generated successfully: {html_path}")


if __name__ == "__main__":
    main()
