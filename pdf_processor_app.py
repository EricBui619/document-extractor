"""
Streamlit Application for PDF Processing
User-friendly interface for PDF content extraction with structure preservation
"""

import streamlit as st
import os
import sys
from pathlib import Path
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_processor import PDFProcessor

# Page configuration
st.set_page_config(
    page_title="PDF Content Extractor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .success-box {
        background: #d1fae5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    .info-box {
        background: #dbeafe;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fef3c7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #3b82f6;
    }
    .stat-label {
        color: #6b7280;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'report' not in st.session_state:
        st.session_state.report = None


def display_header():
    """Display application header"""
    st.markdown('<h1 class="main-header">📄 PDF Content Extractor</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Extract tables and images from PDFs with 100% structure preservation using AI</p>',
        unsafe_allow_html=True
    )


def display_sidebar(uploaded_file=None):
    """Display sidebar with settings"""
    with st.sidebar:
        st.header("⚙️ Settings")

        # Load API key from environment
        api_key = os.getenv("OPENAI_API_KEY", "")

        # Show API key status
        if api_key:
            st.success("✓ OpenAI API Key loaded from .env")
        else:
            st.error("✗ OpenAI API Key not found in .env file")
            st.markdown("""
            **Setup Instructions:**
            1. Create a `.env` file in the project root
            2. Add: `OPENAI_API_KEY=sk-your-key-here`
            3. Restart the application
            """)

        st.divider()

        st.subheader("📄 Page Selection")

        # Page selection options
        page_selection_mode = st.radio(
            "Select pages to extract:",
            options=["All pages", "Specific pages", "Page range"],
            index=0,
            help="Choose which pages to extract from the PDF"
        )

        selected_pages = None
        page_range_start = None
        page_range_end = None

        if uploaded_file is not None:
            # Try to get page count from PDF
            try:
                import fitz  # PyMuPDF
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_pdf_path = temp_dir / f"temp_{timestamp}_{uploaded_file.name}"
                with open(temp_pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                pdf_doc = fitz.open(str(temp_pdf_path))
                total_pages = len(pdf_doc)
                pdf_doc.close()
                temp_pdf_path.unlink()

                st.info(f"📊 Total pages in PDF: {total_pages}")

                if page_selection_mode == "Specific pages":
                    selected_pages_input = st.text_input(
                        "Enter page numbers (comma-separated):",
                        placeholder="e.g., 1, 3, 5, 7",
                        help="Enter specific page numbers separated by commas"
                    )
                    if selected_pages_input:
                        try:
                            selected_pages = [int(p.strip()) for p in selected_pages_input.split(",")]
                            selected_pages = [p for p in selected_pages if 1 <= p <= total_pages]
                            if selected_pages:
                                st.success(f"✓ Will process {len(selected_pages)} page(s): {selected_pages}")
                            else:
                                st.warning("⚠️ No valid page numbers entered")
                        except ValueError:
                            st.error("✗ Invalid input. Please enter numbers separated by commas")

                elif page_selection_mode == "Page range":
                    col1, col2 = st.columns(2)
                    with col1:
                        page_range_start = st.number_input(
                            "From page:",
                            min_value=1,
                            max_value=total_pages,
                            value=1,
                            step=1
                        )
                    with col2:
                        page_range_end = st.number_input(
                            "To page:",
                            min_value=1,
                            max_value=total_pages,
                            value=total_pages,
                            step=1
                        )

                    if page_range_start <= page_range_end:
                        pages_count = page_range_end - page_range_start + 1
                        st.success(f"✓ Will process {pages_count} page(s) from {page_range_start} to {page_range_end}")
                    else:
                        st.error("✗ Start page must be less than or equal to end page")

            except Exception as e:
                st.warning(f"⚠️ Could not read PDF page count: {str(e)}")
        else:
            st.info("📤 Upload a PDF to select pages")

        st.divider()

        st.subheader("🚀 Performance Options")

        # Multi-threading settings
        max_workers = st.slider(
            "Parallel Processing Threads",
            min_value=1,
            max_value=8,
            value=4,
            step=1,
            help="Number of pages to process simultaneously. More threads = faster but higher API rate limit usage"
        )

        st.divider()

        st.subheader("⚙️ Processing Options")

        # DPI setting
        dpi = st.slider(
            "PNG Resolution (DPI)",
            min_value=150,
            max_value=600,
            value=300,
            step=50,
            help="Higher DPI = better quality but slower processing"
        )

        # Table refinement
        refine_tables = st.checkbox(
            "Refine Table Structures",
            value=True,
            help="Use second pass to verify table accuracy (slower but more accurate)"
        )

        # Image extraction
        extract_images = st.checkbox(
            "Extract Embedded Images",
            value=True,
            help="Extract original images directly from PDF"
        )

        # HTML to PDF method
        html_method = st.selectbox(
            "HTML to PDF Method",
            options=["skip", "weasyprint", "playwright", "pdfkit"],
            index=0,
            help="skip: HTML only (pure Python, recommended), weasyprint: High quality PDF (requires system libs)"
        )

        st.divider()

        st.subheader("📚 About")
        st.markdown("""
        This tool uses:
        - **PyMuPDF**: PDF to PNG conversion
        - **OpenAI GPT-4 Vision**: AI content extraction
        - **HTML/CSS**: Layout reconstruction
        - **Multi-threading**: Parallel page processing
        - **Optional**: PDF conversion (requires system libs)

        **Process:**
        1. Convert PDF pages to PNG
        2. Extract content with AI (in parallel)
        3. Generate HTML pages
        4. Optionally create PDF (or use HTML output)

        **Pure Python**: Works out-of-the-box with pip only!
        """)

        return {
            'api_key': api_key,
            'dpi': dpi,
            'refine_tables': refine_tables,
            'extract_images': extract_images,
            'html_method': html_method,
            'max_workers': max_workers,
            'page_selection_mode': page_selection_mode,
            'selected_pages': selected_pages,
            'page_range_start': page_range_start,
            'page_range_end': page_range_end
        }


def process_pdf(uploaded_file, settings):
    """Process the uploaded PDF file"""
    # Save uploaded file temporarily
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_pdf_path = temp_dir / f"{timestamp}_{uploaded_file.name}"

    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Create output directory
    output_dir = Path("output") / timestamp

    # Initialize processor
    processor = PDFProcessor(
        openai_api_key=settings['api_key'],
        dpi=settings['dpi'],
        html_to_pdf_method=settings['html_method'],
        output_dir=str(output_dir)
    )

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(progress: int, message: str):
        progress_bar.progress(progress)
        status_text.text(f"🔄 {message}")

    # Determine pages to process
    pages_to_process = None
    if settings['page_selection_mode'] == "Specific pages" and settings['selected_pages']:
        pages_to_process = settings['selected_pages']
    elif settings['page_selection_mode'] == "Page range":
        if settings['page_range_start'] and settings['page_range_end']:
            pages_to_process = list(range(settings['page_range_start'], settings['page_range_end'] + 1))

    # Process PDF
    try:
        results = processor.process_pdf(
            str(temp_pdf_path),
            refine_tables=settings['refine_tables'],
            extract_images=settings['extract_images'],
            progress_callback=progress_callback,
            max_workers=settings['max_workers'],
            pages_to_process=pages_to_process
        )

        # Load processing report
        report_path = output_dir / "processing_report.json"
        with open(report_path, 'r') as f:
            report = json.load(f)

        # Clean up temp file
        temp_pdf_path.unlink()

        return results, report

    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None, None


def display_results(results, report):
    """Display processing results"""
    st.markdown('<div class="success-box">✅ <strong>Processing Complete!</strong></div>',
                unsafe_allow_html=True)

    # Statistics
    st.subheader("📊 Extraction Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{report['statistics']['total_pages']}</div>
            <div class="stat-label">Pages</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{report['statistics']['total_tables']}</div>
            <div class="stat-label">Tables</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{report['statistics']['total_images_detected']}</div>
            <div class="stat-label">Images Detected</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{report['statistics']['total_text_blocks']}</div>
            <div class="stat-label">Text Blocks</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Download section
    st.subheader("📥 Download Results")

    col1, col2 = st.columns(2)

    with col1:
        # Download extracted HTML
        if results.get('final_html') and os.path.exists(results['final_html']):
            with open(results['final_html'], 'r', encoding='utf-8') as f:
                html_content = f.read()
            st.download_button(
                label="⬇️ Download Extracted HTML",
                data=html_content,
                file_name=Path(results['final_html']).name,
                mime="text/html",
                width='stretch'
            )

    with col2:
        # Download processing report
        report_json = json.dumps(report, indent=2)
        st.download_button(
            label="⬇️ Download Processing Report",
            data=report_json,
            file_name="processing_report.json",
            mime="application/json",
            width='stretch'
        )

    st.divider()

    # Page-by-page results
    st.subheader("📑 Page-by-Page Results")

    with st.expander("View Detailed Results", expanded=False):
        for page_detail in report['page_details']:
            page_num = page_detail['page_num']

            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown(f"**Page {page_num}**")

                # Show PNG preview
                png_path = results['png_pages'][page_num - 1]
                if os.path.exists(png_path):
                    st.image(png_path, caption=f"Page {page_num} PNG", width='stretch')

            with col2:
                st.markdown(f"""
                - **Tables:** {page_detail['tables_count']}
                - **Images:** {page_detail['images_count']}
                - **Text Blocks:** {page_detail['text_blocks_count']}
                - **Layout:** {page_detail['layout'].get('orientation', 'N/A')}
                """)

                # Show extracted content
                content_path = results['extracted_content'][page_num - 1]
                if os.path.exists(content_path):
                    with open(content_path, 'r') as f:
                        content = json.load(f)

                    if content.get('tables'):
                        st.markdown("**Extracted Tables:**")
                        for idx, table in enumerate(content['tables'], 1):
                            table_id = table.get('id', f'table_{idx}')
                            with st.expander(f"Table {table_id}"):
                                st.markdown(table.get('html', ''), unsafe_allow_html=True)

            st.divider()

    # Comparison view
    st.subheader("🔍 Comparison View")

    with st.expander("Compare Original vs Reconstructed", expanded=False):
        st.markdown("""
        <div class="info-box">
        📌 <strong>Tip:</strong> Download both PDFs to compare side-by-side in a PDF viewer.
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Original PDF**")
            st.write(f"📄 {Path(results['original_pdf']).name}")

        with col2:
            st.markdown("**Reconstructed PDF**")
            if results['final_pdf']:
                st.write(f"📄 {Path(results['final_pdf']).name}")


def main():
    """Main application"""
    init_session_state()
    display_header()

    # File upload (needed for sidebar to show page count)
    st.subheader("📤 Upload PDF")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF containing tables and images"
    )

    # Sidebar settings (pass uploaded_file to enable page selection)
    settings = display_sidebar(uploaded_file)

    # Check API key
    if not settings['api_key']:
        st.markdown("""
        <div class="warning-box">
        ⚠️ <strong>OpenAI API Key Required</strong><br>
        Please enter your OpenAI API key in the sidebar to use this tool.
        </div>
        """, unsafe_allow_html=True)

    if uploaded_file is not None:
        # Display file info
        file_size = uploaded_file.size / (1024 * 1024)  # Convert to MB
        st.markdown(f"""
        <div class="info-box">
        📄 <strong>File:</strong> {uploaded_file.name}<br>
        📏 <strong>Size:</strong> {file_size:.2f} MB
        </div>
        """, unsafe_allow_html=True)

        # Process button
        if st.button("🚀 Process PDF", type="primary", width='stretch'):
            if not settings['api_key']:
                st.error("Please provide an OpenAI API key in the sidebar!")
            else:
                with st.spinner("Processing PDF..."):
                    results, report = process_pdf(uploaded_file, settings)

                    if results and report:
                        st.session_state.processing_complete = True
                        st.session_state.results = results
                        st.session_state.report = report
                        st.rerun()

    # Display results if processing is complete
    if st.session_state.processing_complete:
        st.divider()
        display_results(st.session_state.results, st.session_state.report)

        # Reset button
        if st.button("🔄 Process Another PDF", width='stretch'):
            st.session_state.processing_complete = False
            st.session_state.results = None
            st.session_state.report = None
            st.rerun()


if __name__ == "__main__":
    main()
