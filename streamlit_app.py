import streamlit as st
import os
import tempfile
import asyncio
import pandas as pd
from core.prompt_engine import PromptEngine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# --- Sleek Modern CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
body, .stApp, .block-container {
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(120deg, #f8fafc 0%, #e0f2fe 100%) !important;
    color: #1e293b !important;
}
.stApp { background: none !important; }
.sidebar-header {
    display: flex; align-items: center; gap: 12px; padding: 1.5rem 1rem 2rem 1rem;
    background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%);
    color: #fff !important;
    border-radius: 0.8rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px 0 rgba(34,197,94,0.10);
}
.sidebar-header .icon-bg {
    width: 56px;
    height: 56px;
    min-width: 56px;
    min-height: 56px;
    max-width: 56px;
    max-height: 56px;
    border-radius: 50%;
    background: #fff !important;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #22c55e !important;
    font-size: 2rem;
    margin-right: 0.5rem;
    margin-bottom: 0;
}
.sidebar-header h1, .sidebar-header, .sidebar-header * {
    color: #fff !important;
}
[data-testid="stSidebar"] {
    background: #14532d !important;
    border-right: 1px solid #bbf7d0;
}
.block-container { padding: 2.5rem 6vw 2rem 6vw; max-width: 1200px !important; margin: 0 auto !important; }
.welcome-banner {
    background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%);
    color: #111 !important; padding: 2.5rem 2rem; border-radius: 1.2rem; margin-bottom: 2rem;
    box-shadow: 0 4px 24px 0 rgba(34,197,94,0.08);
}
.welcome-banner h1 { font-size: 2.3rem; font-weight: 800; margin-bottom: 0.5rem; color: #fff !important; }
.card {
    background: #fff; border-radius: 1.1rem; padding: 2rem 2rem 1.5rem 2rem;
    box-shadow: 0 2px 12px 0 rgba(16,185,129,0.07);
    margin-bottom: 2rem;
    color: #14532d !important;
}
.card h2 {
    font-size: 1.3rem; font-weight: 700; color: #15803d; margin-bottom: 1.2rem;
}
.stButton>button {
    background: linear-gradient(90deg,#22c55e,#16a34a);
    color: #fff; font-weight: 700; border-radius: 0.7rem; padding: 0.7em 2em; border: none;
    font-size: 1.1em; letter-spacing: 0.5px; transition: background 0.2s;
}
.stButton>button:hover {
    background: linear-gradient(90deg,#16a34a,#22c55e); color: #fff;
}
.stDownloadButton>button {
    background: #e6f9ec; color: #15803d; border-radius: 0.7rem; border: 1px solid #bbf7d0; font-weight: 600;
}
.summary-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-bottom: 2.5rem;
}
.summary-card {
    padding: 2rem; border-radius: 1.1rem; display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 2px 8px 0 rgba(34,197,94,0.07);
    color: #14532d !important;
}
.summary-card-green { background: #f0fdf4; border: 1px solid #bbf7d0; }
.summary-card-blue { background: #eff6ff; border: 1px solid #bfdbfe; }
.summary-card-red { background: #fef2f2; border: 1px solid #fecaca; }
.summary-card .icon { font-size: 2rem; }
.summary-card-green .icon { color: #22c55e; }
.summary-card-blue .icon { color: #3b82f6; }
.summary-card-red .icon { color: #ef4444; }
.stTextInput>div>div>input, .stFileUploader>div>div>input {
    background: #fff !important; color: #14532d !important; border: 1px solid #bbf7d0 !important; border-radius: 8px !important;
}
.stAlert, .stAlert p, .stAlert span, .stAlert div {
    color: #14532d !important;
}
.stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div, .stText, .stText p, .stText span, .stText div {
    color: #14532d !important;
}
.st-emotion-cache-1v0mbdj label, .st-emotion-cache-1dp5vir label, .stRadio label, .stRadio span, .stRadio div[role="radio"], .stRadio div[role="radio"] > div, .stRadio div[role="radio"] > label, .stRadio div[role="radiogroup"] > div > label, .stRadio div[role="radiogroup"] > label, .stRadio div[role="radiogroup"] label span {
    color: #fff !important;
    font-weight: 700 !important;
}

/* Main content radio buttons (not sidebar) */
section.main [role="radiogroup"] label, .block-container [role="radiogroup"] label, .block-container .stRadio label, .block-container .stRadio span {
    color: #14532d !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)


# --- Page Functions ---

@st.cache_data
def get_file_icon(file_name):
    """Returns an appropriate FontAwesome icon for a file type."""
    if file_name.endswith(".pdf"):
        return "fa-file-pdf"
    elif file_name.endswith(".txt"):
        return "fa-file-alt"
    else:
        return "fa-file"

def display_results(result):
    """Renders the analysis results in a structured format."""
    st.markdown("---")
    # Summary Cards
    st.markdown("""
    <div class="summary-grid">
        <div class="summary-card summary-card-blue">
            <div>
                <p class="text-sm font-medium text-blue-600">Total Requirements</p>
                <h3 class="text-2xl font-bold text-blue-800">24</h3>
            </div>
            <i class="fas fa-list-ol icon"></i>
        </div>
        <div class="summary-card summary-card-green">
            <div>
                <p class="text-sm font-medium text-green-600">Fully Compliant</p>
                <h3 class="text-2xl font-bold text-green-800">18</h3>
            </div>
            <i class="fas fa-check-circle icon"></i>
        </div>
        <div class="summary-card summary-card-red">
            <div>
                <p class="text-sm font-medium text-red-600">Non-Compliant</p>
                <h3 class="text-2xl font-bold text-red-800">6</h3>
            </div>
            <i class="fas fa-exclamation-circle icon"></i>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Detailed Results
    output_files = result.get("output_files", [])
    if not output_files:
        st.info("The pipeline ran successfully but produced no output files.")
        st.json(result)
        return

    for file_path in output_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        file_name = os.path.basename(file_path)
        st.markdown(f"### <i class='fas {get_file_icon(file_name)}'></i> Analysis Report: `{file_name}`", unsafe_allow_html=True)
        
        if file_name.endswith(".csv"):
            try:
                df = pd.read_csv(file_path)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Could not parse CSV: {e}")
                st.text_area("File Content", content, height=300)
        else:
            st.text_area("File Content", content, height=400, key=f"text_{file_name}")

        st.download_button(
            label="Download Report",
            data=content,
            file_name=file_name,
            mime="text/plain" if file_name.endswith(".txt") else "text/csv",
        )


def run_pipeline_page():
    st.markdown('<div class="welcome-banner"><h1>Run Tender Analysis</h1><p>Upload your tender document and get instant, actionable compliance and meter recommendations.</p></div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h2><i class="fas fa-file-upload" style="color:#22c55e;"></i> Upload Tender Document</h2>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Drag & drop or click to upload your tender document (PDF, TXT).",
            type=["pdf", "txt"],
            label_visibility="visible"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    if not uploaded_file:
        st.markdown("<div class='stAlert' style='color:#14532d;font-weight:600;'>Please upload a file to begin.</div>", unsafe_allow_html=True)
        return

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h2><i class="fas fa-cogs" style="color:#22c55e;"></i> Select Analysis Pipeline</h2>', unsafe_allow_html=True)
        pipeline_options = {
            "Clause Extraction": "prompts/tender_analysis.yaml",
            "Full Analysis & Meter Recommendation": "prompts/meter_recommendation.yaml",
            "Quick Semantic Match (Chroma-Only)": "prompts/meter_recommendation_chroma_only.yaml"
        }
        pipeline_choice = st.radio(
            "Select the analysis pipeline:",
            options=list(pipeline_options.keys()),
            index=1,
            horizontal=True,
        )
        pipeline_yaml = pipeline_options[pipeline_choice]
        st.markdown('</div>', unsafe_allow_html=True)

    run_btn = st.button("Run Analysis", type="primary")

    if run_btn:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[-1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h2><i class="fas fa-spinner fa-spin"></i> Processing Tender...</h2>', unsafe_allow_html=True)
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_callback(progress, text):
            progress_bar.progress(progress)
            status_text.text(text)

        try:
            engine = PromptEngine()
            inputs = {"tender_document": temp_path} if "analysis" in pipeline_yaml else {"analysis_file": temp_path}
            result = asyncio.run(engine.run_prompt(pipeline_yaml, progress_callback=progress_callback, **inputs))
            if result.get("success"):
                status_text.success("Analysis complete! ✅")
                display_results(result)
            else:
                st.error(f"Pipeline failed: {result.get('error', 'An unknown error occurred.')}")
        finally:
            st.markdown('</div>', unsafe_allow_html=True)
            os.remove(temp_path)


def dashboard_page():
    st.markdown('<div class="welcome-banner"><h1>Welcome to Schneider Prompt Engine</h1><p>Your intelligent assistant for tender compliance and meter recommendation.</p></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h2><i class="fas fa-rocket" style="color:#22c55e;"></i> Quick Start</h2>
        <ol style="padding-left: 20px;">
            <li><b>Upload Tender:</b> Go to <span style='color:#16a34a;'>Run Pipeline</span> and upload your document.</li>
            <li><b>Select Pipeline:</b> Choose the analysis type. <span style='color:#16a34a;'>Full Analysis</span> is recommended for most users.</li>
            <li><b>Analyze & Review:</b> Run the process and review the compliance report and recommendations.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h2><i class="fas fa-sitemap" style="color:#22c55e;"></i> How It Works</h2>
        <ul>
            <li><strong>Document Ingestion:</strong> Parses and chunks tender documents for analysis.</li>
            <li><strong>Clause Extraction:</strong> Uses LLMs to identify key requirements.</li>
            <li><strong>Semantic Search:</strong> Finds the most relevant meters using ChromaDB.</li>
            <li><strong>Compliance Engine:</strong> Generates detailed compliance reports.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar and Page Routing ---
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div class="icon-bg">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M28 4C18 4 4 12 4 24C4 27 7 28 10 28C19 28 28 19 28 4Z" fill="#22c55e" stroke="#15803d" stroke-width="2"/>
                <path d="M12 24C12 18 18 12 28 8" stroke="#15803d" stroke-width="2" stroke-linecap="round"/>
            </svg>
        </div>
        <h1>Schneider Prompt Engine</h1>
    </div>
    """, unsafe_allow_html=True)
    page = st.radio(
        "Navigation", 
        ["Dashboard", "Run Pipeline"], 
        label_visibility="collapsed"
    )

if page == "Dashboard":
    dashboard_page()
elif page == "Run Pipeline":
    run_pipeline_page()