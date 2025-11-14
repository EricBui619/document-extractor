# Dockerfile for PDF Document Extractor
# Production-ready container with all dependencies

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for WeasyPrint
RUN apt-get update && apt-get install -y \
    # Core build tools
    build-essential \
    # WeasyPrint dependencies
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Additional libraries
    libxml2 \
    libxslt1.1 \
    libxslt1-dev \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary pyarrow && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create output directory
RUN mkdir -p output

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import streamlit; print('healthy')" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run the application
CMD ["streamlit", "run", "pdf_processor_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
