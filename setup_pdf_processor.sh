#!/bin/bash

# Setup script for PDF Processor
# This script installs all required dependencies

echo "=================================="
echo "PDF Processor - Setup Script"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found"
echo ""

# Create virtual environment (optional but recommended)
echo "Do you want to create a virtual environment? (recommended) [y/n]"
read -r create_venv

if [ "$create_venv" = "y" ] || [ "$create_venv" = "Y" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "✅ Virtual environment created and activated"
    echo ""
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""

# Check if installation was successful
echo "Verifying installation..."
python3 test_pdf_processor.py

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Set your OpenAI API key:"
echo "   export OPENAI_API_KEY='your-api-key-here'"
echo "   Or create a .env file with: OPENAI_API_KEY=your-api-key-here"
echo ""
echo "2. Run the Streamlit app:"
echo "   streamlit run pdf_processor_app.py"
echo ""
echo "3. Or use the command line:"
echo "   python3 pdf_processor.py <path-to-pdf>"
echo ""
