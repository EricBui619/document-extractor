"""
PDF to PNG Converter Module
Converts each PDF page to high-resolution PNG images using pure Python (non-AI)
"""

import os
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
from PIL import Image


class PDFtoPNGConverter:
    def __init__(self, dpi: int = 300):
        """
        Initialize PDF to PNG converter

        Args:
            dpi: Dots per inch for output PNG images (default: 300 for high quality)
        """
        self.dpi = dpi
        self.zoom = dpi / 72  # PDF default is 72 DPI

    def convert_pdf_to_pngs(self, pdf_path: str, output_dir: str = None) -> List[dict]:
        """
        Convert all pages of a PDF to PNG images

        Args:
            pdf_path: Path to the input PDF file
            output_dir: Directory to save PNG files (default: creates 'png_pages' folder)

        Returns:
            List of dictionaries containing page information:
            [
                {
                    'page_num': 1,
                    'png_path': '/path/to/page_1.png',
                    'width': 2550,
                    'height': 3300,
                    'original_width': 612,
                    'original_height': 792
                },
                ...
            ]
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Create output directory
        if output_dir is None:
            output_dir = Path(pdf_path).parent / "png_pages"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(exist_ok=True, parents=True)

        print(f"Converting PDF to PNG images at {self.dpi} DPI...")
        print(f"Input PDF: {pdf_path}")
        print(f"Output directory: {output_dir}")

        # Open PDF
        pdf_document = fitz.open(pdf_path)
        page_info_list = []

        try:
            total_pages = len(pdf_document)
            print(f"Total pages: {total_pages}")

            for page_num in range(total_pages):
                # Get page
                page = pdf_document[page_num]

                # Get original dimensions (in points)
                original_rect = page.rect
                original_width = original_rect.width
                original_height = original_rect.height

                # Create transformation matrix for high-resolution rendering
                mat = fitz.Matrix(self.zoom, self.zoom)

                # Render page to pixmap (image)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                # Save as PNG
                png_filename = f"page_{page_num + 1}.png"
                png_path = output_dir / png_filename
                pix.save(png_path)

                # Store page information
                page_info = {
                    'page_num': page_num + 1,
                    'png_path': str(png_path),
                    'width': pix.width,
                    'height': pix.height,
                    'original_width': original_width,
                    'original_height': original_height,
                    'dpi': self.dpi
                }
                page_info_list.append(page_info)

                print(f"  ✓ Page {page_num + 1}/{total_pages}: {png_filename} ({pix.width}x{pix.height})")

        finally:
            pdf_document.close()

        print(f"\nConversion complete! {len(page_info_list)} pages saved to {output_dir}")
        return page_info_list

    def extract_images_from_pdf(self, pdf_path: str, output_dir: str = None) -> List[dict]:
        """
        Extract embedded images directly from PDF (without rendering)
        This preserves original image quality without any conversion

        Args:
            pdf_path: Path to the input PDF file
            output_dir: Directory to save extracted images

        Returns:
            List of dictionaries containing extracted image information
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Create output directory
        if output_dir is None:
            output_dir = Path(pdf_path).parent / "extracted_images"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(exist_ok=True, parents=True)

        print(f"Extracting embedded images from PDF...")
        print(f"Input PDF: {pdf_path}")
        print(f"Output directory: {output_dir}")

        pdf_document = fitz.open(pdf_path)
        extracted_images = []

        try:
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                image_list = page.get_images(full=True)

                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]  # Image XREF number

                    # Extract image
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    # Save image
                    image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                    image_path = output_dir / image_filename

                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)

                    # Get image position on page
                    img_rects = page.get_image_rects(xref)

                    extracted_images.append({
                        'page_num': page_num + 1,
                        'image_path': str(image_path),
                        'filename': image_filename,
                        'format': image_ext,
                        'xref': xref,
                        'width': base_image.get("width", 0),
                        'height': base_image.get("height", 0),
                        'rects': [list(rect) for rect in img_rects]  # Bounding boxes
                    })

                    print(f"  ✓ Page {page_num + 1}, Image {img_index + 1}: {image_filename}")

        finally:
            pdf_document.close()

        print(f"\nExtraction complete! {len(extracted_images)} images extracted to {output_dir}")
        return extracted_images

    def get_pdf_metadata(self, pdf_path: str) -> dict:
        """
        Get metadata information from PDF

        Args:
            pdf_path: Path to the input PDF file

        Returns:
            Dictionary containing PDF metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        pdf_document = fitz.open(pdf_path)

        try:
            metadata = {
                'title': pdf_document.metadata.get('title', ''),
                'author': pdf_document.metadata.get('author', ''),
                'subject': pdf_document.metadata.get('subject', ''),
                'creator': pdf_document.metadata.get('creator', ''),
                'producer': pdf_document.metadata.get('producer', ''),
                'creation_date': pdf_document.metadata.get('creationDate', ''),
                'modification_date': pdf_document.metadata.get('modDate', ''),
                'total_pages': len(pdf_document),
                'is_encrypted': pdf_document.is_encrypted,
                'is_pdf': pdf_document.is_pdf
            }

            # Get first page dimensions as reference
            if len(pdf_document) > 0:
                first_page = pdf_document[0]
                metadata['page_width'] = first_page.rect.width
                metadata['page_height'] = first_page.rect.height

            return metadata

        finally:
            pdf_document.close()


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Convert PDF pages to PNG images')
    parser.add_argument('pdf_path', help='Path to the input PDF file')
    parser.add_argument('--output-dir', help='Output directory for PNG files')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for output images (default: 300)')
    parser.add_argument('--extract-images', action='store_true',
                       help='Extract embedded images from PDF')
    parser.add_argument('--metadata', action='store_true',
                       help='Show PDF metadata')

    args = parser.parse_args()

    converter = PDFtoPNGConverter(dpi=args.dpi)

    if args.metadata:
        metadata = converter.get_pdf_metadata(args.pdf_path)
        print("\nPDF Metadata:")
        print("=" * 60)
        for key, value in metadata.items():
            print(f"{key}: {value}")
        print("=" * 60)

    if args.extract_images:
        extracted_images = converter.extract_images_from_pdf(args.pdf_path, args.output_dir)
        print(f"\nExtracted {len(extracted_images)} images")
    else:
        page_info = converter.convert_pdf_to_pngs(args.pdf_path, args.output_dir)
        print(f"\nConverted {len(page_info)} pages")


if __name__ == "__main__":
    main()
