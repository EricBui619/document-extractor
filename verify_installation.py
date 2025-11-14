#!/usr/bin/env python3
"""
Installation Verification Script
Checks that all required dependencies are installed correctly
"""

import sys

def check_module(module_name, package_name=None):
    """Check if a module can be imported"""
    package = package_name or module_name
    try:
        __import__(module_name)
        print(f"✓ {package}")
        return True
    except ImportError as e:
        print(f"✗ {package} - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("PDF Document Extractor - Installation Verification")
    print("=" * 60)
    print()

    required_modules = [
        ('streamlit', 'Streamlit'),
        ('openai', 'OpenAI'),
        ('dotenv', 'python-dotenv'),
        ('fitz', 'PyMuPDF'),
        ('PIL', 'Pillow'),
        ('PyPDF2', 'PyPDF2'),
        ('cv2', 'opencv-python'),
        ('numpy', 'NumPy'),
        ('pyarrow', 'PyArrow'),
    ]

    print("Checking required packages:")
    print("-" * 60)

    all_ok = True
    for module, package in required_modules:
        if not check_module(module, package):
            all_ok = False

    print()
    print("=" * 60)

    if all_ok:
        print("✓ All dependencies installed successfully!")
        print()
        print("Next steps:")
        print("1. Set your OpenAI API key:")
        print("   export OPENAI_API_KEY='sk-your-api-key-here'")
        print()
        print("2. Run the application:")
        print("   streamlit run pdf_processor_app.py")
        print()
        print("=" * 60)
        return 0
    else:
        print("✗ Some dependencies are missing!")
        print()
        print("Please run: pip install -r requirements.txt")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
