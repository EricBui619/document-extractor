"""
HTML to PDF Converter Module
Converts HTML pages back to PDF format with high-quality rendering
"""

import os
from pathlib import Path
from typing import List, Optional
import subprocess


class HTMLtoPDFConverter:
    def __init__(self, method: str = "skip"):
        """
        Initialize HTML to PDF converter

        Args:
            method: Conversion method - "skip" (HTML only), "weasyprint", "playwright", or "pdfkit"
        """
        self.method = method
        if method != "skip":
            self._verify_dependencies()

    def _verify_dependencies(self):
        """Verify that required dependencies are available"""
        if self.method == "weasyprint":
            try:
                import weasyprint
                self.converter = weasyprint
                print(f"Using WeasyPrint for HTML to PDF conversion")
            except ImportError as e:
                print(f"WeasyPrint error: {e}")
                print("Falling back to 'skip' mode - will output HTML only")
                self.method = "skip"

        elif self.method == "playwright":
            try:
                from playwright.sync_api import sync_playwright
                self.playwright = sync_playwright
                print(f"Using Playwright for HTML to PDF conversion")
            except ImportError:
                raise ImportError(
                    "Playwright not installed. Install with: pip install playwright && playwright install"
                )

        elif self.method == "pdfkit":
            try:
                import pdfkit
                self.converter = pdfkit
                print(f"Using pdfkit for HTML to PDF conversion")
            except ImportError:
                raise ImportError(
                    "pdfkit not installed. Install with: pip install pdfkit"
                )
        else:
            raise ValueError(f"Unknown conversion method: {self.method}")

    def convert_html_to_pdf(self, html_path: str, pdf_path: str = None,
                           page_width: str = "8.5in", page_height: str = "11in") -> str:
        """
        Convert a single HTML file to PDF

        Args:
            html_path: Path to input HTML file
            pdf_path: Path to output PDF file (default: same as HTML with .pdf extension)
            page_width: Page width (default: "8.5in" for US Letter)
            page_height: Page height (default: "11in" for US Letter)

        Returns:
            Path to the generated PDF file
        """
        if not os.path.exists(html_path):
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        html_path = Path(html_path)

        if pdf_path is None:
            pdf_path = html_path.with_suffix('.pdf')
        else:
            pdf_path = Path(pdf_path)

        pdf_path.parent.mkdir(exist_ok=True, parents=True)

        print(f"\nConverting HTML to PDF: {html_path.name}")

        if self.method == "skip":
            print(f"  ⊘ PDF conversion skipped - HTML output only")
            print(f"  ℹ  HTML file available at: {html_path}")
            return str(html_path)  # Return HTML path instead
        elif self.method == "weasyprint":
            self._convert_with_weasyprint(html_path, pdf_path, page_width, page_height)
        elif self.method == "playwright":
            self._convert_with_playwright(html_path, pdf_path, page_width, page_height)
        elif self.method == "pdfkit":
            self._convert_with_pdfkit(html_path, pdf_path, page_width, page_height)

        print(f"  ✓ PDF saved to: {pdf_path}")
        return str(pdf_path)

    def _convert_with_weasyprint(self, html_path: Path, pdf_path: Path,
                                 page_width: str, page_height: str):
        """Convert using WeasyPrint"""
        from weasyprint import HTML, CSS

        # Create custom CSS for page size
        css_string = f"""
        @page {{
            size: {page_width} {page_height};
            margin: 0;
        }}
        """

        html = HTML(filename=str(html_path))
        html.write_pdf(
            str(pdf_path),
            stylesheets=[CSS(string=css_string)]
        )

    def _convert_with_playwright(self, html_path: Path, pdf_path: Path,
                                 page_width: str, page_height: str):
        """Convert using Playwright (headless browser)"""
        from playwright.sync_api import sync_playwright

        # Convert dimensions to pixels (assuming 96 DPI)
        width_px, height_px = self._parse_dimensions(page_width, page_height)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path.absolute()}")
            page.pdf(
                path=str(pdf_path),
                width=f"{width_px}px",
                height=f"{height_px}px",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
            )
            browser.close()

    def _convert_with_pdfkit(self, html_path: Path, pdf_path: Path,
                            page_width: str, page_height: str):
        """Convert using pdfkit (wkhtmltopdf wrapper)"""
        import pdfkit

        options = {
            'page-width': page_width,
            'page-height': page_height,
            'margin-top': '0',
            'margin-right': '0',
            'margin-bottom': '0',
            'margin-left': '0',
            'encoding': 'UTF-8',
            'enable-local-file-access': None
        }

        pdfkit.from_file(str(html_path), str(pdf_path), options=options)

    def _parse_dimensions(self, width: str, height: str) -> tuple:
        """Parse dimension strings to pixels (96 DPI)"""
        def to_pixels(dim: str) -> int:
            if dim.endswith('in'):
                return int(float(dim[:-2]) * 96)
            elif dim.endswith('px'):
                return int(float(dim[:-2]))
            elif dim.endswith('pt'):
                return int(float(dim[:-2]) * 96 / 72)
            elif dim.endswith('mm'):
                return int(float(dim[:-2]) * 96 / 25.4)
            elif dim.endswith('cm'):
                return int(float(dim[:-2]) * 96 / 2.54)
            else:
                return int(float(dim))

        return to_pixels(width), to_pixels(height)

    def merge_pdfs(self, pdf_paths: List[str], output_path: str = None) -> str:
        """
        Merge multiple PDF files into one

        Args:
            pdf_paths: List of PDF file paths to merge
            output_path: Path to output merged PDF

        Returns:
            Path to the merged PDF file
        """
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")

        if output_path is None:
            output_path = Path("output/merged_document.pdf")
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(exist_ok=True, parents=True)

        print(f"\nMerging {len(pdf_paths)} PDF files...")

        pdf_merger = PyPDF2.PdfMerger()

        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                print(f"  ⚠ Warning: PDF not found: {pdf_path}")
                continue

            print(f"  Adding: {Path(pdf_path).name}")
            pdf_merger.append(pdf_path)

        with open(output_path, 'wb') as output_file:
            pdf_merger.write(output_file)

        pdf_merger.close()

        print(f"  ✓ Merged PDF saved to: {output_path}")
        return str(output_path)

    def convert_and_merge_html_pages(self, html_paths: List[str], output_path: str = None,
                                    page_width: str = "8.5in", page_height: str = "11in") -> str:
        """
        Convert multiple HTML pages to PDF and merge them

        Args:
            html_paths: List of HTML file paths
            output_path: Path to output merged PDF
            page_width: Page width
            page_height: Page height

        Returns:
            Path to the merged PDF file
        """
        if output_path is None:
            output_path = Path("output/reconstructed_document.pdf")
        else:
            output_path = Path(output_path)

        # Convert each HTML to PDF
        pdf_paths = []
        temp_dir = Path("output/temp_pdfs")
        temp_dir.mkdir(exist_ok=True, parents=True)

        for i, html_path in enumerate(html_paths, 1):
            temp_pdf_path = temp_dir / f"page_{i}.pdf"
            pdf_path = self.convert_html_to_pdf(html_path, str(temp_pdf_path), page_width, page_height)
            pdf_paths.append(pdf_path)

        # Merge all PDFs
        merged_path = self.merge_pdfs(pdf_paths, str(output_path))

        # Clean up temporary PDFs
        print("\nCleaning up temporary files...")
        for pdf_path in pdf_paths:
            try:
                os.remove(pdf_path)
            except:
                pass

        try:
            temp_dir.rmdir()
        except:
            pass

        return merged_path

    def convert_multi_page_html_to_pdf(self, html_path: str, output_path: str = None,
                                      page_width: str = "8.5in", page_height: str = "11in") -> str:
        """
        Convert a multi-page HTML document to PDF
        (Use this when HTML already contains all pages in one file)

        Args:
            html_path: Path to multi-page HTML file
            output_path: Path to output PDF file
            page_width: Page width
            page_height: Page height

        Returns:
            Path to the generated PDF file
        """
        return self.convert_html_to_pdf(html_path, output_path, page_width, page_height)


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Convert HTML to PDF')
    parser.add_argument('html_path', help='Path to input HTML file')
    parser.add_argument('--output', help='Output PDF file path')
    parser.add_argument('--method', choices=['weasyprint', 'playwright', 'pdfkit'],
                       default='weasyprint', help='Conversion method')
    parser.add_argument('--width', default='8.5in', help='Page width (default: 8.5in)')
    parser.add_argument('--height', default='11in', help='Page height (default: 11in)')
    parser.add_argument('--merge', nargs='+', help='Merge multiple HTML files')

    args = parser.parse_args()

    converter = HTMLtoPDFConverter(method=args.method)

    if args.merge:
        # Merge multiple HTML files
        pdf_path = converter.convert_and_merge_html_pages(
            args.merge,
            args.output,
            args.width,
            args.height
        )
    else:
        # Convert single HTML file
        pdf_path = converter.convert_html_to_pdf(
            args.html_path,
            args.output,
            args.width,
            args.height
        )

    print(f"\nConversion complete! PDF saved to: {pdf_path}")


if __name__ == "__main__":
    main()
