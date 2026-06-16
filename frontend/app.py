import streamlit as st
import requests
import os
import time

# Set page configuration
st.set_page_config(
    page_title="DocTalk - Document Q&A",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for the dark theme and custom UI layout
CSS = """
<style>
/* Main app styling */
.stApp {
    background-color: #0F1117;
    color: #E2E8F0;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #0F1117;
    border-right: 1px solid #2D313F;
}

/* Hide default streamlit margins & paddings */
div.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* Title and UI Headers */
.sidebar-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 25px;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Hide Streamlit default file uploader label and style dropzone */
[data-testid="stFileUploader"] {
    margin-bottom: 20px;
}
[data-testid="stFileUploader"] section {
    background-color: #1A1D27 !important;
    border: 1px dashed #2D313F !important;
    border-radius: 8px !important;
    padding: 15px !important;
    color: #E2E8F0 !important;
    transition: border-color 0.2s ease;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #6366F1 !important;
}

/* Section Header for Documents */
.sidebar-header {
    font-size: 0.8rem;
    font-weight: 600;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
    margin-top: 15px;
}

/* Document Card layout in Sidebar */
.doc-card-container {
    background-color: #1A1D27;
    border: 1px solid #2D313F;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: all 0.2s ease;
}
.doc-card-container:hover {
    border-color: #6366F1;
}
.doc-card-active {
    background-color: #242838 !important;
    border-color: #6366F1 !important;
}

.doc-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}

.doc-card-icon {
    font-size: 1.1rem;
}

.doc-card-title {
    font-weight: 500;
    color: #FFFFFF;
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 200px;
}

.doc-card-meta {
    font-size: 0.75rem;
    color: #9CA3AF;
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-badge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
}
.status-indexed {
    color: #10B981;
    background-color: rgba(16, 185, 129, 0.1);
}
.status-processing {
    color: #F59E0B;
    background-color: rgba(245, 158, 11, 0.1);
}
.status-failed {
    color: #EF4444;
    background-color: rgba(239, 68, 68, 0.1);
}

/* Chat Bubbles CSS */
.chat-container {
    padding: 10px 0;
}

.user-bubble-container {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 20px;
    width: 100%;
}
.user-bubble {
    background-color: #E2E8F0;
    color: #0F1117;
    padding: 12px 18px;
    border-radius: 20px 20px 4px 20px;
    max-width: 70%;
    font-size: 0.95rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.assistant-bubble-container {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 20px;
    width: 100%;
}
.assistant-bubble {
    background-color: #1A1D27;
    border: 1px solid #2D313F;
    border-radius: 12px;
    padding: 18px;
    width: 100%;
    max-width: 85%;
    color: #E2E8F0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

.assistant-text {
    line-height: 1.6;
    margin-bottom: 14px;
    font-size: 0.95rem;
}

/* Citations & Sources Card CSS */
.sources-details {
    border-top: 1px solid #2D313F;
    padding-top: 12px;
    margin-top: 12px;
}
.sources-summary {
    cursor: pointer;
    font-weight: 600;
    font-size: 0.8rem;
    color: #9CA3AF;
    display: flex;
    align-items: center;
    gap: 6px;
    outline: none;
    user-select: none;
}
.sources-summary:hover {
    color: #6366F1;
}
.sources-content {
    margin-top: 10px;
}
.source-card {
    background-color: #0F1117;
    border: 1px solid #2D313F;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 10px;
}
.source-page-badge {
    background-color: #2D313F;
    color: #E2E8F0;
    font-size: 0.75rem;
    font-weight: bold;
    padding: 2px 8px;
    border-radius: 12px;
    display: inline-block;
    margin-bottom: 8px;
}
.source-text {
    font-size: 0.85rem;
    color: #9CA3AF;
    line-height: 1.5;
}

/* Main Area Header Pill */
.header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #2D313F;
    padding-bottom: 15px;
    margin-bottom: 25px;
}
.header-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    gap: 8px;
}
.hybrid-badge {
    background-color: #1A1D27;
    border: 1px solid #2D313F;
    padding: 6px 12px;
    border-radius: 20px;
    color: #FFFFFF;
    font-size: 0.8rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Empty State layout */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 100px 20px;
    text-align: center;
    color: #9CA3AF;
}
.empty-icon {
    font-size: 4rem;
    color: #6366F1;
    margin-bottom: 20px;
}
.empty-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #FFFFFF;
    margin-bottom: 8px;
}

/* Custom Chat Input styling */
div[data-testid="stChatInput"] {
    background-color: #1A1D27 !important;
    border: 1px solid #2D313F !important;
    border-radius: 24px !important;
}
div[data-testid="stChatInput"] textarea {
    color: #FFFFFF !important;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Parse query parameters for active doc selection
qp = st.query_params
if "doc" in qp:
    st.session_state.selected_doc = qp["doc"]

# 1. Fetch document list from backend
try:
    response = requests.get("http://localhost:8000/documents")
    if response.status_code == 200:
        documents = response.json()
    else:
        documents = []
except Exception:
    documents = []

# --- SIDEBAR PRESENTATION ---
st.sidebar.markdown("<div class='sidebar-title'>📄 DocTalk</div>", unsafe_allow_html=True)

# File Upload block
uploaded_file = st.sidebar.file_uploader(
    "Upload Document",
    type=["pdf"],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    # Verify if file is already tracked
    existing_filenames = [d["filename"] for d in documents]
    if uploaded_file.name not in existing_filenames:
        with st.sidebar.status("Uploading PDF...") as status:
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                res = requests.post("http://localhost:8000/upload", files=files)
                if res.status_code == 200:
                    status.update(label=f"Uploaded {uploaded_file.name}!", state="complete")
                    st.query_params["doc"] = uploaded_file.name
                    st.session_state.selected_doc = uploaded_file.name
                    st.rerun()
                else:
                    status.update(label="Upload failed", state="error")
                    st.sidebar.error("Failed to parse document.")
            except Exception as e:
                status.update(label="Upload failed", state="error")
                st.sidebar.error(f"Backend offline: {str(e)}")

# Sidebar Documents List
st.sidebar.markdown("<div class='sidebar-header'>Documents</div>", unsafe_allow_html=True)

if not documents:
    st.sidebar.info("No documents uploaded yet.")
else:
    for doc in documents:
        filename = doc["filename"]
        page_count = doc["page_count"]
        status = doc["status"]
        
        is_active = st.session_state.get("selected_doc") == filename
        active_class = "doc-card-active" if is_active else ""
        
        status_color_class = f"status-{status}"
        status_text = f"{status}"
        
        # Clickable document cards linking via query parameters
        card_html = f"""
        <a href="/?doc={filename}" target="_self" style="text-decoration: none;">
            <div class="doc-card-container {active_class}">
                <div class="doc-card-header">
                    <span class="doc-card-icon">📄</span>
                    <span class="doc-card-title" title="{filename}">{filename}</span>
                </div>
                <div class="doc-card-meta">
                    <span>{page_count} pages</span>
                    <span class="status-badge {status_color_class}">● {status_text}</span>
                </div>
            </div>
        </a>
        """
        st.sidebar.markdown(card_html, unsafe_allow_html=True)

    # Fallback selectbox for document selection in environments where URL clicks are restricted
    doc_names = [d["filename"] for d in documents]
    default_idx = 0
    if st.session_state.get("selected_doc") in doc_names:
        default_idx = doc_names.index(st.session_state.selected_doc)
    
    st.sidebar.markdown("<hr style='border-color: #2D313F; margin-top: 20px;'/>", unsafe_allow_html=True)
    selected_name = st.sidebar.selectbox(
        "Fallback Doc Selector",
        doc_names,
        index=default_idx,
        label_visibility="visible"
    )
    if selected_name != st.session_state.get("selected_doc"):
        st.session_state.selected_doc = selected_name
        st.query_params["doc"] = selected_name
        st.rerun()

# --- MAIN WINDOW PRESENTATION ---
if "selected_doc" not in st.session_state or not st.session_state.selected_doc:
    # Empty State when no document has been selected
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">💬</div>
            <div class="empty-title">Welcome to DocTalk</div>
            <p>Upload a document in the sidebar or select one from the list to start asking questions.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    active_doc = st.session_state.selected_doc
    
    # 2. Render Selected Doc Header
    st.markdown(
        f"""
        <div class="header-container">
            <div class="header-title">📄 {active_doc}</div>
            <div class="hybrid-badge">✨ Hybrid Search: ON</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 3. Handle session state chat logs
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
        
    if active_doc not in st.session_state.chat_history:
        st.session_state.chat_history[active_doc] = []
        
    chat_logs = st.session_state.chat_history[active_doc]
    
    # Render chat logs
    chat_placeholder = st.container()
    with chat_placeholder:
        for msg in chat_logs:
            if msg["role"] == "user":
                st.markdown(
                    f"""
                    <div class="user-bubble-container">
                        <div class="user-bubble">{msg['content']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                sources_html = ""
                sources = msg.get("sources", [])
                if sources:
                    source_cards = ""
                    for src in sources:
                        source_cards += f"""
                        <div class="source-card">
                            <span class="source-page-badge">Page {src['page']}</span>
                            <div class="source-text">{src['text']}</div>
                        </div>
                        """
                    
                    sources_html = f"""
                    <details class="sources-details">
                        <summary class="sources-summary">🔗 Sources ({len(sources)})</summary>
                        <div class="sources-content">
                            {source_cards}
                        </div>
                    </details>
                    """
                    
                st.markdown(
                    f"""
                    <div class="assistant-bubble-container">
                        <div class="assistant-bubble">
                            <div class="assistant-text">{msg['content']}</div>
                            {sources_html}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    # 4. Chat Input Box
    if prompt := st.chat_input("Ask a question about this document..."):
        # Append user message and render immediately
        chat_logs.append({"role": "user", "content": prompt})
        st.markdown(
            f"""
            <div class="user-bubble-container">
                <div class="user-bubble">{prompt}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Request response from Backend
        with st.spinner("Analyzing document..."):
            try:
                payload = {
                    "question": prompt,
                    "filename": active_doc
                }
                res = requests.post("http://localhost:8000/query", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    answer = data["answer"]
                    sources = data.get("sources", [])
                    
                    # Store AI answer
                    chat_logs.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                    st.rerun()
                else:
                    st.error("Backend error occurred.")
            except Exception as e:
                st.error(f"Backend offline: {str(e)}")

# Real-time polling to update page status if any doc is processing
any_processing = any(d["status"] == "processing" for d in documents)
if any_processing:
    time.sleep(2)
    st.rerun()
