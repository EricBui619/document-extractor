#!/bin/bash
# Quick setup script for PDF Document Extractor

set -e

echo "=========================================="
echo "PDF Document Extractor - Quick Setup"
echo "=========================================="
echo ""

# Step 1: Install dependencies
echo "Step 1/3: Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""

# Step 2: Verify installation
echo "Step 2/3: Verifying installation..."
python3 verify_installation.py

echo ""

# Step 3: Setup .env file
echo "Step 3/3: Setting up .env file..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env file from template"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env and add your OpenAI API key!"
        echo "   Open .env and replace 'your_openai_api_key_here' with your actual key"
    else
        echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
        echo "✓ Created .env file"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env and add your OpenAI API key!"
    fi
else
    echo "✓ .env file already exists"
fi

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OpenAI API key"
echo "2. Run: streamlit run pdf_processor_app.py"
echo ""
echo "The app will open at http://localhost:8501"
echo ""
