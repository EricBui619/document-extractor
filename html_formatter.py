"""
HTML Formatter Module
Reviews and adjusts HTML formatting for improved readability
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class HTMLFormatter:
    """Formats HTML files for better readability"""

    def __init__(self):
        """Initialize HTML formatter"""
        self.improvements = []

    def review_html_file(self, html_path: str) -> Dict:
        """
        Review an HTML file and identify readability issues

        Args:
            html_path: Path to HTML file

        Returns:
            Dictionary with review results and suggestions
        """
        if not os.path.exists(html_path):
            return {'error': f'File not found: {html_path}'}

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        review = {
            'file': html_path,
            'issues': [],
            'suggestions': [],
            'statistics': {}
        }

        # Analyze content
        tables = soup.find_all('table')
        text_blocks = soup.find_all(class_='text-block')
        paragraphs = soup.find_all('p')

        review['statistics'] = {
            'tables': len(tables),
            'text_blocks': len(text_blocks),
            'paragraphs': len(paragraphs)
        }

        # Check table formatting
        for i, table in enumerate(tables):
            cells = table.find_all(['td', 'th'])
            if cells:
                # Check for small font sizes
                style = table.get('style', '')
                if 'font-size' in style and ('8pt' in style or '9pt' in style):
                    review['issues'].append(f'Table {i+1}: Font size too small')
                    review['suggestions'].append(f'Table {i+1}: Increase font size to at least 10pt')

                # Check for dense content
                if len(cells) > 50:
                    review['issues'].append(f'Table {i+1}: Very dense with {len(cells)} cells')
                    review['suggestions'].append(f'Table {i+1}: Consider adding more padding and spacing')

        # Check text block formatting
        for i, block in enumerate(text_blocks):
            text = block.get_text(strip=True)
            if len(text) > 500:
                review['issues'].append(f'Text block {i+1}: Very long ({len(text)} chars)')
                review['suggestions'].append(f'Text block {i+1}: Consider breaking into smaller chunks')

        return review

    def apply_readability_improvements(self, html_path: str, output_path: str = None) -> str:
        """
        Apply readability improvements to HTML file

        Args:
            html_path: Path to input HTML file
            output_path: Path to save improved HTML (default: overwrite original)

        Returns:
            Path to the improved HTML file
        """
        if not os.path.exists(html_path):
            raise FileNotFoundError(f'File not found: {html_path}')

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Apply improvements
        improved_html = self._improve_html_content(html_content)

        # Save to output
        if output_path is None:
            output_path = html_path

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(improved_html)

        print(f"  ✓ Applied {len(self.improvements)} improvements to {Path(output_path).name}")

        return output_path

    def _improve_html_content(self, html_content: str) -> str:
        """
        Apply various readability improvements to HTML content

        Args:
            html_content: Original HTML content

        Returns:
            Improved HTML content
        """
        self.improvements = []

        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Apply improvements
        self._improve_table_formatting(soup)
        self._improve_text_spacing(soup)
        self._improve_typography(soup)
        self._add_responsive_css(soup)

        return str(soup)

    def _improve_table_formatting(self, soup: BeautifulSoup):
        """Improve table formatting for readability while preserving positioning"""

        # DO NOT modify table containers or table styles - they have absolute positioning
        # Only improve cell content (headers and data cells) for better readability

        # Find all tables
        tables = soup.find_all('table')

        for table in tables:
            # Improve header cells only
            headers = table.find_all('th')
            for th in headers:
                th_style = self._parse_style_string(th.get('style', ''))
                # Only update content styling, not positioning
                th_style.update({
                    'padding': '10px',
                    'background-color': '#4a90e2',  # Professional blue
                    'color': 'white',
                    'font-weight': 'bold',
                    'text-align': 'left'
                })
                th['style'] = self._dict_to_style_string(th_style)

            # Improve data cells only
            cells = table.find_all('td')
            for i, td in enumerate(cells):
                td_style = self._parse_style_string(td.get('style', ''))

                # Determine row number for alternating colors
                row = td.find_parent('tr')
                row_index = 0
                if row:
                    tbody = row.find_parent('tbody')
                    if tbody:
                        rows = tbody.find_all('tr')
                        row_index = rows.index(row)

                # Alternate row colors
                bg_color = '#f9f9f9' if row_index % 2 == 0 else '#ffffff'

                # Only update content styling, not positioning
                td_style.update({
                    'padding': '10px',
                    'background-color': bg_color,
                    'line-height': '1.6'
                })
                td['style'] = self._dict_to_style_string(td_style)

            if cells:
                self.improvements.append(f'Improved table with {len(cells)} cells')

    def _improve_text_spacing(self, soup: BeautifulSoup):
        """Improve text spacing for readability while preserving positioning"""

        # DO NOT modify text blocks or image containers - they have absolute positioning
        # All positioning must be preserved exactly as generated

        # Only improve inline text readability within blocks
        # No modifications to container styles

        # Skip paragraph modifications to preserve layout
        pass

    def _improve_typography(self, soup: BeautifulSoup):
        """Improve typography for readability"""

        # Update body styles
        style_tag = soup.find('style')
        if style_tag:
            css = style_tag.string or ''

            # Add improved typography rules
            typography_css = """
        /* Improved Typography */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            color: #333;
            line-height: 1.6;
        }

        h1, h2, h3, h4, h5, h6 {
            margin-top: 20px;
            margin-bottom: 10px;
            font-weight: 600;
            line-height: 1.3;
            color: #2c3e50;
        }

        h1 { font-size: 2.2em; }
        h2 { font-size: 1.8em; }
        h3 { font-size: 1.5em; }
        h4 { font-size: 1.3em; }

        /* Better link styles */
        a {
            color: #4a90e2;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        /* Code and preformatted text */
        code, pre {
            font-family: 'Courier New', Courier, monospace;
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
        }
"""

            style_tag.string = css + typography_css
            self.improvements.append('Improved typography')

    def _add_responsive_css(self, soup: BeautifulSoup):
        """Add responsive CSS for better mobile experience"""

        style_tag = soup.find('style')
        if style_tag:
            css = style_tag.string or ''

            # Add responsive rules
            responsive_css = """
        /* Responsive Design */
        @media screen and (max-width: 768px) {
            .page {
                width: 100% !important;
                height: auto !important;
                min-height: 100vh;
            }

            table {
                font-size: 10pt !important;
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }

            .text-block {
                position: relative !important;
                width: 100% !important;
                left: 0 !important;
            }

            .table-container {
                position: relative !important;
                width: 100% !important;
                left: 0 !important;
            }
        }

        /* Print styles */
        @media print {
            body {
                background-color: white;
                padding: 0;
            }

            .page {
                box-shadow: none;
                margin: 0;
            }
        }
"""

            style_tag.string = css + responsive_css
            self.improvements.append('Added responsive CSS')

    def _parse_style_string(self, style_str: str) -> Dict[str, str]:
        """Parse CSS style string into dictionary"""
        styles = {}
        if not style_str:
            return styles

        for rule in style_str.split(';'):
            rule = rule.strip()
            if ':' in rule:
                prop, value = rule.split(':', 1)
                styles[prop.strip()] = value.strip()

        return styles

    def _dict_to_style_string(self, style_dict: Dict[str, str]) -> str:
        """Convert dictionary to CSS style string"""
        return '; '.join(f'{k}: {v}' for k, v in style_dict.items())

    def batch_format_directory(self, directory: str, pattern: str = "*.html") -> List[str]:
        """
        Format all HTML files in a directory

        Args:
            directory: Directory containing HTML files
            pattern: File pattern to match (default: *.html)

        Returns:
            List of formatted file paths
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            raise FileNotFoundError(f'Directory not found: {directory}')

        html_files = list(dir_path.glob(pattern))

        if not html_files:
            print(f"No HTML files found in {directory}")
            return []

        print(f"\n📝 Formatting {len(html_files)} HTML files in {directory}...")

        formatted_files = []

        for html_file in html_files:
            try:
                output_path = self.apply_readability_improvements(str(html_file))
                formatted_files.append(output_path)
            except Exception as e:
                print(f"  ✗ Error formatting {html_file.name}: {str(e)}")

        print(f"✓ Successfully formatted {len(formatted_files)} files")

        return formatted_files


def main():
    """Test the HTML formatter"""
    import argparse

    parser = argparse.ArgumentParser(description='Format HTML files for better readability')
    parser.add_argument('path', help='HTML file or directory path')
    parser.add_argument('--review', action='store_true', help='Review only (no changes)')
    parser.add_argument('--output', help='Output path (for single file)')

    args = parser.parse_args()

    formatter = HTMLFormatter()
    path = Path(args.path)

    if path.is_file():
        # Single file
        if args.review:
            review = formatter.review_html_file(str(path))
            print(f"\n=== Review of {path.name} ===")
            print(f"Statistics: {review.get('statistics', {})}")
            print(f"\nIssues ({len(review.get('issues', []))}):")
            for issue in review.get('issues', []):
                print(f"  - {issue}")
            print(f"\nSuggestions ({len(review.get('suggestions', []))}):")
            for suggestion in review.get('suggestions', []):
                print(f"  - {suggestion}")
        else:
            output = args.output or str(path)
            formatter.apply_readability_improvements(str(path), output)
            print(f"✓ Formatted: {output}")

    elif path.is_dir():
        # Directory
        if args.review:
            print("Review mode not supported for directories")
        else:
            formatter.batch_format_directory(str(path))

    else:
        print(f"Error: Path not found: {path}")


if __name__ == '__main__':
    main()
