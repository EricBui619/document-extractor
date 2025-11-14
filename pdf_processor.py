"""
PDF Processor Orchestrator
Main module that coordinates the entire PDF processing pipeline:
PDF → PNG → Content Extraction → HTML → PDF
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from pdf_to_png_converter import PDFtoPNGConverter
from openai_content_extractor import OpenAIContentExtractor
from html_generator import HTMLPageGenerator
from html_to_pdf_converter import HTMLtoPDFConverter
from image_processor import ImageProcessor
from key_value_converter import KeyValueConverter
from html_formatter import HTMLFormatter


class PDFProcessor:
    def __init__(self,
                 openai_api_key: str = None,
                 dpi: int = 300,
                 html_to_pdf_method: str = "weasyprint",
                 output_dir: str = "output"):
        """
        Initialize PDF Processor

        Args:
            openai_api_key: OpenAI API key for content extraction
            dpi: DPI for PNG conversion (default: 300)
            html_to_pdf_method: Method for HTML to PDF conversion
            output_dir: Base output directory for all generated files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Initialize components
        self.pdf_to_png = PDFtoPNGConverter(dpi=dpi)
        self.content_extractor = OpenAIContentExtractor(api_key=openai_api_key)
        self.html_generator = HTMLPageGenerator()
        self.html_to_pdf = HTMLtoPDFConverter(method=html_to_pdf_method)
        self.image_processor = ImageProcessor()
        self.kv_converter = KeyValueConverter()
        self.html_formatter = HTMLFormatter()

        # Create subdirectories
        self.png_dir = self.output_dir / "png_pages"
        self.content_dir = self.output_dir / "extracted_content"
        self.html_dir = self.output_dir / "html_pages"
        self.images_dir = self.output_dir / "extracted_images"

        for directory in [self.png_dir, self.content_dir, self.html_dir, self.images_dir]:
            directory.mkdir(exist_ok=True, parents=True)

        print(f"PDF Processor initialized")
        print(f"Output directory: {self.output_dir.absolute()}")

    def process_pdf(self,
                   pdf_path: str,
                   refine_tables: bool = True,
                   extract_images: bool = True,
                   progress_callback: Optional[Callable] = None,
                   max_workers: int = 4,
                   pages_to_process: Optional[List[int]] = None) -> Dict[str, str]:
        """
        Process entire PDF through the pipeline

        Args:
            pdf_path: Path to input PDF file
            refine_tables: Use second pass to refine table structures
            extract_images: Extract embedded images from PDF
            progress_callback: Optional callback function for progress updates
            max_workers: Maximum number of parallel threads for page processing (default: 4)
            pages_to_process: Optional list of specific page numbers to process (1-indexed).
                            If None, processes all pages.

        Returns:
            Dictionary with paths to generated files:
            {
                'original_pdf': str,
                'png_pages': List[str],
                'extracted_content': List[str],
                'html_pages': List[str],
                'final_pdf': str,
                'extracted_images': List[str],
                'metadata': Dict
            }
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        pdf_path = Path(pdf_path)
        print("\n" + "="*80)
        print(f"PROCESSING PDF: {pdf_path.name}")
        print("="*80)

        results = {
            'original_pdf': str(pdf_path),
            'png_pages': [],
            'extracted_content': [],
            'html_pages': [],
            'extracted_images': [],
            'final_pdf': None,
            'metadata': {}
        }

        # Step 1: Get PDF metadata
        self._update_progress(progress_callback, 0, "Reading PDF metadata")
        metadata = self.pdf_to_png.get_pdf_metadata(str(pdf_path))
        results['metadata'] = metadata
        total_pages = metadata['total_pages']
        print(f"\nPDF Info: {total_pages} pages, {metadata['page_width']}x{metadata['page_height']} pts")

        # Validate and process page selection
        if pages_to_process:
            # Validate page numbers
            pages_to_process = [p for p in pages_to_process if 1 <= p <= total_pages]
            pages_to_process = sorted(list(set(pages_to_process)))  # Remove duplicates and sort
            print(f"📄 Selected pages to process: {pages_to_process}")
        else:
            pages_to_process = list(range(1, total_pages + 1))
            print(f"📄 Processing all pages: 1-{total_pages}")

        # Step 2: Convert PDF to PNG images
        self._update_progress(progress_callback, 10, f"Converting PDF to PNG images ({len(pages_to_process)} pages)")
        page_info_list = self.pdf_to_png.convert_pdf_to_pngs(
            str(pdf_path),
            str(self.png_dir)
        )

        # Filter to only selected pages
        filtered_page_info_list = [page_info_list[p - 1] for p in pages_to_process]
        results['png_pages'] = [info['png_path'] for info in filtered_page_info_list]
        print(f"✓ Step 1 Complete: {len(filtered_page_info_list)} PNG pages created")

        # Step 2: Skip embedded image extraction - ONLY use visual region extraction
        # Visual diagrams are extracted after AI content analysis (more accurate)
        # No need to extract embedded PDF images beforehand
        print("⊘ Skipping embedded image extraction (will extract visual regions from page content)")

        # Step 3: Extract content from each page using OpenAI (Multi-threaded)
        self._update_progress(progress_callback, 20, "Extracting content from pages (OpenAI Vision) - Using parallel threads")

        # Use thread pool for parallel processing
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading

        # Thread-safe lists for collecting results
        num_pages_to_process = len(pages_to_process)
        pages_content = [None] * num_pages_to_process
        all_visual_images = []
        visual_images_lock = threading.Lock()

        # Determine number of threads (limit to avoid API rate limits)
        actual_max_workers = min(max_workers, num_pages_to_process)

        print(f"  🚀 Processing {num_pages_to_process} pages using {actual_max_workers} parallel threads...")

        def process_single_page(page_num, page_info, png_path):
            """Process a single page in a thread"""
            try:
                # Extract content (AI detects all text, tables, and visual elements)
                content = self.content_extractor.extract_page_content(png_path, page_num)

                # Step 3.0: Convert key-value pair text blocks to tables
                content = self.kv_converter.process_extracted_content(content)

                # Step 3.1: Extract visual regions from page PNG
                visual_images = self._extract_visual_regions_from_page(png_path, content, page_num)

                # Step 3.2: Link extracted visual images to content
                if visual_images:
                    self._link_images_to_content(content, visual_images)
                    print(f"  ✓ Page {page_num}: Linked {len(visual_images)} visual diagrams")

                # Refine tables if requested
                if refine_tables and content.get('tables'):
                    for table in content['tables']:
                        table['html'] = self.content_extractor.refine_table_structure(
                            table['html'],
                            png_path
                        )

                # Save content to JSON
                content_path = self.content_dir / f"page_{page_num}_content.json"
                with open(content_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)

                return {
                    'page_num': page_num,
                    'content': content,
                    'visual_images': visual_images,
                    'content_path': str(content_path)
                }
            except Exception as e:
                print(f"  ✗ Error processing page {page_num}: {str(e)}")
                return {
                    'page_num': page_num,
                    'content': None,
                    'visual_images': [],
                    'content_path': None,
                    'error': str(e)
                }

        # Submit all pages to thread pool
        with ThreadPoolExecutor(max_workers=actual_max_workers) as executor:
            # Submit tasks for selected pages only
            future_to_page = {}
            for idx, (page_num, page_info) in enumerate(zip(pages_to_process, filtered_page_info_list)):
                png_path = results['png_pages'][idx]
                future = executor.submit(process_single_page, page_num, page_info, png_path)
                future_to_page[future] = (page_num, idx)

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_page):
                page_num, idx = future_to_page[future]
                result = future.result()

                # Store content in correct order (by index in filtered list)
                pages_content[idx] = result['content']

                # Collect visual images (thread-safe)
                with visual_images_lock:
                    all_visual_images.extend(result['visual_images'])

                # Add to results
                if result['content_path']:
                    results['extracted_content'].append(result['content_path'])

                # Update progress
                completed += 1
                progress = 20 + int((40 / num_pages_to_process) * completed)
                self._update_progress(progress_callback, progress, f"Processed {completed}/{num_pages_to_process} pages")

        print(f"  ✓ All {num_pages_to_process} pages processed in parallel")

        print(f"✓ Step 3 Complete: Content extracted from all pages")

        # Step 3.5: Crop all extracted visual images to remove whitespace
        # This makes the result DIFFERENT from original - tightly cropped to diagram only
        if all_visual_images:
            self._update_progress(progress_callback, 60, "Cropping visual images to remove whitespace")
            all_visual_images = self._crop_extracted_images(all_visual_images)
            print(f"✓ Step 3.5 Complete: {len(all_visual_images)} visual images cropped")

            # Update content items with cropped image paths AND re-save JSON files
            for i, content in enumerate(pages_content, 1):
                updated = False
                if 'content_items' in content:
                    for item in content['content_items']:
                        if item.get('type') == 'image':
                            # Find matching cropped image by original path
                            original_path = item.get('image_path', '')
                            for visual_img in all_visual_images:
                                # Match by original_path (before cropping) or current image_path
                                if (visual_img.get('original_path') == original_path or
                                    visual_img.get('image_path', '').replace('_cropped', '') == original_path.replace('_cropped', '')):
                                    # Update to cropped path
                                    item['image_path'] = visual_img['image_path']
                                    updated = True
                                    break

                # CRITICAL: Also update legacy 'images' list with cropped paths
                # The HTML generator reads from the legacy 'images' list, not content_items
                if updated and 'images' in content:
                    for img in content['images']:
                        original_path = img.get('image_path', '')
                        for visual_img in all_visual_images:
                            # Match by original_path (before cropping) or current image_path
                            if (visual_img.get('original_path') == original_path or
                                visual_img.get('image_path', '').replace('_cropped', '') == original_path.replace('_cropped', '')):
                                # Update legacy images list to cropped path
                                img['image_path'] = visual_img['image_path']
                                break

                # Re-save JSON with updated cropped image paths (both content_items AND legacy images list)
                if updated:
                    content_path = self.content_dir / f"page_{i}_content.json"
                    with open(content_path, 'w', encoding='utf-8') as f:
                        json.dump(content, f, indent=2, ensure_ascii=False)
                    print(f"  ✓ Updated page {i} content JSON with cropped image paths")

            # Update results with all visual images (cropped versions)
            results['extracted_images'].extend([img['image_path'] for img in all_visual_images])

        # Step 4: Generate HTML for each page
        self._update_progress(progress_callback, 70, "Generating HTML pages")
        html_paths = []

        for content, page_info, page_num in zip(pages_content, filtered_page_info_list, pages_to_process):
            html_path = self.html_dir / f"page_{page_num}.html"
            self.html_generator.generate_page_html(
                content,
                page_info,
                str(html_path)
            )
            html_paths.append(str(html_path))
            results['html_pages'].append(str(html_path))

        print(f"✓ Step 4 Complete: {len(html_paths)} HTML pages generated")

        # Step 4.5: Review and format HTML files for better readability
        self._update_progress(progress_callback, 75, "Formatting HTML files for better readability")
        print(f"\n📝 Formatting {len(html_paths)} HTML files for better readability...")

        formatted_count = 0
        for html_path in html_paths:
            try:
                self.html_formatter.apply_readability_improvements(html_path)
                formatted_count += 1
            except Exception as e:
                print(f"  ⚠ Warning: Could not format {Path(html_path).name}: {str(e)}")

        print(f"✓ Step 4.5 Complete: Formatted {formatted_count}/{len(html_paths)} HTML files")

        # Also generate a single multi-page HTML document
        self._update_progress(progress_callback, 80, "Generating multi-page HTML document")
        multi_page_html = self.output_dir / "reconstructed_document.html"
        self.html_generator.generate_multi_page_html(
            pages_content,
            filtered_page_info_list,
            str(multi_page_html)
        )
        print(f"✓ Multi-page HTML created: {multi_page_html.name}")

        # Format the multi-page HTML as well
        try:
            self.html_formatter.apply_readability_improvements(str(multi_page_html))
            print(f"  ✓ Formatted multi-page HTML for better readability")
        except Exception as e:
            print(f"  ⚠ Warning: Could not format multi-page HTML: {str(e)}")

        # Step 5: Convert HTML pages to PDF and merge
        self._update_progress(progress_callback, 85, "Converting HTML to PDF")
        final_pdf_path = self.output_dir / f"{pdf_path.stem}_reconstructed.pdf"

        # Use multi-page HTML for cleaner conversion
        final_pdf = self.html_to_pdf.convert_multi_page_html_to_pdf(
            str(multi_page_html),
            str(final_pdf_path),
            page_width=f"{metadata['page_width']}pt",
            page_height=f"{metadata['page_height']}pt"
        )

        results['final_pdf'] = final_pdf
        print(f"✓ Step 5 Complete: Final PDF created")

        # Step 6: Generate summary report
        self._update_progress(progress_callback, 95, "Generating summary report")
        self._generate_summary_report(results, pages_content)

        self._update_progress(progress_callback, 100, "Processing complete!")

        print("\n" + "="*80)
        print("PROCESSING COMPLETE!")
        print("="*80)
        print(f"\nGenerated Files:")
        print(f"  • PNG Pages: {len(results['png_pages'])} files in {self.png_dir}")
        print(f"  • Extracted Content: {len(results['extracted_content'])} files in {self.content_dir}")
        print(f"  • HTML Pages: {len(results['html_pages'])} files in {self.html_dir}")
        print(f"  • Extracted Images: {len(results['extracted_images'])} files in {self.images_dir}")
        print(f"  • Final PDF: {results['final_pdf']}")
        print(f"\nAll outputs saved to: {self.output_dir.absolute()}")

        return results

    def _update_progress(self, callback: Optional[Callable], progress: int, message: str):
        """Update progress if callback is provided"""
        if callback:
            callback(progress, message)


    def _extract_visual_regions_from_page(self, page_png_path: str, content: Dict, page_num: int,
                                          extraction_padding: int = 20) -> List[Dict]:
        """
        Extract visual regions (diagrams, shapes, charts) from page PNG based on AI-detected bounding boxes
        This captures visual elements that may not be embedded images in the PDF

        The AI is instructed to include ALL related text in the bounding box:
        - Labels, annotations, captions
        - Legends and axis labels
        - Any text that is part of or describes the diagram

        Args:
            page_png_path: Path to the page PNG image
            content: Extracted content with image bounding boxes (AI includes labels/captions/annotations)
            page_num: Page number
            extraction_padding: Pixels to add around bounding box as safety margin (default: 20)

        Returns:
            List of dicts with image_path, bounds, metadata for each visual element
        """
        from PIL import Image
        import numpy as np

        if not os.path.exists(page_png_path):
            return []

        # Get image items from content
        image_items = []
        if 'content_items' in content:
            image_items = [item for item in content['content_items'] if item.get('type') == 'image']

        if not image_items:
            return []

        print(f"  📸 Extracting {len(image_items)} visual regions from page {page_num}...")

        # Open page PNG
        page_img = Image.open(page_png_path)
        page_width, page_height = page_img.size

        extracted_visuals = []

        for idx, item in enumerate(image_items, 1):
            position = item.get('position', {})

            # Get bounding box percentages
            x_start_pct = position.get('x_start', 0)
            y_start_pct = position.get('y_start', 0)
            x_end_pct = position.get('x_end', 100)
            y_end_pct = position.get('y_end', 100)

            # Convert percentages to pixel coordinates
            x1 = int((x_start_pct / 100) * page_width)
            y1 = int((y_start_pct / 100) * page_height)
            x2 = int((x_end_pct / 100) * page_width)
            y2 = int((y_end_pct / 100) * page_height)

            # Add padding to capture full visual element (zoom out to include complete diagram)
            # Note: AI is instructed to include labels, annotations, captions in bounding box
            # This padding is additional safety margin to avoid cutting off edges
            x1 = max(0, x1 - extraction_padding)
            y1 = max(0, y1 - extraction_padding)
            x2 = min(page_width, x2 + extraction_padding)
            y2 = min(page_height, y2 + extraction_padding)

            # Skip invalid bounds
            if x2 <= x1 or y2 <= y1:
                continue

            # Crop the visual region
            visual_region = page_img.crop((x1, y1, x2, y2))

            # Save to images directory
            image_type = item.get('metadata', {}).get('image_type', 'visual')
            output_filename = f"page_{page_num}_visual_{idx}_{image_type}.png"
            output_path = self.images_dir / output_filename

            visual_region.save(output_path, format='PNG', optimize=True)

            # Create metadata
            visual_info = {
                'image_path': str(output_path),
                'page_num': page_num,
                'visual_index': idx,
                'image_type': image_type,
                'bounds': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                'bounds_pct': position,
                'width': x2 - x1,
                'height': y2 - y1,
                'description': item.get('metadata', {}).get('description', ''),
                'format': 'PNG'
            }

            extracted_visuals.append(visual_info)
            # Show extraction details including bounding box position
            print(f"    ✓ Extracted visual {idx}: {image_type}")
            print(f"      Size: {x2-x1}x{y2-y1}px | Position: ({x_start_pct:.1f}%, {y_start_pct:.1f}%) to ({x_end_pct:.1f}%, {y_end_pct:.1f}%)")
            if item.get('metadata', {}).get('description'):
                desc = item['metadata']['description'][:60]  # Truncate long descriptions
                print(f"      Description: {desc}...")

        return extracted_visuals

    def _link_images_to_content(self, content: Dict, page_images: List[Dict]):
        """
        Link extracted images with detected image positions in content
        Matches images by position or index and adds image_path to content items
        """
        if not page_images:
            return

        # Try to match images in content_items (new format)
        if 'content_items' in content:
            image_items = [item for item in content['content_items'] if item.get('type') == 'image']

            # Match by index - try both image_index and visual_index
            for idx, item in enumerate(image_items):
                # AI provides image_index (1-based), visual extraction provides visual_index
                image_index = item.get('metadata', {}).get('image_index', idx + 1)

                # Find matching extracted image (1-indexed)
                matched = False
                if 0 < image_index <= len(page_images):
                    extracted_img = page_images[image_index - 1]

                    # Check if this is the right match by visual_index
                    visual_idx = extracted_img.get('visual_index', image_index)
                    if visual_idx == image_index or len(page_images) == 1:
                        item['image_path'] = extracted_img['image_path']
                        item['metadata']['image_format'] = extracted_img.get('format', 'PNG')
                        item['metadata']['image_width'] = extracted_img.get('width', 0)
                        item['metadata']['image_height'] = extracted_img.get('height', 0)
                        matched = True

                # Fallback: match by order if index didn't work
                if not matched and idx < len(page_images):
                    extracted_img = page_images[idx]
                    item['image_path'] = extracted_img['image_path']
                    item['metadata']['image_format'] = extracted_img.get('format', 'PNG')
                    item['metadata']['image_width'] = extracted_img.get('width', 0)
                    item['metadata']['image_height'] = extracted_img.get('height', 0)

        # Also update legacy format images list
        if 'images' in content:
            for idx, img in enumerate(content['images']):
                if idx < len(page_images):
                    extracted_img = page_images[idx]
                    img['image_path'] = extracted_img['image_path']
                    img['format'] = extracted_img.get('format', 'PNG')

    def _crop_extracted_images(self, extracted_images: List[Dict], padding: int = 10) -> List[Dict]:
        """
        Crop whitespace from extracted images and delete original uncropped versions
        Only keeps the cropped (latest) version

        Args:
            extracted_images: List of extracted image dicts
            padding: Pixels to keep around content

        Returns:
            List of image dicts with updated paths to cropped images
        """
        if not extracted_images:
            return []

        print(f"\n📐 Cropping {len(extracted_images)} images to remove whitespace...")

        cropped_images = []
        for img_info in extracted_images:
            image_path = img_info['image_path']

            # Crop the image
            cropped_path = self.image_processor.crop_whitespace(image_path, padding=padding)

            # Delete original uncropped image (keep only the latest cropped version)
            if cropped_path != image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"  🗑️  Deleted original: {Path(image_path).name}")
                except Exception as e:
                    print(f"  ⚠ Could not delete original {Path(image_path).name}: {e}")

            # Update image info with cropped path
            img_info_copy = img_info.copy()
            img_info_copy['image_path'] = cropped_path
            img_info_copy['original_path'] = image_path
            img_info_copy['is_cropped'] = (cropped_path != image_path)

            cropped_images.append(img_info_copy)

        return cropped_images

    def _generate_summary_report(self, results: Dict, pages_content: List[Dict]):
        """Generate a summary report of the processing"""
        report_path = self.output_dir / "processing_report.json"

        # Collect statistics
        total_tables = sum(len(page.get('tables', [])) for page in pages_content)
        total_images = sum(len(page.get('images', [])) for page in pages_content)
        total_text_blocks = sum(len(page.get('text_blocks', [])) for page in pages_content)

        report = {
            'original_pdf': results['original_pdf'],
            'metadata': results['metadata'],
            'statistics': {
                'total_pages': len(pages_content),
                'total_tables': total_tables,
                'total_images_detected': total_images,
                'total_images_extracted': len(results['extracted_images']),
                'total_text_blocks': total_text_blocks
            },
            'page_details': []
        }

        # Add per-page details
        for i, content in enumerate(pages_content, 1):
            page_detail = {
                'page_num': i,
                'tables_count': len(content.get('tables', [])),
                'images_count': len(content.get('images', [])),
                'text_blocks_count': len(content.get('text_blocks', [])),
                'layout': content.get('layout', {})
            }
            report['page_details'].append(page_detail)

        # Save report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Processing report saved: {report_path.name}")
        print(f"\nStatistics:")
        print(f"  • Total Tables: {total_tables}")
        print(f"  • Total Images: {total_images}")
        print(f"  • Total Text Blocks: {total_text_blocks}")

    def process_single_page(self, pdf_path: str, page_num: int) -> Dict:
        """
        Process a single page from a PDF

        Args:
            pdf_path: Path to input PDF file
            page_num: Page number to process (1-indexed)

        Returns:
            Dictionary with results for the single page
        """
        print(f"\nProcessing single page {page_num} from {Path(pdf_path).name}")

        # Convert single page to PNG
        page_info_list = self.pdf_to_png.convert_pdf_to_pngs(str(pdf_path), str(self.png_dir))

        if page_num > len(page_info_list):
            raise ValueError(f"Page {page_num} does not exist (PDF has {len(page_info_list)} pages)")

        page_info = page_info_list[page_num - 1]
        png_path = page_info['png_path']

        # Extract content
        content = self.content_extractor.extract_page_content(png_path, page_num)

        # Save content
        content_path = self.content_dir / f"page_{page_num}_content.json"
        with open(content_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        # Generate HTML
        html_path = self.html_dir / f"page_{page_num}.html"
        self.html_generator.generate_page_html(content, page_info, str(html_path))

        return {
            'page_num': page_num,
            'png_path': png_path,
            'content_path': str(content_path),
            'html_path': str(html_path),
            'content': content
        }


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Process PDF with 100% structure preservation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process entire PDF
  python pdf_processor.py input.pdf

  # Process with custom output directory
  python pdf_processor.py input.pdf --output-dir my_output

  # Process single page
  python pdf_processor.py input.pdf --page 5

  # Skip table refinement for faster processing
  python pdf_processor.py input.pdf --no-refine-tables
        """
    )

    parser.add_argument('pdf_path', help='Path to input PDF file')
    parser.add_argument('--output-dir', default='output', help='Output directory (default: output)')
    parser.add_argument('--page', type=int, help='Process only specific page number')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for PNG conversion (default: 300)')
    parser.add_argument('--no-refine-tables', action='store_true', help='Skip table refinement')
    parser.add_argument('--no-extract-images', action='store_true', help='Skip image extraction')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY in .env)')
    parser.add_argument('--html-method', choices=['skip', 'weasyprint', 'playwright', 'pdfkit'],
                       default='skip', help='HTML to PDF conversion method (default: skip)')

    args = parser.parse_args()

    # Get API key from args or environment
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("Error: OpenAI API key not found!")
        print("Please either:")
        print("  1. Set OPENAI_API_KEY in .env file, or")
        print("  2. Pass --api-key argument")
        return 1

    # Create processor
    processor = PDFProcessor(
        openai_api_key=api_key,
        dpi=args.dpi,
        html_to_pdf_method=args.html_method,
        output_dir=args.output_dir
    )

    try:
        if args.page:
            # Process single page
            results = processor.process_single_page(args.pdf_path, args.page)
            print(f"\n✓ Page {args.page} processed successfully")
            print(f"  HTML: {results['html_path']}")
        else:
            # Process entire PDF
            results = processor.process_pdf(
                args.pdf_path,
                refine_tables=not args.no_refine_tables,
                extract_images=not args.no_extract_images
            )
            print(f"\n✓ PDF processed successfully")
            print(f"  Final PDF: {results['final_pdf']}")

    except Exception as e:
        print(f"\n✗ Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
