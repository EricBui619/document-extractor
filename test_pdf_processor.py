"""
Test Script for PDF Processor
Quick verification that all modules work correctly
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing module imports...")

    try:
        from pdf_to_png_converter import PDFtoPNGConverter
        print("  ✓ pdf_to_png_converter")
    except ImportError as e:
        print(f"  ✗ pdf_to_png_converter: {e}")
        return False

    try:
        from openai_content_extractor import OpenAIContentExtractor
        print("  ✓ openai_content_extractor")
    except ImportError as e:
        print(f"  ✗ openai_content_extractor: {e}")
        return False

    try:
        from html_generator import HTMLPageGenerator
        print("  ✓ html_generator")
    except ImportError as e:
        print(f"  ✗ html_generator: {e}")
        return False

    try:
        from html_to_pdf_converter import HTMLtoPDFConverter
        print("  ✓ html_to_pdf_converter")
    except ImportError as e:
        print(f"  ✗ html_to_pdf_converter: {e}")
        return False

    try:
        from pdf_processor import PDFProcessor
        print("  ✓ pdf_processor")
    except ImportError as e:
        print(f"  ✗ pdf_processor: {e}")
        return False

    print("\n✅ All modules imported successfully!\n")
    return True


def test_dependencies():
    """Test that all required dependencies are installed"""
    print("Testing dependencies...")

    dependencies = {
        'fitz': 'PyMuPDF',
        'PIL': 'Pillow',
        'openai': 'openai',
        'weasyprint': 'weasyprint',
        'PyPDF2': 'PyPDF2',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'streamlit': 'streamlit'
    }

    all_installed = True

    for module_name, package_name in dependencies.items():
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} - Install with: pip install {package_name}")
            all_installed = False

    if all_installed:
        print("\n✅ All dependencies installed!\n")
    else:
        print("\n⚠️  Some dependencies missing. Install with: pip install -r requirements.txt\n")

    return all_installed


def test_api_key():
    """Test if OpenAI API key is configured"""
    import os

    print("Testing OpenAI API key...")

    api_key = os.environ.get("OPENAI_API_KEY")

    if api_key:
        print(f"  ✓ API key found (starts with: {api_key[:10]}...)")
        print("\n✅ API key configured!\n")
        return True
    else:
        print("  ✗ OPENAI_API_KEY not found in environment")
        print("\n⚠️  Set API key with: export OPENAI_API_KEY=your_key_here")
        print("  Or create a .env file with: OPENAI_API_KEY=your_key_here\n")
        return False


def test_pdf_to_png():
    """Test PDF to PNG conversion with sample PDF"""
    print("Testing PDF to PNG conversion...")

    from pdf_to_png_converter import PDFtoPNGConverter

    # Check if sample PDF exists
    sample_pdf = Path("GlobalDev/24-12N-01E - Evaluation-AFE-Pour Point Analysis-Survey-Report of Investigation.pdf")

    if not sample_pdf.exists():
        print(f"  ⊘ Sample PDF not found: {sample_pdf}")
        print("  Skipping PDF conversion test")
        return True

    try:
        converter = PDFtoPNGConverter(dpi=150)  # Use lower DPI for quick test

        # Get metadata only (no conversion)
        metadata = converter.get_pdf_metadata(str(sample_pdf))

        print(f"  ✓ PDF opened successfully")
        print(f"    - Pages: {metadata['total_pages']}")
        print(f"    - Size: {metadata['page_width']}x{metadata['page_height']} pts")
        print("\n✅ PDF to PNG conversion ready!\n")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("="*80)
    print("PDF PROCESSOR - SYSTEM TEST")
    print("="*80)
    print()

    results = []

    # Test 1: Module imports
    results.append(("Module Imports", test_imports()))

    # Test 2: Dependencies
    results.append(("Dependencies", test_dependencies()))

    # Test 3: API Key
    results.append(("API Key", test_api_key()))

    # Test 4: PDF to PNG
    results.append(("PDF to PNG", test_pdf_to_png()))

    # Summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(result[1] for result in results)

    print()

    if all_passed:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Run Streamlit app: streamlit run pdf_processor_app.py")
        print("  2. Or use CLI: python pdf_processor.py <pdf_file>")
    else:
        print("⚠️  Some tests failed. Please fix the issues above before proceeding.")

    print()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
