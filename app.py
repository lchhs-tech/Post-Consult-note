import streamlit as st
import tempfile
import os
import time

from main import summarize_consultation, extract_text_from_word_filelike
from word_generator import write_summary_to_docx

# Hardcoded Authentication Credentials
USERNAME = "admin"
PASSWORD = "password123"

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ---------- LOGIN PAGE ----------
def login():
    st.set_page_config(page_title="Login - Post Consult Note Summarizer", page_icon="🔒")
    st.markdown(
        """
        <style>
            .login-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 90vh;
            }
            .login-box {
                width: 400px;
                padding: 20px;
                text-align: center;
                background: white;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            }
            .login-logo img {
                width: 150px;
                margin-bottom: 20px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.image("lc-logo-mobile1.png", width=150)
    st.title("🔒 Login to Access")
    username = st.text_input("👤 Username", value="", key="username")
    password = st.text_input("🔑 Password", value="", type="password", key="password")

    if st.button("🔓 Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Login Successful! Redirecting...")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Invalid Username or Password")

# ---------- LOGOUT ----------
def logout():
    st.session_state.authenticated = False
    st.rerun()

# ---------- MAIN APP ----------
def main_app():
    st.set_page_config(page_title="Pre-Consult Notes", layout="wide")

    # Custom Styling
    st.markdown(
        """
        <style>
            .header-container {
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .header-logo img {
                width: 120px;
            }
            .stButton>button {
                width: 100%;
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
            .stSpinner {
                font-size: 20px;
                font-weight: bold;
                color: #3498db;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header
    col1, col2 = st.columns([5, 1])
    with col1:
        st.image("lc-logo-mobile1.png", width=150)
        st.title("Post-Consult Notes")
    with col2:
        if st.button("🚪 Logout"):
            logout()

    st.markdown("Upload a **preconsult note (.docx)** and **video** consultation files to generate a combined summary.")

    uploaded_word_file = st.file_uploader("Upload Preconsult Note (.docx) [Optional]", type=["docx"])
    uploaded_files = st.file_uploader("Upload Audio/Video Consultation Files", type=["mp4"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("Generate Combined Summary (.docx)"):
            st.info("⏳ Processing started. Please wait...")

            extracted_text = ""
            if uploaded_word_file:
                try:
                    extracted_text = extract_text_from_word_filelike(uploaded_word_file)
                except Exception as e:
                    st.error(f"❌ Failed to read Word file: {e}")

            summaries = []
            for file in uploaded_files:
                try:
                    suffix = os.path.splitext(file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(file.read())
                        tmp_path = tmp.name

                    with st.spinner(f"🔄 Processing {file.name}..."):
                        summary = summarize_consultation(tmp_path, extracted_text)
                        summaries.append(summary)
                        st.success(f"✅ Finished: {file.name}")

                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

            final_doc_path = write_summary_to_docx(summaries)

            with open(final_doc_path, "rb") as f:
                st.download_button(
                    label="📥 Download Final Summary (.docx)",
                    data=f,
                    file_name="Post_Consult_note_Summary.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            os.remove(final_doc_path)

# ---------- RUN APP ----------
if st.session_state.authenticated:
    main_app()
else:
    login()
