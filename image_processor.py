"""
Image Processing Module
Handles image cropping, optimization, and preparation for HTML embedding
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import numpy as np


class ImageProcessor:
    """Process images for optimal HTML display"""

    def __init__(self):
        """Initialize image processor"""
        pass

    def crop_whitespace(self, image_path: str, padding: int = 10) -> str:
        """
        Crop whitespace from image borders and save as new file

        Args:
            image_path: Path to input image
            padding: Pixels to keep around content (default: 10)

        Returns:
            Path to cropped image file
        """
        if not os.path.exists(image_path):
            print(f"Warning: Image not found: {image_path}")
            return image_path

        try:
            # Open image
            img = Image.open(image_path)

            # Convert to RGB if needed (handles RGBA, grayscale, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Convert to numpy array for processing
            img_array = np.array(img)

            # Calculate bounding box of non-white content
            bbox = self._find_content_bbox(img_array)

            if bbox is None:
                print(f"  ⚠ Could not detect content boundaries in {Path(image_path).name}")
                return image_path

            # Add padding
            height, width = img_array.shape[:2]
            x1, y1, x2, y2 = bbox

            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(width, x2 + padding)
            y2 = min(height, y2 + padding)

            # Crop image
            cropped_img = img.crop((x1, y1, x2, y2))

            # Generate output path
            input_path = Path(image_path)
            output_path = input_path.parent / f"{input_path.stem}_cropped{input_path.suffix}"

            # Save cropped image
            cropped_img.save(output_path, quality=95, optimize=True)

            # Calculate size reduction
            original_size = os.path.getsize(image_path)
            cropped_size = os.path.getsize(output_path)
            reduction = ((original_size - cropped_size) / original_size) * 100

            print(f"  ✓ Cropped: {input_path.name}")
            print(f"    Original: {width}x{height} → Cropped: {x2-x1}x{y2-y1}")
            print(f"    Size: {original_size//1024}KB → {cropped_size//1024}KB ({reduction:.1f}% reduction)")

            return str(output_path)

        except Exception as e:
            print(f"  ✗ Error cropping {Path(image_path).name}: {e}")
            return image_path

    def _find_content_bbox(self, img_array: np.ndarray,
                          white_threshold: int = 240) -> Optional[Tuple[int, int, int, int]]:
        """
        Find bounding box of non-white content in image

        Args:
            img_array: Image as numpy array (H, W, 3)
            white_threshold: Pixel value above which is considered white (0-255)

        Returns:
            Tuple of (x1, y1, x2, y2) or None if no content found
        """
        # Create mask of non-white pixels
        # Pixel is "white" if all RGB channels are >= threshold
        is_white = np.all(img_array >= white_threshold, axis=2)
        is_content = ~is_white

        # Find rows and columns with content
        rows_with_content = np.any(is_content, axis=1)
        cols_with_content = np.any(is_content, axis=0)

        # Find bounding box
        if not np.any(rows_with_content) or not np.any(cols_with_content):
            return None

        y_indices = np.where(rows_with_content)[0]
        x_indices = np.where(cols_with_content)[0]

        y1 = y_indices[0]
        y2 = y_indices[-1] + 1
        x1 = x_indices[0]
        x2 = x_indices[-1] + 1

        return (x1, y1, x2, y2)

    def crop_all_images_in_directory(self, images_dir: str,
                                     padding: int = 10) -> dict:
        """
        Crop all images in a directory

        Args:
            images_dir: Directory containing images
            padding: Pixels to keep around content

        Returns:
            Dictionary mapping original paths to cropped paths
        """
        images_dir = Path(images_dir)

        if not images_dir.exists():
            print(f"Warning: Directory not found: {images_dir}")
            return {}

        # Find all image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
        image_files = [
            f for f in images_dir.iterdir()
            if f.suffix.lower() in image_extensions and '_cropped' not in f.stem
        ]

        if not image_files:
            print(f"No images found in {images_dir}")
            return {}

        print(f"\nCropping {len(image_files)} images...")

        mapping = {}
        for img_path in image_files:
            cropped_path = self.crop_whitespace(str(img_path), padding=padding)
            mapping[str(img_path)] = cropped_path

        print(f"✓ Completed cropping {len(image_files)} images")

        return mapping

    def optimize_image(self, image_path: str, max_width: int = 1200,
                      quality: int = 85) -> str:
        """
        Optimize image for web display (resize if too large, compress)

        Args:
            image_path: Path to image
            max_width: Maximum width in pixels
            quality: JPEG quality (1-100)

        Returns:
            Path to optimized image
        """
        if not os.path.exists(image_path):
            return image_path

        try:
            img = Image.open(image_path)

            # Resize if too wide
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)
                print(f"  ↓ Resized to {max_width}x{new_height}")

            # Save optimized
            output_path = Path(image_path).parent / f"{Path(image_path).stem}_opt{Path(image_path).suffix}"
            img.save(output_path, quality=quality, optimize=True)

            original_size = os.path.getsize(image_path)
            opt_size = os.path.getsize(output_path)
            reduction = ((original_size - opt_size) / original_size) * 100

            print(f"  ✓ Optimized: {original_size//1024}KB → {opt_size//1024}KB ({reduction:.1f}% reduction)")

            return str(output_path)

        except Exception as e:
            print(f"  ✗ Error optimizing {Path(image_path).name}: {e}")
            return image_path

    def crop_and_optimize(self, image_path: str, padding: int = 10,
                         max_width: int = 1200, quality: int = 85) -> str:
        """
        Crop whitespace and optimize image in one step

        Args:
            image_path: Path to input image
            padding: Pixels to keep around content
            max_width: Maximum width in pixels
            quality: JPEG quality (1-100)

        Returns:
            Path to processed image
        """
        # First crop
        cropped_path = self.crop_whitespace(image_path, padding=padding)

        # Then optimize
        if cropped_path != image_path:
            optimized_path = self.optimize_image(cropped_path, max_width=max_width, quality=quality)
            return optimized_path

        return image_path


def crop_extracted_images(output_dir: str, padding: int = 10):
    """
    Convenience function to crop all extracted images

    Args:
        output_dir: Output directory containing extracted_images folder
        padding: Pixels to keep around content
    """
    images_dir = Path(output_dir) / "extracted_images"

    if not images_dir.exists():
        print(f"No extracted_images directory found in {output_dir}")
        return

    processor = ImageProcessor()
    mapping = processor.crop_all_images_in_directory(str(images_dir), padding=padding)

    return mapping


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        processor = ImageProcessor()
        cropped = processor.crop_whitespace(image_path)
        print(f"Cropped image saved to: {cropped}")
    else:
        print("Usage: python image_processor.py <image_path>")
